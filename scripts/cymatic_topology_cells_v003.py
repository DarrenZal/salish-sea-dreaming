#!/usr/bin/env python3.11
"""
Cymatic topology cells v003.

This pass derives visible primitive/topology cells from generated circle
overlaps instead of placing symbolic primitives over construction circles.
"""
from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass
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
    blend_local_mask,
    canvas,
    draw_arc,
    draw_circle,
    draw_crescent,
    draw_crescent_cupping,
    draw_lens,
    draw_line,
    draw_ring,
    draw_s_crescent,
    draw_trigon,
    draw_trigon_release,
    phase_wave,
    point,
    radial_angles,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/cymatic_topology_cells_v003_2026-05-20"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"

AXIAL_DIRS: tuple[tuple[int, int], ...] = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


@dataclass(frozen=True)
class CircleNode:
    coord: tuple[int, int]
    ring: int
    center: tuple[float, float]
    alpha: float


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def axial_distance(coord: tuple[int, int]) -> int:
    q, r = coord
    return max(abs(q), abs(r), abs(q + r))


def axial_coords(max_ring: int) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for q in range(-max_ring, max_ring + 1):
        for r in range(-max_ring, max_ring + 1):
            coord = (q, r)
            if axial_distance(coord) <= max_ring:
                coords.append(coord)
    coords.sort(key=lambda c: (axial_distance(c), c[1], c[0]))
    return coords


def axial_offset(coord: tuple[int, int], spacing: float, rotation: float) -> tuple[float, float]:
    q, r = coord
    x = spacing * (q + r * 0.5)
    y = spacing * (math.sqrt(3.0) * 0.5 * r)
    c = math.cos(rotation)
    s = math.sin(rotation)
    return (x * c - y * s, x * s + y * c)


def shifted_center(origin: tuple[float, float], offset: tuple[float, float], scale: float) -> tuple[float, float]:
    return (origin[0] + offset[0] * scale, origin[1] + offset[1] * scale)


def build_lattice(
    origin: tuple[float, float],
    *,
    spacing: float,
    max_ring: int,
    rotation: float,
    ring_scale: dict[int, float],
    ring_alpha: dict[int, float],
) -> dict[tuple[int, int], CircleNode]:
    nodes: dict[tuple[int, int], CircleNode] = {}
    for coord in axial_coords(max_ring):
        ring = axial_distance(coord)
        offset = axial_offset(coord, spacing, rotation)
        scale = ring_scale.get(ring, 1.0)
        alpha = ring_alpha.get(ring, 0.0)
        nodes[coord] = CircleNode(coord=coord, ring=ring, center=shifted_center(origin, offset, scale), alpha=alpha)
    return nodes


def add_coords(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return (a[0] + b[0], a[1] + b[1])


def lattice_pairs(nodes: dict[tuple[int, int], CircleNode]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    pairs: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for coord in nodes:
        for direction in AXIAL_DIRS:
            other = add_coords(coord, direction)
            if other in nodes:
                pairs.add(tuple(sorted((coord, other))))
    return sorted(pairs)


def lattice_triangles(nodes: dict[tuple[int, int], CircleNode]) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]]:
    triangles: set[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = set()
    for coord in nodes:
        for i, d1 in enumerate(AXIAL_DIRS):
            d2 = AXIAL_DIRS[(i + 1) % len(AXIAL_DIRS)]
            b = add_coords(coord, d1)
            c = add_coords(coord, d2)
            if b in nodes and c in nodes:
                triangles.add(tuple(sorted((coord, b, c))))
    return sorted(triangles)


def draw_intersection_region(
    frame: np.ndarray,
    centers: list[tuple[float, float]],
    radius: float,
    rgb: tuple[int, int, int],
    *,
    alpha: float,
    outline: bool = False,
    thickness: int = 4,
) -> None:
    if alpha <= 0 or not centers:
        return
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    pad = int(math.ceil(radius + thickness + 6))
    x0 = max(0, int(min(xs) - pad))
    y0 = max(0, int(min(ys) - pad))
    x1 = min(W, int(max(xs) + pad + 1))
    y1 = min(H, int(max(ys) + pad + 1))
    if x1 <= x0 or y1 <= y0:
        return
    intersection = np.full((y1 - y0, x1 - x0), 255, dtype=np.uint8)
    for cx, cy in centers:
        mask = np.zeros_like(intersection)
        cv2.circle(mask, (round(cx - x0), round(cy - y0)), max(1, round(radius)), 255, -1, lineType=cv2.LINE_AA)
        intersection = cv2.bitwise_and(intersection, mask)
    if outline:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, thickness), max(3, thickness)))
        region = cv2.morphologyEx(intersection, cv2.MORPH_GRADIENT, kernel)
    else:
        region = intersection
    if np.count_nonzero(region) < 8:
        return
    blend_local_mask(frame, region, (x0, y0, x1, y1), rgb, alpha)


