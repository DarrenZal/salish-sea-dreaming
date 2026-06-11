#!/usr/bin/env python3
"""
Lane 2A v001 — Roe-particle-field morph.

Atom-aware transition that DOES NOT path-morph the whole piece. Instead
treats the source's radial elements (cosmic_sun's 10 trigons + 10 sun-rays)
as particle emitters and the destination's 184 roe-circles as particle
sinks. Particles fly from source-ray centroids to assigned roe positions
along eased curved paths.

Why this avoids the cross-dissolve problem operator caught earlier:
this is NOT a global pixel blend. The source piece transforms by its
own components flying outward and re-organizing as the destination's
roe field; the destination materializes structurally as particles land,
not as a luma-mask fade.

Z-order handled correctly because we render direct SVG renders at both
endpoints (not engine output).

INTERNAL ONLY per Austin consent floor. Cross-domain Nature↔Animal —
medium cultural load, needs Austin framing context before any external
share.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import csv
import math
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

# Configuration
CANVAS = 1024
FPS = 24
N_FRAMES = 120  # 5 sec
PARTICLES_PER_RAY = 10  # ~ 184 roe / 20 rays
PARTICLE_RADIUS = 8  # px on 1024 canvas
VERSION = 2  # v001 had timing gap; v002 overlaps source/particle/dest phases


def load_atoms(piece_dir: Path, viewbox_size: int) -> list[dict]:
    """Load atoms with centroids normalized to [0, 1] canvas coordinates."""
    csv_path = piece_dir / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cx = float(row["centroid_x"])
                cy = float(row["centroid_y"])
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "centroid_norm": (cx / viewbox_size, cy / viewbox_size),
                    "fill": row["fill_color"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def render_svg(svg_path: Path, out_path: Path, size: int = CANVAS):
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg_path), "-resize", f"{size}x{size}",
        "-gravity", "center", "-extent", f"{size}x{size}",
        str(out_path),
    ], check=True)


def ease_inout(t: float) -> float:
    """Smoothstep cubic ease-in-out."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def bezier_path(p0, p1, control_offset: float, t: float) -> tuple[float, float]:
    """Quadratic bezier from p0 to p1 with a control point perpendicular to
    the midpoint, offset by control_offset (in normalized coords)."""
    mx = (p0[0] + p1[0]) / 2
    my = (p0[1] + p1[1]) / 2
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    length = math.hypot(dx, dy) or 1e-6
    # Perpendicular: rotate (dx, dy) 90deg CCW = (-dy, dx)
    px = -dy / length
    py = dx / length
    cp = (mx + px * control_offset, my + py * control_offset)
    # Quadratic bezier
    u = 1.0 - t
    bx = u * u * p0[0] + 2 * u * t * cp[0] + t * t * p1[0]
    by = u * u * p0[1] + 2 * u * t * cp[1] + t * t * p1[1]
    return (bx, by)


def angle_from_center(pt: tuple[float, float], center: tuple[float, float] = (0.5, 0.5)) -> float:
    return math.atan2(pt[1] - center[1], pt[0] - center[0])


def build_assignments(src_centroids, dst_centroids, n_per_src):
    """For each src centroid, assign n_per_src dst centroids by angular sorting.

    Returns list of (src_centroid, dst_centroid, particle_idx_within_src) tuples.
    """
    # Sort sources by angle from canvas center
    src_sorted = sorted(enumerate(src_centroids), key=lambda x: angle_from_center(x[1]))
    # Sort dests by angle then by distance from center (spiral-like)
    dst_sorted = sorted(
        enumerate(dst_centroids),
        key=lambda x: (angle_from_center(x[1]), math.hypot(x[1][0] - 0.5, x[1][1] - 0.5))
    )

    assignments = []
    n_dst = len(dst_sorted)
    for src_idx_in_sorted, (src_orig_idx, src_pt) in enumerate(src_sorted):
        for k in range(n_per_src):
            # Assign dest[j] where j cycles around dest list
            j = (src_idx_in_sorted * n_per_src + k) % n_dst
            _, dst_pt = dst_sorted[j]
            assignments.append((src_pt, dst_pt, k))
    return assignments


