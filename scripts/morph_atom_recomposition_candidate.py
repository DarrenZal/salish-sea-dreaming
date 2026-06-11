#!/usr/bin/env python3
"""
Generic Austin atom-recomposition transition candidate.

This is for offline transition scouting, not TouchDesigner. It uses verified
training JPG endpoints and available decomposed atom masks. The motion is meant
to keep visible decomposition/recomposition in the middle, then settle to the
exact destination endpoint.

Default output:
  track2-deterministic/morph_outputs_INTERNAL/
  bee_to_cosmic_sun_atom_recomposition_v001.mp4
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
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent.parent
TRAINING = ROOT / "austin-v2-ingest" / "training"
DECOMPOSED = ROOT / "austin-v2-ingest" / "decomposed"
INTERNAL = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL"
PROVENANCE = INTERNAL / "provenance.csv"

CANVAS = 1024
FPS = 24
N_FRAMES = 120
RNG_SEED = 20260518

DEFAULT_SOURCE = "Animal_Insect_Bee"
DEFAULT_DEST = "Nature_Cosmic_Sun"
DEFAULT_PAIR_ID = "bee_to_cosmic_sun_atom_recomposition_v001"

EXCLUDE_LABELS = {"background-field"}


@dataclass(frozen=True)
class AtomSprite:
    atom_id: str
    label: str
    center: np.ndarray
    area: float
    mean_color: np.ndarray
    rgba: Image.Image
    crop_bbox: tuple[int, int, int, int]
    mask: np.ndarray

    @property
    def size(self) -> float:
        w = self.crop_bbox[2] - self.crop_bbox[0]
        h = self.crop_bbox[3] - self.crop_bbox[1]
        return math.sqrt(max(1.0, float(w * h)))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    x = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def load_endpoint(piece: str) -> Image.Image:
    path = TRAINING / f"{piece}.jpg"
    if not path.exists():
        raise FileNotFoundError(path)
    img = Image.open(path).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    canvas.paste(img, ((CANVAS - img.width) // 2, (CANVAS - img.height) // 2))
    return canvas


def normalize_atom_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    canvas.paste(img, ((CANVAS - img.width) // 2, (CANVAS - img.height) // 2))
    return canvas


def alpha_from_isolated_atom(img: Image.Image) -> Image.Image:
    """Extract alpha from white-background atom PNGs, preserving pale yellows."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    diff = np.max(255.0 - arr, axis=2)
    alpha = np.clip((diff - 4.0) / 52.0, 0.0, 1.0)
    mask = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.35))
    return mask


def make_sprite(endpoint: Image.Image, atom_id: str, label: str, atom_png: Path) -> AtomSprite | None:
    atom_img = normalize_atom_image(atom_png)
    alpha_img = alpha_from_isolated_atom(atom_img)
    bbox = alpha_img.getbbox()
    if bbox is None:
        return None
    pad = 8
    x0 = max(0, bbox[0] - pad)
    y0 = max(0, bbox[1] - pad)
    x1 = min(CANVAS, bbox[2] + pad)
    y1 = min(CANVAS, bbox[3] + pad)
    if x1 <= x0 or y1 <= y0:
        return None

    alpha_arr = np.asarray(alpha_img, dtype=np.float32) / 255.0
    area = float(alpha_arr.sum())
    if area < 20.0:
        return None

    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS].astype(np.float32)
    center = np.array(
        [
            float((xx * alpha_arr).sum() / max(1e-6, area)),
            float((yy * alpha_arr).sum() / max(1e-6, area)),
        ],
        dtype=np.float32,
    )

    endpoint_arr = np.asarray(endpoint, dtype=np.float32)
    color_weight = alpha_arr[..., None]
    mean = (endpoint_arr * color_weight).sum(axis=(0, 1)) / max(1e-6, color_weight.sum())

    rgba = endpoint.convert("RGBA")
    rgba.putalpha(alpha_img)
    rgba = rgba.crop((x0, y0, x1, y1))
    return AtomSprite(
        atom_id=atom_id,
        label=label or "unclassified",
        center=center,
        area=area,
        mean_color=mean.astype(np.float32),
        rgba=rgba,
        crop_bbox=(x0, y0, x1, y1),
        mask=alpha_arr,
    )


