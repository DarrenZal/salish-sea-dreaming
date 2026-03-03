#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Video Loop Creator

Creates Instagram-ready video loops from dream images using FFmpeg + Pillow.

Modes:
  - crossfade: Smooth crossfade between dream versions of the same source image
  - kenburns: Slow zoom/pan across a single dream image (contemplative)
  - montage: Crossfade sequence across Five Threads (one image per thread)

Output formats:
  - square (1:1) for Instagram feed
  - portrait (4:5) for Instagram feed
  - story (9:16) for Instagram stories/reels
  - landscape (16:9) for web/presentations

Usage:
    # Ken Burns loop from a single image
    python3.11 create_loops.py --mode kenburns --input path/to/image.png

    # Crossfade between multiple images
    python3.11 create_loops.py --mode crossfade --input img1.png img2.png img3.png

    # Five Threads montage (auto-selects best image per thread)
    python3.11 create_loops.py --mode montage

    # Specify aspect ratio
    python3.11 create_loops.py --mode kenburns --input image.png --format square

    # All formats at once
    python3.11 create_loops.py --mode kenburns --input image.png --format all
"""

import os
import sys
import argparse
import subprocess
import glob
import shutil
import tempfile
from PIL import Image
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..')
EXPERIMENTS_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'experiments')
VIDEO_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'video-loops')

sys.path.insert(0, SCRIPT_DIR)
from dream_briony import IMAGE_CATALOG, DREAM_DIRECTIONS

# Output format specs: (width, height, name)
FORMATS = {
    "square":    (1080, 1080, "1:1 Instagram Feed"),
    "portrait":  (1080, 1350, "4:5 Instagram Feed"),
    "story":     (1080, 1920, "9:16 Instagram Story/Reel"),
    "landscape": (1920, 1080, "16:9 Web/Presentation"),
}

# Five Threads representative images (order matters for montage)
FIVE_THREADS_ORDER = [
    ("herring", "herring-panorama"),
    ("tlep", "octopus"),
    ("kelp", "kelp-underwater"),
    ("salmon", "salmon-stream"),
    ("camas", "seasonal-wheel"),
]


def check_ffmpeg():
    """Verify FFmpeg is available."""
    if not shutil.which("ffmpeg"):
        print("Error: FFmpeg not found. Install with: brew install ffmpeg")
        sys.exit(1)


def crop_to_format(image_path, width, height, output_path):
    """Center-crop and resize an image to the target format."""
    img = Image.open(image_path).convert("RGB")

    # Calculate crop to match target aspect ratio
    target_ratio = width / height
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider - crop sides
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller - crop top/bottom
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    img = img.resize((width, height), Image.LANCZOS)
    img.save(output_path, quality=95)
    return output_path


def create_kenburns(image_path, output_path, width, height, duration=12, fps=30):
    """Create a Ken Burns (slow zoom + pan) video loop from a single image.

    Strategy: zoom in slowly, then the loop point is hidden by a subtle
    crossfade with the starting frame. FFmpeg's zoompan filter handles this.
    """
    # Prepare high-res source (2x target for zoom headroom)
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "source.png")
        img = Image.open(image_path).convert("RGB")

        # Upscale to 2x target for zoom headroom
        src_w, src_h = width * 2, height * 2
        target_ratio = width / height
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        img = img.resize((src_w, src_h), Image.LANCZOS)
        img.save(src, quality=100)

        total_frames = duration * fps

        # Zoompan: slow zoom from 1.0x to 1.15x with gentle drift
        # Then crossfade last 2 seconds with first 2 seconds for seamless loop
        zoom_expr = f"1+0.15*on/{total_frames}"
        # Gentle drift: start slightly left-of-center, drift right
        x_expr = f"(iw-iw/zoom)/2 + 30*sin(2*PI*on/{total_frames})"
        y_expr = f"(ih-ih/zoom)/2 + 20*cos(2*PI*on/{total_frames})"

        # First pass: generate the zoompan video
        raw = os.path.join(tmpdir, "raw.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-i", src,
            "-vf", (
                f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
                f":d={total_frames}:s={width}x{height}:fps={fps},"
                f"format=yuv420p"
            ),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-t", str(duration),
            raw,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FFmpeg zoompan error: {result.stderr[-200:]}")
            return None

        # Make it loop smoothly: crossfade last 2s with first 2s
        fade_dur = 2
        cmd_loop = [
            "ffmpeg", "-y",
            "-i", raw,
            "-filter_complex", (
                f"[0]split[main][tail];"
                f"[tail]trim=start={duration - fade_dur},setpts=PTS-STARTPTS[tailclip];"
                f"[main]trim=start=0:end={duration - fade_dur},setpts=PTS-STARTPTS[mainclip];"
                f"[tailclip][mainclip]xfade=transition=fade:duration={fade_dur}:offset=0,"
                f"format=yuv420p"
            ),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            output_path,
        ]
        result = subprocess.run(cmd_loop, capture_output=True, text=True)
        if result.returncode != 0:
            # Fall back to the raw version if loop crossfade fails
            print(f"  Loop crossfade failed, using raw zoompan")
            shutil.copy(raw, output_path)

    return output_path


def create_crossfade(image_paths, output_path, width, height, hold=4, fade=2, fps=30):
    """Create a crossfade loop between multiple images.

    Each image is held for `hold` seconds, then crossfades to the next over `fade` seconds.
    The last image crossfades back to the first for a seamless loop.
    """
    if len(image_paths) < 2:
        print("  Crossfade requires at least 2 images")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare all images at target resolution
        prepped = []
        for i, path in enumerate(image_paths):
            out = os.path.join(tmpdir, f"frame_{i:03d}.png")
            crop_to_format(path, width, height, out)
            prepped.append(out)

        # Each clip: hold + fade duration, except last which loops back
        clip_dur = hold + fade
        n = len(prepped)

        # Build FFmpeg filter: create video from each still, then xfade chain
        inputs = []
        for p in prepped:
            inputs.extend(["-loop", "1", "-t", str(clip_dur), "-i", p])

        # Build xfade chain
        filter_parts = []
        prev = "[0:v]"
        for i in range(1, n):
            curr = f"[{i}:v]"
            out_label = f"[v{i}]"
            offset = hold + (i - 1) * hold  # Each subsequent xfade starts after previous hold
            filter_parts.append(
                f"{prev}{curr}xfade=transition=fade:duration={fade}:offset={hold}{out_label}"
            )
            prev = out_label

        # Loop back to first: crossfade last result with first image
        inputs.extend(["-loop", "1", "-t", str(clip_dur), "-i", prepped[0]])
        loop_input = f"[{n}:v]"
        filter_parts.append(
            f"{prev}{loop_input}xfade=transition=fade:duration={fade}:offset={hold}[vout]"
        )

        filter_complex = ";".join(filter_parts) + ";[vout]format=yuv420p[final]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[final]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-r", str(fps),
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  FFmpeg crossfade error: {result.stderr[-300:]}")
            return None

    return output_path


def create_montage(output_path, width, height, direction="bioluminescent", hold=5, fade=3, fps=30):
    """Create Five Threads montage: one dreaming image per thread in sequence."""
    # Find best available image for each thread
    image_paths = []
    for thread, default_key in FIVE_THREADS_ORDER:
        # Look for generated images in the specified direction
        dir_path = os.path.join(EXPERIMENTS_DIR, direction)
        if os.path.isdir(dir_path):
            matches = sorted(glob.glob(os.path.join(dir_path, f"*_{default_key}.png")))
            if matches:
                image_paths.append(matches[-1])  # Most recent
                continue

        # Fall back: any direction
        for d in DREAM_DIRECTIONS:
            d_path = os.path.join(EXPERIMENTS_DIR, d)
            if os.path.isdir(d_path):
                matches = sorted(glob.glob(os.path.join(d_path, f"*_{default_key}.png")))
                if matches:
                    image_paths.append(matches[-1])
                    break

    if len(image_paths) < 2:
        print(f"  Not enough thread images found ({len(image_paths)}). Generate more dream images first.")
        print(f"  Looked for: {[key for _, key in FIVE_THREADS_ORDER]}")
        return None

    print(f"  Montage: {len(image_paths)} images from Five Threads")
    for p in image_paths:
        print(f"    {os.path.basename(p)}")

    return create_crossfade(image_paths, output_path, width, height, hold=hold, fade=fade, fps=fps)


def find_dream_images_for_key(image_key, direction=None):
    """Find all generated dream versions of a specific source image."""
    paths = []
    dirs = [direction] if direction else list(DREAM_DIRECTIONS.keys())
    for d in dirs:
        dir_path = os.path.join(EXPERIMENTS_DIR, d)
        if os.path.isdir(dir_path):
            matches = sorted(glob.glob(os.path.join(dir_path, f"*_{image_key}.png")))
            paths.extend(matches)
    # Also check legacy root
    if not direction:
        root_matches = sorted(glob.glob(os.path.join(EXPERIMENTS_DIR, f"*dream-{image_key}*.png")))
        paths.extend(root_matches)
    return paths


def get_reference_path(image_key):
    """Get path to the original Briony watercolor for an image key."""
    if image_key not in IMAGE_CATALOG:
        return None
    info = IMAGE_CATALOG[image_key]
    ref_dir = os.path.join(os.path.dirname(EXPERIMENTS_DIR), '..', 'reference', 'briony-watercolors')
    path = os.path.join(ref_dir, info["file"])
    return path if os.path.exists(path) else None


def create_dreaming_waking(image_key, output_path, width, height, direction="bioluminescent",
                           hold=4, fade=3, fps=30):
    """Create a dreaming/waking loop: original → dream → original.

    Shows the painting transforming into its dream state and back.
    The loop point is seamless because it starts and ends with the original.
    """
    # Find original
    ref_path = get_reference_path(image_key)
    if not ref_path:
        print(f"  Error: Original not found for '{image_key}'")
        return None

    # Find best dream version
    dream_images = find_dream_images_for_key(image_key, direction=direction)
    if not dream_images:
        # Try any direction
        dream_images = find_dream_images_for_key(image_key)
    if not dream_images:
        print(f"  Error: No dream images found for '{image_key}'")
        return None

    dream_path = dream_images[-1]  # Most recent
    print(f"  Original:  {os.path.basename(ref_path)}")
    print(f"  Dream:     {os.path.basename(dream_path)}")
    print(f"  Direction: {direction}")

    # Build: original → dream → original (seamless loop)
    image_paths = [ref_path, dream_path, ref_path]
    return create_crossfade(image_paths, output_path, width, height,
                            hold=hold, fade=fade, fps=fps)


def create_dreaming_cycle(image_keys, output_path, width, height,
                          directions=None, hold=3, fade=3, fps=30):
    """Create a dreaming cycle: paintings travel through multiple dream states.

    For each painting: original → dream1 → dream2 → next painting's original → ...
    A continuous journey through paintings AND dream states.
    """
    if directions is None:
        directions = ["bioluminescent", "night-ocean", "dissolving"]

    image_paths = []
    labels = []

    for key in image_keys:
        ref_path = get_reference_path(key)
        if not ref_path:
            continue

        # Start with original
        image_paths.append(ref_path)
        labels.append(f"original: {key}")

        # Add available dream versions
        for d in directions:
            dreams = find_dream_images_for_key(key, direction=d)
            if dreams:
                image_paths.append(dreams[-1])
                labels.append(f"{d}: {key}")

    if len(image_paths) < 2:
        print(f"  Not enough images for dreaming cycle")
        return None

    print(f"  Dreaming cycle: {len(image_paths)} frames")
    for label in labels:
        print(f"    {label}")

    return create_crossfade(image_paths, output_path, width, height,
                            hold=hold, fade=fade, fps=fps)


def main():
    parser = argparse.ArgumentParser(
        description="Create Instagram-ready video loops from dream images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  kenburns     Slow zoom/pan across a single image (contemplative)
  crossfade    Smooth crossfade between multiple images
  montage      Five Threads sequence (auto-selects best per thread)
  dreaming     Original → dream → original (shows transformation)
  cycle        Journey through paintings and dream states

Examples:
  %(prog)s --mode kenburns --input path/to/image.png
  %(prog)s --mode dreaming --image-key octopus --direction bioluminescent
  %(prog)s --mode dreaming --image-key octopus --format all
  %(prog)s --mode cycle --image-key octopus kelp-underwater salmon-stream
  %(prog)s --mode montage --format story
        """,
    )
    parser.add_argument("--mode", required=True,
                        choices=["kenburns", "crossfade", "montage", "dreaming", "cycle"],
                        help="Video creation mode")
    parser.add_argument("--input", nargs="+", metavar="PATH",
                        help="Input image path(s). For kenburns: 1 image. For crossfade: 2+.")
    parser.add_argument("--image-key", nargs="+", metavar="KEY",
                        help="Painting key(s) from catalog (for dreaming/cycle/crossfade)")
    parser.add_argument("--format", default="square", choices=list(FORMATS.keys()) + ["all"],
                        help="Output format/aspect ratio (default: square)")
    parser.add_argument("--direction", default="bioluminescent",
                        choices=list(DREAM_DIRECTIONS.keys()),
                        help="Dream direction (default: bioluminescent)")
    parser.add_argument("--duration", type=int, default=12,
                        help="Duration in seconds for kenburns (default: 12)")
    parser.add_argument("--hold", type=int, default=4,
                        help="Hold time per image in crossfade/montage (default: 4)")
    parser.add_argument("--fade", type=int, default=2,
                        help="Fade duration for crossfade/montage (default: 2)")
    parser.add_argument("--name", metavar="NAME",
                        help="Custom output filename prefix")
    args = parser.parse_args()

    check_ffmpeg()
    os.makedirs(VIDEO_DIR, exist_ok=True)

    print("=== Salish Sea Dreaming - Video Loop Creator ===\n")

    # Resolve input images for crossfade/kenburns
    input_paths = args.input or []
    if args.image_key and args.mode == "crossfade":
        # For crossfade with image-key, find all dream versions
        for key in args.image_key:
            found = find_dream_images_for_key(key)
            input_paths.extend(found)
        if not input_paths:
            print(f"Error: No dream images found for keys: {args.image_key}")
            sys.exit(1)
        print(f"Found {len(input_paths)} dream images")

    # Validate inputs for modes that need them
    if args.mode == "kenburns" and len(input_paths) < 1:
        print("Error: Ken Burns mode requires --input with at least 1 image")
        sys.exit(1)
    if args.mode == "crossfade" and len(input_paths) < 2:
        print("Error: Crossfade mode requires --input with at least 2 images (or use --image-key)")
        sys.exit(1)
    if args.mode in ("dreaming", "cycle") and not args.image_key:
        print(f"Error: {args.mode} mode requires --image-key")
        sys.exit(1)

    # Determine formats to generate
    if args.format == "all":
        formats_to_run = list(FORMATS.items())
    else:
        formats_to_run = [(args.format, FORMATS[args.format])]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    generated = []

    for fmt_key, (width, height, fmt_name) in formats_to_run:
        # Build output filename
        name_parts = [timestamp, args.mode]
        if args.name:
            name_parts.append(args.name)
        elif args.image_key:
            name_parts.append("-".join(args.image_key[:3]))
        elif input_paths:
            basename = os.path.splitext(os.path.basename(input_paths[0]))[0]
            parts = basename.split("_", 1)
            name_parts.append(parts[-1] if len(parts) > 1 else basename)
        name_parts.append(fmt_key)
        output_name = "_".join(name_parts) + ".mp4"
        output_path = os.path.join(VIDEO_DIR, output_name)

        print(f"\n  Creating: {fmt_name} ({width}x{height})")
        print(f"  Output:   {output_name}")

        path = None

        if args.mode == "kenburns":
            path = create_kenburns(input_paths[0], output_path, width, height,
                                   duration=args.duration)
        elif args.mode == "crossfade":
            path = create_crossfade(input_paths, output_path, width, height,
                                    hold=args.hold, fade=args.fade)
        elif args.mode == "montage":
            path = create_montage(output_path, width, height,
                                  direction=args.direction,
                                  hold=args.hold, fade=args.fade)
        elif args.mode == "dreaming":
            path = create_dreaming_waking(args.image_key[0], output_path, width, height,
                                          direction=args.direction,
                                          hold=args.hold, fade=args.fade)
        elif args.mode == "cycle":
            path = create_dreaming_cycle(args.image_key, output_path, width, height,
                                         hold=args.hold, fade=args.fade)

        if path:
            generated.append(path)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  Size:     {size_mb:.1f} MB")

    print(f"\n=== Done! Created {len(generated)} video(s) ===")
    for g in generated:
        print(f"  {g}")


if __name__ == "__main__":
    main()
