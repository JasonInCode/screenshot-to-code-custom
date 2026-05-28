@echo off
setlocal enabledelayedexpansion

:: One-click startup script: kill port-hogging processes, then launch frontend & backend in separate cmd windows
::
:: Usage:
::   start.bat                    (default frontend 5173, backend 7001)
::   start.bat 3000 8000          (frontend 3000, backend 8000)

set "FRONTEND_PORT=%~1"
set "BACKEND_PORT=%~2"

if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5173
if "%BACKEND_PORT%"=="" set BACKEND_PORT=7001

set "PROJECT_DIR=%~dp0"

:: Set UTF-8 encoding for Python console output
set PYTHONIOENCODING=utf-8

echo ==================================================
echo  Screenshot to Code - One-click Startup
echo ==================================================

:: Kill port-hogging processes using PowerShell + taskkill /T
echo.
echo Cleaning ports %FRONTEND_PORT% and %BACKEND_PORT%...
call :KillPort %FRONTEND_PORT%
call :KillPort %BACKEND_PORT%

:: Launch frontend and backend
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"

echo.
echo Launching backend (port %BACKEND_PORT%) + frontend (port %FRONTEND_PORT%)...

start "Backend :%BACKEND_PORT%" cmd /k "set PYTHONIOENCODING=utf-8 && set IS_DEBUG_ENABLED=True && cd /d "%BACKEND_DIR%" && python -m poetry run uvicorn main:app --port %BACKEND_PORT% --reload --ws-ping-interval=60 --ws-ping-timeout=30"
start "Frontend :%FRONTEND_PORT%" cmd /k "cd /d "%FRONTEND_DIR%" && pnpm install && pnpm run dev -- --port %FRONTEND_PORT%"

echo.
echo Startup complete!
echo    Frontend: http://localhost:%FRONTEND_PORT%
echo    Backend:  http://localhost:%BACKEND_PORT%
echo ==================================================

goto :eof

:: Kill processes on a given port using PowerShell for precise matching
:KillPort
set "PORT=%~1"
set "FOUND=0"

:: PowerShell handles IPv4/IPv6 natively and outputs clean PIDs
for /f %%p in ('powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort %PORT% -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -ne 0 }"') do (
    echo   Killing PID %%p and children ^(port %PORT%^)
    taskkill /F /T /PID %%p >nul 2>&1
    set "FOUND=1"
)

if "!FOUND!"=="0" (
    echo   Port %PORT% is free
)
exit /b 0
