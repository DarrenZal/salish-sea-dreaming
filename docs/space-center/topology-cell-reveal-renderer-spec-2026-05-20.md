# Topology Cell Reveal Renderer Spec - 2026-05-20

Status: internal Agent E renderer implementation spec for Agent B's v004 direction. No rendering performed by this document. This is mathematical/physics-inspired topology guidance only, not Austin-approved grammar, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- `docs/space-center/seed-flower-overlap-cell-extraction-spec-2026-05-20.md`
- `docs/space-center/topology-cell-region-taxonomy-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `scripts/primitive_water_grammar_v4.py`
- `scripts/primitive_water_grammar_v5.py`

## 1. Renderer Goal

Darren's v004 direction is: keep the seed/flower overlap geometry as a hidden scaffold, then reveal primitive classes that are extracted from overlap cells.

The renderer should not draw icons over a sacred/seed/flower diagram. It should:

```text
construction circles
  -> overlap cell extraction
  -> topology classification
  -> class-specific reveal
  -> scaffold fades down or disappears
```

Visible outputs:

- center circle / origin;
- curved trigon / radial ray cells;
- crescent / lens / lune cells;
- optional compound/network cells as faint connective structure;
- falling snowflake layer made from many small primitive-cell snowflakes.

Construction circles are allowed as low-opacity debug or early scaffold only. They should not be the final read.

## 2. Data Model

### ConstructionCircle

```json
{
  "source_id": "circle_000",
  "ring": 0,
  "center_world": [0.0, 0.0],
  "center_px": [960.0, 540.0],
  "radius_world": 1.0,
  "radius_px": 180.0,
  "debug_visible": true,
  "base_opacity": 0.06,
  "visibility_phase": "scaffold",
  "cultural_status": "internal_austin_review_needed"
}
```

Rules:

- `base_opacity` should usually be `0.00` after the scaffold phase.
- Construction circles are not primitive marks unless converted into a specific `OverlapCell` with role `center_origin`.
- Keep stable `source_id`s so cell source attribution can survive ring growth.

### OverlapCell

```json
{
  "cell_id": "seed_r1_cell_014",
  "topology_class": "trigon",
  "role": "radial_ray_cell",
  "region_type": "outer_3circle_scallop",
  "source_ids": ["circle_000", "circle_003", "circle_004"],
  "arc_runs": [
    {"source_id": "circle_000", "arc_fraction": 0.34},
    {"source_id": "circle_003", "arc_fraction": 0.31},
    {"source_id": "circle_004", "arc_fraction": 0.35}
  ],
  "arc_run_count": 3,
  "contour_points_px": [[958, 370], [978, 386], [984, 414]],
  "centroid_px": [966.2, 398.7],
  "centroid_norm": [0.503, 0.369],
  "orientation_rad": -1.48,
  "radial_distance_px": 141.8,
  "radial_angle_rad": -1.52,
  "area_px": 2140.0,
  "perimeter_px": 184.0,
  "confidence": 0.86,
  "phase_offset": 0.12,
  "visibility_phase": "reveal",
  "render_policy": "visible",
  "construction_visible": false,
  "cultural_status": "internal_austin_review_needed"
}
```

Allowed `topology_class` values:

```text
circle
crescent
trigon
compound
ambiguous
```

Use `trigon` in renderer-facing records even when the extractor uses `curved_trigon`; store `role: "curved_trigon"` or `role: "radial_ray_cell"` for the curved subtype.

Renderer-facing roles:

```text
center_origin
lens_overlap
lune_crescent
radial_ray_cell
three_arc_gap
snowflake_arm_cell
snowflake_core_cell
network_connector
debug_rejected
```

### Region Selection Table

Renderer modes must select explicit region types before assigning the broader `topology_class`. Do not infer visible cells from proximity to construction circles.

| Region type | Renderer class/role | Extraction predicate | Curvature direction | Visibility policy |
|---|---|---|---|---|
| `inner_3circle_intersection` | `trigon` / `debug_rejected` | `inside(C0) & inside(C1) & inside(C2)` for a local adjacent triplet | inward/cupped toward construction center | reject for v005 sun trigons; debug overlay only |
| `outer_3circle_scallop` | `trigon` / `radial_ray_cell` or `three_arc_gap` | `inside(C1) & inside(C2) & ~inside(C0)`, adjacent ring pair, centroid on outward bisector | outward from construction center | primary visible trigon/ray target |
| `center_to_center_triangle` | debug guide only | straight `O-C1-C2` center graph, no filled cell mask | none | debug-only; never final primitive |
| `vesica_lens` | `crescent` / `lens_overlap` | `inside(A) & inside(B)` two-source overlap, split by label/components if needed | two-sided, source-pair dependent | visible only in deliberate lens/crescent mode |
| `outer_2circle_crescent` | `crescent` / `lune_crescent` | `inside(A) & ~inside(B)` clipped to local wedge/field bounds | cups around excluded circle; often outward for center-excluded sectors | visible for crescent-field studies, not sun trigons |
| `recursive_crescent_edge` | future child-edge metadata | isolate parent crescent/lens, then add smaller crescent-like edge arcs | inherited per child arc | future/high-value; reject from v005 final |

Every visible selected cell must include `region_type` using one of these names and a debug overlay label/color proving which region type produced it.

### Visibility Phases

Every cell and scaffold source should carry one of these phases:

| Phase | Purpose | Scaffold opacity | Cell behavior |
|---|---|---:|---|
| `scaffold` | briefly expose the generator for internal review | `0.04-0.08` | cells hidden or outline-only |
| `classify` | optional debug pass showing class colors/labels | `0.02-0.05` | low-alpha outlines by class |
| `reveal` | primary output | `0.00-0.02` | selected primitive cells fill/outline |
| `invert` | standing-wave style fill/line swap | `0.00` | filled cells become outlines and inverse set fills |
| `dissolve` | exit state | `0.00` | cells fade, shrink, or break into low-alpha traces |

Do not compute new topology during `invert` or `dissolve`. These phases only change opacity, line/fill state, and optionally scale/blur.

### TopologyRevealScene

```json
{
  "scene_id": "sun_from_seed_v004",
  "renderer_mode": "sun_from_seed",
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "duration_s": 8.0,
  "ring_count": 2,
  "spacing_ratio": 1.0,
  "construction_circles": [],
  "cells": [],
  "visibility_schedule": {
    "scaffold": [0.00, 0.18],
    "classify": [0.12, 0.28],
    "reveal": [0.24, 0.72],
    "invert": [0.58, 0.86],
    "dissolve": [0.82, 1.00]
  },
  "quality_caps": {
    "max_visible_cells": 36,
    "max_visible_circles": 1,
    "max_visible_compound": 4
  }
}
```

## 3. Renderer Mode: `sun_from_seed`

Purpose: reveal a central origin and radial trigon/ray cells derived from seed/flower overlap topology.

### Algorithm

1. Generate circle rings:
   - start with `ring_count = 1` for the seven-circle seed fixture;
   - use `ring_count = 2` only if the first ring is too sparse;
   - default `spacing_ratio = 1.0`;
   - use equal radius circles.
2. Extract overlap cells using the OpenCV label/contour path from `seed-flower-overlap-cell-extraction-spec-2026-05-20.md`.
3. Identify the central circle:
   - source circle with `ring == 0` is `circle_000`;
   - create one renderer cell with `topology_class: "circle"` and `role: "center_origin"`;
   - if the extractor produces several central fragments, keep the highest-confidence one nearest canvas center and reject the rest.
4. Identify adjacent three-arc/trigon cells:
   - `topology_class in ["trigon", "curved_trigon"]`;
   - `arc_run_count == 3`;
   - `source_ids` includes `circle_000` or the cell centroid lies within `1.6R` of origin;
   - radial angle is stable and points outward from center.
5. Rank radial trigons:
   - prefer six or twelve angularly balanced cells;
   - prefer cells with high confidence and similar area;
   - reject tiny slivers and cells touching the crop boundary.
6. Fade scaffold and reveal radial trigons:
   - scaffold visible only in first `10-20%` of loop;
   - center origin pulses first;
   - radial trigons reveal from center outward;
   - crescents may appear as very faint support only if needed.

### Visibility Policy

```text
construction circles: scaffold only, alpha <= 0.08 then 0
center_origin: visible, slow pulse, max 1
radial trigon cells: primary visible cells
crescent/lens cells: low alpha or hidden
compound cells: hidden
```

### Avoid

- full flower lattice as final image;
- generic sunburst triangles;
- radial mandala symmetry with all cells equally bright;
- a face-like center with paired circles.

## 4. Renderer Mode: `trigon_field_reveal`

Purpose: isolate trigon-like cells from a larger overlap arrangement and reveal them as a topology field rather than as drawn triangles.

### Algorithm

1. Generate `ring_count = 2` overlap field.
2. Extract all cells and classify source runs.
3. Keep only trigon-like candidates:

```text
topology_class == "trigon" or topology_class == "curved_trigon"
arc_run_count == 3
confidence >= 0.70
area_px between min_area and max_area
```

4. Suppress circles and lenses:
   - `circle` cells hidden except optional single origin;
   - `crescent` cells hidden or used as alpha mask support below `0.10`;
   - `compound` cells hidden unless used as faint network outlines.
5. Spatially thin the field:
   - sort by confidence and radial/angle balance;
   - keep no two cells whose centroids are closer than `0.35R`;
   - cap visible cells at `18-28`.
6. Reveal:
   - start with a few center-adjacent trigons;
   - ripple outward by radial distance;
   - alternate fill and outline during `invert`;
   - dissolve outer cells first.

### Trigon Rendering Requirements

The rendered cell must use its extracted contour. Do not replace it with `TRIGON_BASE` unless a fallback/debug mode is explicitly requested.

Good trigon signals:

- three parent arcs visible in contour curvature;
- one outward orientation derived from centroid-to-origin vector or longest medial direction;
- non-identical cell sizes;
- large quiet gaps between groups.

## 5. Renderer Mode: `crescent_lens_field`

Purpose: isolate pairwise overlap lenses/lunes and make their two-arc crescent nature visually explicit.

### Algorithm

1. Generate `ring_count = 1` or `2`.
2. Extract cells and classify source runs.
3. Keep lens/lune candidates:

```text
topology_class == "crescent"
arc_run_count == 2
distinct source_ids == 2
confidence >= 0.68
```

4. Separate lens vs lune roles:
   - `lens_overlap`: compact shared overlap, usually balanced arc fractions;
   - `lune_crescent`: one arc dominates or the shape cups around a neighboring source;
   - both remain renderer class `crescent`.
5. Make two-arc nature explicit:
   - draw extracted filled cell at moderate alpha;
   - optionally draw two subtle boundary arc highlights, one per parent source;
   - orient a very faint normal/tangent shimmer along the cup direction;
   - never stamp a crescent icon over the cell.
6. Suppress other classes:
   - center origin may appear only as a low-alpha anchor;
   - trigon cells hidden or delayed until a later mixed-mode pass;
   - compound cells hidden.

### Visibility Policy

```text
construction circles: alpha <= 0.06 in scaffold, then 0
lens/lune cells: primary visible cells
two parent boundary arcs: low-alpha line accents, optional
circle/trigon/compound cells: hidden by default
```

### Avoid

- decorative moon-stamp crescents disconnected from source arcs;
- all pairwise lenses at equal brightness;
- a tiled flower diagram where the lenses are merely colored in.

## 6. Renderer Mode: `falling_snowflake_layer`

Purpose: create a falling layer made from many small primitive-cell snowflakes. Each snowflake is itself a tiny seed/overlap extraction or a cached mini recipe, not a drawn icon.

### Snowflake Primitive Recipe

Each snowflake instance should carry:

```json
{
  "flake_id": "flake_027",
  "base_recipe_id": "seed_flake_r1_variant_03",
  "cells": ["local cell records or recipe reference"],
  "position_px": [812.0, -40.0],
  "depth": 0.62,
  "scale": 0.34,
  "rotation_rad": 1.8,
  "drift_phase": 3.1,
  "fall_speed_px_s": 42.0,
  "alpha": 0.28,
  "blur_px": 0.6,
  "class_mix": {
    "circle": 0.10,
    "crescent": 0.35,
    "trigon": 0.45,
    "compound": 0.10
  }
}
```

### Algorithm

1. Precompute `6-12` tiny seed/snow primitive recipes:
   - use `ring_count = 1`;
   - keep only `6-14` cells per flake;
   - prefer curved trigons and crescents;
   - keep center circle tiny or omit it.
2. Spawn many flake instances:
   - `count = 40-140` depending on output density;
   - random but deterministic seed;
   - depth in `[0, 1]` controls scale, alpha, blur, and fall speed.
3. Apply depth variation:

```text
scale = lerp(0.18, 0.72, depth)
alpha = lerp(0.08, 0.34, depth)
blur_px = lerp(1.8, 0.1, depth)
fall_speed = lerp(18, 72, depth)
```

4. Animate drift:

```text
x += sin(t * drift_speed + drift_phase) * drift_amp
y += fall_speed * t
rotation += spin_rate * t
```

5. Wrap or respawn flakes when they exit bottom.
6. Render each flake's local extracted cells transformed into screen space.

### Snowflake Quality Policy

- The layer can contain many flakes, but each flake must stay sparse.
- Avoid perfect mandala snowflakes. Rotate, scale, thin, and fade cells unevenly.
- Depth should make the field atmospheric, not busy.
- Do not use construction circles as visible snowflake bodies except at very low debug opacity.

## 7. Visual Quality Rules

### Avoid Generic Mandala

- Do not reveal every cell in a full radial lattice.
- Use uneven activation, radial wave timing, and class-specific selection.
- Keep quiet space between cell groups.
- Prefer six to twelve strong radial trigons over hundreds of equal marks.

### Avoid Crude Icons

- Render extracted contours from overlap cells.
- Do not replace derived cells with hand-authored circle/crescent/trigon icon bases except in a labeled fallback.
- Preserve curved source-arc boundaries so trigons feel grown from the scaffold.
- Use outlines/fills from the same contour to support phase inversion.

### Avoid Too Many Tiny Cells

- Reject cells below `min_area_px`.
- Use area percentile caps per mode.
- Merge or hide sliver cells near circle intersections.
- Cap visible cells per scene and per snowflake.

### Construction Opacity Low

- `scaffold` alpha: `0.04-0.08`.
- `classify` alpha: `0.02-0.05`.
- `reveal/invert/dissolve` alpha: `0.00-0.02`, usually `0.00`.
- If the construction scaffold reads more strongly than derived cells, the render fails.

### Cultural / Review Boundary

- Internal only.
- No public claim that seed/flower/cymatic topology is Austin-approved grammar.
- Avoid public use of "sacred geometry" as authorization language.
- No figure, face, eye-pair, fish, bird, crest, clan, named being, or exact Austin-source use in this renderer spec.
- Keep output as black-screen/additive topology layers until separately reviewed.

## 8. OpenCV Pseudocode

```python
def build_topology_scene(mode, width=1920, height=1080, ring_count=2, seed=42):
    circles = generate_hex_circle_sources(ring_count=ring_count, spacing_ratio=1.0)
    label, sdf_stack = rasterize_circle_bitset(circles, width, height)
    cells = extract_overlap_cells_opencv(label, sdf_stack, circles)
    cells = normalize_renderer_classes(cells)

    if mode == "sun_from_seed":
        selected = select_sun_from_seed(cells, circles)
    elif mode == "trigon_field_reveal":
        selected = select_trigon_field(cells)
    elif mode == "crescent_lens_field":
        selected = select_crescent_lenses(cells)
    elif mode == "falling_snowflake_layer":
        selected = build_falling_snowflake_instances(seed)
    else:
        raise ValueError(mode)

    return {
        "construction_circles": circles,
        "cells": selected,
        "visibility_schedule": default_schedule(mode),
        "quality_caps": quality_caps(mode),
    }


