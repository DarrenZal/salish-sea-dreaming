#!/usr/bin/env python3.11
"""
Cymatic standing-wave phase inversion v002.

Builds from cymatic_radiant_water_geometry_v001 with a stronger line/fill
inversion: nodal contours dominate one half-cycle, filled antinodal primitive
cells dominate the opposite half-cycle, then the system swaps back.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from cymatic_radiant_water_geometry_v001 import (
    BLACK,
    DEEP_TEAL,
    FPS,
    H,
    H264Writer,
    ICE_BLUE,
    IVORY,
    MIST,
    N_FRAMES,
    PALE_BLUE,
    ROOT,
    SOFT_IVORY,
    SUN_GOLD,
    W,
    canvas,
    draw_arc,
    draw_circle,
    draw_crescent,
    draw_crescent_cupping,
    draw_lens,
    draw_line,
    draw_oval,
    draw_oval_ring,
    draw_ring,
    draw_s_crescent,
    draw_seed_circles,
    draw_trigon,
    draw_trigon_release,
    nodal_curve,
    phase_wave,
    point,
    radial_angles,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/cymatic_standing_wave_phase_inversion_v002_2026-05-20"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"


def inversion_levels(phase: float) -> tuple[float, float, float]:
    """Return line, fill, and membrane breath levels for a seamless 6s loop."""

    line = 0.5 + 0.5 * math.cos(2.0 * math.pi * phase)
    fill = 1.0 - line
    breath = 0.5 + 0.5 * math.sin(4.0 * math.pi * phase)
    return line, fill, breath


def draw_seed_inversion_cells(
    frame: np.ndarray,
    center: tuple[float, float],
    *,
    radius: float,
    line: float,
    fill: float,
    breath: float,
    rotation: float = 0.0,
) -> None:
    line_alpha = 0.035 + 0.22 * line
    fill_alpha = 0.070 + 0.58 * fill
    quiet_fill = 0.020 + 0.18 * fill
    r = radius * (0.985 + 0.025 * breath)

    draw_seed_circles(frame, center, r, ring_radius=r, rgb=PALE_BLUE, alpha=line_alpha, thickness=5, start=rotation)
    draw_seed_circles(frame, center, r * 0.86, ring_radius=r * 1.72, count=12, rgb=DEEP_TEAL, alpha=line_alpha * 0.42, thickness=3, start=rotation + math.radians(15))
    draw_ring(frame, center, r * 2.92, 4, PALE_BLUE, alpha=line_alpha * 0.46)

    draw_circle(frame, center, 54 + 8 * fill, IVORY, alpha=0.18 + 0.38 * fill)
    for idx, angle in enumerate(radial_angles(6, start=math.radians(30) + rotation)):
        local = phase_wave(fill, idx * 0.08)
        draw_lens(frame, point(center, angle, r * 0.78), 92 + 12 * fill, 32 + 8 * fill, angle, SOFT_IVORY, alpha=fill_alpha * (0.84 + 0.12 * local))
        draw_crescent_cupping(frame, point(center, angle, r * 1.40), center, 104 + 10 * fill, 62 + 7 * fill, IVORY, alpha=fill_alpha * 0.62)
        draw_trigon_release(frame, point(center, angle, r * 2.08), center, 58 + 8 * fill, 68 + 8 * fill, PALE_BLUE, alpha=fill_alpha * 0.46, sharpness=0.54, softness=0.64)

    for angle in radial_angles(6, start=rotation):
        draw_trigon_release(frame, point(center, angle, r * 0.95), center, 42 + 5 * fill, 50 + 8 * fill, BLACK, alpha=min(1.0, 0.35 + 0.52 * fill), sharpness=0.46, softness=0.82)
    for angle in radial_angles(12, start=math.radians(15) + rotation):
        draw_lens(frame, point(center, angle, r * 2.32), 62, 21, angle + math.pi / 2.0, MIST, alpha=quiet_fill * (0.65 if int(angle * 100) % 2 else 1.0))


def render_seed_of_life_phase_inversion(phase: float) -> np.ndarray:
    frame = canvas()
    line, fill, breath = inversion_levels(phase)
    center = (960.0, 540.0)
    rotation = math.radians(3.0) * math.sin(2.0 * math.pi * phase)
    draw_seed_inversion_cells(frame, center, radius=148, line=line, fill=fill, breath=breath, rotation=rotation)
    return frame


def render_rain_interference_phase_inversion(phase: float) -> np.ndarray:
    frame = canvas()
    line, fill, breath = inversion_levels(phase)
    centers = [(700.0, 548.0), (960.0, 502.0), (1220.0, 574.0)]
    line_alpha = 0.030 + 0.19 * line
    fill_alpha = 0.040 + 0.48 * fill
    ring_shift = 18 * math.sin(2.0 * math.pi * phase)

    for idx, center in enumerate(centers):
        impact = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase + idx * 0.18))
        draw_circle(frame, center, 30 + 9 * impact, IVORY, alpha=0.22 + 0.32 * fill)
        for ridx, base in enumerate([104, 212, 344, 506]):
            draw_ring(frame, center, base + ring_shift + idx * 5 + ridx * 6 * breath, 4, PALE_BLUE, alpha=max(0.020, line_alpha - ridx * 0.026))

    # Antinodal interference cells sit where the rings cross, not on a grid.
    cells = [
        ((830.0, 526.0), math.radians(6), "lens"),
        ((1084.0, 535.0), math.radians(-8), "lens"),
        ((960.0, 620.0), math.radians(88), "crescent"),
        ((780.0, 666.0), math.radians(38), "trigon"),
        ((1150.0, 686.0), math.radians(142), "trigon"),
        ((960.0, 398.0), math.radians(-90), "crescent"),
    ]
    for idx, (pos, angle, kind) in enumerate(cells):
        local = phase_wave(phase, idx * 0.075)
        if kind == "lens":
            draw_lens(frame, pos, 92 + 12 * local, 32 + 7 * fill, angle, SOFT_IVORY, alpha=fill_alpha * (0.92 + 0.10 * local))
        elif kind == "crescent":
            draw_crescent(frame, pos, 98 + 10 * fill, 62 + 6 * fill, angle, IVORY, alpha=fill_alpha * 0.74)
        else:
            origin = centers[1]
            draw_trigon_release(frame, pos, origin, 66 + 7 * fill, 78 + 8 * fill, PALE_BLUE, alpha=fill_alpha * 0.66, sharpness=0.52, softness=0.68)

    # Soft standing contour between the impacts: visible in line phase, subdued in fill phase.
    bridge = [
        (centers[0][0], centers[0][1] + 10 * math.sin(2 * math.pi * phase)),
        (830.0, 520.0 - 16 * breath),
        (960.0, 538.0 + 12 * breath),
        (1092.0, 548.0 - 14 * breath),
        (centers[2][0], centers[2][1] + 10 * math.sin(2 * math.pi * (phase + 0.15))),
    ]
    draw_line(frame, bridge, DEEP_TEAL, alpha=0.030 + 0.14 * line, thickness=5)
    return frame


def render_snowflake_harmonic_phase_inversion(phase: float) -> np.ndarray:
    frame = canvas()
    line, fill, breath = inversion_levels(phase)
    center = (960.0, 540.0)
    rotation = math.radians(2.5) * math.sin(2.0 * math.pi * phase)
    line_alpha = 0.035 + 0.20 * line
    fill_alpha = 0.040 + 0.54 * fill
    scale = 0.98 + 0.035 * breath

    draw_ring(frame, center, 92 * scale, 12, ICE_BLUE, alpha=0.16 + 0.40 * fill)
    draw_seed_circles(frame, center, 136 * scale, ring_radius=136 * scale, rgb=ICE_BLUE, alpha=line_alpha * 0.78, thickness=4, start=math.radians(30) + rotation)
    draw_ring(frame, center, 388 * scale, 4, PALE_BLUE, alpha=line_alpha * 0.36)

    for idx, angle in enumerate(radial_angles(6, start=math.radians(30) + rotation)):
        local = phase_wave(phase, idx * 0.08)
        branch = point(center, angle, 260 * scale + 10 * local)
        draw_lens(frame, point(center, angle, 154 * scale), 76 + 10 * fill, 24 + 6 * fill, angle, ICE_BLUE, alpha=fill_alpha * 0.72)
        draw_crescent_cupping(frame, point(center, angle, 245 * scale), center, 100 + 8 * fill, 58 + 6 * fill, SOFT_IVORY, alpha=fill_alpha * 0.60)
        draw_trigon_release(frame, point(center, angle, 410 * scale), center, 54 + 7 * fill, 66 + 8 * fill, ICE_BLUE, alpha=fill_alpha * 0.52, sharpness=0.82, softness=0.24)
        for sign in (-1, 1):
            ba = angle + sign * math.radians(36)
            draw_line(frame, [branch, point(branch, ba, 140 * scale)], PALE_BLUE, alpha=line_alpha * 0.50, thickness=3)
            draw_lens(frame, point(branch, ba, 78 * scale), 42 + 5 * fill, 16 + 3 * fill, ba, ICE_BLUE, alpha=fill_alpha * 0.36)

    for angle in radial_angles(6, start=rotation):
        draw_s_crescent(frame, point(center, angle, 330 * scale), 72 + 8 * fill, angle + math.pi / 2.0, IVORY, alpha=fill_alpha * 0.36)
    return frame


def draw_plate_lines(frame: np.ndarray, center: tuple[float, float], *, line_alpha: float, phase: float, rotate: float) -> None:
    for idx, axes in enumerate([(690, 210), (535, 340), (375, 475), (250, 585)]):
        wobble = 12 * phase_wave(phase, idx * 0.09)
        draw_arc(frame, center, (axes[0] + wobble, axes[1] + wobble * 0.45), math.radians(idx * 28 - 18) + rotate, math.radians(18), math.radians(344), PALE_BLUE, alpha=max(0.018, line_alpha - idx * 0.020), thickness=5)
        draw_arc(frame, center, (axes[0], axes[1]), math.radians(idx * 28 + 92) - rotate * 0.85, math.radians(196), math.radians(336), DEEP_TEAL, alpha=max(0.014, line_alpha * 0.70 - idx * 0.016), thickness=4)


def render_cymatic_nodal_plate_phase_inversion(phase: float) -> np.ndarray:
    frame = canvas()
    line, fill, breath = inversion_levels(phase)
    center = (960.0, 540.0)
    rotate = math.radians(7.0) * math.sin(2.0 * math.pi * phase)
    line_alpha = 0.030 + 0.20 * line
    fill_alpha = 0.030 + 0.50 * fill

    draw_plate_lines(frame, center, line_alpha=line_alpha, phase=phase, rotate=rotate)

    # Cells are placed between nodal arcs and pulse in place. The polar layout is
    # intentional standing-wave geometry, not a particle field.
    for idx, angle in enumerate(radial_angles(16, start=math.radians(8) + rotate * 0.32)):
        ring_idx = idx % 4
        local = phase_wave(phase, idx * 0.055)
        dist = 170 + ring_idx * 82 + 14 * breath
        node = point(center, angle + 0.05 * math.sin(idx), dist)
        tangent = angle + math.pi / 2.0
        if idx % 4 == 0:
            draw_oval(frame, node, (36 + 8 * fill, 26 + 5 * fill), tangent, IVORY, alpha=fill_alpha * (0.70 + 0.16 * local))
        elif idx % 4 == 1:
            draw_lens(frame, node, 58 + 9 * fill, 20 + 4 * fill, tangent, SOFT_IVORY, alpha=fill_alpha * (0.68 + 0.12 * local))
        elif idx % 4 == 2:
            draw_s_crescent(frame, node, 70 + 8 * fill, tangent, IVORY, alpha=fill_alpha * 0.58)
        else:
            draw_trigon_release(frame, node, center, 40 + 6 * fill, 48 + 7 * fill, PALE_BLUE, alpha=fill_alpha * 0.56, sharpness=0.50, softness=0.70)

    # A low-amplitude horizontal standing contour anchors the membrane reading.
    for i, yoff in enumerate([-155, -54, 54, 155]):
        pts = nodal_curve(center, amp=42 - abs(yoff) * 0.06, y_offset=yoff, phase=phase * 0.18 + i * 0.10, width=1040)
        draw_line(frame, pts, DEEP_TEAL, alpha=line_alpha * 0.42, thickness=3)
    return frame


ANIMATIONS: list[tuple[str, str, Callable[[float], np.ndarray]]] = [
    (
        "01_seed_of_life_phase_inversion_v002_black_screen.mp4",
        "Overlapping seed circles invert into filled lune/crescent/trigon cells and back.",
        render_seed_of_life_phase_inversion,
    ),
    (
        "02_rain_on_water_interference_phase_inversion_v002_black_screen.mp4",
        "Rain impact rings create standing antinodal cells at interference crossings.",
        render_rain_interference_phase_inversion,
    ),
    (
        "03_snowflake_harmonic_phase_inversion_v002_black_screen.mp4",
        "Sixfold frozen-water contours invert into harmonic filled primitive cells.",
        render_snowflake_harmonic_phase_inversion,
    ),
    (
        "04_cymatic_nodal_plate_phase_inversion_v002_black_screen.mp4",
        "Chladni-like nodal lines invert into primitive cells between the contours.",
        render_cymatic_nodal_plate_phase_inversion,
    ),
]


def save_contact_sheet(midpoints: list[tuple[str, np.ndarray]]) -> None:
    thumbs: list[np.ndarray] = []
    for idx, (name, frame) in enumerate(midpoints, start=1):
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, f"{idx:02d} {Path(name).stem[:44]}", (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 232), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    cv2.imwrite(str(OUT_DIR / "contact_sheet_cymatic_phase_inversion_v002_midpoints.png"), cv2.hconcat(thumbs), [cv2.IMWRITE_PNG_COMPRESSION, 3])


def render_clip(name: str, render_frame: Callable[[float], np.ndarray]) -> np.ndarray:
    writer = H264Writer(OUT_DIR / name, fps=FPS, size=(W, H))
    midpoint: np.ndarray | None = None
    for fi in range(N_FRAMES):
        phase = fi / N_FRAMES
        frame = render_frame(phase)
        if fi == N_FRAMES // 2:
            midpoint = frame.copy()
        writer.write(frame)
        if (fi + 1) % 48 == 0:
            print(f"  {name} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    if midpoint is None:
        raise RuntimeError(f"No midpoint captured for {name}")
    return midpoint


def render_animations() -> list[tuple[str, np.ndarray]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    midpoints: list[tuple[str, np.ndarray]] = []
    for name, _, fn in ANIMATIONS:
        midpoint = render_clip(name, fn)
        midpoint_name = name.replace(".mp4", "_midpoint.png")
        cv2.imwrite(str(MIDPOINT_DIR / midpoint_name), midpoint, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        midpoints.append((name, midpoint))
    save_contact_sheet(midpoints)
    return midpoints


def write_readme() -> None:
    animation_lines = "\n".join([f"- `{name}`: {note}" for name, note, _ in ANIMATIONS])
    readme = f"""# Cymatic Standing-Wave Phase-Inversion v002 - 2026-05-20

