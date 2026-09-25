@echo off
cd /d %~dp0backend
call venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000
pause
