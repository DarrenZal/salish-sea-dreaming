#!/usr/bin/env python3
"""
wan_morphs.py — Wan 2.1 I2V metamorphosis sequences for Salish Sea Dreaming.

Upload to TELUS and run:
    python /home/jovyan/wan_morphs.py

Produces pairs of 10s and 20s videos for each transformation.
Results saved to /home/jovyan/wan_output/morphs/

Model: Wan-AI/Wan2.1-I2V-14B-480P-Diffusers
Technique: Image-to-Video — start from a reference image, prompt drives the metamorphosis.
"""

import gc
import logging
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

# Install deps on TELUS JupyterHub
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "diffusers>=0.32.0", "transformers", "accelerate", "safetensors",
    "imageio", "imageio-ffmpeg", "Pillow",
])

import torch
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/jovyan/wan_morphs.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("wan_morphs")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("/home/jovyan/wan_output/morphs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Resolution — Wan 480P native sizes (must be divisible by 16)
W, H = 480, 480          # square works well for both fish/birds

NUM_FRAMES_SHORT = 81    # 81 frames @ 8fps = ~10s
NUM_FRAMES_LONG  = 161   # 161 frames @ 8fps = ~20s

INFERENCE_STEPS = 30
GUIDANCE_SCALE  = 5.0
SEEDS = [42, 123, 256]   # 3 dream paths per transformation

NEG_PROMPT = "blurry, distorted, low quality, deformed, static, frozen, pixelated"

# ---------------------------------------------------------------------------
# Start images — Briony's paintings already on TELUS + one murmuration download
# ---------------------------------------------------------------------------
# The dreamy quality of the existing videos came from starting with Briony's
# watercolor paintings. We reuse them here. The murmuration image is downloaded
# from Wikimedia Commons (CC-BY-SA 2.0) on first run.

PAINTINGS = "/home/jovyan/output/inputs"
MURM_PATH = "/home/jovyan/start_images/murmuration.jpg"
MURM_URL  = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/"
    "Murmuration_of_starlings_in_October_2014.jpg/"
    "1280px-Murmuration_of_starlings_in_October_2014.jpg"
)

START_IMAGES = {
    "herring_school": f"{PAINTINGS}/inshore.jpg",    # Briony inshore — fish, coast
    "murmuration":    MURM_PATH,                     # starling murmuration (downloaded)
    "orca":           f"{PAINTINGS}/offshore.jpg",   # Briony offshore — deep water
    "whale_pod":      f"{PAINTINGS}/offshore.jpg",
    "salmon_run":     f"{PAINTINGS}/estuary.jpg",    # Briony estuary — salmon country
    "kelp_forest":    f"{PAINTINGS}/inshore.jpg",
    "single_fish":    f"{PAINTINGS}/moonfish_frame.png",  # actual Moonfish footage frame
}

# ---------------------------------------------------------------------------
# Transformation sequences
# Each entry: (start_image_key, output_name, prompt)
# ---------------------------------------------------------------------------

