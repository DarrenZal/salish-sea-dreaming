# Austin Review Questions — Interactive Dream Grammar — 2026-05-20

Status: INTERNAL prep brief for the operator. Not yet shared with Austin. The 10
questions below are condensed from the dream-grammar provenance file. Everything
in the interactive dream pipeline stays internal and paused until Austin answers
them.

## Purpose

The interactive dream pipeline's grammar file
(`track2-deterministic/primitive_grammar/dream_grammar_provenance_v001.yaml`)
carries 10 unresolved questions for Austin. They gate the lane: the schema /
validator / renderer engineering (WS-1) can proceed without them, but **nothing
renders to a public surface, and the grammar itself may revise, until Austin
sets these boundaries.** This brief keeps the questions low-effort for him given
his limited bandwidth this week — ready for the next Austin review slot.

## How to use this

Each question lists **what it unblocks** and **our internal working assumption**
— which is pause-by-default (the safe reading). Austin can confirm, correct, or
defer each one. A confirm is a thumbs-up; a correction revises the grammar to
v002; a defer keeps that branch paused.

## The 10 questions

| # | Question | What it unblocks | Internal working assumption (pause-by-default) |
|---|---|---|---|
| 1 | Are the working shape labels — circle-like, crescent-like, trigon-like, S-crescent, curved trigon, oval, smooth mass, line/path — acceptable internal terms, or should any be renamed before review? | Terminology in every internal doc and the scene-plan schema. | Provisional internal labels only, no cultural claim; renamed on Austin's word. |
| 2 | Can the circle → crescent → crescent → curved-trigon phrase be used internally across pond ripple, rain impact, river current, waterfall descent, and mist — or should some water states stay separate? | Whether one shared water-phrase template covers all water in the 5 test prompts, or each state needs its own. | Used as one shared internal template; each state flagged as its own review question. |
| 3 | Is mist/cloud allowed partial low-contrast crescent / S-crescent phrases, or should mist stay non-primitive atmosphere until a dedicated cloud direction? | The `clouds` subject mapping and any mist layer. | Mist stays low-contrast partial-phrase, internal-only; no public cloud grammar. |
| 4 | Can rain-to-snow use sparse attached radial / harmonic cells, and what keeps that from reading as sacred geometry, detached sun rays, or unapproved snow symbolism? | The P04 snowflake (the scalar-field six-ray cells). | Snow = sparse attached radial cells, internal-only; debug overlays prove it is not a mandala; never framed as sacred geometry. |
| 5 | Which animal figure behaviors, if any, are acceptable for internal review — salmon schooling / current-following, bird flock paths, orca breach paths, wake-only motion, silhouette-safe masses, or no body depiction at all? | What is even explorable for P01 (orca), P03 (salmon), P05 (birds). | Functional motion + silhouette-safe masses only; no body / face / eye / fin detail; all internal. |
| 6 | Where is the boundary between an allowed circle-like origin / eddy and a review-needed eye, face, joint, body core, roe field, or animal/person figure? | The circle-vs-eye line across every prompt. | Circles are origins / eddies only; any eye / face read is flagged review-needed and not rendered. |
| 7 | Should prompts such as "children playing on the beach" be blocked entirely, reduced to environmental beach/water structure, or allowed only as non-identifiable schema placeholders? | P02. | P02 rendered environment-only; human figures recorded in the schema but not drawn; blocked until Austin rules. |
| 8 | Are Thunderbird, double-headed serpent, Goat-man, TheCreator, and other supernatural / named beings excluded from this pipeline unless Austin directly requests a specific reviewed scene? | Whether the pipeline ever touches named beings. | Excluded / blocked; the pipeline never generates them unless Austin directs a specific reviewed scene. |
| 9 | Which Austin source files are morphology reference only, which may be exact-source inputs, and what approval record is needed before any source-vector animation or public output? | Pipelines B/C and any source-vector work; the reference-vs-exact-source line. | All Austin source = morphology reference only; no exact reuse, tracing, or source-vector animation; blocked without explicit approval. |
| 10 | Beyond file path, output hash, prompt ID, pipeline ID/version, grammar hash, scene-plan schema version, safety status, date, and decision — what other fields should a public-output approval record require? | The per-output review-record format every future approval uses. | Those nine fields are the current proposed record; asking if Austin wants more (e.g. territory wording, attribution line, delete-by date). |

## What we are NOT asking

We are not asking Austin to approve any rendered output, any visitor-generated
image, or any public use. Everything the pipeline produces stays internal until
he reviews a specific, named output. These 10 questions only set the
**boundaries of an internal R&D experiment** — what is safe to explore, what to
pause, and what to block — consistent with the per-output consent floor
(default-pause, not default-ship).

## Sources

- `track2-deterministic/primitive_grammar/dream_grammar_provenance_v001.yaml` — `gaps_questions_for_austin`
- `docs/space-center/dream-grammar-provenance-2026-05-20.md` — human companion
- `docs/space-center/interactive-dream-pipeline-execution-plan-2026-05-20.md` — execution plan this brief supports
