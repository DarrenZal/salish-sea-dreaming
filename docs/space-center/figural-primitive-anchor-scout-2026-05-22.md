# Figural Primitive Anchor Scout -- 2026-05-22

Status: INTERNAL SCOUT / DOCUMENTATION PASS ONLY. No rendering performed. No SVG
edits performed. No motifs extracted. No Coast Salish designs generated. No
external surfaces, public uses, show uses, projector uses, sponsor uses, social
uses, or press uses are authorized by anything in this document.

Boundary contract for every anchor listed below:

- `asset_type: alignment_metadata_only`
- `is_renderable_primitive: false`
- `may_extract_as_motif: false`

Anchors are measured alignment metadata on whole authored sources, not reusable
drawing parts and not a primitive library. Per
[austin-consent-map.md](austin-consent-map.md), the default consent state for
Austin source artwork and derived outputs is `pending / internal-only` until
Austin gives per-output OK. Nothing here changes that. This is not motif
extraction.

Read alongside:

- [austin-artwork-portal-source-map-2026-05-21.md](austin-artwork-portal-source-map-2026-05-21.md)
- [austin-anchor-registry-notes-2026-05-21.md](austin-anchor-registry-notes-2026-05-21.md)
- [austin-source-inventory-2026-05-18.md](austin-source-inventory-2026-05-18.md)
- `track2-deterministic/anchor_graph/austin_anchor_registry_v001.json`
- `austin-v2-ingest/austin-piece-catalog-2026-05-16.md`

---

## Goal

Identify Austin-authored figural pieces (beyond the validated sun-disc spine in
`Nature_Cosmic_Sun.svg` + `Animal_Bird_Raven_Sun.svg`) that could work with the
anchor-portal architecture **without mapping the whole figure**. The aim is to
locate one or two near-term probe candidates where a small, positionally
meaningful primitive anchor -- a single circle, a crescent run, or a trigon
cluster -- could co-exist with a clean whole-source reveal of Austin's intact
artwork.

The currently validated spine uses whole Austin artworks + anchor metadata +
cymatic connective tissue. The pearl-vision dramaturgy keeps the whole-source
artwork intact; anchors are alignment notes only. This scout extends that
contract to figural pieces beyond sun-disc geometry.

## Evaluation method

Two separate ranking axes, scored independently per piece:

1. **Anchor quality.** How clear, strong, and positionally meaningful are the
   candidate primitive anchors (circle / crescent cluster / trigon cluster)?
   Scored `high / medium / low`.
2. **Whole-source reveal quality.** Does the piece have clean figure/ground
   separation, and would the intact authored artwork read well when revealed
   as a whole? Scored `high / medium / low`.

A strong anchor alone is **not enough**. The ideal first probe has both a
strong anchor **and** a clean whole-source reveal.

**Pre-reveal sense test (for any probe Austin authorizes):** Can a viewer who
has not seen the source artwork sense **where the anchor belongs** before the
full figure appears? If yes, the anchor is doing visual work and the reveal
will read as motivated. If no, the reveal will feel arbitrary. This test is
documented here for future probe planning; **no probe is being executed in this
pass**.

Cultural-load and consent posture are noted per piece but do not enter the
ranking; per [austin-consent-map.md](austin-consent-map.md) every piece needs
Austin per-output OK before any external surface regardless of ranking.

---

## Candidates scouted

Candidates are scoped to figural pieces from the Austin v2 curated drive that
are **not** already serving as validated sun-disc spine anchors and are **not**
already registered as primary spine anchors in
`austin_anchor_registry_v001.json` (Salmon-Spawn-Eggs and Wolf-Spindle-Whorl
have partial anchors there but are still considered here for cross-reference;
Bee has a low-confidence bounds anchor and is scouted further).

Source verification: each candidate's file path was confirmed on disk and its
SHA-256 prefix was cross-checked against the `austin-piece-catalog-2026-05-16`
manifest. PDF candidates carry the PDF SHA from the catalog; their converted
SVG counterparts (where present in
`austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/`) are noted separately.

