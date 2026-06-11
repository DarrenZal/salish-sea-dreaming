# Water-Cycle Continuum Orchestration Plan - 2026-05-20

Status: INTERNAL orchestration / planning document only. No rendering was done
for this plan. No Agent B script or output folder was edited. Not
Austin-approved. Not public-use guidance. Not a cultural-meaning claim. Not a
literal physics claim. Not a production dependency. The production floor is
unchanged (see Section 7).

Revised 2026-05-20 (v2, post-adversarial-review): the v003 packet was rendered
shortly after this plan's first draft, and "B v003" is not the taxonomy-doc
Section 8 packet the first draft assumed. The "B v003" precondition and the
evidence floor are corrected to v003's actual output. See Revision Notes at the
end.

Role: Water-Cycle Continuum Orchestrator. This document plans the next
integrated visual lane - a continuous water-cycle piece built on the
scalar-field / cymatic / primitive-grammar engine. It coordinates worker tasks;
it does not render media.

## Source & Path Verification

Every path the task asked to read, and every path this plan cites, was checked
from repository root `/Users/darrenzal/projects/salish-sea-dreaming`. The v003
packet was re-verified on disk for this v2 revision. Honest status:

Task read-list:

| Path | Status |
|---|---|
| `docs/space-center/water-cycle-cymatic-primitive-scene-language-2026-05-20.md` | EXISTS - read |
| `docs/space-center/interference-field-cell-taxonomy-2026-05-20.md` | EXISTS - read |
| `docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md` | EXISTS - read |
| `docs/space-center/primitive-pattern-language-canon-2026-05-20.md` | EXISTS - read |
| `docs/space-center/austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md` | EXISTS - read |
| `docs/space-center/topology-cymatics-pivot-review-curation-2026-05-20.md` | EXISTS - read |
| `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v001_2026-05-20/README.md` | EXISTS - read |
| `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v002_2026-05-20/README.md` | EXISTS - read |
| `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/README.md` | **EXISTS** - the v003 packet was rendered 2026-05-20 ~20:00-20:10, after this plan's first draft (~19:57). Read for the v2 revision. See "What B v003 Actually Is" below. |

Additional context paths checked (cited below):

| Path | Status |
|---|---|
| `scripts/cymatic_field_topology_v001.py` | EXISTS |
| `scripts/cymatic_field_topology_v002.py` | EXISTS |
| `scripts/cymatic_field_topology_v003.py` | EXISTS - the v003 renderer; its output packet has now been produced |
| `track2-deterministic/scene_recipes/` | EXISTS - holds `mist_cloud_water_cycle_primitive_v001.json`, `rain_over_pond_primitive_v001.json`, `tanker_in_burrard_inlet_primitive_v001.json`, `whale_breach_primitive_v001.json` |
| `track2-deterministic/morph_outputs_INTERNAL/mvp_fallback_package_2026-05-19/` | EXISTS - production floor, unchanged |
| `docs/space-center/STATE-2026-05-20-post-water-v002.md` | EXISTS - read for current-state grounding |
| `docs/space-center/austin-consent-map.md` | EXISTS - per-output review log |

Naming-collision warning (important - do not confuse these):

- The task's "B v003" means `cymatic_field_topology_v003` (the
  `cymatic_field_topology` series, v001/v002/v003 all now rendered).
- `cymatic_topology_cells_v003_2026-05-20/` and
  `cymatic_topology_cells_v004_2026-05-20/` EXIST but are a **different
  series** (`cymatic_topology_cells`, not `cymatic_field_topology`).
- `primitive_field_cycle_v003_2026-05-20/` EXISTS but is a **different
  series** again (the primitive-cycle lane).
- None of those three is "B v003" for this plan. B v003 =
  `cymatic_field_topology_v003_2026-05-20/`, now rendered. See immediately
  below.

### What B v003 Actually Is (corrected in v2)

This plan's first draft assumed "B v003" would be a taxonomy-corrected packet
honoring the `interference-field-cell-taxonomy-2026-05-20.md` Section 8 output
contract (`cell_records.json`, `classification_summary.csv`, `debug_overlays/`
with 8 panels, `contact_sheet_debug.png`). That assumption was wrong. It is
corrected here.

The rendered v003 packet does **not** produce the Section 8 contract files -
none of the four is on disk, and `scripts/cymatic_field_topology_v003.py`
contains no code that would write them. v003 is a **canonical-primitive
legibility renderer** ("field handwriting -> primitive typography", per its own
README): the scalar field provides each cell's position, class, scale,
orientation, and timing; the renderer then draws *canonical* primitives (clean
moon-crescent and curved-trigon polygons) for legibility. Cell classification
still happens internally (`classify_cell`, `CellRecord`, `topology_class`,
source attribution); it is simply not exported in the Section 8 format.

The actual v003 packet, verified on disk 2026-05-20:

- 3 clips, 1920x1080, 24 fps, 6 s, 144 frames each:
  `sun_trigon_ring_v003.mp4` (single centre source with sixfold angular
  modulation `1 + alpha*cos(6*theta)`, alpha 0.7; first-ring cells
  canonicalized into radiant curved trigons), `crescent_lens_field_v003.mp4`
  (two fixed sources; interference cells canonicalized into moon-style
  crescents), `two_source_morph_v003.mp4` (two sources animate separation,
  rings into crescent bands and trigon-like cells).
- `cymatic_field_topology_v003_manifest.json` - field / source manifest.
- `primitive_audit_v003.json` - every rendered primitive audited back to one
  extracted source cell. This is the provenance record; it satisfies in
  substance the taxonomy doc's "rendered primitive records must map back to
  `source_cell_id` ..." requirement.
- `debug_stills/` - 6 panels per clip: `scalar_field`, `nodal_lines`,
  `positive_negative_regions`, `cell_class_colors`, `source_points`,
  `debug_composite`.
- `midpoint_stills/`, `legibility_tests/` - 1 per clip.
- 3 contact sheets (`_contact_sheet`, `_debug_contact_sheet`,
  `_phase_contact_sheet`), plus `canonical_primitives_reference_v003.png`,
  `canonical_validation_v003.png`, `sun_alpha_sweep_v003.png`.
- `README.md`.

Consequence for this plan: the continuum **adopts v003's actual evidence
structure** (manifest + `primitive_audit` + `debug_stills/` + contact sheets +
README) as the evidence floor - not the unmet Section 8 contract. v003 is the
renderer the phase studies extend; retrofitting the Section 8
classifier-output format would mean building a parallel renderer, which is
scope creep this lane does not need. Sections 5, 9, and 10 use v003's real
artifact set.

Paths this plan PROPOSES (do not exist yet; flagged inline as `PROPOSED`):

