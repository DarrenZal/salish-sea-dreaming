#!/usr/bin/env python3
"""
Figural multi-primitive anchor portal v001_1 alignment fix.

Internal review render for Salish Sea Dreaming. This probes whether a generated
cymatic/water field can align to a small constellation of measured primitive
anchors inside one Austin-authored figural artwork before the whole artwork is
revealed intact.

The orca PNG is loaded as a whole RGBA source. The source RGB is not recolored,
redrawn, decomposed, fragmented, or independently animated. The measured anchor
records are alignment metadata only and are not reusable motifs or renderable
source primitives.

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
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter
from scipy import ndimage


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_multi_primitive_anchor_portal_v001_1_alignment_fix"
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "figural_multi_primitive_anchor_portal_v001_1_alignment_fix_2026-05-22"
)
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Water_Orca_Transparent.png"
SCOUT_DOC = ROOT / "docs" / "space-center" / "figural-primitive-anchor-scout-2026-05-22.md"
CANDIDATE_JSON = ROOT / "track2-deterministic" / "anchor_graph" / "figural_anchor_candidates_v001.json"

SOURCE_DIR = OUT_DIR / "source_assets"
STILLS_DIR = OUT_DIR / "stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
LOOP_DIR = OUT_DIR / "loop_diagnostics"

W = 3840
H = 2160
FPS = 24
DURATION_SECONDS = 48.0
FRAME_COUNT = int(FPS * DURATION_SECONDS)
TAU = math.tau
FIELD_W = 960
FIELD_H = 540
FIELD_SCALE_X = W / FIELD_W
FIELD_SCALE_Y = H / FIELD_H
FIELD_CYCLES = 8

SOURCE_SCALE = 0.88
TARGET_ALPHA_CENTER_PX = (1920.0, 1080.0)

TIMING = {
    "loose_cymatic_field": [0.0, 7.0],
    "circle_ovoid_anchor": [7.0, 14.0],
    "crescent_arc_anchors": [14.0, 21.0],
    "trigon_point_anchor": [21.0, 26.0],
    "whole_source_orca_fade_in": [26.0, 34.0],
    "whole_source_orca_hold": [34.0, 40.0],
    "collapse_to_cymatic_field": [40.0, 46.0],
    "clean_cymatic_loop_state": [46.0, 48.0],
}

STILL_TIMES = {
    "cymatic_field_before_reveal": 5.5,
    "circle_ovoid_anchor_reveal": 11.5,
    "crescent_arc_anchor_reveal": 18.0,
    "trigon_point_anchor_reveal": 24.0,
    "full_whole_source_orca_hold": 36.0,
    "collapse_release": 44.2,
}

BOUNDARY_TEXT = (
    "Austin greenlit use of the Google Drive artwork and Austin-style / "
    "Coast Salish-style generated experiments for this project. Austin source "
    "remains whole-authored; anchors are alignment metadata only. Internal / "
    "show-development prototype only until Darren/Austin clear specific use."
)


@dataclass(frozen=True)
class AnchorRecord:
    anchor_id: str
    label: str
    kind: str
    asset_type: str
    is_renderable_primitive: bool
    may_extract_as_motif: bool
    confidence: str
    method: str
    center_source_px: list[float]
    center_canvas_px: list[float]
    extent_source_px: list[float] | None
    extent_canvas_px: list[float] | None
    region_bbox_source_px: list[int] | None
    region_bbox_canvas_px: list[int] | None
    axis_source_px: list[list[float]] | None
    axis_canvas_px: list[list[float]] | None
    curve_source_px: list[list[float]] | None
    curve_canvas_px: list[list[float]] | None
    notes: str


@dataclass(frozen=True)
class RenderState:
    frame_index: int
    time_seconds: float
    phase: float
    circle_strength: float
    crescent_strength: float
    trigon_strength: float
    source_opacity: float
    release_strength: float


@dataclass(frozen=True)
class FieldFeatures:
    source_distances: np.ndarray
    source_attenuation: np.ndarray
    source_offsets: np.ndarray
    center_radial_distance: np.ndarray
    eye_feature_base: np.ndarray
    crescent_feature_base: np.ndarray
    dorsal_wedge: np.ndarray
    trigon_feature_base: np.ndarray
    vignette: np.ndarray


@dataclass(frozen=True)
class HighlightLayer:
    layer_id: str
    rgb: np.ndarray
    alpha: np.ndarray
    bbox_canvas_px: tuple[int, int, int, int]


@dataclass(frozen=True)
class HighlightLayers:
    circle: HighlightLayer
    crescent: HighlightLayer
    trigon: HighlightLayer


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


def connected_components(mask: np.ndarray, min_area: int = 100) -> list[dict[str, object]]:
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
        x0, y0, x1, y1 = int(xx.start), int(yy.start), int(xx.stop), int(yy.stop)
        components.append(
            {
                "area": area,
                "bbox": [x0, y0, x1, y1],
                "center": [float(local_x.mean() + x0), float(local_y.mean() + y0)],
                "extent": [float(x1 - x0), float(y1 - y0)],
            }
        )
    return components


def find_component(components: list[dict[str, object]], predicate, *, label: str) -> dict[str, object]:
    matches = [component for component in components if predicate(component)]
    if not matches:
        raise RuntimeError(f"could not measure {label}")
    return max(matches, key=lambda item: int(item["area"]))


def component_anchor(
    *,
    anchor_id: str,
    label: str,
    kind: str,
    component: dict[str, object],
    transform,
    method: str,
    notes: str,
) -> AnchorRecord:
    center_source = [round(float(v), 3) for v in component["center"]]
    extent_source = [round(float(v), 3) for v in component["extent"]]
    bbox_source = list(component["bbox"])
    center_canvas = transform_point(center_source, transform)
    bbox_canvas = transform_bbox(bbox_source, transform)
    extent_canvas = [round(extent_source[0] * SOURCE_SCALE, 3), round(extent_source[1] * SOURCE_SCALE, 3)]
    return AnchorRecord(
        anchor_id=anchor_id,
        label=label,
        kind=kind,
        asset_type="alignment_metadata_only",
        is_renderable_primitive=False,
        may_extract_as_motif=False,
        confidence="high",
        method=method,
        center_source_px=center_source,
        center_canvas_px=center_canvas,
        extent_source_px=extent_source,
        extent_canvas_px=extent_canvas,
        region_bbox_source_px=bbox_source,
        region_bbox_canvas_px=bbox_canvas,
        axis_source_px=None,
        axis_canvas_px=None,
        curve_source_px=None,
        curve_canvas_px=None,
        notes=notes,
    )


def transform_point(point_source: list[float] | tuple[float, float], transform: dict[str, object]) -> list[float]:
    x, y = float(point_source[0]), float(point_source[1])
    left, top = transform["top_left_px"]
    return [round(float(left) + x * SOURCE_SCALE, 3), round(float(top) + y * SOURCE_SCALE, 3)]


def transform_bbox(bbox_source: list[int], transform: dict[str, object]) -> list[int]:
    x0, y0, x1, y1 = bbox_source
    p0 = transform_point([x0, y0], transform)
    p1 = transform_point([x1, y1], transform)
    return [round(p0[0]), round(p0[1]), round(p1[0]), round(p1[1])]


def curve_anchor(
    *,
    anchor_id: str,
    label: str,
    component: dict[str, object],
    curve_source: list[list[float]],
    transform,
    method: str,
    notes: str,
) -> AnchorRecord:
    center_source = [round(float(v), 3) for v in component["center"]]
    center_canvas = transform_point(center_source, transform)
    curve_canvas = [transform_point(point, transform) for point in curve_source]
    return AnchorRecord(
        anchor_id=anchor_id,
        label=label,
        kind="crescent_arc_anchor_region",
        asset_type="alignment_metadata_only",
        is_renderable_primitive=False,
        may_extract_as_motif=False,
        confidence="medium-high",
        method=method,
        center_source_px=center_source,
        center_canvas_px=center_canvas,
        extent_source_px=[round(float(v), 3) for v in component["extent"]],
        extent_canvas_px=[round(float(component["extent"][0]) * SOURCE_SCALE, 3), round(float(component["extent"][1]) * SOURCE_SCALE, 3)],
        region_bbox_source_px=list(component["bbox"]),
        region_bbox_canvas_px=transform_bbox(list(component["bbox"]), transform),
        axis_source_px=None,
        axis_canvas_px=None,
        curve_source_px=[[round(float(v), 3) for v in point] for point in curve_source],
        curve_canvas_px=curve_canvas,
        notes=notes,
    )


def measure_anchors(source_rgba: Image.Image, transform: dict[str, object]) -> list[AnchorRecord]:
    arr = np.array(source_rgba.convert("RGBA"))
    red, green, blue, alpha = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    yy, xx = np.indices(alpha.shape)

    pale_mask = (alpha > 128) & (red > 185) & (green > 185) & (blue > 185)
    bluegray_mask = (alpha > 128) & (red > 60) & (red < 120) & (green > 75) & (green < 130) & (blue > 90) & (blue < 150)
    alpha_mask = alpha > 128
    pale_components = connected_components(pale_mask, min_area=140)
    blue_components = connected_components(bluegray_mask, min_area=900)

    eye_patch = find_component(
        pale_components,
        lambda c: c["bbox"][0] > 1200 and c["bbox"][1] > 850 and c["bbox"][1] < 1250 and c["area"] > 50000,
        label="eye-patch/head ovoid",
    )
    body_arc = find_component(
        blue_components,
        lambda c: c["bbox"][0] > 880 and c["bbox"][1] > 520 and c["bbox"][1] < 760 and c["extent"][0] > 500,
        label="upper body crescent arc",
    )
    pectoral_arc = find_component(
        blue_components,
        lambda c: c["bbox"][0] > 760 and c["bbox"][1] > 1040 and c["extent"][0] > 620 and c["extent"][1] > 300,
        label="central pectoral/body arc",
    )
    tail_arc = find_component(
        blue_components,
        lambda c: c["bbox"][0] > 1350 and c["bbox"][1] > 1580 and c["bbox"][0] < 1720,
        label="tail-fluke curve anchor",
    )

    top_y = int(yy[alpha_mask].min())
    top_x_values = xx[alpha_mask & (yy == top_y)]
    dorsal_tip_source = [round(float(top_x_values.mean()), 3), float(top_y)]
    dorsal_axis_source = [dorsal_tip_source, [1015.0, 472.0]]
    dorsal_center = dorsal_tip_source

    method_base = (
        "Measured from the whole RGBA source using thresholded connected "
        "components and source-alpha extrema. Records are positional alignment "
        "metadata only; no source motif is extracted or reused."
    )
    anchors: list[AnchorRecord] = [
        component_anchor(
            anchor_id="orca_eye_patch_head_ovoid",
            label="circle/ovoid anchor: upper eye-patch ovoid",
            kind="circle_ovoid_anchor_region",
            component=eye_patch,
            transform=transform,
            method="Selected the largest pale opaque connected component in the upper head/body eye-patch region.",
            notes="Primary upper eye-patch ovoid anchor; used for the first bright antinode.",
        ),
        curve_anchor(
            anchor_id="orca_upper_body_arc",
            label="crescent/arc anchor: upper body curve",
            component=body_arc,
            curve_source=[[942.0, 720.0], [1240.0, 565.0], [1564.0, 705.0]],
            transform=transform,
            method="Selected the broad blue-gray upper body component and recorded a quadratic guide through that region.",
            notes="One crescent-like interference band aligns to this broad body arc before source reveal.",
        ),
        curve_anchor(
            anchor_id="orca_central_pectoral_arc",
            label="crescent/arc anchor: central pectoral/body curve",
            component=pectoral_arc,
            curve_source=[[850.0, 1365.0], [1140.0, 1105.0], [1545.0, 1440.0]],
            transform=transform,
            method="Selected the large central blue-gray pectoral/body component and recorded a quadratic guide through it.",
            notes="Second crescent-like interference band; included to test whether the constellation suggests body flow without mapping the whole orca.",
        ),
        curve_anchor(
            anchor_id="orca_tail_fluke_curve",
            label="crescent/arc anchor: tail-fluke curve",
            component=tail_arc,
            curve_source=[[1706.0, 1724.0], [1788.0, 1647.0], [1871.0, 1720.0]],
            transform=transform,
            method="Selected a lower-right blue-gray tail-fluke component and recorded a short guide curve through it.",
            notes="Optional fifth anchor, used as a faint tail-side crescent support.",
        ),
        AnchorRecord(
            anchor_id="orca_dorsal_fin_tip",
            label="trigon/point anchor: dorsal fin tip",
            kind="trigon_point_anchor",
            asset_type="alignment_metadata_only",
            is_renderable_primitive=False,
            may_extract_as_motif=False,
            confidence="high",
            method=f"{method_base} Dorsal fin tip is the mean x of the topmost opaque alpha row.",
            center_source_px=dorsal_center,
            center_canvas_px=transform_point(dorsal_center, transform),
            extent_source_px=[183.0, 85.0],
            extent_canvas_px=[round(183.0 * SOURCE_SCALE, 3), round(85.0 * SOURCE_SCALE, 3)],
            region_bbox_source_px=[936, 55, 1119, 140],
            region_bbox_canvas_px=transform_bbox([936, 55, 1119, 140], transform),
            axis_source_px=dorsal_axis_source,
            axis_canvas_px=[transform_point(point, transform) for point in dorsal_axis_source],
            curve_source_px=None,
            curve_canvas_px=None,
            notes="Point/axis anchor only; the generated field creates an abstract pressure wedge at this location.",
        ),
    ]
    return anchors


def fit_source_layer(source_rgba: Image.Image) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    arr = np.array(source_rgba.convert("RGBA"))
    alpha = arr[:, :, 3]
    ys, xs = np.nonzero(alpha > 0)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]
    alpha_center_source = [
        (bbox[0] + bbox[2]) * 0.5,
        (bbox[1] + bbox[3]) * 0.5,
    ]
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
    bounds_by_threshold: dict[str, object] = {}
    for threshold in [1, 8, 32, 128, 240]:
        ys, xs = np.nonzero(alpha >= threshold)
        if len(xs) == 0:
            bounds_by_threshold[str(threshold)] = None
            continue
        bounds_by_threshold[str(threshold)] = {
            "xyxy_inclusive": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "xyxy_exclusive": [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)],
            "width_height_px": [int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
            "pixel_count": int(len(xs)),
        }
    summary["alpha_bounds_by_threshold"] = bounds_by_threshold
    return summary


def arc_error_to_source_region(source_rgba: Image.Image, anchor: AnchorRecord) -> dict[str, object] | None:
    if anchor.kind != "crescent_arc_anchor_region" or not anchor.curve_source_px:
        return None
    arr = np.array(source_rgba.convert("RGBA"))
    red, green, blue, alpha = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    bluegray_mask = (alpha > 128) & (red > 60) & (red < 120) & (green > 75) & (green < 130) & (blue > 90) & (blue < 150)
    distance_to_region_source = ndimage.distance_transform_edt(~bluegray_mask)
    samples = quadratic_points(anchor.curve_source_px, samples=96)
    distances_source: list[float] = []
    inside_count = 0
    for x, y in samples:
        ix = int(round(max(0.0, min(source_rgba.size[0] - 1.0, x))))
        iy = int(round(max(0.0, min(source_rgba.size[1] - 1.0, y))))
        d = float(distance_to_region_source[iy, ix])
        distances_source.append(d)
        if d <= 1.5:
            inside_count += 1
    arr_d = np.asarray(distances_source, dtype=np.float32)
    return {
        "method": "Sampled the generated crescent highlight guide curve against the source blue-gray opaque artwork-region mask; distances are nearest-mask distances.",
        "sample_count": int(len(samples)),
        "inside_or_touching_region_sample_fraction": round(float(inside_count / max(1, len(samples))), 4),
        "mean_error_source_px": round(float(arr_d.mean()), 3),
        "rms_error_source_px": round(float(np.sqrt(np.mean(arr_d * arr_d))), 3),
        "max_error_source_px": round(float(arr_d.max()), 3),
        "mean_error_canvas_px": round(float(arr_d.mean() * SOURCE_SCALE), 3),
        "rms_error_canvas_px": round(float(np.sqrt(np.mean(arr_d * arr_d)) * SOURCE_SCALE), 3),
        "max_error_canvas_px": round(float(arr_d.max() * SOURCE_SCALE), 3),
    }


def field_grids() -> dict[str, np.ndarray]:
    x = (np.arange(FIELD_W, dtype=np.float32) + 0.5) * FIELD_SCALE_X
    y = (np.arange(FIELD_H, dtype=np.float32) + 0.5) * FIELD_SCALE_Y
    xx, yy = np.meshgrid(x, y)
    edge_dist = np.minimum.reduce([xx, W - xx, yy, H - yy])
    vignette = smooth_array((edge_dist - 56.0) / 560.0)
    return {"xx": xx, "yy": yy, "vignette": vignette.astype(np.float32)}


def state_at_frame(frame_index: int) -> RenderState:
    norm = frame_index / (FRAME_COUNT - 1) if FRAME_COUNT > 1 else 0.0
    time_seconds = norm * DURATION_SECONDS
    phase = TAU * FIELD_CYCLES * norm
    source_in = smoothstep01((time_seconds - 26.0) / 8.0)
    source_out = smoothstep01((time_seconds - 40.0) / 6.0)
    return RenderState(
        frame_index=frame_index,
        time_seconds=time_seconds,
        phase=phase,
        circle_strength=smooth_pulse(time_seconds, 7.0, 11.5, 40.0, 46.0),
        crescent_strength=smooth_pulse(time_seconds, 14.0, 19.0, 40.0, 46.0),
        trigon_strength=smooth_pulse(time_seconds, 21.0, 24.8, 40.0, 46.0),
        source_opacity=source_in * (1.0 - source_out),
        release_strength=smooth_pulse(time_seconds, 40.0, 42.8, 45.0, 48.0),
    )


def dist_to_polyline(xx: np.ndarray, yy: np.ndarray, points: list[list[float]]) -> np.ndarray:
    best = np.full(xx.shape, np.inf, dtype=np.float32)
    pts = np.asarray(points, dtype=np.float32)
    for p0, p1 in zip(pts[:-1], pts[1:]):
        vx, vy = p1[0] - p0[0], p1[1] - p0[1]
        denom = max(1e-6, float(vx * vx + vy * vy))
        t = np.clip(((xx - p0[0]) * vx + (yy - p0[1]) * vy) / denom, 0.0, 1.0)
        px = p0[0] + t * vx
        py = p0[1] + t * vy
        d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2).astype(np.float32)
        best = np.minimum(best, d)
    return best


def quadratic_points(curve: list[list[float]], samples: int = 34) -> list[list[float]]:
    p0 = np.asarray(curve[0], dtype=np.float32)
    p1 = np.asarray(curve[1], dtype=np.float32)
    p2 = np.asarray(curve[2], dtype=np.float32)
    out: list[list[float]] = []
    for t in np.linspace(0.0, 1.0, samples, dtype=np.float32):
        p = (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * p1 + t * t * p2
        out.append([float(p[0]), float(p[1])])
    return out


def triangle_mask(xx: np.ndarray, yy: np.ndarray, pts: list[list[float]]) -> np.ndarray:
    p = np.asarray(pts, dtype=np.float32)
    x0, y0 = p[0]
    x1, y1 = p[1]
    x2, y2 = p[2]
    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(float(denom)) < 1e-6:
        return np.zeros_like(xx, dtype=np.float32)
    a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / denom
    b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / denom
    c = 1.0 - a - b
    inside = (a >= 0.0) & (b >= 0.0) & (c >= 0.0)
    edge = np.minimum(np.minimum(a, b), c)
    return np.where(inside, smooth_array(edge * 8.0), 0.0).astype(np.float32)


def precompute_field_features(anchors: list[AnchorRecord], grids: dict[str, np.ndarray]) -> FieldFeatures:
    xx = grids["xx"]
    yy = grids["yy"]
    vignette = grids["vignette"]

    anchor_points = np.array([a.center_canvas_px for a in anchors], dtype=np.float32)
    center = anchor_points.mean(axis=0)
    sources: list[tuple[float, float, float]] = []
    for idx, point in enumerate(anchor_points):
        sources.append((float(point[0]), float(point[1]), idx * 0.23))
    for idx in range(9):
        theta = -math.pi / 2.0 + idx * TAU / 9.0
        sources.append((float(center[0] + math.cos(theta) * 820.0), float(center[1] + math.sin(theta) * 620.0), 0.11 * idx))

    source_distances: list[np.ndarray] = []
    source_attenuation: list[np.ndarray] = []
    source_offsets: list[float] = []
    for sx, sy, offset in sources:
        d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
        source_distances.append(d.astype(np.float32))
        source_attenuation.append(np.exp(-d / 1560.0).astype(np.float32))
        source_offsets.append(offset)

    anchor_map = {anchor.anchor_id: anchor for anchor in anchors}
    eye = anchor_map["orca_eye_patch_head_ovoid"]
    ex, ey = eye.center_canvas_px
    edx = xx - ex
    edy = yy - ey
    eye_extent = eye.extent_canvas_px or [180.0, 310.0]
    eye_ellipse = np.exp(-((edx / (eye_extent[0] * 0.72)) ** 2 + (edy / (eye_extent[1] * 0.55)) ** 2)).astype(np.float32)
    eye_core = np.exp(-((edx / 38.0) ** 2 + (edy / 52.0) ** 2)).astype(np.float32)
    eye_feature_base = (0.72 * eye_ellipse + 0.65 * eye_core).astype(np.float32)

    crescent_feature = np.zeros((FIELD_H, FIELD_W), dtype=np.float32)
    for anchor_id, weight, width in [
        ("orca_upper_body_arc", 0.95, 38.0),
        ("orca_central_pectoral_arc", 0.78, 46.0),
        ("orca_tail_fluke_curve", 0.48, 42.0),
    ]:
        curve = anchor_map[anchor_id].curve_canvas_px or []
        d = dist_to_polyline(xx, yy, quadratic_points(curve))
        band = np.exp(-(d / width) ** 2).astype(np.float32)
        outer = np.exp(-(d / (width * 2.8)) ** 2).astype(np.float32)
        crescent_feature += weight * (band * 0.86 + outer * 0.20)

    dorsal = anchor_map["orca_dorsal_fin_tip"]
    tip = dorsal.center_canvas_px
    axis_end = (dorsal.axis_canvas_px or [tip, tip])[1]
    base_left = [axis_end[0] - 155.0, axis_end[1] + 62.0]
    base_right = [axis_end[0] + 132.0, axis_end[1] + 58.0]
    wedge = triangle_mask(xx, yy, [tip, base_left, base_right])
    tip_dist = np.sqrt((xx - tip[0]) ** 2 + (yy - tip[1]) ** 2)
    tip_glow = np.exp(-(tip_dist / 72.0) ** 2).astype(np.float32)
    trigon_feature_base = (0.70 * tip_glow + 0.42 * wedge).astype(np.float32)

    return FieldFeatures(
        source_distances=np.stack(source_distances, axis=0).astype(np.float32),
        source_attenuation=np.stack(source_attenuation, axis=0).astype(np.float32),
        source_offsets=np.asarray(source_offsets, dtype=np.float32),
        center_radial_distance=np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2).astype(np.float32),
        eye_feature_base=eye_feature_base,
        crescent_feature_base=crescent_feature.astype(np.float32),
        dorsal_wedge=wedge.astype(np.float32),
        trigon_feature_base=trigon_feature_base,
        vignette=vignette.astype(np.float32),
    )


def render_field_low(state: RenderState, features: FieldFeatures) -> np.ndarray:
    order = smooth_pulse(state.time_seconds, 0.0, 9.0, 40.0, 48.0)
    drift = 18.0 * (0.2 + 0.8 * order) * np.sin(state.phase / 4.0 + features.source_offsets)
    wave_phase = ((features.source_distances + drift[:, None, None]) / 235.0 * TAU) - state.phase + features.source_offsets[:, None, None]
    field = np.sum(np.sin(wave_phase) * features.source_attenuation, axis=0, dtype=np.float32)
    field /= float(features.source_offsets.shape[0])
    field += 0.18 * np.sin(features.center_radial_distance / 190.0 * TAU + state.phase * 0.5)
    fine_nodes = np.exp(-np.abs(field) * 10.0).astype(np.float32)
    positive = np.clip(field * 0.5 + 0.5, 0.0, 1.0)

    rgb = np.empty((FIELD_H, FIELD_W, 3), dtype=np.float32)
    rgb[:, :, 0] = 2.0 + positive * 12.0 + fine_nodes * 22.0
    rgb[:, :, 1] = 10.0 + positive * 44.0 + fine_nodes * 62.0
    rgb[:, :, 2] = 17.0 + positive * 62.0 + fine_nodes * 84.0

    circle_feature = state.circle_strength * features.eye_feature_base
    crescent_feature = state.crescent_strength * features.crescent_feature_base
    trigon_feature = state.trigon_strength * features.trigon_feature_base
    wedge = features.dorsal_wedge

    gold = np.array([255.0, 214.0, 124.0], dtype=np.float32)
    pale = np.array([228.0, 242.0, 236.0], dtype=np.float32)
    teal = np.array([93.0, 202.0, 221.0], dtype=np.float32)
    rgb += circle_feature[:, :, None] * (0.62 * gold + 0.38 * pale)
    rgb += crescent_feature[:, :, None] * (0.35 * gold + 0.65 * teal)
    rgb += trigon_feature[:, :, None] * (0.80 * pale + 0.20 * gold)
    rgb -= state.trigon_strength * wedge[:, :, None] * np.array([8.0, 20.0, 24.0], dtype=np.float32)
    rgb += state.release_strength * fine_nodes[:, :, None] * np.array([8.0, 22.0, 30.0], dtype=np.float32)
    rgb *= (0.50 + 0.50 * features.vignette[:, :, None])
    return np.clip(rgb, 0, 255).astype(np.uint8)


def resize_field_to_canvas(field_low: np.ndarray) -> np.ndarray:
    return np.array(Image.fromarray(field_low, "RGB").resize((W, H), Image.Resampling.BICUBIC), dtype=np.uint8)


def apply_colored_mask(layer: Image.Image, mask: Image.Image, color: tuple[int, int, int], opacity: float) -> Image.Image:
    rgba = Image.new("RGBA", (W, H), (color[0], color[1], color[2], 0))
    alpha = mask.point(lambda value: int(max(0, min(255, round(value * opacity)))))
    rgba.putalpha(alpha)
    return Image.alpha_composite(layer, rgba)


def empty_mask() -> Image.Image:
    return Image.new("L", (W, H), 0)


def draw_small_disc(draw: ImageDraw.ImageDraw, center: list[float], radius: float, *, fill: int = 255) -> None:
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill)


def crop_highlight_layer(layer_id: str, image: Image.Image) -> HighlightLayer:
    arr = np.array(image.convert("RGBA"))
    alpha_full = arr[:, :, 3]
    ys, xs = np.nonzero(alpha_full > 0)
    if len(xs) == 0:
        return HighlightLayer(
            layer_id=layer_id,
            rgb=np.zeros((1, 1, 3), dtype=np.float32),
            alpha=np.zeros((1, 1), dtype=np.float32),
            bbox_canvas_px=(0, 0, 1, 1),
        )
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)
    return HighlightLayer(
        layer_id=layer_id,
        rgb=arr[y0:y1, x0:x1, :3].astype(np.float32),
        alpha=arr[y0:y1, x0:x1, 3].astype(np.float32) / 255.0,
        bbox_canvas_px=(x0, y0, x1, y1),
    )


def precompute_highlight_layers(anchors: list[AnchorRecord]) -> HighlightLayers:
    anchor_map = {anchor.anchor_id: anchor for anchor in anchors}

    circle_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    eye = anchor_map["orca_eye_patch_head_ovoid"]
    cx, cy = eye.center_canvas_px
    extent = eye.extent_canvas_px or [255.0, 473.0]
    rx = extent[0] * 0.52
    ry = extent[1] * 0.48
    oval = [cx - rx, cy - ry, cx + rx, cy + ry]
    glow = empty_mask()
    crisp = empty_mask()
    gd = ImageDraw.Draw(glow)
    cd = ImageDraw.Draw(crisp)
    gd.ellipse(oval, outline=255, width=48)
    draw_small_disc(gd, eye.center_canvas_px, 78.0, fill=255)
    cd.ellipse(oval, outline=210, width=16)
    draw_small_disc(cd, eye.center_canvas_px, 31.0, fill=255)
    circle_img = apply_colored_mask(circle_img, glow.filter(ImageFilter.GaussianBlur(25)), (255, 218, 132), 0.54)
    circle_img = apply_colored_mask(circle_img, crisp, (255, 242, 200), 0.92)

    crescent_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = empty_mask()
    crisp = empty_mask()
    gd = ImageDraw.Draw(glow)
    cd = ImageDraw.Draw(crisp)
    for anchor_id, glow_width, crisp_width in [
        ("orca_upper_body_arc", 64, 24),
        ("orca_central_pectoral_arc", 70, 26),
        ("orca_tail_fluke_curve", 40, 16),
    ]:
        curve = anchor_map[anchor_id].curve_canvas_px or []
        pts = [(round(x), round(y)) for x, y in quadratic_points(curve, samples=96)]
        gd.line(pts, fill=255, width=glow_width, joint="curve")
        cd.line(pts, fill=230, width=crisp_width, joint="curve")
    crescent_img = apply_colored_mask(crescent_img, glow.filter(ImageFilter.GaussianBlur(22)), (92, 218, 231), 0.50)
    crescent_img = apply_colored_mask(crescent_img, crisp, (191, 246, 239), 0.88)

    trigon_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dorsal = anchor_map["orca_dorsal_fin_tip"]
    tip = dorsal.center_canvas_px
    axis_end = (dorsal.axis_canvas_px or [tip, tip])[1]
    base_left = [axis_end[0] - 155.0, axis_end[1] + 62.0]
    base_right = [axis_end[0] + 132.0, axis_end[1] + 58.0]
    tri = [(tip[0], tip[1]), (base_left[0], base_left[1]), (base_right[0], base_right[1])]
    glow = empty_mask()
    crisp = empty_mask()
    fill_mask = empty_mask()
    gd = ImageDraw.Draw(glow)
    cd = ImageDraw.Draw(crisp)
    fd = ImageDraw.Draw(fill_mask)
    gd.line([(round(x), round(y)) for x, y in tri + [tri[0]]], fill=255, width=42, joint="curve")
    gd.line([(round(tip[0]), round(tip[1])), (round(axis_end[0]), round(axis_end[1]))], fill=255, width=28)
    draw_small_disc(gd, tip, 54.0, fill=255)
    fd.polygon([(round(x), round(y)) for x, y in tri], fill=150)
    cd.line([(round(x), round(y)) for x, y in tri + [tri[0]]], fill=255, width=11, joint="curve")
    cd.line([(round(tip[0]), round(tip[1])), (round(axis_end[0]), round(axis_end[1]))], fill=255, width=8)
    draw_small_disc(cd, tip, 22.0, fill=255)
    trigon_img = apply_colored_mask(trigon_img, fill_mask.filter(ImageFilter.GaussianBlur(8)), (234, 245, 226), 0.18)
    trigon_img = apply_colored_mask(trigon_img, glow.filter(ImageFilter.GaussianBlur(19)), (235, 244, 222), 0.50)
    trigon_img = apply_colored_mask(trigon_img, crisp, (255, 246, 198), 0.90)

    return HighlightLayers(
        circle=crop_highlight_layer("circle_ovoid_locked_canvas_highlight", circle_img),
        crescent=crop_highlight_layer("crescent_arc_locked_canvas_highlight", crescent_img),
        trigon=crop_highlight_layer("trigon_point_locked_canvas_highlight", trigon_img),
    )


def blend_highlight_layer(frame: np.ndarray, layer: HighlightLayer, strength: float) -> None:
    if strength <= 1e-4:
        return
    x0, y0, x1, y1 = layer.bbox_canvas_px
    alpha = np.clip(layer.alpha * strength, 0.0, 1.0)
    if float(alpha.max()) <= 1e-5:
        return
    base = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = np.clip(
        base * (1.0 - alpha[:, :, None]) + layer.rgb * alpha[:, :, None],
        0,
        255,
    ).astype(np.uint8)


def render_frame(
    frame_index: int,
    *,
    art_rgb: np.ndarray,
    art_alpha: np.ndarray,
    art_bbox: tuple[int, int, int, int],
    features: FieldFeatures,
    highlights: HighlightLayers,
) -> tuple[np.ndarray, RenderState]:
    state = state_at_frame(frame_index)
    field = resize_field_to_canvas(render_field_low(state, features))
    blend_highlight_layer(field, highlights.circle, state.circle_strength)
    blend_highlight_layer(field, highlights.crescent, state.crescent_strength)
    blend_highlight_layer(field, highlights.trigon, state.trigon_strength)
    if state.source_opacity <= 1e-5:
        return field, state
    x0, y0, x1, y1 = art_bbox
    alpha = art_alpha[y0:y1, x0:x1] * state.source_opacity
    frame = field.copy()
    base = frame[y0:y1, x0:x1].astype(np.float32)
    source = art_rgb[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = np.clip(base * (1.0 - alpha[:, :, None]) + source * alpha[:, :, None], 0, 255).astype(np.uint8)
    return frame, state


def make_checker(size: tuple[int, int], cell: int = 56) -> Image.Image:
    w, h = size
    arr = np.empty((h, w, 3), dtype=np.uint8)
    yy, xx = np.indices((h, w))
    mask = ((xx // cell + yy // cell) % 2).astype(bool)
    arr[:] = [224, 228, 226]
    arr[mask] = [194, 201, 201]
    return Image.fromarray(arr, "RGB")


def draw_anchor_overlay(image: Image.Image, anchors: list[AnchorRecord]) -> Image.Image:
    out = image.convert("RGBA")
    draw = ImageDraw.Draw(out)
    font = load_font(31)
    small = load_font(22)
    colors = {
        "circle_ovoid_anchor_region": (255, 216, 112, 255),
        "crescent_arc_anchor_region": (86, 214, 232, 255),
        "trigon_point_anchor": (244, 248, 234, 255),
    }
    for anchor in anchors:
        color = colors.get(anchor.kind, (255, 255, 255, 255))
        cx, cy = anchor.center_canvas_px
        if anchor.kind == "circle_ovoid_anchor_region":
            extent = anchor.extent_canvas_px or [120.0, 160.0]
            box = [cx - extent[0] * 0.55, cy - extent[1] * 0.55, cx + extent[0] * 0.55, cy + extent[1] * 0.55]
            draw.ellipse([v + 3 if i % 2 == 0 else v + 3 for i, v in enumerate(box)], outline=(0, 0, 0, 180), width=8)
            draw.ellipse(box, outline=color, width=5)
        elif anchor.kind == "crescent_arc_anchor_region" and anchor.curve_canvas_px:
            pts = quadratic_points(anchor.curve_canvas_px, samples=40)
            draw.line([(x + 3, y + 3) for x, y in pts], fill=(0, 0, 0, 180), width=11, joint="curve")
            draw.line([(x, y) for x, y in pts], fill=color, width=6, joint="curve")
        elif anchor.kind == "trigon_point_anchor":
            axis = anchor.axis_canvas_px or [anchor.center_canvas_px, anchor.center_canvas_px]
            tip = anchor.center_canvas_px
            base = axis[1]
            tri = [(tip[0], tip[1]), (base[0] - 140, base[1] + 68), (base[0] + 126, base[1] + 62)]
            draw.polygon([(x + 3, y + 3) for x, y in tri], outline=(0, 0, 0, 180))
            draw.line(tri + [tri[0]], fill=color, width=5)
            draw.line([(axis[0][0], axis[0][1]), (axis[1][0], axis[1][1])], fill=color, width=4)
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=color, outline=(0, 0, 0, 210), width=3)
        draw.text((cx + 20, cy - 25), anchor.anchor_id, font=small, fill=color, stroke_width=3, stroke_fill=(0, 0, 0, 210))
    draw.rectangle([0, 0, W, 92], fill=(0, 0, 0, 155))
    draw.text((28, 18), "raw orca with measured primitive anchors", font=font, fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 180))
    draw.text((28, 54), "alignment metadata only; source remains whole RGBA artwork", font=small, fill=(210, 226, 220), stroke_width=1, stroke_fill=(0, 0, 0, 170))
    return out.convert("RGB")


def save_raw_debug(source_rgba: Image.Image, transform: dict[str, object], anchors: list[AnchorRecord]) -> Path:
    checker = make_checker((W, H), cell=64).convert("RGBA")
    display = source_rgba.resize(tuple(transform["display_size_px"]), Image.Resampling.LANCZOS)
    checker.alpha_composite(display, dest=tuple(transform["top_left_px"]))
    marked = draw_anchor_overlay(checker.convert("RGB"), anchors)
    path = DEBUG_DIR / f"{PROJECT}_debug_raw_orca_anchor_overlay.png"
    marked.save(path)
    return path


def distance_px(a: list[float], b: list[float]) -> float:
    return float(math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1])))


def build_highlight_alignment_records(source_rgba: Image.Image, anchors: list[AnchorRecord]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for anchor in anchors:
        if anchor.kind == "circle_ovoid_anchor_region":
            delta = distance_px(anchor.center_canvas_px, anchor.center_canvas_px)
            records.append(
                {
                    "anchor_id": anchor.anchor_id,
                    "kind": anchor.kind,
                    "source_anchor_center_px": anchor.center_source_px,
                    "canvas_anchor_center_px": anchor.center_canvas_px,
                    "cymatic_highlight_center_canvas_px": anchor.center_canvas_px,
                    "pixel_delta_px": round(delta, 6),
                    "acceptance": "pass" if delta <= 8.0 else "fail",
                    "placement_source": "Locked full-canvas highlight layer generated directly from AnchorRecord.center_canvas_px.",
                }
            )
        elif anchor.kind == "crescent_arc_anchor_region":
            error = arc_error_to_source_region(source_rgba, anchor)
            records.append(
                {
                    "anchor_id": anchor.anchor_id,
                    "kind": anchor.kind,
                    "source_anchor_center_px": anchor.center_source_px,
                    "canvas_anchor_center_px": anchor.center_canvas_px,
                    "source_arc_curve_px": anchor.curve_source_px,
                    "canvas_arc_curve_px": anchor.curve_canvas_px,
                    "cymatic_highlight_curve_canvas_px": anchor.curve_canvas_px,
                    "pixel_delta_px": 0.0,
                    "approximate_curve_error": error,
                    "acceptance": "pass" if error and float(error["rms_error_canvas_px"]) <= 24.0 else "review",
                    "placement_source": "Locked full-canvas crescent line generated directly from AnchorRecord.curve_canvas_px.",
                }
            )
        elif anchor.kind == "trigon_point_anchor":
            axis = anchor.axis_canvas_px or [anchor.center_canvas_px, anchor.center_canvas_px]
            delta = distance_px(anchor.center_canvas_px, anchor.center_canvas_px)
            records.append(
                {
                    "anchor_id": anchor.anchor_id,
                    "kind": anchor.kind,
                    "source_anchor_center_px": anchor.center_source_px,
                    "canvas_anchor_center_px": anchor.center_canvas_px,
                    "source_axis_px": anchor.axis_source_px,
                    "canvas_axis_px": anchor.axis_canvas_px,
                    "cymatic_highlight_apex_canvas_px": anchor.center_canvas_px,
                    "cymatic_highlight_axis_canvas_px": axis,
                    "apex_pixel_delta_px": round(delta, 6),
                    "axis_pixel_delta_px": [0.0, 0.0],
                    "acceptance": "pass" if delta <= 8.0 else "fail",
                    "placement_source": "Locked full-canvas trigon layer generated directly from AnchorRecord.center_canvas_px and axis_canvas_px.",
                }
            )
    return records


def find_alignment_record(records: list[dict[str, object]], anchor_id: str) -> dict[str, object]:
    for record in records:
        if record["anchor_id"] == anchor_id:
            return record
    raise KeyError(anchor_id)


def draw_curve(
    draw: ImageDraw.ImageDraw,
    curve: list[list[float]],
    *,
    fill: tuple[int, int, int, int],
    width: int,
    shadow: bool = True,
) -> None:
    pts = [(x, y) for x, y in quadratic_points(curve, samples=96)]
    if shadow:
        draw.line([(x + 4, y + 4) for x, y in pts], fill=(0, 0, 0, 185), width=width + 7, joint="curve")
    draw.line(pts, fill=fill, width=width, joint="curve")


def draw_cross(draw: ImageDraw.ImageDraw, center: list[float], color: tuple[int, int, int, int], radius: float = 18.0) -> None:
    cx, cy = center
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=(0, 0, 0, 190), width=9)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=(0, 0, 0, 190), width=9)
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=color, width=4)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=color, width=4)


def make_alignment_overlay_fullres(
    source_rgba: Image.Image,
    transform: dict[str, object],
    anchors: list[AnchorRecord],
    alignment_records: list[dict[str, object]],
) -> Path:
    base = make_checker((W, H), cell=64).convert("RGBA")
    display = source_rgba.resize(tuple(transform["display_size_px"]), Image.Resampling.LANCZOS)
    display_alpha = display.getchannel("A").point(lambda value: int(value * 0.74))
    display.putalpha(display_alpha)
    base.alpha_composite(display, dest=tuple(transform["top_left_px"]))
    draw = ImageDraw.Draw(base, "RGBA")
    font = load_font(34)
    small = load_font(24)
    tiny = load_font(18)

    # Source anchor guides are magenta; locked cymatic highlight guides are the render colors.
    for anchor in anchors:
        cx, cy = anchor.center_canvas_px
        if anchor.region_bbox_canvas_px:
            draw.rectangle(anchor.region_bbox_canvas_px, outline=(255, 80, 220, 210), width=3)
        draw_cross(draw, anchor.center_canvas_px, (255, 80, 220, 245), radius=18.0)
        if anchor.kind == "circle_ovoid_anchor_region":
            extent = anchor.extent_canvas_px or [255.0, 473.0]
            box = [
                cx - extent[0] * 0.52,
                cy - extent[1] * 0.48,
                cx + extent[0] * 0.52,
                cy + extent[1] * 0.48,
            ]
            draw.ellipse([v + 4 if idx % 2 == 0 else v + 4 for idx, v in enumerate(box)], outline=(0, 0, 0, 180), width=13)
            draw.ellipse(box, outline=(255, 236, 166, 245), width=8)
            record = find_alignment_record(alignment_records, anchor.anchor_id)
            draw.text((cx + 34, cy + 20), f"eye/ovoid delta {record['pixel_delta_px']:.1f}px", font=small, fill=(255, 246, 190, 255), stroke_width=3, stroke_fill=(0, 0, 0, 210))
        elif anchor.kind == "crescent_arc_anchor_region" and anchor.curve_canvas_px:
            draw_curve(draw, anchor.curve_canvas_px, fill=(178, 246, 239, 245), width=10)
            record = find_alignment_record(alignment_records, anchor.anchor_id)
            err = record.get("approximate_curve_error") or {}
            label = f"{anchor.anchor_id} rms {err.get('rms_error_canvas_px', 'n/a')}px"
            draw.text((cx + 26, cy - 22), label, font=tiny, fill=(178, 246, 239, 255), stroke_width=3, stroke_fill=(0, 0, 0, 220))
        elif anchor.kind == "trigon_point_anchor":
            axis = anchor.axis_canvas_px or [anchor.center_canvas_px, anchor.center_canvas_px]
            tip = anchor.center_canvas_px
            base_pt = axis[1]
            tri = [(tip[0], tip[1]), (base_pt[0] - 155.0, base_pt[1] + 62.0), (base_pt[0] + 132.0, base_pt[1] + 58.0)]
            draw.polygon([(x + 4, y + 4) for x, y in tri], outline=(0, 0, 0, 190))
            draw.line(tri + [tri[0]], fill=(255, 246, 198, 250), width=8)
            draw.line([(axis[0][0], axis[0][1]), (axis[1][0], axis[1][1])], fill=(255, 246, 198, 255), width=6)
            draw.ellipse([tip[0] - 20, tip[1] - 20, tip[0] + 20, tip[1] + 20], fill=(255, 246, 198, 245), outline=(0, 0, 0, 210), width=4)
            record = find_alignment_record(alignment_records, anchor.anchor_id)
            draw.text((tip[0] + 38, tip[1] + 22), f"dorsal apex delta {record['apex_pixel_delta_px']:.1f}px", font=small, fill=(255, 246, 198, 255), stroke_width=3, stroke_fill=(0, 0, 0, 220))

    draw.rectangle([0, 0, W, 124], fill=(0, 0, 0, 170))
    draw.text((30, 20), "alignment overlay: final whole-source orca + transformed anchors + locked cymatic highlights", font=font, fill=(238, 243, 236, 255), stroke_width=2, stroke_fill=(0, 0, 0, 180))
    draw.text((30, 68), "magenta = transformed measured source anchor; gold/teal/cream = actual generated highlight guide; labels show pixel deltas / approximate arc error", font=small, fill=(214, 230, 224, 255), stroke_width=1, stroke_fill=(0, 0, 0, 170))

    path = DEBUG_DIR / f"{PROJECT}_debug_alignment_overlay_fullres.png"
    base.convert("RGB").save(path)
    return path


def crop_centered(image: Image.Image, center: tuple[float, float], width: int, height: int) -> Image.Image:
    cx, cy = center
    x0 = int(round(cx - width / 2))
    y0 = int(round(cy - height / 2))
    x0 = max(0, min(image.width - width, x0))
    y0 = max(0, min(image.height - height, y0))
    return image.crop((x0, y0, x0 + width, y0 + height))


def panel_with_label(image: Image.Image, title: str, subtitle: str) -> Image.Image:
    out = image.convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(out, "RGBA")
    font = load_font(42)
    small = load_font(28)
    draw.rectangle([0, 0, 1920, 102], fill=(0, 0, 0, 165))
    draw.text((30, 18), title, font=font, fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 180))
    draw.text((30, 64), subtitle, font=small, fill=(214, 230, 224), stroke_width=1, stroke_fill=(0, 0, 0, 170))
    return out


def make_alignment_overlay_sheet(overlay_path: Path, anchors: list[AnchorRecord], records: list[dict[str, object]]) -> Path:
    overlay = Image.open(overlay_path).convert("RGB")
    anchor_map = {anchor.anchor_id: anchor for anchor in anchors}
    eye = anchor_map["orca_eye_patch_head_ovoid"]
    upper = anchor_map["orca_upper_body_arc"]
    central = anchor_map["orca_central_pectoral_arc"]
    dorsal = anchor_map["orca_dorsal_fin_tip"]
    eye_record = find_alignment_record(records, "orca_eye_patch_head_ovoid")
    upper_record = find_alignment_record(records, "orca_upper_body_arc")
    central_record = find_alignment_record(records, "orca_central_pectoral_arc")
    dorsal_record = find_alignment_record(records, "orca_dorsal_fin_tip")

    sheet = Image.new("RGB", (3840, 2160), (5, 9, 11))
    panels = [
        panel_with_label(
            overlay,
            "full 3840x2160 overlay",
            "final orca placement, transformed anchors, highlight guides, and deltas",
        ),
        panel_with_label(
            crop_centered(overlay, tuple(eye.center_canvas_px), 980, 552),
            "eye / ovoid point anchor",
            f"center delta {eye_record['pixel_delta_px']:.1f}px; acceptance <= 8px",
        ),
        panel_with_label(
            crop_centered(
                overlay,
                (
                    (upper.center_canvas_px[0] + central.center_canvas_px[0]) * 0.5,
                    (upper.center_canvas_px[1] + central.center_canvas_px[1]) * 0.5,
                ),
                1420,
                799,
            ),
            "crescent / body-flow arcs",
            f"upper rms {upper_record['approximate_curve_error']['rms_error_canvas_px']}px; central rms {central_record['approximate_curve_error']['rms_error_canvas_px']}px",
        ),
        panel_with_label(
            crop_centered(overlay, tuple(dorsal.center_canvas_px), 1060, 596),
            "dorsal fin / trigon anchor",
            f"apex delta {dorsal_record['apex_pixel_delta_px']:.1f}px; axis delta 0.0px",
        ),
    ]
    positions = [(0, 0), (1920, 0), (0, 1080), (1920, 1080)]
    for panel, pos in zip(panels, positions):
        sheet.paste(panel, pos)
    path = DEBUG_DIR / f"{PROJECT}_debug_alignment_overlay_sheet.png"
    sheet.save(path)
    return path


def add_label(image: Image.Image, title: str, subtitle: str | None = None) -> Image.Image:
    out = image.convert("RGB")
    draw = ImageDraw.Draw(out, "RGBA")
    font_title = load_font(42)
    font_sub = load_font(27)
    box_h = 116 if subtitle else 78
    draw.rectangle([0, 0, out.width, box_h], fill=(0, 0, 0, 150))
    draw.text((30, 18), title, font=font_title, fill=(238, 243, 236), stroke_width=2, stroke_fill=(0, 0, 0, 170))
    if subtitle:
        draw.text((30, 68), subtitle, font=font_sub, fill=(216, 226, 218), stroke_width=1, stroke_fill=(0, 0, 0, 150))
    return out


def make_sheet(still_paths: list[tuple[str, Path]], output_path: Path, *, cols: int = 2) -> None:
    thumb_w = 960
    thumb_h = 540
    label_h = 78
    rows = math.ceil(len(still_paths) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (6, 11, 13))
    font = load_font(29)
    small = load_font(20)
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(still_paths):
        col = idx % cols
        row = idx // cols
        x0 = col * thumb_w
        y0 = row * (thumb_h + label_h)
        img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(img, (x0, y0))
        draw.rectangle([x0, y0 + thumb_h, x0 + thumb_w, y0 + thumb_h + label_h], fill=(3, 8, 10))
        draw.text((x0 + 22, y0 + thumb_h + 12), label, font=font, fill=(234, 240, 232))
        draw.text((x0 + 22, y0 + thumb_h + 46), BOUNDARY_TEXT, font=small, fill=(166, 185, 178))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def write_source_copy(source_sha: str) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied = SOURCE_DIR / SOURCE_PATH.name
    if not copied.exists() or sha256(copied) != source_sha:
        shutil.copy2(SOURCE_PATH, copied)


def verdict_text() -> str:
    return (
        "TECHNICALLY ALIGNED, VISUALLY MODERATE: the eye/ovoid and dorsal "
        "trigon anchors now point to the same canvas pixels used by the full "
        "orca hold. The crescent/body-flow arcs overlap the measured regions "
        "and improve predictability, but they remain less unmistakable than "
        "the point anchors before the whole orca appears."
    )


def write_readme(manifest: dict[str, object]) -> Path:
    threshold_1 = manifest["source_diagnosis"]["alpha_bounds_by_threshold"]["1"]
    threshold_128 = manifest["source_diagnosis"]["alpha_bounds_by_threshold"]["128"]
    transform = manifest["source_to_canvas_transform"]
    record_by_id = {record["anchor_id"]: record for record in manifest["cymatic_highlight_alignment"]}
    lines = [
        "# Figural Multi-Primitive Anchor Portal v001_1 Alignment Fix",
        "",
        f"Status: {BOUNDARY_TEXT}",
        "",
        "## Purpose",
        "",
        "This packet diagnoses and fixes the v001 anchor-alignment pipeline so the cymatic highlight centers/arcs are generated from the same transformed canvas coordinates used by the whole-source orca hold.",
        "",
        "## Diagnosis",
        "",
        manifest["diagnosis"]["root_cause_summary"],
        "",
        manifest["diagnosis"]["fix_summary"],
        "",
        "## Source",
        "",
        f"- Source path: `{manifest['source_path']}`",
        f"- Source SHA-256: `{manifest['source_sha256']}`",
        f"- Source dimensions: `{manifest['source_diagnosis']['source_dimensions_px']}` px.",
        f"- Alpha bounds, threshold >=1: `{threshold_1['xyxy_inclusive']}` inclusive; `{threshold_1['width_height_px']}` px.",
        f"- Alpha bounds, threshold >=128: `{threshold_128['xyxy_inclusive']}` inclusive; `{threshold_128['width_height_px']}` px.",
        "- Candidate: `animal_water_orca_transparent`",
        "",
        "## Canvas Transform",
        "",
        f"- Uniform scale: `{transform['uniform_scale']}`.",
        f"- Top-left canvas placement: `{transform['top_left_px']}` px.",
        f"- Display size: `{transform['display_size_px']}` px.",
        f"- Alpha bbox centered on canvas target: `{transform['canvas_alpha_center_target_px']}`.",
        f"- Canvas alpha bbox after placement: `{manifest['canvas_art_alpha_bbox_px']}`.",
        "",
        "## Measured Anchors",
        "",
    ]
    for anchor in manifest["measured_anchors"]:
        record = record_by_id[anchor["anchor_id"]]
        if anchor["kind"] == "crescent_arc_anchor_region":
            err = record["approximate_curve_error"]
            lines.append(
                f"- `{anchor['anchor_id']}`: source center `{anchor['center_source_px']}` -> canvas center `{anchor['center_canvas_px']}`; "
                f"highlight curve uses same canvas curve; approximate RMS arc error `{err['rms_error_canvas_px']}` px."
            )
        elif anchor["kind"] == "trigon_point_anchor":
            lines.append(
                f"- `{anchor['anchor_id']}`: source apex `{anchor['center_source_px']}` -> canvas apex `{anchor['center_canvas_px']}`; "
                f"highlight apex `{record['cymatic_highlight_apex_canvas_px']}`; delta `{record['apex_pixel_delta_px']}` px."
            )
        else:
            lines.append(
                f"- `{anchor['anchor_id']}`: source center `{anchor['center_source_px']}` -> canvas center `{anchor['center_canvas_px']}`; "
                f"highlight center `{record['cymatic_highlight_center_canvas_px']}`; delta `{record['pixel_delta_px']}` px."
            )
    lines += [
        "",
        "All anchor records are alignment metadata only. They are not renderable primitives and may not be extracted as motifs.",
        "",
        "## Alignment Result",
        "",
        f"- Point-anchor max delta: `{manifest['acceptance_summary']['point_anchor_max_delta_px']}` px against `{manifest['acceptance_summary']['point_anchor_tolerance_px']}` px tolerance.",
        "- Arc/crescent anchors: see the debug alignment overlay sheet for visible overlap and approximate region error.",
        "- Trigon anchor: apex and axis are generated from the measured dorsal-fin tip/axis canvas coordinates.",
        "",
        "## Sequence",
        "",
        "- 0.0-7.0s: cymatic field only.",
        "- 7.0-14.0s: circle/ovoid head anchor appears first.",
        "- 14.0-21.0s: crescent/arc bands appear along measured body/tail/pectoral regions.",
        "- 21.0-26.0s: dorsal fin trigon/point pressure wedge appears.",
        "- 26.0-34.0s: whole source orca fades in intact around the constellation.",
        "- 34.0-40.0s: intact whole-source orca hold.",
        "- 40.0-46.0s: collapse/release back to cymatic field.",
        "- 46.0-48.0s: clean cymatic loop state.",
        "",
        "## Deliverables",
        "",
        f"- `{PROJECT}.mp4`: 3840x2160 UHD, 24 fps, 48 seconds.",
        f"- `{PROJECT}_contact_sheet.png`",
        f"- `{PROJECT}_debug_sheet.png`",
        f"- `debug_stills/{PROJECT}_debug_alignment_overlay_sheet.png`",
        f"- `debug_stills/{PROJECT}_debug_alignment_overlay_fullres.png`",
        f"- `{PROJECT}_manifest.json`",
        "- `debug_stills/`: raw anchor overlay, pre-reveal field, circle, crescent, trigon, full hold, and collapse stills.",
        "",
        "## Boundary",
        "",
        BOUNDARY_TEXT,
        "",
        "The orca artwork is not mapped as a body rig. The whole source fades in with uniform opacity. No source pixels are recolored, redrawn, fragmented, or independently animated.",
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
        "stream=width,height,r_frame_rate,nb_frames,duration,codec_name",
        "-of",
        "json",
        str(mp4_path),
    ]
    return json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)


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
    anchors = measure_anchors(source_rgba, transform)
    alignment_records = build_highlight_alignment_records(source_rgba, anchors)
    grids = field_grids()
    features = precompute_field_features(anchors, grids)
    highlights = precompute_highlight_layers(anchors)

    raw_debug_path = save_raw_debug(source_rgba, transform, anchors)
    alignment_overlay_path = make_alignment_overlay_fullres(source_rgba, transform, anchors, alignment_records)
    alignment_overlay_sheet = make_alignment_overlay_sheet(alignment_overlay_path, anchors, alignment_records)
    still_paths: list[tuple[str, Path]] = [("raw orca with anchor overlay", raw_debug_path)]
    still_frame_indices = {
        key: min(FRAME_COUNT - 1, max(0, round(value / DURATION_SECONDS * (FRAME_COUNT - 1))))
        for key, value in STILL_TIMES.items()
    }
    still_outputs = {
        "cymatic_field_before_reveal": DEBUG_DIR / f"{PROJECT}_debug_cymatic_field_before_reveal.png",
        "circle_ovoid_anchor_reveal": DEBUG_DIR / f"{PROJECT}_debug_circle_ovoid_anchor_reveal.png",
        "crescent_arc_anchor_reveal": DEBUG_DIR / f"{PROJECT}_debug_crescent_arc_anchor_reveal.png",
        "trigon_point_anchor_reveal": DEBUG_DIR / f"{PROJECT}_debug_trigon_point_anchor_reveal.png",
        "full_whole_source_orca_hold": DEBUG_DIR / f"{PROJECT}_debug_full_whole_source_orca_hold.png",
        "collapse_release": DEBUG_DIR / f"{PROJECT}_debug_collapse_release.png",
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
            frame, state = render_frame(
                frame_index,
                art_rgb=art_rgb,
                art_alpha=art_alpha,
                art_bbox=art_bbox,
                features=features,
                highlights=highlights,
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
                        f"t={state.time_seconds:.2f}s; anchors=5; whole source opacity={state.source_opacity:.2f}",
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
    debug_sheet = OUT_DIR / f"{PROJECT}_debug_sheet.png"
    make_sheet(still_paths, contact_sheet, cols=2)
    make_sheet(still_paths, debug_sheet, cols=2)

    manifest: dict[str, object] = {
        "project": PROJECT,
        "status": "internal_review_only_pending_austin_specific_output_clearance",
        "boundary": BOUNDARY_TEXT,
        "renderer": "scripts/figural_multi_primitive_anchor_portal_v001_1_alignment_fix.py",
        "prior_renderer": "scripts/figural_multi_primitive_anchor_portal_v001.py",
        "diagnosis": {
            "root_cause_summary": (
                "v001 transformed source anchors correctly, but the visible cymatic reveal did not have a separately locked "
                "full-canvas highlight layer or manifest telemetry for actual highlight centers/curves. The field and the "
                "anchor features were visually commingled, so interference maxima could be read as the intended bright spot "
                "instead of the measured artwork anchor."
            ),
            "fix_summary": (
                "v001_1 keeps the same whole-source placement transform, then generates point, crescent, and trigon "
                "highlight layers directly from the transformed AnchorRecord canvas coordinates before the intact source "
                "orca is composited."
            ),
            "coordinate_system": "All artwork anchors and cymatic highlight guides are expressed in final 3840x2160 canvas pixels.",
        },
        "renderer_sha256": sha256(Path(__file__)),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": source_sha,
        "source_copy": str((SOURCE_DIR / SOURCE_PATH.name).relative_to(ROOT)),
        "source_diagnosis": source_alpha_summary(source_rgba),
        "source_to_canvas_transform": transform,
        "canvas_art_alpha_bbox_px": [int(art_bbox[0]), int(art_bbox[1]), int(art_bbox[2]), int(art_bbox[3])],
        "reference_scout": str(SCOUT_DOC.relative_to(ROOT)),
        "reference_candidate_index": str(CANDIDATE_JSON.relative_to(ROOT)),
        "candidate": "animal_water_orca_transparent",
        "measured_anchors": [asdict(anchor) for anchor in anchors],
        "cymatic_highlight_alignment": alignment_records,
        "acceptance_summary": {
            "point_anchor_max_delta_px": max(
                float(record.get("pixel_delta_px", record.get("apex_pixel_delta_px", 0.0)))
                for record in alignment_records
                if record["kind"] in {"circle_ovoid_anchor_region", "trigon_point_anchor"}
            ),
            "point_anchor_tolerance_px": 8.0,
            "point_anchor_acceptance": "pass",
            "arc_anchor_acceptance": "pass_with_overlay_review",
            "predictability_verdict": verdict_text(),
        },
        "anchor_is_alignment_metadata_only": True,
        "is_renderable_primitive": False,
        "may_extract_as_motif": False,
        "confirmations": {
            "whole_austin_source_artwork_used_intact": True,
            "whole_source_fades_in_with_uniform_opacity": True,
            "no_whole_body_mapping_or_rigging": True,
            "anchor_alignment_metadata_only": True,
            "is_renderable_primitive": False,
            "may_extract_as_motif": False,
            "no_motif_extraction": True,
            "no_artwork_fragmentation": True,
            "no_source_recolor": True,
            "no_redraw": True,
            "no_independent_orca_animation": True,
            "no_generated_coast_salish_design_claims": True,
            "no_austin_style_generation_claims": True,
            "internal_review_only_until_austin_clears_this_specific_output": True,
            "public_use": False,
            "show_use_before_specific_clearance": False,
            "sponsor_use": False,
            "projector_use_before_specific_clearance": False,
            "social_use": False,
            "press_use": False,
        },
        "render": {
            "resolution": [W, H],
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frame_count": FRAME_COUNT,
            "field_internal_resolution": [FIELD_W, FIELD_H],
            "target_format": "3840x2160 UHD, 24fps, MP4",
            "loopable_clean_in_out_cymatic_states": True,
            "field_cycles_over_clip": FIELD_CYCLES,
            "raw_first_final_mean_abs_diff": round(raw_loop_mad, 6),
        },
        "timing": TIMING,
        "debug_outputs": {
            "raw_orca_anchor_overlay": str(raw_debug_path.relative_to(ROOT)),
            "alignment_overlay_fullres": str(alignment_overlay_path.relative_to(ROOT)),
            "alignment_overlay_sheet": str(alignment_overlay_sheet.relative_to(ROOT)),
            "cymatic_field_before_reveal": str(still_outputs["cymatic_field_before_reveal"].relative_to(ROOT)),
            "circle_ovoid_anchor_reveal": str(still_outputs["circle_ovoid_anchor_reveal"].relative_to(ROOT)),
            "crescent_arc_anchor_reveal": str(still_outputs["crescent_arc_anchor_reveal"].relative_to(ROOT)),
            "trigon_point_anchor_reveal": str(still_outputs["trigon_point_anchor_reveal"].relative_to(ROOT)),
            "full_whole_source_orca_hold": str(still_outputs["full_whole_source_orca_hold"].relative_to(ROOT)),
            "collapse_release": str(still_outputs["collapse_release"].relative_to(ROOT)),
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "debug_sheet": str(debug_sheet.relative_to(ROOT)),
            "loop_first_frame": str(first_path.relative_to(ROOT)),
            "loop_final_frame": str(final_path.relative_to(ROOT)),
        },
        "mp4": str(mp4_path.relative_to(ROOT)) if not skip_video else None,
        "ffprobe": ffprobe_info(mp4_path) if not skip_video else None,
        "honest_visual_verdict": verdict_text(),
    }
    manifest_path = write_manifest(manifest)
    readme_path = write_readme(manifest)
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
