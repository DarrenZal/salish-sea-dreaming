"""v6: side-to-side fades with Prav's feedback applied.

- watercolor desaturated ~45%
- on the "watercolor side" of the split, it's multiply(photo, desat_water)
  so photo structure survives and the watercolor acts as a color/line overlay
  rather than a full replacement
- continuous gradient-overlay variant: photo everywhere, watercolor opacity
  ramps smoothly (no split) — closest to the live video experience
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

DESAT_FACTOR = 0.55        # watercolor saturation (1.0 = unchanged, 0 = grayscale)
MULTIPLY_BLEND_INTO_PHOTO = 0.65  # how much of the multiply result shows on the "stylized" side


def extract(src, t, out, vf):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(REPO / src),
         "-frames:v", "1", "-vf", vf, str(out)],
        check=True,
    )


def desaturate(img, factor=DESAT_FACTOR):
    return ImageEnhance.Color(img).enhance(factor)


def split_mask(size, horizontal, pure_frac=0.35):
    mask = Image.new("L", (size, size))
    pure = int(size * pure_frac)
    start, end = pure, size - pure
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
    return mask.filter(ImageFilter.GaussianBlur(radius=12))


def gradient_opacity_mask(size, horizontal, start_opacity=0.0, end_opacity=0.60):
    """Smooth opacity ramp across full frame (no pure-photo pure-watercolor zones)."""
    mask = Image.new("L", (size, size))
    pixels = mask.load()
    for i in range(size):
        t = i / (size - 1)
        opacity = start_opacity + (end_opacity - start_opacity) * t
        v = int(255 * opacity)
        for j in range(size):
            if horizontal:
                pixels[i, j] = v
            else:
                pixels[j, i] = v
    return mask


for name, raw_src, lora_src, t in MOMENTS:
    print(f"[{name}] t={t}s")
    photo_path = OUT / f"{name}_photo.jpg"
    water_path = OUT / f"{name}_watercolor.jpg"
    if not photo_path.exists():
        extract(raw_src, t, photo_path,
                f"crop=1020:1020:(iw-1020)/2:30,scale={SIZE}:{SIZE}:flags=lanczos")
    if not water_path.exists():
        extract(lora_src, t, water_path, f"scale={SIZE}:{SIZE}:flags=lanczos")

    photo = Image.open(photo_path).convert("RGB")
    water = Image.open(water_path).convert("RGB")
    water_desat = desaturate(water)

    # "Stylized" side = photo with desaturated watercolor multiplied over it, blended back into photo
    stylized = ImageChops.multiply(photo, water_desat)
    stylized = Image.blend(photo, stylized, MULTIPLY_BLEND_INTO_PHOTO)

    # Split-multiply-horizontal: pure photo left → blend → photo-with-watercolor-treatment right
    Image.composite(stylized, photo, split_mask(SIZE, horizontal=True)).save(
        OUT / f"{name}_v6-split-h-multiply.jpg", quality=95)
    Image.composite(stylized, photo, split_mask(SIZE, horizontal=False)).save(
        OUT / f"{name}_v6-split-v-multiply.jpg", quality=95)

    # Gradient-overlay: photo everywhere, watercolor opacity smoothly ramps 0→60%
    grad_h = gradient_opacity_mask(SIZE, horizontal=True)
    grad_v = gradient_opacity_mask(SIZE, horizontal=False)
    Image.composite(water_desat, photo, grad_h).save(
        OUT / f"{name}_v6-gradient-h.jpg", quality=95)
    Image.composite(water_desat, photo, grad_v).save(
        OUT / f"{name}_v6-gradient-v.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
