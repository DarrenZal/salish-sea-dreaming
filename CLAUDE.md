# Salish Sea Dreaming

> *"We are the Salish Sea, dreaming itself awake."*

Interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself.

**Target:** Salt Spring Spring Art Show — "Digital Ecologies: Bridging Nature and Technology" at Mahon Hall, April 10–26, 2026.

## Current Status

**Date:** 2026-03-31
**Status:** 10 days to exhibition opening. StreamDiffusion working at 30fps in TD 2025 (Leo session March 28). Shawn posted 16 style-transfer files (video 48 = curator hero). Curator needs to see production quality for space allocation. Briony LoRA expression in StreamDiffusion unverified — trigger token `brionypenn` may not be in use. Moonfish high-res from Deirdre expected imminently. Prav available Fri-Sun at studio for production push.

**License Policy:** COMMERCIAL USE — CC0, CC BY, CC BY-SA only. Artist fee at exhibition = commercial under CC terms. CC BY-NC excluded. Collaborator materials (Moonfish, Denning) under `collaborator permission` — see `training-data/licenses-collaborators.md`. Full credits: `docs/credits-attribution.md`.

**What's Done:**
- **StreamDiffusion 30fps in TD** (March 28): Leo + Prav session — real-time style transfer working. Prompt A/B blending system designed (crossfade weights via Python + CHOP). Poetry DATs drafted for prompt-driven dreaming. StreamDiffusionTD_0.3.0.tox shared.
- **Shawn's ComfyUI/RAVE handoff** (March 30): 16 files on shared Drive (7 stills, 8 videos). Video 48 = hero for curator demo. ComfyUI pipeline warm on Legion. Ready to process Moonfish high-res on arrival.
- **Moonfish + Denning integration** (March 26-27): 13 Moonfish videos (4.7 GB) and David Denning PPT photos received via Prav. 8 hero segments identified, subclips trimmed. 14 Denning high-res photos curated. Exhibition strategy: video as primary exhibition material. Shotlist: `docs/moonfish-shotlist.md`.
- **Intent field concept** (March 30): `docs/intent-field-installation.md` — visitors voice their care, voices become herring via Boids algorithm, collective intent forms schools over 16 exhibition days. Connects to Prav's vision of visitors becoming part of the dreaming.
- **Render packet sent** (March 27): 3 hero subclips (H1, H2, H5) on Drive for Briony LoRA tests. Deirdre request with timecodes for high-res clips.
- **Corpus QC'd and finalized** (March 25): 1,254 images, 50 species. All rejects tracked in `training-data/review/rejects-*.csv`.
- **Fish model kimg 1000 complete** (March 23): Fallback only. TELUS free for dreaming model.
- Prior work: RTX 3090 desktop (6/8 phases), Briony LoRA v1 (22 images, rank 16), LoRA v2 config ready, all datasets on Drive.

**What's Left:**
1. **Verify Briony LoRA in StreamDiffusion** — A/B test with `brionypenn` trigger token. If no difference, LoRA isn't loading or needs more steps.
2. **Curator projection test** — Prav planning for Tuesday or Saturday. Video 48 as hero demo.
3. **Moonfish high-res from Deirdre** — process through ComfyUI/RAVE pipeline on arrival.
4. **Technique lock** — Real-time: StreamDiffusion + LoRA. Pre-rendered: ComfyUI + LoRA. Fallback: raw Moonfish footage.
5. **OSC → TD integration** — Shawn built engine, needs walkthrough with Prav. Poetry DATs + ecological data driving the dream field.
6. **Credits/attribution confirmations** — Written permission needed from Moonfish Media and David Denning. See `docs/credits-attribution.md`.
7. **Weekend production push** (Fri-Sun at Prav's studio) — lock exhibition-ready sequences.
8. **Track B (parallel):** TELUS dreaming model training (~1,500 images, 6-7 days).
9. **Website** — Landing page at SalishSeaDreaming.MOVE37XR.org (or standalone). Phase 1 = landing page, future = interactive voice/image input.

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
| `c2152579` | 2026-03-19–22 | Exhibition strategy + corpus | Multi-wall spatial composition, ecological interface corpus design, 778 intertidal scraped, QC review app deployed, LoRA v2 prep. Fish model kimg 200→944. |
| `c2152579` | 2026-03-24–25 | Dreaming corpus assembly | Assembled 1,600-image corpus (57 species) from iNat + Openverse. Built Openverse scraper. Agent QC pipeline (pre-filter → user verify). Expanded v1: birds + bears + orca video frames. Balance script (interface-weighted). Server-side QC persistence. Animation techniques (AnimateDiff, prompt travel). Signal update sent. Corpus in team review. |
| `5d61ad00` | 2026-03-25 | QC + finalization | Manual QC of all 50 species (1,600→1,254 images, 478 rejects). Fixed QC app species parsing bug (hex/UUID IDs). Supplement scrape for 4 thin species (+132 images: GPO, herring spawn, murrelet, orca). Corpus finalized and synced. Signal update drafted for team review + David/Moonfish image ask. |
| `4337d388` | 2026-03-26–27 | Moonfish + Denning integration | Strategic pivot: video as primary exhibition material, not just corpus input. 8 hero segments subclipped, 3 uploaded to Drive for Prav. 416 underwater frames extracted. Shotlist + render packet sent to Prav. Two-track plan: Track A (exhibition lock by April 1) + Track B (TELUS training, subordinate). New scripts: extract_video_frames.py, contact_sheet.py. |
