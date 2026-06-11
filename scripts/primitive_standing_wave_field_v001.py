#!/usr/bin/env python3.11
"""
Primitive standing-wave field v001.

Internal black-screen additive prototype for Darren's 2026-05-20 primitive
field direction. The pass tests standing-wave / phase-inversion behavior using
circle, crescent, and trigon primitives only:

    filled cells -> nodal outlines -> inverse / negative-space cells -> outlines

No topology extraction, no seed/flower construction, no fish or animals, no SD,
no LoRA, no Austin source artwork, and no public cultural meaning claim.
"""
from __future__ import annotations

import json
import math
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "primitive_standing_wave_field_v001_2026-05-20"
)
STILLS_DIR = OUT_DIR / "midpoint_stills"
SAMPLE_DIR = OUT_DIR / "sample_stills"

W = 1920
H = 1080
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)
MID_FRAME = N_FRAMES // 2
TAU = math.tau

BLACK = (0, 0, 0)
IVORY = (238, 242, 232)
SOFT_IVORY = (208, 224, 218)
PALE_BLUE = (139, 213, 238)
TEAL = (64, 176, 189)
DEEP_TEAL = (29, 73, 82)
GOLD = (255, 204, 104)
AMBER = (229, 126, 74)
RED = (224, 82, 64)
VOID_EDGE = (166, 224, 226)
DEBUG_RGB = (116, 238, 214)
LABEL_RGB = (232, 240, 230)
DIM_RGB = (44, 78, 84)

MORPH_N = 216


@dataclass(frozen=True)
class Primitive:
    primitive_id: str
    clip_key: str
    kind: str
    center: tuple[float, float]
    size: float
    angle: float
    spatial: float
    phase_offset: float
    alpha: float
    role: str
    band_id: str = ""
    debug_rank: int = 999


