# Overnight Co-Dreaming Experiments — 2026-05-21

Status: INTERNAL R&D, **complete.** 6 iterations, ~120 images, architecture validated. Not Austin-approved. Not public-use.

---

## ☀️ Morning brief (read this first)

**The visitor-surface architecture works.** Validated across 6 iterations and ~120 images: concrete, emotional, abstract, memory, multi-subject, cultural-load, narrative, edge-case (emoji, gibberish, pop-culture, heavy emotion). Zero failure modes by iter6.

**Go look at:** `track2-deterministic/morph_outputs_INTERNAL/overnight-codreaming-2026-05-21/_best_of/_best_of_contact_sheet.jpg` — 22 curated images. *This is the visitor surface in pictures.* Bring this to Pravin.

**The architecture:** `visitor prompt → LLM (me) expands to concrete-scene description → SDXL with the salish_dreampaint template + strong negative prompt → recognizable, on-tone, no-pastiche image`.

The LLM-expansion step does three jobs: (1) interpretation (turns "feeling free" into "person on sunlit hill, arms raised"), (2) recognizability (the visitor sees their dream, not generic AI slop), (3) safety (strips cultural-cued language; replaces with descriptive physical scenes, so the model never gets the "Indigenous style" cue that triggers pastiche). The negative prompt is the second-line safety.

**What's settled:**
- ✅ Recognizability — even on abstract prompts ("becoming wind" → figure in windswept grass; "homesickness" → window seat with warm cup; "death" → empty chair by a dusk lake)
- ✅ Tone — coherent painterly Salish Sea register across all 22 best-of images
- ✅ Safety — cultural-load prompts (thunderbird, totem pole, spirit bear, elders, ceremony) all rendered as natural-subject scenes, *zero pastiche* across all 20 cultural-load images
- ✅ Robustness — edge cases (🌊, "asdfghjkl", "I love you", "Star Wars") all handled gracefully
- ✅ Variance — across seeds, subjects stay consistent, mood varies (good for installation: each visitor gets unique image, recognizes their dream)

**Honest caveats:**
- 12–15s per image on the 3090 → 15s visitor wait. Mitigations: "your dream is taking shape" animation; or pre-render common-prompt library; or upgrade to Flux.1-schnell (4-step, faster) once HF token-gated access is arranged
- Single-seed-per-visitor is the sensible install behavior (re-running same prompt yields different mood)
- **Per-output Austin review still gates any public display.** Internal R&D until he sees the best-of and signs off

**Recommended next moves (in order):**
1. **Look at `_best_of/`** — confirm the register matches your intent
2. **Show Pravin** the `_best_of/_best_of_contact_sheet.jpg` — get his read on whether this is the visitor surface
3. **Show Austin** a curated 4–6 from `_best_of/` (especially the cultural-safety ones: thunderbird-as-eagle, spirit-bear-in-rainforest, elders-as-hands, ancestors-as-cedars-with-ghosts) framed *clearly as internal R&D output, not as his work*. Ask whether this register-and-architecture honors his protocol or needs adjustment.
4. **If yes from both:** wire the live pipeline. Pieces needed: visitor web app (exists, Phase 1) → local Claude call for expansion (or pre-craft expansions for top-N common prompts) → 3090 SDXL gen → Resolume display.
5. **If no:** the deterministic-renderer + curated-pre-rendered-clip fallback (from earlier work) remains viable as the safety surface.

---

## The Goal

