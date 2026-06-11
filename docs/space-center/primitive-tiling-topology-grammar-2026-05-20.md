# Primitive Tiling / Topology Grammar - 2026-05-20

Status: internal Agent F design-theory and implementation brief only. No rendering. This is mathematical and physics-inspired topology exploration, not Austin-approved grammar, not public-use guidance, not a cultural interpretation, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `docs/space-center/primitive-pattern-language-next-system-2026-05-19.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`

## 1. Short Answer

Yes, but only if "tile" means a topology-aware cell partition, not literal stamped icons.

The strongest formulation is:

```text
plane substrate -> cell decomposition -> classify cells as circle / crescent / trigon -> render sparse active phrases
```

What works:

- Trigons can tile the plane exactly. Triangular and Delaunay meshes are the cleanest exact substrate.
- Crescents can participate in exact tilings when they are shared-edge curved cells or lens/lune cells from circle arrangements.
- Circles can near-tile through packing, and can also appear as closed cells, vortex cores, impact origins, and selected wave-field regions.
- Overlapping circles do not form a tiling by themselves, but their full planar arrangement does: every arc intersection subdivides the plane into closed cells, lenses, lunes, and three-arc gaps.
- Wave, cymatic, Voronoi, Delaunay, and fluid meshes can all produce cell networks that are classified into the three topology classes.

What does not work:

- Equal circles alone do not tile the Euclidean plane without gaps or overlaps.
- Dense seed-of-life, flower-of-life, Apollonian, or triangular wallpaper should not become the final image.
- Literal triangle grids, moon-stamp crescents, and circle particle fields are too generic unless driven by topology, pressure, flow, or phrase grammar.

The practical goal is therefore not "make wallpaper from three shapes." It is a sparse topology grammar over a hidden or subtle cell system: circles mark origins and vortices, crescents mark interfaces and shear, and trigons carry structure, pressure cells, and release.

## 2. Topology Classes In A Tiling Context

### Circle / One-Boundary Closed Cell

Circle means one closed boundary, not only a perfect disk.

Tiling role:

- Impact origin, pressure node, vortex core, eddy, whirlpool, closed antinode, bubble, seed cell, or membrane pocket.
- In circle packing, circles are near-tiling bodies with residual gaps.
- In wave fields, circles are closed contour components.
- In fluid fields, circles are vortex particles or coherent rotating regions.

Constraint: circles should be sparse and role-labeled. Repeated circles quickly read as bubbles, roe, eyes, or generic particles.

### Crescent / Two-Arc Interface Cell

Crescent means a two-arc relation: lens, lune, S-crescent, cupped interface, shear band, wake, or strain zone.

Tiling role:

- Pairwise circle overlap or circle-minus-circle lune.
- Shared curved edge between two neighboring pressure cells.
- Shear layer between vortex cores.
- Kelvin-Helmholtz-like rollup cue, without claiming physical simulation accuracy.
- Membrane bulge where one cell presses into another.

Constraint: a crescent must have a relation: origin, neighboring cell, flow tangent, membrane, or shear pair. Isolated decorative crescents are weak.

### Trigon / Three-Sided Or Triangular Cell

Trigon means three-sided, three-arc, or triangular cell. It can be a straight triangle, curved triangle, triangular gap, or pressure mesh cell.

Tiling role:

- Exact triangular mesh cell.
- Delaunay triangle.
- Three-circle gap or three-wave interference pocket.
- Pressure/density cell in a CFD-like discretization.
- Directional release or attenuation cell.

Constraint: a trigon should not become a generic equilateral triangle, UI arrow, or random spike. Curved trigons are stronger when their edges inherit from adjacent circles, waves, or membrane boundaries.

## 3. Tiling And Cell Generators

