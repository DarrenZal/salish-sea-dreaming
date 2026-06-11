#!/usr/bin/env python3
"""
Integrated choreographer v001.

Internal mathematical/visual alignment study for Salish Sea Dreaming. This
renderer gathers scalar wave sources into target layouts, then fades in a
primitive composition only when the wave layout has reached the matching target
geometry.

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import cymatic_field_topology_v007 as base


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v001_2026-05-21"
)
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"

W = base.W
H = base.H
FW = base.FW
FH = base.FH
FPS = base.FPS
DURATION_SECONDS = 12.0
N_FRAMES = int(FPS * DURATION_SECONDS)
MIDPOINT_FRAME = int(6.0 * FPS)
PEAK_FRAME = int(6.4 * FPS)
TAU = math.tau

BLACK = (0, 0, 0)
IVORY = (238, 242, 232)
SOFT_IVORY = (208, 224, 218)
CREAM = (236, 229, 197)
PALE_BLUE = (136, 219, 238)
TEAL = (64, 178, 190)
DARK_TEAL = (6, 34, 40)
DEEP_TEAL = (14, 61, 70)
MUTED_GOLD = (213, 178, 112)
GOLD = (246, 197, 92)
INK = (0, 8, 10)
LABEL = (226, 234, 230)


@dataclass(frozen=True)
class TargetSource:
    source_id: str
    x: float
    y: float
    amplitude: float
    drift_scale: float
    orbit_phase: float
    orbit_speed: float
    phase_perturb: float


@dataclass(frozen=True)
class TargetSpec:
    key: str
    filename: str
    title: str
    symmetry_type: str
    source_spacing: float
    drift_amplitude: float
    wavelength: float
    frequency: float
    decay: float
    node_epsilon: float
    threshold: float
    boundary_type: str
    reference_notes: str
    sources: tuple[TargetSource, ...]
    primitive_renderer: Callable[[np.ndarray, "TargetSpec", float, bool], None]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def coherence_at_time(time_seconds: float) -> float:
    """0-3 drift, 3-5 gather, 5-8 lock, 8-10 release, 10-12 drift."""
    t = time_seconds % DURATION_SECONDS
    if t < 3.0:
        return 0.0
    if t < 5.0:
        return smoothstep01((t - 3.0) / 2.0)
    if t < 8.0:
        return 1.0
    if t < 10.0:
        return 1.0 - smoothstep01((t - 8.0) / 2.0)
    return 0.0


def primitive_alpha_for_coherence(coherence: float) -> float:
    return smoothstep01((coherence - 0.7) / 0.3)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def blend_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0:
        return
    color = np.array(rgb_to_bgr(rgb), dtype=np.float32)
    mask_f = (mask.astype(np.float32) / 255.0) * alpha
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask, (0, 0), 9.0)
        frame[:] = np.clip(
            frame.astype(np.float32) + color * ((blur.astype(np.float32) / 255.0) * glow)[..., None],
            0,
            255,
        ).astype(np.uint8)
    out = frame.astype(np.float32)
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[:] = np.clip(out, 0, 255).astype(np.uint8)


def add_poly_mask(
    frame: np.ndarray,
    points: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    outline_rgb: tuple[int, int, int] | None = None,
    outline_alpha: float = 0.0,
) -> None:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.round(points).astype(np.int32)], 255, lineType=cv2.LINE_AA)
    blend_mask(frame, mask, rgb, alpha, glow=0.006)
    if outline_rgb is not None and outline_alpha > 0.0:
        overlay = np.zeros_like(frame)
        cv2.polylines(
            overlay,
            [np.round(points).astype(np.int32)],
            True,
            rgb_to_bgr(outline_rgb),
            2,
            lineType=cv2.LINE_AA,
        )
        cv2.addWeighted(overlay, outline_alpha, frame, 1.0, 0, dst=frame)


def ellipse_mask(
    center: tuple[float, float],
    axes: tuple[float, float],
    angle_degrees: float = 0.0,
    start: float = 0.0,
    end: float = 360.0,
    *,
    thickness: int = -1,
) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (round(center[0]), round(center[1])),
        (max(1, round(axes[0])), max(1, round(axes[1]))),
        angle_degrees,
        start,
        end,
        255,
        thickness,
        lineType=cv2.LINE_AA,
    )
    return mask


def transform_points(
    origin: tuple[float, float],
    angle: float,
    local_points: list[tuple[float, float]],
) -> np.ndarray:
    ca = math.cos(angle)
    sa = math.sin(angle)
    ox, oy = origin
    pts = []
    for x, y in local_points:
        pts.append((ox + ca * x - sa * y, oy + sa * x + ca * y))
    return np.array(pts, dtype=np.float32)


def curved_trigon_points(
    origin: tuple[float, float],
    angle: float,
    length: float,
    half_width: float,
    *,
    waist: float = 0.44,
    curve: float = 0.18,
    samples: int = 18,
) -> np.ndarray:
    """Three-corner ray/fin region in local +x orientation."""
    left_base = (-length * 0.42, -half_width)
    apex = (length * 0.58, 0.0)
    right_base = (-length * 0.42, half_width)
    back = (-length * 0.30, 0.0)
    local: list[tuple[float, float]] = []
    for i in range(samples):
        t = i / (samples - 1)
        x = (1.0 - t) ** 2 * left_base[0] + 2.0 * (1.0 - t) * t * (length * waist) + t * t * apex[0]
        y = (1.0 - t) ** 2 * left_base[1] + 2.0 * (1.0 - t) * t * (-half_width * curve) + t * t * apex[1]
        local.append((x, y))
    for i in range(1, samples):
        t = i / (samples - 1)
        x = (1.0 - t) ** 2 * apex[0] + 2.0 * (1.0 - t) * t * (length * waist) + t * t * right_base[0]
        y = (1.0 - t) ** 2 * apex[1] + 2.0 * (1.0 - t) * t * (half_width * curve) + t * t * right_base[1]
        local.append((x, y))
    for i in range(1, samples):
        t = i / (samples - 1)
        x = (1.0 - t) ** 2 * right_base[0] + 2.0 * (1.0 - t) * t * (-length * 0.50) + t * t * back[0]
        y = (1.0 - t) ** 2 * right_base[1] + 2.0 * (1.0 - t) * t * 0.0 + t * t * back[1]
        local.append((x, y))
    for i in range(1, samples - 1):
        t = i / (samples - 1)
        x = (1.0 - t) ** 2 * back[0] + 2.0 * (1.0 - t) * t * (-length * 0.50) + t * t * left_base[0]
        y = (1.0 - t) ** 2 * back[1] + 2.0 * (1.0 - t) * t * 0.0 + t * t * left_base[1]
        local.append((x, y))
    return transform_points(origin, angle, local)


def target_centroid(target: TargetSpec) -> tuple[float, float]:
    xs = [source.x for source in target.sources]
    ys = [source.y for source in target.sources]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def source_position(target: TargetSpec, source: TargetSource, time_seconds: float, coherence: float) -> tuple[float, float]:
    radius = target.drift_amplitude * source.drift_scale * (1.0 - coherence * coherence)
    angle = TAU * (source.orbit_phase + source.orbit_speed * time_seconds / DURATION_SECONDS)
    wobble = 0.28 * math.sin(TAU * (0.07 * time_seconds + source.phase_perturb))
    return (
        source.x + radius * math.cos(angle + wobble),
        source.y + radius * math.sin(angle + wobble),
    )


def target_sources_at(target: TargetSpec, time_seconds: float, coherence: float | None = None) -> list[base.WaveSource]:
    c = coherence_at_time(time_seconds) if coherence is None else coherence
    locked_phase = TAU * target.frequency * 6.0 - TAU * target.source_spacing / target.wavelength
    wave_sources: list[base.WaveSource] = []
    for source in target.sources:
        x, y = source_position(target, source, time_seconds, c)
        perturb = (1.0 - c) * 0.75 * math.sin(TAU * (0.05 * time_seconds + source.phase_perturb))
        wave_sources.append(
            base.WaveSource(
                source_id=source.source_id,
                x=x,
                y=y,
                amplitude=source.amplitude,
                wavelength=target.wavelength,
                frequency=target.frequency,
                phase=locked_phase + perturb,
                decay=target.decay,
                velocity=(0.0, 0.0),
                birth_time=0.0,
                lifetime=999.0,
                symmetry_order=6 if target.symmetry_type == "C6v" else 1,
                mode="continuous",
            )
        )
    return wave_sources


def radial_sources() -> tuple[TargetSource, ...]:
    cx, cy = W * 0.5, H * 0.5
    spacing = 250.0
    sources = [
        TargetSource("radial_center", cx, cy, 1.18, 0.42, 0.11, 0.34, 0.07),
    ]
    for idx in range(6):
        angle = TAU * idx / 6.0
        sources.append(
            TargetSource(
                f"radial_ring_{idx}",
                cx + spacing * math.cos(angle),
                cy + spacing * math.sin(angle),
                0.94,
                1.0,
                0.17 * idx + 0.03,
                0.20 + 0.035 * idx,
                0.13 * idx + 0.19,
            )
        )
    return tuple(sources)


def axial_sources() -> tuple[TargetSource, ...]:
    cx, cy = W * 0.5, H * 0.5
    unit = 275.0
    return (
        TargetSource("axial_left", cx - unit, cy, 1.08, 0.96, 0.19, 0.22, 0.18),
        TargetSource("axial_right", cx + unit, cy, 1.08, 0.96, 0.64, -0.19, 0.51),
    )


def linear_sources() -> tuple[TargetSource, ...]:
    cx, cy = W * 0.5, H * 0.5
    unit = 210.0
    coords = [
        (-2.0 * unit, 54.0),
        (-1.0 * unit, -42.0),
        (0.0, -10.0),
        (1.0 * unit, 42.0),
        (2.0 * unit, -50.0),
    ]
    sources = []
    for idx, (dx, dy) in enumerate(coords):
        sources.append(
            TargetSource(
                f"flow_{idx}",
                cx + dx,
                cy + dy,
                1.0,
                0.88,
                0.21 * idx + 0.08,
                0.18 + 0.025 * idx,
                0.27 * idx + 0.11,
            )
        )
    return tuple(sources)


def radial_primitive(frame: np.ndarray, target: TargetSpec, alpha: float, labels: bool = False) -> None:
    cx, cy = target_centroid(target)
    spacing = target.source_spacing
    center_mask = ellipse_mask((cx, cy), (0.30 * spacing, 0.30 * spacing))
    blend_mask(frame, center_mask, IVORY, 0.86 * alpha, glow=0.025)
    outline = np.zeros_like(frame)
    cv2.ellipse(outline, (round(cx), round(cy)), (round(0.30 * spacing), round(0.30 * spacing)), 0, 0, 360, rgb_to_bgr(GOLD), 2, lineType=cv2.LINE_AA)
    cv2.addWeighted(outline, 0.50 * alpha, frame, 1.0, 0, dst=frame)

    crescent_layer = np.zeros_like(frame)
    for idx in range(6):
        angle_deg = 60.0 * idx
        cv2.ellipse(
            crescent_layer,
            (round(cx), round(cy)),
            (round(1.05 * spacing), round(1.05 * spacing)),
            0,
            angle_deg - 20,
            angle_deg + 20,
            rgb_to_bgr(SOFT_IVORY),
            round(0.13 * spacing),
            lineType=cv2.LINE_AA,
        )
        cv2.ellipse(
            crescent_layer,
            (round(cx), round(cy)),
            (round(0.92 * spacing), round(0.92 * spacing)),
            0,
            angle_deg - 18,
            angle_deg + 18,
            rgb_to_bgr(PALE_BLUE),
            max(3, round(0.025 * spacing)),
            lineType=cv2.LINE_AA,
        )
    cv2.addWeighted(crescent_layer, 0.72 * alpha, frame, 1.0, 0, dst=frame)

    for idx in range(6):
        angle = TAU * (idx + 0.5) / 6.0
        origin = (cx + 1.58 * spacing * math.cos(angle), cy + 1.58 * spacing * math.sin(angle))
        pts = curved_trigon_points(origin, angle, 0.48 * spacing, 0.16 * spacing, curve=0.08)
        add_poly_mask(frame, pts, MUTED_GOLD, 0.80 * alpha, outline_rgb=IVORY, outline_alpha=0.42 * alpha)

    if labels:
        base.draw_text(frame, "primitive only: radial sixfold circle / crescents / outward trigons", (42, 56), LABEL, scale=0.46)


def axial_primitive(frame: np.ndarray, target: TargetSpec, alpha: float, labels: bool = False) -> None:
    cx, cy = target_centroid(target)
    unit = target.source_spacing
    oval = ellipse_mask((cx, cy), (0.50 * unit, 0.32 * unit))
    blend_mask(frame, oval, IVORY, 0.86 * alpha, glow=0.018)
    outline = np.zeros_like(frame)
    cv2.ellipse(outline, (round(cx), round(cy)), (round(0.50 * unit), round(0.32 * unit)), 0, 0, 360, rgb_to_bgr(GOLD), 2, lineType=cv2.LINE_AA)
    cv2.addWeighted(outline, 0.48 * alpha, frame, 1.0, 0, dst=frame)

    arc_layer = np.zeros_like(frame)
    for side in (-1, 1):
        for band_idx, offset in enumerate((0.74, 1.12)):
            center = (round(cx + side * offset * unit), round(cy))
            axes = (round((0.36 + 0.04 * band_idx) * unit), round((0.62 + 0.06 * band_idx) * unit))
            if side < 0:
                start, end = 104, 256
            else:
                start, end = -76, 76
            cv2.ellipse(
                arc_layer,
                center,
                axes,
                0,
                start,
                end,
                rgb_to_bgr(SOFT_IVORY),
                round((0.105 - 0.018 * band_idx) * unit),
                lineType=cv2.LINE_AA,
            )
            cv2.ellipse(
                arc_layer,
                center,
                (round(axes[0] * 0.80), round(axes[1] * 0.80)),
                0,
                start,
                end,
                rgb_to_bgr(PALE_BLUE),
                max(3, round(0.015 * unit)),
                lineType=cv2.LINE_AA,
            )
        origin = (cx + side * 1.58 * unit, cy)
        pts = curved_trigon_points(origin, 0.0 if side > 0 else math.pi, 0.48 * unit, 0.20 * unit, curve=0.04)
        add_poly_mask(frame, pts, MUTED_GOLD, 0.82 * alpha, outline_rgb=IVORY, outline_alpha=0.45 * alpha)
    cv2.addWeighted(arc_layer, 0.74 * alpha, frame, 1.0, 0, dst=frame)

    if labels:
        base.draw_text(frame, "primitive only: axial oval, nested side crescents, far-side trigons", (42, 56), LABEL, scale=0.46)


def linear_path_points(target: TargetSpec) -> list[tuple[float, float]]:
    return [(source.x, source.y) for source in target.sources]


def path_tangent(points: list[tuple[float, float]], idx: int) -> float:
    if idx == 0:
        a, b = points[0], points[1]
    elif idx == len(points) - 1:
        a, b = points[-2], points[-1]
    else:
        a, b = points[idx - 1], points[idx + 1]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def linear_primitive(frame: np.ndarray, target: TargetSpec, alpha: float, labels: bool = False) -> None:
    unit = target.source_spacing
    points = linear_path_points(target)
    path_layer = np.zeros_like(frame)
    path_np = np.array(points, dtype=np.int32).reshape(-1, 1, 2)
    cv2.polylines(path_layer, [path_np], False, rgb_to_bgr(SOFT_IVORY), 2, lineType=cv2.LINE_AA)
    cv2.addWeighted(path_layer, 0.35 * alpha, frame, 1.0, 0, dst=frame)
    for idx, point in enumerate(points):
        angle = path_tangent(points, idx)
        circle_center = transform_points(point, angle, [(-0.16 * unit, 0.0)])[0]
        mask = ellipse_mask(tuple(circle_center), (0.12 * unit, 0.12 * unit))
        blend_mask(frame, mask, IVORY, 0.80 * alpha, glow=0.012)

        arc_layer = np.zeros_like(frame)
        arc_center = transform_points(point, angle, [(0.12 * unit, 0.0)])[0]
        cv2.ellipse(
            arc_layer,
            (round(arc_center[0]), round(arc_center[1])),
            (round(0.23 * unit), round(0.34 * unit)),
            math.degrees(angle),
            -68,
            68,
            rgb_to_bgr(SOFT_IVORY),
            round(0.070 * unit),
            lineType=cv2.LINE_AA,
        )
        cv2.addWeighted(arc_layer, 0.72 * alpha, frame, 1.0, 0, dst=frame)

        trigon_origin = transform_points(point, angle, [(0.42 * unit, 0.0)])[0]
        pts = curved_trigon_points(tuple(trigon_origin), angle, 0.30 * unit, 0.12 * unit, curve=0.06)
        add_poly_mask(frame, pts, MUTED_GOLD, 0.76 * alpha, outline_rgb=IVORY, outline_alpha=0.38 * alpha)

    if labels:
        base.draw_text(frame, "primitive only: repeated circle -> crescent -> trigon phrases on the source path", (42, 56), LABEL, scale=0.42)


TARGETS: tuple[TargetSpec, ...] = (
    TargetSpec(
        key="radial_sixfold_gather",
        filename="radial_sixfold_gather_v001.mp4",
        title="radial_sixfold",
        symmetry_type="C6v",
        source_spacing=250.0,
        drift_amplitude=130.0,
        wavelength=250.0,
        frequency=0.12,
        decay=1020.0,
        node_epsilon=0.058,
        threshold=0.040,
        boundary_type="sun_disk",
        reference_notes="Darren's earlier sun/ripple/snowflake experiments; seven-source seed/hex layout.",
        sources=radial_sources(),
        primitive_renderer=radial_primitive,
    ),
    TargetSpec(
        key="axial_eye_wave_gather",
        filename="axial_eye_wave_gather_v001.mp4",
        title="axial_eye",
        symmetry_type="bilateral",
        source_spacing=275.0,
        drift_amplitude=118.0,
        wavelength=275.0,
        frequency=0.10,
        decay=940.0,
        node_epsilon=0.054,
        threshold=0.038,
        boundary_type="eye_oval",
        reference_notes="Two-source axial layout based on Austin reference image notes; labeled as mathematical alignment only.",
        sources=axial_sources(),
        primitive_renderer=axial_primitive,
    ),
    TargetSpec(
        key="linear_flow_phrase_gather",
        filename="linear_flow_phrase_gather_v001.mp4",
        title="linear_flow",
        symmetry_type="translational/path",
        source_spacing=210.0,
        drift_amplitude=105.0,
        wavelength=220.0,
        frequency=0.105,
        decay=880.0,
        node_epsilon=0.050,
        threshold=0.040,
        boundary_type="river_channel",
        reference_notes="River/current/salmon-flow grammar as path-following phrases; no fish glyphs.",
        sources=linear_sources(),
        primitive_renderer=linear_primitive,
    ),
)


def target_by_key(key: str) -> TargetSpec:
    for target in TARGETS:
        if target.key == key:
            return target
    raise KeyError(key)


def boundary_mask(target: TargetSpec) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cx, cy = target_centroid(target)
    if target.boundary_type == "sun_disk":
        cv2.ellipse(mask, (round(cx), round(cy)), (570, 470), 0, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    elif target.boundary_type == "eye_oval":
        cv2.ellipse(mask, (round(cx), round(cy)), (720, 330), 0, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    elif target.boundary_type == "river_channel":
        points = np.array(linear_path_points(target), dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(mask, [points], False, 255, 330, lineType=cv2.LINE_AA)
        for point in linear_path_points(target):
            cv2.circle(mask, (round(point[0]), round(point[1])), 165, 255, -1, lineType=cv2.LINE_AA)
    else:
        mask[:, :] = 255
    mask = cv2.GaussianBlur(mask, (0, 0), 0.65)
    return np.where(mask > 16, 255, 0).astype(np.uint8)


BOUNDARY_CACHE = {target.key: boundary_mask(target) for target in TARGETS}
BOUNDARY_SMALL_CACHE = {
    key: np.where(cv2.resize(mask, (FW, FH), interpolation=cv2.INTER_AREA) > 24, 255, 0).astype(np.uint8)
    for key, mask in BOUNDARY_CACHE.items()
}


def draw_boundary_outline(frame: np.ndarray, target: TargetSpec, *, alpha: float = 0.52) -> None:
    mask = BOUNDARY_CACHE[target.key]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    overlay = np.zeros_like(frame)
    cv2.drawContours(overlay, contours, -1, rgb_to_bgr(IVORY), 2, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def render_wave_layer(
    field_norm: np.ndarray,
    target: TargetSpec,
    *,
    labels: bool = False,
) -> np.ndarray:
    frame_small = np.zeros((FH, FW, 3), dtype=np.uint8)
    field_small = cv2.GaussianBlur(field_norm, (0, 0), 0.42)
    mask = BOUNDARY_SMALL_CACHE[target.key]
    inside = mask > 0
    base_mask = mask.copy()
    threshold = target.threshold
    pos_mask = np.where((field_small > threshold) & inside, 255, 0).astype(np.uint8)
    neg_mask = np.where((field_small < -threshold) & inside, 255, 0).astype(np.uint8)
    node_mask = np.where((np.abs(field_small) <= target.node_epsilon) & inside, 255, 0).astype(np.uint8)
    node_mask = cv2.morphologyEx(node_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    blend_mask(frame_small, base_mask, DARK_TEAL, 0.96)
    blend_mask(frame_small, neg_mask, TEAL, 0.88)
    blend_mask(frame_small, pos_mask, CREAM, 0.96)

    blend_mask(frame_small, node_mask, INK, 0.50)
    node_edge = cv2.morphologyEx(node_mask, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    blend_mask(frame_small, node_edge, SOFT_IVORY, 0.10)
    frame = cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)
    draw_boundary_outline(frame, target, alpha=0.42)
    if labels:
        base.draw_text(frame, "wave only: two-tone scalar regions plus carved nodal/interstitial linework", (42, 56), LABEL, scale=0.46)
    return frame


def render_primitive_layer(target: TargetSpec, *, alpha: float = 1.0, labels: bool = False) -> np.ndarray:
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    blend_mask(frame, BOUNDARY_CACHE[target.key], DEEP_TEAL, 0.28)
    target.primitive_renderer(frame, target, alpha, labels)
    draw_boundary_outline(frame, target, alpha=0.22 * alpha)
    return frame


def render_combined_frame(target: TargetSpec, time_seconds: float, *, force_coherence: float | None = None) -> tuple[np.ndarray, dict[str, object]]:
    coherence = coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = target_sources_at(target, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=0.72)
    frame = render_wave_layer(field, target)
    primitive_alpha = primitive_alpha_for_coherence(coherence)
    target.primitive_renderer(frame, target, primitive_alpha)
    return frame, {
        "coherence": round(coherence, 4),
        "primitive_alpha": round(primitive_alpha, 4),
        "source_positions": [
            {
                "source_id": source.source_id,
                "x": round(source.x, 3),
                "y": round(source.y, 3),
                "wavelength": round(source.wavelength, 3),
                "phase": round(source.phase, 4),
            }
            for source in sources
        ],
    }


def render_three_views(target: TargetSpec) -> np.ndarray:
    time_seconds = 6.0
    sources = target_sources_at(target, time_seconds, 1.0)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=0.72)
    wave = render_wave_layer(field, target, labels=True)
    primitive = render_primitive_layer(target, alpha=1.0, labels=True)
    combined = wave.copy()
    target.primitive_renderer(combined, target, 1.0)
    base.draw_text(combined, "combined at c=1: primitive composition annotates same wave layout", (42, 56), LABEL, scale=0.46)
    panels = [
        cv2.resize(wave, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(primitive, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(combined, (640, 360), interpolation=cv2.INTER_AREA),
    ]
    return cv2.hconcat(panels)


def draw_source_position_panel(target: TargetSpec, coherence: float, time_seconds: float) -> np.ndarray:
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    blend_mask(frame, BOUNDARY_CACHE[target.key], DEEP_TEAL, 0.40)
    draw_boundary_outline(frame, target, alpha=0.34)
    target.primitive_renderer(frame, target, 0.14 if coherence >= 0.99 else 0.05)
    current = target_sources_at(target, time_seconds, coherence)
    overlay = np.zeros_like(frame)
    for fixed in target.sources:
        cv2.circle(overlay, (round(fixed.x), round(fixed.y)), 7, rgb_to_bgr(MUTED_GOLD), 1, lineType=cv2.LINE_AA)
    for source in current:
        cv2.circle(overlay, (round(source.x), round(source.y)), 11, rgb_to_bgr(GOLD), 2, lineType=cv2.LINE_AA)
        cv2.circle(overlay, (round(source.x), round(source.y)), 2, rgb_to_bgr(IVORY), -1, lineType=cv2.LINE_AA)
        base.draw_text(overlay, source.source_id, (round(source.x) + 12, round(source.y) - 10), LABEL, scale=0.30)
    cv2.addWeighted(overlay, 0.90, frame, 1.0, 0, dst=frame)
    base.draw_text(frame, f"{target.title}  c={coherence:.1f}", (42, 56), LABEL, scale=0.58)
    base.draw_text(frame, "gold=current source positions; muted rings=target locks", (42, 86), LABEL, scale=0.36)
    return cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)


def make_debug_sheet() -> Path:
    rows = []
    for target in TARGETS:
        panels = [
            draw_source_position_panel(target, 0.0, 1.5),
            draw_source_position_panel(target, 0.5, 4.0),
            draw_source_position_panel(target, 1.0, 6.0),
        ]
        rows.append(cv2.hconcat(panels))
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "integrated_choreographer_v001_debug_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_contact_sheet() -> Path:
    rows = []
    for target in TARGETS:
        mid = cv2.imread(str(MIDPOINT_DIR / f"{target.key}_v001_midpoint.png"), cv2.IMREAD_COLOR)
        peak = cv2.imread(str(PEAK_DIR / f"{target.key}_v001_peak.png"), cv2.IMREAD_COLOR)
        if mid is None or peak is None:
            continue
        left = cv2.resize(mid, (960, 540), interpolation=cv2.INTER_AREA)
        right = cv2.resize(peak, (960, 540), interpolation=cv2.INTER_AREA)
        base.draw_text(left, f"{target.title} midpoint c=1", (34, 48), LABEL, scale=0.55)
        base.draw_text(right, f"{target.title} peak c=1", (34, 48), LABEL, scale=0.55)
        rows.append(cv2.hconcat([left, right]))
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "integrated_choreographer_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip(target: TargetSpec) -> dict[str, object]:
    output_path = OUT_DIR / target.filename
    writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
    midpoint_frame: np.ndarray | None = None
    peak_frame: np.ndarray | None = None
    coherence_samples: dict[str, object] = {}
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = frame_idx / FPS
            frame, info = render_combined_frame(target, time_seconds)
            writer.write(frame)
            if frame_idx == MIDPOINT_FRAME:
                midpoint_frame = frame.copy()
                coherence_samples["midpoint"] = info
            if frame_idx == PEAK_FRAME:
                peak_frame = frame.copy()
                coherence_samples["peak"] = info
    finally:
        writer.close()

    if midpoint_frame is None:
        midpoint_frame, _ = render_combined_frame(target, MIDPOINT_FRAME / FPS)
    if peak_frame is None:
        peak_frame, _ = render_combined_frame(target, PEAK_FRAME / FPS)

    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    midpoint_path = MIDPOINT_DIR / f"{target.key}_v001_midpoint.png"
    peak_path = PEAK_DIR / f"{target.key}_v001_peak.png"
    cv2.imwrite(str(midpoint_path), midpoint_frame)
    cv2.imwrite(str(peak_path), peak_frame)

    three_views = render_three_views(target)
    three_views_path = DEBUG_DIR / f"{target.key}_v001_three_views_comparison.png"
    cv2.imwrite(str(three_views_path), three_views)

    return {
        "key": target.key,
        "filename": target.filename,
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "midpoint_still": str(midpoint_path.relative_to(OUT_DIR)),
        "peak_still": str(peak_path.relative_to(OUT_DIR)),
        "three_views_comparison": str(three_views_path.relative_to(OUT_DIR)),
        "source_count": len(target.sources),
        "symmetry_type": target.symmetry_type,
        "source_spacing": target.source_spacing,
        "wavelength": target.wavelength,
        "coherence_samples": coherence_samples,
    }


def target_to_manifest(target: TargetSpec) -> dict[str, object]:
    return {
        "key": target.key,
        "title": target.title,
        "filename": target.filename,
        "symmetry_type": target.symmetry_type,
        "source_spacing": target.source_spacing,
        "wavelength": target.wavelength,
        "frequency": target.frequency,
        "decay": target.decay,
        "boundary_type": target.boundary_type,
        "reference_notes": target.reference_notes,
        "target_sources": [
            {
                "source_id": source.source_id,
                "target_position": [round(source.x, 3), round(source.y, 3)],
                "amplitude": source.amplitude,
                "drift_scale": source.drift_scale,
                "orbit_phase": source.orbit_phase,
                "orbit_speed": source.orbit_speed,
                "phase_perturb": source.phase_perturb,
            }
            for source in target.sources
        ],
        "primitive_composition": primitive_description(target),
    }


def primitive_description(target: TargetSpec) -> dict[str, object]:
    if target.key == "radial_sixfold_gather":
        return {
            "center": "filled circle radius approx 0.3 * source_spacing",
            "crescents": "six ripple/crescent bands at radius approx 1.0 * source_spacing",
            "trigons": "six outward ray/trigon regions at radius approx 1.6 * source_spacing, offset 30 degrees",
        }
    if target.key == "axial_eye_wave_gather":
        return {
            "center": "filled horizontal oval/circle, about 1.5:1 aspect ratio",
            "crescents": "two nested side crescents on each side, curving away from center",
            "trigons": "one sharp outward trigon at each far side",
        }
    return {
        "phrases": "five repeated circle -> crescent -> trigon phrases along local path tangent",
        "path": "horizontal/gentle S-curve source path",
    }


def write_manifest(summaries: list[dict[str, object]], contact_sheet: Path, debug_sheet: Path) -> Path:
    manifest = {
        "project": "integrated_choreographer_v001",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "renderer": "scripts/integrated_choreographer_v001.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "coherence_curve": {
            "parameter": "c",
            "range": [0.0, 1.0],
            "curve": "smoothstep gather/release",
            "timing_seconds": {
                "0.0-3.0": "loose drifting wave field, c=0",
                "3.0-5.0": "smoothstep gather to target, c 0->1",
                "5.0-8.0": "target lock hold, c=1, primitive composition readable",
                "8.0-10.0": "smoothstep release, c 1->0",
                "10.0-12.0": "drift continues, c=0",
            },
            "drift_behavior": "source orbits target with radius drift_amplitude * (1 - c^2), per-source angular velocity and phase perturbation",
            "primitive_visibility": "primitive layer fades in only when c > 0.7",
        },
        "target_library": [target_to_manifest(target) for target in TARGETS],
        "clips": summaries,
        "deliverables": {
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_sheet.relative_to(OUT_DIR)),
            "midpoint_stills": sorted(path.name for path in MIDPOINT_DIR.glob("*.png")),
            "peak_stills": sorted(path.name for path in PEAK_DIR.glob("*.png")),
            "three_views_comparisons": sorted(path.name for path in DEBUG_DIR.glob("*three_views_comparison.png")),
        },
    }
    path = OUT_DIR / "integrated_choreographer_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    lines = [
        "# Integrated Choreographer v001",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet builds one integrated engine that breathes between loose wave-field motion and clear primitive-composition moments. The source positions themselves gather into coherent target layouts; the primitive composition fades in only when the scalar-wave source layout matches that composition.",
        "",
        "Core design philosophy: the field does not create the exact art. The field gathers into a geometry where the primitive composition becomes the obvious readable view of that same geometry.",
        "",
        "## Architecture",
        "",
        "- Target library: each target stores source positions, a matching primitive composition template, symmetry type, and reference notes.",
        "- Choreographer: coherence `c` controls orbital source drift. At `c=0`, sources orbit around target positions. At `c=1`, sources lock exactly to the current target configuration.",
        "- Wave renderer: full-field two-tone scalar regions with visible nodal/interstitial linework, inherited from the v005-v007 direction.",
        "- Primitive renderer: clean circle/crescent/trigon compositions aligned to the same target center, scale, and symmetry axis, fading in only when `c > 0.7`.",
        "",
        "## Timing",
        "",
        "- 0.0-3.0s: loose drifting wave field",
        "- 3.0-5.0s: smoothstep gather toward target",
        "- 5.0-8.0s: `c=1` hold with primitive composition readable",
        "- 8.0-10.0s: smoothstep release back to drift",
        "- 10.0-12.0s: drift continues",
        "",
        "## Clips",
        "",
    ]
    for summary in summaries:
        target = target_by_key(str(summary["key"]))
        lines.extend(
            [
                f"- `{target.filename}`: target `{target.title}`, symmetry `{target.symmetry_type}`, {len(target.sources)} sources. {target.reference_notes}",
            ]
        )
    lines.extend(
        [
            "",
            "## Deliverables",
            "",
            "- 3 MP4 clips, 1920x1080, 24 fps, 12 seconds.",
            "- Midpoint stills in `midpoint_stills/`.",
            "- Peak stills in `peak_stills/`.",
            "- Contact sheet: `integrated_choreographer_v001_contact_sheet.png`.",
            "- Debug sheet: `integrated_choreographer_v001_debug_sheet.png` showing `c=0`, `c=0.5`, and `c=1` source positions for each target.",
            "- Three-views comparison stills in `debug_stills/`: wave only / primitive only / combined at `c=1`.",
            "- Manifest: `integrated_choreographer_v001_manifest.json`.",
            "",
            "## Honest Verdict",
            "",
            "v001 is intentionally an integrated choreographer rather than a sparse feature extractor. The wave layer remains a two-tone scalar-field composition for the full clip, while the primitive layer appears only during source coherence. The radial sixfold target is the strongest alignment test because the wave source lattice, visual center, crescent bands, and six outward trigons all share the same center and scale. The axial target is an honest two-source bilateral construction; it should read as an eye-like mathematical alignment family, not as a cultural reconstruction. The linear flow target is the most compositional of the three because the repeated phrase layer is path-oriented; it is included to test whether source-path gathering can carry a readable current/flow phrase without fish glyphs or literal iconography.",
            "",
            "The remaining risk is that the primitive layer is still an annotation layer. The intended success condition is that hiding it at `c=1` leaves wave features in the same locations, so the composition reads as a clarified view of the gathered field rather than a separate Resolume-style layer mix.",
            "",
            "## Cultural Boundary",
            "",
            "This is an internal mathematical visual study only. It does not claim to reconstruct Coast Salish design, validate a cultural grammar, or carry cultural meaning. Austin review is required to determine which renderings resonate and which read as off.",
            "",
            "Renderer: `scripts/integrated_choreographer_v001.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render integrated choreographer v001 packet.")
    parser.add_argument(
        "--clip",
        choices=["all", *[target.key for target in TARGETS]],
        default="all",
        help="Render one clip for iteration, or all clips for the final packet.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    selected = list(TARGETS if args.clip == "all" else [target_by_key(args.clip)])
    summaries: list[dict[str, object]] = []
    for target in selected:
        print(f"Rendering {target.filename}", flush=True)
        summaries.append(render_clip(target))

    if args.clip == "all":
        contact_sheet = make_contact_sheet()
        debug_sheet = make_debug_sheet()
        manifest = write_manifest(summaries, contact_sheet, debug_sheet)
        readme = write_readme(summaries)
        print(f"Wrote {contact_sheet}", flush=True)
        print(f"Wrote {debug_sheet}", flush=True)
        print(f"Wrote {manifest}", flush=True)
        print(f"Wrote {readme}", flush=True)
    else:
        print(f"Rendered {selected[0].filename}", flush=True)


if __name__ == "__main__":
    main()
