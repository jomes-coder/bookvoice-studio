@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"

if not exist ".venv\Scripts\python.exe" (
    echo 未找到虚拟环境: .venv\Scripts\python.exe
    echo 请先按项目说明创建虚拟环境并安装依赖。
    pause
    exit /b 1
)

".venv\Scripts\python.exe" tools\build_windows_exe.py

if errorlevel 1 (
    pause
    exit /b %errorlevel%
)

pause
