# Resolume / Wide-Wall Composition Plan - Monday Review

Date: 2026-05-18  
Scope: use existing assets only. No new SD/LoRA renders, no new morphs, no prompt-only Austin-style generation.

Static contact-sheet mockup:
`track2-deterministic/morph_outputs_INTERNAL/resolume-wide-wall-plan-2026-05-18/resolume_wide_wall_layout_options_contact_sheet_3840x2160.png`

## Governing Rule

Austin pieces should remain legible and should not be buried under effects.
Deterministic/vector geometry owns the forms. SD/LoRA is only a finish,
atmosphere, or background layer in explicitly allowed regions.

For Monday review, treat the working canvas as `3840x1080` wide-wall. If the
active projector path is `3840x2160`, keep the same layer logic and center the
wide composition vertically, or build a 16:9 variant with the same hierarchy.

## Proposed Layer Stack

| Order | Layer | Example asset path | Status | Blend | Opacity / scale / placement | Resolume role |
|---|---|---|---|---|---|---|
| 1 | Background / ocean / H6 4K | `media/hero-subclips/H6_kelp_forest_floor_4k.mp4` | Public-safe candidate; non-Austin, still run standard media/license audit before final public use | Normal | 70-90%, darkened; scale-to-cover full wall; slow playback, no fast cuts | Background and safe fallback |
| 2 | Ambient grammar / primitive field | `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4` or `primitive_field_v002_flocking_light.mp4` | Internal-only until Austin/team review; no direct Austin source piece | Screen / Add / Lighten for dark version; Multiply/Overlay for light version | 8-22%; oversized 115-145%; drift slowly; keep behind Austin pieces | Ambient grammar layer and low-risk fallback |
| 3 | Austin piece nodes / isolated figures | `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`, `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`, transparent PNGs in `austin-v2-ingest/approved/` | Austin-OK-required for projector/show use | Normal | 65-100%; one primary figure at a time; center 45-70% wall height or side nodes 18-30% | Foreground subject / graph node |
| 4 | Morph transition layer | Deterministic: `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4`; endpoint-protected finish: `track2-deterministic/morph_outputs_INTERNAL/austin-raven-cosmic-uhd-surround-fill-endpoint-scheduled-4sec-2026-05-18-results/raven_cosmic_endpoint_scheduled_lora035_d30_uhd_surround_fill_3840x2160_4sec.mp4` | Austin-OK-required; relationship-bearing and output-specific | Normal over background; avoid additive blends over linework | Center feature; 55-80% wall height; opacity 100% when featured; do not stack multiple morphs at once | Foreground transition / review candidate |
| 5 | Pearl-bead graph layer | Single-edge: `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4`; multi-pearl: `track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4` | Austin-OK-required as currently rendered because pearls/nodes use Austin source textures; pearl concept also needs framing | Screen / Add for sparse lines; Normal for pearl bead when legibility matters | 20-55%; sparse overlay only; never make it a dense network over the center feature | Relational overlay / transition architecture |
| 6 | TD / gesture interactive layer | `td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe`; Raven/Cosmic TOP `/project1/ssd_morph_mudra_scrubber_raven_cosmic/out_morph`; primitive fallback TOPs documented in `td/templates/README.md` | Primitive fallback: internal-only; Raven/Cosmic scrubber: Austin-OK-required | Normal for scrubbed feature; Add only for gesture feedback | Full center feature or small live window; keep one interactive source active; use primitive scrubber if no Austin approval | Interactive / live control / fallback |
| 7 | Optional SD/LoRA finish layer | Existing endpoint-scheduled Raven->Cosmic finish: `track2-deterministic/morph_outputs_INTERNAL/austin-cn-lora-raven-cosmic-endpoint-scheduled-2026-05-18-results/raven_cosmic_endpoint_scheduled_2026-05-18__canny__endpoint_scheduled_lora035_d30_cn078to100.mp4` | Austin-OK-required; internal until explicit output approval | Normal only; do not use additive effects over linework | Use as an alternate source clip, not a stacked effect; if stacked, <=15% and masked away from linework | Optional finish / A-B review against deterministic |

## Wide-Wall Layout Options

### Option A - Center-Feature Composition

One large Austin piece or Raven->Cosmic morph holds the center. H6 runs behind
it, the primitive field is barely visible as a grammar current, and pearl-bead
traces appear only as sparse relational accents.

- Use when: Austin/team need to judge legibility and cultural feel.
- Suggested stack: H6 at 80%; primitive field dark at 12% Screen; center
  Raven->Cosmic deterministic or endpoint-protected at 100%; sparse pearl-bead
  at 20-30% only during transitions.
