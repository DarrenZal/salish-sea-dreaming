# Interference Field Cell Taxonomy - 2026-05-20

Status: internal Agent E companion spec for Agent B wave-field extraction. No
rendering was performed for this document. This is mathematical extraction
guidance only; it is not Austin-approved, not public-use guidance, not a
traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- [cymatic-standing-wave-algorithm-brief-2026-05-20.md](cymatic-standing-wave-algorithm-brief-2026-05-20.md)
- [topology-cell-region-taxonomy-2026-05-20.md](topology-cell-region-taxonomy-2026-05-20.md)
- [topology-cell-reveal-renderer-spec-2026-05-20.md](topology-cell-reveal-renderer-spec-2026-05-20.md)
- [primitive-grammar-visual-acceptance-criteria-2026-05-20.md](primitive-grammar-visual-acceptance-criteria-2026-05-20.md)

## 1. Purpose

The seed/flower taxonomy handles exact circle CSG cells. This document handles
continuous standing-wave fields where the generator is a scalar field rather
than an explicit set of overlapping construction circles.

Agent B should classify cells from the stable spatial field:

```text
F(x, y) = normalized standing-wave scalar field
```

Then animate display state separately:

```text
Z(x, y, t) = F(x, y) * phase_display(t)
```

Do not classify from the time-multiplied `Z` at every frame. Quarter-phase
values can collapse the field into a full-screen nodal band and destroy the
topology.

## 2. Field Convention

Normalize the field before extraction:

```text
F_norm = smooth(normalize(F, -1, 1))
tau = percentile(abs(F_norm), 68..80)
node_epsilon = 0.015..0.050
```

Extract three primary masks:

```text
positive_mask = F_norm > tau
negative_mask = F_norm < -tau
nodal_band = abs(F_norm) <= node_epsilon
```

Recommended contour sets:

```text
positive_cells = connected components of positive_mask
negative_cells = connected components of negative_mask
nodal_boundaries = contours at F_norm = 0 plus cleaned nodal_band skeletons
source_level_rings = selected level contours around each source/emitter
```

Keep field topology stable for one render window. Phase inversion should swap
which polarity fills and which polarity outlines; it should not recompute cell
membership unless the emitter layout or mode family changes.

## 3. Source Attribution

Continuous interference cells still need parent-source evidence. For each
boundary sample point, assign a dominant contributor:

```text
contribution_i(p) =
  A_i * cos(k_i * distance(p, source_i) + phi_i) * exp(-distance/lambda_i)

source_id(p) = argmax_i abs(contribution_i(p))
```

For Bessel or Chladni fields without point emitters, use mode attribution
instead:

```text
source_id(p) = dominant mode term or radial/angular basis term at p
```

Collapse neighboring sample labels into arc runs:

```json
{
  "arc_runs": [
    {"source_id": "emitter_01", "arc_fraction": 0.42},
    {"source_id": "emitter_03", "arc_fraction": 0.36},
    {"source_id": "emitter_04", "arc_fraction": 0.22}
  ],
  "arc_run_count": 3
}
```

Reject cells whose source attribution is too fragmented unless the purpose is a
debug-only network/nodal study.

## 4. Cell Record Contract

Every extracted candidate should be written before final drawing:

```json
{
  "cell_id": "interference_v002_pos_014",
  "field_family": "multi_emitter_standing_wave",
  "taxonomy_type": "positive_phase_cell",
  "topology_class": "crescent",
  "role": "interference_lens",
  "polarity": "positive",
  "threshold": 0.42,
  "source_ids": ["emitter_01", "emitter_03"],
  "arc_run_count": 2,
  "arc_runs": [
    {"source_id": "emitter_01", "arc_fraction": 0.51},
    {"source_id": "emitter_03", "arc_fraction": 0.49}
  ],
  "nodal_boundary_ids": ["node_007", "node_012"],
  "contour_points_px": [[820, 412], [826, 420]],
  "centroid_px": [846.2, 438.9],
  "orientation_rad": 0.82,
  "area_px": 1820.0,
  "perimeter_px": 168.0,
  "curvature_lobe_count": 2,
  "radial_source_id": "emitter_01",
  "radial_ring_index": 2,
  "confidence": 0.78,
  "render_policy": "candidate",
  "cultural_status": "internal_austin_review_needed"
}
```

Required values for `taxonomy_type`:

