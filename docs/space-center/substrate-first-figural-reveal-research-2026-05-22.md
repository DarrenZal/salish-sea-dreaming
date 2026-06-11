# Substrate-First Figural Reveal Research - 2026-05-22

Status: INTERNAL RESEARCH NOTE ONLY. No rendering performed. No renderer code
written. No source artwork modified. No scripts modified. This is a survey and
comparison of candidate substrate frameworks against the current wave-
interference architecture; it is not a build order, not a scout, not a
clearance to ship, and not a cultural-meaning claim. Per
[austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md),
Austin remains authority on meaning and on final external use. The substrates
discussed below are technical reveal grammars; any candidate that proceeds must
still pass the figural acceptance gate and per-output Austin sign-off per
[austin-consent-map.md](austin-consent-map.md).

Read with:

- [figural-orca-wave-interference-match-research-scout-2026-05-22.md](figural-orca-wave-interference-match-research-scout-2026-05-22.md)
- [figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md](figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md)
- [abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md)
- [figural-fluid-dynamics-reveal-scout-2026-05-22.md](figural-fluid-dynamics-reveal-scout-2026-05-22.md)
- [arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md)
- [primitive-composition-renderer-pivot-plan-2026-05-21.md](primitive-composition-renderer-pivot-plan-2026-05-21.md)

## 1. The Problem To Settle

### 1.1 What the wave-interference scouts established

Two Orca scouts tested whether Austin's internal primitive composition can be
matched by a wave-interference field that emits circles, crescents, and trigons
as field-derived regions rather than drawn overlays.

- **Type 1 (overlap regions).** Predicted primitives are construction-circle
  overlap cells: ovoid `count >= 1`, crescent `count >= 2` (two-circle vesica
  lens), trigon `count >= 3` (three-circle overlap cell). Eight of eight local
  fits passed at centroid-error and IoU thresholds. Global field read was
  `mixed` for all three sampled source configurations (`18`, `11`, `9`
  sources): the asymmetric all-source count map produced `11-17` spurious
  count>=2 components in addition to the targeted cells.
- **Type 2 (gap/cup regions).** Predicted primitives are bounded-complement
  cells: cup-style crescent is `inside outer AND outside cutter`; gap-style
  trigon is the bounded complement outside three near-but-not-overlapping
  circles. Type 2 was worse than Type 1 on `5` of `5` focus targets. Type 2
  off-target area was `373314` px with `16` components >= 1200 px. Global
  coherence remained scattered.

### 1.2 What this means

Local construction-circle fits to authored anchors are tractable. Global field
coherence under both Type 1 and Type 2 is not. The shared failure signature
across both scouts is **spatial non-locality**: in a wave-interference model,
every source contributes to the count/feature field at every position, so an
asymmetric multi-source configuration sufficient to hit all internal primitive
anchors also produces incidental overlap/gap cells everywhere else. The result
reads as a constellation of independent local devices instead of as one Orca-
bound field.

This is structural, not a tuning problem. Adding more sources to improve one
local fit worsens the spurious-feature density elsewhere. Removing sources
restores cleanliness but loses anchors. There is no monotone direction in
source-count space that gives both local fit and global coherence for an
asymmetric figural target inside a fixed wave-equation framework.

### 1.3 Darren's reframe

> Instead of asking "what dynamics produces primitives at specified positions?",
> ask: "what curved-flow substrate naturally produces gap-relationships at
> these positions?"

The reframe moves the design variable from `placement of sources inside a
fixed wave field` to `choice of the underlying substrate itself`. A different
substrate may have a feature vocabulary whose natural geometry is closer to
Austin's primitive grammar, may have stronger spatial locality, and may admit
a more tractable inverse problem.

The remaining sections survey candidate substrates against that question. The
hypothesis under test is not "field models can do this." The hypothesis under
test is "is there a substrate whose default features are closer to circles,
crescents, trigons, cups, and arc-bounded regions, and whose inverse problem
is tractable enough to author an Orca-coherent composition?"

## 2. Evaluation Criteria

Each candidate substrate is evaluated on six axes:

