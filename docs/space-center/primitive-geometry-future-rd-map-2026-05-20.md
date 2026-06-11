# Primitive Geometry Future R&D Map - 2026-05-20

Status: INTERNAL Agent F long-form future R&D map. No rendering. Not Austin-approved. Not public-use guidance. Not a cultural interpretation, not a traditional-meaning claim, and not a general Coast Salish grammar claim. Anything Austin-derived remains internal until Austin gives per-output OK.

This document is a grounded implementation map for primitive geometry research after the 2026-05-18 pivot: circle, crescent, and trigon should operate as a controlled procedural language over water, topology, cymatics, networks, and later 3D field geometry. It is intentionally not a style-transfer plan, not a LoRA plan, and not a static Austin-like salmon replication plan.

Read with:

- `/Users/darrenzal/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md`
- `docs/space-center/topology-cell-region-taxonomy-2026-05-20.md`
- `docs/space-center/pravin-internal-update-rd-lane-map-addendum-2026-05-20.md`
- `docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md`
- `docs/space-center/austin-visual-morphology-atlas-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/primitive-topology-3d-fluid-geometry-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `docs/space-center/topology-cell-interaction-input-design-2026-05-20.md`

## 1. Core Thesis

The useful future direction is not "more primitives." It is a computational grammar where primitive roles are explicit, sparse, and testable:

```text
circle class   -> origin, impact, eddy, node, pressure center, closed cell
crescent class -> two-arc relation, wavefront, shear band, wake, interface
trigon class   -> three-arc cell, release, attenuation, ray, pressure wedge
network class  -> paths, adjacency, flow routing, graph relations, field scaffold
```

The primitives should be generated from topology and motion, not scattered by hand. The strongest technical move is to treat hidden geometry, water fields, cymatic fields, and graph layouts as cell generators. The visible layer then selects a small number of cells and phrases that have roles: origin, interface, release, route, or boundary.

This keeps the direction grounded in the 2026-05-18 Austin meeting:

- circle is the focal origin or impact point;
- crescents carry ripple, phase, cupping, and continuation;
- trigons carry attenuation, release, point, or final ripple form;
- primitives should follow procedural lines, water, salmon/kelp/current motion, and path common-fate;
- water-first work is safer than figure-first work;
- 3D primitive work is possible, but relief/wrapped/cylindrical sculptural translation needs Austin review.

The engineering implication is simple: every future prototype should emit structured recipe data before rendering. A primitive without a role, source relation, tangent, boundary, or cultural status should fail validation before it reaches a renderer.

## 2. Non-Negotiable Boundaries

Use these as hard constraints for every lane in this map.

- Internal only until Austin gives per-output OK.
- No public-ready claims.
- No broad Stable Diffusion, LoRA, or style-transfer work.
- No static Austin-like salmon replication as the default path.
- No Wolf <-> Thunderbird-Background morphs.
- No named chiefs, specific persons, crest/clan implication, or named/supernatural beings on live or public paths without explicit Austin guidance.
- No copying exact Austin source geometry, palette, atom adjacency, or composition.
- No use of James Harry sculpture references beyond private geometry questions unless Austin creates an approval path.
- No "sacred geometry" authorization language. Use "circle-overlap topology", "cell extraction", "standing-wave cells", "field geometry", or "primitive topology sketch".
- No random wallpaper: seed/flower, triangle grids, circle fields, and network fields are construction systems, not final all-over patterns.
- All outputs need verification before reporting. For docs, verify source paths and relative links. For scripts, run `py_compile`. For MP4s, run `ffprobe`. For images, verify counts and dimensions.

## 3. Shared Data Contract

The long-term system should separate topology generation from drawing. Even if a prototype starts in Python, TouchDesigner, Three.js, or Blender, it should describe the same conceptual records.

Minimal record:

```json
{
  "prototype_id": "water_ripple_overlap_cells_v001",
  "cultural_status": "internal_austin_review_needed",
  "geometry_domain": "2d|3d|slice",
  "field_family": "spline|circle_overlap|multi_emitter|bessel|delaunay|vortex|network",
  "cells": [
    {
      "id": "cell_001",
      "topology_class": "circle|crescent|trigon|network|outline",
      "role": "origin|impact|shear|wavefront|release|node|edge|pressure_cell",
      "source_ids": ["emitter_01", "emitter_02"],
      "centroid": [0.52, 0.48],
      "orientation_rad": 1.1,
      "confidence": 0.86
    }
  ],
  "invalid_if": [
    "unlabeled_cultural_status",
    "random_orientation",
    "generic_triangle_trigon",
    "decorative_crescent_without_relation",
    "eye_like_circle_pair",
    "density_exceeds_cap"
  ]
}
```

Validation should happen before visual output:

- `circle` must be one closed boundary or a role-labeled origin/node/core.
- `crescent` must have two-arc relation, cupping target, path tangent, wavefront, or shear source.
- `trigon` must have three-arc, triangular-cell, pressure-release, or endpoint evidence. Reject generic UI arrows and sharp random triangles.
- `network` must have nodes and edges with source roles. Reject all-nodes-fire scatter.
- visible density must stay capped. More construction geometry means more candidates, not more rendered cells.
- every output has a `cultural_status` and `approval_state`.

## 4. 2D Tiling With Circle, Crescent, And Trigon Classes

The word "tiling" is useful only if it means a topology-aware partition, not stamped icons. The plane can be divided into cells by circles, waves, meshes, or graph fields. The visible primitives are selected cells from that partition.

### 4.1 Circle-Overlap / Seed-Flower Generator

Best immediate topology fixture:

```text
construction circles -> arc intersections -> regions -> classify cells -> render sparse selected cells
```

Primitive classes:

- center or one-boundary cell -> circle/origin;
- pairwise lens/lune -> crescent;
- three-boundary outer scallop or triangular gap -> curved trigon;
- intersections and arcs -> network nodes/edges.

Implementation path:

1. Build or reuse a Python SDF/CSG extractor.
2. Generate circle arrangements with explicit parent IDs.
3. Extract connected components from boolean masks.
4. Sample each boundary to label parent circle sources.
5. Classify `outer_3circle_scallop` as the sun/ripple trigon target, per `topology-cell-region-taxonomy-2026-05-20.md`.
6. Reject `inner_3circle_intersection` for v005-style sun trigons unless used as debug-only.
7. Emit recipe JSON before drawing.

This is the cleanest way to avoid decorative placement because the crescents and trigons emerge from overlap regions.

### 4.2 Delaunay / Voronoi Generator

Best for pressure fields, network fields, and trigon-as-structure:

```text
points -> Delaunay triangles -> Voronoi pressure regions -> active cells
```

Primitive classes:

- graph point or pressure extremum -> circle/node;
- Voronoi edge or deformed shared boundary -> crescent/interface;
- Delaunay triangle -> trigon/pressure cell;
- dual graph -> network routing.

Implementation path:

1. Seed points from water events, eddies, visitor nodes, or deterministic PRNG.
2. Build Delaunay triangles and Voronoi regions.
3. Store adjacency, edge ownership, and per-cell field values.
4. Animate pressure/opacity on selected cells without moving topology at first.
5. Later, curve shared edges so triangles bulge into crescent-like interfaces without opening cracks.

This lane is strong because it creates real structural relations. It is weak if it becomes a bright triangle grid.

### 4.3 Curved-Edge Shared Mesh

Best for a living water membrane:

```text
triangular mesh -> shared edge curves -> pressure deformation -> sparse cells
```

A shared-edge model solves the main visual risk of independent cell warping. Adjacent cells use the same edge object, so no gaps or overlaps appear as the membrane breathes.

Primitive classes:

- base cell -> trigon;
- high-pressure closed pocket -> circle/oval;
- curved shared edge between neighboring cells -> crescent/shear interface.

Implementation path:

1. Store edges as first-class objects.
2. Each triangle references three shared edges.
3. Pressure waves change edge curvature and cell fill.
4. Render only cells above role/confidence thresholds.

This is better after a basic Delaunay/field extractor exists.

### 4.4 Wave / Cymatic Cell Generator

Best for standing-wave fields, water ripples, snow/radial forms, and audio-reactive futures:

```text
scalar field F(x,y) -> nodal contours -> antinode components -> topology classes
```

Primitive classes:

- closed antinode lobe -> circle/oval;
- pinched two-arc region -> crescent/lens;
- three-way gap/lobe -> trigon;
- nodal contours -> outline/network.

Implementation path:

1. Use analytic fields first: multi-emitter, Bessel/circular membrane, Chladni.
2. Extract topology from stable spatial field `F(x,y)`, not directly from time-multiplied `Z(x,y,t)`.
3. Animate phase as display state: outline -> positive fill -> outline -> inverse fill -> outline.
4. Keep low mode counts and sparse selection.

This avoids the quarter-phase flash problem where the whole field collapses into a full-screen mask.

### 4.5 Circle Packing / Residual Gap Generator

Useful later, not first:

- circles become near-tiling bodies;
- residual gaps become curved trigons;
- overlaps or circle-minus-circle cells become crescents.

Risk is high density. Apollonian and recursive packing become ornamental quickly. Use only low recursion and only when a specific field event requires scale hierarchy.

## 5. Water And Fluid Dynamics Mapping

Use fluid dynamics as a placement and motion system, not as a public cultural claim and not as a promise of physically exact CFD. Early prototypes can use analytic or simplified fields.

### 5.1 Vortices

Mapping:

- circle/oval -> vortex core, eddy center, pressure node;
- crescent -> rotating shear interface around the core;
- trigon -> downstream release or attenuation wedge;
- network -> connections between vortices, obstacles, and exits.

Implementation options:

- 2D analytic vortex particles with simple velocity fields.
- Curl noise for divergence-free ambient drift.
- Delaunay mesh between vortex cores for pressure cells.
- TouchDesigner later for live vorticity visuals after Python recipe validation.

Prototype:

```text
vorticity_eddy_cluster_v001
  obstacle point
  one stable vortex pocket downstream
  circle at vorticity center
  incoming crescent cups the node
  return crescent orbits against flow
  trigon releases downstream
