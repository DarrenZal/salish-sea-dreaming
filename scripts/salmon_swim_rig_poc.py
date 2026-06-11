#!/usr/bin/env python3
"""
salmon_swim_rig_poc_v001 — continuous body deformation.

Peer 2026-05-17 ~3:25 PM: independent cut-out sprite motion cannot
become convincing swimming. Salmon needs continuous deformation of a
whole fish body — skeleton/lattice/TPS warp. Tail follows mid follows
head as ONE body, no disconnected pieces.

This script: upper salmon only (POC). Treats the whole upper salmon as
one continuous mask; applies cv2.remap with a traveling-wave
displacement field perpendicular to the body's longitudinal spine. Head
anchored (gain=0), tail gets max lateral sway (gain=1), wave travels
from head to tail.

Lower salmon stays static for this POC. Roe stays static. Once one
fish swims believably, mirror/counterphase for the pair.

Acceptance per peer:
  - No disconnected tail
  - No independent cut-out chunks
  - Outline/perimeter bends smoothly
  - Internal shapes warp WITH body (because body deforms, not because
    each atom slides)

Requires cv2 (python3.11 with opencv-python-headless).

INTERNAL ONLY per Austin consent floor.
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

JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"
PIECE = "Animal_Salmon_Spawn_Eggs"

# Salmon body mask = all non-roe, non-bg atoms in the UPPER half.
# For POC: define "upper half" as centroid_y < 750 (viewbox center).
STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}

# Wave params (tuneable)
WAVE_AMPLITUDE_FRAC = 0.04    # 4% of body length as max lateral displacement
WAVELENGTH_FRAC = 1.4         # one wavelength = 1.4x body length (long, gentle undulation)
CYCLES_PER_LOOP = 2           # full sine cycles per 6-second loop


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


def build_upper_salmon_mask(atoms: list[dict]) -> np.ndarray:
    """Union mask of every upper-half non-roe-non-bg atom = whole upper salmon."""
    center_y_vb = VIEWBOX / 2
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    head_candidates = []  # eye-focal atoms
    tail_candidates = []  # fin-tail atoms
    for a in atoms:
        if a["label"] in STATIC_LABELS:
            continue
        if a["centroid"][1] >= center_y_vb:
            continue  # lower half — POC ignores
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        if a["label"] == "eye-focal-oval":
            head_candidates.append(a["centroid"])
        if a["label"] == "fin-tail":
            tail_candidates.append(a["centroid"])
    return union, head_candidates, tail_candidates


def find_spine(mask: np.ndarray, head_vb_candidates: list, tail_vb_candidates: list) -> tuple[tuple[float, float], tuple[float, float]]:
    """Determine head and tail endpoints (canvas px) for spine axis.

    Prefer eye-focal-oval = head, fin-tail = tail. If missing, fall back
    to PCA on the mask pixels.
    """
    scale = CANVAS / VIEWBOX
    if head_vb_candidates and tail_vb_candidates:
        head_vb = head_vb_candidates[0]
        tail_vb = tail_vb_candidates[0]
        return (head_vb[0] * scale, head_vb[1] * scale), (tail_vb[0] * scale, tail_vb[1] * scale)
    # PCA fallback
    ys, xs = np.where(mask > 128)
    pts = np.column_stack([xs, ys]).astype(np.float32)
    mean = pts.mean(axis=0)
    centered = pts - mean
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    major = eigvecs[:, -1]  # largest eigvec
    # Project points onto major axis
    proj = centered @ major
    head_pt = mean + major * proj.min()
    tail_pt = mean + major * proj.max()
    return tuple(head_pt), tuple(tail_pt)


def compute_remap_field(canvas_size: int, mask: np.ndarray,
                        head: tuple[float, float], tail: tuple[float, float],
                        t_phase: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (map_x, map_y) float32 displacement fields for cv2.remap.

    Traveling wave: lateral displacement perpendicular to spine,
    gain ramps from 0 at head to 1 at tail, phase travels head→tail.
    """
    H, W = canvas_size, canvas_size
    xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

    hx, hy = head
    tx, ty = tail
    spine_vec_x = tx - hx
    spine_vec_y = ty - hy
    L = math.hypot(spine_vec_x, spine_vec_y) or 1.0
    sx, sy = spine_vec_x / L, spine_vec_y / L  # spine unit vector
    px, py = -sy, sx  # perpendicular unit (90° CCW)

    A = WAVE_AMPLITUDE_FRAC * L
    wavelength = WAVELENGTH_FRAC * L

    # For each pixel: projection onto spine s ∈ [0..L]
    dx = xs - hx
    dy = ys - hy
    s = dx * sx + dy * sy
    s_norm = np.clip(s / L, 0.0, 1.0)

    # Lateral displacement
    # phase = (2π s/λ) - ωt  → wave moves toward +s direction (head→tail)
    phase = (2 * math.pi * s / wavelength) - t_phase
    # Gain: 0 at head, smoothly rising to 1 at tail. Use smoothstep for ease-in.
    gain = s_norm * s_norm * (3.0 - 2.0 * s_norm)
    lateral = A * gain * np.sin(phase)

    # Displacement vector in image space (perpendicular to spine)
    disp_x = lateral * px
    disp_y = lateral * py

    # For inverse mapping (cv2.remap samples source[map_y, map_x]):
    # output pixel (x,y) should show source pixel (x - disp_x, y - disp_y)
    # so the body appears shifted by +disp at output position.
    map_x = (xs - disp_x).astype(np.float32)
    map_y = (ys - disp_y).astype(np.float32)
    return map_x, map_y


