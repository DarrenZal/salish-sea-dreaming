# PDF→SVG conversion + decomposition QA report — 2026-05-18 AM

Per morning brief: convert 4 low-cultural-load PDFs (Heron, Bee, Deer, Bear), QA against source JPGs, decompose only those that pass. Do not start morph rendering until operator review.

## Summary table

| Piece | PDF→SVG | SVG size | viewBox | Paths | Fills | Suspicious BG rects | Pixel diff (mean/max) | Verdict | Decomposed? |
|---|---|---|---|---|---|---|---|---|---|
| Animal_Insect_Bee | ✓ | 21 KB | 294×243 | 53 | 8 | None | **5.2 / 255** | **PASS** | ✓ 53 atoms |
| Animal_Bear_Background | ✓ | 695 KB | 360×504 | 90 path + 15 rect | 21 | 14× (mostly 144% viewBox clip rects) | 65 / 255 | REVIEW | ✗ |
| Animal_Deer_Background | ✓ | 233 KB | 360×504 | 228 path + 6 rect | 39 | 6× (144% viewBox) | 96 / 255 | REVIEW | ✗ |
| Animal_Bird_Heron_Background | ✓ | 1.2 MB | 360×504 | 58 path + 44 rect | 18 | 41× (144% viewBox) | 118 / 255 | REVIEW | ✗ |

## Key finding: pdftocairo emits PDF page-clip rects as visible rect elements

For Heron / Deer / Bear, `pdftocairo` translated the PDF's page clipping region into multiple `<rect>` elements at 144% of the viewBox area. These show up as "suspicious big shapes" in our QA script.

Visual evidence: the heron's SVG has **41 duplicate** `<rect width="432" height="605">` elements stacking on top of each other. These are background-fill artifacts, not Austin's drawn paths.

**Recommended fix path** (operator decides whether to pursue):
- Option A: filter rects with width × height > 80% viewBox area at decomposition time (one-line script change to `decompose_austin_pieces.py`)
- Option B: pre-clean SVG files by removing those rects via xpath / xml.etree before decomposition
- Option C: ask Austin for native SVG exports for these pieces (cleanest but requires Austin time)

## Bee passes clean — decomposed + LABELED

53 atoms, 8 unique fill colors (multi-color palette including dark, mid-tone, accent colors).
viewBox 294×243 (clean, no inflation).

### Labeling results (sub-agent pass 2026-05-18 AM)

| Label | Count | Notes |
|---|---|---|
| leg | 14 | 4 main leg shafts + 8 small orange joint markers (low-confidence on joint markers — may also read as circle-oval primitives) |
| formline | 10 | Thorax/abdomen decorative shapes |
| eye | 6 | 2 main eye dots + 4 tiny pupil/highlight marks |
| wing-right | 6 | 1 main wing + 5 internal cream highlights |
| wing-left | 6 | 1 main wing + 5 internal cream highlights (symmetric to right) |
| antenna | 4 | 2 base segments + 2 outer shafts |
| head | 3 | 2 dome caps + 1 main head circle |
| stripe | 3 | 1 orange band + 1 cream lower band + 1 mid-abdomen band |
| body | 1 | Main abdomen shape |

**Bilateral symmetry verified**: 21 pairs match across centerline (wings, antennae, eyes, leg segments, all wing highlights).

**Uncertain atoms (confidence < 0.7) — 23 total** (operator may want to review):
- 8 orange leg-joint dots (atom_0012, 0013, 0014, 0016, 0021, 0023, 0024, 0026) — conf 0.55–0.60. Classified as "leg" but anatomically could also read as "circle-oval" primitives. Worth reclassifying if morph engine prefers primitive labels.
- 8 wing internal highlights (0028-0030, 0032, 0034-0036, 0038) — conf 0.60–0.65. Tiny cream sub-shapes grouped with their wing.
- 3 face/mouth formline marks (0046, 0047, 0048) — conf 0.50–0.55. atom_0046 looks like a small trigon primitive (wedge).
- 4 tiny pupil-area dots (0049-0052) — conf 0.55. Functional role unclear; tagged "eye" by proximity.

### Reclassification note

