$base  = 'https://model-deployment-0b50s.paas.ai.telus.com/files'
$token = '8f6ceea09691892cf2d19dc7466669ea'
$dest  = 'C:\Users\user\models\sd-turbo-briony-v5'
$log   = 'C:\Users\user\v5_download.log'

$files = @(
  @{path='model_index.json';                             size_mb=0.001},
  @{path='unet/config.json';                             size_mb=0.002},
  @{path='unet/diffusion_pytorch_model.safetensors';     size_mb=1730},
  @{path='vae/config.json';                              size_mb=0.001},
  @{path='vae/diffusion_pytorch_model.safetensors';      size_mb=160},
  @{path='text_encoder/config.json';                     size_mb=0.001},
  @{path='text_encoder/model.safetensors';               size_mb=650},
  @{path='scheduler/scheduler_config.json';              size_mb=0.001},
  @{path='tokenizer/tokenizer_config.json';              size_mb=0.001},
  @{path='tokenizer/merges.txt';                         size_mb=0.5},
  @{path='tokenizer/special_tokens_map.json';            size_mb=0.001},
  @{path='tokenizer/vocab.json';                         size_mb=1}
)

foreach ($f in $files) {
  $p   = $f.path
  $dir = Split-Path "$dest\$p" -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $out  = "$dest\$p"
  $url  = "$base/sd-turbo-briony-v5/$p`?token=$token"

  # Check if already complete (within 1 MB of expected size)
  if (Test-Path $out) {
    $existing_mb = [math]::Round((Get-Item $out).Length / 1MB, 0)
    if ($existing_mb -ge ($f.size_mb - 1)) {
      Add-Content $log "SKIP $p ($existing_mb MB)"
      continue
    }
    Add-Content $log "RESUME $p (have ${existing_mb} MB, want $($f.size_mb) MB)"
  } else {
    Add-Content $log "START $p"
  }

  # curl with resume (-C -), show progress to log, 5min timeout per chunk
  curl.exe -L -C - --retry 5 --retry-delay 3 --max-time 600 -o $out $url
  $done_mb = [math]::Round((Get-Item $out -ErrorAction SilentlyContinue).Length / 1MB, 1)
  Add-Content $log "DONE $p ($done_mb MB)"
}
Add-Content $log "=== ALL DONE ==="