| Axis | What it asks |
|---|---|
| Feature vocabulary | What shapes does the substrate produce by default, with no styling? |
| Primitive fit | Does that vocabulary naturally include circle, crescent, trigon, cup, arc-bounded region? |
| Control locality | Does a local design change affect a local region (high) or the whole field (low)? |
| Inverse tractability | Given target primitive positions/relationships, can a substrate configuration be solved or searched in reasonable effort? |
| Figural coherence plausibility | Could it bind an Orca composition into one reading rather than a constellation? |
| Implementation cost | Solo-operator cost to a first scout (research-only, scout, first MP4) |

A substrate need not score high on every axis; the priority order is feature
vocabulary -> inverse tractability -> figural coherence -> control locality ->
implementation cost. Primitive fit is the gate: a substrate whose default
features are not in the crescent/trigon/cup/arc-bounded family is rejected
regardless of how cheap it is.

This mirrors the gate ordering in
[abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md)
Section 3: a probe that smuggles primitives back in via overlay tells us
nothing about whether the substrate carries them.

## 3. Candidate Substrate Survey

### 3.1 Continuous vector fields with attractor / repeller poles

**Mechanism.** Place a set of poles on the canvas; each pole contributes a
local pull (attractor), push (repeller), or rotation (vortex) to the vector
field. The visible substrate is rendered as streamlines, LIC (line integral
convolution) texture, or particle trace density.

**Feature vocabulary.** Streamline patterns around poles: closed loops near
attractors, hyperbolic crossings at saddle points, vortex rotation cells.
Negative-space regions form where streamlines diverge or accelerate.

**Primitive fit.** Strong for circle-like (vortex rotation cells produce
near-circular streamline loops). Moderate for crescent-like (streamlines bend
around an attractor adjacent to a repeller produce cupped bands; the cup
direction is set by the pole sign). Moderate for trigon-like (three-way saddle
or triple-junction points where three streamlines meet produce arc-bounded
triangular cells). Strong for arc-bounded regions in general.

**Control locality.** High in practice. A pole's influence falls off with
distance (typically `1/r` or `1/r^2`); placing a new pole near an Orca eye
anchor changes the streamline topology near that eye without rewriting the
rest of the field. This is the structural opposite of wave interference, where
every source contributes equally at every position.

**Inverse tractability.** High. The mapping from pole configuration to
streamline topology is reasonably direct. For a desired primitive at a target
position, place an attractor or vortex at that position with strength tuned to
the desired cell radius; the streamlines self-organize around it. A solver is
not required for a first scout; manual placement is workable.

**Figural coherence plausibility.** Plausible. Streamlines are global
solutions to an ODE, so the field is intrinsically continuous. There are no
spurious overlap cells because the substrate doesn't sum sources; it
integrates them into a single flow.

**Implementation cost.** Low. `scipy`, `numpy`, and a basic LIC implementation
or a particle trace render are enough for a first scout. Could reuse parts of
the existing morph_engine or telus_abstract_cymatic_batch harness for output
plumbing.

**Risk.** Vector field renderings tend to read as physics-simulation
aesthetics (smoke trails, magnetic field lines, fluid flow). Without careful
styling, the result may not feel like the cymatic / Coast Salish primitive
grammar even if the topology is right.

### 3.2 Curved vector fields / streamline topology with explicit topology authoring

**Mechanism.** Same substrate as 3.1 but with the design surface raised one
level: instead of placing poles, the operator places saddle points, sources,
sinks, and limit cycles directly, and the field is reconstructed (Helmholtz-
Hodge decomposition or direct topology synthesis).

**Feature vocabulary.** Same as 3.1 plus explicit limit cycles (closed
streamline loops that act as crescent/oval boundaries) and explicit
separatrices (curves that bound arc-shaped regions).

**Primitive fit.** Slightly stronger than 3.1 because limit cycles and
separatrices map directly to crescent/trigon boundaries. Arc-bounded regions
are first-class.

**Control locality.** Same as 3.1.

**Inverse tractability.** Higher than 3.1 for complex compositions, lower for
simple ones (more solver machinery). Topology synthesis is a researched area
(`Theisel et al.` and similar work on vector field design) but the
implementation is heavier than direct pole placement.

