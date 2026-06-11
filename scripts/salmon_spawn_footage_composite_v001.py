#!/usr/bin/env python3
"""
Deterministic Salmon Spawn Eggs + underwater footage compositing test.

No SD, LoRA, prompt generation, or geometry morphing. Austin geometry is rendered
from the approved SVG, with only the full-canvas low-opacity background rectangle
omitted for compositing.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/salmon_spawn_footage_composite_v001"

SVG_SRC = ROOT / "austin-v2-ingest/approved/Animal_Salmon_Spawn_Eggs.svg"
H1 = ROOT / "media/hero-subclips/H1_salmon_school.mp4"
H6 = ROOT / "media/hero-subclips/H6_kelp_forest_floor_4k.mp4"
H7 = ROOT / "media/hero-subclips/H7_spawn_feast.mp4"

W, H = 1920, 1080
FPS = 24
DURATION = 10
ART_SIZE = 940
ART_POS = ((W - ART_SIZE) // 2, (H - ART_SIZE) // 2)


def run(cmd: list[str]) -> None:
    print(" ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def strip_full_canvas_background_rect() -> Path:
    """Write a derived SVG with the Layer_3 background rect removed."""
    text = SVG_SRC.read_text()
    stripped = re.sub(
        r"\s*<g id=\"Layer_3\" data-name=\"Layer 3\">\s*<rect class=\"cls-13\"[^>]*/>\s*</g>\s*",
        "\n  ",
        text,
        count=1,
    )
    if stripped == text:
        raise RuntimeError("Expected to remove Layer_3 background rect, but no match was found.")
    derived = OUT_DIR / "Animal_Salmon_Spawn_Eggs_no_full_canvas_tint.svg"
    derived.write_text(stripped)
    return derived


def render_svg(svg_path: Path) -> Path:
    render_path = OUT_DIR / "Animal_Salmon_Spawn_Eggs_no_full_canvas_tint_1500.png"
    run([
        "magick",
        "-background",
        "none",
        "-density",
        "192",
        svg_path,
        "-resize",
        "1500x1500",
        render_path,
    ])
    return render_path


def multiply_alpha(img: Image.Image, factor: float) -> Image.Image:
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    a = a.point(lambda x: int(max(0, min(255, round(x * factor)))))
    return Image.merge("RGBA", (r, g, b, a))


def make_full_frame_assets(render_path: Path) -> dict[str, Path]:
    art = Image.open(render_path).convert("RGBA")
    art = art.resize((ART_SIZE, ART_SIZE), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay.alpha_composite(multiply_alpha(art, 0.88), ART_POS)
    overlay_path = OUT_DIR / "salmon_spawn_overlay_full_frame_rgba.png"
    overlay.save(overlay_path)

    mask = Image.new("L", (W, H), 0)
    alpha = art.getchannel("A")
    mask.paste(alpha, ART_POS)
    # A very small close smooths anti-aliased gaps without changing placement.
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    mask_path = OUT_DIR / "salmon_spawn_mask_full_frame_luma.png"
    mask.save(mask_path)

    outline = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    outline.alpha_composite(multiply_alpha(art, 0.34), ART_POS)
    outline_path = OUT_DIR / "salmon_spawn_mask_outline_reference_rgba.png"
    outline.save(outline_path)

    # Diagnostic still: the intact approved-SVG-derived geometry over neutral bg.
    neutral = Image.new("RGBA", (W, H), (245, 240, 232, 255))
    neutral.alpha_composite(overlay)
    neutral.convert("RGB").save(OUT_DIR / "salmon_spawn_overlay_asset_check.jpg", quality=92)

    return {
        "overlay": overlay_path,
        "mask": mask_path,
        "outline": outline_path,
    }


def render_overlay_clip(assets: dict[str, Path]) -> Path:
    out = OUT_DIR / "01_salmon_spawn_over_h1_salmon_school_overlay_v001.mp4"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "8", "-t", str(DURATION), "-i", H1,
        "-loop", "1", "-t", str(DURATION), "-i", assets["overlay"],
        "-filter_complex",
        (
            "[0:v]fps=24,scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,eq=saturation=0.82:contrast=0.96:brightness=-0.015,format=rgba[bg];"
            "[1:v]format=rgba[art];"
            "[bg][art]overlay=0:0:format=auto,format=yuv420p[v]"
        ),
        "-map", "[v]", "-an", "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
        out,
    ])
    return out


def render_mask_clip(assets: dict[str, Path]) -> Path:
    out = OUT_DIR / "02_salmon_spawn_h6_kelp_inside_forms_mask_window_v001.mp4"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "6", "-t", str(DURATION), "-i", H6,
        "-loop", "1", "-t", str(DURATION), "-i", assets["mask"],
        "-loop", "1", "-t", str(DURATION), "-i", assets["outline"],
        "-filter_complex",
        (
            "color=c=0xf5f0e8:s=1920x1080:r=24:d=10[base];"
            "[0:v]fps=24,scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,eq=saturation=0.9:contrast=1.04:brightness=-0.01,format=rgba[fg];"
            "[1:v]format=gray[mask];"
            "[fg][mask]alphamerge[win];"
            "[base][win]overlay=0:0:format=auto[tmp];"
            "[2:v]format=rgba[line];"
            "[tmp][line]overlay=0:0:format=auto,format=yuv420p[v]"
        ),
        "-map", "[v]", "-an", "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
        out,
    ])
    return out


def render_comparison_clip(overlay_clip: Path, mask_clip: Path) -> Path:
    out = OUT_DIR / "03_salmon_spawn_footage_overlay_mask_3up_comparison_v001.mp4"
    filter_complex = (
        "[0:v]fps=24,scale=640:360:force_original_aspect_ratio=increase,crop=640:360,"
        "pad=640:1080:0:360:color=0xf5f0e8,"
        "drawtext=text='SOURCE H1':x=(w-text_w)/2:y=315:fontsize=28:fontcolor=0x40352d[a];"
        "[1:v]fps=24,scale=640:360:force_original_aspect_ratio=increase,crop=640:360,"
        "pad=640:1080:0:360:color=0xf5f0e8,"
        "drawtext=text='AUSTIN OVERLAY':x=(w-text_w)/2:y=315:fontsize=28:fontcolor=0x40352d[b];"
        "[2:v]fps=24,scale=640:360:force_original_aspect_ratio=increase,crop=640:360,"
        "pad=640:1080:0:360:color=0xf5f0e8,"
        "drawtext=text='MASK WINDOW H6':x=(w-text_w)/2:y=315:fontsize=28:fontcolor=0x40352d[c];"
        "[a][b][c]hstack=inputs=3,format=yuv420p[v]"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "8", "-t", str(DURATION), "-i", H1,
        "-i", overlay_clip,
        "-i", mask_clip,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-an", "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
        out,
    ])
    return out


def render_contact_sheet(clips: list[Path]) -> Path:
    sheet = OUT_DIR / "salmon_spawn_footage_composite_v001_contact_sheet.jpg"
    tmp = OUT_DIR / "_contact_sheet_inputs"
    tmp.mkdir(exist_ok=True)
    stills = []
    for i, clip in enumerate(clips, 1):
        still = tmp / f"{i:02d}.jpg"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", "5", "-i", clip, "-vframes", "1",
            "-vf", "scale=640:360:force_original_aspect_ratio=increase,crop=640:360",
            still,
        ])
        stills.append(still)
    run([
        "magick",
        stills[0], stills[1], stills[2],
        "+append",
        sheet,
    ])
    return sheet


def write_readme(clips: list[Path], sheet: Path) -> None:
    rel = lambda p: p.relative_to(ROOT)
    readme = OUT_DIR / "README.md"
    readme.write_text(f"""# Salmon Spawn Eggs + Underwater Footage Composite v001

