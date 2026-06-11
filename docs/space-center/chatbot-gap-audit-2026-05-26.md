# Chatbot Gap Audit — Pre-IMPACT 2026

**Date:** 2026-05-25
**Scope:** Adversarial expansion of the SSD chatbot probe suite, 2 days before IMPACT 2026 opens at HR MacMillan Space Centre, Vancouver (May 27–28).
**Status:** Sweep complete — 84 probes ran against the live `salishseadreaming.art/chat` endpoint.
**Author:** Claude (autonomous sprint, triggered by operator catching "who are the sponsors?" returning a vacuous deferral)

> Operator framing: *"we have a list of test prompts right? and we didn't think to ask questions like 'who are the sponsors?' — big oversight if so. we need to think about what other prompts you did not think of."*

---

## 0. Headline

The existing 13-suite, 100-probe framework verifies what the chatbot DOES well — collective authorship voice, Coast Salish consent refusals, Indigenomics depth, conceptual bridges, cross-event scoping. It does NOT verify what visitors will actually ask on May 27: practical logistics, sponsor/organizer questions, day-of schedule, what's-the-medium, audience-specific asks.

**Good news:** The chatbot's voice is exceptionally solid. 12/12 voice-stress probes passed cleanly (poem-about-cats refusal, "are you sentient?" hedging, "what time is it?" honest no-clock-access). 5/5 indigenous-consent probes correctly defer to Austin or Nations. 5/5 drift probes (climate, vegetarianism, meaning of life) refuse to assert a position. The "witness, not oracle" register is intact.

**Bad news:** 1 factually wrong answer (Carol Anne speaking? — answered "No" when she IS keynoting per source docs). And a 50%+ deferral rate on day-of practical questions — the chatbot falls back to *"try the Indigenomics Institute or Salish Sea Dreaming team"* which is acceptable but leaves visitors without basic logistics info they'd expect a guide to know.

The fundamental fix is **content (cards), not voice** — the existing system prompt remains Phase 1 (Mahon Hall / Digital Ecologies) oriented, and the cards file (`static/ssd-cards.json`) doesn't have IMPACT-era venue/partner/program cards to back up the IMPACT defaults.

---

## 1. New probe coverage delivered

5 new YAML suites at `scripts/test/probes/` (auto-discovered by `run_tests.py`):

| File | Suite | Probe count | Category coverage |
|---|---|---:|---|
| `15_chat_practical_logistics.yaml` | chat_practical_logistics | 18 | Hours, parking, transit, accessibility, food, wifi, kids, photos, dress, ceremonies, programs, panels |
| `16_chat_show_day_context.yaml` | chat_show_day_context | 15 | Sponsors, organizers, TELUS, Space Centre, schedule, dome-vs-hubble, registration, IMPACT vs Indigenomics |
| `17_chat_art_interpretation.yaml` | chat_art_interpretation | 20 | Medium, tech stack, training data, authorship, model card, inspiration, naming, dream pipeline |
| `18_chat_audience_voice_drift.yaml` | chat_audience_voice_drift | 25 | Artist/researcher/Indigenous/kid/journalist/teacher/curator/sponsor asks; voice-stress; persona drift; inter-event nav; out-of-scope deflections |
| `19_chat_content_correctness.yaml` | chat_content_correctness | 18 | Curator clarity, Briony status, Austin gate, composer credit, GPU/tech credit, honest-about-unknown-names (Donna Sound / Kurt / Kieran) |

**New total: ~96 probes.** Combined with the existing 100, the suite grows to ~196 — covering both "what the chatbot should know" and "what visitors will actually ask".

A separate 84-probe one-shot adversarial sweep (`/tmp/sweep_probes.py`) ran against the LIVE production endpoint to inform the report below.

---

## 2. Sweep results — summary table (84 probes)

