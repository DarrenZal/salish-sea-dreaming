# Autolume + TELUS GPU + TouchDesigner Integration
*Technical architecture for Salish Sea Dreaming live visual generation*
*Darren Zal — March 2026*

---

## What is Autolume

[Autolume](https://github.com/Metacreation-Lab/autolume) is a no-code generative AI system from SFU's MetaCreation Lab built on StyleGAN2-ada. It was designed specifically for live visual performance: audio-reactive, OSC/MIDI controllable, with NDI video output. The key capabilities:

- Train custom StyleGAN2-ada models on your own image datasets
- Real-time inference with latent space navigation
- OSC: all parameters addressable via Open Sound Control
- MIDI: "Network Bending" maps latent directions to fader controls
- NDI output: streams generated frames to other apps (TouchDesigner, OBS)

This is exactly the tool for turning the marine life imagery into a live generative visual layer.

---

## Critical Constraint: macOS Not Supported

**Autolume runs on Windows 10/11 and Linux only. No macOS support.**

For our setup, this means:
- **Darren's MacBook** cannot run Autolume directly
- **Darren's Linux server** can host Autolume (NVIDIA GPU access needed)
- **Prav's machine** (likely Windows) is the other natural host
- **TELUS GPU cluster** (Linux) is ideal for training

This needs to be confirmed with Prav before any local install attempt.

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11 or Ubuntu 24.04 |
| GPU | NVIDIA RTX 2070+ (RTX 3090/4090 recommended) |
| CUDA | 12.8 (Development + Runtime) |
| Python | 3.10 (via conda) |
| Build tools | Microsoft C++ Build Tools (Windows) |

On the **TELUS H200 GPU cluster**: hardware exceeds all requirements. H200 = 141GB HBM3e, ~2x A100 performance. Training that takes days on a desktop takes hours on H200.

---

## Architecture

```
MIDI controller
      │
      ▼
  Autolume ←──── OSC ────→ TouchDesigner
  (Windows/TELUS)               │
      │ NDI video stream         ▼
      └──────────────────→  LED volume visuals
                            (Nicholas's rig)
```

Two-way flow:
- **Autolume → TD**: NDI video stream (use NDI In TOP in TouchDesigner)
- **TD ↔ Autolume**: OSC bidirectional (latent parameters, control signals)
- **MIDI → Autolume**: Direct via Network Bending, or routed through TD

---

## TouchDesigner Integration

### Step 1: Receive Autolume NDI Video

In the TD network, add an **NDI In TOP**:
```
NDI In TOP
  Source Name: [auto-detect Autolume stream]
  Output: real-time GAN frames
```

This gives TD the generated video as a texture that can be composited, color-graded, or used to drive other parameters.

### Step 2: OSC In CHOP (receive Autolume parameters)

```
OSC In CHOP
  Network Address: 127.0.0.1 (if same machine) or Autolume host IP
  Port: [check Autolume config — default TBD, commonly 7000 or 8000]
  Outputs: latent vector components → map to particle systems, shaders, noise params
```

Connect OSC output channels to TD visual parameters:
- Truncation PSI → particle spread / density
- Latent directions → color temperature, motion speed, organic distortion

### Step 3: OSC Out CHOP (send control from TD to Autolume)

```
OSC Out CHOP
  Network Address: Autolume host
  Port: Autolume input port
```

TD can drive Autolume from:
- Audio analysis (use Audio Spectrum CHOP → map frequency bands to OSC parameters)
- User interaction (mouse, Kinect, etc.)
- Ecological data feeds (salmon run data → latent drift)

### Step 4: MIDI Routing Options

**Option A — Direct to Autolume (simpler, lower latency):**
```
Physical MIDI controller → Autolume Network Bending
```
Autolume maps MIDI faders directly to latent PCA directions (semantic image manipulation: rotation, zoom, morphing between learned concepts).

**Option B — MIDI → TD → OSC → Autolume (more flexibility):**
```
Physical MIDI controller → MIDI In DAT (TD) → OSC Out CHOP → Autolume
```
TD becomes the hub: MIDI controls both TD visuals and Autolume parameters simultaneously. If Max for Live is already in the signal chain, it can serve as the OSC bridge instead.

**Recommendation:** Option A for Autolume-specific parameters, Option B (or Max for Live) for unified control across TD + Autolume.

---

## Training Dataset Strategy

### Core Insight: One Strong Image Grammar

StyleGAN2-ada doesn't need all-one-species or all-one-composition, but it **does** need visual coherence. At ~500 images, optimize for a shared visual world, not semantic completeness.

Ecological data doesn't tell one GAN what to draw. Instead, data drives:
- Which model/checkpoint is active (underwater vs. painterly)
- Where you navigate in latent space (sparse → abundant)
- How outputs blend in TouchDesigner (layer opacity, compositing)

Multiple models = multiple visual voices. Ecological data = the conductor.

### v1 Strategy: Base + Fine-tune

**For April: one base + one Briony fine-tune is the minimum viable path.**

| Model | Dataset | Size | Training Time (H200) |
|-------|---------|------|---------------------|
| `base-underwater-v1.pkl` | `marine-photo-base/` (500+ underwater/nearshore photos) | 512x512 | ~2-4 hrs |
| `briony-v1.pkl` | Fine-tune on `briony-marine-colour/` (36 images) | 512x512 | ~30-60 min |
| `david-v1.pkl` | Fine-tune on `david-denning/` (if archive arrives) | 512x512 | ~30-60 min |

Save multiple fine-tune checkpoints at `--snap=10` to get a gradient from photographic → painterly.

### Current Assets

- `training-data/briony-marine-colour/` — 36 images at 512x512 (committed, ready)
- `images/marine/` — 128 species × 500px JPEGs from iNaturalist Guide 19640
- Curated species list: `tools/salish-sea-species.tsv` (~38 underwater/nearshore taxa)

### v1 Base Model Scope: Underwater/Nearshore

Fish (single and schools), kelp, eelgrass, octopus, invertebrates, close underwater scenes — these share lighting, color palette, and spatial grammar.

**NOT in v1 base:** Boats, seabirds on open water, horizon-heavy ocean scenes, aerial coastlines, harbor infrastructure. These are visually different domains → separate models in v2.

### Building the Base Dataset

```bash
# Scrape ~570 research-grade photos with provenance tracking
python tools/scrape_inaturalist_guide.py \
  --species-list tools/salish-sea-species.tsv \
  --per-taxon 15 --size large \
  --output ./images/marine-base-raw \
  --provenance

# After QC review, process approved images
python scripts/prep_training_data.py --resolution 512
```

Target: ~38 taxa × 15 = ~570 raw. After QC → 400-500 usable. If below 500, increase `--per-taxon` to 20.

### Future Models (v2+)

| Visual Domain | Description |
|--------------|-------------|
| `surface-horizon` | Whales breaching, seabirds on water, ocean surface |
| `boats-vessels` | Fishing boats, ferries, canoes (Prav's request) |
| `aerial-coastal` | Coastline, estuaries, spawn events from above |
| `forage-school` | Dedicated herring/anchovy schooling model (artistically powerful) |

---

## TELUS GPU Deployment

### TELUS H200 Notebook Bootstrap

Console: `https://console.ai.telus.com` → Developer Hub → Notebooks → "Jupyter Notebook - 1 H200 GPU"
Account: `zaldarren@gmail.com` (Org Admin). Deploy takes ~90 sec.

```bash
# 1. Install dependencies
pip install torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ninja imageio-ffmpeg==0.4.9 psutil scipy click requests tqdm pyspng

# 2. Clone StyleGAN3 codebase (trains both SG2 and SG3 configs)
git clone https://github.com/NVlabs/stylegan3.git
cd stylegan3

# 3. Upload training data zip via JupyterLab file browser
#    Local: zip -j briony-marine-colour.zip training-data/briony-marine-colour/*.png
unzip briony-marine-colour.zip -d ./data/briony/

# 4. Prepare dataset (creates ZIP with metadata for StyleGAN)
python dataset_tool.py --source=./data/briony/ --dest=./data/briony512.zip --resolution=512x512

# 5. Verify
python dataset_tool.py --source=./data/briony512.zip

# 6. Train (smoke test: 200 kimg, ~36 images — will be bad but proves pipeline)
python train.py --outdir=./results \
  --cfg=stylegan2 \
  --data=./data/briony512.zip \
  --gpus=1 --batch=16 --gamma=6.6 \
  --kimg=200 --snap=25

# 7. Full base training (500+ images)
python train.py --outdir=./results \
  --cfg=stylegan2 \
  --data=./data/marine-base512.zip \
  --gpus=1 --batch=32 --gamma=6.6 \
  --kimg=2000 --snap=50

# 8. Fine-tune Briony on top of base
python train.py --outdir=./results \
  --cfg=stylegan2 \
  --data=./data/briony512.zip \
  --gpus=1 --batch=16 --gamma=6.6 \
  --kimg=200 --snap=10 \
  --resume=./results/BASE_CHECKPOINT.pkl
```

**TELUS-specific notes:**
- Storage is **ephemeral** — download `.pkl` checkpoints immediately. A K8s restart wipes everything.
- Keep notebook session open during training (no background jobs on POC).
- One GPU workload at a time.
- GPU: H200, 141 GB HBM3e, CUDA 13.0, Python 3.11.6, ~7.8 TB disk.
- Full reference: `IndigenomicsAI/docs/telus/gpu-access.md`

**Fallback:** If TELUS has CUDA version issues, use RunPod A100 ($2/hr) or Arshia's Compute Canada 4x H100.

### Completed Training Runs

**Briony test run (2026-03-09):** 25 kimg on 36 Briony watercolor crops, StyleGAN2 config, 1× H200 GPU.
- Checkpoints saved locally in `models/briony-test-run/` (not committed — PKLs are ~347 MB each)
- Snapshots: `network-snapshot-000000.pkl`, `000020.pkl`, `000025.pkl`
- FID50k: 388.05 → 340.77 (improving but needs more kimg or base+fine-tune approach)
- Fakes grids and training logs included
- **To share:** Send PKLs via file transfer (Google Drive, rsync, etc.)

### Training workflow

1. **Base model:** Train on `marine-photo-base/` (539 approved) → `base-underwater-v1.pkl` (2-4 hrs on H200)
2. **Fine-tune Briony:** Resume from base, train on `briony-marine-colour/` (36 images) → `briony-v1.pkl` (30-60 min, save multiple checkpoints for photographic→painterly gradient)
3. **Fine-tune David:** If his archive arrives → `david-v1.pkl`

### Inference (keep local for live performance)

For real-time performance, **local inference is preferable**. Network round-trips to TELUS would introduce latency. The workflow:
- Train on TELUS → export checkpoint
- Run inference locally on Prav's Windows machine (RTX card)
- TD connects to local Autolume via OSC/NDI

**Exception:** If Nicholas's LED volume infrastructure includes its own GPU rack with network access, inference could run on-site GPU hardware with local LAN latency (acceptable).

---

## OSC Port Discovery

Exact OSC address paths and default ports are not fully documented publicly. When Autolume is running, probe it:

In TouchDesigner, add an **OSC In CHOP** with port 7000, then 8000, then 9000 — observe which receives messages. Alternatively, check `autolume/config.py` or `autolume/osc.py` in the source for defaults.

---

## Open Questions for Prav

1. **Which Autolume?** MetaCreation Lab's GitHub repo, or another tool?
2. **His hardware:** Is he on Windows? Does he have an NVIDIA GPU?
3. **TELUS access path:** Is Carol Anne the contact, or does Prav have direct credentials?
4. **TELUS purpose:** Training new models, or running live inference remotely?
5. **MIDI controller:** Which one? Is Max for Live already in the chain?
6. **Output target:** Nicholas's LED volume, or smaller-scale Salt Spring Art Show rig?
7. **Timeline:** Does he want something testable before Herring Fest (March 6–8)?

---

## Verification Checklist

- [ ] Confirm Prav's OS + GPU hardware
- [ ] Autolume running on a test dataset (pre-trained checkpoint)
- [ ] OSC messages from Autolume visible in TD's OSC In CHOP
- [ ] NDI stream from Autolume visible in TD's NDI In TOP
- [ ] MIDI controller changing a latent parameter in real time
- [ ] Training dataset decided (species, threads, resolution, count)
- [ ] TELUS access path confirmed (Carol Anne or direct)

---

## References

- [Autolume GitHub](https://github.com/Metacreation-Lab/autolume)
- [Autolume documentation](https://metacreation-lab.github.io/autolume/)
- [Technical report (MetaCreation Lab)](https://www.metacreation.net/projects/autolume-automating-live-music-visualisation-technical-report/)
- [Autolume-Live thesis (SFU)](https://summit.sfu.ca/item/36414)
