# Installation Archive — IMPACT 2026 (3090 Snapshot 2026-06-10)

Snapshot of the production auto-launch + self-healing stack from the 3090 (`windows-desktop`, `DESKTOP-37616PR`) as it ran for the **Indigenomics IMPACT 2026** show at the HR MacMillan Space Centre, **May 27–28, 2026** (Hubble surface = SSD installation). Captured ~13 days post-show while returning the machine to R&D mode.

**Pulled from:** `C:\Users\user\` and `C:\Users\user\Desktop\` on the 3090, via direct LAN SSH (`ssh windows-desktop` → `192.168.1.68`; the box is now at Darren's house, not Prav's studio).

**Companion (April show):** `../README.md` is the prior April 2026 Salt Spring exhibition snapshot. This is the second show archived under the same pattern.

## Contents

### `toe/` (1 file)
- `SSD-exhibition.toe` — **production gallery file** (last modified 2026-05-28 16:01, mid-show; 0.77 MB, pulled with `scp -O` to avoid the macOS 200 KB truncation bug). The `.13.toe` autosave increment is the same file and was not separately pulled. The 53 intermediate `Desktop\Backup\` autosaves were not pulled (low value, high revision count). Older lineage tips (`SSD_gallery_*`, `FantasticSSD*`, `Weresoback`, herring SD examples) are already in `../toe/` from the April archive.

### `tasks/` (27 XML files)
Full Task Scheduler XML exports for every `SSD-*` task as defined on 2026-06-10 (4 more than the April archive's 23 — adds the NDI/fire/sweep tasks from the May sprint). Re-importable via:
```powershell
schtasks /create /tn SSD-TouchDesigner /xml SSD-TouchDesigner.xml /ru user
```

### `scripts/` (19 files)
The IMPACT-relevant delta on top of the April archive's 64 scripts — the NDI toolchain, relay, autolume launchers, and show-day fixes added/changed during the May sprint:
- `td_relay.py` — visitor-app HTTP→OSC bridge into TouchDesigner (21.7 KB; grew from the April version)
- `td_ndi.py`, `td_ndi_inspect.py`, `td_probe.py`, `ndi_find.py`, `ndi_check.ps1` — **NDI source switching + inspection toolchain** (new this show; remote NDI source management)
- `autolume_autostart.py` — Autolume launcher (120-kimg PKL `network-snapshot-000120.pkl`, preset 0)
- `autolume_sweep.py`, `autolume_walk_test.bat` — parameter-sweep / latent-walk render drivers
- `gallery_audio.py`, `resolume_fade.py`, `gallery_resolume_refresh.py` — audio reactivity + Resolume control
- `fix_visitor_snapshot_timing.py` — show-day fix for visitor snapshot poll cadence
- `installation_health.py`, `wasapi_probe.py`, `check_procs.ps1` — health/diagnostic
- `fire_smooth_20260524_2030.bat`, `fire_20min_*.bat`, `fire_baseline_long_*.bat` — timed render-fire batches from the May 23–24 tuning

### `pre-rd-task-states-2026-06-10.txt`
The "before" snapshot: SSD-* task states + running show processes (TouchDesigner, 2× `td_relay.py`, Autolume + workers, 2× `streamdiffusionTD/td_main.py`, Ableton applet) captured at 2026-06-10 17:13 immediately before quiescing to R&D mode. The "after" is in the next section.

## What changed on the 3090 to reach R&D mode (2026-06-10)

20 of 27 SSD-* tasks were **already disabled** before this session (left over from the April→May transitions). This session quiesced the 5 still-active show tasks:

**Stopped + disabled (2026-06-10):**
- `SSD-Autolume`, `SSD-Autolume-Watchdog` — live generative stack
- `SSD-Relay` — `td_relay.py` visitor HTTP→OSC bridge
- `SSD-TD-Watchdog` — would otherwise relaunch TouchDesigner
- `SSD-TouchDesigner` — gallery runtime (was *Ready*; logon trigger disabled)

Then the leftover live processes were force-killed (TouchDesigner, the autolume/relay/streamdiffusion python set, Ableton applet) so the box went idle without a reboot. Note: the pre-RD snapshot showed **duplicate** `td_relay.py` and `streamdiffusionTD/td_main.py` instances — instance drift from the show run; a clean stop resolved it.

**Kept enabled / running (remote access):**
- `SSD-SSH-Tunnel` — reverse tunnel to poly:2222
- `SSD-Tunnel-Watchdog` — keeps the tunnel alive

Verified end-state: only the two tunnel tasks Running, zero show processes, SSH reachable.

## To return to installation mode

Re-enable the show tasks (still defined, just won't auto-trigger):
```powershell
Enable-ScheduledTask -TaskName "SSD-Autolume","SSD-Autolume-Watchdog","SSD-Relay","SSD-TD-Watchdog","SSD-TouchDesigner"
```
Or re-import any deleted task from `tasks/` via `schtasks /create ... /xml`.

## Known operational quirks (carry-forward)

- **NDI source name reverts on reboot** — TouchDesigner's `.toe` NDI source resets to the MSI machine name after a reboot; a persistent NDI config is needed (the `td_ndi.py` / `ndi_check.ps1` toolchain in `scripts/` was the May workaround). See project memory `project_ndi_source_name_reverts_on_reboot`.
- **Large-file transfer** — upload 3090 files directly to Google Drive rather than scp-through-WireGuard (faster). See `project_large_file_transfer_3090_to_drive`.
- **`.toe` over scp** — always `scp -O` (legacy protocol) for binary `.toe` pulls; plain scp silently truncates at 200 KB.
- **Access routes** — `ssh windows-desktop` (LAN 192.168.1.68, while at Darren's house), `windows-desktop-tailscale` (100.91.172.10, stable), `windows-desktop-remote` (reverse tunnel through poly, from anywhere).

## Not archived here (intentional)

- ~200 GB of regenerable cache/renders on the 3090 (`.cache/huggingface` 94 GB, `Videos/` show recordings 68 GB, Desktop render exports ~28 GB) — listed as candidates in `docs/space-center/3090-disk-archive-candidates.md` for a future free-up pass when an external destination is chosen.
- NDI installer binaries in `C:\Users\user\ndi-record-setup\` (539 MB; re-downloadable).
- Visitor-dream DB content — consent-sensitive, snapshotted separately in `../../private-archive/` (gitignored).
