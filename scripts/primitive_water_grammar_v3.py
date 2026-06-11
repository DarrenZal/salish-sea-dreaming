#!/usr/bin/env python3.11
"""
Primitive Water Grammar v003 polish packet.

Layer-only black-background studies for Resolume screen/additive mixing.
No SD, LoRA, SAM, YOLO, or new icon/scene generation.
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
    transform_points,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v003_2026-05-19"
FPS = 24
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"

# Ivory / pale-blue on pure black for Resolume Screen/Additive.
CIRCLE_RGB = (238, 231, 205)
CRESCENT_RGB = (205, 226, 232)
TRIGON_RGB = (170, 199, 214)
OUTLINE_RGB = (226, 238, 238)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    method: str
    resolume_note: str
    recommended: bool = False
    dynamic_note: str = ""


def black_canvas() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def draw_crescent(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(CRESCENT_BASE, center, size, angle),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.16,
        outline_thickness=1,
    )


def draw_trigon(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(TRIGON_BASE, center, size, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.14,
        outline_thickness=1,
    )


def draw_circle(frame: np.ndarray, center: tuple[float, float], radius: float, *, alpha: float) -> None:
    draw_circle_alpha(
        frame,
        center,
        radius,
        CIRCLE_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.12,
    )


def draw_phrase(
    frame: np.ndarray,
    start: tuple[float, float],
    angle: float,
    *,
    spacing: float,
    alpha: float,
    scale: float = 1.0,
    circle_alpha: float = 0.78,
    circle_radius: float = 9.0,
) -> None:
    """Render one clear circle/crescent/crescent/trigon sequence."""

    dx = math.cos(angle)
    dy = math.sin(angle)
    centers = [
        start,
        (start[0] + dx * spacing, start[1] + dy * spacing),
        (start[0] + dx * spacing * 1.72, start[1] + dy * spacing * 1.72),
        (start[0] + dx * spacing * 2.48, start[1] + dy * spacing * 2.48),
    ]
    draw_circle(frame, centers[0], circle_radius * scale, alpha=alpha * circle_alpha)
    draw_crescent(frame, centers[1], 29.0 * scale, angle, alpha=alpha)
    draw_crescent(frame, centers[2], 25.5 * scale, angle, alpha=alpha * 0.78)
    draw_trigon(frame, centers[3], 24.0 * scale, angle, alpha=alpha * 0.62)


def transform_points_aniso(base: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    scaled = base.copy()
    scaled[:, 0] *= sx
    scaled[:, 1] *= sy
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    pts = scaled @ rot.T
    pts[:, 0] += center[0]
    pts[:, 1] += center[1]
    return pts


def draw_flat_crescent(frame: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points_aniso(CRESCENT_BASE, center, sx, sy, angle),
        CRESCENT_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.10,
        outline_thickness=1,
    )


def render_kelp_current_layer_v3() -> ClipResult:
    out = OUT_DIR / "01_kelp_current_layer_only_v003_black_screen.mp4"
    reader = SampledVideo(H6_KELP, start_seconds=8.0)
    writer = H264Writer(out)
    # v002 used 8 phrase anchors. v003 uses 5 and a shared drift direction.
    anchors = [
        {"x": W * 0.18, "y": H * 0.33, "phase": 0.0},
        {"x": W * 0.37, "y": H * 0.45, "phase": 0.8},
        {"x": W * 0.56, "y": H * 0.39, "phase": 1.6},
        {"x": W * 0.73, "y": H * 0.54, "phase": 2.4},
        {"x": W * 0.43, "y": H * 0.70, "phase": 3.2},
    ]
    shared_angle = 0.10
    prev_raw = reader.frame(0)
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else np.zeros((270, 480, 2), dtype=np.float32)
        t = fi / FPS
        frame = black_canvas()
        # One common-fate vector with a small tide-like pulse.
        target_angle = 0.08 + 0.08 * math.sin(t * 0.55)
        shared_angle = smooth_angle(shared_angle, target_angle, amount=0.08)
        for anchor in anchors:
            dx, dy = sample_flow(flow, anchor["x"], anchor["y"])
            anchor["x"] += math.cos(shared_angle) * 0.30 + dx * 0.34
            anchor["y"] += math.sin(shared_angle) * 0.30 + dy * 0.34
            if anchor["x"] > W + 140:
                anchor["x"] = -110
            if anchor["x"] < -150:
                anchor["x"] = W + 110
            anchor["y"] += 0.10 * math.sin(t * 0.75 + anchor["phase"])
            if anchor["y"] < H * 0.20:
                anchor["y"] = H * 0.74
            elif anchor["y"] > H * 0.82:
                anchor["y"] = H * 0.26
            phrase_angle = smooth_angle(shared_angle, math.atan2(dy, dx) if math.hypot(dx, dy) > 0.30 else shared_angle, amount=0.12)
            pulse = 0.88 + 0.12 * math.sin(t * 1.1 + anchor["phase"])
            draw_phrase(frame, (anchor["x"], anchor["y"]), phrase_angle, spacing=44.0, alpha=0.58 * pulse, scale=1.0)
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            print(f"  kelp current v003 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    reader.close()
    return ClipResult(
        filename=out.name,
        source=str(H6_KELP.relative_to(ROOT)),
        test="Layer-only kelp/current grammar with five shared-direction C-Cr-Cr-T phrases.",
        method="H6 optical flow advects phrase anchors; orientation is biased to one common-fate current vector for cleaner water grammar.",
        resolume_note="Use Screen/Additive over H6 or clean kelp footage. Pure black background; no alpha channel required.",
        recommended=True,
    )


def detect_salmon_proxy_v3(frame: np.ndarray, flow: np.ndarray | None) -> list[dict[str, float]]:
    """Scaled v002-style local-darkness detection, kept sparse for layer use."""

    small_w, small_h = 960, 540
    scale_x = W / small_w
    scale_y = H / small_h
    small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    work = cv2.GaussianBlur(gray, (7, 7), 0)
    burn_h = int(small_h * 0.085)
    work[small_h - burn_h :, :] = 180
    bg = cv2.GaussianBlur(work, (0, 0), 23)
    score = cv2.subtract(bg, work)
    mask = ((score > 9) & (work < 150)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=1)
    num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)

    detections: list[dict[str, float]] = []
    for comp_idx in range(1, num):
        x, y, cw, ch, area = stats[comp_idx]
        touches_edge = x <= 2 or y <= 2 or x + cw >= small_w - 2 or y + ch >= small_h - burn_h - 2
        if touches_edge:
            continue
        aspect = cw / max(1, ch)
        extent = area / max(1, cw * ch)
        if not (210 <= area <= 14000 and 0.75 <= aspect <= 8.25 and 12 <= cw <= 260 and 7 <= ch <= 120 and extent > 0.12):
            continue
        cx_s, cy_s = float(cents[comp_idx][0]), float(cents[comp_idx][1])
        cx = cx_s * scale_x
        cy = cy_s * scale_y
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
                angle = smooth_angle(angle, math.atan2(dy, dx), amount=0.34)
        detections.append({"cx": cx, "cy": cy, "area": float(area) * scale_x * scale_y, "angle": angle})

    detections.sort(key=lambda d: d["area"], reverse=True)
    kept: list[dict[str, float]] = []
    for det in detections:
        if len(kept) >= 6:
            break
        if all(math.hypot(det["cx"] - prev["cx"], det["cy"] - prev["cy"]) > 210 for prev in kept):
            kept.append(det)
    return kept


def render_salmon_proxy_layer_v3() -> ClipResult:
    out = OUT_DIR / "02_salmon_proxy_layer_only_v003_black_screen.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    writer = H264Writer(out)
    prev_raw = reader.frame(0)
    detection_counts: list[int] = []
    fallback_frames = 0
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        frame = black_canvas()
        detections = detect_salmon_proxy_v3(raw, flow)
        detection_counts.append(len(detections))
        if len(detections) >= 2:
            for det in detections:
                cx, cy = det["cx"], det["cy"]
                angle = det["angle"]
                scale = max(0.70, min(1.22, math.sqrt(det["area"]) / 128.0))
                # Small/soft body-center circle: present enough to ask Austin,
                # but no longer visually dominates the fish.
                draw_circle(frame, (cx, cy), 5.8 * scale, alpha=0.34)
                phrase_start = (
                    cx + math.cos(angle) * 25.0 * scale,
                    cy + math.sin(angle) * 25.0 * scale,
                )
                draw_phrase(
                    frame,
                    phrase_start,
                    angle,
                    spacing=29.0 * scale,
                    alpha=0.43,
                    scale=scale,
                    circle_alpha=0.22,
                    circle_radius=5.5,
                )
        else:
            fallback_frames += 1
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            avg = sum(detection_counts[-48:]) / max(1, len(detection_counts[-48:]))
            print(f"  salmon proxy v003 {fi + 1}/{N_FRAMES} avg detections last block={avg:.1f}", flush=True)
    writer.close()
    reader.close()
    avg_det = sum(detection_counts) / max(1, len(detection_counts))
    return ClipResult(
        filename=out.name,
        source=str(H1_SALMON.relative_to(ROOT)),
        test="Layer-only salmon proxy with subtler body-center circles and six max ordered phrases.",
        method="Scaled v002-style local-darkness detection, PCA/local-flow direction, max 6 non-overlapping detections, small circle anchors.",
        resolume_note="Use Screen/Additive sparingly over salmon footage. This remains the clip to ask whether circles over salmon centers are acceptable.",
        dynamic_note=f"Average kept salmon-proxy components per frame: {avg_det:.1f}; fallback/no-detection frames: {fallback_frames}/{N_FRAMES}.",
    )


def render_single_droplet_v3() -> ClipResult:
    out = OUT_DIR / "03_single_droplet_ripple_study_v003_black_screen.mp4"
    writer = H264Writer(out)
    impacts = [
        {"start": 0.35, "center": (W * 0.48, H * 0.51), "scale": 1.0, "dirs": 7},
        {"start": 2.60, "center": (W * 0.68, H * 0.42), "scale": 0.62, "dirs": 5},
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for impact in impacts:
            age = t - impact["start"]
            if age < 0.0 or age > 3.4:
                continue
            cx, cy = impact["center"]
            scale = impact["scale"]
            flash = max(0.0, 1.0 - age / 0.92)
            draw_circle(frame, (cx, cy), (10.0 + 7.0 * math.sin(age * 4.0)) * scale, alpha=0.50 * flash)
            dirs = impact["dirs"]
            for ray in range(dirs):
                angle = -0.15 + ray * (2.0 * math.pi / dirs)
                ray_phase = ray * 0.035
                local_age = age - ray_phase
                if local_age <= 0.0:
                    continue
                # Ease-out expansion: quick birth, slow attenuation.
                u = min(1.0, local_age / 2.65)
                ease = math.sqrt(max(0.0, 1.0 - (1.0 - u) * (1.0 - u)))
                base_r = (38.0 + 135.0 * ease) * scale
                alpha = 0.46 * ((1.0 - u) ** 1.35) * scale
                if alpha <= 0.02:
                    continue
                for idx, (kind, offset, size) in enumerate(
                    [
                        ("crescent", 0.0, 30.0),
                        ("crescent", 48.0, 25.0),
                        ("trigon", 94.0, 23.0),
                    ]
                ):
                    r = base_r + offset * scale
                    px = cx + math.cos(angle) * r
                    py = cy + math.sin(angle) * r
                    if kind == "crescent":
                        draw_crescent(frame, (px, py), size * scale, angle, alpha=alpha * (0.86 - idx * 0.10))
                    else:
                        draw_trigon(frame, (px, py), size * scale, angle, alpha=alpha * 0.58)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  droplet ripple v003 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural black-layer study",
        test="Still-pond ripple grammar: impact circle, outward crescents, trigons as final attenuation.",
        method="Two deterministic impact events; sparse radial C/Cr/Cr/T expansion with ease-out fade.",
        resolume_note="Use Screen/Additive over still water, mist, or as an abstract transition. Pure black background.",
        recommended=True,
    )


def render_long_swell_v3() -> ClipResult:
    out = OUT_DIR / "04_long_swell_horizon_crescents_v003_black_screen.mp4"
    writer = H264Writer(out)
    swells = [
        (0.18, H * 0.42, 0.0, 0.82),
        (0.44, H * 0.46, 1.4, 0.62),
        (0.72, H * 0.50, 2.7, 0.52),
        (0.30, H * 0.56, 3.1, 0.50),
        (0.60, H * 0.61, 4.0, 0.42),
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for x_norm, y_base, phase, amp in swells:
            x = (x_norm * W + 44.0 * math.sin(t * 0.22 + phase)) % W
            y = y_base + 10.0 * math.sin(t * 0.70 + phase)
            alpha = 0.22 + 0.13 * amp * (0.5 + 0.5 * math.sin(t * 0.43 + phase))
            draw_flat_crescent(frame, (x, y), 360.0 * amp, 16.0 * amp, 0.0, alpha=alpha)
        writer.write(frame)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural black-layer study",
        test="Optional long-swell crescent horizon: nearly still shared wave direction.",
        method="Five flattened crescents with slow shared lateral/vertical swell phase.",
        resolume_note="Use Screen/Additive at low opacity as a horizon/current bed.",
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


def save_midpoint_stills(results: Iterable[ClipResult]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[np.ndarray] = []
    labels: list[str] = []
    for result in results:
        path = OUT_DIR / result.filename
        cap = cv2.VideoCapture(str(path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        still = MIDPOINT_DIR / f"{Path(result.filename).stem}_midpoint.jpg"
        cv2.imwrite(str(still), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(result.filename).stem[:46], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        thumbs.append(thumb)
        labels.append(still.name)
    if thumbs:
        if len(thumbs) == 1:
            sheet = thumbs[0]
        else:
            rows = []
            for i in range(0, len(thumbs), 2):
                row = thumbs[i : i + 2]
                if len(row) == 1:
                    row.append(np.zeros_like(row[0]))
                rows.append(cv2.hconcat(row))
            sheet = cv2.vconcat(rows)
        cv2.imwrite(str(OUT_DIR / "contact_sheet_midpoints.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])


def nonblank_stats(results: Iterable[ClipResult]) -> dict[str, str]:
    stats: dict[str, str] = {}
    for result in results:
        cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            stats[result.filename] = "midpoint read failed"
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        stats[result.filename] = f"midpoint max luma {int(gray.max())}, nonblack pixels {(gray > 2).sum()}"
    return stats


def write_readme(results: list[ClipResult]) -> None:
    probes = [(result, ffprobe(OUT_DIR / result.filename)) for result in results]
    stats = nonblank_stats(results)
    lines = [
        "# Primitive Water Grammar v003 Polish Packet - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Deterministic layer-only studies; no SD, LoRA, SAM, YOLO, named chiefs/specific people, or new whale/tanker/icon scenes.",
        "",
        "## v002 -> v003 Changes",
        "",
        "- Focused on black-background layer-only clips for Resolume Screen/Additive mixing.",
        "- Reduced marker-like feeling by using fewer phrases, wider spacing, shared direction, and cleaner C/Cr/Cr/T sequencing.",
        "- Kelp/current: 8 v002 anchors -> 5 v003 phrases, with local flow used mostly for drift and a shared current vector for common-fate motion.",
        "- Salmon proxy: max 8 v002 detections -> max 6 v003 detections; body-center circles are smaller and lower opacity.",
        "- Added a pure procedural single-droplet ripple study to make Austin's water-cycle grammar explicit without animal/body placement.",
        "- Added midpoint stills and a contact sheet for quick review.",
        "",
        "## Which Clip Should Lead Austin Review",
        "",
        "`03_single_droplet_ripple_study_v003_black_screen.mp4` should lead. It is the cleanest test of the grammar itself: circle impact, crescents ripple outward, trigons mark final attenuation. Then show `01_kelp_current_layer_only_v003_black_screen.mp4` as the footage-driven current version. Use the salmon proxy only for the body-center acceptability question.",
        "",
        "## Resolume Screen/Additive Mixing Notes",
        "",
        "- All clips are RGB H.264 MP4 on pure `#000000`; no alpha channel is required.",
        "- Set blend mode to Screen or Additive in Resolume. Start clip opacity around 35-55% over footage, then raise only if the primitives disappear in projection.",
        "- The black screen should vanish under Screen blend. If it hazes, check that downstream color/gamma effects are not lifting black.",
        "- H.264 is fine for review; convert to DXV/HAP later for show playback/scrubbing if needed.",
        "",
        "## Austin Questions",
        "",
        "- Should the circle lead or anchor behind motion?",
        "- Should crescents cup toward the impact point or face direction of travel?",
        "- Should trigons point with flow direction or mark final attenuation?",
        "- Is putting a circle over salmon body centers acceptable if it is subtle?",
        "- Does the single-droplet study match the pond/ripple grammar Austin described?",
        "",
        "## Clips",
        "",
    ]
    for result, probe in probes:
        rec = " Recommended lead clip." if result.recommended and result.filename.startswith("03_") else ""
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}{rec}",
                f"- Source: `{result.source}`",
                f"- Technical method: {result.method}",
                f"- Resolume note: {result.resolume_note}",
            ]
        )
        if result.dynamic_note:
            lines.append(f"- Runtime note: {result.dynamic_note}")
        lines.extend(
            [
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                f"- Nonblank check: {stats.get(result.filename, 'not checked')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Review Stills",
            "",
            "- Midpoint stills: `midpoint_stills/`",
            "- Contact sheet: `contact_sheet_midpoints.jpg`",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Water Grammar v003 polish packet to {OUT_DIR}", flush=True)
    results = [
        render_kelp_current_layer_v3(),
        render_salmon_proxy_layer_v3(),
        render_single_droplet_v3(),
        render_long_swell_v3(),
    ]
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
