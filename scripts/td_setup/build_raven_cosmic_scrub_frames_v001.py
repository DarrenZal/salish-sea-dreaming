#!/usr/bin/env python3
"""
Build a TouchDesigner scrub-ready Raven Sun -> Cosmic Sun frame sequence.

This is a TD control asset, not a promoted morph output. It uses the verified
training JPG endpoints and decomposed atom masks so frame 0 and frame N-1 match
Austin's actual raster endpoints instead of the older vector-render morph.

Algorithm:
  - load Animal_Bird_Raven_Sun.jpg and Nature_Cosmic_Sun.jpg, scale to 1024
  - use decomposed atom masks to sample Raven body/sun pixels
  - route Raven body particles into the Cosmic face/eye/mouth atom region
  - route Raven sun/ray particles into Cosmic sun/ray/central atom regions
  - spatially reveal the destination under the particle motion
  - force exact JPG endpoints at first and last frames

INTERNAL ONLY. Austin per-output approval is required before public use.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "austin-v2-ingest" / "training"
DECOMPOSED = ROOT / "austin-v2-ingest" / "decomposed"
ASSETS = ROOT / "td" / "templates" / "assets"

SRC_PIECE = "Animal_Bird_Raven_Sun"
DST_PIECE = "Nature_Cosmic_Sun"
SRC_JPG = TRAINING / "Animal_Bird_Raven_Sun.jpg"
DST_JPG = TRAINING / "Nature_Cosmic_Sun.jpg"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
VIEWBOX = 108.0
RNG_SEED = 170518

OUT_DIR = ASSETS / "raven_sun_to_cosmic_sun_scrub_frames_v001"
OUT_MP4 = ASSETS / "raven_sun_to_cosmic_sun_scrub_preview_v001.mp4"

BODY_LABELS = {"formline-primary", "eye-focal-oval"}
SRC_WARM_LABELS = {"sun-ray", "circle-oval"}
DST_FACE_LABELS = {
    "formline-primary",
    "eye-focal-oval",
    "circle-oval",
    "crescent",
    "trigon",
}
DST_WARM_LABELS = {"sun-ray", "trigon", "circle-oval"}


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    x = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def ease_in_out(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def load_endpoint(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    if img.size != (CANVAS, CANVAS):
        canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
        canvas.paste(img, ((CANVAS - img.width) // 2, (CANVAS - img.height) // 2))
        img = canvas
    return img


def read_atoms(piece: str) -> list[dict]:
    csv_path = DECOMPOSED / piece / "atom_metadata.csv"
    atoms: list[dict] = []
    with csv_path.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                atoms.append(
                    {
                        "atom_id": row["atom_id"],
                        "label": row["ai_label"],
                        "bbox": (
                            float(row["bbox_x"]),
                            float(row["bbox_y"]),
                            float(row["bbox_w"]),
                            float(row["bbox_h"]),
                        ),
                        "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                        "isolated_png": DECOMPOSED / piece / row["isolated_png"],
                    }
                )
            except (KeyError, ValueError):
                continue
    return atoms


def atom_mask(piece: str, atoms: list[dict], labels: set[str], atom_ids: set[str] | None = None) -> np.ndarray:
    mask = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for atom in atoms:
        if atom_ids is not None:
            if atom["atom_id"] not in atom_ids:
                continue
        elif atom["label"] not in labels:
            continue
        iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
        alpha = (255.0 - np.asarray(iso, dtype=np.float32)) / 255.0
        mask = np.maximum(mask, alpha)
    return np.clip(mask, 0.0, 1.0)


def weighted_points(mask: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    weights = mask.reshape(-1)
    total = float(weights.sum())
    if total <= 0.0:
        raise RuntimeError("Cannot sample from an empty atom mask")
    probs = weights / total
    idx = rng.choice(weights.size, size=n, replace=True, p=probs)
    y = idx // CANVAS
    x = idx % CANVAS
    jitter = rng.random((n, 2), dtype=np.float32) - 0.5
    return np.column_stack([x, y]).astype(np.float32) + jitter


def color_at(img_arr: np.ndarray, points: np.ndarray) -> np.ndarray:
    x = np.clip(np.round(points[:, 0]).astype(np.int32), 0, CANVAS - 1)
    y = np.clip(np.round(points[:, 1]).astype(np.int32), 0, CANVAS - 1)
    return img_arr[y, x, :].astype(np.float32)


def make_reveal_noise(rng: np.random.Generator) -> np.ndarray:
    small = (rng.random((96, 96), dtype=np.float32) * 255).astype(np.uint8)
    img = Image.fromarray(small, "L").resize((CANVAS, CANVAS), Image.Resampling.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(radius=10))
    noise = np.asarray(img, dtype=np.float32) / 255.0

    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS].astype(np.float32)
    dx = (xx - CANVAS * 0.5) / (CANVAS * 0.5)
    dy = (yy - CANVAS * 0.52) / (CANVAS * 0.5)
    radial = np.clip(np.sqrt(dx * dx + dy * dy), 0.0, 1.0)
    field = 0.62 * noise + 0.38 * radial
    field = (field - field.min()) / max(1e-6, field.max() - field.min())
    return field


def spatial_reveal(src_arr: np.ndarray, dst_arr: np.ndarray, reveal_field: np.ndarray, t: float) -> np.ndarray:
    phase = smoothstep(0.10, 0.94, t)
    width = 0.18
    alpha = np.clip((phase - reveal_field + width) / (2.0 * width), 0.0, 1.0)
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    # Keep frame 0 and frame N-1 exact.
    if t <= 0.0:
        alpha[:, :] = 0.0
    elif t >= 1.0:
        alpha[:, :] = 1.0
    out = src_arr * (1.0 - alpha[..., None]) + dst_arr * alpha[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def bezier(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float) -> np.ndarray:
    u = 1.0 - t
    return (u**3) * p0 + (3.0 * u * u * t) * p1 + (3.0 * u * t * t) * p2 + (t**3) * p3


def draw_particles(
    image: Image.Image,
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    src_colors: np.ndarray,
    dst_colors: np.ndarray,
    t: float,
    rng_offsets: np.ndarray,
    alpha_scale: float,
    base_radius: float,
) -> None:
    if t <= 0.02 or t >= 0.985:
        return
    p = ease_in_out(smoothstep(0.06, 0.95, t))
    center = np.array([CANVAS * 0.5, CANVAS * 0.52], dtype=np.float32)
    vec0 = src_pts - center
    vec1 = dst_pts - center
    norm0 = np.maximum(1.0, np.linalg.norm(vec0, axis=1, keepdims=True))
    norm1 = np.maximum(1.0, np.linalg.norm(vec1, axis=1, keepdims=True))
    radial0 = vec0 / norm0
    radial1 = vec1 / norm1
    perp = np.column_stack([-radial0[:, 1], radial0[:, 0]])

    amp = (72.0 + 78.0 * rng_offsets[:, 0:1]) * math.sin(math.pi * p)
    c1 = src_pts + radial0 * amp + perp * (34.0 * rng_offsets[:, 1:2])
    c2 = dst_pts - radial1 * amp - perp * (30.0 * rng_offsets[:, 2:3])
    pts = bezier(src_pts, c1, c2, dst_pts, p)
    curl = perp * (math.sin(math.pi * p) * 22.0 * np.sin((rng_offsets[:, 3:4] * 6.283) + p * 7.0))
    pts = pts + curl

    colors = src_colors * (1.0 - p) + dst_colors * p
    alpha = alpha_scale * (math.sin(math.pi * p) ** 0.72)
    radius = base_radius + 2.2 * math.sin(math.pi * p)

    draw = ImageDraw.Draw(image, "RGBA")
    # Draw every second particle early/late to reduce visual mud near endpoints.
    stride = 2 if alpha < 0.45 else 1
    for i in range(0, len(pts), stride):
        x, y = pts[i]
        if x < -8 or y < -8 or x > CANVAS + 8 or y > CANVAS + 8:
            continue
        r = radius * (0.65 + 0.8 * float(rng_offsets[i, 4]))
        c = colors[i]
        a = int(max(0, min(255, 255 * alpha * (0.55 + 0.45 * float(rng_offsets[i, 5])))))
        fill = (int(c[0]), int(c[1]), int(c[2]), a)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def write_readme(out_dir: Path, preview: Path) -> None:
    text = f"""# Raven Sun -> Cosmic Sun TD Scrub Frames v001

