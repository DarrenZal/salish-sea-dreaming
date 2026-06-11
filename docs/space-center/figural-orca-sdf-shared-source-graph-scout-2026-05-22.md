# Figural Orca SDF Shared Source Graph Scout - 2026-05-22

Status: INTERNAL STILL-IMAGE SCOUT ONLY. Pending Austin review. No MP4 or MOV was rendered. No source artwork was modified.

Goal: test whether one shared SDF / Voronoi / medial-axis source set, derived from Austin's Orca construction geometry, reads as a coherent figural primitive graph.

Source and provenance:

- Source artwork: `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
- Source SHA-256: `9608002e18224fe275059a7e4a9ef3d403eafc639a53afea5efc88929d9a6dcb`
- Generator: [figural_orca_sdf_shared_source_graph_scout_v001.py](../../track2-deterministic/scripts/figural_orca_sdf_shared_source_graph_scout_v001.py)
- JSON fit/source data: [orca_sdf_shared_source_graph_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_sdf_shared_source_graph_candidates_v001.json)
- Debug still folder: `track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22`
- Previous SDF scout: [figural-orca-sdf-medial-axis-scout-2026-05-22.md](figural-orca-sdf-medial-axis-scout-2026-05-22.md)

## Method

This scout does not place separate local construction triplets around each target. It segments measured source-color components from the Orca PNG, estimates visible primitive centers, then estimates implied construction centers from source contours:

- visible ovals/circles: component centroid, major axis, minor axis, and orientation from PCA over source pixels;
- crescents: two contour arcs split by source contour endpoints, each fit with a least-squares circle and labeled outer arc versus inner cutting arc by fitted radius;
- trigons: three contour corners from the source contour, then one circle fit per arc-bounded side;
- all visible primitive centers and implied arc centers are pooled as one shared source set before computing nearest-source labels and ridges.

The field operation is a global nearest-source distance field over analytic circle, circle-arc, and ellipse sources. The Voronoi map is the nearest-source label image. The ridge graph is the thinned boundary where nearest-source ownership changes, clipped by the Orca alpha envelope. Final linework is only SDF contour bands and nearest-source ridge pixels; it contains no source markers, labels, symbolic primitive overlays, or source Orca pixels.

## Debug Stills

- [01 visible centers](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_01_visible_primitive_centers_marked.png)
- [02 implied construction centers](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_02_implied_crescent_trigon_centers_marked.png)
- [03 all shared SDF sources](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_03_all_sdf_sources_over_orca.png)
- [04 Voronoi nearest-source map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_04_voronoi_nearest_source_map.png)
- [05 medial-axis ridge graph over Orca](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_05_medial_axis_ridge_graph_over_orca.png)
- [06 final composite, no labels](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_06_final_composite_no_labels.png)
- [07 side-by-side previous SDF scout](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_07_side_by_side_previous_sdf.png)
- [debug sheet](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_sdf_shared_source_graph_scout_v001_2026-05-22/figural_orca_sdf_shared_source_graph_scout_v001_debug_sheet.png)

## Measurement Summary

| Count | Value |
|---|---:|
| Measured visible/source components | 27 |
| Shared SDF sources | 51 |
| Visible ovals | 5 |
| Visible circles | 1 |
| Crescents with implied centers | 18 |
| Trigons with implied centers | 3 |

### Dorsal Trigon

The dorsal trigon was fit from the actual blue-gray source component contour, not by a small local construction triplet.

| Side | Center canvas px | Radius canvas px | Fit error source px | Arc mid angle deg |
|---|---:|---:|---:|---:|
| 1 | [1953.395, 1140.233] | 571.539 | 0.25 | -109.904 |
| 2 | [1462.373, 441.284] | 308.081 | 0.533 | 17.637 |
| 3 | [1886.061, 747.454] | 173.399 | 0.432 | -99.798 |

## Field Metrics

| Metric | Value |
|---|---:|
| Orca envelope area px | 1391605 |
| Visible final-feature px inside Orca envelope | 616784 |
| Visible final-feature px outside Orca envelope | 0 |
| Ridge components after r=2 dilation | 3 |
| Ridge largest component fraction | 0.9996 |
| Final feature components after r=2 dilation | 3 |
| Final feature largest component fraction | 0.9999 |

Zone feature hits:

| Zone | Feature px |
|---|---:|
| Head / eye | 276292 |
| Dorsal | 40013 |
| Body | 258628 |
| Pectoral | 125570 |
| Tail | 63617 |
| Rear side | 49269 |

## Evaluation

- PASS criterion, coherent whole-Orca primitive graph: yes
- PASS criterion, no outside-envelope clutter: pass; zero visible final-feature pixels outside envelope
- PASS criterion, connected relationships across eye/body/dorsal/tail: pass; all named zones have derived field features
- Dorsal trigon read: improved; fitted from real side arcs rather than three small local circles

Verdict: **PASS**.

Rationale: The shared source graph reads as one Orca-related primitive graph, connects head, dorsal, body, pectoral, and tail regions, and produces no visible features outside the Orca envelope.

## Verification Notes

- JSON parses with `python -m json.tool`.
- Markdown links are repository-relative from this document.
- Generated text artifacts are ASCII.
- Source SHA-256 was recorded before generation and checked again after output.
- The scout wrote PNG stills only.
- No MP4 or MOV was created under the scout output folder.
