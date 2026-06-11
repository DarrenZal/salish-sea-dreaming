#!/usr/bin/env python3
"""
Decompose Austin Harry SVG pieces into atomic shapes.

For each input SVG:
  - Parse all path/circle/ellipse elements
  - Extract geometry, fill color, bbox, area, centroid
  - Render each atom as an isolated PNG (just that shape, white BG)
  - Render each atom as an "in-context" PNG (whole piece, atom highlighted)
  - Write atom_metadata.csv per piece

Output structure:
  austin-v2-ingest/decomposed/
    Nature_Cosmic_Sun/
      atom_metadata.csv
      atom_0000.png        # isolated
      atom_0000_context.png  # in-context highlight
      atom_0001.png
      ...
    Animal_Bird_Raven_Sun/
      ...

INTERNAL ONLY per Austin consent floor. These atoms are decomposition
artifacts for understanding the formline grammar; any use in a public
output requires Austin per-output OK.
"""
from __future__ import annotations
from pathlib import Path
import csv
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "track2-deterministic/source-vectors"
OUT_BASE = ROOT / "austin-v2-ingest/decomposed"

# SVG pieces to decompose (SVG-only for first pass; PDFs/PNGs need different tooling)
TARGETS = [
    "Nature_Cosmic_Sun.svg",
    "Animal_Bird_Raven_Sun.svg",
    "Animal_Salmon_Spawn_Eggs.svg",
    "Animal_Wolf_Spindle_Whorl.svg",
    "Supernatural_Human_TheCreator_Background.svg",
]

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

def parse_attr_float(elem, name, default=0.0):
    try:
        v = elem.get(name)
        if v is None:
            return default
        return float(re.sub(r'[^0-9.eE+-]', '', v))
    except (ValueError, TypeError):
        return default

def estimate_bbox_centroid(elem, tag_short: str):
    """Approximate bbox + centroid for a shape element. Returns (x, y, w, h, cx, cy, area)."""
    if tag_short == "circle":
        cx = parse_attr_float(elem, "cx")
        cy = parse_attr_float(elem, "cy")
        r = parse_attr_float(elem, "r")
        return cx - r, cy - r, 2 * r, 2 * r, cx, cy, 3.14159 * r * r
    elif tag_short == "ellipse":
        cx = parse_attr_float(elem, "cx")
        cy = parse_attr_float(elem, "cy")
        rx = parse_attr_float(elem, "rx")
        ry = parse_attr_float(elem, "ry")
        return cx - rx, cy - ry, 2 * rx, 2 * ry, cx, cy, 3.14159 * rx * ry
    elif tag_short == "rect":
        x = parse_attr_float(elem, "x")
        y = parse_attr_float(elem, "y")
        w = parse_attr_float(elem, "width")
        h = parse_attr_float(elem, "height")
        return x, y, w, h, x + w / 2, y + h / 2, w * h
    elif tag_short == "path":
        # Best-effort via svgpathtools if available
        try:
            from svgpathtools import parse_path
            d = elem.get("d", "")
            if not d:
                return 0, 0, 0, 0, 0, 0, 0
            path = parse_path(d)
            try:
                xmin, xmax, ymin, ymax = path.bbox()
            except Exception:
                # bbox can fail on some path types; fall back to point sampling
                pts = [path.point(t) for t in [i / 20 for i in range(21)]]
                xs = [p.real for p in pts]
                ys = [p.imag for p in pts]
                xmin, xmax = min(xs), max(xs)
                ymin, ymax = min(ys), max(ys)
            w = xmax - xmin
            h = ymax - ymin
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            return xmin, ymin, w, h, cx, cy, w * h  # area = bbox-area approx
        except ImportError:
            return 0, 0, 0, 0, 0, 0, 0
    elif tag_short in ("polygon", "polyline"):
        pts_str = elem.get("points", "")
        coords = re.findall(r'[-+]?\d*\.?\d+', pts_str)
        try:
            coords = [float(c) for c in coords]
            pairs = list(zip(coords[0::2], coords[1::2]))
            if not pairs:
                return 0, 0, 0, 0, 0, 0, 0
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            return xmin, ymin, xmax - xmin, ymax - ymin, (xmin + xmax) / 2, (ymin + ymax) / 2, (xmax - xmin) * (ymax - ymin)
        except (ValueError, IndexError):
            return 0, 0, 0, 0, 0, 0, 0
    return 0, 0, 0, 0, 0, 0, 0

def get_fill(elem) -> str:
    """Get fill color from element, defaulting to black."""
    fill = elem.get("fill", "").strip()
    if fill and fill != "none":
        return fill
    # Try style attr
    style = elem.get("style", "")
    m = re.search(r'fill\s*:\s*([^;]+)', style)
    if m:
        return m.group(1).strip()
    return "#000000"

def get_ancestor_transforms(elem, root) -> list[str]:
    """Walk up the tree to find all ancestor transforms. Returns list from root → elem."""
    # ElementTree doesn't have parent pointers; we built a map below in decompose_svg
    return []

def build_parent_map(root) -> dict:
    """Build a child → parent map for transform inheritance."""
    return {c: p for p in root.iter() for c in p}

def collect_transforms(elem, parent_map, root) -> list[str]:
    """Collect all transforms from root down to elem (root first, elem last)."""
    chain = []
    cur = elem
    while cur is not None and cur != root:
        t = cur.get("transform")
        if t:
            chain.append(t)
        cur = parent_map.get(cur)
    # Also root's own transform
    t = root.get("transform")
    if t:
        chain.append(t)
    return list(reversed(chain))

