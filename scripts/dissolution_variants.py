#!/usr/bin/env python3
"""
Salish Sea Dreaming — Landscape Dissolution Variants
=====================================================

"We are the Salish Sea, dreaming itself awake."

Three experiments exploiting the "landscape dissolution" technique: rendering
depth maps from Boids/mesh simulations through ControlNet with landscape prompts.
Creature shapes dissolve into landscape elements — fish become trees, coastlines,
clouds. This is the hero technique for the Salt Spring exhibition (April 10-26).

Experiments:
  1. SALMON->FOREST "River Becoming Forest" (450 frames):
     Salmon->roots depth maps from Blender, progressive prompts:
     spawning salmon -> dissolution into current -> forest nourished by river.

  2. KELP->FOREST (90 frames from Boids school->murmuration):
     Same depth maps, completely different prompts — underwater kelp forest
     becoming land forest. Tests whether Boids motion reads differently
     with different prompts.

  3. THE DREAMING — Abstract Dissolution (uses salmon->roots depth maps):
     Loose ControlNet (0.5), high denoising (0.7). Single ethereal
     prompt throughout. Maximum painterly abstraction.

Approach:
  Uses StableDiffusionControlNetPipeline (SD 1.5 + ControlNet depth +
  Briony LoRA). Depth maps from creature simulations provide structural
  control, while landscape prompts provide the visual content. The result:
  creature shapes dissolve into landscape elements.

Source depth maps: Downloaded from Node 1 by the launcher script.
  - Salmon->roots: /home/jovyan/dissolution_variants/depth/salmon_roots/
  - School->murmuration: /home/jovyan/dissolution_variants/depth/school_murmuration/

Target: H200 GPU, SD 1.5 + Briony LoRA + ControlNet depth.
All output -> /home/jovyan/dissolution_variants/output/
Progress  -> /home/jovyan/dissolution_variants/progress.log

Author: Darren Zal + Claude
Date: 2026-04-03
"""

import os
import sys
import gc
import time
import math
import traceback
import subprocess
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT = Path("/home/jovyan/dissolution_variants")
OUTPUT_DIR = ROOT / "output"
DEPTH_SALMON = ROOT / "depth" / "salmon_roots"
DEPTH_BOIDS = ROOT / "depth" / "school_murmuration"
LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "runwayml/stable-diffusion-v1-5"
PROGRESS_LOG = ROOT / "progress.log"

SEED = 42
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25
NEGATIVE_PROMPT = (
    "photograph, photorealistic, sharp lines, digital art, 3d render, "
    "harsh shadows, blurry, deformed, ugly, text, watermark, signature, "
    "low quality, jpeg artifacts"
)

