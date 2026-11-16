@echo off
setlocal
title ADA Jarvis Operating System

set "ROOT_DIR=D:\ANTIGRAVITY PROJECTS\Transfer_To_New_Laptop\NOVA_AI"
cd /d "%ROOT_DIR%"

:: Check if backend is running on 8000
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% NEQ 0 (
    echo Starting ADA Backend Server...
    start /b "" "%ROOT_DIR%\backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
    timeout /t 3 /nobreak >nul
)

:: Check if frontend is running on 5173
netstat -ano | findstr :5173 | findstr LISTENING >nul
if %ERRORLEVEL% NEQ 0 (
    echo Starting ADA Frontend HUD...
    cd /d "%ROOT_DIR%\frontend"
    start /b "" npm.cmd run dev -- --host 0.0.0.0 --port 5173
    cd /d "%ROOT_DIR%"
    timeout /t 2 /nobreak >nul
)

:: Launch ADA in Native Desktop App Window
if exist "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" (
    start "" "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" --app=http://localhost:5173 --window-size=1280,840
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5173 --window-size=1280,840
) else (
    start http://localhost:5173
)

exit
