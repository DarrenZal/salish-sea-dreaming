#!/usr/bin/env python3
"""
Salmon body articulation v002 — swimming yin-yang.

Big-shapes-alive v001 worked partially: operator confirmed
yin-yang salmon bodies-as-units lands. Failed: roe/circle
sprite mask artifacts (outer ring stays, inner piece moves).

v002 direction per peer 2026-05-17 ~3:10 PM:
  1. FREEZE roe field entirely — leave as part of static base.
     No inpaint, no sprite, no motion. Eliminates mask artifact.
  2. Salmon bodies swim — figure-8 sway + tiny rotation, upper
     and lower counterphase ("chasing each other's tails").
  3. Internal forms move with slight independent personality:
     eye-focal pulse + tiny drift, fin-tail wave delayed from
     body, body crescents follow body with slight phase lag.
  4. Sparse: 6-8 clean animated groups, not 184 fuzzy atoms.
  5. Loop cleanly over 6 seconds.

Groups (salmon yin-yang two-fish, by upper/lower split + label):
  - upper_body: upper non-roe non-eye non-fin atoms (main swim motion)
  - lower_body: same for lower (counterphase swim)
  - upper_eye: eye-focal-oval in upper region (pulse + look)
  - lower_eye: eye-focal-oval in lower region (pulse + look)
  - upper_fin: fin-tail in upper region (delayed wave)
  - lower_fin: fin-tail in lower region (delayed wave)

Roe field = static (part of base; not animated, not inpainted).

INTERNAL ONLY per Austin consent floor. Requires cv2 via python3.11.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import csv
import math
import subprocess
import argparse

try:
    import cv2
    HAVE_CV2 = True
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS = 1536
FPS = 24
N_FRAMES = 144

PIECE = "Animal_Salmon_Spawn_Eggs"
VIEWBOX = 1500
JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"

INPAINT_DILATE_PX = 5

# Atoms that stay STATIC (part of base, never animated)
# Includes egg-roe (peer pivot — freeze for clean visual)
STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}


def load_atoms() -> list[dict]:
    csv_path = DECOMPOSED / PIECE / "atom_metadata.csv"
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
                    "isolated_png": DECOMPOSED / PIECE / row["isolated_png"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def load_base_jpg() -> Image.Image:
    jpg_path = TRAINING / JPG_NAME
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
    iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.LANCZOS)
    return 255 - np.asarray(iso, dtype=np.uint8)


def define_groups(atoms: list[dict]) -> dict:
    """Group atoms into body / eye / fin per upper-or-lower half."""
    center_y_vb = VIEWBOX / 2
    groups = {
        "upper_body": [], "lower_body": [],
        "upper_eye": [], "lower_eye": [],
        "upper_fin": [], "lower_fin": [],
    }
    for a in atoms:
        label = a["label"]
        if label in STATIC_LABELS:
            continue
        cy = a["centroid"][1]
        is_upper = cy < center_y_vb
        if label == "eye-focal-oval":
            (groups["upper_eye"] if is_upper else groups["lower_eye"]).append(a)
        elif label == "fin-tail":
            (groups["upper_fin"] if is_upper else groups["lower_fin"]).append(a)
        else:
            (groups["upper_body"] if is_upper else groups["lower_body"]).append(a)
    return {k: v for k, v in groups.items() if v}


def build_group_layer(group: list[dict], base_arr: np.ndarray) -> dict:
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    cxs, cys = [], []
    for a in group:
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        cxs.append(a["centroid"][0])
        cys.append(a["centroid"][1])
    # Sprite = base masked by union, cropped to bbox
    ys, xs = np.where(union > 128)
    if len(xs) == 0:
        return None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    rgba = np.dstack([base_arr, union])
    sprite_full = Image.fromarray(rgba, "RGBA")
    sprite = sprite_full.crop((x0, y0, x1 + 1, y1 + 1))
    return {
        "sprite": sprite,
        "union_mask": union,  # full canvas mask, for inpaint union
        "bbox_origin": (x0, y0),
        "bbox_center": ((x0 + x1) // 2, (y0 + y1) // 2),
        "atom_count": len(group),
    }


def inpaint_base(base: Image.Image, union_all: np.ndarray) -> Image.Image:
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
    binary = (union_all > 128).astype(np.uint8) * 255
    kernel = np.ones((INPAINT_DILATE_PX, INPAINT_DILATE_PX), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    bgr = cv2.cvtColor(base_arr, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(bgr, dilated, inpaintRadius=12, flags=cv2.INPAINT_TELEA)
    rgb = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb, "RGB")


# === Per-group animation behaviors ===
def swim_motion(t: float, phase_offset: float, amplitude: float = 0.012, rot_amp: float = 1.2) -> tuple[int, int, float, float]:
    """Figure-8 sway suggesting body articulation while swimming.
    drift_x = A * sin(t + phase) — side-to-side
    drift_y = (A/2) * sin(2(t + phase)) — vertical figure-8
    rotate  = rot_amp * sin(t + phase) — body twist syncs with sway
    """
    px = math.sin(t + phase_offset)
    py = math.sin(2 * (t + phase_offset))
    drift_x = int(round(amplitude * CANVAS * px))
    drift_y = int(round((amplitude * 0.5) * CANVAS * py))
    rot = rot_amp * px
    return drift_x, drift_y, 1.0, rot


def eye_motion(t: float, phase_offset: float) -> tuple[int, int, float, float]:
    """Eye: subtle look + pulse, follows body but lags slightly."""
    body_phase = t + phase_offset
    eye_phase = body_phase - 0.3  # 0.3 rad lag behind body
    drift_x = int(round(0.005 * CANVAS * math.sin(eye_phase)))
    drift_y = int(round(0.003 * CANVAS * math.sin(eye_phase + math.pi / 3)))
    scale = 1.0 + 0.03 * math.sin(2.5 * t)  # independent pulse rhythm
    return drift_x, drift_y, scale, 0.0


def fin_motion(t: float, phase_offset: float) -> tuple[int, int, float, float]:
    """Fin: wave delayed from body — follow-through."""
    body_phase = t + phase_offset
    fin_phase = body_phase - 0.5  # bigger lag — fin trails body
    drift_x = int(round(0.015 * CANVAS * math.sin(fin_phase)))
    drift_y = int(round(0.010 * CANVAS * math.sin(fin_phase + math.pi / 4)))
    rot = 2.5 * math.sin(fin_phase)  # bigger rotation for fin wave
    return drift_x, drift_y, 1.0, rot


def get_motion(group_name: str, t: float) -> tuple[int, int, float, float]:
    if group_name == "upper_body":
        return swim_motion(t, phase_offset=0.0)
    elif group_name == "lower_body":
        return swim_motion(t, phase_offset=math.pi)  # counterphase
    elif group_name == "upper_eye":
        return eye_motion(t, phase_offset=0.0)
    elif group_name == "lower_eye":
        return eye_motion(t, phase_offset=math.pi)
    elif group_name == "upper_fin":
        return fin_motion(t, phase_offset=0.0)
    elif group_name == "lower_fin":
        return fin_motion(t, phase_offset=math.pi)
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
    ap.add_argument("--version-tag", default="006_salmon_body_articulation_v002")
    args = ap.parse_args()

    atoms = load_atoms()
    groups = define_groups(atoms)
    static_count = sum(1 for a in atoms if a["label"] in STATIC_LABELS)
    print(f"Salmon: {len(atoms)} total atoms")
    print(f"  static (roe/bg, not animated): {static_count}")
    for name, group in groups.items():
        print(f"  group {name}: {len(group)} atoms")

    base = load_base_jpg()
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)

    # Build per-group layers
    print("Building per-group sprites...")
    group_data = {}
    union_all = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    for name, group_atoms in groups.items():
        gd = build_group_layer(group_atoms, base_arr)
        if gd is None:
            continue
        group_data[name] = gd
        union_all = np.maximum(union_all, gd["union_mask"])

    print("Inpainting base (removing only animated groups — roe stays visible)...")
    inpainted = inpaint_base(base, union_all)

    out_dir = INTERNAL / f"austin_{args.version_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"austin_{args.version_tag}.mp4"
    inpainted.save(out_dir / "_inpainted_base.png")

    # Build diagnostic overlay: shows group boundaries colored
    diag = base.copy()
    overlay = Image.new("RGBA", diag.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    group_colors = {
        "upper_body": (200, 60, 60, 80), "lower_body": (60, 60, 200, 80),
        "upper_eye": (255, 200, 0, 180), "lower_eye": (0, 200, 255, 180),
        "upper_fin": (255, 120, 60, 140), "lower_fin": (60, 255, 120, 140),
    }
    for name, gd in group_data.items():
        color = group_colors.get(name, (128, 128, 128, 80))
        m = (gd["union_mask"] > 128)
        mask_img = Image.fromarray((m * 255).astype(np.uint8), "L")
        color_layer = Image.new("RGBA", diag.size, color)
        overlay = Image.alpha_composite(overlay, Image.composite(color_layer, Image.new("RGBA", diag.size, (0, 0, 0, 0)), mask_img))
    diag_rgba = diag.convert("RGBA")
    diag_final = Image.alpha_composite(diag_rgba, overlay)
    diag_final.convert("RGB").save(out_dir / "_groups_diagnostic.png")

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_peak_t025.png",
              N_FRAMES // 2: "02_mid_cycle_t050.png",
              N_FRAMES - 1: "03_return_t100.png"}

    print(f"Rendering {N_FRAMES} frames at {CANVAS}x{CANVAS}...")
    for i in range(N_FRAMES):
        canvas = inpainted.copy().convert("RGBA")
        t = (i / N_FRAMES) * 2 * math.pi
        for name, gd in group_data.items():
            drift_x, drift_y, scale_mult, rot = get_motion(name, t)
            sprite = transform_layer(gd["sprite"], scale_mult, rot)
            sw, sh = sprite.size
            ow, oh = gd["sprite"].size
            paste_x = gd["bbox_origin"][0] + drift_x - (sw - ow) // 2
            paste_y = gd["bbox_origin"][1] + drift_y - (sh - oh) // 2
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
        print(f"  diagnostics:")
        print(f"    _inpainted_base.png (animated regions removed, roe stays)")
        print(f"    _groups_diagnostic.png (color-coded groups over original)")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
