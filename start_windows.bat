@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt || exit /b 1
py desktop.py
pause
