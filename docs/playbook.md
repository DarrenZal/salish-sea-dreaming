# Salish Sea Dreaming — Gallery Operations Playbook

**Exhibition:** Digital Ecologies: Bridging Nature and Technology
**Venue:** Mahon Hall, Salt Spring Island
**Dates:** April 10–26, 2026
**Equipment location:** Mahon Hall (the 3090 tower is on-site in the gallery)

---

## PART 1 — Quick Reference Card (print & laminate)

### What "working" looks like

- The projection wall is **moving**, with dreamy marine imagery (GAN-generated latent interpolations — salmon, kelp, waves, birds, light).
- You can see organic flowing shapes shifting slowly into each other.
- Sound is playing (gentle ambient audio, looping).
- **If all three are true → the installation is healthy. Leave it alone.**

### If something looks wrong — try these in order

| # | Symptom | Action |
|---|---------|--------|
| 1 | **Black wall / no image** | Wait 2 minutes. The system auto-restarts itself. If still black → **Step 5**. |
| 2 | **Frozen image (not moving)** | Wait 2 minutes. If still frozen → **Step 5**. |
| 3 | **One wall black, other wall fine** (BenQ vs Epson) | Likely BenQ signal drop — a tech can reset it quickly via Resolume. **Text Darren** with a photo of which wall is dark. |
| 4 | **Image on wrong wall** | Wait 30 seconds — display watchdog auto-restores projector assignments. If still wrong → **Step 5**. |
| 5 | **No sound** | Check the speaker power and volume knob. If still silent → **Step 6**. |
| 6 | **Still broken after waiting** | **Text Darren: 518-210-2828** (or message the WhatsApp group) with a photo of the wall. |

### What NOT to do

- ❌ **Don't hit the power button on the computer tower** unless a tech has asked you to. We reboot remotely — randomly power-cycling the machine can interrupt a running recovery.
- ❌ Don't unplug cables or move the equipment.
- ✅ Projector power-cycles are OK — the display watchdog auto-restores the mapping.

### Escalation ladder (if something is broken after waiting 2 min)

| Step | Who / how | What happens |
|------|-----------|--------------|
| 1 | **WhatsApp group** (Darren + Prav) with photo of wall | Fastest — both see it. One of us remote-reboots from our phone / laptop. |
| 2 | **Text Darren directly: 518-210-2828** | If group is quiet. Darren triggers remote reboot. |
| 3 | **Text Prav** | If Darren unreachable. Prav can trigger remote reboot from his phone via the admin URL (see Part 4). |
| 4 | **On-site reboot (only if asked by a tech)** | Tower is on-site. If we're all unreachable AND the wall has been broken for 10+ min, press and hold the power button on the computer tower for 5 seconds to force shutdown, wait 10 seconds, press it once to power on. The auto-start tasks will bring everything back up in ~3–5 minutes. |

**Remote reboot from phone:** `https://ssd-gallery.<tunnel>/admin/reboot` (requires admin password — shared in WhatsApp group pinned message). Darren or Prav can trigger this from anywhere.

---

## PART 2 — Full Symptom → Action Guide

### Visual problems

| Symptom | Likely cause | Docent action | Remote fix |
|---------|--------------|---------------|------------|
| Black wall | Projector off, or Resolume not running | Wait 2 min for auto-recovery. Check projector power LED. | Resolume watchdog restarts it within 2 min. |
| Frozen image | TouchDesigner or StreamDiffusion hung | Wait 2 min for auto-recovery. | TD watchdog restarts it within 2 min. |
| Wrong image (not marine) | Resolume playing wrong composition | Text Darren with photo. | Remote fix: relaunch Resolume with correct composition. |
| Image on wrong wall / misaligned | Windows reshuffled display IDs (projector power-cycle) | Wait 30s for auto-restore. If still wrong after 1 min → text Darren with photo of all walls. | Display-Watchdog detects change, reloads MultiMonitorTool config (~15s). |
| **One wall black, other wall fine** — especially if it's the **BenQ** | EDID handshake drift (BenQ is sensitive; Epsons tolerate it). Intermittent blackouts / signal drops. | Text Darren with photo. Don't power-cycle the projector — that can re-trigger. | Resolume → Output → Advanced Output → reset output for the affected screen. ~10s fix. Long-term: inline EDID emulator (~$30 dongle) locks the handshake. |
| Visitor prompts not appearing | Relay or gallery server down | Text Darren. | Relay watchdog restarts it. Server may need manual check. |
| Pixelated / low quality | Projector resolution mismatch | Text Darren. | Remote fix possible. |
| **Everything was fine yesterday, now all walls are black at opening** | Most likely: Windows Update reboot overnight. Watchdogs re-arm on logon but Resolume may come up idle, BenQ resolution may have reverted to 4K, NDI bindings may be stale. | Wait 3 minutes — auto-start may still be in progress. Still black → text Darren. Don't touch the computer. | (1) SSH in, confirm logon completed. (2) `schtasks /run /tn "SSD-Resolume"` to relaunch Resolume. (3) Re-pin BenQ to 1920×1080 in Display Settings. (4) If wall still black, check `ndiin2.name` in TD for stale hostname. See Part 4 "Windows Update handling." |

