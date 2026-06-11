#!/usr/bin/env python3
"""
Lane 2A v003: Cosmic Sun rays/trigons decompose into a Salmon roe field.

This renderer intentionally avoids the v001/v002 full-piece crossfade pattern.
Source ray atoms are erased as their particle batches launch; destination roe
targets are only faint guides until particles land. The full Salmon Spawn Eggs
render is used only as a short final settle after the particle field is built.
"""
from __future__ import annotations

import csv
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
SOURCE_VECTORS = ROOT / "track2-deterministic/source-vectors"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

PAIR_ID = "cosmic_sun_to_salmon_spawn_roe_particle_field_v003_no_global_fade"
OUT_DIR = INTERNAL / PAIR_ID
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
COSMIC_VIEWBOX = 108.0
SALMON_VIEWBOX = 1500.0
SOURCE_LABELS = {"sun-ray", "trigon"}
ROE_PALETTE = [
    (255, 94, 59),
    (235, 79, 61),
    (135, 84, 81),
    (120, 73, 63),
    (199, 185, 186),
]


@dataclass(frozen=True)
class Atom:
    atom_id: str
    label: str
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    cx: float
    cy: float
    area: float
    png: Path


@dataclass
class SourceMask:
    atom: Atom
    x: int
    y: int
    w: int
    h: int
    mask: Image.Image
    rank: int
    launch_start: float
    points: np.ndarray


@dataclass
class Particle:
    src_rank: int
    start: tuple[float, float]
    end: tuple[float, float]
    src_color: tuple[int, int, int]
    dst_color: tuple[int, int, int]
    dst_radius: float
    launch_frame: float
    flight_frames: float
    curve_offset: float
    curl_phase: float
    spin: float


def read_atoms(piece_dir: Path) -> list[Atom]:
    atoms: list[Atom] = []
    with (piece_dir / "atom_metadata.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                atoms.append(
                    Atom(
                        atom_id=row["atom_id"],
                        label=row["ai_label"],
                        bbox_x=float(row["bbox_x"]),
                        bbox_y=float(row["bbox_y"]),
                        bbox_w=float(row["bbox_w"]),
                        bbox_h=float(row["bbox_h"]),
                        cx=float(row["centroid_x"]),
                        cy=float(row["centroid_y"]),
                        area=float(row["area"]),
                        png=piece_dir / row["isolated_png"],
                    )
                )
            except (KeyError, ValueError):
                continue
    return atoms


def render_svg(svg_path: Path, out_path: Path) -> None:
    subprocess.run(
        [
            "magick",
            "-background",
            "white",
            "-density",
            "180",
            str(svg_path),
            "-resize",
            f"{CANVAS}x{CANVAS}",
            "-gravity",
            "center",
            "-extent",
            f"{CANVAS}x{CANVAS}",
            str(out_path),
        ],
        check=True,
    )


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def angle(pt: tuple[float, float], center: tuple[float, float] = (0.5, 0.5)) -> float:
    return math.atan2(pt[1] - center[1], pt[0] - center[0])


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(lerp(a[0], b[0], t)),
        int(lerp(a[1], b[1], t)),
        int(lerp(a[2], b[2], t)),
    )


def atom_mask(atom: Atom) -> Image.Image:
    """Return an antialiased mask from a white-background isolated atom PNG."""
    rgb = Image.open(atom.png).convert("RGB")
    gray = rgb.convert("L")
    mask = gray.point(lambda v: max(0, min(255, int((255 - v) * 2.2))))
    return mask.filter(ImageFilter.GaussianBlur(radius=0.35))


def mask_for_canvas(atom: Atom, viewbox: float) -> tuple[int, int, int, int, Image.Image]:
    scale = CANVAS / viewbox
    x = int(round(atom.bbox_x * scale))
    y = int(round(atom.bbox_y * scale))
    w = max(1, int(round(atom.bbox_w * scale)))
    h = max(1, int(round(atom.bbox_h * scale)))
    mask = atom_mask(atom).resize((w, h), Image.Resampling.LANCZOS)
    return x, y, w, h, mask


