@echo off
title Database Setup - Attendance System
cd /d "%~dp0"

echo ===============================================
echo   🔧 ATTENDANCE DATABASE SETUP
echo ===============================================
echo.

echo Setting up database and tables...
"d:\Printcare\attendance-system\.venv\Scripts\python.exe" setup_database.py

echo.
echo Database setup complete!
pause
