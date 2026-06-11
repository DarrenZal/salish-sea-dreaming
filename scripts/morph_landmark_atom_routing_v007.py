#!/usr/bin/env python3
"""
Landmark-constrained atom routing v007.

This experiment adds an authored correspondence layer before rendering. Human
pins override the automatic assignment cost matrix; background-field atoms are
excluded from motion; unpinned face atoms are assigned by weighted visual cost.

The correspondence language is intentionally visual and provisional. These are
not symbolic claims unless Austin confirms them.
"""
from __future__ import annotations

import argparse
import csv
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

DEFAULT_PAIR_ID = "cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007"
PAIR_ID = DEFAULT_PAIR_ID
OUT_DIR = INTERNAL / PAIR_ID
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"
CORRESPONDENCES = OUT_DIR / "morph_correspondences.csv"
DIAGNOSTIC = OUT_DIR / "diagnostic_landmark_correspondences_v007.png"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
COSMIC_VIEWBOX = 108.0
SALMON_VIEWBOX = 1500.0
EXTERNAL_TRIGONS = {f"atom_{i:04d}" for i in range(31, 39)}
EXCLUDED_LABELS = {"background-field", "negative-space", "other"}
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


def set_pair_id(pair_id: str) -> None:
    global PAIR_ID, OUT_DIR, OUT_MP4, CORRESPONDENCES, DIAGNOSTIC
    PAIR_ID = pair_id
    OUT_DIR = INTERNAL / PAIR_ID
    OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"
    CORRESPONDENCES = OUT_DIR / "morph_correspondences.csv"
    suffix = pair_id.replace("cosmic_sun_to_salmon_spawn_landmark_atom_routing_", "")
    DIAGNOSTIC = OUT_DIR / f"diagnostic_landmark_correspondences_{suffix}.png"

PIN_SPECS = [
    (
        "atom_0022",
        "atom_0191",
        "pin",
        "Proposed visual pin: Cosmic Sun viewer-left eye oval to lower Salmon eye ovoid.",
    ),
    (
        "atom_0023",
        "atom_0190",
        "pin",
        "Proposed visual pin: Cosmic Sun viewer-left pupil/detail to lower Salmon eye detail.",
    ),
    (
        "atom_0016",
        "atom_0221",
        "pin",
        "Proposed visual pin: Cosmic Sun viewer-right eye oval to upper Salmon eye ovoid.",
    ),
    (
        "atom_0017",
        "atom_0220",
        "pin",
        "Proposed visual pin: Cosmic Sun viewer-right pupil/detail to upper Salmon eye detail.",
    ),
    (
        "atom_0012",
        "atom_0240",
        "pin",
        "Proposed visual pin: Cosmic Sun central disc to Salmon central eye/pivot assembly.",
    ),
    (
        "atom_0015",
        "atom_0243",
        "pin",
        "Proposed visual pin: Cosmic Sun lower-face formline to inner central eye boundary.",
    ),
    (
        "atom_0019",
        "atom_0244",
        "pin",
        "Proposed visual pin: Cosmic Sun mouth oval to central inner ovoid/pupil.",
    ),
]


@dataclass(frozen=True)
class Atom:
    atom_id: str
    piece: str
    label: str
    element_type: str
    fill_color: str
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    cx: float
    cy: float
    area: float
    png: Path
    order: int


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
class Correspondence:
    source: Atom | None
    target: Atom | None
    constraint: str
    notes: str
    cost: float | None = None


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
    constraint: str
    launch_frame: float
    flight_frames: float
    curve_offset: float
    curl_phase: float
    spin: float


