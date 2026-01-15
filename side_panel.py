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
        # Container for medication rows so we can add ad-hoc meds at runtime
        meds_frame = tk.Frame(self.parent)
        meds_frame.pack(fill=tk.X)
        self._meds_container = meds_frame

        # Render configured medications (defaults + any configured meds)
        for med in self.schedule_panel.medications:
            mid = med.get("id")
            name = med.get("name")
            self._create_med_row(mid, name)

        # Render ad-hoc other medications stored in today's log
        for om in self.schedule_panel.log.get("_other_meds", []):
            if isinstance(om, dict):
                mid = om.get("id")
                name = om.get("name")
            elif isinstance(om, str):
                name = om
                mid = om.strip().lower().replace(" ", "_")
            else:
                continue
            self._create_med_row(mid, name)

        # Add button to create a new ad-hoc medication and quick 'Other' recorder
        add_frame = tk.Frame(self.parent)
        add_frame.pack(fill=tk.X, padx=6, pady=(4, 8))

        other_btn = tk.Button(add_frame, text="Other", font=self.side_small_font,
                      command=self.record_other_quick)
        other_btn.pack(side=tk.LEFT, padx=6)

        # Visible log for ad-hoc 'other' medication records
        other_log_lbl = tk.Label(self.parent, text="Other Meds Log", font=self.side_small_font)
        other_log_lbl.pack(padx=6, anchor="w")
        self._other_log_text = tk.Text(self.parent, height=5, font=("Segoe UI", 9))
        self._other_log_text.pack(fill=tk.X, padx=6, pady=(0,8))
        # Load existing other meds entries into the log view
        for entry in self.schedule_panel.log.get("_other_meds_entries", []):
            try:
                ts = entry.get("ts")
                name = entry.get("name")
                t = datetime.datetime.fromisoformat(ts)
                self._other_log_text.insert(tk.END, f"{t.strftime('%H:%M')} - {name}\n")
            except Exception:
                pass

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

        # Update history display (if present)
        hist_var = getattr(self, 'med_history_vars', {}).get(med_id)
        if hist_var is not None:
            try:
                taken_list = self.schedule_panel.log.get("_meds", {}).get(med_id, {}).get("taken") or []
                last_items = []
                for tiso in taken_list[-5:]:
                    try:
                        t = datetime.datetime.fromisoformat(tiso)
                        last_items.append(t.strftime('%H:%M'))
                    except Exception:
                        pass
                hist_var.set(', '.join(last_items))
            except Exception:
                pass

    def add_other_med(self):
        """Prompt for a medication name and add it to today's other meds."""
        name = tk.simpledialog.askstring("Add Medication", "Medication name:", parent=self.parent)
        if not name:
            return
        mid = name.strip().lower().replace(" ", "_")

        # Ensure _other_meds exists and does not already contain this med
        other = self.schedule_panel.log.setdefault("_other_meds", [])
        if any((isinstance(x, dict) and x.get("id") == mid) or (isinstance(x, str) and x.strip().lower().replace(" ", "_") == mid) for x in other):
            messagebox.showinfo("Exists", "Medication already exists.", parent=self.parent)
            return

        other.append({"id": mid, "name": name.strip()})

        # Ensure there's an entry in _meds mapping for history
        meds_map = self.schedule_panel.log.setdefault("_meds", {})
        meds_map.setdefault(mid, {"taken": []})
        self.schedule_panel.save_log()

        # Create the UI row for the new med
        self._create_med_row(mid, name.strip())

    def record_other_quick(self):
        """Prompt for a medication name and record an ad-hoc administration immediately."""
        name = tk.simpledialog.askstring("Other Medication", "Medication taken (e.g. 'Paracetamol 500mg'):", parent=self.parent)
        if not name:
            return

        ts = datetime.datetime.now().isoformat()
        entries = self.schedule_panel.log.setdefault("_other_meds_entries", [])
        entries.append({"ts": ts, "name": name})
        self.schedule_panel.save_log()

        # Append to visible other meds log
        try:
            t = datetime.datetime.fromisoformat(ts)
            self._other_log_text.insert(tk.END, f"{t.strftime('%H:%M')} - {name}\n")
        except Exception:
            try:
                self._other_log_text.insert(tk.END, f"{ts} - {name}\n")
            except Exception:
                pass

    def _create_med_row(self, med_id, name):
        """Create a medication row in the meds container and register its var."""
        # Avoid duplicating rows
        if med_id in self.med_vars:
            return
        container = tk.Frame(self._meds_container)
        container.pack(fill=tk.X, pady=2, padx=6)

        top = tk.Frame(container)
        top.pack(fill=tk.X)

        mlabel = tk.Label(top, text=name, font=self.side_med_font)
        mlabel.pack(side=tk.LEFT)

        taken_list = self.schedule_panel.log.get("_meds", {}).get(med_id, {}).get("taken") or []
        last_taken = ""
        if isinstance(taken_list, list) and taken_list:
            try:
                lt = datetime.datetime.fromisoformat(taken_list[-1])
                last_taken = lt.strftime("%H:%M")
            except Exception:
                pass

        var = tk.StringVar(value=last_taken)
        mchk = tk.Label(top, textvariable=var, font=("Segoe UI", 14), width=3)
        mchk.pack(side=tk.RIGHT)

        mbtn = tk.Button(top, text="Taken", font=self.side_small_font,
                         command=lambda mid=med_id: self.record_med_taken(mid))
        mbtn.pack(side=tk.RIGHT, padx=6)

        # History label under the med row (shows recent administrations)
        hist_var = tk.StringVar()
        hist_label = tk.Label(container, textvariable=hist_var, font=self.side_small_font, anchor='w')
        hist_label.pack(fill=tk.X)

        # Initialize history value
        try:
            last_items = []
            for tiso in taken_list[-5:]:
                try:
                    t = datetime.datetime.fromisoformat(tiso)
                    last_items.append(t.strftime('%H:%M'))
                except Exception:
                    pass
            hist_var.set(', '.join(last_items))
        except Exception:
            hist_var.set('')

        self.med_vars[med_id] = var
        # Store history var for updates
        if not hasattr(self, 'med_history_vars'):
            self.med_history_vars = {}
        self.med_history_vars[med_id] = hist_var
    
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
                              "Add a `quick_calls` entry in config.json with 'name' and 'user' (email or Teams ID).",
                              parent=self.parent)
            return
        
        # Validate config has user identifier
        user = cfg.get('user') or cfg.get('email') or cfg.get('id')
        if not user:
            messagebox.showerror("Invalid config",
                              f"Call button {idx+1} needs a 'user', 'email', or 'id' field.\n\n"
                              "Example: {{\"name\": \"Mom\", \"user\": \"mom@example.com\"}}",
                              parent=self.parent)
            return
        
        name = cfg.get('name', user)
        self.coordinator.request_call(cfg)