Status: INTERNAL ONLY. Austin-review-needed. Not Austin-approved, not public, and not a cultural meaning claim.

Builds from:

`track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/`

## New Direction

This packet tests Darren's phase-inversion insight:

- Lines are nodal geometry / wave contours.
- Filled bodies are antinodal cells between those contours.
- Animation inverts between the two: outline/line phase becomes filled-cell phase, then swaps back.
- Motion should read as a vibrating membrane or standing wave, not as particles traveling through space.

## Topology Interpretation

- `circle`: one-boundary closed form, used as a seed/impact/origin/closed pressure cell.
- `crescent`: two-arc class, including lune, lens, crescent, and S-crescent cells.
- `trigon`: three-sided / three-arc class, including triangular gaps, release cells, and nodal activation cells.

## Clips

{animation_lines}

## Technical Method

- Deterministic Python/OpenCV vector rendering.
- 1920x1080 black-screen H.264 MP4, 24 fps, 6 seconds, 144 frames.
- Seamless phase loop: line phase is strongest at the loop boundary; filled-cell phase is strongest at the midpoint.
- Midpoint stills intentionally show the antinodal fill phase.

Renderer:

`scripts/cymatic_standing_wave_phase_inversion_v002.py`

## Contents

- 4 MP4 loops.
- Midpoint stills in `midpoint_stills/`.
- Contact sheet: `contact_sheet_cymatic_phase_inversion_v002_midpoints.png`.

## Constraints Held

- No salmon, fish, birds, figures, or flocking.
- No debug dots.
- No crude Cartesian grid.
- No generic mandala wallpaper.
- Cells emerge from ring, seed, snowflake, and nodal geometry rather than random placement.

## Review Questions

- Does the line/fill inversion read clearly enough as nodal contours swapping with antinodal cells?
- Which loop best feels like a vibrating membrane: seed, rain interference, snowflake harmonic, or nodal plate?
- Are the filled cells still legible as circle / two-arc / three-arc topology classes?
- Should the next pass push cleaner mathematical cymatics, or keep the more water-ripple interpretation?
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    render_animations()
    write_readme()
    print(f"Wrote cymatic standing-wave phase inversion v002 packet to {OUT_DIR}")


if __name__ == "__main__":
    main()
