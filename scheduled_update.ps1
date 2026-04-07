# Finance Dashboard — 每日 18:00 自動更新腳本
# 執行順序：重啟 Server → 刷新股票資料 → 備份歷史資料

$LogFile = "$PSScriptRoot\scheduled_update.log"
$BaseUrl = "http://localhost:5000"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Tee-Object -FilePath $LogFile -Append
}

Log "===== 定時更新開始 ====="

# ── 1. 重啟 Flask Server ─────────────────────────────────────────
Log "[1/3] 重啟 Flask Server..."
& "$PSScriptRoot\server.ps1"
Start-Sleep -Seconds 8

# 等待 Server 就緒（最多 30 秒）
$ready = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$BaseUrl/api/popular" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 3
}

if (-not $ready) {
    Log "[1/3] 錯誤：Server 未能在 30 秒內啟動，中止更新。"
    exit 1
}
Log "[1/3] Server 已就緒。"

# ── 2. 刷新所有股票資料（bulk-fetch）────────────────────────────
Log "[2/3] 開始刷新股票資料（bulk-fetch）..."
try {
    # SSE 端點，設定較長 timeout 等待完成
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/bulk-fetch" -TimeoutSec 600 -UseBasicParsing -ErrorAction Stop
    Log "[2/3] bulk-fetch 完成。狀態碼：$($response.StatusCode)"
} catch {
    Log "[2/3] bulk-fetch 警告：$($_.Exception.Message)"
}

# ── 3. 備份歷史資料（backup-history）───────────────────────────
Log "[3/3] 開始備份歷史資料..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/backup-history" -TimeoutSec 900 -UseBasicParsing -ErrorAction Stop
    Log "[3/3] backup-history 完成。狀態碼：$($response.StatusCode)"
} catch {
    Log "[3/3] backup-history 警告：$($_.Exception.Message)"
}

Log "===== 定時更新完成 ====="
