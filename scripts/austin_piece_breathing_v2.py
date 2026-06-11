#!/usr/bin/env python3
"""
Austin Piece Breathing v002 — full-anchor.

v001 lost source identity (atoms isolated on white = chart, not piece).
v002 fix per peer 2026-05-17 PM:
  - Frame 0 + frame N = EXACT original SVG render (piece readable)
  - Animated atoms drawn ON TOP of base, so original anchor always shows
  - Only a SELECTED subset of atoms breathes (rays + face crescents/circles),
    NOT all 35 fg atoms. Keeps major body/rings/face structure stable.
  - Motion = primitives "expand/brighten/rotate subtly from their original
    positions" — at peak breath, atom visible at both rest (base) and
    animated position, creating subtle vibration/shimmer not chaos
  - At rest (offset = 0), animated atom overlays exactly on base position →
    looks identical to original
  - Background underlay locked

Acceptance criteria (peer):
  - At any paused frame, viewer can still identify Cosmic_Sun
  - Motion reads as internal vitality
  - No "floating cut-out shapes on white" feeling
  - Side-by-side stills: original, max-inhale, return frame

Output: austin_piece_breathing_nature_cosmic_sun_v002_full_anchor.mp4
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image
import csv
import math
import subprocess
import argparse

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

PIECE_VIEWBOX = {
    "Nature_Cosmic_Sun": 108,
    "Animal_Bird_Raven_Sun": 108,
    "Animal_Wolf_Spindle_Whorl": 1500,
    "Animal_Salmon_Spawn_Eggs": 1500,
    "Supernatural_Human_TheCreator_Background": 1500,
}

PIECE_SVG = {
    "Nature_Cosmic_Sun": "Nature_Cosmic_Sun.svg",
    "Animal_Bird_Raven_Sun": "Animal_Bird_Raven_Sun.svg",
    "Animal_Wolf_Spindle_Whorl": "Animal_Wolf_Spindle_Whorl.svg",
    "Animal_Salmon_Spawn_Eggs": "Animal_Salmon_Spawn_Eggs.svg",
}

# Atoms that ANIMATE (curated — keep structure mostly stable)
ANIMATED_LABELS = {
    "sun-ray",         # rays around outside
    "trigon",          # secondary radiating elements
    "crescent",        # face features
    "circle-oval",     # face details (small)
    "eye-focal-oval",  # eyes/pivots
}

# Atoms that DO NOT animate (anchor / structure)
SKIP_LABELS = {
    "background-field", "negative-space", "background",
    "formline-primary",   # major structural line — lock it
    "formline-secondary", # secondary structure — lock it
    "formline-tertiary",
    "body-element",       # body silhouettes — lock
    "fin-tail",           # body — lock
    "other",
    "wing-feather",
    "egg-roe",            # for salmon — keep roe field as static base unless we want it pulsing
    "sun-ray-spike",
}

CANVAS = 1024
FPS = 24
N_FRAMES = 144  # 6 sec — one slow breath cycle

# Motion params (subtle — peer noted v001 amplitudes felt right; just need
# proper anchor + selection)
DRIFT_AMPLITUDE = 0.012   # 1.2% radial drift outward
SCALE_PULSE = 0.025       # ±2.5% scale
ROTATE_AMPLITUDE = 1.5    # ±1.5 degrees


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


def render_base_svg(piece: str, out_path: Path):
    """Render the full SVG of the piece as the anchor base (always visible)."""
    svg = SOURCE_VECTORS / PIECE_SVG[piece]
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg), "-resize", f"{CANVAS}x{CANVAS}",
        "-gravity", "center", "-extent", f"{CANVAS}x{CANVAS}",
        str(out_path),
    ], check=True)


def transform_atom(img: Image.Image, scale_mult: float, rotate_deg: float) -> Image.Image:
    if abs(scale_mult - 1.0) > 0.001:
        w, h = img.size
        new_w = max(1, int(round(w * scale_mult)))
        new_h = max(1, int(round(h * scale_mult)))
        img = img.resize((new_w, new_h), Image.LANCZOS)
    if abs(rotate_deg) > 0.05:
        img = img.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", default="Nature_Cosmic_Sun",
                    choices=list(PIECE_VIEWBOX.keys()))
    ap.add_argument("--version", type=int, default=2)
    args = ap.parse_args()

    piece = args.piece
    viewbox = PIECE_VIEWBOX[piece]
    atoms = load_atoms(piece)
    print(f"Piece: {piece} (viewBox {viewbox}x{viewbox}, {len(atoms)} atoms)")

    atoms_animated = [a for a in atoms if a["label"] in ANIMATED_LABELS]
    print(f"  Animated atoms: {len(atoms_animated)}")
    if not atoms_animated:
        raise SystemExit("No animated atoms — check ANIMATED_LABELS vs atom labels")

    piece_slug = piece.lower()
    out_dir = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version:03d}_full_anchor"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version:03d}_full_anchor.mp4"

    # Render base SVG once (anchor)
    base_path = out_dir / "_base.png"
    render_base_svg(piece, base_path)
    base = Image.open(base_path).convert("RGBA")

    scale = CANVAS / viewbox
    piece_cx = CANVAS / 2
    piece_cy = CANVAS / 2

    print(f"Rendering {N_FRAMES} frames at {CANVAS}x{CANVAS}...")

    # Stills for peer's acceptance criteria
    stills_to_save = {0: "00_at_rest_t000.png",
                      N_FRAMES // 4: "01_max_inhale_t025.png",
                      N_FRAMES - 1: "02_return_t100.png"}

    for i in range(N_FRAMES):
        canvas = base.copy()
        t = (i / N_FRAMES) * 2 * math.pi

        for a in atoms_animated:
            bbox = a["bbox"]
            if bbox[2] <= 0 or bbox[3] <= 0:
                continue

            cx_canvas = int(round(a["centroid"][0] * scale))
            cy_canvas = int(round(a["centroid"][1] * scale))

            # Per-atom phase based on angular position
            dx = cx_canvas - piece_cx
            dy = cy_canvas - piece_cy
            atom_phase = math.atan2(dy, dx)

            # Scale pulse
            scale_mult = 1.0 + SCALE_PULSE * math.sin(t + atom_phase)
            # Radial drift outward
            drift = DRIFT_AMPLITUDE * CANVAS * math.sin(t + atom_phase)
            dist = math.hypot(dx, dy) or 1.0
            drift_x = int(round((dx / dist) * drift))
            drift_y = int(round((dy / dist) * drift))
            # Rotation
            rot = ROTATE_AMPLITUDE * math.sin(1.7 * t + atom_phase * 0.6)

            # At rest (offset ~0), skip overlay — base already correct
            if abs(drift_x) < 1 and abs(drift_y) < 1 and abs(scale_mult - 1.0) < 0.003 and abs(rot) < 0.1:
                continue

            # Load atom sprite at its actual canvas size
            img = Image.open(a["isolated_png"]).convert("RGBA")
            base_w = max(1, int(round(bbox[2] * scale)))
            base_h = max(1, int(round(bbox[3] * scale)))
            img = img.resize((base_w, base_h), Image.LANCZOS)

            sprite = transform_atom(img, scale_mult, rot)
            sw, sh = sprite.size
            paste_x = cx_canvas + drift_x - sw // 2
            paste_y = cy_canvas + drift_y - sh // 2
            canvas.alpha_composite(sprite, (paste_x, paste_y))

        out_path = out_dir / f"frame_{i:04d}.png"
        canvas.convert("RGB").save(out_path)

        if i in stills_to_save:
            canvas.convert("RGB").save(out_dir / stills_to_save[i])

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
        print(f"  stills for acceptance review:")
        for n in stills_to_save.values():
            print(f"    {out_dir}/{n}")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