- `track2-deterministic/scene_recipes/water_cycle_continuum_v001.json`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_<render-date>/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_transitions_v001_<render-date>/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_continuum_roughcut_v001_<render-date>/`

Current-lane honesty: per `STATE-2026-05-20-post-water-v002.md`, the live R&D
review lead today is **water-flow phrase grammar v002**, and topology/cymatics
is parked as a *lead* until a taxonomy-corrected render exists. This plan does
not contradict that. The water-cycle continuum is the orchestration for what
the topology/cymatics lane becomes now that B v003 has landed; it is a
candidate internal review item for the next wave, not the current review lead
and not a production dependency.

## 1. Production Thesis

The water-cycle continuum is **one evolving scalar field with one classifier
and one renderer**, not a cut sequence of seven clips spliced together.

The engine already exists. `cymatic_field_topology_v001.py` defines a source
tuple:

```text
(x, y, amplitude, wavelength, frequency, phase, decay, velocity,
 birth_time, lifetime, symmetry_order, mode)
```

and a field:

```text
F(x,y,t) = sum_i  A_i * cos(2*pi*distance/lambda_i - omega_i*t + phase_i)
                 * decay(distance) * envelope(t)
```

Two of those tuple fields - `birth_time` and `lifetime` - plus `velocity` and
`symmetry_order` and `mode` are the entire mechanism the continuum needs. A
water-cycle "phase" is not a separate scene; it is a **configuration of the
source list at a moment in time**. A phase transition is emitters being born,
dying, drifting, or changing mode and symmetry parameters while the field is
never torn down.

Continuity therefore comes for free: the field `F(x,y,t)` runs unbroken for
the whole loop, the same threshold/classification pipeline extracts
circle/crescent/trigon cells every frame, and the same boundary-language
renderer draws them. What changes from sun to mist to rain to snow is only
*which taxonomy types dominate* and *how the sources are arranged*. There is no
crossfade because there is nothing to fade between - it is the same field.

This reframes the deliverable. The continuum is authored as a **timeline of
source events** over the existing source-tuple model, expressed once as a
source-list recipe (Section 6) and rendered once as a continuous run. Duration
becomes a render parameter, not an edit.

What the continuum is NOT, stated for the record (from
`water-cycle-cymatic-primitive-scene-language-2026-05-20.md` and
`primitive-pattern-language-canon-2026-05-20.md`):

- Not meteorology, not a literal physics simulation.
- Not ceremony, not sacred geometry, not a mandala/flower-of-life aesthetic.
- Not a cultural-meaning claim and not a general Coast Salish grammar.
- Not exact Austin artwork replication and not SD/LoRA style transfer.
- Not a cut sequence; not a public deliverable; internal R&D until Austin
  per-output review.

The win condition: the piece reads as *water perceiving its own cycle* through
a single shared primitive vocabulary, sparse and role-labelled, with every
visible mark traceable to a field source.

## 2. Core Loop Recommendation

Recommended primary build target: a **90-second loop at 24 fps (2160 frames),
1920x1080**, seven phases, one loop point.

Phase ring (the cycle closes 7 -> 1):

```text
        (1) sun / radiant
       /                  \
  (7) melt/return      (2) vapor / mist
      |                       |
  (6) snowflake           (3) rain onset
       \                     /
   (5) standing-wave -- (4) raindrops on water
