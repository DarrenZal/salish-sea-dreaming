# 3090 Video Editing Toolchain — CLI/MCP-driven from Claude Code

**Built 2026-05-25** for cropping + masking work on captured footage. All driven from Claude Code over SSH (`windows-desktop-wg` / `10.100.0.30` via WireGuard). Files stay on the 3090; GPU + CPU work happens there; we only send commands across the wire.

## Installed stack

| Tool | Version | Where | Purpose |
|---|---|---|---|
| ffmpeg | system-wide | (already there) | Cropping, transcoding, NVENC hardware accel, simple masks |
| Python 3.11.9 | `py` launcher | `C:\Users\user\AppData\Local\Programs\Python\Python311\` | Scripting host |
| Python 3.10 | `python` | `C:\Program Files\Python310\` | (Autolume env, leave alone) |
| Pillow | 11.3.0 | py 3.11 site-packages | Mask PNG generation (geometric shapes, gradients, alpha channels) |
| numpy | 2.4.6 | py 3.11 site-packages | Array ops, perlin noise, mask blending |
| moviepy | 2.2.1 | py 3.11 site-packages | Programmatic timeline composition — multi-clip concat, crossfades, subclip, audio mixing |
| imageio + imageio_ffmpeg | 2.37.3 / 0.6.0 | py 3.11 site-packages | moviepy deps; bundled ffmpeg fallback |

Verified install (smoke test): `from PIL import Image, ImageDraw; import numpy as np; from moviepy import VideoFileClip, concatenate_videoclips`.

## Capability matrix

| Job | Tool | Notes |
|---|---|---|
| Static rectangle crop | `ffmpeg -vf "crop=W:H:X:Y"` | One-liner |
| Animated pan-and-scan crop | `ffmpeg -vf "crop=W:H:'X(t)':'Y(t)'"` | Time expressions |
| Split 5120×1600 → 2× 2560×1600 | `ffmpeg -filter_complex "[0:v]split=2[L][R];[L]crop=2560:1600:0:0[Lout];[R]crop=2560:1600:2560:0[Rout]"` | Left + right halves |
| Rectangle / circle / ellipse mask | Pillow `ImageDraw` → PNG → ffmpeg overlay | I generate PNG via script, apply via overlay filter |
| Polygon mask (fixed points) | Pillow `ImageDraw.polygon` → PNG → ffmpeg overlay | Same pattern |
| Soft-edge / feathered mask | Pillow + `ImageFilter.GaussianBlur` on alpha → overlay | Smooth edges |
| Radial vignette | `ffmpeg -vf "vignette=angle=PI/5"` | Built-in |
| Animated keyframed shape | Pillow generates N PNG frames → ffmpeg image2 sequence → overlay | More work, but doable |
| Multi-clip timeline w/ crossfades | moviepy `concatenate_videoclips([c.crossfadein(1) for c in clips])` | Python script |
| HAP encode for Resolume | `ffmpeg -c:v hap -format hap out.mov` | GPU-decoded by Resolume |
| ProRes 422 HQ for portability | `ffmpeg -c:v prores_ks -profile:v 3 out.mov` | Apple ecosystem-friendly |
| Scene detection / cut list | `ffmpeg -vf "select='gt(scene,0.3)',showinfo"` | Find scene changes |

## NOT yet covered (defer until needed)

| Job | Why not now | When to add |
|---|---|---|
| Hand-drawn / freehand rotoscope masks | Needs visual GUI | Install **Natron** (FOSS, ~250 MB, scriptable Python) |
| Motion-tracked roto | Same | Natron with Mocha-style tracker, or **Blender VSE compositor** |
| Visual timeline scrubbing | Same | Install **Shotcut** (FOSS, ~80 MB, MLT XML scriptable) — I write XML, you scrub in GUI |
| Color grading w/ scopes | Same | Same options |

## Driving from Claude Code

All commands run as `ssh windows-desktop-wg "<command>"`. Examples:

```bash
# Inspect footage
ssh windows-desktop-wg "ffprobe -v error -show_streams -show_format \"C:/path/to/file.mp4\""

# Run a Python mask-gen + ffmpeg pipeline
ssh windows-desktop-wg "py C:/path/to/mask_script.py"

# Hardware-accelerated HEVC encode (when NVENC dim limit doesn't apply)
ssh windows-desktop-wg "ffmpeg -hwaccel cuda -i in.mp4 -c:v hevc_nvenc -b:v 50M out.mp4"
```

## Connection paths

- WireGuard direct: `10.100.0.30` (works even when poly tunnel is down)
- Reverse SSH tunnel via poly: `windows-desktop-remote` (if WireGuard down)
- Local LAN: `windows-desktop` (at Pravin's studio, same network)

## What we parked

- **DaVinci Resolve** — was going to install for GUI editing but pivoted to CLI-driven stack since the operator wanted Claude Code to drive everything. Reinstall option remains if visual-timeline work becomes worth the install overhead.
- **OBS NDI record** — encoder limit + dimension issues unresolved; can revisit if the fallback path becomes critical (Pravin's external SSD is the simpler primary fix).
