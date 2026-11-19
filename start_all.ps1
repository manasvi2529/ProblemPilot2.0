Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   ProblemPilot AI — Launching Full-Stack Services" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonExe = Join-Path $rootDir "venv\Scripts\python.exe"

if (-Not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "`n[1/2] Starting FastAPI Backend on Port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir'; & '$pythonExe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Next.js Frontend on Port 3000..." -ForegroundColor Yellow
$webDir = Join-Path $rootDir "web"
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$webDir'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "`nOpening browser to http://localhost:3000..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host "`n[OK] Backend and Frontend successfully launched in dedicated windows." -ForegroundColor Green
Write-Host "   - Frontend UI : http://localhost:3000" -ForegroundColor White
Write-Host "   - FastAPI API : http://127.0.0.1:8000" -ForegroundColor White
