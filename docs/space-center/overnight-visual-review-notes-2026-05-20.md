# Overnight Visual Review Notes - 2026-05-20

Status: INTERNAL review notes from Darren. Not Austin-approved. Not public-ready.

## Agent B - Primitive Cycle v002

Packet:

- `track2-deterministic/morph_outputs_INTERNAL/primitive_cycle_motion_v002_2026-05-20/`

Review:

- `single_shape_cycle_v002.mp4` looks nice. It is a good primitive proof.
- However, it does not replace the earlier field-scale primitive-cycle work. Darren remembers the older field shown to Austin/Pravin as more interesting because many primitives were cycling together.
- Earlier field references to compare against:
  - `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4`
  - `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4`
  - `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light.mp4`
- `eye_flow_phrase_v002.mp4` is technically right. It matches Austin's explanation of eye flow: circle focal point, then crescent/crescent/trigon direction.

Implication:

- Do not keep iterating only on a single isolated glyph. The stronger next primitive-cycle pass should combine B's cleaner v002 primitive transformation with the older richer field-scale behavior.
- Next target: `primitive_field_cycle_v003` - a field of many clean primitive-cycle phrases, with authored flow/common-fate, not random scatter.

## Agent A - Water Flow Phrase Grammar v001

Packet:

- `track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v001_2026-05-20/`

Review:

- `current_streamline_field_v001.mp4` looks awesome. This is a lead internal review candidate.
- `waterfall_vertical_phrase_v001.mp4` also looks awesome. This is another lead internal review candidate.
- `river_s_curve_phrase_v001.mp4` remains useful as a path-led water grammar test.
- `pond_ripple_phrase_v001.mp4` is less emphasized by this review; keep it behind the stronger current/waterfall work unless later motion review changes that.

Implication:

- The water-flow lane is not a side lane. It is currently one of the strongest outputs and is closer to the 2026-05-18 Austin/Pravin pivot than the topology/cymatics lane.
- Next target: v002 should refine `current_streamline_field` and `waterfall_vertical_phrase`, then optionally composite them over H6 / Moonfish footage at low opacity for Resolume review.

## Current Lead R&D Order

1. Water flow / current grammar: `current_streamline_field_v001`, `waterfall_vertical_phrase_v001`.
2. Primitive cycle / field grammar: combine the new clean cycle with older field-scale primitive-field work.
3. Topology/cymatics: still promising, but requires the region-taxonomy correction before the next render pass.
4. Prompt/dream-to-primitive: architecture lane, not the visual lead today.
5. Functional salmon/birds: parked unless they become real motion systems.

## Do Not Flatten This Review Into One Lane

The topology/cymatics packet is not the whole primitive-shape program. The project now has at least three serious abstract-shape lanes:

- primitive cycle / transformation grammar;
- water-flow / current-following phrase grammar;
- topology / cymatics / radial geometry.

The strongest immediate visual signal from this review is the Agent A water-flow work plus a revived field-scale primitive-cycle pass.
