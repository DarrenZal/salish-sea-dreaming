# 4pm Pravin Call Brief — 2026-05-17

`[INTERNAL — DARREN'S PREP NOTES]`

> Scrollable cheat-sheet for the 4pm Sunday Pravin call. Lead with the strongest single artifact (pearl-bead concept), narrow the ask, hold the rest. Per peer-agent strip-down: one decision ask only; everything else is backup if he engages.

---

## Lead with this one thing

> "Darren had a visual mechanic worth testing: **one pearl travels along one graph edge, and the morph plays on the pearl as it moves**. We built a prototype — want me to show it?"

If he says yes → play `04_pearl_bead_traversal.mp4` first. ~4 sec. Let it loop.

Then ONE ask: **"Is this worth a one-edge TouchDesigner prototype before Tuesday?"**

Hold everything else unless he asks for more.

---

## Curated review packet (peer-assembled 2026-05-17 PM)

**Single entry point** for Austin/team review (and the 4pm Pravin call): `track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/`. README inside has show-order + framing.

Structure:
- `01_lead_with/` — the 5 strong/shareable artifacts in order: pearl-bead traversal → three-stage logic → primitive cycle → **primitive field v001 (NEW)** → raven_sun↔cosmic_sun clean same-viewBox morph
- `02_promising_rough_ask_first/` — multi-pearl + cross-piece raw morphs; show only if conversation has room for rough experiments
- `03_catalogs/` — primitives_catalog.html + atom_catalog.html

**Wording correction (peer 2026-05-17 ~2 PM):** never call the work "culturally honest" — that's Austin's call. Use "structurally closer to the primitive grammar we can observe in the pieces" when describing what atom-level approaches do.

**Lane 2E verbal bridge (use primitive_field_v001 to introduce):** "These primitive transitions — circle, crescent, trigon — can become the *grammar* for atom-level morphs between Austin's actual pieces. When a circle in one piece needs to become a crescent in another, this is the vocabulary that bridges them. We're not yet showing that in motion; the next experiment lane is building it." That's the right framing — concept introduced verbally; per-atom-bridge implementation queued as Lane 2E post-call.

## Files staged for the call

All on disk, ready to AirDrop / share-screen as needed:

### Primary deliverable (lead with this)
- `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4` — single-pearl traversal animation (4 sec @ 24fps)
- `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/02_single_scene_t05.png` — hero still (1920×1080)
- `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/01_progression_3stage.png` — "how it works" diagram

### Secondary (if he wants to see more)
- `track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4` — 3-node 2-pearl simultaneous (polyphonic graph alive)
- `track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/02_multi_pearl_hero_t045.png` — hero still

### Three-fundamental-shapes story
- `track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4` — **18-sec continuous Circle → Crescent → Trigon → Circle morph cycle**
- `austin-v2-ingest/decomposed/primitives_catalog.html` — open in browser; shows all Circle/Crescent/Trigon atoms across Austin's pieces

### Decomposition + AI classification artifacts
- `austin-v2-ingest/decomposed/atom_catalog.html` — full grid, 504 atoms across 5 pieces, AI-classified
- 5 pieces decomposed: Cosmic_Sun (39), Raven_Sun (29), Wolf_Spindle_Whorl (63), Salmon_Spawn_Eggs (242), TheCreator (139)
- 184 Salmon roe pre-labeled by heuristic; the rest AI-classified into 15-class Coast Salish formline taxonomy

### More morph experiments rendered today — frame HONESTLY as "promising but broken"
- `track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn.mp4` — Nature ↔ Animal trophic edge (5 sec)
- `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_salmon_spawn.mp4` — origin-light to return/spawning (5 sec)

