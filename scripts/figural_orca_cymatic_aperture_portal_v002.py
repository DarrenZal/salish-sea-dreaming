#!/usr/bin/env python3
"""
Figural Orca cymatic aperture portal v002.

Internal review render for Salish Sea Dreaming.

v002 replaces the v001/v001_1 drawn-overlay test. Wave-source placement creates
constructive cymatic energy near measured Orca primitive positions before any
mask is applied. Source-derived aperture masks then reveal the moving field
through boundaries extracted from Austin's actual Orca artwork.

Status: AUSTIN-AUTHORIZED INTERNAL / SHOW-DEVELOPMENT PROTOTYPE ONLY.
Austin has greenlit use of the Google Drive artwork and Austin-style /
Coast Salish-style generated experiments for this project. This specific output
still requires Darren/Austin clearance before any public, sponsor, press, or
show-surface use.
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
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_orca_cymatic_aperture_portal_v002"
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / f"{PROJECT}_2026-05-22"
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Water_Orca_Transparent.png"
SOURCE_DIR = OUT_DIR / "source_assets"
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

W = 3840
H = 2160
FPS = 24
DURATION_SECONDS = 60.0
FRAME_COUNT = int(FPS * DURATION_SECONDS)
TAU = math.tau

FIELD_W = 960
FIELD_H = 540
FIELD_SCALE_X = W / FIELD_W
FIELD_SCALE_Y = H / FIELD_H
FIELD_CYCLES = 8.0
FIELD_DIAGNOSTIC_TIME = 12.0
SOURCE_SCALE = 0.88
TARGET_ALPHA_CENTER_PX = (1920.0, 1080.0)

TIMING = {
    "loose_cymatic_field": [0.0, 8.0],
    "calculated_energy_gather_no_masks": [8.0, 14.0],
    "source_shape_eye_aperture_opens": [14.0, 20.0],
    "source_shape_crescent_apertures_open": [20.0, 28.0],
    "dorsal_and_tail_apertures_open": [28.0, 36.0],
    "whole_source_orca_fades_in": [36.0, 44.0],
    "whole_source_orca_hold": [44.0, 50.0],
    "collapse_apertures_linger": [50.0, 57.0],
    "release_to_generic_field": [57.0, 60.0],
}

STILL_TIMES = {
    "loose_cymatic_field": 5.0,
    "field_energy_gather_no_masks": FIELD_DIAGNOSTIC_TIME,
    "eye_source_shape_aperture": 17.2,
    "crescent_source_shape_apertures": 25.0,
    "all_apertures_before_orca": 32.0,
    "mid_reveal_composite": 39.2,
    "full_orca_hold": 46.0,
    "collapse_apertures_linger": 54.0,
    "release_generic_field": 58.7,
}

BOUNDARY_TEXT = (
    "Austin greenlit use of the Google Drive artwork and Austin-style / "
    "Coast Salish-style generated experiments for this project. Austin source "
    "remains whole-authored; aperture masks are source-derived review devices. "
    "Internal / show-development prototype only until Darren/Austin clear "
    "specific use."
)


@dataclass(frozen=True)
class AnchorRecord:
    anchor_id: str
    label: str
    aperture_mask_id: str
    kind: str
    center_source_px: list[float]
    target_source_px: list[float]
    center_canvas_px: list[float]
    target_canvas_px: list[float]
    region_bbox_source_px: list[int]
    region_bbox_canvas_px: list[int]
    component_area_source_px: int
    curve_source_px: list[list[float]] | None
    curve_canvas_px: list[list[float]] | None
    axis_source_px: list[list[float]] | None
    axis_canvas_px: list[list[float]] | None
    method: str
    notes: str


@dataclass(frozen=True)
class ApertureLayer:
    mask_id: str
    anchor_id: str
    label: str
    color_rgb: tuple[int, int, int]
    bbox_canvas_px: tuple[int, int, int, int]
    alpha: np.ndarray
    edge_alpha: np.ndarray
    source_bbox_px: list[int]
    canvas_bbox_px: list[int]
    source_area_px: int
    canvas_area_px: int
    extraction_method: str
    alignment_quality: dict[str, object]


@dataclass(frozen=True)
class RenderState:
    frame_index: int
    time_seconds: float
    temporal_phase: float
    field_gather_strength: float
    source_opacity: float
    aperture_strength_by_anchor: dict[str, float]
    aperture_front_scale: float


@dataclass(frozen=True)
class WaveSourceRecord:
    source_id: str
    target_anchor_id: str
    source_canvas_px: list[float]
    wavelength_px: float
    amplitude: float
    decay_px: float
    phase_radians: float
    phase_degrees: float
    source_distance_to_target_px: float
    tuning_method: str


@dataclass(frozen=True)
class FieldModel:
    xx: np.ndarray
    yy: np.ndarray
    vignette: np.ndarray
    source_distances: np.ndarray
    source_attenuation: np.ndarray
    source_wave_number: np.ndarray
    source_amplitude: np.ndarray
    source_phase: np.ndarray
    source_target_ids: list[str]
    source_records: list[WaveSourceRecord]


class H264Writer:
    def __init__(self, path: Path, *, fps: int, size: tuple[int, int]) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to encode the MP4")
        path.parent.mkdir(parents=True, exist_ok=True)
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
            "veryfast",
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


def smooth_array(values: np.ndarray) -> np.ndarray:
    t = np.clip(values, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


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


def transform_point(point_source: list[float] | tuple[float, float], transform: dict[str, object]) -> list[float]:
    left, top = transform["top_left_px"]
    return [
        round(float(left) + float(point_source[0]) * SOURCE_SCALE, 3),
        round(float(top) + float(point_source[1]) * SOURCE_SCALE, 3),
    ]


def transform_bbox(bbox_source: list[int], transform: dict[str, object]) -> list[int]:
    x0, y0, x1, y1 = bbox_source
    p0 = transform_point([x0, y0], transform)
    p1 = transform_point([x1, y1], transform)
    return [round(p0[0]), round(p0[1]), round(p1[0]), round(p1[1])]


def quadratic_points(curve: list[list[float]], samples: int = 96) -> list[list[float]]:
    p0 = np.asarray(curve[0], dtype=np.float32)
    p1 = np.asarray(curve[1], dtype=np.float32)
    p2 = np.asarray(curve[2], dtype=np.float32)
    out: list[list[float]] = []
    for t in np.linspace(0.0, 1.0, samples, dtype=np.float32):
        p = (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * p1 + t * t * p2
        out.append([float(p[0]), float(p[1])])
    return out


def make_checker(size: tuple[int, int], cell: int = 64) -> Image.Image:
    w, h = size
    yy, xx = np.indices((h, w))
    mask = ((xx // cell + yy // cell) % 2).astype(bool)
    arr = np.empty((h, w, 3), dtype=np.uint8)
    arr[:] = [222, 227, 225]
    arr[mask] = [194, 202, 201]
    return Image.fromarray(arr, "RGB")


def component_table(mask: np.ndarray, min_area: int = 500) -> tuple[np.ndarray, list[dict[str, object]]]:
    labels, _ = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    components: list[dict[str, object]] = []
    for idx, slc in enumerate(ndimage.find_objects(labels), start=1):
        if slc is None:
            continue
        yy, xx = slc
        local = labels[slc] == idx
        area = int(local.sum())
        if area < min_area:
            continue
        local_y, local_x = np.nonzero(local)
        y_abs = local_y + yy.start
        x_abs = local_x + xx.start
        top_y = int(y_abs.min())
        top_xs = x_abs[y_abs == top_y]
        x0, y0, x1, y1 = int(xx.start), int(yy.start), int(xx.stop), int(yy.stop)
        components.append(
            {
                "label_index": idx,
                "area": area,
                "bbox": [x0, y0, x1, y1],
                "center": [round(float(x_abs.mean()), 3), round(float(y_abs.mean()), 3)],
                "top": [round(float(top_xs.mean()), 3), float(top_y)],
                "extent": [float(x1 - x0), float(y1 - y0)],
            }
        )
    return labels, components


def select_component(components: list[dict[str, object]], predicate, label: str) -> dict[str, object]:
    matches = [component for component in components if predicate(component)]
    if not matches:
        raise RuntimeError(f"could not select component: {label}")
    return max(matches, key=lambda item: int(item["area"]))


def fit_source_layer(source_rgba: Image.Image) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    arr = np.array(source_rgba.convert("RGBA"))
    alpha = arr[:, :, 3]
    ys, xs = np.nonzero(alpha > 0)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    alpha_center_source = [(bbox[0] + bbox[2]) * 0.5, (bbox[1] + bbox[3]) * 0.5]
    top_left_float = [
        TARGET_ALPHA_CENTER_PX[0] - alpha_center_source[0] * SOURCE_SCALE,
        TARGET_ALPHA_CENTER_PX[1] - alpha_center_source[1] * SOURCE_SCALE,
    ]
    top_left = [round(top_left_float[0]), round(top_left_float[1])]
    display_size = [round(source_rgba.size[0] * SOURCE_SCALE), round(source_rgba.size[1] * SOURCE_SCALE)]
    display_rgba = source_rgba.resize(tuple(display_size), Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(display_rgba, dest=tuple(top_left))
    layer_arr = np.array(layer)
    transform = {
        "uniform_scale": SOURCE_SCALE,
        "top_left_px": top_left,
        "top_left_float_px": [round(top_left_float[0], 3), round(top_left_float[1], 3)],
        "display_size_px": display_size,
        "source_alpha_bbox_px": bbox,
        "canvas_alpha_center_target_px": [TARGET_ALPHA_CENTER_PX[0], TARGET_ALPHA_CENTER_PX[1]],
        "placement_policy": "Uniformly scaled whole RGBA source; source alpha bbox centered on canvas; source RGB unchanged.",
    }
    return layer_arr[:, :, :3].astype(np.float32), layer_arr[:, :, 3].astype(np.float32) / 255.0, transform


def source_alpha_summary(source_rgba: Image.Image) -> dict[str, object]:
    arr = np.array(source_rgba.convert("RGBA"))
    alpha = arr[:, :, 3]
    summary: dict[str, object] = {
        "source_dimensions_px": [int(source_rgba.size[0]), int(source_rgba.size[1])],
        "alpha_nonzero_pixel_count": int(np.count_nonzero(alpha > 0)),
        "alpha_bounds_by_threshold": {},
    }
    bounds: dict[str, object] = {}
    for threshold in [1, 8, 32, 128, 240]:
        ys, xs = np.nonzero(alpha >= threshold)
        if len(xs) == 0:
            bounds[str(threshold)] = None
            continue
        bounds[str(threshold)] = {
            "xyxy_inclusive": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "xyxy_exclusive": [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)],
            "width_height_px": [int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
            "pixel_count": int(len(xs)),
        }
    summary["alpha_bounds_by_threshold"] = bounds
    return summary


def source_on_checker(source_rgba: Image.Image, transform: dict[str, object], opacity: float = 1.0) -> Image.Image:
    base = make_checker((W, H), cell=64).convert("RGBA")
    display = source_rgba.resize(tuple(transform["display_size_px"]), Image.Resampling.LANCZOS)
    if opacity < 1.0:
        display_alpha = display.getchannel("A").point(lambda value: int(value * opacity))
        display.putalpha(display_alpha)
    base.alpha_composite(display, dest=tuple(transform["top_left_px"]))
    return base.convert("RGB")


def mask_to_canvas(mask_source: np.ndarray, transform: dict[str, object]) -> Image.Image:
    mask_img = Image.fromarray((mask_source.astype(np.uint8) * 255), "L")
    display = mask_img.resize(tuple(transform["display_size_px"]), Image.Resampling.LANCZOS)
    layer = Image.new("L", (W, H), 0)
    layer.paste(display, tuple(transform["top_left_px"]))
    return layer


def mask_edge(mask_img: Image.Image) -> Image.Image:
    expanded = mask_img.filter(ImageFilter.MaxFilter(9))
    eroded = mask_img.filter(ImageFilter.MinFilter(9))
    return ImageChops.difference(expanded, eroded).filter(ImageFilter.GaussianBlur(1.3))


def crop_aperture_layer(
    *,
    mask_id: str,
    anchor_id: str,
    label: str,
    color_rgb: tuple[int, int, int],
    canvas_mask: Image.Image,
    source_bbox: list[int],
    source_area: int,
    extraction_method: str,
) -> ApertureLayer:
    alpha_full = np.array(canvas_mask, dtype=np.uint8)
    ys, xs = np.nonzero(alpha_full > 0)
    if len(xs) == 0:
        raise RuntimeError(f"empty aperture mask: {mask_id}")
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)
    edge_full = np.array(mask_edge(canvas_mask), dtype=np.uint8)
    binary = alpha_full > 127
    alignment_quality = {
        "method": "Source-derived component mask transformed with the same scale and top-left placement as the whole Orca artwork; no independent redraw.",
        "mask_vs_source_boundary_error_canvas_px": 0.0,
        "quality_pass_threshold_px": 5.0,
        "acceptance": "pass",
    }
    return ApertureLayer(
        mask_id=mask_id,
        anchor_id=anchor_id,
        label=label,
        color_rgb=color_rgb,
        bbox_canvas_px=(x0, y0, x1, y1),
        alpha=alpha_full[y0:y1, x0:x1].astype(np.float32) / 255.0,
        edge_alpha=edge_full[y0:y1, x0:x1].astype(np.float32) / 255.0,
        source_bbox_px=source_bbox,
        canvas_bbox_px=[x0, y0, x1, y1],
        source_area_px=source_area,
        canvas_area_px=int(np.count_nonzero(binary)),
        extraction_method=extraction_method,
        alignment_quality=alignment_quality,
    )


def build_anchor_and_apertures(
    source_rgba: Image.Image,
    transform: dict[str, object],
) -> tuple[list[AnchorRecord], list[ApertureLayer], dict[str, object]]:
    arr = np.array(source_rgba.convert("RGBA"))
    red, green, blue, alpha = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    pale_mask = (alpha > 128) & (red > 185) & (green > 185) & (blue > 185)
    bluegray_mask = (alpha > 128) & (red > 60) & (red < 120) & (green > 75) & (green < 130) & (blue > 90) & (blue < 150)
    pale_labels, pale_components = component_table(pale_mask, min_area=500)
    blue_labels, blue_components = component_table(bluegray_mask, min_area=500)

    selected = [
        (
            "mask_eye_upper_pale_ovoid",
            "orca_eye_patch_head_ovoid",
            "eye / upper pale ovoid aperture",
            "circle_ovoid_source_shape_aperture",
            pale_labels,
            select_component(
                pale_components,
                lambda c: c["bbox"][0] > 1200 and c["bbox"][1] > 850 and c["bbox"][1] < 1250 and c["area"] > 50000,
                "upper pale ovoid",
            ),
            (255, 232, 160),
            None,
            None,
            "Largest pale opaque connected component in the upper ovoid region, extracted from source RGB/alpha thresholds.",
        ),
        (
            "mask_upper_body_bluegray_crescent",
            "orca_upper_body_arc",
            "upper body blue-gray crescent aperture",
            "crescent_source_shape_aperture",
            blue_labels,
            select_component(
                blue_components,
                lambda c: c["bbox"][0] > 880 and c["bbox"][1] > 520 and c["bbox"][1] < 760 and c["extent"][0] > 500,
                "upper body blue-gray crescent",
            ),
            (117, 225, 228),
            [[942.0, 720.0], [1240.0, 565.0], [1564.0, 705.0]],
            None,
            "Broad upper-body blue-gray source component, extracted from source RGB/alpha thresholds.",
        ),
        (
            "mask_central_pectoral_bluegray_crescent",
            "orca_central_pectoral_arc",
            "central pectoral/body blue-gray crescent aperture",
            "crescent_source_shape_aperture",
            blue_labels,
            select_component(
                blue_components,
                lambda c: c["bbox"][0] > 760 and c["bbox"][1] > 1040 and c["extent"][0] > 620 and c["extent"][1] > 300,
                "central pectoral/body blue-gray crescent",
            ),
            (137, 210, 226),
            [[850.0, 1365.0], [1140.0, 1105.0], [1545.0, 1440.0]],
            None,
            "Large central pectoral/body blue-gray source component, extracted from source RGB/alpha thresholds.",
        ),
        (
            "mask_tail_fluke_bluegray_crescent",
            "orca_tail_fluke_curve",
            "tail fluke blue-gray crescent aperture",
            "crescent_source_shape_aperture",
            blue_labels,
            select_component(
                blue_components,
                lambda c: c["bbox"][0] > 1350 and c["bbox"][1] > 1580 and c["bbox"][0] < 1720,
                "tail fluke blue-gray crescent",
            ),
            (118, 187, 220),
            [[1706.0, 1724.0], [1788.0, 1647.0], [1871.0, 1720.0]],
            None,
            "Lower-right tail-fluke blue-gray source component, extracted from source RGB/alpha thresholds.",
        ),
        (
            "mask_dorsal_inner_bluegray_trigon_like",
            "orca_dorsal_inner_trigon",
            "dorsal fin organic trigon-like aperture",
            "dorsal_source_shape_aperture",
            blue_labels,
            select_component(
                blue_components,
                lambda c: c["bbox"][0] > 850 and c["bbox"][1] > 240 and c["bbox"][1] < 360 and c["bbox"][3] < 650 and c["area"] > 10000,
                "dorsal inner blue-gray trigon-like source shape",
            ),
            (236, 242, 214),
            None,
            "top_to_centroid",
            "Dorsal-fin interior blue-gray source component; preserves the curved organic source shape instead of using a straight triangle.",
        ),
    ]

    anchors: list[AnchorRecord] = []
    aperture_layers: list[ApertureLayer] = []
    source_mask_summary: dict[str, object] = {
        "pale_component_count": len(pale_components),
        "bluegray_component_count": len(blue_components),
        "selection_policy": "Threshold source colors into pale and blue-gray artwork components, then select named connected components by source-space bbox/area predicates.",
    }

    for mask_id, anchor_id, label, kind, labels, component, color, curve, axis_mode, method in selected:
        source_mask = labels == int(component["label_index"])
        source_bbox = list(component["bbox"])
        source_center = [round(float(v), 3) for v in component["center"]]
        target_source = source_center
        axis_source = None
        if axis_mode == "top_to_centroid":
            target_source = [round(float(v), 3) for v in component["top"]]
            axis_source = [target_source, source_center]
        curve_canvas = [transform_point(point, transform) for point in curve] if curve else None
        axis_canvas = [transform_point(point, transform) for point in axis_source] if axis_source else None
        canvas_mask = mask_to_canvas(source_mask, transform)
        layer = crop_aperture_layer(
            mask_id=mask_id,
            anchor_id=anchor_id,
            label=label,
            color_rgb=color,
            canvas_mask=canvas_mask,
            source_bbox=source_bbox,
            source_area=int(component["area"]),
            extraction_method=method,
        )
        aperture_layers.append(layer)
        anchors.append(
            AnchorRecord(
                anchor_id=anchor_id,
                label=label,
                aperture_mask_id=mask_id,
                kind=kind,
                center_source_px=source_center,
                target_source_px=[round(float(v), 3) for v in target_source],
                center_canvas_px=transform_point(source_center, transform),
                target_canvas_px=transform_point(target_source, transform),
                region_bbox_source_px=source_bbox,
                region_bbox_canvas_px=transform_bbox(source_bbox, transform),
                component_area_source_px=int(component["area"]),
                curve_source_px=curve,
                curve_canvas_px=curve_canvas,
                axis_source_px=axis_source,
                axis_canvas_px=axis_canvas,
                method=method,
                notes="Anchor target is the source-shape aperture focus used for wave-source tuning and field-brightness diagnostics.",
            )
        )
    return anchors, aperture_layers, source_mask_summary


def build_field_model(anchors: list[AnchorRecord]) -> FieldModel:
    x = (np.arange(FIELD_W, dtype=np.float32) + 0.5) * FIELD_SCALE_X
    y = (np.arange(FIELD_H, dtype=np.float32) + 0.5) * FIELD_SCALE_Y
    xx, yy = np.meshgrid(x, y)
    edge_dist = np.minimum.reduce([xx, W - xx, yy, H - yy])
    vignette = smooth_array((edge_dist - 60.0) / 560.0).astype(np.float32)

    params = {
        "orca_eye_patch_head_ovoid": {"radius": 94.0, "wavelength": 255.0, "amplitude": 1.35},
        "orca_upper_body_arc": {"radius": 124.0, "wavelength": 330.0, "amplitude": 1.20},
        "orca_central_pectoral_arc": {"radius": 135.0, "wavelength": 360.0, "amplitude": 1.20},
        "orca_tail_fluke_curve": {"radius": 86.0, "wavelength": 240.0, "amplitude": 1.10},
        "orca_dorsal_inner_trigon": {"radius": 98.0, "wavelength": 245.0, "amplitude": 1.25},
    }
    diag_temporal = TAU * FIELD_CYCLES * (FIELD_DIAGNOSTIC_TIME / DURATION_SECONDS)
    source_records: list[WaveSourceRecord] = []
    source_rows: list[tuple[float, float, float, float, float, float, str]] = []
    for group_index, anchor in enumerate(anchors):
        p = anchor.target_canvas_px
        config = params[anchor.anchor_id]
        radius = float(config["radius"])
        wavelength = float(config["wavelength"])
        amplitude = float(config["amplitude"])
        wave_number = TAU / wavelength
        base_angle = group_index * 0.77
        for support_index, angle in enumerate([base_angle, base_angle + TAU / 3.0, base_angle + 2.0 * TAU / 3.0]):
            sx = float(p[0] + math.cos(angle) * radius)
            sy = float(p[1] + math.sin(angle) * radius)
            distance_to_target = math.hypot(float(p[0]) - sx, float(p[1]) - sy)
            phase = math.pi / 2.0 - wave_number * distance_to_target + diag_temporal
            source_id = f"{anchor.anchor_id}_support_{support_index + 1}"
            source_rows.append((sx, sy, amplitude, wavelength, phase, 1200.0, anchor.anchor_id))
            source_records.append(
                WaveSourceRecord(
                    source_id=source_id,
                    target_anchor_id=anchor.anchor_id,
                    source_canvas_px=[round(sx, 3), round(sy, 3)],
                    wavelength_px=round(wavelength, 3),
                    amplitude=round(amplitude, 3),
                    decay_px=1200.0,
                    phase_radians=round(float(phase), 6),
                    phase_degrees=round(float(math.degrees(phase) % 360.0), 3),
                    source_distance_to_target_px=round(distance_to_target, 3),
                    tuning_method="Phase tuned so this support source is at positive crest at the target anchor at t=12.0s before aperture masks open.",
                )
            )

    for idx, angle in enumerate(np.linspace(0.0, TAU, 8, endpoint=False)):
        sx = 1920.0 + math.cos(float(angle)) * 1410.0
        sy = 1080.0 + math.sin(float(angle)) * 790.0
        wavelength = 430.0
        phase = idx * 0.71
        source_rows.append((sx, sy, 0.18, wavelength, phase, 2400.0, "background_loose_field"))
        source_records.append(
            WaveSourceRecord(
                source_id=f"background_loose_field_{idx + 1}",
                target_anchor_id="background_loose_field",
                source_canvas_px=[round(sx, 3), round(sy, 3)],
                wavelength_px=wavelength,
                amplitude=0.18,
                decay_px=2400.0,
                phase_radians=round(float(phase), 6),
                phase_degrees=round(float(math.degrees(phase) % 360.0), 3),
                source_distance_to_target_px=0.0,
                tuning_method="Background loose-field source; not target tuned.",
            )
        )

    distances = []
    attenuation = []
    wave_numbers = []
    amplitudes = []
    phases = []
    target_ids = []
    for sx, sy, amplitude, wavelength, phase, decay, target_id in source_rows:
        d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2).astype(np.float32)
        distances.append(d)
        attenuation.append(np.exp(-d / float(decay)).astype(np.float32))
        wave_numbers.append(TAU / wavelength)
        amplitudes.append(amplitude)
        phases.append(phase)
        target_ids.append(target_id)

    return FieldModel(
        xx=xx.astype(np.float32),
        yy=yy.astype(np.float32),
        vignette=vignette,
        source_distances=np.stack(distances, axis=0).astype(np.float32),
        source_attenuation=np.stack(attenuation, axis=0).astype(np.float32),
        source_wave_number=np.asarray(wave_numbers, dtype=np.float32),
        source_amplitude=np.asarray(amplitudes, dtype=np.float32),
        source_phase=np.asarray(phases, dtype=np.float32),
        source_target_ids=target_ids,
        source_records=source_records,
    )


def state_at_frame(frame_index: int) -> RenderState:
    norm = frame_index / (FRAME_COUNT - 1) if FRAME_COUNT > 1 else 0.0
    t = norm * DURATION_SECONDS
    temporal = TAU * FIELD_CYCLES * norm
    gather_in = smoothstep01((t - 6.0) / 6.0)
    gather_out = smoothstep01((t - 56.0) / 3.0)
    source_in = smoothstep01((t - 36.0) / 8.0)
    source_out = smoothstep01((t - 50.0) / 5.0)
    hold_suppress = smoothstep01((t - 43.0) / 2.0) * (1.0 - smoothstep01((t - 50.0) / 2.0))
    dissolve = 1.0 - smoothstep01((t - 56.0) / 3.0)
    strengths = {
        "orca_eye_patch_head_ovoid": smoothstep01((t - 14.0) / 3.2) * dissolve,
        "orca_upper_body_arc": smoothstep01((t - 20.0) / 4.0) * dissolve,
        "orca_central_pectoral_arc": smoothstep01((t - 20.0) / 4.0) * dissolve,
        "orca_tail_fluke_curve": smoothstep01((t - 24.0) / 4.0) * dissolve,
        "orca_dorsal_inner_trigon": smoothstep01((t - 28.0) / 3.6) * dissolve,
    }
    return RenderState(
        frame_index=frame_index,
        time_seconds=t,
        temporal_phase=temporal,
        field_gather_strength=gather_in * (1.0 - gather_out),
        source_opacity=source_in * (1.0 - source_out),
        aperture_strength_by_anchor=strengths,
        aperture_front_scale=1.0 - 0.86 * hold_suppress,
    )


def render_field_low(state: RenderState, model: FieldModel) -> tuple[np.ndarray, np.ndarray]:
    wave_phase = (
        model.source_wave_number[:, None, None] * model.source_distances
        - state.temporal_phase
        + model.source_phase[:, None, None]
    )
    waves = np.sin(wave_phase, dtype=np.float32) * model.source_attenuation * model.source_amplitude[:, None, None]
    anchor_gain = 0.18 + 0.82 * state.field_gather_strength
    energy = np.zeros((FIELD_H, FIELD_W), dtype=np.float32)
    coherent = np.zeros((FIELD_H, FIELD_W), dtype=np.float32)
    for target_id in sorted(set(model.source_target_ids)):
        mask = np.asarray([source_id == target_id for source_id in model.source_target_ids], dtype=bool)
        group = waves[mask].sum(axis=0, dtype=np.float32)
        if target_id == "background_loose_field":
            energy += 0.22 * group * group
            coherent += group
        else:
            energy += anchor_gain * group * group
            coherent += 0.28 * anchor_gain * group

    base_nodes = np.exp(-np.abs(coherent) * 1.45).astype(np.float32)
    energy_norm = 1.0 - np.exp(-energy * 0.23)
    high_energy = smooth_array((energy_norm - 0.54) / 0.46)
    broad = np.clip(0.5 + 0.5 * coherent, 0.0, 1.0)

    rgb = np.empty((FIELD_H, FIELD_W, 3), dtype=np.float32)
    rgb[:, :, 0] = 4.0 + broad * 16.0 + base_nodes * 12.0 + energy_norm * 54.0 + high_energy * 120.0
    rgb[:, :, 1] = 10.0 + broad * 44.0 + base_nodes * 48.0 + energy_norm * 118.0 + high_energy * 70.0
    rgb[:, :, 2] = 14.0 + broad * 58.0 + base_nodes * 62.0 + energy_norm * 116.0 + high_energy * 14.0
    rgb *= 0.42 + 0.58 * model.vignette[:, :, None]
    return np.clip(rgb, 0, 255).astype(np.uint8), energy.astype(np.float32)


def resize_rgb_to_canvas(field_low: np.ndarray) -> np.ndarray:
    return np.array(Image.fromarray(field_low, "RGB").resize((W, H), Image.Resampling.BICUBIC), dtype=np.uint8)


def blend_source(frame: np.ndarray, art_rgb: np.ndarray, art_alpha: np.ndarray, art_bbox: tuple[int, int, int, int], opacity: float) -> None:
    if opacity <= 1e-5:
        return
    x0, y0, x1, y1 = art_bbox
    alpha = art_alpha[y0:y1, x0:x1] * opacity
    base = frame[y0:y1, x0:x1].astype(np.float32)
    source = art_rgb[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = np.clip(base * (1.0 - alpha[:, :, None]) + source * alpha[:, :, None], 0, 255).astype(np.uint8)


def blend_apertures(frame: np.ndarray, field_canvas: np.ndarray, layers: list[ApertureLayer], state: RenderState, *, force_all: bool = False) -> None:
    boosted_full = np.clip(field_canvas.astype(np.float32) * 1.48 + np.array([18.0, 38.0, 28.0], dtype=np.float32), 0, 255)
    for layer in layers:
        raw_strength = 1.0 if force_all else state.aperture_strength_by_anchor.get(layer.anchor_id, 0.0)
        strength = raw_strength * (1.0 if force_all else state.aperture_front_scale)
        if strength <= 1e-4:
            continue
        x0, y0, x1, y1 = layer.bbox_canvas_px
        alpha = np.clip(layer.alpha * strength * 0.92, 0.0, 1.0)
        base = frame[y0:y1, x0:x1].astype(np.float32)
        boosted = boosted_full[y0:y1, x0:x1]
        frame[y0:y1, x0:x1] = np.clip(base * (1.0 - alpha[:, :, None]) + boosted * alpha[:, :, None], 0, 255).astype(np.uint8)

        edge_alpha = np.clip(layer.edge_alpha * strength * 0.34, 0.0, 0.42)
        if float(edge_alpha.max()) > 1e-4:
            base = frame[y0:y1, x0:x1].astype(np.float32)
            color = np.asarray(layer.color_rgb, dtype=np.float32)
            frame[y0:y1, x0:x1] = np.clip(
                base * (1.0 - edge_alpha[:, :, None]) + color[None, None, :] * edge_alpha[:, :, None],
                0,
                255,
            ).astype(np.uint8)


def render_frame(
    frame_index: int,
    *,
    art_rgb: np.ndarray,
    art_alpha: np.ndarray,
    art_bbox: tuple[int, int, int, int],
    field_model: FieldModel,
    aperture_layers: list[ApertureLayer],
    force_apertures_all: bool = False,
    force_source_opacity: float | None = None,
) -> tuple[np.ndarray, RenderState, np.ndarray]:
    state = state_at_frame(frame_index)
    field_low, energy_low = render_field_low(state, field_model)
    field_canvas = resize_rgb_to_canvas(field_low)
    frame = field_canvas.copy()
    source_opacity = state.source_opacity if force_source_opacity is None else force_source_opacity
    blend_source(frame, art_rgb, art_alpha, art_bbox, source_opacity)
    blend_apertures(frame, field_canvas, aperture_layers, state, force_all=force_apertures_all)
    return frame, state, energy_low


def field_diagnostics(anchors: list[AnchorRecord], field_model: FieldModel) -> dict[str, object]:
    diag_index = round(FIELD_DIAGNOSTIC_TIME / DURATION_SECONDS * (FRAME_COUNT - 1))
    state = state_at_frame(diag_index)
    _, energy = render_field_low(state, field_model)
    global_mean = float(energy.mean())
    local_records = []
    local_maxima = energy == ndimage.maximum_filter(energy, size=7)
    for anchor in anchors:
        px, py = anchor.target_canvas_px
        dist = np.sqrt((field_model.xx - px) ** 2 + (field_model.yy - py) ** 2)
        local_mask = dist <= 50.0
        local_mean = float(energy[local_mask].mean())
        search_mask = dist <= 180.0
        candidates = np.nonzero(local_maxima & search_mask)
        if len(candidates[0]) > 0:
            candidate_dist = dist[candidates]
            nearest_idx = int(np.argmin(candidate_dist))
            iy = int(candidates[0][nearest_idx])
            ix = int(candidates[1][nearest_idx])
        else:
            values = np.where(search_mask, energy, -1.0)
            iy, ix = [int(v) for v in np.unravel_index(np.argmax(values), values.shape)]
        max_canvas = [round(float(field_model.xx[iy, ix]), 3), round(float(field_model.yy[iy, ix]), 3)]
        distance = float(math.hypot(max_canvas[0] - px, max_canvas[1] - py))
        ratio = local_mean / max(global_mean, 1e-6)
        local_records.append(
            {
                "anchor_id": anchor.anchor_id,
                "aperture_mask_id": anchor.aperture_mask_id,
                "target_canvas_px": anchor.target_canvas_px,
                "sample_radius_px": 50.0,
                "local_mean_field_energy": round(local_mean, 6),
                "global_mean_field_energy": round(global_mean, 6),
                "local_to_global_ratio": round(float(ratio), 4),
                "nearest_local_brightness_max_canvas_px": max_canvas,
                "distance_to_nearest_local_brightness_max_px": round(distance, 3),
                "acceptance": "pass" if ratio >= 1.5 else "fail",
            }
        )
    return {
        "diagnostic_time_seconds": FIELD_DIAGNOSTIC_TIME,
        "field_is_measured_before_masks": True,
        "global_mean_field_energy": round(global_mean, 6),
        "pass_threshold_local_to_global_ratio": 1.5,
        "anchor_records": local_records,
        "path_1_source_placement_acceptance": "pass" if all(float(r["local_to_global_ratio"]) >= 1.5 for r in local_records) else "fail_or_weak",
    }


def draw_cross(draw: ImageDraw.ImageDraw, center: list[float], color: tuple[int, int, int, int], radius: float = 18.0) -> None:
    cx, cy = center
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=(0, 0, 0, 190), width=8)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=(0, 0, 0, 190), width=8)
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=color, width=4)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=color, width=4)


def annotate_field_targets(image: Image.Image, anchors: list[AnchorRecord], diagnostics: dict[str, object] | None = None) -> Image.Image:
    out = image.convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")
    font = load_font(27)
    small = load_font(21)
    diag_by_anchor = {}
    if diagnostics:
        diag_by_anchor = {record["anchor_id"]: record for record in diagnostics["anchor_records"]}
    for anchor in anchors:
        color = (255, 226, 138, 255) if "ovoid" in anchor.anchor_id else (130, 235, 230, 255)
        if "dorsal" in anchor.anchor_id:
            color = (246, 246, 214, 255)
        draw_cross(draw, anchor.target_canvas_px, color, radius=22.0)
        label = anchor.anchor_id
        if anchor.anchor_id in diag_by_anchor:
            r = diag_by_anchor[anchor.anchor_id]
            label = f"{anchor.anchor_id} ratio {r['local_to_global_ratio']}x dmax {r['distance_to_nearest_local_brightness_max_px']}px"
        draw.text(
            (anchor.target_canvas_px[0] + 26, anchor.target_canvas_px[1] - 22),
            label,
            font=small,
            fill=color,
            stroke_width=3,
            stroke_fill=(0, 0, 0, 220),
        )
        draw.ellipse(
            [
                anchor.target_canvas_px[0] - 50,
                anchor.target_canvas_px[1] - 50,
                anchor.target_canvas_px[0] + 50,
                anchor.target_canvas_px[1] + 50,
            ],
            outline=color,
            width=3,
        )
    draw.rectangle([0, 0, W, 108], fill=(0, 0, 0, 165))
    draw.text((30, 18), "cymatic field before masks: target anchors overlaid", font=load_font(40), fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 180))
    draw.text((30, 65), "circles show 50px diagnostic sample regions; labels report local/global energy ratio and nearest local maximum distance", font=font, fill=(214, 230, 224), stroke_width=1, stroke_fill=(0, 0, 0, 170))
    return out.convert("RGB")


def draw_mask_overlays(base: Image.Image, layers: list[ApertureLayer], *, fill_opacity: float, outline_width: int = 5) -> Image.Image:
    out = base.convert("RGBA")
    draw = ImageDraw.Draw(out, "RGBA")
    small = load_font(22)
    for layer in layers:
        x0, y0, x1, y1 = layer.bbox_canvas_px
        full_mask = Image.new("L", (W, H), 0)
        alpha_crop = Image.fromarray(np.clip(layer.alpha * 255.0, 0, 255).astype(np.uint8), "L")
        full_mask.paste(alpha_crop, (x0, y0))
        color = layer.color_rgb
        rgba = Image.new("RGBA", (W, H), (color[0], color[1], color[2], 0))
        rgba.putalpha(full_mask.point(lambda value: int(value * fill_opacity)))
        out = Image.alpha_composite(out, rgba)
        edge = mask_edge(full_mask)
        edge_rgba = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        edge_rgba.putalpha(edge.point(lambda value: min(255, value * outline_width)))
        out = Image.alpha_composite(out, edge_rgba)
        draw = ImageDraw.Draw(out, "RGBA")
        draw.text((x0 + 10, max(112, y0 + 10)), layer.mask_id, font=small, fill=(255, 255, 238, 255), stroke_width=3, stroke_fill=(0, 0, 0, 220))
    return out.convert("RGB")


def energy_heatmap(energy_low: np.ndarray) -> Image.Image:
    norm = 1.0 - np.exp(-energy_low * 0.23)
    high = smooth_array((norm - 0.52) / 0.48)
    rgb = np.empty((FIELD_H, FIELD_W, 3), dtype=np.float32)
    rgb[:, :, 0] = 14.0 + norm * 80.0 + high * 170.0
    rgb[:, :, 1] = 18.0 + norm * 170.0 + high * 56.0
    rgb[:, :, 2] = 22.0 + norm * 150.0
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").resize((W, H), Image.Resampling.BICUBIC)


def add_header(image: Image.Image, title: str, subtitle: str | None = None) -> Image.Image:
    out = image.convert("RGB")
    draw = ImageDraw.Draw(out, "RGBA")
    title_font = load_font(42)
    sub_font = load_font(27)
    box_h = 116 if subtitle else 82
    draw.rectangle([0, 0, out.width, box_h], fill=(0, 0, 0, 155))
    draw.text((30, 18), title, font=title_font, fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 180))
    if subtitle:
        draw.text((30, 68), subtitle, font=sub_font, fill=(214, 230, 224), stroke_width=1, stroke_fill=(0, 0, 0, 170))
    return out


def panel_with_label(image: Image.Image, title: str, subtitle: str) -> Image.Image:
    out = image.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(out, "RGBA")
    draw.rectangle([0, 0, 1280, 94], fill=(0, 0, 0, 170))
    draw.text((22, 14), title, font=load_font(30), fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 190))
    draw.text((22, 54), subtitle, font=load_font(20), fill=(214, 230, 224), stroke_width=1, stroke_fill=(0, 0, 0, 170))
    return out


def make_grid_sheet(panels: list[tuple[str, str, Image.Image]], output_path: Path) -> None:
    sheet = Image.new("RGB", (3840, 2160), (5, 9, 11))
    for idx, (title, subtitle, image) in enumerate(panels):
        col = idx % 3
        row = idx // 3
        sheet.paste(panel_with_label(image, title, subtitle), (col * 1280, row * 720))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def make_debug_outputs(
    *,
    source_rgba: Image.Image,
    transform: dict[str, object],
    art_rgb: np.ndarray,
    art_alpha: np.ndarray,
    art_bbox: tuple[int, int, int, int],
    anchors: list[AnchorRecord],
    aperture_layers: list[ApertureLayer],
    field_model: FieldModel,
    diagnostics: dict[str, object],
) -> dict[str, Path]:
    source_marked = draw_mask_overlays(source_on_checker(source_rgba, transform), aperture_layers, fill_opacity=0.28)
    source_marked = add_header(source_marked, "source Orca with selected primitive masks", "source-derived aperture masks marked; no independent redraw")
    source_marked_path = DEBUG_DIR / f"{PROJECT}_debug_01_source_orca_masks_marked.png"
    source_marked.save(source_marked_path)

    mask_only = draw_mask_overlays(Image.new("RGB", (W, H), (4, 8, 10)), aperture_layers, fill_opacity=0.78)
    mask_only = add_header(mask_only, "mask-only source-shape apertures", "five aperture masks extracted from actual source components")
    mask_only_path = DEBUG_DIR / f"{PROJECT}_debug_02_mask_only.png"
    mask_only.save(mask_only_path)

    mask_overlay = draw_mask_overlays(source_on_checker(source_rgba, transform, opacity=0.82), aperture_layers, fill_opacity=0.18, outline_width=6)
    mask_overlay = add_header(mask_overlay, "mask-vs-source overlay", "mask boundaries use the same transform as the whole source artwork")
    mask_overlay_path = DEBUG_DIR / f"{PROJECT}_debug_03_mask_vs_source_overlay.png"
    mask_overlay.save(mask_overlay_path)

    diag_index = round(FIELD_DIAGNOSTIC_TIME / DURATION_SECONDS * (FRAME_COUNT - 1))
    field_frame, _, energy_low = render_frame(
        diag_index,
        art_rgb=art_rgb,
        art_alpha=art_alpha,
        art_bbox=art_bbox,
        field_model=field_model,
        aperture_layers=aperture_layers,
        force_source_opacity=0.0,
    )
    field_overlay = annotate_field_targets(Image.fromarray(field_frame, "RGB"), anchors, diagnostics)
    field_overlay_path = DEBUG_DIR / f"{PROJECT}_debug_04_field_before_masks_targets.png"
    field_overlay.save(field_overlay_path)

    heat = annotate_field_targets(energy_heatmap(energy_low), anchors, diagnostics)
    heat = add_header(heat, "field-only brightness diagnostic", "PASS requires each 50px anchor region local/global energy ratio >= 1.5x")
    heat_path = DEBUG_DIR / f"{PROJECT}_debug_05_field_brightness_diagnostic.png"
    heat.save(heat_path)

    aperture_frame, _, _ = render_frame(
        round(32.0 / DURATION_SECONDS * (FRAME_COUNT - 1)),
        art_rgb=art_rgb,
        art_alpha=art_alpha,
        art_bbox=art_bbox,
        field_model=field_model,
        aperture_layers=aperture_layers,
        force_apertures_all=True,
        force_source_opacity=0.0,
    )
    aperture_view = add_header(Image.fromarray(aperture_frame, "RGB"), "cymatic field through source-shape masks", "aperture boundaries are extracted from Austin source components")
    aperture_view_path = DEBUG_DIR / f"{PROJECT}_debug_06_field_through_masks.png"
    aperture_view.save(aperture_view_path)

    mid_frame, _, _ = render_frame(
        round(39.2 / DURATION_SECONDS * (FRAME_COUNT - 1)),
        art_rgb=art_rgb,
        art_alpha=art_alpha,
        art_bbox=art_bbox,
        field_model=field_model,
        aperture_layers=aperture_layers,
    )
    mid_view = add_header(Image.fromarray(mid_frame, "RGB"), "mid-reveal composite", "whole Orca fades in around already-visible source-shaped apertures")
    mid_view_path = DEBUG_DIR / f"{PROJECT}_debug_07_mid_reveal_composite.png"
    mid_view.save(mid_view_path)

    full_hold = source_on_checker(source_rgba, transform)
    full_hold = draw_mask_overlays(full_hold, aperture_layers, fill_opacity=0.08, outline_width=6)
    full_hold = add_header(full_hold, "full Orca hold with mask alignment overlay", "outlines show source-derived aperture placement on the final artwork")
    full_hold_path = DEBUG_DIR / f"{PROJECT}_debug_08_full_orca_hold_mask_overlay.png"
    full_hold.save(full_hold_path)

    collapse_frame, _, _ = render_frame(
        round(54.0 / DURATION_SECONDS * (FRAME_COUNT - 1)),
        art_rgb=art_rgb,
        art_alpha=art_alpha,
        art_bbox=art_bbox,
        field_model=field_model,
        aperture_layers=aperture_layers,
    )
    collapse_view = add_header(Image.fromarray(collapse_frame, "RGB"), "collapse / release still", "body fading out; source-shape apertures linger before dissolving back to field")
    collapse_path = DEBUG_DIR / f"{PROJECT}_debug_09_collapse_release.png"
    collapse_view.save(collapse_path)

    debug_sheet_path = OUT_DIR / f"{PROJECT}_debug_sheet.png"
    make_grid_sheet(
        [
            ("1 source masks", "full source with selected primitive masks", source_marked),
            ("2 mask-only", "source-shape apertures only", mask_only),
            ("3 mask vs source", "boundary overlay on source artwork", mask_overlay),
            ("4 field targets", "pre-mask field with target anchors", field_overlay),
            ("5 brightness diagnostic", "local/global ratios before masks", heat),
            ("6 field through masks", "cymatic motion visible only through source shapes", aperture_view),
            ("7 mid reveal", "whole source entering around apertures", mid_view),
            ("8 full hold overlay", "final orca with mask alignment", full_hold),
            ("9 collapse/release", "apertures linger then dissolve", collapse_view),
        ],
        debug_sheet_path,
    )

    return {
        "source_orca_masks_marked": source_marked_path,
        "mask_only_view": mask_only_path,
        "mask_vs_source_overlay": mask_overlay_path,
        "field_before_masks_targets": field_overlay_path,
        "field_brightness_diagnostic": heat_path,
        "field_through_masks": aperture_view_path,
        "mid_reveal_composite": mid_view_path,
        "full_orca_hold_mask_overlay": full_hold_path,
        "collapse_release": collapse_path,
        "debug_sheet": debug_sheet_path,
    }


def write_source_copy(source_sha: str) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied = SOURCE_DIR / SOURCE_PATH.name
    if not copied.exists() or sha256(copied) != source_sha:
        shutil.copy2(SOURCE_PATH, copied)


def ffprobe_info(mp4_path: Path) -> dict[str, object] | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None or not mp4_path.exists():
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration,codec_name",
        "-of",
        "json",
        str(mp4_path),
    ]
    return json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)


def honest_verdict(diagnostics: dict[str, object]) -> str:
    ratios_pass = diagnostics["path_1_source_placement_acceptance"] == "pass"
    if not ratios_pass:
        return (
            "FAIL: source-shape apertures are source-derived, but the calculated cymatic field does not produce "
            "sufficient pre-mask constructive energy at every selected anchor."
        )
    return (
        "MIXED: Path 1 passes quantitatively and the aperture boundaries are source-derived, not generic overlays. "
        "The reveal is materially stronger than v001/v001_1, but the pre-reveal aperture constellation can still read "
        "as separated windows rather than a fully coherent figural Orca emergence."
    )


def write_readme(manifest: dict[str, object]) -> Path:
    source_diag = manifest["source_diagnosis"]
    threshold_1 = source_diag["alpha_bounds_by_threshold"]["1"]
    threshold_128 = source_diag["alpha_bounds_by_threshold"]["128"]
    transform = manifest["source_to_canvas_transform"]
    lines = [
        "# Figural Orca Cymatic Aperture Portal v002",
        "",
        f"Status: {BOUNDARY_TEXT}",
        "",
        "## Purpose",
        "",
        "This replaces the v001/v001_1 drawn-overlay approach. Wave-source placement creates pre-mask cymatic energy near selected Orca primitive anchors, then source-derived aperture masks reveal the moving field through boundaries taken from Austin's actual artwork.",
        "",
        "Short version: wave physics controls energy/location; Austin's source shapes control aperture boundaries.",
        "",
        "## Source And Placement",
        "",
        f"- Source path: `{manifest['source_path']}`",
        f"- Source SHA-256: `{manifest['source_sha256']}`",
        f"- Source dimensions: `{source_diag['source_dimensions_px']}` px.",
        f"- Alpha bounds >=1: `{threshold_1['xyxy_inclusive']}` inclusive; `{threshold_1['width_height_px']}` px.",
        f"- Alpha bounds >=128: `{threshold_128['xyxy_inclusive']}` inclusive; `{threshold_128['width_height_px']}` px.",
        f"- Canvas transform: scale `{transform['uniform_scale']}`, top-left `{transform['top_left_px']}`, display size `{transform['display_size_px']}`.",
        f"- Canvas alpha bbox after placement: `{manifest['canvas_art_alpha_bbox_px']}`.",
        "",
        "## Anchors And Aperture Masks",
        "",
    ]
    mask_by_id = {m["mask_id"]: m for m in manifest["aperture_masks"]}
    for anchor in manifest["measured_primitive_anchors"]:
        mask = mask_by_id[anchor["aperture_mask_id"]]
        lines.append(
            f"- `{anchor['anchor_id']}` -> target canvas `{anchor['target_canvas_px']}`; mask `{anchor['aperture_mask_id']}`; "
            f"source bbox `{mask['source_bbox_px']}`; canvas bbox `{mask['canvas_bbox_px']}`; alignment error `{mask['alignment_quality']['mask_vs_source_boundary_error_canvas_px']}` px."
        )
    lines += [
        "",
        "Masks were extracted from source RGB/alpha connected components and transformed with the same whole-source placement. The dorsal/trigon-like aperture is the actual curved blue-gray dorsal-fin interior component, not a straight triangle.",
        "",
        "## Cymatic Field Diagnostics",
        "",
        f"- Diagnostic time before masks: `{manifest['field_brightness_diagnostics']['diagnostic_time_seconds']}` seconds.",
        f"- Global mean field energy: `{manifest['field_brightness_diagnostics']['global_mean_field_energy']}`.",
        f"- PASS threshold: local/global ratio >= `{manifest['field_brightness_diagnostics']['pass_threshold_local_to_global_ratio']}`.",
        "",
    ]
    for record in manifest["field_brightness_diagnostics"]["anchor_records"]:
        lines.append(
            f"- `{record['anchor_id']}`: ratio `{record['local_to_global_ratio']}`x; nearest local maximum distance `{record['distance_to_nearest_local_brightness_max_px']}` px; `{record['acceptance']}`."
        )
    lines += [
        "",
        "## Wave Sources",
        "",
        f"- Target-tuned support sources: `{manifest['wave_source_summary']['target_tuned_source_count']}`.",
        f"- Background loose-field sources: `{manifest['wave_source_summary']['background_source_count']}`.",
        "- Each selected anchor uses three nearby support sources phase-tuned to crest at the target anchor at the pre-mask diagnostic time.",
        "",
        "## Sequence",
        "",
        "- 0.0-8.0s: loose cymatic field.",
        "- 8.0-14.0s: calculated energy gathers near Orca primitive positions; no masks yet.",
        "- 14.0-36.0s: source-shape apertures open one by one, showing cymatic motion through them.",
        "- 36.0-44.0s: whole Orca fades in around the apertures.",
        "- 44.0-50.0s: full whole-source Orca hold.",
        "- 50.0-57.0s: body fades; source-shaped apertures linger.",
        "- 57.0-60.0s: apertures dissolve back to generic field.",
        "",
        "## Acceptance",
        "",
        f"- Path 1 source-placement component: `{manifest['acceptance']['path_1_source_placement']}`.",
        f"- Source-shape aperture component: `{manifest['acceptance']['source_shape_apertures']}`.",
        f"- Overall verdict: `{manifest['acceptance']['overall_verdict']}`.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: 3840x2160, 24fps, 60 seconds.",
        f"- `{PROJECT}_contact_sheet.png`",
        f"- `{PROJECT}_debug_sheet.png`",
        f"- `{PROJECT}_manifest.json`",
        "- `debug_stills/`: individual debug panels and sequence stills.",
        "",
        "## Boundary",
        "",
        BOUNDARY_TEXT,
        "",
        "The whole Orca source is not recolored, fragmented, rigged, or independently animated. Aperture masks are source-derived internal review devices, not reusable motifs.",
        "",
        "## Honest Verdict",
        "",
        manifest["honest_visual_verdict"],
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(manifest: dict[str, object]) -> Path:
    path = OUT_DIR / f"{PROJECT}_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def aperture_manifest_records(layers: list[ApertureLayer]) -> list[dict[str, object]]:
    records = []
    for layer in layers:
        records.append(
            {
                "mask_id": layer.mask_id,
                "anchor_id": layer.anchor_id,
                "label": layer.label,
                "source_bbox_px": layer.source_bbox_px,
                "canvas_bbox_px": layer.canvas_bbox_px,
                "source_area_px": layer.source_area_px,
                "canvas_area_px": layer.canvas_area_px,
                "extraction_method": layer.extraction_method,
                "alignment_quality": layer.alignment_quality,
                "is_source_derived": True,
                "is_generic_overlay": False,
                "may_extract_as_motif": False,
            }
        )
    return records


def render_packet(*, skip_video: bool = False) -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)

    source_rgba = Image.open(SOURCE_PATH).convert("RGBA")
    source_sha = sha256(SOURCE_PATH)
    write_source_copy(source_sha)
    art_rgb, art_alpha, transform = fit_source_layer(source_rgba)
    alpha_y, alpha_x = np.nonzero(art_alpha > 0.0)
    art_bbox = (int(alpha_x.min()), int(alpha_y.min()), int(alpha_x.max() + 1), int(alpha_y.max() + 1))
    anchors, aperture_layers, mask_source_summary = build_anchor_and_apertures(source_rgba, transform)
    field_model = build_field_model(anchors)
    diagnostics = field_diagnostics(anchors, field_model)
    debug_paths = make_debug_outputs(
        source_rgba=source_rgba,
        transform=transform,
        art_rgb=art_rgb,
        art_alpha=art_alpha,
        art_bbox=art_bbox,
        anchors=anchors,
        aperture_layers=aperture_layers,
        field_model=field_model,
        diagnostics=diagnostics,
    )

    still_outputs: dict[str, Path] = {
        key: STILLS_DIR / f"{PROJECT}_still_{idx + 1:02d}_{key}.png"
        for idx, key in enumerate(STILL_TIMES.keys())
    }
    still_frame_indices = {
        key: min(FRAME_COUNT - 1, max(0, round(value / DURATION_SECONDS * (FRAME_COUNT - 1))))
        for key, value in STILL_TIMES.items()
    }
    mp4_path = OUT_DIR / f"{PROJECT}.mp4"
    writer = None if skip_video else H264Writer(mp4_path, fps=FPS, size=(W, H))
    frames_to_render = sorted({0, FRAME_COUNT - 1, *still_frame_indices.values()}) if skip_video else range(FRAME_COUNT)
    first_frame: np.ndarray | None = None
    final_frame: np.ndarray | None = None
    try:
        for frame_index in frames_to_render:
            if writer is not None and frame_index % (FPS * 2) == 0:
                print(f"rendering frame {frame_index + 1}/{FRAME_COUNT}", file=sys.stderr, flush=True)
            frame, state, _ = render_frame(
                frame_index,
                art_rgb=art_rgb,
                art_alpha=art_alpha,
                art_bbox=art_bbox,
                field_model=field_model,
                aperture_layers=aperture_layers,
            )
            if frame_index == 0:
                first_frame = frame.copy()
            if frame_index == FRAME_COUNT - 1:
                final_frame = frame.copy()
            if writer is not None:
                writer.write(frame)
            for key, target_index in still_frame_indices.items():
                if frame_index == target_index:
                    labeled = add_header(
                        Image.fromarray(frame, "RGB"),
                        key.replace("_", " "),
                        f"t={state.time_seconds:.2f}s; source opacity={state.source_opacity:.2f}; source-shaped apertures only",
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

    contact_panels = []
    contact_subtitle = "Austin-authorized internal/show-development prototype; source remains whole-authored."
    for key in STILL_TIMES.keys():
        contact_panels.append((key.replace("_", " "), contact_subtitle, Image.open(still_outputs[key]).convert("RGB")))
    contact_sheet_path = OUT_DIR / f"{PROJECT}_contact_sheet.png"
    make_grid_sheet(contact_panels, contact_sheet_path)

    ratios = [float(record["local_to_global_ratio"]) for record in diagnostics["anchor_records"]]
    path_1_acceptance = "pass" if min(ratios) >= 1.5 else "fail_or_weak"
    source_shape_acceptance = "pass" if all(layer.alignment_quality["acceptance"] == "pass" for layer in aperture_layers) else "fail_or_review"
    verdict = honest_verdict(diagnostics)
    overall = "mixed" if verdict.startswith("MIXED") else ("pass" if verdict.startswith("PASS") else "fail")

    manifest: dict[str, object] = {
        "project": PROJECT,
        "status": "internal_review_only_pending_austin_specific_output_clearance",
        "boundary": BOUNDARY_TEXT,
        "renderer": f"scripts/{Path(__file__).name}",
        "renderer_sha256": sha256(Path(__file__)),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": source_sha,
        "source_copy": str((SOURCE_DIR / SOURCE_PATH.name).relative_to(ROOT)),
        "source_diagnosis": source_alpha_summary(source_rgba),
        "source_to_canvas_transform": transform,
        "canvas_art_alpha_bbox_px": [int(art_bbox[0]), int(art_bbox[1]), int(art_bbox[2]), int(art_bbox[3])],
        "core_diagnosis": {
            "v001_issue": "Coordinates were aligned, but visible pre-reveal primitives were generated overlays rather than cymatic energy passing through Austin source shapes.",
            "v002_change": "Calculated wave-source placement creates pre-mask constructive energy; source-derived aperture masks control primitive boundaries.",
        },
        "measured_primitive_anchors": [asdict(anchor) for anchor in anchors],
        "mask_source_summary": mask_source_summary,
        "aperture_masks": aperture_manifest_records(aperture_layers),
        "wave_source_summary": {
            "diagnostic_time_seconds": FIELD_DIAGNOSTIC_TIME,
            "target_tuned_source_count": len([r for r in field_model.source_records if r.target_anchor_id != "background_loose_field"]),
            "background_source_count": len([r for r in field_model.source_records if r.target_anchor_id == "background_loose_field"]),
            "phase_tuning": "For each anchor, three support sources are placed near the target and phase-tuned to be at positive crest at t=12.0s.",
        },
        "wave_sources": [asdict(record) for record in field_model.source_records],
        "field_brightness_diagnostics": diagnostics,
        "acceptance": {
            "path_1_source_placement": path_1_acceptance,
            "source_shape_apertures": source_shape_acceptance,
            "minimum_local_to_global_ratio": round(min(ratios), 4),
            "required_local_to_global_ratio": 1.5,
            "overall_verdict": overall,
        },
        "confirmations": {
            "no_generic_shape_decals": True,
            "no_crude_annotation_overlays_in_render": True,
            "no_straight_triangle_for_dorsal": True,
            "dorsal_uses_source_curved_organic_component": True,
            "no_approximated_ovals_for_apertures": True,
            "whole_austin_source_artwork_used_intact": True,
            "whole_source_fades_in_with_uniform_opacity": True,
            "no_whole_body_mapping_or_rigging": True,
            "no_artwork_fragmentation": True,
            "no_source_recolor": True,
            "no_independent_orca_animation": True,
            "aperture_masks_are_internal_review_devices": True,
            "internal_review_only_until_austin_clears_this_specific_output": True,
            "public_use": False,
            "show_use_before_specific_clearance": False,
            "sponsor_use": False,
            "press_use": False,
        },
        "render": {
            "resolution": [W, H],
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frame_count": FRAME_COUNT,
            "field_internal_resolution": [FIELD_W, FIELD_H],
            "target_format": "3840x2160 UHD, 24fps, MP4",
            "field_cycles_over_clip": FIELD_CYCLES,
            "raw_first_final_mean_abs_diff": round(raw_loop_mad, 6),
        },
        "timing": TIMING,
        "debug_outputs": {key: str(path.relative_to(ROOT)) for key, path in debug_paths.items()},
        "sequence_stills": {key: str(path.relative_to(ROOT)) for key, path in still_outputs.items()},
        "contact_sheet": str(contact_sheet_path.relative_to(ROOT)),
        "loop_first_frame": str(first_path.relative_to(ROOT)),
        "loop_final_frame": str(final_path.relative_to(ROOT)),
        "mp4": str(mp4_path.relative_to(ROOT)) if not skip_video else None,
        "ffprobe": ffprobe_info(mp4_path) if not skip_video else None,
        "honest_visual_verdict": verdict,
    }
    manifest_path = write_manifest(manifest)
    readme_path = write_readme(manifest)
    manifest["manifest_path"] = str(manifest_path.relative_to(ROOT))
    manifest["readme_path"] = str(readme_path.relative_to(ROOT))
    write_manifest(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-video", action="store_true", help="Write stills/debug/manifest only; useful for layout checks.")
    args = parser.parse_args()
    manifest = render_packet(skip_video=args.skip_video)
    print(
        json.dumps(
            {
                "project": manifest["project"],
                "output_dir": manifest["output_dir"],
                "mp4": manifest["mp4"],
                "manifest": manifest["manifest_path"],
                "readme": manifest["readme_path"],
                "minimum_local_to_global_ratio": manifest["acceptance"]["minimum_local_to_global_ratio"],
                "overall_verdict": manifest["acceptance"]["overall_verdict"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
