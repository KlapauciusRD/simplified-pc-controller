"""
Teams Monitor - Background thread for monitoring Teams calls and processing call requests.
"""

import threading
import time
import logging
import webbrowser
from urllib.parse import quote

try:
    import pygetwindow as gw
    import pyautogui
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False
    logging.warning("pygetwindow/pyautogui not available - Teams automation disabled")


class TeamsMonitor:
    """Background monitor for Teams calls"""
    
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.running = False
        self.thread = None
        # Stabilize call detection: require consecutive positives/negatives
        self._call_detect_counter = 0
        self._call_clear_counter = 0
        # Require multiple consecutive detections to flip state (reduce false positives)
        self._detect_threshold = 4
        self._clear_threshold = 4
        
    def start(self):
        """Start monitoring thread"""
        if self.thread and self.thread.is_alive():
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logging.info("Teams monitor started")
    
    def stop(self):
        """Stop monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logging.info("Teams monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for call requests from UI
                pending_calls = self.coordinator.get_pending_calls()
                for call_url in pending_calls:
                    self._process_call_request(call_url)
                
                # Check for incoming calls (if automation available)
                if AUTOMATION_AVAILABLE:
                    self._check_incoming_calls()
                
                # Check if Teams call is active (stabilized)
                detected = self._is_teams_call_active()

                if detected:
                    self._call_detect_counter += 1
                    self._call_clear_counter = 0
                else:
                    self._call_clear_counter += 1
                    self._call_detect_counter = 0

                logging.debug(f"TeamsMonitor detection={detected} detect_count={self._call_detect_counter} clear_count={self._call_clear_counter}")

                # Only flip coordinator state after threshold
                if self._call_detect_counter >= self._detect_threshold:
                    self.coordinator.set_call_active(True)
                elif self._call_clear_counter >= self._clear_threshold:
                    self.coordinator.set_call_active(False)
                
            except Exception as e:
                logging.error(f"Teams monitor error: {e}")
            
            time.sleep(1)
    
    def _process_call_request(self, call_config):
        """Process a queued outbound call using a Teams call deep link."""
        try:
            user = call_config.get('user') or call_config.get('email') or call_config.get('id')
            name = call_config.get('name', 'contact')
            
            if not user and not call_config.get('url'):
                logging.error("Call request missing user identifier")
                return
            
            if call_config.get('url'):
                call_url = call_config['url']
            else:
                encoded_user = quote(user.strip(), safe='')
                with_video = 'true' if call_config.get('video', False) else 'false'
                call_url = (f"https://teams.microsoft.com/l/call/0/0?users={encoded_user}"
                            f"&withVideo={with_video}")

            desktop_url = call_url.replace('https://', 'msteams://', 1)
            opened = webbrowser.open(desktop_url, new=1)
            if not opened:
                opened = webbrowser.open(call_url, new=1)

            self.coordinator.last_call_opened = {
                'user': user,
                'name': name,
                'success': bool(opened)
            }
            logging.info(f"Teams call link opened for {name}: success={bool(opened)}")
            
        except Exception as e:
            self.coordinator.last_call_opened = {
                'user': user if 'user' in locals() else None,
                'name': name if 'name' in locals() else 'contact',
                'success': False
            }
            logging.error(f"Error processing call request: {e}")
    
    # Removed fragile auto-click automation - chat opens and user manually clicks video button
    # This is more reliable and works regardless of webcam, Teams version, or UI layout
    
    def _start_audio_call(self):
        """Attempt to start a call in the opened Teams chat (tries video then audio)"""
        if not AUTOMATION_AVAILABLE:
            return False
        
        try:
            # Find Teams window
            teams_windows = gw.getWindowsWithTitle('Teams')
            if not teams_windows:
                logging.debug("No Teams window found")
                return False
            
            tw = teams_windows[0]
            
            # Activate/bring to front
            try:
                tw.activate()
            except Exception:
                try:
                    tw.maximize()
                except Exception:
                    pass
            
            time.sleep(0.5)
            
            # Click in the center-bottom area where message input usually is
            # This ensures focus is in the chat, not search box
            msg_box_x = tw.left + (tw.width // 2)
            msg_box_y = tw.top + tw.height - 100  # Near bottom where message box is
            
            try:
                pyautogui.click(msg_box_x, msg_box_y)
                logging.debug(f"Clicked message area at ({msg_box_x}, {msg_box_y})")
                time.sleep(0.5)
            except Exception as e:
                logging.debug(f"Could not click message area: {e}")
            
            # Try video call first (Alt+Shift+V), then audio as backup (Alt+Shift+A)
            logging.info("Sending video call hotkey (Alt+Shift+V)")
            try:
                pyautogui.hotkey('alt', 'shift', 'v')
            except Exception:
                try:
                    pyautogui.keyDown('alt')
                    pyautogui.keyDown('shift')
                    pyautogui.press('v')
                    pyautogui.keyUp('shift')
                    pyautogui.keyUp('alt')
                except Exception as e:
                    logging.debug(f"Video hotkey failed: {e}")
            
            time.sleep(0.8)
            
            # Backup: audio call (Alt+Shift+A)
            logging.info("Sending audio call hotkey (Alt+Shift+A) as backup")
            try:
                pyautogui.hotkey('alt', 'shift', 'a')
            except Exception:
                try:
                    pyautogui.keyDown('alt')
                    pyautogui.keyDown('shift')
                    pyautogui.press('a')
                    pyautogui.keyUp('shift')
                    pyautogui.keyUp('alt')
                except Exception as e:
                    logging.error(f"Audio hotkey failed: {e}")
                    return False
            
            logging.info("Call hotkeys sent successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error starting audio call: {e}")
            return False
    
    # Auto-join functionality removed - only auto-answer incoming calls
    # def _auto_join_attempt(self):
    #     """DISABLED: Auto-join meetings is not used"""
    #     pass
    
    def _check_incoming_calls(self):
        """Check for incoming Teams calls"""
        if not AUTOMATION_AVAILABLE:
            return
        
        try:
            # Look for Teams windows with "incoming call" in title
            teams_windows = gw.getWindowsWithTitle('Teams')
            for window in teams_windows:
                if 'incoming' in window.title.lower() or 'call from' in window.title.lower():
                    logging.info(f"Incoming call detected: {window.title}")
                    self._auto_answer_call()
                    break
        except Exception as e:
            logging.debug(f"Error checking incoming calls: {e}")
    
    def _auto_answer_call(self):
        """Auto-answer incoming call"""
        if not AUTOMATION_AVAILABLE:
            return
        
        try:
            # Try to find and click answer button
            answer_button = pyautogui.locateOnScreen('answer_button.png', confidence=0.8)
            if answer_button:
                button_center = pyautogui.center(answer_button)
                pyautogui.click(button_center)
                logging.info("Auto-answered incoming call")
        except Exception as e:
            logging.debug(f"Auto-answer failed: {e}")
    
    def _is_teams_call_active(self):
        """Check if a Teams call is currently active"""
        if not AUTOMATION_AVAILABLE:
            return False
        
        try:
            teams_windows = gw.getWindowsWithTitle('Teams')
            for window in teams_windows:
                title_lower = window.title.lower()
                if any(keyword in title_lower for keyword in ['meeting', 'call with', 'calling']):
                    return True
        except Exception:
            pass
        
        return False
