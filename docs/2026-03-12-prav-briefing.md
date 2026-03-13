# The Salish Sea Dreaming — Briefing for Prav

**March 12, 2026 — from Darren**

Hey Prav — sorry we couldn't connect today. Here's everything you need to get oriented and start testing. The most important thing you can do right now is **get Autolume running with the smoke test checkpoint** (Section 6 has the quickstart). That way when the real trained models land in the next few days, you're ready to go.

---

## 1. What We're Building (April 10–26)

**"Digital Ecologies: Bridging Nature and Technology"** — Mahon Hall, Salt Spring. Opens **April 10**.

The Salish Sea Dreaming is an immersive AI art installation where the Salish Sea uses technology to perceive itself. Audiences enter a co-dreaming space — the ecosystem's consciousness made visible through generative imagery, presence-responsive visuals, and biosonification.

**Three visual sources** feed the generative system:

1. **Briony Penn's** ecological watercolors → visual DNA for a custom StyleGAN2 model (training now)
2. **David Denning's** photographic archive → "long-term bioregional witnessing" via LoRA+img2img style transfer
3. **Moonfish Media** underwater cinematography → herring, salmon, marine habitat footage as reference/projection

**The live stack:** Autolume (StyleGAN2 inference) → NDI → TouchDesigner + **Resolume Arena** (projection mapping/video mixing) → 1–2 projectors onto 3–6m wall.

**Sound:** You + TBC collaborator — Ableton Live + Max for Live biosonification.

**Two modes:** Autonomous Installation (runs unattended during gallery hours) + Live Performance (you performing real-time).

**Spatial spec from your Tech Rider:** 4m × 4m floor, 3–6m projection wall, 1–2 projectors, stereo audio, dim lighting.

---

## 2. How the Training Pipeline Works

We're using **StyleGAN2** via [Autolume](https://github.com/Metacreation-Lab/autolume) from SFU MetaCreation Lab — a GAN that learns visual patterns from a dataset and generates new images in the same style.

```
  539 marine photos           54 Briony watercolors          Live performance
  (iNaturalist, CC)           (artist permission)            (Autolume + TD)
        │                           │                             │
        ▼                           ▼                             ▼
   Base training ───────→  Fine-tune (resume) ───────→  .pkl → Autolume → NDI → TD
   539 photos, H200          54 Briony paintings           RTX 3060 inference
   Currently running         Next step                     Real-time, audio-reactive
   → extending to 1000+      Same hardware                 OSC/MIDI control
```

**Stage 1 — Base model** (539 marine photos):
Train from scratch on curated underwater/nearshore photos (37 Salish Sea species). Teaches the model what marine life *looks like* — colour palette, textures, forms, light. Output: `base-underwater-v1.pkl`.

**Stage 2 — Fine-tune** (54 Briony watercolors):
Resume from base checkpoint on Briony's art. Shifts output from photographic → painterly. Multiple snapshots give a **gradient from photographic to painterly** — you pick the sweet spot or interpolate live.

**Stage 3 — Inference** (you in Autolume):
Load the `.pkl` into Autolume. Real-time latent space navigation, audio-reactive, OSC/MIDI, NDI out to TouchDesigner. This is what the audience sees.

---

## 3. Where We Are Right Now (March 12)

**Base model training is running** on the TELUS H200 GPU — 539-image marine photo corpus. Currently ~46% through the first 200 kimg target. Training is stable at 100% GPU utilization.

**Arshia** (SFU MetaCreation Lab researcher — he built Autolume) is advising us. His key guidance:

- Extend base training to **kimg=1000+** (current 200 is just a v1 checkpoint)
- **LoRA + img2img** may be better than GAN fine-tune for applying Briony's style to David Denning's photos
- 54 Briony images is low for fine-tuning — experimental, but worth trying
- Mac Autolume version is **in development** but not ready yet — Windows/Linux only for now
- He has access to **Alliance Canada's 4x H100 cluster** as backup to TELUS

