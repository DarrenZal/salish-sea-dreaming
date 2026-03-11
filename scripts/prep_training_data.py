#!/usr/bin/env python3
"""
Salish Sea Dreaming - StyleGAN2-ada Training Data Preparation

Master preprocessing script that reads approved images from a provenance manifest,
resizes and center-crops them to square format, and outputs to training directories.

No augmentation is applied — ADA handles this during training.

Usage:
    # Process all approved images at default 512px
    python scripts/prep_training_data.py

    # Process at 1024px resolution
    python scripts/prep_training_data.py --resolution 1024

    # Show what would be processed without writing files
    python scripts/prep_training_data.py --dry-run

    # Only run validation checks (no processing)
    python scripts/prep_training_data.py --validate-only
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
TRAINING_DIR = os.path.join(REPO_ROOT, "training-data")
PROVENANCE_CSV = os.path.join(TRAINING_DIR, "provenance.csv")

# Minimum image counts per corpus before a warning is emitted
MINIMUMS = {
    "briony-marine-colour": 40,
    "marine-photo-base": 500,
}


def load_provenance(csv_path):
    """Load provenance.csv and return rows where approved_for_training=yes."""
    if not os.path.exists(csv_path):
        print(f"Error: Provenance manifest not found: {csv_path}")
        sys.exit(1)

    approved = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("approved_for_training", "").strip().lower() == "yes":
                approved.append(row)
    return approved


def corpus_name(filename):
    """Extract the corpus name (first path component) from a filename field."""
    return Path(filename).parts[0] if Path(filename).parts else "unknown"


def apply_exif_orientation(img):
    """Apply EXIF orientation tag so phone photos display correctly."""
    try:
        exif = img.getexif()
        orientation = exif.get(274)  # EXIF orientation tag ID
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError):
        pass
    return img


def apply_crop_box(img, crop_box_str):
    """Apply a crop box from provenance before center-crop-resize.

    crop_box_str is a JSON array string like "[0,0,2500,1064]"
    representing [left, top, right, bottom] in PIL coordinates.
    Returns the cropped image, or the original if no valid crop_box.
    """
    if not crop_box_str or not crop_box_str.strip():
        return img
    try:
        box = json.loads(crop_box_str)
        if len(box) == 4:
            return img.crop(tuple(box))
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return img


def center_crop_resize(img, target_size):
    """Resize with aspect-preserving center-crop to a square.

    1. Scale so the shorter side equals target_size (LANCZOS).
    2. Crop the center of the longer side to produce a target_size x target_size image.
    """
    w, h = img.size
    scale = target_size / min(w, h)
    new_w = round(w * scale)
    new_h = round(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center-crop to square
    left = (new_w - target_size) // 2
    top = (new_h - target_size) // 2
    img = img.crop((left, top, left + target_size, top + target_size))
    return img


def validate_provenance(approved_rows):
    """Check output directories for images that lack provenance entries.

    Returns a list of orphan file paths (relative to training-data/).
    """
    # Build set of expected output filenames
    expected = {row["filename"].strip() for row in approved_rows}

    orphans = []
    if not os.path.isdir(TRAINING_DIR):
        return orphans

    # Directories to skip during orphan check (QC artifacts, not training data)
    skip_dirs = {"review"}

    for dirpath, dirnames, filenames in os.walk(TRAINING_DIR):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, TRAINING_DIR)
            # Skip the manifest itself and non-image files
            if rel == "provenance.csv" or not fname.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp")
            ):
                continue
            if rel not in expected:
                orphans.append(rel)
    return orphans


def process(args):
    approved = load_provenance(PROVENANCE_CSV)
    if not approved:
        print("No approved rows found in provenance.csv")
        return

    # --- Counts per corpus ---
    corpus_counts = {}
    skipped = 0
    processed = 0

    for row in approved:
        filename = row["filename"].strip()
        source_file = row["source_file"].strip()
        src_path = os.path.normpath(os.path.join(REPO_ROOT, source_file))
        dst_path = os.path.normpath(os.path.join(TRAINING_DIR, filename))
        corp = corpus_name(filename)

        if not os.path.exists(src_path):
            print(f"  WARN: source missing, skipping: {source_file}")
            skipped += 1
            continue

        corpus_counts[corp] = corpus_counts.get(corp, 0) + 1

        if args.dry_run:
            print(f"  [dry-run] {source_file} -> training-data/{filename}")
            processed += 1
            continue

        # Create output directory
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)

        try:
            img = Image.open(src_path)
            img = apply_exif_orientation(img)
            img = img.convert("RGB")
            crop_box = row.get("crop_box", "").strip()
            img = apply_crop_box(img, crop_box)
            img = center_crop_resize(img, args.resolution)
            img.save(dst_path, quality=95)
            processed += 1
        except Exception as e:
            print(f"  WARN: failed to process {source_file}: {e}")
            skipped += 1
            corpus_counts[corp] = corpus_counts.get(corp, 0) - 1

    # --- Summary ---
    print()
    print("=" * 50)
    print(f"  Resolution : {args.resolution}x{args.resolution}")
    print(f"  Processed  : {processed}")
    print(f"  Skipped    : {skipped}")
    print("-" * 50)
    print(f"  {'Corpus':<30} {'Count':>6}")
    print("-" * 50)
    for corp in sorted(corpus_counts):
        count = corpus_counts[corp]
        flag = ""
        if corp in MINIMUMS and count < MINIMUMS[corp]:
            flag = f"  ** below minimum ({MINIMUMS[corp]})"
        print(f"  {corp:<30} {count:>6}{flag}")
    print("=" * 50)

    # --- Orphan check ---
    orphans = validate_provenance(approved)
    if orphans:
        print()
        print(f"WARNING: {len(orphans)} image(s) in training-data/ lack provenance entries:")
        for o in sorted(orphans):
            print(f"  {o}")


def validate_only(args):
    approved = load_provenance(PROVENANCE_CSV)

    # Corpus counts from manifest
    corpus_counts = {}
    missing_sources = []
    for row in approved:
        filename = row["filename"].strip()
        source_file = row["source_file"].strip()
        src_path = os.path.normpath(os.path.join(REPO_ROOT, source_file))
        corp = corpus_name(filename)
        corpus_counts[corp] = corpus_counts.get(corp, 0) + 1
        if not os.path.exists(src_path):
            missing_sources.append(source_file)

    print("Validation Report")
    print("=" * 50)
    print(f"  Approved rows : {len(approved)}")
    print(f"  Missing sources : {len(missing_sources)}")
    print("-" * 50)
    print(f"  {'Corpus':<30} {'Count':>6}")
    print("-" * 50)
    for corp in sorted(corpus_counts):
        count = corpus_counts[corp]
        flag = ""
        if corp in MINIMUMS and count < MINIMUMS[corp]:
            flag = f"  ** below minimum ({MINIMUMS[corp]})"
        print(f"  {corp:<30} {count:>6}{flag}")
    print("=" * 50)

    if missing_sources:
        print()
        print("Missing source files:")
        for s in sorted(missing_sources):
            print(f"  {s}")

    orphans = validate_provenance(approved)
    if orphans:
        print()
        print(f"WARNING: {len(orphans)} image(s) in training-data/ lack provenance entries:")
        for o in sorted(orphans):
            print(f"  {o}")

    if not missing_sources and not orphans:
        print()
        print("All checks passed.")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare training data for StyleGAN2-ada from provenance manifest."
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=512,
        choices=[512, 1024],
        help="Target square resolution in pixels (default: 512)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without writing any files",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation checks (no processing)",
    )
    args = parser.parse_args()

    print(f"Repo root: {REPO_ROOT}")
    print(f"Provenance: {PROVENANCE_CSV}")
    print()

    if args.validate_only:
        validate_only(args)
    else:
        process(args)


if __name__ == "__main__":
    main()
