# Smooth Fluid Primitive Grammar Prototype - 2026-05-20

Status: internal prototype brief only. No rendering. This is not Austin-approved, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Related docs:

- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `docs/space-center/primitive-pattern-language-next-system-2026-05-19.md`
- `docs/space-center/austin-informed-water-phrase-recipes-2026-05-19.md`

## Goal

Stop using crude particle drift, Cartesian grids, and random primitive fields. The next visual substrate should feel like smooth water, current, pressure, and membrane behavior while preserving clear primitive phrase grammar.

The fluid substrate should usually be invisible or understated. It should provide:

- Smooth tangents for primitive orientation.
- Curvature and pressure points for circle/oval anchors.
- Wavefronts for crescent phase placement.
- Eddies for rotation and cupping.
- Boundaries and membranes for containment.
- Flow networks for sparse phrase routing.

The primitives remain the authored visual language. The simulation is the motion and placement engine, not the main image.

## Substrate Options

### Curl Noise

Use for continuous current without grid artifacts. Curl noise gives divergence-free motion, so marks drift in coherent loops rather than sliding as random particles.

- Best use: ambient river/current drift, kelp-like flow, subtle mist transport.
- Primitive attachment: sample velocity for tangent; sample curl magnitude for eddy likelihood.
- Constraint: use low-frequency fields and long lifetimes. High-frequency curl becomes busy and decorative.

### Streamlines

Use for stable phrase paths. Integrate velocity fields into curves, then place primitives along the curves.

- Best use: river bend phrases, S-curve current chains, flow networks.
- Primitive attachment: circle at streamline source, bend, knot, or pressure node; crescents along tangent; trigon at release or downstream attenuation.
- Constraint: streamlines should be hand-pruned or ranked by topology. Do not fill the frame with every possible line.

### Navier-Stokes / Simple Fluid Sim

Use for pressure, advection, vorticity, and boundary-aware motion. A lightweight 2D stable-fluid solver is enough; this does not need physically exact water.

- Best use: eddies near rocks, current knots, wave pressure, membrane pushing.
- Primitive attachment: pressure peaks become circle/oval anchors; vorticity centers become eddies; velocity advects phrase origins.
- Constraint: do not render dense dye as the final look. Use the sim to place sparse phrases.

### Reaction-Diffusion-Like Fields

Use as a slow activation field, not as a literal texture. The field can decide where a phrase thickens, splits, fades, or becomes mist.

- Best use: mist partial phrases, shoreline foam thresholds, soft emergence/disappearance.
- Primitive attachment: activator peaks trigger crescents; inhibitor zones keep open water empty.
- Constraint: avoid all-over organic patterning. The phrase must remain visible.

### Membrane Waves

Use for water surfaces, boundaries, and pressure ripples. Treat membranes as soft contained surfaces, not generic sine waves.

- Best use: pond ripple, wave crest/trough, water-plane perspective, boundary pressure.
- Primitive attachment: circle at impulse or pressure node; crescents on wavefronts; trigon at attenuation/spill edge.
- Constraint: wavefronts should generate phrase arcs, not generic concentric rings.

### Signed-Distance Fields

Use for clean primitive shape evaluation, clipping, containment, and soft surface integration.

- Best use: preserving circle/crescent/trigon identity while blending with water masks or membranes.
- Primitive attachment: primitives are SDF objects; water masks and membranes are SDF boundaries; clipping is deterministic.
- Constraint: SDF effects must not blur the primitive into an unreadable fluid texture.

### Spline Advection

Use as the immediate production path. Author a small number of splines, advect or deform them smoothly, then attach phrase units to arc-length positions.

- Best use: next 48-hour prototypes, because it gives beauty and control without solver complexity.
- Primitive attachment: splines define tangent, curvature, compression, release, and phase timing.
- Constraint: spline count stays low. Each spline should carry one readable phrase or phrase family.

## Primitive Attachment Rules

