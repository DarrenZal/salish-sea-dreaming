# Week of Apr 21 — path to 100% self-monitoring + self-healing

Exhibition runs through Saturday Apr 26. Goal: reach unattended-reliable
operation by Fri evening (Natalia + Angora M37XR board visit). After
the show closes, the 3090 comes home for post-show iteration; this week
is the one window to lock things in while the installation is live.

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
- EDID dongle emulation state unverified (may fall back to passthrough overnight)

**Estimated current self-heal: ~75% with tunnel watchdog now in place.**

---

## Day-by-day

### Tue Apr 21

**Prav on-site AM, before 11:00 open (1h):**

1. **AHK kick visual test** (15 min): kill Arena at keyboard, watch wall — does Advanced Output open and projectors auto-assign within ~90s without manual intervention? If yes: kick proven; gap closes. If no: capture the window title/class of any prompt or focused element that blocks the keys; Darren builds fallback that afternoon.
2. **EDID dongle emulation test** (15 min): with PC running, power BenQ off. Does Windows keep the 1920×1080 display listed? If yes: emulation latched. If no: Prav re-holds dongle's button ~3s with BenQ on + live; retest.
3. **Buffer for any surprise issues before open** (30 min).

**Darren solo PM (3h):**

4. **Deploy td_relay_v2 with fade-in** (2h):
   - Kill duplicate td_relay.py instances on 3090
   - Configure SSD-Relay scheduled task to point at td_relay_v2.py (or swap file content)
   - Verify Resolume OSC input on port 7001 already configured (✅ done tonight)
   - Verify composition has TD layer as layer 1 with opacity at 0 baseline; if not, adjust resolume_fade.py layer index
   - Submit a visitor prompt via phone; confirm Arena's TD layer fades in
   - Fade-out after 15–30s so wall rotates visitors naturally
5. **Arena crash validation at lunch lull** (30 min): fresh kill → watch full chain (now includes a validated kick from the morning). Document the chain timing.
6. **Heartbeat manifest read** (30 min): inspect `heartbeat_manifest.json`, mark which components currently write .hb files (resolume_watchdog, tunnel_watchdog ← new). Plan extensions for TD/Autolume/gallery_audio.

**Tue goal:** 85% — fade-in live, EDID verified, kick proven or fallback built.

### Wed Apr 22

**Prav on-site AM (~1.5h, before sons arrive at 4pm):**

7. **Switch automatic-mode audio from Ableton to WMP loop** (1h):
   - Confirm with Prav what audio file(s) play in automatic mode today in Ableton (filename, length, loop behavior)
   - Export to .wav if not already
   - Create `SSD-Ambient-Audio` task that runs `wmplayer.exe /fullscreen <file>` or better use Windows `SoundPlayer` via PowerShell loop
   - Stop Ableton (save Prav's project state first)
   - Test: audio plays on gallery speakers, auto-restarts on machine reboot
   - Build WMP watchdog: checks wmplayer.exe running; restarts on exit
8. **Final smoke test before sons visit** (30 min): full prompt flow + audio + watchdog status.

**Wed PM: HANDS-OFF. Sons visit 4pm; no deploys.**

**Wed goal:** 90% — audio has a proper watchdog; no single point of failure on audio.

### Thu Apr 23

**Darren solo (4–5h, remote):**

9. **TouchDesigner watchdog** (1h): modeled on `resolume_watchdog.ps1`. Detects TD process missing; triggers `SSD-TouchDesigner` task. Heartbeat file. Max-restarts-per-hour crash-loop guard.
10. **Autolume watchdog** (1h): same pattern for Autolume. Also adds an FPS-degradation probe — if Autolume is running but FPS < 10 for 5+ min, log WARN (no auto-restart, just alert — restart often doesn't fix perf issues).
11. **Meta-watchdog** (2h): PowerShell service that reads `heartbeat_manifest.json` every 30s; for each component with `enabled: true`, checks heartbeat file freshness against `max_age_sec`; fires Telegram alert on stalls. Runs as `SSD-Meta-Watchdog` task.
12. **Extend gallery_audio.py to write heartbeat** even with the WASAPI rewrite pending — the _existing_ script can at least write .hb while its data is unreliable. That unlocks the meta-watchdog to notice if gallery_audio.py dies.

**Thu goal:** 97% — watchdogs watch watchers. Only gaps left are audio WASAPI rewrite and Arena 7.22+ upgrade.

### Fri Apr 24

**Darren solo AM (2–3h):**

13. **WASAPI audio detector rewrite** (2h): finish `scripts/wip/gallery_audio_loopback_draft.py`. Install pyaudiowpatch on 3090. Swap deployed script. Re-enable the audio_silent alert in health_probe.ps1 with the new detector's actual silence threshold. Verify with Ableton/WMP playing → state file shows nonzero volume; muted → silent.
14. **Overnight Thu→Fri dry-run verification**: review overnight telemetry (Telegram, heartbeat files, watchdog logs). No intervention = success.
15. **Final smoke test**: kill Arena, Autolume, TD, Ableton in random order during a quiet moment; observe watchers recover everything within 3 min.

**Fri evening: Natalia + Angora visit. HANDS-OFF.**

**Fri goal:** 100% — installation is fully unattended-capable.

### Sat Apr 26 — last day of exhibit

16. No new deploys. Monitor telemetry.
17. Post-show teardown planning: checklist for packing 3090, backing up configs, documenting final state for post-show development work at home.

### Post-show (after Apr 26)

- Arena 7.15 → 7.22+ upgrade (reduces heap-crash frequency)
- Consider UPS for 3090 tower
- Swap EDID dongle to Gefen EXT-HD-EDIDPN or ATEN VC081A (install-grade, documented behavior)
- Consider IP-controlled PDU as ultimate-fallback remote hard-reboot

---

## Tonight's residual work (Mon evening — if energy remains)

- ✅ Tunnel watchdog deployed (done)
- ✅ Audio false-alert silenced (done)
- ✅ Plan written (this doc)
- Optional: pre-stage td_relay_v2 deployment artifacts (write a swap script ready to run Tuesday)
- Optional: prep meta-watchdog scaffolding

## Risk acknowledgements

- **Arena 7.15 heap corruption** keeps crashing — auto-heal handles it but crashes still happen ~daily. Upgrade to 7.22+ mitigates but is post-show (too risky mid-show).
- **No UPS** on the 3090 tower. A power blip during the show takes everything down with no graceful shutdown.
- **Single-machine installation**: everything runs on one 3090. No hot-standby; no failover. For a touring variant this must change.
- **Prav is the only on-site human**: if he can't make it to the gallery on a given day, and something breaks beyond what remote recovery can handle, the wall could stay blank until he arrives.
- **Bluetooth audio transmitter branch**: no way to detect pairing-loss remotely. If BT drops, wired speakers still work but BT speakers go silent silently.

## Validation gates

- **Wed 4/22 4pm**: Arena + Autolume + TD + audio all stable, watchdogs healthy, no manual intervention needed during sons' visit. If not: escalate immediately to human workaround.
- **Fri 4/24 evening**: Natalia arrives to a running installation with no visible fragility. If anything is mid-deploy, roll back to last known good before she arrives.
- **Sat 4/26 EOD**: all tasks closed or documented; ready for teardown Sunday.
