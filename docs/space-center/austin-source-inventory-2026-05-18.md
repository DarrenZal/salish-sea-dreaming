# Austin source-pieces inventory — for next morph pairs

Generated 2026-05-18 AM, final overnight mode #3. **No new renders performed.**
Clean table answering "ready / needs decomp / avoid (cultural load)."

## Important discovery: 7 PDFs available, pdftocairo present

The `austin-v2-ingest/approved/` folder contains **7 PDFs in addition to 5 SVGs**.
PDFs typically contain vector geometry → can be converted to SVG and decomposed.

`pdftocairo` is installed at `/opt/homebrew/bin/pdftocairo`. Conversion command:

```bash
pdftocairo -svg <input>.pdf <output>.svg
# Then run:
python3 scripts/decompose_austin_pieces.py --piece <piece_name>
```

This UNBLOCKS 7 more pieces for atom-level work — significantly expands pair-morph options.

## Full inventory (16 pieces in approved/)

| # | Piece | Vector source | JPG (training) | Decomposed? | Cultural load | Status |
|---|---|---|---|---|---|---|
| 1 | Nature_Cosmic_Sun | SVG ✓ | ✓ | ✓ (39 atoms) | medium | **READY** |
| 2 | Animal_Bird_Raven_Sun | SVG ✓ | ✓ | ✓ (29 atoms) | medium-high | **READY** |
| 3 | Animal_Salmon_Spawn_Eggs | SVG ✓ | ✓ | ✓ (242 atoms) | medium-high | **READY** |
| 4 | Animal_Wolf_Spindle_Whorl | SVG ✓ | ✓ | ✓ (63 atoms) | HIGH | **READY but cultural caution** |
| 5 | Supernatural_Human_TheCreator_Background | SVG ✓ | ✓ | ✓ (131 atoms) | VERY HIGH | **READY but cultural caution** |
| 6 | Animal_Bird_Heron_Background | PDF | ✓ | ✗ | low-medium | **NEEDS PDF→SVG conversion** |
| 7 | Animal_Deer_Background | PDF | ✓ | ✗ | low-medium | **NEEDS PDF→SVG conversion** |
| 8 | Animal_Insect_Bee | PDF | ✓ | ✗ | low | **NEEDS PDF→SVG conversion** |
| 9 | Animal_Bear_Background | PDF | ✓ | ✗ | medium-high | **NEEDS PDF→SVG conversion** |
| 10 | Animal_Wolf_Background | PDF | ✓ | ✗ | HIGH | **NEEDS PDF→SVG conversion (cultural caution)** |
| 11 | Supernatural_Bird_Thunderbird_Background | PDF | ✓ | ✗ | VERY HIGH | **AVOID — restricted per operator (Wolf↔Thunderbird-Bg explicitly banned; treat Thunderbird itself as VERY HIGH)** |
| 12 | Supernatural_Snake_Serpent | PDF | ✓ | ✗ | HIGH-VERY HIGH | **AVOID — defer until Austin guides supernatural pieces** |
| 13 | Animal_Bird_Raven_Transparent | PNG only | ✓ | ✗ | medium-high | NEEDS RASTER VECTORIZATION (or use SVG of Raven_Sun variant) |
| 14 | Animal_Insect_Butterfly_Transparent | PNG only | ✓ | ✗ | low | NEEDS RASTER VECTORIZATION (low priority) |
| 15 | Animal_Water_Octopus_Transparent | PNG only | ✓ | ✗ | medium | NEEDS RASTER VECTORIZATION |
| 16 | Animal_Water_Orca_Transparent | PNG only | ✓ | ✗ | HIGH | NEEDS RASTER VECTORIZATION (cultural caution) |
| 17 | Human_Mother_Bear_Cub_Background | PNG only | ✓ | ✗ | medium | NEEDS RASTER VECTORIZATION |
| 18 | Supernatural_Transformer_Background | PNG only | ✓ | ✗ | VERY HIGH | **AVOID — defer until Austin guides supernatural pieces** |

## Categorized triage

### Ready now (5 pieces — already decomposed)

These are the only pieces immediately usable for atom-level morph experiments tonight without any conversion work:

- **Nature_Cosmic_Sun** (medium) — radial sun, 39 atoms, 108×108 viewBox
- **Animal_Bird_Raven_Sun** (medium-high) — radial-with-bird, 29 atoms, 108×108
- **Animal_Salmon_Spawn_Eggs** (medium-high) — yin-yang, 242 atoms (184 roe), 1500×1500
- **Animal_Wolf_Spindle_Whorl** (HIGH) — 2-fold rotational, 63 atoms, 1500×1500
- **Supernatural_Human_TheCreator_Background** (VERY HIGH) — bilateral, 131 atoms, 1500×1500

