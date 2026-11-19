Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Stopping all processes on port 8000 and 3000" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$ports = @(8000, 3000)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pidToKill in $pids) {
            if ($pidToKill -gt 0) {
                Write-Host "Terminating process PID $pidToKill on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Host "Port $port is already free (no active processes)." -ForegroundColor Green
    }
}

Write-Host "`n[OK] Ports 8000 and 3000 are completely cleared." -ForegroundColor Green
