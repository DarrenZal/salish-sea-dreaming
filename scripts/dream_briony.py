#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Briony's Drawings, Dreaming

Takes Briony's actual watercolors and transforms them into a "dreaming" state.
Her drawings are the FOUNDATIONAL visual layer. We don't replace them.
We make them breathe, glow, partially dissolve - as if seen through moving water.

From the Tech Team Briefing:
- Explore: slow morphing, breathing/drifting, partial emergence and dissolution
- Avoid: sharp cuts, aggressive transformations, high-frequency motion
- Nothing should look "more real" than her drawings
- If it looks like an AI art demo, stop

Usage:
    # Single image, default direction (bioluminescent)
    python3.11 dream_briony.py --images octopus

    # Multiple images with a specific direction
    python3.11 dream_briony.py --images octopus herring-panorama --direction nested-reality

    # Filter by Five Threads
    python3.11 dream_briony.py --thread salmon --direction night-ocean

    # All images, all directions
    python3.11 dream_briony.py --all

    # List available images and directions
    python3.11 dream_briony.py --list
"""

import openai
import base64
import os
import sys
import argparse
from datetime import datetime
from image_metadata import save_metadata

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
REFERENCE_DIR = os.path.join(PROJECT_DIR, 'assets', 'reference', 'briony-watercolors')

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set.")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            sys.exit(1)
        _client = openai.OpenAI(api_key=api_key)
    return _client

# ─── Source Image Catalog ────────────────────────────────────────────────────
# All 13 of Briony's watercolors with metadata for filtering and prompt context.

IMAGE_CATALOG = {
    "tidal-panorama": {
        "file": "2026-02-07T21-29-28.416_00_IMG_1473.jpg",
        "subject": "Panoramic tidal zone - octopus, kelp, boats, 'SLOW' sign",
        "threads": ["tlep", "herring"],
        "context": "A wide panoramic mural of the Salish Sea tidal zone. An octopus appears at one end, kelp forests, fishing boats, and a prominent 'SLOW' sign. This is the ecosystem seen as one continuous landscape.",
    },
    "octopus": {
        "file": "2026-02-07T21-29-28.416_01_IMG_1474.jpg",
        "subject": "Giant Pacific octopus close-up (T'lep)",
        "threads": ["tlep"],
        "context": "A vivid close-up watercolor of a Giant Pacific octopus - red-coral body, tentacles reaching outward. T'lep: nine brains, decentralized intelligence, witness and executive function from the potlatch ceremony.",
    },
    "kelp-divers": {
        "file": "2026-02-07T21-29-28.416_02_IMG_1475.jpg",
        "subject": "Kelp forest with divers, herring eggs on eelgrass",
        "threads": ["herring", "kelp"],
        "context": "Underwater kelp forest scene with human divers swimming among the fronds. Herring eggs visible on eelgrass. Crabs, fish, and the layered underwater world Briony depicts with scientific precision.",
    },
    "herring-panorama": {
        "file": "2026-02-07T21-29-28.416_03_IMG_1476.jpg",
        "subject": "Herring spawn panorama - whales, seabirds, boats",
        "threads": ["herring", "orca"],
        "context": "A wide panoramic scene of the herring spawn event. Whales breach, seabirds circle, fishing boats gather. Above and below the water line. The annual gathering that feeds the entire ecosystem.",
    },
    "eelgrass": {
        "file": "2026-02-07T21-29-28.416_04_IMG_1477.jpg",
        "subject": "Eelgrass meadow - oystercatchers, sea stars, crabs",
        "threads": ["herring"],
        "context": "An eelgrass meadow scene with oystercatchers walking on the surface, sea stars and crabs in the shallows. Islands in the background. The oystercatcher sees only the surface - Briony's basking shark metaphor made visible. What lies beneath is hidden from those who walk above.",
    },
    "kelp-underwater": {
        "file": "2026-02-07T21-29-28.416_05_IMG_1478.jpg",
        "subject": "Kelp forest underwater - bold blues, rockfish",
        "threads": ["kelp"],
        "context": "A bold underwater view of the kelp forest. Deep blues and teals dominate. Rockfish, sea stars, waves above. The vertical world of kelp as cathedral - ancient, breathing, full of life at every depth.",
    },
    "salmon-stream": {
        "file": "2026-02-07T21-29-28.416_06_IMG_1479.jpg",
        "subject": "Salmon stream cross-section - bears, old growth",
        "threads": ["salmon", "cedar"],
        "context": "A cross-section view of a salmon stream. Above: old growth forest, bears fishing. Below: spawning salmon fighting upstream. The salmon-forest cycle - nutrients from ocean to forest and back. Life feeding life.",
    },
    "ink-tree-wide": {
        "file": "2026-02-07T21-29-28.416_07_IMG_1483.jpg",
        "subject": "Ink tree - roots mirror canopy (wide)",
        "threads": ["cedar"],
        "context": "A striking ink drawing where the tree's root system mirrors its canopy above ground. What grows above, grows below. The underground world as reflection of the visible. Mycelium, roots, hidden networks.",
    },
    "ink-tree-detail": {
        "file": "2026-02-07T21-29-28.416_08_IMG_1484.jpg",
        "subject": "Ink tree - close crop, root/branch detail",
        "threads": ["cedar"],
        "context": "Close crop of the same ink tree drawing. Fine detail of the root and branch network visible. Every branch above has a root below. The drawing style is precise, almost scientific - but the mirroring suggests something dreamlike.",
    },
    "seasonal-wheel": {
        "file": "2026-02-07T21-29-28.416_09_IMG_1485.jpg",
        "subject": "Seasonal nature wheel mandala",
        "threads": ["camas"],
        "context": "A circular mandala of seasonal nature observations - leaves, feathers, fungi, insects, seeds arranged in a wheel of time. The year as a cycle, not a line. Indigenous worldview of circular time embedded in natural observation.",
    },
    "flower-wheel": {
        "file": "2026-02-07T21-29-28.416_10_IMG_1486.jpg",
        "subject": "Botanical flower wheel with species names",
        "threads": ["camas"],
        "context": "A botanical illustration arranged as a wheel - camas, shooting star, and other native species with their names. Scientific precision meets artistic beauty. The meadow ecosystem as a mandala of relationships.",
    },
    "flower-detail": {
        "file": "2026-02-07T21-29-28.416_11_IMG_1488.jpg",
        "subject": "Close-up - duskywing butterfly, serviceberry",
        "threads": ["camas"],
        "context": "Close detail from the flower wheel - a duskywing butterfly on serviceberry blossoms, larkspur nearby. The intimate scale of the meadow ecosystem. Pollination, interdependence, beauty in the small.",
    },
    "herring-latest": {
        "file": "2026-02-08T08-03-32.497_00_signal-2026-02-08-070332.jpeg",
        "subject": "Herring/lingcod underwater with oystercatcher",
        "threads": ["herring"],
        "context": "Briony's most recent watercolor shared Feb 8. Underwater scene with herring and lingcod, an oystercatcher visible on the surface. The surface/depth divide. What the bird cannot see below.",
    },
}


# ─── Dream Directions ────────────────────────────────────────────────────────
# Reusable prompt templates. Each gets composed with the per-image context.
# {context} is replaced with the image-specific context from the catalog.

DREAM_DIRECTIONS = {
    "bioluminescent": {
        "name": "Bioluminescent Breathing",
        "description": "Soft glow, breathing edges, inner luminosity. Subtle and restrained.",
        "prompt": (
            "Gently transform this watercolor illustration so it appears to be dreaming. "
            "Keep the exact composition, the hand-drawn line quality, and the naturalist style. "
            "The illustration should still be clearly recognizable as THIS drawing. "
            "{context} "
            "Add subtle bioluminescent glow to the living forms - a soft inner light "
            "that suggests the creatures and plants are quietly luminous. "
            "Soften the edges slightly as if the drawing is being seen through gently moving water. "
            "Some forms begin to partially dissolve at their edges into soft light. "
            "The color palette stays rooted in the original but gains a subtle inner luminosity - "
            "faint cyans and warm glows from within. "
            "This is a watercolor illustration that is breathing, not an AI replacement. "
            "Restraint is essential - less transformation is more."
        ),
    },
    "submerged": {
        "name": "Submerged / Seen Through Water",
        "description": "The drawing is viewed through moving water. Ripple distortion, deep blue-green shift.",
        "prompt": (
            "Transform this watercolor illustration as if it is being seen through gently moving water. "
            "Keep the composition and hand-drawn quality intact - this must still be recognizable as THIS drawing. "
            "{context} "
            "Add subtle water ripple distortion - forms waver slightly as if light is passing through "
            "a moving water surface above the drawing. "
            "Shift the color palette toward deeper blue-green tones, as if the drawing has sunk "
            "beneath the surface and is being viewed from above through seawater. "
            "The deeper parts of the image are more blue-shifted; areas near the top retain more warmth. "
            "Add caustic light patterns - the dancing light shapes that sunlight makes when it passes "
            "through a moving water surface. These should be subtle, dappled, natural. "
            "The feeling: this drawing is resting on the seabed, gently illuminated by filtered light. "
            "Preserve the watercolor medium - this is still a drawing, just one that has been submerged."
        ),
    },
    "nested-reality": {
        "name": "Nested Reality (Basking Shark Metaphor)",
        "description": "Hidden layers within layers. Creatures contain worlds. Surface becomes translucent. Briony's basking shark insight: nested realities, limited perspectives.",
        "prompt": (
            "Transform this watercolor illustration to reveal hidden layers within itself. "
            "Keep the hand-drawn quality and the watercolor medium visible throughout. "
            "{context} "
            "The key concept: NESTED REALITIES - worlds within worlds. "
            "The plankton inside the basking shark experience it as their whole universe; "
            "the oystercatcher on the surface cannot see what's below. "
            "Make some surfaces slightly translucent, so that deeper ecosystems shimmer beneath them. "
            "A creature's body might reveal hints of the world it contains or inhabits - "
            "faint forms within forms, ecosystems nested inside organisms. "
            "The boundary between inside and outside becomes soft and permeable. "
            "Add a subtle luminous quality to these revealed layers - they glow faintly "
            "as if seen through a window that is usually opaque. "
            "Do NOT add creatures that aren't in the original drawing. "
            "Instead, make the EXISTING forms reveal their hidden depths and connections. "
            "The drawing knows it contains more than it shows. Restraint - suggest, don't explain."
        ),
    },
    "night-ocean": {
        "name": "Night Ocean Dreaming",
        "description": "The scene as if the ocean is dreaming at night. Dark palette, forms emerge through bioluminescent outlines and phosphorescent trails.",
        "prompt": (
            "Transform this watercolor illustration as if the ocean is dreaming it at night. "
            "Keep the exact composition and hand-drawn line quality. "
            "{context} "
            "Dramatically darken the overall palette - deep ocean blacks and midnight blues. "
            "But the forms from the original drawing are still visible, now revealed through "
            "bioluminescent outlines and phosphorescent trails. "
            "Creatures glow faintly from within - soft cyan, blue, and occasional warm amber. "
            "The water itself has faint phosphorescent sparkle, as if disturbed plankton "
            "are tracing the shapes of the original drawing. "
            "Some edges trail off into luminous particles, like phosphorescence in a wake. "
            "The drawing remembers its shapes but sees them through darkness. "
            "This should feel like a memory of the daytime scene, dreamed by the ocean at night. "
            "Preserve the watercolor texture - this is still a drawing, now seen by moonlight "
            "and bioluminescence rather than sunlight."
        ),
    },
    "dissolving": {
        "name": "Dissolving Into Light",
        "description": "Higher intensity. Forms breaking apart into particles of light, releasing shapes back into the sea.",
        "prompt": (
            "Transform this watercolor illustration so its forms are dissolving into particles of light. "
            "This is a HIGHER INTENSITY transformation - more change than the subtle versions. "
            "But the drawing must still be recognizable. "
            "{context} "
            "The forms in the drawing are releasing their shapes - breaking apart at their edges "
            "into streams and clouds of luminous particles. Like the drawing is exhaling its shapes "
            "back into the sea. "
            "The center/core of each form remains most solid and recognizable. "
            "The edges and extremities dissolve into flowing particles of light - "
            "cyan, warm gold, soft white - that drift and scatter like bioluminescent plankton. "
            "Some areas of the composition have already dissolved into pure light-particle fields. "
            "Others are still holding their form but beginning to release. "
            "The overall feeling: the drawing is complete and now letting go. "
            "Beautiful dissolution, not destruction. The shapes return to the sea as light. "
            "Still maintain the watercolor quality in the surviving areas."
        ),
    },
}


def dream_drawing(image_path, direction_key, image_key, dry_run=False):
    """Transform one of Briony's drawings into a dreaming state."""
    direction = DREAM_DIRECTIONS[direction_key]
    image_info = IMAGE_CATALOG[image_key]

    # Compose the prompt: direction template + image-specific context
    prompt = direction["prompt"].replace("{context}", image_info["context"])

    # Output directory organized by direction
    direction_dir = os.path.join(OUTPUT_DIR, direction_key)
    os.makedirs(direction_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}_{image_key}.png"
    filepath = os.path.join(direction_dir, filename)

    print(f"\n{'─' * 60}")
    print(f"  Image:     {image_key} - {image_info['subject']}")
    print(f"  Direction: {direction_key} - {direction['name']}")
    print(f"  Threads:   {', '.join(image_info['threads'])}")
    print(f"  Output:    {filepath}")

    if dry_run:
        print(f"  [DRY RUN] Would generate image")
        print(f"  Prompt preview: {prompt[:150]}...")
        return None

    result = get_client().images.edit(
        model="gpt-image-1",
        image=open(image_path, "rb"),
        prompt=prompt,
        size="1536x1024",
        quality="high",
    )

    img_data = base64.b64decode(result.data[0].b64_json)
    with open(filepath, 'wb') as f:
        f.write(img_data)

    # Save metadata sidecar
    save_metadata(
        output_path=filepath,
        model="gpt-image-1",
        prompt=prompt,
        input_images=[image_path],
        config={"size": "1536x1024", "quality": "high"},
        source_direction=direction_key,
        source_image_keys=[image_key],
    )

    print(f"  Saved: {os.path.basename(filepath)}")
    return filepath


