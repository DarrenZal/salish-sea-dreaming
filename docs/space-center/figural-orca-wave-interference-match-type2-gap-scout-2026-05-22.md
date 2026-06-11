# Figural Orca Wave-Interference Type 2 Gap/Cup Scout - 2026-05-22

Status: INTERNAL RESEARCH + GEOMETRY-FIT SCOUT ONLY. No MP4 was rendered and the source artwork was not modified.

Purpose: continue `figural_orca_wave_interference_match_research_scout_v001` by comparing Type 1 overlap geometry against Type 2 gap/cup geometry for Orca internal primitives.

Reviewed source and baseline:

- Source artwork: `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
- Placement transform: scale `0.88`, top-left `[896, 122]`, display size `[2219, 1949]`.
- Baseline Type 1 JSON: [orca_wave_interference_fit_candidates_v001.json](../../track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001.json)
- Updated Type 2 JSON: [orca_wave_interference_fit_candidates_v001_1_type2_gap.json](../../track2-deterministic/anchor_graph/orca_wave_interference_fit_candidates_v001_1_type2_gap.json)
- Debug folder: `track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22`

## Geometry Tested

Type 1 baseline keeps the v001 definitions: ovals are `count >= 1`, crescents are two-circle overlap lenses, and trigons are three-circle overlap cells.

Type 2 definitions:

- Crescent/cup: predicted region is `inside outer circle AND outside cutter circle`, creating a cupped two-arc region with sharper cusp behavior than a symmetric vesica.
- Trigon/gap: predicted region is the bounded complement component outside the union of three nearby construction circles. This makes the sides arc outward away from the trigon interior instead of forming an inward overlap cell.
- Circle/oval targets are retained as controls because gap/cup logic is not the relevant primitive family for those anchors.

## Type 1 vs Type 2 Comparison

| Candidate | Class | Type 1 IoU / err | Type 2 IoU / err | Orientation err | Type 2 quality | Delta | Character verdict |
|---|---|---:|---:|---:|---|---|---|
| `eye_upper_pale_ovoid` | circle/oval | 0.6664 / 0.009 | 0.6664 / 0.009 | 0.013 | PASS | similar | control: circle/oval anchor remains a Type 1 control |
| `lower_large_pale_ovoid` | circle/oval | 0.6606 / 0.006 | 0.6606 / 0.006 | 0.003 | PASS | similar | control: circle/oval anchor remains a Type 1 control |
| `lower_small_pale_ovoid` | circle/oval | 0.7891 / 0.014 | 0.7891 / 0.014 | 0.011 | PASS | similar | control: circle/oval anchor remains a Type 1 control |
| `dorsal_inner_trigon` | trigon / three-arc | 0.6323 / 10.408 | 0.0857 / 12.466 | 88.753 | FAIL | worse | focus: outward gap trigon bounded by nearby arcs |
| `upper_body_bluegray_crescent` | crescent/lens | 0.5848 / 0.013 | 0.4432 / 36.636 | 0.019 | MIXED | worse | focus: cup-shaped arc difference rather than overlap lens |
| `central_pectoral_bluegray_crescent` | crescent/lens | 0.5501 / 0.002 | 0.4396 / 70.666 | 0.0 | MIXED | worse | focus: cup-shaped arc difference rather than overlap lens |
| `tail_fluke_bluegray_crescent` | crescent/lens | 0.9263 / 0.014 | 0.6457 / 15.099 | 0.026 | PASS | worse | focus: cup-shaped arc difference rather than overlap lens |
| `tail_upper_bluegray_trigon` | trigon / three-arc | 0.4467 / 34.334 | 0.0477 / 13.98 | 48.059 | FAIL | worse | focus: outward gap trigon bounded by nearby arcs |

## Focus-Target Read

Across the five requested focus targets, Type 2 is better on `0`, worse on `5`, and mixed/similar on `0`.

- The cup model is conceptually closer to cupped crescents because it produces one filled side and one cutting arc rather than a symmetric lens, but the tested fits overgrow the body bands.
- The dorsal and tail trigon gap model expresses the correct outward-arc idea, but the bounded complement regions do not match the authored trigon masks.
- In this deterministic scout, Type 2 is a useful grammar hypothesis but not a material fit improvement over Type 1.

## Debug Stills

- [source targets marked](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_01_source_targets_marked.png)
- [type1 fits over source](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_02_type1_fits_over_source.png)
- [type2 fits over source](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_03_type2_fits_over_source.png)
- [type1 vs type2 mismatch sheet](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_04_type1_vs_type2_mismatch_sheet.png)
- [type2 gap cup detection map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_05_type2_gap_cup_detection_map.png)
- [combined type2 coherence map](../../track2-deterministic/morph_outputs_INTERNAL/figural_orca_wave_interference_match_type2_gap_scout_v001_2026-05-22/figural_orca_wave_interference_match_type2_gap_scout_v001_debug_06_combined_type2_coherence_map.png)

## Global Field Coherence

- Type 1 background source circles: `18`
- Type 1 background max overlap count: `4`
- Type 2 union area: `656176` px
- Type 2 off-target area: `373314` px
- Type 2 off-target components >= 1200 px: `16`

Type 2 cup/gap regions remain visually separable from the Type 1 overlap background, but they do not stay clean enough to rescue field coherence. The global arrangement still reads as a cluster of independently fitted local constructions, with large off-target regions and failed trigon gap cells.

## Outcome

Go/no-go verdict: **NO-GO**.

- Recommendation for direct `figural_orca_wave_interference_match_v001` beauty render: `false`.
- Rationale: Type 2 did not materially improve the requested focus targets and global field coherence remains scattered.

Recommended next move: do not render a direct beauty pass from this architecture. Keep Type 2 gap/cup geometry as a future grammar thread, but it needs a better bounded-gap construction and a shared source-family or silhouette/flow layer before it can carry the Orca composition.

## Verification Notes

- JSON parses with `python3 -m json.tool`.
- Markdown links are repository-relative from this document.
- Output folder contains PNG stills only.
- Source PNG SHA-256 matches the baseline source hash.
