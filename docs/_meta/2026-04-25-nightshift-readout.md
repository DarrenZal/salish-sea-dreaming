# Nightshift Readout — 2026-04-25 03:00–04:30 PDT

What got done while you slept. Read this first thing in the morning (≤2 min).

---

## TL;DR

- **3 essays** ready for ingestion to salishseadreaming.art chat
- **1 unified TD callback** ready to paste (B-light + orientation + swim, all toggleable)
- **3 TD setup snippets** ready to paste (MediaPipe preflight, NDI Out, orientation params)
- **2 ops docs** ready (RESTART.md, prav-play-guide.md)
- **1 show-day timeline** with hour-by-hour
- **2 harness scripts** built by subagents (local_preview.sh, ingest_check.py)
- **1 critical finding** that requires a server-side patch tomorrow morning
- **0 deploys** — nothing pushed to poly, nothing committed to git, nothing changed in TD

---

## Critical finding — must address tomorrow

The chat backend at `salishseadreaming.art` has a **2-token gate** at
`gallery_server.py:400`:

```python
if len(tokens) < 2: return [], []
```

This means single-token queries like *"What is Kwaxala?"*, *"Why a herring?"*,
*"What is sympoiesis?"* **never trigger RAG** — they fall through to system-prompt
only. So even if we add a `concept:hakini-mudra` card and a 2KB doc-chunk on
sympoiesis, the chat will not surface them on the most natural visitor questions.

**Fix**: patch `gallery_server.py:400` to either:
- Lower threshold to 1 (most permissive)
- OR allow 1-token queries when the token is non-stopword and ≥4 chars (more
  conservative — preserves the "general questions skip RAG" intent)

The morning timeline includes this patch as Step 10:Branch B (10:00 AM). It's a
3-line change to `gallery_server.py`, gets scp'd alongside the JSONs, restart same
service.

This finding came from running `ingest_check.py` against the current prod corpus
with the 10 expected morning queries — 6 of 10 auto-skipped due to the gate.

---

## Files written tonight (full list with paths)

### Essays for ingestion
1. `docs/digital-ecologies/mudra-as-sympoiesis.md` — written earlier this evening; ~170 lines
2. `docs/digital-ecologies/mudra-relational-map.md` — written earlier this evening; ~230 lines
3. `docs/digital-ecologies/mudra-and-joint-commitment.md` — written tonight; ~280 lines; design trajectory framing (Stage 0–6); references Gilbert/Bratman/Tuomela/De Jaegher/Spore canon

### TD-side morning paste-ins
4. `scripts/dreamworld_callback/dream_positions_cb_morning.py` — full unified callback
   - Includes everything from FINAL_0114 + new B-light bilateral logic + per-fish orientation + swim wiggle
   - **All 3 new behaviors gated by toggles** stored on `/project1/salish_dreamworld`:
     - `hakini_bilateral` (default 0)
     - `orient_fish` (default 0)
     - `swim_wiggle` (default 0)
   - Defaults preserve current verified-working behavior
5. `scripts/td_setup/preflight_mediapipe.py` — bumps num_hands=4/num_faces=2, runs ~10s FPS gate (PASS if min ≥45)
6. `scripts/td_setup/wire_ndi_out.py` — creates `ndioutTOP` named `salish_dreamworld_mac`
7. `scripts/td_setup/wire_orientation_params.py` — sets `instancerx/y/z = 'rx'/'ry'/'rz'`

### Ops docs
8. `scripts/dreamworld_callback/RESTART.md` — copy-paste recovery snippets, target ≤60 sec
9. `docs/prav-play-guide.md` — 1-page how-to for Prav (NDI source, kill switches, what not to touch)
10. `docs/show-day-timeline.md` — full hour-by-hour for tomorrow

### Harness scripts (built by subagents)
11. `scripts/local_preview.sh` — boots `gallery_server.py` locally on port 9001 with sandbox `BASE_DIR` (symlink-based)
    - Caveat: requires Python venv at `/Users/darrenzal/projects/salish-sea-dreaming/venv`. Bootstrap command in script's error output:
      ```
      python3 -m venv venv && venv/bin/pip install fastapi 'uvicorn[standard]' python-osc aiosqlite sse-starlette python-dotenv openai
      ```
12. `scripts/ingest_check.py` + `scripts/sample_queries.txt` — JSON validator + keyword coverage report

