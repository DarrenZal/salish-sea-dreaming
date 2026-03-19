#!/usr/bin/env python3
"""
Extract individual 512x512 frames from StyleGAN fakes grids.

Fakes grids are snapshots of generated samples arranged in a grid layout.
This script slices them into individual PNGs for img2img testing.

Usage:
    python extract_frames.py --input ../telus/fakes000200.png --output gan-frames/telus200
    python extract_frames.py --input ../models/base-v1-resume/fakes000120.png --output gan-frames/basev1_120
"""

import argparse
from pathlib import Path
from PIL import Image


def extract_frames(input_path: str, output_dir: str, cell_size: int = 512,
                   max_frames: int = 0, prefix: str = ""):
    img = Image.open(input_path)
    w, h = img.size
    cols = w // cell_size
    rows = h // cell_size
    total = cols * rows

    print(f"Image: {w}x{h}")
    print(f"Grid: {cols}x{rows} = {total} cells at {cell_size}x{cell_size}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not prefix:
        prefix = Path(input_path).stem

    count = 0
    for row in range(rows):
        for col in range(cols):
            if max_frames and count >= max_frames:
                break
            x = col * cell_size
            y = row * cell_size
            cell = img.crop((x, y, x + cell_size, y + cell_size))
            fname = f"{prefix}_{count:03d}.png"
            cell.save(out / fname)
            count += 1
        if max_frames and count >= max_frames:
            break

    print(f"Extracted {count} frames to {out}/")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from StyleGAN fakes grid")
    parser.add_argument("--input", required=True, help="Path to fakes grid PNG")
    parser.add_argument("--output", required=True, help="Output directory for individual frames")
    parser.add_argument("--cell-size", type=int, default=512, help="Cell size in pixels (default: 512)")
    parser.add_argument("--max-frames", type=int, default=0, help="Max frames to extract (0 = all)")
    parser.add_argument("--prefix", default="", help="Filename prefix (default: input filename stem)")
    args = parser.parse_args()
    extract_frames(args.input, args.output, args.cell_size, args.max_frames, args.prefix)
