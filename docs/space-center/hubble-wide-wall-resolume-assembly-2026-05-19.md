# Hubble Wide-Wall Resolume Assembly — 2026-05-19

Date: 2026-05-19
Lane: Agent A (operator assembly doc — practical Resolume deck build for today)
Purpose: tell the operator exactly which files to load, what layer group to put them on, what blend/opacity to start at, and what to keep kill-switched.

Not a creative design doc. No new media is rendered in this lane.

## Projector Path

| Item | Value |
|---|---|
| Hubble wide-wall target | 3840x2160 (UHD), 16:9 (per `mvp-fallback-resolume-package-2026-05-19.md` + `resolume-wide-wall-composition-plan-2026-05-18.md`) |
| Show machine candidates | 3090 (current), 5090 (incoming this week) |
| Codec for today's testing | H.264 (delivered) — HAP transcode is deferred (see below) |
| Audio | Visual layers only; audio runs independently (Ableton / WMP per ops playbook) |

## Folders To Import (Verified Paths)

Repository root: `/Users/darrenzal/projects/salish-sea-dreaming/`

```text
track2-deterministic/morph_outputs_INTERNAL/mvp_fallback_package_2026-05-19/clean_exports/
    evan_vancouver_island_3840x2160_20s.mp4
    h6_kelp_forest_4k_cropped_50s.mp4
    moonfish_P1000011_salmon_surface_3840x2160_50s.mp4
    moonfish_P1077716_reef_garden_3840x2160_50s.mp4
    moonfish_P1099653_dense_salmon_school_3840x2160_50s.mp4
    moonfish_P1111509_reef_anemones_3840x2160_19s.mp4
    moonfish_P1111707_kelp_seal_3840x2160_50s.mp4
    moonfish_P1111785_yellow_kelp_3840x2160_50s.mp4

track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v004_2026-05-19/
    03_perspective_ripple_plane_v004_black_screen.mp4
    04_current_sheet_v004_black_screen.mp4
    01_articulated_fish_glyph_v004_black_screen.mp4
    02_salmon_proxy_articulated_v004_black_screen.mp4
```

Reference-only (do not load into the show deck today — pre-stage on a separate parked group):

```text
track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4
track2-deterministic/morph_outputs_INTERNAL/austin-raven-cosmic-uhd-surround-fill-endpoint-scheduled-4sec-2026-05-18-results/raven_cosmic_endpoint_scheduled_lora035_d30_uhd_surround_fill_3840x2160_4sec.mp4
track2-deterministic/morph_outputs_INTERNAL/austin-cn-lora-raven-cosmic-endpoint-scheduled-2026-05-18-results/raven_cosmic_endpoint_scheduled_2026-05-18__canny__endpoint_scheduled_lora035_d30_cn078to100.mp4
track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4
track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4
track2-deterministic/morph_outputs/exp1_three_primitives_cycle_2026-05-16.mp4
track2-deterministic/morph_outputs/_compose_pearl_dry_run.mp4
```

All paths above were verified present on 2026-05-19. No missing paths to report.

## Layer Group Structure

Build the deck as five Resolume layer groups, top to bottom of the stack. Each group has its own solo/mute so the deck can be reduced to "fallback only" instantly.

| Group # | Group name | Source | Default state today |
|---|---|---|---|
| 1 | `Fallback footage` | `mvp_fallback_package_2026-05-19/clean_exports/` (8 clips) | ON. Stable floor; safe-fallback look. |
| 2 | `Water grammar (v004)` | `primitive_water_grammar_v004_2026-05-19/` clips 03, 04 | ARMED, low opacity. Internal-only until Austin signs off the specific output. |
| 3 | `Fish grammar (v004)` | `primitive_water_grammar_v004_2026-05-19/` clips 01, 02 | LOADED, MUTED. Darren gave change requests in `REVIEW_ORDER.md`; clips have not been Austin-reviewed. Do not show publicly. |
| 4 | `Austin-derived (kill-switched)` | raven-cosmic deterministic + SD/LoRA finish + pearl-bead clips listed above | LOADED, MUTED, bypass on group. Per-output Austin sign-off required before any public showing. |
| 5 | `Prompt/dream system` | (none today) | PARKED. Visitor prompt-to-primitive live system is architectural-only for IMPACT; not part of today's deck. See `interactive-dream-to-primitive-architecture-2026-05-19.md`. |

