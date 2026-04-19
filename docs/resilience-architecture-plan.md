---
plan_type: strategic
---

# Plan: resilience-architecture

## Context

**What we learned on April 19.** A cascade of failures over 14 hours exposed that the Salish Sea Dreaming installation has lots of tactical scripts but no unifying resilience architecture:

| Time | Event | Gap exposed |
|------|-------|------------|
| Apr 18 23:21 | Arena.exe heap-corruption crash | No Arena process watchdog. Sat dead 11h while Telegram fired same alert every 30 min |
| Apr 19 ~06:40 | Windows Update bumped MSVC BuildTools v14.44 (requires CUDA 12.4+) | No update policy; no change-detection for toolchain shifts |
| Apr 19 10:07 | TouchDesigner closed during on-site troubleshooting (Zoe) | No protection against well-meaning human intervention |
| Apr 19 ~10:25 | Arena restored by Prav+Zoe via 5-min WhatsApp call; Autolume never restarted | Recovery required synchronous human attention, not automated |
| Apr 19 11:35 | Zoe reported "no audio" — mic pickup 0.00015 (functionally silent) | No silence detection until I built one today |
| Apr 19 all day | SSD-TD-Watchdog dead since Apr 13 (zombie task); PS SoundPlayer dead since Apr 16; SSD-Audio task zombie | Tasks report "running" while underlying process is dead |
| Apr 19 — | Stale NDI hostname binding `MSI (Autolume Live)` vs real `DESKTOP-37616PR` | Config drift after hostname rename, never detected |

Every incident was individually foreseeable. Root pattern: **we have no meta-layer watching the watchers, and no systematic contract for what "healthy" means per component**. Prav's Apr 19 call concluded with clear direction — no updates during show, minimum functioning mode must always be reachable, daily pre-opening diagnostic, draft support manual for Zoe. This plan operationalizes that direction.

**Why now.** Exhibition runs 7 more days (through Apr 26); then Impact (May), touring after. "Prav on-site every morning" works for 7 days but doesn't scale to tour venues. Proactive hardening now → shippable installation later.

**What exists already.** `docs/playbook.md` (384 lines, comprehensive ops ref); `docs/tour-readiness-plan.md` (horizon-based planning pattern); `scripts/health_probe.ps1` (5-min probe with Telegram alerts via `ssd_notify.ps1`); Task Scheduler infrastructure (14 SSD-* tasks); working SSH reverse tunnel; today's additions: silence detector, daily Telegram diagnostic, Zoe support manual draft.

---

## Goal

Ship an installation that detects its own failures, heals what it can automatically, alerts humans for what it can't, and supports SSH-based remote recovery — so Salish Sea Dreaming can deploy to remote/non-technical venues with minimal on-site technical support, and the current "Prav on-site daily" stopgap becomes a deliberate choice rather than a necessity.

## Stakeholder alignment

This plan depends on three people having parity of knowledge + authority to make decisions on each other's behalf in time-pressured moments. Explicit roles:

- **Prav (Pravin Pillay, Creative Director, machine owner).** Final authority on: composition changes, artistic tradeoffs (minimum mode vs optimal), credential entry (Autologon password, 3090 admin operations requiring his password), Ableton setup, creative assets (heroes, WAV, model weights).
- **Darren.** Final authority on: technical architecture, script changes, remote operations, SSH + secrets, poly-side services (gallery server, tunnel). Owns poly uptime during exhibition week.
- **Zoe (on-site docent/curation).** Eyes-on-ground. Authority to: execute printed steps, escalate. NOT in escalation ownership chain (she calls Prav, Prav decides).

**Backup decision-maker if Prav unreachable during show hours:** Darren, with scope limited to "make current state safer, don't make composition or Ableton changes." If an artistic-intent question arises while Prav unreachable, **default to minimum functioning mode** (WMP + one projector) until Prav available — per Prav's Apr 19 direction explicitly stating minimum mode is always acceptable. No other designated backup (the team is small; over-designing fallback authority adds ambiguity rather than reducing it).

