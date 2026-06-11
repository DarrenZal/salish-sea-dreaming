"""
Non-AI pearl triptych mock — pure PIL/numpy procedural.

Builds one continuous 3840×1080 "pearl interior" canvas (one virtual scene,
nacre gradient + particle current + center focal opening), then slices into
three 1920×1080 panels. Demonstrates the spherical-first authoring recipe
without any AI / 3D engine / GPU dependency.

Outputs:
  pearl-triptych-mock/00_full_continuous_3840x1080.png
  pearl-triptych-mock/01_left_panel_1920x1080.png
  pearl-triptych-mock/02_center_panel_1920x1080.png
  pearl-triptych-mock/03_right_panel_1920x1080.png
  pearl-triptych-mock/seam_check_overlay.png   (shows where seams fall)

Per `docs/space-center/pearl-triptych-mock-spec.md`:
  - Background: nacreous gradient (warm white → mother-of-pearl → deep blue at base)
  - Midground: slow spiral particle current
  - Foreground: center focal opening (placeholder for Austin's three shapes)
  - Low-information seams: ±100px from each panel boundary kept low-detail
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path.home() / "projects/salish-sea-dreaming/austin-reference/pearl-triptych-mock"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(42)
np.random.seed(42)

W, H = 3840, 1080
PANEL_W = 1920


def lerp(a, b, t):
    return a + (b - a) * t


def nacre_gradient_canvas() -> Image.Image:
    """Background: warm-white → mother-of-pearl iridescent → deep blue at base.
    Radial-ish from upper-center, slowly bluer toward bottom + edges."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    cx, cy = W // 2, int(H * 0.35)
    max_d = math.hypot(W, H)
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy) / max_d
            # Vertical bias: bluer toward bottom
            v = y / H
            # Iridescent oscillation
            theta = (x / W) * math.pi * 4
            irid = 0.05 * math.sin(theta + v * math.pi * 2)
            r = int(lerp(255, lerp(180, 50, v), d) + irid * 255)
            g = int(lerp(245, lerp(170, 70, v), d) + irid * 200)
            b = int(lerp(240, lerp(200, 130, v), d) + irid * 100)
            px[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    # Soften
    img = img.filter(ImageFilter.GaussianBlur(radius=4))
    return img


def particle_current(canvas: Image.Image) -> Image.Image:
    """Spiral particle current traversing the volume. Particles tinted in
    Austin's working palette (red / black / gold). Distributed across full
    3840 width so the current crosses panel seams smoothly."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # Parametric spiral path that traverses the wide canvas
    n_particles = 1200
    palette = [(170, 30, 35, 130), (20, 20, 25, 120), (210, 165, 50, 130),
               (60, 80, 130, 110), (240, 240, 240, 150)]
    for i in range(n_particles):
        # Parametric position along a sinuous current
        t = i / n_particles
        # Wide horizontal arc with slow vertical drift
        x = int(t * W * 1.05 - W * 0.025)  # slight overscan
        y = int(H * 0.55 + 0.32 * H * math.sin(t * math.pi * 3.5)
                + random.uniform(-30, 30))
        if not (0 <= x < W and 0 <= y < H):
            continue
        # Particle size + color
        size = random.choice([1, 1, 1, 2, 2, 3, 4])
        col = random.choice(palette)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=col)
    # Slight motion blur on the current
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1))
    composited = canvas.convert("RGBA")
    composited.alpha_composite(overlay)
    return composited.convert("RGB")


def center_focal_opening(canvas: Image.Image) -> Image.Image:
    """Foreground placeholder for Austin's three shapes. A subtle inner
    pearl-within-pearl with three faint primitive silhouettes (placeholder
    for crescent / ovoid / U-form). Lives in the CENTER panel only — does
    not cross seams."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = W // 2, H // 2
    inner_r = 220
    # Inner pearl glow
    for r in range(inner_r, inner_r - 80, -3):
        a = int(60 * (1 - (inner_r - r) / 80))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(255, 245, 230, a), width=2)
    # Three primitive silhouettes (placeholder)
    # 1. Crescent — top
    for k in range(80):
        ang = math.radians(220 + k * 1.5)
        x = cx + int(140 * math.cos(ang))
        y = cy - 120 + int(140 * math.sin(ang))
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(20, 20, 30, 180))
    # 2. Ovoid — center
    draw.ellipse([cx - 70, cy - 30, cx + 70, cy + 50], fill=(170, 30, 35, 200))
    draw.ellipse([cx - 30, cy - 12, cx + 30, cy + 18], fill=(240, 240, 240, 220))
    # 3. U-form — bottom
    for k in range(120):
        ang = math.radians(180 + k * 1.5)
        x = cx + int(80 * math.cos(ang))
        y = cy + 120 + int(60 * math.sin(ang))
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(210, 165, 50, 200))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
    composited = canvas.convert("RGBA")
    composited.alpha_composite(overlay)
    return composited.convert("RGB")