def composite_at(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def erase_with_mask(layer: Image.Image, smask: SourceMask, amount: float) -> None:
    if amount <= 0:
        return
    amount = max(0.0, min(1.0, amount))
    alpha = smask.mask.point(lambda a: int(a * amount))
    overlay = Image.new("RGBA", (smask.w, smask.h), (255, 255, 255, 0))
    overlay.putalpha(alpha)
    composite_at(layer, overlay, smask.x, smask.y)


def sample_points_from_mask(
    smask: SourceMask,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    arr = np.asarray(smask.mask)
    ys, xs = np.where(arr > 30)
    if len(xs) == 0:
        return np.repeat(
            [[smask.atom.cx / COSMIC_VIEWBOX * CANVAS, smask.atom.cy / COSMIC_VIEWBOX * CANVAS]],
            count,
            axis=0,
        )
    picks = rng.integers(0, len(xs), size=count)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    pts = np.column_stack([xs[picks], ys[picks]]).astype(float) + jitter
    pts[:, 0] += smask.x
    pts[:, 1] += smask.y
    return pts


def sampled_color(img: Image.Image, x: float, y: float, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    xi = int(round(x))
    yi = int(round(y))
    if xi < 0 or yi < 0 or xi >= img.width or yi >= img.height:
        return fallback
    patch = img.crop((max(0, xi - 2), max(0, yi - 2), min(img.width, xi + 3), min(img.height, yi + 3)))
    arr = np.asarray(patch.convert("RGB")).reshape(-1, 3)
    # Prefer saturated/non-background pixels when possible.
    chroma = arr.max(axis=1) - arr.min(axis=1)
    nonwhite = np.where((arr.mean(axis=1) < 235) | (chroma > 20))[0]
    if len(nonwhite):
        rgb = arr[nonwhite].mean(axis=0)
        return tuple(int(v) for v in rgb)
    return fallback


def build_source_masks(source_atoms: list[Atom], rng: np.random.Generator) -> list[SourceMask]:
    selected = [a for a in source_atoms if a.label in SOURCE_LABELS]
    selected.sort(key=lambda a: angle((a.cx / COSMIC_VIEWBOX, a.cy / COSMIC_VIEWBOX)))
    masks: list[SourceMask] = []
    for rank, atom in enumerate(selected):
        x, y, w, h, mask = mask_for_canvas(atom, COSMIC_VIEWBOX)
        launch_start = 8 + rank * 2.0 + rng.uniform(-1.0, 1.0)
        placeholder = SourceMask(atom, x, y, w, h, mask, rank, launch_start, np.empty((0, 2)))
        masks.append(placeholder)
    return masks


def build_particles(
    source_masks: list[SourceMask],
    roe_atoms: list[Atom],
    src_img: Image.Image,
    dst_img: Image.Image,
    rng: np.random.Generator,
) -> list[Particle]:
    roe = sorted(
        roe_atoms,
        key=lambda a: (
            angle((a.cx / SALMON_VIEWBOX, a.cy / SALMON_VIEWBOX)),
            math.hypot(a.cx / SALMON_VIEWBOX - 0.5, a.cy / SALMON_VIEWBOX - 0.5),
        ),
    )

    particles: list[Particle] = []
    points_by_source: dict[int, np.ndarray] = {}
    for idx, dst in enumerate(roe):
        smask = source_masks[int(idx * len(source_masks) / max(1, len(roe)))]
        source_count = sum(1 for j in range(len(roe)) if int(j * len(source_masks) / max(1, len(roe))) == smask.rank)
        if smask.rank not in points_by_source:
            points_by_source[smask.rank] = sample_points_from_mask(smask, source_count + 4, rng)
        local_index = sum(1 for p in particles if p.src_rank == smask.rank)
        start_px, start_py = points_by_source[smask.rank][local_index % len(points_by_source[smask.rank])]

        end_px = dst.cx / SALMON_VIEWBOX * CANVAS
        end_py = dst.cy / SALMON_VIEWBOX * CANVAS
        dst_radius = max(3.0, min(38.0, (dst.bbox_w / 2.0) / SALMON_VIEWBOX * CANVAS))

        src_color = sampled_color(src_img, start_px, start_py, (40, 25, 18))
        dst_color = sampled_color(dst_img, end_px, end_py, ROE_PALETTE[idx % len(ROE_PALETTE)])
        if sum(dst_color) > 690:
            dst_color = ROE_PALETTE[idx % len(ROE_PALETTE)]

        launch = smask.launch_start + rng.uniform(0, 20)
        flight = rng.uniform(48, 66)
        particles.append(
            Particle(
                src_rank=smask.rank,
                start=(start_px / CANVAS, start_py / CANVAS),
                end=(end_px / CANVAS, end_py / CANVAS),
                src_color=src_color,
                dst_color=dst_color,
                dst_radius=dst_radius,
                launch_frame=launch,
                flight_frames=flight,
                curve_offset=rng.uniform(-0.22, 0.22),
                curl_phase=rng.uniform(0, math.tau),
                spin=rng.uniform(-math.pi, math.pi),
            )
        )
    return particles


def bezier(p: Particle, t: float) -> tuple[float, float]:
    sx, sy = p.start
    ex, ey = p.end
    mx = (sx + ex) / 2.0
    my = (sy + ey) / 2.0
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy) or 1e-6
    px = -dy / length
    py = dx / length
    cx = mx + px * p.curve_offset
    cy = my + py * p.curve_offset
    u = 1.0 - t
    bx = u * u * sx + 2 * u * t * cx + t * t * ex
    by = u * u * sy + 2 * u * t * cy + t * t * ey
    curl = math.sin(math.pi * t) * 0.025
    bx += math.sin(8 * t + p.curl_phase) * curl
    by += math.cos(7 * t + p.curl_phase) * curl
    return bx, by


def draw_triangle(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    radius: float,
    theta: float,
    color: tuple[int, int, int, int],
) -> None:
    pts = []
    for a, r in [(0, 1.35), (2.45, 0.75), (-2.45, 0.75)]:
        pts.append((x + math.cos(theta + a) * radius * r, y + math.sin(theta + a) * radius * r))
    draw.polygon(pts, fill=color)


def draw_roe_targets(draw: ImageDraw.ImageDraw, roe_atoms: list[Atom], alpha: int) -> None:
    for atom in roe_atoms:
        cx = atom.cx / SALMON_VIEWBOX * CANVAS
        cy = atom.cy / SALMON_VIEWBOX * CANVAS
        radius = max(2.0, min(42.0, (atom.bbox_w / 2.0) / SALMON_VIEWBOX * CANVAS))
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(135, 84, 81, alpha),
            width=1,
        )


def source_layer_for_frame(src_img: Image.Image, source_masks: list[SourceMask], frame: int) -> Image.Image:
    layer = src_img.copy()
    for smask in source_masks:
        p = ease((frame - smask.launch_start) / 30.0)
        erase_with_mask(layer, smask, p)

    # Non-ray sun structure exits by an expanding white aperture, so the source
    # clears spatially instead of by whole-image alpha fade.
    core_p = ease((frame - 58) / 34.0)
    if core_p > 0:
        mask = Image.new("L", (CANVAS, CANVAS), 0)
        d = ImageDraw.Draw(mask)
        radius = lerp(60, 620, core_p)
        d.ellipse([CANVAS / 2 - radius, CANVAS / 2 - radius, CANVAS / 2 + radius, CANVAS / 2 + radius], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
        overlay = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 0))
        overlay.putalpha(mask)
        layer.alpha_composite(overlay)
    return layer


