@echo off
cd /d "%~dp0"
.venv\Scripts\pip freeze > requirements.txt
.venv\Scripts\pyinstaller bitaxe_hashrate_benchmark.py --onefile --name Axe_benchmark
pause