def select_sun_from_seed(cells, circles):
    origin = make_or_select_center_origin(cells, circles)
    trigons = [
        c for c in cells
        if c.topology_class in ("trigon", "curved_trigon")
        and c.arc_run_count == 3
        and c.confidence >= 0.70
        and (
            circle_000_in_sources(c)
            or c.radial_distance_px < 1.6 * median_source_radius_px(circles)
        )
    ]
    trigons = reject_tiny_crop_and_ambiguous(trigons)
    trigons = angular_balance(thin_by_distance(trigons), target_count=6, max_count=12)
    for c in trigons:
        c.topology_class = "trigon"
        c.role = "radial_ray_cell"
        c.visibility_phase = "reveal"
        c.phase_offset = radial_phase(c)
    return [origin] + trigons


def select_trigon_field(cells):
    trigons = [
        c for c in cells
        if c.topology_class in ("trigon", "curved_trigon")
        and c.arc_run_count == 3
        and c.confidence >= 0.70
        and area_in_percentile_band(c, low=20, high=92)
    ]
    trigons = reject_tiny_crop_and_ambiguous(trigons)
    trigons = thin_by_distance(trigons, min_dist_px=0.35 * median_source_radius_px(cells))
    trigons = rank_by_confidence_balance_and_spacing(trigons)[:28]
    for c in trigons:
        c.topology_class = "trigon"
        c.role = "three_arc_gap"
        c.visibility_phase = "reveal"
    return trigons


