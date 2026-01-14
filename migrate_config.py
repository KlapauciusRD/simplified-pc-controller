"""
Configuration Migration Script
Merges existing schedule.json and vlc_config.json into unified config.json
"""

import json
from pathlib import Path


def migrate_configs():
    """Merge old config files into new unified format"""
    
    print("=== Daily Assistant Config Migration ===\n")
    
    # Check for existing configs
    schedule_json = Path('schedule.json')
    vlc_json = Path('vlc_config.json')
    config_json = Path('config.json')
    
    if config_json.exists():
        print("✓ config.json already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Default unified config
    unified_config = {
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
        'teams_buttons': [
            {"label": "Mom", "url": ""},
            {"label": "Dad", "url": ""},
            {"label": "Work", "url": ""},
            {"label": "Friend", "url": ""}
        ],
        'series_dir': 'D:/video/series',
        'movies_dir': 'D:/video/movies',
        'auto_resume': True,
        'fullscreen': False,
        'font_size': 14
    }
    
    # Merge schedule.json if exists
    if schedule_json.exists():
        print(f"\n✓ Found {schedule_json}")
        try:
            with open(schedule_json, 'r') as f:
                schedule_config = json.load(f)
            
            # Merge schedule-related settings
            if 'schedule' in schedule_config:
                unified_config['schedule'] = schedule_config['schedule']
                print(f"  - Migrated {len(schedule_config['schedule'])} schedule items")
            
            if 'weekday_overrides' in schedule_config:
                unified_config['weekday_overrides'] = schedule_config['weekday_overrides']
                print(f"  - Migrated weekday overrides")
            
            if 'water_goal' in schedule_config:
                unified_config['water_goal'] = schedule_config['water_goal']
                print(f"  - Migrated water goal: {schedule_config['water_goal']}")
            
            if 'medication_schedule' in schedule_config:
                unified_config['medication_schedule'] = schedule_config['medication_schedule']
                print(f"  - Migrated {len(schedule_config['medication_schedule'])} medication times")
            
            if 'other_meds' in schedule_config:
                unified_config['other_meds'] = schedule_config['other_meds']
                print(f"  - Migrated other medications")
            
            if 'teams_buttons' in schedule_config:
                unified_config['teams_buttons'] = schedule_config['teams_buttons']
                print(f"  - Migrated {len(schedule_config['teams_buttons'])} Teams buttons")
            
        except Exception as e:
            print(f"  ✗ Error reading schedule.json: {e}")
    else:
        print(f"\n⚠ {schedule_json} not found - using defaults")
    
    # Merge vlc_config.json if exists
    if vlc_json.exists():
        print(f"\n✓ Found {vlc_json}")
        try:
            with open(vlc_json, 'r') as f:
                vlc_config = json.load(f)
            
            # Merge VLC-related settings
            if 'series_dir' in vlc_config:
                unified_config['series_dir'] = vlc_config['series_dir']
                print(f"  - Migrated series directory: {vlc_config['series_dir']}")
            
            if 'movies_dir' in vlc_config:
                unified_config['movies_dir'] = vlc_config['movies_dir']
                print(f"  - Migrated movies directory: {vlc_config['movies_dir']}")
            
            if 'auto_resume' in vlc_config:
                unified_config['auto_resume'] = vlc_config['auto_resume']
                print(f"  - Migrated auto-resume: {vlc_config['auto_resume']}")
            
            if 'fullscreen' in vlc_config:
                unified_config['fullscreen'] = vlc_config['fullscreen']
                print(f"  - Migrated fullscreen: {vlc_config['fullscreen']}")
            
            if 'font_size' in vlc_config:
                unified_config['font_size'] = vlc_config['font_size']
                print(f"  - Migrated font size: {vlc_config['font_size']}")
            
        except Exception as e:
            print(f"  ✗ Error reading vlc_config.json: {e}")
    else:
        print(f"\n⚠ {vlc_json} not found - using defaults")
    
    # Write unified config
    print(f"\n→ Writing unified config.json...")
    try:
        with open('config.json', 'w') as f:
            json.dump(unified_config, f, indent=4)
        print("✓ Migration complete!\n")
        
        # Show summary
        print("Summary:")
        print(f"  - {len(unified_config['schedule'])} schedule items")
        print(f"  - {len(unified_config['teams_buttons'])} Teams buttons")
        print(f"  - Series directory: {unified_config['series_dir']}")
        print(f"  - Movies directory: {unified_config['movies_dir']}")
        
        print("\nNext steps:")
        print("  1. Review config.json and update as needed")
        print("  2. Update Teams button URLs with actual meeting links")
        print("  3. Run: python daily_assistant.py")
        
    except Exception as e:
        print(f"✗ Error writing config.json: {e}")


if __name__ == '__main__':
    migrate_configs()
