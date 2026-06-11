#!/usr/bin/env python3.11
"""
Radial water/sun/snowflake morphology animation v001.

Three restrained 6s black-screen MP4 loops from the strongest v001 radial
still studies. Internal only; Austin-review-needed; not public.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import CRESCENT_BASE, ROOT, draw_poly_alpha
from radial_water_sun_snowflake_morphology_v001 import trigon_points


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/radial_water_sun_snowflake_morphology_animation_v001_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
W = 1920
H = 1080
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)

IVORY = (244, 244, 236)
SOFT_IVORY = (222, 232, 230)
PALE_BLUE = (168, 220, 238)
ICE_BLUE = (198, 236, 246)
SUN_GOLD = (246, 213, 116)
SUN_AMBER = (232, 162, 78)
MIST = (148, 166, 166)
DEEP_FIELD = (32, 58, 65)
BLACK = (0, 0, 0)


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


def canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def blend_local_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    rgb: tuple[int, int, int],
    alpha: float,
) -> None:
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    a = (mask.astype(np.float32) / 255.0) * max(0.0, min(1.0, alpha))
    if not np.any(a > 0):
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    crop[:] = crop * (1.0 - a[..., None]) + color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def phase_wave(phase: float, offset: float = 0.0) -> float:
    return 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase + offset))


def ease01(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def loop_pulse(phase: float, offset: float = 0.0) -> float:
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * ((phase + offset) % 1.0))


def transform_points(base: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float) -> np.ndarray:
    pts = base.copy()
    pts[:, 0] *= sx
    pts[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    out = pts @ rot.T
    out[:, 0] += center[0]
    out[:, 1] += center[1]
    return out


def draw_poly(frame: np.ndarray, pts: np.ndarray, rgb: tuple[int, int, int], *, alpha: float) -> None:
    draw_poly_alpha(frame, pts.astype(np.float32), rgb, alpha=alpha, outline_rgb=rgb, outline_alpha=0.0, outline_thickness=0)


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    draw_poly(frame, transform_points(CRESCENT_BASE, center, sx, sy, angle), rgb, alpha=alpha)


def draw_crescent_cupping(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    angle_to_origin = math.atan2(origin[1] - center[1], origin[0] - center[0])
    draw_crescent(frame, center, sx, sy, angle_to_origin - math.pi, rgb, alpha=alpha)


def draw_trigon(
    frame: np.ndarray,
    center: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.55,
    softness: float = 0.45,
) -> None:
    draw_poly(frame, transform_points(trigon_points(sharpness=sharpness, softness=softness), center, sx, sy, angle), rgb, alpha=alpha)


def draw_trigon_release(
    frame: np.ndarray,
    center: tuple[float, float],
    origin: tuple[float, float],
    sx: float,
    sy: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    sharpness: float = 0.55,
    softness: float = 0.45,
) -> None:
    angle = math.atan2(center[1] - origin[1], center[0] - origin[0])
    draw_trigon(frame, center, sx, sy, angle, rgb, alpha=alpha, sharpness=sharpness, softness=softness)


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
    cx, cy = round(center[0]), round(center[1])
    r = max(1, round(radius))
    pad = r + 4
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r, 255, -1, lineType=cv2.LINE_AA)
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_oval(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    rx, ry = max(1, round(axes[0])), max(1, round(axes[1]))
    pad = max(rx, ry) + 5
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (cx - x0, cy - y0),
        (rx, ry),
        math.degrees(angle),
        0,
        360,
        255,
        -1,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_ring(frame: np.ndarray, center: tuple[float, float], radius: float, thickness: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
    cx, cy = round(center[0]), round(center[1])
    r = max(1, round(radius))
    thick = max(1, round(thickness))
    pad = r + thick + 5
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(
        mask,
        (cx - x0, cy - y0),
        r,
        255,
        thick,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_arc(
    frame: np.ndarray,
    center: tuple[float, float],
    axes: tuple[float, float],
    angle: float,
    start: float,
    end: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    thickness: float,
) -> None:
    cx, cy = round(center[0]), round(center[1])
    rx, ry = max(1, round(axes[0])), max(1, round(axes[1]))
    thick = max(1, round(thickness))
    pad = max(rx, ry) + thick + 6
    x0 = max(0, cx - pad)
    y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1)
    y1 = min(H, cy + pad + 1)
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.ellipse(
        mask,
        (cx - x0, cy - y0),
        (rx, ry),
        math.degrees(angle),
        math.degrees(start),
        math.degrees(end),
        255,
        thick,
        lineType=cv2.LINE_AA,
    )
    blend_local_mask(frame, mask, (x0, y0, x1, y1), rgb, alpha)


def draw_haze(frame: np.ndarray, center: tuple[float, float], radius: float, rgb: tuple[int, int, int], *, alpha: float) -> None:
    # Broad field cue without expensive full-frame Gaussian blur.
    draw_circle(frame, center, radius, rgb, alpha=alpha * 0.36)
    draw_ring(frame, center, radius * 0.72, 4, rgb, alpha=alpha * 0.70)
    draw_ring(frame, center, radius, 3, rgb, alpha=alpha * 0.46)


def radial_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    angle: float,
    *,
    distances: tuple[float, float, float],
    scale: float,
    rgb: tuple[int, int, int],
    trigon_rgb: tuple[int, int, int],
    alpha: float,
    thickness: tuple[float, float] = (1.0, 1.0),
    sharpness: float = 0.55,
    softness: float = 0.45,
) -> None:
    d1, d2, d3 = distances
    c1 = (origin[0] + math.cos(angle) * d1, origin[1] + math.sin(angle) * d1)
    c2 = (origin[0] + math.cos(angle) * d2, origin[1] + math.sin(angle) * d2)
    tri = (origin[0] + math.cos(angle) * d3, origin[1] + math.sin(angle) * d3)
    draw_crescent_cupping(frame, c1, origin, 96 * scale * thickness[0], 66 * scale, rgb, alpha=alpha * 0.90)
    draw_crescent_cupping(frame, c2, origin, 116 * scale * thickness[1], 80 * scale, rgb, alpha=alpha * 0.72)
    draw_trigon_release(frame, tri, origin, 82 * scale, 90 * scale, trigon_rgb, alpha=alpha * 0.56, sharpness=sharpness, softness=softness)


def radial_angles(count: int, *, start: float = 0.0) -> list[float]:
    return [start + 2.0 * math.pi * i / count for i in range(count)]


def render_sun_ripple(phase: float) -> np.ndarray:
    frame = canvas()
    center = (900.0, 545.0)
    slow = phase_wave(phase)
    breathe = 0.94 + 0.085 * slow
    rotate = math.radians(7) + phase * math.radians(10)

    draw_haze(frame, center, 500 + 30 * slow, SUN_GOLD, alpha=0.030)
    draw_haze(frame, center, 610 + 48 * slow, PALE_BLUE, alpha=0.018)
    draw_circle(frame, center, 70 + 8 * slow, SUN_GOLD, alpha=0.72)
    draw_circle(frame, center, 44 + 5 * slow, IVORY, alpha=0.32)
    draw_ring(frame, center, 126 + 10 * slow, 5, IVORY, alpha=0.22)

    for idx, r in enumerate([170, 305, 485, 660]):
        wave = phase_wave(phase, idx * 0.13)
        draw_ring(frame, center, r + 22 * wave, 3 + idx % 2, PALE_BLUE, alpha=max(0.025, 0.14 - idx * 0.028))

    for idx, angle in enumerate(radial_angles(8, start=rotate)):
        local = phase_wave(phase, idx * 0.08)
        radial_phrase(
            frame,
            center,
            angle,
            distances=(215 + 18 * local, 360 + 34 * local, 530 + 58 * local),
            scale=breathe * (0.98 + 0.04 * math.sin(idx)),
            rgb=SOFT_IVORY,
            trigon_rgb=SUN_GOLD if idx % 2 == 0 else MIST,
            alpha=0.50 + 0.13 * local,
            thickness=(0.88, 1.08),
            sharpness=0.62,
            softness=0.42,
        )
    return frame


def render_snowflake(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    breathe = 0.94 + 0.075 * phase_wave(phase)
    rotate = math.radians(30) + math.radians(3.0) * math.sin(2.0 * math.pi * phase)
    draw_haze(frame, center, 420 + 24 * phase_wave(phase), ICE_BLUE, alpha=0.026)
    draw_ring(frame, center, 78 * breathe, 12, ICE_BLUE, alpha=0.68)
    draw_ring(frame, center, 185 + 10 * phase_wave(phase, 0.2), 4, SOFT_IVORY, alpha=0.18)

    for idx, angle in enumerate(radial_angles(6, start=rotate)):
        local = phase_wave(phase, idx / 12.0)
        radial_phrase(
            frame,
            center,
            angle,
            distances=(162 + 8 * local, 292 + 17 * local, 455 + 30 * local),
            scale=breathe * (0.84 + 0.05 * local),
            rgb=ICE_BLUE,
            trigon_rgb=SOFT_IVORY,
            alpha=0.55 + 0.10 * local,
            thickness=(0.46, 0.58),
            sharpness=0.82,
            softness=0.22,
        )
        for sign in (-1, 1):
            branch_angle = angle + sign * math.radians(34)
            branch_origin = (
                center[0] + math.cos(angle) * (260 + 10 * local),
                center[1] + math.sin(angle) * (260 + 10 * local),
            )
            branch_tip = (
                branch_origin[0] + math.cos(branch_angle) * (135 + 12 * local),
                branch_origin[1] + math.sin(branch_angle) * (135 + 12 * local),
            )
            draw_trigon_release(frame, branch_tip, branch_origin, 42, 50, ICE_BLUE, alpha=0.25 + 0.06 * local, sharpness=0.82, softness=0.26)

    # Negative-space pulse from source still 11, restrained and centered.
    for angle in radial_angles(6, start=math.radians(0) + rotate * 0.25):
        cut = (center[0] + math.cos(angle) * 116, center[1] + math.sin(angle) * 116)
        draw_crescent_cupping(frame, cut, center, 78, 47, BLACK, alpha=0.58)
    return frame


def render_abstract_orbital(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    rotate = phase * math.radians(14)
    breathe = 0.96 + 0.075 * phase_wave(phase, 0.2)
    draw_haze(frame, center, 520 + 28 * phase_wave(phase), PALE_BLUE, alpha=0.020)
    draw_ring(frame, center, 106 * breathe, 17, IVORY, alpha=0.52)
    draw_oval(frame, center, (42 * breathe, 30 * breathe), math.radians(-12 + 8 * math.sin(2 * math.pi * phase)), BLACK, alpha=1.0)

    for idx, axes in enumerate([(190, 122), (330, 210), (500, 310), (675, 420)]):
        phase_offset = phase_wave(phase, idx * 0.11)
        draw_arc(
            frame,
            center,
            (axes[0] + 18 * phase_offset, axes[1] + 10 * phase_offset),
            math.radians(-14) + rotate * 0.45,
            math.radians(205),
            math.radians(335),
            PALE_BLUE,
            alpha=max(0.025, 0.12 - idx * 0.018),
            thickness=4,
        )

    for idx, angle in enumerate(radial_angles(8, start=math.radians(10) + rotate)):
        local = phase_wave(phase, idx * 0.07)
        warm = idx in (0, 1)
        radial_phrase(
            frame,
            center,
            angle + 0.035 * math.sin(2.0 * math.pi * (phase + idx * 0.05)),
            distances=(175 + 12 * local, 300 + (idx % 2) * 34 + 22 * local, 465 + (idx % 3) * 20 + 36 * local),
            scale=(0.82 if idx % 2 == 0 else 0.70) * breathe,
            rgb=SOFT_IVORY if idx < 4 else MIST,
            trigon_rgb=SUN_GOLD if warm else PALE_BLUE,
            alpha=(0.48 + 0.10 * local) if idx < 4 else (0.32 + 0.08 * local),
            thickness=(0.70 + 0.10 * (idx % 3), 1.0),
            sharpness=0.48 + 0.07 * (idx % 4),
            softness=0.58,
        )
    return frame


def render_clip(name: str, render_frame) -> np.ndarray:
    out = OUT_DIR / name
    writer = H264Writer(out)
    midpoint: np.ndarray | None = None
    for fi in range(N_FRAMES):
        phase = fi / N_FRAMES
        frame = render_frame(phase)
        if fi == N_FRAMES // 2:
            midpoint = frame.copy()
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  {name} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    if midpoint is None:
        raise RuntimeError(f"No midpoint captured for {name}")
    return midpoint


def save_contact_sheet(midpoints: list[tuple[str, np.ndarray]]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for name, frame in midpoints:
        still_name = name.replace(".mp4", "_midpoint.png")
        cv2.imwrite(str(MIDPOINT_DIR / still_name), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(name).stem[:48], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 232), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    cv2.imwrite(str(OUT_DIR / "contact_sheet_radial_animation_v001_midpoints.png"), cv2.hconcat(thumbs), [cv2.IMWRITE_PNG_COMPRESSION, 3])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    clips = [
        ("01_sun_ripple_shared_expansion_v001_black_screen.mp4", render_sun_ripple),
        ("02_snowflake_frozen_water_radial_breathing_v001_black_screen.mp4", render_snowflake),
        ("03_abstract_orbital_radial_field_v001_black_screen.mp4", render_abstract_orbital),
    ]
    midpoints = [(name, render_clip(name, fn)) for name, fn in clips]
    save_contact_sheet(midpoints)
    print(f"Wrote {len(clips)} MP4 clips, midpoint stills, and contact sheet to {OUT_DIR}")


if __name__ == "__main__":
    main()
