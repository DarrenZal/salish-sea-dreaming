#!/usr/bin/env python3
"""
Balance the dreaming model corpus from multiple QC'd sources.

Reads all tags CSVs, applies the balance rule (no group >35%),
prioritizes by strength (hero > usable > borderline), and outputs
a final selection list.

Usage:
    python scripts/balance_corpus.py --target 1200 --max-group-pct 35
    python scripts/balance_corpus.py --target 1000 --heroes-only
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

# Tag files and their group assignments
TAG_SOURCES = [
    # (tags_csv, group_name, source_dir_for_images)
    ("training-data/review/tags-intertidal-prefilter.csv", "intertidal", "images/intertidal-raw"),
    ("training-data/review/tags-openverse.csv", "intertidal", "images/openverse-raw"),
    ("training-data/review/tags-bears.csv", "bears", None),  # dir in filename
    ("training-data/review/tags-birds.csv", "birds", None),
    ("training-data/review/tags-fish-openverse.csv", "fish", None),
    ("training-data/review/tags-whales.csv", "whales", None),
    ("training-data/review/tags-orca-frames.csv", "whales", "images/orca-wikimedia"),
    ("training-data/review/tags-targeted.csv", None, None),  # mixed groups — auto-assign below
]

# Fish iNat (already approved, no tags CSV — include all)
FISH_INAT_DIR = "training-data/fish-model"

STRENGTH_ORDER = {"hero": 0, "usable": 1, "borderline": 2, "": 3}


SPECIES_GROUP_MAP = {
    "octopus": "intertidal", "kelp": "intertidal", "eelgrass": "intertidal",
    "eagle": "birds", "orca": "whales",
}


def auto_group(species_name):
    """Infer group from species name for mixed-source tag files."""
    name_lower = species_name.lower()
    for key, grp in SPECIES_GROUP_MAP.items():
        if key in name_lower:
            return grp
    return "intertidal"  # default


def load_tags(csv_path, group, default_dir):
    """Load kept images from a tags CSV."""
    entries = []
    if not os.path.exists(csv_path):
        print(f"  SKIP (not found): {csv_path}")
        return entries
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("filename", "").strip()
            if not fn:
                continue
            species = row.get("species", "").strip()
            assigned_group = group if group else auto_group(species)
            entries.append({
                "filename": fn,
                "species": species,
                "group": assigned_group,
                "interface": row.get("interface", ""),
                "composition": row.get("composition", ""),
                "bridge": row.get("bridge", ""),
                "strength": row.get("strength", "usable").strip().lower(),
                "source_csv": csv_path,
                "source_dir": default_dir,
            })
    print(f"  Loaded {len(entries)} from {csv_path} (group={group or 'auto'})")
    return entries


def load_fish_inat(fish_dir):
    """Load approved fish images (no tags CSV, all are approved)."""
    entries = []
    if not os.path.isdir(fish_dir):
        print(f"  SKIP (not found): {fish_dir}")
        return entries
    for fn in sorted(os.listdir(fish_dir)):
        if fn.lower().endswith((".jpg", ".jpeg", ".png")):
            # Parse species from filename
            parts = fn.replace(".jpg", "").replace(".jpeg", "").replace(".png", "").split("_")
            num_idx = next((i for i, p in enumerate(parts) if p.isdigit()), len(parts))
            species = "_".join(parts[:num_idx])
            entries.append({
                "filename": fn,
                "species": species,
                "group": "fish",
                "interface": "underwater",
                "composition": "single_dominant",
                "bridge": "",
                "strength": "usable",  # No strength tags, treat as usable
                "source_csv": "fish-model",
                "source_dir": fish_dir,
            })
    print(f"  Loaded {len(entries)} from {fish_dir} (group=fish, all approved)")
    return entries


INTERFACE_PRIORITY = {
    "underwater": 0,
    "intertidal": 1,
    "surface_split": 2,
    "wading": 3,
    "swimming": 3,
    "terrestrial_near_water": 4,
    "shoreline": 4,
    "aerial_below_sky": 5,
    "aerial_above_water": 5,
    "air-water": 5,
    "surface": 6,
    "cliff": 6,
    "perched-water-bg": 7,
    "": 8,
}


def balance(entries, target, max_group_pct, heroes_only=False):
    """Select images using interface-weighted priority.

    Selection order:
    1. ALL bridge images (ecological transitions — always included)
    2. ALL whale and bear images (rare, every one matters)
    3. Heroes by interface priority (underwater > intertidal > surface_split > surface)
    4. Usables by interface priority
    5. Borderlines if still needed (unlikely)

    Group cap still applies to prevent any one group from overwhelming.
    """

    if heroes_only:
        entries = [e for e in entries if e["strength"] == "hero"]
        print(f"\n  Heroes only: {len(entries)} available")

    # Sort by: bridge first, then strength, then interface priority
    # Species that are ecologically critical but underrepresented — always include
    PRIORITY_SPECIES = {
        "octopus", "giant_pacific_octopus", "kelp", "bull_kelp",
        "eagle", "bald_eagle", "eelgrass", "orca",
    }

    def sort_key(e):
        has_bridge = 0 if e.get("bridge", "").strip() else 1
        is_rare = 0 if e["group"] in ("whales", "bears") else 1
        is_priority = 0 if any(p in e["species"].lower() for p in PRIORITY_SPECIES) else 1
        strength = STRENGTH_ORDER.get(e["strength"], 3)
        interface = INTERFACE_PRIORITY.get(e.get("interface", ""), 8)
        return (has_bridge, is_rare, is_priority, strength, interface)

    entries.sort(key=sort_key)

    by_group = defaultdict(list)
    for e in entries:
        by_group[e["group"]].append(e)

    max_per_group = int(target * max_group_pct / 100)

    # Stats
    bridge_count = sum(1 for e in entries if e.get("bridge", "").strip())
    rare_count = sum(1 for e in entries if e["group"] in ("whales", "bears"))

    print(f"\n  Balance constraints: target={target}, max_per_group={max_per_group} ({max_group_pct}%)")
    print(f"  Bridge images (always included): {bridge_count}")
    print(f"  Rare groups (whales+bears, always included): {rare_count}")
    print(f"\n  Available per group:")
    for g in sorted(by_group):
        heroes = sum(1 for e in by_group[g] if e["strength"] == "hero")
        usable = sum(1 for e in by_group[g] if e["strength"] == "usable")
        underwater = sum(1 for e in by_group[g] if e.get("interface", "") == "underwater")
        intertidal = sum(1 for e in by_group[g] if e.get("interface", "") == "intertidal")
        surface = sum(1 for e in by_group[g] if e.get("interface", "") == "surface")
        bridges = sum(1 for e in by_group[g] if e.get("bridge", "").strip())
        print(f"    {g:15s}: {len(by_group[g]):5d} ({heroes}h/{usable}u) "
              f"[uw:{underwater} it:{intertidal} sf:{surface} br:{bridges}]")

    # Selection with group cap
    selected = []
    selected_fns = set()
    group_counts = defaultdict(int)

    for e in entries:
        if len(selected) >= target:
            break
        if e["filename"] in selected_fns:
            continue
        if group_counts[e["group"]] >= max_per_group:
            continue
        selected.append(e)
        selected_fns.add(e["filename"])
        group_counts[e["group"]] += 1

    return selected


def main():
    parser = argparse.ArgumentParser(description="Balance dreaming model corpus")
    parser.add_argument("--target", type=int, default=1200, help="Target corpus size")
    parser.add_argument("--max-group-pct", type=int, default=35, help="Max percentage per group")
    parser.add_argument("--heroes-only", action="store_true", help="Only include hero-strength images")
    parser.add_argument("--output", default="training-data/review/balanced-selection.csv",
                       help="Output selection CSV")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing")
    args = parser.parse_args()

    print("Loading all QC'd images...")
    all_entries = []

    # Load fish iNat (no tags CSV)
    all_entries.extend(load_fish_inat(FISH_INAT_DIR))

    # Load all tagged sources
    for csv_path, group, default_dir in TAG_SOURCES:
        all_entries.extend(load_tags(csv_path, group, default_dir))

    # Deduplicate by filename
    seen = set()
    unique = []
    for e in all_entries:
        if e["filename"] not in seen:
            seen.add(e["filename"])
            unique.append(e)
    print(f"\nTotal unique images: {len(unique)} (deduped from {len(all_entries)})")

    # Balance
    selected = balance(unique, args.target, args.max_group_pct, args.heroes_only)

    # Summary
    print(f"\n=== SELECTED: {len(selected)} images ===")
    by_group = defaultdict(int)
    by_strength = defaultdict(int)
    by_species = defaultdict(int)
    for e in selected:
        by_group[e["group"]] += 1
        by_strength[e["strength"]] += 1
        by_species[e["species"]] += 1

    print("\nBy group:")
    for g in sorted(by_group):
        pct = by_group[g] / len(selected) * 100
        print(f"  {g:15s}: {by_group[g]:5d} ({pct:.1f}%)")

    print("\nBy strength:")
    for s in ["hero", "usable", "borderline"]:
        print(f"  {s:15s}: {by_strength.get(s, 0):5d}")

    print(f"\nSpecies count: {len(by_species)}")
    print("\nTop 15 species:")
    for sp, count in sorted(by_species.items(), key=lambda x: -x[1])[:15]:
        print(f"  {sp:30s}: {count:4d}")

    if not args.dry_run:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "filename", "species", "group", "interface", "composition",
                "bridge", "strength", "source_csv", "source_dir"
            ])
            writer.writeheader()
            writer.writerows(selected)
        print(f"\nWritten to {args.output}")
    else:
        print("\n(dry-run — no file written)")


if __name__ == "__main__":
    main()
