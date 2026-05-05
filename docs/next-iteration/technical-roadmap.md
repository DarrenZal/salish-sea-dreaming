# Salish Sea Dreaming — Technical Roadmap (Post-Exhibition)

> Drafted 2026-05-04. Synthesizes deferred items from the project `CLAUDE.md` "What's Left" section, post-show meeting notes, and the auto-memory file. Five tracks; A and B block Indigenomics May; C/D/E target MOVE37XR Oct.

## Quick view

| Track | Focus | Blocks Indigenomics May? | Owner | Effort |
|---|---|---|---|---|
| **A** | Touring resilience | **Yes** (mostly) | Darren primary, Prav on-site | ~3–4 wk |
| **B** | Visitor memory / dreaming continuity | **Yes** (gallery-server changes) | Darren | ~1–2 wk |
| **C** | VVVV exploration ("learning buddies") | No | Darren + Prav, paired | ~2 wk spike |
| **D** | Indigenous collab tooling (Austin / Halact) | Partially | Darren + Austin | ongoing, gated by consent |
| **E** | Dreaming corpus evolution | No | Darren + TELUS access | post-Oct |

---

## Track A — Touring resilience

**Why:** every Phase 2 venue inherits the Mahon Hall failure modes unless we close them now. The `installation-archive/` snapshot preserves the Mahon Hall config, but a number of bugs and gaps surfaced over the run that should not travel.

| Item | Source | Blocks Indigenomics? | Effort | Notes |
|---|---|---|---|---|
| **Resolume Advanced Output remote automation** | 2026-04-16 meeting notes | Yes — display-remap recovery currently requires on-site Prav | ~1 wk | Two paths under research: Resolume REST API (newer), Windows COM API. Goal: kill the manual `Ctrl+Shift+A` recovery loop. AHK-based kick (`SSD-Resolume-Kick`) is the current workaround. |
| **WASAPI loopback rewrite of `gallery_audio.py`** | `project_3090_hardware_audio.md`; `CLAUDE.md` post-show backlog | No (cosmetic — silence detector is currently a no-op) | ~3 d | 3090 has no mic; current silence detector reads a non-existent input. Move to WASAPI loopback on the playback device. |
| **Reverse SSH tunnel watchdog hardening** | 2026-05-03 dev-mode-return session: poly tunnel was DOWN despite `SSD-SSH-Tunnel` showing Running | Yes — touring depends on remote access | ~2 d | Add a poly-side `clean_tunnel.sh` audit; investigate why the cron-clean was wiping the listener. WireGuard is the reliable fallback today. |
| **Visitor-app chat-mode bug** | `project_known_quirks_2026-04-21.md` | Optional | ~1 d | Non-blocking but visible. Diagnose root cause (separate from auto-heal). |
| **SD literal-food-prompt quirk** | `project_known_quirks_2026-04-21.md` | Optional | ~1 d | LLM filter false-negatives on food terms. Tune the moderation prompt. |
| **Display ID reassignment after Resolume restart** | observations 25168/25172/25176 | Yes | tied to Resolume automation above | Same root cause as Resolume Advanced Output — addressed by the same automation. |

**Acceptance:** the entire 3090 stack should self-heal across a power cycle plus a Windows Update without requiring on-site keystrokes.

---

## Track B — Visitor memory / dreaming continuity

**Why:** Prav's explicit ask 2026-04-14 — *"archive visitor prompts cumulatively to build installation 'dreaming memory' over time."* This is the conceptual precursor to the three-layer architecture (Brad agentic + Darren KOI + Shawn blockchain) and the simplest way to thread cross-venue continuity.

| Item | Effort | Notes |
|---|---|---|
| **Persistent prompt archive on poly** | ~2 d | Extend gallery server schema; preserve every accepted visitor prompt with timestamp, venue tag, and (optional) anonymized session ID. |
| **Most-co-dreamed surfacing layer** | ~3 d | Slow-cycling Resolume layer or side projection that shows top-N co-dreamed prompts as ambient text — "the installation's memory." |
| **Cross-venue tagging** | ~1 d | Each venue gets a tag (`mahon-2026-04`, `indigenomics-2026-05`, etc.). Memory persists across venues; visitors at MOVE37XR see Mahon's dreams continuing. |
| **Forward path: KOI ingest** | deferred | Visitor prompts as KOI episodes; entity extraction; "bioregional intelligence" layer. Don't build this now — keep the schema clean enough to ingest later. |

**Acceptance:** a visitor prompt at Indigenomics Impact appears in the memory display *and* in the Mahon Hall lineage.

---

## Track C — VVVV exploration ("learning buddies")

**Why:** Prav's 2026-04-22 proposal — learn VVVV together post-show. He's seen its hybrid visual/textual live-programming environment and wants to evaluate it as a TouchDesigner alternative or complement before committing the next venue's visual stack.

