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
- **Prav's machine** (likely Windows) is the natural host for Autolume
- **TELUS GPU cluster** (Linux) is ideal for training
- Alternatively: run Autolume on a Linux VM or Docker container on any machine with NVIDIA GPU access

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

### Current Assets

- `images/marine/` — 128 species × 500px JPEGs from iNaturalist Guide 19640
- Ecologically relevant species already present: Herring, Chinook Salmon, Pink Salmon, Sockeye Salmon, Orca (check manifest)

### StyleGAN2-ada and Small Datasets

StyleGAN2-ada was specifically designed for limited training data. Results are viable with as few as a few hundred images, though 1,000+ images produce better generalization. The "ada" (Adaptive Discriminator Augmentation) makes small-data training tractable.

### Recommended Approach: Five Threads Models

Train separate models per ecological thread — each model becomes a distinct visual "voice" in the installation:

| Thread | Species to include | Semantic feel |
|--------|-------------------|---------------|
| **Herring** | Herring, Anchovy, Sardine, small schooling fish | Silver schools, density, the foundation |
| **Salmon** | Chinook, Sockeye, Pink, Coho | Orange-red, river-bound, return |
| **Orca** | Orca, Dall's Porpoise, Pacific White-sided Dolphin | Black and white, apex, grief |
| **Kelp forest** | Sea stars, anemones, rockfish, urchin | Green-gold, vertical, stillness |
| **Deep / open water** | Cephalopods, deep sea fish, bioluminescent | Darkness, light-point, alien |

Latent interpolation between models = ecological cascade (herring → salmon → orca).

### Expanding the Dataset

The iNaturalist scraper can pull more images. Run at `large` size (1024px) for StyleGAN training:

```bash
python tools/scrape_inaturalist_guide.py --size large --output ./images/marine-1024
```

For salmon specifically, DFO and NOAA have image databases. iNaturalist has Pacific salmon guides with hundreds of observations.

**Target per thread:** 200–500 images at 512px for initial training. 1024px if using H200 for training.

---

## TELUS GPU Deployment

### Training (most valuable TELUS use)

Autolume training is a standard Python process. To run on TELUS:
1. Package as a Docker/Singularity container (TELUS supports both)
2. Submit training job through Carol Anne's TELUS Sovereign AI Factory access
3. StyleGAN2-ada training at 512px resolution: ~2–4 hours on H200 (vs. ~1–3 days on RTX 4090)
4. Output: `.pkl` checkpoint file → bring back locally for inference

### Inference (probably keep local for live performance)

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
