#!/usr/bin/env python3.11
"""
Cymatic field topology v002.

Internal scalar-field / standing-wave topology probe for Salish Sea Dreaming
Phase 2. This lane keeps the v001 scalar-field source engine. It does not
hand-place primitive icons. v002 is a visual-legibility pass over connected
threshold regions, with class-balanced selection, temporal persistence, and
beauty rendering that differentiates classes through boundary language.

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
    / "cymatic_field_topology_v002_2026-05-20"
)
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"

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
LEGIBILITY_FRAME = int(3.75 * FPS)
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
        blur = max(7, int(max(mask.shape) * 0.08) | 1)
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
    field_full = cv2.resize(field_norm, (W, H), interpolation=cv2.INTER_CUBIC)
    positive = np.clip(field_full, 0.0, 1.0)
    negative = np.clip(-field_full, 0.0, 1.0)
    amplitude = np.clip(np.abs(field_full), 0.0, 1.0) ** 0.74
    pos_color = rgb_to_bgr((226, 222, 190))
    neg_color = rgb_to_bgr((80, 172, 186))
    base = frame.astype(np.float32)
    field_rgb = (
        positive[..., None] * pos_color
        + negative[..., None] * neg_color
    ) * amplitude[..., None]
    base += field_rgb * (0.54 * alpha)
    fine = (np.abs(field_full) <= 0.026).astype(np.uint8) * 255
    frame[:, :, :] = np.clip(base, 0, 255).astype(np.uint8)
    add_mask(frame, fine, full_mask_bbox(fine), (120, 204, 204), 0.050 * alpha, glow=0.006 * alpha)


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
            "medium",
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
        field += (source.amplitude * env) * np.cos(phase, dtype=np.float32) * decay

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
    add_mask(frame, node_full, full_mask_bbox(node_full), NODE_RGB, alpha, glow=0.025)


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Render cymatic field topology v002 packet.")
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

    selected_loops = list(LOOPS if args.clip == "all" else [spec for spec in LOOPS if spec.key == args.clip])
    summaries: list[dict[str, object]] = []
    midpoints: list[tuple[LoopSpec, np.ndarray]] = []
    for spec in selected_loops:
        print(f"Rendering {spec.filename}", flush=True)
        midpoint, summary = render_clip(spec)
        summaries.append(summary)
        midpoints.append((spec, midpoint))

    if args.clip == "all":
        contact_sheet = make_contact_sheet(midpoints)
        debug_contact_sheet = make_debug_contact_sheet()
        phase_contact_sheet = make_phase_contact_sheet()
        manifest = write_manifest(summaries, contact_sheet, debug_contact_sheet, phase_contact_sheet)
        readme = write_readme(summaries)
        print(f"Wrote {contact_sheet}")
        print(f"Wrote {debug_contact_sheet}")
        print(f"Wrote {phase_contact_sheet}")
        print(f"Wrote {manifest}")
        print(f"Wrote {readme}")
        print(f"Wrote cymatic field topology v002 packet to {OUT_DIR}")
    else:
        print(f"Wrote clip iteration output to {OUT_DIR}")


if __name__ == "__main__":
    main()