```

Success criterion: the cluster reads as one current system. Failure: separate symbols spinning without shared motion.

### 5.2 Shear

Mapping:

- crescent is the primary shear primitive;
- circle marks pressure centers that shear wraps around;
- trigon appears where shear releases, tears, or attenuates;
- line/outline stores the interface path.

Implementation options:

- velocity-gradient threshold creates candidate shear bands;
- streamlines with curvature create crescent placement arcs;
- Kelvin-Helmholtz-like rollups can be approximated visually, but do not claim simulation accuracy.

Prototype:

```text
shear_band_current_sheet_v001
  two adjacent flow lanes with different speeds
  crescents attach to high-gradient interface
  circles only at pressure knots
  trigons at downstream release points
```

Success criterion: crescents have a source relation. Failure: moon-stamp crescents floating in water.

### 5.3 Waves

Mapping:

- circle -> impulse, droplet, pressure node, wave origin;
- crescent -> partial wavefront arc, not a full generic ring;
- trigon -> weakening edge or attenuation;
- outline -> membrane/nodal boundary.

Implementation options:

- analytic radial emitters for pond/rain;
- shallow-water or damped wave equation later;
- Bessel/circular membrane for radial sun/ripple/snow tests;
- SDF primitives clipped to membrane boundaries.

Prototype:

```text
membrane_wave_pond_impact_v001
  circle impact pulses first
  crescent A and B ride partial wavefronts
  trigon appears late and fades first
  no dense ripple shader
