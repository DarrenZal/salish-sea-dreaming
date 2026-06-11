#!/usr/bin/env python3
"""
Hybrid raw-motion endpoint correction.

Keeps the operator-preferred endpoint_emerge/raw morph middle, then resolves
the ending against the verified Salmon Spawn Eggs training JPG through atom
masks. This targets the straight-line endpoint artifacts without replacing the
whole transition with the v005 duplicated-face style.
"""
from __future__ import annotations

import csv
import math
import shutil
import subprocess
import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from scipy.ndimage import distance_transform_edt


ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

PAIR_ID_PREFIX = "cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct"

CANVAS = 1024
FPS = 24
SALMON_VIEWBOX = 1500.0
INPUT_FRAMES = INTERNAL / "cosmic_sun_to_salmon_spawn_endpoint_emerge_v001"

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


@dataclass(frozen=True)
class ScheduledMask:
    label: str
    start: float
    duration: float
    mask: np.ndarray


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


def fallback_mask(atom: Atom) -> Image.Image:
    scale = CANVAS / SALMON_VIEWBOX
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
    return mask.filter(ImageFilter.GaussianBlur(radius=0.4))


def atom_mask(atom: Atom) -> Image.Image:
    iso = Image.open(atom.png).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
    mask = iso.point(lambda v: max(0, min(255, (255 - v) * 2)))
    if mask.getbbox() is None:
        mask = fallback_mask(atom)
    return mask.filter(ImageFilter.GaussianBlur(radius=0.6))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def build_scheduled_masks(
    struct_start: float,
    struct_span: float,
    struct_duration: float,
    roe_start: float,
    roe_span: float,
    roe_duration: float,
    union_maxfilter: int,
    union_blur: float,
) -> tuple[list[ScheduledMask], np.ndarray]:
    atoms = read_atoms(DECOMPOSED / "Animal_Salmon_Spawn_Eggs")
    targets: list[Atom] = []
    seen_struct: set[tuple[str, int, int, int, int]] = set()
    for atom in atoms:
        if atom.label == "egg-roe":
            targets.append(atom)
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
            targets.append(atom)

    roe = [a for a in targets if a.label == "egg-roe"]
    struct = [a for a in targets if a.label != "egg-roe"]
    roe.sort(key=lambda a: (math.atan2(a.cy / SALMON_VIEWBOX - 0.5, a.cx / SALMON_VIEWBOX - 0.5), a.area))
    struct.sort(key=lambda a: (a.area < 1000, math.atan2(a.cy / SALMON_VIEWBOX - 0.5, a.cx / SALMON_VIEWBOX - 0.5)))

    scheduled: list[ScheduledMask] = []
    content_union = np.zeros((CANVAS, CANVAS), dtype=np.float32)

    def add(atom: Atom, start: float, duration: float) -> None:
        nonlocal content_union
        arr = np.asarray(atom_mask(atom), dtype=np.float32) / 255.0
        content_union = np.maximum(content_union, arr)
        scheduled.append(ScheduledMask(atom.label, start, duration, arr))

    for idx, atom in enumerate(struct):
        add(atom, struct_start + idx / max(1, len(struct) - 1) * struct_span, struct_duration)
    for idx, atom in enumerate(roe):
        add(atom, roe_start + idx / max(1, len(roe) - 1) * roe_span, roe_duration)

    content_img = Image.fromarray(np.clip(content_union * 255, 0, 255).astype(np.uint8))
    if union_maxfilter > 1:
        if union_maxfilter % 2 == 0:
            union_maxfilter += 1
        content_img = content_img.filter(ImageFilter.MaxFilter(union_maxfilter))
    if union_blur > 0:
        content_img = content_img.filter(ImageFilter.GaussianBlur(radius=union_blur))
    content_union = np.asarray(content_img, dtype=np.float32) / 255.0
    return scheduled, content_union


def assembly_mask_for_frame(scheduled: list[ScheduledMask], frame: int) -> np.ndarray:
    out = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for item in scheduled:
        amount = ease((frame - item.start) / item.duration)
        if amount <= 0:
            continue
        out = np.maximum(out, item.mask * amount)
    return np.clip(out, 0.0, 1.0)