```

Timeline (durations include a ~3 s outgoing morph carved from each phase's
tail; transitions are not additive time):

| # | Phase | Duration | Window (s) |
|---|---|---|---|
| 1 | Sun / radiant trigon field | 12 s | 0.0 - 12.0 |
| 2 | Vapor / cloud / mist | 13 s | 12.0 - 25.0 |
| 3 | Rain onset | 9 s | 25.0 - 34.0 |
| 4 | Raindrops on water | 14 s | 34.0 - 48.0 |
| 5 | Standing-wave interference | 15 s | 48.0 - 63.0 |
| 6 | Snowflake / sixfold crystallization | 14 s | 63.0 - 77.0 |
| 7 | Melt / return to sun | 13 s | 77.0 - 90.0 |

**Loop point: t = 90.0 s identical to t = 0.0 s.** The melt phase ends at a
"single-centre field rest" - the source list reduced to one low-amplitude
central emitter. That is exactly the configuration the sun phase opens from.
The render is **2160 frames, indices 0-2159**. Frame 2159 has just settled into
the rest state; frame 0 *is* that rest state; playing frame 2159 -> frame 0 is
continuous. Do not render a 2161st frame - frame "2160" is simply frame 0 of
the next loop. Because the start and end source configurations are identical,
the loop is a **hard cut with zero crossfade**; hold a ~1.5 s low-activity rest
across the seam so the join is invisible. The loop point is deliberately placed
at the moment of *minimum cell count* in the whole piece - the easiest possible
seam.

Phase ordering note: this plan deliberately **re-sequences** the ring. The
task's seven-phase order (sun -> vapor -> rain -> raindrops -> interference ->
snowflake -> melt) tracks physical phase-change order: evaporation,
condensation, precipitation, surface impact, freezing, melt. The
`water-cycle-cymatic-primitive-scene-language-2026-05-20.md` doc gives a
different five-node ring - `rain -> radial wave -> six-ray snowflake ->
cloud/mist -> sun -> rain` - in which snowflake is adjacent to mist and there
is no standing-wave stage (it treats standing waves as a rhythm technique and a
render recipe, not a cycle node). This plan does not claim those are the same
ring traversed from a different start: it adopts the task's physically-ordered
seven-phase ring, splits rain into onset plus surface-impact, and promotes
standing-wave interference to a distinct phase. For phase order in this lane,
treat the scene-language doc as superseded; its state-morphology table,
visual-rhythm guidance, and render recipes remain authoritative. The
scene-language doc should be annotated so the two do not silently disagree.

Scaling: because the continuum is a source-list timeline, 60 s and 120 s
variants are render parameters, not re-edits. For a 60 s cut, compress
interference to ~9 s and vapor to ~8 s and trim the rest proportionally. For
120 s, lengthen dwell per phase (do not add phases). Build and review the 90 s
loop first; 90 s gives each primitive phrase enough temporal persistence to be
legible (the taxonomy doc requires cells to hold long enough to read polarity,
boundary, and role) without an internal reviewer losing the thread.

## 3. Phase Table

Seven phases. For each: visual read, source-list behavior, expected primitive
morphology (using the taxonomy of
`interference-field-cell-taxonomy-2026-05-20.md`), transition into the next
phase, the isolated 6-10 s study (all seven are rendered fresh - see Section 5),
and the review risk / Austin question.

Morphology vocabulary used below - renderer `topology_class`: `circle`,
`crescent`, `trigon`, `outline`, `compound`. Field `taxonomy_type`:
`positive_phase_cell`, `negative_phase_cell`, `nodal_boundary`,
`radial_source_ring`, `interference_lens_crescent`,
`multi_source_trigon_scallop`, `six_ray_snowflake_sun_candidate`,
`ambiguous_rejected`.

### Phase 1 - Sun / Radiant Trigon Field (0-12 s)

- **Visual read:** one luminous central origin; a few partial ring-phase
  crescent arcs around it; a small number of attached curved trigon releases
  at selected lobes. Calm, radiant, low cell count, open negative space
  dominant. The loop opens here from the field-rest state.
- **Source-list behavior:** 1 central emitter; `mode = radial`;
  `symmetry_order` blended low (m=0 toward m=6); optionally 1-3 mode terms;
  steady amplitude with a slow breathing `envelope(t)`. No drift.
- **Expected primitive morphology:** `circle` = central orb
  (`radial_source_ring` collapsed to a compact centre). `crescent` = ring-phase
  arcs (partial `radial_source_ring`). `trigon` =
  `multi_source_trigon_scallop` / radial release lobes, **attached to the
  ring/centre, never detached**. 0-1 faint `six_ray_snowflake_sun_candidate`.
- **Transition into Phase 2:** central amplitude diminishes; the emitter
  weakens and begins slow upward `velocity`; rings break into drifting partial
  arcs; circle origins drop out as `origin_hidden`. The orb "evaporates."
- **Isolated study for B:** `phase1_sun_radiant` 6-10 s, rendered fresh.
  Direct precursor -
  `cymatic_field_topology_v003_2026-05-20/sun_trigon_ring_v003.mp4` (single
  centre source with sixfold angular modulation `1 + alpha*cos(6*theta)`,
  alpha 0.7; canonical curved trigons from first-ring cells). Use it as the
  reference render for this phase.
- **Review risk / Austin question:** HIGHEST Austin risk. Sun/radiant/ray
  behavior can read as Austin-derived sun grammar (`Nature_Cosmic_Sun`,
  `Animal_Bird_Raven_Sun`). Bounded Austin question: *"Does a single-centre
  radiant field whose releases stay curved and attached - never detached rays
  - stay clearly on the abstract-water side of the line, or does any radiant
  treatment need to wait for explicit per-output review?"* Do not present as
  Austin sun grammar.

### Phase 2 - Vapor / Cloud / Mist (12-25 s)

- **Visual read:** faint, low-contrast drifting partial arcs rising and
  spreading. Most circle origins absent. Sparse, soft, the "in-between" water
  state. Lowest contrast in the loop.
- **Source-list behavior:** weak multi-emitter network, low amplitude, high
  `decay`, slow upward `velocity`; 3-7 emitters; low-alpha nodal/flow-network
  edges between them. `mode = network` / weak multi-emitter.
- **Expected primitive morphology:** `crescent` dominant - faint drifting
  arcs along network edges. `circle` mostly omitted (`origin_hidden`, labelled
  intentional). Rare terminal `trigon` only at flow-network edges.
  `nodal_boundary` outlines kept very low density.
- **Transition into Phase 3:** emitters "cool"; drifting arcs slow, gather and
  lower; amplitude re-concentrates into discrete points; mist crescents bead
  back into circle origins (the condensation read).
- **Isolated study for B:** `phase2_vapor_mist` 6-10 s, rendered fresh. No
  render precursor in any version - this is the **least-grounded phase** (see
  risk). A recipe stub exists at
  `track2-deterministic/scene_recipes/mist_cloud_water_cycle_primitive_v001.json`.
- **Review risk / Austin question:** Mist/cloud grammar had **no dedicated
  primitive grammar in the May 18 Meeting 2 screenshots** (per
  `austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md` motif 6).
  Soft cloud forms also carry `eye_pair_risk` / accidental-face risk. Austin
  question, kept separate from the sun question: *"Is a low-contrast partial-
  phrase mist - faint crescents, hidden circle origins, rare trigons - an
  acceptable internal in-between state?"* Keep contrast low; do not promote.

### Phase 3 - Rain Onset (25-34 s)

- **Visual read:** discrete droplet origins appear and fall; the soft mist
  field becomes punctuated by small descending impulse sources. Shortest
  phase; a quick gather.
- **Source-list behavior:** short-lived emitters with staggered `birth_time`
  and short `lifetime`; downward `velocity`; small per-emitter `amplitude`;
  3-7 concurrent. `mode = impulse`.
- **Expected primitive morphology:** `circle` returns as droplet/impact
  origin. `crescent` = first partial ripple arc forming around each nascent
  drop. `trigon` = tiny splash/release mark, small and attenuating.
- **Transition into Phase 4:** droplets land - each falling circle becomes a
  surface impact origin that spawns a radial ripple; impact density rises; the
  field shifts from "falling" to "surface ripple."
- **Isolated study for B:** `phase3_rain_onset` 6-10 s, rendered fresh. No
  v003 precursor (v003 carries no raindrop clip); the closest references are
  the v001/v002 raindrop clips named in their READMEs
  (`raindrops_on_water_field_v001.mp4`, `raindrops_on_water_primitives_v002.mp4`).
- **Review risk / Austin question:** Lower risk - rain-over-pond is close to
  the Meeting 2 pond metaphor. Constraint: rain must be **sparse impact
  phrases, not particle wallpaper** (motif 6). Austin question: *"Is sparse
  per-drop impact phrasing the right density, versus a denser rainfall read?"*

### Phase 4 - Raindrops on Water (34-48 s)

- **Visual read:** radial ripples from multiple impacts; interference where
  ripple fronts cross; a legible `circle -> crescent -> crescent -> trigon`
  phrase per drop. Well-grounded - v001 and v002 both rendered raindrop clips
  (v003 did not carry one forward).
- **Source-list behavior:** 3-7 short-lived radial impact sources, each
  spawning expanding rings; overlapping decaying ripple fields. `mode = radial`
  / `impulse`.
- **Expected primitive morphology:** `circle` = impact origin and interference
  node. `crescent` = partial rings plus `interference_lens_crescent` where two
  ripple fronts cup. `trigon` = `multi_source_trigon_scallop` outward release
  where a ripple weakens or three fronts meet.
- **Transition into Phase 5:** the impact sources stop expiring and become
  persistent; ripples stop decaying and phase-lock; the transient ripple field
  "sets" into a stable standing pattern.
- **Isolated study for B:** `phase4_raindrops_on_water` 6-10 s, rendered fresh.
  Note: the v003 packet has **no raindrop clip** (its three clips are
  `sun_trigon_ring`, `crescent_lens_field`, `two_source_morph`); the closest
  v003 reference is `crescent_lens_field_v003.mp4` for interference-crescent
  legibility. The v001/v002 raindrop clips remain the motion reference.
- **Review risk / Austin question:** Lowest Austin risk; the natural lead for
  an Austin packet. Austin question: *"Does the per-drop phrase read cleanly as
  circle origin -> crescent -> crescent -> trigon attenuation?"*

### Phase 5 - Standing-Wave Interference (48-63 s)

- **Visual read:** a stable nodal lattice of cells; positive antinode cells
  fill, negative cells outline; a slow phase inversion swaps which polarity
  fills. The most overtly "cymatic" phase. Longest phase.
- **Source-list behavior:** 3-7 persistent emitters in a fixed layout; stable
  `F(x,y)`; `phase_display(t)` animates the display `Z(x,y,t)`. **Classify
  cells from stable `F`, never from animated `Z`** (taxonomy doc Section 1) -
  quarter-phase `Z` collapses the field into a full-screen nodal band.
- **Expected primitive morphology:** `circle` = interference node;
  `crescent` = `interference_lens_crescent` cells; `trigon` =
  `multi_source_trigon_scallop` three-source gaps; `nodal_boundary` = stable
  outlines held across both phase states. Phase inversion swaps fill/outline,
  it does not recompute cell membership.
- **Transition into Phase 6:** the emitter layout is pulled toward sixfold
  symmetry; `symmetry_order` ramps to 6; the standing field reorganizes into a
  Bessel `m=6` / sixfold radial field - the lattice "crystallizes."
- **Isolated study for B:** `phase5_standing_wave` 6-10 s, rendered fresh
  (scene-language Recipe 3, "Standing-Wave Phase Inversion"). Direct precursor
  - `cymatic_field_topology_v003_2026-05-20/two_source_morph_v003.mp4` (two
  sources animating separation, rings into crescent bands and trigon-like
  interference cells); the v001/v002 `two_source_interference_*` clips named in
  their READMEs are earlier references.
- **Review risk / Austin question:** MEDIUM risk - the failure mode is
  wallpaper density / generic Chladni / sacred-geometry read. This phase is
  **not for Austin yet**: it is an internal legibility gate. Internal question:
  *"Does it stay sparse and role-labelled (8-24 selected cells, no all-frame
  lattice), or does it become decorative Chladni wallpaper?"* Keep internal
  until that gate passes.

### Phase 6 - Snowflake / Sixfold Crystallization (63-77 s)

- **Visual read:** a sixfold radial structure; selected lens/crescent cells
  along six arms; attached curved trigon ray tips; a centre node. The sixfold
  read is clear but **must not be a mandala**.
- **Source-list behavior:** 1 radial centre plus mode terms, `symmetry_order =
  6`; Bessel `m=6` harmonic. Prefer the radial-centre + mode approach over six
  literal point emitters - v001's `seed_field_breathing_v001` carried visible
  *seven*-source symmetry and read as a scalar-field diagnostic, not a finished
  visual; the m=6 harmonic avoids that artifact.
- **Expected primitive morphology:** `compound` =
  `six_ray_snowflake_sun_candidate` with `center` status =
  `snow_core_candidate`. Child `circle` = centre node / frozen-water cell;
  `crescent` = paired lens cells along the arms; `trigon` = six attached
  curved ray tips. Six arms must not all be equally bright (mandala failure).
- **Transition into Phase 7:** symmetry holds briefly, then amplitude and arm
  definition soften; the six-ray structure collapses inward toward the centre;
  cells dissolve back into the field; the centre re-warms.
- **Isolated study for B:** `phase6_snowflake` 6-10 s, rendered fresh
  (scene-language Recipe 2, "Radial Wave To Six-Ray Snowflake"). The v003 sun
  clip's sixfold angular term `1 + alpha*cos(6*theta)` is a usable starting
  point for sixfold structure; `seed_field_breathing_v001.mp4` is a caution
  case (visible seven-source symmetry), not a target.
- **Review risk / Austin question:** HIGH risk and adjacency risk - sixfold
  radial sits visually close to the radial sun (Phase 1), and
  `six_ray_snowflake_sun_candidate` is explicitly the ambiguous class in the
  taxonomy. Plus mandala-wallpaper risk. Austin question, paired with the sun
  question: *"Does the project distinguish snowflake-sixfold from sun-radial
  clearly enough through palette, motion, and centre treatment, or should both
  be reviewed together as one radial-grammar question?"*

### Phase 7 - Melt / Return to Sun (77-90 s)

- **Visual read:** the sixfold structure dissolves; arms retract; cells fade;
  the field simplifies to a single warming centre. Lowest cell count of the
  loop. Quiet. This phase closes the loop.
- **Source-list behavior:** `symmetry_order` ramps 6 -> 0; emitters merge
  toward the centre; one central low-amplitude emitter remains; amplitude
  begins to re-warm. The phase ends in the **exact Phase 1 opening
  configuration** (the field-rest state).
- **Expected primitive morphology:** `crescent` and `trigon` counts fall;
  `circle` (central) re-emerges as the dominant and finally the only origin.
  The field rests.
- **Transition into Phase 1:** this *is* the loop point - end state identical
  to start state; a ~1.5 s field-rest hold spans the seam (Section 2).
- **Isolated study for B:** `phase7_melt_return` 6-10 s, rendered fresh. No
  precursor clip in any version.
- **Review risk / Austin question:** Low intrinsic risk, but it hands directly
  back into the high-risk sun phase. No separate Austin question; covered by
  the Phase 1 sun question.

## 4. What Not To Include Yet

The continuum v001 is **water-state-only**. The following stay out of the
continuum field and are not the next worker burden. This is deliberate
deferral, not rejection - each has a real reason and a real gate.

- **Salmon, fish, orcas, birds, and human/child figures.** Per
  `primitive-grammar-visual-acceptance-criteria-2026-05-20.md` Lane 5 and
  `primitive-pattern-language-canon-2026-05-20.md` Lane 5, the functional-
  figures lane is **parked**. A figure earns inclusion only when *all* of its
  gates are met: it has a functional show role (swim, school, current-follow,
  emerge from water geometry, return to source), Austin has reviewed the style
  direction and set the source-usage boundary, and the work yields a reusable
  rig - not a one-off still. None of those gates is met now.
- **Why figures break the thesis, not just the schedule.** The continuum's
  whole value (Section 1) is *one scalar field, one classifier, one renderer*.
  A fish or bird needs a *second* pipeline - body spines, joints, articulation
  rigs, flock vectors - which is a different architecture. Baking figures into
  the continuum field would dissolve the single-system property. Figures, if
  they ever join, must be a **separate composited layer** in Resolume with its
  own kill-switch, never sources inside `F(x,y,t)`.
- **The underwater / salmon / river-ascent layer the brief names as
  "potential later."** Treat it as a candidate *Phase 8 / parallel layer* for
  a future version, gated behind the dream/figure pipeline (see
  `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md`
  and `docs/space-center/interactive-dream-pipeline-comparison-plan-2026-05-20.md`)
  and behind Austin review. It is explicitly *not* core burden for v001-v003 of
  this lane.
- **Audio / voice reactivity.** The acceptance-criteria doc (Lane 3) and the
  topology-pivot open questions both say audio-reactive cymatics wait until the
  still/loop geometry is accepted. The continuum v001 is a **fixed-timeline
  render**; it is not driven by visitor audio. Audio reactivity is a later
  version once the loop geometry passes internal review.
- **SD / LoRA / style transfer.** Explicitly excluded from this lane by the
  task and by the canon. The continuum is deterministic field extraction only.
- **Exact Austin source geometry, palette, atom adjacency, faces, Thunderbird,
  serpent, named beings.** Public-blocked by default per the canon. The
  continuum uses *no* Austin source vectors - only a generic scalar field.
- **Prompt / dream scene content** (tankers, whales, named scenes). That is the
  prompt-to-primitive lane, reviewed separately; it does not enter the
  continuum.
- **Any public-readiness, Austin-approval, or cultural-meaning claim** in
  filenames, READMEs, or review notes.

Principle: the continuum stays a closed, legible, water-only system. Every
candidate addition must answer "does this stay one scalar field?" - if not, it
is a separate composited layer reviewed on its own track.

## 5. Render Build Order

Precondition - **B v003: SATISFIED.** The v003 packet
`cymatic_field_topology_v003_2026-05-20/` has been rendered (verified on disk
2026-05-20). It is the canonical-primitive legibility renderer described in
"What B v003 Actually Is" above - 3 clips, manifest, `primitive_audit_v003.json`,
6-panel `debug_stills/`, contact sheets, README. It is **not** the
`interference-field-cell-taxonomy` Section 8 classifier-output packet, and this
plan does not require it to be: the continuum extends v003's renderer and
adopts v003's evidence structure as the floor (Section 9). The three worker
tasks below can therefore start now; there is no v003 escalation gate
remaining.

### Worker Task 1 - Isolated Phase Studies

Render the seven isolated phase studies, one per Section 3 phase, 6-10 s each,
1920x1080, 24 fps, black-screen layer-only. Build them by extending the v003
renderer (`scripts/cymatic_field_topology_v003.py`): import its field engine,
cell classifier, and canonical-primitive machinery into a new sibling script,
or copy that machinery if import proves awkward. Do not edit v003's script or
its output folder. Each study ships the v003-shaped evidence floor (Section 9):
a manifest JSON, a `primitive_audit` JSON, `debug_stills/` (the 6 v003 panels),
a contact sheet (finals beside debug frames), a README with cultural status,
`ffprobe` on every MP4, `py_compile` on the new script. Output to `PROPOSED`
`track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_<render-date>/`.
This is the task the Section 10 prompt covers.

### Worker Task 2 - Transition Tests

Render the six boundary transitions as short clips, proving the source-list
morph is continuous with **no crossfade**: sun->vapor, vapor->rain,
rain->raindrops, raindrops->interference, interference->snowflake,
snowflake->melt. (melt->sun is the loop point, not a clip - it is verified by
field-identity at the seam, not rendered as a transition.) The morph itself is
~3 s (the value in the Section 6 schema); each transition *test clip* is 4-8 s
= the ~3 s morph plus ~1-2 s of lead-in (end of phase N) and lead-out (start of
phase N+1) so the reviewer sees the morph in context. Each transition shows the
param ramp (amplitude, decay, velocity, symmetry_order, birth/death) driving
the change. Evidence floor as Task 1, plus a debug still at the morph midpoint
showing both phases' cell populations co-present. Output to `PROPOSED`
`track2-deterministic/morph_outputs_INTERNAL/water_cycle_transitions_v001_<render-date>/`.

### Worker Task 3 - Assembled Continuum Rough Cut

Render the full 90 s continuum as a single continuous field run from one
source-list timeline recipe (Section 6 schema), 1920x1080, 24 fps, 2160
frames (indices 0-2159), black-screen layer-only. Verify the loop by playing
the rough cut 3x back-to-back with no visible seam. Evidence floor as Task 1,
plus: an ffprobe-confirmed 90.0 s / 2160-frame / 24 fps master, a loop-seam
contact sheet (frames 2157-2159 beside frames 0-2), and a phase-marker timeline
in the README. Output to `PROPOSED`
`track2-deterministic/morph_outputs_INTERNAL/water_cycle_continuum_roughcut_v001_<render-date>/`.

Sequencing rule: Task 2 starts only after Task 1's phase studies pass the
Section 9 acceptance criteria; Task 3 starts only after Task 2 confirms each
transition morphs without crossfade. Do not jump to the rough cut to "see it
whole" before the phases and transitions individually pass - a bad phase
hidden inside a 90 s run is far harder to diagnose.

## 6. Source-List Schema

A minimal JSON schema for the continuum recipe. `PROPOSED` location:
`track2-deterministic/scene_recipes/water_cycle_continuum_v001.json` (the
`scene_recipes/` directory exists; this file does not yet). It extends the
existing source-tuple model from `cymatic_field_topology_v001.py`; it
supersedes the single-state stubs `rain_over_pond_primitive_v001.json` and
`mist_cloud_water_cycle_primitive_v001.json` by spanning all phases in one
timeline.

Schema skeleton (one fully-worked source, phase, and transition shown; the
rest follow the same shape):

```json
{
  "schema": "water_cycle_continuum/v1",
  "status": "internal_austin_review_needed",
  "cultural_claim": false,
  "loop": {
    "duration_s": 90.0,
    "fps": 24,
    "frame_count": 2160,
    "frame_indices": "0..2159",
    "loop_point_s": 0.0,
    "loop_anchor": "single_centre_field_rest",
    "crossfade": false
  },
  "resolution": { "w": 1920, "h": 1080, "master_first": "1080p", "later": "4k_if_accepted" },
  "palette": {
    "background": "#05070b",
    "ink_primary": "ivory",
    "ink_secondary": "pale_blue",
    "accent": ["muted_teal", "muted_gold"],
    "rule": "no red/green/blue debug-category colours in the beauty render"
  },
  "field": {
    "model": "scalar_standing_wave",
    "classify_from": "F_xy_stable",
    "never_classify_from": "Z_xyt_animated",
    "normalize_range": [-1, 1],
    "tau_percentile_range": [68, 80],
    "node_epsilon_range": [0.015, 0.050],
    "caps": {
      "emitters": [3, 7],
      "radial_centre_plus_modes": [1, 3],
      "selected_filled_cells": [8, 24],
      "nodal_boundary_groups": [1, 4],
      "six_ray_candidates": [0, 2],
      "no_all_frame_lattice": true
    }
  },
  "primitive_render_mode": {
    "topology_classes": ["circle", "crescent", "trigon", "outline", "compound"],
    "boundary_language": "class_specific_weight_opacity_persistence",
    "compound_policy": "faint_ghost",
    "temporal_hold_s": 0.4,
    "canonicalize_crescent": "explicit_and_reversible_in_metadata"
  },
  "sources": [
    {
      "id": "emitter_centre",
      "x": 0.5, "y": 0.5,
      "amplitude": 1.0,
      "wavelength": 0.18,
      "frequency": 0.6,
      "phase": 0.0,
      "decay": 0.4,
      "velocity": [0.0, 0.0],
      "birth_time_s": 0.0,
      "lifetime_s": 90.0,
      "symmetry_order": 0,
      "mode": "radial"
    }
  ],
  "phases": [
    {
      "id": "sun_radiant",
      "order": 1,
      "start_s": 0.0,
      "duration_s": 12.0,
      "active_source_ids": ["emitter_centre"],
      "field_intent": "single luminous centre, attached curved releases",
      "dominant_taxonomy": ["radial_source_ring", "multi_source_trigon_scallop"],
      "symmetry_order": 0,
      "mode": "radial",
      "cultural_status": "internal_austin_review_needed",
      "austin_risk": "high"
    }
  ],
  "transitions": [
    {
      "id": "sun_to_vapor",
      "from_phase": "sun_radiant",
      "to_phase": "vapor_mist",
      "start_s": 9.0,
      "duration_s": 3.0,
      "method": "source_param_ramp_and_birth_death",
      "params_ramped": ["amplitude", "decay", "velocity", "symmetry_order"],
      "crossfade": false
    }
  ],
  "austin_boundary": {
    "public_use": false,
    "exact_austin_source": false,
    "sd_lora": false,
    "review_log": "docs/space-center/austin-consent-map.md"
  }
}
```

Per-phase parameter table the recipe must encode (the worker fills the seven
`phases[]` and six `transitions[]` entries from this):

| Phase id | symmetry_order | mode | dominant_taxonomy | source regime |
|---|---|---|---|---|
| `sun_radiant` | 0 (->6 blend) | radial | radial_source_ring, multi_source_trigon_scallop | 1 centre, steady |
| `vapor_mist` | 0 | network | nodal_boundary, interference_lens_crescent | 3-7 weak, upward drift |
| `rain_onset` | 0 | impulse | radial_source_ring, multi_source_trigon_scallop | 3-7 short-lived, downward |
| `raindrops_on_water` | 0 | radial/impulse | interference_lens_crescent, multi_source_trigon_scallop | 3-7 impact, decaying |
| `standing_wave` | 0 | multi_emitter | positive_phase_cell, negative_phase_cell, nodal_boundary | 3-7 persistent, fixed |
| `snowflake` | 6 | radial_bessel | six_ray_snowflake_sun_candidate | 1 centre + modes |
| `melt_return` | 6 ->0 | radial | radial_source_ring | emitters merge to 1 centre |

Schema design notes: (1) sources carry `birth_time_s` / `lifetime_s` /
`velocity` so a single `sources[]` list spans the whole loop - phases reference
source IDs, they do not own separate fields. (2) transitions are param ramps
carved from the phase boundary, never crossfades. (3) `field`,
`primitive_render_mode`, and `palette` are global and constant for the loop -
only `sources[]` and per-phase params evolve. (4) every object carries a
cultural-status / Austin-boundary marker so no downstream agent can strip it.
(5) `tau_percentile_range` and `node_epsilon_range` are *parameter ranges to
choose a value within* (from the taxonomy doc Section 2), not min/max caps -
the `caps` block holds the actual hard limits.

## 7. Resolume / Hubble Fit

The continuum is built as an **additive black-screen layer**, the same shape
as the water-flow phrase grammar v002 outputs.

- **Black background.** Render on `#05070b` near-black so the layer composites
  additive / screen blend in Resolume over the production-floor footage
  (`mvp_fallback_package_2026-05-19/clean_exports/`, e.g. the
  `h6_kelp_forest` wide-wall base). The continuum layer never carries its own
  background plate.
