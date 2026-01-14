@echo off
echo ========================================
echo Daily Assistant - Setup and Installation
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/4] Python found
python --version

REM Install dependencies
echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install
    echo The app may run with limited functionality
)

REM Check for existing config
echo.
echo [3/4] Checking configuration...
if exist config.json (
    echo Config file found: config.json
) else (
    if exist schedule.json (
        echo Found old schedule.json - running migration...
        python migrate_config.py
    ) else (
        echo No config found - app will create default config.json on first run
    )
)

REM Create directories
echo.
echo [4/4] Setting up directories...
if not exist schedule_logs mkdir schedule_logs
if not exist schedule_exports mkdir schedule_exports
echo Directories ready

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit config.json to customize your schedule
echo   2. Update Teams button URLs with your meeting links
echo   3. Verify video directories in config.json
echo   4. Run: python daily_assistant.py
echo.
echo For help, see README.md or QUICKSTART.md
echo.
pause
