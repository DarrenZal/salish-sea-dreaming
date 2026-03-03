#!/usr/bin/env python3.11
"""
Salish Sea Dreaming - Video Generation with Veo

Two modes:
  1. Transitions: Keyframe-controlled transitions between paintings (Veo 3.1)
  2. Animate: Bring a single painting to life with natural motion (Veo 3.1)

The animate mode uses the proven v3 "comes alive" prompt that makes Briony's
watercolors breathe - fish swim, birds fly, water ripples - all while
preserving the original style and composition. Simple prompts win.

Usage:
    # Animate a single painting by catalog key
    python3.11 scripts/dream_video.py --animate octopus

    # Animate multiple paintings
    python3.11 scripts/dream_video.py --animate octopus kelp-underwater salmon-stream

    # Animate ALL cataloged paintings
    python3.11 scripts/dream_video.py --animate-all

    # Animate a dream image (from dream_briony.py output)
    python3.11 scripts/dream_video.py --animate-image path/to/dream.png

    # Single transition test
    python3.11 scripts/dream_video.py \
      --first-frame VisualArt/.../Offshore.jpg \
      --last-frame VisualArt/.../Inshore.jpg \
      --prompt "..." --duration 8

    # Generate the full Central Coast triptych
    python3.11 scripts/dream_video.py --triptych

    # List available presets
    python3.11 scripts/dream_video.py --list-presets
"""

import os
import sys
import time
import argparse
import subprocess
import urllib.request
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
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'video-transitions')
ILLUSTRATIONS_DIR = os.path.join(PROJECT_DIR, 'VisualArt', 'Brionny', 'Illustrations')

sys.path.insert(0, SCRIPT_DIR)
from image_metadata import save_metadata
from dream_briony import IMAGE_CATALOG, REFERENCE_DIR

# Veo model - 3.1 preview supports lastFrame keyframe control
VEO_MODEL = "veo-3.1-generate-preview"

# Output directory for animated paintings
ANIMATE_DIR = os.path.join(PROJECT_DIR, 'assets', 'output', 'animated-paintings')

# ─── Central Coast Triptych Source Images ────────────────────────────────────

TRIPTYCH_IMAGES = {
    "offshore": os.path.join(
        ILLUSTRATIONS_DIR,
        "Central-Coast-Offshore-Scene",
        "Central+Coast+Offshore+scene_BrionyPenn.jpg",
    ),
    "inshore": os.path.join(
        ILLUSTRATIONS_DIR,
        "Central-Coast-Inshore-Scene",
        "Central+Coast+Inshore+scene_BrionyPenn.jpg",
    ),
    "estuary": os.path.join(
        ILLUSTRATIONS_DIR,
        "Central-Coast-Estuary-Scene",
        "Central+coast+estuary+scene_BrionyPenn.jpg",
    ),
}

# ─── Transition Prompts ─────────────────────────────────────────────────────

TRIPTYCH_TRANSITIONS = [
    {
        "name": "offshore-to-inshore",
        "first": "offshore",
        "last": "inshore",
        # This is the exact v3 prompt that produced the best result
        "prompt": (
            "A naturalist watercolor illustration of the BC coast magically "
            "comes alive. The camera slowly drifts from deep ocean toward shore. "
            "Underwater, fish schools swirl and dart through swaying kelp forests. "
            "Sea lions twist and dive. Above the waterline, eagles and seabirds "
            "fly across a sky with drifting clouds. Ocean swells rise and fall. "
            "The waterline itself undulates gently. Small details animate "
            "everywhere: crabs crawl, jellyfish pulse, anemones wave their "
            "tentacles, bubbles rise. The painted mountains in the distance drift "
            "slowly closer. The overall feeling is a living, breathing ecosystem "
            "captured in watercolor - every brushstroke seems to pulse with life. "
            "Smooth continuous motion throughout, never static."
        ),
    },
    {
        "name": "inshore-to-estuary",
        "first": "inshore",
        "last": "estuary",
        # Adapted from v3 for the second transition
        "prompt": (
            "A naturalist watercolor illustration of the BC coast magically "
            "comes alive. The camera slowly drifts from coastal waters into a "
            "river estuary. Underwater, herring schools swirl and give way to "
            "salmon swimming upstream in spawning colors. Sea stars cling to "
            "rocks. Above the waterline, the forest closes in with old-growth "
            "cedar and spruce. Bears wade into the shallows fishing for salmon. "
            "Birds fly across a sky with drifting clouds. The water surface "
            "ripples and flows with the current. Small details animate "
            "everywhere: crabs crawl on rocks, insects hover above the water, "
            "leaves flutter down from trees, river current carries fallen "
            "needles. The overall feeling is arriving home after a long ocean "
            "journey - a living, breathing ecosystem captured in watercolor. "
            "Every brushstroke seems to pulse with life. Smooth continuous "
            "motion throughout, never static."
        ),
    },
]


