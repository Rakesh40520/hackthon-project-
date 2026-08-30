@echo off
cd /d "c:\Users\lordo\OneDrive\Desktop\project _uldathon\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
