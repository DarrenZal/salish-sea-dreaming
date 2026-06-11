# Arc-Bounded Region Rendering Notes - 2026-05-21

Status: INTERNAL ONLY. Markdown note for the next v003/v004 renderer pass. No
rendering performed. This is technical rendering guidance, not Austin approval,
not public-use guidance, and not a cultural construction claim.

Read with:

- [interference-field-cell-taxonomy-2026-05-20.md](interference-field-cell-taxonomy-2026-05-20.md)
- [primitive-svg-reference-validation-2026-05-21.md](primitive-svg-reference-validation-2026-05-21.md)
- [motion-physics-to-primitive-grammar-2026-05-20.md](motion-physics-to-primitive-grammar-2026-05-20.md)
- [primitive-grammar-visual-acceptance-criteria-2026-05-20.md](primitive-grammar-visual-acceptance-criteria-2026-05-20.md)

## What v003 Needs

v003 should stop trying to place clean detached symbols over a field. The
renderer should reveal field-shaped, arc-bounded regions: cells whose edges
come from wavefronts, nodal boundaries, source rings, intersections, and
negative-space cuts.

The output can still read as circle-like, crescent-like, or trigon-like, but
the primitive must grow from the field boundary. Debug frames must preserve the
raw extracted contour before any beauty-render canonicalization.

## Arc-Bounded Crescents vs Blunt Oval Field Cells

Arc-bounded crescents are two-arc relationships. They have a visible outer arc,
a visible inner/cupping arc, two cusp endpoints, and a declared cup direction.
The viewer should be able to see what the crescent cups, follows, or cuts
against.

Blunt oval field cells are different. A smooth antinode island can be useful as
a pressure body, eddy, source region, or compound cell, but it should not be
called a crescent just because it is elongated. If the two-arc relation is not
visible, classify it as oval/circle-like/compound in review language.

For beauty renders, a raw lens or vesica-like cell may be canonicalized toward
a moon-style crescent only when metadata maps back to the source cell, centroid,
bounds, orientation, raw contour, and canonical parameters.

## Trigon-Like Gaps From Negative Space

Trigon-like forms should come from intersections, cusp regions, or negative
space where multiple wavefronts press against each other. Good candidates are:

- three wavefront arcs meeting around a gap;
- a negative cutout pinched between two positive cells and one nodal boundary;
- an attached release point at the end of a crescent/lens flow;
- a scallop-like cusp where a radial source ring is interrupted by another
  field.

Do not draw a standalone triangle and call it a trigon. Trigon-like wave cusps
are renderer hypotheses derived from scalar-field behavior, not cultural
construction claims.

## Why Detached SVG/Glyph Overlays Failed

Detached SVG or glyph overlays failed because they ignored the field that was
supposed to generate them. The crescent became a moon stamp; the trigon became
an arrowhead, spike, or play-button triangle; and the field underneath became a
background instead of the source of the primitive.

The failure mode is attachment. A glyph floating above a current, ring, or
interference field does not prove provenance. The next pass should render the
raw cell boundary, then optionally stylize that same boundary. If a primitive
cannot be traced back to a source cell or boundary operation, reject it.

## Visual Checks

Use these checks before accepting any v003 still or loop:

- Cusp sharpness: crescents have two controlled cusp endpoints; trigons have
  three curved corner/release regions, not blunt blobs or hard UI points.
- Concavity: crescents cup a source, path, void, or neighboring cell; concavity
  is not flipped at random.
- Attachment: trigon-like releases attach to a ring, cell, crescent, or
  negative-space cut; no detached arrows or floating rays.
- Interlock: positive cells, negative cutouts, and wavefront arcs fit together
  as one field. The primitive should feel cut from the same membrane, not pasted
  on top.
- Provenance: debug overlays show raw contours, source IDs, polarity, centroid,
  bounds, orientation, and selected/canonical render parameters.
- Density: enough open space remains for boundary language to read. Dense
  scatter hides cusp, concavity, attachment, and interlock failures.

## Acceptance Rule

Accept field-shaped primitives only when the beauty render and the debug render
agree on provenance. If the beauty render reads better only because it hides the
raw field boundary, keep it as a failed style test rather than a v003 candidate.