def draw_derived_topology_cells(
    frame: np.ndarray,
    nodes: dict[tuple[int, int], CircleNode],
    *,
    circle_radius: float,
    construction_alpha: float,
    pair_fill_alpha: float,
    triple_fill_alpha: float,
    outline_alpha: float,
    inverse: bool = False,
) -> None:
    for node in nodes.values():
        if node.alpha <= 0.01:
            continue
        draw_ring(frame, node.center, circle_radius, 3, PALE_BLUE, alpha=construction_alpha * node.alpha)

    # Two-boundary overlaps: exact pairwise intersections, read as lenses/lunes.
    for idx, (a, b) in enumerate(lattice_pairs(nodes)):
        na = nodes[a]
        nb = nodes[b]
        active = min(na.alpha, nb.alpha)
        if active <= 0.03:
            continue
        rgb = SOFT_IVORY if idx % 2 == 0 else IVORY
        draw_intersection_region(frame, [na.center, nb.center], circle_radius, rgb, alpha=pair_fill_alpha * active)
        if outline_alpha > 0:
            draw_intersection_region(frame, [na.center, nb.center], circle_radius, PALE_BLUE, alpha=outline_alpha * active, outline=True, thickness=5)

    # Three-boundary overlaps: exact three-circle cells, read as curved trigons.
    for idx, tri in enumerate(lattice_triangles(nodes)):
        ns = [nodes[c] for c in tri]
        active = min(n.alpha for n in ns)
        if active <= 0.04:
            continue
        centroid = (sum(n.center[0] for n in ns) / 3.0, sum(n.center[1] for n in ns) / 3.0)
        dist = math.hypot(centroid[0] - 960.0, centroid[1] - 540.0)
        if dist < 52:
            continue
        rgb = PALE_BLUE if not inverse else MIST
        if idx % 5 == 0 and not inverse:
            rgb = SUN_GOLD
        draw_intersection_region(frame, [n.center for n in ns], circle_radius, rgb, alpha=triple_fill_alpha * active)
        if outline_alpha > 0:
            draw_intersection_region(frame, [n.center for n in ns], circle_radius, IVORY, alpha=outline_alpha * 0.72 * active, outline=True, thickness=4)


def render_seed_to_flower_topology_growth(phase: float) -> np.ndarray:
    frame = canvas()
    origin = (960.0, 540.0)
    cycle = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)
    ring1 = smoothstep(0.08, 0.36, cycle)
    ring2 = smoothstep(0.50, 0.86, cycle)
    ring1_scale = 0.20 + 0.80 * smoothstep(0.10, 0.42, cycle)
    ring2_scale = 0.45 + 0.55 * smoothstep(0.54, 0.88, cycle)
    breathe = 0.98 + 0.025 * math.sin(4.0 * math.pi * phase)
    nodes = build_lattice(
        origin,
        spacing=142 * breathe,
        max_ring=2,
        rotation=math.radians(30),
        ring_scale={0: 1.0, 1: ring1_scale, 2: ring2_scale},
        ring_alpha={0: 1.0, 1: ring1, 2: ring2 * 0.72},
    )
    draw_circle(frame, origin, 48 + 8 * cycle, IVORY, alpha=0.38 + 0.28 * cycle)
    draw_derived_topology_cells(
        frame,
        nodes,
        circle_radius=142 * breathe,
        construction_alpha=0.020 + 0.040 * cycle,
        pair_fill_alpha=0.30 + 0.18 * cycle,
        triple_fill_alpha=0.20 + 0.22 * cycle,
        outline_alpha=0.035 + 0.055 * cycle,
    )
    return frame


