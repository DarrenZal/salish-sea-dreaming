#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Gemini Image Generation

Uses Google's Gemini image models (Nano Banana / Nano Banana Pro) for
multi-reference style-guided image generation.

Key advantage over OpenAI: multiple reference images (up to 14 with Pro),
style conditioning from Briony's originals, 4K output, thinking mode.

Models:
  - gemini-2.5-flash-image (Nano Banana): Fast, 1K, up to 3 refs
  - gemini-3-pro-image-preview (Nano Banana Pro): Precise, 4K, up to 14 refs

Every generated image gets a JSON sidecar with full reproduction metadata.

Usage:
    # Generate with Nano Banana Pro (default), 4K, landscape
    python3.11 dream_gemini.py --prompt "..." --refs img1.jpg img2.jpg

    # Quick iteration with Flash
    python3.11 dream_gemini.py --model flash --prompt "..." --refs img1.jpg

    # Use Briony's paintings as style references (shorthand)
    python3.11 dream_gemini.py --briony octopus kelp salmon --prompt "..."

    # Set aspect ratio and size
    python3.11 dream_gemini.py --prompt "..." --aspect 3:2 --size 4K

    # List available Briony references
    python3.11 dream_gemini.py --list-refs
"""

import os
import sys
import argparse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..')

# Auto-load .env from project root
_env_file = os.path.join(PROJECT_DIR, '.env')
if os.path.exists(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _key, _val = _line.split('=', 1)
                os.environ.setdefault(_key.strip(), _val.strip())

OUTPUT_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'experiments')
PAINTINGS_DIR = os.path.join(PROJECT_DIR, 'VisualArt', 'Brionny', 'Paintings')

sys.path.insert(0, SCRIPT_DIR)
from image_metadata import save_metadata

# Briony painting shortcuts for --briony flag
BRIONY_REFS = {
    "octopus": os.path.join(PAINTINGS_DIR, "Giant-Pacific-Octopus", "IMG_1474.jpg"),
    "kelp": os.path.join(PAINTINGS_DIR, "Kelp-Forest-Ecosystem", "IMG_1477.jpg"),
    "salmon": os.path.join(PAINTINGS_DIR, "Salmon-Forest-Cycle", "IMG_1478.jpg"),
    "panorama": os.path.join(PAINTINGS_DIR, "Salish-Sea-Panorama-Horizontal", "IMG_1476.jpg"),
    "vertical": os.path.join(PAINTINGS_DIR, "Salish-Sea-Ecosystem-Vertical", "IMG_1473.jpg"),
    "eelgrass": os.path.join(PAINTINGS_DIR, "Eelgrass-Restoration-Divers", "IMG_1475.jpg"),
    "tree": os.path.join(PAINTINGS_DIR, "Tree-Root-Systems", "IMG_1483.jpg"),
}

# Model aliases
MODELS = {
    "pro": "gemini-3-pro-image-preview",
    "flash": "gemini-2.5-flash-image",
}


def get_client():
    """Get Gemini client (requires GOOGLE_API_KEY env var)."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    from google import genai
    return genai.Client()