```

Success criterion: a still frame reads as circle -> crescent -> crescent -> trigon. Failure: concentric-ring shader with primitive labels added afterward.

### 5.4 Streamlines

Mapping:

- line/spline -> water path, river bend, kelp/current trace;
- circle -> source, bend pressure, knot, eddy, or confluence;
- crescent -> tangent-following phase mark;
- trigon -> release at downstream attenuation;
- network -> branching current graph.

Implementation options:

- hand-authored splines as the immediate production path;
- optical flow from footage later, after the phrase grammar is stable;
- spline advection under low-frequency curl noise for life without random drift.

Prototype:

```text
spline_advection_river_bend_v001
  two or three splines
  circle at inside bend pressure
  crescents along tangent and curvature
  trigon exits downstream
  spacing compresses at bend, opens in calm water
```

This is the most plausible short-run water grammar lane because it gives control and beauty without solver complexity.

### 5.5 Practical Water Backlog

| Prototype | Purpose | Implementation floor | IMPACT fit |
|---|---|---|---|
| `spline_advection_river_bend_v001` | path-led phrase over current | Python recipe or TD spline CHOP/SOP | plausible teaser if rendered and reviewed |
| `membrane_wave_pond_impact_v001` | direct Austin pebble/ripple logic | analytic radial wave, SDF cells | plausible teaser |
| `vorticity_eddy_cluster_v001` | eddy/current knot language | analytic vortex field | post-IMPACT unless time remains |
| `shear_band_current_sheet_v001` | crescent-as-interface | velocity-gradient field | post-IMPACT |
| `flow_network_mist_transition_v001` | water-to-mist partial phrases | sparse graph plus opacity field | possible as subtle later layer |

## 6. Cymatics And Standing Waves

Cymatics is useful as a field generator: vibration creates nodal lines, antinode cells, radial lobes, and interference regions. Do not import metaphysical claims or public authorization language.

### 6.1 Field Families

Ranked for this project:

1. Multi-emitter standing interference: best for rain, ripple fields, water networks, and overlapping wavefront cells.
2. Exact circle-overlap / seed-flower CSG with phase modulation: best topology fixture with clean source labels.
3. Circular membrane / Bessel harmonics: best for snow, sun/ripple, and radial fields.
4. Low-order Chladni plate fields: useful outlines, but can become grid-like.
5. Damped wave equation: best for live touch impacts later; harder for stable classification.

### 6.2 Phase-Inversion Model

Do not threshold a time-varying wave field frame by frame. Extract stable topology once per scene window:

```text
node_lines = contour(F, 0)
positive_cells = connected regions where F > tau
negative_cells = connected regions where F < -tau
```

Animate display:

```text
outline -> positive fill -> outline -> negative fill -> outline
```

This gives a standing-wave breath without strobe. Nodal outlines remain stable, while filled cells trade polarity.

### 6.3 Primitive Classification

- one closed antinode island -> circle/oval;
- two-arc/lens/lune antinode -> crescent;
- three-source gap or triangular lobe -> trigon;
- long nodal contour -> outline/network.

For exact CSG, source attribution is parent-circle based. For wave fields, source attribution can be estimated from dominant emitter contribution along the boundary. Low-confidence cells should be discarded.

### 6.4 Audio Path

Audio can drive parameters only:

- RMS -> membrane energy, fill opacity, ring growth rate;
- onsets -> temporary ripple origins;
- low band -> radius, damping, ring count;
- mid band -> mode blend or phase offsets;
- high band -> trigon release density, shimmer, outline brightness;
- spectral centroid -> mode family shift.

This must be framed as math/design modulation, not cultural translation.

### 6.5 Cymatics Backlog

| Prototype | Purpose | Implementation floor | IMPACT fit |
|---|---|---|---|
| `rain_pond_standing_interference_v002` | water/rain overlap cells | Python NumPy/OpenCV | plausible only if current crude reads are fixed |
| `seed_flower_csg_phase_v002` | show circles generating crescents/trigons | Python SDF/CSG | plausible internal teaser |
| `circular_membrane_snow_sun_v002` | radial snow/sun/ripple field | Bessel or approximate harmonics | plausible if abstract and reviewed |
| `cymatic_cell_inversion_network_v001` | network field from standing waves | contour graph extraction | post-IMPACT |
| `audio_reactive_td_cymatics_v001` | live phase modulation | TD GLSL/TOP after recipe proves | post-IMPACT or non-critical demo only |

## 7. Networks Made From Primitive Nodes And Edges

Network work is a legitimate primitive geometry lane if it stays sparse and role-labeled. It is not a particle field.

Mapping:

- circle -> node, source, sink, eddy, dream, pressure point, graph junction;
- line -> edge, path, flow route, relationship;
- crescent -> curved edge segment, transition zone, held relation, shear along an edge;
- trigon -> terminal release, directional packet, confluence gap, pressure wedge;
- outline -> cluster boundary or membrane.

Useful sources of network geometry:

- Delaunay/Voronoi duals from point fields;
- streamlines through water velocity fields;
- visitor dream graph positions;
- bioregional data nodes;
- knowledge graph relationships;
- cymatic nodal-line intersections.

Implementation path:

1. Start with a small graph: 8 to 30 nodes.
2. Label each node role before rendering.
3. Choose one routing mode: water current, mist network, constellation, or pressure field.
4. Convert edge curvature into crescent candidates only where the relationship has phase or shear.
5. Use trigons sparingly at exits, terminal transitions, or confluences.
6. Do not light every node equally.

Network failure modes:

- generic star-map cliche;
- decorative node scatter;
- circles reading as eyes or roe;
- all edges firing at once;
- no relation between graph behavior and primitive classes.

Network success criterion: a viewer can read motion through a few selected relations, not a full database visualization.

## 8. 3D Extension

3D is a future bridge, not an IMPACT dependency. The goal is not to extrude 2D icons. The goal is to preserve primitive topology roles in 3D field geometry.

### 8.1 Spheres And Tori

2D circle class maps to:

- sphere;
- bubble;
- droplet;
- vortex core;
- pressure cell;
- spherical shell;
- torus/vortex ring for circular circulation.

Torus behavior is especially valuable because it moves like a fluid event:

- ring radius -> circulation scale;
- tube radius -> vortex thickness;
- ring normal -> travel direction;
- phase around tube -> internal circulation.

A torus should be a vortex/field primitive, not a cultural symbol.

### 8.2 Crescent Sheets, Ribbons, And Tubes

2D crescent class maps to:

- curved sheet;
- ribbon;
- shear surface;
- folded membrane;
- vortex tube;
- wake interface.

Animation roles:

- stretch along velocity;
- cup around a vortex core;
- peel from a pressure front;
- roll into a tube;
- dissolve when phase changes.

This is stronger than making a literal 3D crescent object because it keeps crescent as "interface under strain."

### 8.3 Trigon / Tetrahedral Structures

2D trigon class maps to:

- triangular surface face;
- tetrahedron;
- tetrahedral-octahedral scaffold;
- Delaunay cell;
- pressure/density cell;
- transparent mesh facet.

Best behavior:

- low-opacity scaffold;
- selected active cells only;
- circles/spheres and tori as event sources;
- crescent sheets/tubes as active interfaces;
- triangular/tetrahedral cells as structure.

Dense bright tetrahedra will read as generic sci-fi mesh. Keep structural cells subtle.

### 8.4 3D Slices Back To 2D

The key 3D proof is not a fly-through. It is a slice:

```text
3D field of spheres/tori/sheets/tetrahedra
  -> animated slicing plane
  -> 2D cross-section cells
  -> circle/crescent/trigon classifier
