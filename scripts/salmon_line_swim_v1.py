#!/usr/bin/env python3
"""
salmon_line_swim_v001 — A.1 isolated salmon swims left-to-right.

Scope per peer 2026-05-17 ~4:05 PM:
  - One salmon (upper), extracted from Austin's piece
  - Placed on neutral cream background (NOT the original piece — too
    many inpaint artifacts when fish moves away from rest position)
  - Pre-rotated so head points right (direction of motion)
  - Swim wave applied (existing rig)
  - Translates horizontally across canvas, exits right, re-enters left
    (loops cleanly)

Goal: prove the rig can make ONE fish feel alive when isolated from
the original composition's geometric constraints.

v002 would add: TPS body-straightening (gently uncurve the natural
yin-yang arc into a straighter S-spine before applying swim).

Fixes from circle-chase v001:
  - BORDER_CONSTANT instead of BORDER_TRANSPARENT to kill rainbow
    rectangle artifacts from cv2.warpAffine
  - Pre-zero output buffer where needed
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

CANVAS_W = 1920
CANVAS_H = 1080
VIEWBOX = 1500
FPS = 24
N_FRAMES = 192  # 8 sec

PIECE = "Animal_Salmon_Spawn_Eggs"
JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"
SOURCE_CANVAS = 1536  # the canvas we extract the salmon at
STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}

# Background — pulled from the original piece's cream/ochre tone
BG_COLOR = (234, 216, 184)  # warm ochre/cream, approximate Austin tone

# Swim wave
WAVE_AMPLITUDE_FRAC = 0.06  # bumped from 0.04 — more visible on isolated fish
WAVELENGTH_FRAC = 1.2
SWIM_CYCLES_PER_LOOP = 3

# Translation across canvas
# Fish moves from off-canvas-left to off-canvas-right over one loop
TRANSLATE_VERTICAL_BOB = 0.015  # 1.5% gentle bobbing as it swims


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
    img = ImageOps.contain(img, (SOURCE_CANVAS, SOURCE_CANVAS), Image.LANCZOS)
    if img.size != (SOURCE_CANVAS, SOURCE_CANVAS):
        canvas = Image.new("RGB", (SOURCE_CANVAS, SOURCE_CANVAS), (255, 255, 255))
        x = (SOURCE_CANVAS - img.width) // 2
        y = (SOURCE_CANVAS - img.height) // 2
        canvas.paste(img, (x, y))
        img = canvas
    return img


def build_atom_alpha(atom: dict) -> np.ndarray:
    iso = Image.open(atom["isolated_png"]).convert("L").resize((SOURCE_CANVAS, SOURCE_CANVAS), Image.LANCZOS)
    return 255 - np.asarray(iso, dtype=np.uint8)


def extract_upper_salmon(atoms: list[dict], base_rgb: np.ndarray) -> dict:
    """Same connected-components segmentation as v003+. Return upper fish only."""
    union = np.zeros((SOURCE_CANVAS, SOURCE_CANVAS), dtype=np.uint8)
    eye_pos = []
    fin_pos = []
    scale = SOURCE_CANVAS / VIEWBOX
    for a in atoms:
        if a["label"] in STATIC_LABELS:
            continue
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        cxc = a["centroid"][0] * scale
        cyc = a["centroid"][1] * scale
        if a["label"] == "eye-focal-oval":
            eye_pos.append((cxc, cyc))
        elif a["label"] == "fin-tail":
            fin_pos.append((cxc, cyc))

    binary = (union > 128).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    comps = [(i, stats[i, cv2.CC_STAT_AREA], centroids[i][1]) for i in range(1, n_labels)]
    comps.sort(key=lambda x: -x[1])
    top_two = sorted(comps[:2], key=lambda x: x[2])  # cy ascending
    upper_lbl = top_two[0][0]
    upper_mask = ((labels == upper_lbl).astype(np.uint8)) * 255
    upper_mask = cv2.dilate(upper_mask, np.ones((5, 5), np.uint8), iterations=1)

    eyes_in = [p for p in eye_pos if upper_mask[int(p[1]), int(p[0])] > 0]
    fins_in = [p for p in fin_pos if upper_mask[int(p[1]), int(p[0])] > 0]
    if eyes_in and fins_in:
        head = eyes_in[0]
        tail = fins_in[0]
    else:
        # PCA fallback: head = farthest-from-mean along major axis
        ys_pca, xs_pca = np.where(upper_mask > 0)
        pts = np.column_stack([xs_pca, ys_pca]).astype(np.float32)
        mean = pts.mean(axis=0)
        cov = np.cov((pts - mean).T)
        _, eigvecs = np.linalg.eigh(cov)
        major = eigvecs[:, -1]
        proj = (pts - mean) @ major
        # head = the eye-focal end if available, else proj.max() end
        if eyes_in:
            # Tail is PCA endpoint farther from head
            head = eyes_in[0]
            head_proj = (np.array(head) - mean) @ major
            tail_proj = proj.min() if head_proj > 0 else proj.max()
            tail = tuple(mean + major * tail_proj)
        elif fins_in:
            tail = fins_in[0]
            tail_proj_v = (np.array(tail) - mean) @ major
            head_proj = proj.min() if tail_proj_v > 0 else proj.max()
            head = tuple(mean + major * head_proj)
        else:
            head = tuple(mean + major * proj.max())
            tail = tuple(mean + major * proj.min())
        print(f"  PCA fallback used: eyes_in={len(eyes_in)} fins_in={len(fins_in)}")

    # Crop to bbox
    ys, xs = np.where(upper_mask > 0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    cropped_rgba = np.dstack([base_rgb, upper_mask])[y0:y1+1, x0:x1+1]
    head_local = (head[0] - x0, head[1] - y0) if head else None
    tail_local = (tail[0] - x0, tail[1] - y0) if tail else None
    return {
        "rgba": cropped_rgba,
        "head": head_local,
        "tail": tail_local,
        "bbox_origin": (x0, y0),
    }


def pre_rotate_to_horizontal(salmon: dict, apply_180_correction: bool = True) -> dict:
    """Rotate the cropped salmon so head points to +x (right).

    Operator-verified 2026-05-17 PM: PCA-detected "head" is actually the
    salmon's anatomical TAIL end (PCA can't tell head from tail). After
    rotation, the fish faces wrong direction + upside-down. The empirical
    fix is a 180° additional rotation (= flip-both). apply_180_correction
    defaults True; pass False if running on a piece where PCA picks the
    right end naturally.
    """
    head, tail = salmon["head"], salmon["tail"]
    nat_angle = math.atan2(head[1] - tail[1], head[0] - tail[0])
    rotation_deg = math.degrees(-nat_angle)
    if apply_180_correction:
        rotation_deg += 180.0
        head, tail = tail, head  # swap so post-rotation "head" position is on +x side
    cropped = salmon["rgba"]
    h, w = cropped.shape[:2]
    cx, cy = w / 2, h / 2
    M = cv2.getRotationMatrix2D((cx, cy), rotation_deg, 1.0)
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)
    M[0, 2] += (new_w / 2) - cx
    M[1, 2] += (new_h / 2) - cy
    rotated = cv2.warpAffine(cropped, M, (new_w, new_h),
                             flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(0, 0, 0, 0))
    def tx(pt):
        p = np.array([pt[0], pt[1], 1.0])
        new = M @ p
        return (new[0], new[1])
    new_head = tx(head)
    new_tail = tx(tail)
    print(f"  Pre-rotate: {rotation_deg:.1f}° (180° correction={apply_180_correction}), new size {new_w}×{new_h}")
    print(f"  Head: → {new_head}, Tail: → {new_tail}")
    return {
        "rgba": rotated,
        "head": new_head,
        "tail": new_tail,
    }


def compute_remap_field_local(canvas_w: int, canvas_h: int, head: tuple, tail: tuple, t_phase: float) -> tuple[np.ndarray, np.ndarray]:
    """Same warp math as before, sized to local canvas (not square SOURCE_CANVAS)."""
    xs, ys = np.meshgrid(np.arange(canvas_w, dtype=np.float32), np.arange(canvas_h, dtype=np.float32))
    hx, hy = head
    tx, ty = tail
    sx_v, sy_v = tx - hx, ty - hy
    L = math.hypot(sx_v, sy_v) or 1.0
    sx, sy = sx_v / L, sy_v / L
    px, py = -sy, sx
    A = WAVE_AMPLITUDE_FRAC * L
    wavelength = WAVELENGTH_FRAC * L
    dx, dy = xs - hx, ys - hy
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
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    print("Extracting upper salmon (connected components)...")
    upper = extract_upper_salmon(atoms, base_rgb)
    print(f"  Cropped to {upper['rgba'].shape[1]}×{upper['rgba'].shape[0]}")
    print(f"  Head/tail in cropped frame: {upper['head']} / {upper['tail']}")

    print("Pre-rotating to head-points-right orientation...")
    salmon_h = pre_rotate_to_horizontal(upper)

    fish_h, fish_w = salmon_h["rgba"].shape[:2]
    print(f"Horizontal salmon canvas: {fish_w}×{fish_h}")

    # Scale fish to fit comfortably on output canvas
    # Target fish width = 60% of canvas width
    target_fish_w = int(CANVAS_W * 0.6)
    scale_factor = target_fish_w / fish_w
    new_w = int(fish_w * scale_factor)
    new_h = int(fish_h * scale_factor)
    fish_scaled_rgba = cv2.resize(salmon_h["rgba"], (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    head_scaled = (salmon_h["head"][0] * scale_factor, salmon_h["head"][1] * scale_factor)
    tail_scaled = (salmon_h["tail"][0] * scale_factor, salmon_h["tail"][1] * scale_factor)
    print(f"Scaled fish: {new_w}×{new_h} (scale {scale_factor:.2f})")
    print(f"  Head scaled: {head_scaled}, Tail scaled: {tail_scaled}")

    out_dir = INTERNAL / "salmon_line_swim_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_line_swim_v001.mp4"

    # Save isolated salmon as diagnostic
    fish_diag = Image.fromarray(fish_scaled_rgba, "RGBA")
    fish_on_bg = Image.new("RGB", fish_diag.size, BG_COLOR)
    fish_on_bg.paste(fish_diag, (0, 0), fish_diag)
    fish_on_bg.save(out_dir / "_extracted_salmon_horizontal.png")

    # Loop math: fish moves from start_x (off left) to end_x (off right)
    # over N_FRAMES. Fish width = new_w. Canvas width = CANVAS_W.
    start_x = -new_w  # entirely off left
    end_x = CANVAS_W  # entirely off right
    total_dx = end_x - start_x
    # Center vertically with gentle bob
    center_y = (CANVAS_H - new_h) // 2

    stills = {0: "00_t000.png", N_FRAMES // 4: "01_t025.png",
              N_FRAMES // 2: "02_t050.png", 3*N_FRAMES // 4: "03_t075.png"}

    omega_swim = SWIM_CYCLES_PER_LOOP * 2 * math.pi

    print(f"Rendering {N_FRAMES} frames {CANVAS_W}×{CANVAS_H}...")
    for i in range(N_FRAMES):
        t_norm = i / N_FRAMES
        swim_phase = t_norm * omega_swim

        # Apply swim wave to scaled fish
        map_x, map_y = compute_remap_field_local(new_w, new_h, head_scaled, tail_scaled, swim_phase)
        warped_fish = cv2.remap(fish_scaled_rgba, map_x, map_y,
                                interpolation=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        # Place on full canvas
        canvas = np.full((CANVAS_H, CANVAS_W, 3), BG_COLOR, dtype=np.uint8)
        # Translation x: linear from start_x to end_x
        tx_pos = int(start_x + t_norm * total_dx)
        # Gentle vertical bob
        ty_offset = int(TRANSLATE_VERTICAL_BOB * CANVAS_H * math.sin(t_norm * 2 * math.pi * 2))
        ty_pos = center_y + ty_offset

        # Composite warped fish onto canvas
        # Clip to canvas bounds
        src_x0 = max(0, -tx_pos)
        src_y0 = max(0, -ty_pos)
        src_x1 = min(new_w, CANVAS_W - tx_pos)
        src_y1 = min(new_h, CANVAS_H - ty_pos)
        dst_x0 = max(0, tx_pos)
        dst_y0 = max(0, ty_pos)
        if src_x1 > src_x0 and src_y1 > src_y0:
            fish_slice = warped_fish[src_y0:src_y1, src_x0:src_x1]
            alpha = fish_slice[..., 3:4].astype(np.float32) / 255.0
            rgb = fish_slice[..., :3].astype(np.float32)
            bg_slice = canvas[dst_y0:dst_y0 + (src_y1 - src_y0),
                              dst_x0:dst_x0 + (src_x1 - src_x0)].astype(np.float32)
            blended = (rgb * alpha + bg_slice * (1 - alpha)).astype(np.uint8)
            canvas[dst_y0:dst_y0 + (src_y1 - src_y0),
                   dst_x0:dst_x0 + (src_x1 - src_x0)] = blended

        out_img = Image.fromarray(canvas, "RGB")
        out_img.save(out_dir / f"frame_{i:04d}.png")
        if i in stills:
            out_img.save(out_dir / stills[i])
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
        print(f"  _extracted_salmon_horizontal.png — fish on neutral bg, head-right")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
