#!/usr/bin/env python3
"""
salmon_swim_rig_v002_pair_counterphase — yin-yang swim.

Extends v001 POC (single salmon successful per operator 2026-05-17
~3:35 PM "actually looks like it's swimming") to both salmon
counterphase: when upper sways left, lower sways right — yin-yang
chasing each other's tails.

Architecture:
  - Build upper + lower salmon masks separately (split by centroid_y)
  - Detect separate spines (eye-focal + fin-tail per half)
  - Inpaint base removes BOTH bodies
  - Per frame: cv2.remap warp each salmon with own spine field
  - Upper uses phase t; lower uses phase t + π (counterphase)
  - Composite: inpainted_base + upper_warped + lower_warped
  - Roe stays static (part of base, not removed)
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import csv
import math
import subprocess

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS = 1536
VIEWBOX = 1500
FPS = 24
N_FRAMES = 144

PIECE = "Animal_Salmon_Spawn_Eggs"
JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"

STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}

WAVE_AMPLITUDE_FRAC = 0.04
WAVELENGTH_FRAC = 1.4
CYCLES_PER_LOOP = 2


def load_atoms() -> list[dict]:
    csv_path = DECOMPOSED / PIECE / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            try:
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                    "isolated_png": DECOMPOSED / PIECE / row["isolated_png"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def load_base_jpg() -> Image.Image:
    img = Image.open(TRAINING / JPG_NAME).convert("RGB")
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


def build_half_salmon(atoms: list[dict], is_upper: bool) -> dict:
    """Return mask + head/tail centroids (canvas px) for one half-salmon."""
    center_y_vb = VIEWBOX / 2
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    head_vb = None
    tail_vb = None
    for a in atoms:
        if a["label"] in STATIC_LABELS:
            continue
        in_half = (a["centroid"][1] < center_y_vb) if is_upper else (a["centroid"][1] >= center_y_vb)
        if not in_half:
            continue
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        if a["label"] == "eye-focal-oval" and head_vb is None:
            head_vb = a["centroid"]
        elif a["label"] == "fin-tail" and tail_vb is None:
            tail_vb = a["centroid"]
    if head_vb is None or tail_vb is None:
        # PCA fallback
        ys, xs = np.where(union > 128)
        if len(xs) == 0:
            return None
        pts = np.column_stack([xs, ys]).astype(np.float32)
        mean = pts.mean(axis=0)
        cov = np.cov((pts - mean).T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        major = eigvecs[:, -1]
        proj = (pts - mean) @ major
        head_canvas = tuple(mean + major * proj.min())
        tail_canvas = tuple(mean + major * proj.max())
    else:
        scale = CANVAS / VIEWBOX
        head_canvas = (head_vb[0] * scale, head_vb[1] * scale)
        tail_canvas = (tail_vb[0] * scale, tail_vb[1] * scale)
    return {"mask": union, "head": head_canvas, "tail": tail_canvas}


def compute_remap_field(canvas_size: int, head: tuple, tail: tuple, t_phase: float) -> tuple[np.ndarray, np.ndarray]:
    H, W = canvas_size, canvas_size
    xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    hx, hy = head
    tx, ty = tail
    sx_v = tx - hx
    sy_v = ty - hy
    L = math.hypot(sx_v, sy_v) or 1.0
    sx, sy = sx_v / L, sy_v / L
    px, py = -sy, sx
    A = WAVE_AMPLITUDE_FRAC * L
    wavelength = WAVELENGTH_FRAC * L
    dx = xs - hx
    dy = ys - hy
    s = dx * sx + dy * sy
    s_norm = np.clip(s / L, 0.0, 1.0)
    phase = (2 * math.pi * s / wavelength) - t_phase
    gain = s_norm * s_norm * (3.0 - 2.0 * s_norm)
    lateral = A * gain * np.sin(phase)
    disp_x = lateral * px
    disp_y = lateral * py
    map_x = (xs - disp_x).astype(np.float32)
    map_y = (ys - disp_y).astype(np.float32)
    return map_x, map_y


def main():
    atoms = load_atoms()
    print(f"Loaded {len(atoms)} atoms")
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)

    upper = build_half_salmon(atoms, is_upper=True)
    lower = build_half_salmon(atoms, is_upper=False)
    print(f"Upper salmon: mask area {(upper['mask'] > 128).sum()} px, "
          f"head={upper['head']}, tail={upper['tail']}")
    print(f"Lower salmon: mask area {(lower['mask'] > 128).sum()} px, "
          f"head={lower['head']}, tail={lower['tail']}")

    # Combined mask for inpainting
    combined_mask = np.maximum(upper["mask"], lower["mask"])
    print("Inpainting base (removing both salmon)...")
    binary = (combined_mask > 128).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=15, flags=cv2.INPAINT_TELEA)
    inpainted = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted_img = Image.fromarray(inpainted, "RGB")

    # Build per-salmon RGBA layers (full-canvas; mask supplies alpha)
    upper_rgba = np.dstack([base_rgb, upper["mask"]])
    lower_rgba = np.dstack([base_rgb, lower["mask"]])

    out_dir = INTERNAL / "salmon_swim_rig_v002_pair_counterphase"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_swim_rig_v002_pair_counterphase.mp4"
    inpainted_img.save(out_dir / "_inpainted_base.png")

    # Diagnostic still
    diag = base.copy().convert("RGBA")
    ov = Image.new("RGBA", diag.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for color, half in [((255, 0, 0, 60), upper), ((0, 0, 255, 60), lower)]:
        m = Image.fromarray((half["mask"] > 128).astype(np.uint8) * 255, "L")
        clr = Image.new("RGBA", diag.size, color)
        ov = Image.alpha_composite(ov, Image.composite(clr, Image.new("RGBA", diag.size, (0, 0, 0, 0)), m))
    od2 = ImageDraw.Draw(ov)
    for half, line_color, head_color, tail_color in [
        (upper, (0, 200, 255, 255), (0, 255, 0, 255), (255, 255, 0, 255)),
        (lower, (255, 200, 0, 255), (0, 255, 0, 255), (255, 255, 0, 255)),
    ]:
        od2.line([half["head"], half["tail"]], fill=line_color, width=4)
        r = 16
        for pt, c in [(half["head"], head_color), (half["tail"], tail_color)]:
            od2.ellipse([pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r], outline=c, width=4)
    Image.alpha_composite(diag, ov).convert("RGB").save(out_dir / "_spines_diagnostic.png")

    stills = {0: "00_at_rest.png", N_FRAMES // 4: "01_peak.png",
              N_FRAMES // 2: "02_mid.png", N_FRAMES - 1: "03_return.png"}

    omega_total = CYCLES_PER_LOOP * 2 * math.pi

    print(f"Rendering {N_FRAMES} frames (yin-yang counterphase)...")
    for i in range(N_FRAMES):
        t_phase_upper = (i / N_FRAMES) * omega_total
        t_phase_lower = t_phase_upper + math.pi  # counterphase
        # Warp each salmon
        u_mx, u_my = compute_remap_field(CANVAS, upper["head"], upper["tail"], t_phase_upper)
        l_mx, l_my = compute_remap_field(CANVAS, lower["head"], lower["tail"], t_phase_lower)
        u_warped = cv2.remap(upper_rgba, u_mx, u_my,
                             interpolation=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_TRANSPARENT)
        l_warped = cv2.remap(lower_rgba, l_mx, l_my,
                             interpolation=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_TRANSPARENT)
        canvas = inpainted_img.copy().convert("RGBA")
        canvas.alpha_composite(Image.fromarray(u_warped, "RGBA"))
        canvas.alpha_composite(Image.fromarray(l_warped, "RGBA"))
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
        print(f"  diagnostics: _inpainted_base.png, _spines_diagnostic.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
