#!/usr/bin/env python3.11
"""
Radial water/sun/snowflake morphology stills v001.

PNG-only high-quality morphology packet. Internal Darren grammar exploration
only: Austin-review-needed, not Austin-approved, and not a general Coast Salish
grammar claim.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/radial_water_sun_snowflake_morphology_v001_2026-05-19"
W = 1920
H = 1080
SS = 2
HI_W = W * SS
HI_H = H * SS

BLACK = (0, 0, 0)
IVORY = (244, 244, 236)
SOFT_IVORY = (222, 232, 230)
PALE_BLUE = (168, 220, 238)
ICE_BLUE = (198, 236, 246)
DEEP_BLUE = (54, 116, 155)
SUN_GOLD = (246, 213, 116)
SUN_AMBER = (232, 162, 78)
MIST = (148, 166, 166)


def canvas() -> np.ndarray:
    return np.zeros((HI_H, HI_W, 3), dtype=np.uint8)


def finish(frame: np.ndarray) -> np.ndarray:
    return cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)


def blend_mask(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float) -> None:
    if alpha <= 0:
        return
    a = (mask.astype(np.float32) / 255.0) * max(0.0, min(1.0, alpha))
    if not np.any(a > 0):
        return
    base = frame.astype(np.float32)
    color = rgb_to_bgr(rgb)
    base[:] = base * (1.0 - a[..., None]) + color * a[..., None]
    frame[:] = np.clip(base, 0, 255).astype(np.uint8)


def draw_masked(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    if glow_alpha > 0 and glow_radius > 0:
        blur = cv2.GaussianBlur(mask, (0, 0), glow_radius * SS)
        blend_mask(frame, blur, glow_rgb or rgb, glow_alpha)
    blend_mask(frame, mask, rgb, alpha)


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


def trigon_points(*, sharpness: float = 0.55, softness: float = 0.45, samples: int = 44) -> np.ndarray:
    """Curved trigon with a controlled tip and a rounded/flattened rear base."""

    tip_x = 0.92 + 0.18 * sharpness
    rear_x = -0.58 - 0.06 * softness
    half_h = 0.42 + 0.12 * (1.0 - sharpness * 0.35)
    upper_ctrl_1 = (-0.22, -0.60 + 0.08 * softness)
    upper_ctrl_2 = (0.56, -0.30 - 0.06 * sharpness)
    lower_ctrl_1 = (0.56, 0.30 + 0.06 * sharpness)
    lower_ctrl_2 = (-0.22, 0.60 - 0.08 * softness)
    rear_ctrl_1 = (rear_x - 0.18 - 0.08 * softness, half_h * 0.46)
    rear_ctrl_2 = (rear_x - 0.18 - 0.08 * softness, -half_h * 0.46)
    rear_top = (rear_x, -half_h)
    rear_bottom = (rear_x, half_h)
    tip = (tip_x, 0.0)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(rear_top, upper_ctrl_1, upper_ctrl_2, tip, samples))
    pts.extend(cubic_curve(tip, lower_ctrl_1, lower_ctrl_2, rear_bottom, samples))
    pts.extend(cubic_curve(rear_bottom, rear_ctrl_1, rear_ctrl_2, rear_top, samples, include_endpoint=True))
    return np.array(pts, dtype=np.float32)


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


def poly_mask(pts: np.ndarray) -> np.ndarray:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    hi = np.round(pts * SS).astype(np.int32)
    cv2.fillPoly(mask, [hi], 255, lineType=cv2.LINE_AA)
    return mask


def draw_poly(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    draw_masked(frame, poly_mask(pts), rgb, alpha=alpha, glow_rgb=glow_rgb, glow_alpha=glow_alpha, glow_radius=glow_radius)


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    draw_poly(
        frame,
        transform_points(CRESCENT_BASE, center, sx, sy, angle),
        rgb,
        alpha=alpha,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha,
        glow_radius=glow_radius,
    )


def draw_crescent_cupping(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    angle_to_origin = math.atan2(origin[1] - center[1], origin[0] - center[0])
    draw_crescent(
        frame,
        center,
        sx,
        sy,
        angle_to_origin - math.pi,
        rgb,
        alpha=alpha,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha,
        glow_radius=glow_radius,
    )


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    sharpness: float = 0.55,
    softness: float = 0.45,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    draw_poly(
        frame,
        transform_points(trigon_points(sharpness=sharpness, softness=softness), center, sx, sy, angle),
        rgb,
        alpha=alpha,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha,
        glow_radius=glow_radius,
    )


def draw_trigon_release(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    sharpness: float = 0.55,
    softness: float = 0.45,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    angle = math.atan2(center[1] - origin[1], center[0] - origin[0])
    draw_trigon(
        frame,
        center,
        sx,
        sy,
        angle,
        rgb,
        alpha=alpha,
        sharpness=sharpness,
        softness=softness,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha,
        glow_radius=glow_radius,
    )


def draw_circle(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    cv2.circle(mask, (round(center[0] * SS), round(center[1] * SS)), round(radius * SS), 255, -1, lineType=cv2.LINE_AA)
    draw_masked(frame, mask, rgb, alpha=alpha, glow_rgb=glow_rgb, glow_alpha=glow_alpha, glow_radius=glow_radius)


def draw_ring(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    thickness: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    cv2.circle(
        mask,
        (round(center[0] * SS), round(center[1] * SS)),
        round(radius * SS),
        255,
        max(1, round(thickness * SS)),
        lineType=cv2.LINE_AA,
    )
    draw_masked(frame, mask, rgb, alpha=alpha, glow_rgb=glow_rgb, glow_alpha=glow_alpha, glow_radius=glow_radius)


def draw_oval(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float = 1.0,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    glow_radius: int = 0,
) -> None:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (round(center[0] * SS), round(center[1] * SS)),
        (round(axes[0] * SS), round(axes[1] * SS)),
        math.degrees(angle),
        0,
        360,
        255,
        -1,
        lineType=cv2.LINE_AA,
    )
    draw_masked(frame, mask, rgb, alpha=alpha, glow_rgb=glow_rgb, glow_alpha=glow_alpha, glow_radius=glow_radius)


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
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (round(center[0] * SS), round(center[1] * SS)),
        (round(axes[0] * SS), round(axes[1] * SS)),
        math.degrees(angle),
        math.degrees(start),
        math.degrees(end),
        255,
        max(1, round(thickness * SS)),
        lineType=cv2.LINE_AA,
    )
    draw_masked(frame, mask, rgb, alpha=alpha)


def draw_line(frame: np.ndarray, pts: list[tuple[float, float]], rgb: tuple[int, int, int], *, alpha: float, thickness: float) -> None:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    hi = np.round(np.array(pts, dtype=np.float32) * SS).astype(np.int32)
    cv2.polylines(mask, [hi], False, 255, max(1, round(thickness * SS)), cv2.LINE_AA)
    draw_masked(frame, mask, rgb, alpha=alpha)


def radial_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    angle: float,
    *,
    distances: tuple[float, float, float] = (185, 320, 470),
    scale: float = 1.0,
    rgb: tuple[int, int, int] = IVORY,
    trigon_rgb: tuple[int, int, int] | None = None,
    alpha: float = 1.0,
    crescent_thickness: tuple[float, float] = (1.0, 1.0),
    trigon_sharpness: float = 0.55,
    trigon_softness: float = 0.45,
    glow_rgb: tuple[int, int, int] | None = None,
    glow_alpha: float = 0.0,
    separated: bool = True,
) -> None:
    d1, d2, d3 = distances
    if not separated:
        d2 = d1 + 98 * scale
        d3 = d2 + 118 * scale
    c1 = (origin[0] + math.cos(angle) * d1, origin[1] + math.sin(angle) * d1)
    c2 = (origin[0] + math.cos(angle) * d2, origin[1] + math.sin(angle) * d2)
    tri = (origin[0] + math.cos(angle) * d3, origin[1] + math.sin(angle) * d3)
    draw_crescent_cupping(
        frame,
        c1,
        origin,
        96 * scale * crescent_thickness[0],
        66 * scale,
        rgb,
        alpha=alpha * 0.90,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha,
        glow_radius=12,
    )
    draw_crescent_cupping(
        frame,
        c2,
        origin,
        116 * scale * crescent_thickness[1],
        80 * scale,
        rgb,
        alpha=alpha * 0.74,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha * 0.65,
        glow_radius=12,
    )
    draw_trigon_release(
        frame,
        tri,
        origin,
        82 * scale,
        90 * scale,
        trigon_rgb or rgb,
        alpha=alpha * 0.58,
        sharpness=trigon_sharpness,
        softness=trigon_softness,
        glow_rgb=glow_rgb,
        glow_alpha=glow_alpha * 0.45,
        glow_radius=10,
    )


def radial_angles(count: int, *, start: float = 0.0) -> list[float]:
    return [start + (2.0 * math.pi * i / count) for i in range(count)]


def add_radial_haze(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], alpha: float) -> None:
    mask = np.zeros((HI_H, HI_W), dtype=np.uint8)
    cv2.circle(mask, (round(center[0] * SS), round(center[1] * SS)), round(radius * SS), 255, -1, lineType=cv2.LINE_AA)
    blur = cv2.GaussianBlur(mask, (0, 0), 80 * SS)
    blend_mask(frame, blur, rgb, alpha)


def study_01_sun_origin_rays() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    add_radial_haze(frame, center, 420, SUN_GOLD, 0.12)
    draw_circle(frame, center, 86, SUN_GOLD, alpha=0.92, glow_rgb=SUN_AMBER, glow_alpha=0.18, glow_radius=28)
    draw_ring(frame, center, 126, 8, IVORY, alpha=0.34)
    for angle in radial_angles(8, start=math.radians(7)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(220, 360, 525),
            scale=1.10,
            rgb=IVORY,
            trigon_rgb=SUN_GOLD,
            alpha=0.82,
            crescent_thickness=(0.92, 1.12),
            trigon_sharpness=0.72,
            trigon_softness=0.32,
            glow_rgb=SUN_GOLD,
            glow_alpha=0.055,
        )
    return finish(frame)


def study_02_sun_negative_space_disc() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    add_radial_haze(frame, center, 470, SUN_AMBER, 0.11)
    draw_circle(frame, center, 248, SUN_GOLD, alpha=0.80, glow_rgb=SUN_GOLD, glow_alpha=0.10, glow_radius=36)
    for angle in radial_angles(6, start=math.radians(30)):
        cut = (center[0] + math.cos(angle) * 155, center[1] + math.sin(angle) * 155)
        draw_crescent_cupping(frame, cut, center, 118, 74, BLACK, alpha=0.95)
    draw_ring(frame, center, 248, 5, IVORY, alpha=0.38)
    for angle in radial_angles(6, start=math.radians(0)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(330, 450, 615),
            scale=0.95,
            rgb=SOFT_IVORY,
            trigon_rgb=SUN_GOLD,
            alpha=0.76,
            crescent_thickness=(0.72, 0.90),
            trigon_sharpness=0.62,
            glow_rgb=SUN_GOLD,
            glow_alpha=0.04,
        )
    return finish(frame)


def study_03_sun_rotation_pinwheel() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    add_radial_haze(frame, center, 430, SUN_GOLD, 0.10)
    draw_oval(frame, center, (112, 88), math.radians(-12), IVORY, alpha=0.86, glow_rgb=SUN_GOLD, glow_alpha=0.12, glow_radius=24)
    for idx, angle in enumerate(radial_angles(7, start=math.radians(-18))):
        twist = angle + math.radians(14)
        c1 = (center[0] + math.cos(twist) * 195, center[1] + math.sin(twist) * 195)
        c2 = (center[0] + math.cos(twist + 0.10) * 335, center[1] + math.sin(twist + 0.10) * 335)
        tri = (center[0] + math.cos(twist + 0.18) * 515, center[1] + math.sin(twist + 0.18) * 515)
        draw_crescent_cupping(frame, c1, center, 136, 74, IVORY, alpha=0.78 - idx * 0.025, glow_rgb=SUN_GOLD, glow_alpha=0.035, glow_radius=12)
        draw_crescent_cupping(frame, c2, center, 150, 82, SOFT_IVORY, alpha=0.58 - idx * 0.018)
        draw_trigon_release(frame, tri, center, 110, 118, SUN_GOLD, alpha=0.48, sharpness=0.78, softness=0.26)
    return finish(frame)


def study_04_sun_corona_contraction() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_ring(frame, center, 92, 26, SUN_GOLD, alpha=0.84, glow_rgb=SUN_AMBER, glow_alpha=0.16, glow_radius=28)
    draw_circle(frame, center, 36, BLACK, alpha=1.0)
    for angle in radial_angles(10, start=math.radians(18)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(170, 272, 392),
            scale=0.72,
            rgb=IVORY,
            trigon_rgb=SUN_AMBER,
            alpha=0.74,
            crescent_thickness=(0.58, 1.32),
            trigon_sharpness=0.58,
            trigon_softness=0.52,
            separated=False,
        )
    draw_ring(frame, center, 430, 3, SUN_GOLD, alpha=0.12)
    return finish(frame)


def study_05_pond_single_impact() -> np.ndarray:
    frame = canvas()
    center = (720.0, 570.0)
    add_radial_haze(frame, center, 520, PALE_BLUE, 0.08)
    draw_circle(frame, center, 62, IVORY, alpha=0.92, glow_rgb=PALE_BLUE, glow_alpha=0.10, glow_radius=28)
    for r, a in [(165, 0.18), (318, 0.12), (505, 0.07), (690, 0.035)]:
        draw_ring(frame, center, r, 4, PALE_BLUE, alpha=a)
    for angle, strength, scale in [(math.radians(-18), 0.92, 1.18), (math.radians(10), 0.76, 1.02), (math.radians(38), 0.58, 0.88)]:
        radial_phrase(
            frame,
            center,
            angle,
            distances=(225, 405, 605),
            scale=scale,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=strength,
            crescent_thickness=(0.86, 1.08),
            trigon_sharpness=0.50,
            trigon_softness=0.72,
        )
    return finish(frame)


def study_06_rain_three_impacts() -> np.ndarray:
    frame = canvas()
    centers = [(610.0, 445.0), (960.0, 610.0), (1295.0, 438.0)]
    for idx, center in enumerate(centers):
        alpha = 0.78 - idx * 0.08
        draw_circle(frame, center, 38, IVORY, alpha=alpha, glow_rgb=PALE_BLUE, glow_alpha=0.08, glow_radius=22)
        draw_ring(frame, center, 118, 4, PALE_BLUE, alpha=0.13)
        draw_ring(frame, center, 238, 4, PALE_BLUE, alpha=0.07)
        for angle in [math.radians(24 + idx * 18), math.radians(146 + idx * 10), math.radians(266 - idx * 14)]:
            radial_phrase(
                frame,
                center,
                angle,
                distances=(135, 235, 352),
                scale=0.62,
                rgb=SOFT_IVORY,
                trigon_rgb=MIST,
                alpha=0.52,
                crescent_thickness=(0.72, 0.86),
                trigon_sharpness=0.45,
                trigon_softness=0.75,
            )
    return finish(frame)


def study_07_ripple_phase_offsets() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_oval(frame, center, (74, 54), 0.0, IVORY, alpha=0.86, glow_rgb=PALE_BLUE, glow_alpha=0.08, glow_radius=22)
    for r, thickness, alpha in [(150, 3, 0.10), (260, 6, 0.16), (382, 4, 0.08), (535, 8, 0.09)]:
        draw_ring(frame, center, r, thickness, PALE_BLUE, alpha=alpha)
    for angle, dset, scale, alpha in [
        (math.radians(-48), (150, 260, 382), 0.82, 0.84),
        (math.radians(6), (260, 382, 535), 0.96, 0.70),
        (math.radians(58), (382, 535, 690), 1.08, 0.52),
    ]:
        radial_phrase(
            frame,
            center,
            angle,
            distances=dset,
            scale=scale,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=alpha,
            crescent_thickness=(0.72, 1.26),
            trigon_sharpness=0.42,
            trigon_softness=0.82,
        )
    return finish(frame)


def study_08_ripple_contraction() -> np.ndarray:
    frame = canvas()
    center = (1030.0, 540.0)
    add_radial_haze(frame, center, 480, DEEP_BLUE, 0.07)
    draw_ring(frame, center, 112, 18, IVORY, alpha=0.54)
    draw_circle(frame, center, 46, BLACK, alpha=1.0)
    for angle in radial_angles(5, start=math.radians(-20)):
        # The outer trigon remains a release mark, while the thick crescents
        # compress toward the origin.
        radial_phrase(
            frame,
            center,
            angle,
            distances=(270, 192, 410),
            scale=1.05,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=0.70,
            crescent_thickness=(1.34, 0.78),
            trigon_sharpness=0.46,
            trigon_softness=0.70,
            separated=True,
        )
    draw_ring(frame, center, 420, 5, PALE_BLUE, alpha=0.08)
    return finish(frame)


def study_09_snowflake_sixfold() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    add_radial_haze(frame, center, 380, ICE_BLUE, 0.08)
    draw_ring(frame, center, 74, 14, ICE_BLUE, alpha=0.82, glow_rgb=ICE_BLUE, glow_alpha=0.08, glow_radius=18)
    for angle in radial_angles(6, start=math.radians(30)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(165, 295, 455),
            scale=0.88,
            rgb=ICE_BLUE,
            trigon_rgb=SOFT_IVORY,
            alpha=0.78,
            crescent_thickness=(0.50, 0.62),
            trigon_sharpness=0.84,
            trigon_softness=0.22,
        )
        for branch_sign in [-1, 1]:
            branch_angle = angle + branch_sign * math.radians(34)
            branch_origin = (center[0] + math.cos(angle) * 260, center[1] + math.sin(angle) * 260)
            branch_tip = (branch_origin[0] + math.cos(branch_angle) * 145, branch_origin[1] + math.sin(branch_angle) * 145)
            draw_trigon_release(frame, branch_tip, branch_origin, 46, 54, ICE_BLUE, alpha=0.34, sharpness=0.82, softness=0.26)
    return finish(frame)


def study_10_frozen_thin_lattice() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_circle(frame, center, 34, ICE_BLUE, alpha=0.88, glow_rgb=ICE_BLUE, glow_alpha=0.06, glow_radius=14)
    for angle in radial_angles(8, start=math.radians(22.5)):
        end = (center[0] + math.cos(angle) * 575, center[1] + math.sin(angle) * 575)
        draw_line(frame, [center, end], ICE_BLUE, alpha=0.09, thickness=4)
        radial_phrase(
            frame,
            center,
            angle,
            distances=(180, 330, 520),
            scale=0.72,
            rgb=SOFT_IVORY,
            trigon_rgb=ICE_BLUE,
            alpha=0.54,
            crescent_thickness=(0.38, 0.46),
            trigon_sharpness=0.86,
            trigon_softness=0.18,
        )
    draw_ring(frame, center, 335, 3, ICE_BLUE, alpha=0.10)
    return finish(frame)


def study_11_snowflake_negative_core() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_circle(frame, center, 185, ICE_BLUE, alpha=0.58, glow_rgb=ICE_BLUE, glow_alpha=0.07, glow_radius=24)
    for angle in radial_angles(6):
        cut = (center[0] + math.cos(angle) * 116, center[1] + math.sin(angle) * 116)
        draw_crescent_cupping(frame, cut, center, 82, 50, BLACK, alpha=0.95)
    draw_ring(frame, center, 185, 5, SOFT_IVORY, alpha=0.26)
    for angle in radial_angles(6, start=math.radians(30)):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(250, 370, 520),
            scale=0.74,
            rgb=SOFT_IVORY,
            trigon_rgb=ICE_BLUE,
            alpha=0.60,
            crescent_thickness=(0.48, 0.58),
            trigon_sharpness=0.90,
            trigon_softness=0.12,
        )
    return finish(frame)


def study_12_ice_star_soft_points() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_oval(frame, center, (70, 44), math.radians(18), SOFT_IVORY, alpha=0.78, glow_rgb=ICE_BLUE, glow_alpha=0.07, glow_radius=18)
    for idx, angle in enumerate(radial_angles(6, start=math.radians(5))):
        radial_phrase(
            frame,
            center,
            angle,
            distances=(150, 285, 450),
            scale=1.00 if idx % 2 == 0 else 0.82,
            rgb=ICE_BLUE,
            trigon_rgb=SOFT_IVORY,
            alpha=0.66,
            crescent_thickness=(0.66, 0.78),
            trigon_sharpness=0.52,
            trigon_softness=0.84,
        )
    draw_ring(frame, center, 455, 3, ICE_BLUE, alpha=0.08)
    return finish(frame)


def study_13_abstract_asymmetric_field() -> np.ndarray:
    frame = canvas()
    center = (780.0, 580.0)
    add_radial_haze(frame, center, 560, PALE_BLUE, 0.06)
    draw_oval(frame, center, (84, 62), math.radians(-20), IVORY, alpha=0.82)
    for angle, alpha, scale, color in [
        (math.radians(-52), 0.72, 1.20, SOFT_IVORY),
        (math.radians(-10), 0.88, 1.06, IVORY),
        (math.radians(35), 0.58, 0.92, MIST),
        (math.radians(82), 0.42, 0.74, PALE_BLUE),
    ]:
        radial_phrase(
            frame,
            center,
            angle,
            distances=(210, 355, 565),
            scale=scale,
            rgb=color,
            trigon_rgb=color,
            alpha=alpha,
            crescent_thickness=(0.92, 1.18),
            trigon_sharpness=0.62,
            trigon_softness=0.46,
        )
    return finish(frame)


def study_14_abstract_orbital_wavefronts() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    draw_oval(frame, center, (92, 58), math.radians(22), IVORY, alpha=0.82, glow_rgb=PALE_BLUE, glow_alpha=0.06, glow_radius=16)
    for i, axes in enumerate([(190, 122), (330, 210), (500, 310), (675, 420)]):
        draw_arc(frame, center, axes, math.radians(-14), math.radians(205), math.radians(335), PALE_BLUE, alpha=0.13 - i * 0.018, thickness=5)
    for angle in [math.radians(-28), math.radians(12), math.radians(52), math.radians(92)]:
        radial_phrase(
            frame,
            center,
            angle,
            distances=(210, 360, 540),
            scale=0.86,
            rgb=SOFT_IVORY,
            trigon_rgb=MIST,
            alpha=0.58,
            crescent_thickness=(1.16, 0.72),
            trigon_sharpness=0.50,
            trigon_softness=0.58,
        )
    return finish(frame)


def study_15_abstract_reticulated_radial_growth() -> np.ndarray:
    frame = canvas()
    center = (880.0, 545.0)
    nodes = [
        center,
        (1135.0, 380.0),
        (1260.0, 650.0),
        (1485.0, 480.0),
        (1520.0, 760.0),
    ]
    draw_circle(frame, center, 64, IVORY, alpha=0.84, glow_rgb=PALE_BLUE, glow_alpha=0.05, glow_radius=16)
    for idx, node in enumerate(nodes[1:], start=1):
        angle = math.atan2(node[1] - center[1], node[0] - center[0])
        draw_line(frame, [center, node], PALE_BLUE, alpha=0.08, thickness=4)
        anchor = (center[0] + math.cos(angle) * 170, center[1] + math.sin(angle) * 170)
        draw_crescent_cupping(frame, anchor, center, 104 - idx * 7, 66 - idx * 3, SOFT_IVORY, alpha=0.66 - idx * 0.06)
        draw_oval(frame, node, (54 - idx * 4, 36 - idx * 2), angle, IVORY if idx < 3 else MIST, alpha=0.70 - idx * 0.05)
        tip = (center[0] + math.cos(angle) * 520, center[1] + math.sin(angle) * 520)
        draw_trigon_release(frame, tip, center, 58, 62, MIST, alpha=0.34, sharpness=0.54, softness=0.60)
    return finish(frame)


def study_16_abstract_contact_morphology() -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    add_radial_haze(frame, center, 470, ICE_BLUE, 0.06)
    draw_ring(frame, center, 106, 20, IVORY, alpha=0.72, glow_rgb=PALE_BLUE, glow_alpha=0.07, glow_radius=18)
    draw_oval(frame, center, (42, 30), math.radians(-12), BLACK, alpha=1.0)
    for idx, angle in enumerate(radial_angles(8, start=math.radians(10))):
        alpha = 0.78 if idx in (0, 1, 2) else 0.46
        radial_phrase(
            frame,
            center,
            angle,
            distances=(175, 300 + (idx % 2) * 35, 465 + (idx % 3) * 22),
            scale=0.88 if idx % 2 == 0 else 0.74,
            rgb=SOFT_IVORY if idx < 4 else MIST,
            trigon_rgb=SUN_GOLD if idx in (0, 1) else PALE_BLUE,
            alpha=alpha,
            crescent_thickness=(0.70 + 0.10 * (idx % 3), 1.00),
            trigon_sharpness=0.48 + 0.08 * (idx % 4),
            trigon_softness=0.58,
        )
    draw_ring(frame, center, 515, 4, PALE_BLUE, alpha=0.08)
    return finish(frame)


def save_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    studies = [
        ("01_sun_origin_ray_cupped_crescents.png", study_01_sun_origin_rays()),
        ("02_sun_negative_space_disc.png", study_02_sun_negative_space_disc()),
        ("03_sun_rotation_pinwheel.png", study_03_sun_rotation_pinwheel()),
        ("04_sun_corona_contraction.png", study_04_sun_corona_contraction()),
        ("05_pond_single_impact_wavefronts.png", study_05_pond_single_impact()),
        ("06_rain_three_impact_shared_radial_field.png", study_06_rain_three_impacts()),
        ("07_ripple_expansion_phase_offsets.png", study_07_ripple_phase_offsets()),
        ("08_ripple_contraction_return_current.png", study_08_ripple_contraction()),
        ("09_snowflake_sixfold_crescent_branching.png", study_09_snowflake_sixfold()),
        ("10_frozen_water_thin_crescent_lattice.png", study_10_frozen_thin_lattice()),
        ("11_snowflake_negative_space_core.png", study_11_snowflake_negative_core()),
        ("12_ice_star_soft_trigon_points.png", study_12_ice_star_soft_points()),
        ("13_abstract_radial_impact_field_asymmetry.png", study_13_abstract_asymmetric_field()),
        ("14_abstract_orbital_wavefronts.png", study_14_abstract_orbital_wavefronts()),
        ("15_abstract_reticulated_radial_growth.png", study_15_abstract_reticulated_radial_growth()),
        ("16_abstract_radial_morphology_contact.png", study_16_abstract_contact_morphology()),
    ]
    for name, frame in studies:
        cv2.imwrite(str(OUT_DIR / name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(f"Wrote {len(studies)} PNG morphology stills to {OUT_DIR}")


if __name__ == "__main__":
    save_all()
