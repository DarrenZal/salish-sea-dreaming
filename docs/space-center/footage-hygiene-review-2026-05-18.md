# Footage Hygiene Review - 2026-05-18

No generation, no SD, no LoRA. This is a pre-call production-viability pass over available footage for Tuesday projector testing / Resolume background use.

## Outputs

- Visual index: `track2-deterministic/morph_outputs_INTERNAL/footage-hygiene-review-2026-05-18/footage_hygiene_visual_index_reviewed_2026-05-18.jpg`
- Raw specs: `track2-deterministic/morph_outputs_INTERNAL/footage-hygiene-review-2026-05-18/footage_specs_reviewed.json`
- Moonfish originals list: `track2-deterministic/morph_outputs_INTERNAL/footage-hygiene-review-2026-05-18/moonfish_originals_uninspected_due_hydration.json`

## Reviewed Clips

| clip | resolution | duration | fps | watermark / burn-in | recommendation |
|---|---:|---:|---:|---|---|
| Evan Vancouver Island 4K 20s | 4096x2160 | 20.00s | 24.00 | No visible watermark in sampled frames | Clean enough for Tuesday projector testing and Resolume background. Strong non-underwater Vancouver Island atmosphere layer. |
| H1 salmon school local | 1920x1080 | 59.93s | 59.94 | Visible filename / source-timecode burn-in at bottom edge | Technical test only as-is. Could be used for internal projector motion checks; not clean background unless cropped/matted or replaced from original. |
| H6 kelp forest floor local | 1920x1080 | 49.82s | 59.94 | Visible filename / source-timecode burn-in at bottom edge | Good content, but technical test only as-is. Prefer the 4K copy for projector work. |
| H6 kelp forest floor 4K local | 3840x2160 | 50.05s | 59.94 | Visible filename / source-timecode burn-in at bottom edge | Best underwater background candidate if cropped/matted to hide lower burn-in. For clean public/show use, locate clean master or render a cropped delivery. |
| H7 spawn feast local | 1920x1080 | 39.04s | 29.97 | Visible filename / source-timecode burn-in at bottom edge | Technical / texture test only as-is. Drone/aerial view is useful, but lower-res and visibly burned-in. |
| H6 kelp forest floor 4K Proton projector copy | 3840x2160 | 50.05s | 59.94 | Visible filename / source-timecode burn-in at bottom edge | Same recommendation as local 4K H6: viable for Tuesday testing with crop/matte; not clean as a public-ready master. |

## Moonfish Originals

Accessible by path in Proton Drive:

- `Moonfish Originals/underwater/P1000011.mp4`
- `Moonfish Originals/underwater/P1077716.mp4`
- `Moonfish Originals/underwater/P1099653.mp4`
- `Moonfish Originals/underwater/P1111509.mp4`
- `Moonfish Originals/underwater/P1111707.mp4`
- `Moonfish Originals/underwater/P1111785.mp4`

These were not fully inspected in this pass. The first original probe stalled while Proton Drive hydrated the file on demand, so I stopped the original-file scan rather than blocking the pre-call report. These originals are the right next hygiene target because they may be cleaner than the hero subclip exports with timecode burn-in.

## Recommendation

For Tuesday projector / Resolume testing:

1. Use Evan Vancouver Island 4K as the clean non-underwater background.
2. Use H6 4K kelp forest floor as the primary underwater test background only with a bottom crop/matte or safe overscan that hides the burn-in.
3. Keep H1 and H7 as internal technical motion tests until clean masters or cropped deliveries are prepared.

For production hygiene before anything public-facing:

- Hydrate the Moonfish original underwater files from Proton Drive.
- Inspect whether the originals are free of filename/source-timecode burn-in.
- If clean, rebuild H1/H6/H7 hero subclips from originals.
- If not clean, make explicit cropped/matted Resolume-ready delivery versions and document the crop.
