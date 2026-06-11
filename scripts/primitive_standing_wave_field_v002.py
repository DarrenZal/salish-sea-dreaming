#!/usr/bin/env python3.11
"""
Primitive standing-wave field v002.

Internal black-screen additive prototype for Darren's standing-wave /
phase-inversion lane. This v002 pass corrects the v001 small-glyph-grid read by
using fewer, larger antinodal regions attached to explicit nodal bands, radial
rings, current lanes, and multi-emitter pressure lanes.

No topology/seed extraction, no footage-derived motion, no SD/LoRA, no animals,
no Austin source artwork, and no public cultural meaning claim.
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
    / "primitive_standing_wave_field_v002_2026-05-20"
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
MORPH_N = 240

# RGB colors; OpenCV helpers convert to BGR.
BLACK = (0, 0, 0)
IVORY = (238, 242, 232)
SOFT_IVORY = (208, 224, 218)
PALE_BLUE = (135, 215, 236)
TEAL = (74, 184, 194)
DEEP_TEAL = (22, 68, 76)
DIM_TEAL = (34, 88, 92)
GOLD = (252, 199, 88)
AMBER = (224, 121, 69)
VOID_EDGE = (161, 229, 226)
DEBUG_RGB = (116, 238, 214)
LABEL_RGB = (232, 240, 230)


@dataclass(frozen=True)
class WaveRegion:
    region_id: str
    clip_key: str
    primitive: str
    center: tuple[float, float]
    size: float
    angle: float
    polarity: int
    phase_offset: float
    alpha: float
    role: str
    parent_wave_id: str
    debug_rank: int = 999
    aspect: float = 1.0
    band_index: int = -1
    u: float = 0.0


@dataclass(frozen=True)
class ClipSpec:
    key: str
    filename: str
    title: str
    description: str
    renderer: Callable[[int, bool], np.ndarray]
    regions: Callable[[], list[WaveRegion]]


@dataclass(frozen=True)
class CurrentBand:
    band_id: str
    p0: tuple[float, float]
    p1: tuple[float, float]
    p2: tuple[float, float]
    p3: tuple[float, float]
    count: int
    normal_offset: float
    phase_offset: float
    alpha: float


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
        blur_radius = max(9, int(max(mask.shape) * 0.12) | 1)
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


def poly_bbox(pts: np.ndarray, pad: int = 84) -> tuple[int, int, int, int] | None:
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
    thickness: int = 3,
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
) -> None:
    bbox = poly_bbox(pts)
    if bbox is None or alpha <= 0.0:
        return
    fill = local_poly_mask(pts, bbox, fill=True)
    add_mask(frame, fill, bbox, rgb, alpha, glow=glow)


def draw_poly_outline(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 3,
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
    outline = local_poly_mask(pts, bbox, fill=False, thickness=4)
    add_mask(frame, outline, bbox, VOID_EDGE, edge_alpha, glow=0.030 * edge_alpha)


def draw_path_additive(
    frame: np.ndarray,
    pts: list[tuple[float, float]],
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
    closed: bool = False,
    glow: int = 0,
) -> None:
    if alpha <= 0.0 or len(pts) < 2:
        return
    arr = np.round(np.array(pts, dtype=np.float32)).astype(np.int32)
    pad = max(8, thickness + glow * 2 + 6)
    x0 = max(0, int(arr[:, 0].min()) - pad)
    y0 = max(0, int(arr[:, 1].min()) - pad)
    x1 = min(W, int(arr[:, 0].max()) + pad + 1)
    y1 = min(H, int(arr[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = arr.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    overlay = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
    cv2.polylines(overlay, [local], closed, (rgb[2], rgb[1], rgb[0]), thickness, lineType=cv2.LINE_AA)
    if glow > 0:
        overlay = cv2.GaussianBlur(overlay, (glow | 1, glow | 1), 0)
    crop = frame[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = cv2.addWeighted(overlay, alpha, crop, 1.0, 0)


def draw_arrow(
    frame: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    rgb: tuple[int, int, int] = DEBUG_RGB,
    *,
    alpha: float = 0.60,
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


def circle_base(n: int = MORPH_N) -> np.ndarray:
    pts = []
    for i in range(n):
        a = -math.pi / 2.0 + TAU * i / n
        pts.append((0.64 * math.cos(a), 0.64 * math.sin(a)))
    return np.array(pts, dtype=np.float32)


def crescent_base(n: int = MORPH_N) -> np.ndarray:
    """Local +x is release direction; the crescent cups back toward -x."""
    half = n // 2
    top = (-0.42, -0.64)
    bottom = (-0.42, 0.64)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(top, (0.42, -0.80), (0.94, 0.05), bottom, half))
    pts.extend(cubic_curve(bottom, (-0.04, 0.37), (-0.04, -0.37), top, n - half))
    return np.array(pts, dtype=np.float32)


def trigon_base(n: int = MORPH_N) -> np.ndarray:
    """Curved pointed trigon with shaped rear base; local +x is release."""
    upper = n // 3 + 24
    lower = n // 3 + 24
    rear = n - upper - lower
    rear_top = (-0.64, -0.48)
    rear_bottom = (-0.62, 0.48)
    tip = (0.98, 0.00)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(rear_top, (-0.14, -0.70), (0.56, -0.36), tip, upper))
    pts.extend(cubic_curve(tip, (0.56, 0.35), (-0.18, 0.68), rear_bottom, lower))
    pts.extend(cubic_curve(rear_bottom, (-0.84, 0.24), (-0.84, -0.26), rear_top, rear))
    return np.array(pts, dtype=np.float32)


CIRCLE_BASE = circle_base()
CRESCENT_BASE = crescent_base()
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


def base_for_primitive(primitive: str) -> np.ndarray:
    if primitive == "circle":
        return CIRCLE_BASE
    if primitive == "trigon":
        return TRIGON_BASE
    return CRESCENT_BASE


def color_for_primitive(primitive: str) -> tuple[int, int, int]:
    if primitive == "circle":
        return GOLD
    if primitive == "trigon":
        return AMBER
    return IVORY


def region_pressure(region: WaveRegion, phase: float) -> float:
    return region.polarity * math.cos(TAU * ((phase + region.phase_offset) % 1.0))


def shape_points(
    region: WaveRegion,
    *,
    center: tuple[float, float],
    angle: float,
    size: float,
    aspect: float,
) -> np.ndarray:
    return transform_points(base_for_primitive(region.primitive), center, size, size * aspect, angle)


def default_dynamic(
    region: WaveRegion,
    phase: float,
    value: float,
) -> tuple[tuple[float, float], float, float, float]:
    pressure_breath = 0.94 + 0.13 * abs(value)
    slow_shear = 0.98 + 0.035 * math.sin(TAU * (phase + region.phase_offset))
    return region.center, region.angle, region.size * pressure_breath, region.aspect * slow_shear


def draw_phase_regions(
    frame: np.ndarray,
    regions: list[WaveRegion],
    phase: float,
    *,
    debug: bool,
    dynamic: Callable[[WaveRegion, float, float], tuple[tuple[float, float], float, float, float]] | None = None,
) -> None:
    prepared: list[tuple[WaveRegion, float, tuple[float, float], float, float, float]] = []
    dynamic_fn = dynamic or default_dynamic
    for region in regions:
        value = region_pressure(region, phase)
        center, angle, size, aspect = dynamic_fn(region, phase, value)
        prepared.append((region, value, center, angle, size, aspect))

    # Broad antinodal wash first; this makes inverse/negative-space states
    # visible on black without turning the pass into a background texture.
    for region, value, center, angle, size, aspect in prepared:
        pts = shape_points(region, center=center, angle=angle, size=size * 1.18, aspect=aspect)
        wash_alpha = region.alpha * (0.030 + 0.095 * smoothstep(abs(value)))
        draw_poly_fill(frame, pts, DEEP_TEAL, alpha=wash_alpha, glow=0.15 * region.alpha)

    for region, value, center, angle, size, aspect in prepared:
        if value <= 0.06:
            continue
        fill_level = smootherstep((value - 0.06) / 0.76)
        if fill_level <= 0.0:
            continue
        pts = shape_points(
            region,
            center=center,
            angle=angle,
            size=size * (0.98 + 0.06 * fill_level),
            aspect=aspect,
        )
        draw_poly_fill(
            frame,
            pts,
            color_for_primitive(region.primitive),
            alpha=region.alpha * (0.12 + 0.72 * fill_level),
            glow=0.11 * region.alpha * fill_level,
        )

    for region, value, center, angle, size, aspect in prepared:
        if value >= -0.06:
            continue
        void_level = smootherstep((-value - 0.06) / 0.76)
        if void_level <= 0.0:
            continue
        pts = shape_points(
            region,
            center=center,
            angle=angle,
            size=size * (1.00 + 0.05 * void_level),
            aspect=aspect,
        )
        draw_poly_void(
            frame,
            pts,
            amount=0.58 + 0.35 * void_level,
            edge_alpha=region.alpha * (0.18 + 0.48 * void_level),
        )

    for region, value, center, angle, size, aspect in prepared:
        line_level = 1.0 - smoothstep((abs(value) - 0.04) / 0.62)
        outline_alpha = region.alpha * (0.11 + 0.52 * line_level)
        pts = shape_points(region, center=center, angle=angle, size=size, aspect=aspect)
        draw_poly_outline(
            frame,
            pts,
            PALE_BLUE if value >= 0 else VOID_EDGE,
            alpha=outline_alpha,
            thickness=3,
            glow=0.015 * line_level,
        )

    if debug:
        for region, value, center, angle, size, _aspect in prepared:
            if region.debug_rank > 15:
                continue
            polarity = "pos" if region.polarity > 0 else "neg"
            state = "fill" if value > 0.18 else "void" if value < -0.18 else "outline"
            draw_text(
                frame,
                f"{region.region_id} {region.primitive} {polarity} {state} v={value:+.2f}",
                (round(center[0] + 12), round(center[1] - 12)),
                DEBUG_RGB,
                scale=0.33,
            )
            draw_arrow(
                frame,
                center,
                (center[0] + math.cos(angle) * size * 0.78, center[1] + math.sin(angle) * size * 0.78),
                DEBUG_RGB,
                alpha=0.44,
            )


def draw_debug_header(frame: np.ndarray, title: str, phase: float, debug: bool) -> None:
    if not debug:
        return
    drive = math.cos(TAU * phase)
    outline = 1.0 - abs(drive)
    draw_text(frame, title, (70, 72), LABEL_RGB, scale=0.54)
    draw_text(
        frame,
        f"frame={round(phase * N_FRAMES):03d} phase={phase:.3f} global_drive={drive:+.3f} outline_crossing={outline:.2f}",
        (70, 98),
        LABEL_RGB,
        scale=0.39,
    )
    draw_text(
        frame,
        "phase rule: positive antinodes fill; zero crossing outlines; inverse phase cuts/fills complementary regions",
        (70, 126),
        DEBUG_RGB,
        scale=0.38,
    )


def outline_fill_regions() -> list[WaveRegion]:
    rows = [
        ("of.00", "circle", (360.0, 335.0), 132.0, -0.20, 1, "upper-nodal-band", 0.90, 0.94),
        ("of.01", "crescent", (585.0, 426.0), 168.0, 0.12, -1, "upper-nodal-band", 0.88, 1.02),
        ("of.02", "trigon", (845.0, 368.0), 144.0, 0.26, 1, "upper-nodal-band", 0.86, 0.94),
        ("of.03", "crescent", (1124.0, 476.0), 184.0, -0.05, -1, "upper-nodal-band", 0.88, 1.00),
        ("of.04", "circle", (1432.0, 398.0), 128.0, 0.0, 1, "upper-nodal-band", 0.82, 0.88),
        ("of.05", "trigon", (1608.0, 610.0), 154.0, 0.42, -1, "right-pressure-return", 0.82, 0.94),
        ("of.06", "crescent", (455.0, 665.0), 178.0, -0.32, -1, "lower-nodal-band", 0.86, 1.00),
        ("of.07", "trigon", (730.0, 724.0), 142.0, 0.16, 1, "lower-nodal-band", 0.82, 0.95),
        ("of.08", "circle", (1010.0, 650.0), 150.0, 0.0, -1, "lower-nodal-band", 0.86, 0.90),
        ("of.09", "crescent", (1276.0, 736.0), 172.0, 0.24, 1, "lower-nodal-band", 0.84, 1.04),
        ("of.10", "trigon", (1510.0, 794.0), 142.0, -0.08, -1, "lower-nodal-band", 0.80, 0.96),
        ("of.11", "circle", (885.0, 526.0), 108.0, 0.0, 1, "central-pressure-node", 0.74, 0.88),
        ("of.12", "crescent", (1196.0, 574.0), 136.0, 0.50, -1, "central-pressure-node", 0.74, 1.00),
    ]
    out: list[WaveRegion] = []
    for rank, (rid, primitive, center, size, angle, polarity, wave_id, alpha, aspect) in enumerate(rows):
        out.append(
            WaveRegion(
                region_id=rid,
                clip_key="standing_wave_outline_fill",
                primitive=primitive,
                center=center,
                size=size,
                angle=angle,
                polarity=polarity,
                phase_offset=0.0,
                alpha=alpha,
                role="clean phase-inversion cell: outline -> filled body -> outline -> negative-space inverse",
                parent_wave_id=wave_id,
                debug_rank=rank,
                aspect=aspect,
            )
        )
    return out


OUTLINE_FILL_REGIONS = outline_fill_regions()


def outline_curve(y0: float, amp: float, phase: float, k: float, offset: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(150):
        x = -80.0 + i * (W + 160.0) / 149.0
        y = y0 + amp * math.sin(x * k + offset) + 22.0 * math.sin(x * k * 0.53 - offset * 0.7)
        y += 8.0 * math.sin(TAU * phase + x * 0.002)
        pts.append((x, y))
    return pts


def draw_outline_fill_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    drive = math.cos(TAU * phase)
    line_level = 1.0 - abs(drive)
    paths = [
        outline_curve(312.0, 42.0, phase, 0.0048, 0.10),
        outline_curve(532.0, 54.0, phase, 0.0042, 1.85),
        outline_curve(744.0, 46.0, phase, 0.0046, 3.20),
    ]
    for idx, pts in enumerate(paths):
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.08 + 0.20 * line_level, thickness=7, glow=31)
        draw_path_additive(frame, pts, PALE_BLUE, alpha=0.035 + 0.26 * line_level, thickness=2)
        if idx < 2:
            bridge = [(p[0], (paths[idx][j][1] + paths[idx + 1][j][1]) * 0.5) for j, p in enumerate(pts)]
            draw_path_additive(frame, bridge, DIM_TEAL, alpha=0.035 + 0.11 * line_level, thickness=2)
    if debug:
        draw_text(frame, "stable nodal lanes: large antinodal bodies swap fill/void by phase", (70, 154), DEBUG_RGB, scale=0.38)


def render_standing_wave_outline_fill(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_outline_fill_nodal_field(frame, phase, debug)
    draw_phase_regions(frame, OUTLINE_FILL_REGIONS, phase, debug=debug)
    draw_debug_header(frame, "standing_wave_outline_fill_v002", phase, debug)
    return frame


RADIAL_CENTER = (960.0, 540.0)


def radial_regions() -> list[WaveRegion]:
    out: list[WaveRegion] = [
        WaveRegion(
            region_id="rp.00.origin",
            clip_key="radial_cymatic_pressure_wave",
            primitive="circle",
            center=RADIAL_CENTER,
            size=128.0,
            angle=0.0,
            polarity=1,
            phase_offset=0.0,
            alpha=0.88,
            role="central pressure circle / radial standing-wave origin",
            parent_wave_id="radial-origin",
            debug_rank=0,
            aspect=0.92,
        )
    ]
    rings = [(204.0, 4, 0.02), (348.0, 6, 0.10), (520.0, 7, 0.18)]
    rank = 1
    for ridx, (radius, count, phase_offset) in enumerate(rings):
        for idx in range(count):
            theta = TAU * (idx + 0.28 * ridx) / count + 0.08 * math.sin(idx * 1.7 + ridx)
            rr = radius + 18.0 * math.sin(idx * 0.9 + ridx * 1.2)
            center = (RADIAL_CENTER[0] + math.cos(theta) * rr, RADIAL_CENTER[1] + math.sin(theta) * rr * 0.88)
            primitive = ["crescent", "trigon", "circle", "crescent"][(idx + ridx) % 4]
            if ridx == 2 and idx % 2:
                primitive = "trigon"
            polarity = 1 if (idx + ridx) % 2 == 0 else -1
            size = 112.0 + 15.0 * ridx + 9.0 * math.sin(idx * 0.71)
            out.append(
                WaveRegion(
                    region_id=f"rp.{ridx + 1:02d}.{idx:02d}",
                    clip_key="radial_cymatic_pressure_wave",
                    primitive=primitive,
                    center=center,
                    size=size,
                    angle=theta,
                    polarity=polarity,
                    phase_offset=phase_offset,
                    alpha=0.80 - 0.04 * ridx,
                    role="radial antinode cell: crescent cups center, trigon releases outward, circle holds pressure lobe",
                    parent_wave_id=f"radial-ring-{ridx + 1}",
                    debug_rank=rank if rank <= 15 else 999,
                    aspect=0.92 if primitive == "circle" else 1.0,
                )
            )
            rank += 1
    return out


RADIAL_REGIONS = radial_regions()


def ellipse_ring_points(radius: float, phase: float, wobble: float = 0.0, count: int = 260) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(count):
        a = TAU * i / count
        local = radius + wobble * math.sin(5.0 * a + 0.55 * math.sin(TAU * phase))
        pts.append((RADIAL_CENTER[0] + math.cos(a) * local, RADIAL_CENTER[1] + math.sin(a) * local * 0.88))
    return pts


def radial_dynamic(
    region: WaveRegion,
    phase: float,
    value: float,
) -> tuple[tuple[float, float], float, float, float]:
    if region.region_id.endswith("origin"):
        return region.center, 0.0, region.size * (0.94 + 0.12 * abs(value)), region.aspect
    dx = region.center[0] - RADIAL_CENTER[0]
    dy = (region.center[1] - RADIAL_CENTER[1]) / 0.88
    theta = math.atan2(dy, dx)
    radius = math.hypot(dx, dy)
    lift = 20.0 * value
    center = (RADIAL_CENTER[0] + math.cos(theta) * (radius + lift), RADIAL_CENTER[1] + math.sin(theta) * (radius + lift) * 0.88)
    size = region.size * (0.93 + 0.14 * abs(value))
    return center, theta, size, region.aspect


def draw_radial_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    for idx, (radius, offset) in enumerate([(142.0, 0.00), (248.0, 0.05), (392.0, 0.11), (568.0, 0.18)]):
        line_level = 1.0 - abs(math.cos(TAU * (phase + offset)))
        pts = ellipse_ring_points(radius + 8.0 * math.sin(TAU * (phase + offset)), phase, wobble=7.0 + idx * 2.0)
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.055 + 0.16 * line_level, thickness=6, closed=True, glow=35)
        draw_path_additive(frame, pts, PALE_BLUE, alpha=0.025 + 0.20 * line_level, thickness=2, closed=True)
    for spoke in range(10):
        theta = TAU * (spoke + 0.36) / 10.0 + 0.05 * math.sin(spoke)
        pts = []
        for i in range(18, 74):
            r = i * 8.0
            pts.append(
                (
                    RADIAL_CENTER[0] + math.cos(theta + 0.06 * math.sin(r * 0.011)) * r,
                    RADIAL_CENTER[1] + math.sin(theta + 0.06 * math.sin(r * 0.011)) * r * 0.88,
                )
            )
        draw_path_additive(frame, pts, DIM_TEAL, alpha=0.020 + 0.045 * (1.0 - abs(math.cos(TAU * phase))), thickness=1)
    if debug:
        draw_text(frame, "radial/cymatic pressure: ring phase offsets create an outward fill/inverse exchange", (70, 154), DEBUG_RGB, scale=0.38)


def render_radial_cymatic_pressure_wave(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_radial_nodal_field(frame, phase, debug)
    draw_phase_regions(frame, RADIAL_REGIONS, phase, debug=debug, dynamic=radial_dynamic)
    draw_debug_header(frame, "radial_cymatic_pressure_wave_v002", phase, debug)
    return frame


CURRENT_BANDS = [
    CurrentBand(
        "current-band-0",
        (-150.0, H * 0.27),
        (W * 0.18, H * 0.15),
        (W * 0.55, H * 0.42),
        (W + 120.0, H * 0.25),
        3,
        -28.0,
        0.00,
        0.82,
    ),
    CurrentBand(
        "current-band-1",
        (-120.0, H * 0.43),
        (W * 0.20, H * 0.58),
        (W * 0.62, H * 0.24),
        (W + 140.0, H * 0.50),
        4,
        22.0,
        0.08,
        0.82,
    ),
    CurrentBand(
        "current-band-2",
        (-170.0, H * 0.61),
        (W * 0.19, H * 0.44),
        (W * 0.64, H * 0.80),
        (W + 150.0, H * 0.62),
        3,
        -22.0,
        0.16,
        0.80,
    ),
]


def bezier_point(band: CurrentBand, t: float) -> tuple[float, float]:
    u = 1.0 - t
    return (
        u * u * u * band.p0[0]
        + 3.0 * u * u * t * band.p1[0]
        + 3.0 * u * t * t * band.p2[0]
        + t * t * t * band.p3[0],
        u * u * u * band.p0[1]
        + 3.0 * u * u * t * band.p1[1]
        + 3.0 * u * t * t * band.p2[1]
        + t * t * t * band.p3[1],
    )


def bezier_angle(band: CurrentBand, t: float) -> float:
    u = 1.0 - t
    dx = (
        3.0 * u * u * (band.p1[0] - band.p0[0])
        + 6.0 * u * t * (band.p2[0] - band.p1[0])
        + 3.0 * t * t * (band.p3[0] - band.p2[0])
    )
    dy = (
        3.0 * u * u * (band.p1[1] - band.p0[1])
        + 6.0 * u * t * (band.p2[1] - band.p1[1])
        + 3.0 * t * t * (band.p3[1] - band.p2[1])
    )
    return math.atan2(dy, dx)


def current_band_path(band: CurrentBand, samples: int = 132) -> list[tuple[float, float]]:
    return [bezier_point(band, i / (samples - 1)) for i in range(samples)]


def current_regions() -> list[WaveRegion]:
    out: list[WaveRegion] = []
    rank = 0
    for bidx, band in enumerate(CURRENT_BANDS):
        for idx in range(band.count):
            u = (idx + 0.58 + 0.10 * math.sin(bidx)) / band.count
            angle = bezier_angle(band, u)
            normal = (-math.sin(angle), math.cos(angle))
            base = bezier_point(band, u)
            center = (base[0] + normal[0] * band.normal_offset, base[1] + normal[1] * band.normal_offset)
            primitive = ["circle", "crescent", "trigon", "crescent"][(idx + bidx) % 4]
            polarity = 1 if (idx + bidx) % 2 == 0 else -1
            size = 150.0 + 22.0 * math.sin(idx * 0.9 + bidx)
            out.append(
                WaveRegion(
                    region_id=f"cb.{bidx:02d}.{idx:02d}",
                    clip_key="current_band_phase_inversion",
                    primitive=primitive,
                    center=center,
                    size=size,
                    angle=angle,
                    polarity=polarity,
                    phase_offset=band.phase_offset + u * 0.22,
                    alpha=band.alpha,
                    role="current-band antinode: phase travels along the same band; crescent cups upstream and trigon releases downstream",
                    parent_wave_id=band.band_id,
                    debug_rank=rank if rank <= 15 else 999,
                    aspect=0.90 if primitive == "circle" else 1.0,
                    band_index=bidx,
                    u=u,
                )
            )
            rank += 1
    return out


CURRENT_REGIONS = current_regions()


def current_dynamic(
    region: WaveRegion,
    phase: float,
    value: float,
) -> tuple[tuple[float, float], float, float, float]:
    band = CURRENT_BANDS[region.band_index]
    angle = bezier_angle(band, region.u)
    normal = (-math.sin(angle), math.cos(angle))
    base = bezier_point(band, region.u)
    pressure_lift = 24.0 * value
    center = (
        base[0] + normal[0] * (band.normal_offset + pressure_lift),
        base[1] + normal[1] * (band.normal_offset + pressure_lift),
    )
    size = region.size * (0.92 + 0.15 * abs(value))
    aspect = region.aspect * (0.96 + 0.08 * math.sin(TAU * (phase + region.phase_offset)))
    return center, angle, size, aspect


def draw_current_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    for band in CURRENT_BANDS:
        line_level = 1.0 - abs(math.cos(TAU * (phase + band.phase_offset)))
        pts = current_band_path(band)
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.080 + 0.16 * line_level, thickness=11, glow=39)
        draw_path_additive(frame, pts, PALE_BLUE, alpha=0.035 + 0.22 * line_level, thickness=3)
        for offset in (-68.0, 68.0):
            edge_pts: list[tuple[float, float]] = []
            for i, p in enumerate(pts):
                u = i / max(1, len(pts) - 1)
                a = bezier_angle(band, u)
                normal = (-math.sin(a), math.cos(a))
                edge_pts.append((p[0] + normal[0] * offset, p[1] + normal[1] * offset))
            draw_path_additive(frame, edge_pts, DIM_TEAL, alpha=0.020 + 0.075 * line_level, thickness=2)
    if debug:
        draw_text(frame, "current-band standing wave: phase moves along bands, but every region keeps one parent band", (70, 154), DEBUG_RGB, scale=0.38)


def render_current_band_phase_inversion(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_current_nodal_field(frame, phase, debug)
    draw_phase_regions(frame, CURRENT_REGIONS, phase, debug=debug, dynamic=current_dynamic)
    draw_debug_header(frame, "current_band_phase_inversion_v002", phase, debug)
    return frame


def pressure_lane_regions() -> list[WaveRegion]:
    data = [
        ("pl.00", "circle", (490.0, 520.0), 128.0, 0.0, 1, 0.00, "left-emitter-origin", 0.88, 0.90),
        ("pl.01", "crescent", (705.0, 430.0), 168.0, -0.18, -1, 0.04, "left-top-interference-lane", 0.86, 1.02),
        ("pl.02", "trigon", (875.0, 355.0), 138.0, -0.08, 1, 0.08, "left-top-interference-lane", 0.82, 0.96),
        ("pl.03", "circle", (1050.0, 414.0), 118.0, 0.0, -1, 0.12, "top-emitter-origin", 0.82, 0.88),
        ("pl.04", "crescent", (1234.0, 500.0), 178.0, 0.28, 1, 0.16, "top-right-interference-lane", 0.86, 1.02),
        ("pl.05", "trigon", (1438.0, 596.0), 150.0, 0.38, -1, 0.20, "top-right-interference-lane", 0.82, 0.95),
        ("pl.06", "circle", (1540.0, 725.0), 118.0, 0.0, 1, 0.25, "right-emitter-return", 0.78, 0.92),
        ("pl.07", "crescent", (1138.0, 690.0), 188.0, 2.82, -1, 0.17, "lower-return-lane", 0.84, 1.00),
        ("pl.08", "trigon", (910.0, 742.0), 146.0, 3.00, 1, 0.11, "lower-return-lane", 0.82, 0.96),
        ("pl.09", "crescent", (675.0, 688.0), 170.0, -2.80, -1, 0.05, "lower-return-lane", 0.84, 1.00),
        ("pl.10", "trigon", (810.0, 540.0), 126.0, 0.10, 1, 0.03, "central-pressure-saddle", 0.74, 0.95),
        ("pl.11", "circle", (978.0, 568.0), 106.0, 0.0, -1, 0.10, "central-pressure-saddle", 0.74, 0.88),
        ("pl.12", "crescent", (1115.0, 565.0), 138.0, 0.04, 1, 0.15, "central-pressure-saddle", 0.74, 1.00),
    ]
    out: list[WaveRegion] = []
    for rank, (rid, primitive, center, size, angle, polarity, offset, wave_id, alpha, aspect) in enumerate(data):
        out.append(
            WaveRegion(
                region_id=rid,
                clip_key="multi_emitter_pressure_lanes",
                primitive=primitive,
                center=center,
                size=size,
                angle=angle,
                polarity=polarity,
                phase_offset=offset,
                alpha=alpha,
                role="multi-emitter pressure-lane antinode; state follows emitter phase relation, not random glyph timing",
                parent_wave_id=wave_id,
                debug_rank=rank,
                aspect=aspect,
            )
        )
    return out


PRESSURE_LANE_REGIONS = pressure_lane_regions()


def pressure_dynamic(
    region: WaveRegion,
    phase: float,
    value: float,
) -> tuple[tuple[float, float], float, float, float]:
    sway = 10.0 * math.sin(TAU * (phase + region.phase_offset * 0.7))
    normal = (-math.sin(region.angle), math.cos(region.angle))
    center = (region.center[0] + normal[0] * sway * abs(value), region.center[1] + normal[1] * sway * abs(value))
    size = region.size * (0.93 + 0.14 * abs(value))
    aspect = region.aspect * (0.96 + 0.07 * math.sin(TAU * (phase + region.phase_offset)))
    return center, region.angle, size, aspect


def bridge_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    samples: int = 128,
) -> list[tuple[float, float]]:
    return cubic_curve(p0, p1, p2, p3, samples)


def draw_emitter_rings(frame: np.ndarray, center: tuple[float, float], phase: float, offset: float) -> None:
    for idx, radius in enumerate((116.0, 235.0, 368.0, 520.0)):
        line_level = 1.0 - abs(math.cos(TAU * (phase + offset + idx * 0.04)))
        pts = []
        for j in range(180):
            a = TAU * j / 180.0
            r = radius + 7.0 * math.sin(3.0 * a + idx)
            pts.append((center[0] + math.cos(a) * r, center[1] + math.sin(a) * r * 0.88))
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.020 + 0.080 * line_level, thickness=5, closed=True, glow=27)
        draw_path_additive(frame, pts, PALE_BLUE, alpha=0.012 + 0.090 * line_level, thickness=1, closed=True)


def draw_pressure_lane_nodal_field(frame: np.ndarray, phase: float, debug: bool) -> None:
    emitters = [((490.0, 520.0), 0.00), ((1050.0, 414.0), 0.12), ((1540.0, 725.0), 0.24)]
    for center, offset in emitters:
        draw_emitter_rings(frame, center, phase, offset)
    bridges = [
        ((490.0, 520.0), (670.0, 330.0), (910.0, 270.0), (1050.0, 414.0), 0.02),
        ((1050.0, 414.0), (1215.0, 455.0), (1370.0, 540.0), (1540.0, 725.0), 0.12),
        ((1540.0, 725.0), (1260.0, 820.0), (855.0, 840.0), (490.0, 520.0), 0.21),
        ((700.0, 430.0), (860.0, 530.0), (1040.0, 590.0), (1234.0, 500.0), 0.08),
    ]
    for p0, p1, p2, p3, offset in bridges:
        line_level = 1.0 - abs(math.cos(TAU * (phase + offset)))
        pts = bridge_curve(p0, p1, p2, p3)
        draw_path_additive(frame, pts, DEEP_TEAL, alpha=0.055 + 0.16 * line_level, thickness=9, glow=37)
        draw_path_additive(frame, pts, PALE_BLUE, alpha=0.025 + 0.20 * line_level, thickness=2)
    if debug:
        draw_text(frame, "multi-emitter pressure lanes: three coherent sources create bridge cells and central saddle cells", (70, 154), DEBUG_RGB, scale=0.38)


def render_multi_emitter_pressure_lanes(fi: int, debug: bool = False) -> np.ndarray:
    frame = canvas()
    phase = fi / N_FRAMES
    draw_pressure_lane_nodal_field(frame, phase, debug)
    draw_phase_regions(frame, PRESSURE_LANE_REGIONS, phase, debug=debug, dynamic=pressure_dynamic)
    draw_debug_header(frame, "multi_emitter_pressure_lanes_v002", phase, debug)
    return frame


CLIPS: list[ClipSpec] = [
    ClipSpec(
        key="standing_wave_outline_fill",
        filename="standing_wave_outline_fill_v002.mp4",
        title="Standing Wave Outline Fill v002",
        description="Clean phase-inversion demonstration: large primitive regions pass through outline, fill, outline, and inverse negative-space states.",
        renderer=render_standing_wave_outline_fill,
        regions=lambda: OUTLINE_FILL_REGIONS,
    ),
    ClipSpec(
        key="radial_cymatic_pressure_wave",
        filename="radial_cymatic_pressure_wave_v002.mp4",
        title="Radial Cymatic Pressure Wave v002",
        description="Radial pressure rings drive circle/crescent/trigon antinodes without seed/flower topology construction.",
        renderer=render_radial_cymatic_pressure_wave,
        regions=lambda: RADIAL_REGIONS,
    ),
    ClipSpec(
        key="current_band_phase_inversion",
        filename="current_band_phase_inversion_v002.mp4",
        title="Current Band Phase Inversion v002",
        description="Sinuous current bands hold larger primitive bodies; phase moves along each band with common fate.",
        renderer=render_current_band_phase_inversion,
        regions=lambda: CURRENT_REGIONS,
    ),
    ClipSpec(
        key="multi_emitter_pressure_lanes",
        filename="multi_emitter_pressure_lanes_v002.mp4",
        title="Multi-Emitter Pressure Lanes v002",
        description="Three coherent pressure sources create bridge/saddle cells that invert through wave phase.",
        renderer=render_multi_emitter_pressure_lanes,
        regions=lambda: PRESSURE_LANE_REGIONS,
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
    stem = Path(spec.filename).stem
    for fi in range(N_FRAMES):
        frame = spec.renderer(fi, False)
        writer.write(frame)
        if fi in sample_frames:
            save_png(SAMPLE_DIR / f"{stem}_f{fi:03d}.png", frame)
        if (fi + 1) % 48 == 0:
            print(f"  {spec.filename}: {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    save_png(STILLS_DIR / f"{stem}_midpoint_f{MID_FRAME:03d}.png", spec.renderer(MID_FRAME, False))
    save_png(STILLS_DIR / f"{stem}_debug_midpoint_f{MID_FRAME:03d}.png", spec.renderer(MID_FRAME, True))


def build_contact_sheet() -> Path:
    frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    labels = ["f000 phase A", "f036 outline", "f072 inverse/debug", "f108 outline", "f143 return"]
    cell_w, cell_h = 320, 180
    label_w, label_h = 355, 58
    sheet = np.zeros((label_h + len(CLIPS) * cell_h, label_w + len(frames) * cell_w, 3), dtype=np.uint8)
    draw_text(sheet, "primitive standing-wave field v002", (16, 36), LABEL_RGB, scale=0.42)
    for col, label in enumerate(labels):
        draw_text(sheet, label, (label_w + col * cell_w + 12, 36), LABEL_RGB, scale=0.37)
    for row, spec in enumerate(CLIPS):
        y0 = label_h + row * cell_h
        draw_text(sheet, Path(spec.filename).stem, (16, y0 + 34), LABEL_RGB, scale=0.34)
        for col, fi in enumerate(frames):
            debug = fi == MID_FRAME
            thumb = cv2.resize(spec.renderer(fi, debug), (cell_w, cell_h), interpolation=cv2.INTER_AREA)
            x0 = label_w + col * cell_w
            sheet[y0 : y0 + cell_h, x0 : x0 + cell_w] = thumb
            cv2.rectangle(sheet, (x0, y0), (x0 + cell_w - 1, y0 + cell_h - 1), (42, 56, 56), 1)
    out = OUT_DIR / "primitive_standing_wave_field_v002_contact_sheet.png"
    save_png(out, sheet)
    return out


def primitive_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for spec in CLIPS:
        for region in spec.regions():
            records.append(
                {
                    "region_id": region.region_id,
                    "clip_key": region.clip_key,
                    "primitive": region.primitive,
                    "role": region.role,
                    "parent_wave_id": region.parent_wave_id,
                    "center": [round(region.center[0], 2), round(region.center[1], 2)],
                    "rotation_degrees": round(math.degrees(region.angle), 2),
                    "size": round(region.size, 2),
                    "aspect": round(region.aspect, 3),
                    "polarity_family": "positive-antinode" if region.polarity > 0 else "negative-antinode",
                    "phase_offset": round(region.phase_offset, 4),
                    "state_mapping": {
                        "same_sign_phase": "filled primitive body",
                        "zero_crossing": "outline / nodal boundary",
                        "opposite_phase": "negative-space cutout with visible edge; complementary polarity may fill",
                    },
                    "curvature_direction": "crescent cups local origin/upstream/center; trigon points along declared release or radial/current tangent",
                    "cultural_status": "internal grammar-inspired sketch; not Austin-approved; not public; not a cultural meaning claim",
                }
            )
    return records


def write_manifest(contact_sheet: Path) -> Path:
    manifest = {
        "renderer": "scripts/primitive_standing_wave_field_v002.py",
        "created": "2026-05-20",
        "status": "INTERNAL ONLY. Not Austin-approved. Not public-ready. Not a cultural meaning claim.",
        "technical": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frames": N_FRAMES,
            "background": "black-screen additive primitive field with negative-space cutouts",
            "phase_model": "stable nodal lines plus antinodal regions; display state is fill -> outline -> inverse/void -> outline",
        },
        "v002_correction": [
            "Fewer larger antinodal regions replace v001's small repeated glyph marks.",
            "Every visible region has a parent nodal band, ring, current band, or pressure lane.",
            "Phase state controls outline/fill/void; no random per-glyph cycle timing is used.",
            "No topology/seed-of-life extraction and no footage-derived motion.",
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
                "region_count": len(spec.regions()),
            }
            for spec in CLIPS
        ],
        "primitive_records": primitive_records(),
        "constraints": [
            "No decorative scatter/grid of independent icons.",
            "No topology, seed, flower, rosette, or mandala construction.",
            "No fish, animals, figures, SD, LoRA, Austin source artwork, or source-piece replication.",
            "Austin review is required before any public or external use.",
        ],
    }
    out = OUT_DIR / "primitive_standing_wave_field_v002_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out


def write_readme(contact_sheet: Path, manifest: Path) -> None:
    lines = [
        "# Primitive Standing-Wave Field v002 - 2026-05-20",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved, not public-ready, and not a cultural meaning claim.",
        "",
        "This packet is a fresh standing-wave / phase-inversion primitive field pass. It is separate from topology/seed extraction and separate from footage-derived motion work.",
        "",
        "The v002 correction is scale and causality: larger antinodal regions are attached to visible nodal bands, rings, current bands, or pressure lanes. The regions do not run independent icon cycles. Each region's visible state is explained by wave phase: filled primitive body, outline at zero crossing, or negative-space inverse.",
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
            "- Positive antinode family: filled body during same-sign phase, outline at zero crossing, negative-space cutout during opposite phase.",
            "- Negative antinode family: complementary fill/void timing, using the same oscillator.",
            "- Nodal bands/rings/lanes remain visible as stable outline/membrane guides and grow strongest near zero crossings.",
            "- Local offsets in the radial/current/multi-emitter clips create coherent pressure movement through the field without random timing.",
            "",
            "## Boundaries",
            "",
            "- No topology, seed, flower, rosette, or mandala construction.",
            "- No footage-derived motion, optical flow, fish, animals, SD, LoRA, Austin source art, or source-piece replication.",
            "- No claim is made about public cultural meaning, Austin authorship, Austin approval, or traditional significance.",
            "- Austin review is required before any public or external use.",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering primitive standing-wave field v002 packet to {OUT_DIR}", flush=True)
    for spec in CLIPS:
        render_clip(spec)
    contact_sheet = build_contact_sheet()
    manifest = write_manifest(contact_sheet)
    write_readme(contact_sheet, manifest)
    print(f"Done: {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