**Figural coherence plausibility.** Plausible, same reasoning as 3.1.

**Implementation cost.** Moderate to high for a first scout. Topology
synthesis solvers exist in research code but are not pip-installable; a
custom implementation is a meaningful side project.

**Risk.** Same aesthetic risk as 3.1, plus the cost of pulling in a non-
trivial solver before knowing whether the substrate clears the figural gate.

### 3.3 Vorticity fields and vortex pair / vortex sheet arrangements

**Mechanism.** Define a scalar vorticity field on the canvas (positive and
negative vortex cores). Integrate to a velocity field; advect a passive scalar
(dye, ink, smoke) under the velocity for a short time; render the scalar
density.

**Feature vocabulary.** Vortex cores (circles), vortex pairs producing cupped
"mushroom" shapes (crescents), vortex sheets rolling up into spirals, dye
filaments arc-bound by the flow.

**Primitive fit.** Strong for circle (vortex cores). Strong for crescent
(vortex pair entrainment produces visually compelling cupped bands; this is
the same mechanism that gives mushroom-cloud and Karman-vortex-street imagery
its characteristic shapes). Weak-to-moderate for trigon (three-vortex
configurations produce complex chaotic regions rather than clean three-arc
cells).

**Control locality.** Moderate. Vorticity is locally controlled, but the
advected scalar accumulates history, so a vortex placed late in the flow
affects scalar regions downstream of it.

**Inverse tractability.** Moderate. Placing vortices at desired positions is
direct; predicting the resulting scalar field requires integration. For
quasi-steady flow with short advection time, the inverse is roughly
tractable.

**Figural coherence plausibility.** Plausible. The scalar field is one
continuous evolved object, not a sum of independent sources.

**Implementation cost.** Moderate. A first scout needs a small 2D advection
solver (semi-Lagrangian or upwind), which is `~200 lines` of `numpy`.
Reasonable for a one-day spike.

**Risk.** Trigon-like cells are not a natural product. If trigons are needed
for the Orca composition, this substrate would have to combine with another
mechanism for that family.

### 3.4 Curvature fields on 2D manifolds with geodesic visualization

**Mechanism.** Define a curvature field over the canvas (or a heightmap whose
Gaussian curvature is computed). Compute geodesics from boundary or seed
points; render geodesic density or geodesic crossings.

**Feature vocabulary.** Geodesic convergence regions, caustics, focal points,
divergence regions where geodesics spread.

**Primitive fit.** Moderate-to-weak. Caustics can form arc-shaped lines and
crescent-like bright regions; circular shapes appear at point caustics. Trigon
shapes do not naturally appear.

**Control locality.** Moderate. Curvature is local, but geodesic accumulation
is path-dependent and non-local.

**Inverse tractability.** Low. The inverse problem (find a curvature field
that gives caustics at specified positions) is a researched problem in
computer graphics (caustic design for refractive surfaces) but the solvers are
heavy and the parameter space is non-intuitive.

**Figural coherence plausibility.** Uncertain. Caustics are visually
coherent in narrow regions but the global structure depends on the curvature
field in non-obvious ways.

**Implementation cost.** High. Caustic computation and geodesic tracing
require either ray-tracing infrastructure or a specialized solver.

**Risk.** Implementation cost is high relative to the moderate feature-
vocabulary score. Likely a research project, not a first scout.

### 3.5 Reaction-diffusion / Turing systems

**Mechanism.** Two-species coupled PDE (Gray-Scott, FitzHugh-Nagumo, Brusselator).
Initial conditions and parameter field control the emergent pattern.

**Feature vocabulary.** Spots, stripes, labyrinths, spiral waves, target
patterns, branching.

**Primitive fit.** Weak. Default Turing patterns are spot/stripe/labyrinth;
they do not naturally produce crescents, trigons, or cupped regions. Spiral
waves are circular but lack the cupping geometry needed for crescents.

**Control locality.** Low. Reaction-diffusion is famously sensitive to
boundary conditions and parameter values; a small parameter change can shift
the whole pattern from spots to stripes.

