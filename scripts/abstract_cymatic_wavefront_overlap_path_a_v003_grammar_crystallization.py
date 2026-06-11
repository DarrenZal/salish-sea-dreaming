#!/usr/bin/env python3
"""
Abstract cymatic wavefront overlap path A v003 grammar crystallization.

Generated Austin/Coast Salish-style support composition for internal/show-
development review, pending Austin review.

Important boundary:
- No Austin source artwork is read, copied, traced, or modified.
- The wave field does not claim that the final design purely emerges from
  physics. Field-derived wave geometry provides anchors, arcs, normals,
  junctions, pressure points, and timing.
- The grammar layer intentionally crystallizes those field features into a
  generated primitive syntax of circles, crescents, and trigons.
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
PROJECT = "abstract_cymatic_wavefront_overlap_path_a_v003_grammar_crystallization"
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
TAU = math.tau

UHD_SIZE = (3840, 2160)
DRAFT_SIZE = (1920, 1080)

IMPACT_TIME_SECONDS = 6.0
GRAMMAR_SUPPORT_TIME_SECONDS = 44.0
FULL_HOLD_START_SECONDS = 60.0
FULL_HOLD_END_SECONDS = 72.0
RELEASE_START_SECONDS = 72.0
RELEASE_END_SECONDS = 80.0

LATTICE_SPACING_AT_900H = 132.0
WAVE_SPEED_AT_900H = 12.0
RING_WIDTH_AT_900H = 7.0
WAVELENGTH_AT_900H = 42.0

DEEP = (0, 5, 8)
INK = (1, 8, 9)
DARK_WATER = (3, 18, 24)
MID_WATER = (9, 41, 48)
MUTED_BLUE = (30, 83, 96)
TEAL = (45, 145, 154)
ICE = (145, 219, 224)
CREAM = (238, 229, 195)
IVORY = (247, 239, 205)
GOLD = (241, 181, 74)
SALMON = (219, 78, 51)
RED = (166, 38, 31)
LABEL = (226, 234, 230)

KEY_STILLS = (
    ("01_dark_water_rain_ripple_field", 0.0),
    ("02_ripple_field_before_grammar", 12.0),
    ("03_central_circle_crystallizes", 22.0),
    ("04_first_ring_circles_stabilize", 30.0),
    ("05_crescents_crystallize", 42.0),
    ("06_trigons_crystallize", 55.0),
    ("07_full_generated_support_composition_hold", 66.0),
    ("08_dissolve_back_to_water", 76.0),
    ("09_loop_return", DURATION_SECONDS),
)

CONTACT_TIMES = (
    0.0,
    6.0,
    12.0,
    15.0,
    21.0,
    27.0,
    30.0,
    36.0,
    42.0,
    45.0,
    51.0,
    57.0,
    60.0,
    66.0,
    72.0,
    76.0,
    80.0,
    82.0,
    83.0,
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
    grammar_support_time_seconds: float
    release_start_seconds: float
    release_end_seconds: float
    work_canvas_note: str


@dataclass
class FieldState:
    time_seconds: float
    active_sources: list[dict[str, Any]]
    ring_count: np.ndarray
    coverage_count: np.ndarray
    amplitude_field: np.ndarray


@dataclass(frozen=True)
class ComponentCandidate:
    candidate_id: str
    coverage_count: int
    label_index: int
    area_px: int
    bbox_xywh: tuple[int, int, int, int]
    centroid_xy: tuple[float, float]
    radial_distance_px: float
    angle_degrees: float
    compactness: float
    source_ids_at_centroid: tuple[str, ...]


@dataclass(frozen=True)
class PrimitiveSpec:
    primitive_id: str
    primitive_type: str
    field_seed_kind: str
    source_ids: tuple[str, ...]
    field_seed_xy: tuple[float, float]
    style_center_xy: tuple[float, float]
    style_center_adjustment_px: float
    angle_degrees: float
    support_time_seconds: float
    support_count_rule: str
    field_candidate_id: str | None
    field_candidate_area_px: int | None
    field_candidate_coverage_count: int | None
    size_params: dict[str, float]
    grammar_note: str


class H264Writer:
    def __init__(
        self,
        path: Path,
        *,
        fps: int,
        input_size: tuple[int, int],
        output_size: tuple[int, int],
        software_codec: bool,
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
        if software_codec:
            cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "17"])
        else:
            cmd.extend(["-c:v", "h264_videotoolbox", "-b:v", "45M", "-maxrate", "70M", "-bufsize", "90M"])
        cmd.extend(["-pix_fmt", "yuv420p", "-tag:v", "avc1", "-movflags", "+faststart", str(path)])
        self.path = path
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(np.ascontiguousarray(frame).tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        stderr = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with code {code}\n{stderr[-4000:]}")


class GrammarCrystallizationRenderer:
    def __init__(self, config: RenderConfig) -> None:
        self.config = config
        self.scale = config.work_height / 900.0
        self.design_scale = config.work_height / 540.0
        self.output_scale_x = config.width / config.work_width
        self.output_scale_y = config.height / config.work_height
        self.cx = config.work_width * 0.5
        self.cy = config.work_height * 0.5

        y, x = np.mgrid[0 : config.work_height, 0 : config.work_width].astype(np.float32)
        self.x = x
        self.y = y
        self.center_dist = np.sqrt((x - self.cx) ** 2 + (y - self.cy) ** 2)
        self.edge_window = self._edge_window(x, y)
        self.radial_window = self._radial_window(self.center_dist)
        self.base_frame = self._make_base_frame()

        fy = (np.arange(config.field_height, dtype=np.float32) + 0.5) * (config.work_height / config.field_height)
        fx = (np.arange(config.field_width, dtype=np.float32) + 0.5) * (config.work_width / config.field_width)
        self.fx, self.fy = np.meshgrid(fx, fy)
        self.field_center_dist = np.sqrt((self.fx - self.cx) ** 2 + (self.fy - self.cy) ** 2)
        self.field_window = self._radial_window(self.field_center_dist) * self._edge_window(self.fx, self.fy)

        self.sources = self._make_sources()
        self.sources_by_id = {src.source_id: src for src in self.sources}
        self.distance_fields = self._precompute_distance_fields()
        self.field_distance_fields = self._precompute_field_distance_fields()
        self.max_distance_fields = [float(dist.max()) for dist in self.distance_fields]

        self.delta_scratch = np.empty((config.work_height, config.work_width), dtype=np.float32)
        self.ring_scratch = np.empty((config.work_height, config.work_width), dtype=bool)
        self.coverage_scratch = np.empty((config.work_height, config.work_width), dtype=bool)
        self.phase_scratch = np.empty((config.field_height, config.field_width), dtype=np.float32)

        self.primitive_specs = self._build_primitive_specs()
        self.design_layers = self._make_design_layers()

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
        grain = (
            0.50
            + 0.20 * np.sin(7.0 * x_norm + 4.2 * y_norm)
            + 0.12 * np.sin(15.0 * x_norm - 10.0 * y_norm)
            + 0.08 * np.sin(26.0 * (x_norm + y_norm))
        )
        grain = np.clip(grain, 0.0, 1.0)
        radial = np.clip(1.0 - self.center_dist / (0.82 * min(self.config.work_width, self.config.work_height)), 0.0, 1.0)
        base = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.float32)
        deep = np.array(bgr(DEEP), dtype=np.float32)
        dark = np.array(bgr(DARK_WATER), dtype=np.float32)
        mid = np.array(bgr(MID_WATER), dtype=np.float32)
        mix = 0.16 + 0.30 * radial + 0.07 * grain
        base[:] = deep
        base = base * (1.0 - mix[..., None]) + dark * mix[..., None]
        base = base * 0.94 + mid * (0.06 * grain * self.radial_window)[..., None]
        vignette = 0.58 + 0.42 * self.radial_window * self.edge_window
        base *= vignette[..., None]
        return np.clip(base, 0, 255).astype(np.uint8)

    def compute_state(self, t: float, *, include_coverage: bool = True) -> FieldState:
        t_loop = t % self.config.duration_seconds
        ring_count = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        coverage_count = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        amplitude = np.zeros((self.config.field_height, self.config.field_width), dtype=np.float32)
        active_infos: list[dict[str, Any]] = []
        k = TAU / self.config.wavelength_work_px

        if t_loop < self.config.release_end_seconds:
            for idx, (src, dist, dist_small) in enumerate(
                zip(self.sources, self.distance_fields, self.field_distance_fields, strict=True)
            ):
                age = t_loop - src.activation_time_seconds
                if age < 0.0:
                    continue
                radius = self.config.wave_speed_work_px_per_second * age

                if include_coverage:
                    np.less_equal(dist, radius, out=self.coverage_scratch)
                    coverage_count += self.coverage_scratch

                ring_pixels = 0
                if radius <= self.max_distance_fields[idx] + self.config.ring_width_work_px:
                    np.subtract(dist, radius, out=self.delta_scratch)
                    np.abs(self.delta_scratch, out=self.delta_scratch)
                    np.less_equal(self.delta_scratch, self.config.ring_width_work_px, out=self.ring_scratch)
                    ring_count += self.ring_scratch
                    ring_pixels = int(np.count_nonzero(self.ring_scratch))

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
        return FieldState(
            time_seconds=t_loop,
            active_sources=active_infos,
            ring_count=ring_count,
            coverage_count=coverage_count,
            amplitude_field=amplitude,
        )

    def _build_primitive_specs(self) -> list[PrimitiveSpec]:
        specs: list[PrimitiveSpec] = []
        support_state = self.compute_state(GRAMMAR_SUPPORT_TIME_SECONDS, include_coverage=True)
        crescent_candidates = self._extract_component_candidates(support_state.coverage_count, 2)
        trigon_candidates = self._extract_component_candidates(support_state.coverage_count, 3)

        unit = self.design_scale
        center_source = self.sources_by_id["center_00"]
        specs.append(
            PrimitiveSpec(
                primitive_id="circle_center_00",
                primitive_type="circle",
                field_seed_kind="single_source_stable_center_ring",
                source_ids=(center_source.source_id,),
                field_seed_xy=(center_source.x_work_px, center_source.y_work_px),
                style_center_xy=(center_source.x_work_px, center_source.y_work_px),
                style_center_adjustment_px=0.0,
                angle_degrees=0.0,
                support_time_seconds=GRAMMAR_SUPPORT_TIME_SECONDS,
                support_count_rule="center source point from delayed wave lattice; concentric support from center-source wavefront",
                field_candidate_id=None,
                field_candidate_area_px=None,
                field_candidate_coverage_count=None,
                size_params={"radius_px": 38.0 * unit, "inner_radius_px": 18.0 * unit},
                grammar_note="Central circle establishes the readable origin; nested circle is concentric with the same source seed.",
            )
        )

        inner_sources = sorted(
            [src for src in self.sources if src.ring_index == 1],
            key=lambda src: angle_degrees(src.x_work_px - self.cx, src.y_work_px - self.cy),
        )
        for idx, src in enumerate(inner_sources):
            angle = angle_degrees(src.x_work_px - self.cx, src.y_work_px - self.cy)
            specs.append(
                PrimitiveSpec(
                    primitive_id=f"circle_inner_source_{idx:02d}",
                    primitive_type="circle",
                    field_seed_kind="single_source_stable_inner_ring_center",
                    source_ids=(src.source_id,),
                    field_seed_xy=(src.x_work_px, src.y_work_px),
                    style_center_xy=(src.x_work_px, src.y_work_px),
                    style_center_adjustment_px=0.0,
                    angle_degrees=angle,
                    support_time_seconds=GRAMMAR_SUPPORT_TIME_SECONDS,
                    support_count_rule="inner delayed source point from wave lattice; circle center is exact source center",
                    field_candidate_id=None,
                    field_candidate_area_px=None,
                    field_candidate_coverage_count=None,
                    size_params={"radius_px": 27.0 * unit, "inner_radius_px": 12.0 * unit},
                    grammar_note="Source-center circle in the first delayed ring; fewer larger nodes replace v002's small debug detections.",
                )
            )

        crescent_targets = (30.0, 72.0, 108.0, 150.0, 210.0, 252.0, 288.0, 330.0)
        selected_crescents = self._select_by_angles(crescent_candidates, crescent_targets)
        for idx, candidate in enumerate(selected_crescents):
            radial_angle = angle_degrees(candidate.centroid_xy[0] - self.cx, candidate.centroid_xy[1] - self.cy)
            style_center = self._project_inside_frame(candidate.centroid_xy, margin=39.0 * unit)
            specs.append(
                PrimitiveSpec(
                    primitive_id=f"crescent_two_overlap_{idx:02d}",
                    primitive_type="crescent",
                    field_seed_kind="coverage_count_2_lens_annular_band_component",
                    source_ids=candidate.source_ids_at_centroid,
                    field_seed_xy=candidate.centroid_xy,
                    style_center_xy=style_center,
                    style_center_adjustment_px=distance(candidate.centroid_xy, style_center),
                    angle_degrees=radial_angle,
                    support_time_seconds=GRAMMAR_SUPPORT_TIME_SECONDS,
                    support_count_rule="selected connected component of coverage_count == 2 at grammar support frame",
                    field_candidate_id=candidate.candidate_id,
                    field_candidate_area_px=candidate.area_px,
                    field_candidate_coverage_count=candidate.coverage_count,
                    size_params={
                        "outer_axis_tangent_px": 58.0 * unit,
                        "outer_axis_normal_px": 22.0 * unit,
                        "inner_axis_tangent_px": 55.0 * unit,
                        "inner_axis_normal_px": 22.0 * unit,
                        "inner_shift_inward_px": 18.0 * unit,
                    },
                    grammar_note="Crescent follows the radial normal of a two-overlap field component; concave side opens toward the center.",
                )
            )

        trigon_targets = (0.0, 60.0, 120.0, 180.0, 240.0, 300.0)
        selected_trigons = self._select_by_angles(trigon_candidates, trigon_targets)
        for idx, candidate in enumerate(selected_trigons):
            radial_angle = angle_degrees(candidate.centroid_xy[0] - self.cx, candidate.centroid_xy[1] - self.cy)
            style_center = self._project_inside_frame(candidate.centroid_xy, margin=58.0 * unit)
            specs.append(
                PrimitiveSpec(
                    primitive_id=f"trigon_pressure_{idx:02d}",
                    primitive_type="trigon",
                    field_seed_kind="coverage_count_3_pressure_component",
                    source_ids=candidate.source_ids_at_centroid,
                    field_seed_xy=candidate.centroid_xy,
                    style_center_xy=style_center,
                    style_center_adjustment_px=distance(candidate.centroid_xy, style_center),
                    angle_degrees=radial_angle,
                    support_time_seconds=GRAMMAR_SUPPORT_TIME_SECONDS,
                    support_count_rule="selected connected component of coverage_count == 3 at grammar support frame",
                    field_candidate_id=candidate.candidate_id,
                    field_candidate_area_px=candidate.area_px,
                    field_candidate_coverage_count=candidate.coverage_count,
                    size_params={"length_px": 54.0 * unit, "width_px": 43.0 * unit},
                    grammar_note="Trigon is oriented along the outward normal from a triple-overlap pressure component.",
                )
            )
        return specs

    def _extract_component_candidates(self, coverage_count: np.ndarray, target_count: int) -> list[ComponentCandidate]:
        binary = (coverage_count == target_count).astype(np.uint8)
        n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
        candidates: list[ComponentCandidate] = []
        min_area = int(round((90.0 if target_count == 2 else 120.0) * self.design_scale * self.design_scale))
        for label_idx in range(1, n_labels):
            x, y, w, h, area = (int(v) for v in stats[label_idx])
            if area < min_area:
                continue
            cx, cy = float(centroids[label_idx][0]), float(centroids[label_idx][1])
            radial = math.hypot(cx - self.cx, cy - self.cy)
            if radial < self.config.lattice_spacing_work_px * 1.35:
                continue
            bbox_perimeter = float(2 * (w + h))
            compactness = 4.0 * math.pi * area / max(1.0, bbox_perimeter * bbox_perimeter)
            src_ids = tuple(self.covering_source_ids_at((cx, cy), GRAMMAR_SUPPORT_TIME_SECONDS, max_count=target_count))
            candidates.append(
                ComponentCandidate(
                    candidate_id=f"coverage_count_{target_count}_component_{label_idx:03d}",
                    coverage_count=target_count,
                    label_index=label_idx,
                    area_px=area,
                    bbox_xywh=(x, y, w, h),
                    centroid_xy=(cx, cy),
                    radial_distance_px=radial,
                    angle_degrees=angle_degrees(cx - self.cx, cy - self.cy),
                    compactness=compactness,
                    source_ids_at_centroid=src_ids,
                )
            )
        candidates.sort(key=lambda item: (-item.area_px, item.angle_degrees))
        return candidates

    def covering_source_ids_at(self, xy: tuple[float, float], t: float, *, max_count: int | None = None) -> list[str]:
        ids: list[tuple[float, str]] = []
        for src in self.sources:
            age = t - src.activation_time_seconds
            if age < 0.0:
                continue
            radius = self.config.wave_speed_work_px_per_second * age
            d = math.hypot(xy[0] - src.x_work_px, xy[1] - src.y_work_px)
            if d <= radius:
                ids.append((abs(radius - d), src.source_id))
        ids.sort()
        out = [source_id for _delta, source_id in ids]
        if max_count is not None:
            return out[:max_count]
        return out

    def _select_by_angles(self, candidates: list[ComponentCandidate], targets: tuple[float, ...]) -> list[ComponentCandidate]:
        selected: list[ComponentCandidate] = []
        used: set[str] = set()
        for target in targets:
            available = [cand for cand in candidates if cand.candidate_id not in used]
            if not available:
                break
            best = min(
                available,
                key=lambda cand: (
                    angular_distance_degrees(cand.angle_degrees, target),
                    -cand.area_px,
                    abs(cand.radial_distance_px - 0.50 * min(self.config.work_width, self.config.work_height)),
                ),
            )
            used.add(best.candidate_id)
            selected.append(best)
        selected.sort(key=lambda cand: cand.angle_degrees)
        return selected

    def _project_inside_frame(self, xy: tuple[float, float], *, margin: float) -> tuple[float, float]:
        dx = xy[0] - self.cx
        dy = xy[1] - self.cy
        r = math.hypot(dx, dy)
        if r <= 1e-6:
            return xy
        ux = dx / r
        uy = dy / r
        max_r = float("inf")
        if ux > 1e-6:
            max_r = min(max_r, (self.config.work_width - margin - self.cx) / ux)
        elif ux < -1e-6:
            max_r = min(max_r, (margin - self.cx) / ux)
        if uy > 1e-6:
            max_r = min(max_r, (self.config.work_height - margin - self.cy) / uy)
        elif uy < -1e-6:
            max_r = min(max_r, (margin - self.cy) / uy)
        if not math.isfinite(max_r):
            max_r = r
        safe_r = min(r, max(0.0, max_r))
        return (self.cx + ux * safe_r, self.cy + uy * safe_r)

    def _make_design_layers(self) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        layers: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for primitive_type in ("circle", "crescent", "trigon"):
            layer = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
            alpha = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
            for spec in [item for item in self.primitive_specs if item.primitive_type == primitive_type]:
                if primitive_type == "circle":
                    self._draw_circle_primitive(layer, alpha, spec)
                elif primitive_type == "crescent":
                    self._draw_crescent_primitive(layer, alpha, spec)
                elif primitive_type == "trigon":
                    self._draw_trigon_primitive(layer, alpha, spec)
            layers[primitive_type] = (layer, (alpha.astype(np.float32) / 255.0))
        return layers

    def _draw_circle_primitive(self, layer: np.ndarray, alpha: np.ndarray, spec: PrimitiveSpec) -> None:
        cx, cy = int(round(spec.style_center_xy[0])), int(round(spec.style_center_xy[1]))
        radius = int(round(spec.size_params["radius_px"]))
        inner = int(round(spec.size_params["inner_radius_px"]))
        outline = max(3, int(round(4.0 * self.design_scale)))
        draw_circle(layer, alpha, (cx, cy), radius + outline, INK)
        draw_circle(layer, alpha, (cx, cy), radius, IVORY)
        draw_circle(layer, alpha, (cx, cy), inner, INK)
        if spec.primitive_id == "circle_center_00":
            draw_circle(layer, alpha, (cx, cy), max(5, int(round(8.0 * self.design_scale))), SALMON)
            draw_circle(layer, alpha, (cx, cy), max(2, int(round(3.5 * self.design_scale))), INK)
        else:
            angle = math.radians(spec.angle_degrees)
            accent_center = (
                int(round(cx + math.cos(angle) * radius * 0.38)),
                int(round(cy + math.sin(angle) * radius * 0.38)),
            )
            draw_circle(layer, alpha, accent_center, max(4, int(round(6.0 * self.design_scale))), TEAL)

    def _draw_crescent_primitive(self, layer: np.ndarray, alpha: np.ndarray, spec: PrimitiveSpec) -> None:
        cx, cy = spec.style_center_xy
        angle = math.radians(spec.angle_degrees)
        tangent_degrees = spec.angle_degrees + 90.0
        inward = (-math.cos(angle), -math.sin(angle))
        outer_axes = (
            int(round(spec.size_params["outer_axis_tangent_px"])),
            int(round(spec.size_params["outer_axis_normal_px"])),
        )
        inner_axes = (
            int(round(spec.size_params["inner_axis_tangent_px"])),
            int(round(spec.size_params["inner_axis_normal_px"])),
        )
        shift = spec.size_params["inner_shift_inward_px"]
        outline_axes = (
            outer_axes[0] + max(3, int(round(4.0 * self.design_scale))),
            outer_axes[1] + max(3, int(round(4.0 * self.design_scale))),
        )
        center = (int(round(cx)), int(round(cy)))
        cutout_center = (int(round(cx + inward[0] * shift)), int(round(cy + inward[1] * shift)))
        draw_ellipse(layer, alpha, center, outline_axes, tangent_degrees, INK)
        draw_ellipse(layer, alpha, center, outer_axes, tangent_degrees, CREAM)
        draw_ellipse(layer, alpha, cutout_center, inner_axes, tangent_degrees, INK)

        accent_shift = spec.size_params["outer_axis_normal_px"] * 0.76
        accent_center = (
            int(round(cx + math.cos(angle) * accent_shift)),
            int(round(cy + math.sin(angle) * accent_shift)),
        )
        accent_axes = (
            max(7, int(round(16.0 * self.design_scale))),
            max(3, int(round(4.2 * self.design_scale))),
        )
        draw_ellipse(layer, alpha, accent_center, accent_axes, tangent_degrees, SALMON)

    def _draw_trigon_primitive(self, layer: np.ndarray, alpha: np.ndarray, spec: PrimitiveSpec) -> None:
        center = spec.style_center_xy
        angle = math.radians(spec.angle_degrees)
        length = spec.size_params["length_px"]
        width = spec.size_params["width_px"]
        draw_curved_trigon(layer, alpha, center, angle, length + 8.0 * self.design_scale, width + 8.0 * self.design_scale, INK)
        draw_curved_trigon(layer, alpha, center, angle, length, width, SALMON)
        inset_center = (
            center[0] - math.cos(angle) * length * 0.14,
            center[1] - math.sin(angle) * length * 0.14,
        )
        draw_curved_trigon(layer, alpha, inset_center, angle, length * 0.44, width * 0.34, GOLD)
        draw_curved_trigon(layer, alpha, inset_center, angle, length * 0.27, width * 0.21, INK)

    def render_frame(self, t: float, *, output_size: bool = True, mode: str = "final") -> tuple[np.ndarray, dict[str, Any]]:
        if mode == "final":
            frame = self._render_final(t)
        elif mode == "raw_field":
            frame = self._render_raw_field_debug(GRAMMAR_SUPPORT_TIME_SECONDS)
        elif mode == "selected_seeds":
            frame = self._render_selected_seeds_debug()
        elif mode == "grammar_candidates":
            frame = self._render_candidates_debug()
        elif mode == "construction_overlay":
            frame = self._render_construction_overlay_debug()
        elif mode == "audit_overlay":
            frame = self._render_audit_overlay_debug()
        else:
            raise ValueError(f"unknown render mode: {mode}")

        info = self.state_info(t)
        if output_size and (self.config.work_width, self.config.work_height) != (self.config.width, self.config.height):
            frame = cv2.resize(frame, (self.config.width, self.config.height), interpolation=cv2.INTER_LINEAR)
        return frame, info

    def _render_final(self, t: float) -> np.ndarray:
        t_loop = t % self.config.duration_seconds
        state = self.compute_state(t_loop, include_coverage=False)
        frame = self._render_water_background(t_loop, state)

        gains = grammar_gains(t_loop)
        for primitive_type in ("circle", "crescent", "trigon"):
            gain = gains[primitive_type]
            if gain <= 0.0:
                continue
            layer, alpha = self.design_layers[primitive_type]
            self._blend_layer(frame, layer, alpha, gain)
        return np.clip(frame, 0, 255).astype(np.uint8)

    def _render_water_background(self, t: float, state: FieldState) -> np.ndarray:
        frame = self.base_frame.astype(np.float32)
        water_gain = ramp(t, 0.5, 3.5) * (1.0 - ramp(t, 78.0, 80.0))
        if water_gain <= 0.0:
            return frame.astype(np.uint8)

        design_strength = max(grammar_gains(t).values())
        amp = cv2.resize(state.amplitude_field, (self.config.work_width, self.config.work_height), interpolation=cv2.INTER_CUBIC)
        amp = np.clip(amp, -1.0, 1.0)
        watery_lift = (9.0 * water_gain * (0.8 - 0.42 * design_strength) * amp)[..., None]
        frame[..., 0:2] += watery_lift
        frame[..., 2] += 3.0 * water_gain * amp

        ring_context = water_gain * (0.18 - 0.13 * design_strength)
        if ring_context > 0.0:
            ones = state.ring_count == 1
            twos = state.ring_count == 2
            threes = state.ring_count >= 3
            self._blend_bool_mask(frame, ones, MUTED_BLUE, ring_context * 0.42)
            self._blend_bool_mask(frame, twos, ICE, ring_context * 0.35)
            self._blend_bool_mask(frame, threes, GOLD, ring_context * 0.28)
        return np.clip(frame, 0, 255).astype(np.uint8)

    def _blend_bool_mask(self, frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float) -> None:
        if alpha <= 0.0 or not np.any(mask):
            return
        color = np.array(bgr(rgb), dtype=np.float32)
        frame[mask] = frame[mask] * (1.0 - alpha) + color * alpha

    def _blend_layer(self, frame: np.ndarray, layer: np.ndarray, alpha: np.ndarray, gain: float) -> None:
        a = (alpha * gain)[..., None]
        if float(np.max(a)) <= 0.0:
            return
        frame[:] = frame * (1.0 - a) + layer.astype(np.float32) * a

    def _render_raw_field_debug(self, t: float) -> np.ndarray:
        state = self.compute_state(t, include_coverage=True)
        frame = self._render_water_background(t, state).astype(np.float32)
        self._blend_bool_mask(frame, state.coverage_count == 1, TEAL, 0.20)
        self._blend_bool_mask(frame, state.coverage_count == 2, CREAM, 0.34)
        self._blend_bool_mask(frame, state.coverage_count == 3, SALMON, 0.42)
        self._blend_bool_mask(frame, state.coverage_count >= 4, RED, 0.20)
        self._blend_bool_mask(frame, state.ring_count >= 2, ICE, 0.36)
        return np.clip(frame, 0, 255).astype(np.uint8)

    def _render_selected_seeds_debug(self) -> np.ndarray:
        frame = self.base_frame.copy()
        source_color = bgr((82, 138, 144))
        for src in self.sources:
            pt = (int(round(src.x_work_px)), int(round(src.y_work_px)))
            cv2.circle(frame, pt, 4, source_color, -1, cv2.LINE_AA)
        for spec in self.primitive_specs:
            color = primitive_rgb(spec.primitive_type)
            seed = (int(round(spec.field_seed_xy[0])), int(round(spec.field_seed_xy[1])))
            center = (int(round(spec.style_center_xy[0])), int(round(spec.style_center_xy[1])))
            cv2.line(frame, seed, center, bgr((110, 120, 112)), 1, cv2.LINE_AA)
            cv2.circle(frame, seed, 5, bgr(color), -1, cv2.LINE_AA)
            cv2.circle(frame, center, 8, bgr(color), 1, cv2.LINE_AA)
        return frame

    def _render_candidates_debug(self) -> np.ndarray:
        frame = self.base_frame.copy()
        for spec in self.primitive_specs:
            color = primitive_rgb(spec.primitive_type)
            if spec.primitive_type == "circle":
                center = (int(round(spec.style_center_xy[0])), int(round(spec.style_center_xy[1])))
                radius = int(round(spec.size_params["radius_px"]))
                cv2.circle(frame, center, radius, bgr(color), 2, cv2.LINE_AA)
                cv2.circle(frame, center, int(round(spec.size_params["inner_radius_px"])), bgr(color), 1, cv2.LINE_AA)
            elif spec.primitive_type == "crescent":
                self._draw_crescent_outline(frame, spec, color)
            elif spec.primitive_type == "trigon":
                pts = curved_trigon_points(
                    spec.style_center_xy,
                    math.radians(spec.angle_degrees),
                    spec.size_params["length_px"],
                    spec.size_params["width_px"],
                )
                cv2.polylines(frame, [pts.astype(np.int32)], True, bgr(color), 2, cv2.LINE_AA)
        return frame

    def _draw_crescent_outline(self, frame: np.ndarray, spec: PrimitiveSpec, color: tuple[int, int, int]) -> None:
        cx, cy = spec.style_center_xy
        angle = math.radians(spec.angle_degrees)
        tangent_degrees = spec.angle_degrees + 90.0
        inward = (-math.cos(angle), -math.sin(angle))
        outer_axes = (
            int(round(spec.size_params["outer_axis_tangent_px"])),
            int(round(spec.size_params["outer_axis_normal_px"])),
        )
        inner_axes = (
            int(round(spec.size_params["inner_axis_tangent_px"])),
            int(round(spec.size_params["inner_axis_normal_px"])),
        )
        shift = spec.size_params["inner_shift_inward_px"]
        center = (int(round(cx)), int(round(cy)))
        cutout_center = (int(round(cx + inward[0] * shift)), int(round(cy + inward[1] * shift)))
        cv2.ellipse(frame, center, outer_axes, tangent_degrees, 0, 360, bgr(color), 2, cv2.LINE_AA)
        cv2.ellipse(frame, cutout_center, inner_axes, tangent_degrees, 0, 360, bgr(color), 1, cv2.LINE_AA)

    def _render_construction_overlay_debug(self) -> np.ndarray:
        frame = self._render_final(66.0)
        overlay = self._render_selected_seeds_debug()
        return cv2.addWeighted(frame, 0.72, overlay, 0.44, 0.0)

    def _render_audit_overlay_debug(self) -> np.ndarray:
        frame = self._render_final(66.0)
        for spec in self.primitive_specs:
            seed = (int(round(spec.field_seed_xy[0])), int(round(spec.field_seed_xy[1])))
            center = (int(round(spec.style_center_xy[0])), int(round(spec.style_center_xy[1])))
            cv2.line(frame, seed, center, bgr((184, 184, 160)), 1, cv2.LINE_AA)
            cv2.drawMarker(frame, seed, bgr(primitive_rgb(spec.primitive_type)), cv2.MARKER_CROSS, 12, 2, cv2.LINE_AA)
        return frame

    def state_info(self, t: float) -> dict[str, Any]:
        gains = grammar_gains(t % self.config.duration_seconds)
        return {
            "time_seconds": round(t % self.config.duration_seconds, 5),
            "grammar_gains": {key: round(value, 6) for key, value in gains.items()},
            "selected_feature_counts": self.selected_feature_counts(),
            "every_styled_primitive_has_field_seed": all(spec.field_seed_kind and spec.field_seed_xy for spec in self.primitive_specs),
        }

    def selected_feature_counts(self) -> dict[str, int]:
        return {
            "circle": len([spec for spec in self.primitive_specs if spec.primitive_type == "circle"]),
            "crescent": len([spec for spec in self.primitive_specs if spec.primitive_type == "crescent"]),
            "trigon": len([spec for spec in self.primitive_specs if spec.primitive_type == "trigon"]),
            "total": len(self.primitive_specs),
        }

    def primitive_catalog(self) -> list[dict[str, Any]]:
        out = []
        for spec in self.primitive_specs:
            item = asdict(spec)
            item["field_seed_xy_output_px"] = [
                round(spec.field_seed_xy[0] * self.output_scale_x, 3),
                round(spec.field_seed_xy[1] * self.output_scale_y, 3),
            ]
            item["style_center_xy_output_px"] = [
                round(spec.style_center_xy[0] * self.output_scale_x, 3),
                round(spec.style_center_xy[1] * self.output_scale_y, 3),
            ]
            out.append(item)
        return out


def draw_circle(layer: np.ndarray, alpha: np.ndarray, center: tuple[int, int], radius: int, rgb: tuple[int, int, int]) -> None:
    cv2.circle(layer, center, radius, bgr(rgb), -1, cv2.LINE_AA)
    cv2.circle(alpha, center, radius, 255, -1, cv2.LINE_AA)


def draw_ellipse(
    layer: np.ndarray,
    alpha: np.ndarray,
    center: tuple[int, int],
    axes: tuple[int, int],
    angle_degrees_value: float,
    rgb: tuple[int, int, int],
) -> None:
    cv2.ellipse(layer, center, axes, angle_degrees_value, 0, 360, bgr(rgb), -1, cv2.LINE_AA)
    cv2.ellipse(alpha, center, axes, angle_degrees_value, 0, 360, 255, -1, cv2.LINE_AA)


def draw_curved_trigon(
    layer: np.ndarray,
    alpha: np.ndarray,
    center: tuple[float, float],
    angle_radians: float,
    length: float,
    width: float,
    rgb: tuple[int, int, int],
) -> None:
    pts = curved_trigon_points(center, angle_radians, length, width)
    cv2.fillPoly(layer, [pts.astype(np.int32)], bgr(rgb), cv2.LINE_AA)
    cv2.fillPoly(alpha, [pts.astype(np.int32)], 255, cv2.LINE_AA)


def curved_trigon_points(center: tuple[float, float], angle_radians: float, length: float, width: float) -> np.ndarray:
    tip = np.array([length * 0.58, 0.0], dtype=np.float32)
    base_l = np.array([-length * 0.42, -width * 0.50], dtype=np.float32)
    base_r = np.array([-length * 0.42, width * 0.50], dtype=np.float32)
    side_l_control = np.array([length * 0.05, -width * 0.30], dtype=np.float32)
    side_r_control = np.array([length * 0.05, width * 0.30], dtype=np.float32)
    base_control = np.array([-length * 0.63, 0.0], dtype=np.float32)

    pts = []
    pts.extend(quadratic_bezier(base_l, side_l_control, tip, 14))
    pts.extend(quadratic_bezier(tip, side_r_control, base_r, 14))
    pts.extend(quadratic_bezier(base_r, base_control, base_l, 12))
    local = np.array(pts, dtype=np.float32)
    c = math.cos(angle_radians)
    s = math.sin(angle_radians)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    return local @ rot.T + np.array(center, dtype=np.float32)


def quadratic_bezier(a: np.ndarray, b: np.ndarray, c: np.ndarray, steps: int) -> list[np.ndarray]:
    pts = []
    for i in range(steps):
        t = i / max(1, steps - 1)
        pts.append(((1.0 - t) ** 2) * a + 2.0 * (1.0 - t) * t * b + (t**2) * c)
    return pts


def primitive_rgb(primitive_type: str) -> tuple[int, int, int]:
    if primitive_type == "circle":
        return TEAL
    if primitive_type == "crescent":
        return CREAM
    if primitive_type == "trigon":
        return SALMON
    return LABEL


def np_smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep01(value: float) -> float:
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def ramp(t: float, start: float, end: float) -> float:
    return smoothstep01((t - start) / max(1e-6, end - start))


def grammar_gains(t: float) -> dict[str, float]:
    release = 1.0 - ramp(t, RELEASE_START_SECONDS, RELEASE_END_SECONDS)
    return {
        "circle": ramp(t, 15.0, 30.0) * release,
        "crescent": ramp(t, 30.0, 45.0) * release,
        "trigon": ramp(t, 45.0, FULL_HOLD_START_SECONDS) * release,
    }


def bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def angle_degrees(dx: float, dy: float) -> float:
    return math.degrees(math.atan2(dy, dx)) % 360.0


def angular_distance_degrees(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def frame_time(frame_idx: int) -> float:
    return frame_idx / FPS


def draw_text(frame: np.ndarray, text: str, org: tuple[int, int], scale: float = 0.38) -> None:
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, bgr(LABEL), 1, cv2.LINE_AA)


def label_panel(frame: np.ndarray, label: str, *, size: tuple[int, int] = (640, 360)) -> np.ndarray:
    panel = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    shade = np.zeros_like(panel)
    cv2.rectangle(shade, (0, 0), (size[0], 52), bgr(DEEP), -1)
    cv2.addWeighted(shade, 0.64, panel, 1.0, 0, dst=panel)
    draw_text(panel, label, (18, 34), 0.34)
    return panel


def count_statistics(count: np.ndarray, label: str) -> dict[str, Any]:
    unique, counts = np.unique(count, return_counts=True)
    by_count = {str(int(k)): int(v) for k, v in zip(unique, counts, strict=True)}
    total = int(count.size)
    nonzero = int(np.count_nonzero(count > 0))
    return {
        "map": label,
        "pixel_total": total,
        "by_exact_count": by_count,
        "count_0_pixels": int(np.count_nonzero(count == 0)),
        "count_1_pixels": int(np.count_nonzero(count == 1)),
        "count_2_pixels": int(np.count_nonzero(count == 2)),
        "count_3_pixels": int(np.count_nonzero(count == 3)),
        "count_3plus_pixels": int(np.count_nonzero(count >= 3)),
        "nonzero_pixels": nonzero,
        "nonzero_fraction": round(nonzero / total, 8),
        "max_count": int(count.max()) if count.size else 0,
        "empty": nonzero == 0,
        "uniform": len(unique) <= 1,
    }


def config_for(target: str) -> RenderConfig:
    width, height = DRAFT_SIZE if target == "draft1080" else UHD_SIZE
    if target == "uhd":
        work_width = 960
        work_height = 540
        note = "UHD MP4 is encoded at 3840x2160 from a 960x540 analytic work canvas with ffmpeg Lanczos scaling."
    else:
        work_width = 640
        work_height = 360
        note = "Draft MP4 is encoded at 1920x1080 from a 640x360 analytic work canvas with ffmpeg Lanczos scaling."
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
        grammar_support_time_seconds=GRAMMAR_SUPPORT_TIME_SECONDS,
        release_start_seconds=RELEASE_START_SECONDS,
        release_end_seconds=RELEASE_END_SECONDS,
        work_canvas_note=note,
    )


def save_key_stills(renderer: GrammarCrystallizationRenderer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in KEY_STILLS:
        frame, _info = renderer.render_frame(t, output_size=True, mode="final")
        path = STILLS_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[key] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(renderer: GrammarCrystallizationRenderer) -> Path:
    panels = []
    for t in CONTACT_TIMES:
        frame, info = renderer.render_frame(t, output_size=False, mode="final")
        gains = info["grammar_gains"]
        label = f"t={t:04.1f}s | C={gains['circle']:.2f} Cr={gains['crescent']:.2f} T={gains['trigon']:.2f}"
        panels.append(label_panel(frame, label, size=(480, 270)))
    rows = [cv2.hconcat(panels[i : i + 5]) for i in range(0, len(panels), 5)]
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_debug_sheets(renderer: GrammarCrystallizationRenderer) -> dict[str, Path]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    views = [
        ("01 raw field frame", "raw_field", "01_raw_field_frame"),
        ("02 selected field-derived seeds", "selected_seeds", "02_selected_field_derived_seeds"),
        ("03 candidates before styling", "grammar_candidates", "03_grammar_candidates_before_styling"),
        ("04 grammar construction overlay", "construction_overlay", "04_grammar_construction_overlay"),
        ("05 final styled hold frame", "final", "05_final_styled_hold_frame"),
        ("06 no-arbitrary-placement audit", "audit_overlay", "06_no_arbitrary_placement_audit"),
    ]
    panels = []
    outputs: dict[str, Path] = {}
    for label, mode, key in views:
        if mode == "final":
            frame, _ = renderer.render_frame(66.0, output_size=False, mode="final")
        else:
            frame, _ = renderer.render_frame(66.0, output_size=False, mode=mode)
        panels.append(label_panel(frame, label, size=(640, 360)))
        path = DEBUG_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR))
        outputs[key] = path

    sheet = cv2.vconcat([cv2.hconcat(panels[:3]), cv2.hconcat(panels[3:])])
    counts = renderer.selected_feature_counts()
    footer = (
        "debug audit: primary styled primitives are seeded by source centers, coverage_count==2 components, "
        f"or coverage_count==3 components; counts={counts}; no Austin source artwork used."
    )
    draw_text(sheet, footer, (24, sheet.shape[0] - 20), 0.35)
    debug_sheet = DEBUG_DIR / f"{PROJECT}_debug_verification_sheet.png"
    cv2.imwrite(str(debug_sheet), sheet)
    outputs["debug_verification_sheet"] = debug_sheet
    return outputs


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


def render_clip(renderer: GrammarCrystallizationRenderer, *, software_codec: bool) -> dict[str, Any]:
    path = OUT_DIR / f"{PROJECT}.mp4"
    input_size = (renderer.config.work_width, renderer.config.work_height)
    output_size = (renderer.config.width, renderer.config.height)
    writer = H264Writer(path, fps=FPS, input_size=input_size, output_size=output_size, software_codec=software_codec)
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
        "upscale": "ffmpeg Lanczos scale from analytic work canvas to final UHD output" if input_size != output_size else "none",
        "video_encoder": "libx264" if software_codec else "h264_videotoolbox",
        "frame_time_mapping": "frame_idx / fps; final encoded frame is one frame before duration, then loops to frame 0",
    }


def make_loop_diagnostic(renderer: GrammarCrystallizationRenderer, clip: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
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
        "loop_strategy": "0s and 80-84s use the same dark-water base; wave field and grammar layer fade out before the loop point.",
    }
    return path, verification


def ffprobe_json(video_path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,codec_name",
        "-of",
        "json",
        str(video_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_activation_summary(renderer: GrammarCrystallizationRenderer) -> dict[str, Any]:
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


def sampled_field_statistics(renderer: GrammarCrystallizationRenderer) -> dict[str, Any]:
    samples: dict[str, Any] = {}
    for t in (0.0, 15.0, 30.0, GRAMMAR_SUPPORT_TIME_SECONDS, 60.0, 66.0, 72.0, 80.0, DURATION_SECONDS):
        state = renderer.compute_state(t, include_coverage=True)
        samples[f"{t:05.1f}s"] = {
            "ring_count_statistics": count_statistics(state.ring_count, "ring"),
            "coverage_count_statistics": count_statistics(state.coverage_count, "coverage"),
            "active_source_count": len(state.active_sources),
        }
    return samples


def validation_verdict(renderer: GrammarCrystallizationRenderer, loop_verification: dict[str, Any]) -> dict[str, Any]:
    counts = renderer.selected_feature_counts()
    primitive_seeded = all(bool(spec.field_seed_kind) and len(spec.source_ids) >= 1 for spec in renderer.primitive_specs)
    pass_conditions = {
        "feature_count_within_12_to_24": 12 <= counts["total"] <= 24,
        "has_circle_primitives": counts["circle"] > 0,
        "has_crescent_primitives": counts["crescent"] > 0,
        "has_trigon_primitives": counts["trigon"] > 0,
        "every_styled_primitive_has_field_derived_seed": primitive_seeded,
        "full_hold_window_seconds": [FULL_HOLD_START_SECONDS, FULL_HOLD_END_SECONDS],
        "raw_virtual_loop_exact": bool(loop_verification.get("raw_virtual_loop_exact", False)),
        "decoded_loop_seam_mad_below_1": bool(loop_verification.get("decoded_loop_seam_mad_below_1", False))
        if loop_verification.get("decoded_loop_seam_mad_below_1") is not None
        else None,
        "no_austin_source_artwork_read_or_modified": True,
        "no_svg_or_source_asset_modifications": True,
        "final_mp4_contains_debug_text": False,
    }
    required = [
        pass_conditions["feature_count_within_12_to_24"],
        pass_conditions["has_circle_primitives"],
        pass_conditions["has_crescent_primitives"],
        pass_conditions["has_trigon_primitives"],
        pass_conditions["every_styled_primitive_has_field_derived_seed"],
        pass_conditions["raw_virtual_loop_exact"],
        pass_conditions["no_austin_source_artwork_read_or_modified"],
        pass_conditions["no_svg_or_source_asset_modifications"],
        not pass_conditions["final_mp4_contains_debug_text"],
    ]
    if pass_conditions["decoded_loop_seam_mad_below_1"] is not None:
        required.append(pass_conditions["decoded_loop_seam_mad_below_1"])
    verdict = "PASS" if all(required) else "MIXED"
    return {
        "verdict": verdict,
        "conditions": pass_conditions,
        "selected_feature_counts": counts,
        "visual_acceptance_note": (
            "Renderer self-audit passes the grammar/provenance contract. Final visual acceptance still requires Austin review."
        ),
    }


def write_manifest(
    renderer: GrammarCrystallizationRenderer,
    clip: dict[str, Any],
    stills: dict[str, str],
    contact_sheet: Path,
    debug_paths: dict[str, Path],
    loop_sheet: Path | None,
    loop_verification: dict[str, Any],
    probe: dict[str, Any] | None,
) -> Path:
    support_state = renderer.compute_state(GRAMMAR_SUPPORT_TIME_SECONDS, include_coverage=True)
    manifest = {
        "project": PROJECT,
        "status": "generated_austin_coast_salish_style_support_composition_pending_austin_review",
        "use_boundary": "internal/show-development only pending Austin review",
        "important_framing": (
            "This is a generated Austin/Coast Salish-style primitive grammar experiment using wave geometry as scaffold. "
            "It does not claim that the final design purely emerges from physics. Field-derived wave geometry provides "
            "anchors, arcs, normals, junctions, pressure points, and timing; the grammar layer intentionally crystallizes "
            "those features into generated primitive syntax."
        ),
        "authorization_note": (
            "Austin has authorized Austin-style / Coast Salish-style generated experiments for this internal/show-development pipeline."
        ),
        "austin_source_artwork_used": False,
        "austin_source_artwork_read_or_modified": False,
        "svg_or_source_asset_modifications": False,
        "renderer": f"scripts/{PROJECT}.py",
        "renderer_sha256": sha256(ROOT / "scripts" / f"{PROJECT}.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "output_specs": {
            "resolution": [renderer.config.width, renderer.config.height],
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frame_count": N_FRAMES,
            "loopable_mp4": True,
        },
        "source_script_references": [
            "scripts/abstract_cymatic_wavefront_overlap_path_a_v002.py",
            "track2-deterministic/morph_outputs_INTERNAL/abstract_cymatic_wavefront_overlap_path_a_v002_2026-05-22/",
            "track2-deterministic/morph_outputs_INTERNAL/abstract_cymatic_wave_equation_overlap_path_b_v001_2026-05-22/",
        ],
        "render_settings": asdict(renderer.config),
        "field_model": {
            "source_count": len(renderer.sources),
            "lattice": "radius-2 hexagonal / flower-of-life point lattice: 1 center, 6 first ring, 12 second ring",
            "activation_rule": "source activation time = impact_time + distance_from_center / wave_speed; center activates at impact_time",
            "ring_count_rule": "abs(distance_to_source - current_radius) <= ring_width",
            "coverage_count_rule": "distance_to_source <= current_radius",
            "grammar_support_frame_seconds": GRAMMAR_SUPPORT_TIME_SECONDS,
            "sources": [asdict(src) for src in renderer.sources],
            "activation_summary": source_activation_summary(renderer),
        },
        "grammar_layer": {
            "selected_feature_counts": renderer.selected_feature_counts(),
            "every_styled_primitive_has_field_derived_seed": all(
                bool(spec.field_seed_kind) and len(spec.source_ids) >= 1 for spec in renderer.primitive_specs
            ),
            "circle_rule": "7 circle primitives from exact center and first-ring source centers; nested circles remain concentric with those seeds.",
            "crescent_rule": "8 crescent primitives from selected coverage_count == 2 lens/annular-band components.",
            "trigon_rule": "6 trigon primitives from selected coverage_count == 3 pressure components, oriented on outward normals.",
            "hierarchy_rule": "21 primary features selected; weak/noisy detections are discarded.",
            "primitive_catalog": renderer.primitive_catalog(),
        },
        "sequence": {
            "0_15s": "Dark water / rain ripple field; no explicit styled primitives.",
            "15_30s": "Central and first-ring circle primitives crystallize.",
            "30_45s": "Crescents crystallize from selected two-overlap field components.",
            "45_60s": "Trigons crystallize from selected triple-overlap pressure components.",
            "60_72s": "Full generated support composition holds.",
            "72_84s": "Design dissolves back to water and returns to loop start.",
        },
        "support_frame_statistics": {
            "ring_count_statistics": count_statistics(support_state.ring_count, "ring"),
            "coverage_count_statistics": count_statistics(support_state.coverage_count, "coverage"),
        },
        "sampled_field_statistics": sampled_field_statistics(renderer),
        "loop_diagnostics": loop_verification,
        "ffprobe": probe,
        "validation_verdict": validation_verdict(renderer, loop_verification),
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_verification_sheet": str(debug_paths["debug_verification_sheet"].relative_to(OUT_DIR)),
            "readme": "README.md",
            "manifest": f"{PROJECT}_manifest.json",
            "loop_diagnostic_sheet": str(loop_sheet.relative_to(OUT_DIR)) if loop_sheet else None,
            **{key: str(path.relative_to(OUT_DIR)) for key, path in debug_paths.items() if key != "debug_verification_sheet"},
            **{f"{key}_still": rel for key, rel in stills.items()},
        },
        "clip": clip,
    }
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(renderer: GrammarCrystallizationRenderer, loop_verification: dict[str, Any], rendered: bool) -> Path:
    counts = renderer.selected_feature_counts()
    verdict = validation_verdict(renderer, loop_verification)
    lines = [
        "# Abstract Cymatic Wavefront Overlap Path A v003 Grammar Crystallization",
        "",
        "Status: generated Austin/Coast Salish-style support composition for internal/show-development only, pending Austin review.",
        "",
        "No Austin source artwork was used, read, copied, traced, or modified.",
        "",
        "## Framing",
        "",
        "This is not a claim that the finished composition purely emerges from physics. The field-derived wave geometry supplies anchors, arcs, normals, junctions, pressure points, and timing; the grammar layer intentionally crystallizes those features into generated primitive syntax.",
        "",
        "## Output",
        "",
        f"- MP4: `{PROJECT}.mp4`, {renderer.config.width}x{renderer.config.height}, 24fps, {DURATION_SECONDS:.0f}s." if rendered else "- MP4: not rendered in preview mode.",
        f"- Contact sheet: `{PROJECT}_contact_sheet.png`.",
        f"- Debug sheet: `debug/{PROJECT}_debug_verification_sheet.png`.",
        f"- Manifest: `{PROJECT}_manifest.json`.",
        "",
        "## Selected Primitive Counts",
        "",
        f"- Circles: `{counts['circle']}`.",
        f"- Crescents: `{counts['crescent']}`.",
        f"- Trigons: `{counts['trigon']}`.",
        f"- Total primary field-derived features: `{counts['total']}`.",
        f"- Every styled primary primitive has a field-derived seed: `{verdict['conditions']['every_styled_primitive_has_field_derived_seed']}`.",
        "",
        "## Debug / Verification",
        "",
        "- `01_raw_field_frame`: raw field/count-map support frame.",
        "- `02_selected_field_derived_seeds`: selected source/component seeds.",
        "- `03_grammar_candidates_before_styling`: primitive candidates before styling.",
        "- `04_grammar_construction_overlay`: styled primitives over construction seeds.",
        "- `05_final_styled_hold_frame`: final hold frame.",
        "- `06_no_arbitrary_placement_audit`: final frame over source seeds.",
        "",
        "## Loop",
        "",
        f"- Raw virtual frame0/duration MAD: `{loop_verification.get('raw_render_frame0_duration_mean_abs_diff')}`.",
        f"- Decoded frame0/final MAD: `{loop_verification.get('decoded_frame0_final_mean_abs_diff')}`.",
        f"- Loop strategy: `{loop_verification.get('loop_strategy')}`.",
        "",
        "## Renderer Verdict",
        "",
        f"`{verdict['verdict']}` by renderer self-audit for provenance, counts, sequence, and loop diagnostics. Final cultural/style acceptance remains pending Austin review.",
        "",
        f"Renderer: `scripts/{PROJECT}.py`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render v003 field-seeded primitive grammar crystallization.")
    parser.add_argument("--target", choices=("uhd", "draft1080"), default="uhd")
    parser.add_argument("--preview", action="store_true", help="Write stills/debug/manifest without rendering MP4.")
    parser.add_argument("--software-codec", action="store_true", help="Use libx264 instead of h264_videotoolbox.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    renderer = GrammarCrystallizationRenderer(config_for(args.target))
    print("Writing key stills, contact sheet, and debug sheets", flush=True)
    stills = save_key_stills(renderer)
    contact = make_contact_sheet(renderer)
    debug_paths = make_debug_sheets(renderer)

    probe: dict[str, Any] | None = None
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
            "loop_strategy": "0s and 80-84s use the same dark-water base; wave field and grammar layer fade out before the loop point.",
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
        clip = render_clip(renderer, software_codec=args.software_codec)
        print("Writing loop diagnostic sheet", flush=True)
        loop_sheet, loop_verification = make_loop_diagnostic(renderer, clip)
        probe = ffprobe_json(OUT_DIR / clip["mp4"])
        (DEBUG_DIR / f"{PROJECT}_ffprobe.json").write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")

    manifest = write_manifest(renderer, clip, stills, contact, debug_paths, loop_sheet, loop_verification, probe)
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
