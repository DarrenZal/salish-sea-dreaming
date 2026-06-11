# Resolume Show Package Checklist — 2026-05-14

Purpose: define the file package that can be handed to Prav / John / venue testing without smuggling in aesthetic or protocol decisions.

Status: working operator checklist. It does not approve any content for projection. It defines where approved content should land once approval exists.

## Package Principle

Resolume should receive simple, explicit assets:

- one calibration set
- one or more per-panel clip sets
- a provenance note for every clip
- an approval note for every Austin-related clip
- a fallback path that can run if the center lineage layer is not approved yet

Do not hand Resolume a mixed folder of experiments. The package should make it obvious which files are safe to project, which are internal references, and which are excluded.

## Proposed Folder Shape

```text
show-package-space-centre-vYYYYMMDD/
  00_README_OPERATOR.md
  01_calibration/
    synthetic_projector_test_4k.png
    alignment_grid_1920x1080.png
  02_panel_clips/
    L_lens_science/
    C_lineage_pearl/
    R_water_bioregion/
  03_wide_masters/
    pearl_master_5760x1080.mov
    pearl_master_notes.md
  04_sources_provenance/
    footage_sources.md
    ai_workflow_sources.md
    live_data_sources.md
    licenses.md
  05_approval_records/
    austin_output_approvals.md
    public_language_approvals.md
  99_internal_do_not_project/
    dry_run_track2/
    failed_or_unapproved_tests/
```

Rules:

- `02_panel_clips/` is the only folder Resolume should need for show playback.
- `99_internal_do_not_project/` can travel with the archive, but should not be loaded into the show deck.
- If a clip has no provenance note, it does not go into `02_panel_clips/`.
- If a clip contains Austin source forms, Austin-styled AI output, or public-facing cultural wording, it also needs a row in `05_approval_records/`.

## Clip Specs

| Item | Target |
|---|---|
| Per-panel resolution | 1920x1080 |
| Projector assumption | three 1080p projectors |
| Wide master if used | 5760x1080, then sliced to 3 panels |
| Frame rate | match show stack, preferably one rate across all clips |
| Loop length | 7:00 master cycle, plus shorter test loops if needed |
| Audio | none unless explicitly assigned elsewhere |
| Filename style | `panel_role_content_status_version.ext` |

Example names:

```text
L_lens_tide_footage_raw_20260514_v01.mov
C_lineage_pearl_approved_track2_20260516_v01.mov
R_water_bioregion_herring_raw_20260514_v01.mov
```

Avoid filenames that hide status, such as `final.mov`, `test2.mov`, or `austin_good.mov`.

## Package Variants

### Variant A — No Austin Drive Yet

Use if the drive still has not landed.

Allowed show-package content:

- calibration plate
- raw or lightly graded underwater footage, pending Moonfish / Denning reuse confirmation
- non-cultural abstract pearl background
- live tide / Fraser modulation if TD is available

Center panel posture:

- quiet pearl / water / particle interior
- no symbolic foreground
- no Track 2 dry-run placeholder primitives
- no v1.5 LoRA outputs

This is a viable technical rehearsal package, not the desired artistic package.

### Variant B — Austin Drive Landed, v2 LoRA Passes Still Eval

Use after `scripts/austin_v2_pipeline.py` completes train + eval and the v2 outputs pass still-image review.

Allowed additions:

- v2 style-test outputs in `99_internal_do_not_project/` for review
- candidate atmospheric style clips in `99_internal_do_not_project/`
- approved raw source plates in provenance records

Still not allowed in `02_panel_clips/`:

- v2 LoRA clips unless Austin approves the exact output
- style-transfer motion unless the still gate and temporal smoke review both pass
- any synthetic crest or symbol invented from scratch

### Variant C — Austin Approves Track 2 Primitives / Morphs

Use after screenshare review and explicit approval rows.

Allowed additions:

- approved Track 2 rendered morphs in `C_lineage_pearl/`
- approved center-panel stills or loops
- side-panel echoes only if Austin approves that placement

Required records:

- source piece
- primitive label
- morph pair ID
- output filename
- approval date / reviewer
- allowed context: internal only, projector test, public show, sponsor still, or archive

### Variant D — Full Technical Dress

Use when both content and infrastructure are ready.

Required before this package:

- Austin approval rows updated
- Moonfish / Denning reuse terms confirmed
- live data bridge verified against TD or substituted with cached/synthetic values
- Resolume deck built from `02_panel_clips/`
- Advanced Output mapped to the three 1080p projectors
- show package copied locally on the 3090 / 5090 machine

