#!/usr/bin/env python3
"""
Export primitive_field_v002_flocking as clean composable layers.

The original v002 light/dark clips are baked onto backgrounds and include a
small header. This script reuses the same primitive cycle, random seed, and
curl-noise atom motion, but renders transparent-background layer masters for
Resolume composition over footage.
"""
from __future__ import annotations

import json
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from primitive_field_v2_flocking import (
    ATOM_SIZE,
    CANVAS_H,
    CANVAS_W,
    CYCLE_PERIOD_FRAMES,
    FPS,
    N_ATOMS,
    N_FRAMES,
    PALETTE_DARK_BG,
    PALETTE_LIGHT_BG,
    curl_noise,
    load_full_cycle_frames,
    render_atom,
)


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "primitive_field_v002_flocking_layer_exports_2026-05-23"
)


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:])


def init_atoms(palette: list[tuple[int, int, int]]) -> list[dict[str, object]]:
    random.seed(7)
    atoms: list[dict[str, object]] = []
    for _ in range(N_ATOMS):
        atoms.append(
            {
                "pos": [
                    random.uniform(50, CANVAS_W - 50),
                    random.uniform(50, CANVAS_H - 50),
                ],
                "color": random.choice(palette),
                "cycle_offset": random.random(),
                "size_jitter": random.uniform(0.7, 1.2),
            }
        )
    return atoms


def render_variant(name: str, palette: list[tuple[int, int, int]], cycle_frames: list[Image.Image]) -> dict[str, str]:
    frame_dir = OUT_DIR / f"frames_{name}"
    frame_dir.mkdir(parents=True, exist_ok=True)
    atoms = init_atoms(palette)

    for fi in range(N_FRAMES):
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        t = fi / FPS
        for atom in atoms:
            pos = atom["pos"]
            assert isinstance(pos, list)
            dx, dy = curl_noise(float(pos[0]), float(pos[1]), t)
            pos[0] = (float(pos[0]) + dx * 1.5) % CANVAS_W
            pos[1] = (float(pos[1]) + dy * 1.5) % CANVAS_H

            cycle_pos = (float(atom["cycle_offset"]) + fi / CYCLE_PERIOD_FRAMES) % 1.0
            sz = int(ATOM_SIZE * float(atom["size_jitter"]))
            color = atom["color"]
            assert isinstance(color, tuple)
            shape = render_atom(cycle_frames, cycle_pos, color, sz)
            paste_x = int(float(pos[0]) - sz / 2)
            paste_y = int(float(pos[1]) - sz / 2)
            canvas.alpha_composite(shape, (paste_x, paste_y))

        canvas.save(frame_dir / f"frame_{fi:04d}.png")

    alpha_mov = OUT_DIR / f"primitive_field_v002_flocking_{name}_alpha_prores4444.mov"
    overlay_black_mp4 = OUT_DIR / f"primitive_field_v002_flocking_{name}_overlay_black.mp4"

    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frame_dir / "frame_%04d.png"),
            "-c:v",
            "prores_ks",
            "-profile:v",
            "4",
            "-pix_fmt",
            "yuva444p10le",
            str(alpha_mov),
        ]
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frame_dir / "frame_%04d.png"),
            "-filter_complex",
            "color=c=black:s=1920x1080:r=24:d=8[bg];[bg][0:v]overlay=shortest=1:format=auto,format=yuv420p",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(overlay_black_mp4),
        ]
    )

    return {
        "frame_dir": str(frame_dir.relative_to(ROOT)),
        "alpha_mov": str(alpha_mov.relative_to(ROOT)),
        "overlay_black_mp4": str(overlay_black_mp4.relative_to(ROOT)),
    }


def make_contact_sheet() -> Path:
    times = [0, 24, 48, 72, 96, 120, 144, 168]
    variants = ["dark_palette", "light_palette"]
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * len(times), thumb_h * len(variants)), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    for row, variant in enumerate(variants):
        for col, frame_idx in enumerate(times):
            frame = Image.open(OUT_DIR / f"frames_{variant}" / f"frame_{frame_idx:04d}.png").convert("RGBA")
            bg = Image.new("RGBA", frame.size, (0, 0, 0, 255))
            bg.alpha_composite(frame)
            thumb = bg.convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
            x, y = col * thumb_w, row * thumb_h
            sheet.paste(thumb, (x, y))
            draw.rectangle((x, y, x + thumb_w, y + 24), fill=(0, 0, 0))
            draw.text((x + 6, y + 5), f"{variant} t={frame_idx / FPS:.1f}s", fill=(230, 230, 220))
    out = OUT_DIR / "primitive_field_v002_flocking_layer_exports_contact_sheet.png"
    sheet.save(out)
    return out


def ffprobe(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate,nb_frames,pix_fmt",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def write_readme(outputs: dict[str, dict[str, str]], contact_sheet: Path) -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# primitive_field_v002_flocking_layer_exports",
                "",
                "INTERNAL / SHOW-DEVELOPMENT ONLY, pending Austin review.",
                "",
                "Clean layer exports from the older `primitive_field_v002_flocking_dark/light` clips.",
                "The originals were baked onto backgrounds and included a small header; these exports",
                "remove the background and header so the primitive field can be mixed over real footage",
                "in Resolume.",
                "",
                "## Outputs",
                "",
                f"- dark-palette alpha: `{outputs['dark_palette']['alpha_mov']}`",
                f"- dark-palette black overlay: `{outputs['dark_palette']['overlay_black_mp4']}`",
                f"- light-palette alpha: `{outputs['light_palette']['alpha_mov']}`",
                f"- light-palette black overlay: `{outputs['light_palette']['overlay_black_mp4']}`",
                f"- contact sheet: `{contact_sheet.relative_to(ROOT)}`",
                "",
                "## Recommended Use",
                "",
                "- Use alpha MOVs as composable foreground/atmospheric layers over footage.",
                "- Use black MP4s with Add/Screen/Lighten if alpha playback is too heavy.",
                "- Treat as ambient primitive grammar, not as a primary Austin-authored artwork reveal.",
                "",
                "## Specs",
                "",
                f"- Resolution: {CANVAS_W}x{CANVAS_H}",
                f"- FPS: {FPS}",
                f"- Duration: {N_FRAMES / FPS:.3f}s",
                "- No Austin source artwork used.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cycle_frames = load_full_cycle_frames()
    outputs = {
        "dark_palette": render_variant("dark_palette", PALETTE_DARK_BG, cycle_frames),
        "light_palette": render_variant("light_palette", PALETTE_LIGHT_BG, cycle_frames),
    }
    contact_sheet = make_contact_sheet()
    write_readme(outputs, contact_sheet)

    manifest = {
        "project": "primitive_field_v002_flocking_layer_exports",
        "date": "2026-05-23",
        "status": "internal/show-development pending Austin review",
        "source_script": "scripts/primitive_field_v2_flocking.py",
        "render_script": "scripts/primitive_field_v002_flocking_layer_exports.py",
        "direct_austin_source_artwork_used": False,
        "resolution": [CANVAS_W, CANVAS_H],
        "fps": FPS,
        "frames": N_FRAMES,
        "duration_seconds": N_FRAMES / FPS,
        "outputs": outputs,
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "ffprobe": {},
    }
    for variant, paths in outputs.items():
        manifest["ffprobe"][variant] = {
            key: ffprobe(ROOT / rel_path)
            for key, rel_path in paths.items()
            if key.endswith("mov") or key.endswith("mp4")
        }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(OUT_DIR)


if __name__ == "__main__":
    main()
