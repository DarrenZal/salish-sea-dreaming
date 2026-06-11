# Austin Anchor Registry Notes - 2026-05-21

Status: INTERNAL ONLY. Pending Austin review. No public, show, projector,
sponsor, social, or press use. No cultural-meaning claims. No motif extraction.
No atom decomposition. No new SVG assets.

Read with:

- [Austin anchor registry](../../track2-deterministic/anchor_graph/austin_anchor_registry_v001.json)
- [Austin artwork portal source map](austin-artwork-portal-source-map-2026-05-21.md)
- [Austin consent map](austin-consent-map.md)
- [wave_to_artwork_portal_v002 README](../../track2-deterministic/morph_outputs_INTERNAL/wave_to_artwork_portal_v002_2026-05-21/README.md)
- [wave_to_artwork_portal_v002 manifest](../../track2-deterministic/morph_outputs_INTERNAL/wave_to_artwork_portal_v002_2026-05-21/wave_to_artwork_portal_v002_manifest.json)
- [anchored_artwork_portal_chain_v001 README](../../track2-deterministic/morph_outputs_INTERNAL/anchored_artwork_portal_chain_v001_2026-05-21/README.md)
- [anchored_artwork_portal_chain_v001 manifest](../../track2-deterministic/morph_outputs_INTERNAL/anchored_artwork_portal_chain_v001_2026-05-21/anchored_artwork_portal_chain_v001_manifest.json)
- [Austin visual morphology atlas](austin-visual-morphology-atlas-2026-05-20.md)
- [Austin source inventory](austin-source-inventory-2026-05-18.md)

## Purpose

The registry names reusable artwork nodes and anchor metadata for future portal
work. Its job is to let future probes align whole Austin-authored artworks by
center, radius, symmetry, axis count, bounds, and aperture order without
turning any part of the artwork into a reusable primitive library.

The JSON makes this structural distinction explicit. Artwork records use
`asset_type: authored_whole_source_artwork` and `whole_source_only: true`.
Anchor records use `asset_type: alignment_metadata_only`,
`is_renderable_primitive: false`, and `may_extract_as_motif: false`. The schema
section also sets those values as constants for anchor entries.

## Why The Nature To Raven Sun-Disc Anchor Worked

`Nature_Cosmic_Sun.svg` and `Animal_Bird_Raven_Sun.svg` both have a measurable
central sun-disc/orb anchor. Nature's main orb is centered at `[53.92, 53.86]`
with radius `34.08` in SVG viewBox units. Raven Sun's central disc is centered
at `[54.0, 53.51]` with radius `28.15`.

The anchored chain did not copy a disc from one artwork into the other. It
scaled each whole source uniformly so both measured anchors landed on canvas
center `[960.0, 540.0]` at radius `276.0` px. That gave the transition a stable
spatial reference while the surrounding authored compositions stayed intact.

## Why 8-Source Symmetry Matching Mattered

The first wave-to-Nature pass needed the wave field to respect the artwork's
radial structure. `Nature_Cosmic_Sun.svg` is organized around an eight-ray
radial aperture, so v002 used an exact 8-source octagonal gather instead of a
generic or inherited sixfold field.

That mattered because the portal read became structural rather than decorative:
the wave sources gathered along the same eightfold rhythm, the central orb
aperture opened first, the ray apertures followed, and the full authored source
appeared through a radial mask. The result is a stronger wave -> artwork edge
without generating or extracting Austin's ray forms.

## Why Anchors Are Metadata Only

An anchor is a measured alignment fact: a center point, radius, axis count,
canvas placement, mask order, or source-bound reference. It is not a copied SVG
path, not a primitive, not a motif, not a palette, and not a license to recreate
the source shape.

Future renderers may use anchor records only to place or time whole-source
artworks and source-locked masks. They must not render an anchor by itself or
assemble anchors into new artwork. The registry encodes this with hard fields
on every anchor entry, not only prose warnings.

## Adding Another Austin Artwork Node

To add another Austin artwork node:

1. Confirm the canonical source path and SHA-256 hash.
2. Record consent as `pending_austin_review` unless Austin has explicitly
   approved that exact source and use.
3. Add an artwork record with `asset_type: authored_whole_source_artwork` and
   `whole_source_only: true`.
4. Identify only alignment metadata: center, bounds, axes, repeated structure,
   source-layer reference, or aperture order.
