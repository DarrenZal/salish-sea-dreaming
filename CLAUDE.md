<!-- workstream: ssd -->

# Salish Sea Dreaming

> *"We are the Salish Sea, dreaming itself awake."*

> 🌅 **Fresh session start:** run **`/whats-next`** for ranked priorities. CLAUDE.md (this file) auto-loads — no extra command needed. For orchestrator-mode bootstrap behavior, see **Session Start Protocol** below.

## Session Start Protocol

When a fresh session opens here, do these in order before responding to anything else:

1. **Read the canonical plan in full:** `~/.claude/plans/ok-so-i-polymorphic-melody.md` (14-section strategic plan; lint-clean; 3 Codex review rounds resolved). Don't paraphrase from memory — the plan is the source of truth for Phase 2.
2. **Status-check overnight surfaces** in parallel:
   - `ls -lt ~/Documents/Notes/Signal*Dreaming*Chat.md ~/Documents/Notes/M37*Salish*Sea*Dreaming*Chat.md ~/Documents/Notes/Signal*Salish*Sea*Dreaming*Tactical*Chat.md | head -5` — any modified in last 24h means new Signal activity worth reading
   - `ls ~/projects/salish-sea-dreaming/docs/next-iteration/_research/prompt-*__*.md 2>/dev/null` — deep-research outputs returned?
   - Remind operator to check Proton inbox for Prav's reply on the venue thread (subject `Re: 720 dpi projectors in the Hubble Space`) — Claude can't read Proton directly
3. **Run `/whats-next`** for ranked priorities (reads this file + plan + tasks).
4. **Triage today's top 3 actions** with decision gates + ownership (Darren / Prav / Austin / Carol Anne / Natalia).
5. **Frame the session as orchestrator** — high-level coordination, delegate to sub-agents only when operator asks or work is genuinely independent (parallel web research, codebase exploration). Direct tool calls for everything else. Per logged pattern 2026-05-13: don't auto-spawn sub-agents after a velocity push from the operator.
6. **Honor the project memory entries** — esp. `feedback_exploration_over_lockin.md`, `feedback_visitor_interactivity_primary.md`, `feedback_austin_no_ai_generation.md`, `feedback_ssd_email_address_per_thread.md` (in `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/`). These are user-posture corrections from prior sessions and shape behavior here.

If today's CLAUDE.md "Date" is more than ~3 days stale, flag that a fresh `/end` is needed soon.

Interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself.

**Target:** Salt Spring Spring Art Show — "Digital Ecologies: Bridging Nature and Technology" at Mahon Hall, April 10–26, 2026.

## 3090 Remote Access (SSH)

The 3090 is now at **Darren's house** (moved from Prav's studio, 108 Fraser Rd; staying for a while). Accessible via SSH three ways:

**Direct LAN (same house):**
```bash
ssh windows-desktop          # direct, 192.168.1.68 (DHCP, as of 2026-06-10)
```

**Tailscale (stable, survives IP changes):**
```bash
ssh windows-desktop-tailscale   # 100.91.172.10
```

**From anywhere (reverse tunnel):**
```bash
ssh windows-desktop-remote   # via reverse tunnel through poly (37.27.48.12:2222)
```

**How it works:** The 3090 runs a persistent `SSD-SSH-Tunnel` Task Scheduler task that keeps an outbound SSH tunnel open to poly. The tunnel forwards `poly:2222 → 3090:22`. The Mac's `~/.ssh/config` has `windows-desktop-remote` configured with `ProxyCommand ssh -W 127.0.0.1:2222 poly@37.27.48.12`.

**If the remote tunnel is down** (tunnel task not running after reboot before auto-login, etc.):
- Connect via local network: `ssh windows-desktop`
- Or restart the task: `schtasks /run /tn "SSD-SSH-Tunnel"`

**Deploying updated scripts to 3090:**
```bash
# Scripts live at C:\Users\user\ (not a git repo — deploy via scp)
scp scripts/td_relay.py windows-desktop:C:/Users/user/td_relay.py
scp scripts/gallery_audio.py windows-desktop:C:/Users/user/gallery_audio.py
```

**Task Scheduler tasks on 3090** (all trigger on logon, run as admin):
- `SSD-SSH-Tunnel` — reverse SSH tunnel to poly (remote access)
- `SSD-TouchDesigner` — launches `SSD_gallery_2026-04-06_0321.13.toe` after 30s delay
- `SSD-TD-Watchdog` — restarts TD if process dies (checks every 2 min)