```text
positive_phase_cell
negative_phase_cell
nodal_boundary
radial_source_ring
interference_lens_crescent
multi_source_trigon_scallop
six_ray_snowflake_sun_candidate
ambiguous_rejected
```

Renderer-facing `topology_class` remains the simpler visual class:

```text
circle
crescent
trigon
outline
compound
ambiguous
```

## 5. Taxonomy Classes

### `positive_phase_cell`

Description: a connected antinode region where `F_norm > tau`.

Classification evidence:

- `polarity == positive`;
- region is a connected component of `positive_mask`;
- mean field value inside the component is positive;
- component is bounded by nodal lines, opposite-polarity cells, field mask, or
  low-amplitude falloff;
- area and contour smoothness pass pruning thresholds.

Primitive mapping:

- one compact island can map to `circle` or `compound`;
- elongated two-source island can map to `crescent`;
- three-lobed or three-source island can map to `trigon`;
- otherwise keep as `compound` or `ambiguous`.

Render policy:

- visible only when its topology class, role, and source relation are legible;
- during phase inversion, positive cells can fill in phase A and outline in
  phase B.

Reject if:

- it is speckle, crop-edge debris, or a dense texture fragment;
- it creates paired eye-like circles;
- it has no source, node, ring, or path relation.

### `negative_phase_cell`

Description: a connected antinode region where `F_norm < -tau`.

Classification evidence:

- `polarity == negative`;
- region is a connected component of `negative_mask`;
- mean field value inside the component is negative;
- boundary and source attribution are measured exactly like positive cells.

Primitive mapping:

- same topology rules as positive cells;
- negative cells are often useful as voids, inverse fills, or outline accents.

Render policy:

- during phase inversion, negative cells can outline in phase A and fill in
  phase B;
- do not treat negative polarity as culturally or symbolically meaningful.

Reject if:

- it is used only for contrast with no topology role;
- inversion makes the output flash into wallpaper;
- negative/positive alternation destroys the phrase read.

### `nodal_boundary`

Description: a stable contour or narrow band where `F_norm = 0`. Nodal
boundaries separate positive and negative phase cells and can act as membrane
outlines, not filled primitives.

Classification evidence:

- contour extracted at level `0.0`, or skeleton/centerline of `nodal_band`;
- adjacent samples on opposite sides have opposite signs;
- contour length, branch degree, and stability pass pruning thresholds;
- endpoints are either closed, branch nodes, mask edges, or documented open
  boundaries.

Primitive mapping:

- renderer class `outline`;
- role examples: `membrane_boundary`, `water_node_line`, `cell_separator`,
  `network_connector`, `debug_source_contour`.

Render policy:

- may remain visible across both phase states;
- should be low density and stable;
- should not compete with selected primitive cells.

Reject if:

- the nodal set reads as a rectangular grid, full-screen noise, or generic
  Chladni wallpaper;
- branch labels are missing;
- the outline is filled as if it were a primitive cell.

### `radial_source_ring`

Description: a near-circular level contour or antinode band around one emitter
or radial mode center. This is a source-local ring, not automatically an
Austin-like sun or public motif.

Classification evidence:

- one dominant source or radial basis term;
- center is within tolerance of `source.position` or declared membrane center;
- ring radius is stable and assigned `radial_ring_index`;
- circularity or fitted-ellipse residual is within tolerance;
- neighboring rings are ordered by radius.

Primitive mapping:

- compact central source can map to `circle`;
- partial ring segments can become `crescent` only if clipped or interrupted by
  another source, nodal boundary, or mask;
- complete rings remain `outline` or `compound`, not automatic sun rays.

Render policy:

- use as source/debug evidence or quiet ripple structure;
- visible final rings need a declared water/ripple/source role;
- rings can seed `six_ray_snowflake_sun_candidate` extraction when crossed by
  sixfold radial lobes.

Reject if:

- rings are decorative target graphics;
- ring stacks fill the frame;
- a ring is treated as a face/orb/sun claim without Austin review.

### `interference_lens_crescent`

Description: a two-source cell or two-source-bounded region that reads as a
lens, lune, or crescent because two wavefront families cup against each other.

Classification evidence:

- `arc_run_count == 2` after removing tiny fragments;
- exactly two dominant source IDs, or one source plus one nodal/mask boundary;
- medial axis is curved or almond-like;
- one side cups around a source, ring, or neighboring phase cell;
- source arc balance is sufficient for a lens, or one arc dominance is labeled
  as a lune/crescent.

