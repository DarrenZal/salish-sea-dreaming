# Austin piece-pair scouting report — top 5 candidates for future morph experiments

Generated 2026-05-17 overnight per priority #3 of operator's sleep brief.
**No new renders produced** — this is a recommendation document only.

## Methodology

For each candidate pair, scored across:

| Criterion | Weight | Notes |
|---|---|---|
| viewBox/scale compatibility | High | same-scale pairs morph cleanly; cross-scale needs Lane 2E routing rule |
| Shared primitive vocabulary | High | overlap in circle / crescent / trigon atom counts |
| Symmetry compatibility | Medium | radial / 2-fold rotational / bilateral pairings |
| Narrative/aesthetic promise | Medium | meaningful pairing in ecosystem or worldview |
| Cultural risk | Critical filter | Austin's per-output OK required; some pairs need pre-discussion before any visual |

**Restricted explicitly per operator**: Wolf ↔ Thunderbird-Background. Not rendered, not recommended.

## Inventory of decomposed pieces

| Piece | viewBox | Atoms | Dominant primitives | Symmetry | Cultural load |
|---|---|---|---|---|---|
| Nature_Cosmic_Sun | 108×108 | 39 | 10 trigon, 10 sun-ray, 8 crescent, 4 circle | radial | medium |
| Animal_Bird_Raven_Sun | 108×108 | 29 | 10 trigon, 5 sun-ray, 1 circle | radial (with bird overlay) | medium-high |
| Animal_Wolf_Spindle_Whorl | 1500×1500 | 63 | 16 trigon, 16 crescent, 12 formline-tertiary, 3 circle | 2-fold rotational | HIGH (Wolf ancestor + Spindle whorl ceremonial) |
| Animal_Salmon_Spawn_Eggs | 1500×1500 | 242 | 184 egg-roe (circles), 10 crescent, 4 circle, 1 trigon | 2-fold rotational (yin-yang) | medium-high |
| Supernatural_Human_TheCreator_Background | 1500×1500 | 131 | 44 crescent, 31 circle, 21 trigon, 15 body-element | bilateral (with central figure) | VERY HIGH (creator/origin figure) |

Pieces in `austin-v2-ingest/training/` but NOT yet decomposed: Bear_Background, Bird_Heron_Background, Bird_Raven_Transparent, Deer_Background, Insect_Bee, Insect_Butterfly_Transparent, Water_Octopus_Transparent, Water_Orca_Transparent, Bird_Thunderbird_Background, Snake_Serpent, Transformer_Background.

## All decomposed-pair combinations (10 pairs)

| Pair | viewBox match | Shared primitives | Symmetry match | Narrative | Cultural risk | Note |
|---|---|---|---|---|---|---|
| Cosmic_Sun ↔ Raven_Sun | ✓ (108×108) | very high (trigon+sun-ray+circle) | ✓ radial | sun in two forms | medium | **ALREADY SHIPPED** as `01_lead_with/05_raven_sun_to_cosmic_sun_shape_morph.mp4` |
| Cosmic_Sun ↔ Wolf_Spindle | ✗ cross-scale | medium (trigon+crescent+circle) | mixed (radial→2fold) | cosmic ↔ ancestor | HIGH (Wolf) | Cross-scale + cultural risk; defer |
| Cosmic_Sun ↔ Salmon_Spawn | ✗ cross-scale | low (only circle overlap) | mixed | sun-energy ↔ life-cycle | medium-high | Already attempted via raw + endpoint-emerge (failed) and v006 (better, in packet); next iteration via Lane 2E routing rule |
| Cosmic_Sun ↔ TheCreator | ✗ cross-scale | high (circle+crescent+trigon) | mixed | sun ↔ creator | VERY HIGH | Defer until Austin guides |
| Raven_Sun ↔ Wolf_Spindle | ✗ cross-scale | medium (trigon+circle) | mixed | trickster ↔ ancestor | HIGH | Strong narrative but defer |
| Raven_Sun ↔ Salmon_Spawn | ✗ cross-scale | low | mixed | predator ↔ prey | medium-high | Already attempted via raw morph (in packet 02_ask_first as broken control); revisit only after Lane 2E rule mature |
| Raven_Sun ↔ TheCreator | ✗ cross-scale | medium (trigon+circle) | mixed | trickster ↔ creator | VERY HIGH | Defer |
| Wolf_Spindle ↔ Salmon_Spawn | ✓ (1500×1500) | high (crescent+trigon+circle) | ✓ 2-fold | ancestor ↔ provider; predator ↔ prey | HIGH | Same-scale + 2-fold match = clean geometry; HIGH cultural load means: discuss with Austin before any visual. Already exists as `wolf_whorl_to_salmon_spawn` in 02_ask_first packet (high-load, do not lead) |
| Wolf_Spindle ↔ TheCreator | ✓ (1500×1500) | very high (crescent+trigon+circle+body) | mixed | ancestor ↔ creator | VERY HIGH | Same-scale + dense atom set = strong morph candidate IF Austin permits; until then defer |
| Salmon_Spawn ↔ TheCreator | ✓ (1500×1500) | high (crescent+circle+formline) | mixed | life cycle ↔ origin | VERY HIGH | Same-scale + narrative resonance with TheCreator pearl-bridge observation. Defer until Austin guides |

## Top 5 recommendations

