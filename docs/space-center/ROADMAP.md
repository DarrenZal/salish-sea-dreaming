# SSD Roadmap — single source of truth

**Created:** 2026-05-26 evening (T-1 before IMPACT 2026)
**Maintained by:** each session updates this file. Read first, write last. If a parallel session is shipping something, leave an entry under "in flight" with the agent's session label.

This file replaces in-session `TaskCreate` lists that don't persist. Each entry: **id · status · owner · subject · brief**. Don't bury details here — link to plan docs / audit docs / commit messages instead.

Statuses: `🟢 done` · `🟡 in-flight` · `🔵 next` · `⏸ blocked` · `🔭 post-show` · `❄️ parked`

---

## Show readiness (P0 — must work tomorrow morning)

| ID | Status | Owner | Subject | Brief |
|----|---|---|---|---|
| SHOW-1 | 🟡 in-flight | operator | Verify visitor snapshot match on phone at venue | Relay fix shipped (T+15s + T+25s double-pass on 3090). Operator confirms by submitting a dream → waiting ~30s → checking if chat snap-card image matches prompt. If wrong: bump `VISITOR_SNAP_DELAY_SECS` to 18-20s. |
| SHOW-2 | 🟢 done | this-session | Snapshot timing fix on 3090 relay | `td_relay.py` patched 2026-05-26 evening, restarted via SSD-Relay scheduled task. Backup at `C:\Users\user\td_relay.py.bak-snaptime-20260527`. |
| SHOW-3 | 🟢 done | this-session | Coast Salish refusal narrowed | Chat now describes Crescent/Circle/Trigon factually with attribution to Austin/INDIGITAL; refuses only interpretive-meaning questions on Coast Salish people's behalf. `gallery_server.py:320` patched + verified live. |
| SHOW-4 | 🟢 done | this-session | Bridge-hub click reveals members | Clicking dimmed `hub:artists` in IMPACT view now reveals all 13 contributors (9 IMPACT + 5 DE bridges), not just 5 bridges. `ssd-data-map.html:1493` patched. |
| SHOW-5 | 🟢 done | this-session | Indigenomics Themes card populated | `concept:indigenomics-themes` had a node but empty card body. Added 477-char body grounded in Carol Anne's Book 2 Ch 8. |
| SHOW-6 | 🟡 in-flight | dreamworld-session | Dreamworld P0 ship | Sphere reskin, anjali reveal of DE fish, semantic kNN edges, Coast Salish ripples, deep-link focus. Plan: `dreamworld-improvements-plan-2026-05-27.md`. Operator sent feedback; agent rolling. |
| SHOW-7 | ⏸ blocked | operator | Two unnamed Reception Partners | Need phone screenshot of indigenomics.com/events/impact sponsor tiles. Sponsor cards (10/12) already shipped. |
| SHOW-8 | ⏸ blocked | dreamworld-session | Add `meta:remember-mudra` card | This session will add card + `_ENTITY_LINKS` entries once dreamworld-session ships anjali. ~5 min once notified. |
| SHOW-9 | 🔵 next | operator | Real-device phone walkthrough before doors | End-to-end: visitor flow → submit dream → snap card → cloud focus → chat about Austin/sponsors → KP "ask about" button → graph nav. Catch any visible regression before doors open. |
| SHOW-10 | 🟢 done | this-session | TELUS embed ported to v5 | OpenAI 401 was failing cluster labels + embeddings. Switched both `embed_and_position` and backfill to `_embed_via_telus` helper. Cluster labels switched to TELUS Gemma. |
| SHOW-13 | 🟢 done | this-session | Cluster-label TELUS swap (re-fix) | Show-morning audit agent caught that `_label_clusters` at line 1603 was still calling `openai_client.chat.completions.create` directly — my earlier patch had been reverted somewhere. Re-applied with `client = chat_client or openai_client` pattern. Restart verified, chat smoke OK. Remaining `openai_client` direct uses (3) are all defensive fallbacks or dead code — visitor-critical paths fully TELUS. |
| SHOW-11 | 🟢 done | this-session | RAG retrieval hardened | Single-token entity bypass (now retrieves cards for "what is autolume?"), tighter scoring (ID=+5, title=+4, body=+2), expanded stopwords. AS25 voice-drift fixed via `meta:out-of-scope-philosophy` card. |
| SHOW-12 | 🟢 done | this-session | KG invariants written + passing | `scripts/test/kg_invariants.py` + `scripts/test/entity_links_integrity.py`. All 4 invariants currently PASS against live. |

