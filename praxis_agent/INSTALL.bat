@echo off
title Praxis Agent Installer
color 0F
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                    Praxis Agent Installer                    ║
echo  ║                                                              ║
echo  ║            🤖 Your Intelligent AI Assistant 🤖            ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

REM Set console to UTF-8 for emojis
chcp 65001 > nul

echo 🔍 Checking system requirements...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo 📥 Please install Python first:
    echo    1. Go to https://python.org/downloads/
    echo    2. Download Python 3.8 or higher
    echo    3. During installation, check "Add Python to PATH"
    echo    4. Run this installer again
    echo.
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% LSS 3 (
    echo ❌ Python version too old. Need Python 3.8+
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

if %MAJOR% EQU 3 if %MINOR% LSS 8 (
    echo ❌ Python version too old. Need Python 3.8+
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo ✅ Python version compatible: %PYTHON_VERSION%
echo.

REM Change to the script directory
cd /d "%~dp0"

echo 📦 Installing Praxis Agent...
echo.

REM Run the Python setup script
echo 🔧 Running setup script...
python setup.py

if errorlevel 1 (
    echo.
    echo ❌ Installation failed!
    echo.
    echo 🛠️ Troubleshooting:
    echo    1. Make sure you have internet connection
    echo    2. Try running as Administrator
    echo    3. Check the error messages above
    echo.
    echo 📖 For help, see TROUBLESHOOTING.md
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Installation completed successfully!
echo.

echo 🔑 Next Steps:
echo.
echo 1. Set up your AI provider:
echo    📝 Edit config\praxis_config.yaml
echo    🔗 Add your OpenRouter API key (recommended)
echo    🏠 Or install Ollama for local AI (free)
echo.
echo 2. Start Praxis Agent:
echo    🖱️ Double-click START_PRAXIS.bat
echo    💻 Or run: python praxis.py
echo.
echo 3. Look for the system tray icon and enjoy!
echo.

echo 📚 Documentation:
echo    📖 README.md - Full feature guide
echo    🚀 INSTALL_GUIDE.md - Beginner tutorial  
echo    🔧 TROUBLESHOOTING.md - Fix common issues
echo.

echo 🎉 Praxis Agent is ready to use!
echo.
pause
