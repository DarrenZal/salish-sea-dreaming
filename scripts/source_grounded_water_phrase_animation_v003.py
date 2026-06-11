#!/usr/bin/env python3.11
"""
Source-grounded water phrase animation studies v003.

Animated studies only, built from the accepted internal v002 grammar baseline:
circle/origin -> crescent -> crescent -> trigon. No fish, birds, figures,
heightfield/SDF field, or new visible grammar system.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

from source_grounded_water_phrase_layouts_v002 import (
    BLACK,
    GUIDE,
    H,
    PALE_WATER,
    ROCK,
    ROOT,
    SOFT_WHITE,
    W,
    WHITE,
    canvas,
    curve_points,
    draw_circle,
    draw_circle_ring,
    draw_crescent_cupping,
    draw_rock,
    draw_trigon_v2,
    path_point,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/source_grounded_water_phrase_animation_v003_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
FPS = 24
DURATION_SECONDS = 6.0
N_FRAMES = int(FPS * DURATION_SECONDS)

IVORY = WHITE
PALE_BLUE = (186, 226, 241)
DIM_BLUE = (72, 137, 171)
DIM_WHITE = (158, 171, 170)


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


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def fade_in_out(age: float, duration: float, edge: float = 0.12) -> float:
    return min(smoothstep(age / edge), smoothstep((duration - age) / edge))


def circular_age(phase: float, start: float) -> float:
    return (phase - start) % 1.0


def circular_window(phase: float, center: float, width: float) -> float:
    d = abs((phase - center + 0.5) % 1.0 - 0.5)
    return math.exp(-0.5 * (d / width) ** 2)


def alpha_line(frame: np.ndarray, pts: list[tuple[float, float]], rgb: tuple[int, int, int], alpha: float, thickness: int) -> None:
    overlay = frame.copy()
    cv2.polylines(overlay, [np.round(np.array(pts)).astype(np.int32)], False, (rgb[2], rgb[1], rgb[0]), thickness, cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def alpha_poly(frame: np.ndarray, pts: list[tuple[int, int]], rgb: tuple[int, int, int], alpha: float) -> None:
    overlay = frame.copy()
    cv2.fillPoly(overlay, [np.array(pts, dtype=np.int32)], (rgb[2], rgb[1], rgb[0]), lineType=cv2.LINE_AA)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def alpha_mask(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float) -> None:
    color = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    a = (mask.astype(np.float32) / 255.0) * alpha
    crop = frame.astype(np.float32)
    crop[:] = crop * (1.0 - a[..., None]) + color * a[..., None]
    frame[:] = np.clip(crop, 0, 255).astype(np.uint8)


def alpha_rock(frame: np.ndarray, pts: list[tuple[int, int]], alpha: float = 0.34) -> None:
    overlay = frame.copy()
    draw_rock(overlay, pts)
    frame[:] = cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0)


def make_path_mask(path: list[tuple[float, float]], thickness: int) -> np.ndarray:
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.polylines(mask, [np.round(np.array(path)).astype(np.int32)], False, 255, thickness, cv2.LINE_AA)
    return mask


def draw_phrase_on_path_v003(
    frame: np.ndarray,
    path: list[tuple[float, float]],
    s0: float,
    scale: float,
    *,
    alpha: float,
    rgb: tuple[int, int, int] = SOFT_WHITE,
    clip_mask: np.ndarray | None = None,
    offsets: tuple[float, float, float, float] = (0.0, 0.055, 0.112, 0.168),
) -> None:
    origin, _ = path_point(path, s0 + offsets[0])
    c1, _ = path_point(path, s0 + offsets[1])
    c2, _ = path_point(path, s0 + offsets[2])
    tri, tri_angle = path_point(path, s0 + offsets[3])

    draw_circle(frame, (int(origin[0]), int(origin[1])), max(5, int(scale * 0.18)), rgb, alpha=alpha, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c1, origin, scale * 0.60, scale * 0.43, rgb=rgb, alpha=alpha * 0.93, clip_mask=clip_mask)
    draw_crescent_cupping(frame, c2, origin, scale * 0.70, scale * 0.48, rgb=rgb, alpha=alpha * 0.86, clip_mask=clip_mask)
    draw_trigon_v2(frame, tri, scale * 0.50, scale * 0.50, tri_angle, rgb=rgb, alpha=alpha * 0.82, clip_mask=clip_mask)


def render_vancity_frame(phase: float) -> np.ndarray:
    frame = canvas(BLACK)
    center_y = H // 2 + 20
    circle = (1390, center_y)

    circle_p = circular_window(phase, 0.04, 0.07)
    crescent_1_p = circular_window(phase, 0.23, 0.075)
    crescent_2_p = circular_window(phase, 0.41, 0.075)
    trigon_p = circular_window(phase, 0.60, 0.085)
    field_p = circular_window(phase, 0.76, 0.09)

    draw_circle_ring(frame, circle, 118, 36, IVORY, alpha=0.46 + 0.52 * circle_p)
    draw_crescent_cupping(frame, (1190, center_y), circle, 170, 220, rgb=IVORY, alpha=0.40 + 0.54 * crescent_1_p)
    draw_crescent_cupping(frame, (990, center_y), circle, 175, 230, rgb=IVORY, alpha=0.36 + 0.53 * crescent_2_p)
    draw_trigon_v2(frame, (785, center_y), 350, 96, math.pi, rgb=IVORY, alpha=0.36 + 0.52 * trigon_p)
    draw_crescent_cupping(frame, (560, center_y), circle, 255, 340, rgb=IVORY, alpha=0.30 + 0.40 * field_p)

    # Subtle non-diagnostic eye-path pulse, replacing v002 red arrows while
    # keeping the source-grounded direction legible in motion.
    head_x = 1390 - 870 * ((phase + 0.04) % 1.0)
    trace = [(1390, center_y), (1190, center_y), (990, center_y), (785, center_y), (560, center_y)]
    alpha_line(frame, trace, PALE_BLUE, 0.08, 5)
    for i in range(7):
        x = int(head_x + i * 24)
        if 520 <= x <= 1390:
            a = 0.20 * (1.0 - i / 7.0)
            draw_circle(frame, (x, center_y), 5, PALE_BLUE, alpha=a)
    return frame


def render_river_frame(phase: float) -> np.ndarray:
    frame = canvas(BLACK)
    center = curve_points([(70, -20), (310, 270), (710, 415), (1260, 440), (1480, 610), (980, 790), (630, 1115)], samples=260)
    river_mask = make_path_mask(center, 260)
    alpha_mask(frame, river_mask, PALE_WATER, 0.16)
    alpha_line(frame, center, PALE_BLUE, 0.18, 6)

    rocks = [
        [(1110, 430), (1230, 430), (1270, 590), (1080, 610), (1035, 510)],
        [(1370, 270), (1505, 260), (1555, 405), (1340, 420)],
        [(1530, 780), (1660, 675), (1770, 830), (1620, 960)],
    ]
    effective_mask = river_mask.copy()
    for rock in rocks:
        cv2.fillPoly(effective_mask, [np.array(rock, dtype=np.int32)], 0, lineType=cv2.LINE_AA)
    for rock in rocks:
        alpha_rock(frame, rock, alpha=0.28)

    event_specs = [
        (curve_points([(990, 555), (1135, 560), (1285, 520), (1415, 505)], samples=90), 0.15, 0.46, 74, 0.03, 0.55),
        (curve_points([(1300, 395), (1435, 415), (1565, 455), (1680, 500)], samples=90), 0.48, 0.42, 62, 0.08, 0.52),
        (curve_points([(900, 812), (765, 872), (620, 890), (500, 860)], samples=90), 0.84, 0.36, 62, 0.10, 0.48),
    ]

    for path, start, duration, scale, s_start, s_span in event_specs:
        age = circular_age(phase, start)
        if age > duration:
            continue
        progress = age / duration
        alpha = 0.78 * fade_in_out(age, duration, edge=0.12)
        compression = 0.92 + 0.13 * math.sin(math.pi * progress)
        s = s_start + s_span * smoothstep(progress)
        alpha_line(frame, path, PALE_BLUE, 0.05 + 0.10 * alpha, 4)
        draw_phrase_on_path_v003(frame, path, s, scale * compression, alpha=alpha, rgb=SOFT_WHITE, clip_mask=effective_mask)

    # Three small bend-origin points remain embedded in the current as topology
    # anchors, not eye pairs or standalone icons.
    bend_pulse = 0.18 + 0.14 * math.sin(2.0 * math.pi * phase)
    for p in [(1010, 620), (965, 650), (920, 675)]:
        draw_circle(frame, p, 5, SOFT_WHITE, alpha=bend_pulse, clip_mask=effective_mask)
    return frame


def draw_falling_phrase(
    frame: np.ndarray,
    origin: tuple[float, float],
    progress: float,
    scale: float,
    alpha: float,
    *,
    clip_mask: np.ndarray,
    x_drift: float = 0.0,
) -> None:
    y_push = 94.0 * smoothstep(progress)
    origin_shift = (origin[0] + x_drift * 0.18, origin[1])
    draw_circle(frame, (int(origin_shift[0]), int(origin_shift[1])), int(scale * 0.24), SOFT_WHITE, alpha=alpha * (0.42 + 0.42 * (1.0 - progress)), clip_mask=clip_mask)

    c1 = (origin[0] + x_drift * 0.35, origin[1] + scale * 0.92 + y_push * 0.34)
    c2 = (origin[0] + x_drift * 0.64, origin[1] + scale * 1.88 + y_push * 0.72)
    tri = (origin[0] + x_drift, origin[1] + scale * 3.00 + y_push)
    draw_crescent_cupping(frame, c1, origin_shift, scale * 0.66, scale * 0.48, rgb=SOFT_WHITE, alpha=alpha * smoothstep(progress / 0.25), clip_mask=clip_mask)
    draw_crescent_cupping(frame, c2, origin_shift, scale * 0.78, scale * 0.54, rgb=SOFT_WHITE, alpha=alpha * smoothstep((progress - 0.12) / 0.30), clip_mask=clip_mask)
    draw_trigon_v2(frame, tri, scale * 0.62, scale * 0.78, math.pi / 2, rgb=SOFT_WHITE, alpha=alpha * smoothstep((progress - 0.26) / 0.34), clip_mask=clip_mask)


def render_waterfall_frame(phase: float) -> np.ndarray:
    frame = canvas(BLACK)
    fall = [(790, 150), (990, 150), (1065, 880), (670, 880)]
    mask = np.zeros((H, W), dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(fall, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    alpha_poly(frame, [(0, 0), (760, 0), (610, 175), (360, 305), (160, 475), (0, 610)], DIM_BLUE, 0.16)
    alpha_mask(frame, mask, PALE_WATER, 0.17)
    alpha_line(frame, [(890, 150), (875, 350), (875, 560), (910, 850)], PALE_BLUE, 0.18, 5)

    rock = [(620, 790), (790, 705), (950, 830), (890, 940), (620, 930)]
    cv2.fillPoly(mask, [np.array(rock, dtype=np.int32)], 0, lineType=cv2.LINE_AA)
    alpha_rock(frame, rock, alpha=0.34)

    events = [
        ((890.0, 260.0), 0.88, 0.42, 128.0, 18.0),
        ((826.0, 368.0), 0.36, 0.38, 78.0, -26.0),
    ]
    for origin, start, duration, scale, x_drift in events:
        age = circular_age(phase, start)
        if age > duration:
            continue
        progress = age / duration
        alpha = 0.86 * fade_in_out(age, duration, edge=0.10)
        draw_falling_phrase(frame, origin, progress, scale, alpha, clip_mask=mask, x_drift=x_drift)
    return frame


def render_clip(name: str, render_frame) -> np.ndarray:
    out = OUT_DIR / name
    writer = H264Writer(out)
    midpoint = None
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
        cv2.putText(thumb, Path(name).stem[:48], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    sheet = cv2.hconcat(thumbs)
    cv2.imwrite(str(OUT_DIR / "contact_sheet_v003_midpoints.png"), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    clips = [
        ("01_vancity_grammar_phrase_v003_black_screen.mp4", render_vancity_frame),
        ("02_river_s_curve_topology_v003_black_screen.mp4", render_river_frame),
        ("03_waterfall_vertical_descent_v003_black_screen.mp4", render_waterfall_frame),
    ]
    midpoints = [(name, render_clip(name, fn)) for name, fn in clips]
    save_contact_sheet(midpoints)
    print(f"Wrote {len(clips)} MP4 clips, midpoint stills, and contact sheet to {OUT_DIR}")


if __name__ == "__main__":
    main()
