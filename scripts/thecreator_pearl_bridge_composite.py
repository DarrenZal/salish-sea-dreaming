#!/usr/bin/env python3
"""
TheCreator pearl-bridge visual composite.

Side-by-side: source TheCreator piece (faded) with atom_0114 + atom_0117
highlighted, zoomed close-ups of those two atoms in the middle, and our
pearl-bead mockup on the right.

Cautious framing: "visual resonance / structural echo" — NOT a
cosmological or cultural claim. The structural similarity is an
observation, not a thesis. Any specific design-grammar use requires
Austin's direct consultation.

INTERNAL ONLY. Builds on existing decomposition and existing pearl-bead
prototype.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import csv

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed/Supernatural_Human_TheCreator_Background"
TRAINING = ROOT / "austin-v2-ingest/training"
PEARL_BEAD_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS_W = 1920
CANVAS_H = 1080
BG_COLOR = (242, 235, 222)
PANEL_PAD = 30


def load_atom_metadata(piece: str, atom_id: str) -> dict:
    csv_path = ROOT / f"austin-v2-ingest/decomposed/{piece}/atom_metadata.csv"
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            if row["atom_id"] == atom_id:
                return row
    return None


def fit_image(img: Image.Image, w: int, h: int, bg=BG_COLOR) -> Image.Image:
    out = Image.new("RGB", (w, h), bg)
    fitted = ImageOps.contain(img, (w, h), Image.LANCZOS)
    out.paste(fitted, ((w - fitted.width) // 2, (h - fitted.height) // 2))
    return out


def main():
    out_dir = INTERNAL / "thecreator-pearl-bridge-composite-2026-05-17"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load assets
    creator_jpg = Image.open(TRAINING / "Supernatural_Human_TheCreator_Background.jpg").convert("RGB")
    atom_0114 = Image.open(DECOMPOSED / "atom_0114.png").convert("RGBA")
    atom_0114_ctx = Image.open(DECOMPOSED / "atom_0114_context.png").convert("RGBA")
    atom_0117 = Image.open(DECOMPOSED / "atom_0117.png").convert("RGBA")
    atom_0117_ctx = Image.open(DECOMPOSED / "atom_0117_context.png").convert("RGBA")
    pearl_bead = Image.open(PEARL_BEAD_DIR / "02_single_scene_t05.png").convert("RGB")

    meta_114 = load_atom_metadata("Supernatural_Human_TheCreator_Background", "atom_0114")
    meta_117 = load_atom_metadata("Supernatural_Human_TheCreator_Background", "atom_0117")

    # 3-panel layout
    panel_w = (CANVAS_W - 4 * PANEL_PAD) // 3
    panel_h = CANVAS_H - 200  # leave room for header + footer captions

    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Top header
    draw.text((PANEL_PAD, 30), "Visual resonance / structural echo — INTERNAL observation only",
              fill=(80, 80, 80))
    draw.text((PANEL_PAD, 55), "TheCreator (atom_0114 + atom_0117) ↔ pearl-bead-on-edges concept",
              fill=(40, 40, 40))
    draw.text((PANEL_PAD, 80), "NOT a cosmological claim. Any design-grammar use requires Austin's direct consultation.",
              fill=(160, 60, 60))

    panel_top = 130

    # --- Left panel: TheCreator full piece with atoms highlighted ---
    left_x = PANEL_PAD
    creator_panel = fit_image(creator_jpg, panel_w, panel_h)
    canvas.paste(creator_panel, (left_x, panel_top))
    # Highlight atom_0114 + atom_0117 positions
    # The fit scales the JPG into panel_w × panel_h. Need to figure out
    # scale + offset to draw highlight ellipses at atom centroids.
    src_w, src_h = creator_jpg.size
    scale_x = panel_w / src_w
    scale_y = panel_h / src_h
    scale = min(scale_x, scale_y)
    offset_x = (panel_w - int(src_w * scale)) // 2 + left_x
    offset_y = (panel_h - int(src_h * scale)) // 2 + panel_top
    # Atom centroids in viewBox coords (need viewBox to canvas mapping)
    # TheCreator viewBox = 1500 per PIECE_VIEWBOX. JPG is some other res.
    # The atom centroids are in viewBox 1500 coords. The JPG and viewBox
    # may not be the same proportions. Approximate: assume JPG is a
    # direct render of the viewBox (square assumption).
    creator_viewbox = 1500.0
    for color, meta, label in [((220, 60, 60), meta_114, "atom_0114 (sphere)"),
                                ((60, 130, 220), meta_117, "atom_0117 (figure)")]:
        cx_vb = float(meta["centroid_x"])
        cy_vb = float(meta["centroid_y"])
        # Map viewbox coord to JPG pixel
        cx_jpg = (cx_vb / creator_viewbox) * src_w
        cy_jpg = (cy_vb / creator_viewbox) * src_h
        # Map JPG pixel to canvas pixel
        cx_canvas = offset_x + int(cx_jpg * scale)
        cy_canvas = offset_y + int(cy_jpg * scale)
        r = 24
        draw.ellipse([cx_canvas - r, cy_canvas - r, cx_canvas + r, cy_canvas + r],
                     outline=color, width=4)
        draw.text((cx_canvas + r + 5, cy_canvas - 8), label, fill=color)
    draw.text((left_x, panel_top + panel_h + 10),
              "Source — TheCreator piece (full composition; highlighted atoms within)",
              fill=(60, 60, 60))

    # --- Middle panel: zoomed atom_0114 + atom_0117 ---
    mid_x = left_x + panel_w + PANEL_PAD
    mid_inner_h = panel_h // 2 - 20
    # Top half: atom_0114 context (shows the dark sphere)
    atom_114_panel = fit_image(atom_0114_ctx.convert("RGB"), panel_w, mid_inner_h)
    canvas.paste(atom_114_panel, (mid_x, panel_top))
    draw.rectangle([mid_x, panel_top, mid_x + panel_w, panel_top + mid_inner_h],
                   outline=(220, 60, 60), width=3)
    draw.text((mid_x + 10, panel_top + 10), "atom_0114 — dark sphere", fill=(220, 60, 60))
    # Bottom half: atom_0117 context (shows the held figure)
    canvas.paste(fit_image(atom_0117_ctx.convert("RGB"), panel_w, mid_inner_h),
                 (mid_x, panel_top + mid_inner_h + 20))
    draw.rectangle([mid_x, panel_top + mid_inner_h + 20,
                    mid_x + panel_w, panel_top + 2 * mid_inner_h + 20],
                   outline=(60, 130, 220), width=3)
    draw.text((mid_x + 10, panel_top + mid_inner_h + 30),
              "atom_0117 — small held figure (inside sphere region)",
              fill=(60, 130, 220))
    draw.text((mid_x, panel_top + panel_h + 10),
              "Decomposed atoms — context views show each in piece",
              fill=(60, 60, 60))

    # --- Right panel: pearl-bead mockup ---
    right_x = mid_x + panel_w + PANEL_PAD
    canvas.paste(fit_image(pearl_bead, panel_w, panel_h), (right_x, panel_top))
    draw.text((right_x, panel_top + panel_h + 10),
              "Our pearl-bead concept mockup (graph traversal carrying morph)",
              fill=(60, 60, 60))

    # Footer
    footer_y = CANVAS_H - 50
    draw.text((PANEL_PAD, footer_y),
              "Observation: Austin's own composition contains a 'being inside a sphere/pearl' structural pattern (atom_0114 + atom_0117).",
              fill=(40, 40, 40))
    draw.text((PANEL_PAD, footer_y + 20),
              "Our independently-developed pearl-bead concept echoes this structure. Surface as observation only — pending Austin's interpretation.",
              fill=(40, 40, 40))

    composite_path = out_dir / "thecreator_pearl_bridge_composite_v001.png"
    canvas.save(composite_path)
    print(f"→ {composite_path}")

    # Also save individual zoom crops for backup use
    atom_0114_ctx.convert("RGB").save(out_dir / "atom_0114_context_zoom.png")
    atom_0117_ctx.convert("RGB").save(out_dir / "atom_0117_context_zoom.png")
    # README
    (out_dir / "README.md").write_text("""# TheCreator pearl-bridge visual composite

Internal-only observation: Austin's TheCreator_Background piece contains
a structural pattern of a "being inside a sphere/pearl":
  - atom_0114: large dark sphere
  - atom_0117: small held figure positioned within the sphere region

Our independently-developed pearl-bead-on-edges concept (graph traversal
where a pearl carries a real-time morph as it moves along an edge)
shares this structural pattern.

**This is an observation, not a claim.** The visual resonance is
genuine — both structures share "figure-inside-pearl" geometry — but
whether this matters culturally / cosmologically is Austin's call to
make.

For Austin review: show alongside the pearl-bead mockup; ask whether
this resonance feels meaningful or coincidental. Do not assert
interpretation.

## Files

- `thecreator_pearl_bridge_composite_v001.png` — 1920×1080 composite,
  three panels (source piece + decomposed atoms + pearl-bead mockup)
- `atom_0114_context_zoom.png` — atom_0114 highlighted in its context
- `atom_0117_context_zoom.png` — atom_0117 highlighted in its context

## Status

INTERNAL ONLY. Per Austin consent floor: anything carrying his
vocabulary requires per-output OK before audience-facing use.
""")


if __name__ == "__main__":
    main()
