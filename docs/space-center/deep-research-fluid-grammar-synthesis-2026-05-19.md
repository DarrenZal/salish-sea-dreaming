# Deep Research Fluid / Grammar Synthesis - 2026-05-19

Status: internal orchestration synthesis. No clips rendered. No agent output folders edited.

## Verdict

The three reports agree on a technical pivot:

- Stop iterating the current hand-authored Python water renderer for visual polish.
- Move the water lane to a heightfield / SDF-glyph substrate where circle, crescent, and trigon marks are folded into the water height/normal field, not drawn as separate sprites.
- Use TouchDesigner as the fastest next live/prototype stack for water.
- Use Blender Geometry Nodes / Ocean Modifier as the higher-quality pre-render path for hero clips.
- Keep Resolume playback as the production fallback, preferably DXV3 or HAP, with black-background Add/Screen layers or alpha only when necessary.
- Treat the primitive vocabulary as a real shape grammar with a shared `grammar.json`, so Python, TouchDesigner, Blender, and future web demos use the same primitive parameters.

This changes the next agent move: Agent B should not make v007 by tweaking the existing script. Agent B should either build a minimal TouchDesigner/GLSL spec packet or a Python shader prototype of the heightfield/SDF concept. Agent A stays parked until a new lead clip exists. Agent D should wait for the new substrate decision before refreshing the runbook.

## Source Map

- `/Users/darrenzal/Downloads/compass_artifact_wf-411991c1-9f64-4612-9b94-4b3c88be2ae9_text_markdown.md`
  - Lines 4-6: best ROI is TouchDesigner heightfield + glyph compositing, Blender for hero shots, Three.js only if browser needed.
  - Lines 12-16: heightfield + SDF compositing beats true 3D fluid for this aesthetic; TouchDesigner is primary; Blender Ocean Modifier is easiest deep-ocean generator; RGB-on-black DXV No Alpha + Add is recommended for Resolume.
  - Lines 25-30: ranked top approaches: Gerstner/SDF in TD, Tessendorf/Blender, Stam fluids, Gray-Scott, curl-noise.
  - Lines 38-68: build-today TouchDesigner architecture.
  - Lines 91-116: core embedding rule: put glyph SDF into heightmap, recompute normals, refract glyph through surface, share caustic shading.
  - Lines 318-337: output targets and decision-ready recommendations.
- `/Users/darrenzal/Downloads/compass_artifact_wf-f175854c-d092-4657-8d62-a1bad009e8db_text_markdown.md`
  - Lines 3-6: one-day deterministic Python/SVG scene graph; one-week TD live layer; shape grammar as formal system.
  - Lines 12-20: primitive grammar is expressive enough; three composition strategies; TD to Resolume live path, DXV/HAP fallback.
  - Lines 31-49: formal vocabulary and prompt -> scene graph -> skeleton -> primitives -> animation pipeline.
  - Lines 94-149: one-day and one-week architecture.
  - Lines 218-239: staged recommendations.
- `/Users/darrenzal/Downloads/compass_artifact_wf-d3fa528d-4b4b-4ab7-ada8-df49abbfb411_text_markdown.md`
  - Lines 4-6: hybrid stack: Blender for production pre-renders, TouchDesigner for live boids/water, Three.js/WebGPU for review.
  - Lines 12-22: production fallback should be pre-rendered Resolume clips; real-time live is achievable but not load-bearing; SDF crescent definition; Blender GN instancing on normals; ocean simulation ladder.
  - Lines 53-60: boids and topological neighborhoods for flocking.
  - Lines 76-92: Blender Ocean/GN and TouchDesigner rankings.
  - Lines 120-148: Resolume codec and layer separation strategy.
  - Lines 154-160: silhouette-first 3D grammar and shared `grammar.json`.
  - Lines 160-187: fish-school lead-clip proposal, useful later but not the immediate water-priority lead.

## Synthesis

### 1. Water Should Move To Heightfield Plus SDF Glyphs

The key upgrade is not more primitive placement. It is changing the representation:

1. Generate a water heightfield with Gerstner waves, stable fluids, or FFT/ocean.
2. Rasterize circle/crescent/trigon as signed-distance fields.
3. Fold the glyph SDF into the heightfield before normal generation.
4. Recompute normals from the combined water+glyph field.
5. Shade both water and glyphs with the same caustic/refraction model.
6. Output black-background luminous layers for Add/Screen in Resolume.

This directly addresses Darren's v006 critique: the shapes currently read as particles floating above water. They need to become relief, inlay, refraction, contours, or surface structure inside the water field.

### 2. The Fastest Useful Prototype Is TouchDesigner, Not Another Python MP4 Script

TouchDesigner is the best next substrate because it can combine:

