# Prompt-to-Primitive Scene Review Index - 2026-05-19

Scope: Worker C prompt-to-primitive work only.

**Caveat:** INTERNAL / grammar-inspired sketches. These are not Austin Harry artwork, not public cultural claims, and not claims about traditional meaning. They are procedural review artifacts for testing whether visitor prompts can become simple primitive scenes without Stable Diffusion as the core renderer.

## Source Links

- Design spec: [prompt-to-primitive-scene-pipeline-2026-05-19.md](prompt-to-primitive-scene-pipeline-2026-05-19.md)
- Renderer: [render_primitive_scene_recipe.py](../../track2-deterministic/scripts/render_primitive_scene_recipe.py)
- Contact sheet: [contact_sheet_prompt_to_primitive_scene_library_2026-05-19.png](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/contact_sheet_prompt_to_primitive_scene_library_2026-05-19.png)

## Show Order

1. **Rain first** - strongest primitive-water sequencing test.
2. **Tanker second, Pravin only** - useful world-content stress test, but keep it out of Austin-first review until framing is settled.
3. **Mist as ambient** - background/transition layer, not a featured proof.
4. **Whale as system proof** - readable prompt-to-scene proof, but v002 should move away from generic icon animation.

## Clip Index

| Order | Clip | Recipe | Midpoint still | Verdict | Show to |
|---|---|---|---|---|---|
| 1 | [rain_over_pond_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/rain_over_pond_primitive_v001/rain_over_pond_primitive_v001.mp4) | [rain_over_pond_primitive_v001.json](../../track2-deterministic/scene_recipes/rain_over_pond_primitive_v001.json) | [01_rain_over_pond_midpoint.png](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/midpoint_stills/01_rain_over_pond_midpoint.png) | Best review candidate: circle impact, crescents, and trigons read closest to Austin's water-ripple sequencing. | Pravin + Austin |
| 2 | [tanker_in_burrard_inlet_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/tanker_in_burrard_inlet_primitive_v001/tanker_in_burrard_inlet_primitive_v001.mp4) | [tanker_in_burrard_inlet_primitive_v001.json](../../track2-deterministic/scene_recipes/tanker_in_burrard_inlet_primitive_v001.json) | [02_tanker_in_burrard_inlet_midpoint.png](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/midpoint_stills/02_tanker_in_burrard_inlet_midpoint.png) | Readable world-content test, but still too icon-like; use to test low-cultural-load industrial prompts and Resolume layering. | Pravin only |
| 3 | [mist_cloud_water_cycle_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/mist_cloud_water_cycle_primitive_v001/mist_cloud_water_cycle_primitive_v001.mp4) | [mist_cloud_water_cycle_primitive_v001.json](../../track2-deterministic/scene_recipes/mist_cloud_water_cycle_primitive_v001.json) | [03_mist_cloud_water_cycle_midpoint.png](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/midpoint_stills/03_mist_cloud_water_cycle_midpoint.png) | Good ambient water-state layer; too generic as a featured scene without stronger composition. | Pravin; Austin only for four-state-water discussion |
| 4 | [whale_breach_primitive_v001.mp4](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_whale_breach_v001/whale_breach_primitive_v001.mp4) | [whale_breach_primitive_v001.json](../../track2-deterministic/scene_recipes/whale_breach_primitive_v001.json) | [04_whale_breach_midpoint.png](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/midpoint_stills/04_whale_breach_midpoint.png) | System proof that prompt -> scene graph -> primitives -> MP4 works; v002 should start from ripple sequencing before resolving the whale. | Pravin only unless reframed as technical proof |

## Resolume Notes

- Use the library MP4s as black-background `Screen` blend clips.
- Keep this layer group separate from Austin-derived source-art layers.
- Start opacity at 20-45% over footage, 60-100% for review on black.
- Rain has an optional transparent PNG sequence at [rain frames_alpha](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/rain_over_pond_primitive_v001/frames_alpha/).
- Do not add SD/LoRA finish until primitive layout and review framing are accepted.

