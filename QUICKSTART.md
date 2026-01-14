# Quick Start Guide

## Getting Started with Daily Assistant

### 1. Install Dependencies
```bash
pip install python-vlc pygetwindow pyautogui
```

### 2. Migrate Configuration (if upgrading)
If you have existing `schedule.json` or `vlc_config.json`:
```bash
python migrate_config.py
```

This will create a unified `config.json` file.

### 3. Configure Settings
Edit `config.json`:

```json
{
  "schedule": [
    {"time": "06:00", "title": "Wake Up"},
    {"time": "09:00", "title": "Start Work"}
  ],
  "teams_buttons": [
    {"label": "Mom", "url": "https://teams.microsoft.com/l/meetup-join/..."}
  ],
  "series_dir": "D:/video/series",
  "movies_dir": "D:/video/movies"
}
```

**Important**: Update Teams button URLs with your actual meeting links.

### 4. Run the Application
```bash
python daily_assistant.py
```

## First Time Setup Checklist

- [ ] Install Python 3.8+
- [ ] Install dependencies (`pip install python-vlc pygetwindow pyautogui`)
- [ ] Create or migrate `config.json`
- [ ] Update Teams meeting URLs
- [ ] Verify video directories exist
- [ ] Test schedule display
- [ ] Test water/medication tracking
- [ ] Test Teams call buttons
- [ ] Test VLC media playback

## Daily Usage

### Schedule Tab
1. **Check items** as you complete them throughout the day
2. **Add notes** for any item by clicking the note button
3. **Track water** by clicking the water cup icon
4. **Record medications** using the medication tracking section
5. **Add daily notes** in the text box (auto-saves)
6. **Make Teams calls** using the quick-call buttons

### Media Tab
1. **Select series/movies** from dropdown or quick access
2. **Use playback controls** (play, pause, skip, rewind)
3. **Adjust volume** with slider
4. **Reshuffle quick access** to see different shows
5. **Random playlist** plays random episodes from all series

### Key Features
- Schedule highlights current time in green
- Outstanding items (past time, not checked) show in yellow
- VLC automatically pauses when:
  - You have outstanding schedule items
  - A Teams call is active
- All data persists per day in `schedule_logs/`

## Troubleshooting

### Can't play videos
- Check that outstanding items are cleared (no yellow highlights)
- Ensure no active Teams call
- Verify VLC is installed and media directories exist

### Teams buttons don't work
- Verify Teams URLs are correct in `config.json`
- Ensure Microsoft Teams app is installed
- Check `daily_assistant.log` for errors

### Configuration errors
- Validate `config.json` is proper JSON format
- Check all paths use forward slashes or escaped backslashes
- Review default config in README.md

## Tips

- Use **fullscreen mode** for a dedicated media center experience
- Adjust **font_size** in config for better touchscreen visibility
- Keep Teams meeting URLs in config for regular video calls
- Use **weekday_overrides** for recurring weekly events
- Check the log file (`daily_assistant.log`) for debugging

## Support

Review the full [README.md](README.md) for detailed documentation.
Check logs in `daily_assistant.log` for error details.
