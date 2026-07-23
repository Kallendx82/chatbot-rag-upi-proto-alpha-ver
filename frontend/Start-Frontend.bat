@echo off
title UPI Chatbot - Frontend Server
color 0B
echo ============================================
echo   UPI Chatbot RAG - Frontend Server
echo ============================================
echo.
cd /d "%~dp0"
echo [*] Memulai frontend server di port 3000...
echo [*] Tekan Ctrl+C untuk menghentikan server.
echo.
npm run dev
pause