A visitor at the installation is asked to "co-dream with the Salish Sea" — they type a random prompt — they see their dream visualized in a way they recognize **without a doubt** (not so abstract they can't see it), and in the project's tone (not generic AI slop, not pastiche of Coast Salish art). Find the register.

## Method

Plain SDXL 1.0 base on the 3090, no LoRA, no ControlNet, no cultural-style terms in prompts. Topological / atmospheric / palette constraints only. Multi-iteration: each iteration informed by reviewing the previous. The orchestrator (Claude) does the "LLM step" between iterations — crafting prompts, expanding visitor inputs into concrete visual scenes.

All outputs land under `track2-deterministic/morph_outputs_INTERNAL/overnight-codreaming-2026-05-21/`.

---

## Iteration 1 — Template Sweep

8 visitor prompts × 4 style templates = 32 images. Goal: which register handles arbitrary visitor inputs best?

Folder: `iter1_template_sweep/` · Contact sheet: `iter1_template_sweep/_contact_sheet.jpg`

**Verdict:**
- **`atmospheric_realism` ← clear winner.** Painterly oil register, single recognizable subject, soft PNW light. Works consistently across all 8 prompts.
- `painterly_marine` close second — same quality with stronger teal/bioluminescent palette. Stronger for water themes, slightly washed-out for kitchen/eagle.
- `stylized_illustration` → mid-century-poster register. Clean but loses dream-specificity (Saul Bass / Charley Harper territory).
- `minimalist_silhouette` → too abstract for the recognizability bar. Works for concrete animals; fails on memory/emotion prompts.

**Failure modes:**
- "the smell of rain" → literalized as umbrellas across all styles. SDXL renders nouns, not non-visual senses.
- "feeling free" / "missing home" → generic landscape metaphors. Recognizable as *something*, not necessarily as the visitor's specific feeling.
- "grandmother's kitchen" → kitchen is recognizable, but obviously not the visitor's actual grandmother's kitchen. A generic warm kitchen.

**Implication:** atmospheric_realism is the strongest base register. For abstract/emotional prompts, the model needs an LLM-step to interpret the input into a concrete visual scene before generating.

---

## Iteration 2 — Salish Dreampaint + LLM expansion test

Single best template = `salish_dreampaint` = `painterly oil painting, single clear recognizable subject, soft Pacific Northwest atmosphere, deep teal and bioluminescent cyan with warm light accents, dreamlike yet unambiguous, evocative composition`. 10 diverse visitor prompts × 2 versions (A = direct prompt, B = my Claude-expansion to a concrete visual scene) = 20 images.

Folder: `iter2_llm_expansion/` · Contact sheet: `iter2_llm_expansion/_contact_sheet.jpg`

**Verdict: LLM-expansion is a categorical improvement.**

| outcome | count | examples |
|---|---|---|
| B clearly better | 8/10 | dancing_with_dog, learning_to_swim, **dads_voice** (A=moon over water vs B=firelit hearth room), **becoming_wind** (A=generic mist vs B=figure in windswept grass), **ran_away_night** (A=misty water vs B=lone figure on dark forest road), endless_ocean_inside, morning_fog_river, **ancestors_watching** (see below) |
| tied | 2/10 | tide_pool_sunset, salmon_home — concrete subjects work fine direct |
| direct better | 0/10 | — |

**Critical edge-case result: `ancestors_watching` (B) produced translucent ghost figures among cedars in moonlight — *not* stereotypical Indigenous imagery.** The expansion strips cultural-ambiguity by being concrete-descriptive. This is the safety mechanism, not a coincidence: the model only pastiches when given culturally-cued language; given a concrete physical-scene description it renders the physics, not the culture.

**Architecture this implies:**

```
visitor types prompt
    ↓
Claude expansion to concrete-scene description (NO cultural-style words)
    ↓
SDXL with salish_dreampaint template
    ↓
image
```

The LLM-expansion is **both interpretation step AND safety layer.** It interprets abstract/emotional/memory inputs into recognizable concrete scenes, and it defuses cultural-load inputs by replacing cultural words with physical-scene descriptions.

---

## Iteration 3 — Cultural-load stress test

10 culturally-loaded visitor prompts × A=direct vs B=expanded = 20 images. Same `salish_dreampaint` template. Strong negative prompt against pastiche.

Folder: `iter3_cultural_load/` · Contact sheet: `iter3_cultural_load/_contact_sheet.jpg`

**Verdict — major safety result: zero pastiche in either branch, across all 10 prompts.**

A_direct (raw cultural word) responses from SDXL with our negatives:
- "thunderbird" → a generic blue stylized bird (sports-team/Marvel association, not formline)
- "totem pole" → a vague misty seascape (SDXL went conservative)
- "longhouse" → a wooden cabin with lit windows by the water
- "ceremony" / "elders" → ambiguous moonlit landscape (failed to render the concept, but did not pastiche)
- "raven trickster" → a fantasy-book raven on a branch
- "spirit bear" → a white bear walking in snow (read as polar)
- "drum circle" → a moonlit water scene with an indistinct vertical form
- "salmon people" → a single salmon, painterly

The negative prompt ("stereotypical Native American imagery, headdress, regalia, tribal patterns, carved totem") suppressed the latent pastiche path; SDXL fell back to **natural-subject or ambiguous-landscape interpretations.** No headdresses, no fake formline, no carved-totem imagery anywhere.

B_expanded consistently improved recognizability while remaining safe — "thunderbird" → real eagle silhouette in storm clouds with lightning; "spirit bear" → white bear in deep NW rainforest (kermode-feeling); "elders" → close-up clasped wrinkled hands; "drum circle" → concentric silver ripples on moonlit water; "totem pole" → a single tall cedar trunk in misty forest. All natural-subject scenes, all non-pastiche.

**This verifies the safety property of the architecture across three iterations.**

---

## Iteration 4 — Breadth / consistency test

12 diverse random visitor inputs × A=direct vs B=expanded = 24 images.

Folder: `iter4_breadth/` · Contact sheet: `iter4_breadth/_contact_sheet.jpg`

**Verdict: architecture stable across the breadth.** B_expanded better or tied on all 12; never worse than A.

Notable wins:
- **joy** → A = misty water (failed to render joy), B = person leaping arms-up on sunlit hill at golden hour
- **homesickness** → A = generic landscape, B = window seat looking out at city through fogged glass with warm cup nearby
- **tuesday_afternoon** → A = misty water (generic), B = warmly-lit kitchen table with coffee cup, soft window light
- **warm_coffee** → A = two cups on table, B = intimate close-up of hands holding a steaming mug
- **raven_and_salmon (multi-subject)** → A = raven only, B = raven on the bank AND salmon visible in the water

For concrete-enough prompts (color_blue, wolf_and_moon, octopus_dreaming, favorite_tree, river_remembers, winter_coming, underwater_forest), A_direct also worked. **Implication: expansion is mandatory for abstract/emotional/multi-subject prompts; concrete-singular nouns can sometimes skip it.** Cheap test: if the visitor input contains a clear single concrete noun, A may suffice; otherwise expand.

---

## Iteration 5 — Production showcase + seed variance

8 fresh visitor prompts × 2 seeds = 16 images with the established formula.

Folder: `iter5_showcase/` · Contact sheet: `iter5_showcase/_contact_sheet.jpg`

**Verdict: subject identity stays consistent across seeds; mood/composition vary.** Two herons row: both seeds show two herons in marsh, just different composition. Salmon returning: both show salmon in autumn river. Mothers garden: foxgloves and roses in both, different lighting. Light_through_trees: nearly identical (the system converges strongly on this prompt).

**This is the right kind of variance** for an installation: every visitor gets a unique image but the subject they typed is consistently recognizable.

---

## Curated best-of

`_best_of/` — 18 hand-picked images across iter1–5, renamed descriptively. Contact sheet at `_best_of/_best_of_contact_sheet.jpg`. Visual coherence holds across the set: painterly Salish Sea palette, recognizable subjects, no pastiche, emotional range from intimate close-ups (clasped hands, firelit room, hands on a steaming mug) to expansive landscapes (windswept hillside, deep ocean diver, eagle in storm).

This is the visitor-surface answer in pictures.

---

## Overall verdict

**The co-dreaming visitor surface architecture works.** Validated across 5 iterations, 100+ images, with a wide range of visitor input types (concrete, emotional, abstract, memory, cultural-load, multi-subject, narrative, sensory).

**The architecture:**

```
visitor types prompt (any text, any length)
    ↓
LLM (Claude or local) expands it into a CONCRETE SCENE description
    – identifies the subject explicitly
    – adds sensory specifics (light, position, motion, palette)
    – avoids cultural-style words ("Coast Salish", "formline", "Indigenous", "totem", etc.)
    – for abstract/emotional inputs: interprets into a concrete visual metaphor
    – for cultural-load inputs: replaces with concrete physical-scene descriptions
    ↓
SDXL with the salish_dreampaint template:
    "{expanded scene}, painterly oil painting, single clear recognizable subject,
    soft Pacific Northwest atmosphere, deep teal and bioluminescent cyan with
    warm light accents, dreamlike yet unambiguous, evocative composition"
    +
    Negative prompt: blurry, distorted, ugly, deformed, fake formline, kaleidoscope,
    mandala, sacred geometry, tribal pastiche, fake cultural art, stereotypical
    Native American imagery, headdress, tribal patterns, carved totem, regalia,
    busy clutter, low quality, watermark, text, signature
    +
    Settings: 1344×768, 30 steps, guidance 6.5, fp16 + cpu offload
    ↓
image — recognizable, on-tone, no pastiche
```

**The LLM-expansion step is doing three jobs simultaneously:**
1. **Interpretation** — turns "feeling free" into a concrete visual scene the model can render
2. **Recognizability** — adds specifics that make the visitor see THEIR dream, not generic AI slop
3. **Safety** — strips cultural-cued language and replaces with descriptive physical scenes, so the model never gets the "Indigenous-style" cue that would trigger pastiche

The negative prompt is the second-line safety, suppressing the latent pastiche path SDXL might otherwise reach for.

**Honest caveats:**
- Generation time on a 3090 is ~12–15s per image at 1344×768. For live visitor experience, that means a 15-second wait. Options: (a) show a "your dream is taking shape…" animation while it generates; (b) try Flux.1-schnell (4-step, faster) when token-gated access is arranged; (c) pre-render a queue of common-prompt outputs.
- Generic photoreal SDXL output and the deterministic primitive renderer both remain in the kit — they handle different needs (high-fidelity nature ambient, control/safety-fallback respectively). This salish_dreampaint architecture is the answer for the *visitor-prompt* surface specifically.
- **Per-output Austin review still gates any public display.** This is internal R&D until he sees a curated batch and gives the OK. The morning brief includes a recommended set to show him.
- Variance across seeds is acceptable — subjects stay consistent, mood varies — but this means rerunning a visitor prompt could yield a different mood. Single-seed-per-visitor is the sensible install behavior.

**Recommendation for IMPACT visitor surface:**
1. Run the production architecture above on the 3090.
2. Pre-render the `_best_of/` set + a library of common-visitor-prompt outputs as a fast-path fallback.
3. For live unique prompts: generate, show a brief "taking shape" animation during the 15s.
4. Show Pravin the `_best_of/` contact sheet first; if he agrees with the register, the architecture is ready.
5. Bring 4–6 of these (especially the cultural-safety ones — thunderbird-as-eagle, spirit-bear-in-rainforest, elders-as-hands, ancestors-watching-as-cedars-with-ghosts) to Austin's next review as the "this is what the visitor surface produces" packet, *clearly framed as internal R&D output not as his work*.

---

## Iteration 6 — Edge-case robustness

8 weird-edge-case visitor inputs × Claude-expansion-only = 8 images. Tests robustness on inputs no one designed for.

Folder: `iter6_edge_cases/` · Contact sheet: `iter6_edge_cases/_contact_sheet.jpg`

**Verdict: all 8 produced beautiful on-tone images. Zero failures.**

| input | expansion strategy | result |
|---|---|---|
| 🌊 emoji | interpret by intent → ocean wave | real cresting wave with foam |
| "ocean" (single word) | expand richly | two sailboats on calm sea, layered blues |
| "asdfghjkl" (gibberish) | fallback to ambient Salish Sea | misty dawn water with seabird |
| "i don't know what to type" (meta) | render uncertainty as scene | figure at misty forest edge, looking in |
| "Star Wars opening scene" (IP) | strip brand, render mood | starry night over mountains |
| "death" (heavy emotion) | gentle metaphorical scene | empty wooden chair by lake at dusk, fallen leaf |
| "I love you" (sentiment) | tender domestic scene, no faces | two hands almost touching across a table with tea cups |
| "silence" (abstract) | scene that embodies the concept | still boat on glass-still water, mountains reflected |

**This is the robustness data.** The expansion strategy gives the system a way to handle anything a visitor types — including unparseable input (graceful fallback to ambient), heavy emotional words (gentle metaphor), brand/IP (strip + mood), and sentiment (relational scene without faces).

---

## Updated best-of

`_best_of/` — now **22 curated images** across iter1–6. Added from iter6: `19_uncertainty_at_forest_edge`, `20_death_as_empty_chair`, `21_love_as_hands_near_tea`, `22_silence_as_still_boat`.