5. Add anchor records with `asset_type: alignment_metadata_only`,
   `is_renderable_primitive: false`, and `may_extract_as_motif: false`.
6. If a probe exists, add a tested edge with artifact, README, and manifest
   paths. If no probe exists, add only a candidate edge.
7. Keep output use internal until Austin reviews the specific output.

Do not add atom-derived motif records, extracted SVG fragments, recolored
source elements, or new SVG assets to this registry.

## Registry Depth Summary

The registry now covers the six canonical top-level SVG sources currently
available under `track2-deterministic/source-vectors/`:

- `Nature_Cosmic_Sun.svg`
- `Animal_Bird_Raven_Sun.svg`
- `Animal_Insect_Bee.svg`
- `Animal_Salmon_Spawn_Eggs.svg`
- `Animal_Wolf_Spindle_Whorl.svg`
- `Supernatural_Human_TheCreator_Background.svg`

It now contains 10 anchor records. Repeated anchor types are central disc/orb
measurements, major composition or bounding-box centers, circle-field centers,
and radial or twofold axis metadata. These are all alignment records only.

Strongest future portal candidates by geometry:

- Nature Cosmic Sun: strongest validated wave -> artwork target and
  artwork -> artwork sun-disc anchor.
- Raven Sun: strong artwork -> artwork sun-disc anchor and strong
  figure-on-field spatial candidate, still pending Austin review.
- Salmon Spawn Eggs: strong central circle and circle-field geometry for a
  future source-locked test, but roe/body interpretation must wait for Austin.
- Wolf Spindle Whorl: strong central spindle-disc geometry, but high review
  load means it should wait for Austin guidance before any visual probe.

Lower-confidence or constrained nodes:

- Bee is path-only in the SVG. Its bounds anchor is useful for coarse
  whole-source placement, not for a body-spine or wing motif.
- TheCreator has only broad bounds recorded here. Existing architecture notes
  treat it as a possible containing frame node, not a morph endpoint.

Low-confidence anchor records are:

- `animal_insect_bee.composition_bounds_center`
- `animal_salmon_spawn_eggs.roe_circle_cluster`
- `animal_wolf_spindle_whorl.twofold_composition_center`
- `supernatural_human_thecreator_background.major_bounding_box_center`

## Candidate Sources Needing Separate Treatment

Approved-folder PDFs and PNGs are inventoried here only. They do not receive
geometric anchor records in the registry because this pass did not create,
edit, convert, render, or decompose visual assets, and raster/PDF anchors
should not be inferred without a reliable vector or existing decomposition
source.

PDF candidates:

- `austin-v2-ingest/approved/Animal_Bear_Background.pdf`
- `austin-v2-ingest/approved/Animal_Bird_Heron_Background.pdf`
- `austin-v2-ingest/approved/Animal_Deer_Background.pdf`
- `austin-v2-ingest/approved/Animal_Insect_Bee.pdf`
- `austin-v2-ingest/approved/Animal_Wolf_Background.pdf`
- `austin-v2-ingest/approved/Supernatural_Bird_Thunderbird_Background.pdf`
- `austin-v2-ingest/approved/Supernatural_Snake_Serpent.pdf`

PNG candidates:

- `austin-v2-ingest/approved/Animal_Bird_Raven_Transparent.png`
- `austin-v2-ingest/approved/Animal_Insect_Butterfly_Transparent.png`
- `austin-v2-ingest/approved/Animal_Water_Octopus_Transparent.png`
- `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
- `austin-v2-ingest/approved/Human_Mother_Bear_Cub_Background.png`
- `austin-v2-ingest/approved/Supernatural_Transformer_Background.png`

These need separate conversion, vector QA, or Austin-provided vector sources
before anchor metadata should be added. Supernatural, Wolf, Orca, Thunderbird,
Serpent, and Transformer sources should wait for Austin guidance before any
visual probe.

## What Must Wait For Austin Review

These items remain blocked until Austin explicitly reviews and approves the
specific item or category:

- Any public, show, projector, sponsor, social, press, or external use.
- Any claim about cultural meaning, correctness, symbolism, or teaching.
- Any transformation that fragments, isolates, recolors, or reuses motifs.
- Any atom-level decomposition used as a production asset.
- Any Raven Sun wave portal or figure-on-field 3D treatment proposed beyond
  internal source-locked testing.
- Any new artwork node promoted from candidate status to installation use.

The current registry is an internal technical alignment map only.