Primitive mapping:

- renderer class `crescent`;
- role examples: `interference_lens`, `wave_lune`, `source_cupping_crescent`,
  `phase_boundary_crescent`.

Render policy:

- visible candidate for water-flow or cymatic crescent studies;
- must use extracted contour, not a stamped crescent icon;
- optional debug arcs should show the two parent sources.

Reject if:

- it is merely a crescent-shaped isolated island with no two-source evidence;
- the cup direction is wrong or unlabeled;
- it becomes random crescent scatter.

### `multi_source_trigon_scallop`

Description: a curved triangular, scallop, or three-lobed cell near
multi-source interference. This is the continuous-field analogue of the
seed/flower `outer_3circle_scallop`, but its evidence comes from wave-source
arcs and local phase topology rather than exact circle CSG.

Classification evidence:

- `arc_run_count == 3`, or three dominant curvature lobes with stable
  three-source attribution;
- three neighboring sources, rings, or nodal segments bound the cell;
- contour sides are curved, not straight triangle edges;
- orientation vector is derived from centroid-to-source geometry, gradient
  direction, or local release direction;
- cell is not the inward debug-only gap unless explicitly labeled as such.

Primitive mapping:

- renderer class `trigon`;
- role examples: `three_source_gap`, `curved_trigon`, `scallop_release_cell`,
  `radial_ray_candidate`.

Render policy:

- visible only when three-arc evidence is shown in debug overlay;
- final render should preserve the extracted curved contour;
- use as sun/ray candidate only if attached to a center/ring/orb structure and
  not detached.

Reject if:

- contour simplification makes it a crude triangle or UI arrow;
- source evidence is actually two-source lens plus noise;
- it floats as a decorative trigon with no source/path/topology relation.

### `six_ray_snowflake_sun_candidate`

Description: a sixfold radial selection of lobes, scallops, or source rings
that may read as snowflake, sun/ripple, or radial water geometry depending on
context. This is a candidate grouping, not an automatic final symbol.

Classification evidence:

- radial center is declared and stable;
- six angular sectors are detected within tolerance, usually near 60 degrees
  apart;
- each arm contains a selected `multi_source_trigon_scallop`, crescent/lens,
  ring segment, or nodal ray;
- angular balance, radial distance, and confidence are recorded per arm;
- center circle/ring status is explicit: `none`, `debug_source`, `water_origin`,
  `sun_orb_candidate`, or `snow_core_candidate`.

Primitive mapping:

- renderer class `compound`;
- child cells retain their own classes: `circle`, `crescent`, `trigon`, or
  `outline`;
- role examples: `snowflake_candidate`, `sun_ripple_candidate`,
  `sixfold_membrane_mode`, `radial_water_release`.

Render policy:

- internal candidate only;
- must be reviewed as radial topology or water/snow geometry, not generic
  sacred geometry;
- sun-like candidates require Austin review before public use and must keep
  rays attached to the center/ring if shown as sun/ray behavior.

Reject if:

- all six arms are equally bright and read as decorative mandala wallpaper;
- there is no center, no ring, and no source relation;
- the candidate uses detached rays or generic petals;
- it is presented as Austin-approved sun grammar.

### `ambiguous_rejected`

Description: any field component that fails confidence, source attribution,
area, topology, curvature, cultural-boundary, or density tests.

Classification evidence:

- record the reason for rejection;
- keep contour and minimal metrics for debug only;
- do not render as final visible primitive.

Common reasons:

```text
too_small
touches_crop_boundary
source_attribution_fragmented
no_clear_polarity
node_speckle
generic_triangle
decorative_crescent
eye_pair_risk
wallpaper_density
public_boundary_risk
```

## 6. Classification Order For Agent B

Agent B should classify by field evidence before visual resemblance:

1. Build and smooth stable `F_norm`.
2. Extract positive, negative, nodal, and source-ring candidate sets.
3. Compute features: area, perimeter, centroid, circularity, arc runs,
   curvature lobe count, branch degree, source IDs, polarity, and ring index.
4. Assign `taxonomy_type`.
5. Assign renderer-facing `topology_class`.
6. Score confidence and rejection reasons.
7. Apply sparse selection and density caps.
8. Write the cell records and debug overlays before any beauty render.

