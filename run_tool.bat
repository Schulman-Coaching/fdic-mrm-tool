@echo off
echo FDIC MRM Data Collection Tool
echo =============================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH. Trying 'py' command...
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not in PATH
        echo Please install Python 3.8+ and try again
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Using Python command: %PYTHON_CMD%
echo.

REM Check if dependencies are installed
echo Checking dependencies...
%PYTHON_CMD% -c "import pandas, pydantic, sqlalchemy, click, rich" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK
echo.

REM Run the requested command
if "%1"=="" (
    echo Usage: run_tool.bat [command]
    echo.
    echo Available commands:
    echo   init      - Initialize database and import existing data
    echo   collect   - Collect FDIC bank data
    echo   export    - Export data to Excel
    echo   stats     - Show database statistics
    echo   test      - Run system tests
    echo   help      - Show detailed help
    echo.
    pause
    exit /b 0
)

if "%1"=="test" (
    echo Running system tests...
    %PYTHON_CMD% test_system.py
) else if "%1"=="help" (
    %PYTHON_CMD% main.py --help
) else (
    %PYTHON_CMD% main.py %*
)

if %errorlevel% neq 0 (
    echo.
    echo Command failed with error code %errorlevel%
    pause
)