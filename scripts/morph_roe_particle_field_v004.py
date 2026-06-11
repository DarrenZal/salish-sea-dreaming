#!/usr/bin/env python3
"""
Lane 2A v004: source-fidelity roe-particle morph.

v003 proved the routing architecture but started from a broken SVG render.
v004 starts from the verified training JPG and derives source/destination atom
sprites from the real endpoint images plus decomposed full-canvas atom masks.
"""
from __future__ import annotations

import csv
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

PAIR_ID = "cosmic_sun_to_salmon_spawn_roe_particle_field_v004_source_fidelity"
OUT_DIR = INTERNAL / PAIR_ID
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
COSMIC_VIEWBOX = 108.0
SALMON_VIEWBOX = 1500.0
SOURCE_LABELS = {"sun-ray", "trigon"}


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
class SourceAtom:
    atom: Atom
    mask: Image.Image
    noise: np.ndarray
    launch_start: float
    rank: int


@dataclass
class RoeSprite:
    atom: Atom
    sprite: Image.Image
    top_left: tuple[int, int]
    center: tuple[float, float]
    radius: float
    color: tuple[int, int, int]


@dataclass
class Particle:
    src_rank: int
    source_atom: SourceAtom
    roe: RoeSprite
    start: tuple[float, float]
    end: tuple[float, float]
    src_color: tuple[int, int, int]
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


