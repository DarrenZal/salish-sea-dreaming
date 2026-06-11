#!/usr/bin/env python3.11
"""
Cymatic topology cells v004.

Uses seed/flower construction as hidden scaffolding, then fades it down so the
readable layer becomes circle / crescent-lens / curved-trigon primitive topology.
"""
from __future__ import annotations

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
    canvas,
    draw_circle,
    draw_crescent,
    draw_crescent_cupping,
    draw_lens,
    draw_ring,
    draw_s_crescent,
    draw_trigon,
    draw_trigon_release,
    phase_wave,
    point,
    radial_angles,
)
from cymatic_topology_cells_v003 import (
    build_lattice,
    draw_derived_topology_cells,
    draw_intersection_region,
    lattice_pairs,
    lattice_triangles,
    smoothstep,
)


OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/cymatic_topology_cells_v004_2026-05-20"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"


def reveal_cycle(phase: float) -> tuple[float, float, float]:
    """Loop from construction to primitive reveal and back."""

    reveal = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)
    construction = 1.0 - reveal
    breathe = 0.5 + 0.5 * math.sin(4.0 * math.pi * phase)
    return reveal, construction, breathe


def construction_lattice(frame: np.ndarray, *, center: tuple[float, float], alpha: float, spacing: float, rotation: float, max_ring: int = 2) -> None:
    nodes = build_lattice(
        center,
        spacing=spacing,
        max_ring=max_ring,
        rotation=rotation,
        ring_scale={0: 1.0, 1: 1.0, 2: 1.0},
        ring_alpha={0: 1.0, 1: 1.0, 2: 0.72},
    )
    draw_derived_topology_cells(
        frame,
        nodes,
        circle_radius=spacing,
        construction_alpha=0.10 * alpha,
        pair_fill_alpha=0.05 * alpha,
        triple_fill_alpha=0.055 * alpha,
        outline_alpha=0.045 * alpha,
    )


