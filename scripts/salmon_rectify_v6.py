#!/usr/bin/env python3
"""
salmon_rectify_v006 — column-median centerline (no skeleton branches).

v005 used skimage skeletonize → branched skeleton → nearest-neighbor
walker wandered into eye/fin branches, producing a "spine" that went
through the face. Operator confirmed: spine started in middle of back,
took sharp turn, went through head/mouth instead of along body axis.

v006 fix: after pre-rotation puts body roughly horizontal, compute
centerline as column-median — for each x column in the mask's bbox,
find median y of body pixels in that column. Gives a smooth single
centerline that follows actual body axis (no branches).

Plus orientation fixes:
  - Rectified output has head on RIGHT (matches input rotation)
  - Operator's preferred orientation D maintained
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import math
import sys

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salmon_line_swim_v1 import (load_atoms, load_base_jpg, extract_upper_salmon,
                                   pre_rotate_to_horizontal, BG_COLOR)

INTERNAL = Path(__file__).resolve().parent.parent / "track2-deterministic/morph_outputs_INTERNAL"

CENTERLINE_SMOOTH_WINDOW = 31  # moving average to smooth centerline
SAMPLE_STEP_PX = 1  # column step for output


def column_median_centerline(mask: np.ndarray, head: tuple, tail: tuple) -> list[tuple]:
    """Compute centerline as column-by-column median y of mask pixels.

    Returns list of (x, y_smoothed) in head-to-tail order. Since after
    pre-rotation head is on right (x=high), we walk RIGHT to LEFT so the
    ordered centerline starts at head.
    """
    h, w = mask.shape
    xs_with_mask = np.where(mask.any(axis=0))[0]
    if len(xs_with_mask) == 0:
        return []
    x_min, x_max = xs_with_mask.min(), xs_with_mask.max()

    # For each column, median y
    centers = []
    for x in range(x_min, x_max + 1):
        col_mask = mask[:, x]
        ys = np.where(col_mask > 0)[0]
        if len(ys) > 0:
            centers.append((x, float(np.median(ys))))

    if not centers:
        return []

    # Smooth y with moving average
    pts = np.array(centers, dtype=np.float64)
    smooth_y = pts[:, 1].copy()
    half = CENTERLINE_SMOOTH_WINDOW // 2
    smoothed = np.zeros_like(smooth_y)
    for i in range(len(smooth_y)):
        lo, hi = max(0, i - half), min(len(smooth_y), i + half + 1)
        smoothed[i] = smooth_y[lo:hi].mean()
    smoothed_pts = list(zip(pts[:, 0].tolist(), smoothed.tolist()))

    # Order from head to tail: head is on whichever side has HIGHER x
    # (operator-verified orientation D puts head right after pre-rotate)
    head_x = head[0]
    tail_x = tail[0]
    if head_x > tail_x:
        # Head on right → reverse list to start from right
        smoothed_pts = list(reversed(smoothed_pts))
    return smoothed_pts


def compute_tangents(pts: list, window: int = 11) -> np.ndarray:
    n = len(pts)
    pts_arr = np.array(pts, dtype=np.float64)
    tangents = np.zeros_like(pts_arr)
    half = window // 2
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        t = pts_arr[hi - 1] - pts_arr[lo]
        norm = np.linalg.norm(t) or 1.0
        tangents[i] = t / norm
    return tangents


def find_perpendicular_edges(mask: np.ndarray, point: tuple, perp_unit: np.ndarray,
                             max_scan: int = 250) -> tuple[int, int]:
    h, w = mask.shape
    cx, cy = point
    px, py = perp_unit

    def scan(sign):
        for d in range(1, max_scan):
            x = int(round(cx + sign * d * px))
            y = int(round(cy + sign * d * py))
            if x < 0 or x >= w or y < 0 or y >= h:
                return d - 1
            if mask[y, x] == 0:
                return d - 1
        return max_scan

    return scan(1), scan(-1)


def rectify(rgba: np.ndarray, head: tuple, tail: tuple, save_dir: Path):
    h, w = rgba.shape[:2]
    mask = (rgba[..., 3] > 128).astype(np.uint8)

    # Column-median centerline (head→tail order)
    centerline = column_median_centerline(mask, head, tail)
    if len(centerline) < 20:
        raise SystemExit("Centerline too short")
    print(f"  Centerline points: {len(centerline)}")

    # Arc-lengths along centerline
    pts_arr = np.array(centerline, dtype=np.float64)
    arcs = [0.0]
    for i in range(1, len(centerline)):
        arcs.append(arcs[-1] + np.linalg.norm(pts_arr[i] - pts_arr[i-1]))
    arcs = np.array(arcs)
    L = arcs[-1]
    print(f"  Centerline arc length: {L:.0f}px")

    tangents = compute_tangents(centerline, window=15)

    # Sample perpendicular widths along centerline
    widths_pos = []
    widths_neg = []
    for i in range(len(centerline)):
        perp = np.array([-tangents[i][1], tangents[i][0]])
        d_pos, d_neg = find_perpendicular_edges(mask, tuple(pts_arr[i]), perp)
        widths_pos.append(d_pos)
        widths_neg.append(d_neg)
    widths_pos = np.array(widths_pos)
    widths_neg = np.array(widths_neg)
    max_half_w = int(max(widths_pos.max(), widths_neg.max()) + 5)
    print(f"  Max half-width: {max_half_w}px")

    # Rectified output canvas
    out_w = int(math.ceil(L)) + 1
    out_h = 2 * max_half_w + 1
    out = np.zeros((out_h, out_w, 4), dtype=np.uint8)
    print(f"  Rectified canvas: {out_w}×{out_h}")

    # Convention: rectified output has head on the LEFT (column 0 = head end of centerline)
    # We'll flip horizontally at the end so head ends up on RIGHT to match operator-D orientation.
    for col in range(out_w):
        # Skeleton index at arc-length = col
        idx = np.searchsorted(arcs, col)
        if idx >= len(centerline):
            idx = len(centerline) - 1
        sk_pt = pts_arr[idx]
        perp = np.array([-tangents[idx][1], tangents[idx][0]])
        for d in range(-max_half_w, max_half_w + 1):
            src_x = sk_pt[0] + d * perp[0]
            src_y = sk_pt[1] + d * perp[1]
            sx_i = int(round(src_x))
            sy_i = int(round(src_y))
            if 0 <= sx_i < w and 0 <= sy_i < h:
                out[d + max_half_w, col] = rgba[sy_i, sx_i]

    # Flip horizontally so head ends on RIGHT
    out_head_right = cv2.flip(out, 1)

    Image.fromarray(out_head_right, "RGBA").save(save_dir / "_rectified_straight.png")
    bg = Image.new("RGB", (out_w, out_h), BG_COLOR)
    fish_pil = Image.fromarray(out_head_right, "RGBA")
    bg.paste(fish_pil, (0, 0), fish_pil)
    bg.save(save_dir / "_rectified_straight_bg.png")

    # Source with centerline + ribs overlay
    diag = Image.fromarray(rgba, "RGBA").convert("RGB")
    d = ImageDraw.Draw(diag)
    for i in range(0, len(centerline), 5):
        p = pts_arr[i]
        d.ellipse([p[0]-2, p[1]-2, p[0]+2, p[1]+2], fill=(0, 200, 255))
    # Ribs every 40 px arc
    rib_arcs = np.arange(0, L, 40)
    for ra in rib_arcs:
        ri = np.searchsorted(arcs, ra)
        if ri >= len(centerline):
            continue
        sp = pts_arr[ri]
        perp = np.array([-tangents[ri][1], tangents[ri][0]])
        d_pos, d_neg = widths_pos[ri], widths_neg[ri]
        p_outer = (sp[0] + perp[0] * d_pos, sp[1] + perp[1] * d_pos)
        n_outer = (sp[0] - perp[0] * d_neg, sp[1] - perp[1] * d_neg)
        d.line([(p_outer[0], p_outer[1]), (n_outer[0], n_outer[1])], fill=(255, 0, 255), width=2)
    d.ellipse([head[0]-10, head[1]-10, head[0]+10, head[1]+10], outline=(0, 255, 0), width=4)
    d.ellipse([tail[0]-10, tail[1]-10, tail[0]+10, tail[1]+10], outline=(255, 255, 0), width=4)
    diag.save(save_dir / "_source_spine_ribs.png")
    print(f"  Diagnostics saved")


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)

    upper = extract_upper_salmon(atoms, base_rgb)
    salmon_h = pre_rotate_to_horizontal(upper, apply_180_correction=True)

    out_dir = INTERNAL / "salmon_rectify_v006_column_median"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Rectify via column-median centerline...")
    rectify(salmon_h["rgba"], salmon_h["head"], salmon_h["tail"], out_dir)
    print(f"\nInspect: {out_dir}/")


if __name__ == "__main__":
    main()
