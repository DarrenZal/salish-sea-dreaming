#!/usr/bin/env python3.11
"""
Heightfield + SDF water glyph proof v002.

Internal water-only substrate proofs:
  - no object-like glyph phrases, paired eye circles, fish, birds, figures, or flocking
  - circle / crescent / trigon SDFs are embedded into a moving water heightfield
  - normals are recomputed after embedding, then glyph color is refracted/shaded through water

This is deliberately separate from v001 and from primitive_water_membrane_v6.py.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from primitive_water_grammar_v1 import H264Writer, N_FRAMES, ROOT, W, H


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/heightfield_sdf_water_glyph_v002_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
GRAMMAR_PATH = ROOT / "track2-deterministic/primitive_grammar/grammar_v001.json"
FPS = 24

# Internal shader-frame resolution. Output remains 1920x1080.
RW = 384
RH = 216
ASPECT = W / H

X_AXIS = (np.linspace(0.0, 1.0, RW, dtype=np.float32) - 0.5) * ASPECT
Y_AXIS = (np.linspace(0.0, 1.0, RH, dtype=np.float32) - 0.5)
X, Y = np.meshgrid(X_AXIS, Y_AXIS)
DX = float(X_AXIS[1] - X_AXIS[0])
DY = float(Y_AXIS[1] - Y_AXIS[0])


@dataclass(frozen=True)
class ClipResult:
    filename: str
    test: str
    method: str
    caveat: str


def hex_to_rgb01(value: str) -> np.ndarray:
    value = value.strip().lstrip("#")
    return np.array([int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def load_palette() -> dict[str, np.ndarray]:
    fallback = {
        "circle": np.array([0.77, 0.93, 0.96], dtype=np.float32),
        "crescent": np.array([0.60, 0.84, 0.90], dtype=np.float32),
        "trigon": np.array([0.42, 0.65, 0.78], dtype=np.float32),
        "water": np.array([0.25, 0.58, 0.76], dtype=np.float32),
        "rim": np.array([0.86, 0.96, 1.00], dtype=np.float32),
    }
    if not GRAMMAR_PATH.exists():
        return fallback
    data = json.loads(GRAMMAR_PATH.read_text())
    roles = data.get("palette_constraints", {}).get("palette_roles", {})
    water_light = roles.get("water_light", {}).get("colors", [])
    water_depth = roles.get("water_depth", {}).get("colors", [])
    if len(water_light) >= 2:
        fallback["rim"] = hex_to_rgb01(water_light[0])
        fallback["crescent"] = hex_to_rgb01(water_light[1])
    if len(water_depth) >= 3:
        fallback["water"] = hex_to_rgb01(water_depth[2])
        fallback["trigon"] = hex_to_rgb01(water_depth[1])
    fallback["circle"] = fallback["crescent"] * 0.72 + fallback["rim"] * 0.28
    return fallback


PALETTE = load_palette()
TRIGON_VERTS = np.array([[1.0, 0.0], [-0.62, 0.72], [-0.62, -0.72]], dtype=np.float32)


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    denom = edge1 - edge0
    if abs(denom) < 1e-8:
        return (x >= edge1).astype(np.float32)
    t = np.clip((x - edge0) / denom, 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def rotate_to_local(px: np.ndarray, py: np.ndarray, angle: float) -> tuple[np.ndarray, np.ndarray]:
    c = math.cos(angle)
    s = math.sin(angle)
    return px * c + py * s, -px * s + py * c


def sd_circle(px: np.ndarray, py: np.ndarray, radius: float) -> np.ndarray:
    return np.sqrt(px * px + py * py) - radius


def sd_crescent(px: np.ndarray, py: np.ndarray, radius: float) -> np.ndarray:
    # Water-use crescents are flattened into relief arcs so they do not read
    # as eye/ring shapes in the SDF shimmer.
    qy = py * 2.35
    outer = np.sqrt(px * px + qy * qy) - radius
    inner = np.sqrt((px - radius * 0.40) ** 2 + qy * qy) - radius * 0.82
    return np.maximum(outer, -inner)


def sd_polygon(px: np.ndarray, py: np.ndarray, verts: np.ndarray) -> np.ndarray:
    dist2 = np.full_like(px, 1e6, dtype=np.float32)
    inside = np.ones_like(px, dtype=bool)
    area = 0.0
    for i in range(len(verts)):
        j = (i + 1) % len(verts)
        area += float(verts[i, 0] * verts[j, 1] - verts[j, 0] * verts[i, 1])
    orient = 1.0 if area >= 0.0 else -1.0
    for i in range(len(verts)):
        a = verts[i]
        b = verts[(i + 1) % len(verts)]
        ex = b[0] - a[0]
        ey = b[1] - a[1]
        wx = px - a[0]
        wy = py - a[1]
        h = np.clip((wx * ex + wy * ey) / max(1e-6, ex * ex + ey * ey), 0.0, 1.0)
        qx = wx - ex * h
        qy = wy - ey * h
        dist2 = np.minimum(dist2, qx * qx + qy * qy)
        inside &= (ex * wy - ey * wx) * orient >= 0.0
    dist = np.sqrt(dist2)
    return np.where(inside, -dist, dist)


def sd_trigon(px: np.ndarray, py: np.ndarray, radius: float) -> np.ndarray:
    return sd_polygon(px / radius, py / radius, TRIGON_VERTS) * radius


def base_water_height(t: float, *, mode: str) -> np.ndarray:
    if mode == "ripple":
        base = (
            0.020 * np.sin(2.0 * math.pi * (0.58 * X + 0.17 * Y - 0.075 * t))
            + 0.014 * np.sin(2.0 * math.pi * (-0.28 * X + 0.92 * Y + 0.052 * t) + 0.6)
        )
    elif mode == "flow":
        base = (
            0.026 * np.sin(2.0 * math.pi * (0.72 * X + 0.30 * np.sin(2.0 * Y) - 0.090 * t))
            + 0.018 * np.sin(2.0 * math.pi * (1.05 * X - 0.46 * Y - 0.066 * t) + 1.2)
            + 0.010 * np.sin(2.0 * math.pi * (0.20 * X + 1.80 * Y + 0.040 * t))
        )
    else:
        base = (
            0.024 * np.sin(2.0 * math.pi * (0.72 * X + 0.24 * Y - 0.076 * t))
            + 0.018 * np.sin(2.0 * math.pi * (-0.42 * X + 1.05 * Y + 0.058 * t) + 0.9)
            + 0.012 * np.sin(2.0 * math.pi * (1.28 * X - 0.56 * Y - 0.043 * t) + 1.7)
        )
    return base.astype(np.float32)


def contour_xy(row: int, col: int, t: float, *, rows: int, cols: int) -> tuple[float, float, float]:
    u = -0.76 + col * (1.52 / max(1, cols - 1))
    phase = row * 0.62
    y_base = -0.37 + row * (0.74 / max(1, rows - 1))
    drift = 0.018 * math.sin(t * 0.28 + row * 0.37 + col * 0.13)
    x = u + 0.026 * math.sin(t * 0.18 + row * 0.61)
    y = y_base + 0.050 * math.sin(2.0 * math.pi * (0.42 * u - 0.045 * t) + phase) + drift
    dy_dx = 0.050 * math.cos(2.0 * math.pi * (0.42 * u - 0.045 * t) + phase) * 2.0 * math.pi * 0.42
    return x, y, math.atan2(dy_dx, 1.0)


def current_xy(row: int, col: int, t: float) -> tuple[float, float, float, float]:
    u = -0.82 + col * 0.205 + 0.026 * math.sin(t * 0.20 + row * 0.41)
    center = 0.100 * math.sin(2.0 * math.pi * (0.44 * u - 0.052 * t))
    offset = (row - 2.0) * 0.105
    y = center + offset + 0.020 * math.sin(2.0 * math.pi * (0.68 * u + row * 0.19 - 0.030 * t))
    dy_dx = (
        0.100 * math.cos(2.0 * math.pi * (0.44 * u - 0.052 * t)) * 2.0 * math.pi * 0.44
        + 0.020 * math.cos(2.0 * math.pi * (0.68 * u + row * 0.19 - 0.030 * t)) * 2.0 * math.pi * 0.68
    )
    crest = 0.5 + 0.5 * math.sin(2.0 * math.pi * (0.72 * u - 0.070 * t) + row * 0.55)
    return u, y, math.atan2(dy_dx, 1.0), crest


def surface_contour_glyphs(t: float) -> list[dict[str, float | str]]:
    glyphs: list[dict[str, float | str]] = []
    rows, cols = 6, 5
    for row in range(rows):
        for col in range(cols):
            x, y, angle = contour_xy(row, col, t, rows=rows, cols=cols)
            if abs(x) > 0.88 or abs(y) > 0.48:
                continue
            selector = (row * 5 + col * 3) % 10
            if selector in (0, 6):
                kind = "trigon"
                radius = 0.020 + 0.002 * ((row + col) % 2)
                amp = 0.016
            else:
                kind = "crescent"
                radius = 0.024 + 0.003 * ((row + 2 * col) % 3)
                amp = 0.014
            glyphs.append({"kind": kind, "x": x, "y": y, "r": radius, "angle": angle, "amp": amp, "solid": 0.085})
    return glyphs


def ripple_event_glyphs(t: float) -> list[dict[str, float | str]]:
    events = [
        {"start": 0.35, "x": -0.18, "y": 0.02, "scale": 1.0, "rays": 8},
        {"start": 2.55, "x": 0.34, "y": -0.12, "scale": 0.72, "rays": 7},
    ]
    glyphs: list[dict[str, float | str]] = []
    for event in events:
        age = t - float(event["start"])
        if age < 0.0 or age > 2.75:
            continue
        q = min(1.0, age / 2.75)
        scale = float(event["scale"])
        ox = float(event["x"])
        oy = float(event["y"])
        origin_strength = max(0.0, 1.0 - age / 0.80)
        if origin_strength > 0.02:
            glyphs.append(
                {
                    "kind": "circle",
                    "x": ox,
                    "y": oy,
                    "r": 0.014 * scale,
                    "angle": 0.0,
                    "amp": 0.026 * origin_strength,
                    "solid": 0.035,
                }
            )
        radius = (0.065 + 0.345 * math.sqrt(q)) * scale
        alpha = (1.0 - q) ** 1.15
        for ray in range(int(event["rays"])):
            theta = ray * 2.0 * math.pi / int(event["rays"]) + 0.10 * math.sin(t * 0.3)
            for idx, (kind, extra, size, amp_mul) in enumerate(
                [
                    ("crescent", 0.000, 0.032, 1.00),
                    ("crescent", 0.055, 0.026, 0.76),
                    ("trigon", 0.110, 0.021, 0.58),
                ]
            ):
                rr = radius + extra * scale
                x = ox + math.cos(theta) * rr
                y = oy + math.sin(theta) * rr
                if abs(x) > 0.88 or abs(y) > 0.50:
                    continue
                glyphs.append(
                    {
                        "kind": kind,
                        "x": x,
                        "y": y,
                        "r": size * scale,
                        "angle": theta,
                        "amp": 0.023 * alpha * amp_mul,
                        "solid": 0.040,
                    }
                )
    return glyphs


def caustic_refraction_glyphs(t: float) -> list[dict[str, float | str]]:
    glyphs: list[dict[str, float | str]] = []
    rows, cols = 5, 5
    for row in range(rows):
        for col in range(cols):
            x, y, angle = contour_xy(row, col, t * 0.82 + 2.0, rows=rows, cols=cols)
            x += 0.020 * math.sin(row * 1.7 + col * 0.6)
            y += 0.015 * math.sin(col * 1.1)
            selector = (row + col * 2) % 9
            if selector in (3, 7):
                kind = "trigon"
                radius = 0.019
                amp = 0.010
            else:
                kind = "crescent"
                radius = 0.022
                amp = 0.010
            glyphs.append({"kind": kind, "x": x, "y": y, "r": radius, "angle": angle, "amp": amp, "solid": 0.008})
    return glyphs


def flowline_glyphs(t: float) -> list[dict[str, float | str]]:
    glyphs: list[dict[str, float | str]] = []
    for row in range(5):
        for col in range(7):
            x, y, tangent, crest = current_xy(row, col, t)
            if abs(x) > 0.88 or abs(y) > 0.50:
                continue
            kind_selector = (row * 2 + col) % 8
            if kind_selector in (2, 6):
                kind = "trigon"
                radius = 0.020
                amp = 0.014
            else:
                kind = "crescent"
                radius = 0.024 + 0.003 * crest
                amp = 0.014 + 0.004 * crest
            # No sudden flips: angle changes continuously by crest/trough phase.
            angle = tangent + 0.42 * math.sin((crest - 0.5) * math.pi)
            glyphs.append({"kind": kind, "x": x, "y": y, "r": radius, "angle": angle, "amp": amp, "solid": 0.12})
    return glyphs


def glyph_fields(
    gx: np.ndarray,
    gy: np.ndarray,
    glyphs: Iterable[dict[str, float | str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    sdf_union = np.full_like(gx, 10.0, dtype=np.float32)
    fill_rgb = np.zeros((*gx.shape, 3), dtype=np.float32)
    fill_weight = np.zeros_like(gx, dtype=np.float32)
    height = np.zeros_like(gx, dtype=np.float32)
    rim = np.zeros_like(gx, dtype=np.float32)
    for glyph in glyphs:
        px = gx - float(glyph["x"])
        py = gy - float(glyph["y"])
        qx, qy = rotate_to_local(px, py, float(glyph["angle"]))
        radius = float(glyph["r"])
        kind = str(glyph["kind"])
        if kind == "circle":
            sdf = sd_circle(qx, qy, radius)
            color = PALETTE["circle"]
            feather = 0.010
        elif kind == "crescent":
            sdf = sd_crescent(qx, qy, radius)
            color = PALETTE["crescent"]
            feather = 0.012
        elif kind == "trigon":
            sdf = sd_trigon(qx, qy, radius)
            color = PALETTE["trigon"]
            feather = 0.011
        else:
            continue
        sdf_union = np.minimum(sdf_union, sdf)
        inside = smoothstep(feather, -feather, sdf)
        edge = np.exp(-np.minimum((sdf / feather) ** 2, 32.0)).astype(np.float32)
        solid = float(glyph.get("solid", 0.08))
        amp = float(glyph.get("amp", 0.012))
        if kind == "circle":
            fill = inside * solid
            height += amp * (inside * 0.75 + edge * 0.12)
            rim = np.maximum(rim, edge * amp * 0.10)
        else:
            fill = inside * solid + edge * solid * 0.45
            height += amp * (inside * 0.45 + edge * 0.90)
            rim = np.maximum(rim, edge * amp)
        fill_rgb += fill[..., None] * color
        fill_weight += fill
    fill_rgb = fill_rgb / np.maximum(fill_weight, 1e-5)[..., None]
    fill_rgb *= np.clip(fill_weight, 0.0, 1.0)[..., None]
    return sdf_union, fill_rgb.astype(np.float32), np.clip(fill_weight, 0.0, 1.0), height.astype(np.float32), rim.astype(np.float32)


def add_ripple_height(height: np.ndarray, glyphs: Iterable[dict[str, float | str]], t: float) -> np.ndarray:
    out = height.copy()
    for glyph in glyphs:
        if glyph["kind"] != "circle":
            continue
        ox = float(glyph["x"])
        oy = float(glyph["y"])
        r = np.sqrt((X - ox) ** 2 + (Y - oy) ** 2)
        out += 0.016 * np.sin(66.0 * r - 5.2 * t) * np.exp(-7.5 * r)
    return out.astype(np.float32)


def normals_from_height(height: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dhdy, dhdx = np.gradient(height, DY, DX)
    nx = -dhdx * 0.105
    ny = -dhdy * 0.105
    nz = np.ones_like(height, dtype=np.float32)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length
    slope = np.sqrt(nx * nx + ny * ny)
    curvature = np.abs(np.gradient(ny, DX, axis=1) + np.gradient(nx, DY, axis=0)).astype(np.float32)
    return nx.astype(np.float32), ny.astype(np.float32), nz.astype(np.float32), slope.astype(np.float32), curvature


def shade_frame(
    t: float,
    glyphs: list[dict[str, float | str]],
    *,
    mode: str,
    solid_gain: float,
    caustic_gain: float,
    water_gain: float,
    rim_gain: float,
) -> np.ndarray:
    sdf, _, _, glyph_height, _ = glyph_fields(X, Y, glyphs)
    height = base_water_height(t, mode=mode) + glyph_height
    if mode == "ripple":
        height = add_ripple_height(height, glyphs, t)
    nx, ny, nz, slope, curvature = normals_from_height(height)

    refract = 0.034 if mode != "caustic" else 0.055
    _, rglyph_rgb, rfill, _, rrim = glyph_fields(X + nx * refract, Y + ny * refract, glyphs)
    caustic = np.clip(curvature * 0.62 + slope * 2.05, 0.0, 1.0) ** 1.55
    water_lines = np.exp(-np.minimum(((np.sin(height * 132.0 + t * 0.70) + 1.0) * 0.5 / 0.18) ** 2, 32.0))
    water_lines *= 0.20 + np.clip(slope * 1.55, 0.0, 1.0)
    fresnel = ((1.0 - np.clip(nz, 0.0, 1.0)) ** 1.65).astype(np.float32)
    relief = np.clip(rfill * 1.20 + rrim * 25.0 + slope * 0.35, 0.0, 1.0)

    col = np.zeros((RH, RW, 3), dtype=np.float32)
    col += PALETTE["water"] * water_lines[..., None] * water_gain
    col += PALETTE["water"] * caustic[..., None] * slope[..., None] * caustic_gain
    col += rglyph_rgb * solid_gain * (0.22 + 0.78 * caustic[..., None]) * relief[..., None]
    col += PALETTE["rim"] * rrim[..., None] * rim_gain * (0.35 + 0.65 * caustic[..., None])
    col += PALETTE["rim"] * fresnel[..., None] * relief[..., None] * 0.13

    col = np.clip(col, 0.0, 1.0)
    rgb = (col * 255.0).astype(np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return cv2.resize(bgr, (W, H), interpolation=cv2.INTER_CUBIC)


def render_clip(
    filename: str,
    glyph_func,
    *,
    mode: str,
    solid_gain: float,
    caustic_gain: float,
    water_gain: float,
    rim_gain: float,
    progress_label: str,
    test: str,
    method: str,
    caveat: str,
) -> ClipResult:
    out = OUT_DIR / filename
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = shade_frame(
            t,
            glyph_func(t),
            mode=mode,
            solid_gain=solid_gain,
            caustic_gain=caustic_gain,
            water_gain=water_gain,
            rim_gain=rim_gain,
        )
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  {progress_label} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(filename=filename, test=test, method=method, caveat=caveat)


def render_all() -> list[ClipResult]:
    return [
        render_clip(
            "01_embedded_surface_contour_field_v002_black_screen.mp4",
            surface_contour_glyphs,
            mode="surface",
            solid_gain=0.22,
            caustic_gain=0.30,
            water_gain=0.34,
            rim_gain=0.62,
            progress_label="embedded surface contour field v002",
            test="Full-field water surface where many small, sparse glyphs are embedded along wave contours.",
            method="Contour-derived glyphs modify the heightfield before normal generation; visible marks come mostly from shared relief edge, refraction, and caustic shimmer.",
            caveat="Removes circles from the field study; if the remaining crescent/trigon arcs still read as symbols, the next pass should lower glyph visibility further.",
        ),
        render_clip(
            "02_ripple_event_relief_v002_black_screen.mp4",
            ripple_event_glyphs,
            mode="ripple",
            solid_gain=0.22,
            caustic_gain=0.32,
            water_gain=0.20,
            rim_gain=0.82,
            progress_label="ripple event relief v002",
            test="Droplet/ripple events where circles are subtle impact origins and crescents/trigons attenuate outward as relief/refraction.",
            method="Time-windowed radial SDF events are merged into the heightfield; the impact circle is a small relief disk rather than a high-contrast eye/ring.",
            caveat="Circle origin is still culturally and visually sensitive; this version avoids paired circles and uses subdued solid fill.",
        ),
        render_clip(
            "03_caustic_refraction_glyphs_v002_black_screen.mp4",
            caustic_refraction_glyphs,
            mode="caustic",
            solid_gain=0.05,
            caustic_gain=0.46,
            water_gain=0.38,
            rim_gain=0.74,
            progress_label="caustic refraction glyphs v002",
            test="Barely solid glyphs visible primarily through caustic shimmer, refraction, and heightfield normals.",
            method="Low-solid SDF glyphs sit under a stronger caustic/normal shader; their fill is mostly revealed by refracted sampling and relief edges.",
            caveat="This is the least literal grammar read; it may become too subtle in Resolume unless opacity/bloom is raised.",
        ),
        render_clip(
            "04_flowline_heightfield_glyphs_v002_black_screen.mp4",
            flowline_glyphs,
            mode="flow",
            solid_gain=0.18,
            caustic_gain=0.34,
            water_gain=0.34,
            rim_gain=0.60,
            progress_label="flowline heightfield glyphs v002",
            test="Current/flowline study where glyph orientation follows smooth local tangent and crest/trough phase logic.",
            method="Glyphs are distributed across S-curve current bands; crescent/trigon orientation follows continuous tangent offsets before heightfield embedding.",
            caveat="Still abstract current grammar; review should focus on whether it reads as one water field instead of flocking or figures.",
        ),
    ]


def ffprobe(path: Path) -> dict[str, str]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(path),
    ]
    data = json.loads(subprocess.check_output(cmd, text=True))
    stream = data["streams"][0]
    return {
        "width": str(stream.get("width", "")),
        "height": str(stream.get("height", "")),
        "fps": str(stream.get("avg_frame_rate") or stream.get("r_frame_rate", "")),
        "duration": str(stream.get("duration", "")),
        "frames": str(stream.get("nb_frames", "")),
    }


def midpoint_stats(result: ClipResult) -> str:
    cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "midpoint read failed"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return f"midpoint max luma {int(gray.max())}, nonblack pixels {int((gray > 2).sum())}"


def save_midpoint_stills(results: Iterable[ClipResult]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[np.ndarray] = []
    for result in results:
        cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        cv2.imwrite(str(MIDPOINT_DIR / f"{Path(result.filename).stem}_midpoint.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(
            thumb,
            Path(result.filename).stem[:48],
            (14, 248),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        thumbs.append(thumb)
    if thumbs:
        rows = []
        for i in range(0, len(thumbs), 2):
            row = thumbs[i : i + 2]
            if len(row) == 1:
                row.append(np.zeros_like(row[0]))
            rows.append(cv2.hconcat(row))
        cv2.imwrite(str(OUT_DIR / "contact_sheet_midpoints.jpg"), cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])


def write_readme(results: list[ClipResult]) -> None:
    rows = [(result, ffprobe(OUT_DIR / result.filename), midpoint_stats(result)) for result in results]
    lines = [
        "# Heightfield SDF Water Glyph v002 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Water-only black-background Add/Screen-friendly clips; no fish, birds, figures, eyes, bodies, flocking, SD, LoRA, SAM, or YOLO.",
        "",
        "## Darren's v001 Feedback Summary",
        "",
        "- v001 was a good technical substrate proof, but the composition read like two abstract figures or eye-creatures.",
        "- The circle/crescent/trigon phrase arrangement created a circle-on-left, eye-like middle, and trigon-on-right object read.",
        "- v002 changes the composition completely: no object-like phrases, no paired circles, no black-pupil/white-eye circle treatment, and no creature-like groupings.",
        "- The subject is now the water field itself.",
        "",
        "## Method",
        "",
        "- Uses `track2-deterministic/primitive_grammar/grammar_v001.json` for the internal heightfield-SDF projection mode and water-light palette roles.",
        "- Rasterizes circle/crescent/trigon instances as SDFs in normalized scene space.",
        "- Merges each glyph SDF into the water heightfield before normal generation.",
        "- Recomputes normals from the combined field and shades the result with shared caustic/refraction logic.",
        "- Removes circles from full-field/current studies; circles appear only as subtle droplet impact origins.",
        "",
        "## Review Order",
        "",
        "1. `01_embedded_surface_contour_field_v002_black_screen.mp4`",
        "2. `03_caustic_refraction_glyphs_v002_black_screen.mp4`",
        "3. `04_flowline_heightfield_glyphs_v002_black_screen.mp4`",
        "4. `02_ripple_event_relief_v002_black_screen.mp4`",
        "",
        "## Austin / Darren Questions",
        "",
        "- Does the heightfield/SDF substrate now read as a water field rather than as objects or creatures?",
        "- Should circle marks be limited to explicit impact origins?",
        "- Should glyphs be more visible as primitive grammar, or more hidden as caustic/refraction structure?",
        "- Does the flowline study maintain smooth surface logic without random crescent flips?",
        "- Is black-background Add/Screen still the right review format for this substrate?",
        "",
        "## Clips",
        "",
    ]
    for result, probe, stats in rows:
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}",
                f"- Technical method: {result.method}",
                f"- Caveat: {result.caveat}",
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                f"- Nonblank check: {stats}",
                "",
            ]
        )
    lines.extend(
        [
            "## Review Stills",
            "",
            "- Midpoint stills: `midpoint_stills/`",
            "- Contact sheet: `contact_sheet_midpoints.jpg`",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Heightfield SDF Water Glyph v002 to {OUT_DIR}", flush=True)
    results = render_all()
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
