@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto failed
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean AimForge.spec
if errorlevel 1 goto failed
echo.
echo Build complete: dist\AimForge.exe
pause
exit /b 0
:failed
echo.
echo Build failed. See the error above.
pause
exit /b 1
