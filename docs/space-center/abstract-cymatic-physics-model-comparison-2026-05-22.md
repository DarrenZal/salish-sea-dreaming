# Abstract Cymatic Physics Model Comparison - 2026-05-22

Status: INTERNAL planning note. Defines the evaluation framework for two
in-flight abstract cymatic physics probes. No rendering performed by this
document. Not Austin-approved as external output, not a cultural-meaning
claim, not a public-use guidance note.

## 1. Problem being solved

Prior probes in this lane (radial choreographer v001-v004; flower-of-life
emergence v001; several earlier integrated choreographer packets) repeatedly
fell into the same failure mode: the wave/field math ran underneath, but the
visible circles, crescents, and trigons that read on the wall were drawn as
symbolic overlays on top of that field rather than derived from the field
itself.

This produced two coupled problems:

- The renderer asserted "primitives emerged from the field" while in practice
  the primitives were authored shapes pasted into field-shaped composition
  slots; the field was decoration, not source.
- Iteration kept tuning the overlay layer, which masked the question of
  whether the underlying physics can actually carry readable primitive forms.

The two current probes are designed to settle that question by forcing the
visible primitive forms to come out of field features themselves.

- **Path A.** Delayed analytic ripple / wavefront overlap-count masks. Multiple
  analytic ripple sources fired at offset times; the visible primitives are
  taken from regions where wavefronts overlap (count >= threshold).
- **Path B.** 2D wave-equation / field-feature masks. A discretized wave PDE
  evolved over the canvas; the visible primitives are taken from features of
  the resulting field (e.g. extrema, zero-crossings, gradient ridges, phase
  contours).

## 2. Shared renderer contract

Both probes must honor the same authoring contract for this comparison to be
meaningful:

- **Primitive forms (circle, crescent, trigon) must come from field-derived
  masks or count/feature maps.** No drawn paths, no SVG primitives composited
  on top of the field, no pre-authored shape templates blended in.
- **Provenance must show the mask.** Each result packet must include the
  peak overlap/count/feature map for at least one representative frame so
  that an operator can visually confirm the primitive's shape corresponds to
  a region of the underlying field.
- **The field is the source, not the backdrop.** Color, opacity, smoothing,
  blur, and palette are allowed as styling on the derived mask; they are not
  allowed as a way to insert form that the mask did not contain.
- **No rescue overlays.** If the field doesn't carry the primitive cleanly,
  that is a result, not a problem to paper over with an overlay.

A probe that violates this contract is automatically rejected for this
comparison regardless of how beautiful the final render is. The point of the
comparison is to learn whether either physics model can carry the primitive
grammar; a probe that smuggles primitives back in via overlay tells us
nothing about that.

## 3. Evaluation priority

Apply in order. Earlier criteria gate later ones; a probe that fails an
earlier criterion is not rescued by performing well on a later one.

1. **Field-derived primitives (gate).** Are circle, crescent, and trigon
   forms actually visible in the count/feature mask itself? If primitives
   come from overlays rather than from the field, automatic reject.
2. **Visual readability.** Among probes that pass (1), how clearly do
   circles, crescents, and trigons read on the wall? Sharpness of form,
   separation from background, freedom from muddled or arrow-like
   degenerate variants. Read at projector scale, not at thumbnail scale.
3. **Loop usability.** Among probes that pass (1) and (2), how seamlessly
   does the result loop for Resolume / library use? Loop quality is
   important but secondary; a non-looping pass on (1) and (2) is still a
   useful renderer direction and can be made loopable later.

Explicit anti-rule: do not choose a beautiful loop if it fails (1). A
visually striking result that smuggled primitives in via overlay is the
exact failure mode this comparison was set up to detect.

## 4. Required comparison evidence

For each probe (A and B), the result packet must include:

- **Peak overlap/count/feature map only.** A single still showing the raw
  field-derived mask at the peak frame, with no compositing, no overlay, no
  styling. This is the gate-1 evidence.
- **Final peak render.** A single still of the styled output at the same
  peak frame.
- **Spatial correspondence.** The visible primitive forms in the final peak
  render must spatially correspond to features in the peak mask. The pairing
  of these two stills (mask vs render) is the operator-checkable gate.
- **Optional but preferred.**
  - Short clip (2-5 seconds) at native resolution showing the field
    evolution into and out of the peak frame.
  - A second peak frame from a different parameter point in the same probe,
    to show the form is parameter-stable rather than a single lucky frame.
  - Loop diagnostic image and JSON metrics if a looped render exists (same
    schema as `scripts/telus_abstract_cymatic_batch.py` loop diagnostics).

Missing the mask still or the peak render still is sufficient to defer the
probe for re-render before evaluation. Do not evaluate by render-only
material.

## 5. What each result would mean

There are four outcomes; each has a clear next step.

