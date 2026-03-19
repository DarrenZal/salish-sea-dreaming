#!/usr/bin/env python3
"""
Curate a LoRA training dataset from the Briony marine colour corpus.

Selects compositionally distinct images, deduplicates overlapping crops,
and generates style-prefix + content-tag captions for each image.

Usage:
    python scripts/curate_lora_dataset.py                    # dry-run (list selections)
    python scripts/curate_lora_dataset.py --output briony-lora  # copy + caption
"""

import argparse
import csv
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = PROJECT_ROOT / "training-data" / "briony-marine-colour"
PROVENANCE_CSV = PROJECT_ROOT / "training-data" / "provenance.csv"

STYLE_PREFIX = "brionypenn watercolor painting, soft edges, natural pigment, ecological illustration"

# Selected images with per-image content tags.
# Format: (filename_in_briony_marine_colour, content_tags)
CURATED_SET = [
    # === 12 whole-image exports ===
    ("whole-ecosystem-panorama.png",
     "coastal ecosystem, boats, octopus, split waterline view"),
    ("whole-eelgrass-closeup.png",
     "eelgrass, underwater, diver, marine restoration"),
    ("whole-salish-sea-panorama.png",
     "salish sea, whale, herring, seabirds, panoramic seascape"),
    ("whole-giant-pacific-octopus.png",
     "giant pacific octopus, underwater, coral reef, vibrant red"),
    ("whole-kelp-forest-ecosystem.png",
     "kelp forest, sea otter, orca, split waterline view"),
    ("whole-salmon-forest-cycle.png",
     "salmon, ocean, forest cycle, underwater, dramatic waves"),
    ("whole-basking-shark.png",
     "basking shark, underwater, fish, coastal split view"),
    ("whole-central-coast-estuary.png",
     "estuary, bear, forest, salmon, underwater stream"),
    ("whole-central-coast-inshore.png",
     "inshore ecosystem, orca, kelp, coastal split view"),
    ("whole-central-coast-offshore.png",
     "offshore, deep kelp forest, underwater marine life"),
    ("whole-xwaaqwum-clamdigger.png",
     "indigenous woman, clamdigger, beach, warm earth tones"),
    ("whole-alaska-iceberg.png",
     "iceberg, mountains, atmospheric landscape, loose wash"),

    # === Non-whole crops: compositionally distinct subjects ===
    ("surfbird+copy+3__center-crop__center-60pct.png",
     "surfbirds, shore rocks, delicate wash, coastal birds"),
    ("varied+thrush+and+berries+copy__center-crop__center-60pct.png",
     "varied thrush, berries, flowers, bees, botanical illustration"),
    ("image-asset__center-crop__center-60pct.png",
     "dolphins, marine mammals, pencil wash, motion, ocean"),
    ("IMG_1479__vertical-halves__left.png",
     "bear, forest detail, salmon stream, temperate rainforest"),

    # === Underwater-only bottom thirds (pure underwater compositions) ===
    ("IMG_1477__horizontal-thirds__bottom.png",
     "underwater, kelp, crabs, seafloor, marine invertebrates"),
    ("IMG_1478__horizontal-thirds__bottom.png",
     "underwater, anemones, kelp, colorful seafloor, coral"),
    ("Central+Coast+Inshore+scene_BrionyPenn__horizontal-thirds__bottom.png",
     "underwater reef, inshore marine life, kelp, anemones"),
    ("Central+Coast+Offshore+scene_BrionyPenn__horizontal-thirds__bottom.png",
     "deep underwater, offshore kelp forest, marine life"),

    # === Atmospheric washes (different technique) ===
    ("Image+2__horizontal-halves__top.png",
     "atmospheric clouds, mountains, loose watercolor wash, sky"),
    ("Image+2__horizontal-halves__bottom.png",
     "seascape, whale, rocks, atmospheric ocean, muted tones"),
]

