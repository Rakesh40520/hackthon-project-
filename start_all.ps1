Write-Host "Starting Procurement Intelligence Platform..." -ForegroundColor Cyan

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"
$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; & '$pythonPath' -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev"

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host "Servers launched in separate windows!" -ForegroundColor Green
Write-Host "Frontend:          http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend API Docs:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Demo Credentials:  admin@procurement.dev / Admin123!" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Green