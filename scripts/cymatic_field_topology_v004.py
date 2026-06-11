#!/usr/bin/env python3.11
"""
Cymatic field topology v004.

Internal scalar-field / standing-wave topology probe for Salish Sea Dreaming
Phase 2. This lane keeps the scalar-field water/cymatics engine while correcting
the v003 failure mode: no generic primitive templates are pasted over the field.
v004 starts from raw field contours, wavefront arcs, and naturally emerging cusp
regions, then smooths/simplifies only when the cleaned primitive stays close to
the source geometry.

Status: INTERNAL ONLY. Not Austin-approved, not public-use guidance, and not a
cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "cymatic_field_topology_v004_2026-05-20"
)
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
HONESTY_DIR = OUT_DIR / "honesty_checks"

W = 1920
H = 1080
FIELD_SCALE = 0.5
FW = int(W * FIELD_SCALE)
FH = int(H * FIELD_SCALE)
SX = W / FW
SY = H / FH
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)
LEGIBILITY_FRAME = int(3.25 * FPS)
TAU = math.tau

BLACK = (0, 0, 0)
IVORY = (238, 242, 232)
SOFT_IVORY = (208, 224, 218)
PALE_BLUE = (136, 219, 238)
ICE_BLUE = (178, 232, 242)
TEAL = (70, 190, 198)
DEEP_TEAL = (19, 69, 79)
DIM_TEAL = (34, 95, 101)
MUTED_TEAL = (85, 164, 166)
GOLD = (246, 197, 92)
MUTED_GOLD = (213, 178, 112)
AMBER = (226, 121, 72)
MAGENTA = (217, 98, 146)
GREEN = (120, 218, 162)
LABEL = (226, 234, 230)

POS_RGB = (234, 228, 200)
NEG_RGB = (72, 185, 205)
NODE_RGB = (92, 229, 222)

DEBUG_CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    "circle_like": GOLD,
    "crescent_like": PALE_BLUE,
    "trigon_like": MAGENTA,
    "compound": DIM_TEAL,
}

BEAUTY_FILL_COLORS: dict[str, tuple[int, int, int]] = {
    "circle_like": IVORY,
    "crescent_like": PALE_BLUE,
    "trigon_like": MUTED_GOLD,
    "compound": DIM_TEAL,
}

BEAUTY_STROKE_COLORS: dict[str, tuple[int, int, int]] = {
    "circle_like": IVORY,
    "crescent_like": SOFT_IVORY,
    "trigon_like": MUTED_TEAL,
    "compound": DIM_TEAL,
}

CLASS_PRIORITY: dict[str, int] = {
    "trigon_like": 4,
    "crescent_like": 3,
    "circle_like": 2,
    "compound": 1,
}

HOLD_FRAMES = int(0.40 * FPS)
FADE_FRAMES = int(0.28 * FPS)


grid_x = (np.arange(FW, dtype=np.float32) + 0.5) * SX
grid_y = (np.arange(FH, dtype=np.float32) + 0.5) * SY
GRID_X, GRID_Y = np.meshgrid(grid_x, grid_y)
edge_distance = np.minimum.reduce([GRID_X, W - GRID_X, GRID_Y, H - GRID_Y])


def np_smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


EDGE_WINDOW = np_smoothstep(32.0, 180.0, edge_distance).astype(np.float32)


@dataclass(frozen=True)
class WaveSource:
    source_id: str
    x: float
    y: float
    amplitude: float
    wavelength: float
    frequency: float
    phase: float
    decay: float
    velocity: tuple[float, float]
    birth_time: float
    lifetime: float
    symmetry_order: int
    mode: str
    angular_alpha: float = 0.0


@dataclass(frozen=True)
class CellRecord:
    cell_id: str
    loop_key: str
    polarity: str
    topology_class: str
    area_px: float
    perimeter_px: float
    centroid_px: tuple[float, float]
    circularity: float
    hull_ratio: float
    ellipse_elongation: float
    corner_count: int
    curvature_lobe_count: int
    source_neighborhood_count: int
    source_ids: tuple[str, ...]
    confidence: float
    render_policy: str
    contour: np.ndarray


@dataclass(frozen=True)
class ExtractionResult:
    cells: list[CellRecord]
    threshold: float
    rejected_tiny: int
    rejected_edge: int
    raw_contours: int
    counts_by_class: dict[str, int]
    counts_by_polarity: dict[str, int]


@dataclass(frozen=True)
class FeatureRecord:
    feature_id: str
    feature_type: str
    primitive_class: str
    primitive_subtype: str
    raw_points: np.ndarray
    styled_points: np.ndarray
    closed: bool
    source_cell: CellRecord | None
    source_ids: tuple[str, ...]
    centroid_px: tuple[float, float]
    bounds_px: tuple[float, float, float, float]
    orientation_rad: float
    confidence: float
    strength: float
    metrics: dict[str, float]
    render_policy: str
    polarity: str


@dataclass(frozen=True)
class RenderCell:
    cell: CellRecord
    track_id: int
    age_frames: int
    seen_frames: int
    missing_frames: int
    strength: float


@dataclass
class CellTrack:
    track_id: int
    cell: CellRecord
    age_frames: int
    seen_frames: int
    missing_frames: int
    last_seen_frame: int


@dataclass(frozen=True)
class LoopSpec:
    key: str
    filename: str
    description: str
    source_builder: Callable[[float], list[WaveSource]]
    threshold_percentile: float
    min_area: float
    max_area: float
    max_cells: int
    node_epsilon: float
    blur_sigma: float
    compound_policy: str
    dual_threshold: bool = False
    low_threshold_percentile: float = 56.0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = clamp01((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def smootherstep(value: float) -> float:
    t = clamp01(value)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def phase_wave(phase: float, offset: float = 0.0) -> float:
    return 0.5 + 0.5 * math.sin(TAU * ((phase + offset) % 1.0))


def rgb_to_bgr(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)


def canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def draw_text(
    frame: np.ndarray,
    text: str,
    xy: tuple[int, int],
    rgb: tuple[int, int, int] = LABEL,
    *,
    scale: float = 0.44,
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
        blur = max(7, min(35, int(max(mask.shape) * 0.08) | 1))
        glow_mask = cv2.GaussianBlur(mask, (blur, blur), 0)
        crop += color * ((glow_mask.astype(np.float32) / 255.0) * glow)[..., None]
    crop += color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def full_mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    return (0, 0, mask.shape[1], mask.shape[0])


def scaled_contour(contour: np.ndarray) -> np.ndarray:
    pts = contour[:, 0, :].astype(np.float32).copy()
    pts[:, 0] *= SX
    pts[:, 1] *= SY
    return np.round(pts).astype(np.int32).reshape(-1, 1, 2)


def contour_bbox(contour: np.ndarray, pad: int = 24) -> tuple[int, int, int, int] | None:
    pts = contour[:, 0, :]
    x0 = max(0, int(pts[:, 0].min()) - pad)
    y0 = max(0, int(pts[:, 1].min()) - pad)
    x1 = min(W, int(pts[:, 0].max()) + pad + 1)
    y1 = min(H, int(pts[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def draw_contour_fill(
    frame: np.ndarray,
    contour: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    glow: float = 0.0,
) -> None:
    full = scaled_contour(contour)
    bbox = contour_bbox(full)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    local = full.copy()
    local[:, 0, 0] -= x0
    local[:, 0, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(mask, [local], 255, lineType=cv2.LINE_AA)
    add_mask(frame, mask, bbox, rgb, alpha, glow=glow)


def draw_contour_outline(
    frame: np.ndarray,
    contour: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 3,
    glow: float = 0.0,
) -> None:
    full = scaled_contour(contour)
    bbox = contour_bbox(full)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    local = full.copy()
    local[:, 0, 0] -= x0
    local[:, 0, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.polylines(mask, [local], True, 255, thickness, lineType=cv2.LINE_AA)
    add_mask(frame, mask, bbox, rgb, alpha, glow=glow)


def draw_polyline_alpha(
    frame: np.ndarray,
    points: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int,
    closed: bool = False,
) -> None:
    if alpha <= 0.0 or len(points) < 2:
        return
    rounded = np.round(points).astype(np.int32)
    pad = max(4, thickness * 4)
    x0 = max(0, int(rounded[:, 0].min()) - pad)
    y0 = max(0, int(rounded[:, 1].min()) - pad)
    x1 = min(W, int(rounded[:, 0].max()) + pad + 1)
    y1 = min(H, int(rounded[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    overlay = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.uint8)
    pts = rounded.copy()
    pts[:, 0] -= x0
    pts[:, 1] -= y0
    pts = pts.reshape(-1, 1, 2)
    cv2.polylines(
        overlay,
        [pts],
        closed,
        (rgb[2], rgb[1], rgb[0]),
        thickness,
        lineType=cv2.LINE_AA,
    )
    crop = frame[y0:y1, x0:x1]
    cv2.addWeighted(overlay, alpha, crop, 1.0, 0, dst=crop)


def split_flagged_segments(points: np.ndarray, flags: np.ndarray) -> list[np.ndarray]:
    flags = flags.astype(bool)
    n = len(points)
    if n < 3 or not np.any(flags):
        return []
    if bool(np.all(flags)):
        return [points]
    segments: list[np.ndarray] = []
    starts = [idx for idx in range(n) if flags[idx] and not flags[(idx - 1) % n]]
    for start in starts:
        seg: list[np.ndarray] = []
        idx = start
        while flags[idx]:
            seg.append(points[idx])
            idx = (idx + 1) % n
            if idx == start:
                break
        if len(seg) >= 3:
            segments.append(np.asarray(seg, dtype=np.float32))
    segments.sort(key=len, reverse=True)
    return segments


def radial_peak_indices(points: np.ndarray, centroid: tuple[float, float], count: int = 3) -> list[int]:
    if len(points) < 18:
        return []
    cx, cy = centroid
    radii = np.sqrt((points[:, 0] - cx) ** 2 + (points[:, 1] - cy) ** 2)
    win = max(5, min(31, (len(points) // 18) | 1))
    kernel = np.ones(win, dtype=np.float32) / win
    smooth = np.convolve(np.r_[radii[-win:], radii, radii[:win]], kernel, mode="same")[win:-win]
    candidates: list[int] = []
    floor = float(smooth.mean() + 0.08 * (smooth.max() - smooth.min()))
    for idx in range(len(points)):
        if smooth[idx] >= smooth[(idx - 1) % len(points)] and smooth[idx] > smooth[(idx + 1) % len(points)]:
            if smooth[idx] >= floor:
                candidates.append(idx)
    candidates.sort(key=lambda idx: float(smooth[idx]), reverse=True)
    selected: list[int] = []
    min_gap = max(4, len(points) // 7)
    for idx in candidates:
        if all(min(abs(idx - other), len(points) - abs(idx - other)) >= min_gap for other in selected):
            selected.append(idx)
        if len(selected) >= count:
            break
    return sorted(selected)


def temporal_levels(time_seconds: float) -> tuple[float, float]:
    if time_seconds < 1.5:
        field_alpha = 1.0
        cell_alpha = 0.12 * smoothstep(0.80, 1.50, time_seconds)
    elif time_seconds < 3.0:
        field_alpha = 1.0 - 0.70 * smoothstep(1.50, 3.00, time_seconds)
        cell_alpha = 0.12 + 0.88 * smoothstep(1.50, 3.00, time_seconds)
    elif time_seconds < 4.5:
        field_alpha = 0.30 - 0.20 * smoothstep(3.00, 3.25, time_seconds)
        cell_alpha = 1.0
    else:
        field_alpha = 0.10 + 0.90 * smoothstep(4.50, 6.00, time_seconds)
        cell_alpha = 1.0 - smoothstep(4.50, 6.00, time_seconds)
    return clamp01(field_alpha), clamp01(cell_alpha)


def draw_scalar_field_beauty(frame: np.ndarray, field_norm: np.ndarray, *, alpha: float) -> None:
    if alpha <= 0.0:
        return
    positive = np.clip(field_norm, 0.0, 1.0)
    negative = np.clip(-field_norm, 0.0, 1.0)
    amplitude = np.clip(np.abs(field_norm), 0.0, 1.0) ** 0.74
    pos_color = rgb_to_bgr((226, 222, 190))
    neg_color = rgb_to_bgr((80, 172, 186))
    base = frame.astype(np.float32)
    field_rgb_small = (
        positive[..., None] * pos_color
        + negative[..., None] * neg_color
    ) * amplitude[..., None]
    field_rgb = cv2.resize(field_rgb_small, (W, H), interpolation=cv2.INTER_CUBIC)
    base += field_rgb * (0.54 * alpha)
    fine = cv2.resize((np.abs(field_norm) <= 0.026).astype(np.uint8) * 255, (W, H), interpolation=cv2.INTER_LINEAR)
    frame[:, :, :] = np.clip(base, 0, 255).astype(np.uint8)
    add_mask(frame, fine, full_mask_bbox(fine), (120, 204, 204), 0.050 * alpha, glow=0.0)


def reference_point_for_cell(cell: CellRecord, sources: list[WaveSource]) -> tuple[float, float]:
    active_by_id = {source.source_id: source for source in sources}
    for source_id in cell.source_ids:
        source = active_by_id.get(source_id)
        if source is not None:
            return source.x, source.y
    if sources:
        cx, cy = cell.centroid_px
        nearest = min(sources, key=lambda source: (source.x - cx) ** 2 + (source.y - cy) ** 2)
        return nearest.x, nearest.y
    return cell.centroid_px


def draw_circle_language(frame: np.ndarray, cell: CellRecord, alpha: float) -> None:
    draw_contour_fill(frame, cell.contour, BEAUTY_FILL_COLORS["circle_like"], alpha=0.18 * alpha, glow=0.030 * alpha)
    draw_contour_outline(frame, cell.contour, IVORY, alpha=0.62 * alpha, thickness=4, glow=0.018 * alpha)
    draw_contour_outline(frame, cell.contour, MUTED_GOLD, alpha=0.28 * alpha, thickness=1)


def draw_crescent_language(frame: np.ndarray, cell: CellRecord, sources: list[WaveSource], alpha: float) -> None:
    points = scaled_contour(cell.contour)[:, 0, :].astype(np.float32)
    if len(points) < 8:
        draw_contour_outline(frame, cell.contour, PALE_BLUE, alpha=0.42 * alpha, thickness=3)
        return
    ref_x, ref_y = reference_point_for_cell(cell, sources)
    dist = np.sqrt((points[:, 0] - ref_x) ** 2 + (points[:, 1] - ref_y) ** 2)
    outer_flags = dist >= float(np.percentile(dist, 54.0))
    inner_flags = ~outer_flags
    draw_contour_fill(frame, cell.contour, BEAUTY_FILL_COLORS["crescent_like"], alpha=0.070 * alpha, glow=0.018 * alpha)
    draw_contour_outline(frame, cell.contour, MUTED_TEAL, alpha=0.13 * alpha, thickness=2)
    for segment in split_flagged_segments(points, outer_flags)[:2]:
        draw_polyline_alpha(frame, segment, SOFT_IVORY, alpha=0.64 * alpha, thickness=5)
    for segment in split_flagged_segments(points, inner_flags)[:2]:
        draw_polyline_alpha(frame, segment, PALE_BLUE, alpha=0.30 * alpha, thickness=2)


def draw_trigon_language(frame: np.ndarray, cell: CellRecord, alpha: float) -> None:
    points = scaled_contour(cell.contour)[:, 0, :].astype(np.float32)
    draw_contour_fill(frame, cell.contour, BEAUTY_FILL_COLORS["trigon_like"], alpha=0.085 * alpha, glow=0.020 * alpha)
    draw_contour_outline(frame, cell.contour, MUTED_TEAL, alpha=0.32 * alpha, thickness=3)
    if len(points) < 18:
        draw_contour_outline(frame, cell.contour, SOFT_IVORY, alpha=0.34 * alpha, thickness=2)
        return
    peaks = radial_peak_indices(points, cell.centroid_px, count=3)
    if not peaks:
        draw_contour_outline(frame, cell.contour, SOFT_IVORY, alpha=0.28 * alpha, thickness=2)
        return
    n = len(points)
    window = max(5, min(20, n // 18))
    for peak in peaks:
        idxs = [(peak + offset) % n for offset in range(-window, window + 1)]
        arc = points[idxs]
        draw_polyline_alpha(frame, arc, MUTED_GOLD, alpha=0.72 * alpha, thickness=6)
        draw_polyline_alpha(frame, arc, IVORY, alpha=0.24 * alpha, thickness=2)


def draw_compound_language(frame: np.ndarray, cell: CellRecord, alpha: float) -> None:
    draw_contour_outline(frame, cell.contour, DIM_TEAL, alpha=0.090 * alpha, thickness=2)
    draw_contour_fill(frame, cell.contour, DIM_TEAL, alpha=0.018 * alpha)


def draw_source_points(
    frame: np.ndarray,
    sources: list[WaveSource],
    time_seconds: float,
    *,
    labels: bool,
    alpha: float = 0.75,
) -> None:
    overlay = np.zeros_like(frame)
    for idx, source in enumerate(sources):
        env = source_envelope(source, time_seconds)
        if source.mode == "impact" and env <= 0.01:
            continue
        x, y = round(source.x), round(source.y)
        radius = 8 if source.mode != "impact" else 5 + round(9 * env)
        color = GOLD if source.mode != "impact" else ICE_BLUE
        cv2.circle(overlay, (x, y), radius, (color[2], color[1], color[0]), 1, lineType=cv2.LINE_AA)
        cv2.circle(overlay, (x, y), 2, (color[2], color[1], color[0]), -1, lineType=cv2.LINE_AA)
        if labels:
            draw_text(overlay, source.source_id, (x + 10, y - 10), color, scale=0.33)
        if source.mode == "impact":
            cv2.circle(
                overlay,
                (x, y),
                max(12, round(source.wavelength * 0.52 * env)),
                (PALE_BLUE[2], PALE_BLUE[1], PALE_BLUE[0]),
                1,
                lineType=cv2.LINE_AA,
            )
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


class H264Writer:
    def __init__(self, path: Path, *, fps: int, size: tuple[int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = size
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
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
            "-preset",
            "veryfast",
            str(path),
        ]
        self.path = path
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        if frame.shape != (H, W, 3):
            raise ValueError(f"unexpected frame shape {frame.shape}")
        self.proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        stderr = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with code {code}\n{stderr[-4000:]}")


def continuous_envelope(source: WaveSource, _time_seconds: float) -> float:
    if source.lifetime >= DURATION_SECONDS:
        return 1.0
    return 1.0


def impact_envelope(source: WaveSource, time_seconds: float) -> float:
    age = (time_seconds - source.birth_time) % DURATION_SECONDS
    if age > source.lifetime:
        return 0.0
    attack = min(0.18, source.lifetime * 0.16)
    attack_level = smoothstep(0.0, attack, age)
    decay_level = max(0.0, 1.0 - age / source.lifetime) ** 1.45
    return attack_level * decay_level


def source_envelope(source: WaveSource, time_seconds: float) -> float:
    if source.mode == "impact":
        return impact_envelope(source, time_seconds)
    return continuous_envelope(source, time_seconds)


def evaluate_field(sources: list[WaveSource], time_seconds: float, blur_sigma: float) -> np.ndarray:
    field = np.zeros((FH, FW), dtype=np.float32)
    for source in sources:
        env = source_envelope(source, time_seconds)
        if env <= 0.0001:
            continue
        dx = GRID_X - source.x
        dy = GRID_Y - source.y
        distance = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
        omega = TAU * source.frequency
        phase = TAU * distance / source.wavelength - omega * time_seconds + source.phase
        decay = np.exp(-distance / max(1.0, source.decay), dtype=np.float32)
        wave = np.cos(phase, dtype=np.float32) * decay
        if source.mode == "sixfold_radial":
            theta = np.arctan2(dy, dx).astype(np.float32)
            modulation = (
                1.0
                + float(source.angular_alpha)
                * np.cos(float(source.symmetry_order) * theta, dtype=np.float32)
            )
            wave *= modulation
        field += (source.amplitude * env) * wave

    field *= EDGE_WINDOW
    if blur_sigma > 0:
        field = cv2.GaussianBlur(field, (0, 0), blur_sigma)
    max_abs = float(np.percentile(np.abs(field), 99.35))
    if max_abs < 1e-5:
        return field
    norm = np.clip(field / max_abs, -1.0, 1.0).astype(np.float32)
    norm = cv2.GaussianBlur(norm, (0, 0), max(0.25, blur_sigma * 0.48))
    return np.clip(norm, -1.0, 1.0).astype(np.float32)


def contour_lobe_count(contour: np.ndarray, centroid: tuple[float, float]) -> int:
    pts = contour[:, 0, :].astype(np.float32)
    if len(pts) < 28:
        return 0
    cx, cy = centroid[0] / SX, centroid[1] / SY
    radius = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    if float(radius.max() - radius.min()) < 2.0:
        return 0
    win = max(5, min(21, (len(radius) // 18) | 1))
    kernel = np.ones(win, dtype=np.float32) / win
    smooth = np.convolve(np.r_[radius[-win:], radius, radius[:win]], kernel, mode="same")[win:-win]
    threshold = float(smooth.mean() + 0.10 * (smooth.max() - smooth.min()))
    peaks: list[int] = []
    for idx in range(len(smooth)):
        prev_v = smooth[(idx - 1) % len(smooth)]
        next_v = smooth[(idx + 1) % len(smooth)]
        if smooth[idx] > prev_v and smooth[idx] >= next_v and smooth[idx] > threshold:
            if not peaks or idx - peaks[-1] > len(smooth) * 0.055:
                peaks.append(idx)
    if len(peaks) > 1 and peaks[0] + len(smooth) - peaks[-1] < len(smooth) * 0.055:
        peaks.pop()
    return min(9, len(peaks))


def source_attribution(
    centroid: tuple[float, float],
    sources: list[WaveSource],
    time_seconds: float,
) -> tuple[tuple[str, ...], int]:
    contributions: list[tuple[float, str, float]] = []
    for source in sources:
        env = source_envelope(source, time_seconds)
        if env <= 0.01:
            continue
        d = math.hypot(centroid[0] - source.x, centroid[1] - source.y)
        phase = TAU * d / source.wavelength - TAU * source.frequency * time_seconds + source.phase
        contribution = abs(source.amplitude * env * math.cos(phase) * math.exp(-d / max(1.0, source.decay)))
        contributions.append((contribution, source.source_id, d / max(1.0, source.wavelength)))
    if not contributions:
        return tuple(), 0
    contributions.sort(reverse=True)
    max_contrib = contributions[0][0]
    source_ids = tuple(item[1] for item in contributions[:3] if item[0] >= max_contrib * 0.28)
    source_neighborhood_count = sum(1 for item in contributions if item[2] <= 1.35)
    return source_ids, source_neighborhood_count


def classify_cell(
    contour: np.ndarray,
    loop_key: str,
    polarity: str,
    area: float,
    perimeter: float,
    centroid: tuple[float, float],
    sources: list[WaveSource],
    time_seconds: float,
) -> tuple[str, float, dict[str, float | int | tuple[str, ...]]]:
    circularity = clamp01((4.0 * math.pi * area) / max(1e-6, perimeter * perimeter))
    hull = cv2.convexHull(contour)
    hull_area = max(1e-6, float(cv2.contourArea(hull)))
    hull_ratio = clamp01(area / hull_area)
    if len(contour) >= 5:
        ellipse = cv2.fitEllipse(contour)
        axes = ellipse[1]
        short_axis = max(1e-6, min(axes))
        long_axis = max(axes)
        elongation = float(long_axis / short_axis)
    else:
        elongation = 9.0
    approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
    corner_count = int(len(approx))
    lobe_count = contour_lobe_count(contour, centroid)
    source_ids, source_neighborhood_count = source_attribution(centroid, sources, time_seconds)
    nearest_active_source_distance = min(
        (
            math.hypot(centroid[0] - source.x, centroid[1] - source.y)
            for source in sources
            if source_envelope(source, time_seconds) > 0.05 and source.mode == "radial_continuous"
        ),
        default=999999.0,
    )

    strong_three_lobed = (
        3 <= lobe_count <= 4
        and 4 <= corner_count <= 9
        and elongation < 2.20
        and circularity < 0.92
        and hull_ratio > 0.72
    )
    source_three_corner = (
        source_neighborhood_count >= 3
        and 3 <= lobe_count <= 4
        and 4 <= corner_count <= 9
        and hull_ratio > 0.62
        and elongation < 2.35
        and circularity < 0.88
    )
    source_origin_circle = (
        nearest_active_source_distance <= 92.0
        and circularity > 0.70
        and hull_ratio > 0.84
        and elongation < 1.65
    )
    compact = (
        circularity > 0.60
        and hull_ratio > 0.80
        and elongation < 1.58
        and not strong_three_lobed
    )
    long_lens = elongation >= 1.82 or (hull_ratio < 0.73 and corner_count <= 8)
    three_corner = strong_three_lobed or source_three_corner

    if source_origin_circle:
        topology_class = "circle_like"
        confidence = 0.60 + 0.28 * circularity + 0.12 * hull_ratio
    elif three_corner:
        topology_class = "trigon_like"
        confidence = 0.58 + 0.10 * min(lobe_count, 4) + 0.10 * (1.0 - min(1.0, abs(elongation - 1.45) / 1.8))
    elif compact:
        topology_class = "circle_like"
        confidence = 0.50 + 0.36 * circularity + 0.14 * hull_ratio
    elif long_lens or source_neighborhood_count == 2:
        topology_class = "crescent_like"
        confidence = 0.52 + 0.10 * min(elongation, 3.2) / 3.2 + 0.14 * (1.0 - hull_ratio)
    elif circularity > 0.48 and elongation < 2.0:
        topology_class = "circle_like"
        confidence = 0.54
    else:
        topology_class = "compound"
        confidence = 0.32 + 0.04 * min(lobe_count, 5)

    features: dict[str, float | int | tuple[str, ...]] = {
        "circularity": float(circularity),
        "hull_ratio": float(hull_ratio),
        "ellipse_elongation": float(elongation),
        "corner_count": corner_count,
        "curvature_lobe_count": int(lobe_count),
        "source_neighborhood_count": int(source_neighborhood_count),
        "source_ids": source_ids,
    }
    return topology_class, clamp01(confidence), features


def clean_threshold_mask(mask: np.ndarray) -> np.ndarray:
    small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, small, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, medium, iterations=1)
    return mask


CLASS_TARGETS_BY_LOOP: dict[str, dict[str, int]] = {
    "seed_sun_trigon_reveal": {
        "circle_like": 5,
        "crescent_like": 7,
        "trigon_like": 20,
        "compound": 1,
    },
    "two_source_interference_primitives": {
        "circle_like": 5,
        "crescent_like": 18,
        "trigon_like": 8,
        "compound": 1,
    },
    "raindrops_on_water_primitives": {
        "circle_like": 9,
        "crescent_like": 12,
        "trigon_like": 9,
        "compound": 1,
    },
    "dual_threshold_recursive_primitives": {
        "circle_like": 5,
        "crescent_like": 12,
        "trigon_like": 14,
        "compound": 2,
    },
}


def cell_selection_score(cell: CellRecord, spec: LoopSpec) -> float:
    area = cell.area_px
    class_bonus = {
        "circle_like": 0.28,
        "crescent_like": 0.34,
        "trigon_like": 0.40,
        "compound": -0.18,
    }.get(cell.topology_class, 0.0)
    if spec.key == "seed_sun_trigon_reveal" and cell.topology_class == "trigon_like":
        class_bonus += 0.25
    if spec.key == "two_source_interference_primitives" and cell.topology_class == "crescent_like":
        class_bonus += 0.24
    if spec.key == "raindrops_on_water_primitives" and area > 22000:
        class_bonus += 0.12
    area_preference = 1.0 - min(1.0, abs(math.log(max(area, 1.0) / 9000.0)) / 2.4)
    size_floor_bonus = 0.16 if area >= 2200 else -0.25
    return (
        class_bonus
        + 0.54 * cell.confidence
        + 0.18 * area_preference
        + size_floor_bonus
        + 0.04 * min(cell.curvature_lobe_count, 4)
    )


def select_balanced_cells(cells: list[CellRecord], spec: LoopSpec, cap: int) -> list[CellRecord]:
    targets = CLASS_TARGETS_BY_LOOP.get(spec.key, {})
    grouped: dict[str, list[CellRecord]] = {}
    for cell in cells:
        grouped.setdefault(cell.topology_class, []).append(cell)
    for group in grouped.values():
        group.sort(key=lambda cell: cell_selection_score(cell, spec), reverse=True)

    selected: list[CellRecord] = []
    selected_ids: set[str] = set()
    for class_name in ("circle_like", "crescent_like", "trigon_like", "compound"):
        limit = targets.get(class_name, max(1, cap // 4))
        for cell in grouped.get(class_name, [])[:limit]:
            if len(selected) >= cap:
                break
            selected.append(cell)
            selected_ids.add(cell.cell_id)
        if len(selected) >= cap:
            break

    remaining = [cell for cell in cells if cell.cell_id not in selected_ids]
    remaining.sort(key=lambda cell: cell_selection_score(cell, spec), reverse=True)
    for cell in remaining:
        if len(selected) >= cap:
            break
        selected.append(cell)
        selected_ids.add(cell.cell_id)

    selected.sort(
        key=lambda cell: (
            CLASS_PRIORITY.get(cell.topology_class, 0),
            cell_selection_score(cell, spec),
            min(cell.area_px, 36000.0),
        ),
        reverse=True,
    )
    return selected[:cap]


def extract_cells(
    field_norm: np.ndarray,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    *,
    threshold_percentile: float | None = None,
    max_cells: int | None = None,
) -> ExtractionResult:
    percentile = threshold_percentile if threshold_percentile is not None else spec.threshold_percentile
    threshold = float(np.percentile(np.abs(field_norm), percentile))
    threshold = clamp(threshold, 0.22, 0.82)
    min_area = spec.min_area
    max_area = spec.max_area
    cells: list[CellRecord] = []
    rejected_tiny = 0
    rejected_edge = 0
    raw_contours = 0

    for polarity, mask in (
        ("positive", (field_norm > threshold).astype(np.uint8) * 255),
        ("negative", (field_norm < -threshold).astype(np.uint8) * 255),
    ):
        mask = clean_threshold_mask(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        raw_contours += len(contours)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < min_area:
                rejected_tiny += 1
                continue
            if area > max_area:
                rejected_edge += 1
                continue
            x, y, w, h = cv2.boundingRect(contour)
            touches_edge = x <= 1 or y <= 1 or x + w >= FW - 2 or y + h >= FH - 2
            if touches_edge and area > max(min_area * 2.5, 680.0):
                rejected_edge += 1
                continue
            perimeter = float(cv2.arcLength(contour, True))
            if perimeter <= 1.0:
                rejected_tiny += 1
                continue
            moments = cv2.moments(contour)
            if abs(moments["m00"]) < 1e-6:
                rejected_tiny += 1
                continue
            centroid_field = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
            centroid = (centroid_field[0] * SX, centroid_field[1] * SY)
            topology_class, confidence, features = classify_cell(
                contour,
                spec.key,
                polarity,
                area,
                perimeter,
                centroid,
                sources,
                time_seconds,
            )
            render_policy = "candidate"
            if topology_class == "compound":
                render_policy = "faint" if spec.compound_policy == "faint" else "suppress"
            cell = CellRecord(
                cell_id=f"{spec.key}_{polarity[:3]}_{len(cells):03d}",
                loop_key=spec.key,
                polarity=polarity,
                topology_class=topology_class,
                area_px=area * SX * SY,
                perimeter_px=perimeter * ((SX + SY) * 0.5),
                centroid_px=(float(centroid[0]), float(centroid[1])),
                circularity=float(features["circularity"]),
                hull_ratio=float(features["hull_ratio"]),
                ellipse_elongation=float(features["ellipse_elongation"]),
                corner_count=int(features["corner_count"]),
                curvature_lobe_count=int(features["curvature_lobe_count"]),
                source_neighborhood_count=int(features["source_neighborhood_count"]),
                source_ids=tuple(features["source_ids"]),
                confidence=confidence,
                render_policy=render_policy,
                contour=contour,
            )
            cells.append(cell)

    cap = max_cells or spec.max_cells
    cells = select_balanced_cells(cells, spec, cap)
    counts_by_class = dict(Counter(cell.topology_class for cell in cells))
    counts_by_polarity = dict(Counter(cell.polarity for cell in cells))
    return ExtractionResult(
        cells=cells,
        threshold=threshold,
        rejected_tiny=rejected_tiny,
        rejected_edge=rejected_edge,
        raw_contours=raw_contours,
        counts_by_class=counts_by_class,
        counts_by_polarity=counts_by_polarity,
    )


class CellTracker:
    def __init__(self, *, hold_frames: int = HOLD_FRAMES, fade_frames: int = FADE_FRAMES) -> None:
        self.hold_frames = hold_frames
        self.fade_frames = fade_frames
        self.max_missing_frames = hold_frames + fade_frames
        self.next_track_id = 1
        self.tracks: list[CellTrack] = []

    def _match_score(self, track: CellTrack, cell: CellRecord) -> float | None:
        if track.cell.topology_class != cell.topology_class:
            return None
        dx = track.cell.centroid_px[0] - cell.centroid_px[0]
        dy = track.cell.centroid_px[1] - cell.centroid_px[1]
        dist = math.hypot(dx, dy)
        distance_limit = 82.0
        if cell.topology_class == "crescent_like":
            distance_limit = 112.0
        elif cell.topology_class == "trigon_like":
            distance_limit = 104.0
        elif cell.topology_class == "compound":
            distance_limit = 70.0
        if dist > distance_limit:
            return None
        area_ratio = max(track.cell.area_px, cell.area_px) / max(1.0, min(track.cell.area_px, cell.area_px))
        if area_ratio > 2.35:
            return None
        return (dist / distance_limit) + 0.38 * abs(math.log(area_ratio)) + 0.045 * track.missing_frames

    def update(self, cells: list[CellRecord], frame_index: int, *, cap: int) -> list[RenderCell]:
        matched_tracks: set[int] = set()
        matched_cells: set[int] = set()
        for cell_index, cell in enumerate(cells):
            best_track_index: int | None = None
            best_score = float("inf")
            for track_index, track in enumerate(self.tracks):
                if track_index in matched_tracks:
                    continue
                score = self._match_score(track, cell)
                if score is not None and score < best_score:
                    best_score = score
                    best_track_index = track_index
            if best_track_index is None:
                continue
            track = self.tracks[best_track_index]
            track.cell = cell
            track.age_frames += 1
            track.seen_frames += 1
            track.missing_frames = 0
            track.last_seen_frame = frame_index
            matched_tracks.add(best_track_index)
            matched_cells.add(cell_index)

        for cell_index, cell in enumerate(cells):
            if cell_index in matched_cells:
                continue
            self.tracks.append(
                CellTrack(
                    track_id=self.next_track_id,
                    cell=cell,
                    age_frames=1,
                    seen_frames=1,
                    missing_frames=0,
                    last_seen_frame=frame_index,
                )
            )
            self.next_track_id += 1

        for track_index, track in enumerate(self.tracks):
            if track_index in matched_tracks:
                continue
            if track.last_seen_frame != frame_index:
                track.age_frames += 1
                track.missing_frames += 1

        self.tracks = [track for track in self.tracks if track.missing_frames <= self.max_missing_frames]
        render_cells: list[RenderCell] = []
        for track in self.tracks:
            born_strength = 0.40 + 0.60 * smoothstep(1.0, 3.0, float(track.seen_frames))
            persist_strength = 0.74 + 0.26 * smoothstep(3.0, float(self.hold_frames), float(track.seen_frames))
            if track.missing_frames <= self.hold_frames:
                missing_strength = 1.0
            else:
                missing_strength = 1.0 - smoothstep(
                    float(self.hold_frames),
                    float(self.max_missing_frames),
                    float(track.missing_frames),
                )
            strength = clamp01(born_strength * persist_strength * missing_strength)
            render_cells.append(
                RenderCell(
                    cell=track.cell,
                    track_id=track.track_id,
                    age_frames=track.age_frames,
                    seen_frames=track.seen_frames,
                    missing_frames=track.missing_frames,
                    strength=strength,
                )
            )
        render_cells.sort(
            key=lambda rendered: (
                CLASS_PRIORITY.get(rendered.cell.topology_class, 0),
                rendered.strength,
                rendered.cell.confidence,
                min(rendered.cell.area_px, 36000.0),
            ),
            reverse=True,
        )
        return render_cells[:cap]


def draw_nodal_band(frame: np.ndarray, field_norm: np.ndarray, node_epsilon: float, *, alpha: float) -> None:
    node_mask = (np.abs(field_norm) <= node_epsilon).astype(np.uint8) * 255
    node_mask = cv2.morphologyEx(node_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_full = cv2.resize(node_mask, (W, H), interpolation=cv2.INTER_LINEAR)
    add_mask(frame, node_full, full_mask_bbox(node_full), NODE_RGB, alpha, glow=0.0)


def render_beauty(
    field_norm: np.ndarray,
    cells: list[RenderCell],
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    *,
    low_cells: list[CellRecord] | None = None,
) -> np.ndarray:
    frame = canvas()
    field_alpha, cell_alpha = temporal_levels(time_seconds)
    draw_scalar_field_beauty(frame, field_norm, alpha=field_alpha)
    draw_nodal_band(
        frame,
        field_norm,
        spec.node_epsilon,
        alpha=(0.070 if spec.key != "dual_threshold_recursive_primitives" else 0.090) * field_alpha,
    )

    if low_cells:
        for cell in low_cells:
            if cell.render_policy == "suppress":
                continue
            draw_contour_outline(
                frame,
                cell.contour,
                DIM_TEAL,
                alpha=(0.025 + 0.045 * cell.confidence) * cell_alpha,
                thickness=1,
            )

    ordered_cells = sorted(
        cells,
        key=lambda rendered: (
            CLASS_PRIORITY.get(rendered.cell.topology_class, 0),
            rendered.cell.area_px,
        ),
    )
    for rendered in ordered_cells:
        cell = rendered.cell
        if cell.render_policy == "suppress":
            continue
        polarity_scale = 1.0 if cell.polarity == "positive" else 0.82
        confidence_scale = 0.72 + 0.28 * cell.confidence
        alpha = cell_alpha * rendered.strength * polarity_scale * confidence_scale
        if alpha <= 0.004:
            continue
        if cell.topology_class == "circle_like":
            draw_circle_language(frame, cell, alpha)
        elif cell.topology_class == "crescent_like":
            draw_crescent_language(frame, cell, sources, alpha)
        elif cell.topology_class == "trigon_like":
            draw_trigon_language(frame, cell, alpha)
        else:
            draw_compound_language(frame, cell, alpha)

    return frame


def grayscale_layer(field_norm: np.ndarray, title: str) -> np.ndarray:
    gray = np.clip((field_norm * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    frame = cv2.cvtColor(cv2.resize(gray, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_GRAY2BGR)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, "scalar field grayscale: black=-, mid=0, white=+", (42, 84), LABEL, scale=0.38)
    return frame


def nodal_layer(field_norm: np.ndarray, spec: LoopSpec, title: str) -> np.ndarray:
    frame = canvas()
    draw_nodal_band(frame, field_norm, spec.node_epsilon, alpha=0.85)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, f"nodal band abs(F)<= {spec.node_epsilon:.3f}", (42, 84), NODE_RGB, scale=0.38)
    return frame


def regions_layer(field_norm: np.ndarray, threshold: float, spec: LoopSpec, title: str) -> np.ndarray:
    frame = canvas()
    pos = (field_norm > threshold).astype(np.uint8) * 255
    neg = (field_norm < -threshold).astype(np.uint8) * 255
    node = (np.abs(field_norm) <= spec.node_epsilon).astype(np.uint8) * 255
    pos_full = cv2.resize(clean_threshold_mask(pos), (W, H), interpolation=cv2.INTER_LINEAR)
    neg_full = cv2.resize(clean_threshold_mask(neg), (W, H), interpolation=cv2.INTER_LINEAR)
    node_full = cv2.resize(node, (W, H), interpolation=cv2.INTER_LINEAR)
    add_mask(frame, pos_full, full_mask_bbox(pos_full), POS_RGB, 0.74, glow=0.02)
    add_mask(frame, neg_full, full_mask_bbox(neg_full), NEG_RGB, 0.66, glow=0.02)
    add_mask(frame, node_full, full_mask_bbox(node_full), NODE_RGB, 0.55)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, f"positive/negative regions at threshold={threshold:.3f}", (42, 84), LABEL, scale=0.38)
    return frame


def draw_class_key(frame: np.ndarray, x: int = 44, y: int = 92) -> None:
    rows = [
        ("circle_like", DEBUG_CLASS_COLORS["circle_like"]),
        ("crescent_like", DEBUG_CLASS_COLORS["crescent_like"]),
        ("trigon_like", DEBUG_CLASS_COLORS["trigon_like"]),
        ("compound/faint", DEBUG_CLASS_COLORS["compound"]),
    ]
    for idx, (label, rgb) in enumerate(rows):
        yy = y + idx * 26
        cv2.rectangle(frame, (x, yy - 14), (x + 18, yy + 4), (rgb[2], rgb[1], rgb[0]), -1, lineType=cv2.LINE_AA)
        draw_text(frame, label, (x + 28, yy + 2), LABEL, scale=0.36)


def classes_layer(cells: list[CellRecord], title: str) -> np.ndarray:
    frame = canvas()
    for cell in cells:
        color = DEBUG_CLASS_COLORS.get(cell.topology_class, DIM_TEAL)
        alpha = 0.78 if cell.topology_class != "compound" else 0.38
        draw_contour_fill(frame, cell.contour, color, alpha=alpha, glow=0.015)
        draw_contour_outline(frame, cell.contour, PALE_BLUE, alpha=0.20, thickness=2)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, "cell-class colors from connected region morphology", (42, 84), LABEL, scale=0.38)
    draw_class_key(frame)
    return frame


def source_layer(field_norm: np.ndarray, sources: list[WaveSource], time_seconds: float, title: str) -> np.ndarray:
    gray = np.clip(np.abs(field_norm) * 175.0, 0, 175).astype(np.uint8)
    frame = cv2.cvtColor(cv2.resize(gray, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_GRAY2BGR)
    draw_source_points(frame, sources, time_seconds, labels=True, alpha=0.95)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, "source points over abs(field); sources are debug evidence only", (42, 84), LABEL, scale=0.38)
    return frame


def source_to_json(source: WaveSource) -> dict[str, object]:
    row = asdict(source)
    row["velocity"] = list(source.velocity)
    return row


def cell_to_json(cell: CellRecord) -> dict[str, object]:
    pts = cell.contour[:, 0, :].astype(float)
    step = max(1, len(pts) // 48)
    decimated = pts[::step]
    contour_points_px = [[round(float(x * SX), 2), round(float(y * SY), 2)] for x, y in decimated]
    return {
        "cell_id": cell.cell_id,
        "field_family": "multi_emitter_standing_wave_scalar_field",
        "taxonomy_type": f"{cell.polarity}_phase_cell",
        "topology_class": cell.topology_class,
        "polarity": cell.polarity,
        "source_ids": list(cell.source_ids),
        "centroid_px": [round(cell.centroid_px[0], 2), round(cell.centroid_px[1], 2)],
        "area_px": round(cell.area_px, 2),
        "perimeter_px": round(cell.perimeter_px, 2),
        "circularity": round(cell.circularity, 4),
        "hull_ratio": round(cell.hull_ratio, 4),
        "ellipse_elongation": round(cell.ellipse_elongation, 4),
        "corner_count": cell.corner_count,
        "curvature_lobe_count": cell.curvature_lobe_count,
        "source_neighborhood_count": cell.source_neighborhood_count,
        "confidence": round(cell.confidence, 4),
        "render_policy": cell.render_policy,
        "contour_points_px": contour_points_px,
        "cultural_status": "internal_austin_review_needed",
    }


def hex_seed_sources(phase: float) -> list[WaveSource]:
    breathe = 1.0 + 0.050 * math.sin(TAU * phase)
    drift = math.radians(3.0) * math.sin(TAU * phase + 0.4)
    center = (960.0 + 8.0 * math.sin(TAU * phase * 2.0), 540.0 + 5.0 * math.cos(TAU * phase))
    sources = [
        WaveSource("radial_center", center[0], center[1], 1.22, 244.0, 1.0 / DURATION_SECONDS, 0.18, 920.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 6, "radial_continuous")
    ]
    for idx in range(6):
        angle = math.radians(30.0 + idx * 60.0) + drift
        local = 1.0 + 0.025 * math.sin(TAU * phase * 2.0 + idx * 1.7)
        radius = 292.0 * breathe * local
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius * 0.93
        sources.append(
            WaveSource(
                f"radial_ring_{idx:02d}",
                x,
                y,
                0.82 + 0.04 * math.sin(idx),
                214.0 + (idx % 3) * 16.0,
                1.0 / DURATION_SECONDS,
                0.38 * idx + 0.06 * math.sin(TAU * phase),
                940.0,
                (0.0, 0.0),
                0.0,
                DURATION_SECONDS,
                6,
                "radial_continuous_hex_breathing",
            )
        )
    return sources


def two_source_sources(phase: float) -> list[WaveSource]:
    open_level = smootherstep(0.5 - 0.5 * math.cos(TAU * phase))
    sep = 172.0 + 508.0 * open_level
    center = (960.0, 540.0 + 18.0 * math.sin(TAU * phase))
    skew = 22.0 * math.sin(TAU * phase + 0.8)
    freq = 1.0 / DURATION_SECONDS
    return [
        WaveSource("left_source", center[0] - sep * 0.5, center[1] - skew, 1.0, 196.0, freq, 0.0, 1080.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 2, "moving_radial"),
        WaveSource("right_source", center[0] + sep * 0.5, center[1] + skew, 1.0, 196.0, freq, math.pi * 0.03, 1080.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 2, "moving_radial"),
    ]


RAIN_DROPS: tuple[tuple[float, float, float, float, float], ...] = (
    (0.10, 330.0, 276.0, 164.0, 2.80),
    (0.78, 804.0, 354.0, 172.0, 2.70),
    (1.46, 1304.0, 300.0, 158.0, 2.55),
    (2.10, 1042.0, 658.0, 182.0, 2.90),
    (2.82, 548.0, 742.0, 166.0, 2.70),
    (3.50, 1514.0, 638.0, 176.0, 2.78),
    (4.22, 388.0, 526.0, 184.0, 2.95),
    (4.96, 1182.0, 842.0, 162.0, 2.62),
    (5.54, 1662.0, 352.0, 168.0, 2.68),
)


def raindrop_sources(phase: float) -> list[WaveSource]:
    time_seconds = phase * DURATION_SECONDS
    sources: list[WaveSource] = []
    for idx, (birth, x, y, wavelength, lifetime) in enumerate(RAIN_DROPS):
        env = impact_envelope(
            WaveSource("_probe", x, y, 1.0, wavelength, 1.15, 0.0, 620.0, (0.0, 0.0), birth, lifetime, 0, "impact"),
            time_seconds,
        )
        amp = 1.05 if idx % 3 else 0.92
        sources.append(
            WaveSource(
                f"drop_{idx:02d}",
                x,
                y,
                amp,
                wavelength,
                1.15,
                -TAU * birth * 0.07 + idx * 0.11,
                620.0 + 38.0 * (idx % 4),
                (0.0, 0.0),
                birth,
                lifetime,
                0,
                "impact",
            )
        )
        if env > 0.05 and idx % 4 == 1:
            sources.append(
                WaveSource(
                    f"drop_{idx:02d}_soft_echo",
                    x + 26.0,
                    y - 18.0,
                    0.34,
                    wavelength * 1.42,
                    0.78,
                    idx * 0.23,
                    780.0,
                    (0.0, 0.0),
                    birth + 0.12,
                    max(1.7, lifetime - 0.22),
                    0,
                    "impact",
                )
            )
    return sources


def recursive_sources(phase: float) -> list[WaveSource]:
    center = (960.0 + 24.0 * math.sin(TAU * phase * 0.5), 540.0)
    freq = 1.0 / DURATION_SECONDS
    sources: list[WaveSource] = [
        WaveSource("recursive_center_long", center[0], center[1], 0.88, 252.0, freq, 0.0, 880.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 5, "recursive_long"),
        WaveSource("recursive_center_short", center[0] + 6.0, center[1] - 4.0, 0.58, 126.0, 2.0 / DURATION_SECONDS, 0.74, 560.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 5, "recursive_short"),
    ]
    for idx, angle_deg in enumerate([-12, 58, 130, 206, 288]):
        angle = math.radians(angle_deg + 3.0 * math.sin(TAU * phase + idx))
        radius = 342.0 + 18.0 * math.sin(TAU * phase * 2.0 + idx * 0.7)
        x = center[0] + math.cos(angle) * radius
        y = center[1] + math.sin(angle) * radius * 0.82
        sources.append(
            WaveSource(
                f"recursive_ring_{idx:02d}",
                x,
                y,
                0.72,
                198.0 + 12.0 * (idx % 2),
                freq,
                idx * 0.41,
                790.0,
                (0.0, 0.0),
                0.0,
                DURATION_SECONDS,
                5,
                "recursive_ring_long",
            )
        )
        sources.append(
            WaveSource(
                f"recursive_ring_{idx:02d}_inner",
                x * 0.82 + center[0] * 0.18,
                y * 0.82 + center[1] * 0.18,
                0.34,
                104.0 + 8.0 * (idx % 3),
                2.0 / DURATION_SECONDS,
                idx * 0.63 + 0.35,
                500.0,
                (0.0, 0.0),
                0.0,
                DURATION_SECONDS,
                5,
                "recursive_ring_short",
            )
        )
    return sources


LOOPS: tuple[LoopSpec, ...] = (
    LoopSpec(
        key="seed_sun_trigon_reveal",
        filename="seed_sun_trigon_reveal_v002.mp4",
        description="Center/radial scalar field reveal: a source-like circle remains legible while surrounding extracted scallop/trigon cells read as radial release candidates.",
        source_builder=hex_seed_sources,
        threshold_percentile=75.0,
        min_area=210.0,
        max_area=36000.0,
        max_cells=34,
        node_epsilon=0.034,
        blur_sigma=1.35,
        compound_policy="faint",
    ),
    LoopSpec(
        key="two_source_interference_primitives",
        filename="two_source_interference_primitives_v002.mp4",
        description="Two-source interference tuned for readable crescent, lens, and band cells rather than dense antinode texture.",
        source_builder=two_source_sources,
        threshold_percentile=74.0,
        min_area=230.0,
        max_area=62000.0,
        max_cells=32,
        node_epsilon=0.032,
        blur_sigma=1.20,
        compound_policy="faint",
    ),
    LoopSpec(
        key="raindrops_on_water_primitives",
        filename="raindrops_on_water_primitives_v002.mp4",
        description="Fewer, larger impact sources create readable ripple primitives with temporal hold to avoid one-frame speckle shimmer.",
        source_builder=raindrop_sources,
        threshold_percentile=76.0,
        min_area=240.0,
        max_area=42000.0,
        max_cells=31,
        node_epsilon=0.040,
        blur_sigma=1.85,
        compound_policy="faint",
    ),
    LoopSpec(
        key="dual_threshold_recursive_primitives",
        filename="dual_threshold_recursive_primitives_v002.mp4",
        description="Mixed-wavelength scalar field viewed at two thresholds to test nested crescent and trigon boundary readability.",
        source_builder=recursive_sources,
        threshold_percentile=79.0,
        min_area=190.0,
        max_area=42000.0,
        max_cells=33,
        node_epsilon=0.032,
        blur_sigma=1.28,
        compound_policy="faint",
        dual_threshold=True,
        low_threshold_percentile=60.0,
    ),
)


def save_debug_bundle(
    spec: LoopSpec,
    frame: np.ndarray,
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    time_seconds: float,
) -> dict[str, Path]:
    stem = Path(spec.filename).stem
    paths: dict[str, Path] = {}
    beauty_path = MIDPOINT_DIR / f"{stem}_midpoint.png"
    cv2.imwrite(str(beauty_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    paths["beauty"] = beauty_path

    layers = {
        "scalar_field": grayscale_layer(field_norm, f"{stem} scalar field"),
        "nodal_lines": nodal_layer(field_norm, spec, f"{stem} nodal lines"),
        "positive_negative_regions": regions_layer(field_norm, result.threshold, spec, f"{stem} positive/negative regions"),
        "cell_class_colors": classes_layer(result.cells, f"{stem} classified cells"),
        "source_points": source_layer(field_norm, sources, time_seconds, f"{stem} source points"),
    }
    for layer_name, layer in layers.items():
        path = DEBUG_DIR / f"{stem}_{layer_name}_midpoint.png"
        cv2.imwrite(str(path), layer, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        paths[layer_name] = path

    thumbs = [cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)]
    labels = ["beauty"]
    for layer_name in ["scalar_field", "nodal_lines", "positive_negative_regions", "cell_class_colors", "source_points"]:
        thumbs.append(cv2.resize(layers[layer_name], (480, 270), interpolation=cv2.INTER_AREA))
        labels.append(layer_name)
    for thumb, label in zip(thumbs, labels, strict=True):
        draw_text(thumb, label, (16, 248), LABEL, scale=0.42)
    composite = cv2.hconcat(thumbs)
    composite_path = DEBUG_DIR / f"{stem}_debug_composite_midpoint.png"
    cv2.imwrite(str(composite_path), composite, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    paths["debug_composite"] = composite_path
    return paths


def make_contact_sheet(midpoints: list[tuple[LoopSpec, np.ndarray]]) -> Path:
    thumbs: list[np.ndarray] = []
    for spec, frame in midpoints:
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        draw_text(thumb, Path(spec.filename).stem, (14, 248), LABEL, scale=0.40)
        thumbs.append(thumb)
    sheet = cv2.vconcat([cv2.hconcat(thumbs[:2]), cv2.hconcat(thumbs[2:])])
    path = OUT_DIR / "cymatic_field_topology_v002_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_debug_contact_sheet() -> Path:
    rows: list[np.ndarray] = []
    layer_names = ["beauty", "scalar_field", "nodal_lines", "positive_negative_regions", "cell_class_colors", "source_points"]
    for spec in LOOPS:
        stem = Path(spec.filename).stem
        images: list[np.ndarray] = []
        for layer_name in layer_names:
            if layer_name == "beauty":
                path = MIDPOINT_DIR / f"{stem}_midpoint.png"
            else:
                path = DEBUG_DIR / f"{stem}_{layer_name}_midpoint.png"
            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError(f"missing debug still {path}")
            thumb = cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA)
            draw_text(thumb, layer_name, (10, 164), LABEL, scale=0.32)
            images.append(thumb)
        row = cv2.hconcat(images)
        draw_text(row, stem, (10, 22), LABEL, scale=0.42)
        rows.append(row)
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "cymatic_field_topology_v002_debug_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_phase_contact_sheet() -> Path:
    sample_frames = [0, N_FRAMES // 4, N_FRAMES // 2, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    rows: list[np.ndarray] = []
    for spec in LOOPS:
        video_path = OUT_DIR / spec.filename
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"could not open rendered video for phase sheet: {video_path}")
        thumbs: list[np.ndarray] = []
        for frame_index in sample_frames:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                capture.release()
                raise RuntimeError(f"could not read frame {frame_index} from {video_path}")
            thumb = cv2.resize(frame, (384, 216), interpolation=cv2.INTER_AREA)
            draw_text(thumb, f"f{frame_index:03d}", (14, 196), LABEL, scale=0.38)
            thumbs.append(thumb)
        capture.release()
        row = cv2.hconcat(thumbs)
        draw_text(row, Path(spec.filename).stem, (12, 24), LABEL, scale=0.42)
        rows.append(row)
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "cymatic_field_topology_v002_phase_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def render_clip(spec: LoopSpec) -> tuple[np.ndarray, dict[str, object]]:
    writer = H264Writer(OUT_DIR / spec.filename, fps=FPS, size=(W, H))
    tracker = CellTracker()
    midpoint_frame: np.ndarray | None = None
    midpoint_field: np.ndarray | None = None
    midpoint_result: ExtractionResult | None = None
    midpoint_low_result: ExtractionResult | None = None
    midpoint_sources: list[WaveSource] | None = None
    midpoint_render_cells: list[RenderCell] | None = None
    per_frame_counts: list[int] = []
    per_frame_render_counts: list[int] = []
    class_totals: Counter[str] = Counter()
    polarity_totals: Counter[str] = Counter()
    threshold_values: list[float] = []

    for fi in range(N_FRAMES):
        phase = fi / N_FRAMES
        time_seconds = phase * DURATION_SECONDS
        sources = spec.source_builder(phase)
        field_norm = evaluate_field(sources, time_seconds, spec.blur_sigma)
        result = extract_cells(field_norm, sources, spec, time_seconds)
        low_result: ExtractionResult | None = None
        if spec.dual_threshold:
            low_result = extract_cells(
                field_norm,
                sources,
                spec,
                time_seconds,
                threshold_percentile=spec.low_threshold_percentile,
                max_cells=132,
            )
        render_cells = tracker.update(result.cells, fi, cap=spec.max_cells)
        frame = render_beauty(
            field_norm,
            render_cells,
            sources,
            spec,
            time_seconds,
            low_cells=low_result.cells if low_result is not None else None,
        )
        writer.write(frame)

        per_frame_counts.append(len(result.cells))
        per_frame_render_counts.append(len(render_cells))
        class_totals.update(result.counts_by_class)
        polarity_totals.update(result.counts_by_polarity)
        threshold_values.append(result.threshold)

        if fi == LEGIBILITY_FRAME:
            midpoint_frame = frame.copy()
            midpoint_field = field_norm.copy()
            midpoint_result = result
            midpoint_low_result = low_result
            midpoint_sources = sources
            midpoint_render_cells = list(render_cells)

        if (fi + 1) % 24 == 0:
            print(f"  {spec.filename} {fi + 1}/{N_FRAMES}", flush=True)

    writer.close()
    if (
        midpoint_frame is None
        or midpoint_field is None
        or midpoint_result is None
        or midpoint_sources is None
        or midpoint_render_cells is None
    ):
        raise RuntimeError(f"no midpoint captured for {spec.filename}")
    save_debug_bundle(spec, midpoint_frame, midpoint_field, midpoint_result, midpoint_sources, LEGIBILITY_FRAME / FPS)

    summary: dict[str, object] = {
        "filename": spec.filename,
        "description": spec.description,
        "frames": N_FRAMES,
        "fps": FPS,
        "dimensions": [W, H],
        "legibility_still_frame": LEGIBILITY_FRAME,
        "legibility_still_time_seconds": round(LEGIBILITY_FRAME / FPS, 3),
        "threshold_percentile": spec.threshold_percentile,
        "midpoint_threshold": round(midpoint_result.threshold, 5),
        "midpoint_low_threshold": round(midpoint_low_result.threshold, 5) if midpoint_low_result else None,
        "cells_per_frame_min": min(per_frame_counts),
        "cells_per_frame_max": max(per_frame_counts),
        "cells_per_frame_mean": round(float(np.mean(per_frame_counts)), 2),
        "rendered_cells_per_frame_min": min(per_frame_render_counts),
        "rendered_cells_per_frame_max": max(per_frame_render_counts),
        "rendered_cells_per_frame_mean": round(float(np.mean(per_frame_render_counts)), 2),
        "class_totals": dict(class_totals),
        "polarity_totals": dict(polarity_totals),
        "threshold_min": round(min(threshold_values), 5),
        "threshold_max": round(max(threshold_values), 5),
        "midpoint_sources": [source_to_json(source) for source in midpoint_sources],
        "midpoint_cells": [cell_to_json(cell) for cell in midpoint_result.cells[:80]],
        "midpoint_rendered_tracks": [
            {
                "track_id": rendered.track_id,
                "cell_id": rendered.cell.cell_id,
                "topology_class": rendered.cell.topology_class,
                "seen_frames": rendered.seen_frames,
                "missing_frames": rendered.missing_frames,
                "strength": round(rendered.strength, 4),
            }
            for rendered in midpoint_render_cells[:80]
        ],
    }
    return midpoint_frame, summary


def write_manifest(
    summaries: list[dict[str, object]],
    contact_sheet: Path,
    debug_contact_sheet: Path,
    phase_contact_sheet: Path,
) -> Path:
    manifest = {
        "renderer": "scripts/cymatic_field_topology_v002.py",
        "created_for": "Salish Sea Dreaming Phase 2 internal scalar-field topology legibility pass",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "dimensions": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "legibility_still_frame": LEGIBILITY_FRAME,
        "legibility_still_time_seconds": round(LEGIBILITY_FRAME / FPS, 3),
        "field_grid": [FW, FH],
        "field_formula": "F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i - omega_i*t + phase_i)*decay(distance)*envelope(t)",
        "temporal_structure": {
            "0.0-1.5": "full scalar field visible; classified cells mostly hidden",
            "1.5-3.0": "field fades toward 30%; classified cells emerge",
            "3.0-4.5": "field held near 10%; primitive boundaries fully readable",
            "4.5-6.0": "cells dissolve while field returns for loop closure",
        },
        "temporal_persistence": {
            "tracking": "class + centroid proximity + area similarity",
            "hold_frames": HOLD_FRAMES,
            "hold_seconds": round(HOLD_FRAMES / FPS, 3),
            "fade_frames_after_hold": FADE_FRAMES,
        },
        "beauty_render_rule": "Classes use the same restrained ivory, pale-blue, muted teal/gold palette and are differentiated mainly by boundary language, not debug category colors.",
        "source_tuple_fields": [
            "x",
            "y",
            "amplitude",
            "wavelength",
            "frequency",
            "phase",
            "decay",
            "velocity",
            "birth_time",
            "lifetime",
            "symmetry_order",
            "mode",
        ],
        "outputs": {
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "debug_contact_sheet": str(debug_contact_sheet.relative_to(ROOT)),
            "phase_contact_sheet": str(phase_contact_sheet.relative_to(ROOT)),
        },
        "clips": summaries,
    }
    path = OUT_DIR / "cymatic_field_topology_v002_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    rows = "\n".join(
        f"- `{summary['filename']}`: {summary['description']} "
        f"Legibility-frame cells: {len(summary['midpoint_cells'])}; class totals across sampled frames: {summary['class_totals']}."
        for summary in summaries
    )
    readme = f"""# Cymatic Field Topology v002 - 2026-05-20

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim.

