$ErrorActionPreference = "Stop"

$comfyRoot = "D:\ComfyUI-AMD"
$python = Join-Path $comfyRoot ".venv\Scripts\python.exe"
$port = 8188
$logDir = Join-Path $comfyRoot "logs"
$stdoutLog = Join-Path $logDir "comfyui.log"
$stderrLog = Join-Path $logDir "comfyui-error.log"

if (-not (Test-Path -LiteralPath $python)) {
    throw "ComfyUI Python 环境不存在：$python"
}

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Host "ComfyUI 已运行：http://127.0.0.1:$port"
    exit 0
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
Start-Process `
    -FilePath $python `
    -ArgumentList @(
        "main.py",
        "--listen", "127.0.0.1",
        "--port", "$port",
        "--disable-auto-launch"
    ) `
    -WorkingDirectory $comfyRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog

$ready = $false
for ($attempt = 0; $attempt -lt 60; $attempt += 1) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest `
            -Uri "http://127.0.0.1:$port" `
            -UseBasicParsing `
            -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # ComfyUI 仍在加载。
    }
}

if (-not $ready) {
    throw "ComfyUI 启动超时，请查看 $stderrLog"
}

Write-Host "ComfyUI 已启动：http://127.0.0.1:$port"
