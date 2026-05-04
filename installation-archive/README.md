# Installation Archive — 3090 Snapshot 2026-05-03

Snapshot of the full installation auto-launch + self-healing stack from the 3090 (`windows-desktop`, `DESKTOP-37616PR`) at exhibition end. Captured before returning the machine to regular dev mode at Prav's request.

**Pulled from:** `C:\Users\user\` and `C:\Users\user\Desktop\` on the 3090, via WireGuard SSH (`windows-desktop-wg` → `10.100.0.30`).

## Contents

### `scripts/` (64 files)
Everything in `C:\Users\user\` — Python relays, PowerShell watchdogs, batch launchers, AHK kicker, and the (gitignored on remote) `.ssd_secrets.ps1` Telegram credentials.

Notable:
- `td_relay.py` — visitor-app HTTP→OSC bridge into TouchDesigner
- `gallery_audio.py` — audio reactivity capture (note: WASAPI loopback rewrite still TODO)
- `resolume_watchdog.ps1`, `td_watchdog.ps1`, `autolume_watchdog.ps1` — auto-restart logic
- `meta_watchdog.ps1` — orchestrator that re-enables disabled child watchdogs
- `health_probe.ps1` — periodic Telegram health beacon
- `tunnel_watchdog.ps1` — keeps `SSD-SSH-Tunnel` alive

### `tasks/` (23 XML files)
Full Task Scheduler XML exports for every `SSD-*` task. Re-importable via:
```powershell
schtasks /create /tn SSD-Resolume /xml SSD-Resolume.xml /ru user
```

### `toe/` (8 files)
Latest tip of each TouchDesigner project lineage on the Desktop (Backup/ folder of intermediate auto-saves NOT pulled — too many revisions, low value):
- `SSD_gallery_2026-04-06_0321.14.toe` — **production gallery file** (Apr 7)
- `SSD-exhibition.12.toe` — exhibition variant (Apr 13)
- `SSD-exhibition_Backup.toe` — pre-exhibition backup
- `default_stream_diffusion.toe` — SDTD baseline example (renamed from `default stream diffusion.toe`)
- `Checkpoint-HerringSDExample.19.toe` — herring SD experiment tip
- `FantasticSSD1+New.toe` — Fantastic lineage tip
- `202604061259_FantasticSSD1New.1.toe` — Fantastic later branch (renamed from `202604061259 FantasticSSD1+New.1.toe`)
- `Weresoback.2.toe` — recovery experiment

The original Saturday-VJ `.toe` (`SSD_gallery_2026-04-06_0321.13.toe` per CLAUDE.md) was bundled to Proton Drive on 2026-04-23 with assets — not re-archived here since Drive copy is canonical.

## What changed on 3090 to return to dev mode

**Disabled tasks** (still defined, just won't auto-trigger; re-enable with `schtasks /change /tn <name> /enable`):
- Round 1 (resolume + TD/SD per Prav's first ask):
  `SSD-Resolume`, `SSD-Resolume-Watchdog`, `SSD-Resolume-Watchdog-v2`,
  `SSD-Resolume-Kick`, `SSD-Resolume-Rebind-UIA`, `SSD-Resolume-UIA-Probe`,
  `SSD-TouchDesigner`, `SSD-TD-Watchdog`, `SSD-Meta-Watchdog`
- Round 2 (full installation stack down):
  `SSD-Ambient-Audio`, `SSD-Audio`, `SSD-Autolume`, `SSD-Autolume-Watchdog`,
  `SSD-Daily-Diagnostic`, `SSD-Display-Restore`, `SSD-Display-Watchdog`,
  `SSD-Health-Monitor`, `SSD-Health-Probe`, `SSD-Post-Boot-Verify`,
  `SSD-Relay`, `SSD-Relay-Watchdog`

**Kept enabled** (so we can SSH in):
- `SSD-SSH-Tunnel` — reverse tunnel to poly:2222
- `SSD-Tunnel-Watchdog` — keeps the tunnel alive

## To return to installation mode

Re-enable every disabled task. Or if a task is missing entirely (deleted later), re-import its XML from `tasks/`.

```powershell
# Enable all SSD-* tasks
Get-ScheduledTask -TaskName "SSD-*" | Enable-ScheduledTask
```
