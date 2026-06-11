# Austin SD/LoRA Affordance Menu - 2026-05-18

Internal review aid. Not public/show material without Austin per-output approval.

## Framing

This is not a menu of "AI in Austin's style." It is a menu of constrained roles
that SD, ControlNet, masks, and the Austin v2 LoRA could play around
deterministic/vector material.

Baseline rule:

- Deterministic/vector geometry owns the work; SD/LoRA can only add finish,
  atmosphere, or background in explicitly allowed regions.
- Austin controls source pieces, pairings, endpoint approval, masks, language,
  and final output approval.
- No prompt-only Austin-style creatures.
- No new Austin-like figures, crests, clan beings, or ceremonial imagery.
- If model output closes or fills Austin's negative-space linework, it has
  exceeded its role.

## Controlled Option Set

| # | Option | Status | Reference artifact / proposed test | Austin controls | Model allowed to change | Locked | Cultural risk | Useful for this week's show |
|---|---|---|---|---|---|---|---|---|
| 1 | Deterministic Raven->Cosmic baseline with exact original endpoints | Existing proof | `track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/01_lead_with/05_raven_sun_to_cosmic_sun_shape_morph.mp4` and `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4` | Whether this pair is an approved relationship; morph timing; endpoint use; whether it can enter the show | Nothing. No model layer. | Original endpoint geometry, palette, negative space, all linework, source-file boundaries | Medium; lower than high-load clan/supernatural pairs, but still Austin-derived and relationship-bearing. | Yes. This is the safest structural anchor and should remain the reference/control. |
| 2 | SD/LoRA finishing pass on baseline with endpoint geometry protected | Existing proof | 768 scheduled: `track2-deterministic/morph_outputs_INTERNAL/austin-cn-lora-raven-cosmic-endpoint-scheduled-2026-05-18-results/raven_cosmic_endpoint_scheduled_2026-05-18__canny__endpoint_scheduled_lora035_d30_cn078to100.mp4`; 16:9 UHD: `track2-deterministic/morph_outputs_INTERNAL/austin-raven-cosmic-uhd-surround-fill-endpoint-scheduled-4sec-2026-05-18-results/raven_cosmic_endpoint_scheduled_lora035_d30_uhd_surround_fill_3840x2160_4sec.mp4`; comparison: `track2-deterministic/morph_outputs_INTERNAL/austin-raven-cosmic-endpoint-scheduled-comparison-2026-05-18/raven_cosmic_baseline_crossfade_endpoint_scheduled_side_by_side_3840x720_4sec.mp4` | Whether low-scale Austin LoRA can act as finish; acceptable warmth/texture level; mask strictness; projector use | Subtle texture, warmth, atmospheric finish, soft projection richness in non-protected areas | Exact endpoints, linework, white/cream negative-space cuts, source motion, source composition. Endpoint schedule: denoise/LoRA to 0, ControlNet to 1.0 | Low to moderate. Safer than free generation, but still a neural derivative of Austin source material and must stay internal until approved. | Yes, if Austin likes the look. Candidate finishing lane for Raven->Cosmic because the new schedule fixes the endpoint negative-space bleed. |
| 3 | Masked img2img where only background/atmosphere changes | Proposed single test, not rendered yet | Use the same Raven->Cosmic deterministic or endpoint-scheduled source. Build a mask that excludes all Austin linework, fills, face details, rays, and negative-space cuts; allow only outer background/surround fields to receive atmosphere. | Mask boundaries; whether any background treatment is appropriate; atmosphere vocabulary; whether it can sit behind/around his work | Background glow, ocean/space haze, projection-field color, very soft grain, light movement outside Austin forms | All Austin shapes, linework, fills, negative spaces, endpoints, figure identity, and formline geometry | Low to moderate. Lower than full-frame LoRA finishing because Austin forms are locked, but still adjacent to his work. | Yes as a safer fallback if full-frame finish feels too invasive. Useful for projection richness without touching the art. |
| 4 | Primitive-only img2img/ControlNet material study using synthetic Circle/Crescent/Trigon, no Austin piece | Proposed single test, with prior related proof | Related existing motion proof: `track2-deterministic/morph_outputs/exp1_three_primitives_cycle_2026-05-16.mp4`; related internal finish proof: `track2-deterministic/morph_outputs_INTERNAL/austin-cn-lora-finish-primitive-cycle-full-2026-05-18-results/primitive_cycle_full_finish_2026-05-18__canny__default_lora035_d30.mp4`. New test should use synthetic Circle/Crescent/Trigon masks only, no Austin source piece. No prompt-only Austin-style generation. Austin LoRA only if explicitly framed as an internal finish test, not authorship. | Which three forms are correct; orientation; color/material bounds; whether these are useful as pearl-interior vocabulary; whether Austin LoRA should be excluded or allowed only as internal finish | Material, lighting, surface, depth, pearl/ocean/space feel around synthetic primitives. If Austin LoRA is used, it may only act as low-scale finish. | The three primitive silhouettes, cycle/order if animated, no Austin source geometry, no new beings, no prompt-only Austin-style generation | Low to medium. The geometry is abstract/synthetic, but using Austin LoRA raises it above a purely non-Austin primitive study; terminology and relationship among the three forms still need Austin's guidance. | Yes as a low-cultural-load support layer for the pearl interior, especially if Austin wants grammar without showing specific pieces. |
| 5 | Non-Austin atmospheric text-to-image study for pearl/ocean/space projection background | Proposed single test, not rendered yet | One still or short loop generated without Austin LoRA and without Austin motifs. Prompt should target non-figural pearl/ocean/space atmosphere only. | Whether this kind of atmosphere belongs near his work; palette; density; whether it should be separate from or behind his material | Abstract light, water, particles, cosmic haze, pearl refraction, projection background motion | No Austin source material, no Coast Salish motifs, no creatures, no crests, no formline-like invented designs, no text/logos/watermarks | Low if kept purely atmospheric and non-motif. Risk rises if it starts resembling cultural design language. | Yes as a venue/projection background or fallback fill, especially for Resolume layers that should not depend on Austin-derived generation. |

## Recommended Review Order

1. Show Option 1 first as the structural baseline.
2. Show Option 2 next as the most promising constrained finishing layer.
3. Ask whether Option 3 is a safer direction if full-frame finish feels too
   invasive.
4. Use Option 4 to discuss the three-shape grammar without specific Austin
   pieces.
5. Use Option 5 only as a projection-background question, not as Austin-style
   generation.

## Austin Questions

1. Does the deterministic Raven->Cosmic relationship feel like an appropriate
   relationship to explore?
2. In the endpoint-protected finish, is the model's role acceptable as
   atmosphere/finish, or does even that feel too close to authorship?
3. Would you rather the neural layer touch only background/surround fields and
   never touch your linework?
4. For the primitive-only lane, are Circle/Crescent/Trigon the right forms,
   and are the orientations/cycle order meaningful or wrong?
5. Should non-Austin atmospheric backgrounds stay visually separate from your
   pieces, or can they sit behind/around them as projection context?

## Week-Of-Show Recommendation

Use Option 1 as the control and Option 2 as the candidate show-facing finish
only if Austin approves the specific output. Keep Option 3 as the safer fallback
because it can add projection atmosphere without changing Austin geometry. Use
Option 4 only for abstract pearl/primitive context. Use Option 5 for
non-Austin projection fill and venue atmosphere.

Do not spend more time this week making more LoRA variants. The useful next
work is mask discipline, endpoint protection, and choosing which affordance
Austin is comfortable with.