def read_atoms(piece_dir: Path) -> list[Atom]:
    atoms: list[Atom] = []
    with (piece_dir / "atom_metadata.csv").open(newline="") as f:
        for order, row in enumerate(csv.DictReader(f)):
            try:
                atoms.append(
                    Atom(
                        atom_id=row["atom_id"],
                        piece=row["piece"],
                        label=row["ai_label"],
                        element_type=row["element_type"],
                        fill_color=row["fill_color"],
                        bbox_x=float(row["bbox_x"]),
                        bbox_y=float(row["bbox_y"]),
                        bbox_w=float(row["bbox_w"]),
                        bbox_h=float(row["bbox_h"]),
                        cx=float(row["centroid_x"]),
                        cy=float(row["centroid_y"]),
                        area=float(row["area"]),
                        png=piece_dir / row["isolated_png"],
                        order=order,
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


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def atom_norm(atom: Atom, viewbox: float) -> tuple[float, float]:
    return (atom.cx / viewbox, atom.cy / viewbox)


def atom_center_px(atom: Atom, viewbox: float) -> tuple[float, float]:
    return (atom.cx / viewbox * CANVAS, atom.cy / viewbox * CANVAS)


def hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    value = (value or "").strip()
    if value.startswith("#") and len(value) == 7:
        try:
            return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))
        except ValueError:
            return fallback
    return fallback


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum(abs(a[i] - b[i]) for i in range(3)) / (255.0 * 3.0)


def label_cost(src_label: str, dest_label: str) -> float:
    if src_label == dest_label:
        return 0.0
    eyeish = {"eye-focal-oval", "circle-oval"}
    if src_label in eyeish and dest_label in eyeish:
        return 0.10
    if src_label == "crescent" and dest_label in {"crescent", "formline-secondary", "formline-tertiary"}:
        return 0.22
    if src_label == "trigon" and dest_label in {"trigon", "body-element", "formline-secondary", "fin-tail"}:
        return 0.24
    if src_label == "formline-primary" and dest_label in {"formline-primary", "body-element", "eye-focal-oval"}:
        return 0.25
    if dest_label in {"formline-primary", "body-element", "fin-tail"}:
        return 0.55
    return 0.75


def weighted_assignment_cost(src: Atom, dest: Atom) -> float:
    sx, sy = atom_norm(src, COSMIC_VIEWBOX)
    dx, dy = atom_norm(dest, SALMON_VIEWBOX)
    centroid = math.hypot(sx - dx, sy - dy)
    src_area = max(1e-6, src.area / (COSMIC_VIEWBOX * COSMIC_VIEWBOX))
    dest_area = max(1e-6, dest.area / (SALMON_VIEWBOX * SALMON_VIEWBOX))
    size = abs(math.log(src_area / dest_area))
    src_color = hex_to_rgb(src.fill_color, (220, 160, 70))
    dest_color = hex_to_rgb(dest.fill_color, (150, 110, 105))
    color = color_distance(src_color, dest_color)
    z_layer = abs(src.order / 40.0 - dest.order / 244.0)
    return (
        label_cost(src.label, dest.label) * 2.0
        + centroid * 1.4
        + size * 0.28
        + color * 0.35
        + z_layer * 0.20
    )


def is_ray_emitter(atom: Atom) -> bool:
    return atom.label == "sun-ray" or atom.atom_id in EXTERNAL_TRIGONS


def fallback_mask(atom: Atom, viewbox: float) -> Image.Image:
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
        draw.rounded_rectangle([x, y, x + w, y + h], radius=max(2, int(min(w, h) * 0.18)), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=0.35))


def full_canvas_mask(atom: Atom, viewbox: float) -> Image.Image:
    iso = Image.open(atom.png).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    mask = iso.point(lambda v: max(0, min(255, (255 - v) * 2)))
    if mask.getbbox() is None:
        return fallback_mask(atom, viewbox)
    return mask.filter(ImageFilter.GaussianBlur(radius=0.25))


def sampled_color(img: Image.Image, x: float, y: float, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    xi = int(round(x))
    yi = int(round(y))
    if xi < 0 or yi < 0 or xi >= img.width or yi >= img.height:
        return fallback
    patch = img.crop((max(0, xi - 2), max(0, yi - 2), min(img.width, xi + 3), min(img.height, yi + 3)))
    arr = np.asarray(patch.convert("RGB")).reshape(-1, 3)
    return tuple(int(v) for v in arr.mean(axis=0))


def target_from_mask(atom: Atom, mask: Image.Image, img: Image.Image, viewbox: float, fallback: tuple[int, int, int]) -> TargetAtom:
    bbox = mask.getbbox()
    if bbox is None:
        mask = fallback_mask(atom, viewbox)
        bbox = mask.getbbox()
    assert bbox is not None
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - 3)
    y0 = max(0, y0 - 3)
    x1 = min(CANVAS, x1 + 3)
    y1 = min(CANVAS, y1 + 3)
    sprite = img.crop((x0, y0, x1, y1)).convert("RGBA")
    sprite.putalpha(mask.crop((x0, y0, x1, y1)))
    center = atom_center_px(atom, viewbox)
    radius = max(2.5, min(80.0, atom.bbox_w / 2.0 / viewbox * CANVAS))
    color = sampled_color(img, center[0], center[1], fallback)
    return TargetAtom(atom, mask, sprite, (x0, y0), center, radius, color)


