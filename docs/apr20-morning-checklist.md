# Apr 20 Morning — 3090 Operator Checklist

**Purpose:** the keyboard-and-eyes actions Prav (or Zoe, or whoever is at the gallery) performs Apr 20 morning. Darren supports remotely via Signal / voice the moment step 1 completes.

**Time budget:** 5 min for the critical unblocking actions (steps 1–3). Everything else happens with Darren guiding remotely.

---

## Step 1 — Restart SSH tunnel (2 min) ★ DO THIS FIRST ★

**Why:** Darren has no remote access to the 3090 until this is done. The SSH tunnel's reconnect loop stopped at 16:50 PDT Apr 19 and hasn't recovered. Once you run the command below, remote access is restored.

At the 3090 keyboard, open a PowerShell (Start menu → type PowerShell → enter), and run:

```powershell
schtasks /run /tn "SSD-SSH-Tunnel"
```

Expect: "SUCCESS: Attempted to run the scheduled task"

Tell Darren over Signal — he'll confirm he's back in within ~30 seconds.

**If that command fails,** run the script directly:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\ssd_ssh_tunnel.ps1
```

Leave that PowerShell window open — it's the tunnel process.

---

## Step 2 — Confirm remote access (1 min)

Darren's side: `ssh windows-desktop-remote` works → replies "I'm in."

If Darren can't get in within 2 minutes of step 1, something's weirder than we think. Fall back to: on the 3090, run `.\apr20_deploy_bootstrap.ps1` (see step 4) which is self-contained + doesn't need remote access from Darren.

---

## Step 3 — Verify core stack is running (30 sec)

At the 3090 keyboard:

```powershell
Get-Process TouchDesigner, Arena -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, StartTime
```

Expect: both processes listed. If either is missing, tell Darren — he'll diagnose from there.

---

## Step 4 — One-command deploy of Apr 20 updates (2 min, OPTIONAL)

If Darren is NOT available or things need to proceed without him, the 3090 can self-deploy today's Apr 20 items (Resolume watchdog + downloads the Windows Update block script). Run this single command in PowerShell:

```powershell
iex (iwr https://salishseadreaming.art/graph-assets/deploy/apr20/apr20_deploy_bootstrap.ps1).Content
```

What it does:
1. Creates `C:\Users\user\heartbeats\`
2. Downloads the upgraded `resolume_watchdog.ps1` (with exponential backoff + heartbeat)
3. Registers `SSD-Resolume-Watchdog-v2` scheduled task
4. Downloads `heartbeat_manifest.json` for future meta-watchdog
5. Downloads `windows_update_block.ps1` (doesn't run it — separate step below)
6. Runs a synthetic test: kills Arena, verifies watchdog restarts it within 3 min
7. Logs everything to `C:\Users\user\Desktop\apr20_deploy.log`

**This is safe to run with Darren on the call — he can narrate what's happening.**

---

## Step 5 — Windows Update lockdown (3 min, when ready)

Prav explicitly approved this Apr 19 Signal: "Can we stop windows updates - that is just bad."

After step 4, with Darren watching:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\windows_update_block.ps1
```

Log: `C:\Users\user\Desktop\windows_update_block.log`

Verification: `gpresult /r | Select-String WindowsUpdate` should show `NoAutoUpdate: 1`.

**Also requires manual step** (Windows doesn't expose via registry):
- Settings → Network & Internet → (active adapter) → Metered connection: ON

---

## Step 6 — Tailscale-as-secondary setup (5 min, Prav-driven)

Discussed + approved per Apr 20 walkthrough phase 4.9. Gives us a second independent remote-access path so today's tunnel outage can never block us again.

At the 3090 keyboard:

```powershell
tailscale status
```

Expect: shows the machine is signed in and connected. If not signed in, open Tailscale app from the system tray and sign in with Prav's account.

Then on Prav's phone or browser: admin.tailscale.com → invite Darren's Mac (`zaldarren@gmail.com`) as a user or share a specific device.

Darren's side: Darren opens Tailscale on his Mac, accepts invitation, tests `ssh windows-desktop-tailscale`.

---

## Step 7 — Hardware reality check (5–10 min, Darren-driven questions)

Physical inspection Prav does while Darren watches remotely:

- **Any USB mic connected?** Check the back + front of the tower for any USB mic, 3.5mm jack, or wireless receiver. Report make/model if present.
- **Where does computer audio-out go?** Trace the cable: splitter? Direct to one device? Photo helps.
- **Wireless headphones:** Bluetooth-paired or analog through a transmitter?
- **Camera:** any connected?

Answers feed directly into whether today's silence detector is monitoring real hardware.

---

## Post-walkthrough (when gallery opens at 11 AM)

Nothing here is time-sensitive after the steps above. You've restored remote access (step 1), deployed the Arena watchdog (step 4), and blocked Windows updates (step 5). The installation is protected against the two recurring failures we've observed.

Darren will do a final review on Signal when done.

---

## Emergency contacts

- Darren — Signal / 518-210-2828
- Prav on-site at Mahon Hall unless Vancouver-Island-trip day
- Raf — curator, gallery operational issues only (not tech)

## Revert path

If anything from step 4 or 5 causes a problem, revert via:

```powershell
# Undo Apr 20 deploy
schtasks /delete /tn "SSD-Resolume-Watchdog-v2" /f
powershell -ExecutionPolicy Bypass -File C:\Users\user\windows_update_block.ps1 -Unblock
```

The original April-12 `resolume_watchdog.ps1` is preserved in git at tag `v-pre-resolume-wd`.
