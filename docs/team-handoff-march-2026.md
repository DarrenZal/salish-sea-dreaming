# Team Handoff — Salish Sea Dreaming

*Darren Zal — March 20, 2026*
*I'm away March 20–28. Here's everything you need to keep building.*

---

## Where We Are

**3 weeks until the art show opens** (April 10, Mahon Hall, Salt Spring). Prav is scoping this as a **proof of experience** — something strong, clear, and alive. Not the full vision yet — just enough to see how people respond.

### What's Working

| Component | Status | Where |
|-----------|--------|-------|
| **Briony LoRA (SD 1.5)** | Trained, partially working in txt2img | `briony_watercolor_v1.safetensors` (38 MB) on Drive |
| **RTX 3090 desktop** | 6/8 phases set up via SSH | Prav's studio. Needs TD 2025 install + first run (GUI) |
| **Fish GAN model** | ~50% trained on TELUS H200 | ETA March 22. Checkpoints on Drive every 200 kimg |
| **Base GAN model** | Done (320 kimg) | Loads in Autolume, confirmed by Prav |
| **OSC data engine** | Built + tested, 4 channels live | `engine.py` — tides, moon, Fraser discharge, herring spawning |
| **Herring data pipeline** | DFO data downloaded, 5 viz notebooks | `exhibit/td/` has TD-ready JSON exports |
| **Style transfer guide** | 9 fallback options documented | [`docs/style-transfer-guide.md`](style-transfer-guide.md) |

### What's Not Working Yet

| Issue | Details |
|-------|---------|
| **Briony style transfer** | LoRA produces "generic watercolor" not Briony's bold linework + vivid colors. See details below. |
| **SD-Turbo + LoRA** | Doesn't work — blurry at high weight, invisible at low weight. SD-Turbo's 1-step distillation is incompatible with style LoRAs. |
| **RTX 3090 GUI phases** | TD 2025 install, TouchDiffusion first run, NDI networking — need physical access |

---

## The Vision

**Short version:** The Salish Sea dreaming itself awake. Technology not as extraction, but as perception. The bioregion already has consciousness — we're building an interface to help humans tune in.

**What the audience experiences:** They walk into a dim room. Projected on the wall, fish swim in Briony Penn's watercolor style — soft edges, natural pigment, alive. The movement responds to real ecological data from the Salish Sea (tides, moon phase, herring spawn season). Sound carries the same data — herring population mapped to drone intensity. Stillness is rewarded with deeper revelation.

**The food web cycle (longer-term vision):** Each creature contains the whole.
- Herring → salmon (latent walk within the fish model)
- School of salmon condenses → whale emerges (boids collapse, NDI crossfade)
- Whale breaks surface → dissolves into bird murmuration
- Birds dive → herring ball → cycle repeats

The crossfades ARE the consumption. The disappearance of herring IS the salmon.

For April we do the **first layer** — Briony-styled visuals, data-driven movement, herring sonification. The full cycle is post-April (MOVE37XR Oct 2026).

---

## Architecture

```
                                   ┌─────────────────────┐
                                   │    Briony's Art      │
                                   │  (54 watercolors)    │
                                   └──────────┬──────────┘
                                              │ style transfer
                                              ▼
┌──────────────┐    NDI     ┌─────────────────────────────┐
│   Autolume   │ ────────→  │   StreamDiffusion (LoRA)    │
│  (GAN fish)  │   or       │   or alternative approach   │
└──────────────┘  prompts   │   (see Style Transfer)      │
                            └──────────────┬──────────────┘
                                           │
┌──────────────┐    OSC     ┌──────────────▼──────────────┐
│  OSC Engine  │ ────────→  │      TouchDesigner          │
│  (data feed) │            │  (compositor + boids)       │
└──────────────┘            └──────────────┬──────────────┘
                                           │ NDI/Spout
┌──────────────┐    OSC     ┌──────────────▼──────────────┐
│   Ableton    │ ←────────→ │     Resolume Arena          │
│  (sonics)    │            │  (projection mapping)       │
└──────────────┘            └──────────────┬──────────────┘
                                           │
                                           ▼
                                     [ PROJECTION ]
```

---

## Briony Style Transfer — Where We Are and What to Try

