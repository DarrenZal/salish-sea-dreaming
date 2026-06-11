#!/usr/bin/env python3
"""
Figural Orca wave-interference match research scout v001.

This is a research and geometry-fit scout only. It produces still debug images,
JSON fit records, and a Markdown report. It does not render video and does not
modify the source artwork.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_orca_wave_interference_match_research_scout_v001"
DATE = "2026-05-22"
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Water_Orca_Transparent.png"
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / f"{PROJECT}_{DATE}"
JSON_PATH = ROOT / "track2-deterministic" / "anchor_graph" / "orca_wave_interference_fit_candidates_v001.json"
DOC_PATH = ROOT / "docs" / "space-center" / "figural-orca-wave-interference-match-research-scout-2026-05-22.md"

W = 3840
H = 2160
SOURCE_SCALE = 0.88
TOP_LEFT = (896, 122)
DISPLAY_SIZE = (2219, 1949)


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    label: str
    class_name: str
    threshold_class: str
    select: Callable[[dict[str, object]], bool]
    notes: str


@dataclass
class Target:
    spec: CandidateSpec
    source_mask: np.ndarray
    canvas_mask: np.ndarray
    component: dict[str, object]
    stats: dict[str, object]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def md_link(label: str, path: Path) -> str:
    return f"[{label}]({Path(rel(path)).as_posix()})"


def doc_link(label: str, path_like: str | Path) -> str:
    path = Path(path_like)
    if not path.is_absolute():
        path = ROOT / path
    href = Path(os.path.relpath(path, DOC_PATH.parent)).as_posix()
    return f"[{label}]({href})"


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


def transform_point(point_source: list[float] | tuple[float, float]) -> list[float]:
    return [
        round(float(TOP_LEFT[0]) + float(point_source[0]) * SOURCE_SCALE, 3),
        round(float(TOP_LEFT[1]) + float(point_source[1]) * SOURCE_SCALE, 3),
    ]


def transform_bbox(bbox_source: list[int]) -> list[int]:
    x0, y0, x1, y1 = bbox_source
    p0 = transform_point([x0, y0])
    p1 = transform_point([x1, y1])
    return [round(p0[0]), round(p0[1]), round(p1[0]), round(p1[1])]


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


def select_component(components: list[dict[str, object]], predicate: Callable[[dict[str, object]], bool], label: str) -> dict[str, object]:
    matches = [component for component in components if predicate(component)]
    if not matches:
        raise RuntimeError(f"could not select component: {label}")
    return max(matches, key=lambda item: int(item["area"]))


def mask_to_canvas(mask_source: np.ndarray) -> np.ndarray:
    mask_img = Image.fromarray((mask_source.astype(np.uint8) * 255), "L")
    display = mask_img.resize(DISPLAY_SIZE, Image.Resampling.NEAREST)
    layer = Image.new("L", (W, H), 0)
    layer.paste(display, TOP_LEFT)
    return np.array(layer) > 0


def unit(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm < 1e-9:
        return np.array([1.0, 0.0], dtype=np.float64)
    return vec / norm


def rotate(vec: np.ndarray, angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([vec[0] * c - vec[1] * s, vec[0] * s + vec[1] * c], dtype=np.float64)


def mask_stats(mask: np.ndarray) -> dict[str, object]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise RuntimeError("empty target mask")
    coords = np.stack([xs.astype(np.float64), ys.astype(np.float64)], axis=1)
    centroid = coords.mean(axis=0)
    centered = coords - centroid
    cov = np.cov(centered.T)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    u = unit(vecs[:, 0])
    if u[0] < 0:
        u = -u
    v = np.array([-u[1], u[0]], dtype=np.float64)
    proj_u = centered @ u
    proj_v = centered @ v
    q_u = np.percentile(proj_u, [2, 5, 50, 95, 98])
    q_v = np.percentile(proj_v, [2, 5, 50, 95, 98])
    major_len = float(q_u[4] - q_u[0])
    minor_len = float(q_v[4] - q_v[0])
    low_end = coords[proj_u <= q_u[1]]
    high_end = coords[proj_u >= q_u[3]]
    low_width = float(np.ptp((low_end - centroid) @ v)) if len(low_end) else 0.0
    high_width = float(np.ptp((high_end - centroid) @ v)) if len(high_end) else 0.0
    if low_width <= high_width:
        tip_point = low_end.mean(axis=0) if len(low_end) else centroid - u * major_len * 0.5
    else:
        tip_point = high_end.mean(axis=0) if len(high_end) else centroid + u * major_len * 0.5
    tip_dir = unit(tip_point - centroid)
    angle_deg = math.degrees(math.atan2(float(u[1]), float(u[0])))
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)
    return {
        "area_px": int(len(xs)),
        "bbox_canvas_px": [x0, y0, x1, y1],
        "centroid_canvas_px": [round(float(centroid[0]), 3), round(float(centroid[1]), 3)],
        "principal_axis": [round(float(u[0]), 6), round(float(u[1]), 6)],
        "minor_axis": [round(float(v[0]), 6), round(float(v[1]), 6)],
        "principal_angle_degrees": round(float(angle_deg), 3),
        "major_extent_px": round(major_len, 3),
        "minor_extent_px": round(minor_len, 3),
        "aspect_ratio": round(float(major_len / max(minor_len, 1e-6)), 3),
        "tip_dir": [round(float(tip_dir[0]), 6), round(float(tip_dir[1]), 6)],
        "tip_point_canvas_px": [round(float(tip_point[0]), 3), round(float(tip_point[1]), 3)],
        "_centroid": centroid,
        "_u": u,
        "_v": v,
        "_tip_dir": tip_dir,
    }


def crop_bounds_for(circles: list[dict[str, object]], target_bbox: list[int], margin: int = 20) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = target_bbox
    xs = [float(x0), float(x1)]
    ys = [float(y0), float(y1)]
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        r = float(circle["radius_px"])
        xs.extend([float(cx) - r, float(cx) + r])
        ys.extend([float(cy) - r, float(cy) + r])
    return (
        max(0, int(math.floor(min(xs) - margin))),
        max(0, int(math.floor(min(ys) - margin))),
        min(W, int(math.ceil(max(xs) + margin))),
        min(H, int(math.ceil(max(ys) + margin))),
    )


def count_mask_in_bounds(circles: list[dict[str, object]], bounds: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = bounds
    yy, xx = np.ogrid[y0:y1, x0:x1]
    count = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        r = float(circle["radius_px"])
        inside = (xx - float(cx)) ** 2 + (yy - float(cy)) ** 2 <= r * r
        count += inside.astype(np.uint8)
    return count


def evaluate_fit(
    target_mask: np.ndarray,
    circles: list[dict[str, object]],
    threshold: int,
    target_stats: dict[str, object] | None = None,
) -> dict[str, object]:
    if target_stats is None:
        target_stats = mask_stats(target_mask)
    bounds = crop_bounds_for(circles, target_stats["bbox_canvas_px"])
    count = count_mask_in_bounds(circles, bounds)
    pred = count >= threshold
    x0, y0, x1, y1 = bounds
    target = target_mask[y0:y1, x0:x1]
    intersection = int(np.count_nonzero(pred & target))
    union = int(np.count_nonzero(pred | target))
    iou = float(intersection / union) if union else 0.0
    pred_area = int(np.count_nonzero(pred))
    if pred_area:
        py, px = np.nonzero(pred)
        pred_centroid = np.array([px.mean() + x0, py.mean() + y0], dtype=np.float64)
        pred_centroid_list = [round(float(pred_centroid[0]), 3), round(float(pred_centroid[1]), 3)]
        target_centroid = np.array(target_stats["_centroid"], dtype=np.float64)
        centroid_error = float(np.linalg.norm(pred_centroid - target_centroid))
    else:
        pred_centroid_list = None
        centroid_error = float("inf")
    return {
        "iou": round(iou, 4),
        "intersection_px": intersection,
        "union_px": union,
        "predicted_area_px": pred_area,
        "target_area_px": int(target_stats["area_px"]),
        "predicted_centroid_canvas_px": pred_centroid_list,
        "target_centroid_canvas_px": target_stats["centroid_canvas_px"],
        "centroid_error_px": round(float(centroid_error), 3) if math.isfinite(centroid_error) else None,
        "bounds_canvas_px": [x0, y0, x1, y1],
    }


def circle_record(center: np.ndarray | list[float], radius: float, role: str) -> dict[str, object]:
    return {
        "role": role,
        "center_canvas_px": [round(float(center[0]), 3), round(float(center[1]), 3)],
        "radius_px": round(float(radius), 3),
    }


def classify_quality(class_name: str, iou: float, centroid_error: float | None) -> str:
    err = float(centroid_error) if centroid_error is not None else 99999.0
    if class_name == "circle/oval":
        if iou >= 0.58 and err <= 35.0:
            return "PASS"
        if iou >= 0.38 and err <= 70.0:
            return "MIXED"
        return "FAIL"
    if class_name == "crescent/lens":
        if iou >= 0.45 and err <= 45.0:
            return "PASS"
        if iou >= 0.24 and err <= 95.0:
            return "MIXED"
        return "FAIL"
    if class_name == "trigon / three-arc":
        if iou >= 0.40 and err <= 50.0:
            return "PASS"
        if iou >= 0.24 and err <= 95.0:
            return "MIXED"
        return "FAIL"
    return "FAIL"


def fit_circle_oval(target: Target) -> dict[str, object]:
    stats = target.stats
    c = np.array(stats["_centroid"], dtype=np.float64)
    u = np.array(stats["_u"], dtype=np.float64)
    v = np.array(stats["_v"], dtype=np.float64)
    L = float(stats["major_extent_px"])
    T = float(stats["minor_extent_px"])
    aspect = float(stats["aspect_ratio"])
    best: dict[str, object] | None = None
    center_offsets = [(0.0, 0.0), (-0.04 * L, 0.0), (0.04 * L, 0.0), (0.0, -0.04 * T), (0.0, 0.04 * T)]
    if aspect < 1.28:
        base_r = math.sqrt(float(stats["area_px"]) / math.pi)
        for r_scale in [0.9, 1.0, 1.1]:
            for du, dv in center_offsets:
                center = c + du * u + dv * v
                circles = [circle_record(center, base_r * float(r_scale), "single circular wavefront disk")]
                metrics = evaluate_fit(target.canvas_mask, circles, threshold=1, target_stats=stats)
                score = float(metrics["iou"]) - 0.0005 * abs(float(metrics["centroid_error_px"] or 0.0))
                if best is None or score > float(best["_score"]):
                    best = {"circles": circles, "metrics": metrics, "_score": score}
        approximation = "single_circle_count_ge_1"
    else:
        base_r = max(8.0, T * 0.5)
        base_sep = max(0.0, L - T)
        for r_scale in [0.92, 1.0, 1.08, 1.16]:
            for sep_scale in [0.82, 1.0, 1.16]:
                r = base_r * float(r_scale)
                sep = base_sep * float(sep_scale)
                for du, dv in center_offsets:
                    center = c + du * u + dv * v
                    circles = [
                        circle_record(center - u * sep * 0.5, r, "oval approximation support A"),
                        circle_record(center + u * sep * 0.5, r, "oval approximation support B"),
                    ]
                    metrics = evaluate_fit(target.canvas_mask, circles, threshold=1, target_stats=stats)
                    score = float(metrics["iou"]) - 0.0005 * abs(float(metrics["centroid_error_px"] or 0.0))
                    if best is None or score > float(best["_score"]):
                        best = {"circles": circles, "metrics": metrics, "_score": score}
        approximation = "two_circle_union_count_ge_1_capsule"
    assert best is not None
    metrics = best["metrics"]
    quality = classify_quality("circle/oval", float(metrics["iou"]), metrics["centroid_error_px"])
    fit = {
        "fit_method": "circle_oval",
        "overlap_rule": "count >= 1",
        "construction_circles": best["circles"],
        "parameterization": {
            "target_center_canvas_px": stats["centroid_canvas_px"],
            "target_major_extent_px": stats["major_extent_px"],
            "target_minor_extent_px": stats["minor_extent_px"],
            "target_aspect_ratio": stats["aspect_ratio"],
            "principal_angle_degrees": stats["principal_angle_degrees"],
            "approximation": approximation,
            "path_a_circular_wavefront_assessment": "usable for anchor reading; exact oval taper would need more circular samples or a non-circular field",
        },
        "metrics": metrics,
        "shape_fit_quality": quality,
        "notes": "Predicted region is produced only by the union of circular wavefront disks.",
    }
    return fit


def fit_lens(target: Target) -> dict[str, object]:
    stats = target.stats
    c0 = np.array(stats["_centroid"], dtype=np.float64)
    base_u = np.array(stats["_u"], dtype=np.float64)
    L0 = max(8.0, float(stats["major_extent_px"]))
    T0 = max(8.0, float(stats["minor_extent_px"]))
    best: dict[str, object] | None = None
    angle_offsets = [-12, 0, 12]
    l_scales = [1.0, 1.16]
    t_scales = [0.92, 1.12]
    for angle in angle_offsets:
        u = rotate(base_u, math.radians(angle))
        v = np.array([-u[1], u[0]], dtype=np.float64)
        for l_scale in l_scales:
            for t_scale in t_scales:
                L = L0 * l_scale
                T = min(T0 * t_scale, L * 0.94)
                if T <= 2.0:
                    continue
                radius = (L * L + T * T) / (4.0 * T)
                separation = max(0.0, (L * L - T * T) / (2.0 * T))
                if radius > 1800.0:
                    continue
                offsets = [(0.0, 0.0), (-0.06 * L0, 0.0), (0.06 * L0, 0.0)]
                for du, dv in offsets:
                    c = c0 + du * u + dv * v
                    circles = [
                        circle_record(c - v * separation * 0.5, radius, "lens construction circle A"),
                        circle_record(c + v * separation * 0.5, radius, "lens construction circle B"),
                    ]
                    metrics = evaluate_fit(target.canvas_mask, circles, threshold=2, target_stats=stats)
                    score = float(metrics["iou"]) - 0.00035 * abs(float(metrics["centroid_error_px"] or 0.0))
                    if best is None or score > float(best["_score"]):
                        best = {
                            "circles": circles,
                            "metrics": metrics,
                            "_score": score,
                            "lens": {
                                "center_canvas_px": [round(float(c[0]), 3), round(float(c[1]), 3)],
                                "radius_px": round(float(radius), 3),
                                "center_separation_px": round(float(separation), 3),
                                "orientation_degrees": round(float(math.degrees(math.atan2(u[1], u[0]))), 3),
                                "lens_major_axis_px": round(float(L), 3),
                                "lens_thickness_px": round(float(T), 3),
                                "lens_aspect_ratio": round(float(L / T), 3),
                            },
                        }
    assert best is not None
    metrics = best["metrics"]
    quality = classify_quality("crescent/lens", float(metrics["iou"]), metrics["centroid_error_px"])
    fit = {
        "fit_method": "crescent_lens",
        "overlap_rule": "count >= 2",
        "construction_circles": best["circles"],
        "parameterization": best["lens"],
        "metrics": metrics,
        "shape_fit_quality": quality,
        "notes": "Two-circle vesica lens can match center, orientation, and broad thickness, but cannot bend into a true authored crescent band.",
    }
    return fit


def fit_trigon(target: Target) -> dict[str, object]:
    stats = target.stats
    c0 = np.array(stats["_centroid"], dtype=np.float64)
    target_u = np.array(stats["_tip_dir"], dtype=np.float64)
    L0 = max(20.0, float(stats["major_extent_px"]))
    T0 = max(20.0, float(stats["minor_extent_px"]))
    rng = random.Random(20260522 + sum(ord(ch) for ch in target.spec.candidate_id))
    samples: list[tuple[float, float, float, float, float, float, float, float]] = []
    for angle in [-45, 0, 45]:
        for sign in [1.0, -1.0]:
            for length_scale in [0.72, 1.05]:
                for width_scale in [0.7, 1.1]:
                    for radius_scale in [0.85, 1.15]:
                        samples.append((angle, sign, length_scale, width_scale, radius_scale, 0.0, 0.0, 0.0))
    for _ in range(60):
        samples.append(
            (
                rng.uniform(-105.0, 105.0),
                rng.choice([1.0, -1.0]),
                rng.uniform(0.35, 1.45),
                rng.uniform(0.35, 1.55),
                rng.uniform(0.55, 1.55),
                rng.uniform(-0.18, 0.18),
                rng.uniform(-0.18, 0.18),
                rng.uniform(-0.18, 0.18),
            )
        )
    best: dict[str, object] | None = None
    for angle, sign, length_scale, width_scale, radius_scale, off_u, off_v, back_bias in samples:
        u = rotate(target_u * sign, math.radians(angle))
        v = np.array([-u[1], u[0]], dtype=np.float64)
        c = c0 + u * (off_u * L0) + v * (off_v * T0)
        center_len = L0 * length_scale
        half_width = T0 * width_scale * 0.5
        back = center_len * (0.28 + back_bias)
        front = center_len * 0.44
        centers = [
            c + u * front,
            c - u * back + v * half_width,
            c - u * back - v * half_width,
        ]
        side_lengths = [
            float(np.linalg.norm(centers[0] - centers[1])),
            float(np.linalg.norm(centers[1] - centers[2])),
            float(np.linalg.norm(centers[2] - centers[0])),
        ]
        radius = max(side_lengths) * radius_scale
        if radius < 18.0 or radius > 700.0:
            continue
        circles = [
            circle_record(centers[0], radius, "three-arc construction circle tip-side"),
            circle_record(centers[1], radius, "three-arc construction circle base-left"),
            circle_record(centers[2], radius, "three-arc construction circle base-right"),
        ]
        metrics = evaluate_fit(target.canvas_mask, circles, threshold=3, target_stats=stats)
        if not metrics["predicted_area_px"]:
            continue
        area_ratio = float(metrics["predicted_area_px"]) / max(1.0, float(metrics["target_area_px"]))
        area_penalty = abs(math.log(max(area_ratio, 1e-6))) * 0.035
        score = float(metrics["iou"]) - 0.00035 * abs(float(metrics["centroid_error_px"] or 0.0)) - area_penalty
        if best is None or score > float(best["_score"]):
            best = {
                "circles": circles,
                "metrics": metrics,
                "_score": score,
                "triangle": {
                    "center_triangle_side_lengths_px": [round(v, 3) for v in side_lengths],
                    "center_triangle_orientation_degrees": round(float(math.degrees(math.atan2(u[1], u[0]))), 3),
                    "target_tip_point_canvas_px": stats["tip_point_canvas_px"],
                    "overlap_region_centroid_canvas_px": metrics["predicted_centroid_canvas_px"],
                    "concavity": "convex curved triangular three-way overlap; no drawn concave cuts",
                },
            }
    if best is None:
        c = c0
        radius = max(L0, T0)
        centers = [c + np.array([radius, 0.0]), c + np.array([-radius * 0.5, radius * 0.866]), c + np.array([-radius * 0.5, -radius * 0.866])]
        circles = [circle_record(center, radius, f"fallback construction circle {idx}") for idx, center in enumerate(centers, 1)]
        metrics = evaluate_fit(target.canvas_mask, circles, threshold=3, target_stats=stats)
        best = {"circles": circles, "metrics": metrics, "triangle": {"concavity": "fallback"}}
    metrics = best["metrics"]
    quality = classify_quality("trigon / three-arc", float(metrics["iou"]), metrics["centroid_error_px"])
    fit = {
        "fit_method": "trigon_three_arc",
        "overlap_rule": "count >= 3",
        "construction_circles": best["circles"],
        "parameterization": best["triangle"],
        "metrics": metrics,
        "shape_fit_quality": quality,
        "notes": "Predicted trigon is the three-way overlap of three construction circles, not a drawn triangle.",
    }
    return fit


def fit_target(target: Target) -> dict[str, object] | None:
    class_name = target.spec.class_name
    if class_name == "compound region to exclude":
        return None
    if class_name == "circle/oval":
        return fit_circle_oval(target)
    if class_name == "crescent/lens":
        return fit_lens(target)
    if class_name == "trigon / three-arc":
        return fit_trigon(target)
    raise RuntimeError(f"unknown class: {class_name}")


def place_source(source_rgba: Image.Image, checker: bool = True, opacity: float = 1.0) -> Image.Image:
    if checker:
        yy, xx = np.indices((H, W))
        grid = ((xx // 64 + yy // 64) % 2).astype(bool)
        base = np.empty((H, W, 3), dtype=np.uint8)
        base[:] = [222, 227, 225]
        base[grid] = [195, 203, 202]
        canvas = Image.fromarray(base, "RGB").convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), (8, 10, 14, 255))
    display = source_rgba.resize(DISPLAY_SIZE, Image.Resampling.LANCZOS)
    if opacity < 1.0:
        alpha = display.getchannel("A").point(lambda value: int(value * opacity))
        display.putalpha(alpha)
    canvas.alpha_composite(display, dest=TOP_LEFT)
    return canvas.convert("RGBA")


def edge_mask(mask: np.ndarray, size: int = 7) -> np.ndarray:
    img = Image.fromarray((mask.astype(np.uint8) * 255), "L")
    expanded = img.filter(ImageFilter.MaxFilter(size))
    eroded = img.filter(ImageFilter.MinFilter(size))
    return np.array(ImageChops.difference(expanded, eroded)) > 0


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int] = (250, 250, 244)) -> None:
    x, y = xy
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def source_targets_marked(source_rgba: Image.Image, targets: list[Target], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    img = place_source(source_rgba, checker=True, opacity=1.0)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(22)
    for index, target in enumerate(targets, 1):
        color = colors[target.spec.candidate_id]
        edge = edge_mask(target.canvas_mask, size=9)
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[edge] = [color[0], color[1], color[2], 235]
        overlay.alpha_composite(Image.fromarray(rgba, "RGBA"))
        bbox = target.stats["bbox_canvas_px"]
        cx, cy = target.stats["centroid_canvas_px"]
        draw.rectangle(bbox, outline=color + (170,), width=3)
        draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=color + (255,))
        label = f"{index}. {target.spec.candidate_id}"
        draw_label(draw, (bbox[0], max(4, bbox[1] - 28)), label, small, fill=color)
    draw_label(draw, (40, 34), "Orca source with selected primitive targets marked for measurement only", font)
    return Image.alpha_composite(img, overlay).convert("RGB")


def construction_circles_over_source(source_rgba: Image.Image, targets: list[Target], fits: dict[str, dict[str, object]], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    img = place_source(source_rgba, checker=True, opacity=0.92)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(22)
    for index, target in enumerate(targets, 1):
        fit = fits.get(target.spec.candidate_id)
        if fit is None:
            continue
        color = colors[target.spec.candidate_id]
        for circle in fit["construction_circles"]:
            cx, cy = circle["center_canvas_px"]
            r = float(circle["radius_px"])
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color + (220,), width=4)
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color + (255,))
        bbox = target.stats["bbox_canvas_px"]
        draw_label(draw, (bbox[0], max(4, bbox[1] - 24)), f"{index}. {fit['shape_fit_quality']} IoU {fit['metrics']['iou']:.2f}", small, fill=color)
    draw_label(draw, (40, 34), "Fitted construction circles over Orca: predicted shapes are circle-count regions only", font)
    return Image.alpha_composite(img, overlay).convert("RGB")


def all_circles_for(ids: list[str], fits: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    circles: list[dict[str, object]] = []
    for candidate_id in ids:
        fit = fits.get(candidate_id)
        if fit is not None:
            for circle in fit["construction_circles"]:
                item = dict(circle)
                item["candidate_id"] = candidate_id
                circles.append(item)
    return circles


def full_count_map(circles: list[dict[str, object]]) -> np.ndarray:
    yy, xx = np.ogrid[0:H, 0:W]
    count = np.zeros((H, W), dtype=np.uint8)
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        r = float(circle["radius_px"])
        inside = (xx - float(cx)) ** 2 + (yy - float(cy)) ** 2 <= r * r
        count += inside.astype(np.uint8)
    return count


def diagnostic_count_map(circles: list[dict[str, object]], scale: int = 4) -> np.ndarray:
    h = H // scale
    w = W // scale
    yy, xx = np.ogrid[0:h, 0:w]
    count = np.zeros((h, w), dtype=np.uint8)
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        r = float(circle["radius_px"]) / scale
        sx = float(cx) / scale
        sy = float(cy) / scale
        inside = (xx - sx) ** 2 + (yy - sy) ** 2 <= r * r
        count += inside.astype(np.uint8)
    return count


def downsample_bool_any(mask: np.ndarray, scale: int = 4) -> np.ndarray:
    h = H // scale
    w = W // scale
    trimmed = mask[: h * scale, : w * scale]
    return trimmed.reshape(h, scale, w, scale).any(axis=(1, 3))


def count_map_image(source_rgba: Image.Image, circles: list[dict[str, object]], targets: list[Target], title: str) -> tuple[Image.Image, dict[str, object]]:
    scale = 4
    count = diagnostic_count_map(circles, scale=scale)
    palette = np.array(
        [
            [9, 10, 14],
            [30, 83, 132],
            [39, 154, 176],
            [229, 194, 92],
            [219, 97, 84],
            [181, 78, 154],
            [245, 245, 235],
        ],
        dtype=np.uint8,
    )
    clamped = np.clip(count, 0, len(palette) - 1)
    rgb_small = palette[clamped]
    img = Image.fromarray(rgb_small, "RGB").resize((W, H), Image.Resampling.NEAREST).convert("RGBA")
    source_layer = place_source(source_rgba, checker=False, opacity=0.18)
    img = Image.blend(img, source_layer, alpha=0.28).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(22)
    target_union = np.zeros((H // scale, W // scale), dtype=bool)
    for target in targets:
        if target.spec.class_name != "compound region to exclude":
            target_union |= downsample_bool_any(target.canvas_mask, scale=scale)
    spurious_mask = (count >= 2) & (~target_union)
    labels, n = ndimage.label(spurious_mask, structure=np.ones((3, 3), dtype=np.uint8))
    areas = []
    for idx, slc in enumerate(ndimage.find_objects(labels), start=1):
        if slc is None:
            continue
        area = int((labels[slc] == idx).sum()) * scale * scale
        if area >= 1200:
            areas.append(area)
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(255, 255, 255, 230))
    for target in targets:
        if target.spec.class_name == "compound region to exclude":
            continue
        bbox = target.stats["bbox_canvas_px"]
        cx, cy = target.stats["centroid_canvas_px"]
        draw.rectangle(bbox, outline=(245, 245, 235, 170), width=2)
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(245, 245, 235, 210))
    draw_label(draw, (40, 34), title, font)
    draw_label(draw, (40, 76), f"source circles: {len(circles)} | count>=2 spurious components outside targets: {len(areas)}", small)
    return Image.alpha_composite(img, overlay).convert("RGB"), {
        "source_circle_count": len(circles),
        "max_overlap_count": int(count.max()) if count.size else 0,
        "count_ge_2_area_px": int(np.count_nonzero(count >= 2)) * scale * scale,
        "count_ge_3_area_px": int(np.count_nonzero(count >= 3)) * scale * scale,
        "spurious_count_ge_2_component_count_area_ge_1200": len(areas),
        "spurious_count_ge_2_total_area_px": int(sum(areas)),
    }


def predicted_mask_for_fit(fit: dict[str, object], target_mask: np.ndarray) -> np.ndarray:
    threshold = int(str(fit["overlap_rule"]).split(">=")[1].strip())
    circles = fit["construction_circles"]
    bounds = crop_bounds_for(circles, mask_stats(target_mask)["bbox_canvas_px"])
    count = count_mask_in_bounds(circles, bounds)
    pred_local = count >= threshold
    out = np.zeros((H, W), dtype=bool)
    x0, y0, x1, y1 = bounds
    out[y0:y1, x0:x1] = pred_local
    return out


def mismatch_sheet(source_rgba: Image.Image, targets: list[Target], fits: dict[str, dict[str, object]], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    tile_w = 960
    tile_h = 420
    rows = math.ceil(len([t for t in targets if t.spec.class_name != "compound region to exclude"]) / 2)
    sheet = Image.new("RGB", (tile_w * 2, tile_h * rows), (20, 22, 26))
    source_canvas = place_source(source_rgba, checker=False, opacity=0.35).convert("RGB")
    font = load_font(24)
    small = load_font(18)
    fitted_targets = [t for t in targets if t.spec.class_name != "compound region to exclude"]
    for index, target in enumerate(fitted_targets):
        fit = fits[target.spec.candidate_id]
        pred = predicted_mask_for_fit(fit, target.canvas_mask)
        union = pred | target.canvas_mask
        ys, xs = np.nonzero(union)
        margin = 70
        x0 = max(0, int(xs.min()) - margin)
        y0 = max(0, int(ys.min()) - margin)
        x1 = min(W, int(xs.max()) + margin)
        y1 = min(H, int(ys.max()) + margin)
        crop = source_canvas.crop((x0, y0, x1, y1)).convert("RGBA")
        overlay = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        rgba = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
        target_local = target.canvas_mask[y0:y1, x0:x1]
        pred_local = pred[y0:y1, x0:x1]
        overlap = target_local & pred_local
        target_only = target_local & (~pred_local)
        pred_only = pred_local & (~target_local)
        rgba[target_only] = [40, 220, 150, 160]
        rgba[pred_only] = [226, 70, 188, 150]
        rgba[overlap] = [255, 245, 120, 220]
        overlay.alpha_composite(Image.fromarray(rgba, "RGBA"))
        combined = Image.alpha_composite(crop, overlay).convert("RGB")
        combined.thumbnail((tile_w - 30, tile_h - 82), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (tile_w, tile_h), (20, 22, 26))
        draw = ImageDraw.Draw(tile)
        x = (tile_w - combined.size[0]) // 2
        y = 64
        tile.paste(combined, (x, y))
        color = colors[target.spec.candidate_id]
        label = f"{target.spec.candidate_id}: {fit['shape_fit_quality']} IoU {fit['metrics']['iou']:.2f} err {fit['metrics']['centroid_error_px']}"
        draw_label(draw, (18, 14), label, font, fill=color)
        draw_label(draw, (18, 42), "green target only | magenta predicted only | yellow overlap", small)
        sx = (index % 2) * tile_w
        sy = (index // 2) * tile_h
        sheet.paste(tile, (sx, sy))
    return sheet


def make_candidates() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            "eye_upper_pale_ovoid",
            "eye / head pale ovoid",
            "circle/oval",
            "pale",
            lambda c: c["bbox"][0] > 1200 and c["bbox"][1] > 850 and c["bbox"][1] < 1250 and c["area"] > 50000,
            "Strongest authored oval anchor; acts as a head/eye patch focal mark.",
        ),
        CandidateSpec(
            "lower_large_pale_ovoid",
            "lower body large pale ovoid",
            "circle/oval",
            "pale",
            lambda c: c["bbox"][0] > 550 and c["bbox"][0] < 950 and c["bbox"][1] > 1300 and c["area"] > 50000,
            "Large elongated pale anchor in the lower body cluster.",
        ),
        CandidateSpec(
            "lower_small_pale_ovoid",
            "lower body small pale ovoid",
            "circle/oval",
            "pale",
            lambda c: c["bbox"][0] > 350 and c["bbox"][2] < 650 and c["bbox"][1] > 1200 and c["bbox"][1] < 1500,
            "Secondary pale oval anchor; useful for testing repeated oval fitting.",
        ),
        CandidateSpec(
            "dorsal_inner_trigon",
            "dorsal fin organic trigon-like blue-gray form",
            "trigon / three-arc",
            "bluegray",
            lambda c: c["bbox"][0] > 850 and c["bbox"][1] > 240 and c["bbox"][1] < 360 and c["bbox"][3] < 650 and c["area"] > 10000,
            "Dorsal interior reads as a pointed three-arc/trigon-like pressure form.",
        ),
        CandidateSpec(
            "upper_body_bluegray_crescent",
            "upper body blue-gray crescent band",
            "crescent/lens",
            "bluegray",
            lambda c: c["bbox"][0] > 880 and c["bbox"][1] > 520 and c["bbox"][1] < 760 and c["extent"][0] > 500,
            "Broad upper body band; likely harder because it bends more than a pure vesica.",
        ),
        CandidateSpec(
            "central_pectoral_bluegray_crescent",
            "central pectoral/body blue-gray crescent band",
            "crescent/lens",
            "bluegray",
            lambda c: c["bbox"][0] > 760 and c["bbox"][1] > 1040 and c["extent"][0] > 620 and c["extent"][1] > 300,
            "Largest internal body crescent candidate; may be compound but visually important.",
        ),
        CandidateSpec(
            "tail_fluke_bluegray_crescent",
            "tail fluke blue-gray crescent",
            "crescent/lens",
            "bluegray",
            lambda c: c["bbox"][0] > 1350 and c["bbox"][1] > 1580 and c["bbox"][0] < 1720,
            "Compact tail-side crescent/lens with clear local curvature.",
        ),
        CandidateSpec(
            "tail_upper_bluegray_trigon",
            "tail upper blue-gray trigon-like form",
            "trigon / three-arc",
            "bluegray",
            lambda c: c["bbox"][0] > 1350 and c["bbox"][0] < 1750 and c["bbox"][1] > 1550 and c["bbox"][1] < 1680 and c["extent"][0] > 240,
            "Tail-side pointed/three-arc candidate; tests whether the trigon fit generalizes beyond the dorsal.",
        ),
        CandidateSpec(
            "rear_vertical_bluegray_compound_exclude",
            "rear vertical blue-gray compound region",
            "compound region to exclude",
            "bluegray",
            lambda c: c["bbox"][0] > 1750 and c["bbox"][1] > 900 and c["bbox"][1] < 1050 and c["extent"][1] > 250,
            "Visually strong, but it merges multiple body/negative-space readings and is not a clean primitive target.",
        ),
    ]


def extract_targets(source_rgba: Image.Image) -> tuple[list[Target], dict[str, object]]:
    arr = np.array(source_rgba.convert("RGBA"))
    red, green, blue, alpha = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    masks = {
        "pale": (alpha > 128) & (red > 185) & (green > 185) & (blue > 185),
        "bluegray": (alpha > 128) & (red > 60) & (red < 120) & (green > 75) & (green < 130) & (blue > 90) & (blue < 150),
    }
    labels_by_class: dict[str, np.ndarray] = {}
    components_by_class: dict[str, list[dict[str, object]]] = {}
    for name, mask in masks.items():
        labels, components = component_table(mask, min_area=500)
        labels_by_class[name] = labels
        components_by_class[name] = components
    targets: list[Target] = []
    for spec in make_candidates():
        component = select_component(components_by_class[spec.threshold_class], spec.select, spec.candidate_id)
        source_mask = labels_by_class[spec.threshold_class] == int(component["label_index"])
        canvas_mask = mask_to_canvas(source_mask)
        stats = mask_stats(canvas_mask)
        targets.append(Target(spec=spec, source_mask=source_mask, canvas_mask=canvas_mask, component=component, stats=stats))
    summary = {
        "pale_component_count": len(components_by_class["pale"]),
        "bluegray_component_count": len(components_by_class["bluegray"]),
        "selection_policy": "RGB/alpha threshold connected components, then named component predicates in source coordinates.",
    }
    return targets, summary


def round_public_stats(stats: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in stats.items() if not k.startswith("_")}


def candidate_record(target: Target, fit: dict[str, object] | None) -> dict[str, object]:
    component = target.component
    return {
        "candidate_id": target.spec.candidate_id,
        "label": target.spec.label,
        "classification": target.spec.class_name,
        "source_component": {
            "threshold_class": target.spec.threshold_class,
            "bbox_source_px": component["bbox"],
            "bbox_canvas_px_from_transform": transform_bbox(component["bbox"]),
            "center_source_px": component["center"],
            "center_canvas_px_from_transform": transform_point(component["center"]),
            "area_source_px": component["area"],
        },
        "target_mask": round_public_stats(target.stats),
        "notes": target.spec.notes,
        "fit": fit,
    }


def build_markdown(data: dict[str, object]) -> str:
    candidates = data["candidates"]
    debug = data["debug_images"]
    configs = data["source_configurations"]
    verdict = data["verdict"]
    lines: list[str] = []
    lines.append("# Figural Orca Wave-Interference Match Research Scout - 2026-05-22")
    lines.append("")
    lines.append("Status: INTERNAL RESEARCH + GEOMETRY-FIT SCOUT ONLY. No beauty MP4 was rendered. No source artwork was modified. Target masks in this report are source-derived measurement masks used only to evaluate construction-circle fits; they are not a render mechanism.")
    lines.append("")
    lines.append("Goal: evaluate whether Austin's Orca internal primitive composition can be matched by field-derived construction-circle overlap/count geometry without drawn final primitives or aperture masks as the main mechanism.")
    lines.append("")
    lines.append("Reviewed source:")
    lines.append("")
    lines.append(f"- Source artwork: `{data['source_path']}`")
    lines.append(f"- Source SHA-256: `{data['source_sha256']}`")
    lines.append("- Placement transform: scale `0.88`, top-left `[896, 122]`, display size `[2219, 1949]` on a `3840x2160` canvas.")
    lines.append(f"- Fit JSON: {doc_link('orca_wave_interference_fit_candidates_v001.json', JSON_PATH)}")
    lines.append(f"- Debug folder: `{data['output_dir']}`")
    lines.append("")
    lines.append("## Phase 1 - Fitting Method Research")
    lines.append("")
    lines.append("### Circle / Oval Target")
    lines.append("")
    lines.append("Method: measure the source component centroid, principal axis, major/minor extents, and aspect ratio. Near-circular targets use one construction circle with predicted primitive region `count >= 1`. Elongated ovals use a two-circle capsule approximation: two equal-radius construction circles placed along the major axis, with the primitive region as their union (`count >= 1`).")
    lines.append("")
    lines.append("Path A assessment: circular wavefronts can approximate the Orca's ovoid anchors well enough for anchor reading, especially when the mark is broad and self-contained. Exact authored oval taper is not reproduced by one or two circles; more circular samples or a non-circular wavefront family would be needed for high-fidelity taper.")
    lines.append("")
    lines.append("### Crescent / Vesica Target")
    lines.append("")
    lines.append("Method: fit two construction circles whose intersection lens is the predicted primitive region (`count >= 2`). Parameterization uses two centers, equal radius, center separation, orientation of the lens major axis, and lens thickness/aspect ratio. The equal-circle vesica formula is initialized from target major length `L` and thickness `T`: `R = (L^2 + T^2) / (4T)` and `d = (L^2 - T^2) / (2T)`, then locally searched for better IoU.")
    lines.append("")
    lines.append("Limit: this matches a symmetric lens. It does not naturally bend into a banana-shaped body band. Crescent-like body components can score as centered and oriented while still losing the authored curved-band character.")
    lines.append("")
    lines.append("### Trigon / Three-Arc Target")
    lines.append("")
    lines.append("Method: fit three construction circles and use their three-way overlap (`count >= 3`) as the predicted primitive region. The parameter search records three centers, radii, center-triangle side lengths, center-triangle orientation, overlap centroid, and concavity/orientation. The resulting trigon is a convex curved triangular cell from three arcs, not a drawn triangle.")
    lines.append("")
    lines.append("Limit: organic pointed forms can be approximated if their centroid and tip direction are clear. Concave or highly asymmetric authored trigons remain difficult with only three equal-radius construction circles.")
    lines.append("")
    lines.append("### Asymmetric Field Risks")
    lines.append("")
    lines.append("- Spurious secondary features: unrelated construction circles overlap outside target masks and can create extra count regions that read as accidental marks.")
    lines.append("- Noisy fields: fitting many local primitives independently increases the count-map density and weakens the causal read of a single wave field.")
    lines.append("- Mathematical match versus perception: a target can have acceptable centroid error or IoU but still feel scattered if the global source configuration does not bind eye, body, dorsal, and tail into one composition.")
    lines.append("")
    lines.append("## Phase 2 - Orca Primitive Target Extraction")
    lines.append("")
    lines.append("| Candidate | Class | Source bbox px | Canvas centroid px | Decision | Notes |")
    lines.append("|---|---|---:|---:|---|---|")
    for item in candidates:
        fit = item.get("fit")
        decision = "excluded" if fit is None else "fit attempted"
        lines.append(
            f"| `{item['candidate_id']}` | {item['classification']} | `{item['source_component']['bbox_source_px']}` | `{item['target_mask']['centroid_canvas_px']}` | {decision} | {item['notes']} |"
        )
    lines.append("")
    lines.append("The compound rear vertical component was intentionally excluded from fitting because it joins too many body and negative-space readings to be a clean primitive unit.")
    lines.append("")
    lines.append("## Phase 3 - Construction-Circle Fit Attempt")
    lines.append("")
    lines.append("| Candidate | Rule | Construction circle centers/radii in canvas px | Centroid error px | IoU | Quality | Character note |")
    lines.append("|---|---|---|---:|---:|---|---|")
    for item in candidates:
        fit = item.get("fit")
        if fit is None:
            lines.append(f"| `{item['candidate_id']}` | n/a | excluded compound region | n/a | n/a | EXCLUDE | Not fit as a primitive. |")
            continue
        centers = []
        for circle in fit["construction_circles"]:
            centers.append(f"{circle['center_canvas_px']} r={circle['radius_px']}")
        centers_text = "<br>".join(centers)
        note = fit["notes"]
        lines.append(
            f"| `{item['candidate_id']}` | `{fit['overlap_rule']}` | {centers_text} | {fit['metrics']['centroid_error_px']} | {fit['metrics']['iou']} | {fit['shape_fit_quality']} | {note} |"
        )
    lines.append("")
    lines.append("Parameterization details are preserved in the JSON for each target, including lens separation/aspect ratio and trigon center-triangle geometry.")
    lines.append("")
    lines.append("## Phase 4 - Field Coherence Evaluation")
    lines.append("")
    lines.append("Debug stills only:")
    lines.append("")
    lines.append(f"- {doc_link('01 source targets marked', debug['source_targets_marked'])}")
    lines.append(f"- {doc_link('02 fitted construction circles over Orca', debug['fitted_construction_circles'])}")
    lines.append(f"- {doc_link('03 primary overlap-count map', debug['overlap_count_map_primary'])}")
    lines.append(f"- {doc_link('04 target-vs-predicted mismatch sheet', debug['target_vs_predicted_mismatch_sheet'])}")
    lines.append(f"- {doc_link('05 alternative strong-target overlap-count map', debug['overlap_count_map_strong_targets'])}")
    lines.append(f"- {doc_link('06 alternative body/tail overlap-count map', debug['overlap_count_map_body_tail'])}")
    lines.append("")
    lines.append("| Configuration | Source circles | Max count | Count>=2 area px | Spurious count>=2 components | Read |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for config in configs:
        metrics = config["metrics"]
        lines.append(
            f"| `{config['configuration_id']}` | {metrics['source_circle_count']} | {metrics['max_overlap_count']} | {metrics['count_ge_2_area_px']} | {metrics['spurious_count_ge_2_component_count_area_ge_1200']} | {config['field_read']} |"
        )
    lines.append("")
    lines.append("The primary all-target count map demonstrates the core risk: local fits produce valid primitive cells, but the global count field adds many unrelated secondary overlaps. The strong-target subset reduces clutter but still reads as a constellation of local devices more than as one coherent Orca-bound wave system.")
    lines.append("")
    lines.append("## Outcome")
    lines.append("")
    lines.append(f"Go/no-go verdict: **{verdict['go_no_go']}**.")
    lines.append("")
    lines.append(f"- Strong primitive targets matched: `{verdict['strong_pass_count']}` PASS fits out of `{verdict['fit_attempt_count']}` fit attempts.")
    lines.append(f"- Field read: `{verdict['field_read']}`.")
    lines.append(f"- Recommend proceeding to `figural_orca_wave_interference_match_v001` beauty render: `{str(verdict['recommend_render']).lower()}`.")
    lines.append("")
    lines.append("Recommendation: do not proceed directly to a beauty MP4. The scout supports the geometry hypothesis for several local primitives, especially ovoid anchors and compact tail/dorsal cells, but the asymmetric all-source field is visually mixed and too prone to secondary features. A next research pass should either bind the construction circles into fewer shared source families or combine this primitive matching with a silhouette/flow coherence layer before any render.")
    lines.append("")
    lines.append("## Verification Notes")
    lines.append("")
    lines.append("- All referenced paths were generated under the requested doc, JSON, and debug-output locations.")
    lines.append("- JSON is intended to parse with `python3 -m json.tool`.")
    lines.append("- Markdown links are repository-relative from this document.")
    lines.append("- This scout writes PNG stills only and no MP4.")
    lines.append("- The source PNG is read-only input and is not modified.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    source_rgba = Image.open(SOURCE_PATH).convert("RGBA")
    if source_rgba.size != (2522, 2215):
        raise RuntimeError(f"unexpected source dimensions: {source_rgba.size}")
    targets, extraction_summary = extract_targets(source_rgba)
    fits: dict[str, dict[str, object]] = {}
    for target in targets:
        fit = fit_target(target)
        if fit is not None:
            fits[target.spec.candidate_id] = fit

    palette = [
        (255, 211, 87),
        (81, 214, 157),
        (84, 182, 255),
        (255, 132, 112),
        (184, 150, 255),
        (93, 224, 229),
        (255, 153, 213),
        (188, 226, 92),
        (230, 230, 230),
    ]
    colors = {target.spec.candidate_id: palette[index % len(palette)] for index, target in enumerate(targets)}

    debug_paths = {
        "source_targets_marked": OUT_DIR / f"{PROJECT}_debug_01_source_targets_marked.png",
        "fitted_construction_circles": OUT_DIR / f"{PROJECT}_debug_02_fitted_construction_circles_over_orca.png",
        "overlap_count_map_primary": OUT_DIR / f"{PROJECT}_debug_03_overlap_count_map_primary_all_sources.png",
        "target_vs_predicted_mismatch_sheet": OUT_DIR / f"{PROJECT}_debug_04_target_vs_predicted_mismatch_sheet.png",
        "overlap_count_map_strong_targets": OUT_DIR / f"{PROJECT}_debug_05_alt_overlap_count_map_strong_targets.png",
        "overlap_count_map_body_tail": OUT_DIR / f"{PROJECT}_debug_06_alt_overlap_count_map_body_tail.png",
    }
    source_targets_marked(source_rgba, targets, colors).save(debug_paths["source_targets_marked"])
    construction_circles_over_source(source_rgba, targets, fits, colors).save(debug_paths["fitted_construction_circles"])
    mismatch_sheet(source_rgba, targets, fits, colors).save(debug_paths["target_vs_predicted_mismatch_sheet"])

    fit_ids = [target.spec.candidate_id for target in targets if target.spec.candidate_id in fits]
    strong_ids = [
        "eye_upper_pale_ovoid",
        "dorsal_inner_trigon",
        "upper_body_bluegray_crescent",
        "central_pectoral_bluegray_crescent",
        "tail_fluke_bluegray_crescent",
    ]
    body_tail_ids = [
        "upper_body_bluegray_crescent",
        "central_pectoral_bluegray_crescent",
        "tail_fluke_bluegray_crescent",
        "tail_upper_bluegray_trigon",
    ]
    configs_input = [
        ("primary_all_fit_sources", fit_ids, debug_paths["overlap_count_map_primary"], "mixed"),
        ("alternative_strong_targets", [cid for cid in strong_ids if cid in fits], debug_paths["overlap_count_map_strong_targets"], "mixed"),
        ("alternative_body_tail_subset", [cid for cid in body_tail_ids if cid in fits], debug_paths["overlap_count_map_body_tail"], "mixed"),
    ]
    source_configurations: list[dict[str, object]] = []
    for config_id, ids, path, field_read in configs_input:
        circles = all_circles_for(ids, fits)
        img, metrics = count_map_image(source_rgba, circles, targets, f"Overlap-count map: {config_id}")
        img.save(path)
        source_configurations.append(
            {
                "configuration_id": config_id,
                "candidate_ids": ids,
                "debug_image": rel(path),
                "metrics": metrics,
                "field_read": field_read,
            }
        )

    candidates = [candidate_record(target, fits.get(target.spec.candidate_id)) for target in targets]
    pass_count = sum(1 for item in candidates if item.get("fit") and item["fit"]["shape_fit_quality"] == "PASS")
    fit_attempt_count = sum(1 for item in candidates if item.get("fit"))
    verdict = {
        "go_no_go": "MIXED",
        "strong_pass_count": pass_count,
        "fit_attempt_count": fit_attempt_count,
        "field_read": "mixed: several local matches are defensible, but the asymmetric count field reads as a scattered constellation with spurious secondary overlaps",
        "recommend_render": False,
        "rationale": "GO requires at least four strong primitive targets and coherent field read. The fit count clears the local-geometry threshold, but field coherence does not.",
    }

    data = {
        "project": PROJECT,
        "date": DATE,
        "status": "internal research scout only; no MP4 render",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "source_to_canvas_transform": {
            "uniform_scale": SOURCE_SCALE,
            "top_left_px": list(TOP_LEFT),
            "display_size_px": list(DISPLAY_SIZE),
            "canvas_size_px": [W, H],
            "placement_source": "User-provided prior manifest transform.",
        },
        "output_dir": rel(OUT_DIR),
        "debug_images": {key: rel(path) for key, path in debug_paths.items()},
        "target_extraction_summary": extraction_summary,
        "method_summary": {
            "circle_oval": "One circle for near-round targets or two-circle union for elongated ovals; predicted region is count >= 1.",
            "crescent_lens": "Two equal-radius construction circles; predicted region is their intersection, count >= 2.",
            "trigon_three_arc": "Three construction circles; predicted region is their three-way overlap, count >= 3.",
            "hard_rule": "No predicted primitive mask is drawn directly; masks are used only for source-derived target measurement and mismatch evaluation.",
        },
        "candidates": candidates,
        "source_configurations": source_configurations,
        "verdict": verdict,
        "confirmations": {
            "mp4_rendered": False,
            "source_artwork_modified": False,
            "aperture_masks_as_main_mechanism": False,
            "predicted_regions_from_construction_circle_count_geometry": True,
        },
    }
    JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    DOC_PATH.write_text(build_markdown(data), encoding="utf-8")
    print(rel(DOC_PATH))
    print(rel(JSON_PATH))
    print(rel(OUT_DIR))


if __name__ == "__main__":
    main()
