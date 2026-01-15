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
import ctypes
from ctypes import wintypes

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
            try:
                self.coordinator.register_vlc_controller(self)
            except Exception:
                pass
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
            try:
                self.start_status_thread()
            except Exception:
                pass

    def _show_transient_popup(self, message, duration=3000):
        """Show a large, non-modal popup centered over the parent for a short duration."""
        try:
            popup = tk.Toplevel(self.parent)
            popup.overrideredirect(True)
            popup.attributes('-topmost', True)

            # Styling
            bg = "#ffd"  # pale yellow
            frm = tk.Frame(popup, bg=bg, bd=4, relief=tk.RIDGE)
            frm.pack(fill=tk.BOTH, expand=True)

            # Determine width and set wraplength so the full message is visible
            try:
                self.parent.update_idletasks()
                pw = self.parent.winfo_width() or 800
                ph = self.parent.winfo_height() or 600
                px = self.parent.winfo_rootx()
                py = self.parent.winfo_rooty()

                # Use a larger minimum width so text isn't clipped on small popups
                ww = max(480, int(pw * 0.6))
                # Ensure popup not wider than parent minus some padding
                ww = min(ww, pw - 40)

                lbl = tk.Label(frm, text=message, font=("Segoe UI", 20, "bold"), bg=bg, fg="black", justify=tk.CENTER, wraplength=ww-40)
                lbl.pack(padx=20, pady=14)

                # Measure required height after wrapping
                popup.update_idletasks()
                hh = lbl.winfo_reqheight() + 40
                x = px + max(10, (pw - ww) // 2)
                y = py + max(10, (ph - hh) // 2)
                popup.geometry(f"{ww}x{hh}+{x}+{y}")
            except Exception:
                try:
                    lbl = tk.Label(frm, text=message, font=("Segoe UI", 18, "bold"), bg=bg, fg="black", justify=tk.CENTER, wraplength=360)
                    lbl.pack(padx=20, pady=14)
                    popup.geometry("480x120")
                except Exception:
                    pass

            # Auto-destroy after duration ms
            popup.after(duration, popup.destroy)
        except Exception:
            raise

    def _ensure_fullscreen_attempts(self, attempts=5, delay_ms=300):
        """Try to set libVLC fullscreen, retrying a few times, then fallback to window methods."""

        def attempt(n):
            # Try libVLC fullscreen
            try:
                player = None
                try:
                    player = self.player.get_media_player()
                except Exception:
                    player = None

                if player:
                    try:
                        player.set_fullscreen(True)
                        try:
                            player.release()
                        except Exception:
                            pass
                        return True
                    except Exception:
                        try:
                            player.release()
                        except Exception:
                            pass
            except Exception:
                pass

            # If more retries, schedule another attempt
            if n > 0:
                try:
                    self.parent.after(delay_ms, lambda: attempt(n - 1))
                except Exception:
                    pass
                return False

            # Final fallback: try pygetwindow title matching
            try:
                import pygetwindow as gw
                titles = ['VLC', 'VLC (Direct3D11 output)']
                for t in titles:
                    try:
                        wins = gw.getWindowsWithTitle(t) or []
                        if wins:
                            for w in wins:
                                try:
                                    try:
                                        w.restore()
                                    except Exception:
                                        pass
                                    try:
                                        w.maximize()
                                    except Exception:
                                        pass
                                    try:
                                        w.activate()
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                            return True
                    except Exception:
                        pass
            except Exception:
                pass

            # Final Win32 fallback
            try:
                user32 = ctypes.WinDLL('user32', use_last_error=True)
                EnumWindows = user32.EnumWindows
                EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
                GetWindowTextLength = user32.GetWindowTextLengthW
                GetWindowText = user32.GetWindowTextW
                IsWindowVisible = user32.IsWindowVisible
                ShowWindow = user32.ShowWindow
                SetForegroundWindow = user32.SetForegroundWindow

                def foreach(hwnd, lparam):
                    if not IsWindowVisible(hwnd):
                        return True
                    length = GetWindowTextLength(hwnd)
                    if length == 0:
                        return True
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buf, length + 1)
                    txt = buf.value
                    if 'vlc' in txt.lower():
                        SW_MAXIMIZE = 3
                        try:
                            ShowWindow(hwnd, SW_MAXIMIZE)
                        except Exception:
                            pass
                        try:
                            SetForegroundWindow(hwnd)
                        except Exception:
                            pass
                        return False
                    return True

                EnumWindows(EnumWindowsProc(foreach), 0)
                return True
            except Exception:
                pass

            return False

        try:
            attempt(attempts)
        except Exception:
            pass
    
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
                # Determine the reason(s) for blocking
                try:
                    with self.coordinator.lock:
                        outstanding = bool(self.coordinator.outstanding_items)
                        active_call = bool(self.coordinator.active_call)
                except Exception:
                    outstanding = False
                    active_call = False

                parts = []
                if outstanding:
                    parts.append("outstanding schedule items")
                if active_call:
                    parts.append("an active call")
                if not parts:
                    parts_text = "playback is currently blocked"
                else:
                    parts_text = ' and '.join(parts)

                title = "Playback Blocked"
                message = f"Cannot play — {parts_text}."

                # Use a large, transient popup so it's visible and auto-dismisses
                try:
                    self._show_transient_popup(message, duration=3000)
                except Exception:
                    # Fallback to messagebox if popup creation fails
                    from tkinter import messagebox
                    messagebox.showwarning(title, message, parent=self.parent)
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

        try:
            self.player.play()
            self.is_playing = True
            player = self.player.get_media_player()
            if player:
                try:
                    player.set_fullscreen(True)
                finally:
                    try:
                        player.release()
                    except Exception:
                        pass
            # Ensure fullscreen is applied even if player isn't immediately available
            try:
                # Try immediately and also schedule retries
                self._ensure_fullscreen_attempts(5, 300)
                self.parent.after(300, lambda: self._ensure_fullscreen_attempts(5, 300))
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Error starting playback: {e}")
    
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

    def build_ui(self):
        """Build UI with larger buttons in 2-column grid for touchscreen."""
        frame = tk.Frame(self.parent)
        frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Button style configuration
        btn_font = ("Segoe UI", 13, "bold")
        btn_height = 2
        
        # Control buttons in 2-column grid
        controls_frame = tk.Frame(frame)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        # Configure grid columns to expand equally
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        
        # Row 0
        self.play_button = tk.Button(controls_frame, text="▶ Play", font=btn_font, height=btn_height,
                                     relief=tk.RAISED, bd=3, command=self.play)
        self.play_button.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        self.pause_button = tk.Button(controls_frame, text="⏸ Pause", font=btn_font, height=btn_height,
                                      relief=tk.RAISED, bd=3, command=self.pause)
        self.pause_button.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        # Row 1
        self.rewind_button = tk.Button(controls_frame, text="⏪ -30s", font=btn_font, height=btn_height,
                                       relief=tk.RAISED, bd=3, command=self.rewind_30s)
        self.rewind_button.grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        
        self.ff_button = tk.Button(controls_frame, text="⏩ +30s", font=btn_font, height=btn_height,
                                   relief=tk.RAISED, bd=3, command=self.fast_forward_30s)
        self.ff_button.grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        
        # Row 2
        self.prev_button = tk.Button(controls_frame, text="⏮ Previous", font=btn_font, height=btn_height,
                                     relief=tk.RAISED, bd=3, command=self.previous_in_playlist)
        self.prev_button.grid(row=2, column=0, padx=3, pady=3, sticky="ew")
        
        self.next_button = tk.Button(controls_frame, text="⏭ Next", font=btn_font, height=btn_height,
                                     relief=tk.RAISED, bd=3, command=self.next_in_playlist)
        self.next_button.grid(row=2, column=1, padx=3, pady=3, sticky="ew")
        
        # Row 3
        self.random_button = tk.Button(controls_frame, text="🔀 Random", font=btn_font, height=btn_height,
                                       relief=tk.RAISED, bd=3, command=self.random_in_playlist)
        self.random_button.grid(row=3, column=0, padx=3, pady=3, sticky="ew")
        
        self.minimise_button = tk.Button(controls_frame, text="🗕 Minimize", font=btn_font, height=btn_height,
                                         relief=tk.RAISED, bd=3, command=self.hide_window)
        self.minimise_button.grid(row=3, column=1, padx=3, pady=3, sticky="ew")
        
        # Reshuffle button (full width)
        self.reshuffle_button = tk.Button(frame, text="🔄 Reshuffle Shows", font=btn_font, height=btn_height,
                                          relief=tk.RAISED, bd=3, command=self.reshuffle_quick_access)
        self.reshuffle_button.pack(fill='x', pady=(5, 10))
        
        # Quick access section
        quick_label = tk.Label(frame, text="Quick Access:", font=("Segoe UI", 12, "bold"))
        quick_label.pack(pady=(5, 3))
        
        self.quick_access_frame = tk.Frame(frame)
        self.quick_access_frame.pack(fill='both', expand=True, pady=5)
        self.individual_buttons = []        

        try:
            self.update_quick_access_buttons()
        except Exception:
            pass
    
    def reshuffle_quick_access(self):
        self.load_media_options()
        self.update_quick_access_buttons()
    
    def update_quick_access_buttons(self):
        for button in self.individual_buttons:
            button.destroy()
        self.individual_buttons.clear()
        
        # Larger font for quick access buttons
        btn_font = ("Segoe UI", 11)
        
        for media_path in self.media_quick_list:
            button = tk.Button(self.quick_access_frame, text=media_path.name, font=btn_font,
                             relief=tk.RAISED, bd=2, height=1,
                             command=lambda path=media_path: self.change_playlist(path))
            button.pack(fill="x", pady=2)
            self.individual_buttons.append(button)
    
    def change_playlist(self, folder):
        self.current_folder = folder
        video_fn_list = self.find_video_files(self.current_folder)
        self.set_playlist(video_fn_list)
        # Play a random item from the newly set playlist (respecting coordinator)
        self.random_in_playlist()
    
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
        if not VLC_AVAILABLE:
            return

        if not (self.current_media_list and self.current_media_list.count() > 0):
            return

        # Respect coordinator state before starting playback
        try:
            if not self.coordinator.can_play_media():
                # Determine reason(s)
                try:
                    with self.coordinator.lock:
                        outstanding = bool(self.coordinator.outstanding_items)
                        active_call = bool(self.coordinator.active_call)
                except Exception:
                    outstanding = False
                    active_call = False

                parts = []
                if outstanding:
                    parts.append("outstanding schedule items")
                if active_call:
                    parts.append("an active call")
                if not parts:
                    parts_text = "playback is currently blocked"
                else:
                    parts_text = ' and '.join(parts)
                message = f"Cannot play — {parts_text}."
                try:
                    self._show_transient_popup(message, duration=3000)
                except Exception:
                    from tkinter import messagebox
                    messagebox.showwarning("Playback Blocked", message, parent=self.parent)
                return
        except Exception:
            # If coordinator check fails, be conservative and do not start
            return

        try:
            self.player.stop()
            random_index = random.randint(0, self.current_media_list.count() - 1)
            self.player.play_item_at_index(random_index)
            self.is_playing = True
            try:
                player = self.player.get_media_player()
                if player:
                    player.set_fullscreen(True)
                    player.release()
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Error starting random item: {e}")

    def previous_in_playlist(self):
        """Go to previous item in playlist, if supported."""
        try:
            # libvlc media_list_player has no direct previous; try the underlying player
            try:
                self.player.previous()
            except Exception:
                # fallback: stop and play item at index -1 isn't practical; ignore
                pass
        except Exception as e:
            logging.error(f"Error going to previous: {e}")
    
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
            player = None
            try:
                player = self.player.get_media_player()
            except Exception:
                player = None

            # First attempt: set fullscreen via libvlc media player
            if player:
                try:
                    player.set_fullscreen(True)
                    player.release()
                    return
                except Exception:
                    try:
                        player.release()
                    except Exception:
                        pass

            # Fallback: use window manager to maximize/activate the VLC window
            try:
                import pygetwindow as gw
                vlc_windows = gw.getWindowsWithTitle('VLC') or []
                for window in vlc_windows:
                    try:
                        # Try to restore and maximize, then activate
                        if window.isMinimized:
                            window.restore()
                        window.maximize()
                        window.activate()
                    except Exception:
                        try:
                            window.activate()
                        except Exception:
                            pass
                return
            except Exception:
                pass
        except Exception as e:
            logging.error(f"Error showing fullscreen: {e}")