### Streamlines

- Circle/oval: source, bend pressure, knot, or origin.
- Crescents: placed at arc-length offsets downstream, rotated by tangent, cupping back toward origin or local curvature center.
- Trigon: placed at release end, pointing with tangent.
- Spacing: compress at high curvature or constriction, open on calm segments.

### Wavefronts

- Circle: impulse or pressure node.
- Crescents: sampled along expanding wavefront arcs, not full rings.
- Trigon: late-stage attenuation mark where the wavefront thins or spills.
- Motion: circle pulses first; crescents expand and soften; trigon appears last and fades first.

### Eddies

- Circle/oval: vorticity center, pressure node, or current knot.
- Crescents: orbit or cup the eddy center, with one dominant incoming arc and one return arc.
- Trigon: release from the eddy into downstream flow.
- Motion: rotation must be coherent and slow enough to read as cupping, not spinning symbols.

### Membranes

- Oval/outline/SDF mask: boundary or contained water surface.
- Circle: pressure node on membrane.
- Crescents: wave or shear arcs moving along the membrane.
- Trigon: release where membrane pressure exits or attenuates.
- Motion: child primitives stay inside the membrane unless explicitly marked as spill, spray, or review exception.

### Pressure Nodes

- Circle/oval: pressure peak, impact, joint, or pivot.
- Crescents: phase around the pressure node.
- Trigon: points from high pressure toward release.
- Motion: pressure grows before visible expansion; primitive phrase follows the pressure gradient.

### Flow Networks

- Line/spline graph: nodes are sources, bends, confluences, eddies, or exits.
- Circle/oval: graph nodes.
- Crescents: edges where flow is held or phased.
- Trigon: terminal release on outgoing edges.
- Motion: phrases route through the graph with common-fate timing; avoid all edges firing at once.

## Five Concrete Prototype Recipes

### 1. Spline-Advection River Bend

Purpose: replace random current particles with one beautiful S-curve phrase.

- Substrate: two or three hand-authored splines, each slowly advected by low-frequency curl noise.
- Attachment: circle at the inside bend pressure point; first crescent on outside bend tangent; second crescent curls back toward the eddy lane; trigon exits downstream.
- Primitive phrase: `line guide -> circle -> crescent -> crescent -> trigon`.
- Motion: spline deforms gently; primitives follow arc length; spacing compresses at bend and opens downstream.
- Render target later: black-background additive layer or pale water-band composite.
- Success criterion: one still frame clearly reads as a river bend phrase before animation.
- Do not do: no grid streamlines, no many-dot current field, no random crescent rotation.

### 2. Membrane-Wave Pond Impact

Purpose: make pond ripple feel fluid without losing circle/crescent/trigon grammar.

- Substrate: circular membrane impulse with damped wave equation or analytic radial wavefront.
- Attachment: circle at impulse; crescents on partial wavefront arcs; trigon on the weakest attenuation edge.
- Primitive phrase: `circle impact -> crescent wavefront A -> crescent wavefront B -> trigon attenuation`.
- Motion: circle pulse drives membrane height; crescents expand and soften on wavefront arcs; trigon appears late and fades first.
- Render target later: flat head-on water phrase, no perspective initially.
- Success criterion: arcs feel water-like but are still clearly crescents, not rings.
- Do not do: no dense ripple shader, no concentric-circle look, no SDF blur that erases primitive identity.

### 3. Vorticity Eddy Cluster

Purpose: use a simple fluid solver or curl field to make eddies feel intentional.

- Substrate: 2D velocity field with one obstacle and a stable vorticity pocket downstream.
- Attachment: circle/oval at vorticity center; incoming crescent cups the node; return crescent orbits against the main flow; trigon releases downstream.
- Primitive phrase: `circle knot -> crescent incoming -> crescent return -> trigon release`.
- Motion: eddy rotation is slow and phase-locked; phrase rotates as a unit but trigon always knows the downstream exit.
- Render target later: eddy near rock/contact point inside water mask.
- Success criterion: cluster reads as topology-driven current, not decorative spinning symbols.
- Do not do: no independent particle spin, no symmetric eye-pair circles, no four-way compass burst.