Group naming should match exactly so the kill-switch convention is unambiguous.

## Recommended First Scene Deck

One scene at a time. Start here and stop here unless Pravin asks to keep going.

### Scene 1 — `Fallback only (Agent A solo)`

Use to verify the projector path and codec playback. Solo-mute Group 1; mute everything else.

| Layer order (bottom→top) | Clip | Blend | Opacity |
|---|---|---|---|
| 1 | `h6_kelp_forest_4k_cropped_50s.mp4` | Normal | 80% |
| 2 | (rotate) `moonfish_P1077716_reef_garden_3840x2160_50s.mp4` / `moonfish_P1099653_dense_salmon_school_3840x2160_50s.mp4` / `moonfish_P1111785_yellow_kelp_3840x2160_50s.mp4` | Normal | 70–90% |
| 3 | (interstitial) `evan_vancouver_island_3840x2160_20s.mp4` | Normal | 90–100% |
| 4 | (b-roll, optional) `moonfish_P1000011_salmon_surface_3840x2160_50s.mp4` / `moonfish_P1111707_kelp_seal_3840x2160_50s.mp4` / `moonfish_P1111509_reef_anemones_3840x2160_19s.mp4` | Normal or Screen | 50–80% |

### Scene 2 — `Fallback + water grammar (internal review)`

Group 1 ON; Group 2 ARMED at low opacity. Show Pravin only.

| Layer order | Clip | Blend | Opacity |
|---|---|---|---|
| 1 | `h6_kelp_forest_4k_cropped_50s.mp4` | Normal | 80% |
| 2 | `03_perspective_ripple_plane_v004_black_screen.mp4` | Screen (or Add) | 35–55% |
| 3 | `04_current_sheet_v004_black_screen.mp4` | Screen | 10–25% (Darren flagged as first attempt, not directly usable yet; start very low. Not Austin-reviewed.) |

v004 clips are 1920x1080 — scale-to-fit on the 3840x2160 canvas; do not letterbox the v004 overlay. Black background renders transparent under Screen/Add. No alpha channel needed.

Do not enable Scene 2 in front of any third-party / public audience today. Pravin-only.

### Scenes 3–N — Not For Today

`Austin-derived (kill-switched)` and `Prompt/dream system` groups stay muted. They exist in the deck as pre-staged content for later review; not for live playback today.

## Blend Modes And Opacity Reference

| Layer purpose | Blend | Opacity range | Notes |
|---|---|---|---|
| Coastline interstitial (Evan) | Normal | 80–100% | Use as scene-opener; 20s clip — set Resolume loop with crossfade. |
| Underwater base (H6) | Normal | 70–90% | Primary base. Slow playback. Letterbox bars are baked in — do not crop further. |
| Underwater variants (Moonfish 50s clips) | Normal | 70–90% | Rotate with H6 every 1–2 minutes. |
| Underwater b-roll (Moonfish 19s anemones) | Normal or Screen | 50–80% | Resolume crossfade loop required (19s is short). |
| Water grammar v004 — perspective ripple | Screen / Add | 35–55% | Darren: positive internal review note on perspective surface (REVIEW_ORDER). NOT Austin-reviewed. |
| Water grammar v004 — current sheet | Screen / Add | 10–25% | Darren: first attempt, not directly usable yet — keep low. NOT Austin-reviewed. |
| Fish grammar v004 — articulated glyph | Screen / Add | MUTED today | Darren: change requests in REVIEW_ORDER (circles for eyes, smoother motion, etc.) — feedback in v005 backlog. NOT Austin-reviewed. |
| Fish grammar v004 — salmon proxy | Screen / Add | MUTED today | Darren: swim direction reversed; width uniform; needs fix. NOT Austin-reviewed. |
| Austin-derived foreground / morph / pearl | Normal | MUTED today | Per-output sign-off required. |