### 1. `Animal_Bird_Raven_Transparent.png` -- raven-without-sun isolate

Source: `austin-v2-ingest/approved/Animal_Bird_Raven_Transparent.png`
SHA-256 prefix: `a9beaa3c16f0...` (verified on disk; matches catalog).
Format: PNG RGBA, 2521x2215, transparent alpha. No vector source.

Candidate primitive anchors:

- Circle anchor -- primary eye-ovoid: the bright white-with-black-pupil
  eye-ovoid on the raven's head is the unmistakable focal mark.
- Crescent cluster -- wing trailing-edge feather notches: U-form-style cutouts
  along the trailing edges of both wings and the spiral tail-curl.
- Trigon cluster -- beak-and-claw tips (small, optional): the hooked beak and
  splayed primary feather-tips read as pointed elements but are subordinate
  to the eye-ovoid.

Anchor quality: **high.** Single dominant eye-ovoid at a stable head-position,
plus a coherent run of wing/tail crescents that read as a single trailing-edge
cluster.

Whole-source reveal quality: **high.** Clean alpha cutout, hero subject fills
the frame, no landscape competing with figure/ground separation. The PNG was
authored as a compositing isolate, so a whole-source reveal against a stilled
backdrop matches its intended production register.

Cultural-load / consent: Raven carries trickster/crest readings; Nation-specific
protocols apply. Internal-only until explicit Austin OK; do not surface
publicly. Per the catalog this piece is `portfolio-public register` but
story-bearing.

Caution: this is the figure-only Raven, **not** `Animal_Bird_Raven_Sun.svg`
(which already serves as a validated sun-disc spine anchor). The two should
not be confused; this scout is about the cutout-isolate Raven without its sun.

### 2. `Animal_Water_Octopus_Transparent.png` -- octopus isolate

Source: `austin-v2-ingest/approved/Animal_Water_Octopus_Transparent.png`
SHA-256 prefix: `540d8be0d75b...` (verified on disk; matches catalog).
Format: PNG RGBA, 2522x2216, transparent alpha, ~0.89 frame coverage.

Candidate primitive anchors:

- Circle anchor -- slit-eye-ovoid on the mantle: the single cream-yellow
  vertical-slit eye is anatomically distinctive and positionally fixed.
- Crescent cluster -- eight tentacle muscle/joint marks: each tentacle carries
  a run of U-form / crescent marks; together these read as eight free-flowing
  crescent clusters rather than one geometric run.
- Trigon cluster -- none clean (the tentacle tips are tapered curves, not
  pointed/pressure trigons).

Anchor quality: **medium-high.** The slit-eye is a clean single circle anchor;
the eight tentacle crescent clusters are visually busy but not geometrically
stable across poses -- they read as motion rather than as a fixed grammar.

Whole-source reveal quality: **high.** Clean RGBA cutout, hero subject, clear
figure/ground.

Cultural-load / consent: T'lep / Octopus-Intelligence resonance exists in
SSD's own framing; do **not** unilaterally co-opt that resonance without
Austin's explicit OK. Hold for explicit signoff.

### 3. `Animal_Water_Orca_Transparent.png` -- orca breaching isolate

Source: `austin-v2-ingest/approved/Animal_Water_Orca_Transparent.png`
SHA-256 prefix: `9608002e1822...` (verified on disk; matches catalog).
Format: PNG RGBA, 2522x2215, transparent alpha.

Candidate primitive anchors:

- Circle anchor -- eye-patch ovoid: the iconic white eye-patch on the orca's
  head is unmistakable and positionally fixed.
- Trigon cluster -- dorsal fin tip: the dorsal fin reads as a clean trigon
  rising behind the body arc.
- Crescent cluster -- tail-fluke and pectoral arc: the C-curve body arc plus
  tail-fluke notch and pectoral fin curve form a coherent crescent run.

Anchor quality: **high.** Eye-patch is one of the strongest single-circle
anchors in the entire 18-piece set; the dorsal trigon is also clean.

Whole-source reveal quality: **high.** Clean alpha cutout, dynamic pose, no
landscape competition.

