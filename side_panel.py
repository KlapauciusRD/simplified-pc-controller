"""
Side panel with water tracking, medications, notes, and Teams quick-call buttons.
"""

import datetime
import tkinter as tk
from tkinter import messagebox


class SidePanel:
    """Side panel with water, meds, notes, and quick calls"""
    
    def __init__(self, parent, schedule_panel, coordinator, config):
        self.parent = parent
        self.schedule_panel = schedule_panel
        self.coordinator = coordinator
        self.config = config
        
        self.side_label_font = ("Segoe UI", 14, "bold")
        self.side_med_font = ("Segoe UI", 12)
        self.side_small_font = ("Segoe UI", 10)
        
        self.build_ui()
    
    def build_ui(self):
        # Water tracker
        lbl = tk.Label(self.parent, text="Water", font=self.side_label_font)
        lbl.pack(pady=(6, 4))
        
        self.water_var = tk.StringVar()
        self.update_water_var()
        water_lbl = tk.Label(self.parent, textvariable=self.water_var, font=self.side_med_font)
        water_lbl.pack()
        
        btn_drink = tk.Button(self.parent, text="Drink", font=self.side_small_font, width=12,
                            command=self.increment_water)
        btn_drink.pack(pady=6)
        
        # Medications
        lblm = tk.Label(self.parent, text="Medications", font=self.side_label_font)
        lblm.pack(pady=(10, 4))
        
        self.med_vars = {}
        for med in self.schedule_panel.medications:
            frame = tk.Frame(self.parent)
            frame.pack(fill=tk.X, pady=2, padx=6)
            
            mlabel = tk.Label(frame, text=med.get("name"), font=self.side_med_font)
            mlabel.pack(side=tk.LEFT)
            
            mid = med.get("id")
            taken_list = self.schedule_panel.log.get("_meds", {}).get(mid, {}).get("taken") or []
            last_taken = ""
            if isinstance(taken_list, list) and taken_list:
                try:
                    lt = datetime.datetime.fromisoformat(taken_list[-1])
                    last_taken = lt.strftime("%H:%M")
                except Exception:
                    pass
            
            var = tk.StringVar(value=last_taken)
            mchk = tk.Label(frame, textvariable=var, font=("Segoe UI", 14), width=3)
            mchk.pack(side=tk.RIGHT)
            
            mbtn = tk.Button(frame, text="Taken", font=self.side_small_font,
                           command=lambda mid=mid: self.record_med_taken(mid))
            mbtn.pack(side=tk.RIGHT, padx=6)
            
            self.med_vars[mid] = var
        
        # Notes for today
        lbl_notes = tk.Label(self.parent, text="Notes for Today", font=self.side_label_font)
        lbl_notes.pack(pady=(8, 4))
        
        self.notes_text = tk.Text(self.parent, height=5, font=("Segoe UI", 11))
        self.notes_text.pack(fill=tk.X, padx=6, pady=(0, 8))
        
        try:
            self.notes_text.insert("1.0", self.schedule_panel.log.get("_today_notes", ""))
        except Exception:
            pass
        
        self._notes_autosave_after_id = None
        self.notes_text.bind('<KeyRelease>', lambda e: self._on_notes_change())
        self.notes_text.bind('<FocusOut>', lambda e: self.save_today_notes())
        
        # Quick Teams calls
        lbl_calls = tk.Label(self.parent, text="Quick Calls", font=self.side_label_font)
        lbl_calls.pack(pady=(8, 4))
        
        calls_frame = tk.Frame(self.parent)
        calls_frame.pack(fill=tk.X, padx=6, pady=(0, 8))
        
        quick_calls = self.config.get("quick_calls", []) or []
        while len(quick_calls) < 4:
            quick_calls.append(None)
        
        for i in range(4):
            cfg = quick_calls[i]
            name = cfg.get("name") if isinstance(cfg, dict) and cfg.get("name") else f"Call {i+1}"
            btn = tk.Button(calls_frame, text=name, font=("Segoe UI", 10), width=10,
                          command=lambda cfg=cfg, idx=i: self.start_teams_call(cfg, idx))
            btn.grid(row=0, column=i, padx=4)
    
    def update_water_var(self):
        w = self.schedule_panel.log.get("_water", {})
        cnt = w.get("count", 0)
        goal = w.get("goal", self.schedule_panel.water_goal)
        self.water_var.set(f"{cnt} / {goal} bottles")
    
    def increment_water(self):
        entry = self.schedule_panel.log.setdefault("_water",
                                                   {"count": 0, "goal": self.schedule_panel.water_goal})
        entry["count"] = entry.get("count", 0) + 1
        entry.setdefault("entries", []).append(datetime.datetime.now().isoformat())
        self.schedule_panel.save_log()
        self.update_water_var()
    
    def record_med_taken(self, med_id):
        meds = self.schedule_panel.log.setdefault("_meds", {})
        cur = meds.setdefault(med_id, {"taken": []})
        ts = datetime.datetime.now().isoformat()
        
        if not isinstance(cur.get("taken"), list):
            cur["taken"] = []
        cur["taken"].append(ts)
        
        v = self.med_vars.get(med_id)
        if v:
            try:
                lt = datetime.datetime.fromisoformat(ts)
                v.set(lt.strftime("%H:%M"))
            except Exception:
                pass
        
        self.schedule_panel.save_log()
    
    def save_today_notes(self):
        try:
            if getattr(self, '_notes_autosave_after_id', None):
                try:
                    self.parent.after_cancel(self._notes_autosave_after_id)
                except Exception:
                    pass
                self._notes_autosave_after_id = None
        except Exception:
            pass
        
        try:
            txt = self.notes_text.get("1.0", tk.END).strip()
            self.schedule_panel.log["_today_notes"] = txt
            self.schedule_panel.save_log()
        except Exception:
            pass
    
    def _on_notes_change(self):
        try:
            if getattr(self, '_notes_autosave_after_id', None):
                try:
                    self.parent.after_cancel(self._notes_autosave_after_id)
                except Exception:
                    pass
            self._notes_autosave_after_id = self.parent.after(1500, self._autosave_notes)
        except Exception:
            pass
    
    def _autosave_notes(self):
        self._notes_autosave_after_id = None
        try:
            txt = self.notes_text.get("1.0", tk.END).strip()
            if txt != self.schedule_panel.log.get("_today_notes", ""):
                self.schedule_panel.log["_today_notes"] = txt
                self.schedule_panel.save_log()
        except Exception:
            pass
    
    def start_teams_call(self, cfg, idx):
        if not cfg:
            messagebox.showinfo("Not configured",
                              f"No target configured for Call {idx+1}.\n\n"
                              "Add a `quick_calls` entry in config.json with users or url.",
                              parent=self.parent)
            return
        
        self.coordinator.request_call(cfg)
        messagebox.showinfo("Call requested",
                          f"Teams call requested. Auto-join will attempt to connect.",
                          parent=self.parent)