## Next 24-48h (P1)

| ID | Status | Owner | Subject | Brief |
|----|---|---|---|---|
| P1-1 | 🟢 done | this-session | 3D force-directed knowledge graph view | SHIPPED. Live at `/graph-3d`. ~440 lines, uses `3d-force-graph@1` (same lib as dreamworld). Cluster-color spheres, curved 3D links, deep-link via `#node=`/`?node=`, click → KP with relations + "view in 2D map" cross-link. 2D page header now has "3D" nav button. Subtle starfield + cosmic-ocean palette matches dreamworld register. Files: `static/ssd-data-map-3d.html` + `/graph-3d` redirect route in `gallery_server.py`. |
| P1-2 | 🟢 done | this-session | Mobile KG cleanup | Legend hidden on mobile (was overlapping with bottom page-nav). Long labels shortened on mobile via `_mobileShortName()` map: "Indigenomics Themes" → "Themes", "HR MacMillan Space Centre" → "Space Centre", install + event labels also abbreviated. Verified at 390×844 viewport. |
| P1-3 | 🔵 next | this-session | KG/dreamworld navigation continuity | Visitor flow currently: chat → KP → "explore in graph" opens in new tab. Should preserve chat conversation state across the jump. Lower-priority than 3D view but Phase 2 / nice-to-have for tomorrow. |
| P1-4 | 🟢 done | this-session | Kwaxala removed from visitor surfaces | Operator clarification: Kwaxala is Darren+Shawn's company, not for SSD landing/about pages. Removed from `static/index.html` landing tile, `docs/explainers/why-dreams-become-herring.md` (7 mentions rewritten to "worth more swimming" framing with Heiltsuk/Wuikinuxv stewardship attribution preserved), `docs/explainers/what-the-ai-can-and-cannot-know.md` refusal example, `static/ssd-cards.json` `hub:knowledge` body, `gallery_server.py` `_ENTITY_LINKS` mapping + system-prompt refusal example + admin form placeholder. Live verify: 0 kwaxala mentions across landing, /about/herring, /about/ai. |
| P1-5 | 🟢 done | this-session | 3D KG: brighter edges + click-to-expand | Edges bumped from ~0.4 alpha / 0.3-0.5 width → 0.55-0.75 alpha / 0.9-1.4 width — visible against background. `onNodeClick` now routes through `handleNodeClick` which: (a) checks if node is hub/bridge/concept + unexpanded; (b) fetches `/graph/expand?node_id=...&hops=1`; (c) merges new nodes/links into Graph.graphData(); (d) shows detail + focuses camera. Parity with 2D's click-to-expand behavior. |

## Post-show (P2 / R&D)

