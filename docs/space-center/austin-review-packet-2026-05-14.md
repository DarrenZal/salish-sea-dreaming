# Austin Review Packet — 2026-05-14

Purpose: give the operator a tight review path when Austin's Drive lands and/or Austin is available for a Signal check-in. This is not a public document.

Primary record: `docs/space-center/austin-consent-map.md`  
Primitive worksheet: `track2-deterministic/austin-screenshare-worksheet-template.md`  
Ingest operator: `scripts/austin_v2_pipeline.py`
Public-language drafts:

- `docs/space-center/drafts/wall-card-pending-austin-review-2026-05-14.md`
- `docs/space-center/drafts/sponsor-impact-program-copy-pending-austin-review-2026-05-14.md`
- `docs/space-center/drafts/internal-team-description-pending-austin-review-2026-05-14.md`

## Before The Call

- [ ] Run `python3 scripts/austin_v2_pipeline.py status`.
- [ ] If Drive files have landed, run `python3 scripts/austin_v2_pipeline.py auto-until-gate` until triage/caption gate.
- [ ] Open `austin-v2-ingest/provenance/manifest.csv`.
- [ ] Open `docs/space-center/austin-consent-map.md`.
- [ ] Open the three public-language drafts if wording review is likely.
- [ ] Open `track2-deterministic/austin-screenshare-worksheet-template.md`.
- [ ] Prepare 3-5 candidate source pieces to discuss, not every file.
- [ ] If recording notes with Otter/voice memo, ask Austin before recording.

## Frame The Conversation

Suggested opener:

> "We're treating your Drive files as source material under the protocols you approved. Nothing goes public or into the projector without your per-output OK. Today I want to confirm what can be used for internal training, what can be decomposed into primitives, what is off-limits, and the wording around the pearl."

Avoid framing this as "approval paperwork." This is co-authorship and cultural direction.

## Decisions To Capture

| Decision | Recommended ask | Record in |
|---|---|---|
| Drive source scope | "Can these files be used for internal v2 LoRA training, deterministic primitive decomposition, or both?" | consent map + manifest `austin_consent` |
| Restricted material | "Any pieces/forms in here that should not be used or should stay locked to their original context?" | consent map restricted table |
| Three pearl shapes | "Are the three shapes Crescent / Trigon / Circle-Oval (Coast Salish primitives), or something else? Your heritage is hybrid — Northern formline terms like ovoid / U-form may also be in play." | consent map + pearl mock spec + memory |
| Thunderbird role | "Is Thunderbird the sole pearl-passer in this version?" | consent map public-language table |
| First-look outputs | "If the v2 LoRA produces internal recipe-proof stills, do you want to see them? How should we label them?" | consent map output queue |
| Public wording | "How should we phrase 'teaching,' 'pearl,' 'Thunderbird passing,' and your attribution line?" | consent map public-language table |
| Review cadence | "Do you want per-output Signal review, batch review, or live screenshare review?" | consent map sign-off log |

## What To Show

Show:

- The Drive files / thumbnails, if available.
- The v2 ingest status table only if useful.
- The consent map sections for source assets, AI workflows, output queue, and public wording.
- The public-language drafts only if Austin has time to review phrasing line-by-line.
- The Track 2 worksheet if Austin wants to discuss primitive decomposition.
- The pearl triptych mock only as a composition reference and explicitly not as artwork.

Do not show by default:

- v1/v1.5 generated outputs.
- Failed AnimateDiff outputs.
- Dry-run placeholder morph videos as "what your work will look like."
- John projector AI stress plates, unless the conversation specifically turns to projector testing.

## First-Look Output Labels

If Austin agrees to review internal generated outputs, label every image/clip with one of:

- `INTERNAL RECIPE PROOF - NOT PUBLIC ARTWORK`
- `CANDIDATE PRIVATE REVIEW - NEEDS AUSTIN OK`
- `APPROVED FOR [specific use] - [date / channel]`

Never label generated output as "Austin artwork" unless Austin specifically directs that wording.

## Update Immediately After