### Audio problems

| Symptom | Docent action |
|---------|---------------|
| No sound | Check speaker power + volume. Check cable to computer. |
| Distorted | Lower volume. Text Darren. |
| Only one speaker | Check both speaker cables. |

### Visitor interaction (phone QR code)

| Symptom | Docent action |
|---------|---------------|
| QR code not scanning | Ask visitor to try another phone. Clean the printed code. |
| "Page not loading" | Text Darren — cellular / wifi / tunnel may be down. |
| Visitor says prompt didn't appear on wall | Wait 30 seconds — there's a queue. If still nothing → Text Darren. |

---

## PART 3 — Daily Routine

### Opening (gallery opens at 11:00 AM)

**10:40 AM — projector power-on (2 min):**

1. Pick up **both projector remotes**.
2. Point each remote at its projector. **Press the power button on both at roughly the same time** (within a few seconds of each other is fine).
3. Wait ~30 seconds — the projectors warm up, Windows detects them, and the display watchdog restores the saved mapping within ~15 seconds after that.
4. *Why simultaneous?* Windows assigns display IDs in the order it detects the signals. Bringing them up together gives one clean detection event and one restore from the watchdog, instead of cascading triggers. The watchdog handles either case, but together is tidier.

**10:45 AM — walk-in check (5 min):**

Tick each item. If any is ❌ → text Darren immediately (gives us 15 min before opening).

- [ ] **Walls moving?** — flowing marine imagery on both projection walls (not frozen, not black).
- [ ] **Sound playing?** — gentle ambient audio audible from the gallery speakers.
- [ ] **Photo taken?** — one wide shot of the installation for the morning record.
- [ ] **Visitor QR working?** — scan the posted QR with your own phone, confirm the visitor page loads (no need to submit a prompt).

**If anything looks off:**
1. Wait 3 minutes. Watchdogs usually catch it.
2. Still off → text Darren (518-210-2828) with a photo of the wall.
3. Don't power-cycle the computer tower. Don't unplug anything.

**If there was a Windows update overnight** (walls black at first look, but everything was working yesterday): see Part 2 row "Everything was fine yesterday, now all walls are black at opening." This is a known failure pattern — just text Darren and wait.

### During gallery hours

- Walk past every ~hour. If still moving + sound → fine.
- Log any visitor comments / questions in the notebook.
- If the wall goes black mid-visit, smile at visitors and say "it's self-healing, give it a moment" — the watchdogs usually catch it within 2 minutes.

### Closing (gallery closes 5:00 PM)

- The **computer stays on overnight** — don't touch it, don't shut it down.
- Use both projector remotes to **power off the projectors**.
- Take a photo of the wall as you leave (for the morning comparison).
- Put the remotes back in their usual spot so the opening docent can find them.

---

## PART 4 — Remote Reboot Procedure (technical — Darren/Prav only)

### The full cold-boot sequence

The 3090 (on-site at Mahon Hall) runs the entire stack. Remote access via:
- **Local network** (same house): `ssh windows-desktop`
- **From anywhere**: `ssh windows-desktop-remote` (reverse tunnel via poly)

### Scheduled tasks on the 3090 (verified April 12)