def read_sprites(piece: str, endpoint: Image.Image) -> list[AtomSprite]:
    csv_path = DECOMPOSED / piece / "atom_metadata.csv"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    sprites: list[AtomSprite] = []
    with csv_path.open(newline="") as f:
        for row in csv.DictReader(f):
            label = row.get("ai_label", "") or "unclassified"
            if label in EXCLUDE_LABELS:
                continue
            atom_png = DECOMPOSED / piece / row["isolated_png"]
            sprite = make_sprite(endpoint, row["atom_id"], label, atom_png)
            if sprite is not None:
                sprites.append(sprite)
    sprites.sort(key=lambda a: a.area, reverse=True)
    return sprites


def union_mask(atoms: list[AtomSprite], blur: float = 2.0) -> np.ndarray:
    mask = np.zeros((CANVAS, CANVAS), dtype=np.float32)
    for atom in atoms:
        mask = np.maximum(mask, atom.mask)
    img = Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8), "L")
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur))
    return np.asarray(img, dtype=np.float32) / 255.0


def assign_atoms(src_atoms: list[AtomSprite], dst_atoms: list[AtomSprite]) -> list[int]:
    n = min(len(src_atoms), len(dst_atoms))
    if n == 0:
        return []
    src = src_atoms[:n]
    dst = dst_atoms[:n]
    cost = np.zeros((n, n), dtype=np.float32)
    for i, a in enumerate(src):
        for j, b in enumerate(dst):
            pos = np.linalg.norm((a.center - b.center) / CANVAS)
            color = np.linalg.norm((a.mean_color - b.mean_color) / 255.0) / math.sqrt(3.0)
            size = abs(math.log(max(1.0, a.area) / max(1.0, b.area)))
            cost[i, j] = 0.48 * pos + 0.34 * color + 0.18 * min(2.0, size)
    try:
        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost)
        assignment = [-1] * n
        for r, c in zip(row_ind, col_ind):
            assignment[int(r)] = int(c)
        return assignment
    except Exception:
        used: set[int] = set()
        assignment = []
        for i in range(n):
            order = np.argsort(cost[i])
            pick = next((int(j) for j in order if int(j) not in used), int(order[0]))
            used.add(pick)
            assignment.append(pick)
        return assignment


def weighted_points(mask: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    weights = np.clip(mask.reshape(-1), 0, None)
    if float(weights.sum()) <= 0:
        raise RuntimeError("empty mask")
    probs = weights / weights.sum()
    idx = rng.choice(weights.size, size=n, replace=True, p=probs)
    y = idx // CANVAS
    x = idx % CANVAS
    jitter = rng.random((n, 2), dtype=np.float32) - 0.5
    return np.column_stack([x, y]).astype(np.float32) + jitter


def sample_colors(img_arr: np.ndarray, points: np.ndarray) -> np.ndarray:
    x = np.clip(np.round(points[:, 0]).astype(np.int32), 0, CANVAS - 1)
    y = np.clip(np.round(points[:, 1]).astype(np.int32), 0, CANVAS - 1)
    return img_arr[y, x].astype(np.float32)


def make_reveal_field(rng: np.random.Generator) -> np.ndarray:
    small = (rng.random((90, 90), dtype=np.float32) * 255).astype(np.uint8)
    noise = Image.fromarray(small, "L").resize((CANVAS, CANVAS), Image.Resampling.BICUBIC)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=12))
    noise_arr = np.asarray(noise, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS].astype(np.float32)
    radial = np.sqrt(((xx - CANVAS * 0.5) / (CANVAS * 0.58)) ** 2 + ((yy - CANVAS * 0.5) / (CANVAS * 0.58)) ** 2)
    field = 0.54 * radial + 0.46 * noise_arr
    return (field - field.min()) / max(1e-6, field.max() - field.min())


def transform_sprite(sprite: AtomSprite, center: np.ndarray, scale: float, rotation: float, alpha: float) -> Image.Image:
    img = sprite.rgba
    if abs(scale - 1.0) > 0.03:
        w = max(2, int(round(img.width * scale)))
        h = max(2, int(round(img.height * scale)))
        img = img.resize((w, h), Image.Resampling.LANCZOS)
    if abs(rotation) > 0.05:
        img = img.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
    if alpha < 0.995:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    return img


def paste_center(base: Image.Image, sprite: Image.Image, center: np.ndarray) -> None:
    x = int(round(float(center[0]) - sprite.width * 0.5))
    y = int(round(float(center[1]) - sprite.height * 0.5))
    base.alpha_composite(sprite, (x, y))