def source_from_atom(atom: Atom, img: Image.Image, rng: np.random.Generator, launch: float) -> SourceAtom:
    mask = full_canvas_mask(atom, COSMIC_VIEWBOX)
    target_like = target_from_mask(atom, mask, img, COSMIC_VIEWBOX, (220, 140, 50))
    return SourceAtom(atom, mask, target_like.sprite, target_like.top_left, target_like.center, target_like.color, rng.random((CANVAS, CANVAS)), launch)


def dedupe_targets(targets: list[Atom], pinned_ids: set[str]) -> list[Atom]:
    seen: set[tuple[str, int, int, int, int]] = set()
    out: list[Atom] = []
    for atom in targets:
        key = (atom.label, round(atom.bbox_x), round(atom.bbox_y), round(atom.bbox_w), round(atom.bbox_h))
        if atom.atom_id not in pinned_ids and key in seen:
            continue
        seen.add(key)
        out.append(atom)
    return out


def build_correspondences(cosmic_atoms: list[Atom], salmon_atoms: list[Atom]) -> list[Correspondence]:
    cosmic_by_id = {a.atom_id: a for a in cosmic_atoms}
    salmon_by_id = {a.atom_id: a for a in salmon_atoms}

    rows: list[Correspondence] = []
    pinned_src: set[str] = set()
    pinned_tgt: set[str] = set()
    for src_id, dst_id, constraint, notes in PIN_SPECS:
        rows.append(Correspondence(cosmic_by_id[src_id], salmon_by_id[dst_id], constraint, notes, 0.0))
        pinned_src.add(src_id)
        pinned_tgt.add(dst_id)

    for atom in cosmic_atoms:
        if atom.label in EXCLUDED_LABELS:
            rows.append(Correspondence(atom, None, "exclude", "Excluded from motion by default: source background/non-form atom."))
    for atom in salmon_atoms:
        if atom.label in EXCLUDED_LABELS:
            rows.append(Correspondence(None, atom, "exclude", "Excluded from motion by default: destination background/non-form atom."))

    roe_targets = [a for a in salmon_atoms if a.label == "egg-roe"]
    roe_targets.sort(key=lambda a: math.atan2(a.cy / SALMON_VIEWBOX - 0.5, a.cx / SALMON_VIEWBOX - 0.5))
    ray_sources = [a for a in cosmic_atoms if a.atom_id not in pinned_src and is_ray_emitter(a)]
    ray_sources.sort(key=lambda a: math.atan2(a.cy / COSMIC_VIEWBOX - 0.5, a.cx / COSMIC_VIEWBOX - 0.5))
    for idx, atom in enumerate(ray_sources):
        if not roe_targets:
            continue
        target = roe_targets[int(idx * len(roe_targets) / max(1, len(ray_sources)))]
        rows.append(
            Correspondence(
                atom,
                target,
                "auto_particle_field",
                "Representative route only: this source ray/trigon fans out into many Salmon roe atoms.",
                None,
            )
        )

    face_sources = [
        a for a in cosmic_atoms
        if a.atom_id not in pinned_src and a.label not in EXCLUDED_LABELS and not is_ray_emitter(a)
    ]
    structural_targets = [
        a for a in salmon_atoms
        if a.atom_id not in pinned_tgt and a.label in STRUCTURAL_LABELS and a.label not in EXCLUDED_LABELS
    ]
    structural_targets = dedupe_targets(structural_targets, pinned_tgt)
    if face_sources and structural_targets:
        cost = np.zeros((len(face_sources), len(structural_targets)), dtype=np.float32)
        for i, src in enumerate(face_sources):
            for j, dst in enumerate(structural_targets):
                cost[i, j] = weighted_assignment_cost(src, dst)
        src_idx, dst_idx = linear_sum_assignment(cost)
        for i, j in zip(src_idx, dst_idx):
            rows.append(
                Correspondence(
                    face_sources[i],
                    structural_targets[j],
                    "auto",
                    "Automatic visual assignment: label/type, centroid, size, color, and z-layer cost.",
                    float(cost[i, j]),
                )
            )

    def sort_key(row: Correspondence) -> tuple[int, str, str]:
        order = {"pin": 0, "auto": 1, "auto_particle_field": 2, "exclude": 3}.get(row.constraint, 9)
        return (order, row.source.atom_id if row.source else "", row.target.atom_id if row.target else "")

    return sorted(rows, key=sort_key)


