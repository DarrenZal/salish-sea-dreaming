# Seed / Flower Overlap Cell Extraction Spec - 2026-05-20

Status: internal Agent E implementation spec for Agent B. No rendering. This is mathematical topology extraction guidance only, not Austin-approved grammar, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`

## 1. Purpose

Agent B should render derived cells from seed/flower-of-life circle arrangements, not draw primitive icons on top of construction circles.

The construction system is:

```text
hexagonal circle centers
  -> equal-radius overlap arrangement
  -> extracted bounded cells
  -> boundary-source classification
  -> sparse primitive cell records
```

The visible primitive classes come from cell topology:

- one-boundary closed form -> `circle` / `origin`;
- two-arc lens or lune -> `crescent`;
- three-arc triangular/scallop cell -> `curved_trigon`;
- four or more arcs -> `compound` / `network_cell`.

This spec gives an immediate Python/OpenCV v001 path without new heavy dependencies, plus a future exact geometry path.

## 2. Geometry Setup

### Coordinate System

Use normalized composition coordinates first, then scale to pixels.

```text
world center = (0, 0)
pixel scale = min(width, height) * scale_factor
pixel_point = (width / 2 + x * pixel_scale, height / 2 - y * pixel_scale)
```

Recommended v001 canvas for extraction:

- `W = 960`, `H = 540` for fast iteration.
- `W = 1920`, `H = 1080` only after classification works.
- Keep an internal margin of at least `2R` so partial exterior cells do not dominate the contour set.

### Hexagonal Circle Centers

Use axial hex coordinates `(q, r)` and derive `s = -q - r` only for ring distance.

```text
hex_distance(q, r) = max(abs(q), abs(r), abs(-q-r))

