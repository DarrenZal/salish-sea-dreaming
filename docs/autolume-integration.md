---
doc_id: ssd.autolume-integration
doc_kind: architecture
status: active
depends_on:
  - ssd.project-vision
---

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

## Critical Constraint: macOS Not Supported (Yet)

**Autolume runs on Windows 10/11 and Linux only. Mac version is in development** (confirmed by Arshia, March 2026) but not yet available.

For our setup, this means:
- **Darren's MacBook** cannot run Autolume directly (no macOS build yet)
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
Autolume (Fish Model) ──────► NDI In TOP ──┐
Autolume (Whale Model) ─────► NDI In TOP ──┤──► TouchDesigner Compositor
Autolume (Bird Model) ──────► NDI In TOP ──┘          │
Autolume (320k base) ───────► NDI In TOP ─────────────┤  ("dreaming mind" bg layer)
                                                       ▼
MIDI controller ──────────────────────────────► Boids Particle System
Ableton/Max for Live ── OSC /audio/* ─────────► (instanced with GAN texture)
                                                       │
                                                       ▼
                                            Recursive Instancing / Zoom
                                           (scales → fish → school → whale)
                                                       │
                                                       ▼
                                            Resolume Arena ────→ Projection
```

**Signal flow:**
- **3 Autolume instances → TD**: NDI video streams (one per species model)
- **Background layer**: 320 kimg base checkpoint as abstract "dreaming mind" texture
- **TD boids system**: Particle system with GAN textures, drives all visual movement
- **TD ↔ Autolume**: OSC bidirectional (latent parameters, control signals)
- **Audio → TD**: Ableton/Max for Live sends `/audio/amplitude` and `/audio/freq_band` via OSC
- **MIDI → Autolume**: Direct via Network Bending, or routed through TD
- **TD → Resolume**: Final compositing, projection mapping

### Operational Modes

**Autonomous Installation:** Runs unattended with pre-programmed latent space navigation and audio-reactive parameters. For gallery hours when no performer is present.

**Live Performance:** Prav performing real-time latent space navigation, audio-reactive visuals, MIDI/OSC control. For openings, special events, and scheduled performances.

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

### Three Focused Species Models

### Strategy Update (March 21)

The original plan called for three separate species models mixed via NDI crossfades. This has been revised:

**For April:** The **fish model** (378 images, 13 species, kimg 1000) is the primary live GAN. One model, one Autolume instance, one clear live center. Latent navigation across herring/salmon/rockfish clusters provides the visual vocabulary.

**Stretch track for April:** A **CC-safe multi-species "dreaming model"** — fish + intertidal invertebrates (anemones, starfish, nudibranchs, octopus) in one shared latent space. Curated by visual grammar (underwater/intertidal, organism-dominant, consistent lighting), not taxonomy. This is the north star — a latent space where navigating IS navigating the ecosystem.

**Post-April (MOVE37XR Oct 2026):** Expand the dreaming corpus, train to kimg 2000.

**Why single > separate:** Within one model you get smooth latent interpolation — species morph organically. Between separate models you only get pixel crossfades. The dreaming model IS the project's vision: "each creature contains the whole."

**Note on the 320 kimg base model:** The original base (539 images, 37 species) has a **license problem** — majority CC BY-NC or unlicensed. Cannot be used at the exhibition. R&D only. The concept it proved (multi-species latent space) is sound, but the corpus must be rebuilt CC-safe.

| Model | Dataset | Images | Status |
|-------|---------|--------|--------|
| **Fish** | 13 bony fish species | 378 (QC'd, CC-safe) | **Primary for April.** kimg ~780/1000, ETA March 22. |
| **Dreaming** | Fish + intertidal invertebrates | TBD (~500-800) | Stretch track. Corpus curation starts March 22. |
| **Base (320 kimg)** | Original 539 mixed marine | 539 | R&D only — license-tainted. |
| Bird | 10 seabird species | 1,729 (awaiting QC) | Post-April |
| Whale | 6 cetaceans | 731 (awaiting QC) | Post-April |

**License policy:** CC0/CC BY/CC BY-SA only (artist fee = commercial use). All images scraped with `--license-filter`. Provenance tracked in `training-data/provenance.csv`.

### Individual Fish, Not Schools

School images are excluded from the fish-model corpus — mixing schools into an individual-fish dataset creates a bimodal distribution that StyleGAN struggles with. Schools are created in TouchDesigner via boids + instancing (see Holonic Morphing System below). The GAN provides individual fish appearance; TD provides emergent schooling behavior.

School images (12) and herring eggs (15) are saved separately for potential future corpus training.

### Future Training Seeds

| Corpus | Images | Purpose |
|--------|--------|---------|
| `herring-eggs-raw/` | 15 | Herring spawn/egg imagery — future model |
| `fish-schools-raw/` | 12 | School formations — future fish-school model if TD instancing looks too synthetic |
| `briony-marine-colour/` | 54 | Briony Penn watercolors at 512x512 — fine-tune candidate |

---

## Holonic Morphing System

### Vision: The Food Web as Fractal Cycle

The installation explores the Salish Sea food web through fractal, self-similar transitions. Each creature contains the whole:

- Scales of a fish → become individual fish in a school
- School of herring → condenses into a salmon (herring eaten by salmon)
- School of salmon → becomes a whale (salmon eaten by whale)
- Whale breaks the surface → dissolves into a murmuration of birds
- Bird murmuration dives → becomes a herring ball (birds eating herring)
- Herring ball → individual herring whose scales are fish

Each holon contains the whole. The cycle is the food web.

### How It Works: GAN Language + TD Grammar

The GANs provide the *visual language* (what fish/whales/birds look like). TouchDesigner provides the *grammar* (how they move, flock, morph, and consume each other). Cross-model morphing (fish face structurally transforming into whale face) is NOT achievable across separate GANs. What we CAN do is choreographed sequences that feel intentional and on-theme.

### Boids Particle System (TD)

Three behavioral modes for the particle system, each textured with the corresponding GAN output:

**FISH_SCHOOL mode:**
- High cohesion (0.8), high alignment (0.7), fast speed
- Thin disc formation (fish schools are flat, not spherical)
- Silver flash effect: particles briefly brighten on direction change

**BIRD_MURMURATION mode:**
- Medium cohesion (0.5), altitude variation (y-axis drift)
- Wave-like density pulsation, expansion/contraction in long curving shapes

**SINGLE_ENTITY mode:**
- Particles collapse to single point (count → 1)
- GAN output fills full frame (whale: slow drift, breathing surface animation)

**OSC control parameters:**
```
/boids/cohesion     [0.0-1.0]
/boids/separation   [0.0-1.0]
/boids/alignment    [0.0-1.0]
/boids/count        [1-10000]
/boids/mode         [fish|bird|single]
/boids/speed        [0.0-1.0]
```

**Audio reactivity:**
- Boids speed ← audio amplitude (silent = slow drift, loud = fast school burst)
- Boids cohesion ← frequency band (bass = tight school, treble = dispersed)

### Cross-Model Transitions (The Food Web Cycle)

| Transition | What it looks like | What actually happens |
|---|---|---|
| Herring → Salmon | Color warms, form shifts | Latent walk within fish model (herring → salmon cluster) — **real structural morph** |
| School condenses | Many fish → tight ball | Boids cohesion → 1.0 |
| School → Whale | Ball implodes, large form emerges | Boids count → 1, crossfade fish → whale NDI |
| Whale → Bird flock | Form disperses upward | Boids count scales up, crossfade whale → bird NDI, mode → MURMURATION |
| Birds → Herring ball | Murmuration contracts down | Boids mode → FISH_SCHOOL, crossfade bird → fish NDI |

**The crossfades ARE the consumption.** The disappearance of herring IS the salmon. The collapse of the salmon school IS the whale. Coupled with boids expansion/contraction and the fractal instancing, these read as organic transformations, not dissolves.

**The one true structural morph:** Herring → salmon within the fish model via latent space interpolation. After training, Arshia can identify approximate latent clusters via Autolume's projection feature and interpolate between those seeds. This is the keystone moment of the cycle.

### Recursive Instancing — "Fish Made of Fish"

Render-to-texture recursion in TD:

```
Level 0: GAN individual fish texture (from Autolume NDI)
Level 1: Instance 200 fish textures arranged as a fish silhouette
         → Viewer sees "fish made of fish"
Level 2: Instance 50 Level-1 schools arranged as a whale silhouette
         → Viewer sees "whale made of schools"
```

Controlled by a master `zoom_level` parameter [0.0–2.0] via OSC:
- `zoom=0`: Sea of silver light (impressionistic, deep zoom out)
- `zoom=0.5`: Vast school of fish
- `zoom=1.0`: Individual fish, clearly defined
- `zoom=2.0`: Scales magnified → each is a tiny fish

Implementation: `Render TOP` → `Feedback` loop → `Instance Texture` on SOP point clouds shaped from fish/whale silhouette SDFs.

### Background Layer: The Dreaming Mind

The original 320 kimg base model (37 species, abstract/impressionistic) runs as a persistent background layer at low opacity — the Salish Sea dreaming itself while individual organisms swim through. This provides visual continuity during transitions and grounds the installation in the "dreaming" concept.

### Implementation Phasing (April 10 deadline)

**Must-have for April:**
1. Three species models trained (TELUS) ← fish training started
2. Three Autolume instances running → NDI into TD
3. Basic boids fish school (starting point: `examples/FishSchool.toe`)
4. Choreographed crossfades between NDI feeds + boids expansion/contraction
5. Latent walk within fish model (herring ↔ salmon)
6. Background 320 kimg layer
7. Basic audio reactivity (amplitude → boids speed/cohesion)

**Nice-to-have for April:**
8. Fish → whale boids count transition (school → single point → whale)
9. Boids rule morph: fish school ↔ bird murmuration
10. Level-1 recursive instancing: "fish of fish"

**Post-April (MOVE37XR Symposium, Oct 2026):**
11. Full automated food web cycle choreography
12. Level-2 recursive instancing ("whale of schools of fish")
13. Interactive depth (stillness reveals deeper recursion)

### Hardware for Multi-Instance

Three simultaneous Autolume instances + NDI + TD. Prav's minimum spec to curator: RTX 3090.

**Option A — Single RTX 4090 (test first):** 3 instances at 1080p/30fps feasible; VRAM tight. Validate with burn-in test.

**Option B — Two machines (if A fails):** Split Autolume instances across two GPUs, TD on third machine receiving NDI.

**NDI bandwidth:** 1080p ≈ 100-180 Mbps per feed. 4 feeds ≈ 600 Mbps — gigabit LAN minimum, no Wi-Fi.

---

## TELUS GPU Deployment

### TELUS H200 Notebook Bootstrap

Console: `https://console.ai.telus.com` → Developer Hub → Notebooks → "Jupyter Notebook - 1 H200 GPU"
Jupyter API: `https://salishsea-0b50s.paas.ai.telus.com` (token in `.env`)

Full reproducible setup: **`scripts/telus-training-setup.sh`**. Previous run artifacts saved in **`telus/`** (logs, training_options, stats).

```bash
# Key steps (see telus-training-setup.sh for full script):

# 1. Install PyTorch + deps
pip install torch==2.5.1 torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ninja imageio-ffmpeg==0.4.9 psutil scipy click requests tqdm pyspng

# 2. CUDA toolkit + compilers (system gcc 15.2 too new for CUDA 12.4)
mamba install -y -c nvidia/label/cuda-12.4.0 cuda-nvcc cuda-cudart-dev
conda install -y gcc_linux-64=12 gxx_linux-64=12

# 3. Compiler env vars (CRITICAL — without these, falls back to pure-Python, 1.5x slower)
export CC=/opt/conda/bin/x86_64-conda-linux-gnu-gcc
export CXX=/opt/conda/bin/x86_64-conda-linux-gnu-g++
export CUDAHOSTCXX=$CXX
export TORCH_CUDA_ARCH_LIST="9.0"
NVIDIA_INC=$(find /opt/conda/lib/python3.11/site-packages/nvidia -name include -type d | tr '\n' ':')
export CPATH="${NVIDIA_INC}${CPATH}"

# 4. Test CUDA compilation
python -c 'from torch_utils.ops import bias_act; bias_act._init(); print("OK")'

# 5. Train (proven params: batch=8, gamma=20)
python train.py --outdir=./results --cfg=stylegan2 \
  --data=./data/fish512.zip --gpus=1 --batch=8 --gamma=20 \
  --kimg=1000 --snap=50 --metrics=none
```

**Confirmed speed:** ~353 sec/kimg with compiled CUDA, 100% GPU utilization. 1000 kimg ≈ 4 days.

**TELUS-specific notes:**
- Storage is **ephemeral** — download `.pkl` checkpoints before pod restarts.
- Training survives browser disconnect (confirmed: 10+ hours unattended).
- Pod lifecycle / idle timeout: unknown — download checkpoints regularly.
- GPU: H200, 141 GB HBM3e, Python 3.11.6.
- Full reference: `IndigenomicsAI/docs/telus/telus-friday-questions-2026-03-13.md`

### Completed Training Runs

**Briony test run (2026-03-09):** 25 kimg on 36 Briony watercolor crops (since expanded to 54), StyleGAN2 config, 1× H200 GPU.
- Checkpoints saved locally in `models/briony-test-run/` (not committed — PKLs are ~347 MB each)
- Snapshots: `network-snapshot-000000.pkl`, `000020.pkl`, `000025.pkl`
- FID50k: 474.64 → 556.03 → 502.85 (worsened then partial recovery — expected with 36 images, needs base+fine-tune; ran in pure-Python fallback due to missing C/C++ compiler on TELUS)
- Fakes grids and training logs included
- **To share:** Send PKLs via file transfer (Google Drive, rsync, etc.)

### Training Workflow (Current)

1. **Fish model** (378 images, 13 species) — **training now** on TELUS, kimg=1000, ETA Mar 20-21
2. **Bird model** (1,729 images, 10 species) — next, after fish completes + QC
3. **Whale model** (731 images, 6 species) — last (Arshia: shapes less consistent)
4. **Briony fine-tune** (54 watercolors) — resume from species checkpoint for painterly gradient

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

## Open Questions

**For Prav:**
1. Multi-instance burn-in: can his hardware (RTX 3060 laptop?) run 3 Autolume instances + TD? Need to test before committing to full training pipeline.
2. Boids + instancing approach for fish schools — does he have a starting point in TD, or build from `examples/FishSchool.toe`?
3. Target resolution/fps for NDI output? (assumed 1080p/30fps)

**For Arshia:**
1. After fish model training, can you identify herring vs salmon latent clusters via Autolume's projection feature? This enables the herring→salmon within-model morph.
2. Recommended Autolume NDI output resolution for 3 simultaneous instances on a single RTX 4090?
3. YOLO-based smart cropping for whale dataset — worth doing before training, or try without first? (Arshia says try without first.)

---

## Verification Checklist

- [x] Training dataset decided: 3 species models (fish/bird/whale) at 512x512
- [x] Fish model QC'd (378 images) and training started on TELUS
- [x] Autolume loads PKL checkpoints (Prav confirmed with 320 kimg base)
- [x] NDI stream from Autolume visible in TD (Prav confirmed)
- [ ] Fish checkpoint downloaded + tested in Autolume (ETA Mar 20-21)
- [ ] Bird + whale QC'd, prepped, trained
- [ ] Multi-instance burn-in: 3 Autolume + TD on Prav's hardware
- [ ] Boids fish school prototype in TD
- [ ] Choreographed crossfade between 2+ NDI feeds
- [ ] Audio reactivity: amplitude → boids speed via OSC
- [ ] Herring → salmon latent walk demonstrated

---

## References

- [Autolume GitHub](https://github.com/Metacreation-Lab/autolume)
- [Autolume documentation](https://metacreation-lab.github.io/autolume/)
- [Technical report (MetaCreation Lab)](https://www.metacreation.net/projects/autolume-automating-live-music-visualisation-technical-report/)
- [Autolume-Live thesis (SFU)](https://summit.sfu.ca/item/36414)
