# Morph experiment lanes (Sun 2026-05-17 PM)

Captured after the cross-dissolve regression. Synthesizes the operator
+ peer-agent direction: keep the wild raw-morph energy (primitive motion
in middle), improve endpoint discipline without replacing transformation
with fading. Run lanes in parallel; preserve every branch with variant
filenames; iterate only on the promising ones.

**Cultural floor reminder:** all morph outputs are INTERNAL until Austin
sign-off on the specific clip. Per-output OK, not blanket OK. Cross-domain
pairs (Nature↔Animal, Animal↔Animal) need framing context from Austin
before any external share.

## Naming + provenance

See `track2-deterministic/morph_outputs_INTERNAL/VERSIONING_DISCIPLINE.md`.
TL;DR: no overwrites, variant suffix `_<lane>_v<NNN>.mp4`, composites
record their input set.

## Lane 1 — Improve original raw morphs (atom-snap endpoint)

**Hypothesis:** the raw morph's middle is the interesting part (primitive
motion, shapes colliding/morphing through each other). The endpoints
drift because path resampling doesn't reach exact target positions in
finite steps. Cross-fade was the wrong fix because it killed the motion.
**Atom-snap** is the right fix: in the final 10–15 frames, ease remaining
shapes into their exact target positions, preserving motion in the middle.

**Implementation sketch:**

- Start from existing morph-engine frame sequence.
- Render destination SVG to a high-contrast atom mask (per atom from
  decomposition output — we already have these).
- For frame i in [N-15..N-1]:
  - Compute easing factor e = (i - (N-15)) / 15
  - For each detected shape in morph frame: shift towards nearest atom
    position in destination by factor e²·(target - current)
  - In the very last 3 frames: alpha-blend remaining residue to destination
    SVG render to clear drift artifacts
- Output: `<pair>_atom_snap_endpoint_v001.mp4`

**Pairs to try first:**

- `raven_sun_to_salmon_spawn_atom_snap_endpoint_v001.mp4` (high interest)
- `cosmic_sun_to_salmon_spawn_atom_snap_endpoint_v001.mp4` (high interest)
- `raven_sun_to_cosmic_sun_atom_snap_endpoint_v001.mp4` (already clean — control)

**Effort:** 1–2 hours for v001; further refinement iterative.

**Risk:** atom-shape matching across pieces with different atom counts
needs assignment heuristic (e.g., Hungarian algorithm or geometric proximity).
Easy MVP: snap each surviving morph atom to nearest destination atom by
2D position; allow many-to-one (multiple residues collapsing into one
destination atom is visually OK at this stage).

## Lane 2 — Atom-aware transitions

**Hypothesis:** treat each piece as a set of atoms (which we have, via
decomposition: 504 atoms, 179 primitives across 5 pieces). Morph by
routing atoms semantically: sun rays → fish fins, sun circle → fish eye,
roe-as-particle-field, etc.

**Specific experiments:**

### 2A — Cosmic/Raven rays → Salmon roe particle field

The source has a small number of trigon rays radiating from a circle.
The destination has 184 roe-circles arranged in a wave pattern. Animation:
each trigon "shatters" into a stream of small circles that flow into
the roe positions.

- Use the trigon classifications from `cosmic_sun_atom_metadata.csv` and
  the pre-labeled roe atoms from `salmon_spawn_atom_metadata.csv`
- Particle simulation: trigon → N point sources → curl-noise flow toward
  assigned roe positions
- Output: `cosmic_sun_to_salmon_spawn_roe_particle_field_v001.mp4`

### 2B — Sun circle → Salmon central eye/pivot

The sun-center circle in Cosmic_Sun maps naturally to the central pivot
circle in Salmon_Spawn (the yin-yang focal oval). Animation: hold the
central circle constant while the rest of the source decomposes around
it and the salmon body recomposes around it.

- Output: `cosmic_sun_to_salmon_spawn_central_pivot_v001.mp4`

### 2C — Raven body → Salmon body contour

Raven's body silhouette and Salmon's body contour are both elongated
curved forms. Animation: dissolve raven body shapes into vectors of
motion, recompose as salmon body contour. Could pair with 2A for a
two-stream morph (raven body → salmon body + raven rays → roe).

- Output: `raven_sun_to_salmon_spawn_body_contour_v001.mp4`

### 2D — Wolf ↔ Salmon two-fold symmetry

Both Wolf and Salmon (or two-salmon spawn) compositions have two-fold
mirror symmetry. Animation: align symmetry axes, morph atom-pairs across
the axis (left wolf eye ↔ left salmon eye, right wolf eye ↔ right salmon
eye, etc.).

- Output: `wolf_to_salmon_two_fold_symmetry_v001.mp4`
- Risk: needs Wolf-piece atom-classification first (already done via
  sub-agent) — verify per-atom labels match the symmetry pairing.

**Effort:** 2–4 hours per experiment for v001.

## Lane 3 — Three primitives as core studies

The Coast Salish formline primitives (Circle/Oval, Crescent, Trigon) are
the visual grammar. Existing primitive cycle MP4 demos the basic morph.
Extensions:

### 3A — Primitive field

