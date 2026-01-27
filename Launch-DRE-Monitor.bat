@echo off
REM DRE Guardian - Desktop Launcher for Windows
REM Double-click this file to start the governance monitor

echo.
echo ========================================
echo   DRE GUARDIAN - Live Monitor
echo ========================================
echo.

REM Change to guardian directory
cd /d "%~dp0guardian"

REM Check if virtual environment exists
if exist "..\venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call ..\venv\Scripts\activate.bat
) else if exist "..\.venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
) else (
    echo [!] Warning: No virtual environment found
    echo [!] Using system Python
)

echo [*] Starting governance monitor...
echo [*] Dashboard will open at http://localhost:5173
echo.
echo Press Ctrl+C to stop monitoring
echo.

REM Run the monitor with dashboard
python cli.py monitor --dashboard

REM Keep window open if error occurs
if errorlevel 1 (
    echo.
    echo [!] Monitor stopped with error
    pause
)