Cultural-load / consent: **heavily crest-restricted.** Orca clans, lineage
protocols, and the project's own J/K/L-pod thematic gravity compound the
review load. **Hold for explicit Austin OK.** Strong anchor + strong reveal
do not override consent posture.

### 4. `Animal_Insect_Butterfly_Transparent.png` -- bilateral butterfly isolate

Source: `austin-v2-ingest/approved/Animal_Insect_Butterfly_Transparent.png`
SHA-256 prefix: `3568d4d6388e...` (verified on disk; matches catalog).
Format: PNG RGBA, 2521x2215, transparent alpha, frame coverage ~1.0.

Candidate primitive anchors:

- Circle anchor pair -- bilateral wing-ovoids: each upper wing carries a
  primary ovoid eye-cluster; the pair sits symmetrically across the central
  body axis.
- Crescent cluster -- wing-edge crescents (top and bottom wings, both sides):
  a dense run of crescents along all four wing-edges.
- Trigon cluster -- lower-wing split-U flame-shapes: read as paired pointed
  elements at the lower-wing leading-edges.

Anchor quality: **high.** Bilateral dual-ovoid anchor pair is geometrically
unmistakable; densest formline vocabulary in the figural set per catalog.

Whole-source reveal quality: **high.** Clean alpha cutout, bilateral symmetry,
self-contained composition. One of the most pearl-like pieces in the drive
per catalog.

Cultural-load / consent: face-in-wing motif may carry specific teaching;
confirm with Austin before any modification or public surface. Default-OK
for internal analysis only.

### 5. `Animal_Salmon_Spawn_Eggs.svg` -- spawning pair + roe field (cross-reference)

Source: `track2-deterministic/source-vectors/Animal_Salmon_Spawn_Eggs.svg`
SHA-256 prefix: `84987954359e...` (already in registry).
Format: SVG, viewBox 0 0 1500 1500.

Already registered: `central_circle`, `roe_circle_cluster`,
`composition_center` (see `austin_anchor_registry_v001.json`).

Additional figural-anchor candidates surfaced by this scout (still
`alignment_metadata_only`, still `is_renderable_primitive: false`, still
`may_extract_as_motif: false`):

- Circle anchor pair -- bilateral / rotational salmon-eye ovoids: each salmon
  carries a primary eye-ovoid with concentric rings; the two ovoids sit in
  2-fold rotational symmetry around the central circle. Not measured in this
  pass (would require an SVG element walk).
- Crescent cluster -- dorsal-fin and tail crescent runs along each salmon body.

Anchor quality: **strong** (central circle is already validated; bilateral
salmon-eye pair would add a second positionally-meaningful anchor with
strong geometric coherence).

Whole-source reveal quality: **strong.** Already noted in catalog as a complete
teaching scene and "arguably already a pearl."

Cultural-load / consent: **highest among the figural SVGs.** Hold for explicit
Austin OK before any further probe work. This entry is included only for
cross-reference; the scout's first-probe recommendation is **not** this piece.

### 6. `Animal_Insect_Bee.pdf` / `Animal_Insect_Bee.svg` -- bee isolate

Source:
- PDF: `austin-v2-ingest/approved/Animal_Insect_Bee.pdf` (SHA prefix
  `f504a16549ed...`, verified on disk).
- Converted SVG: `austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/Animal_Insect_Bee.svg`
  (verified on disk; viewBox `0 0 293.613 242.717` matches catalog).
- Source-vectors SVG: `track2-deterministic/source-vectors/Animal_Insect_Bee.svg`
  (already registered with low-confidence bounds anchor).

Candidate primitive anchors:

- Circle anchor -- abdomen central marking / body-center ovoid stack: per
  catalog, the bee abdomen carries "a stack of dark crescents that read
  ovoid-from-distance"; usable as a low-confidence central body anchor.
- Crescent cluster -- abdomen stripe bands: the burnt-orange / black abdomen
  stripes read as a horizontal crescent run.
- Trigon cluster -- wing-spread leading-edges and antenna tips: bilateral
  pointed elements at top of frame.

