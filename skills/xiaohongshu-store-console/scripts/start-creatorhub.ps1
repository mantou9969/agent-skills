param(
  [int]$Port = 8200
)

$root = "C:\Users\21878\Desktop\每天进度\codex\integrations\creatorhub"
if (-not (Test-Path (Join-Path $root "start.cmd"))) {
  throw "CreatorHub 尚未安装。"
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
  $arguments = "/c start.cmd --no-open --port $Port"
  Start-Process -FilePath "cmd.exe" -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 3
}

Write-Host "CreatorHub: http://127.0.0.1:$Port"
