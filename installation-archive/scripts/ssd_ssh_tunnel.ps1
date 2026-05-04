# ssd_ssh_tunnel.ps1 - Persistent reverse SSH tunnel to poly server
# Runs as a Task Scheduler task on logon.
# Creates: poly:2222 -> localhost:22 (3090 SSH)

$LogFile = "C:\Users\user\ssd_ssh_tunnel.log"
$Remote  = "poly@37.27.48.12"
$SSHExe  = "C:\Windows\System32\OpenSSH\ssh.exe"

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LogFile -Value "$ts  $msg"
}

Write-Log "SSH tunnel watchdog started (PID $PID)"

while ($true) {
    Write-Log "Connecting reverse tunnel to $Remote ..."
    & $SSHExe -N -R 2222:localhost:22 `
        -o ServerAliveInterval=30 `
        -o ServerAliveCountMax=3 `
        -o ExitOnForwardFailure=yes `
        -o StrictHostKeyChecking=no `
        -o BatchMode=yes `
        $Remote
    Write-Log "Tunnel exited (code $LASTEXITCODE) - reconnecting in 10s"
    Start-Sleep -Seconds 10
}