| Generator | Tiling status | Primitive topology output | Python/OpenCV now | TD/WebGL later | Main caution |
|---|---|---|---:|---:|---|
| Triangle tiling | Exact | Trigons as structural cells; circles at selected vertices or pressure extrema; crescents along deformed shared edges | Strong | Strong | Avoid visible generic triangle wallpaper. |
| Delaunay / Voronoi duals | Exact partition | Delaunay trigons, Voronoi pressure regions, graph nodes, flow paths | Strong with SciPy/skimage; OpenCV can handle contours after rasterization | Strong | Voronoi cells are not automatically circle/crescent/trigon; classify only selected cells. |
| Hexagonal / seed-of-life lattice | Exact as center lattice; overlap arrangement can be exact | Circle boundaries, lenses/crescents, three-arc trigons, node networks | Strong | Strong | Do not use "sacred geometry" as authorization or public language. |
| Circle packing | Near-tile | Closed circle cells plus crescent/trigon residual gaps | Strong for static/offline | Moderate | Too many circles becomes decorative particle texture. |
| Apollonian-like packing | Asymptotic near-tile | Nested circles, shrinking gaps, curved trigons | Strong at low recursion | Moderate | High recursion becomes dense ornamental filler. |
| Curved-edge triangular mesh | Exact if shared edges are common objects | Trigons bulge into lenses/crescents while preserving a gap-free membrane | Moderate offline | Very strong | Requires shared-edge discipline, not independent cell warping. |
| Wave / cymatic cell tiling | Exact after contour partition, approximate after thresholding | Nodal outlines, antinode cells, crescent interfaces, three-way gaps | Strong | Very strong | Threshold flicker can destroy topology unless phase is stabilized. |
| Circle-overlap arrangement | Exact if all arc subdivisions are included | Lunes, lenses, circular cells, three-arc trigons | Very strong | Strong | The raw overlaps are not a tile; the extracted arrangement is. |
| Fluid mesh / pressure field | Exact mesh plus animated scalar/vector field | Trigons as cells, circles as vortices, crescents as shear | Strong for offline tests | Very strong | Do not claim real CFD unless actually solving and validating fluid equations. |

## 4. How Circle Overlaps Produce Crescents And Trigons

Two overlapping circles create the basic two-arc vocabulary:

```text
inside_A and inside_B      -> lens
inside_A and not inside_B  -> lune / crescent from A
inside_B and not inside_A  -> lune / crescent from B
```

Three overlapping circles create three-arc cells:

```text
boundary sources = A, B, C -> curved trigon candidate
```

The important implementation detail is boundary-source attribution. A raster or SDF extractor should sample each cell boundary and record which parent circle, wave, or membrane generated each arc. Then classification can be based on topology:

- one stable closed boundary, one dominant source -> circle / closed cell;
- two dominant arc sources -> crescent / lens / lune;
- three dominant arc sources or three sides -> trigon / curved triangular cell;
- many sources -> network cell, usually not rendered unless simplified or selected.

This makes seed-of-life, rain ripple interference, snowflake harmonics, and vortex fields share one extractor instead of separate visual tricks.

## 5. Fluid-Dynamics Mapping

Use this as a mathematical design mapping only. It is not a claim of cultural meaning and not a promise of physically exact simulation.

2D primitive mapping:

- Trigons / triangular cells = structure, mesh, pressure cells, density cells, and CFD-like discretization.
- Circles / closed cells = vortices, eddies, whirlpools, impact origins, vortex particles, and coherent rotating regions.
- Crescents / two-arc lenses / S-crescents = shear layers, strain zones, vortex stretching, Kelvin-Helmholtz-like rollups, and wake interfaces.
- Networks / tilings = fluid membranes, pressure fields, flow topology, standing-wave cells, and projection-layer routing.

This gives a useful bridge:

```text
topology grammar <-> cymatic cells <-> fluid membrane <-> pressure/vorticity field
```

The renderer should not need full Navier-Stokes to use the mapping. A scalar pressure field, vector flow field, or analytic vortex field is enough for early internal tests.

## 6. Animation Concepts To Evaluate

### 1. Deforming Curved-Edge Tiling

Core idea: the plane remains gap-free because every edge is owned once and shared by its adjacent cells.

- Start from a triangular mesh.
- Store each edge as a shared curve, not as two independent cell boundaries.
- Animate edge curvature from straight to bulged and back.
- Triangles temporarily read as curved trigons, lenses, or crescents.
- Neighboring cells inherit the same edge deformation, so there are no cracks.

Best use: membrane, water surface, pressure skin, slow cymatic breathing.

Feasibility: possible in Python as offline frames or recipe data; better in TouchDesigner/WebGL where shared geometry and shader deformation can run live.

### 2. Vortex-Circle Simulation

Core idea: circular vortex cores move through a field while interface cells appear around their interactions.

