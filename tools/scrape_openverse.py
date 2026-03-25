#!/usr/bin/env python3
"""
Scrape CC-licensed images from the Openverse API for marine species training data.

Openverse aggregates Flickr, Wikimedia Commons, iNaturalist, and other sources.
This complements the iNaturalist scraper by providing additional image diversity.

Usage:
    # Dry run — preview what would be downloaded
    python tools/scrape_openverse.py \
        --species-list tools/species-intertidal.tsv \
        --corpus dreaming-model-openverse --dry-run

    # Download up to 50 images per species (default)
    python tools/scrape_openverse.py \
        --species-list tools/species-intertidal.tsv \
        --corpus dreaming-model-openverse \
        --output ./images/openverse-raw

    # Custom per-species limit and minimum resolution
    python tools/scrape_openverse.py \
        --species-list tools/species-fish.tsv \
        --per-species 30 --min-size 768 \
        --corpus fish-model-openverse \
        --output ./images/openverse-fish-raw

API: https://api.openverse.org/v1/images/
  - No API key needed for basic use
  - Unauthenticated: 240 results max per query (~12 pages × 20), ~100 req/hour
  - License types: commercial (CC0, CC BY, CC BY-SA)
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


OPENVERSE_API = "https://api.openverse.org/v1/images/"
USER_AGENT = "SalishSeaDreaming/1.0 (https://github.com/darrenzal/salish-sea-dreaming)"

# Commercial-safe licenses for art exhibition use (artist fee = commercial)
SAFE_LICENSES = {"cc0", "by", "by-sa"}

# Openverse license codes → our provenance format
LICENSE_MAP = {
    "cc0": "cc0",
    "pdm": "cc0",          # Public Domain Mark
    "by": "cc-by",
    "by-sa": "cc-by-sa",
    "by-nc": "cc-by-nc",
    "by-nd": "cc-by-nd",
    "by-nc-sa": "cc-by-nc-sa",
    "by-nc-nd": "cc-by-nc-nd",
}

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


def api_get(params: dict) -> dict:
    """Make a GET request to the Openverse API."""
    url = f"{OPENVERSE_API}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def safe_filename(common: str, scientific: str, image_id: str, ext: str) -> str:
    """Build a filesystem-safe filename matching iNat naming convention."""
    name = common or scientific
    name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return f"{name}_{image_id}.{ext}"


def load_species_list(path: Path) -> list[dict]:
    """
    Load a curated species list from a TSV/CSV file.

    Expected columns: taxon_id, common_name, scientific_name
    (taxon_id is optional for Openverse — we search by name, not taxon_id)
    """
    species = []
    with open(path) as f:
        sample = f.read(2048)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            taxon_id = row.get("taxon_id", "").strip()
            common = row.get("common_name", "").strip()
            scientific = row.get("scientific_name", "").strip()

            species.append({
                "taxon_id": int(taxon_id) if taxon_id else None,
                "common": common,
                "scientific": scientific,
            })

    return species


def load_existing_provenance_urls() -> set[str]:
    """
    Load all image source URLs from provenance.csv for deduplication.

    Returns a set of URLs already tracked (from any source — iNat, Openverse, etc.).
    """
    repo_root = Path(__file__).resolve().parent.parent
    provenance_path = repo_root / "training-data" / "provenance.csv"
    urls = set()

    if provenance_path.exists():
        with open(provenance_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("url", "").strip()
                if url:
                    urls.add(url)

    return urls


def extract_image_id(result: dict) -> str:
    """Extract a short unique ID from an Openverse result."""
    # Openverse returns a UUID as the 'id' field
    ov_id = result.get("id", "")
    if ov_id:
        # Use last 12 chars of UUID for compact filenames
        return ov_id.replace("-", "")[-12:]
    return "unknown"


def guess_extension(url: str) -> str:
    """Guess file extension from URL."""
    path = urlparse(url).path.lower()
    if path.endswith(".png"):
        return "png"
    if path.endswith(".jpeg"):
        return "jpeg"
    if path.endswith(".webp"):
        return "webp"
    if path.endswith(".gif"):
        return "gif"
    # Default to jpg (most common)
    return "jpg"


def fetch_species_images(
    query: str,
    per_species: int,
    min_size: int,
    license_filter: bool,
    existing_urls: set[str],
) -> list[dict]:
    """
    Fetch images for a species query from Openverse.

    Paginates through results, filtering by resolution and license.
    Deduplicates against existing provenance URLs.

    Returns list of image metadata dicts.
    """
    images = []
    page = 1
    max_pages = 12  # 12 × 20 = 240 results (unauthenticated max)

    while len(images) < per_species and page <= max_pages:
        params = {
            "q": query,
            "page": page,
            "page_size": 20,
        }

        if license_filter:
            params["license_type"] = "commercial"

        try:
            data = api_get(params)
        except Exception as e:
            print(f"    Warning: API request failed (page {page}): {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for result in results:
            if len(images) >= per_species:
                break

            # Check resolution
            width = result.get("width") or 0
            height = result.get("height") or 0
            min_dim = min(width, height) if width and height else 0

            if min_size and min_dim < min_size:
                continue

            # Check license when filtering
            lic = (result.get("license") or "").lower()
            if license_filter and lic not in SAFE_LICENSES:
                continue

            # Get the actual image URL
            image_url = result.get("url", "")
            if not image_url:
                continue

            # Get the source landing page for provenance
            foreign_url = result.get("foreign_landing_url", "")

            # Deduplicate against existing provenance
            if foreign_url in existing_urls or image_url in existing_urls:
                continue

            creator = result.get("creator") or ""
            source = result.get("source") or ""
            image_id = extract_image_id(result)
            ext = guess_extension(image_url)

            images.append({
                "image_url": image_url,
                "foreign_url": foreign_url,
                "license": LICENSE_MAP.get(lic, lic),
                "creator": creator,
                "source_platform": source,
                "image_id": image_id,
                "ext": ext,
                "width": width,
                "height": height,
            })

        # Rate limit: ~100 req/hour = 1 req per 36s
        # We'll use 2s between pages as a compromise (still well within limits
        # for a single species query that uses ~12 pages max)
        time.sleep(2)
        page += 1

    return images


def upsert_provenance(manifest: list[dict], output_dir: Path, corpus: str, dry_run: bool = False):
    """
    Upsert Openverse scrape results into training-data/provenance.csv.

    Idempotency: upsert by filename. If a row with the same filename already
    exists, skip it (preserving any existing approved_for_training value).
    New filenames are appended with approved_for_training=pending.
    """
    repo_root = Path(__file__).resolve().parent.parent
    provenance_path = repo_root / "training-data" / "provenance.csv"

    # Load existing provenance rows keyed by filename
    existing = {}
    if provenance_path.exists():
        with open(provenance_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["filename"]] = row

    new_rows = []
    skipped = 0
    for m in manifest:
        filename = f"{corpus}/{m['file']}"
        source_file = f"{str(output_dir)}/{m['file']}"

        if filename in existing:
            skipped += 1
            continue

        row = {
            "filename": filename,
            "source_file": source_file,
            "source": "Openverse",
            "url": m.get("foreign_url", ""),
            "license": m.get("license", ""),
            "photographer_artist": m.get("creator", ""),
            "parent_source_file": "",
            "crop_box": "",
            "crop_recipe": "",
            "approved_for_training": "pending",
        }
        new_rows.append(row)

    if dry_run:
        print(f"\n--- Provenance dry-run: {len(new_rows)} new rows, {skipped} existing (skipped) ---")
        for row in new_rows[:20]:
            print(f"  {row['filename']}\t{row['photographer_artist']}\t{row['license']}\t{row['url']}")
        if len(new_rows) > 20:
            print(f"  ... and {len(new_rows) - 20} more")
        return

    if not new_rows:
        print(f"\n  Provenance: no new rows to add ({skipped} already exist)")
        return

    # Append new rows
    write_header = not provenance_path.exists()
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    with open(provenance_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROVENANCE_COLUMNS)
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)

    print(f"\n  Provenance: appended {len(new_rows)} new rows, {skipped} existing (skipped)")
    print(f"  File: {provenance_path}")


def scrape(
    species_list_path: Path,
    output_dir: Path,
    per_species: int,
    min_size: int,
    corpus: str,
    license_filter: bool,
    dry_run: bool,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load species list
    all_species = load_species_list(species_list_path)
    if not all_species:
        print("No species found in species list.")
        return

    print(f"  Loaded {len(all_species)} species from {species_list_path}")

    # Load existing provenance URLs for deduplication
    existing_urls = load_existing_provenance_urls()
    print(f"  Loaded {len(existing_urls)} existing URLs from provenance.csv for dedup")
    print()

    manifest = []
    total_downloaded = 0
    total_skipped_existing = 0
    shortfalls = []

    for i, sp in enumerate(all_species, 1):
        common = sp["common"]
        scientific = sp["scientific"]
        name = common or scientific

        # Query using scientific name for precision (common names are ambiguous)
        query = scientific or common
        print(f"  [{i:3d}/{len(all_species)}] {name}")
        filter_msg = " (commercial-safe only)" if license_filter else ""
        print(f"    Query: \"{query}\"{filter_msg}")

        images = fetch_species_images(
            query=query,
            per_species=per_species,
            min_size=min_size,
            license_filter=license_filter,
            existing_urls=existing_urls,
        )

        if len(images) < per_species:
            shortfalls.append((name, len(images), per_species))
            if len(images) == 0:
                print(f"    No images found")
            else:
                print(f"    Shortfall: only {len(images)}/{per_species} images found")
        else:
            print(f"    Found {len(images)} images")

        species_downloaded = 0
        for img in images:
            filename = safe_filename(common, scientific, img["image_id"], img["ext"])
            dest = output_dir / filename

            entry = {
                "common": common,
                "scientific": scientific,
                "file": filename,
                "image_url": img["image_url"],
                "foreign_url": img["foreign_url"],
                "license": img["license"],
                "creator": img["creator"],
                "source_platform": img["source_platform"],
                "width": img["width"],
                "height": img["height"],
            }

            if dest.exists():
                total_skipped_existing += 1
                manifest.append(entry)
                continue

            if dry_run:
                manifest.append(entry)
                continue

            # Download the image
            try:
                req = Request(img["image_url"], headers={"User-Agent": USER_AGENT})
                with urlopen(req, timeout=30) as resp:
                    with open(dest, "wb") as fout:
                        fout.write(resp.read())

                # Verify the file is not zero-byte
                if dest.exists() and dest.stat().st_size == 0:
                    dest.unlink()
                    print(f"      WARNING: zero-byte file removed: {filename}")
                    continue

                species_downloaded += 1
                total_downloaded += 1
                manifest.append(entry)

            except Exception as e:
                print(f"      ERROR downloading {filename}: {e}")
                if dest.exists() and dest.stat().st_size == 0:
                    dest.unlink()

            # Rate limit between downloads: ~1 req/s is safe
            time.sleep(1)

        if not dry_run and species_downloaded > 0:
            print(f"    Downloaded {species_downloaded} images")

        # Pause between species to stay within rate limits
        # ~100 req/hour = need to be conservative with pagination + downloads
        time.sleep(3)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Summary")
    print(f"{'=' * 60}")
    print(f"  Species queried:  {len(all_species)}")
    print(f"  Total in manifest: {len(manifest)}")
    if not dry_run:
        print(f"  New downloads:     {total_downloaded}")
        print(f"  Already existed:   {total_skipped_existing}")
    else:
        print(f"  (dry run — no files downloaded)")

    if shortfalls:
        print(f"\n--- Shortfalls ({len(shortfalls)} species) ---")
        for name, got, wanted in shortfalls:
            print(f"  {name}: {got}/{wanted}")

    # Write filelist.txt
    filelist_path = output_dir / "filelist.txt"
    if not dry_run:
        with open(filelist_path, "w") as f:
            f.write(f"# Openverse scrape — {len(manifest)} entries\n")
            f.write(f"# Species list: {species_list_path}\n")
            f.write(f"# Per-species: {per_species}, min-size: {min_size}\n")
            f.write(f"# Corpus: {corpus}\n")
            f.write(f"# Columns: file\tcommon\tscientific\tlicense\tcreator\turl\twidth\theight\n")
            f.write("\n")
            for m in manifest:
                f.write(
                    f"{m['file']}\t{m['common']}\t{m['scientific']}\t"
                    f"{m['license']}\t{m['creator']}\t{m['foreign_url']}\t"
                    f"{m['width']}\t{m['height']}\n"
                )
        print(f"\n  Filelist written: {filelist_path}")
    else:
        print(f"\n  Filelist: {filelist_path} (skipped — dry run)")

    # Upsert provenance
    upsert_provenance(manifest, output_dir, corpus, dry_run=dry_run)

    print(f"\n  Images directory: {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape CC-licensed images from the Openverse API for species training data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run — preview what would be downloaded
  python tools/scrape_openverse.py \\
      --species-list tools/species-intertidal.tsv \\
      --corpus dreaming-model-openverse --dry-run

  # Download intertidal species images
  python tools/scrape_openverse.py \\
      --species-list tools/species-intertidal.tsv \\
      --corpus dreaming-model-openverse \\
      --output ./images/openverse-raw

  # Fish species with custom limits
  python tools/scrape_openverse.py \\
      --species-list tools/species-fish.tsv \\
      --per-species 30 --min-size 768 \\
      --corpus fish-model-openverse \\
      --output ./images/openverse-fish-raw
        """,
    )
    parser.add_argument("--species-list", type=str, required=True, metavar="FILE",
                        help="Path to species list TSV/CSV (columns: taxon_id, common_name, scientific_name)")
    parser.add_argument("--output", default="./images/openverse-raw",
                        help="Output directory (default: ./images/openverse-raw)")
    parser.add_argument("--per-species", type=int, default=50, metavar="N",
                        help="Max images to download per species (default: 50)")
    parser.add_argument("--min-size", type=int, default=512, metavar="PX",
                        help="Minimum resolution on shortest side in px (default: 512)")
    parser.add_argument("--corpus", type=str, default="dreaming-model-openverse",
                        help="Corpus name prefix for provenance rows (default: dreaming-model-openverse)")
    parser.add_argument("--license-filter", action="store_true", default=True,
                        help="Only download CC0/CC BY/CC BY-SA images (default: on)")
    parser.add_argument("--no-license-filter", action="store_true",
                        help="Disable license filter — download all CC licenses")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be downloaded without saving files")
    args = parser.parse_args()

    # Handle license filter toggle
    license_filter = args.license_filter and not args.no_license_filter

    print(f"Openverse Image Scraper")
    print(f"  Species list: {args.species_list}")
    print(f"  Output:       {args.output}")
    print(f"  Per-species:  {args.per_species}")
    print(f"  Min size:     {args.min_size}px")
    print(f"  Corpus:       {args.corpus}")
    print(f"  License:      {'CC0, CC BY, CC BY-SA only' if license_filter else 'all CC licenses'}")
    print(f"  Dry run:      {args.dry_run}")
    print()

    scrape(
        species_list_path=Path(args.species_list),
        output_dir=Path(args.output),
        per_species=args.per_species,
        min_size=args.min_size,
        corpus=args.corpus,
        license_filter=license_filter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