x = center_spacing * (q + 0.5 * r)
y = center_spacing * (sqrt(3) / 2) * r
```

Generate all centers where:

```text
hex_distance(q, r) <= ring_count
```

Sort by:

```text
(hex_distance(q, r), angle_from_origin, q, r)
```

This gives stable source IDs:

```text
seed_000_center
seed_001_ring1_...
flower_019_ring2_...
```

### Ring Growth

Use ring count as the main topology-growth control:

| Stage | `ring_count` | Circle count | Use |
|---:|---:|---:|---|
| 0 | 0 | 1 | origin / one-boundary test |
| 1 | 1 | 7 | seed-of-life extraction fixture |
| 2 | 2 | 19 | sparse flower field |
| 3 | 3 | 37 | stress test only; likely too dense |

For animation, do not continuously move centers in v001. Add whole rings over time and let cells birth/death at ring boundaries. Continuous center motion is a later deformation path because it makes cell identity tracking harder.

### Circle Radius And Spacing

Default:

```text
R = 1.0
center_spacing = R
```

This matches the practical seed/flower overlap study: each neighboring center lies on the other circle's boundary, producing stable lenses and three-arc gaps.

Useful parameter range:

```text
center_spacing = R * spacing_ratio
spacing_ratio in [0.90, 1.15]
```

Guidance:

- `spacing_ratio < 0.90`: overlaps get heavy; cells merge and boundary counts become ambiguous.
- `spacing_ratio = 1.00`: best first test.
- `spacing_ratio > 1.15`: gaps widen; crescents become weak and trigons may stop reading as arc-derived.

Use equal radii in v001. Radius variation is a later path after the classifier is stable.

### Construction Circle Visibility

Construction circles are source geometry, not the final primitive layer.

Recommended layer roles:

```text
construction_circles: hidden by default; low-alpha debug only
extracted_cells: primary visible topology
cell_boundaries: optional outline/debug layer
cell_labels: debug only
```

If construction circles must be shown during an internal review, keep them subordinate:

- alpha below derived cell alpha;
- thin stroke only;
- fade down as derived cells appear;
- never let the full flower lattice become the main image.

The extraction output should carry `construction_visible: false` by default.

## 3. Cell Extraction Options

### Option A: Exact Computational Geometry

This is the cleanest final model because each boundary arc keeps its parent circle ID.

Exact outline:

1. For each circle pair, compute boundary intersections.
2. Store intersection points on both parent circles with polar angle.
3. Split every circle into directed arc segments between consecutive intersection angles.
4. For each candidate arc midpoint, test which side/cell it borders by sampling just inside and just outside the arc.
5. Build a directed half-edge graph from arcs and intersection vertices.
6. Walk closed loops with consistent winding.
7. Discard the unbounded exterior and tiny numerical slivers.
8. Classify each bounded loop by the number of distinct parent arcs after merging adjacent arcs from the same source.

Core pairwise intersection:

```text
d = distance(c1, c2)
no intersection if d <= eps or d > R1 + R2 or d < abs(R1 - R2)
a = (R1^2 - R2^2 + d^2) / (2d)
h = sqrt(max(0, R1^2 - a^2))
p = c1 + a * (c2 - c1) / d
intersection_1 = p + h * perpendicular(c2 - c1) / d
intersection_2 = p - h * perpendicular(c2 - c1) / d
```

Pros:

- best source attribution;
- best boundary count classification;
- stable cell IDs across ring additions;
- no contour noise from rasterization.

Cons:

- more code than v001 needs;
- requires careful numeric tolerances and half-edge loop walking;
- tangencies and nearly coincident points need snapping.

Use this path after the OpenCV prototype proves the cell vocabulary.

### Option B: Raster SDF + Marching Squares

Represent each circle as a signed distance field:

```text
d_i(x, y) = sqrt((x - cx_i)^2 + (y - cy_i)^2) - R
inside_i = d_i < 0
boundary_owner(x, y) = argmin_i abs(d_i(x, y))
```

Build a label image where each pixel stores the set of construction circles containing it. In practice, use a bitmask if the active circle count is small:

```text
region_mask[y, x] = bitset of circles where inside_i is true
```

Connected components of equal `region_mask` values are arrangement cells. Boundaries between labels are extracted with marching squares or OpenCV contours.

Pros:

- simple to implement;
- gives true overlap cells, not icon stamps;
- works for ring growth and phase masks;
- can support source IDs via the bitset and boundary-owner sampling.

Cons:

- raster resolution affects small cells;
- marching squares adds a second implementation if `skimage` is unavailable;
- bitsets are awkward above 63 circles unless using Python integers or tuples.

Marching-squares variant:

- Use `skimage.measure.find_contours` if it is already available in the selected Python environment.
- If avoiding `skimage`, use OpenCV contours on binary masks first and defer subpixel marching squares.

### Option C: OpenCV Contour Hierarchy

This is the recommended v001 path for Agent B because it avoids new heavy dependencies.

Approach:

1. Rasterize each circle interior into a per-source binary mask.
2. Build an integer or Python-int bitmask label image.
3. For each unique nonzero label value, extract connected components.
4. For each component, call `cv2.findContours(..., cv2.RETR_CCOMP or cv2.RETR_TREE, ...)`.
5. Keep outer contours as cell boundaries and store holes from the hierarchy.
6. Sample contour points against the SDF stack to infer parent boundary sources.
7. Classify by merged boundary-source run count.

Pros:

- available today with NumPy/OpenCV;
- gives useful area, centroid, contour, hierarchy, and simplification tools;
- easy pruning of small components;
- can produce JSON cell records immediately.

Cons:

- contours are pixel stair-steps until smoothed/simplified;
- `RETR_TREE` hierarchy can be noisy around tiny islands;
- boundary-source counts can be ambiguous near intersection vertices;
- exact lenses and trigons are approximated, not analytic arcs.

Use this for `v001`.

### Option D: Shapely / skgeom Later

If later available, use a geometry library to polygonize circle boundaries:

- Shapely: approximate circles as high-resolution polygons, run unary union / polygonize / difference, then classify boundaries by nearest source circle.
- scikit-geometry / CGAL path: exact circular arcs and arrangements if bindings are practical.

Pros:

- faster route to robust planar arrangement than hand-rolling a DCEL;
- good for offline recipe generation.

Cons:

- Shapely polygonizes arcs and can lose exact circular metadata unless we preserve it separately;
- skgeom/CGAL may be heavy to install and not suitable for immediate show-machine work.

Do not block v001 on these dependencies.

## 4. Classification

Classify topology from source-arc evidence before visual resemblance.

### Boundary Source Runs

For each contour, sample points every `sample_step_px` pixels along the contour. For each sample:

```text
source_id = argmin_i abs(d_i(point))
distance_to_boundary = min_i abs(d_i(point))
```

Keep samples only when `distance_to_boundary <= boundary_epsilon_px`. Collapse consecutive identical `source_id` samples into runs. Merge very short runs into their larger neighbors.

Recommended v001 thresholds:

```text
boundary_epsilon_px = 2.0 to 4.0
min_arc_fraction = 0.08
min_area_px = 80 at 960x540, scale with resolution
min_perimeter_px = 32 at 960x540, scale with resolution
```

Then compute:

```text
arc_run_count = number of merged source runs
distinct_source_count = number of unique source IDs in merged runs
holes = contour hierarchy hole count
circularity = 4*pi*area / perimeter^2
convexity = area / area(convex_hull)
```

### Class Rules

| Class | Evidence | v001 action |
|---|---|---|
| `circle` / `origin` | One closed outer boundary, zero major holes, one dominant boundary source or the center/source circle itself. Circularity is high or role is explicit origin. | Keep sparingly. Usually one center origin plus selected ring origins. |
| `crescent` | Two dominant arc runs or two source IDs; component is a pairwise overlap lens/lune; medial axis is cupped or elongated. | Keep if it has source relation and area is not tiny. |
| `curved_trigon` | Three dominant arc runs or three source IDs; shape has three curved sides, three lobes, or triangular/scallop gap inherited from circles. | Keep as preferred proof that trigons are derived, not drawn. |
| `compound` / `network_cell` | Four or more arc runs or source IDs; may contain holes or branch-like boundary complexity. | Usually hide or demote to faint network/outline data. |
| `ambiguous` | Low source confidence, conflicting arc counts, tiny sliver, contour touches crop boundary, or unstable across adjacent frames. | Do not render as primitive; keep for debug JSON only. |

Important corrections:

- A perfect-looking crescent is invalid if it has no two-source relation.
- A triangle-like shape is invalid if it is just a simplified spike with no three-arc parentage.
- A circle is not automatically valid if it creates an eye-pair or decorative bubble field.

### Boundary Count vs Source Count

Use `arc_run_count` as the main class feature, not raw contour vertex count.

Examples:

```text
source runs [A]                 -> circle/origin
source runs [A, B]              -> crescent/lens/lune
source runs [A, B, C]           -> curved_trigon
source runs [A, B, C, D, ...]   -> compound/network_cell
```

Near intersection vertices, a contour may briefly report the wrong source. Merge runs shorter than `min_arc_fraction` before classifying.

## 5. Animation Model

This spec does not render. It defines the cell data needed for later rendering.

### Ring Addition Over Time

Topology-growth stages:

```text
t0: ring_count = 0
t1: ring_count = 1
t2: ring_count = 2
t3: optional ring_count = 3 stress pass
```

At each ring stage:

1. Recompute cells for the current center set.
2. Match cells to the previous stage by centroid proximity, source set, and class.
3. Mark unmatched new cells as `birth`.
4. Mark previous cells with no match as `death`.
5. Do not interpolate topology through the exact moment of ring insertion; crossfade display states later.

### Fill / Line Phase Inversion

Use stable extracted cells and animate display roles:

```text
phase = 0.5 + 0.5 * cos(omega * t + cell.phase_offset)
fill_alpha = smoothstep(0.15, 0.85, phase)
line_alpha = 1.0 - fill_alpha
inverse_fill_alpha = smoothstep(0.15, 0.85, 1.0 - phase)
```

The data contract should include:

```text
phase_group: "positive" | "negative" | "outline"
phase_offset: float
can_invert: bool
```

Do not generate cells by thresholding a time-multiplied field at every frame. That creates full-screen nodal flashes and unstable topology.

### Cell Birth / Death

Each cell record should expose lifecycle fields:

```text
birth_ring: int
death_ring: int | null
birth_time_norm: float
death_time_norm: float | null
stability: float
```

Birth priority:

1. center origin;
2. first-ring lenses/crescents;
3. first-ring three-arc trigons;
4. second-ring selected crescents/trigons;
5. compound/network cells only if needed as faint paths.

Death should be a display fade, not a sudden topology pop.

### Radial Wave Propagation

Ring growth can be staged as a radial wave without changing the extracted geometry:

```text
cell_radius = distance(cell.centroid, origin)
wave = smoothstep(front - width, front, cell_radius)
     * (1 - smoothstep(front, front + width, cell_radius))
