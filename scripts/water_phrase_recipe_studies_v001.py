#!/usr/bin/env python3.11
"""
Water phrase recipe studies v001.

Internal black-screen vector studies for clear primitive phrase logic before
any complex water simulation. No fish, birds, figures, heightfield/SDF field
renderer continuation, SD, LoRA, SAM, or YOLO.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

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


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/water_phrase_recipe_studies_v001_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
RECIPES_PATH = ROOT / "track2-deterministic/primitive_grammar/water_phrase_recipes_v001.json"
GRAMMAR_PATH = ROOT / "track2-deterministic/primitive_grammar/grammar_v001.json"
FPS = 24

CIRCLE_RGB = (244, 235, 210)
CRESCENT_RGB = (194, 224, 233)
TRIGON_RGB = (156, 198, 216)
LINE_RGB = (104, 165, 184)
OUTLINE_RGB = (229, 238, 238)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    recipe_id: str
    recipe_name: str
    test: str
    method: str
    caveat: str
    question: str


def black_canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if abs(edge1 - edge0) < 1e-8:
        return 1.0 if value >= edge1 else 0.0
    x = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def envelope(age: float, duration: float = 5.6, fade: float = 0.55) -> float:
    if age < 0.0 or age > duration:
        return 0.0
    return smoothstep(0.0, fade, age) * (1.0 - smoothstep(duration - fade, duration, age))


def reveal(age: float, start: float, fade: float = 0.28) -> float:
    return smoothstep(start, start + fade, age)


def transform_points_aniso(
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


def unit_circle_points(samples: int = 72) -> np.ndarray:
    return np.array(
        [(math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples)) for i in range(samples)],
        dtype=np.float32,
    )


CIRCLE_BASE = unit_circle_points()


def draw_line(frame: np.ndarray, pts: list[tuple[float, float]], *, alpha: float, thickness: int = 2) -> None:
    if len(pts) < 2 or alpha <= 0.0:
        return
    layer = np.zeros_like(frame)
    bgr = (LINE_RGB[2], LINE_RGB[1], LINE_RGB[0])
    cv2.polylines(layer, [np.round(np.array(pts, dtype=np.float32)).astype(np.int32)], False, bgr, thickness, lineType=cv2.LINE_AA)
    frame[:] = np.clip(frame.astype(np.float32) + layer.astype(np.float32) * alpha, 0, 255).astype(np.uint8)


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, *, alpha: float) -> None:
    draw_circle_alpha(
        frame,
        center,
        radius,
        CIRCLE_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.12,
    )


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    alpha: float,
    flip_y: bool = False,
) -> None:
    draw_poly_alpha(
        frame,
        transform_points_aniso(CRESCENT_BASE, center, sx, sy, angle, flip_y=flip_y),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.10,
        outline_thickness=1,
    )


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    *,
    alpha: float,
) -> None:
    draw_poly_alpha(
        frame,
        transform_points_aniso(TRIGON_BASE, center, sx, sy, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.10,
        outline_thickness=1,
    )


def v(angle: float) -> tuple[float, float]:
    return math.cos(angle), math.sin(angle)


def add(p: tuple[float, float], dx: float, dy: float) -> tuple[float, float]:
    return p[0] + dx, p[1] + dy


def local_to_screen(origin: tuple[float, float], axis: float, x: float, y: float) -> tuple[float, float]:
    ax, ay = v(axis)
    nx, ny = -ay, ax
    return origin[0] + ax * x + nx * y, origin[1] + ay * x + ny * y


def draw_core_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    axis: float,
    scale: float,
    t: float,
    *,
    start: float,
    duration: float = 5.6,
    alpha: float = 0.78,
    partial: int = 4,
    cup_toward_origin: bool = True,
    drift: float = 12.0,
    line_alpha: float = 0.0,
) -> None:
    age = t - start
    env = envelope(age, duration=duration)
    if env <= 0.0:
        return
    breathe = 1.0 + 0.035 * math.sin(age * 2.4)
    drift_px = drift * math.sin(age * 0.9)
    moved_origin = local_to_screen(origin, axis, drift_px, 3.0 * math.sin(age * 1.15))
    parts = [
        ("circle", 0.000, 0.00, 0.00, 0.00),
        ("crescent", 0.170, 0.00, 0.22, 0.16),
        ("crescent", 0.335, 0.00, 0.45, 0.30),
        ("trigon", 0.500, 0.00, 0.72, 0.46),
    ]
    if line_alpha > 0:
        path = [local_to_screen(moved_origin, axis, scale * d, 0.0) for _, d, _, _, _ in parts[:partial]]
        draw_line(frame, path, alpha=line_alpha * env, thickness=1)
    for idx, (kind, d, side, r_start, fade_start) in enumerate(parts[:partial]):
        part_alpha = alpha * env * reveal(age, r_start) * (1.0 - 0.07 * idx)
        if part_alpha <= 0.01:
            continue
        outward = 1.0 + 0.050 * reveal(age, r_start) * math.sin(age * 1.2 + idx)
        center = local_to_screen(moved_origin, axis, scale * d * outward, scale * side)
        if kind == "circle":
            draw_circle(frame, center, scale * 0.043 * breathe, alpha=part_alpha * 0.86)
        elif kind == "crescent":
            c_angle = axis + (math.pi if cup_toward_origin else 0.0)
            size = scale * (0.116 if idx == 1 else 0.128)
            draw_crescent(frame, center, size, size * 0.76, c_angle, alpha=part_alpha)
        else:
            draw_trigon(frame, center, scale * 0.088, scale * 0.082, axis, alpha=part_alpha * 0.92)


def draw_pond_ripple(frame: np.ndarray, t: float) -> None:
    draw_core_phrase(frame, (W * 0.32, H * 0.50), 0.05, 660.0, t, start=0.0, alpha=0.84, line_alpha=0.030)
    draw_core_phrase(frame, (W * 0.58, H * 0.64), -0.55, 430.0, t, start=1.65, alpha=0.54, line_alpha=0.020)
    draw_core_phrase(frame, (W * 0.53, H * 0.35), 2.45, 370.0, t, start=3.10, alpha=0.42, partial=3, line_alpha=0.014)


def bend_path(center: tuple[float, float], scale: float, angle: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(40):
        s = i / 39.0
        x = scale * (-0.22 + 0.56 * s)
        y = scale * (0.11 * math.sin((s - 0.15) * math.pi * 1.25))
        pts.append(local_to_screen(center, angle, x, y))
    return pts


def draw_river_bend_cluster(frame: np.ndarray, center: tuple[float, float], angle: float, scale: float, t: float, start: float, alpha: float) -> None:
    age = t - start
    env = envelope(age, duration=5.2)
    if env <= 0:
        return
    slide = scale * 0.018 * math.sin(age * 0.85)
    c = local_to_screen(center, angle, slide, 0)
    draw_line(frame, bend_path(c, scale, angle), alpha=0.035 * env, thickness=2)
    a = alpha * env
    knot = local_to_screen(c, angle, 0.0, -scale * 0.015)
    bend = local_to_screen(c, angle, scale * 0.135, scale * 0.082)
    eddy = local_to_screen(c, angle, scale * 0.235, -scale * 0.044)
    tip = local_to_screen(c, angle, scale * 0.390, scale * 0.012)
    draw_circle(frame, knot, scale * 0.032, alpha=a * reveal(age, 0.0) * 0.72)
    draw_crescent(frame, bend, scale * 0.130, scale * 0.082, angle + 0.25, alpha=a * reveal(age, 0.20))
    draw_crescent(frame, eddy, scale * 0.104, scale * 0.070, angle + math.pi - 0.48, alpha=a * reveal(age, 0.42))
    draw_trigon(frame, tip, scale * 0.080, scale * 0.070, angle + 0.08, alpha=a * reveal(age, 0.66) * 0.90)


def draw_river_bend(frame: np.ndarray, t: float) -> None:
    draw_river_bend_cluster(frame, (W * 0.43, H * 0.50), -0.22, 620.0, t, 0.0, 0.82)
    draw_river_bend_cluster(frame, (W * 0.64, H * 0.65), 0.58, 390.0, t, 2.20, 0.46)


def draw_waterfall_phrase(frame: np.ndarray, origin: tuple[float, float], scale: float, t: float, start: float, alpha: float) -> None:
    age = t - start
    env = envelope(age, duration=5.4)
    if env <= 0:
        return
    axis = math.pi / 2.0
    fall = 12.0 * math.sin(age * 1.10)
    o = add(origin, 4.0 * math.sin(age * 0.8), fall)
    line_pts = [local_to_screen(o, axis, scale * d, 0) for d in (0.0, 0.16, 0.34, 0.55)]
    draw_line(frame, line_pts, alpha=0.028 * env, thickness=2)
    a = alpha * env
    draw_circle(frame, local_to_screen(o, axis, 0.0, 0), scale * 0.033, alpha=a * reveal(age, 0.00) * 0.76)
    draw_crescent(frame, local_to_screen(o, axis, scale * 0.16, -scale * 0.010), scale * 0.096, scale * 0.078, -math.pi / 2.0, alpha=a * reveal(age, 0.18))
    draw_crescent(frame, local_to_screen(o, axis, scale * 0.34, scale * 0.018), scale * 0.106, scale * 0.086, -math.pi / 2.0, alpha=a * reveal(age, 0.42))
    draw_trigon(frame, local_to_screen(o, axis, scale * 0.54, scale * 0.006), scale * 0.082, scale * 0.118, math.pi / 2.0, alpha=a * reveal(age, 0.66) * 0.90)


def draw_waterfall(frame: np.ndarray, t: float) -> None:
    draw_waterfall_phrase(frame, (W * 0.50, H * 0.20), 665.0, t, 0.0, 0.80)
    draw_waterfall_phrase(frame, (W * 0.35, H * 0.28), 420.0, t, 2.0, 0.44)
    draw_waterfall_phrase(frame, (W * 0.65, H * 0.32), 360.0, t, 3.15, 0.34)


def draw_current_knot_instance(frame: np.ndarray, center: tuple[float, float], angle: float, scale: float, t: float, start: float, alpha: float) -> None:
    age = t - start
    env = envelope(age, duration=4.8)
    if env <= 0:
        return
    twist = 0.10 * math.sin(age * 1.8)
    a = alpha * env
    knot = center
    incoming = local_to_screen(center, angle, -scale * 0.125, -scale * 0.018)
    crossing = local_to_screen(center, angle, scale * 0.045, scale * 0.115)
    release = local_to_screen(center, angle, scale * 0.245, scale * 0.050)
    draw_line(frame, [incoming, knot, release], alpha=0.025 * env, thickness=2)
    draw_circle(frame, knot, scale * 0.036, alpha=a * reveal(age, 0.36) * 0.75)
    draw_crescent(frame, incoming, scale * 0.104, scale * 0.074, angle + twist, alpha=a * reveal(age, 0.00))
    draw_crescent(frame, crossing, scale * 0.100, scale * 0.070, angle + math.pi * 0.58 - twist, alpha=a * reveal(age, 0.22))
    draw_trigon(frame, release, scale * 0.074, scale * 0.064, angle + 0.05, alpha=a * reveal(age, 0.66) * 0.92)


def draw_current_knot(frame: np.ndarray, t: float) -> None:
    draw_current_knot_instance(frame, (W * 0.48, H * 0.52), 0.20, 610.0, t, 0.0, 0.82)
    draw_current_knot_instance(frame, (W * 0.72, H * 0.38), -0.75, 335.0, t, 2.65, 0.38)


def draw_rain_impact(frame: np.ndarray, t: float) -> None:
    impacts = [
        ((W * 0.40, H * 0.50), -0.20, 345.0, 0.00, 4, 0.74),
        ((W * 0.62, H * 0.34), 2.15, 245.0, 1.30, 2, 0.46),
        ((W * 0.68, H * 0.66), -2.45, 225.0, 2.35, 3, 0.40),
        ((W * 0.29, H * 0.68), 0.82, 205.0, 3.30, 2, 0.30),
    ]
    for origin, angle, scale, start, partial, alpha in impacts:
        draw_core_phrase(
            frame,
            origin,
            angle,
            scale,
            t,
            start=start,
            duration=2.8,
            alpha=alpha,
            partial=partial,
            drift=4.0,
            line_alpha=0.0,
        )


def draw_wave_duality_instance(frame: np.ndarray, center: tuple[float, float], angle: float, scale: float, t: float, start: float, alpha: float) -> None:
    age = t - start
    env = envelope(age, duration=5.3)
    if env <= 0:
        return
    pulse = math.sin(age * 1.25)
    a = alpha * env
    spine = [local_to_screen(center, angle, scale * x, scale * 0.045 * math.sin((x + 0.2) * math.pi * 2.0)) for x in (-0.20, -0.04, 0.12, 0.30, 0.46)]
    draw_line(frame, spine, alpha=0.028 * env, thickness=2)
    crest = local_to_screen(center, angle, scale * 0.00, -scale * (0.064 + 0.010 * pulse))
    pressure = local_to_screen(center, angle, scale * 0.135, -scale * 0.010)
    trough = local_to_screen(center, angle, scale * 0.285, scale * (0.074 - 0.006 * pulse))
    spill = local_to_screen(center, angle, scale * 0.430, scale * 0.030)
    draw_crescent(frame, crest, scale * 0.144, scale * 0.084, angle + 0.10, alpha=a * reveal(age, 0.00))
    draw_circle(frame, pressure, scale * 0.034, alpha=a * reveal(age, 0.28) * 0.72)
    draw_crescent(frame, trough, scale * 0.108, scale * 0.070, angle + math.pi - 0.12, alpha=a * reveal(age, 0.48) * 0.82)
    draw_trigon(frame, spill, scale * 0.070, scale * 0.060, angle + 0.05, alpha=a * reveal(age, 0.70) * 0.90)


def draw_wave_duality(frame: np.ndarray, t: float) -> None:
    draw_wave_duality_instance(frame, (W * 0.37, H * 0.52), 0.05, 640.0, t, 0.0, 0.82)
    draw_wave_duality_instance(frame, (W * 0.67, H * 0.61), -0.45, 365.0, t, 2.60, 0.42)


def draw_mist_partial_instance(frame: np.ndarray, center: tuple[float, float], angle: float, scale: float, t: float, start: float, alpha: float) -> None:
    age = t - start
    env = envelope(age, duration=5.8, fade=0.90)
    if env <= 0:
        return
    drift = 18.0 * math.sin(age * 0.45)
    c = local_to_screen(center, angle, drift, 3.0 * math.sin(age * 0.5))
    a = alpha * env
    draw_line(frame, [local_to_screen(c, angle, scale * d, 0) for d in (-0.05, 0.18, 0.40)], alpha=0.018 * env, thickness=2)
    draw_crescent(frame, local_to_screen(c, angle, 0.0, 0.0), scale * 0.158, scale * 0.096, angle + math.pi, alpha=a * reveal(age, 0.0) * 0.62)
    draw_crescent(frame, local_to_screen(c, angle, scale * 0.235, scale * 0.020), scale * 0.122, scale * 0.078, angle + math.pi, alpha=a * reveal(age, 0.82) * 0.44)
    draw_trigon(frame, local_to_screen(c, angle, scale * 0.430, scale * 0.020), scale * 0.060, scale * 0.050, angle, alpha=a * reveal(age, 1.65) * 0.34)


def draw_mist_partial(frame: np.ndarray, t: float) -> None:
    draw_mist_partial_instance(frame, (W * 0.36, H * 0.50), 0.34, 680.0, t, 0.0, 0.70)
    draw_mist_partial_instance(frame, (W * 0.60, H * 0.60), -0.18, 420.0, t, 2.35, 0.38)


class PlaneProjector:
    def __init__(self) -> None:
        src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        dst = np.array(
            [
                [W * 0.31, H * 0.22],
                [W * 0.69, H * 0.22],
                [W * 0.91, H * 0.83],
                [W * 0.09, H * 0.83],
            ],
            dtype=np.float32,
        )
        self.mat = cv2.getPerspectiveTransform(src, dst)

    def project(self, pts: np.ndarray) -> np.ndarray:
        projected = cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float32), self.mat)
        return projected.reshape(-1, 2)


def draw_plane_shape(
    frame: np.ndarray,
    projector: PlaneProjector,
    base: np.ndarray,
    center_uv: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    pts = transform_points_aniso(base, center_uv, sx, sy, angle)
    projected = projector.project(pts)
    draw_poly_alpha(
        frame,
        projected,
        rgb,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.10,
        outline_thickness=1,
    )


def draw_perspective_phrase(frame: np.ndarray, t: float) -> None:
    projector = PlaneProjector()
    # Faint plane-space water guides, projected after authoring.
    for row in (0.36, 0.50, 0.64):
        pts = np.array([(0.10 + i * 0.80 / 50.0, row + 0.015 * math.sin(i * 0.25 + t * 0.5)) for i in range(51)], dtype=np.float32)
        draw_line(frame, [tuple(p) for p in projector.project(pts)], alpha=0.024, thickness=1)
    phrases = [
        ((0.30, 0.58), -0.04, 0.220, 0.0, 0.90, 4),
        ((0.58, 0.42), 0.36, 0.150, 2.05, 0.48, 4),
        ((0.47, 0.70), -0.62, 0.125, 3.25, 0.34, 3),
    ]
    for origin, angle, scale, start, alpha, partial in phrases:
        age = t - start
        env = envelope(age, duration=5.3)
        if env <= 0:
            continue
        u0, v0 = origin
        drift = 0.010 * math.sin(age * 0.7)
        parts = [
            ("circle", 0.000, 0.00, 0.00),
            ("crescent", 0.165, 0.22, 0.17),
            ("crescent", 0.335, 0.45, 0.30),
            ("trigon", 0.505, 0.70, 0.44),
        ]
        path_uv = []
        for kind, d, rstart, _ in parts[:partial]:
            cu = u0 + math.cos(angle) * (d * scale + drift)
            cv = v0 + math.sin(angle) * (d * scale + drift)
            path_uv.append((cu, cv))
        draw_line(frame, [tuple(p) for p in projector.project(np.array(path_uv, dtype=np.float32))], alpha=0.018 * env, thickness=1)
        for idx, (kind, d, rstart, _) in enumerate(parts[:partial]):
            a = alpha * env * reveal(age, rstart) * (1.0 - 0.08 * idx)
            if a <= 0.01:
                continue
            cu = u0 + math.cos(angle) * (d * scale + drift)
            cv = v0 + math.sin(angle) * (d * scale + drift)
            if kind == "circle":
                draw_plane_shape(frame, projector, CIRCLE_BASE, (cu, cv), scale * 0.090, scale * 0.090, 0.0, CIRCLE_RGB, alpha=a * 0.82)
            elif kind == "crescent":
                draw_plane_shape(frame, projector, CRESCENT_BASE, (cu, cv), scale * 0.240, scale * 0.160, angle + math.pi, CRESCENT_RGB, alpha=a)
            else:
                draw_plane_shape(frame, projector, TRIGON_BASE, (cu, cv), scale * 0.170, scale * 0.150, angle, TRIGON_RGB, alpha=a * 0.90)


def draw_background_breath(frame: np.ndarray, t: float) -> None:
    # Very faint non-structural glow so black-screen clips remain visible in
    # review without becoming water simulation.
    band = np.zeros_like(frame)
    for y_mul, alpha in [(0.34, 0.012), (0.61, 0.010)]:
        y = int(H * y_mul + 20 * math.sin(t * 0.35 + y_mul))
        cv2.line(band, (int(W * 0.12), y), (int(W * 0.88), y + int(18 * math.sin(t * 0.22))), (LINE_RGB[2], LINE_RGB[1], LINE_RGB[0]), 2, cv2.LINE_AA)
        frame[:] = np.clip(frame.astype(np.float32) + band.astype(np.float32) * alpha, 0, 255).astype(np.uint8)


def render_study(
    filename: str,
    recipe_id: str,
    draw_fn: Callable[[np.ndarray, float], None],
    *,
    test: str,
    method: str,
    caveat: str,
    recipe_lookup: dict[str, dict],
) -> ClipResult:
    out = OUT_DIR / filename
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        draw_background_breath(frame, t)
        draw_fn(frame, t)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  {Path(filename).stem} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    recipe = recipe_lookup.get(recipe_id, {})
    return ClipResult(
        filename=filename,
        recipe_id=recipe_id,
        recipe_name=str(recipe.get("name", recipe_id)),
        test=test,
        method=method,
        caveat=caveat,
        question=str(recipe.get("review_question_for_Austin", "")),
    )


def load_recipe_lookup() -> dict[str, dict]:
    if not RECIPES_PATH.exists():
        return {}
    data = json.loads(RECIPES_PATH.read_text())
    return {recipe["id"]: recipe for recipe in data.get("recipes", [])}


def render_all() -> list[ClipResult]:
    recipe_lookup = load_recipe_lookup()
    return [
        render_study(
            "01_pond_ripple_phrase_v001_black_screen.mp4",
            "pond_ripple_v001",
            draw_pond_ripple,
            test="Still-water impact phrase: circle origin, two close crescents, trigon attenuation.",
            method="One lead phrase appears first; secondary partial phrases enter later with common-fate drift and fade.",
            caveat="Crescent cupping remains an Austin question; this version cups back toward the origin.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "02_river_bend_eddy_phrase_v001_black_screen.mp4",
            "river_bend_eddy_cluster_v001",
            draw_river_bend,
            test="Sparse bend/eddy cluster around a curved water path.",
            method="Circle knot sits near bend compression; crescents bend and return; trigon exits downstream.",
            caveat="The faint spine is an internal guide for phrase topology, not a final approved visual element.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "03_waterfall_vertical_phrase_v001_black_screen.mp4",
            "waterfall_vertical_phrase_v001",
            draw_waterfall,
            test="Vertical falling-water phrase with stacked circle, crescents, and downward trigon.",
            method="Marks descend along a fall axis with tight spacing near the lip and looser spacing below.",
            caveat="Vertical stacking is a review question; this does not claim approval for waterfall grammar.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "04_current_knot_phrase_v001_black_screen.mp4",
            "current_knot_v001",
            draw_current_knot,
            test="Compact current-knot phrase where two current paths meet without paired circles.",
            method="A single circle anchors the knot; two asymmetric crescents align to tangents; trigon releases downstream.",
            caveat="Only one circle is used per knot to avoid eye-pair reads.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "05_rain_impact_phrase_v001_black_screen.mp4",
            "rain_impact_v001",
            draw_rain_impact,
            test="Sparse miniature rain impacts as partial phrase units.",
            method="One clear lead impact plus three staggered smaller partial phrases; most do not complete the full sequence.",
            caveat="This avoids a rain grid, but any repeated circles remain a review risk.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "06_wave_crest_trough_duality_phrase_v001_black_screen.mp4",
            "wave_crest_trough_duality_v001",
            draw_wave_duality,
            test="Wave crest/trough relation without mirrored crescents or paired circles.",
            method="Crest crescent leads, circle marks pressure, trough crescent follows, trigon spills forward.",
            caveat="The circle is a pressure anchor here; Austin may prefer circles only as impact origins.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "07_mist_partial_phrase_v001_black_screen.mp4",
            "mist_partial_phrase_v001",
            draw_mist_partial,
            test="Partial low-contrast mist phrase without visible circle origin.",
            method="Large soft crescents drift and fade, with only a faint terminal trigon in some moments.",
            caveat="Mist/cloud grammar is especially speculative and should stay parked unless Austin responds well.",
            recipe_lookup=recipe_lookup,
        ),
        render_study(
            "08_perspective_water_plane_phrase_v001_black_screen.mp4",
            "perspective_water_plane_phrase_v001",
            draw_perspective_phrase,
            test="Tilted-plane phrase authored in UV space before projection.",
            method="Circle/crescent/crescent/trigon positions and rotations are computed in plane space, then homography-projected.",
            caveat="Perspective water-plane use is an explicit review question, not an approved 3D/relief direction.",
            recipe_lookup=recipe_lookup,
        ),
    ]


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
            Path(result.filename).stem[:48],
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
        "# Water Phrase Recipe Studies v001 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Black-background Add/Screen-ready vector phrase studies; no fish, birds, figures, heightfield/SDF field renderer continuation, SD, LoRA, SAM, or YOLO.",
        "",
        "## Direction",
        "",
        "- This packet pauses the heightfield/SDF field renderer as the main visual.",
        "- The goal is phrase readability before water simulation: visible circle/crescent/crescent/trigon relationships, sparse composition, intentional orientation, and common-fate animation.",
        "- Shapes stay close enough to read as relational phrase units in still frames.",
        "- Uses the Austin-informed recipe docs and `water_phrase_recipes_v001.json`; no output is Austin-approved.",
        "",
        "## Review Order",
        "",
    ]
    for idx, result in enumerate(results, start=1):
        lines.append(f"{idx}. `{result.filename}`")
    lines.extend(["", "## Recipe Notes", ""])
    for result, probe, stats in rows:
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- Recipe: `{result.recipe_id}` / {result.recipe_name}",
                f"- What it tests: {result.test}",
                f"- Technical method: {result.method}",
                f"- Caveat: {result.caveat}",
                f"- Austin question: {result.question}",
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
    print(f"Writing Water Phrase Recipe Studies v001 to {OUT_DIR}", flush=True)
    results = render_all()
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
