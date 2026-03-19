# Shawn Handoff — Salish Sea Dreaming

*Darren Zal — March 19, 2026*
*I'm away March 20–28. Here's everything you need.*

---

## Where We Are

We have **3 weeks until the art show opens** (April 10, Mahon Hall, Salt Spring). Prav is scoping this as a **proof of experience** — something strong, clear, and alive. Not the full vision yet — just enough to see how people respond.

### What's Working

| Component | Status | Where |
|-----------|--------|-------|
| **Briony LoRA** | Trained + merged into SD-Turbo | `briony_watercolor_sdturbo.safetensors` on Drive + RTX 3090 |
| **RTX 3090 desktop** | 6/8 phases set up via SSH | Prav's studio. Needs TD 2025 install + first run (GUI) |
| **Fish GAN model** | 37.6% trained on TELUS H200 | ETA March 22-23. Checkpoints auto-save every 200 kimg |
| **Base GAN model** | Done (320 kimg) | Loads in Autolume, confirmed by Prav |
| **OSC data engine** | Built + tested, 4 channels live | `engine.py` — tides, moon, Fraser discharge, herring spawning |
| **Herring data pipeline** | DFO data downloaded, 5 viz notebooks | `exhibit/td/` has TD-ready JSON exports |
| **Style transfer guide** | 9 fallback options documented | [`docs/style-transfer-guide.md`](style-transfer-guide.md) |

### What's Not Done Yet

| Task | Owner | Priority |
|------|-------|----------|
| TD 2025 install on RTX 3090 | Prav/Shawn (GUI) | **High** — blocks everything |
| TouchDiffusion first run (webui.bat → TensorRT) | Prav/Shawn (GUI) | **High** — needed for LoRA pipeline |
| NDI networking test (Autolume → TD) | Prav/Shawn | **High** |
| LoRA strength test on projector | Prav | Medium |
| Fish model download from TELUS (~March 22-23) | Darren (remote) or Shawn | Medium |
| QC whale + bird image corpora | Darren (when back) | Low for April |
| Audio layer (Ableton + Manifest) | Prav | Medium |
| Narrative framing | Shawn | Medium |

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

For April we do the **first layer** — Briony-styled fish, data-driven movement, herring sonification. The full cycle is post-April (MOVE37XR Oct 2026).

---

## Architecture

```
                                   ┌─────────────────────┐
                                   │    Briony's Art      │
                                   │  (54 watercolors)    │
                                   └──────────┬──────────┘
                                              │ trained into
                                              ▼
┌──────────────┐    NDI     ┌─────────────────────────────┐
│   Autolume   │ ────────→  │   StreamDiffusion (LoRA)    │
│  (GAN fish)  │            │   "Briony filter"           │
└──────────────┘            │   strength: 0.45            │
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

**Key insight:** Briony's art is the primary visual language (Prav's direction). The AI layer (GAN + LoRA) brings it to life — making it move, breathe, respond to data. The GAN generates organic fish forms; the LoRA paints them in Briony's hand.

---

## Machines

### RTX 3090 Desktop (primary exhibition machine)
- **Location:** Prav's studio, 108 Fraser Rd, Salt Spring
- **Specs:** Ryzen 7700X, RTX 3090 24GB, 32GB DDR5, 1TB NVMe, 1000W PSU
- **OS:** Windows (required for Autolume + TouchDesigner)
- **Installed via SSH:** CUDA 11.8, VS 2022 Build Tools, Miniconda3, Autolume env (Python 3.10, PyTorch 2.8.0+cu128), TouchDiffusion repo + Briony LoRA merged
- **Still needs (GUI):**
  1. Download + install TouchDesigner 2025 (GUI installer)
  2. Load TouchDiffusion.tox, run `webui.bat` first time → builds TensorRT engine (~10 min)
  3. Run `autolume_launch.bat`, verify NDI streams visible in TD
  4. Integration soak test — all components running, monitor `nvidia-smi -l 10` for 30 min
- **SSH access:** Ask Darren for credentials if needed

### Prav's RTX 3060 Laptop
- Already running StreamDiffusionTD at 6 fps
- Autolume confirmed working with our PKL checkpoints
- Role: development, backup, potential second machine

### TELUS H200 (cloud)
- Fish model training in progress — kimg 376/1000 (March 19)
- **Jupyter API:** `https://salishsea-0b50s.paas.ai.telus.com`
- Token: in `.env` file (`Jupyter_REST_API`)
- Check status: `GET /api/contents/stylegan3/results/00014-stylegan2-fish512-gpus1-batch8-gamma20?token=<token>`
- **Important:** Storage is ephemeral. Download checkpoints when they land. Fish model completion ETA: March 22-23.
- **Arshia's guidance:** If no meaningful fish shapes by kimg 500, restart with different gamma.

---

## The Data Layer

### OSC Pulse Server (`engine.py`)
Python script that sends real ecological data over OSC to TouchDesigner. Already built and tested.

**Currently sending (4 channels):**
- `/salish/tide/level` — hourly tidal oscillation (synthetic, 4-constituent harmonic)
- `/salish/moon/illumination` — 29.5-day lunar cycle (computed)
- `/salish/fraser/discharge` — seasonal freshet curve (synthetic)
- `/salish/herring/spawning` — seasonal pulse Feb-Apr (real DFO data)

**Not yet implemented:**
- `/salish/sst/temperature` — needs Lightstation CSV
- `/salish/herring/ecosystem` — annual arc (aggregation → spawn → predator response → quiet)

