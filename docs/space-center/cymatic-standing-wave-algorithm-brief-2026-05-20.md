# Cymatic Standing-Wave Algorithm Brief - 2026-05-20

Status: internal Agent E research/design brief only. No rendering. Not Austin-approved, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Read with:

- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/README.md`
- `track2-deterministic/primitive_grammar/grammar_v001.json`

## 1. Verdict

The best practical path is not a full physics simulator first. Use analytic standing-wave scalar fields, extract contours and connected cells, classify those cells into circle/crescent/trigon topology classes, and render only sparse selected primitive phrases.

Recommended v002 direction for Agent B:

1. Build a deterministic Python 3.11 field-and-contour extractor around three field families: multi-emitter standing interference, circular membrane/Bessel harmonics, and exact overlapping-circle seed/flower geometry.
2. Treat nodal lines as stable outlines from the spatial field `F(x, y) = 0`.
3. Treat antinodal regions as filled cells from `F(x, y) > tau` and `F(x, y) < -tau`.
4. Animate phase inversion by swapping which polarity is filled vs outlined, not by letting the entire field collapse to zero at quarter-cycle.
5. Export cell records with source attribution, contour geometry, topology class, phase polarity, and primitive role before any final drawing.

This keeps the math beautiful enough for cymatics while preserving the primitive grammar contract: circles are one-boundary cells, crescents are two-arc relational cells, and trigons are three-arc or triangular release cells.

## 2. Ranked Algorithm Options

| Rank | Algorithm | Best motifs | Why it ranks here | Python/OpenCV now | TouchDesigner later |
|---:|---|---|---|---|---|
| 1 | Analytic multi-emitter standing-wave interference | rain-on-water, ripple fields, networks, Chladni-like bands | Highest beauty/control ratio. Creates overlapping wavefronts, lenses, crescents, and three-source gaps without a solver. | Strong. NumPy field + OpenCV contours + optional SciPy/skimage marching squares. | Strong. GLSL TOP field, CHOP-driven emitters, live phase/audio control. |
| 2 | Exact overlapping-circle / seed-flower CSG, then wave modulation | seed of life, flower of life, lunes, trigons | Best topology generator. Gives clean parent-source labels for crescent/trigon classification. Less physically cymatic unless modulated by wave phase. | Very strong. Distance fields and boolean masks are simple. | Strong as SDF glyph source or mask library. |
| 3 | Circular membrane modes with Bessel radial harmonics | snowflakes, sun/ripple fields, radial cymatics | Produces elegant radial nodes, petals, rings, and lobes. Maps well to sixfold frozen-water and radiant fields. | Strong with SciPy Bessel functions. | Strong in GLSL if zeros are precomputed; audio can switch modes. |
| 4 | Chladni rectangular/elliptical plate equations | Chladni plates, nodal-line activation | Reliable nodal-line substrate. Good for outlines, but cell classification can become stripe/grid-like without pruning. | Strong. Pure analytic field and contours. | Strong. GLSL field, live mode mixing. |
| 5 | Discrete damped wave-equation heightfield | touch impacts, live rain, audience ripples | Best for real impacts and mouse/touch, but cell extraction from a changing field is harder and noisier. | Moderate. Feasible at low res; needs stabilization and post filters. | Very strong. Feedback TOP/GLSL and audio/touch inputs fit TD. |
| 6 | FFT ocean / Tessendorf / fluid shader fields | deep water atmosphere | Beautiful water, weak primitive topology unless paired with separate SDF extraction. | Weak for immediate v002. More infrastructure than needed. | Useful later as background heightfield, not primary grammar extractor. |

## 3. Core Equations

### Multi-Emitter Standing Interference

Use point emitters as standing spatial fields first:

```text
r_i(x, y) = sqrt((x - x_i)^2 + (y - y_i)^2)
F(x, y) = sum_i A_i * cos(k_i * r_i + phi_i) * exp(-r_i / lambda_i)
Z(x, y, t) = F(x, y) * cos(omega * t)
```

For same-frequency coherent emitters, set most `k_i` equal and vary only amplitude, phase, and falloff. For rain-on-water, use short-lived emitters but still extract cells from a frozen spatial field per event window.

### Chladni Plate Family

For a rectangular plate-like visual:

```text
F_nm(x, y) =
    cos(n * pi * x / Lx) * cos(m * pi * y / Ly)
  - cos(m * pi * x / Lx) * cos(n * pi * y / Ly)