| Task | Status | Purpose |
|------|--------|---------|
| `SSD-SSH-Tunnel` | Running | Reverse tunnel to poly (remote access) |
| `SSD-TouchDesigner` | Ready | On-demand launch of TD + `.toe` file |
| `SSD-TD-Watchdog` | Running | Restarts TD if killed (2 min check) |
| `SSD-Relay` | Running | `td_relay.py` — visitor prompt relay |
| `SSD-Resolume` | Ready | On-demand Resolume launch w/ production composition |
| `SSD-Resolume-Watchdog` | Running | Restarts Resolume if killed |
| `SSD-Audio` | Running | `gallery_audio.py` — visitor voice capture (mic) |
| `SSD-Display-Watchdog` | Running | Detects display-count change, auto-restores MultiMonitorTool config |
| `SSD-Display-Restore` | Ready | On-demand display config restore |
| `SSD-Health-Monitor` | Running | `installation_health.py` — periodic service checks |
| `SSD-Autolume` | **Disabled** | `launch_autolume.bat` — needs enabling + validation before auto-start |

**Note:** Ambient audio playback (Prav's "media player, looping") is **not yet a scheduled task** — currently launched manually. `SSD-Audio` above is the visitor-mic capture, not ambient sound.

### Remote reboot (the nuclear option)

**From phone (fastest, no laptop needed):**
`GET https://ssd-gallery.<tunnel>/admin/reboot` — password-protected endpoint on the gallery server that SSHes to the 3090 and runs `shutdown /r /t 0`. Usable by anyone in the WhatsApp group from any phone. *(Pre-Monday TODO — not yet built.)*

**From laptop with SSH:**
```bash
ssh windows-desktop-remote
shutdown /r /t 0 /f
```

Then wait **3–5 minutes** and verify:

```bash
ssh windows-desktop-remote
# Check auto-login completed + services are up:
Get-Process TouchDesigner, Resolume, python
schtasks /query /tn "SSD-*" /fo LIST
```

### Resolume Advanced Output kick (remote)

**Symptom:** Resolume is running but the projectors aren't outputting (Prav's recurring morning fix is to open the Advanced Output panel — `Ctrl+Shift+A` — which forces the outputs to re-engage).

**Remote trigger from anywhere with SSH:**

```bash
ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Kick"
```

This fires `gallery_resolume_kick.ps1` in the user's interactive session, which brings Arena to the foreground and sends `Ctrl+Shift+A`. Logs to `C:\Users\user\resolume_kick.log`.

**Why a Task Scheduler hop:** SendKeys requires a real desktop. A direct SSH invocation runs in a headless session and the keystroke goes nowhere. The task runs in the logged-in user's session, where the keystroke reaches Arena.

**Note:** `Ctrl+Shift+A` *toggles* the panel — firing it twice cancels out. If you don't know the current state, fire once and check the wall; if still black, fire again.

### Manual service launch (if auto-start failed)

```powershell
# TD
schtasks /run /tn "SSD-TouchDesigner"
# Relay
schtasks /run /tn "SSD-Relay"
# Resolume
schtasks /run /tn "SSD-Resolume"
# SSH tunnel (if dropped)
schtasks /run /tn "SSD-SSH-Tunnel"
```

### Autolume boot sequence (autostart wrapper — pending Monday validation)

**Model:** `C:\Users\user\Documents\models\network-snapshot-000120.pkl`
**Saved presets:** `C:\Users\user\Documents\presets\0` and `\1` (both reference the same model, differ in widget state — latent/layer/adjusters/etc.)

**Wrapper** (deployed 2026-04-12, not yet enabled on boot):

- `C:\Users\user\autolume_autostart.py` — subclasses Autolume, skips Welcome/Splash, seeds the pkl, calls `start_renderer()`, and loads the preset once the render loop is live. Original Autolume source untouched.
- `C:\Users\user\launch_autolume_autostart.bat` — Task Scheduler launcher (activates conda `autolume` env, runs the wrapper with default `--pkl` + `--preset 0`).
- `C:\Users\user\test_autolume_autostart.bat` — interactive dry-run (visible console, `pause` at end to read errors).
- `C:\Users\user\autolume_watchdog.ps1` — 2-min restart watchdog (detects Autolume.exe OR python.exe running autolume).

**Monday validation sequence:**
1. Close current (manual) Autolume.
2. Double-click `test_autolume_autostart.bat` → verify Autolume launches straight into live render with the model loaded and preset applied.
3. If preset 0 isn't the desired state, edit one line in `launch_autolume_autostart.bat` to `PRESET_DIR=...presets\1` and re-test.
4. Once validated: re-point `SSD-Autolume` task action to `launch_autolume_autostart.bat`, enable the task, register the watchdog as `SSD-Autolume-Watchdog`.
5. Cold-boot test.

### Windows Update handling

