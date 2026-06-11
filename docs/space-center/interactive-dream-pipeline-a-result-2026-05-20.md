# Interactive Dream Pipeline — Pipeline A Result — 2026-05-20

Status: INTERNAL R&D result record. Not Austin-approved. Not public-use. Not a
cultural-meaning claim. Not a general Coast Salish grammar claim. Per-output
Austin review gates all public use.

Companion to `interactive-dream-pipeline-execution-plan-2026-05-20.md` (the plan)
and `interactive-dream-pipeline-comparison-plan-2026-05-20.md` (the experiment
design). This document records what was built and verified, and what was not.

## Summary

**Pipeline A — the deterministic, no-GPU, no-diffusion scene-graph pipeline — is
built and verified.** Workstreams WS-1, WS-2, and WS-3 executed it end to end:

```text
visitor prompt  →  provenance-tagged scene plan (validated against the grammar)
              →  R1 deterministic scene-graph renderer  +  R2 scalar-field /
                 cymatics renderer
              →  reproducible, grammar-bounded, internal-only stills
```

This answers the comparison plan's core question for Pipeline A: the narrow,
deterministic pipeline works, and its output is reviewable, reproducible, and
culturally bounded — with no GPU and no diffusion.

## What was built

- The **`track2-deterministic/interactive_dream/`** package — scene-plan JSON
  schema, validator + grammar-provenance cross-check, grammar loader,
  blocked-subject checker, R1 scene-graph renderer, R2 scalar-field/cymatics
  renderer, manifest / debug-overlay / contact-sheet / scoring tooling. **93
  pytest tests, green.**
- **25 comparison stills** — 5 prompts (P01–P05) × 5 seeds (1001–1005) — under
  `morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/A_deterministic_primitives/`,
  plus the WS-1 contract slice.
- Run artifacts: `RUN_MANIFEST.json`, `SCORING_SHEET.md`, two contact sheets,
  `NO_PUBLIC_USE_INTERNAL_ONLY.txt`.

Workstream summary: **WS-1** = schema + validation + R1 renderer; **WS-2** = the
comparison sweep + a phrase-layout redesign (fixed an R1 crash on `line`-token
phrases and the WS-1 "fish-read"); **WS-3** = the R2 scalar-field/cymatics
adapter (reuses the existing `scripts/cymatic_*` field engine on
`scipy.ndimage` + numpy — no opencv). Each workstream's RUN_NOTES are in the
package.

## Verified (independently re-checked by the orchestrator)

| Property | Result |
|---|---|
| Gate 0 — 7 hard binary gates × 25 stills | **25/25 pass** |
| Tests | 93 pytest, green |
| Determinism | re-render byte-identical (R1 and R2) |
| Code-consistency | all 25 stills + contract slice rendered with current code |
| Grammar provenance | every visible atom traces to `dream_grammar_provenance_v001` — validator-enforced; a `kind` disagreeing with the grammar is rejected |
| Renderer isolation | the renderer never receives raw prompt text (test-asserted) |
| Manifest honesty | every recorded SHA256 matches disk |

## What each prompt shows (honest read)

- **P01 `orca breaching`** — a breach arc with spray wavefronts, wake crescents,
  and a release trigon over a water mask. No orca body / face / eye — functional
  motion only, the intended silhouette-safe abstraction.
- **P02 `children playing on the beach`** — environment-only: a shoreline with
  wave-edge crescents. The human `children` entity is recorded
  `safety_status: blocked`, referenced by no structure, and **never drawn**
  (verified). Stays environment-only until Austin resolves the human-beach
  question.
- **P03 `salmon swimming up a river`** — an S-curve river band with sparse
  current ripple-marks and an alternating-side wake trail. No salmon body /
  glyph. The river and salmon-motion structures ride near-identical S-curves and
  crowd slightly.
- **P04 `rain becoming snow on a mountain`** — rain-impact wavefronts (R1) plus a
  sixfold snowflake motif (R2): six sparse arms from a faint centre, attached
  crescents and trigon ray-tips, large negative space — reads sixfold, **not a
  mandala**. The "mountain" renders as a rounded-rectangle mask, not a mountain
  shape.
- **P05 `birds flocking at sunset`** — a flock-path arc with wake crescents (R1)
  plus a sixfold radiant sun motif (R2), rays attached to a centre. The sun
  reads as a hard mechanical cog/star rather than an organic sun.

## Draft scores — and the honest caveat

`SCORING_SHEET.md` carries draft Gate 1 scores (P01 15, P02 15, P03 15, P04 18,
P05 17 — of 18), explicitly marked a dev-worker draft needing confirmation.
Orchestrator read: **the draft scores skew optimistic on prompt fidelity** —
P04 at 18/18 while its mountain is a rounded panel, P05 at 17 while its sun is a
mechanical cog. The verified result is *the pipeline works, is reproducible, and
is provenance-bounded* — not *the stills are show-quality*. They are internal
R&D artifacts; real Gate 1 scoring needs human eyes.

## Known flagged items (none are stop conditions)

- P04 "mountain" renders as a rounded rectangle — an R1 `draw_mask` geometry
  limitation; a mask-shape pass would fix it.
- P05 sun reads as a hard mechanical cog — an R2 aesthetic note; the
  canon-critical rule (rays attached to a centre, never detached) **is** met.
- P03's river and salmon-motion structures ride near-identical S-curves and
  crowd slightly — a scene-plan geometry note, not a renderer fault.
- Draft Gate 1 scores need operator / Austin confirmation.

## Not done / parked (deliberate)

- **WS-4 GPU verification** — not run. It gates the optional diffusion lane.
- **Pipeline B** (procedural pre-finish + diffusion finisher) and **Pipeline C**
  (diffusion → edge-extract → cleanup) — **not built**. The original brief was
  explicit: "treat diffusion as optional async experimental," "do not assume
  SD/LoRA is the winner." Pipeline A complete is the deterministic-renderer
  result the brief said to prefer.
- **Per-output Austin review still gates all public use.** Every still is
  internal R&D; the renderer stamps every manifest `internal_only` /
  `not_austin_approved` / `not_public_use`.
- The 10 grammar questions for Austin are parked as a prepared one-pager
  (`austin-grammar-review-questions-2026-05-20.md`) for whenever that
  conversation happens — not pushed at him.

## Where things live

| Artifact | Path |
|---|---|
| Package (code, schema, scene plans, tests) | `track2-deterministic/interactive_dream/` |
| Run commands | `track2-deterministic/interactive_dream/README.md` |
| Workstream logs | `track2-deterministic/interactive_dream/RUN_NOTES.md` |
| 25 stills + run artifacts | `track2-deterministic/morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/` |
| Contact sheets | `…/contact_sheet_all_final_1920x1080.png`, `…/contact_sheet_debug_overlays_1920x1080.png` |
| Gate 0 per-still detail | `…/RUN_MANIFEST.json` |
| Draft Gate 1 scores | `…/SCORING_SHEET.md` |

The whole `interactive_dream/` package and its output directory are new and
untracked — ready to commit when the operator chooses.

## Boundary

Every artifact recorded here is internal R&D. Nothing is Austin-approved,
public-ready, or a cultural-meaning claim. Public projection, publication,
recording, sponsor/press use, visitor-facing display, and external sharing
remain blocked until Austin reviews the exact output. The six-ray cymatic
motifs are radial-topology candidates, not approved snow or sun grammar.
