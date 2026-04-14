#!/usr/bin/env python3
"""
Refinement 3: Best Eco Narrative Clips — Higher Quality Re-renders
==================================================================
Re-renders the 3 most interesting eco narrative clips at higher quality:
- eco_09_orca_surfacing — orca breach, dramatic motion
- eco_07_herring_school_tightening — herring ball defense, core SSD subject
- eco_02_murmuration_to_single_whale — morphological transformation

Higher quality settings:
- 35 steps (vs 30 original batch)
- ControlNet scale 0.55 (looser → more painterly)
- Temporal smoothing window=9
- 30fps output (vs 8/16fps original)

Run: nohup python3 /home/jovyan/refine/refine_03_eco_hq.py >> /home/jovyan/refine/progress.log 2>&1 &
"""

import os
import sys
import time
import datetime
import subprocess
import glob
import numpy as np
import torch
from pathlib import Path
from PIL import Image

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path("/home/jovyan/refine")
OUTPUT_DIR = BASE_DIR / "output" / "03_eco_hq"
V2V_DIR = Path("/home/jovyan/v2v_batch")

LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET_MODEL = "lllyasviel/control_v11f1p_sd15_depth"

# Best 3 clips to re-render at higher quality
CLIPS = {
    "eco_09_orca_surfacing": {
        "prompt": "brionypenn watercolor painting of orca whale surfacing from deep ocean, dorsal fin breaking water, spray and mist, Pacific Northwest, natural history illustration, soft organic tones, pen-and-ink outlines",
    },
    "eco_07_herring_school_tightening": {
        "prompt": "brionypenn watercolor painting of dense herring school tightening into defensive ball, silver flashing scales, underwater light, Pacific Northwest marine life, natural history illustration, soft organic tones",
    },
    "eco_02_murmuration_to_single_whale": {
        "prompt": "brionypenn watercolor painting of bird murmuration transforming into whale silhouette, transformation between air and water, Pacific Northwest coast, natural history illustration, soft organic tones, pen-and-ink outlines",
    },
}

NEGATIVE_PROMPT = "blurry, low quality, deformed, ugly, cartoon, anime, 3d render, photograph, text, watermark, oversaturated, neon"

# Higher quality settings
CONTROLNET_SCALE = 0.55   # Looser → more painterly
GUIDANCE_SCALE = 7.5
NUM_STEPS = 35             # Up from 25/30
STRENGTH = 0.65
SEED = 42
FPS = 30

SMOOTH_WINDOW = 9
SMOOTH_SIGMA = 2.5

DEVICE = "cuda"
DTYPE = torch.float16


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [R3-HQ] {msg}", flush=True)


def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=9, sigma=2.5):
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
        log(f"ERROR: {result.stderr[-500:]}")


