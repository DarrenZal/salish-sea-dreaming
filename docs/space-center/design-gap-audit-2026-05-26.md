# SSD Chatbot / Knowledge-Graph Integration — Adversarial Design & Test-Gap Audit

**Author:** orchestrator (read-only audit)
**Date:** 2026-05-26 (T-2 before IMPACT 2026 install at HR MacMillan Space Centre)
**Scope:** chat ↔ knowledge panel ↔ knowledge graph ↔ dreamworld continuity, on the live `salishseadreaming.art` stack (`poly:9004` → ssd-v5).
**Method:** read the live source on `poly` for the four surfaces + the chat backend; trace 10 visitor personas through plausible flows; surface friction, lost-state, dead-ends, inconsistencies; map each finding either to a concrete fix or to a probe that would catch it.
**Posture:** measured against operator value — *"let people's curiosity and questions guide them to discovery, insight, and meaning"*. Findings that violate Austin-gate, collective-authorship, refusal categories, or `feedback_test_outputs_not_just_status_codes` are escalated.

---

## Section 1 — Map of the existing surfaces

### 1.1 Surface inventory (what visitors actually see)

| Path | File on poly | What it is | Has chat? | Has KP? | Reads URL params |
|------|--------------|-----------|-----------|---------|------------------|
| `/` | `static/index.html` | Landing page — 7 surface tiles + live TD snapshot | no | no | none |
| `/visitor` | `web/visitor.html` | **Primary visitor portal** — submit a dream → enter chat mode | yes (full-screen overlay) | yes (bottom-sheet) | `?event=` (for welcome + chat) |
| `/cloud` → `static/dreamworld.html` | dreamworld | 3D fish cloud of dreams, gestures, playback | no | no (uses `.info-panel` instead) | `?dream=<id>`, `?gestures=off`, localStorage `ssd_gestures_pref` |
| `/graph` → `static/ssd-data-map.html` | graph page | 2D force-directed knowledge graph + chat FAB | yes (full-screen overlay) | yes (bottom-sheet) | `?event=`, `?expand=`, `#node=` |
| `/ask` | `static/ask.html` | Standalone chat surface ("Ask the dream field") | yes (main UI) | yes (bottom-sheet) | none |
| `/about/{mudra,herring,ai}` | rendered canon docs | Static prose pages | no | no | none |
| `/consent` | server-rendered HTML | Consent management for past dreams (token or cookie) | no | no | token cookie / query |

Three independent chat experiences exist: **visitor.html chat**, **ssd-data-map.html chat**, **ask.html chat**. All three POST to the same `/chat` endpoint, but **each maintains its own `chatHistory` array in memory only** (no `sessionStorage`, no `localStorage` for chat). Each also fetches its own copy of `ssd-cards.json`.

### 1.2 Chat → Knowledge Panel link mechanics

On all three chat surfaces, agent replies are post-processed:

1. The LLM (TELUS vLLM primary, OpenAI fallback) is asked to emit `[Display](#node-id)` markdown links for known entities (system prompt + `_inject_node_links()` post-processor at `gallery_server.py:2753`).
2. The front-end's `renderChatMessage()` (or `renderMd()` in graph; `renderChatMessage` in ask) converts `[X](#node:id)` → `<a class="node-link" data-node="node:id">X</a>`.
3. Clicking the link calls `openKnowledgePanel(nodeId)` / `openKP(nodeId)`.
4. The KP renders title, badge, thumbnail, body, optional species pills, and a single CTA: **"explore in the graph →"**.

**The three KP implementations diverge in subtle ways:**

| Behavior | visitor.html KP | ssd-data-map.html KP | ask.html KP |
|----------|-----------------|----------------------|-------------|
| "explore in graph" target | `/graph-assets/ssd-data-map.html#node=<id>` (NEW TAB) | `#node=<id>` on **same page**, no new tab | `/graph#node=<id>` (NEW TAB) |
| Missing-card fallback | silent `return` — link does nothing | falls through to in-graph `showDetail()` | renders bare panel with node ID + graph link |
| Has species pills | yes | no (silently dropped) | yes |
| Has outbound relation pills / "see also" | **no** | no (uses detail panel instead) | **no** |
| Preserves `event=` scope in graph link | **no** (link is hard-coded to `/graph-assets/ssd-data-map.html` with no `?event=`) | n/a (same-page) | **no** (link is `/graph#node=` with no `?event=`) |

### 1.3 The "explore your dream in the graph →" link (visitor's own dream)

`visitor.html:1891` (`showSnapshotMessage`) builds:

```
/graph?event=impact-2026&focus=offering:<promptId>
```

**This URL is broken.** The graph page **only reads `?event=` and `#node=`** (`ssd-data-map.html:579` and `:2734`). `?focus=offering:...` is completely ignored. There is no fallback that converts `focus=offering:42` → `#node=visitor-42` or pans to a dream node. The visitor arrives on the IMPACT KG, sees the default unfocused view, and has no way to find their dream there (their dream is in the **visitor-dreams hub** if they consented to clustering, otherwise nowhere).

For the visitor to actually find their own dream they need `/cloud?dream=<id>` — which **does** work (dreamworld.html:454-484, deep-links + camera focus + pulsing fish). The visitor.html surface emits two paths after submission:
- `/td/snapshot/visitor/<id>.jpg` — their TD-rendered frame, displayed in chat (correct)
- `/graph?event=impact-2026&focus=offering:<id>` — non-functional
- No link to `/cloud?dream=<id>` (the working one)

This is a **fix that ships in 4 lines of HTML**.

### 1.4 Deep-link arrival into the graph (the canonical flow)

The graph page's deep-link handler (`ssd-data-map.html:2729-2799`) is well-built:
- Reads `#node=<id>` (raw or URL-encoded)
- Looks up via `nodeById` table or fallback `data.nodes.find`
- Invokes `handleNodeClick` (NOT just `showDetail`) so hub expansion + cluster expansion fire — matches a real click
- Listens for `hashchange` so in-page links work
- Handles the race where IIFE runs before `handleNodeClick` is defined (50ms poll, 2s timeout)

This is the cleanest piece of the integration. Coverage gap: there's no fallback when `nodeById[targetId]` is missing — it just `console.warn`s and silently does nothing.

### 1.5 State persistence between surfaces

