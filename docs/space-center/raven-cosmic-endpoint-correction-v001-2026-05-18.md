# Raven -> Cosmic Endpoint Correction v001 - 2026-05-18

Bounded production-relevance pass after Bee review. No SD, LoRA, ControlNet, or
diffusion finishing.

## Outputs

- Corrected MP4: `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4`
- Output folder: `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001/`
- Comparison MP4: `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001/current_vs_endpoint_correct_v001_comparison.mp4`
- Comparison contact sheet: `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001/current_vs_endpoint_correct_contact_sheet.png`
- TD scrub frames: `td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_frames/`
- TD scrub preview: `td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_preview.mp4`

## Packaging Status

As of 2026-05-18, operator review marked `endpoint_correct_v001` visually
acceptable enough to become the preferred deterministic Raven -> Cosmic
baseline.

- Packet v2 item #09 now points to this MP4.
- Morning demo folder `2_supporting/06_raven_to_cosmic_clean_morph.mp4` now
  points to this MP4.
- The older `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4`
  remains preserved as a superseded/control artifact at
  `morning-demo-folder-2026-05-18/2_supporting/09_raven_to_cosmic_OLD_SHAPE_MORPH_SUPERSEDED_CONTROL.mp4`.
- The new TD scrub frame pack is derived from this endpoint-correct clip.

## Method

- Uses current deterministic shape-morph frames from
  `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun/` as the motion
  base.
- Forces frame 0 to verified `Animal_Bird_Raven_Sun.jpg`.
- Forces final frame to verified `Nature_Cosmic_Sun.jpg`.
- Rejoins the existing shape morph over the first 12% of the clip.
- Applies diff-weighted final settle from 72% onward so the endpoint correction
  is less like a late full-frame crossfade.

## Metrics

- Current frame 0 vs Raven training JPG mean absolute delta: 15.1409
- Current final vs Cosmic training JPG mean absolute delta: 5.7066
- Corrected frame 0 vs Raven training JPG mean absolute delta: 0.0
- Corrected final vs Cosmic training JPG mean absolute delta: 0.0
- Corrected clip: 1024x1024, 96 frames, 24fps, 4 seconds.

## Read

This is more production-relevant than the Bee branch because Raven -> Cosmic is
already a clean same-viewBox pair and already TD-ready. v001 fixes endpoint
fidelity while preserving the existing morph behavior. It is now the preferred
deterministic baseline, but it is still endpoint correction around the current
shape morph, not a new authored atom grammar.

Internal only; Austin per-output OK required before any public or staged use.