activation = wave * class_weight * confidence
```

Use radial propagation to activate existing cells from center outward:

- circle/origin activates first;
- crescents activate where two fronts meet;
- curved trigons activate slightly after crescents;
- compound/network cells stay subdued.

## 6. Practical Python/OpenCV v001 Algorithm

Use only NumPy and OpenCV for the first implementation.

Inputs:

```text
width, height
ring_count
R_world
spacing_ratio
world_scale_px
min_area_px
boundary_epsilon_px
max_visible_cells
```

Outputs:

```text
cells: list[CellRecord]
debug: source circles, label stats, rejected components
```

Recommended record:

```json
{
  "cell_id": "seed_r1_label_0003_comp_00",
  "topology_class": "curved_trigon",
  "role": "three_arc_gap",
  "ring_count": 1,
  "source_ids": ["circle_000", "circle_002", "circle_003"],
  "arc_run_count": 3,
  "area_px": 1842.5,
  "perimeter_px": 173.8,
  "centroid_px": [481.2, 238.6],
  "centroid_norm": [0.501, 0.442],
  "orientation_rad": 0.92,
  "confidence": 0.84,
  "phase_group": "positive",
  "phase_offset": 0.18,
  "lifecycle": "birth",
  "construction_visible": false,
  "contour_points_px": [[480, 231], [486, 235]],
  "cultural_status": "internal_austin_review_needed"
}
```

### Step-By-Step v001

1. Generate hex centers for the selected `ring_count`.
2. Convert centers and radius to pixel coordinates.
3. For each source circle, rasterize an interior mask.
4. Build a `uint64` bitset label image while `circle_count <= 63`; switch to Python integer/object labels only for larger stress tests:

```text
label[y, x] |= (1 << source_index) if pixel is inside source circle
```

5. Ignore label `0` exterior pixels unless exterior scallops are deliberately being studied.
6. For each unique label:
   - build `component_mask = (label == unique_label)`;
   - run morphological close/open with a small kernel;
   - run `connectedComponentsWithStats`;
   - reject tiny components;
   - extract contours with `findContours`.
7. For each contour:
   - compute area, perimeter, centroid, circularity, convexity;
   - sample boundary against SDF stack to get source runs;
   - merge short source runs;
   - classify into topology class;
   - assign role and confidence;
   - reject ambiguous/tiny/crop-touching cells.
8. Rank cells and cap visible candidates.
9. Emit JSON recipe data. Rendering is a separate step.

### Ranking For Sparse Output

Score cells before any render pass:

```text
score =
    class_weight
  + confidence
  + source_arc_balance
  + area_balance
  + radial_wave_activation
  - tiny_cell_penalty
  - compound_penalty
  - eye_pair_penalty
  - construction_lattice_penalty