Suggested confidence score:

```text
confidence =
    topology_evidence
  + source_arc_coherence
  + polarity_stability
  + contour_smoothness
  + role_fit
  - density_penalty
  - crop_penalty
  - generic_symbol_penalty
  - eye_pair_penalty
```

Hard caps for first wave-field pass:

- 3 to 7 active point emitters, or 1 radial center plus 1 to 3 mode terms.
- 8 to 24 selected filled cells.
- 1 to 4 selected nodal-boundary groups.
- 0 to 2 six-ray candidates per scene.
- No all-frame lattice, full flower, or dense Chladni wallpaper as final read.

## Visual Differentiation By Boundary Language

Beauty renders should not use debug color coding. Debug colors prove classifier
state; final visuals should distinguish cells through boundary behavior,
line/fill weight, opacity, scale, and temporal persistence.

- `circle_like` rendering: use solid or closed treatment, with a stable origin
  read. Circles may pulse, but should not become paired eye-like dots or loose
  particles.
- `crescent_like` rendering: emphasize the two-arc/lens relationship. Let the
  outer arc carry more weight and the inner/cupping arc stay lighter, thinner,
  or more transparent so the cup direction remains readable.
- `trigon_like` rendering: emphasize three-corner, scallop, or ray behavior.
  Preserve curved sides and a shaped rear/base; reject straight triangle or UI
  arrow reads. Treat trigon-like wave cusps as renderer hypotheses, not
  cultural construction claims.
- `compound` rendering: suppress by default. If needed for field context, keep
  as faint ghost outlines, low-alpha membranes, or delayed background traces.
- Temporal persistence is a legibility requirement: selected cells should hold
  long enough for polarity, boundary type, and role to be read before phase
  inversion or dissolve.
- Density caps are visual grammar, not only performance limits. Keep enough
  empty field around selected cells that circles, crescents, trigons, and
  compounds remain distinguishable without debug labels.

## Canonical Primitive Geometry

Raw extracted field cells and beauty-render primitives are not the same object.
The extractor must preserve field provenance; the renderer may canonicalize
selected cells only after that provenance is recorded.

Raw cells between sources may be vesica/lens-like: two source wavefronts create
a symmetric almond, lune, or irregular two-arc cell. Do not call every raw
vesica/lens cell a moon-style crescent in debug records.

Beauty renders may canonicalize `crescent_like` cells into moon-style crescents
when review legibility is more important than showing the exact raw contour.
That canonicalization must be explicit and reversible in metadata.

Concrete moon crescent geometry:

```text
axis = normalize(cusp_2 - cusp_1)
cusp_1, cusp_2 = the two endpoint/cusp points defining the crescent axis
outer_arc = circle arc with radius R1
inner_arc = circle arc with radius R2 where R2 < R1
inner_center = outer_center + axis * offset
```

`offset` is measured along the principal axis. The inner arc cuts into the
outer disk to create the cup; cup direction is derived from the sign of
`offset` and must be recorded.

Debug frames must preserve raw extracted contours, source arc colors, centroid,
and bounds so field provenance remains visible even when the beauty render uses
a cleaner canonical primitive.

Rendered primitive records must map back to:

```text
source_cell_id, raw_centroid_px, raw_bounds_px, orientation_rad,
canonical_type, R1, R2, offset, cusp_1_px, cusp_2_px, cup_direction
```

## Negative-Space Field Rendering Mode

Negative-space rendering is a first-class mode for v004. The renderer should
make field-shaped primitives from positive cells, negative cutouts, wavefront
arcs, and cusp regions rather than forcing every accepted cell into a clean
symbol.

Mode components:

- `positive_cells`: filled or softly luminous antinode bodies. These are the
  visible membrane/pressure shapes, not stamped icons.
- `negative_cutouts`: opposite-polarity cells used as carved voids, holes,
  inner bites, or inverse phase reveals inside/against positive bodies.
- `wavefront_arcs`: nodal or source-ring contours drawn as partial boundary
  language. They may define outer/inner edges without closing into full cells.
- `cusp_regions`: high-curvature meetings of wavefront arcs where pressure
  regions pinch, split, or release. These may suggest trigon-like scallops or
  rays, but only as a renderer hypothesis.

Rendering rules:

- Debug overlays must keep raw positive/negative/nodal contours visible before
  any cutout or cusp stylization.
