@echo off
setlocal

cd /d "%~dp0"

echo Installing required packages...
py -m pip install -r requirements.txt
if errorlevel 1 (
	echo.
	echo An error occurred during installation.
	pause
	exit /b 1
)

echo.
echo Package installation completed.
pause