```

If the cross-section returns readable 2D primitive topology, the 3D grammar survived the jump. If not, the 3D scene is only spectacle.

### 8.5 3D Backlog

| Prototype | Purpose | Tool floor | IMPACT fit |
|---|---|---|---|
| `transparent_tetra_vortex_slice_v001` | prove 3D field slices back to 2D primitives | Three.js | post-IMPACT; maybe one still in an internal deck |
| `torus_vortex_ring_field_v001` | circle-as-vortex in 3D | Three.js or TD | post-IMPACT |
| `crescent_shear_ribbon_volume_v001` | crescent-as-interface | Three.js curves or Blender GN | post-IMPACT |
| `tetrahedral_pressure_cells_v001` | trigon-as-volume scaffold | Three.js or Blender GN | post-IMPACT |
| `td_audio_vortex_slice_v001` | live 3D field modulation | TouchDesigner | post-IMPACT only |

## 9. Implementation Paths

### 9.1 Python / OpenCV / SciPy

Best role: topology extraction, validation, recipe generation, offline test fixtures.

Use for:

- SDF/circle-overlap CSG;
- connected components;
- boundary-source attribution;
- contour extraction from scalar fields;
- Delaunay/Voronoi data;
- JSON recipe emission;
- regression tests for invalid layouts.

Why first:

- deterministic;
- inspectable;
- good for path verification;
- easy to test without a GPU or show stack.

Do not use Python as the final live show renderer unless the resulting media has been rendered, verified, and routed into the production fallback.

### 9.2 TouchDesigner

Best role: live fields, audio modulation, projection routing, Resolume bridge.

Use after the recipe model is stable:

- CHOPs for audio, MIDI, OSC, smoothing, operator controls;
- TOP/GLSL for standing-wave fields, masks, phase inversion, heightfield shading;
- SOP/Geometry COMP for splines, tori, meshes, ribbons;
- Spout/NDI to Resolume;
- panic/blackout control as its own layer.

Lowest-risk TD sequence:

1. ingest precomputed JSON recipes;
2. render phase/inversion and opacity live;
3. add operator controls;
4. add audio modulation;
5. add touch/template input;
6. only then consider live topology generation.

For IMPACT, TouchDesigner should not become show-critical unless rehearsed and backed by Resolume fallback clips.

### 9.3 Three.js / WebGL

Best role: fast browser-viewable proof of 3D concepts and shareable internal prototypes.

Use for:

- transparent tetrahedral mesh;
- torus vortex rings;
- sphere origins;
- crescent ribbons/tubes;
- animated slicing planes;
- simple interaction: camera orbit, phase, slice depth.

Why useful:

- fast to prototype;
- easy to inspect;
- no TD installation required;
- good for post-IMPACT research demos.

Do not use Three.js as a public cultural claim. Keep prototypes labeled internal and abstract.

### 9.4 Blender / Geometry Nodes

Best role: high-quality offline plates, transparent materials, camera choreography, dome-friendly studies.

Use for:

- tetrahedral/octahedral scaffolds;
- vortex tube/sheet materials;
- pearl-like transparent surfaces;
- offline concept frames;
- prerendered loops after review.

Blender should not become an IMPACT dependency except for already-rendered, verified media. Its strength is post-IMPACT polish and controlled hero studies.

### 9.5 What Not To Build

- No broad SD/LoRA/style-transfer lane.
- No generic "Austin style" prompt system.
- No static salmon replication lane.
- No public asset generation from Austin-derived morphology.
- No live free-form visitor image generation.
- No dense full-field seed/flower/triangle/circle wallpaper.
- No 3D relief/wrapped/cylindrical James Harry-derived form without review.

## 10. IMPACT Teaser Vs Post-IMPACT

The IMPACT window should privilege stable, reviewed, 2D/Resolume-safe material. Future R&D can be mentioned or shown internally only if it does not compete with the floor.

| Idea | IMPACT teaser plausibility | Post-IMPACT path |
|---|---|---|
| 2D circle -> crescent -> crescent -> trigon phrase along a spline | High if rendered, sparse, verified, and Austin-review-framed | Expand to optical-flow and water-state library |
| Seed/flower overlap cell extraction | Moderate to high if shown as internal topology, not public claim | Build robust classifier and TD field renderer |
| Cymatic phase inversion | Moderate if current loops are legible and non-crude | Audio-reactive TD and fuller cell extraction |
| Water ripple / pond impact phrase | High concept fit; implementation must stay simple | Add membrane solver and touch impulses |
| River/current sheet | High concept fit with hand-authored splines | Add optical flow from footage |
| Network primitive graph | Low to moderate as subtle layer only | Integrate visitor dreams, data streams, knowledge graph |
| TouchDesigner live controls | Moderate only if non-critical and rehearsed | Full CSPV-driven live renderer |
| Web prompt template selector | Moderate only as bounded mode selector, never AI art | Full offline classifier and async enrichment for future recipes |
| 3D tetra/vortex/slice prototype | Low for live IMPACT; maybe one internal still | Three.js proof, then TD/Blender branches |
| Blender transparent 3D hero study | Low for IMPACT unless already rendered and reviewed | High-quality post-IMPACT research plate |
| Fish, bird, wing, fin, eye, sun-face, figure semantics | Not a default IMPACT lane | Separate Austin review packet per motif |
| Exact Austin-source animation | Not this lane | Permission-gated future work only |

Practical recommendation:

- IMPACT: 2D water-first, topology-cell, and primitive phrase teasers only if reviewed and stable.
- Post-IMPACT: 3D field geometry, audio-reactive cymatics, network integrations, and richer interaction.
- Deep future: dome-scale field architecture where 2D primitive topology, 3D vortex/tetra fields, visitor dream networks, and water-state dramaturgy share one recipe model.

## 11. Sequenced R&D Plan

### Phase 0: Before Any New Rendering

Goal: make the grammar testable.

Tasks:

- define `primitive_geometry_recipe.v1`;
- add phrase validators for class, role, orientation, source relation, density, and cultural status;
- build fixtures for circle-overlap cells using the taxonomy doc;
- emit JSON-only recipes for water, seed, cymatic, and network scenarios;
- document which scenarios are IMPACT candidates and which are parked.

Exit gate:

- no unlabeled primitives;
- no random crescent/trigon placement;
- no unbounded density;
- all recipe paths and source docs verified.

### Phase 1: IMPACT-Safe 2D Teaser Candidates

Goal: one or two stable primitive geometry loops or stills, if rendering is later approved.

Candidate order:

1. `spline_advection_river_bend_v001`
2. `membrane_wave_pond_impact_v001`
3. `seed_flower_csg_phase_v002`
4. `circular_membrane_snow_sun_v002`
5. `flow_network_mist_transition_v001`

Rules:

- black-screen additive layers first;
- large quiet spaces;
- sparse phrase counts;
- no figures;
- no exact Austin source;
- no public claim;
- verified MP4s/images before reporting if any media is created later.

### Phase 2: Post-IMPACT 2D System

Goal: move from one-off studies to a reusable primitive field engine.

Tasks:

- robust contour/cell extraction;
- phrase graph validator;
- TD renderer ingesting recipe JSON;
- operator controls for density, phase, mode, opacity, and blackout;
- audio modulation as numeric parameter input;
- optional visitor prompt -> bounded template selection;
- Resolume fallback loops for every live mode.

Exit gate:

- live and fallback paths are functionally equivalent at the mode level;
- the operator can kill the primitive layer instantly;
- no model runs on the live visual path;
- every mode carries `internal_austin_review_needed` until approved.

### Phase 3: 3D Field Research

Goal: prove 3D geometry can preserve 2D primitive topology instead of becoming generic mesh spectacle.

First prototype:

```text
transparent_tetra_vortex_slice_v001
  sparse transparent tetra/tri mesh
  one to three torus vortex rings
  sphere pressure cores
  crescent-like shear ribbons
  animated slicing plane
  2D slice classifier output
