#!/usr/bin/env python3
"""
Primitive grammar expansion v002 — 60 atoms, curl-noise drift, dual BG.

Per overnight #4: richer abstract primitive system that demonstrates
the three-shape grammar at scale with motion + flocking/current/field
behavior. NO Austin assets (zero cultural risk).

Variants rendered:
  - light BG (cream)
  - dark BG (deep ocean blue)

Each atom:
  - random position in canvas
  - one of three primitive types (circle / crescent / trigon)
  - random palette color
  - drifts via curl-noise current (atom-local)
  - morphs through full primitive cycle continuously (~3 sec period)

Output:
  primitive_field_v002_flocking_light.mp4
  primitive_field_v002_flocking_dark.mp4
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
FPS = 24
N_FRAMES = 192  # 8 sec

N_ATOMS = 60
ATOM_SIZE = 72  # bbox of each rendered atom
CYCLE_PERIOD_FRAMES = 72  # 3 sec full cycle through 3 primitives

PALETTE_LIGHT_BG = [(40, 40, 40), (180, 50, 40), (220, 160, 30),
                    (60, 80, 110), (130, 60, 100), (60, 130, 80)]
PALETTE_DARK_BG = [(230, 230, 220), (240, 180, 100), (200, 100, 80),
                   (140, 200, 220), (180, 140, 200), (180, 220, 140)]

PRIM_MORPH_DIRS = {
    ("circle", "crescent"): MORPH_OUTPUTS / "prim_circle_to_crescent",
    ("crescent", "trigon"): MORPH_OUTPUTS / "prim_crescent_to_trigon",
    ("trigon", "circle"): MORPH_OUTPUTS / "prim_trigon_to_circle",
}
PRIM_TYPES = ["circle", "crescent", "trigon"]


def load_full_cycle_frames() -> list[Image.Image]:
    """Concatenate the 3 primitive morphs into one continuous cycle (circle→crescent→trigon→circle)."""
    frames = []
    for src, dst in [("circle", "crescent"), ("crescent", "trigon"), ("trigon", "circle")]:
        d = PRIM_MORPH_DIRS[(src, dst)]
        morph_frames = sorted(d.glob("frame_*.png"))
        for f in morph_frames:
            frames.append(Image.open(f).convert("RGBA"))
    return frames


def curl_noise(x: float, y: float, t: float, scale: float = 0.005) -> tuple[float, float]:
    """Simple curl-noise approximation via sin/cos sums."""
    # Two perpendicular flow fields for curl effect
    # Use sums of sines for cheap pseudo-noise
    dx = math.sin(x * scale + t * 0.5) + 0.6 * math.cos(y * scale * 1.3 - t * 0.3)
    dy = math.cos(x * scale * 1.1 - t * 0.4) + 0.6 * math.sin(y * scale - t * 0.6)
    return (dx, dy)


def render_atom(cycle_frames: list[Image.Image], cycle_pos: float, color: tuple, size: int) -> Image.Image:
    """Sample cycle frame at fractional position, tint with color."""
    n = len(cycle_frames)
    idx = int(cycle_pos * n) % n
    frame = cycle_frames[idx].resize((size, size), Image.LANCZOS)
    arr = np.asarray(frame, dtype=np.float32)
    # Treat dark areas as the shape
    darkness = 1.0 - (arr[..., :3].mean(axis=-1) / 255.0)
    alpha = (darkness * 255).astype(np.uint8)
    rgb = np.zeros((size, size, 3), dtype=np.uint8)
    rgb[..., 0] = color[0]
    rgb[..., 1] = color[1]
    rgb[..., 2] = color[2]
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def render_variant(name: str, bg_color: tuple, palette: list, cycle_frames: list):
    out_dir = INTERNAL / f"primitive_field_v002_flocking_{name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    random.seed(7)
    # Initialize atom states
    atoms = []
    for _ in range(N_ATOMS):
        atoms.append({
            "pos": [random.uniform(50, CANVAS_W - 50), random.uniform(50, CANVAS_H - 50)],
            "color": random.choice(palette),
            "cycle_offset": random.random(),  # where in cycle this atom starts
            "size_jitter": random.uniform(0.7, 1.2),  # vary size
        })

    print(f"Rendering primitive_field v002 ({name}, {N_ATOMS} atoms, {N_FRAMES} frames)...")
    for fi in range(N_FRAMES):
        canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), bg_color)
        draw = ImageDraw.Draw(canvas)
        # Header (small, unobtrusive)
        header_color = (180, 180, 170) if name == "dark" else (140, 140, 140)
        draw.text((30, 20), f"primitive grammar field — v002 — {N_ATOMS} atoms curl-noise drift",
                  fill=header_color)

        canvas_rgba = canvas.convert("RGBA")
        t = fi / FPS  # time in seconds

        for a in atoms:
            # Update position via curl noise
            dx, dy = curl_noise(a["pos"][0], a["pos"][1], t)
            a["pos"][0] += dx * 1.5
            a["pos"][1] += dy * 1.5
            # Wrap around canvas edges
            a["pos"][0] = a["pos"][0] % CANVAS_W
            a["pos"][1] = a["pos"][1] % CANVAS_H

            # Cycle position
            cycle_pos = (a["cycle_offset"] + fi / CYCLE_PERIOD_FRAMES) % 1.0
            sz = int(ATOM_SIZE * a["size_jitter"])
            shape = render_atom(cycle_frames, cycle_pos, a["color"], sz)
            paste_x = int(a["pos"][0] - sz / 2)
            paste_y = int(a["pos"][1] - sz / 2)
            canvas_rgba.alpha_composite(shape, (paste_x, paste_y))

        canvas_rgba.convert("RGB").save(out_dir / f"frame_{fi:04d}.png")
        if (fi + 1) % 48 == 0:
            print(f"  frame {fi + 1}/{N_FRAMES}")

    out_mp4 = INTERNAL / f"primitive_field_v002_flocking_{name}.mp4"
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS),
           "-i", str(out_dir / "frame_%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           str(out_mp4)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  → {out_mp4}")
    else:
        print(f"  FFMPEG ERROR: {result.stderr[-300:]}")


def main():
    cycle = load_full_cycle_frames()
    print(f"Loaded primitive cycle: {len(cycle)} frames")
    render_variant("light", (242, 235, 222), PALETTE_LIGHT_BG, cycle)
    render_variant("dark", (16, 22, 38), PALETTE_DARK_BG, cycle)


if __name__ == "__main__":
    main()
