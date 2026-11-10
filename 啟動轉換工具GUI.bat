@echo off
chcp 65001 > nul
title PDF 轉 Markdown 投顧報告智能轉換器
cd /d "%~dp0"
echo 正在啟動投顧報告轉換器 GUI 介面...

where python >nul 2>nul
if %errorlevel% equ 0 (
    python "gui_converter.py"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "gui_converter.py"
) else if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" "gui_converter.py"
) else (
    echo [錯誤] 找不到 Python 執行環境，請先確認已安裝 Python 3.10+。
    pause
)

if %errorlevel% neq 0 (
    echo.
    echo 執行完畢或發生異常，請按任意鍵關閉...
    pause > nul
)

