# Architecture Migration Summary

## What Changed

### From: Multi-Process with File-Based IPC
**Old Structure:**
- `schedule_app.py` - Schedule UI (standalone)
- `runvlc.py` - VLC controller (standalone)
- `teamscontroller.py` - Teams monitor (standalone)
- Communication via flag files:
  - `schedule_block.flag` - Schedule blocks VLC
  - `teams_call_request.json` - UI requests Teams calls
  - `skype_call_flag` - Teams blocks VLC

**Problems:**
- Race conditions from file polling
- Delayed coordination (polling intervals)
- Brittle inter-process communication
- Configuration scattered across files
- No shared state management

### To: Single-Process Modular Architecture
**New Structure:**
- `daily_assistant.py` - Main entry point, window setup
- `coordinator.py` - Thread-safe state manager
- `schedule_panel.py` - Schedule UI module
- `side_panel.py` - Water/meds/notes/Teams UI module
- `media_panel.py` - VLC controller module
- `teams_monitor.py` - Teams monitoring module
- `config.json` - Unified configuration

**Benefits:**
- Direct method calls (no polling)
- Immediate coordination
- Thread-safe shared state
- Modular code organization
- Single configuration file
- Maintainable architecture

## Component Mapping

### coordinator.py (NEW)
**Purpose:** Central state manager with thread-safe operations

**Replaced:**
- `schedule_block.flag` file → `set_outstanding(bool)`
- `teams_call_request.json` → `request_call(url)` + queue
- `skype_call_flag` → `set_call_active(bool)`

**Key Methods:**
- `can_play_media()` - Check if VLC can play (replaces flag file checking)
- `register_vlc_controller()` - Register VLC for automatic pause
- `get_pending_calls()` - Get queued call requests (replaces file read)

### schedule_panel.py
**Extracted from:** `schedule_app.py` (SchedulePanel class)

**Changes:**
- Uses `coordinator.set_outstanding()` instead of writing flag file
- Receives coordinator in constructor
- Otherwise identical functionality

### side_panel.py
**Extracted from:** `schedule_app.py` (SidePanel class)

**Changes:**
- Uses `coordinator.request_call()` instead of writing JSON file
- Receives coordinator in constructor
- Otherwise identical functionality

### media_panel.py
**Adapted from:** `runvlc.py` (VLCController class)

**Changes:**
- Removed `start_schedule_block_monitor()` method (no flag polling)
- `play()` checks `coordinator.can_play_media()` instead of flag file
- Registers with coordinator via `register_vlc_controller()`
- Coordinator calls `pause()` directly when needed
- Simplified status monitoring (no flag polling)

### teams_monitor.py
**Adapted from:** `teamscontroller.py`

**Changes:**
- Background thread instead of standalone process
- Uses `coordinator.get_pending_calls()` instead of reading JSON file
- Uses `coordinator.set_call_active()` instead of writing flag file
- Started/stopped by main app

### daily_assistant.py
**Evolved from:** `main_app.py` (consolidated version)

**Changes:**
- Imports modular components instead of embedding classes
- Lighter weight orchestration
- Tabbed interface layout
- Single `config.json` management

## Configuration Consolidation

### Before
**schedule.json:**
```json
{
  "schedule": [...],
  "water_goal": 8,
  "medication_schedule": [...],
  "teams_buttons": [...]
}
```

**vlc_config.json:**
```json
{
  "series_dir": "D:/video/series",
  "movies_dir": "D:/video/movies",
  "auto_resume": true
}
```

### After
**config.json:**
```json
{
  "schedule": [...],
  "water_goal": 8,
  "medication_schedule": [...],
  "teams_buttons": [...],
  "series_dir": "D:/video/series",
  "movies_dir": "D:/video/movies",
  "auto_resume": true,
  "fullscreen": false,
  "font_size": 14
}
```

**Migration:** Use `migrate_config.py` to consolidate old configs

## File Status

