# gallery_ambient_audio.ps1 — plays the ambient soundtrack on a continuous loop.
#
# Uses .NET's System.Media.SoundPlayer which handles WAV natively with built-in
# looping. Zero external dependencies, runs as a background process.
#
# Registered as Task Scheduler task "SSD-Ambient-Audio" with trigger "At logon".
# Killed by task shutdown or explicit Stop-Process.
#
# To swap to a different ambient file (e.g. once Prav's Ableton export lands),
# edit $AudioFile below and re-run the task.
#
# Logs to ssd_ambient_audio.log on Desktop.

param(
    [string]$AudioFile = "C:\Users\user\Downloads\Salish Dreaming 21 min.wav"
)

$LogFile = "C:\Users\user\Desktop\ssd_ambient_audio.log"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
}

Write-Log "Ambient audio launcher starting (PID $PID), file: $AudioFile"

if (-not (Test-Path $AudioFile)) {
    Write-Log "ERROR: audio file not found — exiting"
    exit 1
}

try {
    $player = New-Object System.Media.SoundPlayer $AudioFile
    $player.Load()
    Write-Log "SoundPlayer loaded — starting PlayLooping()"
    $player.PlayLooping()
} catch {
    Write-Log "ERROR during PlayLooping: $_"
    exit 2
}

# Keep the script alive so the SoundPlayer stays alive. The loop itself runs
# on a background thread inside SoundPlayer — we just need to not exit.
while ($true) {
    Start-Sleep -Seconds 3600
    Write-Log "heartbeat (still looping)"
}