# ============================================================================
# SETUP
# ============================================================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DISSOLUTION] %(message)s",
    handlers=[
        logging.FileHandler(PROGRESS_LOG, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def install_deps():
    """Install required packages."""
    log.info("Installing dependencies...")
    packages = [
        "diffusers>=0.32.0",
        "transformers",
        "accelerate",
        "safetensors",
        "peft",
        "controlnet-aux",
        "opencv-python-headless",
        "imageio",
        "imageio-ffmpeg",
        "Pillow",
        "numpy",
        "scipy",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "--upgrade"] + packages
    )
    log.info("Dependencies installed.")


def save_video(frames_pil, path, fps=30):
    """Save list of PIL images as MP4 video."""
    import imageio
    writer = imageio.get_writer(
        str(path), fps=fps, codec="libx264",
        output_params=["-pix_fmt", "yuv420p", "-crf", "18"],
    )
    for frame in frames_pil:
        arr = np.array(frame)
        if arr.dtype in (np.float32, np.float64):
            arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        writer.append_data(arr)
    writer.close()
    log.info(f"  Saved: {path} ({len(frames_pil)} frames @ {fps}fps)")


def load_depth_sequence(depth_dir, max_frames=None):
    """Load depth maps from directory, sorted by frame number.

    Handles both frame_XXXX.png and ImageXXXX.png naming.
    Prefers frame_XXXX.png (higher resolution) if both exist.
    """
    from PIL import Image

    depth_dir = Path(depth_dir)
    if not depth_dir.exists():
        log.error(f"Depth directory not found: {depth_dir}")
        return []

    # Prefer frame_XXXX.png files (full resolution ~530KB)
    frame_files = sorted(depth_dir.glob("frame_*.png"))
    if not frame_files:
        # Fall back to ImageXXXX.png
        frame_files = sorted(depth_dir.glob("Image*.png"))

    if not frame_files:
        log.error(f"No depth maps found in {depth_dir}")
        return []

    if max_frames and len(frame_files) > max_frames:
        frame_files = frame_files[:max_frames]

    log.info(f"  Loading {len(frame_files)} depth maps from {depth_dir}")
    images = []
    for f in frame_files:
        img = Image.open(f).convert("RGB")
        # Resize to 512x512 for SD 1.5
        if img.size != (512, 512):
            img = img.resize((512, 512), Image.LANCZOS)
        images.append(img)

    return images


def temporal_smooth(frames_pil, window=9):
    """Apply temporal smoothing across a sequence of PIL images.

    Uses weighted averaging over a sliding window to reduce flicker.
    """
    if window <= 1 or len(frames_pil) <= 1:
        return frames_pil

    from PIL import Image

    log.info(f"  Applying temporal smoothing (window={window})...")
    arrays = [np.array(f, dtype=np.float32) for f in frames_pil]
    smoothed = []
    half_w = window // 2

    # Gaussian-like weights
    sigma = half_w / 2 + 0.5
    weights = np.exp(-0.5 * (np.arange(window) - half_w) ** 2 / sigma ** 2)

    for i in range(len(arrays)):
        start = max(0, i - half_w)
        end = min(len(arrays), i + half_w + 1)
        w_start = start - (i - half_w)
        w_end = w_start + (end - start)
        w = weights[w_start:w_end]
        w = w / w.sum()

        blended = np.zeros_like(arrays[i])
        for j, idx in enumerate(range(start, end)):
            blended += arrays[idx] * w[j]

        smoothed.append(Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8)))

    return smoothed


# ============================================================================
# PIPELINE LOADING — uses proven StableDiffusionControlNetPipeline
# ============================================================================

_pipeline = None


