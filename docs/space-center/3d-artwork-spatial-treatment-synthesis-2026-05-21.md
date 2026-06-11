# 3D Artwork Spatial Treatment — Synthesis (2026-05-21)

> **INTERNAL ONLY. Pending Austin per-output approval.** No
> public/show/projector/sponsor/social use. No cultural-meaning claims.
> This synthesis describes what a 2.5D shallow-extrusion probe over two of
> Austin Harry's authored SVGs teaches the installation anchor graph. No
> new MP4s rendered for this doc; no SVG edits.

## Context

- Probe: [`track2-deterministic/probes/3d-extrusion-2026-05-21/README.md`](../../track2-deterministic/probes/3d-extrusion-2026-05-21/README.md)
- Source map: [`austin-artwork-portal-source-map-2026-05-21.md`](austin-artwork-portal-source-map-2026-05-21.md)
- Consent floor: [`austin-consent-map.md`](austin-consent-map.md)
- Contact sheets reviewed:
  - [`stills/nature_cosmic_sun/contact_sheet.png`](../../track2-deterministic/probes/3d-extrusion-2026-05-21/stills/nature_cosmic_sun/contact_sheet.png)
  - [`stills/animal_bird_raven_sun/contact_sheet.png`](../../track2-deterministic/probes/3d-extrusion-2026-05-21/stills/animal_bird_raven_sun/contact_sheet.png)

Method recap (unchanged from probe): authored SVG → split by the file's
own `<g>` grouping into three tiers → faithful `cairosvg` raster → three
flat planes at shallow z-depth → slow pinhole camera push-in + small
yaw/pitch. No shading, no recolor, no diffusion, no atom-level
fragmentation.

## 1. Cosmic Sun (`nature_cosmic_sun`) result

**Verdict: integrity pass, modest visual payoff.**

- Geometry and palette preserved exactly. Authored grouping only
  (`Layer_3` outer cosmic field, `Layer_2` core sun face, three explicit
  `<g>` subgroups inside `Layer_2`). No atoms touched.
- The composition is dense and radial: the back tier alone covers ~71%
  of the canvas, and the front tier (peripheral trigon subgroups) only
  3% — so there is almost no transparent space *between* tiers for
  parallax to read through.
- Spatial depth therefore reads as a small scale + skew differential
  between layers during yaw/pitch, not as the "see distant content
  through near content" parallax that sparser compositions would give.
- The piece holds together as Austin's piece in the angled view — no
  element dislodges, the orange trigons stay attached to the sun, the
  face stays centred — but the 2.5D treatment does not produce a
  moment unavailable in the 2D source.

Takeaway: better as a **wave / artwork portal target** (radial reveal,
center/orb alignment, full-source framing) than as a 3D parallax target.
Close the 3D-extrusion thread for this piece.

## 2. Raven Sun (`animal_bird_raven_sun`) result

**Verdict: pass for figure-on-field spatial treatment.**

The authored grouping supports three useful depth tiers:

| Tier | Authored content | z |
|---|---|---:|
| back | `Layer_2` children [0, 1] — sky gradient + sun disc + rays | −0.35 |
| mid | `Layer_2` children [2..6] — clouds + landscape mass/detail/outlines | 0.00 |
| front | `Layer_5` — the raven figure (whole, not split) | +0.25 |

This grouping is the file's own. Z-separation is ~2× Cosmic Sun's, and
the front tier is a discrete, centred figure (20.3% alpha) rather than
peripheral fragments (3.2%).

Moments produced that the 2D source cannot:

1. **Raven breaks the picture plane.** The front tier projects ~20%
   larger than the back, so the raven's wingtips visibly extend past
   the sky rectangle. It reads as a figure occupying a volume in front
   of the canvas.
2. **Raven shifts relative to the sun.** As the camera yaws, the
   raven's beak crosses the sun centre line and back; the sun stays
   put because it sits deeper. True motion parallax against a fixed
   anchor — not reproducible by a 2D image without independently
   warping the figure (which the brief refuses).
3. **Mid layer slides differently from sky and raven.** The cloud /
   landscape band moves at a third rate, giving a quiet layered-cutout
   feel as the camera pushes in.

The raven figure stays a single rigid plane. No wing/body split. No
recolor. No imitation.

## 3. Rule for future pieces

- **Apply 2.5D shallow extrusion only where the source artwork already
  has authored figure/field/depth separation** (e.g. a discrete figure
  over a field, with the file's own `<g>` grouping reflecting that
  separation).
- **Do not atom-rig wings, rays, eyes, trigons, crescents, or
  individual motif parts** without explicit Austin approval. The
  authored-grouping-only constraint is what keeps the treatment from
  becoming reusable-motif territory.
- **Avoid dense radial / tessellated pieces for this treatment** unless
  Austin specifically asks for it. The payoff is too small for the
  treatment to earn its place over a flat-source presentation.

## 4. Known limitations

- **Raven cloud / canvas clipping artifacts.** Because Austin authored
  cloud paths to be clipped by the canvas edge, the mid-layer plane —
  projecting ~10% larger than the back — shows hard cloud silhouettes
  above/beside the sky rectangle in the front-on still. Integrates
  better in motion than at rest.
- **Attenuation options exist but are not implemented.** Two
  candidates: (a) mask non-back tiers by the back tier's projected
  polygon (kills the raven-breaks-the-picture-plane moment — not
  recommended); (b) pre-feather each tier raster's alpha near the
  canvas edge (geometry-preserving, soft cuts). Neither applied here;
  both stay on the option list for a future Austin-gated pass.
- **Raven plane grows relative to sky on push-in.** A real, honest 3D
  consequence of the closer plane, but a real artistic call about
  whether the bird should grow on push-in or hold apparent size.
- **No projector / show use pending Austin review.** Frame and
  background chosen so the MP4 sits inside a black projection surface,
  but no physical projector test has been run, and none should be
  before Austin's per-output OK.

## 5. Anchor graph status

This synthesis updates the installation anchor graph as follows.

| Edge | Status after this probe |
|---|---|
| `artwork (figure-on-field)` → `spatial treatment (2.5D shallow extrusion)` | **validated** — produces real 3D-only moments while keeping authored geometry/palette intact. Pending Austin per-output OK. |
| `artwork (dense radial / tessellated)` → `spatial treatment (2.5D shallow extrusion)` | **parked** — integrity holds but payoff doesn't justify the treatment over a flat or portal-style presentation. |
| `artwork (radial / orb-centered)` → `wave or artwork portal` | **preferred** for pieces like Cosmic Sun (per source map, radial framing + center alignment is the high-suitability use). |
| `artwork → atom-level rig` (wings, rays, eyes, trigons, crescents) | **disallowed** without explicit Austin call. Consent map restricts fragmentation; this probe deliberately ignored the existing 39-atom decomposition for Cosmic Sun. |

Recommended future use: **private Austin review with Raven Sun as the
reference example** of what figure-on-field shallow extrusion looks like
when the authored-grouping-only constraint is honored. Cosmic Sun is the
counter-example showing where the treatment doesn't earn its place.

## Boundary

Internal only. Pending Austin review. No public / show / projector /
sponsor / social use. No cultural-meaning claims. Per
[austin-consent-map.md](austin-consent-map.md): default state for Austin
source files and derived outputs is `pending / internal-only` until
Austin explicitly approves the specific item.