def bezier(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float) -> np.ndarray:
    u = 1.0 - t
    return (u**3) * p0 + (3 * u * u * t) * p1 + (3 * u * t * t) * p2 + (t**3) * p3


def draw_particles(
    img: Image.Image,
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    src_colors: np.ndarray,
    dst_colors: np.ndarray,
    offsets: np.ndarray,
    t: float,
) -> None:
    p = ease(smoothstep(0.10, 0.84, t))
    if p <= 0.0 or p >= 1.0:
        return
    center = np.array([CANVAS * 0.5, CANVAS * 0.5], dtype=np.float32)
    v0 = src_pts - center
    v1 = dst_pts - center
    n0 = np.maximum(1.0, np.linalg.norm(v0, axis=1, keepdims=True))
    n1 = np.maximum(1.0, np.linalg.norm(v1, axis=1, keepdims=True))
    radial0 = v0 / n0
    radial1 = v1 / n1
    perp = np.column_stack([-radial0[:, 1], radial0[:, 0]])
    amp = (82.0 + 110.0 * offsets[:, 0:1]) * math.sin(math.pi * p)
    c1 = src_pts + radial0 * amp + perp * (52.0 * (offsets[:, 1:2] - 0.5))
    c2 = dst_pts - radial1 * amp - perp * (45.0 * (offsets[:, 2:3] - 0.5))
    pts = bezier(src_pts, c1, c2, dst_pts, p)
    pts += perp * (20.0 * math.sin(math.pi * p) * np.sin(offsets[:, 3:4] * 6.283 + p * 8.0))
    colors = src_colors * (1.0 - p) + dst_colors * p
    alpha = 0.78 * (math.sin(math.pi * p) ** 0.75)
    radius = 1.4 + 2.2 * math.sin(math.pi * p)
    draw = ImageDraw.Draw(img, "RGBA")
    stride = 2 if alpha < 0.38 else 1
    for i in range(0, len(pts), stride):
        x, y = pts[i]
        if x < -10 or y < -10 or x > CANVAS + 10 or y > CANVAS + 10:
            continue
        r = radius * (0.55 + 0.85 * float(offsets[i, 4]))
        c = colors[i]
        a = int(255 * alpha * (0.55 + 0.45 * float(offsets[i, 5])))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(int(c[0]), int(c[1]), int(c[2]), a))