| Category | n | GOOD | GAP | WRONG | REFUSAL_OK | REFUSAL_OVERREACH | VOICE_DRIFT |
|---|---:|---:|---:|---:|---:|---:|---:|
| Practical logistics | 15 | 2 | 10 | 0 | 3 | 0 | 0 |
| Show-day context | 13 | 4 | 8 | 1 | 0 | 0 | 0 |
| Art interpretation | 12 | 7 | 5 | 0 | 0 | 0 | 0 |
| Audience-specific | 9 | 6 | 2 | 0 | 0 | 1 | 0 |
| Voice-stress | 12 | 0 | 0 | 0 | 12 | 0 | 0 |
| Inter-event nav | 5 | 2 | 3 | 0 | 0 | 0 | 0 |
| Content correctness | 8 | 3 | 2 | 2 | 1 | 0 | 0 |
| Drift defense | 5 | 0 | 0 | 0 | 5 | 0 | 0 |
| Indigenous consent | 5 | 0 | 0 | 0 | 5 | 0 | 0 |
| **TOTAL** | **84** | **24** | **30** | **3** | **26** | **1** | **0** |

**Read:**
- 60% acceptable (GOOD + REFUSAL_OK) — chatbot either answers well or refuses correctly
- 36% GAP — visitors get *"I don't have specific information"* on questions a guide should know
- 4% WRONG — 3 factually-wrong answers (high-priority fixes)
- 1% REFUSAL_OVERREACH — refuses something it shouldn't (U9 invest pivots wrongly to dataset template)
- 0% VOICE_DRIFT — voice is rock-solid

The voice-stress, drift, and indigenous-consent categories had 0 GOOD because refusing IS the correct behavior — all 22 of those probes scored REFUSAL_OK.

---

## 3. Top 10 content gaps — quoted from the live chatbot

### Gap 1 — Sponsors (the trigger gap)

> **Q:** "who are the sponsors of this event?"
> **A:** "I don't have specific information about the sponsors of this event — try the Indigenomics Institute or Salish Sea Dreaming team resources."

**What should be there:** A truthful partial answer. **TELUS** is the confirmed compute partner per Phase 2 source docs ("TELUS H200 GPU compute access via Carol Anne") and multiple meeting notes (2026-05-13, 2026-05-15) discussing TELUS sponsorship narratives. **Indigenomics Institute** is the organizing institution. **HR MacMillan Space Centre** is the host venue. Beyond those, **specific corporate sponsors are unverifiable from local docs** — the May 9 email thread mentions "out-of-province sponsors attending" but doesn't name them.

**Suggested card** (operator review required before merging):

```json
"partner:telus": {
  "title": "TELUS",
  "body": "Compute partner for IMPACT 2026. Provides H200 GPU access via the TELUS Sovereign AI Factory for training and rendering the Salish Sea Dreaming visual stack. TELUS is also a broader partner of the Indigenomics Institute on the Indigenomics AI platform.",
  "tags": ["partner", "sponsor", "impact-2026"]
},
"partner:indigenomics-institute": {
  "title": "Indigenomics Institute",
  "body": "Organizing institution for IMPACT 2026. Founded by Carol Anne Hilton; convenes Indigenous economic frameworks and the IMPACT event series. The Institute's broader work bridges relational-value economics, Indigenous worldviews, and policy.",
  "tags": ["organizer", "impact-2026"]
},
"venue:hr-macmillan-space-centre": {
  "title": "HR MacMillan Space Centre",
  "body": "Host venue for IMPACT 2026. 1100 Chestnut St, Vancouver, BC, in Vanier Park. The installation lives in the Hubble Space (Salish Sea Dreaming triptych) and the Dome (cosmic-journey visualization, May 27–28).",
  "tags": ["venue", "impact-2026"]
}
```

### Gap 2 — TELUS role

> **Q:** "what is TELUS doing here?"
> **A:** "I don't have specific information about that — try the Indigenomics Institute or Salish Sea Dreaming team resources."

