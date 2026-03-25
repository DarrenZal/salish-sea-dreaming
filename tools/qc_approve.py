#!/usr/bin/env python3
"""
Batch QC approve/reject for iNaturalist training images.

Reads a reject list (training-data/review/rejects.csv) and updates
provenance.csv: rejected images get approved_for_training=no,
all other pending iNat images get approved_for_training=yes.

Usage:
    # Preview changes (default)
    python tools/qc_approve.py --dry-run

    # Apply changes (writes .bak backup first)
    python tools/qc_approve.py --apply
"""

import argparse
import csv
import os
import shutil
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
TRAINING_DIR = os.path.join(REPO_ROOT, "training-data")
PROVENANCE_CSV = os.path.join(TRAINING_DIR, "provenance.csv")
REJECTS_CSV = os.path.join(TRAINING_DIR, "review", "rejects.csv")


def load_rejects(path):
    """Load reject list and return dict of source_file -> reason."""
    if not os.path.exists(path):
        print(f"Error: Reject list not found: {path}")
        sys.exit(1)

    rejects = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sf = row["source_file"].strip()
            reason = row.get("reason", "").strip()
            rejects[sf] = reason
    return rejects


def species_from_filename(source_file):
    """Extract species name from source_file path like images/marine-base-raw/Pacific_Herring_12345.jpg"""
    basename = os.path.basename(source_file)
    # Split on last underscore (before the iNat ID)
    parts = basename.rsplit("_", 1)
    if len(parts) >= 1:
        return parts[0]
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Batch approve/reject iNaturalist training images based on QC review."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing (default mode)",
    )
    group.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to provenance.csv (creates .bak backup first)",
    )
    parser.add_argument(
        "--corpus",
        type=str,
        default=None,
        help="Only process rows whose filename starts with CORPUS/ (e.g. whale-model)",
    )
    parser.add_argument(
        "--rejects-file",
        type=str,
        default=None,
        help="Path to rejects CSV (default: training-data/review/rejects.csv)",
    )
    args = parser.parse_args()

    # Load reject list
    rejects_path = args.rejects_file if args.rejects_file else REJECTS_CSV
    rejects = load_rejects(rejects_path)
    print(f"Loaded {len(rejects)} rejects from {rejects_path}")
    print()

    # Load provenance
    if not os.path.exists(PROVENANCE_CSV):
        print(f"Error: Provenance not found: {PROVENANCE_CSV}")
        sys.exit(1)

    with open(PROVENANCE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Process only iNat + pending rows
    in_scope = 0
    approved_count = 0
    rejected_count = 0
    skipped = 0
    changes = []  # (index, old_value, new_value, source_file, reason)
    species_approved = Counter()
    species_rejected = Counter()

    for i, row in enumerate(rows):
        source = row.get("source", "").strip()
        status = row.get("approved_for_training", "").strip().lower()
        source_file = row.get("source_file", "").strip()

        # Only touch iNaturalist/Openverse + pending rows
        if source not in ("iNaturalist", "Openverse") or status != "pending":
            skipped += 1
            continue
        # Scope to corpus if specified
        if args.corpus and not row.get("filename", "").startswith(args.corpus + "/"):
            skipped += 1
            continue

        in_scope += 1
        species = species_from_filename(source_file)

        if source_file in rejects:
            new_status = "no"
            rejected_count += 1
            species_rejected[species] += 1
            reason = rejects[source_file]
            changes.append((i, "pending", "no", source_file, reason))
        else:
            new_status = "yes"
            approved_count += 1
            species_approved[species] += 1
            changes.append((i, "pending", "yes", source_file, ""))

        rows[i]["approved_for_training"] = new_status

    # Check for rejects that didn't match any provenance row
    matched_rejects = {c[3] for c in changes if c[2] == "no"}
    unmatched = set(rejects.keys()) - matched_rejects
    if unmatched:
        print(f"WARNING: {len(unmatched)} reject(s) did not match any pending iNat row:")
        for u in sorted(unmatched):
            print(f"  {u}")
        print()

    # Summary
    print("=" * 60)
    print(f"  Scope    : iNaturalist + pending")
    print(f"  In scope : {in_scope}")
    print(f"  Approved : {approved_count} (pending -> yes)")
    print(f"  Rejected : {rejected_count} (pending -> no)")
    print(f"  Skipped  : {skipped} (not in scope)")
    print(f"  Pass rate: {approved_count / in_scope * 100:.1f}%" if in_scope else "  Pass rate: N/A")
    print("=" * 60)
    print()

    # Per-species breakdown
    all_species = sorted(set(list(species_approved.keys()) + list(species_rejected.keys())))
    print(f"  {'Species':<30} {'Pass':>6} {'Reject':>8} {'Total':>7} {'Rate':>7}")
    print("-" * 65)
    for sp in all_species:
        a = species_approved.get(sp, 0)
        r = species_rejected.get(sp, 0)
        t = a + r
        rate = f"{a / t * 100:.0f}%" if t else "N/A"
        print(f"  {sp:<30} {a:>6} {r:>8} {t:>7} {rate:>7}")
    print("-" * 65)
    print()

    # List all rejects
    reject_changes = [c for c in changes if c[2] == "no"]
    if reject_changes:
        print(f"Rejected images ({len(reject_changes)}):")
        for _, _, _, sf, reason in sorted(reject_changes, key=lambda x: x[3]):
            print(f"  {sf}  -- {reason}")
        print()

    if args.dry_run:
        print("[DRY RUN] No files modified.")
        return

    # Apply mode: write backup then update
    bak_path = PROVENANCE_CSV + ".bak"
    shutil.copy2(PROVENANCE_CSV, bak_path)
    print(f"Backup written to {bak_path}")

    with open(PROVENANCE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {PROVENANCE_CSV}")
    print(f"  {approved_count} rows: pending -> yes")
    print(f"  {rejected_count} rows: pending -> no")


if __name__ == "__main__":
    main()
