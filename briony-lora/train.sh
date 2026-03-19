#!/bin/bash
# Briony LoRA Training — run from Mac via SSH
# Prerequisites: kohya-env + sd-scripts + requirements installed on Windows
#
# Usage: bash briony-lora/train.sh

set -e

HOST="windows-desktop"
KOHYA_ENV="C:\\Users\\user\\kohya-env\\Scripts"
SD_SCRIPTS="C:\\Users\\user\\sd-scripts"
TRAIN_DIR="C:\\Users\\user\\briony-training"
IMAGE_DIR="${TRAIN_DIR}\\images"
OUTPUT_DIR="${TRAIN_DIR}\\output"
LOG_DIR="${TRAIN_DIR}\\logs"

echo "=== Briony LoRA Training ==="
echo "Checking Windows connectivity..."
ssh -o ConnectTimeout=10 "$HOST" "echo connected" || { echo "ERROR: Cannot reach $HOST"; exit 1; }

echo "Creating output directories..."
ssh "$HOST" "mkdir \"${OUTPUT_DIR}\" 2>nul & mkdir \"${LOG_DIR}\" 2>nul"

echo "Verifying training images..."
# Images are in 10_brionypenn/ subdirectory (kohya repeats format)
COUNT=$(ssh "$HOST" "dir /b \"${IMAGE_DIR}\\10_brionypenn\\*.png\" 2>nul | find /c /v \"\"")
echo "Found $COUNT training images (in 10_brionypenn/)"

echo "Verifying PyTorch CUDA..."
ssh "$HOST" "${KOHYA_ENV}\\python.exe -c \"import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')\"" || { echo "ERROR: PyTorch/CUDA not working"; exit 1; }

echo ""
echo "Starting LoRA training..."
echo "Base model: runwayml/stable-diffusion-v1-5 (will download ~4GB on first run)"
echo "LoRA rank: 16, alpha: 16, lr: 5e-5, steps: 1000"
echo "Saving checkpoints every 200 steps to ${OUTPUT_DIR}"
echo ""

# Train using command-line args (more reliable than TOML config across versions)
ssh "$HOST" "cd ${SD_SCRIPTS} && ${KOHYA_ENV}\\python.exe train_network.py \
  --pretrained_model_name_or_path=\"runwayml/stable-diffusion-v1-5\" \
  --train_data_dir=\"${IMAGE_DIR}\" \
  --output_dir=\"${OUTPUT_DIR}\" \
  --output_name=\"briony_watercolor_v1\" \
  --save_model_as=safetensors \
  --save_every_n_steps=200 \
  --max_train_steps=1000 \
  --resolution=512 \
  --train_batch_size=2 \
  --network_module=networks.lora \
  --network_dim=16 \
  --network_alpha=16 \
  --optimizer_type=AdamW8bit \
  --learning_rate=5e-5 \
  --lr_scheduler=cosine \
  --lr_warmup_steps=50 \
  --mixed_precision=fp16 \
  --gradient_checkpointing \
  --xformers \
  --caption_extension=.txt \
  --enable_bucket \
  --seed=42 \
  --logging_dir=\"${LOG_DIR}\" \
  --log_prefix=briony_v1"

echo ""
echo "=== Training complete ==="
echo "Checkpoints saved to ${OUTPUT_DIR}"
echo "Download best checkpoint:"
echo "  scp ${HOST}:C:/Users/user/briony-training/output/briony_watercolor_v1.safetensors ."
