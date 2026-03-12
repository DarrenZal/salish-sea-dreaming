# Salish Sea Dreaming

> *"We are the Salish Sea, dreaming itself awake."*

Interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself.

**Target:** Salt Spring Spring Art Show, April 2026.

## Current Status

**Date:** 2026-03-11
**Status:** Both training corpora built. Ready for base model training on TELUS H200.

**What's Done:**
- Briony fine-tune corpus: 54 images at 512x512 (expanded from marine-only to all ecological watercolors), provenance tracked, committed
- Pipeline fix: crop_box now correctly applied in prep_training_data.py (was being ignored)
- Marine photo base corpus: 539 images at 512x512 (scraped 740, QC'd down to 539)
- TELUS H200 smoke test: pipeline validated (25 kimg on Briony, FID 474.6→502.8), PKLs in `models/briony-test-run/`
- Full QC pipeline: `qc_approve.py`, `rejects.csv` (201 rejects), 37 species contact sheets
- iNat scraper enhanced with `--species-list`, `--per-taxon`, `--provenance` flags

**What's Left:**
1. Upload `marine-photo-base/` to TELUS → train base model (kimg=200: ~25 hrs in pure-Python fallback, ~2-3 hrs if compilers installed)
2. Fine-tune on Briony corpus from base checkpoint (`--resume`)
3. Test checkpoint in AutoLume with Prav
4. David Denning photos — if received, create `david-v1.pkl` fine-tune

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
| **Eve (Maya)** | Data scientist | Regen Commons steward |
| **Brad Necyk** | Artist, researcher | Latent space concepts, studio at Cobble Hill |

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
| `tools/scrape_inaturalist_guide.py` | Scrape iNaturalist guide taxa with provenance tracking |
| `tools/qc_approve.py` | Batch approve/reject iNat images from QC review reject list |
| `tools/salish-sea-species.tsv` | 37 curated Salish Sea species for iNat scraping |

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
- StreamDiffusion TOX for real-time AI visuals
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

# iNaturalist scraper (species list + provenance tracking)
python tools/scrape_inaturalist_guide.py \
  --species-list tools/salish-sea-species.tsv \
  --per-taxon 20 --size large \
  --output ./images/marine-base-raw --provenance --dry-run

# QC review + approve
python tools/qc_approve.py --dry-run   # preview
python tools/qc_approve.py --apply     # writes .bak backup, then updates provenance.csv

# Build training corpora from approved images
python scripts/prep_training_data.py --resolution 512

# Knowledge graph
curl http://localhost:8351/health  # check if KOI backend running
# If not: ~/.config/personal-koi/start.sh
```

## Session History

| Date | Scope | Key Work |
|------|-------|----------|
| 2026-02-08 | Scripts | Dream transformations (dream_briony.py), video loops, mycelium/psychedelic TD scripts |
| 2026-02-13 | Visual sprint | Animation research, prototype review |
| 2026-03-02 | Docs + tools | One-pager for Raf finalized; iNaturalist scraper built (128 marine taxa); Proton Drive shared with Prav; coordination drafts written; Autolume/GAN + TELUS GPU plan outlined |
| 2026-03-02 | Repo merge | Consolidated SalishSeaDreaming (Pascal) → salish-sea-dreaming (kebab); scripts/, VisualArt/ (git-lfs), docs migrated |
| 2026-03-06 | Research + Octo | Deep research prompt + Report II ("The Living Salish Sea") to vault + Octo knowledge garden (salishsee.life); 27 entities ingested; fixed Octo chat widget (model config + timeout); salishsee.life now canonical URL |
| 2026-03-09 | Training data (`364134a6`) | Briony crop pipeline + 36-image corpus; iNat scrape (740, 37 species); QC review (539 approved, 201 rejected); marine-photo-base built (539 at 512x512); TELUS smoke test (FID 474.6→502.8 — expected with only 36 images, pure-Python fallback); artifacts downloaded; docs updated; committed `aef147c` |
| 2026-03-11 | Briony corpus expansion | Expanded Briony corpus from 36 to 54 images — broadened scope from marine-only to all ecological watercolors (salmon-forest, camas, landscapes); fixed crop_box bug in prep_training_data.py (crop coordinates were being ignored) |
