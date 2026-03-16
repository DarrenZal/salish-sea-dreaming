#!/usr/bin/env python3
"""
Scrape species images from an iNaturalist guide, with optional per-taxon
observation downloads via the iNaturalist API.

Usage:
    # Basic guide scrape (one image per species)
    python scrape_inaturalist_guide.py
    python scrape_inaturalist_guide.py --guide 19640 --size medium --output ./images/marine

    # Per-taxon: download N research-grade photos per species via observations API
    python scrape_inaturalist_guide.py --per-taxon 10 --size large --output ./images/marine

    # Use a curated species list instead of (or in addition to) a guide
    python scrape_inaturalist_guide.py --species-list species.tsv --per-taxon 20

    # Species list only (no guide), with provenance tracking
    python scrape_inaturalist_guide.py --guide 0 --species-list tools/salish-sea-species.tsv \
        --per-taxon 15 --size large --output ./images/marine-base-raw --provenance

    # Dry run with provenance preview
    python scrape_inaturalist_guide.py --guide 0 --species-list tools/salish-sea-species.tsv \
        --per-taxon 15 --size large --output ./images/marine-base-raw --provenance --dry-run

Guide: https://www.inaturalist.org/guides/19640
       Pacific Northwest Marine Life (128 taxa)

Image sizes available: square (75px), small (240px), medium (500px), large (1024px), original
"""

import argparse
import csv
import html as html_module
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen, urlretrieve


GUIDE_URL = "https://www.inaturalist.org/guides/{guide_id}"
IMAGE_HOST = "inaturalist-open-data.s3.amazonaws.com"
INAT_API = "https://api.inaturalist.org/v1"

# Commercial-safe licenses for art exhibition use (artist fee = commercial)
SAFE_LICENSES = {"cc0", "cc-by", "cc-by-sa"}


def parse_species(html: str) -> list:
    """
    Extract species from guide HTML by parsing per-block.

    Each species lives in a <div class="col-xs-3"> block containing:
    - An <img> tag with the S3 photo URL
    - An <a href="/guide_taxa/ID"> link whose text is the common name
      (some species have no common name — the link text is <i>Scientific</i>)
    - An <i> tag with the scientific name (inside a <div class="quiet">)

    We split on col-xs-3 boundaries and extract all three fields from each
    block, preventing positional drift between lists.
    """
    # Split HTML at each species block boundary
    blocks = re.split(r'<div class="col-xs-3">', html)

    species = []
    for block in blocks:
        # Must contain an S3 image URL to be a species block
        img_match = re.search(
            r'src="(https://inaturalist-open-data\.s3\.amazonaws\.com/photos/[^"]+)"',
            block,
        )
        if not img_match:
            continue

        img_url = img_match.group(1)

        # There are TWO <a href="/guide_taxa/ID"> links per block:
        # 1. The thumbnail: <a ...><img src="..." /></a>
        # 2. The name: <a href="/guide_taxa/ID">Common Name</a>
        # We need the second one (name link), which does NOT contain an <img> tag.
        taxa_links = re.findall(
            r'href="/guide_taxa/\d+">(.*?)</a>',
            block,
            re.DOTALL,
        )

        common = ""
        scientific = ""

        # Find the name link (the one without <img)
        name_link_text = None
        for link_content in taxa_links:
            if "<img" not in link_content:
                name_link_text = link_content.strip()
                break

        if name_link_text:
            # Check if the link text is just an <i> tag (no common name)
            italic_in_link = re.match(r"<i>([^<]+)</i>", name_link_text)
            if italic_in_link:
                # No common name — the italic text IS the scientific name
                scientific = html_module.unescape(italic_in_link.group(1).strip())
            else:
                # Normal case: link text is the common name
                # Strip any trailing <sup> references
                common = re.sub(r"<sup>.*", "", name_link_text, flags=re.DOTALL).strip()
                common = re.sub(r"<[^>]+>", "", common).strip()  # strip any remaining tags
                common = html_module.unescape(common)

        # Extract scientific name from the <div class="quiet"><small><i>...</i> block
        # This is separate from any <i> inside the link
        sci_match = re.search(
            r'<div class="quiet">\s*<small>\s*<i>([^<]+)</i>',
            block,
            re.DOTALL,
        )
        if sci_match:
            scientific = html_module.unescape(sci_match.group(1).strip())

        species.append((common, scientific, img_url))

    return species