- Circles mark vortex cores or raindrop/whirlpool origins.
- A velocity field advects the cores.
- Crescents appear where nearby vortices create shear or strain.
- Trigons fill the pressure mesh between vortex cores, boundaries, and exit paths.

Best use: eddies, whirlpools, rain-on-water interference, current knots.

Feasibility: moderate in Python/OpenCV if the field is analytic or low-resolution; better later in TD/WebGL for live interaction.

### 3. Static Mesh With Animated Field

Core idea: the topology stays stable while the visual energy moves through it.

- Keep a triangular or Delaunay mesh fixed.
- Animate pressure, velocity, vorticity, opacity, or line weight over cells and edges.
- Activate circles at vortex cores or pressure extrema.
- Activate crescents on high-shear edges.
- Activate trigons on pressure cells or release paths.

Best use: near-term internal tests because geometry is stable and classification is easier.

Feasibility: strongest immediate Python/OpenCV path.

### 4. Hybrid Cymatic-Fluid Mesh

Core idea: combine a subtle trigon mesh substrate with circle impacts, crescent shear, and standing-wave inversion.

- Subtle triangular mesh gives structure.
- Circles spawn as vortices, rain impacts, or pressure origins.
- Crescents stretch along shear, streamlines, or overlap arcs.
- Cells invert like cymatic standing waves: outline -> fill -> inverse fill -> outline.
- Network paths route active cells into water, snow, sun/ripple, or projection layers.

Best use: final design bridge from 2D cymatics into fluid geometry without building the full 3D system today.

Feasibility: Python/OpenCV can prototype the data and offline frames; TD/WebGL is better for real-time phase, interaction, and projection.

## 7. Membrane And Standing-Wave Behavior

The most useful animation model is not random motion. It is shared topology under changing pressure.

Rules:

- Shared edges deform together.
- Cell identity persists across frames.
- Field values change opacity, fill state, stroke weight, curvature, and phase.
- Positive and negative standing-wave phases swap which cells are filled.
- Zero crossing shows stable outlines instead of collapsing the whole image.

Readable cycle:

```text
hidden mesh -> nodal outline -> selected cells fill -> outline -> inverse cells fill -> outline
```

This works for water ripples, cymatics, snowflake cells, sun/ripple radial fields, network pulses, and projection masks. It also gives a way to animate without multiplying decorative marks.

## 8. Avoiding Decorative Wallpaper

Use the tiling as a substrate, not the whole picture.

Design rules:

- Render sparse active cells, not the complete lattice.
- Every visible cell needs a role: origin, vortex, pressure cell, shear interface, release, membrane, or network node.
- Use field thresholds, event timing, and topology selection to decide what appears.
- Keep large quiet areas. Density should come from events, not from filling the frame.
- Avoid full-screen seed-of-life, flower-of-life, Apollonian, or triangle-grid displays unless they are hidden construction geometry.
- Avoid "sacred geometry" language in project framing. Use "circle-overlap topology," "cell extraction," "standing-wave cells," or "field geometry."
- Preserve the phrase read: origin -> interface/phase -> release.
- Do not let the mesh imply Austin approval, Coast Salish grammar, or traditional meaning.

The test is simple: if the image still reads as a repeated pattern after removing animation, it is probably wallpaper. If it reads as a pressure event, flow relation, membrane, or field transition, it is closer to the desired grammar.

## 9. Visual Application Lanes

### Rain

- Circle: impact origin or expanding wavefront center.
- Crescent: interference lens between two impacts.
- Trigon: three-impact gap, attenuation cell, or pressure release.
- Best generator: circle-overlap arrangement plus short-lived standing-wave field.

### Snowflakes / Frozen Water

- Circle: central closed cell or local pressure node.
- Crescent: radial lens, branching shear-like arc, or paired lobe.
- Trigon: sixfold triangular wedge, three-arc cell, or crystallization gap.
- Best generator: radial harmonic field, sixfold Delaunay mesh, or controlled circle-overlap lattice.

### Networks

- Circle: graph node, source, sink, vortex, or junction.
- Crescent: interface along an edge or transition between two nodes.
- Trigon: directional release, terminal cell, or pressure packet.
- Best generator: Voronoi/Delaunay dual with sparse activation.

### Water Surfaces

