#!/usr/bin/env python3
"""
Abstract cymatic composition v001.

Standalone procedural cymatic/water composition for the internal Resolume video
library. This renderer uses generated scalar-wave fields plus abstract
source-derived raster masks only. It does not load Austin artwork, SVGs,
motifs, atoms, or any cultural reference assets.

Boundary: generated abstract cymatic/water geometry only. Not Coast Salish.
Not Austin-derived. No public/show/projector/sponsor/social use until
separately approved for the production context.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / "abstract_cymatic_composition_v001_2026-05-22"
STILLS_DIR = OUT_DIR / "stills"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

PROJECT = "abstract_cymatic_composition_v001"
FPS = 24
DURATION_SECONDS = 80.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

UHD_SIZE = (3840, 2160)
DRAFT_SIZE = (1920, 1080)

DEEP = (0, 5, 7)
DARK_WATER = (3, 18, 24)
INK = (0, 7, 9)
DEEP_TEAL = (18, 73, 80)
TEAL = (52, 151, 154)
MUTED_TEAL = (76, 135, 136)
ICE_BLUE = (155, 222, 230)
WARM_CREAM = (235, 224, 190)
SOFT_GOLD = (246, 197, 92)
AMBER = (220, 120, 64)
LABEL = (226, 234, 230)

KEY_STILLS = (
    ("initial_field", 0.0),
    ("central_origin", 14.0),
    ("first_crescent_ring", 25.0),
    ("second_ring", 40.0),
    ("peak_attenuation_pressure", 56.0),
    ("return_loop_point", 80.0),
)

CONTACT_TIMES = (0.0, 6.0, 10.0, 14.0, 20.0, 25.0, 32.0, 40.0, 48.0, 56.0, 64.0, 70.0, 74.0, 78.0, 80.0)


@dataclass(frozen=True)
class WaveSource:
    source_id: str
    ring: str
    angle_rad: float
    base_radius_px: float
    amplitude: float
    wavelength_px: float
    frequency_cycles: int
    phase_offset_rad: float
    decay_px: float
    orbit_cycles: int
    radial_cycles: int
    radial_jitter_px: float
    angular_jitter_rad: float


@dataclass(frozen=True)
class RenderConfig:
    width: int
    height: int
    work_width: int
    work_height: int
    field_width: int
    field_height: int
    fps: int
    duration_seconds: float
    frame_count: int


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
            "17",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.path = path
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        stderr = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with code {code}\n{stderr[-4000:]}")


class AbstractCymaticRenderer:
    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        self.cx = config.work_width * 0.5
        self.cy = config.work_height * 0.5
        self.scale = config.work_height / 1080.0
        self.sources = self._make_sources()

        y, x = np.mgrid[0 : config.work_height, 0 : config.work_width].astype(np.float32)
        self.x = x
        self.y = y
        self.dist = np.sqrt((x - self.cx) ** 2 + (y - self.cy) ** 2)
        self.theta = np.arctan2(y - self.cy, x - self.cx).astype(np.float32)

        fy = (np.arange(config.field_height, dtype=np.float32) + 0.5) * (config.height / config.field_height) / (config.height / config.work_height)
        fx = (np.arange(config.field_width, dtype=np.float32) + 0.5) * (config.width / config.field_width) / (config.width / config.work_width)
        self.fx, self.fy = np.meshgrid(fx, fy)
        self.field_edge_window = self._edge_window(self.fx, self.fy, config.field_width, config.field_height, config.work_width, config.work_height)

        self.field_boundary = self._radial_falloff(485.0 * self.scale, 95.0 * self.scale)
        self.field_boundary_small = cv2.resize(self.field_boundary, (config.field_width, config.field_height), interpolation=cv2.INTER_AREA)
        self.center_mask = self._circle_mask(self.cx, self.cy, 122.0 * self.scale, 30.0 * self.scale)
        self.center_core = self._circle_mask(self.cx, self.cy, 64.0 * self.scale, 22.0 * self.scale)
        self.center_ring = self._ring_mask(132.0 * self.scale, 8.0 * self.scale, 5.0 * self.scale)
        self.first_crescents, self.first_edges = self._make_crescent_ring(8, 245.0 * self.scale, 132.0 * self.scale, 0.47, inward=True)
        self.second_crescents, self.second_edges = self._make_crescent_ring(12, 420.0 * self.scale, 166.0 * self.scale, 0.43, inward=False)
        self.trigon_masks, self.trigon_edges = self._make_pressure_gaps(12, 415.0 * self.scale, 590.0 * self.scale)
        self.nodal_ring_1 = self._ring_mask(250.0 * self.scale, 4.0 * self.scale, 2.8 * self.scale)
        self.nodal_ring_2 = self._ring_mask(420.0 * self.scale, 5.0 * self.scale, 3.4 * self.scale)

    def _make_sources(self) -> list[WaveSource]:
        s = self.scale
        sources = [
            WaveSource("origin_00", "center", 0.0, 0.0, 1.16, 238.0 * s, 8, 0.0, 860.0 * s, 0, 0, 0.0, 0.0)
        ]
        for idx in range(8):
            angle = -math.pi * 0.5 + TAU * idx / 8.0
            sources.append(
                WaveSource(
                    f"first_ring_{idx:02d}",
                    "first_crescent_ring",
                    angle,
                    245.0 * s,
                    0.86,
                    246.0 * s,
                    8,
                    0.19 * idx,
                    760.0 * s,
                    1 + (idx % 2),
                    2 + (idx % 3),
                    18.0 * s,
                    0.030,
                )
            )
        for idx in range(12):
            angle = -math.pi * 0.5 + TAU * (idx + 0.5) / 12.0
            sources.append(
                WaveSource(
                    f"outer_ring_{idx:02d}",
                    "outer_crescent_pressure_ring",
                    angle,
                    420.0 * s,
                    0.70,
                    276.0 * s,
                    6,
                    0.31 * idx + 0.4,
                    920.0 * s,
                    1 + (idx % 3),
                    2 + (idx % 4),
                    24.0 * s,
                    0.026,
                )
            )
        return sources

    def _edge_window(self, gx: np.ndarray, gy: np.ndarray, fw: int, fh: int, ww: int, wh: int) -> np.ndarray:
        dist = np.minimum(np.minimum(gx, ww - gx), np.minimum(gy, wh - gy))
        return np_smoothstep(20.0 * self.scale, 110.0 * self.scale, dist).astype(np.float32)

    def _circle_mask(self, cx: float, cy: float, radius: float, soft_edge: float) -> np.ndarray:
        d = np.sqrt((self.x - cx) ** 2 + (self.y - cy) ** 2)
        alpha = np.clip((radius + soft_edge - d) / max(1e-6, soft_edge), 0.0, 1.0)
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

    def _radial_falloff(self, radius: float, soft_edge: float) -> np.ndarray:
        alpha = np.clip((radius + soft_edge - self.dist) / max(1e-6, soft_edge), 0.0, 1.0)
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

    def _ring_mask(self, radius: float, thickness: float, blur: float) -> np.ndarray:
        half = thickness * 0.5
        mask = np.where((self.dist >= radius - half) & (self.dist <= radius + half), 255, 0).astype(np.uint8)
        return cv2.GaussianBlur(mask, (0, 0), blur)

    def _make_crescent_ring(
        self,
        count: int,
        ring_radius: float,
        lobe_radius: float,
        subtract_shift: float,
        *,
        inward: bool,
    ) -> tuple[list[np.ndarray], list[np.ndarray]]:
        masks: list[np.ndarray] = []
        edges: list[np.ndarray] = []
        for idx in range(count):
            angle = -math.pi * 0.5 + TAU * idx / count
            cx = self.cx + ring_radius * math.cos(angle)
            cy = self.cy + ring_radius * math.sin(angle)
            sign = -1.0 if inward else 1.0
            sx = cx + sign * subtract_shift * lobe_radius * math.cos(angle)
            sy = cy + sign * subtract_shift * lobe_radius * math.sin(angle)
            outer = self._circle_mask(cx, cy, lobe_radius, 16.0 * self.scale).astype(np.float32) / 255.0
            subtract = self._circle_mask(sx, sy, lobe_radius * 0.96, 18.0 * self.scale).astype(np.float32) / 255.0
            annulus = self._radial_band(ring_radius - lobe_radius * 0.95, ring_radius + lobe_radius * 0.95, 42.0 * self.scale)
            crescent = np.clip((outer - 0.82 * subtract) * annulus, 0.0, 1.0)
            crescent = cv2.GaussianBlur((crescent * 255.0).astype(np.uint8), (0, 0), 1.2 * self.scale)
            masks.append(crescent)
            edges.append(mask_edge(crescent, kernel=max(5, round(7 * self.scale) | 1), blur=2.2 * self.scale))
        return masks, edges

    def _radial_band(self, inner: float, outer: float, soft_edge: float) -> np.ndarray:
        inner_alpha = np_smoothstep(inner - soft_edge, inner + soft_edge, self.dist)
        outer_alpha = 1.0 - np_smoothstep(outer - soft_edge, outer + soft_edge, self.dist)
        return np.clip(inner_alpha * outer_alpha, 0.0, 1.0).astype(np.float32)

    def _make_pressure_gaps(self, count: int, inner_radius: float, outer_radius: float) -> tuple[list[np.ndarray], list[np.ndarray]]:
        masks: list[np.ndarray] = []
        edges: list[np.ndarray] = []
        center = np.array([self.cx, self.cy], dtype=np.float32)
        for idx in range(count):
            angle = -math.pi * 0.5 + TAU * idx / count
            width_inner = 0.075
            width_outer = 0.145
            points = []
            for radius, da in (
                (inner_radius, -width_inner),
                (outer_radius, -width_outer),
                (outer_radius + 32.0 * self.scale, 0.0),
                (outer_radius, width_outer),
                (inner_radius, width_inner),
            ):
                points.append((round(center[0] + radius * math.cos(angle + da)), round(center[1] + radius * math.sin(angle + da))))
            mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
            cv2.fillConvexPoly(mask, np.array(points, dtype=np.int32), 255, lineType=cv2.LINE_AA)
            mask = cv2.GaussianBlur(mask, (0, 0), 7.0 * self.scale)
            masks.append(mask)
            edges.append(mask_edge(mask, kernel=max(5, round(9 * self.scale) | 1), blur=4.0 * self.scale))
        return masks, edges

    def source_positions(self, t: float) -> list[tuple[WaveSource, float, float, float]]:
        phase01 = (t % DURATION_SECONDS) / DURATION_SECONDS
        result = []
        for src in self.sources:
            angle = src.angle_rad + src.angular_jitter_rad * math.sin(TAU * (src.orbit_cycles * phase01 + src.phase_offset_rad / TAU))
            radius = src.base_radius_px + src.radial_jitter_px * math.sin(TAU * (src.radial_cycles * phase01 + src.phase_offset_rad / TAU))
            x = self.cx + radius * math.cos(angle)
            y = self.cy + radius * math.sin(angle)
            result.append((src, x, y, source_strength(src, t)))
        return result

    def evaluate_field(self, t: float) -> np.ndarray:
        t_loop = t % DURATION_SECONDS
        field = np.zeros((self.config.field_height, self.config.field_width), dtype=np.float32)
        for src, sx, sy, strength in self.source_positions(t):
            if strength <= 0.001:
                continue
            dx = self.fx - sx
            dy = self.fy - sy
            d = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
            phase = TAU * d / src.wavelength_px - TAU * (src.frequency_cycles / DURATION_SECONDS) * t_loop + src.phase_offset_rad
            wave = np.cos(phase, dtype=np.float32) * np.exp(-d / max(1.0, src.decay_px), dtype=np.float32)
            field += src.amplitude * strength * wave
        field *= self.field_edge_window
        field *= self.field_boundary_small.astype(np.float32) / 255.0
        field = cv2.GaussianBlur(field, (0, 0), 0.52 * self.scale)
        denom = float(np.percentile(np.abs(field), 99.4))
        if denom > 1e-6:
            field = np.clip(field / denom, -1.0, 1.0).astype(np.float32)
        return cv2.GaussianBlur(field, (0, 0), 0.30 * self.scale)

    def render_frame(self, t: float, *, output_size: bool = True) -> tuple[np.ndarray, dict[str, object]]:
        field_small = self.evaluate_field(t)
        field = cv2.resize(field_small, (self.config.work_width, self.config.work_height), interpolation=cv2.INTER_CUBIC)
        shaped = np.sign(field) * (np.abs(field) ** 0.88)
        levels = timeline_levels(t)

        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        blend_mask(frame, self.field_boundary, DARK_WATER, 0.78)

        pos = np.where(shaped > 0.075, self.field_boundary, 0).astype(np.uint8)
        neg = np.where(shaped < -0.060, self.field_boundary, 0).astype(np.uint8)
        nodes = np.where(np.abs(shaped) < 0.034, self.field_boundary, 0).astype(np.uint8)
        nodes = cv2.morphologyEx(nodes, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        region = cv2.bitwise_or(pos, neg)
        region_edge = cv2.morphologyEx(region, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

        blend_mask(frame, neg, TEAL, 0.42 + 0.10 * levels["outer"])
        blend_mask(frame, pos, WARM_CREAM, 0.30 + 0.16 * levels["first"])
        blend_mask(frame, nodes, INK, 0.48 + 0.10 * levels["pressure"])
        blend_mask(frame, region_edge, INK, 0.26)

        self._draw_water_breath(frame, t, 0.18 + 0.13 * levels["pressure"])
        self._draw_geometry(frame, levels, shaped)

        if output_size and (self.config.work_width, self.config.work_height) != (self.config.width, self.config.height):
            frame = cv2.resize(frame, (self.config.width, self.config.height), interpolation=cv2.INTER_CUBIC)

        info = {
            "time_seconds": round(t, 5),
            "levels": {k: round(v, 5) for k, v in levels.items()},
            "active_sources": sum(1 for _src, _x, _y, strength in self.source_positions(t) if strength > 0.01),
            "field_min": round(float(field_small.min()), 6),
            "field_max": round(float(field_small.max()), 6),
        }
        return frame, info

    def _draw_water_breath(self, frame: np.ndarray, t: float, alpha: float) -> None:
        if alpha <= 0.0:
            return
        overlay = np.zeros_like(frame)
        phase = (t / DURATION_SECONDS) % 1.0
        for idx, radius in enumerate((120, 245, 420, 585)):
            wobble = (7.0 + idx * 3.0) * self.scale * math.sin(TAU * ((idx + 1) * phase + idx * 0.17))
            cv2.circle(
                overlay,
                (round(self.cx), round(self.cy)),
                round(radius * self.scale + wobble),
                bgr(MUTED_TEAL if idx % 2 else ICE_BLUE),
                max(1, round(1.1 * self.scale)),
                lineType=cv2.LINE_AA,
            )
        cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)

    def _draw_geometry(self, frame: np.ndarray, levels: dict[str, float], shaped: np.ndarray) -> None:
        center_alpha = levels["center"]
        if center_alpha > 0.0:
            blend_mask_roi(frame, self.center_mask, DEEP_TEAL, 0.36 * center_alpha)
            blend_mask_roi(frame, self.center_core, INK, 0.38 * center_alpha)
            blend_mask_roi(frame, self.center_ring, SOFT_GOLD, 0.68 * center_alpha, glow=0.004 * center_alpha)

        first_alpha = levels["first"]
        if first_alpha > 0.0:
            for idx, mask in enumerate(self.first_crescents):
                breath = 0.82 + 0.18 * math.sin(TAU * (idx / 8.0 + levels["phase"]))
                blend_mask_roi(frame, mask, ICE_BLUE if idx % 2 else WARM_CREAM, 0.36 * first_alpha * breath)
                blend_mask_roi(frame, self.first_edges[idx], SOFT_GOLD, 0.26 * first_alpha)
            blend_mask_roi(frame, self.nodal_ring_1, SOFT_GOLD, 0.28 * first_alpha)

        outer_alpha = levels["outer"]
        if outer_alpha > 0.0:
            for idx, mask in enumerate(self.second_crescents):
                breath = 0.80 + 0.20 * math.sin(TAU * (idx / 12.0 - levels["phase"] * 0.5))
                blend_mask_roi(frame, mask, TEAL if idx % 2 else MUTED_TEAL, 0.42 * outer_alpha * breath)
                blend_mask_roi(frame, self.second_edges[idx], WARM_CREAM, 0.22 * outer_alpha)
            blend_mask_roi(frame, self.nodal_ring_2, MUTED_TEAL, 0.34 * outer_alpha)

        pressure_alpha = levels["pressure"]
        if pressure_alpha > 0.0:
            pressure_gate = np.where(np.abs(shaped) < 0.22, 255, 0).astype(np.uint8)
            for idx, mask in enumerate(self.trigon_masks):
                pulse = 0.82 + 0.18 * math.sin(TAU * (levels["phase"] * 2.0 + idx / 12.0))
                blend_mask_with_gate_roi(frame, mask, pressure_gate, INK, 0.56 * pressure_alpha * pulse)
                blend_mask_roi(frame, self.trigon_edges[idx], AMBER if idx % 2 else SOFT_GOLD, 0.24 * pressure_alpha)


def np_smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep01(value: float) -> float:
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def envelope(t: float, start: float, in_seconds: float, out_start: float, out_seconds: float) -> float:
    return smoothstep01((t - start) / in_seconds) * (1.0 - smoothstep01((t - out_start) / out_seconds))


def timeline_levels(t: float) -> dict[str, float]:
    return {
        "phase": (t % DURATION_SECONDS) / DURATION_SECONDS,
        "center": envelope(t, 4.0, 8.0, 70.0, 10.0),
        "first": envelope(t, 10.0, 12.0, 65.0, 12.0),
        "outer": envelope(t, 24.0, 16.0, 68.0, 10.0),
        "pressure": envelope(t, 42.0, 10.0, 64.0, 12.0),
    }


def source_strength(src: WaveSource, t: float) -> float:
    levels = timeline_levels(t)
    if src.ring == "center":
        return 0.36 + 0.64 * levels["center"]
    if src.ring == "first_crescent_ring":
        return 0.16 + 0.84 * levels["first"]
    return 0.10 + 0.90 * max(levels["outer"], 0.62 * levels["pressure"])


def bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def blend_mask(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float, *, glow: float = 0.0) -> None:
    if alpha <= 0.0:
        return
    mask_f = (mask.astype(np.float32) / 255.0) * alpha
    if float(mask_f.max()) <= 0.0:
        return
    color = np.array(bgr(rgb), dtype=np.float32)
    out = frame.astype(np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask, (0, 0), 8.0)
        out += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[:] = np.clip(out, 0, 255).astype(np.uint8)


def mask_bbox(mask: np.ndarray, *, threshold: int = 1, pad: int = 0) -> tuple[int, int, int, int] | None:
    pts = cv2.findNonZero(np.where(mask > threshold, 255, 0).astype(np.uint8))
    if pts is None:
        return None
    x, y, w, h = cv2.boundingRect(pts)
    return (
        max(0, x - pad),
        max(0, y - pad),
        min(mask.shape[1], x + w + pad),
        min(mask.shape[0], y + h + pad),
    )


def blend_mask_roi(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float, *, glow: float = 0.0) -> None:
    if alpha <= 0.0:
        return
    bbox = mask_bbox(mask, threshold=1, pad=round(12 if glow > 0 else 0))
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    mask_roi = mask[y0:y1, x0:x1]
    mask_f = (mask_roi.astype(np.float32) / 255.0) * alpha
    if float(mask_f.max()) <= 0.0:
        return
    color = np.array(bgr(rgb), dtype=np.float32)
    out = frame[y0:y1, x0:x1].astype(np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask_roi, (0, 0), 8.0)
        out += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)


def blend_mask_with_gate_roi(
    frame: np.ndarray,
    mask: np.ndarray,
    gate: np.ndarray,
    rgb: tuple[int, int, int],
    alpha: float,
) -> None:
    if alpha <= 0.0:
        return
    bbox = mask_bbox(mask, threshold=1)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    gated = cv2.bitwise_and(mask[y0:y1, x0:x1], gate[y0:y1, x0:x1])
    mask_f = (gated.astype(np.float32) / 255.0) * alpha
    if float(mask_f.max()) <= 0.0:
        return
    color = np.array(bgr(rgb), dtype=np.float32)
    out = frame[y0:y1, x0:x1].astype(np.float32)
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)


def mask_edge(mask: np.ndarray, *, kernel: int = 7, blur: float = 2.0) -> np.ndarray:
    src = np.where(mask > 10, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(src, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel)))
    return cv2.GaussianBlur(edge, (0, 0), blur)


def draw_text(frame: np.ndarray, text: str, org: tuple[int, int], scale: float = 0.38) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, bgr(LABEL), 1, cv2.LINE_AA)


def timeline_time_for_frame(frame_idx: int) -> float:
    if N_FRAMES <= 1:
        return 0.0
    return frame_idx / (N_FRAMES - 1) * DURATION_SECONDS


def config_for(target: str) -> RenderConfig:
    width, height = DRAFT_SIZE if target == "draft1080" else UHD_SIZE
    work_width = max(960, width // 2)
    work_height = max(540, height // 2)
    field_width = max(480, work_width // 2)
    field_height = max(270, work_height // 2)
    return RenderConfig(width, height, work_width, work_height, field_width, field_height, FPS, DURATION_SECONDS, N_FRAMES)


def render_clip(renderer: AbstractCymaticRenderer) -> dict[str, object]:
    mp4_path = OUT_DIR / f"{PROJECT}.mp4"
    writer = H264Writer(mp4_path, fps=FPS, size=(renderer.config.width, renderer.config.height))
    try:
        for frame_idx in range(N_FRAMES):
            t = timeline_time_for_frame(frame_idx)
            frame, _info = renderer.render_frame(t)
            writer.write(frame)
            if (frame_idx + 1) % FPS == 0:
                print(f"  {PROJECT}.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    return {
        "mp4": mp4_path.name,
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "frame_count": N_FRAMES,
        "frame_time_mapping": "frame_idx/(frame_count-1)*duration; final encoded frame samples exactly at loop duration",
    }


def save_key_stills(renderer: AbstractCymaticRenderer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in KEY_STILLS:
        frame, _info = renderer.render_frame(t)
        path = STILLS_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[key] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(renderer: AbstractCymaticRenderer) -> Path:
    panels = []
    for t in CONTACT_TIMES:
        frame, _info = renderer.render_frame(t)
        panel = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        draw_text(panel, f"t={t:04.1f}s", (16, 30), 0.34)
        panels.append(panel)
    while len(panels) % 5:
        panels.append(np.zeros_like(panels[0]))
    rows = [cv2.hconcat(panels[i : i + 5]) for i in range(0, len(panels), 5)]
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def read_frame_index(video_path: Path, frame_index: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"could not read frame {frame_index} from {video_path}")
    return frame


def mad(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def verify_source_closure(renderer: AbstractCymaticRenderer) -> dict[str, object]:
    start_sources = renderer.source_positions(0.0)
    end_sources = renderer.source_positions(DURATION_SECONDS)
    max_position_delta = 0.0
    max_wave_phase_delta = 0.0
    for (src_a, x0, y0, _), (src_b, x1, y1, _) in zip(start_sources, end_sources, strict=True):
        if src_a.source_id != src_b.source_id:
            raise RuntimeError("source order changed")
        max_position_delta = max(max_position_delta, math.hypot(x0 - x1, y0 - y1))
        phase0 = src_a.phase_offset_rad
        phase1 = src_b.phase_offset_rad - TAU * src_b.frequency_cycles
        delta = abs(((phase0 - phase1 + math.pi) % TAU) - math.pi)
        max_wave_phase_delta = max(max_wave_phase_delta, delta)
    return {
        "source_positions_match": max_position_delta < 1e-5,
        "source_phases_match_mod_tau": max_wave_phase_delta < 1e-5,
        "max_source_position_delta_px": round(max_position_delta, 8),
        "max_source_phase_delta_rad": round(max_wave_phase_delta, 8),
        "all_frequencies_integer_cycles_over_duration": True,
        "frequency_cycles": sorted({src.frequency_cycles for src in renderer.sources}),
        "duration_seconds": DURATION_SECONDS,
    }


def make_loop_diagnostic(renderer: AbstractCymaticRenderer, clip: dict[str, object]) -> tuple[Path, dict[str, object]]:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUT_DIR / clip["mp4"]
    f0 = read_frame_index(video_path, 0)
    f1 = read_frame_index(video_path, 1)
    fp = read_frame_index(video_path, N_FRAMES - 2)
    ff = read_frame_index(video_path, N_FRAMES - 1)
    cv2.imwrite(str(LOOP_DIR / "frame_0000_extracted.png"), f0)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 1:04d}_final_extracted.png"), ff)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 2:04d}_pre_final_extracted.png"), fp)

    raw0, _ = renderer.render_frame(0.0)
    rawf, _ = renderer.render_frame(DURATION_SECONDS)
    seam = mad(f0, ff)
    adj0 = mad(f0, f1)
    adj1 = mad(fp, ff)
    adjacent = (adj0 + adj1) * 0.5
    raw = mad(raw0, rawf)

    panels = [
        label_panel(f0, "decoded frame 0 / loop start"),
        label_panel(ff, f"decoded final frame {N_FRAMES - 1} / sampled at 80.0s"),
        label_panel(f1, f"adjacent reference frame 1 MAD={adj0:.4f}"),
        label_panel(fp, f"adjacent reference frame {N_FRAMES - 2} MAD={adj1:.4f}"),
    ]
    sheet = cv2.vconcat([cv2.hconcat(panels[:2]), cv2.hconcat(panels[2:])])
    draw_text(sheet, f"decoded seam MAD={seam:.4f}; adjacent reference mean={adjacent:.4f}; raw seam MAD={raw:.8f}", (32, sheet.shape[0] - 32), 0.42)
    path = LOOP_DIR / f"{PROJECT}_loop_diagnostic_sheet.png"
    cv2.imwrite(str(path), sheet)
    verification = {
        "decoded_frame0_final_mean_abs_diff": round(seam, 6),
        "decoded_frame0_frame1_mean_abs_diff": round(adj0, 6),
        "decoded_pre_final_final_mean_abs_diff": round(adj1, 6),
        "decoded_adjacent_reference_mean_abs_diff": round(adjacent, 6),
        "decoded_loop_seam_less_than_adjacent_reference": seam < adjacent,
        "raw_render_frame0_final_mean_abs_diff": round(raw, 8),
        "raw_render_loop_seam_exact": raw < 1e-7,
        "source_phase_frequency_closure": verify_source_closure(renderer),
    }
    return path, verification


def label_panel(frame: np.ndarray, label: str) -> np.ndarray:
    panel = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    shade = np.zeros_like(panel)
    cv2.rectangle(shade, (0, 0), (960, 56), bgr(DEEP), -1)
    cv2.addWeighted(shade, 0.58, panel, 1.0, 0, dst=panel)
    draw_text(panel, label, (22, 38), 0.40)
    return panel


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    renderer: AbstractCymaticRenderer,
    clip: dict[str, object],
    stills: dict[str, str],
    contact_sheet: Path,
    loop_sheet: Path | None,
    loop_verification: dict[str, object],
) -> Path:
    manifest = {
        "project": PROJECT,
        "status": "internal_r_and_d_video_library_candidate",
        "boundary": "Generated abstract cymatic/water geometry only. Not Coast Salish. Not Austin-derived. No public/show/projector/sponsor/social use until separately approved for the production context.",
        "renderer": "scripts/abstract_cymatic_composition_v001.py",
        "renderer_sha256": sha256(ROOT / "scripts" / "abstract_cymatic_composition_v001.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [renderer.config.width, renderer.config.height],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "rules": {
            "austin_assets_used": False,
            "source_artworks_used": False,
            "svg_assets_used": False,
            "cultural_claims": False,
            "coast_salish_framing": False,
            "generated_content": "abstract cymatic/water geometry only",
        },
        "render_settings": asdict(renderer.config),
        "source_configuration": {
            "source_model": "procedural scalar standing-wave emitters",
            "source_count": len(renderer.sources),
            "sources": [asdict(src) for src in renderer.sources],
            "phase_snapping": "all source frequencies are integer cycles over the 80 second clip; source positions use integer-cycle orbit/radial jitter",
        },
        "visual_system": {
            "central_origin": "soft circular source mask and nodal ring driven by central wave source envelope",
            "first_ring": "eight abstract crescent-like raster masks generated from circular source positions and radial subtraction geometry",
            "second_ring": "twelve larger crescent/ripple masks generated from outer source positions",
            "outer_pressure": "soft trigon-like attenuation gaps drawn as dark pressure/negative-space masks and gated by nodal field values",
            "main_mp4_debug_labels": False,
        },
        "loop_verification": loop_verification,
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "loop_diagnostic_sheet": str(loop_sheet.relative_to(OUT_DIR)) if loop_sheet else None,
            "readme": "README.md",
            **{f"{key}_still": rel for key, rel in stills.items()},
        },
    }
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(renderer: AbstractCymaticRenderer, loop_verification: dict[str, object], rendered: bool) -> Path:
    lines = [
        "# Abstract Cymatic Composition v001",
        "",
        "Status: INTERNAL R&D / Resolume video-library candidate. Generated abstract cymatic/water geometry only. Not Coast Salish. Not Austin-derived. No public/show/projector/sponsor/social use until separately approved for the production context.",
        "",
        "## Purpose",
        "",
        "This is the first standalone abstract cymatic/water composition packet. It does not use Austin artwork, Austin motifs, SVG primitive overlays, or cultural-design framing. The visual system is procedural: scalar wave sources, generated crescent/ripple masks, soft nodal rings, and pressure/attenuation gaps.",
        "",
        "## Sequence",
        "",
        "- 0-10s: calm cymatic/water field, central source begins to gather.",
        "- 10-25s: central origin and first crescent-like ring become clear.",
        "- 25-45s: second outer ring expands into larger ripple/crescent forms.",
        "- 45-65s: outer trigon-like attenuation/pressure gaps are strongest.",
        "- 65-80s: system relaxes back to the starting cymatic state.",
        "",
        "## Loop Verification",
        "",
        f"- Raw render frame 0/final MAD: `{loop_verification.get('raw_render_frame0_final_mean_abs_diff')}`.",
        f"- Decoded frame 0/final MAD: `{loop_verification.get('decoded_frame0_final_mean_abs_diff')}`.",
        f"- Adjacent-frame reference MAD: `{loop_verification.get('decoded_adjacent_reference_mean_abs_diff')}`.",
        f"- Seam less than adjacent motion: `{loop_verification.get('decoded_loop_seam_less_than_adjacent_reference')}`.",
        f"- Source phase/frequency closure: `{loop_verification.get('source_phase_frequency_closure')}`.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: {renderer.config.width}x{renderer.config.height}, 24fps, 80 seconds." if rendered else f"- `{PROJECT}.mp4`: not rendered in preview mode.",
        f"- `{PROJECT}_contact_sheet.png`.",
        f"- `stills/`: initial field, central origin, first crescent ring, second ring, peak attenuation/pressure, and return/loop point.",
        f"- `loop_diagnostics/{PROJECT}_loop_diagnostic_sheet.png`." if rendered else "- Loop diagnostic sheet is generated after MP4 render.",
        f"- `{PROJECT}_manifest.json`.",
        "",
        "## Honest Verdict",
        "",
    ]
    seam_ok = loop_verification.get("decoded_loop_seam_less_than_adjacent_reference")
    raw_ok = loop_verification.get("raw_render_loop_seam_exact")
    if seam_ok and raw_ok:
        lines.append(
            "v001 works as a standalone abstract cymatic library entry. It has a legible central origin, inner crescent/ripple ring, larger outer ring, and peak pressure gaps without relying on artwork assets or cultural claims. The loop is mathematically closed at the raw render level and the decoded seam is below normal adjacent-frame motion."
        )
    else:
        lines.append(
            "v001 is a useful abstract cymatic study, but the loop check or decoded seam check did not fully pass. Treat it as an internal draft until the seam is improved."
        )
    lines.extend(
        [
            "",
            "The piece is intentionally restrained: dark water ground, teal/blue field, and warm cream/gold highlights. The trigon-like forms should be read only as abstract wave attenuation/pressure gaps, not icons or cultural design elements.",
            "",
            "Renderer: `scripts/abstract_cymatic_composition_v001.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render abstract cymatic composition v001.")
    parser.add_argument("--target", choices=("uhd", "draft1080"), default="uhd")
    parser.add_argument("--preview", action="store_true", help="Write stills/contact/manifest without rendering the MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    config = config_for(args.target)
    renderer = AbstractCymaticRenderer(config)

    print("Writing abstract cymatic key stills and contact sheet", flush=True)
    stills = save_key_stills(renderer)
    contact = make_contact_sheet(renderer)

    if args.preview:
        raw0, _ = renderer.render_frame(0.0)
        rawf, _ = renderer.render_frame(DURATION_SECONDS)
        loop_verification = {
            "preview_only": True,
            "decoded_frame0_final_mean_abs_diff": None,
            "decoded_adjacent_reference_mean_abs_diff": None,
            "decoded_loop_seam_less_than_adjacent_reference": None,
            "raw_render_frame0_final_mean_abs_diff": round(mad(raw0, rawf), 8),
            "raw_render_loop_seam_exact": mad(raw0, rawf) < 1e-7,
            "source_phase_frequency_closure": verify_source_closure(renderer),
        }
        clip = {"mp4": f"{PROJECT}.mp4", "duration_seconds": DURATION_SECONDS, "fps": FPS, "frame_count": N_FRAMES}
        loop_sheet = None
    else:
        print(f"Rendering {PROJECT}.mp4", flush=True)
        clip = render_clip(renderer)
        print("Writing loop diagnostic sheet", flush=True)
        loop_sheet, loop_verification = make_loop_diagnostic(renderer, clip)

    manifest = write_manifest(renderer, clip, stills, contact, loop_sheet, loop_verification)
    readme = write_readme(renderer, loop_verification, rendered=not args.preview)

    print(f"Wrote {contact}", flush=True)
    if loop_sheet:
        print(f"Wrote {loop_sheet}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)
    if not args.preview:
        print(f"Wrote {OUT_DIR / clip['mp4']}", flush=True)


if __name__ == "__main__":
    main()
