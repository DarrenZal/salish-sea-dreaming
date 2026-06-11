#!/usr/bin/env python3
"""
Raven Sun -> Cosmic Sun endpoint-corrected shape morph v001.

Bounded offline pass:
- use the existing deterministic Raven->Cosmic shape morph as the motion base
- force exact verified training JPG endpoints
- smooth the final settle into the exact Cosmic endpoint
- no SD, no LoRA, no ControlNet
- never overwrite canonical outputs
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent.parent
TRAINING = ROOT / "austin-v2-ingest" / "training"
SOURCE_VECTORS = ROOT / "track2-deterministic" / "source-vectors"
BASE_FRAMES = ROOT / "track2-deterministic" / "morph_outputs" / "raven_sun_to_cosmic_sun"
BASE_MP4 = ROOT / "track2-deterministic" / "morph_outputs" / "raven_sun_to_cosmic_sun.mp4"
INTERNAL = ROOT / "track2-deterministic" / "morph_outputs_INTERNAL"
PROVENANCE = INTERNAL / "provenance.csv"

PAIR_ID = "raven_sun_to_cosmic_sun_endpoint_correct_v001"
OUT_DIR = INTERNAL / PAIR_ID
OUT_FRAMES = OUT_DIR / "frames"
OUT_MP4 = INTERNAL / f"{PAIR_ID}.mp4"
COMPARE_MP4 = OUT_DIR / "current_vs_endpoint_correct_v001_comparison.mp4"
CONTACT_SHEET = OUT_DIR / "current_vs_endpoint_correct_contact_sheet.png"
METRICS_JSON = OUT_DIR / "_endpoint_metrics.json"

CANVAS = 1024
FPS = 24


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    x = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def load_endpoint(name: str) -> Image.Image:
    img = Image.open(TRAINING / f"{name}.jpg").convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    canvas.paste(img, ((CANVAS - img.width) // 2, (CANVAS - img.height) // 2))
    return canvas


def mean_abs_delta(a: Image.Image, b: Image.Image) -> float:
    return float(np.mean(np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))))


def diff_mask(base_arr: np.ndarray, endpoint_arr: np.ndarray) -> np.ndarray:
    diff = np.mean(np.abs(base_arr - endpoint_arr), axis=2) / 255.0
    img = Image.fromarray(np.clip(diff * 255, 0, 255).astype(np.uint8), "L")
    img = img.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(radius=2.6))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.clip((arr - 0.012) / 0.16, 0.0, 1.0)


def render() -> dict:
    if OUT_DIR.exists() or OUT_MP4.exists():
        raise FileExistsError(f"Refusing to overwrite {OUT_DIR} or {OUT_MP4}")
    OUT_FRAMES.mkdir(parents=True, exist_ok=False)

    base_files = sorted(BASE_FRAMES.glob("frame_*.png"))
    if not base_files:
        raise FileNotFoundError(BASE_FRAMES)

    source = load_endpoint("Animal_Bird_Raven_Sun")
    dest = load_endpoint("Nature_Cosmic_Sun")
    source_arr = np.asarray(source, dtype=np.float32)
    dest_arr = np.asarray(dest, dtype=np.float32)
    n = len(base_files)

    for i, frame_path in enumerate(base_files):
        t = i / (n - 1)
        base = Image.open(frame_path).convert("RGB")
        base_arr = np.asarray(base, dtype=np.float32)

        if i == 0:
            out = source
        elif i == n - 1:
            out = dest
        else:
            out_arr = base_arr.copy()

            # Early endpoint correction: leave frame 0 exact, then rejoin the
            # existing shape-morph motion quickly. This fixes the old SVG-raster
            # endpoint mismatch without changing the middle.
            source_lock = 1.0 - smoothstep(0.0, 0.12, t)
            if source_lock > 0:
                out_arr = source_arr * source_lock + out_arr * (1.0 - source_lock)

            # Final correction: a diff-weighted settle toward the verified
            # Cosmic JPG. It starts before the last beat and mainly moves pixels
            # that still differ from the endpoint, so it is less visually like a
            # full-frame late crossfade.
            settle = smoothstep(0.72, 0.985, t)
            if settle > 0:
                mask = diff_mask(out_arr, dest_arr)
                correction = settle * (0.18 + 0.82 * mask)
                out_arr = out_arr * (1.0 - correction[..., None]) + dest_arr * correction[..., None]

            out = Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))

        out.save(OUT_FRAMES / f"frame_{i:04d}.png")

    compile_mp4(OUT_FRAMES / "frame_%04d.png", OUT_MP4)
    write_comparison(base_files)
    write_readme(n)
    append_provenance()
    shutil.copy2(Path(__file__), OUT_DIR / "renderer_raven_cosmic_endpoint_correct_v001.py")
    return write_metrics(base_files, source, dest)


def compile_mp4(input_pattern: Path, output: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(input_pattern),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def write_comparison(base_files: list[Path]) -> None:
    # Contact sheet at frame 0 / 25% / 50% / 75% / final.
    idxs = [0, round((len(base_files) - 1) * 0.25), round((len(base_files) - 1) * 0.50), round((len(base_files) - 1) * 0.75), len(base_files) - 1]
    labels = ["0%", "25%", "50%", "75%", "final"]
    rows = [
        ("current shape morph", BASE_FRAMES),
        ("endpoint-correct v001", OUT_FRAMES),
    ]
    thumb = 220
    left = 260
    header = 44
    row_h = thumb + 44
    sheet = Image.new("RGB", (left + thumb * len(idxs), header + row_h * len(rows)), "white")
    draw = ImageDraw.Draw(sheet)
    draw.rectangle([0, 0, sheet.width, header], fill=(245, 245, 245))
    draw.text((12, 12), "Raven -> Cosmic: current shape morph vs endpoint-correct v001", fill=(0, 0, 0))
    for col, label in enumerate(labels):
        draw.text((left + col * thumb + 8, header + 8), label, fill=(0, 0, 0))
    for row, (name, folder) in enumerate(rows):
        y = header + row * row_h
        draw.rectangle([0, y, left, y + row_h], fill=(250, 250, 250))
        draw.text((12, y + 74), name, fill=(0, 0, 0))
        for col, idx in enumerate(idxs):
            im = Image.open(folder / f"frame_{idx:04d}.png").convert("RGB")
            im.thumbnail((thumb - 8, thumb - 8), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb, thumb), "white")
            tile.paste(im, ((thumb - im.width) // 2, (thumb - im.height) // 2))
            x = left + col * thumb
            sheet.paste(tile, (x, y + 36))
            draw.rectangle([x, y + 36, x + thumb - 1, y + 36 + thumb - 1], outline=(220, 220, 220))
    sheet.save(CONTACT_SHEET)

    # Side-by-side comparison MP4, 2048x1024.
    tmp_dir = OUT_DIR / "comparison_frames"
    tmp_dir.mkdir(exist_ok=False)
    for i, base_path in enumerate(base_files):
        a = Image.open(base_path).convert("RGB")
        b = Image.open(OUT_FRAMES / f"frame_{i:04d}.png").convert("RGB")
        canvas = Image.new("RGB", (CANVAS * 2, CANVAS), "white")
        canvas.paste(a, (0, 0))
        canvas.paste(b, (CANVAS, 0))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, 0, CANVAS, 42], fill=(255, 255, 255))
        d.rectangle([CANVAS, 0, CANVAS * 2, 42], fill=(255, 255, 255))
        d.text((18, 12), "current shape morph", fill=(0, 0, 0))
        d.text((CANVAS + 18, 12), "endpoint-correct v001", fill=(0, 0, 0))
        canvas.save(tmp_dir / f"frame_{i:04d}.png")
    compile_mp4(tmp_dir / "frame_%04d.png", COMPARE_MP4)


def write_metrics(base_files: list[Path], source: Image.Image, dest: Image.Image) -> dict:
    current_first = Image.open(base_files[0]).convert("RGB")
    current_final = Image.open(base_files[-1]).convert("RGB")
    corrected_first = Image.open(OUT_FRAMES / "frame_0000.png").convert("RGB")
    corrected_final = Image.open(OUT_FRAMES / f"frame_{len(base_files)-1:04d}.png").convert("RGB")
    metrics = {
        "pair_id": PAIR_ID,
        "base_mp4": str(BASE_MP4),
        "output_mp4": str(OUT_MP4),
        "comparison_mp4": str(COMPARE_MP4),
        "contact_sheet": str(CONTACT_SHEET),
        "frame_count": len(base_files),
        "fps": FPS,
        "current_frame0_vs_training_jpg_mad": mean_abs_delta(current_first, source),
        "current_final_vs_training_jpg_mad": mean_abs_delta(current_final, dest),
        "corrected_frame0_vs_training_jpg_mad": mean_abs_delta(corrected_first, source),
        "corrected_final_vs_training_jpg_mad": mean_abs_delta(corrected_final, dest),
    }
    METRICS_JSON.write_text(json.dumps(metrics, indent=2))
    return metrics


def write_readme(frame_count: int) -> None:
    text = f"""# {PAIR_ID}