### Active Files (New Architecture)
- ✅ `daily_assistant.py` - Main entry point
- ✅ `coordinator.py` - State manager
- ✅ `schedule_panel.py` - Schedule UI
- ✅ `side_panel.py` - Side panel UI
- ✅ `media_panel.py` - VLC controls
- ✅ `teams_monitor.py` - Teams automation
- ✅ `config.json` - Unified config
- ✅ `migrate_config.py` - Config migration tool

### Legacy Files (Keep for Reference)
- 📁 `schedule_app.py` - Original schedule app
- 📁 `runvlc.py` - Original VLC controller
- 📁 `teamscontroller.py` - Original Teams monitor
- 📁 `main_app.py` - Consolidated single-file version
- 📁 `schedule.json` - Old schedule config
- 📁 `vlc_config.json` - Old VLC config

### Documentation
- 📖 `README.md` - Complete documentation
- 📖 `QUICKSTART.md` - Quick start guide
- 📖 `MIGRATION.md` - This document

### Data Directories (Preserved)
- 📂 `schedule_logs/` - Daily data files (compatible)
- 📂 `schedule_exports/` - Midnight exports (compatible)

## Migration Path

### For Existing Users
1. **Backup existing data:**
   ```bash
   # Logs and exports are preserved automatically
   ```

2. **Migrate configuration:**
   ```bash
   python migrate_config.py
   ```

3. **Update config:**
   - Edit `config.json`
   - Update Teams URLs
   - Verify media directories

4. **Test new app:**
   ```bash
   python daily_assistant.py
   ```

5. **Verify functionality:**
   - Check schedule display
   - Test water/med tracking
   - Test Teams calls
   - Test VLC playback
   - Verify outstanding item blocking
   - Verify call blocking

### For New Users
1. **Install dependencies:**
   ```bash
   pip install python-vlc pygetwindow pyautogui
   ```

2. **Run app (creates default config):**
   ```bash
   python daily_assistant.py
   ```

3. **Customize `config.json`**

## Technical Details

### Thread Safety
All coordinator methods use `threading.Lock`:
```python
def set_outstanding(self, value):
    with self.lock:
        self.outstanding_items = value
```

### Automatic VLC Coordination
Coordinator registers VLC controller and pauses automatically:
```python
def register_vlc_controller(self, controller):
    self.vlc_controller = controller

def set_outstanding(self, value):
    with self.lock:
        self.outstanding_items = value
        if value and self.vlc_controller:
            self.vlc_controller.pause()
```

### Call Request Queue
Thread-safe queue replaces JSON file:
```python
def request_call(self, url):
    with self.lock:
        self.pending_calls.append(url)

def get_pending_calls(self):
    with self.lock:
        calls = self.pending_calls.copy()
        self.pending_calls.clear()
        return calls
```

## Benefits Realized

### Performance
- ❌ File polling every 1-2 seconds
- ✅ Immediate method calls
- ❌ Disk I/O for coordination
- ✅ In-memory state

### Reliability
- ❌ Race conditions possible
- ✅ Thread-safe operations
- ❌ File corruption risk
- ✅ Atomic updates

### Maintainability
- ❌ Single 750+ line file or scattered processes
- ✅ Modular components (~150-250 lines each)
- ❌ Multiple config files
- ✅ Single config file
- ❌ Duplicated logging setup
- ✅ Centralized logging

### User Experience
- ❌ Delayed VLC pause (1-2s polling)
- ✅ Instant VLC pause
- ❌ Separate windows to manage
- ✅ Unified tabbed interface
- ❌ Manual process coordination
- ✅ Automatic coordination

## Rollback Plan

If issues arise, old architecture still works:
1. Run individual scripts: `python schedule_app.py`, `python runvlc.py`, `python teamscontroller.py`
2. Use old config files: `schedule.json`, `vlc_config.json`
3. Flag files still supported by old scripts

## Future Enhancements
- Web API for remote schedule updates
- Mobile companion app
- Voice control integration
- Calendar sync (Google/Outlook)
- Medication reminder popups
- Smart home integration
