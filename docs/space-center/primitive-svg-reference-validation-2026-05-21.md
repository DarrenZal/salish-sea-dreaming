# Primitive SVG Reference Validation - 2026-05-21

Status: INTERNAL Agent E validation pass. No SVGs edited. No images rendered. No cultural approval claims. This checks current primitive SVG references against internal renderer-shape requirements only.

## Baseline Shape Requirements

- Circle: deliberate origin / impact / pivot / orb; no accidental paired-eye or roe read.
- Crescent: cups an origin or follows a path; cusps and body thickness must be controlled; avoid isolated moon-stamp use.
- Trigon: curved pointed primitive with attached/rear relation; avoid generic triangle, UI arrow, play-button, or detached spike.
- Renderer refs should avoid source-specific palette, exact Austin atom adjacency, and embedded white backgrounds unless explicitly handled.

## Per-SVG Findings

### `track2-deterministic/source-vectors/primitives/circle_oval_coast_salish_v1.svg`
- Primitive type: circle.
- Gets right: clean centered closed form; useful as origin, impact, orb, or pivot reference; no eye-pair risk by itself.
- Gets wrong: named circle/oval but only circle; includes white rect background and stroke; no role metadata.
- Future renderer reference: usable.
- Recommended use: use.
- Specific notes: crescent/trigon notes n/a; canonical for circle outline/fill fitting after background removal.

### `track2-deterministic/source-vectors/primitives/crescent_coast_salish_v1.svg`
- Primitive type: crescent.
- Gets right: coherent cupping crescent with substantial body; reads as a held bowl/phase mark rather than thin decorative moon.
- Gets wrong: symmetric and fixed-orientation; cusps are blunt; thick body may overpower small water phrases; includes white rect.
- Future renderer reference: usable for gross crescent silhouette, not final cusp tuning.
- Recommended use: use with caution.
- Specific notes: cusps need sharper/role-adjustable variants; body thickness is useful as a high-thickness limit; no trigon/arrowhead issue.

### `track2-deterministic/source-vectors/primitives/trigon_coast_salish_v1.svg`
- Primitive type: trigon.
- Gets right: elongated curved point, broad rear base, and non-equilateral outline; better than generic triangle.
- Gets wrong: extreme vertical elongation can read as arrowhead/spike when isolated; side concavity is subtle; includes white rect.
- Future renderer reference: usable as primary trigon geometry baseline with orientation/role constraints.
- Recommended use: use with caution.
- Specific notes: trigon concave sides need renderer exaggeration controls; elongation is useful but should be capped for water; arrowhead risk is moderate if detached from crescent/origin.

### `track2-deterministic/source-vectors/primitives/prim_circle_oval_extracted_cosmic_sun.svg`
- Primitive type: circle / orb, source-extracted.
- Gets right: clean arc-based central orb with no background; useful geometry example for radial emitter fitting.
- Gets wrong: source-specific fill color and exact extracted source relationship; not neutral; not an oval.
- Future renderer reference: usable only as private source-derived orb reference, not canonical generic circle.
- Recommended use: use with caution.
- Specific notes: crescent/trigon notes n/a; avoid palette transfer and exact Austin sun-face context reuse.

### `track2-deterministic/source-vectors/primitives/prim_crescent_extracted_wolf_moon.svg`
- Primitive type: crescent, source-extracted.
- Gets right: asymmetric crescent with more organic thickness variation than the synthetic crescent.
- Gets wrong: source-derived from a high-caution context; palette/source identity are not neutral; moon-like C-shape can become decorative if detached from origin/path.
- Future renderer reference: not suitable as canonical renderer input; private morphology comparison only.
- Recommended use: do not use.
- Specific notes: cusp behavior is more natural but source-bound; body thickness varies well; no trigon/arrowhead issue.

