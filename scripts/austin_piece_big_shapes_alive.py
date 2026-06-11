#!/usr/bin/env python3
"""
Big-shapes-alive v001 — Salmon pivot.

Peer + operator 2026-05-17 ~3 PM: Cosmic_Sun v003c is the breathing
proof for RADIAL pieces. Salmon is different piece-nature: roe-field
micro-breathing produces fuzzy noise, not "alive illustration." Operator
wants larger recognizable shapes moving independently — body, head,
roe field as a unit, fin/tail groups, eye/pivots.

This script:
  1. Groups atoms semantically into 4-6 SHAPE GROUPS (not 184+ atoms)
  2. Each group has its own animation behavior (drift/wave/pulse)
  3. Renders at higher resolution (1536) to reduce mask-pixel mismatch
     artifacts
  4. cv2-inpaints base with ALL group regions removed
  5. Composites per-frame with group sprites at animated positions

Groups for Salmon (yin-yang two-fish composition):
  - roe_field: all 184 egg-roe atoms → field-wave (gentle x-wave)
  - upper_half: non-roe atoms with centroid_y < center → body drift
    (very slow rock/sway)
  - lower_half: non-roe atoms with centroid_y >= center → body drift
    (opposite phase, sway with upper)
  - eye_focals: the 2 eye-focal-oval atoms → slow pulse (heartbeat)

Each group moves as ONE sprite. No per-atom micro-motion.

INTERNAL ONLY per Austin consent floor.

Requires cv2 (opencv-python-headless via python3.11).
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
    print("WARNING: cv2 not available — abort")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS = 1536
FPS = 24
N_FRAMES = 144

PIECE_VIEWBOX = {
    "Animal_Salmon_Spawn_Eggs": 1500,
    "Nature_Cosmic_Sun": 108,
}
PIECE_JPG = {
    "Animal_Salmon_Spawn_Eggs": "Animal_Salmon_Spawn_Eggs.jpg",
    "Nature_Cosmic_Sun": "Nature_Cosmic_Sun.jpg",
}

INPAINT_DILATE_PX = 5


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


def build_atom_alpha(atom: dict) -> np.ndarray:
    """uint8 CANVAS×CANVAS mask: 255 inside atom, 0 outside."""
    iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.LANCZOS)
    return 255 - np.asarray(iso, dtype=np.uint8)


def define_groups_salmon(atoms: list[dict], viewbox: int) -> dict:
    """Return dict: group_name → list of atoms in that group."""
    center_y_vb = viewbox / 2
    groups = {
        "roe_field": [],
        "upper_half": [],
        "lower_half": [],
        "eye_focals": [],
    }
    for a in atoms:
        label = a["label"]
        cy = a["centroid"][1]
        if label == "egg-roe":
            groups["roe_field"].append(a)
        elif label == "eye-focal-oval":
            groups["eye_focals"].append(a)
        elif label in {"background-field", "negative-space"}:
            continue  # static, not animated
        else:
            if cy < center_y_vb:
                groups["upper_half"].append(a)
            else:
                groups["lower_half"].append(a)
    return {k: v for k, v in groups.items() if v}


def build_group_layer(group: list[dict]) -> tuple[Image.Image, np.ndarray, tuple[int, int]]:
    """Build union mask + group centroid for a group of atoms.

    Returns (union_mask_image, union_mask_array, group_centroid_canvas).
    """
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    cxs, cys = [], []
    for a in group:
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        cxs.append(a["centroid"][0])
        cys.append(a["centroid"][1])
    # Group centroid in viewbox coords → canvas coords
    return Image.fromarray(union, "L"), union, (sum(cxs) / len(cxs), sum(cys) / len(cys))


def inpaint_base(base: Image.Image, all_group_masks: np.ndarray) -> Image.Image:
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
    binary = (all_group_masks > 128).astype(np.uint8) * 255
    kernel = np.ones((INPAINT_DILATE_PX, INPAINT_DILATE_PX), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    bgr = cv2.cvtColor(base_arr, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(bgr, dilated, inpaintRadius=10, flags=cv2.INPAINT_TELEA)
    rgb = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb, "RGB")


def group_animation(group_name: str, t: float, group_centroid_canvas: tuple[float, float]) -> tuple[int, int, float, float]:
    """Return (drift_x, drift_y, scale_mult, rotate_deg) for this group at time t.

    Behaviors per peer spec:
      roe_field: gentle x-wave (current/flow drift along x axis)
      upper_half: very subtle swim/rock (small drift + tiny rotation)
      lower_half: opposite phase to upper (mirror sway)
      eye_focals: slow pulse (scale only, no drift)
    """
    cx, cy = group_centroid_canvas
    if group_name == "roe_field":
        # Field as a unit drifts gently left-right
        drift_x = int(round(0.008 * CANVAS * math.sin(t)))
        drift_y = int(round(0.003 * CANVAS * math.sin(2 * t)))
        return drift_x, drift_y, 1.0, 0.0
    elif group_name == "upper_half":
        # Slow rock — drift + tiny rotation
        drift_x = int(round(0.010 * CANVAS * math.sin(t)))
        drift_y = int(round(0.005 * CANVAS * math.sin(t + math.pi / 4)))
        rot = 0.8 * math.sin(t)
        return drift_x, drift_y, 1.0, rot
    elif group_name == "lower_half":
        # Mirror sway — opposite phase
        drift_x = int(round(0.010 * CANVAS * math.sin(t + math.pi)))
        drift_y = int(round(0.005 * CANVAS * math.sin(t + math.pi + math.pi / 4)))
        rot = 0.8 * math.sin(t + math.pi)
        return drift_x, drift_y, 1.0, rot
    elif group_name == "eye_focals":
        # Slow pulse — scale only
        scale = 1.0 + 0.04 * math.sin(2 * t)
        return 0, 0, scale, 0.0
    else:
        return 0, 0, 1.0, 0.0


def transform_layer(layer: Image.Image, scale_mult: float, rotate_deg: float) -> Image.Image:
    if abs(scale_mult - 1.0) > 0.001:
        w, h = layer.size
        layer = layer.resize((max(1, int(round(w * scale_mult))),
                              max(1, int(round(h * scale_mult)))), Image.LANCZOS)
    if abs(rotate_deg) > 0.05:
        layer = layer.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    return layer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", default="Animal_Salmon_Spawn_Eggs")
    ap.add_argument("--version-tag", default="005_salmon_big_shapes_alive_v001")
    args = ap.parse_args()

    piece = args.piece
    viewbox = PIECE_VIEWBOX[piece]
    atoms = load_atoms(piece)
    groups = define_groups_salmon(atoms, viewbox)
    print(f"Piece: {piece}")
    for name, group in groups.items():
        print(f"  group {name}: {len(group)} atoms")

    base = load_base_jpg(piece)

    # Build per-group layers (mask, centroid)
    scale = CANVAS / viewbox
    group_data = {}
    union_all = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    print("Building per-group masks...")
    for name, group_atoms in groups.items():
        mask_img, mask_arr, centroid_vb = build_group_layer(group_atoms)
        union_all = np.maximum(union_all, mask_arr)
        cx_canvas = centroid_vb[0] * scale
        cy_canvas = centroid_vb[1] * scale
        # Crop mask to its bounding box
        ys, xs = np.where(mask_arr > 128)
        if len(xs) == 0:
            continue
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
        # Build colored sprite: apply mask to base, crop to bbox
        base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
        rgba = np.dstack([base_arr, mask_arr])
        sprite_full = Image.fromarray(rgba, "RGBA")
        sprite = sprite_full.crop((x0, y0, x1 + 1, y1 + 1))
        group_data[name] = {
            "sprite": sprite,
            "centroid_canvas": (cx_canvas, cy_canvas),
            "bbox_origin": (x0, y0),  # where the sprite was cropped from
            "atom_count": len(group_atoms),
        }
        print(f"  {name}: mask area={int((mask_arr > 128).sum())} px, sprite size={sprite.size}, centroid=({cx_canvas:.0f},{cy_canvas:.0f})")

    print("Inpainting base (removing all animated group regions)...")
    inpainted = inpaint_base(base, union_all)

    out_dir = INTERNAL / f"austin_piece_big_shapes_alive_{args.version_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_piece_big_shapes_alive_{args.version_tag}.mp4"
    inpainted.save(out_dir / "_inpainted_base.png")

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_max_inhale_t025.png",
              N_FRAMES - 1: "02_return_t100.png"}

    print(f"Rendering {N_FRAMES} frames at {CANVAS}x{CANVAS}...")
    for i in range(N_FRAMES):
        canvas = inpainted.copy().convert("RGBA")
        t = (i / N_FRAMES) * 2 * math.pi
        for name, gd in group_data.items():
            drift_x, drift_y, scale_mult, rot = group_animation(name, t, gd["centroid_canvas"])
            sprite = transform_layer(gd["sprite"], scale_mult, rot)
            sw, sh = sprite.size
            # Original sprite paste position (no transform) = bbox_origin
            # Transform changes sprite size; recompute paste so the sprite
            # is still centered on the group's animated position.
            paste_x = gd["bbox_origin"][0] + drift_x - (sw - gd["sprite"].size[0]) // 2
            paste_y = gd["bbox_origin"][1] + drift_y - (sh - gd["sprite"].size[1]) // 2
            canvas.alpha_composite(sprite, (paste_x, paste_y))
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
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