- [ ] Update `docs/space-center/austin-consent-map.md`.
- [ ] Update `austin-v2-ingest/provenance/manifest.csv` statuses if source-file scope was approved.
- [ ] Update `track2-deterministic/primitives.csv` / `morph_pairs.csv` if primitive or morph decisions were made.
- [ ] Update `docs/space-center/pearl-triptych-mock-spec.md` if the three shapes or pearl framing changed.
- [ ] Send Austin/Pravin a short recap with decisions and open questions.

## Open Questions To Carry Forward

- Does Austin want Xwalacktun, James Harry, Squamish Lil'wat Cultural Centre, IM4 Lab, or another advisor involved before public presentation?
- Are there compensation / commercial terms that need separate treatment for MOVE37XR, DEVCON, or Life at Center 2027?
- Does the phrase "AI trained on Austin's work" feel accurate, or should the public wording emphasize "AI-assisted style-transfer experiments under Austin's direction"?

## Framing Questions From Deep Research (2026-05-16)

Three deep-research reports came back on 2026-05-16 (Coast Salish design primitives + symbolism; Thunderbird / pearl / teaching-gesture sources; transformation and morphing as a teaching device). They surfaced three places where our current framing may overreach Austin's vision and the public cultural record. These are **questions for Austin**, not corrections to him — only he can name his own grammar.

1. **Pearl vs spindle whorl as the container.** The "pearl" is not documented as a traditional Coast Salish or Kwakwaka'wakw cosmological object. The closest culturally-grounded analogs are: (a) **spindle whorl** (circular Coast Salish teaching-container — strongest precedent; National Gallery of Canada describes spindle whorls as embodiments of "spirit, culture, and agency"); (b) **mother-of-pearl / abalone** on Kwakwaka'wakw button blankets (*kikugwitsam*, "having mother-of-pearl"); (c) **quartz crystal** in Namxialguyau's forehead (Kevin Cranmer retelling — luminous inner object of transformation); (d) **bentwood treasure boxes**; (e) Tlingit "Box of Daylight" (contained luminosity precedent for immersion). Ask: *"You said 'pearl' — is that the right container, or does 'spindle whorl' or another circular vessel resonate more with what you saw?"*

2. **Three vs four.** The reports found **no public evidence for a triadic cosmology** in Coast Salish discourse. Numerological emphasis falls strongly on **four** — Susan Point explicitly says four has great significance, connecting to four peoples, winds, elements, directions, moons, salmon cycles, seasons; lessLIE frames four in spindle-whorl composition as "wholeness and balance." Crescent and Circle/Oval have rich symbolic readings; **trigon symbolism is much thinner in the public record** (often discussed as a formal generator rather than a standalone symbol). Ask: *"You named three shapes — does four matter more, or does three reflect a teaching you're carrying?"*

3. **One object seen from different angles vs three forms moving inside one space.** This is our interpretation pushing on your verbatim language. Your words were "3 shapes swirling and morphing inside the pearl." We've explored both: (a) a single 3D object whose three orthogonal silhouettes ARE the three primitives (Exp 3 — produced a slab, not pearl-like); (b) three forms arranged on intersecting planes inside a rotating sphere (Exp 4 — passes the legibility test, closer to your literal words). Ask: *"Does the 'one object seen from three angles' interpretation resonate, or do you want to keep it as three forms living/moving inside one space?"*

### Additional protocol notes from the reports

- **"Teaching pose" is not less protocol-sensitive than "power pose."** Once recognizable family imagery enters the work, protocol weight goes up. (Report 12)
- **Primitive morphing** (Crescent ↔ Trigon ↔ Circle) is on solid ground — Susan Point did 70+ spindle-whorl print editions exploring exactly this generative grammar. (Report 13)
- **Creature morphing across separate icons** (e.g., Wolf ↔ Salmon — Exp 2b) needs explicit Austin authority as a new authored relationship, not just per-output approval of a clip. Bracken Hanuse Corlett's *Qvùtix* works because it stays inside a Hanuse family crest; Joe David's Wolf↔Killerwhale series works because it's anchored to a name his family gave him. (Report 13)
- **Strongest precedent for our overall work:** Shawn Hunt's *Transformation Mask* (HoloLens / MR) — explicitly did *not* simulate a specific ceremony; emulated the *experience* of transformation. (Report 13)

Source files: `/Users/darrenzal/Downloads/deep-research-report (12).md`, `(13).md`, `(14).md`. Synthesis logged in session 2026-05-16.
