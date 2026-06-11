# TouchDesigner Mudra Scrubber Demo - 2026-05-18

## Status

Internal demo-ready TouchDesigner prototype. The hand/mudra scrubber now has
these preserved branches:

- Raven Sun -> Cosmic Sun endpoint_correct_v001 is the preferred deterministic
  scrub-ready transition for testing the TD interaction layer on a clean
  same-viewBox pair.
- Primitive Cycle and Primitive Field v001 are low-load gesture-control
  fallbacks.
- Cosmic Sun -> Salmon v006 remains preserved as the more ambitious guided
  cross-piece branch, not the next default scrubber.

## Artifacts

- Workspace TOE: `td/templates/ssd_morph_mudra_workspace_template_v006_frame_sequence_scrub.toe`
- Reusable TOX: `td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox`
- Frame sequence: `td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/`
- Output TOP path used in the saved workspace: `/project1/ssd_morph_mudra_scrubber/out_morph`

Raven Sun -> Cosmic Sun v001:

- Workspace TOE: `td/templates/ssd_morph_mudra_workspace_raven_cosmic_v001.toe`
- Workspace with fallbacks: `td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe`
- Reusable TOX: `td/templates/ssd_morph_mudra_scrubber_raven_cosmic_v001.tox`
- Preferred frame sequence: `td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_frames/`
- Preferred preview MP4: `td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_preview.mp4`
- Superseded/control frame sequence: `td/templates/assets/raven_sun_to_cosmic_sun_scrub_frames_v001/`
- Superseded/control preview MP4: `td/templates/assets/raven_sun_to_cosmic_sun_scrub_preview_v001.mp4`
- Output TOP path: `/project1/ssd_morph_mudra_scrubber_raven_cosmic/out_morph`
- Control CHOP path: `/project1/ssd_morph_mudra_scrubber_raven_cosmic/morph_control`

Low-load fallback scrubbers:

- Primitive Cycle TOX: `td/templates/ssd_morph_mudra_scrubber_primitive_cycle_v001.tox`
- Primitive Cycle frames: `td/templates/assets/primitive_cycle_scrub_frames_v001/`
- Primitive Cycle output TOP: `/project1/ssd_morph_mudra_scrubber_primitive_cycle/out_morph`
- Primitive Field TOX: `td/templates/ssd_morph_mudra_scrubber_primitive_field_v001.tox`
- Primitive Field frames: `td/templates/assets/primitive_field_scrub_frames_v001/`
- Primitive Field output TOP: `/project1/ssd_morph_mudra_scrubber_primitive_field/out_morph`

## Cosmic Sun → Salmon v007 landmark-routing (NEW overnight 2026-05-18 AM)

Newer sibling of v006. Uses Lane 2E landmark-atom routing (Codex worker
built). Smoother endpoint settle than v006; recommended over v006 for new
TD scrubber builds.

- Frame sequence: `td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/`
- Frame count: 120, 24fps, 5sec
- Pack README: `td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/README.md`
- Source clip: `track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4`

TD wiring: re-point any existing v006 scrubber TOX (e.g.
`ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox`) to
this v007 frame folder. Same `progress` 0..1 → frame index mapping.

Verification: `progress=0` → `frame_0001.jpg`; `progress=1` → `frame_0120.jpg`.

## Overnight inventory snapshot (2026-05-18 AM)

6 frame-sequence packs available in `td/templates/assets/`, all with READMEs:

| Pack | Frames | Notes |
|---|---|---|
| `cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/` | 120 | original v006 |
| `cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/` | 120 | **NEW — recommended over v006** |
| `raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_frames/` | 120 | **preferred Raven -> Cosmic baseline; derived from endpoint_correct_v001** |
| `raven_sun_to_cosmic_sun_scrub_frames_v001/` | 120 | superseded/control Raven -> Cosmic pack |
| `primitive_cycle_scrub_frames_v001/` | 120 | low-load fallback |
| `primitive_field_scrub_frames_v001/` | 120 | low-load fallback |

## What Changed In v006

The prior Movie File In TOP path updated its index value, but decoded pixels did
not change reliably. v006 switches the visual source to a 120-frame image
sequence:

```text
frame_0001.jpg ... frame_0120.jpg
```

The `progress` value now directly selects a frame from the sequence. Verification
from the worker run:

