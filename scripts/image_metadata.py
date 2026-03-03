#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Image Generation Metadata Tracker

Saves a JSON sidecar file alongside every generated image so we can
reproduce any image later. Tracks: model, prompt, input images, config,
timestamp, and output dimensions.

Usage:
    from image_metadata import save_metadata, load_metadata

    save_metadata(
        output_path="path/to/generated.png",
        model="gemini-3-pro-image-preview",
        prompt="The actual prompt text...",
        input_images=["path/to/ref1.jpg", "path/to/ref2.jpg"],
        config={"aspect_ratio": "3:2", "image_size": "4K"},
        notes="Iteration on kelp+octopus composite, v3",
    )

    meta = load_metadata("path/to/generated.png")
"""

import json
import os
from datetime import datetime
from PIL import Image


def save_metadata(output_path, model, prompt, input_images=None,
                  config=None, notes=None, source_direction=None,
                  source_image_keys=None):
    """Save a JSON sidecar file alongside a generated image.

    Args:
        output_path: Path to the generated image file
        model: Model ID used (e.g. "gemini-3-pro-image-preview", "gpt-image-1")
        prompt: The full prompt text sent to the model
        input_images: List of input image paths used as references
        config: Dict of model config params (aspect_ratio, image_size, etc.)
        notes: Free-text notes about this generation
        source_direction: Dream direction key if using dream_briony.py pipeline
        source_image_keys: Image catalog keys if using dream_briony.py pipeline
    """
    # Get output image dimensions
    width, height = None, None
    if os.path.exists(output_path):
        try:
            img = Image.open(output_path)
            width, height = img.size
        except Exception:
            pass

    meta = {
        "generated_at": datetime.now().isoformat(),
        "output_file": os.path.basename(output_path),
        "output_path": os.path.abspath(output_path),
        "model": model,
        "prompt": prompt,
        "input_images": [os.path.abspath(p) if os.path.exists(p) else p
                         for p in (input_images or [])],
        "config": config or {},
        "width": width,
        "height": height,
        "notes": notes,
        "source_direction": source_direction,
        "source_image_keys": source_image_keys,
    }

    # Remove None values for cleaner JSON
    meta = {k: v for k, v in meta.items() if v is not None}

    # Save as sidecar JSON (same name, .json extension)
    json_path = os.path.splitext(output_path)[0] + ".json"
    with open(json_path, 'w') as f:
        json.dump(meta, f, indent=2)

    return json_path


def load_metadata(image_path):
    """Load metadata for a generated image from its JSON sidecar."""
    json_path = os.path.splitext(image_path)[0] + ".json"
    if not os.path.exists(json_path):
        return None
    with open(json_path) as f:
        return json.load(f)


def list_all_metadata(experiments_dir):
    """Scan experiments directory and list all images with metadata."""
    results = []
    for root, dirs, files in os.walk(experiments_dir):
        for f in sorted(files):
            if f.endswith('.json'):
                json_path = os.path.join(root, f)
                with open(json_path) as fh:
                    meta = json.load(fh)
                results.append(meta)
    return results


if __name__ == "__main__":
    import sys
    import glob

    experiments = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', 'assets', 'output', 'experiments')

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        metas = list_all_metadata(experiments)
        print(f"\n=== {len(metas)} images with metadata ===\n")
        for m in metas:
            print(f"  {m.get('output_file', '?')}")
            print(f"    Model: {m.get('model', '?')}")
            print(f"    Size:  {m.get('width', '?')}x{m.get('height', '?')}")
            inputs = m.get('input_images', [])
            if inputs:
                print(f"    Refs:  {len(inputs)} reference images")
            notes = m.get('notes', '')
            if notes:
                print(f"    Notes: {notes[:80]}")
            print()
    else:
        # Count images without metadata
        image_files = glob.glob(os.path.join(experiments, '**', '*.png'), recursive=True)
        with_meta = 0
        without_meta = 0
        for img in image_files:
            json_path = os.path.splitext(img)[0] + ".json"
            if os.path.exists(json_path):
                with_meta += 1
            else:
                without_meta += 1
                print(f"  No metadata: {os.path.relpath(img, experiments)}")

        print(f"\n  {with_meta} images with metadata")
        print(f"  {without_meta} images without metadata")
        print(f"\n  Use --list to show all metadata")
        print(f"  Use dream_gemini.py to generate new images (auto-tracks metadata)")