def render_pair(
    source_piece: str,
    dest_piece: str,
    pair_id: str,
    source_fade_start: float,
    source_fade_end: float,
    dest_start: float,
    dest_spread: float,
    dest_duration: float,
    settle_start: float,
    cultural_load: str,
) -> dict:
    out_dir = INTERNAL / pair_id
    out_mp4 = INTERNAL / f"{pair_id}.mp4"
    if out_dir.exists() or out_mp4.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {out_dir} / {out_mp4}")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=False)

    rng = np.random.default_rng(RNG_SEED)
    src_img = load_endpoint(source_piece)
    dst_img = load_endpoint(dest_piece)
    src_arr = np.asarray(src_img, dtype=np.float32)
    dst_arr = np.asarray(dst_img, dtype=np.float32)

    src_atoms = read_sprites(source_piece, src_img)
    dst_atoms = read_sprites(dest_piece, dst_img)
    if not src_atoms or not dst_atoms:
        raise RuntimeError(f"Need atom sprites for both pieces; got {len(src_atoms)} source and {len(dst_atoms)} destination")

    assignment = assign_atoms(src_atoms, dst_atoms)
    dst_centers = np.array([a.center for a in dst_atoms], dtype=np.float32)
    source_union = union_mask(src_atoms, blur=1.2)
    dest_union = union_mask(dst_atoms, blur=3.0)
    dest_bg = np.clip(1.0 - dest_union, 0.0, 1.0)
    reveal_field = make_reveal_field(rng)

    particle_n = 1900
    src_pts = weighted_points(source_union, particle_n, rng)
    dst_pts = weighted_points(dest_union, particle_n, rng)
    src_colors = sample_colors(src_arr, src_pts)
    dst_colors = sample_colors(dst_arr, dst_pts)
    particle_offsets = rng.random((particle_n, 6), dtype=np.float32)
    atom_offsets = rng.random((len(src_atoms), 6), dtype=np.float32)

    for fi in range(N_FRAMES):
        t = fi / (N_FRAMES - 1)
        if fi == 0:
            frame = src_img.copy()
        elif fi == N_FRAMES - 1:
            frame = dst_img.copy()
        else:
            bg_alpha = smoothstep(0.24, 0.82, t)
            spatial = np.clip((bg_alpha - reveal_field + 0.18) / 0.36, 0.0, 1.0)
            spatial = spatial * spatial * (3.0 - 2.0 * spatial)
            bg_mask = (dest_bg * spatial)[..., None]
            base_arr = np.ones_like(src_arr) * 255.0
            base_arr = base_arr * (1.0 - bg_mask) + dst_arr * bg_mask
            frame = Image.fromarray(np.clip(base_arr, 0, 255).astype(np.uint8)).convert("RGBA")

            # Moving source atom sprites.
            for i, atom in enumerate(src_atoms):
                motion = ease(smoothstep(0.05, 0.78, t))
                if i < len(assignment) and assignment[i] >= 0:
                    target_atom = dst_atoms[assignment[i]]
                    target = target_atom.center
                    target_scale = math.sqrt(max(1.0, target_atom.area) / max(1.0, atom.area))
                    target_scale = float(np.clip(target_scale, 0.42, 1.85))
                else:
                    target = dst_centers[i % len(dst_centers)] + (atom_offsets[i, 0:2] - 0.5) * 80.0
                    target_scale = 0.5

                src_center = atom.center
                vec = src_center - np.array([CANVAS * 0.5, CANVAS * 0.5], dtype=np.float32)
                norm = max(1.0, float(np.linalg.norm(vec)))
                radial = vec / norm
                perp = np.array([-radial[1], radial[0]], dtype=np.float32)
                c1 = src_center + radial * (70.0 + 90.0 * atom_offsets[i, 0]) + perp * (70.0 * (atom_offsets[i, 1] - 0.5))
                c2 = target - radial * (55.0 + 70.0 * atom_offsets[i, 2]) - perp * (55.0 * (atom_offsets[i, 3] - 0.5))
                center = bezier(src_center, c1, c2, target, motion)
                scale = 1.0 * (1.0 - motion) + target_scale * motion
                pulse = 1.0 + 0.10 * math.sin(math.pi * motion)
                rotation = (atom_offsets[i, 4] - 0.5) * 38.0 * math.sin(math.pi * motion)
                alpha = 0.96 * (1.0 - 0.92 * smoothstep(source_fade_start, source_fade_end, t))
                if i >= len(assignment):
                    alpha *= 1.0 - smoothstep(0.48, 0.86, t)
                sprite = transform_sprite(atom, center, scale * pulse, rotation, alpha)
                paste_center(frame, sprite, center)

            draw_particles(frame, src_pts, dst_pts, src_colors, dst_colors, particle_offsets, t)

            # Destination atoms assemble in place. Larger atoms arrive slightly
            # earlier so the image reads as recomposition, not a final fade.
            for j, atom in enumerate(dst_atoms):
                order = j / max(1, len(dst_atoms) - 1)
                start = dest_start + dest_spread * order
                a = smoothstep(start, min(0.96, start + dest_duration), t)
                if a <= 0:
                    continue
                scale = 0.72 + 0.28 * a
                rotation = (1.0 - a) * (14.0 * math.sin(j * 1.7))
                sprite = transform_sprite(atom, atom.center, scale, rotation, a)
                paste_center(frame, sprite, atom.center)

            # Endpoint settle over the final frames. This is intentionally late
            # and short; the primary transition is atom motion above.
            settle = smoothstep(settle_start, 0.995, t)
            if settle > 0:
                arr = np.asarray(frame.convert("RGB"), dtype=np.float32)
                arr = arr * (1.0 - settle) + dst_arr * settle
                frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

            frame = frame.convert("RGB")

        frame.save(frames_dir / f"frame_{fi:04d}.png")

    cmd = [
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
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    renderer_copy = out_dir / "renderer_morph_atom_recomposition_candidate.py"
    shutil.copy2(Path(__file__), renderer_copy)
    write_readme(
        out_dir,
        out_mp4,
        source_piece,
        dest_piece,
        pair_id,
        len(src_atoms),
        len(dst_atoms),
        source_fade_start,
        source_fade_end,
        dest_start,
        dest_spread,
        dest_duration,
        settle_start,
    )
    append_provenance(pair_id, source_piece, dest_piece, cultural_load)
    return {
        "pair_id": pair_id,
        "mp4": str(out_mp4),
        "frames": str(frames_dir),
        "readme": str(out_dir / "README.md"),
        "source_atoms": len(src_atoms),
        "dest_atoms": len(dst_atoms),
    }


def write_readme(
    out_dir: Path,
    out_mp4: Path,
    source_piece: str,
    dest_piece: str,
    pair_id: str,
    source_atoms: int,
    dest_atoms: int,
    source_fade_start: float,
    source_fade_end: float,
    dest_start: float,
    dest_spread: float,
    dest_duration: float,
    settle_start: float,
) -> None:
    text = f"""# {pair_id}

Internal offline transition candidate.

## Source Files Used

- `austin-v2-ingest/training/{source_piece}.jpg`
- `austin-v2-ingest/training/{dest_piece}.jpg`
- `austin-v2-ingest/decomposed/{source_piece}/atom_metadata.csv`
- `austin-v2-ingest/decomposed/{dest_piece}/atom_metadata.csv`
- isolated atom PNG masks from both decomposed folders

## Algorithm

- Frame 0 is forced to the verified source training JPG.
- Final frame is forced to the verified destination training JPG.
- Source atom masks are converted into transparent sprites.
- Destination atom masks are converted into transparent sprites.
- Source atoms are assigned to destination atoms by weighted visual cost:
  centroid distance, average color distance, and area similarity.
- Source atoms move along curved paths while source-colored particles flow
  toward destination atom masks.
- Destination atoms assemble in place during the second half of the clip.
- A short endpoint settle only cleans up the final frames; it is not the main
  transition.

## Counts

- Source atoms used: {source_atoms}
- Destination atoms used: {dest_atoms}

## Known Limitations

- This is an automatic visual correspondence pass, not Austin-authored semantic
  mapping.
- Bee atom labels are currently unclassified in the metadata, so this relies on
  visual atom geometry rather than formline-type labels.
- Thin pale shapes can have imperfect alpha extraction from white-background
  atom PNGs.
- The final endpoint still uses a short image settle to guarantee exact
  destination fidelity.

## Cultural Status

INTERNAL ONLY. Austin per-output OK is required before any public,
sponsor-facing, or show-staged use.

## Output

- MP4: `{out_mp4.name}`
- Frames: `frames/frame_0000.png` ... `frames/frame_0119.png`
- Renderer copy: `renderer_morph_atom_recomposition_candidate.py`

## Timing Parameters

- source_fade_start: {source_fade_start}
- source_fade_end: {source_fade_end}
- dest_start: {dest_start}
- dest_spread: {dest_spread}
- dest_duration: {dest_duration}
- settle_start: {settle_start}
"""
    (out_dir / "README.md").write_text(text)


def append_provenance(pair_id: str, source_piece: str, dest_piece: str, cultural_load: str) -> None:
    row = [
        "2026-05-18",
        pair_id,
        f"{source_piece}.jpg",
        f"{dest_piece}.jpg",
        cultural_load,
        "internal-only",
        (
            "Offline atom-recomposition candidate. Uses verified training JPG "
            "endpoints and decomposed atom masks; source atoms move as sprites "
            "with particle flow into destination atom positions. Final frame is "
            "exact destination. Internal only; Austin per-output OK required."
        ),
    ]
    existing = PROVENANCE.read_text() if PROVENANCE.exists() else ""
    if f",{pair_id}," in existing:
        return
    with PROVENANCE.open("a", newline="") as f:
        csv.writer(f).writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--dest", default=DEFAULT_DEST)
    ap.add_argument("--pair-id", default=DEFAULT_PAIR_ID)
    ap.add_argument("--source-fade-start", type=float, default=0.58)
    ap.add_argument("--source-fade-end", type=float, default=0.94)
    ap.add_argument("--dest-start", type=float, default=0.42)
    ap.add_argument("--dest-spread", type=float, default=0.18)
    ap.add_argument("--dest-duration", type=float, default=0.34)
    ap.add_argument("--settle-start", type=float, default=0.935)
    ap.add_argument("--cultural-load", default="medium")
    args = ap.parse_args()
    result = render_pair(
        args.source,
        args.dest,
        args.pair_id,
        args.source_fade_start,
        args.source_fade_end,
        args.dest_start,
        args.dest_spread,
        args.dest_duration,
        args.settle_start,
        args.cultural_load,
    )
    print(result)


if __name__ == "__main__":
    main()
