#!/usr/bin/env python3
"""Prepare a short Austin-derived motion excerpt for ControlNet + LoRA tests.

This extracts evenly sampled frames from a deterministic morph video, normalizes
them to square stills, and writes a manifest for the H200 motion renderer.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "austin-team-exploration-review-2026-05-17"
    / "01_lead_with"
    / "05_raven_sun_to_cosmic_sun_shape_morph.mp4"
)
DEFAULT_OUT = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "austin-controlnet-lora-motion-raven-cosmic-2026-05-17"
)


CONSENT_TEXT = """INTERNAL ONLY — PENDING AUSTIN PER-OUTPUT APPROVAL.

Prepared motion excerpt for ControlNet + Austin v2 LoRA technical testing.
Source frames are extracted from internal deterministic morph sketches derived
from Austin source files. Generated outputs are NOT Austin Harry artwork and
are NOT approved public/show material.

Purpose: test whether ControlNet/Canny and ControlNet/lineart preserve motion
edges, primitive legibility, clean fills, and figure continuity while low-scale
Austin v2 LoRA contributes only palette/register/atmosphere.

Do not share generated outputs outside the internal R&D loop without an
explicit operator decision and Austin's per-output approval.
"""


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def ffprobe_fps(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=avg_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    num, den = result.stdout.strip().split("/")
    return float(num) / float(den)


def load_font(size: int):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_contact_sheet(frames_dir: Path, out_path: Path, *, every: int = 6) -> None:
    files = sorted(frames_dir.glob("frame_*.jpg"))[::every]
    if not files:
        return
    thumb = 160
    label_h = 22
    cols = min(8, len(files))
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    font = load_font(11)
    for i, path in enumerate(files):
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
            x = (i % cols) * thumb
            y = (i // cols) * (thumb + label_h)
            sheet.paste(image, (x + (thumb - image.width) // 2, y))
            draw.text((x + 4, y + thumb + 3), path.stem, fill=(35, 35, 35), font=font)
    sheet.save(out_path, "JPEG", quality=92, optimize=True)


def write_manifest(
    out_dir: Path,
    *,
    source: Path,
    size: int,
    fps: float,
    source_fps: float,
    source_duration: float,
    crop_top_px: int,
    prompt_hint: str,
) -> dict[str, Any]:
    frames = sorted((out_dir / "frames").glob("frame_*.jpg"))
    items = [
        {
            "id": frame.stem,
            "input_file": f"frames/{frame.name}",
            "frame_index": idx,
            "prompt_hint": prompt_hint,
        }
        for idx, frame in enumerate(frames)
    ]
    try:
        source_video = str(source.resolve().relative_to(ROOT))
    except ValueError:
        source_video = str(source.resolve())
    manifest = {
        "boundary": "Internal technical experiment. Generated outputs require Austin per-output approval before any share/show use.",
        "source_video": source_video,
        "source_duration_seconds": source_duration,
        "source_fps": source_fps,
        "frame_count": len(items),
        "fps": fps,
        "size": size,
        "crop_top_px": crop_top_px,
        "items": items,
    }
    (out_dir / "motion_manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--frames", type=int, default=48)
    parser.add_argument("--size", type=int, default=768)
    parser.add_argument("--crop-top-px", type=int, default=48)
    parser.add_argument(
        "--prompt-hint",
        default=(
            "Raven Sun to Cosmic Sun deterministic morph, sun-centered vector "
            "composition, preserve circles crescents trigons, clean line "
            "boundaries and flat color fields"
        ),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    out_dir = args.out_dir
    frames_dir = out_dir / "frames"
    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    frames_dir.mkdir(parents=True)

    duration = ffprobe_duration(source)
    source_fps = ffprobe_fps(source)
    sample_fps = args.frames / duration
    filters: list[str] = []
    if args.crop_top_px > 0:
        filters.append(f"crop=iw:ih-{args.crop_top_px}:0:{args.crop_top_px}")
    filters.extend(
        [
            f"fps={sample_fps:.6f}",
            f"scale={args.size}:{args.size}:force_original_aspect_ratio=decrease",
            f"pad={args.size}:{args.size}:(ow-iw)/2:(oh-ih)/2:color=white",
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vf",
            ",".join(filters),
            "-frames:v",
            str(args.frames),
            "-q:v",
            "2",
            str(frames_dir / "frame_%04d.jpg"),
        ]
    )
    manifest = write_manifest(
        out_dir,
        source=source,
        size=args.size,
        fps=sample_fps,
        source_fps=source_fps,
        source_duration=duration,
        crop_top_px=args.crop_top_px,
        prompt_hint=args.prompt_hint,
    )
    (out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    make_contact_sheet(frames_dir, out_dir / "_source_excerpt_contact_sheet.jpg")
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Austin ControlNet + LoRA Motion Excerpt",
                "",
                "Internal motion-test inputs for Raven Sun to Cosmic Sun.",
                "",
                f"- Source: `{manifest['source_video']}`",
                f"- Frames: {manifest['frame_count']}",
                f"- Render FPS: {manifest['fps']:.3f}",
                "- Boundary: internal only, pending Austin per-output approval.",
                "",
            ]
        )
    )
    print(f"Wrote {manifest['frame_count']} frames to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