MORPHS = [
    # ── Fish school → Murmuration ─────────────────────────────────────────
    (
        "herring_school",
        "fish_school_to_murmuration",
        "A vast silver school of herring flowing through blue ocean water slowly rises toward the surface, "
        "the fish leaping into the air, their silver bodies catching light as they transform into starlings, "
        "the school seamlessly becoming a murmuration that sweeps and billows across the grey sky above the Salish Sea, "
        "continuous organic metamorphosis, dreamlike, cinematic, slow motion",
    ),
    # ── Murmuration → Fish school ─────────────────────────────────────────
    (
        "murmuration",
        "murmuration_to_fish_school",
        "A murmuration of starlings billowing and sweeping across the sky above the ocean slowly descends, "
        "the birds folding into the water's surface, transforming into a vast silver school of herring "
        "that pulses and wheels through the blue depths of the Salish Sea, "
        "continuous organic metamorphosis, dreamlike, cinematic, underwater",
    ),
    # ── Murmuration → Single whale ────────────────────────────────────────
    (
        "murmuration",
        "murmuration_to_whale",
        "Thousands of birds in a murmuration above the ocean coalesce and condense, "
        "spiraling downward into the water, the flock compressing into a single massive form — "
        "a humpback whale that breaches through the surface in slow motion, "
        "dreamlike metamorphosis, Pacific Northwest ocean, cinematic, slow motion",
    ),
    # ── Whale → Fish school ───────────────────────────────────────────────
    (
        "orca",
        "orca_to_fish_school",
        "A lone orca glides through the dark deep water, its body beginning to fragment and multiply, "
        "dissolving into hundreds then thousands of smaller silver fish that expand outward "
        "into a vast wheeling school of herring filling the ocean, "
        "continuous organic metamorphosis, dreamlike, Pacific Northwest, underwater, cinematic",
    ),
    # ── Fish school → Whale ───────────────────────────────────────────────
    (
        "herring_school",
        "herring_school_to_whale",
        "A vast school of silver herring flows and contracts, the fish spinning into a vortex "
        "that condenses and solidifies into a single enormous humpback whale "
        "that slowly rolls through the blue water of the Salish Sea, exhaling mist, "
        "dreamlike metamorphosis, cinematic, underwater, slow motion",
    ),
    # ── Salmon run → Murmuration ──────────────────────────────────────────
    (
        "salmon_run",
        "salmon_to_murmuration",
        "Thousands of red sockeye salmon surging upstream in a river suddenly lift into the air "
        "as if flying, their silver-red bodies becoming birds that rise in a massive murmuration "
        "sweeping across the sky above the forest, continuous organic metamorphosis, "
        "Salish Sea watershed, dreamlike, cinematic",
    ),
    # ── Kelp forest → Murmuration ─────────────────────────────────────────
    (
        "kelp_forest",
        "kelp_to_murmuration",
        "A kelp forest swaying in deep green light, the kelp fronds detaching and rising, "
        "each frond becoming a bird as they ascend through the water and burst through the surface, "
        "forming a murmuration that wheels above the Salish Sea, "
        "continuous organic metamorphosis, dreamlike, cinematic",
    ),
    # ── Orca pod → Fish school → Murmuration (chain) ──────────────────────
    (
        "whale_pod",
        "whale_pod_to_school_to_birds",
        "A pod of orcas swimming together begins to fragment, each whale dissolving into dozens of salmon, "
        "the salmon schooling and accelerating upward, leaping from the ocean in a cascade that becomes "
        "a vast murmuration of seabirds wheeling above the Salish Sea, "
        "three-stage organic metamorphosis, dreamlike, cinematic, Pacific Northwest",
    ),
]

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def save_video(frames, path, fps=8):
    """Save list of PIL images as mp4 using imageio."""
    import imageio
    writer = imageio.get_writer(str(path), fps=fps, codec="libx264",
                                 quality=8, pixelformat="yuv420p")
    for frame in frames:
        writer.append_data(frame if isinstance(frame, __import__('numpy').ndarray)
                          else __import__('numpy').array(frame))
    writer.close()
    size_mb = Path(path).stat().st_size / 1e6
    log.info(f"  Saved: {path.name} ({size_mb:.1f} MB, {len(frames)} frames @ {fps}fps)")