```

Exit gate:

- a slice returns readable circle/crescent/trigon records;
- mesh does not become wallpaper;
- 3D view remains abstract and internal;
- no public cultural or Austin-approval claim.

### Phase 4: Dome / Deep Future Architecture

Goal: one coherent field architecture for dome-scale work.

Potential system:

- water states select field families: ocean, river, still pond, mist;
- visitor dreams select bounded templates, not generated art;
- bioregional data modulates numeric fields;
- primitive topology cells render as 2D layers, 3D slices, or dome volume;
- TouchDesigner handles live modulation and routing;
- Blender renders occasional offline hero plates;
- Three.js hosts lightweight review/proof tools.

Do not begin this as a production system until the 2D grammar and cultural review gates are stable.

## 12. Review Questions For Austin Later

These are questions, not assumptions.

1. In water phrases, should the circle be treated as the start point, the first eye landing point, or both?
2. Should crescents cup back toward the circle origin, face downstream, or change by water state?
3. Should trigons mark attenuation, flow direction, pressure release, or different roles by context?
4. Is vertical waterfall stacking of circle/crescent/trigon phrases an acceptable extension of the pond ripple logic?
5. Can a topology-derived seed/flower overlap study be useful as a private review direction if construction circles remain hidden?
6. Can radial sun/ripple work use attached curved trigons as an internal geometry question, or should sun/ray behavior stay parked?
7. Are mist/network partial phrases useful, or should mist avoid explicit trigons/crescents until there is more guidance?
8. Is 3D center-line / flat-face / wrapped topology a useful private technical reference, or should relief/wrapped geometry stay parked completely?

Each question should be paired with one small, isolated output. Avoid asking for blanket approval of a style.

## 13. Decision Summary

The strongest future R&D path is:

```text
2D phrase grammar
  -> topology-cell extraction
  -> water/fluid placement
  -> cymatic phase inversion
  -> sparse network routing
  -> 3D vortex/sheet/tetra field slices
```

The weakest path is:

```text
style-transfer or LoRA
  -> generic Austin-like texture
  -> static salmon or figure replication
  -> public-facing claims before review
```

For IMPACT, keep the focus narrow: stable 2D primitive water/topology teasers, if reviewed and verified. For post-IMPACT, build the actual primitive geometry engine: recipe records, validators, Python extractors, TD live rendering, Three.js 3D proofs, and Blender hero studies. The deep future is a dome-scale field system where primitive geometry, water motion, standing waves, and network data share one internal, reviewable grammar.
