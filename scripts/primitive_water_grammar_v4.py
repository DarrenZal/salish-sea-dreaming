#!/usr/bin/env python3.11
"""
Primitive Water Grammar v004.

Layer-only black-background clips focused on:
  - articulated primitive fish built from trigon/crescent/circle grammar
  - perspective water/ripple planes and continuous current sheets

No SD, LoRA, SAM, YOLO, or new named/icon scene generation.
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


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v004_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
FPS = 24

# RGB palette for black-screen Screen/Additive use.
CIRCLE_RGB = (238, 231, 205)    # ivory
CRESCENT_RGB = (205, 226, 232)  # pale blue
TRIGON_RGB = (170, 199, 214)    # deeper blue-grey
OUTLINE_RGB = (228, 238, 238)


@dataclass(frozen=True)
class ClipResult:
    filename: str
    source: str
    test: str
    method: str
    layer_role: str
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
        outline_alpha=alpha * 0.12,
        outline_thickness=1,
    )


def draw_trigon(frame: np.ndarray, center: tuple[float, float], size: float, angle: float, *, alpha: float) -> None:
    draw_poly_alpha(
        frame,
        transform_points(TRIGON_BASE, center, size, angle),
        TRIGON_RGB,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.12,
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
        outline_alpha=alpha * 0.10,
    )


def rotate_translate(local: tuple[float, float], center: tuple[float, float], angle: float) -> tuple[float, float]:
    x, y = local
    c = math.cos(angle)
    s = math.sin(angle)
    return (center[0] + x * c - y * s, center[1] + x * s + y * c)


def spine_local(d: float, length: float, phase: float, bend: float) -> tuple[float, float, float]:
    """Return local x/y/tangent angle along head(0) -> tail(1)."""

    x = (0.48 - d) * length
    wave = math.sin(phase - d * 1.75)
    y = bend * length * (d ** 1.35) * wave
    # Derivative in local coordinates. x decreases as d increases.
    dy_dd = bend * length * (
        1.35 * (d ** 0.35) * wave - 1.75 * (d ** 1.35) * math.cos(phase - d * 1.75)
    )
    dx_dd = -length
    tangent = math.atan2(dy_dd, dx_dd) + math.pi
    return x, y, tangent


def draw_articulated_fish(
    frame: np.ndarray,
    center: tuple[float, float],
    length: float,
    angle: float,
    phase: float,
    *,
    alpha: float = 0.72,
    circle_body_alpha: float = 0.40,
    bend: float = 0.095,
) -> None:
    """Primitive fish: trigon head -> crescent gill -> circle body -> tapering crescents -> trigon tail."""

    parts = [
        ("tail", 0.96, 0.102, 0.66),
        ("crescent", 0.78, 0.100, 0.46),
        ("crescent", 0.63, 0.118, 0.52),
        ("crescent", 0.49, 0.132, 0.58),
        ("circle", 0.34, 0.078, circle_body_alpha),
        ("gill", 0.19, 0.112, 0.60),
        ("head", 0.04, 0.110, 0.70),
    ]
    for kind, d, size_mul, part_alpha in parts:
        lx, ly, tangent = spine_local(d, length, phase, bend)
        pos = rotate_translate((lx, ly), center, angle)
        orient = angle + tangent
        if kind == "head":
            draw_trigon(frame, pos, length * size_mul, orient, alpha=alpha * part_alpha)
        elif kind == "tail":
            draw_trigon(frame, pos, length * size_mul, orient + math.pi, alpha=alpha * part_alpha)
        elif kind == "circle":
            draw_circle(frame, pos, length * size_mul, alpha=alpha * part_alpha)
        elif kind == "gill":
            draw_crescent(frame, pos, length * size_mul, orient + 0.10, alpha=alpha * part_alpha)
        else:
            draw_crescent(frame, pos, length * size_mul, orient, alpha=alpha * part_alpha)


def transform_points_aniso(base: np.ndarray, center: tuple[float, float], sx: float, sy: float, angle: float) -> np.ndarray:
    scaled = base.copy()
    scaled[:, 0] *= sx
    scaled[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
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
        outline_alpha=alpha * 0.08,
        outline_thickness=1,
    )


def render_articulated_fish_glyph() -> ClipResult:
    out = OUT_DIR / "01_articulated_fish_glyph_v004_black_screen.mp4"
    writer = H264Writer(out)
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        phase = 2.0 * math.pi * t / 1.85
        center = (W * 0.50 + 20.0 * math.sin(t * 0.50), H * 0.50 + 10.0 * math.sin(t * 0.80))
        draw_articulated_fish(frame, center, 430.0, 0.0, phase, alpha=0.78, circle_body_alpha=0.34, bend=0.105)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  articulated fish glyph v004 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural primitive fish study",
        test="Standalone grammar-built fish with trigon head, crescent gill, circle body/joint, tapering crescent body, trigon tail.",
        method="One articulated spine with sine-wave phase lag; each primitive samples the curved spine tangent, so the tail flexes rather than translating as a rigid phrase.",
        layer_role="Fish figure study. Show before applying to H1-derived positions so Austin can judge the grammar-built figure by itself.",
    )


def detect_salmon_proxy_v4(frame: np.ndarray, flow: np.ndarray | None) -> list[dict[str, float]]:
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
                angle = smooth_angle(angle, math.atan2(dy, dx), amount=0.30)
        detections.append({"cx": cx, "cy": cy, "area": float(area) * scale_x * scale_y, "angle": angle})

    detections.sort(key=lambda d: d["area"], reverse=True)
    kept: list[dict[str, float]] = []
    for det in detections:
        if len(kept) >= 5:
            break
        if all(math.hypot(det["cx"] - prev["cx"], det["cy"] - prev["cy"]) > 235 for prev in kept):
            kept.append(det)
    return kept


def render_salmon_proxy_articulated() -> ClipResult:
    out = OUT_DIR / "02_salmon_proxy_articulated_v004_black_screen.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    writer = H264Writer(out)
    prev_raw = reader.frame(0)
    counts: list[int] = []
    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        frame = black_canvas()
        t = fi / FPS
        detections = detect_salmon_proxy_v4(raw, flow)
        counts.append(len(detections))
        for det in detections:
            length = max(105.0, min(255.0, math.sqrt(det["area"]) * 1.42))
            phase = 2.0 * math.pi * t / 1.65 + (det["cx"] * 0.013 + det["cy"] * 0.007)
            draw_articulated_fish(
                frame,
                (det["cx"], det["cy"]),
                length,
                det["angle"],
                phase,
                alpha=0.56,
                circle_body_alpha=0.28,
                bend=0.095,
            )
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            avg = sum(counts[-48:]) / max(1, len(counts[-48:]))
            print(f"  salmon proxy articulated v004 {fi + 1}/{N_FRAMES} avg detections={avg:.1f}", flush=True)
    writer.close()
    reader.close()
    avg_det = sum(counts) / max(1, len(counts))
    return ClipResult(
        filename=out.name,
        source=str(H1_SALMON.relative_to(ROOT)),
        test="H1-derived articulated primitive fish layer with curved-spine flex instead of rigid marker phrases.",
        method="Scaled local-darkness detection supplies positions/directions; each kept detection renders a sine-bending primitive fish with subtle circle body.",
        layer_role="Fish layer only. Keep separate from water layers in Resolume so fish grammar and water grammar can be accepted/tuned independently.",
        dynamic_note=f"Average kept H1-derived positions per frame: {avg_det:.1f}.",
    )


class PlaneProjector:
    def __init__(self) -> None:
        src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
        dst = np.array(
            [
                [W * 0.30, H * 0.23],
                [W * 0.70, H * 0.23],
                [W * 0.93, H * 0.86],
                [W * 0.07, H * 0.86],
            ],
            dtype=np.float32,
        )
        self.mat = cv2.getPerspectiveTransform(src, dst)

    def project(self, pts: np.ndarray) -> np.ndarray:
        shaped = pts.reshape(-1, 1, 2).astype(np.float32)
        projected = cv2.perspectiveTransform(shaped, self.mat)
        return projected.reshape(-1, 2)


def unit_circle_points(samples: int = 80) -> np.ndarray:
    return np.array(
        [(math.cos(2.0 * math.pi * i / samples), math.sin(2.0 * math.pi * i / samples)) for i in range(samples)],
        dtype=np.float32,
    )


CIRCLE_BASE = unit_circle_points()


def draw_plane_shape(
    frame: np.ndarray,
    projector: PlaneProjector,
    base: np.ndarray,
    center_uv: tuple[float, float],
    sx: float,
    sy: float,
    angle: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
) -> None:
    local = base.copy()
    local[:, 0] *= sx
    local[:, 1] *= sy
    c = math.cos(angle)
    s = math.sin(angle)
    rot = np.array([[c, -s], [s, c]], dtype=np.float32)
    uv = local @ rot.T
    uv[:, 0] += center_uv[0]
    uv[:, 1] += center_uv[1]
    pts = projector.project(uv)
    draw_poly_alpha(
        frame,
        pts,
        rgb,
        alpha=alpha,
        outline_rgb=OUTLINE_RGB,
        outline_alpha=alpha * 0.08,
        outline_thickness=1,
    )


def render_perspective_ripple_plane() -> ClipResult:
    out = OUT_DIR / "03_perspective_ripple_plane_v004_black_screen.mp4"
    writer = H264Writer(out)
    projector = PlaneProjector()
    impacts = [
        {"start": 0.20, "uv": (0.42, 0.58), "scale": 1.0, "dirs": 7},
        {"start": 2.85, "uv": (0.64, 0.40), "scale": 0.65, "dirs": 5},
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for impact in impacts:
            age = t - impact["start"]
            if age < 0.0 or age > 3.35:
                continue
            u, v = impact["uv"]
            scale = impact["scale"]
            flash = max(0.0, 1.0 - age / 0.85)
            draw_plane_shape(
                frame,
                projector,
                CIRCLE_BASE,
                (u, v),
                0.013 * scale,
                0.013 * scale,
                0.0,
                CIRCLE_RGB,
                alpha=0.52 * flash,
            )
            for ray in range(impact["dirs"]):
                angle = -0.08 + ray * 2.0 * math.pi / impact["dirs"]
                local_age = age - ray * 0.028
                if local_age <= 0.0:
                    continue
                q = min(1.0, local_age / 2.65)
                ease = math.sqrt(max(0.0, 1.0 - (1.0 - q) ** 2))
                base_r = (0.030 + 0.170 * ease) * scale
                alpha = 0.44 * ((1.0 - q) ** 1.28) * scale
                if alpha < 0.025:
                    continue
                for idx, (kind, extra, sx, sy) in enumerate(
                    [
                        ("crescent", 0.000, 0.029, 0.020),
                        ("crescent", 0.042, 0.024, 0.017),
                        ("trigon", 0.084, 0.019, 0.019),
                    ]
                ):
                    r = base_r + extra * scale
                    cu = u + math.cos(angle) * r
                    cv = v + math.sin(angle) * r
                    if not (-0.04 <= cu <= 1.04 and -0.04 <= cv <= 1.04):
                        continue
                    if kind == "crescent":
                        draw_plane_shape(frame, projector, CRESCENT_BASE, (cu, cv), sx * scale, sy * scale, angle, CRESCENT_RGB, alpha=alpha * (0.86 - idx * 0.08))
                    else:
                        draw_plane_shape(frame, projector, TRIGON_BASE, (cu, cv), sx * scale, sy * scale, angle, TRIGON_RGB, alpha=alpha * 0.58)
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  perspective ripple plane v004 {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural perspective water-plane study",
        test="Droplet/ripple grammar projected onto a tilted water plane.",
        method="Primitive circles/crescents/trigons are authored in plane UV space and projected through a homography into screen perspective.",
        layer_role="Water layer. Designed to sit under/behind fish layers as river, ocean, or lake surface grammar.",
    )


def render_current_sheet() -> ClipResult:
    out = OUT_DIR / "04_current_sheet_v004_black_screen.mp4"
    writer = H264Writer(out)
    bands = [
        (H * 0.27, 0.00, 0.62),
        (H * 0.39, 1.10, 0.74),
        (H * 0.52, 2.00, 0.88),
        (H * 0.66, 2.85, 0.66),
        (H * 0.77, 3.50, 0.50),
    ]
    for fi in range(N_FRAMES):
        t = fi / FPS
        frame = black_canvas()
        for band_idx, (y_base, phase, alpha_scale) in enumerate(bands):
            shared = 0.04 + 0.05 * math.sin(t * 0.42 + phase)
            for phrase_idx in range(3):
                x = ((phrase_idx * 0.36 + 0.07 * band_idx + t * 0.035) % 1.16 - 0.08) * W
                y = y_base + 24.0 * math.sin((x / W) * 2.0 * math.pi + t * 0.75 + phase)
                angle = shared + 0.11 * math.cos((x / W) * 2.0 * math.pi + phase)
                a = 0.34 * alpha_scale
                # Small circle initiation, then overlapping long crescents and a final trigon.
                draw_circle(frame, (x, y), 4.5, alpha=a * 0.36)
                draw_flat_crescent(frame, (x + 78.0, y + 5.0), 84.0, 10.0, angle, alpha=a * 0.90)
                draw_flat_crescent(frame, (x + 158.0, y + 8.0), 104.0, 12.0, angle, alpha=a * 0.70)
                draw_trigon(frame, (x + 276.0, y + 10.0), 20.0, angle, alpha=a * 0.42)
        writer.write(frame)
    writer.close()
    return ClipResult(
        filename=out.name,
        source="pure procedural current sheet study",
        test="Continuous wave/current sheet, distinct from fish layer and less marker-like.",
        method="Five common-fate horizontal bands with overlapping elongated crescents, tiny initiation circles, and attenuated trigons.",
        layer_role="Water/current layer. Screen/Additive under fish or over footage to suggest shared water motion.",
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


def midpoint_stats(result: ClipResult) -> str:
    cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "midpoint read failed"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return f"midpoint max luma {int(gray.max())}, nonblack pixels {int((gray > 2).sum())}"


def save_midpoint_stills(results: Iterable[ClipResult]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[np.ndarray] = []
    for result in results:
        cap = cv2.VideoCapture(str(OUT_DIR / result.filename))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        cv2.imwrite(str(MIDPOINT_DIR / f"{Path(result.filename).stem}_midpoint.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, Path(result.filename).stem[:46], (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (230, 230, 230), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    if thumbs:
        rows = []
        for i in range(0, len(thumbs), 2):
            row = thumbs[i : i + 2]
            if len(row) == 1:
                row.append(np.zeros_like(row[0]))
            rows.append(cv2.hconcat(row))
        cv2.imwrite(str(OUT_DIR / "contact_sheet_midpoints.jpg"), cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 92])


def write_readme(results: list[ClipResult]) -> None:
    rows = [(result, ffprobe(OUT_DIR / result.filename), midpoint_stats(result)) for result in results]
    lines = [
        "# Primitive Water Grammar v004 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Layer-only black-background clips; no SD, LoRA, SAM, YOLO, named chiefs/specific people, or new whale/tanker/icon scenes.",
        "",
        "## Fish Layer vs Water Layer",
        "",
        "- Fish layers (`01`, `02`) test whether the primitives can build a new fish-like figure without transforming a named/specific being. The figure is articulated on a curved spine: trigon head, crescent gill/neck, circle body/joint, tapering crescents, trigon tail.",
        "- Water layers (`03`, `04`) test surface grammar independent of fish: perspective ripple planes and continuous current sheets. These should remain independently mixable in Resolume so fish acceptance and water acceptance can be judged separately.",
        "",
        "## v003 -> v004 Changes",
        "",
        "- Replaced rigid salmon marker phrases with articulated primitive fish glyphs.",
        "- Added sine-wave spine bending and tail phase lag so the fish flexes rather than translating as one rigid phrase.",
        "- Made the fish body ordering explicit: trigon head -> crescent gill -> circle body/joint -> tapering crescents -> trigon tail.",
        "- Converted the droplet/ripple study into a tilted perspective plane, so the same ripple grammar can represent river/ocean/lake surfaces.",
        "- Added a current sheet that reads as water motion, distinct from fish markers.",
        "",
        "## Austin Questions",
        "",
        "- Does this articulated primitive fish feel acceptable as a new grammar-built figure?",
        "- Is trigon head / circle body / crescent body / trigon tail a better ordering?",
        "- Should water surfaces be flat head-on, or can we use perspective planes?",
        "- Should fish and water remain separate layers in Resolume?",
        "",
        "## Resolume Notes",
        "",
        "- All clips are RGB H.264 MP4 on pure black. Use Screen/Additive blend mode; no alpha channel required.",
        "- Start water layers around 35-55% opacity over footage. Start fish layers lower until Austin signs off on the grammar-built figure.",
        "- Keep fish and water clips in separate Resolume layers for review; this preserves a clear approval boundary.",
        "",
        "## Clips",
        "",
    ]
    for result, probe, stats in rows:
        lines.extend(
            [
                f"### {result.filename}",
                "",
                f"- What it tests: {result.test}",
                f"- Source: `{result.source}`",
                f"- Technical method: {result.method}",
                f"- Layer role: {result.layer_role}",
            ]
        )
        if result.dynamic_note:
            lines.append(f"- Runtime note: {result.dynamic_note}")
        lines.extend(
            [
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                f"- Nonblank check: {stats}",
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
    print(f"Writing Primitive Water Grammar v004 to {OUT_DIR}", flush=True)
    results = [
        render_articulated_fish_glyph(),
        render_salmon_proxy_articulated(),
        render_perspective_ripple_plane(),
        render_current_sheet(),
    ]
    save_midpoint_stills(results)
    write_readme(results)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
