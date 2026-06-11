# IMPACT 2026 Sponsors + YonEarth Chat↔KP Integration Patterns

**Date:** 2026-05-26 (read in 2026-05-25 session)
**Author:** Claude (autonomous research sub-agent)
**Status:** Read-only research — proposes additions to `static/ssd-cards.json`, `scripts/gallery_server.py::_ENTITY_LINKS`, and the chat UI in `static/ssd-data-map.html`. Does NOT edit production files.

**Companion doc:** `docs/space-center/chatbot-gap-audit-2026-05-26.md` — that doc already proposed `partner:telus` + `partner:indigenomics-institute` cards. This doc EXTENDS that proposal with the live sponsor list from the IMPACT event page and adds an integration design for chat-inside-the-knowledge-panel.

---

## Investigation 1 — IMPACT 2026 Sponsor List (URGENT for May 27 show)

### Source

`https://indigenomics.com/events/impact/` — fetched via WebFetch 2026-05-25. Page event title: *Indigenomics IMPACT 2026* — May 27–28, 2026 — H.R. MacMillan Space Centre, Vancouver, BC.

Speaker list, schedule, and pricing are loaded dynamically (JavaScript) and were not in the static HTML; sponsor logos ARE in static HTML (under tiered headings with image alt-text + filenames). The reception-partner row had two additional logos whose alt-text was not legible — flagged below as "needs operator confirmation."

### Sponsor list (verbatim from the event page)