- Risk: Austin-OK-required if the center feature uses Austin source.
- Watch point: never let the primitive field or SD finish wash across white
  negative-space cuts.

### Option B - Panoramic Graph / Pearl Journey

The wall becomes a horizontal relationship space: nodes sit left/center/right,
and one or two pearls traverse sparse edges. This should read as a journey, not
as a busy network map.

- Use when: explaining show architecture to Pravin/team.
- Suggested stack: H6 darkened; primitive field at 8-12%; multi-pearl prototype
  or pearl-bead traversal as the central logic layer.
- Risk: Austin-OK-required for current pearl-bead assets because their nodes and
  pearl textures are Austin-derived.
- Watch point: linework inside pearl beads may become too small on projection;
  use fewer, larger pearls if implemented live.

### Option C - Triptych: Ocean Field / Austin Piece / Morph Destination

Three zones across the wall: left ocean/primitive field, center current Austin
piece or morph midpoint, right destination/next state. This is useful for
reviewing a transition without turning the whole wall into one busy composite.

- Use when: reviewing source-to-destination relationships.
- Suggested stack: left H6 + primitive field; center source/morph; right target
  or future node. Use hard zone discipline rather than overlays everywhere.
- Risk: Austin-OK-required for Austin source zones and morph destination.
- Watch point: the side zones should support the center, not compete with it.

### Option D - Ambient Low-Risk Mode: Primitives + H6 Only

No Austin source pieces. H6 carries the environment and primitive-field/cycle
assets carry abstract grammar. If a pearl layer is needed without Austin
approval, use only non-Austin/synthetic pearl visuals such as dry-run primitive
assets, not the Austin-textured pearl-bead graph.

- Use when: venue test, projector alignment, or fallback playlist before Austin
  approves specific outputs.
- Suggested stack: H6 at 85-95%; primitive field dark at 10-18%; optional
  primitive cycle or dry-run pearl container as a small center insert.
- Existing low-risk examples: `track2-deterministic/morph_outputs/exp1_three_primitives_cycle_2026-05-16.mp4`, `track2-deterministic/morph_outputs/_compose_pearl_dry_run.mp4`.
- Risk: internal-only / lower cultural load. Still ask Austin before public
  meaning claims around the pearl or the three forms.
- Watch point: do not imply that primitives alone are Austin's full grammar.

## Top 3 Demoable Looks This Week

| Demo look | Purpose | Recipe | Status / gate |
|---|---|---|---|
| Safe fallback | Something can run on the wall without Austin-piece transformation | H6 4K background + primitive field dark at low opacity + optional primitive cycle insert. No Austin source piece, no SD/LoRA. | Best fallback for technical tests. Public use still needs media/license check and careful pearl/framing language. |
| Austin-review exploratory look | Show the strongest current Austin-derived result while preserving legibility | H6 dimmed behind center Raven->Cosmic deterministic baseline, then A/B with endpoint-protected SD/LoRA finish. Keep the center large and uncluttered. | Austin-OK-required. This is the clearest review prompt for "does finish help or invade?" |
| Ambitious show-architecture look | Demonstrate graph / pearl journey logic | H6 + low primitive field + one large center node/morph + one sparse pearl-bead traversal, with TD scrubber controlling Raven->Cosmic or primitive fallback. | Austin-OK-required for current Austin-derived node/morph/pearl assets. Use as internal team architecture demo first. |

## Resolume Notes

- Build the deck as scenes, not one mega-composition: `Fallback`, `Center
  Feature`, `Pearl Journey`, `Triptych Review`, `TD Live`.
- Keep Austin-derived content on its own layer group with an easy kill switch.
- Put H6 and primitive field on independent global layers so they can continue
  when foreground content changes.
- Use bypass/mute buttons for `SD/LoRA finish` and `pearl-bead graph` so Austin
  review can compare with and without those layers instantly.
- Avoid blur, colorize, feedback, mirror, kaleidoscope, and heavy displacement
  on Austin piece layers. Those effects can be used on H6/background only.
- If TD is live, feed Resolume one clean Spout/NDI source and treat it as the
  active foreground, not as another texture to bury under effects.

## Monday Review Decision Points

1. Which fallback can run during technical setup without waiting on Austin?
2. Which Austin-derived foreground gets first review: deterministic
   Raven->Cosmic, endpoint-protected finish, or TD scrubber?
3. Should the pearl-bead graph be treated as a show architecture layer this
   week, or only as an internal explanation prototype?
4. Is the final show more effective as one center feature at a time, or as a
   triptych relationship view?
5. What is the exact kill-switch plan for all Austin-derived layers in Resolume?