def main():
    log("=" * 60)
    log("REFINEMENT 3: Best Eco Narratives — HQ Re-render")
    log("=" * 60)

    if not torch.cuda.is_available():
        log("FATAL: No GPU")
        sys.exit(1)
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log(f"GPU: {gpu} ({vram:.1f} GB)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify source frames exist
    for clip_name in CLIPS:
        src_dir = V2V_DIR / clip_name
        frames = sorted(src_dir.glob("*.png"))
        log(f"Source: {clip_name} — {len(frames)} frames")
        if len(frames) == 0:
            log(f"  WARNING: No source frames for {clip_name}")

    # ---- Load pipeline ----
    log("\nLoading pipeline...")
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )
    from controlnet_aux import ZoeDetector

    log("  Loading ZoeDetector...")
    zoe = ZoeDetector.from_pretrained("lllyasviel/Annotators")
    zoe = zoe.to(DEVICE)

    log("  Loading ControlNet depth...")
    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL, torch_dtype=DTYPE
    )

    log("  Loading SD 1.5 + ControlNet img2img...")
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet, torch_dtype=DTYPE, safety_checker=None
    ).to(DEVICE)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    log("  Loading Briony LoRA...")
    pipe.load_lora_weights(LORA_PATH)
    pipe.enable_attention_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
        log("  xformers enabled")
    except Exception:
        log("  xformers not available")
    log("Pipeline loaded.")

    # ---- Render each clip ----
    global_start = time.time()
    total_rendered = 0

    for clip_name, clip_cfg in CLIPS.items():
        log(f"\n{'='*60}")
        log(f"CLIP: {clip_name}")
        log(f"{'='*60}")

        src_dir = V2V_DIR / clip_name
        src_frames = sorted(src_dir.glob("*.png"))
        n_frames = len(src_frames)

        if n_frames == 0:
            log("  No source frames, skipping.")
            continue

        prompt = clip_cfg["prompt"]
        log(f"  Prompt: {prompt[:80]}...")
        log(f"  Frames: {n_frames}")
        log(f"  Settings: steps={NUM_STEPS}, cn_scale={CONTROLNET_SCALE}, strength={STRENGTH}")

        clip_frames_dir = OUTPUT_DIR / f"{clip_name}_hq_frames"
        clip_smooth_dir = OUTPUT_DIR / f"{clip_name}_hq_smoothed"
        clip_frames_dir.mkdir(parents=True, exist_ok=True)
        clip_smooth_dir.mkdir(parents=True, exist_ok=True)

        rendered_frames = []
        timings = []
        clip_start = time.time()

        for frame_idx, frame_path in enumerate(src_frames):
            out_path = clip_frames_dir / f"frame_{frame_idx+1:05d}.png"

            # Resume support
            if out_path.exists():
                rendered_frames.append(np.array(Image.open(out_path).convert("RGB")))
                if frame_idx % 20 == 0:
                    log(f"  Frame {frame_idx+1}/{n_frames} — skipped (exists)")
                continue

            start = time.perf_counter()

            # Load source frame
            src_img = Image.open(frame_path).convert("RGB").resize((512, 512))

            # Extract depth
            depth_map = zoe(src_img)

            # Render with HQ settings
            gen = torch.Generator(device="cpu").manual_seed(SEED)
            result = pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                image=src_img,
                control_image=depth_map,
                num_inference_steps=NUM_STEPS,
                guidance_scale=GUIDANCE_SCALE,
                strength=STRENGTH,
                controlnet_conditioning_scale=CONTROLNET_SCALE,
                generator=gen,
            ).images[0]

            result.save(out_path)
            rendered_frames.append(np.array(result))
            total_rendered += 1

            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            if (frame_idx + 1) % 10 == 0 or frame_idx == 0:
                avg = sum(timings) / len(timings)
                remaining = avg * (n_frames - frame_idx - 1)
                all_remaining = avg * (sum(len(sorted((V2V_DIR / cn).glob("*.png"))) for cn in CLIPS if cn > clip_name) + n_frames - frame_idx - 1)
                log(f"  Frame {frame_idx+1}/{n_frames} — {elapsed:.2f}s (avg {avg:.2f}s, clip ETA {remaining/60:.1f}min)")

        clip_time = time.time() - clip_start
        if timings:
            log(f"  Clip done: {len(timings)} frames in {clip_time/60:.1f}min")

        # Temporal smoothing
        log(f"  Temporal smoothing (window={SMOOTH_WINDOW})...")
        frames_np = np.array(rendered_frames)
        smoothed = temporal_smooth(frames_np, SMOOTH_WINDOW, SMOOTH_SIGMA)
        for i, frame in enumerate(smoothed):
            Image.fromarray(frame).save(clip_smooth_dir / f"frame_{i+1:05d}.png")
        log("  Smoothing done.")

        # Video assembly at 30fps
        video_path = OUTPUT_DIR / f"{clip_name}_hq_30fps.mp4"
        frames_to_video(clip_smooth_dir, video_path, FPS)

        # Also 16fps for comparison
        video_16 = OUTPUT_DIR / f"{clip_name}_hq_16fps.mp4"
        frames_to_video(clip_smooth_dir, video_16, 16)

    total_time = time.time() - global_start
    log("\n" + "=" * 60)
    log("REFINEMENT 3 COMPLETE")
    log(f"Total frames rendered: {total_rendered}")
    log(f"Total time: {total_time/60:.1f} min")
    log(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")
    log("=" * 60)


if __name__ == "__main__":
    main()
