# SSD Phase 2 — Pipeline Build State (2026-05-22 overnight)

Status: INTERNAL ONLY. Overnight 2026-05-21 → 22 pipeline build addressing
Pravin's four 2026-05-21 asks ("I have reviewed the above work…").

## TL;DR

All four of Pravin's 2026-05-21 asks now addressed end-to-end. Reusable scaling
pipeline (3090 → TELUS H200) built and validated. Water-flow grammar v002
extended with alpha-channel ProRes 4444 RGBA outputs + a new inverted
"transpiration" scene + crescent-orientation A/B variant. Five-variant
Autolume sweep at 512² rendered and four of five upscaled to 4K crop framing.
Wild_psi120 (the "intricate Autolume dreaming" Pravin called out) rendered at
30s in both letterbox and crop framings.

## Pravin Ask Scoresheet

| # | 2026-05-21 ask | Status | Artifacts |
|---|----|----|----|
| 1 | Alpha-channel water-flow grammar | ✅ | `track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v002b_2026-05-22/*.mov` (3 ProRes 4444 RGBA, yuva444p12le, 132–165MB each) |
| 2 | Waterfall inversion (transpiration upward to stars) | ✅ | `.../transpiration_vertical_phrase_v002.{mp4,mov}` + `.../transpiration_vertical_phrase_v002_crescentup.{mp4,mov}` A/B |
| 3 | "Intricate Autolume dreaming" | ✅ | `docs/space-center/autolume-wild30s-2026-05-21/wild_psi120_30s_4k_{letterbox,crop}.mp4` (30s, 3840×2160, H.264 yuv420p) |
| 4 | 4K scaling pipeline for Autolume | ✅ | `scripts/telus_upscale.py` + `scripts/_pod_upscale_worker.py`. Validated end-to-end on 5 Autolume variants. |

## Asset Inventory (operator-checkable; every path is on disk as of 2026-05-22 02:00)

### Water-flow grammar v002b — 4 scenes × {RGB MP4, RGBA MOV, Moonfish composite}

`track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v002b_2026-05-22/`:

| Scene | RGB MP4 (H.264) | RGBA MOV (ProRes 4444) | Composite (over P1099653) |
|---|---|---|---|
| current_streamline_field_v002 | ✅ 882KB | ✅ 165MB | ✅ |
| waterfall_vertical_phrase_v002 | ✅ 541KB | ✅ 132MB | ✅ |
| transpiration_vertical_phrase_v002 (NEW) | ✅ 734KB | ✅ 132MB | ✅ |
| transpiration_vertical_phrase_v002_crescentup (NEW A/B) | ✅ ~735KB | ✅ ~132MB | ✅ |

Midpoint PNG stills for each in `midpoint_stills/`.

Composite recipe (unchanged from v002): footage cropped to drop burned-in timecode,
scaled to 1080p, set to 24fps, dimmed by 0.10, layer added at 0.55 opacity.

### Autolume sweep — 5 variants @ 512² + 4K crop set + wild_psi120 30s special

`docs/space-center/autolume-sweep-2026-05-21-v2/` (the 512² source clips,
correctly-state-isolated re-run after the v1 sweep had state-bleed bug):

| Variant | ψ | seed | anim | 512² duration | 4K crop |
|---|---|---|---|---|---|
| 01_baseline | 0.8 | 0 | F | 12.1s | ✅ 28MB |
| 02_tight_psi050 | 0.5 | 0 | F | 15.0s | ✅ 32MB |
| 03_wild_psi120 | 1.2 | 0 | F | 14.6s | ✅ 23MB (this 11s version; for the 30s flagship see below) |
| 04_noise_drift | 0.8 | 0 | T | 15.2s | ✅ 124MB |
| 05_seed42 | 0.8 | 42 | F | 14.7s | ✅ 36MB |

`docs/space-center/autolume-wild30s-2026-05-21/` (30s flagship):

| File | Resolution | Framing | Size |
|---|---|---|---|
| `wild_psi120_30s.mp4` | 512² | source | 4MB |
| `wild_psi120_30s_4k_letterbox.mp4` | 3840×2160 | center 2048² + black bars | 64MB |
| `wild_psi120_30s_4k_crop.mp4` | 3840×2160 | center 16:9 crop, lanczos up | 108MB |

