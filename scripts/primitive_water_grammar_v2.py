#!/usr/bin/env python3.11
"""
Primitive Water Grammar v002 review packet.

Cleaner internal review packet from the strongest v001 clips:
  - ocean/kelp optical-flow
  - salmon school proxy

Changes from v001:
  - restrained ivory / pale-blue palette instead of debug gold/red
  - lower composite opacity so footage breathes
  - 25-40% fewer primitive phrases
  - matching black-background primitive-layer clips for Resolume screen blend
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
    H6_KELP,
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
    soften_background,
    transform_points,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19"
FPS = 24

# Restrained single-family review palette. RGB order.
CIRCLE_RGB = (238, 231, 205)     # warm ivory anchor
CRESCENT_RGB = (205, 226, 232)   # pale water blue
TRIGON_RGB = (176, 204, 218)     # slightly deeper attenuation mark
OUTLINE_RGB = (228, 239, 238)    # soft edge for screen-blend/lower-opacity compositing

COMPOSITE_ALPHA = 0.92
LAYER_ALPHA = 1.00


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    method: str
    review_note: str
    recommended: bool = False
    dynamic_note: str = ""


def draw_crescent_v2(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(CRESCENT_BASE, center, size, angle),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.22,
        outline_thickness=1,
    )


def draw_trigon_v2(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(TRIGON_BASE, center, size, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.20,
        outline_thickness=1,
    )


def draw_circle_v2(frame: np.ndarray, center: tuple[float, float], radius: float, *, alpha: float) -> None:
    draw_circle_alpha(
        frame,
        center,
        radius,
        CIRCLE_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.22,
    )


def draw_phrase_v2(
    frame: np.ndarray,
    anchor: tuple[float, float],
    angle: float,
    *,
    alpha: float,
    spacing: float,
    scale: float = 1.0,
) -> None:
    dx = math.cos(angle)
    dy = math.sin(angle)
    offsets = [-spacing * 1.06, -spacing * 0.21, spacing * 0.62, spacing * 1.31]
    for shape_idx, offset in enumerate(offsets):
        pos = (anchor[0] + dx * offset, anchor[1] + dy * offset)
        if shape_idx == 0:
            draw_circle_v2(frame, pos, 10.5 * scale, alpha=alpha * 0.92)
        elif shape_idx == 1:
            draw_crescent_v2(frame, pos, 30.0 * scale, angle, alpha=alpha)
        elif shape_idx == 2:
            draw_crescent_v2(frame, pos, 26.5 * scale, angle, alpha=alpha * 0.84)
        else:
            draw_trigon_v2(frame, pos, 25.0 * scale, angle, alpha=alpha * 0.72)


def layer_canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def v2_background(frame: np.ndarray) -> np.ndarray:
    graded = soften_background(frame, mode="underwater")
    # Let more original footage through than v001.
    return cv2.addWeighted(frame, 0.36, graded, 0.64, 0)


def detect_salmon_proxy_v2(frame: np.ndarray, flow: np.ndarray | None) -> list[dict[str, float]]:
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
        if not (900 <= area <= 52000 and 0.75 <= aspect <= 8.25 and 24 <= cw <= 520 and 14 <= ch <= 230 and extent > 0.12):
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
                angle = smooth_angle(angle, math.atan2(dy, dx), amount=0.42)
        detections.append({"cx": cx, "cy": cy, "area": float(area), "angle": angle})
    detections.sort(key=lambda d: d["area"], reverse=True)

    kept: list[dict[str, float]] = []
    for det in detections:
        if len(kept) >= 8:
            break
        if all(math.hypot(det["cx"] - prev["cx"], det["cy"] - prev["cy"]) > 155 for prev in kept):
            kept.append(det)
    return kept


def render_ocean_kelp_v2() -> list[ClipResult]:
    composite = OUT_DIR / "01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4"
    layer = OUT_DIR / "02_ocean_kelp_optical_flow_v002_layer_only_black_screen.mp4"
    reader = SampledVideo(H6_KELP, start_seconds=8.0)
    comp_writer = H264Writer(composite)
    layer_writer = H264Writer(layer)
    anchors = []
    # v001 used 12 anchors; v002 uses 8, spaced away from burn-in.
    for idx, (x, y, a) in enumerate(
        [
            (0.22, 0.32, -0.08),
            (0.43, 0.38, 0.12),
            (0.63, 0.35, 0.08),
            (0.79, 0.50, -0.04),
            (0.28, 0.58, 0.18),
            (0.52, 0.61, 0.10),
            (0.72, 0.69, 0.00),
            (0.41, 0.77, 0.14),
        ]
    ):
        anchors.append({"x": W * x, "y": H * y, "angle": a, "phase": idx * 0.43})

    prev_raw = reader.frame(0)
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else np.zeros((270, 480, 2), dtype=np.float32)
        comp = v2_background(raw)
        black = layer_canvas()
        t = fi / FPS
        for anchor in anchors:
            dx, dy = sample_flow(flow, anchor["x"], anchor["y"])
            mag = math.hypot(dx, dy)
            if mag > 0.20:
                anchor["angle"] = smooth_angle(anchor["angle"], math.atan2(dy, dx), amount=0.18)
            else:
                anchor["angle"] = smooth_angle(anchor["angle"], 0.04 + 0.08 * math.sin(t + anchor["phase"]), amount=0.05)
            anchor["x"] += math.cos(anchor["angle"]) * 0.24 + dx * 0.42
            anchor["y"] += math.sin(anchor["angle"]) * 0.24 + dy * 0.42
            if anchor["x"] < -90:
                anchor["x"] = W + 50
            elif anchor["x"] > W + 90:
                anchor["x"] = -50
            if anchor["y"] < 95:
                anchor["y"] = H * 0.78
            elif anchor["y"] > H * 0.86:
                anchor["y"] = H * 0.27
            pulse = 0.90 + 0.10 * math.sin(t * 1.35 + anchor["phase"])
            draw_phrase_v2(comp, (anchor["x"], anchor["y"]), anchor["angle"], alpha=0.18 * pulse * COMPOSITE_ALPHA, spacing=48.0)
            draw_phrase_v2(black, (anchor["x"], anchor["y"]), anchor["angle"], alpha=0.66 * pulse * LAYER_ALPHA, spacing=48.0)
        comp_writer.write(comp)
        layer_writer.write(black)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            print(f"  ocean/kelp v002 {fi + 1}/{N_FRAMES}", flush=True)
    comp_writer.close()
    layer_writer.close()
    reader.close()
    return [
        ClipResult(
            filename=composite.name,
            source=str(H6_KELP.relative_to(ROOT)),
            test="Cleaner H6 ocean/kelp optical-flow composite with sparse primitive phrases following current.",
            method="8 optical-flow phrase anchors, smoothed direction, ivory/pale-blue low-opacity glyphs.",
            review_note="Composite includes filename/timecode burn-in from source footage; this is not added by the primitive renderer.",
            recommended=True,
        ),
        ClipResult(
            filename=layer.name,
            source="primitive layer only; timing/motion matched to H6 composite",
            test="Black-background layer-only version for Resolume screen blend or additive mixing.",
            method="Same H6 optical-flow phrase positions rendered as light glyphs on black.",
            review_note="No source burn-in; intended for independent live mixing over clean footage.",
        ),
    ]


def render_salmon_school_v2() -> list[ClipResult]:
    composite = OUT_DIR / "03_salmon_school_proxy_v002_composite_H1_source_burnin.mp4"
    layer = OUT_DIR / "04_salmon_school_proxy_v002_layer_only_black_screen.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    comp_writer = H264Writer(composite)
    layer_writer = H264Writer(layer)
    prev_raw = reader.frame(0)
    detection_counts: list[int] = []
    fallback_frames = 0

    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        comp = v2_background(raw)
        black = layer_canvas()
        detections = detect_salmon_proxy_v2(raw, flow)
        detection_counts.append(len(detections))
        if len(detections) >= 3:
            for det in detections:
                cx, cy = det["cx"], det["cy"]
                angle = det["angle"]
                scale = max(0.70, min(1.40, math.sqrt(det["area"]) / 115.0))
                draw_circle_v2(comp, (cx, cy), 10.5 * scale, alpha=0.22 * COMPOSITE_ALPHA)
                draw_circle_v2(black, (cx, cy), 10.5 * scale, alpha=0.86 * LAYER_ALPHA)
                # Circle currently anchors on the salmon center; crescents/trigon
                # lead in swim/flow direction to make the Austin question concrete.
                lead_anchor = (cx + math.cos(angle) * 64.0 * scale, cy + math.sin(angle) * 64.0 * scale)
                draw_phrase_v2(comp, lead_anchor, angle, alpha=0.17 * COMPOSITE_ALPHA, spacing=31.0 * scale, scale=scale)
                draw_phrase_v2(black, lead_anchor, angle, alpha=0.66 * LAYER_ALPHA, spacing=31.0 * scale, scale=scale)
        else:
            fallback_frames += 1
            if flow is not None:
                # Sparse fallback: 4 positions only, maintaining phrase order.
                for x, y in [(0.25, 0.38), (0.48, 0.51), (0.68, 0.44), (0.56, 0.70)]:
                    px, py = W * x, H * y
                    dx, dy = sample_flow(flow, px, py)
                    angle = math.atan2(dy, dx) if math.hypot(dx, dy) > 0.15 else 0.0
                    draw_phrase_v2(comp, (px, py), angle, alpha=0.12 * COMPOSITE_ALPHA, spacing=37.0)
                    draw_phrase_v2(black, (px, py), angle, alpha=0.56 * LAYER_ALPHA, spacing=37.0)
        comp_writer.write(comp)
        layer_writer.write(black)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            avg = sum(detection_counts[-48:]) / max(1, len(detection_counts[-48:]))
            print(f"  salmon v002 {fi + 1}/{N_FRAMES} avg detections last block={avg:.1f}", flush=True)

    comp_writer.close()
    layer_writer.close()
    reader.close()
    avg_det = sum(detection_counts) / max(1, len(detection_counts))
    dynamic = f"Average kept salmon-proxy components per frame: {avg_det:.1f}; fallback optical-flow frames: {fallback_frames}/{N_FRAMES}."
    return [
        ClipResult(
            filename=composite.name,
            source=str(H1_SALMON.relative_to(ROOT)),
            test="Cleaner salmon-school proxy: fewer fish centers, pale circle anchors, ordered primitive phrase leading along swim direction.",
            method="Stricter local-darkness segmentation, max 8 non-overlapping components, PCA/local-flow direction, low-opacity palette.",
            review_note="Composite includes filename/timecode burn-in from source footage; this is not added by the primitive renderer.",
            dynamic_note=dynamic,
        ),
        ClipResult(
            filename=layer.name,
            source="primitive layer only; timing/motion matched to H1 composite",
            test="Black-background salmon primitive layer for Resolume screen blend or additive mixing.",
            method="Same salmon detections and phrase positions rendered as light glyphs on black.",
            review_note="No source burn-in; intended for independent live mixing over clean footage.",
            dynamic_note=dynamic,
        ),
    ]


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
    rows = [(result, ffprobe(OUT_DIR / result.filename)) for result in results]
    lines = [
        "# Primitive Water Grammar v002 Review Packet - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. This packet continues the deterministic primitive-water lane: no SD, no LoRA, no prompt generation, no named chiefs/specific people, and no Austin-specific beings.",
        "",
        "## v001 -> v002 Changes",
        "",
        "- Kept the strongest two v001 directions: H6 ocean/kelp optical-flow and H1 salmon-school proxy.",
        "- Replaced debug gold/red semantics with a restrained ivory/pale-blue single-palette variant.",
        "- Lowered composite opacity so the source footage breathes.",
        "- Reduced visual density by roughly one third: H6 optical-flow anchors 12 -> 8; H1 salmon proxy max kept detections 12 -> 8 with wider spacing.",
        "- Preserved circle/crescent/crescent/trigon order in every phrase.",
        "- Added black-background primitive-layer-only clips for Resolume screen/additive blending independent of the footage.",
        "",
        "## Recommended Clip For Austin",
        "",
        "`01_ocean_kelp_optical_flow_v002_composite_H6_source_burnin.mp4` is the cleanest first review clip. It keeps the cultural load abstract, reads as water/current guidance, and avoids putting primitives directly on animal bodies. Follow it with the salmon proxy only for the specific acceptability question.",
        "",
        "## Source Burn-In Note",
        "",
        "The visible filename/timecode text in the composite clips is already present in the source footage. The primitive renderer did not add that burn-in. The layer-only black clips contain no source burn-in and are intended for Resolume mixing over cleaner footage.",
        "",
        "## Austin Questions",
        "",
        "- Should the circle lead or anchor behind motion?",
        "- Should crescents cup toward the impact point or face direction of travel?",
        "- Should trigons point with flow direction or mark final attenuation?",
        "- Is putting a circle over salmon body centers acceptable?",
        "",
        "## Clips",
        "",
    ]
    for result, probe in rows:
        rec = " Recommended first Austin clip." if result.recommended else ""
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}{rec}",
                f"- Source: `{result.source}`",
                f"- Review note: {result.review_note}",
                f"- Technical method: {result.method}",
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
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Water Grammar v002 review packet to {OUT_DIR}", flush=True)
    results: list[ClipResult] = []
    results.extend(render_ocean_kelp_v2())
    results.extend(render_salmon_school_v2())
    write_readme(results)
    print("Done. README includes ffprobe verification.", flush=True)


if __name__ == "__main__":
    main()