def write_correspondence_csv(rows: list[Correspondence]) -> None:
    with CORRESPONDENCES.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_piece",
                "source_atom_id",
                "source_label",
                "dest_piece",
                "dest_atom_id",
                "dest_label",
                "constraint",
                "notes",
                "cost",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_piece": row.source.piece if row.source else "",
                    "source_atom_id": row.source.atom_id if row.source else "",
                    "source_label": row.source.label if row.source else "",
                    "dest_piece": row.target.piece if row.target else "",
                    "dest_atom_id": row.target.atom_id if row.target else "",
                    "dest_label": row.target.label if row.target else "",
                    "constraint": row.constraint,
                    "notes": row.notes,
                    "cost": "" if row.cost is None else f"{row.cost:.4f}",
                }
            )


def diagnostic_point(atom: Atom, viewbox: float, panel_x: int, panel_y: int, panel_size: int) -> tuple[float, float]:
    return (panel_x + atom.cx / viewbox * panel_size, panel_y + atom.cy / viewbox * panel_size)


def render_diagnostic(rows: list[Correspondence], source_img: Image.Image, dest_img: Image.Image) -> None:
    panel = 560
    pad = 48
    top = 92
    width = pad * 3 + panel * 2
    height = top + panel + 120
    img = Image.new("RGB", (width, height), (250, 248, 245))
    source_small = source_img.resize((panel, panel), Image.Resampling.LANCZOS)
    dest_small = dest_img.resize((panel, panel), Image.Resampling.LANCZOS)
    src_x = pad
    dst_x = pad * 2 + panel
    img.paste(source_small, (src_x, top))
    img.paste(dest_small, (dst_x, top))

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    font = ImageFont.load_default()
    version_label = PAIR_ID.replace("cosmic_sun_to_salmon_spawn_landmark_atom_routing_", "")
    title = f"{version_label} diagnostic: proposed visual atom correspondences (internal only)"
    draw.text((pad, 24), title, fill=(60, 45, 45, 255), font=font)
    draw.text((src_x, 70), "Nature_Cosmic_Sun", fill=(60, 45, 45, 255), font=font)
    draw.text((dst_x, 70), "Animal_Salmon_Spawn_Eggs", fill=(60, 45, 45, 255), font=font)

    colors = {
        "pin": (20, 170, 95, 230),
        "auto": (90, 120, 150, 105),
        "auto_particle_field": (245, 120, 30, 90),
    }
    widths = {"pin": 4, "auto": 1, "auto_particle_field": 1}
    for row in rows:
        if row.source is None or row.target is None or row.constraint == "exclude":
            continue
        if row.constraint == "auto" and row.cost is not None and row.cost > 2.8:
            alpha_color = (120, 120, 120, 55)
        else:
            alpha_color = colors.get(row.constraint, (100, 100, 100, 90))
        p0 = diagnostic_point(row.source, COSMIC_VIEWBOX, src_x, top, panel)
        p1 = diagnostic_point(row.target, SALMON_VIEWBOX, dst_x, top, panel)
        draw.line([p0, p1], fill=alpha_color, width=widths.get(row.constraint, 1))
        r = 6 if row.constraint == "pin" else 3
        draw.ellipse([p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r], fill=alpha_color)
        draw.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=alpha_color)
        if row.constraint == "pin":
            draw.text((p0[0] + 7, p0[1] - 10), row.source.atom_id, fill=(0, 95, 55, 255), font=font)
            draw.text((p1[0] + 7, p1[1] - 10), row.target.atom_id, fill=(0, 95, 55, 255), font=font)

    legend_y = top + panel + 26
    legend = [
        ((20, 170, 95, 255), "green = hard pin"),
        ((90, 120, 150, 180), "blue-gray = automatic structural assignment"),
        ((245, 120, 30, 180), "orange = representative ray/trigon to roe-field routing"),
    ]
    x = pad
    for color, text in legend:
        draw.line([(x, legend_y + 8), (x + 36, legend_y + 8)], fill=color, width=4)
        draw.text((x + 46, legend_y), text, fill=(70, 55, 55, 255), font=font)
        x += 330
    draw.text(
        (pad, legend_y + 36),
        "Language note: these are proposed visual correspondences, not confirmed symbolic meanings.",
        fill=(120, 70, 70, 255),
        font=font,
    )

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    img.save(DIAGNOSTIC)


