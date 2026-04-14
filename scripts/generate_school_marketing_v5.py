"""v5 experiments: genuinely different techniques.

1. luminosity   — photo's lightness + watercolor's colors (HSL "color" blend)
2. freq-sep     — photo's high-freq detail + watercolor's low-freq color field
3. color-match  — histogram-match photo to watercolor palette, then multiply
4. edge-sketch  — extract photo edges as ink lines, overlay on watercolor
5. desat-base   — desat photo as base + watercolor ghost on top (inverse approach)
"""
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageEnhance
import colorsys

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


def rgb_to_hls_arr(rgb: np.ndarray) -> np.ndarray:
    """rgb [H,W,3] float [0,1] -> hls [H,W,3] float."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    l = (maxc + minc) / 2
    d = maxc - minc
    s = np.where(d == 0, 0, np.where(l < 0.5, d / (maxc + minc + 1e-9), d / (2 - maxc - minc + 1e-9)))
    rc = np.where(d == 0, 0, (maxc - r) / (d + 1e-9))
    gc = np.where(d == 0, 0, (maxc - g) / (d + 1e-9))
    bc = np.where(d == 0, 0, (maxc - b) / (d + 1e-9))
    h = np.where(r == maxc, bc - gc,
        np.where(g == maxc, 2 + rc - bc, 4 + gc - rc))
    h = (h / 6) % 1.0
    return np.stack([h, l, s], axis=-1)


def hls_to_rgb_arr(hls: np.ndarray) -> np.ndarray:
    h, l, s = hls[..., 0], hls[..., 1], hls[..., 2]
    def _v(m1, m2, hue):
        hue = hue % 1.0
        return np.where(hue < 1/6, m1 + (m2 - m1) * 6 * hue,
               np.where(hue < 0.5, m2,
               np.where(hue < 2/3, m1 + (m2 - m1) * (2/3 - hue) * 6, m1)))
    m2 = np.where(l < 0.5, l * (1 + s), l + s - l * s)
    m1 = 2 * l - m2
    r = np.where(s == 0, l, _v(m1, m2, h + 1/3))
    g = np.where(s == 0, l, _v(m1, m2, h))
    b = np.where(s == 0, l, _v(m1, m2, h - 1/3))
    return np.stack([r, g, b], axis=-1)


def luminosity_blend(photo: Image.Image, water: Image.Image) -> Image.Image:
    """Photo's lightness (structure) + watercolor's hue and saturation (color)."""
    p = np.asarray(photo, dtype=np.float32) / 255
    w = np.asarray(water, dtype=np.float32) / 255
    p_hls = rgb_to_hls_arr(p)
    w_hls = rgb_to_hls_arr(w)
    # Keep H and S from watercolor, L from photo
    out_hls = np.stack([w_hls[..., 0], p_hls[..., 1], w_hls[..., 2]], axis=-1)
    out_rgb = hls_to_rgb_arr(out_hls)
    return Image.fromarray(np.clip(out_rgb * 255, 0, 255).astype(np.uint8))


def frequency_separation(photo: Image.Image, water: Image.Image, radius: int = 25) -> Image.Image:
    """Photo's high-freq detail + watercolor's low-freq color field."""
    p = np.asarray(photo, dtype=np.float32)
    w = np.asarray(water, dtype=np.float32)
    w_blur = np.asarray(water.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    p_blur = np.asarray(photo.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)
    p_high = p - p_blur  # photo's high-frequency (zero-centered)
    # Combine watercolor's low-freq color with photo's high-freq detail
    out = w_blur + p_high
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def histogram_match(source: Image.Image, template: Image.Image) -> Image.Image:
    """Match source's histogram (per-channel) to template's."""
    s = np.asarray(source)
    t = np.asarray(template)
    matched = np.zeros_like(s)
    for c in range(3):
        s_c = s[..., c].ravel()
        t_c = t[..., c].ravel()
        s_vals, s_idx, s_counts = np.unique(s_c, return_inverse=True, return_counts=True)
        t_vals, t_counts = np.unique(t_c, return_counts=True)
        s_cdf = np.cumsum(s_counts).astype(np.float64) / s_c.size
        t_cdf = np.cumsum(t_counts).astype(np.float64) / t_c.size
        interp = np.interp(s_cdf, t_cdf, t_vals)
        matched[..., c] = interp[s_idx].reshape(s[..., c].shape)
    return Image.fromarray(matched.astype(np.uint8))


def color_match_then_multiply(photo: Image.Image, water: Image.Image) -> Image.Image:
    """Harmonize photo to watercolor palette first, then multiply."""
    photo_matched = histogram_match(photo, water)
    blend = Image.blend(photo_matched, water, 0.40)
    return blend


def edge_sketch_overlay(photo: Image.Image, water: Image.Image, strength: float = 0.55) -> Image.Image:
    """Extract photo edges as dark ink lines, overlay on watercolor."""
    gray = photo.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    # Invert so edges are dark on light, then boost contrast
    edges = ImageChops.invert(edges)
    edges = ImageEnhance.Contrast(edges).enhance(1.6)
    # Threshold softly: push mid-grays toward white
    e = np.asarray(edges, dtype=np.float32)
    e = np.clip((e - 100) * 2.5 + 220, 0, 255).astype(np.uint8)
    edges = Image.fromarray(e).convert("RGB")
    # Multiply edges over watercolor (dark lines darken, light areas pass-through)
    ink = ImageChops.multiply(water, edges)
    return Image.blend(water, ink, strength)


def desaturated_base(photo: Image.Image, water: Image.Image, water_opacity: float = 0.55) -> Image.Image:
    """Desaturated photo as base + colorful watercolor ghost on top."""
    photo_desat = ImageEnhance.Color(photo).enhance(0.35)
    photo_desat = ImageEnhance.Brightness(photo_desat).enhance(1.05)
    return Image.blend(photo_desat, water, water_opacity)


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

    luminosity_blend(photo, water).save(OUT / f"{name}_v5-luminosity.jpg", quality=95)
    frequency_separation(photo, water).save(OUT / f"{name}_v5-freq-sep.jpg", quality=95)
    color_match_then_multiply(photo, water).save(OUT / f"{name}_v5-color-match.jpg", quality=95)
    edge_sketch_overlay(photo, water).save(OUT / f"{name}_v5-edge-sketch.jpg", quality=95)
    desaturated_base(photo, water).save(OUT / f"{name}_v5-desat-base.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
