#!/usr/bin/env python3
"""
Austin Piece Breathing v004 — true displacement.

v003c strong worked for Cosmic_Sun (double-exposure shimmer reads as
spirit/energy). v003 Salmon wave-x failed: 184 roe doubled-up reads as
duplicate circles not motion. Operator 2026-05-17 ~2:45 PM: "imagine
the circles themselves moving around, rather than putting new circles
on top."

v004 fix: TRUE DISPLACEMENT.
  1. Pre-compute an "inpainted base" = training JPG with all animated
     atom regions replaced by surrounding background color (cv2.inpaint
     with Telea method). Roe holes → cream background; ray holes →
     orange background.
  2. Per frame: start with inpainted base (no original atoms visible),
     then draw each animated atom sprite at its ANIMATED position only.
  3. At rest (offset=0): sprite drawn at its rest position → looks
     identical to original JPG.
  4. At peak breath: sprite drawn at offset position → original rest
     position now shows the inpainted background → atom appears to have
     actually moved.

No more double-exposure. Circles literally translate.

Requires cv2 (opencv-python-headless). Run with python3.11 if needed:
    python3.11 scripts/austin_piece_breathing_v4.py [args]
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import csv
import math
import subprocess
import argparse

try:
    import cv2
    HAVE_CV2 = True
except ImportError:
    HAVE_CV2 = False
    print("WARNING: cv2 not available — using pure-PIL fallback inpaint (slower, less smooth)")

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

PIECE_VIEWBOX = {
    "Nature_Cosmic_Sun": 108,
    "Animal_Bird_Raven_Sun": 108,
    "Animal_Wolf_Spindle_Whorl": 1500,
    "Animal_Salmon_Spawn_Eggs": 1500,
}
PIECE_JPG = {
    "Nature_Cosmic_Sun": "Nature_Cosmic_Sun.jpg",
    "Animal_Bird_Raven_Sun": "Animal_Bird_Raven_Sun.jpg",
    "Animal_Wolf_Spindle_Whorl": "Animal_Wolf_Spindle_Whorl.jpg",
    "Animal_Salmon_Spawn_Eggs": "Animal_Salmon_Spawn_Eggs.jpg",
}

DEFAULT_LABEL_SETS = {
    "cosmic": {"sun-ray", "eye-focal-oval"},  # v003c strong's set
    "salmon_roe": {"egg-roe", "eye-focal-oval"},
    "all_primitives": {"sun-ray", "trigon", "crescent", "circle-oval", "eye-focal-oval"},
}

CANVAS = 1024
FPS = 24
N_FRAMES = 144

DRIFT_AMPLITUDE_BASE = 0.012
SCALE_PULSE_BASE = 0.025
ROTATE_AMPLITUDE_BASE = 1.5

INTENSITY_PRESETS = {
    "subtle":  {"drift": 0.50, "scale": 0.50, "rotate": 0.60},
    "default": {"drift": 1.00, "scale": 1.00, "rotate": 1.00},
    "strong":  {"drift": 1.50, "scale": 1.50, "rotate": 1.30},
}

PHASE_MODES = {"radial", "wave-x", "wave-y", "pulse"}

# Inpaint mask dilation (expand each atom mask by N px before inpaint to
# ensure clean fill around antialiased edges)
INPAINT_DILATE_PX = 3


def load_atoms(piece: str) -> list[dict]:
    csv_path = DECOMPOSED / piece / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
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


def load_base_jpg(piece: str) -> Image.Image:
    jpg_path = TRAINING / PIECE_JPG[piece]
    img = Image.open(jpg_path).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.LANCZOS)
    if img.size != (CANVAS, CANVAS):
        canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
        x = (CANVAS - img.width) // 2
        y = (CANVAS - img.height) // 2
        canvas.paste(img, (x, y))
        img = canvas
    return img


def build_atom_alpha_mask(atom: dict, viewbox: int) -> np.ndarray:
    """Return uint8 1024x1024 alpha mask for one atom (255 inside, 0 outside)."""
    iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.LANCZOS)
    arr = 255 - np.asarray(iso, dtype=np.uint8)
    return arr


def build_atom_sprite(atom: dict, base_rgba: np.ndarray, viewbox: int) -> tuple[Image.Image, tuple[int, int]]:
    scale = CANVAS / viewbox
    bbox = atom["bbox"]
    bx = int(round(bbox[0] * scale))
    by = int(round(bbox[1] * scale))
    bw = max(1, int(round(bbox[2] * scale)))
    bh = max(1, int(round(bbox[3] * scale)))

    alpha_arr = build_atom_alpha_mask(atom, viewbox)
    rgba = np.dstack([base_rgba, alpha_arr])
    full_layer = Image.fromarray(rgba, "RGBA")

    crop_x0 = max(0, bx)
    crop_y0 = max(0, by)
    crop_x1 = min(CANVAS, bx + bw)
    crop_y1 = min(CANVAS, by + bh)
    if crop_x1 <= crop_x0 or crop_y1 <= crop_y0:
        return None, (0, 0)
    sprite = full_layer.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    cx_canvas = int(round(atom["centroid"][0] * scale))
    cy_canvas = int(round(atom["centroid"][1] * scale))
    return sprite, (cx_canvas, cy_canvas)


def inpaint_base(base: Image.Image, animated_atoms: list[dict], viewbox: int) -> Image.Image:
    """Return base with all animated-atom regions inpainted with surrounding color.

    Uses cv2.inpaint (Telea method) if available, else pure-PIL fallback
    that fills each masked region with the mean color of its bbox boundary.
    """
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)

    # Union of all animated atom masks
    union_mask = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    for a in animated_atoms:
        m = build_atom_alpha_mask(a, viewbox)
        union_mask = np.maximum(union_mask, m)

    # Threshold to binary mask (atoms = 255, bg = 0)
    binary_mask = (union_mask > 128).astype(np.uint8) * 255

    if HAVE_CV2:
        # Dilate to clean up antialiased atom edges
        kernel = np.ones((INPAINT_DILATE_PX, INPAINT_DILATE_PX), np.uint8)
        dilated = cv2.dilate(binary_mask, kernel, iterations=1)
        # Convert to BGR for cv2
        base_bgr = cv2.cvtColor(base_arr, cv2.COLOR_RGB2BGR)
        inpainted_bgr = cv2.inpaint(base_bgr, dilated, inpaintRadius=8, flags=cv2.INPAINT_TELEA)
        inpainted_arr = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(inpainted_arr, "RGB")
    else:
        # Pure-PIL fallback: for each connected masked region, sample mean
        # color of its bbox boundary, fill region with that color.
        # Crude but works.
        from PIL import ImageFilter
        filled = base_arr.copy()
        # Just use boundary-mean fill — simple approach
        for a in animated_atoms:
            scale = CANVAS / viewbox
            bbox = a["bbox"]
            bx = int(round(bbox[0] * scale))
            by = int(round(bbox[1] * scale))
            bw = max(1, int(round(bbox[2] * scale)))
            bh = max(1, int(round(bbox[3] * scale)))
            # Bbox expanded by 8 px for boundary sampling
            ex = max(0, bx - 8)
            ey = max(0, by - 8)
            ex2 = min(CANVAS, bx + bw + 8)
            ey2 = min(CANVAS, by + bh + 8)
            border_region = base_arr[ey:ey2, ex:ex2].copy()
            # mask within border_region
            local_mask = union_mask[ey:ey2, ex:ex2] > 128
            outside = ~local_mask
            if outside.any():
                mean_color = border_region[outside].mean(axis=0).astype(np.uint8)
                # Fill masked pixels in filled[] with mean_color
                fill_target = (union_mask[ey:ey2, ex:ex2] > 128)
                filled[ey:ey2, ex:ex2][fill_target] = mean_color
        return Image.fromarray(filled, "RGB")


def transform_sprite(sprite: Image.Image, scale_mult: float, rotate_deg: float) -> Image.Image:
    if abs(scale_mult - 1.0) > 0.001:
        w, h = sprite.size
        sprite = sprite.resize((max(1, int(round(w * scale_mult))),
                                max(1, int(round(h * scale_mult)))), Image.LANCZOS)
    if abs(rotate_deg) > 0.05:
        sprite = sprite.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    return sprite


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", default="Animal_Salmon_Spawn_Eggs")
    ap.add_argument("--version-tag", default="004_true_displacement_v001")
    ap.add_argument("--intensity", default="default", choices=list(INTENSITY_PRESETS.keys()))
    ap.add_argument("--phase-mode", default="wave-x", choices=sorted(PHASE_MODES))
    ap.add_argument("--label-set", default="salmon_roe",
                    help="Preset key in DEFAULT_LABEL_SETS, OR comma-separated labels.")
    args = ap.parse_args()

    preset = INTENSITY_PRESETS[args.intensity]
    drift_amp = DRIFT_AMPLITUDE_BASE * preset["drift"]
    scale_pulse = SCALE_PULSE_BASE * preset["scale"]
    rotate_amp = ROTATE_AMPLITUDE_BASE * preset["rotate"]

    if "," in args.label_set:
        animated_labels = set(s.strip() for s in args.label_set.split(","))
    elif args.label_set in DEFAULT_LABEL_SETS:
        animated_labels = DEFAULT_LABEL_SETS[args.label_set]
    else:
        animated_labels = {args.label_set}

    piece = args.piece
    viewbox = PIECE_VIEWBOX[piece]
    atoms = load_atoms(piece)
    atoms_animated = [a for a in atoms if a["label"] in animated_labels]
    print(f"Piece: {piece} | intensity: {args.intensity} | phase: {args.phase_mode}")
    print(f"  atoms: {len(atoms)} | animated: {len(atoms_animated)} | labels: {sorted(animated_labels)}")

    base = load_base_jpg(piece)
    print("Building inpainted base (removing animated atoms)...")
    inpainted = inpaint_base(base, atoms_animated, viewbox)

    print("Pre-building atom sprites from ORIGINAL base (so sprites carry correct colors)...")
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
    sprites = []
    for a in atoms_animated:
        sprite, center = build_atom_sprite(a, base_arr, viewbox)
        if sprite is None:
            continue
        sprites.append({"sprite": sprite, "center": center, "atom": a})
    print(f"  Built {len(sprites)} sprites")

    piece_slug = piece.lower()
    out_dir = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version_tag}.mp4"

    # Save inpainted base as diagnostic still
    inpainted.save(out_dir / "_inpainted_base.png")

    piece_cx = CANVAS / 2
    piece_cy = CANVAS / 2

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_max_inhale_t025.png",
              N_FRAMES - 1: "02_return_t100.png"}

    print(f"Rendering {N_FRAMES} frames...")
    for i in range(N_FRAMES):
        # Start from INPAINTED base (no original atoms visible)
        canvas = inpainted.copy().convert("RGBA")
        t = (i / N_FRAMES) * 2 * math.pi

        for s in sprites:
            cx, cy = s["center"]
            dx = cx - piece_cx
            dy = cy - piece_cy

            if args.phase_mode == "radial":
                phase = math.atan2(dy, dx)
            elif args.phase_mode == "wave-x":
                phase = (cx / CANVAS) * 2 * math.pi
            elif args.phase_mode == "wave-y":
                phase = (cy / CANVAS) * 2 * math.pi
            elif args.phase_mode == "pulse":
                phase = (math.hypot(dx, dy) / (CANVAS / 2)) * 2 * math.pi
            else:
                phase = 0.0

            scale_mult = 1.0 + scale_pulse * math.sin(t + phase)
            drift = drift_amp * CANVAS * math.sin(t + phase)
            dist = math.hypot(dx, dy) or 1.0
            drift_x = int(round((dx / dist) * drift))
            drift_y = int(round((dy / dist) * drift))
            rot = rotate_amp * math.sin(1.7 * t + phase * 0.6)

            # ALWAYS draw the sprite — even at "rest" we need to draw it so
            # the inpainted background doesn't show the empty atom hole.
            xform = transform_sprite(s["sprite"], scale_mult, rot)
            sw, sh = xform.size
            paste_x = cx + drift_x - sw // 2
            paste_y = cy + drift_y - sh // 2
            canvas.alpha_composite(xform, (paste_x, paste_y))

        out_path = out_dir / f"frame_{i:04d}.png"
        canvas.convert("RGB").save(out_path)
        if i in stills:
            canvas.convert("RGB").save(out_dir / stills[i])
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
        print(f"\n→ {out_mp4}")
        print(f"  inpainted base: {out_dir}/_inpainted_base.png")
        print(f"  stills: {', '.join(stills.values())}")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
