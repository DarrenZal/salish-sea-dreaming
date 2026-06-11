# Primitive Topology 3D Fluid Geometry Concept Brief - 2026-05-20

Status: internal Agent F forward-looking concept brief only. No rendering. Main work today stays 2D/Resolume. This is mathematical and physics-inspired topology exploration, not Austin-approved grammar, not public-use guidance, not a cultural interpretation, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `docs/space-center/cymatics-interaction-input-design-2026-05-20.md`

## 1. Short Answer

The primitive topology grammar can extend into 3D, but it should not become an IMPACT build dependency.

The useful 3D formulation is:

```text
2D topology cells -> 3D volumes, surfaces, tubes, and slices
circle-like closed form -> sphere / bubble / vortex core / torus ring
crescent-like interface -> curved sheet / shear surface / vortex tube
trigon-like cell -> triangular face / tetrahedral volume / structural mesh cell
```

This is strongest as a post-IMPACT research bridge from 2D cymatics into 3D fluid geometry. For IMPACT, any use should be a teaser: a still concept frame, a pre-rendered reference loop, or a verbal design direction. The show-critical layer should stay with stable 2D clips, Resolume routing, and reviewed primitive/cymatic assets.

## 2. 3D Primitive Analogs

| 2D topology class | 3D analogs | Physics / geometry read | Use |
|---|---|---|---|
| Circle / one-boundary closed form | Sphere, bubble, droplet, vortex core, closed field cell | Origin, impact, pressure node, eddy center, coherent region | Rain impact volumes, bubbles, vortex particles, field seeds |
| Circular vortex | Torus, vortex ring, smoke-ring-like flow loop | Circulation around a closed loop | Vortex rings drifting through field volumes |
| Crescent / two-arc interface | Curved sheet, ribbon, folded membrane, vortex tube, shear surface | Strain, shear, wake, vortex stretching, interface between pressures | Water sheets, current folds, rollups, field boundaries |
| Trigon / three-sided cell | Triangular surface face, tetrahedron, tetrahedral-octahedral cell, triangular mesh patch | Structure, discretization, pressure/density cell, release wedge | Transparent mesh, CFD-like field scaffold, crystal facets |
| Network / tiling | Volumetric lattice, tetrahedral mesh, graph-in-volume, nodal field | Topology of flow, pressure, standing waves, membranes | Projection scaffolds, knowledge graph bridge, 3D field slices |

The key idea is not to extrude icons. It is to preserve topology roles:

- closed forms hold origins or vortices;
- interface forms carry shear, strain, and phase;
- triangular/tetrahedral forms carry structure and pressure cells;
- networks carry relationships through space.

## 3. Extending 2D Seed/Flower Cells To 3D Lattices

2D seed/flower overlap extraction starts with circles on a hexagonal lattice, computes overlaps, extracts bounded cells, then classifies cells by arc count. The 3D extension replaces circles with spheres and arcs with surface patches.

Possible 3D extensions:

- Hexagonal circle rings -> stacked hexagonal layers or close-packed sphere centers.
- 2D circles -> spheres, spherical shells, or pressure bubbles.
- 2D lens cells -> sphere-sphere intersection lenses or curved interface surfaces.
- 2D three-arc trigons -> three-sphere intersection pockets or tetrahedral gaps.
- 2D compound cells -> volumetric network cells or lattice voids.

Implementation read:

```text
place sphere centers -> compute sphere intersections / Voronoi cells -> extract bounded volumes and surface patches -> classify by source count and face count -> slice or render selected cells
```

A practical route is not exact constructive solid geometry first. Start with a point lattice and its duals:

- Use close-packed sphere centers as the seed field.
- Build a Delaunay tetrahedralization for structural cells.
- Use Voronoi regions as pressure volumes around points.
- Treat selected sphere shells as origins or vortex cores.
- Use slicing planes to recover 2D circle/crescent/trigon cross-sections for continuity with the existing grammar.

This keeps the 3D system legible and avoids dense ornamental flower-of-life volume wallpaper.

## 4. Vortex Rings / Tori As Circular Primitives

A vortex ring is the strongest 3D analog of a circle that moves like fluid instead of sitting as a sphere.

3D role:

- Torus geometry marks a circular vortex.
- The tube radius carries vortex thickness or energy.
- The ring radius carries circulation scale.
- Motion direction is normal to the ring plane.
- Internal phase can rotate around the torus to imply circulation.

Visual use:

- A torus ring passes through a transparent tetrahedral field.
- Cells near the ring brighten, invert, or outline.
- A slicing plane cuts the torus, revealing paired circle-like cross-sections in 2D.
- Several rings interact without needing a full CFD solve.

The torus should be framed as a field primitive: vortex ring, water/air circulation, or pressure loop. Do not present it as cultural symbolism.

## 5. Crescents As Shear Sheets, Tubes, And Surfaces

In 3D, the crescent class becomes an interface more than an object.

3D analogs:

- Curved sheet: a crescent extruded through depth, useful for water membranes and wave faces.
- Ribbon: a narrow shear band following a streamline.
- Vortex tube: a curved tube whose centerline bends like an S-crescent.
- Folded membrane: a surface that cups a vortex core or pressure origin.
- Shear surface: a translucent surface between two moving fields.

Animation roles:

- Stretch along velocity direction.
- Fold around a vortex core.
- Peel off from a pressure front.
- Roll into a tube during Kelvin-Helmholtz-like motion.
- Reconnect or dissolve when the field phase changes.

The useful mapping is "crescent = interface under strain." That is stronger than making a 3D crescent sculpture, and it ties directly back to 2D water, rain interference, cymatic phase, and network edges.

## 6. Trigons As Tetrahedral Mesh Or Triangular Surface Cells

Trigons are the easiest primitive to make structural in 3D.

3D analogs:

- Triangular surface face.
- Tetrahedral volume cell.
- Tetrahedral-octahedral honeycomb component.
- Delaunay tetrahedron in a point cloud.
- Boundary triangle on a membrane mesh.

Fluid / field role:

- Pressure cell.
- Density cell.
- CFD-like discretization element.
- Crystalline snow facet.
- Directional release wedge.
- Projection mesh patch.

Best behavior:

- Keep trigons as low-opacity structure, not the main spectacle.
- Let field values activate selected cells.
- Use circles/spheres and tori as event sources.
- Use crescent sheets/tubes as active interfaces.
- Use triangular faces as the scaffold that makes motion legible.

The 3D trigon should usually be transparent, wireframe, or subtly filled. Dense bright tetrahedra will read as generic sci-fi mesh before they read as primitive topology.

## 7. Three.js / WebGL Prototype Idea

Prototype name: `transparent_tetra_vortex_slice_v001`

Purpose: prove that the 2D primitive topology grammar can be seen as slices and events inside a 3D field.

Scene:

- A sparse transparent tetrahedral or triangular mesh in a bounded volume.
- One to three torus vortex rings drifting through the volume.
- Small spheres at selected vortex cores or pressure origins.
- Curved translucent ribbons/sheets trailing behind rings as shear surfaces.
- An animated slicing plane that cuts through the volume and shows 2D cross-section cells.

Interaction:

- Mouse or MIDI controls ring speed, phase, and slicing-plane depth.
- A slow automatic camera orbit is enough for first proof.
- Field values can be procedural: distance to vortex ring, distance to sphere, and mesh-cell depth.

Rendering style:

- Black background.
- Low-opacity mesh lines.
- Sparse highlighted cells only.
- No texture-heavy material pass.
- No Austin-derived palette or exact-source visual language.

Data model:

```json
{
  "prototype_id": "transparent_tetra_vortex_slice_v001",
  "cultural_status": "internal",
  "geometry": {
    "mesh_type": "tetrahedral_or_triangular_scaffold",
    "vortex_primitives": ["torus_ring", "sphere_core"],
    "interface_primitives": ["curved_sheet", "ribbon_tube"],
    "slice_planes": ["xy_phase_slice"]
  },
  "visible_roles": [
    "vortex_core",
    "vortex_ring",
    "shear_surface",
    "pressure_cell",
    "cross_section_topology"
  ],
  "invalid_if": [
    "full_mesh_becomes_visual_wallpaper",
    "public_or_cultural_claim",
    "2d_resolume_layer_not_yet_stable",
    "viewer_cannot_read_primitive_roles"
  ]
}
```

Why Three.js first:

- Fastest path to browser-viewable 3D.
- Good enough for transparent meshes, tori, spheres, ribbons, and slicing planes.
- Easy to share as a concept prototype without installing TouchDesigner.
- Keeps the build isolated from the show-critical Resolume stack.

## 8. TouchDesigner / Blender Later Path

### TouchDesigner

Best for live field geometry after the 2D layer works.

Use when:

- 2D primitive/cymatic clips are stable in Resolume.
- There is a clear need for live interaction, audio modulation, or projection routing.
- The mesh can be reduced to stable TOP/CHOP/SOP data.

Likely TD structure:

- SOP geometry for tetra/triangular mesh.
- Geometry COMP for torus rings, spheres, and ribbon sheets.
- CHOP channels for phase, velocity, ring radius, slice depth, opacity, and event triggers.
- TOP feedback or GLSL for field/slice visualization.
- Spout/NDI into Resolume only after rehearsal.

### Blender / Geometry Nodes

Best for high-quality post-IMPACT studies and offline teasers.

Use when:

- A polished concept plate or animation is needed.
- Transparent volumetric material, refraction, pearl-like surface, or camera choreography matters.
- Geometry Nodes can instance tetra cells, spheres, vortex tubes, and slice planes with stable attributes.

Likely Blender structure:

- Geometry Nodes point lattice -> tetra or triangular scaffold.
- Torus rings with animated paths.
- Curved Bezier tubes or surfaces for shear.
- Transparent materials with depth-aware opacity.
- Camera fly-through or orthographic slice pass.

Blender should not become an IMPACT dependency unless it is generating pre-rendered content that has already been reviewed and routed safely.

## 9. IMPACT Teaser Vs Post-IMPACT

### Useful For IMPACT Teaser

Only if it does not compete with 2D delivery:

- One still diagram in an internal review deck.
- A short pre-rendered or mocked concept loop labeled as future research.
- A verbal bridge: "The 2D topology layer could later become a 3D field of vortices, membranes, and tetrahedral cells."
- A cross-section explanation: 3D field slices can return to the same 2D circle/crescent/trigon grammar.
- A post-show roadmap note for MOVE37XR / DEVCON / Life at Center.

Do not make this a live show feature for IMPACT unless the 2D layer is already stable, reviewed, and rehearsed.

### Better Post-IMPACT

Post-IMPACT is the right window for:

- Three.js proof of concept.
- TouchDesigner field prototype.
- Blender/Geometry Nodes hero study.
- 3D slice-to-2D topology classifier.
- Audio-reactive vortex ring tests.
- Dome-friendly field camera choreography.
- Integration with network/knowledge-graph visuals.

The 3D lane should become a research branch after the immediate 2D/Resolume pipeline is reliable.

## 10. Relation To Rain, Water, Cymatics, Snow, Sun/Ripple, And Networks

Rain:

- 2D impacts become 3D droplets, bubbles, and expanding spherical shells.
- Overlapping shells generate lens-like surfaces and three-way pockets.

Water:

- Vortex rings, sheets, and tubes give a stronger fluid read than flat particle drift.
- Slicing through the 3D field can produce 2D water-surface primitives.

Cymatics:

- 2D nodal outlines become 3D nodal surfaces.
- Antinode cells become filled volumes.
- Phase inversion swaps filled and transparent volumes.

Snow:

- 2D sixfold cells become crystalline lattices, tetra/octa facets, and branching sheets.
- Keep this mathematical and internal; avoid public symbolic claims.

Sun / ripple:

- A central sphere or torus can drive radial field surfaces and triangular release cells.
- Austin-derived sun/sky semantics remain review-needed.

Networks:

- Nodes become spheres or vortices.
- Edges become tubes or shear ribbons.
- Mesh cells become pressure or relation volumes.
- A slicing plane lets the network return to a 2D projection layer.

## 11. Why Not Before The 2D Layer Works

3D adds complexity without solving the urgent show problem.

Reasons to defer:

- Resolume needs stable 2D media and routing first.
- Austin review language is already delicate in 2D; 3D adds new visual ambiguity.
- Transparent meshes, tori, and tubes can become generic sci-fi quickly.
- Live 3D introduces GPU, projection, camera, frame-rate, and compositing risk.
- The primitive roles are easier to validate in 2D still frames and short loops.
- If circle/crescent/trigon topology is not readable in 2D, it will be less readable in 3D.
- The 3D work could distract from show-critical deliverables for IMPACT 2026.

Gate before building:

1. 2D topology classifier or recipe model exists.
2. At least one 2D water/cymatic primitive loop is stable in Resolume.
3. Safety language is settled: internal math/physics exploration only.
4. The 3D prototype has a narrow proof target: vortex rings plus tetra mesh plus slicing plane.
5. No live-show dependency is created.

## 12. Recommendation

For now:

- Keep IMPACT focused on 2D/Resolume.
- Preserve this 3D path as a concept bridge and post-IMPACT research lane.
- If a teaser is needed, use one short internal concept note or still-frame storyboard, not a new live system.

First later build:

```text
Three.js transparent tetra mesh
  + torus vortex rings
  + sphere vortex cores
  + crescent-like shear ribbons
  + animated slicing plane
  -> 2D cross-section cells classified as circle / crescent / trigon
```

That prototype is enough to test whether the grammar survives the jump from 2D topology into 3D fluid geometry.

## 13. Safety Boundary

Allowed internal exploration:

- Mathematical topology analogs in 3D.
- Physics-inspired vortices, shear surfaces, tetrahedral meshes, and cymatic fields.
- Rain, water, snow, sun/ripple, and network visuals as internal field geometry.
- Three.js, TouchDesigner, or Blender prototypes carrying `cultural_status: internal`.

Not allowed by this document:

- Public projection or publication as Austin-approved grammar.
- Claims that 3D topology classes have traditional meanings.
- Claims that this is Coast Salish visual grammar.
- Using "sacred geometry" as cultural authorization.
- Figure, crest, clan, named being, face, eye-pair, fish, bird, sun/sky, or exact Austin-source use without separate Austin review.
- Using 3D complexity to bypass consent, review, or the 2D grammar gates.

This should be framed as internal mathematical/physics-inspired design research. The 3D lane is a future bridge, not a shortcut around the 2D review and production pipeline.
