#!/bin/bash
# TELUS H200 Training Setup — Salish Sea Dreaming
#
# Run this in the TELUS JupyterLab terminal to bootstrap the environment.
# Pod storage is ephemeral — re-run this after every pod restart.
#
# Last validated: 2026-03-13, ~540 sec/kimg at 100% GPU utilization (batch=8, gamma=20)
# Environment: "Jupyter Notebook - 1 H200 GPU" / Minimal, Python 3.11.6
# Previous runs saved in telus/ directory (logs, training_options, stats)

set -e

echo "=== Step 1: Install PyTorch + training dependencies ==="
pip install torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ninja imageio-ffmpeg==0.4.9 psutil scipy click requests tqdm pyspng

echo "=== Step 2: Install CUDA toolkit (nvcc + headers) ==="
mamba install -y -c nvidia/label/cuda-12.4.0 cuda-nvcc cuda-cudart-dev
export CUDA_HOME=$CONDA_PREFIX

echo "=== Step 3: Install conda compilers (system gcc 15.2 too new for CUDA 12.4) ==="
conda install -y gcc_linux-64=12 gxx_linux-64=12

echo "=== Step 4: Set compiler env vars ==="
export CC=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc
export CXX=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++
export CUDAHOSTCXX=$CXX
export CPATH=$CONDA_PREFIX/include:$CPATH

echo "=== Step 5: Clone StyleGAN3 repo ==="
cd /home/jovyan
if [ ! -d "stylegan3" ]; then
    git clone https://github.com/NVlabs/stylegan3.git
fi
cd stylegan3
mkdir -p data results

echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Upload your dataset zip to stylegan3/data/"
echo "     (e.g., fish-model-512.zip, whale-model-512.zip, bird-model-512.zip)"
echo ""
echo "  2. Convert to StyleGAN format:"
echo "     python dataset_tool.py --source=./data/fish-model-512.zip --dest=./data/fish512.zip --resolution=512x512"
echo ""
echo "  3. Test CUDA extension compilation:"
echo "     python -c \"from torch_utils.ops import bias_act; bias_act._init(); print('OK')\""
echo ""
echo "  4. Start training (proven params from run 00012):"
echo "     python train.py --outdir=./results --cfg=stylegan2 \\"
echo "       --data=./data/fish512.zip --gpus=1 --batch=8 --gamma=20 \\"
echo "       --kimg=1000 --snap=50 --metrics=none"
echo ""
echo "  5. To resume from a checkpoint:"
echo "     python train.py --outdir=./results --cfg=stylegan2 \\"
echo "       --data=./data/fish512.zip --gpus=1 --batch=8 --gamma=20 \\"
echo "       --kimg=1000 --snap=50 --metrics=none \\"
echo "       --resume=./results/<run-dir>/network-snapshot-XXXXXX.pkl"
echo ""
echo "  6. Download checkpoints periodically (~540 sec/kimg, 50 kimg ≈ 7.5 hrs):"
echo "     Use JupyterLab file browser or Jupyter REST API"
echo ""
echo "NOTE: --metrics=none skips FID50k evaluation (saves ~30 min per snapshot)."
echo "      Add --metrics=fid50k_full later for quality assessment if needed."
