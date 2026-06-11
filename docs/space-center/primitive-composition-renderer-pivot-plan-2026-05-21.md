# Primitive Composition Renderer Pivot Plan - 2026-05-21

Status: INTERNAL planning note. No rendering performed. This is not
Austin-approved, not public-use guidance, not a cultural-meaning claim, and not
a general Coast Salish grammar claim. It prepares the fallback plan if
`integrated_choreographer_v004_radial_arc_bounded_peak` does not land as a
wall-worthy lead visual.

## Purpose

The current radial arc-bounded choreographer lane is valuable because it keeps
field provenance, negative-space cuts, wavefront arcs, and cusp regions visible.
But it may still fail as a wall lead if the scalar-field architecture cannot
make a clear, authored composition without apology.

This plan defines the pivot: if v004 is not strong enough, stop iterating the
same architecture and move to a direct primitive composition renderer.

## Decision Rule

If `integrated_choreographer_v004_radial_arc_bounded_peak` feels wall-worthy
and can be shown without apology, it becomes the radial spine.

If v004 is "almost there," pivot. Do not commission v005 on the same
architecture. "Almost there" means the direction is promising but still needs
explanation, debug framing, or forgiveness for muddled crescents, arrow-like
trigons, weak attachment, poor wall read, or insufficient compositional force.

The pivot is not a rejection of wave/choreographer work. It is a change in
authority: authored primitive phrases become the visible composition, while
wave/choreographer layers become atmosphere, timing, opacity, motion, and
background field behavior.

## Pivot Target

Target renderer:

```text
primitive_composition_renderer_v001
```

Core shift:

- direct authored primitive phrases, not wave-derived forms;
- SVG/canvas parametric geometry with explicit phrase records;
- wave/choreographer outputs used as atmospheric, background, motion, opacity,
  shimmer, reveal, and dissolve layers;
- no requirement that every visible primitive be generated from scalar-field
  topology.

The renderer should produce clean, sparse, wall-readable compositions first.
Provenance remains important, but the provenance becomes an authored recipe
record rather than a field-cell extraction proof.

## Inputs

Required reading:

- [austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md](austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md)
- [primitive-svg-reference-validation-2026-05-21.md](primitive-svg-reference-validation-2026-05-21.md)
- [arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md)

Internal visual context:

- early radial, snowflake, and ripple experiments, including
  `radial_water_sun_snowflake_morphology_v001`,
  `radial_sacred_geometry_primitive_morphology_v001`,
  `cymatic_radiant_water_geometry_v001`, and water-cycle phase studies;
- integrated choreographer v001-v004 packets as motion/background references,
  not as mandatory geometry sources;
- Austin axial reference image as a private internal reference only. Use it for
  axial rhythm and bilateral phrase structure, not copying, approval language,
  or public-facing cultural claims.

## Initial Phrase Set

### Pond Ripple

Composition:

- central circle as impact/origin;
- sequential cupping crescents expanding from the origin;
- outer trigon/ray releases as attenuation points.

Key controls:

- circle scale and pulse;
- crescent count, thickness, cusp sharpness, cup direction, and spacing;
- trigon attachment to the final crescent/ring;
- decay of opacity and size from center outward.

Failure checks:

- no random crescents;
- no detached trigon arrows;
- no dense ripple wallpaper.

### Radial Sun

Composition:

- central circle;
- six attached trigons/rays;
- optional crescent ring or partial ring arcs between the center and rays.

Key controls:

- ray count fixed at six for the first pass;
- ray attachment to center/ring;
- trigon concavity and rear-base width;
- optional crescent ring opacity below the ray/body layer.

Failure checks:

- no detached rays;
- no generic mandala or sacred-geometry framing;
- no face/eye details copied from Austin source references.

### Axial Eye / Reference Phrase

Composition:

- central oval;
- paired nested crescents on each side;
- outer pointed trigons or pressure releases at the far sides.

Key controls:

- bilateral spacing and 1-2-1 rhythm;
- central oval aspect ratio;
- nested crescent scale falloff;
- outer trigon attachment and concavity.

Boundary:

- Austin axial reference remains private internal reference only;
- do not call this an eye in public-facing language;
- describe as `axial reference phrase` or `bilateral primitive phrase` until
  cultural review.

### Snowflake / Sixfold

Composition:

- radial trigons around a center;
- crescent branches or paired branch arcs along six arms;
- optional small center circle or omitted center if the read becomes too sun-like.

Key controls:

- arm count, branch depth, trigon length, crescent branch angle;
- density cap so the shape stays sparse and does not become a mandala;
- opacity falloff on outer branches.

Failure checks:

