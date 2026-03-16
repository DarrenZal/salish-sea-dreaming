# Salish Sea Dreaming

> *"We are the Salish Sea, dreaming itself awake."*

Interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself.

**Target:** Salt Spring Spring Art Show — "Digital Ecologies: Bridging Nature and Technology" at Mahon Hall, April 10–26, 2026.

## Current Status

**Date:** 2026-03-15
**Status:** CC-safe corpus rebuild in progress. All three corpora scraping (commercial-safe licenses only). Legacy fish corpus archived.

**License Policy:** COMMERCIAL USE — CC0, CC BY, CC BY-SA only. Artist fee at exhibition = commercial under CC terms. CC BY-NC excluded.

**What's Done:**
- Base model v1 (200 kimg) + resume (320 kimg) — checkpoints in `models/`, uploaded to Drive; **PKL loads in Autolume CONFIRMED** (Prav tested, NDI→TD working)
- Team pivot (2026-03-13): Arshia flagged base dataset too diverse → three focused species models (Fish, Whales, Birds) as separate Autolume instances mixed via NDI in TouchDesigner
- Multi-corpus pipeline built: `scraper`, `qc_approve`, `prep_training_data` all have `--corpus` flag + `--license-filter` on scraper; new minimums (fish/whale/bird: 150 each); qc_approve has `--rejects-file` scoping
- `--license-filter` added to scraper: CC0/CC BY/CC BY-SA allowlist, filters before download (no wasted bandwidth)
- `scripts/backfill_licenses.py` created: queries iNat API to fill license column, optionally purges non-safe rows
- Species TSV files: `tools/species-fish.tsv` (13 bony fish — dropped Longfin Smelt/Surf Smelt/Yelloweye Rockfish: <7 CC-safe on iNat), `tools/species-whales.tsv` (6 cetaceans), `tools/species-birds.tsv` (10 seabirds). All taxon_ids populated.
- Legacy fish corpus archived: `training-data/fish-model-legacy-unsafe-20260315/` (305 images, only 21 CC-safe)
- Backfill + purge run on fish-model provenance: 96 non-CC-safe rows marked `approved_for_training=no`
- CC-safe supply assessed via dry-runs: Fish=~800, Whale=728, Bird=1729 (all well above 150 threshold)
- All three CC-safe scrapes launched (2026-03-15): downloading to `images/fish-commercial-raw/`, `images/whales-raw/`, `images/birds-raw/`
- Meeting prep doc: `docs/2026-03-14-meeting-prep.md` — 5 parallel tracks, operational stability plan

**What's Left:**
1. **QC all three corpora** — review raw images in Finder, create per-corpus rejects files, run `qc_approve --corpus <name> --rejects-file ...`
2. **Prep all three corpora** — `prep_training_data.py --resolution 512 --corpus <name>`
3. **Signal Prav** about his 400-500 image fish dataset — may provide higher-quality underwater shots
4. **Contact Moonfish Media** for explicit permission on herring footage (CC-safe iNat herring = 47, want more)
5. **TELUS go/no-go** — check compiler issue; if go, kick off Fish training first
6. **Multi-instance burn-in** — test 3 Autolume + NDI + TD on Prav's hardware before committing to training
7. **Operational stability** — burn-in test 8+ hrs, daily restart checklist, Resolume fallback
8. **Sound owner decision** — name, minimum spec, timeline
9. Darren away March 20–28 — handoff deliverables defined in meeting prep doc

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
| `tools/species-fish.tsv` | 16 bony fish species for fish-model |
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
  --output ./images/whales-raw --provenance --corpus whale-model

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
