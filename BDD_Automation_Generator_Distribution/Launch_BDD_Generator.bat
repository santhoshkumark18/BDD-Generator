@echo off
title BDD Automation Generator
echo.
echo ========================================
echo   BDD Automation Generator
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python is available
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if main file exists
if not exist "bdd_generator.py" (
    echo ❌ bdd_generator.py not found!
    echo Make sure all files are in the same directory.
    echo.
    pause
    exit /b 1
)

echo 🚀 Starting BDD Automation Generator...
echo.

REM Try to run the application
python bdd_generator.py

REM If there was an error, show it
if errorlevel 1 (
    echo.
    echo ❌ The application encountered an error.
    echo.
    echo Troubleshooting steps:
    echo 1. Install dependencies: pip install -r requirements.txt
    echo 2. Check your Python version: python --version
    echo 3. Make sure all files are in the same directory
    echo.
    pause
) else (
    echo.
    echo 👋 Application closed normally.
)

echo.
echo Press any key to exit...
pause >nul
