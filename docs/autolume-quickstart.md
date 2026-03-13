# Autolume Quickstart — Loading Our Checkpoint

**For Prav** — get the base model checkpoint running in Autolume on your RTX 3060 laptop (Windows).

## 1. Prerequisites

- **NVIDIA GPU with CUDA** (your RTX 3060 is fine)
- **Windows or Linux** (no Mac support yet)

## 2. Install Autolume

Download the prebuilt executable from the MetaCreation Lab — no Python/conda setup needed:

**[metacreation.net/autolume#download](https://metacreation.net/autolume#download)**

Download the zip, extract it, and run the executable.

<details>
<summary>Alternative: Developer install from source</summary>

If the prebuilt doesn't work or you need to modify Autolume:

1. Install [CUDA 12.8](https://developer.nvidia.com/cuda-12-8-0-download-archive), [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), [Miniconda](https://docs.anaconda.com/miniconda/)
2. Clone and install:
```bash
git clone https://github.com/Metacreation-Lab/autolume.git
cd autolume
conda create -n autolume python=3.10
conda activate autolume
pip install -r requirements.txt
```
</details>

## 3. Download Our Checkpoint

Download **network-snapshot-000200.pkl** (347 MB) — the base v1 model (200 kimg on 539 marine photos, TELUS H200):

**[Download 000200.pkl](https://drive.google.com/file/d/1QmmeCt2-P_C-KY1Kss2jSvz1gc6CpQB3/view)**

Copy it into Autolume's `models/` folder:
```bash
copy %USERPROFILE%\Downloads\network-snapshot-000200.pkl models\
```

Earlier smoke test checkpoints (optional — undertrained, mostly useful for comparison):
| File | Size | Notes | Link |
|------|------|-------|------|
| network-snapshot-000025.pkl | 347 MB | 25 kimg smoke test | [Download](https://drive.google.com/file/d/1WOMcUhi3RaML_TjqEilvHZOh8mBNyu7E/view) |
| network-snapshot-000020.pkl | 347 MB | 20 kimg smoke test | [Download](https://drive.google.com/file/d/1tquQsIQCTiplsLDPZRBOXGsT_5qtEfQR/view) |

## 4. Launch

Run the Autolume executable (or `python main.py` if using the dev install). It scans the `models/` directory on startup. Our checkpoint should appear in the model picker UI. If not, use the **"Find"** button to browse to the `.pkl` file.

## 5. What to Expect

This is the **base v1 model** — 200 kimg on 539 marine photos (underwater, nearshore, 37 Salish Sea species). Outputs will look **photographic/marine** — recognizable sea life forms, ocean colors and textures. Not painterly yet — that comes after the Briony fine-tune.

Extended training (kimg=1000) is running now and will produce sharper, more coherent output. Briony fine-tune checkpoints after that will give a **gradient from photographic → painterly**.

The goal right now:
1. **Confirm the PKL loads** without errors — this is the critical compatibility check
2. **Learn the Autolume UI** — latent navigation, truncation PSI, Network Bending
3. **Test NDI output** into TouchDesigner
4. **Be ready** to swap in fine-tuned checkpoints as they land

## 6. Evaluating Training Progress

**Tip from Arshia:** Check the `fakesXXXXXX.png` grid images in the training output folder — they show generated samples at each snapshot and give a clear picture of how training is progressing before you load the pkl. The grids for the base v1 run are on the [shared Drive](https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr) (`fakes000000.png` through `fakes000200.png`).

## ⚠ Potential Compatibility Issue

Our PKL was trained with the **NVlabs StyleGAN3** codebase (`--cfg=stylegan2`). Autolume uses its own **fork of StyleGAN2-ada**. There could be architecture mismatches when loading.

**If it fails to load:** that's a critical finding — means we need to retrain using Autolume's own training pipeline. Better to discover this now than after the full training run. Let Darren know immediately.

## Resources

- [Autolume download](https://metacreation.net/autolume#download) — prebuilt executable
- [Autolume GitHub](https://github.com/Metacreation-Lab/autolume) — source code
- [Autolume docs](https://metacreation-lab.github.io/autolume/)
- [Our training data & pipeline](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/training-data)
- [Full technical architecture](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/autolume-integration.md)
- [SSD Shared Drive](https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr)