def select_crescent_lenses(cells):
    crescents = [
        c for c in cells
        if c.topology_class == "crescent"
        and c.arc_run_count == 2
        and len(set(c.source_ids)) == 2
        and c.confidence >= 0.68
    ]
    crescents = reject_tiny_crop_and_ambiguous(crescents)
    for c in crescents:
        balance = arc_fraction_balance(c.arc_runs)
        c.role = "lens_overlap" if balance > 0.72 else "lune_crescent"
        c.visibility_phase = "reveal"
        c.boundary_arc_highlights = make_parent_arc_highlights(c)
    return rank_by_area_confidence_and_spacing(crescents)[:32]


def build_falling_snowflake_instances(seed):
    rng = np.random.default_rng(seed)
    base_recipes = [
        make_seed_flake_recipe(i, ring_count=1, max_cells=rng.integers(6, 15))
        for i in range(12)
    ]
    flakes = []
    for idx in range(90):
        depth = float(rng.uniform(0.0, 1.0))
        recipe = base_recipes[idx % len(base_recipes)]
        flakes.append({
            "flake_id": f"flake_{idx:03d}",
            "base_recipe_id": recipe["recipe_id"],
            "cells": recipe["cells"],
            "position_px": [float(rng.uniform(0, W)), float(rng.uniform(-H, H))],
            "depth": depth,
            "scale": lerp(0.18, 0.72, depth),
            "rotation_rad": float(rng.uniform(0, 2 * math.pi)),
            "drift_phase": float(rng.uniform(0, 2 * math.pi)),
            "fall_speed_px_s": lerp(18, 72, depth),
            "alpha": lerp(0.08, 0.34, depth),
            "blur_px": lerp(1.8, 0.1, depth),
        })
    return flakes


