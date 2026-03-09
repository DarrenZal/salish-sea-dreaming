#!/usr/bin/env python3
"""
Salish Sea Dreaming - Contact Sheet Crop Pipeline

Prepare Briony Penn's watercolor images for StyleGAN2-ada training.
Takes source images + crop recipe, generates candidate crops,
renders contact sheets for human review, and manages a keep/reject manifest.

Workflow:
  1. Generate crop candidates:
     python scripts/crop_candidates.py VisualArt/Brionny/Paintings/IMG_1476.jpg --recipe horizontal-thirds

  2. Generate for multiple images:
     python scripts/crop_candidates.py VisualArt/Brionny/Paintings/*.jpg --recipe quadrants

  3. Render contact sheets from candidates:
     python scripts/crop_candidates.py --contact-sheet training-data/review/contact-sheets/

  4. After filling keep.csv (keep=yes/no), promote approved crops:
     python scripts/crop_candidates.py --promote

  5. Limit crops per source (default 6):
     python scripts/crop_candidates.py image.jpg --recipe quadrants --max-per-source 4
"""

import os
import sys
import csv
import argparse
import glob
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ExifTags

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")

# Output directories
REVIEW_DIR = os.path.join(PROJECT_DIR, "training-data", "review")
CANDIDATES_DIR = os.path.join(REVIEW_DIR, "candidates")
CONTACT_DIR = os.path.join(REVIEW_DIR, "contact-sheets")
KEEP_CSV = os.path.join(REVIEW_DIR, "keep.csv")
PROVENANCE_CSV = os.path.join(PROJECT_DIR, "training-data", "provenance.csv")
TRAINING_DIR = os.path.join(PROJECT_DIR, "training-data", "briony-marine-colour")

# Visual constants (matching proof_sheet.py)
THUMB_SIZE = 400
PADDING = 20
LABEL_HEIGHT = 60
HEADER_HEIGHT = 80
BG_COLOR = (30, 30, 35)
LABEL_BG = (40, 40, 48)
HEADER_BG = (20, 50, 60)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (51, 204, 170)

KEEP_CSV_COLUMNS = ["candidate_file", "source_file", "crop_recipe", "crop_box", "keep"]
PROVENANCE_COLUMNS = [
    "filename",
    "source_file",
    "source",
    "url",
    "license",
    "photographer_artist",
    "parent_source_file",
    "crop_box",
    "crop_recipe",
    "approved_for_training",
]

# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------

def _recipe_horizontal_thirds(w, h):
    """Split image into 3 horizontal bands: top, middle, bottom."""
    band_h = h // 3
    return [
        ("top", (0, 0, w, band_h)),
        ("middle", (0, band_h, w, band_h * 2)),
        ("bottom", (0, band_h * 2, w, h)),
    ]


def _recipe_horizontal_halves(w, h):
    """Split image into 2 horizontal bands."""
    mid = h // 2
    return [
        ("top", (0, 0, w, mid)),
        ("bottom", (0, mid, w, h)),
    ]


def _recipe_vertical_thirds(w, h):
    """Split image into 3 vertical bands: left, center, right."""
    band_w = w // 3
    return [
        ("left", (0, 0, band_w, h)),
        ("center", (band_w, 0, band_w * 2, h)),
        ("right", (band_w * 2, 0, w, h)),
    ]


def _recipe_vertical_halves(w, h):
    """Split image into 2 vertical bands."""
    mid = w // 2
    return [
        ("left", (0, 0, mid, h)),
        ("right", (mid, 0, w, h)),
    ]


def _recipe_quadrants(w, h):
    """Split image into 4 quadrants."""
    mid_w = w // 2
    mid_h = h // 2
    return [
        ("NW", (0, 0, mid_w, mid_h)),
        ("NE", (mid_w, 0, w, mid_h)),
        ("SW", (0, mid_h, mid_w, h)),
        ("SE", (mid_w, mid_h, w, h)),
    ]


def _recipe_center_crop(w, h):
    """Extract center 60% of image."""
    margin_x = int(w * 0.2)
    margin_y = int(h * 0.2)
    return [
        ("center-60pct", (margin_x, margin_y, w - margin_x, h - margin_y)),
    ]


def _recipe_panorama_zones(w, h):
    """Slide a square window across a wide panorama with 25% overlap."""
    side = min(w, h)
    if side == 0:
        return []
    stride = int(side * 0.75)  # 25% overlap
    zones = []
    x = 0
    idx = 0
    while x + side <= w:
        zones.append((f"zone-{idx}", (x, 0, x + side, side)))
        x += stride
        idx += 1
    # If the last zone didn't reach the right edge, add a final zone pinned to right
    if zones and zones[-1][1][2] < w:
        zones.append((f"zone-{idx}", (w - side, 0, w, side)))
    # Similarly handle vertical if image is taller than wide (unlikely for panoramas)
    if not zones:
        zones.append(("zone-0", (0, 0, side, side)))
    return zones


