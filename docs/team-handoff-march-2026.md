# Team Handoff — Salish Sea Dreaming

*Darren Zal — Updated March 23, 2026*
*I'm away March 20–28 (snowboarding, online evenings). Here's everything you need to keep building.*

---

## Where We Are

**3 weeks until the art show opens** (April 10, Mahon Hall, Salt Spring). Prav is scoping this as a **proof of experience** — something strong, clear, and alive. Not the full vision yet — just enough to see how people respond.

### What's Working

| Component | Status | Where |
|-----------|--------|-------|
| **Briony LoRA (SD 1.5)** | Works at 30 steps offline. Real-time (8-20 steps) untested. | `briony_watercolor_v1.safetensors` (38 MB) on Drive |
| **RTX 3090 desktop** | 6/8 phases set up via SSH | Prav's studio. Needs TD 2025 install + first run (GUI) |
| **Fish GAN model** | **Complete** (kimg 1000). Prav tested — "dreams in dead fish on shore." | [PKL on Drive](https://drive.google.com/file/d/1RPb2c_PdKa7oCX---cUBZMq6GljW17la/view) |
| **Base GAN model (320 kimg)** | Loads in Autolume. Prav's preferred ground layer. | On Drive. **License-tainted — R&D only, not for exhibition.** |
| **Dreaming model corpus** | 778 CC-safe intertidal images scraped + QC app deployed | [QC app](http://37.120.162.60:8090/tools/qc-review.html) (salishsea/dreaming2026) |
| **OSC data engine** | Built + tested, 4 channels live | `engine.py` — tides, moon, Fraser discharge, herring spawning |
| **David Denning images** | Intertidal organisms on black backgrounds — arriving Tuesday | Contact Prav for samples |
| **Moonfish footage** | Video samples arriving this week | Contact Prav |

### What's Not Working / Pivoting

| Issue | Details |
|-------|---------|
| **Fish model** | kimg 1000 complete but output is dominated by "dead fish on shore" from iNat training data. **Pivoting to multi-species dreaming model.** |
| **SD-Turbo + LoRA** | img2img doesn't work (blurry). **txt2img untested** — Prav suggests retesting. |
| **Real-time style transfer** | LoRA works at 30 steps offline but not yet proven in real-time StreamDiffusion. Key gap: test at 8-20 steps. |
| **RTX 3090 GUI phases** | TD 2025 install, TouchDiffusion first run, NDI networking — need physical access |

---

## The Vision

**Short version:** The Salish Sea dreaming itself awake. Technology not as extraction, but as perception. The bioregion already has consciousness — we're building an interface to help humans tune in.

**What the audience experiences:** They walk into a dim room — an immersive dreaming space. Projected across multiple walls, marine organisms emerge from and fade into each other... as if floating beneath the water. An octopus dissolves into an anemone, a fish school shimmers and reforms. Briony Penn's watercolor aesthetic holds the room. Sound carries ecological data — herring population mapped to drone intensity. Stillness is rewarded with deeper revelation. Periodically, data visualizations surface — a map of spawning grounds going dark, a keystone web dimming — then dissolve back into the dreaming.

**The room is a spatial composition with four temporal layers:**
1. **Present tense** — live GAN wall (Autolume, dreaming model). The organism, now, shifting.
2. **Memory / narrative** — Briony narrative wall. Pre-rendered ecological film poem at 30 steps.
3. **Deep time / pulse** — data-driven atmosphere (floor/ceiling). Tides, moon, herring spawn.
4. **Witness / evidence** — data visualizations emerging and receding. Political testimony.

**Prav's framing (March 23):** "One immersive dreaming space... as if one were floating in the ocean beneath the water... like a dreaming octopus... being dreamt."

Full exhibition architecture: see plan at `~/.claude/plans/zany-greeting-fox.md`

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

**Step-by-step setup:** [`docs/lora-integration-guide.md`](lora-integration-guide.md) — loading the LoRA, trigger token, txt2img/img2img/video modes, tuning parameters, testing checklist.

### What We Tried (March 19-21)

**SD-Turbo + LoRA: Doesn't work.**
SD-Turbo is distilled for 1-step generation. A style LoRA pushes it off its equilibrium — at low weight (0.04) nothing happens, at weight 1.0 everything goes blurry. No sweet spot.

**SD 1.5 + LoRA + 4 steps (StreamDiffusion): Too few steps.**
Switched to SD 1.5 base with `briony_watercolor_v1.safetensors`. txt2img produced watercolor-ish results, but not recognizably Briony. 4 steps isn't enough for the LoRA to express.

**SD 1.5 + LoRA + 30 steps (offline eval): Actually looks good.**
The [evaluation images](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html) generated at 30 steps with guidance 7.5 show real watercolor feel — soft edges, painterly texture, natural palette, some linework. **The LoRA IS working — the problem was the inference pipeline (too few steps), not the LoRA itself.**

**AdaIN style transfer (March 21): Tested, weaker than LoRA.**
Tested pretrained AdaIN on GAN fish frames + 3 Briony paintings as style reference. Transfers color palette but produces texture-pattern artifacts and no linework. The LoRA at 30 steps is actually better at capturing Briony's style.

### Key Learning

**The LoRA is the right approach.** It just needs more inference steps than SD-Turbo or StreamDiffusion at 4 steps can provide. The path forward: SD 1.5 + LoRA at 8-20 steps. LCM-LoRA can speed up inference without losing quality.

### The Gap (still present)

See the [LoRA evaluation page](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html) — Briony's actual paintings next to what the LoRA produces. At 30 steps the output has watercolor feel but still misses her **boldest ink outlines and vivid saturated colors**. Retraining with all 54 curated watercolors (not 22) at rank 32 should close this gap.

**Training images:** The LoRA was trained on [22 curated watercolors](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/training_contact_sheet.png) — a subset selected for consistent watercolor style. Briony's [full archive](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/archive_not_in_training.png) (~67 works across 9 categories) includes pen-and-ink, maps, mandalas, field journals, and signage — mixed styles that would confuse a LoRA. The curated watercolor corpus has 55 images in `training-data/briony-marine-colour/` if retraining with more.

### Which LoRA file to use

| File | Base model | Status | Link |
|------|-----------|--------|------|
| **`briony_watercolor_v1.safetensors`** (38 MB) | **SD 1.5** | **Use this.** Best results. | [Download](https://drive.google.com/file/d/1fIFBYGorHjfg76w82AwHOhyiiqptSBGu/view) |
| `briony_watercolor_sdturbo.safetensors` (13 MB) | SD-Turbo | Skip — doesn't work | — |
| `briony_watercolor_sdturbo_kohya.safetensors` (13 MB) | SD-Turbo | Skip — kohya format, also doesn't work | — |

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

| Priority | Approach | Setup time | Real-time? | Status |
|----------|----------|-----------|------------|--------|
| **1** | **SD 1.5 + LoRA (8-20 steps)** | Done | 1-6 fps | Best results so far at 30 steps. Find the right step count for real-time. |
| **2** | **LoRA + LCM-LoRA combo** | Minutes | 3-8 fps (est.) | Speed up SD 1.5 to 4-8 steps without losing quality. |
| **3** | **LoRA retrain** (54 images, rank 32) | 30-60 min | Same | Sharpen the Briony style further. |
| **4** | **FNST** | 2-4 hrs train | 30+ fps | If LoRA fps is too low for live performance. |
| **5** | **AdaIN** | Minutes | 20-40 fps | **Tested March 21 — color OK but texture artifacts, weaker than LoRA.** |
| **6** | **CycleGAN** | 12-24 hrs | 30 fps | Research bet. |

**The core decision this week:** The LoRA works — it just needs more inference steps. Test SD 1.5 + LoRA at 8, 15, 20 steps. If fps is too low, try LCM-LoRA combo for speed. If that's still not enough, FNST is the real-time fallback (30+ fps). AdaIN was tested and is weaker than the LoRA. See [`docs/style-transfer-guide.md`](style-transfer-guide.md) for full details.

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
- **Fish model complete** (kimg 1000). All checkpoints on Drive.
- **TELUS is now free** for the dreaming model training.
- Jupyter API: `https://salishsea-0b50s.paas.ai.telus.com` (token in `.env`)
- **Important:** Storage is ephemeral — download checkpoints before pod restarts

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

### Biosonification

**Decision (March 19):** Sonification is data-*inspired* artistic interpretation, not literal data-to-sound translation. Start with spreadsheet/MIDI, move to live OSC as second stage.

**Phase 1 (this weekend):**
- **Eve** is creating MIDI (0-127 CC range) and Manifest CSV data files from the ecological datasets — herring, temperature, tides, moon, spawn intensity, river flow
- **Prav** tests MIDI files on Ableton + Manifest plugin and shares results over weekend

**Phase 2 (stretch):**
- Live OSC pulse server (`engine.py`) feeds real-time data to Ableton and TD simultaneously
- Bidirectional: Ableton ↔ TD (sound drives visuals, visuals could drive sound)

---

## GAN Strategy

### Pivot: Multi-species dreaming model is the direction

**The fish model is complete but not the answer.** Prav tested kimg 1000 in Autolume — the output is dominated by "dead fish on shore" because the iNaturalist training data was mostly fish-on-gravel. The fish model remains available as a fallback but we're pivoting to the dreaming model.

**Prav's vision (March 23):** "One immersive dreaming space using the 320 model as the ground for the immersive Salish Sea consciousness. With images emerging from and fading into it... as if one were floating in the ocean beneath the water... like a dreaming octopus... being dreamt."

**The path forward:** Build a CC-safe multi-species dreaming model trained on underwater/intertidal species (octopus, anemones, starfish, kelp, eelgrass, fish, seals, underwater whales). One model where navigating the latent space IS navigating the ecosystem. Species dissolve into each other organically.

Full concept doc: [`docs/dreaming-model-corpus.md`](dreaming-model-corpus.md)

**320 kimg base model:** Prav likes it as the ground layer — it has the right dreamlike quality. However, it has a **license problem** (majority CC BY-NC in the training data). Cannot be used at the exhibition. The concept is right but the corpus must be rebuilt CC-safe.

**What's available now:**
| Model | Status | Link |
|-------|--------|------|
| Fish kimg 1000 | Complete. Dominated by dead-fish-on-shore. Fallback only. | [PKL](https://drive.google.com/file/d/1RPb2c_PdKa7oCX---cUBZMq6GljW17la/view), [Fakes](https://drive.google.com/file/d/1e0NVRR9vvD2iV9GHY1ehrGaHfokfNdhy/view) |
| Base 320 kimg | Dreamlike quality. License-tainted — R&D only. | [PKL](https://drive.google.com/file/d/11_4WG130pFDq5euT4M75dL2RBNSYA_0X/view) |
| Dreaming model | Corpus being curated (778 intertidal scraped + David's images incoming). Training once QC'd. | [QC app](http://37.120.162.60:8090/tools/qc-review.html) |

**Incoming material:**
- **David Denning's intertidal images** (Tuesday) — organisms isolated on black backgrounds. Could be excellent GAN training data if licensing is clear.
- **Moonfish video samples** — this week

**TELUS is free** — ready for the next training job once the dreaming corpus is QC'd and prepped.

---

## Tasks This Week

### Prav
1. **Test more inference steps** (8, 15, 20) with SD 1.5 + Briony LoRA — is the style there?
2. **Try LCM-LoRA combo** if StreamDiffusionTD supports two LoRAs
3. **Make the pivot decision** — LoRA working or try alternative approach?
4. **Test MIDI files from Eve** on Ableton + Manifest — share results over weekend
5. **Experiment with OSC integration** for live data
6. **Get Moonfish Media footage from David** (Tuesday) — herring, salmon, birds, whales
7. **RTX 3090 setup** — TD 2025 install, TouchDiffusion first run, NDI test
8. **Explore Nano Banana, OpenArt, or [20-min masterpiece](https://medium.com/@jamesonthecrow/20-minute-masterpiece-4b6043fdfff5)** approaches
9. **Connect with Caroline** about Gura Gladue involvement for hackathon

### Shawn
1. **Take over style transfer work** — own the LoRA testing and fallback approaches (Fast NST, AdaIN, etc.) while Darren is away
2. **Prepare contingency Python style transfer** if LoRA doesn't work — see [`docs/style-transfer-guide.md`](style-transfer-guide.md)
3. **Boids flocking algorithm in TouchDesigner** — get a basic fish school working by weekend
4. **Help Prav with RTX 3090 GUI setup** — TD 2025, TouchDiffusion first run
5. **Narrative framing** — what story do we tell visitors? Wall text. Framing for the herring data.
6. **Create new Signal group** for hackathon planning — invite Caroline, Kay, and team
7. **Download fish checkpoints** when they land (~March 22) — place PKL in `C:\Users\user\autolume\models\`

### Eve
1. **Create MIDI (0-127) and Manifest CSV data files** from ecological datasets — herring, temperature, tides, moon, spawn intensity, river flow
2. Deliver to Prav this weekend for Ableton testing

### All
- **Send bios to Prav on Signal** for exhibition curator
- **Draft project definition statement** and vision document for Caroline re hackathon
- **Collective crediting** for exhibition — decision made: not individual lead artist

### Darren (remote)
- Monitor TELUS training, download final fish checkpoint when done (~March 22)
- Get Leo to help with TD 2025 + StreamDiffusion setup next week
- Reachable on Signal for debugging

### Don't Worry About
- Whale/bird QC (Darren when back)
- Knowledge graph integration (post-April)
- Hackathon logistics beyond Signal group setup + weekly sync cadence

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
| **Leo** | TouchDesigner + StreamDiffusion setup help | Darren connecting next week |
| **David Denning** | Moonfish Media footage | Prav getting footage Tuesday |

---

## Incoming This Week

- **Moonfish Media footage** (Tuesday) — Prav getting herring, salmon, birds, whales footage from David. This is a key input for img2img style transfer and Resolume layers.
- **Eve's MIDI/CSV data** (weekend) — ecological datasets converted to MIDI 0-127 for Ableton/Manifest testing.
- **Fish GAN final checkpoint** (~March 22) — kimg 1000, download from TELUS.
- **Leo** — Darren connecting him for TD 2025 + StreamDiffusion setup help next week.

---

## Beyond April: Hackathon / Creator Jam

**What:** Creator Jam / Hackathon at the Indigenomics Impact Summit at Northeastern University
**When:** ~8 weeks out (late May)
**Trajectory:** Life at the Center 2027, potential Indigenous Technology House at ETHCON

**This week:**
- Shawn creates new Signal group for hackathon planning — invite Caroline, Kay, and team
- Draft project definition statement and vision document for Caroline
- Set up weekly sync meetings for coordination
- Prav connecting with Caroline about Gura Gladue involvement

**Note on Gaia AI:** Prav's feedback — promising first step but reads as "Western idealistic." Needs Indigenous traditional wisdom and cultural grounding to become truly powerful. Not a blocker for the art show but important context for the hackathon direction.

---

## Key Decisions Made (March 19)

1. **Collective crediting** for the exhibition — not individual lead artist
2. **Sonification is artistic interpretation** — data-inspired, not literal data-to-sound translation
3. **MIDI first, live OSC second** — prove the concept with spreadsheets before building live pipelines
4. **SD 1.5, not SD-Turbo** — for the Briony LoRA. SD-Turbo is incompatible with style LoRAs.

---

## Important Files

| File | What |
|------|------|
| `CLAUDE.md` | Project status — the source of truth |
| `docs/style-transfer-guide.md` | All 9 style transfer options with code |
| `docs/lora-integration-guide.md` | LoRA setup for StreamDiffusionTD |
| `docs/autolume-integration.md` | Full technical architecture + holonic vision |
| `docs/autolume-quickstart.md` | Loading checkpoints in Autolume |
| `briony-lora/eval/compare-v2.html` | [Honest evaluation](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html) — Briony's art vs LoRA output |
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
