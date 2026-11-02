@echo off
rem La Comunitat - doble clic per a obrir-la (cal Python 3.8 o més nou).
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 comunitat.py
) else (
  python comunitat.py
)
echo.
pause
