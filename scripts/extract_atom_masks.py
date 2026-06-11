#!/usr/bin/env python3
"""
Extract path-geometry-based alpha masks for decomposed atoms.

Per Task #56: decomposition pipeline must produce reliable masks for
light-colored atoms (Bee wings = cream RGB ≈ (254, 253, 248)) where the
default "color on white BG" rendering makes the atom invisible.

Approach: rebuild the SVG with each target atom's fill FORCED to black
+ stroke=none, render with `-background none` for transparent BG. Result:
black-on-transparent silhouette regardless of original fill color. The
alpha channel is the mask.

Does NOT touch existing atom_NNNN.png (color-preserving isolated render
used by labeling pipeline + contact sheets). ADDS atom_NNNN_mask.png as
new file. Optionally updates atom_metadata.csv to add mask_png column.

Acceptance per operator brief:
  1. Bee wing atoms produce non-empty masks
  2. Existing dark atoms still work (their color-preserving PNGs unchanged)
  3. Output remains compatible with current catalog pipeline (new files only)
  4. (separate script) Rebuild Bee atom contact sheet after fix
  5. (separate script) Make one diagnostic showing old-vs-new masks for wing atoms
  6. No new animation videos rendered (this fix is foundational only)

Usage:
  python3 scripts/extract_atom_masks.py --piece Animal_Insect_Bee
  python3 scripts/extract_atom_masks.py --all
"""
from __future__ import annotations
from pathlib import Path
import argparse
import csv
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import shutil

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "track2-deterministic/source-vectors"
OUT_BASE = ROOT / "austin-v2-ingest/decomposed"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

SHAPE_TAGS = {
    f"{{{SVG_NS}}}path": "path",
    f"{{{SVG_NS}}}circle": "circle",
    f"{{{SVG_NS}}}ellipse": "ellipse",
    f"{{{SVG_NS}}}rect": "rect",
    f"{{{SVG_NS}}}polygon": "polygon",
    f"{{{SVG_NS}}}polyline": "polyline",
}

# Reuse helpers from existing decompose script
sys.path.insert(0, str(ROOT / "scripts"))
from decompose_austin_pieces import (
    build_parent_map, collect_transforms, estimate_bbox_centroid
)


def make_mask_svg(original_tree, target_elem, transforms: list[str]) -> str:
    """Build single-element SVG with target's fill FORCED to black.

    Strips: fill (color), stroke, opacity, style — all replaced.
    Keeps: path/rect/circle geometry, parent transforms.
    Result rendered with transparent BG = alpha-only mask.
    """
    root = original_tree.getroot()
    # Preserve root's viewBox + width/height
    new_root = ET.Element(f"{{{SVG_NS}}}svg", root.attrib)
    parent = new_root
    for t in transforms:
        g = ET.SubElement(parent, f"{{{SVG_NS}}}g", {"transform": t})
        parent = g
    # Copy target element + force black fill, kill stroke + style
    elem_copy = ET.fromstring(ET.tostring(target_elem))
    elem_copy.set("fill", "#000000")
    elem_copy.set("fill-opacity", "1")
    elem_copy.set("stroke", "none")
    elem_copy.set("opacity", "1")
    if "style" in elem_copy.attrib:
        del elem_copy.attrib["style"]
    parent.append(elem_copy)
    return ET.tostring(new_root, encoding="unicode")


def rasterize_mask(svg_str: str, out_path: Path, size: int = 256) -> bool:
    """Render SVG to PNG with TRANSPARENT background.

    Result: black-on-transparent silhouette of the target geometry.
    Alpha channel is the mask.
    """
    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(svg_str)
        tmp_path = f.name
    try:
        # -background none gives transparent BG
        result = subprocess.run(
            ["magick", "-background", "none", "-density", "150",
             tmp_path, "-resize", f"{size}x{size}", str(out_path)],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0:
            print(f"    magick stderr: {result.stderr[-200:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        return False
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def extract_masks_for_piece(piece_name: str) -> tuple[int, int]:
    """Extract masks for one piece. Returns (n_attempted, n_success)."""
    svg_path = SOURCE_DIR / f"{piece_name}.svg"
    if not svg_path.exists():
        print(f"  SVG not found: {svg_path}")
        return 0, 0

    out_dir = OUT_BASE / piece_name
    if not out_dir.exists():
        print(f"  Decomposed dir not found: {out_dir}")
        return 0, 0

    csv_path = out_dir / "atom_metadata.csv"
    if not csv_path.exists():
        print(f"  Metadata CSV not found: {csv_path}")
        return 0, 0

    tree = ET.parse(svg_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    # Iterate shapes in same order decompose_austin_pieces.py did
    shapes = [(e, SHAPE_TAGS[e.tag]) for e in root.iter() if e.tag in SHAPE_TAGS]
    # Filter degenerate per same logic
    valid_shapes = []
    for elem, tag_short in shapes:
        x, y, w, h, cx, cy, area = estimate_bbox_centroid(elem, tag_short)
        if w * h < 0.5:
            continue
        valid_shapes.append((elem, tag_short))

    print(f"  {piece_name}: {len(valid_shapes)} atoms to mask")

    n_success = 0
    for i, (elem, tag_short) in enumerate(valid_shapes):
        atom_id = f"atom_{i:04d}"
        mask_path = out_dir / f"{atom_id}_mask.png"

        transforms = collect_transforms(elem, parent_map, root)
        mask_svg = make_mask_svg(tree, elem, transforms)
        if rasterize_mask(mask_svg, mask_path, size=256):
            n_success += 1

        if (i + 1) % 25 == 0:
            print(f"    {i+1}/{len(valid_shapes)}")

    # Update CSV: add mask_png column if not present
    # Read existing CSV; tolerate rows with extra/malformed fields
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        existing_headers = reader.fieldnames or []
        existing_rows = []
        for row in reader:
            # Drop the None key that DictReader inserts when a row has extra columns
            row.pop(None, None)
            existing_rows.append(row)

    if "mask_png" not in existing_headers:
        new_headers = existing_headers + ["mask_png"]
        backup = csv_path.with_suffix(".csv.pre_mask_backup")
        shutil.copy2(csv_path, backup)
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=new_headers, extrasaction="ignore")
            writer.writeheader()
            for row in existing_rows:
                row["mask_png"] = f"{row['atom_id']}_mask.png"
                writer.writerow(row)
        print(f"  Added mask_png column; backup at {backup.name}")
    else:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=existing_headers, extrasaction="ignore")
            writer.writeheader()
            for row in existing_rows:
                row["mask_png"] = f"{row['atom_id']}_mask.png"
                writer.writerow(row)
        print(f"  Refreshed mask_png column values")

    return len(valid_shapes), n_success


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", help="Piece name (without .svg)")
    ap.add_argument("--all", action="store_true",
                    help="Process all decomposed pieces")
    args = ap.parse_args()

    if args.all:
        pieces = [d.name for d in OUT_BASE.iterdir() if d.is_dir()]
    elif args.piece:
        pieces = [args.piece]
    else:
        print("Provide --piece <name> or --all")
        sys.exit(1)

    total_attempted = 0
    total_success = 0
    for piece in pieces:
        print(f"\n==== {piece} ====")
        att, succ = extract_masks_for_piece(piece)
        total_attempted += att
        total_success += succ

    print(f"\n==== Summary ====")
    print(f"  Total attempted: {total_attempted}")
    print(f"  Total successful: {total_success}")
    if total_attempted != total_success:
        print(f"  ⚠ {total_attempted - total_success} masks failed")


if __name__ == "__main__":
    main()
