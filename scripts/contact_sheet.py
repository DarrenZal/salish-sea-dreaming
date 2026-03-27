#!/usr/bin/env python3
"""
Generic contact sheet generator.

Creates a grid of thumbnails with filename labels from any image directory.
Used for QC review of video frame extractions, curated photos, etc.

Usage:
    python scripts/contact_sheet.py images/moonfish-preview/P1077716/
    python scripts/contact_sheet.py images/denning-curated/ --cols 4 --output review.jpg
    python scripts/contact_sheet.py images/moonfish-frames/underwater/ --cols 8 --thumb 200
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont


def make_contact_sheet(image_dir, output=None, cols=6, thumb_size=300, label_height=30):
    """Generate a contact sheet from all images in a directory."""
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    files = sorted(
        f for f in os.listdir(image_dir)
        if os.path.splitext(f)[1].lower() in extensions
    )

    if not files:
        print(f"No images found in {image_dir}")
        return None

    rows = (len(files) + cols - 1) // cols
    cell_w = thumb_size
    cell_h = thumb_size + label_height
    padding = 4

    sheet_w = cols * cell_w + (cols + 1) * padding
    sheet_h = rows * cell_h + (rows + 1) * padding
    sheet = Image.new('RGB', (sheet_w, sheet_h), (30, 30, 35))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 10)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for i, fname in enumerate(files):
        row, col = divmod(i, cols)
        x = col * cell_w + (col + 1) * padding
        y = row * cell_h + (row + 1) * padding

        fpath = os.path.join(image_dir, fname)
        try:
            img = Image.open(fpath)
            img.thumbnail((thumb_size - 4, thumb_size - label_height - 4), Image.LANCZOS)
            # Center thumbnail in cell
            tx = x + (cell_w - img.width) // 2
            ty = y + (thumb_size - label_height - img.height) // 2
            sheet.paste(img, (tx, ty))
        except Exception as e:
            draw.rectangle([x, y, x + cell_w - 4, y + thumb_size - label_height - 4],
                           fill=(60, 20, 20))
            draw.text((x + 4, y + 4), f"ERR: {fname[:20]}", fill=(200, 80, 80), font=font)
            continue

        # Label
        label = fname[:35] + ('...' if len(fname) > 35 else '')
        label_y = y + thumb_size - label_height
        draw.text((x + 2, label_y + 2), label, fill=(200, 200, 200), font=font)

    if output is None:
        dirname = os.path.basename(os.path.normpath(image_dir))
        output = os.path.join(image_dir, f"contact-sheet-{dirname}.jpg")

    sheet.save(output, quality=90)
    print(f"Contact sheet: {output} ({len(files)} images, {cols}x{rows} grid)")
    return output


def main():
    parser = argparse.ArgumentParser(description="Generate contact sheet from image directory")
    parser.add_argument("directory", help="Directory containing images")
    parser.add_argument("--output", "-o", help="Output file path (default: in source dir)")
    parser.add_argument("--cols", type=int, default=6, help="Columns in grid (default: 6)")
    parser.add_argument("--thumb", type=int, default=300, help="Thumbnail size in pixels (default: 300)")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a directory")
        sys.exit(1)

    make_contact_sheet(args.directory, args.output, args.cols, args.thumb)


if __name__ == "__main__":
    main()