## Purpose

This is a visual-legibility pass over the v001 scalar-field topology engine. It
does not hand-place circle/crescent/trigon icons. Visible cells are connected
threshold regions extracted from continuous wave fields, then rendered with
class-specific boundary language so circle-like, crescent-like, and trigon-like
cells can be read in the beauty render.

## Method

- Source tuple model:
  `(x, y, amplitude, wavelength, frequency, phase, decay, velocity, birth_time, lifetime, symmetry_order, mode)`.
- Field:
  `F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i - omega_i*t + phase_i)*decay(distance)*envelope(t)`.
- Each frame is smoothed, normalized, thresholded into positive cells,
  negative cells, and nodal bands.
- Connected components are classified by area, perimeter, centroid, convex-hull
  ratio, fitted-ellipse elongation, contour corner/lobe count, and source
  neighborhood count.
- Tiny speckles and large edge fragments are rejected before rendering.
- Selection is class-balanced and capped to roughly 25-35 visible cells per
  frame.
- Temporal persistence tracks cells by class, centroid proximity, and area
  similarity. Persisting cells render stronger; missing cells hold for about
  0.4s before fading.
- Beauty rendering uses a restrained ivory, pale-blue, muted teal/gold palette.
  It does not use red/green/blue debug category colors.

## Temporal Structure