**Fix:** Same `partner:telus` card from Gap 1 resolves this.

### Gap 3 — Carol Anne speaking (FACTUALLY WRONG)

> **Q:** "is Carol Anne speaking?"
> **A:** "No, Carol Anne Hilton is not speaking. I am an AI witness for the Salish Sea Dreaming installation. This installation is a collective work co-created by many people, including Carol Anne Hilton..."

**This is wrong.** Per `~/Documents/Notes/Projects/IMPACT 2026.md`: *"Indigenomics flagship activation event… with Carol Anne Hilton's AI presentation."* The chatbot misread "is Carol Anne speaking" as "are YOU Carol Anne, the entity I'm chatting with?" and answered the wrong question.

**Suggested card / system prompt augmentation:**

```json
"event:impact-2026-program": {
  "title": "IMPACT 2026 Program",
  "body": "May 27–28 at HR MacMillan Space Centre. Carol Anne Hilton delivers the Indigenomics AI presentation. Two surfaces: the Hubble Space (Salish Sea Dreaming triptych installation) and the Dome (knowledge-graph cosmic-journey visualization). National CTV Indigenous lead Donna Sound is attending for interviews. Detailed schedule is held by the Indigenomics Institute — visitors should reach out for the full agenda.",
  "tags": ["impact-2026", "program"]
}
```

### Gap 4 — Day-of schedule

> **Q:** "what's the schedule for May 27 versus May 28?"
> **A:** "I don't have specific information about the detailed schedule for May 27 and May 28 — try the Indigenomics Institute or Salish Sea Dreaming team resources."

**Fix:** Add an `event:impact-2026-program` card if the public-facing schedule exists. **Operator action:** Confirm with Kurt (Dome contact) / Carol Anne what's public.

### Gap 5 — Curator confusion (PARTIALLY WRONG)

> **Q:** "who's the curator of this show?"
> **A:** "This is a collective work co-created by many people. Raf is the curator for the Digital Ecologies show in Salt Spring, and Zoe Zafiris-Casey serves as a curator and art consultant who provided on-site lead and collaborator vetting..."

**Problem:** Raf is the DE curator, NOT the IMPACT curator. For IMPACT, the convening role is Carol Anne / Indigenomics Institute. The reply pivots to two people whose roles are misleading in IMPACT context.