- **Path A passes (only).** Delayed analytic ripple / wavefront overlap
  count masks can carry the primitive grammar. The existing analytic
  approach becomes the production renderer direction for cymatic loops in
  this lane. Continue to evolve A; B parked.
- **Path B passes (only).** Field-feature masks from the 2D wave equation
  carry the primitive grammar. The physical simulation approach becomes a
  new renderer direction; queue follow-on work on solver parameters, mask
  extraction recipes, and loop strategies for B. A may still be useful as a
  fast/cheap variant but is no longer the lead.
- **Both pass.** Compare on visual quality at projector scale and on loop
  practicality (FPS, file size, seamlessness, parameter stability). Pick the
  lead direction; retain the other as a secondary renderer slot. Field-
  derived primitive emergence is then confirmed as a real architecture, not
  an artifact of one specific math choice.
- **Neither passes.** The primitive grammar cannot be reliably carried by
  either of these field physics directly. Step out of the field-derivation
  lane for primitives and write a small reference implementation
  ("primitive composition renderer v001" per
  [primitive-composition-renderer-pivot-plan-2026-05-21.md](primitive-composition-renderer-pivot-plan-2026-05-21.md))
  that authors primitives directly while using wave/field outputs as
  atmosphere, motion, opacity, and reveal. This is the documented pivot
  path; it is not a defeat outcome, it is a deliberate redirection of
  authority from emergence to authoring with field as accompaniment.

## 6. Austin / protocol framing

Per [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md),
Austin has greenlit Austin-style / Coast Salish-style generated experiments
(including primitive emergence work and cymatic-field probes) for internal
and show-development scope on this project. Both Path A and Path B fall
within that authorization.

Constraints that remain in force:

- Austin remains the authority on meaning and on final external use. This
  comparison is internal renderer evaluation, not a clearance to ship.
- Outputs from either probe carry the Austin-authorized internal label per
  the authorization expansion note (Section 4 of that note) until and unless
  Austin OKs a specific output for external use.
- The whole-vs-support distinction holds: these probes produce
  generated-support compositions, not decompositions of Austin's whole
  authored sources.
- "No invented-from-scratch crests" still applies. Style/grammar emergence
  is in scope; crest invention is not. Bring representative outputs from
  the winning path to Austin review.

## 7. Evaluation priority when both paths return

Restated as a single check ordering for the operator at evaluation time.

1. **Field-derived primitives.** Reject any probe whose visible primitive
   forms come from overlays rather than count/feature masks. This is a hard
   gate. Confirm by inspecting the mask still alongside the render still.
2. **Visual readability.** Among the field-derived passes, choose the one
   where circles, crescents, and trigons read most clearly on the wall at
   projector scale.
3. **Loop usability.** Among the readable, field-derived passes, prefer
   the result that loops more seamlessly for Resolume / library use. A
   non-looping result that passes (1) and (2) is still useful as a renderer
   direction and can be made loopable in a follow-on pass.
4. **Anti-rule.** Do not choose a beautiful loop if it fails (1). A
   striking loop that smuggled in primitives via overlay is a re-instance
   of the exact failure mode this comparison exists to detect.

If neither passes (1), record the negative result honestly, archive both
probe packets with their mask stills as evidence, and proceed to the
primitive-composition-renderer pivot rather than reopening either probe in
its current architecture.

## 8. Linked records

- [primitive-composition-renderer-pivot-plan-2026-05-21.md](primitive-composition-renderer-pivot-plan-2026-05-21.md)
  -- the documented pivot if both probes fail the field-derivation gate.
- [telus-abstract-cymatic-rendering-notes-2026-05-21.md](telus-abstract-cymatic-rendering-notes-2026-05-21.md)
  -- TELUS batch render harness, loop diagnostics schema, contact sheet
  conventions used here as the format for comparison evidence.
- [arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md)
  -- arc-bounded scalar-field lane that motivated the gate against overlay-
  smuggled primitives.
- [primitive-grammar-contract-2026-05-19.md](primitive-grammar-contract-2026-05-19.md)
  -- shared primitive vocabulary (circle / crescent / trigon) referenced by
  both probes.
- [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md)
  -- Austin authorization scope under which both probes run.
- [austin-consent-map.md](austin-consent-map.md) -- operator sign-off log of
  record; per-output Austin review remains the floor for external use of
  any output from either probe.

## 9. Verification

- ASCII-only content; no non-ASCII characters introduced by this note.
- No rendering, no SVG edits, no scripts modified, no generated artwork
  produced by this note.
- Scoped to one new markdown file at
  `docs/space-center/abstract-cymatic-physics-model-comparison-2026-05-22.md`.
- All internal markdown links resolve to existing files in
  `docs/space-center/` (verified by file listing at write time).

Recorded by: operator session, 2026-05-22.
