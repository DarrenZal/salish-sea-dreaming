# Austin Review Packet v001 - 2026-05-22

Status: INTERNAL review packet prepared for Austin. Pending Austin review.
Not approved for public, show, projector, sponsor, social, press, or
external use. No cultural-meaning claim is made by any output in this
packet. Austin's review determines meaning and use.

This packet is intended to help Austin respond as an artistic and
curatorial collaborator on the installation architecture, not as an
approver of individual renders. The goal of the meeting is direction, not
sign-off.

## 1. Framing

- `anchor_graph_spine_v004_1_raven_collapse_polish` is the current finished
  loopable UHD installation spine checkpoint (80 seconds, 3840x2160, 24 fps,
  seam below adjacent-frame step). It is the proof point for the working
  architecture.
- The spine uses **whole Austin-authored artworks** as content. The two
  source artworks in this checkpoint are `Nature_Cosmic_Sun.svg` and
  `Animal_Bird_Raven_Sun.svg`. They remain intact whole authored
  compositions; they are not decomposed into reusable motifs, atoms, or
  generic primitives.
- The transitions between artworks use **anchor metadata** (shared sun-disc
  center, eight-ray geometry, source bounding boxes, masks, timing) as
  alignment information only, and **cymatic / water connective tissue** as
  the visible motion between artwork nodes.
- Per the 2026-05-22 authorization expansion, Austin has greenlit
  Austin-style / Coast Salish-style generated experiments for this project's
  internal and show-development pipeline. Both whole-source artwork nodes
  and generated support compositions appear in this packet under that
  authorization. See
  [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md).
- Austin remains the authority on meaning, on final external use, and on
  curatorial direction. Anything in this packet may resonate with or help
  contextualize Austin's authored forms; nothing in this packet proves
  cultural meaning. Austin's review determines that.

## 2. What is working

The architecture appears to be carrying its load. The four signals we see
in the v004.1 spine checkpoint:

- **Whole-source artwork nodes.** Austin's source compositions read as
  authored artworks on the wall, not as cards or as decomposed motifs. The
  Nature radial mask presents `Nature_Cosmic_Sun.svg` as a round/radial
  authored work rather than a square frame, and the full artwork remains
  visible.
- **Nature Cosmic Sun -> Raven Sun through a shared sun-disc anchor.** The
  transition between two whole artworks uses the measured sun-disc center
  and eight-ray geometry as alignment information only. The shared anchor
  is metadata, not a renderable third object. This is the structural move
  that lets the installation be more than a slideshow of independent
  artworks; whether the move feels meaningful is Austin's call.
- **Cymatic connective tissue.** Generated abstract cymatic / water
  motion serves as the universal connective layer between artwork nodes.
  Artworks collapse through their own anchor metadata into a cymatic field
  and gather from that field into the next artwork. The connective tissue
  is generated atmosphere; it does not claim to depict, prove, or carry
  cultural content.
- **Loopable Resolume-ready video layer.** The spine renders cleanly as an
  80 second UHD MP4 with a measured loop seam below the adjacent-frame
  reference, so it can be parked in a Resolume bin as a self-contained
  spine layer for the installation rather than living as a fragile
  realtime composite.

## 3. Current architecture split

The working thesis is that the installation is not one renderer. It is an
**anchor graph** of transitions between artwork nodes, with two distinct
support-composition lanes depending on the source's morphology.

- **Radial / sun / flower-of-life / round-source compositions.** Use
  cymatic / wave geometry as the support composition (octagonal cymatic
  fields, standing waves, wavefront/feature emergence). The geometric
  centers, radial relationships, and repeated symmetries in these sources
  may resonate with wave-interference visual language. The v004.1 spine
  uses this lane between `Nature_Cosmic_Sun` and `Animal_Bird_Raven_Sun`.
- **Figural animal compositions.** Move first to a
  **silhouette-reveal architecture**. Use fluid / current / flow behavior
  around the animal's alpha silhouette to imply the whole body before the
  full authored artwork fades in. This is a deliberate change after the
  orca cymatic aperture v002 result; the cymatic-aperture approach
  technically passed every internal anchor but read as separated windows
  instead of as one animal emerging. See
  [figural-fluid-dynamics-reveal-scout-2026-05-22.md](figural-fluid-dynamics-reveal-scout-2026-05-22.md).
