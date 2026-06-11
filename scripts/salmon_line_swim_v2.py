#!/usr/bin/env python3
"""
salmon_line_swim_v002 — orientation fix + TPS body straighten.

Per operator pick of orientation diagnostic 2026-05-17 ~4:20 PM:
  - 180° additional rotation = correct orientation (rightside up, mouth right)
  - Also wants body uncurved into S-spine, not the original yin-yang arc

v002 changes from v001:
  1. apply_180_correction=True (bakes in operator's pick)
  2. Add TPS body straighten: detect curved spine via skeletonization,
     fit polyline, warp body to follow a straighter target spine
  3. Then apply swim wave on the straightened body
  4. Same translate-across-canvas mechanic

Requires scikit-image for skeletonization (pip install scikit-image).
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps
import numpy as np
import csv
import math
import subprocess
import sys

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

# Reuse extraction + pre-rotation + warp helpers from v1 script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salmon_line_swim_v1 import (load_atoms, load_base_jpg, extract_upper_salmon,
                                   pre_rotate_to_horizontal,
                                   compute_remap_field_local,
                                   CANVAS_W, CANVAS_H, FPS, N_FRAMES,
                                   BG_COLOR, SWIM_CYCLES_PER_LOOP,
                                   TRANSLATE_VERTICAL_BOB)

INTERNAL = Path(__file__).resolve().parent.parent / "track2-deterministic/morph_outputs_INTERNAL"


def straighten_body_tps(rgba: np.ndarray, head: tuple, tail: tuple,
                        n_control_points: int = 8) -> tuple[np.ndarray, tuple, tuple]:
    """TPS-warp the body so its curved spine maps to a straight line.

    Pipeline:
      1. Detect skeleton centerline of body mask
      2. Order skeleton pixels from head to tail
      3. Sample n_control_points evenly along centerline → source points
      4. Compute straight-line target points along head→tail vector
      5. cv2 TPS shape transformer estimateTransformation + apply via remap
    """
    try:
        from skimage.morphology import skeletonize
        from scipy.spatial.distance import cdist
    except ImportError:
        print("WARNING: scikit-image/scipy missing — skipping TPS straighten")
        return rgba, head, tail

    h, w = rgba.shape[:2]
    mask = (rgba[..., 3] > 128).astype(np.uint8)
    skeleton = skeletonize(mask).astype(np.uint8)

    # Find skeleton pixels
    ys, xs = np.where(skeleton > 0)
    if len(xs) < n_control_points * 2:
        print(f"  WARNING: skeleton too sparse ({len(xs)} px) — skipping TPS")
        return rgba, head, tail

    # Order skeleton points from head to tail by projecting onto head→tail line
    pts = np.column_stack([xs, ys]).astype(np.float32)
    head_arr = np.array(head, dtype=np.float32)
    tail_arr = np.array(tail, dtype=np.float32)
    direction = tail_arr - head_arr
    length = np.linalg.norm(direction)
    if length < 1:
        return rgba, head, tail
    direction /= length
    projections = (pts - head_arr) @ direction
    # Sort skeleton points by projection (head=0, tail=length)
    order = np.argsort(projections)
    ordered_pts = pts[order]
    ordered_proj = projections[order]

    # Sample n_control_points evenly along projection range
    target_proj = np.linspace(0, length, n_control_points)
    # For each target projection, find the median skeleton point at that range
    source_ctrl = []
    for tp in target_proj:
        # Find skeleton points near this projection
        window = length / n_control_points
        mask_window = np.abs(ordered_proj - tp) < window
        if mask_window.sum() == 0:
            continue
        nearby = ordered_pts[mask_window]
        # Median point in this slice
        median_pt = np.median(nearby, axis=0)
        source_ctrl.append(median_pt)
    source_ctrl = np.array(source_ctrl, dtype=np.float32)

    # Target points: straight line from head to tail
    n_used = len(source_ctrl)
    target_ctrl = np.array([
        head_arr + direction * (i / (n_used - 1)) * length
        for i in range(n_used)
    ], dtype=np.float32)

    print(f"  TPS: {n_used} control points from skeleton ({len(xs)} skeleton px)")
    print(f"  Source ctrl (curved): head→tail spine via skeleton")
    print(f"  Target ctrl (straight): head→tail straight line")

    # Build TPS transformer
    tps = cv2.createThinPlateSplineShapeTransformer()
    matches = [cv2.DMatch(i, i, 0) for i in range(n_used)]
    # cv2 wants shape (1, N, 2)
    src_ctrl_cv = source_ctrl.reshape(1, -1, 2)
    tgt_ctrl_cv = target_ctrl.reshape(1, -1, 2)
    # Note: estimateTransformation maps target → source (inverse direction)
    # So pass target as first arg, source as second
    tps.estimateTransformation(tgt_ctrl_cv, src_ctrl_cv, matches)

    # Apply: warpImage actually warps using the inverse map (source → target)
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]
    warped_rgb = tps.warpImage(rgb)
    warped_alpha = tps.warpImage(alpha)
    warped_rgba = np.dstack([warped_rgb, warped_alpha])

    return warped_rgba, tuple(head), tuple(tail)


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    print("Extracting upper salmon...")
    upper = extract_upper_salmon(atoms, base_rgb)

    print("Pre-rotating to head-right orientation (with 180° correction)...")
    salmon_h = pre_rotate_to_horizontal(upper, apply_180_correction=True)

    # TPS body straightening requires opencv-contrib (not headless variant).
    # Defer to v003 — render v002 with orientation fix only so operator can
    # confirm direction is correct before iterating on body shape.
    print("Skipping TPS straighten — using original body curve (needs opencv-contrib for TPS)")
    straightened_rgba = salmon_h["rgba"]
    sh_head = salmon_h["head"]
    sh_tail = salmon_h["tail"]

    fish_h, fish_w = straightened_rgba.shape[:2]
    target_fish_w = int(CANVAS_W * 0.6)
    scale_factor = target_fish_w / fish_w
    new_w = int(fish_w * scale_factor)
    new_h = int(fish_h * scale_factor)
    fish_scaled = cv2.resize(straightened_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    head_scaled = (sh_head[0] * scale_factor, sh_head[1] * scale_factor)
    tail_scaled = (sh_tail[0] * scale_factor, sh_tail[1] * scale_factor)
    print(f"Scaled: {new_w}×{new_h}, head→{head_scaled}, tail→{tail_scaled}")

    out_dir = INTERNAL / "salmon_line_swim_v002_oriented_straightened"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_line_swim_v002_oriented_straightened.mp4"

    # Diagnostic: save extracted+straightened fish on bg
    fish_diag = Image.fromarray(fish_scaled, "RGBA")
    bg_diag = Image.new("RGB", fish_diag.size, BG_COLOR)
    bg_diag.paste(fish_diag, (0, 0), fish_diag)
    bg_diag.save(out_dir / "_extracted_oriented_straightened.png")

    start_x = -new_w
    end_x = CANVAS_W
    total_dx = end_x - start_x
    center_y = (CANVAS_H - new_h) // 2

    stills = {0: "00_t000.png", N_FRAMES // 4: "01_t025.png",
              N_FRAMES // 2: "02_t050.png", 3*N_FRAMES // 4: "03_t075.png"}

    omega_swim = SWIM_CYCLES_PER_LOOP * 2 * math.pi

    print(f"Rendering {N_FRAMES} frames {CANVAS_W}×{CANVAS_H}...")
    for i in range(N_FRAMES):
        t_norm = i / N_FRAMES
        swim_phase = t_norm * omega_swim

        map_x, map_y = compute_remap_field_local(new_w, new_h, head_scaled, tail_scaled, swim_phase)
        warped_fish = cv2.remap(fish_scaled, map_x, map_y,
                                interpolation=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        canvas = np.full((CANVAS_H, CANVAS_W, 3), BG_COLOR, dtype=np.uint8)
        tx_pos = int(start_x + t_norm * total_dx)
        ty_offset = int(TRANSLATE_VERTICAL_BOB * CANVAS_H * math.sin(t_norm * 2 * math.pi * 2))
        ty_pos = center_y + ty_offset

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
        print(f"  _extracted_oriented_straightened.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
