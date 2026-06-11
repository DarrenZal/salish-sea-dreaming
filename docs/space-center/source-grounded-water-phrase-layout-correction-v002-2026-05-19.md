# Source-Grounded Water Phrase Layout Correction v002 - 2026-05-19

Status: INTERNAL ONLY until Austin reviews. This is a PNG-only still-layout correction packet. It is not animation, not Austin-approved artwork, and not public-use guidance.

## Purpose

Darren's v001 review found the real geometry constraints that need to exist before animation: cupping, fitting, void discipline, water-boundary discipline, and trigon specificity.

This v002 packet keeps the source-grounded still-layout path, but corrects the primitive geometry so the layouts can be compared against Austin's screenshots before any motion or shader work resumes.

Machine companion:

`track2-deterministic/primitive_grammar/water_phrase_layouts_source_grounded_v002.json`

PNG still output:

`track2-deterministic/morph_outputs_INTERNAL/source_grounded_water_phrase_layout_correction_v002_2026-05-19/`

Renderer:

`scripts/source_grounded_water_phrase_layouts_v002.py`

## Sources

- `/Users/darrenzal/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md`
- `/Users/darrenzal/Documents/Notes/Transcripts/2026-05-18 The Salish Sea Dreaming Meeting 2 Transcript.md`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/03-austin-course01-phase05-water-shapes.png`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/05-austin-phase05-loopingscreen.png`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/06-austin-vancity-slides-crescent-circle-trigon.png`

## Geometry Rules

### 1. Crescent Cupping

Default rule: the crescent concave side cups the circle/origin.

Implementation: v002 rotates each crescent from its center back toward the phrase origin. It no longer uses a blind `tangent + pi` flip, which could make a crescent face away from the circle.

Flow-following exception: a crescent can rotate with a current/path only if the phrase still reads as holding or following the origin.

### 2. Trigon Specificity

Default rule: the trigon should read as a pointed primitive with a crescent-like/flat rear base, not a generic triangle.

Implementation: v002 replaces the generic trigon with a custom curved trigon. Local point direction is the release/flow direction; the rear is rounded/flat enough to avoid looking like a simple triangle.

The VanCity reconstruction was corrected first because it is the clearest source comparison.

### 3. Gap Logic

Default rule: crescent/trigon adjacency must not create an accidental circle-sized void.

Implementation: v002 closes the VanCity trigon/crescent transition by changing trigon geometry and spacing. No intentional void-fill circles are used in this packet.

Future rule: if a circular void is intentionally needed, fill it with a documented circle/oval anchor rather than leaving it accidental.

### 4. Boundary Logic

Default rule: primitive marks stay inside the water band/sheet unless deliberately marked as foam or spray at an edge.

Implementation: river, waterfall, and S-curve studies use water masks. v002 has no foam/spray exceptions.

## v001 Mistakes Fixed

- Wrong crescent orientation: v001 could place circles and crescents next to each other with the crescent facing away from the origin. v002 explicitly cups the origin.
- Generic trigon: v001's trigon was not specific enough in the VanCity reconstruction. v002 uses a curved trigon with a flatter/rounded rear base.
- Accidental voids: v001/v002 draft spacing could create a circle-like gap between crescent and trigon. Final v002 closes that gap.
- Boundary drift: river and waterfall marks could fall outside the water surface. v002 clips those marks to the water mask.

## Rendered Stills

### 01_vancity_grammar_reconstruction_v002_source_grounded.png

Tests the black-ground VanCity slide logic: right-side circle focal point, large crescents cupping that focal origin, improved trigon, and red dotted eye-path arrows.

Caveat: this is still a reconstruction for layout comparison only.

Question: Does the improved trigon and cupping logic now match the VanCity slide closely enough to use as the geometry baseline?

### 02_procedural_line_following_v002_source_grounded.png

Tests Austin's 24:20 direction: one curved line with repeated `circle -> crescent -> crescent -> trigon` phrases.

Caveat: still diagrammatic; this should not be animated until phrase geometry is accepted.

Question: Does the line-following phrase read as circle origin held by crescents, then released into trigon direction?

### 03_river_band_v002_source_grounded.png

Tests a broad pale-blue river band with sparse phrase marks inside the current.

Caveat: simplified river topology; it is not a reproduction of Austin's art.

Question: Does clipping the phrase marks inside the pale-blue band fix the boundary issue while keeping the source-grounded river-current read?

### 04_waterfall_vertical_v002_source_grounded.png

Tests vertical circle/crescent/crescent/trigon descent inside a falling-water sheet.

Caveat: waterfall translation is still a review question; keep this as a still prompt until Austin weighs in.

Question: Does vertical cupping/downstream trigon placement feel like a valid waterfall adaptation, or should waterfall layouts wait for Austin?

### 05_s_curve_river_topology_v002_source_grounded.png

Tests topology-first placement in a large S-curve river, with marks near bends, rocks, and eddies rather than tiled across the field.

Caveat: simplified topology diagram; the key question is placement discipline.

Question: Does topology-first mark placement now obey water-boundary discipline while staying closer to Austin's looping-screen composition?

## Contact Sheet

`contact_sheet_source_grounded_layouts_v002.png`

Use the contact sheet for quick geometry review, then inspect the VanCity and river/waterfall stills individually for cupping, voids, and boundary discipline.

## Do Not Do Next

- Do not animate these yet.
- Do not create `water_phrase_recipe_studies_v002`.
- Do not continue the heightfield/SDF renderer as the main visual.
- Do not use MP4/MOV in this correction packet.
- Do not introduce new figures, fish, birds, eyes, or scene grammar.

## Next Recommendation

Review v002 stills against Austin's screenshots with the geometry rules visible. If Darren accepts the cupping/trigon/gap/boundary rules, the next visual step should animate only the accepted still compositions while preserving those constraints.