Internal TouchDesigner scrub asset for the mudra-controlled morph prototype.

## Source Files

- `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`
- `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`
- `austin-v2-ingest/decomposed/Animal_Bird_Raven_Sun/atom_metadata.csv`
- `austin-v2-ingest/decomposed/Nature_Cosmic_Sun/atom_metadata.csv`
- atom masks from both decomposed piece folders

## Algorithm

Frame 0 and the last frame are forced to the verified training JPG endpoints.
Intermediate frames use decomposed atom masks to sample Raven body and sun/ray
pixels, route them toward Cosmic Sun face/ray regions, and draw them as moving
particles over a spatial destination reveal. This is meant as a scrub-control
asset for TouchDesigner, not a canonical morph output.

## Known Limitations

- The background reveal is still a spatial image blend; the strongest authored
  motion is in the Raven body and sun/ray particle routing.
- Atom correspondence is visual/prototype-level, not an Austin-confirmed
  symbolic mapping.
- The particle layer is diagnostic and may need a cleaner path-level version if
  this pair becomes a show candidate.

## Cultural Status

INTERNAL ONLY. Austin per-output OK is required before public display.

## Outputs

- Frame sequence: `{out_dir}`
- Preview MP4: `{preview}`
"""
    (out_dir / "README.md").write_text(text)


def render(force: bool = False) -> dict:
    if OUT_DIR.exists() and any(OUT_DIR.glob("frame_*.jpg")) and not force:
        raise SystemExit(f"Refusing to overwrite existing frame sequence: {OUT_DIR}")
    if OUT_MP4.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing preview MP4: {OUT_MP4}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("frame_*.jpg"):
        old.unlink()

    src = load_endpoint(SRC_JPG)
    dst = load_endpoint(DST_JPG)
    src_arr = np.asarray(src, dtype=np.float32)
    dst_arr = np.asarray(dst, dtype=np.float32)

    src_atoms = read_atoms(SRC_PIECE)
    dst_atoms = read_atoms(DST_PIECE)

    src_body = atom_mask(SRC_PIECE, src_atoms, BODY_LABELS, atom_ids={"atom_0020"})
    # Dark-pixel intersection keeps the sampled particles on the actual Raven ink.
    src_dark = (np.mean(src_arr, axis=2) < 70).astype(np.float32)
    src_body = np.clip(src_body * src_dark, 0.0, 1.0)

    dst_face = atom_mask(DST_PIECE, dst_atoms, DST_FACE_LABELS)
    dst_dark = (np.mean(dst_arr, axis=2) < 120).astype(np.float32)
    dst_face = np.clip(dst_face * dst_dark, 0.0, 1.0)

    src_warm = atom_mask(SRC_PIECE, src_atoms, SRC_WARM_LABELS)
    dst_warm = atom_mask(DST_PIECE, dst_atoms, DST_WARM_LABELS)

    rng = np.random.default_rng(RNG_SEED)
    body_n = 1850
    warm_n = 950
    body_src = weighted_points(src_body, body_n, rng)
    body_dst = weighted_points(dst_face, body_n, rng)
    warm_src = weighted_points(src_warm, warm_n, rng)
    warm_dst = weighted_points(dst_warm, warm_n, rng)

    src_u8 = np.asarray(src, dtype=np.uint8)
    dst_u8 = np.asarray(dst, dtype=np.uint8)
    body_src_colors = color_at(src_u8, body_src)
    body_dst_colors = color_at(dst_u8, body_dst)
    warm_src_colors = color_at(src_u8, warm_src)
    warm_dst_colors = color_at(dst_u8, warm_dst)

    reveal = make_reveal_noise(rng)
    body_offsets = rng.random((body_n, 6), dtype=np.float32)
    warm_offsets = rng.random((warm_n, 6), dtype=np.float32)

    for i in range(N_FRAMES):
        t = i / (N_FRAMES - 1)
        if i == 0:
            frame = src.copy()
        elif i == N_FRAMES - 1:
            frame = dst.copy()
        else:
            base_arr = spatial_reveal(src_arr, dst_arr, reveal, t)
            frame = Image.fromarray(base_arr, "RGB").convert("RGBA")
            draw_particles(
                frame,
                warm_src,
                warm_dst,
                warm_src_colors,
                warm_dst_colors,
                t,
                warm_offsets,
                alpha_scale=0.68,
                base_radius=1.2,
            )
            draw_particles(
                frame,
                body_src,
                body_dst,
                body_src_colors,
                body_dst_colors,
                t,
                body_offsets,
                alpha_scale=0.78,
                base_radius=1.0,
            )
            frame = frame.convert("RGB")
        frame.save(OUT_DIR / f"frame_{i + 1:04d}.jpg", quality=94, subsampling=0)

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-framerate",
        str(FPS),
        "-i",
        str(OUT_DIR / "frame_%04d.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        str(OUT_MP4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1000:])

    write_readme(OUT_DIR, OUT_MP4)
    return {
        "frame_dir": str(OUT_DIR),
        "preview_mp4": str(OUT_MP4),
        "frames": N_FRAMES,
        "fps": FPS,
        "source_endpoint": str(SRC_JPG),
        "dest_endpoint": str(DST_JPG),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite this versioned TD asset.")
    args = parser.parse_args()
    result = render(force=args.force)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    main()
