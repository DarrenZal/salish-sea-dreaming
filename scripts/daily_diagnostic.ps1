# daily_diagnostic.ps1 -- composes + sends a pre-opening health summary.
#
# Runs every morning (via SSD-Daily-Diagnostic scheduled task) 30 min before
# the gallery opens. Delivers to Darren + Prav so they know what state the
# install is in before anyone walks up to the tower.
#
# Delivery: Telegram by default (using the same bot as ssd_notify.ps1).
# Email (Gmail SMTP) is sent additionally if $env:GMAIL_USER and
# $env:GMAIL_APP_PASSWORD are both present in .ssd_secrets.ps1; otherwise
# the email step is skipped silently.
#
# Pulls state from:
#   - health_probe.ps1 (all component checks)
#   - ssd_audio_state.json (mic silence detection)
#   - ssd_notify.log (overnight alerts that fired)
#   - td_relay.log (last snapshot upload, OSC deliveries)
#
# Secrets (C:\Users\user\.ssd_secrets.ps1):
#   $env:TELEGRAM_BOT_TOKEN = "..."     (required)
#   $env:TELEGRAM_CHAT_ID   = "..."     (required)
#   $env:GMAIL_USER         = "..."     (optional, enables email)
#   $env:GMAIL_APP_PASSWORD = "..."     (optional, enables email)
# Recipient list for email: $env:DIAGNOSTIC_RECIPIENTS (comma-separated),
# defaults to zaldarren@gmail.com.

$ErrorActionPreference = 'Continue'
$log = "C:\Users\user\daily_diagnostic.log"

function Write-DiagLog {
    param([string]$msg)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $log -Value "$stamp  $msg" -ErrorAction SilentlyContinue
}

Write-DiagLog "--- daily diagnostic start ---"

# Load secrets for SMTP + notifier (same secrets file across the install)
$secretsPath = "C:\Users\user\.ssd_secrets.ps1"
if (-not (Test-Path $secretsPath)) {
    Write-DiagLog "ERROR: secrets file missing; aborting"
    exit 1
}
. $secretsPath

$telegramToken  = $env:TELEGRAM_BOT_TOKEN
$telegramChatId = $env:TELEGRAM_CHAT_ID
$gmailUser      = $env:GMAIL_USER
$gmailPassword  = $env:GMAIL_APP_PASSWORD
$recipientsRaw  = if ($env:DIAGNOSTIC_RECIPIENTS) { $env:DIAGNOSTIC_RECIPIENTS } else { "zaldarren@gmail.com" }
$recipients     = $recipientsRaw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }

if (-not $telegramToken -or -not $telegramChatId) {
    Write-DiagLog "ERROR: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing in secrets"
    exit 1
}

# ---------------------------------------------------------------------------
# Collect diagnostic data
# ---------------------------------------------------------------------------

function Get-ProcessSummary {
    $procs = @(
        @{ Name='TouchDesigner'; Label='TouchDesigner'; Required=$true }
        @{ Name='Arena';         Label='Resolume Arena'; Required=$true }
        @{ Name='Autolume';      Label='Autolume'; Required=$false }
        @{ Name='Ableton Live 12 Suite'; Label='Ableton Live'; Required=$false }
    )
    $lines = @()
    foreach ($p in $procs) {
        $proc = Get-Process -Name $p.Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($proc) {
            $age = (Get-Date) - $proc.StartTime
            $ageStr = "{0:d}d{1:D2}h{2:D2}m" -f $age.Days, $age.Hours, $age.Minutes
            $mem = [math]::Round($proc.WorkingSet / 1GB, 2)
            $lines += "  [OK]   $($p.Label): PID $($proc.Id), up $ageStr, $mem GB RAM"
        } else {
            $marker = if ($p.Required) { '[FAIL]' } else { '[WARN]' }
            $lines += "  $marker $($p.Label): not running"
        }
    }
    return $lines -join "`r`n"
}

