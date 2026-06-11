#!/usr/bin/env python3
"""
Austin review packet v2 — thumbnails + contact sheets + HTML index.

Per overnight #2: real morning-review packet with:
  - Contact sheets / thumbnails per artifact
  - Watch-first order maintained from existing README
  - Categories: SHOW / SHOW INTERNAL / ASK FIRST / INTERNAL ONLY / FAILED CONTROL
  - One-line framing per artifact
  - Consent/cultural guardrails visible
  - HTML index with clickable thumbnails + ordered playlist
"""
from pathlib import Path
from PIL import Image, ImageDraw
import subprocess

ROOT = Path(__file__).resolve().parent.parent
PACKET = ROOT / "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17"
PACKET_V2 = ROOT / "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18"

THUMB_W = 480
THUMB_H = 270


def extract_thumb(mp4: Path, out_jpg: Path):
    """Extract a mid-clip frame as thumbnail."""
    if out_jpg.exists():
        return
    # Get duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
        capture_output=True, text=True
    )
    try:
        duration = float(probe.stdout.strip())
    except (ValueError, AttributeError):
        duration = 5.0
    seek_time = duration / 2
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(seek_time), "-i", str(mp4),
        "-vframes", "1", "-vf", f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:white",
        "-q:v", "3", str(out_jpg)
    ], capture_output=True)


