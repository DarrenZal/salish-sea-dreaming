#!/usr/bin/env python3
"""
Backfill license information for existing provenance rows by querying the
iNaturalist API.

For each row with an empty or unknown license, extracts the photo_id from the
filename (format: Species_Name_PHOTOID.ext) and queries the iNat observations
API to retrieve the license_code.

Optionally marks non-commercial-safe rows as approved_for_training=no.

Usage:
    # Dry run — show what would change
    python scripts/backfill_licenses.py --dry-run

    # Backfill licenses only (don't change approval status)
    python scripts/backfill_licenses.py

    # Backfill licenses AND mark non-CC-safe rows as not approved
    python scripts/backfill_licenses.py --purge-unsafe

    # Only process rows for a specific corpus
    python scripts/backfill_licenses.py --corpus fish-model --purge-unsafe
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
PROVENANCE_CSV = os.path.join(REPO_ROOT, "training-data", "provenance.csv")
INAT_API = "https://api.inaturalist.org/v1"

SAFE_LICENSES = {"cc0", "cc-by", "cc-by-sa"}

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


def extract_photo_id(filename: str) -> str | None:
    """Extract photo_id from filename like 'Species_Name_12345678.jpg'."""
    basename = os.path.basename(filename)
    m = re.search(r"_(\d+)\.[a-z]+$", basename, re.IGNORECASE)
    return m.group(1) if m else None


def extract_observation_id(url: str) -> str | None:
    """Extract observation ID from iNat URL like https://www.inaturalist.org/observations/12345."""
    m = re.search(r"/observations/(\d+)", url or "")
    return m.group(1) if m else None


def api_get(endpoint: str, params: dict) -> dict:
    """Make a GET request to the iNaturalist API v1."""
    from urllib.parse import urlencode
    url = f"{INAT_API}/{endpoint}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "SalishSeaDreaming/1.0"})
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_license_by_observation(obs_id: str) -> str | None:
    """Look up the license of the first photo in an observation."""
    try:
        data = api_get("observations", {"id": obs_id, "per_page": 1})
        results = data.get("results", [])
        if results:
            photos = results[0].get("photos", [])
            if photos:
                return (photos[0].get("license_code") or "").lower() or None
    except Exception as e:
        print(f"    API error for obs {obs_id}: {e}")
    return None


