#!/usr/bin/env python3
"""
salmon_orientation_diagnostic.

v001 line-swim came out upside-down + facing-backwards. The eye-focal-oval
atom may actually be the central spiral pivot, not the anatomical head;
my rotation logic assumed eye = front-of-head.

Render the extracted+pre-rotated salmon in all 4 orientations
(original, flip-h, flip-v, flip-both) as a 2x2 grid so operator can
pick which reads as "rightside up, head/mouth pointing right (swim
direction)."

Saves to: orientation_diagnostic.png in salmon_line_swim_v001/
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import csv
import math
import sys

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

# Reuse extraction from v1 script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salmon_line_swim_v1 import (load_atoms, load_base_jpg, extract_upper_salmon,
                                   pre_rotate_to_horizontal, BG_COLOR)

INTERNAL = Path(__file__).resolve().parent.parent / "track2-deterministic/morph_outputs_INTERNAL"


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    upper = extract_upper_salmon(atoms, base_rgb)
    salmon_h = pre_rotate_to_horizontal(upper)
    fish_rgba = salmon_h["rgba"]

    # 4 orientation variants
    orig = fish_rgba.copy()
    flip_h = cv2.flip(fish_rgba, 1)  # horizontal
    flip_v = cv2.flip(fish_rgba, 0)  # vertical
    flip_both = cv2.flip(fish_rgba, -1)  # both = 180° rotation

    h, w = fish_rgba.shape[:2]
    pad = 40
    grid_w = w * 2 + pad * 3
    grid_h = h * 2 + pad * 3 + 80  # extra for labels
    grid = Image.new("RGB", (grid_w, grid_h), BG_COLOR)
    draw = ImageDraw.Draw(grid)

    cells = [
        ("A: original (current v001)", orig, (pad, pad + 40)),
        ("B: flip-h (mirror left-right)", flip_h, (pad + w + pad, pad + 40)),
        ("C: flip-v (upside down only)", flip_v, (pad, pad + h + pad + 40)),
        ("D: flip-both = 180° rotate", flip_both, (pad + w + pad, pad + h + pad + 40)),
    ]
    for label, arr, (x, y) in cells:
        img = Image.fromarray(arr, "RGBA")
        bg_layer = Image.new("RGB", img.size, BG_COLOR)
        bg_layer.paste(img, (0, 0), img)
        grid.paste(bg_layer, (x, y))
        draw.text((x, y - 30), label, fill=(0, 0, 0))
        # Draw an arrow pointing right showing "swim direction" for reference
        ax0, ay = x + w // 2 - 60, y + h - 20
        ax1 = x + w // 2 + 60
        draw.line([(ax0, ay), (ax1, ay)], fill=(200, 0, 0), width=4)
        draw.polygon([(ax1, ay), (ax1 - 15, ay - 10), (ax1 - 15, ay + 10)], fill=(200, 0, 0))
        draw.text((x + w // 2 - 60, ay + 8), "swim direction →", fill=(150, 0, 0))

    out_dir = INTERNAL / "salmon_line_swim_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "_orientation_diagnostic.png"
    grid.save(out_path)
    print(f"→ {out_path}")
    print("\nPick which cell (A/B/C/D) shows fish RIGHTSIDE UP with FACE pointing RIGHT")
    print("(matching the red arrow direction). That's the correct base orientation.")


if __name__ == "__main__":
    main()