def resize_image_thumb(src: Path, out_jpg: Path):
    if out_jpg.exists():
        return
    img = Image.open(src).convert("RGB")
    img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
    canvas = Image.new("RGB", (THUMB_W, THUMB_H), (255, 255, 255))
    canvas.paste(img, ((THUMB_W - img.width) // 2, (THUMB_H - img.height) // 2))
    canvas.save(out_jpg, "JPEG", quality=88)


# Artifact registry (ordered for watch-first)
ARTIFACTS = [
    {
        "name": "Salmon swim rig v005 — yin-yang counterphase + eye pulse",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/salmon_in_place_v005.mp4",
        "category": "SHOW INTERNAL",
        "framing": "CANONICAL Salmon 'alive within the yin-yang piece' mechanic. Both salmon swim with continuous body deformation (cv2.remap traveling wave), counterphase, plus subtle eye-focal pulse. Roe stays static. Respects piece's geometry.",
        "guardrail": "Per-output Austin OK required before audience-facing use.",
    },
    {
        "name": "Cosmic_Sun breathing v003c — strong",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/austin_piece_breathing_nature_cosmic_sun_v003c_strong.mp4",
        "category": "SHOW INTERNAL",
        "framing": "CANONICAL Cosmic_Sun 'breathing' mechanic. Rays + eye-focals only (fewer atoms louder); subtle radial drift + scale pulse + rotation. Shimmer reads as spirit/energy. Source-fidelity verified vs training JPG.",
        "guardrail": "Per-output Austin OK required before audience-facing use.",
    },
    {
        "name": "Pearl-bead single-edge traversal",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4",
        "category": "SHOW",
        "framing": "Single pearl travels along one graph edge carrying its morph as it moves. Strongest single-clip explanation of pearl-bead-on-edges concept.",
        "guardrail": "Internal-only packet artifact.",
    },
    {
        "name": "Pearl-bead 3-stage logic diagram",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/01_progression_3stage.png",
        "category": "SHOW",
        "framing": "Static diagram: source → mid-morph → destination. Clarifies pearl-bead progression for first-time viewers.",
        "guardrail": "Internal-only packet artifact.",
    },
    {
        "name": "TheCreator pearl-bridge composite (NEW overnight)",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/thecreator_pearl_bridge_composite_v001.png",
        "category": "ASK FIRST",
        "framing": "Visual resonance observation: TheCreator's atom_0114 (sphere) + atom_0117 (held figure) structurally echoes our pearl-bead concept. NOT a cosmological claim — Austin's interpretation needed.",
        "guardrail": "Cultural framing: ask Austin whether this resonance is meaningful or coincidental BEFORE any external use.",
    },
    {
        "name": "Circle/Crescent/Trigon primitive cycle",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4",
        "category": "SHOW",
        "framing": "18-sec continuous transition through Coast Salish primitive forms. Foundational visual grammar.",
        "guardrail": "Internal-only packet artifact.",
    },
    {
        "name": "Primitive field v001",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4",
        "category": "SHOW",
        "framing": "40 phase-offset primitive cycles in 8×5 grid sweeping diagonally. Demonstrates the grammar at compositional scale.",
        "guardrail": "Internal-only packet artifact; low cultural load (abstract).",
    },
    {
        "name": "Abstract primitive-bridge toy demo (NEW overnight)",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/lane_2e_abstract_primitive_grammar_toy.mp4",
        "category": "SHOW",
        "framing": "12 clean primitives left → 12 right. 2 same-type pairs translate; 10 cross-type pairs morph via Circle/Crescent/Trigon bridge. NO Austin assets. Demonstrates Lane 2E grammar without claiming correspondences.",
        "guardrail": "Internal-only artifact; no cultural risk (abstract).",
    },
    {
        "name": "Raven↔Cosmic endpoint-correct v001 — preferred deterministic baseline",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4",
        "category": "SHOW INTERNAL",
        "framing": "Preferred deterministic Raven→Cosmic baseline. Same 108×108 viewBox; preserves the successful shape-morph motion, but frame 0 and final frame are exact verified training JPG endpoints. No SD/LoRA.",
        "guardrail": "Per-output Austin OK required. Older raven_sun_to_cosmic_sun.mp4 remains preserved as superseded/control.",
    },
    {
        "name": "Cosmic→Salmon v007 landmark-routing",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4",
        "category": "ASK FIRST",
        "framing": "Cross-piece morph using v007 landmark-atom routing (Codex worker). Smoother endpoint settle than v006. Still endpoint-assisted.",
        "guardrail": "Per-output Austin OK required. Cross-piece pairing — Austin guidance on which relationships are meaningful.",
    },
    {
        "name": "Cosmic→Salmon v006 (endpoint correct, remove dest bg rect)",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4",
        "category": "ASK FIRST",
        "framing": "Cross-piece morph older sibling of v007. Removes expanding-square background artifact. Retained as control for v007 comparison.",
        "guardrail": "Per-output Austin OK required. Cross-piece pairing.",
    },
    {
        "name": "Multi-pearl 3-node 2-pearl composite",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4",
        "category": "ASK FIRST",
        "framing": "Polyphonic graph-alive concept: 3 nodes in triangle, 2 pearls in flight simultaneously on different edges. Rough; inherits underlying edge transition artifacts.",
        "guardrail": "Internal-only packet artifact; rough state.",
    },
    {
        "name": "Wolf↔Salmon high-load morph",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/04_wolf_whorl_to_salmon_high_load_do_not_lead.mp4",
        "category": "ASK FIRST",
        "framing": "Same viewBox 1500×1500, 2-fold rotational both, geometric pairing technically works. HIGH cultural load: ancestor (wolf) ↔ provider (salmon).",
        "guardrail": "DO NOT lead with this. Show only if conversation has room. Austin discussion BEFORE any external use.",
    },
    {
        "name": "Raven→Salmon raw morph (rough)",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/02_raven_sun_to_salmon_raw_shape_morph_rough.mp4",
        "category": "ASK FIRST",
        "framing": "Interesting primitive-motion energy. Known bugs: start z-order, endpoint drift, seam artifacts.",
        "guardrail": "Rough; not a lead. Per-output Austin OK + bug-disclosure if shown.",
    },
    {
        "name": "Cosmic→Salmon raw morph (rough)",
        "source_path": "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/03_cosmic_sun_to_salmon_raw_shape_morph_rough.mp4",
        "category": "ASK FIRST",
        "framing": "Earlier rough control. Superseded for review by v006 / v007 lead-with clips.",
        "guardrail": "Rough; comparison-control only.",
    },
]


def main():
    PACKET_V2.mkdir(parents=True, exist_ok=True)
    thumbs_dir = PACKET_V2 / "thumbnails"
    thumbs_dir.mkdir(exist_ok=True)

    print(f"Building {len(ARTIFACTS)} thumbnails...")
    for i, art in enumerate(ARTIFACTS, 1):
        src = ROOT / art["source_path"]
        if not src.exists():
            print(f"  SKIP #{i}: {art['name']} → source missing at {src}")
            art["thumb"] = None
            continue
        thumb_name = f"{i:02d}_{src.stem}.jpg"
        thumb_path = thumbs_dir / thumb_name
        if src.suffix.lower() == ".mp4":
            extract_thumb(src, thumb_path)
        else:
            resize_image_thumb(src, thumb_path)
        if thumb_path.exists():
            art["thumb"] = f"thumbnails/{thumb_name}"
            print(f"  #{i:02d} ✓ {art['name']}")
        else:
            art["thumb"] = None
            print(f"  #{i:02d} ✗ thumbnail failed: {art['name']}")

    # Build contact sheet PNG
    n = len(ARTIFACTS)
    cols = 3
    rows = (n + cols - 1) // cols
    margin = 20
    cell_w = THUMB_W + margin
    cell_h = THUMB_H + 80  # extra for caption
    sheet_w = cols * cell_w + margin
    sheet_h = rows * cell_h + margin + 80
    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 240, 228))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 20), "Austin/Team Review Packet v2 — Watch-first contact sheet",
              fill=(40, 40, 40))
    draw.text((margin, 45), "Numbers = watch order. Categories: SHOW = green; SHOW INTERNAL = blue; ASK FIRST = orange.",
              fill=(80, 80, 80))

    cat_colors = {
        "SHOW": (60, 140, 60),
        "SHOW INTERNAL": (60, 100, 160),
        "ASK FIRST": (200, 130, 40),
        "INTERNAL ONLY": (140, 140, 140),
        "FAILED CONTROL": (180, 60, 60),
    }

    for i, art in enumerate(ARTIFACTS):
        row = i // cols
        col = i % cols
        x = margin + col * cell_w
        y = 80 + row * cell_h
        # Border with category color
        bcol = cat_colors.get(art["category"], (100, 100, 100))
        draw.rectangle([x - 4, y - 4, x + THUMB_W + 4, y + THUMB_H + 4],
                       outline=bcol, width=4)
        # Thumbnail
        if art.get("thumb"):
            try:
                t = Image.open(PACKET_V2 / art["thumb"]).convert("RGB")
                sheet.paste(t, (x, y))
            except Exception:
                draw.rectangle([x, y, x + THUMB_W, y + THUMB_H], fill=(200, 200, 200))
        else:
            draw.rectangle([x, y, x + THUMB_W, y + THUMB_H], fill=(220, 200, 200))
            draw.text((x + 10, y + 10), "thumbnail missing", fill=(100, 50, 50))
        # Caption
        draw.text((x, y + THUMB_H + 8),
                  f"#{i+1:02d} [{art['category']}]",
                  fill=bcol)
        # Truncate name
        name = art["name"][:55] + ("..." if len(art["name"]) > 55 else "")
        draw.text((x, y + THUMB_H + 28), name, fill=(40, 40, 40))

    sheet_path = PACKET_V2 / "contact_sheet.png"
    sheet.save(sheet_path)
    print(f"\n  → {sheet_path}")

    # Build HTML index
    html_path = PACKET_V2 / "index.html"
    html = ['<!DOCTYPE html>', '<html><head><meta charset="utf-8">',
            '<title>Austin/Team Review Packet v2 — 2026-05-17</title>',
            '<style>',
            'body { font-family: -apple-system, sans-serif; max-width: 1400px; margin: 20px auto; padding: 20px; background: #f5f0e4; }',
            'h1 { color: #2a2a2a; }',
            '.banner { background: #fff8e6; border-left: 4px solid #c8aa50; padding: 12px 16px; margin: 16px 0; }',
            '.item { display: flex; gap: 16px; padding: 16px; margin: 8px 0; background: white; border-radius: 6px; border-left: 4px solid #999; }',
            '.item.cat-SHOW { border-left-color: #3c8c3c; }',
            '.item.cat-SHOW-INTERNAL { border-left-color: #3c64a0; }',
            '.item.cat-ASK-FIRST { border-left-color: #c88228; }',
            '.item.cat-INTERNAL-ONLY { border-left-color: #909090; }',
            '.item.cat-FAILED-CONTROL { border-left-color: #b43c3c; }',
            '.item .meta { flex: 1; }',
            '.item h3 { margin: 0 0 4px 0; }',
            '.item .cat { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 11px; color: white; }',
            '.item .cat-SHOW { background: #3c8c3c; }',
            '.item .cat-SHOW-INTERNAL { background: #3c64a0; }',
            '.item .cat-ASK-FIRST { background: #c88228; }',
            '.item .cat-INTERNAL-ONLY { background: #909090; }',
            '.item .cat-FAILED-CONTROL { background: #b43c3c; }',
            '.item img { width: 320px; height: 180px; object-fit: contain; background: #eee; border-radius: 4px; }',
            '.item p { margin: 6px 0; color: #444; font-size: 14px; }',
            '.item .guardrail { font-size: 12px; color: #a04020; font-style: italic; }',
            '.item code { background: #f0e8d8; padding: 2px 4px; border-radius: 2px; font-size: 12px; }',
            '</style></head><body>',
            '<h1>Austin / Team Review Packet v2 — 2026-05-17</h1>',
            '<div class="banner"><strong>INTERNAL REVIEW ONLY — DO NOT SHARE OUTSIDE TEAM</strong><br>',
            'Per Austin consent floor: anything carrying his vocabulary requires per-output OK before audience-facing use. Watch order ranked top-to-bottom.',
            '</div>',
            '<p>Suggested framing for sharing: <em>"We have been experimenting internally with your pieces and with the three primitive forms. Nothing here is approved or proposed as final. We want to show a few directions and ask: does any of this feel interesting, useful, or worth developing with you?"</em></p>',
            ]
    for i, art in enumerate(ARTIFACTS, 1):
        cat_class = "cat-" + art["category"].replace(" ", "-")
        thumb_html = (f'<img src="{art["thumb"]}" alt="thumb">'
                      if art.get("thumb") else
                      '<div style="width:320px;height:180px;background:#fadddd;display:flex;align-items:center;justify-content:center;color:#a04;border-radius:4px;">missing</div>')
        html.append(f'<div class="item {cat_class}">')
        html.append(thumb_html)
        html.append('<div class="meta">')
        html.append(f'<h3>#{i:02d} {art["name"]}</h3>')
        html.append(f'<span class="cat {cat_class}">{art["category"]}</span>')
        html.append(f'<p>{art["framing"]}</p>')
        html.append(f'<p class="guardrail">⚠ {art["guardrail"]}</p>')
        html.append(f'<p><code>{art["source_path"]}</code></p>')
        html.append('</div></div>')
    html.append('<hr>')
    html.append('<p style="color:#666;font-size:12px;">Built overnight 2026-05-17→18 via <code>scripts/build_packet_v2_thumbnails.py</code>.</p>')
    html.append('</body></html>')
    html_path.write_text('\n'.join(html))
    print(f"  → {html_path}")

    # Compact README for the v2 packet
    (PACKET_V2 / "README.md").write_text(f"""# Austin/Team Review Packet v2 — 2026-05-17

INTERNAL REVIEW ONLY. Per Austin consent floor: anything carrying his
vocabulary requires per-output OK before audience-facing use.

## Quick start

- **Visual contact sheet**: `contact_sheet.png` — all {len(ARTIFACTS)} artifacts
  thumbnailed in 3-col grid, ordered by watch-first priority.
- **Clickable HTML index**: `index.html` — open in browser, see thumbnails +
  framing + cultural guardrails per artifact.
- **Preferred Raven -> Cosmic baseline**: item #09 now points to
  `raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4`; the older
  `morph_outputs/raven_sun_to_cosmic_sun.mp4` remains superseded/control.
- **Source-of-truth packet** (where the actual files live):
  `../austin-team-exploration-review-2026-05-17/`

## Categories

- **SHOW**: low-cultural-load, packet-ready (Pearl-bead, primitives, abstract toy)
- **SHOW INTERNAL**: Austin-derived, packet-ready pending per-output OK
- **ASK FIRST**: present only when conversation has room; rough or culturally-loaded
- **INTERNAL ONLY**: working artifact
- **FAILED CONTROL**: preserved labeled — DO NOT promote

## Suggested framing for Austin/team review

> "We have been experimenting internally with your pieces and with the three
> primitive forms. Nothing here is approved or proposed as final. We want to show
> a few directions and ask: does any of this feel interesting, useful, or worth
> developing with you?"
""")
    print(f"  → {PACKET_V2}/README.md")


if __name__ == "__main__":
    main()