def lookup_license_by_photo(photo_id: str) -> str | None:
    """Look up license by searching observations that contain this photo_id.

    The iNat API doesn't have a direct /photos/:id endpoint, so we search
    observations with the photo_id parameter.
    """
    try:
        data = api_get("observations", {"photo_id": photo_id, "per_page": 1})
        results = data.get("results", [])
        if results:
            photos = results[0].get("photos", [])
            for photo in photos:
                if str(photo.get("id")) == str(photo_id):
                    return (photo.get("license_code") or "").lower() or None
            # Fallback: return first photo's license
            if photos:
                return (photos[0].get("license_code") or "").lower() or None
    except Exception as e:
        print(f"    API error for photo {photo_id}: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Backfill license data in provenance.csv from iNaturalist API"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without modifying provenance.csv")
    parser.add_argument("--purge-unsafe", action="store_true",
                        help="Set approved_for_training=no for non-CC-safe rows")
    parser.add_argument("--corpus", type=str, default=None,
                        help="Only process rows for this corpus prefix")
    args = parser.parse_args()

    if not os.path.exists(PROVENANCE_CSV):
        print(f"Error: {PROVENANCE_CSV} not found")
        sys.exit(1)

    # Load all rows
    with open(PROVENANCE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    print(f"Loaded {len(all_rows)} provenance rows")

    # Identify rows needing backfill
    needs_backfill = []
    for i, row in enumerate(all_rows):
        if row.get("source", "").strip() != "iNaturalist":
            continue
        if args.corpus and not row["filename"].startswith(f"{args.corpus}/"):
            continue
        license_val = row.get("license", "").strip().lower()
        if not license_val or license_val == "unknown":
            needs_backfill.append(i)

    print(f"Rows needing license backfill: {len(needs_backfill)}")
    if args.corpus:
        print(f"Corpus filter: {args.corpus}")

    if not needs_backfill and not args.purge_unsafe:
        print("Nothing to do.")
        return

    # Backfill licenses via API
    updated = 0
    failed = 0
    for count, idx in enumerate(needs_backfill, 1):
        row = all_rows[idx]
        filename = row["filename"]
        url = row.get("url", "")

        # Try observation ID from URL first (faster, more reliable)
        obs_id = extract_observation_id(url)
        license_code = None

        if obs_id:
            license_code = lookup_license_by_observation(obs_id)

        # Fallback to photo_id lookup
        if not license_code:
            photo_id = extract_photo_id(filename)
            if photo_id:
                license_code = lookup_license_by_photo(photo_id)

        if license_code:
            print(f"  [{count:3d}/{len(needs_backfill)}] {filename}: {license_code}")
            if not args.dry_run:
                all_rows[idx]["license"] = license_code
            updated += 1
        else:
            photo_id = extract_photo_id(filename)
            print(f"  [{count:3d}/{len(needs_backfill)}] {filename}: FAILED (photo_id={photo_id}, obs_id={obs_id})")
            failed += 1

        # Rate limit: ~1 req/sec
        time.sleep(1.0)

    print(f"\nBackfill complete: {updated} updated, {failed} failed")

    # Purge unsafe if requested
    purged = 0
    if args.purge_unsafe:
        for i, row in enumerate(all_rows):
            if args.corpus and not row["filename"].startswith(f"{args.corpus}/"):
                continue
            if row.get("source", "").strip() != "iNaturalist":
                continue
            license_val = row.get("license", "").strip().lower()
            if license_val and license_val not in SAFE_LICENSES:
                if row.get("approved_for_training", "").strip().lower() in ("yes", "pending"):
                    if args.dry_run:
                        print(f"  [purge] {row['filename']}: {license_val} -> approved_for_training=no")
                    else:
                        all_rows[i]["approved_for_training"] = "no"
                    purged += 1

        print(f"\nPurged (marked not approved): {purged} non-CC-safe rows")

    # Summary: count CC-safe vs not
    if args.corpus:
        corpus_rows = [r for r in all_rows if r["filename"].startswith(f"{args.corpus}/")]
    else:
        corpus_rows = [r for r in all_rows if r.get("source", "").strip() == "iNaturalist"]

    safe = sum(1 for r in corpus_rows if r.get("license", "").strip().lower() in SAFE_LICENSES)
    unsafe = sum(1 for r in corpus_rows if r.get("license", "").strip().lower() and r.get("license", "").strip().lower() not in SAFE_LICENSES)
    unknown = sum(1 for r in corpus_rows if not r.get("license", "").strip() or r.get("license", "").strip().lower() == "unknown")
    approved = sum(1 for r in corpus_rows if r.get("approved_for_training", "").strip().lower() == "yes")

    print(f"\nLicense summary{f' ({args.corpus})' if args.corpus else ''}:")
    print(f"  CC-safe (cc0/cc-by/cc-by-sa): {safe}")
    print(f"  Unsafe (cc-by-nc etc):         {unsafe}")
    print(f"  Unknown/empty:                 {unknown}")
    print(f"  Approved for training:         {approved}")

    # Write updated provenance
    if not args.dry_run and (updated > 0 or purged > 0):
        # Backup first
        backup_path = PROVENANCE_CSV + ".bak"
        shutil.copy2(PROVENANCE_CSV, backup_path)
        print(f"\nBackup: {backup_path}")

        with open(PROVENANCE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=PROVENANCE_COLUMNS)
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)
        print(f"Updated: {PROVENANCE_CSV}")
    elif args.dry_run:
        print("\n[DRY RUN] No changes written.")


if __name__ == "__main__":
    main()
