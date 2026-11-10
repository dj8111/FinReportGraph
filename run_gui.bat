@echo off
chcp 65001 > nul
title PDF to Markdown Converter
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "gui_converter.py"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "gui_converter.py"
) else if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" "gui_converter.py"
) else (
    echo [ERROR] Python environment not found. Please install Python 3.10+.
    pause
)