- **Whole Austin artworks remain the anchor content.** Both lanes treat
  Austin's authored sources as whole, with anchors and masks as alignment
  metadata. Neither lane extracts Austin motifs as reusable atoms.
- **Generated support compositions are connective atmosphere and
  experiments.** Wave fields, cymatic geometry, fluid silhouettes, and the
  in-flight Path A / Path B physics probes provide motion, reveal, and
  transition. They are not portrait-replacements for Austin's work; they
  are the connective tissue and the development surface for that tissue.

## 4. Current outputs to show

The intent for the meeting is to show the v004.1 spine first as the main
proof point, then walk through the R&D surface that supports and questions
it. The supporting outputs are honest about being internal and in motion.

- **v004.1 spine** (main proof point).
  `track2-deterministic/morph_outputs_INTERNAL/anchor_graph_spine_v004_1_raven_collapse_polish_2026-05-21/`
  - Main file:
    `anchor_graph_spine_v004_1_raven_collapse_polish.mp4` (80s, 3840x2160,
    24 fps).
  - Contact sheet, v004/v004.1 comparison sheet, loop diagnostic sheet,
    debug masks timeline, peak stills, source assets, and manifest are
    present in the packet.
  - Provenance:
    `Nature_Cosmic_Sun.svg` and `Animal_Bird_Raven_Sun.svg` (SHA-256 in
    `SOURCE_PROVENANCE.md`); anchor registry
    `track2-deterministic/anchor_graph/austin_anchor_registry_v001.json`;
    Raven spatial node `raven_sun_spatial_node_v002_2026-05-21`.
- **Path A / Path B abstract cymatic physics probes** (R&D support).
  Two in-flight probes designed to test whether the cymatic / wave layer
  can carry primitive grammar (circle / crescent / trigon) from field
  features rather than from drawn overlays. Evaluation framework in
  [abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md).
  Probe packets:
  `track2-deterministic/morph_outputs_INTERNAL/abstract_cymatic_wavefront_overlap_path_a_v001_2026-05-22/`
  and
  `track2-deterministic/morph_outputs_INTERNAL/abstract_cymatic_wave_equation_overlap_path_b_v001_2026-05-22/`.
  These are renderer-development evidence, not finished pieces.
- **Orca cymatic aperture v002** (mixed result that informed the figural
  pivot).
  `track2-deterministic/morph_outputs_INTERNAL/figural_orca_cymatic_aperture_portal_v002_2026-05-22/`.
  Wave physics + source-derived aperture masks; every internal anchor
  passed the ratio gate, but the pre-reveal aperture constellation reads
  as separated windows rather than as one animal emerging. This is the
  result that prompted the move to silhouette-reveal as the first read for
  figural pieces.
- **Reserved slots** (leave space; add when they return).
  - Path A v002 follow-up render.
  - Figural fluid / silhouette reveal v001 (Orca silhouette-first probe per
    the figural fluid dynamics reveal scout).

## 5. Questions for Austin

These are the questions the meeting is actually for. They are intended
as a starting point; Austin should feel free to redirect them.

- Which pieces in this packet feel strongest as part of the installation,
  and which feel like they need more work or should be set aside?
- Which anchors and transitions feel meaningful, and which feel arbitrary?
  In particular: does the shared sun-disc anchor between Nature Cosmic Sun
  and Raven Sun feel like a real artistic relationship, or like a
  technical convenience?
- Does the v004.1 spine feel like a respectful and exciting use of his
  work? Where does the current treatment serve the source, and where does
  it get in the way?
- Does the cymatic / wave-geometry layer resonate as connective tissue, or
  does it distract from the artworks? If it resonates, in what role
  (atmosphere, transition, reveal, hold)? If it distracts, where?
- For figural animal pieces, does the proposed move to fluid / silhouette
  dynamics as the first reveal step feel right, or is there a different
  reveal grammar that would better honor the figural sources?
- Of the outputs in this packet, which would Austin clear for show or
  external use, which should remain internal for further development, and
  which should be parked or stopped?
- Are there directions, references, or constraints Austin would like the
  project to be working on next that this packet has not yet surfaced?

## 6. Appendix - output review table

Tone reminder: every "current verdict" cell describes internal renderer
status only. Nothing in this column constitutes external-use approval.
Austin's review determines meaning and use.