- GLSL TOP heightmaps.
- Feedback TOP / stable-fluid passes.
- Noise and audio modulation.
- SDF glyph rasterization.
- Slope/normal generation.
- Bloom/caustic shader passes.
- Movie File Out for loops.
- Future live path to Resolume.

If TouchDesigner automation is awkward, the fallback is to write a Python/OpenGL or shader-only prototype that renders the same heightfield/SDF method to frames. But the research points to TD as the right target.

### 3. Blender Is The Hero-Clip Path

Blender should be reserved for higher-quality hero shots:

- Ocean Modifier for displaced mesh.
- Geometry Nodes after Ocean to instance glyphs on displaced normals.
- Eevee Next for fast preview, Cycles for caustic hero render.
- Output image sequence / ProRes / DXV or HAP through Alley.

This is probably not the next one-hour agent task unless the team has a Blender-capable worker ready. It is the right one-week quality path.

### 4. Shape Grammar Needs A Shared Spec Before More Figure Work

The primitive scene reports converge on a formal vocabulary:

- `circle`
- `crescent`
- `trigon`
- optional `line`
- optional `oval`

The next reusable artifact should be `grammar.json`: primitive parameters, palette, default stroke/fill behavior, crescent ratio, trigon shape, animation roles, and cultural status notes. That becomes the handshake between C's reference brief, B's rendering, and A/D's review docs.

### 5. Fish/Bird/Flocking Is Real But Should Stay Secondary Today

The 3D/flocking report argues for boids/topological neighborhoods and even proposes a fish-school lead clip. That is compelling, but it is culturally and visually more loaded than water. Given the all-hands pivot and Darren's v006 review, water/membrane should remain the next production-facing experiment. Fish/bird/flocking becomes the next research/prototype lane after the water substrate is corrected.

## Decisions For Today

1. Promote "heightfield + SDF glyph embedding" as the next Agent B technical direction.
2. Do not make v007 from `primitive_water_membrane_v6.py`.
3. Ask Agent C or a fresh agent to create `grammar.json` / primitive vocabulary spec from the reports plus Austin reference docs.
4. Keep Agent A parked until there is either a v007 TD/Python proof clip or a clear "no new lead" decision.
5. Keep Agent D parked until Agent B's new substrate proof and the grammar spec land.

## Recommended Next Agent Assignments

### Agent B - New Water Substrate Proof

Goal: produce a technical proof of embedded glyphs, not a polished art pass.

Deliverables:

- `docs/space-center/heightfield-sdf-water-glyph-prototype-brief-2026-05-19.md`
- A small proof clip if feasible today, under:
  - `track2-deterministic/morph_outputs_INTERNAL/heightfield_sdf_water_glyph_v001_2026-05-19/`
- Renderer/script or TouchDesigner notes, depending on available tooling.

Acceptance criteria:

- Glyphs are folded into a height/normal field or visibly refracted by the surface.
- Crescents do not randomly flip orientation without a surface/tangent reason.
- Output is black-background Add/Screen friendly.
- It is clearly a substrate proof, not Austin-approved art.

### Agent C - Grammar Spec

Goal: turn the research plus Austin reference analysis into a reusable shape grammar contract.

Deliverables:

- `track2-deterministic/primitive_grammar/grammar_v001.json`
- `docs/space-center/primitive-grammar-contract-2026-05-19.md`

Acceptance criteria:

- Defines circle/crescent/trigon/oval/line parameters.
- Distinguishes water roles, fish roles, bird roles, sun/sky roles, and blocked/high-review roles.
- Includes palette and projection constraints.
- Includes cultural-status fields: internal, Austin-review-needed, public-blocked.
- Designed for Python/TD/Blender interoperability.

### Agent D - Later Refresh

Wait. D should refresh the final review runbook only after B's new substrate proof and C's grammar contract exist.

## What Not To Do Next

- Do not continue v006-style hand-coded row/particle water tweaks as v007.
- Do not make fish/bird/flocking the production lead before water has a better substrate.
- Do not use SD/LoRA as renderer for visitor prompts or Austin-style outputs.
- Do not treat any generated primitive grammar clip as Austin-approved.
- Do not promise live TouchDesigner for the show without a long stress test; always keep Resolume clips as fallback.

## Open Technical Questions

- Does this machine have a usable TouchDesigner install and licensing state for GLSL TOP export today?
- Should the first heightfield/SDF proof be TouchDesigner-native, Python/OpenGL, or Blender shader-only?
- Does Pravin's Resolume deck prefer DXV3 today, or are H.264/HAP acceptable until the show machine is stable?
- Should `grammar.json` live under `track2-deterministic/primitive_grammar/` or a docs-only path until code consumes it?
