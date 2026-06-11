#!/usr/bin/env python3
"""Build a small contact sheet for Bee's 53 decomposed atoms (no AI labels yet).

Shows each atom with its atom_id + fill_color. Operator can scan visually
to decide whether to run AI labeling pass.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import csv

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed/Animal_Insect_Bee"
OUT = DECOMP / "_atom_contact_sheet_labeled.png"

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


def main():
    csv_path = DECOMP / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            atoms.append(row)

    n = len(atoms)
    rows = (n + COLS - 1) // COLS
    cell_w = THUMB + PAD * 2
    cell_h = THUMB + 56
    w = COLS * cell_w + PAD
    h = rows * cell_h + PAD + 60
    # Bigger cells to fit label text
    cell_h_local = THUMB + 64
    h_local = rows * cell_h_local + PAD + 80

    sheet = Image.new("RGB", (w, h_local), (240, 234, 222))
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 16), f"Animal_Insect_Bee — {n} decomposed atoms with AI labels",
              fill=(40, 40, 40))
    draw.text((PAD, 36), f"Border color = label category. Yellow caption = low-confidence (<0.7).",
              fill=(100, 100, 100))

    for i, a in enumerate(atoms):
        r, c = i // COLS, i % COLS
        x = PAD + c * cell_w
        y = 80 + r * cell_h_local
        label = a.get("ai_label", "") or "?"
        try:
            confidence = float(a.get("ai_confidence", 0) or 0)
        except ValueError:
            confidence = 0
        border = LABEL_COLORS.get(label, (180, 60, 60))
        # Draw colored border
        draw.rectangle([x + PAD - 4, y - 4, x + PAD + THUMB + 4, y + THUMB + 4],
                       outline=border, width=4)
        try:
            iso = Image.open(DECOMP / a["isolated_png"]).convert("RGB")
            iso = iso.resize((THUMB, THUMB), Image.LANCZOS)
            sheet.paste(iso, (x + PAD, y))
        except Exception:
            draw.rectangle([x + PAD, y, x + PAD + THUMB, y + THUMB], fill=(255, 200, 200))
        # Caption: atom_id + label + confidence
        atom_text = a["atom_id"]
        label_text = f"{label} ({confidence:.2f})"
        caption_color = (40, 40, 40)
        if confidence < 0.7:
            caption_color = (180, 120, 30)  # amber for low-confidence
        draw.text((x + PAD, y + THUMB + 4), atom_text, fill=(40, 40, 40))
        draw.text((x + PAD, y + THUMB + 22), label_text, fill=caption_color)
        area = float(a.get("area", 0))
        draw.text((x + PAD, y + THUMB + 42), f"area={area:.0f}", fill=(100, 100, 100))

    sheet.save(OUT)
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