def generate_image(client, model_id, prompt, ref_images=None,
                   aspect_ratio=None, image_size=None,
                   output_dir=None, output_name=None, notes=None):
    """Generate an image with Gemini and save with metadata.

    Args:
        client: genai.Client instance
        model_id: Full model ID string
        prompt: Text prompt
        ref_images: List of (path, PIL.Image) tuples for reference images
        aspect_ratio: e.g. "3:2", "16:9", "1:1"
        image_size: "1K", "2K", or "4K"
        output_dir: Override output directory
        output_name: Custom filename (without extension)
        notes: Free-text notes for metadata

    Returns:
        Path to saved image, or None on failure
    """
    from google.genai import types
    from PIL import Image

    # Build content list: prompt + reference images
    contents = [prompt]
    ref_paths = []
    if ref_images:
        for path in ref_images:
            img = Image.open(path)
            contents.append(img)
            ref_paths.append(path)

    # Build config
    config_kwargs = {
        "response_modalities": ["TEXT", "IMAGE"],
    }

    image_config = {}
    if aspect_ratio:
        image_config["aspect_ratio"] = aspect_ratio
    if image_size:
        image_config["image_size"] = image_size
    if image_config:
        config_kwargs["image_config"] = types.ImageConfig(**image_config)

    config = types.GenerateContentConfig(**config_kwargs)

    print(f"  Model:  {model_id}")
    print(f"  Refs:   {len(ref_paths)} reference images")
    if aspect_ratio:
        print(f"  Aspect: {aspect_ratio}")
    if image_size:
        print(f"  Size:   {image_size}")
    print(f"  Generating...")

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=config,
    )

    # Extract image and text from response
    out_dir = output_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = output_name or "gemini-generation"
    response_text = None
    saved_path = None

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img_data = part.inline_data.data
            outpath = os.path.join(out_dir, f"{ts}_{name}.png")
            with open(outpath, 'wb') as f:
                f.write(img_data)

            # Get dimensions
            img = Image.open(outpath)
            print(f"  Saved:  {outpath}")
            print(f"  Dims:   {img.size[0]}x{img.size[1]}")
            saved_path = outpath

        elif part.text:
            response_text = part.text
            if response_text:
                print(f"  Model says: {response_text[:150]}")

    # Save metadata
    if saved_path:
        meta_config = {}
        if aspect_ratio:
            meta_config["aspect_ratio"] = aspect_ratio
        if image_size:
            meta_config["image_size"] = image_size

        json_path = save_metadata(
            output_path=saved_path,
            model=model_id,
            prompt=prompt,
            input_images=ref_paths,
            config=meta_config,
            notes=notes,
        )
        print(f"  Meta:   {json_path}")

    return saved_path


def list_refs():
    """Print available Briony reference shortcuts."""
    print("\n=== Briony Painting References (for --briony flag) ===\n")
    for key, path in BRIONY_REFS.items():
        exists = "OK" if os.path.exists(path) else "MISSING"
        print(f"  {key:<12} [{exists}]  {os.path.basename(path)}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate images with Gemini (Nano Banana / Pro)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", required=False,
                        help="Text prompt for generation")
    parser.add_argument("--prompt-file", "-f",
                        help="Read prompt from a text file")
    parser.add_argument("--refs", nargs="+", metavar="PATH",
                        help="Reference image paths")
    parser.add_argument("--briony", nargs="+", metavar="KEY",
                        choices=list(BRIONY_REFS.keys()),
                        help="Use Briony's paintings as references (octopus, kelp, salmon, panorama, vertical, eelgrass, tree)")
    parser.add_argument("--model", "-m", default="pro",
                        choices=["pro", "flash"],
                        help="Model: pro (Nano Banana Pro, 4K) or flash (Nano Banana, fast)")
    parser.add_argument("--aspect", default=None,
                        help="Aspect ratio (3:2, 16:9, 1:1, 4:3, etc.)")
    parser.add_argument("--size", default=None,
                        choices=["1K", "2K", "4K"],
                        help="Output size (default: model default)")
    parser.add_argument("--output-dir", "-o",
                        help="Override output directory")
    parser.add_argument("--name", "-n",
                        help="Custom output filename (without extension)")
    parser.add_argument("--notes",
                        help="Notes to save in metadata")
    parser.add_argument("--list-refs", action="store_true",
                        help="List available Briony reference shortcuts")
    args = parser.parse_args()

    if args.list_refs:
        list_refs()
        return

    # Get prompt
    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read().strip()
    if not prompt:
        parser.print_help()
        return

    # Collect reference images
    ref_images = list(args.refs or [])
    if args.briony:
        for key in args.briony:
            path = BRIONY_REFS[key]
            if os.path.exists(path):
                ref_images.append(path)
            else:
                print(f"Warning: Briony ref '{key}' not found at {path}")

    model_id = MODELS[args.model]

    print(f"\n=== Salish Sea Dreaming - Gemini Generation ===\n")

    client = get_client()
    result = generate_image(
        client=client,
        model_id=model_id,
        prompt=prompt,
        ref_images=ref_images if ref_images else None,
        aspect_ratio=args.aspect,
        image_size=args.size,
        output_dir=args.output_dir,
        output_name=args.name,
        notes=args.notes,
    )

    if result:
        print(f"\n  Done! Image saved to: {result}")
    else:
        print(f"\n  No image generated.")


if __name__ == "__main__":
    main()
