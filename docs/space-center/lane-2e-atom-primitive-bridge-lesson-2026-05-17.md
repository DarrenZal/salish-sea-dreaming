# Lane 2E lesson — atom-primitive-bridge is a routing rule, not a visual

2026-05-17 late session. Lane 2E POC v001 (largest-of-type pairs) and
v002 (spatial pairs) both rendered. Both failed to communicate the
concept visually because too few atoms move at scale to convey the
rule. Locked as labeled controls — do not promote.

## What the concept IS

When morphing Austin piece A → piece B, the two pieces typically have
DIFFERENT sets of atoms. Some atom pairs share primitive type
(circle↔circle, easy). Many don't (trigon→circle, crescent→circle).

The **primitive cycle (Circle / Crescent / Trigon)** is the *vocabulary*
for cross-type transitions: when a trigon needs to become a circle,
don't fade or path-resample — animate it through the
trigon→circle primitive morph clip. Each in-between shape is somewhere
on the Coast Salish primitive cycle, never an arbitrary AI invention.

## Why it's a rule, not a deliverable

The 3-atom POC failed because:
- Only 3 atoms move while everything else stays static → viewer reads
  it as "3 random shapes drifting," can't infer the rule
- Source/dest pieces fade behind → most of the visual is the fade, not
  the rule
- The "rule" isn't visible because it's only applied at miniscule scale

The full all-atoms version would mean animating 39 (Cosmic) → 242
(Salmon) atom mappings simultaneously. Likely too chaotic to be
beautiful, and the visual would compete with the rule it's trying to
demonstrate. Operator + peer judgment 2026-05-17 eve: don't build.

## Production use — how to apply the rule

When the operator or another lane wants to morph piece A → piece B
(e.g., the Cosmic_Sun → Salmon v006 in packet 01_lead_with/07), use
this routing logic to guide the morph engine:

1. **Build atom correspondences** by:
   - **Semantic role first** — eye-focal atoms in source route to eye-focal in
     dest (sun "eye" → salmon "eye"); fin-tail → fin-tail; formline-primary →
     formline-primary.
   - **Spatial position second** — for atoms without a clear semantic
     match, prefer pairs at matching positions (top → top, center → center).
   - **Primitive type third** — for unmatched atoms, prefer same-primitive
     pairs (circle → circle, trigon → trigon) over cross-type.

2. **Exclude from morph (treat as static or inpaint-only)**:
   - background-field
   - negative-space
   - very small atoms unlikely to register at projection scale
   - atoms tagged as "other" without a clear primitive type

3. **For cross-type transitions** (trigon → circle, crescent → circle, etc.):
   - Sample the appropriate `prim_*_to_*` morph clip at flight progress
   - Reverse the clip if the direction isn't directly available
   - Tint each frame with the interpolated atom color (src → dst)

4. **Composition**:
   - Source piece dissolves cleanly as atoms leave
   - Destination piece materializes as atoms arrive AT their target positions
   - Background atoms remain static under the morph (no global crossfade)

## Where this would have helped

- Cosmic→Salmon v006 (`packet 01_lead_with/07`) used path-resampling on
  the whole piece. The result has artifacts because trigons get morphed
  to non-trigon-shaped intermediates by the path resampler. Lane 2E
  routing would have routed each trigon to a roe via the trigon→circle
  primitive clip, giving culturally-grammar-consistent intermediates.

- Future Wolf↔Salmon, Raven↔Cosmic, TheCreator transitions can all
  use the same routing logic.

## Operator-surfaced caveat (no claim of meaningful correspondences)

The routing rule selects pairs by semantic / spatial / primitive
criteria, but it does NOT claim that any specific correspondence
("sun-ray top → roe top") is meaningful in Austin's worldview. Those
pairings are author-chosen for technical demonstration of motion
continuity. Any specific correspondence used in audience-facing output
needs Austin's per-output OK.

## Status

- Lane 2E POC v001 (largest-atom pairs): labeled control, do not promote.
- Lane 2E POC v002 (spatial pairs): labeled control, do not promote.
- Lane 2E **concept**: LOCKED as routing rule for future cross-piece
  morphs. Document this rule in any future morph engine spec.
- Lane 2E **visual deliverable**: parked. Would need either (a) the
  full all-atoms version (~1-2hrs, likely chaotic) or (b) an abstract
  toy demo (12 primitives → 12 primitives, no Austin pieces, ~30 min)
  to communicate the grammar cleanly.