**Inverse tractability.** Low. The mapping from parameters/initial conditions
to specific spatial patterns is not analytically invertible; gradient descent
through a Turing solver is a research project (`differentiable Turing` work
exists but is not turn-key).

**Figural coherence plausibility.** Low for asymmetric figural targets.
Turing patterns are statistically isotropic; getting a Turing system to
produce an Orca-shaped pattern is essentially the same hard problem as the
caustic-design inverse problem, with no obvious advantage.

**Implementation cost.** Low for the forward simulation, high for the inverse
problem.

**Verdict.** Reject. Wrong feature vocabulary. The substrate's default
behavior is decorative texture, not figural primitives.

### 3.6 Schlieren / density-gradient fields

**Mechanism.** Compute the gradient magnitude of a scalar field (density,
pressure, refractive index) and render gradient ridges. Often used to
visualize shock fronts in compressible flow.

**Feature vocabulary.** Sharp ridges, shock fronts, arc-shaped discontinuity
lines.

**Primitive fit.** Moderate. Shock arcs are natural; circles form where shock
fronts curve around obstacles; cupped regions form behind blunt bodies.
Trigons do not naturally appear.

**Control locality.** Inherited from the underlying flow. If the flow itself
is a vortex/vector-field substrate, locality is moderate.

**Inverse tractability.** Same as the underlying flow problem. Schlieren is a
visualization mode, not a substrate on its own.

**Figural coherence plausibility.** Same as the underlying flow.

**Verdict.** Not a substrate; a rendering mode applied to other substrates.
Useful as a styling layer over 3.1 / 3.3 if the operator wants ridge-emphasis
output, but not a candidate in its own right.

### 3.7 Inverse fluid dynamics (target-driven flow synthesis)

**Mechanism.** Given a desired final scalar density (or velocity, or vorticity
distribution), solve backward through a Navier-Stokes or simplified flow PDE
to find initial conditions or driving forces.

**Feature vocabulary.** Whatever the flow type produces (typically vortex-pair
and vortex-sheet imagery).

**Primitive fit.** Same as 3.3.

**Control locality.** Low. The inverse problem is non-local by construction.

**Inverse tractability.** Famously hard (ill-posed; the heat equation reversed
is the classic example of an ill-posed inverse). Modern differentiable-fluid
solvers (`PhiFlow`, `JaxFluids`) make it possible but expensive.

**Figural coherence plausibility.** High in principle (the output is by
construction the target), but the cost of authoring is high.

**Implementation cost.** Very high. A first scout would need a differentiable
fluid solver and a meaningful optimization loop.

**Verdict.** Park. The forward version (3.3) gets most of the benefit at
much lower cost. Inverse fluid dynamics is a year-long research direction,
not a sprint candidate.

### 3.8 Eigenmode patterns on custom-shaped domains (Chladni-like)

**Mechanism.** Solve the Helmholtz eigenvalue problem on a custom-shaped 2D
domain. Visible substrate is the nodal lines (zeros) and antinode islands
(extrema) of an eigenfunction.

**Feature vocabulary.** Nodal-line networks, antinode cells separated by
nodal arcs. Classic Chladni-plate patterns.

**Primitive fit.** Moderate. Antinode islands can be circular or elliptical
(circle / oval fit). Nodal arcs can form crescents and arc-bounded triangular
cells (trigon fit). The grammar is closer to the wave-interference
vocabulary than most other substrates here.

**Control locality.** Low globally (each eigenmode is a property of the whole
domain) but high in the sense that domain shape is the design knob: cutting a
notch in the boundary at one location reshapes the local nodal lines.

**Inverse tractability.** Moderate. Eigenmode shape design is a researched
problem (`Chladni inverse problem`); recent work uses neural-network-guided
boundary deformation. Manual domain sketching plus mode selection is
tractable for simple compositions.

**Figural coherence plausibility.** Plausible. Each eigenmode is a single
coherent object on a single domain.

**Implementation cost.** Moderate. `scipy.sparse.linalg.eigsh` on a finite-
difference Laplacian over a masked domain is standard scientific computing;
maybe `~300 lines` for a first scout including domain authoring and
visualization. No external dependencies beyond `scipy`/`numpy`.

