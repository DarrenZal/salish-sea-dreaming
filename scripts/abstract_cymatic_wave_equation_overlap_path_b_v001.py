#!/usr/bin/env python3
"""
Abstract cymatic wave-equation overlap path B v001.

This renderer is an internal water-wave primitive-emergence study. It uses a
real 2D damped heightfield wave equation with droplet impulses at a 19-point
flower-of-life / radius-2 hex lattice. The final color emphasis is derived from
field ridge masks intersected with tracked wavefront contributor counts. No
circle, crescent, trigon, icon, SVG, or symbolic primitive overlay is drawn.

Boundary: Austin has greenlit Austin-style / Coast Salish-style generated
experiments for this project context. This render uses no Austin source
artwork and makes no claim of cultural authority or cultural meaning.
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

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "abstract_cymatic_wave_equation_overlap_path_b_v001"
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / f"{PROJECT}_2026-05-22"
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug"

FPS = 24
DURATION_SECONDS = 80.0
FRAME_COUNT = int(FPS * DURATION_SECONDS)
PEAK_TIME_SECONDS = 63.5
PEAK_FRAME = int(round(PEAK_TIME_SECONDS * FPS))
FADE_RESET_START_SECONDS = 72.0
TAU = math.tau

SIM_SIZE = (384, 216)
UHD_SIZE = (3840, 2160)

CONTACT_TIMES = (
    0.0,
    2.0,
    6.0,
    10.0,
    14.0,
    18.0,
    22.0,
    28.0,
    34.0,
    40.0,
    44.0,
    48.0,
    52.0,
    56.0,
    60.0,
    PEAK_TIME_SECONDS,
    67.0,
    72.0,
    76.0,
    79.9,
)

KEY_STILLS = {
    "00_raw_initial": 0.0,
    "01_center_droplet_first": 2.0,
    "02_first_ring_impulse": 11.0,
    "03_second_ring_impulse": 22.0,
    "04_secondary_first_ring_overlap": 52.0,
    "05_peak_overlap_field": PEAK_TIME_SECONDS,
    "06_fade_to_reset": 76.0,
}

RGB_DEEP = np.array([0, 6, 9], dtype=np.float32)
RGB_DARK = np.array([3, 18, 24], dtype=np.float32)
RGB_TEAL = np.array([30, 116, 124], dtype=np.float32)
RGB_ICE = np.array([150, 226, 234], dtype=np.float32)
RGB_CREAM = np.array([238, 231, 199], dtype=np.float32)
RGB_GOLD = np.array([242, 188, 78], dtype=np.float32)
RGB_SALMON = np.array([216, 82, 58], dtype=np.float32)
RGB_RED = np.array([150, 38, 31], dtype=np.float32)
RGB_MUTED = np.array([95, 139, 139], dtype=np.float32)
RGB_LABEL = np.array([225, 234, 230], dtype=np.float32)


@dataclass(frozen=True)
class SimConfig:
    sim_width: int
    sim_height: int
    output_width: int
    output_height: int
    fps: int
    duration_seconds: float
    frame_count: int
    wave_speed_cells_per_frame: float
    damping: float
    edge_absorb_px: float
    source_spacing_cells: float
    impulse_sigma_cells: float
    impulse_velocity_bias: float
    contributor_band_sigma_cells: float
    contributor_band_growth_cells_per_second: float
    contributor_max_age_seconds: float
    ridge_threshold_floor: float
    ridge_threshold_std_factor: float
    fade_reset_start_seconds: float
    note: str


@dataclass(frozen=True)
class SourcePoint:
    source_id: str
    ring_index: int
    q: int
    r: int
    x: float
    y: float


@dataclass(frozen=True)
class ImpulseEvent:
    event_id: str
    source_id: str
    source_index: int
    group: str
    time_seconds: float
    frame_index: int
    amplitude: float
    repeat_index: int


@dataclass
class FrameMaps:
    frame_index: int
    time_seconds: float
    height: np.ndarray
    feature: np.ndarray
    ridge: np.ndarray
    contributor_count: np.ndarray
    contributor_energy: np.ndarray
    circle_mask: np.ndarray
    crescent_mask: np.ndarray
    trigon_mask: np.ndarray
    union_mask: np.ndarray
    active_event_ids: list[str]
    threshold: float
    fade: float


class FfmpegWriter:
    def __init__(
        self,
        path: Path,
        *,
        input_size: tuple[int, int],
        output_size: tuple[int, int],
        fps: int,
        software_codec: bool = False,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = input_size
        out_width, out_height = output_size
        if software_codec:
            codec_args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17"]
        else:
            codec_args = ["-c:v", "h264_videotoolbox", "-b:v", "42M", "-maxrate", "60M", "-bufsize", "84M"]

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
            "-vf",
            f"scale={out_width}:{out_height}:flags=lanczos,format=yuv420p",
            *codec_args,
            "-tag:v",
            "avc1",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.path = path
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, frame_rgb: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin is closed")
        self.proc.stdin.write(np.ascontiguousarray(frame_rgb).tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        stderr = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with code {code}\n{stderr[-4000:]}")


def smoothstep(edge0: float, edge1: float, value: np.ndarray | float) -> np.ndarray | float:
    if edge0 == edge1:
        return np.where(np.asarray(value) >= edge1, 1.0, 0.0)
    t = np.clip((np.asarray(value) - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def frame_for_time(time_seconds: float) -> int:
    return max(0, min(FRAME_COUNT - 1, int(round(time_seconds * FPS))))


def to_uint8(rgb: np.ndarray) -> np.ndarray:
    return np.clip(rgb, 0.0, 255.0).astype(np.uint8)


def resize_rgb(rgb: np.ndarray, size: tuple[int, int], *, nearest: bool = False) -> np.ndarray:
    resample = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS
    return np.asarray(Image.fromarray(to_uint8(rgb), mode="RGB").resize(size, resample))


def mix(base: np.ndarray, color: np.ndarray, alpha: np.ndarray | float) -> np.ndarray:
    if isinstance(alpha, np.ndarray):
        a = alpha[..., None].astype(np.float32)
    else:
        a = float(alpha)
    return base * (1.0 - a) + color.astype(np.float32) * a


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_label(image: Image.Image, text: str, xy: tuple[int, int] = (18, 16), size: int = 24) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    fnt = font(size)
    bbox = draw.textbbox(xy, text, font=fnt)
    pad = 9
    draw.rounded_rectangle(
        (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
        radius=6,
        fill=(0, 8, 10, 178),
    )
    draw.text(xy, text, fill=(226, 234, 230, 255), font=fnt)


def label_panel(rgb: np.ndarray, label: str, size: tuple[int, int]) -> Image.Image:
    panel = Image.fromarray(resize_rgb(rgb, size), mode="RGB")
    draw_label(panel, label, size=max(18, size[1] // 25))
    return panel


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mad(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


class WaveEquationOverlapStudy:
    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.w = config.sim_width
        self.h = config.sim_height
        self.cx = (self.w - 1) * 0.5
        self.cy = (self.h - 1) * 0.5

        yy, xx = np.mgrid[0 : self.h, 0 : self.w].astype(np.float32)
        self.x = xx
        self.y = yy
        self.sources = self._make_sources()
        self.dist_maps = self._make_dist_maps()
        self.kernels = self._make_impulse_kernels()
        self.events = self._make_impulse_events()
        self.events_by_frame = self._make_events_by_frame()

        edge_dist = np.minimum.reduce([xx, self.w - 1 - xx, yy, self.h - 1 - yy])
        self.edge_window = smoothstep(0.0, config.edge_absorb_px, edge_dist).astype(np.float32)
        radial = np.sqrt(((xx - self.cx) / (self.w * 0.5)) ** 2 + ((yy - self.cy) / (self.h * 0.5)) ** 2)
        self.vignette = np.clip(1.0 - 0.62 * radial, 0.0, 1.0).astype(np.float32)
        self.texture = (
            0.5
            + 0.18 * np.sin(xx * 0.037 + yy * 0.019)
            + 0.12 * np.sin(xx * -0.015 + yy * 0.051 + 1.1)
        ).astype(np.float32)

        self.previous = np.zeros((self.h, self.w), dtype=np.float32)
        self.current = np.zeros((self.h, self.w), dtype=np.float32)

    def _make_sources(self) -> list[SourcePoint]:
        coords: list[tuple[int, int]] = []
        radius = 2
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                if max(abs(q), abs(r), abs(q + r)) <= radius:
                    coords.append((q, r))

        def ring_index(q: int, r: int) -> int:
            return max(abs(q), abs(r), abs(q + r))

        def angle(q: int, r: int) -> float:
            spacing = self.config.source_spacing_cells
            x = spacing * (q + 0.5 * r)
            y = spacing * (math.sqrt(3.0) * 0.5 * r)
            return math.atan2(y, x)

        coords.sort(key=lambda qr: (ring_index(*qr), angle(*qr)))
        sources: list[SourcePoint] = []
        counts = {0: 0, 1: 0, 2: 0}
        for q, r in coords:
            ring = ring_index(q, r)
            counts[ring] += 1
            spacing = self.config.source_spacing_cells
            x = self.cx + spacing * (q + 0.5 * r)
            y = self.cy + spacing * (math.sqrt(3.0) * 0.5 * r)
            if ring == 0:
                source_id = "center_00"
            elif ring == 1:
                source_id = f"ring1_{counts[ring]:02d}"
            else:
                source_id = f"ring2_{counts[ring]:02d}"
            sources.append(SourcePoint(source_id=source_id, ring_index=ring, q=q, r=r, x=x, y=y))
        if len(sources) != 19:
            raise RuntimeError(f"expected 19 source points, got {len(sources)}")
        return sources

    def _make_dist_maps(self) -> np.ndarray:
        maps = []
        for source in self.sources:
            maps.append(np.sqrt((self.x - source.x) ** 2 + (self.y - source.y) ** 2).astype(np.float32))
        return np.stack(maps, axis=0)

    def _make_impulse_kernels(self) -> np.ndarray:
        sigma = self.config.impulse_sigma_cells
        kernels = np.exp(-(self.dist_maps**2) / (2.0 * sigma * sigma)).astype(np.float32)
        return kernels

    def _make_impulse_events(self) -> list[ImpulseEvent]:
        group_times = [
            (0, "center", 2.0, 1.00),
            (0, "first_ring", 11.0, 0.82),
            (0, "second_ring", 22.0, 0.72),
            (1, "center", 42.0, 0.78),
            (1, "first_ring", 50.0, 0.64),
            (1, "second_ring", 58.5, 0.60),
        ]
        events: list[ImpulseEvent] = []
        for repeat_index, group, time_seconds, amplitude in group_times:
            for idx, source in enumerate(self.sources):
                if group == "center" and source.ring_index != 0:
                    continue
                if group == "first_ring" and source.ring_index != 1:
                    continue
                if group == "second_ring" and source.ring_index != 2:
                    continue
                event_id = f"r{repeat_index}_{group}_{source.source_id}"
                events.append(
                    ImpulseEvent(
                        event_id=event_id,
                        source_id=source.source_id,
                        source_index=idx,
                        group=group,
                        time_seconds=time_seconds,
                        frame_index=frame_for_time(time_seconds),
                        amplitude=amplitude,
                        repeat_index=repeat_index,
                    )
                )
        return events

    def _make_events_by_frame(self) -> dict[int, list[ImpulseEvent]]:
        by_frame: dict[int, list[ImpulseEvent]] = {}
        for event in self.events:
            by_frame.setdefault(event.frame_index, []).append(event)
        return by_frame

    def apply_impulses(self, frame_index: int) -> None:
        for event in self.events_by_frame.get(frame_index, []):
            kernel = self.kernels[event.source_index]
            self.current += event.amplitude * kernel
            self.previous -= event.amplitude * self.config.impulse_velocity_bias * kernel

    def advance(self) -> None:
        c2 = self.config.wave_speed_cells_per_frame**2
        lap = np.zeros_like(self.current)
        lap[1:-1, 1:-1] = (
            self.current[1:-1, 0:-2]
            + self.current[1:-1, 2:]
            + self.current[0:-2, 1:-1]
            + self.current[2:, 1:-1]
            - 4.0 * self.current[1:-1, 1:-1]
        )
        nxt = (
            (2.0 - self.config.damping) * self.current
            - (1.0 - self.config.damping) * self.previous
            + c2 * lap
        )
        nxt *= self.edge_window
        self.previous = self.current * self.edge_window
        self.current = nxt.astype(np.float32)

    def visual_fade(self, time_seconds: float) -> float:
        fade_out = smoothstep(FADE_RESET_START_SECONDS, self.config.duration_seconds - 0.3, time_seconds)
        return float(1.0 - fade_out)

    def contributor_maps(self, frame_index: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
        count = np.zeros((self.h, self.w), dtype=np.uint8)
        energy = np.zeros((self.h, self.w), dtype=np.float32)
        active: list[str] = []
        max_age_frames = int(self.config.contributor_max_age_seconds * self.config.fps)
        for event in self.events:
            age_frames = frame_index - event.frame_index
            if age_frames < 0 or age_frames > max_age_frames:
                continue
            active.append(event.event_id)
            age_seconds = age_frames / self.config.fps
            radius = self.config.wave_speed_cells_per_frame * age_frames
            sigma = (
                self.config.contributor_band_sigma_cells
                + self.config.contributor_band_growth_cells_per_second * age_seconds
            )
            band_width = sigma * 1.55
            source = self.sources[event.source_index]
            reach = radius + band_width + 1.0
            x0 = max(0, int(math.floor(source.x - reach)))
            x1 = min(self.w, int(math.ceil(source.x + reach + 1.0)))
            y0 = max(0, int(math.floor(source.y - reach)))
            y1 = min(self.h, int(math.ceil(source.y + reach + 1.0)))
            if x0 >= x1 or y0 >= y1:
                continue
            dist = self.dist_maps[event.source_index, y0:y1, x0:x1]
            band = np.abs(dist - radius)
            mask = band <= band_width
            if not np.any(mask):
                continue
            decay = event.amplitude * math.exp(-age_seconds / 19.0)
            count_view = count[y0:y1, x0:x1]
            energy_view = energy[y0:y1, x0:x1]
            count_view[mask] = np.minimum(count_view[mask] + 1, 15)
            energy_view[mask] += (1.0 - band[mask] / band_width) * decay
        return count, energy, active

    def compute_maps(self, frame_index: int) -> FrameMaps:
        time_seconds = frame_index / self.config.fps
        fade = self.visual_fade(time_seconds)
        height = self.current.copy()
        height *= fade

        abs_h = np.abs(height)
        rms = float(np.sqrt(np.mean(height * height))) if np.any(abs_h) else 0.0
        scale_h = max(1e-5, rms * 2.8)
        abs_n = np.clip(abs_h / scale_h, 0.0, 1.0)

        gx = np.zeros_like(height)
        gy = np.zeros_like(height)
        gx[:, 1:-1] = 0.5 * (height[:, 2:] - height[:, :-2])
        gy[1:-1, :] = 0.5 * (height[2:, :] - height[:-2, :])
        grad = np.sqrt(gx * gx + gy * gy)
        grad_rms = float(np.sqrt(np.mean(grad * grad))) if np.any(grad) else 0.0
        grad_n = np.clip(grad / max(1e-5, grad_rms * 3.2), 0.0, 1.0)

        feature = (0.57 * abs_n + 0.43 * grad_n).astype(np.float32)
        threshold = max(
            self.config.ridge_threshold_floor,
            float(feature.mean() + self.config.ridge_threshold_std_factor * feature.std()),
        )
        ridge = feature > threshold

        count, energy, active = self.contributor_maps(frame_index)
        field_ridge = ridge & (count > 0) & (energy > 0.24)
        circle_mask = field_ridge & (count == 1)
        crescent_mask = field_ridge & (count == 2)
        trigon_mask = field_ridge & (count >= 3)
        union_mask = circle_mask | crescent_mask | trigon_mask

        return FrameMaps(
            frame_index=frame_index,
            time_seconds=time_seconds,
            height=height,
            feature=feature,
            ridge=ridge,
            contributor_count=count,
            contributor_energy=energy,
            circle_mask=circle_mask,
            crescent_mask=crescent_mask,
            trigon_mask=trigon_mask,
            union_mask=union_mask,
            active_event_ids=active,
            threshold=threshold,
            fade=fade,
        )

    def raw_height_rgb(self, maps: FrameMaps) -> np.ndarray:
        height = maps.height
        rms = max(1e-5, float(np.sqrt(np.mean(height * height))) * 2.4)
        signed = np.tanh(height / rms)
        pos = np.clip(signed, 0.0, 1.0)
        neg = np.clip(-signed, 0.0, 1.0)
        gx = np.zeros_like(height)
        gy = np.zeros_like(height)
        gx[:, 1:-1] = 0.5 * (height[:, 2:] - height[:, :-2])
        gy[1:-1, :] = 0.5 * (height[2:, :] - height[:-2, :])
        light = np.clip(0.52 + 1.75 * (-0.45 * gx - 0.30 * gy), 0.0, 1.0)
        base = mix(RGB_DEEP + 11.0 * self.vignette[..., None], RGB_DARK, 0.64)
        base += (self.texture[..., None] - 0.5) * 10.0
        rgb = base
        rgb = mix(rgb, RGB_TEAL, 0.14 + 0.23 * self.vignette)
        rgb = mix(rgb, RGB_ICE, pos * 0.50 * maps.fade)
        rgb = mix(rgb, RGB_TEAL * 0.42, neg * 0.38 * maps.fade)
        rgb += (light[..., None] - 0.52) * 42.0 * maps.fade
        return to_uint8(rgb)

    def feature_rgb(self, maps: FrameMaps) -> np.ndarray:
        f = maps.feature
        rgb = np.zeros((self.h, self.w, 3), dtype=np.float32)
        rgb += RGB_DEEP * 0.55
        rgb = mix(rgb, RGB_TEAL, np.clip(f * 0.45, 0.0, 1.0))
        rgb = mix(rgb, RGB_ICE, np.clip((f - 0.38) / 0.62, 0.0, 1.0) * 0.68)
        rgb[maps.ridge] = mix(rgb[maps.ridge], RGB_CREAM, np.clip(f[maps.ridge] * 0.72, 0.0, 1.0))
        return to_uint8(rgb)

    def count_rgb(self, maps: FrameMaps, *, ridged_only: bool) -> np.ndarray:
        rgb = np.zeros((self.h, self.w, 3), dtype=np.float32)
        rgb += RGB_DEEP * 0.52
        if ridged_only:
            c1 = maps.circle_mask
            c2 = maps.crescent_mask
            c3 = maps.trigon_mask
            strength = np.clip(maps.feature * 0.95 + maps.contributor_energy * 0.18, 0.0, 1.0)
        else:
            c1 = maps.contributor_count == 1
            c2 = maps.contributor_count == 2
            c3 = maps.contributor_count >= 3
            max_energy = max(1e-5, float(np.percentile(maps.contributor_energy, 99.2)))
            strength = np.clip(maps.contributor_energy / max_energy, 0.0, 1.0)
        rgb[c1] = mix(rgb[c1], RGB_CREAM, np.clip(strength[c1] * 0.84, 0.0, 1.0))
        rgb[c2] = mix(rgb[c2], RGB_ICE, np.clip(strength[c2] * 0.91, 0.0, 1.0))
        rgb[c3] = mix(rgb[c3], RGB_SALMON, np.clip(strength[c3] * 0.92, 0.0, 1.0))
        hot = maps.contributor_count >= 5
        if np.any(hot) and not ridged_only:
            rgb[hot] = mix(rgb[hot], RGB_GOLD, 0.42)
        return to_uint8(rgb)

    def mask_rgb(self, maps: FrameMaps) -> np.ndarray:
        rgb = np.zeros((self.h, self.w, 3), dtype=np.float32)
        rgb += RGB_DEEP * 0.50
        strength = np.clip(0.35 + 0.75 * maps.feature, 0.0, 1.0)
        rgb[maps.circle_mask] = mix(rgb[maps.circle_mask], RGB_CREAM, strength[maps.circle_mask])
        rgb[maps.crescent_mask] = mix(rgb[maps.crescent_mask], RGB_ICE, strength[maps.crescent_mask])
        rgb[maps.trigon_mask] = mix(rgb[maps.trigon_mask], RGB_SALMON, strength[maps.trigon_mask])
        return to_uint8(rgb)

    def final_rgb(self, maps: FrameMaps) -> np.ndarray:
        rgb = self.raw_height_rgb(maps).astype(np.float32)
        rgb = mix(rgb, RGB_DARK, 0.24)
        strength = np.clip(0.26 + maps.feature * 0.78 + maps.contributor_energy * 0.08, 0.0, 1.0)
        alpha = np.clip(strength * maps.fade, 0.0, 1.0)

        c = maps.circle_mask
        if np.any(c):
            rgb[c] = mix(rgb[c], RGB_CREAM * 0.80 + RGB_GOLD * 0.20, alpha[c] * 0.78)
        c = maps.crescent_mask
        if np.any(c):
            rgb[c] = mix(rgb[c], RGB_ICE, alpha[c] * 0.84)
        c = maps.trigon_mask
        if np.any(c):
            trigon_color = RGB_SALMON * 0.78 + RGB_GOLD * 0.22
            rgb[c] = mix(rgb[c], trigon_color, alpha[c] * 0.88)

        union = maps.union_mask
        if np.any(union):
            rgb[union] = mix(rgb[union], RGB_CREAM, np.clip((maps.contributor_count[union] - 2) * 0.08, 0.0, 0.22))
        return to_uint8(rgb)

    def timeline_rgb(self, frame_index: int, size: tuple[int, int] = (1280, 720)) -> np.ndarray:
        width, height = size
        image = Image.new("RGB", size, (2, 10, 13))
        draw = ImageDraw.Draw(image, "RGBA")
        margin_x = 92
        right = width - 52
        top = 78
        row_h = 58
        lane_info = [
            ("center", "center", (238, 231, 199, 255)),
            ("first_ring", "first ring", (150, 226, 234, 255)),
            ("second_ring", "second ring", (216, 82, 58, 255)),
        ]
        fnt = font(24)
        small = font(18)

        draw.text((38, 24), "active impulse/source timeline", fill=(226, 234, 230, 255), font=font(30))
        draw.text(
            (38, 54),
            "bars show tracked wavefront contributor windows; vertical line is the captured frame",
            fill=(154, 178, 177, 255),
            font=small,
        )
        for tick in range(0, int(self.config.duration_seconds) + 1, 10):
            x = margin_x + (right - margin_x) * tick / self.config.duration_seconds
            draw.line((x, top - 18, x, top + row_h * 3 + 18), fill=(58, 86, 88, 140), width=1)
            draw.text((x - 12, top + row_h * 3 + 26), f"{tick}s", fill=(156, 178, 177, 255), font=small)

        max_age = self.config.contributor_max_age_seconds
        for lane_idx, (group, label, color) in enumerate(lane_info):
            y = top + lane_idx * row_h
            draw.text((34, y + 10), label, fill=(219, 228, 224, 255), font=fnt)
            draw.line((margin_x, y + 28, right, y + 28), fill=(74, 101, 100, 150), width=2)
            for event in [e for e in self.events if e.group == group]:
                x0 = margin_x + (right - margin_x) * event.time_seconds / self.config.duration_seconds
                x1 = margin_x + (right - margin_x) * min(
                    self.config.duration_seconds, event.time_seconds + max_age
                ) / self.config.duration_seconds
                draw.rounded_rectangle((x0, y + 17, x1, y + 39), radius=4, fill=(*color[:3], 42))
                draw.line((x0, y + 11, x0, y + 45), fill=color, width=3)

        now = frame_index / self.config.fps
        x_now = margin_x + (right - margin_x) * now / self.config.duration_seconds
        draw.line((x_now, top - 38, x_now, top + row_h * 3 + 48), fill=(245, 196, 90, 255), width=3)
        draw.text((x_now + 8, top - 40), f"{now:05.2f}s", fill=(245, 196, 90, 255), font=fnt)

        y0 = height - 250
        draw.text((38, y0), "impact positions", fill=(226, 234, 230, 255), font=font(26))
        draw.text(
            (38, y0 + 32),
            "center + 6 first-ring + 12 second-ring droplets on the radius-2 hex lattice",
            fill=(154, 178, 177, 255),
            font=small,
        )
        map_x0, map_y0 = 740, y0 - 8
        map_w, map_h = 430, 210
        draw.rectangle((map_x0, map_y0, map_x0 + map_w, map_y0 + map_h), outline=(72, 101, 101, 180), width=1)
        for source in self.sources:
            sx = map_x0 + map_w * (source.x / self.w)
            sy = map_y0 + map_h * (source.y / self.h)
            if source.ring_index == 0:
                color = (238, 231, 199, 255)
                r = 7
            elif source.ring_index == 1:
                color = (150, 226, 234, 255)
                r = 5
            else:
                color = (216, 82, 58, 255)
                r = 4
            draw.ellipse((sx - r, sy - r, sx + r, sy + r), fill=color)
        return np.asarray(image)


def default_config() -> SimConfig:
    return SimConfig(
        sim_width=SIM_SIZE[0],
        sim_height=SIM_SIZE[1],
        output_width=UHD_SIZE[0],
        output_height=UHD_SIZE[1],
        fps=FPS,
        duration_seconds=DURATION_SECONDS,
        frame_count=FRAME_COUNT,
        wave_speed_cells_per_frame=0.48,
        damping=0.0135,
        edge_absorb_px=22.0,
        source_spacing_cells=35.5,
        impulse_sigma_cells=1.75,
        impulse_velocity_bias=0.62,
        contributor_band_sigma_cells=1.95,
        contributor_band_growth_cells_per_second=0.016,
        contributor_max_age_seconds=22.0,
        ridge_threshold_floor=0.44,
        ridge_threshold_std_factor=1.05,
        fade_reset_start_seconds=FADE_RESET_START_SECONDS,
        note="Simulation is computed on a 384x216 heightfield and scaled to 3840x2160 at encode time.",
    )


def component_stats(mask: np.ndarray) -> dict[str, Any]:
    try:
        from scipy import ndimage as ndi  # type: ignore

        labels, count = ndi.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
        if count == 0:
            return {"component_count": 0, "area_px": 0, "largest_components_px": []}
        areas = np.bincount(labels.ravel())[1:]
        largest = sorted([int(v) for v in areas], reverse=True)[:12]
        return {
            "component_count": int(count),
            "area_px": int(mask.sum()),
            "largest_components_px": largest,
            "mean_component_area_px": round(float(np.mean(areas)), 4),
        }
    except Exception:
        return {"component_count": None, "area_px": int(mask.sum()), "largest_components_px": []}


def frame_stats(maps: FrameMaps) -> dict[str, Any]:
    total = maps.union_mask.size
    return {
        "frame_index": maps.frame_index,
        "time_seconds": round(maps.time_seconds, 4),
        "active_event_count": len(maps.active_event_ids),
        "active_event_ids": maps.active_event_ids,
        "ridge_threshold": round(float(maps.threshold), 6),
        "ridge_pixels": int(maps.ridge.sum()),
        "circle_mask_pixels": int(maps.circle_mask.sum()),
        "crescent_mask_pixels": int(maps.crescent_mask.sum()),
        "trigon_mask_pixels": int(maps.trigon_mask.sum()),
        "union_mask_pixels": int(maps.union_mask.sum()),
        "union_mask_fraction": round(float(maps.union_mask.sum() / total), 6),
        "max_contributor_count": int(maps.contributor_count.max()),
        "mean_contributor_count_on_union": round(float(maps.contributor_count[maps.union_mask].mean()), 4)
        if np.any(maps.union_mask)
        else 0.0,
        "circle_components": component_stats(maps.circle_mask),
        "crescent_components": component_stats(maps.crescent_mask),
        "trigon_components": component_stats(maps.trigon_mask),
    }


def capture_views(study: WaveEquationOverlapStudy, maps: FrameMaps, final: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "raw_heightfield": study.raw_height_rgb(maps),
        "active_impulse_timeline": study.timeline_rgb(maps.frame_index, size=(1280, 720)),
        "ridge_feature_map": study.feature_rgb(maps),
        "overlap_count_map": study.count_rgb(maps, ridged_only=False),
        "detected_masks": study.mask_rgb(maps),
        "count_feature_only": study.count_rgb(maps, ridged_only=True),
        "final_render": final,
    }


def run_simulation(render_video: bool, software_codec: bool) -> dict[str, Any]:
    config = default_config()
    study = WaveEquationOverlapStudy(config)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    capture_frames: dict[int, list[str]] = {}
    for label, t in KEY_STILLS.items():
        capture_frames.setdefault(frame_for_time(t), []).append(f"key:{label}")
    for idx, t in enumerate(CONTACT_TIMES):
        capture_frames.setdefault(frame_for_time(t), []).append(f"contact:{idx:02d}_{t:05.1f}s")
    capture_frames.setdefault(PEAK_FRAME, []).append("peak")
    capture_frames.setdefault(0, []).append("loop:first")
    capture_frames.setdefault(FRAME_COUNT - 1, []).append("loop:last")
    capture_frames.setdefault(1, []).append("loop:second")
    capture_frames.setdefault(FRAME_COUNT - 2, []).append("loop:prelast")

    writer = None
    mp4_path = OUT_DIR / f"{PROJECT}.mp4"
    if render_video:
        writer = FfmpegWriter(
            mp4_path,
            input_size=(config.sim_width, config.sim_height),
            output_size=(config.output_width, config.output_height),
            fps=config.fps,
            software_codec=software_codec,
        )

    captures: dict[str, dict[str, Any]] = {}
    loop_frames: dict[str, np.ndarray] = {}
    for frame_index in range(config.frame_count):
        study.apply_impulses(frame_index)
        maps = study.compute_maps(frame_index)
        final = study.final_rgb(maps)
        if writer is not None:
            writer.write(final)
        if frame_index in capture_frames:
            views = capture_views(study, maps, final)
            stats = frame_stats(maps)
            for request in capture_frames[frame_index]:
                if request.startswith("loop:"):
                    loop_frames[request.split(":", 1)[1]] = final.copy()
                else:
                    captures[request] = {"views": views, "stats": stats}
        study.advance()
        if frame_index % (config.fps * 10) == 0 and frame_index > 0:
            print(f"Simulated {frame_index // config.fps:02d}s / {int(config.duration_seconds)}s", flush=True)

    if writer is not None:
        writer.close()

    loop_diagnostics = {
        "loop_type": "one-shot PDE study with visual fade-to-reset; not true PDE state closure",
        "raw_visual_frame0_final_mean_abs_diff": round(mad(loop_frames["first"], loop_frames["last"]), 6),
        "raw_visual_frame0_frame1_mean_abs_diff": round(mad(loop_frames["first"], loop_frames["second"]), 6),
        "raw_visual_prelast_final_mean_abs_diff": round(mad(loop_frames["prelast"], loop_frames["last"]), 6),
        "fade_reset_start_seconds": FADE_RESET_START_SECONDS,
        "true_pde_loop_closure_claimed": False,
    }
    return {
        "config": config,
        "study": study,
        "captures": captures,
        "loop_diagnostics": loop_diagnostics,
        "mp4_path": mp4_path if render_video else None,
        "render_video": render_video,
    }


def save_png(path: Path, rgb: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(to_uint8(rgb), mode="RGB").save(path)


def write_stills(captures: dict[str, dict[str, Any]]) -> dict[str, str]:
    written: dict[str, str] = {}
    for label in KEY_STILLS:
        key = f"key:{label}"
        if key not in captures:
            continue
        frame = captures[key]["views"]["final_render"]
        path = STILLS_DIR / f"{PROJECT}_{label}.png"
        save_png(path, resize_rgb(frame, (1920, 1080)))
        written[label] = str(path.relative_to(OUT_DIR))
    return written


def make_contact_sheet(captures: dict[str, dict[str, Any]]) -> Path:
    cell = (768, 432)
    sheet = Image.new("RGB", (cell[0] * 5, cell[1] * 4), (0, 6, 9))
    for idx, t in enumerate(CONTACT_TIMES):
        key = f"contact:{idx:02d}_{t:05.1f}s"
        if key not in captures:
            continue
        panel = label_panel(captures[key]["views"]["final_render"], f"{t:05.1f}s", cell)
        x = (idx % 5) * cell[0]
        y = (idx // 5) * cell[1]
        sheet.paste(panel, (x, y))
    draw = ImageDraw.Draw(sheet, "RGBA")
    draw.rectangle((0, sheet.height - 54, sheet.width, sheet.height), fill=(0, 8, 10, 192))
    draw.text(
        (24, sheet.height - 42),
        f"{PROJECT} contact sheet | final render frames | masks are field-derived, no primitive overlay layer",
        fill=(226, 234, 230, 255),
        font=font(28),
    )
    path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    sheet.save(path)
    return path


def make_debug_sheets(captures: dict[str, dict[str, Any]]) -> dict[str, str]:
    peak = captures["peak"]["views"]
    peak_stats = captures["peak"]["stats"]

    debug_files: dict[str, str] = {}
    for name in (
        "raw_heightfield",
        "active_impulse_timeline",
        "ridge_feature_map",
        "overlap_count_map",
        "detected_masks",
        "count_feature_only",
        "final_render",
    ):
        path = DEBUG_DIR / f"{PROJECT}_{name}_peak.png"
        image = peak[name]
        if name == "active_impulse_timeline":
            save_png(path, image)
        else:
            save_png(path, resize_rgb(image, (1920, 1080), nearest=name in {"detected_masks", "count_feature_only"}))
        debug_files[name] = str(path.relative_to(OUT_DIR))

    sheet_cell = (1280, 720)
    panels = [
        ("1 raw heightfield view", peak["raw_heightfield"]),
        ("2 active impulse/source timeline", peak["active_impulse_timeline"]),
        ("3 ridge/feature map", peak["ridge_feature_map"]),
        ("4 overlap/contributor count map", peak["overlap_count_map"]),
        ("5 detected circle/crescent/trigon masks", peak["detected_masks"]),
        ("6 final render from the same masks", peak["final_render"]),
    ]
    sheet = Image.new("RGB", (sheet_cell[0] * 3, sheet_cell[1] * 2), (0, 6, 9))
    for idx, (label, rgb) in enumerate(panels):
        nearest = label.startswith("5")
        panel = label_panel(rgb, label, sheet_cell)
        if nearest:
            panel = label_panel(resize_rgb(rgb, sheet_cell, nearest=True), label, sheet_cell)
        sheet.paste(panel, ((idx % 3) * sheet_cell[0], (idx // 3) * sheet_cell[1]))
    path = DEBUG_DIR / f"{PROJECT}_debug_verification_sheet.png"
    sheet.save(path)
    debug_files["debug_verification_sheet"] = str(path.relative_to(OUT_DIR))

    compare = Image.new("RGB", (3840, 1080), (0, 6, 9))
    left = label_panel(peak["count_feature_only"], "field-derived count/feature mask only", (1920, 1080))
    right = label_panel(peak["final_render"], "final peak render using the identical mask pixels", (1920, 1080))
    compare.paste(left, (0, 0))
    compare.paste(right, (1920, 0))
    path = DEBUG_DIR / f"{PROJECT}_no_primitive_overlay_comparison.png"
    compare.save(path)
    debug_files["no_primitive_overlay_comparison"] = str(path.relative_to(OUT_DIR))

    stats_path = DEBUG_DIR / f"{PROJECT}_peak_mask_stats.json"
    stats_path.write_text(json.dumps(peak_stats, indent=2) + "\n", encoding="utf-8")
    debug_files["peak_mask_stats"] = str(stats_path.relative_to(OUT_DIR))
    return debug_files


def write_manifest(
    result: dict[str, Any],
    stills: dict[str, str],
    contact_sheet: Path,
    debug_files: dict[str, str],
) -> Path:
    config: SimConfig = result["config"]
    study: WaveEquationOverlapStudy = result["study"]
    captures: dict[str, dict[str, Any]] = result["captures"]
    peak_stats = captures["peak"]["stats"]
    script_path = ROOT / "scripts" / f"{PROJECT}.py"
    manifest = {
        "project": PROJECT,
        "status": "austin_authorized_internal_show_development_prototype",
        "boundary": {
            "austin_greenlit_generated_experiments": True,
            "austin_source_artwork_used": False,
            "source_artworks_used": False,
            "cultural_authority_claimed": False,
            "framing": "Water-wave geometry that may resonate with and help contextualize primitive forms Austin is working with; not a claim of cultural meaning.",
        },
        "renderer": str(script_path.relative_to(ROOT)),
        "renderer_sha256": sha256(script_path),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [config.output_width, config.output_height],
        "simulation_grid": [config.sim_width, config.sim_height],
        "fps": config.fps,
        "duration_seconds": config.duration_seconds,
        "frame_count": config.frame_count,
        "physical_model": {
            "equation": "2D damped finite-difference heightfield wave equation with 4-neighbor Laplacian",
            "wave_speed_cells_per_frame": config.wave_speed_cells_per_frame,
            "damping": config.damping,
            "edge_absorb_px": config.edge_absorb_px,
            "impulse_sigma_cells": config.impulse_sigma_cells,
            "impulse_velocity_bias": config.impulse_velocity_bias,
            "work_canvas_note": config.note,
        },
        "source_positions": [
            {
                **asdict(source),
                "x_norm": round(source.x / config.sim_width, 6),
                "y_norm": round(source.y / config.sim_height, 6),
            }
            for source in study.sources
        ],
        "impact_sequence": [asdict(event) for event in study.events],
        "detection": {
            "feature_map": "0.57 * normalized absolute height + 0.43 * normalized gradient magnitude",
            "ridge_threshold": "max(ridge_threshold_floor, mean(feature) + ridge_threshold_std_factor * std(feature))",
            "ridge_threshold_floor": config.ridge_threshold_floor,
            "ridge_threshold_std_factor": config.ridge_threshold_std_factor,
            "contributor_count": "tracked active wavefront bands from impulse source, age, and wave speed; intersected with the PDE ridge mask",
            "contributor_band_sigma_cells": config.contributor_band_sigma_cells,
            "contributor_band_growth_cells_per_second": config.contributor_band_growth_cells_per_second,
            "contributor_max_age_seconds": config.contributor_max_age_seconds,
            "circle_family_rule": "ridge pixels with exactly one tracked wavefront contributor",
            "crescent_family_rule": "ridge pixels with exactly two tracked wavefront contributors",
            "trigon_family_rule": "ridge pixels with three or more tracked wavefront contributors",
            "no_primitive_overlay_contract": "The final render colors exactly these masks. No independent circle, crescent, trigon, icon, path, SVG, or symbolic layer is drawn.",
        },
        "peak_diagnostics": peak_stats,
        "loop": result["loop_diagnostics"],
        "deliverables": {
            "mp4": f"{PROJECT}.mp4" if result["render_video"] else None,
            "contact_sheet": str(contact_sheet.relative_to(OUT_DIR)),
            "debug_files": debug_files,
            "stills": stills,
            "readme": "README.md",
            "manifest": f"{PROJECT}_manifest.json",
        },
        "honest_verdict": {
            "no_primitive_overlay_contract": "PASS",
            "primitive_emergence_read": "MIXED_PROMISING",
            "reason": "The circle and two-wavefront overlap families are legible as field ridges. The three-plus contributor zones are real and mask-derived, but many read as high-energy nodes rather than clean authored trigons.",
        },
    }
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(result: dict[str, Any], contact_sheet: Path, debug_files: dict[str, str]) -> Path:
    config: SimConfig = result["config"]
    captures: dict[str, dict[str, Any]] = result["captures"]
    peak_stats = captures["peak"]["stats"]
    loop = result["loop_diagnostics"]
    mp4_line = f"- `{PROJECT}.mp4`: 3840x2160, 24fps, {DURATION_SECONDS:.0f}s." if result["render_video"] else "- MP4 was skipped in preview mode."
    readme = f"""# Abstract Cymatic Wave-Equation Overlap Path B v001

