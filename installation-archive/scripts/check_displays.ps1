Write-Output "=== MONITOR STATUS ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorID | ForEach-Object {
    $name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    Write-Output "  $name | Active=$($_.Active) | Instance=$($_.InstanceName)"
}

Write-Output "`n=== ACTIVE SCREENS ==="
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
    Write-Output "  $($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height) at ($($_.Bounds.X),$($_.Bounds.Y)) Primary=$($_.Primary)"
}
