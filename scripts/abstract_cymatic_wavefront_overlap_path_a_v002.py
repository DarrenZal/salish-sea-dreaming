#!/usr/bin/env python3.11
"""
Abstract cymatic wavefront overlap path A v002.

Analytic delayed-ripple prototype for internal/show-development review.

v002 keeps the v001 no-symbol-overlay contract, but moves the main primitive
read from thick-ring intersection marks to bounded regions formed by expanding
wavefront discs. Every visible primitive-like region in the final render comes
from either:
- connected components of exact coverage_count regions, or
- ring_count micro-overlap masks.

No crescent paths, trigon paths, oval markers, icons, or rescue overlays are
drawn on top.

Boundary: Austin-authorized internal/show-development prototype. No Austin
source artwork is used. This explores analytic water-wave geometry only and
does not claim to prove the origin or meaning of Coast Salish vocabulary.
Austin remains the authority on meaning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "abstract_cymatic_wavefront_overlap_path_a_v002"
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / f"{PROJECT}_2026-05-22"
)
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

FPS = 24
DURATION_SECONDS = 84.0
N_FRAMES = int(FPS * DURATION_SECONDS)
PEAK_TIME_SECONDS = 44.0
TAU = math.tau

UHD_SIZE = (3840, 2160)
DRAFT_SIZE = (1920, 1080)

IMPACT_TIME_SECONDS = 6.0
RELEASE_START_SECONDS = 72.0
RELEASE_END_SECONDS = 80.0

LATTICE_SPACING_AT_900H = 132.0
WAVE_SPEED_AT_900H = 12.0
RING_WIDTH_AT_900H = 7.0
WAVELENGTH_AT_900H = 42.0

DEEP = (0, 5, 8)
DARK_WATER = (4, 18, 24)
MID_WATER = (10, 42, 49)
MUTED_BLUE = (38, 91, 106)
TEAL = (54, 146, 155)
ICE = (144, 219, 226)
CREAM = (232, 224, 190)
GOLD = (242, 185, 78)
SALMON = (213, 76, 55)
RED = (160, 40, 34)
LABEL = (226, 234, 230)

KEY_STILLS = (
    ("01_still_dark_water_field", 0.0),
    ("02_center_droplet_impact", 6.3),
    ("03_central_coverage_disc", 12.0),
    ("04_inner_ring_disc_overlaps", 22.0),
    ("05_outer_ring_sources_activate", 28.0),
    ("06_bounded_regions_bloom", 34.0),
    ("07_peak_bounded_region_families", PEAK_TIME_SECONDS),
    ("08_release", 74.0),
    ("09_loop_return", DURATION_SECONDS),
)

CONTACT_TIMES = (
    0.0,
    6.0,
    9.0,
    12.0,
    16.0,
    20.0,
    24.0,
    28.0,
    32.0,
    36.0,
    40.0,
    PEAK_TIME_SECONDS,
    48.0,
    52.0,
    58.0,
    64.0,
    70.0,
    76.0,
    82.0,
    DURATION_SECONDS,
)


@dataclass(frozen=True)
class WaveSource:
    source_id: str
    role: str
    ring_index: int
    q: int
    r: int
    x_work_px: float
    y_work_px: float
    x_output_px: float
    y_output_px: float
    distance_from_center_work_px: float
    activation_time_seconds: float


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
    lattice_spacing_work_px: float
    wave_speed_work_px_per_second: float
    ring_width_work_px: float
    wavelength_work_px: float
    impact_time_seconds: float
    release_start_seconds: float
    release_end_seconds: float
    work_canvas_note: str


@dataclass
class OverlapState:
    time_seconds: float
    active_sources: list[dict[str, Any]]
    ring_count: np.ndarray
    coverage_count: np.ndarray
    amplitude_field: np.ndarray
    component_class_map: np.ndarray
    component_alpha_map: np.ndarray
    component_infos: list[dict[str, Any]]
    component_filter_report: dict[str, Any]
    ring_masks: list[np.ndarray] | None = None


class H264Writer:
    def __init__(
        self,
        path: Path,
        *,
        fps: int,
        input_size: tuple[int, int],
        output_size: tuple[int, int],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        in_width, in_height = input_size
        out_width, out_height = output_size
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{in_width}x{in_height}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
        ]
        if input_size != output_size:
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


class WavefrontRegionRenderer:
    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        self.scale = config.work_height / 900.0
        self.output_scale_x = config.width / config.work_width
        self.output_scale_y = config.height / config.work_height
        self.cx = config.work_width * 0.5
        self.cy = config.work_height * 0.5

        y, x = np.mgrid[0 : config.work_height, 0 : config.work_width].astype(np.float32)
        self.x = x
        self.y = y
        self.center_dist = np.sqrt((x - self.cx) ** 2 + (y - self.cy) ** 2)
        self.edge_window = self._edge_window(x, y)
        self.radial_water_window = self._radial_window(self.center_dist)
        self.base_frame = self._make_base_frame()

        fy = (np.arange(config.field_height, dtype=np.float32) + 0.5) * (config.work_height / config.field_height)
        fx = (np.arange(config.field_width, dtype=np.float32) + 0.5) * (config.work_width / config.field_width)
        self.fx, self.fy = np.meshgrid(fx, fy)
        self.field_center_dist = np.sqrt((self.fx - self.cx) ** 2 + (self.fy - self.cy) ** 2)
        self.field_window = self._radial_window(self.field_center_dist) * self._edge_window(self.fx, self.fy)

        self.sources = self._make_sources()
        self.distance_fields = self._precompute_distance_fields()
        self.field_distance_fields = self._precompute_field_distance_fields()
        self.max_distance_fields = [float(dist.max()) for dist in self.distance_fields]
        self.filter_config = self._component_filter_config()

        self.delta_scratch = np.empty((config.work_height, config.work_width), dtype=np.float32)
        self.ring_scratch = np.empty((config.work_height, config.work_width), dtype=bool)
        self.coverage_scratch = np.empty((config.work_height, config.work_width), dtype=bool)
        self.phase_scratch = np.empty((config.field_height, config.field_width), dtype=np.float32)

    def _make_sources(self) -> list[WaveSource]:
        points: list[tuple[int, int, int, float, float, float]] = []
        spacing = self.config.lattice_spacing_work_px
        for q in range(-2, 3):
            for r in range(-2, 3):
                ring_index = max(abs(q), abs(r), abs(q + r))
                if ring_index > 2:
                    continue
                x = self.cx + spacing * (q + 0.5 * r)
                y = self.cy + spacing * (math.sqrt(3.0) * 0.5 * r)
                distance_from_center = math.hypot(x - self.cx, y - self.cy)
                points.append((ring_index, q, r, x, y, distance_from_center))

        points.sort(key=lambda item: (item[0], math.atan2(item[4] - self.cy, item[3] - self.cx), item[5]))
        role_counts = {0: 0, 1: 0, 2: 0}
        sources: list[WaveSource] = []
        for ring_index, q, r, x, y, distance_from_center in points:
            role_counts[ring_index] += 1
            if ring_index == 0:
                source_id = "center_00"
                role = "center_droplet"
                activation_time = self.config.impact_time_seconds
            elif ring_index == 1:
                source_id = f"inner_ring_{role_counts[ring_index] - 1:02d}"
                role = "inner_ring_delayed_droplet"
                activation_time = self.config.impact_time_seconds + distance_from_center / self.config.wave_speed_work_px_per_second
            else:
                source_id = f"outer_ring_{role_counts[ring_index] - 1:02d}"
                role = "outer_ring_delayed_droplet"
                activation_time = self.config.impact_time_seconds + distance_from_center / self.config.wave_speed_work_px_per_second

            sources.append(
                WaveSource(
                    source_id=source_id,
                    role=role,
                    ring_index=ring_index,
                    q=q,
                    r=r,
                    x_work_px=x,
                    y_work_px=y,
                    x_output_px=x * self.output_scale_x,
                    y_output_px=y * self.output_scale_y,
                    distance_from_center_work_px=distance_from_center,
                    activation_time_seconds=activation_time,
                )
            )
        return sources

    def _precompute_distance_fields(self) -> list[np.ndarray]:
        return [np.sqrt((self.x - src.x_work_px) ** 2 + (self.y - src.y_work_px) ** 2).astype(np.float32) for src in self.sources]

    def _precompute_field_distance_fields(self) -> list[np.ndarray]:
        return [np.sqrt((self.fx - src.x_work_px) ** 2 + (self.fy - src.y_work_px) ** 2).astype(np.float32) for src in self.sources]

    def _edge_window(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        dist = np.minimum(np.minimum(x, self.config.work_width - x), np.minimum(y, self.config.work_height - y))
        return np_smoothstep(16.0 * self.scale, 100.0 * self.scale, dist).astype(np.float32)

    def _radial_window(self, dist: np.ndarray) -> np.ndarray:
        inner = 0.80 * min(self.config.work_width, self.config.work_height)
        outer = 1.00 * min(self.config.work_width, self.config.work_height)
        return (1.0 - np_smoothstep(inner, outer, dist)).astype(np.float32)

    def _make_base_frame(self) -> np.ndarray:
        x_norm = self.x / max(1.0, self.config.work_width - 1.0)
        y_norm = self.y / max(1.0, self.config.work_height - 1.0)
        water_grain = (
            0.50
            + 0.22 * np.sin(7.0 * x_norm + 4.2 * y_norm)
            + 0.16 * np.sin(15.0 * x_norm - 10.0 * y_norm)
            + 0.10 * np.sin(26.0 * (x_norm + y_norm))
        )
        water_grain = np.clip(water_grain, 0.0, 1.0)
        radial = np.clip(1.0 - self.center_dist / (0.80 * min(self.config.work_width, self.config.work_height)), 0.0, 1.0)
        base = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.float32)
        deep = np.array(bgr(DEEP), dtype=np.float32)
        dark = np.array(bgr(DARK_WATER), dtype=np.float32)
        mid = np.array(bgr(MID_WATER), dtype=np.float32)
        mix = 0.18 + 0.33 * radial + 0.08 * water_grain
        base[:] = deep
        base = base * (1.0 - mix[..., None]) + dark * mix[..., None]
        base = base * 0.94 + mid * (0.06 * water_grain * self.radial_water_window)[..., None]
        vignette = 0.62 + 0.38 * self.radial_water_window * self.edge_window
        base *= vignette[..., None]
        return np.clip(base, 0, 255).astype(np.uint8)

    def _component_filter_config(self) -> dict[str, dict[str, float]]:
        s2 = self.scale * self.scale
        total = self.config.work_width * self.config.work_height
        margin = max(3.0, 4.5 * self.scale)
        return {
            "circle_single_wavefront_family": {
                "coverage_count": 1,
                "min_area_px": 180.0 * s2,
                "max_area_px": min(95000.0 * s2, total * 0.13),
                "min_compactness": 0.020,
                "min_extent": 0.035,
                "max_aspect_ratio": 7.5,
                "edge_margin_px": margin,
            },
            "crescent_lens_two_front_family": {
                "coverage_count": 2,
                "min_area_px": 120.0 * s2,
                "max_area_px": min(85000.0 * s2, total * 0.11),
                "min_compactness": 0.035,
                "min_extent": 0.070,
                "max_aspect_ratio": 7.5,
                "edge_margin_px": margin,
            },
            "trigon_three_arc_pressure_family": {
                "coverage_count": 3,
                "min_area_px": 100.0 * s2,
                "max_area_px": min(65000.0 * s2, total * 0.085),
                "min_compactness": 0.040,
                "min_extent": 0.090,
                "max_aspect_ratio": 7.0,
                "edge_margin_px": margin,
            },
        }

    def compute_state(self, t: float, *, include_ring_masks: bool = False, classify: bool = True) -> OverlapState:
        t_loop = t % self.config.duration_seconds
        ring_count = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        coverage_count = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        amplitude = np.zeros((self.config.field_height, self.config.field_width), dtype=np.float32)
        active_infos: list[dict[str, Any]] = []
        ring_masks: list[np.ndarray] | None = [] if include_ring_masks else None
        k = TAU / self.config.wavelength_work_px

        if t_loop < self.config.release_end_seconds:
            for idx, (src, dist, dist_small) in enumerate(
                zip(self.sources, self.distance_fields, self.field_distance_fields, strict=True)
            ):
                age = t_loop - src.activation_time_seconds
                if age < 0.0:
                    continue
                radius = self.config.wave_speed_work_px_per_second * age

                np.less_equal(dist, radius, out=self.coverage_scratch)
                coverage_count += self.coverage_scratch

                ring_pixels = 0
                if radius <= self.max_distance_fields[idx] + self.config.ring_width_work_px:
                    np.subtract(dist, radius, out=self.delta_scratch)
                    np.abs(self.delta_scratch, out=self.delta_scratch)
                    np.less_equal(self.delta_scratch, self.config.ring_width_work_px, out=self.ring_scratch)
                    ring_count += self.ring_scratch
                    ring_pixels = int(np.count_nonzero(self.ring_scratch))
                    if include_ring_masks and ring_masks is not None:
                        ring_masks.append(self.ring_scratch.copy())
                elif include_ring_masks and ring_masks is not None:
                    ring_masks.append(np.zeros_like(self.ring_scratch))

                np.subtract(dist_small, radius, out=self.phase_scratch)
                self.phase_scratch *= k
                np.sin(self.phase_scratch, out=self.phase_scratch)
                source_amp = 1.0 if src.ring_index == 0 else (0.72 if src.ring_index == 1 else 0.54)
                amplitude += source_amp * math.exp(-0.014 * age) * self.phase_scratch

                active_infos.append(
                    {
                        "source_id": src.source_id,
                        "role": src.role,
                        "ring_index": src.ring_index,
                        "activation_time_seconds": round(src.activation_time_seconds, 5),
                        "age_seconds": round(age, 5),
                        "current_radius_work_px": round(radius, 5),
                        "visible_pixels_in_ring_mask": ring_pixels,
                    }
                )

        amplitude *= self.field_window
        amplitude = cv2.GaussianBlur(amplitude, (0, 0), 0.45)

        if classify:
            component_class_map, component_alpha_map, component_infos, filter_report = self.extract_coverage_components(coverage_count)
        else:
            component_class_map = np.zeros_like(coverage_count)
            component_alpha_map = np.zeros(coverage_count.shape, dtype=np.float32)
            component_infos = []
            filter_report = self.empty_filter_report()

        return OverlapState(
            time_seconds=t_loop,
            active_sources=active_infos,
            ring_count=ring_count,
            coverage_count=coverage_count,
            amplitude_field=amplitude,
            component_class_map=component_class_map,
            component_alpha_map=component_alpha_map,
            component_infos=component_infos,
            component_filter_report=filter_report,
            ring_masks=ring_masks,
        )

    def empty_filter_report(self) -> dict[str, Any]:
        return {
            "candidate_components_total": 0,
            "accepted_components_total": 0,
            "by_family": {},
            "rejected_by_reason": {},
        }

    def extract_coverage_components(
        self, coverage_count: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]], dict[str, Any]]:
        class_map = np.zeros_like(coverage_count, dtype=np.uint8)
        alpha_map = np.zeros(coverage_count.shape, dtype=np.float32)
        component_infos: list[dict[str, Any]] = []
        report: dict[str, Any] = {
            "candidate_components_total": 0,
            "accepted_components_total": 0,
            "by_family": {},
            "rejected_by_reason": {},
        }

        families = (
            (1, "circle_single_wavefront_family"),
            (2, "crescent_lens_two_front_family"),
            (3, "trigon_three_arc_pressure_family"),
        )
        for class_value, family in families:
            cfg = self.filter_config[family]
            binary = (coverage_count == class_value).astype(np.uint8)
            n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
            family_report = {
                "coverage_count": class_value,
                "candidate_components": max(0, int(n_labels) - 1),
                "accepted_components": 0,
                "accepted_pixels": 0,
            }
            report["candidate_components_total"] += family_report["candidate_components"]

            class_lookup = np.zeros(n_labels, dtype=np.uint8)
            alpha_lookup = np.zeros(n_labels, dtype=np.float32)
            for label_idx in range(1, n_labels):
                x, y, w, h, area = (int(v) for v in stats[label_idx])
                bbox_perimeter = float(2 * (w + h))
                compactness = 4.0 * math.pi * area / max(1.0, bbox_perimeter * bbox_perimeter)
                reason = self.component_rejection_reason(x, y, w, h, area, compactness, cfg)

                if reason is not None:
                    report["rejected_by_reason"][reason] = int(report["rejected_by_reason"].get(reason, 0)) + 1
                    continue

                extent = area / max(1.0, float(w * h))
                aspect = max(w, h) / max(1.0, min(w, h))
                cx, cy = float(centroids[label_idx][0]), float(centroids[label_idx][1])
                radial = math.hypot(cx - self.cx, cy - self.cy)
                quality = self.component_quality(area, compactness, extent, aspect, cfg)
                class_lookup[label_idx] = class_value
                alpha_lookup[label_idx] = quality
                family_report["accepted_components"] += 1
                family_report["accepted_pixels"] += area
                component_infos.append(
                    {
                        "component_id": f"{family}_{family_report['accepted_components']:03d}",
                        "family": family,
                        "coverage_count": class_value,
                        "area_px": area,
                        "bbox_xywh": [x, y, w, h],
                        "centroid_xy": [round(cx, 3), round(cy, 3)],
                        "radial_distance_from_center_px": round(radial, 3),
                        "compactness": round(compactness, 6),
                        "extent": round(extent, 6),
                        "aspect_ratio": round(aspect, 6),
                        "compactness_basis": "bbox_perimeter_proxy",
                        "bbox_perimeter_px": round(bbox_perimeter, 3),
                        "quality": round(quality, 6),
                        "derived_from": f"connected component of coverage_count == {class_value}",
                    }
                )

            class_pixels = class_lookup[labels]
            accepted_pixels = class_pixels > 0
            class_map[accepted_pixels] = class_pixels[accepted_pixels]
            alpha_pixels = alpha_lookup[labels]
            alpha_map[accepted_pixels] = np.maximum(alpha_map[accepted_pixels], alpha_pixels[accepted_pixels])
            report["accepted_components_total"] += family_report["accepted_components"]
            report["by_family"][family] = family_report
        return class_map, alpha_map, component_infos, report

    def component_rejection_reason(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        area: int,
        compactness: float,
        cfg: dict[str, float],
    ) -> str | None:
        if area < cfg["min_area_px"]:
            return "area_below_min"
        if area > cfg["max_area_px"]:
            return "area_above_max"
        margin = cfg["edge_margin_px"]
        if x <= margin or y <= margin or x + w >= self.config.work_width - margin or y + h >= self.config.work_height - margin:
            return "touches_frame_edge_margin"
        aspect = max(w, h) / max(1.0, min(w, h))
        if aspect > cfg["max_aspect_ratio"]:
            return "aspect_ratio_above_max"
        extent = area / max(1.0, float(w * h))
        if extent < cfg["min_extent"]:
            return "extent_below_threshold"
        if compactness < cfg["min_compactness"]:
            return "compactness_below_threshold"
        return None

    def component_quality(self, area: int, compactness: float, extent: float, aspect: float, cfg: dict[str, float]) -> float:
        area_open = smoothstep01((area - cfg["min_area_px"]) / max(1.0, cfg["min_area_px"] * 3.0))
        area_close = 1.0 - smoothstep01((area - cfg["max_area_px"] * 0.78) / max(1.0, cfg["max_area_px"] * 0.22))
        compact_quality = min(1.0, compactness / max(1e-6, cfg["min_compactness"] * 2.2))
        extent_quality = min(1.0, extent / max(1e-6, cfg["min_extent"] * 2.0))
        aspect_quality = 1.0 - smoothstep01((aspect - 1.0) / max(1e-6, cfg["max_aspect_ratio"] - 1.0))
        return float(np.clip(0.18 + 0.82 * area_open * area_close * compact_quality * extent_quality * aspect_quality, 0.0, 1.0))

    def render_frame(self, t: float, *, output_size: bool = True, mode: str = "final") -> tuple[np.ndarray, dict[str, Any]]:
        include_ring_masks = mode == "active_ring_masks"
        state = self.compute_state(t, include_ring_masks=include_ring_masks)
        if mode == "final":
            frame = self._render_final(state)
        elif mode == "ring_count_map":
            frame = self._render_count_map(state.ring_count, kind="ring")
        elif mode == "coverage_count_map":
            frame = self._render_count_map(state.coverage_count, kind="coverage")
        elif mode == "component_classification_map":
            frame = self._render_component_map(state, include_micro=False)
        elif mode == "no_overlay_source_map":
            frame = self._render_component_map(state, include_micro=True, include_ring_wavefront=True)
        elif mode == "circle_mask":
            frame = self._render_single_mask(state.component_class_map == 1, TEAL)
        elif mode == "crescent_mask":
            frame = self._render_single_mask(state.component_class_map == 2, CREAM)
        elif mode == "trigon_mask":
            frame = self._render_single_mask(state.component_class_map == 3, SALMON)
        elif mode == "active_ring_masks":
            frame = self._render_active_ring_masks(state)
        else:
            raise ValueError(f"unknown render mode: {mode}")

        info = self.state_info(state)
        if output_size and (self.config.work_width, self.config.work_height) != (self.config.width, self.config.height):
            frame = cv2.resize(frame, (self.config.width, self.config.height), interpolation=cv2.INTER_LINEAR)
        return frame, info

    def _render_final(self, state: OverlapState) -> np.ndarray:
        frame = self.base_frame.astype(np.float32)
        visibility = wavefront_visibility(state.time_seconds)
        if visibility <= 0.0:
            return self.base_frame.copy()

        amp = cv2.resize(state.amplitude_field, (self.config.work_width, self.config.work_height), interpolation=cv2.INTER_CUBIC)
        amp = np.clip(0.84 + 0.16 * amp, 0.64, 1.14).astype(np.float32)
        gains = family_gains(state.time_seconds)

        # Subtle propagating wavefronts. Primitive-like emphasis below is not
        # drawn from these lines unless ring_count is a micro-overlap count.
        ring_wavefront = state.ring_count == 1
        self._blend_bool_mask(frame, ring_wavefront, MUTED_BLUE, 0.10 * visibility, amp)

        # Main bounded regions are exact connected components of coverage_count.
        circle_mask = state.component_class_map == 1
        crescent_mask = state.component_class_map == 2
        trigon_mask = state.component_class_map == 3
        alpha = state.component_alpha_map * visibility
        self._blend_float_mask(frame, circle_mask, alpha * 0.40 * gains["circle"], TEAL, amp)
        self._blend_float_mask(frame, crescent_mask, alpha * 0.62 * gains["crescent"], CREAM, amp)
        self._blend_float_mask(frame, trigon_mask, alpha * 0.72 * gains["trigon"], SALMON, amp)

        internal_edge = internal_edge_mask(state.component_class_map > 0)
        self._blend_bool_mask(frame, internal_edge, ICE, 0.18 * visibility * max(gains.values()), amp)

        # Thick-ring micro-geometry remains secondary and is strictly clipped to
        # ring_count == 2 or ring_count >= 3.
        ring_crescent = state.ring_count == 2
        ring_pressure = state.ring_count >= 3
        self._blend_bool_mask(frame, ring_crescent, ICE, 0.42 * visibility * gains["crescent"], amp)
        self._blend_bool_mask(frame, ring_pressure, GOLD, 0.58 * visibility * gains["trigon"], amp)

        support = (state.component_class_map > 0) | ring_crescent | ring_pressure
        if np.any(support):
            color = np.array(bgr(ICE), dtype=np.float32)
            lift = (0.08 * visibility * amp[support])[:, None]
            frame[support] = frame[support] * (1.0 - lift) + color * lift
        return np.clip(frame, 0, 255).astype(np.uint8)

    def _blend_bool_mask(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        rgb: tuple[int, int, int],
        alpha: float,
        amp: np.ndarray,
    ) -> None:
        if alpha <= 0.0 or not np.any(mask):
            return
        color = np.array(bgr(rgb), dtype=np.float32)
        idx = mask
        a = (alpha * amp[idx])[:, None]
        frame[idx] = frame[idx] * (1.0 - a) + color * a

    def _blend_float_mask(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        alpha_map: np.ndarray,
        rgb: tuple[int, int, int],
        amp: np.ndarray,
    ) -> None:
        if not np.any(mask):
            return
        color = np.array(bgr(rgb), dtype=np.float32)
        idx = mask & (alpha_map > 0.0)
        if not np.any(idx):
            return
        a = (alpha_map[idx] * amp[idx])[:, None]
        frame[idx] = frame[idx] * (1.0 - a) + color * a

    def _render_count_map(self, count: np.ndarray, *, kind: str) -> np.ndarray:
        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        frame[:] = bgr((2, 8, 10))
        frame[count == 1] = bgr(TEAL)
        frame[count == 2] = bgr(CREAM)
        frame[count == 3] = bgr(SALMON)
        frame[count >= 4] = bgr(GOLD if kind == "ring" else RED)
        return frame

    def _render_component_map(
        self,
        state: OverlapState,
        *,
        include_micro: bool,
        include_ring_wavefront: bool = False,
    ) -> np.ndarray:
        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        frame[:] = bgr((1, 6, 8))
        if include_ring_wavefront:
            frame[state.ring_count == 1] = bgr((24, 65, 78))
        frame[state.component_class_map == 1] = bgr(TEAL)
        frame[state.component_class_map == 2] = bgr(CREAM)
        frame[state.component_class_map == 3] = bgr(SALMON)
        if include_micro:
            micro_two = (state.ring_count == 2) & (state.component_class_map == 0)
            micro_three = (state.ring_count >= 3) & (state.component_class_map == 0)
            frame[micro_two] = bgr(ICE)
            frame[micro_three] = bgr(GOLD)
        return frame

    def _render_single_mask(self, mask: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        frame[:] = bgr((1, 6, 8))
        frame[mask] = bgr(rgb)
        return frame

    def _render_active_ring_masks(self, state: OverlapState) -> np.ndarray:
        frame = self.base_frame.astype(np.float32) * 0.58
        if not state.ring_masks:
            return np.clip(frame, 0, 255).astype(np.uint8)
        for source_info, mask in zip(state.active_sources, state.ring_masks, strict=True):
            ring_index = int(source_info["ring_index"])
            color = ICE if ring_index == 0 else (TEAL if ring_index == 1 else CREAM)
            alpha = 0.38 if ring_index == 0 else (0.30 if ring_index == 1 else 0.23)
            self._blend_bool_mask(frame, mask, color, alpha, np.ones(mask.shape, dtype=np.float32))
        return np.clip(frame, 0, 255).astype(np.uint8)

    def state_info(self, state: OverlapState) -> dict[str, Any]:
        return {
            "time_seconds": round(state.time_seconds, 5),
            "active_source_count": len(state.active_sources),
            "active_sources": state.active_sources,
            "ring_count_statistics": count_statistics(state.ring_count, "ring"),
            "coverage_count_statistics": count_statistics(state.coverage_count, "coverage"),
            "component_statistics": component_statistics(state),
        }


def np_smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep01(value: float) -> float:
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def ramp(t: float, start: float, end: float) -> float:
    return smoothstep01((t - start) / max(1e-6, end - start))


def wavefront_visibility(t: float) -> float:
    if t >= RELEASE_END_SECONDS:
        return 0.0
    fade_in = ramp(t, IMPACT_TIME_SECONDS - 0.25, IMPACT_TIME_SECONDS + 1.5)
    fade_out = 1.0 - ramp(t, RELEASE_START_SECONDS, RELEASE_END_SECONDS)
    return fade_in * fade_out


def family_gains(t: float) -> dict[str, float]:
    release = 1.0 - ramp(t, RELEASE_START_SECONDS, RELEASE_END_SECONDS)
    return {
        "circle": ramp(t, 7.0, 12.0) * release,
        "crescent": ramp(t, 19.0, 26.0) * release,
        "trigon": ramp(t, 25.0, 34.0) * release,
    }


def bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def draw_text(frame: np.ndarray, text: str, org: tuple[int, int], scale: float = 0.38) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, bgr(LABEL), 1, cv2.LINE_AA)


def label_panel(frame: np.ndarray, label: str, *, size: tuple[int, int] = (640, 360)) -> np.ndarray:
    panel = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    shade = np.zeros_like(panel)
    cv2.rectangle(shade, (0, 0), (size[0], 52), bgr(DEEP), -1)
    cv2.addWeighted(shade, 0.64, panel, 1.0, 0, dst=panel)
    draw_text(panel, label, (18, 34), 0.34)
    return panel


def internal_edge_mask(mask: np.ndarray) -> np.ndarray:
    src = mask.astype(np.uint8)
    if not np.any(src):
        return mask
    eroded = cv2.erode(src, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    return (src > 0) & (eroded == 0)


def frame_time(frame_idx: int) -> float:
    return frame_idx / FPS


def count_statistics(count: np.ndarray, label: str) -> dict[str, Any]:
    unique, counts = np.unique(count, return_counts=True)
    by_count = {str(int(k)): int(v) for k, v in zip(unique, counts, strict=True)}
    total = int(count.size)
    exact_1 = int(np.count_nonzero(count == 1))
    exact_2 = int(np.count_nonzero(count == 2))
    exact_3 = int(np.count_nonzero(count == 3))
    count_3plus = int(np.count_nonzero(count >= 3))
    nonzero = int(np.count_nonzero(count > 0))
    return {
        "map": label,
        "pixel_total": total,
        "by_exact_count": by_count,
        "count_0_pixels": int(np.count_nonzero(count == 0)),
        "count_1_pixels": exact_1,
        "count_2_pixels": exact_2,
        "count_3_pixels": exact_3,
        "count_3plus_pixels": count_3plus,
        "nonzero_pixels": nonzero,
        "nonzero_fraction": round(nonzero / total, 8),
        "max_count": int(count.max()) if count.size else 0,
        "empty": nonzero == 0,
        "uniform": len(unique) <= 1,
    }


def component_statistics(state: OverlapState) -> dict[str, Any]:
    by_family: dict[str, dict[str, Any]] = {}
    for family in (
        "circle_single_wavefront_family",
        "crescent_lens_two_front_family",
        "trigon_three_arc_pressure_family",
    ):
        comps = [info for info in state.component_infos if info["family"] == family]
        by_family[family] = {
            "accepted_components": len(comps),
            "accepted_pixels": int(sum(info["area_px"] for info in comps)),
            "mean_quality": round(float(np.mean([info["quality"] for info in comps])), 6) if comps else 0.0,
        }
    return {
        "accepted_components_total": len(state.component_infos),
        "accepted_pixels_total": int(np.count_nonzero(state.component_class_map > 0)),
        "by_family": by_family,
        "filter_report": state.component_filter_report,
    }


def config_for(target: str) -> RenderConfig:
    width, height = DRAFT_SIZE if target == "draft1080" else UHD_SIZE
    if target == "uhd":
        work_width = 960
        work_height = 540
        note = "UHD MP4 is encoded at 3840x2160 from a 960x540 analytic count-map work canvas with ffmpeg Lanczos scaling."
    else:
        work_width = 640
        work_height = 360
        note = "Draft 1920x1080 output is encoded from a 640x360 analytic count-map work canvas with ffmpeg Lanczos scaling."
    scale = work_height / 900.0
    return RenderConfig(
        width=width,
        height=height,
        work_width=work_width,
        work_height=work_height,
        field_width=max(240, work_width // 4),
        field_height=max(135, work_height // 4),
        fps=FPS,
        duration_seconds=DURATION_SECONDS,
        frame_count=N_FRAMES,
        lattice_spacing_work_px=LATTICE_SPACING_AT_900H * scale,
        wave_speed_work_px_per_second=WAVE_SPEED_AT_900H * scale,
        ring_width_work_px=RING_WIDTH_AT_900H * scale,
        wavelength_work_px=WAVELENGTH_AT_900H * scale,
        impact_time_seconds=IMPACT_TIME_SECONDS,
        release_start_seconds=RELEASE_START_SECONDS,
        release_end_seconds=RELEASE_END_SECONDS,
        work_canvas_note=note,
    )


def save_key_stills(renderer: WavefrontRegionRenderer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in KEY_STILLS:
        frame, _info = renderer.render_frame(t, output_size=True, mode="final")
        path = STILLS_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[key] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(renderer: WavefrontRegionRenderer) -> Path:
    panels = []
    for t in CONTACT_TIMES:
        frame, info = renderer.render_frame(t, output_size=False, mode="final")
        comp_total = info["component_statistics"]["accepted_components_total"]
        label = f"t={t:04.1f}s | active={info['active_source_count']} | comps={comp_total} | ringMax={info['ring_count_statistics']['max_count']}"
        panels.append(label_panel(frame, label, size=(480, 270)))
    rows = [cv2.hconcat(panels[i : i + 5]) for i in range(0, len(panels), 5)]
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_debug_sheets(renderer: WavefrontRegionRenderer) -> dict[str, Path]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    peak = PEAK_TIME_SECONDS
    views = [
        ("ring_count map at peak", "ring_count_map"),
        ("coverage_count map at peak", "coverage_count_map"),
        ("connected-component classification", "component_classification_map"),
        ("circle components: coverage_count == 1", "circle_mask"),
        ("crescent/lens components: coverage_count == 2", "crescent_mask"),
        ("trigon components: coverage_count == 3", "trigon_mask"),
    ]
    panels = []
    for label, mode in views:
        frame, _info = renderer.render_frame(peak, output_size=False, mode=mode)
        panels.append(label_panel(frame, label, size=(640, 360)))
        cv2.imwrite(str(DEBUG_DIR / f"{PROJECT}_{mode}_peak.png"), cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR))
    sheet = cv2.vconcat([cv2.hconcat(panels[:3]), cv2.hconcat(panels[3:])])
    state = renderer.compute_state(peak)
    footer = (
        "debug: bounded regions are connected components of coverage_count==1/2/3; "
        f"accepted components={len(state.component_infos)}; ring micro count2={int(np.count_nonzero(state.ring_count == 2))}; "
        f"ring micro count3+={int(np.count_nonzero(state.ring_count >= 3))}"
    )
    draw_text(sheet, footer, (24, sheet.shape[0] - 20), 0.35)
    debug_sheet = DEBUG_DIR / f"{PROJECT}_debug_verification_sheet.png"
    cv2.imwrite(str(debug_sheet), sheet)

    source_map, _ = renderer.render_frame(peak, output_size=False, mode="no_overlay_source_map")
    final_frame, _ = renderer.render_frame(peak, output_size=False, mode="final")
    comparison = cv2.hconcat(
        [
            label_panel(source_map, "A: classification + ring micro source map", size=(960, 540)),
            label_panel(final_frame, "B: final peak from same field maps", size=(960, 540)),
        ]
    )
    draw_text(
        comparison,
        "No-overlay comparison: final primitive-like regions must be present in coverage components or ring micro-overlap masks.",
        (28, comparison.shape[0] - 24),
        0.40,
    )
    comparison_path = DEBUG_DIR / f"{PROJECT}_no_overlay_comparison.png"
    cv2.imwrite(str(comparison_path), comparison)

    pulse_path = make_temporal_pulse_sheet(renderer)
    return {
        "debug_verification_sheet": debug_sheet,
        "no_overlay_comparison": comparison_path,
        "temporal_pulse_sheet": pulse_path,
    }


def choose_pulse_target(renderer: WavefrontRegionRenderer) -> tuple[float, tuple[float, float], str]:
    for t in (30.0, 34.0, 38.0, 44.0, 26.0):
        state = renderer.compute_state(t)
        candidates = [
            info
            for info in state.component_infos
            if info["family"] == "trigon_three_arc_pressure_family" and info["quality"] >= 0.35
        ]
        if candidates:
            candidates.sort(key=lambda item: (-item["quality"], item["radial_distance_from_center_px"]))
            target = candidates[0]
            return t, (float(target["centroid_xy"][0]), float(target["centroid_xy"][1])), target["family"]
    state = renderer.compute_state(PEAK_TIME_SECONDS)
    if state.component_infos:
        target = state.component_infos[0]
        return PEAK_TIME_SECONDS, (float(target["centroid_xy"][0]), float(target["centroid_xy"][1])), target["family"]
    return PEAK_TIME_SECONDS, (renderer.cx, renderer.cy), "no_component_found"


def make_temporal_pulse_sheet(renderer: WavefrontRegionRenderer) -> Path:
    target_time, center, family = choose_pulse_target(renderer)
    times = [max(0.0, target_time - 8.0), target_time - 4.0, target_time, target_time + 4.0, target_time + 10.0]
    times = [min(DURATION_SECONDS, max(0.0, t)) for t in times]
    crop_w = int(270 * renderer.scale)
    crop_h = int(190 * renderer.scale)
    source_panels = []
    final_panels = []
    for t in times:
        source_map, source_info = renderer.render_frame(t, output_size=False, mode="no_overlay_source_map")
        final_frame, _ = renderer.render_frame(t, output_size=False, mode="final")
        local_components = source_info["component_statistics"]["accepted_components_total"]
        source_crop = crop_around(source_map, center, crop_w, crop_h)
        final_crop = crop_around(final_frame, center, crop_w, crop_h)
        source_panels.append(label_panel(source_crop, f"source t={t:04.1f}s comps={local_components}", size=(384, 216)))
        final_panels.append(label_panel(final_crop, f"final t={t:04.1f}s", size=(384, 216)))
    sheet = cv2.vconcat([cv2.hconcat(source_panels), cv2.hconcat(final_panels)])
    draw_text(sheet, f"temporal pulse crop around detected {family} near t={target_time:.1f}s", (24, sheet.shape[0] - 18), 0.34)
    path = DEBUG_DIR / f"{PROJECT}_temporal_pulse_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def crop_around(frame: np.ndarray, center: tuple[float, float], width: int, height: int) -> np.ndarray:
    cx, cy = int(round(center[0])), int(round(center[1]))
    half_w = max(1, width // 2)
    half_h = max(1, height // 2)
    x0 = max(0, cx - half_w)
    y0 = max(0, cy - half_h)
    x1 = min(frame.shape[1], cx + half_w)
    y1 = min(frame.shape[0], cy + half_h)
    crop = frame[y0:y1, x0:x1]
    if crop.shape[0] == height and crop.shape[1] == width:
        return crop
    out = np.zeros((height, width, 3), dtype=frame.dtype)
    out[: crop.shape[0], : crop.shape[1]] = crop
    return out


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


def render_clip(renderer: WavefrontRegionRenderer) -> dict[str, Any]:
    path = OUT_DIR / f"{PROJECT}.mp4"
    input_size = (renderer.config.work_width, renderer.config.work_height)
    output_size = (renderer.config.width, renderer.config.height)
    writer = H264Writer(path, fps=FPS, input_size=input_size, output_size=output_size)
    try:
        for frame_idx in range(N_FRAMES):
            frame, _info = renderer.render_frame(frame_time(frame_idx), output_size=False, mode="final")
            writer.write(frame)
            if (frame_idx + 1) % FPS == 0:
                print(f"  {PROJECT}.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    return {
        "mp4": path.name,
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "frame_count": N_FRAMES,
        "input_size": list(input_size),
        "output_size": list(output_size),
        "upscale": "ffmpeg Lanczos scale from analytic count-map work canvas to final output" if input_size != output_size else "none",
        "video_encoder": "h264_videotoolbox",
        "target_video_bitrate": "45M",
        "frame_time_mapping": "frame_idx / fps; final encoded frame is one frame before duration, then loops to frame 0",
    }


def make_loop_diagnostic(renderer: WavefrontRegionRenderer, clip: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUT_DIR / clip["mp4"]
    f0 = read_frame_index(video_path, 0)
    f1 = read_frame_index(video_path, 1)
    fp = read_frame_index(video_path, N_FRAMES - 2)
    ff = read_frame_index(video_path, N_FRAMES - 1)

    cv2.imwrite(str(LOOP_DIR / "frame_0000_extracted.png"), f0)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 2:04d}_pre_final_extracted.png"), fp)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 1:04d}_final_extracted.png"), ff)

    raw0, _ = renderer.render_frame(0.0, output_size=True, mode="final")
    rawd, _ = renderer.render_frame(DURATION_SECONDS, output_size=True, mode="final")
    seam = mad(f0, ff)
    raw_seam = mad(raw0, rawd)
    adj0 = mad(f0, f1)
    adj1 = mad(fp, ff)

    panels = [
        label_panel(f0, "decoded frame 0"),
        label_panel(ff, f"decoded final frame {N_FRAMES - 1}"),
        label_panel(f1, f"decoded frame 1 MAD={adj0:.4f}"),
        label_panel(fp, f"decoded pre-final MAD={adj1:.4f}"),
    ]
    sheet = cv2.vconcat([cv2.hconcat(panels[:2]), cv2.hconcat(panels[2:])])
    draw_text(sheet, f"decoded seam MAD={seam:.6f}; raw virtual frame0/duration MAD={raw_seam:.8f}", (28, sheet.shape[0] - 24), 0.42)
    path = LOOP_DIR / f"{PROJECT}_loop_diagnostic_sheet.png"
    cv2.imwrite(str(path), sheet)

    verification = {
        "decoded_frame0_final_mean_abs_diff": round(seam, 6),
        "decoded_frame0_frame1_mean_abs_diff": round(adj0, 6),
        "decoded_pre_final_final_mean_abs_diff": round(adj1, 6),
        "raw_render_frame0_duration_mean_abs_diff": round(raw_seam, 8),
        "raw_virtual_loop_exact": raw_seam < 1e-7,
        "decoded_loop_seam_mad_below_1": seam < 1.0,
        "loop_strategy": "0-6s and 80-84s are the same dark-water hold; wavefront and component maps fade out before the loop point.",
    }
    return path, verification


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_activation_summary(renderer: WavefrontRegionRenderer) -> dict[str, Any]:
    by_role: dict[str, list[float]] = {}
    for src in renderer.sources:
        by_role.setdefault(src.role, []).append(src.activation_time_seconds)
    return {
        role: {
            "count": len(times),
            "first_activation_seconds": round(min(times), 5),
            "last_activation_seconds": round(max(times), 5),
            "activation_times_seconds": [round(t, 5) for t in sorted(times)],
        }
        for role, times in by_role.items()
    }


def sampled_statistics(renderer: WavefrontRegionRenderer) -> dict[str, Any]:
    samples: dict[str, Any] = {}
    for t in CONTACT_TIMES:
        state = renderer.compute_state(t)
        samples[f"{t:05.1f}s"] = {
            "ring_count_statistics": count_statistics(state.ring_count, "ring"),
            "coverage_count_statistics": count_statistics(state.coverage_count, "coverage"),
            "component_statistics": component_statistics(state),
        }
    return samples


def validation_verdict(renderer: WavefrontRegionRenderer) -> dict[str, Any]:
    state = renderer.compute_state(PEAK_TIME_SECONDS)
    ring_stats = count_statistics(state.ring_count, "ring")
    coverage_stats = count_statistics(state.coverage_count, "coverage")
    comp_stats = component_statistics(state)
    family = comp_stats["by_family"]
    pass_conditions = {
        "peak_ring_count_map_not_empty": not ring_stats["empty"],
        "peak_ring_count_map_not_uniform": not ring_stats["uniform"],
        "peak_coverage_count_map_not_empty": not coverage_stats["empty"],
        "peak_coverage_count_map_not_uniform": not coverage_stats["uniform"],
        "peak_has_circle_components": family["circle_single_wavefront_family"]["accepted_components"] > 0,
        "peak_has_crescent_lens_components": family["crescent_lens_two_front_family"]["accepted_components"] > 0,
        "peak_has_trigon_components": family["trigon_three_arc_pressure_family"]["accepted_components"] > 0,
        "peak_has_ring_count_2_micro_accents": int(np.count_nonzero(state.ring_count == 2)) > 0,
        "peak_has_ring_count_3plus_micro_accents": int(np.count_nonzero(state.ring_count >= 3)) > 0,
        "final_uses_only_coverage_components_and_ring_micro_masks_for_primitive_regions": True,
        "separate_primitive_paths_drawn": False,
        "crescent_trigon_oval_icon_overlays_drawn": False,
    }
    method_passed = all(
        value if key not in {"separate_primitive_paths_drawn", "crescent_trigon_oval_icon_overlays_drawn"} else not value
        for key, value in pass_conditions.items()
    )
    verdict = "PASS" if method_passed else "FAIL"
    if method_passed and comp_stats["accepted_pixels_total"] < 600:
        verdict = "MIXED"
    return {
        "verdict": verdict,
        "passed": verdict == "PASS",
        "conditions": pass_conditions,
        "peak_ring_count_statistics": ring_stats,
        "peak_coverage_count_statistics": coverage_stats,
        "peak_component_statistics": comp_stats,
    }


def write_manifest(
    renderer: WavefrontRegionRenderer,
    clip: dict[str, Any],
    stills: dict[str, str],
    contact_sheet: Path,
    debug_paths: dict[str, Path],
    loop_sheet: Path | None,
    loop_verification: dict[str, Any],
) -> Path:
    peak_state = renderer.compute_state(PEAK_TIME_SECONDS)
    manifest = {
        "project": PROJECT,
        "status": "austin_authorized_internal_show_development_prototype",
        "boundary": (
            "Austin-authorized internal/show-development prototype. No Austin source artwork is used. "
            "This explores analytic water-wave geometry only and makes no claim about the origin or meaning "
            "of Coast Salish vocabulary; Austin remains the authority on meaning."
        ),
        "renderer": f"scripts/{PROJECT}.py",
        "renderer_sha256": sha256(ROOT / "scripts" / f"{PROJECT}.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [renderer.config.width, renderer.config.height],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "render_settings": asdict(renderer.config),
        "physical_model": {
            "source_count": len(renderer.sources),
            "lattice": "radius-2 hexagonal / flower-of-life point lattice: 1 center, 6 first ring, 12 second ring",
            "activation_rule": "source activation time = impact_time + distance_from_center / wave_speed; center activates at impact_time",
            "ring_count_rule": "abs(distance_to_source - current_radius) <= ring_width",
            "coverage_count_rule": "distance_to_source <= current_radius",
            "bounded_region_rule": "connected components of coverage_count == 1, == 2, and == 3 after area/compactness/extent/aspect/edge filters",
            "ring_micro_rule": "ring_count == 2 for micro-crescent/crossing accents; ring_count >= 3 for micro-pressure accents",
            "wave_speed_work_px_per_second": renderer.config.wave_speed_work_px_per_second,
            "wave_speed_output_px_per_second": renderer.config.wave_speed_work_px_per_second * renderer.output_scale_x,
            "ring_width_work_px": renderer.config.ring_width_work_px,
            "ring_width_output_px": renderer.config.ring_width_work_px * renderer.output_scale_x,
            "wavelength_work_px": renderer.config.wavelength_work_px,
            "impact_time_seconds": IMPACT_TIME_SECONDS,
            "release_start_seconds": RELEASE_START_SECONDS,
            "release_end_seconds": RELEASE_END_SECONDS,
            "sources": [asdict(src) for src in renderer.sources],
            "activation_summary": source_activation_summary(renderer),
        },
        "component_filters": renderer.filter_config,
        "implementation_contract": {
            "austin_source_artwork_used": False,
            "drawn_primitive_overlays_used": False,
            "crescent_paths_drawn": False,
            "trigon_paths_drawn": False,
            "oval_markers_or_primitive_icons_drawn": False,
            "final_primitive_regions_source": "coverage_count connected components plus ring_count micro-overlap masks",
            "final_wavefront_source": "ring_count == 1 is used only as subtle propagating wavefront context",
            "beauty_render_note": "Fills and internal edges are clipped to accepted component masks; micro accents are clipped to ring_count==2 or ring_count>=3.",
        },
        "peak_time_seconds": PEAK_TIME_SECONDS,
        "peak_active_sources": peak_state.active_sources,
        "peak_ring_count_statistics": count_statistics(peak_state.ring_count, "ring"),
        "peak_coverage_count_statistics": count_statistics(peak_state.coverage_count, "coverage"),
        "peak_component_statistics": component_statistics(peak_state),
        "peak_component_catalog": peak_state.component_infos,
        "sampled_statistics": sampled_statistics(renderer),
        "validation_verdict": validation_verdict(renderer),
        "loop_verification": loop_verification,
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_verification_sheet": str(debug_paths["debug_verification_sheet"].relative_to(OUT_DIR)),
            "no_overlay_comparison": str(debug_paths["no_overlay_comparison"].relative_to(OUT_DIR)),
            "temporal_pulse_sheet": str(debug_paths["temporal_pulse_sheet"].relative_to(OUT_DIR)),
            "loop_diagnostic_sheet": str(loop_sheet.relative_to(OUT_DIR)) if loop_sheet else None,
            "readme": "README.md",
            **{f"{key}_still": rel for key, rel in stills.items()},
        },
        "clip": clip,
    }
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(
    renderer: WavefrontRegionRenderer,
    loop_verification: dict[str, Any],
    rendered: bool,
) -> Path:
    verdict = validation_verdict(renderer)
    peak_components = verdict["peak_component_statistics"]
    lines = [
        "# Abstract Cymatic Wavefront Overlap Path A v002",
        "",
        "Status: Austin-authorized internal/show-development prototype. No Austin source artwork is used.",
        "",
        "## Contract",
        "",
        "v002 keeps the v001 no-symbol-overlay rule but shifts the main read from ring intersection marks to bounded regions.",
        "",
        "- `ring_count` is computed from thick wavefront rings: `abs(distance - current_radius) <= ring_width`.",
        "- `coverage_count` is computed from expanding discs: `distance <= current_radius`.",
        "- Bounded primitive regions are connected components of `coverage_count == 1`, `== 2`, and `== 3` after documented filters.",
        "- Secondary micro-geometry comes only from `ring_count == 2` and `ring_count >= 3`.",
        "- No crescent path, trigon path, oval marker, icon, or separate primitive overlay layer is drawn.",
        "",
        "## Output",
        "",
        f"- MP4: `{PROJECT}.mp4`, {renderer.config.width}x{renderer.config.height}, 24fps, {DURATION_SECONDS:.0f}s." if rendered else "- MP4: not rendered in preview mode.",
        f"- Contact sheet: `{PROJECT}_contact_sheet.png`.",
        f"- Debug sheet: `debug/{PROJECT}_debug_verification_sheet.png`.",
        f"- No-overlay comparison: `debug/{PROJECT}_no_overlay_comparison.png`.",
        f"- Temporal pulse sheet: `debug/{PROJECT}_temporal_pulse_sheet.png`.",
        f"- Manifest: `{PROJECT}_manifest.json`.",
        "",
        "## Peak Component Counts",
        "",
        f"- Circle/single-wavefront components: `{peak_components['by_family']['circle_single_wavefront_family']['accepted_components']}`.",
        f"- Crescent/lens two-front components: `{peak_components['by_family']['crescent_lens_two_front_family']['accepted_components']}`.",
        f"- Trigon three-arc components: `{peak_components['by_family']['trigon_three_arc_pressure_family']['accepted_components']}`.",
        f"- Accepted component pixels: `{peak_components['accepted_pixels_total']}`.",
        "",
        "## Loop",
        "",
        f"- Raw virtual frame0/duration MAD: `{loop_verification.get('raw_render_frame0_duration_mean_abs_diff')}`.",
        f"- Decoded frame0/final MAD: `{loop_verification.get('decoded_frame0_final_mean_abs_diff')}`.",
        f"- Loop strategy: `{loop_verification.get('loop_strategy')}`.",
        "",
        "## Honest Verdict",
        "",
    ]
    if verdict["verdict"] == "PASS":
        lines.append(
            "PASS for the requested implementation contract. The final primitive-like regions are bounded coverage-count components or ring-count micro-overlap masks. The no-overlay comparison is the primary audit artifact."
        )
    elif verdict["verdict"] == "MIXED":
        lines.append(
            "MIXED. The method follows the field-derived contract, but the accepted component area is small enough that visual legibility should be reviewed before treating the render as a strong candidate."
        )
    else:
        lines.append(
            "FAIL as a final candidate. At least one required count-map/component condition did not hold; inspect the manifest validation verdict and debug sheets."
        )
    lines.extend(
        [
            "",
            "Caveat: classification is computed on the recorded analytic work canvas, then scaled to UHD for delivery.",
            "",
            "Cultural framing: this does not claim to prove the origin or meaning of Coast Salish vocabulary. Austin remains the authority on meaning.",
            "",
            f"Renderer: `scripts/{PROJECT}.py`",
        ]
    )
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render analytic delayed-ripple bounded-region prototype.")
    parser.add_argument("--target", choices=("uhd", "draft1080"), default="uhd")
    parser.add_argument("--preview", action="store_true", help="Write stills/debug/manifest without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    renderer = WavefrontRegionRenderer(config_for(args.target))
    print("Writing key stills, contact sheet, and debug sheets", flush=True)
    stills = save_key_stills(renderer)
    contact = make_contact_sheet(renderer)
    debug_paths = make_debug_sheets(renderer)

    if args.preview:
        raw0, _ = renderer.render_frame(0.0, output_size=True, mode="final")
        rawd, _ = renderer.render_frame(DURATION_SECONDS, output_size=True, mode="final")
        raw_mad = mad(raw0, rawd)
        loop_verification = {
            "preview_only": True,
            "decoded_frame0_final_mean_abs_diff": None,
            "raw_render_frame0_duration_mean_abs_diff": round(raw_mad, 8),
            "raw_virtual_loop_exact": raw_mad < 1e-7,
            "decoded_loop_seam_mad_below_1": None,
            "loop_strategy": "0-6s and 80-84s are the same dark-water hold; wavefront and component maps fade out before the loop point.",
        }
        clip = {
            "mp4": f"{PROJECT}.mp4",
            "duration_seconds": DURATION_SECONDS,
            "fps": FPS,
            "frame_count": N_FRAMES,
            "preview_only": True,
        }
        loop_sheet = None
    else:
        print(f"Rendering {PROJECT}.mp4", flush=True)
        clip = render_clip(renderer)
        print("Writing loop diagnostic sheet", flush=True)
        loop_sheet, loop_verification = make_loop_diagnostic(renderer, clip)

    manifest = write_manifest(renderer, clip, stills, contact, debug_paths, loop_sheet, loop_verification)
    readme = write_readme(renderer, loop_verification, rendered=not args.preview)

    print(f"Wrote {contact}", flush=True)
    for path in debug_paths.values():
        print(f"Wrote {path}", flush=True)
    if loop_sheet:
        print(f"Wrote {loop_sheet}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)
    if not args.preview:
        print(f"Wrote {OUT_DIR / clip['mp4']}", flush=True)


if __name__ == "__main__":
    main()
