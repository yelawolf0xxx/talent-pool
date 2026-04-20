@echo off
echo ========================================
echo   AI 简历人才库 - 启动脚本
echo ========================================
echo.

REM 启动后端
echo [1/2] 启动后端服务 (端口 8000)...
start "Backend" cmd /k "cd /d D:\Users\Eholly\IdeaProjects\talent-pool\backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM 启动前端
echo [2/2] 启动前端服务 (端口 5173)...
start "Frontend" cmd /k "cd /d D:\Users\Eholly\IdeaProjects\talent-pool\frontend && npm run dev"

echo.
echo 启动完成！
echo 后端: http://127.0.0.1:8000
echo 前端: http://127.0.0.1:3000
echo.
echo 按任意键退出此窗口...
pause >nul
