# Figural Orca SDF / Medial-Axis Scout - 2026-05-22

Status: INTERNAL STILL-IMAGE SUBSTRATE SCOUT ONLY. No MP4 or MOV was
rendered. No source artwork was modified. This is a substrate validation pass,
not a beauty render and not an approval artifact.

Goal: test whether SDF / medial-axis fields can produce coherent figural
internal primitive structure for Austin's Orca without the non-local spurious
feature problem that broke the Type 1 and Type 2 wave-interference scouts.

Prior context:

- [substrate-first-figural-reveal-research-2026-05-22.md](substrate-first-figural-reveal-research-2026-05-22.md)
- [figural-orca-wave-interference-match-research-scout-2026-05-22.md](figural-orca-wave-interference-match-research-scout-2026-05-22.md)
- [figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md](figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md)

Reviewed source:

- Source artwork: `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
- Source SHA-256:
  `9608002e18224fe275059a7e4a9ef3d403eafc639a53afea5efc88929d9a6dcb`
- Placement transform: scale `0.88`, top-left `[896, 122]`, display size
  `[2219, 1949]` on a `3840x2160` canvas.
- Prior anchor JSON:
  [orca_wave_interference_fit_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001.json)
- SDF candidate JSON:
  [orca_sdf_medial_axis_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_sdf_medial_axis_candidates_v001.json)
- Generator:
  [figural_orca_sdf_medial_axis_scout_v001.py](../../track2-deterministic/scripts/figural_orca_sdf_medial_axis_scout_v001.py)
- Debug folder:
  `track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22`

## Method

The scout reused the eight fit-attempt Orca anchors from the wave-interference
candidate JSON and excluded the rear vertical compound region.

Source silhouette rules:

- Circle / oval anchors: one rotated oval source matched to the measured
  anchor extents.
- Crescent anchors: two mirrored oval sources placed so the nearest-source
  medial ridge passes through the target centroid.
- Trigon anchors: three oval sources placed around the target centroid so the
  medial triple-junction lands at the centroid.

The union SDF was computed as:

```text
sdf = distance_to_outside_of_source_union - distance_inside_source_union
```

using `scipy.ndimage.distance_transform_edt`.

Visible substrate features were extracted only from computed fields:

- SDF isocontours at `0`, `18`, `42`, `78`, and `126` px;
- source-internal medial-axis branches;
- nearest-source medial-axis ridges;
- SDF influence-band medial-axis branches;
- gradient / ridge shock cues from the SDF.

The final composite contains no source Orca pixels, no anchor labels, no source
silhouette fills, and no drawn primitive shapes. The linework is rasterized
from SDF, medial-axis, or ridge masks.

## Debug Stills

- [01 source anchors marked](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_01_source_anchors_marked.png)
- [02 source silhouettes over Orca](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_02_source_silhouettes_over_orca.png)
- [03 SDF isocontours over Orca](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_03_sdf_isocontours_over_orca.png)
- [04 medial-axis network over Orca](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_04_medial_axis_network_over_orca.png)
- [05 labeled primitive cells and anchors](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_05_labeled_primitive_cells_and_anchors.png)
- [06 SDF primitive structure composite, no source visible](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_06_sdf_primitive_structure_composite_no_source.png)
- [debug sheet](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_medial_axis_scout_v001_2026-05-22/figural_orca_sdf_medial_axis_scout_v001_debug_sheet.png)

## Anchor Results

| Candidate | Class | Intended operation | Nearest visible SDF feature px | Status |
|---|---|---|---:|---|
| `eye_upper_pale_ovoid` | circle/oval | SDF zero isocontour plus source-internal medial-axis branch | 0.000 | PASS |
| `lower_large_pale_ovoid` | circle/oval | SDF zero isocontour plus source-internal medial-axis branch | 7.280 | PASS |
| `lower_small_pale_ovoid` | circle/oval | SDF zero isocontour plus source-internal medial-axis branch | 0.000 | PASS |
| `dorsal_inner_trigon` | trigon / three-arc | medial-axis junction from three oval source silhouettes | 0.000 | PASS |
| `upper_body_bluegray_crescent` | crescent/lens | medial-axis ridge from paired oval source silhouettes | 0.000 | PASS |
| `central_pectoral_bluegray_crescent` | crescent/lens | medial-axis ridge from paired oval source silhouettes | 0.000 | PASS |
| `tail_fluke_bluegray_crescent` | crescent/lens | medial-axis ridge from paired oval source silhouettes | 0.000 | PASS |
| `tail_upper_bluegray_trigon` | trigon / three-arc | medial-axis junction from three oval source silhouettes | 0.000 | PASS |

Anchor gate result: all eight retained anchors have a visible SDF-derived
feature within `24` px of the target centroid.

## Field Metrics

| Metric | Value |
|---|---:|
| Source silhouette count | 15 |
| Orca envelope area px | 1391605 |
| Source silhouette area px | 259248 |
| Visible final-feature px inside Orca envelope | 170581 |
| Visible final-feature px outside Orca envelope | 0 |
| Full medial network components after r=2 dilation | 358 |
| Full medial network largest component fraction | 0.5906 |
| Nearest-source ridge components after r=2 dilation | 4 |
| Nearest-source ridge largest component fraction | 0.8032 |

The important improvement over Type 1 and Type 2 wave interference is the
outside-envelope result: the final composite has zero visible feature pixels
outside the Orca alpha envelope. The prior wave scouts had valid local fits
but many incidental count or gap components caused by non-local source
interaction. This SDF pass does not show that same outside-field clutter.

The remaining weakness is graph cohesion. The nearest-source ridge graph is
mostly dominated by one component, but the full visible medial network still
breaks into many small contour and source-skeleton components. Visually, the
composite reads more source-local than a single whole-body primitive graph,
especially between the lower body, dorsal cluster, and tail cluster.

## Provenance Check

Every visible primitive feature in the final composite has a substrate
operation:

| Visible feature family | Provenance |
|---|---|
| Oval outlines and nested rings | SDF isocontours from the union of oval source silhouettes |
| Oval centerlines | `skimage.morphology.medial_axis` on source-silhouette interiors |
| Crescent center arcs | nearest-source medial ridges between paired oval sources |
| Trigon junction marks | nearest-source medial junctions between three oval sources |
| Long binding arcs | SDF influence-band medial-axis branches clipped to the Orca envelope |
| Fine shock/ridge cues | gradient/ridge mask derived from the SDF field |

No final visible primitive is a hand-drawn oval, crescent, trigon, label, or
symbolic overlay.

## Evaluation

- Does every internal anchor have a visible SDF-derived primitive at or near
  its centroid? **Yes.** All eight retained anchors pass the `24` px centroid
  feature gate.
- Does the composite still read as one coherent Orca-related primitive field?
  **Partial.** It plausibly relates to the Orca layout, but still reads as
  clustered source-local geometry rather than a single fully bound graph.
- Are there near-zero spurious cells outside the Orca silhouette envelope?
  **Yes.** The measured outside-envelope visible feature count is `0`.
- Does the medial-axis network form a connected arc/junction graph rather than
  separated local devices? **Partial / no.** The nearest-source ridge is mostly
  connected, but the full visible medial network still has many fragments.
- Does the result feel more coherent than the prior Type 1 / Type 2 wave
  scouts? **Yes on locality and spurious-feature control; partial on global
  figural read.**

## Verdict

Verdict: **PARTIAL**.

The substrate is not a hard fail. It lands all eight retained anchors and
solves the wave-interference failure mode of non-local spurious feature
generation. However, the composite still reads diagrammatic and source-local
rather than as one unified Orca primitive field. This supports a second pass
with a solver or shared-source layout to connect the body, dorsal, and tail
clusters before committing renderer time to an animated beauty pass.

Recommended next pass:

- Keep SDF / medial-axis as a viable substrate.
- Replace per-anchor local source placement with a shared source graph whose
  Voronoi / medial ridges intentionally connect adjacent anchors.
- Treat styling as secondary; the next test should first improve graph
  cohesion without drawing new primitives.

## Verification Notes

- JSON parses with `python -m json.tool`.
- Markdown links are repository-relative from this document.
- Source SHA-256 was recorded before generation and checked again after output.
- The scout wrote PNG stills only.
- No MP4 or MOV was created under the scout output folder.
- The source artwork path remains a read-only input and was not modified.
