# Sunday Internal Experiment Lane — 2026-05-17

`[INTERNAL — DO NOT SHARE]`

> **Operating policy for the next 11 days:**
> **Experiment broadly. Share narrowly. Ship only with Austin's explicit OK.**

The consent/protocol discipline does not mean "don't explore." It means: don't present the experiment as authorized meaning, and don't put it in the show until Austin authors or approves that relationship. This document is the protocol that makes that distinction mechanical, not memory-dependent.

---

## Policy gates (must hold for every render)

### Gate 1 — Folder convention
- All cross-creature experiment renders go to `track2-deterministic/morph_outputs_INTERNAL/` (NEW).
- The main `track2-deterministic/morph_outputs/` is reserved for show-staging-eligible work.
- The `_INTERNAL` suffix makes accidental inclusion in a Resolume show package, Drive share, or zip bundle visible at `ls` time.
- Both `morph_outputs/` AND `morph_outputs_INTERNAL/` are gitignored.

### Gate 2 — Per-render provenance log
- One-line CSV entry per render in `track2-deterministic/morph_outputs_INTERNAL/provenance.csv`.
- Columns: `date, pair_id, source_a, source_b, cultural_load, sharing_status, notes`.
- `sharing_status` initial value = `internal-only`. Only changes via explicit "before sharing with Austin" gate (below).
- Catches "wait, who has seen this" three weeks from now when memory fades.

### Gate 3 — "Before sharing with Austin" question pattern
- Default framing for any Austin-facing share: **"We explored X internally because Y — would you want to see what we did?"**
- NOT: "Here's what we made." That collapses the choice he gets to make.
- Austin retains the right to say no without having to evaluate the artifact.
- Records the answer in `provenance.csv` (`sharing_status` field becomes `austin-shown-approved`, `austin-shown-declined`, or stays `internal-only`).

### General rule — Containing-frame vs morph-endpoint
- For the highest-load motifs (Creator, Thunderbird in some pairs), prefer containing-frame / origin / surround role over morph-endpoint role.
- "Thunderbird as origin/frame" is a different and lighter claim than "Thunderbird as something being morphed into or out of."
- Applies unless Austin specifically signals the morph-endpoint use is appropriate.

---

## Tiered experiment queue

### Tier 1 — Low-risk, high-signal (start first)

| Pair | Input formats | Why it matters technically | Why it's low-load culturally |
|---|---|---|---|
| Animal_Insect_Bee.pdf ↔ Animal_Insect_Butterfly_Transparent.png | PDF + PNG (PDF needs decomp) | Cross-medium pipeline test (PDF→PNG path); transformation/life-cycle logic | Bee/butterfly are not protocol-loaded motifs |
| Animal_Bear_Background.pdf ↔ Animal_Deer_Background.pdf | PDF + PDF (both need decomp) | Same background-series template = controlled experiment for portrait-scene morphing | Animal-to-animal in same scene template; no lineage claims |
| Nature_Cosmic_Sun.svg ↔ Animal_Salmon_Spawn_Eggs.svg | SVG + SVG (direct) | Sun/egg/radiating-field relationship → tests particle/roe field rendering without the Wolf load | Cosmological + ecological, not familial-lineage |

### Tier 2 — Medium-risk, very interesting (after Tier 1 proves pipeline)

| Pair | Input formats | What we'd learn | Cultural notes |
|---|---|---|---|
| Animal_Bird_Raven_Transparent.png ↔ Animal_Water_Octopus_Transparent.png | PNG + PNG **(needs raster-contour adapter — not yet built)** | Air-being ↔ sea-being motion contrast; same transparent cutout format | Raven + octopus both have weight; air-water transition is a real cosmological move |
| Animal_Water_Octopus_Transparent.png ↔ Animal_Water_Orca_Transparent.png | PNG + PNG **(needs raster-contour adapter — not yet built)** | Sea-being continuity; same canvas family | Orca raises protocol load; internal-only is fine for exploration |
| Animal_Bird_Raven_Sun.svg ↔ Animal_Salmon_Spawn_Eggs.svg | SVG + SVG (direct) | Origin-light ↔ return/spawning relationship; rich | Definitely needs Austin's framing before any share — origin/return is a teaching, not just a visual |

### Tier 3 — High-load, don't avoid, sequence carefully

