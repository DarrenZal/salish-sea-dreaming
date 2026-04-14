"""v4: match the live exhibition look.

Prav: "too bright — desaturate slightly and make more transparent like in the
actual video experience. Try multiply layers perhaps."

- watercolor desaturated by ~40%, slight brightness reduction
- multiply blend (darkens structure from both layers — filmic/painterly)
- ghost overlay: desaturated watercolor at 40% opacity over photo
- split-multiply: photo | multiply-zone | desat-watercolor
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance, ImageFilter

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "output" / "school-marketing" / "final"
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 1200

MOMENTS = [
    ("H1_salmon_medium",    "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    20),
    ("H1_salmon_cathedral", "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    40),
    ("H1_salmon_dense",     "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    50),
    ("H2_herring_kelp",     "media/hero-subclips/H2_herring_in_kelp.mp4",  "output/H2_herring_in_kelp_production_raft_smooth.mp4",  20),
    ("H3_kelp_cathedral",   "media/hero-subclips/H3_kelp_cathedral.mp4",   "output/H3_kelp_cathedral_production_raft_smooth.mp4",   30),
]


def extract(src, t, out, vf):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(REPO / src),
         "-frames:v", "1", "-vf", vf, str(out)],
        check=True,
    )


def desaturate(img: Image.Image, factor: float = 0.6) -> Image.Image:
    """factor < 1.0 = less saturated. 0.6 = ~40% desaturated."""
    return ImageEnhance.Color(img).enhance(factor)


def split_mask(size: int, horizontal: bool, pure_frac: float = 0.40) -> Image.Image:
    mask = Image.new("L", (size, size))
    pure = int(size * pure_frac)
    start = pure
    end = size - pure
    length = end - start
    pixels = mask.load()
    for i in range(size):
        if i < start:
            v = 0
        elif i >= end:
            v = 255
        else:
            v = int(255 * (i - start) / length)
        for j in range(size):
            if horizontal:
                pixels[i, j] = v
            else:
                pixels[j, i] = v
    return mask.filter(ImageFilter.GaussianBlur(radius=8))


for name, raw_src, lora_src, t in MOMENTS:
    print(f"[{name}] t={t}s")
    photo_path = OUT / f"{name}_photo.jpg"
    water_path = OUT / f"{name}_watercolor.jpg"
    extract(raw_src, t, photo_path,
            f"crop=1020:1020:(iw-1020)/2:30,scale={SIZE}:{SIZE}:flags=lanczos")
    extract(lora_src, t, water_path, f"scale={SIZE}:{SIZE}:flags=lanczos")

    photo = Image.open(photo_path).convert("RGB")
    water = Image.open(water_path).convert("RGB")
    water_desat = desaturate(water, 0.55)  # ~45% desaturation

    # Multiply: darkens, both layers' structure survives (filmic)
    multiply = ImageChops.multiply(photo, water_desat)
    multiply.save(OUT / f"{name}_v4-multiply.jpg", quality=95)

    # Multiply but lean toward photo (50% blend of photo with multiply result)
    multiply_soft = Image.blend(photo, multiply, 0.65)
    multiply_soft.save(OUT / f"{name}_v4-multiply-soft.jpg", quality=95)

    # Ghost overlay: desat watercolor at 40% opacity over photo
    ghost = Image.blend(photo, water_desat, 0.40)
    ghost.save(OUT / f"{name}_v4-ghost.jpg", quality=95)

    # Ghost-light: even more subtle, 25%
    ghost_light = Image.blend(photo, water_desat, 0.25)
    ghost_light.save(OUT / f"{name}_v4-ghost-light.jpg", quality=95)

    # Split-horizontal with desaturated watercolor side + multiply in blend zone
    # Simpler: just use split with desat on right side
    mask_h = split_mask(SIZE, horizontal=True)
    split_h = Image.composite(water_desat, photo, mask_h)
    split_h.save(OUT / f"{name}_v4-split-horizontal.jpg", quality=95)

    mask_v = split_mask(SIZE, horizontal=False)
    split_v = Image.composite(water_desat, photo, mask_v)
    split_v.save(OUT / f"{name}_v4-split-vertical.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
