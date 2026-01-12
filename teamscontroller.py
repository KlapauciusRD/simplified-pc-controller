# -*- coding: utf-8 -*-
"""
Teams Call Controller - Monitors Microsoft Teams for incoming calls and auto-answers them,
while coordinating with VLC controller via flag file.

Created on January 12, 2026
Adapted from Skype controller
"""

import time
import pathlib
import pygetwindow
import pyautogui
import os
import re

# Configuration
TEAMS_WINDOW_TITLE = "Microsoft Teams"
FLAG_LOCATION = pathlib.Path('c:/users/macka/skype_call_flag')  # Keep same path for VLC compatibility
ANSWER_BUTTON_IMAGE = 'answer_button.png'  # Screenshot of Teams answer button

def find_teams_window():
    """
    Find the Microsoft Teams window by title.
    Returns the window object if found, None otherwise.
    """
    windows = pygetwindow.getWindowsWithTitle(TEAMS_WINDOW_TITLE)
    return windows[0] if windows else None

def is_call_incoming():
    """
    Check for incoming call indicators in Teams.
    Uses multiple methods for reliability.
    """
    teams_window = find_teams_window()
    if not teams_window:
        return False

    # Method 1: Check window title for incoming call indicators
    title_indicators = ["Incoming call", "Incoming video call", "Call from"]
    if any(indicator in teams_window.title for indicator in title_indicators):
        return True

    # Method 2: Look for answer button on screen (more reliable)
    try:
        answer_button = pyautogui.locateOnScreen(ANSWER_BUTTON_IMAGE, confidence=0.8)
        return answer_button is not None
    except Exception as e:
        print(f"Image recognition error: {e}")
        return False

def answer_call():
    """
    Simulate clicking the Teams answer button.
    Returns True if successfully clicked, False otherwise.
    """
    try:
        answer_button = pyautogui.locateOnScreen(ANSWER_BUTTON_IMAGE, confidence=0.8)
        if answer_button:
            # Click the center of the located button
            center = pyautogui.center(answer_button)
            pyautogui.click(center)
            print("Call answered via button click")
            return True
    except Exception as e:
        print(f"Failed to answer call: {e}")
    return False

def is_call_active():
    """
    Check if a Teams call is currently active.
    """
    teams_window = find_teams_window()
    if teams_window:
        # During active call, title typically contains "Call" or "Meeting"
        active_indicators = ["Call with", "Meeting", "In a call"]
        return any(indicator in teams_window.title for indicator in active_indicators)
    return False

def raise_flag():
    """
    Create the flag file to signal VLC controller to pause video.
    """
    if not FLAG_LOCATION.exists():
        print('Raising flag - pausing video')
        FLAG_LOCATION.touch()

def lower_flag():
    """
    Remove the flag file to signal VLC controller to resume.
    """
    if FLAG_LOCATION.exists():
        print('Lowering flag - resuming video')
        os.remove(FLAG_LOCATION)

def make_own_face_big_macro():
    """
    Legacy macro for Skype - may need adjustment for Teams UI.
    Teams UI is different, so coordinates likely need updating.
    """
    # These coordinates were for Skype - Teams has different layout
    # You'll need to update these for Teams interface
    location_1 = (1876, 46)  # Example - needs calibration
    location_2 = (1804, 179)  # Example - needs calibration

    pyautogui.moveTo(*location_1)
    pyautogui.click()
    time.sleep(1.5)
    pyautogui.moveTo(*location_2)
    pyautogui.click()

# Main monitoring loop
def main():
    print("Starting Teams call controller...")
    print("Make sure Teams is running and visible")
    print("Ensure answer_button.png is in the current directory")

    call_active = False

    while True:
        try:
            if is_call_incoming() and not call_active:
                print("Incoming call detected")
                if answer_call():
                    raise_flag()
                    call_active = True
                    # Optional: maximize Teams window
                    teams_window = find_teams_window()
                    if teams_window:
                        teams_window.maximize()
                        time.sleep(2)  # Wait for UI to settle
                        # Uncomment if you want to run the face macro
                        # make_own_face_big_macro()

            elif call_active and not is_call_active():
                print("Call ended")
                lower_flag()
                call_active = False

            time.sleep(1)  # Poll every second

        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(5)  # Wait longer on error

if __name__ == "__main__":
    main()