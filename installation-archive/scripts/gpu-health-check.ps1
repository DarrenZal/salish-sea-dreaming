# GPU Health Check - run periodically
$gpu = nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>$null
$ts = tailscale status 2>$null | Select-Object -First 1
Write-Output "GPU: $gpu"
Write-Output "Tailscale: $ts"
Write-Output "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