- `progress=0` uses `frame_0001.jpg`
- `progress=1` uses `frame_0120.jpg`
- Output frames at progress 0 and 1 differ across the full image bounds
- No movie decode errors

## Demo Steps

1. Open `td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe`.
2. Open/view `/project1/ssd_morph_mudra_scrubber_raven_cosmic/out_morph`.
3. Manually scrub `progress` from 0 to 1 to show Raven Sun -> Cosmic Sun moving.
4. Switch to hand-control mode and show that gesture/control input can scrub the morph.
5. If the Austin-specific transition feels too visually loaded for a control
   demo, switch to `/project1/ssd_morph_mudra_scrubber_primitive_cycle/out_morph`
   or `/project1/ssd_morph_mudra_scrubber_primitive_field/out_morph`.
6. If needed, show the preserved Cosmic Sun -> Salmon branch at
   `/project1/ssd_morph_mudra_scrubber/out_morph` as the harder guided-transition
   experiment.
7. Reset the active branch to `progress=0` before handing off.

## Raven -> Cosmic v001 Notes

The original Raven Sun -> Cosmic Sun TD pack was generated from verified
endpoints and atom metadata, but the preferred 2026-05-18 pack now comes from
the reviewed endpoint-correct deterministic MP4:

- `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`
- `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`
- `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4`

The preferred 2026-05-18 pack now comes from
`raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4`: frame 0 and the final
frame match the verified training JPG endpoints, while the middle preserves the
successful deterministic same-viewBox shape morph. The older particle/atom TD
pack remains preserved as a superseded/control asset.

The Raven/Cosmic installer now points at the endpoint-correct frame pack. A saved
workspace opened from before this packaging pass may still point at the
superseded/control frame pack until the component is refreshed.

Existing TD verification for the frame-sequence scrubber shell:

- `progress=0` loads `frame_0001.jpg`
- `progress=0.5` loads a distinct middle frame
- `progress=1` loads `frame_0120.jpg`
- Saved TD outputs at progress 0, 0.5, and 1 differ across the full image bounds
- 2026-05-18 follow-up: the overlay composite order was fixed so `out_morph`
  visibly shows the slider/status overlay; if it stays on Raven, check
  `hand_present`, `hand_count`, and `/project1/MediaPipe/hands`.
- 2026-05-18 follow-up 2: the control driver now prefers true hand/pinch
  landmarks, but falls back to `/project1/MediaPipe/pose` wrist landmarks when
  `/project1/MediaPipe/hands` is empty. This keeps the scrubber usable when the
  MediaPipe gesture model fails while pose tracking remains live.

## Primitive Fallback Notes

Primitive cycle and primitive field were converted into 120-frame scrub assets
from the existing internal review clips. They use the same pinch/manual control
shell and are meant as lower cultural-load demos of the interaction itself.

Fresh TD verification from the worker run:

- Primitive Cycle: progress 0.5 differs strongly from progress 0 and 1; progress
  0 and 1 are intentionally near-loop points.
- Primitive Field: progress 0, 0.5, and 1 all produce distinct output frames.

## Framing For Pravin / Team

This is a control-surface proof: deterministic Austin-derived morph frames can be
scrubbed live in TouchDesigner. The next production question is which morph
pairs are worth turning into scrub-ready frame sequences.

Do not frame this as approved show content. It carries Austin Harry's visual
vocabulary and remains internal until Austin gives per-output OK.

## Next Work

1. Exercise Raven -> Cosmic in TD first; if the interaction layer feels clean,
   decide whether this pair needs a better non-particle morph sequence.
2. Use Primitive Cycle / Primitive Field when the demo needs a lower-load
   interaction proof.
3. Cosmic Sun -> Salmon Spawn: keep refining because v006/v007 became the best
   cross-piece primitive-motion candidate; useful for testing meaningful
   transition guidance, but do not make it the next default TD scrubber unless
   Raven -> Cosmic works cleanly.
4. Raven Sun -> Salmon Spawn: visually interesting but still has source
   layering/endpoint issues; ask-first candidate, not a lead demo.
5. Wolf Whorl -> Salmon Spawn: technically interesting symmetry pair but higher
   cultural load. Keep internal and do not foreground without Austin-guided
   framing.
