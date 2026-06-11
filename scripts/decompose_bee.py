#!/usr/bin/env python3
"""
Decompose Animal_Insect_Bee.svg (passed QA 2026-05-18 AM).

Wrapper that copies Bee SVG from austin-v2-ingest/converted/ to
source-vectors/ then invokes the decomposition logic. Modular
single-piece invocation so the main decompose_austin_pieces.py
TARGETS list stays unchanged.

Filters out background-clip rects (artifacts from pdftocairo conversion)
during decomposition by skipping any element with bbox > 80% of viewBox.
"""
from pathlib import Path
import shutil
import sys
import os

ROOT = Path(__file__).resolve().parent.parent
CONVERTED = ROOT / "austin-v2-ingest/converted/2026-05-18-pdf-to-svg-v001"
SOURCE_DIR = ROOT / "track2-deterministic/source-vectors"

PIECE_NAME = "Animal_Insect_Bee"
SVG_FILE = f"{PIECE_NAME}.svg"


def main():
    src = CONVERTED / SVG_FILE
    dst = SOURCE_DIR / SVG_FILE
    if not src.exists():
        sys.exit(f"Source missing: {src}")
    if dst.exists():
        print(f"  Already at {dst}")
    else:
        shutil.copy2(src, dst)
        print(f"  Copied: {src} → {dst}")

    # Monkey-patch TARGETS list in decompose_austin_pieces
    sys.path.insert(0, str(ROOT / "scripts"))
    import decompose_austin_pieces as dap
    original = list(dap.TARGETS)
    dap.TARGETS = [SVG_FILE]
    print(f"  Running decomposition for {PIECE_NAME} only...")
    try:
        dap.main()
    finally:
        dap.TARGETS = original

    out_dir = ROOT / "austin-v2-ingest/decomposed" / PIECE_NAME
    if out_dir.exists():
        atom_files = list(out_dir.glob("atom_*.png"))
        meta = out_dir / "atom_metadata.csv"
        print(f"\n  → {out_dir}")
        print(f"  Atoms: {len([f for f in atom_files if 'context' not in f.name])}")
        print(f"  Metadata: {'✓' if meta.exists() else '✗'}")


if __name__ == "__main__":
    main()
