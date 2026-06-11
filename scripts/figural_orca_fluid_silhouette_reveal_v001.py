#!/usr/bin/env python3
"""
Figural Orca fluid silhouette reveal v001.

Internal review render for Salish Sea Dreaming.

This probe intentionally does not continue the cymatic aperture approach. The
Orca alpha is used as an invisible obstacle/control field: current lines bend
around the hidden body, boundary pressure and wake accumulation make the whole
silhouette legible, then the complete Austin-authored Orca artwork fades in
uniformly and intact.

Status: AUSTIN-AUTHORIZED INTERNAL / SHOW-DEVELOPMENT PROTOTYPE ONLY.
Austin has greenlit use of the Google Drive artwork and Austin-style /
Coast Salish-style generated experiments for this project. This specific output
still requires Darren/Austin clearance before any public, sponsor, press, or
show-surface use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_orca_fluid_silhouette_reveal_v001"
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / f"{PROJECT}_2026-05-22"
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Water_Orca_Transparent.png"
SOURCE_DIR = OUT_DIR / "source_assets"
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug_stills"

OUT_W = 3840
OUT_H = 2160
RENDER_W = 1920
RENDER_H = 1080
W = RENDER_W
H = RENDER_H
FPS = 24
DURATION_SECONDS = 60.0
FRAME_COUNT = int(FPS * DURATION_SECONDS)
TAU = math.tau

FIELD_W = 960
FIELD_H = 540
FIELD_SCALE_X = W / FIELD_W
FIELD_SCALE_Y = H / FIELD_H

SOURCE_SCALE = 0.88
SOURCE_TOP_LEFT = (896, 122)
RENDER_TO_OUTPUT_SCALE_X = OUT_W / RENDER_W
RENDER_TO_OUTPUT_SCALE_Y = OUT_H / RENDER_H
OUTPUT_TO_RENDER_SCALE_X = RENDER_W / OUT_W
OUTPUT_TO_RENDER_SCALE_Y = RENDER_H / OUT_H
SOURCE_SCALE_RENDER = SOURCE_SCALE * OUTPUT_TO_RENDER_SCALE_X
SOURCE_TOP_LEFT_RENDER = (
    int(round(SOURCE_TOP_LEFT[0] * OUTPUT_TO_RENDER_SCALE_X)),
    int(round(SOURCE_TOP_LEFT[1] * OUTPUT_TO_RENDER_SCALE_Y)),
)
TARGET_ALPHA_CENTER_PX = (1920.0, 1080.0)
BASE_FLOW_VECTOR = (1.0, 0.07)

TIMING = {
    "dark_water_current_enters": [0.0, 8.0],
    "hidden_orca_obstacle_bends_current": [8.0, 22.0],
    "boundary_accumulation_and_wake_build_body": [22.0, 36.0],
    "silhouette_legibility_hold_no_artwork": [36.0, 40.0],
    "whole_source_orca_fades_in_intact": [40.0, 50.0],
    "whole_source_hold_with_late_internal_eddies": [50.0, 60.0],
}

STILL_TIMES = {
    "00_dark_water_current": 3.0,
    "01_flow_begins_to_deflect": 10.0,
    "02_flow_only_before_artwork": 20.0,
    "03_boundary_accumulation": 28.0,
    "04_silhouette_legible_no_artwork": 37.0,
    "05_artwork_fade_begins": 43.0,
    "06_full_artwork_reveal": 50.0,
    "07_late_internal_eddy_overlay": 56.0,
    "08_final_hold": 59.0,
}

DEBUG_TIMES = {
    "flow_only_frame_before_artwork": 24.0,
    "silhouette_legibility_frame": 37.0,
    "full_artwork_reveal": 50.0,
    "optional_internal_eddy_overlay": 56.0,
}

BOUNDARY_TEXT = (
    "Austin greenlit use of the Google Drive artwork and Austin-style / "
    "Coast Salish-style generated experiments for this project. Austin source "
    "remains whole-authored. This prototype uses the alpha silhouette only as "
    "an invisible current/control field. No source modification, recolor, "
    "rigging, fragmentation, or early primitive-window reveal."
)

INTERNAL_EDDY_ANCHORS = [
    {
        "anchor_id": "orca_eye_patch_head_ovoid",
        "center_canvas_px": [2266.633, 1049.931],
        "radius_px": 110,
        "phase": 0.1,
    },
    {
        "anchor_id": "orca_dorsal_inner_trigon",
        "center_canvas_px": [1782.6, 386.0],
        "radius_px": 88,
        "phase": 0.55,
    },
    {
        "anchor_id": "orca_tail_fluke_curve",
        "center_canvas_px": [2469.825, 1617.653],
        "radius_px": 92,
        "phase": 0.85,
    },
]


@dataclass(frozen=True)
class Streamline:
    points: np.ndarray
    distances: np.ndarray
    min_sdf_field_px: float
    source_kind: str
    phase: float
    weight: float


@dataclass(frozen=True)
class RenderAssets:
    source_rgba: Image.Image
    placed_source_render_rgba: Image.Image
    placed_alpha_render: Image.Image
    placed_source_output_rgba: Image.Image
    placed_alpha_output: Image.Image
    obstacle_alpha_render: Image.Image
    obstacle_alpha_output: Image.Image
    background_rgba: Image.Image
    static_streamline_rgba: Image.Image
    boundary_rgba: Image.Image
    wake_rgba: Image.Image
    void_shadow_rgba: Image.Image
    flow_field: dict[str, Any]
    streamlines: list[Streamline]
    dash_streamlines: list[Streamline]
    source_diagnosis: dict[str, Any]
    transform: dict[str, Any]
    canvas_alpha_bbox_px: list[int]
    source_sha256: str


class H264Writer:
    def __init__(
        self,
        path: Path,
        *,
        fps: int,
        input_size: tuple[int, int],
        output_size: tuple[int, int] | None = None,
    ) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to encode the MP4")
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = input_size
        output_width, output_height = output_size or input_size
        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
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
        ]
        if (output_width, output_height) != (width, height):
            cmd += ["-vf", f"scale={output_width}:{output_height}:flags=fast_bilinear,format=yuv420p"]
        else:
            cmd += ["-vf", "format=yuv420p"]
        cmd += [
            "-c:v",
            "h264_videotoolbox",
            "-b:v",
            "45000k",
            "-allow_sw",
            "1",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.width = width
        self.height = height

    def write(self, frame_rgb: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin is closed")
        expected = (self.height, self.width, 3)
        if frame_rgb.dtype != np.uint8 or frame_rgb.shape != expected:
            raise ValueError(f"expected uint8 RGB frame {expected}, got {frame_rgb.shape} {frame_rgb.dtype}")
        self.proc.stdin.write(np.ascontiguousarray(frame_rgb).tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg exited with status {rc}")


def resampling(name: str) -> int:
    return getattr(Image, "Resampling", Image).__dict__[name]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def smooth_array(values: np.ndarray) -> np.ndarray:
    t = np.clip(values, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                pass
    return ImageFont.load_default()


def alpha_bounds(alpha: np.ndarray, threshold: int) -> dict[str, Any]:
    mask = alpha >= threshold
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return {
            "xyxy_inclusive": None,
            "xyxy_exclusive": None,
            "width_height_px": [0, 0],
            "pixel_count": 0,
        }
    x0 = int(xs.min())
    x1 = int(xs.max())
    y0 = int(ys.min())
    y1 = int(ys.max())
    return {
        "xyxy_inclusive": [x0, y0, x1, y1],
        "xyxy_exclusive": [x0, y0, x1 + 1, y1 + 1],
        "width_height_px": [x1 - x0 + 1, y1 - y0 + 1],
        "pixel_count": int(mask.sum()),
    }


def mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, 0, 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def filled_alpha_silhouette(alpha: Image.Image, *, threshold: int = 128) -> Image.Image:
    mask = np.asarray(alpha, dtype=np.uint8) >= threshold
    # Source alpha contains transparent internal negative spaces. For this
    # silhouette-first test, close those broad internal cuts so the current
    # responds to the whole animal body instead of primitive-like windows.
    close_radius = max(24, int(round(min(alpha.size) / 6.3)))
    dilated = ndimage.distance_transform_edt(~mask) <= close_radius
    filled = ndimage.binary_fill_holes(dilated)
    closed = ndimage.distance_transform_edt(filled) > close_radius
    closed = ndimage.binary_fill_holes(closed)
    return Image.fromarray(np.uint8(closed) * 255, "L")


def normalize01(arr: np.ndarray, percentile: float = 99.0) -> np.ndarray:
    hi = float(np.percentile(arr, percentile))
    if hi <= 1.0e-8:
        return np.zeros_like(arr, dtype=np.float32)
    return np.clip(arr / hi, 0.0, 1.0).astype(np.float32)


def make_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for directory in (SOURCE_DIR, STILLS_DIR, DEBUG_DIR):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    for path in [
        OUT_DIR / f"{PROJECT}.mp4",
        OUT_DIR / f"{PROJECT}_contact_sheet.png",
        OUT_DIR / f"{PROJECT}_debug_sheet.png",
        OUT_DIR / f"{PROJECT}_manifest.json",
        OUT_DIR / "README.md",
    ]:
        if path.exists():
            path.unlink()


def make_placed_source(source: Image.Image, *, canvas_size: tuple[int, int], scale: float, top_left: tuple[int, int]) -> Image.Image:
    display_size = (
        int(round(source.width * scale)),
        int(round(source.height * scale)),
    )
    resized = source.resize(display_size, resampling("LANCZOS"))
    placed = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    placed.alpha_composite(resized, top_left)
    return placed


def make_source_placement() -> tuple[Image.Image, Image.Image, Image.Image, Image.Image, Image.Image, dict[str, Any], dict[str, Any], list[int]]:
    source = Image.open(SOURCE_PATH).convert("RGBA")
    source_alpha_arr = np.asarray(source.getchannel("A"))
    source_diag = {
        "source_dimensions_px": [source.width, source.height],
        "alpha_nonzero_pixel_count": int((source_alpha_arr > 0).sum()),
        "alpha_bounds_by_threshold": {
            str(threshold): alpha_bounds(source_alpha_arr, threshold)
            for threshold in [1, 8, 32, 128, 240]
        },
    }

    display_size = (
        int(round(source.width * SOURCE_SCALE)),
        int(round(source.height * SOURCE_SCALE)),
    )
    placed_output = make_placed_source(
        source,
        canvas_size=(OUT_W, OUT_H),
        scale=SOURCE_SCALE,
        top_left=SOURCE_TOP_LEFT,
    )
    placed_render = make_placed_source(
        source,
        canvas_size=(RENDER_W, RENDER_H),
        scale=SOURCE_SCALE_RENDER,
        top_left=SOURCE_TOP_LEFT_RENDER,
    )
    placed_alpha_output = placed_output.getchannel("A")
    placed_alpha_render = placed_render.getchannel("A")
    canvas_alpha_arr = np.asarray(placed_alpha_output)
    canvas_bbox = alpha_bounds(canvas_alpha_arr, 128)["xyxy_inclusive"]
    transform = {
        "uniform_scale": SOURCE_SCALE,
        "top_left_px": list(SOURCE_TOP_LEFT),
        "top_left_float_px": [
            TARGET_ALPHA_CENTER_PX[0]
            - ((source_diag["alpha_bounds_by_threshold"]["128"]["xyxy_exclusive"][0] + source_diag["alpha_bounds_by_threshold"]["128"]["xyxy_exclusive"][2]) * 0.5 * SOURCE_SCALE),
            TARGET_ALPHA_CENTER_PX[1]
            - ((source_diag["alpha_bounds_by_threshold"]["128"]["xyxy_exclusive"][1] + source_diag["alpha_bounds_by_threshold"]["128"]["xyxy_exclusive"][3]) * 0.5 * SOURCE_SCALE),
        ],
        "display_size_px": list(display_size),
        "source_alpha_bbox_px": source_diag["alpha_bounds_by_threshold"]["128"]["xyxy_exclusive"],
        "canvas_alpha_center_target_px": list(TARGET_ALPHA_CENTER_PX),
        "placement_policy": "Uniformly scaled whole RGBA source; source alpha bbox centered on canvas; source RGB unchanged.",
        "internal_working_transform": {
            "working_resolution_px": [RENDER_W, RENDER_H],
            "uniform_scale": SOURCE_SCALE_RENDER,
            "top_left_px": list(SOURCE_TOP_LEFT_RENDER),
            "display_size_px": [
                int(round(source.width * SOURCE_SCALE_RENDER)),
                int(round(source.height * SOURCE_SCALE_RENDER)),
            ],
            "note": "Flow/current layers are rendered at 1920x1080 and upscaled to 3840x2160; the final whole-source fade uses the 4K placed source.",
        },
    }
    return source, placed_render, placed_alpha_render, placed_output, placed_alpha_output, source_diag, transform, canvas_bbox


def make_background() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xn = xx / float(W - 1)
    yn = yy / float(H - 1)
    diag = 0.52 * xn + 0.48 * (1.0 - yn)
    depth = 1.0 - np.sqrt((xn - 0.48) ** 2 + (yn - 0.48) ** 2) * 0.62
    current = 0.5 + 0.5 * np.sin((xn * 5.2 + yn * 2.6) * TAU)
    slow_band = 0.5 + 0.5 * np.sin((xn * 1.1 - yn * 0.8) * TAU + 1.3)
    r = 3.0 + 8.0 * depth + 5.0 * diag
    g = 16.0 + 28.0 * depth + 10.0 * current + 5.0 * slow_band
    b = 30.0 + 58.0 * depth + 15.0 * diag + 10.0 * slow_band
    arr = np.stack([r, g, b], axis=-1)
    rng = np.random.default_rng(1729)
    noise_low = rng.normal(0.0, 1.0, (270, 480)).astype(np.float32)
    noise_low = ndimage.gaussian_filter(noise_low, 1.2)
    noise = np.asarray(
        Image.fromarray(normalize01(noise_low, 99.5) * 255.0).convert("L").resize((W, H), resampling("BICUBIC")),
        dtype=np.float32,
    )
    arr += (noise[..., None] - 126.0) * np.array([0.015, 0.035, 0.06], dtype=np.float32)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def build_flow_field(alpha_full: Image.Image) -> dict[str, Any]:
    alpha_low = np.asarray(alpha_full.resize((FIELD_W, FIELD_H), resampling("BILINEAR")), dtype=np.float32) / 255.0
    obstacle = alpha_low >= 0.50
    obstacle = ndimage.binary_fill_holes(obstacle)
    inside_dist = ndimage.distance_transform_edt(obstacle).astype(np.float32)
    outside_dist = ndimage.distance_transform_edt(~obstacle).astype(np.float32)
    signed = outside_dist - inside_dist
    signed_smooth = ndimage.gaussian_filter(signed, 1.15)
    gy, gx = np.gradient(signed_smooth)
    norm = np.sqrt(gx * gx + gy * gy) + 1.0e-6
    nx = gx / norm
    ny = gy / norm

    base = np.asarray(BASE_FLOW_VECTOR, dtype=np.float32)
    base = base / np.linalg.norm(base)
    bx = float(base[0])
    by = float(base[1])

    tx = -ny
    ty = nx
    tangent_dot = bx * tx + by * ty
    tx = np.where(tangent_dot < 0, -tx, tx)
    ty = np.where(tangent_dot < 0, -ty, ty)
    tangent_dot = np.abs(bx * tx + by * ty)

    outside = signed > 0
    band = np.exp(-np.clip(signed, 0, None) / 12.0) * outside
    wide_band = np.exp(-np.clip(signed, 0, None) / 32.0) * outside
    dot_bn = bx * nx + by * ny
    inward = np.maximum(0.0, -dot_bn) * outside
    shear = tangent_dot * band

    yy, xx = np.mgrid[0:FIELD_H, 0:FIELD_W].astype(np.float32)
    swirl_noise_x = 0.035 * np.sin(xx * 0.028 + yy * 0.019)
    swirl_noise_y = 0.030 * np.cos(xx * 0.017 - yy * 0.031)

    vx = np.full((FIELD_H, FIELD_W), bx, dtype=np.float32)
    vy = np.full((FIELD_H, FIELD_W), by, dtype=np.float32)
    vx += (1.55 * inward * nx + (0.22 + 1.05 * inward) * tx) * band
    vy += (1.55 * inward * ny + (0.22 + 1.05 * inward) * ty) * band
    vx += swirl_noise_x * (1.0 - np.clip(band * 0.8, 0, 1))
    vy += swirl_noise_y * (1.0 - np.clip(band * 0.8, 0, 1))

    bbox = mask_bbox(obstacle)
    x0, y0, x1, y1 = bbox
    wake_centers = [
        [x1 + 38.0, y1 - 88.0, 58.0, 0.30, 1.0],
        [x1 + 92.0, y1 - 44.0, 76.0, -0.26, 0.35],
        [x1 + 70.0, (y0 + y1) * 0.57, 88.0, 0.18, 0.05],
        [x1 + 144.0, (y0 + y1) * 0.72, 115.0, -0.15, 0.50],
    ]
    wake_map = np.zeros((FIELD_H, FIELD_W), dtype=np.float32)
    for cx, cy, radius, amp, phase in wake_centers:
        dx = xx - cx
        dy = yy - cy
        r2 = dx * dx + dy * dy
        falloff = np.exp(-r2 / (2.0 * radius * radius))
        vx += amp * (-dy / max(radius, 1.0)) * falloff
        vy += amp * (dx / max(radius, 1.0)) * falloff
        wake_map += falloff * (0.55 + 0.45 * abs(amp))

    vx = np.where(obstacle, 0.0, vx)
    vy = np.where(obstacle, 0.0, vy)
    speed = np.sqrt(vx * vx + vy * vy)
    max_speed = 1.85
    limiter = np.minimum(1.0, max_speed / (speed + 1.0e-6))
    vx *= limiter
    vy *= limiter

    boundary_map = normalize01(
        ndimage.gaussian_filter((0.78 * inward + 0.62 * shear + 0.36 * wide_band) * outside, 0.85),
        99.4,
    )
    pressure_map = normalize01(ndimage.gaussian_filter(inward * band, 1.3), 99.0)
    wake_map = normalize01(ndimage.gaussian_filter(wake_map * (xx > x1 - 10), 1.8), 99.6)

    return {
        "alpha_low": alpha_low,
        "obstacle": obstacle,
        "inside_dist": inside_dist,
        "outside_dist": outside_dist,
        "signed": signed,
        "normal_x": nx.astype(np.float32),
        "normal_y": ny.astype(np.float32),
        "velocity_x": vx.astype(np.float32),
        "velocity_y": vy.astype(np.float32),
        "boundary_map": boundary_map,
        "pressure_map": pressure_map,
        "wake_map": wake_map,
        "bbox_field_px": list(bbox),
        "wake_centers_field_px": wake_centers,
        "base_flow_unit_vector": [bx, by],
    }


def sample_field(arr: np.ndarray, x: float, y: float, fallback: float = 0.0) -> float:
    if x < 0 or y < 0 or x >= arr.shape[1] - 1 or y >= arr.shape[0] - 1:
        return fallback
    x0 = int(x)
    y0 = int(y)
    fx = x - x0
    fy = y - y0
    v00 = float(arr[y0, x0])
    v10 = float(arr[y0, x0 + 1])
    v01 = float(arr[y0 + 1, x0])
    v11 = float(arr[y0 + 1, x0 + 1])
    return (v00 * (1 - fx) + v10 * fx) * (1 - fy) + (v01 * (1 - fx) + v11 * fx) * fy


def integrate_streamline(
    seed: tuple[float, float],
    field: dict[str, Any],
    *,
    max_steps: int = 780,
    step_px: float = 2.25,
    source_kind: str = "current_seed",
    phase: float = 0.0,
) -> Streamline | None:
    vx = field["velocity_x"]
    vy = field["velocity_y"]
    signed = field["signed"]
    nx = field["normal_x"]
    ny = field["normal_y"]
    bx, by = field["base_flow_unit_vector"]
    x, y = seed
    points: list[tuple[float, float]] = []
    min_sdf = 9999.0
    skipped_inside = 0
    for _ in range(max_steps):
        if x > FIELD_W + 70 or y < -90 or y > FIELD_H + 90:
            break
        if x < 0:
            ux, uy = bx, by
            sdf = 999.0
            gx, gy = 0.0, 0.0
        elif x >= FIELD_W - 1 or y < 0 or y >= FIELD_H - 1:
            ux, uy = bx, by
            sdf = 999.0
            gx, gy = 0.0, 0.0
        else:
            ux = sample_field(vx, x, y, bx)
            uy = sample_field(vy, x, y, by)
            sdf = sample_field(signed, x, y, 999.0)
            gx = sample_field(nx, x, y, 0.0)
            gy = sample_field(ny, x, y, 0.0)
            if sdf < 2.1:
                push = (2.1 - sdf) * 1.45
                ux += gx * push
                uy += gy * push
                skipped_inside += 1
        speed = math.hypot(ux, uy)
        if speed < 0.02:
            ux, uy = bx, by
            speed = 1.0
        ux /= speed
        uy /= speed
        x += ux * step_px
        y += uy * step_px
        if 0 <= x < FIELD_W and 0 <= y < FIELD_H and sdf > 0.8:
            min_sdf = min(min_sdf, sdf)
            points.append((x * FIELD_SCALE_X, y * FIELD_SCALE_Y))
    if len(points) < 80:
        return None
    arr = np.asarray(points, dtype=np.float32)
    deltas = np.diff(arr, axis=0)
    seg = np.sqrt((deltas * deltas).sum(axis=1))
    distances = np.concatenate([[0.0], np.cumsum(seg)]).astype(np.float32)
    if distances[-1] < 420:
        return None
    weight = 1.0 / (1.0 + max(min_sdf, 0.0) / 28.0)
    if skipped_inside > 30:
        weight *= 0.72
    return Streamline(arr, distances, float(min_sdf), source_kind, phase, float(weight))


def generate_streamlines(field: dict[str, Any]) -> list[Streamline]:
    rng = np.random.default_rng(91357)
    lines: list[Streamline] = []
    x0, y0, x1, y1 = field["bbox_field_px"]

    seeds: list[tuple[float, float, str]] = []
    for y in np.linspace(-32, FIELD_H + 32, 220):
        seeds.append((-42.0 + rng.normal(0, 5.0), float(y + rng.normal(0, 3.0)), "left_current"))
    for y in np.linspace(y0 - 58, y1 + 58, 190):
        seeds.append((x0 - 190.0 + rng.normal(0, 18.0), float(y + rng.normal(0, 8.0)), "obstacle_upstream_current"))
    for x in np.linspace(-10, FIELD_W * 0.42, 80):
        seeds.append((float(x + rng.normal(0, 8.0)), -24.0 + rng.normal(0, 5.0), "upper_cross_current"))
    for x in np.linspace(-10, FIELD_W * 0.34, 70):
        seeds.append((float(x + rng.normal(0, 8.0)), FIELD_H + 24.0 + rng.normal(0, 5.0), "lower_cross_current"))

    for idx, (sx, sy, kind) in enumerate(seeds):
        phase = float(rng.random())
        line = integrate_streamline((sx, sy), field, source_kind=kind, phase=phase)
        if line is not None:
            lines.append(line)
    lines.sort(key=lambda line: (line.min_sdf_field_px, -line.distances[-1]))
    return lines[:520]


def make_static_streamline_layer(streamlines: list[Streamline]) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for idx, line in enumerate(streamlines):
        pts = [tuple(map(float, point)) for point in line.points[::2]]
        if len(pts) < 3:
            continue
        near = clamp01(1.0 - line.min_sdf_field_px / 44.0)
        alpha = int(18 + 52 * near + 14 * line.weight)
        width = 1 if near < 0.55 else 2
        if idx % 7 == 0 and near > 0.5:
            width += 1
        color = (
            int(46 + 38 * near),
            int(122 + 55 * near),
            int(152 + 64 * near),
            alpha,
        )
        draw.line(pts, fill=color, width=width, joint="curve")
    return layer.filter(ImageFilter.GaussianBlur(0.15))


def rgba_from_scalar(
    scalar: np.ndarray,
    *,
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
    alpha_max: int,
    gamma: float = 1.0,
) -> Image.Image:
    scalar = np.clip(scalar, 0.0, 1.0) ** gamma
    scalar_img = Image.fromarray(np.uint8(np.clip(scalar * 255, 0, 255)), "L").resize((W, H), resampling("BICUBIC"))
    s = np.asarray(scalar_img, dtype=np.float32) / 255.0
    a = np.uint8(np.clip((s ** gamma) * alpha_max, 0, 255))
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    ca = np.asarray(color_a, dtype=np.float32)
    cb = np.asarray(color_b, dtype=np.float32)
    col = ca[None, None, :] * (1.0 - s[..., None]) + cb[None, None, :] * s[..., None]
    rgb[...] = np.clip(col, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


def make_void_shadow_layer(placed_alpha: Image.Image) -> Image.Image:
    alpha = placed_alpha.filter(ImageFilter.GaussianBlur(20))
    expanded = ImageChops.lighter(alpha, placed_alpha.filter(ImageFilter.GaussianBlur(5)))
    arr = np.asarray(expanded, dtype=np.float32) / 255.0
    arr = smooth_array(arr)
    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[..., 0] = 0
    rgba[..., 1] = 11
    rgba[..., 2] = 22
    rgba[..., 3] = np.uint8(np.clip(arr * 190, 0, 255))
    return Image.fromarray(rgba, "RGBA")


def make_boundary_layers(field: dict[str, Any]) -> tuple[Image.Image, Image.Image]:
    boundary = rgba_from_scalar(
        field["boundary_map"],
        color_a=(45, 126, 151),
        color_b=(164, 231, 232),
        alpha_max=205,
        gamma=0.82,
    ).filter(ImageFilter.GaussianBlur(1.1))
    wake = rgba_from_scalar(
        field["wake_map"],
        color_a=(21, 83, 112),
        color_b=(132, 218, 225),
        alpha_max=132,
        gamma=1.08,
    ).filter(ImageFilter.GaussianBlur(2.0))
    return boundary, wake


def alpha_scaled(layer: Image.Image, factor: float) -> Image.Image | None:
    factor = clamp01(factor)
    if factor <= 0.003:
        return None
    out = layer.copy()
    alpha = out.getchannel("A")
    alpha = alpha.point(lambda p: int(p * factor))
    out.putalpha(alpha)
    return out


def composite_scaled(base: Image.Image, layer: Image.Image, factor: float) -> None:
    scaled = alpha_scaled(layer, factor)
    if scaled is not None:
        base.alpha_composite(scaled)


def phase_strengths(t: float) -> dict[str, float]:
    current = smoothstep01(t / 8.0)
    obstacle = smoothstep01((t - 8.0) / 14.0)
    boundary = smoothstep01((t - 16.0) / 16.0)
    legibility = smoothstep01((t - 22.0) / 14.0)
    artwork = smoothstep01((t - 40.0) / 10.0)
    eddies = smoothstep01((t - 50.0) / 6.0)
    pre_art_hold = 1.0 - 0.18 * smoothstep01((t - 40.0) / 12.0)
    return {
        "current": current,
        "obstacle": obstacle,
        "boundary": boundary,
        "legibility": legibility,
        "artwork": artwork,
        "late_internal_eddies": eddies,
        "pre_art_hold": pre_art_hold,
    }


def draw_dynamic_dashes(base: Image.Image, streamlines: list[Streamline], t: float, opacity: float) -> None:
    if opacity <= 0.01:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    speed = 285.0
    dash_len = 112.0
    period = 820.0
    for idx, line in enumerate(streamlines):
        total = float(line.distances[-1])
        if total < 480:
            continue
        near = clamp01(1.0 - line.min_sdf_field_px / 48.0)
        if near < 0.18 and idx % 3 != 0:
            continue
        phase_offset = line.phase * period + (idx % 11) * 18.0
        count = max(1, int(total // period) + 1)
        alpha = int((32 + 58 * near + 22 * line.weight) * opacity)
        width = 2 if near < 0.75 else 3
        color = (132, 218, 226, alpha)
        for k in range(count):
            s0 = (speed * t + phase_offset + k * period) % max(total - dash_len - 1.0, dash_len)
            s1 = min(total, s0 + dash_len)
            i0 = int(np.searchsorted(line.distances, s0, side="left"))
            i1 = int(np.searchsorted(line.distances, s1, side="right"))
            if i1 - i0 < 2:
                continue
            pts = [tuple(map(float, point)) for point in line.points[i0:i1:2]]
            if len(pts) > 1:
                draw.line(pts, fill=color, width=width, joint="curve")
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.18)))


def draw_wake_arcs(base: Image.Image, field: dict[str, Any], t: float, strength: float) -> None:
    if strength <= 0.01:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for idx, (cx, cy, radius, _amp, phase) in enumerate(field["wake_centers_field_px"]):
        x = cx * FIELD_SCALE_X
        y = cy * FIELD_SCALE_Y
        r_base = radius * FIELD_SCALE_X * (0.82 + 0.08 * idx)
        pulse = 0.5 + 0.5 * math.sin(TAU * (t * 0.075 + phase))
        for ring in range(3):
            r = r_base * (0.55 + 0.33 * ring + 0.08 * pulse)
            alpha = int((44 - ring * 9) * strength * (0.55 + 0.45 * pulse))
            start = (t * 25.0 + phase * 360 + ring * 76) % 360
            end = start + 140 + 18 * ring
            box = [x - r, y - r * 0.62, x + r, y + r * 0.62]
            draw.arc(box, start=start, end=end, fill=(126, 216, 224, alpha), width=max(2, int(3 - ring * 0.3)))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.7)))


def draw_internal_eddies(base: Image.Image, t: float, strength: float, *, coordinate_scale: float) -> None:
    if strength <= 0.01:
        return
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    for anchor in INTERNAL_EDDY_ANCHORS:
        x = float(anchor["center_canvas_px"][0]) * coordinate_scale
        y = float(anchor["center_canvas_px"][1]) * coordinate_scale
        radius = float(anchor["radius_px"]) * coordinate_scale
        phase = float(anchor["phase"])
        pulse = 0.5 + 0.5 * math.sin(TAU * (t * 0.11 + phase))
        for ring in range(3):
            r = radius * (0.52 + 0.24 * ring + 0.05 * pulse)
            squash = 0.54 + 0.08 * ring
            alpha = int((38 - 7 * ring) * strength)
            start = (t * (34 + ring * 9) + phase * 360 + ring * 110) % 360
            end = start + 178 - ring * 22
            box = [x - r, y - r * squash, x + r, y + r * squash]
            draw.arc(box, start=start, end=end, fill=(170, 232, 232, alpha), width=2)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.35)))


def render_frame(assets: RenderAssets, t: float) -> Image.Image:
    strengths = phase_strengths(t)
    frame = assets.background_rgba.copy()

    void_factor = 0.46 * strengths["legibility"] * strengths["pre_art_hold"] * (1.0 - 0.35 * strengths["artwork"])
    composite_scaled(frame, assets.void_shadow_rgba, void_factor)

    flow_factor = (0.10 * strengths["current"] + 0.90 * strengths["current"] * strengths["obstacle"]) * (1.0 - 0.25 * strengths["artwork"])
    composite_scaled(frame, assets.static_streamline_rgba, flow_factor)

    boundary_pulse = 0.74 + 0.26 * math.sin(TAU * (t / 7.5))
    boundary_factor = strengths["boundary"] * boundary_pulse * (1.0 - 0.18 * strengths["artwork"])
    composite_scaled(frame, assets.boundary_rgba, boundary_factor)

    wake_factor = smoothstep01((t - 20.0) / 14.0) * (1.0 - 0.12 * strengths["artwork"])
    composite_scaled(frame, assets.wake_rgba, 0.78 * wake_factor)
    draw_wake_arcs(frame, assets.flow_field, t, 0.85 * wake_factor)

    dash_factor = (0.38 + 0.62 * strengths["obstacle"]) * (1.0 - 0.22 * strengths["artwork"])
    draw_dynamic_dashes(frame, assets.dash_streamlines, t, dash_factor)

    return frame


def render_output_frame(assets: RenderAssets, t: float) -> Image.Image:
    strengths = phase_strengths(t)
    frame = render_frame(assets, t)
    if frame.size != (OUT_W, OUT_H):
        frame = frame.resize((OUT_W, OUT_H), resampling("BICUBIC"))
    if strengths["artwork"] > 0.001:
        composite_scaled(frame, assets.placed_source_output_rgba, strengths["artwork"])
    draw_internal_eddies(frame, t, strengths["late_internal_eddies"] * (0.45 + 0.55 * strengths["artwork"]), coordinate_scale=1.0)
    return frame


def render_video_frame(assets: RenderAssets, t: float) -> Image.Image:
    strengths = phase_strengths(t)
    frame = render_frame(assets, t)
    if strengths["artwork"] > 0.001:
        composite_scaled(frame, assets.placed_source_render_rgba, strengths["artwork"])
    draw_internal_eddies(
        frame,
        t,
        strengths["late_internal_eddies"] * (0.45 + 0.55 * strengths["artwork"]),
        coordinate_scale=OUTPUT_TO_RENDER_SCALE_X,
    )
    return frame


def make_debug_source_alpha(assets: RenderAssets) -> Image.Image:
    panel = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 255))
    alpha = assets.placed_alpha_output
    rgba = np.zeros((OUT_H, OUT_W, 4), dtype=np.uint8)
    arr = np.asarray(alpha)
    rgba[..., 0] = arr
    rgba[..., 1] = arr
    rgba[..., 2] = arr
    rgba[..., 3] = 255
    panel = Image.fromarray(rgba, "RGBA")
    draw = ImageDraw.Draw(panel, "RGBA")
    bbox = assets.canvas_alpha_bbox_px
    draw.rectangle(bbox, outline=(70, 220, 235, 230), width=5)
    return panel


def make_debug_control_field(assets: RenderAssets) -> Image.Image:
    field = assets.flow_field
    signed = field["signed"]
    pressure = field["pressure_map"]
    boundary = field["boundary_map"]
    wake = field["wake_map"]
    outside = np.clip(signed, 0, None)
    inside = np.clip(-signed, 0, None)
    outside_n = normalize01(outside, 96.0)
    inside_n = normalize01(inside, 96.0)
    rgb = np.zeros((FIELD_H, FIELD_W, 3), dtype=np.float32)
    rgb[..., 0] = 34 + 155 * pressure + 50 * inside_n
    rgb[..., 1] = 42 + 146 * boundary + 84 * wake
    rgb[..., 2] = 64 + 132 * outside_n + 150 * wake
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB").resize((OUT_W, OUT_H), resampling("BICUBIC")).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = field["bbox_field_px"]
    draw.rectangle(
        [
            x0 * (OUT_W / FIELD_W),
            y0 * (OUT_H / FIELD_H),
            x1 * (OUT_W / FIELD_W),
            y1 * (OUT_H / FIELD_H),
        ],
        outline=(240, 240, 255, 190),
        width=4,
    )
    return img


def label_panel(img: Image.Image, label: str) -> Image.Image:
    out = img.convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")
    font = load_font(42)
    pad = 24
    box_h = 82
    draw.rectangle([0, 0, out.width, box_h], fill=(0, 8, 15, 185))
    draw.text((pad, 20), label, fill=(224, 245, 246, 255), font=font)
    return out


def make_sheet(items: list[tuple[str, Image.Image]], path: Path, *, columns: int = 3) -> None:
    thumb_w = 960
    thumb_h = 540
    label_h = 82
    rows = math.ceil(len(items) / columns)
    sheet = Image.new("RGBA", (columns * thumb_w, rows * (thumb_h + label_h)), (4, 12, 22, 255))
    font = load_font(30)
    draw = ImageDraw.Draw(sheet, "RGBA")
    for idx, (label, img) in enumerate(items):
        col = idx % columns
        row = idx // columns
        x = col * thumb_w
        y = row * (thumb_h + label_h)
        thumb = img.convert("RGB").resize((thumb_w, thumb_h), resampling("LANCZOS")).convert("RGBA")
        sheet.alpha_composite(thumb, (x, y + label_h))
        draw.rectangle([x, y, x + thumb_w, y + label_h], fill=(0, 8, 15, 245))
        draw.text((x + 18, y + 24), label, fill=(226, 244, 245, 255), font=font)
    sheet.convert("RGB").save(path, quality=94)


def save_stills_and_debug(assets: RenderAssets) -> dict[str, str]:
    still_paths: dict[str, str] = {}
    contact_items: list[tuple[str, Image.Image]] = []
    for label, t in STILL_TIMES.items():
        frame = render_output_frame(assets, t)
        path = STILLS_DIR / f"{label}_{t:05.2f}s.png"
        frame.convert("RGB").save(path)
        still_paths[label] = str(path.relative_to(ROOT))
        contact_items.append((f"{label.replace('_', ' ')} - {t:0.1f}s", frame))

    make_sheet(contact_items, OUT_DIR / f"{PROJECT}_contact_sheet.png", columns=3)

    debug_items: list[tuple[str, Image.Image]] = []
    source_alpha = make_debug_source_alpha(assets)
    source_alpha_path = DEBUG_DIR / "01_source_alpha_silhouette.png"
    source_alpha.convert("RGB").save(source_alpha_path)
    debug_items.append(("source alpha silhouette", source_alpha))

    control = make_debug_control_field(assets)
    control_path = DEBUG_DIR / "02_obstacle_control_field_sdf_pressure_wake.png"
    control.convert("RGB").save(control_path)
    debug_items.append(("obstacle/control field", control))

    for idx, (label, t) in enumerate(DEBUG_TIMES.items(), start=3):
        frame = render_output_frame(assets, t)
        path = DEBUG_DIR / f"{idx:02d}_{label}_{t:05.2f}s.png"
        frame.convert("RGB").save(path)
        debug_items.append((f"{label.replace('_', ' ')} - {t:0.1f}s", frame))

    make_sheet(debug_items, OUT_DIR / f"{PROJECT}_debug_sheet.png", columns=3)
    return still_paths


def render_video(assets: RenderAssets) -> None:
    output_path = OUT_DIR / f"{PROJECT}.mp4"
    writer = H264Writer(output_path, fps=FPS, input_size=(W, H), output_size=(OUT_W, OUT_H))
    try:
        for frame_index in range(FRAME_COUNT):
            t = frame_index / FPS
            frame = render_video_frame(assets, t).convert("RGB")
            writer.write(np.asarray(frame, dtype=np.uint8))
            if frame_index % 120 == 0:
                print(f"rendered frame {frame_index}/{FRAME_COUNT} ({t:0.1f}s)", flush=True)
    finally:
        writer.close()


def build_assets() -> RenderAssets:
    source, placed_render, placed_alpha_render, placed_output, placed_alpha_output, source_diag, transform, canvas_bbox = make_source_placement()
    obstacle_alpha_render = filled_alpha_silhouette(placed_alpha_render)
    obstacle_alpha_output = filled_alpha_silhouette(placed_alpha_output)
    field = build_flow_field(obstacle_alpha_render)
    streamlines = generate_streamlines(field)
    dash_streamlines = [
        line
        for idx, line in enumerate(streamlines)
        if line.min_sdf_field_px < 52 or idx % 5 == 0
    ][:80]
    background = make_background()
    static_layer = make_static_streamline_layer(streamlines)
    boundary_layer, wake_layer = make_boundary_layers(field)
    void_shadow = make_void_shadow_layer(obstacle_alpha_render)
    return RenderAssets(
        source_rgba=source,
        placed_source_render_rgba=placed_render,
        placed_alpha_render=placed_alpha_render,
        placed_source_output_rgba=placed_output,
        placed_alpha_output=placed_alpha_output,
        obstacle_alpha_render=obstacle_alpha_render,
        obstacle_alpha_output=obstacle_alpha_output,
        background_rgba=background,
        static_streamline_rgba=static_layer,
        boundary_rgba=boundary_layer,
        wake_rgba=wake_layer,
        void_shadow_rgba=void_shadow,
        flow_field=field,
        streamlines=streamlines,
        dash_streamlines=dash_streamlines,
        source_diagnosis=source_diag,
        transform=transform,
        canvas_alpha_bbox_px=canvas_bbox,
        source_sha256=sha256(SOURCE_PATH),
    )


def manifest_for(assets: RenderAssets, still_paths: dict[str, str], *, stills_only: bool) -> dict[str, Any]:
    renderer_path = Path(__file__).resolve()
    x0, y0, x1, y1 = assets.flow_field["bbox_field_px"]
    return {
        "project": PROJECT,
        "status": "internal_review_only_pending_austin_specific_output_clearance",
        "boundary": BOUNDARY_TEXT,
        "renderer": str(renderer_path.relative_to(ROOT)),
        "renderer_sha256": sha256(renderer_path),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": assets.source_sha256,
        "source_copy": str((SOURCE_DIR / SOURCE_PATH.name).relative_to(ROOT)),
        "source_diagnosis": assets.source_diagnosis,
        "source_to_canvas_transform": assets.transform,
        "canvas_art_alpha_bbox_px": assets.canvas_alpha_bbox_px,
        "architecture": {
            "type": "silhouette_reveal",
            "explicitly_not": [
                "cymatic_aperture_reveal",
                "scattered_internal_primitive_windows_first",
                "source_fragmentation",
                "source_recolor",
                "source_rigging",
            ],
            "control_field": "Placed Orca alpha threshold >= 128 is morphologically closed and hole-filled into an outer-body silhouette, then treated as an invisible obstacle for current deflection and boundary accumulation.",
            "source_reveal": "Whole Austin-authored RGBA source fades in uniformly after the current field has established a legible body silhouette.",
        },
        "render_spec": {
            "width_px": OUT_W,
            "height_px": OUT_H,
            "internal_working_resolution_px": [RENDER_W, RENDER_H],
            "final_scale_from_internal": [RENDER_TO_OUTPUT_SCALE_X, RENDER_TO_OUTPUT_SCALE_Y],
            "video_encode": "Frames are generated at internal working resolution and scaled to 3840x2160 by ffmpeg using h264_videotoolbox. Contact/debug stills are written at final 4K output size.",
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frame_count": FRAME_COUNT,
            "mp4": None if stills_only else str((OUT_DIR / f"{PROJECT}.mp4").relative_to(ROOT)),
        },
        "flow_model": {
            "field_resolution_px": [FIELD_W, FIELD_H],
            "base_flow_unit_vector": assets.flow_field["base_flow_unit_vector"],
            "obstacle_bbox_field_px": [x0, y0, x1, y1],
            "streamline_count": len(assets.streamlines),
            "animated_dash_streamline_count": len(assets.dash_streamlines),
            "sdf_method": "scipy.ndimage distance_transform_edt on the closed/hole-filled placed whole-source alpha silhouette; positive outside obstacle, negative inside.",
            "deflection_method": "Base current removes inward normal velocity near SDF boundary, preserves/slightly boosts tangential slip, and adds restrained wake vortices downstream.",
            "boundary_accumulation": "Boundary alpha map combines pressure/convergence, tangential shear, and a wide SDF band. It is blurred and rendered as water density, not a direct contour stroke.",
            "wake_vortices_field_px": assets.flow_field["wake_centers_field_px"],
        },
        "timing": TIMING,
        "internal_eddy_policy": {
            "used": True,
            "starts_after_seconds": 50.0,
            "purpose": "Late hybrid accent only after the silhouette is already established and the whole source is fading/visible.",
            "anchors": INTERNAL_EDDY_ANCHORS,
            "not_used_for_first_read": True,
        },
        "acceptance": {
            "first_read_goal": "An Orca-shaped body forming in water before artwork appears.",
            "flow_only_before_artwork_frame": str((DEBUG_DIR / "03_flow_only_frame_before_artwork_24.00s.png").relative_to(ROOT)),
            "silhouette_legibility_frame": str((DEBUG_DIR / "04_silhouette_legibility_frame_37.00s.png").relative_to(ROOT)),
            "full_artwork_reveal_frame": str((DEBUG_DIR / "05_full_artwork_reveal_50.00s.png").relative_to(ROOT)),
            "body_legible_before_artwork_self_assessment": "PASS_CANDIDATE",
            "verdict": "PASS_CANDIDATE_PENDING_HUMAN_REVIEW",
            "failure_condition_if_seen_in_review": "Mark MIXED if the 37s silhouette legibility frame does not read as one Orca-shaped body before the source appears.",
        },
        "deliverables": {
            "video": None if stills_only else str((OUT_DIR / f"{PROJECT}.mp4").relative_to(ROOT)),
            "contact_sheet": str((OUT_DIR / f"{PROJECT}_contact_sheet.png").relative_to(ROOT)),
            "debug_sheet": str((OUT_DIR / f"{PROJECT}_debug_sheet.png").relative_to(ROOT)),
            "manifest": str((OUT_DIR / f"{PROJECT}_manifest.json").relative_to(ROOT)),
            "readme": str((OUT_DIR / "README.md").relative_to(ROOT)),
            "stills": still_paths,
            "debug_stills_dir": str(DEBUG_DIR.relative_to(ROOT)),
        },
    }


def write_manifest(manifest: dict[str, Any]) -> None:
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def write_readme(manifest: dict[str, Any]) -> None:
    lines = [
        f"# {PROJECT}",
        "",
        "Status: Austin-authorized internal / show-development prototype only. This specific output still requires Darren/Austin clearance before any public, sponsor, press, or show-surface use.",
        "",
        "## Purpose",
        "",
        "This is the silhouette-first fluid/current reveal recommended by `docs/space-center/figural-fluid-dynamics-reveal-scout-2026-05-22.md`.",
        "",
        "It does not continue the cymatic aperture approach. It does not reveal scattered internal primitive windows first. The whole Orca alpha silhouette is used only as an invisible current obstacle/control field, and the complete Austin-authored Orca source fades in uniformly after the body has already been implied by water behavior.",
        "",
        "## Source And Placement",
        "",
        f"- Source path: `{manifest['source_path']}`",
        f"- Source SHA-256: `{manifest['source_sha256']}`",
        "- Source dimensions: `[2522, 2215]` px.",
        "- Canvas transform: scale `0.88`, top-left `[896, 122]`, display size `[2219, 1949]`.",
        f"- Canvas alpha bbox after placement: `{manifest['canvas_art_alpha_bbox_px']}`.",
        "",
        "## Mechanic",
        "",
        "- A left-to-right, slight-up current crosses a dark water field.",
        "- The placed Orca alpha mask is morphologically closed and hole-filled into an outer-body silhouette, then converted into an SDF obstacle.",
        "- Current removes inward normal velocity near the silhouette, slips tangentially around the boundary, and forms downstream wake vortices.",
        "- Streamlines, boundary pressure, wake eddies, and negative-space accumulation make the Orca body legible before source artwork appears.",
        "- The full whole-source Orca artwork fades in intact from 40s to 50s.",
        "- Late internal eddies at the eye, dorsal, and tail anchors start only after 50s; they are not used for first read.",
        "",
        "## Sequence",
        "",
        "- 0-8s: dark water current enters.",
        "- 8-22s: hidden Orca obstacle begins bending the current.",
        "- 22-36s: boundary accumulation and wake build the body.",
        "- 36-40s: silhouette legibility hold with no artwork visible.",
        "- 40-50s: whole source Orca fades in uniformly and intact.",
        "- 50-60s: whole-source hold with subtle late internal eddy overlay.",
        "",
        "## Acceptance",
        "",
        "- First-read target: an Orca-shaped body forming in water.",
        "- Self-assessment: `PASS_CANDIDATE_PENDING_HUMAN_REVIEW`.",
        "- Review rule: mark `MIXED` if the 37s silhouette legibility frame does not read as one Orca-shaped body before the artwork appears.",
        "- Review rule: mark `FAIL` if the source artwork reads as a card/fade without fluid anticipation.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: 3840x2160, 24fps, 60 seconds.",
        f"- `{PROJECT}_contact_sheet.png`",
        f"- `{PROJECT}_debug_sheet.png`",
        f"- `{PROJECT}_manifest.json`",
        "- `stills/`: sequence stills.",
        "- `debug_stills/`: source alpha, obstacle/control field, flow-only frame, silhouette legibility frame, full artwork reveal, and late eddy overlay.",
        "",
        "## Boundary",
        "",
        BOUNDARY_TEXT,
        "",
        "The whole Orca source is not recolored, fragmented, rigged, or independently animated. Internal eddies are late current accents only, not source masks or primitive-window reveals.",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stills-only",
        action="store_true",
        help="Generate stills, sheets, README, and manifest without encoding the MP4.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(SOURCE_PATH)
    make_dirs()
    shutil.copy2(SOURCE_PATH, SOURCE_DIR / SOURCE_PATH.name)
    print(f"building assets for {PROJECT}", flush=True)
    assets = build_assets()
    print(f"generated {len(assets.streamlines)} streamlines ({len(assets.dash_streamlines)} animated dash carriers)", flush=True)
    still_paths = save_stills_and_debug(assets)
    if not args.stills_only:
        render_video(assets)
    manifest = manifest_for(assets, still_paths, stills_only=args.stills_only)
    write_manifest(manifest)
    write_readme(manifest)
    print(f"wrote {OUT_DIR.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
