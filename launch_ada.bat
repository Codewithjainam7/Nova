@echo off
cd /d "%~dp0"

:: 1. Check & Start Backend Engine (port 8000)
set "BACKEND_STATUS="
for /f "delims=" %%i in ('curl.exe -s -o NUL -w "%%{http_code}" http://localhost:8000/health 2^>nul') do set "BACKEND_STATUS=%%i"
if not "%BACKEND_STATUS%"=="200" (
    echo [ADA Launcher] Starting Backend Engine...
    start "" /b cmd.exe /c ""%~dp0backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > "%~dp0backend_daemon.log" 2>&1"
)

:: 2. Wait for Backend Engine (port 8000) to respond with 200 OK
set /a b_wait=0
:WAIT_BACKEND
for /f "delims=" %%i in ('curl.exe -s -o NUL -w "%%{http_code}" http://localhost:8000/health 2^>nul') do set "B_CODE=%%i"
if "%B_CODE%"=="200" goto BACKEND_OK
set /a b_wait+=1
if %b_wait% geq 35 goto BACKEND_OK
ping 127.0.0.1 -n 2 >nul 2>&1
goto WAIT_BACKEND
:BACKEND_OK

:: 3. Launch Electron Cleanly
taskkill /F /IM electron.exe >nul 2>&1
ping 127.0.0.1 -n 2 >nul 2>&1
start "" "%~dp0frontend\node_modules\electron\dist\electron.exe" "%~dp0frontend\electron\main.cjs"
exit
