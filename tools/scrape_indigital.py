#!/usr/bin/env python3
"""
Scrape image references from Austin Harry / INDIGITAL portfolio pages
(https://www.indigitaldesign.ca) for personal-reference use only.

Output: ./austin-reference/<page-slug>/<filename> + manifest.json with provenance.

The folder is gitignored. Consent to be confirmed retroactively with Austin
on the first call. If Austin objects, delete austin-reference/.

Usage:
    python tools/scrape_indigital.py --dry-run    # list URLs without downloading
    python tools/scrape_indigital.py              # full pull (idempotent — sha256-skip)
    python tools/scrape_indigital.py --format 1500w  # smaller variant

Pages crawled are listed in PAGES below. Only Squarespace CDN image URLs
are fetched; YouTube / Instagram links are recorded under
manifest['external_video'] / manifest['external_social'] but not downloaded.
"""

import argparse
import hashlib
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


SITE_ROOT = "https://www.indigitaldesign.ca"
CDN_HOST = "images.squarespace-cdn.com"

# (slug, page-path) — slug becomes the subfolder under austin-reference/
PAGES = [
    ("studio-home", "/"),
    ("about", "/about"),
    ("media", "/media"),
    ("portfolio-index", "/portfolio"),
    ("salish-spirit", "/portfolio/project-salishspirit"),
    ("whitecaps", "/portfolio/whitecaps-fc-indigenous-celebration-game"),
    ("arcteryx", "/portfolio/arcteryx"),
    ("mst-justice-centre", "/portfolio/project-one-ephnc-ml4je"),
    ("vch", "/portfolio/vancouver-coastal-health"),
    ("westridge-elementary", "/portfolio/westridge-elementary-school"),
    ("nelson-elementary", "/portfolio/nelson-elementary"),
    ("cheeilth-marvel", "/portfolio/cheeilth"),
    ("kalkalilh-banff", "/portfolio/kalkalilh-banff-centre-residency"),
    ("kwikwi", "/portfolio/kwikwi-projects"),
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Re-parses each page; never trusts a stale URL list. The patterns capture
# Squarespace CDN URLs from <img src=>, <source srcset=>, <meta og:image=>,
# data-src= and data-image= attributes.
RE_IMG_SRC = re.compile(
    r'(?:src|data-src|data-image|content)=["\']((?:https?:)?//images\.squarespace-cdn\.com/[^"\']+)["\']',
    re.IGNORECASE,
)
RE_SRCSET = re.compile(r'srcset=["\']([^"\']+)["\']', re.IGNORECASE)
RE_YOUTUBE = re.compile(r'(?:https?://)?(?:www\.)?(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))[\w\-]+')
RE_INSTAGRAM = re.compile(r'https?://(?:www\.)?instagram\.com/[^"\'\s<>)]+')


def fetch(url: str, timeout: int = 30) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def normalize_cdn_url(url: str, format_param: str) -> str:
    """Strip any existing ?format=... and apply our requested format.

    Handles protocol-relative URLs (//images.squarespace-cdn.com/...) by
    prepending https:.
    """
    url = html.unescape(url)
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    # Drop existing query, replace with chosen format
    return urlunparse(parsed._replace(query=f"format={format_param}"))


def cdn_filename(url: str) -> str:
    """Derive a stable filename from a Squarespace CDN URL.

    Squarespace paths look like
    /content/v1/<site>/<asset-id>/<original-filename>.jpg, sometimes followed
    by transform tokens. We take the last meaningful path segment.
    """
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return "image.jpg"
    last = parts[-1]
    # Strip any embedded transform suffix (e.g. "+v1+...")
    last = last.split("?")[0]
    if not re.search(r"\.(jpg|jpeg|png|gif|webp|svg)$", last, re.IGNORECASE):
        last = last + ".jpg"
    return last


def parse_page(html_text: str, format_param: str) -> tuple[set[str], set[str], set[str]]:
    """Return (cdn_image_urls, youtube_urls, instagram_urls) found on a page."""
    images: set[str] = set()
    for m in RE_IMG_SRC.finditer(html_text):
        images.add(normalize_cdn_url(m.group(1), format_param))
    for m in RE_SRCSET.finditer(html_text):
        # srcset is a comma-separated list of "url widthDescriptor"
        for entry in m.group(1).split(","):
            url = entry.strip().split(" ")[0]
            if CDN_HOST in url:
                images.add(normalize_cdn_url(url, format_param))
    youtube = set(RE_YOUTUBE.findall(html_text))
    instagram = set(RE_INSTAGRAM.findall(html_text))
    return images, youtube, instagram


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="list URLs, do not download")
    ap.add_argument(
        "--format",
        default="2500w",
        help="Squarespace ?format= param (default: 2500w; alternates: 1500w, 1000w, original)",
    )
    ap.add_argument(
        "--output",
        default="austin-reference",
        help="output directory (default: austin-reference; gitignored)",
    )
    ap.add_argument("--sleep", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args()

    out_root = Path(args.output)
    if not args.dry_run:
        out_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source": SITE_ROOT,
        "format": args.format,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "consent_status": "personal-reference, not redistributed; retroactive ask pending",
        "pages": [],
        "images": [],
        "external_video": [],
        "external_social": [],
    }

    seen_images: set[str] = set()
    seen_video: set[str] = set()
    seen_social: set[str] = set()

    for slug, path in PAGES:
        url = urljoin(SITE_ROOT, path)
        print(f"\n== {slug}  {url}", file=sys.stderr)
        try:
            body = fetch(url).decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  ! fetch failed: {e}", file=sys.stderr)
            manifest["pages"].append({"slug": slug, "url": url, "status": f"error: {e}"})
            continue

        images, youtube, instagram = parse_page(body, args.format)

        manifest["pages"].append({
            "slug": slug,
            "url": url,
            "status": "ok",
            "image_count": len(images),
        })

        for v in youtube:
            if v not in seen_video:
                seen_video.add(v)
                manifest["external_video"].append({"page": slug, "url": v})
        for s in instagram:
            if s not in seen_social:
                seen_social.add(s)
                manifest["external_social"].append({"page": slug, "url": s})

        for img_url in sorted(images):
            if img_url in seen_images:
                continue
            seen_images.add(img_url)

            filename = cdn_filename(img_url)
            local_path = out_root / slug / filename

            if args.dry_run:
                print(f"  [dry-run] {filename:50s}  {img_url}")
                manifest["images"].append({
                    "page": slug,
                    "url": img_url,
                    "local": str(local_path),
                    "status": "dry-run",
                })
                continue

            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Idempotent: skip if already present and non-empty
            if local_path.exists() and local_path.stat().st_size > 0:
                digest = sha256_of(local_path)
                manifest["images"].append({
                    "page": slug,
                    "url": img_url,
                    "local": str(local_path),
                    "size_bytes": local_path.stat().st_size,
                    "sha256": digest,
                    "status": "cached",
                })
                print(f"  cached    {filename}")
                continue

            try:
                data = fetch(img_url)
            except Exception as e:
                print(f"  ! image fetch failed: {img_url}: {e}", file=sys.stderr)
                manifest["images"].append({
                    "page": slug,
                    "url": img_url,
                    "local": str(local_path),
                    "status": f"error: {e}",
                })
                continue

            local_path.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            manifest["images"].append({
                "page": slug,
                "url": img_url,
                "local": str(local_path),
                "size_bytes": len(data),
                "sha256": digest,
                "status": "fetched",
            })
            print(f"  fetched   {filename}  ({len(data):,} bytes)")
            time.sleep(args.sleep)

        time.sleep(args.sleep)

    if not args.dry_run:
        (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))

    fetched = sum(1 for i in manifest["images"] if i.get("status") == "fetched")
    cached = sum(1 for i in manifest["images"] if i.get("status") == "cached")
    errors = sum(1 for i in manifest["images"] if str(i.get("status", "")).startswith("error"))
    print(
        f"\nSummary: {len(manifest['images'])} unique images "
        f"(fetched={fetched}, cached={cached}, errors={errors}), "
        f"{len(manifest['external_video'])} videos, "
        f"{len(manifest['external_social'])} social links",
        file=sys.stderr,
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
