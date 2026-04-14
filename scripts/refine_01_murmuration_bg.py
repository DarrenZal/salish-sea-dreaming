#!/usr/bin/env python3
"""
Refinement 1: School→Murmuration with Background Anchoring
===========================================================
Fixes the background jumping between frames by:
1. Generating a fixed background image (SD 1.5 + LoRA)
2. Using it as img2img base for every frame
3. ControlNet depth overlays the murmuration/school structure
4. Prompt progression: herring (0-45) → seabirds (45-90)
5. Higher ControlNet scale (0.75)
6. Wider temporal smoothing (window=9)
7. 30fps output

Run: nohup python3 /home/jovyan/refine/refine_01_murmuration_bg.py >> /home/jovyan/refine/progress.log 2>&1 &
"""

import os
import sys
import time
import datetime
import subprocess
import numpy as np
import torch
from pathlib import Path
from PIL import Image, ImageFilter

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path("/home/jovyan/refine")
OUTPUT_DIR = BASE_DIR / "output" / "01_murmuration_bg_anchor"
FRAMES_DIR = OUTPUT_DIR / "frames"
SMOOTH_DIR = OUTPUT_DIR / "smoothed"

DEPTH_DIR = Path("/home/jovyan/blender_render/input/school_to_murmuration_depth")
LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET_MODEL = "lllyasviel/control_v11f1p_sd15_depth"

BG_PROMPT = "brionypenn watercolor painting of Pacific Northwest coastal landscape, ocean and sky, grey overcast, soft muted tones, atmospheric perspective"
NEGATIVE_PROMPT = "blurry, low quality, photographic, 3d render, digital art, neon, oversaturated, text, watermark"

# Prompt progression
PROMPT_UNDERWATER = "brionypenn watercolor of silver herring school swimming underwater, deep ocean blue, shimmering scales, natural history illustration"
PROMPT_SKY = "brionypenn watercolor of dark seabirds in murmuration against grey sky, Pacific Northwest coastline, atmospheric, pen-and-ink outlines"

CONTROLNET_SCALE = 0.75  # Higher than original 0.65
GUIDANCE_SCALE = 7.5
NUM_STEPS = 30
SEED = 42
FPS = 30
IMG2IMG_STRENGTH = 0.55  # How much to transform the background

SMOOTH_WINDOW = 9   # Wider than original 7
SMOOTH_SIGMA = 2.5

DEVICE = "cuda"
DTYPE = torch.float16


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [R1-MURMURATION] {msg}", flush=True)


def preprocess_depth(path):
    """Load 16-bit depth and normalize to 3-channel RGB."""
    img = Image.open(path)
    arr = np.array(img, dtype=np.float32)
    if arr.max() > 255:
        arr = (arr / arr.max() * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    return Image.fromarray(np.stack([arr, arr, arr], axis=-1)).resize((512, 512))


def get_prompt_for_frame(frame_idx, total_frames):
    """Smooth prompt interpolation from underwater herring to sky murmuration."""
    midpoint = total_frames // 2
    if frame_idx <= midpoint:
        return PROMPT_UNDERWATER
    else:
        # After midpoint, blend prompt toward sky
        # We use the midpoint prompt for first half, sky for second half
        # SD doesn't support actual prompt blending, so we transition abruptly at midpoint
        # but the background anchoring + controlnet provides visual continuity
        progress = (frame_idx - midpoint) / (total_frames - midpoint)
        if progress < 0.3:
            return PROMPT_UNDERWATER  # Hold underwater a bit past midpoint
        elif progress < 0.5:
            return f"brionypenn watercolor of silver fish rising toward surface, light filtering from above, transition between water and sky"
        else:
            return PROMPT_SKY


def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=9, sigma=2.5):
    """Temporal gaussian smoothing."""
    if len(frames_np) < window:
        return frames_np
    kernel = gaussian_kernel(window, sigma)
    half_w = window // 2
    smoothed = np.copy(frames_np).astype(np.float32)

    for i in range(len(frames_np)):
        start = max(0, i - half_w)
        end = min(len(frames_np), i + half_w + 1)
        k_start = half_w - (i - start)
        k_end = k_start + (end - start)
        k = kernel[k_start:k_end]
        k = k / k.sum()

        weighted = np.zeros_like(frames_np[0], dtype=np.float32)
        for j, ki in zip(range(start, end), k):
            weighted += frames_np[j].astype(np.float32) * ki
        smoothed[i] = np.clip(weighted, 0, 255)

    return smoothed.astype(np.uint8)


def frames_to_video(frames_dir, output_path, fps=30):
    """Assemble frames into MP4."""
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    frames = sorted(Path(frames_dir).glob("frame_*.png"))
    filelist = frames_dir / "_filelist.txt"
    with open(filelist, 'w') as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")

    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-r", str(fps),
        "-i", str(filelist),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    filelist.unlink(missing_ok=True)

    if result.returncode == 0:
        size_mb = Path(output_path).stat().st_size / 1e6
        log(f"Video: {output_path} ({size_mb:.1f} MB)")
    else:
        log(f"ERROR encoding video: {result.stderr[-500:]}")


