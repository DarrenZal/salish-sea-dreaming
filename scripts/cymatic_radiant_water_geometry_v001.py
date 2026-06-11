#!/usr/bin/env python3.11
"""
Cymatic / radiant water geometry v001.

Internal deterministic exploration of primitive topology classes:
circle = one closed boundary; crescent/lens/S-crescent = two-arc class;
trigon = three-sided / three-arc / triangular release cell.
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


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20"
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
MIST = (145, 164, 162)
DEEP_TEAL = (70, 118, 130)
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


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
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
    cv2.ellipse(mask, (cx - x0, cy - y0), (rx, ry), math.degrees(angle), 0, 360, 255, -1, lineType=cv2.LINE_AA)
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_ring(frame: np.ndarray, center: tuple[float, float], radius: float, thickness: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
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
    cv2.ellipse(mask, (cx - x0, cy - y0), (rx, ry), math.degrees(angle), 0, 360, 255, thick, lineType=cv2.LINE_AA)
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


def lens_points(samples: int = 48) -> np.ndarray:
    upper: list[tuple[float, float]] = []
    lower: list[tuple[float, float]] = []
    for i in range(samples + 1):
        t = i / samples
        x = -1.0 + 2.0 * t
        y = -math.sin(math.pi * t)
        upper.append((x, y))
        lower.append((x, -y))
    return np.array(upper + list(reversed(lower)), dtype=np.float32)


def draw_lens(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    draw_poly(frame, transform_points(lens_points(), center, sx, sy, angle), rgb, alpha=alpha)


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


def draw_s_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    size: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    first = (center[0] - dx * size * 0.24 + px * size * 0.17, center[1] - dy * size * 0.24 + py * size * 0.17)
    second = (center[0] + dx * size * 0.24 - px * size * 0.17, center[1] + dy * size * 0.24 - py * size * 0.17)
    draw_crescent(frame, first, size * 0.58, size * 0.38, angle, rgb, alpha=alpha)
    draw_crescent(frame, second, size * 0.58, size * 0.38, angle + math.pi, rgb, alpha=alpha * 0.86)


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.56,
    softness: float = 0.50,
) -> None:
    draw_poly(frame, transform_points(trigon_points(sharpness=sharpness, softness=softness), center, sx, sy, angle), rgb, alpha=alpha)


def draw_trigon_release(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.56,
    softness: float = 0.50,
) -> None:
    angle = math.atan2(center[1] - origin[1], center[0] - origin[0])
    draw_trigon(frame, center, sx, sy, angle, rgb, alpha=alpha, sharpness=sharpness, softness=softness)


def draw_haze(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
    draw_circle(frame, center, radius, rgb, alpha=alpha * 0.20)
    draw_ring(frame, center, radius * 0.70, 4, rgb, alpha=alpha * 0.48)
    draw_ring(frame, center, radius, 3, rgb, alpha=alpha * 0.36)


def draw_topology_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    angle: float,
    *,
    distances: tuple[float, float, float] = (170, 300, 440),
    scale: float = 1.0,
    rgb: tuple[int, int, int] = SOFT_IVORY,
    trigon_rgb: tuple[int, int, int] = PALE_BLUE,
    alpha: float = 0.70,
) -> None:
    draw_crescent_cupping(frame, point(origin, angle, distances[0]), origin, 92 * scale, 62 * scale, rgb, alpha=alpha * 0.90)
    draw_lens(frame, point(origin, angle, distances[1]), 82 * scale, 34 * scale, angle, rgb, alpha=alpha * 0.56)
    draw_trigon_release(frame, point(origin, angle, distances[2]), origin, 74 * scale, 82 * scale, trigon_rgb, alpha=alpha * 0.50, sharpness=0.58, softness=0.54)


def draw_seed_circles(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    *,
    ring_radius: float | None = None,
    count: int = 6,
    start: float = 0.0,
    rgb: tuple[int, int, int] = PALE_BLUE,
    alpha: float = 0.13,
    thickness: float = 4,
) -> None:
    rr = radius if ring_radius is None else ring_radius
    draw_ring(frame, center, radius, thickness, rgb, alpha=alpha * 1.12)
    for angle in radial_angles(count, start=start):
        draw_ring(frame, point(center, angle, rr), radius, thickness, rgb, alpha=alpha)


def nodal_curve(
    center: tuple[float, float],
    *,
    amp: float,
    y_offset: float,
    width: float = 1320,
    samples: int = 160,
    phase: float = 0.0,
) -> list[tuple[float, float]]:
    pts = []
    for i in range(samples):
        u = i / (samples - 1)
        x = center[0] - width * 0.5 + width * u
        y = center[1] + y_offset + amp * math.sin(2.0 * math.pi * (u * 2.0 + phase)) * math.sin(math.pi * u)
        pts.append((x, y))
    return pts


def study_01_raindrop_interference() -> np.ndarray:
    frame = canvas()
    centers = [(695.0, 545.0), (960.0, 505.0), (1225.0, 570.0)]
    for idx, center in enumerate(centers):
        draw_circle(frame, center, 42, IVORY, alpha=0.68)
        for r, a in [(118, 0.18), (225, 0.13), (360, 0.075), (520, 0.038)]:
            draw_ring(frame, center, r + idx * 8, 4, PALE_BLUE, alpha=a)
    for idx, angle in enumerate([math.radians(-20), math.radians(18), math.radians(52), math.radians(155)]):
        draw_topology_phrase(frame, centers[idx % 3], angle, distances=(145, 250, 385), scale=0.74, alpha=0.58)
    return frame


def study_02_radial_wave_interference_cells() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_haze(frame, center, 580, PALE_BLUE, alpha=0.052)
    for angle in radial_angles(6, start=math.radians(30)):
        c = point(center, angle, 188)
        draw_circle(frame, c, 30, IVORY, alpha=0.54)
        for r, a in [(120, 0.12), (235, 0.070), (350, 0.040)]:
            draw_ring(frame, c, r, 4, PALE_BLUE, alpha=a)
        draw_lens(frame, point(center, angle, 100), 64, 26, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.42)
    draw_circle(frame, center, 56, IVORY, alpha=0.62)
    return frame


def study_03_seed_decomposed_lunes_trigons() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_circles(frame, center, 158, rgb=PALE_BLUE, alpha=0.13, thickness=4)
    draw_circle(frame, center, 60, IVORY, alpha=0.60)
    for idx, angle in enumerate(radial_angles(6, start=math.radians(30))):
        draw_lens(frame, point(center, angle, 122), 86, 34, angle, SOFT_IVORY, alpha=0.54)
        draw_crescent_cupping(frame, point(center, angle, 214), center, 96, 58, IVORY, alpha=0.46)
        draw_trigon_release(frame, point(center, angle, 318), center, 56, 64, PALE_BLUE if idx % 2 else MIST, alpha=0.38, sharpness=0.54, softness=0.62)
    return frame


def study_04_seed_triangular_gap_cells() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_circles(frame, center, 142, rgb=SOFT_IVORY, alpha=0.12, thickness=5, start=math.radians(30))
    for angle in radial_angles(6, start=math.radians(0)):
        draw_trigon_release(frame, point(center, angle, 118), center, 58, 64, BLACK, alpha=1.0, sharpness=0.48, softness=0.80)
        draw_trigon_release(frame, point(center, angle, 238), center, 74, 84, PALE_BLUE, alpha=0.34, sharpness=0.50, softness=0.68)
        draw_crescent_cupping(frame, point(center, angle, 186), center, 82, 52, IVORY, alpha=0.42)
    draw_ring(frame, center, 320, 4, PALE_BLUE, alpha=0.10)
    return frame


def study_05_flower_water_orbit_field() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_circles(frame, center, 118, ring_radius=118, rgb=PALE_BLUE, alpha=0.14, thickness=4)
    draw_seed_circles(frame, center, 118, ring_radius=236, count=12, start=math.radians(15), rgb=DEEP_TEAL, alpha=0.055, thickness=3)
    for idx, angle in enumerate(radial_angles(12, start=math.radians(15))):
        draw_oval_ring(frame, point(center, angle, 304), (128, 58), angle, 4, PALE_BLUE, alpha=0.070)
        if idx % 2 == 0:
            draw_lens(frame, point(center, angle, 242), 82, 30, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.42)
        else:
            draw_s_crescent(frame, point(center, angle, 260), 88, angle + math.pi / 2.0, IVORY, alpha=0.36)
    draw_circle(frame, center, 62, IVORY, alpha=0.54)
    return frame


def study_06_flower_orbit_trigon_release() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_seed_circles(frame, center, 132, ring_radius=132, rgb=PALE_BLUE, alpha=0.11, thickness=4)
    for idx, angle in enumerate(radial_angles(8, start=math.radians(22.5))):
        draw_crescent_cupping(frame, point(center, angle, 220), center, 126, 74, SOFT_IVORY, alpha=0.48)
        draw_trigon_release(frame, point(center, angle, 392), center, 78, 92, SUN_GOLD if idx in (0, 1, 7) else PALE_BLUE, alpha=0.42, sharpness=0.64, softness=0.42)
    draw_ring(frame, center, 92, 16, IVORY, alpha=0.52)
    draw_circle(frame, center, 35, BLACK, alpha=1.0)
    return frame


def study_07_cymatic_standing_wave_field() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for i, yoff in enumerate([-245, -145, -52, 52, 145, 245]):
        pts = nodal_curve(center, amp=58 - abs(yoff) * 0.08, y_offset=yoff, phase=i * 0.12)
        draw_line(frame, pts, PALE_BLUE, alpha=0.12 if i in (2, 3) else 0.075, thickness=5)
    for i, x in enumerate([600, 780, 960, 1140, 1320]):
        for j, y in enumerate([360, 460, 560, 660, 760]):
            if (i + j) % 2 == 0:
                draw_lens(frame, (x, y), 54, 20, math.radians(18 * (i - j)), SOFT_IVORY, alpha=0.30)
            else:
                draw_trigon(frame, (x, y), 34, 42, math.radians(90 + 12 * (i + j)), PALE_BLUE, alpha=0.25, sharpness=0.56, softness=0.60)
    draw_circle(frame, center, 48, IVORY, alpha=0.46)
    return frame


def study_08_cymatic_node_activation() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for angle in radial_angles(8, start=math.radians(22.5)):
        draw_arc(frame, center, (390, 155), angle, math.radians(205), math.radians(334), PALE_BLUE, alpha=0.10, thickness=5)
    for idx, angle in enumerate(radial_angles(16, start=math.radians(11.25))):
        dist = 205 + 120 * (idx % 2)
        node = point(center, angle, dist)
        if idx % 4 == 0:
            draw_circle(frame, node, 32, IVORY, alpha=0.46)
        elif idx % 4 == 1:
            draw_lens(frame, node, 58, 22, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.34)
        elif idx % 4 == 2:
            draw_crescent_cupping(frame, node, center, 70, 44, PALE_BLUE, alpha=0.34)
        else:
            draw_trigon_release(frame, node, center, 42, 50, PALE_BLUE, alpha=0.31, sharpness=0.50, softness=0.68)
    return frame


def study_09_snowflake_sixfold_fractal() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_ring(frame, center, 88, 12, ICE_BLUE, alpha=0.58)
    for angle in radial_angles(6, start=math.radians(30)):
        draw_topology_phrase(frame, center, angle, distances=(150, 278, 430), scale=0.78, rgb=ICE_BLUE, trigon_rgb=SOFT_IVORY, alpha=0.70)
        branch = point(center, angle, 280)
        for sign in (-1, 1):
            ba = angle + sign * math.radians(36)
            draw_lens(frame, point(branch, ba, 82), 48, 18, ba, ICE_BLUE, alpha=0.32)
            draw_trigon_release(frame, point(branch, ba, 154), branch, 36, 44, ICE_BLUE, alpha=0.28, sharpness=0.82, softness=0.24)
    return frame


def study_10_sun_circle_trigon_crescent_rays() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_haze(frame, center, 500, SUN_GOLD, alpha=0.070)
    draw_circle(frame, center, 118, SUN_GOLD, alpha=0.64)
    draw_circle(frame, center, 58, IVORY, alpha=0.28)
    for angle in radial_angles(12, start=math.radians(15)):
        draw_crescent_cupping(frame, point(center, angle, 220), center, 112, 66, IVORY, alpha=0.48)
        draw_lens(frame, point(center, angle, 318), 66, 24, angle, SOFT_IVORY, alpha=0.35)
        draw_trigon_release(frame, point(center, angle, 448), center, 72, 88, SUN_GOLD, alpha=0.42, sharpness=0.76, softness=0.28)
    return frame


def study_11_network_primitive_cells() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    nodes = [point(center, angle, 260 + 38 * math.sin(i * 1.4)) for i, angle in enumerate(radial_angles(9, start=math.radians(-10)))]
    for i in range(len(nodes)):
        draw_line(frame, [nodes[i], nodes[(i + 1) % len(nodes)]], DEEP_TEAL, alpha=0.13, thickness=4)
        draw_line(frame, [center, nodes[i]], DEEP_TEAL, alpha=0.075, thickness=3)
    for i, node in enumerate(nodes):
        angle = math.atan2(node[1] - center[1], node[0] - center[0])
        if i % 3 == 0:
            draw_circle(frame, node, 42, IVORY, alpha=0.48)
        elif i % 3 == 1:
            draw_lens(frame, node, 60, 24, angle, SOFT_IVORY, alpha=0.42)
        else:
            draw_trigon_release(frame, node, center, 46, 54, PALE_BLUE, alpha=0.36, sharpness=0.52, softness=0.64)
    draw_circle(frame, center, 58, IVORY, alpha=0.48)
    return frame


def study_12_chladni_nodal_line_activation() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for idx, axes in enumerate([(700, 210), (520, 340), (365, 470)]):
        draw_arc(frame, center, axes, math.radians(idx * 28 - 18), math.radians(16), math.radians(344), PALE_BLUE, alpha=0.095 - idx * 0.018, thickness=5)
        draw_arc(frame, center, axes, math.radians(idx * 28 + 92), math.radians(196), math.radians(336), DEEP_TEAL, alpha=0.075 - idx * 0.014, thickness=4)
    for idx, angle in enumerate(radial_angles(14, start=math.radians(8))):
        dist = 185 + 78 * (idx % 4)
        node = point(center, angle + 0.10 * math.sin(idx), dist)
        if idx % 3 == 0:
            draw_s_crescent(frame, node, 72, angle + math.pi / 2.0, IVORY, alpha=0.33)
        elif idx % 3 == 1:
            draw_lens(frame, node, 58, 20, angle, PALE_BLUE, alpha=0.30)
        else:
            draw_trigon_release(frame, node, center, 38, 46, PALE_BLUE, alpha=0.28, sharpness=0.50, softness=0.70)
    return frame


STUDIES: list[tuple[str, str, str, Callable[[], np.ndarray]]] = [
    ("01_raindrop_radial_wave_interference_v001.png", "raindrop/water ripple", "Multiple circle origins generate expanding rings; crescents, lenses, and trigons appear at interference paths.", study_01_raindrop_interference),
    ("02_radial_wave_interference_cells_v001.png", "raindrop/water ripple", "Sixfold water-impact interference with lens cells at overlaps.", study_02_radial_wave_interference_cells),
    ("03_seed_of_life_decomposed_lunes_trigons_v001.png", "seed-of-life", "Seed circles decomposed into lune/lens two-arc cells and trigon release cells.", study_03_seed_decomposed_lunes_trigons),
    ("04_seed_of_life_triangular_gap_cells_v001.png", "seed-of-life", "Triangular gaps/cells are treated as trigon topology, with no generic triangle marks.", study_04_seed_triangular_gap_cells),
    ("05_flower_of_life_water_orbit_field_v001.png", "flower-of-life/orbit", "Flower circle field becomes an orbital water surface with lenses and S-crescents.", study_05_flower_water_orbit_field),
    ("06_flower_orbit_trigon_release_v001.png", "flower-of-life/sun", "Flower geometry pushes outward into crescent and trigon release/ray cells.", study_06_flower_orbit_trigon_release),
    ("07_cymatic_standing_wave_field_v001.png", "cymatic standing wave", "Standing-wave bands activate primitive cells at antinode-like positions.", study_07_cymatic_standing_wave_field),
    ("08_cymatic_node_activation_v001.png", "cymatic standing wave", "Alternating circle, lens, crescent, and trigon cells mark nodal activation around elliptical modes.", study_08_cymatic_node_activation),
    ("09_snowflake_frozen_water_sixfold_fractal_v001.png", "snowflake/frozen water", "Sixfold frozen-water topology branches into repeated lens and trigon cells.", study_09_snowflake_sixfold_fractal),
    ("10_sun_circle_trigon_crescent_rays_v001.png", "sun/radiant geometry", "Circle origin radiates through crescent/lens/trigon rays.", study_10_sun_circle_trigon_crescent_rays),
    ("11_network_of_primitive_cells_v001.png", "primitive-cell network", "Network nodes alternate one-boundary, two-arc, and trigon topology classes.", study_11_network_primitive_cells),
    ("12_chladni_nodal_line_primitive_activation_v001.png", "Chladni/nodal-line", "Nodal-line arcs activate primitive cells without a crude grid or wallpaper layout.", study_12_chladni_nodal_line_activation),
]


def render_raindrop_interference_loop(phase: float) -> np.ndarray:
    frame = canvas()
    centers = [(695.0, 545.0), (960.0, 505.0), (1225.0, 570.0)]
    for idx, center in enumerate(centers):
        pulse = phase_wave(phase, idx * 0.12)
        draw_circle(frame, center, 34 + 7 * pulse, IVORY, alpha=0.58)
        for ridx, base in enumerate([105, 220, 360, 520]):
            local = phase_wave(phase, ridx * 0.10 + idx * 0.08)
            draw_ring(frame, center, base + 32 * local, 4, PALE_BLUE, alpha=max(0.026, 0.15 - ridx * 0.030))
    for idx, angle in enumerate([math.radians(-20), math.radians(18), math.radians(52), math.radians(155)]):
        local = phase_wave(phase, idx * 0.09)
        draw_topology_phrase(frame, centers[idx % 3], angle + math.radians(3) * math.sin(2 * math.pi * phase), distances=(140 + 10 * local, 248 + 20 * local, 382 + 32 * local), scale=0.70, alpha=0.50 + 0.08 * local)
    return frame


def render_seed_flower_emergence_loop(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    rotate = phase * math.radians(9)
    pulse = 0.96 + 0.07 * phase_wave(phase)
    draw_seed_circles(frame, center, 132 * pulse, ring_radius=132 * pulse, rgb=PALE_BLUE, alpha=0.13, thickness=4, start=rotate)
    draw_seed_circles(frame, center, 116 * pulse, ring_radius=232 * pulse, count=12, start=math.radians(15) + rotate * 0.7, rgb=DEEP_TEAL, alpha=0.050, thickness=3)
    for idx, angle in enumerate(radial_angles(12, start=math.radians(15) + rotate)):
        local = phase_wave(phase, idx * 0.06)
        if idx % 2 == 0:
            draw_lens(frame, point(center, angle, 240 + 16 * local), 78, 28, angle + math.pi / 2.0, SOFT_IVORY, alpha=0.34 + 0.08 * local)
        else:
            draw_s_crescent(frame, point(center, angle, 258 + 14 * local), 84, angle + math.pi / 2.0, IVORY, alpha=0.30 + 0.06 * local)
        if idx % 3 == 0:
            draw_trigon_release(frame, point(center, angle, 410 + 28 * local), center, 58, 68, PALE_BLUE, alpha=0.32, sharpness=0.54, softness=0.62)
    draw_circle(frame, center, 58 * pulse, IVORY, alpha=0.48)
    return frame


def render_cymatic_standing_wave_loop(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    for i, yoff in enumerate([-245, -145, -52, 52, 145, 245]):
        pts = nodal_curve(center, amp=58 - abs(yoff) * 0.08, y_offset=yoff, phase=phase * 0.36 + i * 0.12)
        draw_line(frame, pts, PALE_BLUE, alpha=0.12 if i in (2, 3) else 0.075, thickness=5)
    for i, x in enumerate([600, 780, 960, 1140, 1320]):
        for j, y in enumerate([360, 460, 560, 660, 760]):
            local = phase_wave(phase, (i + j) * 0.07)
            if (i + j) % 2 == 0:
                draw_lens(frame, (x, y + 10 * math.sin(2 * math.pi * (phase + i * 0.03))), 48 + 8 * local, 18 + 4 * local, math.radians(18 * (i - j)), SOFT_IVORY, alpha=0.22 + 0.10 * local)
            else:
                draw_trigon(frame, (x, y), 30 + 5 * local, 38 + 6 * local, math.radians(90 + 12 * (i + j)), PALE_BLUE, alpha=0.20 + 0.08 * local, sharpness=0.56, softness=0.60)
    draw_circle(frame, center, 42 + 5 * phase_wave(phase), IVORY, alpha=0.40)
    return frame


def render_chladni_activation_loop(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    rotate = math.radians(7) * math.sin(2 * math.pi * phase)
    for idx, axes in enumerate([(700, 210), (520, 340), (365, 470)]):
        draw_arc(frame, center, (axes[0] + 12 * phase_wave(phase, idx * 0.08), axes[1] + 7 * phase_wave(phase, idx * 0.12)), math.radians(idx * 28 - 18) + rotate, math.radians(16), math.radians(344), PALE_BLUE, alpha=0.090 - idx * 0.018, thickness=5)
        draw_arc(frame, center, axes, math.radians(idx * 28 + 92) - rotate * 0.8, math.radians(196), math.radians(336), DEEP_TEAL, alpha=0.070 - idx * 0.014, thickness=4)
    for idx, angle in enumerate(radial_angles(14, start=math.radians(8) + rotate)):
        local = phase_wave(phase, idx * 0.055)
        dist = 180 + 78 * (idx % 4) + 16 * local
        node = point(center, angle + 0.10 * math.sin(idx), dist)
        if idx % 3 == 0:
            draw_s_crescent(frame, node, 66 + 8 * local, angle + math.pi / 2.0, IVORY, alpha=0.26 + 0.09 * local)
        elif idx % 3 == 1:
            draw_lens(frame, node, 54 + 8 * local, 19 + 4 * local, angle, PALE_BLUE, alpha=0.24 + 0.08 * local)
        else:
            draw_trigon_release(frame, node, center, 36 + 5 * local, 44 + 6 * local, PALE_BLUE, alpha=0.22 + 0.08 * local, sharpness=0.50, softness=0.70)
    return frame


ANIMATIONS: list[tuple[str, str, Callable[[float], np.ndarray]]] = [
    ("13_raindrop_interference_expansion_v001_black_screen.mp4", "Rings expand from multiple circle origins while primitive cells appear at interference zones.", render_raindrop_interference_loop),
    ("14_seed_flower_cell_emergence_v001_black_screen.mp4", "Crescents, lenses, S-crescents, and trigons emerge from overlapping circle geometry.", render_seed_flower_emergence_loop),
    ("15_cymatic_standing_wave_activation_v001_black_screen.mp4", "Standing-wave bands breathe while cells activate at node/antinode positions.", render_cymatic_standing_wave_loop),
    ("16_chladni_nodal_primitive_activation_v001_black_screen.mp4", "Nodal-line arcs phase slowly as primitive topology classes appear and recede.", render_chladni_activation_loop),
]


def save_contact_sheet(stills: list[tuple[str, np.ndarray]], out_name: str) -> None:
    thumbs: list[np.ndarray] = []
    for idx, (name, frame) in enumerate(stills, start=1):
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, f"{idx:02d} {Path(name).stem[:42]}", (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 232), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    rows = [cv2.hconcat(thumbs[i : i + 4]) for i in range(0, len(thumbs), 4)]
    cv2.imwrite(str(OUT_DIR / out_name), cv2.vconcat(rows), [cv2.IMWRITE_PNG_COMPRESSION, 3])


def render_stills() -> list[tuple[str, np.ndarray]]:
    rendered: list[tuple[str, np.ndarray]] = []
    for name, _, _, fn in STUDIES:
        frame = fn()
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        rendered.append((name, frame))
    save_contact_sheet(rendered, "contact_sheet_cymatic_radiant_water_geometry_v001.png")
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
    save_contact_sheet(midpoints, "contact_sheet_cymatic_radiant_water_geometry_v001_animation_midpoints.png")
    return midpoints


def write_readme() -> None:
    study_lines = []
    for name, family, note, _ in STUDIES:
        study_lines.append(f"### `{name}`\n\nFamily: {family}. {note}\n")
    animation_lines = []
    for name, note, _ in ANIMATIONS:
        animation_lines.append(f"- `{name}`: {note}")
    readme = f"""# Cymatic / Radiant Water Geometry v001 - 2026-05-20