def darken_seam_zones(canvas: Image.Image, seam_width: int = 100) -> Image.Image:
    """Per spec: ±100px around panel boundaries should be low-information.
    Slightly fade the gradient at seam zones (gentle vignette per seam)."""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for seam_x in [PANEL_W, 2 * PANEL_W]:
        for dx in range(-seam_width, seam_width + 1):
            x = seam_x + dx
            if not (0 <= x < W):
                continue
            # Gaussian-ish darkening, peak at seam
            falloff = math.exp(-(dx ** 2) / (seam_width * 0.5) ** 2)
            alpha = int(60 * falloff)
            draw.line([(x, 0), (x, H)], fill=(0, 0, 30, alpha))
    composited = canvas.convert("RGBA")
    composited.alpha_composite(overlay)
    return composited.convert("RGB")


print("Building pearl interior continuous canvas (3840x1080)…", flush=True)
canvas = nacre_gradient_canvas()
canvas = particle_current(canvas)
canvas = center_focal_opening(canvas)
canvas = darken_seam_zones(canvas)

full = OUT / "00_full_continuous_3840x1080.png"
canvas.save(full, "PNG", optimize=True)
print(f"  saved: {full.name}  ({full.stat().st_size // 1024} KB)")

# Slice into three panels
for i, (xs, name) in enumerate([(0, "01_left_panel_1920x1080.png"),
                                 (PANEL_W, "02_center_panel_1920x1080.png"),
                                 (2 * PANEL_W, "03_right_panel_1920x1080.png")]):
    panel = canvas.crop((xs, 0, xs + PANEL_W, H))
    panel.save(OUT / name, "PNG", optimize=True)
    print(f"  saved: {name}")

# Seam-check overlay (shows where seams fall on the continuous canvas)
overlay = canvas.copy()
draw = ImageDraw.Draw(overlay)
for x in [PANEL_W, 2 * PANEL_W]:
    draw.line([(x, 0), (x, H)], fill=(255, 0, 100), width=2)
    draw.text((x + 8, 12), f"seam @ x={x}", fill=(255, 100, 200))
for x, label in [(PANEL_W // 2, "LEFT"),
                 (PANEL_W + PANEL_W // 2, "CENTER"),
                 (2 * PANEL_W + PANEL_W // 2, "RIGHT")]:
    draw.text((x - 30, H - 28), label, fill=(255, 255, 255))
overlay.save(OUT / "seam_check_overlay.png")
print(f"  saved: seam_check_overlay.png")

print(f"\nMock complete. {len(list(OUT.iterdir()))} files in {OUT}/")
print(f"\nVerify:")
print(f"  - Center panel = the only one with the focal opening (three shapes placeholder)")
print(f"  - Particle current crosses left↔center↔right seams smoothly")
print(f"  - Seams (±100px) are low-information (slight vertical darken)")
print(f"  - Nacre gradient continuous across all three panels")