def draw_particle(draw: ImageDraw.ImageDraw, p: Particle, frame: int) -> None:
    local = (frame - p.launch_frame) / p.flight_frames
    if local < 0:
        return

    if local <= 1.0:
        t = ease(local)
        x_norm, y_norm = bezier(p, t)
        x = x_norm * CANVAS
        y = y_norm * CANVAS
        color_t = ease((t - 0.45) / 0.45)
        rgb = lerp_rgb(p.src_color, p.dst_color, color_t)
        alpha = int(220 * (1.0 - max(0.0, local - 0.94) / 0.06))
        radius = lerp(4.0, min(15.0, p.dst_radius), ease((t - 0.62) / 0.38))
        theta = angle((p.end[0] - p.start[0], p.end[1] - p.start[1]), (0.0, 0.0)) + p.spin * (1.0 - t)
        if t < 0.68:
            draw_triangle(draw, x, y, radius, theta, (*rgb, alpha))
        elif t < 0.82:
            mix = ease((t - 0.68) / 0.14)
            draw_triangle(draw, x, y, radius * (1.0 - 0.45 * mix), theta, (*rgb, int(alpha * (1.0 - mix * 0.45))))
            draw.ellipse([x - radius * mix, y - radius * mix, x + radius * mix, y + radius * mix], fill=(*rgb, alpha))
        else:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*rgb, alpha))
        return

    settled = ease(min(1.0, (frame - (p.launch_frame + p.flight_frames)) / 10.0))
    radius = lerp(4.0, p.dst_radius, settled)
    x = p.end[0] * CANVAS
    y = p.end[1] * CANVAS
    alpha = int(230 * settled)
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*p.dst_color, alpha))