Status: INTERNAL ONLY. Austin-review-needed. Not Austin-approved, not public, and not a cultural meaning claim.

This packet stops the salmon/figure lane and treats the primitives as topology classes inside water, cymatic, radiant, and frozen-water geometry. Seed-of-life, flower-of-life, cymatics, Chladni/nodal-line studies, snowflake forms, sun geometry, and water ripple interference are used only as general geometric fields. No cultural or ceremonial meaning is claimed.

## Topology-Class Interpretation

- `circle`: one closed boundary. Used as impact origin, seed cell, orbit node, sun disc, or closed pressure boundary.
- `crescent`: two-arc class. Includes lune, lens, crescent, and S-crescent variants created from two-arc overlap/phase relationships.
- `trigon`: three-sided / three-arc class. Used as triangular gap, release cell, attenuated wave point, ray cell, or nodal activation cell. Trigons remain curved/specific rather than generic triangles.
- `negative space`: a deliberate topological gap or void; not a missing circle or accidental hole.

The visual aim is not symbolic clusters on black. The aim is a radiant water field where circles overlap, produce two-arc cells, open into trigons, and animate through interference, standing waves, and nodal activation.

## Contents

- 12 PNG stills at 1920x1080.
- 4 black-screen 6s MP4 loops at 1920x1080, 24 fps.
- Still contact sheet: `contact_sheet_cymatic_radiant_water_geometry_v001.png`.
- Animation midpoint contact sheet: `contact_sheet_cymatic_radiant_water_geometry_v001_animation_midpoints.png`.
- Midpoint stills in `midpoint_stills/`.

Renderer:

`scripts/cymatic_radiant_water_geometry_v001.py`

## Still Studies

{chr(10).join(study_lines)}
## Motion Studies

{chr(10).join(animation_lines)}

## Motion Rules

- Rings expand from circle origins.
- Waves interfere through overlapping ring fields and nodal arcs.
- Cells appear/disappear at nodes and antinodes.
- Crescents, lenses, S-crescents, and trigons emerge from overlapping circles.
- No debug dots, no crude Cartesian grids, no generic mandala wallpaper, no salmon/fish/figures.

## Review Questions

- Does the topology-class framing make the primitive grammar feel more like water geometry?
- Which field reads strongest: raindrop interference, seed/flower decomposition, cymatic standing wave, snowflake/frozen water, sun/radiant, network, or Chladni/nodal activation?
- Do the lens/S-crescent variants clarify the two-arc class, or do they drift too far from the accepted crescent grammar?
- Are trigons reading as three-arc/topology cells rather than generic triangles?
- Which study should be carried forward into a more polished projection layer?
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    render_stills()
    render_animations()
    write_readme()
    print(f"Wrote cymatic radiant water geometry v001 packet to {OUT_DIR}")


if __name__ == "__main__":
    main()
