$base = 'https://model-deployment-0b50s.paas.ai.telus.com/files'
$token = '8f6ceea09691892cf2d19dc7466669ea'
$dest = 'C:\Users\user\models\sd-turbo-briony-v5'
$log  = 'C:\Users\user\v5_download.log'

$files = @(
  'model_index.json',
  'unet/config.json',
  'unet/diffusion_pytorch_model.safetensors',
  'vae/config.json',
  'vae/diffusion_pytorch_model.safetensors',
  'text_encoder/config.json',
  'text_encoder/model.safetensors',
  'scheduler/scheduler_config.json',
  'tokenizer/tokenizer_config.json',
  'tokenizer/merges.txt',
  'tokenizer/special_tokens_map.json',
  'tokenizer/vocab.json'
)

foreach ($f in $files) {
  $dir = Split-Path "$dest\$f" -Parent
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $out = "$dest\$f"
  if (Test-Path $out) { Add-Content $log "SKIP $f"; continue }
  Add-Content $log "START $f"
  curl.exe -s -L -o $out "$base/sd-turbo-briony-v5/${f}?token=$token"
  $mb = [math]::Round((Get-Item $out).Length/1MB,1)
  Add-Content $log "DONE $f ($mb MB)"
}
Add-Content $log "ALL DONE"
