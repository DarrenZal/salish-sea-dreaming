# Austin Artwork Portal Source Map - 2026-05-21

Status: INTERNAL ONLY. No rendering performed. This note identifies Austin
SVG/source assets that may be useful for private portal tests. It does not
grant Austin approval, public-use permission, show-use permission, cultural
meaning, or permission to fragment/recolor source artwork.

Consent floor: per [austin-consent-map.md](austin-consent-map.md), the default
state for Austin source files and outputs is `pending / internal-only` until
Austin gives per-output OK. The `austin-v2-ingest/approved/` folder name means
triaged into the clean source set; it does not override the manifest consent
status.

Read with:

- [austin-consent-map.md](austin-consent-map.md)
- [austin-source-inventory-2026-05-18.md](austin-source-inventory-2026-05-18.md)
- [austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md](austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md)
- [austin-visual-morphology-atlas-2026-05-20.md](austin-visual-morphology-atlas-2026-05-20.md)

## Summary

| Asset | Consent/provenance status | Layered SVG | Portal suitability | Use posture |
|---|---|---:|---|---|
| `Nature_Cosmic_Sun.svg` | Austin curated Drive; manifest `pending`; inventory `READY`, cultural load `medium` | yes, broad layers | high | Best first internal portal anchor because it is radial, centered, and has clear orb/ray structure. |
| `Animal_Bird_Raven_Sun.svg` | Austin curated Drive; manifest `pending`; inventory `READY`, cultural load `medium-high` | yes, broad layers | medium | Useful only as private whole-composition portal/reference test; figure-bearing and relationship-bearing. |

## 1. `Nature_Cosmic_Sun.svg`

Source paths:

- `austin-v2-ingest/approved/Nature_Cosmic_Sun.svg`
- `track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg`
- companion JPG: `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`
- decomposition: `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atom_metadata.csv`

Provenance / approval status:

- Provenance manifest row: `Austin curated drive`, `austin_consent=pending`,
  hash `197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1`.
- Source inventory: vector source yes, JPG yes, decomposed yes, 39 atoms,
  cultural load `medium`, status `READY`.
- Consent map: source vectors are pending; deterministic primitive/morph or
  portal outputs need Austin review before any show/public use.

Layered SVG status:

- SVG viewBox: `0 0 108 108`.
- Broad layers present: `Layer_3`, `Layer_2`.
- Element counts observed: 34 paths, 4 circles, 1 ellipse, 2 lines, 6 groups.
- Layering is useful for internal inspection, but groups are not sufficient
  semantic portal controls; use atom metadata for motif-level anchors.

Obvious anchor points:

- Composition center: `(54, 54)` by viewBox.
- Main orb / sun body center from metadata: approximately `(53.92, 53.86)`.
- Outer source extent exceeds the viewBox because rays run off-canvas:
  approximately `x=-7.47..114.49`, `y=-6.09..113.04`.
- Radial axes: vertical, horizontal, and diagonal sun-ray axes around the center.
- Major motif centers:
  - central orb / rings: `(53.92, 53.86)`;
  - top ray: `(53.92, 8.26)` and top trigon tip near `(53.92, 14.44)`;
  - bottom ray: `(53.92, 99.48)` and bottom trigon tip near `(53.92, 93.27)`;
  - left/right ray centers near `(9.99, 26.89)`, `(9.98, 81.64)`,
    `(97.44, 27.30)`, `(97.43, 81.25)`;
  - face/eye details exist around `(33.76, 51.70)` and `(74.09, 51.70)`.

Recommended portal suitability: **high** for internal tests.

Best internal portal use:

- Whole-source radial portal framing.
- Center/orb alignment and radial reveal timing.
- Private source-locked portal tests where the artwork remains intact.

Cautions:

- Do not fragment the sun face, eyes, mouth, cheek crescents, or ray atoms into
  generic reusable portal parts.
- Do not recolor, palette-shift, or treat Austin's sun palette as a general
  renderer palette.