Status: Austin-authorized internal/show-development prototype. Austin has
greenlit Austin-style / Coast Salish-style generated experiments for this
project. This render uses no Austin source artwork. It should be framed as
water-wave geometry that resonates with, and may help contextualize, primitive
forms Austin is working with. It does not claim authority over cultural meaning.

## Purpose

This pass tests primitive emergence with a real 2D damped wave-equation
heightfield. It deliberately avoids drawn primitive overlays. The only bright
primitive-family emphasis in the final render comes from simulated-field ridge
pixels intersected with tracked wavefront contributor counts.

## Model

- Grid-based water surface: `{config.sim_width}x{config.sim_height}` simulation grid, encoded to 3840x2160.
- Wave equation: damped finite-difference 4-neighbor Laplacian.
- Impact positions: 19 total, center + 6 first-ring + 12 second-ring hex-lattice droplets.
- Impact sequence: center at 2.0s, first ring at 11.0s, second ring at 22.0s; secondary lower-amplitude sequence at 42.0s, 50.0s, and 58.5s.
- Detection: absolute height + gradient magnitude -> ridge mask; contributor count -> circle/crescent/trigon field masks.

## No-Primitive-Overlay Check

The final render uses the same boolean masks shown in
`{debug_files["no_primitive_overlay_comparison"]}`. The left panel is the raw
count/feature mask only; the right panel is the final peak frame. Colored
primitive-family emphasis in the final frame is spatially identical to that
field-derived mask. There are no independent crescent paths, trigon icons,
construction-circle overlays, or symbolic primitive layers.

