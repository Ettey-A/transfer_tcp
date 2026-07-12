@echo off
setlocal
cd /d "%~dp0"

if not exist "main.py" (
    echo.
    echo ERROR: main.py was not found in this folder:
    echo   %CD%
    echo.
    echo Expected files: main.py, requirements.txt, file_transfer\
    echo.
    dir /b
    echo.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found. Install Python 3 from https://python.org
    echo During setup, check "Add python.exe to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing / updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo Starting File Transfer...
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
