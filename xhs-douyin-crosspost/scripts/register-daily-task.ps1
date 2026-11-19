# 注册/取消"每天定点备好三条视频"的计划任务
#
#   pwsh -File register-daily-task.ps1                      # 每天 20:00 备三条
#   pwsh -File register-daily-task.ps1 -Time 09:30 -Count 3
#   pwsh -File register-daily-task.ps1 -DryRun              # 只看会创建什么
#   pwsh -File register-daily-task.ps1 -Remove              # 取消
#
# 它只"备料"：抓好的素材转成片、写好待审单，绝不会自己发出去。
# 发布必须人点头后再跑 xp.py approve + publish。

param(
    [string]$Time = "20:00",
    [int]$Count = 3,
    [string]$TaskName = "xhs-crosspost-daily",
    [string]$Python = "",
    [switch]$DryRun,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$xp = Join-Path $PSScriptRoot "xp.py"

if (-not (Test-Path $xp)) { throw "找不到 xp.py：$xp" }
if (-not $Python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "找不到 python，用 -Python 指定完整路径" }
    $Python = $cmd.Source
}

if ($Remove) {
    if ($DryRun) { "会删除计划任务：$TaskName"; exit 0 }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    "已取消：$TaskName"
    exit 0
}

$argLine = '"{0}" "{1}" daily --count {2}' -f $Python, $xp, $Count
$action = New-ScheduledTaskAction -Execute $Python -Argument ('"{0}" daily --count {1}' -f $xp, $Count) -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 3)

if ($DryRun) {
    "会创建计划任务：$TaskName"
    "  每天 $Time 执行：$Python $argLine"
    "  只备料，不发布"
    exit 0
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "小红书/抖音搬运：每天备好待审的短视频，发布需人工点头" -Force | Out-Null
"已注册：$TaskName，每天 $Time 备 $Count 条（只备料，不发布）"
"查看：Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
