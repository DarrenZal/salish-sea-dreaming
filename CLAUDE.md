# Salish Sea Dreaming

> *"We are the Salish Sea, dreaming itself awake."*

Interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself.

**Target:** Salt Spring Spring Art Show — "Digital Ecologies: Bridging Nature and Technology" at Mahon Hall, April 10–26, 2026.

## Current Status

**Date:** 2026-03-19
**Status:** RTX 3090 desktop 6/8 phases set up via SSH. Fish model at kimg 376/1000 on TELUS (37.6%, ETA March 22-23). Briony LoRA + SD-Turbo merged and ready for TouchDiffusion. Creative jam today/tomorrow with Prav, Shawn, Eve.

**License Policy:** COMMERCIAL USE — CC0, CC BY, CC BY-SA only. Artist fee at exhibition = commercial under CC terms. CC BY-NC excluded.

**What's Done:**
- Base model v1 (200 kimg) + resume (320 kimg) — **PKL loads in Autolume CONFIRMED** (Prav tested, NDI→TD working)
- Team pivot (2026-03-13): three focused species models (Fish, Whales, Birds) as separate Autolume instances mixed via NDI in TouchDesigner
- Multi-corpus pipeline: `scraper` (`--corpus`, `--license-filter`, 30s download timeout), `qc_approve` (`--corpus`, `--rejects-file`), `prep_training_data` (`--corpus`). `scripts/backfill_licenses.py` for retroactive license auditing.
- Species TSVs: `tools/species-fish.tsv` (13 bony fish), `tools/species-whales.tsv` (6 cetaceans), `tools/species-birds.tsv` (10 seabirds). All taxon_ids populated.
- **All three CC-safe corpora scraped** (2026-03-15): Fish 911 (13 sp), Whale 731 (6 sp), Bird 1729 (10 sp). All provenance tracked.
- **Fish QC complete** (2026-03-16): 378 approved, 507 rejected (dead fish, blurry, wrong species). Herring eggs (15), fish schools (12), birds-in-fish (5) separated to own folders for future training.
- **Fish model training** (run 00014): started March 17 03:32 UTC, kimg=1000, snap=50 (→ checkpoint every 200 kimg). At **kimg 376** as of March 19 ~19:00 UTC (~573 sec/kimg). kimg 200 checkpoint + fakes grid downloaded — fish shapes emerging, training healthy. ETA completion: **March 22-23**. **Arshia: if no meaningful results by kimg 500, restart with different gamma.**
- TELUS training artifacts saved locally: `telus/` (logs, training_options, stats from runs 00009+00012), `scripts/telus-training-setup.sh` (reproducible bootstrap)
- **TELUS Jupyter API:** `https://salishsea-0b50s.paas.ai.telus.com` — token in `.env` (`Jupyter_REST_API`). Check run status: `GET /api/contents/stylegan3/results/00014-stylegan2-fish512-gpus1-batch8-gamma20?token=<token>`
- All datasets + QC'd zips uploaded to [Drive](https://drive.google.com/drive/folders/17QVEYgmEZDYupWI4vGF2QicXSVKWfk_6)
- Arshia feedback: fish + bird datasets look best; whale last (shapes unclear). Training order: Fish → Bird → Whale.
- **Holonic morphing vision** documented in `docs/autolume-integration.md` — food web as fractal cycle, boids system, recursive instancing, cross-model transitions via NDI crossfades
- `docs/` reorganized: 11 dated/sent docs archived to `docs/archive/`
- **RTX 3090 desktop purchased + 6/8 phases set up** (2026-03-19): Ryzen 7700X + Gigabyte RTX 3090 24GB + 32GB DDR5 + 1TB NVMe + 1000W PSU — CA$1,950. Setup via SSH: GPU verified (24GB, 61 MiB idle), VS 2022 Build Tools (MSVC 14.44), Miniconda3 (conda 26.1.1), Autolume env (Python 3.10, PyTorch 2.8.0+cu128, ndi-python, python-osc), TouchDiffusion repo cloned + Briony LoRA merged into SD-Turbo (128 layers fused, saved as diffusers + UNet safetensors). **Remaining (needs GUI):** TD 2025 install, TouchDiffusion first run (webui.bat → venv + TensorRT build ~10 min), NDI networking test, integration burn-in. **Autolume: only 1 instance per machine** (Arshia, March 17).

