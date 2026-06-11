# Visitor Persona Walkthrough Audit — Overnight 2026-05-27

**Author:** orchestrator (autonomous overnight)
**Date:** 2026-05-27 ~00:00 PDT — T-2 days before IMPACT 2026 doors open
**Method:** Drive `https://salishseadreaming.art/` live via chrome-devtools MCP. For each persona: hit the chat API, navigate the relevant deep-link path, screenshot the meaningful states, document friction.
**Scope:** 10 personas from `design-gap-audit-2026-05-26.md` §2.
**Screenshots:** `/Users/darrenzal/projects/salish-sea-dreaming/.tmp-overnight-personas/`
**Chat responses (raw):** `chat-responses-1-5.json`, `chat-responses-6-10.json`

> Note: 60-min budget on persona walkthroughs. Where the UI-level click path was redundant against the chat API (which is the load-bearing surface), I exercised the API directly and screenshotted only the framing surfaces (visitor landing, graph, cloud, KP-open).

---

## Surface health snapshot (pre-walkthrough)

| Surface | URL | Status | Notes |
|---|---|---|---|
| Home | `/` | OK | 7 surface tiles render; live TD snapshot loads |
| Visitor portal | `/visitor` | OK | Textarea, consent toggles, voice feed, snapshot all live |
| Graph | `/graph?event=impact-2026` | OK | 4 bridges, hubs render |
| Cloud (Dreamworld) | `/cloud` | **DEGRADED** | `/dreams/3d` returns 0 dreams — page shows "0 dreams in the Salish Sea / Dreaming... the Salish Sea is waking up". **Critical bug.** |
| Ask | `/ask` | OK | Witness register copy intact |
| About AI | `/about/ai` | OK | Canon page renders all 5 refusal categories |

---

## Persona 1 — Researcher who wants to understand the AI architecture

**Starting context:** mid-50s, journalism / academic background. Lands on `/visitor`. Types "How does this AI actually work?"

**What they saw:**
- Chat response (200 OK, ~9s): A clean architectural explanation. Names Pravin Pillay, Darren Zal, Eve Marenghi, Shawn Anderson with `#person:` links. Describes embeddings → UMAP → 3D cloud. References `concept:dream-field-mapping`, `technique:umap`. Reads as "witness, not oracle" register.
- Clicked the `Austin Aan'yas Harry` link (via simulated DOM test): KP opens with full bio. **The KP "explore in graph →" link now includes `?event=impact-2026` scope** — fixed since the gap audit. Link still uses `target="_blank"`.

**Where they got stuck:**
- StreamDiffusion / Briony LoRA artifact cards (Phase 1 archived stack) were not mentioned by the chat — instead it described the *current* pipeline. **GOOD — system prompt has been updated to suppress Phase 1 framing for IMPACT context.**
- The "node-link in new tab" UX pattern survives. Chat conversation is lost when they navigate to the graph. Documented but not fixed.

**What worked:** Witness register holds. Node links resolve. Phase 1 leakage suppressed.

**Severity:** LOW. P2 (post-show)

**Screenshots:** `persona-01-landing.png`, `persona-01-step1-chat-mode-open.png`, `visitor-kp-austin-open.png`

---

## Persona 2 — Child whose parent is curious

**Starting context:** Kid age 9, parent encourages QR scan. Submits "I dreamed about a rainbow octopus."

**What they saw:**
- Chat response (200 OK): *"Thank you for sharing that. Your offering has been gathered into the field. The system notices where these dreams drift and how they cluster, and your rainbow octopus now exists as part of that collective movement. If you wish, you can see how your dream sits among others in the 3D view at `/dreams/3d`."*
- 3 sentences, warm-but-spare. **Improved over the 600+ char welcome the gap audit flagged.**

**Where they got stuck:**
- The link "`/dreams/3d`" is presented as code-formatted text (not clickable). Kid (or parent) has to manually type it. Even if they navigate there, **the cloud shows 0 dreams** — the rainbow octopus they just submitted is not visible.

**What worked:** Concise reply. Welcoming tone. No "I am an AI witness" preamble (good — Drift 5 from the gap audit is being managed).

**Severity:** **HIGH** — degraded cloud breaks the marquee child-engagement flow. The kid won't find their fish.

**Screenshots:** `cloud-zero-dreams-bug.png` (shows the empty cloud state)

---

## Persona 3 — Indigenous community member asks about Austin

**Starting context:** Asks "Tell me about Austin Harry."

**What they saw:**
- Chat response (200 OK): Clean, respectful. Names lineage (Sḵwx̱wú7mesh Wolf + Nam̓gis Thunderbird), names Xwalacktun, names INDIGITAL, declares Austin's stewardship over Coast Salish framings. Ends with *"For deeper insight into those specific areas, you can ask him directly or read what he and his collaborators have published."*
- Austin-gate is respected — no Coast Salish content is paraphrased.