# Exclusion reasons for documentation
EXCLUDED = {
    "Tsawoutwheelsmall+copy__center-crop__center-60pct.png": "text-heavy mandala",
    "Uplands+Wheel+smalljpeg+copy__center-crop__center-60pct.png": "text-heavy ecological wheel",
    "wintermedicinewheelwebversion+copy__center-crop__center-60pct.png": "text-heavy medicine wheel",
    "all quadrant crops (*__quadrants__*)": "redundant crops of text-heavy wheels",
    "all non-bottom horizontal-thirds": "overlap with whole images",
    "all panorama-zones except whole": "overlap with whole image",
    "IMG_1474__center-crop__center-60pct.png": "overlap with whole-giant-pacific-octopus",
    "signal-2026-02-08-070332__center-crop__center-60pct.png": "overlap with whole-basking-shark",
    "IMG_1475__horizontal-halves__*": "overlap with whole-eelgrass-closeup",
    "IMG_1476__panorama-zones__*": "overlap with whole-salish-sea-panorama",
    "Central+coast+estuary__horizontal-thirds__bottom": "very similar to central-coast-estuary whole",
}


def validate_selection():
    """Verify all selected files exist in training-data/briony-marine-colour/."""
    missing = []
    for filename, _ in CURATED_SET:
        path = TRAINING_DIR / filename
        if not path.exists():
            missing.append(filename)
    return missing


def count_source_overlap():
    """Check how many images come from the same source painting."""
    from collections import Counter
    source_map = {}
    with open(PROVENANCE_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["filename"].startswith("briony-marine-colour/"):
                fname = row["filename"].split("/", 1)[1]
                source_map[fname] = row["source_file"]

    selected_sources = []
    for filename, _ in CURATED_SET:
        src = source_map.get(filename, "UNKNOWN")
        selected_sources.append((filename, src))

    counts = Counter(src for _, src in selected_sources)
    return selected_sources, counts


def curate(output_dir: Path, dry_run: bool = False):
    """Copy selected images and write caption .txt files."""
    missing = validate_selection()
    if missing:
        print("ERROR: Missing files:")
        for m in missing:
            print(f"  {m}")
        return False

    selected_sources, source_counts = count_source_overlap()

    print(f"Curated LoRA dataset: {len(CURATED_SET)} images")
    print(f"Unique source paintings: {len(source_counts)}")
    print()

    # Check max images per source (plan says ≤2)
    over_limit = {s: c for s, c in source_counts.items() if c > 2}
    if over_limit:
        print("WARNING: >2 images from same source:")
        for src, count in over_limit.items():
            print(f"  {count}x {src.split('/')[-1]}")
        print()

    print("=== Selected images ===")
    for i, (filename, tags) in enumerate(CURATED_SET, 1):
        src = dict(selected_sources).get(filename, "?")
        caption = f"{STYLE_PREFIX}, {tags}"
        print(f"  {i:2d}. {filename}")
        print(f"      caption: {caption}")
        print(f"      source:  {src.split('/')[-1]}")
        print()

    if dry_run:
        print("DRY RUN — no files copied.")
        return True

    # Create output directory and copy files + captions
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, tags in CURATED_SET:
        src_path = TRAINING_DIR / filename
        # Use simple numbered names for cleanliness
        dst_path = output_dir / filename
        caption = f"{STYLE_PREFIX}, {tags}"

        shutil.copy2(src_path, dst_path)
        caption_path = dst_path.with_suffix(".txt")
        caption_path.write_text(caption)

    print(f"Copied {len(CURATED_SET)} images + captions to {output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Curate LoRA training dataset")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: dry-run only)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List selections without copying")
    args = parser.parse_args()

    if args.output:
        output_dir = PROJECT_ROOT / args.output
        curate(output_dir, dry_run=args.dry_run)
    else:
        curate(Path("/dev/null"), dry_run=True)


if __name__ == "__main__":
    main()