- 0.0-1.5s: full scalar field visible.
- 1.5-3.0s: field fades toward 30%; classified cells emerge.
- 3.0-4.5s: field is reduced near 10%; primitive boundaries are most readable.
- 4.5-6.0s: cells dissolve back into the field and the loop closes.

Legibility stills are sampled at frame {LEGIBILITY_FRAME} ({LEGIBILITY_FRAME / FPS:.2f}s),
inside the 3.0-4.5s review window.

## Clips

{rows}

## Evidence Bundle

- 4 MP4 loops, 1920x1080, 24 fps, 6 seconds, 144 frames.
- Legibility-window midpoint stills in `midpoint_stills/`.
- Debug stills in `debug_stills/` for scalar grayscale, nodal lines,
  positive/negative regions, cell-class colors, and source points.
- Contact sheet: `cymatic_field_topology_v002_contact_sheet.png`.
- Debug contact sheet: `cymatic_field_topology_v002_debug_contact_sheet.png`.
- Phase contact sheet: `cymatic_field_topology_v002_phase_contact_sheet.png`.
- Manifest/source list: `cymatic_field_topology_v002_manifest.json`.

## Honest Read

The visible marks are still field-extracted cells, not placed icons. v002 only
tunes thresholding, selection, temporal hold, and boundary rendering. Compound
regions are intentionally suppressed or rendered as faint ghosts because they
often read as ambiguous topology rather than clear primitive-cell morphology.
The radial seed clip is a canary for trigon/ray readability, not an
Austin-approved sun grammar.

