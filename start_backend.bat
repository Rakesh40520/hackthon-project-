@echo off
cd /d "%~dp0backend"
echo ============================================
echo Starting Backend Server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo ============================================
"%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
pause