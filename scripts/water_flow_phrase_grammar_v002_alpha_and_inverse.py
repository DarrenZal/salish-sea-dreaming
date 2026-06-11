#!/usr/bin/env python3
"""
Add-on to water_flow_phrase_grammar_v002.py — two Pravin asks from 2026-05-21:

1. ALPHA-CHANNEL VERSIONS of the water-flow grammar clips. Same phrase grammar
   (circle → crescent → crescent → trigon), same scenes, but each frame is also
   encoded as ProRes 4444 RGBA. Alpha = max(R, G, B) of the additive RGB on
   black, so the same content reads correctly with either Screen/Additive
   blend (RGB MP4) OR Over blend (RGBA MOV) in Resolume.

2. INVERTED WATERFALL ("transpiration_vertical_phrase_v002") — new scene.
   Phrase bundles rise from earth (bottom of frame) to stars (top of frame),
   under the same gravitational-ease curve (q**1.8) so they accelerate while
   leaving the surface and slow as they reach the top, like vapor diffusing.
   Lane geometry, sway, ease, and phrase grammar are identical to the
   downward waterfall — only the y direction is flipped. Crescent orientation
   is unchanged from v002 (cups back toward origin); orientation-as-direction
   remains an Austin Q1 open question.

Outputs (6 files):
    track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v002b_2026-05-22/
      ├── current_streamline_field_v002.mp4              (H.264 RGB on black)
      ├── current_streamline_field_v002.mov              (ProRes 4444 RGBA)
      ├── waterfall_vertical_phrase_v002.mp4
      ├── waterfall_vertical_phrase_v002.mov
      ├── transpiration_vertical_phrase_v002.mp4
      └── transpiration_vertical_phrase_v002.mov

The RGB MP4s are bit-identical to what v002 produced (same renderer code path)
except for the transpiration scene which v002 didn't have.

INTERNAL ONLY. Not Austin-approved.

Usage:
    python3 scripts/water_flow_phrase_grammar_v002_alpha_and_inverse.py
    python3 scripts/water_flow_phrase_grammar_v002_alpha_and_inverse.py --frames 12  # smoke
"""

import argparse
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

# Reuse the v002 machinery wholesale — it's well-tested and we don't want to
# drift from the canonical Austin-pending grammar.
_v002_path = Path(__file__).parent / "water_flow_phrase_grammar_v002.py"
sys.path.insert(0, str(_v002_path.parent))
import water_flow_phrase_grammar_v002 as v002


# --------------------------------------------------------------------------
# new scene: transpiration_vertical_phrase_v002 (inverted waterfall)
# --------------------------------------------------------------------------

def transp_path(t, lane):
    """y maps t=0 → BOTTOM (earth), t=1 → TOP (stars). Lane sway and phase
    inherited unchanged from v002's WF_LANES so each lane reads as the same
    column with its motion direction simply reversed."""
    y = (v002.H - v002.WF_MY) - t * (v002.H - 2.0 * v002.WF_MY)
    x = lane["x"] + lane["sway"] * math.sin(math.pi * 1.3 * t + lane["ph"])
    return x, y


def transp_tan(t, lane):
    """Tangent: dy is negative (upward). Sway derivative is the same as
    waterfall's since sway is x(t), not direction-dependent."""
    dy = -(v002.H - 2.0 * v002.WF_MY)
    dx = lane["sway"] * math.pi * 1.3 * math.cos(math.pi * 1.3 * t + lane["ph"])
    el = math.hypot(dx, dy)
    return dx / el, dy / el


def frame_transpiration(canvas, f, n):
    """Mirrors v002.frame_waterfall structure with transp_path/transp_tan.
    Same gap, span, lane bases — only the path direction is reversed."""
    gap = 0.150
    span = 1.0 + 6.0 * gap
    bases = (0.00, 0.17, 0.34)
    for lane, base in zip(v002.WF_LANES, bases):
        pf = lambda t, ln=lane: transp_path(t, ln)
        tf = lambda t, ln=lane: transp_tan(t, ln)
        for off in (base, base + 0.5):
            q = (f / n + off) % 1.0
            u_head = -3.0 * gap + (q ** 1.8) * span
            v002.render_phrase_on_path(canvas, pf, tf, u_head, q, gap)


def build_guide_transpiration():
    """Faint upward-flowing ribbon guides — same as v002 waterfall guide
    but along the inverted path. Density and width inherited."""
    layer = np.zeros((v002.H, v002.W), np.float32)
    for lane in v002.WF_LANES:
        v002._stamp_ribbon(
            layer, lambda t, ln=lane: transp_path(t, ln), 320, 31.0, 0.078,
        )
    return layer