def blend_arrays(a: np.ndarray, b: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    if np.isscalar(alpha):
        return a * (1.0 - float(alpha)) + b * float(alpha)
    if alpha.ndim == 2:
        alpha = alpha[..., None]
    return a * (1.0 - alpha) + b * alpha


def white_seed_distance(source_img: Image.Image) -> np.ndarray:
    """Distance-to-white-source-regions field.

    The seed is intentionally source-derived: high-luma, low-saturation areas
    in the Cosmic Sun face/cheeks. Later variants use this to grow the Salmon
    background from existing white form, not from an arbitrary square.
    """
    arr = np.asarray(source_img.convert("RGB"), dtype=np.float32)
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    seed = (lum > 235) & (sat < 45)
    seed_img = Image.fromarray((seed * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(9))
    seed = np.asarray(seed_img, dtype=np.uint8) > 0
    return distance_transform_edt(~seed).astype(np.float32)


def white_seed_reveal(distance_field: np.ndarray, frame: int, start: float, duration: float, max_radius: float, feather: float) -> np.ndarray:
    growth = ease((frame - start) / duration)
    if growth <= 0:
        return np.zeros_like(distance_field, dtype=np.float32)
    radius = max_radius * growth
    return np.clip((radius + feather - distance_field) / max(1.0, feather), 0.0, 1.0)


def raw_foreground_alpha(
    img: Image.Image,
    blur_radius: float,
    diff_threshold: float,
    sat_threshold: float,
    luma_threshold: float,
    maxfilter: int,
    alpha_blur: float,
) -> np.ndarray:
    """Estimate moving primitive foreground, leaving flat background fields out.

    This is an image-level control for the endpoint_emerge frames. It keeps
    high-frequency or strongly colored forms while letting flat interpolated
    background polygons fall back to a neutral underlay.
    """
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(radius=blur_radius)), dtype=np.float32)
    diff = np.abs(arr - blurred).max(axis=2)
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    fg = ((diff > diff_threshold) | (sat > sat_threshold) | (lum > luma_threshold)).astype(np.uint8) * 255
    mask = Image.fromarray(fg, "L")
    if maxfilter > 1:
        if maxfilter % 2 == 0:
            maxfilter += 1
        mask = mask.filter(ImageFilter.MaxFilter(maxfilter))
    if alpha_blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=alpha_blur))
    return np.asarray(mask, dtype=np.float32) / 255.0


