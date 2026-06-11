#!/usr/bin/env python3
"""
Fix morph video endpoints: cross-fade the first/last N frames with
actual SVG-direct renders of source/destination pieces so the video
starts and ends with the genuine artwork (not the morph engine's
interpretation of t=0/t=1).

Per operator feedback 2026-05-17:
  - cosmic_sun_to_salmon_spawn: end doesn't match actual Salmon piece
  - raven_sun_to_salmon_spawn: beginning has sun overlapping raven body
Both are morph-engine path-resampling + z-order artifacts.

Approach: regenerate the MP4 from the existing frame sequence, but
replace the first FADE_FRAMES with a cross-fade source_svg→morph_frame_N,
and the last FADE_FRAMES with morph_frame_(N-FADE)→dest_svg.

Run:
  python3 scripts/fix_morph_endpoints.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import subprocess
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

# Videos to fix: (frames_dir, source_svg, dest_svg, mp4_out)
TARGETS = [
    {
        "name": "cosmic_sun_to_salmon_spawn",
        "frames_dir": INTERNAL / "cosmic_sun_to_salmon_spawn",
        "source_svg": SOURCE_VECTORS / "Nature_Cosmic_Sun.svg",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "mp4_out": INTERNAL / "cosmic_sun_to_salmon_spawn.mp4",
    },
    {
        "name": "raven_sun_to_salmon_spawn",
        "frames_dir": INTERNAL / "raven_sun_to_salmon_spawn",
        "source_svg": SOURCE_VECTORS / "Animal_Bird_Raven_Sun.svg",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "mp4_out": INTERNAL / "raven_sun_to_salmon_spawn.mp4",
    },
]

FADE_FRAMES = 18  # cross-fade duration at each end (~0.75 sec at 24fps)
RENDER_SIZE = 1024  # match morph engine canvas

def render_svg_to_png(svg_path: Path, out_path: Path, size: int = RENDER_SIZE):
    """Render SVG to PNG via ImageMagick."""
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg_path), "-resize", f"{size}x{size}",
        "-gravity", "center", "-extent", f"{size}x{size}",
        str(out_path)
    ], check=True)

def lerp_image(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    """Linear interpolation between two RGB images."""
    return Image.blend(a.convert("RGB"), b.convert("RGB"), t)

def fix_target(target: dict):
    name = target["name"]
    frames_dir = target["frames_dir"]
    if not frames_dir.exists():
        print(f"SKIP {name}: frames_dir not found")
        return
    frames = sorted(frames_dir.glob("frame_*.png"))
    if len(frames) < FADE_FRAMES * 2 + 10:
        print(f"SKIP {name}: only {len(frames)} frames, need at least {FADE_FRAMES*2+10}")
        return

    print(f"Fixing {name} ({len(frames)} frames; {FADE_FRAMES}-frame cross-fades at ends)")

    # Render source + dest SVGs to PNG
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        src_png = tmpdir / "src.png"
        dst_png = tmpdir / "dst.png"
        render_svg_to_png(target["source_svg"], src_png)
        render_svg_to_png(target["dest_svg"], dst_png)

        # Match the morph frames' size
        sample = Image.open(frames[0])
        size = sample.size
        src_img = Image.open(src_png).resize(size, Image.LANCZOS).convert("RGB")
        dst_img = Image.open(dst_png).resize(size, Image.LANCZOS).convert("RGB")

        # Build output frames in a new temp dir
        out_dir = tmpdir / "frames_fixed"
        out_dir.mkdir()
        n_total = len(frames)

        for i, frame_path in enumerate(frames):
            morph_frame = Image.open(frame_path).convert("RGB")
            if i < FADE_FRAMES:
                # Cross-fade from src_svg to morph_frame_FADE
                # At i=0: 100% src_svg, 0% morph
                # At i=FADE_FRAMES: 0% src_svg, 100% morph
                # Use morph_frame_FADE as target for the fade
                target_frame = Image.open(frames[FADE_FRAMES]).convert("RGB")
                blend_t = i / FADE_FRAMES
                out = lerp_image(src_img, target_frame, blend_t)
            elif i >= n_total - FADE_FRAMES:
                # Cross-fade from morph_frame_(n-FADE) to dst_svg
                target_frame = Image.open(frames[n_total - FADE_FRAMES - 1]).convert("RGB")
                fade_idx = i - (n_total - FADE_FRAMES)
                blend_t = (fade_idx + 1) / FADE_FRAMES
                out = lerp_image(target_frame, dst_img, blend_t)
            else:
                # Middle frames unchanged
                out = morph_frame
            out.save(out_dir / f"frame_{i:04d}.png")

        # Recompile MP4
        cmd = [
            "ffmpeg", "-y", "-framerate", "24",
            "-i", str(out_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(target["mp4_out"])
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  → {target['mp4_out']} ({n_total} frames)")
        else:
            print(f"  FFMPEG ERROR: {result.stderr[-200:]}")

def main():
    print(f"Fixing morph endpoints (FADE_FRAMES={FADE_FRAMES}) for {len(TARGETS)} videos...\n")
    for target in TARGETS:
        fix_target(target)
        print()
    print("Done. Operator: re-watch videos to confirm endpoints match the actual artwork now.")

if __name__ == "__main__":
    main()
