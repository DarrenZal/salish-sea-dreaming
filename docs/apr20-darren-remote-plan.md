# Apr 20 — Remote plan Darren runs over SSH

Once Prav runs `schtasks /run /tn "SSD-SSH-Tunnel"` and I confirm
`ssh windows-desktop-remote` works, execute the following over SSH. Most
of this happens in parallel with Prav doing dongle install + hardware
walk-around.

**Prereq Darren does himself tonight:**

1. Sign up at tailscale.com with `zaldarren@gmail.com` (Google SSO, free
   tier). This creates Darren's tailnet.
2. admin.tailscale.com → Settings → Keys → Generate auth key. Reusable,
   ephemeral off, 24h expiry. Copy the `tskey-auth-xxxxx` value — will
   paste into step 2 below.
3. Confirm Tailscale is installed + signed in on Darren's Mac (already
   installed per Apr 19 screenshot; just sign in with the same Google
   account).

No Prav involvement in Tailscale setup. The 3090 joins Darren's tailnet,
not Prav's.

---

## Sequence

### 1. Arena watchdog + Windows Update block + heartbeat manifest (10 min)

One command runs the whole pre-staged bundle on the 3090:

```powershell
iex (iwr https://salishseadreaming.art/graph-assets/deploy/apr20/apr20_deploy_bootstrap.ps1).Content
```

Does: heartbeats/ dir, resolume_watchdog.ps1, SSD-Resolume-Watchdog-v2
task, heartbeat_manifest.json, downloads windows_update_block.ps1,
runs synthetic Stop-Process Arena sanity test. Logs to
`C:\Users\user\Desktop\apr20_deploy.log`.

Then run the Windows Update block:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\windows_update_block.ps1
```

Verify: `gpresult /r | Select-String WindowsUpdate` → `NoAutoUpdate: 1`.

### 2. Tailscale install + auth (5 min)

```powershell
# Silent install (try winget first, fall back to direct MSI)
winget install --id Tailscale.Tailscale -e --silent --accept-package-agreements --accept-source-agreements

# If winget unavailable, fallback:
# Invoke-WebRequest -Uri "https://pkgs.tailscale.com/stable/tailscale-setup-latest.exe" -OutFile "C:\Users\user\tailscale-setup.exe"
# Start-Process -FilePath "C:\Users\user\tailscale-setup.exe" -ArgumentList "/S" -Wait

# Auth using Prav's pre-generated key
& "C:\Program Files\Tailscale\tailscale.exe" up --authkey=tskey-auth-REDACTED --accept-routes

# Verify
& "C:\Program Files\Tailscale\tailscale.exe" status
```

On my Mac in parallel: ensure Tailscale signed in with my account
(already invited as user on Prav's tailnet), then:

```bash
ssh user@<3090-tailscale-ip>
```

Add `windows-desktop-tailscale` to `~/.ssh/config`.

### 3. Daily diagnostic scheduled task (3 min)

```powershell
schtasks /create /tn "SSD-Daily-Diagnostic" /tr "powershell -ExecutionPolicy Bypass -File C:\Users\user\daily_diagnostic.ps1" /sc DAILY /st 09:15 /ru "user" /rl HIGHEST /f
schtasks /run /tn "SSD-Daily-Diagnostic"  # test fire
```

Verify Telegram received the message.

### 4. System health scans (background, fire-and-forget)

```powershell
# Runs ~10-20 min in the background; doesn't block us
Start-Process -FilePath "cmd.exe" -ArgumentList "/c sfc /scannow > C:\Users\user\Desktop\sfc_scan.log 2>&1" -WindowStyle Hidden
```

Check later: `Get-Content C:\Users\user\Desktop\sfc_scan.log`.

### 5. Answer Prav's hardware questions → update gallery_audio.py (5 min)

Based on Prav's walk-around answers (mic? audio-out path? camera?),
either:
- confirm current `AUDIO_DEVICE_INDEX=0` monitors a real mic (leave alone),
- or switch the silence detector to a loopback / WASAPI output device.

Patch `scripts/gallery_audio.py` on the 3090 as needed.

### 6. Autolume cache revert (deferred to tomorrow evening)

Only after Prav is gone and things are stable:
- install CUDA 12.4 (silent MSI install, `-s` flag)
- revert `autolume/torch_utils/ops/params.py` `use_custom = True`
- test autolume relaunch

This is the day's nice-to-have, not blocker.

---

## Verification before calling it done

Before Prav leaves at 10:30:
- [ ] `schtasks /query /tn "SSD-Resolume-Watchdog-v2"` → State: Running
- [ ] `Test-Path C:\Users\user\heartbeats\resolume_watchdog.hb` → True
- [ ] `Get-Content C:\Users\user\Desktop\apr20_deploy.log` → PASS on synthetic
- [ ] `gpresult /r | Select-String WindowsUpdate` → NoAutoUpdate: 1
- [ ] `tailscale status` → 3090 online; Darren's Mac can `ssh windows-desktop-tailscale`
- [ ] Visitor prompt smoke test → Prav confirms wall + audio
- [ ] Daily diagnostic test message received on Telegram

If any of these fail, hold Prav until resolved or rolled back.

## What still needs Prav (can't be done over SSH)

- The tunnel restart itself (obviously — no remote access yet)
- Plugging the dongle into the tower
- Looking at the physical cables / devices and answering questions
- Watching the wall + hearing the audio during smoke test
- The `Metered connection: ON` Wi-Fi toggle (Windows doesn't expose via
  registry) — we can defer this; Prav can do it anytime during the week
  or Zoe can during opening

That's it. Total Prav keyboard/body time ~15 min, not 60.
