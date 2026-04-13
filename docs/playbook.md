# Salish Sea Dreaming — Gallery Operations Playbook

**Exhibition:** Digital Ecologies: Bridging Nature and Technology
**Venue:** Mahon Hall, Salt Spring Island
**Dates:** April 10–26, 2026
**Equipment location:** Mahon Hall (the 3090 tower is on-site in the gallery)

---

## PART 1 — Quick Reference Card (print & laminate)

### What "working" looks like

- The projection wall is **moving**, with watercolor-style marine imagery.
- You can see dreamy shapes: fish, kelp, light, sometimes visitor prompts appearing.
- Sound is playing (gentle ambient audio, looping).
- **If all three are true → the installation is healthy. Leave it alone.**

### If something looks wrong — try these in order

| # | Symptom | Action |
|---|---------|--------|
| 1 | **Black wall / no image** | Wait 2 minutes. The system auto-restarts itself. If still black → **Step 4**. |
| 2 | **Frozen image (not moving)** | Wait 2 minutes. If still frozen → **Step 4**. |
| 3 | **Image on wrong wall** | Wait 30 seconds — display watchdog auto-restores projector assignments. If still wrong → **Step 4**. |
| 4 | **No sound** | Check the speaker power and volume knob. If still silent → **Step 5**. |
| 5 | **Still broken after waiting** | **Text Darren: 518-210-2828** (or message the WhatsApp group) with a photo of the wall. |

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
| Visitor prompts not appearing | Relay or gallery server down | Text Darren. | Relay watchdog restarts it. Server may need manual check. |
| Pixelated / low quality | Projector resolution mismatch | Text Darren. | Remote fix possible. |

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

**10:45 AM — walk-in check (5 min):**

1. Look at the wall. Is it moving?
2. Listen. Is sound playing?
3. Stand back and take a photo of the installation.
4. **If anything looks off → text Darren immediately** (gives us 15 min before opening).

**If you had to remote-reboot overnight:** allow 3–5 minutes for all services to come up before assessing.

### During gallery hours

- Walk past every ~hour. If still moving + sound → fine.
- Log any visitor comments / questions in the notebook.
- If the wall goes black mid-visit, smile at visitors and say "it's self-healing, give it a moment" — the watchdogs usually catch it within 2 minutes.

### Closing (gallery closes 5:00 PM)

- The installation keeps running overnight — **do not shut anything down**.
- Take a photo of the wall as you leave (for the morning comparison).

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

### Autolume boot sequence (manual — not yet automated)

Prav's instructions: Autolume needs to boot with **320/120 pkl file** animating from **Autolume live performance mode**. 3 instances expected.

**TODO (before April 13 test):** Convert this to a Task Scheduler auto-start.

### Known gaps (cold-boot test priorities — April 13)

- ❗ **Autolume auto-start is broken.** `SSD-Autolume` task is **disabled**. Existing `launch_autolume.bat` only runs `python main.py` — opens the GUI but doesn't load a .pkl model or enter live performance mode. `autolume_launch.bat all` loads 3 instances (fish-400kimg.pkl / whale.pkl / bird.pkl) but Prav referenced a specific "320/120 pkl" file — need to confirm which model + how to auto-enter live performance mode. **The 3 Autolume instances currently running were launched manually and will be lost on reboot.**
- ❗ **Ambient audio has no auto-start.** Ableton Live 12 Suite is currently running (presumably playing the loop) but no scheduled task or Startup folder entry launches it on logon. Same story: running now, lost on reboot. Need either a task that opens the .als file, or a simpler media-player loop.
- ✅ **Resolume auto-start — confirmed working.** `SSD-Resolume` is "At logon time" with `Last Result: 0`. Task status shows "Ready" because the launcher bat exits after `start ""` — Arena.exe itself is what runs. Verified via `tasklist | findstr Arena` (Arena.exe PID 132748).
- ✅ **TouchDesigner auto-start — confirmed working.** `SSD-TouchDesigner` "At logon time", launches `SSD-exhibition.toe` after 30s ping delay.
- ✅ **Display ID reshuffle — solved.** `SSD-Display-Watchdog` polls every 15s, detects display count changes, waits 15s for HDMI settle, runs `MultiMonitorTool /LoadConfig display_config.cfg`.

---

## PART 5 — Architecture Overview (for remote troubleshooting)

### Components

```
Visitor phone (QR)
    ↓
Gallery server (poly, 37.27.48.12:9000) — FastAPI, queues prompts
    ↓  (polled every 2s)
Relay (3090, td_relay.py) — pulls /td/next, sends via OSC
    ↓  (OSC port 7000)
TouchDesigner (3090) — StreamDiffusion styles the image
    ↓  (NDI / capture)
Resolume (3090) — mapping + video mixing → projectors
    ↓  (HDMI × 2)
Projection wall (Mahon Hall)
```

Parallel:
- **Autolume** (3090) → separate projection output (320/120 pkl latent animation)
- **Audio**: media player on 3090 → stereo speakers (looped ambient)

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
| 2026-04-12 | Initial playbook. Verified live task list on 3090 (11 scheduled tasks). Display reshuffle gap confirmed solved via `SSD-Display-Watchdog` + MultiMonitorTool. |
| 2026-04-13 | (planned) Remote reboot test w/ Prav — validate full cold-boot sequence. |
| — | (pre-Monday TODO) Phone-accessible `/admin/reboot` URL on gallery server so anyone in WhatsApp group can remote-reboot without laptop/SSH. |
| — | (planned) Enable + validate `SSD-Autolume` — load `network-snapshot-000120.pkl`, enter live performance mode. |
| — | (planned) Ambient audio auto-start — WMP-on-loop launcher now; Ableton session after Prav ports it from 3060. |
| — | (planned) Diagnostic chatbot — docent types "wall is black" → gets guided recovery + one-tap reboot button. |