# ─── Animation Prompts ─────────────────────────────────────────────────────
# Per-painting motion descriptions appended to the base "comes alive" prompt.
# Simple prompts win - just describe what should move, no constraints.

ANIMATE_BASE_PROMPT = (
    "Gently animate this watercolor painting. Do not change the composition, "
    "do not add any new elements, do not change the style or colors. "
    "Only bring the existing elements to life with subtle natural movement: "
)

ANIMATE_DETAILS = {
    "tidal-panorama": (
        "The octopus shifts and breathes, tentacles curling slowly. "
        "Kelp sways in the current. Boats rock gently on the water. "
        "Seabirds fly overhead. Waves lap against the shore. "
        "Small fish dart through the underwater sections. "
        "The water surface ripples and reflects light."
    ),
    "octopus": (
        "The octopus breathes slowly, its body pulsing with color. "
        "Tentacles curl and uncurl with fluid grace. "
        "The eye tracks slowly, alive and watchful. "
        "Ink lines seem to breathe and shift subtly. "
        "The water around the octopus ripples gently."
    ),
    "kelp-divers": (
        "Kelp fronds sway gracefully in the current. "
        "Divers kick slowly through the water. "
        "Small fish dart between the kelp. "
        "Herring eggs shimmer on the eelgrass. "
        "Crabs creep along the bottom. Bubbles rise."
    ),
    "herring-panorama": (
        "Whales breach and dive slowly. Herring school and swirl in silver clouds. "
        "Seabirds circle and dive from above. Boats rock on the gentle swell. "
        "The water surface ripples and flows. Waves lap at the shore. "
        "Everything moves with the rhythm of the sea."
    ),
    "eelgrass": (
        "Oystercatchers peck and walk along the shore. "
        "Crabs scuttle sideways through the shallows. "
        "Small fish school and dart through the eelgrass. "
        "Sea stars creep slowly on the rocks. "
        "Water ripples and light dances on the surface."
    ),
    "kelp-underwater": (
        "Kelp sways and undulates in the deep current. "
        "Rockfish dart and hover among the fronds. "
        "Sea stars creep along the rocks below. "
        "Light filters down through the water, shifting and dappling. "
        "Waves roll gently across the surface above."
    ),
    "salmon-stream": (
        "Bears wade slowly in the stream, fishing for salmon. "
        "Salmon leap and fight upstream in flashes of red and silver. "
        "Eagles circle overhead, wings spread wide. "
        "The stream current flows and ripples over rocks. "
        "Trees sway slightly in the wind. Leaves drift down."
    ),
    "ink-tree-wide": (
        "Roots pulse slowly with life underground. "
        "Branches sway gently in a light breeze. "
        "Birds nest and flutter in the canopy. "
        "The mirror between roots and branches shifts subtly. "
        "Small creatures move along the trunk."
    ),
    "ink-tree-detail": (
        "Fine branches sway in a gentle breeze. "
        "Roots pulse and shift underground. "
        "The ink lines breathe with organic movement. "
        "Birds flit between the detailed branches."
    ),
    "seasonal-wheel": (
        "Insects buzz and flutter around the wheel. "
        "Leaves shift in a gentle spiral motion. "
        "Fungi pulse slowly with life. "
        "Seeds drift and scatter on invisible wind. "
        "The wheel slowly rotates, seasons flowing into each other."
    ),
    "flower-wheel": (
        "Flowers bob gently as if in a breeze. "
        "Butterflies flutter between the blooms. "
        "Petals shift and unfurl slowly. "
        "Bees hover and move from flower to flower. "
        "The botanical wheel breathes with life."
    ),
    "flower-detail": (
        "The duskywing butterfly opens and closes its wings slowly. "
        "Serviceberry blossoms sway in a light breeze. "
        "Larkspur petals shift gently. "
        "Small insects move through the flowers."
    ),
    "herring-latest": (
        "Herring school and dart in silver flashes underwater. "
        "The lingcod hovers and shifts position slowly. "
        "The oystercatcher on the surface pecks and walks. "
        "Water ripples between the above and below worlds. "
        "Seaweed sways in the gentle current."
    ),
}

