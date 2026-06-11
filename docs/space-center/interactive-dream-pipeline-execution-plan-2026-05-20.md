# Interactive Dream Pipeline — Execution Plan — 2026-05-20

Status: INTERNAL execution plan. No rendering was performed by this document.
Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim. Not
a general Coast Salish grammar claim.

> **Update 2026-05-20 (executed):** WS-1, WS-2, and WS-3 have been run —
> Pipeline A (R1 scene-graph + R2 scalar-field/cymatics) is built and verified:
> 25 comparison stills, Gate 0 25/25, 93 tests. See the result record
> `interactive-dream-pipeline-a-result-2026-05-20.md`. The diffusion lanes
> (Pipelines B/C) and WS-4 GPU verification remain optional and are not built.

This document turns the existing interactive-dream planning docs into a
concrete, ordered execution plan for visitor-prompt-generated visuals. It is the
companion to the comparison plan; the comparison plan defines *what the
experiment is*, this document defines *what to build first, in what order, by
whom, and how to know it passed*.

## Purpose

Broad Austin-style LoRA / style-transfer was dropped as unsafe and unreliable.
The next direction is a **deterministic scene-graph renderer** driven by a
provenance-tagged scene-plan JSON, with diffusion demoted to an optional async
experimental lane. This plan answers the ten execution questions and ends with a
copy-paste prompt for the first dev worker.

## Inputs read

- `docs/space-center/interactive-dream-pipeline-comparison-plan-2026-05-20.md` — experiment design, scene-plan schema v001 draft, 5 test prompts, scoring rubric, GPU-verification checklist, first build order, stop conditions.
- `track2-deterministic/primitive_grammar/dream_grammar_provenance_v001.yaml` — shared grammar/provenance file (shape vocabulary, grammar rules, subject mappings, forbidden/paused areas, Austin questions). **Exists on disk** (created 2026-05-20).
- `docs/space-center/dream-grammar-provenance-2026-05-20.md` — human companion to the YAML.
- `docs/space-center/primitive-pattern-language-canon-2026-05-20.md` — morphology classes, valid adjacency, motion semantics, 5-lane canon, failure-derived do-not-do list.
- `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md` — live runtime path, prompt-mapping table, top-8 templates, latency/fallback ladder, compact scene-command schema.
- `docs/space-center/water-cycle-cymatic-primitive-scene-language-2026-05-20.md` — water-cycle state machine (rain → radial wave → snowflake → cloud → sun), render recipes.
- `docs/space-center/interference-field-cell-taxonomy-2026-05-20.md` — Agent E spec for scalar-field cell classification, debug overlay requirements.

Also checked: canonical plan `~/.claude/plans/ok-so-i-polymorphic-melody.md`, `CURRENT_STATE.md`, and on-disk assets under `track2-deterministic/`.

## Framing reconciliation — read this before anything else

Three points the source docs leave implicit:

1. **This is R&D, not an IMPACT show surface.** The newest governing doc (the
   2026-05-20 comparison plan) reframes the whole dream pipeline as an
   *internal controlled experiment* that "should not run" until shared grammar +
   schema + validated scene plans + a blocked-subject checker exist. The
   visitor-prompt loop is **not** lit for IMPACT (May 27–28). Treat the live
   architecture as a horizon target (MOVE37XR-era), and treat the deterministic
   ambient fallback as the only thing genuinely live-safe at IMPACT.

2. **Two schemas exist; both are correct, at different layers.** The comparison
   plan's `interactive_dream_scene_plan_v001` is the *rich authoring/experiment
   plan* — provenance-tagged, reviewed offline, what the experiment and Austin
   review consume. The architecture doc's `dream_scene_command.v1` is the
   *compact live-runtime command* — enum-bounded, derived from a chosen template.
   The experiment needs only the rich scene plan. The compact command matters
   only when/if the live loop is lit. In **both** cases the renderer receives
   bounded structured data, never raw visitor text.

3. **Renderers are mostly built already.** A scalar-field/cymatics renderer
   exists at v002-era (`scripts/cymatic_field_topology_v003.py`,
   `scripts/primitive_standing_wave_field_v002.py`, `scripts/cymatic_topology_cells_v004.py`,
   `scripts/cymatic_standing_wave_phase_inversion_v002.py`,
   `scripts/cymatic_radiant_water_geometry_v001.py`). A generator-based recipe
   renderer exists for the *old* untagged format
   (`track2-deterministic/scripts/render_primitive_scene_recipe.py` consuming
   `track2-deterministic/scene_recipes/*.json`). The net-new work is a
   **provenance-tagged scene-plan schema and a renderer that consumes it** — it
   may lift drawing code from the existing renderers; it does not start from zero.

## 0. Decisions at a glance