### This document
13. `docs/_meta/2026-04-25-nightshift-readout.md` — what you're reading

---

## What's queued for morning execution

In execution order. The show-day-timeline.md has full detail; this is the
condensed call sheet:

| Time | Step | Owner |
|---|---|---|
| 08:00 | Read this readout + 3 essays | You |
| 08:30 | Open TD, run RESTART.md to bring up scene | You + TD |
| 08:45 | Paste `preflight_mediapipe.py` — gate decides B-light viability | You + TD |
| 09:00 | Paste `wire_ndi_out.py` | You + TD |
| 09:15 | Paste `dream_positions_cb_morning.py` content into callback DAT | You + TD |
| 09:30 | Paste `wire_orientation_params.py` | You + TD |
| 09:45 | Toggle each new behavior on, test, leave on if good | You + TD |
| 10:00 | Branch A: generate cards + chunks (Claude) — Branch B: patch gallery_server.py:400 | You + Claude |
| 10:30 | `local_preview.sh` + `ingest_check.py` — verify chat answers | You |
| 11:00 | Snapshot prod JSONs on poly + scp + restart + smoke test | You |
| 11:30 | Pre-fetch dreams snapshot for offline fallback | You |
| 11:45 | Re-checkpoint + git commit + push | You |
| 12:00 | Cold-start full cycle test, stopwatch RESTART.md | You |
| 12:30 | Pack (MacBook, charger, ethernet, Cat6, hub, HDMI, task light, cooling pad) | You |
| 13:00 | Travel | You |
| 14:00–17:00 | Venue setup with Prav, threshold tuning, NDI to Resolume, walk Prav through guide | You + Prav |
| 17:00 | Dress rehearsal | You + Prav |
| 19:00+ | Show | You + Prav |
| Late | Pack out, migrate to Prav's | You |

---

## What I did NOT do (and why)

- ❌ **Did not generate the actual entity cards / doc chunks** — you wanted morning
  eyes on the essay framing first before downstream summaries get baked. Branch A
  of step 10:00 handles this.
- ❌ **Did not modify `gallery_server.py`** — the 2-token gate patch is small, but
  it's a server-side production change. You should sign off before scp.
- ❌ **Did not touch poly** over SSH — no production changes overnight.
- ❌ **Did not commit or push to git** — staging is for the morning, after you've
  read the new docs and either approved or edited them.
- ❌ **Did not modify TD or any .toe / .tox files** — TD is force-quit per your
  earlier action; everything I built is *paste-ready text* that you'll apply
  in the morning when TD reopens.

---

## Things to think about while you sleep (no action needed)

1. **`hakini_bilateral` gracefully self-disables** when too many people are in
   frame, when face attribution is ambiguous, or when one hand is at the
   midline (x ∈ [0.45, 0.55]). It's designed to refuse uncertainty rather
   than fire incorrectly. The first time you test with 3+ people in frame, it
   should look identical to the toggle-off baseline.

2. **The morning callback file is a complete drop-in replacement** — pasting it
   doesn't merge or patch, it overwrites the existing callback DAT entirely.
   That's intentional: simpler than diffing.

3. **The asymmetric-fray visual is deliberately subtle** in this version — fish
   on the released side disperse first over ~3 seconds, fish on the holding
   side pause then slowly dissolve. No hard pop, no flash, no jarring visual.
   The Gilbertian-ness is in the *difference between two release patterns*,
   not in any single dramatic moment.

4. **`mudra-and-joint-commitment.md` describes a 6-stage trajectory** of which
   B-light is Stage 1. Stages 2–6 are the post-show roadmap. The doc explicitly
   says "we are at Stage 0; B-light intends to land Stage 1 behind a kill switch
   for the closing show." The living intelligence answers should follow this
   framing — never claim more than what's actually shipped.

5. **The chat-corpus changes are independent of all the TD changes.** If TD
   work goes sideways, the chat improvements still ship. If chat work goes
   sideways, the TD show still ships. Decoupled.

6. **The readout's "12:00 cold-start full cycle test" is the most important
   verification** — it proves the morning's recovery path actually works
   under stopwatch. If it fails, the rest of the day reads as "fix recovery,
   then ship A only."

---

## Total time spent on nightshift

Started: 03:08 PDT
Files written: 13
Approx wall time: ~85 minutes (within budget)

Sleep well. The fish are still swimming.