**Running:**
```bash
python engine.py                          # live OSC to TD (port 7000)
python engine.py --dry-run --speed 10     # terminal preview, compressed time
python engine.py --demo                   # compress full year into 5 min
```

**Dependencies:** `pandas`, `python-osc`, `numpy`, `pyyaml`

### Herring Data
- All DFO datasets downloaded with provenance tracking
- Catch history (1888-2025), spawn timeseries, section extirpation dates
- 5 visualization notebooks: Long Decline, Spatial Collapse, DFO Forecast Accuracy, Shifting Baseline, Keystone Web
- TD-ready JSON exports in `exhibit/td/`
- **Key story:** Targeting of matriarchs in the fishing industry — herring that hold knowledge of where to spawn. Local extirpation of entire spawning populations. DFO's 1953 baseline was already a terrible year; Indigenous knowledge documents vastly different historical reality.
- **Data quality caveat (Peter Bradley, herringscraps.com/hs42/):** 1988 method break (surface→dive surveys), spawn index is a minimum estimate, pre-1978 data uses subjective categories

### Biosonification
- Prav's domain: Ableton Live + Manifest plugin
- Herring population data → mapped to drone intensity, harmonic complexity
- Tidal/seasonal cycles → rhythmic foundation
- OSC bidirectional: Ableton ↔ TD (sound drives visuals, visuals could drive sound)

---

## Style Transfer

We have a **Briony LoRA** (primary) and **8 documented fallback approaches** in case StreamDiffusion doesn't cooperate.

**Full guide:** [`docs/style-transfer-guide.md`](style-transfer-guide.md)

**Quick summary of fallbacks:**
1. **IP-Adapter** (minutes to set up, zero training) — point at a Briony painting as reference
2. **Fast Neural Style** (2-4 hrs to train, 30+ fps) — best real-time fallback
3. **AdaIN** (minutes, pretrained) — can blend between multiple Briony paintings live
4. **ControlNet + LoRA** (overnight pre-render) — highest quality for hero sequences
5. **Classic NST** (50 lines of Python) — guaranteed to work, slow but reliable

---

## Key People

| Person | Role | Contact |
|--------|------|---------|
| **Prav** (Pravin Pillay) | Creative Director, TD, final creative decisions | Signal group chat |
| **Arshia** | MetaCreation Lab (SFU), Autolume expert, training guidance | Signal group chat |
| **Eve** | Herring datasets, Regen Commons | Signal |
| **Darren** | Knowledge graph, data pipeline, training infra | Away March 20-28, reachable by Signal |
| **Carol Anne** | TELUS GPU access, Indigenomics framework | |
| **Briony Penn** | The watercolors — the primary visual language | |

---

## What You Can Do This Week

### High Priority
1. **Help Prav finish RTX 3090 setup** — TD 2025 install, TouchDiffusion first run, NDI test
2. **Narrative framing** — what's the story we tell visitors? How do we frame the herring data, the Briony art, the AI layer? What does the wall text say?
3. **Test LoRA on projector** — does strength 0.45 hold up at scale in a dark room?

### If You Have Time
4. **Download fish checkpoints** when they land (~March 22-23) from TELUS API. Place PKL in `C:\Users\user\autolume\models\`
5. **Explore alternative style transfer** — if LoRA + StreamDiffusion feels wrong, try IP-Adapter or Fast Neural Style (see guide)
6. **OSC engine → TD mapping** — wire up the 4 data channels to visual parameters in TD (color temperature, particle speed, opacity)

### Don't Worry About
- Whale/bird QC (Darren handles when back)
- TELUS training (running autonomously, will check remotely)
- Knowledge graph integration (post-April)

---

## Important Files

| File | What |
|------|------|
| `CLAUDE.md` | Project status — the source of truth, updated March 19 |
| `docs/style-transfer-guide.md` | All style transfer options with code |
| `docs/prav-lora-integration-guide.md` | LoRA setup for Prav's StreamDiffusionTD |
| `docs/autolume-integration.md` | Full technical architecture + holonic vision |
| `docs/autolume-quickstart.md` | Loading checkpoints in Autolume |
| `briony-lora/train_config.toml` | LoRA training config (if retraining needed) |
| `briony-lora/eval/` | HTML comparison pages showing LoRA results |
| `.env` | TELUS API token |
| `scripts/telus-training-setup.sh` | Reproducible TELUS training bootstrap |

---

## Shared Resources

- **Google Drive:** https://drive.google.com/drive/folders/17QVEYgmEZDYupWI4vGF2QicXSVKWfk_6
- **GitHub:** https://github.com/DarrenZal/salish-sea-dreaming
- **Mind Map:** https://coggle.it/diagram/aW01lIKXUtVgH4cW
- **Signal:** M37 Salish Sea Dreaming Chat (primary comms)

---

## The 30-Second Test

Someone walks into Mahon Hall cold. Dim light, projection wall.

**They see:** Fish swimming in soft watercolor — Briony Penn's palette, alive and breathing. Schools tighten and disperse. Colors shift with the tide.

**They hear:** A low drone that rises and falls. Herring data made audible — the sound of a species in trouble, but also the sound of resilience.

**They feel:** The room is breathing with the Salish Sea. Not a screensaver — a living connection to the water outside.

**They stay because:** The longer they're still, the more they notice. Movement in the corner of their eye. The fish respond to something they can't quite name. It's not performing for them — it's dreaming, and they've been invited in.