def compile_mp4(frames_dir: Path, mp4_out: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(mp4_out),
        ],
        check=True,
    )


def main() -> None:
    if OUT_DIR.exists() or OUT_MP4.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {OUT_DIR} / {OUT_MP4}")

    rng = np.random.default_rng(20260517)
    cosmic_atoms = read_atoms(DECOMPOSED / "Nature_Cosmic_Sun")
    salmon_atoms = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    source_masks = build_source_masks(cosmic_atoms, rng)
    roe_atoms = [a for a in salmon_atoms if a.label == "egg-roe"]

    print(f"source ray/trigon atoms: {len(source_masks)}")
    print(f"destination roe atoms: {len(roe_atoms)}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src_png = tmp_path / "source.png"
        dst_png = tmp_path / "destination.png"
        render_svg(SOURCE_VECTORS / "Nature_Cosmic_Sun.svg", src_png)
        render_svg(SOURCE_VECTORS / "Animal_Salmon_Spawn_Eggs.svg", dst_png)
        src_img = Image.open(src_png).convert("RGBA")
        dst_img = Image.open(dst_png).convert("RGBA")

        particles = build_particles(source_masks, roe_atoms, src_img, dst_img, rng)
        print(f"particles: {len(particles)}")

        OUT_DIR.mkdir(parents=True, exist_ok=False)
        for frame in range(N_FRAMES):
            canvas = Image.new("RGBA", (CANVAS, CANVAS), (255, 255, 255, 255))

            if frame < 100:
                canvas.alpha_composite(source_layer_for_frame(src_img, source_masks, frame))

            ghost_alpha = int(28 * ease((frame - 10) / 18.0) * (1.0 - 0.55 * ease((frame - 84) / 20.0)))
            if ghost_alpha > 0 and frame < 108:
                ghost = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
                draw_roe_targets(ImageDraw.Draw(ghost), roe_atoms, ghost_alpha)
                canvas.alpha_composite(ghost)

            particle_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            pdraw = ImageDraw.Draw(particle_layer)
            for particle in particles:
                draw_particle(pdraw, particle, frame)
            canvas.alpha_composite(particle_layer)

            final_alpha = ease((frame - 108) / 11.0)
            if final_alpha > 0:
                final = dst_img.copy()
                final.putalpha(final.getchannel("A").point(lambda a: int(a * final_alpha)))
                canvas.alpha_composite(final)

            canvas.convert("RGB").save(OUT_DIR / f"frame_{frame:04d}.png", quality=95)
            if (frame + 1) % 20 == 0:
                print(f"frame {frame + 1}/{N_FRAMES}")

        compile_mp4(OUT_DIR, OUT_MP4)
        print(f"wrote {OUT_MP4}")
        print(f"frames preserved in {OUT_DIR}")

    # Keep a tiny reproducibility marker inside the output folder.
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_morph_roe_particle_field_v003.py")


if __name__ == "__main__":
    main()