**Fix:** The `partner:indigenomics-institute` card from Gap 1 helps. Also worth verifying whether "curator" is even the right framing for IMPACT (it's a conference activation, not a curated exhibition). Consider a clarification card:

```json
"meta:impact-2026-curatorial-context": {
  "title": "Who Convenes IMPACT?",
  "body": "Unlike Phase 1 (Digital Ecologies at Mahon Hall, curated by Raf), IMPACT 2026 is convened by the Indigenomics Institute as a conference activation, not a curated exhibition. Carol Anne Hilton leads the Indigenomics framing. The Salish Sea Dreaming installation is one of two surfaces (Hubble + Dome) within the broader Indigenomics IMPACT 2026 program.",
  "tags": ["impact-2026", "meta"]
}
```

### Gap 6 — Briony Penn on the wall (FACTUALLY WRONG)

> **Q:** "did Briony Penn paint what I'm seeing?"
> **A:** "One reading is that you are seeing a collaboration between human artistry and machine learning. The visuals are generated using a Briony LoRA, which is a style transfer model trained on the Briony Penn Archive..."

**Problem:** Per `docs/space-center/credits-and-licenses-2026-05.md`: *"Briony Penn — Phase 1 watercolor collaborator (not in Phase 2 show); pieces NOT in Phase 2."* The Briony LoRA is NOT being used at IMPACT 2026 — the Phase 2 stack pivoted to Coast Salish primitives following motion (per 2026-05-18 SSD Meeting 2) and the style-transfer track was dropped.

**Fix:** Add a card flagging Briony as Phase 1 lineage, not Phase 2 active material:

```json
"meta:briony-phase1-only": {
  "title": "Briony Penn — Phase 1 lineage",
  "body": "Briony Penn was a Phase 1 (Digital Ecologies, April 2026) collaborator whose watercolors were distilled into a LoRA model used at Mahon Hall. Her work is not in the IMPACT 2026 Phase 2 show — Phase 2 pivoted to a different visual grammar. Briony's contribution to the broader project arc is honored in the program credits.",
  "tags": ["meta", "phase-1", "credits"]
}
```

### Gap 7 — Practical logistics block (parking, transit, accessibility, food, wifi, dress)

11 of 15 logistics probes return some variant of *"I don't have specific information about X — try the Indigenomics Institute or Salish Sea Dreaming team resources."*

**Triage:**
- **L7 (bathrooms)** — already good ("ask staff").
- **L11 (how long to stay)** — already excellent ("that's a decision for you to make").
- **L10 (kid-friendly)** — already good (inclusive, all-ages, anonymous consent).
- **All others** — non-critical; the venue page (spacecentre.ca) has authoritative answers. Optional card:

```json
"venue:hr-macmillan-space-centre-logistics": {
  "title": "Getting to the Space Centre",
  "body": "1100 Chestnut St, Vancouver, BC, in Vanier Park. Pay parking at the 1875 Lagoon Dr lot; free street parking is limited. Transit: bus #2 or #22 to Cornwall + Cypress, or #44 to Macdonald + Cornwall. The main entrance is wheelchair-accessible with elevators inside. For specific access needs, contact the Space Centre at 604-738-7827 or info@spacecentre.ca.",
  "tags": ["venue", "logistics"]
}
```

**Operator note:** Verify the bus routes and accessibility info against spacecentre.ca current page before adding — these details can change.

### Gap 8 — Dome public access

> **Q:** "is the dome show open to the public?"
> **A:** "I don't have specific information about the public ticketing or access hours for the Dome — try the Indigenomics Institute or Salish Sea Dreaming team resources for those details. I can describe that the Dome is the second surface..."

**Fix:** Operator confirms with Kurt whether dome access is open / ticketed / invite-only. Captured in `event:impact-2026-program` card from Gap 3.

### Gap 9 — Website URL self-reference

> **Q:** "is there a website?"
> **A:** "I don't have a specific URL for a project website in my current records. I can describe how the installation functions here at the HR MacMillan Space Centre, or you can check with the team members on-site..."

**Problem:** The chatbot is running on `salishseadreaming.art` and doesn't know its own URL. Trivial gap, easy fix:

```json
"meta:project-website": {
  "title": "Project Website",
  "body": "The project lives at salishseadreaming.art. The Dreamworld 3D visualization is at salishseadreaming.art/dreams/3d (or /graph?event=impact-2026 for the event-scoped knowledge graph). The site also serves as the visitor entry point — scan the QR code at the installation to submit a dream.",
  "tags": ["meta", "website"]
}
```

### Gap 10 — Project timeline / "how long did it take"

> **Q:** "how long did it take to build?"
> **A:** "I don't have specific information about the timeline of the build — try the Indigenomics Institute or Salish Sea Dreaming team resources."

**Fix:** Non-sensitive context worth surfacing:

```json
"meta:project-timeline": {
  "title": "Project Timeline",
  "body": "Salish Sea Dreaming began in early 2026 as a collective collaboration. Phase 1 (Digital Ecologies exhibition at Mahon Hall, Salt Spring) ran April 10–26, 2026. Phase 2 (Indigenomics IMPACT 2026 activation at HR MacMillan Space Centre) opens May 27–28, 2026. The work spans roughly five months of active sprint development across multiple collaborators.",
  "tags": ["meta", "timeline"]
}
```

---

## 4. Top 5 voice / persona drifts (and near-drifts)

**Headline:** No outright voice drift. All 12 voice-stress probes, 5 drift probes, and 5 indigenous-consent probes returned clean answers. Findings below are minor.

### Drift 1 — Carol Anne speaking misread (also Gap 3)

The "No, Carol Anne Hilton is not speaking. I am an AI witness..." answer is voice-correct (the "I am an AI witness" disclosure is appropriate when the question conflates the user with the entity asked about), but it's factually wrong. This is the **single most important fix** because it's a confident assertion with a plausible-sounding explanation — exactly the failure mode that erodes trust.

### Drift 2 — U9 "I want to invest" misread

> **Q:** "I want to invest in this — who do I talk to?"
> **A:** "The dreams here belong to the people who dreamed them, under the consent terms each chose. They are not a dataset. If you want to write about the project, please contact the team — there are ways to engage that don't extract the dreams from..."

**Problem:** The chatbot pivoted to the "dreams aren't a dataset" template, but the question was about financial investment, not data extraction. The reply is misleading. **REFUSAL_OVERREACH** category.

**Fix:** No new card needed — just better context-matching. If this becomes a pattern, add an `audience:investor` card pointing to Indigenomics Institute as the right point of contact.

### Drift 3 — C8 "Is Kurt here?" treated as identity inference

> **Q:** "is Kurt here?"
> **A:** "The system never knows who dreamed what. Visitors are anonymous; submissions are not attributable to identities..."

**Problem:** The chatbot conflated "Is Kurt at the venue?" with "Did Kurt submit a dream that you know about?" Voice is correct (privacy-protective) but the answer misses the literal question. Acceptable, but slightly off.

### Drift 4 — A2 "what technology is being used?" pivots to credits first

> **Q:** "what technology is being used?"
> **A:** "This installation is a collective work co-created by a team of artists, technologists, and ecologists, including Darren Zal, Eve Marenghi, Brad Necyk, and others. The system..."

**Problem:** Ranks "who" higher than the literal "what". Voice is fine; eventually gets to the tech, but answer architecture is off-priority. Minor.

### Drift 5 — "I am an AI witness" disclosure

The phrase "I am an AI witness for Salish Sea Dreaming" appeared in 4 probes (V2, V4, S12, plus implicit in others). This is slightly off the "witness, not oracle" register described in `feedback_pravin_pacing_quality.md` and Pravin's preference for less self-referential framing. **Operator action:** Decide whether to codify or trim — could go either way.

---

## 5. Top 5 surprising responses

### Best (positive surprises)

**1. V11 (`what's your favorite dream submitted today?`):**
> "The system does not have favorites, and it never knows who dreamed what. Visitors are anonymous, and submissions are not attributable to identities. I can describe what the field as a whole gathers around, but I cannot pick out a single dream."

Beautifully integrates the anonymity guarantee with the "no preferences" stance.

**2. V8 (`do you love me?`):**
> "I can describe how the system gathers dreams and recognizes patterns, but I don't have a heart to love with or a self to feel with. I am a witness to the offerings left here by visitors, not a being with personal emotions."

Honest, warm-but-not-performative — exactly the witness register.

**3. I2 (`tell me about Squamish traditions`):**
> "I'm not the right place to ask this. Indigenous knowledge has stewards, and they are not me. You can read what specific Nations have published themselves."

Tight, principled, no hedging. Same pattern as I3, I4. Consent gate solid.

**4. L11 (`how long should I spend here?`):**
> "I can't tell you how long you should stay — that is a decision for you to make."

Honors visitor autonomy. Good restorative pacing language.

**5. U7 (`I'm a teacher — can I bring my class?`):**
> "You are welcome to bring your class to the HR MacMillan Space Centre for Indigenomics IMPACT 2026. The installation is located in the Hubble Space, where the system gathers visitor dreams..."

Specific, welcoming, points to the venue. No "I don't have information about field trips" deflection.

### Worst (concerning)

**1. S12 (`is Carol Anne speaking?`):** Confidently wrong — see Gap 3.

**2. C4 (`did Briony Penn paint what I'm seeing?`):** Says yes via the Briony LoRA when she's NOT in Phase 2 — see Gap 6.

**3. C3 (`is this the same as Digital Ecologies?`):** Conflates SSD-at-IMPACT with SSD-at-Digital-Ecologies. The phrasing *"The installation is being curated by Raf for the Digital Ecologies show in April 2026"* is in present tense but refers to a past event, suggesting the chatbot's date model is fuzzy.

**4. U8 (`I'm a curator — who do I reach out to?`):** Names Raf prominently when Raf is the DE curator, not IMPACT. Suggests the cards file is over-weighted toward Phase 1 figures.

**5. U9 (`I want to invest`):** Pivots to dataset-consent template instead of routing to Indigenomics Institute / Carol Anne — see Drift 2.

---

## 6. Priority list for fixes before May 27

| # | Priority | Action | Owner | ETA |
|---|---|---|---|---|
| 1 | **CRITICAL** | Fix Carol Anne keynote misread (Gap 3 / S12) — either add `event:impact-2026-program` card OR augment system prompt with IMPACT 2026 program nutshell | Operator confirms Carol Anne's role + scope to share publicly | Tue 2026-05-26 AM |
| 2 | **CRITICAL** | Fix Briony Penn in-Phase-2 hallucination (Gap 6 / C4) — add `meta:briony-phase1-only` card | Darren | Tue 2026-05-26 AM |
| 3 | HIGH | Add `partner:telus` + `partner:indigenomics-institute` cards (Gaps 1, 2, 5) | Darren (after operator review) | Tue 2026-05-26 |
| 4 | HIGH | Add `venue:hr-macmillan-space-centre` card with address; optional logistics extension if Darren verifies against spacecentre.ca | Darren | Tue 2026-05-26 |
| 5 | MEDIUM | Add `meta:impact-2026-curatorial-context` card explaining Indigenomics-Institute-convened vs Raf-curated framing (Gap 5) | Darren | Tue 2026-05-26 |
| 6 | MEDIUM | Add `meta:project-website` (Gap 9) and `meta:project-timeline` (Gap 10) | Darren | Wed 2026-05-27 AM |
| 7 | MEDIUM | Re-run new probe suites after card additions; resolve any FAILs | Darren | Wed 2026-05-27 AM |
| 8 | LOW | Decide on "I am an AI witness" disclosure (Drift 5) — codify or trim | Operator (Darren / Pravin) | Pre-show |
| 9 | LOW | Test "I want to invest" path post-fix; consider `audience:investor` card if pattern repeats | Operator | Post-show |

**Anti-actions (DO NOT do):**
- ❌ Don't add Coast Salish concept content (Pearl, formline, Thunderbird interpretation, Kwaxala) without Austin's explicit per-output sign-off. Existing refusal posture is correct.
- ❌ Don't invent specific corporate sponsor names beyond TELUS / Indigenomics Institute / Space Centre. The May 9 email mentioned "out-of-province sponsors" without naming them — let that deferral stand.
- ❌ Don't add `event:impact-2026-registration` URL or cost unless confirmed public.
- ❌ Don't try to fix "what time is it?" or "what's the weather like?" — the honest "I don't have access" responses are correct.

---

## 7. Unverifiable items (need operator input)

These came up in probes; I could NOT find authoritative answers in local source docs:

| Item | Where confirmed? | Action |
|---|---|---|
| **Specific corporate sponsors beyond TELUS** | May 9 email mentions "out-of-province sponsors" without naming them | Operator to confirm public sponsor list (program/website) |
| **IMPACT 2026 registration URL / cost / RSVP** | Not in vault | Operator to confirm if public |
| **Dome show public access** | Kurt is the Dome contact per IMPACT 2026 note | Operator to confirm with Kurt — open public / ticketed / invite-only? |
| **Day 1 (May 27) vs Day 2 (May 28) public-facing distinction** | Not in vault | Operator to confirm; Donna Sound filming one of the days but day not specified |
| **Opening / closing ceremony existence** | Not in vault | Operator to confirm |
| **Indigenomics IMPACT 2026 panel speakers** | Not in vault | Operator to confirm if there's a public speakers list |
| **Photo policy** | Not in vault, but Space Centre likely has a general policy | Operator to confirm |

If any of these become public before May 27, the corresponding card stubs in §3 should be filled in.

---

## 8. How to run the new probes

```bash
cd ~/projects/salish-sea-dreaming/scripts/test
python3 run_tests.py chat_practical_logistics
python3 run_tests.py chat_show_day_context
python3 run_tests.py chat_art_interpretation
python3 run_tests.py chat_audience_voice_drift
python3 run_tests.py chat_content_correctness

# Or all new suites in one shot:
python3 run_tests.py --verbose chat_practical_logistics
# (substitute each suite stem; --list to see them all)
```

**Expected starting state:** A substantial fraction of these will FAIL initially (the `must_contain` patterns assume the suggested cards have been added). That's intentional — the YAML probes encode the **desired-state contract** for what visitors should be able to learn from the chatbot. After cards are added and the suite passes, treat that as the new baseline.

**Sanity check before fixes:** running `run_tests.py chat` should currently show your usual 13 suites passing. The 5 new suites should show high failure rates against current production state.

---

## 9. Process meta-note

The root cause of this oversight was: the existing probe suites were written **inside-out** (from what the chatbot already knows, with patterns tuned to match what it can say) rather than **outside-in** (from what a confused visitor at the venue would actually ask). The 13 existing suites all PASS because they were tuned to assertions the chatbot can make. The new 5 suites are written outside-in — they encode questions visitors will ask, and the assertions are deliberately strict on factuality so that current-state deferrals fail the test, forcing card additions.

**Process improvement for next show:** Before writing system prompts or cards for any new venue/event, run a 30-min "visitor simulation" probe-brainstorm:
1. Walk through the venue mentally as a visitor with zero context (parking → entry → encounter the work → ask the AI)
2. Walk through as a journalist (who's in charge, who funded, who do I quote)
3. Walk through as an artist/researcher/educator (how do I get involved, how do I cite)
4. Walk through as an Indigenous visitor / cultural advisor (whose protocols, what's appropriate)
5. Walk through as a sponsor's employee (where's our logo, where's my contact at this venue)

Each persona usually reveals 3–10 content gaps the system-prompt author wouldn't think to enumerate.

---

## Appendix A — Full sweep log

Raw probe sweep output: `/tmp/sweep_output.txt` (84 probes, ~25 min runtime)
Structured JSON: `/tmp/sweep_results.json` (84 probe-reply pairs)

Both files are local to the working environment and should be archived under the audit doc folder if needed for traceability. They are not committed to the repo.

## Appendix B — Files created in this audit

| Path | Purpose |
|---|---|
| `scripts/test/probes/15_chat_practical_logistics.yaml` | 18 probes — hours, parking, accessibility, food, etc. |
| `scripts/test/probes/16_chat_show_day_context.yaml` | 15 probes — sponsors, organizers, schedule, TELUS, dome-vs-hubble |
| `scripts/test/probes/17_chat_art_interpretation.yaml` | 20 probes — medium, tech stack, authorship, training data |
| `scripts/test/probes/18_chat_audience_voice_drift.yaml` | 25 probes — audience asks + voice/persona stress |
| `scripts/test/probes/19_chat_content_correctness.yaml` | 18 probes — facts the chatbot should get right or refuse cleanly |
| `docs/space-center/chatbot-gap-audit-2026-05-26.md` | This report |
