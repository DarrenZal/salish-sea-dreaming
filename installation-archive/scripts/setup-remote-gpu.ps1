# Setup script for Pravin's Windows 3090 machine
# Ensures reliable remote GPU access for RAVE pipeline
# Run via: ssh user@100.91.172.10 "powershell -ExecutionPolicy Bypass -File C:\Users\user\setup-remote-gpu.ps1"

Write-Host "=== Setting up reliable remote GPU access ==="

# 1. OpenSSH Server auto-start
Write-Host "`n--- Step 1: OpenSSH Server ---"
$sshd = Get-Service -Name sshd -ErrorAction SilentlyContinue
if ($sshd) {
    Set-Service -Name sshd -StartupType Automatic
    Start-Service sshd -ErrorAction SilentlyContinue
    Write-Host "OpenSSH Server: StartupType=Automatic, Status=$((Get-Service sshd).Status)"
} else {
    Write-Host "WARNING: OpenSSH Server not installed"
}

# 2. Disable sleep/hibernate
Write-Host "`n--- Step 2: Disable sleep/hibernate ---"
powercfg -change -standby-timeout-ac 0
powercfg -change -hibernate-timeout-ac 0
powercfg -change -monitor-timeout-ac 0
Write-Host "Sleep, hibernate, and monitor timeout disabled on AC power"

# 3. Add CUDA tools to system PATH for SSH sessions
Write-Host "`n--- Step 3: PATH for nvidia-smi ---"
$cudaPaths = @(
    "C:\Windows\System32",
    "C:\Program Files\NVIDIA Corporation\NVSMI",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin",
    "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"
)
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
foreach ($p in $cudaPaths) {
    if (Test-Path $p) {
        if ($currentPath -notlike "*$p*") {
            $currentPath = "$currentPath;$p"
            Write-Host "Added to PATH: $p"
        } else {
            Write-Host "Already in PATH: $p"
        }
    }
}
[Environment]::SetEnvironmentVariable("PATH", $currentPath, "Machine")

# 4. Test nvidia-smi
Write-Host "`n--- Step 4: GPU verification ---"
$nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvsmi) {
    nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
} else {
    Write-Host "nvidia-smi not found in PATH"
    # Try direct path
    $directPath = "C:\Windows\System32\nvidia-smi.exe"
    if (Test-Path $directPath) {
        & $directPath --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
        Write-Host "Found at: $directPath"
    }
}

# 5. Tailscale auto-start check
Write-Host "`n--- Step 5: Tailscale ---"
$ts = Get-Service -Name Tailscale -ErrorAction SilentlyContinue
if ($ts) {
    Set-Service -Name Tailscale -StartupType Automatic
    Write-Host "Tailscale: StartupType=Automatic, Status=$($ts.Status)"
} else {
    Write-Host "Tailscale service not found (may use tray app)"
}

# 6. Create a health check script
Write-Host "`n--- Step 6: Creating health check script ---"
$healthScript = @'
# GPU Health Check - run periodically
$gpu = nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>$null
$ts = tailscale status 2>$null | Select-Object -First 1
Write-Output "GPU: $gpu"
Write-Output "Tailscale: $ts"
Write-Output "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
'@
$healthScript | Out-File -FilePath "C:\Users\user\gpu-health-check.ps1" -Encoding UTF8
Write-Host "Health check script created at C:\Users\user\gpu-health-check.ps1"

Write-Host "`n=== Setup complete ==="
Write-Host "Test from Legion: ssh user@100.91.172.10 'nvidia-smi'"
