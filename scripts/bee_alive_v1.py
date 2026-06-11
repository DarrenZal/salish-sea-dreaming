#!/usr/bin/env python3
"""
Bee-alive proof v001 — subtle wing shimmer + body hover.

Per operator scope 2026-05-18 AM:
  - Keep original Bee composition recognizable
  - Subtle wing shimmer / wing pulse / hover-breathing only
  - No cross-piece morph
  - Versioned output, internal only

Approach: same v003c "breathing" pattern that worked for Cosmic_Sun.
Full-color training JPG as anchor; selected atoms (wings, body) get
subtle motion overlaid as sprites.

Bee viewBox is 294×243 (non-square). Script handles this by
parameterizing viewBox dimensions separately from rendering canvas.

INTERNAL ONLY per Austin consent floor.
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
N_FRAMES = 144  # 6 sec — slow breathing cycle

# Motion params — KEEP SUBTLE per brief
WING_SHIMMER_DRIFT = 0.008  # 0.8% canvas radial sway (very subtle)
WING_SHIMMER_SCALE = 0.020  # ±2% scale pulse on wings
WING_SHIMMER_ROTATE = 1.0   # ±1° wing rotation
BODY_HOVER_AMPLITUDE = 0.004  # 0.4% canvas vertical drift (gentle hover)

# Which atoms animate (wing shimmer + body hover only — per brief)
ANIMATED_LABELS = {"wing-left", "wing-right", "body"}


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


def load_base_jpg() -> tuple[Image.Image, tuple[float, float]]:
    """Load training JPG, fit to CANVAS×CANVAS keeping aspect.
    Returns (image, (scale_x, scale_y)) where scales map viewBox→canvas px.
    """
    img = Image.open(TRAINING).convert("RGB")
    # Fit preserving aspect into CANVAS×CANVAS
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.LANCZOS)
    fitted_w, fitted_h = img.size
    # Pad to square with white
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    off_x = (CANVAS - fitted_w) // 2
    off_y = (CANVAS - fitted_h) // 2
    canvas.paste(img, (off_x, off_y))
    # viewBox→canvas scale (both X and Y use the same factor since aspect preserved)
    scale = fitted_w / VIEWBOX_W
    return canvas, (scale, scale, off_x, off_y)


def build_atom_alpha(atom: dict, canvas_w: int, canvas_h: int,
                     scale: float, off_x: int, off_y: int) -> np.ndarray:
    """Build full-canvas alpha mask for an atom (isolated PNG resized + positioned)."""
    iso = Image.open(atom["isolated_png"]).convert("L")
    # The decomp script renders each atom into its own viewBox-aligned PNG.
    # For Bee, atom PNGs likely represent the full piece bbox.
    # Resize to fitted piece size then paste at offset.
    fitted_w = int(VIEWBOX_W * scale)
    fitted_h = int(VIEWBOX_H * scale)
    iso = iso.resize((fitted_w, fitted_h), Image.LANCZOS)
    # Mask is 255 - L (dark = atom)
    iso_arr = np.asarray(iso, dtype=np.uint8)
    alpha = 255 - iso_arr
    # Place into full canvas
    full = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    full[off_y:off_y + fitted_h, off_x:off_x + fitted_w] = alpha
    return full


def build_sprite(atom: dict, base_rgba: np.ndarray, alpha_mask: np.ndarray) -> tuple[Image.Image, tuple[int, int]]:
    """Build colored sprite from base masked by atom; crop to bbox.
    Returns (sprite_image, centroid_on_canvas).
    """
    rgba = np.dstack([base_rgba, alpha_mask])
    full_layer = Image.fromarray(rgba, "RGBA")
    ys, xs = np.where(alpha_mask > 128)
    if len(xs) == 0:
        return None, (0, 0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    sprite = full_layer.crop((x0, y0, x1 + 1, y1 + 1))
    # Centroid: use mean of mask pixels (more accurate than bbox center)
    cx = int(xs.mean())
    cy = int(ys.mean())
    return sprite, (cx, cy)


def transform_sprite(sprite: Image.Image, scale_mult: float, rotate_deg: float) -> Image.Image:
    if abs(scale_mult - 1.0) > 0.001:
        w, h = sprite.size
        sprite = sprite.resize((max(1, int(round(w * scale_mult))),
                                max(1, int(round(h * scale_mult)))), Image.LANCZOS)
    if abs(rotate_deg) > 0.05:
        sprite = sprite.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    return sprite


def main():
    atoms = load_atoms()
    print(f"Loaded {len(atoms)} atoms")
    animated = [a for a in atoms if a["label"] in ANIMATED_LABELS]
    print(f"Animated: {len(animated)} atoms (labels: {sorted(set(a['label'] for a in animated))})")

    base, (scale_x, scale_y, off_x, off_y) = load_base_jpg()
    base_arr = np.asarray(base.convert("RGB"), dtype=np.uint8)
    print(f"Base: {base.size}, scale_x={scale_x:.2f}, off=({off_x},{off_y})")

    # Build sprites once
    sprites = []
    for a in animated:
        alpha = build_atom_alpha(a, CANVAS, CANVAS, scale_x, off_x, off_y)
        sprite, center = build_sprite(a, base_arr, alpha)
        if sprite is None:
            continue
        sprites.append({
            "sprite": sprite,
            "center": center,
            "label": a["label"],
            "atom_id": a["atom_id"],
        })

    # Piece center (for radial drift calculation on wings)
    piece_cx = off_x + int(VIEWBOX_W * scale_x) // 2
    piece_cy = off_y + int(VIEWBOX_H * scale_x) // 2

    out_dir = INTERNAL / "bee_alive_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "bee_alive_v001.mp4"

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_max_inhale_t025.png",
              N_FRAMES // 2: "02_mid_t050.png",
              N_FRAMES - 1: "03_return_t100.png"}

    print(f"Rendering {N_FRAMES} frames @ {CANVAS}×{CANVAS}...")
    for i in range(N_FRAMES):
        canvas = base.copy().convert("RGBA")
        t = (i / N_FRAMES) * 2 * math.pi  # one full cycle per video

        for s in sprites:
            cx, cy = s["center"]
            dx = cx - piece_cx
            dy = cy - piece_cy

            if s["label"] in ("wing-left", "wing-right"):
                # Wing shimmer: subtle scale pulse + drift outward from body + tiny rotation
                # Use radial phase (left wing 180° offset from right)
                phase = math.atan2(dy, dx)
                scale_mult = 1.0 + WING_SHIMMER_SCALE * math.sin(t + phase * 0.3)
                drift = WING_SHIMMER_DRIFT * CANVAS * math.sin(t + phase * 0.3)
                dist = math.hypot(dx, dy) or 1.0
                drift_x = int(round((dx / dist) * drift))
                drift_y = int(round((dy / dist) * drift))
                # Rotation tilts wing slightly
                rot = WING_SHIMMER_ROTATE * math.sin(1.3 * t + phase * 0.3)
            elif s["label"] == "body":
                # Body hover: gentle vertical drift only
                scale_mult = 1.0
                drift_x = 0
                drift_y = int(round(BODY_HOVER_AMPLITUDE * CANVAS * math.sin(t)))
                rot = 0.0
            else:
                continue

            # Skip overlay if at rest (motion is zero)
            if abs(drift_x) < 1 and abs(drift_y) < 1 and abs(scale_mult - 1.0) < 0.003 and abs(rot) < 0.1:
                continue

            xform = transform_sprite(s["sprite"], scale_mult, rot)
            sw, sh = xform.size
            paste_x = cx + drift_x - sw // 2
            paste_y = cy + drift_y - sh // 2
            canvas.alpha_composite(xform, (paste_x, paste_y))

        canvas.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
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
    else:
        print(f"FFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