| Output / path | Type | Uses Austin source? | Generated support? | Current verdict | Review question for Austin |
|---|---|---|---|---|---|
| `anchor_graph_spine_v004_1_raven_collapse_polish_2026-05-21/` (v004.1 spine) | spine | yes (`Nature_Cosmic_Sun.svg`, `Animal_Bird_Raven_Sun.svg`) | yes (cymatic connective tissue, anchor-aligned reveal/collapse) | finished internal UHD checkpoint; loop seam below adjacent-frame step; honest Raven hold caveat (1080p spatial-node source inside UHD render) | does this feel like a respectful and exciting use of these two artworks, and does the shared sun-disc transition feel meaningful? |
| `abstract_cymatic_wavefront_overlap_path_a_v001_2026-05-22/` (Path A probe) | R&D | no | yes | in-flight R&D; field-derivation gate per the physics-model comparison framework; not a finished piece | does the wavefront-overlap field language read as connective atmosphere you would want to see used in transitions? |
| `abstract_cymatic_wave_equation_overlap_path_b_v001_2026-05-22/` (Path B probe) | R&D | no | yes | in-flight R&D; field-derivation gate per the physics-model comparison framework; not a finished piece | does the wave-equation field language read as connective atmosphere you would want to see used in transitions? |
| `figural_orca_cymatic_aperture_portal_v002_2026-05-22/` (orca cymatic aperture v002) | parked - informed pivot | yes (`austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`) | yes (source-derived aperture masks + cymatic field) | mixed; quantitative anchor pass, reads as separated windows; not the figural reveal direction | does the figural pivot to fluid / silhouette reveal feel right for the animals, or is there a different reveal grammar that should be tried first? |
| Path A v002 (when it returns) | R&D | no | yes | reserved slot; pending render and field-derivation gate evaluation | which Path A vs Path B language reads as installation-grade connective tissue? |
| Figural fluid / silhouette reveal v001 (when it returns) | R&D - figural support | yes (Orca whole source) | yes (fluid silhouette reveal) | reserved slot; pending render | does fluid-around-silhouette feel like the right first read for the Orca, ahead of full whole-source fade-in? |

## 7. Linked records

- [installation-anchor-graph-architecture-2026-05-21.md](installation-anchor-graph-architecture-2026-05-21.md)
  -- working installation architecture: anchor graph of transitions between
  artwork nodes via cymatic / water connective tissue.
- [abstract-cymatic-physics-model-comparison-2026-05-22.md](abstract-cymatic-physics-model-comparison-2026-05-22.md)
  -- Path A / Path B evaluation framework. Field-derived primitives are
  the gate; visual readability and loop usability are secondary.
- [figural-fluid-dynamics-reveal-scout-2026-05-22.md](figural-fluid-dynamics-reveal-scout-2026-05-22.md)
  -- documents the orca v002 mixed result and the move to fluid /
  silhouette reveal for figural sources.
- [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md)
  -- scope under which generated Austin-style / Coast Salish-style
  experiments and Drive-artwork use are authorized for internal /
  show-development work; per-output Austin review remains the floor for
  external use.
- [austin-consent-map.md](austin-consent-map.md) -- operator sign-off log
  of record.
- [austin-architectural-review-packet-draft-2026-05-21.md](austin-architectural-review-packet-draft-2026-05-21.md)
  -- prior architectural review packet draft (2026-05-21).
- `track2-deterministic/anchor_graph/austin_anchor_registry_v001.json`
  -- anchor registry of record; the metadata-only alignment source used by
  the v004.1 spine.
- `track2-deterministic/morph_outputs_INTERNAL/anchor_graph_spine_v004_1_raven_collapse_polish_2026-05-21/`
  -- v004.1 spine packet (README, manifest, MP4, contact sheet, comparison
  sheet, loop diagnostic, debug masks timeline, peak stills, source
  assets).

## 8. Verification

- ASCII-only content; no non-ASCII characters introduced by this packet.
- All linked markdown paths exist under `docs/space-center/`.
- All linked `track2-deterministic/` paths exist on disk.
- No rendering, no SVG edits, no source artwork modification, no scripts
  modified, no generated artwork produced by this document.
- No external-use authorizations granted by this document. Per-output
  Austin review remains the floor for any external surface.

Recorded by: operator session, 2026-05-22.