Anchor quality: **medium.** Strong bilateral symmetry, but the bee has the
lowest formline density of the figural set; no single dominant eye-ovoid like
the Raven, Orca, or Butterfly. The existing registry bounds-anchor is already
marked `confidence: low`.

Whole-source reveal quality: **high.** Clean isolate, no landscape
competition, lowest cultural load in the figural set.

Cultural-load / consent: lowest in the set; bee/pollinator iconography is not
a traditional Coast Salish crest. Still: confirm with Austin before any
public surface. **Probably the lowest-risk piece for early engine-rehearsal
work**, but the anchor is doing less visual work than on the Raven or Orca.

### 7. Background-PDF series -- figure-in-landscape (collective assessment)

Pieces: `Animal_Bear_Background.pdf` (`fd53da5dd67d...`),
`Animal_Deer_Background.pdf` (`eb54f912e220...`),
`Animal_Bird_Heron_Background.pdf` (`6bfa1bc3d33a...`),
`Animal_Wolf_Background.pdf` (`56e59d6d2dfd...`),
`Supernatural_Bird_Thunderbird_Background.pdf` (`ef0e6fc1277a...`). All
verified on disk; PDF hashes match catalog. Converted SVGs exist in
`austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/` for Bear, Heron,
Deer (Bee already covered above); no Wolf-Background or Thunderbird-Background
conversions found in that folder as of this scout.

Candidate primitive anchors (per piece, conservatively):

- Hero-figure eye-ovoid (Bear, Deer, Heron, Wolf, Thunderbird) -- usable as a
  single positional anchor but partially buried in landscape detail.
- Antler-frames-sun composition center (Deer specifically) -- vertical-axis
  anchor crossing antler-tips, eye, and framed sun disc.
- Wing-ovoid joint marks (Heron, Thunderbird) -- single ovoid on the wing-
  shoulder, well-defined per catalog.

Anchor quality: **medium.** Eye-ovoids and wing-ovoids exist and are stable,
but the surrounding landscape competes for attention and makes the anchor
position less immediately readable than on an alpha-cutout figure.

Whole-source reveal quality: **medium.** Each PDF is a complete
hero-in-landscape composition with strong production polish, but figure/ground
is not "clean" in the alpha-cutout sense -- the landscape is part of the work,
which makes any reveal carry both figure and atmosphere simultaneously.

Cultural-load / consent:

- Bear, Deer, Heron: portfolio-public register, lower load. Default-OK for
  internal analysis only.
- Wolf-Background: heavily crest-restricted, plausibly self-representational
  (Sḵwx̱wú7mesh Wolf Clan). Hold.
- Thunderbird-Background: heavily crest-restricted, plausibly
  self-representational (Nam̓gis Thunderbird Clan). Hold. Also potentially the
  dramaturgical frame piece for the pearl-vision per catalog.

### 8. Pieces explicitly excluded from this scout

These are intentionally **not** scouted as first-probe candidates because
their cultural load, narrative completeness, or compositional complexity
makes them poor fits for a small primitive-anchor probe even when the anchor
case could be made:

- `Animal_Wolf_Spindle_Whorl.svg` -- ceremonial-register spindle-whorl form;
  already has anchors in the registry; cultural caution per registry entry
  explicitly requires Austin guidance before any visual probe.
- `Supernatural_Human_TheCreator_Background.svg` -- flagged as
  pearl-vision frame-piece candidate per catalog and registry; do not probe
  without explicit Austin guidance.
- `Supernatural_Snake_Serpent.pdf` -- Sisiutl-load piece; hold for explicit
  Austin signoff.
- `Supernatural_Transformer_Background.png` -- graphic-register outlier; the
  split-canvas composition is not a clean figure-on-field; cultural reading
  is unclear without Austin's input.
- `Human_Mother_Bear_Cub_Background.png` -- only human figure in the drive;
  narratively complete; highest consent floor in the set per catalog.

---

## Ranking matrix