Ordered by combination of: technical promise (geometric compatibility), narrative depth, and feasibility-given-cultural-load. Each picks the FIRST experiment that's low-risk to start.

### 1. Cosmic_Sun ↔ Salmon_Spawn — apply Lane 2E routing rule to v006

**Status**: v006 already in packet as best cross-piece primitive-motion candidate. Has known artifacts (path-resampling generates non-primitive intermediates).

**Why top**: Already approved by operator for show consideration; primitive types align (trigon→circle pathway clear: sun-rays → roe); cross-scale is mitigated by Lane 2E routing (each atom independently mapped).

**Recommended first experiment** (post-Austin-OK):
- Apply Lane 2E routing rule to refine v006
- Trigons (sun-rays) route to top roe atoms via prim_trigon_to_circle clip
- Crescents route to formline-secondary positions
- Circle-ovals route to egg-roe + circle-oval positions
- Inpaint cosmic background; salmon background materializes as atoms arrive
- Effort: ~3-4 hrs to implement, test
- Cultural load: medium (least restrictive of the cross-piece options)

### 2. Wolf_Spindle ↔ Salmon_Spawn — discussion with Austin first

**Status**: Exists as 02_ask_first/04_wolf_whorl_to_salmon_high_load_do_not_lead.mp4 (raw morph, known high cultural load).

**Why top**: Same viewBox 1500×1500, both 2-fold rotational, very strong narrative pairing (ancestor / provider; predator / prey). Best same-scale candidate.

**Cultural risk**: HIGH on both sides. Wolf is ancestor; Salmon is foundational. The pairing implicates Coast Salish foodways and clan relationships.

**Recommended first experiment**:
- **NOT a render**. First step is an Austin conversation: "We see geometric and narrative resonance here. Is this a pairing you'd want explored, or kept apart? What would respectful animation look like — and what would not?"
- If Austin OK: apply v005-style swim rig to both wolves AND both salmon simultaneously; render in-place (both at rest positions, both breathing/swimming). NO cross-piece morph yet.
- Effort: 1 conversation, then ~1 hr render if approved
- Cultural load: HIGH — handle accordingly

### 3. Cosmic_Sun ↔ Raven_Sun — already shipped; investigate sub-grammar

**Status**: 05_raven_sun_to_cosmic_sun in packet 01_lead_with.

**Why top**: Already validated. Both 108×108, both have radial sun-ray geometry. Strong primitive vocabulary overlap.

**Recommended next experiment**:
- Atom-level analysis: which of Raven_Sun's atoms correspond to Cosmic_Sun atoms? Build a correspondence catalog (similar to TheCreator pearl-bridge composite) showing how the morph routes.
- This becomes a teaching artifact: "Lane 2E routing rule applied to a same-scale pair."
- Effort: ~1 hr (analysis + visualization)
- Cultural load: medium

### 4. Animal_Bird_Heron_Background ↔ Animal_Salmon_Spawn_Eggs — decompose Heron first

**Status**: Heron not yet decomposed. Salmon already done (242 atoms).

**Why top**: Heron + Salmon = predator/prey ecology pair from same watershed. Lower cultural load than Wolf/Thunderbird/TheCreator pairs. Natural narrative ("the heron fishes the spawning ground").

**Recommended first experiment**:
- Run `scripts/decompose_austin_pieces.py` on Bird_Heron_Background.svg (if SVG exists; otherwise needs source from Austin)
- Build atom catalog
- Apply Lane 2E routing: heron body → salmon body forms; heron beak (trigon-like?) → salmon fin-tail
- Effort: ~30 min decompose + ~3 hrs morph build
- Cultural load: medium

### 5. Animal_Water_Orca_Transparent ↔ Animal_Water_Octopus_Transparent — decompose both first

**Status**: Neither decomposed. Both "transparent" (no background) = simpler geometry.

**Why top**: Pure Salish Sea marine creatures, both deep cultural significance but no `_Background` qualifier suggests they're standalone figures rather than ceremonial compositions. Lower cultural load.

**Recommended first experiment**:
- Decompose both
- Apply v005-style swim rig to Orca (already proven on Salmon)
- Then apply same to Octopus
- Cross-piece morph as Lane 2E POC at higher complexity than today's
- Effort: ~1 hr decompose + ~1 hr per-piece swim rig
- Cultural load: medium (Orca + Octopus both meaningful but transparent variants suggest secular/educational use OK)

## Pairs explicitly NOT recommended for rendering

| Pair | Reason |
|---|---|
| Wolf_Spindle ↔ Bird_Thunderbird_Background | Operator-restricted |
| TheCreator ↔ anything | VERY HIGH cultural load; needs Austin's explicit framing first |
| Wolf_Spindle ↔ TheCreator | Both very high load; combination amplifies |

## Operational notes

- **Cross-scale routing rule** (Lane 2E lesson doc): for pairs spanning 108×108 ↔ 1500×1500, use atom-level routing instead of whole-piece path-resampling. Document at `docs/space-center/lane-2e-atom-primitive-bridge-lesson-2026-05-17.md`.
- **Decomposition pipeline**: `scripts/decompose_austin_pieces.py` can run on any SVG in `austin-v2-ingest/approved/`. Outputs atom_metadata.csv + per-atom PNGs.
- **First-pass classification**: sub-agent labels via 15-class formline taxonomy. May need re-classification pass for low-confidence atoms.
- **Per-output Austin OK** required for any audience-facing use, regardless of cultural-load tier.