def main():
    log("=" * 60)
    log("REFINEMENT 1: School→Murmuration with Background Anchoring")
    log("=" * 60)

    # GPU check
    if not torch.cuda.is_available():
        log("FATAL: No GPU")
        sys.exit(1)
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log(f"GPU: {gpu} ({vram:.1f} GB)")

    # Verify depth maps
    depth_files = sorted(DEPTH_DIR.glob("frame_*.png"))
    log(f"Depth maps: {len(depth_files)}")
    if len(depth_files) == 0:
        log("FATAL: No depth maps found!")
        sys.exit(1)

    # Create dirs
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    SMOOTH_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Load pipelines ----
    log("Loading pipelines...")
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        StableDiffusionPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    # Text-to-image pipeline for background generation
    log("  Loading SD 1.5 txt2img for background...")
    bg_pipe = StableDiffusionPipeline.from_pretrained(
        BASE_MODEL, torch_dtype=DTYPE, safety_checker=None
    ).to(DEVICE)
    bg_pipe.scheduler = UniPCMultistepScheduler.from_config(bg_pipe.scheduler.config)
    bg_pipe.load_lora_weights(LORA_PATH)
    bg_pipe.enable_attention_slicing()

    # Generate the fixed background
    log("  Generating fixed background image...")
    gen = torch.Generator(DEVICE).manual_seed(SEED)
    bg_image = bg_pipe(
        prompt=BG_PROMPT,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=40,
        guidance_scale=7.5,
        generator=gen,
        width=512,
        height=512,
    ).images[0]
    bg_path = OUTPUT_DIR / "background.png"
    bg_image.save(bg_path)
    log(f"  Background saved: {bg_path}")

    # Free txt2img pipeline
    del bg_pipe
    torch.cuda.empty_cache()

    # ControlNet img2img pipeline
    log("  Loading ControlNet depth model...")
    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL, torch_dtype=DTYPE
    )

    log("  Loading SD 1.5 + ControlNet img2img pipeline...")
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet, torch_dtype=DTYPE, safety_checker=None
    ).to(DEVICE)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LORA_PATH)
    pipe.enable_attention_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
        log("  xformers enabled")
    except Exception:
        log("  xformers not available")

    log("Pipeline loaded.")

    # ---- Render frames ----
    n_frames = len(depth_files)
    log(f"\nRendering {n_frames} frames with background anchoring...")
    timings = []
    rendered_frames = []

    for i, depth_path in enumerate(depth_files):
        # Check resume
        out_path = FRAMES_DIR / f"frame_{i:05d}.png"
        if out_path.exists():
            img = Image.open(out_path)
            rendered_frames.append(np.array(img))
            if i % 15 == 0:
                log(f"  Frame {i+1}/{n_frames} — skipped (exists)")
            continue

        start = time.perf_counter()

        # Load depth map
        depth_image = preprocess_depth(depth_path)

        # Get prompt for this frame
        prompt = get_prompt_for_frame(i, n_frames)

        # Use background as img2img base
        gen = torch.Generator(DEVICE).manual_seed(SEED)
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=bg_image,              # Fixed background as base
            control_image=depth_image,   # Depth map drives structure
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            strength=IMG2IMG_STRENGTH,
            controlnet_conditioning_scale=CONTROLNET_SCALE,
            generator=gen,
        ).images[0]

        result.save(out_path)
        rendered_frames.append(np.array(result))

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        if i % 10 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            log(f"  Frame {i+1}/{n_frames} — {elapsed:.2f}s (avg {avg:.2f}s, ETA {remaining/60:.1f}min)")
            log(f"    Prompt: {prompt[:80]}...")

    total_render = sum(timings)
    if timings:
        log(f"Rendering done: {len(timings)} frames in {total_render/60:.1f}min (avg {total_render/len(timings):.2f}s/frame)")

    # ---- Temporal smoothing ----
    log(f"\nTemporal smoothing (window={SMOOTH_WINDOW}, sigma={SMOOTH_SIGMA})...")
    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=SMOOTH_WINDOW, sigma=SMOOTH_SIGMA)

    for i, frame in enumerate(smoothed):
        Image.fromarray(frame).save(SMOOTH_DIR / f"frame_{i:05d}.png")
    log("Smoothing done.")

    # ---- Video assembly ----
    log("\nAssembling video at 30fps...")
    video_path = OUTPUT_DIR / "school_to_murmuration_bg_anchor_30fps.mp4"
    frames_to_video(SMOOTH_DIR, video_path, FPS)

    # Also make 16fps version for comparison
    video_16 = OUTPUT_DIR / "school_to_murmuration_bg_anchor_16fps.mp4"
    frames_to_video(SMOOTH_DIR, video_16, 16)

    log("\n" + "=" * 60)
    log("REFINEMENT 1 COMPLETE")
    log(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")
    log(f"  background.png")
    log("=" * 60)


if __name__ == "__main__":
    main()