## Boundaries

No salmon, birds, figures, Austin source artwork, exact Austin motif geometry,
public-readiness claim, traditional-meaning claim, or Austin-approval claim is
included in this packet.

Renderer:

`scripts/cymatic_field_topology_v002.py`
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# v004 contour-respecting wave-geometry override.
#
# The v002 machinery above remains useful for scalar-field construction,
# threshold extraction, debug layers, and basic morphology. v004 replaces the
# beauty pass and packet writer with source-feature records that always carry a
# raw contour/arc and a geometry-gated cleaned version.

SELECTED_SUN_ALPHA = 0.70
SELECTED_SUN_WAVELENGTH = 150.0


def temporal_levels(time_seconds: float) -> tuple[float, float]:
    if time_seconds < 1.0:
        field_alpha = 1.0
        primitive_alpha = 0.0
    elif time_seconds < 2.0:
        k = smoothstep(1.0, 2.0, time_seconds)
        field_alpha = 1.0 - 0.70 * k
        primitive_alpha = k
    elif time_seconds < 4.5:
        field_alpha = 0.30 - 0.20 * smoothstep(2.0, 2.35, time_seconds)
        primitive_alpha = 1.0
    else:
        k = smoothstep(4.5, 6.0, time_seconds)
        field_alpha = 0.10 + 0.90 * k
        primitive_alpha = 1.0 - k
    return clamp01(field_alpha), clamp01(primitive_alpha)


