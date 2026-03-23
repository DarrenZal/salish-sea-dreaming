#!/usr/bin/env python3
"""
Generate QC contact sheets from scraped images — one grid per species.
Opens in browser for fast visual review.

Usage:
    python tools/make_qc_sheets.py --input images/intertidal-raw --output training-data/review/qc-intertidal
    python tools/make_qc_sheets.py --input images/whales-raw --output training-data/review/qc-whales
"""

import argparse
import os
import sys
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow required. Install with: pip install Pillow")
    sys.exit(1)


def make_contact_sheet(images, title, output_path, thumb_size=200, cols=10):
    """Create a contact sheet grid from a list of image paths."""
    rows = (len(images) + cols - 1) // cols
    margin = 4
    label_h = 20
    cell_w = thumb_size + margin
    cell_h = thumb_size + margin + label_h
    width = cols * cell_w + margin
    height = rows * cell_h + margin + 40  # 40px for title

    sheet = Image.new("RGB", (width, height), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)

    # Title
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
    except (OSError, IOError):
        font = ImageFont.load_default()
        small_font = font

    draw.text((margin, 8), f"{title} ({len(images)} images)", fill=(200, 200, 200), font=font)

    for i, img_path in enumerate(sorted(images)):
        row = i // cols
        col = i % cols
        x = col * cell_w + margin
        y = row * cell_h + margin + 40

        try:
            img = Image.open(img_path)
            img.thumbnail((thumb_size, thumb_size))
            sheet.paste(img, (x, y))
        except Exception as e:
            draw.rectangle([x, y, x + thumb_size, y + thumb_size], fill=(80, 30, 30))
            draw.text((x + 4, y + 4), "ERR", fill=(255, 100, 100), font=small_font)

        # Filename label
        fname = Path(img_path).stem
        short = fname[:25] + "..." if len(fname) > 25 else fname
        draw.text((x, y + thumb_size + 2), short, fill=(150, 150, 150), font=small_font)

    sheet.save(output_path, quality=90)
    return len(images)


def make_html_review(species_sheets, output_dir):
    """Generate an HTML page linking all contact sheets for browser review."""
    html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>QC Review — Intertidal Dreaming Corpus</title>
<style>
body { background: #111; color: #ddd; font-family: system-ui; padding: 20px; }
h1 { color: #8ecae6; }
h2 { color: #ccc; margin-top: 30px; }
.sheet { margin: 10px 0; max-width: 100%; }
.sheet img { width: 100%; border: 1px solid #333; border-radius: 4px; }
.info { color: #888; font-size: 13px; margin-bottom: 20px; }
</style></head><body>
<h1>QC Review — Intertidal Dreaming Corpus</h1>
<div class="info">
Review each species grid. Note filenames of images to reject in <code>rejects-intertidal-dreaming.csv</code>.<br>
Reject: dead/beached, human handling, surface/sky dominant, subject too small, bad quality.<br>
Keep: underwater, intertidal, organism-dominant, multi-subject ecological scenes, habitat-rich.
</div>
"""
    for species, (sheet_path, count) in sorted(species_sheets.items()):
        fname = Path(sheet_path).name
        html += f'<h2>{species} ({count} images)</h2>\n'
        html += f'<div class="sheet"><img src="{fname}" alt="{species}"></div>\n'

    html += "</body></html>"

    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w") as f:
        f.write(html)
    return html_path


def main():
    parser = argparse.ArgumentParser(description="Generate QC contact sheets")
    parser.add_argument("--input", required=True, help="Input image directory")
    parser.add_argument("--output", required=True, help="Output directory for contact sheets")
    parser.add_argument("--thumb-size", type=int, default=200, help="Thumbnail size (default 200)")
    parser.add_argument("--cols", type=int, default=10, help="Columns per sheet (default 10)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group images by species
    species_images = defaultdict(list)
    for f in sorted(input_dir.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png") and f.name != "CLAUDE.md":
            # Extract species from filename: Species_Name_12345.jpg → Species_Name
            parts = f.stem.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                species = parts[0]
            else:
                species = f.stem
            species_images[species].append(str(f))

    print(f"Found {sum(len(v) for v in species_images.values())} images across {len(species_images)} species")

    species_sheets = {}
    for species, images in sorted(species_images.items()):
        sheet_path = output_dir / f"{species}.jpg"
        count = make_contact_sheet(
            images, species.replace("_", " "),
            str(sheet_path), args.thumb_size, args.cols
        )
        species_sheets[species] = (str(sheet_path), count)
        print(f"  {species}: {count} images → {sheet_path.name}")

    html_path = make_html_review(species_sheets, str(output_dir))
    print(f"\nHTML review page: {html_path}")
    print(f"Open with: open {html_path}")


if __name__ == "__main__":
    main()