- **Layer-only master is the deliverable.** An optional composite-preview over
  one Moonfish clip is allowed *as a review aid only*, clearly labelled - not a
  production master. This matches the STATE doc's treatment of the water-flow
  v002 "over Moonfish" clips ("review aid, not production master").
- **1920x1080 first.** v001, v002, and v003 are all 1920x1080; build and review
  the continuum at 1080p. Render a 4K (3840x2160) master **only after** the
  loop is accepted internally - 4K before acceptance just multiplies
  re-render cost.
- **Codec.** Review MP4 (H.264) for now. HAP / Resolume-native codec export is
  deferred until the loop is accepted (the STATE doc keeps HAP exports
  deferred unless specifically requested).
- **Kill-switch discipline.** The continuum must stay a single, separable
  Resolume layer that can be muted instantly. The canon requires
  topology/cymatics layers to be kill-switched by default. It is never wired
  as a hard production dependency.
- **Loop in Resolume.** Set the layer to loop; the loop point (Section 2) is a
  hard cut at the field-rest seam, so Resolume's native loop handles it with
  no dissolve.
- **Venue note.** Lorraine approved 1080p+ for the Space Centre Hubble surface,
  but that approval does not put this lane on the wall. The continuum reaches a
  projector only after Austin per-output review (Section 8). 1080p-first here
  is an R&D-cost decision, not a venue spec.

