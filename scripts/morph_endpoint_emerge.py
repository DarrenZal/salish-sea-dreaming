#!/usr/bin/env python3
"""
Morph endpoint-emerge (Lane 1 v001).

Goal: keep the raw shape-morph's primitive-motion in the middle, but
in the final K frames, let the destination SVG's shapes "emerge through"
the morph so the clip ends on the actual destination piece — without
the dumb-cross-dissolve "two static images fading" feel that operator
caught earlier.

Technique (honest naming — this is NOT true shape-motion atom-snap):
  - Compute destination luma mask (where dest has non-white content)
  - In final K frames, ramp the mask strength from 0 → 1 with ease-in
  - Per pixel: out = morph_frame * (1 - mask*t) + dest_render * (mask*t)

So destination shapes appear gradually IN POSITION through the morph,
rather than the whole frame fading to a static end-image. Middle frames
are untouched, preserving primitive motion.

True shape-motion atom-snap (where remaining morph atoms physically
move to destination atom positions) is a larger build needing per-frame
shape data from the morph engine. Queued as v002+.

Outputs to NEW frame dir (never overwrites). MP4 named per
VERSIONING_DISCIPLINE.md.

INTERNAL ONLY per Austin consent floor.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np
import subprocess
import argparse
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

DEFAULT_TARGETS = [
    {
        "pair_id": "raven_sun_to_salmon_spawn",
        "frames_dir": INTERNAL / "raven_sun_to_salmon_spawn",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "fps": 24,
    },
    {
        "pair_id": "cosmic_sun_to_salmon_spawn",
        "frames_dir": INTERNAL / "cosmic_sun_to_salmon_spawn",
        "dest_svg": SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg",
        "fps": 24,
    },
]


def render_svg_to_png(svg_path: Path, out_path: Path, size: int):
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg_path), "-resize", f"{size}x{size}",
        "-gravity", "center", "-extent", f"{size}x{size}",
        str(out_path)
    ], check=True)


def luma_content_mask(img: Image.Image, dilate_px: int = 3) -> np.ndarray:
    """Return mask in [0,1] where destination has non-white content.

    Mask is soft-edged (gaussian-blurred) so emergence isn't pixel-hard.
    """
    arr = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    # Non-white = content. White = 1.0 luma, so content = 1 - luma.
    content = 1.0 - arr
    # Soft expand so edges feather in
    mask_img = Image.fromarray(np.clip(content * 255, 0, 255).astype(np.uint8))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=dilate_px))
    return np.asarray(mask_img, dtype=np.float32) / 255.0


def ease_in(t: float, power: float = 2.0) -> float:
    """Ease-in: slow start, fast finish. Higher power = more abrupt."""
    return float(np.clip(t, 0.0, 1.0)) ** power


def emerge(target: dict, emerge_frames: int, version: int, mask_strength: float):
    pair = target["pair_id"]
    frames_dir = target["frames_dir"]
    fps = target["fps"]
    if not frames_dir.exists():
        print(f"SKIP {pair}: frames dir not found at {frames_dir}")
        return

    frames = sorted(frames_dir.glob("frame_*.png"))
    n_total = len(frames)
    if n_total < emerge_frames + 5:
        print(f"SKIP {pair}: only {n_total} frames, need ≥ {emerge_frames + 5}")
        return

    # Pick canvas size from existing morph frames so dest render matches
    sample = Image.open(frames[0])
    canvas_size = sample.size[0]
    assert sample.size[0] == sample.size[1], "Expected square morph frames"

    lane = f"endpoint_emerge_v{version:03d}"
    out_frames_dir = INTERNAL / f"{pair}_{lane}"
    out_frames_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"{pair}_{lane}.mp4"

    print(f"Endpoint-emerge: {pair} ({n_total} frames, emerge over last {emerge_frames}, mask_strength={mask_strength})")
    print(f"  Render dest SVG at {canvas_size}px to match morph canvas")

    # Render dest SVG to match canvas
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        dst_png = tmpdir / "dst.png"
        render_svg_to_png(target["dest_svg"], dst_png, canvas_size)

        dst_img = Image.open(dst_png).convert("RGB")
        dst_arr = np.asarray(dst_img, dtype=np.float32)
        dst_mask = luma_content_mask(dst_img)  # [0,1], soft-edged

        for i, frame_path in enumerate(frames):
            morph_arr = np.asarray(Image.open(frame_path).convert("RGB"), dtype=np.float32)
            emerge_start = n_total - emerge_frames
            if i < emerge_start:
                out_arr = morph_arr
            else:
                local_t = (i - emerge_start) / max(1, emerge_frames - 1)
                ramp = ease_in(local_t) * mask_strength
                # Per-pixel blend strength = dst_mask * ramp (so emergence
                # happens only where dest has content; white BG areas
                # gradually clean up to white via the same blend)
                blend = (dst_mask * ramp)[..., None]  # H×W×1
                out_arr = morph_arr * (1.0 - blend) + dst_arr * blend
            out_img = Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))
            out_img.save(out_frames_dir / f"frame_{i:04d}.png")

        # Compile MP4
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", str(out_frames_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(out_mp4),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  → {out_mp4}")
            print(f"  frames preserved in {out_frames_dir}/")
        else:
            print(f"  FFMPEG ERROR: {result.stderr[-300:]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emerge-frames", type=int, default=18,
                    help="Number of final frames over which destination emerges (default 18)")
    ap.add_argument("--mask-strength", type=float, default=1.0,
                    help="Max blend strength of dest mask (0.0–1.0). Lower = morph residue stays visible at end.")
    ap.add_argument("--version", type=int, default=1,
                    help="Variant version number for output filename")
    ap.add_argument("--pair", choices=["raven", "cosmic", "both"], default="both",
                    help="Which pair to render")
    args = ap.parse_args()

    targets = DEFAULT_TARGETS
    if args.pair == "raven":
        targets = [t for t in DEFAULT_TARGETS if t["pair_id"].startswith("raven")]
    elif args.pair == "cosmic":
        targets = [t for t in DEFAULT_TARGETS if t["pair_id"].startswith("cosmic")]

    for target in targets:
        emerge(target, args.emerge_frames, args.version, args.mask_strength)
        print()


if __name__ == "__main__":
    main()
