@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python seed_demo.py
if errorlevel 1 (
  echo.
  echo Could not prepare demo data. Start MongoDB Server and check MONGO_URI in .env.
  pause
  exit /b 1
)
python app.py
pause