**Approach:** time-boxed spike, **2 weeks**, paired with Prav.

1. Pick **one** of the three TD scenes built 2026-04-23 (`salish_audio` mycelium, `salish_prisms` species cards, or `salish_dreamworld` live-fetch breathing) as the rebuild target. Recommend `salish_audio` — simplest, audio-reactive, direct compare on a known good baseline.
2. Rebuild in VVVV, scoring on:
   - Authoring ergonomics (paired-session feel)
   - Performance (fps at 1080p / 4K)
   - NDI / OSC integration (gallery-server compatibility)
   - StreamDiffusion / Autolume integration paths
   - Stability under 24-hour gallery loop
3. Decision gate at end of week 2: stay TD-only / go VVVV-only / dual-stack with NDI bridge.

**Out of scope:** rebuilding the visitor web app, gallery server, or auto-heal stack. Those stay where they are regardless of the VJ-tool choice.

---

## Track D — Indigenous collaboration tooling

**Why:** Austin (Coast Salish digital designer, see `austin-collab-brief.md`) and Halact + son (Squamish-territory collaborators for MOVE37XR per 2026-03-31) are the next collaborators. Tooling has to *follow* the cultural protocol conversation, not lead it.

| Item | Effort | Gating |
|---|---|---|
| **Cultural-lens overlay** — Austin's crests as togglable layer over iNat species deck | ~1 wk build, but **gated on Austin's explicit per-motif consent** | Don't build until consent map is in hand |
| **LoRA-or-not-LoRA decision for Austin's work** | conversation, not code | Default to img2img / IP-Adapter / direct compositing rather than fine-tune unless Austin explicitly opts in |
| **Halact integration for MOVE37XR** | TBD | Separate conversation Prav drives; not a Darren-direct workstream until intro happens |
| **Squamish Lil'wat Cultural Centre advisory** | comms, not engineering | Mirror the Marvel/Kabam precedent if Austin wants it |

**Anti-pattern to avoid:** training a LoRA on Austin's portfolio "as a draft to show him." Either it's consented, or it doesn't exist.

---

## Track E — Dreaming corpus evolution

**Why:** the fish model "dreams in dead fish" (per `project_gan_strategy.md`). The multi-species dreaming model is the long-term visual goal; the current 320 kimg base is licensed R&D-only and should not feed any public installation.

| Item | Effort | Notes |
|---|---|---|
| **Corpus rebalancing** | ~1 wk | Continue the post-March-25 QC pass; under-represented species need supplement scrapes. |
| **Retrain on TELUS H200** | ~2–4 h compute, weeks of prep | Only when corpus is balanced. Carol Anne has access. |
| **Post-show LoRA refinement** | ~1 wk | Briony LoRA strength calibration: does 0.45 hold up at large-scale projection? Question raised 2026-03-19, never answered. |
| **License audit** | ~2 d | Re-verify CC0 / CC BY / CC BY-SA only; CC BY-NC stays excluded. Refresh `training-data/licenses-collaborators.md`. |

**Out of scope here:** any new species expansion. Decide what to train *with* before scraping more.

---

## Sequencing

```
Today (2026-05-04)
├── Track A (touring resilience) — start now, ~3–4 weeks
│   └── Resolume automation, tunnel hardening, WASAPI rewrite
├── Track B (visitor memory) — start in parallel, ~1–2 weeks
│   └── poly schema + Resolume memory layer
├── Indigenomics Impact (May) — Tracks A + B should be in place
├── Track C (VVVV spike) — start after Indigenomics, ~2 weeks
├── Track D (Indigenous collab) — gated on Austin's consent map
│   └── Build only what Austin explicitly green-lights
├── MOVE37XR Squamish (Oct) — Tracks A/B/C/D land here
└── Track E (corpus evolution) — post-MOVE37XR, into 2027
```

## Risks

- **Resolume automation false start.** REST API may not cover Advanced Output remap; if so, fall back to COM, then to AHK kick. Don't burn more than 1 week before deciding.
- **Cultural-protocol scope creep.** Track D has to stay disciplined: build only what's explicitly consented, never on speculation.
- **VVVV rabbit hole.** 2-week spike is firm; if VVVV looks promising at week 2, the *decision* moves forward — the *full migration* doesn't.
- **Corpus retraining time-and-attention sink.** Track E is real but post-Oct. Don't let it bleed into pre-MOVE37XR runway.

## Out of scope

- Any reach-outs to Austin / Halact / Carol Anne (Prav drives those).
- Re-enabling installation mode on the 3090 (Prav's call).
- Brad's agentic engine / Shawn's blockchain memory layer — those are Phase 2 architectural questions for the venue strategy, not engineering tasks here.
- New Briony LoRA training. Existing LoRA holds.
