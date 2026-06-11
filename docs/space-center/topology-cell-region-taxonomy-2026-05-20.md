# Topology Cell Region Taxonomy - 2026-05-20

Status: internal Agent E handoff for Agent B v005 topology/cymatics lane. No rendering, no MP4s. This is mathematical extraction guidance and Austin-source morphology reference only; it is not a public cultural-grammar claim.

Read with:

- `docs/space-center/seed-flower-overlap-cell-extraction-spec-2026-05-20.md`
- `docs/space-center/topology-cell-reveal-renderer-spec-2026-05-20.md`
- `track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg`
- `track2-deterministic/source-vectors/Animal_Bird_Raven_Sun.svg`
- `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`
- `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/06-austin-vancity-slides-crescent-circle-trigon.png`

## 1. Reference Separation

Austin art pieces are the morphology target. Use them to judge sun/orb/ray attachment, ray curvature, and how pointed trigons sit against a center circle.

The meeting screenshot is only a grammar/sequence teaching reference: crescent -> circle -> trigon, directionality, and simple slide-language. Do not treat its white primitives as Austin's actual sun morphology.

## 2. Austin Sun Morphology Observations

- Center circle/orb is dominant. `Nature_Cosmic_Sun` has a yellow orb with a red outline; `Animal_Bird_Raven_Sun` has a large yellow orb partly covered by the raven.
- Rays/trigons are directly attached around the center circle. They touch, tuck under, or share the circle perimeter; they are not detached marks floating outside the orb.
- Rays point outward from the center and are curved/elegant. Their sides are Bezier-like arcs tapering to pointed outer tips, not crude straight triangles.
- Austin-style sun trigons are solar rays with radial intent. Generic sacred-geometry petals/vesicas are lens-like overlaps; they do not automatically read as Austin sun rays.
- The raven source shows that rays can be partially occluded by foreground figure geometry. Attachment to the orb still remains the sun rule.

## 3. Coordinate Convention

Use equal radius `R`, construction center `O = (0,0)`, center circle `C0 = O`, and adjacent ring centers:

```text
C1 = (R, 0)
C2 = (R/2, sqrt(3)R/2)
u12 = normalize(C1 + C2)  # outward bisector from O between C1 and C2
inside(Ci) = distance(p, Ci) <= R
```

For the other five sectors, rotate the same definitions by 60 degrees.

## 4. Region Taxonomy

### `inner_3circle_intersection`

- Description: local common overlap of `C0`, `C1`, and `C2`; a central Reuleaux-like triangular overlap inside the seed/flower scaffold.
- Boundary arcs: one arc each from `C0`, `C1`, and `C2`.
- Curvature direction: inward/cupped relative to construction center `O`; this is the inward overlap, not the outward ray.
- OpenCV/raster mask: `mask = inside(C0) & inside(C1) & inside(C2)`; choose the component nearest the local triple-intersection centroid, reject crop/tiny slivers.
- Render status: reject for v005 sun trigons; debug-only for proving the classifier can name it.

### `outer_3circle_scallop`

- Description: outward curved triangular/scallop cell attached to the outside of `C0` between adjacent ring circles; this is Darren's seed/flower-derived trigon target.
- Boundary arcs: base/cut arc from `C0`, side arcs from `C1` and `C2`; the side arcs meet toward the outward bisector `u12`.
- Curvature direction: outward relative to `O`; the cell points away from center and can be shaped toward Austin-style attached rays.
- OpenCV/raster mask: `mask = inside(C1) & inside(C2) & ~inside(C0)`; choose the connected component whose centroid has positive dot with `u12`; in full fields, keep source labels containing adjacent ring IDs and excluding `C0`.
- Render status: visible-final for seed/flower-derived trigons and `sun_from_seed` rays.

### `center_to_center_triangle`

- Description: straight construction triangle connecting `O`, `C1`, and `C2`; useful for showing which three centers produced a sector.
- Boundary arcs: none; edges are straight debug segments `O-C1`, `C1-C2`, `C2-O`.
- Curvature direction: none; it is not an extracted topology cell.
- OpenCV/raster mask: no cell mask; optional `cv2.polylines` overlay only, never `fillPoly` as output.
- Render status: debug-only; reject as final visible primitive.

### `vesica_lens`

- Description: two-circle overlap lens, e.g. `C0` with `C1`; symmetric almond/petal region.
- Boundary arcs: one arc from each of the two parent circles.
- Curvature direction: two-sided; each edge curves toward its opposite source. Relative to `O`, it may read inward or outward depending pair and side.
- OpenCV/raster mask: `mask = inside(A) & inside(B)`; for arrangement cells, optionally subtract other source masks or split connected components by label.
- Render status: visible-final only when deliberately selected for lens/crescent mode; not a sun trigon by default.

### `outer_2circle_crescent`

- Description: crescent/lune outside one circle and bounded by another circle's arc, e.g. the part of `C1` outside `C0`.
- Boundary arcs: dominant outer arc from included circle `C1`, cut/cupping arc from excluded circle `C0`; may need a field clip to close the component.
- Curvature direction: cups around the excluded circle; for center-excluded sectors it generally opens/points outward from `O`.
- OpenCV/raster mask: `mask = inside(C1) & ~inside(C0)` clipped to local wedge/field bounds; choose the connected component by centroid and source IDs.
- Render status: visible-final for crescent-field studies; do not substitute it for `outer_3circle_scallop` in sun mode.

### `recursive_crescent_edge`

- Description: a lens/crescent whose own edge treatment is made from smaller crescent-like arcs; a parent crescent with nested crescent scalloping.
- Boundary arcs: parent arcs from the selected lens/lune plus secondary child arcs generated along one or both parent edges.
- Curvature direction: inherited from parent crescent, with smaller arcs alternating along the edge; direction must be explicit per child arc.
- OpenCV/raster mask: first isolate `vesica_lens` or `outer_2circle_crescent`, then apply a second pass of small arc masks along sampled boundary normals; keep as separate child-region metadata.
- Render status: future/high-value idea; reject from v005 final output unless explicitly requested as an experiment.

## 5. B v005 Instruction Seed

B must not:

- place random crescents;
- use `inner_3circle_intersection` when `outer_3circle_scallop` is requested;
- leave construction circles as the final read;
- make Austin sun rays detached from the center circle;
- omit a debug overlay showing which region type each visible shape came from.
