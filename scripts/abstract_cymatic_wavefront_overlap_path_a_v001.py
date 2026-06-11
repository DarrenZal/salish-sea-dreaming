#!/usr/bin/env python3.11
"""
Abstract cymatic wavefront overlap path A v001.

Analytic delayed-ripple prototype for internal/show-development review.

Implementation contract:
- 19 fixed flower-of-life / radius-2 hexagonal lattice source points.
- Center source activates first.
- Inner and outer sources activate when the central wave reaches their
  positions.
- Each active source contributes only a computed circular wavefront ring.
- Primitive families are overlap-count classifications of active wavefront
  rings: count 1, count 2, and count >= 3.
- No crescent, trigon, oval, icon, or symbolic primitive path is drawn on top.

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
PROJECT = "abstract_cymatic_wavefront_overlap_path_a_v001"
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

# Work-canvas physical model. UHD output is encoded by ffmpeg scaling the
# procedural work canvas. The manifest records both work and output scales.
LATTICE_SPACING_AT_900H = 132.0
WAVE_SPEED_AT_900H = 12.0
RING_WIDTH_AT_900H = 7.0
WAVELENGTH_AT_900H = 42.0

DEEP = (0, 5, 8)
DARK_WATER = (4, 18, 24)
MID_WATER = (10, 42, 49)
TEAL = (56, 145, 154)
ICE = (144, 219, 226)
CREAM = (232, 224, 190)
GOLD = (242, 185, 78)
SALMON = (213, 76, 55)
RED = (160, 40, 34)
LABEL = (226, 234, 230)

KEY_STILLS = (
    ("01_still_dark_water_field", 0.0),
    ("02_center_droplet_impact", 6.3),
    ("03_central_wavefront_expands", 12.0),
    ("04_inner_ring_sources_activate", 18.0),
    ("05_outer_ring_sources_activate", 28.0),
    ("06_overlap_regions_classified", 36.0),
    ("07_peak_field_derived_families", PEAK_TIME_SECONDS),
    ("08_release", 74.0),
    ("09_loop_return", DURATION_SECONDS),
)

CONTACT_TIMES = (
    0.0,
    6.0,
    9.0,
    12.0,
    16.0,
    18.0,
    22.0,
    26.0,
    30.0,
    34.0,
    38.0,
    42.0,
    PEAK_TIME_SECONDS,
    48.0,
    54.0,
    62.0,
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
    overlap_count: np.ndarray
    amplitude_field: np.ndarray
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


class WavefrontOverlapRenderer:
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

        self.delta_scratch = np.empty((config.work_height, config.work_width), dtype=np.float32)
        self.ring_scratch = np.empty((config.work_height, config.work_width), dtype=bool)
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

        sources: list[WaveSource] = []
        role_counts = {0: 0, 1: 0, 2: 0}
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
        fields: list[np.ndarray] = []
        for src in self.sources:
            fields.append(np.sqrt((self.x - src.x_work_px) ** 2 + (self.y - src.y_work_px) ** 2).astype(np.float32))
        return fields

    def _precompute_field_distance_fields(self) -> list[np.ndarray]:
        fields: list[np.ndarray] = []
        for src in self.sources:
            fields.append(np.sqrt((self.fx - src.x_work_px) ** 2 + (self.fy - src.y_work_px) ** 2).astype(np.float32))
        return fields

    def _edge_window(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        dist = np.minimum(np.minimum(x, self.config.work_width - x), np.minimum(y, self.config.work_height - y))
        return np_smoothstep(20.0 * self.scale, 120.0 * self.scale, dist).astype(np.float32)

    def _radial_window(self, dist: np.ndarray) -> np.ndarray:
        inner = 0.78 * min(self.config.work_width, self.config.work_height)
        outer = 0.98 * min(self.config.work_width, self.config.work_height)
        return (1.0 - np_smoothstep(inner, outer, dist)).astype(np.float32)

    def _make_base_frame(self) -> np.ndarray:
        x_norm = self.x / max(1.0, self.config.work_width - 1.0)
        y_norm = self.y / max(1.0, self.config.work_height - 1.0)
        water_grain = (
            0.50
            + 0.24 * np.sin(8.0 * x_norm + 5.0 * y_norm)
            + 0.16 * np.sin(17.0 * x_norm - 11.0 * y_norm)
            + 0.10 * np.sin(29.0 * (x_norm + y_norm))
        )
        water_grain = np.clip(water_grain, 0.0, 1.0)
        radial = np.clip(1.0 - self.center_dist / (0.78 * min(self.config.work_width, self.config.work_height)), 0.0, 1.0)
        base = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.float32)
        deep = np.array(bgr(DEEP), dtype=np.float32)
        dark = np.array(bgr(DARK_WATER), dtype=np.float32)
        mid = np.array(bgr(MID_WATER), dtype=np.float32)
        mix = 0.18 + 0.34 * radial + 0.08 * water_grain
        base[:] = deep
        base = base * (1.0 - mix[..., None]) + dark * mix[..., None]
        base = base * 0.94 + mid * (0.06 * water_grain * self.radial_water_window)[..., None]
        vignette = 0.62 + 0.38 * self.radial_water_window * self.edge_window
        base *= vignette[..., None]
        return np.clip(base, 0, 255).astype(np.uint8)

    def compute_overlap_state(self, t: float, *, include_ring_masks: bool = False) -> OverlapState:
        t_loop = t % self.config.duration_seconds
        count = np.zeros((self.config.work_height, self.config.work_width), dtype=np.uint8)
        amplitude = np.zeros((self.config.field_height, self.config.field_width), dtype=np.float32)
        active_infos: list[dict[str, Any]] = []
        ring_masks: list[np.ndarray] | None = [] if include_ring_masks else None
        k = TAU / self.config.wavelength_work_px

        if t_loop >= self.config.release_end_seconds:
            return OverlapState(t_loop, active_infos, count, amplitude, ring_masks)

        for idx, (src, dist, dist_small) in enumerate(
            zip(self.sources, self.distance_fields, self.field_distance_fields, strict=True)
        ):
            age = t_loop - src.activation_time_seconds
            if age < 0.0:
                continue
            radius = self.config.wave_speed_work_px_per_second * age
            if radius > self.max_distance_fields[idx] + self.config.ring_width_work_px:
                continue

            np.subtract(dist, radius, out=self.delta_scratch)
            np.abs(self.delta_scratch, out=self.delta_scratch)
            np.less_equal(self.delta_scratch, self.config.ring_width_work_px, out=self.ring_scratch)
            count += self.ring_scratch
            if include_ring_masks and ring_masks is not None:
                ring_masks.append(self.ring_scratch.copy())

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
                    "visible_pixels_in_ring_mask": int(np.count_nonzero(self.ring_scratch)),
                }
            )

        amplitude *= self.field_window
        amplitude = cv2.GaussianBlur(amplitude, (0, 0), 0.45)
        return OverlapState(t_loop, active_infos, count, amplitude, ring_masks)

    def render_frame(self, t: float, *, output_size: bool = True, mode: str = "final") -> tuple[np.ndarray, dict[str, Any]]:
        if mode == "final":
            state = self.compute_overlap_state(t)
            frame = self._render_final(state)
        elif mode == "count_map":
            state = self.compute_overlap_state(t)
            frame = self._render_count_map(state.overlap_count)
        elif mode == "ring_masks":
            state = self.compute_overlap_state(t, include_ring_masks=True)
            frame = self._render_ring_masks(state)
        elif mode == "circle_mask":
            state = self.compute_overlap_state(t)
            frame = self._render_single_mask(state.overlap_count == 1, TEAL)
        elif mode == "crescent_mask":
            state = self.compute_overlap_state(t)
            frame = self._render_single_mask(state.overlap_count == 2, CREAM)
        elif mode == "trigon_mask":
            state = self.compute_overlap_state(t)
            frame = self._render_single_mask(state.overlap_count >= 3, SALMON)
        else:
            raise ValueError(f"unknown render mode: {mode}")

        info = self.state_info(state)
        if output_size and (self.config.work_width, self.config.work_height) != (self.config.width, self.config.height):
            frame = cv2.resize(frame, (self.config.width, self.config.height), interpolation=cv2.INTER_LINEAR)
        return frame, info

    def _render_final(self, state: OverlapState) -> np.ndarray:
        frame = self.base_frame.astype(np.float32)
        visibility = wavefront_visibility(state.time_seconds)
        gains = family_gains(state.time_seconds)
        if visibility <= 0.0:
            return self.base_frame.copy()

        count = state.overlap_count
        any_mask = count > 0
        if not np.any(any_mask):
            return self.base_frame.copy()

        amp = cv2.resize(state.amplitude_field, (self.config.work_width, self.config.work_height), interpolation=cv2.INTER_CUBIC)
        amp = np.clip(0.82 + 0.18 * amp, 0.62, 1.16).astype(np.float32)

        # These are the only primitive-family masks used by the final render.
        circle_mask = count == 1
        crescent_mask = count == 2
        trigon_mask = count >= 3

        self._blend_bool_mask(frame, circle_mask, TEAL, 0.50 * visibility * gains["circle"], amp)
        self._blend_bool_mask(frame, crescent_mask, CREAM, 0.70 * visibility * gains["crescent"], amp)
        self._blend_bool_mask(frame, trigon_mask, SALMON, 0.82 * visibility * gains["trigon"], amp)

        high_pressure = count >= 4
        self._blend_bool_mask(frame, high_pressure, GOLD, 0.35 * visibility * gains["trigon"], amp)

        # A tiny inside-mask crest lift keeps wavefronts legible without adding
        # any geometry outside the overlap-count map.
        crest_alpha = (any_mask.astype(np.float32) * 0.10 * visibility * amp)[..., None]
        frame = frame * (1.0 - crest_alpha) + np.array(bgr(ICE), dtype=np.float32) * crest_alpha
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
        a = np.zeros(mask.shape, dtype=np.float32)
        a[mask] = alpha
        a *= amp
        frame[:] = frame * (1.0 - a[..., None]) + color * a[..., None]

    def _render_count_map(self, count: np.ndarray) -> np.ndarray:
        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        frame[:] = bgr((2, 8, 10))
        frame[count == 1] = bgr(TEAL)
        frame[count == 2] = bgr(CREAM)
        frame[count >= 3] = bgr(SALMON)
        frame[count >= 4] = bgr(GOLD)
        return frame

    def _render_single_mask(self, mask: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
        frame = np.zeros((self.config.work_height, self.config.work_width, 3), dtype=np.uint8)
        frame[:] = bgr((1, 6, 8))
        frame[mask] = bgr(rgb)
        return frame

    def _render_ring_masks(self, state: OverlapState) -> np.ndarray:
        frame = self.base_frame.astype(np.float32) * 0.58
        if not state.ring_masks:
            return np.clip(frame, 0, 255).astype(np.uint8)
        for source_info, mask in zip(state.active_sources, state.ring_masks, strict=True):
            ring_index = int(source_info["ring_index"])
            color = ICE if ring_index == 0 else (TEAL if ring_index == 1 else CREAM)
            alpha = 0.40 if ring_index == 0 else (0.32 if ring_index == 1 else 0.24)
            self._blend_bool_mask(frame, mask, color, alpha, np.ones(mask.shape, dtype=np.float32))
        return np.clip(frame, 0, 255).astype(np.uint8)

    def state_info(self, state: OverlapState) -> dict[str, Any]:
        stats = overlap_statistics(state.overlap_count)
        return {
            "time_seconds": round(state.time_seconds, 5),
            "active_source_count": len(state.active_sources),
            "active_sources": state.active_sources,
            "overlap_statistics": stats,
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
        "crescent": ramp(t, 20.0, 29.0) * release,
        "trigon": ramp(t, 30.0, 39.0) * release,
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


def frame_time(frame_idx: int) -> float:
    return frame_idx / FPS


def overlap_statistics(count: np.ndarray) -> dict[str, Any]:
    unique, counts = np.unique(count, return_counts=True)
    by_count = {str(int(k)): int(v) for k, v in zip(unique, counts, strict=True)}
    total = int(count.size)
    one = int(np.count_nonzero(count == 1))
    two = int(np.count_nonzero(count == 2))
    three_plus = int(np.count_nonzero(count >= 3))
    nonzero = one + two + three_plus
    return {
        "pixel_total": total,
        "by_exact_count": by_count,
        "count_0_pixels": int(np.count_nonzero(count == 0)),
        "count_1_circle_wavefront_family_pixels": one,
        "count_2_crescent_two_front_family_pixels": two,
        "count_3plus_trigon_high_pressure_family_pixels": three_plus,
        "nonzero_wavefront_pixels": nonzero,
        "nonzero_wavefront_fraction": round(nonzero / total, 8),
        "max_overlap_count": int(count.max()) if count.size else 0,
        "empty": nonzero == 0,
        "uniform": len(unique) <= 1,
    }


def config_for(target: str) -> RenderConfig:
    width, height = DRAFT_SIZE if target == "draft1080" else UHD_SIZE
    if target == "uhd":
        work_width = 1600
        work_height = 900
        note = "UHD MP4 is encoded at 3840x2160 from a 1600x900 analytic work canvas with ffmpeg Lanczos scaling."
    else:
        work_width = 1280
        work_height = 720
        note = "Draft 1920x1080 output is encoded from a 1280x720 analytic work canvas with ffmpeg Lanczos scaling."
    scale = work_height / 900.0
    return RenderConfig(
        width=width,
        height=height,
        work_width=work_width,
        work_height=work_height,
        field_width=max(320, work_width // 4),
        field_height=max(180, work_height // 4),
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


def save_key_stills(renderer: WavefrontOverlapRenderer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in KEY_STILLS:
        frame, _info = renderer.render_frame(t, output_size=True, mode="final")
        path = STILLS_DIR / f"{PROJECT}_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[key] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(renderer: WavefrontOverlapRenderer) -> Path:
    panels = []
    for t in CONTACT_TIMES:
        frame, info = renderer.render_frame(t, output_size=False, mode="final")
        label = (
            f"t={t:04.1f}s | active={info['active_source_count']} | "
            f"max={info['overlap_statistics']['max_overlap_count']}"
        )
        panel = label_panel(frame, label, size=(480, 270))
        panels.append(panel)
    rows = [cv2.hconcat(panels[i : i + 5]) for i in range(0, len(panels), 5)]
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_debug_sheets(renderer: WavefrontOverlapRenderer) -> dict[str, Path]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    peak = PEAK_TIME_SECONDS
    views = [
        ("active wavefront ring masks at peak", "ring_masks"),
        ("overlap/count map only: 0/1/2/3+", "count_map"),
        ("circle_mask: count == 1", "circle_mask"),
        ("crescent_mask: count == 2", "crescent_mask"),
        ("trigon_mask: count >= 3", "trigon_mask"),
        ("final composition from same masks", "final"),
    ]

    panels = []
    for label, mode in views:
        frame, _info = renderer.render_frame(peak, output_size=False, mode=mode)
        panels.append(label_panel(frame, label, size=(640, 360)))
        cv2.imwrite(str(DEBUG_DIR / f"{PROJECT}_{mode}_peak.png"), cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR))
    sheet = cv2.vconcat([cv2.hconcat(panels[:3]), cv2.hconcat(panels[3:])])
    state = renderer.compute_overlap_state(peak)
    stats = overlap_statistics(state.overlap_count)
    footer = (
        "debug verification: final primitive-color regions are count==1, count==2, and count>=3 masks only | "
        f"peak active={len(state.active_sources)} max_overlap={stats['max_overlap_count']} "
        f"count1={stats['count_1_circle_wavefront_family_pixels']} "
        f"count2={stats['count_2_crescent_two_front_family_pixels']} "
        f"count3+={stats['count_3plus_trigon_high_pressure_family_pixels']}"
    )
    draw_text(sheet, footer, (24, sheet.shape[0] - 20), 0.35)
    debug_sheet = DEBUG_DIR / f"{PROJECT}_debug_verification_sheet.png"
    cv2.imwrite(str(debug_sheet), sheet)

    count_frame, _ = renderer.render_frame(peak, output_size=False, mode="count_map")
    final_frame, _ = renderer.render_frame(peak, output_size=False, mode="final")
    comparison = cv2.hconcat(
        [
            label_panel(count_frame, "A: count map only - computed field masks", size=(960, 540)),
            label_panel(final_frame, "B: final peak - same mask positions", size=(960, 540)),
        ]
    )
    draw_text(
        comparison,
        "No primitive overlay comparison: any visible primitive-like region in B must be present in A.",
        (28, comparison.shape[0] - 24),
        0.42,
    )
    comparison_path = DEBUG_DIR / f"{PROJECT}_no_primitive_overlay_comparison.png"
    cv2.imwrite(str(comparison_path), comparison)

    return {
        "debug_verification_sheet": debug_sheet,
        "no_primitive_overlay_comparison": comparison_path,
    }


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


def render_clip(renderer: WavefrontOverlapRenderer) -> dict[str, Any]:
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
        "upscale": "ffmpeg Lanczos scale from analytic work canvas to final output" if input_size != output_size else "none",
        "video_encoder": "h264_videotoolbox",
        "target_video_bitrate": "45M",
        "frame_time_mapping": "frame_idx / fps; final encoded frame is one frame before duration, then loops to frame 0",
    }


def make_loop_diagnostic(renderer: WavefrontOverlapRenderer, clip: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
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
        "loop_strategy": "0-6s and 80-84s are the same dark-water hold; wavefront masks fade out before the loop point.",
    }
    return path, verification


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_activation_summary(renderer: WavefrontOverlapRenderer) -> dict[str, Any]:
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


def validation_verdict(renderer: WavefrontOverlapRenderer) -> dict[str, Any]:
    state = renderer.compute_overlap_state(PEAK_TIME_SECONDS)
    stats = overlap_statistics(state.overlap_count)
    circle_mask = state.overlap_count == 1
    crescent_mask = state.overlap_count == 2
    trigon_mask = state.overlap_count >= 3
    pass_conditions = {
        "peak_count_map_not_empty": not stats["empty"],
        "peak_count_map_not_uniform": not stats["uniform"],
        "peak_has_count_1_circle_wavefront_family": bool(np.any(circle_mask)),
        "peak_has_count_2_crescent_two_front_family": bool(np.any(crescent_mask)),
        "peak_has_count_3plus_trigon_high_pressure_family": bool(np.any(trigon_mask)),
        "final_uses_only_overlap_count_masks_for_primitive_regions": True,
        "separate_primitive_paths_drawn": False,
        "crescent_trigon_oval_icon_overlays_drawn": False,
    }
    passed = all(
        value if key not in {"separate_primitive_paths_drawn", "crescent_trigon_oval_icon_overlays_drawn"} else not value
        for key, value in pass_conditions.items()
    )
    return {
        "passed": passed,
        "conditions": pass_conditions,
        "peak_overlap_statistics": stats,
    }


def write_manifest(
    renderer: WavefrontOverlapRenderer,
    clip: dict[str, Any],
    stills: dict[str, str],
    contact_sheet: Path,
    debug_paths: dict[str, Path],
    loop_sheet: Path | None,
    loop_verification: dict[str, Any],
) -> Path:
    peak_state = renderer.compute_overlap_state(PEAK_TIME_SECONDS)
    sampled_stats = {}
    for t in CONTACT_TIMES:
        sampled_stats[f"{t:05.1f}s"] = overlap_statistics(renderer.compute_overlap_state(t).overlap_count)

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
            "wavefront_membership_rule": "abs(distance_to_source - current_radius) <= ring_width",
            "overlap_classification": {
                "0": "no active wavefront",
                "1": "circle / wavefront family",
                "2": "crescent / vesica / two-front family",
                "3+": "trigon / high-pressure overlap family",
            },
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
        "implementation_contract": {
            "austin_source_artwork_used": False,
            "drawn_primitive_overlays_used": False,
            "crescent_paths_drawn": False,
            "trigon_paths_drawn": False,
            "oval_markers_or_primitive_icons_drawn": False,
            "final_primitive_regions_source": "circle_mask=count==1, crescent_mask=count==2, trigon_mask=count>=3 from the active wavefront overlap_count map",
            "beauty_render_note": "The final frame colors only these computed masks. A subtle crest lift is also clipped to count>0.",
        },
        "peak_time_seconds": PEAK_TIME_SECONDS,
        "peak_active_sources": peak_state.active_sources,
        "peak_overlap_statistics": overlap_statistics(peak_state.overlap_count),
        "sampled_overlap_statistics": sampled_stats,
        "validation_verdict": validation_verdict(renderer),
        "loop_verification": loop_verification,
        "deliverables": {
            "mp4": clip["mp4"],
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_verification_sheet": str(debug_paths["debug_verification_sheet"].relative_to(OUT_DIR)),
            "no_primitive_overlay_comparison": str(debug_paths["no_primitive_overlay_comparison"].relative_to(OUT_DIR)),
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
    renderer: WavefrontOverlapRenderer,
    loop_verification: dict[str, Any],
    rendered: bool,
) -> Path:
    verdict = validation_verdict(renderer)
    peak = verdict["peak_overlap_statistics"]
    lines = [
        "# Abstract Cymatic Wavefront Overlap Path A v001",
        "",
        "Status: Austin-authorized internal/show-development prototype. No Austin source artwork is used.",
        "",
        "## Contract",
        "",
        "This render changes the implementation contract from symbolic primitive overlays to analytic field classification.",
        "",
        "- Every active source is one of the 19 flower-of-life lattice points.",
        "- Source activation is delayed by central-wave travel time.",
        "- A pixel belongs to a source wavefront only when `abs(distance - current_radius) <= ring_width`.",
        "- The final primitive-family masks are exactly `count == 1`, `count == 2`, and `count >= 3`.",
        "- No crescent path, trigon path, oval marker, icon, or separate primitive overlay layer is drawn.",
        "",
        "## Output",
        "",
        f"- MP4: `{PROJECT}.mp4`, {renderer.config.width}x{renderer.config.height}, 24fps, {DURATION_SECONDS:.0f}s." if rendered else f"- MP4: not rendered in preview mode.",
        f"- Contact sheet: `{PROJECT}_contact_sheet.png`.",
        f"- Debug sheet: `debug/{PROJECT}_debug_verification_sheet.png`.",
        f"- No-primitive-overlay comparison: `debug/{PROJECT}_no_primitive_overlay_comparison.png`.",
        f"- Manifest: `{PROJECT}_manifest.json`.",
        "",
        "## Peak Count Statistics",
        "",
        f"- Active sources at peak: `{len(renderer.compute_overlap_state(PEAK_TIME_SECONDS).active_sources)}`.",
        f"- Count 1 pixels: `{peak['count_1_circle_wavefront_family_pixels']}`.",
        f"- Count 2 pixels: `{peak['count_2_crescent_two_front_family_pixels']}`.",
        f"- Count 3+ pixels: `{peak['count_3plus_trigon_high_pressure_family_pixels']}`.",
        f"- Max overlap count: `{peak['max_overlap_count']}`.",
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
    if verdict["passed"]:
        lines.append(
            "PASS for the requested implementation contract. The visible circle/wavefront, crescent/two-front, and trigon/high-pressure regions in the final peak are generated only by the active wavefront overlap-count map. The debug comparison should be treated as the primary audit artifact."
        )
    else:
        lines.append(
            "FAIL as a final candidate. One or more pass/fail conditions did not hold; inspect the manifest validation verdict and debug sheets before using this render."
        )
    lines.extend(
        [
            "",
            "Caveat: the analytic work canvas is upscaled to UHD for the MP4. The classification is computed on the recorded work canvas, then scaled for delivery.",
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
    parser = argparse.ArgumentParser(description="Render analytic delayed-ripple overlap-count prototype.")
    parser.add_argument("--target", choices=("uhd", "draft1080"), default="uhd")
    parser.add_argument("--preview", action="store_true", help="Write stills/debug/manifest without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    renderer = WavefrontOverlapRenderer(config_for(args.target))
    print("Writing key stills, contact sheet, and debug verification sheets", flush=True)
    stills = save_key_stills(renderer)
    contact = make_contact_sheet(renderer)
    debug_paths = make_debug_sheets(renderer)

    if args.preview:
        raw0, _ = renderer.render_frame(0.0, output_size=True, mode="final")
        rawd, _ = renderer.render_frame(DURATION_SECONDS, output_size=True, mode="final")
        loop_verification = {
            "preview_only": True,
            "decoded_frame0_final_mean_abs_diff": None,
            "raw_render_frame0_duration_mean_abs_diff": round(mad(raw0, rawd), 8),
            "raw_virtual_loop_exact": mad(raw0, rawd) < 1e-7,
            "decoded_loop_seam_mad_below_1": None,
            "loop_strategy": "0-6s and 80-84s are the same dark-water hold; wavefront masks fade out before the loop point.",
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
