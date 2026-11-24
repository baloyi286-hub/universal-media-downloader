@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt || exit /b 1
py -m uvicorn app:app --host 0.0.0.0 --port 8765
pause
