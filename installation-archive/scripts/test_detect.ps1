$p = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*td_relay.py*" }
Write-Host "found $($p.Count) matching"
foreach ($proc in $p) { Write-Host "  PID=$($proc.ProcessId)" }
Write-Host "---"
Write-Host "bool result: $([bool]$p)"
