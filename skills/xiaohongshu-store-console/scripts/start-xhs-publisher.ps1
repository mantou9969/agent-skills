param(
  [int]$Port = 8100
)

$root = "C:\Users\21878\Desktop\每天进度\codex\integrations\xhs_ai_publisher"
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "xhs_ai_publisher 尚未安装依赖，请先运行它的安装脚本。"
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
  Start-Process -FilePath $python -ArgumentList @(
    "-m", "uvicorn", "src.web.app:app",
    "--host", "127.0.0.1",
    "--port", "$Port"
  ) -WorkingDirectory $root -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 3
}

Write-Host "XHS Publisher: http://127.0.0.1:$Port"
