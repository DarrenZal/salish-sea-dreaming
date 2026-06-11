#!/usr/bin/env python3
"""
Lane 2A v005: full atom recomposition, not just roe routing.

v004 fixed endpoint fidelity but still treated the Cosmic Sun face as residue.
v005 routes the face atoms into Salmon structural atoms while rays/trigons keep
breaking into roe particles.
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

PAIR_ID = "cosmic_sun_to_salmon_spawn_roe_particle_field_v005_full_atom_recomposition"
OUT_DIR = INTERNAL / PAIR_ID
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
COSMIC_VIEWBOX = 108.0
SALMON_VIEWBOX = 1500.0
EXTERNAL_TRIGONS = {f"atom_{i:04d}" for i in range(31, 39)}
STRUCTURAL_LABELS = {
    "formline-primary",
    "formline-secondary",
    "formline-tertiary",
    "body-element",
    "fin-tail",
    "circle-oval",
    "crescent",
    "trigon",
    "eye-focal-oval",
}


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
    sprite: Image.Image
    top_left: tuple[int, int]
    center: tuple[float, float]
    color: tuple[int, int, int]
    noise: np.ndarray
    launch_start: float
    rank: int


@dataclass
class TargetAtom:
    atom: Atom
    mask: Image.Image
    sprite: Image.Image
    top_left: tuple[int, int]
    center: tuple[float, float]
    radius: float
    color: tuple[int, int, int]


@dataclass
class RoeParticle:
    src: SourceAtom
    target: TargetAtom
    start: tuple[float, float]
    end: tuple[float, float]
    launch_frame: float
    flight_frames: float
    curve_offset: float
    curl_phase: float
    spin: float


@dataclass
class StructureMover:
    src: SourceAtom
    target: TargetAtom
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


def fallback_mask(atom: Atom, viewbox: float, kind: str) -> Image.Image:
    scale = CANVAS / viewbox
    x = atom.bbox_x * scale
    y = atom.bbox_y * scale
    w = max(2.0, atom.bbox_w * scale)
    h = max(2.0, atom.bbox_h * scale)
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(mask)
    if atom.label in {"egg-roe", "circle-oval", "eye-focal-oval"}:
        draw.ellipse([x, y, x + w, y + h], fill=255)
    elif atom.label == "trigon":
        draw.polygon([(x + w / 2, y), (x + w, y + h), (x, y + h)], fill=255)
    else:
        draw.rounded_rectangle([x, y, x + w, y + h], radius=max(2, int(min(w, h) * 0.22)), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=0.35))


def full_canvas_mask(atom: Atom, viewbox: float) -> Image.Image:
    iso = Image.open(atom.png).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    mask = iso.point(lambda v: max(0, min(255, (255 - v) * 2)))
    if mask.getbbox() is None:
        return fallback_mask(atom, viewbox, atom.label)
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


def sprite_from_mask(atom: Atom, mask: Image.Image, img: Image.Image, viewbox: float, fallback: tuple[int, int, int]) -> TargetAtom:
    bbox = mask.getbbox()
    if bbox is None:
        mask = fallback_mask(atom, viewbox, atom.label)
        bbox = mask.getbbox()
    assert bbox is not None
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - 3)
    y0 = max(0, y0 - 3)
    x1 = min(CANVAS, x1 + 3)
    y1 = min(CANVAS, y1 + 3)
    sprite = img.crop((x0, y0, x1, y1)).convert("RGBA")
    sprite.putalpha(mask.crop((x0, y0, x1, y1)))
    center = (atom.cx / viewbox * CANVAS, atom.cy / viewbox * CANVAS)
    radius = max(2.5, min(90.0, atom.bbox_w / 2.0 / viewbox * CANVAS))
    color = sampled_color(img, center[0], center[1], fallback)
    return TargetAtom(atom, mask, sprite, (x0, y0), center, radius, color)


def make_source_atom(atom: Atom, img: Image.Image, viewbox: float, rank: int, launch: float, rng: np.random.Generator) -> SourceAtom:
    mask = full_canvas_mask(atom, viewbox)
    target_like = sprite_from_mask(atom, mask, img, viewbox, (220, 110, 40))
    return SourceAtom(atom, mask, target_like.sprite, target_like.top_left, target_like.center, target_like.color, rng.random((CANVAS, CANVAS)), launch, rank)


def composite_at(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def is_ray_emitter(atom: Atom) -> bool:
    return atom.label == "sun-ray" or atom.atom_id in EXTERNAL_TRIGONS


def make_sources(cosmic_atoms: list[Atom], source_img: Image.Image, rng: np.random.Generator) -> tuple[list[SourceAtom], list[SourceAtom]]:
    rays = [a for a in cosmic_atoms if is_ray_emitter(a)]
    face = [a for a in cosmic_atoms if a.label != "background-field" and not is_ray_emitter(a)]
    rays.sort(key=lambda a: angle((a.cx / COSMIC_VIEWBOX, a.cy / COSMIC_VIEWBOX)))
    face.sort(key=lambda a: (a.label, angle((a.cx / COSMIC_VIEWBOX, a.cy / COSMIC_VIEWBOX))))
    ray_sources = [
        make_source_atom(atom, source_img, COSMIC_VIEWBOX, i, 8 + i * 1.45 + rng.uniform(-0.6, 0.6), rng)
        for i, atom in enumerate(rays)
    ]
    face_sources = [
        make_source_atom(atom, source_img, COSMIC_VIEWBOX, i, 22 + i * 2.1 + rng.uniform(-1.0, 1.0), rng)
        for i, atom in enumerate(face)
    ]
    return ray_sources, face_sources


def make_targets(salmon_atoms: list[Atom], dest_img: Image.Image) -> tuple[list[TargetAtom], list[TargetAtom]]:
    roe: list[TargetAtom] = []
    structure: list[TargetAtom] = []
    seen_struct: set[tuple[str, int, int, int, int]] = set()
    for atom in salmon_atoms:
        if atom.label == "egg-roe":
            roe.append(sprite_from_mask(atom, full_canvas_mask(atom, SALMON_VIEWBOX), dest_img, SALMON_VIEWBOX, (255, 94, 59)))
        elif atom.label in STRUCTURAL_LABELS:
            key = (
                atom.label,
                round(atom.bbox_x),
                round(atom.bbox_y),
                round(atom.bbox_w),
                round(atom.bbox_h),
            )
            if key in seen_struct:
                continue
            seen_struct.add(key)
            structure.append(sprite_from_mask(atom, full_canvas_mask(atom, SALMON_VIEWBOX), dest_img, SALMON_VIEWBOX, (130, 90, 85)))
    return roe, structure


def sample_points(source: SourceAtom, count: int, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(source.mask)
    ys, xs = np.where(arr > 50)
    if len(xs) == 0:
        return np.repeat([[source.center[0], source.center[1]]], count, axis=0)
    picks = rng.integers(0, len(xs), size=count)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    return np.column_stack([xs[picks], ys[picks]]).astype(float) + jitter


def build_roe_particles(ray_sources: list[SourceAtom], roe_targets: list[TargetAtom], rng: np.random.Generator) -> list[RoeParticle]:
    roe_sorted = sorted(
        roe_targets,
        key=lambda r: (
            angle((r.center[0] / CANVAS, r.center[1] / CANVAS)),
            math.hypot(r.center[0] / CANVAS - 0.5, r.center[1] / CANVAS - 0.5),
        ),
    )
    particles: list[RoeParticle] = []
    points_by_source: dict[int, np.ndarray] = {}
    for idx, target in enumerate(roe_sorted):
        src = ray_sources[int(idx * len(ray_sources) / max(1, len(roe_sorted)))]
        local_count = sum(1 for j in range(len(roe_sorted)) if int(j * len(ray_sources) / max(1, len(roe_sorted))) == src.rank)
        if src.rank not in points_by_source:
            points_by_source[src.rank] = sample_points(src, local_count + 4, rng)
        local_idx = sum(1 for p in particles if p.src.rank == src.rank)
        sx, sy = points_by_source[src.rank][local_idx % len(points_by_source[src.rank])]
        particles.append(
            RoeParticle(
                src=src,
                target=target,
                start=(sx / CANVAS, sy / CANVAS),
                end=(target.center[0] / CANVAS, target.center[1] / CANVAS),
                launch_frame=src.launch_start + rng.uniform(0, 16),
                flight_frames=rng.uniform(44, 62),
                curve_offset=rng.uniform(-0.2, 0.2),
                curl_phase=rng.uniform(0, math.tau),
                spin=rng.uniform(-math.pi, math.pi),
            )
        )
    return particles


def compatibility(src: SourceAtom, target: TargetAtom) -> float:
    sl = src.atom.label
    tl = target.atom.label
    if sl == tl:
        return 0.0
    if sl in {"eye-focal-oval", "circle-oval"} and tl in {"eye-focal-oval", "circle-oval"}:
        return 0.2
    if sl == "crescent" and tl in {"crescent", "formline-secondary", "formline-tertiary"}:
        return 0.25
    if sl in {"formline-primary", "trigon"} and tl in {"formline-primary", "body-element", "fin-tail", "trigon"}:
        return 0.3
    if tl in {"formline-primary", "body-element", "fin-tail"}:
        return 0.7
    return 0.5


def build_structure_movers(face_sources: list[SourceAtom], structure_targets: list[TargetAtom], rng: np.random.Generator) -> list[StructureMover]:
    targets = sorted(structure_targets, key=lambda t: (t.atom.area < 1000, angle((t.center[0] / CANVAS, t.center[1] / CANVAS))))
    usage = {src.rank: 0 for src in face_sources}
    movers: list[StructureMover] = []
    for idx, target in enumerate(targets):
        best = min(
            face_sources,
            key=lambda src: (
                compatibility(src, target)
                + usage[src.rank] * 0.23
                + abs(angle((src.center[0] / CANVAS, src.center[1] / CANVAS)) - angle((target.center[0] / CANVAS, target.center[1] / CANVAS))) * 0.08
            ),
        )
        usage[best.rank] += 1
        launch = best.launch_start + usage[best.rank] * 1.8 + rng.uniform(-1.5, 1.5)
        movers.append(
            StructureMover(
                src=best,
                target=target,
                launch_frame=launch,
                flight_frames=rng.uniform(42, 58),
                curve_offset=rng.uniform(-0.15, 0.15),
                curl_phase=rng.uniform(0, math.tau),
                spin=rng.uniform(-0.35, 0.35),
            )
        )
    return movers


def erase_source(layer: Image.Image, fill_bg: Image.Image, source: SourceAtom, frame: int, duration: float) -> None:
    progress = ease((frame - source.launch_start) / duration)
    if progress <= 0:
        return
    mask_arr = np.asarray(source.mask, dtype=np.float32) / 255.0
    threshold = np.clip(progress * 1.18 - source.noise, 0.0, 1.0)
    alpha_arr = (mask_arr * threshold * 255).astype(np.uint8)
    alpha = Image.fromarray(alpha_arr, "L").filter(ImageFilter.GaussianBlur(radius=0.45))
    patch = fill_bg.copy().convert("RGBA")
    patch.putalpha(alpha)
    layer.alpha_composite(patch)


def source_layer_for_frame(source_img: Image.Image, fill_bg: Image.Image, all_sources: list[SourceAtom], frame: int) -> Image.Image:
    layer = source_img.copy().convert("RGBA")
    for source in all_sources:
        erase_source(layer, fill_bg, source, frame, 24 if is_ray_emitter(source.atom) else 34)
    return layer


def bezier(start: tuple[float, float], end: tuple[float, float], curve: float, phase: float, t: float) -> tuple[float, float]:
    sx, sy = start
    ex, ey = end
    mx = (sx + ex) / 2.0
    my = (sy + ey) / 2.0
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy) or 1e-6
    px = -dy / length
    py = dx / length
    cx = mx + px * curve
    cy = my + py * curve
    u = 1.0 - t
    bx = u * u * sx + 2 * u * t * cx + t * t * ex
    by = u * u * sy + 2 * u * t * cy + t * t * ey
    curl = math.sin(math.pi * t) * 0.018
    bx += math.sin(8.0 * t + phase) * curl
    by += math.cos(7.0 * t + phase) * curl
    return bx, by


def transformed_sprite_between(src: SourceAtom, target: TargetAtom, t: float, alpha: int) -> Image.Image:
    source_sprite = src.sprite
    target_sprite = target.sprite
    target_w, target_h = max(1, target_sprite.width), max(1, target_sprite.height)
    scale_x = target_w / max(1, source_sprite.width)
    scale_y = target_h / max(1, source_sprite.height)
    scale = lerp(1.0, min(2.4, max(0.22, (scale_x + scale_y) / 2.0)), ease(t))
    src_resized = source_sprite.resize(
        (max(1, int(source_sprite.width * scale)), max(1, int(source_sprite.height * scale))),
        Image.Resampling.LANCZOS,
    )
    if abs((1.0 - t) * 8.0) > 0.05:
        src_resized = src_resized.rotate((1.0 - t) * 8.0, resample=Image.Resampling.BICUBIC, expand=True)

    morph_t = ease((t - 0.58) / 0.32)
    if morph_t <= 0:
        sprite = src_resized
    else:
        dst_resized = target_sprite.resize(src_resized.size, Image.Resampling.LANCZOS)
        sprite = Image.blend(src_resized, dst_resized, morph_t)
    sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a * alpha / 255)))
    return sprite


def draw_triangle(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, theta: float, color: tuple[int, int, int, int]) -> None:
    pts = []
    for a, r in [(0, 1.35), (2.45, 0.75), (-2.45, 0.75)]:
        pts.append((x + math.cos(theta + a) * radius * r, y + math.sin(theta + a) * radius * r))
    draw.polygon(pts, fill=color)


def draw_roe_particle(draw: ImageDraw.ImageDraw, p: RoeParticle, frame: int) -> None:
    local = (frame - p.launch_frame) / p.flight_frames
    if local < 0 or local > 1.0:
        return
    t = ease(local)
    x_norm, y_norm = bezier(p.start, p.end, p.curve_offset, p.curl_phase, t)
    x = x_norm * CANVAS
    y = y_norm * CANVAS
    rgb = lerp_rgb(p.src.color, p.target.color, ease((t - 0.48) / 0.4))
    alpha = int(230 * (1.0 - max(0.0, local - 0.96) / 0.04))
    radius = lerp(3.0, min(13.0, p.target.radius), ease((t - 0.65) / 0.35))
    theta = angle((p.end[0] - p.start[0], p.end[1] - p.start[1]), (0.0, 0.0)) + p.spin * (1.0 - t)
    if t < 0.68:
        draw_triangle(draw, x, y, radius, theta, (*rgb, alpha))
    elif t < 0.83:
        mix = ease((t - 0.68) / 0.15)
        draw_triangle(draw, x, y, radius * (1.0 - 0.5 * mix), theta, (*rgb, int(alpha * (1.0 - mix * 0.4))))
        draw.ellipse([x - radius * mix, y - radius * mix, x + radius * mix, y + radius * mix], fill=(*rgb, alpha))
    else:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(*rgb, alpha))


def draw_landed(layer: Image.Image, target: TargetAtom, settle: float) -> None:
    if settle <= 0:
        return
    sprite = target.sprite.copy()
    sprite.putalpha(sprite.getchannel("A").point(lambda a: int(a * settle)))
    composite_at(layer, sprite, target.top_left[0], target.top_left[1])


def draw_structure_mover(layer: Image.Image, mover: StructureMover, frame: int) -> None:
    local = (frame - mover.launch_frame) / mover.flight_frames
    if local < 0:
        return
    landed = mover.launch_frame + mover.flight_frames
    if local >= 1.0:
        draw_landed(layer, mover.target, ease((frame - landed) / 8.0))
        return
    t = ease(local)
    start = (mover.src.center[0] / CANVAS, mover.src.center[1] / CANVAS)
    end = (mover.target.center[0] / CANVAS, mover.target.center[1] / CANVAS)
    x_norm, y_norm = bezier(start, end, mover.curve_offset, mover.curl_phase, t)
    alpha = int(230 * (1.0 - max(0.0, local - 0.98) / 0.02))
    sprite = transformed_sprite_between(mover.src, mover.target, t, alpha)
    x = int(round(x_norm * CANVAS - sprite.width / 2))
    y = int(round(y_norm * CANVAS - sprite.height / 2))
    composite_at(layer, sprite, x, y)


def draw_roe_targets(draw: ImageDraw.ImageDraw, roe_targets: list[TargetAtom], alpha: int) -> None:
    for target in roe_targets:
        x, y = target.center
        r = max(2.0, min(48.0, target.radius))
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

    rng = np.random.default_rng(2026051705)
    source_img = load_training_jpg("Nature_Cosmic_Sun.jpg")
    dest_img = load_training_jpg("Animal_Salmon_Spawn_Eggs.jpg")
    # Fill source holes with a warm, low-detail field rather than white or a
    # whole-image fade; destination atoms are responsible for recomposition.
    fill_bg = Image.blend(source_img.filter(ImageFilter.GaussianBlur(radius=26)), Image.new("RGB", (CANVAS, CANVAS), (246, 237, 237)), 0.38)

    cosmic_atoms = read_atoms(DECOMPOSED / "Nature_Cosmic_Sun")
    salmon_atoms = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    ray_sources, face_sources = make_sources(cosmic_atoms, source_img, rng)
    roe_targets, structure_targets = make_targets(salmon_atoms, dest_img)
    roe_particles = build_roe_particles(ray_sources, roe_targets, rng)
    structure_movers = build_structure_movers(face_sources, structure_targets, rng)
    all_sources = ray_sources + face_sources

    print(f"source endpoint: {TRAINING / 'Nature_Cosmic_Sun.jpg'}")
    print(f"destination endpoint: {TRAINING / 'Animal_Salmon_Spawn_Eggs.jpg'}")
    print(f"ray/trigon sources to roe: {len(ray_sources)}")
    print(f"face atom sources to structure: {len(face_sources)}")
    print(f"roe targets/particles: {len(roe_targets)} / {len(roe_particles)}")
    print(f"structural targets/movers: {len(structure_targets)} / {len(structure_movers)}")

    OUT_DIR.mkdir(parents=True, exist_ok=False)
    for frame in range(N_FRAMES):
        if frame == 0:
            canvas = source_img.copy().convert("RGBA")
        else:
            canvas = source_layer_for_frame(source_img, fill_bg, all_sources, frame)

            ghost_alpha = int(18 * ease((frame - 12) / 18.0) * (1.0 - 0.65 * ease((frame - 86) / 20.0)))
            if ghost_alpha > 0 and frame < 104:
                ghost = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
                draw_roe_targets(ImageDraw.Draw(ghost), roe_targets, ghost_alpha)
                canvas.alpha_composite(ghost)

            atom_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            atom_draw = ImageDraw.Draw(atom_layer)
            for particle in roe_particles:
                draw_roe_particle(atom_draw, particle, frame)
                draw_landed(atom_layer, particle.target, ease((frame - (particle.launch_frame + particle.flight_frames)) / 8.0))
            for mover in structure_movers:
                draw_structure_mover(atom_layer, mover, frame)
            canvas.alpha_composite(atom_layer)

            final_alpha = ease((frame - 116) / 3.0)
            if final_alpha > 0:
                final = dest_img.copy().convert("RGBA")
                final.putalpha(final.getchannel("A").point(lambda a: int(a * final_alpha)))
                canvas.alpha_composite(final)

        canvas.convert("RGB").save(OUT_DIR / f"frame_{frame:04d}.png", quality=95)
        if (frame + 1) % 20 == 0:
            print(f"frame {frame + 1}/{N_FRAMES}")

    compile_mp4()
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_morph_roe_particle_field_v005.py")
    print(f"wrote {OUT_MP4}")
    print(f"frames preserved in {OUT_DIR}")


if __name__ == "__main__":
    main()