function Get-AudioSummary {
    $statePath = "C:\Users\user\ssd_audio_state.json"
    if (-not (Test-Path $statePath)) {
        return "  [FAIL] Audio monitor has never written state (gallery_audio.py not running?)"
    }
    $ageSec = [int]((Get-Date) - (Get-Item $statePath).LastWriteTime).TotalSeconds
    try {
        $data = Get-Content -Path $statePath -Raw | ConvertFrom-Json
    } catch {
        return "  [FAIL] Audio state file unreadable"
    }
    $vol60 = [math]::Round($data.vol_max_60s, 5)
    $silenceThreshold = 0.002
    $silent = $vol60 -lt $silenceThreshold -and $data.samples_in_window -ge 300
    $monitorAlive = $ageSec -lt 30
    $lines = @(
        "  Monitor last write: ${ageSec}s ago ($(if ($monitorAlive) { 'OK' } else { 'STALE' }))"
        "  vol_max (60s rolling): $vol60 (threshold $silenceThreshold)"
        "  Status: $(if (-not $monitorAlive) { '[FAIL] monitor dead' } elseif ($silent) { '[FAIL] SILENT' } else { '[OK]' })"
    )
    return $lines -join "`r`n"
}

function Get-OvernightAlerts {
    $notifyLog = "C:\Users\user\ssd_notify.log"
    if (-not (Test-Path $notifyLog)) { return "  (no notify log)" }
    $since = (Get-Date).AddHours(-14)  # covers overnight + morning
    $sent = @()
    Get-Content $notifyLog | ForEach-Object {
        if ($_ -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+SENT\s+(\S+)\s+\((\w+)\):\s*(.+)$') {
            $t = [DateTime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null)
            if ($t -gt $since) {
                $sent += "  $($matches[1])  [$($matches[3])]  $($matches[2]): $($matches[4])"
            }
        }
    }
    if ($sent.Count -eq 0) { return "  (none - clean overnight)" }
    return $sent -join "`r`n"
}

function Get-RelaySummary {
    $relayLog = "C:\Users\user\td_relay.log"
    if (-not (Test-Path $relayLog)) { return "  (no relay log)" }
    $lastSnap = $null
    $snapshotsLast10m = 0
    $oscDeliveriesLast24h = @()
    $cutoffSnap = (Get-Date).AddMinutes(-10)
    $cutoffOsc  = (Get-Date).AddHours(-24)
    Get-Content $relayLog -Tail 2000 | ForEach-Object {
        if ($_ -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[INFO\]\s+Snapshot uploaded') {
            $lastSnap = $matches[1]
            $t = [DateTime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null)
            if ($t -gt $cutoffSnap) { $snapshotsLast10m++ }
        }
        if ($_ -match '^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[INFO\]\s+-> OSC seq=(\d+):\s*(.+)$') {
            $t = [DateTime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null)
            if ($t -gt $cutoffOsc) {
                $oscDeliveriesLast24h += "    $($matches[1])  seq=$($matches[2])  $($matches[3])"
            }
        }
    }
    $lines = @(
        "  Last snapshot upload: $(if ($lastSnap) { $lastSnap } else { 'never in recent log' })"
        "  Snapshots in last 10 min: $snapshotsLast10m"
        "  Visitor prompts delivered (last 24h): $($oscDeliveriesLast24h.Count)"
    )
    if ($oscDeliveriesLast24h.Count -gt 0) {
        $lines += "  Recent:"
        $lines += $oscDeliveriesLast24h | Select-Object -Last 5
    }
    return $lines -join "`r`n"
}

function Get-DiskGPUSummary {
    $lines = @()
    $c = Get-PSDrive C -ErrorAction SilentlyContinue
    if ($c) {
        $freeGB = [math]::Round($c.Free / 1GB, 1)
        $usedGB = [math]::Round($c.Used / 1GB, 1)
        $totalGB = $freeGB + $usedGB
        $lines += "  Disk C: $freeGB GB free / $totalGB GB total"
    }
    try {
        $gpu = & nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>&1
        if ($LASTEXITCODE -eq 0 -and $gpu) {
            $parts = $gpu -split ','
            $lines += "  GPU util $($parts[0].Trim())% | VRAM $($parts[2].Trim())/$($parts[3].Trim()) MiB | $($parts[4].Trim())C"
        }
    } catch {}
    return $lines -join "`r`n"
}

function Get-ProbeLastResult {
    $probeLog = "C:\Users\user\health_probe.log"
    if (-not (Test-Path $probeLog)) { return "  (no probe log)" }
    $lines = Get-Content $probeLog -Tail 30
    # Find the most recent probe block
    $lastStart = -1
    for ($i = $lines.Count - 1; $i -ge 0; $i--) {
        if ($lines[$i] -match 'probe start') { $lastStart = $i; break }
    }
    if ($lastStart -lt 0) { return "  (no probe cycles in tail)" }
    return ($lines[$lastStart..($lines.Count - 1)] | ForEach-Object { "  $_" }) -join "`r`n"
}

