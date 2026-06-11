# MVP Fallback Resolume Package — 2026-05-19

Date: 2026-05-19
Lane: Agent A (production fallback / clean media)
Sister lanes:
- Agent B — primitive water grammar (Crescent / Circle / Trigon)
- Agent C — prompt-to-primitive scene design

This is the stable floor for the Hubble wide wall: clean, projector/Resolume-ready clips that can run even if every Austin-derived layer in the deck is muted. No SD, no LoRA, no Austin-derived morphs. No generation in this lane today.

## Scope

Build a fallback Resolume package that:

- Plays at the projector-path resolution (3840x2160) with no visible filename / source-timecode burn-in.
- Uses only Austin-independent footage (Evan Vancouver Island, H6 kelp forest, Moonfish underwater).
- Supports Option D of the wide-wall plan: ambient low-risk mode = H6 + primitive field, no Austin source pieces, no SD/LoRA.
- Lets the operator switch the deck into "fallback only" instantly if Austin per-output review delays push the Austin-derived layers behind a kill switch.

## Package Location

`track2-deterministic/morph_outputs_INTERNAL/mvp_fallback_package_2026-05-19/`

```
mvp_fallback_package_2026-05-19/
├── README.md                       # per-file specs, crop decisions, Resolume layer stack
├── clean_exports/                  # the Resolume-ready MP4s
│   ├── evan_vancouver_island_3840x2160_20s.mp4
│   ├── h6_kelp_forest_4k_cropped_50s.mp4
│   ├── moonfish_P1000011_salmon_surface_3840x2160_50s.mp4
│   ├── moonfish_P1077716_reef_garden_3840x2160_50s.mp4
│   ├── moonfish_P1099653_dense_salmon_school_3840x2160_50s.mp4
│   ├── moonfish_P1111509_reef_anemones_3840x2160_19s.mp4
│   ├── moonfish_P1111707_kelp_seal_3840x2160_50s.mp4
│   └── moonfish_P1111785_yellow_kelp_3840x2160_50s.mp4
├── sources_probe_frames/           # frames used to inspect source burn-in and verify outputs
└── _provenance/                    # ffprobe JSON for every output
```

## Moonfish Files — Usable Proxy/Fallback Media (Not a Blocker)

The 2026-05-18 footage hygiene review listed six Moonfish underwater clips as accessible-but-uninspected because the Proton Drive hydration stalled the first probe. Today they were available locally at `media/collaborators/moonfish-video/underwater/` (all six, 19s–428s, 1920x1080 @ 59.94fps).

Frame extraction at mid-clip and t=0.9 confirmed: all six Moonfish files carry the same burn-in pattern as the H6 hero subclips — filename label at lower-left (e.g. `P1000011.MOV`, `P1099653.MOV`) and source-timecode at lower-right (e.g. `SRC TC: 01:54:37;54`). The H6 4K subclip's bottom-edge burn-in shows `P1099653.MOV`, which is one of the Moonfish files — H6 was almost certainly cut from these proxies.

**How to treat these files:** they are usable proxy/fallback media for everything this package is for. The burn-in lives in a bottom band and is fully removable two ways:

- baked into the exports here via `crop=… , pad=… :color=black` (already applied — symmetric letterbox);
- or live in Resolume via a layer-level crop / source-rect adjust (acceptable as an alternative if the operator prefers a non-letterboxed background and is willing to lose a sliver of bottom imagery instead).

Either path is fine for projector testing today.

**Clean-master swap-in is a future improvement, not a blocker.** Moonfish Media is away right now, so the request for true-master exports without filename / SRC TC burn-in is deferred to the post-return checklist. If/when clean masters arrive, the cropped underwater clips here can be swapped 1:1 inside the same Resolume layer group with no other deck changes.

## Crop & Pad Decisions

Three transformations were applied, one per source family:

### 1. Evan Vancouver Island 4K — center-crop to 3840x2160

- Source: 4096x2160 @ 24fps, 20s, 480 frames, h264 (Proton Drive, "Vancouver Island 4K - Evan")
- Bottom-edge inspection: clean — rocky coastline, no overlay text.
- Transform: `crop=3840:2160:128:0` (center-cropped, 128px from each side discarded).
- Rationale: Hubble projector path is 3840x2160 native. 4096 width is preserved as the documented source; the cropped delivery is what Resolume plays back at 3840x2160 without any per-clip scaling.