## 8. Austin / Pravin Review Strategy

Per `feedback_austin_consent_trust_floor.md`, per-output Austin approval is the
**floor, not a milestone** - default-pause, not default-ship. Public-framing
language is in scope for review, not only visual motifs.

### To Pravin (internal R&D review)

- Show the isolated phase studies and the assembled rough cut as **internal
  R&D**, explicitly *not* a production dependency.
- Open by confirming the production floor (MVP fallback footage package) is
  untouched and intact regardless of how the continuum progresses.
- Keep the continuum layer kill-switched during any review that is not
  explicitly an internal R&D session.
- Sequencing: the current review lead is water-flow phrase grammar v002. The
  continuum is the *next* wave - present it after v002 review, not instead of
  it.

### To Austin

- **Lead with the lowest-risk phase.** Phase 4 (raindrops on water) is the
  natural lead - closest to the Meeting 2 pond metaphor, lowest Austin risk.
- **Frame as an internal topology / legibility question, never a cultural
  claim.** Per the acceptance-criteria Lane 3 and the topology-pivot doc, use
  "radial topology" rather than "sacred geometry," and present the work as
  internal design hypotheses, not Austin-authored output.
- **Show the sun and snowflake phases only as explicit review questions** -
  not as finished looks. They are the ask, not the deliverable.

