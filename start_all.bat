@echo off
echo Starting Procurement Intelligence Platform...
echo.
start "Procurement Backend (Port 8000)" cmd /c "%~dp0start_backend.bat"
start "Procurement Frontend (Port 5173)" cmd /c "%~dp0start_frontend.bat"
echo ===================================================
echo Backend & Frontend launched in separate windows!
echo Frontend:          http://localhost:5173
echo Backend API Docs:  http://localhost:8000/docs
echo Demo Credentials:  admin@procurement.dev / Admin123!
echo ===================================================