Avoid blur / colorize / mirror / kaleidoscope / feedback on any layer of Groups 1–3 today. Effects only on background if needed.

## What To Show Pravin Today

Yes:

1. Scene 1 (Fallback only) on the projector at 3840x2160 — confirm playback, color, contrast in venue lighting.
2. Scene 2 (Fallback + water grammar v004 perspective ripple at low opacity) — show internal grammar progress; Darren's v004 review note on the perspective ripple plane (clip 03 in `REVIEW_ORDER.md`) was positive. Clip is NOT Austin-approved — this is internal/Pravin review only.
3. The layer-group structure and kill-switch convention.
4. The folder map above so he knows where the assets live.

Defer or skip:

- Fish grammar v004 (01, 02) — Darren's v004 review notes in `REVIEW_ORDER.md` are change requests; clips have not been Austin-reviewed.
- Current sheet v004 (04) — Darren flagged it as a first attempt, not directly usable yet; clip has not been Austin-reviewed.
- All Austin-derived foreground (raven-cosmic / pearl-bead / SD-LoRA finish).
- Any framing of the deck as "show-ready" — it is technical assembly today.

## What Requires Austin Review Before Any Public Showing

Per-output sign-off is the floor, not a milestone (per `feedback_austin_consent_trust_floor.md`). The following are loaded into the deck but stay muted in the `Austin-derived (kill-switched)` group until Austin has approved that specific output:

- `raven_sun_to_cosmic_sun.mp4` (deterministic morph)
- `raven_cosmic_endpoint_scheduled_lora035_d30_uhd_surround_fill_3840x2160_4sec.mp4` (endpoint-protected UHD)
- `raven_cosmic_endpoint_scheduled_2026-05-18__canny__endpoint_scheduled_lora035_d30_cn078to100.mp4` (SD/LoRA finish)
- `04_pearl_bead_traversal.mp4` and `04_multi_pearl_animation.mp4` (pearls use Austin source textures; pearl/spindle-whorl framing also still open per `project_austin_pearl_vision.md`)
- v004 clips 01 (articulated fish glyph), 02 (salmon proxy articulated), and 04 (current sheet) — Darren gave change requests in `REVIEW_ORDER.md`. None of these have been Austin-reviewed.
- v004 clip 03 (perspective ripple plane) — Darren gave a positive internal review note in `REVIEW_ORDER.md` ("good job…working with topology is really interesting"). This is internal review feedback only. Clip 03 is **not Austin-approved**.
- v005 primitive grammar clips (any) — no v005 clip is treated as Austin-approved by this doc.

No v004 or v005 primitive grammar clip is public-approved. Internal-only / Pravin-review showing is the ceiling until Austin has reviewed the specific output.

## What NOT To Show Publicly (Today's No-Go List)

- Anything from the `Austin-derived (kill-switched)` group.
- Fish grammar v004 (01, 02).
- Current sheet v004 (04).
- Any prompt-to-primitive live demo (parked until after IMPACT — see `interactive-dream-to-primitive-architecture-2026-05-19.md`).
- Any "Austin-style" or "Coast Salish style" framing in operator-facing UI or signage.
- Pearl / spindle-whorl public language — wording is still open.
- Recording or screen-capture of the wall for distribution — Moonfish / Evan license terms still pending (see clean-master note below).

The fallback clips (Group 1) are safe for projector testing in the venue today. Public showing or recording of those clips still requires the media/license audit on the post-return checklist; this is a hard rule from the MVP fallback package, not a Today blocker because there is no public audience for technical assembly.

## HAP Transcode Checklist (Deferred — Do Not Transcode Today Unless Asked)

