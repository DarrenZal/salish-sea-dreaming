#!/usr/bin/env python3
"""
Build a focused HTML view of the THREE FUNDAMENTAL Coast Salish primitives
(Circle/Oval, Crescent, Trigon) across all Austin pieces.

Filters the decomposed atom catalog to show ONLY the three primitive classes,
arranged as 3 columns (one per primitive) with rows per source piece. The
intent is to make Austin's primitive grammar visible in one glance: how does
he use Circle/Crescent/Trigon across his work?

Output: austin-v2-ingest/decomposed/primitives_catalog.html

INTERNAL ONLY per Austin consent floor.
"""
from __future__ import annotations
from pathlib import Path
import csv
import json
import html

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed"
OUT_HTML = DECOMP / "primitives_catalog.html"

PRIMITIVE_LABELS = ["circle-oval", "crescent", "trigon"]
PRIMITIVE_COLORS = {
    "circle-oval": "#ff7e7e",
    "crescent":    "#7eb8ff",
    "trigon":      "#ffd47e",
}

def load_primitive_atoms():
    """Load atoms classified as one of the 3 primitives."""
    atoms_by_piece_and_label = {}  # piece -> label -> [atoms]
    pieces = sorted([d for d in DECOMP.iterdir() if d.is_dir()])
    for piece_dir in pieces:
        meta = piece_dir / "atom_metadata.csv"
        if not meta.exists():
            continue
        atoms_by_piece_and_label[piece_dir.name] = {l: [] for l in PRIMITIVE_LABELS}
        with open(meta) as f:
            for row in csv.DictReader(f):
                label = (row.get("ai_label") or "").strip()
                if label in PRIMITIVE_LABELS:
                    row["_iso_rel"] = f"{piece_dir.name}/{row.get('isolated_png', '')}"
                    row["_ctx_rel"] = f"{piece_dir.name}/{row.get('context_png', '')}"
                    atoms_by_piece_and_label[piece_dir.name][label].append(row)
    return atoms_by_piece_and_label

