#!/usr/bin/env python3
"""
Portable TELUS batch harness for generated abstract cymatic compositions.

This script intentionally does not load source artwork or Austin assets. It
renders generated scalar-field wave geometry only, writes PNG frames to local
scratch, encodes MP4 with ffmpeg, and emits contact sheets plus loop diagnostics.
It is safe to import from a Jupyter notebook or run as a CLI script.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
TAU = math.tau

DEFAULT_CONFIG: dict[str, Any] = {
    "batch_name": "telus_abstract_cymatic_batch",
    "width": 3840,
    "height": 2160,
    "fps": 24,
    "duration_seconds": 5.0,
    "field_scale": 0.375,
    "crf": 18,
    "preset": "medium",
    "keep_frames": True,
    "variants": [
        {
            "name": "abstract_membrane_seed",
            "family": "radial_lattice",
            "seed": 37,
            "source_count": 7,
            "rings": 5,
            "wavelength": 0.155,
            "decay": 0.92,
            "angular_order": 6,
            "angular_alpha": 0.18,
            "threshold": 0.42,
            "node_width": 0.075,
            "rotation": 0.08,
            "palette": "deep_water",
        }
    ],
}

PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "deep_water": {
        "background": (4, 11, 13),
        "low": (18, 47, 54),
        "negative": (56, 174, 191),
        "positive": (234, 232, 205),
        "node": (118, 235, 224),
        "spark": (246, 198, 94),
    },
    "mineral": {
        "background": (9, 11, 12),
        "low": (30, 38, 41),
        "negative": (88, 144, 156),
        "positive": (220, 226, 214),
        "node": (170, 218, 208),
        "spark": (214, 163, 82),
    },
    "ice_gold": {
        "background": (5, 12, 19),
        "low": (25, 53, 68),
        "negative": (107, 197, 219),
        "positive": (236, 239, 225),
        "node": (196, 243, 245),
        "spark": (245, 204, 103),
    },
}

_GRID_CACHE: dict[tuple[int, int, float], dict[str, np.ndarray | int | float]] = {}


@dataclass(frozen=True)
class RenderSettings:
    width: int
    height: int
    fps: int
    duration_seconds: float
    field_scale: float
    crf: int
    preset: str
    keep_frames: bool

    @property
    def frame_count(self) -> int:
        return int(round(self.fps * self.duration_seconds))


def resolve_scratch(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser().resolve()
    for key in ("TELUS_SCRATCH", "SLURM_TMPDIR", "TMPDIR", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            return Path(value).expanduser().resolve()
    return Path("/tmp").resolve()


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        user_config = json.load(handle)
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    deep_update(merged, user_config)
    return merged


def deep_update(base: dict[str, Any], override: dict[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value


def render_settings_from_config(config: dict[str, Any], args: argparse.Namespace | None = None) -> RenderSettings:
    width = int(getattr(args, "width", None) or config.get("width", DEFAULT_CONFIG["width"]))
    height = int(getattr(args, "height", None) or config.get("height", DEFAULT_CONFIG["height"]))
    fps = int(getattr(args, "fps", None) or config.get("fps", DEFAULT_CONFIG["fps"]))
    duration_seconds = float(
        getattr(args, "duration", None) or config.get("duration_seconds", DEFAULT_CONFIG["duration_seconds"])
    )
    field_scale = float(getattr(args, "field_scale", None) or config.get("field_scale", DEFAULT_CONFIG["field_scale"]))
    crf = int(getattr(args, "crf", None) or config.get("crf", DEFAULT_CONFIG["crf"]))
    preset = str(getattr(args, "preset", None) or config.get("preset", DEFAULT_CONFIG["preset"]))
    keep_frames = bool(config.get("keep_frames", DEFAULT_CONFIG["keep_frames"]))
    if getattr(args, "discard_frames", False):
        keep_frames = False
    return RenderSettings(
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration_seconds,
        field_scale=field_scale,
        crf=crf,
        preset=preset,
        keep_frames=keep_frames,
    )


def expand_variants(config: dict[str, Any]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for raw in config.get("variants", []):
        base = {key: value for key, value in raw.items() if key != "sweep"}
        sweep = raw.get("sweep")
        if not sweep:
            expanded.append(base)
            continue
        keys = list(sweep.keys())
        values = [sweep[key] if isinstance(sweep[key], list) else [sweep[key]] for key in keys]
        for combo in itertools.product(*values):
            variant = dict(base)
            suffix_parts: list[str] = []
            for key, value in zip(keys, combo, strict=True):
                variant[key] = value
                safe_value = str(value).replace(".", "p").replace("-", "m")
                suffix_parts.append(f"{key}-{safe_value}")
            variant["name"] = safe_name(f"{base.get('name', 'variant')}__{'__'.join(suffix_parts)}")
            expanded.append(variant)
    return expanded


def safe_name(value: str) -> str:
    keep = []
    for char in value.strip().lower():
        if char.isalnum():
            keep.append(char)
        elif char in {"-", "_"}:
            keep.append(char)
        elif char in {" ", ".", "/"}:
            keep.append("_")
    name = "".join(keep).strip("_")
    return name or "variant"


def get_grid(settings: RenderSettings) -> dict[str, np.ndarray | int | float]:
    key = (settings.width, settings.height, settings.field_scale)
    cached = _GRID_CACHE.get(key)
    if cached is not None:
        return cached

    fw = max(64, int(round(settings.width * settings.field_scale)))
    fh = max(64, int(round(settings.height * settings.field_scale)))
    aspect = settings.width / settings.height
    x = np.linspace(-aspect, aspect, fw, dtype=np.float32)
    y = np.linspace(-1.0, 1.0, fh, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    rx = xx / aspect
    radial = np.sqrt(rx * rx + yy * yy, dtype=np.float32)
    x_edge = np.minimum(np.arange(fw, dtype=np.float32) + 1.0, fw - np.arange(fw, dtype=np.float32))[None, :]
    y_edge = np.minimum(np.arange(fh, dtype=np.float32) + 1.0, fh - np.arange(fh, dtype=np.float32))[:, None]
    edge_distance = np.minimum(x_edge, y_edge)
    edge_window = smoothstep_array(8.0, max(24.0, min(fw, fh) * 0.105), edge_distance)
    vignette = np.clip(1.0 - 0.50 * smoothstep_array(0.38, 1.16, radial), 0.34, 1.0).astype(np.float32)
    cached = {
        "fw": fw,
        "fh": fh,
        "aspect": aspect,
        "x": xx,
        "y": yy,
        "radial": radial,
        "edge_window": edge_window.astype(np.float32),
        "vignette": vignette.astype(np.float32),
    }
    _GRID_CACHE[key] = cached
    return cached


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = min(1.0, max(0.0, (value - edge0) / max(1e-8, edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def smoothstep_array(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / max(1e-8, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def palette_for(variant: dict[str, Any]) -> dict[str, np.ndarray]:
    raw = PALETTES.get(str(variant.get("palette", "deep_water")), PALETTES["deep_water"])
    return {key: np.array(value, dtype=np.float32) for key, value in raw.items()}


def evaluate_field(variant: dict[str, Any], settings: RenderSettings, frame_index: int) -> np.ndarray:
    grid = get_grid(settings)
    x = grid["x"]
    y = grid["y"]
    assert isinstance(x, np.ndarray)
    assert isinstance(y, np.ndarray)
    field = np.zeros_like(x, dtype=np.float32)
    phase = frame_index / max(1, settings.frame_count)
    family = str(variant.get("family", "radial_lattice"))

    if family == "chladni":
        field = evaluate_chladni_field(variant, x, y, phase)
    elif family == "raindrop_interference":
        field = evaluate_raindrop_field(variant, x, y, phase)
    else:
        field = evaluate_radial_lattice_field(variant, x, y, phase)

    edge_window = grid["edge_window"]
    assert isinstance(edge_window, np.ndarray)
    field *= edge_window
    max_abs = float(np.percentile(np.abs(field), 99.4))
    if max_abs > 1e-7:
        field = np.clip(field / max_abs, -1.0, 1.0)
    return field.astype(np.float32)


def evaluate_radial_lattice_field(variant: dict[str, Any], x: np.ndarray, y: np.ndarray, phase: float) -> np.ndarray:
    rng = np.random.default_rng(int(variant.get("seed", 0)))
    source_count = max(2, int(variant.get("source_count", 7)))
    wavelength = float(variant.get("wavelength", 0.155))
    decay = float(variant.get("decay", 0.92))
    angular_order = int(variant.get("angular_order", 6))
    angular_alpha = float(variant.get("angular_alpha", 0.12))
    rotation_cycles = float(variant.get("rotation_cycles", 0.0))
    rotation_amplitude = float(variant.get("rotation", variant.get("rotation_amplitude", 0.08)))
    rotation = TAU * rotation_cycles * phase + rotation_amplitude * math.sin(TAU * phase)
    breathe = 1.0 + 0.075 * math.sin(TAU * phase)
    field = np.zeros_like(x, dtype=np.float32)

    source_rows: list[tuple[float, float, float, float, float]] = [(0.0, 0.0, 1.15, 0.0, 1.0)]
    ring_count = source_count - 1
    for idx in range(ring_count):
        angle = rotation + TAU * idx / ring_count + float(rng.normal(0.0, 0.018))
        radius = 0.44 * breathe * (1.0 + float(rng.normal(0.0, 0.035)))
        sx = math.cos(angle) * radius
        sy = math.sin(angle) * radius
        amp = 0.72 + 0.16 * math.sin(idx * 1.7 + phase * TAU)
        source_phase = idx * 0.41 + 0.22 * math.sin(TAU * phase + idx)
        source_rows.append((sx, sy, amp, source_phase, 1.0))

    for sx, sy, amp, source_phase, env in source_rows:
        dx = x - sx
        dy = y - sy
        distance = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
        theta = np.arctan2(dy, dx).astype(np.float32)
        angular = 1.0 + angular_alpha * np.cos(angular_order * theta + TAU * phase, dtype=np.float32)
        wave = np.cos((TAU / wavelength) * distance - TAU * phase + source_phase, dtype=np.float32)
        falloff = np.exp(-distance / max(0.05, decay), dtype=np.float32)
        field += np.float32(amp * env) * wave * falloff * angular

    rings = max(0, int(variant.get("rings", 5)))
    if rings:
        radial = np.sqrt(x * x + y * y, dtype=np.float32)
        ring_phase_cycles = float(variant.get("ring_phase_cycles", 1.0))
        ring_wave = np.cos(TAU * rings * radial - TAU * phase * ring_phase_cycles, dtype=np.float32)
        field += np.float32(0.28) * ring_wave * np.exp(-radial * 0.88, dtype=np.float32)
    return field


def evaluate_raindrop_field(variant: dict[str, Any], x: np.ndarray, y: np.ndarray, phase: float) -> np.ndarray:
    rng = np.random.default_rng(int(variant.get("seed", 0)))
    source_count = max(4, int(variant.get("source_count", 10)))
    wavelength = float(variant.get("wavelength", 0.105))
    decay = float(variant.get("decay", 0.72))
    field = np.zeros_like(x, dtype=np.float32)
    for idx in range(source_count):
        sx = float(rng.uniform(-1.45, 1.45))
        sy = float(rng.uniform(-0.78, 0.78))
        birth = (idx / source_count + float(rng.uniform(-0.05, 0.05))) % 1.0
        age = (phase - birth) % 1.0
        lifetime = 0.46 + 0.12 * float(rng.random())
        env = smoothstep(0.0, 0.055, age) * max(0.0, 1.0 - age / lifetime) ** 1.55 if age < lifetime else 0.0
        if env <= 0.0005:
            continue
        dx = x - sx
        dy = y - sy
        distance = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
        wave = np.cos((TAU / wavelength) * distance - TAU * age * 2.7 + idx * 0.17, dtype=np.float32)
        falloff = np.exp(-distance / max(0.05, decay), dtype=np.float32)
        field += np.float32(env * (0.9 + 0.25 * (idx % 3 == 0))) * wave * falloff
    return field


def evaluate_chladni_field(variant: dict[str, Any], x: np.ndarray, y: np.ndarray, phase: float) -> np.ndarray:
    mode_a = int(variant.get("mode_a", 3))
    mode_b = int(variant.get("mode_b", 5))
    mode_c = int(variant.get("mode_c", 2))
    mode_d = int(variant.get("mode_d", 7))
    drift = 0.12 * math.sin(TAU * phase)
    xx = (x + 1.0 + drift) * math.pi
    yy = (y + 1.0 - drift * 0.5) * math.pi
    first = np.cos(mode_a * xx, dtype=np.float32) * np.cos(mode_b * yy, dtype=np.float32)
    second = np.cos(mode_b * xx, dtype=np.float32) * np.cos(mode_a * yy, dtype=np.float32)
    third = np.cos(mode_c * xx + TAU * phase, dtype=np.float32) * np.cos(mode_d * yy, dtype=np.float32)
    return first - second + np.float32(0.28) * third


def render_frame_array(variant: dict[str, Any], settings: RenderSettings, frame_index: int) -> np.ndarray:
    field = evaluate_field(variant, settings, frame_index)
    grid = get_grid(settings)
    vignette = grid["vignette"]
    radial = grid["radial"]
    assert isinstance(vignette, np.ndarray)
    assert isinstance(radial, np.ndarray)

    palette = palette_for(variant)
    threshold = float(variant.get("threshold", 0.42))
    node_width = float(variant.get("node_width", 0.075))
    phase = frame_index / max(1, settings.frame_count)
    swap = 0.5 + 0.5 * math.cos(TAU * phase)

    positive = smoothstep_array(threshold - 0.08, threshold + 0.16, field)
    negative = smoothstep_array(threshold - 0.08, threshold + 0.16, -field)
    nodes = np.exp(-((np.abs(field) / max(0.012, node_width)) ** 2), dtype=np.float32)
    nodes *= 0.48 + 0.52 * smoothstep_array(0.08, 0.95, radial)

    rgb = palette["background"][None, None, :] + palette["low"][None, None, :] * (0.15 + 0.24 * vignette[..., None])
    rgb += positive[..., None] * palette["positive"][None, None, :] * (0.26 + 0.56 * swap)
    rgb += negative[..., None] * palette["negative"][None, None, :] * (0.22 + 0.58 * (1.0 - swap))
    rgb += nodes[..., None] * palette["node"][None, None, :] * (0.22 + 0.18 * math.sin(TAU * phase) ** 2)

    gy, gx = np.gradient(field)
    slope = np.clip(np.sqrt(gx * gx + gy * gy, dtype=np.float32) * 2.8, 0.0, 1.0)
    rgb += slope[..., None] * palette["spark"][None, None, :] * 0.12
    rgb *= vignette[..., None]

    small = np.clip(rgb, 0, 255).astype(np.uint8)
    if small.shape[1] == settings.width and small.shape[0] == settings.height:
        return small
    image = Image.fromarray(small, "RGB").resize((settings.width, settings.height), Image.Resampling.BICUBIC)
    return np.asarray(image, dtype=np.uint8)


def render_frame_to_png(task: tuple[dict[str, Any], RenderSettings, int, str]) -> dict[str, Any]:
    variant, settings, frame_index, frames_dir_text = task
    start = time.perf_counter()
    frame = render_frame_array(variant, settings, frame_index)
    frame_path = Path(frames_dir_text) / f"frame_{frame_index:06d}.png"
    Image.fromarray(frame, "RGB").save(frame_path, compress_level=1)
    return {
        "frame": frame_index,
        "path": str(frame_path),
        "seconds": time.perf_counter() - start,
    }


def render_variant(
    variant: dict[str, Any],
    settings: RenderSettings,
    output_dir: Path,
    *,
    workers: int = 1,
    overwrite: bool = True,
) -> dict[str, Any]:
    variant_name = safe_name(str(variant.get("name", "variant")))
    variant_dir = output_dir / variant_name
    frames_dir = variant_dir / "frames"
    if overwrite and frames_dir.exists():
        for frame_path in frames_dir.glob("frame_*.png"):
            frame_path.unlink()
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_count = settings.frame_count
    start = time.perf_counter()
    frame_stats: list[dict[str, Any]] = []
    if workers <= 1:
        for frame_index in range(frame_count):
            frame_stats.append(render_frame_to_png((variant, settings, frame_index, str(frames_dir))))
            print_progress(variant_name, len(frame_stats), frame_count)
    else:
        tasks = [(variant, settings, frame_index, str(frames_dir)) for frame_index in range(frame_count)]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(render_frame_to_png, task) for task in tasks]
            completed = 0
            for future in as_completed(futures):
                frame_stats.append(future.result())
                completed += 1
                print_progress(variant_name, completed, frame_count)

    render_seconds = time.perf_counter() - start
    mp4_path = variant_dir / f"{variant_name}_{settings.width}x{settings.height}_{settings.frame_count}f.mp4"
    encode_seconds = encode_mp4(frames_dir, mp4_path, settings)
    contact_sheet_path = make_contact_sheet(frames_dir, variant_dir / f"{variant_name}_contact_sheet.png", settings)
    loop_diag = make_loop_diagnostics(frames_dir, variant_dir / f"{variant_name}_loop_diagnostics.png", settings)
    manifest_path = variant_dir / f"{variant_name}_manifest.json"
    avg_frame_seconds = float(np.mean([row["seconds"] for row in frame_stats])) if frame_stats else 0.0
    manifest = {
        "renderer": "scripts/telus_abstract_cymatic_batch.py",
        "boundary": "Generated abstract scalar-field cymatic geometry only; no Austin assets; no source artwork; no cultural claims.",
        "variant": variant,
        "settings": {
            "width": settings.width,
            "height": settings.height,
            "fps": settings.fps,
            "duration_seconds": settings.duration_seconds,
            "frame_count": settings.frame_count,
            "field_scale": settings.field_scale,
            "crf": settings.crf,
            "preset": settings.preset,
            "workers": workers,
        },
        "timing": {
            "render_seconds": round(render_seconds, 3),
            "encode_seconds": round(encode_seconds, 3),
            "avg_worker_frame_seconds": round(avg_frame_seconds, 4),
            "effective_frames_per_second_rendered": round(frame_count / max(1e-6, render_seconds), 3),
        },
        "outputs": {
            "frames_dir": str(frames_dir),
            "mp4": str(mp4_path),
            "contact_sheet": str(contact_sheet_path),
            "loop_diagnostics": str(loop_diag["image"]),
            "loop_diagnostics_json": str(loop_diag["json"]),
        },
        "loop_metrics": loop_diag["metrics"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if not settings.keep_frames:
        shutil.rmtree(frames_dir)
        manifest["outputs"]["frames_dir"] = None
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "variant": variant_name,
        "variant_dir": str(variant_dir),
        "mp4": str(mp4_path),
        "contact_sheet": str(contact_sheet_path),
        "loop_diagnostics": str(loop_diag["image"]),
        "manifest": str(manifest_path),
        "timing": manifest["timing"],
        "loop_metrics": loop_diag["metrics"],
    }


def print_progress(name: str, completed: int, total: int) -> None:
    stride = max(1, total // 10)
    if completed == total or completed == 1 or completed % stride == 0:
        print(f"{name}: {completed}/{total} frames", flush=True)


def encode_mp4(frames_dir: Path, mp4_path: Path, settings: RenderSettings) -> float:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-framerate",
        str(settings.fps),
        "-i",
        str(frames_dir / "frame_%06d.png"),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        str(settings.crf),
        "-preset",
        settings.preset,
        "-movflags",
        "+faststart",
        str(mp4_path),
    ]
    start = time.perf_counter()
    subprocess.run(cmd, check=True)
    return time.perf_counter() - start


def make_contact_sheet(frames_dir: Path, output_path: Path, settings: RenderSettings) -> Path:
    indices = evenly_spaced_indices(settings.frame_count, 8)
    thumbs: list[Image.Image] = []
    for frame_index in indices:
        path = frames_dir / f"frame_{frame_index:06d}.png"
        image = Image.open(path).convert("RGB")
        image.thumbnail((480, 270), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (480, 300), (8, 12, 14))
        canvas.paste(image, ((480 - image.width) // 2, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 276), f"f{frame_index:06d}  t={frame_index / settings.fps:0.2f}s", fill=(226, 234, 230))
        thumbs.append(canvas)

    sheet = Image.new("RGB", (480 * 4, 300 * 2), (8, 12, 14))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % 4) * 480, (idx // 4) * 300))
    sheet.save(output_path, compress_level=4)
    return output_path


def make_loop_diagnostics(frames_dir: Path, output_path: Path, settings: RenderSettings) -> dict[str, Any]:
    first = np.asarray(Image.open(frames_dir / "frame_000000.png").convert("RGB"), dtype=np.float32)
    last_index = settings.frame_count - 1
    last = np.asarray(Image.open(frames_dir / f"frame_{last_index:06d}.png").convert("RGB"), dtype=np.float32)
    diff = np.abs(first - last)
    adjacent_means: list[float] = []
    for frame_index in evenly_spaced_indices(max(1, settings.frame_count - 1), min(12, max(1, settings.frame_count - 1))):
        if frame_index >= settings.frame_count - 1:
            continue
        current = np.asarray(Image.open(frames_dir / f"frame_{frame_index:06d}.png").convert("RGB"), dtype=np.float32)
        next_frame = np.asarray(Image.open(frames_dir / f"frame_{frame_index + 1:06d}.png").convert("RGB"), dtype=np.float32)
        adjacent_means.append(float(np.abs(next_frame - current).mean()))
    adjacent_median = float(np.median(adjacent_means)) if adjacent_means else 0.0
    seam_mean = float(diff.mean())
    metrics = {
        "first_last_mean_abs_rgb_delta": round(seam_mean, 4),
        "first_last_p95_abs_rgb_delta": round(float(np.percentile(diff, 95)), 4),
        "first_last_max_abs_rgb_delta": round(float(diff.max()), 4),
        "sample_adjacent_mean_abs_rgb_delta_median": round(adjacent_median, 4),
        "loop_to_adjacent_delta_ratio": round(seam_mean / max(adjacent_median, 1e-6), 4),
    }
    diff_vis = np.clip(diff * 5.0, 0, 255).astype(np.uint8)
    panels = [
        Image.fromarray(first.astype(np.uint8), "RGB"),
        Image.fromarray(last.astype(np.uint8), "RGB"),
        Image.fromarray(diff_vis, "RGB"),
    ]
    thumbs: list[Image.Image] = []
    labels = ["first", "last", "abs diff x5"]
    for label, panel in zip(labels, panels, strict=True):
        panel.thumbnail((640, 360), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (640, 392), (8, 12, 14))
        tile.paste(panel, ((640 - panel.width) // 2, 0))
        ImageDraw.Draw(tile).text((12, 368), label, fill=(226, 234, 230))
        thumbs.append(tile)
    sheet = Image.new("RGB", (640 * 3, 392), (8, 12, 14))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, (idx * 640, 0))
    sheet.save(output_path, compress_level=4)
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {"image": output_path, "json": json_path, "metrics": metrics}


def evenly_spaced_indices(count: int, samples: int) -> list[int]:
    if count <= 1:
        return [0]
    return sorted({int(round(value)) for value in np.linspace(0, count - 1, samples)})


def run_batch(
    config: dict[str, Any],
    *,
    scratch: str | Path | None = None,
    settings: RenderSettings | None = None,
    workers: int | None = None,
    only: str | None = None,
    overwrite: bool = True,
) -> list[dict[str, Any]]:
    settings = settings or render_settings_from_config(config)
    worker_count = max(1, int(workers or os.cpu_count() or 1))
    batch_name = safe_name(str(config.get("batch_name", DEFAULT_CONFIG["batch_name"])))
    output_dir = resolve_scratch(scratch) / batch_name
    output_dir.mkdir(parents=True, exist_ok=True)
    variants = expand_variants(config)
    if only:
        wanted = safe_name(only)
        variants = [variant for variant in variants if safe_name(str(variant.get("name", ""))) == wanted]
        if not variants:
            raise ValueError(f"variant not found: {only}")
    results = []
    for variant in variants:
        results.append(render_variant(variant, settings, output_dir, workers=worker_count, overwrite=overwrite))
    summary_path = output_dir / "batch_summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote batch summary: {summary_path}", flush=True)
    return results


def benchmark_cpu(config: dict[str, Any], settings: RenderSettings, *, frame_count: int, workers: list[int]) -> list[dict[str, Any]]:
    variant = expand_variants(config)[0]
    frames = list(range(frame_count))
    rows: list[dict[str, Any]] = []

    serial_start = time.perf_counter()
    serial_checksums = [frame_checksum(variant, settings, frame_index) for frame_index in frames]
    serial_seconds = time.perf_counter() - serial_start
    rows.append(benchmark_row("serial", 1, frame_count, serial_seconds, settings, serial_checksums))

    for worker_count in workers:
        if worker_count <= 1:
            continue
        tasks = [(variant, settings, frame_index) for frame_index in frames]
        start = time.perf_counter()
        with ProcessPoolExecutor(max_workers=worker_count) as pool:
            checksums = list(pool.map(frame_checksum_task, tasks))
        seconds = time.perf_counter() - start
        rows.append(benchmark_row("multiprocessing", worker_count, frame_count, seconds, settings, checksums))
    return rows


def frame_checksum_task(task: tuple[dict[str, Any], RenderSettings, int]) -> int:
    variant, settings, frame_index = task
    return frame_checksum(variant, settings, frame_index)


def frame_checksum(variant: dict[str, Any], settings: RenderSettings, frame_index: int) -> int:
    frame = render_frame_array(variant, settings, frame_index)
    return int(frame[::64, ::64].sum())


def benchmark_row(
    mode: str,
    workers: int,
    frame_count: int,
    seconds: float,
    settings: RenderSettings,
    checksums: list[int],
) -> dict[str, Any]:
    pixels = settings.width * settings.height * frame_count
    return {
        "mode": mode,
        "workers": workers,
        "frames": frame_count,
        "seconds": round(seconds, 4),
        "frames_per_second": round(frame_count / max(seconds, 1e-9), 4),
        "megapixels_per_second": round((pixels / 1_000_000.0) / max(seconds, 1e-9), 3),
        "checksum": int(sum(checksums)),
    }


def benchmark_gpu_field(config: dict[str, Any], settings: RenderSettings, *, frame_count: int) -> dict[str, Any]:
    variant = expand_variants(config)[0]
    try:
        return benchmark_cupy_field(variant, settings, frame_count)
    except Exception as cupy_error:
        try:
            return benchmark_torch_cuda_field(variant, settings, frame_count, str(cupy_error))
        except Exception as torch_error:
            return {
                "status": "skipped",
                "reason": "No usable CuPy or PyTorch CUDA backend was available.",
                "cupy_error": str(cupy_error),
                "torch_cuda_error": str(torch_error),
            }


def benchmark_cupy_field(variant: dict[str, Any], settings: RenderSettings, frame_count: int) -> dict[str, Any]:
    import cupy as cp  # type: ignore[import-not-found]

    grid = get_grid(settings)
    x_np = grid["x"]
    y_np = grid["y"]
    assert isinstance(x_np, np.ndarray)
    assert isinstance(y_np, np.ndarray)
    x = cp.asarray(x_np)
    y = cp.asarray(y_np)
    seed = int(variant.get("seed", 0))
    source_count = max(2, int(variant.get("source_count", 7)))
    wavelength = float(variant.get("wavelength", 0.155))
    decay = float(variant.get("decay", 0.92))
    start = time.perf_counter()
    checksum_acc = cp.asarray(0.0, dtype=cp.float32)
    for frame_index in range(frame_count):
        phase = frame_index / max(1, frame_count)
        field = cp.zeros_like(x, dtype=cp.float32)
        for sx, sy, amp, source_phase in deterministic_sources(seed, source_count, phase):
            dx = x - sx
            dy = y - sy
            distance = cp.sqrt(dx * dx + dy * dy)
            wave = cp.cos((TAU / wavelength) * distance - TAU * phase + source_phase)
            falloff = cp.exp(-distance / max(0.05, decay))
            field += np.float32(amp) * wave * falloff
        checksum_acc = checksum_acc + cp.mean(field)
    cp.cuda.Stream.null.synchronize()
    checksum = float(checksum_acc.get())
    seconds = time.perf_counter() - start
    pixels = int(grid["fw"]) * int(grid["fh"]) * frame_count
    return {
        "status": "ok",
        "backend": "cupy",
        "frames": frame_count,
        "field_resolution": [int(grid["fw"]), int(grid["fh"])],
        "seconds": round(seconds, 4),
        "megapixels_per_second": round((pixels / 1_000_000.0) / max(seconds, 1e-9), 3),
        "checksum": round(checksum, 6),
    }


def benchmark_torch_cuda_field(
    variant: dict[str, Any],
    settings: RenderSettings,
    frame_count: int,
    cupy_error: str,
) -> dict[str, Any]:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("torch.cuda.is_available() is false")

    grid = get_grid(settings)
    x_np = grid["x"]
    y_np = grid["y"]
    assert isinstance(x_np, np.ndarray)
    assert isinstance(y_np, np.ndarray)
    device = torch.device("cuda")
    x = torch.as_tensor(x_np, device=device)
    y = torch.as_tensor(y_np, device=device)
    seed = int(variant.get("seed", 0))
    source_count = max(2, int(variant.get("source_count", 7)))
    wavelength = float(variant.get("wavelength", 0.155))
    decay = float(variant.get("decay", 0.92))
    torch.cuda.synchronize()
    start = time.perf_counter()
    checksum_acc = torch.zeros((), device=device)
    for frame_index in range(frame_count):
        phase = frame_index / max(1, frame_count)
        field = torch.zeros_like(x)
        for sx, sy, amp, source_phase in deterministic_sources(seed, source_count, phase):
            dx = x - sx
            dy = y - sy
            distance = torch.sqrt(dx * dx + dy * dy)
            wave = torch.cos((TAU / wavelength) * distance - TAU * phase + source_phase)
            falloff = torch.exp(-distance / max(0.05, decay))
            field = field + float(amp) * wave * falloff
        checksum_acc = checksum_acc + torch.mean(field)
    torch.cuda.synchronize()
    checksum = float(checksum_acc.detach().cpu())
    seconds = time.perf_counter() - start
    pixels = int(grid["fw"]) * int(grid["fh"]) * frame_count
    return {
        "status": "ok",
        "backend": "torch_cuda",
        "cupy_error": cupy_error,
        "frames": frame_count,
        "field_resolution": [int(grid["fw"]), int(grid["fh"])],
        "seconds": round(seconds, 4),
        "megapixels_per_second": round((pixels / 1_000_000.0) / max(seconds, 1e-9), 3),
        "checksum": round(checksum, 6),
    }


def deterministic_sources(seed: int, source_count: int, phase: float) -> list[tuple[float, float, float, float]]:
    rng = np.random.default_rng(seed)
    rows: list[tuple[float, float, float, float]] = [(0.0, 0.0, 1.15, 0.0)]
    ring_count = source_count - 1
    rotation = 0.06 * math.sin(TAU * phase)
    breathe = 1.0 + 0.075 * math.sin(TAU * phase)
    for idx in range(ring_count):
        angle = rotation + TAU * idx / ring_count + float(rng.normal(0.0, 0.018))
        radius = 0.44 * breathe * (1.0 + float(rng.normal(0.0, 0.035)))
        rows.append(
            (
                math.cos(angle) * radius,
                math.sin(angle) * radius,
                0.72 + 0.16 * math.sin(idx * 1.7 + phase * TAU),
                idx * 0.41 + 0.22 * math.sin(TAU * phase + idx),
            )
        )
    return rows


def write_example_config(path: Path) -> None:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    config["variants"][0]["sweep"] = {
        "seed": [37, 91],
        "wavelength": [0.135, 0.155],
        "palette": ["deep_water", "ice_gold"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(path)


def parse_workers(value: str | None) -> list[int]:
    if not value:
        cpu = os.cpu_count() or 1
        return sorted({2, min(4, cpu), cpu})
    return [max(1, int(part)) for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render variants from a JSON config or the built-in default.")
    render.add_argument("--config", type=Path)
    render.add_argument("--scratch", type=Path)
    render.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    render.add_argument("--only", help="Render one expanded variant by name.")
    render.add_argument("--width", type=int)
    render.add_argument("--height", type=int)
    render.add_argument("--fps", type=int)
    render.add_argument("--duration", type=float)
    render.add_argument("--field-scale", type=float)
    render.add_argument("--crf", type=int)
    render.add_argument("--preset")
    render.add_argument("--discard-frames", action="store_true")
    render.add_argument("--no-overwrite", action="store_true")

    benchmark = sub.add_parser("benchmark", help="Benchmark serial vs multiprocessing frame evaluation.")
    benchmark.add_argument("--config", type=Path)
    benchmark.add_argument("--width", type=int, default=1920)
    benchmark.add_argument("--height", type=int, default=1080)
    benchmark.add_argument("--frames", type=int, default=32)
    benchmark.add_argument("--field-scale", type=float, default=0.375)
    benchmark.add_argument("--workers", help="Comma-separated worker counts, e.g. 2,4,8.")
    benchmark.add_argument("--json-out", type=Path)

    gpu = sub.add_parser("gpu-benchmark", help="Optional CuPy/PyTorch CUDA field-evaluation proof-of-concept.")
    gpu.add_argument("--config", type=Path)
    gpu.add_argument("--width", type=int, default=3840)
    gpu.add_argument("--height", type=int, default=2160)
    gpu.add_argument("--frames", type=int, default=32)
    gpu.add_argument("--field-scale", type=float, default=0.375)
    gpu.add_argument("--json-out", type=Path)

    example = sub.add_parser("write-example-config", help="Write a JSON sweep config template.")
    example.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "write-example-config":
        write_example_config(args.path)
        return 0

    config = load_config(args.config)
    if args.command == "render":
        settings = render_settings_from_config(config, args)
        run_batch(
            config,
            scratch=args.scratch,
            settings=settings,
            workers=args.workers,
            only=args.only,
            overwrite=not args.no_overwrite,
        )
        return 0

    if args.command == "benchmark":
        settings = RenderSettings(
            width=args.width,
            height=args.height,
            fps=24,
            duration_seconds=max(1.0, args.frames / 24.0),
            field_scale=args.field_scale,
            crf=18,
            preset="veryfast",
            keep_frames=True,
        )
        rows = benchmark_cpu(config, settings, frame_count=args.frames, workers=parse_workers(args.workers))
        text = json.dumps(rows, indent=2)
        print(text)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(text + "\n", encoding="utf-8")
        return 0

    if args.command == "gpu-benchmark":
        settings = RenderSettings(
            width=args.width,
            height=args.height,
            fps=24,
            duration_seconds=max(1.0, args.frames / 24.0),
            field_scale=args.field_scale,
            crf=18,
            preset="veryfast",
            keep_frames=True,
        )
        result = benchmark_gpu_field(config, settings, frame_count=args.frames)
        text = json.dumps(result, indent=2)
        print(text)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(text + "\n", encoding="utf-8")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
