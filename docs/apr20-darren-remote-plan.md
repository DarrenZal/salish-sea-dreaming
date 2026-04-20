# Apr 20 — Remote plan Darren runs over SSH

Once Prav runs `schtasks /run /tn "SSD-SSH-Tunnel"` and I confirm
`ssh windows-desktop-remote` works, execute the following over SSH. Most
of this happens in parallel with Prav doing dongle install + hardware
walk-around.

**Prereq Darren did on 2026-04-19 evening:**

1. Decided against Tailscale (Mac GUI client broken; CLI needs running
   GUI app; blocks Anthropic API when connected). Pivoted to WireGuard
   via the existing `wg-koi` network on poly.
2. Generated 3090 WireGuard keypair → stored at
   `~/.config/ssd/wg/3090_private.key` (mode 600, outside any git repo).
3. Wrote 3090's WireGuard config → `~/.config/ssd/wg/wg-koi-3090.conf`
   (mode 600). 3090's assigned WG IP: `10.100.0.30`.
4. Added 3090 as peer on poly — runtime (`sudo wg set`) + persistent
   (appended to `/etc/wireguard/wg-koi.conf`, backup taken). Verified
   via `sudo wg show wg-koi`.
5. TODO tonight if not already done: bring up Mac's wg-koi and confirm
   Mac ↔ poly reachability (`ping 10.100.0.1`). Needs Mac sudo once.

No Prav involvement. Existing Tailscale auth key (memory file
`project_tailscale_authkey_apr20.md`) is **unused** — can be revoked at
admin.tailscale.com any time; it expires in 24h regardless.

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

### 2. WireGuard install + tunnel on 3090 (5 min)

From Darren's Mac (after SSH tunnel back up via step 0):

```bash
# Copy the pre-written config to the 3090
scp ~/.config/ssd/wg/wg-koi-3090.conf \
    windows-desktop-remote:C:/Users/user/wg-koi.conf
```

Then on 3090 via SSH:

```powershell
# Download WireGuard for Windows (silent MSI install)
Invoke-WebRequest -Uri "https://download.wireguard.com/windows-client/wireguard-installer.exe" -OutFile "C:\Users\user\wireguard-installer.exe"
Start-Process -FilePath "C:\Users\user\wireguard-installer.exe" -ArgumentList "/S" -Wait

# Install the tunnel as a Windows service (auto-start on boot)
& "C:\Program Files\WireGuard\wireguard.exe" /installtunnelservice "C:\Users\user\wg-koi.conf"

# Verify
Get-Service WireGuardTunnel`$wg-koi
& "C:\Program Files\WireGuard\wg.exe" show
```

From Darren's Mac, after confirming the tunnel is up on 3090:

```bash
# Test reachability over WG
ping -c 3 10.100.0.30

# Add SSH alias for the WG path
cat >> ~/.ssh/config <<'EOF'

# Backup path via WireGuard (wg-koi network through poly)
Host windows-desktop-wg
  HostName 10.100.0.30
  User user
  IdentityFile ~/.ssh/id_ed25519
EOF

# Test SSH over WireGuard (should work independent of the poly SSH tunnel)
ssh windows-desktop-wg "hostname; whoami"
```

Now we have two independent paths:
- **Primary:** `ssh windows-desktop-remote` (reverse SSH tunnel via poly:2222)
- **Backup:** `ssh windows-desktop-wg` (WireGuard mesh via poly's wg-koi)

Both depend on poly being up. If poly dies, both die. Considered
acceptable for April; a second-VPS or cloudflared fallback is a
post-show hardening item.

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

### 5. Rewrite gallery_audio.py to WASAPI loopback (15 min)

Hardware walk-around resolved ahead of time via Signal 2026-04-19:
3090 has **no mic, no camera**; audio = 3.5mm → splitter → wired +
Bluetooth broadcaster. The existing input-side silence detector
(`AUDIO_DEVICE_INDEX=0`) is watching nothing meaningful.

Replacement approach: WASAPI loopback on the **default playback device**
to peak-detect the signal actually going out to the splitter. Catches
Ableton/WMP crashes, app silence, mute events. Does NOT catch
BT-broadcaster pairing failures (known gap, not solving in April).

Patch `scripts/gallery_audio.py`:
- Replace `sounddevice.InputStream` with a WASAPI loopback stream via
  `sounddevice.WasapiSettings(loopback=True)` on the default output
  device, OR use `pyaudio` if `sounddevice` loopback is flaky on 3090.
- Keep the existing rolling-window volume + `ssd_audio_state.json`
  snapshot writer — just change the data source.
- Re-test: `python gallery_audio.py --list-devices` → identify the
  default output device → confirm loopback captures peak when audio is
  playing.

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
- [ ] `ssh windows-desktop-wg "hostname"` succeeds → WireGuard backup path live
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
