#!/usr/bin/env python3.11
"""
Radial sacred-geometry primitive morphology v001.

Internal geometric exploration only. The phrase "sacred geometry" is treated
as a general radial/ornamental geometry prompt here, not as a cultural or
ceremonial claim.
"""
from __future__ import annotations

import math
import subprocess
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT, draw_poly_alpha
from radial_water_sun_snowflake_morphology_v001 import trigon_points


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/radial_sacred_geometry_primitive_morphology_v001_2026-05-20"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
W = 1920
H = 1080
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)

BLACK = (0, 0, 0)
IVORY = (244, 244, 236)
SOFT_IVORY = (224, 232, 228)
PALE_BLUE = (168, 220, 238)
ICE_BLUE = (202, 238, 248)
DEEP_TEAL = (76, 126, 136)
MIST = (145, 164, 162)
SUN_GOLD = (246, 213, 116)
SUN_AMBER = (232, 162, 78)


class H264Writer:
    def __init__(self, path: Path, *, fps: int = FPS, size: tuple[int, int] = (W, H)):
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

    def write(self, frame_bgr: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(frame_bgr.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with exit code {rc}")


def canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)


def blend_local_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    rgb: tuple[int, int, int],
    alpha: float,
) -> None:
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    a = (mask.astype(np.float32) / 255.0) * max(0.0, min(1.0, alpha))
    if not np.any(a > 0):
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = rgb_to_bgr(rgb)
    crop[:] = crop * (1.0 - a[..., None]) + color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def transform_points(base: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float) -> np.ndarray:
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


def point(origin: tuple[float, float], angle: float, distance: float) -> tuple[float, float]:
    return (origin[0] + math.cos(angle) * distance, origin[1] + math.sin(angle) * distance)


def radial_angles(count: int, *, start: float = 0.0) -> list[float]:
    return [start + 2.0 * math.pi * i / count for i in range(count)]


def phase_wave(phase: float, offset: float = 0.0) -> float:
    return 0.5 + 0.5 * math.sin(2.0 * math.pi * ((phase + offset) % 1.0))


def draw_poly(frame: np.ndarray, pts: np.ndarray, rgb: tuple[int, int, int], *, alpha: float) -> None:
    draw_poly_alpha(frame, pts.astype(np.float32), rgb, alpha=alpha, outline_alpha=0.0, outline_thickness=0)


