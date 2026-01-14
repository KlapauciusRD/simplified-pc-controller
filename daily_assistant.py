"""
Daily Assistant - Unified touchscreen application
Combines schedule, Teams, and media controls in a single interface.
"""

import tkinter as tk
from tkinter import ttk
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
        
        # Setup UI
        self.setup_window()
        self.create_layout()
        
        # Start Teams monitor
        self.teams_monitor = TeamsMonitor(self.coordinator)
        self.teams_monitor.start()
        
        logging.info("Daily Assistant started")
    
    def load_config(self):
        """Load unified configuration"""
        config_path = Path('config.json')
        
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
            'water_goal': 8,
            'medication_schedule': ["Morning (08:00)", "Evening (20:00)"],
            'other_meds': ["Vitamin D", "Magnesium"],
            
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
            'fullscreen': False,
            'font_size': 14
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logging.error(f"Error loading config: {e}")
        else:
            # Save default config
            self.save_config(default_config)
        
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
        if self.config.get('fullscreen', False):
            self.root.attributes('-fullscreen', True)
        else:
            self.root.geometry('1400x800')
        
        self.root.configure(bg='white')
    
    def create_layout(self):
        """Create main layout with schedule, side panel, and media"""
        
        # Main container
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Column 1: Schedule (50% width)
        schedule_frame = tk.Frame(main_frame, bg='white')
        schedule_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        self.schedule_panel = SchedulePanel(schedule_frame, self.coordinator, self.config)
        
        # Column 2: Side panel - water, meds, notes, Teams (25% width)
        side_frame = tk.Frame(main_frame, bg='lightgray', width=350)
        side_frame.pack(side='left', fill='both', padx=5, pady=5)
        side_frame.pack_propagate(False)
        self.side_panel = SidePanel(side_frame, self.schedule_panel, self.coordinator, self.config)
        
        # Column 3: Media controls (25% width)
        media_frame = tk.Frame(main_frame, bg='white', width=350)
        media_frame.pack(side='left', fill='both', padx=5, pady=5)
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
        if self.config.get('fullscreen', False):
            close_btn = tk.Button(
                self.root,
                text='×',
                font=('Arial', 16, 'bold'),
                bg='red',
                fg='white',
                command=self.quit,
                width=3
            )
            close_btn.place(x=self.root.winfo_screenwidth() - 60, y=10)
    
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
