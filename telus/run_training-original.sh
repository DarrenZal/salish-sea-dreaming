#!/bin/bash
set -e

export CC=/opt/conda/bin/x86_64-conda-linux-gnu-gcc
export CXX=/opt/conda/bin/x86_64-conda-linux-gnu-g++
export CUDAHOSTCXX=/opt/conda/bin/x86_64-conda-linux-gnu-g++
export TORCH_CUDA_ARCH_LIST="9.0"

# Set CPATH for all nvidia includes
NVIDIA_INC=$(find /opt/conda/lib/python3.11/site-packages/nvidia -name include -type d 2>/dev/null | tr '\n' ':')
export CPATH="${NVIDIA_INC}${CPATH}"

cd /home/jovyan/stylegan3

# Clear compilation cache
rm -rf ~/.cache/torch_extensions

# Test CUDA compilation first
echo "=== Testing CUDA extension compilation ==="
python -c 'from torch_utils.ops import bias_act; bias_act._init(); print("bias_act OK")'
python -c 'from torch_utils.ops import upfirdn2d; upfirdn2d._init(); print("upfirdn2d OK")'
echo "=== All CUDA extensions compiled ==="

# Start training with Arshia's recommended params
echo "=== Starting training: batch=8, gamma=20, kimg=200, snap=10 ==="
python train.py --outdir=./results --cfg=stylegan2 \
  --data=./data/marine-base512.zip --gpus=1 --batch=8 \
  --gamma=20 --kimg=200 --snap=10

