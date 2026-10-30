Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class WorkbenchWake {
  [DllImport("kernel32.dll")]
  public static extern uint SetThreadExecutionState(uint flags);
}
"@

Write-Host "长任务防休眠已启动。按 Ctrl+C 结束。"
try {
  while ($true) {
    [WorkbenchWake]::SetThreadExecutionState(0x80000001) | Out-Null
    Start-Sleep -Seconds 30
  }
} finally {
  [WorkbenchWake]::SetThreadExecutionState(0x80000000) | Out-Null
}