### NEEDS PDF→SVG conversion (4 LOW-MED cultural load — highest priority for next morph experiments)

In priority order for morning conversion + decomposition:

1. **Animal_Bird_Heron_Background** (low-medium) — ecology pair with Salmon makes immediate narrative sense; "the heron fishes the spawning ground." Pairs cleanly with already-decomposed Salmon.
2. **Animal_Deer_Background** (low-medium) — common figure; could pair with Bear or with mammalian land-animal compositions.
3. **Animal_Insect_Bee** (low) — pollinator, ecology pair with Salmon_Spawn (life-cycle parallel). Low cultural risk.
4. **Animal_Bear_Background** (medium-high) — clan animal but common iconography; pairs with Deer / Mother_Bear_Cub narratively.

### NEEDS PDF→SVG conversion (cultural caution)

1. **Animal_Wolf_Background** (HIGH) — Wolf in different framing than spindle-whorl variant; both Wolf-related → defer until Austin guides.

### AVOID — restricted / VERY HIGH cultural load

- **Supernatural_Bird_Thunderbird_Background** — Wolf↔Thunderbird-Background explicitly excluded by operator; Thunderbird in any pair = AVOID until explicit Austin guidance.
- **Supernatural_Snake_Serpent** — supernatural serpent figure; defer.
- **Supernatural_Transformer_Background** — supernatural being; defer.

### NEEDS RASTER VECTORIZATION (low priority — raster→vector loss expected)

Transparent PNGs have no vector source. Conversion would need vectorization tools (Adobe Illustrator Image Trace, Vector Magic, etc.) and may lose Austin's intended line weights/forms. Better to ask Austin for SVG/PDF exports of these:

- Animal_Bird_Raven_Transparent (medium-high) — but Raven_Sun.svg already available, may not be needed
- Animal_Insect_Butterfly_Transparent (low) — pair candidate with Bee
- Animal_Water_Octopus_Transparent (medium) — pair candidate with Orca
- Animal_Water_Orca_Transparent (HIGH) — sacred whale, cultural caution
- Human_Mother_Bear_Cub_Background (medium) — pair with Bear
- Supernatural_Transformer_Background (VERY HIGH) — AVOID

## Recommended next morph-pair experiments (post-conversion + Austin OK)

Low cultural load + immediately actionable after PDF→SVG conversion:

| Pair | Both decomposed? | Cultural load | Notes |
|---|---|---|---|
| **Heron ↔ Salmon_Spawn** | Heron PDF→SVG needed; Salmon ready | low-medium | Ecological adjacency candidate (per peer caution 2026-05-18: avoid interpretive framing of meaning). Heron simpler geometry than salmon yin-yang. |
| **Bee ↔ Salmon_Spawn** | Bee PDF→SVG needed; Salmon ready | low | Pollinator + life-cycle. Bee's small atoms (wing pattern, body segments) may map to roe field interestingly. |
| **Deer ↔ Bear** | Both need PDF→SVG | low-medium / medium-high | Land-mammal pair. Both have body-formline structure. |
| **Bee ↔ Butterfly** | Bee PDF→SVG; Butterfly needs vectorization | low / low | Two insects, both have wing-pattern atoms. Lowest cultural load possible. Butterfly = raster though. |

**Best first experiment to run morning**: convert Heron PDF → SVG → decompose → render Heron↔Salmon morph using Lane 2E routing rule. ~3-4 hrs total (30 min conversion + decompose, 30 min routing assignment, 2-3 hrs render + iteration).

## Operational notes

- PDF→SVG conversion: `pdftocairo -svg input.pdf output.svg` then save to `austin-v2-ingest/approved/`. Verify visual fidelity matches the JPG (paths may differ from Inkscape exports).
- Decomposition: `python3 scripts/decompose_austin_pieces.py --piece <piece_name>` (assuming script supports piece selection; otherwise will need a minor flag addition).
- Sub-agent classification: existing 15-class formline taxonomy applies to new decompositions.
- All Austin-derived outputs INTERNAL until per-output OK.
- Wolf↔Thunderbird-Background pair explicitly excluded by operator regardless of how decomposition lands.

## Reference

- Pair-scouting report (already-decomposed pieces): `docs/space-center/austin-piece-pair-scouting-report-2026-05-17.md`
- Decomposition script: `scripts/decompose_austin_pieces.py`
- Catalogs: `austin-v2-ingest/decomposed/atom_catalog.html`, `primitives_catalog.html`