def phase_pulse(phase: float, center: float, width: float) -> float:
    d = abs(((phase - center + 0.5) % 1.0) - 0.5)
    return max(0.0, 1.0 - d / width) ** 2


def render_seed_to_flower_phase_inversion(phase: float) -> np.ndarray:
    frame = canvas()
    origin = (960.0, 540.0)
    line = 0.16 + 0.84 * phase_pulse(phase, 0.0, 0.34)
    pair_fill = phase_pulse(phase, 0.28, 0.30)
    inverse_fill = phase_pulse(phase, 0.68, 0.30)
    breathe = 0.985 + 0.025 * math.sin(4.0 * math.pi * phase)
    nodes = build_lattice(
        origin,
        spacing=140 * breathe,
        max_ring=2,
        rotation=math.radians(30) + math.radians(1.5) * math.sin(2.0 * math.pi * phase),
        ring_scale={0: 1.0, 1: 1.0, 2: 1.0},
        ring_alpha={0: 1.0, 1: 1.0, 2: 0.68},
    )
    draw_derived_topology_cells(
        frame,
        nodes,
        circle_radius=140 * breathe,
        construction_alpha=0.018 + 0.070 * line,
        pair_fill_alpha=0.04 + 0.58 * pair_fill + 0.06 * inverse_fill,
        triple_fill_alpha=0.04 + 0.16 * pair_fill + 0.54 * inverse_fill,
        outline_alpha=0.026 + 0.18 * line,
        inverse=inverse_fill > pair_fill,
    )
    draw_circle(frame, origin, 46 + 7 * max(pair_fill, inverse_fill), IVORY, alpha=0.24 + 0.30 * max(pair_fill, inverse_fill))
    draw_circle(frame, origin, 22 + 5 * inverse_fill, BLACK, alpha=0.55 * inverse_fill)
    return frame


@dataclass(frozen=True)
class SnowSpec:
    x: float
    y: float
    size: float
    alpha: float
    cycles: int
    drift: float
    rot: float


def snow_specs() -> list[SnowSpec]:
    specs: list[SnowSpec] = []
    for i in range(34):
        x = 90 + ((i * 313) % 1740)
        y = ((i * 197) % 1320) - 120
        size = 0.44 + 0.065 * (i % 8)
        alpha = 0.30 + 0.050 * (i % 7)
        cycles = 1 + (1 if i % 7 == 0 else 0)
        drift = 22 + (i % 5) * 8
        rot = math.radians((i * 37) % 360)
        specs.append(SnowSpec(float(x), float(y), size, alpha, cycles, float(drift), rot))
    return specs


def draw_primitive_snowflake(frame: np.ndarray, center: tuple[float, float], *, size: float, alpha: float, rotation: float, phase: float) -> None:
    s = 70 * size
    pulse = 0.92 + 0.10 * phase_wave(phase)
    draw_circle(frame, center, 10 * size * pulse, IVORY, alpha=alpha * 0.82)
    for idx, angle in enumerate(radial_angles(6, start=rotation)):
        local = phase_wave(phase, idx * 0.08)
        draw_lens(frame, point(center, angle, s * 0.42), s * 0.25, s * 0.080, angle, ICE_BLUE, alpha=alpha * (0.58 + 0.14 * local))
        draw_crescent_cupping(frame, point(center, angle, s * 0.72), center, s * 0.25, s * 0.16, SOFT_IVORY, alpha=alpha * 0.54)
        draw_trigon_release(frame, point(center, angle, s * 1.06), center, s * 0.16, s * 0.19, PALE_BLUE, alpha=alpha * 0.50, sharpness=0.78, softness=0.26)
        if idx % 2 == 0:
            draw_s_crescent(frame, point(center, angle + math.radians(28), s * 0.88), s * 0.23, angle + math.pi / 2.0, ICE_BLUE, alpha=alpha * 0.40)