| Pair | Why include at all | Sequencing note |
|---|---|---|
| Animal_Wolf_Spindle_Whorl.svg ↔ Animal_Salmon_Spawn_Eggs.svg v2 | Worth improving — first test (Exp 2) exposed the egg-field problem. Treat the roe as a generative particle field, not fade-ins. | Internal v2 render to fix the technical bug. Share with Austin only if he asks how Exp 2 evolved. |
| Animal_Wolf_Background.pdf ↔ Supernatural_Bird_Thunderbird_Background.pdf | Potentially the most meaningful pair — touches Austin's own Sḵwx̱wú7mesh Wolf + Nam̓gis Thunderbird lineage (father = Xwalacktun, Squamish Hereditary Chief). | **DO NOT RENDER until we've had a trust conversation with Austin about cross-lineage exploration.** First time Austin sees this pair shouldn't be a sneak-preview — that surprise itself becomes the disrespect. Probably Tue-Fri sprint week, after the Tier 1 + 2 experiments give us something to talk about. |
| Supernatural_Human_TheCreator_Background.svg | Frame-piece use, not morph-subject use. | Use as containing field / origin surround in other pairs. Do not morph TO or FROM the Creator motif. |

---

## Tonight's overnight queue (Sat 2026-05-16 → Sun AM)

Per the tonight plan (`~/.claude/plans/ssd-tonight-2026-05-16-and-gan-resolution-question.md`):

1. **Primary (gating the Sunday sneak-peek to Pravin):** 18-sec motion render via SD + v2 LoRA img2img on Exp 4 pearl frames → `track2-deterministic/morph_outputs/`. **Status: production-candidate / internal review render only.** NOT show-staged, NOT in any Resolume package, NOT shared externally without Austin's per-output OK. The consent floor applies to anything carrying his vocabulary regardless of which pipeline produced it.
2. **Secondary (after primary completes, low cultural load, no decomp required):** Cosmic_Sun.svg ↔ Salmon_Spawn_Eggs.svg via `morph_engine.py`. **Operational note:** the engine hardcodes `OUTPUT_DIR = morph_outputs/` (line 47) with no `--output-dir` flag (line 924 argparse). For internal renders, run the engine as-is, then immediately `mv morph_outputs/<pair_id>/ morph_outputs_INTERNAL/<pair_id>/` and append a `provenance.csv` row. Engine `--output-dir` patch is a small Sunday/Monday improvement (see Parked Improvements below).

## Sunday morning continuation

1. PDF decomposition pass for Tier 1 pairs (Bee, Bear, Deer backgrounds) — Inkscape Trace Bitmap or `potrace` → SVG, then `compute_svg_bbox.py`. Desk work, not GPU work.
2. Queue Tier 1 PDF pairs into engine after decomp.
3. **PNG-only Tier 2 pairs (Raven↔Octopus, Octopus↔Orca) are BLOCKED** until a raster-contour adapter exists. Options: (a) vectorize via Inkscape Trace Bitmap / potrace first (produces SVG → engine works as-is), or (b) build a separate raster-morph path (img2img interpolation or optical-flow between PNG pairs — different pipeline entirely). Pick path Sunday or defer to Monday. Do NOT assume direct-to-engine.
4. Hold Tier 2 SVG pair (Raven_Sun↔Salmon_Spawn_Eggs) for after Tier 1 results review (its cultural load means we want to look at lighter results first).
5. Hold Tier 3 entirely until trust conversation lands.

## Parked tooling improvements (small, not blocking tonight)

- **`morph_engine.py --output-dir <path>` flag** — currently hardcodes `OUTPUT_DIR = morph_outputs/` at line 47. ~5-line argparse addition + replace `OUTPUT_DIR` references with `args.output_dir`. Removes the post-render `mv` requirement for `_INTERNAL` renders. Sunday or Monday morning desk fix.
- **Raster-contour adapter for PNG pairs** — wraps Inkscape Trace Bitmap or potrace as a preprocess step so PNG inputs become SVG inputs the engine can consume. Alternative: a separate `raster_morph.py` doing img2img interpolation between PNG endpoints. Sunday afternoon or Monday work; not tonight.

## Compute budget caveat

TELUS H200 pod has finite session time. Queue cross-creature renders BEHIND the production-candidate motion render in priority order, not parallel. If pod times out, internal experiments are the ones to drop, not the production-candidate render (which still needs Austin per-output OK before any show staging — see policy at top).

## What this is NOT

- Not a list of pairs we will ship.
- Not a list of pairs we will show Austin.
- Not a license to render Tier 3 without the sequencing discipline.
- Not a substitute for the per-output Austin OK on anything public-facing.

## References

- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/feedback_austin_consent_trust_floor.md`
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/feedback_austin_no_ai_generation.md`
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/project_austin_pearl_vision.md`
- `~/projects/salish-sea-dreaming/track2-deterministic/README.md`
- `~/projects/salish-sea-dreaming/docs/space-center/austin-consent-map.md`
