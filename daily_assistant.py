"""
Daily Assistant - Unified touchscreen application
Combines schedule, Teams, and media controls in a single interface.
"""

import tkinter as tk
from tkinter import ttk
from screeninfo import get_monitors
import json
import logging
import sys
from pathlib import Path

# Import our modules
from coordinator import AppCoordinator
from schedule_panel import SchedulePanel
from side_panel import SidePanel
from media_panel import MediaPanel
from teams_monitor import TeamsMonitor

# Setup logging
logging.basicConfig(
    filename='daily_assistant.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class DailyAssistantApp:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Assistant")
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize coordinator
        self.coordinator = AppCoordinator()
        # Apply config to coordinator (e.g., pause_on_outstanding)
        try:
            self.coordinator.set_config(self.config)
        except Exception:
            pass
        
        # Setup UI
        self.setup_window()
        self.create_layout()
        
        # Start Teams monitor
        self.teams_monitor = TeamsMonitor(self.coordinator)
        self.teams_monitor.start()
        
        logging.info("Daily Assistant started")
    
    def load_config(self):
        """Load unified configuration"""
        config_path = Path('config.json').resolve()
        logging.info(f"Loading config from: {config_path}")
        logging.info(f"Config file exists: {config_path.exists()}")
        
        # Default configuration
        default_config = {
            # Schedule settings
            'schedule': [
                {"time": "06:00", "title": "Wake Up"},
                {"time": "07:00", "title": "Breakfast"},
                {"time": "09:00", "title": "Morning Work"},
                {"time": "12:00", "title": "Lunch"},
                {"time": "13:00", "title": "Afternoon Work"},
                {"time": "18:00", "title": "Dinner"},
                {"time": "22:00", "title": "Bedtime"}
            ],
            'weekday_overrides': {},
            'water_goal': 2,
            
            # Teams settings
            'teams_buttons': [
                {"label": "Mom", "url": ""},
                {"label": "Dad", "url": ""},
                {"label": "Work", "url": ""},
                {"label": "Friend", "url": ""}
            ],
            
            # VLC settings
            'series_dir': 'D:/video/series',
            'movies_dir': 'D:/video/movies',
            'auto_resume': True,
            
            # UI settings
            'fullscreen': True,
            'screen_index': 1,
            'font_size': 12
            ,
            # Coordinator behavior
            'pause_on_outstanding': True
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    logging.info(f"Loaded config keys: {loaded_config.keys()}")
                    logging.info(f"Loaded schedule items: {len(loaded_config.get('schedule', []))}")
                    logging.info(f"Loaded water_goal: {loaded_config.get('water_goal')}")
                    default_config.update(loaded_config)
                    logging.info(f"Config merged successfully")
            except Exception as e:
                logging.error(f"Error loading config: {e}", exc_info=True)
        else:
            # Save default config only if file doesn't exist
            self.save_config(default_config)
        
        # Log the resolved schedule for debugging (helps verify config is used)
        try:
            logging.info(f"Resolved schedule: {default_config.get('schedule')}")
            logging.info(f"Resolved water_goal: {default_config.get('water_goal')}")
        except Exception:
            pass
        
        return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def setup_window(self):
        """Configure main window"""
        try:
            monitors = get_monitors()
            # default to second monitor (index 1) if available
            idx = int(self.config.get('screen_index', 1))
            if monitors and 0 <= idx < len(monitors):
                screen = monitors[idx]
            elif monitors:
                screen = monitors[0]
            else:
                screen = None

            # Move window to selected monitor coordinates before fullscreen
            if screen:
                self.root.geometry(f"1x1+{screen.x}+{screen.y}")
                self._current_monitor = screen
            else:
                self._current_monitor = None

            if self.config.get('fullscreen', True):
                # ensure geometry update before toggling fullscreen
                self.root.update_idletasks()
                self.root.attributes('-fullscreen', True)
                # Make the window borderless to reclaim screen space
                try:
                    self.root.overrideredirect(True)
                except Exception:
                    pass
            else:
                self.root.geometry('1400x800')

            self.root.configure(bg='white')
        except Exception as e:
            logging.error(f"Error setting up window positioning: {e}")
            # Fallback
            if self.config.get('fullscreen', True):
                self.root.attributes('-fullscreen', True)
            else:
                self.root.geometry('1400x800')
            self.root.configure(bg='white')
    
    def create_layout(self):
        """Create main layout with schedule, side panel, and media"""
        # Main container
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Compute column widths from monitor if available (schedule 60%, side 20%, media 20%)
        monitor_w = None
        try:
            if hasattr(self, '_current_monitor') and self._current_monitor:
                monitor_w = int(self._current_monitor.width)
        except Exception:
            monitor_w = None

        if monitor_w:
            # Use 40/25/35 split: further reduce schedule and expand media panel
            sched_w = int(monitor_w * 0.40)
            side_w = int(monitor_w * 0.25)
            media_w = monitor_w - sched_w - side_w
        else:
            sched_w = None
            side_w = 350
            media_w = 350

        # Column 1: Schedule
        schedule_frame = tk.Frame(main_frame, bg='white', width=sched_w)
        schedule_frame.pack(side='left', fill='both', expand=(sched_w is None), padx=6, pady=6)
        if sched_w:
            schedule_frame.pack_propagate(False)
        self.schedule_panel = SchedulePanel(schedule_frame, self.coordinator, self.config)

        # Column 2: Side panel - water, meds, notes, Teams
        side_frame = tk.Frame(main_frame, bg='lightgray', width=side_w)
        side_frame.pack(side='left', fill='both', padx=6, pady=6)
        side_frame.pack_propagate(False)
        self.side_panel = SidePanel(side_frame, self.schedule_panel, self.coordinator, self.config)

        # Column 3: Media controls
        media_frame = tk.Frame(main_frame, bg='white', width=media_w)
        media_frame.pack(side='left', fill='both', padx=6, pady=6)
        media_frame.pack_propagate(False)
        try:
            self.media_panel = MediaPanel(media_frame, self.coordinator, self.config)
            logging.info("Media panel created successfully")
        except Exception as e:
            logging.error(f"Error creating media panel: {e}")
            error_label = tk.Label(media_frame, text=f"Error loading media panel:\n{e}", 
                                  font=("Segoe UI", 10), fg="red")
            error_label.pack(pady=20)
        
        # Add close button if fullscreen
        # Window decorations removed when fullscreen to reclaim space
    
    def quit(self):
        """Clean shutdown"""
        logging.info("Shutting down Daily Assistant")
        
        # Stop Teams monitor
        if hasattr(self, 'teams_monitor'):
            self.teams_monitor.stop()
        
        # Stop VLC
        if hasattr(self, 'media_panel') and hasattr(self.media_panel, 'player'):
            try:
                self.media_panel.stop()
            except Exception:
                pass
        
        # Save any pending data
        if hasattr(self, 'schedule_panel'):
            self.schedule_panel.save_log()
        
        if hasattr(self, 'side_panel'):
            self.side_panel.save_today_notes()
        
        self.root.quit()
        sys.exit(0)


def main():
    """Entry point"""
    root = tk.Tk()
    app = DailyAssistantApp(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.quit)
    
    # Start main loop
    root.mainloop()


if __name__ == '__main__':
    main()
