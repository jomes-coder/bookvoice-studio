@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"

if not exist ".venv\Scripts\python.exe" (
    echo Python virtual environment not found: .venv\Scripts\python.exe
    echo Please create/install the environment first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m bookvoice.gui
if errorlevel 1 (
    echo.
    echo GUI exited with an error.
    pause
)
