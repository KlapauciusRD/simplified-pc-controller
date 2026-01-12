# AI Coding Agent Instructions

## Project Overview
This codebase consists of two Python scripts that integrate VLC media playback with Teams call monitoring:
- `runvlc.py`: Tkinter GUI controller for VLC player with video library management
- `teamscontroller.py`: Teams call monitor that auto-answers calls and coordinates with VLC

## Architecture
- **Inter-process Communication**: Uses a flag file (`c:/users/macka/skype_call_flag`) for communication between scripts
- **Polling-Based Design**: Teams controller polls window state and uses image recognition for call detection
- **Window Management**: Automatic hiding of VLC window during Teams calls using `pygetwindow`

## Key Components
- `VLCController` class: Manages VLC instance, playlists, and GUI controls with status monitoring
- Teams monitoring loop: Polls Teams window for incoming calls and call state
- Configuration system: JSON-based settings for paths, UI preferences, and behavior
- Status monitoring thread: Updates UI with playback progress, current media, and player state
- Flag monitoring thread: Runs continuously checking for Teams call state changes

## Critical Workflows
- **Running the System**: Execute both scripts simultaneously - `python runvlc.py` for GUI, `python teamscontroller.py` for monitoring
- **Video Library Structure**: Videos organized in configurable directories (default: `D:/video/series/` and `D:/video/movies/`)
- **Teams Integration**: Monitors call start/end via window title and image recognition, auto-answers calls
- **Configuration**: Settings stored in `vlc_config.json`, editable via Settings dialog

## Project-Specific Patterns
- **Path Handling**: Use `pathlib.Path` for all file operations, configurable absolute paths for media directories
- **GUI Layout**: Right-side panel with status display, progress bar, volume control, and large buttons (configurable font size)
- **Playlist Management**: Random shuffling for quick access buttons, full random playlist from all series
- **Quick Access Reshuffling**: "Reshuffle Shows" button randomly selects new shows for quick access buttons
- **Window Control**: Direct manipulation of VLC and Teams windows using `pygetwindow` and `pyautogui`
- **Image Recognition**: Uses `pyautogui.locateOnScreen()` for detecting Teams UI elements like answer button
- **Configuration Management**: JSON config file with defaults, loaded on startup and saved via Settings dialog
- **Status Monitoring**: Background thread updates UI with real-time playback information
- **Subtitle Support**: Automatic subtitle downloading from OpenSubtitles.org when videos start playing
- **Error Handling**: Comprehensive try-catch blocks with logging to `vlc_controller.log`
- **Resume Playback**: Automatic position saving and restoration when configured
- **Simplicity First**: Large, clearly labeled buttons only - no keyboard shortcuts or complex interactions

## Dependencies & Environment
- Requires VLC installed with Python bindings
- Microsoft Teams desktop app must be running and visible
- Reference image `answer_button.png` needed for call answering automation
- Optional: `subliminal` library for advanced subtitle downloading
- Windows-specific window management APIs
- Screen geometry calculations for multi-monitor setup
- Configuration file `vlc_config.json` created automatically

## Development Notes
- Scripts run independently but coordinate via filesystem flag
- GUI is borderless and always-on-top for media center usage
- Video extensions: `.mp4`, `.avi`, `.mkv`, `.flv`, `.mov`, `.wmv`, `.mpg`, `.mpeg`
- Teams automation requires UI calibration for different screen resolutions
- Subtitle downloading runs in background threads to avoid blocking UI
- Logging provides debugging information in `vlc_controller.log`
- Settings changes may require restart for full effect
- **User Interface Priority**: Keep interactions extremely simple - large buttons, clear labels, minimal options

## Common Tasks
- **Adding Media Controls**: Extend `VLCController.create_gui()` with new buttons calling player methods
- **Modifying Directories**: Update paths via Settings dialog or edit `vlc_config.json`
- **Teams Event Handling**: Adjust `is_call_incoming()` and `is_call_active()` for Teams UI changes
- **Window Behavior**: Adjust `hide()` and `make_fullscreen()` for different UI requirements
- **UI Calibration**: Update coordinates in `make_own_face_big_macro()` for Teams interface
- **Adding Features**: Use config system for new settings, add UI elements to `create_gui()`
- **Quick Access Management**: Modify `load_media_options()` and `reshuffle_quick_access()` for different show selection logic
- **Subtitle Integration**: Modify `download_subtitles()` for different subtitle sources
- **Maintaining Simplicity**: Always prioritize large, clearly labeled buttons over shortcuts or complex features</content>
<parameter name="filePath">c:\Users\chris williams\Downloads\liz\.github\copilot-instructions.md