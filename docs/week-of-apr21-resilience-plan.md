# Week of Apr 21 — path to 100% self-monitoring + self-healing

Exhibition runs through Saturday Apr 26. Goal: **100% unattended-reliable by
Thursday evening**, so Fri–Sat are monitor-only. Board visit Fri evening
(Natalia + Angora, M37XR) is the gate; after that, the 3090 comes home
Sunday for post-show iteration.

## Current state (Mon Apr 20 end-of-day)

**Working auto-heal:**
- Arena watchdog v2 (restarts Arena within ~60–90s of crash; proven in wild today ×2)
- Arena prompt suppression (`launch_resolume.bat` v2 validated tonight — composition loads without modal)
- Windows Updates blocked at 5 layers
- WireGuard backup tunnel (Mac ↔ 3090 via poly, independent of SSH tunnel)
- SSH tunnel reachability watchdog (deployed tonight, auto-restarts on 2 consecutive failed checks)
- Daily diagnostic Telegram at 09:15 PDT

**Known gaps (ordered by impact):**
- AHK kick effectiveness (projector auto-assign after Arena restart) — untested visually
- TouchDesigner has no watchdog
- Autolume has no watchdog (also running at degraded 8.7 FPS)
- Ableton has no auto-start and no watchdog → single point of audio failure
- Audio silence detection disabled (was false-positive-spamming; needs WASAPI loopback rewrite to re-enable)
- No meta-watchdog watching the watchdogs
- td_relay fade-in (resolume_fade.py) built but not deployed; duplicate td_relay instances running

**Estimated current self-heal: ~80% with tunnel watchdog in place.**

---

## Compressed schedule (Tue–Thu work, Fri–Sat monitor-only)

### Tue Apr 21

**Prav on-site AM 9:30–10:30 (2 critical validations):**

1. **AHK kick visual test** (15 min): kill Arena at keyboard, watch wall. Does Advanced Output open + projectors auto-assign within ~90s without manual intervention? If yes: kick proven. If no: capture prompt title/class for fallback.
2. **EDID dongle emulation test** (15 min): with PC running, power BenQ off. Does Windows keep the 1920×1080 display? If yes: emulation latched. If no: re-hold dongle button ~3s with BenQ on+live; retest.
3. **Buffer before open** (30 min).

**Darren solo PM 11:00–16:00 (~4h):**

4. **Deploy td_relay_v2 with fade-in** (1.5h):
   - Kill duplicate td_relay.py instances
   - Swap to td_relay_v2.py (or update SSD-Relay task)
   - Resolume OSC input on :7001 is already enabled (verified Mon)
   - Verify layer index matches composition's TD layer
   - Submit a visitor prompt from phone; confirm TD layer fades in on wall
