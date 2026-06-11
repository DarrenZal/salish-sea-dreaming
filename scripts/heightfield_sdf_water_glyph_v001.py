#!/usr/bin/env python3.11
"""
Heightfield + SDF water glyph proof v001.

Internal deterministic substrate proof:
  - circle / crescent / trigon are rasterized as signed-distance fields
  - glyph SDFs are folded into a moving water heightfield before normals
  - final color samples a refracted glyph fill from the combined normal field

This is deliberately separate from primitive_water_membrane_v6.py. No fish,
birds, figures, flocking, SD, LoRA, SAM, or YOLO.
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


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/heightfield_sdf_water_glyph_v001_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
FPS = 24
# Internal shader-frame resolution. Output is still 1920x1080; this proof
# prioritizes turnaround over hero-quality supersampling.
RW = 640
RH = 360
ASPECT = W / H

CIRCLE_RGB = np.array([0.96, 0.91, 0.76], dtype=np.float32)
CRESCENT_RGB = np.array([0.62, 0.86, 0.94], dtype=np.float32)
TRIGON_RGB = np.array([0.44, 0.68, 0.82], dtype=np.float32)
WATER_RGB = np.array([0.34, 0.70, 0.86], dtype=np.float32)
RIM_RGB = np.array([0.92, 0.96, 0.94], dtype=np.float32)

X_AXIS = (np.linspace(0.0, 1.0, RW, dtype=np.float32) - 0.5) * ASPECT
Y_AXIS = (np.linspace(0.0, 1.0, RH, dtype=np.float32) - 0.5)
X, Y = np.meshgrid(X_AXIS, Y_AXIS)
DX = float(X_AXIS[1] - X_AXIS[0])
DY = float(Y_AXIS[1] - Y_AXIS[0])


@dataclass(frozen=True)
class ClipResult:
    filename: str
    method: str
    dynamic_note: str = ""


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
    # Boolean difference of two circles. The smaller offset circle carves the
    # open mouth; the SDF then becomes a height/normal contribution.
    outer = np.sqrt(px * px + py * py) - radius
    inner = np.sqrt((px - radius * 0.40) ** 2 + py * py) - radius * 0.84
    return np.maximum(outer, -inner)


TRIGON_VERTS = np.array([[1.0, 0.0], [-0.62, 0.72], [-0.62, -0.72]], dtype=np.float32)


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
        cross = ex * wy - ey * wx
        inside &= cross * orient >= 0.0
    dist = np.sqrt(dist2)
    return np.where(inside, -dist, dist)


def sd_trigon(px: np.ndarray, py: np.ndarray, radius: float) -> np.ndarray:
    return sd_polygon(px / radius, py / radius, TRIGON_VERTS) * radius


def glyph_phrase(t: float) -> list[dict[str, float | str]]:
    slow = 0.030 * math.sin(t * 0.43)
    lift = 0.020 * math.sin(t * 0.37 + 0.8)
    phrase_a = [
        {"kind": "circle", "x": -0.48 + slow, "y": 0.055 + lift, "r": 0.035, "angle": 0.05},
        {"kind": "crescent", "x": -0.28 + slow, "y": 0.076 + lift, "r": 0.070, "angle": 0.12},
        {"kind": "crescent", "x": -0.08 + slow, "y": 0.042 + lift, "r": 0.060, "angle": -0.10},
        {"kind": "trigon", "x": 0.135 + slow, "y": 0.006 + lift, "r": 0.058, "angle": -0.14},
    ]
    phrase_b = [
        {"kind": "circle", "x": 0.245 - slow * 0.6, "y": -0.165 - lift * 0.6, "r": 0.024, "angle": -0.34},
        {"kind": "crescent", "x": 0.365 - slow * 0.6, "y": -0.202 - lift * 0.5, "r": 0.050, "angle": -0.24},
        {"kind": "crescent", "x": 0.500 - slow * 0.6, "y": -0.221 - lift * 0.4, "r": 0.042, "angle": -0.12},
        {"kind": "trigon", "x": 0.645 - slow * 0.6, "y": -0.227 - lift * 0.3, "r": 0.040, "angle": -0.08},
    ]
    return phrase_a + phrase_b


def glyph_fields(
    gx: np.ndarray,
    gy: np.ndarray,
    glyphs: Iterable[dict[str, float | str]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sdf_union = np.full_like(gx, 10.0, dtype=np.float32)
    fill_rgb = np.zeros((*gx.shape, 3), dtype=np.float32)
    fill_weight = np.zeros_like(gx, dtype=np.float32)
    for glyph in glyphs:
        px = gx - float(glyph["x"])
        py = gy - float(glyph["y"])
        qx, qy = rotate_to_local(px, py, float(glyph["angle"]))
        radius = float(glyph["r"])
        kind = str(glyph["kind"])
        if kind == "circle":
            sdf = sd_circle(qx, qy, radius)
            color = CIRCLE_RGB
        elif kind == "crescent":
            sdf = sd_crescent(qx, qy, radius)
            color = CRESCENT_RGB
        elif kind == "trigon":
            sdf = sd_trigon(qx, qy, radius)
            color = TRIGON_RGB
        else:
            continue
        sdf_union = np.minimum(sdf_union, sdf)
        fill = smoothstep(0.010, -0.004, sdf)
        fill_rgb += fill[..., None] * color
        fill_weight += fill
    fill_weight_safe = np.maximum(fill_weight, 1e-5)
    fill_rgb = fill_rgb / fill_weight_safe[..., None]
    fill_rgb *= np.clip(fill_weight, 0.0, 1.0)[..., None]
    return sdf_union, fill_rgb, np.clip(fill_weight, 0.0, 1.0)


def water_height(t: float, glyphs: Iterable[dict[str, float | str]], sdf: np.ndarray) -> np.ndarray:
    h = (
        0.030 * np.sin(2.0 * math.pi * (0.80 * X + 0.22 * Y - 0.105 * t))
        + 0.020 * np.sin(2.0 * math.pi * (-0.35 * X + 1.16 * Y + 0.070 * t) + 0.9)
        + 0.014 * np.sin(2.0 * math.pi * (1.55 * X - 0.58 * Y - 0.052 * t) + 1.7)
    )
    for glyph in glyphs:
        if glyph["kind"] != "circle":
            continue
        rx = X - float(glyph["x"])
        ry = Y - float(glyph["y"])
        r = np.sqrt(rx * rx + ry * ry)
        h += 0.020 * np.sin(52.0 * r - 4.2 * t) * np.exp(-8.5 * r)

    inside = smoothstep(0.012, -0.010, sdf)
    rim = np.exp(-np.minimum((sdf / 0.010) ** 2, 32.0))
    # Positive relief plus a fine rim: the primitive modifies the heightfield
    # before normal generation, which is the core non-sticker test.
    return (h + 0.058 * inside + 0.026 * rim).astype(np.float32)


def normals_from_height(height: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dhdy, dhdx = np.gradient(height, DY, DX)
    nx = -dhdx * 0.11
    ny = -dhdy * 0.11
    nz = np.ones_like(height, dtype=np.float32)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length
    slope = np.sqrt(nx * nx + ny * ny)
    return nx.astype(np.float32), ny.astype(np.float32), nz.astype(np.float32), slope.astype(np.float32)


def shade_frame(t: float) -> np.ndarray:
    glyphs = glyph_phrase(t)
    sdf, _, _ = glyph_fields(X, Y, glyphs)
    height = water_height(t, glyphs, sdf)
    nx, ny, nz, slope = normals_from_height(height)

    refract_strength = 0.052
    rsdf, rglyph_rgb, rfill = glyph_fields(X + nx * refract_strength, Y + ny * refract_strength, glyphs)
    rim = np.exp(-np.minimum((rsdf / 0.012) ** 2, 32.0)).astype(np.float32)

    dny_dx = np.gradient(ny, DX, axis=1)
    dnx_dy = np.gradient(nx, DY, axis=0)
    curvature = np.abs(dny_dx + dnx_dy)
    caustic = np.clip((curvature * 0.85 + slope * 2.1), 0.0, 1.0)
    caustic = (caustic ** 1.45).astype(np.float32)

    wave_lines = np.exp(-np.minimum(((np.sin(height * 120.0 + t * 0.8) + 1.0) * 0.5 / 0.18) ** 2, 32.0))
    wave_lines *= np.clip(slope * 1.65, 0.0, 1.0)

    fresnel = ((1.0 - np.clip(nz, 0.0, 1.0)) ** 1.8).astype(np.float32)
    disturbance = np.clip(rfill * 1.25 + rim * 1.35 + slope * 0.34, 0.0, 1.0)

    col = np.zeros((RH, RW, 3), dtype=np.float32)
    col += rglyph_rgb * (0.24 + 0.86 * caustic[..., None]) * (0.50 + 0.50 * disturbance[..., None])
    col += RIM_RGB * rim[..., None] * (0.40 + 0.55 * caustic[..., None])
    col += WATER_RGB * wave_lines[..., None] * 0.17
    col += WATER_RGB * caustic[..., None] * slope[..., None] * 0.18
    col += RIM_RGB * fresnel[..., None] * disturbance[..., None] * 0.20

    col = np.clip(col, 0.0, 1.0)
    rgb = (col * 255.0).astype(np.uint8)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return cv2.resize(bgr, (W, H), interpolation=cv2.INTER_CUBIC)


def render_proof_clip() -> ClipResult:
    out = OUT_DIR / "01_heightfield_sdf_glyph_embedding_v001_black_screen.mp4"
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        writer.write(shade_frame(t))
        if (fi + 1) % 48 == 0:
            print(f"  heightfield SDF glyph proof v001 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        method="Python/NumPy shader-frame proof: SDF glyph union -> merged water heightfield -> finite-difference normals -> refracted glyph shading on black.",
    )


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


def midpoint_stats(path: Path) -> str:
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "midpoint read failed"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return f"midpoint max luma {int(gray.max())}, nonblack pixels {int((gray > 2).sum())}"


def save_midpoint_still(result: ClipResult) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / result.filename
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return
    still_path = MIDPOINT_DIR / f"{Path(result.filename).stem}_midpoint.jpg"
    cv2.imwrite(str(still_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
    thumb = cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA)
    cv2.putText(
        thumb,
        Path(result.filename).stem[:72],
        (24, 505),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.56,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )
    cv2.imwrite(str(OUT_DIR / "contact_sheet_midpoints.jpg"), thumb, [cv2.IMWRITE_JPEG_QUALITY, 92])


def write_readme(result: ClipResult) -> None:
    probe = ffprobe(OUT_DIR / result.filename)
    stats = midpoint_stats(OUT_DIR / result.filename)
    lines = [
        "# Heightfield SDF Water Glyph v001 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Black-background Add/Screen-friendly substrate proof; no fish, birds, figures, flocking, SD, LoRA, SAM, or YOLO.",
        "",
        f"- Clip: `{result.filename}`",
        "- What it tests: circle/crescent/trigon marks folded into a moving water height/normal field, then refracted by that same field.",
        f"- Method: {result.method}",
        f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
        f"- Nonblank check: {stats}",
        "- Midpoint still: `midpoint_stills/`",
        "- Contact sheet: `contact_sheet_midpoints.jpg`",
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Heightfield SDF Water Glyph v001 to {OUT_DIR}", flush=True)
    result = render_proof_clip()
    save_midpoint_still(result)
    write_readme(result)
    print("Done. README includes ffprobe metadata and nonblank check.", flush=True)


if __name__ == "__main__":
    main()
