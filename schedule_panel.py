"""
Schedule management panel with timeline, checks, and highlighting.
"""

import json
import datetime
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog

# Constants
HERE = Path(__file__).parent
LOG_DIR = HERE / "schedule_logs"
EXPORT_DIR = HERE / "schedule_exports"

# Ensure log and export directories exist
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
try:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

DEFAULT_HIGHLIGHT = "#fffbcc"
CURRENT_BG = "#cfe9ff"
OUTSTANDING_BG = "#ffd6d6"


class SchedulePanel:
    """Schedule management panel"""
    
    def __init__(self, parent, coordinator, config):
        self.parent = parent
        self.coordinator = coordinator
        self.config = config
        # Compute fonts from config base size for better scaling on large displays
        base = int(self.config.get('font_size', 14))
        self.base = base
        # Slightly reduce multipliers so text fits better and allow descriptions to wrap
        self.font_large = ("Segoe UI", max(12, int(base * 1.0)))
        self.font_med = ("Segoe UI", max(9, int(base * 0.85)))
        self.font_small = ("Segoe UI", max(8, int(base * 0.75)))
        
        self.water_goal = self.config.get("water_goal", 2)

        # Build medications list for the side panel UI.
        # Support legacy `medications` config, include default painkillers,
        # and include `other_meds` entries from config (strings).
        meds = []
        # If config provides explicit medications (list of dicts), use them
        cfg_meds = self.config.get("medications")
        if isinstance(cfg_meds, list) and cfg_meds:
            for m in cfg_meds:
                if isinstance(m, dict) and m.get("id") and m.get("name"):
                    meds.append({"id": m.get("id"), "name": m.get("name")})

        # Ensure basic painkillers are present
        def ensure_med(mid, name):
            if not any(x.get("id") == mid for x in meds):
                meds.append({"id": mid, "name": name})

        # Add hard-coded morning/evening medication entries first
        ensure_med("morning", "Morning")
        ensure_med("evening", "Evening")
        # Ensure basic painkillers are present after the daily meds
        ensure_med("paracetamol", "Paracetamol")
        ensure_med("ibuprofen", "Ibuprofen")

        # Do NOT pre-load `other_meds` from config; other meds are added
        # ad-hoc by the user at runtime and stored in the daily log.
        self.medications = meds
        self.base_schedule = self.config.get("schedule", [])
        self.schedule = []
        self.refresh_schedule_for_date(datetime.date.today())
        
        self.today = datetime.date.today()
        self.log = self.load_log(self.today)
        self.running = True
        
        self.build_ui()
        self.update_clock()
        self.update_highlight()
        self.schedule_midnight()
        
    def load_log(self, date):
        p = LOG_DIR / f"{date.isoformat()}.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
            if "_water" not in data:
                data["_water"] = {"count": 0, "goal": self.water_goal}
            if "_meds" not in data:
                data["_meds"] = {m.get("id"): {"taken": []} for m in self.medications}
            if "_other_meds" not in data:
                data["_other_meds"] = []
            if "_today_notes" not in data:
                data["_today_notes"] = ""
            return data
        
        data = {item["id"]: {"checked": False, "note": ""} for item in self.schedule}
        data["_water"] = {"count": 0, "goal": self.water_goal}
        data["_meds"] = {m.get("id"): {"taken": []} for m in self.medications}
        data["_other_meds"] = []
        data["_today_notes"] = ""
        return data
    
    def save_log(self):
        p = LOG_DIR / f"{self.today.isoformat()}.json"
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            # Fail quietly but log to stderr
            try:
                import logging
                logging.error(f"Failed to save schedule log {p}: {e}")
            except Exception:
                pass
    
    def parse_schedule(self, sched):
        out = []
        for idx, item in enumerate(sched):
            t = datetime.datetime.strptime(item["time"], "%H:%M").time()
            # Generate ID from time+title if not present
            item_id = item.get("id")
            if not item_id:
                item_id = f"{item['time']}_{item.get('title', '')}"
            out.append({
                "id": item_id,
                "time": t,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "notes": item.get("notes", "")
            })
        out.sort(key=lambda x: x["time"])
        return out
    
    def apply_overrides(self, day=None):
        try:
            overrides = self.config.get("weekday_overrides", {})
            target_day = day or self.today
            wd = target_day.strftime("%A")
            day_cfg = overrides.get(wd, {})
            extras = day_cfg.get("extra") if isinstance(day_cfg, dict) else None
            if extras:
                for ex in extras:
                    if isinstance(ex, dict) and ex.get("time") and ex.get("title"):
                        try:
                            t = datetime.datetime.strptime(ex["time"], "%H:%M").time()
                        except Exception:
                            continue
                        self.schedule.append({
                            "id": ex.get("id") or f"override_{ex.get('time')}",
                            "time": t,
                            "title": ex.get("title"),
                            "description": ex.get("description", ""),
                            "notes": ex.get("notes", "")
                        })
                self.schedule.sort(key=lambda x: x["time"])
        except Exception:
            pass

    def refresh_schedule_for_date(self, day):
        self.schedule = self.parse_schedule(self.base_schedule)
        self.apply_overrides(day)
    
    def build_ui(self):
        # Top header
        top = tk.Frame(self.parent)
        top.pack(fill=tk.X, padx=8, pady=6)

        # Date and time fonts: slightly reduced multipliers for tighter layout
        date_font = ("Segoe UI", max(14, int(self.base * 1.2)))
        time_font = ("Segoe UI", max(18, int(self.base * 1.6)), "bold")
        self.date_label = tk.Label(top, text="", font=date_font)
        self.date_label.pack(side=tk.LEFT)
        self.time_label = tk.Label(top, text="", font=time_font)
        self.time_label.pack(side=tk.RIGHT)
        
        # Schedule list with scrollbar
        list_frame = tk.Frame(self.parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.frame = tk.Frame(canvas)
        self.frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.build_schedule_rows()
    
    def build_schedule_rows(self):
        for c in list(self.frame.winfo_children()):
            c.destroy()
        self.row_widgets = {}
        
        for item in self.schedule:
            row = tk.Frame(self.frame, pady=2)
            row.pack(fill=tk.X, padx=4, pady=1)
            
            time_str = item.get("time").strftime("%H:%M") if item.get("time") else ""
            lbl_time = tk.Label(row, text=time_str, font=self.font_med, width=6, anchor="w")
            lbl_time.pack(side=tk.LEFT)
            
            # Title and description container
            text_frame = tk.Frame(row)
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            lbl_title = tk.Label(text_frame, text=item.get("title", ""), font=self.font_med, anchor="w")
            lbl_title.pack(anchor="w")
            
            # Show description if present
            description = item.get("description", "")
            if description and str(description).strip():
                # Create description label with a reasonable default wraplength,
                # then adjust it after geometry has settled so it becomes visible.
                # Use a slightly darker grey for better contrast and allow the
                # label to fill available horizontal space so wraplength applies.
                lbl_desc = tk.Label(text_frame, text=description, font=self.font_small,
                                   anchor="w", fg="#444", justify="left", wraplength=480)
                lbl_desc.pack(anchor="w", fill='x')


                def adjust_wrap():
                    try:
                        self.parent.update_idletasks()
                        # Prefer the parent's (schedule_frame) width which was set
                        parent_w = self.parent.winfo_width() or 0
                        if not parent_w or parent_w < 100:
                            # fallback to toplevel width
                            try:
                                parent_w = self.parent.winfo_toplevel().winfo_width()
                            except Exception:
                                parent_w = 800

                        # Subtract time column and check button widths to compute available text area
                        est_margin = 140
                        wrap = max(180, int((parent_w - est_margin) * 0.9))
                        # If calculation produced a small wrap length, ensure a reasonable default
                        if wrap < 200:
                            wrap = max(200, int(parent_w * 0.6))
                        lbl_desc.config(wraplength=wrap)
                    except Exception:
                        pass

                # Run a couple of times after layout to capture final geometry
                self.parent.after(50, adjust_wrap)
                self.parent.after(300, adjust_wrap)
            
            chk_text = tk.StringVar(value=("✓" if self.log.get(item.get("id"), {}).get("checked") else ""))

            # Combined check icon button (toggles checked state) - compact
            check_symbol = "✓" if chk_text.get() else "☐"

            # Notes button temporarily removed from UI (functionality retained)
            check_btn = tk.Button(row, text=check_symbol, font=("Segoe UI", 16), width=2,
                                  command=lambda i=item: self.toggle_check(i))
            check_btn.pack(side=tk.RIGHT, padx=(6, 4))

            self.row_widgets[item.get("id")] = {"frame": row, "check_var": chk_text, "check_btn": check_btn}
    
    def toggle_check(self, item):
        cur = self.log.setdefault(item["id"], {"checked": False, "note": ""})
        cur["checked"] = not cur.get("checked", False)
        self.row_widgets[item["id"]]["check_var"].set("✓" if cur["checked"] else "")
        # Update the compact check button symbol if present
        try:
            btn = self.row_widgets[item["id"]].get("check_btn")
            if btn:
                btn.config(text=("✓" if cur["checked"] else "☐"))
        except Exception:
            pass
        self.save_log()
        self.update_outstanding_flag()
    
    def edit_note(self, item):
        cur = self.log.get(item["id"], {})
        initial = cur.get("note", "")
        note = simpledialog.askstring("Note for " + item["title"], "Enter note:",
                                     initialvalue=initial, parent=self.parent)
        if note is not None:
            self.log[item["id"]]["note"] = note
            self.save_log()
    
    def update_clock(self):
        if not self.running:
            return
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A %d %b %Y"))
        
        if now.date() != self.today:
            self.rollover_to_date(now.date())
        
        self.parent.after(1000, self.update_clock)
    
    def update_highlight(self):
        now_time = datetime.datetime.now().time()
        cur = None
        for item in self.schedule:
            if item["time"] <= now_time:
                cur = item
            else:
                break
        
        for item in self.schedule:
            item_id = item.get("id")
            w = self.row_widgets.get(item_id, {}).get("frame")
            if not w:
                continue
            
            checked = bool(self.log.get(item_id, {}).get("checked"))
            
            if cur and item_id == cur.get("id"):
                bg = CURRENT_BG
            elif item.get("time") and (item.get("time") < now_time) and (not checked):
                bg = OUTSTANDING_BG
            else:
                bg = DEFAULT_HIGHLIGHT
            
            w.configure(bg=bg)
            for child in w.winfo_children():
                try:
                    child.configure(bg=bg)
                except Exception:
                    pass
        
        self.update_outstanding_flag()
        if self.running:
            self.parent.after(5000, self.update_highlight)
    
    def update_outstanding_flag(self):
        now_time = datetime.datetime.now().time()
        has_outstanding = False
        
        for item in self.schedule:
            item_time = item.get("time")
            item_id = item.get("id")
            if item_time and item_time < now_time:
                checked = bool(self.log.get(item_id, {}).get("checked"))
                if not checked:
                    has_outstanding = True
                    break
        
        self.coordinator.set_outstanding(has_outstanding)
    
    def schedule_midnight(self):
        now = datetime.datetime.now()
        next_midnight = datetime.datetime.combine((now + datetime.timedelta(days=1)).date(),
                                                  datetime.time.min)
        ms = int((next_midnight - now).total_seconds() * 1000)
        self.parent.after(ms, self._midnight_handler)

    def rollover_to_date(self, new_date):
        self.today = new_date
        self.refresh_schedule_for_date(new_date)
        self.log = self.load_log(self.today)
        self.build_schedule_rows()
        try:
            self.update_outstanding_flag()
        except Exception:
            pass
        side_panel = getattr(self, "side_panel", None)
        if side_panel and hasattr(side_panel, "refresh_for_new_day"):
            try:
                side_panel.refresh_for_new_day()
            except Exception:
                pass
    
    def _midnight_handler(self):
        try:
            previous_day = self.today
            # Save current day's log; ensure directories exist
            try:
                self.save_log()
            except Exception:
                pass

            try:
                p = LOG_DIR / f"{previous_day.isoformat()}.json"
                if p.exists():
                    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(p, EXPORT_DIR / p.name)
                    except Exception:
                        pass
            except Exception:
                pass

            # Reset to today's actual date (handles clock changes or missed midnights)
            try:
                new_day = datetime.date.today()
            except Exception:
                new_day = previous_day + datetime.timedelta(days=1)

            self.rollover_to_date(new_day)
        finally:
            self.schedule_midnight()
