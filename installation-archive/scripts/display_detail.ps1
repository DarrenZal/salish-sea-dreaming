Write-Output "=== MONITOR EDID DETAILS ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorID | ForEach-Object {
    $name = ($_.UserFriendlyName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    $mfr = ($_.ManufacturerName | Where-Object {$_ -ne 0} | ForEach-Object {[char]$_}) -join ""
    $prod = $_.ProductCodeID
    Write-Output "  $name | Mfr=$mfr | ProductCode=$prod | YearMfr=$($_.YearOfManufacture) | Instance=$($_.InstanceName)"
}

Write-Output "`n=== SUPPORTED MODES (BenQ) ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorListedSupportedSourceModes | Where-Object { $_.InstanceName -match "BNQ" } | ForEach-Object {
    $_.MonitorSourceModes | ForEach-Object {
        Write-Output "  $($_.HorizontalActivePixels)x$($_.VerticalActivePixels) @ $([math]::Round($_.VerticalSyncFreqDivider,0))Hz"
    }
} 2>$null
if (-not $?) { Write-Output "  (Could not query supported modes)" }

Write-Output "`n=== SUPPORTED MODES (EPSON) ==="
Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorListedSupportedSourceModes | Where-Object { $_.InstanceName -match "SEC" } | Select-Object -First 1 | ForEach-Object {
    $_.MonitorSourceModes | ForEach-Object {
        Write-Output "  $($_.HorizontalActivePixels)x$($_.VerticalActivePixels) @ $([math]::Round($_.VerticalSyncFreqDivider,0))Hz"
    }
} 2>$null
if (-not $?) { Write-Output "  (Could not query supported modes)" }

Write-Output "`n=== ACTIVE DISPLAY PATHS (DisplayConfig) ==="
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
    Write-Output "  $($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height) at ($($_.Bounds.X),$($_.Bounds.Y)) Primary=$($_.Primary) WorkArea=$($_.WorkingArea.Width)x$($_.WorkingArea.Height)"
}

Write-Output "`n=== NVIDIA-SMI CONNECTED DISPLAYS ==="
nvidia-smi --query-gpu=name,display_mode,display_active,gpu_bus_id --format=csv,noheader 2>$null
