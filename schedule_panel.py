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

DEFAULT_HIGHLIGHT = "#fffbcc"
CURRENT_BG = "#cfe9ff"
OUTSTANDING_BG = "#ffd6d6"


class SchedulePanel:
    """Schedule management panel"""
    
    def __init__(self, parent, coordinator, config):
        self.parent = parent
        self.coordinator = coordinator
        self.config = config
        
        self.font_large = ("Segoe UI", 20)
        self.font_med = ("Segoe UI", 16)
        self.font_small = ("Segoe UI", 12)
        
        self.water_goal = self.config.get("water_goal", 3)

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

        ensure_med("paracetamol", "Paracetamol")
        ensure_med("ibuprofen", "Ibuprofen")

        # Do NOT pre-load `other_meds` from config; other meds are added
        # ad-hoc by the user at runtime and stored in the daily log.
        self.medications = meds
        self.schedule = self.parse_schedule(self.config.get("schedule", []))
        self.apply_overrides()
        
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
        p.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")
    
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
                "notes": item.get("notes", "")
            })
        out.sort(key=lambda x: x["time"])
        return out
    
    def apply_overrides(self):
        try:
            overrides = self.config.get("overrides", {})
            wd = datetime.date.today().strftime("%A")
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
                            "notes": ex.get("notes", "")
                        })
                self.schedule.sort(key=lambda x: x["time"])
        except Exception:
            pass
    
    def build_ui(self):
        # Top header
        top = tk.Frame(self.parent)
        top.pack(fill=tk.X, padx=10, pady=8)
        
        self.date_label = tk.Label(top, text="", font=self.font_large)
        self.date_label.pack(side=tk.LEFT)
        
        self.time_label = tk.Label(top, text="", font=("Segoe UI", 36, "bold"))
        self.time_label.pack(side=tk.RIGHT)
        
        # Schedule list with scrollbar
        list_frame = tk.Frame(self.parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        
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
            row = tk.Frame(self.frame, pady=6)
            row.pack(fill=tk.X, padx=6, pady=4)
            
            time_str = item.get("time").strftime("%H:%M") if item.get("time") else ""
            lbl_time = tk.Label(row, text=time_str, font=self.font_med, width=8, anchor="w")
            lbl_time.pack(side=tk.LEFT)
            
            lbl_title = tk.Label(row, text=item.get("title", ""), font=self.font_med, anchor="w")
            lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            chk_text = tk.StringVar(value=("✓" if self.log.get(item.get("id"), {}).get("checked") else ""))
            lbl_check = tk.Label(row, textvariable=chk_text, font=("Segoe UI", 22), width=3)
            lbl_check.pack(side=tk.LEFT)
            
            btn_note = tk.Button(row, text="Notes", font=self.font_small, width=10,
                               command=lambda i=item: self.edit_note(i))
            btn_note.pack(side=tk.RIGHT, padx=6)
            
            btn_check = tk.Button(row, text="Check", font=self.font_small, width=10,
                                command=lambda i=item: self.toggle_check(i))
            btn_check.pack(side=tk.RIGHT)
            
            self.row_widgets[item.get("id")] = {"frame": row, "check_var": chk_text}
    
    def toggle_check(self, item):
        cur = self.log.setdefault(item["id"], {"checked": False, "note": ""})
        cur["checked"] = not cur.get("checked", False)
        self.row_widgets[item["id"]]["check_var"].set("✓" if cur["checked"] else "")
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
            self.today = now.date()
            self.log = self.load_log(self.today)
            for item in self.schedule:
                chk = self.log.get(item["id"], {}).get("checked")
                self.row_widgets[item["id"]]["check_var"].set("✓" if chk else "")
        
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
    
    def _midnight_handler(self):
        try:
            self.save_log()
            p = LOG_DIR / f"{self.today.isoformat()}.json"
            if p.exists():
                try:
                    shutil.copy2(p, EXPORT_DIR / p.name)
                except Exception:
                    pass
            self.today = self.today + datetime.timedelta(days=1)
            self.log = self.load_log(self.today)
            for item in self.schedule:
                chk = self.log.get(item["id"], {}).get("checked")
                self.row_widgets[item["id"]]["check_var"].set("✓" if chk else "")
        finally:
            self.schedule_midnight()
