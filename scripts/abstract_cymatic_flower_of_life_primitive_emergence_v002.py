#!/usr/bin/env python3
"""
Abstract cymatic flower-of-life primitive emergence v002.

Standalone procedural cymatic/water composition for the internal/show
development video library. Circle, crescent/lens, and concave trigon primitive
families are explicitly classified and revealed one at a time from a 19-circle
flower-of-life / hexagonal construction lattice. The wave field supplies water
atmosphere, drift, and breathing; the peak geometry is built from arc-bounded
cell masks rather than amplitude-threshold blobs.

Boundary: Austin-authorized internal/show-development prototype. Austin has
greenlit Austin-style / Coast Salish-style generated experiments for this
project. No Austin source artwork is used here; this is generated primitive
vocabulary exploration and still requires exact-output review before public,
sponsor, or unaffiliated use.
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
    / "abstract_cymatic_flower_of_life_primitive_emergence_v002_2026-05-22"
)
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

PROJECT = "abstract_cymatic_flower_of_life_primitive_emergence_v002"
FPS = 24
DURATION_SECONDS = 84.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

UHD_SIZE = (3840, 2160)
DRAFT_SIZE = (1920, 1080)

DEEP = (0, 5, 7)
DARK_WATER = (3, 18, 24)
INK = (0, 7, 9)
FORM_BLACK = (4, 9, 10)
DEEP_TEAL = (12, 56, 62)
TEAL = (48, 147, 152)
MUTED_TEAL = (78, 132, 132)
ICE_BLUE = (145, 219, 228)
WARM_CREAM = (235, 226, 194)
SOFT_GOLD = (245, 196, 90)
AMBER = (210, 118, 66)
OCHRE = (196, 143, 63)
FORM_RED = (152, 41, 31)
SALMON_RED = (209, 78, 53)
CONSTRUCTION = (160, 178, 165)
LABEL = (226, 234, 230)
BBOX_CACHE: dict[int, tuple[int, int, int, int] | None] = {}

KEY_STILLS = (
    ("initial_raw_interference", 0.0),
    ("nineteen_construction_circles", 10.0),
    ("phase_a_circle_family_only", 18.0),
    ("phase_b_crescent_lens_family_only", 31.0),
    ("phase_c_concave_trigon_family_only", 44.0),
    ("phase_d_all_three_families", 61.0),
    ("peak_beauty_composite", 64.0),
    ("return_loop_point", DURATION_SECONDS),
)

CONTACT_TIMES = (
    0.0,
    8.0,
    12.0,
    16.0,
    20.0,
    24.0,
    28.0,
    32.0,
    36.0,
    40.0,
    44.0,
    48.0,
    53.0,
    58.0,
    63.0,
    68.0,
    74.0,
    80.0,
    DURATION_SECONDS,
)

PEAK_TIME_SECONDS = 62.0


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
    def __init__(self, path: Path, *, fps: int, size: tuple[int, int], output_size: tuple[int, int] | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = size
        output_size = output_size or size
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
        ]
        if output_size != size:
            out_width, out_height = output_size
            cmd.extend(["-vf", f"scale={out_width}:{out_height}:flags=lanczos"])
        cmd.extend(
            [
                "-c:v",
                "h264_videotoolbox",
                "-pix_fmt",
                "yuv420p",
                "-b:v",
                "45M",
                "-maxrate",
                "70M",
                "-bufsize",
                "90M",
                "-tag:v",
                "avc1",
                "-movflags",
                "+faststart",
                str(path),
            ]
        )
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
        self.circle_regions, self.crescent_regions, self.trigon_regions = self._make_regions()
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

    def _make_regions(self) -> tuple[list[CellRegion], list[CellRegion], list[CellRegion]]:
        source_clear = self._make_source_clear_mask(self.construction_radius * 0.090)

        circle_regions: list[CellRegion] = []
        for idx, circle in enumerate(self.construction_circles):
            if circle.ring_index == 0:
                radius = circle.radius_px * 0.235
                fill = DEEP_TEAL
                outline = SOFT_GOLD
            elif circle.ring_index == 1:
                radius = circle.radius_px * 0.175
                fill = FORM_BLACK if idx % 2 else DEEP_TEAL
                outline = WARM_CREAM if idx % 2 else SOFT_GOLD
            else:
                radius = circle.radius_px * 0.130
                fill = TEAL if idx % 3 else FORM_RED
                outline = WARM_CREAM if idx % 3 else SOFT_GOLD
            mask = mask_intersection(self._solid_circle(circle.x, circle.y, radius, soften=1.1 * self.scale), self.field_boundary)
            circle_regions.append(
                CellRegion(
                    f"circle_family_{idx:02d}",
                    "circle_family",
                    (circle.circle_id,),
                    (circle.source_id,),
                    "visible source/wavefront circle primitive centered on one of the 19 equal-radius construction-circle centers",
                    fill,
                    outline,
                    mask,
                    mask_edge(mask, kernel=max(5, round(7 * self.scale) | 1), blur=1.7 * self.scale),
                )
            )

        crescent_regions: list[CellRegion] = []
        pairs = self._neighbor_pairs()
        center_spokes = [pair for pair in pairs if {pair[0].ring_index, pair[1].ring_index} == {0, 1}]
        first_ring_pairs = [pair for pair in pairs if pair[0].ring_index == 1 and pair[1].ring_index == 1]
        outer_ring_pairs = [pair for pair in pairs if pair[0].ring_index == 2 and pair[1].ring_index == 2]
        selected_pairs = first_ring_pairs[:6] + outer_ring_pairs[:12]
        for idx, (a, b) in enumerate(selected_pairs):
            pair_angle = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
            exact_lens = mask_intersection(self.circle_masks[a.circle_id], self.circle_masks[b.circle_id], self.field_boundary)
            exact_lens = mask_subtract(exact_lens, source_clear)
            if idx >= 6:
                # Alternate outer cells are local lunes from one circle minus its neighbor,
                # clipped near the shared arc so the crescent read is explicit.
                base = mask_subtract(self.circle_masks[a.circle_id], self.circle_masks[b.circle_id]) if idx % 2 else mask_subtract(self.circle_masks[b.circle_id], self.circle_masks[a.circle_id])
                window = self._pair_ellipse_window(a, b, long_axis=self.construction_radius * 1.22, short_axis=self.construction_radius * 0.42)
                mask = mask_intersection(base, window, self.field_boundary)
                region_class = "crescent_lune_family"
                rule = "two adjacent construction-circle arcs form a local lune/crescent clipped to the pair window for legible primitive-family reveal"
                fill = SALMON_RED if idx % 2 else OCHRE
            else:
                mask = exact_lens
                region_class = "vesica_lens_family"
                rule = "exact two-circle equal-radius intersection between adjacent flower-lattice construction circles"
                fill = WARM_CREAM if idx % 3 != 1 else ICE_BLUE
            mask = cv2.GaussianBlur(mask, (0, 0), 0.75 * self.scale)
            crescent_regions.append(
                CellRegion(
                    f"crescent_lens_family_{idx:02d}",
                    region_class,
                    (a.circle_id, b.circle_id),
                    (a.source_id, b.source_id),
                    rule,
                    fill,
                    FORM_BLACK,
                    mask,
                    mask_edge(mask, kernel=max(5, round(8 * self.scale) | 1), blur=1.8 * self.scale),
                )
            )

        trigon_regions: list[CellRegion] = []
        triples = self._neighbor_triples()
        mid_triples: list[tuple[ConstructionCircle, ConstructionCircle, ConstructionCircle]] = []
        outer_triples: list[tuple[ConstructionCircle, ConstructionCircle, ConstructionCircle]] = []
        for triple in triples:
            centroid_x = sum(circle.x for circle in triple) / 3.0
            centroid_y = sum(circle.y for circle in triple) / 3.0
            centroid_radius = math.hypot(centroid_x - self.cx, centroid_y - self.cy)
            if self.construction_radius * 0.95 < centroid_radius < self.construction_radius * 1.32:
                mid_triples.append(triple)
            elif centroid_radius >= self.construction_radius * 1.42:
                outer_triples.append(triple)
        selected_triples = mid_triples[:6] + outer_triples[::2][:6]
        for idx, triple in enumerate(selected_triples):
            centroid_x = sum(circle.x for circle in triple) / 3.0
            centroid_y = sum(circle.y for circle in triple) / 3.0
            centroid_angle = math.atan2(centroid_y - self.cy, centroid_x - self.cx)
            size = self.construction_radius * (0.32 if idx < 6 else 0.34)
            mask = self._concave_trigon_mask(centroid_x, centroid_y, centroid_angle + (math.pi / 6.0 if idx % 2 else 0.0), size)
            mask = mask_intersection(mask, self.field_boundary)
            mask = cv2.GaussianBlur(mask, (0, 0), 0.70 * self.scale)
            trigon_regions.append(
                CellRegion(
                    f"concave_trigon_family_{idx:02d}",
                    "concave_trigon_family",
                    tuple(circle.circle_id for circle in triple),
                    tuple(circle.source_id for circle in triple),
                    "concave-sided curved triangle generated as a local arc-cut pressure cell anchored to three mutually adjacent construction-circle centers",
                    FORM_RED if idx % 3 != 1 else AMBER,
                    SOFT_GOLD if idx % 2 else FORM_BLACK,
                    mask,
                    mask_edge(mask, kernel=max(5, round(7 * self.scale) | 1), blur=1.7 * self.scale),
                )
            )

        return circle_regions, crescent_regions, trigon_regions

    def _pair_ellipse_window(
        self,
        a: ConstructionCircle,
        b: ConstructionCircle,
        *,
        long_axis: float,
        short_axis: float,
    ) -> np.ndarray:
        mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        midpoint = (round((a.x + b.x) * 0.5), round((a.y + b.y) * 0.5))
        angle_deg = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        axes = (max(1, round(long_axis * 0.5)), max(1, round(short_axis * 0.5)))
        cv2.ellipse(mask, midpoint, axes, angle_deg, 0, 360, 255, -1, lineType=cv2.LINE_AA)
        return cv2.GaussianBlur(mask, (0, 0), 0.65 * self.scale)

    def _concave_trigon_mask(self, cx: float, cy: float, angle: float, size: float) -> np.ndarray:
        mask = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        vertices: list[tuple[float, float]] = []
        for i in range(3):
            theta = angle + TAU * (i / 3.0)
            vertices.append((cx + size * math.cos(theta), cy + size * math.sin(theta)))
        poly = np.array([[round(x), round(y)] for x, y in vertices], dtype=np.int32)
        cv2.fillPoly(mask, [poly], 255, lineType=cv2.LINE_AA)

        cuts = np.zeros_like(mask)
        for i in range(3):
            ax, ay = vertices[i]
            bx, by = vertices[(i + 1) % 3]
            mx = (ax + bx) * 0.5
            my = (ay + by) * 0.5
            outward_x = mx - cx
            outward_y = my - cy
            length = max(1e-6, math.hypot(outward_x, outward_y))
            outward_x /= length
            outward_y /= length
            cut_x = mx + outward_x * size * 0.55
            cut_y = my + outward_y * size * 0.55
            cv2.circle(cuts, (round(cut_x), round(cut_y)), max(2, round(size * 0.72)), 255, -1, lineType=cv2.LINE_AA)
        mask = mask_subtract(mask, cuts)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        return mask

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
        circle_dark = [region.mask for idx, region in enumerate(self.circle_regions) if idx % 3 == 0]
        circle_light = [region.mask for idx, region in enumerate(self.circle_regions) if idx % 3 != 0]
        lens_even = [region.mask for idx, region in enumerate(self.crescent_regions) if idx % 2 == 0]
        lens_odd = [region.mask for idx, region in enumerate(self.crescent_regions) if idx % 2 == 1]
        trigon_red = [region.mask for idx, region in enumerate(self.trigon_regions) if idx % 3 != 1]
        trigon_ochre = [region.mask for idx, region in enumerate(self.trigon_regions) if idx % 3 == 1]
        return {
            "circle_dark": mask_union(*circle_dark),
            "circle_light": mask_union(*circle_light),
            "circle_edges": mask_union(*(region.edge for region in self.circle_regions)),
            "lens_even": mask_union(*lens_even),
            "lens_odd": mask_union(*lens_odd),
            "lens_edges": mask_union(*(region.edge for region in self.crescent_regions)),
            "trigon_red": mask_union(*trigon_red),
            "trigon_ochre": mask_union(*trigon_ochre),
            "trigon_edges": mask_union(*(region.edge for region in self.trigon_regions)),
        }

    def source_positions(self, t: float) -> list[tuple[WaveSource, float, float, float]]:
        p = (t % DURATION_SECONDS) / DURATION_SECONDS
        levels = timeline_levels(t)
        lock = 0.78 * max(levels["construction"], levels["circle_family"], levels["crescent_family"], levels["trigon_family"], levels["all_families"])
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
        elif mode == "circles":
            self._draw_construction(frame, alpha=0.34, include_sources=False)
            self._draw_cell_regions(frame, self.circle_regions, 1.0, pulse_phase=levels["phase"], fill_scale=0.94)
            if labels:
                draw_text(frame, "3 Phase A: circle family only", (32, 48), 0.48)
        elif mode == "crescents":
            self._draw_construction(frame, alpha=0.42, include_sources=True)
            self._draw_cell_regions(frame, self.crescent_regions, 1.0, pulse_phase=levels["phase"], fill_scale=0.98)
            if labels:
                draw_text(frame, "4 Phase B: crescent / vesica / lens family only", (32, 48), 0.43)
        elif mode == "trigons":
            self._draw_construction(frame, alpha=0.38, include_sources=True)
            self._draw_cell_regions(frame, self.trigon_regions, 1.0, pulse_phase=levels["phase"], fill_scale=1.0)
            if labels:
                draw_text(frame, "5 Phase C: concave-sided trigon family only", (32, 48), 0.44)
        else:
            self._draw_water_breath(frame, t, 0.10 + 0.13 * max(levels["trigon_family"], levels["all_families"]))
            self._draw_beauty_geometry(frame, levels)
            if labels:
                draw_text(frame, "6 Phase D: circle + crescent/lens + trigon families", (32, 48), 0.44)

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
        geometry_strength = max(levels["circle_family"], levels["crescent_family"], levels["trigon_family"], levels["all_families"])
        out = frame.astype(np.float32)
        for mask, rgb, alpha in (
            (neg, TEAL, 0.34 + 0.07 * geometry_strength),
            (pos, WARM_CREAM, 0.20 + 0.08 * levels["crescent_family"]),
            (nodes, INK, 0.44 + 0.10 * levels["trigon_family"]),
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
            if region.region_class == "circle_family":
                fill_alpha = 0.54 * alpha * pulse * fill_scale
                edge_alpha = 0.48 * alpha
            elif region.region_class == "crescent_lune_family":
                fill_alpha = 0.64 * alpha * pulse * fill_scale
                edge_alpha = 0.43 * alpha
            elif region.region_class == "vesica_lens_family":
                fill_alpha = 0.46 * alpha * pulse * fill_scale
                edge_alpha = 0.36 * alpha
            elif region.region_class == "concave_trigon_family":
                fill_alpha = 0.58 * alpha * pulse * fill_scale
                edge_alpha = 0.42 * alpha
            else:
                fill_alpha = 0.48 * alpha * fill_scale
                edge_alpha = 0.45 * alpha
            blend_mask_roi(frame, region.mask, region.fill_rgb, fill_alpha, glow=0.004 * alpha)
            blend_mask_roi(frame, region.edge, region.outline_rgb, edge_alpha)

    def _draw_beauty_geometry(self, frame: np.ndarray, levels: dict[str, float]) -> None:
        construction_alpha = 0.18 * levels["construction"] + 0.05 * max(
            levels["circle_family"], levels["crescent_family"], levels["trigon_family"], levels["all_families"]
        )
        self._draw_construction(frame, alpha=construction_alpha, include_sources=False)
        self._draw_cell_unions(frame, levels)

    def _draw_cell_unions(self, frame: np.ndarray, levels: dict[str, float]) -> None:
        crescent_alpha = max(levels["crescent_family"], levels["all_families"])
        if crescent_alpha > 0.0:
            self._draw_cell_regions(frame, self.crescent_regions, crescent_alpha, pulse_phase=levels["phase"], fill_scale=0.98)

        trigon_alpha = max(levels["trigon_family"], levels["all_families"])
        if trigon_alpha > 0.0:
            self._draw_cell_regions(frame, self.trigon_regions, trigon_alpha, pulse_phase=levels["phase"], fill_scale=1.0)

        circle_alpha = max(levels["circle_family"], levels["all_families"])
        if circle_alpha > 0.0:
            self._draw_cell_regions(frame, self.circle_regions, circle_alpha, pulse_phase=levels["phase"], fill_scale=0.94)


def np_smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep01(value: float) -> float:
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def envelope(t: float, start: float, in_seconds: float, out_start: float, out_seconds: float) -> float:
    return smoothstep01((t - start) / in_seconds) * (1.0 - smoothstep01((t - out_start) / out_seconds))


def timeline_levels(t: float) -> dict[str, float]:
    circle_family = envelope(t, 14.0, 2.0, 24.0, 2.0)
    crescent_family = envelope(t, 27.0, 2.0, 37.0, 2.0)
    trigon_family = envelope(t, 40.0, 2.0, 50.0, 2.0)
    all_families = envelope(t, 53.0, 3.0, 69.0, 4.0)
    return {
        "phase": (t % DURATION_SECONDS) / DURATION_SECONDS,
        "construction": envelope(t, 6.0, 5.0, 71.0, 8.0),
        "circle_family": circle_family,
        "crescent_family": crescent_family,
        "trigon_family": trigon_family,
        "all_families": all_families,
        "raw_release": 1.0 - max(circle_family, crescent_family, trigon_family, all_families),
    }


def source_strength(src: WaveSource, t: float) -> float:
    levels = timeline_levels(t)
    if src.role == "center_antinode":
        return 0.32 + 0.68 * max(levels["circle_family"], levels["all_families"])
    if src.role == "first_ring_antinode":
        return 0.20 + 0.80 * max(levels["construction"], levels["circle_family"], levels["crescent_family"], 0.74 * levels["all_families"])
    return 0.18 + 0.82 * max(0.30 * levels["construction"], levels["crescent_family"], levels["trigon_family"], levels["all_families"])


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
        note = "UHD encode from a 1600x900 procedural work canvas with ffmpeg Lanczos scaling to 3840x2160."
    else:
        work_width = width
        work_height = height
        note = "Draft encode and procedural work canvas are both 1920x1080."
    field_width = 400 if work_width >= 1600 else 360
    field_height = 225 if work_width >= 1600 else 202
    return RenderConfig(width, height, work_width, work_height, field_width, field_height, FPS, DURATION_SECONDS, N_FRAMES, note)


def render_clip(renderer: PrimitiveEmergenceRenderer) -> dict[str, object]:
    mp4_path = OUT_DIR / f"{PROJECT}.mp4"
    input_size = (renderer.config.work_width, renderer.config.work_height)
    output_size = (renderer.config.width, renderer.config.height)
    writer = H264Writer(mp4_path, fps=FPS, size=input_size, output_size=output_size)
    try:
        for frame_idx in range(N_FRAMES):
            t = timeline_time_for_frame(frame_idx)
            frame, _info = renderer.render_frame(t, output_size=False)
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
        "input_size": input_size,
        "output_size": output_size,
        "upscale": "ffmpeg lanczos scale from procedural work canvas to final UHD frame" if input_size != output_size else "none",
        "video_encoder": "h264_videotoolbox",
        "target_video_bitrate": "45M",
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
        ("Phase A: circle family only", "circles"),
        ("Phase B: crescent/lens family only", "crescents"),
        ("Phase C: concave trigon family only", "trigons"),
        ("Phase D beauty composite", "beauty"),
    ]
    panels = []
    for label, mode in views:
        frame, _info = renderer.render_frame(PEAK_TIME_SECONDS, mode=mode, labels=False)
        panels.append(label_panel(frame, label, size=(768, 432)))
    sheet = cv2.hconcat(panels)
    draw_text(sheet, "debug views: raw field -> construction -> circles only -> crescents/lenses only -> concave trigons only -> all families", (28, sheet.shape[0] - 24), 0.42)
    path = DEBUG_DIR / f"{PROJECT}_debug_views_sheet.png"
    cv2.imwrite(str(path), sheet)

    for label, mode in views:
        frame, _info = renderer.render_frame(PEAK_TIME_SECONDS, mode=mode, labels=True)
        cv2.imwrite(str(DEBUG_DIR / f"{PROJECT}_{mode}_debug_peak.png"), frame)
    return path


def make_classification_sheet(renderer: PrimitiveEmergenceRenderer) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    views = [
        (18.0, "circles", f"circle family | {len(renderer.circle_regions)} cells | source/wavefront centers"),
        (31.0, "crescents", f"crescent/lens family | {len(renderer.crescent_regions)} cells | vesica + lune arcs"),
        (44.0, "trigons", f"concave trigon family | {len(renderer.trigon_regions)} cells | arc-cut pressure cells"),
        (62.0, "beauty", "Phase D | all three classified families together"),
    ]
    panels = []
    for t, mode, label in views:
        frame, _info = renderer.render_frame(t, mode=mode, labels=False)
        panels.append(label_panel(frame, label, size=(960, 540)))
    sheet = cv2.hconcat(panels)
    draw_text(sheet, "classification sheet: selected cells are grouped by primitive family before the combined reveal", (28, sheet.shape[0] - 24), 0.42)
    path = DEBUG_DIR / f"{PROJECT}_classification_sheet.png"
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
        label_panel(ff, f"decoded final frame {N_FRAMES - 1} / sampled at {DURATION_SECONDS:.1f}s"),
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
    classification_sheet: Path,
    loop_sheet: Path | None,
    loop_verification: dict[str, object],
) -> Path:
    cell_counts = {
        "circle_family": len(renderer.circle_regions),
        "crescent_lens_family": len(renderer.crescent_regions),
        "concave_trigon_family": len(renderer.trigon_regions),
        "total_selected_classified_cells": len(renderer.circle_regions) + len(renderer.crescent_regions) + len(renderer.trigon_regions),
    }
    manifest = {
        "project": PROJECT,
        "status": "austin_authorized_internal_show_development_prototype",
        "boundary": "Austin-authorized internal/show-development prototype. Austin has greenlit Austin-style / Coast Salish-style generated experiments for this project. No Austin source artwork is used in this render; generated Coast Salish/Austin-style primitive exploration requires exact-output review before public, sponsor, or unaffiliated use.",
        "renderer": "scripts/abstract_cymatic_flower_of_life_primitive_emergence_v002.py",
        "renderer_sha256": sha256(ROOT / "scripts" / "abstract_cymatic_flower_of_life_primitive_emergence_v002.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [renderer.config.width, renderer.config.height],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "render_settings": asdict(renderer.config),
        "rules": {
            "austin_assets_used": False,
            "austin_source_artwork_used": False,
            "austin_style_generated_experiment_authorized": True,
            "source_artworks_used": False,
            "svg_assets_used": False,
            "standalone_primitive_icons_drawn": False,
            "cultural_claims": False,
            "coast_salish_primitive_vocabulary_used": "generated circle / crescent-lens / concave trigon primitive vocabulary, Austin-authorized for this project context",
            "generated_content": "procedural cymatic/water geometry and generated Austin-style / Coast Salish-style primitive exploration",
            "review_status": "internal prototype, exact output still needs Austin/project review",
        },
        "field_configuration": {
            "source_model": "procedural scalar wave emitters at the 19 construction-circle centers",
            "source_count": len(renderer.sources),
            "sources": [asdict(src) for src in renderer.sources],
            "phase_snapping": f"all wave frequencies are integer cycles over the {DURATION_SECONDS:.0f} second clip; source position drift uses integer-cycle loops",
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
        "primitive_family_counts": cell_counts,
        "sequence": {
            "raw_water_cymatic_field": "0-8s",
            "construction_circles_faint": "6-14s fade-in; faint scaffolding persists through primitive reveals",
            "phase_a_circles_only": "14-26s envelope, with >=8s fully legible circle-family hold from 16-24s",
            "phase_b_crescents_lenses_only": "27-39s envelope, with >=8s fully legible crescent/lens-family hold from 29-37s",
            "phase_c_trigons_only": "40-52s envelope, with >=8s fully legible concave-trigon-family hold from 42-50s",
            "phase_d_all_three_families": "53-73s envelope, with >=12s fully legible combined hold from 56-69s",
            "release_to_water_field": "73-84s",
        },
        "selected_cell_logic": {
            "circle_family": [region.generation_rule for region in renderer.circle_regions],
            "crescent_lens_family": [region.generation_rule for region in renderer.crescent_regions],
            "concave_trigon_family": [region.generation_rule for region in renderer.trigon_regions],
            "cell_counts_per_primitive_family": cell_counts,
            "classification_contract": "Every visible primitive cell belongs to exactly one of circle_family, crescent_lens_family, or concave_trigon_family; Phase A/B/C reveal only one family at a time, Phase D reveals all three.",
        },
        "loop_verification": loop_verification,
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_sheet.relative_to(OUT_DIR)),
            "classification_sheet": str(classification_sheet.relative_to(OUT_DIR)),
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
        "# Abstract Cymatic Flower-of-Life Primitive Emergence v002",
        "",
        "Status: Austin-authorized internal/show-development prototype. Austin has explicitly greenlit Austin-style / Coast Salish-style generated experiments for this project. No Austin source artwork is used in this render. Treat this as generated primitive-vocabulary exploration pending exact-output review before public, sponsor, or unaffiliated use.",
        "",
        "## Purpose",
        "",
        "v002 keeps the full 19-circle flower-of-life / radius-2 hexagonal lattice from v001, but fixes the core visual issue: primitive families are explicitly classified and revealed sequentially instead of filling the lattice as one uniform mandala.",
        "",
        "The primary peak forms are not wave-amplitude threshold blobs. Circle, crescent/lens, and concave-trigon regions are precomputed as arc-bounded primitive-family masks derived from the construction-circle lattice. The wave field provides water atmosphere, drift, gather/release, and interior breathing.",
        "",
        "## Sequence",
        "",
        "- 0-8s: raw overlapping ripple/interference field.",
        "- 6-14s: all 19 construction circles appear faintly as scaffold/wavefront logic.",
        "- 14-26s: Phase A, circle family only; the fully legible hold is 16-24s.",
        "- 27-39s: Phase B, crescent / vesica / lens family only; the fully legible hold is 29-37s.",
        "- 40-52s: Phase C, concave-sided trigon family only; the fully legible hold is 42-50s.",
        "- 53-73s: Phase D, all three primitive families together; the fully legible hold is 56-69s.",
        "- 73-84s: release back to the raw water/cymatic field and close the loop.",
        "",
        "## Construction Logic",
        "",
        f"- Construction circles: `{len(renderer.construction_circles)}` total, center plus six first-ring circles plus twelve second-ring circles.",
        f"- Construction radius on work canvas: `{renderer.construction_radius:.3f}px`.",
        f"- Circle-family cells: `{len(renderer.circle_regions)}` visible source/wavefront circles anchored to the construction-circle centers.",
        f"- Crescent/lens-family cells: `{len(renderer.crescent_regions)}` sparse two-circle vesica/lune regions selected from adjacent construction-circle pairs.",
        f"- Concave-trigon-family cells: `{len(renderer.trigon_regions)}` arc-cut curved triangular pressure cells anchored to mutually adjacent construction-circle triples.",
        "- Phase A/B/C are family-exclusive except for the faint construction scaffold; Phase D combines the three family layers with distinct color/edge treatment.",
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
        f"- `{PROJECT}.mp4`: {renderer.config.width}x{renderer.config.height}, 24fps, {DURATION_SECONDS:.0f} seconds." if rendered else f"- `{PROJECT}.mp4`: not rendered in preview mode.",
        f"- `{PROJECT}_contact_sheet.png`.",
        "- `stills/`: initial raw field, 19-circle construction, Phase A circles, Phase B crescents/lenses, Phase C trigons, Phase D composite, return loop point.",
        f"- `debug/{PROJECT}_debug_views_sheet.png`: raw field, construction, family-exclusive views, final beauty.",
        f"- `debug/{PROJECT}_classification_sheet.png`: primitive-family classification sheet with counts.",
        f"- `loop_diagnostics/{PROJECT}_loop_diagnostic_sheet.png`." if rendered else "- Loop diagnostic sheet is generated after MP4 render.",
        f"- `{PROJECT}_manifest.json`.",
        "",
        "## Honest Verdict",
        "",
    ]
    if seam_ok and raw_ok:
        lines.append(
            "v002 is a stronger prototype than v001 for the stated brief. The family-exclusive holds make the derivation readable: circles read as source/wavefront primitives, the sparse vesica/lune layer reads as crescent/lens geometry, and the red/ochre pressure cells read as concave-sided trigons before the combined Phase D. The combined state is still decorative, but it no longer depends on a uniform lattice fill."
        )
    else:
        lines.append(
            "v002 has the intended classified primitive-family sequence, but the loop check did not fully pass. Treat this as an internal draft until the loop seam is corrected."
        )
    lines.extend(
        [
            "",
            "Residual risk: this is intentionally closer to Coast Salish/Austin-style primitive vocabulary than v001 under the updated permission context. It is Austin-authorized project work, but it is not a substitute for Austin's review of the exact output. The renderer uses no Austin source artwork.",
            "",
            f"Render note: {renderer.config.work_canvas_note}",
            "",
            "Renderer: `scripts/abstract_cymatic_flower_of_life_primitive_emergence_v002.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render abstract cymatic primitive emergence v002.")
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
    classification = make_classification_sheet(renderer)

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

    manifest = write_manifest(renderer, clip, stills, contact, debug, classification, loop_sheet, loop_verification)
    readme = write_readme(renderer, loop_verification, rendered=not args.preview)

    print(f"Wrote {contact}", flush=True)
    print(f"Wrote {debug}", flush=True)
    print(f"Wrote {classification}", flush=True)
    if loop_sheet:
        print(f"Wrote {loop_sheet}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)
    if not args.preview:
        print(f"Wrote {OUT_DIR / clip['mp4']}", flush=True)


if __name__ == "__main__":
    main()