def render_falling_snowflake_primitive_layer(phase: float) -> np.ndarray:
    frame = canvas()
    span = H + 260
    for i, spec in enumerate(snow_specs()):
        y = ((spec.y + span * spec.cycles * phase) % span) - 130
        x = spec.x + spec.drift * math.sin(2.0 * math.pi * phase + i * 0.63)
        rot = spec.rot + math.radians(18.0) * math.sin(2.0 * math.pi * phase + i * 0.22)
        depth_pulse = 0.86 + 0.14 * math.sin(2.0 * math.pi * phase + i)
        draw_primitive_snowflake(frame, (x, y), size=spec.size * depth_pulse, alpha=spec.alpha, rotation=rot, phase=phase + i * 0.017)
    return frame


def render_radiant_wave_growth_from_circle(phase: float) -> np.ndarray:
    frame = canvas()
    origin = (760.0, 560.0)
    draw_circle(frame, origin, 52 + 6 * phase_wave(phase), IVORY, alpha=0.62)
    draw_ring(frame, origin, 82 + 8 * phase_wave(phase, 0.12), 5, PALE_BLUE, alpha=0.18)

    arc_windows = [
        (math.radians(-32), math.radians(74)),
        (math.radians(82), math.radians(168)),
        (math.radians(198), math.radians(292)),
    ]
    for wave_idx in range(4):
        t = (phase + wave_idx * 0.25) % 1.0
        radius = 105 + 680 * t
        fade = (1.0 - t) ** 1.25
        if fade <= 0.02:
            continue
        for start, end in arc_windows:
            draw_arc(frame, origin, (radius, radius * 0.72), math.radians(-9), start, end, PALE_BLUE, alpha=0.060 * fade, thickness=4)
        cell_count = 3 + (wave_idx % 2)
        for cidx in range(cell_count):
            angle = math.radians(-14 + cidx * 34 + wave_idx * 8)
            local_radius = radius + 10 * math.sin(cidx + phase * 2.0 * math.pi)
            pos = point(origin, angle, local_radius)
            if cidx % 3 == 0:
                draw_crescent_cupping(frame, pos, origin, 88 * fade + 20, 52 * fade + 12, SOFT_IVORY, alpha=0.42 * fade)
            elif cidx % 3 == 1:
                draw_lens(frame, pos, 70 * fade + 16, 24 * fade + 8, angle + math.pi / 2.0, IVORY, alpha=0.36 * fade)
            else:
                draw_trigon_release(frame, pos, origin, 56 * fade + 18, 68 * fade + 18, SUN_GOLD if wave_idx == 0 else PALE_BLUE, alpha=0.34 * fade, sharpness=0.58, softness=0.58)
        # One quieter counterwave keeps it water-like rather than a perfect emblem.
        counter_angle = math.radians(150 + wave_idx * 17)
        draw_crescent_cupping(frame, point(origin, counter_angle, radius * 0.82), origin, 72 * fade + 16, 42 * fade + 10, MIST, alpha=0.24 * fade)
    return frame


ANIMATIONS: list[tuple[str, str, Callable[[float], np.ndarray]]] = [
    (
        "01_seed_to_flower_topology_growth_v003_black_screen.mp4",
        "Central one-boundary circle grows into seed and flower rings; exact pair/triple circle-overlap cells become lenses/crescents and curved trigons.",
        render_seed_to_flower_topology_growth,
    ),
    (
        "02_seed_to_flower_phase_inversion_v003_black_screen.mp4",
        "Same derived overlap topology, with construction/region outlines swapping into filled two-arc cells, then inverse three-boundary cells, then outline.",
        render_seed_to_flower_phase_inversion,
    ),
    (
        "03_falling_snowflake_primitive_layer_v003_black_screen.mp4",
        "Projection-friendly falling snow layer: many small primitive/topology snowflakes, not one centered emblem.",
        render_falling_snowflake_primitive_layer,
    ),
    (
        "04_radiant_wave_growth_from_circle_v003_black_screen.mp4",
        "A single origin circle sends partial radial wavefronts outward into rings of crescents, lenses, and curved trigons.",
        render_radiant_wave_growth_from_circle,
    ),
]


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


