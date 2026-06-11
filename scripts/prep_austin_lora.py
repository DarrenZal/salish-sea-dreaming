"""
Prep Austin Harry's reference portfolio for SD 1.5 LoRA training on TELUS.

Walks austin-reference/, filters images by size + project relevance, scale +
center-crops to 512x512, writes paired .txt captions (kohya/diffusers
convention), and bundles to austin-reference/pilot-512/.

Outputs:
  austin-reference/pilot-512/{project}__{n:03d}.jpg
  austin-reference/pilot-512/{project}__{n:03d}.txt
  austin-reference/pilot-512.tar.gz       (for upload)
  austin-reference/pilot-512.manifest.csv (per-image provenance)

Internal-use only. Outputs are gitignored.
"""
from __future__ import annotations

import csv
import json
import shutil
import tarfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1] / "austin-reference"
OUT_DIR = ROOT / "pilot-512"
TAR_OUT = ROOT / "pilot-512.tar.gz"
MANIFEST_CSV = ROOT / "pilot-512.manifest.csv"

# Min size — anything smaller than 512 on shortest side gets upscaled (worse
# quality but kept; the training set values variety over uniform quality).
# Discard only if shortest < 256 (genuine low-res / icon).
MIN_SHORTEST_DISCARD = 256
TARGET = 512

# Project-folder → caption suffix. Style anchor token `austinharrystyle`
# precedes every caption so the LoRA learns to associate that token with
# Austin's visual register.
ANCHOR = "austinharrystyle, Coast Salish design"

PROJECT_CAPTIONS = {
    "salish-spirit":      "Salish Spirit at VanLive Robson LED display, formline orca and salmon",
    "westridge-elementary": "Westridge Elementary orca and salmon school commission",
    "whitecaps":          "Whitecaps FC Sinulhka two-headed serpent crest, sports identity design",
    "kwikwi":             "KwiKwi Thunderbird design",
    "mst-justice-centre": "MST Justice Centre plant series, chocolate lilies red cedar stinging nettle wapato",
    "cheeilth-marvel":    "Chee'ilth Marvel character design with Squamish Lil'wat cultural partnership",
    "kalkalilh-banff":    "Kalkalilh Banff projection installation",
    "nelson-elementary":  "Nelson Elementary commission",
    "arcteryx":           "Arc'teryx apparel collaboration",
    "vch":                "Vancouver Coastal Health commission",
    "studio-home":        "Austin Harry studio work in progress",
    "portfolio-index":    "Austin Harry portfolio piece",
}
# Folders to skip entirely (not design content)
SKIP_FOLDERS = {"media", "about"}


def caption_for(project: str) -> str:
    suffix = PROJECT_CAPTIONS.get(project, "Austin Harry contemporary Coast Salish artwork")
    return f"{ANCHOR}, {suffix}"


def square_crop_512(src: Path, dst: Path) -> tuple[int, int, int]:
    """Open `src`, scale-and-center-crop to 512x512 RGB JPG, save to `dst`.
    Returns (src_w, src_h, action_code) where action_code:
      0 = native ≥ 512 (downscale + crop)
      1 = native < 512 (upscale + crop; lower fidelity)
      2 = discarded (too small)
    """
    with Image.open(src) as im:
        # EXIF orient + flatten alpha to white background
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1] if "A" in im.mode else None)
            im = bg
        else:
            im = im.convert("RGB")

        w, h = im.size
        short = min(w, h)
        if short < MIN_SHORTEST_DISCARD:
            return w, h, 2

        # Scale so shortest side = TARGET
        scale = TARGET / short
        new_w, new_h = int(round(w * scale)), int(round(h * scale))
        im = im.resize((new_w, new_h), Image.LANCZOS)
        # Center-crop to TARGET x TARGET
        left = (new_w - TARGET) // 2
        top = (new_h - TARGET) // 2
        im = im.crop((left, top, left + TARGET, top + TARGET))

        im.save(dst, "JPEG", quality=92, optimize=True)
        return w, h, 0 if short >= TARGET else 1


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(f"austin-reference/ not found at {ROOT}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    rows: list[dict] = []
    project_counts: dict[str, int] = {}

    for project_dir in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in {"pilot-512"}):
        project = project_dir.name
        if project in SKIP_FOLDERS:
            print(f"  [SKIP] {project}/ — not design content")
            continue

        idx = 0
        for img_path in sorted(project_dir.iterdir()):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            try:
                dst_name = f"{project}__{idx:03d}.jpg"
                dst = OUT_DIR / dst_name
                w, h, action = square_crop_512(img_path, dst)
                if action == 2:
                    dst.unlink(missing_ok=True)
                    rows.append({
                        "project": project, "src": img_path.name, "src_w": w, "src_h": h,
                        "action": "discard_too_small", "out": "",
                    })
                    continue
                # Caption sidecar
                caption = caption_for(project)
                (OUT_DIR / f"{project}__{idx:03d}.txt").write_text(caption + "\n")
                rows.append({
                    "project": project, "src": img_path.name, "src_w": w, "src_h": h,
                    "action": "upscale_crop" if action == 1 else "scale_crop",
                    "out": dst_name,
                })
                idx += 1
            except Exception as e:
                rows.append({
                    "project": project, "src": img_path.name, "src_w": 0, "src_h": 0,
                    "action": f"error: {type(e).__name__}: {e}", "out": "",
                })
        project_counts[project] = idx
        print(f"  [{project}] kept {idx} images")

    # Write manifest CSV
    with MANIFEST_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["project", "src", "src_w", "src_h", "action", "out"])
        w.writeheader()
        w.writerows(rows)

    total_kept = sum(project_counts.values())
    total_discarded = sum(1 for r in rows if r["action"].startswith("discard"))
    print()
    print(f"=== SUMMARY ===")
    print(f"  total in: {len(rows)}  kept: {total_kept}  discarded: {total_discarded}")
    print(f"  caption anchor token: {ANCHOR!r}")

    # Tarball for upload
    print(f"\n  Packing {TAR_OUT.name}…")
    with tarfile.open(TAR_OUT, "w:gz") as tar:
        for f in sorted(OUT_DIR.iterdir()):
            tar.add(f, arcname=f.name)
    size_mb = TAR_OUT.stat().st_size / 1e6
    print(f"  Done. tarball size: {size_mb:.1f} MB")

    # Drop a meta json so the pod knows what it's got
    meta = {
        "anchor_token": ANCHOR.split(",")[0].strip(),
        "image_count": total_kept,
        "target_size": TARGET,
        "projects": project_counts,
        "captions": {p: caption_for(p) for p in project_counts},
    }
    (OUT_DIR / "_pilot_meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
