#!/usr/bin/env python3
"""
Build an HTML catalog of decomposed Austin atoms.

Reads atom_metadata.csv from each piece in austin-v2-ingest/decomposed/
and renders a single HTML page with all atoms organized by piece + label.

Features:
  - Grid layout, sortable + filterable by label / piece / color / size
  - Each atom card shows: isolated PNG (large), context PNG thumbnail,
    label, confidence, reason, geometry metadata, source piece
  - Color-coded by formline class
  - Click atom to see full-resolution + reason

Output: austin-v2-ingest/decomposed/atom_catalog.html

INTERNAL ONLY per Austin consent floor.
"""
from __future__ import annotations
from pathlib import Path
import csv
import json
import html

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed"
OUT_HTML = DECOMP / "atom_catalog.html"

# Color coding for labels (visual cue in the grid)
LABEL_COLORS = {
    "circle-oval":         "#ff7e7e",  # warm red
    "crescent":            "#7eb8ff",  # blue
    "trigon":              "#ffd47e",  # gold
    "formline-primary":    "#1a1a1a",  # near-black
    "formline-secondary":  "#444444",  # dark gray
    "formline-tertiary":   "#666666",  # mid gray
    "eye-focal-oval":      "#c47eff",  # violet
    "wing-feather":        "#7effd6",  # mint
    "fin-tail":            "#7effa0",  # green
    "body-element":        "#ffae7e",  # peach
    "sun-ray":             "#fff07e",  # yellow
    "egg-roe":             "#ffb8d9",  # pink
    "negative-space":      "#cccccc",  # light gray
    "background-field":    "#aaaaaa",  # gray
    "other":               "#e0e0e0",  # very light gray
    "":                    "#f0f0f0",  # unlabeled
}

def load_all_atoms():
    """Load every atom from every piece's metadata CSV."""
    atoms = []
    pieces = sorted([d for d in DECOMP.iterdir() if d.is_dir()])
    for piece_dir in pieces:
        meta = piece_dir / "atom_metadata.csv"
        if not meta.exists():
            continue
        with open(meta) as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["_piece_dir"] = piece_dir.name
                # Build relative paths to PNGs (relative to catalog HTML location)
                if row.get("isolated_png"):
                    row["_iso_rel"] = f"{piece_dir.name}/{row['isolated_png']}"
                else:
                    row["_iso_rel"] = ""
                if row.get("context_png"):
                    row["_ctx_rel"] = f"{piece_dir.name}/{row['context_png']}"
                else:
                    row["_ctx_rel"] = ""
                atoms.append(row)
    return atoms