No atoms classified as `circle-oval`, `crescent`, `trigon`, `background`, or `other` — Austin's bee uses anatomical parts more than abstract primitive forms. If downstream morph engine prefers primitive-grammar labels for cross-piece routing, candidates for reclassification:
- atom_0017, 0018 (currently "stripe") could be "crescent" — they're orange/cream curved bands
- atom_0046 (currently "formline") could be "trigon" — wedge shape
- 8 orange leg-joint dots could be "circle-oval"

Path: `austin-v2-ingest/decomposed/Animal_Insect_Bee/`
- `atom_metadata.csv` (53 rows, all labeled)
- 53 × `atom_NNNN.png` (isolated shapes)
- 53 × `atom_NNNN_context.png` (whole-piece highlight)
- `_atom_contact_sheet.png` (unlabeled grid)
- `_atom_contact_sheet_labeled.png` (label-color-bordered grid with confidence; amber caption = low-confidence)

## QA artifacts produced

| Artifact | Path |
|---|---|
| Conversion folder | `austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/` |
| 4 converted SVGs | `Animal_Bird_Heron_Background.svg`, `Animal_Insect_Bee.svg`, `Animal_Deer_Background.svg`, `Animal_Bear_Background.svg` |
| QA contact sheet (all 4 pieces side-by-side: source / rendered / diff / stats) | `austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/_QA/_QA_contact_sheet.png` |
| Per-piece QA panels | `_QA/<Piece>_qa_panel.png` |
| Rendered SVG previews | `_QA/<Piece>_svg_rendered.png` |
| Pixel diff heatmaps | `_QA/<Piece>_diff.png` |
| Bee atom contact sheet | `austin-v2-ingest/decomposed/Animal_Insect_Bee/_atom_contact_sheet.png` |
| Bee atom metadata | `austin-v2-ingest/decomposed/Animal_Insect_Bee/atom_metadata.csv` |

## Verdicts per piece

### ✓ Animal_Insect_Bee — PASS, DECOMPOSED

- Visual match: extremely close (mean diff 5.2/255 = ~2% pixel-level)
- Clean SVG: no background-clip rect artifacts
- Multi-color palette: 8 fills including dark, mid-tone, and accent colors
- 53 paths is appropriate complexity (not too sparse, not bloated)
- **Cleared for morph experiments** if operator greenlights

### ⚠ Animal_Bear_Background — REVIEW

- Pixel diff 65/255 — moderate. Could be due to:
  - Background clip rects washing out diff measurement
  - Color rendering differences (pdftocairo may emit gradient stops differently than original)
- 14 suspicious large rects (1 at 95% viewBox = likely actual background fill; 13 at 144% = clip artifacts)
- 90 paths is appropriate
- **Recommendation**: filter background rects from atom set, then re-evaluate

### ⚠ Animal_Deer_Background — REVIEW

- Pixel diff 96/255 — high. Likely background-rect dominance + color rendering
- 6 suspicious 144% rects
- 228 paths (most complex of the 4)
- 39 unique fills (richest palette)
- **Recommendation**: filter background rects; if filter works, this would be a rich decomposition candidate

### ⚠ Animal_Bird_Heron_Background — REVIEW

- Pixel diff 118/255 — highest. Lots of duplicated background-clip rects (41× the same 432×605 rect)
- 58 paths is reasonable but the rect artifact volume is concerning
- 18 unique fills
- **Recommendation**: this one needs the most cleanup. Consider pre-filtering the SVG with `sed`/`xmlstarlet` to drop all rects with `width>360` before decomposition.

## Operator review checklist

Before greenlighting any morph experiment with these:

1. Open `austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/_QA/_QA_contact_sheet.png` and visually confirm:
   - **Bee**: source JPG and rendered SVG look essentially identical
   - **Bear/Deer/Heron**: rendered SVG vs source JPG — is the artwork content there (just visually obscured by overlay rects)? If yes, filtering should rescue them. If no, the conversion lost actual paths.

2. Open `austin-v2-ingest/decomposed/Animal_Insect_Bee/_atom_contact_sheet.png`:
   - Do the 53 atoms look like recognizable parts of the bee (wings, body, legs, eyes)?
   - Are any atoms obvious background artifacts that should be excluded?
   - Decide whether to invest in AI labeling (sub-agent pass) before any morph experiment