H.264 at 4K / 59.94 plays fine for assembly and testing. HAP is the production codec to drop CPU load before show day; only run after the deck is settled.

Checklist for later:

1. Open Resolume Alley.
2. Add the eight `mvp_fallback_package_2026-05-19/clean_exports/*.mp4` clips.
3. Codec: HAP (not HAP Q, not HAP Alpha — these clips have no alpha).
4. Output dir: `track2-deterministic/morph_outputs_INTERNAL/mvp_fallback_package_2026-05-19/hap_exports/` (create on transcode day).
5. Verify each output plays back at 3840x2160 in Resolume preview.
6. Swap the HAP files into the `Fallback footage` group; keep the H.264 files as backup until show day.
7. Note: v004 clips are short (6s, 1920x1080) — HAP transcode is optional; H.264 load is negligible.

Do not transcode today. Wait for explicit ask.

## Moonfish Clean-Master Note (Deferred — Not Blocking)

The eight fallback clips carry baked symmetric letterbox bars that hide a filename / SRC TC burn-in present in the Moonfish proxy footage and the H6 subclip cut from it (per `mvp_fallback_package_2026-05-19/README.md`). The letterbox reads as cinema-style framing in a darkened gallery and is safe for projector assembly today.

Moonfish Media is away. The ask for true clean-master exports (no filename / SRC TC burn-in) is on the post-return checklist. If/when clean masters arrive, they swap into the `Fallback footage` group 1:1 with no other deck changes. Do not action this today.

## On-Site Projector Test Checklist (3090 / 5090)

Short loop for the venue assembly session. Run end-to-end before adding any Group 2/3 clips.

1. Verify show machine is running native 3840x2160 desktop resolution at the projector.
2. Open Resolume on the show machine; confirm composition output is set to 3840x2160 matching the projector.
3. Load `Fallback footage` group only; trigger `h6_kelp_forest_4k_cropped_50s.mp4` on Layer 2; confirm playback is smooth and no frame drops in 60s.
4. Trigger Evan coastline (`evan_vancouver_island_3840x2160_20s.mp4`) — confirm full-frame fill, no scale artifacts, correct loop.
5. Cycle through the three Moonfish 50s clips; watch for any letterbox-bar irregularity (should be symmetric 80px top + bottom — anything else means a layer-level crop is firing and should be turned off).
6. Run a 30-minute soak on Scene 1 (Fallback only). Watch CPU/GPU load; on the 3090, H.264 4K @ 59.94 should sit well under thermal limits but is the most expensive playback path. If load is high, HAP transcode moves up the priority list.
7. Dim the gallery lighting to show conditions; confirm the letterbox bars on H6 / Moonfish clips read as cinema framing, not as visible matte error.
8. Toggle the `Fallback footage` group mute on and off — confirm a clean cut to black with no flash artifact.
9. Add Scene 2 (Group 2 ON, perspective ripple at 35–55% Screen). Confirm the 1920x1080 v004 clip scales to fill without visible pixelation at viewing distance.
10. Solo-mute every group except `Fallback footage` and confirm the deck reduces to safe-floor state in one operator action. This is the kill-switch test.

If any step 1–4 fails, stop; that is a projector-path or show-machine issue, not a content issue.

## Cross-References

- `docs/space-center/mvp-fallback-resolume-package-2026-05-19.md` — package origin + per-clip spec.
- `track2-deterministic/morph_outputs_INTERNAL/mvp_fallback_package_2026-05-19/README.md` — ffprobe values + ffmpeg invocations.
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v004_2026-05-19/README.md` — v004 clip-by-clip specs.
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v004_2026-05-19/REVIEW_ORDER.md` — Darren's v004 review notes (internal review; not Austin feedback).
- `docs/space-center/resolume-wide-wall-composition-plan-2026-05-18.md` — composition-level layer plan and options A–D.
- `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md` — why the prompt/dream system is parked for IMPACT.
- `docs/space-center/resolume-show-package-checklist-2026-05-14.md` — folder-shape conventions for handoff packages.