**Multi-day Prav absence (owner-only action blocking).** Two items are password-gated and require Prav directly: (a) AutoLogon credential entry via Sysinternals, (b) any 3090 admin operation triggering a UAC password prompt (rare since `user` is admin + most tools run via saved task-scheduler tokens). Policy: if Prav will be unreachable for >48h (scheduled absence), he configures AutoLogon ahead of time AND provides Darren a one-time temp-access credential sealed in a secure channel (Signal's disappearing-message feature), used only if a reboot happens during the absence. This is not pre-arranged today — adding as a Horizon 3 / touring-preparation item: "Prav + Darren establish a break-glass credential handoff protocol."

**Minimum-mode promotion rule — pre-approved exception threshold.** The rule "Darren never promotes from minimum mode remotely" has exactly ONE pre-approved exception: if minimum mode is active and the root cause is a known-to-be-transient event (e.g., Autolume VRAM gate deferred launch because Phase 2 mid-deploy caused a VRAM spike; that spike resolved + median free is back above threshold), Darren may trigger a promotion retry by running the same scripts a human on-site would run. This is narrow — the rule doesn't change for artistic-intent decisions, only for "the transient that forced minimum mode has cleared."

**Apr 21 10:30–10:45 AM window contingency.** If Prav is unavailable on Apr 21: defer the window to Apr 22 same time. If unavailable Apr 22 too: the 2 Resolume degradations (SD-stuck-fallback, TD-dead-fallback) automatically move to Parking Lot; remaining Phase 1 proceeds without them (they're additive, not gating). The Autologon credential entry is the only item that might further block — if autologon is NOT configured per 0.0.a, that single decision slides until Prav is reachable; InteractiveToken tasks queue up waiting for next logon, which happens on any reboot or Prav's next on-site morning (worst-case one-day delay during a period when he's always on-site).

**15-min window may not fit 4 decisions.** Realistic: AutoLogon entry (5 min), Ableton mode check (2 min), audio device designation (3 min), Resolume composition map walk (8 min). Total ~18 min — tight for a 15-min window. Decision: if the window runs over, the LAST item (Resolume map) is the one to defer. Rationale: AutoLogon unblocks many things downstream; Ableton mode + audio device are quick binary confirmations; Resolume map can slip to a 20-min Apr 22 window without blocking other phases. Split-gate deadlines: AutoLogon + Ableton + audio device = Apr 21 (or Apr 22 if Prav misses Apr 21). Resolume map = by end of Apr 22 or defer to Parking Lot.

**Phase 2 conflict accountability.** When Phase 2 gates are ambiguous (e.g., technical gates pass but "no visitor complaints" is subjective), **Prav is the single decision-maker** — he's the creative director + has eyes on what visitors actually see. Darren's role: present data, not vote. Decision log: the Phase 2 go/no-go result gets logged as a dated line in `docs/phase2-go-nogo.md` with Prav's call + Darren's data summary. Keeps a trail for post-show review.

**Poly-side exhibition-period change approval.** The SQLite-durable-queue + submissions-paused-banner bundle requires a gallery-server change during show week. **Decision: defer the full bundle to post-show (Horizon 3)** unless current gallery-server has a visitor-facing bug that actively needs fixing (none known). Apr 19 post-mortem showed the relay+server recovered cleanly from the 14-hour outage once TD came back; existing behavior is "good enough during show." Moving to Parking Lot item with (Impact: M) (Effort: M) (When: post-show). This resolves the review's concern about exhibition-period risk.

**Matt's touring permission — already in place.** Confirmed per collaborator agreement; not an open item, no Parking Lot entry needed. Touring packaging includes the WAV as-is.

**Human response rota during exhibition hours.**
- **Primary (9:45 AM – 5:15 PM, every day the gallery is open):** Prav on-site. Direct visibility + phone reachable. (Apr 17 Friday was a one-off absence, not a standing pattern; plan assumes Prav on-site every day the gallery is open.)
- **Secondary (show hours):** Darren, via Telegram + phone (518-210-2828 per playbook).
- **Occasional Prav-off-site day (any):** Darren primary; Zoe eyes-on-ground reports to Darren. Fallback modes (noise input, Arena still running, WMP backup) maintain minimum-working even without either primary.
- **After 5:15 PM daily:** both off-site. Alerts still fire (to Darren via Telegram; Prav via email if configured). Either on-call can triage; automated watchdogs continue attempting recovery.

**Alert-channel split (important — not symmetric).**
- **Darren receives real-time Telegram alerts** from `ssd_notify.ps1`. This is the primary incident channel.
- **Prav does NOT use Telegram.** Prav's preferred channel is **email**. Implementation path: daily diagnostic script (already built) has Gmail SMTP stubbed in; when Prav provides a Gmail app password (added to `.ssd_secrets.ps1`), diagnostic email fires daily at 9:15 AM to Prav's address. Same mechanism can be extended to send per-incident email for CRITICAL-severity events; today both Darren and Prav get the daily digest via their respective channels but only Darren gets per-incident pings.
- **Implication for incident triage during show hours:** if something goes wrong at 11:00 AM on a normal day, Darren sees the Telegram alert first and either triages remotely or calls Prav (who's on-site). Prav doesn't see the same real-time alert — he learns from either (a) visible gallery symptom, (b) Darren's phone call, or (c) next morning's diagnostic email. This is why same-day response from Darren is explicit in the rota.
- **Prav-only-online days (Darren unreachable):** real-time Telegram becomes moot. Fallback: Prav learns of an incident via gallery symptom or visitor report; calls Darren when reachable. The system's own watchdogs continue attempting auto-recovery independently.
- **Adding per-incident email to Prav is a Horizon 2 enhancement** (Phase 2.x to be added): extend `ssd_notify.ps1` with an optional Gmail SMTP path for severity=CRITICAL events, gated on Prav's explicit preference ("email me for everything" vs "email daily digest only, no per-incident"). Don't do this unilaterally — Prav decides the noise level he's OK with.

**Reboot interim model if Autologon is NOT configured when Phase 0 deploys.** Before Autologon is fixed: avoid reboots. If a reboot happens anyway (power glitch, Windows hangs) and no human is available to log in, InteractiveToken tasks stall → walls black → alert fires → human sees alert → human instructs Zoe to log in on-site OR uses SSH to force `query session` + remote restart + on-site logon. This is strictly worse than post-Autologon operation; it's what Apr 19 morning looked like. Mitigation: Prav configures Autologon as the FIRST item of the Apr 21 window (5 min of the 15-min slot). Bridging the 1–2 day gap until Apr 21 call: don't voluntarily reboot; trust SSH-accessible recovery path for any involuntary reboot; if auto-login turns out already-enabled (likely per evidence — see Assumptions), this whole paragraph is moot.

**Minimum-mode vs artistic-intent authority.** When the system falls into minimum mode (WMP + one projector), staying in minimum mode during show hours is always acceptable. Returning to optimal mode (all projectors + Ableton + headphones) during show hours requires Prav's judgment call — he's the one facing visitors + curators. Darren does NOT promote out of minimum mode remotely. This avoids the failure pattern of "automated re-optimization breaks during a window that was manageable in simple mode."

**Touring-rights status (Horizon 3 dependency).** H1–H6 TELUS hero renders: rights confirmed per `docs/credits-attribution.md` on Apr 5 commit (sources + license chains tracked). Ambient WAV (Matt's 3-sound loop): permission to use confirmed per collaborator agreement — covered for touring. Briony watercolors: not in the live auto-mode pipeline today (per memory note), so not a touring blocker until re-introduced. No third-party media currently unaccounted for — touring rights are not an open item.

**Phase 2 go/no-go gate (objective criteria to defer to post-show).** Phase 2 proceeds ONLY if ALL of these hold on Apr 22 morning:
- Phase 0 + Phase 1 green (all ACs signed off, no new CRITICAL alerts in prior 48h not already tracked).
- Pre-flight audit item 0.0.e (VRAM headroom) shows median free VRAM ≥ 4 GB under normal TD+SD load for a 2h sample window, i.e., the 4 GB Autolume launch gate can realistically pass.
- No visitor-facing complaints logged in the prior 24h (shows the "do no harm" bar is held).
- Prav explicitly green-lights Phase 2 start (via Signal). Mute-consent does not count.

If any fail: Phase 2 defers in-full to post-show (Horizon 3). Partial slips (e.g., do WMP swap but skip CUDA-12.4) are NOT allowed — bundle stays coherent.

**Evidence threshold to abandon custom watchdog architecture.** If first 48h post-Phase-0 deployment shows alert false-positive rate ≥ 30% (alerts that cleared within 5 min without intervention, divided by total alerts fired), **pause Phase 1, do a root-cause pass on thresholds, then re-evaluate**. If after one threshold-tuning pass false-positive rate is still ≥ 20% at 72h, escalation: disable the new watchdogs, revert to `v-pre-resilience`, open a retrospective question about whether SaaS monitoring is actually the right call after all (contradicting Approach choice A, but with real data). This is the empirical out-clause — the architecture choice isn't dogma.

## Non-goals

- Not redesigning the artistic stack (TD project file, SD prompts, Autolume GAN model).
- Not replacing working components (gallery_server.py, td_relay.py, Resolume composition).
- Not adopting a heavyweight monitoring stack (Prometheus/Grafana/Alertmanager) — keep the ops surface minimal and owned.
- Not eliminating on-site humans (Zoe's curation role stays; this plan reduces technical load, not her presence).
- Not solving the Windows license/version question (stay on current Win 11).
- Not migrating off Task Scheduler (NSSM/systemd/Windows Services deferred to post-tour).

## Constraints

- **Gallery operating windows (per `docs/playbook.md`):**
  - **Public-open hours: 11:00 AM – 5:00 PM local, daily except Friday.** No disruptive changes to visitor-facing components (walls, audio) during public-open hours.
  - **Prav on-site window: 9:45 AM – 5:15 PM.** He's at the gallery for opening prep (≥ 1h before open) and a brief close window.
  - **Safe change windows:** (a) before 10:30 AM (while Prav is arriving + prepping, tolerates disruption if recovery is fast), (b) after 5:15 PM (gallery closed + Prav gone), (c) overnight (lowest risk for anything requiring reboot).
  - **Scheduled Prav-call windows:** 10:30–10:45 AM is the designated "Prav-on-site + gallery-not-yet-open" slot usable for the Apr 21 Resolume-composition-map call and similar coordinated work.
  - "Disruptive changes" = any action that could make walls black or audio silent. Read-only probes + heartbeat additions + task creation are NOT disruptive and can happen anytime.
- **Single 3090 machine.** TD/SD + Autolume contend for 24 GB VRAM; Apr 19 evidence suggests near-limit operation.
- **Interactive user session 1 required** for GUI apps (TD, Arena, Autolume, Ableton). SSH runs in session 0 — GUI actions must go through scheduled tasks with `LogonType = InteractiveToken`.
- **No budget for commercial monitoring SaaS.** Reuse Telegram bot + scheduled tasks.
- **Secrets in `C:\Users\user\.ssd_secrets.ps1`** (local only, not in git). Any new cred goes there.
- **CUDA 11.8 installed;** CUDA 12.4+ required for Autolume ext compile post-MSVC-upgrade. New install must coexist; 11.8 stays until migration verified.
- **Gallery Server currently runs on `poly` (not 3090).** Portable-venue story must not assume this infrastructure.

### Component host map

All components are on the **3090** except gallery_server, which is on **poly**. Meta-watchdog observes only 3090-local components via heartbeat files under `C:\Users\user\heartbeats\`. Gallery server is observed by the existing `Test-GalleryServer` check in `health_probe.ps1` (HTTP probe to `poly:9000/health`), which already runs every 5 min — no heartbeat needed on poly.

**Heartbeat filename contract (authoritative).** The complete, canonical set is shown in the table above under column "Heartbeat file". **Exactly 8 heartbeat files**: `td_watchdog.hb`, `resolume_watchdog.hb`, `autolume_watchdog.hb`, `ableton_watchdog.hb`, `ambient_audio.hb`, `gallery_audio.hb`, `td_relay.hb`, `meta_watchdog.hb`. Health-probe itself does not write a `.hb` file — its liveness is observable via the existing `schtasks /query /tn SSD-Health-Probe` Last Run Time plus its 5-min append to `health_probe.log`; a separate `Test-HealthProbeAlive` check in meta_watchdog.ps1 alerts if `health_probe.log` mtime > 15 min. **There is no `touchdesigner.hb`, `ambient_wmp.hb`, or `relay.hb`** — those would be errors. The manifest enforces this.

**Per-component `max_age_sec` (heartbeat freshness thresholds).** Each value = (expected write interval) × 1.5 + 30s buffer, rounded up:

| Component | Heartbeat file | Write interval | max_age_sec | Rationale |
|---|---|---|---|---|
| td_watchdog | `td_watchdog.hb` | 120s (watchdog's check cycle) | 210 | one cycle + 1.5× buffer |
| resolume_watchdog | `resolume_watchdog.hb` | 120s | 210 | same |
| autolume_watchdog | `autolume_watchdog.hb` | 120s | 210 | same |
| ableton_watchdog | `ableton_watchdog.hb` | 120s | 210 | same |
| gallery_audio.py | `gallery_audio.hb` | 1s (writes state every 1s; piggyback heartbeat) | 30 | 30× the write interval — tolerates GC hiccups |
| ambient_audio (WMP or SoundPlayer) | `ambient_audio.hb` | 3600s (hourly, per existing SoundPlayer pattern) | 7200 | allows one missed hourly tick |
| td_relay.py | `td_relay.hb` | 30s (piggyback on existing relay poll interval) | 90 | 3× the interval |
| meta_watchdog.ps1 (self) | `meta_watchdog.hb` | 120s (its own cycle) | 240 | 2× cycle; detected by health_probe as a special case |

Thresholds validated before Phase-0 synthetic tests fire: run each task for ≥ 30 min, observe actual heartbeat intervals via `(Get-ChildItem <hb>).LastWriteTime` diff, confirm max observed gap < `max_age_sec / 2`. Any component whose real cadence exceeds half its threshold gets its value revised before the plan proceeds to synthetic failure tests.

| Component | Host | Process identity | Heartbeat file | Session | Task |
|---|---|---|---|---|---|
| TouchDesigner | 3090 | `TouchDesigner.exe` | *covered by `td_watchdog.hb` + snapshot freshness check, no separate file* | 1 (Interactive) | SSD-TouchDesigner, SSD-TD-Watchdog |
| StreamDiffusion | 3090 | inside TD (PID 461492 today) | *covered by TD's heartbeat + `td_snap.jpg` freshness* | 1 | (TD) |
| Resolume Arena | 3090 | `Arena.exe` | `resolume_watchdog.hb` (new) | 1 | SSD-Resolume, SSD-Resolume-Watchdog-v2 (new) |
| Autolume | 3090 | `python.exe` with `autolume_autostart.py` in cmdline | `autolume_watchdog.hb` (written by watchdog, new) | 1 | SSD-Autolume (on-demand launcher, exists), SSD-Autolume-Watchdog (new: process-check + VRAM-gate + restart, every 2 min) |
| Ableton Live 12 Suite | 3090 | `Ableton Live 12 Suite.exe` | `ableton_watchdog.hb` (new) | 1 | (Ableton started manually; watchdog monitors) |
| Ambient audio (WMP or SoundPlayer) | 3090 | `wmplayer.exe` (Phase 2) or `powershell.exe` running `gallery_ambient_audio.ps1` (current) | `ambient_audio.hb` (new — same filename regardless of which backend plays) | 1 | SSD-Ambient-Audio |
| gallery_audio.py | 3090 | `python.exe` with `gallery_audio.py` | `gallery_audio.hb` | 1 (no GUI needed, but runs in session 1 for consistency) | SSD-Audio |
| td_relay.py | 3090 | `python.exe` with `td_relay.py` | `td_relay.hb` | 1 (consistent) | SSD-Relay |
| gallery_server.py | **poly** | uvicorn | *(observed via HTTP probe on health_probe, not heartbeat)* | n/a | poly-side service |
| meta_watchdog.ps1 | 3090 | `powershell.exe` with `meta_watchdog.ps1` | `meta_watchdog.hb` (self) | 1 (InteractiveToken) | SSD-Meta-Watchdog (new) |

**Expected-heartbeat set source of truth** = `scripts/heartbeat_manifest.json` (new, committed to repo, deployed alongside scripts). One entry per watched component: `name`, `file`, `max_age_sec`, `alert_key`, `enabled`. Meta-watchdog reads this manifest at each tick; adding/removing a component = editing one file in git. **No other file name is valid** — if a script writes to a `.hb` name not in the manifest, meta-watchdog ignores it; if the manifest references a file that doesn't exist, meta-watchdog alerts.

## Assumptions

- SSH reverse tunnel (SSD-SSH-Tunnel task) stays up — infrastructure already hardened.
- Telegram bot chat (TELEGRAM_CHAT_ID) is monitored by **Darren only** during show hours (Prav uses email for summaries, not Telegram).
- Prav reachable by phone during gallery hours (validated by Apr 19).
- Windows Task Scheduler remains the task runner for this show (not switching mid-show).
- GPU has ≥2 GB VRAM headroom for a new Autolume instance alongside running TD/SD — TBD, may need explicit budgeting in Phase 1.
- `DEFERRED: which venues are committed post-Impact?` (Horizon 3 items adapt to whatever list emerges; not blocking.)
- `DEFERRED: does Prav have a pre-mixed ambient WAV ready for WMP auto-mode?` (Affects Phase 2 timing; plan proceeds either way.)
- **Default Ableton runtime mode during exhibition hours: WASAPI-visible (not ASIO).** Assumed true based on: (a) current Ableton config has been running since Apr 13 via standard Windows audio routing per Prav's ops, (b) the auto-mode experience doesn't require ASIO's ultra-low latency (ambient sound is fine at default WASAPI latency), (c) ASIO is reserved for live-performance events that Prav explicitly switches to and is present for. Phase-1.4 auto-failover can rely on this default. **If Prav confirms otherwise in the Apr 21 call, AUDIO_FAILOVER_ENABLED stays off by default and we'd need per-mode config — documented as alternative path in playbook appendix.**
- **Phase 2.4 ambient fallback WAV delivery.** Primary plan: **Prav provides a newly-mixed WAV by Apr 22 EOD**, stored at `C:\Users\user\ambient-audio\<name>.wav` on the 3090 (via scp or Drive download). Interim fallback if Prav can't deliver by Apr 22: use the **existing `C:\Users\user\Downloads\Salish Dreaming 21 min.wav`** that `gallery_ambient_audio.ps1` was already configured to play (verified present in the ps1 file on Apr 19). This file exists today + was the production ambient source until the PS SoundPlayer died Apr 16. Functionally sufficient for the minimum-config mode Prav described. Decision deadline: Apr 23 AM — if new mix not delivered, Phase 2.4 proceeds with existing WAV; Prav can swap the file later without plan re-work.

### Account + privilege prerequisites (validated before Phase 0)

- **3090 runtime account:** all scheduled tasks (existing + new) run as **`DESKTOP-37616PR\user`** (SID `S-1-5-21-3151823897-1990050577-3676455961-1000`), same account that's logged into session 1 and owns the TD/Resolume/Autolume processes. This account is in the local Administrators group — confirmed by today's successful `schtasks /change`, `Copy-Item` under Program Files, and `Stop-Process -Force` calls via SSH (SSH session inherits the account's admin token).
- **Meta-watchdog account:** uses the same `user` account via `LogonType = InteractiveToken` (matches SSD-Health-Probe pattern). Rationale over SYSTEM: meta-watchdog reads `C:\Users\user\heartbeats\` + `scripts/heartbeat_manifest.json` + sources `C:\Users\user\.ssd_secrets.ps1` for Telegram creds. SYSTEM can't access user-profile files without explicit ACL changes; keeping everything under `user` avoids that complication.
- **Admin operations required for Phase 0:** `gpresult /r`, `Set-ItemProperty` under `HKLM:\...WindowsUpdate\AU`, `schtasks /change`, `schtasks /create /xml`. All confirmed accessible from SSH as `user`. Rollback operations (task disable, git checkout + scp) use the same path and are always available as long as SSH tunnel is up.
- **Secrets already present:** `C:\Users\user\.ssd_secrets.ps1` contains `$env:TELEGRAM_BOT_TOKEN` and `$env:TELEGRAM_CHAT_ID` (verified today). No new secrets required for Phase 0 or Phase 1. Phase 2's optional email delivery uses `$env:GMAIL_USER` + `$env:GMAIL_APP_PASSWORD` which are absent today; diagnostic script silently skips email if missing (confirmed today). Adding Gmail creds is a Prav-approval, 2-line append to the secrets file — not a prerequisite.
- **Rollback access during incident:** even if meta-watchdog or a new task misbehaves, the SSH reverse tunnel (`windows-desktop-remote`) is maintained by `SSD-SSH-Tunnel` task which this plan does not modify; rollback via `schtasks /change /disable` and `git checkout v-pre-resilience` always reachable.

### Session 1 availability (auto-login assumption)

All new tasks with `LogonType = InteractiveToken` require `DESKTOP-37616PR\user` to be logged into interactive Session 1 when the task fires. Evidence it currently is: SSD-TouchDesigner, SSD-Resolume, explorer.exe, winlogon.exe are all in Session 1 across reboots (verified today via `Get-WmiObject Win32_Process | Where SessionId=1`), and the stack recovers from overnight reboots every morning without a human logging in manually → **Windows auto-login is already configured** for the `user` account.

AC for this assumption (added to Phase 0): capture current auto-login state via `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'` — expect `AutoAdminLogon = 1`, `DefaultUserName = user`, `DefaultPassword` present. If the assumption is FALSE (auto-login disabled), all `InteractiveToken` tasks require manual human login after every reboot — a known hole that must be fixed before Phase 0 completion.

**Credential ownership for Autologon configuration:** the `DESKTOP-37616PR\user` account password is held by Prav (machine owner). If Phase 0 AC reveals auto-login not configured, I cannot set it up unilaterally (Sysinternals Autologon requires typing the password). Flow: Phase 0 captures the current state + alerts; if not configured, a 5-min item is added to the Apr 21 Prav call (he types password into Autologon.exe while Darren watches via screen share; configuration verified by a controlled reboot during the pre-opening window). Authority already implicit: Prav has green-lit the full hardening plan by this conversation's existence. Recovery path formally documented in playbook appendix on completion.

If Session 1 is ever absent for any reason (auto-login fails, user manually logs off), `InteractiveToken` tasks will be stuck in "ready to run when user logs on" state — NOT fail with error. Detection: meta-watchdog will see stale heartbeats, alert. Recovery: SSH in, use `query session` to confirm no session 1, reboot (which triggers auto-login). Document this failure mode in playbook appendix.

---

## Approach

**Options considered.**

**A. Roll our own — extend current scripts.** Heartbeat files + meta-watchdog + standardized component contract on top of existing `health_probe.ps1` + Task Scheduler + Telegram. Pro: ~60% already built; cognitive load stays low; owned. Con: we're the only users.

**B. Adopt Prometheus + Grafana + Alertmanager.** Industry standard. Pro: mature patterns, rich dashboards. Con: overkill for 6-component install on single machine; Windows-awkward install; new deps add surface area for the exact "silent death" class we're solving.

**C. Managed/SaaS monitoring (Datadog, UptimeRobot).** Pro: external eye, no self-host. Con: budget, outbound-network dependency from 3090, doesn't cover process-level detail.

**Chosen: A.** The Apr 19 failure wasn't "current pattern is wrong" — it was "current pattern has holes": watchdogs die silently, no one watches the watchers, no standardized contract per component. Fix at this level. Rewrite risk >> extension risk during an active show.

**Architectural shape.**

```
┌────────────────────────────────────────────────────────────────┐
│                     META-WATCHDOG (new)                        │
│  Runs every 2 min. Reads heartbeat files for all tasks.        │
│  Alerts if any heartbeat stale. Never restarts (alert-only).   │
└────────────────────────────────────────────────────────────────┘
          │ reads                             │ alerts via
          ▼                                   ▼
┌───────────────────────────┐        ┌────────────────────┐
│ heartbeats/ dir           │        │ ssd_notify.ps1     │
│  td_watchdog.hb           │        │ (existing Telegram)│
│  resolume_watchdog.hb     │        └────────────────────┘
│  autolume_watchdog.hb     │
│  ableton_watchdog.hb      │
│  ambient_audio.hb         │  written by
│  gallery_audio.hb         │     each long-lived task
│  td_relay.hb              │  (see canonical table)
│  meta_watchdog.hb         │
└───────────────────────────┘
          ▲
          │ heartbeats written by
┌────────────────────────────────────────────────────────────────┐
│ PER-COMPONENT WATCHDOGS (existing + new)                       │
│  SSD-TD-Watchdog        ─ restarts TD, writes td_watchdog.hb   │
│  SSD-Resolume-Watchdog  ─ restarts Arena (NEW), writes hb      │
│  SSD-Autolume-Watchdog  ─ restarts Autolume w/ backoff         │
│  SSD-Ableton-Watchdog   ─ checks audio session, writes hb      │
│  SSD-Audio (monitor)    ─ writes hb + audio state JSON         │
│  SSD-Relay              ─ writes relay.hb                      │
└────────────────────────────────────────────────────────────────┘
          ▲
          │ observed by
┌────────────────────────────────────────────────────────────────┐
│ HEALTH PROBE (existing scripts/health_probe.ps1, extended)     │
│  Every 5 min: process checks, snapshot freshness, audio level, │
│  audio_silent (added today), gallery_server health.            │
│  Reports FAIL → ssd_notify with 30-min cooldown + digest.      │
└────────────────────────────────────────────────────────────────┘
```

**Key invariants.**

1. **No silent death.** Every long-lived task writes a heartbeat at a cadence documented in the heartbeat manifest; cadences range from 1s (fast poller like gallery_audio) to 3600s (existing hourly SoundPlayer heartbeat). Meta-watchdog compares each file's mtime against its `max_age_sec` threshold and escalates. There is no universal interval — per-component values in the threshold table are authoritative. Eliminates the "task shows running but process is dead" anti-pattern.
2. **Silence is a signal.** Mic silence, log silence (no new snapshot uploads, no OSC deliveries), state-file staleness — all alertable.
3. **Graceful degradation.** When a component fails, the system continues in a reduced mode without waiting for a human. Documented fallback mapping per component.
4. **Minimum functioning mode always reachable.** Per Prav: WMP + one main projector + ambient speakers is the floor.
5. **Updates are changes.** Windows Update, driver update, TD/Resolume/Autolume upgrade — all treated as deliberate deployments, not background events. Locked during show.
6. **Every failure class has a runbook entry.** The symptom → action table in `playbook.md` is the canonical inventory. New failure → new row, same day.

### Authoritative audio silence definition

The gallery has three possible output paths: **room speakers** (RME USB audio device), **projector HDMI audio** (not used for program audio — carries visual-only), and **wireless headphones** (Bluetooth). Because different operating modes route audio to different devices, no single check is authoritative. Rule:

- **mic_silent** = today's detector. `ssd_audio_state.json.vol_max_60s < 0.002` for ≥ 60s. Catches "speakers dead" (mic is in the room).
- **output_silent** = WASAPI peak level on the **default output device** (tracks whichever device is currently active for Ableton/WMP output). `GetSession.AudioMeterInformation.PeakValue < 0.005` for ≥ 30s, sampled every 2s. Catches "headphones active but no audio reaching them" (mic wouldn't detect this).
- **Composite silence** (what triggers `audio_silent` CRITICAL alert) = **both** `mic_silent` AND `output_silent` true. Either alone is WARN-severity only. This avoids false positives when the gallery runs in headphones-only mode (mic silent, headphones playing = not silent).
- **Ableton render device identification.** Don't attempt to parse Ableton's preferences. Instead, use the Windows Core Audio API (IAudioSessionManager2) to enumerate all active audio sessions and locate the one whose `DisplayName` or `Process.Name` matches `"Ableton Live 12 Suite"`. That session's `AudioMeterInformation.PeakValue` is Ableton's current output level, regardless of which physical device (speakers / headphones / HDMI) Ableton routes to — the session is bound to the process, not the device. If no matching session found → Ableton is not producing audio (either closed or routed via a non-system path like ASIO that WASAPI doesn't see). Treat "no session found" for an alive Ableton process as WARN-severity `ableton_asio_maybe` (not CRITICAL), since Ableton in ASIO mode is a legitimate config for live performance and would bypass WASAPI.
- **Auto-failover trigger** (Phase 1.4 Ableton→WMP swap) = Ableton session found via the above enumeration AND its peak value < 0.005 for ≥ 30s AND Ableton Live process still alive. Fires WMP fallback + info Telegram. Does NOT trigger if Ableton session is simply not visible (avoids overriding live performance mode).

## Implementation Steps

### Phase 0 — Immediate (today, before Apr 20 9:45 AM opening)

Goal: close the three worst holes Apr 19 exposed (Windows Update cascade, silent-death watchdogs, no Arena watchdog). Prefixed by a pre-flight audit that captures the environmental ground truth the rest of the plan needs.

0.0. **Pre-flight environment audit.** Captures seven current-state values that **intentionally cannot be pre-answered in the plan** — they are values that exist only on the live 3090 + poly + in Prav's head, and verifying them mid-plan would be speculation. Output: `docs/environment-audit-2026-04-19.md` committed to repo. Each value either (a) confirms a plan assumption, (b) updates a plan value in place (specifically: `$SSD_DEFAULT_OUTPUT_DEVICE_NAME`, `$SSD_SUBMISSION_DB_PATH`, Ableton-driver-mode, AudioDeviceCmdlets-install-path choice), or (c) triggers a documented plan-trim (move an item to Parking Lot + note here). Gate: Phase 0.1 onward does not start until this audit completes and each triggered trim is recorded in this plan.

**Note to reviewer:** questions of the form "what is the exact X name?" or "is Y installed?" or "where is Z provisioned on poly?" are all answered by Phase 0.0's audit output, not by the plan prose itself. This is a deliberate plan-design choice: the plan commits to the audit step and commits to how results are consumed; attempting to pre-fill those values here would require unverified guesses. If a sub-item needs to block *execution* rather than *planning*, it's listed as such in the sub-step's gate condition.

   0.0.a. **AutoAdminLogon state.** `Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' | Select AutoAdminLogon, DefaultUserName, DefaultDomainName`. **✅ CONFIRMED Apr 19 17:xx UTC: `AutoAdminLogon = 1, DefaultUserName = user`.** No Prav credential entry required for Phase 0 — InteractiveToken tasks will survive reboots via auto-login. The conditional "if 0 → Apr 21 call" branch is resolved and does not apply.

   0.0.b. **Canonical audio output device name.** `Get-CimInstance Win32_SoundDevice | Select Name, Manufacturer, Status` + `Get-PnpDevice -Class AudioEndpoint | Where Status -eq 'OK'`. Produces the list of audio devices. Prav designates one as canonical during Apr 21 call (until then, script falls back to whatever Windows-default is, no pinning). Recorded as `$SSD_DEFAULT_OUTPUT_DEVICE_NAME` in `scripts/.ssd_audio_config.ps1`. If designation not made by end of Apr 21 window → "Default output device pinning" sub-feature (new `SSD-Audio-Device-Pin` task) moves to Parking Lot; silence detection operates on whichever device Windows defaults to, with a known-accepted risk of false-positives on device switch.

   0.0.c. **AudioDeviceCmdlets module availability.** `Get-Module -ListAvailable AudioDeviceCmdlets`. If present → use module's `Set-DefaultAudioDevice`. If not → either `Install-Module AudioDeviceCmdlets -Scope CurrentUser` (PSGallery trusted) or fall back to raw MMDeviceEnumerator via a small C# helper compiled inline. Record chosen path in audit doc.

   0.0.d. **Ableton's current output driver mode.** Inspection by Prav during Apr 21 call: open Ableton → Preferences → Audio → Driver Type. Expected: "MME/DirectX" or "WASAPI". If "ASIO" → note which device. This is the default auto-mode state that `AUDIO_FAILOVER_ENABLED` will be gated against; if ASIO is the default, failover stays off by design (see ASIO policy in Approach section).

   0.0.e. **Current VRAM headroom under normal load.** 5-min sample: `nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader,nounits -l 60 | head -6`. Expected: free ≥ 8 GB when TD+SD running without Autolume (today's state). Document observed min/max/median. If median free < 4 GB under normal load → the 4 GB Autolume launch gate will never pass in production, meaning Phase 2 Autolume restore is infeasible on shared GPU; that's a design signal (not a plan failure) — move Autolume restore to Parking Lot and add "GPU-budget-split between TD and Autolume" as a post-show architecture item.

   0.0.f. **Current Resolume composition layer structure (read-only probe).** OSC query to Arena: `/composition/layers/size` + iterate `/composition/layers/{n}/clips/selected/name` + `/composition/layers/{n}/name` for n=1..size. Produces a snapshot of current layer state. Pre-populates the Apr 21 call so Prav walks into it with the current reality already documented, not spent figuring it out. If OSC query fails (Arena OSC not enabled, or unreachable from 3090 scripts), manual snapshot via screenshot during the Apr 21 call; either way the layer map lands in `docs/resilience-spec.md` as appendix.

   0.0.g. **Poly filesystem + permissions probe for SQLite path.** `ssh poly "stat /var/lib/ssd-gallery 2>&1 || ls -la ~/ssd-gallery-data"`. Confirms where the SQLite DB will live + writable by the `ssd-gallery` service user. Records exact path in plan + sets the `SSD_SUBMISSION_DB_PATH` config value. If path isn't provisioned → `mkdir -p + chown` as a Phase 2 pre-step (poly has sudo or user-owned paths — low risk).

0.1. **Block Windows Update.** Group Policy `NoAutoUpdate=1` + pause via Settings + set connection to metered. Verify via `gpresult /r`.

0.2. **Block NVIDIA auto-updates.** Disable GFE auto-update; disable `NVIDIA Display Container LS` auto-driver-update scheduled tasks.

0.3. **Heartbeat-file standard.** Create `C:\Users\user\heartbeats\`. Extend each script to write its canonical `.hb` file **at the cadence listed in the per-component threshold table** (not a single uniform interval — ranges from 1s for `gallery_audio.py` through 3600s for `gallery_ambient_audio.ps1`). Rule: each script writes at frequency ≥ (max_age_sec / 3) so transient delays don't false-alert. Scripts to extend (heartbeat filename is authoritative from the canonical table — each script writes exactly one `.hb`):
- `td_watchdog.ps1` writes `td_watchdog.hb` (new file write at end of each 120s cycle).
- `gallery_ambient_audio.ps1` writes `ambient_audio.hb` (keep existing hourly heartbeat semantics; replace current `ssd_ambient_audio.log` heartbeat-line with a proper `.hb` file write).
- `gallery_audio.py` writes `gallery_audio.hb` (already writes state JSON every 1s; add `.hb` file `os.utime` in same loop — effectively zero cost).
- `td_relay.py` writes `td_relay.hb` (add heartbeat write every 30s alongside existing poll).
- new `resolume_watchdog.ps1` writes `resolume_watchdog.hb` (0.4).
- new `autolume_watchdog.ps1` writes `autolume_watchdog.hb` (Phase 2 pre-req; stubbed in Phase 0 with `enabled: false` in manifest).
- new `ableton_watchdog.ps1` writes `ableton_watchdog.hb` (stubbed Phase 0, active Phase 1).
- new `meta_watchdog.ps1` writes `meta_watchdog.hb` (0.5).

0.4. **Resolume process watchdog.** New `scripts/resolume_watchdog.ps1` matching TD pattern. Relaunches Arena via `schtasks /run /tn SSD-Resolume` when `Get-Process Arena` returns empty; writes heartbeat; 60s backoff after restart; exponential backoff to max 5 restarts/hour (see Risks). Register `SSD-Resolume-Watchdog-v2` task using the same XML pattern as `SSD-Health-Probe` (verified Apr 19): `LogonType = InteractiveToken`, `UserId = S-1-5-21-3151823897-1990050577-3676455961-1000` (the `user` account), `RunLevel = HighestAvailable`. This ensures the subsequently-spawned `SSD-Resolume` task (which has `/ru user` and needs a GUI for Arena) lands in Session 1. SSD-Resolume task itself remains as-registered (Interactive only logon mode).

0.5. **Meta-watchdog.** New `scripts/meta_watchdog.ps1`. Scheduled every 2 min. Reads `scripts/heartbeat_manifest.json` (the source of truth — see Constraints section "Component host map"). For each entry where `enabled: true`, if the target `.hb` file is missing OR its mtime older than the entry's `max_age_sec` → fire `meta_<alert_key>_stalled` Telegram alert. Writes `meta_watchdog.hb` itself. Honors the maintenance-mode lock (see 0.8 below). **Strictly alert-only — never kills or restarts processes.** All corrective action (restart) is owned by the individual per-component watchdogs (td_watchdog, resolume_watchdog, etc.); meta-watchdog's role is to catch the case where one of those watchdogs itself has gone zombie. Task runs as **`DESKTOP-37616PR\user` with `LogonType = InteractiveToken`** (matches SSD-Health-Probe pattern — single authoritative configuration for all new tasks in this plan; earlier drafting said "session 0 / SYSTEM" but user-account + InteractiveToken is the committed choice so meta-watchdog can read `C:\Users\user\heartbeats\` and source `.ssd_secrets.ps1` without ACL surgery).

0.6. **Audit current watchdogs for zombie state.** Kill orphaned python/powershell procs from prior sessions, ensure fresh watchdog procs running. Document current PID + start time in playbook appendix.

0.7. **Commit + push.** Deploy to 3090. Tag commit `v-pre-resilience` immediately before Phase 0 deployment begins (enables full revert). Verify heartbeat files appearing. Synthetic tests:
- `Stop-Process Arena -Force` → Arena restored within 3 min.
- Kill gallery_audio python proc (not task) → meta-watchdog Telegram alert within 10 min.

0.8. **Maintenance-mode lock.** New `scripts/maintenance.ps1 -Minutes <N> -Reason "<text>"` creates `C:\Users\user\maintenance.lock` (JSON: `{"until": "<ISO8601>", "reason": "..."}`). Meta-watchdog + `ssd_notify.ps1` check for this file on each alert attempt; if `until > now`, suppress **new** alerts (keep logging FAILs to probe log but don't Telegram). Auto-expires. Maintenance lock itself triggers one info Telegram message on creation ("maintenance window opened: \<reason\> until \<time\>") and one on expiry. Prevents alert-spam during planned deployments, reboots, Autolume restarts. Separate scheduled task `SSD-Maintenance-Cleanup` runs every 5 min and removes the lock file if `until` is past.

### Phase 1 — Resilience hardening (Apr 20–24, low-traffic windows)

Goal: standardize per-component contract, add graceful degradation, reduce alert noise.

1.1. **Component Contract template** at `docs/component-contract-template.md`. For each service: process identity, health check, heartbeat path + interval, restart procedure + backoff, graceful-degradation behavior, escalation (alert severity + key).

1.2. **Apply contract to 8 subsystems** in new `docs/resilience-spec.md`: TouchDesigner, StreamDiffusion (within TD), Resolume Arena, Autolume, Ableton Live, WMP ambient (new), gallery_audio, td_relay. One markdown section per.

1.3. **Audio session-level silence detection.** Today's detector uses mic pickup — misses headphone output. Add Windows Core Audio API check of default output device peak volume. Complements mic check; together catches room-speakers-only and headphone-only modes.

1.4. **Graceful degradation mapping + implementation:**
- Autolume down → SD continues on `noise1` fallback (proved Apr 19 — already implicit in TD project; no new work).
- Ableton silent > 30s → auto-switch audio to WMP Matt's loop. Trigger condition detailed under "Authoritative audio silence definition" (Approach). Implementation: new `scripts/audio_failover.ps1` invoked by health_probe when Ableton WASAPI session peak < 0.005 for 30s + Ableton process alive. Launches WMP via `SSD-Ambient-Audio` and sends info Telegram "Ableton silent, switched to WMP fallback". **Hard prerequisite: Phase 2.4 (WMP+WAV ambient) must be deployed and verified working first.** Feature flag in code: `AUDIO_FAILOVER_ENABLED` env var, defaults `false`. Phase 1.4 lands the code with the flag off; Phase 2.4 flips the flag on after the WMP fallback is validated. If auto-failover fires but WMP launch fails (task returns non-zero, or WMP process not alive within 30s), fire `audio_failover_broken` CRITICAL Telegram alert and do NOT retry within the same hour — prevents fallback-loop thrashing. Also disabled when Ableton is in ASIO mode (no WASAPI session visible — see ASIO policy below).

  **Ableton handling during failover and recovery path.** When failover fires: Ableton process is NOT stopped. Rationale: stopping Ableton's process (Stop-Process) can leave the `.als` session state in a weird save-prompt state, risks corrupting the live set on next open. Instead, WMP is launched on the same default output device; since Ableton is already proven silent at failover time, no audible double-audio exists. **If Ableton's output later recovers (peak > 0.005 in the same session) while WMP is also playing, the result would be mixed audio** — acceptable as an audibly-obvious signal to a human that something needs attention. **Recovery is manual, not automatic.** To return to Ableton: human (Prav or Darren via SSH, during a safe window) runs `scripts/audio_revert.ps1` which stops WMP (`Stop-Process wmplayer`), clears the failover state file, sends info Telegram "reverted to Ableton". Daily diagnostic flags `failover_state = WMP` prominently so a missed revert gets caught next morning. The auto-switch-back-to-Ableton path is explicitly out of scope — too many ambiguous states (ASIO mode, performance mode, transient silence).

- **Ableton ASIO-mode operational policy.** In live-performance mode, Ableton may use ASIO drivers directly (bypasses WASAPI). When the WASAPI session enumerator finds no session matching Ableton's process, two interpretations are possible: (a) Ableton is legitimately in ASIO / live mode, or (b) Ableton is routed to a device that's gone offline. We can't distinguish these from the outside without parsing Ableton's internal state. Policy: treat "no session found + Ableton process alive" as **WARN `ableton_asio_maybe`** (not CRITICAL); include in daily diagnostic so a human notices day-over-day; **auto-failover to WMP is DISABLED** under this condition. Rationale: wrong-silencing a live-performance Ableton is worse than missing a genuine silent-Ableton failure, because the performer would notice + fix within seconds but an auto-switch could interrupt a concert. Live performance mode is always human-attended; silence detection for ASIO-mode Ableton is explicitly out of scope for this plan and documented in playbook as "on-site human monitors live performance audio".

### Default output device pinning

Windows can re-elect the default output device when hardware connects/disconnects (common with Bluetooth headphones + USB DACs). If silence detection + failover are targeting device X but Windows has re-routed to device Y, we get false-positive silence alerts on X while audio is actually playing on Y, or vice versa. Mitigation: pin the default output to a specific canonical device at every logon.

- **Canonical output device for auto-mode:** the RME USB audio interface driving the gallery speakers. **Precise device name: TBD during Apr 21 Prav call** (varies by USB enumeration order; Prav has physical access + knows the brand/model). Recorded in `scripts/.ssd_audio_config.ps1` as `$SSD_DEFAULT_OUTPUT_DEVICE_NAME = "..."`.
- **Pinning mechanism:** new `scripts/set_default_audio.ps1` invoked at every logon via new `SSD-Audio-Device-Pin` task. Uses PowerShell module `AudioDeviceCmdlets` (or raw MMDeviceEnumerator calls if module unavailable) to `Set-DefaultAudioDevice` matching the canonical name. Logs result + writes `audio_device_pin.hb` heartbeat.
- **Live-performance-mode override:** if Prav switches Ableton into ASIO mode on a different device, pinning is bypassed (ASIO doesn't touch default-device routing). No conflict.
- **Failure mode:** if the canonical device is missing (unplugged, dead, renamed), pin task fails visibly → Telegram `audio_device_missing` CRITICAL; operating in whatever-Windows-picks fallback. This condition is documented in playbook's symptom table as "speakers silent on opening" with USB-replug as the on-site action.
- **Resolume fallback layers — 15-min Prav call, scheduled for Apr 21 during the 10:30–10:45 AM window (Prav on-site, gallery not yet public-open).** Owner: Prav (holds composition state + authority to modify). Darren joins via Signal/WhatsApp to capture. Goal: document current composition via Resolume's OSC (`/composition/layers/size` + each layer's `name` and `clip[0]/name`), then decide 3 questions: (a) **TD NDI layer** — confirm layer number (assumed 4 per Apr 18 runbook), record authoritative number in playbook; (b) **hero video fallback** — confirm whether H1–H6 TELUS renders already live as clips in the composition; if yes, record which layer + clip slots; if no, Prav adds during that same 15-min window from the shared Drive + local cache at `C:\Users\user\SSD-heroes\` (asset sync task to be created if needed); (c) **OSC crossfade control** — test `/composition/layers/{N}/crossfader/values` or clip opacity toggles live; confirm which control swaps TD NDI out and hero video in. Output of the call: 1-page "Resolume composition map" appendix added to `playbook.md` + concrete implementation of the fallback CHOP in `scripts/resolume_degradation.ps1`.

  **If the Apr 21 call does not produce a complete map** (assets missing, or call cut short, or Prav determines the current composition can't accept a fallback layer without risky changes), the following items are **explicitly moved to Parking Lot** before Phase 1 closes: "SD fps<1 → Resolume hero-video fallback" and "TD-dead → Resolume last-frame fallback". Phase 1.4 ships WITHOUT these two degradations (the Autolume→noise path already covers the most common failure and is Phase-0-sufficient). A follow-up "composition-map resolution" work item is added to Horizon 3 / Parking Lot with priority (Impact: M) (Effort: L) (When: post-show) — Prav can make composition changes during post-show quiet period without show-pressure.
- **TD dead > 3 min → Resolume shows last-good-output layer.** Same Apr 21 call covers this. Depends on a "hold last frame" or static-fallback layer in the composition. Same disposition: if not already present and Prav can't add on the call → moved to Parking Lot; interim behavior is what Resolume does natively (NDI input caches last frame for ~3s then goes black). This is the known Phase-0 degraded mode we accept until the Apr 21 call resolves it.
- **Pre-rendered hero video assets — ownership and runtime location.** Per CLAUDE.md the hero video set is H1–H6 from the TELUS render batch, stored in the project shared Drive folder (`https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr`). For runtime use they must be present locally on the 3090 (Resolume loads clips from disk). Local path convention: `C:\Users\user\SSD-heroes\H1.mp4` through `H6.mp4`. **Owner: Prav** (original renderer; final curated set of 6). **Sync task: new `SSD-Heroes-Sync`** (low priority, runs once weekly; rsync-equivalent via `rclone` if Drive API configured, else manual copy during setup). Sync task is scope-creep — deferred to Parking Lot unless clips are missing on Apr 21. For Apr 21 call: Prav verifies locally; if missing, manual drag-drop from shared Drive via his machine → onto 3090 desktop.
- Relay down > 5 min → visitor page shows "submissions paused" banner. **Requires change to `gallery_server.py` + `web/visitor.html` on poly**. Poly is Darren's account; deployment path is `git pull` + `systemctl --user restart ssd-gallery`; tested deploy window = any time outside gallery hours, ideally 5 PM – midnight local. Implementation: server checks `time_since_last_td_next_poll > 300s` in a new `/status` endpoint; visitor page polls `/status` every 30s and shows a non-blocking banner when `submissions_paused: true` while still accepting prompts (queued for when relay recovers).

  **Submission durability during pause.** Today the server keeps prompts in an in-memory structure (monotonic `td_prompt_seq` counter + queue). A server restart during a relay outage would drop queued submissions silently. As part of this change: **migrate prompt queue to SQLite-backed persistence** on poly (`/var/lib/ssd-gallery/prompts.sqlite` or similar under the service's data dir; confirm exact path during implementation). Every `POST /prompt` writes to SQLite before responding; every `GET /td/next` reads from SQLite. Durable across crashes + reboots + `systemctl restart`. Schema minimal: `(seq INTEGER PK, prompt TEXT, submitted_at TEXT, consumed_at TEXT NULL)`. Consumption = setting `consumed_at` when the relay acknowledges (new `POST /td/ack` endpoint, optional). Rollback: keep the in-memory path alongside as a fallback for one release cycle.

  **Deferred to late-Phase-1 or Phase 2** — requires poly deploy window + FE change + SQLite migration. Not blocking Phase 0. If Phase 1 time-pressured, the whole poly-side bundle (banner + durability + ack endpoint) moves to Parking Lot as one item — they belong together.

1.5. **Alert digest / de-dup.** Extend `ssd_notify.ps1`: same alert key ≥3 times in 1h → digest mode. Suppress individual alerts; fire "still down (since X, N alerts suppressed)" every 6h until key clears. Fixes Apr 18–19 30-min spam pattern.

1.6. **Daily state snapshot.** `scripts/daily_snapshot.ps1` at 4 AM on the 3090. Runs on same machine as TD, so MCP reachable via `http://127.0.0.1:9981`. Captures (in order, each step independent + non-fatal):
- `visitor_queue` contents via TD MCP `execute_python_script` — 5s timeout; if MCP unreachable, write `visitor_queue_capture_FAILED.txt` with the error and continue.
- prompt_sequencer runtime state (slot weights, current concept) via MCP — same timeout/fallback pattern.
- Copy of current TD .toe file (`Copy-Item` on `SSD-exhibition.toe` — independent of MCP).
- Last 500 lines of `health_probe.log`, `td_relay.log`, `autolume_run.log`, `ssd_notify.log` (plain file copies, always succeed).
- Files for last 24h under `C:\Users\user\heartbeats\` (snapshot of last-observed liveness).

Stored under `C:\Users\user\snapshots\YYYY-MM-DD\`. 30-day retention (cleanup task `SSD-Snapshot-Cleanup` deletes dirs older than 30 days). Snapshot success/failure summary written to daily_diagnostic output so morning email captures any gaps.

1.7. **`docs/resilience-spec.md`** — committed spec doc. Derived from this plan. Lives next to playbook.md. Update playbook's Part 4 to link.

### Phase 2 — Recovery + restoration (Apr 22–26, quiet windows)

Goal: restore full artistic stack (Autolume), replace Ableton in auto mode, verify system health.

2.1. **CUDA 12.4 install** side-by-side with 11.8. Set `CUDA_HOME`. Delete `torch_extensions` cache. Verify `nvcc --version`.

2.2. **Rebuild Autolume CUDA extensions** in isolation — single process, verbose. Verify 3 .pyd files produced. Validate via Python import + `_init()` returns True.

2.3. **Revert `params.use_custom = False`** patch. Keep `visualizer.py` patch (real upstream bug, still needed). **Before re-triggering SSD-Autolume, enforce VRAM gate:** query `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits`. Require **≥ 4096 MiB free**. Rationale: Autolume's StyleGAN2 model loads ~2 GB; TRT engine init pushes ~0.5 GB transient; +1.5 GB headroom keeps TD/SD from VRAM-starving during Autolume spin-up. If threshold not met, log WARN, defer Autolume launch by 10 min + retry (up to 3 retries); if still below, alert `autolume_vram_insufficient` and leave Autolume off (walls stay in `noise1` fallback). Codify the gate in `scripts/autolume_watchdog.ps1` as `Test-VRAMHeadroom`. Verify NDI publishes real frames, TD ndiin2 reads non-zero pixels.

2.4. **Pre-mixed ambient WAV via WMP.** Prav provides mix. `scripts/ambient_wmp.ps1` launches WMP with WAV on loop + heartbeat. Replaces PS SoundPlayer (dead since Apr 16). Repoint `SSD-Ambient-Audio` task. Ableton becomes live-performance-only.

2.5. **`sfc /scannow`** at 3 AM. Log result. Document in postmortem appendix.

2.6. **Persist ndiin2 binding.** Current `DESKTOP-37616PR (Autolume Live)` binding is runtime-only. Save TD .toe so it survives restart. Add startup-time binding check in TD that auto-corrects hostname drift.

2.7. **Apr 19 incident postmortem** in `playbook.md` appendix: timeline, root causes, fixes, lessons, new invariants. Cross-links to this plan + spec.

### Phase 3 — Tour-readiness (post-show, Apr 27+)

Goal: shippable installation without a team member on-site.

3.1. **Macrium / Clonezilla backup image** of working 3090 config. Stored off-3090. Recovery-to-bare-metal verified in VM.

3.2. **Non-technical staff training pack.** Loom walkthrough (~15 min); laminated single-page quick-ref (today's DRAFT manual finalized); troubleshooting decision-tree poster near the tower.

3.3. **Deploy-elsewhere package.** Scripted install for new 3090-equivalent box: TD + .toe deploy, Resolume + composition, Autolume + model, all SSD-* tasks, secrets template, SSH tunnel config.

3.4. **Gallery server portability.** Port gallery_server.py to 3090, or provide cloud-host-in-a-box for remote venues.

3.5. **Knowledge graph entities.** Register Zoe (pending consent), components, runbook docs as SpecDocs, failure modes as Risks with mitigation links.

3.6. **Post-show update window.** Unblock Windows/NVIDIA/TD/Resolume. Apply pending patches. Re-verify full probe cycle. Capture new Macrium image.

---

## Acceptance criteria

**Phase 0:**
- [ ] **Pre-flight audit** (Phase 0.0) committed as `docs/environment-audit-2026-04-19.md` with all 7 sub-items (0.0.a through 0.0.g) answered; any resulting Parking Lot moves recorded in this plan.
- [ ] Windows Update auto-install disabled — `gpresult /r` + Settings shows paused; no Microsoft Update scheduled tasks active next 7 days.
- [ ] NVIDIA GFE auto-update off — verified in GFE settings + no pending driver notifications.
- [ ] `scripts/heartbeat_manifest.json` committed + deployed; meta-watchdog reads it at startup and logs the expected set.
- [ ] `C:\Users\user\heartbeats\` exists; every manifest entry where `enabled: true` has a `*.hb` file mtime within its `max_age_sec` tolerance.
- [ ] `SSD-Resolume-Watchdog-v2` registered with `LogonType = InteractiveToken` (verified via `schtasks /query /tn 'SSD-Resolume-Watchdog-v2' /xml` output containing `<LogonType>InteractiveToken</LogonType>`); heartbeat fresh.
- [ ] `SSD-Meta-Watchdog` registered + running; writes own `meta_watchdog.hb`.
- [ ] Synthetic A: `Stop-Process Arena -Force` → alive again within 3 min; verified by `Get-Process Arena` returning a PID with `StartTime` after the kill.
- [ ] Synthetic B: kill gallery_audio python proc (NOT the task) → `meta_gallery_audio_stalled` Telegram alert received within 10 min.
- [ ] Maintenance lock honored: run `scripts/maintenance.ps1 -Minutes 5 -Reason "test"`, trigger synthetic silence for 3 min, verify NO Telegram alert during the window, verify alerts resume after the lock expires.
- [ ] All Phase-0 code committed + pushed + deployed via `scp`; `v-pre-resilience` tag exists pointing at commit immediately before deployment.

**Phase 1:**
- [ ] `docs/resilience-spec.md` has Component Contract section for ≥8 subsystems (grep `^## Component:` ≥8).
- [ ] **Composite audio silence:** headphones playing tone + room speakers muted → probe reports `audio_silent = PASS` (because `output_silent = false`). Confirmed by running tone through Ableton, disconnecting speakers, watching probe log.
- [ ] **Composite audio silence — positive case:** headphones disconnected + speakers muted → probe fires `audio_silent` CRITICAL within 90s.
- [ ] Autolume kill → walls never go black; SD continues on `noise1`. Verified: `Stop-Process` all Autolume procs, `/td/snapshot` remains dynamic for 5 min (content changes, not static frame).
- [ ] Alert digest: synthetic 5-consecutive same-key silence triggers digest mode by alert #4; next firing ≥6h later; digest message includes suppression count.
- [ ] `C:\Users\user\snapshots\2026-04-20\` exists by EOD Apr 20, contains `visitor_queue.txt` (or `_FAILED.txt` with error), `SSD-exhibition.toe` copy, log tails. Snapshot result also echoed in daily_diagnostic Telegram output.
- [ ] **Resolume fallback layers** — either confirmed live in composition (with Prav on Apr 21 call) and verified via `Stop-Process TouchDesigner -Force` triggering the fallback, OR explicitly **moved to Parking Lot** (post-show work item, not Phase 2) with a note here in the plan. Choice is Parking-Lot, not Phase 2, because Phase 2 has a fixed 4-day window (Apr 22–26) with a packed agenda (CUDA install, WMP migration, sfc, etc.) — composition changes need Prav's focused creative time which is better found during the post-show quiet period.

**Phase 2:**
- [ ] `bias_act_plugin.pyd`, `filtered_lrelu_plugin.pyd`, `upfirdn2d_plugin.pyd` all present under CUDA 12.4 cache dir, ≥1 MB each.
- [ ] `params.use_custom = True` committed.
- [ ] **VRAM gate:** `Test-VRAMHeadroom` returns true (≥ 4096 MiB free) before Autolume launches; synthetic test confirms that when artificially constrained to < 4 GB free, Autolume launch is deferred with expected alert.
- [ ] SSD-Autolume launches + NDI publishes for ≥10 min continuous.
- [ ] ndiin2 in TD reads non-zero pixels for ≥5 min continuous.
- [ ] WMP auto-starts on reboot with Matt's WAV on loop; `Get-Process wmplayer` alive + default output device audio session shows non-zero peak level.
- [ ] `sfc /scannow` log captured in incident postmortem.
- [ ] Playbook Apr 19 appendix committed.

**Phase 3:**
- [ ] Macrium image produced + restored-to-VM tested.
- [ ] Training video recorded + laminated card printed.
- [ ] Deploy-elsewhere script tested end-to-end in VM.
- [ ] Zoe + ≥6 components registered in knowledge graph.

## Verification plan

Phase 0:
- AC0.0 (Pre-flight audit) → `git show HEAD:docs/environment-audit-2026-04-19.md | head -80` returns audit doc with sections for 0.0.a–0.0.g; `git log docs/environment-audit-2026-04-19.md` shows commit before any Phase 0.1–0.9 commits (audit precedes changes).
- AC0.1 (Windows Update off) → `ssh windows-desktop-remote "gpresult /r | Select-String WindowsUpdate"` + `Get-ScheduledTask Microsoft*Update* | Select TaskName,State` (expect all `Disabled` or no rows)
- AC0.2 (NVIDIA update off) → GFE GUI check (screen share with Prav) + `Get-ScheduledTask NVIDIA* | Select TaskName,State`
- AC0.3 (manifest + heartbeats) → `Get-Content scripts/heartbeat_manifest.json | ConvertFrom-Json` lists all expected entries; `Get-ChildItem C:\Users\user\heartbeats\*.hb` shows matching files all < their respective `max_age_sec`
- AC0.4 (Resolume watchdog session) → `schtasks /query /tn 'SSD-Resolume-Watchdog-v2' /xml` output grep `LogonType` returns `InteractiveToken`
- AC0.5 (meta-watchdog self-alive) → `meta_watchdog.hb` mtime < 120s; Telegram info alert on first run confirms startup
- AC0.6 (Synthetic A) → `Stop-Process Arena -Force; Start-Sleep 180; Get-Process Arena` expect PID alive; `StartTime` after kill
- AC0.7 (Synthetic B) → kill gallery_audio python proc via `Stop-Process -Id <pid>` (leaving task itself alone); observe `meta_gallery_audio_stalled` Telegram alert within 10 min
- AC0.8 (Maintenance lock) → run `scripts/maintenance.ps1 -Minutes 5 -Reason "test"`; trigger synthetic silence; check `ssd_notify.log` for "SKIP (maintenance)" entries, no Telegram SENT; after 6 min (lock expired), run synthetic silence again, expect Telegram fires normally
- AC0.9 (commit tag) → `git tag | grep v-pre-resilience` returns tag; `git log origin/main --oneline -10` shows Phase-0 commits after tag

Phase 1:
- AC1.1 → `ls docs/resilience-spec.md && grep -c '^## Component:' docs/resilience-spec.md` returns ≥8
- AC1.2 (composite silence negative) → with headphones playing tone + speakers muted: probe log shows PASS for `audio_silent` across 3 consecutive probe cycles (15 min); no Telegram fired
- AC1.3 (composite silence positive) → headphones disconnected + speakers muted: `audio_silent` CRITICAL Telegram fires within 90s; clearing (tone playing) resolves within 1 probe cycle
- AC1.4 (Autolume degradation) → `Stop-Process python -Force` for all Autolume procs (not TD's); poll `https://salishseadreaming.art/td/snapshot?t=$(date +%s)` every 30s for 5 min; diff SHA256 between fetches shows ≥3 distinct snapshots (proves dynamic output, not frozen frame)
- AC1.5 (alert digest) → force `vol_max_60s < 0.002` for 2h continuous (via temporary script override); count Telegram SENT events for `audio_silent` key: expect ≤3 in first hour, then 0–1 in next 5h, exactly 1 digest message around the 6h mark containing suppression count
- AC1.6 (daily snapshot) → `Test-Path C:\Users\user\snapshots\2026-04-20\SSD-exhibition.toe` returns true; file size > 500 KB
- AC1.7 (resolume fallback) — if live: `Stop-Process TouchDesigner -Force`, visit `/td/snapshot` in a browser for 4 min; expect Resolume output continues (fallback layer visible). If deferred: corresponding Parking Lot entry exists citing this plan.

Phase 2:
- AC2.1 (plugins built) → `Get-ChildItem C:\Users\user\AppData\Local\torch_extensions\*\Cache\*\*_plugin -Recurse -Filter *.pyd` returns 3 files ≥ 1 MB
- AC2.2 (VRAM gate enforcement) → artificially allocate ~22 GB of VRAM via torch in a separate process → Autolume launch attempt logs `autolume_vram_insufficient` + no Autolume process started; free VRAM (`nvidia-smi`) confirms ≥ 4 GB free after deallocation; subsequent launch attempt succeeds
- AC2.3 (Autolume NDI publish) → 10 min of TD ndiin2 samples via MCP; `vol_max` over samples > 0 and pixel samples non-zero
- AC2.4 (WMP on reboot) → full machine reboot; within 5 min of logon, `Get-Process wmplayer` returns PID + WASAPI peak on default output > 0.01
- AC2.5 (sfc scannow) → `findstr /C:"Windows Resource Protection" %WINDIR%\Logs\CBS\CBS.log` returns expected success-or-repaired line
- AC2.6 (playbook appendix) → `git log docs/playbook.md` shows recent commit with "Apr 19 incident" in message

Phase 3 verification expanded per sub-step when we reach them.

---

## Rollback

**Trigger conditions.**
- Any Phase-0 change causes walls black or audio silent during Apr 20 9:45 AM opening.
- A per-component watchdog (not meta-watchdog — meta-watchdog is strictly alert-only) incorrectly restarts a healthy process during visitor hours, causing visible disruption.
- Heartbeat writes saturate disk (> 100 MB/day — shouldn't happen, but guard).
- Phase-2 CUDA 12.4 install breaks existing TD/SD.

**Rollback steps.**

Phase 0:
1. `schtasks /change /tn 'SSD-Meta-Watchdog' /disable` (stops alerting, no side effects).
2. `schtasks /change /tn 'SSD-Resolume-Watchdog-v2' /disable`.
3. Restore prior scripts: `git checkout v-pre-resilience -- scripts/` then `scp` to 3090.
4. Re-enable Windows Update only if critical security patch needed.

Phase 1: sub-steps independent; disable any failing task, leave others running.

Phase 2 CUDA rollback:
1. Uninstall CUDA 12.4 via Windows Add/Remove (keeps 11.8).
2. Reset `CUDA_HOME` to 11.8 path.
3. Restore `params.use_custom = False` + visualizer.py patches from git.

**Data safety.** Heartbeat files + state snapshots are append-only / new-dir; no mutation of existing TD .toe or Resolume composition until Phase 2. Tag `v-pre-resilience` before Phase 0 starts enables full revert.

## Risks

- **Heartbeat I/O noise.** Mitigation: 30–60s interval, 1 KB files, monthly rotation. Negligible vs existing snapshot uploads.
- **Meta-watchdog false positives** (process legitimately slow). Mitigation: 120s threshold + jitter; digest mode if repeated.
- **Auto-restart loops** (crash → restart → crash). Mitigation: exponential backoff, max 5 restarts/hour, then disable + alert.
- **Disabling Windows Update leaves security holes** post-show. Mitigation: unblock procedure documented Phase 3.6; machine is behind NAT + admin-only.
- **Building this solo during open show.** Mitigation: Phase 0 only today with synthetic-test gate; Phase 1+ in quiet windows; every sub-step independently rollback-able.
- **Telegram outage.** Mitigation: logs on disk + SSH always available as primary control path. **Backup alert path:** if the Telegram bot API returns non-200 for 3 consecutive attempts, `ssd_notify.ps1` also writes a flag file `C:\Users\user\ALERT_UNDELIVERED.txt` listing the unsent alerts. Daily diagnostic (9:15 AM) reads this file + includes its content + clears it. So a missed Telegram during quiet hours is surfaced the next morning at latest. Longer-term (Phase 3): add SMTP backup via the Gmail path (already stubbed; Prav provides app password). Not Phase-0-critical since SSH is always there and Telegram's uptime is excellent historically.
- **SSH reverse-tunnel outage.** If tunnel down at incident time (e.g., poly is unavailable), recovery is blocked until tunnel restored. Mitigations: (a) tunnel is maintained by `SSD-SSH-Tunnel` with its own watchdog behavior (verified running today); (b) local-network SSH `ssh windows-desktop` works if someone is on-site (Prav or docent with laptop); (c) Tailscale was considered and may be added Phase 3 as a second reachability path — parking it. In the worst case (tunnel down + nobody on-site), the system continues in whatever mode it was in; watchdogs continue attempting local recovery; alerts buffer in `ssd_notify.log` until tunnel restored. Not-great, but bounded: single-provider poly + single-tunnel setup is Horizon 3 to address via Tailscale.

### Dual-outage on-site signal (Telegram + tunnel both down)

If Telegram delivery fails AND SSH tunnel is unreachable, no remote party learns of a failure in real time. To give on-site staff (Zoe or any docent) a visible/audible cue without requiring them to monitor a computer screen, add a simple local-only fallback:

- **Mechanism:** health_probe.ps1, after 2 consecutive probe cycles where BOTH (a) `ssd_notify.ps1` returns delivery-fail AND (b) the tunnel `SSD-SSH-Tunnel` task shows `Last Result != 0` or tunnel process absent, plays a short distinct audio cue on the default output device (`[System.Media.SoundPlayer]` with a 2-second chime file stored locally) AND writes a prominent text file to the desktop: `C:\Users\user\Desktop\INSTALLATION_NEEDS_ATTENTION.txt` with timestamp + what's broken.
- **Why not constantly play the cue:** probe runs every 5 min; the cue plays at most once per dual-outage detection, with a 15-min cool down. It's a "heads up" not an "alarm." Zoe sees the desktop file on her next glance at the tower (which she does during opening checks per playbook).
- **Why this is not Phase 0:** it's an additive feature that doesn't affect normal operation and depends on already-built silence detector + tunnel-state check. Moving to **Phase 1.7** (new sub-step) alongside alert digest + state snapshot. If Prav rejects the concept (audio interruption could be mis-read by visitors as installation artifact), the Desktop text-file half ships without the audio cue.
- **GPU contention** worsens when Autolume restored in Phase 2. Mitigation: explicit VRAM check before launch; defer if TD/SD near memory ceiling.

---

## Parking Lot

- (Impact: M) (Effort: M) (When: post-launch) — Move Gallery Server from poly to 3090 for venue portability.
- (Impact: L) (Effort: S) (When: next-sprint) — Log visitor prompts + snapshot-at-submission to a "submissions" knowledge-graph index.
- (Impact: M) (Effort: L) (When: next-sprint) — Explicit VRAM budget per component + pre-launch check.
- (Impact: H) (Effort: L) (When: post-tour) — Formalize "Salish Sea Dreaming Installation" as packaged deployable artifact with venue-config adapter.
- (Impact: L) (Effort: S) (When: someday) — Save Ableton output-device routing to a config file so re-selecting after restart is programmatic.
- (Impact: M) (Effort: S) (When: post-launch) — Replace mic-based silence detector entirely with WASAPI output-session level once Phase 1 proves the API works on this Win 11 build.
- (Impact: L) (Effort: M) (When: next-sprint) — Migrate from per-task `.hb` files to `heartbeats.sqlite` if subsystem count exceeds ~50.

## References

- docs/playbook.md
- docs/tour-readiness-plan.md
- docs/onsite-support-manual-DRAFT.md
- scripts/health_probe.ps1
- scripts/ssd_notify.ps1
