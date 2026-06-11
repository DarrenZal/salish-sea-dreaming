#!/usr/bin/env python3
"""Prepare 12 Austin-derived stills for the ControlNet + LoRA matrix.

This is a local-only prep step. It extracts/crops representative frames from
the deterministic morph outputs, normalizes them to square PNGs, writes a
manifest, and builds Canny/edge previews so the H200 job has clean inputs.

Boundary: internal technical experiment only. These inputs come from existing
internal deterministic sketches; any generated outputs remain pending Austin
per-output approval.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "austin-controlnet-lora-matrix-2026-05-17"
)


@dataclass(frozen=True)
class SourceSpec:
    id: str
    path: str
    fractions: tuple[float, ...]
    prompt_hint: str
    crop_top_px: int = 0


SOURCES = [
    SourceSpec(
        id="primitive_cycle",
        path="track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4",
        fractions=(0.15, 0.50, 0.85),
        prompt_hint="circle oval crescent trigon primitive shape study, clean flat vector forms",
        crop_top_px=48,
    ),
    SourceSpec(
        id="primitive_field",
        path="track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4",
        fractions=(0.25, 0.75),
        prompt_hint="field of circle oval crescent trigon primitive forms, clean repeated vector geometry",
        crop_top_px=0,
    ),
    SourceSpec(
        id="raven_cosmic",
        path="track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/01_lead_with/05_raven_sun_to_cosmic_sun_shape_morph.mp4",
        fractions=(0.08, 0.50, 0.92),
        prompt_hint="sun-centered vector composition, radial trigons, clean circular geometry",
        crop_top_px=48,
    ),
    SourceSpec(
        id="cosmic_salmon_v007",
        path="track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4",
        fractions=(0.35, 0.75),
        prompt_hint="sun to salmon internal morph study, clean line boundaries, circle and crescent structure",
        crop_top_px=0,
    ),
    SourceSpec(
        id="pearl_bead",
        path="track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4",
        fractions=(0.35, 0.65),
        prompt_hint="pearl bead carrying a vector morph across a graph edge, circular container, clean geometry",
        crop_top_px=0,
    ),
]


CONSENT_TEXT = """INTERNAL ONLY — PENDING AUSTIN PER-OUTPUT APPROVAL.

Prepared inputs for ControlNet + Austin v2 LoRA technical matrix.
Generated from existing internal deterministic sketches and synthetic graph/
primitive prototypes. These are NOT public assets and NOT approved artwork.

Use case: test whether ControlNet/Canny can preserve circles, crescents,
trigons, line boundaries, and clean fills while a low-scale Austin v2 LoRA
acts only as palette/register/style prior.

Do not share generated outputs outside the internal R&D loop without Austin's
explicit per-output approval.
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


def extract_video_frame(src: Path, out: Path, *, fraction: float, size: int, crop_top_px: int) -> None:
    duration = ffprobe_duration(src)
    timestamp = max(0.0, min(duration * fraction, max(0.0, duration - 0.05)))
    filters: list[str] = []
    if crop_top_px > 0:
        filters.append(f"crop=iw:ih-{crop_top_px}:0:{crop_top_px}")
    filters.extend(
        [
            f"scale={size}:{size}:force_original_aspect_ratio=decrease",
            f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=white",
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.4f}",
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-vf",
            ",".join(filters),
            "-q:v",
            "2",
            "-update",
            "1",
            str(out),
        ]
    )


def normalize_image(src: Path, out: Path, *, size: int, crop_top_px: int) -> None:
    with Image.open(src) as image:
        image = image.convert("RGB")
        if crop_top_px > 0:
            image = image.crop((0, crop_top_px, image.width, image.height))
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (size, size), "white")
        canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
        if out.suffix.lower() in {".jpg", ".jpeg"}:
            canvas.save(out, "JPEG", quality=94, optimize=True)
        else:
            canvas.save(out)


def edge_preview(src: Path, out: Path) -> None:
    try:
        import cv2
        import numpy as np

        arr = np.array(Image.open(src).convert("RGB"))
        edges = cv2.Canny(arr, threshold1=80, threshold2=180)
        Image.fromarray(edges).convert("RGB").save(out)
    except Exception:
        with Image.open(src) as image:
            image = ImageOps.grayscale(image)
            image = image.filter(ImageFilter.FIND_EDGES)
            image = ImageOps.autocontrast(image)
            image.convert("RGB").save(out)


def write_readme(out_dir: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Austin ControlNet + LoRA Matrix Inputs",
        "",
        "Internal technical inputs for testing ControlNet/Canny + Austin v2 LoRA.",
        "",
        "- `inputs/`: normalized 768x768 source stills",
        "- `control_previews/`: local Canny/edge previews",
        "- `input_manifest.json`: provenance and prompt hints",
        "- `CONSENT.txt`: internal-only boundary",
        "",
        f"Prepared still count: {len(manifest['items'])}",
        "",
        "Evaluation question: do circle/crescent/trigon shapes and clean vector",
        "boundaries survive while LoRA acts only as a low-scale atmospheric pass?",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--size", type=int, default=768)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir
    inputs_dir = out_dir / "inputs"
    previews_dir = out_dir / "control_previews"
    if out_dir.exists():
        if not args.force:
            raise SystemExit(f"Output exists; pass --force to replace: {out_dir}")
        shutil.rmtree(out_dir)
    inputs_dir.mkdir(parents=True)
    previews_dir.mkdir(parents=True)

    items: list[dict[str, Any]] = []
    idx = 1
    for source in SOURCES:
        src = ROOT / source.path
        if not src.exists():
            raise FileNotFoundError(src)
        for frame_idx, fraction in enumerate(source.fractions, start=1):
            item_id = f"{idx:02d}_{source.id}_{frame_idx:02d}"
            out_png = inputs_dir / f"{item_id}.jpg"
            if src.suffix.lower() in {".mp4", ".mov", ".m4v"}:
                extract_video_frame(
                    src,
                    out_png,
                    fraction=fraction,
                    size=args.size,
                    crop_top_px=source.crop_top_px,
                )
            else:
                normalize_image(src, out_png, size=args.size, crop_top_px=source.crop_top_px)
            edge_png = previews_dir / f"{item_id}_canny.png"
            edge_preview(out_png, edge_png)
            items.append(
                {
                    "id": item_id,
                    "source": asdict(source),
                    "source_path": str(src.relative_to(ROOT)),
                    "fraction": fraction,
                    "input_file": f"inputs/{out_png.name}",
                    "control_preview_file": f"control_previews/{edge_png.name}",
                    "prompt_hint": source.prompt_hint,
                }
            )
            idx += 1

    manifest = {
        "boundary": "Internal technical experiment. Generated outputs require Austin per-output approval before any share/show use.",
        "size": args.size,
        "control_method": "Canny edges computed by the H200 matrix runner; local previews included.",
        "items": items,
    }
    (out_dir / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    write_readme(out_dir, manifest)
    print(f"Prepared {len(items)} input stills in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
