#!/usr/bin/env python3.11
"""
Primitive syntax and phrase quality still studies v001.

PNG-only packet. No MP4/MOV. Internal Darren grammar exploration only:
not Austin-approved, not a general Coast Salish grammar claim.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT, draw_poly_alpha


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_syntax_phrase_quality_v001_2026-05-19"
W = 1920
H = 1080

BLACK = (0, 0, 0)
IVORY = (246, 247, 242)
SOFT_IVORY = (224, 234, 232)
PALE_BLUE = (168, 217, 236)
DIM_BLUE = (58, 118, 151)
DIM_LINE = (70, 84, 88)
ROCK = (142, 154, 152)


def canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


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


def cubic_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    samples: int,
    *,
    include_endpoint: bool = False,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    stop = samples + 1 if include_endpoint else samples
    for i in range(stop):
        t = i / max(1, samples)
        omt = 1.0 - t
        x = (
            omt * omt * omt * p0[0]
            + 3.0 * omt * omt * t * p1[0]
            + 3.0 * omt * t * t * p2[0]
            + t * t * t * p3[0]
        )
        y = (
            omt * omt * omt * p0[1]
            + 3.0 * omt * omt * t * p1[1]
            + 3.0 * omt * t * t * p2[1]
            + t * t * t * p3[1]
        )
        pts.append((x, y))
    return pts


def syntax_trigon_points(samples: int = 34) -> np.ndarray:
    """Curved trigon with a flattened/crescent-like rear and pointed release.

    Local +x is the release direction. The rear is deliberately shaped so it
    can sit next to a crescent without creating an accidental circle-sized void.
    """

    rear_top = (-0.58, -0.48)
    rear_bottom = (-0.58, 0.48)
    tip = (0.98, 0.0)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(rear_top, (-0.20, -0.62), (0.58, -0.30), tip, samples))
    pts.extend(cubic_curve(tip, (0.58, 0.30), (-0.20, 0.62), rear_bottom, samples))
    pts.extend(cubic_curve(rear_bottom, (-0.74, 0.28), (-0.74, -0.28), rear_top, samples, include_endpoint=True))
    return np.array(pts, dtype=np.float32)


TRIGON_BASE = syntax_trigon_points()


def transform_points(
    base: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
) -> np.ndarray:
    pts = base.copy()
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    out = pts @ rot.T
    out[:, 0] += center[0]
    out[:, 1] += center[1]
    return out


def restore_outside_clip(frame: np.ndarray, before: np.ndarray, clip_mask: np.ndarray | None) -> None:
    if clip_mask is None:
        return
    changed = cv2.absdiff(frame, before).max(axis=2) > 0
    outside = changed & (clip_mask == 0)
    frame[outside] = before[outside]


def draw_poly(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int] = IVORY,
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    draw_poly_alpha(frame, pts.astype(np.float32), rgb, alpha=alpha, outline_rgb=rgb, outline_alpha=0.0, outline_thickness=0)
    if before is not None:
        restore_outside_clip(frame, before, clip_mask)


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    rgb: tuple[int, int, int] = IVORY,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    draw_poly(frame, transform_points(CRESCENT_BASE, center, sx, sy, angle), rgb, alpha=alpha, clip_mask=clip_mask)


def draw_crescent_cupping(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    *,
    rgb: tuple[int, int, int] = IVORY,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    angle_to_origin = math.atan2(origin[1] - center[1], origin[0] - center[0])
    draw_crescent(frame, center, sx, sy, angle_to_origin - math.pi, rgb=rgb, alpha=alpha, clip_mask=clip_mask)


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    rgb: tuple[int, int, int] = IVORY,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    draw_poly(frame, transform_points(TRIGON_BASE, center, sx, sy, angle), rgb, alpha=alpha, clip_mask=clip_mask)


def draw_trigon_release_from(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    *,
    rgb: tuple[int, int, int] = IVORY,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    angle = math.atan2(center[1] - origin[1], center[0] - origin[0])
    draw_trigon(frame, center, sx, sy, angle, rgb=rgb, alpha=alpha, clip_mask=clip_mask)


def draw_circle(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int] = IVORY,
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    overlay = frame.copy()
    cv2.circle(overlay, (round(center[0]), round(center[1])), round(radius), (rgb[2], rgb[1], rgb[0]), -1, lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)
    if before is not None:
        restore_outside_clip(frame, before, clip_mask)


def draw_ring(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    thickness: float,
    rgb: tuple[int, int, int] = IVORY,
    *,
    alpha: float = 1.0,
) -> None:
    overlay = frame.copy()
    cv2.circle(overlay, (round(center[0]), round(center[1])), round(radius), (rgb[2], rgb[1], rgb[0]), round(thickness), lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def draw_oval(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    rgb: tuple[int, int, int] = IVORY,
    *,
    alpha: float = 1.0,
    clip_mask: np.ndarray | None = None,
) -> None:
    before = frame.copy() if clip_mask is not None else None
    overlay = frame.copy()
    cv2.ellipse(
        overlay,
        (round(center[0]), round(center[1])),
        (round(axes[0]), round(axes[1])),
        math.degrees(angle),
        0,
        360,
        (rgb[2], rgb[1], rgb[0]),
        -1,
        lineType=cv2.LINE_AA,
    )
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)
    if before is not None:
        restore_outside_clip(frame, before, clip_mask)


def draw_line(frame: np.ndarray, pts: list[tuple[float, float]], rgb: tuple[int, int, int], alpha: float, thickness: int) -> None:
    overlay = frame.copy()
    cv2.polylines(overlay, [np.round(np.array(pts)).astype(np.int32)], False, (rgb[2], rgb[1], rgb[0]), thickness, cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def draw_poly_fill(frame: np.ndarray, pts: list[tuple[int, int]], rgb: tuple[int, int, int], alpha: float) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(pts, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    color = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    a = (mask.astype(np.float32) / 255.0) * alpha
    base = frame.astype(np.float32)
    base[:] = base * (1.0 - a[..., None]) + color * a[..., None]
    frame[:] = np.clip(base, 0, 255).astype(np.uint8)
    return mask


def draw_path_band(frame: np.ndarray, pts: list[tuple[float, float]], thickness: int, rgb: tuple[int, int, int], alpha: float) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.polylines(mask, [np.round(np.array(pts)).astype(np.int32)], False, 255, thickness, cv2.LINE_AA)
    color = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    a = (mask.astype(np.float32) / 255.0) * alpha
    base = frame.astype(np.float32)
    base[:] = base * (1.0 - a[..., None]) + color * a[..., None]
    frame[:] = np.clip(base, 0, 255).astype(np.uint8)
    return mask


def draw_rock(frame: np.ndarray, pts: list[tuple[int, int]], mask: np.ndarray | None = None) -> None:
    poly = np.array(pts, dtype=np.int32)
    cv2.fillPoly(frame, [poly], (ROCK[2], ROCK[1], ROCK[0]), lineType=cv2.LINE_AA)
    cv2.polylines(frame, [poly], True, (SOFT_IVORY[2], SOFT_IVORY[1], SOFT_IVORY[0]), 5, cv2.LINE_AA)
    if mask is not None:
        cv2.fillPoly(mask, [poly], 0, lineType=cv2.LINE_AA)


def curve_points(points: list[tuple[float, float]], samples: int = 160) -> list[tuple[float, float]]:
    pts = np.array(points, dtype=np.float32)
    out: list[tuple[float, float]] = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        seg_n = max(6, samples // max(1, len(pts) - 1))
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
    alpha: float = 1.0,
    rgb: tuple[int, int, int] = IVORY,
    clip_mask: np.ndarray | None = None,
) -> None:
    origin, _ = path_point(path, s0)
    c1, _ = path_point(path, s0 + 0.060)
    c2, _ = path_point(path, s0 + 0.118)
    tri, tri_angle = path_point(path, s0 + 0.178)
    draw_circle(frame, origin, scale * 0.18, rgb, alpha=alpha, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c1, origin, scale * 0.62, scale * 0.43, rgb=rgb, alpha=alpha * 0.92, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c2, origin, scale * 0.72, scale * 0.50, rgb=rgb, alpha=alpha * 0.84, clip_mask=clip_mask)
    draw_trigon(frame, tri, scale * 0.48, scale * 0.52, tri_angle, rgb=rgb, alpha=alpha * 0.82, clip_mask=clip_mask)


def study_01_pond_ripple() -> np.ndarray:
    frame = canvas()
    origin = (645.0, 560.0)
    for r, a in [(150, 0.10), (300, 0.075), (465, 0.050), (620, 0.035)]:
        draw_ring(frame, origin, r, 3, PALE_BLUE, alpha=a)
    draw_circle(frame, origin, 54, IVORY, alpha=0.95)
    # Asymmetric ripple phrases avoid a decorative radial symbol. Each phrase
    # still preserves circle -> crescent -> crescent -> trigon.
    for deg, strength, scale in [(-38, 0.84, 0.98), (0, 0.94, 1.08), (38, 0.66, 0.92)]:
        angle = math.radians(deg)
        c1 = (origin[0] + math.cos(angle) * 210, origin[1] + math.sin(angle) * 210)
        c2 = (origin[0] + math.cos(angle) * 390, origin[1] + math.sin(angle) * 390)
        tri = (origin[0] + math.cos(angle) * 585, origin[1] + math.sin(angle) * 585)
        draw_crescent_cupping(frame, c1, origin, 112 * scale, 78 * scale, alpha=0.88 * strength)
        draw_crescent_cupping(frame, c2, origin, 132 * scale, 92 * scale, alpha=0.70 * strength)
        draw_trigon_release_from(frame, tri, origin, 94 * scale, 100 * scale, alpha=0.56 * strength)
    return frame


def study_02_river_bend() -> np.ndarray:
    frame = canvas()
    center = curve_points([(120, 710), (445, 635), (760, 690), (1050, 600), (1420, 430), (1820, 505)], samples=220)
    mask = draw_path_band(frame, center, 210, PALE_BLUE, 0.20)
    draw_line(frame, center, PALE_BLUE, 0.18, 5)
    rock = [(960, 498), (1060, 465), (1132, 560), (1024, 635), (925, 588)]
    draw_rock(frame, rock, mask=mask)
    bend_path = curve_points([(820, 650), (990, 625), (1180, 555), (1390, 468)], samples=120)
    draw_phrase_on_path(frame, bend_path, 0.05, 116, alpha=0.88, rgb=SOFT_IVORY, clip_mask=mask)
    draw_phrase_on_path(frame, bend_path, 0.48, 92, alpha=0.54, rgb=SOFT_IVORY, clip_mask=mask)
    return frame


def study_03_waterfall_descent() -> np.ndarray:
    frame = canvas()
    fall = [(805, 118), (1050, 118), (1115, 910), (690, 910)]
    mask = draw_poly_fill(frame, fall, PALE_BLUE, 0.20)
    draw_line(frame, [(925, 132), (900, 420), (922, 690), (930, 900)], PALE_BLUE, 0.20, 5)
    origin = (925.0, 250.0)
    draw_circle(frame, origin, 44, SOFT_IVORY, alpha=0.90, clip_mask=mask)
    draw_crescent_cupping(frame, (918, 405), origin, 118, 82, rgb=SOFT_IVORY, alpha=0.86, clip_mask=mask)
    draw_crescent_cupping(frame, (914, 590), origin, 138, 94, rgb=SOFT_IVORY, alpha=0.72, clip_mask=mask)
    draw_trigon(frame, (930, 780), 102, 130, math.pi / 2, rgb=SOFT_IVORY, alpha=0.68, clip_mask=mask)
    draw_rock(frame, [(650, 800), (805, 722), (980, 845), (890, 970), (650, 944)])
    return frame


def study_04_eddy_current_knot() -> np.ndarray:
    frame = canvas()
    origin = (950.0, 545.0)
    spiral: list[tuple[float, float]] = []
    for i in range(180):
        t = i / 179
        a = 1.0 + t * 1.82 * math.pi
        r = 75 + 405 * t
        spiral.append((origin[0] + math.cos(a) * r, origin[1] + math.sin(a) * r * 0.66))
    draw_line(frame, spiral, PALE_BLUE, 0.16, 5)
    draw_ring(frame, origin, 84, 3, PALE_BLUE, alpha=0.12)
    draw_circle(frame, origin, 42, IVORY, alpha=0.92)
    for s, scale, alpha in [(0.18, 104, 0.82), (0.36, 116, 0.72), (0.58, 104, 0.58)]:
        p, _ = path_point(spiral, s)
        draw_crescent_cupping(frame, p, origin, scale, scale * 0.68, rgb=SOFT_IVORY, alpha=alpha)
    p, angle = path_point(spiral, 0.79)
    draw_trigon(frame, p, 88, 98, angle, rgb=SOFT_IVORY, alpha=0.62)
    return frame


def study_05_fin() -> np.ndarray:
    frame = canvas()
    origin = (690.0, 560.0)
    draw_oval(frame, origin, (72, 48), math.radians(-12), IVORY, alpha=0.92)
    draw_crescent_cupping(frame, (840, 540), origin, 150, 105, rgb=SOFT_IVORY, alpha=0.84)
    draw_trigon_release_from(frame, (1065, 505), origin, 230, 168, rgb=IVORY, alpha=0.88)
    draw_crescent_cupping(frame, (1015, 670), origin, 130, 82, rgb=SOFT_IVORY, alpha=0.54)
    return frame


def study_06_joint() -> np.ndarray:
    frame = canvas()
    origin = (960.0, 540.0)
    draw_circle(frame, origin, 84, IVORY, alpha=0.95)
    for deg, scale, alpha in [(35, 150, 0.82), (165, 136, 0.68), (274, 120, 0.55)]:
        angle = math.radians(deg)
        p = (origin[0] + math.cos(angle) * 205, origin[1] + math.sin(angle) * 160)
        draw_crescent_cupping(frame, p, origin, scale, scale * 0.64, rgb=SOFT_IVORY, alpha=alpha)
    for deg, scale, alpha in [(-12, 104, 0.66), (218, 88, 0.48)]:
        angle = math.radians(deg)
        p = (origin[0] + math.cos(angle) * 360, origin[1] + math.sin(angle) * 260)
        draw_trigon_release_from(frame, p, origin, scale, scale * 0.92, rgb=SOFT_IVORY, alpha=alpha)
    return frame


def study_07_body_segment() -> np.ndarray:
    frame = canvas()
    path = curve_points([(430, 610), (650, 510), (900, 525), (1160, 590), (1450, 520)], samples=180)
    draw_line(frame, path, DIM_LINE, 0.22, 4)
    anchors = [0.06, 0.27, 0.49, 0.70]
    last_origin: tuple[float, float] | None = None
    for idx, s in enumerate(anchors):
        p, angle = path_point(path, s)
        draw_oval(frame, p, (64 - idx * 7, 44 - idx * 3), angle, IVORY, alpha=0.90 - idx * 0.10)
        if last_origin is not None:
            c, _ = path_point(path, s - 0.07)
            draw_crescent_cupping(frame, c, last_origin, 100 - idx * 8, 64 - idx * 4, rgb=SOFT_IVORY, alpha=0.74 - idx * 0.08)
        last_origin = p
    tail, tail_angle = path_point(path, 0.91)
    draw_trigon(frame, tail, 96, 88, tail_angle, rgb=SOFT_IVORY, alpha=0.62)
    return frame


def study_08_wing_spine_abstraction() -> np.ndarray:
    frame = canvas()
    root = (620.0, 700.0)
    spine = curve_points([root, (780, 545), (1010, 435), (1300, 385)], samples=150)
    draw_line(frame, spine, DIM_LINE, 0.28, 4)
    draw_circle(frame, root, 52, IVORY, alpha=0.90)
    for s, scale, lift, alpha in [(0.22, 130, -76, 0.76), (0.42, 156, -94, 0.70), (0.62, 138, -82, 0.62)]:
        p, angle = path_point(spine, s)
        origin = root
        c = (p[0] + math.cos(angle - math.pi / 2) * lift, p[1] + math.sin(angle - math.pi / 2) * lift)
        draw_crescent_cupping(frame, c, origin, scale, scale * 0.58, rgb=SOFT_IVORY, alpha=alpha)
    p, angle = path_point(spine, 0.86)
    draw_trigon(frame, (p[0] + 40, p[1] - 28), 132, 106, angle - 0.10, rgb=SOFT_IVORY, alpha=0.72)
    return frame


def study_09_symmetry() -> np.ndarray:
    frame = canvas()
    origin = (960.0, 540.0)
    draw_circle(frame, origin, 58, IVORY, alpha=0.95)
    for side in [-1, 1]:
        for dx, y, sx, sy, alpha in [(190, 445, 120, 82, 0.80), (360, 610, 142, 96, 0.66)]:
            p = (origin[0] + side * dx, y)
            draw_crescent_cupping(frame, p, origin, sx, sy, rgb=SOFT_IVORY, alpha=alpha)
        tri = (origin[0] + side * 540, 540)
        draw_trigon_release_from(frame, tri, origin, 118, 108, rgb=SOFT_IVORY, alpha=0.62)
    draw_line(frame, [(960, 220), (960, 860)], PALE_BLUE, 0.05, 3)
    return frame


def study_10_radial() -> np.ndarray:
    frame = canvas()
    origin = (960.0, 540.0)
    draw_ring(frame, origin, 72, 16, IVORY, alpha=0.90)
    for deg in [0, 60, 120, 180, 240, 300]:
        angle = math.radians(deg)
        c1 = (origin[0] + math.cos(angle) * 195, origin[1] + math.sin(angle) * 195)
        c2 = (origin[0] + math.cos(angle) * 320, origin[1] + math.sin(angle) * 320)
        tri = (origin[0] + math.cos(angle) * 455, origin[1] + math.sin(angle) * 455)
        draw_crescent_cupping(frame, c1, origin, 92, 62, rgb=SOFT_IVORY, alpha=0.72)
        draw_crescent_cupping(frame, c2, origin, 104, 68, rgb=SOFT_IVORY, alpha=0.55)
        draw_trigon_release_from(frame, tri, origin, 72, 78, rgb=SOFT_IVORY, alpha=0.42)
    return frame


def study_11_s_curve() -> np.ndarray:
    frame = canvas()
    path = curve_points([(280, 770), (520, 405), (830, 505), (1120, 655), (1400, 415), (1660, 300)], samples=230)
    draw_line(frame, path, PALE_BLUE, 0.12, 5)
    for s, scale, alpha in [(0.05, 118, 0.90), (0.35, 106, 0.76), (0.64, 96, 0.62)]:
        draw_phrase_on_path(frame, path, s, scale, alpha=alpha, rgb=SOFT_IVORY)
    return frame


def study_12_cellular_reticulated_growth() -> np.ndarray:
    frame = canvas()
    nodes = [
        (540.0, 570.0, 54.0),
        (820.0, 420.0, 42.0),
        (1010.0, 650.0, 48.0),
        (1250.0, 455.0, 38.0),
        (1430.0, 700.0, 34.0),
    ]
    branches = [
        (0, 1, 0.78),
        (0, 2, 0.72),
        (1, 3, 0.58),
        (2, 4, 0.52),
    ]
    for a, b, alpha in branches:
        p0 = nodes[a]
        p1 = nodes[b]
        path = curve_points([(p0[0], p0[1]), ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - 80), (p1[0], p1[1])], samples=70)
        draw_line(frame, path, PALE_BLUE, 0.08, 4)
        c, _ = path_point(path, 0.45)
        draw_crescent_cupping(frame, c, (p0[0], p0[1]), 78, 50, rgb=SOFT_IVORY, alpha=alpha)
        tri, angle = path_point(path, 0.74)
        draw_trigon(frame, tri, 54, 56, angle, rgb=SOFT_IVORY, alpha=alpha * 0.70)
    for x, y, r in nodes:
        draw_oval(frame, (x, y), (r, r * 0.72), math.radians((x + y) % 27), IVORY, alpha=0.86)
    return frame


def save_contact_sheet(studies: list[tuple[str, np.ndarray]]) -> None:
    thumbs = []
    for name, frame in studies:
        thumb = cv2.resize(frame, (384, 216), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(name).stem[:44], (12, 198), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (220, 225, 225), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    rows = []
    for i in range(0, len(thumbs), 4):
        rows.append(cv2.hconcat(thumbs[i : i + 4]))
    cv2.imwrite(str(OUT_DIR / "contact_sheet_12_studies.png"), cv2.vconcat(rows), [cv2.IMWRITE_PNG_COMPRESSION, 3])


def save_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    studies = [
        ("01_water_pond_ripple_syntax.png", study_01_pond_ripple()),
        ("02_water_river_bend_syntax.png", study_02_river_bend()),
        ("03_water_waterfall_descent_syntax.png", study_03_waterfall_descent()),
        ("04_water_eddy_current_knot_syntax.png", study_04_eddy_current_knot()),
        ("05_figure_fin_syntax.png", study_05_fin()),
        ("06_figure_joint_syntax.png", study_06_joint()),
        ("07_figure_body_segment_syntax.png", study_07_body_segment()),
        ("08_figure_wing_spine_abstraction_syntax.png", study_08_wing_spine_abstraction()),
        ("09_pattern_symmetry_syntax.png", study_09_symmetry()),
        ("10_pattern_radial_syntax.png", study_10_radial()),
        ("11_pattern_s_curve_syntax.png", study_11_s_curve()),
        ("12_pattern_cellular_reticulated_growth_syntax.png", study_12_cellular_reticulated_growth()),
    ]
    for name, frame in studies:
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    save_contact_sheet(studies)
    print(f"Wrote {len(studies)} PNG syntax studies plus contact sheet to {OUT_DIR}")


if __name__ == "__main__":
    save_all()
