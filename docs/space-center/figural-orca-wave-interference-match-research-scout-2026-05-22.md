# Figural Orca Wave-Interference Match Research Scout - 2026-05-22

Status: INTERNAL RESEARCH + GEOMETRY-FIT SCOUT ONLY. No beauty MP4 was rendered. No source artwork was modified. Target masks in this report are source-derived measurement masks used only to evaluate construction-circle fits; they are not a render mechanism.

Goal: evaluate whether Austin's Orca internal primitive composition can be matched by field-derived construction-circle overlap/count geometry without drawn final primitives or aperture masks as the main mechanism.

Reviewed source:

- Source artwork: `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
- Source SHA-256: `9608002e18224fe275059a7e4a9ef3d403eafc639a53afea5efc88929d9a6dcb`
- Placement transform: scale `0.88`, top-left `[896, 122]`, display size `[2219, 1949]` on a `3840x2160` canvas.
- Fit JSON: [orca_wave_interference_fit_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001.json)
- Debug folder: `track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22`

## Phase 1 - Fitting Method Research

### Circle / Oval Target

Method: measure the source component centroid, principal axis, major/minor extents, and aspect ratio. Near-circular targets use one construction circle with predicted primitive region `count >= 1`. Elongated ovals use a two-circle capsule approximation: two equal-radius construction circles placed along the major axis, with the primitive region as their union (`count >= 1`).

Path A assessment: circular wavefronts can approximate the Orca's ovoid anchors well enough for anchor reading, especially when the mark is broad and self-contained. Exact authored oval taper is not reproduced by one or two circles; more circular samples or a non-circular wavefront family would be needed for high-fidelity taper.

### Crescent / Vesica Target

Method: fit two construction circles whose intersection lens is the predicted primitive region (`count >= 2`). Parameterization uses two centers, equal radius, center separation, orientation of the lens major axis, and lens thickness/aspect ratio. The equal-circle vesica formula is initialized from target major length `L` and thickness `T`: `R = (L^2 + T^2) / (4T)` and `d = (L^2 - T^2) / (2T)`, then locally searched for better IoU.

Limit: this matches a symmetric lens. It does not naturally bend into a banana-shaped body band. Crescent-like body components can score as centered and oriented while still losing the authored curved-band character.

### Trigon / Three-Arc Target

Method: fit three construction circles and use their three-way overlap (`count >= 3`) as the predicted primitive region. The parameter search records three centers, radii, center-triangle side lengths, center-triangle orientation, overlap centroid, and concavity/orientation. The resulting trigon is a convex curved triangular cell from three arcs, not a drawn triangle.

Limit: organic pointed forms can be approximated if their centroid and tip direction are clear. Concave or highly asymmetric authored trigons remain difficult with only three equal-radius construction circles.

### Asymmetric Field Risks

- Spurious secondary features: unrelated construction circles overlap outside target masks and can create extra count regions that read as accidental marks.
- Noisy fields: fitting many local primitives independently increases the count-map density and weakens the causal read of a single wave field.
- Mathematical match versus perception: a target can have acceptable centroid error or IoU but still feel scattered if the global source configuration does not bind eye, body, dorsal, and tail into one composition.

## Phase 2 - Orca Primitive Target Extraction

| Candidate | Class | Source bbox px | Canvas centroid px | Decision | Notes |
|---|---|---:|---:|---|---|
| `eye_upper_pale_ovoid` | circle/oval | `[1329, 949, 1821, 1183]` | `[2266.312, 1049.763]` | fit attempted | Strongest authored oval anchor; acts as a head/eye patch focal mark. |
| `lower_large_pale_ovoid` | circle/oval | `[594, 1383, 884, 1921]` | `[1520.587, 1547.81]` | fit attempted | Large elongated pale anchor in the lower body cluster. |
| `lower_small_pale_ovoid` | circle/oval | `[420, 1284, 612, 1638]` | `[1342.251, 1388.051]` | fit attempted | Secondary pale oval anchor; useful for testing repeated oval fitting. |
| `dorsal_inner_trigon` | trigon / three-arc | `[904, 300, 1127, 580]` | `[1788.676, 536.934]` | fit attempted | Dorsal interior reads as a pointed three-arc/trigon-like pressure form. |
| `upper_body_bluegray_crescent` | crescent/lens | `[942, 574, 1564, 936]` | `[1978.879, 714.632]` | fit attempted | Broad upper body band; likely harder because it bends more than a pure vesica. |
| `central_pectoral_bluegray_crescent` | crescent/lens | `[832, 1117, 1599, 1553]` | `[1941.045, 1317.968]` | fit attempted | Largest internal body crescent candidate; may be compound but visually important. |
| `tail_fluke_bluegray_crescent` | crescent/lens | `[1700, 1645, 1878, 1755]` | `[2469.482, 1617.332]` | fit attempted | Compact tail-side crescent/lens with clear local curvature. |
| `tail_upper_bluegray_trigon` | trigon / three-arc | `[1402, 1622, 1691, 1809]` | `[2271.883, 1619.357]` | fit attempted | Tail-side pointed/three-arc candidate; tests whether the trigon fit generalizes beyond the dorsal. |
| `rear_vertical_bluegray_compound_exclude` | compound region to exclude | `[1812, 964, 1987, 1292]` | `[2566.094, 1135.335]` | excluded | Visually strong, but it merges multiple body/negative-space readings and is not a clean primitive target. |

The compound rear vertical component was intentionally excluded from fitting because it joins too many body and negative-space readings to be a clean primitive unit.

## Phase 3 - Construction-Circle Fit Attempt

| Candidate | Rule | Construction circle centers/radii in canvas px | Centroid error px | IoU | Quality | Character note |
|---|---|---|---:|---:|---|---|
| `eye_upper_pale_ovoid` | `count >= 1` | [2172.103, 1064.359] r=92.099<br>[2360.52, 1035.168] r=92.099 | 0.009 | 0.6664 | PASS | Predicted region is produced only by the union of circular wavefront disks. |
| `lower_large_pale_ovoid` | `count >= 1` | [1495.668, 1633.507] r=92.765<br>[1545.506, 1462.112] r=92.765 | 0.006 | 0.6606 | PASS | Predicted region is produced only by the union of circular wavefront disks. |
| `lower_small_pale_ovoid` | `count >= 1` | [1320.052, 1450.752] r=71.672<br>[1364.45, 1325.35] r=71.672 | 0.014 | 0.7891 | PASS | Predicted region is produced only by the union of circular wavefront disks. |
| `dorsal_inner_trigon` | `count >= 3` | [1784.815, 475.548] r=121.225<br>[1862.3, 571.522] r=121.225<br>[1719.964, 580.473] r=121.225 | 10.408 | 0.6323 | PASS | Predicted trigon is the three-way overlap of three construction circles, not a drawn triangle. |
| `upper_body_bluegray_crescent` | `count >= 2` | [1948.402, 604.326] r=224.487<br>[2009.355, 824.937] r=224.487 | 0.013 | 0.5848 | PASS | Two-circle vesica lens can match center, orientation, and broad thickness, but cannot bend into a true authored crescent band. |
| `central_pectoral_bluegray_crescent` | `count >= 2` | [2015.761, 1061.211] r=438.108<br>[1866.329, 1574.724] r=438.108 | 0.002 | 0.5501 | PASS | Two-circle vesica lens can match center, orientation, and broad thickness, but cannot bend into a true authored crescent band. |
| `tail_fluke_bluegray_crescent` | `count >= 2` | [2483.319, 1565.993] r=98.544<br>[2455.646, 1668.672] r=98.544 | 0.014 | 0.9263 | PASS | Two-circle vesica lens can match center, orientation, and broad thickness, but cannot bend into a true authored crescent band. |
| `tail_upper_bluegray_trigon` | `count >= 3` | [2263.392, 1603.814] r=93.323<br>[2342.739, 1595.716] r=93.323<br>[2317.86, 1662.079] r=93.323 | 34.334 | 0.4467 | PASS | Predicted trigon is the three-way overlap of three construction circles, not a drawn triangle. |
| `rear_vertical_bluegray_compound_exclude` | n/a | excluded compound region | n/a | n/a | EXCLUDE | Not fit as a primitive. |

Parameterization details are preserved in the JSON for each target, including lens separation/aspect ratio and trigon center-triangle geometry.

## Phase 4 - Field Coherence Evaluation

Debug stills only:

- [01 source targets marked](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_01_source_targets_marked.png)
- [02 fitted construction circles over Orca](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_02_fitted_construction_circles_over_orca.png)
- [03 primary overlap-count map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_03_overlap_count_map_primary_all_sources.png)
- [04 target-vs-predicted mismatch sheet](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_04_target_vs_predicted_mismatch_sheet.png)
- [05 alternative strong-target overlap-count map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_05_alt_overlap_count_map_strong_targets.png)
- [06 alternative body/tail overlap-count map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_research_scout_v001_2026-05-22/figural_orca_wave_interference_match_research_scout_v001_debug_06_alt_overlap_count_map_body_tail.png)

| Configuration | Source circles | Max count | Count>=2 area px | Spurious count>=2 components | Read |
|---|---:|---:|---:|---:|---|
| `primary_all_fit_sources` | 18 | 4 | 536544 | 17 | mixed |
| `alternative_strong_targets` | 11 | 4 | 446880 | 11 | mixed |
| `alternative_body_tail_subset` | 9 | 4 | 377168 | 11 | mixed |

The primary all-target count map demonstrates the core risk: local fits produce valid primitive cells, but the global count field adds many unrelated secondary overlaps. The strong-target subset reduces clutter but still reads as a constellation of local devices more than as one coherent Orca-bound wave system.

## Outcome

Go/no-go verdict: **MIXED**.

- Strong primitive targets matched: `8` PASS fits out of `8` fit attempts.
- Field read: `mixed: several local matches are defensible, but the asymmetric count field reads as a scattered constellation with spurious secondary overlaps`.
- Recommend proceeding to `figural_orca_wave_interference_match_v001` beauty render: `false`.

Recommendation: do not proceed directly to a beauty MP4. The scout supports the geometry hypothesis for several local primitives, especially ovoid anchors and compact tail/dorsal cells, but the asymmetric all-source field is visually mixed and too prone to secondary features. A next research pass should either bind the construction circles into fewer shared source families or combine this primitive matching with a silhouette/flow coherence layer before any render.

## Verification Notes

- All referenced paths were generated under the requested doc, JSON, and debug-output locations.
- JSON is intended to parse with `python3 -m json.tool`.
- Markdown links are repository-relative from this document.
- This scout writes PNG stills only and no MP4.
- The source PNG is read-only input and is not modified.