Plus `docs/space-center/autolume-sweep-2026-05-21/03_wild_psi120_4k.mp4` — the
original 11s 4K letterbox integration test (20MB), kept for provenance.

## Pipeline Components Built

### `scripts/telus_upscale.py` + `scripts/_pod_upscale_worker.py`

Local driver + pod-side worker for Spandrel + Real-ESRGAN upscale on TELUS H200
Jupyter pod. Chunked upload (≤700KB per PUT via Contents API) + WebSocket kernel
execution. Reusable for any video upscale.

CLI:
```
python3 scripts/telus_upscale.py INPUT.mp4 [-o OUT.mp4]
    [--model x2plus|x4plus]            # x2plus for 1080p→UHD; x4plus for 512²→4K
    [--canvas 3840x2160]
    [--framing letterbox|crop]         # letterbox = pad bars; crop = center 16:9 slice
    [--job-name NAME]
    [--keep-job-dir]
```

Validated workloads:
- 1920×1080 24fps 6s → x2plus → 3840×2160 6s: 60s wall-clock
- 512² 30fps 14.6s → x4plus → 4K crop: 322s (5.4min)
- 512² 30fps 28.8s → x4plus → 4K crop: 780s (13min)

### `scripts/autolume_sweep.py` + `scripts/autolume_sweep.bat`

Headless Autolume render driver. Subclasses Autolume's live renderer to drive a
state machine: `preset_load → settle → record variant_i → settle → record
variant_(i+1) → …`. Each variant fully specifies all dials (truncation, noise
seed, noise anim) — no state inheritance. Uses Autolume's internal
`viz.start_recording(file_path)` for cv2 VideoWriter mp4v @ 30fps capture.

CLI:
```
python autolume_sweep.py
    --pkl PATH                # absolute path to .pkl model
    --preset PATH             # absolute path to Autolume preset dir
    --output-dir PATH         # where MP4s land
    --autolume-dir PATH       # default C:\Users\user\autolume
    --record-seconds N        # default 15
    --settle-seconds N        # default 2
    --variants JSON           # inline JSON list overriding DEFAULT_VARIANTS
    --variants-file PATH      # JSON list from file (avoids cmd escaping)
```

Triggered via `SSD-Autolume-Sweep` scheduled task (currently disabled but
registered) with `/ru INTERACTIVE` so the GLFW window can spawn in the auto-login
user's Console session 1.

### `scripts/water_flow_phrase_grammar_v002_alpha_and_inverse.py`

Add-on to v002. Adds the transpiration scene + per-scene ProRes 4444 RGBA
encoder. Imports v002's machinery wholesale (no drift from canonical grammar).

### `scripts/water_flow_phrase_grammar_v002_transpiration_crescentup.py`

A/B variant — same transpiration scene with crescent open_angle flipped from
`ang + pi` (cup back to origin) to `ang` (cup forward to terminus). Touches
Austin's open Q1 from v002. Internal A/B only.

### `scripts/water_flow_phrase_grammar_v002b_composites.py`

Generates composite previews of the 4 layer MP4s over Moonfish P1099653 footage,
using v002's `make_composite` recipe at 55% opacity + 10% footage dim. Output
sibling MP4s in the v002b dir.

## Failure Modes Logged Tonight

1. **Hedge-as-defer caught** (operator: "why are we waiting til tomorrow morning?").
   I'd written "Alpha-channel + waterfall inversion tomorrow AM" without auditing
   actual blockers. Operator challenge: classic `feedback_defer_with_a_signal_not_a_hedge`
   pattern (logged 2026-05-19 with same class of failure). Actual work was 35min.
   Memory entry already exists; this is a second instance worth tracking but
   not a new memory.

2. **CWD drift after `open` command** — used `open <folder>` in Bash, then for-loop
   with relative `scripts/telus_upscale.py` path failed because cwd had drifted to
   the opened folder. Fix: always use absolute paths in scripts that invoke other
   scripts.