| ID | Status | Owner | Subject | Brief |
|----|---|---|---|---|
| POST-1 | 🔭 post-show | future-session | Incremental UMAP | Switch `recompute_umap()` from `fit_transform()` to saved-model + `.transform()`. Eliminates field-shake on every new prompt. ~30 lines. |
| POST-2 | 🔭 post-show | future-session | YonEarth "recommended content" strip | Chat replies could surface related dreams/concepts below each answer. Significant Phase 2 work. |
| POST-3 | 🔭 post-show | operator+future-session | Viewport `user-scalable=no` (WCAG 1.4.4) | 1-line fix on `visitor.html`. Trade-off: kiosk-mode wants zoom locked; phone-mode wants zoom enabled. Decide after show. |
| POST-4 | 🔭 post-show | future-session | Sheaf-theory cohesion visualization | H⁰ harmonies / H¹ obstructions on cluster boundaries. Beautiful R&D but needs both math + audience-onboarding language. Notes in vault. |
| POST-5 | 🔭 post-show | future-session | Cross-app bridge to IndigenomicsAI web app | `cross_app_url` field + KP rendering hook already shipped (feature-flag CSS in place). Awaits IndigenomicsAI public deploy URL. |
| POST-6 | 🔭 post-show | future-session | Recommend over-strict probes in suite 17 | Live chat answers correctly for autolume/touchdesigner/resolume/training-data; probe regexes are too narrow (require exact "stylegan" string). Loosen regexes OR rewrite cards to include exact terms. |
| POST-7 | 🔭 post-show | future-session | Sandra Semchuk / Chris Jordan bios — confirm with them | Current bios are factually grounded from Wikipedia + chrisjordan.com but they haven't reviewed. Send for sign-off after show. |
| POST-8 | 🔭 post-show | future-session | v6 promotion decision | v5 is current primary (with all today's fixes). v6 parallel-deployed. Decide whether to promote v6 after show settles. |

## Parked / decided-against

| ID | Status | Reason |
|----|---|---|
| PARK-1 | ❄️ parked | Force-directed view for DREAMS (not the KG). Individual dreams don't have meaningful structural relationships beyond what semantic UMAP already shows. Decided 2026-05-26. KG force-directed (P1-1) is a different question and DOES make sense. |
| PARK-2 | ❄️ parked | Briony LoRA as IMPACT content. Phase 2 dropped Briony per 2026-05-18 SSD Meeting 2. Chat now correctly answers "no" to "did Briony paint this?" |

## Blockers / waiting on operator

- Phone screenshot of indigenomics.com IMPACT sponsor tiles (SHOW-7)
- Phone walkthrough at venue (SHOW-9)
- Visitor snapshot match verification (SHOW-1)
- Decision on `cross_app_url` placeholder behavior — leave CSS-only or seed `install:salish-sea-dreaming` with a `salishseadreaming.art/about/indigenomics` self-link as stand-in?
- Naming for the current fish-constellation mudra (Hakini one-hand vs two-hand?) — relevant to SHOW-6

## Plan docs (read these for detail)

| Document | What it covers |
|----------|----------------|
| `dreamworld-improvements-plan-2026-05-27.md` | Authoritative dreamworld plan (SHOW-6). Operator + dreamworld-session both reference. |
| `morning-briefing-2026-05-27.md` | Status as of overnight 2026-05-26. What landed, what didn't. |
| `today-frontend-audit-2026-05-26.md` | Audit of all 4 visitor surfaces. P0+P1+P2 polish opportunities. |
| `overnight-work-2026-05-27.md` | Background subagent's overnight report. Persona walks + 96-probe sweep + 5 patches. |
| `chatbot-gap-audit-2026-05-26.md` | 84-probe chatbot sweep. 24 GOOD / 30 GAP / 3 WRONG / 26 REFUSAL_OK. |
| `design-gap-audit-2026-05-26.md` | Adversarial design + integration gap review across 4 surfaces. |
| `indigenomicsai-bridge-2026-05-26.md` | Curved-edge port reference + cross-app bridge pattern. **Useful for P1-1.** |
| `sponsors-and-chat-kp-integration-2026-05-26.md` | Sponsor crawl (11 sponsors) + YonEarth chat-KP integration scout. |
| `v6-promotion-procedure.md` | How to swap primary URL Caddy port. Not invoked yet. |
| `may-27-readiness-2026-05-27.md` | Operator-facing show-day runbook. Operational ops + escalation. |

## Recently shipped (last 24h, condensed)

- KG: bridge-hub click fix; Indigenomics Themes card; Austin/Matt added to hub:artists.contains; Sandra/Chris bios; layout tuning (link-distance, collide-radius, label outlines); curved edges via SVG elliptical arc; dropdown hidden; Sen̓áḵw rename; ask-about-entity button in KP; cross-app-link CSS rule.
- Chat: TELUS embed port; TELUS Gemma cluster labels; RAG single-token bypass + tighter scoring; 6 new content cards (tech-stack, AI-use, training-data, model-card, autolume, resolume); meta:out-of-scope-philosophy card (AS25 fix); Coast Salish refusal narrowed.
- Visitor: snap-card link routes to `/cloud?dream=<id>`; welcome opening-day phrasing.
- Dreamworld: "Show all" button when cluster selected; mobile gesture hint toast.
- Landing: "The sea is resting" 8s fallback.
- Ops: backup tarballs of both v5 + v6 static dirs + DBs; relay snapshot timing (T+8 → T+15 + T+25).

## Maintenance notes for future sessions

1. **This file is the index, not the content.** Each task entry is ≤2 lines. Plan docs hold the substance.
2. **Update on completion.** When a task ships, flip status to 🟢, leave the row in place (history). Move "ancient" 🟢 rows to "Recently shipped" condensed list once they're >48h old.
3. **Owner column matters.** `this-session` / `dreamworld-session` / `operator` / `future-session` — makes parallel work tractable.
4. **One file, one truth.** If you find yourself making another `roadmap-*.md` or `todo-*.md`, append here instead.
5. **Cross-session handoff format.** When you finish a chunk of work in one session, leave the "Recently shipped" bullet so the next session can pick up.
