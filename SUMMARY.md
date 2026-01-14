# Daily Assistant - Complete Modular Application

## What You Have Now

A touchscreen-friendly unified application with modular architecture that combines:
- **Schedule Management** - Daily timeline with persistence
- **Health Tracking** - Water and medication tracking
- **Teams Integration** - Quick-call buttons with auto-join
- **Media Controls** - VLC player with automatic coordination

## New Architecture

### Modular Components (6 files)
1. **daily_assistant.py** - Main entry point (180 lines)
2. **coordinator.py** - State manager (80 lines)
3. **schedule_panel.py** - Schedule UI (250 lines)
4. **side_panel.py** - Water/meds/Teams UI (200 lines)
5. **media_panel.py** - VLC controls (250 lines)
6. **teams_monitor.py** - Teams automation (150 lines)

### Benefits Over Old Architecture
✅ **Single process** - No more coordination via files  
✅ **Immediate coordination** - VLC pauses instantly  
✅ **Modular code** - Each component ~150-250 lines  
✅ **Thread-safe** - Proper locking for shared state  
✅ **Unified config** - Single config.json file  
✅ **Maintainable** - Clear separation of concerns  

## Quick Start

### Installation
```bash
# Run automated setup
setup.bat

# Or manual installation
pip install -r requirements.txt
python migrate_config.py  # If upgrading
python daily_assistant.py
```

### Configuration
Edit `config.json`:
- Update schedule items
- Add Teams meeting URLs
- Configure video directories
- Set water goals and medications

## Key Features

### Automatic Coordination
- VLC **automatically pauses** when:
  - Schedule items become outstanding (past time, not checked)
  - Teams call becomes active
- Resume by clearing outstanding items or ending call

### Data Persistence
- Check marks, notes, water, medications saved per day
- Daily logs: `schedule_logs/YYYY-MM-DD.json`
- Midnight exports: `schedule_exports/`

### Smart UI
- **Green highlight** - Current time block
- **Yellow highlight** - Outstanding items
- **Tabbed interface** - Schedule/Tasks + Media
- **2:1 layout** - Schedule (left) + Side panel (right)

## File Structure

```
liz/
├── daily_assistant.py       # Main app - START HERE
├── coordinator.py            # State manager
├── schedule_panel.py         # Schedule UI
├── side_panel.py            # Water/meds/notes/Teams
├── media_panel.py           # VLC player
├── teams_monitor.py         # Background Teams monitor
├── config.json              # Unified configuration
├── requirements.txt         # Python dependencies
├── setup.bat                # Windows setup script
├── migrate_config.py        # Config migration tool
├── README.md                # Full documentation
├── QUICKSTART.md            # Quick start guide
├── MIGRATION.md             # Architecture details
└── schedule_logs/           # Daily data files
```

## Legacy Files (Preserved)

These still work but are superseded by new architecture:
- `schedule_app.py` - Original schedule app
- `runvlc.py` - Original VLC controller  
- `teamscontroller.py` - Original Teams monitor
- `main_app.py` - Single-file consolidated version

## Documentation

- **README.md** - Complete feature documentation
- **QUICKSTART.md** - Step-by-step getting started
- **MIGRATION.md** - Architecture comparison & migration
- **This file** - Quick reference

## Common Tasks

### Running the App
```bash
python daily_assistant.py
```

### Updating Configuration
```json
// config.json
{
  "schedule": [
    {"time": "09:00", "title": "Work Start"}
  ],
  "teams_buttons": [
    {"label": "Mom", "url": "https://teams.microsoft.com/l/..."}
  ],
  "series_dir": "D:/video/series",
  "movies_dir": "D:/video/movies"
}
```

### Migrating from Old Setup
```bash
python migrate_config.py
```

### Adding Schedule Items
Edit `config.json` → `schedule` array

### Adding Teams Buttons
Edit `config.json` → `teams_buttons` array with meeting URLs

### Changing Video Directories
Edit `config.json` → `series_dir` and `movies_dir`

## Troubleshooting

**VLC won't play:**
- Clear outstanding schedule items (yellow highlights)
- End active Teams call
- Check `can_play_media()` in logs

**Teams buttons don't work:**
- Verify URLs in config.json
- Ensure Teams app installed
- Check daily_assistant.log

**Import errors:**
- Run: `pip install -r requirements.txt`
- VLC: `pip install python-vlc`
- Teams automation: `pip install pygetwindow pyautogui`

## Next Steps

1. ✅ Run `setup.bat` or install dependencies
2. ✅ Review and edit `config.json`
3. ✅ Update Teams URLs
4. ✅ Run `python daily_assistant.py`
5. ✅ Test all features
6. 🎉 Enjoy your unified daily assistant!

## Support

- Review logs: `daily_assistant.log`
- Check documentation: `README.md`
- Migration guide: `MIGRATION.md`
- Quick start: `QUICKSTART.md`
