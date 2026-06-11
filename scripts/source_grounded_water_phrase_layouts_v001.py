#!/usr/bin/env python3.11
"""
Source-grounded water phrase layout stills v001.

PNG-only correction packet. No animation, no MP4s. These stills are layout
studies against Austin's meeting screenshots/transcript, not approved artwork.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT, TRIGON_BASE, draw_poly_alpha


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/source_grounded_water_phrase_layout_correction_2026-05-19"
W = 1920
H = 1080

BLACK = (0, 0, 0)
WHITE = (245, 247, 244)
PALE_WATER = (151, 206, 231)
MID_WATER = (82, 140, 191)
DEEP_BLUE = (45, 77, 111)
TREE_BLUE = (19, 126, 160)
ROCK = (159, 170, 170)
RED = (255, 28, 28)
SOFT_WHITE = (230, 244, 248)


def canvas(color: tuple[int, int, int] = BLACK) -> np.ndarray:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    arr[:] = (color[2], color[1], color[0])
    return arr


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


def draw_poly(frame: np.ndarray, pts: np.ndarray, rgb: tuple[int, int, int], *, alpha: float = 1.0) -> None:
    draw_poly_alpha(frame, pts.astype(np.float32), rgb, alpha=alpha, outline_rgb=rgb, outline_alpha=0.0, outline_thickness=0)


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
) -> None:
    draw_poly(frame, transform_points(CRESCENT_BASE, center, sx, sy, angle, flip_y=flip_y), rgb, alpha=alpha)


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
) -> None:
    draw_poly(frame, transform_points(TRIGON_BASE, center, sx, sy, angle), rgb, alpha=alpha)


def draw_circle(frame: np.ndarray, center: tuple[int, int], radius: int, rgb: tuple[int, int, int], *, alpha: float = 1.0) -> None:
    overlay = frame.copy()
    cv2.circle(overlay, center, radius, (rgb[2], rgb[1], rgb[0]), -1, lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


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


def draw_phrase_on_path(
    frame: np.ndarray,
    path: list[tuple[float, float]],
    s0: float,
    scale: float,
    *,
    rgb: tuple[int, int, int] = WHITE,
    alpha: float = 1.0,
    include_circle: bool = True,
) -> None:
    offsets = [0.0, 0.055, 0.115, 0.185]
    for idx, off in enumerate(offsets):
        pos, angle = path_point(path, s0 + off)
        if idx == 0 and include_circle:
            draw_circle(frame, (int(pos[0]), int(pos[1])), int(scale * 0.18), rgb, alpha=alpha)
        elif idx in (1, 2):
            draw_crescent(frame, pos, scale * (0.58 if idx == 1 else 0.66), scale * 0.43, angle + math.pi, rgb=rgb, alpha=alpha * (0.96 - idx * 0.06))
        elif idx == 3:
            draw_trigon(frame, pos, scale * 0.46, scale * 0.42, angle, rgb=rgb, alpha=alpha * 0.86)


def draw_rock(frame: np.ndarray, points: list[tuple[int, int]]) -> None:
    cv2.fillPoly(frame, [np.array(points, dtype=np.int32)], (ROCK[2], ROCK[1], ROCK[0]), lineType=cv2.LINE_AA)
    cv2.polylines(frame, [np.array(points, dtype=np.int32)], True, (255, 255, 255), 5, lineType=cv2.LINE_AA)


def study_01_vancity() -> np.ndarray:
    frame = canvas(BLACK)
    center_y = H // 2 + 20
    # Source-grounded, slide-like: large ring/crescent/trigon/crescent/crescent sequence.
    draw_circle_ring(frame, (1390, center_y), 118, 36, WHITE)
    draw_crescent(frame, (1190, center_y), 170, 220, math.pi, rgb=WHITE)
    draw_crescent(frame, (990, center_y), 175, 230, math.pi, rgb=WHITE)
    draw_trigon(frame, (760, center_y), 365, 72, math.pi, rgb=WHITE)
    draw_crescent(frame, (575, center_y), 260, 345, math.pi, rgb=WHITE)
    dotted_arrow(frame, (1390, center_y), (525, center_y), rgb=RED)
    dotted_arrow(frame, (1390, center_y - 120), (760, center_y - 120), rgb=RED)
    dotted_arrow(frame, (1390, center_y + 120), (760, center_y + 120), rgb=RED)
    return frame


def study_02_line_following() -> np.ndarray:
    frame = canvas(BLACK)
    path = curve_points([(190, 725), (420, 425), (720, 455), (1020, 295), (1395, 410), (1710, 285)], samples=180)
    cv2.polylines(frame, [np.round(np.array(path)).astype(np.int32)], False, (80, 80, 80), 4, cv2.LINE_AA)
    for s, scale, alpha in [(0.03, 112, 1.0), (0.31, 102, 0.92), (0.59, 96, 0.86), (0.79, 88, 0.74)]:
        draw_phrase_on_path(frame, path, s, scale, rgb=WHITE, alpha=alpha)
    return frame


def study_03_river_band() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    band = np.array(
        [
            (0, 620), (305, 620), (350, 655), (425, 658), (500, 605), (1010, 600), (1090, 640),
            (1220, 640), (1275, 600), (1920, 600), (1920, 805), (1240, 805), (1170, 775),
            (1030, 775), (960, 820), (0, 820)
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(frame, [band], (PALE_WATER[2], PALE_WATER[1], PALE_WATER[0]), lineType=cv2.LINE_AA)
    # Land cuts echo the screenshot's river notches.
    cv2.fillPoly(frame, [np.array([(330, 620), (425, 620), (450, 715), (375, 720)], dtype=np.int32)], (DEEP_BLUE[2], DEEP_BLUE[1], DEEP_BLUE[0]), lineType=cv2.LINE_AA)
    cv2.fillPoly(frame, [np.array([(760, 720), (900, 720), (930, 805), (710, 805)], dtype=np.int32)], (DEEP_BLUE[2], DEEP_BLUE[1], DEEP_BLUE[0]), lineType=cv2.LINE_AA)
    # Sparse current marks inside the broad river band.
    path = curve_points([(270, 765), (520, 710), (835, 710), (1120, 745), (1460, 665), (1790, 665)], samples=160)
    draw_phrase_on_path(frame, path, 0.03, 62, rgb=SOFT_WHITE, alpha=0.95, include_circle=False)
    draw_phrase_on_path(frame, path, 0.32, 58, rgb=SOFT_WHITE, alpha=0.42, include_circle=False)
    draw_phrase_on_path(frame, path, 0.77, 76, rgb=SOFT_WHITE, alpha=0.52, include_circle=False)
    draw_rock(frame, [(760, 565), (835, 560), (865, 630), (780, 635)])
    draw_rock(frame, [(1540, 785), (1625, 730), (1710, 820), (1515, 820)])
    return frame


def study_04_waterfall_vertical() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    # Mountain / cliff and falling-water sheet.
    cv2.fillPoly(frame, [np.array([(0, 0), (760, 0), (610, 175), (360, 305), (160, 475), (0, 610)], dtype=np.int32)], (MID_WATER[2], MID_WATER[1], MID_WATER[0]), lineType=cv2.LINE_AA)
    fall = np.array([(790, 150), (990, 150), (1065, 880), (670, 880)], dtype=np.int32)
    cv2.fillPoly(frame, [fall], (PALE_WATER[2], PALE_WATER[1], PALE_WATER[0]), lineType=cv2.LINE_AA)
    draw_rock(frame, [(620, 790), (790, 705), (950, 830), (890, 940), (620, 930)])
    # Vertical stacked marks: large enough to read from Austin's waterfall precedent.
    x = 890
    draw_circle(frame, (x, 260), 34, SOFT_WHITE, alpha=0.85)
    draw_crescent(frame, (x + 5, 390), 92, 66, -math.pi / 2, rgb=SOFT_WHITE, alpha=0.88)
    draw_crescent(frame, (x - 8, 535), 104, 72, -math.pi / 2, rgb=SOFT_WHITE, alpha=0.78)
    draw_trigon(frame, (x + 12, 710), 86, 120, math.pi / 2, rgb=SOFT_WHITE, alpha=0.78)
    # Smaller adjacent fall phrase.
    x2 = 720
    draw_circle(frame, (x2, 370), 18, SOFT_WHITE, alpha=0.45)
    draw_crescent(frame, (x2 - 8, 455), 56, 42, -math.pi / 2, rgb=SOFT_WHITE, alpha=0.46)
    draw_trigon(frame, (x2 - 6, 550), 42, 64, math.pi / 2, rgb=SOFT_WHITE, alpha=0.38)
    return frame


def study_05_s_curve_river() -> np.ndarray:
    frame = canvas(DEEP_BLUE)
    # Broad S-curve river path inspired by the looping-screen screenshot.
    center = curve_points([(70, -20), (310, 270), (710, 415), (1260, 440), (1480, 610), (980, 790), (630, 1115)], samples=220)
    river_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.polylines(river_mask, [np.round(np.array(center)).astype(np.int32)], False, 255, 260, cv2.LINE_AA)
    frame[river_mask > 0] = (PALE_WATER[2], PALE_WATER[1], PALE_WATER[0])
    # Topology / rocks, with marks only near bends and contact points.
    draw_rock(frame, [(1110, 430), (1230, 430), (1270, 590), (1080, 610), (1035, 510)])
    draw_rock(frame, [(1370, 270), (1505, 260), (1555, 405), (1340, 420)])
    draw_rock(frame, [(1530, 780), (1660, 675), (1770, 830), (1620, 960)])
    # Foam/contact marks and phrase fragments near bends/rocks, not throughout.
    path1 = curve_points([(1020, 555), (1160, 560), (1300, 520), (1420, 505)], samples=80)
    draw_phrase_on_path(frame, path1, 0.05, 68, rgb=SOFT_WHITE, alpha=0.78, include_circle=False)
    path2 = curve_points([(1310, 385), (1450, 410), (1570, 450), (1680, 500)], samples=80)
    draw_phrase_on_path(frame, path2, 0.08, 58, rgb=SOFT_WHITE, alpha=0.58, include_circle=False)
    path3 = curve_points([(890, 820), (760, 875), (620, 890), (500, 860)], samples=80)
    draw_phrase_on_path(frame, path3, 0.10, 58, rgb=SOFT_WHITE, alpha=0.48, include_circle=False)
    for p in [(1010, 620), (965, 650), (920, 675)]:
        draw_circle(frame, p, 5, SOFT_WHITE, alpha=0.65)
    return frame


def save_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    studies = [
        ("01_vancity_grammar_reconstruction_source_grounded.png", study_01_vancity()),
        ("02_procedural_line_following_source_grounded.png", study_02_line_following()),
        ("03_river_band_source_grounded.png", study_03_river_band()),
        ("04_waterfall_vertical_source_grounded.png", study_04_waterfall_vertical()),
        ("05_s_curve_river_topology_source_grounded.png", study_05_s_curve_river()),
    ]
    thumbs = []
    for name, frame in studies:
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(name).stem[:46], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    rows = []
    for i in range(0, len(thumbs), 2):
        row = thumbs[i : i + 2]
        if len(row) == 1:
            row.append(np.zeros_like(row[0]))
        rows.append(cv2.hconcat(row))
    cv2.imwrite(str(OUT_DIR / "contact_sheet_source_grounded_layouts.png"), cv2.vconcat(rows), [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"Wrote {len(studies)} PNG studies plus contact sheet to {OUT_DIR}")


if __name__ == "__main__":
    save_all()
