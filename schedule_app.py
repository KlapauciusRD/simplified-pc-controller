import json
import datetime
import threading
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, messagebox

HERE = Path(__file__).parent
CONFIG_PATH = HERE / "schedule.json"
LOG_DIR = HERE / "schedule_logs"
LOG_DIR.mkdir(exist_ok=True)
EXPORT_DIR = HERE / "schedule_exports"
EXPORT_DIR.mkdir(exist_ok=True)
BLOCK_FLAG = HERE / "schedule_block.flag"

DEFAULT_HIGHLIGHT = "#fffbcc"
CURRENT_BG = "#cfe9ff"
OUTSTANDING_BG = "#ffd6d6"

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Schedule")
        # Touchscreen-friendly: large default sizes
        self.font_large = ("Segoe UI", 20)
        self.font_med = ("Segoe UI", 16)
        self.font_small = ("Segoe UI", 12)

        # Fullscreen friendly but allow windowed by pressing ESC
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        self.config = self.load_config()
        self.water_goal = self.config.get("water_goal", 3)
        self.block_feature_enabled = self.config.get("block_on_outstanding", True)
        self.medications = self.config.get("medications", [])
        self.schedule = self.parse_schedule(self.config.get("schedule", []))
        # apply any per-weekday overrides (extra events)
        self.apply_overrides()

        self.today = datetime.date.today()
        self.log = self.load_log(self.today)

        self.build_ui()
        self.running = True
        self.update_clock()
        self.update_highlight()
        # schedule automatic midnight export/refresh
        self.schedule_midnight()

    def load_config(self):
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {}

    def parse_schedule(self, sched):
        out = []
        for item in sched:
            t = datetime.datetime.strptime(item["time"], "%H:%M").time()
            out.append({"id": item.get("id"), "time": t, "title": item.get("title",""), "notes": item.get("notes","")})
        out.sort(key=lambda x: x["time"])
        return out

    def log_path(self, date):
        return LOG_DIR / f"{date.isoformat()}.json"

    def load_log(self, date):
        p = self.log_path(date)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            # ensure water and meds keys exist for older logs
            if not isinstance(data, dict):
                data = {}
            if "_water" not in data:
                data["_water"] = {"count": 0, "goal": self.water_goal}
            if "_meds" not in data:
                data["_meds"] = {m.get("id"): {"taken": []} for m in self.medications}
            if "_other_meds" not in data:
                data["_other_meds"] = []
            return data
        # initialize log structure
        data = {item["id"]: {"checked": False, "note": ""} for item in self.schedule}
        # water and medication defaults
        data["_water"] = {"count": 0, "goal": self.water_goal}
        data["_meds"] = {m.get("id"): {"taken": []} for m in self.medications}
        data["_other_meds"] = []
        return data

    def save_log(self):
        p = self.log_path(self.today)
        p.write_text(json.dumps(self.log, indent=2, ensure_ascii=False), encoding="utf-8")

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=10, pady=8)

        self.date_label = tk.Label(top, text="", font=self.font_large)
        self.date_label.pack(side=tk.LEFT)

        self.time_label = tk.Label(top, text="", font=("Segoe UI", 36, "bold"))
        self.time_label.pack(side=tk.RIGHT)

        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # Left: schedule list (with scroll)
        left = tk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(left)
        scrollbar = tk.Scrollbar(left, orient=tk.VERTICAL, command=canvas.yview)
        self.frame = tk.Frame(canvas)
        self.frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right: side panel for water and meds
        side = tk.Frame(main, width=280)
        side.pack(side=tk.RIGHT, fill=tk.Y, padx=(8,0))
        self.build_side_panel(side)

        # Build rows
        self.build_schedule_rows()

        # Bottom controls (touch-friendly)
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=10, pady=8)
        btn_quit = tk.Button(bottom, text="Quit", font=self.font_small, command=self.root.quit)
        btn_quit.pack(side=tk.RIGHT)

    def build_side_panel(self, parent):
        # Water tracker
        lbl = tk.Label(parent, text="Water", font=("Segoe UI", 18, "bold"))
        lbl.pack(pady=(6,4))
        self.water_var = tk.StringVar()
        self.update_water_var()
        water_lbl = tk.Label(parent, textvariable=self.water_var, font=("Segoe UI", 16))
        water_lbl.pack()
        self.water_label_widget = water_lbl
        # status text below water
        self.water_status_var = tk.StringVar()
        water_status_lbl = tk.Label(parent, textvariable=self.water_status_var, font=("Segoe UI", 12), fg="red")
        water_status_lbl.pack()
        self.water_status_lbl = water_status_lbl
        btn_drink = tk.Button(parent, text="Drink", font=self.font_small, width=12, command=self.increment_water)
        btn_drink.pack(pady=6)
        btn_reset = tk.Button(parent, text="Reset Water", font=("Segoe UI",10), command=self.reset_water)
        btn_reset.pack(pady=(0,10))

        # Medications
        lblm = tk.Label(parent, text="Medications", font=("Segoe UI", 18, "bold"))
        lblm.pack(pady=(10,4))
        self.med_vars = {}
        self.med_hist_widgets = {}
        for med in self.medications:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, pady=2, padx=6)
            mlabel = tk.Label(frame, text=med.get("name"), font=self.font_med)
            mlabel.pack(side=tk.LEFT)
            # determine checked state defensively (older logs may lack keys)
            meds_state = self.log.get("_meds") if isinstance(self.log.get("_meds"), dict) else {}
            mid = med.get("id")
            last_taken = ""
            if mid is not None:
                taken_list = meds_state.get(mid, {}).get("taken") or []
                if isinstance(taken_list, list) and taken_list:
                    try:
                        # show last taken as HH:MM
                        lt = datetime.datetime.fromisoformat(taken_list[-1])
                        last_taken = lt.strftime("%H:%M")
                    except Exception:
                        last_taken = ""
            var = tk.StringVar(master=self.root, value=(last_taken if last_taken else ""))
            mchk = tk.Label(frame, textvariable=var, font=("Segoe UI", 20), width=3)
            mchk.pack(side=tk.RIGHT)
            mbtn = tk.Button(frame, text="Taken", font=("Segoe UI",10), command=lambda mid=med.get("id"): self.record_med_taken(mid))
            mbtn.pack(side=tk.RIGHT, padx=6)
            self.med_vars[med.get("id")] = var
            # history listbox under the medication row
            hist = tk.Listbox(parent, height=4, font=("Segoe UI",10))
            hist.pack(fill=tk.X, padx=12, pady=(0,8))
            self.med_hist_widgets[med.get("id")] = hist
            # populate history from log
            taken_list = self.log.get("_meds", {}).get(med.get("id"), {}).get("taken") or []
            for t in taken_list:
                try:
                    txt = datetime.datetime.fromisoformat(t).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    txt = str(t)
                hist.insert(tk.END, txt)
        # Other meds recorder
        lblo = tk.Label(parent, text="Other Medication", font=("Segoe UI", 16, "bold"))
        lblo.pack(pady=(8,4))
        btn_other = tk.Button(parent, text="Record Other Med", font=self.font_small, command=self.record_other_med)
        btn_other.pack(pady=(0,6))
        self.other_med_hist = tk.Listbox(parent, height=6, font=("Segoe UI",10))
        self.other_med_hist.pack(fill=tk.X, padx=6, pady=(0,8))
        # populate other med history
        other_list = self.log.get("_other_meds", []) or []
        for rec in other_list:
            try:
                name = rec.get("name", "")
                txt = f"{rec.get('ts','')} - {name}"
            except Exception:
                txt = str(rec)
            self.other_med_hist.insert(tk.END, txt)

    def edit_note(self, item):
        cur = self.log.get(item["id"], {})
        initial = cur.get("note", "")
        note = simpledialog.askstring("Note for " + item["title"], "Enter note:", initialvalue=initial, parent=self.root)
        if note is not None:
            self.log[item["id"]]["note"] = note
            self.save_log()

    def apply_overrides(self):
        """Merge any overrides for today's weekday into `self.schedule`.
        Expects overrides format: config['overrides']["Monday"].get('extra', [ ... ])
        """
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

    def build_schedule_rows(self):
        # clear existing rows
        for c in list(self.frame.winfo_children()):
            c.destroy()
        self.row_widgets = {}
        for idx, item in enumerate(self.schedule):
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

            btn_note = tk.Button(row, text="Notes", font=self.font_small, width=10, command=lambda i=item: self.edit_note(i))
            btn_note.pack(side=tk.RIGHT, padx=6)

            btn_check = tk.Button(row, text="Check", font=self.font_small, width=10, command=lambda i=item: self.toggle_check(i))
            btn_check.pack(side=tk.RIGHT)

            self.row_widgets[item.get("id")] = {"frame": row, "check_var": chk_text}
            

    def update_water_var(self):
        w = self.log.get("_water", {})
        cnt = w.get("count", 0)
        goal = w.get("goal", self.water_goal)
        self.water_var.set(f"{cnt} / {goal} bottles")
        # update status text and highlight after changing water var
        try:
            self.update_water_status()
        except Exception:
            pass

    def update_water_status(self):
        w = self.log.get("_water", {})
        cnt = w.get("count", 0)
        now = datetime.datetime.now()
        # default: clear status and normal background
        status = ""
        bg = DEFAULT_HIGHLIGHT
        # before 14:00 require at least 1
        if now.time() < datetime.time(14, 0) and cnt < 1:
            status = "Behind on water: need 1 bottle before 14:00"
            bg = OUTSTANDING_BG
        # at/after 21:00 require at least 2
        elif now.time() >= datetime.time(21, 0) and cnt < 2:
            status = "Behind on water: need 2 bottles by 21:00"
            bg = OUTSTANDING_BG
        # apply
        if hasattr(self, "water_status_var"):
            self.water_status_var.set(status)
        if hasattr(self, "water_label_widget"):
            try:
                self.water_label_widget.configure(bg=bg)
            except Exception:
                pass
        if hasattr(self, "water_status_lbl"):
            try:
                self.water_status_lbl.configure(bg=bg)
            except Exception:
                pass
        # update block flag in case water status impacts outstanding state
        try:
            self.update_outstanding_flag()
        except Exception:
            pass

    def increment_water(self):
        entry = self.log.setdefault("_water", {"count": 0, "goal": self.water_goal})
        # allow recording more than the goal (unlimited)
        entry["count"] = entry.get("count", 0) + 1
        entry.setdefault("entries", []).append(datetime.datetime.now().isoformat())
        self.save_log()
        self.update_water_var()

    def reset_water(self):
        entry = self.log.setdefault("_water", {"count": 0, "goal": self.water_goal})
        entry["count"] = 0
        entry["entries"] = []
        self.save_log()
        self.update_water_var()

    def toggle_med(self, med_id):
        # legacy toggle kept to avoid breaking calls; treat as record
        self.record_med_taken(med_id)

    def record_med_taken(self, med_id):
        meds = self.log.setdefault("_meds", {})
        cur = meds.setdefault(med_id, {"taken": []})
        # append ISO timestamp
        ts = datetime.datetime.now().isoformat()
        if not isinstance(cur.get("taken"), list):
            cur["taken"] = []
            # refresh other meds history
            if hasattr(self, "other_med_hist") and self.other_med_hist is not None:
                self.other_med_hist.delete(0, tk.END)
                other_list = self.log.get("_other_meds", []) or []
                for rec in other_list:
                    try:
                        txt = f"{rec.get('ts','')} - {rec.get('name','')}"
                    except Exception:
                        txt = str(rec)
                    self.other_med_hist.insert(tk.END, txt)
        cur["taken"].append(ts)
        # update UI with last taken time
        v = self.med_vars.get(med_id)
        if v is not None:
            try:
                lt = datetime.datetime.fromisoformat(ts)
                v.set(lt.strftime("%H:%M"))
            except Exception:
                v.set("")
        # also append to history widget if present
        hist = self.med_hist_widgets.get(med_id)
        if hist is not None:
            try:
                hist.insert(tk.END, datetime.datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S"))
            except Exception:
                hist.insert(tk.END, ts)
        self.save_log()

    def record_other_med(self):
        kind = simpledialog.askstring("Other medication", "What kind?", parent=self.root)
        if not kind:
            return
        recs = self.log.setdefault("_other_meds", [])
        ts = datetime.datetime.now().isoformat()
        rec = {"name": kind, "ts": ts}
        recs.append(rec)
        # update listbox
        if hasattr(self, "other_med_hist") and self.other_med_hist is not None:
            try:
                txt = f"{ts} - {kind}"
                self.other_med_hist.insert(tk.END, txt)
            except Exception:
                pass
        self.save_log()

    def toggle_check(self, item):
        cur = self.log.setdefault(item["id"], {"checked": False, "note": ""})
        cur["checked"] = not cur.get("checked", False)
        # update UI
        self.row_widgets[item["id"]]["check_var"].set("✓" if cur["checked"] else "")
        self.save_log()
        # update outstanding flag since a check changed
        try:
            self.update_outstanding_flag()
        except Exception:
            pass

    def clear_today(self):
        if not messagebox.askyesno("Clear", "Clear all checks for today?", parent=self.root):
            return
        for k in self.log.keys():
            self.log[k]["checked"] = False
            self.log[k]["note"] = ""
            w = self.row_widgets.get(k)
            if w:
                w["check_var"].set("")
        self.save_log()

    def export_today(self):
        p = self.log_path(self.today)
        # copy to export folder for archival
        try:
            if p.exists():
                shutil.copy2(p, EXPORT_DIR / p.name)
            messagebox.showinfo("Exported", f"Log exported: {p}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Export failed", str(e), parent=self.root)

    def current_item(self):
        now = datetime.datetime.now().time()
        cur = None
        for item in self.schedule:
            if item["time"] <= now:
                cur = item
            else:
                break
        return cur

    def update_clock(self):
        if not self.running:
            return
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A %d %b %Y"))
        # reload if day changed
        if now.date() != self.today:
            self.today = now.date()
            self.log = self.load_log(self.today)
            # update check marks
            for item in self.schedule:
                chk = self.log.get(item["id"], {}).get("checked")
                self.row_widgets[item["id"]]["check_var"].set("✓" if chk else "")
            # update water and meds UI
            if hasattr(self, "water_var"):
                self.update_water_var()
            if hasattr(self, "med_vars"):
                for mid, var in self.med_vars.items():
                        # show last taken time or blank, and update history listbox
                        taken_list = self.log.get("_meds", {}).get(mid, {}).get("taken") or []
                        last = ""
                        if isinstance(taken_list, list) and taken_list:
                            try:
                                last = datetime.datetime.fromisoformat(taken_list[-1]).strftime("%H:%M")
                            except Exception:
                                last = ""
                        var.set(last)
                        hist = self.med_hist_widgets.get(mid)
                        if hist is not None:
                            hist.delete(0, tk.END)
                            for t in taken_list:
                                try:
                                    txt = datetime.datetime.fromisoformat(t).strftime("%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    txt = str(t)
                                hist.insert(tk.END, txt)
            # update water and meds UI
            if hasattr(self, "water_var"):
                self.update_water_var()
            if hasattr(self, "med_vars"):
                for mid, var in self.med_vars.items():
                    taken_list = self.log.get("_meds", {}).get(mid, {}).get("taken") or []
                    last = ""
                    if isinstance(taken_list, list) and taken_list:
                        try:
                            last = datetime.datetime.fromisoformat(taken_list[-1]).strftime("%H:%M")
                        except Exception:
                            last = ""
                    var.set(last)
        self.root.after(1000, self.update_clock)

    def update_highlight(self):
        cur = self.current_item()
        now_time = datetime.datetime.now().time()
        for item in self.schedule:
            item_id = item.get("id")
            w = self.row_widgets.get(item_id, {}).get("frame")
            if not w:
                continue
            # determine checked state
            checked = bool(self.log.get(item_id, {}).get("checked"))
            # current item highlights first
            if cur and item_id == cur.get("id"):
                bg = CURRENT_BG
            else:
                # outstanding: scheduled earlier today and not checked
                item_time = item.get("time")
                if item_time and (item_time < now_time) and (not checked):
                    bg = OUTSTANDING_BG
                else:
                    bg = DEFAULT_HIGHLIGHT
            w.configure(bg=bg)
            for child in w.winfo_children():
                try:
                    child.configure(bg=bg)
                except Exception:
                    pass
        # update block flag after highlighting decisions
        try:
            self.update_outstanding_flag()
        except Exception:
            pass
        # schedule next highlight update
        if self.running:
            self.root.after(5000, self.update_highlight)

    def schedule_midnight(self):
        now = datetime.datetime.now()
        next_midnight = datetime.datetime.combine((now + datetime.timedelta(days=1)).date(), datetime.time.min)
        ms = int((next_midnight - now).total_seconds() * 1000)
        # schedule the midnight handler
        self.root.after(ms, self._midnight_handler)

    def update_outstanding_flag(self):
        """Create or remove the schedule block flag file depending on whether outstanding items exist and feature enabled."""
        try:
            if not self.block_feature_enabled:
                # ensure flag removed
                if BLOCK_FLAG.exists():
                    BLOCK_FLAG.unlink()
                return

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

            if has_outstanding:
                # touch flag file
                BLOCK_FLAG.write_text("outstanding", encoding="utf-8")
            else:
                if BLOCK_FLAG.exists():
                    BLOCK_FLAG.unlink()
        except Exception:
            pass

    def _midnight_handler(self):
        try:
            # ensure current day's log is saved
            self.save_log()
            # copy the saved log to exports for archival
            p = self.log_path(self.today)
            if p.exists():
                try:
                    shutil.copy2(p, EXPORT_DIR / p.name)
                except Exception:
                    pass
            # advance to next day and load fresh log
            self.today = self.today + datetime.timedelta(days=1)
            self.log = self.load_log(self.today)
            # refresh UI check marks (cleared for new day)
            for item in self.schedule:
                chk = self.log.get(item["id"], {}).get("checked")
                self.row_widgets[item["id"]]["check_var"].set("✓" if chk else "")
        finally:
            # reschedule next midnight
            self.schedule_midnight()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.mainloop()