```

Default class weights:

```text
origin/circle: 0.50
crescent: 0.85
curved_trigon: 1.00
compound/network_cell: 0.20
ambiguous: -1.00
```

Hard caps:

- ring 1: keep 6 to 18 derived cells;
- ring 2: keep 12 to 32 derived cells;
- no full lattice render;
- no more than 2 high-contrast origin circles unless an internal review asks for a stress test.

## 7. Failure Modes

### Contour Noise

Cause:

- raster resolution too low;
- mask edges stair-step;
- tiny fragments near circle intersections;
- morphological cleanup too weak or too strong.

Mitigation:

- start at `960x540` or higher;
- close/open with `3x3` kernel only;
- reject by area and perimeter;
- simplify contours after classification, not before;
- keep debug rejected-cell counts.

### Too Many Tiny Cells

Cause:

- high ring count;
- dense flower arrangement shown directly;
- exterior slivers or near-tangent artifacts.

Mitigation:

- cap `ring_count` at `2` for useful studies;
- reject cells under area threshold;
- discard crop-touching cells;
- rank by class confidence and radial activation;
- keep `compound/network_cell` hidden unless specifically requested.

### Construction Circles Overpowering Derived Cells

Cause:

- visible circle strokes remain brighter than extracted cells;
- all source circles are shown at once;
- flower lattice becomes the subject.

Mitigation:

- default `construction_visible: false`;
- use construction circles only as debug layer;
- fade construction strokes down as cells appear;
- render sparse selected derived cells, not the full circle system.

### Ambiguous Boundary Counts

Cause:

- contour samples near intersection vertices flip source IDs;
- arcs from the same source are split by short noisy runs;
- raster labels merge small cells;
- center spacing too tight.

Mitigation:

- merge source runs shorter than `min_arc_fraction`;
- require source confidence above threshold;
- mark uncertain cells `ambiguous`;
- use `spacing_ratio = 1.0` until stable;
- compare against the exact geometry path later.

### Hierarchy / Hole Confusion

Cause:

- `RETR_TREE` reports nested contours from small holes or aliases;
- compound cells contain interior voids.

Mitigation:

- in v001, reject major-hole cells from primitive classes;
- keep holes as `network_cell` metadata;
- use `RETR_CCOMP` first if `RETR_TREE` is too noisy.

### Crop Boundary Artifacts

Cause:

- partial cells cut by the canvas edge;
- exterior region included as a cell.

Mitigation:

- add a world margin;
- reject contours touching image border;
- ignore label `0` exterior;
- only include exterior scallops in a deliberate later pass.

## 8. Pseudocode

```python
def axial_hex_centers(ring_count, spacing):
    centers = []
    for q in range(-ring_count, ring_count + 1):
        for r in range(-ring_count, ring_count + 1):
            s = -q - r
            dist = max(abs(q), abs(r), abs(s))
            if dist <= ring_count:
                x = spacing * (q + 0.5 * r)
                y = spacing * (3 ** 0.5 / 2.0) * r
                centers.append({
                    "source_id": f"circle_{len(centers):03d}",
                    "q": q,
                    "r": r,
                    "ring": dist,
                    "center_world": (x, y),
                })
    centers.sort(key=lambda c: (
        c["ring"],
        math.atan2(c["center_world"][1], c["center_world"][0]),
        c["q"],
        c["r"],
    ))
    for i, center in enumerate(centers):
        center["source_id"] = f"circle_{i:03d}"
    return centers


