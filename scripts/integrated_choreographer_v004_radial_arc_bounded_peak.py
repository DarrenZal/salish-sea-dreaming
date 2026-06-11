#!/usr/bin/env python3
"""
Integrated choreographer v004, radial arc-bounded peak.

Internal mathematical/visual alignment study for Salish Sea Dreaming. This
version parks axial and linear targets, keeps the v003 radial source layout,
and resolves the peak as a dark-ground arc-bounded composition: one central
source region and six selected center-ring lens/crescent regions. The visible
forms derive from the same source positions and construction radii used by the
wave field.

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import cymatic_field_topology_v007 as base
import integrated_choreographer_v003_geometric_synthesis as v003


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v004_radial_arc_bounded_peak_2026-05-21"
)
V002_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v002_field_only_2026-05-21"
)
V003_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "integrated_choreographer_v003_geometric_synthesis_2026-05-21"
)

PEAK_DIR = OUT_DIR / "peak_stills"
PALETTE_DIR = OUT_DIR / "palette_tests"
DEBUG_DIR = OUT_DIR / "debug_stills"
COMPARISON_DIR = OUT_DIR / "comparison_stills"

W = base.W
H = base.H
FW = base.FW
FH = base.FH
FPS = base.FPS
DURATION_SECONDS = 12.0
N_FRAMES = int(FPS * DURATION_SECONDS)
PEAK_FRAME = int(6.4 * FPS)
PEAK_TIME_SECONDS = PEAK_FRAME / FPS
TAU = math.tau

BLACK = (0, 0, 0)
DEEP_GROUND = (0, 5, 7)
DARK_WATER = (3, 28, 32)
TEAL = (45, 151, 158)
MUTED_TEAL = (78, 126, 124)
CREAM = (239, 231, 194)
SOFT_CREAM = (219, 205, 159)
OCHRE = (222, 169, 72)
GOLD = (246, 196, 88)
CENTER_ACCENT = (238, 178, 74)
INCISE_DARK = (1, 10, 12)
INCISE_WARM = (165, 149, 98)
CONSTRUCTION = (147, 158, 139)
LABEL = (226, 234, 230)

SELECTED_PALETTE = "cream"
PRIMARY_PALETTES: dict[str, tuple[int, int, int]] = {
    "cream": CREAM,
    "ochre": OCHRE,
}

TARGET = replace(
    v003.TARGETS[0],
    key="radial_arc_bounded_peak",
    filename="radial_arc_bounded_peak_v004.mp4",
    title="radial_arc_bounded_peak",
    reference_notes=(
        "Radial-only v004 study derived from the v003 radial_sixfold source layout. "
        "Axial and linear targets are parked."
    ),
    tuning_notes=(
        "Dark-ground peak renderer. Full construction circles appear only during gather, "
        "then fade behind seven selected source-derived positive regions: one central "
        "source disc and six center-ring arc-bounded lens/crescent forms."
    ),
)
v003.BOUNDARY_CACHE[TARGET.key] = v003.full_boundary_mask(TARGET)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def coherence_at_time(time_seconds: float) -> float:
    return v003.coherence_at_time(time_seconds)


def layer_levels(time_seconds: float, coherence: float) -> dict[str, float]:
    reveal = smoothstep01((time_seconds - 3.0) / 2.0)
    dissolve = 1.0 - smoothstep01((time_seconds - 8.0) / 2.0)
    hold_gate = clamp01(reveal * dissolve)
    coherence_gate = smoothstep01((coherence - 0.62) / 0.38)
    selected = hold_gate * coherence_gate
    return {
        "wave_regions": clamp01(0.94 * (1.0 - 0.94 * selected)),
        "wave_lines": clamp01(0.55 - 0.30 * selected),
        "construction": clamp01(0.23 * reveal * (1.0 - coherence_gate) + 0.025 * selected),
        "selected_regions": clamp01(0.98 * selected),
        "outer_registration": clamp01(0.13 * selected),
        "hold_gate": hold_gate,
        "coherence_gate": coherence_gate,
    }


def blend_full_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    glow: float = 0.0,
) -> None:
    v003.blend_full_mask(frame, mask, rgb, alpha, glow=glow)


def blend_small_mask(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float) -> None:
    v003.blend_mask(frame, mask, rgb, alpha)


def render_dark_wave_field(
    field_norm: np.ndarray,
    target: v003.TargetSpec,
    *,
    region_alpha: float,
    line_alpha: float,
) -> np.ndarray:
    frame_small = np.zeros((FH, FW, 3), dtype=np.uint8)
    field_small = cv2.GaussianBlur(v003.shape_field(field_norm, target.field_gamma), (0, 0), 0.40)
    boundary = v003.boundary_mask_small(target) > 0

    mask = np.where(boundary, 255, 0).astype(np.uint8)
    pos = np.where((field_small > target.threshold) & boundary, 255, 0).astype(np.uint8)
    neg = np.where((field_small < -target.threshold) & boundary, 255, 0).astype(np.uint8)
    node = np.where((np.abs(field_small) <= target.node_epsilon) & boundary, 255, 0).astype(np.uint8)
    node = cv2.morphologyEx(node, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    region = cv2.bitwise_or(pos, neg)
    edge = cv2.morphologyEx(region, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_edge = cv2.morphologyEx(node, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    blend_small_mask(frame_small, mask, DARK_WATER, 0.42 * region_alpha)
    blend_small_mask(frame_small, neg, TEAL, 0.55 * region_alpha)
    blend_small_mask(frame_small, pos, SOFT_CREAM, 0.60 * region_alpha)
    blend_small_mask(frame_small, edge, INCISE_DARK, 0.24 * line_alpha)
    blend_small_mask(frame_small, node, INCISE_DARK, 0.54 * line_alpha)
    blend_small_mask(frame_small, node_edge, MUTED_TEAL, 0.18 * line_alpha)
    return cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)


def circle_mask(x: float, y: float, radius: float) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(mask, (round(x), round(y)), max(1, round(radius)), 255, -1, lineType=cv2.LINE_AA)
    return mask


def tapered_gap_mask(
    cx: float,
    cy: float,
    angle: float,
    inner_radius: float,
    outer_radius: float,
    inner_half_angle: float,
    outer_half_angle: float,
) -> np.ndarray:
    points = []
    for radius, theta in (
        (inner_radius, angle - inner_half_angle),
        (inner_radius, angle + inner_half_angle),
        (outer_radius, angle + outer_half_angle),
        (outer_radius, angle - outer_half_angle),
    ):
        points.append((round(cx + radius * math.cos(theta)), round(cy + radius * math.sin(theta))))
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(points, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    return mask


def bounded(mask: np.ndarray) -> np.ndarray:
    return v003.mask_intersection(mask, v003.boundary_mask_for(TARGET))


def build_peak_geometry(
    target: v003.TargetSpec,
    sources: list[base.WaveSource],
) -> dict[str, object]:
    circles = v003.active_circles(target, sources)
    center = v003.find_circle(circles, "radial_center")
    ring = v003.radial_ring_circles(circles, center)
    radius = target.wavelength

    # Slightly broader wavefront radii make adjacent lens cusps approach each
    # other, while the center gutter keeps the seven positive forms separate.
    construction_radius = radius
    lens_radius = radius * 1.000
    center_disc_radius = radius * 0.345
    center_gutter_radius = radius * 0.430
    outer_reference_radius = radius * 1.515

    center_mask = bounded(circle_mask(center.x, center.y, center_disc_radius))
    center_gutter = circle_mask(center.x, center.y, center_gutter_radius)
    center_wave = circle_mask(center.x, center.y, lens_radius)

    raw_crescent_masks: list[np.ndarray] = []
    crescent_ids: list[str] = []
    for idx, circle in enumerate(ring):
        ring_wave = circle_mask(circle.x, circle.y, lens_radius)
        lens = v003.mask_intersection(center_wave, ring_wave)
        lens = v003.mask_subtract(lens, center_gutter)
        lens = bounded(lens)
        lens = cv2.morphologyEx(lens, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        raw_crescent_masks.append(lens)
        crescent_ids.append(f"radial_arc_bounded_crescent_{idx:02d}")

    gap_masks: list[np.ndarray] = []
    outer_reference = circle_mask(center.x, center.y, outer_reference_radius)
    for idx, circle in enumerate(ring):
        nxt = ring[(idx + 1) % len(ring)]
        a0 = math.atan2(circle.y - center.y, circle.x - center.x)
        a1 = math.atan2(nxt.y - center.y, nxt.x - center.x)
        if a1 < a0:
            a1 += TAU
        gap_angle = (a0 + a1) * 0.5
        gap = tapered_gap_mask(
            center.x,
            center.y,
            gap_angle,
            radius * 0.455,
            lens_radius * 1.02,
            math.radians(5.4),
            math.radians(0.25),
        )
        gap = v003.mask_intersection(gap, center_wave, outer_reference)
        gap = bounded(gap)
        gap_masks.append(gap)

    gap_union = v003.mask_union(*gap_masks)
    crescent_masks = [
        cv2.morphologyEx(v003.mask_subtract(mask, gap_union), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        for mask in raw_crescent_masks
    ]

    return {
        "circles": circles,
        "center_circle": center,
        "ring_circles": ring,
        "center_mask": center_mask,
        "crescent_masks": crescent_masks,
        "crescent_ids": crescent_ids,
        "gap_masks": gap_masks,
        "construction_radius": construction_radius,
        "lens_radius": lens_radius,
        "center_disc_radius": center_disc_radius,
        "center_gutter_radius": center_gutter_radius,
        "outer_reference_radius": outer_reference_radius,
        "primary_positive_count": 1 + len(crescent_masks),
        "primary_source_circle_ids": [
            "radial_center_R1",
            *[f"{circle.source_id}_R1" for circle in ring],
        ],
    }


def draw_circle_outline(
    frame: np.ndarray,
    x: float,
    y: float,
    radius: float,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    thickness: int = 1,
) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    cv2.circle(overlay, (round(x), round(y)), max(1, round(radius)), rgb_to_bgr(rgb), thickness, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_reveal_scaffold(frame: np.ndarray, geometry: dict[str, object], alpha: float) -> None:
    if alpha <= 0.0:
        return
    for circle in geometry["circles"]:
        draw_circle_outline(frame, circle.x, circle.y, circle.radius, CONSTRUCTION, alpha, thickness=2)


def draw_outer_registration(frame: np.ndarray, geometry: dict[str, object], alpha: float) -> None:
    if alpha <= 0.0:
        return
    center = geometry["center_circle"]
    draw_circle_outline(
        frame,
        center.x,
        center.y,
        float(geometry["outer_reference_radius"]),
        INCISE_WARM,
        alpha,
        thickness=1,
    )


def draw_mask_outline(
    frame: np.ndarray,
    mask: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    thickness: int,
) -> None:
    v003.draw_mask_outline(frame, mask, rgb, alpha, thickness=thickness)


def draw_selected_regions(
    frame: np.ndarray,
    geometry: dict[str, object],
    *,
    alpha: float,
    primary_rgb: tuple[int, int, int],
) -> None:
    if alpha <= 0.0:
        return

    for mask in geometry["crescent_masks"]:
        blend_full_mask(frame, mask, primary_rgb, 0.96 * alpha, glow=0.005 * alpha)
    blend_full_mask(frame, geometry["center_mask"], CENTER_ACCENT, 1.00 * alpha, glow=0.020 * alpha)

    for mask in geometry["gap_masks"]:
        blend_full_mask(frame, mask, DEEP_GROUND, 0.86 * alpha)

    for mask in geometry["crescent_masks"]:
        draw_mask_outline(frame, mask, INCISE_DARK, 0.90 * alpha, thickness=3)
        draw_mask_outline(frame, mask, INCISE_WARM, 0.44 * alpha, thickness=1)
    draw_mask_outline(frame, geometry["center_mask"], INCISE_DARK, 0.92 * alpha, thickness=3)
    draw_mask_outline(frame, geometry["center_mask"], GOLD, 0.34 * alpha, thickness=1)


def draw_subtle_nodal_lines(
    frame: np.ndarray,
    field_norm: np.ndarray,
    target: v003.TargetSpec,
    *,
    alpha: float,
) -> None:
    if alpha <= 0.0:
        return
    field_small = cv2.GaussianBlur(v003.shape_field(field_norm, target.field_gamma), (0, 0), 0.34)
    boundary = v003.boundary_mask_small(target) > 0
    node = np.where((np.abs(field_small) <= target.node_epsilon) & boundary, 255, 0).astype(np.uint8)
    node = cv2.morphologyEx(node, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    edge = cv2.morphologyEx(node, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_full = cv2.resize(node, (W, H), interpolation=cv2.INTER_LINEAR)
    edge_full = cv2.resize(edge, (W, H), interpolation=cv2.INTER_LINEAR)
    blend_full_mask(frame, node_full, INCISE_DARK, 0.18 * alpha)
    blend_full_mask(frame, edge_full, MUTED_TEAL, 0.10 * alpha)


def render_frame(
    time_seconds: float,
    *,
    force_coherence: float | None = None,
    palette_name: str = SELECTED_PALETTE,
    labels: bool = False,
) -> tuple[np.ndarray, dict[str, object]]:
    coherence = coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = v003.target_sources_at(TARGET, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=TARGET.blur_sigma)
    levels = layer_levels(time_seconds, coherence)

    frame = render_dark_wave_field(
        field,
        TARGET,
        region_alpha=levels["wave_regions"],
        line_alpha=levels["wave_lines"],
    )
    geometry = build_peak_geometry(TARGET, sources)
    draw_subtle_nodal_lines(frame, field, TARGET, alpha=0.72 * levels["wave_lines"])
    draw_reveal_scaffold(frame, geometry, levels["construction"])
    draw_outer_registration(frame, geometry, levels["outer_registration"])
    draw_selected_regions(
        frame,
        geometry,
        alpha=levels["selected_regions"],
        primary_rgb=PRIMARY_PALETTES[palette_name],
    )
    if labels:
        base.draw_text(frame, f"radial arc-bounded peak v004  c={coherence:.2f}", (42, 58), LABEL, scale=0.58)
        base.draw_text(
            frame,
            "dark ground; 7 selected source-derived positive regions; scaffold nearly hidden at peak",
            (42, 88),
            LABEL,
            scale=0.38,
        )
    return frame, {
        "coherence": round(coherence, 4),
        "levels": {key: round(value, 4) for key, value in levels.items()},
        "palette": palette_name,
        "source_positions": [
            {
                "source_id": source.source_id,
                "x": round(source.x, 3),
                "y": round(source.y, 3),
                "wavelength": round(source.wavelength, 3),
            }
            for source in sources
        ],
        "geometry": {
            "primary_positive_count": geometry["primary_positive_count"],
            "crescent_count": len(geometry["crescent_masks"]),
            "gap_count": len(geometry["gap_masks"]),
            "construction_circle_count": len(geometry["circles"]),
            "construction_radius": round(float(geometry["construction_radius"]), 3),
            "lens_radius": round(float(geometry["lens_radius"]), 3),
            "center_disc_radius": round(float(geometry["center_disc_radius"]), 3),
            "center_gutter_radius": round(float(geometry["center_gutter_radius"]), 3),
            "outer_reference_radius": round(float(geometry["outer_reference_radius"]), 3),
            "primary_source_circle_ids": geometry["primary_source_circle_ids"],
        },
    }


def render_peak_still(palette_name: str, *, labels: bool = False) -> tuple[np.ndarray, dict[str, object]]:
    return render_frame(PEAK_TIME_SECONDS, force_coherence=1.0, palette_name=palette_name, labels=labels)


def render_full_construction_debug() -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    sources = v003.target_sources_at(TARGET, PEAK_TIME_SECONDS, 1.0)
    geometry = build_peak_geometry(TARGET, sources)
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    blend_full_mask(frame, v003.boundary_mask_for(TARGET), DARK_WATER, 0.34)
    draw_outer_registration(frame, geometry, 0.80)
    for circle in geometry["circles"]:
        draw_circle_outline(frame, circle.x, circle.y, circle.radius, CONSTRUCTION, 0.86, thickness=2)
        cv2.circle(frame, (round(circle.x), round(circle.y)), 4, rgb_to_bgr(GOLD), -1, lineType=cv2.LINE_AA)
        base.draw_text(frame, circle.circle_id, (round(circle.x) + 10, round(circle.y) - 10), LABEL, scale=0.30)
    for mask in geometry["gap_masks"]:
        blend_full_mask(frame, mask, MUTED_TEAL, 0.32)
        draw_mask_outline(frame, mask, MUTED_TEAL, 0.82, thickness=2)
    for mask in geometry["crescent_masks"]:
        blend_full_mask(frame, mask, CREAM, 0.42)
        draw_mask_outline(frame, mask, CREAM, 0.88, thickness=2)
    blend_full_mask(frame, geometry["center_mask"], CENTER_ACCENT, 0.72)
    draw_mask_outline(frame, geometry["center_mask"], GOLD, 0.9, thickness=2)
    base.draw_text(frame, "full construction geometry debug: source circles, selected regions, gap provenance", (42, 58), LABEL, scale=0.48)
    base.draw_text(frame, "debug only; the beauty peak suppresses the full scaffold", (42, 88), LABEL, scale=0.36)
    path = DEBUG_DIR / "radial_arc_bounded_peak_v004_full_construction_geometry_debug.png"
    cv2.imwrite(str(path), frame)
    return path


def read_or_blank(path: Path, label: str) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is not None:
        return img
    blank = np.zeros((H, W, 3), dtype=np.uint8)
    base.draw_text(blank, label, (60, 78), LABEL, scale=0.58)
    base.draw_text(blank, f"missing: {path}", (60, 116), LABEL, scale=0.34)
    return blank


def make_palette_tests() -> dict[str, str]:
    PALETTE_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for palette_name in ("cream", "ochre"):
        frame, _info = render_peak_still(palette_name, labels=False)
        path = PALETTE_DIR / f"radial_arc_bounded_peak_v004_palette_{palette_name}.png"
        cv2.imwrite(str(path), frame)
        outputs[palette_name] = str(path.relative_to(OUT_DIR))
    return outputs


def make_peak_still() -> tuple[Path, dict[str, object]]:
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    frame, info = render_peak_still(SELECTED_PALETTE, labels=False)
    path = PEAK_DIR / "radial_arc_bounded_peak_v004_peak.png"
    cv2.imwrite(str(path), frame)
    return path, info


def make_contact_comparison_sheet() -> Path:
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    v002_peak = V002_DIR / "peak_stills" / "radial_sixfold_field_only_v002_peak.png"
    v003_peak = V003_DIR / "peak_stills" / "radial_sixfold_geometric_synthesis_v003_peak.png"
    v004_peak = PEAK_DIR / "radial_arc_bounded_peak_v004_peak.png"
    panels = [
        cv2.resize(read_or_blank(v002_peak, "v002 radial field-only peak"), (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(read_or_blank(v003_peak, "v003 radial geometric synthesis peak"), (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(read_or_blank(v004_peak, "v004 radial arc-bounded peak"), (640, 360), interpolation=cv2.INTER_AREA),
    ]
    labels = [
        "v002 radial: field-only",
        "v003 radial: geometric synthesis",
        "v004 radial: dark-ground selected arcs",
    ]
    for panel, label in zip(panels, labels, strict=True):
        base.draw_text(panel, label, (22, 38), LABEL, scale=0.42)
    sheet = cv2.hconcat(panels)
    path = COMPARISON_DIR / "radial_arc_bounded_peak_v004_v002_v003_v004_comparison.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_contact_sheet() -> Path:
    peak = cv2.imread(str(PEAK_DIR / "radial_arc_bounded_peak_v004_peak.png"), cv2.IMREAD_COLOR)
    cream = cv2.imread(str(PALETTE_DIR / "radial_arc_bounded_peak_v004_palette_cream.png"), cv2.IMREAD_COLOR)
    ochre = cv2.imread(str(PALETTE_DIR / "radial_arc_bounded_peak_v004_palette_ochre.png"), cv2.IMREAD_COLOR)
    debug = cv2.imread(str(DEBUG_DIR / "radial_arc_bounded_peak_v004_full_construction_geometry_debug.png"), cv2.IMREAD_COLOR)
    panels = []
    for img, label in (
        (peak, "selected final peak"),
        (cream, "palette test: cream forms"),
        (ochre, "palette test: ochre forms"),
        (debug, "debug provenance"),
    ):
        panel = cv2.resize(img if img is not None else np.zeros((H, W, 3), dtype=np.uint8), (960, 540), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (28, 46), LABEL, scale=0.50)
        panels.append(panel)
    sheet = cv2.vconcat([cv2.hconcat(panels[:2]), cv2.hconcat(panels[2:])])
    path = OUT_DIR / "integrated_choreographer_v004_radial_arc_bounded_peak_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip() -> dict[str, object]:
    output_path = OUT_DIR / TARGET.filename
    writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
    peak_info: dict[str, object] | None = None
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = frame_idx / FPS
            frame, info = render_frame(time_seconds, palette_name=SELECTED_PALETTE)
            writer.write(frame)
            if frame_idx == PEAK_FRAME:
                peak_info = info
            if (frame_idx + 1) % FPS == 0:
                print(f"  {TARGET.filename} {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_peak_still(SELECTED_PALETTE)
    return {
        "filename": TARGET.filename,
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "peak_frame": PEAK_FRAME,
        "peak_time_seconds": round(PEAK_TIME_SECONDS, 4),
        "peak_info": peak_info,
    }


def write_manifest(
    clip_summary: dict[str, object],
    peak_path: Path,
    palette_paths: dict[str, str],
    debug_path: Path,
    comparison_path: Path,
    contact_path: Path,
) -> Path:
    manifest = {
        "project": "integrated_choreographer_v004_radial_arc_bounded_peak",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "renderer": "scripts/integrated_choreographer_v004_radial_arc_bounded_peak.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "parked": ["axial_eye", "linear_flow"],
        "base": "v003 radial_sixfold source-derived geometric synthesis",
        "selected_palette": SELECTED_PALETTE,
        "palette_choice": (
            "Cream/off-white primary forms were selected over ochre because they keep the six crescents readable "
            "against dark ground while allowing the central gold source region to carry the strongest accent."
        ),
        "beauty_layer_rule": {
            "dark_ground_peak": True,
            "filled_bounded_silhouette_at_peak": False,
            "full_construction_scaffold_at_peak": "nearly invisible; retained only as reveal scaffolding",
            "generic_primitive_glyphs": False,
            "primary_positive_forms_at_peak": 7,
            "primary_positive_forms": ["1 central source circle", "6 center-ring arc-bounded lens/crescent regions"],
            "negative_gap_rule": "six dark trigon-like gaps are left as negative spaces between adjacent crescent cusps and a faint outer registration arc",
        },
        "coherence_curve": {
            "parameter": "c",
            "range": [0.0, 1.0],
            "curve": "smoothstep gather/release",
            "timing_seconds": {
                "0.0-3.0": "loose drifting wave field",
                "3.0-5.0": "smoothstep gather; faint construction scaffold appears",
                "5.0-8.0": "c=1 hold; selected arc-bounded positive forms are primary",
                "8.0-10.0": "smoothstep release",
                "10.0-12.0": "return to drift",
            },
        },
        "target": {
            "key": TARGET.key,
            "filename": TARGET.filename,
            "source_spacing": TARGET.source_spacing,
            "wavelength": TARGET.wavelength,
            "frequency": TARGET.frequency,
            "decay": TARGET.decay,
            "threshold": TARGET.threshold,
            "node_epsilon": TARGET.node_epsilon,
            "boundary_type": TARGET.boundary_type,
            "boundary_axes": list(TARGET.boundary_axes),
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
                for source in TARGET.sources
            ],
        },
        "clip": clip_summary,
        "deliverables": {
            "mp4": TARGET.filename,
            "peak_still": str(peak_path.relative_to(OUT_DIR)),
            "palette_tests": palette_paths,
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "comparison_sheet": str(comparison_path.relative_to(OUT_DIR)),
            "debug_full_construction_geometry": str(debug_path.relative_to(OUT_DIR)),
            "readme": "README.md",
        },
    }
    path = OUT_DIR / "integrated_choreographer_v004_radial_arc_bounded_peak_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(clip_summary: dict[str, object]) -> Path:
    lines = [
        "# Integrated Choreographer v004 Radial Arc-Bounded Peak",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "v004 focuses only on the radial_sixfold layout. It keeps the v003 source-derived geometry but resolves the peak as a darker, simpler beauty render: one central source region plus six selected arc-bounded lens/crescent regions. Axial and linear targets are parked.",
        "",
        "Core design rule: the visible forms trace to the same source positions and construction radii as the wave field. The renderer does not add detached primitive icons, thick crescent stamps, or separate arrow/ray glyphs.",
        "",
        "## Timing",
        "",
        "- 0.0-3.0s: loose drifting wave field.",
        "- 3.0-5.0s: sources gather; faint construction circles appear as scaffold.",
        "- 5.0-8.0s: peak readable state; full scaffold is nearly invisible, selected arc-bounded regions carry the read.",
        "- 8.0-10.0s: selected regions dissolve.",
        "- 10.0-12.0s: return to drifting wave field.",
        "",
        "## Palette Test",
        "",
        "Two peak stills were produced: cream/off-white primary forms on dark and warm ochre/yellow primary forms on dark. The final MP4 uses the cream/off-white primary forms. The cream version keeps the six crescents distinct and lets the central gold source region become the strongest accent; the ochre version is warmer but flattens the hierarchy between center and ring.",
        "",
        "## Deliverables",
        "",
        "- `radial_arc_bounded_peak_v004.mp4`: 1920x1080, 24 fps, 12 seconds.",
        "- Peak still: `peak_stills/radial_arc_bounded_peak_v004_peak.png`.",
        "- Palette tests in `palette_tests/`.",
        "- Contact sheet: `integrated_choreographer_v004_radial_arc_bounded_peak_contact_sheet.png`.",
        "- v002/v003/v004 comparison: `comparison_stills/radial_arc_bounded_peak_v004_v002_v003_v004_comparison.png`.",
        "- Provenance debug still: `debug_stills/radial_arc_bounded_peak_v004_full_construction_geometry_debug.png`.",
        "- Manifest: `integrated_choreographer_v004_radial_arc_bounded_peak_manifest.json`.",
        "",
        "## Honest Verdict",
        "",
        "The radial peak is less diagrammatic than v003 because the full construction scaffold fades out and the cream bounded silhouette is removed. It is clearer than v002 for the seven intended positive forms: one central circle and six selected source-derived crescent/lens forms. The dark trigon-like gaps between adjacent crescents are present as negative pressure spaces, helped by a faint outer registration arc.",
        "",
        "Remaining limitation: the result is intentionally constructed and still reads as a mathematical alignment study. The negative gaps are readable, but their sharpness depends on the selected lens radius and outer registration arc; this packet should be reviewed as an internal visual test, not as cultural validation.",
        "",
        "## Peak Audit",
        "",
        f"- Primary positive forms at peak: {clip_summary['peak_info']['geometry']['primary_positive_count']} (1 center + 6 crescents).",
        f"- Construction circles at peak: {clip_summary['peak_info']['geometry']['construction_circle_count']} available for provenance, with beauty alpha {clip_summary['peak_info']['levels']['construction']}.",
        f"- Selected palette: {SELECTED_PALETTE}.",
        "",
        "## Cultural Boundary",
        "",
        "This is an internal mathematical visual study only. It is not Austin-approved. It does not claim Coast Salish correctness, reconstruct Coast Salish design, validate a cultural grammar, or carry cultural meaning. Austin review is required to determine which renderings resonate and which read as off.",
        "",
        "Renderer: `scripts/integrated_choreographer_v004_radial_arc_bounded_peak.py`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render integrated choreographer v004 radial arc-bounded peak.")
    parser.add_argument("--preview", action="store_true", help="Write still/debug artifacts without rendering the MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    PALETTE_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    print("Writing palette tests and peak stills", flush=True)
    palette_paths = make_palette_tests()
    peak_path, peak_info = make_peak_still()
    debug_path = render_full_construction_debug()
    comparison_path = make_contact_comparison_sheet()
    contact_path = make_contact_sheet()

    clip_summary: dict[str, object]
    if args.preview:
        clip_summary = {
            "filename": TARGET.filename,
            "mp4": TARGET.filename,
            "peak_frame": PEAK_FRAME,
            "peak_time_seconds": round(PEAK_TIME_SECONDS, 4),
            "peak_info": peak_info,
        }
    else:
        print(f"Rendering {TARGET.filename}", flush=True)
        clip_summary = render_clip()

    manifest = write_manifest(clip_summary, peak_path, palette_paths, debug_path, comparison_path, contact_path)
    readme = write_readme(clip_summary)
    print(f"Wrote {peak_path}", flush=True)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