**Timeline for you getting real models:**
- v1 base checkpoint (200 kimg): ~12-24 hours from now
- Extended base (1000+ kimg): ~3-4 days
- Briony fine-tune: starts after base, ~1 hour per run, multiple snapshots

---

## 4. The GitHub Repo

**[github.com/DarrenZal/salish-sea-dreaming](https://github.com/DarrenZal/salish-sea-dreaming)**

| What | Link |
|------|------|
| Full repo | [github.com/DarrenZal/salish-sea-dreaming](https://github.com/DarrenZal/salish-sea-dreaming) |
| Training data + provenance | [training-data/](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/training-data) |
| Corpus specs + smoke test results | [training-data/README.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/training-data/README.md) |
| Full technical architecture | [docs/autolume-integration.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/autolume-integration.md) |
| Briony art archive (git-lfs) | [VisualArt/Brionny/](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/VisualArt/Brionny) |
| Scripts + tools | [scripts/](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/scripts) · [tools/](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/tools) |

---

## 5. The Training Data

### Briony fine-tune corpus — 54 watercolors at 512×512

- [Browse all 54 PNGs on GitHub](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/training-data/briony-marine-colour)
- [provenance.csv](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/training-data/briony-marine-colour/provenance.csv) — tracks source painting, crop method, artist permission
- Expanded from marine-only → all ecological watercolors (salmon-forest, camas, landscapes)

### Marine photo base corpus — 539 photos at 512×512

- [marine-photo-base.zip on Google Drive](https://drive.google.com/file/d/1l1x0TEY8W9WNG7jIX9TZ5iFdQkRoyHfo/view) — 64 MB download
- QC'd from 740 iNaturalist candidates across 37 Salish Sea species
- [rejects.csv](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/training-data/review/rejects.csv) — 201 rejected images with reasons

---

## 6. YOUR FIRST STEP: Get the Base Model Running in Autolume

This is the most useful thing you can do right now. The base v1 checkpoint (200 kimg on 539 marine photos) is on the shared Drive. Getting Autolume working with this means when the fine-tuned Briony models land, you just swap the file.

### Quickstart Guide

Full step-by-step: **[docs/autolume-quickstart.md on GitHub](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/autolume-quickstart.md)**

**TL;DR:**
1. Install CUDA 12.8 + C++ Build Tools + Miniconda
2. Clone Autolume: `git clone https://github.com/Metacreation-Lab/autolume.git`
3. Download checkpoint: [**network-snapshot-000200.pkl** (347 MB)](https://drive.google.com/file/d/1QmmeCt2-P_C-KY1Kss2jSvz1gc6CpQB3/view) → put in `models/`
4. Run: `python main.py`

### Available Checkpoints

| Checkpoint | Download | Notes |
|-----------|----------|-------|
| **network-snapshot-000200.pkl** | [**347 MB**](https://drive.google.com/file/d/1QmmeCt2-P_C-KY1Kss2jSvz1gc6CpQB3/view) | **Base v1 (200 kimg, 539 marine photos) — start with this** |
| network-snapshot-000025.pkl | [347 MB](https://drive.google.com/file/d/1WOMcUhi3RaML_TjqEilvHZOh8mBNyu7E/view) | Early smoke test (25 kimg) |
| network-snapshot-000020.pkl | [347 MB](https://drive.google.com/file/d/1tquQsIQCTiplsLDPZRBOXGsT_5qtEfQR/view) | Early smoke test (20 kimg) |

### Dataset zips (also on Drive)

| File | Download |
|------|----------|
| briony-marine-colour.zip (54 watercolors) | [27 MB](https://drive.google.com/file/d/1cOoF09ZuNjpXQocg_hJ7NuMobVNd5ioV/view) |
| marine-photo-base.zip (539 photos) | [64 MB](https://drive.google.com/file/d/1l1x0TEY8W9WNG7jIX9TZ5iFdQkRoyHfo/view) |

**[SSD Shared Drive folder](https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr)** — all assets live here

### Compatibility Warning

Our PKL was trained with the NVlabs StyleGAN3 codebase. Autolume uses its own fork. If the checkpoint **fails to load**, let me know immediately — we'd need to retrain with Autolume's own training pipeline. Better to find this out now than after the Briony fine-tune.

---

## 7. Installation Hardware

| Option | Pros | Cons |
|--------|------|------|
| Your RTX 3060 laptop | Works now, can test today | Not ideal for 24/7 exhibition |
| Dedicated desktop (RTX 3060/3070) | Reliable, affordable used | Need to source + budget |
| Mac Mini M4 (MOVE37XR inventory) | Already available | **Won't work** — Autolume is Windows/Linux only (Mac version in dev, not ready) |

**Key constraint:** Autolume requires **NVIDIA GPU with CUDA**. No Apple Silicon support yet.

You mentioned grant budget may be available. Even a used desktop with an RTX 3060 would be solid for continuous exhibition mode.

---

## 8. Scope Alignment — Your Exhibition Outline

I reviewed your three project docs (Collaboration Outline, Exhibition Outline, Tech Rider). Really well articulated. A few things I want to make sure we're aligned on for April:

**Explicitly excluded for April** (from your Exhibition Outline):
- No networked GPUs or cloud inference
- No live ecological data feeds
- No multi-room installation
- No AI agents or chat interfaces

This aligns well with where we are. The April version is: pre-trained models running locally on an NVIDIA machine, Autolume inference, TD + Resolume compositing, Kinect presence, Ableton sound. Clean and focused.

**"Integrity over ambition" / "succeeds by doing less, not more"** — agreed. Let's nail this.

**Things your docs mention that aren't in our technical architecture yet:**
- Resolume Arena (I've added it to our docs now)
- Sound layer details (Ableton + Max for Live biosonification)
- Two operational modes (autonomous vs live performance)

**Things our side has that aren't in your docs yet:**
- TELUS H200 training progress (base model running)
- Arshia's involvement + MetaCreation Lab advisory
- LoRA + img2img as alternative to pure GAN fine-tune
- Alliance Canada backup GPU access

We should do a joint pass to sync these up.

---

## 9. Phase 2 Venues (from your docs)

| Venue | Date |
|-------|------|
| Indigenomics Impact | May 2026 |
| MOVE37XR Symposium | October 2026 |
| DEV CON ETH Mumbai | November 2026 |

---

## 10. What You Can Do Right Now

**Priority 1 — Test Autolume:**
1. Download [000200.pkl (347 MB)](https://drive.google.com/file/d/1QmmeCt2-P_C-KY1Kss2jSvz1gc6CpQB3/view)
2. Follow the [quickstart guide](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/autolume-quickstart.md)
3. Tell me if it loads or fails — this is critical info

**Priority 2 — Hardware decision:**
- What machine for the April 10 exhibition? Your laptop or dedicated desktop?
- Is grant budget available?

**Priority 3 — Review the repo:**
- Browse the [GitHub repo](https://github.com/DarrenZal/salish-sea-dreaming)
- Look at the [54 Briony training images](https://github.com/DarrenZal/salish-sea-dreaming/tree/main/training-data/briony-marine-colour)
- Read the [full architecture doc](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/autolume-integration.md)

---

## What I'm Doing Next

- Monitoring base training on TELUS (should finish 200 kimg overnight)
- Download v1 checkpoint and share with you on Drive
- Resume training to kimg=1000+ (Arshia's recommendation)
- Start Briony fine-tune from base checkpoint — will share snapshots as they come
- Friday 12:30 call with Arshia — review training progress, discuss LoRA approach
- Friday TELUS meeting — push for environment improvements

I'll share new checkpoints on the [Drive folder](https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr) as they land.

---

**Questions? Hit me on Signal anytime.**