def composite_at(base: Image.Image, overlay: Image.Image, x: int, y: int) -> None:
    left = max(0, x)
    top = max(0, y)
    right = min(base.width, x + overlay.width)
    bottom = min(base.height, y + overlay.height)
    if right <= left or bottom <= top:
        return
    crop = overlay.crop((left - x, top - y, right - x, bottom - y))
    base.alpha_composite(crop, (left, top))


def erase_source(layer: Image.Image, fill_bg: Image.Image, source: SourceAtom, frame: int, duration: float) -> None:
    progress = ease((frame - source.launch_start) / duration)
    if progress <= 0:
        return
    mask_arr = np.asarray(source.mask, dtype=np.float32) / 255.0
    threshold = np.clip(progress * 1.14 - source.noise, 0.0, 1.0)
    alpha_arr = (mask_arr * threshold * 255).astype(np.uint8)
    alpha = Image.fromarray(alpha_arr, "L").filter(ImageFilter.GaussianBlur(radius=0.45))
    patch = fill_bg.copy().convert("RGBA")
    patch.putalpha(alpha)
    layer.alpha_composite(patch)


def source_layer_for_frame(source_img: Image.Image, fill_bg: Image.Image, sources: list[SourceAtom], frame: int) -> Image.Image:
    layer = source_img.copy().convert("RGBA")
    for source in sources:
        duration = 22 if is_ray_emitter(source.atom) else 36
        erase_source(layer, fill_bg, source, frame, duration)
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
    curl = math.sin(math.pi * t) * 0.016
    return (bx + math.sin(7.0 * t + phase) * curl, by + math.cos(8.0 * t + phase) * curl)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (int(lerp(a[0], b[0], t)), int(lerp(a[1], b[1], t)), int(lerp(a[2], b[2], t)))


def transformed_sprite_between(src: SourceAtom, target: TargetAtom, t: float, alpha: int) -> Image.Image:
    source_sprite = src.sprite
    target_sprite = target.sprite
    scale_x = target_sprite.width / max(1, source_sprite.width)
    scale_y = target_sprite.height / max(1, source_sprite.height)
    scale = lerp(1.0, min(2.25, max(0.20, (scale_x + scale_y) / 2.0)), ease(t))
    src_resized = source_sprite.resize(
        (max(1, int(source_sprite.width * scale)), max(1, int(source_sprite.height * scale))),
        Image.Resampling.LANCZOS,
    )
    if abs((1.0 - t) * 8.0) > 0.05:
        src_resized = src_resized.rotate((1.0 - t) * 8.0, resample=Image.Resampling.BICUBIC, expand=True)
    morph_t = ease((t - 0.58) / 0.32)
    if morph_t > 0:
        dst_resized = target_sprite.resize(src_resized.size, Image.Resampling.LANCZOS)
        src_resized = Image.blend(src_resized, dst_resized, morph_t)
    src_resized.putalpha(src_resized.getchannel("A").point(lambda a: int(a * alpha / 255)))
    return src_resized


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
    theta = math.atan2(p.end[1] - p.start[1], p.end[0] - p.start[0]) + p.spin * (1.0 - t)
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


