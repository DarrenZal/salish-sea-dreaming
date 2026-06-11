# Heightfield SDF Water Glyph Prototype Brief - 2026-05-19

Status: INTERNAL ONLY until Austin reviews. This is a technical substrate proof, not Austin-approved artwork.

## Summary

Darren paused the v006 renderer path. Do not make v007 by tweaking `scripts/primitive_water_membrane_v6.py`.

The new direction is heightfield + SDF glyph embedding: circle, crescent, and trigon marks should be folded into, refracted by, or lit through a shared moving water height/normal field. The goal is to stop the marks reading as particles or overlays and start testing whether they can behave as luminous inlays, relief, or refraction events inside one water surface.

## Sources Read

- `docs/space-center/deep-research-fluid-grammar-synthesis-2026-05-19.md`
- `/Users/darrenzal/Downloads/compass_artifact_wf-411991c1-9f64-4612-9b94-4b3c88be2ae9_text_markdown.md`

## Technical Pivot

The research synthesis recommends changing representation rather than polishing placement:

- Generate a moving water heightfield.
- Rasterize circle, crescent, and trigon as signed-distance fields.
- Merge the glyph SDF into the heightfield before normal generation.
- Recompute normals from the combined water + glyph field.
- Shade/refract the glyph fill through those normals.
- Output RGB-on-black layers for Add/Screen in Resolume.

This is the core test: if the same normal field affects water and glyphs, the primitives read less like stickers and more like embedded surface structure.

## Tool Decision

TouchDesigner is installed at `/Applications/TouchDesigner.app`, but it was not running during this pass. `glslViewer` was not found for a simple headless GLSL render.

For today, I created a Python/NumPy shader-frame proof so the substrate idea exists as a reviewable MP4 without touching the v006 renderer. TouchDesigner/GLSL remains the recommended next implementation path.

## Proof Clip

Folder:

`track2-deterministic/morph_outputs_INTERNAL/heightfield_sdf_water_glyph_v001_2026-05-19/`

Clip:

`01_heightfield_sdf_glyph_embedding_v001_black_screen.mp4`

Renderer:

`scripts/heightfield_sdf_water_glyph_v001.py`

Output metadata:

- Resolution: `1920x1080`
- FPS: `24/1`
- Duration: `6.000s`
- Frames: `144`
- Midpoint nonblank check: max luma `255`, nonblack pixels `130302`
- Midpoint stills: `midpoint_stills/`
- Contact sheet: `contact_sheet_midpoints.jpg`

## What The Proof Does

- Builds two sparse circle/crescent/crescent/trigon phrases on black.
- Converts each primitive into an SDF:
  - circle: distance to radius
  - crescent: boolean difference of two circles
  - trigon: triangular polygon SDF
- Builds a moving water heightfield from summed waves plus circle-origin ripples.
- Adds the glyph SDF into the heightfield as relief/rim before normals are computed.
- Recomputes normals by finite differences from the merged field.
- Samples the glyph color through normal-offset refraction.
- Adds shared caustic/rim shading from curvature/slope so water and glyphs share a light model.

## What It Tests

The proof asks whether the primitive vocabulary can live in a water substrate rather than on top of one. The stills remain very graphic, but the rendered motion should show the primitives bending, shimmering, and lighting from the same field as the water disturbance.

This directly responds to the v005/v006 issue: marks that read like separate particles, rows, or overlay markers.

## Caveats

- This is not a polished visual direction. It is a substrate proof.
- The Python version is CPU/NumPy and internally renders at `640x360`, then upscales to `1920x1080` for turnaround.
- The glyphs still read strongly as graphic silhouettes; the next pass should reduce solid fill and increase refracted edge/caustic behavior.
- The black water field is intentionally subtle for Add/Screen mixing, but it may need stronger background normals for standalone review.
- No cultural approval is implied. This remains internal until Austin reviews.

## Recommended TouchDesigner Path

Build a TOP-only TouchDesigner network:

1. `noiseTOP` or GLSL Gerstner wave pass generates `height_wave`.
2. GLSL SDF glyph rasterizer outputs `glyph_sdf` and optional `glyph_fill`.
3. GLSL composite pass merges `height_wave + glyph_sdf_to_height`.
4. `slopeTOP` or GLSL finite-difference pass computes normals from the merged height.
5. GLSL shading pass samples `glyph_fill` at `uv + normal.xy * refract_strength`.
6. Add shared caustics/rim/fresnel from the merged normal field.
7. Bloom lightly.
8. Export RGB-on-black for Add/Screen in Resolume.

Do not composite glyph color after water shading as a separate sprite layer; that recreates the overlay problem.

## GPU / H200 Note

The Telus H200s are useful if the next step becomes:

- CuPy/Taichi heightfield or stable-fluid batches.
- Larger 4K/60 shader-frame renders.
- Blender/Cycles or Geometry Nodes hero renders.
- Parameter sweeps across SDF depth, refraction, and caustic strength.

For this v001 proof, local CPU rendering was sufficient after lowering the internal shader resolution.

## Austin Review Questions

- Do circle/crescent/trigon marks embedded into a water height/normal field feel more appropriate than marks placed on top of footage or a membrane?
- Should this water grammar read as raised relief, carved/inset marks, luminous refraction, or something flatter?
- Can the glyphs be visibly refracted/distorted by water, or should their graphic forms remain crisp?
- Is a black-background Add/Screen layer the right review format for this substrate?
- Should the next water prototype be TouchDesigner/GLSL live patch, Blender hero render, or another fast Python shader proof?

## Next Recommendation

Move to a small TouchDesigner/GLSL prototype with the same method: SDF glyphs folded into the heightmap, normals recomputed from the merged field, and glyph fill refracted through the water normals. Keep fish, birds, figures, flocking, SD, and LoRA parked.
