---
plan_type: strategic
---

# Plan: apr-20-onsite-walkthrough

## Context

Prav asked (Apr 19 evening) for "a program for tomorrow AM testing. Of all the above" — referring to the day's cascade of incidents, investigations, fixes, the resilience-architecture plan, and the Zoe support manual. He surfaced two material clarifications that change how tomorrow should run:

1. **"I don't know if there is actually a mic on the 3090. There were not inbuilt speakers either."** Implication: the silence detector built today reads from `AUDIO_DEVICE_INDEX=0` — likely HDMI loopback or NDI virtual audio if no physical mic exists. The 0.0001 silence readings today may be non-signal noise from an input that was never connected to the gallery's audio environment. Full silence-detection architecture needs hardware re-verification before we trust any of its outputs.
2. **"We can set up with 4 projectors in my home studio to test out."** A duplicate-ish rig where we can break things safely without visitor impact. Better substrate for Phase 0/1 resilience work than the live gallery machine during show hours.
3. **Zoe restarted Arena at 3:22 PM today** without prompt from either of us. Not a passive eyes-on-ground docent — she's comfortable with the Advanced Output fix and executed it solo. The resilience plan's escalation section needs to update from "Zoe has no escalation authority" to "Zoe is a first-responder for known failures; escalates unknowns."

We shipped real changes to the 3090 today (silence detector, daily diagnostic, health probe retry, patched Autolume `visualizer.py`, fixed NDI hostname binding). Tomorrow is **alignment + empirical verification**, not new deploys. Prav has had a long day with visitors + Raf's pressure; a well-paced walkthrough gets him from "sense of lots happening" to "I understand what's running, what's broken, and what's planned."

**Reference docs (existing today, not to be duplicated):**
- `~/.claude/plans/resilience-architecture.md` — strategic plan post 8 review passes
- `docs/onsite-support-manual-DRAFT.md` — Zoe's printed manual draft (v0.1)
- `docs/environment-audit-2026-04-19.md` — pre-flight audit; AutoLogon confirmed, 6 other items open
- `docs/playbook.md` — existing 385-line ops reference

---

## Goal

Deliver a structured, time-boxed walkthrough with Prav that (a) establishes ground-truth on the actual hardware reality of the 3090 audio/mic/camera path, (b) aligns on what shipped today + what's planned next, (c) decides whether Phase 0/1 resilience work moves to Prav's home-studio test rig rather than the live gallery machine, and (d) produces one consolidated "OK go" signal or explicit deferral for each sub-item.

## Non-goals

- **Not deploying new scheduled tasks during the session.** Today's tight loop of "deploy to live 3090" caused enough pressure; tomorrow is for clarity, testing what's already there, and planning.
- **Not rewriting the resilience plan during the walkthrough.** The plan exists. Tomorrow captures Prav's decisions as bullets to incorporate after.
- **Not running intrusive tests during the session** (e.g., `Stop-Process Arena -Force` right before gallery opens). Everything disruptive moves to the home-studio rig or post-close windows.
- **Not solving Autolume/CUDA 12.4 migration.** Explicitly Phase 2 / post-show.
- **Not processing visitors** — gallery opens 11:00, we stop at 10:45 regardless of completion.

## Constraints

- **Time budget: 9:45 AM – 10:45 AM = 60 min** of walkthrough + test. Hard stop at 10:45 to give Prav 15 min for pre-opening prep.
- **Location: Mahon Hall gallery** (3090 tower is there). Prav physically present; Darren remote via Signal/WhatsApp voice.
- **No changes to live gallery composition or TD project** during the session unless explicitly deciding to revert something from today.
- **Every decision goes to written form** (committed to repo before session ends, not verbally-held).
- **Prav is not yet caught up on the full resilience plan** — his mental model is from today's incidents, not the writeup. Walkthrough sequence matters: ground truth first, plan second.

## Assumptions

- Prav arrives Mahon Hall by 9:45 AM Apr 20.
- SSH tunnel to 3090 is up so Darren can remote-in while Prav inspects the machine physically.
- Darren + Prav both online via Signal or WhatsApp voice during the session.
- Zoe is NOT in this session — Darren + Prav only. Zoe's role is discussed; she doesn't join live (respects her weekend; bring her updates later via printed manual).
- `DEFERRED: should Prav record the session for async review?` Nice-to-have; decide on call.
- `DEFERRED: Shawn or other collaborators in the session?` Default no — keep focused.

