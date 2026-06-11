# Lane 2A v003 — Particles BUILD the destination (Codex worker spec)

Written 2026-05-17 PM after peer review of v001+v002. Claude work on
Lane 2A is paused; Codex worker owns v003. v001 and v002 preserved as
labeled variants (do not promote) — they demonstrate what we're not
trying to do.

## Why v001 + v002 are wrong direction

v001 timing bug (~40-frame blank middle) was a surface problem.
v002 fixed the timing but the architecture is wrong:

- Source and destination still composite as whole-image alpha layers
  (full-piece crossfades operator caught earlier — same failure pattern)
- Source rays don't visibly decompose — particles just appear from
  centroids while rays remain intact then fade as a layer
- Destination fades in as a complete artwork — so particles don't feel
  responsible for building it
- Particles are generic black circles, not Austin's roe color/form

## v003 rule changes (five corrections)

### 1. No full destination fade-in until final settle

Destination roe positions may appear as faint ghost targets (≤20% alpha
outlines), but the Salmon piece should NOT fade in underneath as a full
artwork. Audience should perceive the destination as ASSEMBLED by the
particles, not as a separate layer being revealed.

Final settle (last 5-10 frames): dest can crisp to full opacity once
particles have landed at roe positions and become them.

### 2. Particles inherit SOURCE color/form

- Source = Cosmic_Sun. Rays are wedge-shaped, dark on white (Austin's
  `#000000` fills).
- Particles must start as wedge/ray FRAGMENTS in Austin's palette —
  not generic black circles
- Use ray atom color from `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atom_metadata.csv`
  (`fill_color` column) — currently all `#000000` but check `isolated_png` /
  `context_png` for actual rendered color including any stroke/highlight

### 3. Particles must LAND ON roe atoms and become them

- Each particle's destination = exact roe centroid (already in
  `Animal_Salmon_Spawn_Eggs/atom_metadata.csv`, `centroid_x/y` columns,
  viewBox 1500×1500)
- On landing, particle transforms (morphs in shape/color over 5-10 frames)
  into Austin's roe rendering: small filled oval, roe color/scale
- Roe color: inspect a roe atom's `isolated_png` (e.g. `atom_0050.png` —
  pick any pre-labeled `egg-roe`). Likely Austin's signature roe red/orange.

### 4. Source rays VISIBLY decompose per batch launch

- Each source ray (10 trigons + 10 sun-rays from
  `Nature_Cosmic_Sun/atom_metadata.csv` where `ai_label IN
  ('trigon', 'sun-ray')`) owns a particle batch
- When a ray's batch launches, the ray itself BREAKS APART or DISSOLVES
  into the particles (rather than just fading as a separate layer)
- Implementation options:
  - Mask-based: render ray, then progressively erode/shatter via mask
    animation, with eroded pieces "becoming" the launching particles
  - Atom-replace: at launch moment, swap the ray's isolated PNG with the
    sum of its particle sprites in flight
- The visual contract: the ray's mass conserves into its particle batch

### 5. Clean underlay — no full-piece crossfades

- For v003, use white underlay (or very faint ≤15% alpha ghost of dest
  showing roe positions as outlines)
- Remove the full source/dest alpha-layer composites entirely
- This lets us evaluate the atom motion without it being masked by
  whole-image fades

## File outputs

- `cosmic_sun_to_salmon_spawn_roe_particle_field_v003_no_global_fade.mp4`
- Frames in `cosmic_sun_to_salmon_spawn_roe_particle_field_v003_no_global_fade/`
- Per VERSIONING_DISCIPLINE.md, never overwrite v001 or v002

## Inputs already available

- `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atom_metadata.csv` —
  39 atoms, 10 trigons + 10 sun-rays with centroids
- `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atoms/atom_NNNN.png` —
  isolated ray PNGs (transparent BG, exact Austin rendering)
- `austin-v2-ingest/decomposed/Animal_Salmon_Spawn_Eggs/atom_metadata.csv`
  — 242 atoms, 184 roe with centroids
- `austin-v2-ingest/decomposed/Animal_Salmon_Spawn_Eggs/atoms/atom_NNNN.png`
  — isolated roe PNGs
- `scripts/morph_roe_particle_field.py` — v002 implementation as
  reference for grid math + bezier paths; rewrite the rendering core

## Effort estimate (Codex)

- Read v002 script for path/assignment scaffolding (15 min)
- Replace particle rendering with sprite-based (read atom PNGs at small
  scale, color-shift on landing) (60 min)
- Replace whole-image layer fades with ray decomposition + ghost outlines
  (60 min)
- Iterate timing + visual polish (30-60 min)

Total: 2-3 hrs

## Decision gate

After v003 renders, side-by-side comparison with:
- `cosmic_sun_to_salmon_spawn.mp4` (raw shape morph — operator-liked but
  broken)
- `cosmic_sun_to_salmon_spawn_roe_particle_field_v001.mp4` (control,
  blank middle)
- `cosmic_sun_to_salmon_spawn_roe_particle_field_v002.mp4` (control,
  full-piece crossfade)
- `cosmic_sun_to_salmon_spawn_roe_particle_field_v003_no_global_fade.mp4`
  (the right architecture)

Operator decides whether v003 is shareable with Pravin / Austin. Per
cultural floor: no external surface without Austin per-output OK.