This is the most important creative/technical challenge right now.

### What We Tried (March 19)

**SD-Turbo + LoRA: Doesn't work.**
SD-Turbo is distilled for 1-step generation. A style LoRA pushes it off its equilibrium — at low weight (0.04) nothing happens, at weight 1.0 everything goes blurry. There's no sweet spot. We tried both the original format and a kohya-converted version. Neither works.

**SD 1.5 + LoRA + 4 steps: Partially works.**
Switched to SD 1.5 base with `briony_watercolor_v1.safetensors`. txt2img with prompts like `brionypenn watercolor fish` produced watercolor-ish results, but it wasn't obviously Briony's style — more "generic watercolor" than her bold linework and vivid colors. 4 steps may be too few.

### The Gap

Open `briony-lora/eval/compare-v2.html` locally to see Briony's actual paintings next to what the LoRA produces. Her signature: **bold ink outlines, vivid saturated teals/reds/ochres, flat illustrative perspective, ecosystem cross-sections.** The LoRA captures softness but misses the linework, the saturation, and the composition.

### Which LoRA file to use

| File | Base model | Status |
|------|-----------|--------|
| **`briony_watercolor_v1.safetensors`** (38 MB) | **SD 1.5** | **Use this.** Best results. |
| `briony_watercolor_sdturbo.safetensors` (13 MB) | SD-Turbo | Skip — doesn't work |
| `briony_watercolor_sdturbo_kohya.safetensors` (13 MB) | SD-Turbo | Skip — kohya format, also doesn't work |