def draw_destination_scaffold(
    layer: Image.Image,
    targets: list[TargetAtom],
    moved_target_ids: set[str],
    frame: int,
    start: float,
    span: float,
    duration: float,
) -> None:
    ordered = sorted(
        targets,
        key=lambda t: (
            t.atom.label != "eye-focal-oval",
            math.atan2(t.center[1] / CANVAS - 0.5, t.center[0] / CANVAS - 0.5),
            t.atom.area,
        ),
    )
    for idx, target in enumerate(ordered):
        local_start = start + idx / max(1, len(ordered) - 1) * span
        alpha = ease((frame - local_start) / duration)
        if target.atom.atom_id in moved_target_ids:
            alpha *= 0.32
        draw_landed(layer, target, alpha)


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
    alpha = int(235 * (1.0 - max(0.0, local - 0.98) / 0.02))
    sprite = transformed_sprite_between(mover.src, mover.target, t, alpha)
    x = int(round(x_norm * CANVAS - sprite.width / 2))
    y = int(round(y_norm * CANVAS - sprite.height / 2))
    composite_at(layer, sprite, x, y)


def make_sources(cosmic_atoms: list[Atom], source_img: Image.Image, rows: list[Correspondence], rng: np.random.Generator) -> dict[str, SourceAtom]:
    source_ids = {row.source.atom_id for row in rows if row.source is not None and row.constraint != "exclude"}
    ray_ids = {atom.atom_id for atom in cosmic_atoms if atom.atom_id in source_ids and is_ray_emitter(atom)}
    sources: dict[str, SourceAtom] = {}
    for idx, atom in enumerate([a for a in cosmic_atoms if a.atom_id in source_ids]):
        if atom.atom_id in ray_ids:
            launch = 8 + idx * 0.8 + rng.uniform(-0.8, 0.8)
        elif atom.atom_id in {spec[0] for spec in PIN_SPECS}:
            launch = 28 + idx * 0.9 + rng.uniform(-1.2, 1.2)
        else:
            launch = 42 + idx * 1.3 + rng.uniform(-1.8, 1.8)
        sources[atom.atom_id] = source_from_atom(atom, source_img, rng, launch)
    return sources


def make_targets(salmon_atoms: list[Atom], dest_img: Image.Image) -> tuple[dict[str, TargetAtom], list[TargetAtom], list[TargetAtom]]:
    all_targets: dict[str, TargetAtom] = {}
    roe: list[TargetAtom] = []
    structure: list[TargetAtom] = []
    pinned_ids = {spec[1] for spec in PIN_SPECS}
    structural_atoms = dedupe_targets(
        [a for a in salmon_atoms if a.label in STRUCTURAL_LABELS and a.label not in EXCLUDED_LABELS],
        pinned_ids,
    )
    for atom in salmon_atoms:
        if atom.label == "egg-roe":
            target = target_from_mask(atom, full_canvas_mask(atom, SALMON_VIEWBOX), dest_img, SALMON_VIEWBOX, (255, 94, 59))
            all_targets[atom.atom_id] = target
            roe.append(target)
    for atom in structural_atoms:
        target = target_from_mask(atom, full_canvas_mask(atom, SALMON_VIEWBOX), dest_img, SALMON_VIEWBOX, (135, 100, 96))
        all_targets[atom.atom_id] = target
        structure.append(target)
    return all_targets, roe, structure