def resolve_image_path(image_key):
    """Get the full path for an image key, verifying it exists."""
    info = IMAGE_CATALOG[image_key]
    path = os.path.join(REFERENCE_DIR, info["file"])
    if not os.path.exists(path):
        print(f"Warning: {path} not found")
        return None
    return path


def list_catalog():
    """Print the full image catalog and dream directions."""
    print("\n=== Source Images ===\n")
    print(f"{'Key':<20} {'Threads':<20} {'Subject'}")
    print(f"{'─'*20} {'─'*20} {'─'*40}")
    for key, info in IMAGE_CATALOG.items():
        threads = ", ".join(info["threads"])
        print(f"{key:<20} {threads:<20} {info['subject']}")

    print("\n=== Dream Directions ===\n")
    print(f"{'Key':<20} {'Name':<35} {'Description'}")
    print(f"{'─'*20} {'─'*35} {'─'*50}")
    for key, info in DREAM_DIRECTIONS.items():
        print(f"{key:<20} {info['name']:<35} {info['description'][:50]}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Transform Briony's watercolors into dreaming states",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --images octopus                        # One image, bioluminescent
  %(prog)s --images octopus --direction nested-reality  # Specific direction
  %(prog)s --thread salmon cedar                   # All salmon & cedar images
  %(prog)s --direction night-ocean --all           # All images, night-ocean
  %(prog)s --all --all-directions                  # Everything (expensive!)
  %(prog)s --list                                  # Show catalog
  %(prog)s --dry-run --all                         # Preview without generating
        """,
    )
    parser.add_argument("--images", nargs="+", metavar="KEY",
                        help="Image keys to process (see --list)")
    parser.add_argument("--thread", nargs="+", metavar="THREAD",
                        help="Process all images for given Five Threads (salmon, cedar, herring, kelp, camas, tlep, orca)")
    parser.add_argument("--direction", default="bioluminescent",
                        choices=list(DREAM_DIRECTIONS.keys()),
                        help="Dream direction to apply (default: bioluminescent)")
    parser.add_argument("--all-directions", action="store_true",
                        help="Run all dream directions on selected images")
    parser.add_argument("--all", action="store_true",
                        help="Process all 13 source images")
    parser.add_argument("--list", action="store_true",
                        help="List available images and directions")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without calling the API")
    args = parser.parse_args()

    if args.list:
        list_catalog()
        return

    # Determine which images to process
    image_keys = []
    if args.all:
        image_keys = list(IMAGE_CATALOG.keys())
    elif args.thread:
        for key, info in IMAGE_CATALOG.items():
            if any(t in info["threads"] for t in args.thread):
                image_keys.append(key)
    elif args.images:
        for key in args.images:
            if key not in IMAGE_CATALOG:
                print(f"Error: Unknown image key '{key}'. Use --list to see available images.")
                sys.exit(1)
            image_keys.append(key)
    else:
        parser.print_help()
        return

    # Determine which directions to run
    directions = list(DREAM_DIRECTIONS.keys()) if args.all_directions else [args.direction]

    # Summary
    total = len(image_keys) * len(directions)
    print("=== Salish Sea Dreaming - Making Briony's Drawings Dream ===")
    print(f"Principle: Her drawings are the visual DNA. We add breath, not replacement.\n")
    print(f"Images:     {len(image_keys)}")
    print(f"Directions: {', '.join(directions)}")
    print(f"Total:      {total} image(s) to generate")
    if not args.dry_run:
        est_cost = total * 0.12
        print(f"Est. cost:  ~${est_cost:.2f}")
    print()

    generated = []
    errors = []

    for direction_key in directions:
        print(f"\n{'═' * 60}")
        print(f"  Direction: {direction_key} - {DREAM_DIRECTIONS[direction_key]['name']}")
        print(f"{'═' * 60}")

        for image_key in image_keys:
            image_path = resolve_image_path(image_key)
            if not image_path:
                errors.append((image_key, direction_key, "File not found"))
                continue
            try:
                path = dream_drawing(image_path, direction_key, image_key, dry_run=args.dry_run)
                if path:
                    generated.append(path)
            except Exception as e:
                print(f"  Error: {e}")
                errors.append((image_key, direction_key, str(e)))

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  COMPLETE")
    print(f"{'═' * 60}")
    if args.dry_run:
        print(f"  [DRY RUN] Would have generated {total} images")
    else:
        print(f"  Generated: {len(generated)} images")
        for g in generated:
            print(f"    {g}")
    if errors:
        print(f"\n  Errors: {len(errors)}")
        for img, direction, err in errors:
            print(f"    {img} / {direction}: {err}")


if __name__ == "__main__":
    main()
