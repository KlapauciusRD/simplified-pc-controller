import os
import random
import vlc
import tkinter as tk
from tkinter import ttk, messagebox
import pathlib
from screeninfo import get_monitors
import tkinter.font as tkFont
import pygetwindow
import threading
import time
import json
import logging
import subprocess
import re
import requests
from urllib.parse import quote

# Set up logging
logging.basicConfig(filename='vlc_controller.log', level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
CONFIG_FILE = pathlib.Path('vlc_config.json')
DEFAULT_CONFIG = {
    'series_dir': 'D:/video/series',
    'movies_dir': 'D:/video/movies',
    'vlc_window_title': 'VLC (Direct3D11 output)',
    'flag_file': 'c:/users/macka/skype_call_flag',
    'screen_index': 1,
    'window_width_percent': 25,
    'font_size': 26,
    'auto_resume': True,
    'auto_subtitles': True,
    'subtitle_language': 'en',
    'last_playlist': None,
    'last_position': 0
}

print('Running video controller')
SKYPE_FLAG_LOCATION = pathlib.Path('c:/users/macka/skype_call_flag')

VLC_WINNAME = 'VLC (Direct3D11 output)'

def load_config():
    """Load configuration from file or return defaults"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving config: {e}")

config = load_config()
SKYPE_FLAG_LOCATION = pathlib.Path(config['flag_file'])
VLC_WINNAME = config['vlc_window_title']

def minimise_vlc_window():
    # This function is now deprecated - use VLCController methods instead
    pass

def maximise_vlc_window():
    # This function is now deprecated - use VLCController methods instead
    pass



class VLCController:
    def __init__(self, root):
        self.config = config
        # Create VLC instance
        # Note: VLC window titles cannot be customized via initialization options
        # The window title is set by VLC internally based on the video output module
        # Common titles: "VLC media player", "VLC (Direct3D11 output)", etc.
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_list_player_new()
        self.playlists = []
        self.current_folder = None
        self.current_media_list = None
        self.series_dir = pathlib.Path(self.config['series_dir'])
        self.movies_dir = pathlib.Path(self.config['movies_dir'])
        self.series_available = []
        self.movies_available = []
        self.media_quick_list = []
        self.current_position = 0
        self.is_playing = False
        
        # VLC window management
        self.vlc_window = None
        
        # Status variables
        self.status_label = None
        self.progress_var = tk.DoubleVar()
        self.volume_var = tk.IntVar(value=100)
        
        self.load_media_options()
        self.start_monitoring_thread()
        self.start_status_thread()
        
        self.root = root
        
        # Find VLC window after initialization
        self.find_vlc_window()

    def find_vlc_window(self):
        """Find and store reference to VLC window"""
        try:
            windows = pygetwindow.getWindowsWithTitle(self.config['vlc_window_title'])
            if windows:
                self.vlc_window = windows[0]
                logging.info(f"Found VLC window: {self.vlc_window.title}")
                # Restore saved position if available
                self.restore_vlc_window_position()
                return True
            else:
                logging.warning("VLC window not found")
                self.vlc_window = None
                return False
        except Exception as e:
            logging.error(f"Error finding VLC window: {e}")
            self.vlc_window = None
            return False

    def get_vlc_window(self):
        """Get current VLC window reference, finding it if necessary"""
        if self.vlc_window is None or not self.vlc_window.visible:
            self.find_vlc_window()
        return self.vlc_window

    def set_vlc_window_position(self, x=None, y=None, width=None, height=None):
        """Manually set VLC window position and size"""
        window = self.get_vlc_window()
        if window:
            try:
                if x is not None and y is not None:
                    window.moveTo(x, y)
                if width is not None and height is not None:
                    window.resizeTo(width, height)
                
                # Save position to config
                if x is not None:
                    self.config['vlc_window_x'] = x
                if y is not None:
                    self.config['vlc_window_y'] = y
                if width is not None:
                    self.config['vlc_window_width'] = width
                if height is not None:
                    self.config['vlc_window_height'] = height
                save_config(self.config)
                
                logging.info(f"Set VLC window position: x={x}, y={y}, w={width}, h={height}")
            except Exception as e:
                logging.error(f"Error setting VLC window position: {e}")

    def restore_vlc_window_position(self):
        """Restore VLC window position from config"""
        x = self.config.get('vlc_window_x')
        y = self.config.get('vlc_window_y')
        width = self.config.get('vlc_window_width')
        height = self.config.get('vlc_window_height')
        
        if x is not None and y is not None:
            self.set_vlc_window_position(x=x, y=y, width=width, height=height)

    def center_vlc_window(self):
        """Center VLC window on screen"""
        window = self.get_vlc_window()
        if window:
            try:
                # Get screen dimensions
                monitors = get_monitors()
                if monitors:
                    screen = monitors[0]  # Primary monitor
                    screen_center_x = screen.x + screen.width // 2
                    screen_center_y = screen.y + screen.height // 2
                    
                    window_width = window.width
                    window_height = window.height
                    
                    x = screen_center_x - window_width // 2
                    y = screen_center_y - window_height // 2
                    
                    window.moveTo(x, y)
                    logging.info(f"Centered VLC window at: {x}, {y}")
            except Exception as e:
                logging.error(f"Error centering VLC window: {e}")

    def create_gui(self):
        self.create_gui()
        
        self.create_gui()

      
    def monitor_flag(self):
        current_state = False
        while True:
            new_state = SKYPE_FLAG_LOCATION.exists()
            if new_state:
                os.remove(SKYPE_FLAG_LOCATION)
                print('ingesting flag')
                self.hide()
            time.sleep(1)

    def start_status_thread(self):
        """Start thread to monitor playback status"""
        status_thread = threading.Thread(target=self.monitor_status)
        status_thread.daemon = True
        status_thread.start()

    def monitor_status(self):
        """Monitor playback status and update UI"""
        while True:
            try:
                if self.player and self.status_label:
                    player = self.player.get_media_player()
                    if player:
                        # Update progress
                        current_time = player.get_time()
                        length = player.get_length()
                        if length > 0:
                            progress = (current_time / length) * 100
                            self.progress_var.set(progress)
                        
                        # Update status
                        state = player.get_state()
                        state_names = {
                            0: "Nothing",
                            1: "Opening",
                            2: "Buffering", 
                            3: "Playing",
                            4: "Paused",
                            5: "Stopped",
                            6: "Ended",
                            7: "Error"
                        }
                        status_text = f"Status: {state_names.get(state, 'Unknown')}"
                        
                        # Add current media info
                        if self.current_media_list:
                            current_index = self.player.get_media_list().index_of_item(self.player.get_media_player().get_media())
                            if current_index >= 0:
                                current_media = self.current_media_list.item_at_index(current_index)
                                if current_media:
                                    media_name = pathlib.Path(current_media.get_mrl()).name
                                    status_text += f" | Playing: {media_name}"
                        
                        self.status_label.config(text=status_text)
                        player.release()
                        
            except Exception as e:
                logging.error(f"Status monitoring error: {e}")
            
            time.sleep(1)

    def create_gui(self):
        frame = tk.Frame(self.root)
        frame.pack(side="right", fill="y", padx=20, pady=20)
        
        
        self.title_label = ttk.Label(frame, text='VIDEO CONTROLS')
        self.title_label.pack(pady=10)

        # Status display
        self.status_label = ttk.Label(frame, text="Status: Stopped", wraplength=300)
        self.status_label.pack(pady=5)

        # Progress bar
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)

        # Volume control
        volume_frame = tk.Frame(frame)
        volume_frame.pack(pady=5)
        ttk.Label(volume_frame, text="Volume:").pack(side="left")
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, variable=self.volume_var, 
                                    command=self.set_volume, orient="horizontal")
        self.volume_scale.pack(side="left", padx=(5,0))

        self.play_button = ttk.Button(frame, text="Play", command=self.play)
        self.play_button.pack(pady=5)
        
        self.pause_button = ttk.Button(frame, text="Pause", command=self.pause)
        self.pause_button.pack(pady=5)
        
        self.rewind_button = ttk.Button(frame, text="Rewind 30s", command=self.rewind_30s)
        self.rewind_button.pack(pady=5)
        
        self.ff_button = ttk.Button(frame, text="Fast Forward 30s", command=self.fast_forward_30s)
        self.ff_button.pack(pady=5)
        
        self.prev_button = ttk.Button(frame, text="Previous", command=self.previous_in_playlist)
        self.prev_button.pack(pady=5)
        
        self.next_button = ttk.Button(frame, text="Next", command=self.next_in_playlist)
        self.next_button.pack(pady=5)
        
        self.random_button = ttk.Button(frame, text="Random", command=self.random_in_playlist)
        self.random_button.pack(pady=5)

        self.playlist_series_combo = ttk.Combobox(frame, values=[sa.name for sa in self.series_available], font="Verdana 22 bold")
        self.playlist_series_combo.pack(pady=5)
        self.playlist_series_combo.bind("<<ComboboxSelected>>", self.change_playlist_combo_series)
        
        self.playlist_movies_combo = ttk.Combobox(frame, values=[ma.name for ma in self.movies_available], font="Verdana 22 bold")
        self.playlist_movies_combo.pack(pady=5)
        self.playlist_movies_combo.bind("<<ComboboxSelected>>", self.change_playlist_combo_movie)
        
        self.full_random = ttk.Button(frame, text="Any random (default play)", command=self.full_random_playlist)
        self.full_random.pack(pady=5)
        
        # Reshuffle quick access button
        self.reshuffle_button = ttk.Button(frame, text="Reshuffle Shows", command=self.reshuffle_quick_access)
        self.reshuffle_button.pack(pady=5)
        
        # Quick access buttons
        ttk.Label(frame, text="Quick Access:").pack(pady=(10,5))
        self.quick_access_frame = tk.Frame(frame)
        self.quick_access_frame.pack(pady=5)
        self.individual_buttons = []        
        
        self.update_quick_access_buttons()
        
    def reshuffle_quick_access(self):
        """Reshuffle the quick access show buttons"""
        self.load_media_options()
        self.update_quick_access_buttons()

    def update_quick_access_buttons(self):
        """Update the quick access buttons with current media_quick_list"""
        # Clear existing buttons
        for button in self.individual_buttons:
            button.destroy()
        self.individual_buttons.clear()
        
        # Create new buttons
        for media_path in self.media_quick_list:
            button = ttk.Button(self.quick_access_frame,
                              text=media_path.name,
                              command=lambda path=media_path: self.change_playlist(path))
            button.pack(pady=2)
            self.individual_buttons.append(button)
        
        # Settings button
        self.settings_button = ttk.Button(frame, text="Settings", command=self.show_settings)
        self.settings_button.pack(pady=5)
        
        self.root.mainloop()



    def play(self):
        self.make_fullscreen()
        self.maximise_vlc_window()
        if self.current_media_list is None:
            self.full_random_playlist()
        
        # Resume from saved position if enabled
        if self.config.get('auto_resume', True) and self.current_position > 0:
            try:
                player = self.player.get_media_player()
                if player:
                    player.set_time(self.current_position)
                    player.release()
            except Exception as e:
                logging.error(f"Error resuming position: {e}")
        
        self.player.play()
        self.is_playing = True

    def pause(self):
        try:
            player = self.player.get_media_player()
            if player:
                # Save current position
                self.current_position = player.get_time()
                if player.get_state() == 3:  # Playing state
                    self.player.pause()
                    self.is_playing = False
                player.release()
        except Exception as e:
            print(f"Error pausing video: {e}")

    def rewind_30s(self):
        try:
            player = self.player.get_media_player()
            if player:
                current_time = player.get_time()
                if current_time > 30000:  # Don't go negative
                    player.set_time(current_time - 30000)
                player.release()
        except Exception as e:
            print(f"Error rewinding: {e}")

    def fast_forward_30s(self):
        try:
            player = self.player.get_media_player()
            if player:
                player.set_time(player.get_time() + 30000)
                player.release()
        except Exception as e:
            print(f"Error fast forwarding: {e}")

    def set_volume(self, value):
        """Set VLC volume"""
        try:
            player = self.player.get_media_player()
            if player:
                player.audio_set_volume(int(float(value)))
                player.release()
        except Exception as e:
            logging.error(f"Error setting volume: {e}")

    def download_subtitles(self, video_path):
        """Download subtitles for the given video file"""
        if not self.config.get('auto_subtitles', True):
            return None
            
        try:
            video_file = pathlib.Path(video_path)
            if not video_file.exists():
                return None
                
            # Create subtitle filename
            subtitle_file = video_file.with_suffix('.srt')
            if subtitle_file.exists():
                logging.info(f"Subtitles already exist: {subtitle_file}")
                return str(subtitle_file)
            
            # Try to download subtitles
            logging.info(f"Attempting to download subtitles for: {video_file.name}")
            
            # Use subliminal if available, otherwise fallback to basic method
            try:
                import subliminal
                from subliminal import download_best_subtitles, region, save_subtitles
                
                # Configure subliminal
                video = subliminal.Video.from_path(str(video_file))
                language = subliminal.Language(self.config.get('subtitle_language', 'en'))
                
                with region.cache:
                    subtitles = download_best_subtitles([video], {language})
                    
                if subtitles and subtitles[video]:
                    save_subtitles(video, subtitles[video])
                    logging.info(f"Downloaded subtitles using subliminal: {subtitle_file}")
                    return str(subtitle_file)
                    
            except ImportError:
                # Fallback: Try OpenSubtitles API
                return self.download_from_opensubtitles(video_file)
                
        except Exception as e:
            logging.error(f"Error downloading subtitles: {e}")
            
        return None

    def download_from_opensubtitles(self, video_file):
        """Fallback subtitle download using OpenSubtitles"""
        try:
            # This is a simplified implementation
            # In practice, you'd need proper API authentication
            filename = video_file.stem
            search_url = f"https://rest.opensubtitles.org/search/query-{quote(filename)}/sublanguageid-eng"
            
            headers = {'User-Agent': 'VLC Subtitle Downloader'}
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Download the first result
                    sub_url = data[0]['SubDownloadLink']
                    sub_response = requests.get(sub_url, headers=headers, timeout=10)
                    
                    if sub_response.status_code == 200:
                        subtitle_file = video_file.with_suffix('.srt')
                        with open(subtitle_file, 'wb') as f:
                            f.write(sub_response.content)
                        logging.info(f"Downloaded subtitles from OpenSubtitles: {subtitle_file}")
                        return str(subtitle_file)
                        
        except Exception as e:
            logging.error(f"OpenSubtitles download failed: {e}")
            
        return None

    def load_subtitles_into_vlc(self, subtitle_path):
        """Load subtitles into VLC player"""
        try:
            if subtitle_path and pathlib.Path(subtitle_path).exists():
                player = self.player.get_media_player()
                if player:
                    # Add subtitle track
                    player.add_slave(vlc.MediaSlaveType.subtitle, str(subtitle_path), True)
                    logging.info(f"Loaded subtitles: {subtitle_path}")
                    player.release()
        except Exception as e:
            logging.error(f"Error loading subtitles into VLC: {e}")

    def next_in_playlist(self):
        self.player.next()

    def previous_in_playlist(self):
        self.player.previous()


    def load_media_options(self):
        if self.movies_dir.exists():
            self.movies_available = [folder for folder in self.movies_dir.glob('*/') if folder.is_dir()]
        else:
            print(f"Movies directory not found: {self.movies_dir}")
            self.movies_available = []
            
        if self.series_dir.exists():
            self.series_available = [folder for folder in self.series_dir.glob('*/') if folder.is_dir()]
        else:
            print(f"Series directory not found: {self.series_dir}")
            self.series_available = []

        series_list = self.series_available.copy()
        random.shuffle(series_list)
        series_list = series_list[0:min(5,len(series_list))]
        movie_list  = self.movies_available.copy()
        random.shuffle(movie_list)
        movie_list = movie_list[0:min(2,len(movie_list))]
        self.media_quick_list = series_list+movie_list
 
        
    def reshuffle_quick_access(self):
        """Reshuffle the quick access show buttons"""
        self.load_media_options()
        self.update_quick_access_buttons()

    def update_quick_access_buttons(self):
        """Update the quick access buttons with current media_quick_list"""
        # Clear existing buttons
        for button in self.individual_buttons:
            button.destroy()
        self.individual_buttons.clear()
        
        # Create new buttons
        for media_path in self.media_quick_list:
            button = ttk.Button(self.quick_access_frame,
                              text=media_path.name,
                              command=lambda path=media_path: self.change_playlist(path))
            button.pack(pady=2)
            self.individual_buttons.append(button)
        
    def change_playlist(self, folder):
        self.current_folder = folder
        video_fn_list = self.find_video_files(self.current_folder)
        self.set_playlist(video_fn_list)
        self.random_in_playlist()
        self.play()
        
        # Try to download subtitles for the first video in background
        if video_fn_list:
            threading.Thread(target=self.download_subtitles_for_current, daemon=True).start()
        
        
    def set_playlist(self, fn_list):
        media_list = self.vlc_instance.media_list_new()
        for video_media in fn_list:
            media_list.add_media(video_media)

        self.current_media_list = media_list
        self.player.set_media_list(self.current_media_list)

    def download_subtitles_for_current(self):
        """Download subtitles for currently playing video"""
        try:
            time.sleep(2)  # Wait for video to start
            player = self.player.get_media_player()
            if player:
                media = player.get_media()
                if media:
                    media_path = media.get_mrl()
                    if media_path.startswith('file://'):
                        media_path = media_path[7:]  # Remove file:// prefix
                        subtitle_path = self.download_subtitles(media_path)
                        if subtitle_path:
                            # Load subtitles after a short delay
                            time.sleep(1)
                            self.load_subtitles_into_vlc(subtitle_path)
                player.release()
        except Exception as e:
            logging.error(f"Error in subtitle download thread: {e}")

        
        
    def find_video_files(self, folder):
        """
        This function finds all video files acceptable to VLC in a given directory.
        :param directory: The directory to search for video files.
        :return: A list of paths to the video files.
        """
        video_extensions = ['.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv', '.mpg', '.mpeg']
        video_files = []
        folder = pathlib.Path(folder)
        
        for ext in video_extensions:
            video_files.extend(folder.rglob(f'*{ext}'))  # Recursive glob search

        return video_files
    
    def full_random_playlist(self):
        full_list = self.find_video_files(self.series_dir)
        random.shuffle(full_list)
        self.set_playlist(full_list)
        self.play()

    def random_in_playlist(self):
        if self.current_media_list and self.current_media_list.count() > 0:
            self.player.stop()
            random_index = random.randint(0, self.current_media_list.count() - 1)
            self.player.play_item_at_index(random_index)


    def change_playlist_combo_series(self, event):
        selected_folder = self.playlist_series_combo.get()
        if selected_folder:
            folder_path = self.series_dir / selected_folder
            if folder_path.exists() and folder_path.is_dir():
                self.change_playlist(folder_path)
            else:
                print(f"Series folder not found: {folder_path}")

        
    def change_playlist_combo_movie(self, event):
        selected_folder = self.playlist_movies_combo.get()
        if selected_folder:
            folder_path = self.movies_dir / selected_folder
            if folder_path.exists() and folder_path.is_dir():
                self.change_playlist(folder_path)
            else:
                print(f"Movie folder not found: {folder_path}")


    def turn_off_fullscreen(self):
        try:
            player = self.player.get_media_player()
            if player:
                player.set_fullscreen(False)
                player.release()
        except Exception as e:
            print(f"Error turning off fullscreen: {e}")


    def make_fullscreen(self):
        """
        This function makes the VLC player window fullscreen.
        :param player: The VLC media player instance.
        """
        try:
            player = self.player.get_media_player()
            if player:
                player.set_fullscreen(True)
                player.release()
        except Exception as e:
            print(f"Error making fullscreen: {e}")

    def minimise_vlc_window(self):
        """Minimize VLC window"""
        window = self.get_vlc_window()
        if window:
            try:
                window.minimize()
            except Exception as e:
                logging.error(f"Could not minimize VLC window: {e}")

    def maximise_vlc_window(self):
        """Maximize VLC window"""
        window = self.get_vlc_window()
        if window:
            try:
                window.maximize()
            except Exception as e:
                logging.error(f"Could not maximize VLC window: {e}")

    def hide(self):
        self.pause()
        self.turn_off_fullscreen()
        self.minimise_vlc_window()
        

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        # Series directory
        ttk.Label(settings_window, text="Series Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        series_var = tk.StringVar(value=str(self.config['series_dir']))
        series_entry = ttk.Entry(settings_window, textvariable=series_var, width=40)
        series_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Movies directory
        ttk.Label(settings_window, text="Movies Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        movies_var = tk.StringVar(value=str(self.config['movies_dir']))
        movies_entry = ttk.Entry(settings_window, textvariable=movies_var, width=40)
        movies_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Screen index
        ttk.Label(settings_window, text="Screen Index:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        screen_var = tk.IntVar(value=self.config['screen_index'])
        screen_spin = tk.Spinbox(settings_window, from_=0, to=10, textvariable=screen_var, width=5)
        screen_spin.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Font size
        ttk.Label(settings_window, text="Font Size:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        font_var = tk.IntVar(value=self.config['font_size'])
        font_spin = tk.Spinbox(settings_window, from_=10, to=50, textvariable=font_var, width=5)
        font_spin.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Auto subtitles
        ttk.Label(settings_window, text="Auto-Download Subtitles:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        sub_var = tk.BooleanVar(value=self.config.get('auto_subtitles', True))
        sub_check = ttk.Checkbutton(settings_window, variable=sub_var)
        sub_check.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Subtitle language
        ttk.Label(settings_window, text="Subtitle Language:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        lang_var = tk.StringVar(value=self.config.get('subtitle_language', 'en'))
        lang_entry = ttk.Entry(settings_window, textvariable=lang_var, width=5)
        lang_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        def save_settings():
            self.config['series_dir'] = series_var.get()
            self.config['movies_dir'] = movies_var.get()
            self.config['screen_index'] = screen_var.get()
            self.config['font_size'] = font_var.get()
            self.config['auto_subtitles'] = sub_var.get()
            self.config['subtitle_language'] = lang_var.get()
            save_config(self.config)
            messagebox.showinfo("Settings", "Settings saved! Restart required for some changes.")
            settings_window.destroy()
        
        ttk.Button(settings_window, text="Save", command=save_settings).grid(row=4, column=0, columnspan=2, pady=20)

    def end_all(self):
        self.player.stop()
        root.destroy()


def disable_close():
    pass  # This function does nothing, effectively disabling the close button


def set_window_geometry(root, screen_index=1, width_percentage=25):
    monitors = get_monitors()
    if screen_index < len(monitors):
        screen = monitors[screen_index]
        screen_width = screen.width
        screen_height = screen.height
        window_width = int(screen_width * (width_percentage / 100))
        x_position = screen.x + screen_width - window_width
        y_position = screen.y
        root.geometry(f"{window_width}x{screen_height}+{x_position}+{y_position}")
    else:
        print(f"Screen index {screen_index} out of range, using primary screen")
        # Fall back to primary screen (index 0)
        if monitors:
            screen = monitors[0]
            screen_width = screen.width
            screen_height = screen.height
            window_width = int(screen_width * (width_percentage / 100))
            x_position = screen.x + screen_width - window_width
            y_position = screen.y
            root.geometry(f"{window_width}x{screen_height}+{x_position}+{y_position}")


if __name__ == "__main__":
    root = tk.Tk()
    set_window_geometry(root, config['screen_index'], config['window_width_percent'])
    root.protocol("WM_DELETE_WINDOW", disable_close)
    root.title("Media Controller")
    root.overrideredirect(1)
    root.attributes('-topmost', True)
    
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(size=config['font_size'])
    root.option_add("*TCombobox*Listbox*Font", default_font)
    app = VLCController(root)
