# May 27 Day-of Readiness — Indigenomics IMPACT 2026

**Show:** Indigenomics IMPACT 2026 art activation, May 27–28
**Venue:** HR MacMillan Space Centre, Hubble Space, 1100 Chestnut St, Vancouver
**Doors:** confirm with venue contact
**Generated:** 2026-05-25 overnight by Claude (autonomous session); please review + add anything missing before May 27.

This document is **documentation only**. None of the rollback commands here were run autonomously — they exist for Darren to execute by hand if the show needs a fast revert.

---

## 1. Current production state (verified 2026-05-25 ~02:45 PDT)

| Surface | URL | Backend | Status |
|---------|-----|---------|--------|
| Primary (QR target) | `salishseadreaming.art`, `www.salishseadreaming.art` | poly :9004 (`~/ssd-v5/`) | ✅ live |
| v1 rollback | `v1.salishseadreaming.art` | poly :9000 (`~/salish-sea-dreaming/`) | ✅ live |
| v2/v3/v4/v5 sandboxes | `vN.salishseadreaming.art` | poly :9001–9004 | ✅ live |
| TouchDesigner relay | 3090 (Pravin's studio) → polls `salishseadreaming.art/td/next` every 2s | n/a | ✅ polling per server logs |
| Knowledge graph | `salishseadreaming.art/graph?event=impact-2026` | static `ssd-data-map-zoom.json` + dynamic `/graph/event/<id>` | ✅ 13 nodes (10 members + 3 bridges) + live visitor offerings |
| Chat | `salishseadreaming.art/chat` | TELUS Gemma 4 31B endpoint | ✅ responsive |
| Visitor app snapshot-in-chat | shown after submit via `pollVisitorSnapshot()` | uses `/td/snapshot/visitor/<id>.jpg` | ✅ verified end-to-end |

## 2. URL routing

Caddyfile on poly at `/etc/caddy/Caddyfile` routes:

```
salishseadreaming.art, www.salishseadreaming.art → localhost:9004  (v5, IMPACT-ready)
v1.salishseadreaming.art → localhost:9000  (Digital Ecologies-era code; safe rollback)
```

**Rollback to v1 (emergency only — say "this is unsafe to ship"):**

```bash
ssh poly@37.27.48.12 'sudo sed -i "s/reverse_proxy localhost:9004/reverse_proxy localhost:9000/" /etc/caddy/Caddyfile && sudo systemctl reload caddy'
# Then re-point the relay back to :9000 too:
ssh windows-desktop 'taskkill /F /IM python.exe /FI "WINDOWTITLE eq td_relay*" 2>nul; cd C:\Users\user && set GALLERY_URL=http://37.27.48.12:9000 && start /B venv\Scripts\python.exe td_relay.py'
# Verify:
curl -sL https://salishseadreaming.art/visitor.html | grep -c consent-panel  # should be 0 after rollback (v1 has no consent UI)
```

**Test rollback path lightly before doors (without actually committing):**

```bash
# Just curl-check that v1 URL is alive and serves the older HTML
curl -s https://v1.salishseadreaming.art/health
curl -sL https://v1.salishseadreaming.art/visitor.html | grep -c -E "snap-card|pollVisitorSnapshot"   # should be ≥2 (v1 has tonight's snapshot-in-chat)
```

## 3. Database state

| DB | Path | Schema |
|----|------|--------|
| v1 | `~/salish-sea-dreaming/prompts.db` | 18 cols, no consent fields |
| v5 (live) | `~/ssd-v5/prompts-v5.db` | 24+ cols including `visible_in_installation`, `included_in_clustering`, `quotable_by_agent`, `available_post_show`, `consent_token`, `archived_at` |

**Event windows for `event_membership.event_for()`:**

- `digital-ecologies-2026`: 2026-04-10 00:00 PDT → 2026-04-26 23:59 PDT
- `impact-2026`: 2026-05-25 00:00 PDT → 2026-05-29 23:59 PDT
- Everything else: `None` (will not appear in any event-scoped view)

**To re-bucket counts at any time:**

```bash
ssh poly@37.27.48.12 'python3 ~/ssd-v5/scripts/event_membership.py ~/ssd-v5/prompts-v5.db'
```

## 4. Pre-doors smoke tests (run ~30 min before May 27 doors)

Run on Darren's laptop from this repo:

```bash
cd ~/projects/salish-sea-dreaming
bash scripts/integration_test_kg.sh         # ~30s; expects "=== All checks passed ==="
```

Manual browser checks:

1. Open `https://salishseadreaming.art/` on a phone (or QR-scan a printed test code) → see the offering page with consent panel (4 toggles, conservative defaults)
2. Submit a real-looking prompt → see "your offering is joining the dream" → snapshot card appears in chat → "save your dream" downloads JPEG, "explore your dream in the graph →" opens the KG
3. The KG page should: default to `?event=impact-2026`, show the event-picker top-left, show the IMPACT event hub centered, ~13 base nodes + however many test-mode offerings already exist, dimmed cross-event bridge nodes
4. Click a dimmed bridge node → expands into Digital Ecologies cluster; breadcrumb appears; ✕ collapses
5. `https://salishseadreaming.art/chat` page (visited via the chat-mode in visitor app) → ask "what is this installation about?" → should get a coherent Gemma response (won't mention IMPACT specifically until card content gets refreshed — that's the known limitation in §6)

## 5. Known issues / things to verify with team

| Issue | Severity | Action |
|-------|:--------:|--------|
| Chat RAG still uses `ssd-cards.json` Digital Ecologies-era card content (mentions Mahon Hall) | medium | Schedule daytime session with Austin/Carol Anne/Pravin to author IMPACT-specific card content. Hard guardrail: no autonomous content authoring. |
| Visitor-offering consent gate uses `visible_in_installation` AND `included_in_clustering` — toggle wording doesn't explicitly mention KG-node visibility | medium | Team re-affirmation requested. Conservative interpretation (BOTH required) currently shipped. |
| Bridge computation in `/graph/event/<id>` is O(L²) — ~3-4s warm latency for digital-ecologies (197 offerings + 1500 base nodes) | low | Acceptable for gallery (1-3 concurrent visitors typical); flagged for post-show optimization. |
| v1 rollback re-points relay too — requires SSH access to 3090 to flip GALLERY_URL env var. If 3090 SSH is down (as it was 2026-05-25 ~02:20), rollback is partial (web UI flips back but TD still receives prompts from v5) | medium | Confirm 3090 SSH access pre-doors. If access is down, only the URL flip works — visitor experience falls back to "see dream in graph + dreamworld" but TD shows the prompts that v5 OSC's. |
| 3090 SSH access was DOWN during the overnight session (direct LAN + reverse tunnel both timed out) — relay still polling per server logs but couldn't verify TD state | medium | Confirm SSH path before doors (try both `windows-desktop` and `windows-desktop-remote`). Restart `SSD-SSH-Tunnel` scheduled task on the 3090 if needed (which requires console access). |
| OpenAI API key in `~/ssd-v5/.env` and `~/salish-sea-dreaming/.env` ends in `…GdwA`, returns 401 | low | TELUS Gemma is primary now — OpenAI fallback only fires if TELUS goes down. Rotate key when convenient. |
| Card content in chat RAG mentions "Briony Penn", "Moonfish Media", etc. — those are accurate but Digital-Ecologies-framed | low | Same as first row. |

## 6. Rollback hierarchy (worst-to-best preserve)

If something breaks before/during doors:

1. **Tiny issue** (e.g., a specific node mis-render) → leave it; gallery experience is robust to single-node weirdness
2. **`/graph` view broken but everything else works** → set `?include_offerings=false` query param in the QR's URL as a temporary fix; visitors lose live offerings but see the IMPACT graph backbone
3. **`/graph` and `/chat` broken** → flip Caddy to v1 (§2 above). Visitors get the Digital Ecologies-era app + snapshot-in-chat (tonight's port) + their dreams reach TD via v1's relay path
4. **Site fully down** → restart v5 service: `ssh poly@37.27.48.12 'kill $(ss -lntp 2>/dev/null | grep ":9004 " | grep -oE "pid=[0-9]+" | head -1 | cut -d= -f2); cd ~/ssd-v5 && nohup env TD_OSC_PORT=7777 GALLERY_SERVER_PORT=9004 DB_PATH=/home/poly/ssd-v5/prompts-v5.db COOKIE_SECURE=true venv/bin/uvicorn scripts.gallery_server:app --host 0.0.0.0 --port 9004 --workers 1 >> v5.log 2>&1 </dev/null & disown'`
5. **Total disaster** → flip Caddy + restart relay manually via console on 3090

## 7. Pre-doors human checklist (Darren's checklist)

- [ ] Confirm SSH access to 3090 (`ssh windows-desktop` should respond)
- [ ] Confirm relay process running on 3090 (poly server logs should show `/td/next` requests every 2s from `70.67.168.108`)
- [ ] Confirm TELUS Gemma endpoint responding (run a `/chat` test)
- [ ] Run `bash scripts/integration_test_kg.sh` — green
- [ ] Visit `salishseadreaming.art/` from a phone via real cellular (not gallery wifi) — submit a test prompt, walk through chat → snapshot → graph link
- [ ] Walk a non-technical person through the same flow — surface anything confusing
- [ ] (Optional but recommended) reach out to Austin/Carol Anne/Pravin for the open-question affirmations from the overnight plan §Stakeholder Alignment
- [ ] Phone Memory Express to confirm 5090 pickup status (per project CLAUDE.md `What's Left` row)
- [ ] (If TELUS Gemma is down) rotate OpenAI key + update both .env files + restart v5

## 8. Backup files present on poly (for emergency restore)

```
~/ssd-v5/.env.bak.20260525-013316                              (pre-TELUS-endpoint-update; old config)
~/ssd-v5/scripts/gallery_server.py.bak.20260524-215314         (pre-snapshot-in-chat port; full v5)
~/ssd-v5/scripts/gallery_server.py.bak-pre-snap.20260524-215314
~/ssd-v5/scripts/gallery_server.py.bak-pre-p6.20260525-020925  (with snapshot, before visitor-offering KG merge)
~/ssd-v5/web/visitor.html.bak.20260524-215314                  (pre-snapshot-in-chat; original v5)
~/ssd-v5/web/visitor.html.bak-pre-p7.20260525-021616           (after P4/P5 deploy but before explore-link)
~/ssd-v5/static/ssd-data-map.html.bak-pre-p4.20260525-020535   (pre-P4 filter UI)
~/ssd-v5/static/ssd-data-map.html.bak-pre-p5.20260525-022313   (P4-deployed; pre-P5 click-to-expand)
~/ssd-v5/static/ssd-data-map-zoom.json.bak.20260525-003305     (pre-P1 schema additions; original graph data)
~/ssd-v5/static/ssd-data-map-zoom.json.bak-pre-p3.20260525-013718  (post-P1 schema; pre-IMPACT-data assembly)
~/ssd-v5/static/ssd-edge-vocab.json.bak.20260525-003305        (pre-P1 edge-vocab additions)

~/salish-sea-dreaming/prompts.db.bak.20260525-072752           (v1 DB snapshot pre v5-promotion)
/etc/caddy/Caddyfile.bak.20260525-072752                       (pre v5-promotion Caddy config)
```

## 9. Out of scope / parked for daytime

- IMPACT-specific card content authoring (requires team consent gate)
- Coast Salish concept nodes (Crescent / Circle / Trigon / Pearl) — held per Austin consent floor
- Bridge-computation perf optimization (current O(L²) is fine for gallery traffic)
- v1 .env updates (rollback path needs same TELUS or new OpenAI key if invoked)
- TELUS pod uptime ownership for May 27–28 (currently single-endpoint dependency)
- Witnessing receipts / Creator Jam integration (deferred — per round-1 Q5 disposition)