def main():
    # Phase 0: load both pieces' atom metadata
    cosmic_dir = DECOMPOSED / "Nature_Cosmic_Sun"
    salmon_dir = DECOMPOSED / "Animal_Salmon_Spawn_Eggs"
    # cosmic_sun is 108x108 viewBox; salmon_spawn is 1500x1500
    cosmic_atoms = load_atoms(cosmic_dir, viewbox_size=108)
    salmon_atoms = load_atoms(salmon_dir, viewbox_size=1500)

    # Filter to source radials + destination roe
    source_rays = [a for a in cosmic_atoms if a["label"] in ("trigon", "sun-ray")]
    dest_roe = [a for a in salmon_atoms if a["label"] == "egg-roe"]
    print(f"Source rays (trigon + sun-ray): {len(source_rays)}")
    print(f"Destination roe: {len(dest_roe)}")
    if not source_rays or not dest_roe:
        raise SystemExit("Missing atom data — abort")

    src_centroids = [a["centroid_norm"] for a in source_rays]
    dst_centroids = [a["centroid_norm"] for a in dest_roe]

    # Phase 1: render direct SVG of source and destination for endpoint frames
    out_dir = INTERNAL / f"cosmic_sun_to_salmon_spawn_roe_particle_field_v{VERSION:03d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / f"cosmic_sun_to_salmon_spawn_roe_particle_field_v{VERSION:03d}.mp4"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        src_png = tmpdir / "src.png"
        dst_png = tmpdir / "dst.png"
        render_svg(SOURCE_VECTORS / "Nature_Cosmic_Sun.svg", src_png, CANVAS)
        render_svg(SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg", dst_png, CANVAS)
        src_img = Image.open(src_png).convert("RGBA")
        dst_img = Image.open(dst_png).convert("RGBA")

        # Phase 2: build per-particle assignments + paths
        assignments = build_assignments(src_centroids, dst_centroids, PARTICLES_PER_RAY)
        n_particles = len(assignments)
        print(f"Particles: {n_particles}")

        # Per-particle launch delay (staggered launch over wider window so
        # particles are still spawning when destination starts materializing —
        # eliminates v001 blank-middle bug)
        rng = np.random.default_rng(42)
        launch_delays = rng.uniform(0.0, 0.60, n_particles)
        # Per-particle control offset for path curvature (orthogonal bow)
        curve_offsets = rng.uniform(-0.18, 0.18, n_particles)

        # Phase 3: render each frame
        # Frame plan (N=120) — v002 OVERLAPPING phases (no blank middle):
        #   0-7:    pure source SVG (8 frames hold) — particles start emitting
        #   8-49:   source fades out 100→0% over 42 frames (slow exit while
        #           particles are launching and beginning flight)
        #   30-95:  dest fades in 0→100% over 65 frames (starts before src
        #           fully gone; particles in flight bridge the visual span)
        #   96-119: pure dest SVG (24 frames hold) — particles all settled

        HOLD_SRC_END = 8
        SRC_FADE_END = 50
        DST_FADE_START = 30
        HOLD_DST_START = 96

        for i in range(N_FRAMES):
            t_global = i / (N_FRAMES - 1)
            canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))

            # --- Source layer alpha ---
            if i < HOLD_SRC_END:
                src_alpha = 1.0
            elif i < SRC_FADE_END:
                src_alpha = 1.0 - (i - HOLD_SRC_END) / (SRC_FADE_END - HOLD_SRC_END)
            else:
                src_alpha = 0.0

            # --- Destination layer alpha ---
            if i < DST_FADE_START:
                dst_alpha = 0.0
            elif i < HOLD_DST_START:
                dst_alpha = (i - DST_FADE_START) / (HOLD_DST_START - DST_FADE_START)
            else:
                dst_alpha = 1.0

            # Composite src under particles, dst under src
            if dst_alpha > 0:
                dst_layer = dst_img.copy()
                alpha_band = dst_layer.split()[3].point(lambda a: int(a * dst_alpha))
                dst_layer.putalpha(alpha_band)
                canvas = Image.alpha_composite(canvas, dst_layer)
            if src_alpha > 0:
                src_layer = src_img.copy()
                alpha_band = src_layer.split()[3].point(lambda a: int(a * src_alpha))
                src_layer.putalpha(alpha_band)
                canvas = Image.alpha_composite(canvas, src_layer)

            # --- Particle layer ---
            # Each particle has a delayed start and a 50-frame flight window.
            # Launch window now spans 0-60% of timeline so last particles
            # still in flight when destination is well-materialized.
            FLIGHT_FRAMES = 50
            launch_window_frames = int(N_FRAMES * 0.60)  # ~72 frames
            particle_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            pdraw = ImageDraw.Draw(particle_layer)

            for p_idx, (src_pt, dst_pt, _k) in enumerate(assignments):
                # Particle launches at frame HOLD_SRC_END + launch_delays[p_idx] * launch_window_frames
                launch_frame = HOLD_SRC_END + launch_delays[p_idx] * launch_window_frames
                local_t = (i - launch_frame) / FLIGHT_FRAMES
                if local_t < 0:
                    continue  # not yet launched
                if local_t > 1:
                    # Already settled — draw at destination
                    pos_t = 1.0
                else:
                    pos_t = ease_inout(local_t)

                pos_norm = bezier_path(src_pt, dst_pt, curve_offsets[p_idx], pos_t)
                px = pos_norm[0] * CANVAS
                py = pos_norm[1] * CANVAS

                # Fade particle alpha based on flight progress: bright in transit,
                # fade to 0 when settled into dst layer (so it doesn't double-draw
                # on top of dst's own roe).
                if local_t < 0.85:
                    p_alpha = 220
                elif local_t < 1.0:
                    p_alpha = int(220 * (1.0 - (local_t - 0.85) / 0.15))
                else:
                    p_alpha = 0

                if p_alpha > 0:
                    pdraw.ellipse(
                        [px - PARTICLE_RADIUS, py - PARTICLE_RADIUS,
                         px + PARTICLE_RADIUS, py + PARTICLE_RADIUS],
                        fill=(20, 20, 20, p_alpha),
                    )

            canvas = Image.alpha_composite(canvas, particle_layer)
            canvas.convert("RGB").save(out_dir / f"frame_{i:04d}.png")

            if (i + 1) % 20 == 0:
                print(f"  frame {i + 1}/{N_FRAMES}")

        # Phase 4: compile MP4
        cmd = [
            "ffmpeg", "-y", "-framerate", str(FPS),
            "-i", str(out_dir / "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            str(out_mp4),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n→ {out_mp4}")
            print(f"  frames preserved in {out_dir}/")
        else:
            print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
