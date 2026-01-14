"""
VLC Media Panel - Video playback control integrated with app coordinator.
"""

import random
import pathlib
import threading
import time
import logging
import tkinter as tk
from tkinter import ttk

try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    logging.warning("VLC library not available")


class MediaPanel:
    """VLC media control panel"""
    
    def __init__(self, parent, coordinator, config):
        self.parent = parent
        self.coordinator = coordinator
        self.config = config
        
        # VLC setup (conditional)
        if VLC_AVAILABLE:
            self.vlc_instance = vlc.Instance()
            self.player = self.vlc_instance.media_list_player_new()
            self.current_media_list = None
            self.current_folder = None
            self.current_position = 0
            self.is_playing = False
            # Register with coordinator
            self.coordinator.register_vlc_controller(self)
        else:
            self.vlc_instance = None
            self.player = None
            self.current_media_list = None
            self.current_folder = None
            self.current_position = 0
            self.is_playing = False
        
        # Paths
        self.series_dir = pathlib.Path(self.config.get('series_dir', 'D:/video/series'))
        self.movies_dir = pathlib.Path(self.config.get('movies_dir', 'D:/video/movies'))
        
        # Media lists
        self.series_available = []
        self.movies_available = []
        self.media_quick_list = []
        
        # UI variables
        self.progress_var = tk.DoubleVar()
        self.volume_var = tk.IntVar(value=100)
        
        # Load media and build UI
        self.load_media_options()
        self.build_ui()
        if VLC_AVAILABLE:
            self.start_status_thread()
    
    def build_ui(self):
        frame = tk.Frame(self.parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Show warning if VLC not available
        if not VLC_AVAILABLE:
            warning = tk.Label(frame, 
                             text="⚠️ VLC not available\nUI preview only",
                             font=("Segoe UI", 9), 
                             fg="orange",
                             bg="lightyellow",
                             pady=5)
            warning.pack(fill="x", pady=(0, 5))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        # Playback controls
        controls = tk.Frame(frame)
        controls.pack(pady=5)
        
        ttk.Button(controls, text="Play", command=self.play).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(controls, text="Pause", command=self.pause).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(controls, text="Stop", command=self.stop).grid(row=0, column=2, padx=2, pady=2, sticky='ew')
        
        ttk.Button(controls, text="<< 30s", command=self.rewind_30s).grid(row=1, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(controls, text="Next", command=self.next_in_playlist).grid(row=1, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(controls, text="30s >>", command=self.fast_forward_30s).grid(row=1, column=2, padx=2, pady=2, sticky='ew')
        
        # Utility buttons
        ttk.Button(frame, text="Random from All Series",
                  command=self.full_random_playlist).pack(fill="x", pady=2)
        ttk.Button(frame, text="Reshuffle Shows",
                  command=self.reshuffle_quick_access).pack(fill="x", pady=2)
        ttk.Button(frame, text="Hide Window",
                  command=self.hide_window).pack(fill="x", pady=2)
        ttk.Button(frame, text="Show Fullscreen",
                  command=self.show_fullscreen).pack(fill="x", pady=2)
        
        # Playlist selection
        self.playlist_series_combo = ttk.Combobox(frame, 
                                                  values=[sa.name for sa in self.series_available],
                                                  state="readonly")
        self.playlist_series_combo.pack(fill="x", pady=2)
        self.playlist_series_combo.bind("<<ComboboxSelected>>", self.change_playlist_combo_series)
        
        self.playlist_movies_combo = ttk.Combobox(frame,
                                                  values=[ma.name for ma in self.movies_available],
                                                  state="readonly")
        self.playlist_movies_combo.pack(fill="x", pady=2)
        self.playlist_movies_combo.bind("<<ComboboxSelected>>", self.change_playlist_combo_movie)
        
        # Quick access
        self.quick_access_frame = tk.Frame(frame)
        self.quick_access_frame.pack(fill="x", pady=(5, 0))
        self.individual_buttons = []
        self.update_quick_access_buttons()
    
    def start_status_thread(self):
        """Start thread to monitor playback status"""
        thread = threading.Thread(target=self.monitor_status, daemon=True)
        thread.start()
    
    def monitor_status(self):
        """Monitor playback status and update UI"""
        while True:
            try:
                if self.player and hasattr(self, 'status_label'):
                    player = self.player.get_media_player()
                    if player:
                        current_time = player.get_time()
                        length = player.get_length()
                        if length > 0:
                            progress = (current_time / length) * 100
                            self.progress_var.set(progress)
                        
                        player.release()
            except Exception as e:
                logging.error(f"Status monitoring error: {e}")
            
            time.sleep(1)
    
    def play(self):
        if not VLC_AVAILABLE:
            return
        
        # Check if playback is allowed
        if not self.coordinator.can_play_media():
            try:
                from tkinter import messagebox
                messagebox.showwarning("Playback Blocked",
                                     "Cannot play: outstanding schedule items or active call.",
                                     parent=self.parent)
            except Exception:
                pass
            return
        
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
        try:
            player = self.player.get_media_player()
            if player:
                player.set_fullscreen(True)
                player.release()
        except Exception:
            pass
    
    def pause(self):
        if not VLC_AVAILABLE:
            return
        try:
            player = self.player.get_media_player()
            if player:
                self.current_position = player.get_time()
                if player.get_state() == 3:  # Playing state
                    self.player.pause()
                    self.is_playing = False
                player.release()
        except Exception as e:
            logging.error(f"Error pausing: {e}")
    
    def stop(self):
        if not VLC_AVAILABLE:
            return
        try:
            self.player.stop()
            self.is_playing = False
        except Exception as e:
            logging.error(f"Error stopping: {e}")
    
    def rewind_30s(self):
        if not VLC_AVAILABLE:
            return
        try:
            player = self.player.get_media_player()
            if player:
                current_time = player.get_time()
                if current_time > 30000:
                    player.set_time(current_time - 30000)
                player.release()
        except Exception as e:
            logging.error(f"Error rewinding: {e}")
    
    def fast_forward_30s(self):
        if not VLC_AVAILABLE:
            return
        try:
            player = self.player.get_media_player()
            if player:
                player.set_time(player.get_time() + 30000)
                player.release()
        except Exception as e:
            logging.error(f"Error fast forwarding: {e}")
    
    def next_in_playlist(self):
        if not VLC_AVAILABLE:
            return
        self.player.next()
    
    def set_volume(self, value):
        if not VLC_AVAILABLE:
            return
        try:
            player = self.player.get_media_player()
            if player:
                player.audio_set_volume(int(float(value)))
                player.release()
        except Exception as e:
            logging.error(f"Error setting volume: {e}")
    
    def load_media_options(self):
        if self.movies_dir.exists():
            self.movies_available = [f for f in self.movies_dir.glob('*/') if f.is_dir()]
        else:
            self.movies_available = []
        
        if self.series_dir.exists():
            self.series_available = [f for f in self.series_dir.glob('*/') if f.is_dir()]
        else:
            self.series_available = []
        
        # Create quick list
        series_list = self.series_available.copy()
        random.shuffle(series_list)
        series_list = series_list[:min(5, len(series_list))]
        
        movie_list = self.movies_available.copy()
        random.shuffle(movie_list)
        movie_list = movie_list[:min(2, len(movie_list))]
        
        self.media_quick_list = series_list + movie_list
    
    def reshuffle_quick_access(self):
        self.load_media_options()
        self.update_quick_access_buttons()
    
    def update_quick_access_buttons(self):
        for button in self.individual_buttons:
            button.destroy()
        self.individual_buttons.clear()
        
        for media_path in self.media_quick_list:
            button = ttk.Button(self.quick_access_frame, text=media_path.name,
                              command=lambda path=media_path: self.change_playlist(path))
            button.pack(fill="x", pady=2)
            self.individual_buttons.append(button)
    
    def change_playlist(self, folder):
        self.current_folder = folder
        video_fn_list = self.find_video_files(self.current_folder)
        self.set_playlist(video_fn_list)
        self.random_in_playlist()
        self.play()
    
    def set_playlist(self, fn_list):
        media_list = self.vlc_instance.media_list_new()
        for video_media in fn_list:
            media_list.add_media(video_media)
        self.current_media_list = media_list
        self.player.set_media_list(self.current_media_list)
    
    def find_video_files(self, folder):
        video_extensions = ['.mp4', '.avi', '.mkv', '.flv', '.mov', '.wmv', '.mpg', '.mpeg']
        video_files = []
        folder = pathlib.Path(folder)
        
        for ext in video_extensions:
            video_files.extend(folder.rglob(f'*{ext}'))
        
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
    
    def change_playlist_combo_movie(self, event):
        selected_folder = self.playlist_movies_combo.get()
        if selected_folder:
            folder_path = self.movies_dir / selected_folder
            if folder_path.exists() and folder_path.is_dir():
                self.change_playlist(folder_path)
    
    def hide_window(self):
        """Hide VLC window"""
        if not VLC_AVAILABLE:
            return
        try:
            import pygetwindow as gw
            vlc_windows = gw.getWindowsWithTitle('VLC')
            for window in vlc_windows:
                window.minimize()
        except Exception as e:
            logging.error(f"Error hiding window: {e}")
    
    def show_fullscreen(self):
        """Show VLC window fullscreen"""
        if not VLC_AVAILABLE:
            return
        try:
            player = self.player.get_media_player()
            if player:
                player.set_fullscreen(True)
                player.release()
        except Exception as e:
            logging.error(f"Error showing fullscreen: {e}")
