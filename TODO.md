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

**To do (after the ~1-day hold):**
- [ ] Add an `ongoing` event window to `~/ssd-v5/scripts/event_membership.py` (start 2026-05-30 00:00 PDT → open-ended).
- [ ] Make `ongoing` the default scope in `~/ssd-v5/static/dreamworld.html` + `web/visitor.html`
      (currently hardcoded `|| 'impact-2026'`).
- [ ] Seed the `ongoing` view with a curated set of good dreams (decide content WITH operator),
      POSTed through the normal `/prompt` pipeline so they embed + cluster emergently. Set their
      consent flags fully on (these are ours): visible + cluster + post_show.
- [ ] Publish the **public 3-dream** IMPACT snapshot (the `available_post_show=1` set) —
      e.g. `static/dreams_snapshot_impact-2026.json` (committable; consented content).
- [ ] **Archive the 63 non-consented-but-served IMPACT dreams** (set `archived_at`) so they stay in the
      DB but are no longer served — honoring the "Kept after the show closes" = unchecked choice.
      Do this *together with* the default flip so the public view never looks sparse.

**Sequencing note:** flip default → seed ongoing → THEN archive non-consented, so visitors always land
on a populated view. The impact-2026 view becomes a historical archive (3 served + reachable).
