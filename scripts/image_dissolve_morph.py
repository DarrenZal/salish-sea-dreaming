#!/usr/bin/env python3
"""
Image cross-dissolve as honest replacement for broken cross-scale morphs.

The track2 morph engine works well for SAME-VIEWBOX pairs (Exp 2
raven_sun↔cosmic_sun, both 108×108). It falls apart for CROSS-SCALE
pairs (cosmic_sun 108×108 ↔ salmon_spawn 1500×1500) because path
resampling can't reconcile wildly different shape counts and produces
wrong z-order + lost detail at endpoints.

Operator feedback 2026-05-17 PM: my SVG cross-fade "bandaid" made the
issue more visible, not less. Honest fix: don't pretend to do a shape
morph; do an image cross-dissolve between the two SVG renders.

For Pravin 4pm: this gives clean videos where both endpoints are
exactly the real artworks and the middle is a smooth fade. We frame it
as "for cross-scale pairs, image dissolve is the right tool, not the
morph engine."

INTERNAL ONLY per Austin consent floor.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

TARGETS = [
    {
        "name": "cosmic_sun_to_salmon_spawn",
        "source_svg": SOURCE_VECTORS / "Nature_Cosmic_Sun.svg",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "mp4_out": INTERNAL / "cosmic_sun_to_salmon_spawn.mp4",
        "duration_sec": 5,
        "fps": 24,
    },
    {
        "name": "raven_sun_to_salmon_spawn",
        "source_svg": SOURCE_VECTORS / "Animal_Bird_Raven_Sun.svg",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "mp4_out": INTERNAL / "raven_sun_to_salmon_spawn.mp4",
        "duration_sec": 5,
        "fps": 24,
    },
]

RENDER_SIZE = 1024
# Ease-in-out: spend more time at endpoints (showing each piece clearly),
# transition faster in the middle. Smoother visual rhythm than linear.
def ease_t(t: float) -> float:
    # Smoothstep: 3t² - 2t³ — gentle acceleration at start, deceleration at end
    return t * t * (3 - 2 * t)

def render_svg_to_png(svg_path: Path, out_path: Path, size: int = RENDER_SIZE):
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg_path), "-resize", f"{size}x{size}",
        "-gravity", "center", "-extent", f"{size}x{size}",
        str(out_path)
    ], check=True)

def dissolve(target: dict):
    name = target["name"]
    fps = target["fps"]
    n_frames = target["duration_sec"] * fps

    print(f"Image dissolve: {name} ({n_frames} frames @ {fps}fps)")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        src_png = tmpdir / "src.png"
        dst_png = tmpdir / "dst.png"
        render_svg_to_png(target["source_svg"], src_png)
        render_svg_to_png(target["dest_svg"], dst_png)

        src_img = Image.open(src_png).convert("RGB")
        dst_img = Image.open(dst_png).convert("RGB")

        # Generate dissolve frames
        out_dir = tmpdir / "frames"
        out_dir.mkdir()
        # Hold first ~10% on source, transition middle ~80%, hold last ~10% on dest
        hold_frames = int(n_frames * 0.10)
        transition_frames = n_frames - 2 * hold_frames
        for i in range(n_frames):
            if i < hold_frames:
                blend = 0.0
            elif i >= n_frames - hold_frames:
                blend = 1.0
            else:
                # Linear within transition window, then eased
                linear_t = (i - hold_frames) / (transition_frames - 1) if transition_frames > 1 else 0
                blend = ease_t(linear_t)
            out = Image.blend(src_img, dst_img, blend)
            out.save(out_dir / f"frame_{i:04d}.png")

        # Compile MP4
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(out_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(target["mp4_out"])
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  → {target['mp4_out']}")
        else:
            print(f"  ERROR: {result.stderr[-200:]}")

def main():
    for target in TARGETS:
        dissolve(target)
        print()
    print("Done. These cross-scale pairs now use image dissolve (honest)")
    print("instead of broken shape morph. Same-viewBox pairs (like Exp 2")
    print("raven_sun↔cosmic_sun) still use the morph engine.")

if __name__ == "__main__":
    main()