def render_sun_from_seed_geometry(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    reveal, construction, breathe = reveal_cycle(phase)
    primitive = smoothstep(0.18, 0.72, reveal)
    spacing = 134 * (0.99 + 0.018 * breathe)

    construction_lattice(frame, center=center, alpha=0.95 * construction, spacing=spacing, rotation=math.radians(30), max_ring=2)

    # Primitive sun/ripple read: center origin, cupping crescents, trigon ray ring.
    draw_circle(frame, center, 68 + 9 * primitive, SUN_GOLD, alpha=0.16 * construction + 0.66 * primitive)
    draw_circle(frame, center, 38 + 4 * primitive, IVORY, alpha=0.20 + 0.34 * primitive)
    draw_ring(frame, center, 108 + 8 * breathe, 5, PALE_BLUE, alpha=0.04 * construction + 0.18 * primitive)

    for idx, angle in enumerate(radial_angles(12, start=math.radians(15))):
        local = phase_wave(phase, idx * 0.06)
        inner = point(center, angle, 142 + 8 * local)
        ray = point(center, angle, 224 + 16 * local)
        outer = point(center, angle, 322 + 24 * local)
        draw_crescent_cupping(frame, inner, center, 78 + 8 * primitive, 48 + 5 * primitive, SOFT_IVORY, alpha=0.06 * construction + 0.46 * primitive)
        draw_trigon_release(frame, ray, center, 66 + 12 * primitive, 82 + 12 * primitive, SUN_GOLD if idx % 3 == 0 else PALE_BLUE, alpha=0.08 * construction + 0.58 * primitive, sharpness=0.68, softness=0.38)
        if idx % 2 == 0:
            draw_lens(frame, outer, 74 + 10 * primitive, 24 + 6 * primitive, angle + math.pi / 2.0, IVORY, alpha=0.04 * construction + 0.22 * primitive)
    return frame


def render_trigon_field_reveal(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    reveal, construction, breathe = reveal_cycle(phase)
    primitive = smoothstep(0.20, 0.78, reveal)
    spacing = 138 * (0.99 + 0.02 * breathe)
    rotation = math.radians(30) + math.radians(2.0) * math.sin(2.0 * math.pi * phase)
    nodes = build_lattice(
        center,
        spacing=spacing,
        max_ring=2,
        rotation=rotation,
        ring_scale={0: 1.0, 1: 1.0, 2: 1.0},
        ring_alpha={0: 1.0, 1: 1.0, 2: 0.76},
    )

    # Construction and lens evidence fades away; trigons remain.
    draw_derived_topology_cells(
        frame,
        nodes,
        circle_radius=spacing,
        construction_alpha=0.10 * construction,
        pair_fill_alpha=0.12 * construction,
        triple_fill_alpha=0.06 * construction,
        outline_alpha=0.08 * construction,
    )

    for idx, tri in enumerate(lattice_triangles(nodes)):
        ns = [nodes[c] for c in tri]
        active = min(n.alpha for n in ns)
        if active < 0.10:
            continue
        centroid = (sum(n.center[0] for n in ns) / 3.0, sum(n.center[1] for n in ns) / 3.0)
        dx = centroid[0] - center[0]
        dy = centroid[1] - center[1]
        dist = math.hypot(dx, dy)
        if dist < 78 or dist > 430:
            continue
        angle = math.atan2(dy, dx)
        size = 48 + 18 * (dist / 430.0)
        rgb = SUN_GOLD if idx % 6 in (0, 1) else PALE_BLUE
        draw_trigon_release(frame, centroid, center, size, size * 1.08, rgb, alpha=(0.10 * construction + 0.64 * primitive) * active, sharpness=0.62, softness=0.48)
        if idx % 3 == 0:
            draw_trigon(frame, point(centroid, angle, 44), size * 0.54, size * 0.64, angle, SOFT_IVORY, alpha=0.28 * primitive * active, sharpness=0.70, softness=0.32)

    draw_circle(frame, center, 42, IVORY, alpha=0.12 * construction + 0.30 * primitive)
    return frame


def render_crescent_lens_field(phase: float) -> np.ndarray:
    frame = canvas()
    center = (960.0, 540.0)
    reveal, construction, breathe = reveal_cycle(phase)
    primitive = smoothstep(0.16, 0.78, reveal)
    spacing = 136 * (0.99 + 0.02 * breathe)
    rotation = math.radians(30) + math.radians(4.0) * math.sin(2.0 * math.pi * phase)
    nodes = build_lattice(
        center,
        spacing=spacing,
        max_ring=2,
        rotation=rotation,
        ring_scale={0: 1.0, 1: 1.0, 2: 1.0},
        ring_alpha={0: 1.0, 1: 1.0, 2: 0.60},
    )

    draw_derived_topology_cells(
        frame,
        nodes,
        circle_radius=spacing,
        construction_alpha=0.075 * construction,
        pair_fill_alpha=0.05 * construction,
        triple_fill_alpha=0.025 * construction,
        outline_alpha=0.055 * construction,
    )

    # Use only a directional S-band subset of two-circle overlaps so this reads
    # as crescent/lune topology rather than a centered flower emblem.
    selected: list[tuple[float, tuple[float, float], float, tuple[tuple[int, int], tuple[int, int]]]] = []
    for pair in lattice_pairs(nodes):
        a, b = pair
        na = nodes[a]
        nb = nodes[b]
        active = min(na.alpha, nb.alpha)
        if active < 0.10:
            continue
        mid = ((na.center[0] + nb.center[0]) * 0.5, (na.center[1] + nb.center[1]) * 0.5)
        dx = mid[0] - center[0]
        dy = mid[1] - center[1]
        curve_y = 0.22 * dx + 58.0 * math.sin(dx / 210.0)
        band = abs(dy - curve_y)
        dist = math.hypot(dx, dy)
        if band < 96 and 118 < dist < 440:
            angle = math.atan2(nb.center[1] - na.center[1], nb.center[0] - na.center[0])
            selected.append((dist, mid, angle, pair))
    selected.sort(key=lambda item: item[1][0])

    for idx, (_, mid, angle, pair) in enumerate(selected[:22]):
        a, b = pair
        active = min(nodes[a].alpha, nodes[b].alpha)
        draw_intersection_region(frame, [nodes[a].center, nodes[b].center], spacing, SOFT_IVORY if idx % 2 else PALE_BLUE, alpha=0.10 * construction + 0.22 * primitive * active)
        draw_intersection_region(frame, [nodes[a].center, nodes[b].center], spacing, IVORY, alpha=0.02 * construction + 0.26 * primitive * active, outline=True, thickness=5)
        # Cupped crescent accent on one side of the lens makes the two-arc class explicit.
        origin = center if idx % 2 == 0 else nodes[a].center
        crescent_pos = point(mid, angle + math.pi / 2.0, 26 + 4 * (idx % 3))
        draw_crescent_cupping(frame, crescent_pos, origin, 58 + 5 * primitive, 34 + 4 * primitive, IVORY, alpha=0.36 * primitive * active)
        if idx % 5 == 0:
            draw_s_crescent(frame, point(mid, angle, 44), 58, angle + math.pi / 2.0, PALE_BLUE, alpha=0.24 * primitive * active)

    return frame


@dataclass(frozen=True)
class SnowSpec:
    x: float
    y: float
    size: float
    alpha: float
    speed: float
    drift: float
    rot: float
    depth: float


def snow_specs_v004() -> list[SnowSpec]:
    specs: list[SnowSpec] = []
    for i in range(42):
        depth = (i % 9) / 8.0
        x = 70 + ((i * 337) % 1780)
        y = ((i * 191) % 1340) - 130
        size = 0.28 + 0.54 * depth
        alpha = 0.14 + 0.36 * depth
        speed = 0.52 + 0.38 * depth
        drift = 7 + 20 * depth
        rot = math.radians((i * 43) % 360)
        specs.append(SnowSpec(float(x), float(y), size, alpha, speed, drift, rot, depth))
    return specs


def draw_clean_snowflake(frame: np.ndarray, center: tuple[float, float], *, size: float, alpha: float, rotation: float, phase: float) -> None:
    s = 72 * size
    pulse = 0.94 + 0.08 * phase_wave(phase)
    draw_circle(frame, center, 9 * size * pulse, IVORY, alpha=alpha * 0.72)
    for idx, angle in enumerate(radial_angles(6, start=rotation)):
        local = phase_wave(phase, idx * 0.07)
        draw_lens(frame, point(center, angle, s * 0.40), s * 0.24, s * 0.078, angle, ICE_BLUE, alpha=alpha * (0.46 + 0.12 * local))
        draw_crescent_cupping(frame, point(center, angle, s * 0.70), center, s * 0.25, s * 0.15, SOFT_IVORY, alpha=alpha * 0.45)
        draw_trigon_release(frame, point(center, angle, s * 1.02), center, s * 0.15, s * 0.19, PALE_BLUE, alpha=alpha * 0.42, sharpness=0.80, softness=0.24)
        if idx % 2 == 0:
            branch = point(center, angle, s * 0.72)
            draw_lens(frame, point(branch, angle + math.radians(33), s * 0.28), s * 0.14, s * 0.046, angle + math.radians(33), ICE_BLUE, alpha=alpha * 0.27)
            draw_lens(frame, point(branch, angle - math.radians(33), s * 0.28), s * 0.14, s * 0.046, angle - math.radians(33), ICE_BLUE, alpha=alpha * 0.27)


def render_falling_snowflake_layer(phase: float) -> np.ndarray:
    frame = canvas()
    span = H + 300
    for i, spec in enumerate(snow_specs_v004()):
        y = ((spec.y + span * spec.speed * phase) % span) - 150
        x = spec.x + spec.drift * math.sin(2.0 * math.pi * phase * 0.62 + i * 0.51)
        rot = spec.rot + math.radians(10.0 + 12.0 * spec.depth) * math.sin(2.0 * math.pi * phase * 0.45 + i * 0.22)
        shimmer = 0.88 + 0.12 * math.sin(2.0 * math.pi * phase + i)
        draw_clean_snowflake(frame, (x, y), size=spec.size * shimmer, alpha=spec.alpha, rotation=rot, phase=phase + i * 0.013)
    return frame


ANIMATIONS: list[tuple[str, str, Callable[[float], np.ndarray]]] = [
    (
        "01_sun_from_seed_geometry_v004_black_screen.mp4",
        "Faint seed/flower construction fades into a center circle with a clear curved-trigon/ray ring and supporting crescent/lens cells.",
        render_sun_from_seed_geometry,
    ),
    (
        "02_trigon_field_reveal_v004_black_screen.mp4",
        "Flower/seed overlap fades down until the curved trigon/ray cells become the dominant plane.",
        render_trigon_field_reveal,
    ),
    (
        "03_crescent_lens_field_v004_black_screen.mp4",
        "Two-circle overlap cells are emphasized as crescent/lune/lens boundaries in a directional field, avoiding a plain petal mandala read.",
        render_crescent_lens_field,
    ),
    (
        "04_falling_snowflake_layer_v004_black_screen.mp4",
        "Improved rectangular falling snow layer with slower drift, depth variation, and cleaner primitive-cell snowflakes.",
        render_falling_snowflake_layer,
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
    cv2.imwrite(str(OUT_DIR / "contact_sheet_cymatic_topology_cells_v004_midpoints.png"), cv2.hconcat(thumbs), [cv2.IMWRITE_PNG_COMPRESSION, 3])


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
    readme = f"""# Cymatic Topology Cells v004 - 2026-05-20

Status: INTERNAL ONLY. Austin-review-needed. Not Austin-approved, not public, and not a cultural meaning claim.

Builds from:

`track2-deterministic/morph_outputs_INTERNAL/cymatic_topology_cells_v003_2026-05-20/`

## Darren v003 Review Incorporated

- Kept and improved the falling snowflake layer as a rectangular black-screen layer.
- Reworked the seed/flower direction so it does not finish as plain sacred geometry.
- Pushed v003 `01` toward the center-circle plus trigon/ray-ring logic that resembled Austin's sun/ray construction.
- Dropped the v003 `04` radiant wave direction entirely.

## Design Rule

Seed/flower geometry is used as hidden construction, not the final visual. Construction circles may appear briefly, then fade down. The readable layer should be primitive topology:

- center `circle` / origin
- surrounding curved `trigon` / ray cells
- `crescent`, `lens`, and `lune` cells from two-arc overlap
- rings or fields of primitive cells

## Clips

{animation_lines}

## Technical Method

- Deterministic Python/OpenCV vector and local mask rendering.
- 1920x1080 black-screen H.264 MP4, 24 fps, 6 seconds, 144 frames.
- Construction geometry is generated from seed/flower circle lattices, then faded down.
- Visible midpoint/final phases emphasize circle/crescent/trigon topology instead of construction circles.

Renderer:

`scripts/cymatic_topology_cells_v004.py`

## Contents

- 4 MP4 loops.
- Midpoint stills in `midpoint_stills/`.
- Contact sheet: `contact_sheet_cymatic_topology_cells_v004_midpoints.png`.

## Constraints Held

- No v003 `04` radiant wave continuation.
- No crude rain-on-water pass.
- No nodal plate pass.
- No salmon, fish, birds, figures, or flocking.
- Construction geometry is only brief/faint; final readable layer is primitive topology.

## Review Questions

- Does `01` now read as a primitive sun/ripple figure rather than plain seed geometry?
- Does `02` make the curved-trigon/ray plane obvious enough?
- Does `03` make lens/crescent two-arc topology explicit without becoming generic petals?
- Is `04` strong enough as a projection-friendly snow layer direction?
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    render_animations()
    write_readme()
    print(f"Wrote cymatic topology cells v004 packet to {OUT_DIR}")


if __name__ == "__main__":
    main()