| # | Question | One-line answer |
|---|---|---|
| 1 | MVP live-safe visitor path | `prompt → local safety filter → rule classifier → bounded template_id → pre-rendered Austin-reviewed clip`. Not lit for IMPACT; IMPACT runs operator-triggered deterministic ambient only. |
| 2 | First executable prototype | The contract slice: one hand-authored scene plan → validator → Pipeline A renderer → one PNG + debug overlay + manifest. First *prompt-complete* still = Pipeline A / P04 / seed 1001. |
| 3 | Renderer split | Two deterministic renderers sharing one schema + draw layer: **R1** scene-graph (path/mask/flock/school/weather_transition), **R2** scalar-field/cymatics (scalar_field/contour_field/topology_cell_field). R2 already exists; adapt it. |
| 4 | 5 prompts → scene-plan JSON | Each prompt maps to grammar `subject_mappings` → entities + structures (typed → routed to R1 or R2) + primitive_phrases, every element provenance-tagged. P04 fully worked below. |
| 5 | CPU-only now | All of Pipeline A (R1 + R2), Pipeline B's procedural pre-finish, Pipeline C's edge-extraction tooling on fixtures, plus schema/validator/checker/manifest/scoring. |
| 6 | Needs GPU verification first | Only diffusion: Pipeline B's finisher and Pipeline C's source image. Run the no-render GPU verification checklist before either. |
| 7 | Parked until Austin reviews | The visitor→renderer connection, all figure-body depiction, public sun/snow/cloud grammar, all diffusion output, Pipeline C. Separately *blocked*: named beings, exact-source replication, "Austin style". |
| 8 | Workstreams next | WS-1 schema+validation, WS-2 R1 renderer, WS-3 R2 schema adapter, WS-4 GPU verification (no render), WS-5 scoring/review packet. |
| 9 | Pass/fail rubric | Hard binary gates (provenance, blocked-subject, reproducibility, manifest) then the 6-dimension 0–3 score; PASS = all gates + provenance 3 + safety ≥2 + reproducibility ≥2 + total ≥12/18. |
| 10 | First worker's files | A new `track2-deterministic/interactive_dream/` package: schema, validator, normalizer, blocked checker, grammar loader, primitive-draw layer, R1 renderer, manifest/overlay, 5 scene plans, tests. |

---

## 1. MVP live-safe visitor dream path

The architectural path, from `interactive-dream-to-primitive-architecture-2026-05-19.md`:

```text
visitor prompt (web app)
  → local safety keyword filter        (runs locally, first, before anything)
  → local rule-based intent classifier (keyword → template_id enum)
  → bounded scene command              (dream_scene_command.v1: template_id +
                                        seed + numeric params; NO raw text)
  → pre-rendered Austin-reviewed clip   (Resolume clip trigger, 0.2–1.0 s)
  → screen-blend over fallback ambient media
  → operator kill switch + per-scene dwell cap
```

The deterministic primitive renderer (Pipeline A) is the **Mode B fallback**
(0.5–3 s) for a template that has no pre-rendered clip. It receives only the
enum `template_id` + numeric params — never raw prompt text.

**This path is not lit for IMPACT, for two reasons:**

- The schema, validated scene plans, and blocked-subject checker do not exist
  yet (grammar v001 does). The comparison plan explicitly blocks the experiment
  — and therefore the live loop — until they land.
- Every clip in the pre-rendered library needs per-output Austin review (the
  consent floor). No reviewed clip library exists.

So the MVP splits:

| Tier | What it is | Live-safe when | Status |
|---|---|---|---|
| **MVP-A** (architecture target) | The full path above, visitor prompt → reviewed clip | After the experiment lands a reviewed template/clip set **and** Austin signs off per-output **and** approves the visitor-prompt connection itself | Horizon (MOVE37XR-era), parked |
| **MVP-B** (live-safe now) | Operator-triggered deterministic ambient water-state templates (ripple / mist / clean water / current); **no visitor text reaches any renderer**; no public claim of Austin authorship | After each ambient clip has per-output Austin review | The only candidate for IMPACT |

**Recommendation:** treat the visitor-prompt loop as parked for IMPACT. Build
the experiment now so the loop can be lit at the next venue. For IMPACT itself,
the live-safe surface is MVP-B: operator-driven deterministic ambient, kill
switch, screen-blend on black, and even those clips reviewed per-output.

Least-privilege invariants that make the path safe and must hold at every tier:
the renderer never sees free text; the visitor never sees un-reviewed output;
the operator can always mute the whole layer.

## 2. First executable prototype

The first executable prototype is **not** a full prompt-to-still. It is the
**vertical contract slice** that proves the schema end-to-end:

```text
hand-authored scene_plan.json  (schema-valid, one water phrase, seed 1001)
  → validate_scene_plan.py     (passes; provenance resolves)
  → render_pipeline_a.py (R1)  → final_1920x1080_srgb.png
                               + debug_overlay_1920x1080_srgb.png
  → manifest.py                → manifest.json + grammar_provenance_report.json
```

The scene plan contains exactly one water phrase
(`circle-like origin → crescent-like → crescent-like → curved trigon`) on a
black canvas. No prompt parsing, no cymatics, no diffusion. It proves: the schema
validates, every grammar atom reference resolves to `dream_grammar_provenance_v001.yaml`,
the renderer is deterministic (re-run → identical SHA256), the manifest captures
everything, and the debug overlay shows phrase IDs + provenance kinds.

**First prompt-complete still:** Pipeline A / **P04 `rain becoming snow on a
mountain`** / seed 1001 — per the comparison plan's first-build-order. P04 is
the safest test prompt (weather/environment, no human, no named being). Its
snow/radial portion is rendered in **layout-only** form by R1 first (authored
sparse radial cells, manifest flag `cymatics: deferred`); R2 swaps in on a
second pass. **P03 `salmon swimming up a river`** follows as the first
water + motion stress test.

Why the contract slice before P04: P04 done *properly* needs R2 (a six-ray
snowflake is a scalar field). De-risk the schema and R1 with a one-phrase render
before adding renderer complexity.

## 3. Renderer split — scalar-field/cymatics vs scene/figure renderer

There are **two deterministic renderers**. They share the scene-plan JSON
contract, the grammar file, and one common primitive-drawing / canvas layer.
They differ only in *how primitive placements are derived*.

