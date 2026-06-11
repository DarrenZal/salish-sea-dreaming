#!/usr/bin/env python3
"""
Build one deterministic wide-wall MVP loop for Pravin.

One clean version only:
  - H6 kelp 4K background
  - primitive field dark as low-opacity ambient grammar
  - Cosmic -> Salmon v006 as one large centered hero insert
"""
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/wide_wall_mvp_loop_v001"
OUT_MP4 = OUT_DIR / "wide_wall_mvp_loop_v001_3840x2160_20sec.mp4"

H6 = ROOT / "media/hero-subclips/H6_kelp_forest_floor_4k.mp4"
PRIMITIVE_DARK = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4"
HERO = ROOT / "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4"


def run(cmd: list[str]) -> None:
    print(" ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def render_loop() -> None:
    filter_complex = (
        "[0:v]fps=24,scale=3840:2160:force_original_aspect_ratio=increase,"
        "crop=3840:2160,trim=duration=20,setpts=PTS-STARTPTS,"
        "eq=saturation=0.78:contrast=0.96:brightness=-0.035[bg];"
        "[1:v]fps=24,scale=3840:2160:force_original_aspect_ratio=increase,"
        "crop=3840:2160,trim=duration=20,setpts=PTS-STARTPTS[prim];"
        "[2:v]fps=24,split[hero_f][hero_r];"
        "[hero_r]reverse[hero_rev];"
        "[hero_f][hero_rev]concat=n=2:v=1:a=0,setpts=PTS-STARTPTS[hero10];"
        "[hero10]loop=loop=1:size=240:start=0,trim=duration=20,setpts=PTS-STARTPTS,"
        "scale=1440:1440:flags=lanczos[hero];"
        "[bg][prim]blend=all_mode=screen:all_opacity=0.16[base];"
        "[base]drawbox=x=1168:y=328:w=1504:h=1504:color=black@0.22:t=fill[matte];"
        "[matte][hero]overlay=x=(W-w)/2:y=(H-h)/2:format=auto,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "8", "-t", "20", "-i", H6,
        "-stream_loop", "-1", "-i", PRIMITIVE_DARK,
        "-i", HERO,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-an",
        "-frames:v", "480",
        "-r", "24",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        OUT_MP4,
    ])


def write_readme() -> None:
    readme = OUT_DIR / "README.md"
    readme.write_text(f"""# Wide Wall MVP Loop v001

One deterministic 20-second review loop for Pravin's stable-palette /
production-floor composition discussion.

## Output

- `track2-deterministic/morph_outputs_INTERNAL/wide_wall_mvp_loop_v001/wide_wall_mvp_loop_v001_3840x2160_20sec.mp4`
- 3840x2160
- 24fps
- 20 seconds / 480 frames
- H.264 review encode

## Sources

- Background: `media/hero-subclips/H6_kelp_forest_floor_4k.mp4`
- Ambient grammar layer: `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4`
- Center hero insert: `track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4`

## Algorithm

1. Use H6 Kelp 4K as a full-frame 3840x2160 background, slightly darkened and
   desaturated for projection-style headroom.
2. Screen-blend the dark primitive field across the whole wall at 16% opacity.
3. Build a 20-second center insert from Cosmic -> Salmon v006 by playing the
   5-second clip forward then backward, repeated twice. This avoids a hard
   Salmon-to-Cosmic reset inside the review loop.
4. Place the insert centered at 1440x1440 over a subtle dark matte so the
   artwork remains large and legible.

## Caveats

- INTERNAL REVIEW ONLY. Austin per-output OK required before audience-facing use
  because the center insert uses Austin-derived artwork.
- This is not a new morph experiment. It is a compositing proof of the
  production-floor stack: H6 background + primitive-field layer + one hero
  insert.
- H.264 review version only, not a final Resolume alpha/multi-layer export.
- Primitive field is abstract/low-load; Cosmic -> Salmon v006 remains an
  Austin-review hero candidate, not approved show content.
""")


def append_provenance() -> None:
    provenance = ROOT / "track2-deterministic/morph_outputs_INTERNAL/provenance.csv"
    line = (
        '2026-05-18,wide_wall_mvp_loop_v001,'
        'H6_kelp_forest_floor_4k.mp4 + primitive_field_v002_flocking_dark.mp4,'
        'cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4,'
        'medium,internal-only,'
        '"Deterministic 3840x2160 20-second wide-wall MVP composition proof for Pravin. '
        'Uses H6 Kelp as full background, primitive field dark at low-opacity screen blend, '
        'and one large centered Cosmic -> Salmon v006 hero insert with ping-pong timing. '
        'No SD/LoRA/prompt generation/new morph variants. Austin per-output OK required for the Austin-derived insert."\n'
    )
    with provenance.open("a") as f:
        f.write(line)


def main() -> None:
    if OUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing output folder: {OUT_DIR}")
    for src in (H6, PRIMITIVE_DARK, HERO):
        if not src.exists():
            raise FileNotFoundError(src)
    OUT_DIR.mkdir(parents=True)
    render_loop()
    write_readme()
    append_provenance()
    print(OUT_MP4.relative_to(ROOT))
    print((OUT_DIR / "README.md").relative_to(ROOT))


if __name__ == "__main__":
    main()