| Name | Tier | Logo filename (from page) | Notes |
|------|------|---------------------------|-------|
| **Vancity** | Platinum Multi-Year Sponsor | `vancity-logo.png` | Member-owned credit union, Vancouver |
| **TELUS** | Platinum Multi-Year Sponsor | `Telus-Logo.png` | Already known to SSD via H200 compute partnership |
| **Earnscliffe** | Platinum Multi-Year Sponsor | `earnscliffe_logo_CMYK_EN.png` | Public affairs / strategy firm |
| **Scotiabank** | Platinum Multi-Year Sponsor | `scotiabank-logo-red-desktop-200px.png` | Canadian bank |
| **BCLC** | Silver | `bclc-logo.jpeg` | British Columbia Lottery Corporation |
| **H.R. MacMillan Space Centre** | Event Partner | `spacecentre-color-transparent-web.png` | Venue host |
| **Kilala** | Logistics Partner | `kilala-150x150.png` | Logistics support — type/firm not identified from page |
| **MOVE37XR** | Creative Partner | `MOVE37XR-Logo-1.png` | Pravin Pillay's company — already a `person:prav-pillay` adjacent entity in SSD cards |
| **18OG** | Beverage Sponsor | `Asset18OGlogoreddetail-scaled.webp` | Beverage brand — needs operator verification on what "18OG" actually is |
| **MJ Coffee** | Coffee Sponsor | `mjcoffee-logo-round.webp` | Coffee provider |
| **NkMip Cellars** | Reception Partner | `NkMip-Cellars-logo.png` | Indigenous-owned winery, Osoyoos First Nation |
| **(unknown #1)** | Reception Partner | not extractable | Two additional reception-partner logos present but alt-text not legible from page HTML |
| **(unknown #2)** | Reception Partner | not extractable | " |

**Tier groupings the page uses:** *Platinum Multi-Year Sponsors* / *Silver* / *Event Partner* / *Logistics Partner* / *Creative Partner* / *Beverage Sponsor* / *Coffee Sponsor* / *Reception Partners*. There is no "Gold" tier visible.

### What changed vs the current chatbot answer

The current chatbot says *"only TELUS"* because that was the only sponsor mentioned in local Phase 2 source docs. The actual sponsor list above is what should ground the answer. Of these 11 named entities, **only TELUS is already in `ssd-cards.json`** (and even TELUS doesn't have a `partner:telus` card yet — see gap audit). H.R. MacMillan Space Centre exists as a vault entity but not as a chatbot card. MOVE37XR has no dedicated card (only Pravin Pillay's person card mentions it).

### Proposed cards for `static/ssd-cards.json`

Cards follow the existing schema (`title`, `body`, optional `url`, `tags`). Bodies are FACTUALLY GROUNDED — where I have only the event-page placement, the body says only that. No invented detail.

```json
"partner:vancity": {
  "title": "Vancity",
  "body": "Platinum Multi-Year Sponsor of Indigenomics IMPACT 2026. Vancity is a Vancouver-based member-owned credit union.",
  "url": "https://www.vancity.com/",
  "tags": ["partner", "sponsor", "impact-2026", "platinum"]
},

"partner:telus": {
  "title": "TELUS",
  "body": "Platinum Multi-Year Sponsor of Indigenomics IMPACT 2026. TELUS is also the compute partner for the Salish Sea Dreaming visual stack — H200 GPU access via the TELUS Sovereign AI Factory, coordinated through the Indigenomics AI platform.",
  "url": "https://www.telus.com/",
  "tags": ["partner", "sponsor", "impact-2026", "platinum", "compute"]
},

"partner:earnscliffe": {
  "title": "Earnscliffe",
  "body": "Platinum Multi-Year Sponsor of Indigenomics IMPACT 2026. Earnscliffe Strategies is a Canadian public-affairs and strategy firm.",
  "url": "https://www.earnscliffe.ca/",
  "tags": ["partner", "sponsor", "impact-2026", "platinum"]
},

"partner:scotiabank": {
  "title": "Scotiabank",
  "body": "Platinum Multi-Year Sponsor of Indigenomics IMPACT 2026.",
  "url": "https://www.scotiabank.com/",
  "tags": ["partner", "sponsor", "impact-2026", "platinum"]
},

"partner:bclc": {
  "title": "BCLC",
  "body": "Silver sponsor of Indigenomics IMPACT 2026. BCLC is the British Columbia Lottery Corporation.",
  "url": "https://corporate.bclc.com/",
  "tags": ["partner", "sponsor", "impact-2026", "silver"]
},

"partner:hr-macmillan-space-centre": {
  "title": "H.R. MacMillan Space Centre",
  "body": "Event Partner and host venue for Indigenomics IMPACT 2026 (May 27–28, 2026). Located at 1100 Chestnut Street, Vancouver, BC. The Salish Sea Dreaming installation runs in the Hubble Space; the Living Intelligence cosmic-journey runs in the Planetarium dome.",
  "url": "https://www.spacecentre.ca/",
  "tags": ["partner", "venue", "impact-2026", "event-partner"]
},

"partner:kilala": {
  "title": "Kilala",
  "body": "Logistics Partner for Indigenomics IMPACT 2026.",
  "tags": ["partner", "sponsor", "impact-2026", "logistics"]
},

"partner:move37xr": {
  "title": "MOVE37XR",
  "body": "Creative Partner for Indigenomics IMPACT 2026. MOVE37XR is Pravin Pillay's creative studio, leading TouchDesigner, AI visualization, and immersive-media direction for the show.",
  "url": "https://www.move37xr.com/",
  "tags": ["partner", "sponsor", "impact-2026", "creative", "studio"]
},

"partner:18og": {
  "title": "18OG",
  "body": "Beverage Sponsor of Indigenomics IMPACT 2026.",
  "tags": ["partner", "sponsor", "impact-2026", "beverage"]
},

"partner:mj-coffee": {
  "title": "MJ Coffee",
  "body": "Coffee Sponsor of Indigenomics IMPACT 2026.",
  "tags": ["partner", "sponsor", "impact-2026", "coffee"]
},

"partner:nkmip-cellars": {
  "title": "NkMip Cellars",
  "body": "Reception Partner for Indigenomics IMPACT 2026. NkMip Cellars is an Indigenous-owned winery in Osoyoos, BC.",
  "url": "https://www.nkmipcellars.com/",
  "tags": ["partner", "sponsor", "impact-2026", "reception"]
},

"partner:indigenomics-institute": {
  "title": "Indigenomics Institute",
  "body": "Founding institution and organizer of Indigenomics IMPACT 2026. Led by Carol Anne Hilton. Frames the event around Indigenous economic power, immersive technology, and imagination.",
  "url": "https://indigenomics.com/",
  "tags": ["partner", "organizer", "impact-2026"]
}
```

**Note on body length:** Following the project memory rule (do not invent), most bodies are short. The four Platinum sponsors get one extra sentence of factual context drawn from the org's public identity (member-owned credit union, public-affairs firm, Canadian bank, etc.) — these are unambiguous facts about long-established Canadian institutions, not invented attributes. **18OG, MJ Coffee, and Kilala bodies are intentionally minimal** because I cannot confirm their identity from the event page alone and the source-harvest constraint says don't pad.

### Proposed additions to `_ENTITY_LINKS` (in `scripts/gallery_server.py` ~line 1772)

This dict is what enables the chatbot to auto-link sponsor mentions to KP cards. Add these entries:

```python
# Sponsor / partner auto-links (IMPACT 2026)
"Vancity": "partner:vancity",
"TELUS": "partner:telus",
"Telus": "partner:telus",
"Earnscliffe": "partner:earnscliffe",
"Earnscliffe Strategies": "partner:earnscliffe",
"Scotiabank": "partner:scotiabank",
"BCLC": "partner:bclc",
"British Columbia Lottery Corporation": "partner:bclc",
"H.R. MacMillan Space Centre": "partner:hr-macmillan-space-centre",
"HR MacMillan Space Centre": "partner:hr-macmillan-space-centre",
"Space Centre": "partner:hr-macmillan-space-centre",
"Kilala": "partner:kilala",
"MOVE37XR": "partner:move37xr",
"Move37XR": "partner:move37xr",
"18OG": "partner:18og",
"MJ Coffee": "partner:mj-coffee",
"NkMip Cellars": "partner:nkmip-cellars",
"Nk'Mip Cellars": "partner:nkmip-cellars",  # alternate apostrophe form
"Indigenomics Institute": "partner:indigenomics-institute",
"Indigenomics": "partner:indigenomics-institute",  # NB: ambiguous w/ Indigenomics AI — disambiguate downstream if needed
```

### Open items — operator to confirm before adding

1. **Two unnamed Reception Partners** — Operator should screenshot the page or pull image filenames from devtools and add cards for those before the show. Until confirmed, the chatbot should answer "Vancity, TELUS, Earnscliffe, Scotiabank, BCLC, plus event/logistics/creative/beverage/coffee/reception partners — the full list is on indigenomics.com/events/impact" rather than enumerate sponsors we haven't verified.
2. **18OG identity** — Could be a beverage brand, could be a partner code. Operator to verify.
3. **Kilala** — Same — needs operator verification on what kind of firm.
4. **Speakers & schedule** — Site loads these dynamically. Operator should grab the Whova registration link's program detail (the page references `whova.com` for registration) and provide a snapshot for a `program:impact-2026-day1` / `program:impact-2026-day2` card pair.
5. **System prompt update** — The chatbot's IMPACT system prompt should now reference the actual sponsor tier list ("Platinum: Vancity, TELUS, Earnscliffe, Scotiabank…") so it answers from posture rather than from card lookup alone. This is a separate edit from card additions; see `chatbot-gap-audit-2026-05-26.md` recommendation #2.

### Constraint check

- DO NOT invent sponsor attributes — bodies for unknown sponsors say only what the event page says
- DO NOT propose Coast Salish concept content — none of these cards reference Coast Salish content
- DO NOT edit production files — this doc proposes JSON/Python additions only

---

## Investigation 2 — YonEarth Chat↔KP Integration Patterns

### Repo located

`/Users/darrenzal/projects/yonearth-gaia-chatbot/` (existing chatbot the operator built and references frequently). Key files:

| File | Role | Lines |
|------|------|-------|
| `web/index.html` | Guide layout — split view: KG iframe on left, chat panel on right | 259 |
| `web/chat.js` | Chat input, message rendering, send loop | 2845 |
| `web/chat-kg-bridge.js` | The integration layer — entity extraction, postMessage to KG iframe, resource card requests | 932 |
| `web/entity-panel.js` | Collapsible right-side entity detail panel, fetches from KG data file | 157 |

### How YonEarth surfaces "Recommended Content" (the screenshot pattern)

Found in `web/index.html` lines 155–159:

```html
<!-- Episode Recommendations — re-anchored as last child by chat.js after each response -->
<div class="recommendations" id="recommendations" style="display: none;">
    <h3>Recommended Content</h3>
    <div class="recommendations-list" id="recommendationsList"></div>
</div>
```

Mechanism (from reading `chat.js` references + the comment): after each chat response, `chat.js` re-anchors the `#recommendations` element as the LAST child of `#chatMessages`, then populates `#recommendationsList` with cards. The data comes from the chat backend's RAG citations payload (similar to SSD's `sources` field on `/chat` response).

### How YonEarth links entities INSIDE chat replies (the real magic)

`chat-kg-bridge.js` does five things in order on every chat reply (see `processResponseWithLinks` at line 287):

1. **HTML-escape the reply text** (XSS protection).
2. **`addEpisodeBookLinks`** — regex-replace patterns like `Episode 120` or `Y on Earth` with clickable spans that navigate the KG iframe to that node. (Lines 136–166.)
3. **`addEntityLinksToResponse`** — for every entity name in the cached KG data (sorted longest-first to handle "Regenerative Agriculture" before "Agriculture"), regex-replace whole-word occurrences with `<span class="kg-entity-link" onclick="openResourceCard(...)">` (lines 94–128). Critically it tracks `linkedRanges` to avoid double-linking and checks "before" context to skip if already inside an HTML tag or anchor.
4. **`createCitationsSection`** — builds a References block at the bottom of the reply with episode/book icons that also navigate the KG (lines 241–279).
5. **`processResponse`** — separately calls the highlight system: extract entities → search KG cache → highlight matched nodes in the KG iframe via `postMessage` (lines 561–594).

### How YonEarth opens entity detail without losing chat state

`entity-panel.js` (157 lines, simpler than I expected):

- Adds a class `entity-panel-open` to `#mainContainer` (the chat panel) — CSS handles the slide-out animation
- Loads KG data once, caches it, looks up entity by EXACT name match (case-insensitive)
- Renders: type badge, description, outgoing/incoming relationships (each clickable to re-open panel for that entity), "View in Knowledge Graph" button that navigates the iframe
- Chat state is NEVER touched — the chat container, message history, and input all remain in place. The entity panel is purely additive overlay.

### Cross-frame communication

Uses **postMessage with same-origin enforcement** (see `SplitViewController.handleKGMessage` at line 818) for chat→KG and KG→chat resource-card requests. Also uses **BroadcastChannel** (`chat-kg-sync`) as a secondary path for iframe-to-iframe sync. The KG iframe sends `kgReady` when its data is loaded, `resourceSelected` when a node is clicked, and `resourceError` when a requested entity doesn't exist; the chat side has a 2s timeout (line 656) and shows an error card if no response.

### Layout

`web/index.html` line 61–65: split view is a flexbox parent (`.guide-split`) with two children — `.guide-kg-panel` (iframe) and `.guide-chat-panel` (chat). The mobile tab bar (lines 49–58) toggles between them on `<900px` viewports via body class `mobile-tab-chat` / `mobile-tab-explore`. On desktop both are always visible.

This is **conceptually different from SSD's current model**, where chat is a fullscreen takeover (`.chat-mode { position: fixed; inset: 0; z-index: 100 }`) that COVERS the graph. YonEarth's chat lives BESIDE the graph.

### How this maps to SSD's existing structure

SSD has the same building blocks already (just not wired together this way):

| Concept | YonEarth file:line | SSD file:line | Status |
|---------|-------------------|---------------|--------|
| Cached card data | `chat-kg-bridge.js:13` (`kgDataCache`) | `ssd-data-map.html:1874` (`cardData`) | Same — already cached on chat open |
| Entity → card resolution | `entity-panel.js:29` (`findEntity`) | `gallery_server.py:1772` (`_ENTITY_LINKS`) | SSD does this server-side at reply time; YonEarth does it client-side at render time |
| Inline entity link in chat reply | `chat-kg-bridge.js:107` (`<span class="kg-entity-link" onclick=...>`) | `ssd-data-map.html:1928` (`<a class="nav-pill" data-node=...>`) | Same idea, different markup |
| Click entity → open detail | `entity-panel.js:65` (`openEntityPanel`) | `ssd-data-map.html:2028` (`openKP`) | SSD's KP overlay is functionally equivalent to YonEarth's entity panel |
| Recommended content under chat | `index.html:155` (`.recommendations`) | not present | **Gap.** |
| Chat-while-graph-visible | `index.html:61` (split-view layout) | not present (chat is fullscreen) | **Gap.** |

### What the operator's screenshot is asking for

The "Ask Aaron's Guide" pattern with "Recommended Content" below the chat is a **persistent split-view + recommendations** layout. Two parts:

1. Chat lives BESIDE (or in a panel within) the knowledge surface, not as a fullscreen takeover.
2. After each reply, related entity/topic cards appear in a scrollable strip below the message area.

### Proposed integration options for SSD

For each option I describe (a) the change, (b) where it lands in the SSD codebase, (c) trade-offs.

#### Option A — Chat input bar persists at bottom of the KP overlay

**Change:** When the KP overlay opens for an entity, the chat input box (a copy of `#chatInput` + `#chatSend`) appears at the bottom of the KP card. Typing there sends a message to `/chat` pre-scoped to that entity (e.g. `Tell me more about <entity>` as system context).

**Lands in:**
- `static/ssd-data-map.html` lines 2028–2046 (`openKP` function) — append a chat-input div to `#kpContent`
- `static/ssd-data-map.html` lines 1979–2021 (`sendChat`) — add an optional entity-scope parameter; on send from KP, include it in the request payload
- `scripts/gallery_server.py` `/chat` endpoint — accept an optional `entity_scope` field and include it in the system context for that request

**Trade-offs:**
- ✅ Visitor doesn't lose KP context to talk about it
- ✅ Single chat thread (no fragmentation) — sends still go to main `chatHistory`
- ❌ Visually heavier — the KP card was designed to be a quick scan, not a chat surface
- ❌ Mobile-cramped — KP card is already small on phones

#### Option B — "Ask about this" button in KP returns focus to chat with pre-filled input

**Change:** Add a single button at the bottom of every KP card: *"Ask about [Entity Title]"*. Clicking it (1) closes the KP, (2) pre-fills `#chatInput` with `Tell me more about [Entity Title]`, (3) focuses the input but does NOT auto-send (per `feedback_voice_ux.md`: never auto-submit).

**Lands in:**
- `static/ssd-data-map.html` lines 2028–2046 (`openKP`) — append a button to `#kpContent` after the body paragraph
- The button's onclick: `closeKP(); chatInput.value = 'Tell me more about ' + card.title; chatInput.focus();`

**Trade-offs:**
- ✅ Smallest possible change — single button, single onclick handler
- ✅ Respects the existing fullscreen-chat affordance — visitor stays in chat mode
- ✅ No new endpoints, no payload changes
- ✅ Honors voice-UX rule (user verifies before send)
- ❌ Not the YonEarth-style integration the operator's screenshot showed — this is the "minimum viable bridge," not the "chat-in-knowledge-panel" UX
- ❌ Each entity question starts a new turn rather than continuing a conversation about that entity

#### Option C — "Recommended Content" strip below chat replies (true YonEarth pattern)

**Change:** After each `/chat` reply, render a horizontal scroll of 3–5 entity cards based on the reply's `sources` field (the `_node_links` injected by `_inject_node_links`) PLUS any entities the model didn't explicitly link but exist in `_ENTITY_LINKS` and appear in the reply text. Each card is a mini-version of the KP — title, badge, 1-line body, click → opens full KP.

**Lands in:**
- `static/ssd-data-map.html` add new CSS class `.chat-recommendations` (analog of YonEarth's `.recommendations`)
- `static/ssd-data-map.html` `addMsg('assistant', …)` (line 1940) — after appending the assistant message, look up `cardData[sourceId]` for each source and render mini-cards
- `scripts/gallery_server.py` `ChatResponse.sources` — already exists at line 1768; ensure it includes ALL entity matches, not just the ones the model wrote into the text. (Currently `sources` is populated from RAG retrieval, not from `_inject_node_links` output — may need a separate `entity_cards` field.)

**Trade-offs:**
- ✅ Closest to the operator's screenshot reference
- ✅ Surfaces related entities the visitor didn't know to ask about
- ✅ Reuses existing `cardData` cache + `openKP` function — no new data sources needed
- ❌ Largest change of the three — requires backend response shape change + new render path
- ❌ Risks information overload if every reply gets 5 cards stapled to it

#### Recommended sequence

1. **Phase 1 (ship for May 27):** Option B. One button per KP card, zero risk, takes ~20 min to implement, immediately addresses the "I clicked an entity in chat, now I want to keep asking about it" friction.
2. **Phase 2 (post-show iteration):** Option C. The true YonEarth-style recommendations strip — but only after the gap-audit's TELUS / Indigenomics / sponsor cards are in place so there's actually content to recommend.
3. **Skip Option A** unless the operator explicitly wants chat-in-KP. The friction it introduces (cramped mobile, KP no longer scannable) outweighs the convenience.

### Out of scope (deliberately not proposed)

- Persistent split-view chat-beside-graph layout — large rework of `ssd-data-map.html` (chat is currently fullscreen overlay); should be a separate plan
- Streaming markdown rendering — YonEarth uses it, SSD currently full-response renders; orthogonal
- Voice integration (Aaron TTS) — YonEarth has it, SSD doesn't and the operator hasn't asked for it on SSD
- Entity panel relationship graph (incoming/outgoing edges) — SSD's KP cards don't carry relationship data; would require KG export expansion

---

## Files referenced

- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-cards.json` — card data (where new sponsor cards go)
- `/Users/darrenzal/projects/salish-sea-dreaming/scripts/gallery_server.py` lines 1760–1827 — chat reply, `_ENTITY_LINKS`, `_inject_node_links`
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html` lines 1859–2050 — chat UI, send loop, `openKP` / `closeKP`
- `/Users/darrenzal/projects/salish-sea-dreaming/docs/space-center/chatbot-gap-audit-2026-05-26.md` — predecessor gap-audit doc proposing partner cards
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/index.html` — YonEarth guide layout (split view + recommendations)
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js` — YonEarth chat↔KG integration layer (the pattern to learn from)
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/entity-panel.js` — YonEarth entity detail panel
- `https://indigenomics.com/events/impact/` — IMPACT 2026 event page (source for sponsor list)
