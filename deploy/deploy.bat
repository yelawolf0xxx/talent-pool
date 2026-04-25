@echo off
chcp 65001 >nul
echo ========================================
echo   AI Resume System - Deploy to Server
echo ========================================
echo.

set SERVER=root@192.168.3.84

:: Step 1: Build frontend
echo [1/4] Building frontend...
cd /d "%~dp0..\frontend"
call npm run build
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)
echo Frontend build complete.

:: Step 2: Sync backend code
echo.
echo [2/4] Syncing backend to server...
cd /d "%~dp0.."
scp -r backend\* %SERVER%:/usr/TalentPool/backend/
echo Backend synced.

:: Step 3: Sync frontend dist
echo.
echo [3/4] Syncing frontend dist to server...
scp -r frontend\dist\* %SERVER%:/usr/TalentPool/frontend-dist/
echo Frontend synced.

:: Step 4: Restart backend service
echo.
echo [4/4] Restarting backend service...
ssh %SERVER% "systemctl restart talent-pool && sleep 2 && curl -s http://127.0.0.1:8001/health"
echo.

echo ========================================
echo   Deploy complete!
echo   Frontend: http://192.168.3.84
echo   Backend:  http://192.168.3.84:8001
echo ========================================
echo.
pause