Internal deterministic compositing test for whether Austin's
`Animal_Salmon_Spawn_Eggs` can behave as stable, composable Resolume material
over real underwater footage.

## Cultural Status

INTERNAL ONLY. Austin per-output OK required before any public, staged, or
audience-facing use.

## Source Files

- Austin source SVG: `{rel(SVG_SRC)}`
- Overlay footage: `{rel(H1)}`
- Mask/window footage: `{rel(H6)}`
- Additional candidate inspected but not used in v001: `{rel(H7)}`

## Outputs

- Overlay clip: `{rel(clips[0])}`
- Mask/window clip: `{rel(clips[1])}`
- 3-up comparison clip: `{rel(clips[2])}`
- Contact sheet: `{rel(sheet)}`

All MP4s are 1920x1080, 24fps, 10 seconds, H.264.

## Algorithm

1. Copy the approved Salmon Spawn Eggs SVG into this output folder as a derived
   working SVG and remove only the full-canvas low-opacity background rectangle
   (`Layer_3`). The salmon, roe, linework, and internal geometry remain in the
   same positions.
2. Render the derived SVG with ImageMagick on a transparent background.
3. Build a centered full-frame transparent overlay asset from the rendered SVG.
4. Build a luma mask from the rendered SVG alpha channel.
5. Render three deterministic ffmpeg composites:
   - H1 salmon-school footage with the Austin salmon/roe geometry overlaid.
   - H6 kelp footage visible only inside the Austin salmon/roe geometry, with
     a faint reference overlay to keep the original graphic readable.
   - A 3-up comparison: source H1 footage, overlay result, mask/window result.