- Circle: eddy, whirlpool, impact, pressure origin.
- Crescent: shear band, wake, wave face, strain zone.
- Trigon: pressure mesh cell, spill edge, attenuation wedge.
- Best generator: static triangular mesh with animated pressure/vorticity, then curved-edge membrane.

### Sun / Ripple Fields

- Circle: central orb or pulse origin.
- Crescent: phase arcs around radial pressure.
- Trigon: ray-like or release cells from radial lobes.
- Best generator: circular membrane modes or seed/ripple overlap, with strict internal review language.

### Projection Layers

Use the topology grammar as layered output, not one flattened render:

- substrate layer: hidden or low-alpha mesh, membrane, or nodal outline;
- event layer: circles for impacts, vortices, and origins;
- interface layer: crescents for shear, wake, overlap, and phase;
- cell layer: trigons for pressure and release;
- mask layer: projection clipping, water-plane depth, or Resolume alpha routing.

This lets the team route geometry into black-screen primitives, water surface overlays, dome projection, or Resolume compositing without changing the grammar.

## 10. 3D Extension

This is a later bridge, not a build requirement today.

3D topology mapping:

- Trigons -> tetrahedra, tetrahedral-octahedral honeycomb, structural CFD mesh, pressure-volume cells.
- Circles -> spheres, bubbles, closed vortical cores, impact volumes.
- Circular vortices -> tori, vortex rings, smoke-ring-like water/air structures.
- Crescents -> vortex tubes, curved sheets, shear surfaces, folded membranes.
- Networks / tilings -> volumetric meshes, field slices, skeleton graphs, particle-path bundles.

Animation concepts:

- Vortex rings drift through a transparent tetrahedral mesh.
- Spherical vortex cores activate cells as they pass.
- Tubes stretch, bend, and reconnect through the mesh.
- Shear sheets fold into crescent-like surfaces.
- 2D slices through the 3D field reveal circles, crescents, and trigons as cross-sections.
- A cymatic phase inversion in 2D becomes alternating filled volumes and transparent cells in 3D.

Practical prototype path:

1. Three.js/WebGL: transparent tetrahedral mesh plus simple torus vortex rings.
2. Three.js/WebGL: animated slicing plane that reveals 2D circle/crescent/trigon cross-sections.
3. TouchDesigner: live TOP/CHOP-driven field values, feedback, and projection routing.
4. Blender / Geometry Nodes: higher-quality tetra mesh, vortex tubes, transparent materials, and offline camera studies.

The first 3D test should be symbolic field geometry, not a physical CFD solve: a tetrahedral mesh, moving torus rings, and a slicing plane are enough to prove the visual bridge.

## 11. Practical Feasibility

Feasible today in Python/OpenCV:

- Raster SDF circle-overlap arrangements.
- Connected-component cell extraction.
- Boundary-source classification into circle/crescent/trigon.
- Delaunay or triangular mesh recipes with scalar pressure fields.
- Fixed-mesh animated field states.
- Low-recursion Apollonian or circle packing tests.
- Offline frame sequences for rain, ripple, snowflake, and network studies.

Better later in TouchDesigner/WebGL:

- Real-time shared-edge mesh deformation.
- GPU standing-wave field evaluation.
- Interactive vortex fields and particle/mesh coupling.
- Projection-layer routing with live opacity, masks, and phase.
- 3D vortex rings through transparent tetrahedral meshes.
- Audio or visitor-input modulation once the topology contract is stable.

Better later in Blender / Geometry Nodes:

- Transparent volumetric studies.
- Tetrahedral-octahedral honeycomb staging.
- Vortex tubes, shear sheets, and camera fly-throughs.
- High-quality projection test plates.

## 12. Five Practical Render Recipes

These are render recipes only as implementation designs. No rendering is required in this document.

### 1. Static Delaunay Pressure Mesh

Purpose: prove the trigon-as-structure mapping without decorative grid behavior.

- Substrate: seeded Delaunay triangulation over a water plane or circular membrane.
- Primitive mapping: trigons are pressure cells; circles appear only at pressure extrema or vortex cores; crescents appear on high-shear edges between neighboring triangles.
- Animation: keep geometry fixed; animate scalar pressure and line weight through the cells.
- Python/OpenCV today: strong. Generate mesh, rasterize triangles, compute per-cell values, export recipe JSON or offline frames.
- TD/WebGL later: useful for live field modulation and projection mapping.
- Success criterion: the viewer reads a breathing pressure surface, not a triangle pattern.
- Do not do: no uniform full-bright triangle grid, no random color per cell, no isolated decorative circles.