5. **TouchDesigner watchdog** (1h): template-copy of `resolume_watchdog.ps1`. Detects TD process missing, triggers `SSD-TouchDesigner` task. Heartbeat + crash-loop guard.
6. **Autolume watchdog** (1h): same template. Also: if running but FPS < 10 for 5+ min, log WARN (don't auto-restart — restart rarely fixes perf).
7. **Buffer + logs review** (30 min).

**Tue goal:** 90% — fade-in live, all 3 major processes (Arena, TD, Autolume) have watchdogs.

### Wed Apr 22 — LAST big-deploy day before board visit

**Darren solo AM 08:00–12:00 (~4h, before 4pm sons visit):**

8. **Ableton → WMP swap** (1.5h):
   - Confirm with Prav tonight: audio files currently playing in Ableton
   - Export to .wav
   - Create `SSD-Ambient-Audio` task playing loop via PowerShell `SoundPlayer` or `wmplayer.exe`
   - Stop Ableton (save project state first)
   - Test: audio plays after a reboot
9. **WMP watchdog** (1h): detects ambient_audio process missing, restarts. Heartbeat file.
10. **Meta-watchdog** (1.5h): reads `heartbeat_manifest.json` every 30s; for each component with `enabled: true`, alerts on stale heartbeat. Runs as `SSD-Meta-Watchdog` task. This is the watcher of watchers — closes the "watchdog dies silently" gap that bit us between Apr 16 and Apr 20.
11. Also extend the existing `gallery_audio.py` to write `gallery_audio.hb` even though its data is unreliable — unblocks meta-watchdog for that component.

**Wed PM: HANDS-OFF.** Sons visit at 4pm is our first real "acceptance test" of the hardened installation.

**Wed night: 1st overnight dry-run**. All watchdogs live; we observe Wed→Thu AM telemetry.

**Wed goal:** 98% — all components watched; meta-watchdog catches watchdog-stalls.

### Thu Apr 23 — LOCK-IN DAY

**Darren solo (~5h, morning-afternoon):**

12. **Review Wed→Thu overnight telemetry** (30 min): any alerts? Any stall events? Any watchdog restart loops? If anything concerning: fix, then extend the freeze.
13. **WASAPI audio detector rewrite** (3h): finish `scripts/wip/gallery_audio_loopback_draft.py`. `pip install pyaudiowpatch` on 3090. Swap `gallery_audio.py`. Calibrate silence threshold with Ableton/WMP playing → volume non-zero; muted → silent. Re-enable `audio_silent` CRITICAL alert in `health_probe.ps1`.
14. **Full synthetic crash-test suite** (1h): sequentially kill Arena, TD, Autolume, ambient-audio, tunnel process — verify each recovers. Document timing.
15. **Documentation + handoff** (30 min): update heal-tree with current state; memory updates; git push.

**Thu evening 20:00: FREEZE.** No more deploys. No more changes. Only revert if something is verifiably broken and can't be repaired with rollback.

**Thu night: 2nd overnight dry-run** (with WASAPI audio detector back online). This is the confidence run — if this is clean, we're truly done.

**Thu goal:** 100%. System fully unattended-capable. Evidence: 2 consecutive clean overnights (Wed→Thu and Thu→Fri).

### Fri Apr 24 — MONITOR ONLY

16. AM: review Thu→Fri overnight telemetry. Confirm clean.
17. If anything is off: **no new code**. Revert to last known good; accept imperfection over experimentation.
18. Install runs autonomously through the day and the Natalia visit.

### Sat Apr 26 — MONITOR ONLY

19. Final day. Watch; don't touch.
20. Post-show: teardown checklist, config backups, move 3090 home Sunday.

---

## Tonight's residual work (Mon evening — optional)

- ✅ Tunnel watchdog deployed
- ✅ Audio false-alert silenced
- ✅ Plan written (this doc)
- Optional: pre-stage td_relay_v2 swap script (ready to run Tuesday) — 30 min
- Optional: pre-draft TD + Autolume watchdog scripts (template copies) so Tue PM is mostly deploy-and-verify — 1h

## Risk acknowledgements

- **Arena 7.15 heap corruption**: auto-heal handles it but crashes still happen. Upgrade to 7.22+ is post-show (too risky mid-show).
- **No UPS** on the 3090. A power blip takes everything down with no graceful shutdown.
- **Single-machine installation**: no hot-standby. For touring variant this must change.
- **Bluetooth audio transmitter branch**: no way to detect pairing-loss remotely. Wired speakers still work; BT speakers may go silent silently.
- **If Thu overnight dry-run has issues**: do NOT iterate on Fri. Revert and accept the gap.

## Validation gates

- **Wed 4/22 4pm (sons)**: all watchdogs healthy; no human intervention during the visit. If anything breaks: document + manual workaround; don't redeploy that day.
- **Thu 4/23 20:00 (freeze)**: 2 overnight dry-runs done or in progress; final synthetic crash test passed.
- **Fri 4/24 evening (Natalia)**: 2nd overnight clean; installation showcases reliability unattended.
- **Sat 4/26 EOD**: all tasks closed; ready for teardown Sunday.

## Parking-lot (post-show, not this week)

- Arena 7.22+ upgrade
- UPS for 3090 tower
- Pro-AV EDID dongle swap (Gefen EXT-HD-EDIDPN or ATEN VC081A)
- IP-controlled PDU for remote hard-reboot
- Touring variant: multi-machine redundancy design
