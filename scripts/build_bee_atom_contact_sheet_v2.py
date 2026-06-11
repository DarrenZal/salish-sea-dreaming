#!/usr/bin/env python3
"""Rebuild Bee atom contact sheet using NEW SVG-geometry masks.

Renders each atom's mask alpha as a colored silhouette so cream-colored
wing atoms are visible (the old contact sheet showed them as invisible
cream-on-cream).

Per Task #56 acceptance criterion 4.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import csv

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed/Animal_Insect_Bee"
OUT = DECOMP / "_atom_contact_sheet_labeled_v2_new_masks.png"

THUMB = 120
PAD = 8
COLS = 8

LABEL_COLORS = {
    "wing-left":  (100, 160, 220),
    "wing-right": (100, 160, 220),
    "body":       (180, 100, 60),
    "head":       (180, 60, 100),
    "eye":        (60, 180, 60),
    "antenna":    (160, 100, 200),
    "leg":        (200, 140, 60),
    "stripe":     (220, 180, 80),
    "formline":   (120, 120, 120),
    "circle-oval": (80, 100, 180),
    "crescent":   (80, 180, 180),
    "trigon":     (180, 80, 180),
    "background": (160, 160, 160),
    "other":      (100, 100, 100),
}


def mask_to_silhouette(mask_path: Path, atom_color: tuple, fallback_size: tuple = (256, 256)) -> Image.Image:
    """Render mask alpha as a silhouette tinted with atom_color, on light BG."""
    if not mask_path.exists():
        img = Image.new("RGB", fallback_size, (240, 200, 200))
        return img
    img = Image.open(mask_path)
    if img.mode == "LA":
        _, A = img.split()
        alpha = np.asarray(A, dtype=np.uint8)
    elif img.mode == "RGBA":
        alpha = np.asarray(img, dtype=np.uint8)[..., 3]
    else:
        alpha = np.asarray(img.convert("L"), dtype=np.uint8)
    h, w = alpha.shape
    # White BG, atom_color where mask
    rgb = np.full((h, w, 3), 245, dtype=np.uint8)
    rgb[..., 0] = np.where(alpha > 30, atom_color[0], 245)
    rgb[..., 1] = np.where(alpha > 30, atom_color[1], 245)
    rgb[..., 2] = np.where(alpha > 30, atom_color[2], 245)
    return Image.fromarray(rgb, "RGB")


def main():
    csv_path = DECOMP / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            atoms.append(row)

    n = len(atoms)
    rows = (n + COLS - 1) // COLS
    cell_w = THUMB + PAD * 2
    cell_h = THUMB + 64
    w = COLS * cell_w + PAD
    h = rows * cell_h + PAD + 100

    sheet = Image.new("RGB", (w, h), (240, 234, 222))
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 16), f"Animal_Insect_Bee — {n} atoms (NEW SVG-geometry masks, post Task #56)",
              fill=(40, 40, 40))
    draw.text((PAD, 36), f"Silhouette = NEW mask alpha. Border = AI label color. Caption amber if confidence<0.7.",
              fill=(100, 100, 100))
    draw.text((PAD, 56), f"Difference from v1 contact sheet: cream-colored wing atoms (0027-0032, 0033-0038) are now VISIBLE.",
              fill=(120, 80, 40))

    for i, a in enumerate(atoms):
        r, c = i // COLS, i % COLS
        x = PAD + c * cell_w
        y = 100 + r * cell_h
        label = a.get("ai_label", "") or "?"
        try:
            confidence = float(a.get("ai_confidence", 0) or 0)
        except ValueError:
            confidence = 0
        border = LABEL_COLORS.get(label, (180, 60, 60))
        # Border
        draw.rectangle([x + PAD - 4, y - 4, x + PAD + THUMB + 4, y + THUMB + 4],
                       outline=border, width=4)
        # Render NEW mask as tinted silhouette
        mask_path = DECOMP / a.get("mask_png", f"{a['atom_id']}_mask.png")
        sil = mask_to_silhouette(mask_path, border)
        sil = sil.resize((THUMB, THUMB), Image.LANCZOS)
        sheet.paste(sil, (x + PAD, y))
        # Caption
        caption_color = (40, 40, 40) if confidence >= 0.7 else (180, 120, 30)
        draw.text((x + PAD, y + THUMB + 4), a["atom_id"], fill=(40, 40, 40))
        draw.text((x + PAD, y + THUMB + 22), f"{label} ({confidence:.2f})", fill=caption_color)
        area = float(a.get("area", 0))
        draw.text((x + PAD, y + THUMB + 42), f"area={area:.0f}", fill=(100, 100, 100))

    sheet.save(OUT)
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