Z_nm(x, y, t) = F_nm(x, y) * cos(omega_nm * t)
```

Mix two or three low-order modes only:

```text
F = w1 * F_nm + w2 * F_pq + w3 * F_rs
```

Keep the mode count low. Dense high-order Chladni patterns quickly become wallpaper and do not preserve sparse primitive phrases.

### Circular Membrane / Bessel Modes

For a circular membrane of radius `R`:

```text
r = sqrt((x - cx)^2 + (y - cy)^2)
theta = atan2(y - cy, x - cx)
F_mn(r, theta) = J_m(alpha_mn * r / R) * cos(m * theta + theta0)
Z_mn(r, theta, t) = F_mn(r, theta) * cos(omega_mn * t + phase)
```

`J_m` is the Bessel function of the first kind. `alpha_mn` is the nth zero of `J_m`, so the membrane is zero at the boundary. Practical mode picks:

- `m = 0, n = 2..4` for rings and ripple basins.
- `m = 3, n = 1..3` for triangular/trigon pressure.
- `m = 6, n = 1..3` for snowflake/radial fields.
- Blend `m = 0` with `m = 6` for sun/ripple fields.

### Discrete Damped Wave Equation

Use this later for live impacts:

```text
lap = u[x-1,y] + u[x+1,y] + u[x,y-1] + u[x,y+1] - 4*u[x,y]
u_next = damping * (2*u - u_prev + c^2 * dt^2 * lap + dt^2 * input)
```

This is excellent for mouse/touch/rain impulses, but use it after the analytic extractor is proven because the changing topology makes classification harder.

### Exact Circle CSG For Seed/Flower Cells

Represent each circle boundary as a signed distance:

```text
d_i(x, y) = sqrt((x - cx_i)^2 + (y - cy_i)^2) - R_i
inside_i = d_i < 0
ring_i = abs(d_i) < epsilon
```

Pairwise overlaps give lenses/lunes:

```text
lens_ab = inside_a and inside_b
crescent_a_minus_b = inside_a and not inside_b
```

Three-circle residual or overlap cells give trigon candidates:

```text
tri_cell_abc = region whose boundary samples are attributed to circles a, b, and c
```

This exact CSG path should be used as a topology test fixture for the contour classifier.

## 4. Phase Inversion

Do not implement inversion by thresholding `Z(x, y, t)` directly at every frame. At `cos(omega*t) = 0`, the whole field becomes numerically nodal and the visual will flash into a full-screen mask.

Instead:

1. Compute the stable spatial topology once per field window:

```text
node_lines = contour(F, level=0)
positive_cells = connected_regions(F > tau)
negative_cells = connected_regions(F < -tau)
```

2. Animate the display state with an oscillator:

```text
p = 0.5 + 0.5 * cos(omega * t)
positive_fill_alpha = smoothstep(0.15, 0.85, p)
negative_fill_alpha = smoothstep(0.15, 0.85, 1 - p)
positive_outline_alpha = 1 - positive_fill_alpha
negative_outline_alpha = 1 - negative_fill_alpha
node_outline_alpha = constant or gently pulsed
```

3. Render phase swap as a role swap:

```text
phase A: positive antinodes are filled cells; negative cells are outline/void accents
phase B: negative antinodes are filled cells; positive cells are outline/void accents
nodes: stable membrane outlines across both phases
```

This creates the vibrating-membrane effect Darren asked for: lines and fills swap like a phase inversion while the contour topology remains legible.

## 5. Contour And Cell Extraction

### Recommended Python v002 Pipeline

Use `/opt/homebrew/bin/python3.11` for v002 work on this machine: it has `numpy`, `cv2`, `scipy`, and `skimage` available. The default `/opt/homebrew/bin/python3` is Python 3.14.2 and currently lacks `cv2` and `skimage`.

```text
for scene in selected_field_family:
    F = make_field(scene, W_field, H_field)
    F = normalize_and_smooth(F)

    node_contours = contours_at_level(F, 0.0)
    pos_masks = threshold(F > tau)
    neg_masks = threshold(F < -tau)

    pos_components = connected_components(pos_masks)
    neg_components = connected_components(neg_masks)

    for component in pos_components + neg_components:
        contour = outer_boundary(component)
        hole_count = contour_hierarchy_holes(component)
        features = measure_contour(contour, F, emitter_sources)
        class_name = classify_topology(features)
        if keep_sparse_candidate(class_name, features):
            emit_cell_record(component, contour, class_name, features)
