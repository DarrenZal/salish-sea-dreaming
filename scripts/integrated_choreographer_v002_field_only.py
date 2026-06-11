#!/usr/bin/env python3
"""
Integrated choreographer v002, field-only.

Internal mathematical/visual alignment study for Salish Sea Dreaming. This
version keeps the v001 source-gathering architecture, removes the separate
primitive overlay from beauty renders, and tests whether the coherent scalar
field itself carries a primitive-like positive/negative composition.

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
    / "integrated_choreographer_v002_field_only_2026-05-21"
)
V001_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v001_2026-05-21"
)
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
COMPARISON_DIR = OUT_DIR / "comparison_stills"

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
        key=f"axial_eye_field_only{key_suffix}",
        filename="axial_eye_field_only_v002.mp4",
        title="axial_eye_field_only",
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
            f"Axial source separation tested as {ratio:.1f}x wavelength; chosen target seeks one central oval, "
            "or focal channel, two side crescent-like bands per side, and a far-side pressure/cusp region through field and boundary only."
        ),
        sources=axial_sources(unit),
    )


TARGETS: tuple[TargetSpec, ...] = (
    TargetSpec(
        key="radial_sixfold_field_only",
        filename="radial_sixfold_field_only_v002.mp4",
        title="radial_sixfold_field_only",
        target_library_key="radial_sixfold",
        symmetry_type="C6v",
        source_spacing=250.0,
        source_spacing_ratio=None,
        drift_amplitude=130.0,
        wavelength=250.0,
        frequency=0.12,
        decay=980.0,
        node_epsilon=0.050,
        threshold=0.055,
        blur_sigma=0.68,
        field_gamma=0.90,
        phase_anchor_distance=250.0,
        boundary_type="sun_disk",
        boundary_axes=(570.0, 465.0),
        reference_notes="Seven-source radial seed/hex layout inherited from v001; linear flow parked for v002.",
        tuning_notes=(
            "Beauty uses only thresholded scalar regions and nodal linework. Center source amplitude is raised within the "
            "requested +10-20% range; central circle, surrounding cupped lobes, and negative-space trigon gaps are field regions."
        ),
        sources=radial_sources(250.0),
    ),
    # Ratio 2.0 kept the clearest nested side-band read in the generated spacing test sheet.
    make_axial_target_for_ratio(2.0),
)


BASELINE_TARGETS: dict[str, TargetSpec] = {
    "radial_sixfold_field_only": replace(
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
        reference_notes="v001-equivalent wave-only baseline with the primitive overlay hidden.",
        tuning_notes="Baseline field-only read before v002 sharpening.",
    ),
    "axial_eye_field_only": replace(
        make_axial_target_for_ratio(2.0, key_suffix="_baseline"),
        key="axial_eye_field_only",
        source_spacing=550.0,
        wavelength=275.0,
        decay=940.0,
        node_epsilon=0.054,
        threshold=0.038,
        blur_sigma=0.72,
        field_gamma=1.0,
        boundary_type="eye_oval",
        boundary_axes=(720.0, 330.0),
        reference_notes="v001-equivalent two-source axial wave-only baseline with the primitive overlay hidden.",
        tuning_notes="Baseline field-only read before spacing and threshold test.",
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
    labels: bool = False,
    baseline: bool = False,
) -> np.ndarray:
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

    blend_mask(frame_small, mask, DARK_TEAL, 0.96)
    blend_mask(frame_small, neg_mask, TEAL, 0.90)
    blend_mask(frame_small, pos_mask, CREAM, 0.98)

    # Linework is derived from nodal/interstitial zero-regions, not from a separate glyph layer.
    blend_mask(frame_small, edge_mask, INK, 0.28)
    blend_mask(frame_small, node_mask, INK, 0.70)
    blend_mask(frame_small, node_edge, CYAN_LINE, 0.18)

    frame = cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)
    draw_boundary_outline(frame, target, alpha=0.52, baseline=baseline)
    if labels:
        base.draw_text(frame, "field only: positive/negative regions + nodal/interstitial linework", (42, 56), LABEL, scale=0.46)
    return frame


def render_frame(target: TargetSpec, time_seconds: float, *, force_coherence: float | None = None, labels: bool = False) -> tuple[np.ndarray, dict[str, object]]:
    coherence = coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = target_sources_at(target, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=target.blur_sigma)
    frame = render_field_only_layer(field, target, labels=labels)
    return frame, {
        "coherence": round(coherence, 4),
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


def make_debug_sheet() -> Path:
    rows = []
    for target in TARGETS:
        rows.append(
            cv2.hconcat(
                [
                    draw_source_debug_panel(target, 0.0, 1.5),
                    draw_source_debug_panel(target, 0.5, 4.0),
                    draw_source_debug_panel(target, 1.0, 6.0),
                ]
            )
        )
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "integrated_choreographer_v002_field_only_debug_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_contact_sheet() -> Path:
    rows = []
    for target in TARGETS:
        mid = cv2.imread(str(MIDPOINT_DIR / f"{target.key}_v002_midpoint.png"), cv2.IMREAD_COLOR)
        peak = cv2.imread(str(PEAK_DIR / f"{target.key}_v002_peak.png"), cv2.IMREAD_COLOR)
        if mid is None or peak is None:
            continue
        left = cv2.resize(mid, (960, 540), interpolation=cv2.INTER_AREA)
        right = cv2.resize(peak, (960, 540), interpolation=cv2.INTER_AREA)
        base.draw_text(left, f"{target.title} midpoint c=1 field-only", (34, 48), LABEL, scale=0.55)
        base.draw_text(right, f"{target.title} peak c=1 field-only", (34, 48), LABEL, scale=0.55)
        rows.append(cv2.hconcat([left, right]))
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "integrated_choreographer_v002_field_only_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_v001_v002_comparison(target: TargetSpec) -> Path:
    v001_name = {
        "radial_sixfold_field_only": "radial_sixfold_gather_v001_peak.png",
        "axial_eye_field_only": "axial_eye_wave_gather_v001_peak.png",
    }[target.key]
    v001_path = V001_DIR / "peak_stills" / v001_name
    v002_path = PEAK_DIR / f"{target.key}_v002_peak.png"
    v001 = cv2.imread(str(v001_path), cv2.IMREAD_COLOR)
    v002 = cv2.imread(str(v002_path), cv2.IMREAD_COLOR)
    if v001 is None:
        v001 = np.zeros((H, W, 3), dtype=np.uint8)
        base.draw_text(v001, f"missing v001 comparison source: {v001_path}", (60, 80), LABEL, scale=0.54)
    if v002 is None:
        v002 = np.zeros((H, W, 3), dtype=np.uint8)
        base.draw_text(v002, f"missing v002 peak source: {v002_path}", (60, 80), LABEL, scale=0.54)
    left = cv2.resize(v001, (960, 540), interpolation=cv2.INTER_AREA)
    right = cv2.resize(v002, (960, 540), interpolation=cv2.INTER_AREA)
    base.draw_text(left, "v001 peak: combined overlay", (34, 48), LABEL, scale=0.58)
    base.draw_text(right, "v002 peak: field only", (34, 48), LABEL, scale=0.58)
    comparison = cv2.hconcat([left, right])
    path = COMPARISON_DIR / f"{target.key}_v001_v002_peak_comparison.png"
    cv2.imwrite(str(path), comparison)
    return path


def make_axial_spacing_test_sheet() -> Path:
    panels = []
    for ratio in (2.0, 2.5, 3.0):
        candidate = make_axial_target_for_ratio(ratio, key_suffix=f"_spacing_{str(ratio).replace('.', '_')}")
        BOUNDARY_CACHE[candidate.key] = full_boundary_mask(candidate)
        sources = target_sources_at(candidate, PEAK_TIME_SECONDS, 1.0)
        field = base.evaluate_field(sources, PEAK_TIME_SECONDS, blur_sigma=candidate.blur_sigma)
        panel = render_field_only_layer(field, candidate, labels=False)
        panel_small = cv2.resize(panel, (640, 360), interpolation=cv2.INTER_AREA)
        base.draw_text(panel_small, f"axial spacing test: separation={ratio:.1f}x wavelength", (22, 36), LABEL, scale=0.42)
        panels.append(panel_small)
    sheet = cv2.hconcat(panels)
    path = DEBUG_DIR / "axial_spacing_ratio_test_v002.png"
    cv2.imwrite(str(path), sheet)
    return path


def save_debug_stills(target: TargetSpec) -> dict[str, str]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    baseline_peak = render_baseline_wave_peak(target)
    baseline_path = DEBUG_DIR / f"{target.key}_v002_v001_baseline_wave_only_peak.png"
    cv2.imwrite(str(baseline_path), baseline_peak)

    sharpened_peak, _ = render_frame(target, PEAK_TIME_SECONDS, force_coherence=1.0, labels=True)
    sharpened_path = DEBUG_DIR / f"{target.key}_v002_sharpened_field_peak.png"
    cv2.imwrite(str(sharpened_path), sharpened_peak)

    source_debug = draw_source_boundary_debug_still(target)
    source_debug_path = DEBUG_DIR / f"{target.key}_v002_source_boundary_debug_peak.png"
    cv2.imwrite(str(source_debug_path), source_debug)

    comparison_path = make_v001_v002_comparison(target)
    return {
        "baseline_wave_only_peak": str(baseline_path.relative_to(OUT_DIR)),
        "sharpened_field_peak": str(sharpened_path.relative_to(OUT_DIR)),
        "source_boundary_debug_peak": str(source_debug_path.relative_to(OUT_DIR)),
        "v001_v002_peak_comparison": str(comparison_path.relative_to(OUT_DIR)),
    }


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
    midpoint_path = MIDPOINT_DIR / f"{target.key}_v002_midpoint.png"
    peak_path = PEAK_DIR / f"{target.key}_v002_peak.png"
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
        "beauty_render": "field-only two-tone positive/negative regions with nodal/interstitial linework; no separate primitive overlay",
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
    spacing_test_sheet: Path,
) -> Path:
    manifest = {
        "project": "integrated_choreographer_v002_field_only",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "renderer": "scripts/integrated_choreographer_v002_field_only.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "parked": ["linear_flow"],
        "beauty_layer_rule": {
            "field_only": True,
            "separate_primitive_overlay": False,
            "deleted_from_beauty": [
                "brown trigon/arrow/dart glyphs",
                "thick white/cream crescent strokes",
                "separately drawn primitive icons",
            ],
            "preserved": [
                "two-tone positive/negative field regions",
                "dark nodal/interstitial linework",
                "bounded silhouette/mask",
            ],
        },
        "coherence_curve": {
            "parameter": "c",
            "range": [0.0, 1.0],
            "curve": "smoothstep gather/release",
            "timing_seconds": {
                "0.0-3.0": "loose drifting wave field, c=0",
                "3.0-5.0": "smoothstep gather to target, c 0->1",
                "5.0-8.0": "target lock hold, c=1; field-only composition must carry the read",
                "8.0-10.0": "smoothstep release, c 1->0",
                "10.0-12.0": "drift continues, c=0",
            },
            "drift_behavior": "source orbits target with radius drift_amplitude * (1 - c^2), per-source angular velocity and phase perturbation",
        },
        "target_library": [target_to_manifest(target) for target in TARGETS],
        "axial_spacing_tests": {
            "tested_source_separation_to_wavelength_ratios": [2.0, 2.5, 3.0],
            "chosen_ratio": 2.0,
            "reason": "cleanest internal field-only axial read in generated peak spacing sheet: strongest nested side crescent-like bands and less broad flattening than 2.5x or 3.0x",
            "debug_sheet": str(spacing_test_sheet.relative_to(OUT_DIR)),
        },
        "clips": summaries,
        "deliverables": {
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_sheet.relative_to(OUT_DIR)),
            "axial_spacing_test_sheet": str(spacing_test_sheet.relative_to(OUT_DIR)),
            "midpoint_stills": sorted(path.name for path in MIDPOINT_DIR.glob("*.png")),
            "peak_stills": sorted(path.name for path in PEAK_DIR.glob("*.png")),
            "comparison_stills": sorted(path.name for path in COMPARISON_DIR.glob("*.png")),
            "debug_stills": sorted(path.name for path in DEBUG_DIR.glob("*.png")),
        },
    }
    path = OUT_DIR / "integrated_choreographer_v002_field_only_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    axial_ref_status = (
        f"located and viewed at `{AXIAL_REFERENCE_IMAGE}`"
        if AXIAL_REFERENCE_IMAGE.exists()
        else "not locatable in repo/meeting media during this render; proceeded from known axial structure"
    )
    lines = [
        "# Integrated Choreographer v002 Field Only",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet isolates the v001 question: can the coherent wave field carry the composition without a separate primitive overlay? The beauty renders remove the brown trigon/dart glyphs, thick cream crescent strokes, and all separately drawn primitive icons. What remains is the scalar field rendered as two-tone positive/negative regions, bounded silhouette, and dark nodal/interstitial linework.",
        "",
        "Core design philosophy: the field does not create exact art. The field gathers into a geometry where a primitive-like positive/negative composition may become the readable view of that same geometry.",
        "",
        "Use safe internal language only: primitive-like positive/negative composition; field structure that may resonate with circle/crescent/trigon vocabulary; internal exploration pending cultural review.",
        "",
        "## Architecture",
        "",
        "- Reuses the v001 target-library and choreographer shape for the radial and axial targets.",
        "- Parks linear flow for this test.",
        "- Keeps 12-second timing: 0-3s drift, 3-5s smoothstep gather, 5-8s coherence hold, 8-10s release, 10-12s drift.",
        "- Beauty render is field-only: no primitive renderer, no separate composition glyphs, no icon overlays.",
        "- Sharpening is limited to field parameters: source amplitude, source spacing, wavelength, threshold, nodal epsilon, blur, decay, and boundary/mask interaction.",
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
            "- Contact sheet: `integrated_choreographer_v002_field_only_contact_sheet.png`.",
            "- Debug sheet: `integrated_choreographer_v002_field_only_debug_sheet.png` showing `c=0`, `c=0.5`, and `c=1` source positions for each target.",
            "- Debug stills include v001-equivalent wave-only peak, sharpened v002 field peak, source/boundary peak debug, and axial spacing-ratio tests.",
            "- Comparison stills in `comparison_stills/`: v001 peak with overlay vs v002 peak field-only, same scale.",
            "- Manifest: `integrated_choreographer_v002_field_only_manifest.json`.",
            "",
            "## Honest Verdict",
            "",
            "Radial: the field-only peak is the stronger of the two v002 studies. It gives a solid central field cell, six cupping surrounding regions, and dark interstitial gaps that can be read as trigon-like negative spaces without drawing separate rays. The read is still mathematical and water/cymatic, but the overlay is no longer needed for the main structure.",
            "",
            "Axial: the field-only peak benefits from removing the v001 arrows and heavy crescent strokes. The 2.0x source-separation-to-wavelength setting gave the cleanest internal field-only axial read among 2.0x, 2.5x, and 3.0x because it preserved the nested side crescent-like bands. The center reads more as a focal channel than a clean oval, and the far-side pressure points remain subtler than the radial trigons.",
            "",
            "Self-check: no external reviewers were available inside this automated render run. B's honest checklist rating is: radial passes the circle-like / crescent-like / wedge-trigon-like read; axial passes circle/oval and crescent/arc-like read, with trigon/point-like regions present but less forceful. This is enough for the requested final solo test, but it should pause here for Austin review packet curation rather than continuing solo iterations.",
            "",
            "## Cultural Boundary",
            "",
            "This is an internal mathematical visual study only. It is not Austin-approved. It does not claim Coast Salish correctness, reconstruct Coast Salish design, validate a cultural grammar, or carry cultural meaning. Austin review is required to determine which renderings resonate and which read as off.",
            "",
            "Renderer: `scripts/integrated_choreographer_v002_field_only.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render integrated choreographer v002 field-only packet.")
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

    selected = list(TARGETS if args.clip == "all" else [target_by_key(args.clip)])
    summaries: list[dict[str, object]] = []
    for target in selected:
        action = "Previewing" if args.preview else "Rendering"
        print(f"{action} {target.filename}", flush=True)
        summaries.append(render_clip(target, write_video=not args.preview))

    if args.clip == "all":
        spacing_test_sheet = make_axial_spacing_test_sheet()
        contact_sheet = make_contact_sheet()
        debug_sheet = make_debug_sheet()
        manifest = write_manifest(summaries, contact_sheet, debug_sheet, spacing_test_sheet)
        readme = write_readme(summaries)
        print(f"Wrote {spacing_test_sheet}", flush=True)
        print(f"Wrote {contact_sheet}", flush=True)
        print(f"Wrote {debug_sheet}", flush=True)
        print(f"Wrote {manifest}", flush=True)
        print(f"Wrote {readme}", flush=True)
    else:
        print(f"{'Previewed' if args.preview else 'Rendered'} {selected[0].filename}", flush=True)


if __name__ == "__main__":
    main()
