Schedule App

- Files added:
  - schedule.json: default daily schedule configuration
  - schedule_app.py: touchscreen-friendly Tkinter app to view and check off activities
  - schedule_logs/: directory created at first run to store per-day logs

Run

Open a terminal and run:

```bash
python schedule_app.py
```

Features

- Shows current date and time, highlights current scheduled activity
- Large buttons for touchscreens: `Check`, `Notes`, `Clear Today Checks`, `Export Today Log`
- Persists checks and notes in `schedule_logs/YYYY-MM-DD.json`
- Configuration in `schedule.json` can be edited to change times/titles

Next steps

- Add remote overrides (API stub placeholder in code)
- Integrate into the existing app set or add a launcher button