def load_morph_engine():
    engine_path = ROOT / "track2-deterministic/scripts/morph_engine.py"
    spec = importlib.util.spec_from_file_location("ssd_morph_engine", engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load morph engine at {engine_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_raw_tweens_without_dest_rect(resample_n: int):
    """Rebuild raw morph frames with the destination background rect removed."""
    me = load_morph_engine()
    source_svg = ROOT / "track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg"
    target_svg = ROOT / "track2-deterministic/source-vectors/Animal_Salmon_Spawn_Eggs.svg"
    src_shapes, src_meta = me.load_svg_shapes(source_svg, resample_n)
    tgt_shapes, tgt_meta = me.load_svg_shapes(target_svg, resample_n)
    filtered_tgt = [
        shape for shape in tgt_shapes
        if not (shape.kind == "rect" and shape.bucket == "rect" and shape.area > 0.75)
    ]
    tweens, tween_meta = me.build_shape_tweens(src_shapes, filtered_tgt, resample_n)
    meta = {
        "src": src_meta,
        "tgt": tgt_meta,
        "filtered_target_shapes": len(tgt_shapes) - len(filtered_tgt),
        "tweens": tween_meta,
    }
    return me, tweens, meta


def compile_mp4(out_dir: Path, out_mp4: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(out_dir / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(out_mp4),
        ],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version-tag", default="v002_delayed_settle")
    ap.add_argument("--raw-until", type=int, default=98)
    ap.add_argument("--struct-start", type=float, default=98)
    ap.add_argument("--struct-span", type=float, default=14)
    ap.add_argument("--struct-duration", type=float, default=13)
    ap.add_argument("--roe-start", type=float, default=101)
    ap.add_argument("--roe-span", type=float, default=15)
    ap.add_argument("--roe-duration", type=float, default=10)
    ap.add_argument("--bg-start", type=float, default=106)
    ap.add_argument("--bg-duration", type=float, default=13)
    ap.add_argument("--bg-strength", type=float, default=0.70)
    ap.add_argument("--final-start", type=float, default=118)
    ap.add_argument("--final-duration", type=float, default=1)
    ap.add_argument("--union-maxfilter", type=int, default=7)
    ap.add_argument("--union-blur", type=float, default=3)
    ap.add_argument("--white-bg-from-source", action="store_true")
    ap.add_argument("--white-bg-start", type=float, default=10)
    ap.add_argument("--white-bg-duration", type=float, default=82)
    ap.add_argument("--white-bg-radius", type=float, default=920)
    ap.add_argument("--white-bg-feather", type=float, default=95)
    ap.add_argument("--white-bg-strength", type=float, default=0.88)
    ap.add_argument("--early-white-underlay", action="store_true")
    ap.add_argument("--underlay-start", type=float, default=30)
    ap.add_argument("--underlay-duration", type=float, default=18)
    ap.add_argument("--underlay-strength", type=float, default=0.95)
    ap.add_argument("--underlay-rgb", default="242,238,237")
    ap.add_argument("--underlay-blur", type=float, default=28)
    ap.add_argument("--underlay-diff-threshold", type=float, default=22)
    ap.add_argument("--underlay-sat-threshold", type=float, default=78)
    ap.add_argument("--underlay-luma-threshold", type=float, default=188)
    ap.add_argument("--underlay-maxfilter", type=int, default=15)
    ap.add_argument("--underlay-alpha-blur", type=float, default=2.0)
    ap.add_argument("--rebuild-raw-no-dest-rect", action="store_true")
    ap.add_argument("--rebuild-resample-n", type=int, default=96)
    args = ap.parse_args()

    pair_id = f"{PAIR_ID_PREFIX}_{args.version_tag}"
    out_dir = INTERNAL / pair_id
    out_mp4 = INTERNAL / f"{pair_id}.mp4"
    if out_dir.exists() or out_mp4.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {out_dir} / {out_mp4}")
    frames = sorted(INPUT_FRAMES.glob("frame_*.png"))
    if len(frames) != 120:
        raise SystemExit(f"Expected 120 input frames in {INPUT_FRAMES}, found {len(frames)}")

    source_img = load_training_jpg("Nature_Cosmic_Sun.jpg")
    dest_img = load_training_jpg("Animal_Salmon_Spawn_Eggs.jpg")
    dest_arr = np.asarray(dest_img, dtype=np.float32)
    try:
        underlay_rgb = np.array([int(v) for v in args.underlay_rgb.split(",")], dtype=np.float32)
    except ValueError as exc:
        raise SystemExit(f"Invalid --underlay-rgb value {args.underlay_rgb!r}; expected R,G,B") from exc
    if underlay_rgb.shape != (3,):
        raise SystemExit(f"Invalid --underlay-rgb value {args.underlay_rgb!r}; expected R,G,B")
    white_distance = white_seed_distance(source_img) if args.white_bg_from_source else None
    scheduled, dest_content = build_scheduled_masks(
        args.struct_start,
        args.struct_span,
        args.struct_duration,
        args.roe_start,
        args.roe_span,
        args.roe_duration,
        args.union_maxfilter,
        args.union_blur,
    )
    background_mask = 1.0 - dest_content
    raw_rebuild = None
    if args.rebuild_raw_no_dest_rect:
        raw_rebuild = build_raw_tweens_without_dest_rect(args.rebuild_resample_n)

    out_dir.mkdir(parents=True, exist_ok=False)
    print(f"input middle: {INPUT_FRAMES}")
    print(f"scheduled destination atom masks: {len(scheduled)}")
    if raw_rebuild is not None:
        print(f"rebuilt raw morph without destination rect: {raw_rebuild[2]}")
    print(f"output: {out_mp4}")

    for i, path in enumerate(frames):
        if i == 0:
            out = np.asarray(source_img, dtype=np.float32)
        else:
            if raw_rebuild is None:
                raw_img = Image.open(path).convert("RGB")
            else:
                me, tweens, _meta = raw_rebuild
                t_raw = i / max(1, len(frames) - 1)
                t = me.ease(t_raw, "easeInOut")
                raw_img = me.rasterize_shape_tweens(
                    tweens,
                    i,
                    len(frames),
                    t,
                    "austin__cosmic_sun_whole -> austin__salmon_spawn_eggs_whole",
                ).convert("RGB")
            base = np.asarray(raw_img, dtype=np.float32)
            if args.early_white_underlay:
                underlay_amount = ease((i - args.underlay_start) / args.underlay_duration) * args.underlay_strength
                if underlay_amount > 0:
                    fg_alpha = raw_foreground_alpha(
                        raw_img,
                        args.underlay_blur,
                        args.underlay_diff_threshold,
                        args.underlay_sat_threshold,
                        args.underlay_luma_threshold,
                        args.underlay_maxfilter,
                        args.underlay_alpha_blur,
                    )
                    cleaned = blend_arrays(
                        np.broadcast_to(underlay_rgb, base.shape).astype(np.float32),
                        base,
                        fg_alpha,
                    )
                    base = blend_arrays(base, cleaned, underlay_amount)
            if i < args.raw_until:
                out = base
            else:
                bg_amount = ease((i - args.bg_start) / args.bg_duration) * args.bg_strength
                # Clean only non-destination areas first; this removes late
                # straight-line residue without flattening active destination shapes.
                out = blend_arrays(base, dest_arr, background_mask * bg_amount)

                if white_distance is not None:
                    white_reveal = white_seed_reveal(
                        white_distance,
                        i,
                        args.white_bg_start,
                        args.white_bg_duration,
                        args.white_bg_radius,
                        args.white_bg_feather,
                    )
                    white_reveal = white_reveal * background_mask * args.white_bg_strength
                    out = blend_arrays(out, dest_arr, white_reveal)

                atom_amount = assembly_mask_for_frame(scheduled, i)
                out = blend_arrays(out, dest_arr, atom_amount)

                # A tiny final settle guarantees exact endpoint, after atom-mask
                # assembly has already done the main correction.
                final = ease((i - args.final_start) / args.final_duration)
                if final > 0:
                    out = blend_arrays(out, dest_arr, final)

        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(out_dir / f"frame_{i:04d}.png")
        if (i + 1) % 20 == 0:
            print(f"frame {i + 1}/120")

    compile_mp4(out_dir, out_mp4)
    shutil.copy2(Path(__file__), out_dir / "renderer_morph_raw_motion_endpoint_correct.py")
    print(f"wrote {out_mp4}")
    print(f"frames preserved in {out_dir}")


if __name__ == "__main__":
    main()