def build_label_image(width, height, centers_px, radius_px):
    if len(centers_px) > 63:
        raise ValueError("v001 uint64 label path supports up to 63 circles")

    label = np.zeros((height, width), dtype=np.uint64)
    yy, xx = np.mgrid[0:height, 0:width]
    sdf_stack = []
    for i, center in enumerate(centers_px):
        dx = xx - center[0]
        dy = yy - center[1]
        d = np.sqrt(dx * dx + dy * dy) - radius_px
        inside = d < 0
        label[inside] = label[inside] | (np.uint64(1) << np.uint64(i))
        sdf_stack.append(d.astype(np.float32))
    return label, np.stack(sdf_stack, axis=0)


def extract_cells(label, sdf_stack, params):
    cells = []
    for label_value in unique_nonzero_values(label):
        region = (label == label_value).astype(np.uint8) * 255
        region = cv2.morphologyEx(region, cv2.MORPH_CLOSE, params.kernel3)
        region = cv2.morphologyEx(region, cv2.MORPH_OPEN, params.kernel3)

        count, comp, stats, centroids = cv2.connectedComponentsWithStats(region, 8)
        for comp_id in range(1, count):
            area = stats[comp_id, cv2.CC_STAT_AREA]
            if area < params.min_area_px:
                continue

            comp_mask = (comp == comp_id).astype(np.uint8) * 255
            contours, hierarchy = cv2.findContours(
                comp_mask,
                cv2.RETR_CCOMP,
                cv2.CHAIN_APPROX_NONE,
            )

            for contour in outer_contours(contours, hierarchy):
                if touches_border(contour, params.width, params.height):
                    continue

                features = measure_contour(contour)
                source_runs = boundary_source_runs(
                    contour,
                    sdf_stack,
                    params.boundary_epsilon_px,
                    params.min_arc_fraction,
                )
                classification = classify_from_runs(source_runs, features)
                confidence = score_confidence(source_runs, features, classification)

                if classification == "ambiguous" or confidence < params.min_confidence:
                    continue

                cells.append(make_cell_record(
                    contour=contour,
                    label_value=label_value,
                    source_runs=source_runs,
                    features=features,
                    classification=classification,
                    confidence=confidence,
                ))

    return rank_and_cap(cells, params.max_visible_cells)


