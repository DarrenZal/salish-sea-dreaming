#!/usr/bin/env python3
"""
QA pass on freshly-converted SVGs vs original JPG source.

For each converted SVG:
  1. Render at 1024×1024 via ImageMagick
  2. Place side-by-side with source JPG (also at 1024×1024)
  3. Compute pixel-diff heatmap
  4. Parse SVG XML for:
     - path count
     - element types (path/rect/circle/ellipse/polygon counts)
     - fill colors present
     - any path/rect covering >80% of viewBox area (likely background rect)
  5. Produce per-piece QA panel: source | rendered | diff | stats
  6. Aggregate into single contact sheet PNG

Output to: austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001/_QA/
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageOps
import xml.etree.ElementTree as ET
import subprocess
import re
import numpy as np
import sys

ROOT = Path(__file__).resolve().parent.parent
CONVERTED = ROOT / "austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001"
TRAINING = ROOT / "austin-v2-ingest/training"
QA_DIR = CONVERTED / "_QA"

PIECES = [
    "Animal_Bird_Heron_Background",
    "Animal_Insect_Bee",
    "Animal_Deer_Background",
    "Animal_Bear_Background",
]

RENDER_SIZE = 1024


def parse_svg_stats(svg_path: Path) -> dict:
    """Count paths, elements, fills, suspicious large shapes."""
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as e:
        return {"error": f"parse failed: {e}"}
    root = tree.getroot()
    # Get viewBox
    vb = root.get("viewBox", "0 0 100 100")
    try:
        vbx, vby, vbw, vbh = [float(x) for x in vb.split()]
        vb_area = vbw * vbh
    except Exception:
        vbw, vbh, vb_area = 100, 100, 10000

    # SVG namespace
    ns = "{http://www.w3.org/2000/svg}"
    elements = {}
    fills = set()
    suspicious_big = []
    for tag in ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line"):
        items = root.iter(f"{ns}{tag}")
        ct = 0
        for el in items:
            ct += 1
            fill = el.get("fill", "")
            if fill and fill != "none":
                fills.add(fill.lower())
            # Check for rect that covers most of viewBox
            if tag == "rect":
                try:
                    rw = float(el.get("width", "0"))
                    rh = float(el.get("height", "0"))
                    if rw * rh > 0.8 * vb_area:
                        suspicious_big.append(f"<rect> w={rw:.0f} h={rh:.0f} ({rw*rh/vb_area*100:.0f}% viewBox)")
                except ValueError:
                    pass
            # Path with very large bbox is harder to estimate without rendering
        if ct > 0:
            elements[tag] = ct

    total_drawable = sum(elements.values())
    return {
        "viewbox": f"{vbw:.0f}x{vbh:.0f}",
        "elements": elements,
        "total_drawable": total_drawable,
        "fills": sorted(fills),
        "n_fills": len(fills),
        "suspicious_big": suspicious_big,
    }


def render_svg(svg_path: Path, out_path: Path, size: int = RENDER_SIZE):
    subprocess.run([
        "magick", "-background", "white", "-density", "150",
        str(svg_path), "-resize", f"{size}x{size}",
        "-gravity", "center", "-extent", f"{size}x{size}",
        str(out_path)
    ], check=True, capture_output=True)


def load_and_fit(img_path: Path, size: int) -> Image.Image:
    img = Image.open(img_path).convert("RGB")
    img = ImageOps.contain(img, (size, size), Image.LANCZOS)
    out = Image.new("RGB", (size, size), (255, 255, 255))
    out.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return out


def pixel_diff_heatmap(a: Image.Image, b: Image.Image) -> Image.Image:
    """Return a grayscale heatmap of pixel differences."""
    arr_a = np.asarray(a, dtype=np.int16)
    arr_b = np.asarray(b, dtype=np.int16)
    diff = np.abs(arr_a - arr_b).mean(axis=-1).astype(np.uint8)
    return Image.fromarray(diff, "L"), float(diff.mean()), float(diff.max())


def build_panel(piece: str, stats: dict) -> Image.Image:
    """Per-piece QA panel: source | rendered | diff heatmap | stats text."""
    svg_path = CONVERTED / f"{piece}.svg"
    jpg_path = TRAINING / f"{piece}.jpg"
    rendered_path = QA_DIR / f"{piece}_svg_rendered.png"
    diff_path = QA_DIR / f"{piece}_diff.png"

    render_svg(svg_path, rendered_path)

    source_img = load_and_fit(jpg_path, RENDER_SIZE)
    rendered_img = Image.open(rendered_path).convert("RGB")
    rendered_img = ImageOps.contain(rendered_img, (RENDER_SIZE, RENDER_SIZE), Image.LANCZOS)
    if rendered_img.size != (RENDER_SIZE, RENDER_SIZE):
        canvas = Image.new("RGB", (RENDER_SIZE, RENDER_SIZE), (255, 255, 255))
        canvas.paste(rendered_img, ((RENDER_SIZE - rendered_img.width) // 2, (RENDER_SIZE - rendered_img.height) // 2))
        rendered_img = canvas

    diff_heatmap, mean_diff, max_diff = pixel_diff_heatmap(source_img, rendered_img)
    diff_rgb = ImageOps.colorize(diff_heatmap, (0, 0, 80), (255, 200, 100))
    diff_rgb.save(diff_path)

    # Build composite panel: 4 thumbnails + stats text
    thumb_size = 360
    pad = 16
    text_w = 460
    panel_w = thumb_size * 3 + pad * 4 + text_w
    panel_h = thumb_size + pad * 2 + 80
    panel = Image.new("RGB", (panel_w, panel_h), (240, 234, 222))
    draw = ImageDraw.Draw(panel)

    # Header
    draw.text((pad, 16), f"{piece}", fill=(40, 40, 40))
    draw.text((pad, 36), f"viewBox: {stats.get('viewbox', '?')} | drawable: {stats.get('total_drawable', '?')} | fills: {stats.get('n_fills', '?')} unique",
              fill=(100, 100, 100))

    y_thumbs = 72
    # Thumb 1: source JPG
    t = source_img.resize((thumb_size, thumb_size), Image.LANCZOS)
    panel.paste(t, (pad, y_thumbs))
    draw.text((pad, y_thumbs + thumb_size + 4), "source JPG", fill=(60, 60, 60))
    # Thumb 2: rendered SVG
    t = rendered_img.resize((thumb_size, thumb_size), Image.LANCZOS)
    panel.paste(t, (pad * 2 + thumb_size, y_thumbs))
    draw.text((pad * 2 + thumb_size, y_thumbs + thumb_size + 4), "rendered SVG", fill=(60, 60, 60))
    # Thumb 3: diff heatmap
    t = diff_rgb.resize((thumb_size, thumb_size), Image.LANCZOS)
    panel.paste(t, (pad * 3 + thumb_size * 2, y_thumbs))
    draw.text((pad * 3 + thumb_size * 2, y_thumbs + thumb_size + 4),
              f"pixel diff (mean={mean_diff:.1f}/255, max={max_diff:.0f})",
              fill=(60, 60, 60))
    # Stats text panel
    stats_x = pad * 4 + thumb_size * 3
    stats_y = y_thumbs
    lines = [f"SVG STATS:"]
    if stats.get("elements"):
        for tag, n in sorted(stats["elements"].items(), key=lambda x: -x[1]):
            lines.append(f"  <{tag}>: {n}")
    lines.append("")
    lines.append(f"FILLS ({stats.get('n_fills', 0)} unique):")
    for f in stats.get("fills", [])[:10]:
        lines.append(f"  {f}")
    if stats.get("n_fills", 0) > 10:
        lines.append(f"  ...+{stats['n_fills']-10} more")
    if stats.get("suspicious_big"):
        lines.append("")
        lines.append("⚠ SUSPICIOUS BG:")
        for s in stats["suspicious_big"][:3]:
            lines.append(f"  {s}")
    # Verdict
    lines.append("")
    verdict = []
    if mean_diff < 30:
        verdict.append("PIXEL: close match")
    elif mean_diff < 60:
        verdict.append("PIXEL: moderate diff (color rendering)")
    else:
        verdict.append("PIXEL: large diff (investigate)")
    if stats.get("total_drawable", 0) < 5:
        verdict.append("⚠ very few elements")
    if stats.get("n_fills", 0) < 2 and stats.get("total_drawable", 0) > 10:
        verdict.append("⚠ single-color (no palette)")
    if stats.get("suspicious_big"):
        verdict.append("⚠ background rect detected")
    if not (stats.get("total_drawable", 0) < 5 or stats.get("suspicious_big")):
        verdict.append("VERDICT: PASS for decomposition")
    else:
        verdict.append("VERDICT: REVIEW before decomp")
    lines.append("")
    lines.extend(verdict)

    for i, line in enumerate(lines):
        draw.text((stats_x, stats_y + i * 18), line, fill=(40, 40, 40))

    return panel, {
        "piece": piece,
        "mean_diff": mean_diff,
        "max_diff": max_diff,
        "stats": stats,
        "verdict_lines": verdict,
    }


def main():
    QA_DIR.mkdir(parents=True, exist_ok=True)

    all_panels = []
    all_results = []
    for piece in PIECES:
        svg_path = CONVERTED / f"{piece}.svg"
        if not svg_path.exists():
            print(f"  ✗ SKIP {piece}: SVG missing")
            continue
        print(f"\n==== QA: {piece} ====")
        stats = parse_svg_stats(svg_path)
        print(f"  viewBox: {stats.get('viewbox')}")
        print(f"  elements: {stats.get('elements')}")
        print(f"  fills: {stats.get('n_fills')} unique")
        if stats.get("suspicious_big"):
            print(f"  ⚠ suspicious large shapes: {stats['suspicious_big']}")
        panel, result = build_panel(piece, stats)
        all_panels.append(panel)
        all_results.append(result)
        panel.save(QA_DIR / f"{piece}_qa_panel.png")
        print(f"  → panel saved")

    # Build aggregated contact sheet
    if all_panels:
        panel_w = all_panels[0].width
        panel_h = all_panels[0].height
        gap = 16
        sheet_w = panel_w + gap * 2
        sheet_h = panel_h * len(all_panels) + gap * (len(all_panels) + 1) + 60
        sheet = Image.new("RGB", (sheet_w, sheet_h), (230, 224, 210))
        draw = ImageDraw.Draw(sheet)
        draw.text((gap, 16), f"PDF→SVG Conversion QA — 2026-05-18 AM | {len(all_panels)} pieces", fill=(40, 40, 40))
        draw.text((gap, 36), "Per panel: source JPG | rendered SVG | pixel diff heatmap | SVG stats + verdict", fill=(100, 100, 100))
        for i, p in enumerate(all_panels):
            sheet.paste(p, (gap, 60 + i * (panel_h + gap)))
        sheet_path = QA_DIR / "_QA_contact_sheet.png"
        sheet.save(sheet_path)
        print(f"\n  → contact sheet: {sheet_path}")

    # Summary verdict
    print("\n==== SUMMARY ====")
    pass_count = 0
    for r in all_results:
        v = "PASS" if any("PASS" in line for line in r["verdict_lines"]) else "REVIEW"
        print(f"  {v}: {r['piece']:40s} mean_diff={r['mean_diff']:.1f}")
        if v == "PASS":
            pass_count += 1
    print(f"\n  {pass_count}/{len(all_results)} ready for decomposition")
    return all_results


if __name__ == "__main__":
    main()