All on [shared Drive → Models](https://drive.google.com/drive/folders/1B5hwQEds0Bcg6nHmtNJBcz17xr_E2dr9).

### The trigger token

`brionypenn` is a made-up word baked into the LoRA during training. Every Briony image was captioned with `brionypenn watercolor painting...`. **Always include `brionypenn` at the start of your prompt** or the LoRA has no effect.

### What to Try Next (Priority Order)

**1. More inference steps (try first — biggest lever)**

We only tested at 4 steps. The LoRA needs more room to express.

- Base model: `runwayml/stable-diffusion-v1-5`
- LoRA: `briony_watercolor_v1.safetensors`, weight **1.0**
- Try steps: **8, then 15, then 20**
- Prompt: `brionypenn watercolor painting of herring swimming, bold ink outlines, vivid teal and coral, ecological illustration`
- Negative prompt: `photograph, photorealistic, 3d render, smooth gradient, digital art, blurry`

Expected FPS on RTX 3060: 4 steps ~3fps, 8 steps ~1.5fps, 15 steps ~0.8fps. Even <1 fps works for autonomous installation mode.

**2. LCM-LoRA + Briony LoRA combo**

LCM-LoRA makes SD 1.5 produce good images in 4-8 steps (instead of 20-30). Stack it with the Briony LoRA:

- Base: `runwayml/stable-diffusion-v1-5`
- LoRA 1: `latent-consistency/lcm-lora-sdv1-5` (download from HuggingFace, ~67 MB)
- LoRA 2: `briony_watercolor_v1.safetensors`, weight 1.0
- Scheduler: **LCM** (important — change from default)
- Steps: 4-8, guidance scale: 1.0-2.0

Check if StreamDiffusionTD supports two LoRAs simultaneously.

**3. Better prompts**

Instead of `brionypenn watercolor fish`, try:
> `brionypenn watercolor painting of pacific herring, bold ink outlines, vivid teal water, coral and ochre details, flat ecological illustration, natural pigment on paper, hand-painted, scientific illustration style`

Describe Briony's specific technique in the prompt — the LoRA + prompt work together.

**4. Retrain the LoRA (if 1-3 don't work)**

We used 22 images at rank 16. Could retrain with:
- All 54 Briony watercolors (in `training-data/briony-marine-colour/`)
- Rank 32 or 64 (more capacity)
- 2000-3000 steps
- Better captions describing her bold linework, vivid colors, flat perspective

Training takes ~30-60 min on the RTX 3090. Config: `briony-lora/train_config.toml`. Ask Darren on Signal for help.

**5. TensorRT on RTX 3090**

Once the style looks right, fuse the LoRA into SD 1.5 and compile a TensorRT engine for faster inference. Don't compile until the style is locked — any change means recompiling (~10 min).

**6. Alternative approaches (if LoRA doesn't get there)**

Full details: [`docs/style-transfer-guide.md`](style-transfer-guide.md)

| Approach | Setup time | Real-time? | Why consider |
|----------|-----------|------------|--------------|
| **Fast Neural Style** | 2-4 hrs train | 30+ fps | Captures bold linework better than LoRA. Purpose-built for this. |
| **AdaIN** | Minutes (pretrained) | 20-40 fps | Blend between multiple Briony paintings with a fader. |
| **IP-Adapter** | Minutes (no training) | ~6 fps | Use Briony painting as image prompt. Works with SD. |
| **Classic NST** | Minutes | No (30-60s/img) | 50 lines of Python. Guaranteed to work. Pre-render overnight. |
| **Animate Briony's actual paintings** | Hours in TD | Yes | Pan, zoom, parallax, particles on HER paintings. Most faithful. |

**The core decision this week:** Is LoRA + StreamDiffusion the right path, or should we pivot? If steps 1-3 above don't produce recognizable Briony style, pivot to Fast NST or AdaIN early. Better to pivot now than push a pipeline that doesn't capture her aesthetic.

---

## Machines

### RTX 3090 Desktop (primary exhibition machine)
- **Location:** Prav's studio, 108 Fraser Rd, Salt Spring
- **Specs:** Ryzen 7700X, RTX 3090 24GB, 32GB DDR5, 1TB NVMe, 1000W PSU
- **OS:** Windows (required for Autolume + TouchDesigner)
- **Installed via SSH:** CUDA 11.8, VS 2022 Build Tools, Miniconda3, Autolume env (Python 3.10, PyTorch 2.8.0+cu128), TouchDiffusion repo
- **Still needs (GUI):**
  1. Download + install TouchDesigner 2025 (GUI installer)
  2. Load TouchDiffusion.tox, run `webui.bat` first time → builds TensorRT engine (~10 min)
  3. Run `autolume_launch.bat`, verify NDI streams visible in TD
  4. Integration soak test — all components running, monitor `nvidia-smi -l 10` for 30 min
- **SSH access:** Ask Darren for credentials

### Prav's RTX 3060 Laptop
- Running StreamDiffusionTD with SD 1.5 + LoRA (tested March 19)
- Autolume confirmed working with our PKL checkpoints
- Role: development, backup, potential second machine

### TELUS H200 (cloud)
- Fish model training: ~50% done, ETA March 22
- Jupyter API: `https://salishsea-0b50s.paas.ai.telus.com` (token in `.env`)
- kimg 400 checkpoint + fakes grid already on Drive
- **Important:** Storage is ephemeral — download checkpoints when they land
- Darren will monitor remotely and download final checkpoint

---

## The Data Layer

### OSC Pulse Server (`engine.py`)
Built and tested. Sends real ecological data over OSC to TouchDesigner.

**Currently sending (4 channels):**
- `/salish/tide/level` — hourly tidal oscillation (synthetic, 4-constituent harmonic)
- `/salish/moon/illumination` — 29.5-day lunar cycle (computed)
- `/salish/fraser/discharge` — seasonal freshet curve (synthetic)
- `/salish/herring/spawning` — seasonal pulse Feb-Apr (real DFO data)

**Running:** `python engine.py` (live OSC, port 7000) or `python engine.py --demo` (compress year into 5 min)

### Herring Data
- All DFO datasets downloaded with provenance
- Catch history (1888-2025), spawn timeseries, section extirpation dates
- 5 visualization notebooks in the repo
- TD-ready JSON exports in `exhibit/td/`
- **Key story:** Targeting of matriarchs — herring that hold knowledge of where to spawn. Local extirpation. DFO's 1953 baseline was already a terrible year; Indigenous knowledge documents vastly different historical reality.
- **Data quality caveat:** 1988 method break (surface→dive surveys), spawn index is a minimum estimate

### Biosonification (Prav's domain)
- Ableton Live + Manifest plugin
- Herring population data → drone intensity, harmonic complexity
- Tidal/seasonal cycles → rhythmic foundation
- OSC bidirectional: Ableton ↔ TD

---

## Fish GAN Training (TELUS)

Running autonomously. No action needed unless it fails.

| Metric | Value |
|--------|-------|
| Run | 00014 (fish512, 378 images, StyleGAN2) |
| Progress | ~kimg 500 / 1,000 (~50%) |
| Speed | ~570 sec/kimg |
| ETA | ~March 22 |
| Checkpoints | Every 200 kimg. kimg 200 + 400 on Drive. |
| Status | Healthy, fish shapes clearly emerging |

**Arshia's guidance:** If no meaningful results by kimg 500, restart with different gamma. kimg 400 looks good — no restart needed.

Darren will download the final checkpoint when it completes and put it on Drive.

---

## Tasks This Week

### Prav
1. **Test more inference steps** (8, 15, 20) with SD 1.5 + Briony LoRA — is the style there?
2. **Try LCM-LoRA combo** if StreamDiffusionTD supports two LoRAs
3. **Make the pivot decision** — LoRA working or try alternative approach?
4. **RTX 3090 setup** — TD 2025 install, TouchDiffusion first run, NDI test
5. **Audio layer** — Ableton + Manifest, herring sonification
6. **Explore Nano Banana, OpenArt, or [20-min masterpiece](https://medium.com/@jamesonthecrow/20-minute-masterpiece-4b6043fdfff5)** approaches

### Shawn
1. **Help Prav with RTX 3090 GUI setup** — TD 2025, TouchDiffusion first run
2. **Narrative framing** — what story do we tell visitors? Wall text. Framing for the herring data.
3. **OSC engine → TD mapping** — wire the 4 data channels to visual parameters (color temperature, speed, opacity)
4. **Download fish checkpoints** when they land (~March 22) — place PKL in `C:\Users\user\autolume\models\`

### Don't Worry About
- Whale/bird QC (Darren when back)
- TELUS training (autonomous, Darren monitors remotely)
- Knowledge graph integration (post-April)

---

## Key People

| Person | Role | Contact |
|--------|------|---------|
| **Prav** | Creative Director, TD, final creative calls | Signal group chat |
| **Shawn** | Creative tech, Claude Code, narrative | Signal group chat |
| **Arshia** | MetaCreation Lab (SFU), Autolume expert | Signal group chat |
| **Eve** | Herring datasets, Regen Commons | Signal |
| **Darren** | Data pipelines, training infra, knowledge graph | Away March 20-28, reachable on Signal |
| **Carol Anne** | TELUS GPU access, Indigenomics framework | |
| **Briony Penn** | The watercolors — the primary visual language | |

---

## Important Files

| File | What |
|------|------|
| `CLAUDE.md` | Project status — the source of truth |
| `docs/style-transfer-guide.md` | All 9 style transfer options with code |
| `docs/prav-lora-integration-guide.md` | LoRA setup for StreamDiffusionTD |
| `docs/autolume-integration.md` | Full technical architecture + holonic vision |
| `docs/autolume-quickstart.md` | Loading checkpoints in Autolume |
| `briony-lora/eval/compare-v2.html` | Honest evaluation — Briony's art vs LoRA output |
| `briony-lora/train_config.toml` | LoRA training config (if retraining) |
| `.env` | TELUS API token |

## Shared Resources

- **Google Drive:** https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr
- **GitHub:** https://github.com/DarrenZal/salish-sea-dreaming
- **Mind Map:** https://coggle.it/diagram/aW01lIKXUtVgH4cW
- **Signal:** M37 Salish Sea Dreaming Chat

---

## The 30-Second Test

Someone walks into Mahon Hall cold. Dim light, projection wall.

**They see:** Fish swimming in soft watercolor — Briony Penn's palette, alive and breathing. Schools tighten and disperse. Colors shift with the tide.

**They hear:** A low drone that rises and falls. Herring data made audible — the sound of a species in trouble, but also the sound of resilience.

**They feel:** The room is breathing with the Salish Sea. Not a screensaver — a living connection to the water outside.

**They stay because:** The longer they're still, the more they notice. Movement in the corner of their eye. The fish respond to something they can't quite name. It's not performing for them — it's dreaming, and they've been invited in.
