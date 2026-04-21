# ambient_audio.ps1 -- play the gallery ambient-mode audio file on infinite loop.
# Replaces the need for Ableton running in automatic mode: Ableton is heavy,
# has no built-in watchdog, and requires a licensed session. This script is
# lightweight (pure .NET SoundPlayer or MediaPlayer) and can be watchdog'd.
#
# Source audio: Matt - file 2 Mp3.mp3 (the single track Prav had active in
# SSD_ABLETON_V2_PERFORMANCE_3090.als per 2026-04-20 inspection).
#
# Registered as SSD-Ambient-Audio scheduled task, triggered on logon,
# runs as user in interactive session (required for audio output to the
# correct default device).
#
# Writes heartbeat to C:\Users\user\heartbeats\ambient_audio.hb every 30s
# so the meta-watchdog can detect if this script goes zombie.
#
# Status: DRAFT -- not yet deployed. Intended for Wed AM deploy after
# confirming the .NET MediaPlayer approach works with the MP3 on the 3090.

# SingleInstance guard
$myPid = $PID
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessId -ne $myPid -and $_.CommandLine -like "*ambient_audio.ps1*" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

$AudioFile     = "C:\Users\user\Documents\SalishSeaDreaming - Ableton\SSD_ABLETON_V2_PERFORMANCE Project\Samples\Imported\Matt - file 2 Mp3.mp3"
$LogFile       = "C:\Users\user\Desktop\ssd_ambient_audio.log"
$HeartbeatDir  = "C:\Users\user\heartbeats"
$HeartbeatFile = Join-Path $HeartbeatDir "ambient_audio.hb"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg" -ErrorAction SilentlyContinue
}

function Write-Heartbeat {
    try {
        if (-not (Test-Path $HeartbeatDir)) {
            New-Item -ItemType Directory -Path $HeartbeatDir -Force | Out-Null
        }
        Set-Content -Path $HeartbeatFile -Value (Get-Date -Format "o") -ErrorAction SilentlyContinue
    } catch {}
}

Write-Log "ambient_audio started (PID $PID) source=$AudioFile"

if (-not (Test-Path $AudioFile)) {
    Write-Log "FATAL: audio file missing at $AudioFile"
    exit 1
}

# Use Windows.Media.Playback (UWP) via PresentationCore for MP3 support.
# System.Media.SoundPlayer is WAV-only, so we use MediaPlayer instead.
Add-Type -AssemblyName PresentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open([System.Uri]::new($AudioFile))

# Re-trigger play on media end (manual loop)
$mediaEnd = {
    $player.Position = [TimeSpan]::Zero
    $player.Play()
    Write-Log "loop -- media ended, restarting"
}
Register-ObjectEvent -InputObject $player -EventName "MediaEnded" -Action $mediaEnd | Out-Null

# Volume 0-1 (start at 0.8; adjust via Ableton-replacement convention)
$player.Volume = 0.8
$player.Play()
Write-Log "playback started, volume=$($player.Volume)"

# Heartbeat loop + liveness monitor.
while ($true) {
    Write-Heartbeat
    Start-Sleep -Seconds 30

    # Safety check: if MediaPlayer got into a bad state, restart playback.
    if ($player.Source -eq $null) {
        Write-Log "WARN: player.Source is null, re-opening"
        $player.Open([System.Uri]::new($AudioFile))
        $player.Play()
    }
}