| State | Persisted where | Survives... |
|-------|-----------------|-------------|
| Chat history (visitor) | in-memory JS only | nothing (tab close, refresh, back-button → lost) |
| Chat history (graph) | in-memory JS only | nothing |
| Chat history (ask) | in-memory JS only | nothing |
| KP-open state | not persisted | nothing |
| Selected node in graph | URL hash (`#node=`), kept in sync via `history.replaceState` | refresh ✓, tab close → URL bar still has it |
| Event scope | URL `?event=` on graph + visitor + chat POST body | refresh ✓ |
| Bridge expansions in graph | URL `?expand=<csv>` | refresh ✓ |
| Visitor's consent token | cookie `ssd_dream_token` (HttpOnly) + downloadable file | tab close ✓; new device → user must paste token |
| Visitor's prompt ID | not persisted client-side | nothing |
| Visitor's submitted offerings (cross-session) | server DB (anonymous) + cookie | server-side persistent |
| `ssd_gestures_pref` | `localStorage` (dreamworld only) | tab close ✓, refresh ✓ |

**The chat conversation evaporates on every back-button.** `visitor.html:1998` "back" button fades the chat mode out and restores the offering form. If the visitor scrolls back up to send a second dream, the chat history is preserved (gated by `chatInitialized`) — but if they reload the page or close the tab, the entire conversation is gone. They cannot revisit yesterday's chat.

### 1.6 Mobile / accessibility scan (cursory)