@dataclass(frozen=True)
class ClipSpec:
    key: str
    filename: str
    title: str
    description: str
    renderer: Callable[[int, bool], np.ndarray]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def smoothstep(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(value: float) -> float:
    t = clamp01(value)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def rgb_to_bgr(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)


def canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def draw_text(
    frame: np.ndarray,
    text: str,
    xy: tuple[int, int],
    rgb: tuple[int, int, int] = LABEL_RGB,
    *,
    scale: float = 0.46,
    thickness: int = 1,
) -> None:
    cv2.putText(
        frame,
        text,
        xy,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (rgb[2], rgb[1], rgb[0]),
        thickness,
        lineType=cv2.LINE_AA,
    )


def add_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0:
        return
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = rgb_to_bgr(rgb)
    a = (mask.astype(np.float32) / 255.0) * alpha
    if glow > 0.0:
        blur_radius = max(7, int(max(mask.shape) * 0.085) | 1)
        glow_mask = cv2.GaussianBlur(mask, (blur_radius, blur_radius), 0)
        crop += color * ((glow_mask.astype(np.float32) / 255.0) * glow)[..., None]
    crop += color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def cut_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    amount: float,
) -> None:
    if amount <= 0.0:
        return
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    a = (mask.astype(np.float32) / 255.0) * clamp01(amount)
    crop *= (1.0 - a[..., None])
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def poly_bbox(pts: np.ndarray, pad: int = 58) -> tuple[int, int, int, int] | None:
    if pts.size == 0:
        return None
    x0 = max(0, int(math.floor(float(pts[:, 0].min()))) - pad)
    y0 = max(0, int(math.floor(float(pts[:, 1].min()))) - pad)
    x1 = min(W, int(math.ceil(float(pts[:, 0].max()))) + pad + 1)
    y1 = min(H, int(math.ceil(float(pts[:, 1].max()))) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def local_poly_mask(
    pts: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    fill: bool,
    thickness: int = 2,
) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    local = np.round(pts).astype(np.int32).copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    if fill:
        cv2.fillPoly(mask, [local], 255, lineType=cv2.LINE_AA)
    else:
        cv2.polylines(mask, [local], True, 255, thickness, lineType=cv2.LINE_AA)
    return mask


def draw_poly_fill(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    glow: float = 0.06,
    outline_alpha: float = 0.0,
) -> None:
    bbox = poly_bbox(pts)
    if bbox is None or alpha <= 0.0:
        return
    fill = local_poly_mask(pts, bbox, fill=True)
    add_mask(frame, fill, bbox, rgb, alpha, glow=glow)
    if outline_alpha > 0.0:
        outline = local_poly_mask(pts, bbox, fill=False, thickness=2)
        add_mask(frame, outline, bbox, rgb, outline_alpha, glow=0.0)


def draw_poly_outline(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
    glow: float = 0.0,
) -> None:
    bbox = poly_bbox(pts)
    if bbox is None or alpha <= 0.0:
        return
    outline = local_poly_mask(pts, bbox, fill=False, thickness=thickness)
    add_mask(frame, outline, bbox, rgb, alpha, glow=glow)


def draw_poly_void(
    frame: np.ndarray,
    pts: np.ndarray,
    *,
    amount: float,
    edge_alpha: float,
) -> None:
    bbox = poly_bbox(pts)
    if bbox is None or amount <= 0.0:
        return
    fill = local_poly_mask(pts, bbox, fill=True)
    cut_mask(frame, fill, bbox, amount=amount)
    outline = local_poly_mask(pts, bbox, fill=False, thickness=3)
    add_mask(frame, outline, bbox, VOID_EDGE, edge_alpha, glow=0.018 * edge_alpha)


def draw_line_additive(
    frame: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    cv2.line(
        overlay,
        (round(p0[0]), round(p0[1])),
        (round(p1[0]), round(p1[1])),
        (rgb[2], rgb[1], rgb[0]),
        thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_path_additive(
    frame: np.ndarray,
    pts: list[tuple[float, float]],
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
    closed: bool = False,
) -> None:
    if alpha <= 0.0 or len(pts) < 2:
        return
    overlay = np.zeros_like(frame)
    arr = np.round(np.array(pts, dtype=np.float32)).astype(np.int32)
    cv2.polylines(overlay, [arr], closed, (rgb[2], rgb[1], rgb[0]), thickness, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_arrow(
    frame: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    rgb: tuple[int, int, int] = DEBUG_RGB,
    *,
    alpha: float = 0.72,
) -> None:
    overlay = np.zeros_like(frame)
    cv2.arrowedLine(
        overlay,
        (round(p0[0]), round(p0[1])),
        (round(p1[0]), round(p1[1])),
        (rgb[2], rgb[1], rgb[0]),
        2,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def circle_base(n: int = MORPH_N) -> np.ndarray:
    pts = []
    for i in range(n):
        a = -math.pi / 2.0 + TAU * i / n
        pts.append((0.63 * math.cos(a), 0.63 * math.sin(a)))
    return np.array(pts, dtype=np.float32)


def cubic_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    samples: int,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(samples):
        t = i / max(1, samples)
        u = 1.0 - t
        pts.append(
            (
                u * u * u * p0[0]
                + 3.0 * u * u * t * p1[0]
                + 3.0 * u * t * t * p2[0]
                + t * t * t * p3[0],
                u * u * u * p0[1]
                + 3.0 * u * u * t * p1[1]
                + 3.0 * u * t * t * p2[1]
                + t * t * t * p3[1],
            )
        )
    return pts


def crescent_base(n: int = MORPH_N, *, phase_variant: float = 0.0) -> np.ndarray:
    half = n // 2
    top = (-0.42, -0.63 - 0.035 * phase_variant)
    bottom = (-0.42, 0.63 + 0.030 * phase_variant)
    outer_ctrl_a = (0.45 + 0.06 * phase_variant, -0.76)
    outer_ctrl_b = (0.88, 0.10 + 0.02 * phase_variant)
    inner_ctrl_a = (-0.03 + 0.05 * phase_variant, 0.34)
    inner_ctrl_b = (-0.02, -0.34)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(top, outer_ctrl_a, outer_ctrl_b, bottom, half))
    pts.extend(cubic_curve(bottom, inner_ctrl_a, inner_ctrl_b, top, n - half))
    return np.array(pts, dtype=np.float32)


def trigon_base(n: int = MORPH_N) -> np.ndarray:
    upper = n // 3 + 20
    lower = n // 3 + 20
    rear = n - upper - lower
    rear_top = (-0.63, -0.48)
    rear_bottom = (-0.61, 0.48)
    tip = (0.98, 0.00)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(rear_top, (-0.18, -0.66), (0.58, -0.34), tip, upper))
    pts.extend(cubic_curve(tip, (0.57, 0.33), (-0.20, 0.66), rear_bottom, lower))
    pts.extend(cubic_curve(rear_bottom, (-0.82, 0.26), (-0.82, -0.25), rear_top, rear))
    return np.array(pts, dtype=np.float32)


CIRCLE_BASE = circle_base()
CRESCENT_BASE_A = crescent_base(phase_variant=0.0)
CRESCENT_BASE_B = crescent_base(phase_variant=0.85)
TRIGON_BASE = trigon_base()


def rotate_points(points: np.ndarray, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    return points @ rot.T


def transform_points(
    base: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
) -> np.ndarray:
    pts = base.astype(np.float32).copy()
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    pts = rotate_points(pts, angle)
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]
    return pts


def base_for_kind(kind: str) -> np.ndarray:
    if kind == "circle":
        return CIRCLE_BASE
    if kind == "crescent_b":
        return CRESCENT_BASE_B
    if kind == "trigon":
        return TRIGON_BASE
    return CRESCENT_BASE_A


def color_for_kind(kind: str) -> tuple[int, int, int]:
    if kind == "circle":
        return GOLD
    if kind == "trigon":
        return AMBER
    if kind == "crescent_b":
        return SOFT_IVORY
    return IVORY


def shape_points(
    primitive: Primitive,
    *,
    center: tuple[float, float] | None = None,
    angle: float | None = None,
    size: float | None = None,
    squash: float = 1.0,
) -> np.ndarray:
    return transform_points(
        base_for_kind(primitive.kind),
        center if center is not None else primitive.center,
        size if size is not None else primitive.size,
        (size if size is not None else primitive.size) * squash,
        angle if angle is not None else primitive.angle,
    )


def primitive_phase_value(primitive: Primitive, phase: float, *, travel: bool = False) -> float:
    if travel:
        return primitive.spatial * math.cos(TAU * ((phase + primitive.phase_offset) % 1.0))
    return primitive.spatial * math.cos(TAU * phase)


def node_label(spatial: float) -> str:
    mag = abs(spatial)
    if mag < 0.22:
        return "NODE"
    if mag > 0.74:
        return "ANTINODE"
    return "PHASE"


def draw_phase_primitives(
    frame: np.ndarray,
    primitives: list[Primitive],
    phase: float,
    *,
    debug: bool,
    travel: bool = False,
    dynamic: Callable[[Primitive, float, float], tuple[tuple[float, float], float, float, float]] | None = None,
) -> None:
    prepared: list[tuple[Primitive, float, tuple[float, float], float, float, float]] = []
    for primitive in primitives:
        value = primitive_phase_value(primitive, phase, travel=travel)
        center, angle, size, squash = primitive.center, primitive.angle, primitive.size, 1.0
        if dynamic is not None:
            center, angle, size, squash = dynamic(primitive, phase, value)
        prepared.append((primitive, value, center, angle, size, squash))

    # A low antinodal wash makes negative-space primitives read as cutouts on a
    # black additive layer instead of disappearing into the background.
    for primitive, value, center, angle, size, squash in prepared:
        wash = 0.018 + 0.045 * smoothstep(abs(value))
        pts = shape_points(primitive, center=center, angle=angle, size=size * 1.08, squash=squash)
        draw_poly_fill(frame, pts, DEEP_TEAL, alpha=wash * primitive.alpha, glow=0.035, outline_alpha=0.0)

    for primitive, value, center, angle, size, squash in prepared:
        line_level = 1.0 - smoothstep((abs(value) - 0.08) / 0.62)
        if abs(primitive.spatial) < 0.22:
            line_level = max(line_level, 0.74)
        alpha = primitive.alpha * (0.075 + 0.38 * line_level)
        pts = shape_points(primitive, center=center, angle=angle, size=size, squash=squash)
        draw_poly_outline(frame, pts, PALE_BLUE if value >= 0 else VOID_EDGE, alpha=alpha, thickness=2)

    for primitive, value, center, angle, size, squash in prepared:
        if value <= 0.02:
            continue
        fill_level = smootherstep((value - 0.10) / 0.86)
        if fill_level <= 0.0:
            continue
        pts = shape_points(
            primitive,
            center=center,
            angle=angle,
            size=size * (0.96 + 0.08 * fill_level),
            squash=squash,
        )
        draw_poly_fill(
            frame,
            pts,
            color_for_kind(primitive.kind),
            alpha=primitive.alpha * (0.14 + 0.74 * fill_level),
            glow=0.09 * primitive.alpha * fill_level,
            outline_alpha=0.04 + 0.08 * fill_level,
        )

    for primitive, value, center, angle, size, squash in prepared:
        if value >= -0.02:
            continue
        void_level = smootherstep((-value - 0.10) / 0.86)
        if void_level <= 0.0:
            continue
        pts = shape_points(
            primitive,
            center=center,
            angle=angle,
            size=size * (0.99 + 0.07 * void_level),
            squash=squash,
        )
        draw_poly_void(frame, pts, amount=0.48 + 0.44 * void_level, edge_alpha=primitive.alpha * (0.12 + 0.42 * void_level))

    if debug:
        for primitive, value, center, angle, size, _squash in prepared:
            if primitive.debug_rank > 12:
                continue
            label = f"{primitive.primitive_id} {node_label(primitive.spatial)} phase={value:+.2f}"
            draw_text(frame, label, (round(center[0] + 12), round(center[1] - 10)), DEBUG_RGB, scale=0.34)
            draw_arrow(
                frame,
                center,
                (center[0] + math.cos(angle) * size * 0.94, center[1] + math.sin(angle) * size * 0.94),
                DEBUG_RGB,
                alpha=0.46,
            )


def field_mode_grid(x: float, y: float) -> float:
    a = 0.54 * math.sin(0.0071 * x + 0.0028 * y + 0.55 * math.sin(y * 0.0045))
    b = 0.42 * math.cos(-0.0024 * x + 0.0086 * y + 0.30 * math.sin(x * 0.0031))
    c = 0.26 * math.sin(0.0052 * x - 0.0064 * y)
    return clamp(a + b + c, -1.0, 1.0)


def field_angle(mode_fn: Callable[[float, float], float], x: float, y: float) -> float:
    eps = 5.0
    dx = mode_fn(x + eps, y) - mode_fn(x - eps, y)
    dy = mode_fn(x, y + eps) - mode_fn(x, y - eps)
    return math.atan2(dy, dx) + math.pi / 2.0


def build_phase_grid_primitives() -> list[Primitive]:
    primitives: list[Primitive] = []
    debug_rank = 0
    for row in range(8):
        count = 9 + (row % 3)
        y_base = 156.0 + row * 111.0
        for col in range(count):
            u = (col + 0.5) / count
            x = 155.0 + u * 1620.0 + 42.0 * math.sin(row * 1.23) + 24.0 * math.sin(col * 0.71 + row)
            y = y_base + 38.0 * math.sin(col * 0.78 + row * 0.54) + 19.0 * math.sin(x * 0.0062)
            if x < 70 or x > W - 70 or y < 80 or y > H - 80:
                continue
            spatial = field_mode_grid(x, y)
            kind = ["circle", "crescent", "crescent_b", "trigon"][(col + row * 2) % 4]
            size = 43.0 + 9.0 * math.sin((row + 1) * 0.8 + col * 0.44)
            angle = field_angle(field_mode_grid, x, y)
            if kind == "trigon":
                angle += 0.10 * math.sin(row + col)
            role = f"{node_label(spatial).lower()} primitive in oblique standing-wave field"
            rank = 999
            if abs(spatial) < 0.20 or abs(spatial) > 0.78:
                rank = debug_rank
                debug_rank += 1
            primitives.append(
                Primitive(
                    primitive_id=f"g{row:02d}.{col:02d}",
                    clip_key="phase_inversion_grid",
                    kind=kind,
                    center=(x, y),
                    size=size,
                    angle=angle,
                    spatial=spatial,
                    phase_offset=0.0,
                    alpha=0.78,
                    role=role,
                    band_id=f"oblique-row-{row}",
                    debug_rank=rank,
                )
            )
    return primitives


PHASE_GRID_PRIMITIVES = build_phase_grid_primitives()


def draw_grid_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    drive = math.cos(TAU * phase)
    line_level = 1.0 - abs(drive)
    for row in range(7):
        pts: list[tuple[float, float]] = []
        for i in range(118):
            x = -60.0 + i * (W + 120.0) / 117.0
            y = 155.0 + row * 128.0 + 34.0 * math.sin(x * 0.0065 + row * 0.72) + 18.0 * math.sin(x * 0.012 - phase * TAU)
            pts.append((x, y))
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.045 + 0.15 * line_level, thickness=2)
    for col in range(5):
        pts = []
        for i in range(96):
            y = -60.0 + i * (H + 120.0) / 95.0
            x = 330.0 + col * 320.0 + 42.0 * math.sin(y * 0.006 + col * 1.12)
            pts.append((x, y))
        draw_path_additive(frame, pts, DIM_RGB, alpha=0.030 + 0.09 * line_level, thickness=1)
    if debug:
        draw_text(frame, "non-Cartesian standing-wave field: outlines at zero crossing, fills invert by phase sign", (70, 112), DEBUG_RGB, scale=0.42)


def render_phase_inversion_grid(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_grid_nodal_field(frame, phase, debug)
    draw_phase_primitives(frame, PHASE_GRID_PRIMITIVES, phase, debug=debug)
    draw_debug_header(frame, "phase_inversion_grid_v001", phase, debug)
    return frame


def radial_spatial(radius: float, theta: float) -> float:
    radial = math.cos((radius - 74.0) / 105.0 * math.pi)
    lobes = 0.62 + 0.38 * math.cos(7.0 * theta + 0.45 * math.sin(radius * 0.012))
    return clamp(radial * lobes, -1.0, 1.0)


def build_radial_primitives() -> list[Primitive]:
    primitives: list[Primitive] = [
        Primitive(
            primitive_id="r00.center",
            clip_key="radial_standing_wave",
            kind="circle",
            center=(W * 0.50, H * 0.51),
            size=112.0,
            angle=0.0,
            spatial=1.0,
            phase_offset=0.0,
            alpha=0.84,
            role="central circle origin / radial pressure antinode",
            band_id="origin",
            debug_rank=0,
        )
    ]
    center = (W * 0.50, H * 0.51)
    rings = [(154.0, 8), (258.0, 11), (372.0, 14), (504.0, 18)]
    debug_rank = 1
    for ridx, (radius, count) in enumerate(rings):
        start = 0.18 * ridx + 0.04 * math.sin(ridx)
        for idx in range(count):
            theta = start + TAU * idx / count + 0.045 * math.sin(idx * 1.7 + ridx)
            local_radius = radius + 14.0 * math.sin(idx * 0.83 + ridx * 1.6)
            x = center[0] + math.cos(theta) * local_radius
            y = center[1] + math.sin(theta) * local_radius * 0.93
            spatial = radial_spatial(local_radius, theta)
            if ridx == 0:
                kind = "crescent" if idx % 3 else "circle"
            elif ridx == len(rings) - 1:
                kind = "trigon" if idx % 2 else "crescent_b"
            else:
                kind = ["crescent", "crescent_b", "trigon"][(idx + ridx) % 3]
            angle = theta
            rank = 999
            if abs(spatial) < 0.20 or abs(spatial) > 0.76:
                rank = debug_rank
                debug_rank += 1
            primitives.append(
                Primitive(
                    primitive_id=f"r{ridx + 1:02d}.{idx:02d}",
                    clip_key="radial_standing_wave",
                    kind=kind,
                    center=(x, y),
                    size=47.0 + 4.0 * ridx,
                    angle=angle,
                    spatial=spatial,
                    phase_offset=0.0,
                    alpha=0.76 - 0.035 * ridx,
                    role="radial lobe primitive: crescent cups center, trigon releases outward",
                    band_id=f"ring-{ridx + 1}",
                    debug_rank=rank,
                )
            )
    return primitives


RADIAL_PRIMITIVES = build_radial_primitives()


def draw_ring_outline(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
) -> None:
    pts = []
    for i in range(240):
        a = TAU * i / 240.0
        pts.append((center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius * 0.93))
    draw_path_additive(frame, pts, rgb, alpha=alpha, thickness=thickness, closed=True)


def draw_radial_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    center = (W * 0.50, H * 0.51)
    drive = math.cos(TAU * phase)
    line_level = 1.0 - abs(drive)
    for radius in [205.0, 316.0, 430.0, 574.0]:
        draw_ring_outline(frame, center, radius, DEEP_TEAL, alpha=0.040 + 0.18 * line_level, thickness=2)
    for spoke in range(14):
        theta = TAU * (spoke + 0.5) / 14.0 + 0.04 * math.sin(spoke)
        pts = []
        for i in range(8, 70):
            r = i * 8.0
            wobble = 6.0 * math.sin(r * 0.018 + spoke)
            pts.append((center[0] + math.cos(theta) * (r + wobble), center[1] + math.sin(theta) * (r + wobble) * 0.93))
        draw_path_additive(frame, pts, DIM_RGB, alpha=0.020 + 0.06 * line_level, thickness=1)
    if debug:
        draw_text(frame, "radial standing wave: fixed lobes swap foreground/background at phase inversion", (70, 112), DEBUG_RGB, scale=0.42)


def radial_dynamic(primitive: Primitive, phase: float, value: float) -> tuple[tuple[float, float], float, float, float]:
    center = (W * 0.50, H * 0.51)
    x, y = primitive.center
    if primitive.primitive_id.endswith("center"):
        scale = 0.96 + 0.08 * abs(value)
        return primitive.center, primitive.angle, primitive.size * scale, 1.0
    dx = x - center[0]
    dy = (y - center[1]) / 0.93
    theta = math.atan2(dy, dx)
    r = math.hypot(dx, dy)
    lift = 11.0 * math.sin(TAU * phase + r * 0.016) * abs(primitive.spatial)
    new_center = (center[0] + math.cos(theta) * (r + lift), center[1] + math.sin(theta) * (r + lift) * 0.93)
    size = primitive.size * (0.94 + 0.10 * abs(value))
    return new_center, theta, size, 1.0


def render_radial_standing_wave(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_radial_nodal_field(frame, phase, debug)
    draw_phase_primitives(frame, RADIAL_PRIMITIVES, phase, debug=debug, dynamic=radial_dynamic)
    draw_debug_header(frame, "radial_standing_wave_v001", phase, debug)
    return frame


def membrane_curve_y(x: float, band: int, phase: float) -> float:
    u = x / W
    base = 150.0 + band * 145.0
    standing = 40.0 * math.sin(TAU * (u * 1.12 + band * 0.115))
    smaller = 18.0 * math.sin(TAU * (u * 2.35 - band * 0.07))
    rise = 18.0 * math.sin(TAU * (phase + u * 0.55 + band * 0.08))
    return base + standing + smaller + rise


def membrane_tangent_angle(x: float, band: int, phase: float) -> float:
    eps = 4.0
    y0 = membrane_curve_y(x - eps, band, phase)
    y1 = membrane_curve_y(x + eps, band, phase)
    return math.atan2(y1 - y0, eps * 2.0)


def build_membrane_primitives() -> list[Primitive]:
    primitives: list[Primitive] = []
    debug_rank = 0
    for band in range(6):
        count = 12 if band % 2 else 13
        for idx in range(count):
            u = (idx + 0.42 + 0.18 * (band % 2)) / count
            x = 90.0 + u * 1740.0
            y = membrane_curve_y(x, band, 0.0)
            angle = membrane_tangent_angle(x, band, 0.0)
            spatial = clamp(math.sin(TAU * (u * 2.25 + band * 0.13)) * (0.74 + 0.26 * math.sin(idx * 0.9)), -1.0, 1.0)
            kind = ["circle", "crescent", "crescent_b", "trigon"][(idx + band) % 4]
            rank = 999
            if abs(spatial) < 0.19 or abs(spatial) > 0.76:
                rank = debug_rank
                debug_rank += 1
            primitives.append(
                Primitive(
                    primitive_id=f"m{band:02d}.{idx:02d}",
                    clip_key="water_membrane_phase_field",
                    kind=kind,
                    center=(x, y),
                    size=40.0 + 8.0 * math.sin(idx * 0.41 + band),
                    angle=angle,
                    spatial=spatial,
                    phase_offset=(x / W) * 0.56 + band * 0.063,
                    alpha=0.74,
                    role="primitive riding a water-membrane phase band",
                    band_id=f"membrane-band-{band}",
                    debug_rank=rank,
                )
            )
    return primitives


MEMBRANE_PRIMITIVES = build_membrane_primitives()


def draw_membrane_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    for band in range(6):
        pts = [(x, membrane_curve_y(x, band, phase)) for x in np.linspace(-60.0, W + 60.0, 132)]
        line_alpha = 0.065 + 0.045 * math.sin(TAU * (phase + band * 0.11)) ** 2
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=line_alpha, thickness=3)
        if band < 5:
            mid_pts = []
            for x in np.linspace(-60.0, W + 60.0, 110):
                y = (membrane_curve_y(x, band, phase) + membrane_curve_y(x, band + 1, phase)) * 0.5
                mid_pts.append((x, y))
            draw_path_additive(frame, mid_pts, DIM_RGB, alpha=0.040, thickness=1)
    if debug:
        draw_text(frame, "water membrane: phase bands travel through fixed primitive roles; bodies rise/fall together", (70, 112), DEBUG_RGB, scale=0.42)


def membrane_dynamic(primitive: Primitive, phase: float, value: float) -> tuple[tuple[float, float], float, float, float]:
    band = int(primitive.band_id.rsplit("-", 1)[-1])
    x = primitive.center[0]
    y = membrane_curve_y(x, band, phase)
    angle = membrane_tangent_angle(x, band, phase)
    size = primitive.size * (0.94 + 0.12 * abs(value))
    squash = 0.92 + 0.12 * math.sin(TAU * (phase + primitive.phase_offset))
    return (x, y), angle, size, squash


def render_water_membrane_phase_field(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_membrane_nodal_field(frame, phase, debug)
    draw_phase_primitives(frame, MEMBRANE_PRIMITIVES, phase, debug=debug, travel=True, dynamic=membrane_dynamic)
    draw_debug_header(frame, "water_membrane_phase_field_v001", phase, debug)
    return frame


@dataclass(frozen=True)
class Ribbon:
    ribbon_id: str
    p0: tuple[float, float]
    p1: tuple[float, float]
    p2: tuple[float, float]
    p3: tuple[float, float]
    count: int
    speed: float
    phase_offset: float


COMPARE_RIBBONS = [
    Ribbon("c0", (0.04, 0.28), (0.24, 0.16), (0.60, 0.38), (0.96, 0.25), 9, 0.044, 0.03),
    Ribbon("c1", (0.03, 0.43), (0.28, 0.62), (0.64, 0.26), (0.97, 0.49), 10, 0.038, 0.19),
    Ribbon("c2", (0.04, 0.60), (0.22, 0.42), (0.64, 0.78), (0.96, 0.60), 10, 0.041, 0.35),
    Ribbon("c3", (0.08, 0.76), (0.30, 0.90), (0.67, 0.55), (0.94, 0.78), 8, 0.035, 0.52),
]


def panel_point(p: tuple[float, float], *, right: bool) -> tuple[float, float]:
    x0 = W * (0.535 if right else 0.045)
    x1 = W * (0.965 if right else 0.455)
    return (x0 + p[0] * (x1 - x0), H * p[1])


def bezier_point(ribbon: Ribbon, t: float, *, right: bool) -> tuple[float, float]:
    u = 1.0 - t
    p0 = panel_point(ribbon.p0, right=right)
    p1 = panel_point(ribbon.p1, right=right)
    p2 = panel_point(ribbon.p2, right=right)
    p3 = panel_point(ribbon.p3, right=right)
    return (
        u * u * u * p0[0] + 3.0 * u * u * t * p1[0] + 3.0 * u * t * t * p2[0] + t * t * t * p3[0],
        u * u * u * p0[1] + 3.0 * u * u * t * p1[1] + 3.0 * u * t * t * p2[1] + t * t * t * p3[1],
    )


def bezier_angle(ribbon: Ribbon, t: float, *, right: bool) -> float:
    u = 1.0 - t
    p0 = panel_point(ribbon.p0, right=right)
    p1 = panel_point(ribbon.p1, right=right)
    p2 = panel_point(ribbon.p2, right=right)
    p3 = panel_point(ribbon.p3, right=right)
    dx = 3.0 * u * u * (p1[0] - p0[0]) + 6.0 * u * t * (p2[0] - p1[0]) + 3.0 * t * t * (p3[0] - p2[0])
    dy = 3.0 * u * u * (p1[1] - p0[1]) + 6.0 * u * t * (p2[1] - p1[1]) + 3.0 * t * t * (p3[1] - p2[1])
    return math.atan2(dy, dx)


def ribbon_path(ribbon: Ribbon, *, right: bool, samples: int = 96) -> list[tuple[float, float]]:
    return [bezier_point(ribbon, i / (samples - 1), right=right) for i in range(samples)]


def morph_base_for_phase(phase: float) -> tuple[np.ndarray, tuple[int, int, int]]:
    states = [
        (CIRCLE_BASE, GOLD),
        (CRESCENT_BASE_A, IVORY),
        (CRESCENT_BASE_B, SOFT_IVORY),
        (TRIGON_BASE, AMBER),
        (CIRCLE_BASE, GOLD),
    ]
    pos = (phase % 1.0) * 4.0
    idx = min(3, int(pos))
    local = pos - idx
    t = smootherstep(local)
    a_pts, a_rgb = states[idx]
    b_pts, b_rgb = states[idx + 1]
    pts = a_pts * (1.0 - t) + b_pts * t
    rgb = tuple(int(round(mix(a_rgb[i], b_rgb[i], t))) for i in range(3))
    return pts, rgb


def build_compare_phase_primitives() -> list[Primitive]:
    primitives: list[Primitive] = []
    debug_rank = 0
    for ribbon in COMPARE_RIBBONS:
        for idx in range(ribbon.count):
            s = (idx + 0.50) / ribbon.count
            center = bezier_point(ribbon, s, right=True)
            angle = bezier_angle(ribbon, s, right=True)
            spatial = clamp(
                0.62 * math.sin(TAU * (s * 1.65 + ribbon.phase_offset))
                + 0.38 * math.cos(TAU * (s * 0.72 - ribbon.phase_offset)),
                -1.0,
                1.0,
            )
            kind = ["circle", "crescent", "crescent_b", "trigon"][(idx + len(ribbon.ribbon_id)) % 4]
            rank = 999
            if abs(spatial) < 0.22 or abs(spatial) > 0.76:
                rank = debug_rank
                debug_rank += 1
            primitives.append(
                Primitive(
                    primitive_id=f"{ribbon.ribbon_id}.{idx:02d}",
                    clip_key="primitive_field_cycle_phase_compare",
                    kind=kind,
                    center=center,
                    size=40.0,
                    angle=angle,
                    spatial=spatial,
                    phase_offset=ribbon.phase_offset,
                    alpha=0.74,
                    role="field-cycle primitive upgraded to standing-wave phase inversion",
                    band_id=ribbon.ribbon_id,
                    debug_rank=rank,
                )
            )
    return primitives


COMPARE_PHASE_PRIMITIVES = build_compare_phase_primitives()


def draw_cycle_only_ghost(frame: np.ndarray, phase: float) -> None:
    for ribbon in COMPARE_RIBBONS:
        draw_path_additive(frame, ribbon_path(ribbon, right=False), DIM_RGB, alpha=0.045, thickness=2)
        for idx in range(ribbon.count):
            base_s = (idx + 0.5) / ribbon.count
            s = (base_s + ribbon.speed * phase) % 1.0
            center = bezier_point(ribbon, s, right=False)
            angle = bezier_angle(ribbon, s, right=False)
            cycle_phase = phase * 1.08 + ribbon.phase_offset + idx * 0.087 + s * 0.35
            pts_base, rgb = morph_base_for_phase(cycle_phase)
            pts = transform_points(pts_base, center, 39.0, 39.0, angle)
            edge = smoothstep(min(s / 0.12, (1.0 - s) / 0.12))
            draw_poly_fill(frame, pts, rgb, alpha=0.26 * edge, glow=0.025, outline_alpha=0.025)


def draw_compare_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    drive = math.cos(TAU * phase)
    line_level = 1.0 - abs(drive)
    draw_line_additive(frame, (W * 0.50, 84.0), (W * 0.50, H - 84.0), DIM_RGB, alpha=0.28, thickness=2)
    for ribbon in COMPARE_RIBBONS:
        draw_path_additive(frame, ribbon_path(ribbon, right=True), DEEP_TEAL, alpha=0.075 + 0.13 * line_level, thickness=3)
    if debug:
        draw_text(frame, "left: cycle-only ghost from older field idea", (92, H - 62), DIM_RGB, scale=0.40)
        draw_text(frame, "right: same field held as phase-inversion standing wave", (W // 2 + 92, H - 62), DEBUG_RGB, scale=0.40)


def render_primitive_field_cycle_phase_compare(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_cycle_only_ghost(frame, phase)
    draw_compare_nodal_field(frame, phase, debug)
    draw_phase_primitives(frame, COMPARE_PHASE_PRIMITIVES, phase, debug=debug)
    draw_debug_header(frame, "primitive_field_cycle_phase_compare_v001", phase, debug)
    return frame


def draw_debug_header(frame: np.ndarray, title: str, phase: float, debug: bool) -> None:
    if not debug:
        return
    drive = math.cos(TAU * phase)
    line_level = 1.0 - abs(drive)
    positive_fill = max(0.0, drive)
    inverse_fill = max(0.0, -drive)
    draw_text(frame, title, (70, 72), LABEL_RGB, scale=0.55, thickness=1)
    draw_text(
        frame,
        f"frame={round(phase * N_FRAMES):03d} phase={phase:.3f} drive={drive:+.3f} outline={line_level:.2f} fill+={positive_fill:.2f} inverse={inverse_fill:.2f}",
        (70, 96),
        LABEL_RGB,
        scale=0.40,
    )
    draw_text(frame, "NODE = low spatial amplitude / outline lock; ANTINODE = fill or negative-space body", (70, 136), DEBUG_RGB, scale=0.40)


CLIPS: list[ClipSpec] = [
    ClipSpec(
        key="phase_inversion_grid",
        filename="phase_inversion_grid_v001.mp4",
        title="Phase Inversion Grid v001",
        description="Structured oblique field, not Cartesian wallpaper: primitives swap outline, fill, and negative-space states.",
        renderer=render_phase_inversion_grid,
    ),
    ClipSpec(
        key="radial_standing_wave",
        filename="radial_standing_wave_v001.mp4",
        title="Radial Standing Wave v001",
        description="Circle-origin radial standing wave with crescent/trigon lobes pulsing in rings without seed/flower geometry.",
        renderer=render_radial_standing_wave,
    ),
    ClipSpec(
        key="water_membrane_phase_field",
        filename="water_membrane_phase_field_v001.mp4",
        title="Water Membrane Phase Field v001",
        description="Flowing membrane bands drive phase through fixed primitive roles, like rising and falling water.",
        renderer=render_water_membrane_phase_field,
    ),
    ClipSpec(
        key="primitive_field_cycle_phase_compare",
        filename="primitive_field_cycle_phase_compare_v001.mp4",
        title="Primitive Field Cycle Phase Compare v001",
        description="Older field-cycle motion is shown as a dim ghost beside the upgraded standing-wave phase field.",
        renderer=render_primitive_field_cycle_phase_compare,
    ),
]


class H264Writer:
    def __init__(self, path: Path, *, fps: int = FPS, size: tuple[int, int] = (W, H), frames: int = N_FRAMES) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{size[0]}x{size[1]}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.path = path

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with exit code {rc}")


def save_png(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError(f"Could not write {path}")


def render_clip(spec: ClipSpec) -> None:
    writer = H264Writer(OUT_DIR / spec.filename)
    sample_frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    for fi in range(N_FRAMES):
        frame = spec.renderer(fi, False)
        writer.write(frame)
        if fi in sample_frames:
            save_png(SAMPLE_DIR / f"{Path(spec.filename).stem}_f{fi:03d}.png", frame)
        if (fi + 1) % 48 == 0:
            print(f"  {spec.filename}: {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    stem = Path(spec.filename).stem
    save_png(STILLS_DIR / f"{stem}_midpoint_f{MID_FRAME:03d}.png", spec.renderer(MID_FRAME, False))
    save_png(STILLS_DIR / f"{stem}_debug_midpoint_f{MID_FRAME:03d}.png", spec.renderer(MID_FRAME, True))


def build_contact_sheet() -> Path:
    frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    frame_labels = ["f000 fill+", "f036 outline", "f072 inverse/debug", "f108 outline", "f143 fill+"]
    cell_w, cell_h = 320, 180
    label_w, label_h = 340, 58
    sheet = np.zeros((label_h + len(CLIPS) * cell_h, label_w + len(frames) * cell_w, 3), dtype=np.uint8)
    draw_text(sheet, "primitive standing-wave field v001", (16, 36), LABEL_RGB, scale=0.42)
    for col, label in enumerate(frame_labels):
        draw_text(sheet, label, (label_w + col * cell_w + 12, 36), LABEL_RGB, scale=0.38)
    for row, spec in enumerate(CLIPS):
        y0 = label_h + row * cell_h
        draw_text(sheet, Path(spec.filename).stem, (16, y0 + 34), LABEL_RGB, scale=0.36)
        for col, fi in enumerate(frames):
            debug = fi == MID_FRAME
            thumb = cv2.resize(spec.renderer(fi, debug), (cell_w, cell_h), interpolation=cv2.INTER_AREA)
            x0 = label_w + col * cell_w
            sheet[y0 : y0 + cell_h, x0 : x0 + cell_w] = thumb
            cv2.rectangle(sheet, (x0, y0), (x0 + cell_w - 1, y0 + cell_h - 1), (42, 56, 56), 1)
    out = OUT_DIR / "primitive_standing_wave_field_v001_contact_sheet.png"
    save_png(out, sheet)
    return out


def primitive_records() -> list[dict[str, object]]:
    all_primitives = PHASE_GRID_PRIMITIVES + RADIAL_PRIMITIVES + MEMBRANE_PRIMITIVES + COMPARE_PHASE_PRIMITIVES
    records: list[dict[str, object]] = []
    for primitive in all_primitives:
        records.append(
            {
                "primitive_id": primitive.primitive_id,
                "clip_key": primitive.clip_key,
                "primitive": "crescent" if primitive.kind == "crescent_b" else primitive.kind,
                "variant": primitive.kind,
                "role": primitive.role,
                "center": [round(primitive.center[0], 2), round(primitive.center[1], 2)],
                "rotation_degrees": round(math.degrees(primitive.angle), 2),
                "size": round(primitive.size, 2),
                "spatial_phase_value": round(primitive.spatial, 4),
                "node_antinode_class": node_label(primitive.spatial),
                "phase_offset": round(primitive.phase_offset, 4),
                "parent_band_id": primitive.band_id,
                "from_state": "outline",
                "to_state": "fill or inverse-negative-space depending on standing-wave phase",
                "curvature_direction": "crescent cups local origin/phase band; trigon points along radial, tangent, or release direction",
                "cultural_status": "internal grammar-inspired sketch; not Austin-approved; not public; not a cultural meaning claim",
            }
        )
    return records


def write_manifest(contact_sheet: Path) -> Path:
    manifest = {
        "renderer": "scripts/primitive_standing_wave_field_v001.py",
        "created": "2026-05-20",
        "status": "INTERNAL ONLY. Not Austin-approved. Not public-ready. Not a cultural meaning claim.",
        "technical": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frames": N_FRAMES,
            "background": "black-screen additive primitive field",
            "phase_model": "standing-wave sign inversion: positive fill, zero-crossing outline, negative/inverse cutout",
        },
        "constraints": [
            "No topology extraction.",
            "No seed-of-life, flower-of-life, rosette, or mandala construction.",
            "No fish, animals, SD, LoRA, Austin source artwork, or source-piece replication.",
            "No random scatter; placement is deterministic on authored oblique fields, radial lobes, membrane bands, or ribbons.",
        ],
        "outputs": {
            "mp4s": [str((OUT_DIR / spec.filename).relative_to(ROOT)) for spec in CLIPS],
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "midpoint_stills_dir": str(STILLS_DIR.relative_to(ROOT)),
            "sample_stills_dir": str(SAMPLE_DIR.relative_to(ROOT)),
        },
        "clips": [
            {
                "key": spec.key,
                "filename": spec.filename,
                "title": spec.title,
                "description": spec.description,
            }
            for spec in CLIPS
        ],
        "primitive_records": primitive_records(),
    }
    out = OUT_DIR / "primitive_standing_wave_field_v001_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out


def write_readme(contact_sheet: Path, manifest: Path) -> None:
    lines = [
        "# Primitive Standing-Wave Field v001 - 2026-05-20",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved, not public-ready, and not a cultural meaning claim.",
        "",
        "This packet tests a standing-wave primitive field rather than another drifting primitive field. Circle, crescent, and trigon bodies are fixed into authored field structures, then the field phase swaps them through outline, fill, and inverse / negative-space states.",
        "",
        "## Outputs",
        "",
    ]
    for spec in CLIPS:
        lines.append(f"- `{spec.filename}`: {spec.description}")
    lines.extend(
        [
            f"- Contact sheet: `{contact_sheet.name}`",
            "- Midpoint stills and debug midpoint stills: `midpoint_stills/`",
            "- Sample stills: `sample_stills/`",
            f"- Sidecar manifest: `{manifest.name}`",
            "",
            "## Render Contract",
            "",
            f"- Resolution: `{W}x{H}`",
            f"- Frame rate: `{FPS}fps`",
            f"- Duration: `{DURATION_SECONDS:.1f}s`",
            f"- Frame count: `{N_FRAMES}`",
            "- Background/blend: black-screen additive with negative-space cutouts",
            "",
            "## Phase Model",
            "",
            "- Positive phase fills antinodal circle/crescent/trigon bodies.",
            "- Zero crossing emphasizes nodal outlines.",
            "- Negative phase cuts the same primitive bodies into the field as inverse / negative space.",
            "- Field placement is authored and deterministic, not random particle drift.",
            "",
            "## Boundaries",
            "",
            "- No topology, seed, or flower extraction.",
            "- No fish, animals, SD, LoRA, Austin source art, or source-piece replication.",
            "- No claim is made about public cultural meaning, Austin authorship, Austin approval, or traditional significance.",
            "- Austin review is required before any public or external use.",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering primitive standing-wave field packet to {OUT_DIR}", flush=True)
    for spec in CLIPS:
        render_clip(spec)
    contact_sheet = build_contact_sheet()
    manifest = write_manifest(contact_sheet)
    write_readme(contact_sheet, manifest)
    print(f"Done: {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