3. Decide on background-rect filter approach for Bear/Deer/Heron:
   - A) script-level filter at decomp time (~10 min code)
   - B) one-time SVG pre-clean (~10 min sed/xpath)
   - C) ask Austin for native SVG exports (requires Austin time)

## No morphs rendered

Per brief, no Heron→Salmon or other pair morphs started. Decision required from operator before any rendering.

## Bee-alive proof results

### v001 — DECOMPOSITION PROOF (subtle breathing, NOT show artifact)

`track2-deterministic/morph_outputs_INTERNAL/bee_alive_v001/`

Validates the PDF→SVG→decomposition pipeline produces usable atom data for at least some atoms (body, head, legs, antenna — all dark-colored). Subtle wing shimmer + body hover applied via the same v003c breathing pattern that worked for Cosmic_Sun. Motion intentionally subtle per first brief.

Operator verdict: "proves the Bee decomposition is usable, but the motion is not compelling." → kept as decomposition proof, not promoted as show artifact.

### v002 — WING FLUTTER ATTEMPT (BLOCKED by decomposition limitation)

`track2-deterministic/morph_outputs_INTERNAL/bee_alive_v002_wing_flutter/`

Attempted to change mechanic per operator second brief: wing hinge rotation at 8 Hz + motion blur + body hover + antenna twitch. Hinges were computed as wing-mask pixels closest to body center.

**BLOCKED by decomposition pipeline limitation.** The wing atoms (atom_0027 + 5 highlights + atom_0033 + 5 highlights) have CREAM fill color (RGB ≈ (254, 253, 248)). The decompose script renders each atom in its actual color on a WHITE background, so cream-on-white atoms are visually indistinguishable from background. My `255 - L` mask extraction treats them as "background pixels = transparent" → wing masks are essentially empty.

Diagnostic confirmed:
- `atom_0027.png` opens as RGBA with alpha=255 everywhere AND mean RGB (254, 253, 248) — atom indistinguishable from background
- `atom_0033.png` same
- `atom_0003.png` (body, dark RGB ≈ (33, 27, 23)) works correctly

All 3 hinges computed identically at (519, 458) because empty wing-masks fall back to body-center.

**This affects multi-color pieces broadly.** The 5 originally-decomposed pieces (Cosmic, Raven, Wolf, Salmon, TheCreator) didn't hit this because their atoms are mostly dark.

**Fix path** (queued, NOT done overnight — more than a quick pass):
- Modify `scripts/decompose_austin_pieces.py` to render atom masks via SVG path geometry directly (not via image rendering with white BG), producing clean alpha masks regardless of fill color
- OR use ImageMagick to render the SVG with all atoms BUT the target one hidden, diff against full render to isolate the target's pixels
- Either approach ~1-2 hrs to implement + verify

### Move-on status

Per operator brief: "If that is more than a quick pass, document Bee-alive v001 as 'decomposition proof, not show artifact' and move on." DOING THAT.

- **v001**: kept as decomposition proof of pipeline functionality on dark atoms
- **v002**: kept as failed control documenting the cream-atom decomposition limitation
- **Bee→Salmon morph**: blocked until decomposition fix; would inherit the same cream-atom bug
- **Heron/Bear/Deer**: blocked by separate background-clip-rect issue from PDF conversion
- **All show-quality multi-color piece animation**: requires decomposition pipeline upgrade first

## Task #56 — decomposition mask extraction upgrade — SHIPPED 2026-05-18 AM

Operator greenlit Task #56 immediately after Bee-alive v002 failed. Built `scripts/extract_atom_masks.py` adding SVG-path-geometry-based alpha mask extraction alongside existing isolated PNGs. Bypasses the raster-contrast bug entirely.

### Mechanism

For each atom, build a single-element SVG with:
- Target element's `fill` FORCED to `#000000` (black)
- `stroke="none"`, `opacity="1"`, `style=""` (overrides cleared)
- Parent transforms preserved via `<g transform="...">` wrappers

Render with ImageMagick `-background none` → black-on-transparent silhouette. Alpha channel = atom mask, color-independent.

