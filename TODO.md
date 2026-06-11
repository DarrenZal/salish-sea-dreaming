# SSD — Open TODO

## Post-show dream handling (IMPACT 2026 → ongoing) — opened 2026-05-29

**Context:** IMPACT 2026 show is over (May 27–28). Live site `salishseadreaming.art/cloud?event=impact-2026`
still serves all 66 visible dreams — **intentionally left as-is** because the operator shared that exact link
on social media on 2026-05-29. Planned cleanup deferred ~1 day.

**Checkpoint already done (2026-05-29):**
- Private full archive of all 337 DB rows (102 during-event IMPACT dreams) →
  `private-archive/impact-2026-checkpoint-2026-05-29.json` (gitignored, off public surface).
- Draws the line: dreams in that file = "during the event"; anything after = "after."

**Consent facts (live `~/ssd-v5/prompts-v5.db` on poly:9004):**
- 102 IMPACT submissions total.
- 66 have `visible_in_installation=1` (currently served — in-show consent only).
- **Only 3** have `available_post_show=1` ("Kept after the show closes" — the post-show retention toggle).
  - `oceans as canoe highways`, `two headed sea serpent`, `barnacles turning into eyes of the sea`.
- No auto-archival job exists; nothing changes unless we act.

**✅ DONE — executed 2026-06-10** (live on `salishseadreaming.art`, ssd-v5 / poly:9004):
- [x] Added `ongoing` event window (2026-05-30 00:00 PDT → open-ended) to `~/ssd-v5/scripts/event_membership.py`.
- [x] Flipped default scope `impact-2026` → `ongoing` in `~/ssd-v5/static/dreamworld.html` (1×) + `web/visitor.html` (3×).
- [x] Seeded the `ongoing` view with **12 authored example dreams** (ours; full consent: visible + cluster + quotable + post_show), POSTed through `/prompt` so they embedded + positioned + clustered emergently (ids 23322–23333). Verified 12 nodes live.
- [x] Published the public **3-dream** IMPACT snapshot → `static/dreams_snapshot_impact-2026.json` (committed to repo; served at `/graph-assets/dreams_snapshot_impact-2026.json`). The `available_post_show=1 AND event=impact-2026` set: oceans as canoe highways / two headed sea serpent / barnacles turning into eyes of the sea.
- [x] **Archived the 63 non-consented-but-served IMPACT dreams** (`archived_at` set; 63-count guardrail passed). They remain in the DB, no longer served — honoring "Kept after the show closes" = unchecked.

**End state (verified end-to-end through Caddy):** default `/cloud` → `ongoing` (12 dreams); `impact-2026` view → 3 consented; DB row count unchanged at 349 (337 + 12 seeds); nothing deleted.

**Deployment notes for next time:**
- Production is **ssd-v5 on poly:9004** (Caddy: `salishseadreaming.art → localhost:9004`). NOT the `salish-sea-dreaming/` systemd service on 9000 (that's `v1.salishseadreaming.art`, old schema). The 9004 process is a **manually-started, nohup'd uvicorn** (no systemd) — restart by killing the pid on :9004 and relaunching `venv/bin/python3 -B venv/bin/uvicorn scripts.gallery_server:app --host 0.0.0.0 --port 9004 --workers 1` from `~/ssd-v5` (it self-loads `.env`).
- `event_membership.py` is imported and **cached in-process** → an edit needs a 9004 restart to take effect (static files are read per-request, no restart). Pre-mutation backups left on poly as `*.bak-2026-06-10`.
- The API's bare default (no `?event=`) is still `impact-2026` per `ssd-events.json meta.default_event`; the client always sends `?event=ongoing` so visitors see ongoing. Left as-is (chatbot context).
- Fresh pre-mutation checkpoint: `private-archive/impact-2026-checkpoint-2026-06-10.{db,json}` (gitignored).