def sample_points(source: SourceAtom, count: int, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(source.mask)
    ys, xs = np.where(arr > 50)
    if len(xs) == 0:
        return np.repeat([[source.center[0], source.center[1]]], count, axis=0)
    picks = rng.integers(0, len(xs), size=count)
    jitter = rng.uniform(-0.5, 0.5, size=(count, 2))
    return np.column_stack([xs[picks], ys[picks]]).astype(float) + jitter


def build_roe_particles(sources: dict[str, SourceAtom], roe_targets: list[TargetAtom], rows: list[Correspondence], rng: np.random.Generator) -> list[RoeParticle]:
    ray_sources = [sources[row.source.atom_id] for row in rows if row.constraint == "auto_particle_field" and row.source and row.source.atom_id in sources]
    ray_sources.sort(key=lambda s: math.atan2(s.center[1] / CANVAS - 0.5, s.center[0] / CANVAS - 0.5))
    roe_sorted = sorted(
        roe_targets,
        key=lambda r: (
            math.atan2(r.center[1] / CANVAS - 0.5, r.center[0] / CANVAS - 0.5),
            math.hypot(r.center[0] / CANVAS - 0.5, r.center[1] / CANVAS - 0.5),
        ),
    )
    particles: list[RoeParticle] = []
    points_by_source: dict[str, np.ndarray] = {}
    for idx, target in enumerate(roe_sorted):
        if not ray_sources:
            break
        src = ray_sources[int(idx * len(ray_sources) / max(1, len(roe_sorted)))]
        if src.atom.atom_id not in points_by_source:
            local_count = max(8, len(roe_sorted) // max(1, len(ray_sources)) + 8)
            points_by_source[src.atom.atom_id] = sample_points(src, local_count, rng)
        local_idx = sum(1 for p in particles if p.src.atom.atom_id == src.atom.atom_id)
        sx, sy = points_by_source[src.atom.atom_id][local_idx % len(points_by_source[src.atom.atom_id])]
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


def build_structure_movers(sources: dict[str, SourceAtom], targets: dict[str, TargetAtom], rows: list[Correspondence], rng: np.random.Generator) -> list[StructureMover]:
    movers: list[StructureMover] = []
    for row in rows:
        if row.constraint not in {"pin", "auto"} or row.source is None or row.target is None:
            continue
        if row.source.atom_id not in sources or row.target.atom_id not in targets:
            continue
        src = sources[row.source.atom_id]
        target = targets[row.target.atom_id]
        if row.constraint == "pin":
            launch = src.launch_start + rng.uniform(-1.0, 1.0)
            flight = rng.uniform(46, 58)
            curve = rng.uniform(-0.10, 0.10)
        else:
            launch = src.launch_start + rng.uniform(-2.0, 2.0)
            flight = rng.uniform(42, 58)
            curve = rng.uniform(-0.16, 0.16)
        movers.append(
            StructureMover(
                src=src,
                target=target,
                constraint=row.constraint,
                launch_frame=launch,
                flight_frames=flight,
                curve_offset=curve,
                curl_phase=rng.uniform(0, math.tau),
                spin=rng.uniform(-0.35, 0.35),
            )
        )
    return movers


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


def render_video(
    rows: list[Correspondence],
    source_img: Image.Image,
    dest_img: Image.Image,
    cosmic_atoms: list[Atom],
    salmon_atoms: list[Atom],
    continuity_settle: bool = False,
) -> None:
    if OUT_MP4.exists() or any(OUT_DIR.glob("frame_*.png")):
        raise SystemExit(f"Refusing to overwrite existing frames or MP4 in {OUT_DIR}")
    rng = np.random.default_rng(2026051707)
    fill_bg = Image.blend(
        source_img.filter(ImageFilter.GaussianBlur(radius=28)),
        Image.new("RGB", (CANVAS, CANVAS), (248, 243, 240)),
        0.82 if continuity_settle else 0.48,
    )
    sources = make_sources(cosmic_atoms, source_img, rows, rng)
    targets, roe_targets, structure_targets = make_targets(salmon_atoms, dest_img)
    roe_particles = build_roe_particles(sources, roe_targets, rows, rng)
    structure_movers = build_structure_movers(sources, targets, rows, rng)
    all_sources = list(sources.values())
    moved_target_ids = {mover.target.atom.atom_id for mover in structure_movers}

    print(f"correspondences: {len(rows)}")
    print(f"source atoms in motion: {len(all_sources)}")
    print(f"pinned structure movers: {sum(1 for m in structure_movers if m.constraint == 'pin')}")
    print(f"auto structure movers: {sum(1 for m in structure_movers if m.constraint == 'auto')}")
    print(f"roe targets/particles: {len(roe_targets)} / {len(roe_particles)}")
    print(f"structural targets available: {len(structure_targets)}")

    for frame in range(N_FRAMES):
        if frame == 0:
            canvas = source_img.copy().convert("RGBA")
        else:
            canvas = source_layer_for_frame(source_img, fill_bg, all_sources, frame)
            if continuity_settle:
                clear_alpha = ease((frame - 58) / 42.0) * 0.78
                if clear_alpha > 0:
                    neutral = Image.new("RGBA", (CANVAS, CANVAS), (248, 243, 240, 255))
                    canvas = Image.blend(canvas, neutral, clear_alpha)

            atom_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            atom_draw = ImageDraw.Draw(atom_layer)
            for particle in roe_particles:
                draw_roe_particle(atom_draw, particle, frame)
                draw_landed(atom_layer, particle.target, ease((frame - (particle.launch_frame + particle.flight_frames)) / 8.0))
            if continuity_settle:
                draw_destination_scaffold(
                    atom_layer,
                    structure_targets,
                    moved_target_ids,
                    frame,
                    start=78,
                    span=18,
                    duration=24,
                )
            for mover in structure_movers:
                draw_structure_mover(atom_layer, mover, frame)
            canvas.alpha_composite(atom_layer)

            if continuity_settle:
                final_alpha = ease((frame - 108) / 10.0)
            else:
                final_alpha = ease((frame - 116) / 3.0)
            if frame >= 118:
                final_alpha = 1.0
            if final_alpha > 0:
                final = dest_img.copy().convert("RGBA")
                final.putalpha(final.getchannel("A").point(lambda a: int(a * final_alpha)))
                canvas.alpha_composite(final)

        canvas.convert("RGB").save(OUT_DIR / f"frame_{frame:04d}.png", quality=95)
        if (frame + 1) % 20 == 0:
            print(f"frame {frame + 1}/{N_FRAMES}")
    compile_mp4()
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_morph_landmark_atom_routing_v007.py")


def validate_eye_pins(rows: list[Correspondence]) -> None:
    required = {
        ("atom_0022", "atom_0191"),
        ("atom_0023", "atom_0190"),
        ("atom_0016", "atom_0221"),
        ("atom_0017", "atom_0220"),
    }
    actual = {
        (row.source.atom_id, row.target.atom_id)
        for row in rows
        if row.constraint == "pin" and row.source is not None and row.target is not None
    }
    missing = required - actual
    if missing:
        raise SystemExit(f"Eye pin validation failed, missing: {sorted(missing)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair-id", default=DEFAULT_PAIR_ID)
    ap.add_argument("--diagnostic-only", action="store_true")
    ap.add_argument("--render-video", action="store_true")
    ap.add_argument("--continuity-settle", action="store_true")
    args = ap.parse_args()
    set_pair_id(args.pair_id)
    if not args.diagnostic_only and not args.render_video:
        raise SystemExit("Pass --diagnostic-only first, then --render-video after inspecting the diagnostic.")
    if OUT_MP4.exists():
        raise SystemExit(f"Refusing to overwrite existing MP4: {OUT_MP4}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    source_img = load_training_jpg("Nature_Cosmic_Sun.jpg")
    dest_img = load_training_jpg("Animal_Salmon_Spawn_Eggs.jpg")
    cosmic_atoms = read_atoms(DECOMPOSED / "Nature_Cosmic_Sun")
    salmon_atoms = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    rows = build_correspondences(cosmic_atoms, salmon_atoms)
    validate_eye_pins(rows)
    write_correspondence_csv(rows)
    render_diagnostic(rows, source_img, dest_img)
    print(f"wrote {CORRESPONDENCES}")
    print(f"wrote {DIAGNOSTIC}")
    print("eye pins validated by atom id; inspect diagnostic before video render")
    if args.render_video:
        render_video(rows, source_img, dest_img, cosmic_atoms, salmon_atoms, continuity_settle=args.continuity_settle)
        print(f"wrote {OUT_MP4}")
        print(f"frames preserved in {OUT_DIR}")


if __name__ == "__main__":
    main()
