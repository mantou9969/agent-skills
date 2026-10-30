param(
  [string]$AppRoot = "C:\Users\21878\Desktop\每天进度\codex"
)

$pidFile = Join-Path $AppRoot "workspace\supervisor.pid"
if (-not (Test-Path $pidFile)) {
  Write-Host "没有发现守护进程记录。"
  exit 0
}

$supervisorId = [int](Get-Content -LiteralPath $pidFile -Raw)
Stop-Process -Id $supervisorId -ErrorAction SilentlyContinue
Write-Host "后台守护进程已停止。工作台当前进程不受影响。"