- no all-over decorative snowflake field;
- no cultural or ceremonial snow/sun claim;
- no exact source color or motif transfer.

### River / Current Phrase

Composition:

- repeated `circle -> crescent -> trigon` motifs along a path;
- circles at knots, bends, impacts, or eddies;
- crescents cupping or following the path tangent;
- trigons releasing downstream.

Key controls:

- path spline, phrase spacing, tangent alignment;
- per-phrase phase offset;
- curvature response at bends;
- opacity and scale variation along the current.

Failure checks:

- no motifs outside the water/path band without foam/spray role;
- no repeated glyph stamping;
- common-fate motion must be readable.

## Technical Approach

Build `primitive_composition_renderer_v001` as an SVG/canvas parametric
renderer with explicit phrase recipes.

Suggested recipe structure:

```json
{
  "composition_id": "pond_ripple_v001",
  "cultural_status": "internal_austin_review_needed",
  "phrase_type": "pond_ripple",
  "canvas": {"width": 1920, "height": 1080},
  "primitives": [
    {
      "id": "origin_circle_001",
      "type": "circle",
      "role": "origin",
      "center": [960, 540],
      "scale": 1.0,
      "rotation": 0.0
    }
  ],
  "animation": {
    "mode": "phrase_appears_then_settles",
    "wave_background_driver": "optional"
  }
}
```

Shape parameters:

- cusp sharpness;
- crescent thickness;
- crescent arc angle and cup direction;
- trigon concavity;
- trigon rear-base width and point length;
- attachment point and overlap;
- rhythm, spacing, scale falloff, and opacity falloff.

Optional animation:

- phrase elements appear as ripples, wavefronts, or pressure reveals;
- each element settles into the authored composition;
- waves may drive timing, opacity, jitter, shimmer, or background movement;
- the wave field does not need to generate the primitive geometry.

Required debug outputs if rendering happens later:

- recipe JSON;
- contact sheet with final stills plus construction overlays;
- per-primitive labels showing role, attachment, cup direction, and parent
  phrase;
- visual checks for cusp sharpness, concavity, attachment, spacing, and
  interlock.

## Cultural Boundary

All outputs from this pivot are internal only.

Do not describe them as Austin-approved, culturally approved, public-ready, or
traditional meaning. Do not claim the renderer implements Coast Salish grammar.

Use this framing:

```text
authored primitive-like composition studies pending cultural review
```

Do not use:

- public-use claims;
- cultural-meaning claims;
- exact Austin source geometry, palette, atom adjacency, face details, or
  source composition;
- Thunderbird, serpent, wolf, named/supernatural beings, chiefs/specific
  people, or crest-like scenes.

Austin-derived references remain internal until Austin gives per-output OK.

## First Work Order Prompt For B

```text
You are Agent B. Pivot only if integrated_choreographer_v004_radial_arc_bounded_peak is not wall-worthy without apology.

Create primitive_composition_renderer_v001 as a direct authored primitive phrase renderer. Do not build v005 on the same integrated_choreographer architecture.

Scope:
- No external comms.
- Internal only; not Austin-approved; no cultural-meaning claims.
- Do not touch other agents' output folders.
- Do not render broad SD/LoRA/style-transfer work.

Read first:
- docs/space-center/primitive-composition-renderer-pivot-plan-2026-05-21.md
- docs/space-center/austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md
- docs/space-center/primitive-svg-reference-validation-2026-05-21.md
- docs/space-center/arc-bounded-region-rendering-notes-2026-05-21.md

Implement:
1. A parametric SVG/canvas renderer with recipe JSON for authored primitive phrases.
2. Initial phrase presets:
   - pond_ripple
   - radial_sun
   - axial_reference_phrase
   - snowflake_sixfold
   - river_current_phrase
3. Shape controls for cusp sharpness, crescent thickness, trigon concavity, attachment, rhythm, spacing, scale falloff, and opacity falloff.
4. Optional animation where elements appear as ripples/waves and settle into composition.
5. Optional wave/choreographer background driver for opacity, shimmer, and motion only; do not require wave fields to generate primitive geometry.
6. Debug/contact-sheet outputs that expose construction, labels, attachment points, cup direction, and role metadata.

Acceptance:
- Each phrase must read on a wall without apology in a still frame.
- No detached arrows, moon-stamp crescents, generic mandalas, or glyph scatter.
- Every primitive has a role and attachment/path/origin relation.
- Report py_compile for scripts, image dimensions/counts for still/contact sheets, ffprobe for MP4s if any are rendered, and checked paths for docs.
```

## Stop Condition

If the direct authored renderer also fails to make one wall-worthy still per
phrase family, stop and curate the best existing water-flow phrase work instead
of adding another renderer architecture.
