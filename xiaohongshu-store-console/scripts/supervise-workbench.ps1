param(
  [string]$AppRoot = "C:\Users\21878\Desktop\每天进度\codex",
  [int]$Port = 4173
)

$pidFile = Join-Path $AppRoot "workspace\supervisor.pid"
$logFile = Join-Path $AppRoot "workspace\supervisor.log"
New-Item -ItemType Directory -Path (Split-Path $pidFile) -Force | Out-Null
Set-Content -LiteralPath $pidFile -Value $PID -Encoding utf8

try {
  while ($true) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listener) {
      $node = (Get-Command node -ErrorAction Stop).Source
      Start-Process -FilePath $node -ArgumentList @("server.js") -WorkingDirectory $AppRoot -WindowStyle Hidden | Out-Null
      Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format o) restarted workbench" -Encoding utf8
    }
    Start-Sleep -Seconds 10
  }
} finally {
  if (Test-Path $pidFile) {
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
  }
}
