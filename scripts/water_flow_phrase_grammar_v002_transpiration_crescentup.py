#!/usr/bin/env python3
"""
Render the transpiration scene with crescents flipped to cup FORWARD (toward
the trigon terminus / direction of travel). The default v002 crescent cups
BACK toward the origin; on the rising transpiration phrase that reads as
crescents catching vapor from below (umbrella-pointing-down). This variant
flips them to point skyward — phrase "opening up" as it rises.

Touches Austin's open Q1 from v002 ("does crescent orientation depend on
direction of flow?"). Internal A/B only; not Austin-approved.

Outputs to the same dir as the addon:
    track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v002b_2026-05-22/
      ├── transpiration_vertical_phrase_v002_crescentup.mp4
      └── transpiration_vertical_phrase_v002_crescentup.mov

Usage:
    python3 scripts/water_flow_phrase_grammar_v002_transpiration_crescentup.py
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

_here = Path(__file__).parent
sys.path.insert(0, str(_here))
import water_flow_phrase_grammar_v002 as v002
import water_flow_phrase_grammar_v002_alpha_and_inverse as addon


def render_phrase_on_path_crescent_up(canvas, path_fn, tan_fn, u_head, q, gap, scale=1.0):
    """Mirror of v002.render_phrase_on_path; the ONLY change is the crescent's
    open_angle goes from `ang + pi` (cup backward / toward origin) to `ang`
    (cup forward / toward terminus / sky in the transpiration case)."""
    win = float(v002.window(q, 0.09))
    layout = (
        (0, "trigon",   v002.COL_TRIGON, v002.R_TRIGON, v002.I_TRIGON),
        (1, "crescent", v002.COL_CRESC,  v002.R_CRESC,  v002.I_CRESC),
        (2, "crescent", v002.COL_CRESC,  v002.R_CRESC,  v002.I_CRESC),
        (3, "circle",   v002.COL_CIRCLE, v002.R_CIRCLE, v002.I_CIRCLE),
    )
    for rank, kind, col, size, inten in layout:
        u = u_head - rank * gap
        if u < 0.0 or u > 1.0:
            continue
        x, y = path_fn(u)
        tx, ty = tan_fn(u)
        ang = math.atan2(ty, tx)
        fade = float(v002.smoothstep(0.0, 0.09, u) * v002.smoothstep(1.0, 0.91, u)) * win
        if fade <= 0.003:
            continue
        # motion-trail wake (unchanged from v002)
        wake_r = size * scale * 0.42
        for j in range(1, v002.TRAIL_N + 1):
            ut = u - j * v002.TRAIL_GAP
            if ut < 0.0:
                break
            bx, by = path_fn(ut)
            bfade = fade * 0.45 * (v002.TRAIL_FALL ** j) * float(v002.smoothstep(0.0, 0.06, ut))
            v002.draw_blob(canvas, bx, by, wake_r * (1.0 - 0.13 * j), col, inten * bfade)
        if kind == "circle":
            v002.draw_circle(canvas, x, y, size * scale, col, inten * fade)
        elif kind == "crescent":
            # FLIPPED — open_angle = ang (forward) instead of ang + pi (backward)
            v002.draw_crescent(canvas, x, y, size * scale, ang, col, inten * fade)
        else:
            v002.draw_trigon(canvas, x, y, size * scale, ang, col, inten * fade)


def frame_transpiration_crescentup(canvas, f, n):
    gap = 0.150
    span = 1.0 + 6.0 * gap
    bases = (0.00, 0.17, 0.34)
    for lane, base in zip(v002.WF_LANES, bases):
        pf = lambda t, ln=lane: addon.transp_path(t, ln)
        tf = lambda t, ln=lane: addon.transp_tan(t, ln)
        for off in (base, base + 0.5):
            q = (f / n + off) % 1.0
            u_head = -3.0 * gap + (q ** 1.8) * span
            render_phrase_on_path_crescent_up(canvas, pf, tf, u_head, q, gap)


def main():
    outdir = (Path(__file__).resolve().parent.parent
              / "track2-deterministic" / "morph_outputs_INTERNAL"
              / "water_flow_phrase_grammar_v002b_2026-05-22")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "midpoint_stills").mkdir(exist_ok=True)

    scene_name = "transpiration_vertical_phrase_v002_crescentup"
    guide = addon.build_guide_transpiration()

    print(f"== transpiration crescent-up A/B variant ==")
    print(f"  outdir: {outdir}")
    addon.render_scene_dual(scene_name, frame_transpiration_crescentup, guide,
                            outdir, v002.N_FRAMES)


if __name__ == "__main__":
    main()
