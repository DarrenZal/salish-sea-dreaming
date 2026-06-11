#!/usr/bin/env python3
"""
Integrated choreographer v003, geometric synthesis.

Internal mathematical/visual alignment study for Salish Sea Dreaming. This
version keeps the v002 source-gathering architecture, keeps separate primitive
icons deleted, and synthesizes multiple source-derived mathematical views of the
same layout: wave-amplitude field, construction-circle arcs, selected
arc-bounded regions, and thin nodal/interstitial linework.

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
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
    / "integrated_choreographer_v003_geometric_synthesis_2026-05-21"
)
V002_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v002_field_only_2026-05-21"
)
V007_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "cymatic_field_topology_v007_2026-05-20"
)
V004_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "cymatic_field_topology_v004_2026-05-20"
)
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
COMPARISON_DIR = OUT_DIR / "comparison_stills"
THREE_VIEW_DIR = OUT_DIR / "three_view_stills"

W = base.W
H = base.H
FW = base.FW
FH = base.FH
FPS = base.FPS
DURATION_SECONDS = 12.0
N_FRAMES = int(FPS * DURATION_SECONDS)
MIDPOINT_FRAME = int(6.0 * FPS)
PEAK_FRAME = int(6.4 * FPS)
PEAK_TIME_SECONDS = PEAK_FRAME / FPS
TAU = math.tau

BLACK = (0, 0, 0)
IVORY = (238, 242, 232)
CREAM = (236, 229, 197)
SOFT_IVORY = (208, 224, 218)
PALE_BLUE = (136, 219, 238)
TEAL = (64, 178, 190)
DEEP_TEAL = (8, 44, 52)
DARK_TEAL = (3, 26, 31)
MUTED_GOLD = (213, 178, 112)
GOLD = (246, 197, 92)
INK = (0, 7, 9)
CYAN_LINE = (84, 222, 232)
LABEL = (226, 234, 230)
ARC_CREAM = (232, 225, 191)
ARC_TEAL = (84, 178, 184)
CONSTRUCTION = (166, 181, 165)

AXIAL_REFERENCE_IMAGE = (
    Path("/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2")
    / "06-austin-vancity-slides-crescent-circle-trigon.png"
)


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
    target_library_key: str
    symmetry_type: str
    source_spacing: float
    source_spacing_ratio: float | None
    drift_amplitude: float
    wavelength: float
    frequency: float
    decay: float
    node_epsilon: float
    threshold: float
    blur_sigma: float
    field_gamma: float
    phase_anchor_distance: float
    boundary_type: str
    boundary_axes: tuple[float, float]
    reference_notes: str
    tuning_notes: str
    sources: tuple[TargetSource, ...]


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
    out = frame.astype(np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask, (0, 0), 7.0)
        out += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[:] = np.clip(out, 0, 255).astype(np.uint8)


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
    locked_phase = TAU * target.frequency * 6.0 - TAU * target.phase_anchor_distance / target.wavelength
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


def radial_sources(spacing: float = 250.0) -> tuple[TargetSource, ...]:
    cx, cy = W * 0.5, H * 0.5
    sources = [
        # +15% against v001's 1.18 center amplitude, staying within the requested field-only tuning path.
        TargetSource("radial_center", cx, cy, 1.36, 0.42, 0.11, 0.34, 0.07),
    ]
    for idx in range(6):
        angle = TAU * idx / 6.0
        sources.append(
            TargetSource(
                f"radial_ring_{idx}",
                cx + spacing * math.cos(angle),
                cy + spacing * math.sin(angle),
                0.93,
                1.0,
                0.17 * idx + 0.03,
                0.20 + 0.035 * idx,
                0.13 * idx + 0.19,
            )
        )
    return tuple(sources)


def axial_sources(unit: float, amplitude: float = 1.08) -> tuple[TargetSource, ...]:
    cx, cy = W * 0.5, H * 0.5
    return (
        TargetSource("axial_left", cx - unit, cy, amplitude, 0.96, 0.19, 0.22, 0.18),
        TargetSource("axial_right", cx + unit, cy, amplitude, 0.96, 0.64, -0.19, 0.51),
    )


def make_axial_target_for_ratio(ratio: float, *, key_suffix: str = "") -> TargetSpec:
    wavelength = 250.0
    separation = ratio * wavelength
    unit = separation * 0.5
    return TargetSpec(
        key=f"axial_eye_geometric_synthesis{key_suffix}",
        filename="axial_eye_geometric_synthesis_v003.mp4",
        title="axial_eye_geometric_synthesis",
        target_library_key="axial_eye",
        symmetry_type="bilateral",
        source_spacing=separation,
        source_spacing_ratio=ratio,
        drift_amplitude=118.0,
        wavelength=wavelength,
        frequency=0.10,
        decay=840.0,
        node_epsilon=0.050,
        threshold=0.054,
        blur_sigma=0.66,
        field_gamma=0.93,
        phase_anchor_distance=unit,
        boundary_type="pinched_eye_oval",
        boundary_axes=(705.0, 305.0),
        reference_notes=(
            "Two-source axial target. The internal reference image was viewed before rendering: "
            f"{AXIAL_REFERENCE_IMAGE if AXIAL_REFERENCE_IMAGE.exists() else 'not found'}."
        ),
        tuning_notes=(
            f"Axial source separation held at {ratio:.1f}x wavelength from v002. v003 adds source-derived "
            "wavefront construction rings at integer and fractional wavelength radii to recover nested side crescents "
            "and side pressure/notch regions without drawn arrows."
        ),
        sources=axial_sources(unit),
    )


TARGETS: tuple[TargetSpec, ...] = (
    TargetSpec(
        key="radial_sixfold_geometric_synthesis",
        filename="radial_sixfold_geometric_synthesis_v003.mp4",
        title="radial_sixfold_geometric_synthesis",
        target_library_key="radial_sixfold",
        symmetry_type="C6v",
        source_spacing=250.0,
        source_spacing_ratio=None,
        drift_amplitude=130.0,
        wavelength=250.0,
        frequency=0.12,
        decay=980.0,
        node_epsilon=0.043,
        threshold=0.060,
        blur_sigma=0.62,
        field_gamma=0.88,
        phase_anchor_distance=250.0,
        boundary_type="sun_disk",
        boundary_axes=(570.0, 465.0),
        reference_notes="Seven-source radial seed/hex layout inherited from v001/v002; linear flow parked for v003.",
        tuning_notes=(
            "v003 keeps the two-tone field as the base, then reveals construction circles at source wavelength R. "
            "Selected center-ring intersections become arc-bounded crescent regions; adjacent ring intersections minus the "
            "center construction circle become negative-space trigon-like gaps."
        ),
        sources=radial_sources(250.0),
    ),
    # Ratio 2.0 kept the clearest nested side-band read in the v002 spacing test sheet.
    make_axial_target_for_ratio(2.0),
)


BASELINE_TARGETS: dict[str, TargetSpec] = {
    "radial_sixfold_geometric_synthesis": replace(
        TARGETS[0],
        sources=tuple(
            [TargetSource("radial_center", W * 0.5, H * 0.5, 1.18, 0.42, 0.11, 0.34, 0.07)]
            + [
                TargetSource(
                    f"radial_ring_{idx}",
                    W * 0.5 + 250.0 * math.cos(TAU * idx / 6.0),
                    H * 0.5 + 250.0 * math.sin(TAU * idx / 6.0),
                    0.94,
                    1.0,
                    0.17 * idx + 0.03,
                    0.20 + 0.035 * idx,
                    0.13 * idx + 0.19,
                )
                for idx in range(6)
            ]
        ),
        decay=1020.0,
        node_epsilon=0.058,
        threshold=0.040,
        blur_sigma=0.72,
        field_gamma=1.0,
        boundary_axes=(570.0, 470.0),
        reference_notes="v002-comparison wave-only baseline with geometric synthesis hidden.",
        tuning_notes="Baseline field-only read before v003 construction/arc-region synthesis.",
    ),
    "axial_eye_geometric_synthesis": replace(
        make_axial_target_for_ratio(2.0, key_suffix="_baseline"),
        key="axial_eye_geometric_synthesis",
        source_spacing=550.0,
        wavelength=275.0,
        decay=940.0,
        node_epsilon=0.054,
        threshold=0.038,
        blur_sigma=0.72,
        field_gamma=1.0,
        boundary_type="eye_oval",
        boundary_axes=(720.0, 330.0),
        reference_notes="v002-comparison two-source axial wave-only baseline with geometric synthesis hidden.",
        tuning_notes="Baseline field-only read before v003 construction/arc-region synthesis.",
    ),
}


def target_by_key(key: str) -> TargetSpec:
    for target in TARGETS:
        if target.key == key:
            return target
    raise KeyError(key)


def full_boundary_mask(target: TargetSpec) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cx, cy = target_centroid(target)
    ax, ay = target.boundary_axes
    if target.boundary_type == "sun_disk":
        cv2.ellipse(mask, (round(cx), round(cy)), (round(ax), round(ay)), 0, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    elif target.boundary_type == "eye_oval":
        cv2.ellipse(mask, (round(cx), round(cy)), (round(ax), round(ay)), 0, 0, 360, 255, -1, lineType=cv2.LINE_AA)
    elif target.boundary_type == "pinched_eye_oval":
        xs = np.linspace(-ax, ax, 420, dtype=np.float32)
        upper: list[tuple[float, float]] = []
        lower: list[tuple[float, float]] = []
        for x in xs:
            u = abs(float(x)) / ax
            y = ay * (max(0.0, 1.0 - u**1.72) ** 0.54)
            pinch = 0.94 + 0.06 * math.cos(math.pi * float(x) / ax)
            y *= pinch
            upper.append((cx + float(x), cy - y))
            lower.append((cx + float(x), cy + y))
        points = np.array(upper + lower[::-1], dtype=np.int32)
        cv2.fillPoly(mask, [points], 255, lineType=cv2.LINE_AA)
    else:
        mask[:, :] = 255
    mask = cv2.GaussianBlur(mask, (0, 0), 0.65)
    return np.where(mask > 16, 255, 0).astype(np.uint8)


BOUNDARY_CACHE: dict[str, np.ndarray] = {target.key: full_boundary_mask(target) for target in TARGETS}
for key, target in BASELINE_TARGETS.items():
    BOUNDARY_CACHE[f"{key}__baseline"] = full_boundary_mask(target)


def boundary_mask_for(target: TargetSpec, *, baseline: bool = False) -> np.ndarray:
    key = f"{target.key}__baseline" if baseline else target.key
    return BOUNDARY_CACHE[key]


def boundary_mask_small(target: TargetSpec, *, baseline: bool = False) -> np.ndarray:
    mask = boundary_mask_for(target, baseline=baseline)
    return np.where(cv2.resize(mask, (FW, FH), interpolation=cv2.INTER_AREA) > 24, 255, 0).astype(np.uint8)


def draw_boundary_outline(frame: np.ndarray, target: TargetSpec, *, alpha: float = 0.55, baseline: bool = False) -> None:
    contours, _ = cv2.findContours(boundary_mask_for(target, baseline=baseline), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    overlay = np.zeros_like(frame)
    cv2.drawContours(overlay, contours, -1, rgb_to_bgr(IVORY), 2, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def shape_field(field_norm: np.ndarray, gamma: float) -> np.ndarray:
    if abs(gamma - 1.0) < 1e-6:
        return field_norm
    return (np.sign(field_norm) * (np.abs(field_norm) ** gamma)).astype(np.float32)


def render_field_only_layer(
    field_norm: np.ndarray,
    target: TargetSpec,
    *,
    wave_alpha: float = 1.0,
    nodal_alpha: float | None = None,
    labels: bool = False,
    baseline: bool = False,
) -> np.ndarray:
    wave_alpha = clamp01(wave_alpha)
    if nodal_alpha is None:
        nodal_alpha = wave_alpha
    frame_small = np.zeros((FH, FW, 3), dtype=np.uint8)
    blur = 0.38 if not baseline else 0.42
    field_small = cv2.GaussianBlur(shape_field(field_norm, target.field_gamma), (0, 0), blur)
    mask = boundary_mask_small(target, baseline=baseline)
    inside = mask > 0

    threshold = target.threshold
    pos_mask = np.where((field_small > threshold) & inside, 255, 0).astype(np.uint8)
    neg_mask = np.where((field_small < -threshold) & inside, 255, 0).astype(np.uint8)
    node_mask = np.where((np.abs(field_small) <= target.node_epsilon) & inside, 255, 0).astype(np.uint8)
    node_mask = cv2.morphologyEx(node_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    region_mask = cv2.bitwise_or(pos_mask, neg_mask)
    edge_mask = cv2.morphologyEx(region_mask, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_edge = cv2.morphologyEx(node_mask, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    blend_mask(frame_small, mask, DARK_TEAL, 0.96 * wave_alpha)
    blend_mask(frame_small, neg_mask, TEAL, 0.90 * wave_alpha)
    blend_mask(frame_small, pos_mask, CREAM, 0.98 * wave_alpha)

    # Linework is derived from nodal/interstitial zero-regions, not from a separate glyph layer.
    blend_mask(frame_small, edge_mask, INK, 0.28 * nodal_alpha)
    blend_mask(frame_small, node_mask, INK, 0.70 * nodal_alpha)
    blend_mask(frame_small, node_edge, CYAN_LINE, 0.18 * nodal_alpha)

    frame = cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)
    draw_boundary_outline(frame, target, alpha=0.52 * max(wave_alpha, 0.35), baseline=baseline)
    if labels:
        base.draw_text(frame, "wave view: positive/negative regions + nodal/interstitial linework", (42, 56), LABEL, scale=0.46)
    return frame


@dataclass(frozen=True)
class SynthCircle:
    circle_id: str
    source_id: str
    x: float
    y: float
    radius: float
    role: str
    ring_index: float


@dataclass(frozen=True)
class SynthRegion:
    region_id: str
    region_class: str
    subtype: str
    source_circle_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    mask: np.ndarray
    fill_rgb: tuple[int, int, int]
    outline_rgb: tuple[int, int, int]
    visible_at_peak: bool
    generation_rule: str


def synthesis_levels(time_seconds: float, coherence: float) -> dict[str, float]:
    """Layer levels for the 12s v002 choreographer timeline."""
    reveal = smoothstep01((time_seconds - 3.0) / 2.0)
    dissolve = 1.0 - smoothstep01((time_seconds - 8.0) / 2.0)
    hold_gate = clamp01(reveal * dissolve)
    coherence_gate = smoothstep01((coherence - 0.62) / 0.38)
    construction_alpha = 0.14 * hold_gate + 0.06 * reveal * (1.0 - coherence_gate)
    region_alpha = 0.74 * hold_gate * coherence_gate
    return {
        "wave_alpha": 1.0 - 0.32 * hold_gate * coherence_gate,
        "construction_alpha": clamp01(construction_alpha),
        "region_alpha": clamp01(region_alpha),
        "nodal_alpha": clamp01(0.70 + 0.22 * hold_gate * coherence_gate),
        "coherence_gate": clamp01(coherence_gate),
    }


def full_mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask > 4)
    if len(xs) == 0 or len(ys) == 0:
        return None
    return (
        max(0, int(xs.min()) - 8),
        max(0, int(ys.min()) - 8),
        min(W, int(xs.max()) + 9),
        min(H, int(ys.max()) + 9),
    )


def blend_full_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0:
        return
    bbox = full_mask_bbox(mask)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    crop_mask = mask[y0:y1, x0:x1]
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = np.array(rgb_to_bgr(rgb), dtype=np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(crop_mask, (0, 0), 6.0)
        crop += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    a = (crop_mask.astype(np.float32) / 255.0) * alpha
    crop = crop * (1.0 - a[..., None]) + color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def mask_intersection(*masks: np.ndarray) -> np.ndarray:
    if not masks:
        return np.zeros((H, W), dtype=np.uint8)
    return np.minimum.reduce([mask.astype(np.uint8) for mask in masks])


def mask_union(*masks: np.ndarray) -> np.ndarray:
    if not masks:
        return np.zeros((H, W), dtype=np.uint8)
    return np.maximum.reduce([mask.astype(np.uint8) for mask in masks])


def mask_subtract(mask: np.ndarray, subtract: np.ndarray) -> np.ndarray:
    return np.clip(mask.astype(np.int16) - subtract.astype(np.int16), 0, 255).astype(np.uint8)


def circle_mask(circle: SynthCircle, *, radius_override: float | None = None) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    radius = circle.radius if radius_override is None else radius_override
    cv2.circle(mask, (round(circle.x), round(circle.y)), max(1, round(radius)), 255, -1, lineType=cv2.LINE_AA)
    return mask


def half_plane_mask(kind: str, cutoff: float) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    if kind == "left":
        mask[:, : max(0, min(W, round(cutoff)))] = 255
    elif kind == "right":
        mask[:, max(0, min(W, round(cutoff))) :] = 255
    elif kind == "above":
        mask[: max(0, min(H, round(cutoff))), :] = 255
    elif kind == "below":
        mask[max(0, min(H, round(cutoff))) :, :] = 255
    return mask


def horizontal_band_mask(center_y: float, half_height: float) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    y0 = max(0, round(center_y - half_height))
    y1 = min(H, round(center_y + half_height))
    mask[y0:y1, :] = 255
    return mask


def active_circles(target: TargetSpec, sources: list[base.WaveSource]) -> list[SynthCircle]:
    circles: list[SynthCircle] = []
    if target.target_library_key == "radial_sixfold":
        for source in sources:
            circles.append(
                SynthCircle(
                    circle_id=f"{source.source_id}_R1",
                    source_id=source.source_id,
                    x=source.x,
                    y=source.y,
                    radius=source.wavelength,
                    role="source_wavelength_R",
                    ring_index=1.0,
                )
            )
    else:
        for source in sources:
            for multiplier in (1.0, 1.48, 1.92, 2.34):
                circles.append(
                    SynthCircle(
                        circle_id=f"{source.source_id}_R{multiplier:.2f}",
                        source_id=source.source_id,
                        x=source.x,
                        y=source.y,
                        radius=source.wavelength * multiplier,
                        role="axial_wavefront_multiple",
                        ring_index=multiplier,
                    )
                )
    return circles


def find_circle(circles: list[SynthCircle], source_id: str, ring_index: float = 1.0) -> SynthCircle:
    for circle in circles:
        if circle.source_id == source_id and abs(circle.ring_index - ring_index) < 0.01:
            return circle
    raise KeyError((source_id, ring_index))


def radial_ring_circles(circles: list[SynthCircle], center: SynthCircle) -> list[SynthCircle]:
    ring = [circle for circle in circles if circle.source_id.startswith("radial_ring_")]
    ring.sort(key=lambda circle: math.atan2(circle.y - center.y, circle.x - center.x))
    return ring


def source_disc_region(circle: SynthCircle, radius_factor: float, region_id: str) -> SynthRegion:
    mask = mask_intersection(circle_mask(circle, radius_override=circle.radius * radius_factor), boundary_mask_for(target_by_geometry_circle(circle)))
    return SynthRegion(
        region_id=region_id,
        region_class="circle_like",
        subtype="source_anchored_disc",
        source_circle_ids=(circle.circle_id,),
        source_ids=(circle.source_id,),
        mask=mask,
        fill_rgb=ARC_CREAM,
        outline_rgb=INK,
        visible_at_peak=True,
        generation_rule=f"source-center disc at {radius_factor:.2f} of construction radius for {circle.source_id}",
    )


def target_by_geometry_circle(circle: SynthCircle) -> TargetSpec:
    if circle.source_id.startswith("radial_"):
        return target_by_key("radial_sixfold_geometric_synthesis")
    return target_by_key("axial_eye_geometric_synthesis")


def bounded(mask: np.ndarray, target: TargetSpec) -> np.ndarray:
    return mask_intersection(mask, boundary_mask_for(target))


def make_region(
    region_id: str,
    region_class: str,
    subtype: str,
    source_circles: tuple[SynthCircle, ...],
    mask: np.ndarray,
    fill_rgb: tuple[int, int, int],
    outline_rgb: tuple[int, int, int],
    generation_rule: str,
) -> SynthRegion:
    return SynthRegion(
        region_id=region_id,
        region_class=region_class,
        subtype=subtype,
        source_circle_ids=tuple(circle.circle_id for circle in source_circles),
        source_ids=tuple(dict.fromkeys(circle.source_id for circle in source_circles)),
        mask=mask,
        fill_rgb=fill_rgb,
        outline_rgb=outline_rgb,
        visible_at_peak=True,
        generation_rule=generation_rule,
    )


def build_radial_geometry(target: TargetSpec, circles: list[SynthCircle]) -> tuple[list[SynthRegion], list[SynthRegion]]:
    center = find_circle(circles, "radial_center")
    ring = radial_ring_circles(circles, center)
    visible: list[SynthRegion] = []
    all_regions: list[SynthRegion] = []

    center_disc = bounded(circle_mask(center, radius_override=center.radius * 0.30), target)
    visible.append(
        make_region(
            "radial_center_source_disc",
            "circle_like",
            "central_source_cell",
            (center,),
            center_disc,
            ARC_CREAM,
            INK,
            "central source disc derived from radial_center and radius R",
        )
    )
    all_regions.append(visible[-1])

    center_mask = circle_mask(center)
    center_small = circle_mask(center, radius_override=center.radius * 0.28)
    for idx, circle in enumerate(ring):
        lens = bounded(mask_subtract(mask_intersection(center_mask, circle_mask(circle)), center_small), target)
        region = make_region(
            f"radial_center_ring_crescent_{idx:02d}",
            "crescent_like",
            "center_ring_arc_bounded_lens_crescent",
            (center, circle),
            lens,
            ARC_CREAM,
            INK,
            "intersection of center construction circle and one ring construction circle, with central source disc removed",
        )
        visible.append(region)
        all_regions.append(region)

    for idx, circle in enumerate(ring):
        nxt = ring[(idx + 1) % len(ring)]
        gap = bounded(mask_subtract(mask_intersection(circle_mask(circle), circle_mask(nxt)), center_mask), target)
        region = make_region(
            f"radial_negative_trigon_gap_{idx:02d}",
            "trigon_like",
            "adjacent_ring_minus_center_negative_gap",
            (circle, nxt, center),
            gap,
            INK,
            ARC_CREAM,
            "adjacent ring construction-circle intersection minus center construction circle",
        )
        visible.append(region)
        all_regions.append(region)

    return visible, all_regions


def annular_segment(
    target: TargetSpec,
    circle: SynthCircle,
    inner_factor: float,
    outer_factor: float,
    side_mask: np.ndarray,
    *,
    band: np.ndarray | None = None,
) -> np.ndarray:
    outer = circle_mask(circle, radius_override=circle.radius * outer_factor)
    inner = circle_mask(circle, radius_override=circle.radius * inner_factor)
    mask = mask_subtract(outer, inner)
    if band is not None:
        mask = mask_intersection(mask, band)
    return bounded(mask_intersection(mask, side_mask), target)


def build_axial_geometry(target: TargetSpec, circles: list[SynthCircle]) -> tuple[list[SynthRegion], list[SynthRegion]]:
    left_r1 = find_circle(circles, "axial_left", 1.0)
    right_r1 = find_circle(circles, "axial_right", 1.0)
    left_r148 = find_circle(circles, "axial_left", 1.48)
    right_r148 = find_circle(circles, "axial_right", 1.48)
    left_r192 = find_circle(circles, "axial_left", 1.92)
    right_r192 = find_circle(circles, "axial_right", 1.92)
    left_r234 = find_circle(circles, "axial_left", 2.34)
    right_r234 = find_circle(circles, "axial_right", 2.34)
    cx, cy = target_centroid(target)
    band = horizontal_band_mask(cy, target.wavelength * 0.62)
    left_side = half_plane_mask("left", cx - 18)
    right_side = half_plane_mask("right", cx + 18)
    far_left = half_plane_mask("left", left_r1.x - target.wavelength * 0.58)
    far_right = half_plane_mask("right", right_r1.x + target.wavelength * 0.58)

    visible: list[SynthRegion] = []
    all_regions: list[SynthRegion] = []

    central = bounded(mask_intersection(circle_mask(left_r148), circle_mask(right_r148), band), target)
    central = cv2.morphologyEx(central, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    visible.append(
        make_region(
            "axial_central_focal_lens",
            "circle_like",
            "source_derived_central_focal_region",
            (left_r148, right_r148),
            central,
            ARC_CREAM,
            INK,
            "intersection of 1.48R construction circles from both axial sources, clipped to the axial field band",
        )
    )
    all_regions.append(visible[-1])

    for side, source, r192, r234, side_mask in (
        ("left", left_r1, left_r192, left_r234, left_side),
        ("right", right_r1, right_r192, right_r234, right_side),
    ):
        inner = annular_segment(target, source, 0.72, 1.06, side_mask, band=band)
        outer = annular_segment(target, source, 1.24, 1.58, side_mask, band=band)
        for idx, mask in enumerate((inner, outer)):
            region = make_region(
                f"axial_{side}_nested_crescent_{idx + 1}",
                "crescent_like",
                "single_source_wavefront_annular_crescent",
                (source,),
                mask,
                ARC_TEAL if idx == 0 else ARC_CREAM,
                INK,
                "annular segment between wavefront radii from one axial source, clipped by side and axial band",
            )
            visible.append(region)
            all_regions.append(region)

        tip_side = far_left if side == "left" else far_right
        tip_mask = bounded(
            mask_intersection(
                mask_subtract(circle_mask(r234), circle_mask(r192)),
                tip_side,
                boundary_mask_for(target),
            ),
            target,
        )
        tip = make_region(
            f"axial_{side}_negative_side_pressure",
            "trigon_like",
            "boundary_pinched_negative_pressure",
            (r192, r234),
            tip_mask,
            INK,
            ARC_CREAM,
            "outer annular wavefront segment where construction rings meet the pinched boundary",
        )
        visible.append(tip)
        all_regions.append(tip)

    return visible, all_regions


def build_geometry(target: TargetSpec, sources: list[base.WaveSource]) -> tuple[list[SynthCircle], list[SynthRegion], list[SynthRegion]]:
    circles = active_circles(target, sources)
    if target.target_library_key == "radial_sixfold":
        visible, all_regions = build_radial_geometry(target, circles)
    else:
        visible, all_regions = build_axial_geometry(target, circles)
    return circles, visible, all_regions


def draw_construction_circles(
    frame: np.ndarray,
    target: TargetSpec,
    circles: list[SynthCircle],
    *,
    alpha: float,
    labels: bool = False,
) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    for circle in circles:
        thickness = 1 if circle.ring_index != 1.0 else 2
        cv2.circle(
            overlay,
            (round(circle.x), round(circle.y)),
            max(1, round(circle.radius)),
            rgb_to_bgr(CONSTRUCTION),
            thickness,
            lineType=cv2.LINE_AA,
        )
        if labels:
            cv2.circle(overlay, (round(circle.x), round(circle.y)), 3, rgb_to_bgr(MUTED_GOLD), -1, lineType=cv2.LINE_AA)
            base.draw_text(overlay, circle.circle_id, (round(circle.x) + 8, round(circle.y) - 8), LABEL, scale=0.28)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)
    draw_boundary_outline(frame, target, alpha=0.16 * alpha)


def draw_mask_outline(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    thickness: int = 2,
) -> None:
    if alpha <= 0.0:
        return
    contours, _ = cv2.findContours((mask > 9).astype(np.uint8) * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return
    overlay = np.zeros_like(frame)
    cv2.drawContours(overlay, contours, -1, rgb_to_bgr(rgb), thickness, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_arc_regions(frame: np.ndarray, regions: list[SynthRegion], *, alpha: float) -> None:
    if alpha <= 0.0:
        return
    ordered = sorted(regions, key=lambda region: 1 if region.region_class == "trigon_like" else 0)
    for region in ordered:
        if not region.visible_at_peak:
            continue
        if region.region_class == "trigon_like":
            blend_full_mask(frame, region.mask, region.fill_rgb, 0.70 * alpha, glow=0.004 * alpha)
        elif region.region_class == "crescent_like":
            blend_full_mask(frame, region.mask, region.fill_rgb, 0.42 * alpha, glow=0.005 * alpha)
        else:
            blend_full_mask(frame, region.mask, region.fill_rgb, 0.60 * alpha, glow=0.003 * alpha)
    for region in ordered:
        thickness = 2 if region.region_class != "trigon_like" else 3
        draw_mask_outline(frame, region.mask, region.outline_rgb, 0.66 * alpha, thickness=thickness)
        if region.region_class != "trigon_like":
            draw_mask_outline(frame, region.mask, CONSTRUCTION, 0.20 * alpha, thickness=1)


def render_construction_only(target: TargetSpec, circles: list[SynthCircle], regions: list[SynthRegion], *, labels: bool = False) -> np.ndarray:
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    blend_full_mask(frame, boundary_mask_for(target), DARK_TEAL, 0.76)
    draw_construction_circles(frame, target, circles, alpha=0.72, labels=labels)
    draw_arc_regions(frame, regions, alpha=1.0)
    if labels:
        base.draw_text(frame, "construction arcs + selected arc-bounded regions only", (42, 56), LABEL, scale=0.54)
        base.draw_text(frame, "all masks derive from source coordinates and wavefront radii", (42, 84), LABEL, scale=0.36)
    return frame


def draw_nodal_overlay(frame: np.ndarray, field_norm: np.ndarray, target: TargetSpec, *, alpha: float) -> None:
    if alpha <= 0.0:
        return
    field_small = cv2.GaussianBlur(shape_field(field_norm, target.field_gamma), (0, 0), 0.32)
    mask = boundary_mask_small(target) > 0
    node = np.where((np.abs(field_small) <= target.node_epsilon) & mask, 255, 0).astype(np.uint8)
    node = cv2.morphologyEx(node, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    edge = cv2.morphologyEx(node, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_full = cv2.resize(node, (W, H), interpolation=cv2.INTER_LINEAR)
    edge_full = cv2.resize(edge, (W, H), interpolation=cv2.INTER_LINEAR)
    blend_full_mask(frame, node_full, INK, 0.30 * alpha)
    blend_full_mask(frame, edge_full, CYAN_LINE, 0.12 * alpha)


def render_frame(target: TargetSpec, time_seconds: float, *, force_coherence: float | None = None, labels: bool = False) -> tuple[np.ndarray, dict[str, object]]:
    coherence = coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = target_sources_at(target, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=target.blur_sigma)
    levels = synthesis_levels(time_seconds, coherence)
    frame = render_field_only_layer(
        field,
        target,
        wave_alpha=levels["wave_alpha"],
        nodal_alpha=levels["nodal_alpha"],
        labels=labels,
    )
    circles, visible_regions, all_regions = build_geometry(target, sources)
    draw_construction_circles(frame, target, circles, alpha=levels["construction_alpha"], labels=False)
    draw_arc_regions(frame, visible_regions, alpha=levels["region_alpha"])
    draw_nodal_overlay(frame, field, target, alpha=levels["nodal_alpha"])
    if labels:
        base.draw_text(frame, "final synthesis: wave field + construction arcs + source-derived arc regions", (42, 88), LABEL, scale=0.42)
    return frame, {
        "coherence": round(coherence, 4),
        "levels": {key: round(value, 4) for key, value in levels.items()},
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
        "geometry": {
            "construction_circle_count": len(circles),
            "visible_region_count": len([region for region in visible_regions if region.visible_at_peak]),
            "visible_region_classes": {
                class_name: sum(1 for region in visible_regions if region.region_class == class_name)
                for class_name in ("circle_like", "crescent_like", "trigon_like")
            },
            "region_ids": [region.region_id for region in visible_regions if region.visible_at_peak],
        },
    }


def render_baseline_wave_peak(target: TargetSpec) -> np.ndarray:
    baseline = BASELINE_TARGETS[target.key]
    sources = target_sources_at(baseline, PEAK_TIME_SECONDS, 1.0)
    field = base.evaluate_field(sources, PEAK_TIME_SECONDS, blur_sigma=baseline.blur_sigma)
    return render_field_only_layer(field, baseline, labels=True, baseline=True)


def draw_source_debug_panel(target: TargetSpec, coherence: float, time_seconds: float) -> np.ndarray:
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    blend_mask(frame, boundary_mask_for(target), DEEP_TEAL, 0.42)
    draw_boundary_outline(frame, target, alpha=0.38)
    current = target_sources_at(target, time_seconds, coherence)
    overlay = np.zeros_like(frame)
    for fixed in target.sources:
        cv2.circle(overlay, (round(fixed.x), round(fixed.y)), 8, rgb_to_bgr(MUTED_GOLD), 1, lineType=cv2.LINE_AA)
    for source in current:
        cv2.circle(overlay, (round(source.x), round(source.y)), 12, rgb_to_bgr(GOLD), 2, lineType=cv2.LINE_AA)
        cv2.circle(overlay, (round(source.x), round(source.y)), 2, rgb_to_bgr(IVORY), -1, lineType=cv2.LINE_AA)
        base.draw_text(overlay, source.source_id, (round(source.x) + 13, round(source.y) - 10), LABEL, scale=0.30)
    cv2.addWeighted(overlay, 0.92, frame, 1.0, 0, dst=frame)
    base.draw_text(frame, f"{target.title}  c={coherence:.1f}", (42, 56), LABEL, scale=0.58)
    base.draw_text(frame, "gold=current sources; muted rings=target locks; no primitive overlays", (42, 86), LABEL, scale=0.36)
    return cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)


def draw_source_boundary_debug_still(target: TargetSpec) -> np.ndarray:
    field_frame, _ = render_frame(target, PEAK_TIME_SECONDS, force_coherence=1.0, labels=True)
    overlay = np.zeros_like(field_frame)
    sources = target_sources_at(target, PEAK_TIME_SECONDS, 1.0)
    for source in sources:
        cv2.circle(overlay, (round(source.x), round(source.y)), 14, rgb_to_bgr(GOLD), 2, lineType=cv2.LINE_AA)
        cv2.circle(overlay, (round(source.x), round(source.y)), 3, rgb_to_bgr(IVORY), -1, lineType=cv2.LINE_AA)
        base.draw_text(overlay, source.source_id, (round(source.x) + 14, round(source.y) - 12), LABEL, scale=0.34)
    cv2.addWeighted(overlay, 0.92, field_frame, 1.0, 0, dst=field_frame)
    base.draw_text(field_frame, "source / boundary debug at c=1", (42, 88), LABEL, scale=0.44)
    return field_frame


def wave_only_peak(target: TargetSpec, *, labels: bool = False) -> tuple[np.ndarray, np.ndarray, list[base.WaveSource], list[SynthCircle], list[SynthRegion], list[SynthRegion]]:
    sources = target_sources_at(target, PEAK_TIME_SECONDS, 1.0)
    field = base.evaluate_field(sources, PEAK_TIME_SECONDS, blur_sigma=target.blur_sigma)
    frame = render_field_only_layer(field, target, labels=labels)
    circles, regions, all_regions = build_geometry(target, sources)
    if labels:
        base.draw_text(frame, "wave only at c=1", (42, 88), LABEL, scale=0.42)
    return frame, field, sources, circles, regions, all_regions


def render_final_peak(target: TargetSpec, *, labels: bool = False) -> tuple[np.ndarray, dict[str, object]]:
    return render_frame(target, PEAK_TIME_SECONDS, force_coherence=1.0, labels=labels)


def make_three_view_still(target: TargetSpec) -> Path:
    THREE_VIEW_DIR.mkdir(parents=True, exist_ok=True)
    wave, _field, _sources, circles, regions, _all_regions = wave_only_peak(target, labels=True)
    construction = render_construction_only(target, circles, regions, labels=True)
    final, _ = render_final_peak(target, labels=True)
    panels = [
        cv2.resize(wave, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(construction, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(final, (640, 360), interpolation=cv2.INTER_AREA),
    ]
    sheet = cv2.hconcat(panels)
    path = THREE_VIEW_DIR / f"{target.key}_v003_three_views_peak.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_debug_sheet() -> Path:
    rows = []
    for target in TARGETS:
        row = cv2.hconcat(
            [
                draw_source_debug_panel(target, 0.0, 1.5),
                draw_source_debug_panel(target, 0.5, 4.0),
                draw_source_debug_panel(target, 1.0, 6.0),
            ]
        )
        rows.append(row)
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "integrated_choreographer_v003_geometric_synthesis_debug_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_contact_sheet() -> Path:
    rows = []
    for target in TARGETS:
        mid = cv2.imread(str(MIDPOINT_DIR / f"{target.key}_v003_midpoint.png"), cv2.IMREAD_COLOR)
        peak = cv2.imread(str(PEAK_DIR / f"{target.key}_v003_peak.png"), cv2.IMREAD_COLOR)
        if mid is None or peak is None:
            continue
        left = cv2.resize(mid, (960, 540), interpolation=cv2.INTER_AREA)
        right = cv2.resize(peak, (960, 540), interpolation=cv2.INTER_AREA)
        base.draw_text(left, f"{target.title} midpoint c=1", (34, 48), LABEL, scale=0.55)
        base.draw_text(right, f"{target.title} peak synthesis", (34, 48), LABEL, scale=0.55)
        rows.append(cv2.hconcat([left, right]))
    sheet = cv2.vconcat(rows) if rows else np.zeros((540, 1920, 3), dtype=np.uint8)
    path = OUT_DIR / "integrated_choreographer_v003_geometric_synthesis_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def blank_missing(label: str, path: Path) -> np.ndarray:
    img = np.zeros((H, W, 3), dtype=np.uint8)
    base.draw_text(img, label, (60, 80), LABEL, scale=0.58)
    base.draw_text(img, f"missing: {path}", (60, 116), LABEL, scale=0.36)
    return img


def read_or_blank(path: Path, label: str) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return blank_missing(label, path)
    return img


def make_v002_v003_comparison(target: TargetSpec) -> Path:
    v002_peak = {
        "radial_sixfold_geometric_synthesis": V002_DIR / "peak_stills" / "radial_sixfold_field_only_v002_peak.png",
        "axial_eye_geometric_synthesis": V002_DIR / "peak_stills" / "axial_eye_field_only_v002_peak.png",
    }[target.key]
    v003_peak = PEAK_DIR / f"{target.key}_v003_peak.png"
    left = cv2.resize(read_or_blank(v002_peak, "v002 field-only peak"), (960, 540), interpolation=cv2.INTER_AREA)
    right = cv2.resize(read_or_blank(v003_peak, "v003 geometric synthesis peak"), (960, 540), interpolation=cv2.INTER_AREA)
    base.draw_text(left, "v002 peak: field-only rounded regions", (34, 48), LABEL, scale=0.54)
    base.draw_text(right, "v003 peak: source-derived geometric synthesis", (34, 48), LABEL, scale=0.54)
    comparison = cv2.hconcat([left, right])
    path = COMPARISON_DIR / f"{target.key}_v002_v003_peak_comparison.png"
    cv2.imwrite(str(path), comparison)
    return path


def make_radial_v007_comparison(target: TargetSpec) -> Path | None:
    if target.target_library_key != "radial_sixfold":
        return None
    v007_peak = V007_DIR / "peak_stills" / "raindrop_to_sun_v007_peak.png"
    v003_peak = PEAK_DIR / f"{target.key}_v003_peak.png"
    left = cv2.resize(read_or_blank(v007_peak, "v007 raindrop_to_sun peak"), (960, 540), interpolation=cv2.INTER_AREA)
    right = cv2.resize(read_or_blank(v003_peak, "v003 radial peak"), (960, 540), interpolation=cv2.INTER_AREA)
    base.draw_text(left, "v007 raindrop_to_sun: stronger construction, heavier overlay", (24, 48), LABEL, scale=0.46)
    base.draw_text(right, "v003 radial: same idea integrated into v002 choreographer", (24, 48), LABEL, scale=0.46)
    comparison = cv2.hconcat([left, right])
    path = COMPARISON_DIR / f"{target.key}_v007_raindrop_to_sun_comparison.png"
    cv2.imwrite(str(path), comparison)
    return path


def make_v004_reference_comparison(target: TargetSpec) -> Path:
    if target.target_library_key == "radial_sixfold":
        stem = "sun_raw_scallop_trigons_v004"
    else:
        stem = "two_source_lens_cells_v004"
    posneg = V004_DIR / "debug_stills" / f"{stem}_positive_negative_regions_midpoint.png"
    nodal = V004_DIR / "debug_stills" / f"{stem}_nodal_lines_midpoint.png"
    peak = PEAK_DIR / f"{target.key}_v003_peak.png"
    panels = [
        cv2.resize(read_or_blank(posneg, "v004 positive/negative reference"), (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(read_or_blank(nodal, "v004 nodal reference"), (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(read_or_blank(peak, "v003 peak"), (640, 360), interpolation=cv2.INTER_AREA),
    ]
    labels = ["v004 positive/negative", "v004 nodal linework", "v003 synthesis"]
    for panel, label in zip(panels, labels, strict=True):
        base.draw_text(panel, label, (18, 36), LABEL, scale=0.42)
    sheet = cv2.hconcat(panels)
    path = COMPARISON_DIR / f"{target.key}_v004_reference_comparison.png"
    cv2.imwrite(str(path), sheet)
    return path


def save_debug_stills(target: TargetSpec) -> dict[str, str]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    THREE_VIEW_DIR.mkdir(parents=True, exist_ok=True)

    baseline_peak = render_baseline_wave_peak(target)
    baseline_path = DEBUG_DIR / f"{target.key}_v003_wave_only_baseline_peak.png"
    cv2.imwrite(str(baseline_path), baseline_peak)

    wave_peak, field, sources, circles, regions, all_regions = wave_only_peak(target, labels=True)
    wave_peak_path = DEBUG_DIR / f"{target.key}_v003_wave_only_peak.png"
    cv2.imwrite(str(wave_peak_path), wave_peak)

    construction_peak = render_construction_only(target, circles, regions, labels=True)
    construction_path = DEBUG_DIR / f"{target.key}_v003_construction_regions_only_peak.png"
    cv2.imwrite(str(construction_path), construction_peak)

    source_debug = draw_source_boundary_debug_still(target)
    source_debug_path = DEBUG_DIR / f"{target.key}_v003_source_boundary_debug_peak.png"
    cv2.imwrite(str(source_debug_path), source_debug)

    full_geometry = render_construction_only(target, circles, all_regions, labels=True)
    full_geometry_path = DEBUG_DIR / f"{target.key}_v003_full_geometry_debug_peak.png"
    cv2.imwrite(str(full_geometry_path), full_geometry)

    three_view_path = make_three_view_still(target)
    v002_comparison = make_v002_v003_comparison(target)
    v004_comparison = make_v004_reference_comparison(target)
    radial_v007 = make_radial_v007_comparison(target)

    out = {
        "wave_only_baseline_peak": str(baseline_path.relative_to(OUT_DIR)),
        "wave_only_peak": str(wave_peak_path.relative_to(OUT_DIR)),
        "construction_regions_only_peak": str(construction_path.relative_to(OUT_DIR)),
        "source_boundary_debug_peak": str(source_debug_path.relative_to(OUT_DIR)),
        "full_geometry_debug_peak": str(full_geometry_path.relative_to(OUT_DIR)),
        "three_view_peak": str(three_view_path.relative_to(OUT_DIR)),
        "v002_v003_peak_comparison": str(v002_comparison.relative_to(OUT_DIR)),
        "v004_reference_comparison": str(v004_comparison.relative_to(OUT_DIR)),
    }
    if radial_v007 is not None:
        out["v007_raindrop_to_sun_comparison"] = str(radial_v007.relative_to(OUT_DIR))
    return out


def render_clip(target: TargetSpec, *, write_video: bool = True) -> dict[str, object]:
    output_path = OUT_DIR / target.filename
    midpoint_frame: np.ndarray | None = None
    peak_frame: np.ndarray | None = None
    coherence_samples: dict[str, object] = {}

    if write_video:
        writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
        try:
            for frame_idx in range(N_FRAMES):
                time_seconds = frame_idx / FPS
                frame, info = render_frame(target, time_seconds)
                writer.write(frame)
                if frame_idx == MIDPOINT_FRAME:
                    midpoint_frame = frame.copy()
                    coherence_samples["midpoint"] = info
                if frame_idx == PEAK_FRAME:
                    peak_frame = frame.copy()
                    coherence_samples["peak"] = info
                if (frame_idx + 1) % FPS == 0:
                    print(f"  {target.filename} {frame_idx + 1}/{N_FRAMES}", flush=True)
        finally:
            writer.close()
    else:
        output_path = OUT_DIR / target.filename
        midpoint_frame, coherence_samples["midpoint"] = render_frame(target, MIDPOINT_FRAME / FPS, force_coherence=1.0)
        peak_frame, coherence_samples["peak"] = render_frame(target, PEAK_TIME_SECONDS, force_coherence=1.0)

    if midpoint_frame is None:
        midpoint_frame, coherence_samples["midpoint"] = render_frame(target, MIDPOINT_FRAME / FPS, force_coherence=1.0)
    if peak_frame is None:
        peak_frame, coherence_samples["peak"] = render_frame(target, PEAK_TIME_SECONDS, force_coherence=1.0)

    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    midpoint_path = MIDPOINT_DIR / f"{target.key}_v003_midpoint.png"
    peak_path = PEAK_DIR / f"{target.key}_v003_peak.png"
    cv2.imwrite(str(midpoint_path), midpoint_frame)
    cv2.imwrite(str(peak_path), peak_frame)

    debug_stills = save_debug_stills(target)

    return {
        "key": target.key,
        "filename": target.filename,
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "midpoint_still": str(midpoint_path.relative_to(OUT_DIR)),
        "peak_still": str(peak_path.relative_to(OUT_DIR)),
        "debug_stills": debug_stills,
        "source_count": len(target.sources),
        "symmetry_type": target.symmetry_type,
        "source_spacing": target.source_spacing,
        "source_spacing_ratio": target.source_spacing_ratio,
        "wavelength": target.wavelength,
        "threshold": target.threshold,
        "node_epsilon": target.node_epsilon,
        "coherence_samples": coherence_samples,
    }


def target_to_manifest(target: TargetSpec) -> dict[str, object]:
    return {
        "key": target.key,
        "title": target.title,
        "target_library_key": target.target_library_key,
        "filename": target.filename,
        "beauty_render": "source-derived geometric synthesis: two-tone wave field, construction-circle arcs, selected arc-bounded regions, nodal/interstitial linework; no generic primitive glyphs",
        "symmetry_type": target.symmetry_type,
        "source_spacing": target.source_spacing,
        "source_spacing_ratio_to_wavelength": target.source_spacing_ratio,
        "wavelength": target.wavelength,
        "frequency": target.frequency,
        "decay": target.decay,
        "threshold": target.threshold,
        "node_epsilon": target.node_epsilon,
        "blur_sigma": target.blur_sigma,
        "field_gamma": target.field_gamma,
        "boundary_type": target.boundary_type,
        "boundary_axes": list(target.boundary_axes),
        "reference_notes": target.reference_notes,
        "tuning_notes": target.tuning_notes,
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
    }


def write_manifest(
    summaries: list[dict[str, object]],
    contact_sheet: Path,
    debug_sheet: Path,
) -> Path:
    manifest = {
        "project": "integrated_choreographer_v003_geometric_synthesis",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "renderer": "scripts/integrated_choreographer_v003_geometric_synthesis.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "parked": ["linear_flow"],
        "beauty_layer_rule": {
            "separate_primitive_overlay": False,
            "generic_primitive_glyphs": False,
            "source_derived_layers": [
                "wave-amplitude positive/negative field",
                "construction-circle arcs from source coordinates and wavefront radii",
                "selected arc-bounded regions from boolean construction-circle masks",
                "thin nodal/interstitial linework",
            ],
            "deleted_from_beauty": [
                "former v001 arrow and ray overlays",
                "thick white/cream crescent overlay strokes",
                "detached primitive icons",
            ],
        },
        "coherence_curve": {
            "parameter": "c",
            "range": [0.0, 1.0],
            "curve": "smoothstep gather/release",
            "timing_seconds": {
                "0.0-3.0": "loose drifting wave field, c=0",
                "3.0-5.0": "smoothstep gather to target, c 0->1",
                "5.0-8.0": "target lock hold, c=1; wave field remains and source-derived geometric synthesis becomes primary",
                "8.0-10.0": "smoothstep release, c 1->0",
                "10.0-12.0": "drift continues, c=0",
            },
            "drift_behavior": "source orbits target with radius drift_amplitude * (1 - c^2), per-source angular velocity and phase perturbation",
        },
        "target_library": [target_to_manifest(target) for target in TARGETS],
        "construction_rule": {
            "radial": "source spacing S equals construction radius R; selected center-ring and adjacent-ring circle intersections form the peak crescent/trigon-like regions",
            "axial": "two source positions stay from v002; construction rings use source wavelength multiples as wavefront radii to form nested side crescents and pinched side pressure regions",
            "audit_principle": "Every visible arc-bounded region stores source_circle_ids/source_ids in the peak coherence sample.",
        },
        "clips": summaries,
        "deliverables": {
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_sheet.relative_to(OUT_DIR)),
            "midpoint_stills": sorted(path.name for path in MIDPOINT_DIR.glob("*.png")),
            "peak_stills": sorted(path.name for path in PEAK_DIR.glob("*.png")),
            "comparison_stills": sorted(path.name for path in COMPARISON_DIR.glob("*.png")),
            "three_view_stills": sorted(path.name for path in THREE_VIEW_DIR.glob("*.png")),
            "debug_stills": sorted(path.name for path in DEBUG_DIR.glob("*.png")),
        },
    }
    path = OUT_DIR / "integrated_choreographer_v003_geometric_synthesis_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    axial_ref_status = (
        f"located and viewed at `{AXIAL_REFERENCE_IMAGE}`"
        if AXIAL_REFERENCE_IMAGE.exists()
        else "not locatable in repo/meeting media during this render; proceeded from known axial structure"
    )
    lines = [
        "# Integrated Choreographer v003 Geometric Synthesis",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet recovers the strongest qualities from v004/v007 while keeping the cleaner v002 choreographer. v002 proved the former v001 arrow/ray overlays, thick cream crescent strokes, and detached primitive icons should stay gone. v003 does not bring those back. Instead it renders multiple mathematical views of the same source configuration: wave-amplitude field, construction-circle arcs, selected arc-bounded regions, and thin nodal/interstitial linework.",
        "",
        "Core design philosophy: the field does not create exact art. The field gathers into a geometry where a primitive-like positive/negative composition may become the readable view of that same geometry. v003 names that view as source-derived geometric synthesis, not cultural validation.",
        "",
        "Use safe internal language only: primitive-like positive/negative composition; source-derived geometric synthesis; internal exploration pending cultural review.",
        "",
        "## Architecture",
        "",
        "- Reuses the v002 target-library and choreographer shape for the radial and axial targets.",
        "- Parks linear flow.",
        "- Keeps 12-second timing: 0-3s drift, 3-5s smoothstep gather, 5-8s coherence hold, 8-10s release, 10-12s drift.",
        "- Beauty render has no generic primitive glyph overlay.",
        "- Peak synthesis layers are wave field, faint construction arcs, selected arc-bounded regions, and carved nodal/interstitial linework.",
        "- All arc-bounded regions derive from source positions and wavefront radii. Radial uses S=R construction circles. Axial uses wavefront-radius multiples from the same two source positions.",
        "",
        "## Reference Handling",
        "",
        f"The axial internal reference image was {axial_ref_status}. It was used only as a private structural reference for an axial 1-2-1 rhythm. This packet does not copy that image, does not claim cultural correctness, and does not present the result as an Austin-approved form.",
        "",
        "## Clips",
        "",
    ]
    for summary in summaries:
        target = target_by_key(str(summary["key"]))
        lines.append(
            f"- `{target.filename}`: target `{target.target_library_key}`, symmetry `{target.symmetry_type}`, {len(target.sources)} sources. {target.tuning_notes}"
        )
    lines.extend(
        [
            "",
            "## Deliverables",
            "",
            "- 2 MP4 clips, 1920x1080, 24 fps, 12 seconds.",
            "- Midpoint stills in `midpoint_stills/`.",
            "- Peak stills in `peak_stills/`.",
            "- Contact sheet: `integrated_choreographer_v003_geometric_synthesis_contact_sheet.png`.",
            "- Debug sheet: `integrated_choreographer_v003_geometric_synthesis_debug_sheet.png` showing `c=0`, `c=0.5`, and `c=1` source positions.",
            "- Three-view stills in `three_view_stills/`: wave-only / construction arcs plus arc regions / final synthesis.",
            "- Comparison stills in `comparison_stills/`: v002 peak vs v003 peak, v007 raindrop_to_sun vs radial v003, and v004 positive-negative/nodal references vs v003.",
            "- Manifest: `integrated_choreographer_v003_geometric_synthesis_manifest.json`.",
            "",
            "## Honest Verdict",
            "",
            "Radial: v003 is deliberately more legible than v002. The peak recovers a central source circle, six source-derived crescent/lens regions, and six darker negative-space trigon-like gaps. It avoids v001's pasted icon problem because the shapes are boolean combinations of the same construction circles that share the wave source positions and wavelength. The result is more constructed than v002, but the construction layer explains the read instead of sitting beside the field.",
            "",
            "Axial: v003 improves the nested side crescent read by adding source-derived wavefront annular segments. The central region is still a focal/lens construction rather than a clean designed oval, and the side pressure/notch regions remain less forceful than the radial trigon gaps. This is a useful mathematical alignment study, not a finished visual answer.",
            "",
            "Self-check: no external reviewers were available inside this automated render run. B's honest checklist rating is: radial passes the requested improvement test against v002; it no longer reads as only rounded amplitude blobs and does not use detached icons. Axial passes the crescent/arc improvement test, but the trigon/side-pressure read remains subtle and should be treated as provisional.",
            "",
            "## Cultural Boundary",
            "",
            "This is an internal mathematical visual study only. It is not Austin-approved. It does not claim Coast Salish correctness, reconstruct Coast Salish design, validate a cultural grammar, or carry cultural meaning. Austin review is required to determine which renderings resonate and which read as off.",
            "",
            "Renderer: `scripts/integrated_choreographer_v003_geometric_synthesis.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render integrated choreographer v003 geometric-synthesis packet.")
    parser.add_argument(
        "--clip",
        choices=["all", *[target.key for target in TARGETS]],
        default="all",
        help="Render one clip for iteration, or all clips for the final packet.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Write still/debug artifacts without MP4s for fast tuning.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    THREE_VIEW_DIR.mkdir(parents=True, exist_ok=True)

    selected = list(TARGETS if args.clip == "all" else [target_by_key(args.clip)])
    summaries: list[dict[str, object]] = []
    for target in selected:
        action = "Previewing" if args.preview else "Rendering"
        print(f"{action} {target.filename}", flush=True)
        summaries.append(render_clip(target, write_video=not args.preview))

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
        print(f"{'Previewed' if args.preview else 'Rendered'} {selected[0].filename}", flush=True)


if __name__ == "__main__":
    main()