def _ensure_murmuration():
    """Download the murmuration start image if not present."""
    p = Path(MURM_PATH)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"  Downloading murmuration image from Wikimedia Commons...")
    try:
        req = urllib.request.Request(MURM_URL, headers={"User-Agent": "WanMorphs/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            p.write_bytes(resp.read())
        log.info(f"  Murmuration saved: {p} ({p.stat().st_size/1e6:.1f} MB)")
    except Exception as e:
        log.warning(f"  Murmuration download failed ({e}) — using dark sky placeholder")
        img = Image.new("RGB", (W, H), (30, 35, 50))
        img.save(str(p))


def load_start_image(key):
    """Load and resize start image to W x H."""
    if key == "murmuration":
        _ensure_murmuration()
    path = START_IMAGES[key]
    if not os.path.exists(path):
        log.warning(f"  Start image not found: {path}")
        log.warning("  Creating placeholder — replace with real photo for best results")
        img = Image.new("RGB", (W, H), (30, 50, 80))  # dark ocean blue
    else:
        img = Image.open(path).convert("RGB")
    # Center-crop to target aspect ratio then resize
    target_ratio = W / H
    img_ratio = img.width / img.height
    if img_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=" * 70)
    log.info("WAN MORPHS — Salish Sea metamorphosis sequences")
    log.info(f"Output: {OUTPUT_DIR}")
    log.info(f"Short: {NUM_FRAMES_SHORT} frames @ 8fps = {NUM_FRAMES_SHORT/8:.0f}s")
    log.info(f"Long:  {NUM_FRAMES_LONG} frames @ 8fps = {NUM_FRAMES_LONG/8:.0f}s")
    log.info("=" * 70)

    # Load pipeline once — it's 14B params, takes ~3 min to load
    log.info("Loading Wan I2V 14B pipeline...")
    t0 = time.time()
    from diffusers import WanImageToVideoPipeline

    pipe = WanImageToVideoPipeline.from_pretrained(
        "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers",
        torch_dtype=torch.float16,
    )
    pipe.to("cuda")
    pipe.enable_model_cpu_offload()
    log.info(f"Pipeline loaded in {time.time()-t0:.0f}s")

    total_generated = 0
    total_failed = 0

    for start_key, out_name, prompt in MORPHS:
        log.info(f"\n{'='*60}")
        log.info(f"MORPH: {out_name}")
        log.info(f"Start: {start_key}")
        log.info(f"Prompt: {prompt[:100]}...")
        log.info(f"{'='*60}")

        img = load_start_image(start_key)

        for seed in SEEDS:
            for num_frames, label in [(NUM_FRAMES_SHORT, "10s"), (NUM_FRAMES_LONG, "20s")]:
                tag = f"{out_name}_s{seed}_{label}"
                out_path = OUTPUT_DIR / f"{tag}.mp4"

                if out_path.exists():
                    log.info(f"  SKIP (exists): {tag}")
                    continue

                log.info(f"\n  Generating: {tag}")
                t0 = time.time()
                try:
                    gen = torch.Generator("cuda").manual_seed(seed)
                    output = pipe(
                        image=img,
                        prompt=prompt,
                        negative_prompt=NEG_PROMPT,
                        height=H,
                        width=W,
                        num_frames=num_frames,
                        num_inference_steps=INFERENCE_STEPS,
                        guidance_scale=GUIDANCE_SCALE,
                        generator=gen,
                    )
                    frames = output.frames[0]
                    elapsed = time.time() - t0
                    log.info(f"  Generated {len(frames)} frames in {elapsed:.0f}s ({elapsed/len(frames):.1f}s/frame)")

                    save_video(frames, out_path, fps=8)
                    # Also save at 16fps for smoother playback
                    save_video(frames, OUTPUT_DIR / f"{tag}_16fps.mp4", fps=16)

                    # Save first and last frames as reference
                    frames[0].save(OUTPUT_DIR / f"{tag}_frame0.png")
                    frames[-1].save(OUTPUT_DIR / f"{tag}_frameN.png")

                    total_generated += 1
                    del output, frames
                    gc.collect()
                    torch.cuda.empty_cache()

                except Exception as e:
                    log.error(f"  FAILED {tag}: {e}")
                    traceback.print_exc()
                    total_failed += 1
                    gc.collect()
                    torch.cuda.empty_cache()

    log.info("\n" + "=" * 70)
    log.info(f"DONE — {total_generated} generated, {total_failed} failed")
    log.info(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log.info(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