- Do not detach rays or use atom adjacency as generic sun grammar.
- Do not use public-facing, sponsor-facing, show, or projector outputs without
  Austin per-output OK.
- Do not imply the source is culturally approved for portal use; it is an
  internal test source only.

## 2. `Animal_Bird_Raven_Sun.svg`

Source paths:

- `austin-v2-ingest/approved/Animal_Bird_Raven_Sun.svg`
- `track2-deterministic/source-vectors/Animal_Bird_Raven_Sun.svg`
- companion JPG: `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`
- decomposition: `austin-v2-ingest/decomposed/Animal_Bird_Raven_Sun/atom_metadata.csv`

Provenance / approval status:

- Provenance manifest row: `Austin curated drive`, `austin_consent=pending`,
  hash `5fa0ceaea6a49cc4c1408434541dc3a69e89d935fd96740606a4f1787c92c766`.
- Source inventory: vector source yes, JPG yes, decomposed yes, 29 atoms,
  cultural load `medium-high`, status `READY`.
- Consent map: Raven subject and source-vector outputs remain pending; public,
  show, morph, and portal use require Austin per-output OK.

Layered SVG status:

- SVG viewBox: `0 0 108 108`.
- Broad layers present: `Layer_2`, `Layer_5`; includes `radial-gradient`.
- Element counts observed: 29 paths, 2 circles, 1 rect, 9 groups.
- Layering separates broad background/sun/figure regions, but not enough to
  license fragmentation. Treat as whole-composition or source-locked reference.

Obvious anchor points:

- Composition center: `(54, 54)` by viewBox.
- Sun disc center: metadata `(54.00, 53.51)`, radius approximately `28.15`.
- Full canvas/background bounding field: rect `x=0`, `y=-0.49`,
  `w=108`, `h=103.54`.
- Radial axes: sun-ray points at top, left, right, and upper diagonals around
  the sun disc.
- Major motif centers:
  - top sun ray: `(53.92, 17.01)`;
  - left/right sun rays: `(17.49, 53.60)`, `(90.51, 53.43)`;
  - upper diagonal sun rays: `(31.15, 30.77)`, `(76.73, 30.66)`;
  - figure/body focal point from metadata: small circle near `(52.84, 67.71)`;
  - landscape/foreground mass center from metadata: approximately
    `(51.80, 81.64)`.

Recommended portal suitability: **medium** for internal tests.

Best internal portal use:

- Whole-composition portal alignment test with sun disc as the portal center.
- Private reference for figure-crossing-radial-field composition.
- Internal comparison against `Nature_Cosmic_Sun.svg` for radial field strength.

Cautions:

- Do not fragment the raven silhouette, body details, wing/figure forms,
  landscape marks, or sun relationship into reusable glyph parts.
- Do not isolate the raven as a portal actor or flock template.
- Do not recolor, palette-shift, or animate exact source components.
- Do not use public-facing, sponsor-facing, show, or projector outputs without
  Austin per-output OK.
- Do not imply Raven Sun composition, bird-in-front-of-sun behavior, or radial
  figure symbolism is culturally approved.

## Portal Test Rules

- Use full-source or source-locked masks first; avoid atom-level fragmentation
  unless the test is explicitly provenance/debug-only.
- Keep original geometry, proportions, and palette intact for source tests.
- If a portal test uses only anchors, use center points, bounding boxes, and
  radial axes as alignment metadata, not copied motifs.
- Any derived output must carry `internal_austin_review_needed`.
- Any review packet must state that the asset is pending consent for output use
  and not public/show approved.

## Next Additions

Candidate future rows after Austin/source review:

- `Animal_Salmon_Spawn_Eggs.svg`: likely useful for rotational portal tests,
  but source-like salmon replication is currently parked.
- `Animal_Insect_Bee.svg`: lower cultural load if/when vector conversion status
  is settled, but not needed for the first radial portal test.
- Avoid Thunderbird, serpent, wolf, and supernatural/human sources for portal
  tests unless Austin gives explicit guidance.
