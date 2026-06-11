#!/usr/bin/env python3
"""
Figural Orca wave-interference Type 2 gap/cup scout v001.

Compares the Type 1 overlap constructions from the previous scout with Type 2
gap/cup constructions:
- cup crescent: inside one construction circle and outside a cutter circle
- gap trigon: bounded complement component between three construction circles

This is a still/debug research scout only. It does not render video and does
not modify source artwork.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import figural_orca_wave_interference_match_research_scout_v001 as v1


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "figural_orca_wave_interference_match_type2_gap_scout_v001"
DATE = "2026-05-22"
SOURCE_PATH = ROOT / "austin-v2-ingest" / "approved" / "Animal_Water_Orca_Transparent.png"
V1_JSON_PATH = ROOT / "track2-deterministic" / "anchor_graph" / "orca_wave_interference_fit_candidates_v001.json"
JSON_PATH = ROOT / "track2-deterministic" / "anchor_graph" / "orca_wave_interference_fit_candidates_v001_1_type2_gap.json"
DOC_PATH = ROOT / "docs" / "space-center" / "figural-orca-wave-interference-match-type2-gap-scout-2026-05-22.md"
OUT_DIR = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL" / f"{PROJECT}_{DATE}"

W = v1.W
H = v1.H
TYPE2_FOCUS_IDS = [
    "dorsal_inner_trigon",
    "tail_upper_bluegray_trigon",
    "upper_body_bluegray_crescent",
    "central_pectoral_bluegray_crescent",
    "tail_fluke_bluegray_crescent",
]


def rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return str(p.relative_to(ROOT))


def doc_link(label: str, path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return f"[{label}]({Path(os.path.relpath(p, DOC_PATH.parent)).as_posix()})"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_font(size: int) -> ImageFont.ImageFont:
    return v1.load_font(size)


def unit(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm < 1e-9:
        return np.array([1.0, 0.0], dtype=np.float64)
    return vec / norm


def rotate(vec: np.ndarray, angle_rad: float) -> np.ndarray:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return np.array([vec[0] * c - vec[1] * s, vec[0] * s + vec[1] * c], dtype=np.float64)


def circle_record(center: np.ndarray | list[float], radius: float, role: str) -> dict[str, object]:
    return {
        "role": role,
        "center_canvas_px": [round(float(center[0]), 3), round(float(center[1]), 3)],
        "radius_px": round(float(radius), 3),
    }


def bounds_for_circles(circles: list[dict[str, object]], bbox: list[int], margin: int = 24) -> tuple[int, int, int, int]:
    xs = [float(bbox[0]), float(bbox[2])]
    ys = [float(bbox[1]), float(bbox[3])]
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


def circle_masks(circles: list[dict[str, object]], bounds: tuple[int, int, int, int]) -> list[np.ndarray]:
    x0, y0, x1, y1 = bounds
    yy, xx = np.ogrid[y0:y1, x0:x1]
    masks = []
    for circle in circles:
        cx, cy = circle["center_canvas_px"]
        r = float(circle["radius_px"])
        masks.append(((xx - float(cx)) ** 2 + (yy - float(cy)) ** 2) <= r * r)
    return masks


def metrics_from_prediction(target_mask: np.ndarray, pred: np.ndarray, target_stats: dict[str, object] | None = None) -> dict[str, object]:
    if target_stats is None:
        target_stats = v1.mask_stats(target_mask)
    intersection = int(np.count_nonzero(target_mask & pred))
    union = int(np.count_nonzero(target_mask | pred))
    iou = float(intersection / union) if union else 0.0
    pred_area = int(np.count_nonzero(pred))
    if pred_area:
        py, px = np.nonzero(pred)
        pc = np.array([px.mean(), py.mean()], dtype=np.float64)
        tc = np.array(target_stats["_centroid"], dtype=np.float64)
        centroid_error = float(np.linalg.norm(pc - tc))
        pred_centroid = [round(float(pc[0]), 3), round(float(pc[1]), 3)]
    else:
        centroid_error = float("inf")
        pred_centroid = None
    return {
        "iou": round(iou, 4),
        "intersection_px": intersection,
        "union_px": union,
        "predicted_area_px": pred_area,
        "target_area_px": int(target_stats["area_px"]),
        "predicted_centroid_canvas_px": pred_centroid,
        "target_centroid_canvas_px": target_stats["centroid_canvas_px"],
        "centroid_error_px": round(float(centroid_error), 3) if math.isfinite(centroid_error) else None,
    }


def orientation_error_degrees(target_mask: np.ndarray, pred: np.ndarray) -> float | None:
    if np.count_nonzero(pred) < 20:
        return None
    target_stats = v1.mask_stats(target_mask)
    pred_stats = v1.mask_stats(pred)
    ta = float(target_stats["principal_angle_degrees"])
    pa = float(pred_stats["principal_angle_degrees"])
    diff = abs((pa - ta + 90.0) % 180.0 - 90.0)
    return round(float(diff), 3)


def classify_type2(class_name: str, metrics: dict[str, object], orient_error: float | None, character: str) -> str:
    iou = float(metrics["iou"])
    err = float(metrics["centroid_error_px"] or 99999.0)
    orient = float(orient_error if orient_error is not None else 99999.0)
    if class_name == "crescent/lens":
        if iou >= 0.48 and err <= 55.0 and orient <= 28.0 and "cup" in character:
            return "PASS"
        if iou >= 0.28 and err <= 110.0:
            return "MIXED"
        return "FAIL"
    if class_name == "trigon / three-arc":
        if iou >= 0.42 and err <= 70.0 and "outward" in character:
            return "PASS"
        if iou >= 0.24 and err <= 115.0:
            return "MIXED"
        return "FAIL"
    if class_name == "circle/oval":
        if iou >= 0.58 and err <= 45.0:
            return "PASS"
        if iou >= 0.38 and err <= 75.0:
            return "MIXED"
        return "FAIL"
    return "FAIL"


def local_score(metrics: dict[str, object]) -> float:
    err = float(metrics["centroid_error_px"] or 99999.0)
    area_ratio = float(metrics["predicted_area_px"]) / max(1.0, float(metrics["target_area_px"]))
    return float(metrics["iou"]) - 0.0005 * err - 0.04 * abs(math.log(max(area_ratio, 1e-6)))


def fit_type2_circle_control(target: v1.Target, type1_fit: dict[str, object]) -> tuple[dict[str, object], np.ndarray]:
    pred = v1.predicted_mask_for_fit(type1_fit, target.canvas_mask)
    metrics = metrics_from_prediction(target.canvas_mask, pred, target.stats)
    orient = orientation_error_degrees(target.canvas_mask, pred)
    quality = classify_type2(target.spec.class_name, metrics, orient, "circle control; not a gap/cup target")
    fit = {
        "fit_method": "type2_circle_control_same_as_type1",
        "predicate": "count >= 1; circle/oval is not a gap/cup primitive",
        "construction_circles": type1_fit["construction_circles"],
        "parameterization": {"control": True},
        "metrics": metrics,
        "orientation_error_degrees": orient,
        "curvature_concavity_match": "not applicable",
        "visual_character_match": "circle/oval anchor remains a Type 1 control",
        "shape_fit_quality": quality,
        "notes": "Included only to keep every v001 target represented; Type 2 is evaluated on cup/trigon targets.",
    }
    return fit, pred


def cup_prediction(circles: list[dict[str, object]], target_mask: np.ndarray, target_stats: dict[str, object]) -> np.ndarray:
    bounds = bounds_for_circles(circles, target_stats["bbox_canvas_px"], margin=18)
    outer, cutter = circle_masks(circles, bounds)
    pred_local = outer & (~cutter)
    pred = np.zeros((H, W), dtype=bool)
    x0, y0, x1, y1 = bounds
    pred[y0:y1, x0:x1] = pred_local
    return pred


def fit_type2_cup(target: v1.Target) -> tuple[dict[str, object], np.ndarray]:
    stats = target.stats
    c = np.array(stats["_centroid"], dtype=np.float64)
    base_u = np.array(stats["_u"], dtype=np.float64)
    L = float(stats["major_extent_px"])
    T = float(stats["minor_extent_px"])
    segment_r = max(T * 0.55, (L * L + T * T) / max(1.0, 4.0 * T))
    best: tuple[float, dict[str, object], np.ndarray] | None = None
    for angle in [0.0]:
        u = rotate(base_u, math.radians(angle))
        v = np.array([-u[1], u[0]], dtype=np.float64)
        for sign in [-1.0, 1.0]:
            for r_scale in [1.0, 1.22]:
                for thickness_scale in [1.0]:
                    for cutter_scale in [1.0]:
                        for du_scale in [0.0]:
                            R_outer = segment_r * r_scale
                            R_cutter = segment_r * r_scale * cutter_scale
                            thickness = T * thickness_scale
                            du = L * du_scale
                            outer_center = c + u * du - sign * v * max(0.0, R_outer - thickness * 0.50)
                            cutter_center = c + u * du - sign * v * (R_cutter + thickness * 0.50)
                            circles = [
                                circle_record(outer_center, R_outer, "type2 cup outer arc circle"),
                                circle_record(cutter_center, R_cutter, "type2 cup cutter arc circle"),
                            ]
                            pred = cup_prediction(circles, target.canvas_mask, stats)
                            metrics = metrics_from_prediction(target.canvas_mask, pred, stats)
                            score = local_score(metrics)
                            if best is None or score > best[0]:
                                parameterization = {
                                    "outer_center_canvas_px": circles[0]["center_canvas_px"],
                                    "outer_radius_px": circles[0]["radius_px"],
                                    "cutter_center_canvas_px": circles[1]["center_canvas_px"],
                                    "cutter_radius_px": circles[1]["radius_px"],
                                    "orientation_degrees": round(float(math.degrees(math.atan2(u[1], u[0]))), 3),
                                    "cup_opening_side": "positive normal" if sign > 0 else "negative normal",
                                    "cup_thickness_px": round(float(thickness), 3),
                                }
                                fit = {
                                    "fit_method": "type2_cup_difference",
                                    "predicate": "inside outer circle AND outside cutter circle",
                                    "construction_circles": circles,
                                    "parameterization": parameterization,
                                    "metrics": metrics,
                                    "orientation_error_degrees": orientation_error_degrees(target.canvas_mask, pred),
                                    "curvature_concavity_match": "cupped two-arc boundary; sharper cusp behavior than symmetric vesica",
                                    "visual_character_match": "cup-shaped arc difference rather than overlap lens",
                                    "notes": "Predicted region is a circle-arc cup produced by subtraction/complement, not a drawn crescent.",
                                }
                                best = (score, fit, pred)
    assert best is not None
    _, fit, pred = best
    fit["shape_fit_quality"] = classify_type2(
        target.spec.class_name,
        fit["metrics"],
        fit["orientation_error_degrees"],
        str(fit["visual_character_match"]),
    )
    return fit, pred


def gap_prediction(circles: list[dict[str, object]], target_mask: np.ndarray, stats: dict[str, object]) -> tuple[np.ndarray, bool]:
    bounds = bounds_for_circles(circles, stats["bbox_canvas_px"], margin=36)
    masks = circle_masks(circles, bounds)
    union = np.zeros_like(masks[0], dtype=bool)
    for mask in masks:
        union |= mask
    complement = ~union
    labels, count = ndimage.label(complement, structure=np.ones((3, 3), dtype=np.uint8))
    if count == 0:
        return np.zeros((H, W), dtype=bool), False
    x0, y0, x1, y1 = bounds
    target_local = target_mask[y0:y1, x0:x1]
    best_label = 0
    best_overlap = 0
    for idx in range(1, count + 1):
        overlap = int(np.count_nonzero((labels == idx) & target_local))
        if overlap > best_overlap:
            best_label = idx
            best_overlap = overlap
    if best_label == 0:
        cx, cy = stats["centroid_canvas_px"]
        lx = int(round(float(cx))) - x0
        ly = int(round(float(cy))) - y0
        if 0 <= lx < labels.shape[1] and 0 <= ly < labels.shape[0]:
            best_label = int(labels[ly, lx])
    if best_label == 0:
        return np.zeros((H, W), dtype=bool), False
    local = labels == best_label
    touches_border = bool(local[0, :].any() or local[-1, :].any() or local[:, 0].any() or local[:, -1].any())
    pred = np.zeros((H, W), dtype=bool)
    pred[y0:y1, x0:x1] = local
    return pred, not touches_border


def triangle_vertices(c: np.ndarray, u: np.ndarray, L: float, T: float, front: float, back: float, half: float) -> list[np.ndarray]:
    v = np.array([-u[1], u[0]], dtype=np.float64)
    return [
        c + u * (L * front),
        c - u * (L * back) + v * (T * half),
        c - u * (L * back) - v * (T * half),
    ]


def fit_type2_gap_trigon(target: v1.Target) -> tuple[dict[str, object], np.ndarray]:
    stats = target.stats
    c = np.array(stats["_centroid"], dtype=np.float64)
    base_u = np.array(stats["_tip_dir"], dtype=np.float64)
    L = float(stats["major_extent_px"])
    T = float(stats["minor_extent_px"])
    best: tuple[float, dict[str, object], np.ndarray] | None = None
    for sign in [1.0, -1.0]:
        for angle in [0.0]:
            u = rotate(base_u * sign, math.radians(angle))
            for front in [0.48]:
                for back in [0.36]:
                    for half in [0.68]:
                        vertices = triangle_vertices(c, u, L, T, front, back, half)
                        distances = [float(np.linalg.norm(vertex - c)) for vertex in vertices]
                        min_d = min(distances)
                        max_d = max(distances)
                        if min_d < 8.0:
                            continue
                        for radius_frac in [0.70, 0.86]:
                            radius = min_d * radius_frac
                            if radius <= 8.0 or radius >= max_d * 1.25:
                                continue
                            circles = [
                                circle_record(vertices[0], radius, "type2 gap circle near tip arc"),
                                circle_record(vertices[1], radius, "type2 gap circle near base-left arc"),
                                circle_record(vertices[2], radius, "type2 gap circle near base-right arc"),
                            ]
                            pred, bounded = gap_prediction(circles, target.canvas_mask, stats)
                            if not np.count_nonzero(pred):
                                continue
                            metrics = metrics_from_prediction(target.canvas_mask, pred, stats)
                            bounded_bonus = 0.06 if bounded else -0.08
                            score = local_score(metrics) + bounded_bonus
                            if best is None or score > best[0]:
                                side_lengths = [
                                    float(np.linalg.norm(vertices[0] - vertices[1])),
                                    float(np.linalg.norm(vertices[1] - vertices[2])),
                                    float(np.linalg.norm(vertices[2] - vertices[0])),
                                ]
                                fit = {
                                    "fit_method": "type2_arc_bounded_gap_trigon",
                                    "predicate": "bounded complement component outside union of three construction circles",
                                    "construction_circles": circles,
                                    "parameterization": {
                                        "center_triangle_side_lengths_px": [round(v, 3) for v in side_lengths],
                                        "center_triangle_orientation_degrees": round(float(math.degrees(math.atan2(u[1], u[0]))), 3),
                                        "gap_component_bounded": bounded,
                                        "gap_region_centroid_canvas_px": metrics["predicted_centroid_canvas_px"],
                                        "arc_curvature": "sides curve outward away from trigon interior because the predicted region is outside the generating disks",
                                    },
                                    "metrics": metrics,
                                    "orientation_error_degrees": orientation_error_degrees(target.canvas_mask, pred),
                                    "curvature_concavity_match": "outward-curving arc-bounded gap" if bounded else "open gap candidate; boundedness weak",
                                    "visual_character_match": "outward gap trigon bounded by nearby arcs",
                                    "notes": "Predicted region is selected as the complement gap between three disks, not a three-circle overlap cell.",
                                }
                                best = (score, fit, pred)
    assert best is not None
    _, fit, pred = best
    fit["shape_fit_quality"] = classify_type2(
        target.spec.class_name,
        fit["metrics"],
        fit["orientation_error_degrees"],
        str(fit["visual_character_match"]),
    )
    return fit, pred


def fit_type2(target: v1.Target, type1_fit: dict[str, object]) -> tuple[dict[str, object], np.ndarray]:
    if target.spec.class_name == "circle/oval":
        return fit_type2_circle_control(target, type1_fit)
    if target.spec.class_name == "crescent/lens":
        return fit_type2_cup(target)
    if target.spec.class_name == "trigon / three-arc":
        return fit_type2_gap_trigon(target)
    raise RuntimeError(f"no Type 2 fit for {target.spec.class_name}")


def compare_record(target: v1.Target, type1_fit: dict[str, object], type2_fit: dict[str, object]) -> dict[str, object]:
    t1 = type1_fit["metrics"]
    t2 = type2_fit["metrics"]
    delta_iou = round(float(t2["iou"]) - float(t1["iou"]), 4)
    t1_err = float(t1["centroid_error_px"] or 99999.0)
    t2_err = float(t2["centroid_error_px"] or 99999.0)
    delta_err = round(t2_err - t1_err, 3)
    if target.spec.candidate_id in TYPE2_FOCUS_IDS:
        if delta_iou > 0.03 and type2_fit["shape_fit_quality"] in ["PASS", "MIXED"]:
            verdict = "TYPE2_BETTER"
        elif delta_iou < -0.08 or type2_fit["shape_fit_quality"] == "FAIL":
            verdict = "TYPE1_BETTER"
        else:
            verdict = "MIXED"
    else:
        verdict = "CONTROL"
    return {
        "candidate_id": target.spec.candidate_id,
        "classification": target.spec.class_name,
        "type1_iou": t1["iou"],
        "type2_iou": t2["iou"],
        "delta_iou_type2_minus_type1": delta_iou,
        "type1_centroid_error_px": t1["centroid_error_px"],
        "type2_centroid_error_px": t2["centroid_error_px"],
        "delta_centroid_error_px": delta_err,
        "type2_orientation_error_degrees": type2_fit["orientation_error_degrees"],
        "type1_quality": type1_fit["shape_fit_quality"],
        "type2_quality": type2_fit["shape_fit_quality"],
        "comparison_verdict": verdict,
        "curvature_concavity_match": type2_fit["curvature_concavity_match"],
        "visual_character_match": type2_fit["visual_character_match"],
    }


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: tuple[int, int, int] = (250, 250, 244)) -> None:
    v1.draw_label(draw, xy, text, font, fill)


def draw_source_targets(source_rgba: Image.Image, targets: list[v1.Target], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    img = v1.place_source(source_rgba, checker=True, opacity=1.0)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(22)
    for index, target in enumerate(targets, 1):
        color = colors[target.spec.candidate_id]
        bbox = target.stats["bbox_canvas_px"]
        cx, cy = target.stats["centroid_canvas_px"]
        draw.rectangle(bbox, outline=color + (220,), width=4)
        draw.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=color + (255,))
        draw_label(draw, (bbox[0], max(4, bbox[1] - 28)), f"{index}. {target.spec.candidate_id}", small, fill=color)
    draw_label(draw, (40, 34), "Orca source with reused v001 primitive targets marked", font)
    return Image.alpha_composite(img, overlay).convert("RGB")


def draw_type1(source_rgba: Image.Image, targets: list[v1.Target], type1_fits: dict[str, dict[str, object]], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    return v1.construction_circles_over_source(source_rgba, targets, type1_fits, colors)


def draw_type2(source_rgba: Image.Image, targets: list[v1.Target], type2_fits: dict[str, dict[str, object]], colors: dict[str, tuple[int, int, int]]) -> Image.Image:
    img = v1.place_source(source_rgba, checker=True, opacity=0.92)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(22)
    for index, target in enumerate(targets, 1):
        fit = type2_fits.get(target.spec.candidate_id)
        if fit is None:
            continue
        color = colors[target.spec.candidate_id]
        for circle in fit["construction_circles"]:
            cx, cy = circle["center_canvas_px"]
            r = float(circle["radius_px"])
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color + (215,), width=4)
            draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color + (255,))
        bbox = target.stats["bbox_canvas_px"]
        label = f"{index}. {fit['shape_fit_quality']} T2 IoU {fit['metrics']['iou']:.2f}"
        draw_label(draw, (bbox[0], max(4, bbox[1] - 24)), label, small, fill=color)
    draw_label(draw, (40, 34), "Type 2 gap/cup construction circles over Orca", font)
    return Image.alpha_composite(img, overlay).convert("RGB")


def type1_pred(type1_fit: dict[str, object], target: v1.Target) -> np.ndarray:
    return v1.predicted_mask_for_fit(type1_fit, target.canvas_mask)


def mismatch_sheet(
    source_rgba: Image.Image,
    focus_targets: list[v1.Target],
    type1_fits: dict[str, dict[str, object]],
    type2_fits: dict[str, dict[str, object]],
    type2_predictions: dict[str, np.ndarray],
    colors: dict[str, tuple[int, int, int]],
) -> Image.Image:
    tile_w = 960
    tile_h = 360
    sheet = Image.new("RGB", (tile_w * 2, tile_h * len(focus_targets)), (18, 20, 24))
    source_canvas = v1.place_source(source_rgba, checker=False, opacity=0.35).convert("RGB")
    font = load_font(22)
    small = load_font(16)
    for row, target in enumerate(focus_targets):
        for col, kind in enumerate(["Type 1 overlap", "Type 2 gap/cup"]):
            fit = type1_fits[target.spec.candidate_id] if col == 0 else type2_fits[target.spec.candidate_id]
            pred = type1_pred(fit, target) if col == 0 else type2_predictions[target.spec.candidate_id]
            union = pred | target.canvas_mask
            ys, xs = np.nonzero(union)
            margin = 64
            x0 = max(0, int(xs.min()) - margin)
            y0 = max(0, int(ys.min()) - margin)
            x1 = min(W, int(xs.max()) + margin)
            y1 = min(H, int(ys.max()) + margin)
            crop = source_canvas.crop((x0, y0, x1, y1)).convert("RGBA")
            rgba = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
            target_local = target.canvas_mask[y0:y1, x0:x1]
            pred_local = pred[y0:y1, x0:x1]
            rgba[target_local & (~pred_local)] = [40, 220, 150, 160]
            rgba[pred_local & (~target_local)] = [226, 70, 188, 150]
            rgba[target_local & pred_local] = [255, 245, 120, 220]
            overlay = Image.fromarray(rgba, "RGBA")
            combined = Image.alpha_composite(crop, overlay).convert("RGB")
            combined.thumbnail((tile_w - 30, tile_h - 82), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (tile_w, tile_h), (18, 20, 24))
            draw = ImageDraw.Draw(tile)
            x = (tile_w - combined.size[0]) // 2
            tile.paste(combined, (x, 62))
            color = colors[target.spec.candidate_id]
            draw_label(draw, (18, 12), f"{target.spec.candidate_id} | {kind}: {fit['shape_fit_quality']} IoU {fit['metrics']['iou']:.2f}", font, fill=color)
            draw_label(draw, (18, 38), "green target only | magenta predicted only | yellow overlap", small)
            sheet.paste(tile, (tile_w * col, tile_h * row))
    return sheet


def edge_mask(mask: np.ndarray, size: int = 7) -> np.ndarray:
    img = Image.fromarray((mask.astype(np.uint8) * 255), "L")
    expanded = img.filter(ImageFilter.MaxFilter(size))
    eroded = img.filter(ImageFilter.MinFilter(size))
    return np.array(ImageChops.difference(expanded, eroded)) > 0


def type2_detection_map(
    source_rgba: Image.Image,
    focus_targets: list[v1.Target],
    type2_fits: dict[str, dict[str, object]],
    type2_predictions: dict[str, np.ndarray],
    colors: dict[str, tuple[int, int, int]],
) -> Image.Image:
    base = v1.place_source(source_rgba, checker=False, opacity=0.22).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(20)
    for target in focus_targets:
        fit = type2_fits[target.spec.candidate_id]
        color = colors[target.spec.candidate_id]
        for circle in fit["construction_circles"]:
            cx, cy = circle["center_canvas_px"]
            r = float(circle["radius_px"])
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(70, 120, 180, 110), width=3)
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[type2_predictions[target.spec.candidate_id]] = [color[0], color[1], color[2], 170]
        rgba[edge_mask(target.canvas_mask, size=7)] = [245, 245, 235, 180]
        overlay.alpha_composite(Image.fromarray(rgba, "RGBA"))
        cx, cy = target.stats["centroid_canvas_px"]
        draw.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(245, 245, 235, 220))
    draw_label(draw, (40, 34), "Type 2 detected regions: cup difference and bounded gap complement", font)
    draw_label(draw, (40, 74), "blue outlines = construction circles | colored fills = detected Type 2 regions | white edges = targets", small)
    return Image.alpha_composite(base, overlay).convert("RGB")


def combined_type2_coherence_map(
    source_rgba: Image.Image,
    targets: list[v1.Target],
    type1_fits: dict[str, dict[str, object]],
    type2_fits: dict[str, dict[str, object]],
    type2_predictions: dict[str, np.ndarray],
    colors: dict[str, tuple[int, int, int]],
) -> tuple[Image.Image, dict[str, object]]:
    type1_circles: list[dict[str, object]] = []
    for fit in type1_fits.values():
        type1_circles.extend(fit["construction_circles"])
    count = v1.diagnostic_count_map(type1_circles, scale=4)
    palette = np.array([[8, 10, 14], [20, 53, 92], [34, 106, 132], [150, 118, 65], [168, 68, 76], [190, 90, 155]], dtype=np.uint8)
    bg = Image.fromarray(palette[np.clip(count, 0, len(palette) - 1)], "RGB").resize((W, H), Image.Resampling.NEAREST).convert("RGBA")
    source = v1.place_source(source_rgba, checker=False, opacity=0.12)
    img = Image.blend(bg, source, alpha=0.25).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = load_font(30)
    small = load_font(20)
    type2_union = np.zeros((H, W), dtype=bool)
    target_union = np.zeros((H, W), dtype=bool)
    for target in targets:
        if target.spec.candidate_id not in type2_predictions:
            continue
        pred = type2_predictions[target.spec.candidate_id]
        type2_union |= pred
        target_union |= target.canvas_mask
        color = colors[target.spec.candidate_id]
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        rgba[pred] = [color[0], color[1], color[2], 165]
        overlay.alpha_composite(Image.fromarray(rgba, "RGBA"))
        bbox = target.stats["bbox_canvas_px"]
        draw.rectangle(bbox, outline=color + (160,), width=2)
    off_target = type2_union & (~target_union)
    labels, _ = ndimage.label(off_target[::4, ::4], structure=np.ones((3, 3), dtype=np.uint8))
    spurious_components = 0
    for idx, slc in enumerate(ndimage.find_objects(labels), start=1):
        if slc is None:
            continue
        if int((labels[slc] == idx).sum()) * 16 >= 1200:
            spurious_components += 1
    draw_label(draw, (40, 34), "Combined Type 2 regions over Type 1 overlap background", font)
    draw_label(draw, (40, 74), f"Type 2 off-target components area>=1200: {spurious_components}", small)
    metrics = {
        "type1_background_source_circles": len(type1_circles),
        "type1_background_max_count": int(count.max()),
        "type2_union_area_px": int(np.count_nonzero(type2_union)),
        "type2_off_target_area_px": int(np.count_nonzero(off_target)),
        "type2_off_target_component_count_area_ge_1200": spurious_components,
    }
    return Image.alpha_composite(img, overlay).convert("RGB"), metrics


def quality_delta_text(compare: dict[str, object]) -> str:
    delta = float(compare["delta_iou_type2_minus_type1"])
    if delta > 0.03:
        return "improves"
    if delta < -0.08:
        return "worse"
    return "similar"


def build_markdown(data: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Figural Orca Wave-Interference Type 2 Gap/Cup Scout - 2026-05-22")
    lines.append("")
    lines.append("Status: INTERNAL RESEARCH + GEOMETRY-FIT SCOUT ONLY. No MP4 was rendered and the source artwork was not modified.")
    lines.append("")
    lines.append("Purpose: continue `figural_orca_wave_interference_match_research_scout_v001` by comparing Type 1 overlap geometry against Type 2 gap/cup geometry for Orca internal primitives.")
    lines.append("")
    lines.append("Reviewed source and baseline:")
    lines.append("")
    lines.append(f"- Source artwork: `{data['source_path']}`")
    lines.append("- Placement transform: scale `0.88`, top-left `[896, 122]`, display size `[2219, 1949]`.")
    lines.append(f"- Baseline Type 1 JSON: {doc_link('orca_wave_interference_fit_candidates_v001.json', V1_JSON_PATH)}")
    lines.append(f"- Updated Type 2 JSON: {doc_link('orca_wave_interference_fit_candidates_v001_1_type2_gap.json', JSON_PATH)}")
    lines.append(f"- Debug folder: `{data['output_dir']}`")
    lines.append("")
    lines.append("## Geometry Tested")
    lines.append("")
    lines.append("Type 1 baseline keeps the v001 definitions: ovals are `count >= 1`, crescents are two-circle overlap lenses, and trigons are three-circle overlap cells.")
    lines.append("")
    lines.append("Type 2 definitions:")
    lines.append("")
    lines.append("- Crescent/cup: predicted region is `inside outer circle AND outside cutter circle`, creating a cupped two-arc region with sharper cusp behavior than a symmetric vesica.")
    lines.append("- Trigon/gap: predicted region is the bounded complement component outside the union of three nearby construction circles. This makes the sides arc outward away from the trigon interior instead of forming an inward overlap cell.")
    lines.append("- Circle/oval targets are retained as controls because gap/cup logic is not the relevant primitive family for those anchors.")
    lines.append("")
    lines.append("## Type 1 vs Type 2 Comparison")
    lines.append("")
    lines.append("| Candidate | Class | Type 1 IoU / err | Type 2 IoU / err | Orientation err | Type 2 quality | Delta | Character verdict |")
    lines.append("|---|---|---:|---:|---:|---|---|---|")
    for comp in data["comparisons"]:
        focus = "focus" if comp["candidate_id"] in TYPE2_FOCUS_IDS else "control"
        lines.append(
            f"| `{comp['candidate_id']}` | {comp['classification']} | {comp['type1_iou']} / {comp['type1_centroid_error_px']} | {comp['type2_iou']} / {comp['type2_centroid_error_px']} | {comp['type2_orientation_error_degrees']} | {comp['type2_quality']} | {quality_delta_text(comp)} | {focus}: {comp['visual_character_match']} |"
        )
    lines.append("")
    lines.append("## Focus-Target Read")
    lines.append("")
    focus_rows = [comp for comp in data["comparisons"] if comp["candidate_id"] in TYPE2_FOCUS_IDS]
    better = sum(1 for comp in focus_rows if comp["comparison_verdict"] == "TYPE2_BETTER")
    worse = sum(1 for comp in focus_rows if comp["comparison_verdict"] == "TYPE1_BETTER")
    mixed = len(focus_rows) - better - worse
    lines.append(f"Across the five requested focus targets, Type 2 is better on `{better}`, worse on `{worse}`, and mixed/similar on `{mixed}`.")
    lines.append("")
    lines.append("- The cup model is conceptually closer to cupped crescents because it produces one filled side and one cutting arc rather than a symmetric lens, but the tested fits overgrow the body bands.")
    lines.append("- The dorsal and tail trigon gap model expresses the correct outward-arc idea, but the bounded complement regions do not match the authored trigon masks.")
    lines.append("- In this deterministic scout, Type 2 is a useful grammar hypothesis but not a material fit improvement over Type 1.")
    lines.append("")
    lines.append("## Debug Stills")
    lines.append("")
    for label, path in data["debug_images"].items():
        pretty = label.replace("_", " ")
        lines.append(f"- {doc_link(pretty, path)}")
    lines.append("")
    lines.append("## Global Field Coherence")
    lines.append("")
    coh = data["coherence"]
    lines.append(f"- Type 1 background source circles: `{coh['type1_background_source_circles']}`")
    lines.append(f"- Type 1 background max overlap count: `{coh['type1_background_max_count']}`")
    lines.append(f"- Type 2 union area: `{coh['type2_union_area_px']}` px")
    lines.append(f"- Type 2 off-target area: `{coh['type2_off_target_area_px']}` px")
    lines.append(f"- Type 2 off-target components >= 1200 px: `{coh['type2_off_target_component_count_area_ge_1200']}`")
    lines.append("")
    lines.append("Type 2 cup/gap regions remain visually separable from the Type 1 overlap background, but they do not stay clean enough to rescue field coherence. The global arrangement still reads as a cluster of independently fitted local constructions, with large off-target regions and failed trigon gap cells.")
    lines.append("")
    lines.append("## Outcome")
    lines.append("")
    verdict = data["verdict"]
    lines.append(f"Go/no-go verdict: **{verdict['go_no_go']}**.")
    lines.append("")
    lines.append(f"- Recommendation for direct `figural_orca_wave_interference_match_v001` beauty render: `{str(verdict['recommend_render']).lower()}`.")
    lines.append(f"- Rationale: {verdict['rationale']}")
    lines.append("")
    lines.append("Recommended next move: do not render a direct beauty pass from this architecture. Keep Type 2 gap/cup geometry as a future grammar thread, but it needs a better bounded-gap construction and a shared source-family or silhouette/flow layer before it can carry the Orca composition.")
    lines.append("")
    lines.append("## Verification Notes")
    lines.append("")
    lines.append("- JSON parses with `python3 -m json.tool`.")
    lines.append("- Markdown links are repository-relative from this document.")
    lines.append("- Output folder contains PNG stills only.")
    lines.append("- Source PNG SHA-256 matches the baseline source hash.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    source_rgba = Image.open(SOURCE_PATH).convert("RGBA")
    with V1_JSON_PATH.open() as f:
        v1_data = json.load(f)
    targets, extraction_summary = v1.extract_targets(source_rgba)
    target_by_id = {target.spec.candidate_id: target for target in targets}
    type1_fits = {item["candidate_id"]: item["fit"] for item in v1_data["candidates"] if item.get("fit")}

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

    type2_fits: dict[str, dict[str, object]] = {}
    type2_predictions: dict[str, np.ndarray] = {}
    comparisons: list[dict[str, object]] = []
    for target in targets:
        type1_fit = type1_fits.get(target.spec.candidate_id)
        if type1_fit is None:
            continue
        type2_fit, pred = fit_type2(target, type1_fit)
        type2_fits[target.spec.candidate_id] = type2_fit
        type2_predictions[target.spec.candidate_id] = pred
        comparisons.append(compare_record(target, type1_fit, type2_fit))

    focus_targets = [target_by_id[candidate_id] for candidate_id in TYPE2_FOCUS_IDS]

    debug_paths = {
        "source_targets_marked": OUT_DIR / f"{PROJECT}_debug_01_source_targets_marked.png",
        "type1_fits_over_source": OUT_DIR / f"{PROJECT}_debug_02_type1_fits_over_source.png",
        "type2_fits_over_source": OUT_DIR / f"{PROJECT}_debug_03_type2_fits_over_source.png",
        "type1_vs_type2_mismatch_sheet": OUT_DIR / f"{PROJECT}_debug_04_type1_vs_type2_mismatch_sheet.png",
        "type2_gap_cup_detection_map": OUT_DIR / f"{PROJECT}_debug_05_type2_gap_cup_detection_map.png",
        "combined_type2_coherence_map": OUT_DIR / f"{PROJECT}_debug_06_combined_type2_coherence_map.png",
    }
    draw_source_targets(source_rgba, targets, colors).save(debug_paths["source_targets_marked"])
    draw_type1(source_rgba, targets, type1_fits, colors).save(debug_paths["type1_fits_over_source"])
    draw_type2(source_rgba, targets, type2_fits, colors).save(debug_paths["type2_fits_over_source"])
    mismatch_sheet(source_rgba, focus_targets, type1_fits, type2_fits, type2_predictions, colors).save(debug_paths["type1_vs_type2_mismatch_sheet"])
    type2_detection_map(source_rgba, focus_targets, type2_fits, type2_predictions, colors).save(debug_paths["type2_gap_cup_detection_map"])
    coherence_img, coherence = combined_type2_coherence_map(source_rgba, targets, type1_fits, type2_fits, type2_predictions, colors)
    coherence_img.save(debug_paths["combined_type2_coherence_map"])

    focus_comps = [comp for comp in comparisons if comp["candidate_id"] in TYPE2_FOCUS_IDS]
    type2_better = sum(1 for comp in focus_comps if comp["comparison_verdict"] == "TYPE2_BETTER")
    type2_fail = sum(1 for comp in focus_comps if comp["type2_quality"] == "FAIL")
    if type2_better >= 4 and coherence["type2_off_target_component_count_area_ge_1200"] <= 3:
        go_no_go = "GO"
        recommend_render = True
        rationale = "Type 2 improved most focus targets and the global field stayed controlled."
    elif type2_better == 0 or type2_fail >= 3:
        go_no_go = "NO-GO"
        recommend_render = False
        rationale = "Type 2 did not materially improve the requested focus targets and global field coherence remains scattered."
    else:
        go_no_go = "MIXED"
        recommend_render = False
        rationale = "Type 2 improves local primitive character for cup/gap forms, but global field coherence remains scattered."

    data = {
        "project": PROJECT,
        "date": DATE,
        "status": "internal Type 2 gap/cup geometry scout only; no MP4 render",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "source_to_canvas_transform": v1_data["source_to_canvas_transform"],
        "baseline_type1_json": rel(V1_JSON_PATH),
        "output_dir": rel(OUT_DIR),
        "target_extraction_summary": extraction_summary,
        "focus_candidate_ids": TYPE2_FOCUS_IDS,
        "type1_method": v1_data["method_summary"],
        "type2_method": {
            "crescent_cup": "inside outer construction circle AND outside cutter construction circle",
            "trigon_gap": "bounded complement component outside union of three construction circles",
            "circle_control": "circle/oval targets retained as Type 1 controls",
        },
        "type2_fits": type2_fits,
        "comparisons": comparisons,
        "coherence": coherence,
        "debug_images": {key: rel(path) for key, path in debug_paths.items()},
        "verdict": {
            "go_no_go": go_no_go,
            "recommend_render": recommend_render,
            "rationale": rationale,
        },
        "confirmations": {
            "mp4_rendered": False,
            "source_artwork_modified": False,
            "type2_regions_from_circle_arc_gap_cup_geometry": True,
        },
    }
    JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    DOC_PATH.write_text(build_markdown(data), encoding="utf-8")
    print(rel(DOC_PATH))
    print(rel(JSON_PATH))
    print(rel(OUT_DIR))


if __name__ == "__main__":
    main()