## Deliverables

{mp4_line}
- `{contact_sheet.relative_to(OUT_DIR)}`.
- `debug/{PROJECT}_debug_verification_sheet.png`.
- `debug/{PROJECT}_no_primitive_overlay_comparison.png`.
- `debug/{PROJECT}_peak_mask_stats.json`.
- `stills/`: key final-render frames.
- `{PROJECT}_manifest.json`.

## Peak Diagnostics

- Peak time: `{PEAK_TIME_SECONDS:.2f}s`.
- Active tracked wavefront events at peak: `{peak_stats["active_event_count"]}`.
- Max contributor count at peak: `{peak_stats["max_contributor_count"]}`.
- Circle-mask pixels: `{peak_stats["circle_mask_pixels"]}`.
- Crescent-mask pixels: `{peak_stats["crescent_mask_pixels"]}`.
- Trigon-mask pixels: `{peak_stats["trigon_mask_pixels"]}`.
- Union mask fraction: `{peak_stats["union_mask_fraction"]}`.

## Loop Status

This is not a true PDE loop. It is a one-shot 80s study with a visual
fade-to-reset from {FADE_RESET_START_SECONDS:.0f}s to the end. I am not claiming
state closure.

- Raw visual frame 0/final MAD: `{loop["raw_visual_frame0_final_mean_abs_diff"]}`.
- Frame 0/frame 1 MAD: `{loop["raw_visual_frame0_frame1_mean_abs_diff"]}`.
- Pre-final/final MAD: `{loop["raw_visual_prelast_final_mean_abs_diff"]}`.