What NOT to show Austin:

- Not the standing-wave interference phase until it passes the internal
  no-wallpaper legibility gate (Section 3, Phase 5).
- Not anything labelled public-ready, Austin-approved, or Austin-authored.
- No salmon / figure / dream-scene material in this packet - the continuum
  packet is water-state-only.
- Not "sacred geometry," "ceremony," "teaching," or "Coast Salish grammar" as
  descriptors of the output.

Exact questions to ask Austin (bounded, copy from the phase table):

1. Is a water-cycle continuum - water states sharing one primitive grammar -
   a valid internal direction to keep developing? (topology-pivot Q1)
2. Sun/radiant phase: does a single-centre radiant field with only attached,
   curved releases (never detached rays) stay on the abstract-water side, or
   does any radiant/ray treatment need to wait for explicit per-output review?
3. Snowflake-sixfold vs sun-radial: are these distinct enough through palette,
   motion, and centre treatment, or should both be reviewed together as one
   radial-grammar question?
4. Cloud/mist: is a low-contrast partial-phrase mist a safe internal in-between
   state, given Meeting 2 showed no dedicated cloud/mist primitive grammar?
5. Review-facing language: are "water-cycle continuum," "radial topology,"
   "standing-wave cell," "interference lens" acceptable; are "sacred geometry,"
   "snowflake," "cymatic," "teaching" off-limits or too claim-heavy?
