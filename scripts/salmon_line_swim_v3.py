#!/usr/bin/env python3
"""
salmon_line_swim_v003 — TPS body straighten via scipy RBF.

v002 had correct orientation but body was still tucked-tail curled
(operator: "like a dog with tail tucked under its legs"). v003 fixes by
TPS-warping the body so the curved skeleton spine maps to a straight
spine.

Pipeline:
  1. Extract upper salmon (connected component) + pre-rotate per
     operator-verified D orientation (180° correction)
  2. Detect skeleton via skimage.morphology.skeletonize
  3. Order skeleton pixels by projection along head→tail direction
  4. Sample N control points along curved spine (source positions)
  5. Compute matching control points on a STRAIGHT head→tail line
     (target positions)
  6. Build scipy.interpolate.RBFInterpolator with thin-plate kernel:
     X = target positions, Y = source positions
  7. Evaluate at every pixel → map_x, map_y for cv2.remap
  8. Result: body straightened, ready for swim wave

Then apply swim wave + translate same as v002.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import math
import subprocess
import sys

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

try:
    from skimage.morphology import skeletonize
    from scipy.interpolate import RBFInterpolator
except ImportError:
    raise SystemExit("Needs scikit-image + scipy")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salmon_line_swim_v1 import (load_atoms, load_base_jpg, extract_upper_salmon,
                                   pre_rotate_to_horizontal,
                                   compute_remap_field_local,
                                   CANVAS_W, CANVAS_H, FPS, N_FRAMES,
                                   BG_COLOR, SWIM_CYCLES_PER_LOOP,
                                   TRANSLATE_VERTICAL_BOB)

INTERNAL = Path(__file__).resolve().parent.parent / "track2-deterministic/morph_outputs_INTERNAL"

N_CONTROL_POINTS = 12  # along spine
TARGET_BODY_CURVE = 0.0  # 0 = straight, +/- for slight S-curve
EXPAND_CANVAS_FACTOR = 1.25  # straightened fish is longer than curved one


def straighten_with_scipy_rbf(rgba: np.ndarray, head: tuple, tail: tuple,
                              save_diag: Path = None) -> tuple[np.ndarray, tuple, tuple]:
    """TPS warp via scipy RBFInterpolator."""
    h, w = rgba.shape[:2]
    mask = (rgba[..., 3] > 128).astype(np.uint8)
    skeleton = skeletonize(mask).astype(np.uint8)

    ys, xs = np.where(skeleton > 0)
    if len(xs) < N_CONTROL_POINTS * 2:
        print(f"  Skeleton sparse ({len(xs)} px) — skipping straighten")
        return rgba, head, tail

    head_arr = np.array(head, dtype=np.float64)
    tail_arr = np.array(tail, dtype=np.float64)
    direction = tail_arr - head_arr
    L = np.linalg.norm(direction)
    if L < 1:
        return rgba, head, tail
    direction_unit = direction / L

    # Project skeleton onto head→tail line; bin by projection
    pts = np.column_stack([xs, ys]).astype(np.float64)
    projections = (pts - head_arr) @ direction_unit

    # Sample N control points evenly along projection
    target_projs = np.linspace(0, L, N_CONTROL_POINTS)
    source_ctrl = []
    for tp in target_projs:
        window_size = max(8, L / (N_CONTROL_POINTS * 1.5))
        nearby_mask = np.abs(projections - tp) < window_size
        if nearby_mask.sum() == 0:
            continue
        nearby = pts[nearby_mask]
        median_pt = np.median(nearby, axis=0)
        source_ctrl.append(median_pt)
    source_ctrl = np.array(source_ctrl, dtype=np.float64)
    n_used = len(source_ctrl)

    # Target control points: straight head→tail line, expanded to actual
    # spine length (not chord length) — uncurled fish is longer
    spine_length_curved = 0
    for i in range(1, n_used):
        spine_length_curved += np.linalg.norm(source_ctrl[i] - source_ctrl[i-1])
    print(f"  Skeleton path length: {spine_length_curved:.0f}px vs chord: {L:.0f}px")
    print(f"  Stretch factor: {spine_length_curved / L:.2f}")

    # Stretch target: head fixed, tail extends along direction to match spine length
    target_tail = head_arr + direction_unit * spine_length_curved
    target_ctrl = np.array([
        head_arr + (target_tail - head_arr) * (i / (n_used - 1))
        for i in range(n_used)
    ], dtype=np.float64)

    # Build expanded canvas to fit straightened fish
    out_h = int(h * EXPAND_CANVAS_FACTOR)
    out_w = int(w * EXPAND_CANVAS_FACTOR)
    # Shift target so head/tail land within expanded canvas
    target_x_min = target_ctrl[:, 0].min()
    target_x_max = target_ctrl[:, 0].max()
    target_y_min = target_ctrl[:, 1].min()
    target_y_max = target_ctrl[:, 1].max()
    # Center the straightened fish in the new canvas
    shift_x = (out_w - (target_x_max - target_x_min)) / 2 - target_x_min
    shift_y = (out_h - (target_y_max - target_y_min)) / 2 - target_y_min
    target_ctrl_shifted = target_ctrl + np.array([shift_x, shift_y])

    print(f"  {n_used} control points, expanded canvas {out_w}×{out_h}")

    # Optional diagnostic
    if save_diag is not None:
        diag = Image.fromarray(rgba, "RGBA").convert("RGB")
        d = ImageDraw.Draw(diag)
        # Draw curved skeleton
        for x, y in zip(xs[::10], ys[::10]):
            d.ellipse([x-1, y-1, x+1, y+1], fill=(100, 100, 100))
        # Draw source control points (cyan)
        for sp in source_ctrl:
            d.ellipse([sp[0]-6, sp[1]-6, sp[0]+6, sp[1]+6], outline=(0, 200, 255), width=2)
        # Draw target straight line (magenta)
        for i in range(n_used - 1):
            tp0, tp1 = target_ctrl[i], target_ctrl[i+1]
            d.line([(tp0[0], tp0[1]), (tp1[0], tp1[1])], fill=(255, 0, 255), width=2)
        d.ellipse([head[0]-10, head[1]-10, head[0]+10, head[1]+10], outline=(0, 255, 0), width=3)
        d.ellipse([tail[0]-10, tail[1]-10, tail[0]+10, tail[1]+10], outline=(255, 255, 0), width=3)
        diag.save(save_diag)
        print(f"  Saved spine diagnostic → {save_diag}")

    # Build RBF interpolator: input target position, output source position (inverse map)
    rbf = RBFInterpolator(target_ctrl_shifted, source_ctrl, kernel='thin_plate_spline', smoothing=0.5)

    # Evaluate RBF at every output pixel
    out_xs, out_ys = np.meshgrid(np.arange(out_w), np.arange(out_h))
    eval_pts = np.column_stack([out_xs.ravel(), out_ys.ravel()])
    print(f"  Evaluating RBF at {len(eval_pts)} pixels...")
    src_pts = rbf(eval_pts)  # Nx2 (source x, y) for each output pixel
    map_x = src_pts[:, 0].reshape(out_h, out_w).astype(np.float32)
    map_y = src_pts[:, 1].reshape(out_h, out_w).astype(np.float32)

    # Apply remap
    warped = cv2.remap(rgba, map_x, map_y,
                       interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    # New head/tail in expanded canvas
    new_head = (target_ctrl_shifted[0, 0], target_ctrl_shifted[0, 1])
    new_tail = (target_ctrl_shifted[-1, 0], target_ctrl_shifted[-1, 1])
    return warped, new_head, new_tail


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    upper = extract_upper_salmon(atoms, base_rgb)
    salmon_h = pre_rotate_to_horizontal(upper, apply_180_correction=True)

    out_dir = INTERNAL / "salmon_line_swim_v003_tps_straightened"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("TPS straighten via scipy RBF...")
    straightened_rgba, sh_head, sh_tail = straighten_with_scipy_rbf(
        salmon_h["rgba"], salmon_h["head"], salmon_h["tail"],
        save_diag=out_dir / "_spine_control_points.png")

    # Save the straightened fish on bg for visual diagnostic
    Image.fromarray(straightened_rgba, "RGBA").convert("RGB").save(out_dir / "_straightened_fish_raw.png")
    bg_diag = Image.new("RGB", (straightened_rgba.shape[1], straightened_rgba.shape[0]), BG_COLOR)
    fish_pil = Image.fromarray(straightened_rgba, "RGBA")
    bg_diag.paste(fish_pil, (0, 0), fish_pil)
    bg_diag.save(out_dir / "_extracted_straightened.png")

    fish_h, fish_w = straightened_rgba.shape[:2]
    target_fish_w = int(CANVAS_W * 0.6)
    scale_factor = target_fish_w / fish_w
    new_w = int(fish_w * scale_factor)
    new_h = int(fish_h * scale_factor)
    fish_scaled = cv2.resize(straightened_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    head_scaled = (sh_head[0] * scale_factor, sh_head[1] * scale_factor)
    tail_scaled = (sh_tail[0] * scale_factor, sh_tail[1] * scale_factor)
    print(f"Scaled: {new_w}×{new_h}")

    out_mp4 = INTERNAL / "salmon_line_swim_v003_tps_straightened.mp4"

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

        Image.fromarray(canvas, "RGB").save(out_dir / f"frame_{i:04d}.png")
        if i in stills:
            Image.fromarray(canvas, "RGB").save(out_dir / stills[i])
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
        print(f"  Diagnostics:")
        print(f"    _spine_control_points.png — curved spine (cyan) vs straight target (magenta)")
        print(f"    _straightened_fish_raw.png — TPS-warped fish on transparent")
        print(f"    _extracted_straightened.png — on cream BG")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