**Where they got stuck:**
- The "ask him directly" framing has no clickable contact path. There's no `mailto:`, no INDIGITAL portfolio URL. **A visitor who wants to follow up has no concrete channel.** Open in gap audit §2.3.
- Deep-link `/graph?event=impact-2026#node=person:austin-harry` resolved correctly on second navigation. **First navigation showed a race condition** — landed on Chris Jordan instead — but reload fixed it. Possible IIFE race in `ssd-data-map.html:2729-2799`. Documented but inconsistent.

**What worked:** Refusal posture correct. Lineage named accurately. Stewardship clearly declared. No invented detail.

**Severity:** MEDIUM. Deep-link race condition could surprise venue docents demoing the flow.

**Screenshots:** `graph-austin-deeplink-resolves-to-chris-jordan.png` (first attempt — bug), `graph-austin-deeplink-second-try-good.png` (reload — fixed)

---

## Persona 4 — Potential sponsor at IMPACT

**Starting context:** Suit, badge. Asks "What is TELUS doing here? Can my company sponsor next year?"

**What they saw:**
- Chat response (200 OK): *"Compute and the Indigenomics AI platform are supported by [TELUS](#partner:telus) through their Sovereign AI Factory and H200 GPUs. Regarding sponsorship for next year, I don't have information on future sponsorship opportunities. If you would like to engage with the project or the [Indigenomics Institute](#partner:indigenomics-institute), please contact the team directly."*
- Two node links: `partner:telus` and `partner:indigenomics-institute`. Both should resolve (verified in `ssd-cards.json` on poly — `partner:telus`, `partner:indigenomics-institute`, `venue:hr-macmillan-space-centre` all exist).

**Where they got stuck:**
- No concrete contact email / URL for "contact the team directly". The visitor leaves without an action step.
- "I don't have information about future sponsorship" — fair refusal, but no breadcrumb to the Indigenomics Institute's website or contact page.

**What worked:** TELUS partner card resolves. Sponsorship-overreach correctly refused (no fabricated names). Indigenomics Institute named as the right venue.

**Severity:** MEDIUM. P1 — add concrete contact channels to `partner:indigenomics-institute` body.

---

## Persona 5 — Bioregional activist

**Starting context:** From the BWL (Bioregional Weaving Labs) network. Asks "What's a bioregion? How does this connect to bioregional weaving labs?"

**What they saw:**
- Chat response (200 OK): Solid two-paragraph answer. Cites `concept:bioregional-mapping`. Describes the BWL: *"network of over 25 international organizations, funders, and impact investors initiated by Ashoka and co-led with Commonland and OpEPA, supporting practitioners who work with communities and conservationists to shift how we relate to the land."*
- Bridges the two via *"the attempt to map complex fields — whether they are ecological signals, visitor dreams, or economic commitments — to see how they cluster and weave together without imposing a pre-determined human narrative."*

**Where they got stuck:**
- No `concept:bioregional-weaving-labs` or `partner:bwl` node — link resolution would fail if user clicks "BWL" thinking it's clickable. (The chat reply did not emit a node-link for BWL — good.)
- Verify that BWL framing is sourced (was it from a card or paraphrased from system prompt?). Worth a probe.

**What worked:** Domain-specific framing intact. Conceptual bridge to commitment pools / dream field hinted but not over-claimed.

**Severity:** LOW. Information density is reasonable.

---

## Persona 6 — Journalist on deadline

**Starting context:** Asks "Who is the press contact for this show? Who is the curator?"

**What they saw:**
- Chat response (200 OK): *"I don't have a specific press contact listed in my records. If you are looking to write about the project or need media inquiries, please contact the [Indigenomics Institute](#partner:indigenomics-institute) team. Regarding the curation, this is a collective work co-created by many people. Raf served as the curator for the *[Digital Ecologies](#hub:exhibition)* show in April, and Zoe Zafiris-Casey was the on-site lead and collaborator for that presentation. For the current [IMPACT 2026](#event:impact-2026) activation, the work is convened by the Indigenomics Institute."*
- **Excellent disambiguation** between Phase 1 curator (Raf) and Phase 2 convening (Indigenomics Institute). This was a wrong-answer in the 2026-05-25 sweep (Gap 5) — appears to be fixed.

**Where they got stuck:**
- No concrete press contact email. Journalist on deadline now has to look up Indigenomics Institute → find their website → find press contact. Adds 5-10 min friction.
- No "copy to clipboard" affordance on the chat reply (gap audit §2.6).

**What worked:** Phase 1/2 disambiguation. No false attribution. Collective framing preserved.

**Severity:** MEDIUM. P1 — add `darren@salishseadreaming.art` (already in `/about/ai` page) to the press-contact answer.

