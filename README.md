# Daily Assistant - Modular Unified Application

## Overview
This is a touchscreen-friendly daily assistant application that combines:
- **Schedule Management**: Daily timeline with checkmarks, notes, and highlighting
- **Health Tracking**: Water intake and medication tracking with history
- **Teams Integration**: Quick-call buttons with auto-join capability
- **Media Controls**: VLC video player integration with playlist management

## Architecture

### Modular Design
The application uses a **coordinator pattern** with separate modules:

```
daily_assistant.py    # Main entry point, window setup, layout
coordinator.py        # Shared state manager (thread-safe)
schedule_panel.py     # Schedule timeline UI
side_panel.py         # Water, meds, notes, Teams buttons
media_panel.py        # VLC player controls
teams_monitor.py      # Background Teams call monitoring
```

### Key Features
- **Single Process**: All components run in one application
- **Direct Communication**: Components communicate via coordinator (no file polling)
- **Thread-Safe**: Proper locking for concurrent access
- **Automatic Coordination**: VLC pauses when schedule items outstanding or call active
- **Persistent Data**: Daily logs saved to `schedule_logs/YYYY-MM-DD.json`

## Installation

### Requirements
```bash
pip install python-vlc pygetwindow pyautogui
```

### Directory Structure
```
liz/
├── daily_assistant.py       # Main application
├── coordinator.py            # State coordinator
├── schedule_panel.py         # Schedule UI
├── side_panel.py            # Side panel UI
├── media_panel.py           # VLC controls
├── teams_monitor.py         # Teams automation
├── config.json              # Unified configuration
├── schedule_logs/           # Daily data files
└── schedule_exports/        # Midnight exports
```

## Configuration

### config.json
All settings are stored in a single `config.json` file:

```json
{
  "schedule": [
    {"time": "06:00", "title": "Wake Up"},
    {"time": "09:00", "title": "Morning Work"}
  ],
  "weekday_overrides": {
    "Tuesday": [{"time": "14:00", "title": "Team Meeting"}]
  },
  "water_goal": 8,
  "medication_schedule": ["Morning (08:00)", "Evening (20:00)"],
  "other_meds": ["Vitamin D"],
  "teams_buttons": [
    {"label": "Mom", "url": "https://teams.microsoft.com/l/..."}
  ],
  "series_dir": "D:/video/series",
  "movies_dir": "D:/video/movies",
  "auto_resume": true,
  "fullscreen": false,
  "font_size": 14
}
```

### Migrating from Old Setup
If you have existing `schedule.json` and `vlc_config.json`:

1. Merge settings into new `config.json` format
2. Existing `schedule_logs/` directory will continue to work
3. Update Teams button URLs in new config

## Usage

### Starting the Application
```bash
python daily_assistant.py
```

### Interface Layout

**Tab 1: Schedule & Tasks**
- Left (2/3): Schedule timeline with current time highlighting
- Right (1/3): Water tracking, medications, notes, Teams call buttons

**Tab 2: Media**
- VLC player controls
- Playlist selection (series/movies)
- Quick access buttons
- Volume and progress controls

### Key Behaviors

#### Automatic VLC Pausing
VLC automatically pauses when:
- Schedule items become outstanding (past their time and not checked)
- A Teams call is active

Resume by clearing outstanding items or ending the call.

#### Schedule Highlighting
- **Green**: Current time block
- **Yellow**: Outstanding items (past time, not checked)
- Auto-updates every minute

#### Daily Data Persistence
- Check marks, notes, water, and medication data saved per day
- Exports previous day at midnight to `schedule_exports/`

## Component Details

### AppCoordinator
Central state manager with thread-safe methods:
- `set_outstanding(bool)`: Mark outstanding schedule items
- `set_call_active(bool)`: Mark Teams call active
- `can_play_media()`: Check if VLC can play (no outstanding/call)
- `request_call(url)`: Queue Teams call request
- `register_vlc_controller(controller)`: Register VLC for automatic pause

### Schedule Panel
- Displays daily timeline
- Per-item checkmarks and notes
- Weekday-specific overrides
- Outstanding item detection
- Daily log persistence

### Side Panel
- Water intake counter (visual cups)
- Medication tracking with history
- Notes text box with autosave
- Teams call buttons (opens meetings)

### Media Panel
- Full VLC player integration
- Series and movie library browsing
- Random playlist generation
- Quick access shuffling
- Automatic subtitle downloading (if enabled)

### Teams Monitor
- Background thread monitoring Teams window state
- Processes call requests from UI buttons
- Auto-answers incoming calls (requires reference images)
- Detects active calls for VLC coordination

## Troubleshooting

### VLC Not Available
Install python-vlc:
```bash
pip install python-vlc
```

### Teams Automation Not Working
1. Install dependencies: `pip install pygetwindow pyautogui`
2. Create reference images: `join_button.png`, `answer_button.png`
3. UI automation is brittle - manual join may be needed

### Configuration Issues
- Check `config.json` is valid JSON
- Verify media directories exist
- Review `daily_assistant.log` for errors

### VLC Won't Play
- Check for outstanding schedule items (yellow highlights)
- Verify no active Teams call
- Review `can_play_media()` blocking reasons in log

## Development

### Adding Features
1. Identify appropriate module (schedule, side panel, media, etc.)
2. Add methods to the module class
3. Update coordinator if cross-component communication needed
4. Add configuration to `config.json` structure

### Modifying Layout
Edit `create_layout()` in `daily_assistant.py`:
- Adjust frame sizes for different proportions
- Add new tabs to notebook
- Modify widget placement

### Extending Coordinator
Add new state variables and methods to `coordinator.py`:
- Use `self.lock` for thread-safe updates
- Provide getter/setter methods
- Document behavior for consumers

## Future Enhancements
- Remote override capability (edit schedule from another device)
- Calendar integration (Google Calendar, Outlook)
- Voice commands for hands-free control
- Mobile companion app
- Medication reminder popups

## License
Personal use project - no license specified.
