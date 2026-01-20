@echo off
setlocal
echo ===================================================
echo    UIDAI Load Predictor - Operational Dashboard
echo ===================================================
echo.

:: 1. Environment Audit
echo [1/4] Verifying environment...
if not exist "dashboard\node_modules" (
    echo [!] "node_modules" not found in dashboard folder.
    echo [!] Running "npm install" first...
    cd dashboard && call npm install && cd ..
)

:: 2. Data Pipeline Execution
echo [2/4] Running Data Processing Pipeline...
echo - This may take a moment (Ingestion, Cleaning, Forecasting)...
python run_pipeline.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] Data Pipeline failed. Services will not start.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Port Sanitization
echo [3/4] Cleaning up active server processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 4. Strategic Service Launch
echo [4/4] Launching Backend ^& Frontend Services...

echo - Initializing Analytical Engine (Backend)...
start "UIDAI-Backend" /min cmd /k "python api/main.py"

echo - Waiting for Handshake...
timeout /t 5 /nobreak >nul

:: Verification of Backend
echo - Checking API Health...
powershell -Command "try { $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing; if ($resp.StatusCode -eq 200) { Write-Host 'Backend Online!' -ForegroundColor Green } else { Write-Host 'Backend Error Code: ' + $resp.StatusCode -ForegroundColor Red } } catch { Write-Host 'Backend Unreachable!' -ForegroundColor Red }"

echo - Initializing Intelligence Dashboard (Frontend)...
start "UIDAI-Frontend" /min cmd /k "cd dashboard && npm run dev"

echo.
echo ---------------------------------------------------
echo DASHBOARD URL: http://localhost:5173
echo API URL:       http://localhost:8000
echo ---------------------------------------------------
echo.
echo Success! Both services are running in background tabs.
echo.
echo Press any key to terminate all services and exit.
pause >nul

:: Cleanup on exit
echo Terminating services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo.
echo Shutdown complete.
exit
