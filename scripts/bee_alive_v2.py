#!/usr/bin/env python3
"""
Bee-alive v002 — wing hinge flutter + body hover.

Per operator brief 2026-05-18: change MECHANIC not amplitude.
  - Wings rotate around plausible hinge points (where wing meets body)
  - Fast flutter (~8 Hz)
  - Motion blur via multi-sub-frame blending
  - Whole-body subtle vertical hover bob (body/head/legs/antenna/stripe)
  - NO independent atom drift on body parts

Wings grouped as one assembly per side. Inner edge = hinge point.

v001 preserved as "decomposition proof" — this is the show-artifact attempt.
"""
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import csv
import math
import subprocess

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — python3.11")

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed/Animal_Insect_Bee"
TRAINING = ROOT / "austin-v2-ingest/training/Animal_Insect_Bee.jpg"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

VIEWBOX_W = 294.0
VIEWBOX_H = 243.0
CANVAS = 1024
FPS = 24
N_FRAMES = 96  # 4 sec — short loop, flutter doesn't need duration

# Flutter
WING_FLUTTER_HZ = 8.0   # 8 wing-beats per second
WING_FLUTTER_ANGLE = 14  # ±14° rotation around hinge
WING_MOTION_BLUR_SUBFRAMES = 3  # blend 3 wing positions per output frame

# Body hover
BODY_HOVER_AMPLITUDE_PX = 6  # ±6 px vertical translation
BODY_HOVER_HZ = 1.2  # 1.2 hover-cycles per second (gentle)

# Antenna twitch (optional small motion)
ANTENNA_TWITCH_HZ = 0.5
ANTENNA_TWITCH_ANGLE = 4  # ±4°

WING_LABELS = {"wing-left", "wing-right"}
BODY_LABELS = {"body", "head", "leg", "stripe", "formline"}  # hover together
EYE_LABEL = "eye"  # static
ANTENNA_LABEL = "antenna"


def load_atoms() -> list[dict]:
    atoms = []
    with (DECOMP / "atom_metadata.csv").open() as f:
        for row in csv.DictReader(f):
            try:
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "bbox": (float(row["bbox_x"]), float(row["bbox_y"]),
                             float(row["bbox_w"]), float(row["bbox_h"])),
                    "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                    "isolated_png": DECOMP / row["isolated_png"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def load_base_jpg() -> tuple[Image.Image, float, int, int]:
    img = Image.open(TRAINING).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.LANCZOS)
    fitted_w, fitted_h = img.size
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    off_x = (CANVAS - fitted_w) // 2
    off_y = (CANVAS - fitted_h) // 2
    canvas.paste(img, (off_x, off_y))
    scale = fitted_w / VIEWBOX_W
    return canvas, scale, off_x, off_y


def atom_alpha_full(atom: dict, scale: float, off_x: int, off_y: int) -> np.ndarray:
    iso = Image.open(atom["isolated_png"]).convert("L")
    fitted_w = int(VIEWBOX_W * scale)
    fitted_h = int(VIEWBOX_H * scale)
    iso = iso.resize((fitted_w, fitted_h), Image.LANCZOS)
    iso_arr = np.asarray(iso, dtype=np.uint8)
    alpha = 255 - iso_arr
    full = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    full[off_y:off_y + fitted_h, off_x:off_x + fitted_w] = alpha
    return full


def union_mask(atoms: list[dict], scale: float, off_x: int, off_y: int) -> np.ndarray:
    """Union mask for a group of atoms (e.g., all wing-left)."""
    u = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    for a in atoms:
        u = np.maximum(u, atom_alpha_full(a, scale, off_x, off_y))
    return u


def compute_hinge_point(wing_mask: np.ndarray, body_center: tuple) -> tuple:
    """For a wing mask, hinge = mask pixel closest to body_center."""
    ys, xs = np.where(wing_mask > 128)
    if len(xs) == 0:
        return body_center
    cx_body, cy_body = body_center
    distances = np.hypot(xs - cx_body, ys - cy_body)
    idx = np.argmin(distances)
    return (int(xs[idx]), int(ys[idx]))


