# Tomorrow handoff brief — 2026-05-18 AM

> Short brief for Darren after morning checklist read. Decisions / actions for the day.

## Major overnight finding (READ FIRST)

**`austin-v2-ingest/approved/` contains 7 PDFs in addition to 5 SVGs.**
PDFs are vector. `pdftocairo` is installed locally. Conversion path:

```bash
pdftocairo -svg austin-v2-ingest/approved/Animal_Bird_Heron_Background.pdf \
                austin-v2-ingest/approved/Animal_Bird_Heron_Background.svg
python3 scripts/decompose_austin_pieces.py --piece Animal_Bird_Heron_Background
```

This unblocks 7 more pieces for atom-level work (4 low-medium cultural load: Heron, Deer, Bee, Bear). The Pravin question about "more vector exports" is partially answered: **vector sources for these 7 pieces already exist locally — just need conversion.**

See full source inventory at `docs/space-center/austin-source-inventory-2026-05-18.md`.

## What to show Pravin FIRST

In order, on call or via shared screen:

1. **`morning-demo-folder-2026-05-18/1_watch_first/01_packet_v2_CONTACT_SHEET.png`** — single-glance review of all 15 packet artifacts with category-colored borders. Sets the visual context for everything in <30 seconds.
2. **`03_salmon_v005_CANONICAL.mp4`** — "this is the canonical Salmon mechanic. Both salmon swimming in place via continuous body deformation, counterphase, subtle eye pulse."
3. **`04_cosmic_breathing_v003c_CANONICAL.mp4`** — "this is the canonical Cosmic breathing mechanic. Rays + eyes only, subtle drift/pulse, shimmer reads as spirit/energy."
4. **`06_pearl_bead_single_traversal.mp4`** — "core pearl-bead-on-edges concept; one pearl carrying its morph along the edge."
5. **`2_supporting/01-02_primitive_field_v002_LIGHT/DARK`** — "NEW overnight; 60 atoms drifting, dual BG variants. Zero cultural risk so safe to use as Resolume ambient layer."
6. **`05_thecreator_pearl_bridge_NEW_OBSERVATION.png`** — "overnight discovery: Austin's TheCreator piece structurally echoes our pearl-bead. Visual resonance, NOT cosmological claim. Ask Austin whether this resonance is meaningful."

If conversation has room and Pravin asks for more:
- Cosmic→Salmon v007 (cross-piece morph) — frame as "promising direction, Austin's call on which relationships matter"
- Multi-pearl 3-node — frame as "polyphonic concept demo, rough"
- Raven↔Cosmic — already approved direction

## What to show Austin (exploratory / internal)

**ASK FRAMING**: "We've been experimenting internally with your pieces and the three primitive forms. Nothing here is approved or proposed as final. We want to ask: does any of this feel interesting, useful, or worth developing with you?"

Priority items (in `morning-demo-folder-2026-05-18/3_internal_ask_first/`):

1. **`01_cosmic_to_salmon_v007_landmark_routing.mp4`** — cross-piece morph using semantic atom routing
2. **`02_cosmic_to_salmon_v006_endpoint_correct.mp4`** — older sibling; comparison
3. **`05_wolf_to_salmon_HIGH_LOAD.mp4`** — **discuss BEFORE showing as artifact.** Wolf is ancestor, Salmon is provider; this pairing implicates clan relationships. Ask first: "Is this a pairing you'd want explored, or kept apart? What would respectful animation look like — and what would NOT?"

Also worth Austin's review (NEW overnight observations):
- **TheCreator pearl-bridge composite** (`1_watch_first/05_*`) — "We noticed atom_0114 (sphere) + atom_0117 (figure) in your TheCreator piece structurally echo a pearl-bead concept we developed independently. Is this resonance meaningful, or a coincidence? If meaningful, how should we treat it?"
- **Atom catalogs** (`packet v1 03_catalogs/`) — "We tried to map the visual atoms and primitive forms inside the pieces. What labels or relationships feel wrong? What should we be careful with?"

Cultural-load-tier reminder:
- LOW/MEDIUM: ask, share for feedback OK
- MEDIUM-HIGH: ask before sharing
- HIGH (Wolf, Orca): ask BEFORE showing; discussion-first
- VERY HIGH (TheCreator, Snake_Serpent, Thunderbird, Transformer): discussion-first, treat as ceremonial-level

## What to AVOID showing