**Context:** On 2026-04-16, a Windows Update reboot overnight left all projectors dark at opening. Resolume restart fixed it, but we want this to not need Prav's hands.

**Layered defence (apply in order):**

1. **Pause updates for 7 days** (covers remaining exhibition window, April 20–26).
   Settings → Windows Update → Pause updates → 7 days.
   Reversible anytime (Resume updates).

2. **Set Active Hours to 10:00–18:00** (prevents mid-visit reboots).
   Settings → Windows Update → Advanced options → Active hours → Manually → 10:00 to 18:00.

3. **`SSD-Post-Boot-Verify` task** — runs 60s after logon, checks:
   - Resolume + TouchDesigner processes alive,
   - BenQ display resolution is 1920×1080 (not 4K),
   - NDI sources bound to current hostname (not stale `MSI`).
   Writes to `C:\Users\user\post_boot_verify.log`. Log-only for now (upgrade to Telegram/WhatsApp if a real incident slips past).
   Script: `scripts/post_boot_verify.ps1` in repo; register as Task Scheduler task with 60s logon delay.

**Recovery playbook if a Windows Update still breaks the wall (docent sees black at opening):**

| Step | Action |
|------|--------|
| 1 | Docent texts Darren + photo. Doesn't touch the tower. |
| 2 | Darren/Prav SSH into 3090 (`ssh windows-desktop-remote`). Confirm logon completed (`Get-Process explorer`). |
| 3 | Relaunch Resolume: `schtasks /run /tn "SSD-Resolume"`. Wait 30s. |
| 4 | If wall still black: check BenQ resolution via Settings → Display → Advanced; re-pin to 1920×1080 if reverted to 4K. Re-map Resolume slice if needed. |
| 5 | If wall still black: check TD `ndiin2.name` — should be `DESKTOP-37616PR (Autolume Live)`. If `MSI (*)`, re-apply runtime fix (see April 13 entry in change log). |
| 6 | Once working: `Get-Content C:\Users\user\post_boot_verify.log -Tail 20` to see what the verify task saw (sanity-check for next time). |

### Known gaps (cold-boot test priorities — April 13)

- 🟡 **Autolume autostart — wrapper deployed, awaiting Monday validation.** New `autolume_autostart.py` wrapper subclasses Autolume to skip the Welcome screen, seed `network-snapshot-000120.pkl`, and load preset 0 (parameterized — one-line flip to preset 1). Verified imports + argparse work via SSH. Still needs an interactive dry-run on a real desktop session before re-enabling `SSD-Autolume`. See "Autolume boot sequence" below.
- 🟡 **Ambient audio — launcher built, awaiting Monday validation.** `gallery_ambient_audio.ps1` plays `Salish Dreaming 21 min.wav` on loop via .NET `SoundPlayer.PlayLooping()` (hidden, no GUI). Syntax + file-path verified. Pending: interactive test (stop current WMP → launch script → confirm audio) and registering `SSD-Ambient-Audio` task. Longer term: swap to Ableton auto-start once Prav ports his mix session from the 3060.
- ✅ **Resolume auto-start — confirmed working.** `SSD-Resolume` is "At logon time" with `Last Result: 0`. Task status shows "Ready" because the launcher bat exits after `start ""` — Arena.exe itself is what runs. Verified via `tasklist | findstr Arena` (Arena.exe PID 132748).
- ✅ **TouchDesigner auto-start — confirmed working.** `SSD-TouchDesigner` "At logon time", launches `SSD-exhibition.toe` after 30s ping delay.
- ✅ **Display ID reshuffle — solved.** `SSD-Display-Watchdog` polls every 15s, detects display count changes, waits 15s for HDMI settle, runs `MultiMonitorTool /LoadConfig display_config.cfg`.
- ❓ **Does simultaneous projector power-on actually matter?** In theory the watchdog handles any ordering, but one clean detection event is better than two cascading triggers. Worth empirically validating during the April 13 test: power one projector on, wait 30s, power the other, confirm mapping still lands correctly.
- ✅ **BenQ = root cause of Resolume crashes — confirmed fixed April 13.** Prav on the follow-up call: *"once I changed the BenQ down [to 1920×1080], it stopped doing its funny jiggling and weirdness and crashing Resolume. It was the BenQ that was crashing Resolume."* Applied mitigations:
  - ✅ **Windows → Display Settings → Advanced → pin BenQ to 1920×1080 @ 60 Hz.** ⚠️ **Gotcha:** changing resolution invalidates the existing Resolume slice — the main screen had to be **remapped in Advanced Output** after the res change. Any future res/refresh change → expect a remap.
  - ✅ BenQ menu: disabled **Auto Source Detect** and **Eco Mode**, enabled **PC/Presentation Mode**.
  - 🟡 **EDID copy-from-source dongles** ordered for Impact venue (May) — passive HDMI dongle that captures native EDID once and replays it forever so the projector can never re-handshake. Defence in depth; not required now but belt-and-braces for tour.
  - 🟡 **Epson replacement for BenQ** — Prav's strong preference going forward: *"BenQs aren't a very good brand. Epsons are what you want if you're a VJ."* On the equipment list for Impact.
