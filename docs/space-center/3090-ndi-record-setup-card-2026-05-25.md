# 3090 NDI-Record Setup Card

**Built 2026-05-25 as fallback for Pravin's Resolume composition recording.**
**For use when someone's at the 3090 with UI access (HRMSC Monday or remote desktop).**

## Pre-staged on 3090

Location: `C:\Users\user\ndi-record-setup\`

| Component | File | Status |
|---|---|---|
| OBS Studio 32.1.2 | `OBS-Studio-installer.exe` (158 MB) | ✅ already installed at `C:\Program Files\obs-studio\` |
| NDI Tools 6 | `NDI-Tools.exe` (565 MB) | ✅ already installed at `C:\Program Files\NDI\NDI 6 Tools` (since March) |
| DistroAV plugin | `DistroAV-installer.exe` (3.3 MB) — bypassed via portable ZIP | ✅ installed at `%APPDATA%\obs-studio\plugins\distroav\` (per-user, no admin needed) — `distroav.dll` 617 KB + locale data |

## Remaining steps (~5-10 min, GUI required)

All software is installed. Remaining steps are OBS configuration only.

### 1. Open OBS Studio (first run will create config files)

Start menu → OBS Studio. On first launch it'll run the auto-configuration wizard — pick **"Optimize for recording, I will not be streaming"** so it tunes for local recording quality, not live streaming.

### 2. Configure NDI source

- Sources panel → **+** → **DistroAV NDI Source** → name it (e.g. "Pravin Resolume")
- Pick Pravin's Mac NDI feed from the dropdown (his Mac must have NDI output enabled in Resolume)
- Click OK

You should see his composition preview in OBS canvas.

### 3. Configure recording

- Settings → **Output** → tab to **Recording** sub-section
- Recording Format: **MP4** (or MKV for crash-safety, can remux to MP4 after)
- Encoder: **NVIDIA NVENC H.264** (uses dedicated hardware, won't fight Autolume's CUDA cores)
- Bitrate: **40 Mbps** (good projection-grade for 4K), or 60 Mbps if disk space allows
- Recording Path: anywhere on C:\ — there's **371 GB free** as of 2026-05-25 09:00 PDT, can confirm with `fsutil volume diskfree C:` before going

### 4. Configure video

- Settings → **Video**
- Base (Canvas) Resolution: match Pravin's Resolume composition (likely **3840x2160** or **1920x1080**)
- Output (Scaled) Resolution: same as base (no scaling)
- FPS: match Pravin's composition (30 or 60)

### 5. Test recording first

Hit **Start Recording** for 30 sec, **Stop Recording**, verify the file plays cleanly in QuickTime/VLC. If it works, real run.

### 6. The real run

Pravin's Resolume composition running → his Mac NDI Output on → OBS on 3090 shows his feed in the canvas preview → hit **Start Recording** → leave it running for the 20-min loop length → hit **Stop Recording** → file lands at your configured path.

## File size math at 40 Mbps NVENC H.264

| Duration | File size |
|---|---|
| 5 min | ~1.5 GB |
| 20 min | ~6 GB |
| 60 min | ~18 GB |

371 GB free → plenty of headroom even for multiple takes.

## Notes

- **NVENC won't fight Autolume**: NVIDIA's NVENC is dedicated hardware blocks on the GPU separate from the CUDA cores Autolume uses. Both can run simultaneously without contention.
- **NDI works on the LAN**: Pravin's Mac and the 3090 must be on the same network. Studio LAN at 108 Fraser Rd is fine. HRMSC LAN should also be fine once both machines are there.
- **If NDI source doesn't appear in OBS**: check Pravin's Resolume → Output → NDI is turned on, and his Mac firewall isn't blocking NDI mDNS (port 5353) or NDI streams (port range 5960-5990).
- **Recording during live performance**: OBS recording is non-blocking — Pravin can keep composing live; OBS just captures the output stream. He doesn't have to babysit OBS.