def classify_from_runs(source_runs, features):
    run_count = len(source_runs)
    source_count = len({run.source_id for run in source_runs})

    if features.holes > 0:
        return "compound"
    if run_count <= 1 and source_count <= 1:
        return "circle"
    if run_count == 2 or source_count == 2:
        return "crescent"
    if run_count == 3 or source_count == 3:
        return "curved_trigon"
    if run_count >= 4 or source_count >= 4:
        return "compound"
    return "ambiguous"
```

Implementation note: ring 2 has only 19 circles and ring 3 has 37 circles, so `uint64` is enough for the first useful seed/flower fields. A Python-int/object label path is only needed for wider stress tests.

## 9. Future Exact Geometry Path

The future exact extractor should replace the raster label/contour step with a circular-arc arrangement.

Target data structures:

```text
CircleSource:
  source_id
  center
  radius
  ring

IntersectionVertex:
  vertex_id
  point
  incident_source_ids

ArcHalfEdge:
  edge_id
  source_id
  start_vertex_id
  end_vertex_id
  start_angle
  end_angle
  left_sample_label
  right_sample_label

CellFace:
  cell_id
  ordered_edge_ids
  source_ids
  arc_run_count
  area
  centroid
  topology_class
```

Exact loop walk:

1. Snap intersection vertices within `eps`.
2. Sort each circle's vertices by angle.
3. Create clockwise and counterclockwise half-edges for each consecutive vertex pair.
4. At each vertex, sort outgoing half-edges by tangent angle.
5. Walk faces by taking the next half-edge that keeps the face on the same side.
6. Compute signed area to reject exterior or wrong-winding loops.
7. Merge adjacent half-edges from the same source into source runs.
8. Classify faces with the same rules as v001.

Why this matters later:

- exact arc metadata gives cleaner crescents and trigons;
- cell identity can persist through ring additions;
- contours can be exported as Bezier/SVG-like arcs instead of pixel polylines;
- TouchDesigner/WebGL can render derived cells from recipe data while Python remains the topology authority.

Do not implement this until v001 has proven that derived overlap cells are visually useful.

## 10. Agent B Handoff

Immediate build target:

```text
scripts/seed_flower_overlap_cells_v001.py
track2-deterministic/morph_outputs_INTERNAL/seed_flower_overlap_cells_v001_2026-05-20/
```

Required first output:

- JSON recipe containing cells, rejected-cell stats, and source circle metadata.
- Optional debug stills only if the renderer path is already approved separately.
- No final rendering in this spec.

Acceptance checks for the v001 extractor:

- `ring_count = 1` produces center/source cells, pairwise lens/crescent candidates, and at least some three-arc `curved_trigon` candidates.
- Construction circles are hidden or marked debug-only in the output contract.
- Every visible candidate has `topology_class`, `role`, `source_ids`, `arc_run_count`, `confidence`, and `cultural_status`.
- Ambiguous cells are rejected or marked debug-only.
- Full flower lattice display is not the default output.

## 11. Source And Path Verification

Referenced source paths verified locally during this pass:

- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`

Created path:

- `docs/space-center/seed-flower-overlap-cell-extraction-spec-2026-05-20.md`
