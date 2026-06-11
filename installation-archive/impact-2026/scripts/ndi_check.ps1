$ErrorActionPreference = 'SilentlyContinue'

Write-Host "=== NDI-related services / processes ==="
Get-Process | Where-Object { $_.ProcessName -match 'NDI|ndi' } | Select-Object ProcessName, Id | Format-Table

Write-Host ""
Write-Host "=== UDP ports in use (NDI uses 5353 mDNS + 5960+ dynamic) ==="
netstat -ano -p UDP | findstr "5353"

Write-Host ""
Write-Host "=== NDI sender ports that are listening on 3090 (TCP NDI is 5960+) ==="
netstat -ano -p TCP | findstr "LISTENING" | Select-String "5960|5961|5962|5963|5964|5965|5966|5970|5971|5972|5973|5974|5975"

Write-Host ""
Write-Host "=== Is there an NDI Tools / Studio Monitor that can list sources? ==="
$tools = @(
  "C:\Program Files\NDI\NDI 5 Tools\Studio Monitor\Application Files",
  "C:\Program Files\NDI\NDI 6 Tools\Studio Monitor\Application Files",
  "C:\Program Files\NewTek\NDI 5 SDK\Bin\x64",
  "C:\Program Files\NewTek\NDI 6 SDK\Bin\x64"
)
foreach ($t in $tools) {
  if (Test-Path $t) { Write-Host "  FOUND: $t" }
}

Write-Host ""
Write-Host "=== Is NDI Access Manager running? (controls who can see streams) ==="
Get-Process | Where-Object { $_.ProcessName -match 'NDIAccessManager|NDI Access' } | Select-Object ProcessName, Id

Write-Host ""
Write-Host "=== mDNS/Bonjour service (NDI discovery) ==="
Get-Service mDNSResponder, "Bonjour Service" -ErrorAction SilentlyContinue | Select-Object Name, Status