## Resolume Deck Shape

Suggested layer order:

| Layer | Content | Notes |
|---|---|---|
| 1 | black / emergency still | bottom safety layer |
| 2 | calibration / alignment | disabled during show |
| 3 | pearl background | all panels |
| 4 | underwater footage | left + right emphasis |
| 5 | live-data modulation / TD feed | if TD active |
| 6 | center lineage layer | Austin-approved only |
| 7 | subtle particles / breath overlay | keep seams low-detail |
| 8 | emergency cover / fade-to-black | top safety layer |

Do not rely on layer names alone to carry approval state. Approval state lives in the package records and filenames.

## Calibration Pack

Current ready item:

- `austin-reference/john-projector-test-pack-v1_2026-05-13.zip`

Use this for projector behavior characterization, not show preview. It contains:

- synthetic projector calibration plate
- internal AI stress plates
- README with caveats

When a real show package exists, keep the John pack separate from it. The John pack is diagnostic material. It is not a content folder.

## Provenance Requirements

Every show-package asset needs one provenance row:

| Field | Meaning |
|---|---|
| filename | exact packaged filename |
| source | raw footage, Austin source, Track 2, v2 LoRA, live data, TD render, calibration |
| source path | repo path or external source note |
| approval dependency | none, Austin, Prav, venue, Moonfish/Denning, Carol Anne |
| public allowed? | yes / no / pending |
| notes | restrictions, known artifacts, or fallback role |

Austin-related files need extra fields:

- source piece or source file
- consent scope
- output approval state
- whether derivatives are allowed
- whether revocation / removal terms have been captured

The canonical approval source remains `docs/space-center/austin-consent-map.md`. Do not duplicate approval truth in multiple places; package records should point back to consent-map rows.

## Hard Exclusions

These do not go into a projector-ready folder:

- Track 2 dry-run placeholders
- any output with `[DRY-RUN]` burned in
- v1.5 LoRA proof images
- failed AnimateDiff outputs
- IP-Adapter outputs based on installation-context photos
- scraped portfolio context photos presented as source design plates
- public-language drafts still marked `[PENDING AUSTIN REVIEW]`
- any unapproved AI-generated crest-like form in Austin's register

If one of these is useful for operator learning, keep it under `99_internal_do_not_project/` with a plain-language warning.

## Open Technical Checks

| Check | Why it matters | Current posture |
|---|---|---|
| Autolume output path | Spout switch depends on the actual patched `visualizer.py` or installed sender | unresolved until Prav / 3090 confirms |
| TD live feed | tide / Fraser bridge is locally tested, but not live in TD | waits on 3090 / TD access |
| Resolume Advanced Output | three 1080p projector map must be confirmed on the actual machine | venue / John test |
| Moonfish / Denning reuse | raw footage fallback depends on reuse terms | use `docs/space-center/moonfish-denning-reuse-confirmation-2026-05-14.md` before public package |
| 7-minute loop seam | transit audience needs a clean re-entry point | test once first clips exist |

## Operator Build Checklist

1. Build or collect candidate assets outside the package folder.
2. Reject anything that violates the hard exclusions.
3. Slice wide masters into per-panel 1920x1080 clips.
4. Put only projection-safe clips in `02_panel_clips/`.
5. Add provenance rows before importing clips into Resolume.
6. Add approval references for Austin-related outputs.
7. Import `02_panel_clips/` into Resolume.
8. Test calibration plate first, then raw footage, then center lineage layer.
9. Run a full 7-minute loop and check seams / brightness / panel balance.
10. Archive the package with date, version, and checksum.

## Validator

Create a clean package skeleton:

```bash
python3 scripts/scaffold_resolume_package.py show-package-space-centre-vYYYYMMDD/
```

Before venue handoff, run:

```bash
python3 scripts/validate_resolume_package.py show-package-space-centre-vYYYYMMDD/
```

The validator checks:

- required package files and directories
- expected panel folders
- `02_panel_clips/` media dimensions
- mixed frame rates across panel clips
- hard-exclusion tokens in projector-ready filenames
- whether panel media filenames appear in provenance / approval records

Passing this script does not mean the package is culturally or artistically approved. It only means the package is structurally clean enough to hand to Resolume.

## Day 4 Use

If Austin's Drive does not land overnight, use this checklist to prepare Variant A and keep the package technical. If the Drive lands and v2 passes, use Variant B for internal review only. The first true public candidate package is Variant C, because it requires explicit Austin approval of center-panel forms and morph outputs.
