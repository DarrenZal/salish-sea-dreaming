# ssd_notify.ps1 -- Telegram notifier for the Salish Sea Dreaming install.
#
# Dot-source this file to get the Send-SSDAlert function, then call it
# with a severity and message. Pulls the Telegram bot token and chat ID
# from C:\Users\user\.ssd_secrets.ps1 (not in git).
#
# Built-in de-dupe: the same alert key won't re-fire within a configurable
# cooldown window (default 30 min) so a stuck failure doesn't spam the
# operator. Each alert writes its fingerprint to
# C:\Users\user\.ssd_alert_state.json.
#
# Usage:
#     . C:\Users\user\ssd_notify.ps1
#     Send-SSDAlert -Key "resolume_down" -Severity "CRITICAL" -Message "Arena.exe not running"
#
# Secrets file format (C:\Users\user\.ssd_secrets.ps1):
#     $env:TELEGRAM_BOT_TOKEN = "<bot token>"
#     $env:TELEGRAM_CHAT_ID   = "<chat id>"

$script:SSDNotifyStatePath = "C:\Users\user\.ssd_alert_state.json"
$script:SSDNotifyLog       = "C:\Users\user\ssd_notify.log"
$script:SSDNotifySecrets   = "C:\Users\user\.ssd_secrets.ps1"

function Write-SSDNotifyLog {
    param([string]$msg)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $script:SSDNotifyLog -Value "$stamp  $msg" -ErrorAction SilentlyContinue
}

function Get-SSDAlertState {
    if (Test-Path $script:SSDNotifyStatePath) {
        try {
            return Get-Content -Path $script:SSDNotifyStatePath -Raw | ConvertFrom-Json
        } catch {
            Write-SSDNotifyLog "state file unreadable, resetting"
            return @{}
        }
    }
    return @{}
}

function Save-SSDAlertState {
    param($state)
    $state | ConvertTo-Json -Compress | Set-Content -Path $script:SSDNotifyStatePath -Encoding UTF8
}

function Send-SSDAlert {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)] [string]$Key,
        [Parameter(Mandatory=$true)] [ValidateSet('INFO','WARN','CRITICAL')] [string]$Severity,
        [Parameter(Mandatory=$true)] [string]$Message,
        [int]$CooldownMinutes = 30,
        [switch]$Force
    )

    # Load secrets on each call so rotation works without re-sourcing
    if (-not (Test-Path $script:SSDNotifySecrets)) {
        Write-SSDNotifyLog "ERROR: secrets file missing: $script:SSDNotifySecrets"
        return $false
    }
    . $script:SSDNotifySecrets

    $token  = $env:TELEGRAM_BOT_TOKEN
    $chatId = $env:TELEGRAM_CHAT_ID
    if (-not $token -or -not $chatId) {
        Write-SSDNotifyLog "ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set"
        return $false
    }

    # De-dupe check
    $state = Get-SSDAlertState
    $now   = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    $prev  = $null
    if ($state.PSObject.Properties.Name -contains $Key) {
        $prev = $state.$Key
    }

    if (-not $Force -and $prev -and ($now - [int64]$prev.last_sent) -lt ($CooldownMinutes * 60)) {
        $age = $now - [int64]$prev.last_sent
        Write-SSDNotifyLog "SKIP ${Key} (cooldown, ${age}s since last send)"
        return $true
    }

    # Prefix severity marker (ASCII only - Telegram renders reliably either way)
    $prefix = switch ($Severity) {
        'INFO'     { '[i]' }
        'WARN'     { '[!]' }
        'CRITICAL' { '[!!]' }
    }
    $hostname = [System.Net.Dns]::GetHostName()
    $body = "$prefix [$Severity] SSD/$hostname`n$Message"

    $url = "https://api.telegram.org/bot$token/sendMessage"
    try {
        $resp = Invoke-RestMethod -Method Post -Uri $url -Body @{
            chat_id = $chatId
            text    = $body
        } -TimeoutSec 15

        if ($resp.ok) {
            Write-SSDNotifyLog "SENT ${Key} ($Severity): $Message"
            $state | Add-Member -NotePropertyName $Key -NotePropertyValue @{ last_sent = $now; severity = $Severity } -Force
            Save-SSDAlertState -state $state
            return $true
        } else {
            Write-SSDNotifyLog "FAIL ${Key}: Telegram API ok=false"
            return $false
        }
    } catch {
        $errMsg = $_.Exception.Message
        Write-SSDNotifyLog "FAIL ${Key}: $errMsg"
        return $false
    }
}

function Clear-SSDAlert {
    param([Parameter(Mandatory=$true)] [string]$Key)
    $state = Get-SSDAlertState
    if ($state.PSObject.Properties.Name -contains $Key) {
        $state.PSObject.Properties.Remove($Key)
        Save-SSDAlertState -state $state
        Write-SSDNotifyLog "CLEAR ${Key}"
    }
}
