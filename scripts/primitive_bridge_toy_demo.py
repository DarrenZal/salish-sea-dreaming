#!/usr/bin/env python3
"""
Abstract primitive-bridge toy demo.

12 clean primitives on the left → 12 clean primitives on the right.
All atoms move, with Circle/Crescent/Trigon bridge vocabulary for
cross-type transitions. No Austin artwork in background.

Purpose: communicate the primitive-bridge GRAMMAR visually without
claiming Austin correspondences. Lane 2E v001+v002 failed to read as
the grammar because too few atoms moved while Austin pieces were
faded behind. This toy strips both confusions away.

Output: lane_2e_abstract_primitive_grammar_toy.mp4
"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import math
import subprocess
import random

ROOT = Path(__file__).resolve().parent.parent
MORPH_OUTPUTS = ROOT / "track2-deterministic/morph_outputs"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS_W = 1920
CANVAS_H = 1080
BG_COLOR = (242, 235, 222)
FPS = 24
N_FRAMES = 96  # 4 sec

# Austin-inspired primitive palette (cream BG, dark + warm + accent)
PALETTE = [(40, 40, 40), (180, 50, 40), (220, 160, 30), (60, 80, 110),
           (130, 60, 100), (60, 130, 80), (200, 100, 60), (90, 60, 40)]

# Grid: 12 slots arranged 4 wide × 3 tall on each side
COLS, ROWS = 4, 3
N_PAIRS = COLS * ROWS  # 12

LEFT_CENTER_X = CANVAS_W // 4
RIGHT_CENTER_X = 3 * CANVAS_W // 4
TOP_MARGIN = 160
BOTTOM_MARGIN = 100
CELL_W = (CANVAS_W // 4 - 100) // COLS
CELL_H = (CANVAS_H - TOP_MARGIN - BOTTOM_MARGIN) // ROWS
ATOM_SIZE = min(CELL_W, CELL_H) - 20

# Use Austin-inspired primitive_morph dirs as the shape bridge data
PRIM_MORPH_DIRS = {
    ("circle", "crescent"): MORPH_OUTPUTS / "prim_circle_to_crescent",
    ("crescent", "trigon"): MORPH_OUTPUTS / "prim_crescent_to_trigon",
    ("trigon", "circle"): MORPH_OUTPUTS / "prim_trigon_to_circle",
}

PRIM_TYPES = ["circle", "crescent", "trigon"]


def grid_position(col: int, row: int, center_x: int) -> tuple:
    x0 = center_x - (CELL_W * COLS) // 2
    y0 = TOP_MARGIN
    return (x0 + col * CELL_W + CELL_W // 2,
            y0 + row * CELL_H + CELL_H // 2)


def render_primitive(prim: str, color: tuple, size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 10
    if prim == "circle":
        d.ellipse([pad, pad, size - pad, size - pad], fill=color + (255,))
    elif prim == "crescent":
        d.ellipse([pad, pad, size - pad, size - pad], fill=color + (255,))
        d.ellipse([pad + size // 3, pad, size - pad + size // 3, size - pad],
                  fill=(BG_COLOR[0], BG_COLOR[1], BG_COLOR[2], 255))
    elif prim == "trigon":
        # Triangle pointing right with slight curve feel
        d.polygon([(pad, pad), (size - pad, size // 2), (pad, size - pad)],
                  fill=color + (255,))
    return img


def load_prim_morph(src: str, dst: str) -> tuple:
    """Return (frames list, reversed_flag) for src→dst transition."""
    if src == dst:
        return None, False
    if (src, dst) in PRIM_MORPH_DIRS:
        d = PRIM_MORPH_DIRS[(src, dst)]
        return [Image.open(f).convert("RGBA") for f in sorted(d.glob("frame_*.png"))], False
    if (dst, src) in PRIM_MORPH_DIRS:
        d = PRIM_MORPH_DIRS[(dst, src)]
        return list(reversed([Image.open(f).convert("RGBA") for f in sorted(d.glob("frame_*.png"))])), True
    return None, False


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def main():
    random.seed(7)
    # Build 12 atom pairs — mix of same-type and cross-type transitions
    # Distribute types: 4 of each (circle/crescent/trigon) at start; shuffled at end
    src_types = ["circle"] * 4 + ["crescent"] * 4 + ["trigon"] * 4
    dst_types = src_types.copy()
    random.shuffle(dst_types)
    # Color: random from palette
    src_colors = [random.choice(PALETTE) for _ in range(N_PAIRS)]
    dst_colors = [random.choice(PALETTE) for _ in range(N_PAIRS)]
    # Grid positions
    src_positions = []
    dst_positions = []
    # Match src grid order to dst grid order so they translate L→R cleanly
    # (but in same row/col so movement is mostly horizontal)
    for row in range(ROWS):
        for col in range(COLS):
            src_positions.append(grid_position(col, row, LEFT_CENTER_X))
            dst_positions.append(grid_position(col, row, RIGHT_CENTER_X))

    pairs = []
    for i in range(N_PAIRS):
        frames, reversed_flag = load_prim_morph(src_types[i], dst_types[i])
        pairs.append({
            "src_type": src_types[i],
            "dst_type": dst_types[i],
            "src_color": src_colors[i],
            "dst_color": dst_colors[i],
            "src_pos": src_positions[i],
            "dst_pos": dst_positions[i],
            "morph_frames": frames,
        })

    # Count transition types
    same_type = sum(1 for p in pairs if p["src_type"] == p["dst_type"])
    print(f"Pairs: {N_PAIRS} total, {same_type} same-type, {N_PAIRS - same_type} cross-type")
    for p in pairs:
        kind = "same" if p["src_type"] == p["dst_type"] else "bridge"
        print(f"  {p['src_type']} → {p['dst_type']} ({kind})")

    out_dir = INTERNAL / "lane_2e_abstract_primitive_grammar_toy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "lane_2e_abstract_primitive_grammar_toy.mp4"

    # Animation phases
    HOLD_SRC_END = 10
    HOLD_DST_START = 80

    print(f"Rendering {N_FRAMES} frames {CANVAS_W}×{CANVAS_H}...")
    for i in range(N_FRAMES):
        canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
        draw = ImageDraw.Draw(canvas)
        # Header
        draw.text((40, 30), "Abstract primitive-bridge grammar toy",
                  fill=(40, 40, 40))
        draw.text((40, 55), "12 clean primitives left → 12 right. Same-type translates;"
                            " cross-type uses Circle↔Crescent↔Trigon bridge.",
                  fill=(80, 80, 80))
        draw.text((40, 80), "(Not Austin-derived. Demonstrates the grammar without claiming correspondences.)",
                  fill=(140, 80, 80))
        # Column labels
        draw.text((LEFT_CENTER_X - 50, TOP_MARGIN - 35), "SOURCE", fill=(60, 60, 60))
        draw.text((RIGHT_CENTER_X - 50, TOP_MARGIN - 35), "DESTINATION", fill=(60, 60, 60))

        canvas_rgba = canvas.convert("RGBA")

        # Animation progress
        if i < HOLD_SRC_END:
            pair_t = 0.0
        elif i < HOLD_DST_START:
            pair_t = (i - HOLD_SRC_END) / (HOLD_DST_START - HOLD_SRC_END)
        else:
            pair_t = 1.0
        pair_t_eased = pair_t * pair_t * (3 - 2 * pair_t)

        # Render each pair
        for p in pairs:
            # Position
            px = p["src_pos"][0] + pair_t_eased * (p["dst_pos"][0] - p["src_pos"][0])
            py = p["src_pos"][1] + pair_t_eased * (p["dst_pos"][1] - p["src_pos"][1])
            # Color
            color = lerp_color(p["src_color"], p["dst_color"], pair_t_eased)
            # Shape
            if p["morph_frames"] is None:
                # Same-type — render src primitive at current position (could scale if needed)
                shape = render_primitive(p["src_type"], color, ATOM_SIZE)
            else:
                n_morph = len(p["morph_frames"])
                idx = int(round(pair_t_eased * (n_morph - 1)))
                idx = max(0, min(n_morph - 1, idx))
                morph_frame = p["morph_frames"][idx].resize((ATOM_SIZE, ATOM_SIZE), Image.LANCZOS)
                # Treat dark areas as the shape mask
                arr = np.asarray(morph_frame, dtype=np.float32)
                darkness = 1.0 - (arr[..., :3].mean(axis=-1) / 255.0)
                alpha = (darkness * 255).astype(np.uint8)
                rgb = np.zeros((ATOM_SIZE, ATOM_SIZE, 3), dtype=np.uint8)
                rgb[..., 0] = color[0]
                rgb[..., 1] = color[1]
                rgb[..., 2] = color[2]
                shape = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")

            sw, sh = shape.size
            canvas_rgba.alpha_composite(shape, (int(px - sw / 2), int(py - sh / 2)))

        canvas_rgba.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
        if (i + 1) % 24 == 0:
            print(f"  frame {i + 1}/{N_FRAMES}")

    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(out_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"→ {out_mp4}")
    else:
        print(f"FFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
