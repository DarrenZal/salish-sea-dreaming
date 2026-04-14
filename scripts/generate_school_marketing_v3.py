"""v3: compositions where BOTH are unambiguously visible.

- split-horizontal: left 40% pure photo, middle 20% soft blend, right 40% pure watercolor
- split-vertical: top 40% photo, middle 20% blend, bottom 40% watercolor
- diptych: photo | watercolor side-by-side, thin white border
- photo-hero: photo as base, watercolor lightly tinting (ghost dream wash)
- watercolor-hero: watercolor as base, photo ghosted on top (structural overlay)
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageFilter

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


def split_mask(size: int, horizontal: bool, pure_frac: float = 0.40) -> Image.Image:
    """Pure photo on first side, pure watercolor on opposite side, gradient between.
    pure_frac = fraction of each side that stays pure (not blended)."""
    mask = Image.new("L", (size, size))
    pure = int(size * pure_frac)
    blend_start = pure
    blend_end = size - pure
    blend_len = blend_end - blend_start
    pixels = mask.load()
    for i in range(size):
        if horizontal:
            if i < blend_start:
                v = 0
            elif i >= blend_end:
                v = 255
            else:
                v = int(255 * (i - blend_start) / blend_len)
            for j in range(size):
                pixels[i, j] = v
        else:
            if i < blend_start:
                v = 0
            elif i >= blend_end:
                v = 255
            else:
                v = int(255 * (i - blend_start) / blend_len)
            for j in range(size):
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

    # Split horizontal: left 40% photo | middle 20% blend | right 40% watercolor
    Image.composite(water, photo, split_mask(SIZE, horizontal=True)).save(
        OUT / f"{name}_split-horizontal.jpg", quality=95)

    # Split vertical: top 40% photo | middle 20% blend | bottom 40% watercolor
    Image.composite(water, photo, split_mask(SIZE, horizontal=False)).save(
        OUT / f"{name}_split-vertical.jpg", quality=95)

    # Diptych: photo | watercolor side-by-side (landscape 2:1)
    half = SIZE // 2
    dip = Image.new("RGB", (SIZE + 20, half + 20), "white")
    dip.paste(photo.resize((half, half), Image.LANCZOS), (10, 10))
    dip.paste(water.resize((half, half), Image.LANCZOS), (10 + half, 10))
    dip.save(OUT / f"{name}_diptych.jpg", quality=95)

    # Photo-hero: photo as base, watercolor ghosted on top at 30% opacity
    photo_hero = Image.blend(photo, water, 0.30)
    photo_hero.save(OUT / f"{name}_photo-hero.jpg", quality=95)

    # Watercolor-hero: watercolor base, photo ghosted at 30% for structure
    water_hero = Image.blend(water, photo, 0.30)
    water_hero.save(OUT / f"{name}_watercolor-hero.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