def full_points_from_contour(contour: np.ndarray) -> np.ndarray:
    return scaled_contour(contour)[:, 0, :].astype(np.float32)


def polyline_length(points: np.ndarray, closed: bool = False) -> float:
    if len(points) < 2:
        return 0.0
    deltas = np.diff(points, axis=0)
    length = float(np.sqrt((deltas * deltas).sum(axis=1)).sum())
    if closed:
        delta = points[0] - points[-1]
        length += float(math.hypot(float(delta[0]), float(delta[1])))
    return length


def point_bounds(points: np.ndarray, pad: float = 0.0) -> tuple[float, float, float, float]:
    if len(points) == 0:
        return (0.0, 0.0, 0.0, 0.0)
    x0 = max(0.0, float(points[:, 0].min()) - pad)
    y0 = max(0.0, float(points[:, 1].min()) - pad)
    x1 = min(float(W), float(points[:, 0].max()) + pad)
    y1 = min(float(H), float(points[:, 1].max()) + pad)
    return x0, y0, x1, y1


def point_centroid(points: np.ndarray) -> tuple[float, float]:
    if len(points) == 0:
        return (0.0, 0.0)
    return (float(points[:, 0].mean()), float(points[:, 1].mean()))


def point_orientation(points: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    centered = points.astype(np.float32) - np.mean(points.astype(np.float32), axis=0, keepdims=True)
    if float(np.abs(centered).sum()) <= 1e-6:
        return 0.0
    cov = np.cov(centered.T)
    values, vectors = np.linalg.eigh(cov)
    axis = vectors[:, int(np.argmax(values))]
    return float(math.atan2(float(axis[1]), float(axis[0])))


def smooth_closed_points(points: np.ndarray, iterations: int = 2) -> np.ndarray:
    if len(points) < 5:
        return points.astype(np.float32)
    out = points.astype(np.float32).copy()
    for _ in range(iterations):
        out = (np.roll(out, 1, axis=0) + 2.0 * out + np.roll(out, -1, axis=0)) * 0.25
    return out.astype(np.float32)


def smooth_open_points(points: np.ndarray, iterations: int = 2) -> np.ndarray:
    if len(points) < 5:
        return points.astype(np.float32)
    out = points.astype(np.float32).copy()
    start = out[0].copy()
    end = out[-1].copy()
    for _ in range(iterations):
        inner = out.copy()
        inner[1:-1] = (out[:-2] + 2.0 * out[1:-1] + out[2:]) * 0.25
        out = inner
        out[0] = start
        out[-1] = end
    return out.astype(np.float32)


def simplify_points(points: np.ndarray, *, closed: bool, epsilon: float) -> np.ndarray:
    if len(points) < (8 if closed else 4):
        return points.astype(np.float32)
    approx = cv2.approxPolyDP(points.reshape(-1, 1, 2).astype(np.float32), epsilon, closed)
    simplified = approx[:, 0, :].astype(np.float32)
    if closed and len(simplified) < 8:
        return points.astype(np.float32)
    if not closed and len(simplified) < 4:
        return points.astype(np.float32)
    return simplified


def points_to_local_mask(
    points: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    closed: bool,
    thickness: int = 5,
) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    mask = np.zeros((max(1, y1 - y0), max(1, x1 - x0)), dtype=np.uint8)
    if len(points) < 2:
        return mask
    pts = np.round(points).astype(np.int32).copy()
    pts[:, 0] -= x0
    pts[:, 1] -= y0
    pts = pts.reshape(-1, 1, 2)
    if closed and len(points) >= 3:
        cv2.fillPoly(mask, [pts], 255, lineType=cv2.LINE_AA)
    else:
        cv2.polylines(mask, [pts], False, 255, thickness, lineType=cv2.LINE_AA)
    return mask


def geometry_iou(raw: np.ndarray, styled: np.ndarray, *, closed: bool) -> float:
    if len(raw) < 2 or len(styled) < 2:
        return 0.0
    union = np.vstack([raw, styled])
    x0, y0, x1, y1 = point_bounds(union, pad=18.0)
    bbox = (int(x0), int(y0), int(math.ceil(x1)) + 1, int(math.ceil(y1)) + 1)
    raw_mask = points_to_local_mask(raw, bbox, closed=closed)
    styled_mask = points_to_local_mask(styled, bbox, closed=closed)
    intersection = int(np.logical_and(raw_mask > 0, styled_mask > 0).sum())
    union_count = int(np.logical_or(raw_mask > 0, styled_mask > 0).sum())
    if union_count <= 0:
        return 0.0
    return float(intersection / union_count)


def sample_points(points: np.ndarray, max_points: int = 96) -> np.ndarray:
    if len(points) <= max_points:
        return points.astype(np.float32)
    idx = np.linspace(0, len(points) - 1, max_points).astype(np.int32)
    return points[idx].astype(np.float32)


def mean_boundary_distance(raw: np.ndarray, styled: np.ndarray) -> float:
    if len(raw) == 0 or len(styled) == 0:
        return 9999.0
    a = sample_points(raw)
    b = sample_points(styled)
    diff = a[:, None, :] - b[None, :, :]
    dist = np.sqrt((diff * diff).sum(axis=2))
    return float(dist.min(axis=1).mean())


def style_points_with_gate(raw_points: np.ndarray, *, closed: bool) -> tuple[np.ndarray, dict[str, float], str]:
    raw = raw_points.astype(np.float32)
    if len(raw) < (5 if closed else 4):
        return raw, {
            "iou": 1.0,
            "mean_boundary_distance_px": 0.0,
            "used_raw_fallback": 1.0,
            "candidate_iou": 1.0,
            "candidate_mean_boundary_distance_px": 0.0,
        }, "raw_short_feature"

    if closed:
        smoothed = smooth_closed_points(raw, iterations=2)
        epsilon = max(1.8, min(5.2, polyline_length(smoothed, closed=True) * 0.006))
        candidate = simplify_points(smoothed, closed=True, epsilon=epsilon)
        iou = geometry_iou(raw, candidate, closed=True)
        distance = mean_boundary_distance(raw, candidate)
        if iou < 0.68 or distance > 14.0:
            return raw, {
                "iou": 1.0,
                "mean_boundary_distance_px": 0.0,
                "used_raw_fallback": 1.0,
                "candidate_iou": round(iou, 4),
                "candidate_mean_boundary_distance_px": round(distance, 3),
            }, "raw_geometry_gate_fallback"
        return candidate, {
            "iou": round(iou, 4),
            "mean_boundary_distance_px": round(distance, 3),
            "used_raw_fallback": 0.0,
            "candidate_iou": round(iou, 4),
            "candidate_mean_boundary_distance_px": round(distance, 3),
        }, "smoothed_contour"

    smoothed = smooth_open_points(raw, iterations=2)
    epsilon = max(1.2, min(4.0, polyline_length(smoothed, closed=False) * 0.010))
    candidate = simplify_points(smoothed, closed=False, epsilon=epsilon)
    iou = geometry_iou(raw, candidate, closed=False)
    distance = mean_boundary_distance(raw, candidate)
    endpoint_distance = float(math.hypot(*(candidate[0] - raw[0])) + math.hypot(*(candidate[-1] - raw[-1])))
    if iou < 0.54 or distance > 10.0 or endpoint_distance > 16.0:
        return raw, {
            "iou": 1.0,
            "mean_boundary_distance_px": 0.0,
            "endpoint_distance_px": 0.0,
            "used_raw_fallback": 1.0,
            "candidate_iou": round(iou, 4),
            "candidate_mean_boundary_distance_px": round(distance, 3),
        }, "raw_geometry_gate_fallback"
    return candidate, {
        "iou": round(iou, 4),
        "mean_boundary_distance_px": round(distance, 3),
        "endpoint_distance_px": round(endpoint_distance, 3),
        "used_raw_fallback": 0.0,
        "candidate_iou": round(iou, 4),
        "candidate_mean_boundary_distance_px": round(distance, 3),
    }, "smoothed_open_arc"


def active_sources(sources: list[WaveSource], time_seconds: float, *, impact_only: bool = False) -> list[WaveSource]:
    items: list[WaveSource] = []
    for source in sources:
        if impact_only and source.mode != "impact":
            continue
        if source_envelope(source, time_seconds) > 0.035:
            items.append(source)
    return items


def nearest_source_id(
    centroid: tuple[float, float],
    sources: list[WaveSource],
    time_seconds: float,
    *,
    impact_only: bool = False,
) -> tuple[str, ...]:
    usable = active_sources(sources, time_seconds, impact_only=impact_only)
    if not usable:
        usable = active_sources(sources, time_seconds)
    if not usable:
        return tuple()
    usable.sort(key=lambda source: math.hypot(centroid[0] - source.x, centroid[1] - source.y))
    return (usable[0].source_id,)


def make_feature(
    *,
    feature_id: str,
    feature_type: str,
    primitive_class: str,
    primitive_subtype: str,
    raw_points: np.ndarray,
    closed: bool,
    source_cell: CellRecord | None,
    source_ids: tuple[str, ...],
    confidence: float,
    strength: float,
    polarity: str,
) -> FeatureRecord | None:
    if len(raw_points) < (4 if not closed else 8):
        return None
    styled, metrics, render_policy = style_points_with_gate(raw_points, closed=closed)
    centroid = point_centroid(raw_points)
    if not source_ids and source_cell is not None:
        source_ids = source_cell.source_ids
    return FeatureRecord(
        feature_id=feature_id,
        feature_type=feature_type,
        primitive_class=primitive_class,
        primitive_subtype=primitive_subtype,
        raw_points=raw_points.astype(np.float32),
        styled_points=styled.astype(np.float32),
        closed=closed,
        source_cell=source_cell,
        source_ids=tuple(source_ids),
        centroid_px=centroid,
        bounds_px=point_bounds(raw_points, pad=0.0),
        orientation_rad=point_orientation(raw_points),
        confidence=clamp01(confidence),
        strength=clamp01(strength),
        metrics=metrics,
        render_policy=render_policy,
        polarity=polarity,
    )


def feature_score(feature: FeatureRecord) -> float:
    x0, y0, x1, y1 = feature.bounds_px
    size = max(1.0, (x1 - x0) * (y1 - y0))
    size_score = 1.0 - min(1.0, abs(math.log(size / 24000.0)) / 3.0)
    type_bonus = {
        "circle_like": 0.20,
        "crescent_like": 0.28,
        "trigon_like": 0.34,
        "wavefront_arc": 0.30,
    }.get(feature.primitive_class, 0.0)
    fallback_penalty = 0.08 * feature.metrics.get("used_raw_fallback", 0.0)
    return (
        type_bonus
        + 0.58 * feature.confidence
        + 0.22 * size_score
        + 0.18 * feature.strength
        - fallback_penalty
    )


def nonmax_features(features: list[FeatureRecord], cap: int, min_distance: float = 56.0) -> list[FeatureRecord]:
    ordered = sorted(features, key=feature_score, reverse=True)
    selected: list[FeatureRecord] = []
    for feature in ordered:
        if len(selected) >= cap:
            break
        cx, cy = feature.centroid_px
        if all(math.hypot(cx - other.centroid_px[0], cy - other.centroid_px[1]) >= min_distance for other in selected):
            selected.append(feature)
    return selected


def circle_points(center: tuple[float, float], radius: float, count: int = 80) -> np.ndarray:
    angles = np.linspace(0.0, TAU, count, endpoint=False, dtype=np.float32)
    return np.column_stack(
        [
            center[0] + np.cos(angles) * radius,
            center[1] + np.sin(angles) * radius,
        ]
    ).astype(np.float32)


def build_impact_circle_features(
    sources: list[WaveSource],
    time_seconds: float,
    spec: LoopSpec,
    frame_index: int,
) -> list[FeatureRecord]:
    features: list[FeatureRecord] = []
    for idx, source in enumerate(sources):
        if source.mode != "impact":
            continue
        env = source_envelope(source, time_seconds)
        if env <= 0.055:
            continue
        radius = 8.0 + 20.0 * smoothstep(0.05, 0.42, env)
        raw = circle_points((source.x, source.y), radius, count=72)
        feature = make_feature(
            feature_id=f"{spec.key}_f{frame_index:03d}_impact_{idx:02d}",
            feature_type="field_source_impact",
            primitive_class="circle_like",
            primitive_subtype="positive_impact_circle",
            raw_points=raw,
            closed=True,
            source_cell=None,
            source_ids=(source.source_id,),
            confidence=0.82 + 0.16 * env,
            strength=env,
            polarity="positive",
        )
        if feature is not None:
            features.append(feature)
    return features


def split_closed_contour_into_arcs(points: np.ndarray, target_length: float = 250.0) -> list[np.ndarray]:
    if len(points) < 24:
        return []
    total = polyline_length(points, closed=True)
    pieces = max(2, min(9, int(round(total / target_length))))
    step = max(10, len(points) // pieces)
    overlap = max(4, step // 8)
    arcs: list[np.ndarray] = []
    for piece in range(pieces):
        start = piece * step
        count = min(len(points) - 1, step + overlap)
        indices = (np.arange(count, dtype=np.int32) + start) % len(points)
        arc = points[indices].astype(np.float32)
        if polyline_length(arc, closed=False) >= 70.0:
            arcs.append(arc)
    return arcs


def extract_wavefront_arc_features(
    field_norm: np.ndarray,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
    *,
    cap: int,
    impact_only: bool = True,
) -> list[FeatureRecord]:
    tau = clamp(float(np.percentile(np.abs(field_norm), 67.0)), 0.16, 0.46)
    candidates: list[FeatureRecord] = []
    usable_sources = active_sources(sources, time_seconds, impact_only=impact_only)
    if not usable_sources and impact_only:
        usable_sources = active_sources(sources, time_seconds)
    for polarity, sign in (("positive", 1.0), ("negative", -1.0)):
        mask = ((field_norm * sign) > tau).astype(np.uint8) * 255
        mask = clean_threshold_mask(mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for contour_index, contour in enumerate(contours):
            area = float(cv2.contourArea(contour)) * SX * SY
            if area < 700.0 or area > 140000.0:
                continue
            points = full_points_from_contour(contour)
            for arc_index, arc in enumerate(split_closed_contour_into_arcs(points)):
                length = polyline_length(arc, closed=False)
                if length < 95.0 or length > 520.0:
                    continue
                chord = math.hypot(float(arc[-1, 0] - arc[0, 0]), float(arc[-1, 1] - arc[0, 1]))
                if chord <= 1.0:
                    continue
                curvature_ratio = length / chord
                if curvature_ratio < 1.035 or curvature_ratio > 3.2:
                    continue
                centroid = point_centroid(arc)
                source_ids = nearest_source_id(centroid, sources, time_seconds, impact_only=impact_only)
                source_strength = 0.45
                if source_ids:
                    source = next((item for item in sources if item.source_id == source_ids[0]), None)
                    if source is not None:
                        source_strength = source_envelope(source, time_seconds)
                        radial_distance = math.hypot(centroid[0] - source.x, centroid[1] - source.y)
                        if impact_only and (radial_distance < 32.0 or radial_distance > 690.0):
                            continue
                confidence = 0.58 + 0.24 * min(1.0, (curvature_ratio - 1.0) / 0.95) + 0.12 * source_strength
                feature = make_feature(
                    feature_id=f"{spec.key}_f{frame_index:03d}_arc_{polarity[:3]}_{contour_index:03d}_{arc_index:02d}",
                    feature_type="wavefront_segment",
                    primitive_class="crescent_like",
                    primitive_subtype="open_wavefront_crescent",
                    raw_points=arc,
                    closed=False,
                    source_cell=None,
                    source_ids=source_ids,
                    confidence=confidence,
                    strength=max(0.35, source_strength),
                    polarity=polarity,
                )
                if feature is not None:
                    candidates.append(feature)
    return nonmax_features(candidates, cap=cap, min_distance=76.0)


def source_ids_for_cell(cell: CellRecord, sources: list[WaveSource], time_seconds: float) -> tuple[str, ...]:
    if cell.source_ids:
        return cell.source_ids
    return nearest_source_id(cell.centroid_px, sources, time_seconds, impact_only=False)


def build_closed_cell_features(
    result: ExtractionResult,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
    *,
    allowed_classes: tuple[str, ...],
    cap: int,
    primitive_subtype: str,
) -> list[FeatureRecord]:
    candidates: list[FeatureRecord] = []
    for idx, cell in enumerate(result.cells):
        if cell.topology_class not in allowed_classes:
            continue
        if cell.render_policy == "suppress":
            continue
        if cell.area_px < 1250.0 or cell.area_px > spec.max_area * SX * SY:
            continue
        primitive_class = cell.topology_class
        if primitive_class == "compound":
            primitive_class = "compound"
        raw = full_points_from_contour(cell.contour)
        feature = make_feature(
            feature_id=f"{spec.key}_f{frame_index:03d}_cell_{idx:03d}",
            feature_type="threshold_cell",
            primitive_class=primitive_class,
            primitive_subtype=primitive_subtype,
            raw_points=raw,
            closed=True,
            source_cell=cell,
            source_ids=source_ids_for_cell(cell, sources, time_seconds),
            confidence=cell.confidence,
            strength=0.72 + 0.28 * cell.confidence,
            polarity=cell.polarity,
        )
        if feature is not None:
            candidates.append(feature)
    return nonmax_features(candidates, cap=cap, min_distance=62.0)


def build_two_source_features(
    result: ExtractionResult,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> list[FeatureRecord]:
    features = build_closed_cell_features(
        result,
        sources,
        spec,
        time_seconds,
        frame_index,
        allowed_classes=("crescent_like", "circle_like", "trigon_like"),
        cap=24,
        primitive_subtype="raw_lens_or_cell_contour",
    )
    features.sort(
        key=lambda feature: (
            0 if feature.primitive_class != "crescent_like" else 1,
            feature_score(feature),
        ),
        reverse=True,
    )
    return nonmax_features(features, cap=18, min_distance=68.0)


def build_sun_scallop_features(
    result: ExtractionResult,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> list[FeatureRecord]:
    center = (960.0, 540.0)
    candidates: list[FeatureRecord] = []
    for idx, cell in enumerate(result.cells):
        if cell.render_policy == "suppress":
            continue
        dx = cell.centroid_px[0] - center[0]
        dy = cell.centroid_px[1] - center[1]
        radial_distance = math.hypot(dx, dy)
        if radial_distance < 96.0 or radial_distance > 640.0:
            continue
        scallop_evidence = (
            cell.topology_class == "trigon_like"
            or (cell.curvature_lobe_count >= 2 and cell.circularity < 0.91 and cell.hull_ratio > 0.58)
        )
        if not scallop_evidence:
            continue
        raw = full_points_from_contour(cell.contour)
        feature = make_feature(
            feature_id=f"{spec.key}_f{frame_index:03d}_scallop_{idx:03d}",
            feature_type="cusp_region" if cell.topology_class == "trigon_like" else "threshold_cell",
            primitive_class="trigon_like",
            primitive_subtype="raw_outward_scallop_ray_cell",
            raw_points=raw,
            closed=True,
            source_cell=cell,
            source_ids=source_ids_for_cell(cell, sources, time_seconds) or ("sixfold_center",),
            confidence=min(1.0, cell.confidence + 0.10 * min(3, cell.curvature_lobe_count)),
            strength=0.82,
            polarity=cell.polarity,
        )
        if feature is not None:
            candidates.append(feature)
    return nonmax_features(candidates, cap=16, min_distance=72.0)


def build_negative_space_features(
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> list[FeatureRecord]:
    arcs = extract_wavefront_arc_features(
        field_norm,
        sources,
        spec,
        time_seconds,
        frame_index,
        cap=13,
        impact_only=True,
    )
    cells = build_closed_cell_features(
        result,
        sources,
        spec,
        time_seconds,
        frame_index,
        allowed_classes=("crescent_like", "trigon_like"),
        cap=5,
        primitive_subtype="negative_space_cutout_cell",
    )
    combined = arcs + cells
    return nonmax_features(combined, cap=16, min_distance=70.0)


def build_features_for_frame(
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> list[FeatureRecord]:
    if spec.key == "raindrop_wavefront_crescents":
        circles = build_impact_circle_features(sources, time_seconds, spec, frame_index)
        arcs = extract_wavefront_arc_features(
            field_norm,
            sources,
            spec,
            time_seconds,
            frame_index,
            cap=18,
            impact_only=True,
        )
        return nonmax_features(circles + arcs, cap=22, min_distance=48.0)
    if spec.key == "two_source_lens_cells":
        return build_two_source_features(result, sources, spec, time_seconds, frame_index)
    if spec.key == "sun_raw_scallop_trigons":
        return build_sun_scallop_features(result, sources, spec, time_seconds, frame_index)
    if spec.key == "negative_space_silhouette":
        return build_negative_space_features(field_norm, result, sources, spec, time_seconds, frame_index)
    return []


def draw_points_fill(
    frame: np.ndarray,
    points: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0 or len(points) < 3:
        return
    x0f, y0f, x1f, y1f = point_bounds(points, pad=28.0)
    bbox = (int(x0f), int(y0f), int(math.ceil(x1f)) + 1, int(math.ceil(y1f)) + 1)
    mask = points_to_local_mask(points, bbox, closed=True)
    add_mask(frame, mask, bbox, rgb, alpha, glow=glow)


def draw_points_outline(
    frame: np.ndarray,
    points: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 3,
    closed: bool = True,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0 or len(points) < 2:
        return
    x0f, y0f, x1f, y1f = point_bounds(points, pad=max(20.0, thickness * 5.0))
    bbox = (int(x0f), int(y0f), int(math.ceil(x1f)) + 1, int(math.ceil(y1f)) + 1)
    mask = points_to_local_mask(points, bbox, closed=closed, thickness=thickness)
    add_mask(frame, mask, bbox, rgb, alpha, glow=glow)


def draw_tapered_polyline(
    frame: np.ndarray,
    points: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    max_thickness: int = 8,
    min_thickness: int = 1,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0 or len(points) < 2:
        return
    rounded = np.round(points).astype(np.int32)
    pad = max(10, max_thickness * 5)
    x0 = max(0, int(rounded[:, 0].min()) - pad)
    y0 = max(0, int(rounded[:, 1].min()) - pad)
    x1 = min(W, int(rounded[:, 0].max()) + pad + 1)
    y1 = min(H, int(rounded[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    local = rounded.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    segment_count = len(local) - 1
    for idx in range(segment_count):
        t = (idx + 0.5) / max(1, segment_count)
        weight = math.sin(math.pi * t) ** 0.75
        thickness = max(min_thickness, int(round(min_thickness + (max_thickness - min_thickness) * weight)))
        cv2.line(mask, tuple(local[idx]), tuple(local[idx + 1]), 255, thickness, lineType=cv2.LINE_AA)
    add_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha, glow=glow)


def draw_feature(frame: np.ndarray, feature: FeatureRecord, alpha: float, *, negative_cutout: bool = False) -> None:
    if alpha <= 0.0:
        return
    points = feature.styled_points
    if negative_cutout:
        cut_rgb = (2, 10, 12)
        if feature.closed:
            draw_points_fill(frame, points, cut_rgb, alpha=0.90 * alpha, glow=0.0)
            draw_points_outline(frame, points, IVORY, alpha=0.10 * alpha, thickness=1, closed=True)
        else:
            draw_tapered_polyline(frame, points, cut_rgb, alpha=0.95 * alpha, max_thickness=13, glow=0.0)
            draw_tapered_polyline(frame, points, PALE_BLUE, alpha=0.10 * alpha, max_thickness=3, glow=0.0)
        return

    if not feature.closed:
        draw_tapered_polyline(frame, points, PALE_BLUE, alpha=0.66 * alpha, max_thickness=9, glow=0.018 * alpha)
        draw_tapered_polyline(frame, points, SOFT_IVORY, alpha=0.28 * alpha, max_thickness=4)
        return

    if feature.primitive_class == "circle_like":
        draw_points_fill(frame, points, IVORY, alpha=0.20 * alpha, glow=0.030 * alpha)
        draw_points_outline(frame, points, IVORY, alpha=0.70 * alpha, thickness=4, closed=True, glow=0.015 * alpha)
        draw_points_outline(frame, points, MUTED_GOLD, alpha=0.26 * alpha, thickness=1, closed=True)
    elif feature.primitive_class == "crescent_like":
        draw_points_fill(frame, points, PALE_BLUE, alpha=0.105 * alpha, glow=0.017 * alpha)
        draw_points_outline(frame, points, SOFT_IVORY, alpha=0.45 * alpha, thickness=4, closed=True)
        draw_points_outline(frame, points, MUTED_TEAL, alpha=0.30 * alpha, thickness=2, closed=True)
    elif feature.primitive_class == "trigon_like":
        draw_points_fill(frame, points, MUTED_GOLD, alpha=0.090 * alpha, glow=0.017 * alpha)
        draw_points_outline(frame, points, MUTED_TEAL, alpha=0.36 * alpha, thickness=3, closed=True)
        peaks = radial_peak_indices(points, feature.centroid_px, count=3)
        if peaks:
            n = len(points)
            window = max(4, min(18, n // 16))
            for peak in peaks:
                idxs = [(peak + offset) % n for offset in range(-window, window + 1)]
                draw_polyline_alpha(frame, points[idxs], MUTED_GOLD, alpha=0.46 * alpha, thickness=5)
                draw_polyline_alpha(frame, points[idxs], IVORY, alpha=0.16 * alpha, thickness=2)
        else:
            draw_points_outline(frame, points, SOFT_IVORY, alpha=0.22 * alpha, thickness=2, closed=True)
    else:
        draw_points_outline(frame, points, DIM_TEAL, alpha=0.12 * alpha, thickness=2, closed=True)


def render_surface_silhouette(frame: np.ndarray, field_norm: np.ndarray, field_alpha: float) -> None:
    field_full = cv2.resize(field_norm, (W, H), interpolation=cv2.INTER_CUBIC)
    amplitude = np.clip(np.abs(field_full), 0.0, 1.0) ** 0.55
    base = np.zeros((H, W, 3), dtype=np.float32)
    base[:, :, :] = rgb_to_bgr((13, 47, 53))
    base += amplitude[..., None] * rgb_to_bgr((66, 148, 153)) * (0.62 + 0.20 * field_alpha)
    node_mask = cv2.GaussianBlur((np.abs(field_full) <= 0.028).astype(np.uint8) * 255, (0, 0), 1.2)
    frame[:, :, :] = np.clip(base, 0, 255).astype(np.uint8)
    add_mask(frame, node_mask, full_mask_bbox(node_mask), (184, 224, 219), 0.080 * field_alpha, glow=0.006)


def render_beauty_v004(
    field_norm: np.ndarray,
    features: list[FeatureRecord],
    sources: list[WaveSource],
    spec: LoopSpec,
    time_seconds: float,
) -> np.ndarray:
    frame = canvas()
    field_alpha, primitive_alpha = temporal_levels(time_seconds)
    negative_cutout = spec.key == "negative_space_silhouette"
    if negative_cutout:
        render_surface_silhouette(frame, field_norm, field_alpha)
    else:
        draw_scalar_field_beauty(frame, field_norm, alpha=field_alpha)
        draw_nodal_band(frame, field_norm, spec.node_epsilon, alpha=0.055 * field_alpha)
    ordered = sorted(features, key=feature_score)
    for feature in ordered:
        alpha = primitive_alpha * feature.strength * (0.72 + 0.28 * feature.confidence)
        if feature.polarity == "negative" and not negative_cutout:
            alpha *= 0.84
        draw_feature(frame, feature, alpha, negative_cutout=negative_cutout)
    if spec.key == "raindrop_wavefront_crescents" and primitive_alpha > 0.01:
        draw_source_points(frame, sources, time_seconds, labels=False, alpha=0.12 * primitive_alpha)
    return frame


def feature_debug_layer(features: list[FeatureRecord], title: str) -> np.ndarray:
    frame = canvas()
    for idx, feature in enumerate(features):
        color = DEBUG_CLASS_COLORS.get(feature.primitive_class, DIM_TEAL)
        if feature.closed:
            draw_points_fill(frame, feature.raw_points, color, alpha=0.28, glow=0.008)
            draw_points_outline(frame, feature.raw_points, color, alpha=0.70, thickness=2, closed=True)
            draw_points_outline(frame, feature.styled_points, IVORY, alpha=0.42, thickness=1, closed=True)
        else:
            draw_tapered_polyline(frame, feature.raw_points, color, alpha=0.62, max_thickness=5)
            draw_tapered_polyline(frame, feature.styled_points, IVORY, alpha=0.40, max_thickness=2)
        cx, cy = feature.centroid_px
        draw_text(frame, f"{idx}:{feature.primitive_subtype}", (int(cx) + 8, int(cy)), LABEL, scale=0.30)
    draw_text(frame, title, (42, 56), LABEL, scale=0.58)
    draw_text(frame, "debug colors only: raw source geometry with cleaned overlay", (42, 84), LABEL, scale=0.38)
    draw_class_key(frame)
    return frame


def legibility_test_sheet(
    field_norm: np.ndarray,
    result: ExtractionResult,
    features: list[FeatureRecord],
    beauty: np.ndarray,
    spec: LoopSpec,
    title: str,
) -> np.ndarray:
    left = grayscale_layer(field_norm, f"{title} raw field")
    middle = classes_layer(result.cells, f"{title} extracted cells")
    for feature in features:
        color = DEBUG_CLASS_COLORS.get(feature.primitive_class, DIM_TEAL)
        if feature.closed:
            draw_points_outline(middle, feature.raw_points, color, alpha=0.75, thickness=2, closed=True)
        else:
            draw_tapered_polyline(middle, feature.raw_points, color, alpha=0.85, max_thickness=5)
    right = beauty.copy()
    for idx, feature in enumerate(features[:20]):
        cx, cy = feature.centroid_px
        draw_text(
            right,
            f"{idx} {feature.primitive_class}",
            (int(cx) + 8, int(cy)),
            LABEL,
            scale=0.31,
        )
    draw_text(right, f"{title} primitives + labels", (42, 56), LABEL, scale=0.58)
    thumbs = [
        cv2.resize(left, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(middle, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(right, (640, 360), interpolation=cv2.INTER_AREA),
    ]
    return cv2.hconcat(thumbs)


def crop_feature_view(
    base: np.ndarray,
    feature: FeatureRecord,
    *,
    raw: bool,
    size: tuple[int, int] = (300, 168),
) -> np.ndarray:
    points = feature.raw_points if raw else feature.styled_points
    x0f, y0f, x1f, y1f = point_bounds(points, pad=55.0)
    cx = (x0f + x1f) * 0.5
    cy = (y0f + y1f) * 0.5
    aspect = size[0] / size[1]
    width = max(x1f - x0f, (y1f - y0f) * aspect, 180.0)
    height = width / aspect
    x0 = int(max(0, min(W - width, cx - width * 0.5)))
    y0 = int(max(0, min(H - height, cy - height * 0.5)))
    x1 = int(min(W, x0 + width))
    y1 = int(min(H, y0 + height))
    crop = base[y0:y1, x0:x1].copy()
    local = points.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    local_i = np.round(local).astype(np.int32).reshape(-1, 1, 2)
    if raw:
        color = DEBUG_CLASS_COLORS.get(feature.primitive_class, PALE_BLUE)
        bgr = (color[2], color[1], color[0])
        if feature.closed:
            cv2.polylines(crop, [local_i], True, bgr, 2, lineType=cv2.LINE_AA)
        else:
            cv2.polylines(crop, [local_i], False, bgr, 4, lineType=cv2.LINE_AA)
    else:
        ivory_bgr = (IVORY[2], IVORY[1], IVORY[0])
        if feature.closed:
            fill = BEAUTY_FILL_COLORS.get(feature.primitive_class, PALE_BLUE)
            overlay = crop.copy()
            cv2.fillPoly(overlay, [local_i], (fill[2], fill[1], fill[0]), lineType=cv2.LINE_AA)
            cv2.addWeighted(overlay, 0.22, crop, 0.78, 0, dst=crop)
            cv2.polylines(crop, [local_i], True, ivory_bgr, 3, lineType=cv2.LINE_AA)
        else:
            cv2.polylines(crop, [local_i], False, (PALE_BLUE[2], PALE_BLUE[1], PALE_BLUE[0]), 6, lineType=cv2.LINE_AA)
    return cv2.resize(crop, size, interpolation=cv2.INTER_AREA)


def make_honesty_check(
    spec: LoopSpec,
    field_norm: np.ndarray,
    features: list[FeatureRecord],
    beauty: np.ndarray,
) -> Path:
    stem = Path(spec.filename).stem
    gray = np.clip((field_norm * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    raw_base = cv2.cvtColor(cv2.resize(gray, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_GRAY2BGR)
    selected = sorted(features, key=feature_score, reverse=True)[:5]
    rows: list[np.ndarray] = []
    header = np.zeros((70, 760, 3), dtype=np.uint8)
    draw_text(header, f"{stem} honesty check: raw field source beside cleaned render", (18, 32), LABEL, scale=0.48)
    draw_text(header, "Each row is one rendered primitive. v004 gate uses IoU and boundary-distance checks.", (18, 56), LABEL, scale=0.34)
    rows.append(header)
    for idx, feature in enumerate(selected):
        raw_crop = crop_feature_view(raw_base, feature, raw=True)
        styled_crop = crop_feature_view(beauty, feature, raw=False)
        label = np.zeros((168, 160, 3), dtype=np.uint8)
        draw_text(label, f"{idx} {feature.primitive_class}", (10, 28), LABEL, scale=0.38)
        draw_text(label, feature.feature_type, (10, 54), LABEL, scale=0.30)
        draw_text(label, feature.render_policy, (10, 80), LABEL, scale=0.30)
        draw_text(label, f"IoU {feature.metrics.get('iou', 0):.2f}", (10, 106), LABEL, scale=0.30)
        draw_text(label, f"d {feature.metrics.get('mean_boundary_distance_px', 0):.1f}px", (10, 132), LABEL, scale=0.30)
        rows.append(cv2.hconcat([label, raw_crop, styled_crop]))
    while len(rows) < 6:
        rows.append(np.zeros((168, 760, 3), dtype=np.uint8))
    sheet = cv2.vconcat(rows)
    path = HONESTY_DIR / f"{stem}_honesty_check.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_validation_sheet(samples: list[tuple[LoopSpec, FeatureRecord, np.ndarray, np.ndarray]]) -> Path:
    rows: list[np.ndarray] = []
    header = np.zeros((76, 960, 3), dtype=np.uint8)
    draw_text(header, "cymatic_field_topology_v004 raw-contour-vs-stylized validation", (18, 34), LABEL, scale=0.50)
    draw_text(header, "Raw source geometry is left; cleaned render is right. Fallback rows preserve raw when the gate fails.", (18, 60), LABEL, scale=0.34)
    rows.append(header)
    for idx, (spec, feature, raw_base, beauty) in enumerate(samples[:16]):
        raw_crop = crop_feature_view(raw_base, feature, raw=True, size=(330, 186))
        styled_crop = crop_feature_view(beauty, feature, raw=False, size=(330, 186))
        label = np.zeros((186, 300, 3), dtype=np.uint8)
        draw_text(label, f"{idx:02d} {Path(spec.filename).stem}", (10, 28), LABEL, scale=0.32)
        draw_text(label, feature.primitive_subtype, (10, 54), LABEL, scale=0.29)
        draw_text(label, f"class {feature.primitive_class}", (10, 80), LABEL, scale=0.29)
        draw_text(label, f"source {feature.feature_type}", (10, 106), LABEL, scale=0.29)
        draw_text(label, f"IoU {feature.metrics.get('iou', 0):.2f}", (10, 132), LABEL, scale=0.29)
        draw_text(label, f"dist {feature.metrics.get('mean_boundary_distance_px', 0):.1f}px", (10, 158), LABEL, scale=0.29)
        rows.append(cv2.hconcat([label, raw_crop, styled_crop]))
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "raw_contour_vs_stylized_validation_v004.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def feature_points_sample(points: np.ndarray, max_points: int = 28) -> list[list[float]]:
    sampled = sample_points(points, max_points=max_points)
    return [[round(float(x), 2), round(float(y), 2)] for x, y in sampled]


def feature_to_audit(
    feature: FeatureRecord,
    spec: LoopSpec,
    frame_index: int,
    time_seconds: float,
) -> dict[str, object]:
    source_cell = feature.source_cell
    if source_cell is not None:
        source_cell_bounds = point_bounds(full_points_from_contour(source_cell.contour), pad=0.0)
        source_cell_centroid: list[float] | None = [
            round(source_cell.centroid_px[0], 2),
            round(source_cell.centroid_px[1], 2),
        ]
        source_cell_id = source_cell.cell_id
        source_cell_orientation = point_orientation(full_points_from_contour(source_cell.contour))
    else:
        source_cell_bounds = None
        source_cell_centroid = None
        source_cell_id = None
        source_cell_orientation = None
    return {
        "primitive_id": feature.feature_id,
        "clip": spec.filename,
        "frame": frame_index,
        "time_seconds": round(time_seconds, 4),
        "primitive_class": feature.primitive_class,
        "primitive_subtype": feature.primitive_subtype,
        "source_feature_type": feature.feature_type,
        "source_feature_ids": list(feature.source_ids),
        "source_cell_id": source_cell_id,
        "source_cell_centroid": source_cell_centroid,
        "source_cell_bounds": [round(float(v), 2) for v in source_cell_bounds] if source_cell_bounds else None,
        "source_cell_orientation": round(float(source_cell_orientation), 5) if source_cell_orientation is not None else None,
        "source_feature_centroid": [round(feature.centroid_px[0], 2), round(feature.centroid_px[1], 2)],
        "source_feature_bounds": [round(float(v), 2) for v in feature.bounds_px],
        "source_feature_orientation": round(feature.orientation_rad, 5),
        "polarity": feature.polarity,
        "closed": feature.closed,
        "confidence": round(feature.confidence, 4),
        "strength": round(feature.strength, 4),
        "render_policy": feature.render_policy,
        "geometry_gate": {key: round(float(value), 5) for key, value in feature.metrics.items()},
        "raw_points_sample_px": feature_points_sample(feature.raw_points),
        "styled_points_sample_px": feature_points_sample(feature.styled_points),
        "cultural_status": "internal_austin_review_needed",
    }


def sixfold_sun_sources(phase: float) -> list[WaveSource]:
    center = (960.0, 540.0)
    return [
        WaveSource(
            "sixfold_center",
            center[0],
            center[1],
            1.15,
            SELECTED_SUN_WAVELENGTH,
            1.0 / DURATION_SECONDS,
            0.0,
            980.0,
            (0.0, 0.0),
            0.0,
            DURATION_SECONDS,
            6,
            "sixfold_radial",
            SELECTED_SUN_ALPHA,
        )
    ]


def fixed_two_source_sources(phase: float) -> list[WaveSource]:
    center = (960.0, 540.0)
    sep = 430.0
    sway = 8.0 * math.sin(TAU * phase)
    freq = 1.0 / DURATION_SECONDS
    return [
        WaveSource("left_source", center[0] - sep * 0.5, center[1] - sway, 1.0, 204.0, freq, 0.0, 1140.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 2, "fixed_radial"),
        WaveSource("right_source", center[0] + sep * 0.5, center[1] + sway, 1.0, 204.0, freq, math.pi * 0.04, 1140.0, (0.0, 0.0), 0.0, DURATION_SECONDS, 2, "fixed_radial"),
    ]


def negative_space_sources(phase: float) -> list[WaveSource]:
    return raindrop_sources(phase)


LOOPS = (
    LoopSpec(
        key="raindrop_wavefront_crescents",
        filename="raindrop_wavefront_crescents_v004.mp4",
        description="Multiple impact sources emit extracted wavefront arcs. Impact circles are positive source forms; crescent arcs are open iso-line segments with tapered stroke weight.",
        source_builder=raindrop_sources,
        threshold_percentile=72.0,
        min_area=170.0,
        max_area=76000.0,
        max_cells=44,
        node_epsilon=0.038,
        blur_sigma=1.55,
        compound_policy="suppress",
    ),
    LoopSpec(
        key="two_source_lens_cells",
        filename="two_source_lens_cells_v004.mp4",
        description="Fixed two-source interference with actual lens/crescent threshold cells preserved as lens-like geometry, not forced into moon crescents.",
        source_builder=fixed_two_source_sources,
        threshold_percentile=74.0,
        min_area=220.0,
        max_area=68000.0,
        max_cells=34,
        node_epsilon=0.032,
        blur_sigma=1.20,
        compound_policy="suppress",
    ),
    LoopSpec(
        key="sun_raw_scallop_trigons",
        filename="sun_raw_scallop_trigons_v004.mp4",
        description="Single center source with sixfold angular modulation. Only raw outward scallop/ray cells are rendered; no generic triangle templates.",
        source_builder=sixfold_sun_sources,
        threshold_percentile=80.0,
        min_area=190.0,
        max_area=76000.0,
        max_cells=32,
        node_epsilon=0.030,
        blur_sigma=1.10,
        compound_policy="suppress",
    ),
    LoopSpec(
        key="negative_space_silhouette",
        filename="negative_space_silhouette_v004.mp4",
        description="The raindrop field is inverted into a solid water/surface silhouette, with source-traced wavefront crescents and cusp-like cells cut out as negative space.",
        source_builder=negative_space_sources,
        threshold_percentile=72.0,
        min_area=190.0,
        max_area=76000.0,
        max_cells=38,
        node_epsilon=0.038,
        blur_sigma=1.55,
        compound_policy="suppress",
    ),
)


def save_debug_bundle(
    spec: LoopSpec,
    frame: np.ndarray,
    field_norm: np.ndarray,
    result: ExtractionResult,
    features: list[FeatureRecord],
    sources: list[WaveSource],
    time_seconds: float,
) -> dict[str, Path]:
    stem = Path(spec.filename).stem
    paths: dict[str, Path] = {}
    beauty_path = MIDPOINT_DIR / f"{stem}_midpoint.png"
    cv2.imwrite(str(beauty_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    paths["beauty"] = beauty_path

    layers = {
        "scalar_field": grayscale_layer(field_norm, f"{stem} scalar field"),
        "nodal_lines": nodal_layer(field_norm, spec, f"{stem} nodal lines"),
        "positive_negative_regions": regions_layer(field_norm, result.threshold, spec, f"{stem} positive/negative regions"),
        "cell_class_colors": classes_layer(result.cells, f"{stem} classified cells"),
        "source_points": source_layer(field_norm, sources, time_seconds, f"{stem} source points"),
        "rendered_source_features": feature_debug_layer(features, f"{stem} rendered source features"),
        "legibility_test_frame": legibility_test_sheet(field_norm, result, features, frame, spec, stem),
    }
    for layer_name, layer in layers.items():
        path = DEBUG_DIR / f"{stem}_{layer_name}_midpoint.png"
        cv2.imwrite(str(path), layer, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        paths[layer_name] = path

    honesty_path = make_honesty_check(spec, field_norm, features, frame)
    paths["honesty_check"] = honesty_path

    thumbs = [cv2.resize(frame, (360, 202), interpolation=cv2.INTER_AREA)]
    labels = ["beauty"]
    for layer_name in [
        "scalar_field",
        "positive_negative_regions",
        "cell_class_colors",
        "rendered_source_features",
        "source_points",
    ]:
        thumbs.append(cv2.resize(layers[layer_name], (360, 202), interpolation=cv2.INTER_AREA))
        labels.append(layer_name)
    for thumb, label in zip(thumbs, labels, strict=True):
        draw_text(thumb, label, (12, 184), LABEL, scale=0.32)
    composite = cv2.hconcat(thumbs)
    composite_path = DEBUG_DIR / f"{stem}_debug_composite_midpoint.png"
    cv2.imwrite(str(composite_path), composite, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    paths["debug_composite"] = composite_path
    return paths


def make_contact_sheet(midpoints: list[tuple[LoopSpec, np.ndarray]]) -> Path:
    thumbs: list[np.ndarray] = []
    for spec, frame in midpoints:
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        draw_text(thumb, Path(spec.filename).stem, (14, 248), LABEL, scale=0.38)
        thumbs.append(thumb)
    sheet = cv2.vconcat([cv2.hconcat(thumbs[:2]), cv2.hconcat(thumbs[2:])])
    path = OUT_DIR / "cymatic_field_topology_v004_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_debug_contact_sheet() -> Path:
    rows: list[np.ndarray] = []
    layer_names = ["beauty", "scalar_field", "positive_negative_regions", "cell_class_colors", "rendered_source_features", "source_points"]
    for spec in LOOPS:
        stem = Path(spec.filename).stem
        images: list[np.ndarray] = []
        for layer_name in layer_names:
            if layer_name == "beauty":
                path = MIDPOINT_DIR / f"{stem}_midpoint.png"
            else:
                path = DEBUG_DIR / f"{stem}_{layer_name}_midpoint.png"
            img = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if img is None:
                raise RuntimeError(f"missing debug still {path}")
            thumb = cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA)
            draw_text(thumb, layer_name, (10, 164), LABEL, scale=0.29)
            images.append(thumb)
        row = cv2.hconcat(images)
        draw_text(row, stem, (10, 22), LABEL, scale=0.40)
        rows.append(row)
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "cymatic_field_topology_v004_debug_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_phase_contact_sheet() -> Path:
    sample_frames = [0, int(1.5 * FPS), LEGIBILITY_FRAME, int(4.5 * FPS), N_FRAMES - 1]
    rows: list[np.ndarray] = []
    for spec in LOOPS:
        video_path = OUT_DIR / spec.filename
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"could not open rendered video for phase sheet: {video_path}")
        thumbs: list[np.ndarray] = []
        for frame_index in sample_frames:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                capture.release()
                raise RuntimeError(f"could not read frame {frame_index} from {video_path}")
            thumb = cv2.resize(frame, (384, 216), interpolation=cv2.INTER_AREA)
            draw_text(thumb, f"f{frame_index:03d}", (14, 196), LABEL, scale=0.36)
            thumbs.append(thumb)
        capture.release()
        row = cv2.hconcat(thumbs)
        draw_text(row, Path(spec.filename).stem, (12, 24), LABEL, scale=0.40)
        rows.append(row)
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "cymatic_field_topology_v004_phase_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def create_sun_alpha_sweep() -> Path:
    panels: list[np.ndarray] = []
    for alpha in (0.30, 0.50, 0.70):
        source = WaveSource(
            "sixfold_center",
            960.0,
            540.0,
            1.15,
            SELECTED_SUN_WAVELENGTH,
            1.0 / DURATION_SECONDS,
            0.0,
            980.0,
            (0.0, 0.0),
            0.0,
            DURATION_SECONDS,
            6,
            "sixfold_radial",
            alpha,
        )
        probe_spec = next(item for item in LOOPS if item.key == "sun_raw_scallop_trigons")
        t = LEGIBILITY_FRAME / FPS
        field_norm = evaluate_field([source], t, probe_spec.blur_sigma)
        result = extract_cells(field_norm, [source], probe_spec, t, max_cells=48)
        features = build_sun_scallop_features(result, [source], probe_spec, t, LEGIBILITY_FRAME)
        frame = render_beauty_v004(field_norm, features, [source], probe_spec, t)
        panel = cv2.resize(frame, (560, 315), interpolation=cv2.INTER_AREA)
        draw_text(panel, f"alpha={alpha:.1f} rendered={len(features)}", (18, 290), LABEL, scale=0.42)
        panels.append(panel)
    sheet = cv2.hconcat(panels)
    path = OUT_DIR / "sun_alpha_sweep_v004.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def render_clip(spec: LoopSpec) -> tuple[np.ndarray, dict[str, object], list[dict[str, object]], list[tuple[LoopSpec, FeatureRecord, np.ndarray, np.ndarray]]]:
    writer = H264Writer(OUT_DIR / spec.filename, fps=FPS, size=(W, H))
    midpoint_frame: np.ndarray | None = None
    midpoint_field: np.ndarray | None = None
    midpoint_result: ExtractionResult | None = None
    midpoint_sources: list[WaveSource] | None = None
    midpoint_features: list[FeatureRecord] | None = None
    per_frame_counts: list[int] = []
    rendered_feature_counts: list[int] = []
    class_totals: Counter[str] = Counter()
    primitive_totals: Counter[str] = Counter()
    feature_type_totals: Counter[str] = Counter()
    threshold_values: list[float] = []
    audit_entries: list[dict[str, object]] = []

    for fi in range(N_FRAMES):
        phase = fi / N_FRAMES
        time_seconds = phase * DURATION_SECONDS
        sources = spec.source_builder(phase)
        field_norm = evaluate_field(sources, time_seconds, spec.blur_sigma)
        result = extract_cells(field_norm, sources, spec, time_seconds)
        features = build_features_for_frame(field_norm, result, sources, spec, time_seconds, fi)
        frame = render_beauty_v004(field_norm, features, sources, spec, time_seconds)
        writer.write(frame)

        per_frame_counts.append(len(result.cells))
        rendered_feature_counts.append(len(features))
        class_totals.update(result.counts_by_class)
        primitive_totals.update(feature.primitive_class for feature in features)
        feature_type_totals.update(feature.feature_type for feature in features)
        threshold_values.append(result.threshold)
        audit_entries.extend(feature_to_audit(feature, spec, fi, time_seconds) for feature in features)

        if fi == LEGIBILITY_FRAME:
            midpoint_frame = frame.copy()
            midpoint_field = field_norm.copy()
            midpoint_result = result
            midpoint_sources = sources
            midpoint_features = list(features)

        if (fi + 1) % 24 == 0:
            print(f"  {spec.filename} {fi + 1}/{N_FRAMES}", flush=True)

    writer.close()
    if (
        midpoint_frame is None
        or midpoint_field is None
        or midpoint_result is None
        or midpoint_sources is None
        or midpoint_features is None
    ):
        raise RuntimeError(f"no midpoint captured for {spec.filename}")

    save_debug_bundle(spec, midpoint_frame, midpoint_field, midpoint_result, midpoint_features, midpoint_sources, LEGIBILITY_FRAME / FPS)
    gray = np.clip((midpoint_field * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    raw_base = cv2.cvtColor(cv2.resize(gray, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_GRAY2BGR)
    validation_samples = [
        (spec, feature, raw_base, midpoint_frame)
        for feature in sorted(midpoint_features, key=feature_score, reverse=True)[:5]
    ]
    fallback_count = sum(1 for entry in audit_entries if float(entry["geometry_gate"].get("used_raw_fallback", 0.0)) > 0.5)
    summary: dict[str, object] = {
        "filename": spec.filename,
        "description": spec.description,
        "frames": N_FRAMES,
        "fps": FPS,
        "dimensions": [W, H],
        "legibility_still_frame": LEGIBILITY_FRAME,
        "legibility_still_time_seconds": round(LEGIBILITY_FRAME / FPS, 3),
        "threshold_percentile": spec.threshold_percentile,
        "midpoint_threshold": round(midpoint_result.threshold, 5),
        "cells_per_frame_min": min(per_frame_counts),
        "cells_per_frame_max": max(per_frame_counts),
        "cells_per_frame_mean": round(float(np.mean(per_frame_counts)), 2),
        "rendered_features_per_frame_min": min(rendered_feature_counts),
        "rendered_features_per_frame_max": max(rendered_feature_counts),
        "rendered_features_per_frame_mean": round(float(np.mean(rendered_feature_counts)), 2),
        "class_totals": dict(class_totals),
        "primitive_totals": dict(primitive_totals),
        "feature_type_totals": dict(feature_type_totals),
        "threshold_min": round(min(threshold_values), 5),
        "threshold_max": round(max(threshold_values), 5),
        "geometry_gate_raw_fallback_count": fallback_count,
        "audit_entries": len(audit_entries),
        "midpoint_sources": [source_to_json(source) for source in midpoint_sources],
        "midpoint_cells": [cell_to_json(cell) for cell in midpoint_result.cells[:80]],
        "midpoint_rendered_features": [
            {
                "primitive_id": feature.feature_id,
                "primitive_class": feature.primitive_class,
                "primitive_subtype": feature.primitive_subtype,
                "source_feature_type": feature.feature_type,
                "source_feature_ids": list(feature.source_ids),
                "render_policy": feature.render_policy,
                "geometry_gate": feature.metrics,
            }
            for feature in midpoint_features
        ],
    }
    return midpoint_frame, summary, audit_entries, validation_samples


def write_audit_json(audit_entries: list[dict[str, object]]) -> Path:
    path = OUT_DIR / "primitive_audit_v004.json"
    packet = {
        "renderer": "scripts/cymatic_field_topology_v004.py",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "rule": "Every rendered primitive maps to a source field feature: threshold cell, wavefront segment, cusp region, or field source impact.",
        "entries": audit_entries,
    }
    path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    return path


def write_manifest(
    summaries: list[dict[str, object]],
    contact_sheet: Path,
    debug_contact_sheet: Path,
    phase_contact_sheet: Path,
    validation_sheet: Path,
    audit_json: Path,
    alpha_sweep: Path,
) -> Path:
    manifest = {
        "renderer": "scripts/cymatic_field_topology_v004.py",
        "created_for": "Salish Sea Dreaming Phase 2 internal contour-respecting wave-geometry pass",
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "dimensions": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "legibility_still_frame": LEGIBILITY_FRAME,
        "legibility_still_time_seconds": round(LEGIBILITY_FRAME / FPS, 3),
        "field_grid": [FW, FH],
        "field_formula": "F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i - omega_i*t + phase_i)*decay(distance)*envelope(t), with sixfold scene using (1 + alpha*cos(6*theta)).",
        "selected_sun_parameters": {
            "alpha": SELECTED_SUN_ALPHA,
            "wavelength": SELECTED_SUN_WAVELENGTH,
            "tested_alpha_values": [0.3, 0.5, 0.7],
        },
        "temporal_structure": {
            "0.0-1.0": "full scalar field visible; primitives hidden",
            "1.0-2.0": "field fades toward 30%; source-traced primitives emerge",
            "2.0-4.5": "field near 10%; contour-respecting primitives fully readable",
            "4.5-6.0": "primitives dissolve while field returns for loop closure",
        },
        "geometry_gate": {
            "closed_contours": "smooth/simplify only accepted when IoU >= 0.68 and mean boundary distance <= 14 px",
            "open_arcs": "smooth/simplify only accepted when IoU >= 0.54, mean boundary distance <= 10 px, and endpoints stay close",
            "fallback": "raw source geometry is rendered if a cleaned candidate fails the gate",
        },
        "outputs": {
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "debug_sheet": str(debug_contact_sheet.relative_to(ROOT)),
            "phase_contact_sheet": str(phase_contact_sheet.relative_to(ROOT)),
            "raw_contour_vs_stylized_validation": str(validation_sheet.relative_to(ROOT)),
            "primitive_audit_json": str(audit_json.relative_to(ROOT)),
            "sun_alpha_sweep": str(alpha_sweep.relative_to(ROOT)),
            "honesty_checks_dir": str(HONESTY_DIR.relative_to(ROOT)),
        },
        "clips": summaries,
    }
    path = OUT_DIR / "cymatic_field_topology_v004_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    rows = "\n".join(
        f"- `{summary['filename']}`: {summary['description']} "
        f"Midpoint rendered features: {len(summary['midpoint_rendered_features'])}; "
        f"primitive totals: {summary['primitive_totals']}; source feature totals: {summary['feature_type_totals']}."
        for summary in summaries
    )
    readme = f"""# Cymatic Field Topology v004 - 2026-05-20

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim.

## Purpose

v003 proved that canonical primitives could be mapped to field cells, but the
beauty result looked like generic icons pasted over water. v004 is a
contour-respecting wave-geometry pass. The scalar field still provides source
position, interference, timing, scale, and orientation, but the renderer now
starts from raw extracted cells, iso-line wavefront arcs, or naturally emerging
cusp regions. It smooths or simplifies only when the cleaned form stays
recognizably tied to the raw source geometry.

## Honest Framing

This engine produces wave-motion geometry. Coast Salish primitives are living
cultural forms; this packet does not claim to reconstruct or validate Coast
Salish design. Austin's teaching and public artist/education sources support a
pebble/ripple relationship for circle/crescent/trigon-like flow, but the
trigon-as-wave-cusp treatment remains a working visual hypothesis. Austin review
is required before any cultural framing or public use.

## Method

- Source tuple model:
  `(x, y, amplitude, wavelength, frequency, phase, decay, velocity, birth_time, lifetime, symmetry_order, mode, angular_alpha)`.
- Field:
  `F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i - omega_i*t + phase_i)*decay(distance)*envelope(t)`.
- The sun study uses one center source with:
  `F=A*cos(2*pi*r/lambda - omega*t)*(1 + alpha*cos(6*theta))`.
  Tested alpha values: 0.3, 0.5, 0.7. Selected alpha: {SELECTED_SUN_ALPHA};
  selected wavelength: {SELECTED_SUN_WAVELENGTH}.
- Closed cells are threshold-connected regions. Open wavefront crescents are
  extracted from iso-line segments, not placed templates.
- Cleaned contours are gated by area/IoU and boundary-distance checks. If the
  cleaned version drifts too far, v004 renders the raw source geometry or
  suppresses the feature.
- Vesica/lens-like cells remain lens/crescent subtypes. They are not forced
  into moon-crescent templates.
- The negative-space study cuts source-traced features out of a solid
  water/surface silhouette.

## Temporal Structure

- 0.0-1.0s: full scalar field visible, no primitives.
- 1.0-2.0s: field fades toward 30%; source-traced primitives emerge.
- 2.0-4.5s: field near 10%; contour-respecting primitives are most readable.
- 4.5-6.0s: primitives dissolve and the field returns.

Legibility stills are sampled at frame {LEGIBILITY_FRAME} ({LEGIBILITY_FRAME / FPS:.2f}s).

## Clips

{rows}

## Evidence Bundle

- 4 MP4 loops, 1920x1080, 24 fps, 6 seconds, 144 frames.
- Midpoint stills in `midpoint_stills/`.
- Honesty-check frames in `honesty_checks/`, each showing five rendered
  primitives beside their raw field source geometry.
- Debug stills in `debug_stills/` for scalar field, nodal lines,
  positive/negative regions, class colors, source points, rendered source
  features, and legibility test frames.
- Contact sheet: `cymatic_field_topology_v004_contact_sheet.png`.
- Debug sheet: `cymatic_field_topology_v004_debug_sheet.png`.
- Phase sheet: `cymatic_field_topology_v004_phase_contact_sheet.png`.
- Raw-contour-vs-stylized validation:
  `raw_contour_vs_stylized_validation_v004.png`.
- Primitive audit JSON: `primitive_audit_v004.json`.
- Manifest: `cymatic_field_topology_v004_manifest.json`.

## Honest Verdict

v004 is intentionally less iconographic than v003. The rendered forms should
read as cleaned wave geometry rather than generic pasted symbols. The raindrop
and negative-space studies are the strongest fit because the open wavefront
arcs visibly trace to water/ripple motion. The two-source lens study preserves
actual vesica/lens geometry instead of forcing a moon-crescent convention. The
sixfold sun study is still the riskiest cultural read: it demonstrates raw
scallop/ray cells from angular modulation, but the trigon-as-wave-cusp idea
remains a visual hypothesis for Austin review, not a claim.

## Boundaries

No salmon, birds, figures, Austin source artwork, exact Austin motif geometry,
public-readiness claim, traditional-meaning claim, or Austin-approval claim is
included in this packet.

Renderer:

`scripts/cymatic_field_topology_v004.py`
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render cymatic field topology v004 packet.")
    parser.add_argument(
        "--clip",
        choices=["all", *[spec.key for spec in LOOPS]],
        default="all",
        help="Render one clip for iteration, or all clips for the final packet.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    HONESTY_DIR.mkdir(parents=True, exist_ok=True)

    selected_loops = list(LOOPS if args.clip == "all" else [spec for spec in LOOPS if spec.key == args.clip])
    summaries: list[dict[str, object]] = []
    midpoints: list[tuple[LoopSpec, np.ndarray]] = []
    all_audit_entries: list[dict[str, object]] = []
    validation_samples: list[tuple[LoopSpec, FeatureRecord, np.ndarray, np.ndarray]] = []
    alpha_sweep = create_sun_alpha_sweep() if args.clip == "all" else OUT_DIR / "sun_alpha_sweep_v004.png"
    for spec in selected_loops:
        print(f"Rendering {spec.filename}", flush=True)
        midpoint, summary, audit_entries, samples = render_clip(spec)
        summaries.append(summary)
        midpoints.append((spec, midpoint))
        all_audit_entries.extend(audit_entries)
        validation_samples.extend(samples)

    if args.clip == "all":
        contact_sheet = make_contact_sheet(midpoints)
        debug_contact_sheet = make_debug_contact_sheet()
        phase_contact_sheet = make_phase_contact_sheet()
        validation_sheet = make_validation_sheet(validation_samples)
        audit_json = write_audit_json(all_audit_entries)
        manifest = write_manifest(summaries, contact_sheet, debug_contact_sheet, phase_contact_sheet, validation_sheet, audit_json, alpha_sweep)
        readme = write_readme(summaries)
        print(f"Wrote {contact_sheet}")
        print(f"Wrote {debug_contact_sheet}")
        print(f"Wrote {phase_contact_sheet}")
        print(f"Wrote {validation_sheet}")
        print(f"Wrote {audit_json}")
        print(f"Wrote {manifest}")
        print(f"Wrote {readme}")
        print(f"Wrote cymatic field topology v004 packet to {OUT_DIR}")
    else:
        print(f"Wrote clip iteration output to {OUT_DIR}")


if __name__ == "__main__":
    main()