Internal Raven Sun -> Cosmic Sun endpoint-corrected shape morph.

## Source Files Used

- Motion base: `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun/`
- Baseline MP4: `track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4`
- Verified source endpoint: `austin-v2-ingest/training/Animal_Bird_Raven_Sun.jpg`
- Verified destination endpoint: `austin-v2-ingest/training/Nature_Cosmic_Sun.jpg`
- Source SVG reference: `track2-deterministic/source-vectors/Animal_Bird_Raven_Sun.svg`
- Destination SVG reference: `track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg`

## Algorithm

- Preserve the current deterministic shape-morph middle.
- Force frame 0 to the verified Raven Sun training JPG.
- Rejoin the existing shape-morph motion over the first 12% of the clip.
- Apply a diff-weighted final settle from 72% onward toward the verified Cosmic
  Sun training JPG.
- Force the final frame to the exact verified Cosmic Sun training JPG.
- No SD, no LoRA, no ControlNet, no diffusion finishing.

## Outputs

- MP4: `{OUT_MP4.name}`
- Frames: `frames/frame_0000.png` ... `frames/frame_{frame_count - 1:04d}.png`
- Comparison MP4: `current_vs_endpoint_correct_v001_comparison.mp4`
- Contact sheet: `current_vs_endpoint_correct_contact_sheet.png`
- Metrics: `_endpoint_metrics.json`