- **Anything in `4_failed_controls/`** — preserved for internal context only. Do not include in any external review. Failed for documented architectural reasons.
- **Wolf↔Thunderbird-Background morph** — explicitly excluded per operator directive. Do not render, do not show, do not propose.
- **TheCreator pair morphs** (Cosmic↔TheCreator, Wolf↔TheCreator, Salmon↔TheCreator, Raven↔TheCreator) — VERY HIGH cultural load. Discuss with Austin before any pairing experiment.
- **The cross-dissolve regression videos** (preserved as anti-pattern controls) — useful internally but confusing if shown out of context.
- **Lane 2E POC v001/v002 visuals** — mechanism works but reads as "random shapes drifting" because too few atoms. Concept is documented; visual is failed control.

## What TD/Resolume can demo tomorrow

**TD frame-sequence scrub packs** (5 ready, all in `td/templates/assets/`):

1. **`cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/`** — **recommended canonical scrubber for cross-piece Austin demos.** 120 JPG frames, README present.
2. `cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/` — older sibling, retain as control.
3. `raven_sun_to_cosmic_sun_scrub_frames_v001/` — clean same-viewBox morph; lower cultural load than salmon transitions.
4. `primitive_cycle_scrub_frames_v001/` — LOW cultural load fallback.
5. `primitive_field_scrub_frames_v001/` — LOW cultural load fallback.

All packs verified: progress=0 → `frame_0001.jpg`; progress=1 → `frame_0120.jpg`. See `docs/space-center/td-mudra-scrubber-demo-2026-05-18.md` for wiring.

**Resolume-ready MP4 ambient layers** (drop into Resolume as video clips):

- `primitive_field_v002_flocking_light.mp4` — 1920×1080, 8 sec loop, ZERO cultural risk
- `primitive_field_v002_flocking_dark.mp4` — 1920×1080, 8 sec loop, ZERO cultural risk
- `primitive_field_v001.mp4` — 1920×1080, 6 sec loop, ZERO cultural risk (already used)
- `primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4` — 1024×1024, 18 sec loop
- Pearl-bead single + multi clips
- Salmon v005 + Cosmic breathing v003c (Austin per-output OK required for show use)

## What Agent 3 / Codex worker / H200 should continue

1. **Lane 2A v003 roe-particle-field** — spec at `docs/space-center/morph-lane-2a-v003-spec-2026-05-17.md`. Particles must BUILD the destination (no full dest fade). Codex worker assigned earlier.
2. **Lane #3 Moonfish-driven primitives** — optical flow drives primitive motion. Task #40.
3. **Lane #4 ControlNet still sheet matrix** — 9-cell matrix to test diffusion preservation of primitive geometry. Task #41.
4. **NEW: PDF→SVG conversion + decomposition of low-cultural-load pieces** — Heron, Deer, Bee, Bear. If Codex worker has bandwidth, this unblocks low-risk pair experiments. ~30 min per piece.

## Immediate next morph experiment recommendation

**Heron→Salmon morph via Lane 2E routing rule.**

Why:
- Heron PDF exists; pdftocairo can convert in 1 command
- Decomposition pipeline already proven on 5 pieces
- Heron+Salmon = ecology narrative ("Heron↔Salmon ecological adjacency candidate" (per peer caution 2026-05-18: avoid interpretive framing of meaning to Austin/Pravin)), low cultural risk
- First test of Lane 2E routing rule on a freshly-decomposed piece

Effort: ~3-4 hrs total
- 30 min: PDF→SVG conversion + decompose Heron + sub-agent classification
- 30 min: spine/eye/wing atom inspection
- 30 min: routing assignment per Lane 2E rule (semantic > spatial > primitive)
- 2 hrs: render + iterate

Best parallel work while morph renders: TD-wire the Heron scrubber pack once frames are ready.

## Open questions for Pravin

1. **5090 procurement** — spec confirm, source verify, order before Tue install. Task #26 in_progress.
2. **John handoff package** — Mon EOD hard deadline. Status?
3. **Sign-off on packet v2 for Austin** — packet ready at `morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/` when Pravin says go.
4. **Raster pieces** — should we attempt vectorizing Orca / Octopus / Mother_Bear_Cub PNGs (raster→vector), or ask Austin for vector source?

## Stop here

This is the final autonomous artifact. Wake up → morning checklist → contact sheet → this brief → decisions for the day.

Sleep well.
