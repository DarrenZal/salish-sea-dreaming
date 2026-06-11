#!/usr/bin/env python3.11
"""
Primitive Water Membrane v006.

Water-only, layer-only black-background review packet:
  - no fish, salmon proxy, birds, flocking, figures, SD, LoRA, SAM, or YOLO
  - circle / crescent / trigon phrases attached to a moving 2D water membrane
  - deterministic Python/OpenCV/vector rendering for internal Austin review
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from primitive_water_grammar_v1 import (
    CRESCENT_BASE,
    H264Writer,
    N_FRAMES,
    ROOT,
    TRIGON_BASE,
    W,
    H,
    draw_circle_alpha,
    draw_poly_alpha,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_membrane_v006_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
FPS = 24

# Restrained review palette for additive/screen mixing.
CIRCLE_RGB = (242, 236, 214)
CRESCENT_RGB = (199, 224, 233)
TRIGON_RGB = (156, 192, 211)
THREAD_RGB = (142, 194, 212)
OUTLINE_RGB = (228, 238, 238)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    method: str
    caveat: str
    austin_question: str
    dynamic_note: str = ""


def black_canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def unit_circle_points(samples: int = 80) -> np.ndarray:
    return np.array(
        [(math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples)) for i in range(samples)],
        dtype=np.float32,
    )


CIRCLE_BASE = unit_circle_points()


def smooth_angle(current: float, target: float, amount: float) -> float:
    delta = math.atan2(math.sin(target - current), math.cos(target - current))
    return current + delta * amount


def edge_fade(u: float, v: float, margin: float = 0.075) -> float:
    left = min(1.0, max(0.0, u / margin))
    right = min(1.0, max(0.0, (1.0 - u) / margin))
    top = min(1.0, max(0.0, v / margin))
    bottom = min(1.0, max(0.0, (1.0 - v) / margin))
    return left * right * top * bottom


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, *, alpha: float) -> None:
    draw_circle_alpha(
        frame,
        center,
        radius,
        CIRCLE_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.075,
    )


def additive_polyline(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 1,
) -> None:
    if len(pts) < 2 or alpha <= 0:
        return
    layer = np.zeros_like(frame)
    bgr = (int(rgb[2]), int(rgb[1]), int(rgb[0]))
    cv2.polylines(layer, [np.round(pts).astype(np.int32)], False, bgr, thickness, lineType=cv2.LINE_AA)
    work = frame.astype(np.float32) + layer.astype(np.float32) * alpha
    frame[:] = np.clip(work, 0, 255).astype(np.uint8)


class WaterMembraneProjector:
    """Author shapes in UV surface space, then warp/project into screen space."""

    def __init__(self, *, profile: str = "standard") -> None:
        src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        if profile == "shallow":
            dst = np.array(
                [
                    [W * 0.19, H * 0.24],
                    [W * 0.81, H * 0.24],
                    [W * 0.96, H * 0.83],
                    [W * 0.04, H * 0.83],
                ],
                dtype=np.float32,
            )
        elif profile == "wide":
            dst = np.array(
                [
                    [W * 0.10, H * 0.19],
                    [W * 0.90, H * 0.19],
                    [W * 1.02, H * 0.86],
                    [W * -0.02, H * 0.86],
                ],
                dtype=np.float32,
            )
        else:
            dst = np.array(
                [
                    [W * 0.28, H * 0.18],
                    [W * 0.72, H * 0.18],
                    [W * 0.94, H * 0.88],
                    [W * 0.06, H * 0.88],
                ],
                dtype=np.float32,
            )
        self.mat = cv2.getPerspectiveTransform(src, dst)

    @staticmethod
    def height(u: np.ndarray | float, v: np.ndarray | float, t: float) -> np.ndarray | float:
        return (
            0.52 * np.sin(2.0 * math.pi * (1.12 * u - 0.105 * t) + 0.75 * np.sin(2.0 * math.pi * (v * 0.68 + 0.034 * t)))
            + 0.31 * np.sin(2.0 * math.pi * (0.58 * u + 1.08 * v - 0.072 * t) + 0.40)
            + 0.17 * np.sin(2.0 * math.pi * (1.85 * u - 0.42 * v + 0.052 * t))
        )

    def warp_uv(self, pts: np.ndarray, t: float) -> np.ndarray:
        uv = pts.copy()
        u = uv[:, 0]
        v = uv[:, 1]
        h = self.height(u, v, t)
        # Conservative topology: enough deformation to bind marks to a surface,
        # not a heavy 3D effect or relief simulation.
        depth = 0.30 + 0.88 * v
        uv[:, 0] = u + 0.010 * depth * h + 0.006 * np.sin(2.0 * math.pi * (v * 1.25 - t * 0.040))
        uv[:, 1] = v + 0.020 * depth * h + 0.007 * np.sin(2.0 * math.pi * (u * 0.74 + t * 0.035))
        return uv

    def project(self, pts: np.ndarray, t: float) -> np.ndarray:
        uv = self.warp_uv(pts, t)
        projected = cv2.perspectiveTransform(uv.reshape(-1, 1, 2).astype(np.float32), self.mat)
        return projected.reshape(-1, 2)

    def contour_angle(self, u: float, v: float, t: float) -> float:
        eps = 0.004
        dhdu = (float(self.height(u + eps, v, t)) - float(self.height(u - eps, v, t))) / (2.0 * eps)
        dhdv = (float(self.height(u, v + eps, t)) - float(self.height(u, v - eps, t))) / (2.0 * eps)
        # Tangent to an equal-height contour in UV space.
        return math.atan2(dhdu, -dhdv)

    def screen_angle(self, center_uv: tuple[float, float], angle_uv: float, t: float, delta: float = 0.010) -> float:
        c = np.array(center_uv, dtype=np.float32)
        d = np.array([math.cos(angle_uv), math.sin(angle_uv)], dtype=np.float32) * delta
        pts = self.project(np.vstack([c - d, c + d]), t)
        return math.atan2(float(pts[1, 1] - pts[0, 1]), float(pts[1, 0] - pts[0, 0]))


def draw_membrane_shape(
    frame: np.ndarray,
    projector: WaterMembraneProjector,
    base: np.ndarray,
    center_uv: tuple[float, float],
    sx: float,
    sy: float,
    angle_uv: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    t: float,
    flip_y: bool = False,
) -> None:
    if alpha <= 0:
        return
    base_pts = base.copy()
    if flip_y:
        base_pts[:, 1] *= -1.0
    base_pts[:, 0] *= sx
    base_pts[:, 1] *= sy
    c = math.cos(angle_uv)
    s = math.sin(angle_uv)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    uv = base_pts @ rot.T
    uv[:, 0] += center_uv[0]
    uv[:, 1] += center_uv[1]
    pts = projector.project(uv, t)
    draw_poly_alpha(
        frame,
        pts,
        rgb,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.055,
        outline_thickness=1,
    )


def draw_membrane_circle(
    frame: np.ndarray,
    projector: WaterMembraneProjector,
    center_uv: tuple[float, float],
    radius_uv: float,
    *,
    alpha: float,
    t: float,
) -> None:
    draw_membrane_shape(frame, projector, CIRCLE_BASE, center_uv, radius_uv, radius_uv, 0.0, CIRCLE_RGB, alpha=alpha, t=t)


def draw_membrane_thread(
    frame: np.ndarray,
    projector: WaterMembraneProjector,
    path_uv: list[tuple[float, float]],
    *,
    alpha: float,
    t: float,
    thickness: int = 1,
) -> None:
    pts = np.array(path_uv, dtype=np.float32)
    valid = (pts[:, 0] >= -0.08) & (pts[:, 0] <= 1.08) & (pts[:, 1] >= -0.08) & (pts[:, 1] <= 1.08)
    if valid.sum() < 2:
        return
    additive_polyline(frame, projector.project(pts[valid], t), THREAD_RGB, alpha=alpha, thickness=thickness)


def contour_path(row: int, u: float, t: float) -> tuple[float, float]:
    phase = row * 0.63
    base_v = 0.195 + row * 0.112
    v = (
        base_v
        + 0.026 * math.sin(2.0 * math.pi * (u * 1.04 - t * 0.055) + phase)
        + 0.012 * math.sin(2.0 * math.pi * (u * 2.10 + t * 0.026) - phase * 0.55)
    )
    return u, v


def contour_tangent(row: int, u: float, t: float) -> float:
    eps = 0.006
    _, v0 = contour_path(row, u - eps, t)
    _, v1 = contour_path(row, u + eps, t)
    return math.atan2(v1 - v0, 2.0 * eps)


def render_wave_membrane_heightfield() -> ClipResult:
    out = OUT_DIR / "01_wave_membrane_heightfield_v006_black_screen.mp4"
    writer = H264Writer(out)
    projector = WaterMembraneProjector(profile="standard")
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()

        for row in range(6):
            path = [contour_path(row, i / 54.0, t) for i in range(55)]
            draw_membrane_thread(frame, projector, path, alpha=0.030 + 0.006 * (row % 2), t=t, thickness=1)

        for row in range(6):
            drift = (0.030 * t + row * 0.073) % 0.245
            for phrase in range(4):
                u0 = 0.075 + phrase * 0.245 + drift
                if u0 > 1.03:
                    u0 -= 0.98
                for part, offset, sx, sy, rgb, a_scale in [
                    ("circle", 0.000, 0.0065, 0.0065, CIRCLE_RGB, 0.36),
                    ("crescent", 0.045, 0.0240, 0.0100, CRESCENT_RGB, 0.34),
                    ("crescent", 0.087, 0.0200, 0.0085, CRESCENT_RGB, 0.27),
                    ("trigon", 0.132, 0.0150, 0.0120, TRIGON_RGB, 0.22),
                ]:
                    u = u0 + offset
                    if u > 1.0:
                        continue
                    cu, cv = contour_path(row, u, t)
                    fade = edge_fade(cu, cv) * (0.88 - row * 0.055)
                    if fade <= 0.02:
                        continue
                    angle = contour_tangent(row, u, t)
                    wave_bias = projector.contour_angle(cu, cv, t)
                    angle = smooth_angle(angle, wave_bias, 0.18)
                    if part == "circle":
                        draw_membrane_circle(frame, projector, (cu, cv), sx, alpha=a_scale * fade, t=t)
                    elif part == "crescent":
                        draw_membrane_shape(frame, projector, CRESCENT_BASE, (cu, cv), sx, sy, angle, rgb, alpha=a_scale * fade, t=t, flip_y=(row % 2 == 1))
                    else:
                        draw_membrane_shape(frame, projector, TRIGON_BASE, (cu, cv), sx, sy, angle, rgb, alpha=a_scale * fade, t=t)

        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  wave membrane heightfield v006 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural water membrane / heightfield study",
        test="A tilted 2D water membrane where sparse primitive phrases ride shared traveling contours.",
        method="UV contour rows are warped by a soft wave heightfield, then projected in perspective; circles/crescents/trigons attach to local contour tangents.",
        caveat="The faint contour threads are technical scaffolding for the membrane read; Austin should decide whether final layers use only filled primitives.",
        austin_question="Does this wavy membrane make the primitive marks feel embedded in a water surface rather than floating as separate markers?",
    )


def ripple_bias_angle(projector: WaterMembraneProjector, u: float, v: float, radial_angle: float, t: float) -> float:
    return smooth_angle(radial_angle, projector.contour_angle(u, v, t), 0.16)


def render_ripples_on_wavy_membrane() -> ClipResult:
    out = OUT_DIR / "02_ripples_on_wavy_membrane_v006_black_screen.mp4"
    writer = H264Writer(out)
    projector = WaterMembraneProjector(profile="standard")
    impacts = [
        {"start": 0.10, "uv": (0.38, 0.57), "scale": 1.00, "rays": 7},
        {"start": 1.85, "uv": (0.63, 0.42), "scale": 0.72, "rays": 6},
        {"start": 3.55, "uv": (0.50, 0.68), "scale": 0.82, "rays": 6},
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()

        for row in range(6):
            path = [contour_path(row, i / 54.0, t) for i in range(55)]
            draw_membrane_thread(frame, projector, path, alpha=0.020, t=t, thickness=1)

        for impact in impacts:
            age = t - impact["start"]
            if age < 0.0 or age > 2.85:
                continue
            origin_u, origin_v = impact["uv"]
            scale = impact["scale"]
            pulse = max(0.0, 1.0 - age / 0.95)
            draw_membrane_circle(frame, projector, (origin_u, origin_v), 0.0125 * scale, alpha=0.62 * pulse, t=t)
            for ray in range(impact["rays"]):
                local_age = age - ray * 0.020
                if local_age <= 0.0:
                    continue
                q = min(1.0, local_age / 2.42)
                ease = math.sqrt(max(0.0, 1.0 - (1.0 - q) * (1.0 - q)))
                base_angle = -0.20 + ray * 2.0 * math.pi / impact["rays"]
                surface_push = 0.012 * math.sin(2.0 * math.pi * (q + ray * 0.17 + t * 0.035))
                radius = (0.034 + 0.185 * ease + surface_push) * scale
                alpha = 0.60 * ((1.0 - q) ** 1.30) * scale
                if alpha < 0.018:
                    continue
                for idx, (kind, extra, sx, sy, part_alpha) in enumerate(
                    [
                        ("crescent", 0.000, 0.028, 0.0118, 0.96),
                        ("crescent", 0.043, 0.023, 0.0100, 0.82),
                        ("trigon", 0.086, 0.016, 0.0135, 0.66),
                    ]
                ):
                    rr = radius + extra * scale
                    cu = origin_u + math.cos(base_angle) * rr
                    cv = origin_v + math.sin(base_angle) * rr
                    fade = edge_fade(cu, cv)
                    if fade <= 0.01:
                        continue
                    angle = ripple_bias_angle(projector, cu, cv, base_angle, t)
                    if kind == "crescent":
                        draw_membrane_shape(frame, projector, CRESCENT_BASE, (cu, cv), sx * scale, sy * scale, angle, CRESCENT_RGB, alpha=alpha * part_alpha * fade, t=t)
                    else:
                        draw_membrane_shape(frame, projector, TRIGON_BASE, (cu, cv), sx * scale, sy * scale, angle, TRIGON_RGB, alpha=alpha * part_alpha * fade, t=t)

        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  ripples on wavy membrane v006 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural droplet ripple / membrane study",
        test="Multiple droplet impacts where circle origins and outward crescent/crescent/trigon phrases bend with a moving surface.",
        method="Ripple phrases expand in UV space, then local heightfield tangents bias placement/orientation before perspective projection.",
        caveat="Crescent cupping versus travel-facing orientation is still unresolved; this version favors outward phrase travel with a light surface-tangent bias.",
        austin_question="Should ripple crescents follow the outward travel direction, cup back toward the circle origin, or align more strongly to the local water-surface tangent?",
    )


def current_centerline(u: float, t: float) -> tuple[float, float, float]:
    phase = 2.0 * math.pi * (0.72 * u - 0.065 * t)
    v = 0.51 + 0.130 * math.sin(phase) + 0.035 * math.sin(2.0 * phase + 0.70)
    dv_du = 0.130 * math.cos(phase) * 2.0 * math.pi * 0.72 + 0.035 * math.cos(2.0 * phase + 0.70) * 4.0 * math.pi * 0.72
    tangent = math.atan2(dv_du, 1.0)
    return u, v, tangent


def current_band_point(u: float, band_offset: float, t: float) -> tuple[float, float, float]:
    cu, cv, tangent = current_centerline(u, t)
    normal = tangent + math.pi / 2.0
    compression = 0.5 + 0.5 * math.sin(2.0 * math.pi * (1.35 * u - 0.11 * t))
    width = (0.070 + 0.018 * compression) * band_offset
    return cu + math.cos(normal) * width, cv + math.sin(normal) * width, tangent


def render_current_as_continuous_surface() -> ClipResult:
    out = OUT_DIR / "03_current_as_continuous_surface_v006_black_screen.mp4"
    writer = H264Writer(out)
    projector = WaterMembraneProjector(profile="wide")
    bands = [-1.15, -0.58, 0.0, 0.58, 1.15]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()

        for bi, band in enumerate(bands):
            path = [current_band_point(i / 64.0, band, t)[:2] for i in range(65)]
            draw_membrane_thread(frame, projector, path, alpha=0.028 if bi in (1, 2, 3) else 0.018, t=t, thickness=1)

        for bi, band in enumerate(bands):
            drift = (0.022 * t + bi * 0.031) % 0.128
            for col in range(8):
                u = 0.065 + col * 0.128 + drift
                if u > 0.965:
                    continue
                cu, cv, tangent = current_band_point(u, band, t)
                compression = 0.5 + 0.5 * math.sin(2.0 * math.pi * (1.35 * u - 0.11 * t))
                fade = edge_fade(cu, cv) * (0.92 - 0.06 * abs(band))
                if fade <= 0.02:
                    continue
                wave_angle = smooth_angle(tangent, projector.contour_angle(cu, cv, t), 0.12)
                crest = ((bi + col) % 2 == 0)
                sx = 0.034 + 0.012 * compression
                sy = 0.0075 + 0.0025 * compression
                alpha = (0.25 + 0.070 * compression) * fade
                draw_membrane_shape(
                    frame,
                    projector,
                    CRESCENT_BASE,
                    (cu, cv),
                    sx,
                    sy,
                    wave_angle if crest else wave_angle + math.pi,
                    CRESCENT_RGB,
                    alpha=alpha,
                    t=t,
                    flip_y=not crest,
                )
                if col in (2, 5) and abs(band) < 0.7:
                    draw_membrane_shape(
                        frame,
                        projector,
                        TRIGON_BASE,
                        (cu + math.cos(tangent) * 0.050, cv + math.sin(tangent) * 0.050),
                        0.013,
                        0.010,
                        wave_angle,
                        TRIGON_RGB,
                        alpha=alpha * 0.42,
                        t=t,
                    )
                if col == 0 and bi in (1, 3):
                    draw_membrane_circle(frame, projector, (cu - math.cos(tangent) * 0.034, cv - math.sin(tangent) * 0.034), 0.0050, alpha=alpha * 0.28, t=t)

        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  current as continuous surface v006 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural continuous current-surface study",
        test="A current sheet built from shared S-curve bands, phase-locked crest/trough rows, and sparse primitive attenuation marks.",
        method="Five common-fate bands follow one S-curve surface; alternating crescent orientation marks peaks/troughs while trigon/circle accents stay secondary.",
        caveat="This is still abstract current topology; it should be reviewed for whether it reads as one water body or slips back into separate marks.",
        austin_question="Does the shared S-curve/current sheet read as a continuous water surface rather than particles, flocking, or figure-like glyphs?",
    )


def tile_path(row: int, u: float, t: float) -> tuple[float, float, float]:
    base_v = 0.24 + row * 0.130
    phase = row * 0.85
    v = base_v + 0.035 * math.sin(2.0 * math.pi * (u * 0.92 - t * 0.040) + phase)
    dv_du = 0.035 * math.cos(2.0 * math.pi * (u * 0.92 - t * 0.040) + phase) * 2.0 * math.pi * 0.92
    return u, v, math.atan2(dv_du, 1.0)


def render_primitive_tiling_water_surface() -> ClipResult:
    out = OUT_DIR / "04_primitive_tiling_water_surface_v006_black_screen.mp4"
    writer = H264Writer(out)
    projector = WaterMembraneProjector(profile="shallow")
    pattern = ["circle", "crescent", "crescent", "trigon"]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()

        for row in range(5):
            path = [tile_path(row, i / 54.0, t)[:2] for i in range(55)]
            draw_membrane_thread(frame, projector, path, alpha=0.018, t=t, thickness=1)

        for row in range(5):
            drift = 0.018 * math.sin(t * 0.34 + row * 0.70)
            for col in range(5):
                kind = pattern[(row + col) % len(pattern)]
                u = 0.145 + col * 0.175 + drift + 0.020 * (row % 2)
                cu, cv, tangent = tile_path(row, u, t)
                fade = edge_fade(cu, cv) * (0.86 - 0.05 * row)
                if fade <= 0.02:
                    continue
                local_angle = smooth_angle(tangent, projector.contour_angle(cu, cv, t), 0.16)
                pulse = 0.78 + 0.22 * math.sin(2.0 * math.pi * (0.42 * t + col * 0.18 + row * 0.11))
                if kind == "circle":
                    draw_membrane_circle(frame, projector, (cu, cv), 0.0062, alpha=0.30 * fade * pulse, t=t)
                elif kind == "crescent":
                    draw_membrane_shape(
                        frame,
                        projector,
                        CRESCENT_BASE,
                        (cu, cv),
                        0.022,
                        0.0090,
                        local_angle,
                        CRESCENT_RGB,
                        alpha=0.29 * fade * pulse,
                        t=t,
                        flip_y=((row + col) % 3 == 0),
                    )
                else:
                    draw_membrane_shape(
                        frame,
                        projector,
                        TRIGON_BASE,
                        (cu, cv),
                        0.013,
                        0.011,
                        local_angle,
                        TRIGON_RGB,
                        alpha=0.24 * fade * pulse,
                        t=t,
                    )

        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  primitive tiling water surface v006 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural sparse primitive tiling study",
        test="A sparse circle/crescent/trigon tiling that follows wave contours without becoming dense wallpaper.",
        method="Five shallow membrane contours carry a restrained repeating primitive order; local tangent and heightfield bias orientation.",
        caveat="The tiling may still be too decorative if the phrase order is not tied to clear water origins or current events.",
        austin_question="Are sparse contour-following primitive tiles acceptable for water surfaces, or should every mark belong to an explicit ripple/current phrase?",
    )


def ffprobe(path: Path) -> dict[str, str]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(path),
    ]
    data = json.loads(subprocess.check_output(cmd, text=True))
    stream = data["streams"][0]
    return {
        "width": str(stream.get("width", "")),
        "height": str(stream.get("height", "")),
        "fps": str(stream.get("avg_frame_rate") or stream.get("r_frame_rate", "")),
        "duration": str(stream.get("duration", "")),
        "frames": str(stream.get("nb_frames", "")),
    }


def midpoint_stats(result: ClipResult) -> str:
    cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "midpoint read failed"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return f"midpoint max luma {int(gray.max())}, nonblack pixels {int((gray > 2).sum())}"


def save_midpoint_stills(results: Iterable[ClipResult]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[np.ndarray] = []
    for result in results:
        cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        cv2.imwrite(str(MIDPOINT_DIR / f"{Path(result.filename).stem}_midpoint.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(
            thumb,
            Path(result.filename).stem[:46],
            (14, 248),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        thumbs.append(thumb)
    if thumbs:
        rows = []
        for i in range(0, len(thumbs), 2):
            row = thumbs[i : i + 2]
            if len(row) == 1:
                row.append(np.zeros_like(row[0]))
            rows.append(cv2.hconcat(row))
        cv2.imwrite(str(OUT_DIR / "contact_sheet_midpoints.jpg"), cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])


def write_readme(results: list[ClipResult]) -> None:
    rows = [(result, ffprobe(OUT_DIR / result.filename), midpoint_stats(result)) for result in results]
    lines = [
        "# Primitive Water Membrane v006 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Water-only, layer-only pure-black clips; no fish, salmon proxy, birds, flocking, figures, SD, LoRA, SAM, or YOLO.",
        "",
        "## Darren's v005 Water Feedback Summary",
        "",
        "- `01` perspective ripple/topology was interesting but only a modest improvement; the promising branch is a wavy 2D membrane/surface with ripples living on it.",
        "- `02` duality current sheet improved, but still did not fully read as a coherent membrane/body/field of water and could look like separate particles or flocking.",
        "- Fish clips `03`/`04` are parked for now. v006 keeps fish, salmon proxy, birds, figures, and flocking out of scope.",
        "",
        "## Membrane / Topology Idea",
        "",
        "v006 authors primitives in a simple UV water-surface coordinate system, applies a soft traveling heightfield/topology warp, and then projects that surface to the black-screen output. The intent is not 3D relief or cultural approval; it is a conservative technical question: can circle/crescent/trigon phrases behave as marks embedded in one moving water body rather than as independent overlay markers?",
        "",
        "## v005 -> v006 Changes",
        "",
        "- Removed fish, salmon proxy, birds, flocking, figures, and footage-derived tracking from this lane.",
        "- Shifted from standalone markers toward shared membrane coordinates, contour tangents, and common-fate surface motion.",
        "- Kept the v005 perspective plane direction but made the surface/membrane behavior the lead question.",
        "- Made current-sheet motion more banded and phase-locked so it can be reviewed as one continuous water layer.",
        "- Added midpoint stills and a contact sheet for quick internal review.",
        "",
        "## Review Order",
        "",
        "1. `01_wave_membrane_heightfield_v006_black_screen.mp4`",
        "2. `02_ripples_on_wavy_membrane_v006_black_screen.mp4`",
        "3. `03_current_as_continuous_surface_v006_black_screen.mp4`",
        "4. `04_primitive_tiling_water_surface_v006_black_screen.mp4`",
        "",
        "## Austin Questions",
        "",
        "- Does a wavy 2D membrane make the primitive marks feel embedded in water, or should this stay flat/head-on?",
        "- Can ripples live on a tilted/perspective water plane, or should the grammar remain front-facing until Austin approves perspective?",
        "- Should ripple crescents follow outward travel, cup back toward the circle origin, or align to local water-surface tangent?",
        "- Does the current sheet read as one continuous water body rather than separate particles, flocking, or figure-like glyphs?",
        "- Are sparse contour-following primitive tiles acceptable for water surfaces, or should every mark belong to an explicit ripple/current phrase?",
        "",
        "## Resolume Screen/Additive Notes",
        "",
        "- All four clips are pure black with restrained ivory/pale-blue primitives for Screen/Additive mixing over Agent A fallback footage.",
        "- Start with low opacity in Resolume; the membrane contour threads are intentionally faint and can disappear if the blend is too soft.",
        "- These are water-only layers. Keep them separate from any future figure/fish review layers.",
        "",
        "## Clips",
        "",
    ]
    for result, probe, stats in rows:
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}",
                f"- Source: `{result.source}`",
                f"- Technical method: {result.method}",
                f"- Caveat: {result.caveat}",
                f"- Exact Austin question: {result.austin_question}",
            ]
        )
        if result.dynamic_note:
            lines.append(f"- Runtime note: {result.dynamic_note}")
        lines.extend(
            [
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                f"- Nonblank check: {stats}",
                "",
            ]
        )
    lines.extend(
        [
            "## Review Stills",
            "",
            "- Midpoint stills: `midpoint_stills/`",
            "- Contact sheet: `contact_sheet_midpoints.jpg`",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Water Membrane v006 to {OUT_DIR}", flush=True)
    results = [
        render_wave_membrane_heightfield(),
        render_ripples_on_wavy_membrane(),
        render_current_as_continuous_surface(),
        render_primitive_tiling_water_surface(),
    ]
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
