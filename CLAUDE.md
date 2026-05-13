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

The 3090 at Prav's studio (108 Fraser Rd, Salt Spring) is accessible via SSH from anywhere using a reverse tunnel through poly.

**From local network (same house):**
```bash
ssh windows-desktop          # direct, 10.0.0.81
```

**From anywhere (remote):**
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

**Date:** 2026-05-13
**Status:** **Phase 2 sprint Day 3 of ~14** — Indigenomics IMPACT activation at **HR MacMillan Space Centre, Hubble Space**, late May (~May 25 doors; May 22–24 install window). Comprehensive plan complete + Codex-reviewed; Phase 0 scaffolding shipped; Prav email sent via Proton awaiting his forward to venue group (Michael Unger / Lorraine Lowe / Bryce Tordiffe / Natalia Lebedinskaia).

**📋 Read first:** `~/.claude/plans/ok-so-i-polymorphic-melody.md` — 14-section strategic plan (lint-clean, 3 Codex `/review-plan` rounds at x-high reasoning). Canonical source of truth for Phase 2.

**Venue identity (clarified):** Indigenomics IMPACT IS the Space Centre show (same event — earlier plans treated separately). Lorraine approved 1080p+ projector upgrade 2026-05-09. Pre-event install + test access secured. 1100 Chestnut St, Vancouver. Territory: xʷməθkʷəy̓əm (Musqueam) / Sḵwx̱wú7mesh (Squamish) / səlilwətaɬ (Tsleil-Waututh).

**License Policy:** COMMERCIAL USE — CC0, CC BY, CC BY-SA only. CC BY-NC excluded. Full credits + audit: `docs/space-center/credits-and-licenses-2026-05.md`.

**What's Done (Phase 2 plan + Phase 0 kickoff, 2026-05-11 → 13):**
- Comprehensive plan + 3 Codex rounds resolved 30+ open questions; remaining strategic items are Prav-conversation-owned and documented as Stakeholder Alignment dependencies
- 5 deep-research prompts paste-ready at `docs/next-iteration/_research/prompt-0[1-5]*.md` for parallel ChatGPT / Gemini / Claude.ai Deep Research triangulation
- Phase 0 scaffolding in `docs/space-center/`: `austin-consent-map.md` (Day-2 screenshare template), `credits-and-licenses-2026-05.md` (Day-8 lockdown audit), `license-audit.md`, `draft-email-to-michael-unger-2026-05-12.md`
- Vault People notes: created `People/Michael Unger.md`, updated `People/Natalia Lebedinskaia.md` with full contact + expanded role
- Email to Prav sent via Proton 2026-05-13 (subject: "Re: 720 dpi projectors in the Hubble Space") asking him to forward venue-group draft; correction follow-up sent re: cc address
- **Root-cause fix:** built `proton-send` skill at `~/projects/darren-workflow/skills/proton-send/` wrapping local Proton Mail Bridge SMTP — Proton sends now first-class in any session
- 9 new memory entries: see `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/MEMORY.md`
- Austin's "no AI generation in my style" stance captured (May 5 meeting; Xwalacktun teaching) — LoRA-on-Austin's-portfolio dropped from May default; primary morph technique = manual decomposition + TD interpolation of his actual vectors
- TELUS confirmed 3× H200 available (Apr 4 ops data); parallel Jupyter strategy validated. Phase 1 "Landscape Dissolution" (Boids+depth+ControlNet) flagged as adaptable to formline morphs.
- 5090 sourcing scoped: Memory Express + Canada Computers Vancouver have AIB 32GB ~$2,500–3,500 CAD; full build $7–8k feasible

**Prior session work (compressed, see claude-mem for detail):** Phase 2 planning kickoff 2026-05-04 (Austin research, 127-image portfolio scrape); post-exhibition return 2026-05-03 (96-file installation-archive, scp -O gotcha); Saturday VJ prep 2026-04-23 (3 audio-reactive TD scenes, MediaPipe `hand_pos` bridge).

