#!/usr/bin/env python3
"""
salmon_rectify_v005 — spine-aligned rectification (diagnostic only).

TPS approach (v003-v004) deformed body. Switch to spine-aligned
rectification: for each point along curved spine, sample perpendicular
cross-section across body mask, write samples as column in straightened
output. Preserves local cross-section width without global warp.

Per peer 2026-05-17 ~4:45 PM: diagnostic first, no animation until
rectified fish reads as fish. Target: rectified straight fish; if good,
v006 adds gentle S-curve target + swim animation.

Outputs:
  _source_spine_ribs.png      — source with ordered spine + perpendicular ribs
  _rectified_straight.png     — rectified fish on transparent
  _rectified_straight_bg.png  — rectified fish on cream BG
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
try:
    from skimage.morphology import skeletonize
except ImportError:
    raise SystemExit("Needs scikit-image")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salmon_line_swim_v1 import (load_atoms, load_base_jpg, extract_upper_salmon,
                                   pre_rotate_to_horizontal, BG_COLOR)

INTERNAL = Path(__file__).resolve().parent.parent / "track2-deterministic/morph_outputs_INTERNAL"


def order_skeleton_by_arc_length(skel: np.ndarray, head: tuple, tail: tuple) -> list[tuple[int, int]]:
    """Order skeleton pixels into a connected path from head to tail by walking
    nearest-neighbor from head.
    """
    ys, xs = np.where(skel > 0)
    points = set(zip(xs.tolist(), ys.tolist()))
    if not points:
        return []
    # Start at the skeleton point nearest to `head`
    head_arr = np.array(head)
    start = min(points, key=lambda p: np.linalg.norm(np.array(p) - head_arr))
    tail_arr = np.array(tail)

    ordered = [start]
    points.remove(start)
    while points:
        last = np.array(ordered[-1])
        # Find nearest remaining point within reasonable distance
        nearest = min(points, key=lambda p: np.linalg.norm(np.array(p) - last))
        if np.linalg.norm(np.array(nearest) - last) > 5:
            # Path is broken — bail and use what we have
            break
        ordered.append(nearest)
        points.remove(nearest)
    return ordered


def compute_arc_lengths(ordered_pts: list) -> np.ndarray:
    arcs = [0.0]
    for i in range(1, len(ordered_pts)):
        d = np.linalg.norm(np.array(ordered_pts[i]) - np.array(ordered_pts[i-1]))
        arcs.append(arcs[-1] + d)
    return np.array(arcs)


def smooth_tangents(ordered_pts: list, window: int = 9) -> np.ndarray:
    """Compute smoothed tangent at each ordered point via window-centered finite diffs."""
    n = len(ordered_pts)
    pts = np.array(ordered_pts, dtype=np.float64)
    tangents = np.zeros_like(pts)
    half = window // 2
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        if hi - lo < 2:
            tangents[i] = np.array([1.0, 0.0])
            continue
        t = pts[hi - 1] - pts[lo]
        norm = np.linalg.norm(t) or 1.0
        tangents[i] = t / norm
    return tangents


def find_perpendicular_edges(mask: np.ndarray, point: tuple, perp_unit: np.ndarray,
                             max_scan: int = 200) -> tuple[int, int]:
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
    """Rectify the salmon along its skeleton spine.

    Output: rectangular RGBA where x = arc length along spine,
    y = perpendicular distance from spine (centered).
    """
    h, w = rgba.shape[:2]
    mask = (rgba[..., 3] > 128).astype(np.uint8)
    skel = skeletonize(mask).astype(np.uint8)

    ordered = order_skeleton_by_arc_length(skel, head, tail)
    print(f"  Skeleton ordered: {len(ordered)} points")
    if len(ordered) < 20:
        raise SystemExit("Skeleton too short to rectify")

    arcs = compute_arc_lengths(ordered)
    L = arcs[-1]
    print(f"  Skeleton arc length: {L:.0f}px")

    tangents = smooth_tangents(ordered, window=15)

    # Determine max body width perpendicular to spine across all spine points
    print("  Sampling perpendicular widths...")
    widths_pos = []
    widths_neg = []
    pts_arr = np.array(ordered)
    for i in range(len(ordered)):
        perp = np.array([-tangents[i][1], tangents[i][0]])
        d_pos, d_neg = find_perpendicular_edges(mask, tuple(pts_arr[i]), perp)
        widths_pos.append(d_pos)
        widths_neg.append(d_neg)
    widths_pos = np.array(widths_pos)
    widths_neg = np.array(widths_neg)
    max_half_w = int(max(widths_pos.max(), widths_neg.max()) + 5)
    print(f"  Max half-width: {max_half_w}px")

    # Output canvas: width = arc length (1px per skeleton step ≈ 1px arc)
    out_w = int(math.ceil(L)) + 1
    out_h = 2 * max_half_w + 1
    out = np.zeros((out_h, out_w, 4), dtype=np.uint8)
    print(f"  Rectified canvas: {out_w}×{out_h}")

    # For each output column, sample perpendicular cross-section from source
    # at the skeleton point with arc length = column index
    for col in range(out_w):
        # Find skeleton point with arc length closest to `col`
        idx = np.searchsorted(arcs, col)
        if idx >= len(ordered):
            idx = len(ordered) - 1
        sk_pt = pts_arr[idx]
        perp = np.array([-tangents[idx][1], tangents[idx][0]])
        # Sample perpendicular from -max_half_w to +max_half_w
        for d in range(-max_half_w, max_half_w + 1):
            src_x = sk_pt[0] + d * perp[0]
            src_y = sk_pt[1] + d * perp[1]
            sx_i = int(round(src_x))
            sy_i = int(round(src_y))
            if 0 <= sx_i < w and 0 <= sy_i < h:
                out[d + max_half_w, col] = rgba[sy_i, sx_i]

    # Save rectified diagnostics
    Image.fromarray(out, "RGBA").save(save_dir / "_rectified_straight.png")
    bg = Image.new("RGB", (out_w, out_h), BG_COLOR)
    fish_pil = Image.fromarray(out, "RGBA")
    bg.paste(fish_pil, (0, 0), fish_pil)
    bg.save(save_dir / "_rectified_straight_bg.png")

    # Save source with spine + ribs overlay
    diag = Image.fromarray(rgba, "RGBA").convert("RGB")
    d = ImageDraw.Draw(diag)
    # Spine
    for i in range(0, len(ordered), 3):
        p = ordered[i]
        d.ellipse([p[0]-1, p[1]-1, p[0]+1, p[1]+1], fill=(0, 200, 255))
    # Ribs every 30 px arc length
    rib_indices = np.searchsorted(arcs, np.arange(0, L, 30))
    for ri in rib_indices:
        if ri >= len(ordered):
            continue
        sp = pts_arr[ri]
        perp = np.array([-tangents[ri][1], tangents[ri][0]])
        d_pos, d_neg = widths_pos[ri], widths_neg[ri]
        p_outer = (sp[0] + perp[0] * d_pos, sp[1] + perp[1] * d_pos)
        n_outer = (sp[0] - perp[0] * d_neg, sp[1] - perp[1] * d_neg)
        d.line([(p_outer[0], p_outer[1]), (n_outer[0], n_outer[1])], fill=(255, 0, 255), width=1)
    # Head/tail markers
    d.ellipse([head[0]-8, head[1]-8, head[0]+8, head[1]+8], outline=(0, 255, 0), width=3)
    d.ellipse([tail[0]-8, tail[1]-8, tail[0]+8, tail[1]+8], outline=(255, 255, 0), width=3)
    diag.save(save_dir / "_source_spine_ribs.png")
    print(f"  Diagnostics saved to {save_dir}")


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    upper = extract_upper_salmon(atoms, base_rgb)
    salmon_h = pre_rotate_to_horizontal(upper, apply_180_correction=True)

    out_dir = INTERNAL / "salmon_rectify_v005"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Rectifying via spine-aligned unroll...")
    rectify(salmon_h["rgba"], salmon_h["head"], salmon_h["tail"], out_dir)
    print("\nDONE. Inspect:")
    print(f"  {out_dir}/_source_spine_ribs.png")
    print(f"  {out_dir}/_rectified_straight.png")
    print(f"  {out_dir}/_rectified_straight_bg.png")


if __name__ == "__main__":
    main()
