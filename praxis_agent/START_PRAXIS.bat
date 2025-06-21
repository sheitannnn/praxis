@echo off
echo Starting Praxis Agent...
cd /d "%~dp0"
python praxis.py --mode gui
pause