**Gallery server** runs on poly (`37.27.48.12:9000`), NOT on the 3090. The 3090's relay polls it.

## Current Status

> ✅ **Consent thread CLOSED (2026-06-10):** post-show visitor-dream archival executed live on `salishseadreaming.art` (ssd-v5/poly:9004). Added `ongoing` window, flipped default to it, seeded 12 authored dreams, archived the 63 non-consented IMPACT dreams (retained in DB, no longer served), published the 3-dream consented snapshot. End state: default `/cloud` → `ongoing` (12); `impact-2026` → 3 consented; 349 rows, nothing deleted. Details + deployment notes in **`TODO.md`**.

**Date:** 2026-06-10
**Status:** **Between installations — IMPACT 2026 over (May 27–28, HR MacMillan Space Centre; GREEN show-morning call, 188/196 probe sweep, no P0 visitor-blockers).** 3090 quiesced to R&D idle. Next target: **MOVE37XR Dome Theatre, Oct 2026** (then DEVCON ETH Mumbai, Nov 2026).

**📋 Read first:** `~/.claude/plans/ok-so-i-polymorphic-melody.md` (14-section Phase 2 plan) + `docs/space-center/debrief-impact-2026.md` + `docs/space-center/next-installation-improvements.md`. `docs/space-center/` holds Phase 2 working docs.

**Venue (past):** Indigenomics IMPACT = Space Centre, 1100 Chestnut St, Vancouver. **License:** CC0 / CC BY / CC BY-SA only.

**What's Done (consolidation session, 2026-06-10):**
- **3090 → R&D idle.** Stopped + disabled the live show stack (`SSD-Autolume`/`-Watchdog`, `SSD-Relay`, `SSD-TD-Watchdog`, `SSD-TouchDesigner`) + killed leftover processes; only `SSD-SSH-Tunnel` + `SSD-Tunnel-Watchdog` remain. SSH preserved.
- **IMPACT production stack archived** → `installation-archive/impact-2026/` (production `SSD-exhibition.toe` + 27 task XMLs + 19 show scripts + README with re-enable procedure + quirks). Mirrors the April `installation-archive/` pattern.
- **Git consolidated + pushed** (`cd4995a..da67904`): 5 commits, 493 files / +166K lines. Hardened `.gitignore` (excludes `bob-turner-corpus/`, `td/`, `track2-deterministic/` renders, sweeps, `.tmp-*`); committed the 182-script R&D corpus + ~150 research docs + the test suite.
- **Show learnings harvested** → `debrief-impact-2026.md` (what worked / what failed / quirks / collaborator feedback) + `next-installation-improvements.md` (MOVE37XR pre-work). Durable lessons already in memory from the May sprint.

**3090 location:** now at **Darren's house** (192.168.1.68 LAN / Tailscale 100.91.172.10 / poly reverse tunnel). Was at Pravin's studio. Will stay at Darren's for a while.

**Prior session work (compressed):** SSD Meeting 2 + 8 koi-backend fixes (`ebcddf4d`); process-note completion gate (`4a9a7b17`); Verification gate v1 + Pravin call (`8695b704`); Phase 2 sprint plan + v2 LoRA + Track 2 morph engine (`63a5fec1`); Phase 2 plan + proton-send (`64276b6e`); April post-exhibition archive (`156cd786`).

**Prior production stack (intact, dormant — re-enable via `installation-archive/impact-2026/README.md`):** Autolume 120 kimg + StreamDiffusion sd-turbo + Resolume + visitor app + auto-heal + SSH tunnel. **Briony layer + style-transfer-of-Austin's-work both DROPPED** (Phase 2 = Coast Salish primitives Crescent/Circle/Trigon).

**What's Left (priority-ordered):**
1. **Visitor-dream consent archival** (the open thread above) — sequenced in Phase 7 of `~/.claude/plans/ok-so-the-shw-snuggly-tide.md`; fires on operator go (needs seed-curation).
2. **MOVE37XR Oct prep** — work the `next-installation-improvements.md` list: finish the `_label_clusters` TELUS port, persist the NDI config, fix the Autolume sweep recording bug, build the 4K→equirectangular dome pipeline, adopt visitor-perspective test discipline.
3. **`_label_clusters` 10-line fix** — swap `openai_client` → `chat_client` in `gallery_server.py:1603` (removes 401 log noise).
4. **Optional 3090 disk free-up** (~200 GB) — candidates in `docs/space-center/3090-disk-archive-candidates.md`; deferred pending an external destination.
5. **Arshia follow-up** — positive post-show note (Signal, May 28); reconnect before MOVE37XR given the Autolume lineage.

