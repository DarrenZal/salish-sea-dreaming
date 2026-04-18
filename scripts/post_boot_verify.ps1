# post_boot_verify.ps1
# Runs 60s after logon via Task Scheduler (SSD-Post-Boot-Verify).
# Writes structured checks to C:\Users\user\post_boot_verify.log so we can diagnose
# a post-Windows-Update-reboot failure without waiting for a docent to notice a black wall.
#
# Checks:
#   1. Resolume Arena process alive
#   2. TouchDesigner process alive
#   3. Python processes alive (relay + StreamDiffusion)
#   4. Primary display resolution is 1920x1080 (BenQ doesn't want to stay there)
#   5. Autolume process alive (proxy for NDI source "DESKTOP-37616PR (Autolume Live)")
#
# Exit codes: 0 = all green, 1 = at least one check failed.
# The log is the source of truth; exit code is mostly cosmetic.

$LogPath = "C:\Users\user\post_boot_verify.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Hostname  = [System.Net.Dns]::GetHostName()
$Failures  = @()

function Write-Log {
    param([string]$Line)
    Add-Content -Path $LogPath -Value $Line
}

Write-Log ""
Write-Log "=== $Timestamp | host=$Hostname ==="

# 1. Resolume
$resolume = Get-Process -Name "Arena" -ErrorAction SilentlyContinue
if ($resolume) {
    $pids = ($resolume.Id) -join ","
    Write-Log "[OK]   Resolume: PID $pids"
} else {
    Write-Log "[FAIL] Resolume: process 'Arena' not found"
    $Failures += "Resolume"
}

# 2. TouchDesigner
$td = Get-Process -Name "TouchDesigner" -ErrorAction SilentlyContinue
if ($td) {
    $pids = ($td.Id) -join ","
    Write-Log "[OK]   TouchDesigner: PID $pids"
} else {
    Write-Log "[FAIL] TouchDesigner: process not found"
    $Failures += "TouchDesigner"
}

# 3. Python (relay + StreamDiffusion)
$python = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($python) {
    $count = ($python | Measure-Object).Count
    Write-Log "[OK]   Python: $count process(es) -- expected relay plus 1-2 StreamDiffusion"
} else {
    Write-Log "[FAIL] Python: no processes -- relay plus StreamDiffusion should be running"
    $Failures += "Python"
}

# 4. Primary display resolution
try {
    Add-Type -AssemblyName System.Windows.Forms
    $screens = [System.Windows.Forms.Screen]::AllScreens
    foreach ($s in $screens) {
        $w = $s.Bounds.Width
        $h = $s.Bounds.Height
        if ($s.Primary) { $tag = "PRIMARY" } else { $tag = "SECONDARY" }
        Write-Log "[INFO] Display $tag : ${w}x${h}"
        if ($s.Primary -and ($w -ne 1920 -or $h -ne 1080)) {
            Write-Log "[FAIL] Primary display is ${w}x${h}, expected 1920x1080 (BenQ may have reverted to 4K after update)"
            $Failures += "DisplayRes"
        }
    }
} catch {
    $err = $_.Exception.Message
    Write-Log "[WARN] Display-resolution check errored: $err"
}

# 5. Autolume
$autolume = Get-Process -Name "Autolume" -ErrorAction SilentlyContinue
if (-not $autolume) {
    $autolume = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'autolume' }
}
if ($autolume) {
    Write-Log "[OK]   Autolume: running"
} else {
    Write-Log "[FAIL] Autolume: not detected -- NDI source DESKTOP-37616PR Autolume Live will be missing, walls will be black"
    $Failures += "Autolume"
}

# Summary + Telegram push
if ($Failures.Count -eq 0) {
    Write-Log "[RESULT] ALL GREEN"
    # Optional: suppress notification on clean boot to avoid nightly noise.
    # Uncomment if you want a green boot confirmation each morning:
    # . C:\Users\user\ssd_notify.ps1; Send-SSDAlert -Key post_boot_result -Severity INFO -Message "Post-boot verify: all checks green" -CooldownMinutes 300
    exit 0
} else {
    $failStr = $Failures -join ", "
    Write-Log "[RESULT] FAILED: $failStr"

    # Push Telegram alert on any failure. 30 min cooldown default keeps
    # the alert from spamming if a reboot is retrying quickly.
    try {
        . C:\Users\user\ssd_notify.ps1
        Send-SSDAlert -Key post_boot_failures `
            -Severity CRITICAL `
            -Message "Post-boot verify FAILED after logon: $failStr. Check log at C:\Users\user\post_boot_verify.log"
    } catch {
        $errMsg = $_.Exception.Message
        Write-Log "[WARN] Telegram notifier call errored: $errMsg"
    }

    exit 1
}