def load_pipeline():
    """Load SD 1.5 + ControlNet depth + Briony LoRA.

    Uses StableDiffusionControlNetPipeline (txt2img + ControlNet), which is
    proven to work on this node from the r3 experiments.
    Returns the pipeline.
    """
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    import torch
    from diffusers import (
        StableDiffusionControlNetPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    log.info("Loading ControlNet depth model...")
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16,
    )

    log.info("Loading SD 1.5 + ControlNet pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        BASE_MODEL,
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")

    if os.path.exists(LORA_PATH):
        pipe.load_lora_weights(LORA_PATH)
        log.info("  Briony LoRA loaded")
    else:
        log.warning(f"  LoRA not found at {LORA_PATH}")

    pipe.enable_vae_slicing()

    _pipeline = pipe
    log.info("Pipeline ready.")
    return pipe


def render_sequence(depth_frames, prompts_by_range,
                    controlnet_scale=0.75,
                    smooth_window=9, label="render"):
    """Render depth map sequence through ControlNet depth.

    The landscape dissolution technique: depth maps from creature simulations
    are rendered through ControlNet with landscape prompts. Creature shapes
    dissolve into landscape elements.

    Args:
        depth_frames: List of PIL depth map images (RGB)
        prompts_by_range: List of (start_frame, end_frame, prompt) tuples
        controlnet_scale: ControlNet conditioning scale (0.0-1.0)
        smooth_window: Temporal smoothing window size
        label: Label for logging
    Returns:
        List of rendered PIL images (temporally smoothed)
    """
    import torch

    pipe = load_pipeline()
    n_frames = len(depth_frames)
    log.info(f"  Rendering {n_frames} frames: cn_scale={controlnet_scale}, label={label}")

    rendered = []
    t0 = time.time()

    for i, depth_img in enumerate(depth_frames):
        # Determine prompt for this frame
        prompt = None
        for start, end, p in prompts_by_range:
            if start <= i < end:
                prompt = p
                break
        if prompt is None:
            prompt = prompts_by_range[-1][2]

        gen = torch.Generator("cuda").manual_seed(SEED + i)
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                image=depth_img,
                num_inference_steps=NUM_STEPS,
                guidance_scale=GUIDANCE_SCALE,
                controlnet_conditioning_scale=controlnet_scale,
                generator=gen,
            )
            rendered.append(result.images[0])
            del result
        except Exception as e:
            log.error(f"    Frame {i} failed: {e}")
            if rendered:
                rendered.append(rendered[-1].copy())
            else:
                from PIL import Image
                rendered.append(Image.new("RGB", (512, 512), (0, 0, 0)))

        if (i + 1) % 25 == 0 or i == 0:
            elapsed = time.time() - t0
            fps_rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (n_frames - i - 1) / fps_rate if fps_rate > 0 else 0
            log.info(f"    [{label}] Frame {i+1}/{n_frames} "
                     f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")

        # Periodic VRAM cleanup
        if (i + 1) % 50 == 0:
            gc.collect()
            torch.cuda.empty_cache()

    elapsed = time.time() - t0
    log.info(f"  Rendering complete: {n_frames} frames in {elapsed:.0f}s "
             f"({elapsed/n_frames:.1f}s/frame)")

    # Apply temporal smoothing
    if smooth_window > 1:
        rendered = temporal_smooth(rendered, window=smooth_window)

    return rendered


def save_keyframes(frames, outdir, prefix, indices=None):
    """Save keyframe images for quick review."""
    if indices is None:
        n = len(frames)
        indices = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    for idx in indices:
        if 0 <= idx < len(frames):
            frames[idx].save(os.path.join(outdir, f"{prefix}_kf{idx:04d}.png"))


# ============================================================================
# EXPERIMENT 1: Salmon->Roots as "River Becoming Forest" (450 frames)
# ============================================================================
def experiment_1_salmon_to_forest():
    log.info("\n" + "=" * 70)
    log.info("EXPERIMENT 1: Salmon->Forest (450 frames)")
    log.info("=" * 70)

    outdir = OUTPUT_DIR / "exp1_salmon_to_forest"
    outdir.mkdir(parents=True, exist_ok=True)

    # Load depth maps
    depth_frames = load_depth_sequence(DEPTH_SALMON, max_frames=450)
    if not depth_frames:
        log.error("No salmon->roots depth maps found. Skipping experiment 1.")
        return

    n = len(depth_frames)
    log.info(f"  Loaded {n} depth maps")

    # Progressive prompts -- three acts of dissolution
    # The depth maps provide the creature structure, the prompts provide the landscape
    third = n // 3
    prompts = [
        (0, third,
         "brionypenn watercolor of sockeye salmon swimming upstream in clear river, "
         "red and green spawning colors, river rocks below, "
         "Pacific Northwest river flowing through old growth forest"),
        (third, 2 * third,
         "brionypenn watercolor of salmon dissolving into flowing water, "
         "the fish becoming the current, nutrients flowing into the earth, "
         "mossy banks and cedar roots"),
        (2 * third, n,
         "brionypenn watercolor of tree roots spreading through dark forest floor, "
         "mushrooms growing, ferns unfurling, the forest nourished by the river, "
         "cedar and spruce"),
    ]

    rendered = render_sequence(
        depth_frames, prompts,
        controlnet_scale=0.75,
        smooth_window=9, label="salmon->forest",
    )

    # Save videos at both framerates
    save_video(rendered, str(outdir / "salmon_to_forest_30fps.mp4"), fps=30)
    save_video(rendered, str(outdir / "salmon_to_forest_16fps.mp4"), fps=16)

    # Copy final videos to main output
    import shutil
    shutil.copy2(str(outdir / "salmon_to_forest_30fps.mp4"),
                 str(OUTPUT_DIR / "salmon_to_forest_30fps.mp4"))
    shutil.copy2(str(outdir / "salmon_to_forest_16fps.mp4"),
                 str(OUTPUT_DIR / "salmon_to_forest_16fps.mp4"))

    # Save keyframes
    save_keyframes(rendered, str(outdir), "salmon_forest")

    log.info("EXPERIMENT 1 complete.")
    del depth_frames, rendered
    gc.collect()
    import torch
    torch.cuda.empty_cache()


# ============================================================================
# EXPERIMENT 2: Kelp->Forest Parallel (Boids depth maps, 90 frames)
# ============================================================================
def experiment_2_kelp_to_forest():
    log.info("\n" + "=" * 70)
    log.info("EXPERIMENT 2: Kelp->Forest (90 Boids frames)")
    log.info("=" * 70)

    outdir = OUTPUT_DIR / "exp2_kelp_to_forest"
    outdir.mkdir(parents=True, exist_ok=True)

    # Load Boids school->murmuration depth maps
    depth_frames = load_depth_sequence(DEPTH_BOIDS, max_frames=90)
    if not depth_frames:
        log.error("No Boids depth maps found. Skipping experiment 2.")
        return

    n = len(depth_frames)
    log.info(f"  Loaded {n} Boids depth maps")

    # Two-act prompt transition: kelp -> cedar
    # Boids motion reads as kelp swaying underwater, then as trees in forest
    half = n // 2
    prompts = [
        (0, half,
         "brionypenn watercolor of underwater bull kelp forest swaying in green water, "
         "fronds reaching toward light, misty Pacific Northwest coast"),
        (half, n,
         "brionypenn watercolor of old growth cedar forest, tall trunks reaching "
         "toward sky, moss and ferns below, fog and mist"),
    ]

    rendered = render_sequence(
        depth_frames, prompts,
        controlnet_scale=0.7,
        smooth_window=7, label="kelp->forest",
    )

    # Save videos
    save_video(rendered, str(outdir / "kelp_to_forest_30fps.mp4"), fps=30)
    save_video(rendered, str(outdir / "kelp_to_forest_16fps.mp4"), fps=16)

    import shutil
    shutil.copy2(str(outdir / "kelp_to_forest_30fps.mp4"),
                 str(OUTPUT_DIR / "kelp_to_forest_30fps.mp4"))
    shutil.copy2(str(outdir / "kelp_to_forest_16fps.mp4"),
                 str(OUTPUT_DIR / "kelp_to_forest_16fps.mp4"))

    save_keyframes(rendered, str(outdir), "kelp_forest")

    log.info("EXPERIMENT 2 complete.")
    del depth_frames, rendered
    gc.collect()
    import torch
    torch.cuda.empty_cache()


# ============================================================================
# EXPERIMENT 3: "The Dreaming" -- Abstract Dissolution
# ============================================================================
def experiment_3_dreaming_abstract():
    log.info("\n" + "=" * 70)
    log.info("EXPERIMENT 3: The Dreaming -- Abstract Dissolution")
    log.info("=" * 70)

    outdir = OUTPUT_DIR / "exp3_dreaming_abstract"
    outdir.mkdir(parents=True, exist_ok=True)

    # Use salmon->roots depth maps for the most frames (450),
    # but with very loose control for maximum abstraction
    depth_frames = load_depth_sequence(DEPTH_SALMON, max_frames=450)
    if not depth_frames:
        # Fall back to Boids
        log.info("  Salmon depth maps not found, falling back to Boids...")
        depth_frames = load_depth_sequence(DEPTH_BOIDS)

    if not depth_frames:
        log.error("No depth maps found for experiment 3. Skipping.")
        return

    n = len(depth_frames)
    log.info(f"  Loaded {n} depth maps for abstract rendering")

    # Single prompt throughout -- let depth maps create the motion
    # Very loose ControlNet scale = depth as suggestion only = maximum painterly
    dreaming_prompt = (
        "brionypenn watercolor painting of the Salish Sea dreaming, "
        "creatures emerging from and dissolving into water and light, "
        "natural history illustration of consciousness, "
        "the bioregion perceiving itself, twilight bioluminescent water"
    )
    prompts = [(0, n, dreaming_prompt)]

    rendered = render_sequence(
        depth_frames, prompts,
        controlnet_scale=0.5,  # Very loose -- depth as suggestion only
        smooth_window=9, label="dreaming",
    )

    # Save videos
    save_video(rendered, str(outdir / "dreaming_abstract_30fps.mp4"), fps=30)
    save_video(rendered, str(outdir / "dreaming_abstract_16fps.mp4"), fps=16)

    import shutil
    shutil.copy2(str(outdir / "dreaming_abstract_30fps.mp4"),
                 str(OUTPUT_DIR / "dreaming_abstract_30fps.mp4"))
    shutil.copy2(str(outdir / "dreaming_abstract_16fps.mp4"),
                 str(OUTPUT_DIR / "dreaming_abstract_16fps.mp4"))

    save_keyframes(rendered, str(outdir), "dreaming")

    log.info("EXPERIMENT 3 complete.")
    del depth_frames, rendered
    gc.collect()
    import torch
    torch.cuda.empty_cache()


# ============================================================================
# MAIN
# ============================================================================
def main():
    log.info("=" * 70)
    log.info("SALISH SEA DREAMING -- Landscape Dissolution Variants")
    log.info(f"Started: {datetime.now().isoformat()}")
    log.info("=" * 70)

    t_start = time.time()

    # Install deps
    install_deps()

    import torch
    log.info(f"PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log.info(f"GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        mem = getattr(props, 'total_memory', getattr(props, 'total_mem', 0)) / 1e9
        log.info(f"VRAM: {mem:.1f} GB")

    # Verify depth maps exist
    salmon_count = len(list(DEPTH_SALMON.glob("frame_*.png"))) if DEPTH_SALMON.exists() else 0
    boids_count = len(list(DEPTH_BOIDS.glob("frame_*.png"))) if DEPTH_BOIDS.exists() else 0
    log.info(f"Depth maps: salmon_roots={salmon_count}, school_murmuration={boids_count}")

    if salmon_count == 0 and boids_count == 0:
        log.error("NO DEPTH MAPS FOUND. Run the launcher to download first.")
        sys.exit(1)

    # Load pipeline once (cached globally)
    pipe = load_pipeline()

    # Run experiments
    experiments = [
        ("Exp 1: Salmon->Forest", experiment_1_salmon_to_forest),
        ("Exp 2: Kelp->Forest", experiment_2_kelp_to_forest),
        ("Exp 3: The Dreaming", experiment_3_dreaming_abstract),
    ]

    results = {}
    for name, func in experiments:
        try:
            log.info(f"\n{'='*70}")
            log.info(f"STARTING: {name}")
            log.info(f"{'='*70}")
            t_exp = time.time()
            func()
            elapsed = time.time() - t_exp
            results[name] = f"OK ({elapsed:.0f}s)"
            log.info(f"{name} completed in {elapsed:.0f}s")
        except Exception as e:
            log.error(f"{name} FAILED: {e}")
            traceback.print_exc()
            results[name] = f"FAILED: {e}"
        gc.collect()
        torch.cuda.empty_cache()

    # Summary
    total_elapsed = time.time() - t_start
    log.info("\n" + "=" * 70)
    log.info("DISSOLUTION VARIANTS -- FINAL SUMMARY")
    log.info(f"Total runtime: {total_elapsed:.0f}s ({total_elapsed/3600:.1f}h)")
    log.info("=" * 70)
    for name, status in results.items():
        log.info(f"  {name}: {status}")

    # List output files
    log.info("\nOutput files:")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        size_mb = f.stat().st_size / 1e6
        log.info(f"  {f.name} ({size_mb:.1f} MB)")

    log.info(f"\nFinished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