### 2. Shared-Edge Curved Trigon Membrane

Purpose: test exact gap-free deformation where triangles bulge into lenses and crescents.

- Substrate: triangular mesh with explicit shared edge objects.
- Primitive mapping: each cell begins as a trigon; edge curvature produces crescent-like interfaces; closed high-pressure pockets become circle/oval cells.
- Animation: edges bulge and relax with a damped wave or standing-wave phase.
- Python/OpenCV today: moderate for recipe data and offline rasterization.
- TD/WebGL later: best path for real-time membrane deformation.
- Success criterion: no cracks or overlaps appear as cells deform; adjacent cells share the same moving boundary.
- Do not do: no independent per-triangle warping that opens gaps; no wobbly wallpaper.

### 3. Circle-Overlap Rain Interference

Purpose: use rain impacts to generate circles, crescents, and trigons from actual overlap topology.

- Substrate: time-staggered circular wavefronts from rain impacts.
- Primitive mapping: circles are impact origins; two-wave overlaps become crescents/lenses; three-wave gaps become curved trigons.
- Animation: impacts spawn, expand, overlap, then fade; phase inversion can swap fill and outline.
- Python/OpenCV today: very strong. SDF masks, bitmask regions, contours, and connected components are enough.
- TD/WebGL later: best for live rain, touch, audio, or projection interaction.
- Success criterion: crescents and trigons appear because wavefronts meet, not because they were scattered by hand.
- Do not do: no raindrop grid, no dense ripple shader, no all-over seed pattern.

### 4. Vortex-Circle Shear Field

Purpose: connect the primitive grammar to fluid-dynamics-inspired motion.

- Substrate: analytic vortex particles moving through a bounded 2D field.
- Primitive mapping: circles mark vortex cores; crescents mark shear/strain zones between interacting vortices; trigons fill or outline pressure cells in a Delaunay mesh between cores.
- Animation: vortex cores advect slowly; crescents stretch along shear; trigons pulse where pressure changes.
- Python/OpenCV today: moderate. Use simple analytic velocity and vorticity fields, not full CFD.
- TD/WebGL later: strong for live interaction and richer flow.
- Success criterion: circles, crescents, and trigons read as one flow system.
- Do not do: no spinning symbols disconnected from the velocity field; no claim of accurate CFD.

### 5. Cymatic Cell Inversion Network

Purpose: unify snow, sun/ripple, water membrane, and network visuals under one standing-wave cell extractor.

- Substrate: analytic scalar field from radial modes, multi-emitter ripples, or a graph-based wave network.
- Primitive mapping: closed antinode cells become circles/ovals; two-arc cells become crescents; three-way gaps become trigons; nodal lines become outlines or network paths.
- Animation: outline -> positive fill -> outline -> inverse fill -> outline.
- Python/OpenCV today: strong with NumPy fields and contour extraction.
- TD/WebGL later: best for real-time phase inversion, audio modulation, and projection-layer routing.
- Success criterion: cells breathe through phase while their topology remains legible.
- Do not do: no flickering full-field threshold, no metaphysical framing, no public claim that the geometry is Austin-approved.

## 13. Minimal Recipe Data Model

Future prototypes should describe topology before drawing:

```json
{
  "prototype_id": "primitive_tiling_topology_v001",
  "cultural_status": "internal",
  "field_type": "delaunay_pressure_mesh",
  "tiling_status": "exact_partition",
  "cells": [
    {
      "id": "cell_001",
      "topology_class": "trigon",
      "role": "pressure_cell",
      "boundary_source_count": 3,
      "neighbors": ["cell_002", "cell_003", "cell_004"],
      "field_values": {
        "pressure": 0.72,
        "vorticity": 0.14,
        "strain": 0.38
      }
    }
  ],
  "events": [
    {
      "id": "vortex_001",
      "primitive": "circle",
      "role": "vortex_core",
      "activates_cells": ["cell_001", "cell_008"]
    }
  ],
  "invalid_if": [
    "full_lattice_rendered_as_wallpaper",
    "circle_field_without_origin_roles",
    "crescent_without_interface_or_shear_role",
    "generic_triangle_grid_without_pressure_or_structure_role",
    "public_or_cultural_claim"
  ]
}
```

