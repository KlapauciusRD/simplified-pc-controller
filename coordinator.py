"""
Central coordinator for shared state between application components.
Thread-safe state management without flag files.
"""

import threading
import logging


class AppCoordinator:
    """Central coordinator for shared state between components"""
    
    def __init__(self):
        self.outstanding_items = False
        self.active_call = False
        self.call_request_queue = []
        self.vlc_controller = None
        self.lock = threading.Lock()
        
    def set_outstanding(self, value):
        """Set whether there are outstanding schedule items"""
        with self.lock:
            old_value = self.outstanding_items
            self.outstanding_items = value
            
            # If outstanding status changed and VLC is playing, pause it
            if value and not old_value and self.vlc_controller:
                try:
                    if self.vlc_controller.is_playing:
                        self.vlc_controller.pause()
                        logging.info("Paused playback due to outstanding items")
                except Exception as e:
                    logging.error(f"Error pausing for outstanding items: {e}")
            
    def can_play_media(self):
        """Check if media playback is allowed"""
        with self.lock:
            return not self.outstanding_items and not self.active_call
            
    def set_call_active(self, value):
        """Set whether a Teams call is active"""
        with self.lock:
            old_value = self.active_call
            self.active_call = value
            
            # If call started and VLC is playing, pause it
            if value and not old_value and self.vlc_controller:
                try:
                    if self.vlc_controller.is_playing:
                        self.vlc_controller.pause()
                        logging.info("Paused playback due to active call")
                except Exception as e:
                    logging.error(f"Error pausing for call: {e}")
            
    def request_call(self, call_config):
        """Queue a Teams call request"""
        with self.lock:
            self.call_request_queue.append(call_config)
            logging.info(f"Call requested: {call_config.get('name', 'Unknown')}")
            
    def get_pending_calls(self):
        """Retrieve and clear pending call requests"""
        with self.lock:
            calls = self.call_request_queue.copy()
            self.call_request_queue.clear()
            return calls
    
    def register_vlc_controller(self, vlc_controller):
        """Register VLC controller for coordination"""
        with self.lock:
            self.vlc_controller = vlc_controller
