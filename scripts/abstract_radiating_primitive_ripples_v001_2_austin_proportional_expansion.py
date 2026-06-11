#!/usr/bin/env python3
"""
abstract_radiating_primitive_ripples_v001_2_austin_proportional_expansion

v001.2 — Austin feedback 2026-05-24: proportional expansion of crescent↔trigon gap
as radial position grows. Generated Austin-style / Coast Salish-style primitive phrase ripple layer for
internal/show-development use, pending Austin review.

This is an authored beauty/render-library candidate, not a research proof and
not a claim about physical origins of Coast Salish forms. The motion borrows
the feel of soft radiating pond ripples; the circle/crescent/trigon vocabulary
is intentionally styled.

Default outputs:
  track2-deterministic/morph_outputs_INTERNAL/
    abstract_radiating_primitive_ripples_v001_1_orientation_polish_2026-05-23/
      abstract_radiating_primitive_ripples_v001_1_orientation_polish_overlay_black.mp4
      abstract_radiating_primitive_ripples_v001_1_orientation_polish_alpha_prores4444.mov
      abstract_radiating_primitive_ripples_v001_1_orientation_polish_over_moonfish-water.mp4
      abstract_radiating_primitive_ripples_v001_1_orientation_polish_contact_sheet.png
      README.md
      manifest.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "abstract_radiating_primitive_ripples_v001_2_austin_proportional_expansion"
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / f"{PROJECT}_2026-05-24"
)

REFERENCE_CLIP = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_flow_phrase_grammar_v002b_2026-05-22"
    / "waterfall_vertical_phrase_v002__over_moonfish-water.mp4"
)
REFERENCE_COMPOSITE_60S = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_flow_phrase_grammar_v002b_2026-05-22"
    / "waterfall_vertical_phrase_v002_60s__over_moonfish-water.mp4"
)
MOONFISH_FOOTAGE = (
    ROOT / "media" / "collaborators" / "moonfish-video" / "underwater" / "P1099653.mp4"
)

OUTPUT_W = 3840
OUTPUT_H = 2160
RENDER_SCALE = 1.0 / 3.0
W = int(OUTPUT_W * RENDER_SCALE)
H = int(OUTPUT_H * RENDER_SCALE)
FPS = 24
DEFAULT_DURATION_SECONDS = 60.0
DEFAULT_FRAMES = int(round(DEFAULT_DURATION_SECONDS * FPS))
TAU = math.tau

# Glow and tone-map tuned for projection readability: soft, but not washed out.
GLOW_TIGHT = 18.0 * RENDER_SCALE
GLOW_WIDE = 54.0 * RENDER_SCALE
EXPOSURE = 1.42
POST_GAMMA = 1.0 / 1.32

COL_CREAM = np.array([0.98, 0.90, 0.70], np.float32)
COL_TEAL = np.array([0.36, 0.92, 0.88], np.float32)
COL_CORAL = np.array([0.96, 0.45, 0.34], np.float32)
COL_RED = np.array([0.72, 0.20, 0.18], np.float32)
COL_OCHRE = np.array([0.92, 0.66, 0.28], np.float32)
COL_WATER_GUIDE = np.array([0.10, 0.32, 0.46], np.float32)
COL_MOON_BLUE = np.array([0.22, 0.62, 0.78], np.float32)


@dataclass(frozen=True)
class RippleSystem:
    origin_xy: tuple[float, float]
    count: int
    phase: float
    max_radius: float
    angle_offset: float
    cycle_seconds: float
    crescent_size: float
    trigon_size: float
    intensity: float
    palette_shift: int
    note: str


SYSTEMS: tuple[RippleSystem, ...] = (
    RippleSystem((0.285, 0.455), 10, 0.00, 1300.0, 0.10, 15.0, 92.0, 76.0, 0.93, 0, "left-center broad pond ripple"),
    RippleSystem((0.670, 0.365), 8, 0.27, 1420.0, 0.42, 15.0, 98.0, 82.0, 0.86, 1, "upper-right slow crossing ripple"),
    RippleSystem((0.455, 0.730), 12, 0.52, 1180.0, -0.14, 15.0, 82.0, 70.0, 0.76, 2, "low-center soft dense ring"),
    RippleSystem((0.825, 0.640), 7, 0.74, 1050.0, 0.28, 15.0, 88.0, 74.0, 0.72, 3, "right-edge partial ripple"),
)

CONTACT_TIMES_SECONDS = (0.0, 6.0, 12.0, 18.0, 24.0, 30.0, 36.0, 42.0, 48.0, 54.0, 59.0)


def smoothstep(e0: float, e1: float, x: float | np.ndarray) -> float | np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ease_out_sine(x: float) -> float:
    return math.sin((math.pi * 0.5) * float(np.clip(x, 0.0, 1.0)))


def ease_in_out(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


def life_window(q: float, edge: float = 0.075) -> float:
    return float(smoothstep(0.0, edge, q) * smoothstep(1.0, 1.0 - edge, q))


def _box(cx: float, cy: float, reach: float) -> tuple[int, int, int, int]:
    x0 = max(0, int(math.floor(cx - reach)))
    x1 = min(W, int(math.ceil(cx + reach)))
    y0 = max(0, int(math.floor(cy - reach)))
    y1 = min(H, int(math.ceil(cy + reach)))
    return x0, y0, x1, y1


def _local(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    cx: float,
    cy: float,
) -> tuple[np.ndarray, np.ndarray]:
    lx = (np.arange(x0, x1, dtype=np.float32) + 0.5) - np.float32(cx)
    ly = (np.arange(y0, y1, dtype=np.float32) + 0.5) - np.float32(cy)
    return lx[None, :], ly[:, None]


def _sdf_field(sdf: np.ndarray) -> np.ndarray:
    fill = smoothstep(2.1, -2.1, sdf)
    pos = np.maximum(sdf, 0.0)
    glow_tight = np.exp(-(pos / GLOW_TIGHT) ** 2)
    glow_wide = np.exp(-(pos / GLOW_WIDE) ** 2)
    return np.maximum(fill, np.maximum(0.48 * glow_tight, 0.11 * glow_wide)).astype(np.float32)


def _add(
    canvas: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    field: np.ndarray,
    color: np.ndarray,
    intensity: float,
) -> None:
    if intensity <= 0.001:
        return
    canvas[y0:y1, x0:x1, :] += field[:, :, None] * (color[None, None, :] * np.float32(intensity))


def draw_disc(
    canvas: np.ndarray,
    cx: float,
    cy: float,
    radius: float,
    color: np.ndarray,
    intensity: float,
) -> None:
    if intensity <= 0.002 or radius <= 0.5:
        return
    reach = radius + GLOW_WIDE * 2.4 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    sdf = np.sqrt(lx * lx + ly * ly) - np.float32(radius)
    _add(canvas, x0, y0, x1, y1, _sdf_field(sdf), color, intensity)


def draw_ring(
    canvas: np.ndarray,
    cx: float,
    cy: float,
    radius: float,
    thickness: float,
    color: np.ndarray,
    intensity: float,
) -> None:
    if intensity <= 0.002 or radius <= 0.5 or thickness <= 0.5:
        return
    reach = radius + thickness + GLOW_WIDE * 2.1 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    sdf = np.abs(np.sqrt(lx * lx + ly * ly) - np.float32(radius)) - np.float32(thickness)
    _add(canvas, x0, y0, x1, y1, _sdf_field(sdf), color, intensity)


def draw_crescent(
    canvas: np.ndarray,
    cx: float,
    cy: float,
    size: float,
    open_angle: float,
    color: np.ndarray,
    intensity: float,
) -> None:
    """Tapered arc blade. The concave cup opens toward open_angle."""
    if intensity <= 0.002 or size <= 0.5:
        return
    r_spine = size * 1.23
    half_span = 0.96
    half_thick = size * 0.34
    ccx = cx + r_spine * math.cos(open_angle)
    ccy = cy + r_spine * math.sin(open_angle)
    mid = open_angle + math.pi
    pad = half_thick + GLOW_WIDE * 2.3 + 5.0
    xs = [
        ccx + r_spine * math.cos(mid - half_span + (2.0 * half_span) * (k / 8.0))
        for k in range(9)
    ]
    ys = [
        ccy + r_spine * math.sin(mid - half_span + (2.0 * half_span) * (k / 8.0))
        for k in range(9)
    ]
    x0 = max(0, int(math.floor(min(xs) - pad)))
    x1 = min(W, int(math.ceil(max(xs) + pad)))
    y0 = max(0, int(math.floor(min(ys) - pad)))
    y1 = min(H, int(math.ceil(max(ys) + pad)))
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, ccx, ccy)
    rad = np.sqrt(lx * lx + ly * ly)
    theta = np.arctan2(ly, lx)
    dth = np.abs((theta - np.float32(mid) + math.pi) % TAU - math.pi)
    taper = np.clip(np.cos(np.clip(dth / half_span, 0.0, 1.0) * (math.pi / 2.0)), 0.0, 1.0)
    ht = np.float32(half_thick) * (taper ** 0.58)
    band = np.abs(rad - np.float32(r_spine)) - ht
    over = np.maximum(dth - np.float32(half_span), 0.0) * np.float32(r_spine)
    sdf = np.where(dth < half_span, band, np.sqrt(over * over + (rad - np.float32(r_spine)) ** 2))
    _add(canvas, x0, y0, x1, y1, _sdf_field(sdf), color, intensity)


def _triangle_sdf(px: np.ndarray, py: np.ndarray, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> np.ndarray:
    e0 = (p1[0] - p0[0], p1[1] - p0[1])
    e1 = (p2[0] - p1[0], p2[1] - p1[1])
    e2 = (p0[0] - p2[0], p0[1] - p2[1])
    v0x, v0y = px - p0[0], py - p0[1]
    v1x, v1y = px - p1[0], py - p1[1]
    v2x, v2y = px - p2[0], py - p2[1]

    def pq(vx: np.ndarray, vy: np.ndarray, e: tuple[float, float]) -> tuple[np.ndarray, np.ndarray]:
        d = e[0] * e[0] + e[1] * e[1]
        t = np.clip((vx * e[0] + vy * e[1]) / d, 0.0, 1.0)
        return vx - e[0] * t, vy - e[1] * t

    pq0x, pq0y = pq(v0x, v0y, e0)
    pq1x, pq1y = pq(v1x, v1y, e1)
    pq2x, pq2y = pq(v2x, v2y, e2)
    s = math.copysign(1.0, e0[0] * e2[1] - e0[1] * e2[0])
    dx = np.minimum(
        np.minimum(pq0x * pq0x + pq0y * pq0y, pq1x * pq1x + pq1y * pq1y),
        pq2x * pq2x + pq2y * pq2y,
    )
    c0 = s * (v0x * e0[1] - v0y * e0[0])
    c1 = s * (v1x * e1[1] - v1y * e1[0])
    c2 = s * (v2x * e2[1] - v2y * e2[0])
    dy = np.minimum(np.minimum(c0, c1), c2)
    return -np.sqrt(np.maximum(dx, 0.0)) * np.sign(dy)


def _edge_bite(
    px: np.ndarray,
    py: np.ndarray,
    va: tuple[float, float],
    vb: tuple[float, float],
    g: tuple[float, float],
    bite: float,
) -> np.ndarray:
    mx, my = (va[0] + vb[0]) * 0.5, (va[1] + vb[1]) * 0.5
    ex, ey = vb[0] - va[0], vb[1] - va[1]
    el = math.hypot(ex, ey)
    nx, ny = ey / el, -ex / el
    if nx * (mx - g[0]) + ny * (my - g[1]) < 0.0:
        nx, ny = -nx, -ny
    d_off = 1.35 * el
    ccx, ccy = mx + nx * d_off, my + ny * d_off
    r = d_off + bite
    return r - np.sqrt((px - np.float32(ccx)) ** 2 + (py - np.float32(ccy)) ** 2)


def draw_trigon(
    canvas: np.ndarray,
    cx: float,
    cy: float,
    size: float,
    point_angle: float,
    color: np.ndarray,
    intensity: float,
    concavity: float = 0.16,
) -> None:
    """Concave-sided arc-bounded trigon with the elongated head pointing outward."""
    if intensity <= 0.002 or size <= 0.5:
        return
    reach = size * 1.35 + GLOW_WIDE * 2.3 + 5.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    ca, sa = math.cos(point_angle), math.sin(point_angle)
    rx = np.float32(ca) * lx + np.float32(sa) * ly
    ry = -np.float32(sa) * lx + np.float32(ca) * ly
    v0 = (1.16 * size, 0.0)
    v1 = (-0.74 * size, 0.62 * size)
    v2 = (-0.74 * size, -0.62 * size)
    g = ((v0[0] + v1[0] + v2[0]) / 3.0, 0.0)
    sdf = _triangle_sdf(rx, ry, v0, v1, v2)
    bite = concavity * size
    for va, vb in ((v0, v1), (v1, v2), (v2, v0)):
        sdf = np.maximum(sdf, _edge_bite(rx, ry, va, vb, g, bite))
    _add(canvas, x0, y0, x1, y1, _sdf_field(sdf), color, intensity)


def tonemap(canvas: np.ndarray) -> np.ndarray:
    x = 1.0 - np.exp(-np.maximum(canvas, 0.0) * np.float32(EXPOSURE))
    x = np.power(np.clip(x, 0.0, 1.0), np.float32(POST_GAMMA))
    return (x * 255.0 + 0.5).astype(np.uint8)


def _palette(system: RippleSystem, ring: str) -> np.ndarray:
    palettes = (
        {"circle": COL_CREAM, "crescent": COL_TEAL, "trigon": COL_CORAL},
        {"circle": COL_OCHRE, "crescent": COL_CREAM, "trigon": COL_TEAL},
        {"circle": COL_CREAM, "crescent": COL_MOON_BLUE, "trigon": COL_OCHRE},
        {"circle": COL_TEAL, "crescent": COL_CREAM, "trigon": COL_RED},
    )
    return palettes[system.palette_shift % len(palettes)][ring]


def render_ripple_system(canvas: np.ndarray, system: RippleSystem, frame_index: int, n_frames: int) -> None:
    t = frame_index / FPS
    px = RENDER_SCALE
    max_radius = system.max_radius * px
    crescent_size_base = system.crescent_size * px
    trigon_size_base = system.trigon_size * px
    ox = system.origin_xy[0] * W
    oy = system.origin_xy[1] * H

    # Three staggered phrase waves per origin. Each wave is a nested cell set:
    # circle ripple -> inward-cupping crescent -> close outward trigon.
    layers = (
        (0.00, 1.00, 1.00, 0.00),
        (0.19, 0.62, 1.10, 0.17),
        (0.38, 0.38, 1.22, -0.11),
    )
    for layer_index, (delay, alpha_scale, radius_scale, angle_jitter) in enumerate(layers):
        q = ((t / system.cycle_seconds) + system.phase - delay) % 1.0
        base_win = life_window(q)
        if base_win <= 0.002:
            continue

        breathe = 1.0 + 0.060 * math.sin(TAU * (q * 2.0 + system.phase * 1.7 + layer_index * 0.23))
        wave_soft = 1.0 + 0.075 * layer_index

        # 1. Circular ripple. Later waves are wider, softer, and dimmer.
        circle_t = float(np.clip(q / 0.62, 0.0, 1.0))
        circle_fade = smoothstep(0.00, 0.08, q) * smoothstep(0.76, 0.50, q) * alpha_scale
        circle_r = (
            (24.0 + circle_t * 250.0 * radius_scale)
            * px
            * (0.98 + 0.045 * math.sin(TAU * (q * 2.4 + layer_index * 0.19)))
        )
        if circle_fade > 0.002:
            draw_ring(
                canvas,
                ox,
                oy,
                circle_r,
                (7.5 + 3.0 * (1.0 - circle_t)) * px * wave_soft,
                _palette(system, "circle"),
                system.intensity * 0.78 * circle_fade,
            )
            if q < 0.15 and layer_index == 0:
                draw_disc(
                    canvas,
                    ox,
                    oy,
                    (17.0 + 17.0 * circle_t) * px,
                    _palette(system, "circle"),
                    system.intensity * 0.32 * circle_fade,
                )

        # 2/3. Adjacent crescent+trigon cells riding the same radial phrase.
        cell_t = (q - 0.13) / 0.74
        if not (0.0 <= cell_t <= 1.0):
            continue

        cell_win = smoothstep(0.0, 0.12, cell_t) * smoothstep(1.0, 0.76, cell_t)
        distance_fade = 1.0 - 0.50 * ease_out_sine(cell_t)
        c_intensity = system.intensity * 0.76 * alpha_scale * cell_win * distance_fade
        t_intensity = system.intensity * 0.62 * alpha_scale * cell_win * (distance_fade ** 1.08)
        cell_r = (
            (136.0 * px)
            + ease_out_sine(cell_t) * (max_radius * 0.66 * radius_scale)
            + 8.0 * px * math.sin(TAU * (q * 1.8 + layer_index * 0.21))
        )

        for k in range(system.count):
            theta0 = TAU * (k / system.count) + system.angle_offset + angle_jitter
            wobble_phase = q * 1.12 + k * 0.137 + system.phase + layer_index * 0.31
            theta = theta0 + 0.030 * math.sin(TAU * wobble_phase)
            radial_wobble = 13.0 * px * math.sin(TAU * (q * 1.5 + k * 0.091 + layer_index * 0.29))
            radius_here = cell_r + radial_wobble
            cx = ox + math.cos(theta) * radius_here
            cy = oy + math.sin(theta) * radius_here
            size = (
                crescent_size_base
                * wave_soft
                * breathe
                * (0.92 + 0.09 * math.sin(TAU * (q * 2.0 + k / system.count + layer_index * 0.17)))
            )
            # Critical v001.1 polish: inward-facing cup. open_angle=theta+pi
            # cradles the previous circle/arc instead of facing away from it.
            draw_crescent(canvas, cx, cy, size, theta + math.pi, _palette(system, "crescent"), c_intensity)

            # Austin feedback 2026-05-24: the (crescent↔trigon) gap should expand
            # in proportion as the crescent radiates outward from origin. v001.1
            # used a fixed gap based only on shape sizes; v001.2 adds a proportional
            # term so the trigon "breathes" further out as the system radiates.
            #
            # The max() preserves v001.1's close-spacing at very small radii
            # (avoids overlap during the first 10-15% of the ripple lifecycle).
            TRI_GAP_PROPORTION = 0.30  # tunable
            tri_gap = max(
                size * 0.82 + trigon_size_base * 0.33,
                radius_here * TRI_GAP_PROPORTION,
            )
            tx = ox + math.cos(theta) * (radius_here + tri_gap)
            ty = oy + math.sin(theta) * (radius_here + tri_gap)
            tri_size = (
                trigon_size_base
                * wave_soft
                * breathe
                * (0.95 + 0.07 * math.sin(TAU * (q * 1.7 + k / max(1, system.count - 1) + layer_index * 0.13)))
            )
            draw_trigon(canvas, tx, ty, tri_size, theta, _palette(system, "trigon"), t_intensity)


def render_overlay_frame(frame_index: int, n_frames: int) -> np.ndarray:
    canvas = np.zeros((H, W, 3), np.float32)
    # Very faint periodic shimmer keeps the black overlay alive when screened,
    # while remaining safe for alpha extraction.
    for system in SYSTEMS:
        render_ripple_system(canvas, system, frame_index, n_frames)
    return tonemap(canvas)


def _encoder_rgb_mp4(out_path: Path) -> subprocess.Popen[bytes]:
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{W}x{H}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-vf",
        f"scale={OUTPUT_W}:{OUTPUT_H}:flags=lanczos",
        "-c:v",
        "h264_videotoolbox",
        "-b:v",
        "55M",
        "-maxrate",
        "80M",
        "-bufsize",
        "120M",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def _encoder_rgba_prores(out_path: Path) -> subprocess.Popen[bytes]:
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgba",
        "-video_size",
        f"{W}x{H}",
        "-framerate",
        str(FPS),
        "-i",
        "pipe:0",
        "-vf",
        f"scale={OUTPUT_W}:{OUTPUT_H}:flags=lanczos,format=yuva444p10le",
        "-c:v",
        "prores_ks",
        "-profile:v",
        "4444",
        "-pix_fmt",
        "yuva444p10le",
        str(out_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def close_encoder(proc: subprocess.Popen[bytes], label: str) -> None:
    if proc.stdin:
        proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        err = b""
        if proc.stderr:
            err = proc.stderr.read()
        raise RuntimeError(f"ffmpeg encoder failed for {label}:\n{err.decode('utf-8', 'replace')}")


def frame_difference(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    d = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return {
        "mean_abs_rgb_0_255": float(d.mean()),
        "p95_abs_rgb_0_255": float(np.percentile(d, 95)),
        "max_abs_rgb_0_255": float(d.max()),
    }


def render_overlay_and_alpha(outdir: Path, n_frames: int, render_alpha: bool) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    stills_dir = outdir / "stills"
    stills_dir.mkdir(exist_ok=True)

    overlay_path = outdir / f"{PROJECT}_overlay_black.mp4"
    alpha_path = outdir / f"{PROJECT}_alpha_prores4444.mov"
    contact_frame_indices = {
        min(n_frames - 1, max(0, int(round(t * FPS)))): t
        for t in CONTACT_TIMES_SECONDS
        if t < n_frames / FPS
    }
    contact_frame_indices[n_frames - 1] = (n_frames - 1) / FPS

    proc_rgb = _encoder_rgb_mp4(overlay_path)
    proc_alpha = _encoder_rgba_prores(alpha_path) if render_alpha else None

    first_frame: np.ndarray | None = None
    final_frame: np.ndarray | None = None
    saved_stills: list[dict[str, Any]] = []
    t0 = time.time()

    try:
        for frame_index in range(n_frames):
            rgb = render_overlay_frame(frame_index, n_frames)
            if frame_index == 0:
                first_frame = rgb.copy()
                Image.fromarray(rgb).save(stills_dir / "overlay_first_frame.png")
            if frame_index == n_frames - 1:
                final_frame = rgb.copy()
                Image.fromarray(rgb).save(stills_dir / "overlay_final_frame.png")
            if frame_index in contact_frame_indices:
                seconds = contact_frame_indices[frame_index]
                path = stills_dir / f"overlay_t{seconds:05.2f}.png"
                Image.fromarray(rgb).save(path)
                saved_stills.append({"time_seconds": seconds, "path": str(path.relative_to(outdir))})

            proc_rgb.stdin.write(rgb.tobytes())  # type: ignore[union-attr]
            if proc_alpha is not None:
                alpha = rgb.max(axis=2, keepdims=True).astype(np.uint8)
                rgba = np.concatenate([rgb, alpha], axis=2)
                proc_alpha.stdin.write(rgba.tobytes())  # type: ignore[union-attr]

            if (frame_index + 1) % 120 == 0:
                elapsed = time.time() - t0
                print(f"  rendered {frame_index + 1}/{n_frames} frames ({elapsed:.1f}s)")
    finally:
        close_encoder(proc_rgb, "black overlay MP4")
        if proc_alpha is not None:
            close_encoder(proc_alpha, "alpha ProRes 4444 MOV")

    if first_frame is None or final_frame is None:
        raise RuntimeError("missing first/final frames for seam check")

    return {
        "overlay_path": overlay_path,
        "alpha_path": alpha_path if render_alpha else None,
        "saved_stills": saved_stills,
        "seam_check": frame_difference(first_frame, final_frame),
        "elapsed_seconds": time.time() - t0,
    }


def make_composite(layer_mp4: Path, outdir: Path, n_frames: int) -> Path | None:
    background = REFERENCE_COMPOSITE_60S if REFERENCE_COMPOSITE_60S.is_file() else MOONFISH_FOOTAGE
    if not background.is_file():
        print(f"  composite skipped: missing footage {background}")
        return None

    duration = n_frames / FPS
    out_mp4 = outdir / f"{PROJECT}_over_moonfish-water.mp4"
    if background == REFERENCE_COMPOSITE_60S:
        bg_filter = (
            f"scale={OUTPUT_W}:{OUTPUT_H}:flags=lanczos,fps={FPS},"
            f"trim=duration={duration:.6f},setpts=PTS-STARTPTS,"
            f"eq=brightness=-0.025:contrast=1.02:saturation=1.04,format=gbrp[bg]"
        )
        input_args = ["-stream_loop", "-1", "-i", str(background)]
        layer_opacity = 0.62
    else:
        crop = "crop=1770:996:75:0,scale=3840:2160:flags=lanczos"
        bg_filter = (
            f"{crop},fps={FPS},trim=duration={duration:.6f},setpts=PTS-STARTPTS,"
            f"eq=brightness=-0.085:contrast=1.035:saturation=1.04,format=gbrp[bg]"
        )
        input_args = ["-ss", "4.0", "-i", str(background)]
        layer_opacity = 0.68
    fc = (
        f"[0:v]{bg_filter};"
        f"[1:v]fps={FPS},trim=duration={duration:.6f},setpts=PTS-STARTPTS,format=gbrp,"
        f"colorchannelmixer=rr={layer_opacity}:gg={layer_opacity}:bb={layer_opacity}[lay];"
        f"[bg][lay]blend=all_mode=addition:shortest=1,format=yuv420p[out]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        *input_args,
        "-i",
        str(layer_mp4),
        "-filter_complex",
        fc,
        "-map",
        "[out]",
        "-t",
        f"{duration:.6f}",
        "-c:v",
        "h264_videotoolbox",
        "-b:v",
        "70M",
        "-maxrate",
        "95M",
        "-bufsize",
        "140M",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    normalize_mp4_timescale(out_mp4)
    return out_mp4


def normalize_mp4_timescale(mp4_path: Path) -> None:
    tmp = mp4_path.with_name(f"{mp4_path.stem}__timescale_tmp{mp4_path.suffix}")
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(mp4_path),
        "-c",
        "copy",
        "-video_track_timescale",
        str(FPS),
        str(tmp),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    tmp.replace(mp4_path)


def run_ffprobe(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-count_frames",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames",
        "-show_entries",
        "format=duration,size,format_name",
        "-of",
        "json",
        str(path),
    ]
    data = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    stream = data["streams"][0]
    fmt = data["format"]
    return {
        "path": str(path),
        "codec_name": stream.get("codec_name"),
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "pix_fmt": stream.get("pix_fmt"),
        "r_frame_rate": stream.get("r_frame_rate"),
        "avg_frame_rate": stream.get("avg_frame_rate"),
        "nb_read_frames": int(stream.get("nb_read_frames", 0)),
        "duration": float(fmt.get("duration", 0.0)),
        "format_name": fmt.get("format_name"),
        "size_bytes": int(fmt.get("size", path.stat().st_size)),
    }


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def extract_composite_stills(composite_path: Path, outdir: Path, n_frames: int) -> list[dict[str, Any]]:
    stills_dir = outdir / "stills"
    duration = n_frames / FPS
    times = [t for t in CONTACT_TIMES_SECONDS[:6] if t < duration]
    records: list[dict[str, Any]] = []
    for seconds in times:
        path = stills_dir / f"composite_t{seconds:05.2f}.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{seconds:.6f}",
            "-i",
            str(composite_path),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        records.append({"time_seconds": seconds, "path": str(path.relative_to(outdir))})
    return records


def build_contact_sheet(
    outdir: Path,
    overlay_stills: list[dict[str, Any]],
    composite_stills: list[dict[str, Any]],
) -> Path:
    cell_w, cell_h = 640, 360
    cols = 6
    rows = 2
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    title_font = _load_font(22)
    small_font = _load_font(16)

    panels: list[tuple[str, dict[str, Any]]] = []
    for rec in composite_stills[:cols]:
        panels.append(("composite", rec))
    for rec in overlay_stills[:cols]:
        panels.append(("overlay alpha/source", rec))

    for idx, (label, rec) in enumerate(panels[: rows * cols]):
        px = (idx % cols) * cell_w
        py = (idx // cols) * cell_h
        img = Image.open(outdir / rec["path"]).convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        sheet.paste(img, (px, py))
        seconds = float(rec["time_seconds"])
        text = f"{label}  t={seconds:04.1f}s"
        draw.rectangle((px, py, px + cell_w, py + 36), fill=(0, 0, 0))
        draw.text((px + 12, py + 7), text, font=title_font, fill=(232, 240, 238))

    footer = "internal/show-development pending Austin review | generated radiating primitive phrase, not physics proof"
    draw.rectangle((0, rows * cell_h - 26, cols * cell_w, rows * cell_h), fill=(0, 0, 0))
    draw.text((14, rows * cell_h - 22), footer, font=small_font, fill=(170, 195, 198))
    outpath = outdir / f"{PROJECT}_contact_sheet.png"
    sheet.save(outpath)
    return outpath


def write_readme(outdir: Path, manifest: dict[str, Any]) -> Path:
    outputs = manifest["outputs"]
    specs = manifest["render_specs"]
    seam = manifest["loop_seam_check"]
    lines = [
        f"# {PROJECT}",
        "",
        "INTERNAL / SHOW-DEVELOPMENT ONLY, pending Austin review.",
        "",
        "Austin has authorized Austin-style / Coast Salish-style generated experiments for internal/show-development use. Austin remains the authority on meaning and final public use.",
        "",
        "## Visual Intent",
        "",
        "A loopable UHD visual layer where authored primitive syntax behaves like soft pond ripples on dark water. Each ripple event starts from an origin point, then radiates as nested circle / inward-cupping crescent / outward trigon phrase cells.",
        "",
        "This is a beauty/render library candidate. It is not a research proof and does not claim physical origins of Coast Salish forms.",
        "",
        "## Source References",
        "",
        f"- Mood/reference clip: `{REFERENCE_CLIP.relative_to(ROOT)}`",
        f"- Preferred moonfish/water composite base: `{REFERENCE_COMPOSITE_60S.relative_to(ROOT)}`",
        f"- Fallback raw moonfish/water footage: `{MOONFISH_FOOTAGE.relative_to(ROOT)}`",
        "",
        "## Render Specs",
        "",
        f"- Resolution: {specs['width']}x{specs['height']}",
        f"- Frame rate: {specs['fps']} fps",
        f"- Duration: {specs['duration_seconds']:.3f}s",
        f"- Frames: {specs['frame_count']}",
        "- Motion: authored radial ripple phrases, staggered across four origins with three delayed phrase layers per origin",
        "- Palette: dark water blues with cream, teal, coral, muted red, and soft ochre accents",
        "",
        "## Outputs",
        "",
    ]
    for key, info in outputs.items():
        if info is None:
            lines.append(f"- {key}: not generated")
            continue
        probe = info.get("ffprobe")
        if probe:
            lines.append(
                f"- {key}: `{Path(info['path']).name}` "
                f"({probe['width']}x{probe['height']}, {probe['r_frame_rate']}, "
                f"{probe['duration']:.3f}s, {probe['codec_name']}, {probe['pix_fmt']})"
            )
        else:
            lines.append(f"- {key}: `{Path(info['path']).name}`")
    lines += [
        "",
        "## Shape Notes",
        "",
        "- Crescents are tapered arc blades with two arc-bounded sides and sharp cusps; their concave cups face inward toward the parent circle/arc.",
        "- Trigons are generated as concave-sided, arc-bounded directional heads; they point outward but sit close to the crescent outer edge so the cell reads as adjacent phrase syntax.",
        "- v001.1 fixes the v001 crescent orientation error by using `open_angle = theta + pi` for radial crescent cells.",
        "- The primitive vocabulary is authored/styled. The ripple timing is used as movement language, not as a derivation model.",
        "",
        "## Loop Seam",
        "",
        f"- First/final overlay-frame mean absolute RGB delta: {seam['mean_abs_rgb_0_255']:.4f} / 255",
        f"- 95th percentile delta: {seam['p95_abs_rgb_0_255']:.4f} / 255",
        f"- Max channel delta: {seam['max_abs_rgb_0_255']:.1f} / 255",
        "- The animation is phase-periodic over the full duration; the final frame is the normal preceding frame before returning to frame 0.",
        "",
        "## Boundary",
        "",
        "For internal/show-development review only. Do not present this as Austin-approved public cultural grammar, and do not present it as proving a physical or wave-interference origin of Coast Salish forms.",
        "",
    ]
    path = outdir / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_manifest(outdir: Path, manifest: dict[str, Any]) -> Path:
    path = outdir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def nonempty_file(path: Path | None) -> bool:
    return bool(path and path.is_file() and path.stat().st_size > 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render authored radial primitive ripples for show-development use.")
    parser.add_argument("--outdir", type=Path, default=OUT_DIR)
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--frames", type=int, default=None, help="Override frame count; duration becomes frames / 24.")
    parser.add_argument("--skip-alpha", action="store_true", help="Skip ProRes 4444 alpha MOV.")
    parser.add_argument("--skip-composite", action="store_true", help="Skip Moonfish/water composite.")
    args = parser.parse_args()

    n_frames = args.frames if args.frames is not None else int(round(args.duration * FPS))
    duration = n_frames / FPS
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"== {PROJECT} ==")
    print(f"  outdir:   {outdir}")
    print(f"  output:   {OUTPUT_W}x{OUTPUT_H}, {FPS}fps, {n_frames} frames ({duration:.3f}s)")
    print(f"  work:     {W}x{H} raster, lanczos upscale to UHD")
    print(f"  alpha:    {'no' if args.skip_alpha else 'yes, ProRes 4444'}")
    print(f"  composite:{' no' if args.skip_composite else ' yes, moonfish/water'}")

    render_result = render_overlay_and_alpha(outdir, n_frames, not args.skip_alpha)
    composite_path: Path | None = None
    composite_stills: list[dict[str, Any]] = []
    if not args.skip_composite:
        print("  building moonfish/water composite")
        composite_path = make_composite(render_result["overlay_path"], outdir, n_frames)
        if composite_path is not None:
            composite_stills = extract_composite_stills(composite_path, outdir, n_frames)

    contact_sheet_path = build_contact_sheet(outdir, render_result["saved_stills"], composite_stills)

    output_records: dict[str, Any] = {}
    overlay_path = Path(render_result["overlay_path"])
    alpha_path = Path(render_result["alpha_path"]) if render_result["alpha_path"] else None
    for key, path in (
        ("black_background_overlay_mp4", overlay_path),
        ("alpha_mov", alpha_path),
        ("moonfish_water_composite_mp4", composite_path),
        ("contact_sheet", contact_sheet_path),
    ):
        if path is None:
            output_records[key] = None
            continue
        rec: dict[str, Any] = {"path": str(path), "size_bytes": path.stat().st_size}
        if path.suffix.lower() in {".mp4", ".mov"}:
            rec["ffprobe"] = run_ffprobe(path)
        output_records[key] = rec

    manifest: dict[str, Any] = {
        "project": PROJECT,
        "date": "2026-05-23",
        "status": "internal/show-development pending Austin review",
        "classification": "beauty/render library candidate, not a research proof",
        "render_specs": {
            "width": OUTPUT_W,
            "height": OUTPUT_H,
            "fps": FPS,
            "duration_seconds": duration,
            "frame_count": n_frames,
            "work_width": W,
            "work_height": H,
            "work_to_output_scale": OUTPUT_W / W,
        },
        "visual_intent": "Austin-style / Coast Salish-style authored primitive syntax radiating like soft pond ripples, with inward-cupping crescents nested against parent circles/arcs.",
        "source_references": {
            "mood_reference_clip": str(REFERENCE_CLIP),
            "preferred_composite_base": str(REFERENCE_COMPOSITE_60S),
            "moonfish_water_footage": str(MOONFISH_FOOTAGE),
        },
        "orientation_polish": {
            "crescent_radial_open_angle": "theta + pi",
            "crescent_orientation": "concave cup faces inward toward parent circle/ripple arc",
            "trigon_orientation": "points outward and sits close to the crescent outer edge",
            "phrase_layers_per_origin": 3,
        },
        "boundary": "Internal/show-development only. Austin remains authority on meaning and final public use. This does not claim physical origins of Coast Salish forms.",
        "ripple_systems": [asdict(s) for s in SYSTEMS],
        "loop_seam_check": render_result["seam_check"],
        "alpha_fallback_note": "ProRes 4444 alpha MOV generated via ffmpeg prores_ks when alpha_mov is present; black-background MP4 remains suitable for Resolume Screen/Add blend.",
        "outputs": output_records,
        "nonempty_outputs": {
            key: None if info is None else bool(Path(info["path"]).is_file() and Path(info["path"]).stat().st_size > 0)
            for key, info in output_records.items()
        },
        "render_elapsed_seconds": render_result["elapsed_seconds"],
    }

    manifest_path = write_manifest(outdir, manifest)
    readme_path = write_readme(outdir, manifest)
    print(f"  contact:  {contact_sheet_path}")
    print(f"  manifest: {manifest_path}")
    print(f"  readme:   {readme_path}")

    missing = [key for key, ok in manifest["nonempty_outputs"].items() if ok is False]
    if missing:
        raise RuntimeError(f"missing or empty outputs: {missing}")


if __name__ == "__main__":
    main()