# ---------------------------------------------------------------------------
# Compose email
# ---------------------------------------------------------------------------

$hostname = [System.Net.Dns]::GetHostName()
$now = Get-Date
$subject = "SSD Daily Diagnostic - " + $now.ToString('yyyy-MM-dd HH:mm') + " - " + $hostname

$sep = "============================================================"
$nl = "`r`n"

$body  = "Salish Sea Dreaming installation - morning diagnostic" + $nl
$body += $hostname + " / " + $now.ToString('yyyy-MM-dd HH:mm:ss zzz') + $nl + $nl
$body += $sep + $nl + "PROCESSES" + $nl + $sep + $nl
$body += (Get-ProcessSummary) + $nl + $nl
$body += $sep + $nl + "AUDIO" + $nl + $sep + $nl
$body += (Get-AudioSummary) + $nl + $nl
$body += $sep + $nl + "RELAY + VISITOR PIPELINE" + $nl + $sep + $nl
$body += (Get-RelaySummary) + $nl + $nl
$body += $sep + $nl + "DISK + GPU" + $nl + $sep + $nl
$body += (Get-DiskGPUSummary) + $nl + $nl
$body += $sep + $nl + "OVERNIGHT ALERTS (last 14h Telegram SENT)" + $nl + $sep + $nl
$body += (Get-OvernightAlerts) + $nl + $nl
$body += $sep + $nl + "LAST HEALTH PROBE CYCLE" + $nl + $sep + $nl
$body += (Get-ProbeLastResult) + $nl + $nl
$body += $sep + $nl
$body += "Generated by scripts/daily_diagnostic.ps1 on SSD/" + $hostname + $nl

Write-DiagLog "composed diagnostic ($($body.Length) chars)"

# ---------------------------------------------------------------------------
# Deliver #1: Telegram (always, assuming creds present)
# ---------------------------------------------------------------------------

# Telegram has a 4096-char per-message cap. Chunk if needed.
$maxChunk = 3900
$chunks = @()
if ($body.Length -le $maxChunk) {
    $chunks = @($body)
} else {
    $i = 0
    while ($i -lt $body.Length) {
        $end = [Math]::Min($i + $maxChunk, $body.Length)
        $chunks += $body.Substring($i, $end - $i)
        $i = $end
    }
}

$tgUrl = "https://api.telegram.org/bot$telegramToken/sendMessage"
$tgSent = 0
foreach ($chunk in $chunks) {
    $prefix = if ($chunks.Count -gt 1) { "[$($tgSent+1)/$($chunks.Count)] " } else { "" }
    $msg = $prefix + $subject + "`n`n" + $chunk
    try {
        $resp = Invoke-RestMethod -Method Post -Uri $tgUrl -Body @{
            chat_id = $telegramChatId
            text    = $msg
        } -TimeoutSec 20
        if ($resp.ok) { $tgSent++ }
    } catch {
        Write-DiagLog "FAIL telegram chunk: $($_.Exception.Message)"
    }
}
Write-DiagLog "Telegram: sent $tgSent/$($chunks.Count) chunks"

# ---------------------------------------------------------------------------
# Deliver #2: Gmail SMTP (optional, skipped silently if creds absent)
# ---------------------------------------------------------------------------

if ($gmailUser -and $gmailPassword) {
    $securePw = ConvertTo-SecureString $gmailPassword -AsPlainText -Force
    $cred     = New-Object System.Management.Automation.PSCredential($gmailUser, $securePw)
    try {
        Send-MailMessage `
            -From $gmailUser `
            -To $recipients `
            -Subject $subject `
            -Body $body `
            -SmtpServer "smtp.gmail.com" `
            -Port 587 `
            -UseSsl `
            -Credential $cred `
            -Encoding ([System.Text.Encoding]::UTF8) `
            -ErrorAction Stop
        Write-DiagLog "SENT diagnostic email to: $($recipients -join ', ')"
    } catch {
        Write-DiagLog "FAIL email send: $($_.Exception.Message)"
    }
} else {
    Write-DiagLog "Gmail creds not configured -- skipping email (Telegram only)"
}

Write-DiagLog "--- daily diagnostic complete ---"
