param(
  [string]$AppRoot = "C:\Users\21878\Desktop\每天进度\codex",
  [int]$Port = 4173
)

$ErrorActionPreference = "Stop"
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
  Write-Host "工作台已运行：http://127.0.0.1:$Port"
  exit 0
}

if (-not (Test-Path (Join-Path $AppRoot "server.js"))) {
  throw "没有找到工作台：$AppRoot"
}

$node = (Get-Command node -ErrorAction Stop).Source
Start-Process -FilePath $node -ArgumentList @("server.js") -WorkingDirectory $AppRoot -WindowStyle Hidden | Out-Null
Start-Sleep -Milliseconds 900

$state = Invoke-RestMethod "http://127.0.0.1:$Port/api/state"
Write-Host "工作台已启动：http://127.0.0.1:$Port"
Write-Host "队列任务：$($state.jobs.Count)"
