# Triptych Show Integration Board — 2026-05-14

Purpose: map the ready technical surfaces into the actual three-projector show so Day 4 work does not fragment into unrelated scripts.

Status: working integration plan. Public/aesthetic content remains subject to Austin approval.

## Core Thesis

One continuous pearl interior, seen through three projector windows:

| Panel | Role | Primary content | Approval posture |
|---|---|---|---|
| Left | Lens / Western science | tide, Fraser flow, underwater footage, iNat/science texture if used | low cultural risk if framed as physical signal |
| Center | Lineage / Coast Salish design | Austin-approved Thunderbird / three shapes / Track 2 morphs | highest approval requirement |
| Right | Water / Bioregion | underwater footage, particle current, river-to-sea mixing, atmospheric style layer if approved | low-to-medium risk depending on style layer |

The three panels should feel like one shared volume, not three unrelated videos. Render / author as a single wide or spherical scene where possible, then slice into panels.

## Layer Stack

| Layer | Panel emphasis | Source | Current status | Fallback if blocked |
|---|---|---|---|---|
| Pearl interior background | all panels | `austin-reference/pearl-triptych-mock/` recipe; future TD/Blender scene | mock proven, production scene pending 3090/TD | use pre-rendered nacre/particle background from PIL mock |
| Particle current / breath | all panels | TD particles or pre-rendered `compose_pearl_dry_run.py` concept | dry-run proof only | non-cultural abstract particles / gradients |
| Live tide + Fraser modulation | left + right, subtle center | `scripts/bioregional_osc_bridge.py` + TD callback | endpoint + local OSC test passed; live TD hookup pending | use cached values or slow synthetic breath if API unavailable |
| Underwater footage | left + right | `media/hero-subclips/` and `output/temporal-style-smoke-2026-05-13/inputs/` | available now | raw footage without style transfer |
| Austin-approved primitives | center | Austin Drive + Track 2 decomposition | pending Drive + Austin review | no symbolic foreground; keep center quiet |
| Track 2 morphs | center, occasional side echo | `track2-deterministic/` | dry-run engine ready; real source pending | static approved stills / no morph |
| v2 LoRA style layer | left/right atmospheric only unless explicitly approved | `scripts/eval_lora.py`, `scripts/run_temporal_style_smoke.py` | pending Drive + v2 still gate | raw underwater footage / non-AI color treatment |
| Visitor / interaction layer | secondary for May unless tracking scope reopens | existing visitor app / MediaPipe history | not active in current Day 3 plan | static transit-audience loop |

## Asset Board

| Asset / source | Use | Ready? | Notes |
|---|---|---:|---|
| `media/hero-subclips/H2_herring_in_kelp.mp4` | left/right underwater structure; temporal smoke input | yes | best fish/kelp structure candidate |
| `media/hero-subclips/H5_reef_garden.mp4` | reef texture / complexity test | yes | temporal smoke variant C |
| `media/hero-subclips/H8_milky_water.mp4` | pearl-water atmosphere | yes | temporal smoke variant D |
| `output/temporal-style-smoke-2026-05-13/inputs/` | 5s 720p smoke inputs | yes | upload only after v2 still gate passes |
| `austin-reference/pearl-triptych-mock/` | composition proof, not artwork | yes | no Austin motifs |
| `track2-deterministic/morph_outputs/` | dry-run proof | dev only | do not show as Austin preview |
| `austin-reference/john-projector-test-pack-v1_2026-05-13.zip` | John projector technical stress test | ready | not show content |
| `austin-v2-ingest/` | v2 source ingestion | ready, empty | wait for Drive |

## Seven-Minute Breath Cycle Sketch

| Time | Dramaturgy | Technical layer emphasis |
|---:|---|---|
| 0:00-0:45 | Arrival / water-dark interior | pearl background, low particle current, underwater footage low opacity |
| 0:45-1:45 | Lens opens | left panel tide/Fraser modulation, footage becomes legible |
| 1:45-3:00 | Pearl gathers | particle current crosses all panels, center begins to brighten |
| 3:00-4:30 | Lineage / teaching center | Austin-approved center forms / Track 2 morphs; side panels quiet |
| 4:30-5:45 | Water carries outward | right panel water-memory motion, particle release |
| 5:45-6:45 | Dissolve / exhale | forms settle, footage softens, tide-rate bias controls breath direction |
| 6:45-7:00 | Loop seam | low-information near-black / nacre stillness; no symbolic seam crossing |

Rules:

- Symbolic content lives mostly in center during high-information moments.
- Side panels can carry atmosphere and physical-system signals; they should not compete with Austin-approved forms.
- Seam zones stay low-detail: background, particles, and water only.

## Live Data Mapping

| OSC value | Visual parameter | Panel | Smoothing |
|---|---|---|---|
| `bio_tide_level_m` | waterline / horizon height / pearl interior brightness | left + all | slow lag, 60-120s |
| `bio_tide_rate_mph` | inhale/exhale bias, particle current direction | all | slow lag, clamp extremes |
| `bio_tide_next_hilo_seconds` | gathering vs release phase bias | all | map to broad cycle, not literal countdown |
| `bio_fraser_discharge_cms` | particle density / river-to-sea mixing amount | right | very slow lag |
| `bio_cache_used` | hidden operator indicator only | none public | do not visibly signal outage |

## Approval Gates By Layer

| Layer | Can build now? | Can show internally? | Can ship? |
|---|---|---|---|
| raw underwater footage | yes | yes, subject to Moonfish reuse confirmation | after reuse terms confirmed |
| tide / Fraser data modulation | yes | yes | yes if framed as physical-system signal |
| pearl background / abstract particles | yes | yes | yes if no Austin/cultural claims attached |
| Austin source forms | after Drive | yes after Austin source scope OK | only after per-output OK |
| Track 2 morphs | after vectors | Austin review only | only after primitive + morph + render OK |
| v2 LoRA outputs | after Drive + train | only if useful and clearly labeled | only after per-output OK |
| public language | drafted | Austin/Indigenomics/Pravin review | only after approval rows updated |

## Resolume / TD Handoff Shape

Minimum viable show package for May:

```text
resolume/
  panel_L_background_or_footage.mov
  panel_C_lineage_or_pearl.mov
  panel_R_water_or_footage.mov
  synthetic_projector_test_4k.png
  README_install_notes.txt
```

Preferred show package if 3090/TD returns:

```text
TD scene -> 3 Render TOPs or pre-rendered panel clips
bioregional_osc_bridge.py -> OSC port 7001 -> TD callback -> smoothed CHOP params
Resolume Arena -> Advanced Output -> 3 projectors @ 1080p
```

Open output-path issue:

- Autolume upstream does not prove NDI/Spout.
- April archive proves a local `visualizer.py` patch existed, but the patched file is not recovered yet.
- Do not promise NDI or Spout until the 3090 install confirms the actual mechanism.

## Day 4 Build Priorities From This Board

If Austin Drive lands:

1. v2 ingest/train/eval.
2. Identify first center-panel source candidates.
3. Begin Track 2 decomposition only for Austin-approved or review-candidate pieces.

If Austin Drive does not land:

1. No more stale-data model work.
2. Improve the abstract pearl background / footage assembly path.
3. Prepare Resolume packaging notes for the John/venue test.

If 3090 returns:

1. Verify TD can receive the live feed.
2. Verify Autolume output mechanism.
3. Build a bare pearl scene with three cameras and no Austin motifs.