- **Briony LoRA trained + evaluated** (2026-03-18): LoRA v1 trained on 22 Briony Penn watercolors (rank 16, 1000 steps, SD 1.5 base) on Windows RTX 3090. 18 eval images confirm style generalizes across marine, land, and atmospheric subjects. Checkpoint: `briony_watercolor_v1.safetensors` on Windows desktop.
- **LoRA img2img integration tested** (2026-03-18): Successfully applied LoRA as post-processing "Briony filter" on StyleGAN fish output. 20 GAN frames tested at 5 strength levels (0.25–0.65). **Sweet spot: s0.35–0.45** — watercolor aesthetic visible while preserving GAN composition. Avg latency: 0.97s/frame on RTX 3090 (~1 fps, viable for pre-rendered pipeline). Temporal coherence test shows stable style across frames. Results: `briony-lora/eval/img2img_compare.html`.
- **SD-Turbo LoRA variant** (2026-03-18): Retrained LoRA on SD-Turbo base to match Prav's StreamDiffusionTD setup. `briony_watercolor_sdturbo.safetensors` (13 MB). Merged into TouchDiffusion on RTX 3090 desktop — 128 layers fused into base model. Integration guide: `docs/prav-lora-integration-guide.md`. Trigger token: `brionypenn`.

**What's Left:**
1. **Creative jam** (March 19-20) with Prav, Shawn, Eve — lock proof-of-experience scope, test LoRA on projector, define minimum viable build
2. **RTX 3090 remaining setup** (needs GUI): TD 2025 install, TouchDiffusion first run (webui.bat → TensorRT ~10 min), NDI networking, integration burn-in. Fish PKL → `C:\Users\user\autolume\models\`
3. **Download fish kimg 400 checkpoint** — due ~March 19-20, test in Autolume on RTX 3090
4. **QC whale + bird corpora** — review in Finder, create rejects CSVs, run `qc_approve`, `prep_training_data`
5. **Kick off bird training** on TELUS after fish completes (~March 22-23)
6. **Contact Moonfish Media** for herring footage permission
7. **Herring data + biosonification** — Eve/Shawn herring datasets, Ableton + Manifest plugin, OSC→boids reactivity
8. Darren away March 20–28
9. **Post-jam:** Whale training (last), multi-instance burn-in, full integration test

## Project Vision

Technology not as extraction, but as perception. The bioregion already has consciousness — we're building an interface to help humans tune into it. Stillness and attention are rewarded, not performance.

**Core themes:** Bioregional consciousness, Indigenous worldviews, data poetics, emergent organic behaviors, three-eyed seeing (Western science + Indigenous knowledge + the land itself).

## Team & Collaborators

| Person | Role | Notes |
|--------|------|-------|
| **Pravin Pillay** (MOVE37XR) | Creative Director | TouchDesigner, AI visualization, immersive media. Studio: 108 Fraser Rd, Salt Spring |
| **Carol Anne Hilton** | Indigenomics founder | Framework, relational value, TELUS GPU access |
| **Briony Penn** | Naturalist, illustrator | Watercolors, ecological storytelling |
| **Darren Zal** | Technical infrastructure | Knowledge graphs, KOI, data integration |
| **Shawn** | Creative technologist | Claude Code, GPU activation |
| **Eve Marenghi** | Data scientist | Regen Commons steward |
| **Brad Necyk** | Artist, researcher | Latent space concepts, studio at Cobble Hill |
| **Moonfish Media** | Underwater cinematography | Herring, salmon, marine habitat footage |
| **Natalia Lebedinskaia** | Panel moderation | Contextual framing |
| **David Denning** | Photographer | Long-term bioregional witnessing |

**Curator:** Raf (Digital Ecologies / Salt Spring) — not ACON, not "Rob"

## Repository Structure

```
salish-sea-dreaming/
├── CLAUDE.md
├── README.md
├── scripts/              # Training pipeline scripts (see Scripts section)
├── docs/                 # Project docs and briefing notes
├── examples/             # TouchDesigner .toe files
├── web/                  # Three.js prototype (Vite, WebGL, GLSL shaders)
├── tools/                # Utility scripts (iNat scraper, QC tools)
├── images/marine/        # 128 iNaturalist taxa (Guide 19640, 500px)
├── images/marine-base-raw/  # 740 raw 1024px iNat photos (gitignored)
├── training-data/        # Training corpora + provenance tracking
│   ├── briony-marine-colour/ # 54 Briony watercolors at 512x512
│   ├── marine-photo-base/    # 539 QC'd marine photos at 512x512
│   └── review/               # QC contact sheets + rejects.csv
├── briony-lora/           # LoRA style transfer exploration
│   ├── *.png/*.txt        # 22 training image+caption pairs
│   ├── train_config.toml  # kohya_ss training config
│   ├── train.sh           # Cross-platform training automation
│   ├── extract_frames.py  # Slice fakes grids into individual frames
│   ├── test_img2img.py    # img2img batch with strength sweep
│   ├── evaluate_lora.py   # Generate eval images across subjects
│   └── eval/              # Evaluation results + HTML comparison pages
├── models/               # Trained checkpoints (gitignored, ~347 MB each)
└── VisualArt/            # Briony Penn's full art archive (git-lfs)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/prep_training_data.py` | Resize + center-crop approved images to 512x512 training corpora |
| `scripts/crop_candidates.py` | Generate candidate crops + contact sheets from Briony paintings |
| `scripts/dream_briony.py` | img2img dream transformations (13 images, 5 directions) |
| `scripts/generate_visuals.py` | Text-to-image generation (DALL-E 3) |
| `scripts/proof_sheet.py` | Contact sheet generator for review |
| `scripts/create_loops.py` | FFmpeg video loop creator (Instagram formats) |
| `scripts/mycelium.py` | v14 — TouchDesigner mycelium network |
| `scripts/psychedelic_video.py` | v4 — TouchDesigner video effect chain |
| `scripts/dream_video.py` | Dream video generation |
| `scripts/dream_gemini.py` | Gemini-based dream generation |
| `scripts/image_metadata.py` | Image metadata utilities |

## Tools

| Tool | Purpose |
|------|---------|
| `tools/scrape_inaturalist_guide.py` | Scrape iNaturalist guide taxa with provenance tracking (`--corpus` flag for multi-dataset) |
| `tools/qc_approve.py` | Batch approve/reject iNat images (`--corpus` + `--rejects-file` for scoped review) |
| `tools/salish-sea-species.tsv` | 37 curated Salish Sea species (full marine) |
| `tools/species-fish.tsv` | 13 bony fish species for fish-model |
| `tools/species-whales.tsv` | 6 cetaceans for whale-model |
| `tools/species-birds.tsv` | 10 coastal seabirds for bird-model |

Scripts use TouchDesigner's Python API (`op()`, `noiseTOP`, `edgeTOP`, etc.). To test, paste into TouchDesigner's Textport or run via the TouchDesigner MCP.

## TouchDesigner Integration

This project uses the TouchDesigner MCP. When TD is running with the MCP component active,
you can directly create and modify nodes, run Python scripts, and query the project state.

Key TD tools: `create_td_node`, `get_td_nodes`, `execute_python_script`, `update_td_node_parameters`

## Technical Stack

### TouchDesigner (Production)
- TouchDesigner with MCP integration for AI-assisted development
- Python scripts for procedural generation (in `scripts/`)
- Kinect presence detection, projection mapping
- Resolume Arena for projection mapping/video mixing
- StreamDiffusion TOX for real-time AI visuals
- Sound: Ableton Live + Max for Live biosonification
- Pravin's stack: TD, Unity, VVVV, Stable Diffusion, Ableton/Max for Live

### Web (Prototyping)
- Three.js + WebGL with custom GLSL shaders
- Vite dev server with hot reload
- GitHub Pages: https://darrenzal.github.io/salish-sea-dreaming/
- 50,000 particle system with bioluminescence
- **Key files:** `web/src/main.js`, `web/src/shaders/particle.vert/.frag`, `web/src/config.js`

### Infrastructure
- TELUS H200 GPUs (Sovereign AI Factory) — Carol Anne has access
- Personal KOI backend for knowledge graph integration

## Key Concepts

### The Five Threads
| Thread | Represents | Data |
|--------|-----------|------|
| Salmon | Migration, cycles, return | Run data, habitat health |
| Camas | Restoration, community care | Meadow restoration |
| Herring | Foundation species | Water quality, fishery tension |
| Cedar | Long time, patience | Forest health, carbon |
| Orca | Family, grief, resilience | J/K/L pod population |

### Installation Concepts (simplest → full vision)
1. **"The Watercolor Dreaming"** — Briony's watercolors + Kinect + Stable Diffusion
2. **"The Listening Room"** — Room-scale projection, collective stillness
3. **"Speaking / Listening Stations"** — Visitors speak, AI responds with dreamscape
4. **"The Five Threads"** — Five data-driven projected forms
5. **"The Dreaming Mind"** — Full cybernetic nervous system (north star)

### Kwaxala Model
Herring worth more swimming — forage fish ecosystem accounting. Heiltsuk / Wuikinuxv nations challenged DFO and took over their own stock assessment. DFO 1953 baseline was already a terrible herring year; Indigenous knowledge documents vastly different historical reality.

### T'lep — The Octopus Intelligence
From potlatch ceremony — 9 brains, decentralized intelligence, witness and executive function. Cultural values embedded in system architecture.

## Style

- Favor **emergent, organic behaviors** over mechanical precision
- Think: plankton, currents, bioluminescence, flocking fish, kelp forests, mycelium
- **Stillness should be rewarded** — deeper revelation with sustained attention
- Colors: deep ocean blues, bioluminescent cyans/greens, warm salmon pinks
- Movement should feel like underwater currents, not mechanical animation
- Keep visualizations nature-focused

## Obsidian Knowledge Base

- **Project note:** `~/Documents/Notes/Projects/The Salish Sea Dreaming.md`
- **Signal chats:** `M37 Salish Sea Dreaming Chat.md`, `M37 Dreaming Network Member Chat.md`, `Intelligent Media Lab Chat.md`, `Prav Chat.md`

Use MCP vault tools (`vault_read_note`, `vault_search_notes`) to access these.

## Shared Resources

- **Mind Map:** https://coggle.it/diagram/aW01lIKXUtVgH4cW/t/wen%2Cn%C3%A1%2Cnec
- **Shared Drive:** https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr
- **Art Show:** https://saltspringarts.com/spring-art-show/

## Quick Start

```bash
# Web prototype
cd web && npm install && npm run dev  # http://localhost:3000

# Scrape a species corpus (e.g., whales)
python tools/scrape_inaturalist_guide.py \
  --guide 0 --species-list tools/species-whales.tsv \
  --per-taxon 50 --size large \
  --output ./images/whales-raw --provenance --corpus whale-model --license-filter

# QC review + approve (scoped to corpus)
python tools/qc_approve.py --corpus whale-model \
  --rejects-file training-data/review/rejects-whale-model.csv --dry-run
python tools/qc_approve.py --corpus whale-model \
  --rejects-file training-data/review/rejects-whale-model.csv --apply

# Build corpus from approved images
python scripts/prep_training_data.py --resolution 512 --corpus whale-model

# Knowledge graph
curl http://localhost:8351/health  # check if KOI backend running
# If not: ~/.config/personal-koi/start.sh
```

## Session History

| Session ID | Date | Scope | Key Work |
|------------|------|-------|----------|
| — | 2026-02-08 | Scripts | Dream transforms, video loops, mycelium/psychedelic TD scripts |
| — | 2026-03-02 | Docs + tools | One-pager for Raf; iNat scraper built; repo merge (Pascal→kebab); Autolume/TELUS plan |
| — | 2026-03-06 | Research | "The Living Salish Sea" Report II → vault + salishsee.life; 27 entities ingested |
| — | 2026-03-09 | Training data | Briony crop pipeline + 54-image corpus; iNat scrape (739, 37sp); QC (539 approved); marine-photo-base built; TELUS smoke test |
| — | 2026-03-12 | Arshia + Prav docs | Training guidance integrated (kimg=1000+, LoRA alt); Prav's 3 PDFs added; exhibition date fixed |
| `93132576` | 2026-03-13 | TELUS ops | Base 200 kimg downloaded + uploaded to Drive; resume to kimg=1000 kicked off (run 00012) |
| `f85e12c9` | 2026-03-13 | Pivot | Arshia: dataset too diverse → stopped training, downloaded 320 kimg checkpoints, new direction: LoRA→synthetic→GAN |
| — | 2026-03-14 | Meeting prep | Multi-layer strategy doc, 5 parallel tracks, gap analysis, operational stability plan |
| `f024a856` | 2026-03-14 | Dataset pipeline | Three-dataset strategy: multi-corpus scraper/qc/prep pipeline; fish/whale/bird TSVs; fish corpus assembled (174); supplement scraped (207 unique herring+salmon); dedupe fix |
| `ba05bf17` | 2026-03-15–17 | License → training → vision | CC-safe pipeline + 3 corpora scraped, fish QC (378 approved), TELUS training live (353 sec/kimg), holonic morphing vision documented, docs reorganized, Drive updated |
| — | 2026-03-18 | Briony LoRA | LoRA trained (22 images, rank 16, 1000 steps), eval confirmed style transfer. img2img integration tested on 20 GAN frames × 5 strengths — sweet spot s0.35–0.45, avg 0.97s/frame. Temporal coherence stable. HTML comparison viewer created. |
| — | 2026-03-18–19 | RTX 3090 setup | Desktop purchased ($1,950 CAD). 6/8 phases via SSH: GPU verified, VS Build Tools, Miniconda3, Autolume env (PyTorch 2.8+cu128), TouchDiffusion cloned + Briony LoRA merged into SD-Turbo. Remaining: TD 2025 GUI install, webui.bat first run, NDI networking, integration test. |
| — | 2026-03-19 | Training monitor + overview | Fish model at kimg 376/1000 (37.6%), kimg 200 fakes grid shows healthy fish shape emergence. PKL downloaded. Comprehensive project overview synthesized for creative jam. |
