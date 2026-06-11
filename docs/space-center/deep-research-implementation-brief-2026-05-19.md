# Deep Research Implementation Brief - 2026-05-19

Date: 2026-05-19
Role: Agent C - deep research integration and review strategy
Status: internal production brief

## Production Decision

Lead with the 2D primitive water grammar: circle, crescent, trigon. The broad Austin style-transfer lane stays dropped. The Hubble wide wall gets the stable fallback first, then sparse primitive grammar layers once review framing is clear.

For today, the highest-value move is not a new render. It is a disciplined review sequence: prove that the optical-flow primitive layer can sit over water/kelp without over-claiming cultural meaning, then ask Austin the minimum set of boundary questions before making the salmon/body-center version a visual direction.

## Immediate Changes for Agent B v002/v003

### v002 Review Strategy

Do not change the current v002 packet before the Pravin/Austin review. Use it as a review artifact, not as final show media.

The first clip should be the H6 ocean/kelp optical-flow composite because it keeps the cultural load abstract and avoids putting primitives directly on animal bodies:

[01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4)

Then show the matching black-background layer-only version to explain how the same motion grammar can become a Resolume `Screen`/additive layer over clean footage:

[02_ocean_kelp_optical_flow_v002_layer_only_black_screen.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/02_ocean_kelp_optical_flow_v002_layer_only_black_screen.mp4)

Only then show the salmon proxy, and only for the boundary question: is a circle over salmon body centers acceptable?

[03_salmon_school_proxy_v002_composite_H1_source_burnin.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/03_salmon_school_proxy_v002_composite_H1_source_burnin.mp4)

### v003 Implementation Notes

- Keep H6 ocean/kelp as the lead visual lane. It is the best bridge between stable fallback footage and the primitive grammar.
- Prefer sparse optical-flow phrases over object detection. Dense flow plus temporal smoothing degrades gracefully in turbid footage; segmentation is optional polish.
- Keep black-background layer-only renders as the Resolume target. Source composites are for review only, especially while burn-in is visible in source footage.
- Reduce density before adding features. The reports converge on "common fate" and ordered motion as the thing that makes water read as water; extra particles read as noise.
- Use temporal EMA, spatial smoothing, and a magnitude gate as non-negotiable flow hygiene. If the raw flow jitters, the glyphs will read as nervous rather than meditative.
- Keep the phrase order visible but understated: circle -> crescent -> crescent -> trigon. Do not over-explain it in the visual itself.
- If salmon-body circles are rejected, redirect circles to water impact anchors, current knots, or phrase origins near but not on bodies.
- After Austin review, render the accepted layer-only variant at the Hubble wall target resolution rather than stretching a 1080p layer.
- Add sidecar data only if it is cheap: per-frame anchors, direction vectors, and primitive phrase ids would help later TouchDesigner/Resolume debugging, but should not displace visual review work today.
- Keep all Austin/culturally derived outputs internal until Austin reviews them.

## Prompt-to-Primitive Pipeline Later

The prompt-to-primitive system remains promising, but it is not the visual lead today. It should become a controlled scene-recipe lane after the water grammar is reviewed.

Carry forward:

- Use constrained scene recipes and deterministic layout. The LLM, if used later, chooses semantic intent, zone, layer, and motion template; it does not choose raw pixel coordinates.
- Narrow the public-facing vocabulary to circle, crescent, and trigon. Helper fields, lines, and bands can exist internally if the renderer needs them, but review language should stay focused on the three-shape grammar.
- Build from low-cultural-load water-state prompts first: rain over pond, mist, ocean swell, river/current. These test motion without invoking specific beings or high-load stories.
- Use pure black background for screen-blend delivery and keep the primitive layer easy to mute.
- Add schema fields for `cultural_load`, `review_required`, and `render_policy` before connecting the lane to visitor prompts.
- Treat "reads as the prompt" as human review, not an automatic metric.
- Keep all seeds deterministic and store recipes next to outputs so any clip can be reproduced.

Defer:

- Live Spout/Syphon/NDI.
- Prompt repair loops.
- More scene categories.
- Diffusion finishing.
- Automatic prompt-readability evaluation.

## What to Show Pravin Today

Start with the production frame: stable fallback is the floor, primitive water grammar is the innovation layer, and anything Austin-derived is behind review.

Show in this order:

1. H6 ocean/kelp optical-flow v002 composite.
2. H6 ocean/kelp v002 layer-only black clip.
3. Salmon proxy v002, framed only as the Austin boundary question.
4. Rain-over-pond prompt sketch as the secondary proof of the prompt-to-primitive lane.
5. Tanker only for Pravin as a world-content stress test.
6. Whale only as a technical proof that prompt -> recipe -> primitives -> MP4 works, not as a visual lead.

Pravin decision asks:

- Does the H6 primitive layer feel worth putting above the fallback wide-wall footage today?
- Should the operator plan around `Screen`/additive black-background primitive clips rather than source-composited clips?
- Is tanker/industry useful as a Pravin-only stress test for low-cultural-load prompts?
- Is the prompt-to-primitive lane worth continuing after the Austin grammar review, or should all effort stay on optical-flow water?

## What to Show Austin on Wed May 20

Frame everything as internal grammar-inspired sketches for critique. Do not call them Austin artwork, do not claim traditional meaning, and do not ask Austin to approve a whole pipeline at once.

Austin sequence:

1. H6 ocean/kelp optical-flow composite: "Does this use of circle/crescent/trigon over water/current feel like a direction we can keep exploring?"
2. H6 layer-only black clip: "This is the same layer without footage, so it can sit over cleaner wide-wall media."
3. Salmon proxy: "Boundary question only: is a circle over salmon body centers acceptable, or should circles be impact/current anchors instead?"
4. Rain-over-pond sketch: "Separate prompt-to-primitive proof. Are new low-cultural-load water scenes made from this primitive grammar acceptable as internal sketches?"
5. Do not show tanker unless Pravin thinks the industrial/world-content framing needs Austin input.
6. Do not lead with whale. If shown, frame it as a technical pipeline proof that still needs grammar correction.