def _recipe_custom(w, h, box_str=None):
    """Custom crop from explicit x,y,w,h coordinates."""
    if not box_str:
        raise ValueError("--custom-box x,y,w,h required for custom recipe")
    parts = [int(p.strip()) for p in box_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Expected 4 values for custom box, got {len(parts)}")
    cx, cy, cw, ch = parts
    return [("custom", (cx, cy, cx + cw, cy + ch))]


RECIPES = {
    "horizontal-thirds": _recipe_horizontal_thirds,
    "horizontal-halves": _recipe_horizontal_halves,
    "vertical-thirds": _recipe_vertical_thirds,
    "vertical-halves": _recipe_vertical_halves,
    "quadrants": _recipe_quadrants,
    "center-crop": _recipe_center_crop,
    "panorama-zones": _recipe_panorama_zones,
    "custom": _recipe_custom,
}

# ---------------------------------------------------------------------------
# Fonts (reused from proof_sheet.py pattern)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# EXIF orientation
# ---------------------------------------------------------------------------

def apply_exif_orientation(img):
    """Apply EXIF orientation tag so phone photos display correctly.

    Phone cameras store the image in sensor orientation and set an EXIF tag
    to tell viewers how to rotate it. PIL doesn't auto-apply this, so
    portrait photos shot sideways appear rotated.
    """
    try:
        exif = img.getexif()
        # EXIF orientation tag ID = 274
        orientation = exif.get(274)
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError):
        pass  # no EXIF data
    return img


# ---------------------------------------------------------------------------
# Crop generation
# ---------------------------------------------------------------------------

def make_candidate_filename(source_path, recipe_name, zone_label):
    """Deterministic filename for a candidate crop."""
    base = os.path.splitext(os.path.basename(source_path))[0]
    # Sanitize
    safe_base = base.replace(" ", "-").replace("/", "-")
    return f"{safe_base}__{recipe_name}__{zone_label}.png"


def generate_crops(source_path, recipe_name, max_per_source=6, custom_box=None):
    """Generate crop candidate images from a single source.

    Returns list of dicts with keys:
      candidate_file, source_file, crop_recipe, crop_box
    """
    source_path = os.path.abspath(source_path)
    if not os.path.isfile(source_path):
        print(f"  WARNING: source not found: {source_path}")
        return []

    img = Image.open(source_path)
    img = apply_exif_orientation(img)
    img = img.convert("RGB")
    w, h = img.size

    recipe_fn = RECIPES.get(recipe_name)
    if recipe_fn is None:
        print(f"  ERROR: unknown recipe '{recipe_name}'")
        return []

    if recipe_name == "custom":
        zones = recipe_fn(w, h, box_str=custom_box)
    else:
        zones = recipe_fn(w, h)

    # Enforce max-per-source
    zones = zones[:max_per_source]

    os.makedirs(CANDIDATES_DIR, exist_ok=True)
    results = []

    for zone_label, box in zones:
        # box is (left, upper, right, lower) for PIL crop
        cropped = img.crop(box)
        fname = make_candidate_filename(source_path, recipe_name, zone_label)
        out_path = os.path.join(CANDIDATES_DIR, fname)
        cropped.save(out_path, quality=95)

        # Make source relative to project dir for portability
        try:
            rel_source = os.path.relpath(source_path, PROJECT_DIR)
        except ValueError:
            rel_source = source_path

        results.append({
            "candidate_file": fname,
            "source_file": rel_source,
            "crop_recipe": f"{recipe_name}-{zone_label}",
            "crop_box": f"[{box[0]},{box[1]},{box[2]},{box[3]}]",
        })
        print(f"  Crop: {fname}  box={box}")

    return results


def update_keep_csv(new_rows):
    """Append new rows to keep.csv, preserving any existing entries."""
    existing = {}
    if os.path.exists(KEEP_CSV):
        with open(KEEP_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["candidate_file"]] = row

    # Merge: new entries get empty keep, existing keep their value
    for row in new_rows:
        key = row["candidate_file"]
        if key not in existing:
            existing[key] = {**row, "keep": ""}
        else:
            # Update metadata but preserve the keep decision
            keep_val = existing[key].get("keep", "")
            existing[key].update(row)
            existing[key]["keep"] = keep_val

    os.makedirs(os.path.dirname(KEEP_CSV), exist_ok=True)
    with open(KEEP_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP_CSV_COLUMNS)
        writer.writeheader()
        for key in sorted(existing):
            writer.writerow(existing[key])

    print(f"\n  Updated keep.csv: {len(existing)} entries  ({KEEP_CSV})")