def build_html(atoms_by_piece):
    # Totals
    totals = {l: 0 for l in PRIMITIVE_LABELS}
    for piece in atoms_by_piece:
        for label in PRIMITIVE_LABELS:
            totals[label] += len(atoms_by_piece[piece][label])
    grand_total = sum(totals.values())

    # Build atom cards HTML for each piece × label cell
    def card_for_atom(atom):
        a = atom
        return f"""<div class="atom-card" data-atom-id="{html.escape(a.get('atom_id',''))}" onclick='showModal({json.dumps(a, default=str)})'>
            <img class="iso" src="{html.escape(a['_iso_rel'])}" loading="lazy"/>
            <div class="atom-id">{html.escape(a.get('atom_id','')[5:])}</div>
        </div>"""

    rows_html = ""
    for piece in sorted(atoms_by_piece.keys()):
        piece_atoms = atoms_by_piece[piece]
        piece_total = sum(len(piece_atoms[l]) for l in PRIMITIVE_LABELS)
        if piece_total == 0:
            continue
        cells = ""
        for label in PRIMITIVE_LABELS:
            cell_atoms = piece_atoms[label]
            atom_cards = "".join(card_for_atom(a) for a in cell_atoms)
            cells += f"""<td class="atom-cell">
                <div class="cell-count">{len(cell_atoms)}</div>
                <div class="atom-grid">{atom_cards}</div>
            </td>"""
        rows_html += f"""<tr>
            <td class="piece-name">{html.escape(piece)}<br><span class="piece-total">{piece_total} primitives</span></td>
            {cells}
        </tr>"""

    # Header row with primitive labels + totals
    header_cells = "".join(
        f'<th class="primitive-header" style="background:{PRIMITIVE_COLORS[l]};color:#000;">'
        f'{l}<br><span class="primitive-total">{totals[l]} total</span></th>'
        for l in PRIMITIVE_LABELS
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Austin's Three Primitives [INTERNAL]</title>
<style>
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #1a1a1a; color: #e0e0e0; }}
  header {{ background: #2a2a2a; padding: 16px 24px; border-bottom: 1px solid #444; }}
  .banner {{ color: #ff7e7e; font-size: 11px; font-weight: bold; letter-spacing: 1px; }}
  h1 {{ margin: 8px 0 4px; font-size: 22px; font-weight: 500; }}
  .subtitle {{ color: #aaa; font-size: 13px; max-width: 900px; line-height: 1.4; }}
  .stats {{ color: #aaa; font-size: 12px; margin-top: 12px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #2a2a2a; padding: 12px; text-align: center; font-size: 14px; font-weight: 600; vertical-align: top; }}
  .primitive-header {{ padding: 16px; font-size: 16px; }}
  .primitive-total {{ font-size: 11px; font-weight: 400; opacity: 0.7; }}
  td {{ padding: 12px; border-top: 1px solid #333; vertical-align: top; }}
  .piece-name {{ font-size: 13px; color: #aaa; width: 200px; font-family: monospace; }}
  .piece-total {{ font-size: 10px; color: #777; }}
  .atom-cell {{ background: #1f1f1f; min-height: 80px; }}
  .cell-count {{ font-size: 11px; color: #666; text-align: right; }}
  .atom-grid {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }}
  .atom-card {{ width: 60px; cursor: pointer; transition: transform 0.1s; }}
  .atom-card:hover {{ transform: scale(1.5); position: relative; z-index: 5; }}
  .atom-card .iso {{ width: 60px; height: 60px; background: white; object-fit: contain; border-radius: 3px; }}
  .atom-card .atom-id {{ font-size: 9px; color: #666; text-align: center; margin-top: 2px; }}
  #modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 100; padding: 40px; }}
  #modal.active {{ display: block; }}
  #modal .close {{ position: fixed; top: 20px; right: 30px; color: white; font-size: 30px; cursor: pointer; }}
  #modal .body {{ max-width: 1100px; margin: 0 auto; background: #2a2a2a; border-radius: 8px; overflow: hidden; }}
  #modal .images {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #444; }}
  #modal .images img {{ width: 100%; background: white; display: block; }}
  #modal .details {{ padding: 24px; }}
  #modal .details h2 {{ margin: 0 0 12px; }}
  #modal .details .row {{ margin: 6px 0; font-size: 13px; color: #ccc; }}
  #modal .details .row strong {{ color: #fff; display: inline-block; min-width: 120px; }}
</style>
</head>
<body>
<header>
  <div class="banner">[INTERNAL — DO NOT SHARE]</div>
  <h1>Austin's Three Fundamental Primitives</h1>
  <div class="subtitle">
    Circle-Oval, Crescent, Trigon — the three foundational Coast Salish formline shapes
    as they appear across Austin Harry's pieces. Each cell shows the AI-classified primitive
    atoms from that piece in that class. Click any atom to see it isolated + in context.
  </div>
  <div class="stats">{grand_total} primitive atoms across {len(atoms_by_piece)} pieces · Cycle 2026-05-17</div>
</header>
<table>
  <thead>
    <tr>
      <th>Piece</th>
      {header_cells}
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<div id="modal">
  <span class="close" id="modal-close">×</span>
  <div class="body" id="modal-body"></div>
</div>

<script>
function showModal(a) {{
  document.getElementById('modal-body').innerHTML = `
    <div class="images">
      <img src="${{a._iso_rel}}" alt="isolated"/>
      <img src="${{a._ctx_rel}}" alt="context"/>
    </div>
    <div class="details">
      <h2>${{a.ai_label}} — ${{a.atom_id}}</h2>
      <div class="row"><strong>piece:</strong> ${{a.piece}}</div>
      <div class="row"><strong>element:</strong> ${{a.element_type}} (fill ${{a.fill_color}})</div>
      <div class="row"><strong>bbox:</strong> ${{parseFloat(a.bbox_w).toFixed(1)}} × ${{parseFloat(a.bbox_h).toFixed(1)}}</div>
      <div class="row"><strong>centroid:</strong> (${{parseFloat(a.centroid_x).toFixed(1)}}, ${{parseFloat(a.centroid_y).toFixed(1)}})</div>
      <div class="row"><strong>confidence:</strong> ${{a.ai_confidence}}</div>
      <div class="row"><strong>reason:</strong> ${{a.ai_reason}}</div>
    </div>
  `;
  document.getElementById('modal').classList.add('active');
}}
document.getElementById('modal-close').onclick = () => document.getElementById('modal').classList.remove('active');
document.getElementById('modal').onclick = (e) => {{ if (e.target.id === 'modal') document.getElementById('modal').classList.remove('active'); }};
</script>
</body>
</html>
"""

def main():
    atoms_by_piece = load_primitive_atoms()
    html_str = build_html(atoms_by_piece)
    OUT_HTML.write_text(html_str)
    totals = {l: sum(len(atoms_by_piece[p][l]) for p in atoms_by_piece) for l in PRIMITIVE_LABELS}
    grand = sum(totals.values())
    print(f"Built primitives catalog: {OUT_HTML}")
    print(f"  Total primitive atoms: {grand}")
    for l in PRIMITIVE_LABELS:
        print(f"    {l}: {totals[l]}")
    for piece in sorted(atoms_by_piece.keys()):
        total = sum(len(atoms_by_piece[piece][l]) for l in PRIMITIVE_LABELS)
        if total > 0:
            breakdown = "/".join(str(len(atoms_by_piece[piece][l])) for l in PRIMITIVE_LABELS)
            print(f"    {piece}: {total} ({breakdown} c/cr/tr)")

if __name__ == "__main__":
    main()