def make_isolated_svg(original_tree, target_elem, transforms: list[str]) -> str:
    """Build a single-element SVG containing just `target_elem` with parent transforms applied."""
    root = original_tree.getroot()
    new_root = ET.Element(f"{{{SVG_NS}}}svg", root.attrib)
    # Apply transforms by wrapping in a <g>
    parent = new_root
    for t in transforms:
        g = ET.SubElement(parent, f"{{{SVG_NS}}}g", {"transform": t})
        parent = g
    # Append the target element
    elem_copy = ET.fromstring(ET.tostring(target_elem))
    parent.append(elem_copy)
    # Serialize
    return ET.tostring(new_root, encoding="unicode")

def make_context_svg(original_tree, target_elem) -> str:
    """Build an SVG where ALL other elements are dimmed and target is highlighted."""
    root = original_tree.getroot()
    # Deep copy by re-parsing
    tree_str = ET.tostring(root, encoding="unicode")
    new_root = ET.fromstring(tree_str)
    # Find equivalent of target in new tree by traversal index
    # Simplest: rebuild target by attribute match — but attributes can collide
    # Better: walk both trees in parallel, find matching position
    orig_shapes = [e for e in root.iter() if e.tag in SHAPE_TAGS]
    new_shapes = [e for e in new_root.iter() if e.tag in SHAPE_TAGS]
    target_idx = None
    for i, e in enumerate(orig_shapes):
        if e is target_elem:
            target_idx = i
            break
    if target_idx is None:
        return ET.tostring(new_root, encoding="unicode")

    # Dim all shapes except target
    for i, e in enumerate(new_shapes):
        if i == target_idx:
            # Highlight: bright red stroke
            e.set("stroke", "#ff2266")
            e.set("stroke-width", "8")
            e.set("fill-opacity", "1")
        else:
            # Dim
            e.set("opacity", "0.20")
    return ET.tostring(new_root, encoding="unicode")

def rasterize_svg_string(svg_str: str, out_path: Path, size: int = 256) -> bool:
    """Use ImageMagick to convert SVG string → PNG."""
    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(svg_str)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["magick", "-background", "white", "-density", "150",
             tmp_path, "-resize", f"{size}x{size}", str(out_path)],
            capture_output=True, text=True, timeout=20
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    finally:
        Path(tmp_path).unlink(missing_ok=True)

def decompose_svg(svg_path: Path, out_dir: Path) -> int:
    """Decompose one SVG into atoms. Returns count of atoms extracted."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    parent_map = build_parent_map(root)

    # Collect all shape elements
    shapes = []
    for elem in root.iter():
        if elem.tag in SHAPE_TAGS:
            shapes.append((elem, SHAPE_TAGS[elem.tag]))

    if not shapes:
        print(f"  WARN: no shapes found in {svg_path.name}")
        return 0

    # Write metadata CSV
    meta_path = out_dir / "atom_metadata.csv"
    with open(meta_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "atom_id", "piece", "element_type", "fill_color",
            "bbox_x", "bbox_y", "bbox_w", "bbox_h",
            "centroid_x", "centroid_y", "area",
            "isolated_png", "context_png",
            "ai_label", "ai_confidence", "ai_reason"  # filled by labeling step
        ])
        for i, (elem, tag_short) in enumerate(shapes):
            atom_id = f"atom_{i:04d}"
            isolated_name = f"{atom_id}.png"
            context_name = f"{atom_id}_context.png"

            # Geometry
            x, y, w, h, cx, cy, area = estimate_bbox_centroid(elem, tag_short)
            fill = get_fill(elem)

            # Skip degenerate shapes (zero-area, etc.)
            if w * h < 0.5:
                continue

            # Rasterize isolated
            transforms = collect_transforms(elem, parent_map, root)
            iso_svg = make_isolated_svg(tree, elem, transforms)
            iso_ok = rasterize_svg_string(iso_svg, out_dir / isolated_name, size=256)

            # Rasterize context
            ctx_svg = make_context_svg(tree, elem)
            ctx_ok = rasterize_svg_string(ctx_svg, out_dir / context_name, size=512)

            writer.writerow([
                atom_id, svg_path.stem, tag_short, fill,
                f"{x:.2f}", f"{y:.2f}", f"{w:.2f}", f"{h:.2f}",
                f"{cx:.2f}", f"{cy:.2f}", f"{area:.2f}",
                isolated_name if iso_ok else "",
                context_name if ctx_ok else "",
                "", "", ""
            ])
    return len(shapes)

def main():
    print(f"Decomposing {len(TARGETS)} Austin SVG pieces → {OUT_BASE}/")
    print()
    for filename in TARGETS:
        svg_path = SOURCE_DIR / filename
        if not svg_path.exists():
            print(f"  SKIP: {filename} not found at {svg_path}")
            continue
        out_dir = OUT_BASE / svg_path.stem
        print(f"  Decomposing {filename}")
        n = decompose_svg(svg_path, out_dir)
        # Count actual rasterized atoms (CSV rows minus header)
        meta = out_dir / "atom_metadata.csv"
        actual = 0
        if meta.exists():
            with open(meta) as f:
                actual = sum(1 for _ in f) - 1
        print(f"    → {actual} atoms extracted (of {n} candidate shapes)")

    print()
    print(f"Done. Atoms in: {OUT_BASE}/")
    print("Next: python3 scripts/label_atoms_with_claude.py")

if __name__ == "__main__":
    main()
