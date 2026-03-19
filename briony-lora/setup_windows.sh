#!/bin/bash
# Complete Windows setup for Briony LoRA training.
# Run from Mac when Windows desktop is back online.
#
# Usage: bash briony-lora/setup_windows.sh

set -e

HOST="windows-desktop"
KOHYA_ENV="C:\\Users\\user\\kohya-env"
SD_SCRIPTS="C:\\Users\\user\\sd-scripts"

echo "=== Briony LoRA — Windows Setup ==="

# 1. Test connectivity
echo "Testing SSH..."
ssh -o ConnectTimeout=10 "$HOST" "echo connected" || { echo "ERROR: $HOST unreachable"; exit 1; }
echo "Connected!"

# 2. Verify PyTorch
echo ""
echo "Checking PyTorch + CUDA..."
ssh "$HOST" "${KOHYA_ENV}\\Scripts\\python.exe -c \"import torch; print(f'PyTorch {torch.__version__}, CUDA {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')\"" || {
    echo "ERROR: PyTorch not working. Re-install:"
    echo "  ssh $HOST \"${KOHYA_ENV}\\Scripts\\pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121\""
    exit 1
}

# 3. Install sd-scripts requirements (may have been interrupted)
echo ""
echo "Installing sd-scripts requirements (safe to re-run)..."
ssh "$HOST" "cd ${SD_SCRIPTS} && ${KOHYA_ENV}\\Scripts\\pip install -r requirements.txt" 2>&1 | tail -5

# 4. Install xformers
echo ""
echo "Installing xformers..."
ssh "$HOST" "${KOHYA_ENV}\\Scripts\\pip install xformers" 2>&1 | tail -3

# 5. Verify training images exist
echo ""
echo "Checking training data..."
COUNT=$(ssh "$HOST" "dir /b C:\\Users\\user\\briony-training\\images\\*.png 2>nul | find /c /v \"\"")
echo "Training images: $COUNT"
CAPTIONS=$(ssh "$HOST" "dir /b C:\\Users\\user\\briony-training\\images\\*.txt 2>nul | find /c /v \"\"")
echo "Caption files: $CAPTIONS"

if [ "$COUNT" -ne 22 ]; then
    echo "WARNING: Expected 22 images, found $COUNT"
    echo "Re-transferring from Mac..."
    scp -r "$(dirname "$0")"/../briony-lora/*.png "$HOST:C:/Users/user/briony-training/images/" 2>/dev/null || true
    scp -r "$(dirname "$0")"/../briony-lora/*.txt "$HOST:C:/Users/user/briony-training/images/" 2>/dev/null || true
fi

# 6. Transfer evaluation scripts
echo ""
echo "Transferring evaluation scripts..."
ssh "$HOST" "mkdir C:\\Users\\user\\briony-training\\scripts 2>nul" 2>/dev/null || true
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
scp "$SCRIPT_DIR/evaluate_lora.py" "$HOST:C:/Users/user/briony-training/scripts/"
scp "$SCRIPT_DIR/test_img2img.py" "$HOST:C:/Users/user/briony-training/scripts/"

# 7. Quick GPU check
echo ""
echo "GPU status:"
ssh "$HOST" "nvidia-smi --query-gpu=name,memory.free,temperature.gpu --format=csv,noheader"

# 8. Verify sd-scripts can import
echo ""
echo "Verifying sd-scripts..."
ssh "$HOST" "cd ${SD_SCRIPTS} && ${KOHYA_ENV}\\Scripts\\python.exe -c \"import library.train_util; print('sd-scripts OK')\"" 2>&1

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next: Run training with:"
echo "  bash briony-lora/train.sh"
echo ""
echo "Or manually via SSH:"
echo "  ssh $HOST"
echo "  cd C:\\Users\\user\\sd-scripts"
echo "  C:\\Users\\user\\kohya-env\\Scripts\\python.exe train_network.py \\"
echo "    --pretrained_model_name_or_path=runwayml/stable-diffusion-v1-5 \\"
echo "    --train_data_dir=C:\\Users\\user\\briony-training\\images \\"
echo "    --output_dir=C:\\Users\\user\\briony-training\\output \\"
echo "    --output_name=briony_watercolor_v1 \\"
echo "    --save_model_as=safetensors --save_every_n_steps=200 \\"
echo "    --max_train_steps=1000 --resolution=512 --train_batch_size=2 \\"
echo "    --network_module=networks.lora --network_dim=16 --network_alpha=16 \\"
echo "    --optimizer_type=AdamW8bit --learning_rate=5e-5 \\"
echo "    --lr_scheduler=cosine --lr_warmup_steps=50 \\"
echo "    --mixed_precision=fp16 --gradient_checkpointing --xformers \\"
echo "    --caption_extension=.txt --enable_bucket --seed=42"