def build_html(atoms):
    # Stats
    by_label = {}
    by_piece = {}
    for a in atoms:
        l = a.get("ai_label", "") or ""
        by_label[l] = by_label.get(l, 0) + 1
        p = a.get("_piece_dir", "")
        by_piece[p] = by_piece.get(p, 0) + 1

    # JSON for client-side filtering
    atoms_json = json.dumps([{
        "atom_id": a["atom_id"],
        "piece": a["_piece_dir"],
        "label": a.get("ai_label", "") or "",
        "confidence": a.get("ai_confidence", "") or "",
        "reason": a.get("ai_reason", "") or "",
        "element_type": a.get("element_type", ""),
        "fill_color": a.get("fill_color", ""),
        "bbox_w": float(a.get("bbox_w") or 0),
        "bbox_h": float(a.get("bbox_h") or 0),
        "area": float(a.get("area") or 0),
        "iso_rel": a["_iso_rel"],
        "ctx_rel": a["_ctx_rel"],
    } for a in atoms])

    all_labels = sorted(by_label.keys())
    label_options = "".join(
        f'<option value="{html.escape(l)}">{html.escape(l) or "(unlabeled)"} ({by_label[l]})</option>'
        for l in all_labels
    )
    piece_options = "".join(
        f'<option value="{html.escape(p)}">{html.escape(p)} ({by_piece[p]})</option>'
        for p in sorted(by_piece.keys())
    )
    label_color_json = json.dumps(LABEL_COLORS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Austin Atom Catalog [INTERNAL]</title>
<style>
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background: #1a1a1a;
    color: #e0e0e0;
  }}
  header {{
    background: #2a2a2a;
    padding: 16px 24px;
    border-bottom: 1px solid #444;
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  h1 {{ margin: 0 0 8px; font-size: 18px; font-weight: 500; }}
  .banner {{
    color: #ff7e7e;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .stats {{ font-size: 12px; color: #aaa; margin-bottom: 12px; }}
  .controls {{
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }}
  .controls label {{ font-size: 12px; color: #aaa; }}
  .controls select, .controls input {{
    background: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 12px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    padding: 20px;
  }}
  .card {{
    background: #2a2a2a;
    border-radius: 6px;
    overflow: hidden;
    border: 2px solid transparent;
    cursor: pointer;
    transition: transform 0.1s, border-color 0.1s;
  }}
  .card:hover {{
    transform: scale(1.03);
    border-color: #fff;
  }}
  .card .iso {{
    width: 100%;
    aspect-ratio: 1;
    background: white;
    object-fit: contain;
  }}
  .card .meta {{
    padding: 8px;
    font-size: 11px;
  }}
  .card .label {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    color: #000;
    font-weight: 500;
    margin-bottom: 4px;
  }}
  .card .id {{ color: #aaa; font-size: 10px; }}
  .card .piece {{ color: #888; font-size: 10px; margin-top: 2px; }}
  #modal {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.9);
    z-index: 100;
    padding: 20px;
    overflow: auto;
  }}
  #modal.active {{ display: block; }}
  #modal .close {{
    position: fixed;
    top: 20px;
    right: 30px;
    color: white;
    font-size: 30px;
    cursor: pointer;
    z-index: 101;
  }}
  #modal .body {{
    max-width: 1200px;
    margin: 0 auto;
    background: #2a2a2a;
    border-radius: 8px;
    overflow: hidden;
  }}
  #modal .images {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: #444;
  }}
  #modal .images img {{ width: 100%; background: white; display: block; }}
  #modal .details {{ padding: 24px; }}
  #modal .details h2 {{ margin: 0 0 12px; font-size: 20px; }}
  #modal .details .row {{ margin: 8px 0; font-size: 13px; color: #ccc; }}
  #modal .details .row strong {{ color: #fff; display: inline-block; min-width: 120px; }}
</style>
</head>
<body>
<header>
  <div class="banner">[INTERNAL — DO NOT SHARE]</div>
  <h1>Austin Atom Catalog</h1>
  <div class="stats">
    {len(atoms)} atoms across {len(by_piece)} pieces.
    Labeled: {sum(by_label.get(l, 0) for l in by_label if l)} /
    Unlabeled: {by_label.get("", 0)}
  </div>
  <div class="controls">
    <label>piece: <select id="filter-piece"><option value="">all ({len(atoms)})</option>{piece_options}</select></label>
    <label>label: <select id="filter-label"><option value="">all</option>{label_options}</select></label>
    <label>sort by: <select id="sort">
      <option value="default">default (piece, atom_id)</option>
      <option value="label">label</option>
      <option value="confidence">confidence (desc)</option>
      <option value="area">area (desc)</option>
      <option value="bbox_w">width (desc)</option>
    </select></label>
    <span id="visible-count" style="color: #aaa; font-size: 12px; margin-left: auto;"></span>
  </div>
</header>
<div class="grid" id="grid"></div>

<div id="modal">
  <span class="close" id="modal-close">×</span>
  <div class="body" id="modal-body"></div>
</div>

<script>
const atoms = {atoms_json};
const labelColors = {label_color_json};

const grid = document.getElementById('grid');
const filterPiece = document.getElementById('filter-piece');
const filterLabel = document.getElementById('filter-label');
const sortSelect = document.getElementById('sort');
const visibleCount = document.getElementById('visible-count');

function render() {{
  const piece = filterPiece.value;
  const label = filterLabel.value;
  const sortBy = sortSelect.value;
  let filtered = atoms.filter(a => (!piece || a.piece === piece) && (label === "" || a.label === label));
  if (sortBy === 'label') filtered.sort((x, y) => (x.label || '').localeCompare(y.label || ''));
  else if (sortBy === 'confidence') filtered.sort((x, y) => parseFloat(y.confidence || 0) - parseFloat(x.confidence || 0));
  else if (sortBy === 'area') filtered.sort((x, y) => y.area - x.area);
  else if (sortBy === 'bbox_w') filtered.sort((x, y) => y.bbox_w - x.bbox_w);
  grid.innerHTML = '';
  for (const a of filtered) {{
    const card = document.createElement('div');
    card.className = 'card';
    const labelColor = labelColors[a.label] || '#e0e0e0';
    card.innerHTML = `
      <img class="iso" src="${{a.iso_rel}}" alt="${{a.atom_id}}" loading="lazy">
      <div class="meta">
        <div class="label" style="background:${{labelColor}};">${{a.label || '(unlabeled)'}}</div>
        <div class="id">${{a.atom_id}} · ${{a.element_type}}</div>
        <div class="piece">${{a.piece}}</div>
      </div>
    `;
    card.onclick = () => showModal(a);
    grid.appendChild(card);
  }}
  visibleCount.textContent = `${{filtered.length}} visible`;
}}

function showModal(a) {{
  const labelColor = labelColors[a.label] || '#e0e0e0';
  document.getElementById('modal-body').innerHTML = `
    <div class="images">
      <img src="${{a.iso_rel}}" alt="isolated"/>
      <img src="${{a.ctx_rel}}" alt="context"/>
    </div>
    <div class="details">
      <h2><span style="background:${{labelColor}};color:#000;padding:2px 8px;border-radius:3px;">${{a.label || '(unlabeled)'}}</span> ${{a.atom_id}}</h2>
      <div class="row"><strong>piece:</strong> ${{a.piece}}</div>
      <div class="row"><strong>element type:</strong> ${{a.element_type}}</div>
      <div class="row"><strong>fill color:</strong> ${{a.fill_color}}</div>
      <div class="row"><strong>bbox:</strong> ${{a.bbox_w.toFixed(1)}} × ${{a.bbox_h.toFixed(1)}}</div>
      <div class="row"><strong>area:</strong> ${{a.area.toFixed(1)}}</div>
      <div class="row"><strong>AI confidence:</strong> ${{a.confidence || 'n/a'}}</div>
      <div class="row"><strong>AI reason:</strong> ${{a.reason || 'n/a'}}</div>
    </div>
  `;
  document.getElementById('modal').classList.add('active');
}}

document.getElementById('modal-close').onclick = () => document.getElementById('modal').classList.remove('active');
document.getElementById('modal').onclick = (e) => {{ if (e.target.id === 'modal') document.getElementById('modal').classList.remove('active'); }};

filterPiece.onchange = render;
filterLabel.onchange = render;
sortSelect.onchange = render;
render();
</script>
</body>
</html>
"""

def main():
    atoms = load_all_atoms()
    if not atoms:
        print("No atoms found in", DECOMP)
        return
    html_str = build_html(atoms)
    OUT_HTML.write_text(html_str)
    print(f"Built catalog: {OUT_HTML}")
    print(f"  {len(atoms)} atoms across {len(set(a['_piece_dir'] for a in atoms))} pieces")
    by_label = {}
    for a in atoms:
        l = a.get("ai_label", "") or "(unlabeled)"
        by_label[l] = by_label.get(l, 0) + 1
    for l in sorted(by_label.keys()):
        print(f"    {l}: {by_label[l]}")
    print()
    print(f"Open in browser: open {OUT_HTML}")

if __name__ == "__main__":
    main()
