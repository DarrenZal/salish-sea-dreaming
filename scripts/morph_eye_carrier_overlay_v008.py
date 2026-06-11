#!/usr/bin/env python3
"""
Eye-carrier overlay prototype.

Base: cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v007_smooth_final_settle

This is a diagnostic semantic-gravity test, not a final pure morph. It keeps
the successful raw primitive motion intact, then overlays only the Cosmic Sun
eye regions traveling toward the upper/lower Salmon eye regions. The raw eye
residue under the carriers is lightly suppressed so the authored relationship
can be evaluated without replacing the whole morph.
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

BASE_ID = "cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v007_smooth_final_settle"
PAIR_ID = "cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v008_eye_carrier_overlay"
BASE_DIR = INTERNAL / BASE_ID
OUT_DIR = INTERNAL / PAIR_ID
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
COSMIC_VIEWBOX = 108.0
SALMON_VIEWBOX = 1500.0


@dataclass(frozen=True)
class Atom:
    atom_id: str
    piece: str
    label: str
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    cx: float
    cy: float
    area: float
    png: Path


@dataclass(frozen=True)
class EyeRegion:
    name: str
    source_ids: tuple[str, ...]
    target_ids: tuple[str, ...]
    source_center: tuple[float, float]
    target_center: tuple[float, float]
    source_sprite: Image.Image
    target_sprite: Image.Image
    source_mask: Image.Image
    target_mask: Image.Image
    source_bbox: tuple[int, int, int, int]
    target_bbox: tuple[int, int, int, int]
    curve: float
    phase: float


def read_atoms(piece_dir: Path) -> dict[str, Atom]:
    atoms: dict[str, Atom] = {}
    with (piece_dir / "atom_metadata.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                atom = Atom(
                    atom_id=row["atom_id"],
                    piece=row["piece"],
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
                atoms[atom.atom_id] = atom
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


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def atom_center_px(atom: Atom, viewbox: float) -> tuple[float, float]:
    return (atom.cx / viewbox * CANVAS, atom.cy / viewbox * CANVAS)


def group_center(atoms: list[Atom], viewbox: float) -> tuple[float, float]:
    total = sum(max(1.0, a.area) for a in atoms)
    x = sum(atom_center_px(a, viewbox)[0] * max(1.0, a.area) for a in atoms) / total
    y = sum(atom_center_px(a, viewbox)[1] * max(1.0, a.area) for a in atoms) / total
    return x, y


def atom_mask(atom: Atom, viewbox: float) -> Image.Image:
    iso = Image.open(atom.png).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    mask = iso.point(lambda v: max(0, min(255, (255 - v) * 2)))
    if mask.getbbox() is not None:
        return mask.filter(ImageFilter.GaussianBlur(radius=0.25))

    scale = CANVAS / viewbox
    x = atom.bbox_x * scale
    y = atom.bbox_y * scale
    w = max(2.0, atom.bbox_w * scale)
    h = max(2.0, atom.bbox_h * scale)
    fallback = Image.new("L", (CANVAS, CANVAS), 0)
    draw = ImageDraw.Draw(fallback)
    draw.ellipse([x, y, x + w, y + h], fill=255)
    return fallback.filter(ImageFilter.GaussianBlur(radius=0.5))


def group_mask(atoms: list[Atom], viewbox: float) -> Image.Image:
    acc = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for atom in atoms:
        acc = np.maximum(acc, np.asarray(atom_mask(atom, viewbox), dtype=np.float32))
    mask = Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8), "L")
    return mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(radius=0.6))


def sprite_from_mask(img: Image.Image, mask: Image.Image, pad: int = 12) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("empty eye mask")
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(CANVAS, x1 + pad)
    y1 = min(CANVAS, y1 + pad)
    sprite = img.crop((x0, y0, x1, y1)).convert("RGBA")
    sprite.putalpha(mask.crop((x0, y0, x1, y1)))
    return sprite, (x0, y0, x1, y1)


def build_eye_regions(source_img: Image.Image, dest_img: Image.Image) -> list[EyeRegion]:
    cosmic = read_atoms(DECOMPOSED / "Nature_Cosmic_Sun")
    salmon = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    specs = [
        (
            "viewer_left_to_lower_salmon_eye",
            ("atom_0022", "atom_0023"),
            ("atom_0191", "atom_0190"),
            0.12,
            0.4,
        ),
        (
            "viewer_right_to_upper_salmon_eye",
            ("atom_0016", "atom_0017"),
            ("atom_0221", "atom_0220"),
            -0.12,
            2.7,
        ),
    ]
    regions: list[EyeRegion] = []
    for name, src_ids, dst_ids, curve, phase in specs:
        src_atoms = [cosmic[aid] for aid in src_ids]
        dst_atoms = [salmon[aid] for aid in dst_ids]
        src_mask = group_mask(src_atoms, COSMIC_VIEWBOX)
        dst_mask = group_mask(dst_atoms, SALMON_VIEWBOX)
        src_sprite, src_bbox = sprite_from_mask(source_img, src_mask, pad=14)
        dst_sprite, dst_bbox = sprite_from_mask(dest_img, dst_mask, pad=8)
        regions.append(
            EyeRegion(
                name=name,
                source_ids=src_ids,
                target_ids=dst_ids,
                source_center=group_center(src_atoms, COSMIC_VIEWBOX),
                target_center=group_center(dst_atoms, SALMON_VIEWBOX),
                source_sprite=src_sprite,
                target_sprite=dst_sprite,
                source_mask=src_mask,
                target_mask=dst_mask,
                source_bbox=src_bbox,
                target_bbox=dst_bbox,
                curve=curve,
                phase=phase,
            )
        )
    return regions


def bezier(start: tuple[float, float], end: tuple[float, float], curve: float, phase: float, t: float) -> tuple[float, float]:
    sx, sy = start[0] / CANVAS, start[1] / CANVAS
    ex, ey = end[0] / CANVAS, end[1] / CANVAS
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
    x = u * u * sx + 2 * u * t * cx + t * t * ex
    y = u * u * sy + 2 * u * t * cy + t * t * ey
    curl = math.sin(math.pi * t) * 0.012
    x += math.sin(7.0 * t + phase) * curl
    y += math.cos(6.0 * t + phase) * curl
    return x * CANVAS, y * CANVAS


def blend_arrays(a: np.ndarray, b: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    if alpha.ndim == 2:
        alpha = alpha[..., None]
    return a * (1.0 - alpha) + b * alpha


def alpha_at_center(sprite: Image.Image, center: tuple[float, float], canvas_size: int = CANVAS) -> Image.Image:
    layer = Image.new("L", (canvas_size, canvas_size), 0)
    x = int(round(center[0] - sprite.width / 2))
    y = int(round(center[1] - sprite.height / 2))
    layer.paste(sprite.getchannel("A"), (x, y))
    return layer


def resize_sprite(sprite: Image.Image, scale: float) -> Image.Image:
    return sprite.resize(
        (max(1, int(round(sprite.width * scale))), max(1, int(round(sprite.height * scale)))),
        Image.Resampling.LANCZOS,
    )


def carrier_sprite(region: EyeRegion, t: float, alpha: float) -> Image.Image:
    target_scale = min(
        1.0,
        max(
            0.18,
            0.5 * (
                region.target_sprite.width / max(1, region.source_sprite.width)
                + region.target_sprite.height / max(1, region.source_sprite.height)
            ),
        ),
    )
    scale = 1.0 + (target_scale - 1.0) * ease(t)
    src = resize_sprite(region.source_sprite, scale)
    dst = region.target_sprite.resize(src.size, Image.Resampling.LANCZOS)
    morph = ease((t - 0.64) / 0.26)
    out = Image.blend(src, dst, morph) if morph > 0 else src
    if abs((1.0 - t) * 5.0) > 0.05:
        out = out.rotate((1.0 - t) * 5.0, resample=Image.Resampling.BICUBIC, expand=True)
    out.putalpha(out.getchannel("A").point(lambda a: int(a * alpha)))
    return out


def composite_at(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def suppress_under_eye(base: Image.Image, masks: list[Image.Image], amount: float) -> Image.Image:
    if amount <= 0:
        return base
    mask_arr = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for mask in masks:
        softened = mask.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(radius=7.0))
        mask_arr = np.maximum(mask_arr, np.asarray(softened, dtype=np.float32) / 255.0)
    alpha = np.clip(mask_arr * amount, 0.0, 0.72)
    arr = np.asarray(base.convert("RGB"), dtype=np.float32)
    blurred = np.asarray(base.convert("RGB").filter(ImageFilter.GaussianBlur(radius=18)), dtype=np.float32)
    out = blend_arrays(arr, blurred, alpha)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def render() -> None:
    if OUT_DIR.exists() or OUT_MP4.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {OUT_DIR} / {OUT_MP4}")
    frames = sorted(BASE_DIR.glob("frame_*.png"))
    if len(frames) != N_FRAMES:
        raise SystemExit(f"Expected {N_FRAMES} base frames in {BASE_DIR}, found {len(frames)}")

    source_img = load_training_jpg("Nature_Cosmic_Sun.jpg")
    dest_img = load_training_jpg("Animal_Salmon_Spawn_Eggs.jpg")
    regions = build_eye_regions(source_img, dest_img)

    OUT_DIR.mkdir(parents=True, exist_ok=False)
    for i, path in enumerate(frames):
        base = Image.open(path).convert("RGBA")
        if 0 < i < 118:
            residue_masks: list[Image.Image] = []
            for region in regions:
                t = ease((i - 34) / 76.0)
                visible = ease((i - 20) / 14.0) * (1.0 - ease((i - 110) / 8.0))
                if visible <= 0:
                    continue
                center = bezier(region.source_center, region.target_center, region.curve, region.phase, t)
                sprite = carrier_sprite(region, t, 0.92 * visible)
                carrier_mask = alpha_at_center(sprite, center)
                source_residue = 0.26 * ease((i - 28) / 28.0) * (1.0 - ease((i - 90) / 22.0))
                if source_residue > 0:
                    residue_masks.append(region.source_mask.point(lambda a, s=source_residue: int(a * s)))
                residue_masks.append(carrier_mask.point(lambda a, v=visible: int(a * 0.55 * v)))
            base = suppress_under_eye(base, residue_masks, 1.0)

            for region in regions:
                t = ease((i - 34) / 76.0)
                visible = ease((i - 20) / 14.0) * (1.0 - ease((i - 110) / 8.0))
                if visible <= 0:
                    continue
                center = bezier(region.source_center, region.target_center, region.curve, region.phase, t)
                sprite = carrier_sprite(region, t, 0.92 * visible)
                x = int(round(center[0] - sprite.width / 2))
                y = int(round(center[1] - sprite.height / 2))
                composite_at(base, sprite, x, y)

        base.convert("RGB").save(OUT_DIR / f"frame_{i:04d}.png", quality=95)
        if (i + 1) % 20 == 0:
            print(f"frame {i + 1}/{N_FRAMES}")

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
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_morph_eye_carrier_overlay_v008.py")
    write_correspondence_note(regions)
    print(f"wrote {OUT_MP4}")
    print(f"frames preserved in {OUT_DIR}")


def write_correspondence_note(regions: list[EyeRegion]) -> None:
    with (OUT_DIR / "eye_carrier_correspondences.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_piece",
                "source_atom_ids",
                "dest_piece",
                "dest_atom_ids",
                "constraint",
                "notes",
            ],
        )
        writer.writeheader()
        for region in regions:
            writer.writerow(
                {
                    "source_piece": "Nature_Cosmic_Sun",
                    "source_atom_ids": " ".join(region.source_ids),
                    "dest_piece": "Animal_Salmon_Spawn_Eggs",
                    "dest_atom_ids": " ".join(region.target_ids),
                    "constraint": "eye_carrier_overlay",
                    "notes": f"Prototype overlay: {region.name}. Proposed visual relationship only; not symbolic unless Austin confirms.",
                }
            )


if __name__ == "__main__":
    render()