def load_training_jpg(name: str) -> Image.Image:
    img = Image.open(TRAINING / name).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    if img.size == (CANVAS, CANVAS):
        return img
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    canvas.paste(img, ((CANVAS - img.width) // 2, (CANVAS - img.height) // 2))
    return canvas


def full_canvas_mask(atom: Atom) -> Image.Image:
    """Isolated atom PNGs are full-canvas white/black masks, not transparent sprites."""
    iso = Image.open(atom.png).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    mask = iso.point(lambda v: max(0, min(255, (255 - v) * 2)))
    return mask.filter(ImageFilter.GaussianBlur(radius=0.25))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def angle(pt: tuple[float, float], center: tuple[float, float] = (0.5, 0.5)) -> float:
    return math.atan2(pt[1] - center[1], pt[0] - center[0])


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (int(lerp(a[0], b[0], t)), int(lerp(a[1], b[1], t)), int(lerp(a[2], b[2], t)))


def sampled_color(img: Image.Image, x: float, y: float, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    xi = int(round(x))
    yi = int(round(y))
    if xi < 0 or yi < 0 or xi >= img.width or yi >= img.height:
        return fallback
    patch = img.crop((max(0, xi - 2), max(0, yi - 2), min(img.width, xi + 3), min(img.height, yi + 3)))
    arr = np.asarray(patch.convert("RGB")).reshape(-1, 3)
    return tuple(int(v) for v in arr.mean(axis=0))


def composite_at(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def make_source_atoms(atoms: list[Atom], rng: np.random.Generator) -> list[SourceAtom]:
    selected = [a for a in atoms if a.label in SOURCE_LABELS]
    selected.sort(key=lambda a: angle((a.cx / COSMIC_VIEWBOX, a.cy / COSMIC_VIEWBOX)))
    result: list[SourceAtom] = []
    for rank, atom in enumerate(selected):
        mask = full_canvas_mask(atom)
        noise = rng.random((CANVAS, CANVAS))
        launch_start = 10 + rank * 1.55 + rng.uniform(-0.7, 0.7)
        result.append(SourceAtom(atom=atom, mask=mask, noise=noise, launch_start=launch_start, rank=rank))
    return result


def make_roe_sprite(atom: Atom, dest_img: Image.Image) -> RoeSprite | None:
    mask = full_canvas_mask(atom)
    bbox = mask.getbbox()
    if bbox is None:
        return None
    x0, y0, x1, y1 = bbox
    # Add a small margin so antialias edges survive sprite transforms.
    x0 = max(0, x0 - 2)
    y0 = max(0, y0 - 2)
    x1 = min(CANVAS, x1 + 2)
    y1 = min(CANVAS, y1 + 2)
    base_crop = dest_img.crop((x0, y0, x1, y1)).convert("RGBA")
    alpha = mask.crop((x0, y0, x1, y1))
    base_crop.putalpha(alpha)
    center = (atom.cx / SALMON_VIEWBOX * CANVAS, atom.cy / SALMON_VIEWBOX * CANVAS)
    radius = max(2.0, min(54.0, atom.bbox_w / 2.0 / SALMON_VIEWBOX * CANVAS))
    color = sampled_color(dest_img, center[0], center[1], (255, 94, 59))
    return RoeSprite(atom=atom, sprite=base_crop, top_left=(x0, y0), center=center, radius=radius, color=color)


def sample_points(source: SourceAtom, count: int, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(source.mask)
    ys, xs = np.where(arr > 50)
    if len(xs) == 0:
        cx = source.atom.cx / COSMIC_VIEWBOX * CANVAS
        cy = source.atom.cy / COSMIC_VIEWBOX * CANVAS
        return np.repeat([[cx, cy]], count, axis=0)
    picks = rng.integers(0, len(xs), size=count)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    return np.column_stack([xs[picks], ys[picks]]).astype(float) + jitter


def build_particles(
    source_atoms: list[SourceAtom],
    roe_sprites: list[RoeSprite],
    source_img: Image.Image,
    rng: np.random.Generator,
) -> list[Particle]:
    roe_sorted = sorted(
        roe_sprites,
        key=lambda r: (
            angle((r.center[0] / CANVAS, r.center[1] / CANVAS)),
            math.hypot(r.center[0] / CANVAS - 0.5, r.center[1] / CANVAS - 0.5),
        ),
    )
    particles: list[Particle] = []
    points_by_source: dict[int, np.ndarray] = {}
    for idx, roe in enumerate(roe_sorted):
        src = source_atoms[int(idx * len(source_atoms) / max(1, len(roe_sorted)))]
        local_count = sum(
            1
            for j in range(len(roe_sorted))
            if int(j * len(source_atoms) / max(1, len(roe_sorted))) == src.rank
        )
        if src.rank not in points_by_source:
            points_by_source[src.rank] = sample_points(src, local_count + 4, rng)
        local_idx = sum(1 for p in particles if p.src_rank == src.rank)
        sx, sy = points_by_source[src.rank][local_idx % len(points_by_source[src.rank])]
        src_color = sampled_color(source_img, sx, sy, (220, 90, 35))
        launch = src.launch_start + rng.uniform(0, 15)
        particles.append(
            Particle(
                src_rank=src.rank,
                source_atom=src,
                roe=roe,
                start=(sx / CANVAS, sy / CANVAS),
                end=(roe.center[0] / CANVAS, roe.center[1] / CANVAS),
                src_color=src_color,
                launch_frame=launch,
                flight_frames=rng.uniform(46, 63),
                curve_offset=rng.uniform(-0.2, 0.2),
                curl_phase=rng.uniform(0, math.tau),
                spin=rng.uniform(-math.pi, math.pi),
            )
        )
    return particles


def erase_source_atom(layer: Image.Image, source_bg: Image.Image, source: SourceAtom, frame: int) -> None:
    progress = ease((frame - source.launch_start) / 28.0)
    if progress <= 0:
        return
    mask_arr = np.asarray(source.mask, dtype=np.float32) / 255.0
    # Stochastic erasure fragments rays/trigons instead of uniformly fading them.
    threshold = np.clip((progress * 1.18) - source.noise, 0.0, 1.0)
    alpha_arr = (mask_arr * threshold * 255).astype(np.uint8)
    alpha = Image.fromarray(alpha_arr, "L").filter(ImageFilter.GaussianBlur(radius=0.45))
    patch = source_bg.copy().convert("RGBA")
    patch.putalpha(alpha)
    layer.alpha_composite(patch)


def source_layer_for_frame(source_img: Image.Image, source_bg: Image.Image, source_atoms: list[SourceAtom], frame: int) -> Image.Image:
    layer = source_img.copy().convert("RGBA")
    for source in source_atoms:
        erase_source_atom(layer, source_bg, source, frame)

    # Late granular clearing of remaining face/background identity. This avoids
    # the v003 blank white disc: the face leaves as noise and warm blur, not a
    # circular aperture.
    late = ease((frame - 86) / 24.0)
    if late > 0:
        yy, xx = np.mgrid[0:CANVAS, 0:CANVAS]
        radial = np.sqrt((xx - CANVAS / 2) ** 2 + (yy - CANVAS / 2) ** 2) / (CANVAS / 2)
        soft = np.clip((1.08 - radial) * late, 0.0, 1.0)
        noise = ((np.sin(xx * 0.087 + frame * 0.23) + np.cos(yy * 0.071 - frame * 0.19)) * 0.5 + 0.5)
        alpha_arr = (soft * np.clip(late * 1.15 - noise * 0.55, 0.0, 1.0) * 210).astype(np.uint8)
        alpha = Image.fromarray(alpha_arr, "L").filter(ImageFilter.GaussianBlur(radius=1.2))
        clearing = Image.new("RGBA", (CANVAS, CANVAS), (246, 237, 237, 0))
        clearing.putalpha(alpha)
        layer.alpha_composite(clearing)
    return layer


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
    curl = math.sin(math.pi * t) * 0.024
    bx += math.sin(8.5 * t + p.curl_phase) * curl
    by += math.cos(7.5 * t + p.curl_phase) * curl
    return bx, by


def draw_triangle(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, theta: float, color: tuple[int, int, int, int]) -> None:
    pts = []
    for a, r in [(0, 1.35), (2.45, 0.75), (-2.45, 0.75)]:
        pts.append((x + math.cos(theta + a) * radius * r, y + math.sin(theta + a) * radius * r))
    draw.polygon(pts, fill=color)


def draw_particle(draw: ImageDraw.ImageDraw, p: Particle, frame: int) -> None:
    local = (frame - p.launch_frame) / p.flight_frames
    if local < 0:
        return
    if local <= 1.0:
        t = ease(local)
        x_norm, y_norm = bezier(p, t)
        x = x_norm * CANVAS
        y = y_norm * CANVAS
        color_t = ease((t - 0.48) / 0.38)
        rgb = lerp_rgb(p.src_color, p.roe.color, color_t)
        alpha = int(230 * (1.0 - max(0.0, local - 0.96) / 0.04))
        radius = lerp(3.2, min(14.0, p.roe.radius), ease((t - 0.65) / 0.35))
        theta = angle((p.end[0] - p.start[0], p.end[1] - p.start[1]), (0.0, 0.0)) + p.spin * (1.0 - t)
        if t < 0.68:
            draw_triangle(draw, x, y, radius, theta, (*rgb, alpha))
        elif t < 0.83:
            mix = ease((t - 0.68) / 0.15)
            draw_triangle(draw, x, y, radius * (1.0 - 0.5 * mix), theta, (*rgb, int(alpha * (1.0 - mix * 0.4))))
            draw.ellipse([x - radius * mix, y - radius * mix, x + radius * mix, y + radius * mix], fill=(*rgb, alpha))
        else:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*rgb, alpha))


def draw_landed_roe(layer: Image.Image, particles: list[Particle], frame: int) -> None:
    for p in particles:
        landed_frame = p.launch_frame + p.flight_frames
        settle = ease((frame - landed_frame) / 8.0)
        if settle <= 0:
            continue
        sprite = p.roe.sprite.copy()
        sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a * settle)))
        composite_at(layer, sprite, p.roe.top_left[0], p.roe.top_left[1])