def extract_taxon_id_from_guide(html: str) -> dict:
    """
    Extract taxon IDs from guide HTML by parsing guide_taxa detail links.

    Returns dict mapping (common_name, scientific_name) -> taxon_id.
    The guide_taxa pages contain the actual iNaturalist taxon_id needed for API calls.
    """
    # We'd need to fetch individual guide_taxa pages to get taxon IDs.
    # Instead, we can use the iNaturalist API to look up taxon IDs by name.
    return {}


def fetch_guide_page(guide_id: int, page: int = 1) -> str:
    url = f"https://www.inaturalist.org/guides/{guide_id}?page={page}"
    print(f"  Fetching: {url}")
    with urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_page_count(html: str) -> int:
    """Parse the pagination to find total page count."""
    pages = re.findall(r"\?page=(\d+)", html)
    return max((int(p) for p in pages), default=1)


def swap_image_size(url: str, size: str) -> str:
    """Replace 'small'/'square'/etc. in the S3 URL with the requested size."""
    return re.sub(r"/(square|small|medium|large|original)\.", f"/{size}.", url)


def safe_filename(common: str, scientific: str, photo_id: str, ext: str) -> str:
    """Build a filesystem-safe filename."""
    name = common or scientific
    name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return f"{name}_{photo_id}.{ext}"


def extract_photo_id(url: str) -> str:
    m = re.search(r"/photos/(\d+)/", url)
    return m.group(1) if m else "unknown"


# ---------------------------------------------------------------------------
# iNaturalist API helpers for --per-taxon
# ---------------------------------------------------------------------------

def api_get(endpoint: str, params: dict) -> dict:
    """Make a GET request to the iNaturalist API v1."""
    url = f"{INAT_API}/{endpoint}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "SalishSeaDreaming/1.0"})
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_taxon_id(name: str) -> int | None:
    """Look up a taxon ID by scientific or common name."""
    try:
        data = api_get("taxa", {"q": name, "per_page": 1})
        if data.get("results"):
            return data["results"][0]["id"]
    except Exception as e:
        print(f"    Warning: taxon lookup failed for '{name}': {e}")
    return None


def fetch_taxon_photos(
    taxon_id: int,
    n: int,
    size: str,
    license_filter: bool = False,
) -> list[dict]:
    """
    Fetch up to N research-grade observation photos for a taxon.

    Sampling policy:
    - Order by votes (community quality signal) for best images first
    - One photo per observation (the default/first photo)
    - Skip duplicate user_ids to maximize diversity
    - Paginate until N unique samples collected or results exhausted
    """
    photos = []
    seen_users = set()
    page = 1
    per_page = 200  # max allowed by API

    while len(photos) < n:
        try:
            data = api_get("observations", {
                "taxon_id": taxon_id,
                "photos": "true",
                "per_page": per_page,
                "page": page,
                "quality_grade": "research",
                "order_by": "votes",
                "order": "desc",
            })
        except Exception as e:
            print(f"    Warning: API request failed (page {page}): {e}")
            break

        results = data.get("results", [])
        if not results:
            break  # no more results

        for obs in results:
            if len(photos) >= n:
                break

            user_id = obs.get("user", {}).get("id")
            if user_id in seen_users:
                continue  # skip duplicate users
            seen_users.add(user_id)

            obs_photos = obs.get("photos", [])
            if not obs_photos:
                continue

            photo = obs_photos[0]  # first/default photo
            photo_url = photo.get("url", "")
            if not photo_url:
                continue

            # Skip non-commercial-safe licenses when filter is active
            if license_filter:
                license_code = (photo.get("license_code") or "").lower()
                if license_code not in SAFE_LICENSES:
                    continue

            # iNaturalist API returns URLs with "square" size — swap to requested
            photo_url = re.sub(r"/square\.", f"/{size}.", photo_url)
            # Also handle "small" format
            photo_url = re.sub(r"/small\.", f"/{size}.", photo_url)

            photos.append({
                "url": photo_url,
                "photo_id": photo.get("id", "unknown"),
                "observation_id": obs.get("id"),
                "user_login": obs.get("user", {}).get("login", "unknown"),
                "license": photo.get("license_code", "unknown"),
            })

        # Check if we've exhausted all results
        total = data.get("total_results", 0)
        if page * per_page >= total:
            break
        page += 1
        time.sleep(1)  # be polite to the API

    return photos