```

Use OpenCV now:

- `cv2.findContours` for binary nodal bands and antinode component boundaries.
- `cv2.connectedComponentsWithStats` for area, centroid, and pruning.
- `cv2.approxPolyDP`, `cv2.arcLength`, `cv2.contourArea`, and fitted ellipse/circle metrics for shape features.
- Morphological open/close to remove speckle before classification.

Use marching squares when subpixel contours matter:

- `skimage.measure.find_contours(F, level)` is available under Python 3.11.
- If avoiding `skimage`, implement a small marching-squares table for level `0`, `tau`, and `-tau`.

### Feature Measurements

For each closed component:

```text
area = contourArea(contour)
perimeter = arcLength(contour)
circularity = 4*pi*area / perimeter^2
bbox_aspect = width / height
holes = hierarchy_hole_count
curvature_peaks = count_dominant_curvature_extrema(contour)
source_ids = parent_wave_sources_along_boundary(contour)
polarity = sign(mean(F inside component))
```

For parent-source attribution, sample points along the boundary and assign each point to the nearest field contributor:

```text
source_id(point) = argmax_i abs(A_i * cos(k_i*r_i + phi_i) * exp(-r_i/lambda_i))
unique_sources = stable source ids after removing tiny arc fragments
```

For exact circle CSG, source attribution is cleaner:

```text
source_id(point) = argmin_i abs(d_i(point))
```

### Topology Classification

Classify by boundary relations before visual resemblance:

| Class | Required evidence | Reject if |
|---|---|---|
| `circle` / one-boundary cell | One closed outer boundary, no major holes, circularity high enough or fitted ellipse stable, source count 1 or antinode island role clear. | It is one of a paired eye-like cluster, too tiny, or lacks an origin/pressure role. |
| `crescent` / lens / lune | Boundary has two dominant source arcs, or component is a pairwise overlap/difference cell, or medial axis is curved and cupped. | It is only a decorative moon stamp with no source relation. |
| `trigon` / three-arc cell | Boundary has three dominant source arcs, three curvature lobes, or three neighboring pressure regions; centroid points toward release. | It is a generic sharp triangle, UI arrow, or isolated spike. |
| `outline` / nodal line | Long or branching contour at `F = 0`; used as membrane/line, not filled primitive. | It becomes dense grid texture or competes with filled cells. |
| `network` | Nodal contours form stable graph nodes/edges; intersections have degree 3 or more. | All nodes fire equally or become a Cartesian mesh. |

### Sparse Selection

After classification, rank candidates and keep only the strongest:

```text
score =
    topology_confidence
  + source_arc_balance
  + contour_smoothness
  + distance_from_recent_cells
  + role_priority
  - density_penalty
  - eye_pair_penalty
  - generic_triangle_penalty
