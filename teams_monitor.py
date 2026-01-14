"""
Teams Monitor - Background thread for monitoring Teams calls and processing call requests.
"""

import threading
import time
import logging
import webbrowser

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
                
                # Check if Teams call is active
                call_active = self._is_teams_call_active()
                self.coordinator.set_call_active(call_active)
                
            except Exception as e:
                logging.error(f"Teams monitor error: {e}")
            
            time.sleep(1)
    
    def _process_call_request(self, call_url):
        """Process outbound call request from UI"""
        try:
            logging.info(f"Processing call request: {call_url}")
            
            # Open Teams URL
            webbrowser.open(call_url)
            time.sleep(3)
            
            # Try to auto-join (best effort)
            if AUTOMATION_AVAILABLE:
                self._auto_join_attempt()
            
        except Exception as e:
            logging.error(f"Error processing call request: {e}")
    
    def _auto_join_attempt(self):
        """Attempt to auto-join meeting (brittle - depends on Teams UI)"""
        if not AUTOMATION_AVAILABLE:
            return
        
        try:
            # Wait for Teams window
            time.sleep(2)
            
            # Try to find and click join button
            join_button = pyautogui.locateOnScreen('join_button.png', confidence=0.8)
            if join_button:
                button_center = pyautogui.center(join_button)
                pyautogui.click(button_center)
                logging.info("Auto-join: clicked join button")
                time.sleep(1)
                
                # Try to click "join now" button
                join_now = pyautogui.locateOnScreen('join_now_button.png', confidence=0.8)
                if join_now:
                    button_center = pyautogui.center(join_now)
                    pyautogui.click(button_center)
                    logging.info("Auto-join: clicked join now")
        except Exception as e:
            logging.debug(f"Auto-join attempt failed (expected): {e}")
    
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