| # | Piece | Anchor quality | Whole-source reveal | Cultural-load posture | First-probe fit |
|---|---|---|---|---|---|
| 1 | Animal_Bird_Raven_Transparent.png | high | high | mid; per-output OK required | **recommended first probe** |
| 2 | Animal_Insect_Butterfly_Transparent.png | high | high | mid; confirm face-in-wing teaching | strong alternate first probe |
| 3 | Animal_Water_Orca_Transparent.png | high | high | high (crest-restricted) | hold; do not probe without Austin signoff |
| 4 | Animal_Water_Octopus_Transparent.png | medium-high | high | high (T'lep resonance) | hold; do not probe without Austin signoff |
| 5 | Animal_Salmon_Spawn_Eggs.svg | strong (already registered) | strong | high | hold; cross-reference only |
| 6 | Animal_Insect_Bee.svg/.pdf | medium | high | low | engine-rehearsal only; anchor does less visual work |
| 7 | Background-PDF series (Bear, Deer, Heron) | medium | medium | low-to-mid | not first probe; landscape competes |
| 7' | Background-PDF series (Wolf, Thunderbird) | medium | medium | high (crest-restricted) | hold |

---

## Recommended first probe candidate

**`Animal_Bird_Raven_Transparent.png` -- raven-without-sun isolate.**

Why this piece:

- The eye-ovoid is the single strongest positional circle anchor among the
  pieces that are **not** already serving as validated spine anchors and not
  in the explicit-hold cultural-load tier.
- The alpha cutout gives the cleanest figure/ground separation in the figural
  set, so a whole-source reveal would read clearly without landscape
  competition.
- Cultural load is mid-tier (lower than Orca/Wolf/Thunderbird, higher than
  Bee/Bear/Deer), which keeps consent posture as `per-output OK required`
  rather than `hold for explicit guidance`.
- The pre-reveal sense test plausibly succeeds: a viewer attending to the
  forming eye-ovoid is likely to anticipate a head-and-wing figure resolving
  around it, so the anchor is doing real visual work.

**Recommended simplest reveal strategy: single-circle-anchor reveal.** Hold on
the eye-ovoid position; let the whole authored Raven figure resolve outward
from that single anchor. **Do not** sequence multiple anchors on the first
probe -- the eye-ovoid alone carries enough positional meaning. **Do not**
fragment the wing trailing-edge crescents or the beak/claw trigons into
isolated motifs; if any crescent/trigon work is added in a future probe,
treat it as supporting reveal cadence only, not as a primitive library.

**Strong alternate:** `Animal_Insect_Butterfly_Transparent.png` if a bilateral
dual-anchor reveal is desired. The bilateral wing-ovoid pair gives a stable
2-anchor sequential reveal with mirror-axis coherence. Defer to Austin on
whether the face-in-wing motif should be foregrounded before this is
attempted.

**Both probes remain subject to per-output Austin OK before any probe is
executed.** This scout does not authorize a probe; it documents the case
for one.

---

## What this scout did **not** do

- Did not render anything.
- Did not edit any SVG.
- Did not generate any Coast Salish design.
- Did not extract motifs.
- Did not decompose figures into reusable parts.
- Did not recolor, palette-shift, or restyle any source.
- Did not claim cultural meaning or interpretation on Austin's behalf.
- Did not write back to `austin_anchor_registry_v001.json`. New figural
  candidates are recorded only in the optional JSON config below as
  `proposed_candidate` records pending Austin review.

## Verification

- All seven directly-cited source paths were confirmed on disk
  (`austin-v2-ingest/approved/*` and
  `track2-deterministic/source-vectors/*` for SVGs;
  `austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/*` for converted
  PDFs).
- SHA-256 prefixes were recomputed for the figural PNGs and PDFs and matched
  the catalog manifest in `austin-v2-ingest/austin-piece-catalog-2026-05-16.md`.
- Internal markdown links resolve to files present in
  `docs/space-center/` and `track2-deterministic/anchor_graph/`.
- ASCII-only content (no smart quotes, em-dashes, or emoji).
- No rendering, no SVG edits, no generated artwork.
