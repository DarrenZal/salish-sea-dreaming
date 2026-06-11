# Design Palette — Production Tools

**Built 2026-05-25** alongside the visual-grammar palette work (primitives, fluid motion, water phrases). This doc captures the **operational tools** available for working on the palette — cropping, masking, compositing, transcoding — all CLI-driven from Claude Code via SSH to the 3090.

Related palette docs (visual grammar):
- `pravin-stable-palette-meeting-brief-2026-05-18.md`
- `primitive-grammar-contract-2026-05-19.md`
- `motion-physics-to-primitive-grammar-2026-05-20.md`
- `smooth-fluid-primitive-grammar-prototype-2026-05-20.md`

This one (operational):
- ffmpeg + Pillow + numpy + moviepy on 3090
- Driven from Claude Code via `ssh windows-desktop-wg "..."`
- Files stay on the 3090 (GPU is there, footage is there) — only commands cross the wire

## When to use what

| Creative job | Tool | Why |
|---|---|---|
| **Crop a wide projection frame down to a sub-region** | `ffmpeg crop` | One-liner, exact pixel control |
| **Split 5120×1600 projection into L/R 2560×1600 halves** | `ffmpeg filter_complex` with `split` + 2× `crop` | Useful for routing different content per projector |
| **Apply a primitive-shape mask (circle/crescent/trigon) to footage** | Pillow generates PNG with alpha → ffmpeg `overlay` | Bridges our primitive grammar work + footage |
| **Soft-edge feathered mask (gradient falloff)** | Pillow `ImageFilter.GaussianBlur` on alpha PNG → overlay | For matte-painting style transitions, edge-blending |
| **Radial vignette (focus attention to center)** | `ffmpeg vignette` filter | Built-in, fast |
| **Animated keyframed shape mask** | Pillow generates per-frame PNG sequence → ffmpeg `image2` → overlay | Rotoscoping-lite; works for geometric shapes following motion |
| **Multi-clip timeline w/ crossfades** | moviepy `concatenate_videoclips` | E.g. assembly of hero clips with smooth transitions |
| **Color tonal grading** | `ffmpeg -vf eq=brightness:contrast:saturation` | Per-clip color match |
| **Transcode to HAP for Resolume** | `ffmpeg -c:v hap -format hap out.mov` | GPU-decoded in Resolume; no Alley step needed |
| **Transcode to ProRes 422 HQ** | `ffmpeg -c:v prores_ks -profile:v 3 out.mov` | Apple-ecosystem, QuickTime-previewable |
| **Inspect a file** | `ffprobe` | Frame rate, resolution, codec, duration, bitrate |
| **Scene detection / find cut points** | `ffmpeg -vf "select='gt(scene,0.3)',showinfo"` | Find natural cut points in a long clip |

## Driving from this end (Claude Code → 3090)

```bash
# Inspect a clip
ssh windows-desktop-wg "ffprobe -v error -show_streams -show_format 'C:/path/to/file.mp4'"

# Run a Python script (e.g. Pillow mask gen + ffmpeg overlay)
ssh windows-desktop-wg "py C:/path/to/script.py"

# Hardware-accelerated HEVC encode
ssh windows-desktop-wg "ffmpeg -hwaccel cuda -i in.mp4 -c:v hevc_nvenc -b:v 50M out.mp4"
```

## What we DON'T have yet (defer until needed)

| Job | Why not now | When to add |
|---|---|---|
| **Hand-drawn rotoscope** (freehand mask around a moving subject) | Needs visual GUI | Install **Natron** (FOSS, ~250 MB, scriptable in Python) |
| **Motion-tracked masks** (mask follows a tracked feature) | Same | Natron or Blender VSE compositor |
| **Visual timeline scrubbing** (DAW-style preview) | Same | **Shotcut** (FOSS, ~80 MB, MLT XML scriptable) — I write XML, you scrub in GUI |

All three are FOSS and installable in ~5–10 min when a specific need surfaces. No reason to pre-install speculatively.

## Connection paths to 3090

- **WireGuard direct:** `10.100.0.30` (works even when poly tunnel is down)
- **Reverse SSH via poly:** `windows-desktop-remote` (fallback)
- **Local LAN:** `windows-desktop` (at Pravin's studio)

## Reference

Full capability matrix + technical install state lives at `3090-video-editing-toolchain-2026-05-25.md`.
