#!/usr/bin/env python3.11
"""
Primitive cycle motion v002.

Internal black-screen additive studies for the May 20 primitive-cycle lane.
No SD, no LoRA, no Austin source artwork, no animals, no topology/cymatics,
and no public cultural claim. The renderer keeps circle / crescent / trigon
as procedural morphology classes with declared origin, direction, attenuation,
and Austin-review-needed status.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "primitive_cycle_motion_v002_2026-05-20"
)

W = 1920
H = 1080
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)
MID_FRAME = N_FRAMES // 2

# RGB colors; draw helpers convert to BGR for OpenCV frames.
BLACK = (0, 0, 0)
ORIGIN_RGB = (255, 202, 96)
CRESCENT_RGB = (234, 239, 231)
TRIGON_RGB = (220, 93, 64)
CURRENT_RGB = (91, 183, 196)
DEBUG_RGB = (118, 224, 210)
LABEL_RGB = (235, 240, 228)
DIM_RGB = (46, 74, 78)

MORPH_N = 216


@dataclass(frozen=True)
class LoopSpec:
    key: str
    title: str
    description: str
    origin_role: str
    direction_role: str
    renderer: Callable[[int, bool], np.ndarray]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(value: float) -> float:
    t = clamp01(value)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def window01(phase: float, start: float, end: float, fade: float = 0.10) -> float:
    """Soft rectangular window over normalized phase."""
    if phase < start or phase > end:
        return 0.0
    return min(smoothstep((phase - start) / fade), smoothstep((end - phase) / fade))


def periodic_window(phase: float, center: float, width: float) -> float:
    """Cosine window around center on a 0..1 periodic phase."""
    d = abs((phase - center + 0.5) % 1.0 - 0.5)
    if d >= width * 0.5:
        return 0.0
    return 0.5 + 0.5 * math.cos(math.pi * d / (width * 0.5))


def ease_between(phase: float, start: float, end: float) -> float:
    return smootherstep((phase - start) / max(1e-6, end - start))


def mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def rotate_points(points: np.ndarray, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    return points @ rot.T


def transform_points(
    base: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
) -> np.ndarray:
    pts = base.astype(np.float32).copy()
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    pts = rotate_points(pts, angle)
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]
    return pts


def quadratic_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    samples: int,
    *,
    include_endpoint: bool = False,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    stop = samples + 1 if include_endpoint else samples
    for i in range(stop):
        t = i / max(1, samples)
        u = 1.0 - t
        pts.append(
            (
                u * u * p0[0] + 2.0 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2.0 * u * t * p1[1] + t * t * p2[1],
            )
        )
    return pts


def cubic_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    samples: int,
    *,
    include_endpoint: bool = False,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    stop = samples + 1 if include_endpoint else samples
    for i in range(stop):
        t = i / max(1, samples)
        u = 1.0 - t
        pts.append(
            (
                u * u * u * p0[0]
                + 3.0 * u * u * t * p1[0]
                + 3.0 * u * t * t * p2[0]
                + t * t * t * p3[0],
                u * u * u * p0[1]
                + 3.0 * u * u * t * p1[1]
                + 3.0 * u * t * t * p2[1]
                + t * t * t * p3[1],
            )
        )
    return pts


def circle_base(n: int = MORPH_N) -> np.ndarray:
    pts = []
    for i in range(n):
        a = -math.pi / 2.0 + math.tau * i / n
        pts.append((0.63 * math.cos(a), 0.63 * math.sin(a)))
    return np.array(pts, dtype=np.float32)


def crescent_base(n: int = MORPH_N, *, phase_variant: float = 0.0) -> np.ndarray:
    """Local +x is release direction; the crescent cups back toward -x."""
    half = n // 2
    top = (-0.42, -0.63 - 0.035 * phase_variant)
    bottom = (-0.42, 0.63 + 0.030 * phase_variant)
    outer_ctrl_a = (0.45 + 0.06 * phase_variant, -0.76)
    outer_ctrl_b = (0.88, 0.10 + 0.02 * phase_variant)
    inner_ctrl_a = (-0.03 + 0.05 * phase_variant, 0.34)
    inner_ctrl_b = (-0.02, -0.34)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(top, outer_ctrl_a, outer_ctrl_b, bottom, half))
    pts.extend(cubic_curve(bottom, inner_ctrl_a, inner_ctrl_b, top, n - half))
    return np.array(pts, dtype=np.float32)


def trigon_base(n: int = MORPH_N) -> np.ndarray:
    """Curved pointed trigon with shaped rear base; local +x is release."""
    upper = n // 3 + 20
    lower = n // 3 + 20
    rear = n - upper - lower
    rear_top = (-0.63, -0.48)
    rear_bottom = (-0.61, 0.48)
    tip = (0.98, 0.00)
    pts: list[tuple[float, float]] = []
    pts.extend(cubic_curve(rear_top, (-0.18, -0.66), (0.58, -0.34), tip, upper))
    pts.extend(cubic_curve(tip, (0.57, 0.33), (-0.20, 0.66), rear_bottom, lower))
    pts.extend(cubic_curve(rear_bottom, (-0.82, 0.26), (-0.82, -0.25), rear_top, rear))
    return np.array(pts, dtype=np.float32)


CIRCLE_BASE = circle_base()
CRESCENT_BASE_A = crescent_base(phase_variant=0.0)
CRESCENT_BASE_B = crescent_base(phase_variant=1.0)
TRIGON_BASE = trigon_base()


def new_frame() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)


def add_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    rgb: tuple[int, int, int],
    alpha: float,
    *,
    glow: float = 0.0,
) -> None:
    if alpha <= 0.0:
        return
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = rgb_to_bgr(rgb)
    a = (mask.astype(np.float32) / 255.0) * alpha
    if glow > 0.0:
        blur_radius = max(9, int(max(mask.shape) * 0.11) | 1)
        glow_mask = cv2.GaussianBlur(mask, (blur_radius, blur_radius), 0)
        crop += color * ((glow_mask.astype(np.float32) / 255.0) * glow)[..., None]
    crop += color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def draw_poly_additive(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    glow: float = 0.08,
    outline_alpha: float = 0.12,
) -> None:
    if alpha <= 0.0:
        return
    pts_i = np.round(pts).astype(np.int32)
    if pts_i.size == 0:
        return
    pad = 44
    x0 = max(0, int(pts_i[:, 0].min()) - pad)
    y0 = max(0, int(pts_i[:, 1].min()) - pad)
    x1 = min(W, int(pts_i[:, 0].max()) + pad + 1)
    y1 = min(H, int(pts_i[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = pts_i.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(mask, [local], 255, lineType=cv2.LINE_AA)
    add_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha, glow=glow)
    if outline_alpha > 0.0:
        outline = np.zeros_like(mask)
        cv2.polylines(outline, [local], True, 255, 2, lineType=cv2.LINE_AA)
        add_mask(frame, outline, (x0, y0, x1, y1), rgb, outline_alpha, glow=0.0)


def draw_circle_additive(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    glow: float = 0.10,
    outline_alpha: float = 0.12,
) -> None:
    if alpha <= 0.0 or radius <= 0.0:
        return
    cx, cy = center
    pad = int(radius + 48)
    x0 = max(0, int(cx) - pad)
    y0 = max(0, int(cy) - pad)
    x1 = min(W, int(cx) + pad + 1)
    y1 = min(H, int(cy) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local_c = (int(round(cx - x0)), int(round(cy - y0)))
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(mask, local_c, int(round(radius)), 255, -1, lineType=cv2.LINE_AA)
    add_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha, glow=glow)
    if outline_alpha > 0.0:
        outline = np.zeros_like(mask)
        cv2.circle(outline, local_c, int(round(radius)), 255, 2, lineType=cv2.LINE_AA)
        add_mask(frame, outline, (x0, y0, x1, y1), rgb, outline_alpha, glow=0.0)


def draw_line_additive(
    frame: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
) -> None:
    overlay = np.zeros_like(frame)
    cv2.line(
        overlay,
        (round(p0[0]), round(p0[1])),
        (round(p1[0]), round(p1[1])),
        (rgb[2], rgb[1], rgb[0]),
        thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_path_additive(
    frame: np.ndarray,
    pts: list[tuple[float, float]],
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: int = 2,
) -> None:
    overlay = np.zeros_like(frame)
    arr = np.round(np.array(pts, dtype=np.float32)).astype(np.int32)
    cv2.polylines(overlay, [arr], False, (rgb[2], rgb[1], rgb[0]), thickness, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_text(frame: np.ndarray, text: str, xy: tuple[int, int], rgb: tuple[int, int, int] = LABEL_RGB, scale: float = 0.48) -> None:
    cv2.putText(
        frame,
        text,
        xy,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (rgb[2], rgb[1], rgb[0]),
        1,
        lineType=cv2.LINE_AA,
    )


def draw_arrow_debug(
    frame: np.ndarray,
    p0: tuple[float, float],
    p1: tuple[float, float],
    rgb: tuple[int, int, int] = DEBUG_RGB,
) -> None:
    cv2.arrowedLine(
        frame,
        (round(p0[0]), round(p0[1])),
        (round(p1[0]), round(p1[1])),
        (rgb[2], rgb[1], rgb[0]),
        2,
        line_type=cv2.LINE_AA,
        tipLength=0.08,
    )


class H264Writer:
    def __init__(self, path: Path, *, fps: int = FPS, size: tuple[int, int] = (W, H)):
        path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{size[0]}x{size[1]}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-frames:v",
            str(N_FRAMES),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.path = path

    def write(self, frame_bgr: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(frame_bgr.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with exit code {rc}")


def morph_base_for_phase(phase: float) -> tuple[np.ndarray, tuple[int, int, int], str]:
    states = [
        (CIRCLE_BASE, ORIGIN_RGB, "circle/origin"),
        (CRESCENT_BASE_A, CRESCENT_RGB, "crescent/cupping"),
        (CRESCENT_BASE_B, CRESCENT_RGB, "crescent/phase"),
        (TRIGON_BASE, TRIGON_RGB, "trigon/release"),
        (CIRCLE_BASE, ORIGIN_RGB, "circle/return"),
    ]
    pos = phase * 4.0
    idx = min(3, int(pos))
    local = pos - idx
    t = smootherstep(local)
    a_pts, a_rgb, a_label = states[idx]
    b_pts, b_rgb, b_label = states[idx + 1]
    pts = a_pts * (1.0 - t) + b_pts * t
    rgb = tuple(int(round(mix(a_rgb[i], b_rgb[i], t))) for i in range(3))
    label = b_label if t > 0.55 else a_label
    return pts, rgb, label


def render_single_shape_cycle(fi: int, debug: bool = False) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    pts, rgb, label = morph_base_for_phase(phase)
    center = (W * 0.50, H * 0.51)
    spin = math.radians(16.0 * math.sin(math.tau * phase) + 10.0 * phase)
    breath = 1.0 + 0.035 * math.sin(math.tau * phase * 2.0)
    draw_poly_additive(frame, transform_points(pts, center, 215.0 * breath, 215.0 * breath, spin), rgb, alpha=0.78, glow=0.16)
    draw_circle_additive(frame, center, 7.5, ORIGIN_RGB, alpha=0.28, glow=0.05, outline_alpha=0.0)
    if debug:
        draw_circle_additive(frame, center, 10.0, DEBUG_RGB, alpha=0.45, glow=0.03)
        draw_arrow_debug(frame, center, (center[0] + 260.0 * math.cos(spin), center[1] + 260.0 * math.sin(spin)))
        draw_text(frame, "single_shape_cycle_v002", (72, 76))
        draw_text(frame, f"state: {label}", (72, 112))
        draw_text(frame, "role: one glyph cycles circle -> crescent -> crescent -> trigon -> circle", (72, 148))
    return frame


def phrase_centers(
    origin: tuple[float, float],
    angle: float,
    spacing: float,
    *,
    release: float = 1.0,
) -> list[tuple[str, tuple[float, float], float, float]]:
    offsets = [0.0, 1.15, 2.10, 3.18]
    kinds = ["circle", "crescent", "crescent", "trigon"]
    sizes = [31.0, 65.0, 58.0, 54.0]
    atten = [1.00, 0.86, 0.70, 0.54]
    dx = math.cos(angle)
    dy = math.sin(angle)
    out = []
    for kind, off, size, att in zip(kinds, offsets, sizes, atten):
        d = spacing * off * release
        out.append((kind, (origin[0] + dx * d, origin[1] + dy * d), size, att))
    return out


def draw_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    angle: float,
    *,
    alpha: float,
    spacing: float,
    reveal: float = 1.0,
    scale: float = 1.0,
    release: float = 1.0,
    debug: bool = False,
    phrase_id: str = "",
) -> None:
    stages = phrase_centers(origin, angle, spacing, release=release)
    stage_reveals = [
        smoothstep((reveal - 0.00) / 0.18),
        smoothstep((reveal - 0.20) / 0.20),
        smoothstep((reveal - 0.43) / 0.22),
        smoothstep((reveal - 0.68) / 0.20),
    ]
    for idx, (kind, center, size, att) in enumerate(stages):
        a = alpha * att * stage_reveals[idx]
        if a <= 0.001:
            continue
        if kind == "circle":
            draw_circle_additive(frame, center, size * 0.45 * scale, ORIGIN_RGB, alpha=a * 0.85, glow=0.08 * a)
        elif kind == "crescent":
            base = CRESCENT_BASE_A if idx == 1 else CRESCENT_BASE_B
            pts = transform_points(base, center, size * scale, size * scale, angle)
            draw_poly_additive(frame, pts, CRESCENT_RGB, alpha=a, glow=0.07 * a)
        else:
            pts = transform_points(TRIGON_BASE, center, size * scale, size * scale, angle)
            draw_poly_additive(frame, pts, TRIGON_RGB, alpha=a * 0.96, glow=0.08 * a)
    if debug:
        line_end = (
            origin[0] + math.cos(angle) * spacing * 3.55 * release,
            origin[1] + math.sin(angle) * spacing * 3.55 * release,
        )
        draw_arrow_debug(frame, origin, line_end)
        draw_circle_additive(frame, origin, 5.0, DEBUG_RGB, alpha=0.55, glow=0.0)
        for idx, (kind, center, _size, _att) in enumerate(stages):
            draw_text(frame, f"{phrase_id}{idx}:{kind}", (round(center[0] + 12), round(center[1] - 12)), DEBUG_RGB, scale=0.42)


def render_eye_flow_phrase(fi: int, debug: bool = False) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    origin = (W * 0.29, H * 0.51)
    angle = math.radians(-5.0)
    reveal = smoothstep(phase / 0.78)
    fade = min(smoothstep((phase - 0.02) / 0.12), smoothstep((0.97 - phase) / 0.18))
    release = 0.74 + 0.30 * smoothstep(phase / 0.82)
    draw_line_additive(
        frame,
        (origin[0] + 20.0, origin[1]),
        (origin[0] + math.cos(angle) * 650.0, origin[1] + math.sin(angle) * 650.0),
        DIM_RGB,
        alpha=0.12 * fade,
        thickness=2,
    )
    boundary_pulse = 0.5 + 0.5 * math.cos(math.tau * phase)
    draw_circle_additive(frame, origin, 14.0 + 3.0 * boundary_pulse, ORIGIN_RGB, alpha=0.22 + 0.10 * boundary_pulse, glow=0.08)
    draw_phrase(
        frame,
        origin,
        angle,
        alpha=0.78 * fade,
        spacing=142.0,
        reveal=reveal,
        release=release,
        scale=1.08,
        debug=debug,
        phrase_id="eye.",
    )
    if debug:
        draw_text(frame, "eye_flow_phrase_v002", (72, 76))
        draw_text(frame, "circle focal point releases crescent / crescent / trigon along one eye-flow line", (72, 112))
        draw_text(frame, "crescent concavity cups the circle; trigon points downstream with attenuation", (72, 148))
    return frame


def render_radial_ripple_cycle(fi: int, debug: bool = False) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    origin = (W * 0.50, H * 0.52)
    draw_circle_additive(frame, origin, 19.0 + 3.0 * math.sin(math.tau * phase), ORIGIN_RGB, alpha=0.55, glow=0.11)
    directions = [math.radians(d) for d in (-18, 18, 55, 102, 146, 214, 260, 305)]
    starts = [0.04, 0.12, 0.22, 0.34, 0.47, 0.58, 0.70, 0.82]
    for idx, (angle, start) in enumerate(zip(directions, starts)):
        active = window01(phase, start, min(0.98, start + 0.19), fade=0.045)
        if active <= 0.0:
            continue
        local = smoothstep((phase - start) / 0.19)
        spacing = mix(54.0, 118.0, local)
        alpha = 0.58 * active * (1.0 - 0.16 * idx / len(directions))
        draw_phrase(
            frame,
            origin,
            angle,
            alpha=alpha,
            spacing=spacing,
            reveal=local,
            release=mix(0.68, 1.10, local),
            scale=mix(0.72, 0.92, local),
            debug=debug and idx in (1, 4),
            phrase_id=f"r{idx}.",
        )
        if debug:
            end = (
                origin[0] + math.cos(angle) * spacing * 3.75,
                origin[1] + math.sin(angle) * spacing * 3.75,
            )
            draw_arrow_debug(frame, origin, end)
    if debug:
        draw_text(frame, "radial_ripple_cycle_v002", (72, 76))
        draw_text(frame, "one impact origin; sparse phrase cycles radiate with directional attenuation", (72, 112))
        draw_text(frame, "not topology/cymatics: no construction circles, no seed/flower scaffold", (72, 148))
    return frame


def bezier_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    u = 1.0 - t
    return (
        u * u * u * p0[0] + 3.0 * u * u * t * p1[0] + 3.0 * u * t * t * p2[0] + t * t * t * p3[0],
        u * u * u * p0[1] + 3.0 * u * u * t * p1[1] + 3.0 * u * t * t * p2[1] + t * t * t * p3[1],
    )


def bezier_tangent(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> float:
    u = 1.0 - t
    dx = 3.0 * u * u * (p1[0] - p0[0]) + 6.0 * u * t * (p2[0] - p1[0]) + 3.0 * t * t * (p3[0] - p2[0])
    dy = 3.0 * u * u * (p1[1] - p0[1]) + 6.0 * u * t * (p2[1] - p1[1]) + 3.0 * t * t * (p3[1] - p2[1])
    return math.atan2(dy, dx)


CURRENT_P0 = (-140.0, H * 0.63)
CURRENT_P1 = (W * 0.25, H * 0.30)
CURRENT_P2 = (W * 0.70, H * 0.78)
CURRENT_P3 = (W + 160.0, H * 0.37)


def current_path_points(samples: int = 80) -> list[tuple[float, float]]:
    return [bezier_point(CURRENT_P0, CURRENT_P1, CURRENT_P2, CURRENT_P3, i / (samples - 1)) for i in range(samples)]


def render_current_line_cycle(fi: int, debug: bool = False) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    path_pts = current_path_points()
    draw_path_additive(frame, path_pts, DIM_RGB, alpha=0.18, thickness=2)
    for lane, offset in enumerate((0.00, 0.34)):
        p = (phase + offset) % 1.0
        edge = math.sin(math.pi * p)
        if edge <= 0.04:
            continue
        s = smoothstep(p)
        center = bezier_point(CURRENT_P0, CURRENT_P1, CURRENT_P2, CURRENT_P3, s)
        angle = bezier_tangent(CURRENT_P0, CURRENT_P1, CURRENT_P2, CURRENT_P3, s)
        normal = (-math.sin(angle), math.cos(angle))
        origin = (center[0] + normal[0] * (lane - 0.5) * 55.0, center[1] + normal[1] * (lane - 0.5) * 55.0)
        draw_phrase(
            frame,
            origin,
            angle,
            alpha=0.53 * edge,
            spacing=76.0,
            reveal=smoothstep(p / 0.78),
            release=1.0,
            scale=0.74,
            debug=debug and lane == 0,
            phrase_id="cur.",
        )
    if debug:
        draw_text(frame, "current_line_cycle_v002", (72, 76))
        draw_text(frame, "same phrase travels along one authored current spline", (72, 112))
        draw_text(frame, "orientation follows tangent; sparse duplicate is phase-offset on same current family", (72, 148))
    return frame


FIELD_PHRASES = [
    ((W * 0.18, H * 0.30), math.radians(11), 0.03, 0.82, 0.90),
    ((W * 0.36, H * 0.43), math.radians(-8), 0.19, 0.78, 0.82),
    ((W * 0.58, H * 0.31), math.radians(19), 0.36, 0.74, 0.80),
    ((W * 0.77, H * 0.47), math.radians(-17), 0.52, 0.70, 0.76),
    ((W * 0.28, H * 0.71), math.radians(5), 0.68, 0.66, 0.74),
    ((W * 0.51, H * 0.66), math.radians(24), 0.82, 0.68, 0.73),
    ((W * 0.72, H * 0.74), math.radians(-4), 0.43, 0.60, 0.68),
]


def render_field_breathing_cycle(fi: int, debug: bool = False) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    for idx, (origin, angle, offset, max_alpha, scale) in enumerate(FIELD_PHRASES):
        local = (phase + offset) % 1.0
        breath = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(math.tau * local))
        release = 0.90 + 0.10 * math.sin(math.tau * local + 0.45)
        reveal = 0.88 + 0.12 * math.sin(math.tau * local - 0.35)
        draw_line_additive(
            frame,
            origin,
            (origin[0] + math.cos(angle) * 310.0, origin[1] + math.sin(angle) * 310.0),
            DIM_RGB,
            alpha=0.055 * breath,
            thickness=1,
        )
        draw_phrase(
            frame,
            origin,
            angle,
            alpha=max_alpha * 0.42 * breath,
            spacing=68.0,
            reveal=reveal,
            release=release,
            scale=scale,
            debug=debug and idx in (1, 5),
            phrase_id=f"f{idx}.",
        )
    if debug:
        draw_text(frame, "field_breathing_cycle_v002", (72, 76))
        draw_text(frame, "sparse authored field; each phrase has origin, direction, and attenuation", (72, 112))
        draw_text(frame, "phase offsets create breathing, not random scatter or wallpaper density", (72, 148))
    return frame


def loop_specs() -> list[LoopSpec]:
    return [
        LoopSpec(
            key="single_shape_cycle_v002",
            title="Single Shape Cycle v002",
            description="One luminous glyph cycles circle -> crescent -> crescent -> curved trigon -> circle with subtle spin.",
            origin_role="origin / pivot / return",
            direction_role="morph continuity; trigon release emerges from crescent phase",
            renderer=render_single_shape_cycle,
        ),
        LoopSpec(
            key="eye_flow_phrase_v002",
            title="Eye Flow Phrase v002",
            description="A circle focal point releases crescent / crescent / trigon along one line, echoing the meeting note's eye-flow explanation.",
            origin_role="circle focal point / impact",
            direction_role="line-led release; crescents cup origin and trigon points downstream",
            renderer=render_eye_flow_phrase,
        ),
        LoopSpec(
            key="radial_ripple_cycle_v002",
            title="Radial Ripple Cycle v002",
            description="Sparse phrase cycles radiate outward from one origin as ripple/sun logic without topology construction.",
            origin_role="single ripple impact / radial center",
            direction_role="outward release with attenuation by distance and time",
            renderer=render_radial_ripple_cycle,
        ),
        LoopSpec(
            key="current_line_cycle_v002",
            title="Current Line Cycle v002",
            description="The same circle / crescent / crescent / trigon phrase travels along a curved current spline.",
            origin_role="moving phrase anchor on authored current",
            direction_role="spline tangent; common-fate current family",
            renderer=render_current_line_cycle,
        ),
        LoopSpec(
            key="field_breathing_cycle_v002",
            title="Field Breathing Cycle v002",
            description="Sparse field of phrase cycles with authored origins, directions, attenuation, and phase offsets.",
            origin_role="per-phrase circle anchor / current knot",
            direction_role="authored local flow vector; no random scatter",
            renderer=render_field_breathing_cycle,
        ),
    ]


def save_png(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), frame)
    if not ok:
        raise RuntimeError(f"Could not write {path}")


def render_loop(spec: LoopSpec) -> dict[str, str]:
    print(f"Rendering {spec.key} ({N_FRAMES} frames)", flush=True)
    mp4_path = OUT_DIR / f"{spec.key}.mp4"
    writer = H264Writer(mp4_path)
    stills: dict[int, np.ndarray] = {}
    sample_frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    for fi in range(N_FRAMES):
        frame = spec.renderer(fi, False)
        writer.write(frame)
        if fi in sample_frames:
            stills[fi] = frame.copy()
        if (fi + 1) % 48 == 0:
            print(f"  {spec.key}: {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    midpoint = OUT_DIR / f"{spec.key}_midpoint_f{MID_FRAME:03d}.png"
    debug = OUT_DIR / f"{spec.key}_debug_midpoint_f{MID_FRAME:03d}.png"
    save_png(midpoint, stills[MID_FRAME])
    save_png(debug, spec.renderer(MID_FRAME, True))
    for fi, frame in stills.items():
        save_png(OUT_DIR / "sample_stills" / f"{spec.key}_f{fi:03d}.png", frame)
    return {
        "mp4": str(mp4_path.relative_to(ROOT)),
        "midpoint_still": str(midpoint.relative_to(ROOT)),
        "debug_midpoint_still": str(debug.relative_to(ROOT)),
    }


def build_contact_sheet(specs: list[LoopSpec]) -> Path:
    frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    cell_w = 320
    cell_h = 180
    label_h = 48
    left_w = 300
    cols = len(frames) + 1
    sheet_w = left_w + cols * cell_w
    sheet_h = label_h + len(specs) * cell_h
    sheet = np.zeros((sheet_h, sheet_w, 3), dtype=np.uint8)
    headers = ["start", "quarter", "midpoint", "three-quarter", "end", "debug mid"]
    for col, text in enumerate(headers):
        draw_text(sheet, text, (left_w + col * cell_w + 12, 30), LABEL_RGB, scale=0.48)
    draw_text(sheet, "primitive_cycle_motion_v002", (16, 30), LABEL_RGB, scale=0.40)
    for row, spec in enumerate(specs):
        y0 = label_h + row * cell_h
        draw_text(sheet, spec.key, (16, y0 + 36), LABEL_RGB, scale=0.45)
        draw_text(sheet, spec.origin_role[:42], (16, y0 + 66), DEBUG_RGB, scale=0.36)
        row_frames = [spec.renderer(fi, False) for fi in frames]
        row_frames.append(spec.renderer(MID_FRAME, True))
        for col, frame in enumerate(row_frames):
            thumb = cv2.resize(frame, (cell_w, cell_h), interpolation=cv2.INTER_AREA)
            x0 = left_w + col * cell_w
            sheet[y0 : y0 + cell_h, x0 : x0 + cell_w] = thumb
            cv2.rectangle(sheet, (x0, y0), (x0 + cell_w - 1, y0 + cell_h - 1), (34, 42, 42), 1)
    out = OUT_DIR / "primitive_cycle_motion_v002_contact_sheet.png"
    save_png(out, sheet)
    return out


def write_manifest(specs: list[LoopSpec], outputs: dict[str, dict[str, str]], contact_sheet: Path) -> None:
    manifest = {
        "renderer": "scripts/primitive_cycle_motion_v002.py",
        "created": "2026-05-20",
        "status": "INTERNAL R&D. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim.",
        "technical": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frames": N_FRAMES,
            "background": "black",
            "blend": "additive RGB over black",
        },
        "boundaries": [
            "No topology/cymatics/seed-of-life construction.",
            "No fish, animals, SD, LoRA, Austin source artwork, or source-piece replication.",
            "Every phrase has declared origin, direction, and attenuation.",
            "Trigons are curved pointed primitives with shaped rear bases, not crude triangles.",
        ],
        "sources_read": [
            "docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md",
            "docs/space-center/primitive-pattern-language-canon-2026-05-20.md",
            "/Users/darrenzal/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md",
        ],
        "reference_clips": [
            "track2-deterministic/morph_outputs/prim_circle_to_crescent.mp4",
            "track2-deterministic/morph_outputs/prim_crescent_to_trigon.mp4",
            "track2-deterministic/morph_outputs/prim_trigon_to_circle.mp4",
            "track2-deterministic/morph_outputs/coast_salish__circle_to_crescent_001.mp4",
        ],
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "loops": [
            {
                "key": spec.key,
                "title": spec.title,
                "description": spec.description,
                "origin_role": spec.origin_role,
                "direction_role": spec.direction_role,
                "cultural_status": "internal grammar-inspired sketch; Austin review required before any external/public use",
                "primitive_sequence": "circle -> crescent -> crescent -> trigon -> circle/return",
                **outputs[spec.key],
            }
            for spec in specs
        ],
    }
    (OUT_DIR / "primitive_cycle_motion_v002_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def write_readme(specs: list[LoopSpec], outputs: dict[str, dict[str, str]], contact_sheet: Path) -> None:
    lines = [
        "# Primitive Cycle Motion v002 - 2026-05-20",
        "",
        "Status: INTERNAL R&D review packet. Not Austin-approved, not public-ready, not public-use cultural guidance, and not a claim about traditional meaning.",
        "",
        "This packet renders black-screen additive primitive-cycle studies only. It does not use SD, LoRA, Austin source artwork, animals, fish, topology/cymatics, seed-of-life construction, or source-piece replication.",
        "",
        "## Sources Read",
        "",
        "- `docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md`",
        "- `docs/space-center/primitive-pattern-language-canon-2026-05-20.md`",
        "- `/Users/darrenzal/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md`",
        "",
        "## Reference Clips Consulted",
        "",
        "- `track2-deterministic/morph_outputs/prim_circle_to_crescent.mp4`",
        "- `track2-deterministic/morph_outputs/prim_crescent_to_trigon.mp4`",
        "- `track2-deterministic/morph_outputs/prim_trigon_to_circle.mp4`",
        "- `track2-deterministic/morph_outputs/coast_salish__circle_to_crescent_001.mp4`",
        "",
        "## Output Contract",
        "",
        f"- Resolution: `{W}x{H}`",
        f"- Frame rate: `{FPS}fps`",
        f"- Duration: `{DURATION_SECONDS:.1f}s`",
        f"- Frame count: `{N_FRAMES}`",
        "- Background/blend: black-screen additive RGB",
        f"- Contact sheet: `{contact_sheet.name}`",
        "- Sidecar manifest: `primitive_cycle_motion_v002_manifest.json`",
        "",
        "## Rendered Loops",
        "",
    ]
    for spec in specs:
        paths = outputs[spec.key]
        lines.extend(
            [
                f"### {spec.title}",
                "",
                spec.description,
                "",
                f"- MP4: `{Path(paths['mp4']).name}`",
                f"- Midpoint still: `{Path(paths['midpoint_still']).name}`",
                f"- Debug midpoint still: `{Path(paths['debug_midpoint_still']).name}`",
                f"- Origin role: {spec.origin_role}",
                f"- Direction role: {spec.direction_role}",
                "- Cultural status: internal grammar-inspired sketch; Austin review required before any external/public use.",
                "",
            ]
        )
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sample_stills").mkdir(parents=True, exist_ok=True)
    specs = loop_specs()
    outputs: dict[str, dict[str, str]] = {}
    for spec in specs:
        outputs[spec.key] = render_loop(spec)
    contact_sheet = build_contact_sheet(specs)
    write_manifest(specs, outputs, contact_sheet)
    write_readme(specs, outputs, contact_sheet)
    print(f"Done: {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
