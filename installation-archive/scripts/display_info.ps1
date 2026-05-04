Write-Output "=== CONNECTED MONITORS ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorID | ForEach-Object {
    $name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    $mfr = ($_.ManufacturerName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    Write-Output "  $name (mfr: $mfr) Instance: $($_.InstanceName)"
}

Write-Output "`n=== CONNECTION TYPES ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorConnectionParams | ForEach-Object {
    $type = switch($_.VideoOutputTechnology) {
        0 {"VGA"} 2 {"DVI"} 4 {"DVI"} 5 {"HDMI"} 6 {"LVDS"} 9 {"DisplayPort"} 10 {"DisplayPort"} 11 {"HDMI"} -1 {"Internal"} default {"Unknown($_)"}
    }
    Write-Output "  $($_.InstanceName) -> $type"
}

Write-Output "`n=== DISPLAY SETTINGS ==="
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
    Write-Output "  $($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height) Primary=$($_.Primary)"
}

Write-Output "`n=== NVIDIA-SMI DISPLAY ==="
nvidia-smi --query-gpu=name,display_mode,display_active --format=csv,noheader 2>$null