No SD, LoRA, prompt generation, frame interpolation, or free-swimming puppet work
is used.

## Known Limitations

- This is a flat 2D compositing test. The Austin salmon do not swim or deform.
- MP4/H.264 has no alpha channel, so these are review composites rather than
  final transparent Resolume alpha assets.
- The full-canvas SVG tint rectangle is intentionally omitted for composability;
  if Austin considers that field integral, a separate intact-background variant
  should be tested.
- The mask/window version uses alpha from the graphic forms, not hand-authored
  semantic body masks.

## Read

This is useful if Pravin wants stable palette, composable production material:
it keeps Austin's geometry intact and tests whether real footage can supply
motion/texture without inventing new imagery.
""")


def append_provenance(clips: list[Path]) -> None:
    provenance = ROOT / "track2-deterministic/morph_outputs_INTERNAL/provenance.csv"
    line = (
        '2026-05-18,salmon_spawn_footage_composite_v001,'
        'Animal_Salmon_Spawn_Eggs.svg,'
        'H1_salmon_school.mp4 + H6_kelp_forest_floor_4k.mp4,'
        'medium,internal-only,'
        '"Deterministic no-AI compositing test for stable Resolume material. '
        'Renders approved Salmon Spawn Eggs SVG with full-canvas tint layer omitted for composability; '
        'produces overlay, mask/window, and 3-up comparison MP4s over real underwater footage. '
        'No SD/LoRA/prompt generation/free-swimming puppet work. Austin geometry remains fixed; '
        'Austin per-output OK required."\n'
    )
    with provenance.open("a") as f:
        f.write(line)


def main() -> None:
    if OUT_DIR.exists():
        raise SystemExit(f"Refusing to overwrite existing output folder: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True)

    for path in (SVG_SRC, H1, H6, H7):
        if not path.exists():
            raise FileNotFoundError(path)

    working_svg = strip_full_canvas_background_rect()
    render_path = render_svg(working_svg)
    assets = make_full_frame_assets(render_path)
    overlay = render_overlay_clip(assets)
    mask = render_mask_clip(assets)
    comparison = render_comparison_clip(overlay, mask)
    sheet = render_contact_sheet([overlay, mask, comparison])
    write_readme([overlay, mask, comparison], sheet)
    append_provenance([overlay, mask, comparison])

    print("\nOutputs:")
    for p in (overlay, mask, comparison, sheet, OUT_DIR / "README.md"):
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