### 4. Pressure-Node Wave Crest / Trough

Purpose: create wave motion with pressure and phase instead of sinusoidal wallpaper.

- Substrate: one traveling pressure ridge on a shallow-water or analytic wave surface.
- Attachment: crest crescent rides the high-pressure ridge; circle marks folding pressure; trough crescent follows lower and downstream; trigon releases at spill edge.
- Primitive phrase: `crescent crest -> circle pressure -> crescent trough -> trigon spill`.
- Motion: crest leads; circle pulses at fold; trough lags; trigon releases and fades.
- Render target later: wide water-plane phrase or black-screen layer.
- Success criterion: crest/trough reads as one relational phrase, not a repeated wave pattern.
- Do not do: no tiled sine waves, no mirrored crescent pair, no paired circles.

### 5. Flow-Network Mist And Current Transition

Purpose: test a soft bridge from visible current phrase to partial mist phrase.

- Substrate: sparse flow network with low-frequency curl noise plus reaction-diffusion-like activation controlling opacity.
- Attachment: circles only at selected pressure/source nodes; crescents ride active edges; trigons appear only at terminal release nodes; mist edges drop circle origins and keep partial crescents.
- Primitive phrase: `circle source -> crescent current -> crescent soft echo -> optional trigon release`, dissolving into `crescent -> faint crescent`.
- Motion: phrase travels through one or two graph edges, then loses the circle and becomes a partial mist phrase.
- Render target later: low-contrast internal water/mist transition.
- Success criterion: transition feels smooth and atmospheric while still phrase-based.
- Do not do: no fog particle field, no full-frame reaction texture, no many repeated origins.

## Prototype Implementation Order

1. Start with spline advection. It has the best control-to-beauty ratio.
2. Add membrane waves for pond and pressure-node tests.
3. Add curl noise as a deformation layer, not as a particle emitter.
4. Add simple fluid/vorticity only for eddy and obstacle tests.
5. Add reaction-diffusion-like activation last, and keep it invisible except as opacity/placement control.

## Minimal Data Model For Renderers

Each future prototype should emit a recipe JSON before rendering:

```json
{
  "prototype_id": "spline_advection_river_bend_v001",
  "substrate": "spline_advection",
  "cultural_status": "internal",
  "paths": [],
  "fields": [],
  "pressure_nodes": [],
  "primitive_phrases": [],
  "invalid_if": [
    "cartesian_grid_placement",
    "random_orientation",
    "generic_triangle_trigon",
    "eye_like_circle_pair",
    "unbounded_marks"
  ]
}
```

The renderer should fail before drawing if a phrase has no origin, tangent, boundary, topology reason, or cultural status.

## Approval Boundary

Safe internal exploration:

- Water-only substrates: streamlines, eddies, membrane waves, pressure nodes, flow networks, SDF clipping.
- Abstract current and mist phrases that remain sparse and non-figurative.
- Spline, field, and graph data structures that output internal debug JSON.

Austin approval required:

- Public use of any primitive grammar output.
- Fish, bird, wing, fin, rib, eye, ray, sun/sky, face, or figure semantics.
- Exact Austin source geometry, palette, source atom adjacency, or composition.
- Relief/wrapped 3D, carved-depth simulation, or James Harry sculpture-derived topology.
- Any claim that the system represents Coast Salish grammar, traditional meaning, or Austin-approved cultural language.

## Bottom Line

The next beautiful system is not more particles. It is sparse primitive phrases attached to smooth flow structures: streamlines, wavefronts, eddies, membranes, pressure nodes, and flow networks. Simulate the water to get believable motion; render the primitives so the grammar remains legible.