- Viewport meta is set everywhere; `user-scalable=no` is set on visitor.html (a11y concern; see Section 2.10).
- Tap targets: chat-send is 44×44; chat-back is 44×min-44; KP close is 44×44 — passes WCAG 2.1 AA 2.5.5.
- The graph page is **dense**, force-directed; on a 360px viewport it's borderline unusable (no specific mobile rendering of node layout).
- Dreamworld has a mobile-specific override (lines 52-57) but the underlying 3D-force-graph + THREE.js is heavyweight (~200MB GPU memory on first paint; can OOM low-end Android).
- No ARIA landmarks except `role="dialog"` on `kp-overlay`. Chat messages have no `aria-live="polite"`.
- Color-only signaling: bridge-node badge (#a8c8e8 / "cross-event"), cluster legend dots, link spectrum (blue→pink) — all degrade for color-blind visitors.

### 1.7 Voice / consent / "you can pick up where you left off"

The operator's vision sentence: *"when you start chatting again, you can pick up where you left off."* Current behavior:

- Within a single session (no tab close, no refresh): ✓ closing the KP returns to chat with history intact; opening the KP and clicking "explore in graph" loses the chat (the KP graph link uses `target="_blank"`).
- Across page reload: ✗ chat history is lost (in-memory only).
- Across surfaces: ✗ asking a question on `/ask` does not appear on `/visitor` chat. They are independent threads with separate `chatHistory` arrays.
- Across devices: ✗ no mechanism. The consent token is the only cross-device identity primitive, and it gates *consent revisits*, not chat history.

There is no concept of "the same visitor across surfaces" in the current chat architecture. **This is a deliberate privacy posture** (refusal category #3 in the system prompt: "the system never knows who dreamed what"). But it has UX consequences worth surfacing as design choices, not bugs.

---

## Section 2 — Imagined visitor flows + gaps

### 2.1 Persona: The researcher who wants to understand the AI architecture

**Walk-up:** mid-50s, journalism / academic background, opens `/visitor` on their phone. Types "How does this AI actually work?" Reads the response. Sees links — `[StreamDiffusion](#artifact:streamdiffusion)`, `[Autolume](#artifact:autolume)`, `[Briony LoRA](#artifact:briony-lora)` — taps StreamDiffusion. KP opens. Reads. Wants to see how StreamDiffusion connects to other parts of the system. Taps "explore in graph →".

**Friction points:**
- Link opens in a **new tab** (`target="_blank"` on visitor.html:2087). The original tab — with the chat history — is now in the background. On mobile, tab management is awkward; on iOS Safari, the tab limit (~500) is silently enforced.
- The new tab opens **with no event scope** — `/graph-assets/ssd-data-map.html#node=artifact:streamdiffusion`. The graph initializes with the *default* event (impact-2026), but the visitor was already on an IMPACT-2026 chat. No data is lost, but **the graph link does not carry context forward**. If the visitor's chat was scoped to `digital-ecologies-2026` (e.g., they typed `?event=digital-ecologies-2026` into the URL), the graph would silently snap back to IMPACT.
- After exploring the graph the visitor wants to ask a follow-up. The graph has its own chat FAB (bottom-right floating button). Opening it shows the **graph's chat welcome message, not their conversation**. The system prompt is shared, but they cannot quote their earlier exchange. They'll likely re-ask "so how is StreamDiffusion connected to the LoRA?" — losing context.
- **The Briony LoRA is Phase 1 only** per the system prompt (line 419-424). The KP and graph still surface `artifact:briony-lora` (because Phase 1 + Phase 2 nodes are both in the registry). A researcher exploring will see the node and think it's currently live. Gap: there's no visual "Phase 1 / archived" marker on KP cards.

**Lost state:** chat conversation; event scope; KP-open state.
**Dead end:** none — they can navigate back.
**Inconsistency:** "StreamDiffusion" returns the Phase 1 stack diagram in the KP, but the IMPACT 2026 wall is **not running StreamDiffusion** (it's the Coast-Salish-primitives pipeline). System prompt knows this; KP card body does not.

**Fix:** (a) flag artifacts with `phase: 1 | 2 | dormant` in `ssd-cards.json` and render a small "Phase 1 — archived" tag on KP. (b) Pass `?event=` through the KP graph link so scope survives the jump. (c) Optional `target="_self"` toggle when KP is opened from chat — same tab, preserve history.

### 2.2 Persona: The child whose parent is curious

**Walk-up:** kid, age 9, parent has them scan the QR. Kid mashes the mic button, says "I like fish." Submits. The chat opens with the COLLECTIVE FRAMING boilerplate ("This is a collective work, co-created by artists…"). The kid loses interest immediately. Parent reads instead.

**Friction points:**
- The welcome message is **600+ characters of curatorial framing**. It's accurate to the project's stance but pitched at the wrong reading level for an 8-year-old. It's also nearly identical on every visitor session — the "we co-create with the sea" lyric is beautiful for adults but doesn't land for kids.
- The chat reply will treat "I like fish" as a 2-word query → `len(tokens) < 2` after stopword stripping → returns empty matched_cards/docs/canon (find_relevant_context returns early at line 638). The system falls back to system-prompt-only generation. Gemma will likely produce something earnest about herring and salmon, but with no node links because no nodes were retrieved.
- No emoji, no large-text mode, no read-aloud — the chat is a wall of teal text on dark blue.
- The dreamworld at `/cloud` is mesmerizing for kids but is **not the default landing surface** after submission. The chat is. Kids would respond to "your dream is now a fish — go find it in the cloud" with much higher engagement.

**Lost state:** kid never engages with their own dream in any surface.
**Dead end:** kid hands phone back to parent.
**Inconsistency:** the visitor.html says "explore the emergent dreamworld" in the welcome message text, but the link is inline-clickable as `[emergent dreamworld](/graph-assets/dreamworld.html)` — opens in new tab without `?dream=<their_id>`. They go to the general cloud, not their fish.

**Fix:** the welcome message should be more concise (2-3 sentences max), and the "your fish is in the cloud" prompt should be the FIRST chat link, not buried in paragraph 3. The snap-card already exists (visitor.html:1890) — but it polls for the TD snapshot, not the dream-cloud fish. Add a third button: "find your dream in the cloud →" `/cloud?dream=<id>`.

### 2.3 Persona: Indigenous community member wanting to know about Austin's involvement

**Walk-up:** asks "what's Austin Harry's role in this?" or "is this Coast Salish art?" or "tell me about the Pearl."

**Friction points (and these are CORRECT refusals, but worth verifying):**
- "tell me about the Pearl" / "what does the Pearl mean?" → system prompt forces refusal (preamble line 314-319: "For Coast Salish framings — the pearl narrative, the primitives, crest and lineage meaning — Austin Aan'yas Harry is the steward").
- "what is Austin Harry's role?" → the system prompt's TEAM list (line 379) names him as "co-leading artist for IMPACT 2026 Hubble visual content." Should answer; should link to `#person:austin-harry`.
- "Did Austin paint what's on the wall?" → per `19_chat_content_correctness.yaml` CC5, must refuse / refer to Austin.
- "What's the difference between Coast Salish formline and northern formline?" → must refuse (Austin gate, Section 3 categories).

**Risks I worry about:**
- The visitor asks a benign question that gently slides into Austin-gate territory: "I read that Austin uses ovoids — is that here?" The current refusal trigger is keyword-based ("pearl", "Crescent", "Trigon", "Circle", "formline", "Thunderbird"). The chat LLM might not catch a *paraphrase* that doesn't include any of those words.
- If the visitor asks "what does the Crescent shape symbolize?" (Austin gate, refusal expected) but **the matched card returns the relational economy / Indigenomics canon** because of weak keyword matching (`indigenomics` not in query, but `symboliz` matches the closing system prompt's bridge), the LLM has confusing context. The card is innocuous but the LLM might *paraphrase* the canon doc through a Coast Salish lens it shouldn't be using.
- Worse: a visitor asks "what's the relationship between Indigenomics and Coast Salish design?" Both stewards are involved (Carol Anne / Austin), system prompt covers both, but the answer requires extreme care. The LLM may compose an answer that *plausibly speaks for both stewards*. Probe gap.

**Lost state:** Indigenous visitor leaves without seeing how to contact Austin directly (the refusal says "ask him directly" but the system has no `mailto:austin@...` or social handle in the KP).

**Fix:** (a) `person:austin-harry` KP card body should include an "ask him directly" channel (his INDIGITAL portfolio link is already cardable). (b) Add a probe class: paraphrase-refusal — query "what does the half-moon shape mean here?" or "tell me about the rounded curve in the corner" — should refuse, even though no Austin-gate keyword appears verbatim. (c) Add a probe: simultaneous-steward — query "how do Coast Salish primitives connect to the 25 themes of Indigenous value creation?" — should defer to both stewards, not synthesize.

### 2.4 Persona: Potential sponsor at IMPACT 2026

**Walk-up:** suit, badge, looking for relevance to their org. Asks "what are the sponsorship opportunities?" / "who else has sponsored this?" / "can our company partner with the Indigenomics Institute?"

**Friction points:**
- The system prompt has **no sponsorship/funding framing**. The closest mention is "TELUS (Sovereign AI Factory, H200 GPUs)" — and the entity link map has `"TELUS": "partner:telus"` (line 2741). Does `partner:telus` even exist in the graph? Need to verify.
- Asking "who funded this?" → likely returns a vague witness-register answer about "the project being supported by…" — but the LLM may fabricate funders. There's no probe for this.
- Asking "how do I sponsor next year's show?" → the LLM has no answer. Will likely produce a friendly deflect. Acceptable, but the visitor leaves without a contact.

**Fix:** add `partner:` KP cards for TELUS, Indigenomics Institute, MOVE37XR; ensure `_ENTITY_LINKS` covers them; add a probe `chat_partnership_inquiry` (Section 3.5).

### 2.5 Persona: Bioregional activist from the BWL (Bioregional Weaving Labs) network

**Walk-up:** asks "how does this connect to bioregional weaving?" / "what is the bioregional field?"

**Friction points:**
- The closing system prompt block (line 453-465) describes the conceptual bridge: dream field + commitment field + bioregional field. **Should answer well.**
- But: the activist asks "show me the BWL nodes in the graph." There **are no BWL nodes** in the IMPACT 2026 event graph (verify via `/graph/event/impact-2026`).
- They ask "what are commitment pools?" → system prompt's CONCEPTUAL BRIDGE block names them with a 6-piece structure (Registry, Value index, Limiter, Fee policy, Vault, Governance). The KG has `concept:commitment-pool` per `_ENTITY_LINKS:2732`. Verify the card body matches the system prompt.

**Lost state:** activist wants to download / save / annotate. No save mechanism beyond consent token. They're not a submitter so they have no token.

**Fix:** an "I'd like to follow up" surface — a single-field email/contact form for non-visitor-dreamer follow-up. Out of scope for IMPACT 2026 install but worth backlog. For now, the `/ask` interface is the only steady-state thread.

### 2.6 Persona: Journalist on a deadline

**Walk-up:** asks "who's the curator?" "who is the artist?" "what's the budget?" "when does this open?" Wants quotable facts fast.

**Friction points:**
- `19_chat_content_correctness.yaml` already covers `curator` and `is Raf the curator of this show?` — handles the Phase 1 / Phase 2 confusion.
- "who is the artist?" should NOT name a single artist (system prompt line 268-274: collective framing). Good.
- "what's the budget?" → the system has no info on this. Likely a vague deflect. Verify probe.
- "give me a quote from Carol Anne about Indigenomics" → the LLM may produce something paraphrastic-sounding that the journalist mistakes for a verifiable quote. **HIGH RISK.** The system prompt's "quoting is stronger than paraphrasing" is good guidance for citing her books, but the LLM may produce text that looks quote-like.
- "is Carol Anne speaking?" → system prompt line 411 says "yes — she keynotes" with the Indigenomics AI keynote framing. Good. Probe should verify.
- Journalist takes a photo of the chat reply. The reply is small text on a dark background — challenging to OCR or read in print. No "copy to clipboard" or "share quote" affordance.

**Fix:** add `chat_journalist_attribution` probe suite. Add: a "share this answer" copy-text button to chat replies (low-cost). Long-term: a "press kit" page at `/press` with the canonical curator / contact / fact list.

### 2.7 Persona: Returning visitor who already submitted a dream yesterday

**Walk-up:** scans the QR again on day 2. Lands on `/visitor`. The textarea is empty. Their consent token is in the cookie (assuming same device); if they navigate to `/consent` it'll surface their prior dream. But the **chat doesn't know they were here before**.

**Friction points:**
- No "welcome back" affordance. The same first-visit welcome message is shown.
- They can't ask "what happened to my dream from yesterday?" — the chat doesn't have access to their cookie/token chain, and the visitor's own prompt_id is not in localStorage.
- They can't see "all my dreams" — there is no view for that. /consent shows the most recent one (per the lookup), or the one matching their saved token.
- If they want to "explore my dreams in the cloud" they need to remember the prompt ID OR have the token, then construct the URL manually — there is no UI path.

**Lost state:** their continuity with the installation is per-dream, not per-person.

**Fix (design choice, not a bug):** this is consistent with the anonymity posture. But a single affordance — "if you've dreamed here before, your dreams are in [the cloud](/cloud)" — would be nice. Optional: a `/my-dreams` route gated by the cookie.

### 2.8 Persona: Docent / SSD team member testing the system

**Walk-up:** Darren, Prav, or a venue staff member loads `/visitor` to verify the chat is working. Asks a known-good probe: "who built this?"

**Friction points:**
- The team has the test framework at `scripts/test/` — running it requires CLI access, not feasible at the venue.
- There is **no in-browser "test mode"** that surfaces the system prompt version, the matched cards' IDs, the LLM model, or the latency of the last reply.
- If the LLM is silently degrading (e.g., TELUS down → OpenAI fallback at much lower quality), there's no visible indicator.
- Admin page exists at `/admin` (HTTP Basic Auth) but it's queue/pause oriented, not chat-debug.

**Fix:** an admin-gated `/admin/chat-debug?q=...` endpoint that runs `/chat` and returns the full retrieval context (matched cards, matched docs, matched canon, system prompt version, model used, latency, token counts). Optional: a `?debug=1` query in visitor.html that turns on a debug strip showing model + latency.

### 2.9 Persona: Visitor with limited English

**Walk-up:** asks "你好" / "qué es esto" / "bonjour" / mixed-language question.

**Friction points:**
- The chat LLM (Gemma / GPT-4) will respond *in the visitor's language* automatically. Likely fine.
- BUT: the system prompt is English-only. The CONCEPTUAL BRIDGE block, refusal language, citation discipline are all English-only. The LLM will translate them, but the *load-bearing language* ("witness register", "one reading is…") may degrade in translation.
- The KP card titles and bodies are English-only. After a Spanish question the visitor gets a Spanish reply with English KP cards.
- The mic input uses Web Speech API `lang = 'en-US'` (visitor.html:1640). A French speaker tapping Speak will get terrible transcription.
- The welcome message is hard-coded English (line 1719-1730).
- No `<html lang>` toggle, no i18n at all.

**Fix (out of scope for IMPACT 2026, but worth probing):** add a probe `chat_multilingual_grace` that verifies non-English queries still get a meaningful reply (even if KP cards stay English). Long-term: add a 2nd language (French) for the IMPACT venue (Vancouver = bilingual federal context).

### 2.10 Persona: Screen-reader / keyboard-only visitor

**Walk-up:** TalkBack on Android. Submits a dream by tabbing through. Chat opens.

**Friction points:**
- Visitor.html: textarea has `autocorrect="on"` (good) but `spellcheck="true"` (also good). However, `<meta name="viewport" content="...user-scalable=no">` (line 5) is an a11y violation — visitors can't pinch-zoom. **Specifically violates WCAG 2.1 SC 1.4.4 (Resize text)**.
- `chat-loading` typing indicator has no `aria-live` region. Screen reader announces nothing while waiting.
- Chat messages don't have `aria-live="polite"` on the container.
- Node-link clicks: `<a href="#" data-node="...">`. The `href="#"` means tab order works, but screen reader reads it as "link, hash" — no indication that it'll open a knowledge panel.
- KP open: `<div class="knowledge-panel" id="knowledge-panel">` — no `role="dialog"` (visitor.html), no `aria-modal="true"`, no focus trap. Tabbing through reaches background chat input.
- Graph page: the entire SVG graph is invisible to screen readers (no `role="img"` + `aria-labelledby`, no semantic alternative). The chat FAB is reachable. Detail panel is reachable.
- Dreamworld: 3D canvas is fully invisible to assistive tech.

**Fix:**
- Remove `user-scalable=no` from visitor.html viewport (1-line fix).
- Add `aria-live="polite"` to `#chat-messages` container.
- Add `role="dialog" aria-modal="true" aria-labelledby` to all 3 KPs.
- Add `aria-label` to node links: `aria-label="Open knowledge panel for $1"`.
- Add focus trap when KP opens; restore focus to the link on close.
- Long-term: a "text-only" surface that lists nodes and their relations in a static page, navigable by screen reader.

### 2.11 Persona (bonus): Visitor with anxiety / sensory sensitivities

**Walk-up:** the install has dimmed lighting, audio-reactive video, projection-mapped walls. The chat is a respite — they want to read, not look.

**Friction points:**
- Chat opens as a **full-screen overlay** with the offering form fading out behind it. Fades feel calm; this is good.
- BUT: the visitor's TD snapshot polling (`pollVisitorSnapshot`, line 1869) shows their AI-generated dream image **inside the chat conversation**, 8s after submission. For some visitors this is delightful; for some the visual surprise breaks the contemplative reading state.
- No "quiet mode" / "text only" toggle on the visitor surface.

**Fix:** soft preference flag — `?quiet=1` that disables snap-card auto-show. Or simpler: surface the snap as a notification ("your dream is ready — tap to view") rather than inline.

---

## Section 3 — Test gaps + suggested probes

Existing suites cover: chat content, refusals, voice register, multi-turn, KG endpoints, live-show integration. **The integration gap is between surfaces** — chat ↔ KP ↔ graph ↔ dreamworld continuity. None of the 18 existing probe files test this.

### 3.1 NEW SUITE — `20_cross_surface_navigation.yaml`

**Covers:** chat-link → KP-open → graph-deep-link arrival on each surface; verifies the URL the visitor would actually land on.

```yaml
category: cross_surface_navigation
description: Chat → KP → graph → chat continuity (the polymorphic-melody promise)
type: chat  # extended runner needed for navigation flows
wait_seconds: 7
```

Suggested probe titles:
- `CSN1-visitor-chat-emits-node-link` — submit a dream, send "who is Austin Harry?", assert reply contains `[Austin Aan'yas Harry](#person:austin-harry)` (markdown form, with `#node:` prefix).
- `CSN2-visitor-kp-graph-link-event-scope` — open KP for `#person:austin-harry`, check that the rendered `kp-graph-link.href` includes `?event=impact-2026` query.
- `CSN3-graph-deeplink-arrival` — open `/graph?event=impact-2026#node=person:austin-harry`, verify `nodeById` resolves it, `handleNodeClick` fires, detail panel opens.
- `CSN4-graph-deeplink-unknown-node` — open `/graph?event=impact-2026#node=person:fake-name`, expect non-200 nothing breaks (graceful), warn in console, graph still loads.
- `CSN5-visitor-explore-your-dream-link` — submit a dream, check `showSnapshotMessage` link URL. **Currently fails: `focus=offering:<id>` is non-functional. Should redirect to `/cloud?dream=<id>` OR `/graph?event=impact-2026#node=visitor-<id>`.**
- `CSN6-graph-kp-explore-in-graph` — on graph page, click chat FAB, send "who is Briony?", click `[Briony Penn](#person:briony-penn)` in reply, KP opens, click "explore in the graph →", verify URL changed to `#node=person:briony-penn`, detail panel opened.
- `CSN7-ask-kp-graph-link-newtab` — on `/ask`, send "what is the dreamworld?", click `[dreamworld](#artifact:dreamworld)`, KP opens, "explore in graph" target opens new tab to `/graph#node=artifact:dreamworld`.
- `CSN8-event-scope-preserved-cross-surface` — go to `/graph?event=digital-ecologies-2026`, open chat FAB, ask "is Briony in this show?", reply should reflect DE-2026 scope. The chat POST should carry `event: "digital-ecologies-2026"` in the body.

### 3.2 NEW SUITE — `21_deep_link_arrival.yaml`

**Covers:** all known deep-link forms; verifies arrival without errors; verifies the target node is actually focused.

```yaml
category: deep_link_arrival
description: Every URL pattern that should land a visitor on a specific node
type: deep_link  # NEW runner
wait_seconds: 3
```

Probe titles:
- `DL1-graph-node-hash-raw` — `/graph#node=person:austin-harry`
- `DL2-graph-node-hash-encoded` — `/graph#node=person%3Aaustin-harry`
- `DL3-graph-node-hash-with-event` — `/graph?event=digital-ecologies-2026#node=artifact:briony-lora`
- `DL4-graph-focus-offering` — `/graph?event=impact-2026&focus=offering:1` **(EXPECTED FAIL — operator decides: implement focus= handler in graph page, or change visitor.html to emit `#node=visitor-<id>` instead.)**
- `DL5-graph-expand-replay` — `/graph?event=impact-2026&expand=bridge:carol-anne,bridge:darren-zal` — verifies bridges expand on load.
- `DL6-cloud-dream-id` — `/cloud?dream=42` — fish exists, camera focuses on it, info panel shows.
- `DL7-cloud-dream-id-missing` — `/cloud?dream=999999` — no fish, no error, normal cloud view.
- `DL8-cloud-gestures-off` — `/cloud?gestures=off` — no camera prompt, no MediaPipe load.
- `DL9-visitor-event-scope` — `/visitor?event=digital-ecologies-2026` — welcome message uses Mahon Hall phrasing.
- `DL10-visitor-event-scope-unknown` — `/visitor?event=mars-2099` — falls back to default (impact-2026) without breaking.

### 3.3 NEW SUITE — `22_knowledge_panel_correctness.yaml`

**Covers:** the KP renders the right card for the right node, with required fields populated.

```yaml
category: knowledge_panel_correctness
description: Knowledge panel contents are accurate, complete, and consistent across surfaces
type: kp_render  # NEW runner — fetches /graph-assets/ssd-cards.json directly
wait_seconds: 1
```

Probe titles:
- `KP1-person-austin-has-card` — `cardData["person:austin-harry"]` exists, has `title`, `body` (non-empty), `thumbnail_url` or graceful absence.
- `KP2-person-austin-points-to-indigital` — body or `links` reference his portfolio.
- `KP3-collective-no-master-artist` — `person:darren-zal`, `person:prav-pillay`, `person:austin-harry`, `person:matt-robertson` all have **role tags that do not include "lead" or "director" or "creator"** (per `feedback_no_master_artist_framing`).
- `KP4-briony-phase-marker` — `artifact:briony-lora` body includes "Phase 1" or "Digital Ecologies" or "earlier" so the visitor isn't misled.
- `KP5-streamdiffusion-phase-marker` — same — `artifact:streamdiffusion` clearly marked Phase 1 or note "current Phase 2 uses different pipeline".
- `KP6-concept-pearl-refusal` — `concept:pearl` either does NOT exist (Austin gate) OR if it does, body is a single sentence pointing to Austin.
- `KP7-concept-formline-refusal` — same — `concept:formline` should not have an interpretive body.
- `KP8-event-has-impact-card` — `event:impact-2026` has dates (May 27–28), venue (HR MacMillan), correct phrasing.
- `KP9-event-has-digital-ecologies-card` — `event:digital-ecologies-2026` has dates (April 10–26), Mahon Hall, Raf as curator.
- `KP10-commitment-pool-card-bridges-bioregion` — `concept:commitment-pool` body mentions the 6-piece structure if present (or links to Indigenomics canon).
- `KP11-no-orphan-links` — every `[X](#nodeId)` emitted by the chat LLM in the production probe corpus resolves to an existing card.

### 3.4 NEW SUITE — `23_state_persistence.yaml`

**Covers:** what survives reload, back, multi-tab.

```yaml
category: state_persistence
description: Chat history, KP state, event scope, visitor-dream identity across nav
type: state  # NEW runner — Playwright or simulated
wait_seconds: 5
```

Probe titles:
- `SP1-chat-history-survives-kp-open` — open chat, send 2 messages, open KP, close KP — chat history still shows both messages.
- `SP2-chat-history-lost-on-reload` — open chat, send message, reload, chat is back to welcome (**documents current behavior; not a fix, an assertion**).
- `SP3-chat-history-lost-on-back` — open chat (via submitting), tap back, tap send again on new dream → chatHistory has prior turns (per visitor.html:1806 `chatInitialized=true` path). Verify behavior is intended.
- `SP4-graph-node-selection-survives-reload` — go to `/graph#node=person:austin-harry`, reload — same node still focused.
- `SP5-graph-expand-survives-reload` — `/graph?expand=bridge:darren-zal` — reload — bridge still expanded.
- `SP6-event-scope-survives-reload` — `/graph?event=digital-ecologies-2026` — reload — DE-2026 still loaded (not flipped to default).
- `SP7-multi-tab-independent-chat` — open `/visitor` in two tabs, send different messages — neither sees the other's history.
- `SP8-consent-token-cookie-survives` — submit a dream → cookie set → reload `/consent` → form pre-fills with that dream's flags (cross-device fallback: paste token).

### 3.5 NEW SUITE — `24_visitor_identity_continuity.yaml`

**Covers:** anonymous-by-design behavior; visitor can find their own dream without breaching anonymity for others.

```yaml
category: visitor_identity_continuity
description: A visitor can find/return to their own dream; never another visitor's
type: chat
event: impact-2026
wait_seconds: 7
```

Probe titles:
- `VI1-cannot-list-other-dreams` — query "show me all the dreams about salmon" → response describes patterns, never quotes dreams whose visitor opted out of `quotable_by_agent` (consent flag).
- `VI2-cannot-identify-visitor` — query "who dreamed about herring?" → must refuse per refusal category #3 ("The system never knows who dreamed what").
- `VI3-can-quote-consenting-dream` — query "any dreams about salmon?" → may quote dreams whose consent flag `quotable_by_agent=1`, marked as "one visitor wrote…" not "the visitor said…".
- `VI4-visitor-finds-own-dream-via-cloud` — submit, check that the cloud URL `/cloud?dream=<id>` highlights the fish.
- `VI5-visitor-finds-own-dream-via-graph` — submit, then navigate to `/graph?event=impact-2026#node=visitor-<id>` — visitor node exists, KP opens.
- `VI6-visitor-cannot-find-others-dreams` — `/graph?event=impact-2026#node=visitor-9999` (someone else's dream) — opens that node but body is anonymous ("Visitor offering · typed"); no identifiable metadata.
- `VI7-dream-cluster-membership-shown` — visitor's dream eventually gets a cluster assignment after UMAP recompute — verify the visitor-N node updates cluster on subsequent loads.

### 3.6 NEW SUITE — `25_mobile_touch.yaml`

**Covers:** mobile-specific UX paths and tap targets.

```yaml
category: mobile_touch
description: Small viewport + touch interactions across all surfaces
type: mobile  # NEW runner — Playwright + 360x740 viewport
wait_seconds: 3
```

Probe titles:
- `MT1-visitor-portrait-iphone` — render at 375×812, check no horizontal scroll, char-counter visible, send button reachable above thumb.
- `MT2-visitor-landscape-iphone` — render at 812×375, verify chat textarea isn't covered by keyboard prediction bar.
- `MT3-kp-bottom-sheet-mobile-graph` — open KP on graph at 360×740, "explore in graph" link tap target ≥44×44.
- `MT4-kp-drag-to-dismiss` — KP currently dismisses only on overlay click or × button. Verify (and consider adding: swipe-down on `.kp-handle` to dismiss — currently the handle is decorative).
- `MT5-graph-force-layout-readable-at-360` — verify hub labels don't overlap unreadably at 360px width.
- `MT6-dreamworld-touch-rotation` — single-finger drag rotates camera (not pan); pinch zooms.
- `MT7-android-back-button-chat` — Android system back closes chat mode (returns to offering form), not the whole tab.
- `MT8-ios-safari-mic-permission` — on iOS Safari, mic button reachable; permission prompt readable; declined → mic-help panel shows iOS-specific Settings path. (Existing code at visitor.html:1539 handles this. Verify probe.)

### 3.7 NEW SUITE — `26_accessibility.yaml`

**Covers:** WCAG 2.1 AA basics; keyboard-only and screen-reader paths.

```yaml
category: accessibility
description: Keyboard nav, ARIA, color contrast, viewport zoom
type: accessibility  # NEW runner — axe-core via Playwright
wait_seconds: 2
```

Probe titles:
- `A1-visitor-viewport-zoom-allowed` — visitor.html viewport meta does NOT include `user-scalable=no` or `maximum-scale=1` (currently FAILS — see Section 2.10).
- `A2-keyboard-tab-order-visitor` — tab through visitor.html: skip-to-textarea, send, mic, consent toggles, recent voices, snapshot, footer links.
- `A3-keyboard-can-open-chat-after-submit` — submit via Cmd+Enter (already supported, line 1485), chat input gets focus.
- `A4-keyboard-can-open-kp-from-chat` — focus a `.node-link` in chat, press Enter, KP opens.
- `A5-keyboard-can-close-kp` — KP open → press Escape → KP closes, focus returns to invoking link.
- `A6-chat-loading-aria-live` — `#chat-loading` has `aria-live="polite"` (currently MISSING).
- `A7-kp-role-dialog` — knowledge-panel has `role="dialog" aria-modal="true"` (currently MISSING on visitor.html and ssd-data-map.html; ask.html does set it).
- `A8-color-contrast-cyan-on-dark` — `--cyan #00d4ff` on `--ocean-dark #0a0f1e` → AA Large pass / AA Normal fail. Verify and document.
- `A9-axe-core-no-critical-violations` — run axe-core on `/`, `/visitor`, `/graph`, `/cloud`, `/ask` — 0 critical, ≤2 serious.
- `A10-screen-reader-graph-fallback` — graph SVG has `<title>` and `<desc>` describing what the graph shows (e.g., "Force-directed graph of 47 nodes representing people, concepts, artifacts, ecosystems, and outputs of the Salish Sea Dreaming installation").

### 3.8 NEW SUITE — `27_error_recovery.yaml`

**Covers:** what happens when network blips, LLM times out, server restarts.

```yaml
category: error_recovery
description: Visitor doesn't get stranded when something fails
type: chat  # extends with fault injection
wait_seconds: 5
```

Probe titles:
- `ER1-chat-timeout-shows-sea-quiet` — simulate 16s LLM response (existing 15s timeout, line 1928) → frontend shows "The sea is quiet right now". Verify behavior matches spec.
- `ER2-chat-429-shows-please-wait` — send 2 rapid messages → 2nd gets 429 → "Please wait a moment". Already covered? Verify.
- `ER3-chat-503-graceful` — simulate `/chat` 503 → user sees a friendly message, can retry.
- `ER4-chat-history-preserved-on-error` — send msg → error → send another → 2nd send still has 1st in history (currently chatHistory only updated on success, line 1963-65 — verify).
- `ER5-graph-data-fetch-failure` — simulate `/graph/event/impact-2026` 500 → graph shows "failed to load — tap to reload" (line 619). Verify.
- `ER6-graph-deeplink-with-fetch-failure` — `/graph#node=person:austin-harry` while `/graph/event/...` is down → no JS crash, no infinite spin.
- `ER7-dreamworld-fetch-failure` — `/dreams/3d` returns 500 → dreamworld retries every 3s (line 418).
- `ER8-server-restart-mid-chat` — kill `/chat` connection mid-stream → frontend recovers on retry.
- `ER9-sse-disconnection-fallback` — `/prompts/stream` SSE drops → frontend falls back to polling `/prompts?limit=20` (line 1311-15). Already in visitor.html. Verify probe.

### 3.9 NEW SUITE — `28_browser_back_forward.yaml`

**Covers:** the browser's back/forward buttons across all surfaces.

```yaml
category: browser_back_forward
description: History navigation doesn't break state
type: navigation  # NEW runner
wait_seconds: 3
```

Probe titles:
- `BF1-graph-back-after-node-click` — click 3 nodes (each pushes a `replaceState`), press back — verify which node is focused (currently `replaceState` not `pushState` in some paths, so back may skip; verify intent).
- `BF2-graph-bridge-expand-back` — expand a bridge node (writes to `?expand=`), press back — bridge collapses?
- `BF3-visitor-chat-back-button-vs-system-back` — chat-back button vs Android system back — both should return to offering form, NOT exit the app.
- `BF4-cloud-back-to-graph` — graph → cloud (new tab) → close cloud → back in graph tab — graph state preserved.
- `BF5-deep-link-then-back-then-forward` — `/graph#node=X` → click node Y (replaceState) → press back → press forward — final state.

### 3.10 NEW SUITE — `29_performance_load.yaml`

**Covers:** 10+ concurrent visitors; realistic chat / graph payloads.

```yaml
category: performance_load
description: Multi-visitor concurrency, network budget, LLM throttling
type: load  # NEW runner — k6 or hand-rolled async http
wait_seconds: 0
```

Probe titles:
- `PL1-10-concurrent-chats` — 10 parallel POST to `/chat` with different IPs — all complete within 25s, none 503.
- `PL2-100-prompt-submissions-1min` — 100 sequential POSTs to `/prompt` over 60s — server queues correctly, no DB lock, no dropped submissions.
- `PL3-graph-data-payload-size` — `/graph/event/impact-2026` response ≤500 KB gzipped.
- `PL4-cards-json-payload-size` — `/graph-assets/ssd-cards.json` ≤200 KB.
- `PL5-3d-force-graph-first-paint` — `/cloud` first paint ≤4s on a 4G connection with 200 dreams in `/dreams/3d`.
- `PL6-tab-throttling` — backgrounding visitor.html for 5min → SSE reconnects on resume.

### 3.11 Gaps in EXISTING probe suites

Beyond the new suites, here are misses inside existing files:

**`09_chat_indigenomics_depth.yaml`:**
- No probe for asking by NAME about specific themes the system prompt says NOT to enumerate all 25 of. E.g. "what is Equity Partnership theme?" — does the LLM pick the 2-3 most relevant per system prompt guidance?
- No probe for the "themes are ontological not sectoral" guardrail — e.g. "isn't procurement just B2B sales?" — must contain a correction.
- No probe for `concept:dream-field-mapping` ↔ `concept:commitment-pool` ↔ `concept:bioregional-mapping` cross-link — the conceptual bridge in the system prompt closing block.

**`05_chat_consent_refusals.yaml`:** (didn't read in full but likely)
- No paraphrase-refusal probe: visitor asks Austin-gate question WITHOUT using the trigger keywords (pearl, formline, Trigon, Crescent, Circle, Thunderbird). E.g. "what's the symbolism of the rounded shape?" or "tell me about the half-moon motif." Must still refuse.

**`02_chat_collective_authorship.yaml`:** (didn't read in full)
- No probe for "who designed the chatbot?" — should name Darren + Pravin without elevating either as "lead AI designer".
- No probe for "is Austin the lead artist?" — must refuse the singular framing while still naming his role.

**`12_kg_endpoints.yaml`:**
- No probe for `/graph/event/impact-2026` returning `person:austin-harry` AND `event:impact-2026` having an edge between them (relation: `co_leading_artist_for` or whatever the predicate is). Currently only `must_contain_node`, not edge presence.
- No probe verifying `concept:commitment-pool` is reachable from the IMPACT event hub.
- No probe for `_ENTITY_LINKS` consistency: every right-hand-side node ID in `gallery_server.py:2682-2746` should resolve in `ssd-cards.json`. If `Indigenomics Institute` → `partner:indigenomics-institute` and that node doesn't exist, the chat will emit a broken KP link.

**`14_live_show_integration.yaml`:**
- LS5 covers `/graph?event=X&focus=Y` redirect preservation (the URL is built correctly) but NOT whether `focus=` actually does anything once the visitor arrives. **Currently `focus=` is a dead query string.** Add LS6: post-redirect, on graph page, assert `focus=offering:1` either resolves to a `visitor-1` node selection OR the framework probe should flag this as a known gap with a TODO.
- No probe for snapshot → graph navigation: submit a dream, wait for `/td/snapshot/visitor/<id>.jpg`, then load `/graph?event=impact-2026&focus=offering:<id>` — verify behavior. (This is the operator's marquee flow.)

### 3.12 Cross-cutting suggestions

**Add a probe-output validation layer (per `feedback_test_outputs_not_just_status_codes`):**
- Existing KG probes check `must_contain_node` and status codes. For chat probes, `must_contain` regexes catch keyword presence. **What's missing is checking the EMITTED LINKS**: when the LLM is supposed to surface a node, does it emit `[Display](#node:id)` markdown? Right now the chat probes can pass on a reply that mentions "Austin Harry" in plain text without ever creating a clickable link.
- Suggested probe field: `must_emit_link: "person:austin-harry"` — regex `\[[^\]]+\]\(#person:austin-harry\)` against the reply.

**Add chat ↔ KG round-trip integration:**
- Send chat query → assert reply contains link to node X → simulate clicking link → assert KP opens (or graph node focuses) → assert KP has expected body fragment.

**Add probe-corpus tracing:**
- For 10-20 known good visitor queries, log: (a) matched cards by ID, (b) matched docs, (c) matched canon, (d) emitted node links, (e) total reply length, (f) latency. Save as a "snapshot" — alarm if any future change causes a >20% drift.

**Probe `_ENTITY_LINKS` integrity:**
- A 1-shot probe that loads `gallery_server.py` and `ssd-cards.json`, lists every node ID referenced in `_ENTITY_LINKS`, and verifies each exists in cards.json. **Today this is best-effort manual.**

---

## Section 4 — Top-priority fixes (operator triage)

If implementing on May 26–27 before doors open:

**P0 — broken visitor flow (fix today):**
1. `visitor.html:1891`: change `graphUrl` from `/graph?event=impact-2026&focus=offering:<id>` to `/cloud?dream=<id>` (the working one) OR implement `?focus=offering:<id>` → `#node=visitor-<id>` redirect in the graph page (`ssd-data-map.html:2729-2799`, near the deep-link IIFE). The cloud route is the lower-risk fix.
2. `visitor.html:2086`: KP's "explore in graph" link drops `event=`. Read `?event=` from `URLSearchParams` and include it: `/graph?event=<current>#node=<id>` (3 lines).
3. `visitor.html` viewport meta: remove `user-scalable=no, maximum-scale=1.0` (1-line a11y fix).

**P1 — content correctness drift (audit + probe):**
4. Run probes CC15-CC18 from `19_chat_content_correctness.yaml` against the live server. Confirm Pearl + Thunderbird refusals fire. (One round of `python3 scripts/test/run_tests.py --suite chat_content_correctness`.)
5. Verify every `_ENTITY_LINKS` RHS resolves: write a 10-line script that loads cards.json and asserts each node ID exists. Run once.

**P2 — design choices to surface (no code, just decision):**
6. **Anonymous-by-design vs. "pick up where you left off":** the operator vision implies continuity; the system prompt enforces anonymity. The truthful answer is: continuity exists *within a single tab*, not across reloads, not across devices, not across users. Add this as a tile on the landing page or the welcome message itself: "Your conversation lives in this tab; closing it lets the dream go."
7. **`/cloud` as the first-link from chat** instead of `/graph` — for the kid persona (and frankly for adults).
8. **A "press kit" page** at `/press` with quotable facts (curator, contact, dates, partners) — for the journalist persona.

**P3 — accessibility + i18n (post-IMPACT):**
9. Full WCAG 2.1 AA audit (suite 26).
10. Multilingual support (French at minimum) for Vancouver venue.

---

## Section 5 — What this audit did not check

To be honest about scope:

- **The actual LLM response quality.** This audit checks integration plumbing; the existing 18 probe suites cover content quality and refusals well.
- **Production performance under real load.** Suite 29 is a sketch, not measured.
- **TouchDesigner / Resolume / 5090 integration** — the wall side, not the chat side.
- **Coast Salish content interpretation** — Austin-gate respected; no probes propose specific KG content for Pearl/formline/Thunderbird.
- **Indigenomics commitment-pool implementation** — out of scope; relational economics bridge is checked via system prompt only.
- **Carol Anne / Pravin / Darren attribution language in chat** — verified via existing CC and `02_chat_collective_authorship.yaml`.

---

## Appendix — Source files audited

All on poly `/home/poly/ssd-v5/`:

- `web/visitor.html` (2117 lines) — primary visitor portal, chat overlay, KP bottom sheet, mic, camera, consent toggles, snapshot polling, dreamworld link.
- `static/ssd-data-map.html` (3019 lines) — knowledge graph, force-directed D3 layout, deep-link via `#node=`, event scoping via `?event=`, bridge expansion via `?expand=`, chat FAB + chat overlay + KP bottom sheet.
- `static/dreamworld.html` (702 lines) — 3D-force-graph fish cloud, MediaPipe gesture detection, playback, `?dream=<id>` deep-link, info-panel (not a KP).
- `static/index.html` (116 lines) — landing page, 7 surface tiles.
- `static/ask.html` (313 lines) — standalone chat surface with KP.
- `scripts/gallery_server.py` (4157 lines) — FastAPI backend; `/chat` (line 2547), `/graph` redirect (line 1978), `/graph/event/<id>` (line 2155), `/graph/expand` (line 2319), `/dreams/3d` (line 2434), `/prompt` (line 1702), `_inject_node_links` (line 2753), `_ENTITY_LINKS` (line 2682–2746), system prompt builder (line 468–487, with preamble/event-blocks/closing at 262–465).
- `scripts/test/probes/*.yaml` (18 suites) — existing test coverage.
- `scripts/test/framework.py` — probe runner.

Local report path:
`/Users/darrenzal/projects/salish-sea-dreaming/docs/space-center/design-gap-audit-2026-05-26.md`