## Known Limitations

- This is endpoint correction around the existing shape morph, not a new
  authored atom correspondence system.
- The first 12% still blends from exact JPG endpoint into the existing SVG-based
  shape morph.
- The final settle is diff-weighted to avoid a visible late full-frame fade, but
  it is still an endpoint correction layer.

## Cultural Status

INTERNAL ONLY. Austin per-output OK is required before public,
sponsor-facing, or show-staged use.
"""
    (OUT_DIR / "README.md").write_text(text)


def append_provenance() -> None:
    row = [
        "2026-05-18",
        PAIR_ID,
        "Animal_Bird_Raven_Sun.jpg + Animal_Bird_Raven_Sun.svg",
        "Nature_Cosmic_Sun.jpg + Nature_Cosmic_Sun.svg",
        "medium",
        "internal-only",
        (
            "Endpoint-corrected Raven Sun -> Cosmic Sun shape morph. Uses current "
            "deterministic SVG shape-morph frames as motion base, forces exact "
            "verified training JPG endpoints, and applies diff-weighted final "
            "settle. No SD/LoRA/ControlNet. Internal only; Austin per-output OK required."
        ),
    ]
    existing = PROVENANCE.read_text() if PROVENANCE.exists() else ""
    if f",{PAIR_ID}," in existing:
        return
    with PROVENANCE.open("a", newline="") as f:
        csv.writer(f).writerow(row)


def main() -> None:
    result = render()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
