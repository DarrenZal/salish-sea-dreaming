#!/usr/bin/env python3.11
"""
Source-grounded water phrase layout stills v002.

PNG-only correction packet. No animation, no MP4s. These stills tighten the
primitive geometry rules before any motion pass: crescents cup the origin,
trigons are not generic triangles, gaps are intentional/closed, and marks stay
inside water bands unless explicitly documented as edge foam/spray.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT, draw_poly_alpha


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/source_grounded_water_phrase_layout_correction_v002_2026-05-19"
W = 1920
H = 1080

BLACK = (0, 0, 0)
WHITE = (246, 247, 244)
SOFT_WHITE = (230, 244, 248)
PALE_WATER = (151, 206, 231)
MID_WATER = (82, 140, 191)
DEEP_BLUE = (45, 77, 111)
ROCK = (159, 170, 170)
RED = (255, 28, 28)
GUIDE = (74, 80, 82)


def canvas(color: tuple[int, int, int] = BLACK) -> np.ndarray:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    arr[:] = (color[2], color[1], color[0])
    return arr


def quadratic_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    samples: int,
    *,
    include_endpoint: bool = False,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    stop = samples + 1 if include_endpoint else samples
    for i in range(stop):
        t = i / max(1, samples)
        omt = 1.0 - t
        x = omt * omt * p0[0] + 2.0 * omt * t * p1[0] + t * t * p2[0]
        y = omt * omt * p0[1] + 2.0 * omt * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def trigon_v2_points(samples: int = 28) -> np.ndarray:
    """Pointed trigon with a crescent-like rear/base, not a generic triangle.

    Local +x is the point/release direction. The rear face is a short bowed
    base, giving the trigon a specific glyph-like body instead of three straight
    triangle edges.
    """

    rear_top = (-0.60, -0.52)
    rear_bottom = (-0.60, 0.52)
    tip = (0.88, 0.0)
    upper_ctrl = (-0.06, -0.54)
    lower_ctrl = (-0.06, 0.54)
    rear_ctrl = (-0.68, 0.0)
    pts: list[tuple[float, float]] = []
    pts.extend(quadratic_curve(rear_top, upper_ctrl, tip, samples))
    pts.extend(quadratic_curve(tip, lower_ctrl, rear_bottom, samples))
    pts.extend(quadratic_curve(rear_bottom, rear_ctrl, rear_top, samples, include_endpoint=True))
    return np.array(pts, dtype=np.float32)


TRIGON_V2_BASE = trigon_v2_points()


def transform_points(
    base: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    flip_y: bool = False,
) -> np.ndarray:
    pts = base.copy()
    if flip_y:
        pts[:, 1] *= -1.0
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    out = pts @ rot.T
    out[:, 0] += center[0]
    out[:, 1] += center[1]
    return out


def _restore_outside_clip(frame: np.ndarray, before: np.ndarray, clip_mask: np.ndarray | None) -> None:
    if clip_mask is None:
        return
    changed = cv2.absdiff(frame, before).max(axis=2) > 0
    outside = changed & (clip_mask == 0)
    frame[outside] = before[outside]


def draw_poly(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    draw_poly_alpha(frame, pts.astype(np.float32), rgb, alpha=alpha, outline_rgb=rgb, outline_alpha=0.0, outline_thickness=0)
    if before is not None:
        _restore_outside_clip(frame, before, clip_mask)


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
    flip_y: bool = False,
    clip_mask: np.ndarray | None = None,
) -> None:
    draw_poly(frame, transform_points(CRESCENT_BASE, center, sx, sy, angle, flip_y=flip_y), rgb, alpha=alpha, clip_mask=clip_mask)


def draw_crescent_cupping(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    # The base crescent's concave side faces local -x. Rotate local -x toward
    # the circle/origin so the crescent reads as holding the origin.
    angle_to_origin = math.atan2(origin[1] - center[1], origin[0] - center[0])
    draw_crescent(frame, center, sx, sy, angle_to_origin - math.pi, rgb=rgb, alpha=alpha, clip_mask=clip_mask)


def draw_trigon_v2(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    draw_poly(frame, transform_points(TRIGON_V2_BASE, center, sx, sy, angle), rgb, alpha=alpha, clip_mask=clip_mask)


def draw_circle(
    frame: np.ndarray,
    center: tuple[int, int],
    radius: int,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    overlay = frame.copy()
    cv2.circle(overlay, center, radius, (rgb[2], rgb[1], rgb[0]), -1, lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)
    if before is not None:
        _restore_outside_clip(frame, before, clip_mask)


def draw_ellipse(
    frame: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    overlay = frame.copy()
    cv2.ellipse(overlay, center, axes, math.degrees(angle), 0, 360, (rgb[2], rgb[1], rgb[0]), -1, lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)
    if before is not None:
        _restore_outside_clip(frame, before, clip_mask)


def draw_circle_ring(
    frame: np.ndarray,
    center: tuple[int, int],
    radius: int,
    thickness: int,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
) -> None:
    overlay = frame.copy()
    cv2.circle(overlay, center, radius, (rgb[2], rgb[1], rgb[0]), thickness, lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def dotted_arrow(frame: np.ndarray, p0: tuple[int, int], p1: tuple[int, int], *, rgb: tuple[int, int, int] = RED) -> None:
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length <= 1:
        return
    ux, uy = dx / length, dy / length
    step = 26
    dash = 14
    for s in np.arange(0, length - 42, step):
        a = (int(x0 + ux * s), int(y0 + uy * s))
        b = (int(x0 + ux * min(length - 42, s + dash)), int(y0 + uy * min(length - 42, s + dash)))
        cv2.line(frame, a, b, (rgb[2], rgb[1], rgb[0]), 4, cv2.LINE_AA)
    tip = np.array([x1, y1], dtype=np.float32)
    left = tip - np.array([ux, uy]) * 44 + np.array([-uy, ux]) * 24
    right = tip - np.array([ux, uy]) * 44 - np.array([-uy, ux]) * 24
    cv2.fillPoly(frame, [np.round(np.vstack([tip, left, right])).astype(np.int32)], (rgb[2], rgb[1], rgb[0]), lineType=cv2.LINE_AA)


def curve_points(points: list[tuple[float, float]], samples: int = 120) -> list[tuple[float, float]]:
    pts = np.array(points, dtype=np.float32)
    out: list[tuple[float, float]] = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        seg_n = max(4, samples // max(1, len(pts) - 1))
        for j in range(seg_n):
            t = j / seg_n
            t2 = t * t
            t3 = t2 * t
            q = 0.5 * (
                (2 * p1)
                + (-p0 + p2) * t
                + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
            )
            out.append((float(q[0]), float(q[1])))
    out.append((float(pts[-1, 0]), float(pts[-1, 1])))
    return out


def tangent_at(path: list[tuple[float, float]], idx: int) -> float:
    i0 = max(0, idx - 2)
    i1 = min(len(path) - 1, idx + 2)
    return math.atan2(path[i1][1] - path[i0][1], path[i1][0] - path[i0][0])


def path_point(path: list[tuple[float, float]], s: float) -> tuple[tuple[float, float], float]:
    idx = int(max(0, min(len(path) - 1, round(s * (len(path) - 1)))))
    return path[idx], tangent_at(path, idx)


def water_band_mask(frame: np.ndarray, outer: list[tuple[int, int]], cuts: list[list[tuple[int, int]]] | None = None) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(outer, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    for cut in cuts or []:
        cv2.fillPoly(mask, [np.array(cut, dtype=np.int32)], 0, lineType=cv2.LINE_AA)
    frame[mask > 0] = (PALE_WATER[2], PALE_WATER[1], PALE_WATER[0])
    return mask


def draw_phrase_on_path(
    frame: np.ndarray,
    path: list[tuple[float, float]],
    s0: float,
    scale: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
    circle_radius_mul: float = 0.18,
    gap_fill: bool = False,
) -> None:
    offsets = [0.0, 0.055, 0.112, 0.168]
    origin, _ = path_point(path, s0)
    c1, _ = path_point(path, s0 + offsets[1])
    c2, _ = path_point(path, s0 + offsets[2])
    tri, tri_angle = path_point(path, s0 + offsets[3])

    draw_circle(frame, (int(origin[0]), int(origin[1])), max(4, int(scale * circle_radius_mul)), rgb, alpha=alpha, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c1, origin, scale * 0.60, scale * 0.43, rgb=rgb, alpha=alpha * 0.92, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c2, origin, scale * 0.70, scale * 0.48, rgb=rgb, alpha=alpha * 0.84, clip_mask=clip_mask)
    if gap_fill:
        # Intentional pressure/void fill where a crescent-to-trigon gap would
        # otherwise read as an accidental missing circle.
        mid = ((c2[0] + tri[0]) * 0.5, (c2[1] + tri[1]) * 0.5)
        draw_ellipse(frame, (int(mid[0]), int(mid[1])), (max(5, int(scale * 0.10)), max(3, int(scale * 0.055))), tri_angle, rgb, alpha=alpha * 0.46, clip_mask=clip_mask)
    draw_trigon_v2(frame, tri, scale * 0.49, scale * 0.50, tri_angle, rgb=rgb, alpha=alpha * 0.82, clip_mask=clip_mask)


def draw_rock(frame: np.ndarray, points: list[tuple[int, int]], mask: np.ndarray | None = None) -> None:
    poly = np.array(points, dtype=np.int32)
    cv2.fillPoly(frame, [poly], (ROCK[2], ROCK[1], ROCK[0]), lineType=cv2.LINE_AA)
    cv2.polylines(frame, [poly], True, (255, 255, 255), 5, lineType=cv2.LINE_AA)
    if mask is not None:
        cv2.fillPoly(mask, [poly], 0, lineType=cv2.LINE_AA)


def study_01_vancity() -> np.ndarray:
    frame = canvas(BLACK)
    center_y = H // 2 + 20
    circle = (1390, center_y)

    # Source-grounded, slide-like: large black-ground construction, with all
    # crescents explicitly cupping the right-side circle/focal origin.
    draw_circle_ring(frame, circle, 118, 36, WHITE)
    draw_crescent_cupping(frame, (1190, center_y), circle, 170, 220, rgb=WHITE)
    draw_crescent_cupping(frame, (990, center_y), circle, 175, 230, rgb=WHITE)
    # The v002 trigon has a bowed base and a single leftward point; spacing is
    # closed so the crescent/trigon transition does not form a missing circle.
    draw_trigon_v2(frame, (785, center_y), 350, 96, math.pi, rgb=WHITE)
    draw_crescent_cupping(frame, (560, center_y), circle, 255, 340, rgb=WHITE)
    dotted_arrow(frame, circle, (520, center_y), rgb=RED)
    dotted_arrow(frame, (1390, center_y - 120), (760, center_y - 120), rgb=RED)
    dotted_arrow(frame, (1390, center_y + 120), (760, center_y + 120), rgb=RED)
    return frame


def study_02_line_following() -> np.ndarray:
    frame = canvas(BLACK)
    path = curve_points([(190, 735), (420, 425), (720, 455), (1020, 295), (1395, 410), (1710, 285)], samples=190)
    cv2.polylines(frame, [np.round(np.array(path)).astype(np.int32)], False, (GUIDE[2], GUIDE[1], GUIDE[0]), 4, cv2.LINE_AA)
    for s, scale, alpha in [(0.03, 118, 1.0), (0.30, 106, 0.90), (0.58, 98, 0.82), (0.78, 88, 0.72)]:
        draw_phrase_on_path(frame, path, s, scale, rgb=WHITE, alpha=alpha, gap_fill=False)
    return frame


def study_03_river_band() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    band = [
        (0, 620), (305, 620), (350, 655), (425, 658), (500, 605), (1010, 600), (1090, 640),
        (1220, 640), (1275, 600), (1920, 600), (1920, 805), (1240, 805), (1170, 775),
        (1030, 775), (960, 820), (0, 820)
    ]
    cuts = [
        [(330, 620), (425, 620), (450, 715), (375, 720)],
        [(760, 720), (900, 720), (930, 805), (710, 805)],
    ]
    mask = water_band_mask(frame, band, cuts)
    path = curve_points([(210, 760), (510, 710), (835, 708), (1120, 744), (1460, 665), (1780, 666)], samples=170)
    # All marks are clipped to the water mask; no edge spray exceptions in v002.
    draw_phrase_on_path(frame, path, 0.04, 70, rgb=SOFT_WHITE, alpha=0.82, clip_mask=mask)
    draw_phrase_on_path(frame, path, 0.43, 62, rgb=SOFT_WHITE, alpha=0.48, clip_mask=mask)
    draw_phrase_on_path(frame, path, 0.73, 78, rgb=SOFT_WHITE, alpha=0.55, clip_mask=mask)
    draw_rock(frame, [(760, 565), (835, 560), (865, 630), (780, 635)])
    draw_rock(frame, [(1540, 785), (1625, 730), (1710, 820), (1515, 820)])
    return frame


def study_04_waterfall_vertical() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    cv2.fillPoly(frame, [np.array([(0, 0), (760, 0), (610, 175), (360, 305), (160, 475), (0, 610)], dtype=np.int32)], (MID_WATER[2], MID_WATER[1], MID_WATER[0]), lineType=cv2.LINE_AA)
    fall = [(790, 150), (990, 150), (1065, 880), (670, 880)]
    mask = water_band_mask(frame, fall)

    origin = (890.0, 260.0)
    draw_circle(frame, (int(origin[0]), int(origin[1])), 34, SOFT_WHITE, alpha=0.85, clip_mask=mask)
    draw_crescent_cupping(frame, (895, 388), origin, 92, 66, rgb=SOFT_WHITE, alpha=0.88, clip_mask=mask)
    draw_crescent_cupping(frame, (882, 532), origin, 104, 72, rgb=SOFT_WHITE, alpha=0.78, clip_mask=mask)
    draw_trigon_v2(frame, (902, 690), 86, 120, math.pi / 2, rgb=SOFT_WHITE, alpha=0.78, clip_mask=mask)

    origin2 = (826.0, 374.0)
    draw_circle(frame, (int(origin2[0]), int(origin2[1])), 18, SOFT_WHITE, alpha=0.45, clip_mask=mask)
    draw_crescent_cupping(frame, (822, 456), origin2, 56, 42, rgb=SOFT_WHITE, alpha=0.46, clip_mask=mask)
    draw_crescent_cupping(frame, (816, 528), origin2, 60, 44, rgb=SOFT_WHITE, alpha=0.38, clip_mask=mask)
    draw_trigon_v2(frame, (812, 604), 44, 68, math.pi / 2, rgb=SOFT_WHITE, alpha=0.36, clip_mask=mask)

    draw_rock(frame, [(620, 790), (790, 705), (950, 830), (890, 940), (620, 930)])
    return frame


def study_05_s_curve_river() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    center = curve_points([(70, -20), (310, 270), (710, 415), (1260, 440), (1480, 610), (980, 790), (630, 1115)], samples=240)
    river_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.polylines(river_mask, [np.round(np.array(center)).astype(np.int32)], False, 255, 260, cv2.LINE_AA)
    frame[river_mask > 0] = (PALE_WATER[2], PALE_WATER[1], PALE_WATER[0])

    effective_mask = river_mask.copy()
    rocks = [
        [(1110, 430), (1230, 430), (1270, 590), (1080, 610), (1035, 510)],
        [(1370, 270), (1505, 260), (1555, 405), (1340, 420)],
        [(1530, 780), (1660, 675), (1770, 830), (1620, 960)],
    ]
    for rock in rocks:
        cv2.fillPoly(effective_mask, [np.array(rock, dtype=np.int32)], 0, lineType=cv2.LINE_AA)

    # Phrase placements are sparse and bend/contact-driven; clipping keeps them
    # inside the water surface rather than drifting onto banks or rocks.
    path1 = curve_points([(990, 555), (1135, 560), (1285, 520), (1415, 505)], samples=86)
    draw_phrase_on_path(frame, path1, 0.04, 72, rgb=SOFT_WHITE, alpha=0.76, clip_mask=effective_mask)
    path2 = curve_points([(1300, 395), (1435, 415), (1565, 455), (1680, 500)], samples=86)
    draw_phrase_on_path(frame, path2, 0.08, 60, rgb=SOFT_WHITE, alpha=0.56, clip_mask=effective_mask)
    path3 = curve_points([(900, 812), (765, 872), (620, 890), (500, 860)], samples=86)
    draw_phrase_on_path(frame, path3, 0.10, 58, rgb=SOFT_WHITE, alpha=0.48, clip_mask=effective_mask)

    for p in [(1010, 620), (965, 650), (920, 675)]:
        draw_circle(frame, p, 5, SOFT_WHITE, alpha=0.62, clip_mask=effective_mask)
    for rock in rocks:
        draw_rock(frame, rock)
    return frame


def save_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    studies = [
        ("01_vancity_grammar_reconstruction_v002_source_grounded.png", study_01_vancity()),
        ("02_procedural_line_following_v002_source_grounded.png", study_02_line_following()),
        ("03_river_band_v002_source_grounded.png", study_03_river_band()),
        ("04_waterfall_vertical_v002_source_grounded.png", study_04_waterfall_vertical()),
        ("05_s_curve_river_topology_v002_source_grounded.png", study_05_s_curve_river()),
    ]
    thumbs = []
    for name, frame in studies:
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(name).stem[:48], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    rows = []
    for i in range(0, len(thumbs), 2):
        row = thumbs[i : i + 2]
        if len(row) == 1:
            row.append(np.zeros_like(row[0]))
        rows.append(cv2.hconcat(row))
    cv2.imwrite(str(OUT_DIR / "contact_sheet_source_grounded_layouts_v002.png"), cv2.vconcat(rows), [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"Wrote {len(studies)} PNG studies plus contact sheet to {OUT_DIR}")


if __name__ == "__main__":
    save_all()