```

Hard caps for v002:

- 3 to 7 active origins/emitters.
- 8 to 24 filled primitive cells per frame family.
- 1 to 4 stable nodal-line groups.
- No all-frame flower lattice.
- No two high-contrast circles placed as a face-like pair.

## 6. Recommended v002 Renderer Approach For Agent B

Build a new deterministic renderer/extractor instead of extending the v001 hand-drawn cymatic studies directly.

Suggested future file shape. These are proposed implementation paths, not files created by this brief:

```text
scripts/cymatic_standing_wave_cells_v002.py
track2-deterministic/morph_outputs_INTERNAL/cymatic_standing_wave_cells_v002_2026-05-20/
```

Recommended internal modules:

```text
make_field_multi_emitter(params) -> F
make_field_bessel_modes(params) -> F
make_field_chladni(params) -> F
make_seed_flower_sdf(params) -> signed_distance_stack
extract_cells(F, source_model, thresholds) -> list[Cell]
classify_cell(cell, source_model) -> topology_class
phase_style(cell, t) -> fill_alpha, outline_alpha
write_recipe_json(cells, params, status)
```

Data contract for extracted cells:

```json
{
  "cell_id": "rain_pond_003_pos_012",
  "topology_class": "crescent",
  "role": "interference_lune",
  "polarity": "positive",
  "phase_offset": 0.25,
  "source_ids": ["emitter_01", "emitter_03"],
  "contour_points": [[0.42, 0.51], [0.43, 0.52]],
  "centroid": [0.44, 0.54],
  "orientation_rad": 1.2,
  "confidence": 0.82,
  "cultural_status": "internal_austin_review_needed"
}
```

Implementation choices:

- Field resolution: start at `640x360` or `960x540`, then scale contours to 1920x1080 if rendering later.
- Smoothing: light Gaussian blur on `F` before contouring; avoid noise-driven texture.
- Thresholds: adaptive `tau = percentile(abs(F), 68..80)` per field family, with fixed clamps for reproducibility.
- Contour simplification: simplify only after classification; premature simplification destroys crescent/trigon source arcs.
- Output: write JSON cell recipes first, then optional black-screen layers after this brief's scope.

Why this is better than drawing more motifs:

- It proves whether cymatic math can generate primitive topology, not just decorate with primitive icons.
- It gives Agent B a testable extraction contract.
- It keeps TouchDesigner migration clean: Python can remain the topology classifier while TD becomes the live shader/phase renderer.

## 7. Failure Modes

1. Full-screen nodal flash: caused by thresholding the time-multiplied field at quarter phase. Fix by extracting topology from stable `F(x, y)` and animating polarity display.
2. Wallpaper/mandala overload: high-order Chladni, flower-of-life, or Bessel modes fill the whole frame. Fix with low mode counts, sparse selection, and region caps.
3. Generic triangle trigons: contour simplification can turn a three-arc gap into a sharp triangle. Fix by preserving curved source arcs and rejecting arrow-like shapes.
4. Eye/creature reads: paired circles or circle-in-crescent clusters can read as faces. Fix with role labels, spacing penalties, subdued circle contrast, and no paired high-contrast origins.
5. Crescent as decorative moon: a two-arc shape without source relation is weak. Fix by requiring two parent arcs, a cupping target, or wavefront relation.
6. Contour speckle: noisy fields create many tiny islands. Fix with smoothing, area thresholds, morphological cleanup, and confidence scoring.
7. Source attribution ambiguity: interference fields can make mixed boundaries hard to label. Fix by keeping emitters few, adding CSG seed fixtures, and discarding low-confidence cells.
8. Chladni grid read: rectangular modes can look like math wallpaper instead of water/cymatics. Fix with elliptical masks, low-order mode blends, and sparse primitive extraction.
9. TD topology gap: TouchDesigner is good at live fields but weaker at robust topology classification. Fix by precomputing cells in Python or using TD only for phase/shading after Python emits recipes.
10. Cultural-status drift: sun/ray, snowflake, fish, bird, and figure associations may raise review load. Fix by marking all outputs internal and Austin-review-needed, and by keeping the brief water/cymatics-only.

## 8. Next 3 Render Experiments

No rendering is performed in this brief. These are the recommended next experiments when rendering resumes.

### Experiment 1: Rain Pond Standing Interference v002

- Field: 5 coherent point emitters with damped radial standing waves.
- Extraction: nodal outlines at `F = 0`; antinode cells from `F > tau` and `F < -tau`.
- Primitive focus: impact circles only at emitter origins; pairwise overlap cells as crescents/lunes; three-source gaps as trigons.
- Motion: polarity display swap over 6 seconds; node outlines remain stable.
- Success criterion: one still frame reads as rain-on-water cymatics, and the loop reads as membrane inversion rather than ring expansion only.

### Experiment 2: Seed/Flower CSG Plus Phase Field

- Field: exact seven-circle seed and one sparse twelve-circle flower ring, modulated by a low-order standing wave.
- Extraction: source-attributed circle/lens/trigon cells from CSG first, then activate them by wave polarity.
- Primitive focus: prove that overlapping circles naturally produce two-arc crescents/lunes and three-arc trigons.
- Motion: cells reveal from circle boundaries into lenses/trigons, then invert fill/outline phase.
- Success criterion: viewer can see topology emerging from overlap without the full flower lattice becoming wallpaper.

### Experiment 3: Circular Membrane Snow/Sun/Ripple Mode

- Field: blend `m=0` ring modes with `m=6` radial modes using precomputed Bessel zeros.
- Extraction: rings and lobes become nodal outlines; selected radial antinode cells become crescents and trigons.
- Primitive focus: frozen-water/snowflake and sun/ripple fields without exact Austin sun replication.
- Motion: sixfold phase breathing with sparse radial release cells.
- Success criterion: radial field reads as water/snow/sun geometry depending on context, not as a generic mandala.

## 9. TouchDesigner / Audio-Reactive Path

TouchDesigner should become the live renderer after the Python topology extractor proves the field families.

Recommended TD network:

```text
Audio Device In CHOP / OSC / MIDI / Touch input
  -> Analyze CHOP / FFT CHOP / Filter CHOP
  -> emitter and mode parameter DAT/CHOP
  -> GLSL TOP field generator: multi-emitter, Chladni, or Bessel
  -> Threshold/Level TOP masks for positive, negative, nodal bands
  -> optional Python DAT precomputed cell recipe ingest
  -> SDF primitive raster TOP
  -> heightfield merge TOP
  -> Slope/normal GLSL TOP
  -> caustic/refraction/bloom TOP
  -> Movie File Out / NDI / Spout / Resolume layer