- 🟡 **NDI flicker — observed April 13 afternoon, partially diagnosed April 13 evening.** Both Resolume NDI inputs and TouchDesigner NDI inputs go "offline" briefly (a few seconds) then recover. A second, more severe issue was uncovered in evening diagnostics: **stale NDI hostname bindings** (see next item). After the hostname fix, continue monitoring for real flicker. Remaining suspects if flicker returns:
  - LAN capacity — NDI is bandwidth-hungry (~100 Mbps per HD stream).
  - NIC / driver power management — disable on Windows NIC settings.
  - GPU encode capacity — NDI encoder shares GPU with TD/StreamDiffusion.
  - Diagnostics: NDI Tools Studio Monitor; `Get-Counter` on NIC during a drop.
- 🔴→✅ **NDI hostname mismatch — root cause of post-reboot black visuals, fixed at runtime April 13 evening, needs persistence.** The 3090's hostname is `DESKTOP-37616PR` but was once `MSI`. TD's `/project1/ndiin2` was hardcoded to listen for `MSI (Autolume Live)` — stream that hasn't existed since the hostname change. After reboot, the default Autolume → StreamDiffusion → Resolume pipeline received black frames → web-app snapshot was black. Same root cause very likely behind the Arena "nothing playing, had to click Advanced Output" symptom (Arena sources also hardcoded to `MSI (*)`).
  - ✅ **Runtime fix April 13 evening:** `op('/project1/ndiin2').par.name = 'DESKTOP-37616PR (Autolume Live)'` — snapshot went from 11KB black → 430KB real content within seconds.
  - ⚠️ **Not yet persisted:** fix is ephemeral until TD re-saves `SSD-exhibition.toe`. On next reboot, the stale MSI name returns.
  - 🟡 **Pending April 14 morning with Prav:** (1) Ctrl+S the .toe to persist the NDI source name. (2) Open Arena, check every NDI source, re-pick from dropdown, save the composition. (3) Grep the .toe binary for any other `MSI` references (it's binary but contains ASCII strings; `findstr` should surface them).
- 🟡 **BenQ resolution doesn't persist across reboots — Windows reverts to 4K.** Prav pinned BenQ to 1920×1080 in the afternoon, but after the evening reboot Windows defaulted it back to 4K, then he had to re-pin manually. This needs to be automated as part of the boot sequence — either a boot script that enforces display resolution, or an EDID emulator dongle (which would make Windows "see" only 1080p as a valid mode).
- 🟡 **Arena "click to play" on cold boot.** Even after Arena auto-starts, the composition window's clips don't begin playing until someone clicks into the Arena window (focuses it). Prav's workaround during manual recovery: click Arena's main window → clips start playing. **Automation option:** PowerShell script triggered after Arena launch that uses `SetForegroundWindow` + a safe mouse click into the composition area. Risk: brittle if window position changes.
- 🟡 **Arena first-clip-can't-be-missing-source rule.** In Arena, if the first clip on a clip line references a NDI source that isn't yet broadcasting (e.g., Autolume not up), the whole clip line freezes. Prav rearranged composition April 13 so Autolume is no longer first. Document this constraint so we don't accidentally revert.
- 🟡 **StreamDiffusion resolution resets to 1024×1024 on cold boot.** After April 13 reboot, SD came up at 1024 (heavy — ~6 fps). Prav manually changed to 768 and saved via the TD UI, but unclear if the save persists to the .toe or is in-memory only. Needs verification on April 14 reboot: does it come up at 768 or 1024?
- 🔴 **Autolume wrapper `autolume_autostart.py` has a TypeError — wrapper approach deferred.** Test run showed `PickleWidget.load() got an unexpected keyword argument 'ignore_errors'` — Autolume's own `start_renderer()` → `load_pickle()` path passes `ignore_errors` to `PickleWidget.load()` which doesn't accept it. Root cause is a version mismatch inside Autolume that the programmatic call path exposes. The GUI click path works because it doesn't hit this branch. Fix options: monkey-patch `PickleWidget.load` to accept `**kwargs` in the wrapper, or find an alternative API path in Autolume that doesn't call `load_pickle(..., ignore_errors=...)`. Until this is fixed, Autolume auto-start is disabled and Prav manually launches it after cold boot.
- 🟡 **Ambient audio task registered and running, but audio may not have been audible post-reboot.** `SSD-Ambient-Audio` fired on logon (log confirmed `SoundPlayer.PlayLooping()` started at T+90sec), but Prav couldn't hear anything. Most likely cause: Windows reset the default audio output device at boot (e.g., to NVIDIA HDMI, NDI Webcam Audio, or wrong USB device). **Pending verification April 14**: what's the default audio output device after cold boot, and does the .ps1 script play to the correct speakers? Fix if wrong: explicitly set the default audio endpoint via PowerShell at boot, or pin it via `audioswitch`/`SoundVolumeView`.
- 🟡 **TD spawns TWO StreamDiffusion instances on startup.** On April 13 reboot, two Python subprocesses both running `streamdiffusionTD/td_main.py` spawned at the exact same second — one using venv Python, one using system Python 3.11. Composition has both `/project1/StreamDiffusionTD` and `/project1/StreamDiffusionTD1` operators. Not necessarily a bug — may be intentional (dual SD pipelines, e.g., for two walls). Worth confirming design intent with Prav and verifying the PATH resolution issue (system Python spawning via relative `python` is not reliable long-term — safer to hardcode the venv python in whatever DAT is spawning).

---

## PART 5 — Architecture Overview (for remote troubleshooting)

### Components

**The main live render pipeline (confirmed April 13):**

```
Autolume (3090, GAN latent interpolation — Salish Sea model) 
    ↓  NDI: "DESKTOP-37616PR (Autolume Live)"
TouchDesigner/ndiin2 → StreamDiffusionTD (pass-through / minimal styling) → TD/ndiout2
    ↓  NDI: "DESKTOP-37616PR (TouchDesigner)"
Resolume Arena — mapping + video mixing
    ↓  HDMI × 2
Projection walls (Mahon Hall — 1× BenQ, 1× Epson)
```

**Note on StreamDiffusion:** the original vision was SD applying Briony-watercolor LoRA styling to Autolume's GAN output in real time, but SD-Turbo and SD 1.5 LoRA were never compatible. StreamDiffusion is currently running effectively as pass-through; the visual aesthetic on the walls is Autolume's GAN output directly. See `CLAUDE.md` "Briony Style Transfer" options for exhibition-time alternatives.

**Visitor prompt pipeline (in parallel):**

```
Visitor phone (QR) → Gallery server (poly, 37.27.48.12:9000, FastAPI)
    ↓  poll /td/next every 2s
Relay (3090, td_relay.py) → OSC port 7000
    ↓
TouchDesigner (applies visitor prompt to SD)
    ↓  (affects the NDI stream out to Resolume)
Walls
```

**Snapshot pipeline (drives the visitor web app preview):**

```
TD/ndiout2 → snap_runner DAT (every 600 frames) → C:\Users\user\Desktop\td_snap.jpg
    ↓  relay watches mtime, POSTs when changed
Gallery server /td/snapshot endpoint
    ↓  GET every ~2s from visitor.html
https://salishseadreaming.art/static/visitor.html — live preview
```

**Other outputs:**
- **Audio**: `gallery_ambient_audio.ps1` .NET SoundPlayer → stereo speakers (21-min .wav loop). Prav plans to swap this to an Ableton live-set after April 14.

### Watchdogs (all active as of April 12)

| Watchdog | Script | Interval |
|----------|--------|----------|
| TD | `scripts/td_watchdog.ps1` | 2 min |
| Relay | `scripts/relay_watchdog.ps1` | 2 min |
| Resolume | `scripts/resolume_watchdog.ps1` | 2 min |
| Display config | `C:\Users\user\display_watchdog.ps1` | 15 s |
| Health monitor | `C:\Users\user\installation_health.py` | periodic |
| SSH tunnel | Task Scheduler built-in | restart on failure |

Logs: `ssd_watchdog.log`, `display_watchdog.log`, etc. on the 3090 desktop.

### Gallery server endpoints

- `GET /td/next?after=N` — poll for new visitor prompts (monotonic seq)
- `POST /visitor/prompt` — visitor web app submits here
- Check health: `curl http://37.27.48.12:9000/health`

---

## PART 6 — Contacts

| Role | Name | Contact | When |
|------|------|---------|------|
| Technical lead | Darren Zal | **518-210-2828 (SMS)** or WhatsApp group | Any system issue |
| Creative director | Pravin Pillay | WhatsApp group | Gallery coordination |
| On-site fallback | Blair | — | Physical access to venue |
| Curator | Raf | — | Exhibition / visitor context |

**WhatsApp group** (Darren + Prav) is the fastest way to reach both of us at once.

---

## PART 7 — Change log

| Date | Change |
|------|--------|
| 2026-04-12 | Initial playbook. Verified live task list on 3090 (11 scheduled tasks). Display reshuffle gap confirmed solved via `SSD-Display-Watchdog` + MultiMonitorTool. Autolume autostart wrapper (`autolume_autostart.py`) built + deployed; enable pending Monday validation. |
| 2026-04-13 | (planned) Remote reboot test w/ Prav — validate full cold-boot sequence. |
| 2026-04-13 | BenQ EDID blackout observed during setup (Prav). Recovery: Resolume → Output → Advanced Output → reset. Added symptom rows to Parts 1 + 2 and known-gaps entry w/ mitigation ladder (refresh-rate pin → BenQ menu toggles → EDID emulator). |
| 2026-04-13 | BenQ mitigations applied (Prav): pinned to 1920×1080 @ 60 Hz + BenQ menu toggles. **Gotcha logged:** res change invalidated Resolume slice → required main-screen remap in Advanced Output. EDID copy-from-source dongles on order (staging 2) for Impact venue; may pre-stage for April if drops recur. Autolume transitions also working well. |
| 2026-04-13 | **BenQ confirmed as root cause of Resolume crashes** (Prav follow-up call): "once I changed the BenQ down, it stopped crashing Resolume." Status upgraded to ✅. Epson replacement planned for Impact. **New known issue: NDI flicker** — all NDI streams (Resolume + TD) drop offline briefly then recover. Likely capacity/routing. Diagnostics plan added. Tour-readiness plan drafted at `docs/tour-readiness-plan.md`. |
| 2026-04-13 | **Reboot test + deep NDI diagnostic.** Triggered remote reboot at 16:33. All auto-start tasks fired cleanly (TD, Resolume, Relay, SSH tunnel, watchdogs, NEW `SSD-Ambient-Audio`). Prav manually fixed three post-boot state issues: (1) BenQ Windows resolution reverted to 4K → manually re-pinned to 1920×1080; (2) SD came up at 1024×1024 → manually changed to 768 + saved; (3) Arena composition frozen on launch → clicked window to start playback, rearranged first clip to not reference Autolume. **Autolume wrapper validation failed** — `PickleWidget.load() got an unexpected keyword argument 'ignore_errors'` — SSD-Autolume task reverted to disabled + old launcher; Prav manual-launches Autolume. **BIGGEST FIND:** web-app visitor preview black because TD's `ndiin2` was listening for `MSI (Autolume Live)` but machine hostname is now `DESKTOP-37616PR`. Actual NDI name is `DESKTOP-37616PR (Autolume Live)`. Fixed at runtime via TD MCP — snap went from 11KB black → 430KB real content. Fix is ephemeral until .toe save. Likely same stale-hostname root cause for Arena "click to start" symptom and possibly earlier NDI flicker reports. Full April 14 morning checklist in `docs/tour-readiness-plan.md` Horizon 1. |
| — | (pre-Monday TODO) Phone-accessible `/admin/reboot` URL on gallery server so anyone in WhatsApp group can remote-reboot without laptop/SSH. |
| — | (planned) Enable + validate `SSD-Autolume` — load `network-snapshot-000120.pkl`, enter live performance mode. |
| — | (built, pending enable) Ambient audio auto-start via `gallery_ambient_audio.ps1` (SoundPlayer.PlayLooping). Swap to Ableton once Prav ports his mix from 3060. |
| — | (planned) Diagnostic chatbot — docent types "wall is black" → gets guided recovery + one-tap reboot button. |
