@echo off
title ZelaznaCRM

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [BLAD] Nie znaleziono srodowiska wirtualnego .venv
    echo Uruchom najpierw: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Uruchamianie ZelaznaCRM...
start "" "http://127.0.0.1:8000"
python manage.py runserver 127.0.0.1:8000

pause