### 2. H6 Kelp Forest Floor 4K — crop bottom 160px, pad symmetric letterbox

- Source: `media/hero-subclips/H6_kelp_forest_floor_4k.mp4` — 3840x2160 @ 59.94fps, 50.05s, 3000 frames.
- Bottom-edge inspection: burn-in present, "P1099653.MOV" lower-left and "SRC TC: 09:06:35;46" lower-right; text band occupies roughly y=2020–2100.
- Transform: `crop=3840:2000:0:0, pad=3840:2160:0:80:color=black` — crop the bottom 160px to eliminate burn-in with safety margin, then pad symmetric 80px black bars top + bottom.
- Result: imagery is vertically centered in a 3840x2160 frame; thin matte bars top and bottom. In a darkened gallery the bars read as cinema-style letterboxing.

### 3. Moonfish 1080p — crop bottom 80px, lanczos upscale, pad symmetric letterbox

- Sources: all six `media/collaborators/moonfish-video/underwater/P*.mp4` — 1920x1080 @ 59.94fps, h264 ~27 Mbps. Lengths range 19s to 428s.
- Bottom-edge inspection: same burn-in family as H6.
- Transform: `crop=1920:1000:0:0, scale=3840:2000:flags=lanczos, pad=3840:2160:0:80:color=black`. Drop bottom 80px → crop is 1920x1000; lanczos upscale → 3840x2000; pad symmetric 80px black bars top + bottom.
- Quality note: lanczos upscale of 1080p source holds up well on the 3840 wall for soft underwater content (kelp, schooling fish, ambient light). For tight foreground subjects or text it would not; underwater wide-angle is the right use.

All three outputs target the same 3840x2160 container so Resolume can swap them inside the same composition layer without re-mapping.

## What Is Public-Safe vs Internal-Only

This lane keeps the cultural-load floor as low as possible. Each clip's status:

| Clip family | Cultural load | Public-safe today? | Notes |
|---|---|---|---|
| Evan Vancouver Island 4K | Low — non-Austin landscape | Yes for projector testing; **media/license audit still required for any public showing or recording** | Vancouver Island coastline (Evan footage). Confirm permission terms with Evan before public framing. |
| H6 Kelp Forest Floor 4K (cropped) | Low — non-Austin marine | Yes for projector testing; **media/license audit still required for public showing** | Moonfish-sourced; needs Moonfish credit/permission on any public framing. The cropped delivery hides the SRC TC; it does not change the underlying footage rights. |
| Moonfish underwater (cropped + upscaled) | Low — non-Austin marine | Yes for projector testing; **same Moonfish license requirement as H6** | Six clips: salmon-over-surface, reef garden + salmon, dense salmon school looking up, reef + anemones, kelp + seal, yellow kelp forest. |
| Anything Austin-derived | High — cultural / consent floor | **No — per-output Austin sign-off required before public showing** | Not included in this package by design. Lives in Agent B/C lanes and in the wide-wall plan layers 3–5. |

This package is built so the Hubble wall can run in technical-test mode today without waiting on Austin per-output review and without front-loading any Austin-derived assets.

## How It Fits the Wide-Wall Plan

This package is the Option D / "Ambient Low-Risk Mode" floor described in `docs/space-center/resolume-wide-wall-composition-plan-2026-05-18.md`. Layer 1 in that plan ("Background / ocean / H6 4K") maps directly here; the optional ambient grammar layer (Layer 2) is what Agent B will produce in a separate lane.

Wide-wall plan's three demoable looks this week:

- "Safe fallback" — this package, full stop. No Austin source, no SD/LoRA. The clips here are the H6/Moonfish/Evan layer-1 material.
- "Austin-review exploratory look" — adds Layer 3 / 4 (Austin pieces, deterministic Raven→Cosmic) on top of this floor. Out of scope for Agent A.
- "Ambitious show-architecture look" — pearl-bead graph etc. Out of scope for Agent A.

If any Austin-derived layer review goes long or doesn't land, the deck stays on this package.

## Recommended Resolume Layer Stack (Fallback Only)