### `track2-deterministic/source-vectors/primitives/prim_trigon_synthesized_reference.svg`
- Primitive type: trigon, synthesized.
- Gets right: compact Bezier trigon with no background; curved sides and broad rear base are easier for renderer fitting than point-sampled paths.
- Gets wrong: synthesized, not source-grounded; broad top-to-base silhouette can still read as arrowhead/rocket when isolated.
- Future renderer reference: usable as a temporary renderer proxy, not canonical shape truth.
- Recommended use: use with caution.
- Specific notes: concave sides are mild; elongation is lower than `trigon_coast_salish_v1`; arrowhead risk remains if not attached to crescent/origin.

### `track2-deterministic/decomposed/coast_salish_primitives/circle_oval_coast_salish_v1.svg`
- Primitive type: circle.
- Gets right: byte-identical to `source-vectors/primitives/circle_oval_coast_salish_v1.svg`; same clean origin geometry.
- Gets wrong: duplicate with same white rect/stroke and no oval variant.
- Future renderer reference: usable, but avoid maintaining two divergent canon paths.
- Recommended use: use.
- Specific notes: crescent/trigon notes n/a; treat as duplicate canonical circle copy.

### `track2-deterministic/decomposed/coast_salish_primitives/crescent_coast_salish_v1.svg`
- Primitive type: crescent.
- Gets right: byte-identical to `source-vectors/primitives/crescent_coast_salish_v1.svg`; same robust thick crescent body.
- Gets wrong: duplicate with blunt cusps, fixed orientation, white rect, and high body weight.
- Future renderer reference: usable as duplicate only.
- Recommended use: use with caution.
- Specific notes: cusps require sharpening controls; body thickness is a max-weight reference, not the only crescent profile.

### `track2-deterministic/decomposed/coast_salish_primitives/trigon_coast_salish_v1.svg`
- Primitive type: trigon.
- Gets right: byte-identical to `source-vectors/primitives/trigon_coast_salish_v1.svg`; same elongated non-generic trigon.
- Gets wrong: duplicate with moderate arrowhead/spike risk when isolated; white rect included.
- Future renderer reference: usable as duplicate only.
- Recommended use: use with caution.
- Specific notes: concave sides need tunable emphasis; elongation is a high-end bound for water overlays; attach to phrase context to reduce arrowhead read.

## Cross-Cut Validation Notes

- The neutral generated circle/crescent/trigon trio is the better renderer baseline than source-extracted fragments.
- White background rects are present in the generated trio and decomposed duplicates; renderers should isolate the filled path, not use the full SVG as-is for overlays.
- Existing crescent references do not cover thin, mist, wake, or small rain-impact crescents; new renderer parameters should vary cusp sharpness, arc angle, and thickness without editing these SVGs.
- Existing trigon references cover elongated and compact cases but not enough side-concavity variation; renderer should expose concavity/base-flatness controls.
- Source-extracted wolf/cosmic fragments should not become canonical overlay refs because they carry source/palette/context load.

## Recommended Canonical Refs For Future Overlay/Fitting Work

| Primitive | Canonical ref | Recommendation | Use notes |
|---|---|---|---|
| Circle | `track2-deterministic/source-vectors/primitives/circle_oval_coast_salish_v1.svg` | use | Strip background; use for origin/orb/impact fitting. |
| Crescent | `track2-deterministic/source-vectors/primitives/crescent_coast_salish_v1.svg` | use with caution | Use as thick-body baseline; add renderer-side cusp/thickness variants. |
| Trigon | `track2-deterministic/source-vectors/primitives/trigon_coast_salish_v1.svg` | use with caution | Use as source-grounded baseline; attach to phrases and control elongation/concavity. |
| Compact trigon proxy | `track2-deterministic/source-vectors/primitives/prim_trigon_synthesized_reference.svg` | use with caution | Temporary fitting proxy only; do not treat as canonical. |
| Source-extracted orb/crescent | `prim_circle_oval_extracted_cosmic_sun.svg`, `prim_crescent_extracted_wolf_moon.svg` | do not use | Keep for private comparison only; not future overlay canon. |