6. Sequencing: should Austin see water-flow phrase grammar v002 first, then the
   continuum as a separate second wave?

After any Austin review, record the per-output answers in
`docs/space-center/austin-consent-map.md` before any projector-facing or
public promotion. Nothing in the continuum ships public on a single blanket
"yes."

## 9. Acceptance Criteria

The lane is working visually when all five hold, with the evidence floor
attached:

1. **Reads as water cycle, not generic sacred geometry.** A viewer with no
   caption reads water / weather / a cycle - light, mist, rain, ripple, freeze,
   melt - not "mandala" or "flower of life." Concretely: the seven-phase order
   is legible without labels; the sixfold phase reads as crystallization /
   snow, not as a decorative rosette; no phase reads as all-over pattern fill.
2. **Primitive grammar visible but not pasted on.** Every visible
   circle/crescent/trigon is driven by a field-extracted cell, not a
   hand-placed icon. `primitive_audit` traces each rendered primitive back to
   one extracted source cell; the 6 v003 debug panels show the
   field -> nodal -> polarity -> class -> source chain. Cell-count caps are
   respected: 3-7 emitters (or 1 centre + 1-3 modes), 8-24 selected filled
   cells, 1-4 nodal groups, 0-2 six-ray candidates, no all-frame lattice.
3. **Loops cleanly.** The render is 2160 frames (indices 0-2159); frame 2159
   settles into the single-centre field-rest state and frame 0 *is* that state,
   so playing 2159 -> 0 is seamless - no visible cut, no crossfade. Verified by
   playing the rough cut 3x back-to-back.
4. **Can be muted / used as an internal R&D layer.** Black-screen layer-only;
   a single separable Resolume layer with a kill-switch; never a production
   dependency; the MVP-fallback production floor is provably unaffected.
5. **No public / cultural approval claim.** Every artifact - README, contact
   sheet, filename, sidecar - carries `internal_austin_review_needed`. No
   "Austin-approved," no "Coast Salish," no traditional-meaning claim;
   "radial topology," not "sacred geometry."

Evidence floor each render pass must attach (or be reported incomplete). This
matches the rendered v003 packet's actual structure - it is **not** the unmet
`interference-field-cell-taxonomy` Section 8 contract:

- README naming the lane, source references, cultural status, Austin boundary.
- A manifest JSON (field / source list), in the shape of
  `cymatic_field_topology_v003_manifest.json`.
- A `primitive_audit` JSON auditing every rendered primitive back to one
  extracted field cell, in the shape of `primitive_audit_v003.json` - this is
  the provenance record proving marks are field-extracted, not hand-placed.
- `debug_stills/` with the 6 v003 panels per clip: `scalar_field`,
  `nodal_lines`, `positive_negative_regions`, `cell_class_colors`,
  `source_points`, `debug_composite`.
- Contact sheet(s) showing final frames beside debug frames.
- Image dimensions and counts; `ffprobe` (duration, fps, codec, dimensions)
  for every MP4.
- `py_compile` for any changed or new script.
- Path checks for every doc, sheet, sidecar, and media file the review note
  cites.

If a reviewer later wants the taxonomy doc's dedicated `rejected_cells`,
`selected_cells`, or `six_ray_group` debug panels, adding them is a small
additive change to the renderer - worth noting as a possible follow-up, but not
a blocker for the phase studies.

Process gate: classification is done from stable `F(x,y)`, never from animated
`Z(x,y,t)` - confirm this in the README of every pass.

## 10. Next Worker Prompt

The following is a complete, copy-pasteable prompt for the next render worker.
It covers Worker Task 1 of Section 5 - the isolated phase studies.

```text
You are the Water-Cycle Phase-Studies render worker for Salish Sea Dreaming
Phase 2. Render seven isolated phase studies for the water-cycle continuum.

CONSTRAINTS (hard):
- INTERNAL ONLY. Not Austin-approved. No cultural-meaning claims. No public-use
  framing in any filename, README, or note.
- No SD / LoRA / style transfer. Deterministic scalar-field extraction only.
- No exact Austin source geometry, palette, faces, Thunderbird, serpent, named
  beings, salmon, fish, birds, or figures.
- Do NOT edit any other agent's script or output folder. Write only to your
  new folder.
- Verify every path before you cite it; report missing paths honestly.

PRECONDITION - B v003 is already rendered (verified 2026-05-20):
- The v003 packet
  track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/
  exists: 3 clips (sun_trigon_ring_v003.mp4, crescent_lens_field_v003.mp4,
  two_source_morph_v003.mp4), cymatic_field_topology_v003_manifest.json,
  primitive_audit_v003.json, debug_stills/ (6 panels per clip), contact sheets,
  README.md.
- v003 is a canonical-primitive legibility renderer, NOT a taxonomy Section 8
  classifier packet. Do not expect or require cell_records.json,
  classification_summary.csv, or debug_overlays/ - they do not exist and are
  not needed.
- Build the phase studies by extending the v003 renderer
  scripts/cymatic_field_topology_v003.py: import its field engine, cell
  classifier, and canonical-primitive machinery into a new sibling script (or
  copy that machinery if import is awkward). Do NOT edit v003's script or its
  output folder.

READ FIRST:
- docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md
  (this plan - Sections 2, 3, 6, 9)
- docs/space-center/water-cycle-cymatic-primitive-scene-language-2026-05-20.md
- docs/space-center/interference-field-cell-taxonomy-2026-05-20.md
- docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md
- track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/README.md

DELIVERABLE:
Seven black-screen layer-only phase studies, one per Section 3 phase:
  phase1_sun_radiant, phase2_vapor_mist, phase3_rain_onset,
  phase4_raindrops_on_water, phase5_standing_wave, phase6_snowflake,
  phase7_melt_return
- Each 6-10 s, 1920x1080, 24 fps, MP4 (H.264), rendered on #05070b near-black.
- Each uses the v003 field engine and cell classifier. Classify cells from the
  stable field F(x,y), NEVER from the animated display Z(x,y,t).
- Honor the source-list parameters in Section 6's per-phase table (symmetry
  order, mode, dominant taxonomy, source regime).
- Respect caps: 3-7 emitters (or 1 centre + 1-3 modes), 8-24 selected filled
  cells, 1-4 nodal-boundary groups, 0-2 six-ray candidates, no all-frame
  lattice. Preserve open negative space.
- Render circle / crescent / trigon / outline / compound with class-specific
  boundary language (line weight, opacity, persistence), NOT debug colours.
  Compound cells: faint ghost. Temporal hold ~0.4 s.

OUTPUT FOLDER (new - create it):
track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_<YYYY-MM-DD>/
(use the actual render date per repo folder convention)

EVIDENCE FLOOR (per study; a study missing any item is reported incomplete).
This matches the rendered v003 packet's structure - NOT the taxonomy Section 8
contract:
- A manifest JSON (field / source list), shaped like
  cymatic_field_topology_v003_manifest.json.
- A primitive_audit JSON auditing every rendered primitive back to one
  extracted field cell, shaped like primitive_audit_v003.json.
- debug_stills/ with the 6 v003 panels: scalar_field, nodal_lines,
  positive_negative_regions, cell_class_colors, source_points, debug_composite.
- A contact sheet showing final frames beside debug frames.
- README.md: lane, source refs, field family + seed, thresholds, class counts,
  selected-cell count, cultural status, Austin boundary, and an explicit line
  confirming classification was done from F(x,y) not Z(x,y,t).
- ffprobe output (duration, fps, codec, dimensions) for every MP4.
- py_compile for the new script.

DO NOT in this task:
- Do not render transitions or the assembled continuum - those are the next
  two worker tasks.
- Do not add salmon, fish, birds, figures, dream scenes, or audio reactivity.
- Do not make any phase public-ready or claim Austin approval.
- Do not lead with the standing-wave phase as a finished look - it is an
  internal legibility gate.

REPORT when done:
- Which of the seven studies passed the Section 9 acceptance criteria.
- Which failed or are unresolved, with the specific criterion.
- The verified output paths and the verification commands you ran.
- That the pass is internal-only and Austin-review-needed.
```