**Risk.** This is essentially a refined version of the existing cymatic /
Path B work in
[abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md).
If Path B passes the gate, this substrate naturally extends it. If Path B
fails the gate for the same global-coherence reason as Type 1 wave
interference, this substrate may inherit the failure.

### 3.9 Signed-distance / medial-axis fields around source silhouettes

**Mechanism.** Place a set of source primitives (points, curves, or
silhouettes) on the canvas. Compute the signed distance field (SDF) to the
union of sources. The visible substrate is:

- distance isocontours (concentric curves around sources);
- the medial axis (the set of points equidistant from two or more sources);
- gradient-magnitude ridges where the SDF transitions between source-
  influence regions.

**Feature vocabulary.** Distance isocontours around a circle source are
concentric circles. Distance isocontours around an oval source are nested
ovals. Distance isocontours around a concave region are arc-bounded crescents
that cup the source. The medial axis between three nearby sources is a Y-
shaped trigon trace whose arms terminate in triple-junction cells. Arc-
bounded regions are first-class everywhere.

**Primitive fit.** Strong across the full grammar. Circle, crescent, trigon,
cup, and arc-bounded region all have direct SDF realizations. This is the
substrate whose default features most closely match the primitive vocabulary.

**Control locality.** Very high. The SDF at a point is determined by the
nearest source; moving a source affects only its near region. This is the
strongest locality of any candidate here, including wave interference.

**Inverse tractability.** Trivial. The mapping from source placement to SDF
features is direct and intuitive: place a source where you want a circle
center; place two sources where you want a medial-axis crescent between them;
place three sources where you want a trigon-cell at the centroid.

**Figural coherence plausibility.** Plausible. The SDF is one continuous
scalar field; isocontours at each level form one set of nested curves; the
medial axis is one connected graph. There are no `count >= k` overlap regions
that grow with source count.

**Implementation cost.** Low. SDF computation is `scipy.ndimage.distance_transform_edt`
plus minor post-processing. Medial-axis extraction is `scipy.ndimage` or
`skimage.morphology.medial_axis`. A first scout is maybe `~150 lines`
including source authoring, SDF computation, isocontour and medial-axis
extraction, and a still-frame render.

**Risk.** The default SDF aesthetic is geometric and clean; without
animation, it may read as a vector-graphics diagram rather than a cymatic
field. This is fixable with styling layers (gradient noise, displacement,
opacity falloff) but the styling must be added without reintroducing the
overlay-smuggling failure mode.