### Alert-channel reality (confirmed earlier)

- **Darren gets Telegram alerts** in real time. Prav does not use Telegram.
- **Prav gets email** — daily diagnostic (deployed today as Telegram) also goes to Prav via Gmail SMTP once his app password is added to `.ssd_secrets.ps1`. That password exchange is a 2-min item in the walkthrough.

### Stakeholder alignment — answers to strategic open questions

**Raf/curatorial on "minimum mode" acceptability during public hours.** Prav's Apr 19 WhatsApp to Raf explicitly framed minimum functioning mode (main wall + WMP loop) as acceptable, and Raf's response ("great to hear you'll be here every day") accepted the operating envelope without objection. Taken as tacit green-light, NOT an explicit sign-off. Add a 1-sentence item to walkthrough **4.7** ("alignment ladder"): decide whether to send Raf a short written "here's the minimum-functioning-mode policy" note for the record, or leave as tacit. Prav's call. Not blocking Phase 0.

**Zoe's escalation protocol — current doc conflict.** Two docs disagree:
- `docs/onsite-support-manual-DRAFT.md` (today's draft): "Call Prav first. Don't touch the computer tower."
- Demonstrated reality Apr 19: Zoe clicked Advanced Output in Resolume solo at 3:22 PM and recovered Arena.

Resolution proposed for session **4.6**: adopt a two-tier protocol explicitly. Tier A ("known-fix" set — the 2–3 symptoms on the quick-reference card where Prav has walked her through the fix): Zoe executes without waiting, Darren gets notified via WhatsApp after. Tier B (anything else): Zoe texts Prav/Darren before touching anything. Update the Zoe draft manual with the explicit split. This converts Apr 19's ad-hoc recovery into a codified permission.

**Home-studio rig equivalence evidence (if green-lit in 4.2).** "Equivalent enough" means matching these specific aspects that have bitten us:
- **Same GPU class** (RTX 3090 or better) for VRAM behavior + NVIDIA driver path.
- **Same Windows major version + up-to-date MSVC BuildTools** so CUDA compile issues reproduce.
- **Same audio topology** (computer out → splitter → speakers + wireless receiver) so silence detection validates.
- **Same task scheduler tasks + heartbeat manifest** deployed identically via repo.
- **Not required to match:** specific projectors (projection content is the artistic output, not the monitoring target). 1–2 projectors is sufficient for test rig; 4 is nice-to-have for composition work.

Adopting it: before any Phase 0/1 change declared "done based on home-rig tests," the same change runs on the rig with the 4 equivalence items all validated. If any fails to match, that change still deploys-to-live with standard 48h observe window + rollback ready.

**Default branch for unresolved Apr 20 session gates.** If a 4.x item can't be decided by 10:40 AM:
- 4.1 (Gmail password) → defer; email path stays off until next sync; daily digest remains Telegram-only.
- 4.2 (home-studio rig) → defer; Phase 0 continues live-3090 with extra caution (overnight-only deploys, 48h observe).
- 4.3 / 4.4 (silence detector) → retire the alert (threshold=0) as safe default; rebuild is Phase 1.
- 4.5 (Resolume watchdog tonight) → ship anyway — it's additive, low-risk, and the failure pattern is proven; Darren's ship decision if Prav explicitly deferred.
- 4.6 (Zoe role) → update manual to Tier-A/Tier-B as default; Prav can override in follow-up.
- 4.7 (governance 4) → defer to async Signal thread; no blocker.
- 4.8 (Windows Update lockdown) → ship anyway (strictly protective, directly addresses Apr 19's root cause); Darren's ship decision.

**Stability-freeze trigger.** Objective condition that moves us to "no changes, babysit through Apr 26": any of (a) ≥ 2 visitor-facing incidents in a single day caused by our own changes, (b) Prav explicitly requesting freeze, (c) discovery of a cascading dependency not in our model (e.g., TD update breaks SD loading). If triggered: all Phase 0/1 work halts; plan resumes post-show; focus shifts to on-site support + rapid-response only.

**Who owns real-time incident detection when Darren is unavailable.** Current gap. Prav doesn't see Telegram; Zoe does eyes-on-ground. Mitigations to decide in 4.7: (a) add Prav to Telegram group-chat as read-only — Telegram has no "email me on alert" built in, but group-chat lets him see post-hoc without being the primary channel; (b) add a 2nd notifier that emails Prav on CRITICAL only (limit noise); (c) acknowledge the gap and treat "Darren unavailable + incident during show hours" as a known-accepted risk, falling back to Zoe's on-site response for known patterns. Recommend (b) post-Phase-2. Not blocking.

**poly + reverse tunnel single failure acceptance.** Acknowledged risk for show week. Degradation pattern if both fail: Darren loses remote SSH; Prav loses Gmail diagnostic (served via poly? actually gallery-server not diagnostic — diagnostic is on 3090 via 3090's own Gmail SMTP). So poly+tunnel dual-failure means: walls continue operating, visitor prompts stop flowing, diagnostic email still fires, but Darren can't remote-fix. On-site fix is only option. Acceptable: visitors still have non-interactive experience; Zoe's manual covers the worst case. Tailscale as secondary tunnel is Horizon 3.

**Unresolved written permissions for existing assets.** Known risks from `docs/credits-attribution.md` + CLAUDE.md:
- **Moonfish Media videos** — "collaborator permission" per CLAUDE.md; written permission status for touring TBD. Owner: Prav.
- **David Denning photos** — same status; "collaborator permission" noted, touring clearance TBD. Owner: Prav.
- **StreamDiffusionTD TOX** — open source, license OK per dotsimulate's terms; no blocker.
- **Autolume** — Apache 2 license per MetaCreation Lab; no blocker.
- **Briony Penn watercolors** — not in live pipeline; not a blocker today.
These are **touring dependencies (Horizon 3)**, not Phase 0/1 blockers. Added to the Horizon 3 tracking: "Prav confirms written touring permission from Moonfish + Denning before tour packaging ships."

### Hardware-reality gap

- **Assumed today, not verified:** mic connected to 3090.
- **Assumed today, not verified:** room speakers powered + fed from the 3090.
- **Confirmed from Prav's message:** no built-in 3090 speakers.
- These are the first items of the walkthrough; everything downstream depends on the answers.

---

## Approach

Structure the 60-min session as six time-boxed phases, in order of "ground truth first, planning second, tests last." Each phase has a written artifact (bullets in `docs/apr-20-session-notes.md` committed at session end). Walkthrough is **Darren-driven agenda, Prav-driven content** — Darren reads agenda, Prav answers / inspects / decides.

**Sequence rationale:**
1. **Hardware reality check first** (10 min). Without this, half of what we built today is possibly non-signal.
2. **What shipped today** (10 min). Prav sees the current 3090 state vs. yesterday.
3. **Today's incident recap** (5 min). Shared vocabulary before planning.
4. **Resilience plan in brief** (10 min). High-level, not line-by-line.
5. **Decisions from Prav** (15 min). 4 governance questions + home-studio rig offer + audio threshold + new items from hardware check.
6. **Live verification + closeout** (10 min). Safe checks only. Commit session notes.

**Home-studio rig as a pivot.** If green-lit in phase 5, Phase 0/1 resilience work (silent-death watchdogs, Arena watchdog, meta-watchdog, heartbeat manifest) moves there. Live-gallery changes limited to the Resolume watchdog (already justified by two crashes in 18h) and anything strictly protective. Reduces operational risk of the plan by ~70% — we'd no longer modify an active installation.

## Implementation Steps

### Phase 0 (9:45–9:55) — Hardware reality check

Darren asks; Prav physically inspects. Answers land in session notes.

0.1. **Mic presence.** Prav checks 3090 tower + connected USB peripherals. ANY physical mic (USB, 3.5mm, wireless receiver) present? If yes, model + position?

0.2. **Speaker setup.** Trace the audio-out cable → where? Splitter? Direct to one device? Photo of the cable chain + label each end. Previous session memory assumed "splitter → speakers + wireless headphone transmitter" — verify or correct.

0.3. **Wireless headphone path.** Bluetooth-paired to Windows, or analog-fed from a transmitter after the splitter? If Bluetooth, device name in Windows audio settings? If analog, transmitter model?

0.4. **Windows audio-device enumeration.** Darren runs `Get-PnpDevice -Class AudioEndpoint | Where Status -eq 'OK' | Select FriendlyName, Status` live; Prav confirms which device is actually in use.

0.5. **Camera presence.** Prav's earlier message mentioned bringing "a wired mic and camera" — is there any camera on the 3090 currently? Context: not in use today, but knowing matters for future visitor-presence-detection.

0.6. **Write-up.** One paragraph per item in session notes, with a PASS/FAIL on "what we thought today."

### Phase 1 (9:55–10:05) — What shipped to the 3090 today

Darren walks through each artifact with a one-line verification Prav can see.

1.1. **Silence detector.** Live: `ssh windows-desktop-remote "Get-Content C:\Users\user\ssd_audio_state.json"`. Prav sees the 60-sec rolling max. If Phase 0 revealed no mic, the reading is meaningless → decision to retire the alert until Phase 2 rebuild with real hardware.

1.2. **Daily diagnostic Telegram.** Darren shows Telegram history: daily diag at 14:32 today. Email path stubbed, awaits Prav's Gmail app password.

1.3. **Zoe support manual draft** (`docs/onsite-support-manual-DRAFT.md`). Prav reads the one-page quick-reference section — the only page Zoe sees day-one. Flag any language issues.

1.4. **Autolume patches shipped today** (4 touches):
   - `autolume/modules/visualizer.py`: `load` → `load_pkl` upstream bug fix. Keep.
   - `autolume/torch_utils/ops/params.py`: `use_custom = False` workaround for MSVC/CUDA cutoff. Keep as interim; revert post-CUDA-12.4 install.
   - `SSD-Autolume` task re-pointed at `launch_autolume_autostart.bat` via delegator. Keep.
   - 3 Autolume processes killed ~12:42; Autolume not currently running. Known; SD noise fallback covers it.

1.5. **Health probe additions.** `health_probe.ps1` now has retry on gallery-server check + `audio_monitor` + `audio_silent` checks. Show log tail so Prav sees what's firing.

1.6. **Commit trail.** `git log --oneline -10` — Prav sees the 4–5 commits from today + the resilience plan.

### Phase 2 (10:05–10:10) — Today's incident recap

Not re-litigating; confirming shared understanding. 5 min max.

2.1. **Apr 18 23:21 → Apr 19 10:25** — Arena overnight heap crash, 11-hour silent period, Telegram every 30 min. Zoe restarted via Advanced Output fix this morning.

2.2. **Apr 19 ~6:40 AM** — Windows Update upgraded MSVC BuildTools → Autolume CUDA kernel compile broke.

2.3. **Apr 19 10:07** — TD died during on-site troubleshooting with Zoe.

2.4. **Apr 19 ~12:20 PM** — Darren brought TD back up via schtasks remote trigger.

2.5. **Apr 19 ~3:22 PM** — Arena crashed AGAIN (same pattern). Zoe restarted solo. Confirms repeating failure, not one-off.

2.6. **Summary:** four system-level incidents, two Zoe recoveries, ~4 hours of degraded operation. Walls stayed (mostly) up; audio state unclear due to Phase 0 hardware gap.

### Phase 3 (10:10–10:20) — Resilience plan walkthrough (high level)

Not line-by-line. Prav gets the architecture + four phases + decision points.

3.1. **Plan link + elevator pitch:** extend existing scripts with heartbeat files + meta-watchdog to eliminate the "task says running, process is dead" pattern we've seen 3× this week.

3.2. **Four phases summary table.** One row per phase with goal + time window + biggest decision.

3.3. **Two big new things for Prav's mental model:** (a) every long-lived task writes a heartbeat file; meta-watchdog alerts if any heartbeat goes stale; (b) Resolume gets a process watchdog matching the TD one.

3.4. **Home-studio test rig proposal (from Prav's message).** Brief pitch: duplicate setup where Phase 0 + Phase 1 resilience work happens instead of on the live machine. Dramatically lower operational risk. Logistics: what's needed, rough timeline. This is the pivot decision.

3.5. **NOT doing until Phase 3:** CUDA 12.4 install, Macrium backup, deploy-elsewhere package, NSSM migration, Tailscale secondary tunnel. All post-show.

### Phase 4 (10:20–10:35) — Decisions from Prav

Explicit list with thumbs or "defer." Each written into session notes + committed.

4.1. **Gmail app password** for email diagnostic. Prav generates via Google → shares via Signal (not group). Darren installs into `.ssd_secrets.ps1`. 2 min.

4.2. **Home-studio test rig green-light.** Yes/no/more-info. If yes: 4 projectors, mic, camera, 3090-equivalent or same-spec substitute? Who buys/brings what? Target online date.

4.3. **Silence detector rebuild priority.** Given Phase 0 findings: rebuild on real hardware (home rig + physical mic + WASAPI output session check) as Phase 1 priority? Or retire the alert until home rig exists?

4.4. **Audio threshold calibration.** If mic exists: test with a known tone now to calibrate. If not: defer to home rig.

4.5. **Resolume process watchdog — ship tonight?** Additive, low-risk, addresses demonstrated repeating failure. Proposed: ship matching the TD watchdog, to the live 3090, tonight after gallery close. Prav's explicit OK or defer.

4.6. **Zoe's role update.** She's doing tech recovery (restarted Arena today). Update escalation from "eyes-on-ground only" to "first-responder for known failures, escalates unknowns." Also: formal permission to add her to knowledge graph as creative-team entity.

4.7. **The 4 governance questions from the plan's Prav DM.** Walk through quickly if time allows:
   - Overall architecture blessing
   - Apr 21 15-min window budget (may moot if home-studio rig is happening)
   - Email vs Telegram rota
   - "Minimum-mode promotion" exception scope

4.8. **Windows Update lockdown timing.** Proposed: tonight. Approval to proceed.

### Phase 5 (10:35–10:45) — Live verification + closeout

Only safe, read-only or trivially-reversible checks.

5.1. **Run daily diagnostic manually.** `ssh windows-desktop-remote "powershell -ExecutionPolicy Bypass -File C:\Users\user\daily_diagnostic.ps1"`. Prav sees Telegram message land (Darren's phone). If Gmail password added in 4.1, Prav sees email arrive. ~10s.

5.2. **Read current state.** `ssd_audio_state.json` + health_probe.log tail on screen together so we share the reality going into tomorrow's operations.

5.3. **Confirm commits pushed.** `git log origin/main --oneline | head -8` from the repo.

5.4. **Session notes commit.** `docs/apr-20-session-notes.md` gets everything written during session, committed + pushed before session ends.

5.5. **Next checkpoint.** Set next Darren+Prav sync window — target Apr 22 or home-rig-online day, whichever first.

---

## Acceptance criteria

- [ ] Phase 0 hardware-reality check completed; answers for 0.1–0.6 all documented; no "unknown" left behind.
- [ ] Phase 1 walkthrough completed; Prav has seen (not just heard about) each of today's 6 sub-items on the 3090.
- [ ] `docs/apr-20-session-notes.md` committed + pushed to main before 10:45 AM hard stop.
- [ ] Decision recorded (yes/no/defer) for each of 4.1–4.8; no item left as "TBD will-discuss-later."
- [ ] Home-studio rig decision made; if yes, target online-date noted; if no, live-deploy plan stays with Prav's explicit blessing.
- [ ] Resolume watchdog deploy decision explicit; if yes, deployment happens same evening with verification ping to Prav.
- [ ] Gmail app password received + installed in `.ssd_secrets.ps1`; test email verified received (if 4.1 yes).
- [ ] Silence detector status recorded: kept / retired / rebuild-pending. No ambiguity.
- [ ] Zoe's role update documented in 2–3 sentences; knowledge-graph-permission status captured.
- [ ] Every AC traced to a specific line in `docs/apr-20-session-notes.md`.

## Verification plan

- AC Phase 0 done → `grep -c "^## 0\." docs/apr-20-session-notes.md` ≥ 6
- AC Phase 1 walkthrough → session notes include screenshots or quoted output from each of the 6 sub-items
- AC session notes committed → `git log docs/apr-20-session-notes.md` shows commit timestamped before 10:45 AM Apr 20
- AC all decisions recorded → `grep -E "^\- \*\*Decision:" docs/apr-20-session-notes.md | wc -l` = 8 (one per 4.1–4.8)
- AC home-studio decision → session notes contain explicit "Home-studio rig: YES/NO/DEFER" with rationale
- AC watchdog deploy → if YES on 4.5, `git log --oneline --since "2026-04-20"` shows `resolume_watchdog.ps1` commit by end of day
- AC Gmail integration → if YES on 4.1, test diagnostic + screenshot of received email; logged in session notes
- AC silence detector → one-line statement of current operational status
- AC Zoe role → notes document updated escalation role + knowledge-graph-permission row

---

## Rollback

**Trigger conditions.**
- Session runs long, threatens gallery-open readiness at 10:45.
- Hardware-reality discovery reveals something that changes today's fixes (e.g., no mic → silence detector data was all noise).
- Prav raises a concern that blocks Phase 0/1 resilience work entirely (e.g., "no new changes on the live 3090 until home rig").

**Rollback steps.**

1. **Time overrun.** Hard-stop at 10:40. Remaining 4.x items deferred to Apr 22 follow-up. Session notes capture what wasn't covered.

2. **Silence-detector retire.** Disable `audio_silent` check in health_probe.ps1 by setting threshold to 0 (always-PASS) rather than removing code. One commit, fully reversible.

3. **"No new changes on live 3090" verdict.**
   - Keep today's deployed changes (revert is higher-risk than just stopping).
   - Home-studio rig becomes the only Phase 0/1 execution surface.
   - Resilience plan timeline extends; Phase 0 slips to home-rig-online date.

**Data safety.** Walkthrough session, not a code-change session. Only write operations planned: (a) session notes commit, (b) Gmail password to secrets file, (c) optionally Resolume watchdog deploy in the evening. All additive + reversible. Tag `v-pre-apr20-session` before session starts to enable full revert.

## Risks

- **Session derails into open-ended architecture debate.** Mitigation: Darren strictly drives agenda; non-agenda items go to "parking" in session notes, not live discussion.
- **Hardware-reality discovery cascades into 20 new items.** Mitigation: each discovery gets one line in notes + parked for follow-up; session doesn't attempt to solve them.
- **Prav in post-visitor exhaustion.** Mitigation: ask at start if 60 min is realistic today or split to 2x30 across Apr 20 + 22.
- **Gallery open hits at 11:00 mid-conversation.** Mitigation: hard-stop 10:45 regardless of completion.
- **Home-studio discussion becomes a 30-min deep-dive.** Mitigation: phase-3 slot is 10 min, yes/no only; logistics deferred to followup Signal thread.
- **Darren's SSH tunnel drops mid-session.** Mitigation: verify tunnel at 9:30; local-network SSH as fallback; Prav has Darren's phone if remote fails.

---

## Parking Lot

- (Impact: H) (Effort: M) (When: post-launch if home-rig green-lit) — Instrument home-studio rig with its own heartbeat manifest + Telegram bot so we can validate the full resilience stack before it touches live gallery.
- (Impact: M) (Effort: S) (When: next-sprint) — Add visitor-facing camera (Prav offered) as a secondary "is the wall showing content?" visual check, separate from mic.
- (Impact: M) (Effort: M) (When: post-show) — Ingest `docs/apr-20-session-notes.md` and prior runbooks as SpecDoc entities in knowledge graph for cross-doc search.
- (Impact: L) (Effort: S) (When: someday) — Record the session (with permission) and produce a written summary via Whisper + claude-mem for future reference.
- (Impact: M) (Effort: L) (When: post-show) — If home-rig becomes permanent, replicate SSH reverse-tunnel + Telegram bot chat so home ops + gallery ops have parallel monitoring.
- (Impact: M) (Effort: M) (When: post-show) — Rebuild silence detector on real hardware with WASAPI output-session peak as primary signal + mic as secondary, once mic existence/placement verified.

## References

- ~/.claude/plans/resilience-architecture.md
- docs/onsite-support-manual-DRAFT.md
- docs/environment-audit-2026-04-19.md
- docs/playbook.md
- scripts/health_probe.ps1
