@echo off
setlocal
echo =============================================
echo    UIDAI Load Predictor - Dashboard Launcher
echo =============================================
echo.

:: Check for existing processes on ports 8000 and 5173
echo Checking for active server processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    if not "%%a"=="" (
        echo Warning: Port 8000 is already in use. Attempting to terminate PID %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo 1. Launching Backend API (FastAPI)...
start "UIDAI-Backend" /min cmd /k "python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting 3 seconds for backend to warm up...
timeout /t 3 /nobreak >nul

echo 2. Launching Frontend (React/Vite)...
start "UIDAI-Frontend" /min cmd /k "cd dashboard && npm run dev"

echo.
echo ---------------------------------------------
echo DASHBOARD URL: http://localhost:5173
echo API URL:       http://localhost:8000
echo ---------------------------------------------
echo Logs are running in minimized windows.
echo Press any key to exit this launcher.
pause >nul
