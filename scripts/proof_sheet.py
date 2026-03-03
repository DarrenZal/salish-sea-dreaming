#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Proof Sheet Generator

Creates contact sheets (proof sheets) from generated dream images for review.
Pairs each dream version with its original watercolor for comparison.

Usage:
    # Generate proof sheets for all directions
    python3.11 proof_sheet.py

    # Specific direction only
    python3.11 proof_sheet.py --direction bioluminescent

    # Best-of sheet (one per image key, most recent version)
    python3.11 proof_sheet.py --best-of

    # Custom columns
    python3.11 proof_sheet.py --columns 4
"""

import os
import sys
import argparse
import glob
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..')
EXPERIMENTS_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'experiments')
REFERENCE_DIR = os.path.join(PROJECT_DIR, 'assets', 'reference', 'briony-watercolors')
PROOF_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'proof-sheets')

# Import the catalog from dream_briony
sys.path.insert(0, SCRIPT_DIR)
from dream_briony import IMAGE_CATALOG, DREAM_DIRECTIONS

# Layout constants
THUMB_WIDTH = 480
THUMB_HEIGHT = 320
PADDING = 20
LABEL_HEIGHT = 50
HEADER_HEIGHT = 80
BG_COLOR = (30, 30, 35)
LABEL_BG = (40, 40, 48)
HEADER_BG = (20, 50, 60)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (51, 204, 170)  # Bioluminescent cyan


def get_font(size=14):
    """Get a font, falling back to default if needed."""
    for font_path in [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_thumbnail(image_path, width=THUMB_WIDTH, height=THUMB_HEIGHT):
    """Resize image to thumbnail, maintaining aspect ratio with letterboxing."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((width, height), Image.LANCZOS)

    thumb = Image.new("RGB", (width, height), BG_COLOR)
    x = (width - img.width) // 2
    y = (height - img.height) // 2
    thumb.paste(img, (x, y))
    return thumb


def find_generated_images(direction=None):
    """Find all generated dream images, optionally filtered by direction.
    Returns dict: {direction: {image_key: [paths sorted by timestamp]}}
    """
    results = {}

    if direction:
        dirs_to_scan = [direction]
    else:
        dirs_to_scan = [d for d in os.listdir(EXPERIMENTS_DIR)
                        if os.path.isdir(os.path.join(EXPERIMENTS_DIR, d))
                        and d in DREAM_DIRECTIONS]

    # Also check the root experiments dir for old-format images
    root_pngs = glob.glob(os.path.join(EXPERIMENTS_DIR, "*.png"))

    for d in sorted(dirs_to_scan):
        dir_path = os.path.join(EXPERIMENTS_DIR, d)
        results[d] = {}
        for f in sorted(glob.glob(os.path.join(dir_path, "*.png"))):
            basename = os.path.basename(f)
            # Parse: YYYYMMDD-HHMMSS_image-key.png
            parts = basename.split("_", 1)
            if len(parts) == 2:
                image_key = parts[1].replace(".png", "")
                if image_key in IMAGE_CATALOG:
                    results[d].setdefault(image_key, []).append(f)

    # Handle legacy root-level images (from before the refactor)
    # Old format: 20260209-192207_dream-kelp-breathing.png
    if root_pngs and not direction:
        # Map legacy suffixes to catalog keys
        legacy_map = {
            "kelp-breathing": "kelp-underwater",
            "octopus-dreaming": "octopus",
            "herring-emergence": "herring-panorama",
        }
        results.setdefault("_legacy", {})
        for f in sorted(root_pngs):
            basename = os.path.basename(f)
            # Try to extract a meaningful key
            parts = basename.replace(".png", "").split("_", 1)
            if len(parts) == 2:
                suffix = parts[1].replace("dream-", "")
                mapped_key = legacy_map.get(suffix, suffix)
                results["_legacy"].setdefault(mapped_key, []).append(f)

    return results


def get_reference_path(image_key):
    """Get the original watercolor path for an image key."""
    if image_key not in IMAGE_CATALOG:
        return None
    filename = IMAGE_CATALOG[image_key]["file"]
    path = os.path.join(REFERENCE_DIR, filename)
    return path if os.path.exists(path) else None