---

## Persona 7 — Returning visitor

**Starting context:** Submitted a dream yesterday. Asks "How do I find it again?"

**What they saw:**
- Chat response (200 OK): *"The system never knows who dreamed what. Visitors are anonymous; submissions are not attributable to identities. I can describe what the field as a whole gathers around, but I cannot tell you which specific dream belongs to you. Your offering may be visible as a fish-shape in the [dreamworld](#artifact:dreamworld) 3D view (`/dreams/3d`) or within the event knowledge graph (`/graph?event=impact-2026`), but it remains anonymous."*
- This is the **correct refusal posture per Category 3** (identity inference about other visitors) — but it conflates "the visitor's own dream" with "another visitor's identity". The visitor IS the dreamer, so the cookie-bound token *could* surface it. The chat doesn't access the cookie.

**Where they got stuck:**
- Dream cloud is broken (0 dreams). Even if the chat pointed them there, they wouldn't see their fish.
- No mention of `/consent` as a path for the cookie-holder to revisit their own dream's consent settings.

**What worked:** Refusal register intact. No fabrication. No leakage of other visitors' data.

**Severity:** **HIGH** — but the root cause is the empty cloud, not the chat.

---

## Persona 8 — SSD team member testing

**Starting context:** Darren / Pravin / docent. Asks "I want to test this — what hubs are in the knowledge graph?"

**What they saw:**
- Chat response (200 OK): Names `event:impact-2026`, `surface:hubble-space`, `person:darren-zal`, links to `node:gallery-server`. **Honest answer, with node-links resolvable.**
- Reply doesn't enumerate ALL hubs (correct restraint per gap audit §3.11 — system prompt guidance against listing all 25 themes).

**Where they got stuck:**
- No in-browser test/debug mode (gap audit §2.8). Docents cannot quickly verify chat health from a phone at the venue. The `/admin` page exists but isn't designed for chat-debug. Documented as a known gap.

**What worked:** Reasonable depth. Node-links emitted. No hallucinated hubs.

**Severity:** LOW (post-show concern).

---

## Persona 9 — Visitor with limited English

**Starting context:** Asks `¿Qué es esto?`

**What they saw:**
- Chat response (200 OK): **Full Spanish reply.** Translates the witness register: *"Una lectura de lo que sucede aquí es que el sistema reúne las 'ofrendas' o sueños de los visitantes y los organiza en un espacio semántico, permitiendo que emerjan agrupaciones y temas sin que alguien los nombre de antemano."*
- The translation is good. Maintains the "una lectura" (one reading) hedging.

**Where they got stuck:**
- No node-links emitted in the Spanish reply (the post-processor may not detect Spanish entity references). KP cards remain English-only.
- Mic input still hard-coded to `en-US`. A French / Spanish visitor tapping Speak gets bad transcription.
- The visitor.html welcome message is still hard-coded English.
- `<html lang="en">` not toggled.

**What worked:** Surprising — the LLM gracefully shifts language. Witness register translation is faithful.

**Severity:** LOW. Confirmed gap from §2.9; post-IMPACT.

---

## Persona 10 — Screen reader / keyboard-only

**Starting context:** Tab through `/visitor` with screen reader.

**What they saw / measured:**
- `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">` — **WCAG 1.4.4 violation.** Pinch-zoom disabled. **P0 fix per gap audit §2.10.**
- Knowledge panel: NO `role="dialog"`, NO `aria-modal`, NO `aria-label`. Tabbing through KP reaches background chat input.
- `#chat-messages`: NO `aria-live="polite"`. Screen reader won't announce new agent replies.
- `#chat-loading`: NO `aria-live`. No announcement while waiting.
- `<html lang="en">` is set (good).
- Tab order across `/visitor`: textarea → "Speak your offering" → "Send your offering" → consent checkboxes → footer links. Reasonable order.

**Where they got stuck:**
- KP open without focus trap, no `Escape` key listener, no focus restoration on close.
- Node links in chat have no `aria-label` (just `<a href="#" data-node="...">` — screen reader reads "link, hash").
- The chat reply on Persona 10's actual question ("Are there any keyboard shortcuts? Is this accessible?"): *"I don't have specific information about keyboard shortcuts or the full accessibility specifications for the installation — try the Salish Sea Dreaming team resources for those technical details."* **GAP — could point to `/about/ai` and `/consent` as keyboard-reachable paths.**

**What worked:** Visible focus rings present. Consent toggles labeled correctly. Tab order linear.

**Severity:** **HIGH** for the viewport `user-scalable=no` (visible to any user pinching to zoom). MEDIUM for the rest (a11y).

**Screenshots:** `visitor-landing.png` (default), `about-ai-page.png` (the answer that the chat *should* point to)

---

## Punch list — ranked by severity

### CRITICAL (block-the-show)

