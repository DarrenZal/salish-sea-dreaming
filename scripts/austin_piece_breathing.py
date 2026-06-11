#!/usr/bin/env python3
"""
Lane #1 (peer-ranked) — Austin Piece Breathing v001.

Animate one of Austin's pieces by per-atom subtle motion in place:
breath-like radial drift, gentle scale pulse, small rotation. No
cross-piece morph. Tests whether the atom decomposition can carry
"the piece comes alive" cleanly, before committing to Lane 2E
atom-primitive-bridge.

Pipeline:
  1. Load atom_metadata.csv for one piece (default Nature_Cosmic_Sun)
  2. Render every atom from its isolated PNG at canvas-correct
     position + scale (using bbox + viewBox + canvas mapping)
  3. Background-field + negative-space atoms stay static (anchor)
  4. Foreground atoms (trigon, sun-ray, crescent, circle-oval, etc.)
     get per-frame motion driven by per-atom phase-offset sines:
       - radial drift (subtle outward / inward from piece centroid)
       - scale pulse
       - rotation around atom center
  5. Composite per frame, save MP4

INTERNAL ONLY. Per Austin consent floor: any internal/team review of
breathing output for an Austin-specific piece needs his per-output OK
before sponsor/show-staged surfaces. Per peer wording 2026-05-17 PM:
describe this as "structurally closer to the primitive grammar we can
observe in the pieces" — not as "culturally honest." Cultural meaning
is Austin's call.

Output: track2-deterministic/morph_outputs_INTERNAL/austin_piece_breathing_<piece>_v001.mp4
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import numpy as np
import csv
import math
import subprocess
import argparse

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

# Mapping from piece name to its source viewBox size (square assumed)
PIECE_VIEWBOX = {
    "Nature_Cosmic_Sun": 108,
    "Animal_Bird_Raven_Sun": 108,
    "Animal_Wolf_Spindle_Whorl": 1500,
    "Animal_Salmon_Spawn_Eggs": 1500,
    "Supernatural_Human_TheCreator_Background": 1500,
}

# Atoms that DO NOT animate (static base layer)
STATIC_LABELS = {"background-field", "negative-space", "background"}

CANVAS = 1024
FPS = 24
N_FRAMES = 144  # 6 seconds — one slow full breath

# Breathing motion parameters (tuned to be SUBTLE — peer-style noted that
# heavy motion will read as kinetic chaos, not breathing)
DRIFT_AMPLITUDE = 0.012  # 1.2% of canvas — barely visible but registers
SCALE_PULSE = 0.025      # ±2.5% scale
ROTATE_AMPLITUDE = 1.5   # ±1.5 degrees


def load_atoms(piece: str) -> list[dict]:
    csv_path = DECOMPOSED / piece / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "bbox": (float(row["bbox_x"]), float(row["bbox_y"]),
                             float(row["bbox_w"]), float(row["bbox_h"])),
                    "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                    "isolated_png": DECOMPOSED / piece / row["isolated_png"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def compose_static(atoms: list[dict], viewbox: int) -> Image.Image:
    """Render the full piece as a static composite of all atoms (no motion).

    This is the anchor base. Animated atoms will be re-drawn on top with
    transformations, so we use this only as a fallback if a non-animated
    layer is needed. Currently unused but kept for diagnostic compares.
    """
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
    scale = CANVAS / viewbox
    for a in atoms:
        bbox = a["bbox"]
        if bbox[2] <= 0 or bbox[3] <= 0:
            continue
        img = Image.open(a["isolated_png"]).convert("RGBA")
        target_w = max(1, int(round(bbox[2] * scale)))
        target_h = max(1, int(round(bbox[3] * scale)))
        img = img.resize((target_w, target_h), Image.LANCZOS)
        x = int(round(bbox[0] * scale))
        y = int(round(bbox[1] * scale))
        canvas.alpha_composite(img, (x, y))
    return canvas


def transform_atom(img: Image.Image, scale_mult: float, rotate_deg: float) -> Image.Image:
    """Scale + rotate an atom sprite around its own center.

    Returns a (potentially larger) image with transparent padding so
    rotation doesn't clip. Caller must adjust paste position accordingly
    (use returned size to recompute top-left).
    """
    if abs(scale_mult - 1.0) > 0.001:
        w, h = img.size
        new_w = max(1, int(round(w * scale_mult)))
        new_h = max(1, int(round(h * scale_mult)))
        img = img.resize((new_w, new_h), Image.LANCZOS)
    if abs(rotate_deg) > 0.05:
        img = img.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    return img


def paste_centered(canvas: Image.Image, sprite: Image.Image, center_x: int, center_y: int):
    """Paste sprite onto canvas centered at (center_x, center_y)."""
    sw, sh = sprite.size
    x = center_x - sw // 2
    y = center_y - sh // 2
    canvas.alpha_composite(sprite, (x, y))


def render_frame(atoms_static: list[dict], atoms_breath: list[dict], i: int,
                 viewbox: int, breath_phase: float) -> Image.Image:
    """Render one frame: static atoms first, then breathing atoms with motion."""
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))
    scale = CANVAS / viewbox

    # Piece center on canvas (for radial drift)
    piece_cx_canvas = CANVAS / 2
    piece_cy_canvas = CANVAS / 2

    # Phase t for this frame (full cycle = N_FRAMES → one slow breath in/out)
    t = (i / N_FRAMES) * 2 * math.pi

    # --- Static atoms (anchor) ---
    for a in atoms_static:
        bbox = a["bbox"]
        if bbox[2] <= 0 or bbox[3] <= 0:
            continue
        img = Image.open(a["isolated_png"]).convert("RGBA")
        target_w = max(1, int(round(bbox[2] * scale)))
        target_h = max(1, int(round(bbox[3] * scale)))
        img = img.resize((target_w, target_h), Image.LANCZOS)
        x = int(round(bbox[0] * scale))
        y = int(round(bbox[1] * scale))
        canvas.alpha_composite(img, (x, y))

    # --- Breathing atoms ---
    for a in atoms_breath:
        bbox = a["bbox"]
        if bbox[2] <= 0 or bbox[3] <= 0:
            continue
        img = Image.open(a["isolated_png"]).convert("RGBA")
        base_w = max(1, int(round(bbox[2] * scale)))
        base_h = max(1, int(round(bbox[3] * scale)))
        img = img.resize((base_w, base_h), Image.LANCZOS)

        # Atom centroid on canvas
        cx_canvas = int(round(a["centroid"][0] * scale))
        cy_canvas = int(round(a["centroid"][1] * scale))

        # Per-atom phase offset based on angle from piece center (creates
        # radial wave: atoms on one side breathe slightly ahead of opposite)
        dx = cx_canvas - piece_cx_canvas
        dy = cy_canvas - piece_cy_canvas
        atom_angle = math.atan2(dy, dx)
        atom_phase = atom_angle + breath_phase

        # Scale pulse (in-out)
        scale_mult = 1.0 + SCALE_PULSE * math.sin(t + atom_phase)

        # Radial drift (outward / inward — same rhythm as scale for breath feel)
        drift = DRIFT_AMPLITUDE * CANVAS * math.sin(t + atom_phase)
        dist = math.hypot(dx, dy) or 1.0
        drift_x = int(round((dx / dist) * drift))
        drift_y = int(round((dy / dist) * drift))

        # Rotation (slightly faster cycle for shimmer)
        rot = ROTATE_AMPLITUDE * math.sin(1.7 * t + atom_phase * 0.6)

        sprite = transform_atom(img, scale_mult, rot)
        paste_centered(canvas, sprite, cx_canvas + drift_x, cy_canvas + drift_y)

    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", default="Nature_Cosmic_Sun",
                    choices=list(PIECE_VIEWBOX.keys()))
    ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--breath-phase", type=float, default=0.0,
                    help="Global phase shift to align breath with audio")
    args = ap.parse_args()

    piece = args.piece
    viewbox = PIECE_VIEWBOX[piece]
    atoms = load_atoms(piece)
    print(f"Piece: {piece} (viewBox {viewbox}x{viewbox}, {len(atoms)} atoms)")

    atoms_static = [a for a in atoms if a["label"] in STATIC_LABELS]
    atoms_breath = [a for a in atoms if a["label"] not in STATIC_LABELS]
    print(f"  Static atoms (anchor): {len(atoms_static)}")
    print(f"  Breathing atoms: {len(atoms_breath)}")

    piece_slug = piece.lower().replace("_", "_")
    out_dir = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version:03d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version:03d}.mp4"

    print(f"Rendering {N_FRAMES} frames at {CANVAS}x{CANVAS}...")
    for i in range(N_FRAMES):
        frame = render_frame(atoms_static, atoms_breath, i, viewbox, args.breath_phase)
        frame.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
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
