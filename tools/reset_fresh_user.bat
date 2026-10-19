@echo off
setlocal
title SceneryX Fresh User Reset Routine

echo =================================================================
echo   SceneryX Fresh User Environment Reset Launcher
echo =================================================================
echo.

:: Check for Administrative privileges and elevate if needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: Run the PowerShell reset script with execution policy bypass
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset_fresh_user.ps1"

echo.
pause
