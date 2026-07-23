@echo off
REM Ingestion batch script - repeatable dari command line
REM Usage: ingest.bat "C:\path\to\pdfs" "CategoryName"
REM         ingest.bat --help

setlocal enabledelayedexpansion

if "%~1"=="" goto :usage
if /i "%~1"=="--help" goto :usage
if /i "%~1"=="/?" goto :usage

set PDF_DIR=%~1
set CATEGORY=%~2

if not exist "!PDF_DIR!" (
    echo [ERROR] PDF folder not found: !PDF_DIR!
    exit /b 1
)

if "!CATEGORY!"=="" (
    echo [ERROR] Category name required
    echo Usage: ingest.bat "C:\path\to\pdfs" "CategoryName"
    exit /b 1
)

REM Find project root and backend venv
for %%F in ("%~dp0.") do set PROJECT_ROOT=%%~dpF
set BACKEND_DIR=!PROJECT_ROOT!backend
set VENV_PYTHON=!BACKEND_DIR!\.venv\Scripts\python.exe
set PIPELINE_SCRIPT=!BACKEND_DIR!\scripts\ingestion\run_pipeline.py

if not exist "!VENV_PYTHON!" (
    echo [ERROR] Backend venv not found at !VENV_PYTHON!
    echo        Run UPI-Chatbot-Launcher.exe first to set up venv
    exit /b 1
)

echo [*] Project root   : !PROJECT_ROOT!
echo [*] PDF folder     : !PDF_DIR!
echo [*] Category       : !CATEGORY!
echo.

cd /d "!BACKEND_DIR!"
"!VENV_PYTHON!" "!PIPELINE_SCRIPT!" --pdf-dir "!PDF_DIR!" --category "!CATEGORY!"

if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Ingestion selesai. Restart backend agar dokumen baru bisa dicari.
    exit /b 0
) else (
    echo.
    echo [ERROR] Ingestion gagal - lihat pesan di atas.
    exit /b 1
)

:usage
echo.
echo === UPI Chatbot - Repeatable PDF Ingestion ===
echo.
echo USAGE:
echo   ingest.bat "C:\path\to\pdfs" "CategoryName"
echo.
echo EXAMPLES:
echo   ingest.bat "D:\Project\chatbot-rag-upi-alpha\New PDF\MyPDFs" "BiroSDM"
echo   ingest.bat "C:\Users\User\Downloads\NewDocs" "Perpustakaan"
echo.
echo AFTER:
echo   Restart backend: run UPI-Chatbot-Launcher.exe
echo.
exit /b 0
