#!/usr/bin/env python3
"""
Scrape species images from an iNaturalist guide.

Usage:
    python scrape_inaturalist_guide.py
    python scrape_inaturalist_guide.py --guide 19640 --size medium --output ./images/marine

Guide: https://www.inaturalist.org/guides/19640
       Pacific Northwest Marine Life (128 taxa)

Image sizes available: square (75px), small (240px), medium (500px), large (1024px), original
"""

import argparse
import html as html_module
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen, urlretrieve


GUIDE_URL = "https://www.inaturalist.org/guides/{guide_id}"
IMAGE_HOST = "inaturalist-open-data.s3.amazonaws.com"


def parse_species(html: str) -> list:
    """
    Extract species from guide HTML.

    Each entry has this structure (nested divs make a block-level regex unreliable):
        <div class="col-xs-3">
          <a ...><img src="...s3.amazonaws.com/photos/ID/small.jpeg" /></a>
          <h5>
            <a href="/guide_taxa/ID">Common Name</a>...
            <i>Scientific name</i>
          </h5>
        </div>

    Strategy: collect all img URLs at S3, all taxon common names, all scientific names,
    then zip them positionally — they appear in the same order.
    """
    img_urls = re.findall(
        r'src="(https://inaturalist-open-data\.s3\.amazonaws\.com/photos/[^"]+)"',
        html,
    )
    # Common names: anchor text for /guide_taxa/ links (first link per block is the image link, second is the name)
    # The name link pattern: href="/guide_taxa/ID">Name\n
    common_names = re.findall(
        r'href="/guide_taxa/\d+">\s*([^\n<]+)\s*\n',
        html,
    )
    scientific_names = re.findall(r"<i>([^<]+)</i>", html)

    # Zip: img_urls and common_names should have the same count per page
    species = []
    for i, img_url in enumerate(img_urls):
        common = html_module.unescape(common_names[i].strip()) if i < len(common_names) else "unknown"
        scientific = html_module.unescape(scientific_names[i].strip()) if i < len(scientific_names) else ""
        species.append((common, scientific, img_url))
    return species


def fetch_guide_page(guide_id: int, page: int = 1) -> str:
    url = f"https://www.inaturalist.org/guides/{guide_id}?page={page}"
    print(f"  Fetching: {url}")
    with urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_page_count(html: str) -> int:
    """Parse the pagination to find total page count."""
    # Looks for links like ?page=3 in the pagination block
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


def scrape(guide_id: int, size: str, output_dir: Path, dry_run: bool = False):
    output_dir.mkdir(parents=True, exist_ok=True)

    # Page 1 — also learn total page count
    html = fetch_guide_page(guide_id, 1)
    total_pages = find_page_count(html)
    print(f"  Guide has {total_pages} page(s)")

    all_html = [html]
    for page in range(2, total_pages + 1):
        time.sleep(0.5)  # be polite
        all_html.append(fetch_guide_page(guide_id, page))

    # Parse all pages
    species = []
    for html in all_html:
        species.extend(parse_species(html))
    print(f"\nFound {len(species)} species entries\n")

    # Download
    manifest = []
    for i, (common, scientific, img_url) in enumerate(species, 1):
        sized_url = swap_image_size(img_url, size)
        photo_id = extract_photo_id(img_url)
        ext = "jpg" if sized_url.endswith(".jpg") else "jpeg"
        filename = safe_filename(common, scientific, photo_id, ext)
        dest = output_dir / filename

        status = "exists" if dest.exists() else "download"
        if dry_run:
            status = "dry-run"

        print(f"  [{i:3d}/{len(species)}] {common:<35} {status}")
        manifest.append({"common": common, "scientific": scientific,
                          "url": sized_url, "file": filename})

        if not dry_run and not dest.exists():
            try:
                urlretrieve(sized_url, dest)
            except Exception as e:
                print(f"           ERROR: {e}")
            time.sleep(0.2)

    # Write manifest
    manifest_path = output_dir / "manifest.txt"
    with open(manifest_path, "w") as f:
        f.write(f"# iNaturalist Guide {guide_id} — {len(species)} taxa\n")
        f.write(f"# Image size: {size}\n\n")
        for m in manifest:
            f.write(f"{m['file']}\t{m['common']}\t{m['scientific']}\t{m['url']}\n")

    print(f"\nManifest written: {manifest_path}")
    print(f"Images saved to:  {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Scrape images from an iNaturalist guide")
    parser.add_argument("--guide", type=int, default=19640,
                        help="Guide ID (default: 19640 = Pacific NW Marine Life)")
    parser.add_argument("--size", default="medium",
                        choices=["square", "small", "medium", "large", "original"],
                        help="Image size to download (default: medium = 500px)")
    parser.add_argument("--output", default="./images/marine",
                        help="Output directory (default: ./images/marine)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List what would be downloaded without saving files")
    args = parser.parse_args()

    print(f"iNaturalist Guide Scraper")
    print(f"  Guide:  {args.guide}")
    print(f"  Size:   {args.size}")
    print(f"  Output: {args.output}")
    print(f"  Dry run: {args.dry_run}\n")

    scrape(
        guide_id=args.guide,
        size=args.size,
        output_dir=Path(args.output),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