**Open questions:** "Pearl" vs "spindle whorl" framing for Austin's vision (Susan Point's lineage uses spindle whorl — Pravin gating). Per `feedback_austin_consent_trust_floor.md`: per-output sign-off is the floor.

## Briony Style Transfer — Options for StreamDiffusion

**Context:** SD-Turbo is architecturally incompatible with SD 1.5 LoRAs (confirmed GitHub issue #182). The `brionypenn` trigger in prompts currently does nothing — no style model is active. The v5 baked model (sd-turbo fine-tune, 5000 steps) produces abstract blobs. The LoRA at 30 steps on TELUS H200 produces excellent results (Prav: "AMAZING", March 31) — that's the proven path for offline rendering.

**Files on 3090 Desktop:**
- `briony_watercolor_sdturbo.safetensors` (13MB) — SD-Turbo specific LoRA, trained March 28
- `briony_watercolor_sdturbo_kohya.safetensors` (13MB) — alternate SD-Turbo LoRA (kohya trainer)
- `briony_watercolor_v1.safetensors` (38MB) — SD 1.5 LoRA, rank 16, 1000 steps

**Option 0 — SD-Turbo LoRA (try first, ~30 min)**
Already on Desktop. Load `briony_watercolor_sdturbo.safetensors` via SDTD LoRA Loader page. Keep sd-turbo as base model. This LoRA was created March 28 (same day as "30fps in TD" milestone — may have been what was running). Set weight 0.7–1.0.
- Risk: Unclear if this LoRA was ever validated; unknown training quality
- If it works: easiest win

**Option 1 — IP-Adapter with Briony painting reference (~1 hour)**
SDTD has IP-Adapter built-in (`Ipadapterenable`, `Ipadapterscale`, `Ipadapterimage`). Load a Briony watercolor into a MovieFileIn TOP in TD, point IP-Adapter at it, set scale 0.5–0.8. Works with sd-turbo at 4 steps, no training needed.
- Risk: IP-Adapter + sd-turbo untested; style guidance may be weak at 4 steps
- Briony reference images: `briony-lora/*.png` (copy to 3090)

**Option 2 — SD 1.5 + LCM + Briony LoRA (~4 hours)**
Switch `Modelid` to `runwayml/stable-diffusion-v1-5` (download ~4GB to 3090). Load `briony_watercolor_v1.safetensors` via LoRA Loader. Keep `Scheduler: lcm`, run at 8 steps. Expected ~12–18fps. LoRA style visible at 8 steps per compare-v2.html.
- Risk: fps may feel choppy; need to download SD 1.5 base model
- Briony LoRA file: `C:\Users\user\Desktop\briony_watercolor_v1.safetensors`

**Option 3 — Pre-rendered + Resolume (zero risk fallback)**
30-step TELUS renders (ControlNet + LoRA) already produced exhibition-quality videos. Play styled clips as video layers in Resolume. No live diffusion dependency. This was the March 31 decision. Hero videos: H1–H6 in shared Drive.
- Use this if Options 0–2 fail by April 9 morning

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
| `af3eb5d9` | 2026-04-22 | ops | Silence false-positive Telegram alert: disabled `audio_monitor` health probe check in `health_probe.ps1` (3090 has no mic; `audio_silent` was already disabled Apr 20 for same reason). Deployed to 3090 via scp, committed + pushed. |
| `f82e40c5` | 2026-04-23 | TD VJ prep + gallery fixes | **Pivot day per Prav's Signal directive.** (A) Gallery: hardened prompt filter (regex + gpt-4.1-mini moderation) + new co-dream label deployed to poly. (B) Three audio-reactive TD scenes built live via TD MCP: `salish_audio` (mycelium, hand-conducted), `salish_prisms` (128 species cards, mic-reactive), `salish_dreamworld` (live /dreams/3d fetch with music-driven unity→cluster→individual bezier breathing). (C) MediaPipe hand tracking integrated via `hand_pos` Constant CHOP bridge. (D) Bundle (184MB .toe + scripts + species images + README) uploaded to Proton Drive, link sent to Prav on Signal. Key TD gotchas discovered and documented: `instancing` (not `instanceactive`) is master toggle; LFO CHOP `rate` unreliable — use `absTime.seconds`; webclientDAT response format varies; per-instance textures need `instancetexs` TOPMulti. |
| `156cd786` | 2026-05-03 | ops + archive | **Post-exhibition dev-mode return.** Tunneled to 3090 via WireGuard (poly tunnel + Tailscale both down). Pulled full installation stack into `installation-archive/` (96 files, 6.1MB): 64 scripts from `C:\Users\user\` + 23 `SSD-*` task XML exports + 8 `.toe` lineage tips. Disabled 21 of 23 SSD-* tasks; kept `SSD-SSH-Tunnel` + `SSD-Tunnel-Watchdog` for remote access. Killed running watchdog instances. Commit `ba94a83` pushed to GitHub on `mudra-living-intelligence-2026-04-26` (with upstream tracking). Signal DM to Prav (ts `1777868635067`) confirming dev-mode return. **Discovered:** macOS scp silently truncates `.toe` files at 200KB; `scp -O` (legacy protocol) is the workaround. |
| `240a8327` | 2026-05-04 | Phase 2 planning + Austin/INDIGITAL prep | Researched Austin Harry / INDIGITAL (Sḵwx̱wú7mesh Wolf + Nam̓gis Thunderbird; Xwalacktun's son; Salish Spirit @ VanLive! = closest SSD precedent). Pulled 127 portfolio images into gitignored `austin-reference/` via new `tools/scrape_indigital.py`. Produced 4 docs under `docs/next-iteration/`: research dossier, Austin brief v0.1, technical roadmap (5 tracks), venue strategy (Indigenomics May → MOVE37XR Oct → DEVCON Nov → Life at Center 2027). Codex `/review-plan` round 1 applied. Commit `13699ed` pushed; Signal sent to Prav (ts `1777961376697`) with 3 open decisions. |
| `91bcf2a6` | 2026-05-11 | Meeting-notes batch processing | Fully processed three SSD meeting notes (5/5 main, 5/5 Austin onboarding, 5/8 sprint planning): populated YAML + structured bodies; created 11 new entity vault notes (Austin Harry, Xwalacktun, INDIGITAL, Mohawk Nation, HR MacMillan Space Center, NewTech, Coast Salish Design, Sandra Semchuk, Chris Jordan, Institute for Global Health Research, Style Transfer, Spout, Berlin); ingested entities to KOI via `vault_ingest_extraction`; applied wikilinks across bodies; overrode 7 bad backend merges (Austin→Austin via Guard A, Sonia Su→Sen via B, Indigenomics Impact→Indigenomics AI via E ×2, Chris Jordan→Chris Krug via B); created 28 task files in `Tasks/` + registered all with backend; auto-closed 10 stale SSD tasks with quoted same-day evidence; propagated `mentionedIn` backlinks to 30 entity notes; captured 20 facts to KOI knowledge graph in 3 episodes; logged 7 bad merges + 2 patterns + 2 tooling issues to `Meta/Entity Resolution Issues.md`. No code changes to repo. |
| `64276b6e` | 2026-05-11 → 13 | Phase 2 plan + Phase 0 kickoff + proton-send root-cause fix | Built comprehensive 14-section Phase 2 plan (`~/.claude/plans/ok-so-i-polymorphic-melody.md`) through 3 Codex rounds. Resolved Indigenomics IMPACT = Space Centre show. 5 deep-research prompts paste-ready. Phase 0 scaffolding in `docs/space-center/`. Built `proton-send` skill wrapping local Proton Bridge SMTP. 9 memory entries. Plan corrections: visitor-app + MediaPipe = PRIMARY, 5090 active R&D track. |
| `63a5fec1` | 2026-05-13 eve | Phase 2 tooling + IMPACT framing correction | **Major framing correction** verified against IndigenomicsAI meeting notes (Apr 17–May 13): IMPACT 2026 = May 27–28 at HR MacMillan Space Centre; two surfaces / one event arc (Hubble = SSD installation ~May 25, Dome = Living Intelligence cosmic-journey May 27–28); survey is Whova-backed → screen, not Dome. Kurt reply: Dan owns Dome specs (call queued). Built operator-ready v2 LoRA pipeline: `austin_v2_pipeline.py` (12-stage orchestrator), `eval_lora.py` (parameterized), `--root` flag; cold-start rehearsal passed. Built Track 2 deterministic morph engine dry run (`morph_engine.py` w/ svgpathtools + approval gate, `compute_svg_bbox.py`, `compose_pearl_dry_run.py`). Operational handoff: John pack zip + drafts, 3 public-language drafts `[PENDING AUSTIN REVIEW]`, consistency audit, `fact-checks-2026-05-13.md` (⚠️ Autolume NDI not in upstream). Parallel-session work also landed: live-feed OSC bridge, Resolume scaffold/validator, temporal-style runner, caption validator, Dome asset generator, `CURRENT_STATE.md` index. Memory: `feedback_dont_overshare_when_tunnel_unblocks.md`. No git commits (per user convention). |
| `f3c12288` | 2026-05-14 | vault tooling fix (not SSD repo) | **QuickAdd "New Meeting" dedup + quote-strip fix** in Obsidian vault. Two root causes: (1) duplicate project notes — `Projects/Salish Sea Dreaming.md` is a 2026-05-01 stub of canonical `Projects/The Salish Sea Dreaming.md`; (2) `Templates/newmeetingmacro.js` `getAllProjects()` didn't strip YAML quotes from `name:`, so the canonical note's quoted name produced a literal-quote folder path → "neither lands in the folder." Fixes: macro now strips quotes, skips `quickaddExclude: true` notes, dedupes by name, skips `CLAUDE.md`, sorts; stub note marked `quickaddExclude: true` (kept for ~90 backlinks). Patched 2026-05-14 SSD meeting note (project/title/transcriptFile), renamed it + transcript to "The …" form, repointed 7 `Tasks/2026-05-14-*` backlinks. Committed to vault git (`911fd66`) — vault has **no git remote**, so no push possible. Logged file-format tooling issue. |
| `8695b704` | 2026-05-16 | meeting processing + verification gate v1 | **2026-05-16 Pravin Signal call fully processed** (transcript + meeting note + 14 tasks + 24 entity-note backlinks + 15 KG facts; 7 Guard-A overrides logged). **Main-thread email sent** to John/Dan/Austin/Natalia with Sato-sphere screenshots + Carol Anne's dome-floor feedback. **Austin side-thread reply drafted but NOT sent** — Layer 3 caught the draft mis-attributing dome black-arcs to Austin's model when transcript was ambiguous (could be projector geometry). **Trustable email stack v1 SHIPPED** (`~/.claude/plans/trustable-email-stack-verification-gate.md`, 3 rounds Codex x-high review, 11/11 ACs verified): 5-layer verification gate live across all 4 send skills (proton/slack/signal/telegram). Engine at `~/projects/darren-workflow/scripts/verify-draft/`. Layer 3 reviewer via `claude -p` in warn mode per D9. Audit log at `~/.claude/local/send-audit.jsonl` + `/send-audit` drift digest skill. Failure-mode root cause: VLC misattribution in Draft 1 ("(taken from VLC)" — actually Sato-sphere viewer). Class of fix: mechanical gate at send boundary, can't be self-bypassed by Claude. Reusable artifacts: `verify_draft.py`, `gate_helpers.py`, `claude -p --disable-slash-commands` adversarial-reviewer pattern, `--skip-verify-confirmed-by-operator <UNIX_TS>` operator-override pattern. New memory: `reference_verify_draft_engine`, `feedback_no_unverified_attributions_in_external_drafts`, `reference_coast_salish_formline_primitives`. |
| `ebcddf4d` | 2026-05-19 | SSD Meeting 2 processing + 8 koi-backend bugfixes + 3 meta-learnings | **2026-05-18 Austin/Pravin/Darren/Eve meeting processed** (transcript + meeting note + 11 Otter screenshots embedded under `media/2026-05-18-ssd-meeting-2/` + 12 tasks + 4 new entity notes [James Nexw'Kalus-Xwalacktun Harry, Matt Robertson, Thunderbird, Formline] + 15 KG facts + 22 entity backlinks via backend full-sync). Style transfer DROPPED — pivot to Coast Salish primitives (Crescent/Circle/Trigon) following motion in marine footage. 5 prior stale SSD tasks auto-closed (5090 procurement + style-transfer LoRA superseded). **Eight koi-processor / process-note bugs investigated and fixed** (uncommitted in 3 repos): (1) `MentionedInDocument.first_seen` Pydantic NULL→500 (349 rows had NULL `created_at`); (2) sensor RIDs (`claude-session:`, `orn:gmail.message:`, etc) leaking into vault `mentionedIn` (SQL filter + path branch in single+batch endpoints); (3) `add_knowledge` defaulting new entities to Concept regardless of type (added `subject_type`/`object_type` to FactInput + MCP schema); (4) MOVE37XR→MOVE37 prefix-extension false merge (strict-prefix guard in `passes_token_overlap_check`); (5) process-note Check 2 missed YAML-side dangling wikilinks (scan extended to full file); (6) MOVE37XR Project→Organization type drift (UPDATE registry); (7) 50 stale `document_entity_links` RIDs (44 rewritten via basename find + 6 orphan deletes, in 1 tx); (8) `TypeMismatch` field on `EpisodeCreateResponse` so callers can detect existing-entity-type-vs-hint divergence (Tier 1/1b queries now return `entity_type`). **Two failure modes I caused during fixes:** (a) regex-based `mentionedIn` sync corrupted all 23 entity notes' YAML on the 3rd run — recovered via `recover_entity_notes.py`; rule: parse→mutate-dict→`yaml.safe_dump`, never regex YAML; (b) stale-RID cleanup misclassified `2026-05-14 Salish Sea Dreaming Meeting` as deleted (exact-basename `find` missed "The"-prefix rename) — 15 links dropped, renamed file's 31 links cover the entity set, vault_sync will reconcile. **Three new memory files**: `feedback_finish_the_backend_flow_when_chained_from_meeting_notes` (don't substitute manual flow for MCP pipeline — same class as Pravin pacing feedback), `feedback_defer_with_a_signal_not_a_hedge` (audit "intentionally deferred" — most are 10–20 min of work), `reference_yaml_and_data_writing_hygiene` (parse→mutate→serialize for structured data + validate data not script-return). Plus `reference_koi_backend_fixes_2026_05_19` covering all 8 backend patches with file:line + test. |
| `4a9a7b17` | 2026-05-19 eve | SSD prep call processed + **process-note completion gate built (7 phases, cross-project workflow infra in darren-workflow, not SSD)** | (a) Processed **2026-05-18 Darren+Pravin prep call** (transcript + meeting note + 10 tasks + entity wikilinks + 15 KG facts; documented the Otter "Victor Piper" phantom-speaker bug in `darren-workflow/docs/transcription.md`). (b) Operator reflection on the morning's failure modes ("how do we make sure these never happen again") → drafted `~/.claude/plans/process-note-completion-gate.md` (5 rounds Codex x-high review: R1-R3 design + mechanism, R4 must-fix with 8 Blockers + 5 Missing Tests + 5 Missing AC all addressed, R5 stopped at apply-creates-new-seams zone per disposition policy). 14 design decisions, 17 ACs, 772 lines. (c) **Executed all 7 phases**: P1 foundation (init script, vault_yaml.py atomic-write, audit.py concurrent-safe JSONL, two PreToolUse/PostToolUse hooks registered in `~/.claude/settings.json`, review.py digest); P2 executable Guards A-E with `log_backend_response` returning CORRECTED response (B5 bypass closer); P3 mentioned_in.py backend full-sync killing the 2026-05-19 local-append code path; P4 verify_run.py end-of-run L1-L5 gate with split-mode strict/warn + AC10 incident-replay fixture; P5 SKILL.md production cutover (next /process-note routes through gate); P6 triage layer surfacing top-5 prior-task close candidates inline with operator y/n/skip per Q9 happy path; P7 **autonomous strict-phase flip via launchd** (daily 09:05 fire, deterministic rubric, idempotent, ships in default `strict-vault, warn-phase` mode + flips after clean 14-day soak with ≥1 guard override). **PR #9 merged** (Phases 1-6, ~7400 lines, merge commit 7f3be2f). **PR #10 open** (Phase 7, +959 lines, daemon already installed + validated via launchctl kickstart). **131 pytest tests passing**. Telegram self-notifications wired (after fixing send-telegram.py flag name + installing telethon system-wide via `pip --break-system-packages` — telethon was silently missing from system Python, breaking ALL telegram-send invocations on this Mac; now unblocked). personal-koi task #2938 (due 2026-06-02) remains as belt-and-braces. 2 new tooling-issues logged: send-telegram.py venv path-math bug (extra `.parent` makes lookup miss), macOS-osascript-under-launchd unreliable. **All 2026-05-19 failure modes now mechanically detectable on the next /process-note run** (Phase 8 mis-skip → L2; Phase 9 local-append → L1; bad-merge wikilinks → L3 corrected-response-not-used; vault YAML corruption → L4 vault-mutation-bypass; blocklisted rationales → L2; missing phase in catalog → L1). |
