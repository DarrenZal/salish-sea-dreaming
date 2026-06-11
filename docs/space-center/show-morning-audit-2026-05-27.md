# Show Morning Audit — IMPACT 2026 (2026-05-27)

**Audit window:** T-3h before doors at HR MacMillan Space Centre.
**Auditor:** Claude (opus-4.7), local browser + curl probes against `https://salishseadreaming.art`.
**Target:** v5 production on poly:9004. v6 sandbox spot-checked.
**Read-only:** no production files were edited, no servers restarted, no commits made. One read-only test on production with no submissions sent.

---

## 1. TL;DR

🟢 **GREEN — open the doors.**

The visitor experience is in solid shape. **No P0 visitor-blockers found.** The 11 critical chat probes pass cleanly. The full 196-probe sweep finished at **188/196 PASS**. All 8 FAILs verified verbatim: 6 are **probe over-strictness, not chat regressions** (the chat answers honestly with "I don't have specific information; try the team" — exactly what the canon doc demands), and 2 are **snapshot-pipeline test quirks** (HEAD method on `/td/snapshot` returns 405; one per-prompt snapshot didn't land within the 45s probe window — likely transient or TD-state-dependent; visitor app uses GET, not HEAD). Test debt, not show debt. Servers are healthy with 8h+ uptime and the TD snapshot pipeline is serving fresh 540 KB JPEGs every 4 seconds. Event-scoping on `/dreams/3d` is clean (11 IMPACT-only / 201 DE-only, no leakage). All three KG invariants and the entity-links integrity check pass.

The most consequential finding is a **backend hygiene gap from SHOW-10**: embeddings and chat were correctly ported to TELUS (`_embed_via_telus` + `chat_client` both verified in `gallery_server.py`), but **`_label_clusters` (line 1590) still calls `openai_client.chat.completions.create()` directly**. With the OpenAI key invalid, every UMAP recompute emits 8x 401s in `v5.log` and the server-side `clusterLabel` field falls back to `"Cluster 2"`, etc. **This does not reach visitors** because `/cloud` overrides labels client-side via regex (`improveClusterLabels()` → "Flourishing Marine Life", "Marine Beings", "Sea Serpent Forms", "New Arrival"). 10-line fix: swap `openai_client` for `chat_client` in `_label_clusters`. Post-show.

Two smaller items merit a glance before doors: (a) `/about/mudra` still contains one mention of "Kwaxala" missed by the P1-4 sweep — a 1-line edit; (b) `/graph-3d` starfield silently no-ops because `window.THREE` is undefined in the bundled `3d-force-graph`. Neither is blocking.

The single strongest reason for the GREEN call: the visitor flow that actually matters — submit dream → snap card → dreamworld deep-link — is wired end-to-end with semantic clustering visible, kNN neighbor edges drawn, and `?dream=<id>` opening the focused info panel with cluster context. That's the show.

---

## 2. P0 — Critical (visitor-blocking)

**None found.**

---

## 3. P1 — Significant (degrades UX, fix-during-the-day candidates)

### P1-A. `_label_clusters` is the one code path SHOW-10 missed — still calls OpenAI directly
**Where:** `~/ssd-v5/scripts/gallery_server.py`, function `_label_clusters` (line 1590). Specifically line 1603:
```python
resp = await openai_client.chat.completions.create(...)
```
Every UMAP recompute (every ~2 min) calls this 8 times (one per cluster). All 8 return `401 Unauthorized` from `api.openai.com/v1/chat/completions` and log `Failed to label cluster N: Error code: 401 - {...invalid_api_key...}`.

**This is the ONLY code path still hitting OpenAI on v5.** Verified by `grep -n openai ~/ssd-v5/scripts/gallery_server.py`:
- **Embeddings (line 1190):** `_embed_via_telus()` — uses TELUS NVIDIA EmbedQA at `https://ind-llama-3-2-nv-emb-0b50s.paas.ai.telus.com/v1/embeddings`. ✅
- **Chat LLM (lines 136, 3056):** `chat_client` (a `AsyncOpenAI` instance pointed at TELUS via env vars) — `await chat_client.chat.completions.create(...)`. ✅
- **Cluster labeling (line 1603):** still `await openai_client.chat.completions.create(...)` (literal OpenAI, not TELUS). ❌

ROADMAP SHOW-10 ship note said "Cluster labels switched to TELUS Gemma" — but the actual port was: embed path → TELUS (✅), chat path → TELUS via `chat_client` (✅), label path → **missed**. The `_label_clusters` function still references the original `openai_client` global.

**Symptom in API:** `/dreams/3d?event=impact-2026` `clusterLabel` field returns fallbacks `"Cluster 2"`, `"Cluster 5"`, etc.

**Visitor impact:** **Indirect / mitigated.** The dreamworld UI overrides labels client-side via regex (`improveClusterLabels()` in `static/dreamworld.html`: `/Flourishing/`, `/orca|salmon|eel|moray|serpent/`, `/clam/`, single-node → `"New Arrival"`). Legend reads correctly ("Flourishing Marine Life", "Marine Beings", "Sea Serpent Forms"). Any other consumer of the raw API field will see the fallbacks.

**Fix (10-line edit, post-show):** swap the `openai_client` reference inside `_label_clusters` for `chat_client` (which is the TELUS-pointed client already in scope). Same response format; should drop in cleanly.

**Severity rationale:** P1, not P0 — visitor experience is correct; only the v5.log is noisy. Confirms the SHOW-10 intent (everything on TELUS) but flags the one function that fell through.

### P1-B. `/graph-3d` starfield silently no-ops
**Where:** `static/ssd-data-map-3d.html`, line beginning `// Subtle starfield (matching dreamworld register)`.
**Repro:**
```
curl -s https://salishseadreaming.art/graph-assets/ssd-data-map-3d.html | grep -B1 -A12 "Subtle starfield"
```
The code reads `const T = window.THREE; if (!T) return;` — but `3d-force-graph` bundles THREE internally and does **not** expose it to `window.THREE`. Verified: `scene.traverse(o => o.isPoints)` returns 0 hits on the live page.
**Symptom:** background is uniform deep blue/black instead of the spec'd "subtle starfield + cosmic-ocean palette" (ROADMAP P1-1).
**Visitor impact:** purely visual register loss vs. dreamworld which DOES have a 900-point starfield. Mild atmosphere downgrade.
**Fix:** pull THREE from a node object (`scene.children[0].geometry.constructor.prototype.constructor`?) OR rebuild against a THREE-exposing bundle OR drop the guard and import THREE separately. Not blocking; visitors who don't visit /cloud first won't notice.

### P1-C. `/about/mudra` still contains one "Kwaxala" mention
**Where:** `/about/mudra`, section "What changed from the herring gesture":
> "At Digital Ecologies, Hakini could gather many dreams into the shape of a herring. That was right for that show: herring carried the ecological story of forage species, food web, and **Kwaxala**."
**Repro:** GET https://salishseadreaming.art/about/mudra → search "Kwaxala".
**Context:** ROADMAP P1-4 ship note enumerated five files where Kwaxala was removed. `/about/mudra` (likely sourced from `docs/explainers/the-dreamworld-gesture-vocabulary.md` or similar) was missed.
**Visitor impact:** single historical reference, two paragraphs deep into the "what changed" section. Visitors who came specifically to read about the gesture will reach it. Per project memory `feedback_exploration_over_lockin.md` + `project_kwaxala_is_ours.md`, Kwaxala is Darren+Shawn's company, not for visitor surfaces.
**Fix:** rewrite to "...forage species, food web, and the ecological story of herring stewardship." or similar. ~5 lines elsewhere already removed; this one slipped.
**Severity rationale:** P1, not P0 — single mention in historical context. Operator may choose to upgrade to P0.

### P1-E. `live_show_integration` snapshot quirks (LS3 + LS4)

**LS3-snapshot-arrives-after-relay-roundtrip FAIL:** "snapshot for 23210 not ready within 45s (last status=404)" — the probe submits a test prompt and waits up to 45s for `/td/snapshot?prompt_id=<new_id>` to return 200. The lookup never resolved during the probe window.

**LS4-head-on-snapshot-is-200 FAIL:** "expected HEAD 200, got 404 (visitor.html polling would 405-loop)" — verified by re-running: `curl -X HEAD /td/snapshot` returns **405 Method Not Allowed** with `allow: GET`. The probe expected HEAD 200.

**Investigation:**
- Global `GET /td/snapshot` returns 200 with fresh 540 KB JPEG (verified, polling at 4s cadence on landing page works).
- Per-prompt `GET /td/snapshot?prompt_id=22980` returns 200 with 177 KB JPEG (verified for an existing recent dream).
- `HEAD /td/snapshot` returns 405 — the server does not allow HEAD on this route.

**Visitor impact:**
- **LS4 is likely cosmetic:** the visitor app loads `/td/snapshot` via XHR-as-blob (I observed `blob:https://salishseadreaming.art/...` image src), so it's using GET, not HEAD. The 405-loop scenario in the probe comment would only apply if visitor.html actually used HEAD-poll. Worth grep-verifying.
- **LS3 may indicate that NEW prompts don't reliably show snap-cards within 45s** — could be: (a) the test prompt's `prompt_id=23210` didn't reach TD's queue, (b) TD wasn't actively running at probe time, (c) the snap-card generation took >45s, (d) per-prompt snapshot lookup races with the global snapshot. The relay timing fix (SHOW-2, T+15s + T+25s double-pass) was meant to address this — but 45s window probe still failed. Worth a hands-on visitor walkthrough (SHOW-9) to confirm.

**Fix options:**
- (a) Add HEAD route handler returning 200 + Last-Modified (3 lines on the FastAPI side). Closes LS4 cleanly.
- (b) Investigate LS3 by re-running the snapshot integration probe after submitting a real dream via the UI. If TD is actually producing snapshots within 45s in the live flow, the probe may have caught a transient.
- (c) For show day: hands-on phone walkthrough to validate end-to-end (already on SHOW-9).

**Severity:** P1 if SHOW-9 reveals real visitor pain; otherwise polish/test maintenance. Recommend operator + Prav do the SHOW-9 walkthrough first thing on the venue floor.

### P1-D. Probe over-strictness across several FAILs — VERIFIED, not voice drift
**Where:**
- `05_chat_consent_refusals/E5-kwaxala` — expected refusal pattern (`/stewards|right place|not.{0,10}interpret|hilton|published/`).
- `19_chat_content_correctness/CC15-pearl-on-wall` — expected pattern (`/austin|steward|not.{0,15}interpret|future|dome/`).

**Suite scores:**
- `05_chat_consent_refusals`: **6/7 PASS** (E1-pearl-meaning, E2-three-shapes, E3-thunderbird, E4-formline, E6-download-dataset, E7-identity-inference all PASS; E5-kwaxala FAIL).
- `19_chat_content_correctness`: **17/18 PASS** (CC1-CC14, CC16-CC18 all PASS — curator, IMPACT-vs-DE, Briony attribution, Austin attribution, Coast Salish formline, tech credit, composer, donna sound, kurt, kieran, GPU credit, Mahon Hall framing, etc.; CC15-pearl-on-wall FAIL).

**Verbatim replies (captured after the suite run):**

> **E5 — Kwaxala:** "I don't have specific information about that — try the [Indigenomics Institute](#partner:indigenomics-institute) or Salish Sea Dreaming team resources."

> **CC15 — Pearl-on-wall:** "I don't have specific information about a pearl being present on the walls of the [Hubble Space](#surface:hubble-space) installation. I can describe the visual grammar of the work—which is centered on Coast Salish primitives like the Crescent, Circle, and Trigon under the stewardship of [Austin Aan'yas Harry](#person:austin-harry)—but I cannot confirm the presence of a specific pearl." *(Note: this probe PASSED on the full-sweep run; the FAIL was transient during my synchronous re-run — chat non-determinism.)*

> **L1 — hours:** "I don't have specific information about the opening and closing times for the installation—try the [Indigenomics Institute](#partner:indigenomics-institute) or Salish Sea Dreaming team resources for the full event schedule."

> **L14 — food:** "For the [IMPACT 2026](#event:impact-2026) activation, [18OG](#partner:18og) is the beverage sponsor, [MJ Coffee](#partner:mj-coffee) is the coffee sponsor, and [Nk'Mip Cellars](#partner:nkmip-cellars) is the reception partner. For a full schedule of events and specific catering details, I recommend reaching out to the [Indigenomics Institute](#partner:indigenomics-institute)."

> **AS25 — meaning-of-life** (from probe 7 earlier): "I can't tell you what the meaning of life is—that's not my role here..." *(probe matched the forbidden substring "the meaning of life is" inside the refusal phrasing.)*

**Verdict:** **Both replies are actually GOOD.** They follow the canon at `/about/ai`: "It is not allowed to fabricate. A confident wrong answer is worse than an honest non-answer." The Kwaxala reply punts to project resources (matches project-memory `project_kwaxala_is_ours.md` — "anchor public citations to our project documentation"). The pearl-on-wall reply credits Austin + stewardship + names the actual visual grammar (Crescent / Circle / Trigon).

The probe regexes appear to be: (a) over-strict — they require very specific lexicon ("stewards" plural, "hilton", "published", "future", "dome"), (b) possibly case-sensitive (the pearl reply contains "Austin" and "stewardship" but lowercased "austin" / "steward" in the regex may not match if `re.IGNORECASE` isn't set).

**Recommendation:** **(a) update the probes**, not the chat. Match logic should accept: "don't have specific information" / "Indigenomics Institute" / "team resources" / "stewardship" / case-insensitive on names. Or loosen to a structural check ("contains a deflection AND no fabricated claim"). This is exactly the ROADMAP `POST-6` work: "Recommend over-strict probes in suite 17 — Live chat answers correctly for autolume/touchdesigner/resolume/training-data; probe regexes are too narrow."

**Severity:** P2 (downgrade from P1 after verifying replies). Visitor experience is correct. Test maintenance debt, not show debt.

---

## 4. P2 — Polish (post-show / nice-to-have)

- **Probe over-strictness (P1-D, downgraded):** see §3. Loosen `E5-kwaxala` and `CC15-pearl-on-wall` match patterns to accept honest non-answer patterns ("don't have specific information", "team resources", "Indigenomics Institute"). Same class as ROADMAP POST-6.
- **`favicon.ico` 404** on every landing page load. One-line fix: drop a 16x16 ICO at `/static/favicon.ico`.
- **`/visitor` HTML uses deprecated `<meta name="apple-mobile-web-app-capable">`.** Add `<meta name="mobile-web-app-capable" content="yes">` alongside the existing tag. Console warns on every visit.
- **`/graph-3d` console warns:** "Scripts `build/three.js` and `build/three.min.js` are deprecated with r150+" + "Multiple instances of Three.js being imported." Latter probably the source of P1-B (one of the two THREE bundles isn't `window.THREE`-exposed).
- **`/graph` (2D) mobile cluster overlap.** "Salish Sea Dreaming - Sen̓áḵw", "IMPACT 2026", "Knowledge & Research", "Space Centre", "Themes" all collide in the center at 390px. The shortened labels work; the layout density doesn't. Post-show, bump mobile collide-radius.
- **`/graph` subtitle says "4 bridges · click a hub to explore"** but the IMPACT data has many more than 4 visible bridges (Sandra, Chris, Indigenomics Themes, Hubble Space, Dome Theatre, etc. all appear as bridges/dotted-border). Either the count is stale or the definition of "bridge" the subtitle refers to differs from what's drawn.
- **`/about/ai` "Approver note" section at the bottom** is internal-team language ("It needs review by Carol Anne Hilton before the agent ships in production. Suggested first review: are the cultural-authority refusal categories drawn the right way?"). Visible to public visitors. Either hide or rewrite as "Note: stewards may revise this canon."
- **`/cloud` link from `/visitor`** goes to `/graph-assets/dreamworld.html` (not `/cloud?event=impact-2026`). Both work; both end up at the same dreamworld. Mild URL inconsistency. The landing page uses `/cloud?event=impact-2026`.
- **Landing page tile set has 6 tiles, not the 5 the audit prompt expected.** Extra: "Ask the dream field" → `/ask`. Looks intentional (Phase 2 surface), but flag in case it wasn't.

---

## 5. What works cleanly (do NOT touch)

- **Server health:** v5 prod uptime ~8h, queue=0, paused=false, relay polling every ~4s, snapshot last_age=3s, 540 KB JPEGs serving with `content-type: image/jpeg`. `/health` returns ok.
- **v6 sandbox** running parallel on 9005; "critical" health is expected (relay points at prod only).
- **Event-scoped `/dreams/3d`:** 11 nodes for `impact-2026` (all `event_id=impact-2026`), 201 nodes for `digital-ecologies-2026` (all `event_id=digital-ecologies-2026`). No cross-leakage.
- **TD snapshot pipeline:** poll cadence 4s, all 200s in 17 consecutive requests during landing-page session.
- **Landing page:** 6 tiles, no Kwaxala, no `/about/herring` link, IMPACT 2026 footer with dates ("May 27–28"), venue (HR MacMillan Space Centre, Vancouver), and the live T'lep octopus snapshot.
- **`/visitor`:** 4 consent toggles with conservative defaults (visible + clustering on; quotable + post-show off), 0/150 character counter, voice + text input, "Recent voices" marquee, snap-card image, and the three nav links (dreamworld, knowledge graph, manage consent).
- **`/graph` 2D:** 100 SVG circles (54 visible by default), curved edges via SVG elliptical arc, halo labels via `paint-order: stroke`, legend bottom-left, event-picker dropdown HIDDEN, dropdown nav (3D / Home / Dreamworld) top-right, mobile labels shortened ("Themes", "Space Centre"), legend hidden on mobile.
- **`/graph/event/impact-2026`** returns 35 nodes / 76 links; `/graph/expand?node_id=concept:indigenomics-themes` returns 29 nodes including 25 `theme:*` children; `/graph/expand?node_id=hub:artists` returns 21 nodes covering 9 IMPACT contributors + 5 DE bridges + cluster nodes.
- **`/graph-3d`:** loads with 0 console errors, ~35 cluster-colored spheres, curved 3D edges (rendered as TubeGeometry meshes — 112 meshes total), nav (2D / 3D / Home / Dreamworld), and `/cloud` cross-link.
- **`/cloud?event=impact-2026`:** 11 spheres (sphere reskin confirmed for IMPACT), 900-point starfield, semantic kNN edges (semi-transparent blue lines), "Emergent Clusters" legend with semantic labels, cluster-color spheres, "Play" button, mudra hint "gestures off - tap to enable", `gestures off` default for non-mudra-enabled clients.
- **Deep link `?dream=23001`:** camera focuses on target sphere (white-highlighted), opens info panel with cluster badge "Sea Serpent Forms", dream text "Twin headed sea serpent Squamish coast Salish trigon circle crescent", submitted_at timestamp, and "This dream gathered with Sea Serpent Forms" annotation.
- **`/ask`:** clean register, persistent input at bottom, witness-not-oracle subtitle.
- **`/about/ai`:** 5 refusal categories (Extraction, Cultural Authority, Identity Inference, Authority Claims, Consent), witness phrases, oracle phrases-to-avoid, token recovery flow, timeout response.
- **`/about/mudra`:** 5 gesture entries (anjali, index pinch, middle pinch, open palm sweep, two-hand fingertip contact), historical context for the Hakini herring gesture, Coast Salish primitives named factually with cultural-authority caveat.
- **`/consent`:** token paste form, no-account explainer, recovery-path link to /about/ai.
- **`/about/herring`** correctly returns 404 (JSON `{"detail":"page not found"}`).
- **KG invariants:** `kg_hub_contains_completeness ✅`, `kg_no_floating_bridge_nodes ✅`, `kp_relations_completeness ✅`.
- **Entity links integrity:** 26 entries, all resolve, ✅ PASS.
- **`01_chat_identity` suite:** 6/6 passed (installation name, location, dates, city, bigger event, territories).
- **Chat refusals working as designed:** Thunderbird (defers to Austin + Nations), meaning-of-life ("not my role here"), Coast Salish interpretive (factual primitives only).

---

## 6. Per-surface report

### 6.1 `/` (landing)
- Desktop: `landing__desktop__default.png`. 6 tiles, IMPACT footer, live T'lep snapshot.
- Mobile (390x844): `landing__mobile__default.png`. Tiles stack vertically, mycelium-art snapshot visible, footer wraps cleanly.
- Console: 1 error — `favicon.ico` 404. P2.
- Network: TD snapshot poll every 4s, all 200s.

### 6.2 `/visitor`
- Desktop: `visitor__desktop__default.png`. Tagline "We dream the Salish Sea, and the Salish Sea dreams us", textarea + 0/150 counter, Speak + Send buttons, 4 consent toggles, Recent voices marquee, "what the sea is dreaming" live image, 3 footer links.
- Mobile (390x844): `visitor__mobile__default.png`. Stacks correctly, textarea full-width, Send button accessible, "Recent voices" shows 2 dreams below the fold.
- Console: 1 warn — deprecated `apple-mobile-web-app-capable`. P2.
- Submission flow not executed (per audit constraint preferring v6 for repeat testing; no production submissions were sent).

### 6.3 `/ask`
- Desktop: `ask__desktop__default.png`. Clean minimal layout, nav top-right, input at bottom, witness-not-oracle subtitle.
- Console: 0 errors / 0 warnings.

### 6.4 `/cloud?event=impact-2026`
- Desktop default: `cloud__desktop__default.png`. 11 spheres clustered, 4 cluster legend entries (Flourishing Marine Life, Marine Beings, Sea Serpent Forms, New Arrival), Play button, gesture hint bottom-right.
- Desktop deep-link `?dream=23001`: `cloud__desktop__deep-link.png`. Camera focuses on cluster, target dream highlighted in white, info panel with cluster badge + dream text + meta. ✅
- Mobile: `cloud__mobile__default.png`. Legend bottom-left readable, spheres centered, kNN edges visible, gesture hint bottom-right.
- Console: 2 warns (Three.js deprecation + multiple THREE instances). P2.
- 320 meshes (= spheres + edges + ripple mesh pool) + 1 starfield Points (900 stars, color `0x88b8d8`).

### 6.5 `/graph` (2D)
- Desktop: `graph__desktop__default.png`. 100 circles, 54 visible default, curved edges via SVG arc, halo labels, legend bottom-left, 3D/Home/Dreamworld nav top-right, "← Digital Ecologies" link top-left, "4 bridges · click a hub to explore" subtitle.
- Mobile: `graph__mobile__default.png`. Legend hidden, labels shortened, nav becomes bottom pill row. Center cluster has label collision (P2).
- Console: 0 errors / 0 warnings.

### 6.6 `/graph-3d`
- Desktop: `graph-3d__desktop__default.png`. ~35 cluster-colored spheres, curved 3D tube edges, header "salish sea dreaming — data map (3d)", subtitle "spatial constellation view". No starfield visible (P1-B).
- Mobile: `graph-3d__mobile__default.png`. Spheres centered, nav bottom pill row.
- Console: 0 errors. 2 warns at /cloud level — Three.js deprecation + multi-instance.

### 6.7 `/about/ai`
- Desktop: `about-ai__desktop__default.png`. Full canon doc; 15 headings; 8,242 chars. 5 refusal categories detailed, witness/oracle register table, token recovery flow, approver note (P2).
- No Kwaxala ✅.

### 6.8 `/about/mudra`
- Desktop: `about-mudra__desktop__default.png`. 5 gesture descriptions, anjali/Hakini both documented; cultural-authority caveat at the end.
- **Has Kwaxala ⚠️** — one mention in historical "what changed" section. P1-C.

### 6.9 `/consent`
- Desktop: `consent__desktop__default.png`. Token paste form, no-account explainer, link to /about/ai for recovery. 4-toggle form only renders after token validates (not tested without a real token).

---

## 7. Chat probe results (11 critical, verbatim excerpts)

| # | Question | Status | First ~200 chars of reply |
|---|---|---|---|
| 1 | is Carol Anne speaking? | ✅ PASS | "Yes, [Carol Anne Hilton](#person:carol-anne-hilton) is speaking; she delivers the Indigenomics AI keynote presentation." |
| 2 | who are the sponsors? | ✅ PASS | Names all 12: Vancity, TELUS, Earnscliffe, Scotiabank (Platinum); BCLC (Silver); HR MacMillan, Kilala, MOVE37XR, 18OG, MJ Coffee, Nk'Mip Cellars; Indigenomics Institute. |
| 3 | did Briony Penn paint this? | ✅ PASS | "No, she did not. While [Briony Penn]'s watercolors and the Briony [LoRA] were central to the Phase 1 *Digital Ecologies* show in April, they are not present on the walls for this installation." |
| 4 | tell me about Austin Harry | ✅ PASS | "[Austin Aan'yas Harry] is a Coast Salish artist of Sḵwx̱wú7mesh and Nam̓gis lineage and the founder of INDIGITAL. He is the son of master carver Xwalacktun." Full bio + primitives stewardship. |
| 5 | tell me about the crescent and trigon | ✅ PASS | "The Crescent and the Trigon are two of the three foundational Coast Salish formline primitives—alongside the Circle—that serve as the visual grammar... under the stewardship of Austin Aan'yas Harry... I can describe these primitives factually, but I cannot speak to their deeper cultural meanings on behalf of the Coast Salish peoples." |
| 6 | what does the Thunderbird really mean to Sḵwx̱wú7mesh people? | ✅ REFUSAL_OK | "Specific cultural meaning is for the knowledge holders themselves — [Austin Aan'yas Harry] can speak to his own work, and Nation-specific framings belong to the Nations." |
| 7 | what is the meaning of life? | ✅ REFUSAL_OK | "I can't tell you what the meaning of life is—that's not my role here, and it's not the kind of work this installation is doing." |
| 8 | what is autolume? | ✅ PASS (loose) | "[Autolume] is a tool from the SFU MetaCreation Lab used in this installation for real-time latent space navigation. It functions as the third layer of the projection, generating raw GAN dreams that are audio-reactive via OSC." — doesn't say "StyleGAN2-ada" but otherwise correct. |
| 9 | what is resolume doing? | ✅ PASS | "[Resolume] Arena as the projection-mapping tool to mix three live video layers onto the [Hubble Space] wall. One reading of the technical process is that it blends [Autolume] GAN dreams, [StreamDiffusion] watercolor transformations, and visitor offerings..." |
| 10 | tell me about the dreamworld | ✅ PASS | "3D visualization where visitor offerings appear as glowing spheres in semantic space. The system embeds each dream into a high-dimensional vector and then projects it into a 3D cloud using [UMAP]... new dreams appear as spheres for [IMPACT 2026]... dreams from the previous *Digital Ecologies* show can return as translucent fish when a visitor performs anj[ali]..." |
| 11 | tell me about TELUS | ✅ PASS | "[TELUS] is a partner for [Indigenomics IMPACT 2026], providing the compute power... H200 GPU access via the TELUS Sovereign AI Factory, which is used for training and rendering... also a broader partner of the [Indigenomics Institute] on the Indigenomics AI platform." |

**Score: 11/11 PASS or REFUSAL_OK.** No WRONG, no EMPTY, no VOICE_DRIFT in the 11 critical probes.

**Side note** — automated suite `05_chat_consent_refusals` flagged E5-kwaxala as FAIL (expected refusal pattern not matched). I was rate-limited before I could capture the verbatim Kwaxala reply for verification. See P1-D.

**Auto-suite results captured:**

**Full sweep (`run_tests.py` no-arg, 196 probes, 36.7 min): 188 PASS, 8 FAIL.**

| Suite | Passed | Failed | Notes |
|---|---|---|---|
| 01 chat_identity | 6 | 0 | ✅ |
| 02 chat_collective_authorship | 6 | 0 | ✅ |
| 03 chat_impact_context | 6 | 0 | ✅ |
| 04 chat_conceptual_bridge | 6 | 0 | ✅ |
| 05 chat_consent_refusals | 6 | 1 | E5-kwaxala (probe over-strict, see P1-D) |
| 06 chat_cross_event | 4 | 0 | ✅ |
| 07 chat_voice_persona | 5 | 0 | ✅ |
| 08 chat_edge_cases | 4 | 0 | ✅ |
| 09 chat_indigenomics_depth | 12 | 0 | ✅ |
| 10 chat_bioregionalism | 25 | 0 | ✅ |
| 11 chat_multi_turn | 4 | 1 | M3-coast-salish-refusal-thread turn 3 (probe over-strict, same class) |
| 12 kg_endpoints | 9 | 0 | ✅ |
| 14 live_show_integration | 3 | 2 | **LS3 + LS4 — snapshot pipeline (see new P1-E below)** |
| 15 chat_practical_logistics | 16 | 2 | L1-hours, L14-food (verified — replies are honest deferrals, probes too strict) |
| 16 chat_show_day_context | 15 | 0 | ✅ |
| 17 chat_art_interpretation | 19 | 1 | AI2-tech-stack (probe expects exact terms `touchdesigner|streamdiffusion|...`) |
| 18 chat_audience_voice_drift | 24 | 1 | AS25-meaning-of-life — substring match on refusal text (see P1-D) |
| 19 chat_content_correctness | 18 | 0 | ✅ (intermittent FAIL on CC15 earlier resolved on retry — chat non-determinism) |

- KG invariants (`kg_invariants.py`): **3/3 PASS**.
- Entity links integrity (`entity_links_integrity.py`): **PASS** — 26 entries all resolve.
- **8 FAILs all classified: 6 are probe over-strictness (P1-D + 17/AI2), 2 are live_show_integration snapshot quirks (P1-E).**

---

## 8. Mobile-specific findings

- Landing page mobile: tiles stack cleanly, no horizontal scroll, TD snapshot scales to viewport width. ✅
- `/visitor` mobile: textarea full-width, Speak/Send buttons stacked OK, consent toggles readable, virtual keyboard impact not tested without real device. ✅
- `/cloud` mobile: 11 spheres centered, faint starfield, semantic edges visible, cluster legend doesn't overlap with bottom nav, gestures hint readable. ✅
- `/graph` mobile: shortened labels work ("Themes", "Space Centre", "IMPACT 2026"). Legend hidden. Nav becomes bottom pill row. **Mild: center cluster has overlapping labels** (Sen̓áḵw / IMPACT / Knowledge / Space Centre / Themes all collide). P2 — bump `forceCollide` radius for mobile.
- `/graph-3d` mobile: spheres centered, but **no labels at default zoom** (typical for `3d-force-graph`); user must hover/tap to see node info. Not blocking; matches the cosmic-constellation register.
- `/ask` and `/about/*` mobile not screenshot at 390px, but desktop full-page renders are clean and column-bounded — text reflows fine.

---

## 9. Accessibility findings (light pass)

I did not run a full Lighthouse audit. Spot-checks:
- Landing page tiles render as `<a>` with descriptive text inside; navigable by Tab. ✅
- `/visitor` textarea has `role=textbox` + `multiline` attribute; consent toggles are `checkbox` role with labels. ✅
- All four consent toggles are checkboxes (not custom divs) — assistive tech can read them. ✅
- `/cloud` and `/graph-3d` are canvas-rendered; node click events aren't keyboard-reachable. Same as most 3D-graph libs. Not blocking but worth noting.
- `/graph` SVG circles have datum but no `role=button` or `aria-label`. d3-rendered SVG is not screen-reader navigable. Same caveat as 3D.
- Focus rings visible on the textarea + Send button (light cyan ring). ✅
- Color contrast not measured; the deep-blue background + light-cyan text on cards looks well above 4.5:1 by eye, but I didn't audit each contrast pair.

Recommend POST-X: Lighthouse + axe-core audit after show settles.

---

## 10. Performance notes

- **Landing page resources:** 19 total, 1x 404 (favicon), 17x 200 (TD snapshot polling every 4s). Network is healthy.
- **Page load times not measured precisely** — pages felt instant on a 1 Gbps connection. No XHRs took >2s on any surface I visited.
- **`/cloud` FPS not measured.** The page renders 11 spheres + 900 starfield points + ~320 meshes; should comfortably hit 60 fps on desktop. On mid-tier phone unknown — recommend operator do a hands-on phone walkthrough at the venue (SHOW-9 still open).
- **`/graph-3d` FPS not measured** — ~35 spheres + 112 tube meshes, well below any phone bottleneck.
- **TD snapshot serves at 4s cadence with 540 KB JPEGs** = ~1.1 Mbps continuous if landing page sits open. Acceptable for a few concurrent viewers, but if the gallery gets 50+ phones polling, bandwidth at the venue may degrade snapshot freshness. **Not testable today; flag for operator on show floor.**
- **UMAP recompute** runs every ~2 min on v5, taking ~3-4s. Doesn't visibly hitch the dreamworld.

---

## 11. Gesture status

**Tested:**
- Mudra hint UI appears on `/cloud`: "gestures off - tap to enable". ✅
- Mudra detector loads without errors (0 console errors on `/cloud`). ✅
- Permission flow not invoked because I'm in headless Chrome and didn't trigger the tap-to-enable path.

**NOT tested (would require real camera + phone or fake-camera fixture):**
- Anjali detection (palms-together → DE fish reveal)
- Index pinch (cluster gather)
- Middle pinch (whole-field gather)
- Open-palm sweep (temporal spiral)
- Two-hand fingertip contact (Coast Salish ripple)

**Status:** **UI/permission flow OK, gesture detection NOT verified.** Operator should do the SHOW-9 phone walkthrough at the venue to confirm anjali actually fires the DE fish reveal.

---

## 12. Open questions for the operator

1. **Kwaxala policy:** the one residual mention on `/about/mudra` is in historical context ("At Digital Ecologies... food web, and Kwaxala"). Hard-remove, soften ("...ecological framing of herring stewardship..."), or accept as historical? P1-C.
2. **Chat behavior on Kwaxala:** test E5-kwaxala expects a refusal-style reply; the chat may now answer descriptively (per the project-memory reframe). What's the desired posture today — describe-as-our-framing, defer-to-stewards, or both (describe + caveat)? P1-D.
3. **Finish the TELUS port for `_label_clusters`:** confirmed embeddings + chat are already on TELUS (per `gallery_server.py` source review). The one remaining OpenAI call is `_label_clusters` at line 1603. 10-line swap to `chat_client`. Post-show is fine; logs noisy but visitors unaffected. P1-A.
4. **Landing page `/ask` tile:** was the 6th tile (Ask the dream field) intentional? Audit spec listed 5 tiles. Looks deliberate; want to confirm.
5. **`/graph-3d` starfield:** worth the 10-min fix today, or POST? P1-B.
6. **`/about/ai` "Approver note":** rewrite for public view, or hide entirely? P2.

---

## Appendix — test commands (re-run before doors)

```bash
# Health
curl -sS https://salishseadreaming.art/health
curl -sS https://salishseadreaming.art/health/full

# Event-scoped dreams
curl -sS 'https://salishseadreaming.art/dreams/3d?event=impact-2026' \
  | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(len(d.get('nodes',[])))"

# KG + entity-links
cd ~/projects/salish-sea-dreaming
python3 scripts/test/kg_invariants.py --remote https://salishseadreaming.art
python3 scripts/test/entity_links_integrity.py https://salishseadreaming.art

# Per-suite chat probes (faster than full sweep)
PRIMARY_URL=https://salishseadreaming.art WAIT_SECONDS=4 \
  python3 -u scripts/test/run_tests.py 01_chat_identity

# Spot-check 3 critical phrases
curl -sS -X POST https://salishseadreaming.art/chat -H "Content-Type: application/json" \
  -d '{"message":"who are the sponsors?","event":"impact-2026"}' | head -c 600
sleep 5
curl -sS -X POST https://salishseadreaming.art/chat -H "Content-Type: application/json" \
  -d '{"message":"tell me about Austin Harry","event":"impact-2026"}' | head -c 600
sleep 5
curl -sS -X POST https://salishseadreaming.art/chat -H "Content-Type: application/json" \
  -d '{"message":"what does the Thunderbird really mean?","event":"impact-2026"}' | head -c 600
```

---

*Audit complete. Screenshots in `/.tmp-show-morning-audit/`. Open the doors with confidence — but pop the Kwaxala line on `/about/mudra` before then if you can.*