def save_contact_sheet(midpoints: list[tuple[str, np.ndarray]]) -> None:
    thumbs: list[np.ndarray] = []
    for idx, (name, frame) in enumerate(midpoints, start=1):
        thumb = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        cv2.putText(thumb, f"{idx:02d} {Path(name).stem[:44]}", (14, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (226, 232, 232), 1, cv2.LINE_AA)
        thumbs.append(thumb)
    cv2.imwrite(str(OUT_DIR / "contact_sheet_cymatic_topology_cells_v003_midpoints.png"), cv2.hconcat(thumbs), [cv2.IMWRITE_PNG_COMPRESSION, 3])


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
    readme = f"""# Cymatic Topology Cells v003 - 2026-05-20

Status: INTERNAL ONLY. Austin-review-needed. Not Austin-approved, not public, and not a cultural meaning claim.

Builds from:

`track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/`

This packet incorporates Darren's v002 review:

- Rejects v002 rain-on-water as too crude and not fluid/water enough.
- Rejects the v002 nodal plate for now.
- Keeps the seed-of-life direction, but derives visible cells from generated circle overlaps instead of drawing primitive icons on top.
- Reframes snowflake as a falling snow layer made from many primitive/topology snowflakes.

## Derived Topology Cells

The seed/flower clips generate a hexagonal lattice of construction circles. The construction circles are faint, and the visible layer is mostly derived from their overlap regions:

- `circle`: one-boundary origin/center cell.
- `crescent` / `lens` / `lune`: exact two-circle intersection regions, rendered as two-arc topology cells.
- `trigon`: exact three-circle intersection regions, rendered as curved three-boundary cells or triangular/scalloped gaps.

This is an approximation of region classification, but the visible cells are computed from the circle geometry instead of manually placing symbols.

## Clips

{animation_lines}

## Motion Rules

- `01` grows from central circle to first seed ring, then hints a second flower ring.
- `02` makes line/fill inversion explicit: outline -> filled two-arc cells -> inverse three-boundary cells -> outline.
- `03` is a rectangular falling snow layer, with different sizes/depths and looped fall paths.
- `04` grows partial wavefronts from one circle into rings of crescents/lenses/trigons so it can read as water/sun/snow without becoming a generic mandala.

## Constraints Held

- No crude rain-on-water clip in this pass.
- No nodal plate clip in this pass.
- No salmon, fish, birds, figures, or flocking.
- No debug dots.
- No crude Cartesian grid.
- No generic mandala wallpaper.

## Technical Method

- Deterministic Python/OpenCV vector/mask rendering.
- 1920x1080 black-screen H.264 MP4, 24 fps, 6 seconds, 144 frames.
- Pairwise and triple overlap regions are generated as local OpenCV circle-intersection masks.
- Midpoint stills and a midpoint contact sheet are included.

Renderer:

`scripts/cymatic_topology_cells_v003.py`

## Contents

- 4 MP4 loops.
- Midpoint stills in `midpoint_stills/`.
- Contact sheet: `contact_sheet_cymatic_topology_cells_v003_midpoints.png`.

## Review Questions

- Does deriving cells from actual circle overlap solve the icon-on-top problem?
- Are the two-arc and three-boundary cells legible enough without showing too much construction geometry?
- Does the snowflake layer read as a usable projection layer rather than a centered emblem?
- Does the radiant wave feel like water/sun/snow topology rather than generic mandala wallpaper?
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    render_animations()
    write_readme()
    print(f"Wrote cymatic topology cells v003 packet to {OUT_DIR}")


if __name__ == "__main__":
    main()