def load_species_list(path: Path) -> list[dict]:
    """
    Load a curated species list from a TSV/CSV file.

    Expected columns: taxon_id, common_name, scientific_name
    (taxon_id is optional — will be looked up if missing)
    """
    species = []
    with open(path) as f:
        # Auto-detect delimiter
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


# ---------------------------------------------------------------------------
# Main scrape logic
# ---------------------------------------------------------------------------

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


def upsert_provenance(manifest: list[dict], output_dir: Path, corpus: str, dry_run: bool = False):
    """Upsert iNaturalist scrape results into training-data/provenance.csv.

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
        obs_id = m.get("observation_id", "")
        filename = f"{corpus}/{m['file']}"
        source_file = f"{str(output_dir)}/{m['file']}"

        if filename in existing:
            skipped += 1
            continue

        url = f"https://www.inaturalist.org/observations/{obs_id}" if obs_id else ""

        row = {
            "filename": filename,
            "source_file": source_file,
            "source": "iNaturalist",
            "url": url,
            "license": m.get("license", ""),
            "photographer_artist": m.get("observer", ""),
            "parent_source_file": "",
            "crop_box": "",
            "crop_recipe": "",
            "approved_for_training": "pending",
        }
        new_rows.append(row)

    if dry_run:
        print(f"\n--- Provenance dry-run: {len(new_rows)} new rows, {skipped} existing (skipped) ---")
        for row in new_rows:
            print(f"  {row['filename']}\t{row['photographer_artist']}\t{row['license']}\t{row['url']}")
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
    guide_id: int,
    size: str,
    output_dir: Path,
    dry_run: bool = False,
    per_taxon: int = 0,
    species_list_path: Path | None = None,
    provenance: bool = False,
    corpus: str = "marine-photo-base",
    license_filter: bool = False,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect species from guide and/or species list
    # Each entry: (common, scientific, img_url_or_None, taxon_id_or_None)
    all_species = []

    if guide_id:
        # Page 1 — also learn total page count
        html = fetch_guide_page(guide_id, 1)
        total_pages = find_page_count(html)
        print(f"  Guide has {total_pages} page(s)")

        all_html = [html]
        for page in range(2, total_pages + 1):
            time.sleep(0.5)  # be polite
            all_html.append(fetch_guide_page(guide_id, page))

        # Parse all pages — guide entries have no pre-known taxon_id
        for html in all_html:
            for common, scientific, img_url in parse_species(html):
                all_species.append((common, scientific, img_url, None))
        print(f"\nFound {len(all_species)} species from guide\n")

    # Merge species list if provided
    if species_list_path:
        extra = load_species_list(species_list_path)
        print(f"  Loaded {len(extra)} species from {species_list_path}")
        for sp in extra:
            all_species.append((sp["common"], sp["scientific"], None, sp["taxon_id"]))

    if not all_species:
        print("No species found. Check guide ID or species list.")
        return

    # --------------- Guide-image download (one per species) ---------------
    manifest = []
    if not per_taxon:
        # Original behavior: download the single guide image per species
        for i, (common, scientific, img_url, _tid) in enumerate(all_species, 1):
            if not img_url:
                print(f"  [{i:3d}/{len(all_species)}] {common or scientific:<35} skip (no guide image)")
                continue

            sized_url = swap_image_size(img_url, size)
            photo_id = extract_photo_id(img_url)
            ext = "jpg" if sized_url.endswith(".jpg") else "jpeg"
            filename = safe_filename(common, scientific, photo_id, ext)
            dest = output_dir / filename

            status = "exists" if dest.exists() else "download"
            if dry_run:
                status = "dry-run"

            print(f"  [{i:3d}/{len(all_species)}] {common or scientific:<35} {scientific:<35} {status}")
            manifest.append({"common": common, "scientific": scientific,
                              "url": sized_url, "file": filename})

            if not dry_run and not dest.exists():
                try:
                    urlretrieve(sized_url, dest)
                except Exception as e:
                    print(f"           ERROR: {e}")
                time.sleep(0.2)

    # --------------- Per-taxon observation download ---------------
    if per_taxon:
        print(f"\n--- Per-taxon mode: up to {per_taxon} photos per species ---\n")
        shortfalls = []

        for i, (common, scientific, _, known_tid) in enumerate(all_species, 1):
            name = common or scientific
            print(f"  [{i:3d}/{len(all_species)}] {name}")

            # Use pre-known taxon ID from species list, or look up via API
            taxon_id = known_tid
            if not taxon_id:
                lookup_name = scientific or common
                taxon_id = lookup_taxon_id(lookup_name)
                if not taxon_id and common and scientific:
                    taxon_id = lookup_taxon_id(common)

            if not taxon_id:
                print(f"    Could not find taxon ID for '{lookup_name}' — skipping")
                shortfalls.append((name, 0, per_taxon))
                continue

            filter_msg = " (CC-safe only)" if license_filter else ""
            print(f"    Taxon ID: {taxon_id} — fetching up to {per_taxon} photos{filter_msg}...")
            photos = fetch_taxon_photos(taxon_id, per_taxon, size, license_filter=license_filter)

            if len(photos) < per_taxon:
                shortfalls.append((name, len(photos), per_taxon))
                if len(photos) < per_taxon:
                    print(f"    Shortfall: only {len(photos)}/{per_taxon} unique photos found")

            for photo in photos:
                photo_id = str(photo["photo_id"])
                url = photo["url"]
                ext = "jpg" if ".jpg" in url else "jpeg"
                filename = safe_filename(common, scientific, photo_id, ext)
                dest = output_dir / filename

                status = "exists" if dest.exists() else "download"
                if dry_run:
                    status = "dry-run"

                manifest.append({
                    "common": common,
                    "scientific": scientific,
                    "url": url,
                    "file": filename,
                    "observer": photo.get("user_login", ""),
                    "license": photo.get("license", ""),
                    "observation_id": photo.get("observation_id", ""),
                })

                if not dry_run and not dest.exists():
                    try:
                        req = Request(url, headers={"User-Agent": "SalishSeaDreaming/1.0"})
                        with urlopen(req, timeout=30) as resp:
                            with open(dest, "wb") as fout:
                                fout.write(resp.read())
                    except Exception as e:
                        print(f"      ERROR downloading {filename}: {e}")
                        if dest.exists() and dest.stat().st_size == 0:
                            dest.unlink()  # remove zero-byte file
                    time.sleep(0.3)

            time.sleep(1)  # pause between taxa

        if shortfalls:
            print(f"\n--- Shortfalls ({len(shortfalls)} taxa) ---")
            for name, got, wanted in shortfalls:
                print(f"  {name}: {got}/{wanted}")

    # Write manifest
    manifest_path = output_dir / "manifest.txt"
    with open(manifest_path, "w") as f:
        if per_taxon:
            f.write(f"# iNaturalist Per-Taxon — {len(manifest)} entries\n")
            f.write(f"# Image size: {size}\n")
            f.write(f"# Per-taxon: {per_taxon}\n")
            f.write(f"# Columns: file, common, scientific, url, observer, license, observation_id\n")
            f.write("\n")
            for m in manifest:
                obs_id = m.get("observation_id", "")
                observer = m.get("observer", "")
                lic = m.get("license", "")
                f.write(f"{m['file']}\t{m['common']}\t{m['scientific']}\t{m['url']}\t{observer}\t{lic}\t{obs_id}\n")
        else:
            f.write(f"# iNaturalist Guide {guide_id} — {len(manifest)} entries\n")
            f.write(f"# Image size: {size}\n")
            f.write("\n")
            for m in manifest:
                f.write(f"{m['file']}\t{m['common']}\t{m['scientific']}\t{m['url']}\n")

    print(f"\nManifest written: {manifest_path}")
    print(f"Total entries:    {len(manifest)}")
    print(f"Images saved to:  {output_dir}/")

    # Upsert provenance if requested (only meaningful for per-taxon mode)
    if provenance and per_taxon:
        upsert_provenance(manifest, output_dir, corpus, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape images from an iNaturalist guide",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic guide scrape
  python scrape_inaturalist_guide.py --dry-run

  # Download 10 research-grade photos per species (large size for training)
  python scrape_inaturalist_guide.py --per-taxon 10 --size large

  # Use a curated species list with provenance tracking
  python scrape_inaturalist_guide.py --guide 0 --species-list tools/salish-sea-species.tsv \\
      --per-taxon 15 --size large --output ./images/marine-base-raw --provenance

  # Dry run with provenance preview (prints rows, doesn't write provenance.csv)
  python scrape_inaturalist_guide.py --guide 0 --species-list tools/salish-sea-species.tsv \\
      --per-taxon 15 --size large --output ./images/marine-base-raw --provenance --dry-run
        """,
    )
    parser.add_argument("--guide", type=int, default=19640,
                        help="Guide ID (default: 19640 = Pacific NW Marine Life)")
    parser.add_argument("--size", default="medium",
                        choices=["square", "small", "medium", "large", "original"],
                        help="Image size to download (default: medium = 500px)")
    parser.add_argument("--output", default="./images/marine",
                        help="Output directory (default: ./images/marine)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List what would be downloaded without saving files")
    parser.add_argument("--per-taxon", type=int, default=0, metavar="N",
                        help="Download N research-grade photos per species via observations API")
    parser.add_argument("--species-list", type=str, default=None, metavar="FILE",
                        help="Path to curated species list (TSV/CSV with taxon_id, common_name, scientific_name)")
    parser.add_argument("--provenance", action="store_true",
                        help="Upsert download metadata into training-data/provenance.csv (per-taxon mode only)")
    parser.add_argument("--corpus", type=str, default="marine-photo-base",
                        help="Corpus name prefix for provenance rows (default: marine-photo-base)")
    parser.add_argument("--license-filter", action="store_true",
                        help="Only download CC0/CC BY/CC BY-SA images (commercial-safe)")
    args = parser.parse_args()

    print(f"iNaturalist Guide Scraper")
    print(f"  Guide:  {args.guide}")
    print(f"  Size:   {args.size}")
    print(f"  Output: {args.output}")
    print(f"  Dry run: {args.dry_run}")
    if args.per_taxon:
        print(f"  Per-taxon: {args.per_taxon}")
    if args.species_list:
        print(f"  Species list: {args.species_list}")
    if args.provenance:
        print(f"  Provenance: enabled (corpus: {args.corpus})")
    if args.license_filter:
        print(f"  License filter: CC0, CC BY, CC BY-SA only")
    print()

    scrape(
        guide_id=args.guide,
        size=args.size,
        output_dir=Path(args.output),
        dry_run=args.dry_run,
        per_taxon=args.per_taxon,
        species_list_path=Path(args.species_list) if args.species_list else None,
        provenance=args.provenance,
        corpus=args.corpus,
        license_filter=args.license_filter,
    )


if __name__ == "__main__":
    main()
