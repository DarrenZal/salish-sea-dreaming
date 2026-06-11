#!/usr/bin/env python3
"""Build old-vs-new mask diagnostic for Bee wing atoms.

Shows the cream-color decomposition limitation visually:
  - OLD isolated PNG (cream-on-white, invisible)
  - NEW mask PNG (alpha-on-transparent, visible silhouette)

Per Task #56 acceptance criterion 5.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed/Animal_Insect_Bee"
OUT = DECOMP / "_old_vs_new_mask_diagnostic.png"

# Pick representative atoms to compare:
# Wing atoms (cream, broken in OLD) + a dark body atom (worked in OLD, proves new doesn't break it)
EXAMPLES = [
    ("atom_0027", "Wing-right (cream, OLD broken)"),
    ("atom_0033", "Wing-left (cream, OLD broken)"),
    ("atom_0029", "Wing highlight (cream, OLD broken)"),
    ("atom_0003", "Body (dark, OLD worked)"),
    ("atom_0017", "Stripe (orange, OLD partial)"),
    ("atom_0006", "Antenna (dark, OLD worked)"),
]

THUMB = 220
PAD = 12


def make_old_view(atom_id: str) -> Image.Image:
    """Render the OLD isolated PNG on a white BG (simulates how it was used)."""
    p = DECOMP / f"{atom_id}.png"
    img = Image.open(p).convert("RGBA")
    canvas = Image.new("RGB", img.size, (255, 255, 255))
    canvas.paste(img, (0, 0), img)
    return canvas.resize((THUMB, THUMB), Image.LANCZOS)


def make_new_view(atom_id: str) -> Image.Image:
    """Render the NEW mask: alpha channel as red overlay on white BG."""
    p = DECOMP / f"{atom_id}_mask.png"
    img = Image.open(p)
    if img.mode == "LA":
        _, A = img.split()
        alpha = np.asarray(A, dtype=np.uint8)
    elif img.mode == "RGBA":
        alpha = np.asarray(img, dtype=np.uint8)[..., 3]
    else:
        alpha = np.asarray(img.convert("L"), dtype=np.uint8)
    h, w = alpha.shape
    # Build RGB image: white BG, red where mask
    rgb = np.full((h, w, 3), 255, dtype=np.uint8)
    rgb[..., 0] = np.where(alpha > 30, 200, 255)
    rgb[..., 1] = np.where(alpha > 30, 60, 255)
    rgb[..., 2] = np.where(alpha > 30, 80, 255)
    img_out = Image.fromarray(rgb, "RGB")
    return img_out.resize((THUMB, THUMB), Image.LANCZOS)


def count_visible(atom_id: str, kind: str) -> int:
    """Count visible pixels for old (dark in isolated PNG) or new (alpha in mask PNG)."""
    if kind == "old":
        p = DECOMP / f"{atom_id}.png"
        img = Image.open(p).convert("L")
        arr = np.asarray(img, dtype=np.uint8)
        return int((arr < 100).sum())  # dark pixels = atom (old method)
    else:
        p = DECOMP / f"{atom_id}_mask.png"
        img = Image.open(p)
        if img.mode == "LA":
            _, A = img.split()
            return int((np.asarray(A) > 128).sum())
        return int((np.asarray(img.convert("RGBA"))[..., 3] > 128).sum())


def main():
    cols = 4  # atom_id | OLD | NEW | label
    rows = len(EXAMPLES) + 1  # +1 for header
    cell_w = THUMB + PAD * 2
    col_widths = [180, cell_w, cell_w, 360]
    total_w = sum(col_widths) + PAD * (len(col_widths) + 1)
    row_h = THUMB + PAD * 2
    total_h = 80 + row_h * len(EXAMPLES) + PAD

    sheet = Image.new("RGB", (total_w, total_h), (244, 238, 226))
    draw = ImageDraw.Draw(sheet)

    # Title
    draw.text((PAD, 14), "Bee decomposition: OLD raster-contrast mask vs NEW SVG-geometry mask",
              fill=(40, 40, 40))
    draw.text((PAD, 34), "OLD: 255-Luminance of isolated_png. Fails for cream/light atoms (cream≈white BG → mask empty).",
              fill=(80, 80, 80))
    draw.text((PAD, 54), "NEW: SVG path geometry rasterized with forced fill=black + transparent BG. Color-independent.",
              fill=(80, 80, 80))

    # Column headers
    headers = ["atom_id / label", "OLD (raster-contrast)", "NEW (SVG-geometry)", "Counts"]
    x = PAD
    for h, w in zip(headers, col_widths):
        draw.text((x + 4, 80), h, fill=(40, 40, 40))
        x += w + PAD

    y = 100
    for atom_id, label in EXAMPLES:
        x = PAD
        # Col 1: atom_id + label
        draw.text((x + 4, y + 4), atom_id, fill=(40, 40, 40))
        # Multi-line label
        words = label.split(" ", 2)
        for i, w in enumerate(words):
            draw.text((x + 4, y + 26 + i * 18), w, fill=(80, 80, 80))
        x += col_widths[0] + PAD

        # Col 2: OLD view
        old = make_old_view(atom_id)
        sheet.paste(old, (x + PAD, y + PAD))
        x += col_widths[1] + PAD

        # Col 3: NEW view
        new = make_new_view(atom_id)
        sheet.paste(new, (x + PAD, y + PAD))
        x += col_widths[2] + PAD

        # Col 4: counts + verdict
        old_count = count_visible(atom_id, "old")
        new_count = count_visible(atom_id, "new")
        draw.text((x + 4, y + 4), f"OLD dark px: {old_count}", fill=(40, 40, 40))
        draw.text((x + 4, y + 26), f"NEW alpha px: {new_count}", fill=(40, 40, 40))
        verdict = "✓ fixed" if old_count < 50 and new_count > 100 else (
            "✓ unchanged (already worked)" if old_count > 100 and new_count > 100 else "—")
        color = (60, 140, 60) if "✓" in verdict else (140, 140, 140)
        draw.text((x + 4, y + 56), verdict, fill=color)

        y += row_h

    sheet.save(OUT)
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
