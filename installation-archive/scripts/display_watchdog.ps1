# Display Watchdog — restores display config when projectors power on/off
Add-Type -AssemblyName System.Windows.Forms

$configPath = "C:\Users\user\display_config.cfg"
$mmt = "C:\Users\user\MultiMonitorTool\MultiMonitorTool.exe"
$logPath = "C:\Users\user\display_watchdog.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Out-File -Append $logPath -Encoding utf8
}

Log "Display watchdog started"

$lastCount = ([System.Windows.Forms.Screen]::AllScreens).Count
Log "Initial display count: $lastCount"

while ($true) {
    try {
        $currentCount = ([System.Windows.Forms.Screen]::AllScreens).Count
        
        if ($currentCount -ne $lastCount) {
            Log "Display change: $lastCount -> $currentCount displays. Waiting 15s for HDMI settle..."
            Start-Sleep -Seconds 15
            & $mmt /LoadConfig $configPath
            $newCount = ([System.Windows.Forms.Screen]::AllScreens).Count
            Log "Config restored. Now $newCount displays."
        }
        $lastCount = $currentCount
    } catch {
        Log "Error: $_"
    }
    Start-Sleep -Seconds 15
}