def create_proof_sheet(title, image_pairs, columns=3, output_path=None):
    """Create a proof sheet from pairs of (label, image_path).
    image_pairs: list of (label_text, image_path)
    """
    if not image_pairs:
        print(f"  No images for: {title}")
        return None

    font_small = get_font(12)
    font_medium = get_font(16)
    font_large = get_font(22)

    cell_width = THUMB_WIDTH + PADDING
    cell_height = THUMB_HEIGHT + LABEL_HEIGHT + PADDING

    rows = (len(image_pairs) + columns - 1) // columns
    sheet_width = columns * cell_width + PADDING
    sheet_height = HEADER_HEIGHT + rows * cell_height + PADDING

    sheet = Image.new("RGB", (sheet_width, sheet_height), BG_COLOR)
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([0, 0, sheet_width, HEADER_HEIGHT], fill=HEADER_BG)
    draw.text((PADDING, 15), title, fill=ACCENT_COLOR, font=font_large)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((PADDING, 45), f"Generated: {timestamp}", fill=TEXT_COLOR, font=font_small)

    # Thumbnails
    for i, (label, img_path) in enumerate(image_pairs):
        col = i % columns
        row = i // columns
        x = PADDING + col * cell_width
        y = HEADER_HEIGHT + row * cell_height

        try:
            thumb = make_thumbnail(img_path)
            sheet.paste(thumb, (x, y))
        except Exception as e:
            draw.rectangle([x, y, x + THUMB_WIDTH, y + THUMB_HEIGHT], fill=(50, 20, 20))
            draw.text((x + 10, y + THUMB_HEIGHT // 2), f"Error: {e}", fill=(200, 80, 80), font=font_small)

        # Label background
        label_y = y + THUMB_HEIGHT
        draw.rectangle([x, label_y, x + THUMB_WIDTH, label_y + LABEL_HEIGHT], fill=LABEL_BG)

        # Truncate label if too long
        label_lines = label.split("\n")
        for j, line in enumerate(label_lines[:2]):
            draw.text((x + 8, label_y + 5 + j * 18), line[:60], fill=TEXT_COLOR, font=font_small)

    os.makedirs(PROOF_DIR, exist_ok=True)
    if output_path is None:
        safe_title = title.lower().replace(" ", "-").replace("/", "-")[:40]
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(PROOF_DIR, f"{timestamp}_proof-{safe_title}.png")

    sheet.save(output_path, quality=95)
    print(f"  Saved: {output_path}")
    return output_path


def proof_by_direction(direction_key, columns=3):
    """Create a proof sheet for a specific dream direction, pairing originals with dreams."""
    images = find_generated_images(direction_key)
    if direction_key not in images or not images[direction_key]:
        print(f"  No images found for direction: {direction_key}")
        return None

    direction_info = DREAM_DIRECTIONS[direction_key]
    pairs = []

    for image_key, paths in sorted(images[direction_key].items()):
        # Add original
        ref_path = get_reference_path(image_key)
        if ref_path:
            subject = IMAGE_CATALOG[image_key]["subject"]
            pairs.append((f"ORIGINAL: {image_key}\n{subject[:55]}", ref_path))

        # Add all dream versions (most recent last)
        for path in paths:
            basename = os.path.basename(path)
            pairs.append((f"{direction_key}: {image_key}\n{basename}", path))

    title = f"{direction_info['name']} ({direction_key})"
    return create_proof_sheet(title, pairs, columns=columns)


def proof_best_of(columns=3):
    """Create a best-of sheet: most recent dream version per image key across all directions."""
    all_images = find_generated_images()
    pairs = []

    # Collect the most recent version per (image_key, direction)
    best = {}
    for direction_key, images in all_images.items():
        label = "bioluminescent" if direction_key == "_legacy" else direction_key
        for image_key, paths in images.items():
            if paths:
                best[(label, image_key)] = paths[-1]  # Most recent

    # Group by image key, show original then all direction variants
    seen_keys = set()
    for (direction_key, image_key), path in sorted(best.items(), key=lambda x: x[0][1]):
        if image_key not in seen_keys:
            ref_path = get_reference_path(image_key)
            if ref_path:
                subject = IMAGE_CATALOG[image_key]["subject"]
                pairs.append((f"ORIGINAL: {image_key}\n{subject[:55]}", ref_path))
            seen_keys.add(image_key)
        pairs.append((f"{direction_key}: {image_key}\n{os.path.basename(path)}", path))

    return create_proof_sheet("Best Of - All Directions", pairs, columns=columns)


def proof_comparison(image_key, columns=None):
    """Create a comparison sheet: one image across all available directions."""
    all_images = find_generated_images()
    pairs = []

    ref_path = get_reference_path(image_key)
    if ref_path:
        pairs.append((f"ORIGINAL: {image_key}\n{IMAGE_CATALOG[image_key]['subject'][:55]}", ref_path))

    for direction_key, images in sorted(all_images.items()):
        if direction_key == "_legacy":
            continue
        if image_key in images and images[image_key]:
            path = images[image_key][-1]
            dir_name = DREAM_DIRECTIONS[direction_key]["name"]
            pairs.append((f"{dir_name}\n{direction_key}", path))

    if columns is None:
        columns = min(len(pairs), 6)

    return create_proof_sheet(f"Comparison: {image_key}", pairs, columns=columns)


def main():
    parser = argparse.ArgumentParser(description="Generate proof sheets from dream experiments")
    parser.add_argument("--direction", choices=list(DREAM_DIRECTIONS.keys()),
                        help="Generate proof sheet for specific direction")
    parser.add_argument("--best-of", action="store_true",
                        help="Generate best-of sheet (most recent per image per direction)")
    parser.add_argument("--compare", metavar="IMAGE_KEY",
                        help="Compare one image across all directions")
    parser.add_argument("--all", action="store_true",
                        help="Generate proof sheets for all directions + best-of")
    parser.add_argument("--columns", type=int, default=3,
                        help="Number of columns in the grid (default: 3)")
    args = parser.parse_args()

    os.makedirs(PROOF_DIR, exist_ok=True)
    print("=== Salish Sea Dreaming - Proof Sheet Generator ===\n")

    generated = []

    if args.compare:
        if args.compare not in IMAGE_CATALOG:
            print(f"Error: Unknown image key '{args.compare}'")
            sys.exit(1)
        path = proof_comparison(args.compare, columns=args.columns)
        if path:
            generated.append(path)

    elif args.best_of:
        path = proof_best_of(columns=args.columns)
        if path:
            generated.append(path)

    elif args.direction:
        path = proof_by_direction(args.direction, columns=args.columns)
        if path:
            generated.append(path)

    elif args.all:
        # One sheet per direction
        for dk in DREAM_DIRECTIONS:
            path = proof_by_direction(dk, columns=args.columns)
            if path:
                generated.append(path)
        # Plus best-of
        path = proof_best_of(columns=args.columns)
        if path:
            generated.append(path)

    else:
        # Default: best-of
        path = proof_best_of(columns=args.columns)
        if path:
            generated.append(path)

    print(f"\n=== Done! Generated {len(generated)} proof sheet(s) ===")
    for g in generated:
        print(f"  {g}")


if __name__ == "__main__":
    main()