**Prior production stack (intact):** Autolume 120 kimg + StreamDiffusion sd-turbo + Resolume Arena + visitor web app + auto-heal + SSH reverse tunnel. **Briony layer DROPPED** for Phase 2 (aesthetic mismatch with Austin's Coast Salish lines).

**What's Left (next session, priority-ordered):**
1. **5090 decision (BLOCKING TODAY 2026-05-13):** order from Memory Express / Canada Computers Vancouver, or punt to next venue. Confirm budget with Prav.
2. **Status check on Prav reply** to the Proton email — has he forwarded venue-group draft to Michael Unger? Any edits requested?
3. **Run 5 deep-research prompts** in parallel external tools (paste-ready files in `docs/next-iteration/_research/`); save outputs as `prompt-NN__claude.md` / `__gemini.md` / `__chatgpt.md` for triangulation
4. **Austin asset gate Thu May 14 (Day 4):** first batch in? YES → kick off TELUS H200 parallel render. NO → continue formline-decomposition experiments on already-scraped `austin-reference/` with verbal per-piece OK gating
5. **Carol Anne sign-off** on protocol/sharing posture (async via Signal — Prav-owned)
6. **Formline decomposition experiments START** on austin-reference/: 3–5 hero pieces (Salish Spirit Thunderbird, Westridge Orca, Whitecaps Sínulhka, MST Thunderbird House Post, KwiKwi); review with Austin via Signal screenshare
7. **TELUS H200 access provisioning** with Carol Anne — EOD Wed May 13
8. **Track A items** (Resolume Advanced Output remote automation, WASAPI rewrite, tunnel hardening) — parallel to content work
9. **Older deferred (stretch only):** visitor-app chat-mode bug, SD food-prompt quirk

**Open questions (Prav-conversation-owned — Stakeholder Alignment in plan):** Austin contract signed? Indigenomics organizer thesis approval? Sponsor expectation (transit-triptych vs ceremonial)? Compensation alignment across collaborators?

See `Tasks/2026-05-05-*` and `Tasks/2026-05-08-*` for the 18 individual open tasks from the latest meetings (10 already auto-closed against same-day evidence).

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
| `64276b6e` | 2026-05-11 → 13 | Phase 2 plan + Phase 0 kickoff + proton-send root-cause fix | **Indigenomics IMPACT @ Hubble Space (Space Centre) strategic plan + Phase 0 kickoff.** Built comprehensive 14-section plan at `~/.claude/plans/ok-so-i-polymorphic-melody.md` through 3 Codex `/review-plan` rounds at x-high (lint-clean strategic type; 30+ open questions resolved across rounds; remaining strategic items documented as Prav-conversation-owned Stakeholder Alignment dependencies). Resolved Indigenomics IMPACT = Space Centre show (same event). 5 deep-research prompts saved paste-ready at `docs/next-iteration/_research/prompt-0[1-5]*.md` for parallel ChatGPT/Gemini/Claude.ai Deep Research triangulation. Phase 0 scaffolding: `docs/space-center/austin-consent-map.md` + `credits-and-licenses-2026-05.md` + `license-audit.md` + drafts. Vault: `People/Michael Unger.md` created, `People/Natalia Lebedinskaia.md` expanded. **Email to Prav sent via Proton 2026-05-13** asking him to forward venue-group draft (Michael/Lorraine/Bryce/Natalia). **Root-cause fix:** built `proton-send` skill + Python script at `~/projects/darren-workflow/{scripts,skills}/proton-send/` wrapping local Proton Mail Bridge SMTP — Proton sends now first-class alongside Gmail MCP. 9 new memory entries (`reference_*`, `feedback_*`, `project_*`) capturing venue identity, contact chain, Austin's "no AI generation" stance, exploration-over-lock-in posture, proton-send skill, SSD-uses-Proton-not-Gmail address rule. User-driven plan corrections: visitor-app + MediaPipe restored as PRIMARY (not Tier-2), 5090 active R&D track, Austin's stated preference for interactive morphing of existing pieces (not AI-generation) shifted plan defaults. TELUS = 3× H200 confirmed; "Landscape Dissolution" Phase 1 technique flagged adaptable to formline morphs. 5090 sourcing scoped (Memory Express + Canada Computers Vancouver, $7–8k full build). No git commits this session (per user convention; commit when ready). |
