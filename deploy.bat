@echo off
cd /d "%~dp0"
.venv\Scripts\pip freeze > requirements.txt
.venv\Scripts\pyinstaller benchmark.py --onefile --name benchmark
pause
