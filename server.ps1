# Finance Dashboard — server management script
# Usage:
#   .\server.ps1          start (kills old instance first)
#   .\server.ps1 stop     kill running server
#   .\server.ps1 status   show status

param([string]$Action = "start")

$Port    = 5000
$PidFile = "$PSScriptRoot\.server.pid"
$AppFile = "$PSScriptRoot\app.py"

function Kill-Port {
    $pids = (netstat -ano | Select-String ":$Port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Sort-Object -Unique)
    foreach ($p in $pids) {
        if ($p -match '^\d+$' -and $p -ne '0') {
            try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
    # Also kill any stray python processes running app.py
    Get-WmiObject Win32_Process -Filter "Name='python.exe'" | Where-Object {
        $_.CommandLine -like "*app.py*"
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    # Wait until port is free (max 5s)
    $waited = 0
    while ($waited -lt 5) {
        $inUse = netstat -ano | Select-String ":$Port\s"
        if (-not $inUse) { break }
        Start-Sleep -Milliseconds 500
        $waited += 0.5
    }
}

function Get-ServerPid {
    if (Test-Path $PidFile) {
        $stored = Get-Content $PidFile -Raw
        if ($stored -match '^\d+$') { return [int]$stored }
    }
    return $null
}

switch ($Action) {
    "stop" {
        Write-Host "Stopping server..."
        Kill-Port
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force }
        Write-Host "Server stopped."
    }

    "status" {
        $inUse = netstat -ano | Select-String ":$Port\s"
        if ($inUse) {
            $pid = Get-ServerPid
            Write-Host "Server is RUNNING on port $Port (PID: $pid)"
        } else {
            Write-Host "Server is STOPPED"
        }
    }

    default {
        Write-Host "Stopping any existing server on port $Port..."
        Kill-Port

        Write-Host "Starting Finance Dashboard..."
        $proc = Start-Process -FilePath "python" `
            -ArgumentList $AppFile `
            -WorkingDirectory $PSScriptRoot `
            -WindowStyle Hidden `
            -PassThru
        $proc.Id | Out-File $PidFile -Force
        Write-Host "Server started (PID: $($proc.Id)) at http://localhost:$Port"
    }
}