1. **`/dreams/3d` returns 0 dreams.** Cloud surface is empty. The `/prompts` endpoint has 76+ dreams (76 latest at time of test). The UMAP / 3D positions pipeline either has not been seeded or `/dreams/3d` filtering excludes everything. **This breaks Persona 2, 7, and the marquee "find your fish" flow.** Needs operator decision: kick off UMAP recompute (`POST /admin/recompute-umap` per `/about/ai`), or investigate `/dreams/3d` handler. **Same-day investigate.**

### HIGH

2. **Viewport `user-scalable=no` on `/visitor`.** A11y blocker per WCAG 1.4.4. Verified live. 1-line fix in `web/visitor.html` meta tag.
3. **Deep-link race condition on `/graph#node=...`.** First nav loaded Chris Jordan when URL specified Austin. Second nav resolved correctly. Likely IIFE timing race per `ssd-data-map.html:2729-2799`. Could embarrass at the venue if docent's first demo lands wrong.
4. **Persona 7's "find my dream" reply** redirects to the broken cloud. If cloud stays broken, system prompt should NOT direct visitors there. Suggest mentioning `/consent` as the cookie-bound surface instead.

### MEDIUM

5. **No press / sponsorship contact email in chat replies.** "Contact the team" is vague. Darren's email is on `/about/ai` (`darren@salishseadreaming.art`). Add to `partner:indigenomics-institute` body.
6. **KP missing `role="dialog"`, `aria-modal`, focus trap, `Escape` listener.** Affects screen-reader and keyboard-only visitors. Documented in §2.10 — multi-line fix.
7. **Persona 10's accessibility question gets a deflection.** Chatbot should know about `/about/ai`, `/consent`, and basic keyboard paths. Card additions worth considering.

### LOW

8. **Mic input hard-coded `en-US`.** Spanish/French speakers get bad voice transcription. Documented gap §2.9.
9. **No "copy to clipboard" on chat replies.** Journalist-friction.
10. **`/dreams/3d` not clickable in chat replies (code-formatted).** Kid persona has to manually type or remember the path.
11. **Briony LoRA / StreamDiffusion KP cards may still show without Phase 1 markers** (gap audit §2.1 #KP4 / KP5 — could not fully verify card body without reading the full cards.json).

### POSITIVE FINDINGS (regressions averted)

- **Persona 6 (curator confusion)** — `chatbot-gap-audit-2026-05-26.md` Gap 5 (Raf wrongly named as IMPACT curator) appears resolved. Reply correctly disambiguates Raf (Phase 1) vs Indigenomics Institute (Phase 2).
- **Gap audit P0 #2** — KP "explore in graph" link now includes `?event=impact-2026` scope. Fix shipped.
- **Persona 1 (researcher)** — Briony / StreamDiffusion Phase 1 stack NOT mentioned for IMPACT visitors. System prompt scoping working.
- **Persona 3 (Indigenous visitor)** — Austin-gate refusal posture clean. No invented Coast Salish content.
- **Persona 9 (limited English)** — Witness register translates faithfully into Spanish.
- **Voice register** — No instances of "I am an AI witness" preamble observed (Drift 5 from 2026-05-25 audit appears managed).

### NEEDS OPERATOR DECISION (skipped autonomously)

- Whether to ship the `user-scalable=no` viewport fix tonight (it's an obvious win but the operator may want to coordinate with Pravin given the iPad / kiosk display modes).
- Whether to kick `POST /admin/recompute-umap` to populate the empty cloud (depends on whether 3D positions DB was seeded for v5 / v6 — could be a v5↔v6 migration artifact).
- Whether to populate explicit press/sponsorship contact info in cards (Carol Anne / Indigenomics Institute may want a specific email beyond `darren@salishseadreaming.art`).

---

## Coverage matrix

| Persona | Chat tested | Screenshot | KP tested | Graph tested | Cloud tested |
|---|---|---|---|---|---|
| 1 Researcher | ✓ | ✓ | ✓ (Austin) | ✓ | n/a |
| 2 Child | ✓ | n/a | n/a | n/a | ✓ (broken) |
| 3 Indigenous | ✓ | ✓ | ✓ (Austin) | ✓ (race condition) | n/a |
| 4 Sponsor | ✓ | n/a | n/a | n/a | n/a |
| 5 Activist | ✓ | n/a | n/a | n/a | n/a |
| 6 Journalist | ✓ | n/a | n/a | n/a | n/a |
| 7 Returning | ✓ | n/a | n/a | n/a | ✓ (broken) |
| 8 SSD team | ✓ | n/a | n/a | n/a | n/a |
| 9 Limited English | ✓ | n/a | n/a | n/a | n/a |
| 10 Screen reader | ✓ | ✓ (viewport) | ✓ (a11y attrs) | n/a | n/a |