Saves `atom_NNNN_mask.png` alongside existing files. Adds `mask_png` column to `atom_metadata.csv` (existing labels + columns preserved; backup at `atom_metadata.csv.pre_mask_backup`).

### Acceptance criteria verification

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Bee wing atoms produce non-empty masks | ✓ PASS | atom_0027 (wing-right): 2490 opaque px at centroid (64%, 70%); atom_0033 (wing-left): 2485 opaque px at centroid (37%, 70%). Bilateral, properly positioned. |
| 2 | Existing dark atoms still work | ✓ PASS | Cosmic_Sun re-processed: 39/39 atoms produce valid masks. Sample: atom_0000 (4900 px), atom_0010 (30280 px), atom_0020 (123 px tiny). |
| 3 | Output PNGs/context sheets remain compatible | ✓ PASS | New mask PNGs added as additional files. CSV gains `mask_png` column; all existing columns + labels preserved. CSV backed up before modification. |
| 4 | Rebuild Bee atom contact sheet | ✓ PASS | `_atom_contact_sheet_labeled_v2_new_masks.png`. Renders mask-alpha as label-colored silhouette → cream wing atoms NOW VISIBLE. |
| 5 | Old-vs-new mask diagnostic | ✓ PASS | `_old_vs_new_mask_diagnostic.png`. 6 atoms compared: 3 wings (OLD broken → NEW fixed), 1 body (OLD worked → NEW unchanged), 1 stripe (OLD partial), 1 antenna (OLD worked). |
| 6 | No new Bee-alive / morph videos | ✓ PASS | No animation rendering performed in this pass. |

### What's now possible

- **Bee-alive v003 with full wing animation** — wing-left and wing-right groups now have real masks. v002 wing-hinge mechanic can be retried with non-empty masks. (Not done tonight per criterion #6.)
- **Any multi-color piece** — same mask extraction works regardless of fill color. Pieces with colored atoms (when we get more SVGs decomposed) no longer require dark fills.
- **Layer-extraction workflows** — Resolume composition now has reliable per-atom alpha layers, not raster-contrast guesses.

### Files added overnight

- `scripts/extract_atom_masks.py` — the upgrade script (run per-piece or `--all`)
- `scripts/build_mask_diagnostic.py` — diagnostic builder
- `scripts/build_bee_atom_contact_sheet_v2.py` — updated contact sheet using new masks
- `austin-v2-ingest/decomposed/Animal_Insect_Bee/atom_NNNN_mask.png` × 53
- `austin-v2-ingest/decomposed/Animal_Insect_Bee/_old_vs_new_mask_diagnostic.png`
- `austin-v2-ingest/decomposed/Animal_Insect_Bee/_atom_contact_sheet_labeled_v2_new_masks.png`
- `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atom_NNNN_mask.png` × 39
- CSV updates: `mask_png` column added to Bee + Cosmic_Sun metadata (with backups)

### Recommended next-session order

Per operator: this is foundational. After review:

1. Re-process remaining 3 pieces (Raven_Sun, Wolf_Spindle, Salmon_Spawn, TheCreator) via `python3 scripts/extract_atom_masks.py --all` (~30 sec each).
2. Retry Bee-alive v003 with wing-flutter mechanic on real masks.
3. Bee↔Salmon morph using Lane 2E routing rule now feasible.
4. Heron/Bear/Deer still blocked by PDF page-clip-rect issue — separate fix.

## Next-step recommendation (only if operator greenlights)

If Bee QA visually checks out AND operator wants a low-cultural-load morph proof-of-concept:

**Bee ↔ Salmon_Spawn** is now feasible. Both decomposed. Bee has clean palette + clean atoms. Salmon has 184 roe + body. Could test Lane 2E routing rule:
- Bee body → salmon body (formline-primary atoms)
- Bee wings → some subset of salmon roe (smaller atoms)
- Bee eye → salmon eye-focal-oval
- Bee legs → salmon fin-tail / formline-tertiary

Effort: ~2-3 hrs render + iterate. Lower cultural load than any Austin-Austin pair we've attempted.

Heron / Deer / Bear: defer until background-rect issue resolved.
