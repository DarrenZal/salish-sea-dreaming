#!/usr/bin/env python3
"""
Austin Piece Breathing v003 — source-fidelity fix.

Peer 2026-05-17 PM caught two render-pipeline bugs in v002:
  Bug 1: ImageMagick rendered Nature_Cosmic_Sun.svg badly (huge black
    disc, missing color/face structure). Frame 0 must visually match the
    actual training JPG, not a broken SVG render.
  Bug 2: Isolated atom PNGs are grayscale-on-white silhouettes (no
    transparency), not colored sprites. Direct alpha_composite over a
    base produced white boxes / black cutouts, not animated atoms.

v003 fixes:
  - base = austin-v2-ingest/training/Nature_Cosmic_Sun.jpg scaled to 1024
  - per animated atom:
      1. resize isolated PNG to canvas (256→1024)
      2. derive alpha mask from PNG luminance: mask = 255 - L
         (black atom pixels → opaque, white background → transparent)
      3. apply mask to a copy of the base → colored_layer where only
         this atom's pixels are visible
      4. crop colored_layer to the atom's bbox (drop empty space)
      5. apply per-frame transform (scale + rotate around bbox center)
      6. paste at offset centroid
  - Frame 0 / return frame = pure base (no overlays at rest)
  - Max-inhale = atom-colored sprites visible at offset positions

The double-exposure question (atom visible at both rest position from
base AND offset position from overlay) is still open architecturally;
v003 ships honest first-pass to confirm the source-fidelity bug is fixed.
If double-exposure reads as ghosting rather than vibration, v004 will
add true-displacement (mask atom out of base before drawing at offset).

INTERNAL ONLY per Austin consent floor.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import csv
import math
import subprocess
import argparse

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

ANIMATED_LABELS_DEFAULT = {"sun-ray", "trigon", "crescent", "circle-oval", "eye-focal-oval"}
# Reduced set for "strong" variant — fewer atoms moving more dramatically
# keeps the piece readable even when motion is larger
ANIMATED_LABELS_RAYS_ONLY = {"sun-ray", "eye-focal-oval"}
# Salmon-specific: roe field as current/wave + eye/pivot pulse
ANIMATED_LABELS_ROE_PLUS_EYES = {"egg-roe", "eye-focal-oval"}

# Phase functions — how per-atom phase offset is derived from position
# radial   : phase = angle from piece center (radial wave)
# wave-x   : phase = x position (left-to-right wave; good for roe field)
# wave-y   : phase = y position (top-to-bottom wave)
# pulse    : phase = distance from center (outward pulse from center)
PHASE_MODES = {"radial", "wave-x", "wave-y", "pulse"}

CANVAS = 1024
FPS = 24
N_FRAMES = 144

# Base motion params (multipliers below scale these per --intensity preset)
DRIFT_AMPLITUDE_BASE = 0.012
SCALE_PULSE_BASE = 0.025
ROTATE_AMPLITUDE_BASE = 1.5

INTENSITY_PRESETS = {
    # subtle / projection-safe: meditative shimmer, unmistakably original
    "subtle":  {"drift": 0.50, "scale": 0.50, "rotate": 0.60, "label_set": "default"},
    # default v003 — operator confirmed lane viable at this intensity
    "default": {"drift": 1.00, "scale": 1.00, "rotate": 1.00, "label_set": "default"},
    # strong / "alive": more visible motion, fewer atoms so it doesn't read noisy
    "strong":  {"drift": 1.50, "scale": 1.50, "rotate": 1.30, "label_set": "rays_only"},
}


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
    """Load training JPG and fit to CANVAS×CANVAS preserving aspect."""
    jpg_path = TRAINING / PIECE_JPG[piece]
    if not jpg_path.exists():
        raise SystemExit(f"Missing training JPG: {jpg_path}")
    img = Image.open(jpg_path).convert("RGB")
    # Fit to canvas, pad with white if non-square
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.LANCZOS)
    if img.size != (CANVAS, CANVAS):
        canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
        x = (CANVAS - img.width) // 2
        y = (CANVAS - img.height) // 2
        canvas.paste(img, (x, y))
        img = canvas
    return img


def build_atom_layer(atom: dict, base_rgba: Image.Image, viewbox: int) -> tuple[Image.Image, tuple[int, int]]:
    """Return (colored sprite cropped to atom bbox, bbox center on canvas).

    Pipeline: scale isolated PNG → 1024, invert luminance for alpha mask,
    apply mask to base → colored 1024x1024 with only this atom visible.
    Crop to atom's canvas bbox + return with center for transform anchoring.
    """
    scale = CANVAS / viewbox
    bbox = atom["bbox"]

    # Canvas-space bbox (allow negative offsets — atom may extend past viewbox edge)
    bx = int(round(bbox[0] * scale))
    by = int(round(bbox[1] * scale))
    bw = max(1, int(round(bbox[2] * scale)))
    bh = max(1, int(round(bbox[3] * scale)))

    # Load isolated mask PNG, resize to canvas, derive alpha
    iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.LANCZOS)
    iso_arr = np.asarray(iso, dtype=np.uint8)
    alpha_arr = 255 - iso_arr  # black atom -> opaque; white bg -> transparent

    # Build colored layer = base RGB + alpha mask
    base_arr = np.asarray(base_rgba.convert("RGB"), dtype=np.uint8)
    rgba = np.dstack([base_arr, alpha_arr])
    full_layer = Image.fromarray(rgba, "RGBA")

    # Crop to atom canvas bbox (clip to canvas bounds for safety)
    crop_x0 = max(0, bx)
    crop_y0 = max(0, by)
    crop_x1 = min(CANVAS, bx + bw)
    crop_y1 = min(CANVAS, by + bh)
    if crop_x1 <= crop_x0 or crop_y1 <= crop_y0:
        return None, (0, 0)
    sprite = full_layer.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    # Center of cropped sprite on canvas (use atom centroid, not bbox center)
    cx_canvas = int(round(atom["centroid"][0] * scale))
    cy_canvas = int(round(atom["centroid"][1] * scale))
    return sprite, (cx_canvas, cy_canvas)


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
    ap.add_argument("--piece", default="Nature_Cosmic_Sun")
    ap.add_argument("--version-tag", default="003_source_fidelity",
                    help="Tag appended to output filenames (e.g., '003b_subtle', '003c_strong')")
    ap.add_argument("--intensity", default="default",
                    choices=list(INTENSITY_PRESETS.keys()),
                    help="Motion preset (subtle / default / strong)")
    ap.add_argument("--phase-mode", default="radial", choices=sorted(PHASE_MODES),
                    help="How per-atom phase is derived: radial (Cosmic_Sun rays), "
                         "wave-x/y (traveling wave through a field — good for roe), "
                         "pulse (distance from center).")
    ap.add_argument("--label-set", default=None,
                    help="Override animated atom label set. Comma-separated, e.g. "
                         "'egg-roe,eye-focal-oval' for Salmon. Defaults from --intensity.")
    args = ap.parse_args()

    preset = INTENSITY_PRESETS[args.intensity]
    drift_amp = DRIFT_AMPLITUDE_BASE * preset["drift"]
    scale_pulse = SCALE_PULSE_BASE * preset["scale"]
    rotate_amp = ROTATE_AMPLITUDE_BASE * preset["rotate"]
    if args.label_set:
        animated_labels = set(s.strip() for s in args.label_set.split(",") if s.strip())
    elif preset["label_set"] == "rays_only":
        animated_labels = ANIMATED_LABELS_RAYS_ONLY
    else:
        animated_labels = ANIMATED_LABELS_DEFAULT

    piece = args.piece
    viewbox = PIECE_VIEWBOX[piece]
    atoms = load_atoms(piece)
    atoms_animated = [a for a in atoms if a["label"] in animated_labels]
    print(f"Piece: {piece} | intensity: {args.intensity} (drift x{preset['drift']}, scale x{preset['scale']}, rot x{preset['rotate']})")
    print(f"  atoms: {len(atoms)} | animated: {len(atoms_animated)} | label set: {preset['label_set']}")

    base = load_base_jpg(piece)

    piece_slug = piece.lower()
    out_dir = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_piece_breathing_{piece_slug}_v{args.version_tag}.mp4"

    # Pre-build colored sprite + center for each animated atom (one pass; sprite reused per frame with transforms)
    print("Pre-building atom sprites from training JPG...")
    sprites = []
    for a in atoms_animated:
        sprite, center = build_atom_layer(a, base, viewbox)
        if sprite is None:
            continue
        sprites.append({
            "sprite": sprite,
            "center": center,  # rest centroid on canvas
            "atom": a,
        })
    print(f"  Built {len(sprites)} sprites")

    piece_cx = CANVAS / 2
    piece_cy = CANVAS / 2

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_max_inhale_t025.png",
              N_FRAMES - 1: "02_return_t100.png"}

    print(f"Rendering {N_FRAMES} frames...")
    for i in range(N_FRAMES):
        canvas = base.copy().convert("RGBA")
        t = (i / N_FRAMES) * 2 * math.pi

        for s in sprites:
            cx, cy = s["center"]
            dx = cx - piece_cx
            dy = cy - piece_cy

            # Phase function selection
            if args.phase_mode == "radial":
                phase = math.atan2(dy, dx)
            elif args.phase_mode == "wave-x":
                # Wavelength = canvas width → 2π across canvas; gives traveling wave
                phase = (cx / CANVAS) * 2 * math.pi
            elif args.phase_mode == "wave-y":
                phase = (cy / CANVAS) * 2 * math.pi
            elif args.phase_mode == "pulse":
                # Distance-from-center scaled to one wavelength = half canvas
                phase = (math.hypot(dx, dy) / (CANVAS / 2)) * 2 * math.pi
            else:
                phase = 0.0

            scale_mult = 1.0 + scale_pulse * math.sin(t + phase)
            drift = drift_amp * CANVAS * math.sin(t + phase)
            dist = math.hypot(dx, dy) or 1.0
            drift_x = int(round((dx / dist) * drift))
            drift_y = int(round((dy / dist) * drift))
            rot = rotate_amp * math.sin(1.7 * t + phase * 0.6)

            # Skip overlay if at rest (atom already in correct position from base)
            if abs(drift_x) < 1 and abs(drift_y) < 1 and abs(scale_mult - 1.0) < 0.003 and abs(rot) < 0.1:
                continue

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
        print(f"  stills:")
        for n in stills.values():
            print(f"    {out_dir}/{n}")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