```

Audio mappings:

- Amplitude/RMS: global membrane energy, fill opacity, bloom, and ripple strength.
- Onsets/transients: trigger rain impacts or add temporary point emitters.
- Low band: radius, damping, and large ring modes.
- Mid band: Chladni mode blend or emitter phase offsets.
- High band: trigon release density, shimmer, and outline brightness.
- Spectral centroid: shift between water/rain, snow/radial, and sun/ripple mode families.
- Voice pitch estimate: choose Bessel angular mode `m` or Chladni mode pair.

Control mappings:

- Resolume knobs: density cap, phase speed, line/fill balance, mode family, colorway, bloom, and blackout.
- Mouse/touch: inject wave-equation impulses or temporary emitters at normalized coordinates.
- Web-app dream prompts: never feed raw prompt text into TD. Map prompt to a bounded `template_id` and numeric parameters before it reaches the renderer.
- Offline fallback: deterministic mode presets with fixed seeds, no internet requirement, and pre-rendered Resolume clips if live TD is unstable.

Division of labor:

- Python remains the robust topology extraction and recipe-writing path.
- TD handles live phase inversion, audio reactivity, heightfield shading, refraction, and show output.
- Resolume remains the production fallback layer stack.

## 10. Source And Path Verification

Verified local source paths during this pass:

- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/README.md`
- `track2-deterministic/primitive_grammar/grammar_v001.json`

No external web links are referenced in this brief.