ANIMATE_TAIL = (
    "Keep the exact same scene, framing, and watercolor style throughout. "
    "Smooth continuous motion, never static."
)


def get_client():
    """Get Google GenAI client (requires GOOGLE_API_KEY env var)."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Set it with: export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    from google import genai
    return genai.Client()


def generate_transition(client, first_frame_path, last_frame_path, prompt,
                        duration=8, aspect_ratio="9:16", resolution="720p",
                        output_dir=None, output_name=None, notes=None):
    """Generate a video transition between two keyframe images using Veo.

    Args:
        client: genai.Client instance
        first_frame_path: Path to the first frame image
        last_frame_path: Path to the last frame image
        prompt: Text prompt describing the transition
        duration: Video duration in seconds (5 or 8)
        aspect_ratio: "9:16" (portrait), "16:9" (landscape), "1:1" (square)
        resolution: "720p" or "1080p" (1080p requires duration=8)
        output_dir: Override output directory
        output_name: Custom filename (without extension)
        notes: Free-text notes for metadata

    Returns:
        Path to saved video, or None on failure
    """
    from google.genai import types

    out_dir = output_dir or OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = output_name or "transition"
    outpath = os.path.join(out_dir, f"{ts}_{name}.mp4")

    print(f"\n{'─' * 60}")
    print(f"  Model:       {VEO_MODEL}")
    print(f"  First frame: {os.path.basename(first_frame_path)}")
    print(f"  Last frame:  {os.path.basename(last_frame_path)}")
    print(f"  Duration:    {duration}s")
    print(f"  Aspect:      {aspect_ratio}")
    print(f"  Resolution:  {resolution}")
    print(f"  Output:      {outpath}")
    print(f"  Generating...")

    # Load keyframe images
    with open(first_frame_path, "rb") as f:
        first_bytes = f.read()
    with open(last_frame_path, "rb") as f:
        last_bytes = f.read()

    first_mime = "image/jpeg" if first_frame_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    last_mime = "image/jpeg" if last_frame_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

    first_img = types.Image(imageBytes=first_bytes, mimeType=first_mime)
    last_img = types.Image(imageBytes=last_bytes, mimeType=last_mime)

    # Generate video (returns an async operation)
    config = types.GenerateVideosConfig(
        aspectRatio=aspect_ratio,
        durationSeconds=duration,
        resolution=resolution,
        lastFrame=last_img,
        numberOfVideos=1,
    )

    # Submit with auto-retry on rate limit (429)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            operation = client.models.generate_videos(
                model=VEO_MODEL,
                prompt=prompt,
                image=first_img,
                config=config,
            )
            break
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait = 60 * (attempt + 1)  # 60s, 120s, 180s, 240s
                print(f"  Rate limited. Waiting {wait}s before retry "
                      f"({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise

    # Poll until done (typically 11s to 6min)
    start_time = time.time()
    poll_count = 0
    while not operation.done:
        poll_count += 1
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        print(f"  Waiting... {mins}:{secs:02d} elapsed (poll #{poll_count})", end='\r')
        time.sleep(10)
        operation = client.operations.get(operation)

    elapsed = time.time() - start_time
    mins, secs = divmod(int(elapsed), 60)
    print(f"  Generation complete in {mins}:{secs:02d}                    ")

    # Check for errors
    if not operation.result or not operation.result.generated_videos:
        print(f"  Error: No video generated")
        if hasattr(operation, 'error') and operation.error:
            print(f"  Error details: {operation.error}")
        return None

    # Download video from URI (requires API key for auth)
    video = operation.result.generated_videos[0]
    video_uri = video.video.uri
    print(f"  Downloading from: {video_uri[:80]}...")

    # Add API key to download URL for authentication
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    sep = '&' if '?' in video_uri else '?'
    auth_uri = f"{video_uri}{sep}key={api_key}"
    urllib.request.urlretrieve(auth_uri, outpath)
    file_size = os.path.getsize(outpath)
    print(f"  Saved: {outpath} ({file_size / 1024 / 1024:.1f} MB)")

    # Save metadata sidecar
    json_path = save_metadata(
        output_path=outpath,
        model=VEO_MODEL,
        prompt=prompt,
        input_images=[first_frame_path, last_frame_path],
        config={
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration,
            "resolution": resolution,
            "type": "keyframe_transition",
            "first_frame": os.path.basename(first_frame_path),
            "last_frame": os.path.basename(last_frame_path),
        },
        notes=notes,
    )
    print(f"  Metadata: {json_path}")

    return outpath


def generate_animation(client, image_path, prompt, image_key=None,
                       duration=8, aspect_ratio="16:9", resolution="720p",
                       output_dir=None, output_name=None, notes=None):
    """Animate a single painting (no lastFrame - Veo brings it to life).

    Args:
        client: genai.Client instance
        image_path: Path to the source image
        prompt: Text prompt describing what should move
        image_key: Catalog key (for naming and metadata)
        duration: Video duration in seconds (5 or 8)
        aspect_ratio: "9:16" (portrait), "16:9" (landscape), "1:1" (square)
        resolution: "720p" or "1080p"
        output_dir: Override output directory
        output_name: Custom filename (without extension)
        notes: Free-text notes for metadata

    Returns:
        Path to saved video, or None on failure
    """
    from google.genai import types

    out_dir = output_dir or ANIMATE_DIR
    os.makedirs(out_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = output_name or (f"animate-{image_key}" if image_key else "animate")
    outpath = os.path.join(out_dir, f"{ts}_{name}.mp4")

    print(f"\n{'─' * 60}")
    print(f"  Mode:        animate (single painting)")
    print(f"  Model:       {VEO_MODEL}")
    print(f"  Source:      {os.path.basename(image_path)}")
    if image_key:
        print(f"  Key:         {image_key}")
    print(f"  Duration:    {duration}s")
    print(f"  Aspect:      {aspect_ratio}")
    print(f"  Resolution:  {resolution}")
    print(f"  Output:      {outpath}")
    print(f"  Generating...")

    # Load source image
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    mime = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"
    source_img = types.Image(imageBytes=img_bytes, mimeType=mime)

    # Generate video - NO lastFrame, just animate the single image
    config = types.GenerateVideosConfig(
        aspectRatio=aspect_ratio,
        durationSeconds=duration,
        resolution=resolution,
        numberOfVideos=1,
    )

    # Submit with auto-retry on rate limit (429)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            operation = client.models.generate_videos(
                model=VEO_MODEL,
                prompt=prompt,
                image=source_img,
                config=config,
            )
            break
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait = 60 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s before retry "
                      f"({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise

    # Poll until done
    start_time = time.time()
    poll_count = 0
    while not operation.done:
        poll_count += 1
        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        print(f"  Waiting... {mins}:{secs:02d} elapsed (poll #{poll_count})", end='\r')
        time.sleep(10)
        operation = client.operations.get(operation)

    elapsed = time.time() - start_time
    mins, secs = divmod(int(elapsed), 60)
    print(f"  Generation complete in {mins}:{secs:02d}                    ")

    # Check for errors
    if not operation.result or not operation.result.generated_videos:
        print(f"  Error: No video generated")
        if hasattr(operation, 'error') and operation.error:
            print(f"  Error details: {operation.error}")
        return None

    # Download video
    video = operation.result.generated_videos[0]
    video_uri = video.video.uri
    print(f"  Downloading from: {video_uri[:80]}...")

    api_key = os.environ.get('GOOGLE_API_KEY', '')
    sep = '&' if '?' in video_uri else '?'
    auth_uri = f"{video_uri}{sep}key={api_key}"
    urllib.request.urlretrieve(auth_uri, outpath)
    file_size = os.path.getsize(outpath)
    print(f"  Saved: {outpath} ({file_size / 1024 / 1024:.1f} MB)")

    # Save metadata sidecar
    json_path = save_metadata(
        output_path=outpath,
        model=VEO_MODEL,
        prompt=prompt,
        input_images=[image_path],
        config={
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration,
            "resolution": resolution,
            "type": "single_image_animation",
            "source_key": image_key,
        },
        notes=notes,
    )
    print(f"  Metadata: {json_path}")

    return outpath


def build_animate_prompt(image_key):
    """Build a full animation prompt for a catalog painting."""
    generic = (
        "fish swim and dart, birds fly and flap their wings, kelp and seaweed sway "
        "in the current, water surface ripples and flows, waves lap gently, "
        "clouds drift across the sky, trees sway slightly in the wind. "
        "Every living creature moves naturally. The water breathes."
    )
    details = ANIMATE_DETAILS.get(image_key, generic) if image_key else generic
    return f"{ANIMATE_BASE_PROMPT}{details} {ANIMATE_TAIL}"


def resolve_painting_path(image_key):
    """Get the full path for a painting from the catalog."""
    if image_key not in IMAGE_CATALOG:
        return None
    info = IMAGE_CATALOG[image_key]
    path = os.path.join(REFERENCE_DIR, info["file"])
    return path if os.path.exists(path) else None


def run_animate(client, image_keys, duration=8, aspect_ratio="16:9",
                resolution="720p", output_dir=None):
    """Animate multiple catalog paintings."""
    out_dir = output_dir or ANIMATE_DIR

    print("=" * 60)
    print("  Living Paintings - Bringing Watercolors to Life")
    print("=" * 60)

    generated = []
    errors = []

    for key in image_keys:
        path = resolve_painting_path(key)
        if not path:
            print(f"\n  Skipping {key}: file not found")
            errors.append(key)
            continue

        prompt = build_animate_prompt(key)
        subject = IMAGE_CATALOG[key]["subject"]
        print(f"\n  Animating: {key} - {subject}")

        try:
            result = generate_animation(
                client=client,
                image_path=path,
                prompt=prompt,
                image_key=key,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                output_dir=out_dir,
                notes=f"Living painting: {subject}",
            )
            if result:
                generated.append(result)
            else:
                errors.append(key)
        except Exception as e:
            print(f"  Error animating {key}: {e}")
            errors.append(key)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  ANIMATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Generated: {len(generated)} videos")
    for g in generated:
        print(f"    {os.path.basename(g)}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors:
            print(f"    {e}")
    print()

    return generated


def stitch_videos(video_paths, output_path):
    """Concatenate multiple videos using FFmpeg.

    Args:
        video_paths: List of paths to MP4 files to concatenate
        output_path: Path for the stitched output

    Returns:
        Path to stitched video, or None on failure
    """
    if len(video_paths) < 2:
        print("  Need at least 2 videos to stitch")
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Build FFmpeg filter_complex for concat
    inputs = []
    filter_parts = []
    for i, path in enumerate(video_paths):
        inputs.extend(["-i", path])
        filter_parts.append(f"[{i}:v]")

    filter_str = f"{''.join(filter_parts)}concat=n={len(video_paths)}:v=1:a=0[out]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        output_path,
    ]

    print(f"\n  Stitching {len(video_paths)} clips...")
    print(f"  Output: {output_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[:500]}")
        return None

    file_size = os.path.getsize(output_path)
    print(f"  Stitched: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
    return output_path


def run_triptych(client, duration=8, aspect_ratio="9:16", resolution="720p",
                 output_dir=None):
    """Generate the full Central Coast triptych: Offshore → Inshore → Estuary.

    Generates each transition, then stitches them into one continuous video.
    """
    out_dir = output_dir or OUTPUT_DIR
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    print("=" * 60)
    print("  Central Coast Triptych - Ecological Journey")
    print("  Offshore → Inshore → Estuary")
    print("=" * 60)

    # Verify source images
    for key, path in TRIPTYCH_IMAGES.items():
        if not os.path.exists(path):
            print(f"  Error: Missing {key} image: {path}")
            return None
        print(f"  {key:<10} OK  {os.path.basename(path)}")

    generated = []
    for transition in TRIPTYCH_TRANSITIONS:
        first_path = TRIPTYCH_IMAGES[transition["first"]]
        last_path = TRIPTYCH_IMAGES[transition["last"]]

        result = generate_transition(
            client=client,
            first_frame_path=first_path,
            last_frame_path=last_path,
            prompt=transition["prompt"],
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_dir=out_dir,
            output_name=transition["name"],
            notes=f"Central Coast Triptych: {transition['name']}",
        )

        if result:
            generated.append(result)
        else:
            print(f"\n  Failed: {transition['name']} - stopping triptych")
            return None

    # Stitch into one continuous video
    if len(generated) == len(TRIPTYCH_TRANSITIONS):
        stitched_path = os.path.join(out_dir, f"{ts}_central-coast-journey.mp4")
        stitch_result = stitch_videos(generated, stitched_path)

        if stitch_result:
            # Save metadata for stitched video
            save_metadata(
                output_path=stitched_path,
                model=VEO_MODEL,
                prompt="Central Coast Triptych: Offshore → Inshore → Estuary",
                input_images=[TRIPTYCH_IMAGES[k] for k in ["offshore", "inshore", "estuary"]],
                config={
                    "type": "stitched_triptych",
                    "source_clips": [os.path.basename(p) for p in generated],
                    "duration_seconds": duration * len(generated),
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                },
                notes="Full Central Coast ecological journey stitched from individual transitions",
            )

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  TRIPTYCH COMPLETE")
    print(f"{'=' * 60}")
    for g in generated:
        print(f"  Clip:     {os.path.basename(g)}")
    if stitch_result:
        print(f"  Journey:  {os.path.basename(stitch_result)}")
    print()

    return generated


def _override_model(model_id):
    """Override the default Veo model."""
    global VEO_MODEL
    VEO_MODEL = model_id


def list_presets():
    """Print available presets and source images."""
    print("\n=== Animate Mode - Living Paintings ===\n")
    print("Bring any painting to life. Simple prompts, natural motion.\n")

    print(f"{'Key':<20} {'Status':<8} {'Subject'}")
    print(f"{'─'*20} {'─'*8} {'─'*40}")
    for key, info in IMAGE_CATALOG.items():
        path = resolve_painting_path(key)
        status = "OK" if path else "MISSING"
        has_prompt = "+" if key in ANIMATE_DETAILS else " "
        print(f"{key:<20} [{status}]{has_prompt}  {info['subject'][:45]}")
    print(f"\n  + = has custom animation prompt (others use generic)")

    print("\n=== Central Coast Triptych ===\n")
    print("Journey: Offshore → Inshore → Estuary")
    print("(Deep ocean toward land, BC Central Coast)\n")

    print("Source images:")
    for key, path in TRIPTYCH_IMAGES.items():
        exists = "OK" if os.path.exists(path) else "MISSING"
        print(f"  {key:<10} [{exists}]  {os.path.basename(path)}")

    print("\nTransitions:")
    for t in TRIPTYCH_TRANSITIONS:
        print(f"  {t['name']}")
        print(f"    {t['first']} → {t['last']}")
        print(f"    {t['prompt'][:100]}...")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated paintings and video transitions using Veo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --animate octopus                            # Animate one painting
  %(prog)s --animate octopus kelp-underwater salmon-stream  # Animate several
  %(prog)s --animate-all                                # Animate all 13 paintings
  %(prog)s --animate-image path/to/dream.png -p "..."   # Animate any image
  %(prog)s --animate octopus --aspect-ratio 9:16        # Portrait for reels
  %(prog)s --list-presets                                # Show all paintings
  %(prog)s --triptych                                    # Central Coast journey
  %(prog)s --first-frame img1.jpg --last-frame img2.jpg --prompt "..."
        """,
    )

    # Animate mode (single-image, no lastFrame)
    parser.add_argument("--animate", nargs="+", metavar="KEY",
                        help="Animate catalog paintings by key (see --list-presets)")
    parser.add_argument("--animate-all", action="store_true",
                        help="Animate all 13 catalog paintings")
    parser.add_argument("--animate-image", metavar="PATH",
                        help="Animate an arbitrary image file (dream image, etc.)")

    # Single transition mode
    parser.add_argument("--first-frame", metavar="PATH",
                        help="Path to the first keyframe image")
    parser.add_argument("--last-frame", metavar="PATH",
                        help="Path to the last keyframe image")
    parser.add_argument("--prompt", "-p",
                        help="Text prompt describing the transition/animation")

    # Triptych mode
    parser.add_argument("--triptych", action="store_true",
                        help="Generate the full Central Coast triptych sequence")

    # Common options
    parser.add_argument("--duration", type=int, default=8, choices=[5, 8],
                        help="Video duration in seconds (default: 8)")
    parser.add_argument("--aspect-ratio", default="16:9",
                        choices=["9:16", "16:9", "1:1"],
                        help="Aspect ratio (default: 16:9 landscape)")
    parser.add_argument("--resolution", default="720p",
                        choices=["720p", "1080p"],
                        help="Video resolution (default: 720p)")
    parser.add_argument("--output-dir", "-o",
                        help="Override output directory")
    parser.add_argument("--name", "-n",
                        help="Custom output filename (without extension)")
    parser.add_argument("--notes",
                        help="Notes to save in metadata")
    parser.add_argument("--model", "-m", default=VEO_MODEL,
                        help=f"Veo model ID (default: {VEO_MODEL})")
    parser.add_argument("--list-presets", action="store_true",
                        help="List available presets and source images")

    args = parser.parse_args()

    if args.list_presets:
        list_presets()
        return

    # Override model if specified
    if args.model != VEO_MODEL:
        _override_model(args.model)

    # Animate mode: catalog paintings
    if args.animate or args.animate_all:
        client = get_client()
        if args.animate_all:
            keys = list(IMAGE_CATALOG.keys())
        else:
            # Validate keys
            for key in args.animate:
                if key not in IMAGE_CATALOG:
                    print(f"Error: Unknown painting key '{key}'. Use --list-presets.")
                    sys.exit(1)
            keys = args.animate
        run_animate(
            client=client,
            image_keys=keys,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_dir=args.output_dir,
        )
        return

    # Animate mode: arbitrary image file
    if args.animate_image:
        if not os.path.exists(args.animate_image):
            print(f"Error: Image not found: {args.animate_image}")
            sys.exit(1)
        prompt = args.prompt or build_animate_prompt(None)
        client = get_client()
        result = generate_animation(
            client=client,
            image_path=args.animate_image,
            prompt=prompt,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_dir=args.output_dir,
            output_name=args.name,
            notes=args.notes,
        )
        if result:
            print(f"\n  Done! Video saved to: {result}")
        else:
            print(f"\n  No video generated.")
        return

    if args.triptych:
        client = get_client()
        run_triptych(
            client=client,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_dir=args.output_dir,
        )
        return

    if args.first_frame and args.last_frame and args.prompt:
        client = get_client()
        result = generate_transition(
            client=client,
            first_frame_path=args.first_frame,
            last_frame_path=args.last_frame,
            prompt=args.prompt,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_dir=args.output_dir,
            output_name=args.name,
            notes=args.notes,
        )
        if result:
            print(f"\n  Done! Video saved to: {result}")
        else:
            print(f"\n  No video generated.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