**Operator + peer review (1:30 PM):** primitive-motion middle is the interesting part; endpoints have three known issues — (1) start-frame z-order wrong (sun on top of raven; Austin's source has raven on top), (2) destination eye/pivot color reads slightly off, (3) straight diagonal seams from background-field polygons being morphed. Today's `endpoint_emerge_v001` attempt at image-level fix did not resolve these — they're atom-level problems, not endpoint-timing. Spec for proper v002 fix at `docs/space-center/morph-lane-1-v002-atom-level-spec-2026-05-17.md` (bg-atom exclusion + direct-render endpoints; 4-6 hrs).

**Show ONLY if Pravin specifically asks** for cross-creature morph examples; otherwise hold these — they're not yet exhibition-ready.

**Sunday afternoon iteration history (DO NOT show unless asked — all preserved as labeled variants):**
- `*_endpoint_emerge_v001.mp4` — image-level luma-mask fix; peer reviewed → does not solve atom-level problems (z-order, bg seams, palette). NOT promoted. Spec for proper v002 atom-level fix: `docs/space-center/morph-lane-1-v002-atom-level-spec-2026-05-17.md`.
- `cosmic_sun_to_salmon_spawn_roe_particle_field_v001.mp4` — Lane 2A first attempt, timing bug (blank middle). Variant control.
- `cosmic_sun_to_salmon_spawn_roe_particle_field_v002.mp4` — Lane 2A timing fix, but architecture still wrong (whole-piece crossfades, particles don't build dest, generic black dots not Austin's roe). FAILED DIRECTION. Codex worker now owns v003 per spec at `docs/space-center/morph-lane-2a-v003-spec-2026-05-17.md`.

**Honest framing if Pravin sees the iteration log:** "we're running parallel experiment lanes with strict no-overwrite versioning; the failed attempts stay labeled as control so we can compare. The right direction for the cross-creature morphs needs atom-level not image-level work — building that this week."

### Architectural docs (only if he asks)
- `docs/space-center/austin-graph-show-architecture-2026-05-17.md` — graph-as-show-backbone, pearl-beads, place-anchored substrate option
- `docs/space-center/pearl-interior-experiment-spec-2026-05-17.md` — 62 ranked pearl-interior ideas
- `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md` — cross-creature morph policy
- **`docs/space-center/morph-experiment-lanes-2026-05-17.md`** — 5 parallel experiment lanes, variant-naming discipline, multi-pearl as composite. Shows we have an architecture for parallel exploration, not a flailing iteration log.
- **`track2-deterministic/morph_outputs_INTERNAL/VERSIONING_DISCIPLINE.md`** — no-overwrite rule + variant naming grammar after today's regression (cross-dissolve clobbered a version operator liked; peer recovered originals from surviving frame dirs; canonical names now alias raw morphs; cross-dissolves preserved as labeled controls).

---

## If he engages: unpack in this order (only if asked)

1. **Pearl-bead is one mechanic in a larger graph-as-show architecture** — multi-minute traversal of Austin's piece graph; pearl-beads are how it stays visible
2. **Place-anchored Salish Sea substrate option** — peer-surfaced this morning; "There's a larger idea of putting this on a Salish Sea coordinate substrate later, but I don't think we decide that today." ← exact framing per peer
3. **Decomposition + AI classification surfaced real grammar findings** — Wolf is 2-fold mirror not 4-fold; Salmon is two-salmon yin-yang with roe-as-field; Raven_Sun reuses Cosmic_Sun's trigon-spike vocabulary
4. **Three primitives view** — `primitives_catalog.html` shows **179 Circle/Crescent/Trigon atoms** across all 5 pieces (43 circle / 78 crescent / 58 trigon); Austin's primitive library is stable across his work
5. **MAJOR FINDING — TheCreator already contains the pearl framing structurally.** Atom_0114 is a large dark sphere with atom_0117 = a small figure held INSIDE it. That's literally "the being inside the pearl" from `project_austin_pearl_vision.md` — but it's in **Austin's OWN composition**, not our interpretation. Our pearl-interior concept is resonant with structure already present in his highest-cultural-load piece. **DO NOT CLAIM IT** — surface as observation only; agent flagged that any design-grammar use requires Austin's direct consultation. But it's a bridge that strengthens the architectural framing without our overreach.

---

## Honest caveats to volunteer if relevant

- **Pearl rendering is PIL-composite, NOT true 3D UV-mapping.** Production needs TouchDesigner (instance system + Movie File In TOP) or Blender (UV-mapped sphere with animated texture). Operator-side iteration on pearl shading happened this morning — current is brighter texture-dominant version after first attempt was too dark.
- **Legibility risk:** Austin's linework may render as beautiful-but-illegible marble at projection scale. Prototype MUST test at actual projection resolution. Three mitigations ready if it fails (larger pearls, translucent shell, flat-quad crossfade fallback).
- **Docking is designed aesthetic crossfade, NOT literal pixel match.** Video-textured lit sphere ≠ flat node thumbnail unless designed that way.
- **Scope distinction:** pearl-beads collapse CONCEPTUAL scope (graph + morphs + pearl into one logic), but it DOESN'T zero TECHNICAL scope. One pearl on one edge = 1-2 hr TD sketch. Production pearl-graph (multiple beads, scrub, trails, docking, convergence, place paths) = sprint-week work.
- **Cultural language:** "teaching carried between forms" is INTERNAL framing only; use "visual relationship / morph carrier" externally until Austin blesses.

---

## Things explicitly to HOLD (don't bring up unless he asks)

- The 27 atomic decomposition + recombination experiments (mention only that the spec exists as a parking lot)
- The Sunday-internal-experiment-lane cross-creature morph queue
- The 62-item pearl-interior experiment menu
- Detailed place-anchored substrate scope (one-sentence mention max)
- The 5090 procurement details (already decided either way: built today via MemEx Victoria or fallback UNIWAY Aurora)

---

## Procurement update (1-line if he asks)

5090 procurement decision-tree is sorted: at MemEx Victoria today getting a complete build, or UNIWAY Aurora as Best Buy CA fallback ($8,999 + tax, Burnaby 2BD ship). Will report outcome via Signal afterward.

---

## Procedural reminders (proof-before-send per Pravin's standing rule)

- This is a Pravin-facing call → full pacing posture applies
- After the call, any follow-up email/Signal to him goes through proof-before-send via `verify_draft.py` gate
- Cultural floor: any Austin-vocabulary outputs we show Pravin are INTERNAL — for design discussion only; not for Austin-facing or audience surface without his per-output OK

---

## What "good" looks like for this call

✅ Pravin says yes to the one-edge TD prototype before Tuesday
✅ He understands the graph-as-architecture framing without committing to it today
✅ He surfaces concerns we can address Mon morning (legibility? scope? cultural?)
✅ Call wraps in time for his 5pm Briony Penn plant event

⚠️ If he wants to discuss place-substrate or 27-experiment menu → defer to Tue-Fri sprint week
⚠️ If he wants Austin involved before Tue → revise plan; ask for Signal intro

---

## Operator opening line (just in case the start is awkward)

> "Hey. Quick update before your 5pm — three things landed this morning that I think are worth showing you. Cool if I share my screen?"

(One quick thing, not three things. Lead pearl-bead, see if he bites.)
