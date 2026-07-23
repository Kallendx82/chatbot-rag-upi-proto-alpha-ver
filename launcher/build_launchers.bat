@echo off
REM Build launcher .exe files using PyInstaller
REM Run this from project root if you modified launcher.py or add_pdf_launcher.py

setlocal enabledelayedexpansion

echo === Building UPI Chatbot Launcher ===
echo.

set PROJECT_ROOT=%~dp0
set VENV_PYTHON=!PROJECT_ROOT!backend\.venv\Scripts\python.exe

if not exist "!VENV_PYTHON!" (
    echo [ERROR] Backend venv not found. Run UPI-Chatbot-Launcher.exe first.
    exit /b 1
)

echo [*] Checking PyInstaller...
"!VENV_PYTHON!" -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] Installing PyInstaller...
    "!VENV_PYTHON!" -m pip install pyinstaller
)

echo.
echo [*] Building UPI-Chatbot-Launcher.exe...
cd /d "!PROJECT_ROOT!"
"!VENV_PYTHON!" -m PyInstaller launcher\launcher.py --onefile --name UPI-Chatbot-Launcher --distpath . --workpath build --specpath build

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed.
    exit /b 1
)

echo.
echo [*] Building Add-New-PDF.exe...
"!VENV_PYTHON!" -m PyInstaller launcher\add_pdf_launcher.py --onefile --name Add-New-PDF --distpath . --workpath build --specpath build

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed.
    exit /b 1
)

echo.
echo [OK] All launchers built successfully!
echo     - UPI-Chatbot-Launcher.exe
echo     - Add-New-PDF.exe
echo.

REM Clean up build artifacts
if exist build (
    echo [*] Cleaning up build directory...
    rmdir /s /q build
)

echo [OK] Done.
exit /b 0