- Beauty renders may subtract `negative_cutouts` from `positive_cells`, but the
  record must preserve both source cell IDs and the boolean operation.
- `wavefront_arcs` should remain field arcs, not decorative outlines.
- `cusp_regions` may be rendered as curved trigon-like releases only when the
  source wavefronts, centroid, bounds, and orientation are recorded.
- Do not describe trigon-like wave cusps as a cultural construction claim or an
  approved primitive grammar. They are internal renderer hypotheses derived
  from scalar-field behavior.

## 7. Debug Overlay Requirements

Agent B must export debug overlays before any review candidate can be accepted.
These can be stills only. No rendering is requested by this document.

Required overlays:

1. `field_heatmap_debug`: scalar `F_norm` with positive/negative color ramp and
   zero level visible.
2. `polarity_masks_debug`: `positive_mask`, `negative_mask`, and `nodal_band`
   in separate colors.
3. `nodal_boundaries_debug`: `F = 0` contours, branch points, contour IDs, and
   pruned/kept status.
4. `source_attribution_debug`: emitter positions or modal centers, source IDs,
   radial rings, and boundary arc colors by dominant source.
5. `cell_classification_debug`: every candidate colored by `taxonomy_type` with
   labels for `cell_id`, `polarity`, `topology_class`, and confidence.
6. `rejected_cells_debug`: rejected components drawn at low alpha with reason
   codes.
7. `selected_cells_debug`: only selected final candidates with source arcs,
   orientation vectors, ring index where applicable, and render policy.
8. `six_ray_group_debug`: for each six-ray candidate, center point, six sector
   spokes, arm IDs, angular error, and child cell IDs.

Minimum contact sheet layout:

```text
01 field heatmap
02 polarity masks
03 nodal boundaries
04 source attribution
05 all candidate classifications
06 rejected cells with reasons
07 selected cells only
08 final preview, if a later renderer pass creates one
```

Do not submit a final-looking image without the first seven debug panels.

## 8. Agent B Output Contract

When rendering resumes, the first deliverable should be recipes and debug stills
before final MP4s:

```text
cell_records.json
classification_summary.csv
debug_overlays/
  01_field_heatmap_debug.png
  02_polarity_masks_debug.png
  03_nodal_boundaries_debug.png
  04_source_attribution_debug.png
  05_cell_classification_debug.png
  06_rejected_cells_debug.png
  07_selected_cells_debug.png
  08_six_ray_group_debug.png
contact_sheet_debug.png
README.md
```

`classification_summary.csv` should include:

```text
cell_id,taxonomy_type,topology_class,polarity,source_ids,arc_run_count,
area_px,confidence,render_policy,rejection_reason,cultural_status
```

The README must state:

- field family and parameter seed;
- thresholds and smoothing used;
- counts by taxonomy type;
- rejection counts by reason;
- selected-cell count;
- debug overlay paths;
- cultural status and Austin boundary;
- whether any six-ray candidate is snowflake, sun/ripple, or only generic
  radial topology for internal review.

## 9. Austin Boundary

All wave-field outputs are internal and Austin-review-needed. Positive/negative
phase, nodal boundaries, radial source rings, lenses, crescents, trigons, and
six-ray groupings do not carry approved cultural meaning by default.

Do not:

- call a six-ray grouping an Austin sun unless Austin reviews that output;
- turn snowflake/sun candidates into generic sacred geometry claims;
- detach rays from a center/orb/ring in sun-like candidates;
- use exact Austin source colors, faces, figures, Thunderbird, serpent, wolf,
  or named/supernatural subjects;
- present any output as public-ready.

Use review language such as `radial topology candidate`, `standing-wave cell`,
`interference lens`, `curved trigon candidate`, or `sixfold water/snow
candidate` until Austin gives more specific guidance.

## 10. B v002 Instruction Seed

Agent B must not:

- classify from animated `Z(x, y, t)` instead of stable `F(x, y)`;
- render positive/negative phase cells without polarity labels;
- fill nodal boundaries as primitive cells;
- call every two-source shape a crescent without source-arc evidence;
- call every three-lobed island a trigon without curved three-source evidence;
- promote sixfold symmetry into generic sacred geometry;
- omit rejected-cell debug evidence;
- omit source attribution and ring/index overlays;
- submit final MP4s before debug stills and cell records exist.