def rotate_layer_around_point(layer: Image.Image, angle_deg: float, pivot: tuple) -> Image.Image:
    """Rotate a full-canvas RGBA layer around a specific pivot point."""
    # PIL rotate has center parameter; expand=False keeps canvas size
    return layer.rotate(angle_deg, resample=Image.BICUBIC, center=pivot, expand=False, fillcolor=(0, 0, 0, 0))


def translate_layer(layer: Image.Image, dx: int, dy: int) -> Image.Image:
    """Translate by (dx, dy)."""
    if dx == 0 and dy == 0:
        return layer
    return layer.transform(layer.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy),
                           resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))


def main():
    atoms = load_atoms()
    base, scale, off_x, off_y = load_base_jpg()
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    # Group atoms by category
    wing_left = [a for a in atoms if a["label"] == "wing-left"]
    wing_right = [a for a in atoms if a["label"] == "wing-right"]
    body_group = [a for a in atoms if a["label"] in BODY_LABELS]
    antenna_group = [a for a in atoms if a["label"] == ANTENNA_LABEL]
    print(f"Groups: wing-left={len(wing_left)}, wing-right={len(wing_right)}, "
          f"body-group={len(body_group)}, antenna={len(antenna_group)}")

    # Build union masks per group
    wing_left_mask = union_mask(wing_left, scale, off_x, off_y)
    wing_right_mask = union_mask(wing_right, scale, off_x, off_y)
    body_mask = union_mask(body_group, scale, off_x, off_y)
    antenna_mask = union_mask(antenna_group, scale, off_x, off_y)

    # Build group layers (RGBA: RGB from base, alpha from mask)
    def build_layer(mask: np.ndarray) -> Image.Image:
        rgba = np.dstack([base_arr, mask])
        return Image.fromarray(rgba, "RGBA")

    wing_left_layer = build_layer(wing_left_mask)
    wing_right_layer = build_layer(wing_right_mask)
    body_layer = build_layer(body_mask)
    antenna_layer = build_layer(antenna_mask)

    # Body center (centroid of body mask)
    body_ys, body_xs = np.where(body_mask > 128)
    if len(body_xs) == 0:
        body_center = (CANVAS // 2, CANVAS // 2)
    else:
        body_center = (int(body_xs.mean()), int(body_ys.mean()))
    print(f"Body center: {body_center}")

    # Hinge points
    wing_left_hinge = compute_hinge_point(wing_left_mask, body_center)
    wing_right_hinge = compute_hinge_point(wing_right_mask, body_center)
    antenna_hinge = compute_hinge_point(antenna_mask, body_center)
    print(f"Hinges: wing_left={wing_left_hinge}, wing_right={wing_right_hinge}, antenna={antenna_hinge}")

    # Inpaint base to remove animated atoms (so they don't show in rest position)
    print("Inpainting base...")
    all_animated = np.maximum(wing_left_mask, wing_right_mask)
    all_animated = np.maximum(all_animated, body_mask)
    all_animated = np.maximum(all_animated, antenna_mask)
    binary = (all_animated > 128).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    bgr = cv2.cvtColor(base_arr, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=10, flags=cv2.INPAINT_TELEA)
    inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted = Image.fromarray(inpainted_rgb, "RGB")

    out_dir = INTERNAL / "bee_alive_v002_wing_flutter"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "bee_alive_v002_wing_flutter.mp4"

    inpainted.save(out_dir / "_inpainted_base.png")

    # Diagnostic: show hinges on base
    from PIL import ImageDraw
    diag = base.copy().convert("RGBA")
    dd = ImageDraw.Draw(diag)
    r = 18
    for hinge, color, label in [
        (wing_left_hinge, (100, 160, 220), "WL hinge"),
        (wing_right_hinge, (220, 100, 160), "WR hinge"),
        (antenna_hinge, (160, 100, 200), "antenna hinge"),
        (body_center, (180, 100, 60), "body center"),
    ]:
        dd.ellipse([hinge[0]-r, hinge[1]-r, hinge[0]+r, hinge[1]+r], outline=color, width=4)
        dd.text((hinge[0]+r+5, hinge[1]-8), label, fill=color)
    diag.convert("RGB").save(out_dir / "_hinges_diagnostic.png")

    stills = {0: "00_t000.png", N_FRAMES // 4: "01_t025.png",
              N_FRAMES // 2: "02_t050.png", 3*N_FRAMES // 4: "03_t075.png"}

    print(f"Rendering {N_FRAMES} frames with motion blur...")
    for i in range(N_FRAMES):
        t = i / FPS  # seconds

        # Body hover offset (vertical only)
        body_dy = int(round(BODY_HOVER_AMPLITUDE_PX * math.sin(2 * math.pi * BODY_HOVER_HZ * t)))

        # Wing angles for motion blur: 3 sub-positions per output frame
        wing_angles = []
        for sub in range(WING_MOTION_BLUR_SUBFRAMES):
            sub_t = t + sub / (FPS * WING_MOTION_BLUR_SUBFRAMES * 3)  # tiny phase offset
            angle = WING_FLUTTER_ANGLE * math.sin(2 * math.pi * WING_FLUTTER_HZ * sub_t)
            wing_angles.append(angle)

        # Antenna twitch (single position, no blur — too small)
        antenna_angle = ANTENNA_TWITCH_ANGLE * math.sin(2 * math.pi * ANTENNA_TWITCH_HZ * t)

        # Start with inpainted base + translated body
        canvas = inpainted.copy().convert("RGBA")
        body_translated = translate_layer(body_layer, 0, body_dy)
        canvas.alpha_composite(body_translated)

        # Antenna: rotate around its hinge + translate with body
        antenna_rotated = rotate_layer_around_point(antenna_layer, antenna_angle, antenna_hinge)
        antenna_translated = translate_layer(antenna_rotated, 0, body_dy)
        canvas.alpha_composite(antenna_translated)

        # Wings with motion blur: average alpha across N sub-positions
        # Use mirrored angle for left wing (so they flap together visually)
        wl_composite = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        wr_composite = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        for angle in wing_angles:
            # Right wing: positive angle = wings up; left wing: negate
            wr = rotate_layer_around_point(wing_right_layer, -angle, wing_right_hinge)
            wl = rotate_layer_around_point(wing_left_layer, angle, wing_left_hinge)
            # Translate with body
            wr = translate_layer(wr, 0, body_dy)
            wl = translate_layer(wl, 0, body_dy)
            # Reduce alpha for blending (each sub-position contributes 1/N)
            wr_arr = np.asarray(wr, dtype=np.uint8).copy()
            wl_arr = np.asarray(wl, dtype=np.uint8).copy()
            wr_arr[..., 3] = (wr_arr[..., 3].astype(np.float32) / WING_MOTION_BLUR_SUBFRAMES).astype(np.uint8)
            wl_arr[..., 3] = (wl_arr[..., 3].astype(np.float32) / WING_MOTION_BLUR_SUBFRAMES).astype(np.uint8)
            wr_composite.alpha_composite(Image.fromarray(wr_arr, "RGBA"))
            wl_composite.alpha_composite(Image.fromarray(wl_arr, "RGBA"))

        canvas.alpha_composite(wr_composite)
        canvas.alpha_composite(wl_composite)

        canvas.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
        if i in stills:
            canvas.convert("RGB").save(out_dir / stills[i])
        if (i + 1) % 24 == 0:
            print(f"  frame {i + 1}/{N_FRAMES}")

    cmd = ["ffmpeg", "-y", "-framerate", str(FPS),
           "-i", str(out_dir / "frame_%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
           str(out_mp4)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n→ {out_mp4}")
        print(f"  diagnostic: {out_dir}/_hinges_diagnostic.png")
    else:
        print(f"FFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
