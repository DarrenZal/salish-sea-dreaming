#!/usr/bin/env python3.11
"""
Primitive field cycle v003.

Combines the clean procedural circle -> crescent -> crescent -> trigon
transformation from primitive_cycle_motion_v002 with the field-scale energy of
primitive_field_v001 and primitive_field_v002_flocking_dark/light. This pass is
not a single-glyph proof: it renders many morphing primitive cycles on authored
common-fate current ribbons with deterministic phase offsets and no random
scatter.

Internal R&D only. Not Austin-approved. No SD, LoRA, animals, fish, topology,
cymatics, seed-of-life construction, or Austin source artwork.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from primitive_cycle_motion_v002 import (
    DEBUG_RGB,
    DIM_RGB,
    DURATION_SECONDS,
    FPS,
    H,
    LABEL_RGB,
    MID_FRAME,
    N_FRAMES,
    ROOT,
    W,
    draw_arrow_debug,
    draw_circle_additive,
    draw_path_additive,
    draw_poly_additive,
    draw_text,
    morph_base_for_phase,
    transform_points,
)


OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "primitive_field_cycle_v003_2026-05-20"
)

V001_MP4 = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4"
V002_DARK_MP4 = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4"
V002_LIGHT_MP4 = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light.mp4"
SINGLE_V002_MP4 = (
    ROOT
    / "track2-deterministic/morph_outputs_INTERNAL/primitive_cycle_motion_v002_2026-05-20/single_shape_cycle_v002.mp4"
)

IVORY = (236, 241, 232)
GOLD = (255, 202, 96)
RED = (220, 93, 64)
TEAL = (91, 183, 196)


@dataclass(frozen=True)
class Ribbon:
    ribbon_id: str
    p0: tuple[float, float]
    p1: tuple[float, float]
    p2: tuple[float, float]
    p3: tuple[float, float]
    count: int
    normal_offset: float
    phase_offset: float
    speed: float
    scale: float
    alpha: float


RIBBONS = [
    Ribbon(
        "r0",
        (-210.0, H * 0.27),
        (W * 0.22, H * 0.15),
        (W * 0.58, H * 0.38),
        (W + 190.0, H * 0.21),
        9,
        -34.0,
        0.02,
        0.050,
        0.78,
        0.55,
    ),
    Ribbon(
        "r1",
        (-180.0, H * 0.40),
        (W * 0.22, H * 0.55),
        (W * 0.64, H * 0.25),
        (W + 170.0, H * 0.48),
        10,
        22.0,
        0.16,
        0.043,
        0.84,
        0.58,
    ),
    Ribbon(
        "r2",
        (-220.0, H * 0.57),
        (W * 0.18, H * 0.43),
        (W * 0.64, H * 0.75),
        (W + 210.0, H * 0.58),
        10,
        -20.0,
        0.31,
        0.046,
        0.88,
        0.60,
    ),
    Ribbon(
        "r3",
        (-160.0, H * 0.72),
        (W * 0.29, H * 0.89),
        (W * 0.66, H * 0.56),
        (W + 160.0, H * 0.77),
        9,
        30.0,
        0.48,
        0.040,
        0.78,
        0.54,
    ),
    Ribbon(
        "r4",
        (W * 0.08, H + 120.0),
        (W * 0.18, H * 0.76),
        (W * 0.37, H * 0.25),
        (W * 0.50, -120.0),
        7,
        24.0,
        0.64,
        0.035,
        0.68,
        0.46,
    ),
    Ribbon(
        "r5",
        (W * 0.87, -100.0),
        (W * 0.75, H * 0.25),
        (W * 0.66, H * 0.68),
        (W * 0.83, H + 130.0),
        7,
        -26.0,
        0.79,
        0.036,
        0.66,
        0.44,
    ),
]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def edge_fade(s: float) -> float:
    return smoothstep(min(s / 0.10, (1.0 - s) / 0.10))


def bezier_point(ribbon: Ribbon, t: float) -> tuple[float, float]:
    u = 1.0 - t
    return (
        u * u * u * ribbon.p0[0]
        + 3.0 * u * u * t * ribbon.p1[0]
        + 3.0 * u * t * t * ribbon.p2[0]
        + t * t * t * ribbon.p3[0],
        u * u * u * ribbon.p0[1]
        + 3.0 * u * u * t * ribbon.p1[1]
        + 3.0 * u * t * t * ribbon.p2[1]
        + t * t * t * ribbon.p3[1],
    )


def bezier_angle(ribbon: Ribbon, t: float) -> float:
    u = 1.0 - t
    dx = (
        3.0 * u * u * (ribbon.p1[0] - ribbon.p0[0])
        + 6.0 * u * t * (ribbon.p2[0] - ribbon.p1[0])
        + 3.0 * t * t * (ribbon.p3[0] - ribbon.p2[0])
    )
    dy = (
        3.0 * u * u * (ribbon.p1[1] - ribbon.p0[1])
        + 6.0 * u * t * (ribbon.p2[1] - ribbon.p1[1])
        + 3.0 * t * t * (ribbon.p3[1] - ribbon.p2[1])
    )
    return math.atan2(dy, dx)


def path_points(ribbon: Ribbon, samples: int = 96) -> list[tuple[float, float]]:
    return [bezier_point(ribbon, i / (samples - 1)) for i in range(samples)]


def new_frame() -> np.ndarray:
    return np.zeros((H, W, 3), dtype=np.uint8)


def draw_background(frame: np.ndarray, phase: float) -> None:
    # Very dark, not decorative: just enough low-frequency current energy to
    # support the authored field without turning it into random particles.
    overlay = np.zeros_like(frame)
    for y in range(0, H, 42):
        a = 0.016 + 0.010 * math.sin(math.tau * (phase + y / H * 0.27))
        color = (10, 28 + int(10 * a * 60), 33)
        cv2.line(overlay, (0, y), (W, y + int(16 * math.sin(y * 0.013))), color, 1, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.52, frame, 1.0, 0, dst=frame)


def glyph_phase(ribbon: Ribbon, glyph_idx: int, s: float, field_phase: float) -> float:
    row_wave = 0.09 * math.sin(math.tau * (field_phase + glyph_idx * 0.073 + ribbon.phase_offset))
    return (field_phase * 1.10 + ribbon.phase_offset + glyph_idx * 0.087 + s * 0.42 + row_wave) % 1.0


def draw_field(debug: bool, fi: int) -> np.ndarray:
    frame = new_frame()
    phase = fi / N_FRAMES
    draw_background(frame, phase)

    for ribbon in RIBBONS:
        pts = path_points(ribbon)
        draw_path_additive(frame, pts, DIM_RGB, alpha=0.090 if debug else 0.040, thickness=2 if debug else 1)
        origin = bezier_point(ribbon, 0.08)
        if debug:
            angle = bezier_angle(ribbon, 0.16)
            end = (origin[0] + math.cos(angle) * 115.0, origin[1] + math.sin(angle) * 115.0)
            draw_circle_additive(frame, origin, 5.5, DEBUG_RGB, alpha=0.42, glow=0.02, outline_alpha=0.0)
            draw_arrow_debug(frame, origin, end, DEBUG_RGB)
            draw_text(frame, f"{ribbon.ribbon_id} origin/common-fate current", (round(origin[0] + 12), round(origin[1] - 10)), DEBUG_RGB, scale=0.38)

        for glyph_idx in range(ribbon.count):
            base_s = (glyph_idx + 0.50) / ribbon.count
            flow_s = (base_s + ribbon.speed * phase) % 1.0
            angle = bezier_angle(ribbon, flow_s)
            normal = (-math.sin(angle), math.cos(angle))
            wave = math.sin(math.tau * (phase * 0.55 + glyph_idx * 0.13 + ribbon.phase_offset))
            offset = ribbon.normal_offset + wave * 10.0
            center = bezier_point(ribbon, flow_s)
            center = (center[0] + normal[0] * offset, center[1] + normal[1] * offset)

            if center[0] < -140 or center[0] > W + 140 or center[1] < -140 or center[1] > H + 140:
                continue

            cycle_phase = glyph_phase(ribbon, glyph_idx, flow_s, phase)
            base, rgb, state_label = morph_base_for_phase(cycle_phase)
            pulse = 0.86 + 0.14 * math.sin(math.tau * (phase + glyph_idx * 0.17 + ribbon.phase_offset))
            size = 72.0 * ribbon.scale * (0.90 + 0.12 * edge_fade(flow_s)) * pulse
            alpha = ribbon.alpha * (0.52 + 0.42 * edge_fade(flow_s)) * (0.88 + 0.12 * pulse)
            spin = math.radians(8.0 * math.sin(math.tau * (cycle_phase + ribbon.phase_offset)))
            pts_glyph = transform_points(base, center, size, size, angle + spin)
            draw_poly_additive(frame, pts_glyph, rgb, alpha=alpha, glow=0.050 * alpha, outline_alpha=0.055)

            # Tiny anchor dot preserves origin/field legibility at scale.
            if cycle_phase < 0.10 or cycle_phase > 0.92:
                draw_circle_additive(frame, center, 2.8, GOLD, alpha=0.18, glow=0.015, outline_alpha=0.0)

            if debug and glyph_idx in (0, ribbon.count // 2):
                draw_text(
                    frame,
                    f"{ribbon.ribbon_id}.{glyph_idx} {state_label}",
                    (round(center[0] + 10), round(center[1] + 16)),
                    LABEL_RGB,
                    scale=0.34,
                )

    if debug:
        draw_text(frame, "primitive_field_cycle_v003", (70, 76), LABEL_RGB, scale=0.50)
        draw_text(frame, "many clean circle -> crescent -> crescent -> trigon cycles", (70, 112), LABEL_RGB, scale=0.42)
        draw_text(frame, "authored current ribbons, shared tangent, deterministic phase offsets, no random scatter", (70, 146), DEBUG_RGB, scale=0.42)
    return frame


class H264Writer:
    def __init__(self, path: Path) -> None:
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
            f"{W}x{H}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-frames:v",
            str(N_FRAMES),
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

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        self.proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed for {self.path} with exit code {rc}")


def save_png(path: Path, frame: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), frame)
    if not ok:
        raise RuntimeError(f"Could not write {path}")


def render_v003() -> Path:
    out_mp4 = OUT_DIR / "primitive_field_cycle_v003.mp4"
    writer = H264Writer(out_mp4)
    samples = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    for fi in range(N_FRAMES):
        frame = draw_field(False, fi)
        writer.write(frame)
        if fi in samples:
            save_png(OUT_DIR / "sample_stills" / f"primitive_field_cycle_v003_f{fi:03d}.png", frame)
        if (fi + 1) % 48 == 0:
            print(f"  primitive_field_cycle_v003: {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    save_png(OUT_DIR / "primitive_field_cycle_v003_midpoint_f072.png", draw_field(False, MID_FRAME))
    save_png(OUT_DIR / "primitive_field_cycle_v003_debug_midpoint_f072.png", draw_field(True, MID_FRAME))
    return out_mp4


def sample_video(path: Path, frac: float) -> np.ndarray:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        draw_text(frame, f"missing: {path.name}", (70, 90), RED, scale=0.60)
        return frame
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    idx = int(round(clamp01(frac) * (frame_count - 1)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        draw_text(frame, f"unreadable: {path.name}", (70, 90), RED, scale=0.60)
        return frame
    if frame.shape[1] != W or frame.shape[0] != H:
        frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
    return frame


def build_v003_contact_sheet() -> Path:
    frames = [0, N_FRAMES // 4, MID_FRAME, (N_FRAMES * 3) // 4, N_FRAMES - 1]
    cell_w, cell_h = 320, 180
    label_w, label_h = 300, 46
    sheet = np.zeros((label_h + cell_h, label_w + len(frames) * cell_w, 3), dtype=np.uint8)
    draw_text(sheet, "primitive_field_cycle_v003", (16, 29), LABEL_RGB, scale=0.42)
    for col, fi in enumerate(frames):
        draw_text(sheet, f"f{fi:03d}", (label_w + col * cell_w + 12, 29), LABEL_RGB, scale=0.44)
        thumb = cv2.resize(draw_field(fi == MID_FRAME, fi), (cell_w, cell_h), interpolation=cv2.INTER_AREA)
        x0 = label_w + col * cell_w
        y0 = label_h
        sheet[y0 : y0 + cell_h, x0 : x0 + cell_w] = thumb
        cv2.rectangle(sheet, (x0, y0), (x0 + cell_w - 1, y0 + cell_h - 1), (36, 46, 46), 1)
    out = OUT_DIR / "primitive_field_cycle_v003_contact_sheet.png"
    save_png(out, sheet)
    return out


def build_comparison_sheet(v003_mp4: Path) -> Path:
    sources = [
        ("v001 grid wave", V001_MP4),
        ("v002 flock dark", V002_DARK_MP4),
        ("v002 flock light", V002_LIGHT_MP4),
        ("v003 authored field", v003_mp4),
        ("single_shape v002", SINGLE_V002_MP4),
    ]
    fracs = [0.00, 0.25, 0.50, 0.75]
    cell_w, cell_h = 300, 169
    label_w, label_h = 260, 46
    sheet = np.zeros((label_h + len(fracs) * cell_h, label_w + len(sources) * cell_w, 3), dtype=np.uint8)
    draw_text(sheet, "comparison", (16, 29), LABEL_RGB, scale=0.44)
    for col, (label, _path) in enumerate(sources):
        draw_text(sheet, label, (label_w + col * cell_w + 12, 29), LABEL_RGB, scale=0.38)
    for row, frac in enumerate(fracs):
        y0 = label_h + row * cell_h
        draw_text(sheet, f"{frac:.2f} loop", (16, y0 + 36), DEBUG_RGB, scale=0.42)
        for col, (_label, path) in enumerate(sources):
            frame = sample_video(path, frac)
            thumb = cv2.resize(frame, (cell_w, cell_h), interpolation=cv2.INTER_AREA)
            x0 = label_w + col * cell_w
            sheet[y0 : y0 + cell_h, x0 : x0 + cell_w] = thumb
            cv2.rectangle(sheet, (x0, y0), (x0 + cell_w - 1, y0 + cell_h - 1), (38, 46, 46), 1)
    out = OUT_DIR / "primitive_field_cycle_v003_comparison_contact_sheet.png"
    save_png(out, sheet)
    return out


def write_manifest(v003_mp4: Path, contact_sheet: Path, comparison_sheet: Path) -> None:
    glyphs = []
    for ribbon in RIBBONS:
        for glyph_idx in range(ribbon.count):
            glyphs.append(
                {
                    "glyph_id": f"{ribbon.ribbon_id}.{glyph_idx}",
                    "parent_ribbon_id": ribbon.ribbon_id,
                    "base_s": round((glyph_idx + 0.5) / ribbon.count, 4),
                    "from_state": "circle",
                    "through_states": ["crescent", "crescent", "trigon"],
                    "to_state": "circle",
                    "role": "morphing primitive cycle carried by common-fate flow",
                    "origin": "ribbon authored start / current source",
                    "direction": "Bezier current tangent",
                    "curvature_direction": "crescent cups upstream/origin side while trigon releases downstream",
                    "cultural_status": "internal grammar-inspired sketch; Austin review required before public use",
                }
            )
    manifest = {
        "renderer": "scripts/primitive_field_cycle_v003.py",
        "created": "2026-05-20",
        "status": "INTERNAL R&D. Not Austin-approved. Not public-ready. Not a cultural-meaning claim.",
        "technical": {
            "width": W,
            "height": H,
            "fps": FPS,
            "duration_seconds": DURATION_SECONDS,
            "frames": N_FRAMES,
            "background": "black/dark current field",
            "blend": "additive",
        },
        "inputs_compared": [
            str(V001_MP4.relative_to(ROOT)),
            str(V002_DARK_MP4.relative_to(ROOT)),
            str(V002_LIGHT_MP4.relative_to(ROOT)),
            str(SINGLE_V002_MP4.relative_to(ROOT)),
        ],
        "outputs": {
            "mp4": str(v003_mp4.relative_to(ROOT)),
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "comparison_contact_sheet": str(comparison_sheet.relative_to(ROOT)),
            "midpoint_still": str((OUT_DIR / "primitive_field_cycle_v003_midpoint_f072.png").relative_to(ROOT)),
            "debug_midpoint_still": str((OUT_DIR / "primitive_field_cycle_v003_debug_midpoint_f072.png").relative_to(ROOT)),
        },
        "ribbons": [
            {
                "ribbon_id": r.ribbon_id,
                "control_points": [r.p0, r.p1, r.p2, r.p3],
                "glyph_count": r.count,
                "normal_offset": r.normal_offset,
                "phase_offset": r.phase_offset,
                "speed": r.speed,
                "common_fate": "all glyphs on this ribbon share Bezier tangent, drift direction, phase family, and edge attenuation",
            }
            for r in RIBBONS
        ],
        "glyphs": glyphs,
        "boundaries": [
            "No random scatter; positions are deterministic samples on authored current ribbons.",
            "No topology/cymatics/seed-of-life construction.",
            "No fish, animals, SD, LoRA, Austin source artwork, or source-piece replication.",
            "Not a single-glyph proof; 52 morphing cycles are visible across six flow families.",
        ],
    }
    (OUT_DIR / "primitive_field_cycle_v003_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def write_readme(v003_mp4: Path, contact_sheet: Path, comparison_sheet: Path) -> None:
    lines = [
        "# Primitive Field Cycle v003 - 2026-05-20",
        "",
        "Status: INTERNAL R&D review packet. Not Austin-approved, not public-ready, not public-use cultural guidance, and not a claim about traditional meaning.",
        "",
        "This pass combines the cleaner primitive transformation from `primitive_cycle_motion_v002` with the older field-scale energy of `primitive_field_v001` and `primitive_field_v002_flocking_dark/light`.",
        "",
        "Unlike the v002 single-glyph proof, this is a field of many morphing `circle -> crescent -> crescent -> trigon -> circle` cycles. The glyphs are placed on authored current ribbons with shared tangent, deterministic phase offsets, and edge attenuation rather than random scatter.",
        "",
        "## Outputs",
        "",
        f"- MP4: `{v003_mp4.name}`",
        f"- Contact sheet: `{contact_sheet.name}`",
        f"- Comparison contact sheet: `{comparison_sheet.name}`",
        "- Midpoint still: `primitive_field_cycle_v003_midpoint_f072.png`",
        "- Debug midpoint still: `primitive_field_cycle_v003_debug_midpoint_f072.png`",
        "- Sidecar: `primitive_field_cycle_v003_manifest.json`",
        "",
        "## Render Contract",
        "",
        f"- Resolution: `{W}x{H}`",
        f"- Frame rate: `{FPS}fps`",
        f"- Duration: `{DURATION_SECONDS:.1f}s`",
        f"- Frame count: `{N_FRAMES}`",
        "- Background/blend: dark field with additive primitive glyphs",
        "",
        "## Comparison Sources",
        "",
        f"- `{V001_MP4.relative_to(ROOT)}`",
        f"- `{V002_DARK_MP4.relative_to(ROOT)}`",
        f"- `{V002_LIGHT_MP4.relative_to(ROOT)}`",
        f"- `{SINGLE_V002_MP4.relative_to(ROOT)}`",
        "",
        "## Boundaries",
        "",
        "- No random scatter; every glyph is tied to an authored flow ribbon.",
        "- No topology/cymatics/seed-of-life construction.",
        "- No fish, animals, SD, LoRA, Austin source artwork, or source-piece replication.",
        "- Austin review is required before any public/external use.",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sample_stills").mkdir(parents=True, exist_ok=True)
    print(f"Rendering primitive_field_cycle_v003 to {OUT_DIR}", flush=True)
    v003_mp4 = render_v003()
    contact_sheet = build_v003_contact_sheet()
    comparison_sheet = build_comparison_sheet(v003_mp4)
    write_manifest(v003_mp4, contact_sheet, comparison_sheet)
    write_readme(v003_mp4, contact_sheet, comparison_sheet)
    print(f"Done: {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