def render_frame(scene, t_norm):
    # No implementation in this spec. Agent B's renderer should:
    # 1. compute phase opacities from scene.visibility_schedule;
    # 2. draw construction circles only in scaffold/classify phases;
    # 3. draw extracted cell contours, not stamped primitive icons;
    # 4. use fill/outline inversion from stable cell records;
    # 5. apply dissolve without recomputing topology.
    pass
```

OpenCV drawing primitives for implementation:

```text
cv2.fillPoly(frame, [contour], rgb)
cv2.polylines(frame, [contour], isClosed=True, color=rgb, thickness=1)
cv2.GaussianBlur(local_layer, ksize, sigma) for depth blur
cv2.addWeighted or custom alpha composite for black-screen additive layers
```

## 9. Future Exact-Geometry Path

The v004 renderer can start from raster OpenCV contours. The future path should move the source data to exact circular arcs while keeping the same renderer data model.

Future exact steps:

1. Build a circular-arc arrangement from construction circles.
2. Store each cell as ordered `ArcHalfEdge` records rather than pixel contours.
3. Classify from exact parent arc count:
   - one arc/run -> `circle`;
   - two arc/runs -> `crescent`;
   - three arc/runs -> `trigon`;
   - four-plus -> `compound`.
4. Convert arcs to renderable splines only at the last step.
5. Keep exact source metadata for boundary arc highlights in `crescent_lens_field`.
6. Let TouchDesigner/WebGL ingest JSON recipes and handle phase, opacity, depth, and projection live.

Renderer contract should not change when exact geometry arrives. Only the `contour_points_px` field gets supplemented by:

```json
{
  "arc_edges": [
    {
      "source_id": "circle_003",
      "center_px": [1048.0, 540.0],
      "radius_px": 180.0,
      "start_angle": 2.09,
      "end_angle": 3.14,
      "winding": "ccw"
    }
  ]
}
```

## 10. Agent B Handoff

Suggested implementation target:

```text
scripts/topology_cell_reveal_renderer_v004.py
track2-deterministic/morph_outputs_INTERNAL/topology_cell_reveal_v004_2026-05-20/
```

Initial modes to implement, in order:

1. `sun_from_seed`
2. `trigon_field_reveal`
3. `crescent_lens_field`
4. `falling_snowflake_layer`

Required first output is recipe/debug JSON. Optional black-screen clips or stills belong to Agent B's renderer pass, not this document.

Acceptance checks:

- construction circles are hidden or low-opacity after scaffold/classify;
- visible cells come from extracted overlap contours;
- `sun_from_seed` shows one center origin and radial curved trigons without a full mandala;
- `trigon_field_reveal` suppresses circles/lenses and isolates three-arc cells;
- `crescent_lens_field` makes two parent arcs legible without stamping crescent icons;
- `falling_snowflake_layer` uses many sparse primitive-cell snowflakes with depth/drift variation;
- every visible cell has `topology_class`, `role`, `region_type`, `source_ids`, `confidence`, and `cultural_status`;
- debug/classify output labels which region type each visible shape came from.

## 11. Referenced Path Verification

Referenced local paths to verify for this spec:

- `docs/space-center/seed-flower-overlap-cell-extraction-spec-2026-05-20.md`
- `docs/space-center/topology-cell-region-taxonomy-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `scripts/primitive_water_grammar_v4.py`
- `scripts/primitive_water_grammar_v5.py`

Created path:

- `docs/space-center/topology-cell-reveal-renderer-spec-2026-05-20.md`
