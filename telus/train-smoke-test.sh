#!/bin/bash
set -e

echo "=== Salish Sea Dreaming — StyleGAN2 Smoke Test ==="
echo ""

# Step 1: Install dependencies
echo "--- Step 1: Installing dependencies ---"
pip install torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124 2>&1 | tail -5
pip install ninja imageio-ffmpeg==0.4.9 psutil scipy click requests tqdm pyspng 2>&1 | tail -5
echo ""

# Step 2: Check GPU
echo "--- Step 2: GPU Check ---"
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
"
echo ""

# Step 3: Clone StyleGAN3
echo "--- Step 3: Cloning StyleGAN3 ---"
if [ -d "stylegan3" ]; then
    echo "stylegan3 already cloned"
else
    git clone https://github.com/NVlabs/stylegan3.git
fi
cd stylegan3
mkdir -p data
echo ""

# Step 4: Prepare dataset
echo "--- Step 4: Preparing dataset ---"
python3 dataset_tool.py --source=~/data/briony/ --dest=./data/briony512.zip --resolution=512x512
echo ""

# Step 5: Verify dataset
echo "--- Step 5: Verifying dataset ---"
python3 dataset_tool.py --source=./data/briony512.zip
echo ""

# Step 6: Train!
echo "--- Step 6: Training (smoke test — 200 kimg) ---"
echo "This should take ~10-20 min on H200..."
python3 train.py --outdir=./results \
  --cfg=stylegan2 \
  --data=./data/briony512.zip \
  --gpus=1 --batch=16 --gamma=6.6 \
  --kimg=200 --snap=25

echo ""
echo "=== DONE ==="
echo "Checkpoints are in stylegan3/results/"
echo "Download .pkl files NOW — TELUS storage is ephemeral!"
ls -lh results/*/network-snapshot-*.pkl 2>/dev/null || echo "No checkpoints found — check results/ manually"