```text
                 ┌─────────────────────────────────────────┐
  scene_plan.json│  structures[]  (typed)                   │
  (validated)    │     path / mask / flock / school /       │──▶ R1  scene-graph
                 │       weather_transition                 │     primitive renderer
                 │     scalar_field / contour_field /        │──▶ R2  scalar-field /
                 │       topology_cell_field                 │     cymatics renderer
                 └─────────────────────────────────────────┘
                                   │
                R2 emits classified cells back as primitive instances
                                   ▼
                 ┌─────────────────────────────────────────┐
                 │  shared primitive-draw layer (one canvas)│──▶ final PNG
                 │  circle / crescent / trigon / oval /      │──▶ debug overlay
                 │  line / mask  +  deterministic seeding    │──▶ manifest
                 └─────────────────────────────────────────┘
```

**R1 — scene-graph primitive renderer** (the "scene/figure renderer"; Pipeline A core)

- Consumes `structures` of type `path`, `mask`, `flock`, `school`, `weather_transition`.
- Places `primitive_phrases` by **authored layout rules**: along a path tangent,
  around a declared origin, inside a mask, sparse at bends/impacts.
- Handles: orca breach path, salmon school path, river axis, bird flock path,
  mountain/shoreline masks, weather-transition bands, authored rain impacts.
- CPU-only — PIL + numpy (both installed). New file: `render_pipeline_a.py`.
  May lift drawing code from `track2-deterministic/scripts/render_primitive_scene_recipe.py`.

**R2 — scalar-field / cymatics renderer** (the "scalar-field/cymatics renderer")

- Consumes `structures` of type `scalar_field`, `contour_field`, `topology_cell_field`.
- Builds a stable normalized field `F(x,y)`, classifies connected-component
  cells per `interference-field-cell-taxonomy-2026-05-20.md` (positive/negative
  phase cells, nodal boundaries, radial source rings, interference-lens
  crescents, multi-source trigon scallops, six-ray snowflake/sun candidates),
  emits each cell with a renderer-facing `topology_class` ∈ {circle, crescent,
  trigon, outline, compound}.
- Handles: standing-wave water interference, radial water wave, six-ray
  snowflake, sun/radiant field, mist drift networks — the water-cycle states.
- **Already exists** at v002-era: `scripts/cymatic_field_topology_v003.py`,
  `scripts/primitive_standing_wave_field_v002.py`, `scripts/cymatic_topology_cells_v004.py`,
  `scripts/cymatic_standing_wave_phase_inversion_v002.py`,
  `scripts/cymatic_radiant_water_geometry_v001.py`. R2 work = a **schema adapter**
  that lets these consume scene-plan `scalar_field`/`topology_cell_field`
  structures and emit provenance-tagged cells. CPU-only — numpy + scipy + opencv
  (scipy/opencv to be confirmed by the worker; classify from stable `F(x,y)`,
  never from animated `Z(x,y,t)`).

**Integration rule — R2 is a structure provider to the shared draw layer.** A
`scalar_field` / `topology_cell_field` structure in a scene plan is realized by
R2 into a set of classified cells; those cells become primitive instances drawn
by the **same draw layer** R1 uses. A single scene (e.g. P04) mixes R1-authored
mountain mask + rain impacts + transition band **and** R2-extracted snowflake
radial cells: one compositor, one canvas, one manifest. The debug overlay tags
each primitive with its renderer of origin.

**Pipeline mapping:**

- Pipeline **A** = R1 + R2, both deterministic, no diffusion. The comparison plan's "deterministic primitive renderer."
- Pipeline **B** = R1/R2 procedural pre-finish (CPU) → diffusion finisher (GPU). Only the finisher is GPU.
- Pipeline **C** = diffusion source image (GPU) → opencv edge/contour extraction → cleanup mapped back to grammar. Extraction can run CPU on fixtures.

Per-prompt renderer use:

| Prompt | R1 (scene-graph) | R2 (scalar-field/cymatics) |
|---|---|---|
| P01 orca breaching | breach path, water-sheet mask, spray, silhouette-safe mass | — (optional: wake interference) |
| P02 children on beach | shoreline mask, wave-edge crescents (environment only) | — |
| P03 salmon up a river | river axis path, water band mask, school path, sparse phrases | — (optional: eddy interference at bends) |
| P04 rain → snow on a mountain | mountain mask, rain impacts, weather-transition band | **snow six-ray harmonic cells** |
| P05 birds flocking at sunset | flock path, sky-gradient mask | **sun radiant field** (optional; or authored attached-radial in R1) |

## 4. The five test prompts → scene-plan JSON

Every prompt maps through the grammar YAML's `subject_mappings`. The mapping is
mechanical: subject → `phrase_templates` → `primitive_order`; subject status →
`safety.lane_status` + `blocked_subjects`; every entity / structure / phrase
carries `provenance_refs` pointing at grammar atom IDs. The validator rejects any
untagged element.

| Prompt | Grammar subject(s) | Phrase template(s) | Structures (type → renderer) | Lane status | Key blocked subjects |
|---|---|---|---|---|---|
| **P01** `orca breaching` | `orca_whale` | `orca_whale.breach_water_event` `[line/path, smooth mass, crescent-like, curved trigon]` | breach_path (`path`→R1), water_sheet (`mask`→R1), spray (`path`→R1) | internal_only | orca face/eye/teeth, species markings, exact Austin orca source |
| **P02** `children playing on the beach` | `human_figures` + `beach` | `beach.shoreline_boundary` `[smooth mass, line/path, crescent-like]`; humans → `human.non_identifiable_schema_placeholder` marked `safety_status: blocked` | shoreline_mask (`mask`→R1), wave_edge (`path`→R1); human entities recorded, **not drawn** | **blocked** (figures) / internal_only (environment) | identifiable children, faces, bodies, named people |
| **P03** `salmon swimming up a river` | `river` + `salmon_fish` | `river.s_curve_current` `[line/path, circle-like, crescent-like, S-crescent, curved trigon]` + `fish.motion_field_without_body` `[line/path, crescent-like, S-crescent, curved trigon]` | river_axis (`path`→R1), water_band (`mask`→R1), school_path (`school`→R1) | internal_only | static Austin-like salmon replica, two-fish rotational comp, roe field, fish body/eye detail |
| **P04** `rain becoming snow on a mountain` | `rain` + `snow` + terrain | `rain.sparse_impact_phrase` `[circle-like, crescent-like, curved trigon]` + `snow.attached_harmonic_cells` `[circle-like, crescent-like, curved trigon]` | mountain_mask (`mask`→R1), rain_to_snow_transition (`weather_transition`→R1), snow_radial_field (`topology_cell_field`→**R2**) | internal_only | sacred-geometry framing, mandala lattice, detached sun rays |
| **P05** `birds flocking at sunset` | `birds` + `sun` | `birds.flock_path` `[line/path, crescent-like, curved trigon]` + `sun.attached_radial_field` `[circle-like, crescent-like, curved trigon]` | sky_gradient (`mask`→R1), flock_path (`flock`→R1), sun_radiant (`scalar_field`→R2, optional) | internal_only | raven silhouette, beak/eye/wing detail, bird-in-front-of-sun public comp, Raven Sun transition |

