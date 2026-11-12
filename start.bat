@echo off
setlocal
title Dishwasher Dish Counter

cd /d "%~dp0"

cls
echo.
echo  ==================================================
echo   Dishwasher Dish Counter
echo  ==================================================
echo.
echo   Initializing...
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.11 --version >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=py -3.11"
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo   Python was not found.
        echo   Please install Python 3.11 or newer.
        echo.
        pause
        exit /b 1
    )
)

echo   [1/4] Preparing environment...
if not exist ".venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo   Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

echo   [2/4] Checking dependencies...
if not exist ".venv\.deps_installed" (
    python -m pip install --upgrade pip
    pip install -r requirements.txt

    if errorlevel 1 (
        echo.
        echo   Failed to install dependencies.
        pause
        exit /b 1
    )

    echo ok > ".venv\.deps_installed"
)

echo   [3/4] Loading application...
timeout /t 1 >nul

echo   [4/4] Starting local server...
echo.
echo  ==================================================
echo   App URL: http://127.0.0.1:5000
echo  ==================================================
echo.

start "" cmd /c "timeout /t 4 >nul && start http://127.0.0.1:5000"

python app.py

echo.
echo   Server stopped.
pause
