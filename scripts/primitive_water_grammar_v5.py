#!/usr/bin/env python3.11
"""
Primitive Water Grammar v005.

Layer-only black-background review packet:
  - water topology/current layers
  - grammar-built articulated fish layers

No SD, LoRA, SAM, YOLO, or named/specific being transformations.
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

from primitive_water_grammar_v1 import (
    CRESCENT_BASE,
    H1_SALMON,
    H264Writer,
    N_FRAMES,
    ROOT,
    SampledVideo,
    TRIGON_BASE,
    W,
    H,
    calc_flow,
    draw_circle_alpha,
    draw_poly_alpha,
    sample_flow,
    smooth_angle,
    transform_points,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v005_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
FPS = 24

CIRCLE_RGB = (240, 232, 206)
CRESCENT_RGB = (205, 226, 232)
TRIGON_RGB = (166, 198, 214)
OUTLINE_RGB = (228, 238, 238)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    method: str
    layer_role: str
    dynamic_note: str = ""


def black_canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def draw_crescent(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(CRESCENT_BASE, center, size, angle),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.11,
        outline_thickness=1,
    )


def draw_trigon(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(TRIGON_BASE, center, size, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.11,
        outline_thickness=1,
    )


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, *, alpha: float) -> None:
    draw_circle_alpha(
        frame,
        center,
        radius,
        CIRCLE_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.09,
    )


def rotate_translate(local: tuple[float, float], center: tuple[float, float], angle: float) -> tuple[float, float]:
    x, y = local
    c = math.cos(angle)
    s = math.sin(angle)
    return center[0] + x * c - y * s, center[1] + x * s + y * c


def spine_sample(d: float, length: float, phase: float, bend: float) -> tuple[float, float, float]:
    """Local head(0) -> tail(1) curved spine point and tangent angle."""

    x = (0.50 - d) * length
    wave = math.sin(phase - d * 2.05)
    y = bend * length * (d ** 1.55) * wave
    dx_dd = -length
    dy_dd = bend * length * (
        1.55 * (d ** 0.55) * wave - 2.05 * (d ** 1.55) * math.cos(phase - d * 2.05)
    )
    tangent = math.atan2(dy_dd, dx_dd) + math.pi
    return x, y, tangent


def draw_fish_v5(
    frame: np.ndarray,
    center: tuple[float, float],
    length: float,
    angle: float,
    phase: float,
    *,
    alpha: float,
    bend: float = 0.075,
    body_alpha: float = 0.58,
) -> None:
    """Trigon head -> crescent gill -> circle body -> tapering crescents -> trigon tail."""

    # Draw tail-to-head so the bigger body/head read on top.
    body_parts = [
        ("tail", 0.98, 0.125, 0.72),
        ("crescent", 0.82, 0.082, 0.48),
        ("crescent", 0.68, 0.105, 0.54),
        ("crescent", 0.54, 0.130, 0.62),
        ("fin_bottom", 0.47, 0.058, 0.40),
        ("fin_top", 0.40, 0.052, 0.38),
        ("circle", 0.35, 0.115, body_alpha),
        ("gill", 0.18, 0.120, 0.62),
        ("head", 0.035, 0.130, 0.78),
        ("eye", 0.000, 0.018, 0.62),
    ]
    for kind, d, size_mul, part_alpha in body_parts:
        lx, ly, tangent = spine_sample(d, length, phase, bend)
        orient = angle + tangent
        if kind == "fin_top":
            lx, ly = lx - length * 0.015, ly - length * 0.115
            pos = rotate_translate((lx, ly), center, angle)
            draw_crescent(frame, pos, length * size_mul, orient - 0.85, alpha=alpha * part_alpha)
        elif kind == "fin_bottom":
            lx, ly = lx - length * 0.025, ly + length * 0.105
            pos = rotate_translate((lx, ly), center, angle)
            draw_crescent(frame, pos, length * size_mul, orient + 0.80, alpha=alpha * part_alpha)
        elif kind == "head":
            pos = rotate_translate((lx, ly), center, angle)
            draw_trigon(frame, pos, length * size_mul, orient, alpha=alpha * part_alpha)
        elif kind == "tail":
            pos = rotate_translate((lx, ly), center, angle)
            draw_trigon(frame, pos, length * size_mul, orient + math.pi, alpha=alpha * part_alpha)
        elif kind == "circle":
            pos = rotate_translate((lx, ly), center, angle)
            draw_circle(frame, pos, length * size_mul, alpha=alpha * part_alpha)
        elif kind == "gill":
            pos = rotate_translate((lx, ly), center, angle)
            draw_crescent(frame, pos, length * size_mul, orient + 0.06, alpha=alpha * part_alpha)
        elif kind == "eye":
            # A tiny primitive circle near the head, offset toward the dorsal side.
            eye_pos = rotate_translate((lx + length * 0.020, ly - length * 0.035), center, angle)
            draw_circle(frame, eye_pos, length * size_mul, alpha=alpha * part_alpha)
        else:
            pos = rotate_translate((lx, ly), center, angle)
            draw_crescent(frame, pos, length * size_mul, orient, alpha=alpha * part_alpha)


def transform_points_aniso(base: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float) -> np.ndarray:
    scaled = base.copy()
    scaled[:, 0] *= sx
    scaled[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    pts = scaled @ rot.T
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]
    return pts


def draw_flat_crescent(frame: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float, *, alpha: float, flip: bool = False) -> None:
    base = CRESCENT_BASE.copy()
    if flip:
        base[:, 1] *= -1.0
    draw_poly_alpha(
        frame,
        transform_points_aniso(base, center, sx, sy, angle),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.075,
        outline_thickness=1,
    )


def draw_flat_trigon(frame: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points_aniso(TRIGON_BASE, center, sx, sy, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.075,
        outline_thickness=1,
    )


def unit_circle_points(samples: int = 72) -> np.ndarray:
    return np.array(
        [(math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples)) for i in range(samples)],
        dtype=np.float32,
    )


CIRCLE_BASE = unit_circle_points()


class TopologyProjector:
    def __init__(self) -> None:
        src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        dst = np.array(
            [
                [W * 0.31, H * 0.21],
                [W * 0.69, H * 0.21],
                [W * 0.94, H * 0.88],
                [W * 0.06, H * 0.88],
            ],
            dtype=np.float32,
        )
        self.mat = cv2.getPerspectiveTransform(src, dst)

    def warp_uv(self, pts: np.ndarray, t: float) -> np.ndarray:
        uv = pts.copy()
        u = uv[:, 0]
        v = uv[:, 1]
        # Small topology warp: enough to show surface orientation, not enough
        # to turn the plane into a separate spectacle.
        uv[:, 1] = v + 0.018 * np.sin(2.0 * math.pi * (u * 1.15 + t * 0.055)) * (0.25 + 0.75 * v)
        uv[:, 0] = u + 0.010 * np.sin(2.0 * math.pi * (v * 0.90 - t * 0.035)) * (0.20 + 0.80 * v)
        return uv

    def project(self, pts: np.ndarray, t: float) -> np.ndarray:
        uv = self.warp_uv(pts, t)
        projected = cv2.perspectiveTransform(uv.reshape(-1, 1, 2).astype(np.float32), self.mat)
        return projected.reshape(-1, 2)


def draw_plane_shape(
    frame: np.ndarray,
    projector: TopologyProjector,
    base: np.ndarray,
    center_uv: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    t: float,
) -> None:
    local = base.copy()
    local[:, 0] *= sx
    local[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    uv = local @ rot.T
    uv[:, 0] += center_uv[0]
    uv[:, 1] += center_uv[1]
    pts = projector.project(uv, t)
    draw_poly_alpha(
        frame,
        pts,
        rgb,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.08,
        outline_thickness=1,
    )


def render_perspective_ripple_topology() -> ClipResult:
    out = OUT_DIR / "01_perspective_ripple_plane_topology_v005_black_screen.mp4"
    writer = H264Writer(out)
    projector = TopologyProjector()
    impacts = [
        {"start": 0.10, "uv": (0.40, 0.61), "scale": 1.0, "dirs": 7},
        {"start": 2.65, "uv": (0.66, 0.39), "scale": 0.62, "dirs": 5},
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for impact in impacts:
            age = t - impact["start"]
            if age < 0.0 or age > 3.45:
                continue
            u, v = impact["uv"]
            scale = impact["scale"]
            flash = max(0.0, 1.0 - age / 0.90)
            draw_plane_shape(frame, projector, CIRCLE_BASE, (u, v), 0.012 * scale, 0.012 * scale, 0.0, CIRCLE_RGB, alpha=0.50 * flash, t=t)
            for ray in range(impact["dirs"]):
                angle = -0.08 + ray * 2.0 * math.pi / impact["dirs"]
                local_age = age - ray * 0.026
                if local_age <= 0.0:
                    continue
                q = min(1.0, local_age / 2.75)
                ease = math.sqrt(max(0.0, 1.0 - (1.0 - q) ** 2))
                base_r = (0.032 + 0.180 * ease) * scale
                alpha = 0.46 * ((1.0 - q) ** 1.30) * scale
                if alpha < 0.024:
                    continue
                for idx, (kind, extra, sx, sy) in enumerate(
                    [
                        ("crescent", 0.000, 0.030, 0.019),
                        ("crescent", 0.042, 0.025, 0.016),
                        ("trigon", 0.086, 0.019, 0.019),
                    ]
                ):
                    r = base_r + extra * scale
                    cu = u + math.cos(angle) * r
                    cv = v + math.sin(angle) * r
                    if not (-0.05 <= cu <= 1.05 and -0.05 <= cv <= 1.05):
                        continue
                    if kind == "crescent":
                        draw_plane_shape(frame, projector, CRESCENT_BASE, (cu, cv), sx * scale, sy * scale, angle, CRESCENT_RGB, alpha=alpha * (0.88 - idx * 0.08), t=t)
                    else:
                        draw_plane_shape(frame, projector, TRIGON_BASE, (cu, cv), sx * scale, sy * scale, angle, TRIGON_RGB, alpha=alpha * 0.60, t=t)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  perspective ripple topology v005 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural water topology study",
        test="Tilted/warped water surface where ripple primitives live on a perspective plane.",
        method="Authored in UV surface coordinates, gently warped to suggest topology, then projected through a homography.",
        layer_role="Water topology layer. Leads the water review because it preserves the v004 direction and makes the surface-orientation parameter explicit.",
    )


def render_duality_current_sheet() -> ClipResult:
    out = OUT_DIR / "02_duality_current_sheet_v005_black_screen.mp4"
    writer = H264Writer(out)
    bands = [
        (H * 0.28, 0.00, 0.70),
        (H * 0.40, 1.10, 0.84),
        (H * 0.52, 2.10, 0.92),
        (H * 0.64, 3.05, 0.78),
        (H * 0.76, 4.00, 0.58),
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for band_idx, (y_base, phase, alpha_scale) in enumerate(bands):
            scroll = t * 0.030 + band_idx * 0.045
            for col in range(13):
                s = ((col / 12.0 + scroll) % 1.16) - 0.08
                x = s * W
                wave_phase = 2.0 * math.pi * (s * 1.06 - t * 0.105) + phase
                y = y_base + 32.0 * math.sin(wave_phase)
                dy_dx = 32.0 * math.cos(wave_phase) * 2.0 * math.pi * 1.06 / W
                tangent = math.atan2(dy_dx * W, W)
                compression = 0.5 + 0.5 * math.sin(wave_phase)
                alpha = (0.16 + 0.16 * compression) * alpha_scale
                normal = tangent + math.pi / 2.0
                gap = 14.0 + 10.0 * compression
                crest = (x + math.cos(normal) * gap, y + math.sin(normal) * gap)
                trough = (x - math.cos(normal) * gap, y - math.sin(normal) * gap)
                sx = 78.0 + 36.0 * compression
                sy = 9.0 + 4.0 * compression
                # Alternating orientation: crest/trough duality. The rows are
                # phase locked so the sheet reads as one water body.
                draw_flat_crescent(frame, crest, sx, sy, tangent, alpha=alpha * 0.76, flip=(band_idx % 2 == 0))
                draw_flat_crescent(frame, trough, sx * 0.86, sy * 0.86, tangent + math.pi, alpha=alpha * 0.58, flip=(band_idx % 2 == 1))
                if col % 4 == band_idx % 4:
                    draw_circle(frame, (x - 42.0, y), 3.7 + 1.8 * compression, alpha=alpha * 0.35)
                if col % 5 == (band_idx + 2) % 5:
                    draw_flat_trigon(frame, (x + 92.0, y), 18.0, 13.0, tangent, alpha=alpha * 0.34)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  duality current sheet v005 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural duality current study",
        test="A cohesive water/current sheet built from phase-shifted peak/trough crescent bands.",
        method="S-curve bands with compression/decompression, alternating crest/trough crescent orientation, small circles and trigons as accents.",
        layer_role="Water/current layer. Keep separate from fish layers; mix under footage or fish as continuous water motion.",
    )


def render_articulated_fish_glyph() -> ClipResult:
    out = OUT_DIR / "03_articulated_fish_glyph_v005_black_screen.mp4"
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        phase = 2.0 * math.pi * t / 1.95
        frame = black_canvas()
        center = (W * 0.50 + 12.0 * math.sin(t * 0.42), H * 0.50 + 8.0 * math.sin(t * 0.70))
        draw_fish_v5(frame, center, 435.0, 0.0, phase, alpha=0.80, bend=0.073, body_alpha=0.64)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  articulated fish glyph v005 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural grammar-built fish study",
        test="Clearer articulated fish silhouette with larger body circle, eye, fins, stronger taper, and smoother bend.",
        method="Primitive fish drawn along one sine-bending spine: trigon head, crescent gill, circle body, tapering crescents, fin accents, trigon tail.",
        layer_role="Fish figure layer. Review independently before showing the H1-derived placement layer.",
    )


def detect_salmon_candidates(frame: np.ndarray, flow: np.ndarray | None) -> list[dict[str, float]]:
    small_w, small_h = 960, 540
    sx = W / small_w
    sy = H / small_h
    small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    work = cv2.GaussianBlur(gray, (7, 7), 0)
    burn_h = int(small_h * 0.085)
    work[small_h - burn_h :, :] = 180
    bg = cv2.GaussianBlur(work, (0, 0), 23)
    score = cv2.subtract(bg, work)
    mask = ((score > 9) & (work < 150)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=1)
    num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    out: list[dict[str, float]] = []
    for comp_idx in range(1, num):
        x, y, cw, ch, area = stats[comp_idx]
        touches_edge = x <= 2 or y <= 2 or x + cw >= small_w - 2 or y + ch >= small_h - burn_h - 2
        if touches_edge:
            continue
        aspect = cw / max(1, ch)
        extent = area / max(1, cw * ch)
        if not (210 <= area <= 14000 and 0.75 <= aspect <= 8.25 and 12 <= cw <= 260 and 7 <= ch <= 120 and extent > 0.12):
            continue
        cx = float(cents[comp_idx][0]) * sx
        cy = float(cents[comp_idx][1]) * sy
        ys, xs = np.where(labels[y : y + ch, x : x + cw] == comp_idx)
        angle = 0.0
        if len(xs) >= 8:
            pts = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
            pts -= pts.mean(axis=0, keepdims=True)
            cov = pts.T @ pts / max(1, len(pts) - 1)
            vals, vecs = np.linalg.eigh(cov)
            major = vecs[:, int(np.argmax(vals))]
            axis = math.atan2(float(major[1]), float(major[0]))
            if math.cos(axis) < 0:
                axis += math.pi
            angle = axis
        if flow is not None:
            fx, fy = sample_flow(flow, cx, cy)
            if math.hypot(fx, fy) > 0.16:
                # Disambiguate PCA axis so the trigon head leads along motion.
                if math.cos(angle) * fx + math.sin(angle) * fy < 0:
                    angle += math.pi
                angle = smooth_angle(angle, math.atan2(fy, fx), amount=0.22)
        out.append({"x": cx, "y": cy, "angle": angle, "area": float(area) * sx * sy})
    out.sort(key=lambda d: d["area"], reverse=True)
    kept: list[dict[str, float]] = []
    for det in out:
        if len(kept) >= 5:
            break
        if all(math.hypot(det["x"] - prev["x"], det["y"] - prev["y"]) > 230 for prev in kept):
            kept.append(det)
    return kept


def track_update(tracks: list[dict[str, float]], detections: list[dict[str, float]], next_id: int, frame_idx: int) -> tuple[list[dict[str, float]], int]:
    assigned: set[int] = set()
    for track in tracks:
        best_i = -1
        best_d = 9999.0
        for i, det in enumerate(detections):
            if i in assigned:
                continue
            dist = math.hypot(det["x"] - track["x"], det["y"] - track["y"])
            if dist < best_d:
                best_d = dist
                best_i = i
        if best_i >= 0 and best_d < 185.0:
            det = detections[best_i]
            assigned.add(best_i)
            track["x"] = track["x"] * 0.72 + det["x"] * 0.28
            track["y"] = track["y"] * 0.72 + det["y"] * 0.28
            track["angle"] = smooth_angle(track["angle"], det["angle"], amount=0.16)
            target_len = max(105.0, min(240.0, math.sqrt(det["area"]) * 1.36))
            track["length"] = track["length"] * 0.80 + target_len * 0.20
            track["age"] += 1
            track["missing"] = 0
            track["seen_frame"] = frame_idx
        else:
            track["missing"] += 1

    for i, det in enumerate(detections):
        if i in assigned or len(tracks) >= 7:
            continue
        tracks.append(
            {
                "id": float(next_id),
                "x": det["x"],
                "y": det["y"],
                "angle": det["angle"],
                "length": max(105.0, min(240.0, math.sqrt(det["area"]) * 1.36)),
                "age": 0.0,
                "missing": 0.0,
                "phase_offset": det["x"] * 0.012 + det["y"] * 0.006,
                "seen_frame": float(frame_idx),
            }
        )
        next_id += 1
    tracks = [track for track in tracks if track["missing"] <= 12]
    tracks.sort(key=lambda tr: (tr["missing"], -tr["age"]))
    return tracks[:6], next_id


def render_salmon_proxy_articulated_smoothed() -> ClipResult:
    out = OUT_DIR / "04_salmon_proxy_articulated_smoothed_v005_black_screen.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    writer = H264Writer(out)
    prev_raw = reader.frame(0)
    tracks: list[dict[str, float]] = []
    next_id = 1
    active_counts: list[int] = []
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        detections = detect_salmon_candidates(raw, flow)
        tracks, next_id = track_update(tracks, detections, next_id, fi)
        frame = black_canvas()
        t = fi / FPS
        active = 0
        for track in tracks:
            fade_in = min(1.0, track["age"] / 10.0)
            fade_out = max(0.0, 1.0 - track["missing"] / 12.0)
            alpha = 0.56 * fade_in * fade_out
            if alpha < 0.035:
                continue
            active += 1
            phase = 2.0 * math.pi * t / 1.70 + track["phase_offset"]
            draw_fish_v5(
                frame,
                (track["x"], track["y"]),
                track["length"],
                track["angle"],
                phase,
                alpha=alpha,
                bend=0.070,
                body_alpha=0.50,
            )
        active_counts.append(active)
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            avg = sum(active_counts[-48:]) / max(1, len(active_counts[-48:]))
            print(f"  salmon proxy smoothed v005 {fi + 1}/{N_FRAMES} avg active={avg:.1f}", flush=True)
    writer.close()
    reader.close()
    avg_active = sum(active_counts) / max(1, len(active_counts))
    return ClipResult(
        filename=out.name,
        source=str(H1_SALMON.relative_to(ROOT)),
        test="H1-derived articulated fish with head-first orientation, persistent tracks, fade in/out, and smoother bend.",
        method="Local-darkness detections feed nearest-neighbor tracks; PCA axis is disambiguated with local optical flow so trigon head leads.",
        layer_role="Fish layer only. Keep separate from water topology/current layers for Austin review.",
        dynamic_note=f"Average active smoothed fish tracks per frame: {avg_active:.1f}.",
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
        cv2.putText(thumb, Path(result.filename).stem[:46], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
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
        "# Primitive Water Grammar v005 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Layer-only pure-black clips; no SD, LoRA, SAM, YOLO, named chiefs/specific people, or new whale/tanker/icon scenes.",
        "",
        "## Darren's v004 Feedback Summary",
        "",
        "- Keep the v004 perspective ripple plane direction; it is working.",
        "- The salmon proxy is interesting, but the fish feel stiff and marker-like.",
        "- The current glyph can read as circle head/body plus crescent/trigon tail, so fish and water grammar need stronger separation.",
        "- Try a more fish-like primitive body: trigon head -> crescent gill/neck -> circle body/joint -> tapering crescents -> trigon tail.",
        "- Add subtle swimming bend through a curved spine and tail phase lag.",
        "- Make the water surface reusable as a tilted/warped plane, and make current feel like a continuous sheet/body of water.",
        "",
        "## v004 -> v005 Changes",
        "",
        "- Preserved the perspective ripple plane and made surface orientation/topology explicit through a simple UV warp before projection.",
        "- Rebuilt current as a duality sheet: S-curve rows, crest/trough pairs, compression/decompression, and alternating crescent orientation.",
        "- Improved the standalone fish silhouette with larger body circle, small eye, fin accents, stronger taper, and smoother bend.",
        "- Improved H1-derived fish placement with head-first disambiguation, persistent nearest-neighbor tracks, temporal smoothing, and fade in/out.",
        "- Fish and water remain separate black-screen Resolume layers.",
        "",
        "## Review Order",
        "",
        "1. `01_perspective_ripple_plane_topology_v005_black_screen.mp4`",
        "2. `02_duality_current_sheet_v005_black_screen.mp4`",
        "3. `03_articulated_fish_glyph_v005_black_screen.mp4`",
        "4. `04_salmon_proxy_articulated_smoothed_v005_black_screen.mp4`",
        "",
        "## Water Topology/Current Questions",
        "",
        "- Should water surfaces be flat head-on, or can we use perspective planes?",
        "- Does the surface-orientation/topology idea feel useful for river/ocean/lake layers?",
        "- Does the duality current sheet read as a continuous water body rather than separate markers?",
        "- Should fish and water remain separate layers in Resolume?",
        "",
        "## Grammar-Built Fish Figure Questions",
        "",
        "- Does this articulated primitive fish feel acceptable as a new grammar-built figure?",
        "- Is trigon head / circle body / crescent body / trigon tail a better ordering?",
        "- Are small circle eyes and simple fin primitives acceptable, or should the fish stay more abstract?",
        "- Does the H1-derived smoothed fish layer now read head-first with tail trailing?",
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
                f"- Source: `{result.source}`",
                f"- Technical method: {result.method}",
                f"- Layer role: {result.layer_role}",
            ]
        )
        if result.dynamic_note:
            lines.append(f"- Runtime note: {result.dynamic_note}")
        lines.extend(
            [
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
    print(f"Writing Primitive Water Grammar v005 to {OUT_DIR}", flush=True)
    results = [
        render_perspective_ripple_topology(),
        render_duality_current_sheet(),
        render_articulated_fish_glyph(),
        render_salmon_proxy_articulated_smoothed(),
    ]
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