Many instances of each primitive arranged in a field, morphing
collectively: circles → roe pattern, trigons → ray pattern, crescents →
body/flow marks. Demonstrates the primitives at compositional scale.

- Output: `primitive_field_v001.mp4`

### 3B — Positive/negative inversion

Isolate a single atom (e.g., a beautiful Salmon eye-focal-oval), animate
positive/negative space inversion. The figure becomes the ground,
ground becomes figure. Highlights Austin's use of negative space as a
formline element.

- Output: `primitive_inversion_eye_focal_oval_v001.mp4`

## Lane 4 — More pair exploration

**Priority order:** same-viewBox pairs first (morph engine works cleanly
on these), then cross-scale pairs as atom-motion compositions (NOT as
whole-piece path morphs).

**Same-viewBox candidates** (108×108):
- Raven_Sun ↔ Cosmic_Sun (DONE, this is Exp 2)
- Need to check: are there other 108×108 pieces in austin-v2-ingest?
  - Check via: `for f in austin-v2-ingest/approved/*.svg; do
    head -3 "$f" | grep -E "viewBox|width"; done`

**Cross-scale candidates** (treat as atom-motion):
- Wolf (1500×1500) ↔ Salmon (1500×1500) — these MIGHT be same-viewBox
  actually; check
- Cosmic_Sun (108×108) ↔ Salmon (1500×1500) — cross-scale, Lane 2 territory
- Raven_Sun (108×108) ↔ Salmon (1500×1500) — cross-scale, Lane 2 territory
- TheCreator (?) ↔ pearl-bead mockup — symbolic resonance per the
  TheCreator atom_0114 + atom_0117 discovery

**Avoid:** cross-dissolve except as labeled control. The
`*_CURRENT_2026-05-17-1259_crossdissolve-regressed.mp4` files are
preserved as the control for "what fades look like, do not do this."

## Lane 5 — Catalog/decomposition continued

Already shipped:
- 504 atoms decomposed across 5 SVG pieces
- 179 primitives classified (43 circle / 78 crescent / 58 trigon)
- `atom_catalog.html` + `primitives_catalog.html`

Next:
- Re-classify Cosmic_Sun low-confidence atoms (Issue 5 from operator
  feedback: similar-looking atoms got different labels)
- Add a "similar atoms" cluster view (group atoms by visual hash, surface
  inconsistencies)
- VLM second-pass with explicit confidence + human correction queue

## Multi-pearl composite

Multi-pearl is a COMPOSITE — it inherits whatever lane outputs the underlying
edges use. Improvements to Lane 1 / Lane 2 propagate up automatically when
multi-pearl re-renders.

**Don't iterate on multi-pearl directly until at least one of:**
- Lane 1 atom-snap-endpoint v001+ is approved for the underlying pair
- Lane 2 atom-aware transition v001+ is approved for the underlying pair

When re-rendering, name as composite per VERSIONING_DISCIPLINE.md:
`multi_pearl_animation_v<NNN>__<edge1>=<lane>_v<XXX>__<edge2>=<lane>_v<XXX>__<edge3>=<lane>_v<XXX>.mp4`

## Priority for next 24h

Ranked by impact / effort:

1. **Lane 1 atom-snap v001** on raven_sun→salmon_spawn (the operator-liked
   pair) — preserves motion, fixes the endpoint drift complaint, ~1.5 hrs
2. **Lane 2A roe-particle-field v001** on cosmic_sun→salmon_spawn —
   strongest atom-aware transition because trigon→roe is semantically
   obvious; ~2 hrs
3. **Re-render multi-pearl** loading Lane 1 / Lane 2A outputs once
   approved; ~30 min
4. **Lane 3A primitive field** — demonstrates primitives at scale, low
   cultural risk, easy to show Austin without per-output friction; ~1.5 hrs
5. **Lane 2D wolf↔salmon two-fold symmetry** — strong concept, needs
   atom-pair verification first; ~3 hrs

Lower priority but valuable:
6. Catalog cleanup (Lane 5)
7. TheCreator pearl-bridge visual evidence composite (1 hr)
8. Atom-microscope (single beautiful atom extreme zoom)

## For 4pm Pravin call

**Show:** single-pearl traversal (`pearl-bead-prototype-2026-05-17/`),
primitive-cycle (`primitive-cycle-2026-05-17/`), atom catalog
(`atom_catalog.html` / `primitives_catalog.html`).

**Show with framing as "promising primitive-motion tests, not finished":**
the restored RAW shape-morph versions (`raven_sun_to_salmon_spawn.mp4`,
`cosmic_sun_to_salmon_spawn.mp4`). Set expectation: endpoint drift is the
known artifact; Lane 1 / Lane 2 are the lanes addressing it without
killing the primitive-motion quality.

**Do NOT show** the cross-dissolve versions (`*_CURRENT_*_crossdissolve-
regressed.mp4`). They are the control for "what we are NOT doing."

**Communicate:** five parallel experiment lanes, variant-naming discipline
locked in, multi-pearl composes from approved lane outputs only. This
shows Pravin that we have an architecture for parallel exploration, not
just a flailing iteration log.
