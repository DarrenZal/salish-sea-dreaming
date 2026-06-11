#!/usr/bin/env python3
"""Prepare short real-footage clips for temporal style-transfer smoke tests.

This is intentionally local/CPU-only. It extracts short 720p H.264 excerpts
from Phase 1 hero clips and writes a manifest suitable for TELUS upload.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUT_DIR = Path("output/temporal-style-smoke-2026-05-13")

CLIPS = [
    {
        "id": "H2_herring_in_kelp_5s",
        "src": "media/hero-subclips/H2_herring_in_kelp.mp4",
        "start": 12.0,
        "duration": 5.0,
        "why": "fish/kelp structure; best candidate for ControlNet Canny + style pass",
    },
    {
        "id": "H5_reef_garden_5s",
        "src": "media/hero-subclips/H5_reef_garden.mp4",
        "start": 4.0,
        "duration": 5.0,
        "why": "complex reef texture; best candidate for img2img style pass",
    },
    {
        "id": "H8_milky_water_5s",
        "src": "media/hero-subclips/H8_milky_water.mp4",
        "start": 5.0,
        "duration": 5.0,
        "why": "soft water/spawn atmosphere; candidate pearl-background material",
    },
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def extract_clip(spec: dict) -> dict:
    src = Path(spec["src"])
    if not src.exists():
        raise FileNotFoundError(src)

    inputs_dir = OUT_DIR / "inputs"
    thumbs_dir = OUT_DIR / "thumbs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    out = inputs_dir / f"{spec['id']}.mp4"
    thumb = thumbs_dir / f"{spec['id']}_mid.jpg"

    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(spec["start"]),
            "-t",
            str(spec["duration"]),
            "-i",
            str(src),
            "-map",
            "0:v:0",
            "-map_metadata",
            "-1",
            "-an",
            "-dn",
            "-vf",
            "scale=1280:-2,fps=24",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-write_tmcd",
            "0",
            str(out),
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(spec["duration"] / 2),
            "-i",
            str(out),
            "-frames:v",
            "1",
            "-update",
            "1",
            "-q:v",
            "2",
            str(thumb),
        ]
    )

    probed = ffprobe(out)
    return {
        **spec,
        "output": str(out),
        "thumbnail": str(thumb),
        "probe": probed,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [extract_clip(spec) for spec in CLIPS]
    manifest = {
        "created": "2026-05-13",
        "purpose": "Internal temporal style-transfer smoke: real footage motion + v2 Austin style post-process.",
        "approval_boundary": "Internal recipe proof only; not public artwork and not for Austin/sponsors without explicit operator decision.",
        "clips": results,
    }
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