# --------------------------------------------------------------------------
# encoders
# --------------------------------------------------------------------------

def _encoder_rgb_mp4(out_path):
    """H.264 RGB on black — same as v002._encoder."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", f"{v002.W}x{v002.H}", "-framerate", str(v002.FPS),
        "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def _encoder_rgba_prores(out_path):
    """ProRes 4444 RGBA. Universal codec for compositing; Resolume reads it
    fine, FCP/Premiere/Resolve all read it. Larger files than HAP Alpha but
    no quality loss and one less transcode for the artist."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgba",
        "-video_size", f"{v002.W}x{v002.H}", "-framerate", str(v002.FPS),
        "-i", "pipe:0",
        "-c:v", "prores_ks", "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le",
        str(out_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

# (scene_name, frame_fn, guide_array)
def _scene_specs():
    return [
        ("current_streamline_field_v002",
         v002.frame_current,
         v002.build_guide("current_streamline_field_v002")),
        ("waterfall_vertical_phrase_v002",
         v002.frame_waterfall,
         v002.build_guide("waterfall_vertical_phrase_v002")),
        ("transpiration_vertical_phrase_v002",
         frame_transpiration,
         build_guide_transpiration()),
    ]


def render_scene_dual(scene_name, frame_fn, guide, outdir, n_frames):
    """Render one scene as both RGB H.264 MP4 and RGBA ProRes 4444 MOV in one
    pass. Each rendered frame is tonemapped once; the same uint8 RGB drives
    both encoders, with alpha = max channel for the RGBA stream."""
    rgb_path = outdir / f"{scene_name}.mp4"
    rgba_path = outdir / f"{scene_name}.mov"
    midpoint_idx = n_frames // 2

    proc_rgb = _encoder_rgb_mp4(rgb_path)
    proc_rgba = _encoder_rgba_prores(rgba_path)
    mid_frame = None
    t0 = time.time()

    try:
        for f in range(n_frames):
            canvas = np.zeros((v002.H, v002.W, 3), np.float32)
            shimmer = 0.80 + 0.20 * math.sin(2.0 * math.pi * f / n_frames)
            canvas += guide[:, :, None] * (
                v002.COL_GUIDE[None, None, :] * np.float32(shimmer)
            )
            frame_fn(canvas, f, n_frames)
            rgb = v002.tonemap(canvas)  # (H,W,3) uint8
            alpha = rgb.max(axis=2, keepdims=True).astype(np.uint8)  # (H,W,1)
            rgba = np.concatenate([rgb, alpha], axis=2)  # (H,W,4)

            if f == midpoint_idx:
                mid_frame = rgb.copy()

            proc_rgb.stdin.write(rgb.tobytes())
            proc_rgba.stdin.write(rgba.tobytes())
    finally:
        for proc, name in ((proc_rgb, "rgb-mp4"), (proc_rgba, "rgba-mov")):
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.wait()
            if proc.returncode != 0:
                err = proc.stderr.read().decode("utf-8", "replace")
                raise RuntimeError(f"ffmpeg {name} failed for {scene_name}:\n{err}")

    if mid_frame is not None:
        Image.fromarray(mid_frame).save(
            outdir / "midpoint_stills" / f"{scene_name}_mid.png"
        )
    elapsed = time.time() - t0
    print(f"  {scene_name}: {n_frames} frames → mp4 + mov in {elapsed:4.1f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--frames", type=int, default=v002.N_FRAMES,
                        help=f"frames per scene (default {v002.N_FRAMES} = 6s @ 24fps)")
    parser.add_argument("--outdir", default=None,
                        help="override default output dir")
    args = parser.parse_args()

    outdir = Path(args.outdir) if args.outdir else (
        Path(__file__).resolve().parent.parent
        / "track2-deterministic" / "morph_outputs_INTERNAL"
        / "water_flow_phrase_grammar_v002b_2026-05-22"
    )
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "midpoint_stills").mkdir(exist_ok=True)

    print(f"== water-flow v002 alpha + transpiration ==")
    print(f"  outdir: {outdir}")
    print(f"  frames: {args.frames} ({args.frames / v002.FPS:.2f}s at {v002.FPS}fps)")
    print()

    t0 = time.time()
    for scene_name, frame_fn, guide in _scene_specs():
        render_scene_dual(scene_name, frame_fn, guide, outdir, args.frames)
    print(f"\ntotal: {time.time() - t0:.1f}s")
    print(f"\noutputs in {outdir}")


if __name__ == "__main__":
    main()