# ---------------------------------------------------------------------------
# Contact sheet rendering
# ---------------------------------------------------------------------------

def make_thumbnail(image_path, size=THUMB_SIZE):
    """Resize image to square thumbnail with letterboxing."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((size, size), Image.LANCZOS)
    thumb = Image.new("RGB", (size, size), BG_COLOR)
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    thumb.paste(img, (x, y))
    return thumb


def render_contact_sheet(title, image_entries, output_dir=None, columns=3):
    """Render a contact sheet image.

    image_entries: list of (label_text, image_path)
    """
    if not image_entries:
        print(f"  No images for contact sheet: {title}")
        return None

    font_small = get_font(12)
    font_medium = get_font(14)
    font_large = get_font(22)

    cell_w = THUMB_SIZE + PADDING
    cell_h = THUMB_SIZE + LABEL_HEIGHT + PADDING

    rows = (len(image_entries) + columns - 1) // columns
    sheet_w = columns * cell_w + PADDING
    sheet_h = HEADER_HEIGHT + rows * cell_h + PADDING

    sheet = Image.new("RGB", (sheet_w, sheet_h), BG_COLOR)
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([0, 0, sheet_w, HEADER_HEIGHT], fill=HEADER_BG)
    draw.text((PADDING, 15), title, fill=ACCENT_COLOR, font=font_large)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((PADDING, 45), f"Generated: {timestamp}", fill=TEXT_COLOR, font=font_small)

    # Thumbnails
    for i, (label, img_path) in enumerate(image_entries):
        col = i % columns
        row = i // columns
        x = PADDING + col * cell_w
        y = HEADER_HEIGHT + row * cell_h

        try:
            thumb = make_thumbnail(img_path)
            sheet.paste(thumb, (x, y))
        except Exception as e:
            draw.rectangle([x, y, x + THUMB_SIZE, y + THUMB_SIZE], fill=(50, 20, 20))
            draw.text(
                (x + 10, y + THUMB_SIZE // 2),
                f"Error: {e}",
                fill=(200, 80, 80),
                font=font_small,
            )

        # Label background
        label_y = y + THUMB_SIZE
        draw.rectangle(
            [x, label_y, x + THUMB_SIZE, label_y + LABEL_HEIGHT], fill=LABEL_BG
        )

        # Label text (up to 3 lines)
        label_lines = label.split("\n")
        for j, line in enumerate(label_lines[:3]):
            draw.text(
                (x + 8, label_y + 5 + j * 16),
                line[:65],
                fill=TEXT_COLOR,
                font=font_small,
            )

    if output_dir is None:
        output_dir = CONTACT_DIR
    os.makedirs(output_dir, exist_ok=True)

    safe_title = title.lower().replace(" ", "-").replace("/", "-")[:40]
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(output_dir, f"{ts}_crop-review-{safe_title}.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved contact sheet: {out_path}")
    return out_path


def build_contact_sheets_from_candidates(output_dir=None):
    """Group all candidates by source image and render a contact sheet per source."""
    if not os.path.exists(KEEP_CSV):
        print(f"  No keep.csv found at {KEEP_CSV}. Generate crops first.")
        return []

    with open(KEEP_CSV, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by source file
    by_source = {}
    for row in rows:
        src = row["source_file"]
        by_source.setdefault(src, []).append(row)

    sheets = []
    for source, entries in sorted(by_source.items()):
        source_name = os.path.basename(source)
        recipe_set = set(e["crop_recipe"].rsplit("-", 1)[0] for e in entries)
        recipe_label = ", ".join(sorted(recipe_set))
        title = f"{source_name} | {recipe_label}"

        image_entries = []
        for e in entries:
            cand_path = os.path.join(CANDIDATES_DIR, e["candidate_file"])
            if not os.path.isfile(cand_path):
                continue
            label = f"{e['crop_recipe']}\n{e['crop_box']}\nkeep: {e.get('keep', '?')}"
            image_entries.append((label, cand_path))

        if image_entries:
            path = render_contact_sheet(title, image_entries, output_dir=output_dir)
            if path:
                sheets.append(path)

    return sheets


# ---------------------------------------------------------------------------
# Promote approved crops
# ---------------------------------------------------------------------------

def promote():
    """Read keep.csv, copy approved crops to training dir, append to provenance.csv."""
    if not os.path.exists(KEEP_CSV):
        print(f"  No keep.csv found at {KEEP_CSV}")
        return

    with open(KEEP_CSV, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    approved = [r for r in rows if r.get("keep", "").strip().lower() == "yes"]
    if not approved:
        print("  No approved crops (keep=yes) found in keep.csv")
        return

    os.makedirs(TRAINING_DIR, exist_ok=True)

    # Load existing provenance to avoid duplicates
    existing_provenance = set()
    if os.path.exists(PROVENANCE_CSV):
        with open(PROVENANCE_CSV, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_provenance.add(row.get("filename", ""))

    new_provenance = []
    copied = 0

    for row in approved:
        cand_path = os.path.join(CANDIDATES_DIR, row["candidate_file"])
        if not os.path.isfile(cand_path):
            print(f"  WARNING: candidate missing: {cand_path}")
            continue

        dest_name = row["candidate_file"]
        dest_path = os.path.join(TRAINING_DIR, dest_name)
        # Filename in provenance is relative to training-data/
        provenance_filename = f"briony-marine-colour/{dest_name}"

        # Copy the image
        img = Image.open(cand_path)
        img.save(dest_path, quality=95)
        copied += 1

        # Build provenance row
        if provenance_filename not in existing_provenance:
            new_provenance.append({
                "filename": provenance_filename,
                "source_file": row["source_file"],
                "source": "Briony Penn archive",
                "url": "",
                "license": "artist permission",
                "photographer_artist": "Briony Penn",
                "parent_source_file": row["source_file"],
                "crop_box": row["crop_box"],
                "crop_recipe": row["crop_recipe"],
                "approved_for_training": "yes",
            })

    # Append to provenance.csv
    write_header = not os.path.exists(PROVENANCE_CSV)
    os.makedirs(os.path.dirname(PROVENANCE_CSV), exist_ok=True)
    with open(PROVENANCE_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PROVENANCE_COLUMNS)
        if write_header:
            writer.writeheader()
        for prow in new_provenance:
            writer.writerow(prow)

    print(f"\n  Promoted {copied} crop(s) to {TRAINING_DIR}")
    print(f"  Added {len(new_provenance)} new row(s) to {PROVENANCE_CSV}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Contact sheet crop pipeline for StyleGAN2-ada training data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "sources",
        nargs="*",
        help="Source image file(s) to crop",
    )
    parser.add_argument(
        "--recipe",
        choices=list(RECIPES.keys()),
        help="Crop recipe to apply",
    )
    parser.add_argument(
        "--custom-box",
        metavar="x,y,w,h",
        help="Explicit crop box for --recipe custom (x,y,width,height)",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=6,
        help="Maximum crop candidates per source image (default: 6)",
    )
    parser.add_argument(
        "--contact-sheet",
        nargs="?",
        const=CONTACT_DIR,
        metavar="OUTPUT_DIR",
        help="Render contact sheets from existing candidates (optionally specify output dir)",
    )
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promote approved crops (keep=yes) from keep.csv to training dir + provenance.csv",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=3,
        help="Number of columns in contact sheet grid (default: 3)",
    )

    args = parser.parse_args()

    # Resolve paths relative to project root
    os.chdir(PROJECT_DIR)

    print("=== Salish Sea Dreaming - Crop Candidate Pipeline ===\n")

    # Mode: promote
    if args.promote:
        promote()
        return

    # Mode: contact-sheet
    if args.contact_sheet is not None:
        output_dir = args.contact_sheet if args.contact_sheet != CONTACT_DIR else None
        sheets = build_contact_sheets_from_candidates(output_dir=output_dir)
        print(f"\n  Generated {len(sheets)} contact sheet(s)")
        return

    # Mode: generate crops
    if not args.sources:
        parser.print_help()
        sys.exit(1)

    if not args.recipe:
        print("ERROR: --recipe is required when generating crops")
        sys.exit(1)

    # Expand globs (shell may have already expanded, but handle both)
    source_files = []
    for pattern in args.sources:
        expanded = glob.glob(pattern)
        if expanded:
            source_files.extend(expanded)
        else:
            source_files.append(pattern)

    all_rows = []
    for src in source_files:
        print(f"\nProcessing: {src}")
        rows = generate_crops(
            src,
            args.recipe,
            max_per_source=args.max_per_source,
            custom_box=args.custom_box,
        )
        all_rows.extend(rows)

    if all_rows:
        update_keep_csv(all_rows)

        # Auto-render contact sheets for the just-generated crops
        print("\nRendering contact sheets...")
        sheets = build_contact_sheets_from_candidates()
        print(f"\n=== Done! {len(all_rows)} candidates, {len(sheets)} contact sheet(s) ===")
    else:
        print("\n  No crops generated.")


if __name__ == "__main__":
    main()