This is the minimum-risk live arrangement that uses only this package's clips. Agent B's primitive-grammar layer slots in above it once delivered.

| Order | Layer name | Source clip(s) | Blend | Opacity | Notes |
|---|---|---|---|---|---|
| 1 | Ambient — coastline (non-underwater) | `evan_vancouver_island_3840x2160_20s.mp4` | Normal | 80–100% | Short 20s loop; use as scene-opener or interstitial between underwater scenes. |
| 2 | Background — kelp forest dense | `h6_kelp_forest_4k_cropped_50s.mp4` | Normal | 70–90% | Primary underwater base. Slow playback, no fast cuts. Slight letterbox already baked in. |
| 3 | Background — kelp/fish variant pool | `moonfish_P1077716_reef_garden_3840x2160_50s.mp4`, `moonfish_P1099653_dense_salmon_school_3840x2160_50s.mp4`, `moonfish_P1111785_yellow_kelp_3840x2160_50s.mp4` | Normal | 70–90% | Rotate as the underwater base when H6 has been on long enough; same blend recipe. |
| 4 | Texture/transition — short clips | `moonfish_P1000011_salmon_surface_3840x2160_50s.mp4`, `moonfish_P1111707_kelp_seal_3840x2160_50s.mp4`, `moonfish_P1111509_reef_anemones_3840x2160_19s.mp4` | Normal or Screen | 50–80% | Use as B-roll for transitions; the P1111509 19s clip is short — set Resolume loop with crossfade. |
| 5 | (reserved) Primitive grammar layer | Agent B output (TBD) | Screen / Add | 8–22% | Slot above the background once primitive-field clips arrive. |
| 6 | (reserved) Austin-derived foreground | None in this package | — | — | Kill-switched off until per-output review. Lives on its own layer group per the wide-wall plan. |

Notes for Resolume operator:

- Keep all of this on a dedicated layer group "Fallback (Agent A)" so it can solo-mute everything else for a clean technical test.
- For best playback performance on the 3090 / 5090, convert the H.264 deliverables to HAP via Resolume Alley before show day; H.264 4K @ 59.94 will work but uses more CPU than HAP. Document the HAP conversion in the package README once done.
- Avoid blur / colorize / mirror / kaleidoscope on this layer group — these clips are the floor and should read as themselves.

## What This Lane Did Not Touch (and Why)

- **No Austin LoRA, no SD, no morphs.** Out of scope for the stable floor lane; lives in other lanes.
- **No primitive-grammar generation.** Agent B's lane. This package only provides the background that Agent B's primitive overlays will sit on top of.
- **No new venue-facing communications.** This is internal production hygiene.
- **No Moonfish or Evan outreach.** Moonfish Media is away; permission confirmations and the clean-master swap-in are on the post-return checklist (see Operator Closeout). Nothing is sent in this lane.

## Verification

Every output MP4 in `clean_exports/` is ffprobed for width, height, fps, duration, and frame count; results are written into `_provenance/ffprobe_outputs.json` and reproduced in the package README. The same per-clip values are quoted in the README's spec table.

## Operator Closeout

This package is the stable fallback floor. To put it to work:

1. **Load** the package's `clean_exports/` clips into Resolume as a single layer group named **"Fallback (Agent A)"**. Eight clips, all 3840x2160 — they share a container so the layer group can swap between them without re-mapping.
2. **Use for projector / Resolume testing now.** Solo-mute the group for a clean technical test of the Hubble wide-wall path. Letterbox bars on H6 and Moonfish clips are intentional — they hide the source burn-in and read as cinema-style framing in a darkened gallery.
3. **HAP transcode later via Resolume Alley** before show day to reduce CPU during playback. The H.264 deliverables here will play, but HAP is the production codec on the 3090 / 5090. Not blocking for testing — do it once the deck is settled.
4. **Post-return checklist (do not action now):**
   - Confirm Evan's permission terms for any public-facing use of the Vancouver Island 4K clip.
   - Ask Moonfish Media (once back) whether a true-master export without filename / SRC TC burn-in exists. If yes, swap into the same Resolume layer group 1:1.
   - Once Agent B's primitive-grammar layer is ready, restack per "Recommended Resolume Layer Stack" above.