## Honest Verdict

PASS for the no-primitive-overlay contract: final primitive-family emphasis is
field-derived and matches the debug mask. MIXED/PROMISING for primitive
emergence: circles and two-wavefront overlap arcs are readable, while the
three-or-more contributor regions are real high-energy meeting zones but tend
to read as nodes more than clean authored trigons. This is a better physical
test than the prior symbolic flower-of-life overlays, but it is still an
internal R&D result needing Austin/project review before any broader use.

Renderer: `scripts/{PROJECT}.py`
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def ffprobe_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,nb_frames,duration,codec_name",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"exists": True, "ffprobe_error": proc.stderr.strip()}
    return json.loads(proc.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wave-equation overlap path B v001.")
    parser.add_argument("--preview", action="store_true", help="Write stills/debug/docs without the MP4 encode.")
    parser.add_argument("--software-codec", action="store_true", help="Use libx264 instead of h264_videotoolbox.")
    args = parser.parse_args()

    print(f"Running {PROJECT}", flush=True)
    result = run_simulation(render_video=not args.preview, software_codec=args.software_codec)
    print("Writing stills and verification sheets", flush=True)
    stills = write_stills(result["captures"])
    contact_sheet = make_contact_sheet(result["captures"])
    debug_files = make_debug_sheets(result["captures"])
    manifest = write_manifest(result, stills, contact_sheet, debug_files)
    readme = write_readme(result, contact_sheet, debug_files)
    if result["mp4_path"] is not None:
        probe = ffprobe_summary(result["mp4_path"])
        probe_path = DEBUG_DIR / f"{PROJECT}_ffprobe.json"
        probe_path.write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {result['mp4_path']}", flush=True)
        print(f"Wrote {probe_path}", flush=True)
    print(f"Wrote {contact_sheet}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
