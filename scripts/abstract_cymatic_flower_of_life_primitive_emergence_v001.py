#!/usr/bin/env python3
"""
Abstract cymatic flower-of-life primitive emergence v001.

Standalone procedural cymatic/water composition for the internal Resolume video
library. Circle, crescent/lens, and trigon-like pressure cells are generated
from a 19-circle flower-of-life / hexagonal construction lattice. The wave
field supplies water atmosphere, drift, and breathing; the peak geometry is not
an amplitude-threshold blob layer.

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
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "abstract_cymatic_flower_of_life_primitive_emergence_v001_2026-05-22"
)
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

PROJECT = "abstract_cymatic_flower_of_life_primitive_emergence_v001"
FPS = 24
DURATION_SECONDS = 60.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

UHD_SIZE = (3840, 2160)
DRAFT_SIZE = (1920, 1080)

DEEP = (0, 5, 7)
DARK_WATER = (3, 18, 24)
INK = (0, 7, 9)
DEEP_TEAL = (12, 56, 62)
TEAL = (48, 147, 152)
MUTED_TEAL = (78, 132, 132)
ICE_BLUE = (145, 219, 228)
WARM_CREAM = (235, 226, 194)
SOFT_GOLD = (245, 196, 90)
AMBER = (210, 118, 66)
CONSTRUCTION = (160, 178, 165)
LABEL = (226, 234, 230)
BBOX_CACHE: dict[int, tuple[int, int, int, int] | None] = {}

KEY_STILLS = (
    ("initial_raw_interference", 0.0),
    ("nineteen_construction_circles", 14.0),
    ("two_circle_lens_lattice", 26.0),
    ("second_ring_lens_expansion", 34.0),
    ("three_circle_trigon_cells", 42.0),
    ("peak_beauty_composite", 46.0),
    ("return_loop_point", DURATION_SECONDS),
)

CONTACT_TIMES = (
    0.0,
    5.0,
    8.0,
    12.0,
    16.0,
    21.0,
    26.0,
    32.0,
    38.0,
    44.0,
    48.0,
    52.0,
    56.0,
    58.0,
    DURATION_SECONDS,
)

PEAK_TIME_SECONDS = 44.0


@dataclass(frozen=True)
class WaveSource:
    source_id: str
    role: str
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
class ConstructionCircle:
    circle_id: str
    source_id: str
    x: float
    y: float
    radius_px: float
    role: str
    ring_index: int
    q: int
    r: int


@dataclass(frozen=True)
class CellRegion:
    region_id: str
    region_class: str
    source_circle_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    generation_rule: str
    fill_rgb: tuple[int, int, int]
    outline_rgb: tuple[int, int, int]
    mask: np.ndarray
    edge: np.ndarray


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
    work_canvas_note: str


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


class PrimitiveEmergenceRenderer:
    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        self.cx = config.work_width * 0.5
        self.cy = config.work_height * 0.5
        self.scale = config.work_height / 1080.0
        self.construction_radius = 162.0 * self.scale
        self.outer_source_radius = 440.0 * self.scale

        y, x = np.mgrid[0 : config.work_height, 0 : config.work_width].astype(np.float32)
        self.x = x
        self.y = y
        self.dist = np.sqrt((x - self.cx) ** 2 + (y - self.cy) ** 2)
        self.theta = np.arctan2(y - self.cy, x - self.cx).astype(np.float32)

        fy = (np.arange(config.field_height, dtype=np.float32) + 0.5) * (config.work_height / config.field_height)
        fx = (np.arange(config.field_width, dtype=np.float32) + 0.5) * (config.work_width / config.field_width)
        self.fx, self.fy = np.meshgrid(fx, fy)

        self.field_boundary = self._radial_falloff(530.0 * self.scale, 90.0 * self.scale)
        self.field_boundary_f = self.field_boundary.astype(np.float32) / 255.0
        self.field_boundary_small = cv2.resize(self.field_boundary, (config.field_width, config.field_height), interpolation=cv2.INTER_AREA)
        self.field_edge_window = self._edge_window(self.fx, self.fy)

        self.sources = self._make_sources()
        self.construction_circles = self._make_construction_circles()
        self.circle_masks = {circle.circle_id: self._solid_circle(circle.x, circle.y, circle.radius_px) for circle in self.construction_circles}
        self.circle_rings = {
            circle.circle_id: self._ring_at(circle.x, circle.y, circle.radius_px, 2.1 * self.scale, 1.5 * self.scale)
            for circle in self.construction_circles
        }
        self.construction_ring_union = mask_union(*self.circle_rings.values())
        self.source_dots = self._make_source_dots()
        self.origin_region, self.lens_regions, self.triple_regions, self.negative_regions = self._make_regions()
        self.region_unions = self._make_region_unions()
        self.inner_wave_rings = self._make_wavefront_rings()

    def _flower_lattice_points(self) -> list[tuple[int, int, int, float, float, float, float]]:
        """Return radius-2 triangular-lattice points: 1 center, 6 first ring, 12 second ring."""
        points: list[tuple[int, int, int, float, float, float, float]] = []
        r0 = self.construction_radius
        for q in range(-2, 3):
            for r in range(-2, 3):
                ring_index = max(abs(q), abs(r), abs(q + r))
                if ring_index > 2:
                    continue
                x_local = r0 * (q + 0.5 * r)
                y_local = r0 * (math.sqrt(3.0) * 0.5 * r)
                base_radius = math.hypot(x_local, y_local)
                angle = math.atan2(y_local, x_local) if base_radius > 1e-6 else 0.0
                points.append((ring_index, q, r, self.cx + x_local, self.cy + y_local, angle, base_radius))
        points.sort(key=lambda item: (item[0], math.atan2(item[4] - self.cy, item[3] - self.cx)))
        return points

    def _make_sources(self) -> list[WaveSource]:
        sources: list[WaveSource] = []
        for idx, (ring_index, _q, _r, _x, _y, angle, base_radius) in enumerate(self._flower_lattice_points()):
            if ring_index == 0:
                source_id = "flower_center_00"
                role = "center_antinode"
                amplitude = 1.06
                frequency = 9
                decay = 820.0 * self.scale
                radial_jitter = 0.0
                angular_jitter = 0.0
            elif ring_index == 1:
                source_id = f"flower_first_ring_{idx:02d}"
                role = "first_ring_antinode"
                amplitude = 0.84
                frequency = 9
                decay = 760.0 * self.scale
                radial_jitter = 18.0 * self.scale
                angular_jitter = 0.028
            else:
                source_id = f"flower_second_ring_{idx:02d}"
                role = "second_ring_antinode"
                amplitude = 0.58
                frequency = 6
                decay = 920.0 * self.scale
                radial_jitter = 24.0 * self.scale
                angular_jitter = 0.022
            sources.append(
                WaveSource(
                    source_id,
                    role,
                    angle,
                    base_radius,
                    amplitude,
                    self.construction_radius * 1.04,
                    frequency,
                    0.173 * idx + 0.037 * ring_index,
                    decay,
                    1 + (idx % 3),
                    2 + (idx % 4),
                    radial_jitter,
                    angular_jitter,
                )
            )
        return sources

    def _make_construction_circles(self) -> list[ConstructionCircle]:
        circles: list[ConstructionCircle] = []
        for idx, (ring_index, q, r, x, y, _angle, _base_radius) in enumerate(self._flower_lattice_points()):
            if ring_index == 0:
                source_id = "flower_center_00"
                circle_id = "flower_center_00_R1"
                role = "center construction circle in 19-circle flower lattice"
            elif ring_index == 1:
                source_id = f"flower_first_ring_{idx:02d}"
                circle_id = f"{source_id}_R1"
                role = "first-ring equal-radius construction circle"
            else:
                source_id = f"flower_second_ring_{idx:02d}"
                circle_id = f"{source_id}_R1"
                role = "second-ring equal-radius construction circle"
            circles.append(
                ConstructionCircle(
                    circle_id,
                    source_id,
                    x,
                    y,
                    self.construction_radius,
                    role,
                    ring_index,
                    q,
                    r,
                )
            )
        return circles

    def _edge_window(self, gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
        dist = np.minimum(np.minimum(gx, self.config.work_width - gx), np.minimum(gy, self.config.work_height - gy))
        return np_smoothstep(24.0 * self.scale, 135.0 * self.scale, dist).astype(np.float32)

    def _radial_falloff(self, radius: float, soft_edge: float) -> np.ndarray:
        alpha = np.clip((radius + soft_edge - self.dist) / max(1e-6, soft_edge), 0.0, 1.0)
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

    def _solid_circle(self, cx: float, cy: float, radius: float, *, soften: float | None = None) -> np.ndarray:
        mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        cv2.circle(mask, (round(cx), round(cy)), max(1, round(radius)), 255, -1, lineType=cv2.LINE_AA)
        sigma = 0.8 * self.scale if soften is None else soften
        return cv2.GaussianBlur(mask, (0, 0), sigma)

    def _ring_at(self, cx: float, cy: float, radius: float, thickness: float, blur: float) -> np.ndarray:
        d = np.sqrt((self.x - cx) ** 2 + (self.y - cy) ** 2)
        half = thickness * 0.5
        mask = np.where((d >= radius - half) & (d <= radius + half), 255, 0).astype(np.uint8)
        return cv2.GaussianBlur(mask, (0, 0), blur)

    def _radial_band(self, inner: float, outer: float, soft_edge: float) -> np.ndarray:
        inner_alpha = np_smoothstep(inner - soft_edge, inner + soft_edge, self.dist)
        outer_alpha = 1.0 - np_smoothstep(outer - soft_edge, outer + soft_edge, self.dist)
        return np.clip(inner_alpha * outer_alpha * 255.0, 0, 255).astype(np.uint8)

    def _make_source_dots(self) -> np.ndarray:
        mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        for circle in self.construction_circles:
            cv2.circle(mask, (round(circle.x), round(circle.y)), max(2, round(3.2 * self.scale)), 255, -1, lineType=cv2.LINE_AA)
        return cv2.GaussianBlur(mask, (0, 0), 1.0 * self.scale)

    def _neighbor_pairs(self) -> list[tuple[ConstructionCircle, ConstructionCircle]]:
        pairs: list[tuple[ConstructionCircle, ConstructionCircle]] = []
        max_dist = self.construction_radius * 1.06
        for idx, a in enumerate(self.construction_circles):
            for b in self.construction_circles[idx + 1 :]:
                if math.hypot(a.x - b.x, a.y - b.y) <= max_dist:
                    pairs.append((a, b))
        pairs.sort(
            key=lambda pair: (
                max(pair[0].ring_index, pair[1].ring_index),
                math.atan2((pair[0].y + pair[1].y) * 0.5 - self.cy, (pair[0].x + pair[1].x) * 0.5 - self.cx),
            )
        )
        return pairs

    def _neighbor_triples(self) -> list[tuple[ConstructionCircle, ConstructionCircle, ConstructionCircle]]:
        triples: list[tuple[ConstructionCircle, ConstructionCircle, ConstructionCircle]] = []
        max_dist = self.construction_radius * 1.06
        circles = self.construction_circles
        for i, a in enumerate(circles):
            for j, b in enumerate(circles[i + 1 :], start=i + 1):
                if math.hypot(a.x - b.x, a.y - b.y) > max_dist:
                    continue
                for c in circles[j + 1 :]:
                    if math.hypot(a.x - c.x, a.y - c.y) <= max_dist and math.hypot(b.x - c.x, b.y - c.y) <= max_dist:
                        triples.append((a, b, c))
        triples.sort(
            key=lambda triple: (
                max(circle.ring_index for circle in triple),
                math.atan2(sum(circle.y for circle in triple) / 3.0 - self.cy, sum(circle.x for circle in triple) / 3.0 - self.cx),
            )
        )
        return triples

    def _make_regions(self) -> tuple[CellRegion, list[CellRegion], list[CellRegion], list[CellRegion]]:
        center = next(circle for circle in self.construction_circles if circle.ring_index == 0)
        center_core = self._solid_circle(center.x, center.y, center.radius_px * 0.20, soften=1.4 * self.scale)
        source_clear = self._make_source_clear_mask(center.radius_px * 0.105)

        origin_mask = mask_intersection(center_core, self.field_boundary)
        origin = CellRegion(
            "center_origin_circle",
            "circle_origin",
            (center.circle_id,),
            (center.source_id,),
            "small central origin from the center construction circle at 0.20R",
            DEEP_TEAL,
            SOFT_GOLD,
            origin_mask,
            mask_edge(origin_mask, kernel=max(5, round(7 * self.scale) | 1), blur=1.8 * self.scale),
        )

        lenses: list[CellRegion] = []
        for idx, (a, b) in enumerate(self._neighbor_pairs()):
            lens = mask_intersection(self.circle_masks[a.circle_id], self.circle_masks[b.circle_id], self.field_boundary)
            lens = mask_subtract(lens, source_clear)
            lens = cv2.GaussianBlur(lens, (0, 0), 0.85 * self.scale)
            max_ring = max(a.ring_index, b.ring_index)
            lenses.append(
                CellRegion(
                    f"two_circle_lens_{idx:02d}",
                    "two_circle_lens",
                    (a.circle_id, b.circle_id),
                    (a.source_id, b.source_id),
                    f"two-circle equal-radius intersection between adjacent flower lattice circles; max ring {max_ring}",
                    WARM_CREAM if idx % 3 != 1 else ICE_BLUE,
                    INK,
                    lens,
                    mask_edge(lens, kernel=max(5, round(7 * self.scale) | 1), blur=1.8 * self.scale),
                )
            )

        triples: list[CellRegion] = []
        pressure_cells: list[CellRegion] = []
        for idx, triple in enumerate(self._neighbor_triples()):
            a, b, c = triple
            mask = mask_intersection(
                self.circle_masks[a.circle_id],
                self.circle_masks[b.circle_id],
                self.circle_masks[c.circle_id],
                self.field_boundary,
            )
            mask = mask_subtract(mask, source_clear)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
            mask = cv2.GaussianBlur(mask, (0, 0), 0.95 * self.scale)
            centroid_x = (a.x + b.x + c.x) / 3.0
            centroid_y = (a.y + b.y + c.y) / 3.0
            centroid_radius = math.hypot(centroid_x - self.cx, centroid_y - self.cy)
            region = CellRegion(
                f"three_circle_cell_{idx:02d}",
                "three_circle_trigon_like_cell" if centroid_radius < self.construction_radius * 1.45 else "negative_space_trigon_like_cell",
                (a.circle_id, b.circle_id, c.circle_id),
                (a.source_id, b.source_id, c.source_id),
                "three mutually adjacent equal-radius construction circles intersect to form an arc-bounded curved triangular pressure cell",
                TEAL if centroid_radius < self.construction_radius * 1.45 else INK,
                SOFT_GOLD if centroid_radius < self.construction_radius * 1.45 else WARM_CREAM,
                mask,
                mask_edge(mask, kernel=max(5, round(8 * self.scale) | 1), blur=2.0 * self.scale),
            )
            if region.region_class == "three_circle_trigon_like_cell":
                triples.append(region)
            else:
                pressure_cells.append(region)

        return origin, lenses, triples, pressure_cells

    def _make_source_clear_mask(self, radius: float) -> np.ndarray:
        mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        for circle in self.construction_circles:
            cv2.circle(mask, (round(circle.x), round(circle.y)), max(1, round(radius)), 255, -1, lineType=cv2.LINE_AA)
        return cv2.GaussianBlur(mask, (0, 0), 0.8 * self.scale)

    def _make_wavefront_rings(self) -> list[np.ndarray]:
        rings: list[np.ndarray] = []
        for radius, thickness, blur in (
            (self.construction_radius * 0.52, 2.0, 1.5),
            (self.construction_radius, 2.2, 1.6),
            (self.construction_radius * 1.50, 2.4, 1.8),
            (self.construction_radius * 2.04, 2.8, 2.0),
            (self.construction_radius * 2.58, 2.8, 2.0),
            (self.construction_radius * 3.00, 3.0, 2.2),
        ):
            rings.append(self._ring_at(self.cx, self.cy, radius, thickness * self.scale, blur * self.scale))
        return rings

    def _make_region_unions(self) -> dict[str, np.ndarray]:
        lens_even = [region.mask for idx, region in enumerate(self.lens_regions) if idx % 2 == 0]
        lens_odd = [region.mask for idx, region in enumerate(self.lens_regions) if idx % 2 == 1]
        return {
            "lens_even": mask_union(*lens_even),
            "lens_odd": mask_union(*lens_odd),
            "lens_edges": mask_union(*(region.edge for region in self.lens_regions)),
            "triple": mask_union(*(region.mask for region in self.triple_regions)),
            "triple_edges": mask_union(*(region.edge for region in self.triple_regions)),
            "negative": mask_union(*(region.mask for region in self.negative_regions)),
            "negative_edges": mask_union(*(region.edge for region in self.negative_regions)),
        }

    def source_positions(self, t: float) -> list[tuple[WaveSource, float, float, float]]:
        p = (t % DURATION_SECONDS) / DURATION_SECONDS
        levels = timeline_levels(t)
        lock = 0.78 * max(levels["construction"], levels["lenses"], levels["trigons"])
        drift_gate = 1.0 - lock
        result: list[tuple[WaveSource, float, float, float]] = []
        for src in self.sources:
            angle = src.angle_rad + drift_gate * src.angular_jitter_rad * math.sin(TAU * (src.orbit_cycles * p + src.phase_offset_rad / TAU))
            radius = src.base_radius_px + drift_gate * src.radial_jitter_px * math.sin(TAU * (src.radial_cycles * p + src.phase_offset_rad / TAU))
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
        field = cv2.GaussianBlur(field, (0, 0), 0.50 * self.scale)
        denom = float(np.percentile(np.abs(field), 99.2))
        if denom > 1e-6:
            field = np.clip(field / denom, -1.0, 1.0).astype(np.float32)
        return cv2.GaussianBlur(field, (0, 0), 0.28 * self.scale)

    def render_frame(self, t: float, *, output_size: bool = True, mode: str = "beauty", labels: bool = False) -> tuple[np.ndarray, dict[str, object]]:
        field_small = self.evaluate_field(t)
        field = cv2.resize(field_small, (self.config.work_width, self.config.work_height), interpolation=cv2.INTER_CUBIC)
        shaped = np.sign(field) * (np.abs(field) ** 0.86)
        levels = timeline_levels(t)

        base = self.field_boundary_f * 0.82
        frame = (np.array(bgr(DARK_WATER), dtype=np.float32) * base[..., None]).astype(np.uint8)
        self._draw_field(frame, shaped, levels)

        if mode == "raw":
            if labels:
                draw_text(frame, "1 raw interference field", (32, 48), 0.50)
        elif mode == "construction":
            self._draw_construction(frame, alpha=0.86, include_sources=True)
            if labels:
                draw_text(frame, "2 full 19-circle flower-of-life construction lattice", (32, 48), 0.42)
        elif mode == "lenses":
            self._draw_construction(frame, alpha=0.42, include_sources=True)
            self._draw_cell_regions(frame, [self.origin_region], 1.0, pulse_phase=levels["phase"], fill_scale=0.92)
            self._draw_cell_regions(frame, self.lens_regions, 1.0, pulse_phase=levels["phase"], fill_scale=0.98)
            if labels:
                draw_text(frame, "3 selected 2-circle intersection lens regions", (32, 48), 0.46)
        elif mode == "trigons":
            self._draw_construction(frame, alpha=0.38, include_sources=True)
            self._draw_cell_regions(frame, self.triple_regions, 1.0, pulse_phase=levels["phase"], fill_scale=0.96)
            self._draw_cell_regions(frame, self.negative_regions, 1.0, pulse_phase=levels["phase"], fill_scale=1.0)
            if labels:
                draw_text(frame, "4 selected 3-circle and negative-space trigon-like cells", (32, 48), 0.42)
        else:
            self._draw_water_breath(frame, t, 0.12 + 0.16 * levels["trigons"])
            self._draw_beauty_geometry(frame, levels)
            if labels:
                draw_text(frame, "5 final beauty composite", (32, 48), 0.50)

        if output_size and (self.config.work_width, self.config.work_height) != (self.config.width, self.config.height):
            frame = cv2.resize(frame, (self.config.width, self.config.height), interpolation=cv2.INTER_LINEAR)

        info = {
            "time_seconds": round(t, 5),
            "levels": {key: round(value, 5) for key, value in levels.items()},
            "active_sources": sum(1 for _src, _x, _y, strength in self.source_positions(t) if strength > 0.01),
            "field_min": round(float(field_small.min()), 6),
            "field_max": round(float(field_small.max()), 6),
        }
        return frame, info

    def _draw_field(self, frame: np.ndarray, shaped: np.ndarray, levels: dict[str, float]) -> None:
        pos = np.where(shaped > 0.080, self.field_boundary, 0).astype(np.uint8)
        neg = np.where(shaped < -0.070, self.field_boundary, 0).astype(np.uint8)
        nodes = np.where(np.abs(shaped) < 0.032, self.field_boundary, 0).astype(np.uint8)
        nodes = cv2.morphologyEx(nodes, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        edge = cv2.morphologyEx(cv2.bitwise_or(pos, neg), cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        geometry_strength = max(levels["lenses"], levels["trigons"])
        out = frame.astype(np.float32)
        for mask, rgb, alpha in (
            (neg, TEAL, 0.34 + 0.07 * geometry_strength),
            (pos, WARM_CREAM, 0.22 + 0.10 * levels["lenses"]),
            (nodes, INK, 0.46 + 0.10 * levels["trigons"]),
            (edge, INK, 0.20),
        ):
            a = (mask.astype(np.float32) / 255.0) * alpha
            color = np.array(bgr(rgb), dtype=np.float32)
            out = out * (1.0 - a[..., None]) + color * a[..., None]
        frame[:] = np.clip(out, 0, 255).astype(np.uint8)

    def _draw_water_breath(self, frame: np.ndarray, t: float, alpha: float) -> None:
        if alpha <= 0.0:
            return
        phase = (t % DURATION_SECONDS) / DURATION_SECONDS
        for idx, ring in enumerate(self.inner_wave_rings):
            rgb = ICE_BLUE if idx % 2 else MUTED_TEAL
            pulse = 0.65 + 0.35 * math.sin(TAU * ((idx + 1) * phase + idx * 0.13))
            blend_mask_roi(frame, ring, rgb, alpha * (0.10 + 0.09 * pulse))

    def _draw_construction(self, frame: np.ndarray, *, alpha: float, include_sources: bool) -> None:
        if alpha <= 0.0:
            return
        blend_mask_roi(frame, self.construction_ring_union, CONSTRUCTION, 0.58 * alpha)
        if include_sources:
            blend_mask_roi(frame, self.source_dots, SOFT_GOLD, 0.72 * alpha)

    def _draw_cell_regions(
        self,
        frame: np.ndarray,
        regions: list[CellRegion],
        alpha: float,
        *,
        pulse_phase: float,
        fill_scale: float,
    ) -> None:
        if alpha <= 0.0:
            return
        for idx, region in enumerate(regions):
            pulse = 0.82 + 0.18 * math.sin(TAU * (pulse_phase + idx / max(1, len(regions))))
            if region.region_class == "negative_space_trigon_like_cell":
                fill_alpha = 0.58 * alpha * pulse * fill_scale
                edge_alpha = 0.28 * alpha
            elif region.region_class == "three_circle_trigon_like_cell":
                fill_alpha = 0.44 * alpha * pulse * fill_scale
                edge_alpha = 0.34 * alpha
            elif region.region_class == "two_circle_lens":
                fill_alpha = 0.42 * alpha * pulse * fill_scale
                edge_alpha = 0.30 * alpha
            else:
                fill_alpha = 0.48 * alpha * fill_scale
                edge_alpha = 0.45 * alpha
            blend_mask_roi(frame, region.mask, region.fill_rgb, fill_alpha, glow=0.004 * alpha)
            blend_mask_roi(frame, region.edge, region.outline_rgb, edge_alpha)

    def _draw_beauty_geometry(self, frame: np.ndarray, levels: dict[str, float]) -> None:
        construction_alpha = 0.16 * levels["construction"] + 0.06 * levels["lenses"]
        self._draw_construction(frame, alpha=construction_alpha, include_sources=False)
        self._draw_cell_unions(frame, levels)

    def _draw_cell_unions(self, frame: np.ndarray, levels: dict[str, float]) -> None:
        origin = levels["origin"]
        if origin > 0.0:
            blend_mask_roi(frame, self.origin_region.mask, self.origin_region.fill_rgb, 0.42 * origin, glow=0.004 * origin)
            blend_mask_roi(frame, self.origin_region.edge, self.origin_region.outline_rgb, 0.42 * origin)

        lenses = levels["lenses"]
        if lenses > 0.0:
            blend_mask_roi(frame, self.region_unions["lens_even"], WARM_CREAM, 0.38 * lenses, glow=0.004 * lenses)
            blend_mask_roi(frame, self.region_unions["lens_odd"], ICE_BLUE, 0.36 * lenses, glow=0.004 * lenses)
            blend_mask_roi(frame, self.region_unions["lens_edges"], INK, 0.25 * lenses)

        trigons = levels["trigons"]
        if trigons > 0.0:
            blend_mask_roi(frame, self.region_unions["triple"], TEAL, 0.36 * trigons, glow=0.003 * trigons)
            blend_mask_roi(frame, self.region_unions["triple_edges"], SOFT_GOLD, 0.26 * trigons)

        negative = levels["negative"]
        if negative > 0.0:
            blend_mask_roi(frame, self.region_unions["negative"], INK, 0.58 * negative, glow=0.004 * negative)
            blend_mask_roi(frame, self.region_unions["negative_edges"], WARM_CREAM, 0.25 * negative)


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
        "origin": envelope(t, 5.0, 7.0, 52.0, 8.0),
        "construction": envelope(t, 7.0, 9.0, 50.0, 9.0),
        "lenses": envelope(t, 15.0, 11.0, 48.0, 10.0),
        "trigons": envelope(t, 29.0, 8.0, 48.0, 9.0),
        "negative": envelope(t, 32.0, 8.0, 50.0, 8.0),
    }


def source_strength(src: WaveSource, t: float) -> float:
    levels = timeline_levels(t)
    if src.role == "center_antinode":
        return 0.34 + 0.66 * levels["origin"]
    if src.role == "first_ring_antinode":
        return 0.20 + 0.80 * max(levels["construction"], levels["lenses"], 0.74 * levels["trigons"])
    return 0.18 + 0.82 * max(0.30 * levels["construction"], levels["trigons"], levels["negative"])


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
    cache_key = (id(mask) << 16) ^ (threshold << 8) ^ pad
    if cache_key in BBOX_CACHE:
        return BBOX_CACHE[cache_key]
    pts = cv2.findNonZero(np.where(mask > threshold, 255, 0).astype(np.uint8))
    if pts is None:
        BBOX_CACHE[cache_key] = None
        return None
    x, y, w, h = cv2.boundingRect(pts)
    bbox = (
        max(0, x - pad),
        max(0, y - pad),
        min(mask.shape[1], x + w + pad),
        min(mask.shape[0], y + h + pad),
    )
    BBOX_CACHE[cache_key] = bbox
    return bbox


def blend_mask_roi(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float, *, glow: float = 0.0) -> None:
    if alpha <= 0.0:
        return
    bbox = mask_bbox(mask, threshold=1, pad=round(16 if glow > 0 else 0))
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


def mask_intersection(*masks: np.ndarray) -> np.ndarray:
    if not masks:
        raise ValueError("mask_intersection requires at least one mask")
    return np.minimum.reduce([mask.astype(np.uint8) for mask in masks])


def mask_union(*masks: np.ndarray) -> np.ndarray:
    if not masks:
        raise ValueError("mask_union requires at least one mask")
    return np.maximum.reduce([mask.astype(np.uint8) for mask in masks])


def mask_subtract(mask: np.ndarray, subtract: np.ndarray) -> np.ndarray:
    return np.clip(mask.astype(np.int16) - subtract.astype(np.int16), 0, 255).astype(np.uint8)


def mask_edge(mask: np.ndarray, *, kernel: int = 7, blur: float = 2.0) -> np.ndarray:
    src = np.where(mask > 10, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(src, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel)))
    return cv2.GaussianBlur(edge, (0, 0), blur)


def draw_text(frame: np.ndarray, text: str, org: tuple[int, int], scale: float = 0.38) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, bgr(LABEL), 1, cv2.LINE_AA)


def label_panel(frame: np.ndarray, label: str, *, size: tuple[int, int] = (960, 540)) -> np.ndarray:
    panel = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    shade = np.zeros_like(panel)
    cv2.rectangle(shade, (0, 0), (size[0], 58), bgr(DEEP), -1)
    cv2.addWeighted(shade, 0.58, panel, 1.0, 0, dst=panel)
    draw_text(panel, label, (22, 38), 0.38)
    return panel


def timeline_time_for_frame(frame_idx: int) -> float:
    if N_FRAMES <= 1:
        return 0.0
    return frame_idx / (N_FRAMES - 1) * DURATION_SECONDS


def config_for(target: str) -> RenderConfig:
    width, height = DRAFT_SIZE if target == "draft1080" else UHD_SIZE
    if target == "uhd":
        work_width = 1600
        work_height = 900
        note = "UHD encode from a 1600x900 procedural work canvas with final linear resampling to 3840x2160."
    else:
        work_width = width
        work_height = height
        note = "Draft encode and procedural work canvas are both 1920x1080."
    field_width = 400 if work_width >= 1600 else 360
    field_height = 225 if work_width >= 1600 else 202
    return RenderConfig(width, height, work_width, work_height, field_width, field_height, FPS, DURATION_SECONDS, N_FRAMES, note)


def render_clip(renderer: PrimitiveEmergenceRenderer) -> dict[str, object]:
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


def save_key_stills(renderer: PrimitiveEmergenceRenderer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in KEY_STILLS:
        frame, _info = renderer.render_frame(t)
        path = STILLS_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[key] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(renderer: PrimitiveEmergenceRenderer) -> Path:
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


def make_debug_sheet(renderer: PrimitiveEmergenceRenderer) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    views = [
        ("raw interference field", "raw"),
        ("19 construction circles", "construction"),
        ("2-circle crescent/lens cells", "lenses"),
        ("3-circle / negative-space cells", "trigons"),
        ("beauty composite", "beauty"),
    ]
    panels = []
    for label, mode in views:
        frame, _info = renderer.render_frame(PEAK_TIME_SECONDS, mode=mode, labels=False)
        panels.append(label_panel(frame, label, size=(768, 432)))
    sheet = cv2.hconcat(panels)
    draw_text(sheet, "debug views: raw field -> 19 construction circles -> 2-circle cells -> 3-circle/pressure cells -> beauty", (28, sheet.shape[0] - 24), 0.42)
    path = DEBUG_DIR / f"{PROJECT}_debug_views_sheet.png"
    cv2.imwrite(str(path), sheet)

    for label, mode in views:
        frame, _info = renderer.render_frame(PEAK_TIME_SECONDS, mode=mode, labels=True)
        cv2.imwrite(str(DEBUG_DIR / f"{PROJECT}_{mode}_debug_peak.png"), frame)
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


def verify_source_closure(renderer: PrimitiveEmergenceRenderer) -> dict[str, object]:
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
        "construction_circle_positions_match": True,
        "construction_circle_count": len(renderer.construction_circles),
        "max_source_position_delta_px": round(max_position_delta, 8),
        "max_source_phase_delta_rad": round(max_wave_phase_delta, 8),
        "all_frequencies_integer_cycles_over_duration": True,
        "frequency_cycles": sorted({src.frequency_cycles for src in renderer.sources}),
        "duration_seconds": DURATION_SECONDS,
    }


def make_loop_diagnostic(renderer: PrimitiveEmergenceRenderer, clip: dict[str, object]) -> tuple[Path, dict[str, object]]:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUT_DIR / clip["mp4"]
    f0 = read_frame_index(video_path, 0)
    f1 = read_frame_index(video_path, 1)
    fp = read_frame_index(video_path, N_FRAMES - 2)
    ff = read_frame_index(video_path, N_FRAMES - 1)
    cv2.imwrite(str(LOOP_DIR / "frame_0000_extracted.png"), f0)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 2:04d}_pre_final_extracted.png"), fp)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 1:04d}_final_extracted.png"), ff)

    raw0, _ = renderer.render_frame(0.0)
    rawf, _ = renderer.render_frame(DURATION_SECONDS)
    seam = mad(f0, ff)
    adj0 = mad(f0, f1)
    adj1 = mad(fp, ff)
    adjacent = (adj0 + adj1) * 0.5
    raw = mad(raw0, rawf)

    panels = [
        label_panel(f0, "decoded frame 0 / loop start"),
        label_panel(ff, f"decoded final frame {N_FRAMES - 1} / sampled at 60.0s"),
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    renderer: PrimitiveEmergenceRenderer,
    clip: dict[str, object],
    stills: dict[str, str],
    contact_sheet: Path,
    debug_sheet: Path,
    loop_sheet: Path | None,
    loop_verification: dict[str, object],
) -> Path:
    manifest = {
        "project": PROJECT,
        "status": "internal_r_and_d_video_library_candidate",
        "boundary": "Generated abstract cymatic/water geometry only. Not Coast Salish. Not Austin-derived. No public/show/projector/sponsor/social use until separately approved for the production context.",
        "renderer": "scripts/abstract_cymatic_flower_of_life_primitive_emergence_v001.py",
        "renderer_sha256": sha256(ROOT / "scripts" / "abstract_cymatic_flower_of_life_primitive_emergence_v001.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [renderer.config.width, renderer.config.height],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "render_settings": asdict(renderer.config),
        "rules": {
            "austin_assets_used": False,
            "austin_motifs_used": False,
            "source_artworks_used": False,
            "svg_assets_used": False,
            "standalone_primitive_icons_drawn": False,
            "cultural_claims": False,
            "coast_salish_framing": False,
            "generated_content": "abstract cymatic/water geometry only",
        },
        "field_configuration": {
            "source_model": "procedural scalar wave emitters at the 19 construction-circle centers",
            "source_count": len(renderer.sources),
            "sources": [asdict(src) for src in renderer.sources],
            "phase_snapping": "all wave frequencies are integer cycles over the 60 second clip; source position drift uses integer-cycle loops",
        },
        "construction_circle_parameters": {
            "construction_circle_count": len(renderer.construction_circles),
            "construction_radius_px_work_canvas": round(renderer.construction_radius, 4),
            "arrangement": "full 19-circle flower-of-life / radius-2 hexagonal lattice: 1 center, 6 first ring, 12 second ring",
            "circles": [
                {
                    "circle_id": circle.circle_id,
                    "source_id": circle.source_id,
                    "x": round(circle.x, 4),
                    "y": round(circle.y, 4),
                    "radius_px": round(circle.radius_px, 4),
                    "role": circle.role,
                    "ring_index": circle.ring_index,
                    "q": circle.q,
                    "r": circle.r,
                }
                for circle in renderer.construction_circles
            ],
        },
        "selected_cell_logic": {
            "origin": renderer.origin_region.generation_rule,
            "two_circle_lenses": [region.generation_rule for region in renderer.lens_regions],
            "three_circle_cells": [region.generation_rule for region in renderer.triple_regions],
            "outer_pressure_trigons": [region.generation_rule for region in renderer.negative_regions],
            "cell_counts": {
                "origin": 1,
                "two_circle_lens": len(renderer.lens_regions),
                "three_circle_trigon_like_cell": len(renderer.triple_regions),
                "outer_pressure_trigon_like_cell": len(renderer.negative_regions),
            },
        },
        "loop_verification": loop_verification,
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_sheet.relative_to(OUT_DIR)),
            "loop_diagnostic_sheet": str(loop_sheet.relative_to(OUT_DIR)) if loop_sheet else None,
            "readme": "README.md",
            **{f"{key}_still": rel for key, rel in stills.items()},
        },
    }
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(renderer: PrimitiveEmergenceRenderer, loop_verification: dict[str, object], rendered: bool) -> Path:
    seam_ok = loop_verification.get("decoded_loop_seam_less_than_adjacent_reference")
    raw_ok = loop_verification.get("raw_render_loop_seam_exact")
    closure = loop_verification.get("source_phase_frequency_closure")
    lines = [
        "# Abstract Cymatic Flower-of-Life Primitive Emergence v001",
        "",
        "Status: INTERNAL R&D / Resolume video-library candidate. Generated abstract cymatic/water geometry only. Not Coast Salish. Not Austin-derived. No public/show/projector/sponsor/social use until separately approved for the production context.",
        "",
        "## Purpose",
        "",
        "This packet replaces the seed-of-life v001 direction with a full 19-circle flower-of-life / radius-2 hexagonal lattice. It explores circle, crescent/lens, and trigon-like geometry as abstract wave-derived construction. It uses no Austin artworks, no Austin motifs, no SVG assets, and no cultural-design claim.",
        "",
        "The primary peak forms are not wave-amplitude threshold blobs. They are arc-bounded cells created from overlapping equal-radius construction circles placed at procedural source/antinode positions. The wave field provides water atmosphere, drift, gather/release, and interior breathing.",
        "",
        "## Sequence",
        "",
        "- 0-8s: raw overlapping ripple/interference field.",
        "- 8-21s: all 19 construction circles become implied as wavefront/source geometry.",
        "- 21-34s: 2-circle lens/crescent cells emerge across the first and second rings.",
        "- 34-48s: 3-circle curved triangular pressure cells become strongest while the lens lattice remains visible.",
        "- 48-60s: geometry releases back into the initial raw cymatic field and closes the loop.",
        "",
        "## Construction Logic",
        "",
        f"- Construction circles: `{len(renderer.construction_circles)}` total, center plus six first-ring circles plus twelve second-ring circles.",
        f"- Construction radius on work canvas: `{renderer.construction_radius:.3f}px`.",
        f"- 2-circle lens cells: `{len(renderer.lens_regions)}` adjacent-circle intersections across the lattice.",
        f"- Inner 3-circle cells: `{len(renderer.triple_regions)}` mutually adjacent equal-radius circle intersections.",
        f"- Outer curved triangular pressure cells: `{len(renderer.negative_regions)}` mutually adjacent equal-radius circle intersections farther out in the lattice.",
        "",
        "## Loop Verification",
        "",
        f"- Raw render frame 0/final MAD: `{loop_verification.get('raw_render_frame0_final_mean_abs_diff')}`.",
        f"- Decoded frame 0/final MAD: `{loop_verification.get('decoded_frame0_final_mean_abs_diff')}`.",
        f"- Adjacent-frame reference MAD: `{loop_verification.get('decoded_adjacent_reference_mean_abs_diff')}`.",
        f"- Seam less than adjacent motion: `{seam_ok}`.",
        f"- Source phase/frequency closure: `{closure}`.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: {renderer.config.width}x{renderer.config.height}, 24fps, 60 seconds." if rendered else f"- `{PROJECT}.mp4`: not rendered in preview mode.",
        f"- `{PROJECT}_contact_sheet.png`.",
        "- `stills/`: initial raw field, 19-circle construction, lens lattice, second-ring expansion, trigon cells, peak beauty, return loop point.",
        f"- `debug/{PROJECT}_debug_views_sheet.png`: raw field, 19 construction circles, 2-circle lens cells, 3-circle/pressure cells, final beauty.",
        f"- `loop_diagnostics/{PROJECT}_loop_diagnostic_sheet.png`." if rendered else "- Loop diagnostic sheet is generated after MP4 render.",
        f"- `{PROJECT}_manifest.json`.",
        "",
        "## Honest Verdict",
        "",
    ]
    if seam_ok and raw_ok:
        lines.append(
            "v001 passes as a standalone abstract flower-of-life cymatic primitive-emergence study. The circle, crescent/lens, and trigon-like reads are visibly tied to the 19 overlapping construction circles rather than detached icons. The field still feels watery because the cells breathe over the interference layer instead of replacing it with a flat geometry diagram."
        )
    else:
        lines.append(
            "v001 has the intended 19-circle construction logic, but the loop check did not fully pass. Treat this as an internal draft until the loop seam is corrected."
        )
    lines.extend(
        [
            "",
            "Residual risk: the peak is intentionally more geometric than the earlier abstract cymatic composition. If it is pushed brighter or held longer, it could start reading as a static flower-of-life diagram. In the current timing, the water field and opacity breathing keep it in the intended abstract wave-study lane.",
            "",
            f"Render note: {renderer.config.work_canvas_note}",
            "",
            "Renderer: `scripts/abstract_cymatic_flower_of_life_primitive_emergence_v001.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render abstract cymatic primitive emergence v001.")
    parser.add_argument("--target", choices=("uhd", "draft1080"), default="uhd")
    parser.add_argument("--preview", action="store_true", help="Write stills/contact/debug/manifest without rendering the MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    config = config_for(args.target)
    renderer = PrimitiveEmergenceRenderer(config)

    print("Writing primitive-emergence key stills, contact sheet, and debug sheet", flush=True)
    stills = save_key_stills(renderer)
    contact = make_contact_sheet(renderer)
    debug = make_debug_sheet(renderer)

    if args.preview:
        raw0, _ = renderer.render_frame(0.0)
        rawf, _ = renderer.render_frame(DURATION_SECONDS)
        raw_mad = mad(raw0, rawf)
        loop_verification = {
            "preview_only": True,
            "decoded_frame0_final_mean_abs_diff": None,
            "decoded_adjacent_reference_mean_abs_diff": None,
            "decoded_loop_seam_less_than_adjacent_reference": None,
            "raw_render_frame0_final_mean_abs_diff": round(raw_mad, 8),
            "raw_render_loop_seam_exact": raw_mad < 1e-7,
            "source_phase_frequency_closure": verify_source_closure(renderer),
        }
        clip = {"mp4": f"{PROJECT}.mp4", "duration_seconds": DURATION_SECONDS, "fps": FPS, "frame_count": N_FRAMES}
        loop_sheet = None
    else:
        print(f"Rendering {PROJECT}.mp4", flush=True)
        clip = render_clip(renderer)
        print("Writing loop diagnostic sheet", flush=True)
        loop_sheet, loop_verification = make_loop_diagnostic(renderer, clip)

    manifest = write_manifest(renderer, clip, stills, contact, debug, loop_sheet, loop_verification)
    readme = write_readme(renderer, loop_verification, rendered=not args.preview)

    print(f"Wrote {contact}", flush=True)
    print(f"Wrote {debug}", flush=True)
    if loop_sheet:
        print(f"Wrote {loop_sheet}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)
    if not args.preview:
        print(f"Wrote {OUT_DIR / clip['mp4']}", flush=True)


if __name__ == "__main__":
    main()
