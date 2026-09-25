@echo off
setlocal
cd /d %~dp0backend
echo ===============================================
echo SURAKSHA NER - Backend Setup
echo ===============================================
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
echo.
echo Setup complete.
echo Start backend with: START_BACKEND.bat
pause
