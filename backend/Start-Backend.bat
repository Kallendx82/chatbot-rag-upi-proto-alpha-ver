@echo off
title UPI Chatbot - Backend Server
color 0A
echo ============================================
echo   UPI Chatbot RAG - Backend Server
echo ============================================
echo.
cd /d "%~dp0"
echo [*] Memulai backend server di port 8000...
echo [*] Tekan Ctrl+C untuk menghentikan server.
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
pause