def draw_circle(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    r = max(1, round(radius))
    pad = r + 5
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r, 255, -1, lineType=cv2.LINE_AA)
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_oval(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    rx, ry = max(1, round(axes[0])), max(1, round(axes[1]))
    pad = max(rx, ry) + 6
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (cx - x0, cy - y0),
        (rx, ry),
        math.degrees(angle),
        0,
        360,
        255,
        -1,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_ring(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    thickness: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    r = max(1, round(radius))
    thick = max(1, round(thickness))
    pad = r + thick + 6
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r, 255, thick, lineType=cv2.LINE_AA)
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_oval_ring(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    thickness: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    rx, ry = max(1, round(axes[0])), max(1, round(axes[1]))
    thick = max(1, round(thickness))
    pad = max(rx, ry) + thick + 7
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (cx - x0, cy - y0),
        (rx, ry),
        math.degrees(angle),
        0,
        360,
        255,
        thick,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_arc(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    start: float,
    end: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    rx, ry = max(1, round(axes[0])), max(1, round(axes[1]))
    thick = max(1, round(thickness))
    pad = max(rx, ry) + thick + 7
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (cx - x0, cy - y0),
        (rx, ry),
        math.degrees(angle),
        math.degrees(start),
        math.degrees(end),
        255,
        thick,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_line(frame: np.ndarray, pts: list[tuple[float, float]], rgb: tuple[int, int, int], *, alpha: float, thickness: float) -> None:
    if len(pts) < 2:
        return
    arr = np.round(np.array(pts, dtype=np.float32)).astype(np.int32)
    pad = int(max(6, thickness + 6))
    x0 = max(0, int(arr[:, 0].min()) - pad)
    y0 = max(0, int(arr[:, 1].min()) - pad)
    x1 = min(W, int(arr[:, 0].max()) + pad + 1)
    y1 = min(H, int(arr[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = arr.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.polylines(mask, [local], False, 255, max(1, round(thickness)), cv2.LINE_AA)
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    draw_poly(frame, transform_points(CRESCENT_BASE, center, sx, sy, angle), rgb, alpha=alpha)


def draw_crescent_cupping(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    angle_to_origin = math.atan2(origin[1] - center[1], origin[0] - center[0])
    draw_crescent(frame, center, sx, sy, angle_to_origin - math.pi, rgb, alpha=alpha)


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.55,
    softness: float = 0.45,
) -> None:
    base = trigon_points(sharpness=sharpness, softness=softness)
    draw_poly(frame, transform_points(base, center, sx, sy, angle), rgb, alpha=alpha)


def draw_trigon_release(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.55,
    softness: float = 0.45,
) -> None:
    angle = math.atan2(center[1] - origin[1], center[0] - origin[0])
    draw_trigon(frame, center, sx, sy, angle, rgb, alpha=alpha, sharpness=sharpness, softness=softness)


def draw_s_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    size: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    # Built from two opposing crescent primitives so it remains in the grammar.
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    first = (center[0] - dx * size * 0.24 + px * size * 0.17, center[1] - dy * size * 0.24 + py * size * 0.17)
    second = (center[0] + dx * size * 0.24 - px * size * 0.17, center[1] + dy * size * 0.24 - py * size * 0.17)
    draw_crescent(frame, first, size * 0.58, size * 0.38, angle, rgb, alpha=alpha)
    draw_crescent(frame, second, size * 0.58, size * 0.38, angle + math.pi, rgb, alpha=alpha * 0.88)


def draw_haze(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
    draw_circle(frame, center, radius, rgb, alpha=alpha * 0.22)
    draw_ring(frame, center, radius * 0.72, 4, rgb, alpha=alpha * 0.52)
    draw_ring(frame, center, radius, 3, rgb, alpha=alpha * 0.40)


def radial_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    angle: float,
    *,
    distances: tuple[float, float, float] = (180, 320, 470),
    scale: float = 1.0,
    rgb: tuple[int, int, int] = IVORY,
    trigon_rgb: tuple[int, int, int] | None = None,
    alpha: float = 0.8,
    crescent_ratio: tuple[float, float] = (0.95, 1.10),
    sharpness: float = 0.58,
    softness: float = 0.48,
) -> None:
    c1 = point(origin, angle, distances[0])
    c2 = point(origin, angle, distances[1])
    tri = point(origin, angle, distances[2])
    draw_crescent_cupping(frame, c1, origin, 98 * scale * crescent_ratio[0], 66 * scale, rgb, alpha=alpha * 0.92)
    draw_crescent_cupping(frame, c2, origin, 124 * scale * crescent_ratio[1], 80 * scale, rgb, alpha=alpha * 0.70)
    draw_trigon_release(
        frame,
        tri,
        origin,
        88 * scale,
        94 * scale,
        trigon_rgb or rgb,
        alpha=alpha * 0.56,
        sharpness=sharpness,
        softness=softness,
    )


def draw_seed_or_flower_circles(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    *,
    count: int = 6,
    ring_radius: float | None = None,
    rgb: tuple[int, int, int] = SOFT_IVORY,
    alpha: float = 0.18,
    thickness: float = 5,
    start: float = 0.0,
) -> None:
    rr = ring_radius if ring_radius is not None else radius
    draw_ring(frame, center, radius, thickness, rgb, alpha=alpha * 1.12)
    for angle in radial_angles(count, start=start):
        draw_ring(frame, point(center, angle, rr), radius, thickness, rgb, alpha=alpha)


def study_01_sun_seed_ray_geometry() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_haze(frame, center, 500, SUN_GOLD, alpha=0.075)
    draw_seed_or_flower_circles(frame, center, 122, count=6, rgb=SUN_GOLD, alpha=0.15, thickness=4)
    draw_circle(frame, center, 86, SUN_GOLD, alpha=0.78)
    draw_circle(frame, center, 42, IVORY, alpha=0.34)
    for angle in radial_angles(8, start=math.radians(7)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(215, 352, 535),
            scale=1.04,
            rgb=IVORY,
            trigon_rgb=SUN_GOLD,
            alpha=0.80,
            sharpness=0.70,
            softness=0.32,
        )
    return frame


def study_02_sun_mandala_negative_crescents() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_circle(frame, center, 282, SUN_GOLD, alpha=0.62)
    for angle in radial_angles(8, start=math.radians(22.5)):
        draw_crescent_cupping(frame, point(center, angle, 190), center, 140, 86, BLACK, alpha=0.94)
    draw_ring(frame, center, 282, 5, IVORY, alpha=0.42)
    draw_ring(frame, center, 120, 10, IVORY, alpha=0.38)
    for angle in radial_angles(8, start=math.radians(0)):
        draw_trigon_release(frame, point(center, angle, 410), center, 96, 118, SUN_AMBER, alpha=0.56, sharpness=0.68, softness=0.34)
        draw_crescent_cupping(frame, point(center, angle, 335), center, 108, 68, IVORY, alpha=0.58)
    return frame


def study_03_ripple_seed_impact_wavefront() -> np.ndarray:
    frame = canvas()
    center = (790.0, 565.0)
    draw_haze(frame, center, 630, PALE_BLUE, alpha=0.052)
    draw_circle(frame, center, 64, IVORY, alpha=0.86)
    for r, a, t in [(148, 0.19, 4), (265, 0.15, 6), (420, 0.10, 4), (605, 0.052, 4)]:
        draw_ring(frame, center, r, t, PALE_BLUE, alpha=a)
    for idx, angle in enumerate([math.radians(-24), math.radians(3), math.radians(30), math.radians(59)]):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(205 + idx * 7, 360 + idx * 22, 560 + idx * 30),
            scale=1.02 - idx * 0.08,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=0.84 - idx * 0.11,
            sharpness=0.48,
            softness=0.72,
        )
    return frame


def study_04_ripple_flower_impact_interference() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for idx, impact in enumerate([center, (790.0, 540.0), (1130.0, 540.0), (960.0, 372.0), (960.0, 708.0)]):
        draw_ring(frame, impact, 170, 4, PALE_BLUE, alpha=0.09 if idx else 0.14)
        draw_ring(frame, impact, 282, 3, PALE_BLUE, alpha=0.045 if idx else 0.07)
        draw_circle(frame, impact, 34 if idx else 48, IVORY, alpha=0.60 if idx else 0.74)
    for angle in radial_angles(6, start=math.radians(30)):
        draw_crescent_cupping(frame, point(center, angle, 235), center, 116, 72, SOFT_IVORY, alpha=0.54)
        draw_trigon_release(frame, point(center, angle, 395), center, 74, 84, MIST, alpha=0.38, sharpness=0.46, softness=0.70)
    return frame


def study_05_snowflake_sixfold_s_crescent() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_haze(frame, center, 455, ICE_BLUE, alpha=0.044)
    draw_ring(frame, center, 96, 12, ICE_BLUE, alpha=0.70)
    for angle in radial_angles(6, start=math.radians(30)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(165, 298, 455),
            scale=0.82,
            rgb=ICE_BLUE,
            trigon_rgb=SOFT_IVORY,
            alpha=0.74,
            crescent_ratio=(0.46, 0.58),
            sharpness=0.82,
            softness=0.24,
        )
        draw_s_crescent(frame, point(center, angle, 285), 98, angle + math.pi / 2.0, ICE_BLUE, alpha=0.42)
    return frame


def study_06_frozen_water_crystal_trigon_lattice() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_or_flower_circles(frame, center, 134, count=6, rgb=ICE_BLUE, alpha=0.12, thickness=4, start=math.radians(30))
    for angle in radial_angles(12, start=math.radians(15)):
        is_long = int(round(math.degrees(angle))) % 60 == 15
        dist = 382 if is_long else 290
        draw_trigon_release(frame, point(center, angle, dist), center, 58 if is_long else 42, 72 if is_long else 54, ICE_BLUE, alpha=0.52 if is_long else 0.32, sharpness=0.86, softness=0.20)
        draw_crescent_cupping(frame, point(center, angle, dist - 100), center, 76 if is_long else 56, 42 if is_long else 34, SOFT_IVORY, alpha=0.38)
    draw_circle(frame, center, 52, IVORY, alpha=0.60)
    draw_circle(frame, center, 25, BLACK, alpha=1.0)
    return frame


def study_07_seed_of_life_circle_crescent_geometry() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_or_flower_circles(frame, center, 164, count=6, rgb=SOFT_IVORY, alpha=0.20, thickness=5)
    draw_circle(frame, center, 58, IVORY, alpha=0.70)
    for angle in radial_angles(6, start=math.radians(30)):
        origin = point(center, angle, 164)
        draw_circle(frame, origin, 32, PALE_BLUE, alpha=0.44)
        draw_crescent_cupping(frame, point(origin, angle, 94), origin, 76, 50, IVORY, alpha=0.54)
        draw_trigon_release(frame, point(origin, angle, 188), origin, 52, 62, PALE_BLUE, alpha=0.36, sharpness=0.58, softness=0.52)
    return frame


def study_08_flower_of_life_water_orbit() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_or_flower_circles(frame, center, 126, count=6, ring_radius=126, rgb=PALE_BLUE, alpha=0.16, thickness=4)
    for angle in radial_angles(12, start=math.radians(15)):
        draw_oval_ring(frame, point(center, angle, 250), (152, 76), angle, 4, PALE_BLUE, alpha=0.080)
    for idx, angle in enumerate(radial_angles(6, start=math.radians(0))):
        draw_crescent_cupping(frame, point(center, angle, 255), center, 132, 80, IVORY, alpha=0.50)
        draw_crescent_cupping(frame, point(center, angle, 342), center, 84, 52, BLACK, alpha=0.80)
        draw_trigon_release(frame, point(center, angle, 456), center, 66, 74, PALE_BLUE if idx % 2 else SOFT_IVORY, alpha=0.40, sharpness=0.50, softness=0.64)
    draw_circle(frame, center, 70, IVORY, alpha=0.56)
    return frame


def study_09_mandala_cupped_crescent_rosette() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_ring(frame, center, 112, 16, IVORY, alpha=0.62)
    draw_ring(frame, center, 236, 4, PALE_BLUE, alpha=0.20)
    for angle in radial_angles(10, start=math.radians(18)):
        draw_crescent_cupping(frame, point(center, angle, 188), center, 132, 76, SOFT_IVORY, alpha=0.62)
        draw_crescent_cupping(frame, point(center, angle, 285), center, 94, 58, PALE_BLUE, alpha=0.36)
    for angle in radial_angles(5, start=math.radians(-18)):
        draw_trigon_release(frame, point(center, angle, 430), center, 76, 88, SUN_GOLD, alpha=0.42, sharpness=0.62, softness=0.40)
    return frame


def study_10_mandala_trigon_corona() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_or_flower_circles(frame, center, 105, count=8, ring_radius=178, rgb=SOFT_IVORY, alpha=0.10, thickness=4, start=math.radians(22.5))
    draw_oval(frame, center, (92, 70), math.radians(-8), SUN_GOLD, alpha=0.62)
    draw_oval(frame, center, (38, 28), math.radians(-8), BLACK, alpha=1.0)
    for angle in radial_angles(16, start=math.radians(11.25)):
        outer = point(center, angle, 372)
        draw_trigon_release(frame, outer, center, 58, 76, SUN_GOLD if int(angle * 100) % 2 else IVORY, alpha=0.42, sharpness=0.78, softness=0.26)
    for angle in radial_angles(8, start=math.radians(22.5)):
        draw_crescent_cupping(frame, point(center, angle, 245), center, 118, 70, SOFT_IVORY, alpha=0.48)
    return frame


def study_11_orbital_oval_field() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for idx, axes in enumerate([(220, 112), (360, 190), (530, 285), (700, 385)]):
        draw_arc(
            frame,
            center,
            axes,
            math.radians(-13 + idx * 4),
            math.radians(205),
            math.radians(338),
            PALE_BLUE,
            alpha=0.15 - idx * 0.026,
            thickness=5 if idx < 2 else 4,
        )
    draw_oval(frame, center, (88, 56), math.radians(-13), IVORY, alpha=0.66)
    for idx, angle in enumerate([math.radians(-8), math.radians(24), math.radians(63), math.radians(123), math.radians(198)]):
        origin = point(center, angle, 132 + idx * 18)
        radial_phrase(
            frame,
            origin,
            angle + math.radians(8),
            distances=(130, 242, 380),
            scale=0.70 + idx * 0.035,
            rgb=SOFT_IVORY,
            trigon_rgb=SUN_GOLD if idx < 2 else PALE_BLUE,
            alpha=0.70 - idx * 0.055,
            sharpness=0.52,
            softness=0.58,
        )
    return frame


def study_12_orbital_oval_nodes_s_crescent() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for idx, angle in enumerate(radial_angles(9, start=math.radians(-20))):
        radius = 310 + 48 * math.sin(idx * 1.7)
        node = point(center, angle, radius)
        draw_oval(frame, node, (50 + 7 * (idx % 3), 31), angle + math.pi / 2.0, PALE_BLUE if idx % 2 else IVORY, alpha=0.50)
        draw_s_crescent(frame, point(center, angle + 0.08, radius + 96), 94, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.48)
        draw_trigon_release(frame, point(center, angle + 0.14, radius + 185), center, 58, 66, MIST, alpha=0.34, sharpness=0.50, softness=0.66)
    draw_ring(frame, center, 124, 9, IVORY, alpha=0.42)
    draw_circle(frame, center, 42, BLACK, alpha=1.0)
    return frame


def study_13_network_radial_reticulation() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    nodes = [point(center, angle, 250 + 55 * math.sin(i * 1.4)) for i, angle in enumerate(radial_angles(8, start=math.radians(8)))]
    for i in range(len(nodes)):
        draw_line(frame, [nodes[i], nodes[(i + 1) % len(nodes)]], DEEP_TEAL, alpha=0.13, thickness=4)
        draw_line(frame, [center, nodes[i]], DEEP_TEAL, alpha=0.08, thickness=3)
    for i, node in enumerate(nodes):
        angle = math.atan2(node[1] - center[1], node[0] - center[0])
        draw_circle(frame, node, 44 if i % 2 == 0 else 32, IVORY if i % 2 == 0 else PALE_BLUE, alpha=0.58)
        draw_crescent_cupping(frame, point(node, angle, 98), node, 72, 48, SOFT_IVORY, alpha=0.50)
        if i % 2 == 0:
            draw_trigon_release(frame, point(node, angle, 184), node, 52, 60, PALE_BLUE, alpha=0.36, sharpness=0.52, softness=0.62)
    draw_circle(frame, center, 62, IVORY, alpha=0.52)
    return frame


def study_14_network_flower_cells_negative_space() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    cell_centers = [center] + [point(center, angle, 172) for angle in radial_angles(6, start=math.radians(30))]
    for c in cell_centers:
        draw_circle(frame, c, 118, PALE_BLUE, alpha=0.20)
    for angle in radial_angles(6, start=math.radians(0)):
        draw_crescent_cupping(frame, point(center, angle, 142), center, 108, 68, BLACK, alpha=0.88)
        draw_crescent_cupping(frame, point(center, angle, 262), center, 92, 56, SOFT_IVORY, alpha=0.42)
    for angle in radial_angles(6, start=math.radians(30)):
        draw_trigon_release(frame, point(center, angle, 396), center, 60, 70, PALE_BLUE, alpha=0.36, sharpness=0.55, softness=0.58)
    draw_ring(frame, center, 286, 4, IVORY, alpha=0.18)
    return frame


def study_15_water_impact_geometry_contraction() -> np.ndarray:
    frame = canvas()
    center = (1030.0, 535.0)
    draw_haze(frame, center, 560, PALE_BLUE, alpha=0.046)
    draw_circle(frame, center, 72, IVORY, alpha=0.76)
    for r, alpha, start in [(190, 0.17, -20), (304, 0.13, 22), (450, 0.08, -8), (615, 0.045, 20)]:
        draw_arc(frame, center, (r, r * 0.62), math.radians(-10), math.radians(start), math.radians(start + 245), PALE_BLUE, alpha=alpha, thickness=5)
    for idx, angle in enumerate([math.radians(160), math.radians(188), math.radians(220), math.radians(254), math.radians(292)]):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(175 + idx * 8, 280 + idx * 18, 420 + idx * 28),
            scale=0.82 - idx * 0.035,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=0.72 - idx * 0.055,
            sharpness=0.46,
            softness=0.74,
        )
    return frame


def study_16_composite_radial_geometry_field() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_or_flower_circles(frame, center, 118, count=6, ring_radius=118, rgb=PALE_BLUE, alpha=0.12, thickness=4, start=math.radians(30))
    draw_ring(frame, center, 252, 4, IVORY, alpha=0.18)
    draw_ring(frame, center, 404, 4, PALE_BLUE, alpha=0.12)
    draw_oval(frame, center, (86, 62), math.radians(16), IVORY, alpha=0.58)
    draw_oval(frame, center, (38, 24), math.radians(16), BLACK, alpha=1.0)
    for idx, angle in enumerate(radial_angles(12, start=math.radians(5))):
        if idx % 3 == 0:
            draw_s_crescent(frame, point(center, angle, 270), 118, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.50)
        elif idx % 3 == 1:
            draw_crescent_cupping(frame, point(center, angle, 246), center, 110, 68, IVORY, alpha=0.46)
        else:
            draw_oval(frame, point(center, angle, 238), (58, 34), angle, PALE_BLUE, alpha=0.40)
        draw_trigon_release(
            frame,
            point(center, angle + 0.035 * math.sin(idx), 468 + 18 * (idx % 2)),
            center,
            60,
            70,
            SUN_GOLD if idx in (0, 1, 11) else PALE_BLUE,
            alpha=0.34,
            sharpness=0.56,
            softness=0.54,
        )
    return frame


STUDIES: list[tuple[str, str, str, Callable[[], np.ndarray]]] = [
    ("01_sun_seed_ray_geometry_v001.png", "sun", "Warm origin with seed-circle geometry and ray/release trigons.", study_01_sun_seed_ray_geometry),
    ("02_sun_mandala_negative_crescents_v001.png", "sun/mandala", "Mandala-like sun disc using black crescent cutouts as deliberate negative space.", study_02_sun_mandala_negative_crescents),
    ("03_ripple_seed_impact_wavefront_v001.png", "ripple", "Single water impact where circles/rings set the origin and crescents/trigons expand outward.", study_03_ripple_seed_impact_wavefront),
    ("04_ripple_flower_impact_interference_v001.png", "ripple/flower", "Multi-impact ripple interference arranged as a restrained flower geometry.", study_04_ripple_flower_impact_interference),
    ("05_snowflake_sixfold_s_crescent_v001.png", "snowflake", "Sixfold frozen-water form using thin crescents, S-crescents, and sharp curved trigons.", study_05_snowflake_sixfold_s_crescent),
    ("06_frozen_water_crystal_trigon_lattice_v001.png", "snowflake", "Frozen-water crystal lattice with specific curved trigons and central negative space.", study_06_frozen_water_crystal_trigon_lattice),
    ("07_seed_of_life_circle_crescent_geometry_v001.png", "seed-of-life", "Seven-circle seed geometry with small circle/crescent/trigon phrases at the outer nodes.", study_07_seed_of_life_circle_crescent_geometry),
    ("08_flower_of_life_water_orbit_v001.png", "flower-of-life", "Flower-of-life circle logic translated into water/orbital phrase movement.", study_08_flower_of_life_water_orbit),
    ("09_mandala_cupped_crescent_rosette_v001.png", "mandala", "Rosette of cupped crescents around a ring origin, with sparse trigon release marks.", study_09_mandala_cupped_crescent_rosette),
    ("10_mandala_trigon_corona_v001.png", "mandala/sun", "Trigon corona around an oval origin, testing ray quality without crude triangles.", study_10_mandala_trigon_corona),
    ("11_orbital_oval_field_v001.png", "orbital field", "Elliptic orbit arcs with phrase units moving along a directional sweep.", study_11_orbital_oval_field),
    ("12_orbital_oval_nodes_s_crescent_v001.png", "orbital field", "Oval nodes, S-crescents, and attenuating trigons in a non-grid orbital field.", study_12_orbital_oval_nodes_s_crescent),
    ("13_network_radial_reticulation_v001.png", "network", "Radial reticulation with large nodes and phrase attachments, avoiding dense wallpaper.", study_13_network_radial_reticulation),
    ("14_network_flower_cells_negative_space_v001.png", "network/flower", "Flower-cell network using positive circles and intentional crescent negative spaces.", study_14_network_flower_cells_negative_space),
    ("15_water_impact_geometry_contraction_v001.png", "water-impact", "Contraction/return-current geometry built from partial arcs and phrase compression.", study_15_water_impact_geometry_contraction),
    ("16_composite_radial_geometry_field_v001.png", "composite", "Shared radial grammar combining seed, orbital, ripple, and mandala readings.", study_16_composite_radial_geometry_field),
]


def render_seed_flower_rotation(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    rotate = phase * math.radians(12)
    pulse = 0.96 + 0.08 * phase_wave(phase)
    draw_haze(frame, center, 510 + 28 * phase_wave(phase), SUN_GOLD, alpha=0.055)
    draw_seed_or_flower_circles(frame, center, 126 * pulse, count=6, rgb=SUN_GOLD, alpha=0.14, thickness=4, start=rotate)
    draw_circle(frame, center, 78 * pulse, SUN_GOLD, alpha=0.62)
    draw_circle(frame, center, 38 * pulse, IVORY, alpha=0.28)
    for idx, angle in enumerate(radial_angles(8, start=math.radians(7) + rotate)):
        local = phase_wave(phase, idx * 0.07)
        radial_phrase(
            frame,
            center,
            angle,
            distances=(210 + 12 * local, 350 + 26 * local, 525 + 40 * local),
            scale=0.96 + 0.05 * local,
            rgb=SOFT_IVORY,
            trigon_rgb=SUN_GOLD,
            alpha=0.58 + 0.08 * local,
            sharpness=0.68,
            softness=0.34,
        )
    return frame


def render_mandala_breathing(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    pulse = 0.94 + 0.10 * phase_wave(phase)
    draw_ring(frame, center, 112 * pulse, 16, IVORY, alpha=0.54)
    draw_ring(frame, center, 238 * pulse, 4, PALE_BLUE, alpha=0.18)
    for idx, angle in enumerate(radial_angles(10, start=math.radians(18))):
        local = phase_wave(phase, idx * 0.05)
        draw_crescent_cupping(frame, point(center, angle, (184 + 10 * local) * pulse), center, 128 * pulse, 74 * pulse, SOFT_IVORY, alpha=0.50 + 0.06 * local)
        draw_crescent_cupping(frame, point(center, angle, (282 + 16 * local) * pulse), center, 94 * pulse, 58 * pulse, PALE_BLUE, alpha=0.32)
    for angle in radial_angles(5, start=math.radians(-18) + math.radians(3) * math.sin(2 * math.pi * phase)):
        draw_trigon_release(frame, point(center, angle, 428 * pulse), center, 76 * pulse, 88 * pulse, SUN_GOLD, alpha=0.38, sharpness=0.62, softness=0.40)
    return frame


def render_orbital_field_phase(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    rotate = phase * math.radians(16)
    for idx, axes in enumerate([(220, 112), (360, 190), (530, 285), (700, 385)]):
        local = phase_wave(phase, idx * 0.09)
        draw_arc(
            frame,
            center,
            (axes[0] + 16 * local, axes[1] + 8 * local),
            math.radians(-13) + rotate * 0.38,
            math.radians(205),
            math.radians(338),
            PALE_BLUE,
            alpha=max(0.035, 0.14 - idx * 0.026),
            thickness=5 if idx < 2 else 4,
        )
    draw_oval(frame, center, (88, 56), math.radians(-13) + rotate * 0.22, IVORY, alpha=0.60)
    for idx, angle in enumerate([math.radians(-8), math.radians(24), math.radians(63), math.radians(123), math.radians(198), math.radians(250)]):
        local = phase_wave(phase, idx * 0.08)
        origin = point(center, angle + rotate * 0.6, 128 + idx * 15 + 10 * local)
        radial_phrase(
            frame,
            origin,
            angle + math.radians(8) + rotate * 0.7,
            distances=(126 + 9 * local, 236 + 18 * local, 370 + 26 * local),
            scale=0.64 + idx * 0.025,
            rgb=SOFT_IVORY,
            trigon_rgb=SUN_GOLD if idx < 2 else PALE_BLUE,
            alpha=0.54 - idx * 0.035 + 0.07 * local,
            sharpness=0.52,
            softness=0.58,
        )
    return frame


def render_water_impact_expansion(phase: float) -> np.ndarray:
    frame = canvas()
    center = (910.0, 548.0)
    wave = phase_wave(phase)
    draw_haze(frame, center, 575 + 40 * wave, PALE_BLUE, alpha=0.042)
    draw_circle(frame, center, 58 + 5 * wave, IVORY, alpha=0.70)
    for idx, base in enumerate([150, 265, 420, 600]):
        local = phase_wave(phase, idx * 0.12)
        draw_ring(frame, center, base + 30 * local, 4 if idx != 1 else 6, PALE_BLUE, alpha=max(0.035, 0.16 - idx * 0.030))
    for idx, angle in enumerate([math.radians(-24), math.radians(3), math.radians(30), math.radians(59)]):
        local = phase_wave(phase, idx * 0.10)
        radial_phrase(
            frame,
            center,
            angle + math.radians(3) * math.sin(2 * math.pi * (phase + idx * 0.04)),
            distances=(200 + 12 * local, 355 + 28 * local, 555 + 44 * local),
            scale=0.96 - idx * 0.05,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=0.62 - idx * 0.06 + 0.08 * local,
            sharpness=0.48,
            softness=0.72,
        )
    return frame


ANIMATIONS: list[tuple[str, str, Callable[[float], np.ndarray]]] = [
    ("17_seed_flower_rotation_v001_black_screen.mp4", "Seed/flower/sun geometry rotating and breathing as one radial field.", render_seed_flower_rotation),
    ("18_mandala_breathing_v001_black_screen.mp4", "Mandala/crescent rosette breathing with restrained trigon release.", render_mandala_breathing),
    ("19_orbital_field_phase_v001_black_screen.mp4", "Orbital field with slow phase-shifted arcs and phrase units.", render_orbital_field_phase),
    ("20_water_impact_expansion_v001_black_screen.mp4", "Water-impact/ripple expansion loop from circle origin through crescents to trigons.", render_water_impact_expansion),
]


def save_contact_sheet(stills: list[tuple[str, np.ndarray]], out_name: str) -> None:
    thumbs: list[np.ndarray] = []
    for idx, (name, frame) in enumerate(stills, start=1):
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, f"{idx:02d} {Path(name).stem[:42]}", (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 232), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    rows = [cv2.hconcat(thumbs[i : i + 4]) for i in range(0, len(thumbs), 4)]
    sheet = cv2.vconcat(rows)
    cv2.imwrite(str(OUT_DIR / out_name), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])


def render_stills() -> list[tuple[str, np.ndarray]]:
    rendered: list[tuple[str, np.ndarray]] = []
    for name, _, _, fn in STUDIES:
        frame = fn()
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        rendered.append((name, frame))
    save_contact_sheet(rendered, "contact_sheet_radial_sacred_geometry_v001.png")
    return rendered


def render_clip(name: str, render_frame: Callable[[float], np.ndarray]) -> np.ndarray:
    writer = H264Writer(OUT_DIR / name)
    midpoint: np.ndarray | None = None
    for fi in range(N_FRAMES):
        phase = fi / N_FRAMES
        frame = render_frame(phase)
        if fi == N_FRAMES // 2:
            midpoint = frame.copy()
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  {name} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    if midpoint is None:
        raise RuntimeError(f"No midpoint captured for {name}")
    return midpoint


def render_animations() -> list[tuple[str, np.ndarray]]:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    midpoints: list[tuple[str, np.ndarray]] = []
    for name, _, fn in ANIMATIONS:
        midpoint = render_clip(name, fn)
        midpoint_name = name.replace(".mp4", "_midpoint.png")
        cv2.imwrite(str(MIDPOINT_DIR / midpoint_name), midpoint, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        midpoints.append((name, midpoint))
    save_contact_sheet(midpoints, "contact_sheet_radial_sacred_geometry_v001_animation_midpoints.png")
    return midpoints


def write_readme() -> None:
    study_lines = []
    for name, family, note, _ in STUDIES:
        study_lines.append(f"### `{name}`\n\nFamily: {family}. {note}\n")

    animation_lines = []
    for name, note, _ in ANIMATIONS:
        animation_lines.append(f"- `{name}`: {note}")

    readme = f"""# Radial Sacred-Geometry Primitive Morphology v001 - 2026-05-20

Status: INTERNAL ONLY. Austin-review-needed. Not Austin-approved, not public, and not a cultural, ceremonial, or general Coast Salish grammar claim.

This packet extends the prior radial water/sun/snowflake morphology work into broader radial geometry: seed-of-life, flower-of-life, mandala, orbital, network, and water-impact forms. The term "sacred geometry" is used only as a design prompt for general mathematical/radial composition. It does not assert that any primitive or arrangement carries cultural meaning.

## Shared Primitive Grammar

- `circle` / `oval`: origin, seed, impact, orbit node, pressure point, or negative-space anchor.
- `crescent`: cupping, phase, wake, petal, orbit segment, or echo of an origin.
- `S-crescent`: built from two crescent primitives; used for rotational/orbital flow without adding a new figurative symbol.
- `trigon`: curved release, ray, attenuation, or point of motion; intentionally not a generic triangle.
- `negative space`: black cutouts used as deliberate voids, channels, or phase gaps.

The same grammar can lean toward sun, ripple, frozen water, seed/flower geometry, mandala, network, or orbital field through proportion, symmetry, palette, spacing, and positive/negative space. This is geometric exploration only.

## Contents

- 16 PNG stills at 1920x1080.
- 4 optional 6s black-screen H.264 animation loops at 1920x1080, 24 fps.
- Still contact sheet: `contact_sheet_radial_sacred_geometry_v001.png`.
- Animation midpoint contact sheet: `contact_sheet_radial_sacred_geometry_v001_animation_midpoints.png`.
- Midpoint stills in `midpoint_stills/`.

Renderer:

`scripts/radial_sacred_geometry_primitive_morphology_v001.py`

## Still Studies

{chr(10).join(study_lines)}
## Optional Animation Loops

{chr(10).join(animation_lines)}

## Review Questions

- Which radial geometry families feel strongest as a shared primitive morphology: sun, ripple, snowflake, seed/flower geometry, mandala, network, or orbital field?
- Do the S-crescents help imply rotation/flow while staying inside the primitive grammar?
- Are the trigons now specific and beautiful enough, or do any still read as generic triangles?
- Which negative-space moves should be retained before another animation pass?
- Which studies feel useful as projection layers over water footage without claiming cultural meaning?

## Caveats

- These are large, sparse geometric studies, not an Austin-approved vocabulary.
- Flower-of-life, seed-of-life, mandala, and "sacred geometry" language is descriptive of mathematical layout only.
- The packet is still black-screen/Add-or-Screen-friendly; it has not yet been composited over footage.
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    render_stills()
    render_animations()
    write_readme()
    print(f"Wrote radial sacred-geometry primitive morphology v001 packet to {OUT_DIR}")


if __name__ == "__main__":
    main()