**P02 handling is deliberate:** P02's `scene_plan.json` is authored and validated,
but human entities carry `safety_status: blocked` so the renderer **emits the
beach environment and draws nothing for the figures**. The manifest records P02
as `human_figures: blocked, rendered_environment_only`. P02 stays schema-only /
environment-only until Austin resolves grammar question `human_beach_prompts`.

### Schema reconciliation notes (WS-1 must resolve and document)

1. **Provenance-kind mapping.** The schema's `provenance_ref.kind` enum is
   `{austin_taught, inferred, needs_review, blocked}` (4 coarse values, one per
   ref). The grammar YAML's `source_tag_vocabulary` is `{Austin_taught,
   Austin_artwork_observed, Darren_inferred, needs_Austin_review}` and atoms
   carry a *list* of tags. WS-1 defines the mapping in `grammar_loader.py`:
   recommended `Austin_taught→austin_taught`, `Austin_artwork_observed→austin_taught`
   (reference-only; carries the no-copy constraint via `safety`),
   `Darren_inferred→inferred`, `needs_Austin_review→needs_review`; a `blocked`
   safety on the atom → `kind: blocked`. `review_status` is derived
   (`needs_Austin_review` present → `austin_review_needed`; blocked safety →
   `blocked`).
2. **Coordinate convention.** The schema's `bounds_norm` / `control_points_norm`
   define no convention. `grammar_v001.json`'s `interop_contract` uses
   center-origin, x/y ∈ [-1,1], +y up. WS-1 picks one convention, documents it
   in the schema `$comment` and the README, and authors all 5 scene plans
   consistently. Recommend matching `grammar_v001.json` for cross-tool
   consistency.
3. **Old recipe format is superseded for the experiment.** The 4 existing
   `track2-deterministic/scene_recipes/*.json` files (generator-based, no
   provenance) are reference only. The comparison runs on the new
   `interactive_dream_scene_plan_v001` schema. The new `render_pipeline_a.py`
   may reuse drawing code from `render_primitive_scene_recipe.py` but consumes
   the new schema.

### Worked example — P04 scene plan

Illustrative skeleton for `scene_plans/P04_rain_becoming_snow_on_a_mountain.json`.
**WS-1 has since landed the authoritative authored plans** at
`track2-deterministic/interactive_dream/scene_plans/` (see that package's
`RUN_NOTES.md`) — defer to those. Two points the skeleton shows loosely and the
authored plan pins exactly: `bounds_norm` is center-origin normalized space
(`[x_min, y_min, x_max, y_max]`, x/y ∈ [-1, 1], +y up); and every
`provenance_ref` `kind` / `review_status` is **derived from the grammar, not
author-chosen** — in `dream_grammar_provenance_v001` every atom resolves to
`needs_review` / `austin_review_needed`, so the `austin_taught` / `inferred`
values shown below are placeholders the validator would reject. `grammar_hash`
is filled by tooling.

```json
{
  "schema_version": "interactive_dream_scene_plan_v001",
  "scene_id": "p04_rain_becoming_snow_on_a_mountain",
  "prompt": {
    "prompt_id": "P04",
    "raw_text": "rain becoming snow on a mountain",
    "normalized_text": "rain becoming snow on a mountain",
    "notes": "Safest test prompt: weather/environment, no human, no named being."
  },
  "safety": {
    "lane_status": "internal_only",
    "public_use": "blocked_until_exact_output_review",
    "requires_austin_review": true,
    "blocked_subjects": ["sacred_geometry_framing", "mandala_lattice", "detached_sun_rays", "exact_austin_source"],
    "review_questions": [
      "Can rain-to-snow use sparse attached radial/harmonic cells without reading as sacred geometry? (grammar gap: snow_radial_topology)"
    ]
  },
  "canvas": { "width": 1920, "height": 1080, "color_space": "sRGB", "background": "black" },
  "grammar_context": {
    "grammar_file": "track2-deterministic/primitive_grammar/dream_grammar_provenance_v001.yaml",
    "grammar_version": "dream_grammar_provenance_v001",
    "grammar_hash": "<sha256-filled-by-tooling>",
    "provenance_policy": "all_referenced_atoms_must_have_provenance"
  },
  "entities": [
    { "id": "mountain", "label": "mountain mass", "entity_type": "terrain", "safety_status": "internal",
      "bounds_norm": [0.20, 0.30, 0.80, 1.00],
      "provenance_refs": [ { "grammar_atom_id": "smooth_mass", "kind": "inferred", "review_status": "austin_review_needed" } ] },
    { "id": "rain", "label": "rain", "entity_type": "weather", "safety_status": "internal",
      "bounds_norm": [0.00, 0.45, 1.00, 1.00],
      "provenance_refs": [ { "grammar_atom_id": "rain.sparse_impact_phrase", "kind": "austin_taught", "review_status": "austin_review_needed" } ] },
    { "id": "snow", "label": "snow", "entity_type": "weather", "safety_status": "austin_review_needed",
      "bounds_norm": [0.00, 0.00, 1.00, 0.55],
      "provenance_refs": [ { "grammar_atom_id": "snow.attached_harmonic_cells", "kind": "needs_review", "review_status": "austin_review_needed" } ] }
  ],
  "structures": [
    { "id": "mountain_mask", "structure_type": "mask", "role": "terrain_container", "entity_refs": ["mountain"],
      "provenance_refs": [ { "grammar_atom_id": "phrase.boundary_discipline.v001", "kind": "inferred", "review_status": "austin_review_needed" } ] },
    { "id": "rain_to_snow_transition", "structure_type": "weather_transition", "role": "altitude_band_rain_to_snow", "entity_refs": ["rain", "snow"],
      "provenance_refs": [ { "grammar_atom_id": "phrase.sparse_water_fields.v001", "kind": "inferred", "review_status": "austin_review_needed" } ] },
    { "id": "snow_radial_field", "structure_type": "topology_cell_field", "role": "six_ray_snow_harmonic_cells", "entity_refs": ["snow"],
      "provenance_refs": [ { "grammar_atom_id": "snow.attached_harmonic_cells", "kind": "needs_review", "review_status": "austin_review_needed" } ] }
  ],
  "primitive_phrases": [
    { "id": "rain_impact_phrase_01", "role": "rain_impact_release", "entity_refs": ["rain"], "structure_refs": ["rain_to_snow_transition"],
      "primitive_order": ["circle", "crescent", "trigon"], "placement_rule": "sparse_drop_impacts_lower_altitude_band",
      "provenance_refs": [ { "grammar_atom_id": "phrase.water_origin_phase_release.v001", "kind": "austin_taught", "review_status": "austin_review_needed" } ] },
    { "id": "snow_harmonic_phrase_01", "role": "snow_attached_radial_release", "entity_refs": ["snow"], "structure_refs": ["snow_radial_field"],
      "primitive_order": ["circle", "crescent", "trigon"], "placement_rule": "sparse_attached_radial_cells_upper_altitude_band",
      "provenance_refs": [ { "grammar_atom_id": "snow.attached_harmonic_cells", "kind": "needs_review", "review_status": "austin_review_needed" } ] }
  ],
  "render_intent": {
    "pipeline_id": "A_deterministic_primitives",
    "seed": 1001,
    "allowed_methods": ["deterministic_primitive_layout", "scalar_field_cell_extraction"],
    "disallowed_methods": ["lora_training", "diffusion", "exact_source_replication", "austin_style_prompting"]
  },
  "outputs": {
    "output_root": "track2-deterministic/morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/A_deterministic_primitives/P04",
    "required_files": ["scene_plan.json", "manifest.json", "final_1920x1080_srgb.png", "debug_overlay_1920x1080_srgb.png", "primitive_layout_1920x1080_srgb.png", "grammar_provenance_report.json"]
  }
}
```

Note: `render_intent.disallowed_methods` must always contain `"lora_training"`
(the schema enforces it via a `contains` constraint). Pipeline A's first P04
pass renders R1-only with the manifest flag `cymatics: deferred`; the second
pass realizes `snow_radial_field` through R2.

## 5. Work that can be built CPU-only now

Everything below needs no GPU. Confirmed installed: PIL 12.1.1, numpy 2.4.2,
`jsonschema`. To confirm by the worker: `pyyaml` (grammar loading), `scipy` +
`opencv-python` (R2 and Pipeline C extraction). R1 needs none of those three.

1. **Scene-plan JSON schema file** — lift the draft from the comparison plan
   (lines ~124–455) into a real `schemas/interactive_dream_scene_plan_v001.json`.
2. **Schema validator + provenance cross-check** — `jsonschema` validation, plus:
   every `grammar_atom_id` resolves in the YAML; every entity/structure/phrase
   has non-empty `provenance_refs`; no `blocked`-kind atom appears in a
   renderable element.
3. **Five scene-plan examples** — P01–P05 authored and validated (P02
   environment-only).
4. **Prompt normalization + blocked-subject checker** — keyword blocklist
   sourced from grammar `forbidden_or_paused_areas`.
5. **R1 deterministic scene-graph renderer** + the shared primitive-draw layer
   (circle/crescent/trigon/oval/line/mask, deterministic seeding).
6. **R2 scalar-field/cymatics renderer** — exists at v002-era; the new schema
   adapter is CPU work.
7. **Manifest + SHA256 hashing + `RUN_MANIFEST.json`**.
8. **Contact-sheet builder, debug-overlay renderer, scoring-sheet template,
   schema-validation utility**.
9. **opencv edge/contour extraction tooling** — built and tested on **existing
   fixture images only** (e.g. prior `morph_outputs/*` PNGs), never on
   newly-generated diffusion images. This pre-builds Pipeline C's post-processor
   with zero GPU.
10. **Review-packet template + `NO_PUBLIC_USE_INTERNAL_ONLY.txt`**.

Net: Pipeline A entirely, Pipeline B's procedural pre-finish entirely, and
Pipeline C's extraction tooling — all CPU. Only the diffusion *finisher* (B) and
diffusion *source* (C) need a GPU.

## 6. Work that requires local GPU verification before diffusion

Diffusion is **optional and async** — never in the live core path, never the
core geometry, never "Austin style". Before **any** diffusion run (Pipeline B
finisher *or* Pipeline C source image), a GPU worker runs the comparison plan's
**no-render verification checklist**:

- Host, OS, GPU model, VRAM, driver version, CUDA runtime (`nvidia-smi`).
- Python environment path + package lock/export.
- PyTorch CUDA availability + device name.
- `diffusers`, `transformers`, `accelerate`, `safetensors`, `opencv`, `pillow` versions.
- Model cache path, selected model ID, **license status**, file checksums, VRAM budget.
- xFormers / FlashAttention / Metal / CUDA / CPU-fallback decision.
- No-diffusion dry check: imports, a CUDA tensor allocation, model-metadata
  inspection, output-dir writability, disk-space check.
- Safety-filter availability + configuration.
- Determinism: seed handling, scheduler version, precision mode, bitwise-vs-visual reproducibility.

Hard rules:

- **Verification does not render.** It only decides whether the GPU lane is
  *eligible* to run later.
- The diffusion lane does not start until grammar + schema + Pipeline A and
  Pipeline B's procedural CPU baselines all exist (comparison plan first-build-
  order step 5).
- The GPU is the 3090 at Prav's studio (currently dev-mode return per
  `CURRENT_STATE.md`) or the 5090 if it arrives. Verification runs over SSH on
  whichever box, in a window that does not collide with show-prep use.
- The diffusion model's licence **and its training-data provenance** are
  themselves review items — the project licence floor is CC0 / CC BY / CC BY-SA
  for non-Austin material. "Austin-style" / "Coast Salish style" prompting is
  blocked regardless of GPU eligibility.

## 7. What to park until Austin reviews

All rendered output is internal until per-output Austin review. Beyond that,
two distinct categories:

**Parked — may resume after a specific Austin review:**

| Item | Resume gate |
|---|---|
| Visitor-prompt → live renderer connection | Austin approves the bounded-template visitor loop as a concept |
| P02 human figures beyond environment-only / schema-only | Austin answers grammar question `human_beach_prompts` |
| Figure-body depiction — orca/salmon/bird bodies, eyes, faces, fins, wings, joints | Austin sets the figure-lane boundary (keep functional motion + silhouette-safe masses only meanwhile) |
| Sun/ray grammar as public; snowflake/radial/cymatic visuals beyond internal review | Austin reviews sun + `snow_radial_topology` |
| Cloud/mist grammar as a public show layer | Austin gives a dedicated cloud direction (`cloud_mist_grammar`) |
| All diffusion output (Pipeline B finished, Pipeline C raw/cleanup) | GPU verification + A/B CPU baselines exist, then per-output review |
| Pipeline C entirely | Runs last, if at all — diffusion picks content before grammar |
| The 10 `gaps_questions_for_austin` in the grammar YAML | These *are* the review agenda — do not self-answer them |

**Blocked — needs a separate explicit approval path, not just a review:**

- Named chiefs, specific people, portraits, living public figures, identifiable children.
- Supernatural / named beings — Thunderbird, double-headed serpent, Transformer, TheCreator, Goat-man — and crest/clan-specific scenes.
- Exact Austin source replication — copied silhouettes, traced geometry, source atom adjacency, source palette, exact composition, source-vector animation.
- "Austin style" / "Coast Salish style" / "Indigenous style" prompting.
- James Harry relief / wrapped-form / sculpture-derived topology translation (paused).
- Any public claim of Austin authorship, cultural meaning, traditional meaning, or public-readiness.

## 8. Agents / workstreams needed next

The grammar file is done (comparison plan first-build-order step 1 complete).
Execution picks up at step 2. Five workstreams; each **owns its own folder** and
must not touch another's outputs (canon rule).

| WS | Title | Owner type | Depends on | Deliverable | Gate |
|---|---|---|---|---|---|
| **WS-1** | Schema + validation | Dev worker (Agent A/E) | grammar v001 (done) | Scene-plan schema file, validator, prompt-normalizer, blocked-subject checker, grammar loader, 5 validated scene plans | Schema lints; all 5 plans validate; validator rejects an untagged-atom fixture |
| **WS-2** | Pipeline A / R1 renderer | Dev worker (Agent A) | WS-1 | Shared primitive-draw layer, `render_pipeline_a.py`, manifest/overlay/contact-sheet; contract-slice prototype; P04 then P03 stills | Contract slice deterministic (two runs, same SHA256); P04 still passes the §9 rubric |
| **WS-3** | R2 scalar-field schema adapter | Worker (Agent B/E) | WS-1 + existing scalar-field v002 | Adapter so `scripts/cymatic_*` / `primitive_standing_wave_field_v002.py` consume scene-plan `scalar_field`/`topology_cell_field` structures and emit provenance-tagged cells | P04 snowflake renders via R2 with the interference-field debug overlays; sixfold reads, not mandala |
| **WS-4** | Diffusion GPU verification | GPU worker | WS-1 + WS-2 (must exist first) | The §6 no-render verification report; go/no-go eligibility | Report complete; **no diffusion rendered** |
| **WS-5** | Scoring + review packet | Reviewer (Agent G) | WS-2 outputs | `RUN_MANIFEST.json`, `SCORING_SHEET.md`, contact sheets, review-packet template; runs the rubric; assembles the Austin packet | Every still scored; blocked-subject scan clean |

Pipeline **B** (procedural + finisher) and Pipeline **C** are **not workstreams
yet** — they are gated behind WS-3 (procedural pre-finish) and WS-4 (diffusion
eligibility). A standing **safety/provenance auditor** role (WS-1 owner can hold
it) enforces the §12 stop conditions across all workstreams.

Sequencing: `WS-1 → (WS-2 ∥ WS-3) → WS-5`; WS-4 starts after WS-2 but its
*output* — actual diffusion — stays gated.

## 9. Pass/fail rubric for generated stills

Two layers. **Gate 0** is hard and binary — any failure voids the still. **Gate
1** is the 6-dimension score.

### Gate 0 — hard binary gates (any FAIL → still fails, score void)

- Output is exactly 1920×1080, sRGB, 8-bit PNG.
- Every visible subject and primitive role traces to a scene-plan
  `provenance_ref` → a grammar atom in `dream_grammar_provenance_v001.yaml`. Any
  unprovenanced atom → FAIL (and a §12 stop condition).
- No `blocked` subject is rendered — no faces, identifiable children, crest-like
  imagery, supernatural/named beings, exact Austin-source replication. Any →
  FAIL + stop condition.
- Reproducible from the manifest — re-run with the same seed, grammar hash, and
  code commit yields the same output (bitwise for CPU pipelines). Not
  reproducible → FAIL.
- `manifest.json` is complete: prompt ID, pipeline ID, seed, schema version,
  grammar hash, code commit, model IDs (if diffusion), safety status, every
  output file's SHA256. Incomplete → FAIL.
- `grammar_provenance_report.json` lists every grammar atom used and its
  provenance kind. Missing → FAIL.
- A paired `debug_overlay` still exists. Missing → FAIL.
- The renderer did not silently drop safety metadata. Dropped → FAIL + stop condition.

### Gate 1 — scored (0–3 per dimension, comparison plan rubric)

Safety containment · Prompt fidelity · Grammar provenance · Primitive/structure
legibility · Reproducibility · Review usefulness. Max 18.

### PASS bar

A still **passes** when **all** hold:

- All Gate 0 gates pass; and
- Grammar provenance = **3** (every visible rule/role tagged — non-negotiable per the no-untagged-atoms policy); and
- Safety containment ≥ **2**; and
- Reproducibility ≥ **2**; and
- Total ≥ **12 / 18**.

Any `blocked` safety result voids the total — the still fails regardless of
other scores. **A passing still is still only an internal artifact.** Passing
the rubric ≠ Austin approval ≠ public-ready; it means the still is eligible to
enter the Austin review packet.

## 10. Files / scripts the first dev worker creates

A new clean package — no collision with existing folders:

```text
track2-deterministic/interactive_dream/
  README.md                                  # boundary banner, run instructions, internal-only
  NO_PUBLIC_USE_INTERNAL_ONLY.txt
  RUN_NOTES.md                                # worker log
  schemas/
    interactive_dream_scene_plan_v001.json    # schema lifted from the comparison plan
  src/
    grammar_loader.py        # load + SHA256 dream_grammar_provenance_v001.yaml; resolve atom IDs; tag→kind mapping
    prompt_normalize.py      # raw prompt text → normalized text (deterministic)
    blocked_subjects.py      # keyword blocklist from grammar forbidden_or_paused_areas; block/allow + matched terms
    validate_scene_plan.py   # jsonschema validation + provenance cross-check; CLI: validate_scene_plan.py <plan.json>
    primitive_draw.py        # shared canvas + deterministic circle/crescent/trigon/oval/line/mask draw funcs
    render_pipeline_a.py     # R1 scene-graph renderer; validated plan → final PNG + primitive_layout PNG
    debug_overlay.py         # debug overlay: phrase IDs, provenance kinds, structure roles, renderer-of-origin
    manifest.py              # manifest.json (+ SHA256 of every output) + grammar_provenance_report.json
    contact_sheet.py         # final + debug-overlay contact sheets
    score_sheet.py           # emits SCORING_SHEET.md template with the §9 rubric
  scene_plans/
    P01_orca_breaching.json
    P02_children_playing_on_the_beach.json    # environment-only; human entities safety_status: blocked
    P03_salmon_swimming_up_a_river.json
    P04_rain_becoming_snow_on_a_mountain.json
    P05_birds_flocking_at_sunset.json
  tests/
    test_validate_scene_plan.py               # valid plans pass; untagged-atom fixture rejected
    test_blocked_subjects.py                  # blocklist catches named-being / person fixtures
    test_render_pipeline_a_smoke.py           # contract slice renders; two runs → identical SHA256
```

Render **outputs** are written to (not created until the schema lands):

```text
track2-deterministic/morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/
  A_deterministic_primitives/P0X/{scene_plan,manifest,grammar_provenance_report}.json
  A_deterministic_primitives/P0X/{final,debug_overlay,primitive_layout}_1920x1080_srgb.png
```

`field_renderer_adapter.py` (R2 schema adapter) is **WS-3**, not the first
worker. `contact_sheet.py` / `score_sheet.py` may be stubbed by the first worker
and filled once the first stills exist.

The first worker's scope = **WS-1 complete + the R1 renderer + the contract-slice
smoke render**. P04 and P03 prompt-complete stills are the immediate follow-on.

## 11. Build sequence + decision gates

1. **WS-1** lands the schema + validator + normalizer + blocked checker + grammar
   loader + 5 scene plans. **Gate:** schema lints; all 5 plans validate; the
   validator rejects an untagged-atom fixture; the tag→kind mapping is documented.
2. **WS-2** builds the shared draw layer + R1 + manifest/overlay, then the
   **contract-slice prototype** (one water phrase). **Gate:** two renders →
   identical SHA256; manifest + overlay + provenance report complete.
3. **WS-2** renders **P04** (Pipeline A, R1, `cymatics: deferred`), then **P03**.
   **Gate:** each still passes the §9 rubric; review-packet row written.
4. **WS-3** builds the R2 schema adapter; **P04 re-rendered** with the R2
   snowflake. **Gate:** interference-field debug overlays present; sixfold reads,
   not a mandala.
5. **WS-5** assembles the Pipeline A comparison run across P01 / P03 / P04 / P05
   (P02 environment-only), seeds 1001–1005. **Gate:** `RUN_MANIFEST.json` +
   `SCORING_SHEET.md` + contact sheets complete.
6. **WS-4** runs GPU verification (no render). **Gate:** go/no-go eligibility
   report. Starts only after steps 1–3.
7. Pipeline **B** procedural pre-finish stills (CPU) — only after WS-3. Then —
   only if WS-4 = go *and* the Austin review boundary allows — the diffusion
   finisher.
8. Pipeline **C** last, if at all.

The Austin review packet is assembled after step 5. Nothing goes public,
recorded, sponsor-facing, or onto a wall without per-output Austin sign-off.

## 12. Stop conditions

Stop the experiment immediately if any of these occur (comparison plan):

- A scene plan contains an unprovenanced grammar atom.
- A renderer silently drops safety metadata.
- A diffusion path produces faces, identifiable children, crest-like imagery,
  supernatural/named beings, or Austin-source-like replication.
- A final still cannot be reproduced from its manifest.
- A pipeline requires different grammar or schema assumptions than the others.
- An output is described as public-ready or Austin-approved without exact
  per-output review.

## 13. Next-worker prompt (copy-paste)

```text
You are the first dev worker on the Interactive Dream Pipeline (Salish Sea
Dreaming Phase 2 R&D). Working dir: /Users/darrenzal/projects/salish-sea-dreaming

SCOPE: WS-1 (schema + validation) + the R1 deterministic renderer + a single
contract-slice smoke render. Do NOT render the five test prompts yet. Do NOT
touch diffusion, LoRA, GPU, or any existing output folder.

BOUNDARY: Everything you produce is INTERNAL R&D. Not Austin-approved, not
public-use, not a cultural-meaning claim. No external comms. No public-ready
claims. Anything Austin-derived stays internal until Austin gives per-output OK.

READ FIRST (in order):
  - docs/space-center/interactive-dream-pipeline-execution-plan-2026-05-20.md  (this plan — sections 3, 4, 9, 10, 12)
  - docs/space-center/interactive-dream-pipeline-comparison-plan-2026-05-20.md  (scene-plan schema draft, lines ~124-455; test prompts; stop conditions)
  - track2-deterministic/primitive_grammar/dream_grammar_provenance_v001.yaml   (the grammar file you validate against)
  - docs/space-center/primitive-pattern-language-canon-2026-05-20.md            (morphology classes, valid adjacency, failure list)

CREATE the package track2-deterministic/interactive_dream/ exactly as listed in
section 10 of the execution plan:
  - schemas/interactive_dream_scene_plan_v001.json  — lift the schema verbatim from the comparison plan, save as a real JSON file
  - src/grammar_loader.py, prompt_normalize.py, blocked_subjects.py,
    validate_scene_plan.py, primitive_draw.py, render_pipeline_a.py,
    debug_overlay.py, manifest.py  (+ stub contact_sheet.py, score_sheet.py)
  - scene_plans/P01..P05 .json  — 5 schema-valid, provenance-tagged scene plans;
    P02 is environment-only with human entities at safety_status: blocked
  - tests/  — pytest for validation, blocked-subjects, and a render smoke test
  - README.md, NO_PUBLIC_USE_INTERNAL_ONLY.txt, RUN_NOTES.md

RESOLVE AND DOCUMENT (execution plan section 4, "Schema reconciliation notes"):
  1. The grammar-tag -> schema provenance-kind mapping (4 YAML tags -> 4 schema kinds), in grammar_loader.py.
  2. The coordinate convention for bounds_norm / control_points_norm — pick one,
     document it in the schema $comment and README; recommend matching
     grammar_v001.json interop_contract (center origin, [-1,1], +y up).

R1 RENDERER: deterministic, CPU-only (PIL + numpy — both installed). May lift
drawing code from track2-deterministic/scripts/render_primitive_scene_recipe.py.
Consumes a validated scene plan; draws path/mask/flock/school/weather_transition
structures + primitive_phrases. structure_type scalar_field / contour_field /
topology_cell_field are R2's job — for those, render a labeled placeholder and
set manifest flag "cymatics: deferred".

CONTRACT-SLICE SMOKE RENDER (the first executable prototype): hand-author one
scene plan with a single water phrase (circle -> crescent -> crescent -> curved
trigon) on black, seed 1001. Render it through validate -> render_pipeline_a ->
manifest. Output goes under
track2-deterministic/morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/
A_deterministic_primitives/. Do not create any other render outputs.

ACCEPTANCE — run all of these and paste the output before reporting done:
  - python3 -m py_compile src/*.py
  - python3 -m pytest tests/ -q                              (green)
  - python3 src/validate_scene_plan.py scene_plans/P0*.json   (all 5 pass)
  - validator rejects a deliberate untagged-atom fixture      (prove it fails)
  - smoke render: confirm the PNG is exactly 1920x1080, sRGB, 8-bit (PIL check)
  - run the smoke render twice; assert identical SHA256 (determinism)
  - confirm pyyaml / scipy / opencv-python availability; note any missing in RUN_NOTES.md

DO NOT: render P01-P05; build R2; touch GPU/diffusion/LoRA; modify any existing
file outside track2-deterministic/interactive_dream/ and its output dir; make
any external-facing or public claim. If anything is ambiguous, stop at
text/schema/metadata and write the question into RUN_NOTES.md.
```

---

*Plan landed 2026-05-20. The experiment is not ready to render the five test
prompts until WS-1 lands the schema, validator, blocked-subject checker, and
five validated scene plans. Per-output Austin review gates every public use.*