3. **Worker `sys.exit(0)` raised inside Jupyter kernel** appears as SystemExit
   error to driver. Fix: don't sys.exit() at end of worker; driver polls status
   marker file instead.

4. **First-variant Autolume cold-start steals frames** — initial settle window
   needed to grow from 60 frames (2s) to 180 frames (6s) to let the async renderer
   warm up before recording. Variant 1 originally produced 41 frames; with longer
   settle gets 362+ frames. See autolume_sweep.bat record/settle defaults.

5. **State bleed across variants** — when only specifying changed dials per variant,
   prior dial values persist. Fix: every variant FULLY specifies all dials (psi,
   noise_seed, noise_anim) in DEFAULT_VARIANTS.

6. **ffprobe field-order surprise** — `-show_entries stream=r_frame_rate,width,height
   -of default=noprint_wrappers=1:nokey=1` returns fields in stream-struct order,
   not show_entries order. Fix: use `-of json` for stable parse.

7. **Jupyter Contents API base64 chunks** — Jupyter has ALREADY decoded base64
   chunks to binary on disk; pod-side reassembly should concatenate raw bytes,
   not re-base64decode.

## Open Items for Tomorrow / Friday

1. **Send Pravin the update** — proton-send + signal-send drafts ready to fire.
   See draft contour in CLAUDE.md or directly compose with operator review.
2. **Book Austin Friday check-in** — Pravin requested in 2026-05-21 message.
3. **Pravin picks favorites** from the 5-variant Autolume 4K crop set + the alpha
   layer A/Bs (especially the transpiration crescent-up vs default). Then we
   render any 30s-parity versions if not already done.
4. **Optional: HAP Alpha codec versions** of the 3 water-flow layers for live-mix
   playback in Resolume. Quick swap (~10min) — only if Pravin needs faster
   decode than ProRes 4444 supports.
5. **Audio path** — Pravin mentioned "video AND audio playback in next 48h". We
   haven't touched audio tonight. Status unknown; needs Pravin sync.
6. **Sunday live mix** — Pravin composes the live mix Sunday for Saturday
   recording. Asset packet is ready.

## Critical Path to Saturday Recording

- **Fri 2026-05-22 morning**: Pravin reviews assets, picks Autolume favorites + crescent A/B
- **Fri 2026-05-22 afternoon**: We render any requested variants at chosen lengths + framings
- **Fri 2026-05-22 PM**: All assets ready in Pravin's hands
- **Sat 2026-05-23**: Pravin records
- **Sun 2026-05-24**: Pravin composes live mix
- **Sun 2026-05-24 PM**: Pack for Monday install
- **Mon 2026-05-25 3pm YVR**: Install at HR MacMillan Space Centre

## Ready-to-Fire Signal Draft (NOT YET SENT)

```
Yes, up for check-in if you're still around.

All 4 of your asks landed tonight:
1. Scaling pipeline wired & validated: 3090 → TELUS H200 spandrel x4 → 4K.
   wild_psi120 30s ready in two framings — letterbox preserving the square,
   crop filling 16:9. Plus 4 more sweep variants at 4K crop for picking.
2. Alpha-channel versions of current_streamline + waterfall_vertical
   (ProRes 4444 RGBA) in water_flow_phrase_grammar_v002b_2026-05-22/.
3. Transpiration scene — inverted waterfall, phrases rising earth → stars.
   Crescent orientation A/B: default (cups back to origin) AND crescent-up
   (cups forward to terminus/sky). Pick whichever reads as "vapor" for you.
4. "Intricate Autolume dreaming" = wild_psi120 (ψ=1.2). 5-variant sweep
   ready for you to pick more flavors from.

Composite previews of all 4 water-flow layers over Moonfish underwater
footage — the sun rays at the top of frame become the "stars" the
transpiration phrases rise toward. Strong.

Local files in repo. Can upload to Proton in the AM if you want a
take-home packet, or scrub at the studio tomorrow.

For Austin Friday — what time works? I'll reach out once we lock a slot.
```

Sidecar will reference: this STATE doc, the on-disk artifact paths, the
ffprobe specs captured above. Through verify_draft gate.