def main():
    atoms = load_atoms()
    print(f"Loaded {len(atoms)} atoms")

    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)

    mask, head_vb, tail_vb = build_upper_salmon_mask(atoms)
    print(f"Upper salmon mask area: {(mask > 128).sum()} px")
    print(f"  Head candidates (eye-focal): {len(head_vb)}")
    print(f"  Tail candidates (fin-tail): {len(tail_vb)}")
    head_canvas, tail_canvas = find_spine(mask, head_vb, tail_vb)
    print(f"  Spine: head={head_canvas}, tail={tail_canvas}")

    # Inpaint base to remove the entire upper salmon
    print("Inpainting base (removing whole upper salmon)...")
    binary = (mask > 128).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations=1)
    bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=15, flags=cv2.INPAINT_TELEA)
    inpainted = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted_img = Image.fromarray(inpainted, "RGB")

    # Build upper salmon RGBA layer (colored + masked, full-canvas size for clean remap)
    salmon_rgba = np.dstack([base_rgb, mask])  # H×W×4

    out_dir = INTERNAL / "salmon_swim_rig_poc_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_swim_rig_poc_v001.mp4"
    inpainted_img.save(out_dir / "_inpainted_base.png")

    # Diagnostic still: show spine line + body mask overlay
    diag = base.copy().convert("RGBA")
    ov = Image.new("RGBA", diag.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    mask_overlay = Image.fromarray((mask > 128).astype(np.uint8) * 255, "L")
    red_layer = Image.new("RGBA", diag.size, (255, 0, 0, 60))
    ov = Image.alpha_composite(ov, Image.composite(red_layer, Image.new("RGBA", diag.size, (0, 0, 0, 0)), mask_overlay))
    od2 = ImageDraw.Draw(ov)
    od2.line([head_canvas, tail_canvas], fill=(0, 0, 255, 255), width=4)
    r = 16
    od2.ellipse([head_canvas[0]-r, head_canvas[1]-r, head_canvas[0]+r, head_canvas[1]+r], outline=(0, 255, 0, 255), width=4)
    od2.ellipse([tail_canvas[0]-r, tail_canvas[1]-r, tail_canvas[0]+r, tail_canvas[1]+r], outline=(255, 255, 0, 255), width=4)
    diag_final = Image.alpha_composite(diag, ov)
    diag_final.convert("RGB").save(out_dir / "_spine_diagnostic.png")

    stills = {0: "00_at_rest_t000.png",
              N_FRAMES // 4: "01_peak_t025.png",
              N_FRAMES // 2: "02_mid_t050.png",
              N_FRAMES - 1: "03_return_t100.png"}

    omega_total = CYCLES_PER_LOOP * 2 * math.pi  # total radians per loop

    print(f"Rendering {N_FRAMES} frames with cv2.remap warp...")
    for i in range(N_FRAMES):
        t_phase = (i / N_FRAMES) * omega_total
        map_x, map_y = compute_remap_field(CANVAS, mask, head_canvas, tail_canvas, t_phase)
        # Warp the salmon RGBA layer
        warped = cv2.remap(salmon_rgba, map_x, map_y,
                           interpolation=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_TRANSPARENT)
        # Composite onto inpainted base
        warped_img = Image.fromarray(warped, "RGBA")
        canvas = inpainted_img.copy().convert("RGBA")
        canvas.alpha_composite(warped_img)
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
        print(f"  diagnostics: _inpainted_base.png, _spine_diagnostic.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
