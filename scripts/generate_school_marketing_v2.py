"""Generate marketing images with real-and-imaginary blending.

v2: adds gradient-mask fades (horizontal, vertical, radial) + screen composite.
The goal is compositions where BOTH the photo and the watercolor are clearly
visible, fading into each other — not a linear average where one dominates.

Output: output/school-marketing/final/
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

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


def extract(src: str, t: int, out_path: Path, vf: str) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(REPO / src),
         "-frames:v", "1", "-vf", vf, str(out_path)],
        check=True,
    )


def gradient_mask_horizontal(size: int, reverse: bool = False) -> Image.Image:
    """Linear L→R mask: black on left (photo shows), white on right (watercolor shows)."""
    mask = Image.new("L", (size, size))
    for x in range(size):
        v = int(255 * x / (size - 1))
        if reverse:
            v = 255 - v
        for y in range(size):
            mask.putpixel((x, y), v)
    return mask


def gradient_mask_vertical(size: int, reverse: bool = False) -> Image.Image:
    """Top→bottom: photo at top, watercolor bleeds up from below."""
    mask = Image.new("L", (size, size))
    for y in range(size):
        v = int(255 * y / (size - 1))
        if reverse:
            v = 255 - v
        for x in range(size):
            mask.putpixel((x, y), v)
    return mask


def gradient_mask_radial(size: int) -> Image.Image:
    """Center = photo (focal subject), edges = watercolor dream."""
    mask = Image.new("L", (size, size))
    cx = cy = size / 2
    max_r = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(size):
        for x in range(size):
            r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            v = int(255 * r / max_r)
            mask.putpixel((x, y), v)
    return mask.filter(ImageFilter.GaussianBlur(radius=40))


for name, raw_src, lora_src, t in MOMENTS:
    print(f"[{name}] t={t}s")
    raw_path = OUT / f"{name}_photo.jpg"
    lora_path = OUT / f"{name}_watercolor.jpg"

    # Already extracted in v1, but re-run to be safe
    extract(raw_src, t, raw_path,
            f"crop=1020:1020:(iw-1020)/2:30,scale={SIZE}:{SIZE}:flags=lanczos")
    extract(lora_src, t, lora_path, f"scale={SIZE}:{SIZE}:flags=lanczos")

    photo = Image.open(raw_path).convert("RGB")
    water = Image.open(lora_path).convert("RGB")

    # Horizontal fade: photo on LEFT, watercolor fades in from RIGHT
    mask_h = gradient_mask_horizontal(SIZE)
    fade_h = Image.composite(water, photo, mask_h)
    fade_h.save(OUT / f"{name}_fade-horizontal.jpg", quality=95)

    # Vertical fade: photo on TOP, watercolor dreams up from BOTTOM
    mask_v = gradient_mask_vertical(SIZE)
    fade_v = Image.composite(water, photo, mask_v)
    fade_v.save(OUT / f"{name}_fade-vertical.jpg", quality=95)

    # Radial: photo in CENTER (focal subject), watercolor on edges
    mask_r = gradient_mask_radial(SIZE)
    fade_r = Image.composite(water, photo, mask_r)
    fade_r.save(OUT / f"{name}_fade-radial.jpg", quality=95)

    # Screen blend: preserves highlights from both, classic double-exposure
    #   screen(a,b) = 255 - ((255-a)*(255-b))/255
    screen = ImageChops.screen(photo, water)
    screen.save(OUT / f"{name}_screen.jpg", quality=95)

    # Lighten: max(a, b) per channel — similar but sharper
    lighten = ImageChops.lighter(photo, water)
    lighten.save(OUT / f"{name}_lighten.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