**Note on relationship to existing arc-bounded notes.** The arc-bounded
region rendering notes
([arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md))
describe a target aesthetic ("cells whose edges come from wavefronts, nodal
boundaries, source rings, intersections, and negative-space cuts"). SDF /
medial-axis fields produce exactly this geometry by construction, with
provenance preserved (each cell is uniquely tied to the source set whose SDF
boundary defines it). This substrate may be the cleanest path to the v003/
v004 acceptance criteria already documented.

### 3.10 Conformal field maps

**Mechanism.** A conformal (angle-preserving) map from a simple reference
domain to the canvas. The reference domain has a clean grid; the conformal
map deforms that grid into curved coordinate lines that follow the geometry
of singularities placed in the map.

**Feature vocabulary.** Orthogonal pairs of coordinate families that bend
around singularities. Circles map to circles (Mobius transformations) or to
curves with controllable cusps (Schwarz-Christoffel).

**Primitive fit.** Moderate. Circle and crescent map naturally; trigon needs
specific singularity placement.

**Control locality.** Moderate. Conformal maps are global (a singularity
affects the entire conformal structure) but the visible deformation falls off
with distance.

**Inverse tractability.** Moderate. Conformal map construction is well-
researched (`conformal-py`, `pyconmap`) but the parameter-to-geometry
intuition is harder than SDF or vector fields.

**Implementation cost.** Moderate to high depending on chosen library.

**Verdict.** Plausible but not the strongest candidate. The grammar fit is
real but no better than 3.1, and the implementation cost is higher.

## 4. Substrate Comparison Summary

| Substrate | Feature voc. | Primitive fit | Locality | Inverse | Coherence | Cost | Gate | Note |
|---|---|---|---|---|---|---|---|---|
| 3.1 Vector field with poles | streamlines, vortex cells, separatrices | strong | high | high | plausible | low | PASS | strong runner-up |
| 3.2 Topology-authored vector field | + limit cycles, explicit separatrices | strong | high | moderate | plausible | moderate-high | PASS | research-grade variant of 3.1 |
| 3.3 Vorticity / vortex pairs | cores, mushroom shapes, sheets | moderate | moderate | moderate | plausible | moderate | PASS | weak on trigon |
| 3.4 Curvature / caustics | caustic arcs, focal points | moderate-weak | moderate | low | uncertain | high | REJECT | cost-vocabulary mismatch |
| 3.5 Reaction-diffusion | spots, stripes, labyrinths | weak | low | low | low | low/high | REJECT | wrong vocabulary for figural |
| 3.6 Schlieren | ridges | (rendering mode) | n/a | n/a | n/a | n/a | N/A | styling layer, not substrate |
| 3.7 Inverse fluid dynamics | target-driven flow | strong | low | very low | high | very high | PARK | year-long research direction |
| 3.8 Eigenmodes on custom domains | nodal lines, antinodes | moderate | low / high-via-domain | moderate | plausible | moderate | PASS | extends Path B; inherits its risks |
| 3.9 SDF / medial-axis | isocontours, medial axis | strong | very high | trivial | plausible | low | PASS | best candidate |
| 3.10 Conformal maps | orthogonal curved grids | moderate | moderate | moderate | plausible | moderate-high | PASS | no clear win over 3.1 |

Three candidates clear the gate and are cheap enough to scout: 3.1, 3.8, 3.9.
3.9 (SDF / medial-axis) scores highest on every priority axis except aesthetic
risk.

## 5. Comparison Against Current Validated Approaches

### 5.1 v004.1 radial / cymatic artwork spine

Status: validated radial spine candidate; works because the source composition
itself is radial / symmetric and the wave field's natural symmetry aligns
with it. Substrates 3.1, 3.8, 3.9 could all reproduce this radial work but
would not improve on it; the radial lane is already fit-for-purpose. Substrate
research is targeted at figural / asymmetric cases where the radial lane does
not extend.

### 5.2 Abstract Path A/B wave/cymatic support layers

Status: in flight, comparison gated by
[abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md).
Path A is direct competitor to substrate 3.9; both are field-derived primitive
emergence. Path B (2D wave PDE) is the same substrate as 3.8 (eigenmode
patterns). The substrate survey is parallel to that comparison; if both Paths
A and B fail the gate, 3.9 (SDF) is the recommended next substrate to test
because its feature vocabulary is the closest match to the arc-bounded
acceptance criteria in
[arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md).

### 5.3 Orca fluid silhouette v001

Status: silhouette-reveal approach documented in
[figural-fluid-dynamics-reveal-scout-2026-05-22.md](figural-fluid-dynamics-reveal-scout-2026-05-22.md).
Recommended architecture for figural pieces was:

```text
fluid-around-silhouette reveal
  -> full whole-source Orca fade-in
  -> optional late internal eddies/apertures at v002 primitive anchors
```

Substrate 3.3 (vorticity / vortex pairs) is the natural physics behind that
fluid-around-silhouette layer. Substrate 3.9 (SDF) could provide the
internal-anchor layer in the optional third stage: each anchor's primitive is
rendered as an SDF isocontour around a per-anchor source. The substrate
survey does not replace the silhouette-reveal recommendation; it provides a
candidate for the internal-anchor layer that the wave-interference scouts
struggled to deliver.

### 5.4 Orca Type 1 / Type 2 wave-match scouts

Status: documented in Sections 1.1 and 1.2 above. The substrate survey
proposes 3.9 (SDF) as the most promising replacement for the wave-
interference architecture used in those scouts. The local-fit story would
remain testable; the global-coherence story would be structurally different
(no `count >= k` field, no spurious overlap cells).

## 6. Most Promising Substrate and First Scout

### 6.1 Pick

**Substrate 3.9: SDF / medial-axis fields around source silhouettes.**

### 6.2 Why this has better odds than wave interference

Three structural advantages:

- **Feature vocabulary matches by default.** Distance isocontours around
  source silhouettes produce circles, nested ovals, cupped crescents (around
  concave sources), and arc-bounded triangular cells (in three-source medial-
  axis junctions). No styling pass is required to make the primitive grammar
  emerge.
- **Locality is structural, not tuned.** Each point's SDF value depends only
  on the nearest source. Adding a source for a new internal anchor cannot
  create spurious features elsewhere because the new source only "wins" the
  SDF in its own neighborhood. This is the property whose absence broke the
  wave-interference scouts.
- **Inverse problem is trivial.** Author the composition by placing source
  silhouettes; the substrate's features appear where the sources are placed.
  No solver loop, no optimization, no parameter sweep.

### 6.3 First scout design

This is a scout proposal only; no scripts written, no rendering performed.

- **Name:** `figural_orca_sdf_medial_axis_scout_v001`.
- **Source artwork:** same Orca PNG as the existing wave-interference scouts.
- **Source primitive anchors:** reuse the v001 anchor coordinates from
  [orca_wave_interference_fit_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001.json).
- **Method:**
  1. For each of the eight non-excluded internal anchors, define a source
     silhouette whose shape matches the anchor's primitive class:
     - circle / oval anchors: source is an oval matched to the anchor bbox;
     - crescent anchors: source is a pair of oval sources placed so that
       their medial-axis arc cups the anchor centroid;
     - trigon anchors: source is a triplet of oval sources placed so that
       their medial-axis triple-junction sits at the anchor centroid.
  2. Compute the union-SDF over all sources via
     `scipy.ndimage.distance_transform_edt`.
  3. Extract:
     - distance isocontours at three to five levels;
     - the medial-axis network via `skimage.morphology.medial_axis`;
     - the gradient-magnitude field for arc-bounded region detection.
  4. Render three debug stills (matching the existing scout convention):
     - source silhouettes marked over the Orca;
     - distance isocontour overlay over the Orca;
     - medial-axis overlay over the Orca with primitive cells labeled.
  5. Render one composite still: SDF-derived primitives only, with no source
     visible, for the figural-coherence read.
- **Output folder:** `track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22`.
- **Verification gate:** primitive provenance must show that every visible
  primitive cell traces back to a specific source-set boundary operation
  (mirrors the
  [arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md)
  Acceptance Rule).

### 6.4 What success looks like

- Every internal anchor has a visible SDF-derived primitive at its centroid.
- The composite still reads as one Orca composition, not as a constellation
  of independent local devices.
- The figural-coherence map (sum of distance isocontours across all sources
  on a per-pixel basis) has zero or near-zero spurious cells outside the
  Orca silhouette envelope.
- The debug medial-axis still shows a connected graph of arcs and triple-
  junctions whose topology corresponds 1:1 with the Orca primitive layout.

### 6.5 What failure looks like

- Source silhouettes for crescent and trigon anchors are difficult to place
  such that the medial-axis cell sits exactly at the target centroid (the
  inverse mapping turns out to be tractable but non-trivial). This is a
  PARTIAL pass; addressable in a second iteration.
- The SDF aesthetic reads as a vector-graphics diagram and styling cannot
  recover a cymatic / arc-bounded feel without reintroducing overlay
  smuggling. This is a STYLE failure; the substrate is right but the
  rendering layer needs more work.
- The composite still reads as separated apertures around each anchor rather
  than as one composition. This is a HARD failure of the same class as the
  wave-interference scouts and would suggest the figural-coherence problem
  is not substrate-bound but composition-bound (in which case the
  silhouette-reveal architecture in
  [figural-fluid-dynamics-reveal-scout-2026-05-22.md](figural-fluid-dynamics-reveal-scout-2026-05-22.md)
  remains the correct primary path).

### 6.6 Effort estimate

| Stage | Effort |
|---|---|
| Research-only (this document) | done |
| Scout (script + JSON + debug stills) | ~half a day for someone familiar with `scipy.ndimage` and the existing scout-output conventions |
| First MP4 render | not in scope until scout passes; add ~1 day for styling, animation timing, and loop diagnostic if scout clears the gate |

## 7. Honest Recommendation

**PROCEED.**

Recommendation: schedule `figural_orca_sdf_medial_axis_scout_v001` as the
next figural-renderer experiment, before any further iteration on the wave-
interference Type 1 / Type 2 architecture. Rationale:

- The two existing wave-interference scouts have established the limit of
  that substrate for asymmetric figural compositions; further Type 1 / Type 2
  iteration is not expected to break out of the global-coherence failure
  mode.
- The SDF / medial-axis substrate is the only candidate in this survey that
  scores `strong` on feature vocabulary, `very high` on locality, `trivial`
  on inverse tractability, and `low` on implementation cost. The other gate-
  passing candidates (3.1 vector field with poles, 3.8 eigenmodes on custom
  domains) are weaker on at least one of these axes.
- The scout is small enough to be a half-day spike. A negative result is
  inexpensive; a positive result unblocks the figural lane that the wave-
  interference scouts left in `NO-GO` status.
- The scout's success would not preempt the silhouette-reveal architecture
  recommended for figural pieces; the two are complementary (silhouette-
  reveal for whole-body binding, SDF for internal-anchor primitives).

Constraints in force:

- Internal scout only. No external surfaces, no Austin-approved framing, no
  cultural-meaning claim. Per
  [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md),
  Austin remains authority on meaning and on final external use. Outputs
  from this scout carry the Austin-authorized internal label until per-
  output Austin sign-off per
  [austin-consent-map.md](austin-consent-map.md).
- The scout produces stills only on a first pass. No MP4, no animation, no
  Resolume packaging, no loop diagnostic until the substrate clears the
  figural-coherence gate.
- The scout follows the same provenance discipline as the wave-interference
  scouts: source artwork is read-only input, all generated outputs land in
  a dated `track2-deterministic/morph_outputs_INTERNAL/` folder, JSON is
  parseable with `python3 -m json.tool`, markdown is ASCII-only.

If the scout passes, the follow-on questions are:

- Can the SDF substrate carry the radial / cymatic spine as well, replacing
  the wave-equation Path B work, or is it a figural-only substrate?
- Can the SDF substrate be animated such that the internal primitives
  "appear from" the substrate over time, or does it read best as a static
  composition revealed by separate timing layers?
- What's the smallest source-set whose SDF carries a recognizable Orca
  primitive grammar? (Source-set minimality is a useful proxy for whether
  the substrate is doing real work versus the operator authoring the answer.)

If the scout fails, the recommended next move is **not** to try another
substrate from this survey before reviewing the failure mode. A `HARD`
failure (composition reads as separated apertures) likely means the figural-
coherence problem is composition-bound, and the silhouette-reveal
architecture should carry figural pieces with substrate work confined to
support layers; a `STYLE` failure means the SDF substrate is correct but the
rendering stack needs more work; a `PARTIAL` failure means the inverse
mapping needs a small solver loop, which is a one-day add-on.

## 8. Verification

- ASCII-only content. No emojis. No special characters.
- No rendering performed by this document.
- No source artwork modification. The referenced Orca PNG was not opened,
  read, or modified by this note; the SHA-256 in Section 1.1 is reproduced
  from the prior scout documents for reader cross-reference.
- No script changes. No scripts were created, edited, or invoked.
- All internal markdown links are repository-relative and resolve to
  existing files in `docs/space-center/` (verified by file listing at write
  time): `figural-orca-wave-interference-match-research-scout-2026-05-22.md`,
  `figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md`,
  `abstract-cymatic-physics-model-comparison-2026-05-22.md`,
  `figural-fluid-dynamics-reveal-scout-2026-05-22.md`,
  `arc-bounded-region-rendering-notes-2026-05-21.md`,
  `primitive-composition-renderer-pivot-plan-2026-05-21.md`,
  `austin-authorization-expansion-2026-05-22.md`,
  `austin-consent-map.md`. The JSON link in Section 6.3
  (`track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001.json`)
  is reproduced from the v001 scout document and resolves on the same
  branch.
- Scoped to one new markdown file at
  `docs/space-center/substrate-first-figural-reveal-research-2026-05-22.md`.

Recorded by: operator session, 2026-05-22.