def draw_roe_targets(draw: ImageDraw.ImageDraw, roe_sprites: list[RoeSprite], alpha: int) -> None:
    for roe in roe_sprites:
        x, y = roe.center
        r = max(2.0, min(48.0, roe.radius))
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(135, 84, 81, alpha), width=1)


def compile_mp4() -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(OUT_DIR / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(OUT_MP4),
        ],
        check=True,
    )


def main() -> None:
    if OUT_DIR.exists() or OUT_MP4.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {OUT_DIR} / {OUT_MP4}")

    rng = np.random.default_rng(2026051704)
    source_img = load_training_jpg("Nature_Cosmic_Sun.jpg")
    dest_img = load_training_jpg("Animal_Salmon_Spawn_Eggs.jpg")
    source_bg = source_img.filter(ImageFilter.GaussianBlur(radius=24))

    cosmic_atoms = read_atoms(DECOMPOSED / "Nature_Cosmic_Sun")
    salmon_atoms = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    source_atoms = make_source_atoms(cosmic_atoms, rng)
    roe_sprites = [
        sprite
        for atom in salmon_atoms
        if atom.label == "egg-roe"
        for sprite in [make_roe_sprite(atom, dest_img)]
        if sprite is not None
    ]
    particles = build_particles(source_atoms, roe_sprites, source_img, rng)

    print(f"source endpoint: {TRAINING / 'Nature_Cosmic_Sun.jpg'}")
    print(f"destination endpoint: {TRAINING / 'Animal_Salmon_Spawn_Eggs.jpg'}")
    print(f"source ray/trigon atoms: {len(source_atoms)}")
    print(f"destination roe sprites: {len(roe_sprites)}")
    print(f"particles: {len(particles)}")

    OUT_DIR.mkdir(parents=True, exist_ok=False)
    for frame in range(N_FRAMES):
        if frame == 0:
            canvas = source_img.copy().convert("RGBA")
        else:
            canvas = source_layer_for_frame(source_img, source_bg, source_atoms, frame)

            ghost_alpha = int(24 * ease((frame - 14) / 18.0) * (1.0 - 0.65 * ease((frame - 86) / 20.0)))
            if ghost_alpha > 0 and frame < 108:
                ghost = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
                draw_roe_targets(ImageDraw.Draw(ghost), roe_sprites, ghost_alpha)
                canvas.alpha_composite(ghost)

            particle_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            pdraw = ImageDraw.Draw(particle_layer)
            for particle in particles:
                draw_particle(pdraw, particle, frame)
            draw_landed_roe(particle_layer, particles, frame)
            canvas.alpha_composite(particle_layer)

            final_alpha = ease((frame - 114) / 5.0)
            if final_alpha > 0:
                final = dest_img.copy().convert("RGBA")
                final.putalpha(final.getchannel("A").point(lambda a: int(a * final_alpha)))
                canvas.alpha_composite(final)

        canvas.convert("RGB").save(OUT_DIR / f"frame_{frame:04d}.png", quality=95)
        if (frame + 1) % 20 == 0:
            print(f"frame {frame + 1}/{N_FRAMES}")

    compile_mp4()
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_morph_roe_particle_field_v004.py")
    print(f"wrote {OUT_MP4}")
    print(f"frames preserved in {OUT_DIR}")


if __name__ == "__main__":
    main()
