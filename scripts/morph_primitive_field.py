#!/usr/bin/env python3
"""
Lane 3A v001 — Primitive field morph.

Demonstrates Coast Salish primitives (Circle/Crescent/Trigon) at
compositional scale: a grid field where each cell instances the
3-primitive cycle at a different phase. Waves of morphing sweep across
the field.

Low cultural load (abstract primitives, not specific Austin pieces) —
shareable internally without per-output Austin friction. Demonstrates
the primitives are a *grammar*, not specific shapes.

INTERNAL ONLY per Austin consent floor for any output that touches
his work. This particular variant uses ONLY the abstract primitive
references (`source-vectors/primitives/`), not Austin-specific
decompositions, so cultural load is low.

Output: track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import numpy as np
import subprocess
import math

ROOT = Path(__file__).resolve().parent.parent
MORPH_OUTPUTS = ROOT / "track2-deterministic/morph_outputs"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

# Each primitive morph dir
PRIM_DIRS = [
    MORPH_OUTPUTS / "prim_circle_to_crescent",
    MORPH_OUTPUTS / "prim_crescent_to_trigon",
    MORPH_OUTPUTS / "prim_trigon_to_circle",
]

# Output config
CANVAS_W = 1920
CANVAS_H = 1080
GRID_COLS = 8
GRID_ROWS = 5  # 8x5 = 40 instances
FPS = 24
N_FRAMES = 144  # 6 sec — enough for at least one wave sweep
INSTANCE_SCALE = 0.12  # each instance is ~12% of canvas height
PHASE_AXIS = "diagonal"  # "horizontal", "vertical", "diagonal", "radial"

BG_COLOR = (245, 245, 240, 255)  # warm off-white (slightly Austin-ish ink-on-paper feel)


def load_cycle_frames() -> list[Image.Image]:
    """Concatenate the 3 primitive morphs into one continuous cycle."""
    frames = []
    for d in PRIM_DIRS:
        if not d.exists():
            raise SystemExit(f"Missing morph dir: {d}")
        for f in sorted(d.glob("frame_*.png")):
            frames.append(Image.open(f).convert("RGB"))
    return frames


def phase_for_cell(gx: int, gy: int, n_cycle: int) -> int:
    """Return frame-offset for a grid cell so morphing sweeps across the field.

    Different PHASE_AXIS modes give different visual feels.
    """
    if PHASE_AXIS == "horizontal":
        norm = gx / max(1, GRID_COLS - 1)
    elif PHASE_AXIS == "vertical":
        norm = gy / max(1, GRID_ROWS - 1)
    elif PHASE_AXIS == "diagonal":
        norm = (gx + gy) / max(1, (GRID_COLS - 1) + (GRID_ROWS - 1))
    elif PHASE_AXIS == "radial":
        cx, cy = (GRID_COLS - 1) / 2, (GRID_ROWS - 1) / 2
        d = math.hypot(gx - cx, gy - cy)
        max_d = math.hypot(cx, cy)
        norm = d / max(0.001, max_d)
    else:
        norm = 0.0
    return int(norm * n_cycle)


def main():
    INTERNAL.mkdir(parents=True, exist_ok=True)
    out_dir = INTERNAL / "primitive_field_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "primitive_field_v001.mp4"

    cycle = load_cycle_frames()
    n_cycle = len(cycle)
    print(f"Loaded cycle: {n_cycle} frames from {len(PRIM_DIRS)} morph dirs")

    instance_size = int(CANVAS_H * INSTANCE_SCALE)
    # Cell spacing: evenly distribute instances across canvas
    cell_w = CANVAS_W // GRID_COLS
    cell_h = CANVAS_H // GRID_ROWS
    print(f"Grid: {GRID_COLS}x{GRID_ROWS} = {GRID_COLS * GRID_ROWS} instances at {instance_size}px each, phase={PHASE_AXIS}")
    print(f"Cell size: {cell_w}x{cell_h}, canvas {CANVAS_W}x{CANVAS_H}")

    # Pre-resize cycle frames once to save time
    print("Pre-resizing cycle frames...")
    cycle_small = [f.resize((instance_size, instance_size), Image.LANCZOS) for f in cycle]

    # Compute per-cell phase once
    phases = [[phase_for_cell(gx, gy, n_cycle) for gx in range(GRID_COLS)]
              for gy in range(GRID_ROWS)]

    print(f"Rendering {N_FRAMES} frames...")
    for i in range(N_FRAMES):
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
        for gy in range(GRID_ROWS):
            for gx in range(GRID_COLS):
                # Each cell advances through cycle at same rate but with phase offset
                # Speed: 1.5 cycle frames per output frame for snappier motion
                frame_idx = (int(i * 1.5) + phases[gy][gx]) % n_cycle
                inst = cycle_small[frame_idx]
                # Center of cell
                cx = gx * cell_w + cell_w // 2
                cy = gy * cell_h + cell_h // 2
                paste_x = cx - instance_size // 2
                paste_y = cy - instance_size // 2
                canvas.paste(inst, (paste_x, paste_y))
        canvas.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
        if (i + 1) % 24 == 0:
            print(f"  frame {i + 1}/{N_FRAMES}")

    # Compile MP4
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(out_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n→ {out_mp4}")
        print(f"  frames preserved in {out_dir}/")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