## Verification Notes

Verified from repository root `/Users/darrenzal/projects/salish-sea-dreaming`
on 2026-05-20:

- No rendering was performed for this plan. No Agent B script or output folder
  was edited. This document is orchestration / planning only.
- All eight task read-list documents were read in full. The ninth,
  `cymatic_field_topology_v003_2026-05-20/README.md`, was absent at the first
  draft and now EXISTS - the v003 packet was rendered 2026-05-20 ~20:00-20:10.
  It was re-verified on disk for this v2 revision (3 clips, manifest, primitive
  audit, 6-panel debug stills, contact sheets, README).
- All additional paths cited in this plan were path-checked and labelled
  EXISTS or PROPOSED. The `PROPOSED` paths
  (`water_cycle_continuum_v001.json`, the three `water_cycle_*` output folders)
  do not exist; this plan proposes them and they are flagged inline.
- Naming-collision risk was checked and reported: `cymatic_topology_cells_v003`,
  `cymatic_topology_cells_v004`, and `primitive_field_cycle_v003` exist but are
  different series and are NOT "B v003."

## Revision Notes

- v1 draft: 2026-05-20 ~19:57 - orchestration plan first written.
- v2 revision: 2026-05-20, post-adversarial-review. The review found two
  blockers: (B1) the v003 output folder was rendered ~3-13 minutes after the
  first draft, so the plan's "v003 absent" claim went stale; (B2) the plan
  defined "B v003" as a taxonomy-doc Section 8 classifier packet, but the
  rendered v003 is a canonical-primitive legibility renderer with a different
  evidence structure (manifest + `primitive_audit` + 6-panel `debug_stills/`).
  Resolved: the "Source & Path Verification" section, and Sections 3, 5, 9, and
  10, now reflect the rendered v003 packet and adopt its evidence structure as
  the floor. Five should-fix items were also resolved: the phase-order
  reconciliation is now stated honestly as a deliberate re-sequencing
  (Section 2); the transition morph vs test-clip duration is disambiguated
  (Sections 5, 6); the loop-point frame index is stated as 2160 frames /
  indices 0-2159 (Sections 2, 9); Phase 4's isolated-study contradiction was
  removed and the invented `raindrops_on_water_primitives_v003` filename
  deleted (Section 3); `tau`/`node_epsilon` are labelled as parameter ranges,
  not caps (Section 6).

## Build Status

- 2026-05-20: Worker Task 1 (seven isolated phase studies) COMPLETE and
  independently verified. Output: `water_cycle_phase_studies_v001_2026-05-20/`
  - 7 MP4s (1920x1080, 24 fps, 7-10 s), 42 debug stills, manifest,
  `primitive_audit`, contact sheet, README. New script
  `scripts/water_cycle_phase_studies.py` imports the v003 engine; v003 itself
  is untouched. All seven pass the Section 9 criteria. Two caveats accepted
  as-is and routed to Austin review: phase1 (sun) and phase6 (snowflake)
  rendered with no trigon cells (crescents + circles only); sun / melt /
  snowflake share a central-node + radiating-crescent structure.
- 2026-05-20: Worker Task 2 (six transition tests) COMPLETE and independently
  verified. Output: `water_cycle_transitions_v001_2026-05-20/` - 6 MP4s
  (1920x1080, 24 fps, 6.0 s), 42 debug stills, 6 morph-midpoint co-presence
  stills, manifest, `primitive_audit`, contact sheet, README. New script
  `scripts/water_cycle_transitions.py`; v003 and the Task 1 outputs untouched.
  All six pass Section 9 and the no-crossfade check (manifest confirms
  `crossfade: false` and both-phases-co-present at every morph midpoint).
- 2026-05-21: Worker Task 3 (assembled 90 s continuum rough cut) COMPLETE and
  independently verified. Output:
  `water_cycle_continuum_roughcut_v001_2026-05-21/` - master MP4 (exactly
  2160 frames / 90.000000 s / 24 fps / 1920x1080 / H.264, 28 MB), recipe
  `track2-deterministic/scene_recipes/water_cycle_continuum_v001.json` (schema
  valid; 7 phases tile 0-90 s contiguously; 7 transitions including the loop
  seam), manifest, `primitive_audit` (43,566 entries, all traced to a source
  cell), 6 v003 debug stills, contact sheet, loop-seam contact sheet, README.
  New script `scripts/water_cycle_continuum.py`; v003, Task 1, and Task 2
  outputs untouched. Passes all five Section 9 criteria. The clean-loop
  criterion 3 was reproduced independently (orchestrator-side, not by the
  worker): seam |frame 0 - frame 2159| mean = 0.926; reference adjacent
  |frame 1000 - frame 1001| mean = 1.754; the seam is 0.53x a typical
  adjacent-frame delta - structurally less perceptible than a normal frame
  step.
- BUILD ORDER COMPLETE. Next: internal (Pravin) review of the three
  deliverables, then Austin per-output review per plan Section 8. Two bounded
  Austin questions queued: phase1 (sun) and phase6 (snowflake) rendered with
  no trigon cells (crescents + circles only - arguably safer for the highest
  Austin-risk phase, but ask Austin whether radiant/sixfold should carry
  attached trigon tips at all); and sun / melt / snowflake structural
  adjacency (central node + radiating crescents - distinct enough through
  palette/motion/centre treatment, or one combined radial-grammar review?).
  Per `austin-consent-map.md`, log per-output answers before any
  projector-facing or public promotion.