## Review Order

1. Agent B v002 ocean/kelp optical-flow composite first:
   [01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4)
2. Agent B v002 ocean/kelp layer-only black clip second:
   [02_ocean_kelp_optical_flow_v002_layer_only_black_screen.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/02_ocean_kelp_optical_flow_v002_layer_only_black_screen.mp4)
3. Agent B v002 salmon proxy third, only for the Austin boundary question:
   [03_salmon_school_proxy_v002_composite_H1_source_burnin.mp4](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/03_salmon_school_proxy_v002_composite_H1_source_burnin.mp4)
   Question: is a circle over salmon body centers acceptable?
4. Rain-over-pond prompt sketch as secondary proof of the prompt-to-primitive system:
   [rain_over_pond_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/rain_over_pond_primitive_v001/rain_over_pond_primitive_v001.mp4)
5. Tanker only for Pravin unless framing is needed:
   [tanker_in_burrard_inlet_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/tanker_in_burrard_inlet_primitive_v001/tanker_in_burrard_inlet_primitive_v001.mp4)
6. Whale only as technical proof, not visual lead:
   [whale_breach_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_whale_breach_v001/whale_breach_primitive_v001.mp4)

## Top 10 Actionable Recommendations

1. Lead every review with the H6 ocean/kelp v002 optical-flow composite. It has the best production value because it tests the real direction with the lowest cultural load.
2. Immediately follow with the H6 layer-only black clip. This moves the conversation from "nice composite" to "usable Resolume layer over the wide-wall fallback."
3. Keep the salmon proxy out of the lead position. Use it only to ask whether body-center circles are acceptable.
4. For v003, spend effort on flow smoothing and sparse phrase placement, not detection. EMA, spatial blur, magnitude gates, and fewer anchors matter more today than object labels.
5. Use a restrained ivory/pale-cyan-on-black palette. Debug colors, outlines, and semantic color-coding should stay out of Austin-facing review.
6. Align the accepted v003 layer-only render to the Hubble wall target after review. Do not spend today fighting 4K output before the grammar direction is accepted.
7. Recast any rejected salmon-body circle as an impact/current anchor. This keeps the technical pipeline useful even if the body-center interpretation is not acceptable.
8. Keep rain-over-pond as the prompt-to-primitive proof. It best demonstrates circle impact, crescent ripple, and trigon attenuation without an animal or industrial subject.
9. Park tanker as Pravin-only unless Austin boundary framing is required. It is a useful world-content test but still reads too icon-like.
10. Preserve recipe/provenance notes for every review clip. Reproducibility and clear "internal only" labeling are part of production safety, not paperwork.

## Questions for Austin

- Should circle lead motion, sit on body centers, or mark impact anchors?
- Which way should crescents cup relative to impact or travel?
- Should trigons point with flow or mark final attenuation?
- Are new low-cultural-load scenes made from primitive grammar acceptable as internal sketches?
- Where is the line between grammar layer and culturally specific figure?

## Do Not Spend Time Today

- SAM/SAM2.
- YOLO unless B's v002 fails badly.
- Alpha codec fights.
- Generic icon-scene generation.
- More SD/LoRA as core renderer.
- TouchDesigner real-time rebuilds.
- External-cultural naming systems or pattern references as review language.
- Thunderbird, Goat-man, double-headed serpent, James Harry model references, or any culturally specific figure until explicit Austin framing is available.

## Parked

- SAM/SAM2 and mask-first segmentation.
- Fish-specific YOLO detector experiments unless optical-flow v002/v003 fails badly.
- Alpha codec delivery and ProRes/DXV/HAP-alpha fights.
- Generic icon-scene expansion in the prompt-to-primitive lane.
- SD/LoRA as a core renderer.
- Real-time Spout/Syphon/NDI.
- TouchDesigner companion renderer.
- Prompt-to-scene LLM integration.
- Automatic "reads as prompt" evaluation.
- Public-facing interpretation of the primitive grammar before Austin review.

## Source Map

Primary research reports:

- [Motion-driven symbolic overlays](/Users/darrenzal/Downloads/compass_artifact_wf-8b20265b-45c8-4755-ada9-83fa16ade49b_text_markdown.md)
- [Fish/salmon detection tactical plan](/Users/darrenzal/Downloads/compass_artifact_wf-bb5ad649-04e1-409b-964a-6683f7f4fbc5_text_markdown.md)
- [Abstract water-cycle motion studies](/Users/darrenzal/Downloads/compass_artifact_wf-b35a3b65-9fad-4463-b79b-00a05a3deb36_text_markdown.md)
- [Diffusion-free prompt-to-abstract-scene pipeline](/Users/darrenzal/Downloads/compass_artifact_wf-f046679f-85ec-46a0-ab5f-9f4ce81cc63e_text_markdown.md)

Project context:

- [2026-05-18 The Salish Sea Dreaming Meeting 2](</Users/darrenzal/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md>)
- [Prompt-to-Primitive Scene Review Index](prompt-to-primitive-scene-review-index-2026-05-19.md)
- [Agent B primitive water grammar v002 README](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/README.md)
- [Agent B primitive water grammar v001 README](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_2026-05-19/README.md)
- [Agent A MVP fallback Resolume package](mvp-fallback-resolume-package-2026-05-19.md)
- [Prompt-to-Primitive Scene Pipeline](prompt-to-primitive-scene-pipeline-2026-05-19.md)
