param(
  [string]$BaseUrl = "http://127.0.0.1:4173"
)

$ErrorActionPreference = "Stop"
$state = Invoke-RestMethod "$BaseUrl/api/state"

Write-Host "后台自动流程：$($state.runner.enabled)"
Write-Host "后台状态：$($state.runner.message)"
Write-Host ""
$state.jobs |
  Select-Object title, stage, blockedReason, @{Name = "更新"; Expression = { $_.updatedAt } } |
  Format-Table -AutoSize