The renderer should fail before drawing if a visible primitive has no topology class, role, origin or field reason, adjacency context, and cultural status.

## 14. Recommendation

Immediate internal path:

1. Start with `Static Delaunay Pressure Mesh`.
2. Add `Circle-Overlap Rain Interference`.
3. Add `Cymatic Cell Inversion Network`.
4. Prototype `Shared-Edge Curved Trigon Membrane`.
5. Keep `Vortex-Circle Shear Field` as the bridge into later TouchDesigner/WebGL.

Later 3D path:

1. Three.js/WebGL transparent tetrahedral mesh.
2. Torus vortex rings drifting through it.
3. Animated slicing plane that reveals 2D topology classes.
4. TouchDesigner or Blender/Geometry Nodes once the 2D classification and review language are stable.

This gives the team a bridge from 2D cymatics into 3D fluid geometry without needing to build the 3D system today.

## 15. Cultural And Safety Boundary

Allowed internal exploration:

- Mathematical topology classes: one-boundary, two-arc, three-sided cells.
- Physics-inspired mappings: pressure, vorticity, shear, membranes, standing waves, and flow topology.
- Rain, water, snowflake, sun/ripple, network, and projection-layer studies framed as internal field geometry.
- Python/OpenCV, TouchDesigner, WebGL, or Blender prototypes that carry `cultural_status: internal`.

Not allowed by this document:

- Public projection or publication as Austin-approved grammar.
- Claims that the topology classes have traditional meanings.
- Claims that this is Coast Salish visual grammar.
- "Sacred geometry" as cultural authorization.
- Figure, crest, clan, named being, face, eye-pair, fish, bird, sun/sky, or exact Austin-source use without separate Austin review.
- Using mathematical overlap or fluid vocabulary to bypass consent.

This workstream should be described as internal mathematical/physics-inspired design research. Austin review is still required before any public-facing grammar, figure use, source-derived language, or cultural interpretation.

## Appendix A. Seed/Flower Overlap Cell Extraction

This is the concrete extraction algorithm for seed-of-life or flower-of-life style circle-overlap topology. The output is a cell arrangement that can be classified into circle-like, crescent/lens, curved-trigon, or compound/network cells. The construction circles can remain hidden.

Algorithm:

1. Place circle centers in hexagonal rings.
   - Start with one center at `(0, 0)`.
   - Add ring `r = 1..N` on the axial hex grid.
   - Convert axial coordinates to 2D with equal spacing, usually one radius apart for seed/flower overlap studies.
   - Assign every circle a stable `source_id`.

2. Compute the arrangement/intersections of circles.
   - For each circle pair, compute intersection points where their boundaries cross.
   - Split each circle boundary into arc segments between intersection points.
   - Keep parent metadata on every arc: `source_id`, center, radius, start angle, end angle, and neighboring sources.

3. Extract bounded regions.
   - Treat arc endpoints as graph vertices and arc segments as directed half-edges.
   - Walk closed loops by always taking the next boundary edge with consistent winding.
   - Discard the unbounded exterior loop and tiny numerical slivers.
   - Store each region as an ordered list of parent arcs.

4. Classify each region by boundary arc count.
   - `1` arc or one closed curve -> circle-like closed cell.
   - `2` arcs -> crescent / lens / lune.
   - `3` arcs -> curved trigon.
   - `4+` arcs -> compound cell / network cell; usually keep as construction topology or simplify before rendering.

5. Render region fills/edges.
   - Draw selected region fills, outlines, or both.
   - Optionally hide the construction circles and show only extracted cells.
   - Preserve region metadata so every visible cell knows its source circles and topology class.

6. Animate by adding rings and phase-inverting fills/edges.
   - Add hex rings over time: center, first ring, second ring, then wider flower field.
   - Fade construction circles down as extracted cells become legible.
   - Use standing-wave staging: outline -> selected fills -> outline -> inverse fills -> outline.
   - Keep topology stable per ring step; do not let threshold flicker create unstable cell identities.

Practical note: Python can prototype this either exactly with a planar arc graph, or approximately with raster SDF masks and OpenCV contours. The exact arc graph is cleaner for classification. The raster path is faster to test and aligns with the existing OpenCV extraction pipeline.
