#!/usr/bin/env python3.11
"""
Primitive Water Grammar v001.

Internal deterministic prototype lane for 2026-05-19:
circle / crescent / trigon as a transparent compositional layer over
real water footage. No SD, LoRA, prompt generation, or named/specific
people/being transformations.

Outputs:
  track2-deterministic/morph_outputs_INTERNAL/
    primitive_water_grammar_2026-05-19/
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


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_2026-05-19"

H1_SALMON = ROOT / "media/hero-subclips/H1_salmon_school.mp4"
H6_KELP = ROOT / "media/hero-subclips/H6_kelp_forest_floor.mp4"
H8_WATER = ROOT / "media/hero-subclips/H8_milky_water.mp4"

W = 1920
H = 1080
FPS = 24
DURATION = 6.0
N_FRAMES = int(FPS * DURATION)

# Shape colors are deliberately restrained and semantic, not randomized:
# circle = impact/attention, crescent = ripple/current body, trigon = final
# attenuation. RGB order here; OpenCV frames are BGR but drawing helpers convert.
CIRCLE_RGB = (255, 199, 78)
CRESCENT_RGB = (238, 233, 208)
TRIGON_RGB = (215, 85, 55)
OUTLINE_RGB = (18, 29, 28)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    status: str
    method: str
    next_recommendation: str
    dynamic_note: str = ""


class SampledVideo:
    """Sequential frame sampler from source fps to deterministic output fps."""

    def __init__(self, path: Path, *, start_seconds: float, out_fps: int = FPS, size: tuple[int, int] = (W, H)):
        self.path = path
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video: {path}")
        src_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not src_fps or math.isnan(src_fps):
            src_fps = out_fps
        self.src_fps = float(src_fps)
        self.out_fps = out_fps
        self.size = size
        self.start_frame = int(round(start_seconds * self.src_fps))
        self.current_frame_idx = self.start_frame - 1
        self.last_frame: np.ndarray | None = None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

    def frame(self, out_idx: int) -> np.ndarray:
        target = self.start_frame + int(round(out_idx * self.src_fps / self.out_fps))
        while self.current_frame_idx < target:
            ok, frame = self.cap.read()
            self.current_frame_idx += 1
            if not ok:
                if self.last_frame is None:
                    raise RuntimeError(f"Could not read frame {target} from {self.path}")
                frame = self.last_frame.copy()
            self.last_frame = frame
        assert self.last_frame is not None
        frame = self.last_frame.copy()
        if (frame.shape[1], frame.shape[0]) != self.size:
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
        return frame

    def close(self) -> None:
        self.cap.release()


class H264Writer:
    """Raw BGR frames into ffmpeg/libx264."""

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


def soften_background(frame: np.ndarray, *, mode: str) -> np.ndarray:
    """Light grade that keeps source footage legible while making overlays read."""

    if mode == "surface":
        graded = cv2.convertScaleAbs(frame, alpha=0.94, beta=-5)
        tint = np.full_like(graded, (88, 128, 120))  # BGR teal/gray
        return cv2.addWeighted(graded, 0.90, tint, 0.10, 0)
    if mode == "underwater":
        graded = cv2.convertScaleAbs(frame, alpha=0.90, beta=-9)
        tint = np.full_like(graded, (74, 126, 108))
        return cv2.addWeighted(graded, 0.92, tint, 0.08, 0)
    return frame


def _blend_mask(frame: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int], rgb: tuple[int, int, int], alpha: float) -> None:
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return
    a = (mask.astype(np.float32) / 255.0) * float(max(0.0, min(1.0, alpha)))
    if not np.any(a > 0):
        return
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    color = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
    crop[:] = crop * (1.0 - a[..., None]) + color * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(crop, 0, 255).astype(np.uint8)


def draw_poly_alpha(
    frame: np.ndarray,
    pts: np.ndarray,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    outline_rgb: tuple[int, int, int] = OUTLINE_RGB,
    outline_alpha: float = 0.28,
    outline_thickness: int = 2,
) -> None:
    h, w = frame.shape[:2]
    pts_i = np.round(pts).astype(np.int32)
    x0 = max(0, int(pts_i[:, 0].min()) - outline_thickness - 3)
    y0 = max(0, int(pts_i[:, 1].min()) - outline_thickness - 3)
    x1 = min(w, int(pts_i[:, 0].max()) + outline_thickness + 4)
    y1 = min(h, int(pts_i[:, 1].max()) + outline_thickness + 4)
    if x1 <= x0 or y1 <= y0:
        return
    local = pts_i.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    fill_mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(fill_mask, [local], 255, lineType=cv2.LINE_AA)
    _blend_mask(frame, fill_mask, (x0, y0, x1, y1), rgb, alpha)
    if outline_thickness > 0 and outline_alpha > 0:
        outline_mask = np.zeros_like(fill_mask)
        cv2.polylines(outline_mask, [local], True, 255, outline_thickness, lineType=cv2.LINE_AA)
        _blend_mask(frame, outline_mask, (x0, y0, x1, y1), outline_rgb, outline_alpha)


def draw_circle_alpha(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    outline_rgb: tuple[int, int, int] = OUTLINE_RGB,
    outline_alpha: float = 0.30,
) -> None:
    h, w = frame.shape[:2]
    cx, cy = center
    r = int(max(1, round(radius)))
    x0 = max(0, int(cx - r - 5))
    y0 = max(0, int(cy - r - 5))
    x1 = min(w, int(cx + r + 6))
    y1 = min(h, int(cy + r + 6))
    if x1 <= x0 or y1 <= y0:
        return
    local_c = (int(round(cx - x0)), int(round(cy - y0)))
    fill_mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.circle(fill_mask, local_c, r, 255, -1, lineType=cv2.LINE_AA)
    _blend_mask(frame, fill_mask, (x0, y0, x1, y1), rgb, alpha)
    outline_mask = np.zeros_like(fill_mask)
    cv2.circle(outline_mask, local_c, r, 255, 2, lineType=cv2.LINE_AA)
    _blend_mask(frame, outline_mask, (x0, y0, x1, y1), outline_rgb, outline_alpha)


def crescent_points(samples: int = 42) -> np.ndarray:
    """Crescent glyph with eye-flow direction along +x."""

    outer_sag = 0.58
    inner_sag = 0.21
    y_radius = 0.70
    pts: list[tuple[float, float]] = []
    for i in range(samples):
        a = -math.pi / 2 + math.pi * i / max(1, samples - 1)
        pts.append((outer_sag * math.cos(a), y_radius * math.sin(a)))
    for i in range(samples):
        a = math.pi / 2 - math.pi * i / max(1, samples - 1)
        pts.append((inner_sag * math.cos(a), y_radius * math.sin(a)))
    arr = np.array(pts, dtype=np.float32)
    arr[:, 0] -= (outer_sag + inner_sag) * 0.5
    return arr


def trigon_points(samples_per_side: int = 22) -> np.ndarray:
    """Concave trigon glyph with attenuated direction along +x."""

    verts = np.array(
        [
            [0.72, 0.0],
            [-0.55, 0.50],
            [-0.47, -0.50],
        ],
        dtype=np.float32,
    )
    center = np.array([-0.08, 0.0], dtype=np.float32)
    pts: list[np.ndarray] = []
    for i in range(3):
        p0 = verts[i]
        p1 = verts[(i + 1) % 3]
        ctrl = (p0 + p1) * 0.5 + (center - (p0 + p1) * 0.5) * 0.36
        for j in range(samples_per_side):
            t = j / max(1, samples_per_side)
            omt = 1.0 - t
            pts.append((omt * omt * p0) + (2.0 * omt * t * ctrl) + (t * t * p1))
    return np.array(pts, dtype=np.float32)


CRESCENT_BASE = crescent_points()
TRIGON_BASE = trigon_points()


def transform_points(base: np.ndarray, center: tuple[float, float], size: float, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    pts = (base * float(size)) @ rot.T
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]
    return pts


def draw_crescent(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(frame, transform_points(CRESCENT_BASE, center, size, angle), CRESCENT_RGB, alpha=alpha)


def draw_trigon(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(frame, transform_points(TRIGON_BASE, center, size, angle), TRIGON_RGB, alpha=alpha)


def fade01(x: float) -> float:
    return max(0.0, min(1.0, x))


def edge_fade(s: float) -> float:
    return fade01(min(s / 0.10, (1.0 - s) / 0.10))


def flowline_point(line_idx: int, s: float) -> tuple[tuple[float, float], float]:
    x = -130.0 + s * (W + 260.0)
    base_y = H * (0.25 + 0.115 * line_idx)
    y = base_y + 48.0 * math.sin(2.0 * math.pi * (1.18 * s + 0.17 * line_idx))
    y += 18.0 * math.sin(2.0 * math.pi * (2.3 * s + 0.11 * line_idx))

    dx = W + 260.0
    dy = 48.0 * 2.0 * math.pi * 1.18 * math.cos(2.0 * math.pi * (1.18 * s + 0.17 * line_idx))
    dy += 18.0 * 2.0 * math.pi * 2.3 * math.cos(2.0 * math.pi * (2.3 * s + 0.11 * line_idx))
    return (x, y), math.atan2(dy, dx)


def render_pond_ripple() -> ClipResult:
    out = OUT_DIR / "01_pond_ripple_circle_crescent_trigon_H8.mp4"
    reader = SampledVideo(H8_WATER, start_seconds=2.0)
    writer = H264Writer(out)
    events = [
        (0.35, (W * 0.33, H * 0.55), [0.05, 0.92, 1.82, 2.72, 3.67, 4.75]),
        (1.85, (W * 0.58, H * 0.43), [0.35, 1.23, 2.20, 3.10, 4.18, 5.18]),
        (3.20, (W * 0.73, H * 0.62), [-0.15, 0.75, 1.65, 2.55, 3.48, 4.38]),
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = soften_background(reader.frame(fi), mode="surface")
        for start, center, angles in events:
            age = t - start
            if age < 0.0 or age > 3.8:
                continue
            center_alpha = 0.58 * fade01(1.0 - age / 2.5)
            draw_circle_alpha(frame, center, 17.0 + 5.0 * math.sin(age * 4.0), CIRCLE_RGB, alpha=center_alpha)
            for ai, angle in enumerate(angles):
                local_age = age - ai * 0.035
                if local_age < 0.0:
                    continue
                base_r = 38.0 + local_age * 74.0
                phrase_alpha = 0.48 * fade01(1.0 - local_age / 3.4)
                for kind, extra_r, size_mul in [
                    ("crescent", 0.0, 1.00),
                    ("crescent", 58.0, 0.88),
                    ("trigon", 116.0, 0.80),
                ]:
                    r = base_r + extra_r
                    if r > 345.0:
                        continue
                    px = center[0] + math.cos(angle) * r
                    py = center[1] + math.sin(angle) * r
                    if kind == "crescent":
                        draw_crescent(frame, (px, py), 50.0 * size_mul, angle, alpha=phrase_alpha * (1.0 - r / 410.0))
                    else:
                        draw_trigon(frame, (px, py), 46.0 * size_mul, angle, alpha=phrase_alpha * (1.0 - r / 430.0))
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  pond ripple {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    reader.close()
    return ClipResult(
        filename=out.name,
        source=str(H8_WATER.relative_to(ROOT)),
        test="Pond/still-water ripple grammar: circle impact points, crescents moving outward, trigons as final attenuated ripple forms.",
        status="Abstract-only primitive grammar, internal. Austin review required before public use because it applies Coast Salish vocabulary.",
        method="Deterministic radial event schedule over H8 water footage; no detection, no generative model.",
        next_recommendation="Ask Austin whether crescent cup/trigon orientation should face inward to the impact or outward along the ripple front.",
    )


def render_river_current() -> ClipResult:
    out = OUT_DIR / "02_river_current_ordered_strings_H8.mp4"
    reader = SampledVideo(H8_WATER, start_seconds=9.0)
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = soften_background(reader.frame(fi), mode="surface")
        for line_idx in range(5):
            for phrase_idx in range(3):
                base_s = (0.10 * line_idx + 0.31 * phrase_idx + t * 0.075) % 1.18 - 0.09
                offsets = [0.000, 0.034, 0.070, 0.112]
                for shape_idx, ds in enumerate(offsets):
                    s = base_s + ds
                    if s < 0.0 or s > 1.0:
                        continue
                    pos, angle = flowline_point(line_idx, s)
                    alpha = 0.42 * edge_fade(s)
                    size = 24.0 if shape_idx == 0 else 42.0 - 2.5 * shape_idx
                    if shape_idx == 0:
                        draw_circle_alpha(frame, pos, size * 0.50, CIRCLE_RGB, alpha=alpha * 0.95)
                    elif shape_idx in (1, 2):
                        draw_crescent(frame, pos, size, angle, alpha=alpha)
                    else:
                        draw_trigon(frame, pos, size, angle, alpha=alpha * 0.95)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  river current {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    reader.close()
    return ClipResult(
        filename=out.name,
        source=str(H8_WATER.relative_to(ROOT)),
        test="River/current grammar: ordered circle/crescent/crescent/trigon strings following repeatable procedural flow lines.",
        status="Abstract-only primitive grammar, internal. Austin review required before public use because it applies Coast Salish vocabulary.",
        method="Five deterministic sinusoidal current paths; each phrase preserves fixed C-Cr-Cr-T order and tangent orientation.",
        next_recommendation="Tune line count and spacing with Austin; this is the clearest candidate for a reusable Resolume/current layer.",
    )


def calc_flow(prev_bgr: np.ndarray, curr_bgr: np.ndarray, *, flow_size: tuple[int, int] = (480, 270)) -> np.ndarray:
    prev = cv2.resize(cv2.cvtColor(prev_bgr, cv2.COLOR_BGR2GRAY), flow_size, interpolation=cv2.INTER_AREA)
    curr = cv2.resize(cv2.cvtColor(curr_bgr, cv2.COLOR_BGR2GRAY), flow_size, interpolation=cv2.INTER_AREA)
    return cv2.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 21, 3, 5, 1.15, 0)


def sample_flow(flow: np.ndarray, x: float, y: float) -> tuple[float, float]:
    fh, fw = flow.shape[:2]
    sx = int(max(0, min(fw - 1, round(x / W * fw))))
    sy = int(max(0, min(fh - 1, round(y / H * fh))))
    dx = float(flow[sy, sx, 0]) * (W / fw)
    dy = float(flow[sy, sx, 1]) * (H / fh)
    return dx, dy


def smooth_angle(old: float, new: float, amount: float = 0.20) -> float:
    ox, oy = math.cos(old), math.sin(old)
    nx, ny = math.cos(new), math.sin(new)
    vx = ox * (1.0 - amount) + nx * amount
    vy = oy * (1.0 - amount) + ny * amount
    return math.atan2(vy, vx)


def phrase_positions(anchor: tuple[float, float], angle: float, spacing: float) -> list[tuple[tuple[float, float], str, float]]:
    dx = math.cos(angle)
    dy = math.sin(angle)
    offsets = [-spacing * 1.10, -spacing * 0.22, spacing * 0.62, spacing * 1.35]
    kinds = ["circle", "crescent", "crescent", "trigon"]
    sizes = [22.0, 43.0, 39.0, 36.0]
    out: list[tuple[tuple[float, float], str, float]] = []
    for off, kind, size in zip(offsets, kinds, sizes):
        out.append(((anchor[0] + dx * off, anchor[1] + dy * off), kind, size))
    return out


def render_phrase(frame: np.ndarray, anchor: tuple[float, float], angle: float, *, alpha: float, spacing: float = 50.0) -> None:
    for pos, kind, size in phrase_positions(anchor, angle, spacing):
        if kind == "circle":
            draw_circle_alpha(frame, pos, size * 0.55, CIRCLE_RGB, alpha=alpha * 1.05)
        elif kind == "crescent":
            draw_crescent(frame, pos, size, angle, alpha=alpha)
        else:
            draw_trigon(frame, pos, size, angle, alpha=alpha * 0.95)


def render_ocean_kelp_flow() -> ClipResult:
    out = OUT_DIR / "03_ocean_kelp_optical_flow_H6.mp4"
    reader = SampledVideo(H6_KELP, start_seconds=8.0)
    writer = H264Writer(out)
    anchors = []
    for idx, (x, y, a) in enumerate(
        [
            (0.18, 0.30, -0.15),
            (0.34, 0.38, 0.10),
            (0.52, 0.32, 0.18),
            (0.70, 0.40, 0.05),
            (0.83, 0.52, -0.10),
            (0.23, 0.57, 0.22),
            (0.43, 0.62, 0.16),
            (0.61, 0.58, 0.12),
            (0.77, 0.69, 0.04),
            (0.30, 0.76, 0.20),
            (0.50, 0.80, 0.08),
            (0.68, 0.78, -0.04),
        ]
    ):
        anchors.append({"x": W * x, "y": H * y, "angle": a, "phase": idx * 0.37})
    prev_raw = reader.frame(0)
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        frame = soften_background(raw, mode="underwater")
        flow = calc_flow(prev_raw, raw) if fi > 0 else np.zeros((270, 480, 2), dtype=np.float32)
        t = fi / FPS
        for anchor in anchors:
            dx, dy = sample_flow(flow, anchor["x"], anchor["y"])
            mag = math.hypot(dx, dy)
            if mag > 0.20:
                observed = math.atan2(dy, dx)
                anchor["angle"] = smooth_angle(anchor["angle"], observed, amount=0.22)
            else:
                anchor["angle"] = smooth_angle(anchor["angle"], 0.05 + 0.12 * math.sin(t + anchor["phase"]), amount=0.06)
            drift_x = math.cos(anchor["angle"]) * 0.32 + dx * 0.55
            drift_y = math.sin(anchor["angle"]) * 0.32 + dy * 0.55
            anchor["x"] += drift_x
            anchor["y"] += drift_y
            if anchor["x"] < -100:
                anchor["x"] = W + 60
            elif anchor["x"] > W + 100:
                anchor["x"] = -60
            if anchor["y"] < 80:
                anchor["y"] = H * 0.80
            elif anchor["y"] > H * 0.90:
                anchor["y"] = H * 0.24
            pulse = 0.86 + 0.14 * math.sin(t * 1.6 + anchor["phase"])
            render_phrase(frame, (anchor["x"], anchor["y"]), anchor["angle"], alpha=0.32 * pulse, spacing=45.0)
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            print(f"  ocean kelp flow {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    reader.close()
    return ClipResult(
        filename=out.name,
        source=str(H6_KELP.relative_to(ROOT)),
        test="Ocean/kelp-current grammar: sparse primitive phrases advected and oriented by dense optical flow.",
        status="Austin-review-required internal test. Abstract primitives only, but placed over real Salish Sea footage.",
        method="Farneback optical flow sampled at phrase anchors; smoothed tangent orientation; no prompt/generative model.",
        next_recommendation="Use this as the technical base for kelp/current overlays, then tune opacity lower for show integration.",
    )


def detect_salmon_proxy(frame: np.ndarray, flow: np.ndarray | None) -> list[dict[str, float]]:
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    work = cv2.GaussianBlur(gray, (9, 9), 0)
    burn_h = int(h * 0.085)
    work[h - burn_h :, :] = 180
    bg = cv2.GaussianBlur(work, (0, 0), 31)
    score = cv2.subtract(bg, work)
    mask = ((score > 10) & (work < 150)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8), iterations=1)
    num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    detections: list[dict[str, float]] = []
    for comp_idx in range(1, num):
        x, y, cw, ch, area = stats[comp_idx]
        touches_edge = x <= 2 or y <= 2 or x + cw >= w - 2 or y + ch >= h - burn_h - 2
        if touches_edge:
            continue
        aspect = cw / max(1, ch)
        extent = area / max(1, cw * ch)
        if not (800 <= area <= 52000 and 0.70 <= aspect <= 8.50 and 20 <= cw <= 520 and 12 <= ch <= 230 and extent > 0.10):
            continue
        cx, cy = float(cents[comp_idx][0]), float(cents[comp_idx][1])
        ys, xs = np.where(labels[y : y + ch, x : x + cw] == comp_idx)
        angle = 0.0
        if len(xs) >= 8:
            pts = np.column_stack([xs.astype(np.float32), ys.astype(np.float32)])
            pts -= pts.mean(axis=0, keepdims=True)
            cov = pts.T @ pts / max(1, len(pts) - 1)
            vals, vecs = np.linalg.eigh(cov)
            major = vecs[:, int(np.argmax(vals))]
            angle = math.atan2(float(major[1]), float(major[0]))
            if math.cos(angle) < 0:
                angle += math.pi
        if flow is not None:
            dx, dy = sample_flow(flow, cx, cy)
            if math.hypot(dx, dy) > 0.18:
                f_angle = math.atan2(dy, dx)
                angle = smooth_angle(angle, f_angle, amount=0.45)
        detections.append({"cx": cx, "cy": cy, "w": float(cw), "h": float(ch), "area": float(area), "angle": angle})
    detections.sort(key=lambda d: d["area"], reverse=True)
    # Keep a sparse non-overlapping set so the layer reads as guidance, not labels.
    kept: list[dict[str, float]] = []
    for det in detections:
        if len(kept) >= 12:
            break
        if all(math.hypot(det["cx"] - prev["cx"], det["cy"] - prev["cy"]) > 120 for prev in kept):
            kept.append(det)
    return kept


def render_flow_fallback(frame: np.ndarray, flow: np.ndarray, t: float) -> None:
    for yi, y in enumerate(np.linspace(H * 0.25, H * 0.78, 5)):
        for xi, x in enumerate(np.linspace(W * 0.16, W * 0.84, 5)):
            dx, dy = sample_flow(flow, float(x), float(y))
            mag = math.hypot(dx, dy)
            if mag < 0.15:
                angle = 0.12 * math.sin(t + xi * 0.7 + yi)
            else:
                angle = math.atan2(dy, dx)
            if (xi + yi) % 2 == 0:
                render_phrase(frame, (float(x), float(y)), angle, alpha=0.22, spacing=38.0)


def render_salmon_school_proxy() -> ClipResult:
    out = OUT_DIR / "04_salmon_school_proxy_H1.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    writer = H264Writer(out)
    prev_raw = reader.frame(0)
    detection_counts: list[int] = []
    fallback_frames = 0
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        frame = soften_background(raw, mode="underwater")
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        detections = detect_salmon_proxy(raw, flow)
        detection_counts.append(len(detections))
        if len(detections) >= 4:
            for det in detections:
                cx, cy = det["cx"], det["cy"]
                angle = det["angle"]
                scale = max(0.70, min(1.55, math.sqrt(det["area"]) / 105.0))
                draw_circle_alpha(frame, (cx, cy), 13.0 * scale, CIRCLE_RGB, alpha=0.50)
                lead1 = (cx + math.cos(angle) * 38.0 * scale, cy + math.sin(angle) * 38.0 * scale)
                lead2 = (cx + math.cos(angle) * 78.0 * scale, cy + math.sin(angle) * 78.0 * scale)
                lead3 = (cx + math.cos(angle) * 118.0 * scale, cy + math.sin(angle) * 118.0 * scale)
                draw_crescent(frame, lead1, 34.0 * scale, angle, alpha=0.38)
                draw_crescent(frame, lead2, 30.0 * scale, angle, alpha=0.31)
                draw_trigon(frame, lead3, 28.0 * scale, angle, alpha=0.28)
        else:
            fallback_frames += 1
            if flow is not None:
                render_flow_fallback(frame, flow, fi / FPS)
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            avg = sum(detection_counts[-48:]) / max(1, len(detection_counts[-48:]))
            print(f"  salmon proxy {fi + 1}/{N_FRAMES} avg detections last block={avg:.1f}", flush=True)
    writer.close()
    reader.close()
    avg_det = sum(detection_counts) / max(1, len(detection_counts))
    note = f"Average detected salmon-proxy components per frame: {avg_det:.1f}; fallback optical-flow frames: {fallback_frames}/{N_FRAMES}."
    return ClipResult(
        filename=out.name,
        source=str(H1_SALMON.relative_to(ROOT)),
        test="Salmon-school proxy: circles near detected dark salmon centers, crescents/trigons leading along estimated swim direction.",
        status="Austin-review-required internal test. It does not transform a named/specific being, but it uses live salmon footage and Coast Salish primitive language.",
        method="Local-darkness segmentation, connected components, PCA plus local optical-flow direction; fallback to dense optical-flow primitive phrases if detection drops.",
        next_recommendation="Improve detection with a fish-specific tracker only if Austin likes this grammar; current prototype is intentionally light and non-identifying.",
        dynamic_note=note,
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


def write_readme(results: Iterable[ClipResult]) -> None:
    rows = []
    for result in results:
        probe = ffprobe(OUT_DIR / result.filename)
        rows.append((result, probe))
    lines = [
        "# Primitive Water Grammar Prototypes - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. These clips intentionally use only the abstract primitive grammar lane: circle, crescent, trigon. They do not use SD, LoRA, prompt generation, named chiefs, specific people, or Austin-specific beings.",
        "",
        "## Clips",
        "",
    ]
    for result, probe in rows:
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}",
                f"- Source footage: `{result.source}`",
                f"- Review status: {result.status}",
                f"- Technical method: {result.method}",
                f"- Next recommendation: {result.next_recommendation}",
            ]
        )
        if result.dynamic_note:
            lines.append(f"- Runtime note: {result.dynamic_note}")
        lines.extend(
            [
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Design Notes",
            "",
            "- The layer is sparse and directional by construction: fixed phrase order, no randomized confetti field.",
            "- Circle is treated as the impact or attention point. Crescents carry ripple/current motion. Trigons mark the final attenuated form.",
            "- Colors are temporary debug semantics for review; final integration can reduce opacity, remove outlines, or move to a single ink/paper palette after Austin feedback.",
            "- All outputs are technical prototypes for internal review, not show-ready cultural approval.",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Water Grammar prototypes to {OUT_DIR}", flush=True)
    results = [
        render_pond_ripple(),
        render_river_current(),
        render_ocean_kelp_flow(),
        render_salmon_school_proxy(),
    ]
    write_readme(results)
    print("Done. README includes ffprobe verification.", flush=True)


if __name__ == "__main__":
    main()
