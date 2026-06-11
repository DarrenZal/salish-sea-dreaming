$ErrorActionPreference = 'SilentlyContinue'
Write-Host "=== Python processes with command line ==="
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Select-Object ProcessId, ParentProcessId, CreationDate, @{N='Cmd';E={$_.CommandLine}} |
  Format-List

Write-Host ""
Write-Host "=== Autolume autostart log tail ==="
$log = Get-ChildItem C:\Users\user\autolume_run.log
if ($log) { Get-Content $log.FullName -Tail 30 } else { Write-Host "(no log)" }

Write-Host ""
Write-Host "=== Autolume debug log tail ==="
$dbg = Get-ChildItem C:\Users\user\autolume_debug.log
if ($dbg) { Get-Content $dbg.FullName -Tail 15 } else { Write-Host "(no log)" }
