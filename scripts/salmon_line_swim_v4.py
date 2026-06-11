#!/usr/bin/env python3
"""
salmon_line_swim_v004 — TPS straighten with body-width anchors.

v003 over-straightened: only constrained the spine, so body width
collapsed perpendicular to spine = "thin snake" instead of fish.

v004 adds: for each spine control point, also sample body width
(distance from spine to mask edge perpendicular to spine direction)
and add LEFT + RIGHT control points at that distance. Target control
points place those perp anchors at SAME perp distance from straight
spine. Result: warp preserves body cross-section while straightening
spine.
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
    raise SystemExit("Needs cv2")
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

N_SPINE_CONTROL = 10
EXPAND_CANVAS_FACTOR = 1.3
RBF_SMOOTHING = 0.5


def find_perpendicular_edges(mask: np.ndarray, point: tuple, perp_unit: tuple,
                             max_scan: int = 200) -> tuple[float, float]:
    """From point, walk in +perp and -perp directions until hitting mask edge.
    Returns (dist_positive_perp, dist_negative_perp).
    """
    h, w = mask.shape
    cx, cy = point
    px, py = perp_unit

    def scan(sign):
        for d in range(1, max_scan):
            x = int(round(cx + sign * d * px))
            y = int(round(cy + sign * d * py))
            if x < 0 or x >= w or y < 0 or y >= h:
                return d
            if mask[y, x] == 0:
                return d
        return max_scan

    return scan(1), scan(-1)


def straighten_with_width_anchors(rgba: np.ndarray, head: tuple, tail: tuple,
                                  save_diag: Path = None) -> tuple[np.ndarray, tuple, tuple]:
    h, w = rgba.shape[:2]
    mask = (rgba[..., 3] > 128).astype(np.uint8)
    skeleton = skeletonize(mask).astype(np.uint8)

    ys, xs = np.where(skeleton > 0)
    if len(xs) < N_SPINE_CONTROL * 2:
        return rgba, head, tail

    head_arr = np.array(head, dtype=np.float64)
    tail_arr = np.array(tail, dtype=np.float64)
    direction = tail_arr - head_arr
    L = np.linalg.norm(direction)
    direction_unit = direction / L

    # Project + sample spine points
    pts = np.column_stack([xs, ys]).astype(np.float64)
    projections = (pts - head_arr) @ direction_unit
    target_projs = np.linspace(0, L, N_SPINE_CONTROL)
    spine_ctrl = []
    for tp in target_projs:
        window_size = max(8, L / (N_SPINE_CONTROL * 1.5))
        nearby_mask = np.abs(projections - tp) < window_size
        if nearby_mask.sum() == 0:
            continue
        nearby = pts[nearby_mask]
        spine_ctrl.append(np.median(nearby, axis=0))
    spine_ctrl = np.array(spine_ctrl, dtype=np.float64)
    n_spine = len(spine_ctrl)

    # Compute local tangent at each spine point via finite differences
    tangents = []
    for i in range(n_spine):
        if i == 0:
            t = spine_ctrl[1] - spine_ctrl[0]
        elif i == n_spine - 1:
            t = spine_ctrl[-1] - spine_ctrl[-2]
        else:
            t = spine_ctrl[i+1] - spine_ctrl[i-1]
        t_norm = t / (np.linalg.norm(t) or 1)
        tangents.append(t_norm)
    tangents = np.array(tangents)

    # Find body width at each spine point (perpendicular scan)
    widths = []
    for i, sp in enumerate(spine_ctrl):
        perp = (-tangents[i][1], tangents[i][0])
        d_pos, d_neg = find_perpendicular_edges(mask, tuple(sp), perp)
        widths.append((d_pos, d_neg))
    widths = np.array(widths)

    # Build source control points: spine + 2 perp anchors per spine point
    source_ctrl = []
    for i, sp in enumerate(spine_ctrl):
        perp = np.array([-tangents[i][1], tangents[i][0]])
        d_pos, d_neg = widths[i]
        # Slightly inset (80% of edge distance) so anchors are on body, not exactly at edge
        source_ctrl.append(sp)
        if d_pos > 5:
            source_ctrl.append(sp + perp * d_pos * 0.8)
        if d_neg > 5:
            source_ctrl.append(sp - perp * d_neg * 0.8)
    source_ctrl = np.array(source_ctrl, dtype=np.float64)

    # Compute curved spine length (for stretching target)
    spine_length_curved = sum(
        np.linalg.norm(spine_ctrl[i] - spine_ctrl[i-1]) for i in range(1, n_spine)
    )

    # Target spine: straight along original head→tail direction, stretched to spine length
    target_tail = head_arr + direction_unit * spine_length_curved
    target_spine = np.array([
        head_arr + (target_tail - head_arr) * (i / (n_spine - 1))
        for i in range(n_spine)
    ], dtype=np.float64)

    # Target perpendiculars: all perpendicular to straight direction
    target_perp = np.array([-direction_unit[1], direction_unit[0]])
    target_ctrl = []
    for i, tsp in enumerate(target_spine):
        d_pos, d_neg = widths[i]
        target_ctrl.append(tsp)
        if d_pos > 5:
            target_ctrl.append(tsp + target_perp * d_pos * 0.8)
        if d_neg > 5:
            target_ctrl.append(tsp - target_perp * d_neg * 0.8)
    target_ctrl = np.array(target_ctrl, dtype=np.float64)
    assert len(source_ctrl) == len(target_ctrl), "control point mismatch"

    print(f"  {n_spine} spine + {len(source_ctrl) - n_spine} perp anchors = {len(source_ctrl)} total")
    print(f"  Curved length {spine_length_curved:.0f}px vs chord {L:.0f}px (stretch {spine_length_curved/L:.2f}x)")

    # Build expanded canvas
    out_h = int(h * EXPAND_CANVAS_FACTOR)
    out_w = int(w * EXPAND_CANVAS_FACTOR)
    tx_min, tx_max = target_ctrl[:, 0].min(), target_ctrl[:, 0].max()
    ty_min, ty_max = target_ctrl[:, 1].min(), target_ctrl[:, 1].max()
    shift_x = (out_w - (tx_max - tx_min)) / 2 - tx_min
    shift_y = (out_h - (ty_max - ty_min)) / 2 - ty_min
    target_ctrl_shifted = target_ctrl + np.array([shift_x, shift_y])

    if save_diag is not None:
        diag = Image.fromarray(rgba, "RGBA").convert("RGB")
        d = ImageDraw.Draw(diag)
        for x, y in zip(xs[::8], ys[::8]):
            d.ellipse([x-1, y-1, x+1, y+1], fill=(120, 120, 120))
        for i, sp in enumerate(spine_ctrl):
            d.ellipse([sp[0]-5, sp[1]-5, sp[0]+5, sp[1]+5], outline=(0, 200, 255), width=2)
        # Show width anchors
        for sc in source_ctrl[n_spine:]:
            d.ellipse([sc[0]-3, sc[1]-3, sc[0]+3, sc[1]+3], outline=(255, 100, 0), width=1)
        # Straight target
        d.line([(target_spine[0][0], target_spine[0][1]),
                (target_spine[-1][0], target_spine[-1][1])], fill=(255, 0, 255), width=2)
        for tsp in target_spine:
            d.ellipse([tsp[0]-4, tsp[1]-4, tsp[0]+4, tsp[1]+4], outline=(255, 0, 255), width=1)
        diag.save(save_diag)
        print(f"  Saved spine+width diagnostic → {save_diag}")

    rbf = RBFInterpolator(target_ctrl_shifted, source_ctrl,
                          kernel='thin_plate_spline', smoothing=RBF_SMOOTHING)
    out_xs, out_ys = np.meshgrid(np.arange(out_w), np.arange(out_h))
    eval_pts = np.column_stack([out_xs.ravel(), out_ys.ravel()])
    print(f"  Evaluating RBF at {len(eval_pts)} pixels...")
    src_pts = rbf(eval_pts)
    map_x = src_pts[:, 0].reshape(out_h, out_w).astype(np.float32)
    map_y = src_pts[:, 1].reshape(out_h, out_w).astype(np.float32)
    warped = cv2.remap(rgba, map_x, map_y,
                       interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    new_head = tuple(target_ctrl_shifted[0])
    new_tail = tuple(target_ctrl_shifted[(n_spine - 1) * (len(source_ctrl) // n_spine)
                                          if False else 0])  # fallback below
    # Better: new_head = target_spine[0] shifted; new_tail = target_spine[-1] shifted
    new_head = (target_spine[0][0] + shift_x, target_spine[0][1] + shift_y)
    new_tail = (target_spine[-1][0] + shift_x, target_spine[-1][1] + shift_y)
    return warped, new_head, new_tail


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    upper = extract_upper_salmon(atoms, base_rgb)
    salmon_h = pre_rotate_to_horizontal(upper, apply_180_correction=True)

    out_dir = INTERNAL / "salmon_line_swim_v004_width_anchored_tps"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("TPS straighten with body-width anchors...")
    straightened_rgba, sh_head, sh_tail = straighten_with_width_anchors(
        salmon_h["rgba"], salmon_h["head"], salmon_h["tail"],
        save_diag=out_dir / "_spine_width_diagnostic.png")

    bg = Image.new("RGB", (straightened_rgba.shape[1], straightened_rgba.shape[0]), BG_COLOR)
    fish_pil = Image.fromarray(straightened_rgba, "RGBA")
    bg.paste(fish_pil, (0, 0), fish_pil)
    bg.save(out_dir / "_extracted_straightened.png")

    fish_h, fish_w = straightened_rgba.shape[:2]
    target_fish_w = int(CANVAS_W * 0.6)
    scale_factor = target_fish_w / fish_w
    new_w = int(fish_w * scale_factor)
    new_h = int(fish_h * scale_factor)
    fish_scaled = cv2.resize(straightened_rgba, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    head_scaled = (sh_head[0] * scale_factor, sh_head[1] * scale_factor)
    tail_scaled = (sh_tail[0] * scale_factor, sh_tail[1] * scale_factor)

    out_mp4 = INTERNAL / "salmon_line_swim_v004_width_anchored_tps.mp4"

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
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
