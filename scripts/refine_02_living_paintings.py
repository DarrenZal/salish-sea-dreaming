#!/usr/bin/env python3
"""
Refinement 2: Living Paintings — Briony's Art Gently Breathing
==============================================================
Downloads Briony's Central Coast paintings from Node 1,
then generates 300 frames (10s @ 30fps) per painting where
each frame uses the PREVIOUS frame as input, anchored by
blending 90% previous + 10% original to prevent drift.

The result: the painting gently "breathing" — creatures shift,
water ripples, kelp sways. Very low img2img strength (0.08-0.12).

Run: nohup python3 /home/jovyan/refine/refine_02_living_paintings.py >> /home/jovyan/refine/progress.log 2>&1 &
"""

import os
import sys
import time
import datetime
import subprocess
import requests
import numpy as np
import torch
from pathlib import Path
from PIL import Image

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path("/home/jovyan/refine")
OUTPUT_DIR = BASE_DIR / "output" / "02_living_paintings"
INPUT_DIR = BASE_DIR / "input" / "briony_paintings"

LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"

# Node 1 Jupyter API for downloading paintings
NODE1_BASE = "https://model-deployment-0b50s.paas.ai.telus.com"
NODE1_TOKEN = "8f6ceea09691892cf2d19dc7466669ea"

PAINTINGS = {
    "estuary": {
        "filename": "briony_estuary.jpg",
        "prompt": "brionypenn watercolor of a Pacific Northwest river estuary coming alive, water rippling gently, salmon fry swimming, reeds swaying in breeze, soft morning light, natural history illustration",
        "node1_path": "ComfyUI/input/briony_estuary.jpg",
    },
    "inshore": {
        "filename": "briony_inshore.jpg",
        "prompt": "brionypenn watercolor of Pacific Northwest inshore waters, kelp gently swaying, herring school drifting, light filtering through water, subtle current movement, natural history illustration",
        "node1_path": "ComfyUI/input/briony_inshore.jpg",
    },
}

# We don't have "offshore" confirmed on Node 1, but check for it
# If it exists, add it dynamically

NEGATIVE_PROMPT = "blurry, low quality, deformed, ugly, cartoon, anime, 3d render, text, watermark, dramatic change, harsh, neon"

IMG2IMG_STRENGTH = 0.10       # Very low — just gentle motion
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25
SEED = 42
ANCHOR_BLEND = 0.10          # 10% original, 90% previous
N_FRAMES = 300               # 10 seconds at 30fps
FPS = 30

SMOOTH_WINDOW = 9
SMOOTH_SIGMA = 2.0

DEVICE = "cuda"
DTYPE = torch.float16


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [R2-LIVING] {msg}", flush=True)


def download_from_node1(node1_path, local_path):
    """Download a file from Node 1 via Jupyter API."""
    url = f"{NODE1_BASE}/api/contents/{node1_path}"
    headers = {"Authorization": f"Token {NODE1_TOKEN}"}

    log(f"  Downloading {node1_path} from Node 1...")
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    if data.get("format") == "base64":
        import base64
        content = base64.b64decode(data["content"])
        with open(local_path, "wb") as f:
            f.write(content)
        log(f"  Saved: {local_path} ({len(content)/1024:.0f} KB)")
    else:
        # Try content endpoint
        url2 = f"{NODE1_BASE}/files/{node1_path}?token={NODE1_TOKEN}"
        resp2 = requests.get(url2)
        resp2.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp2.content)
        log(f"  Saved: {local_path} ({len(resp2.content)/1024:.0f} KB)")


def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=9, sigma=2.0):
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
        log(f"ERROR encoding: {result.stderr[-500:]}")


def main():
    log("=" * 60)
    log("REFINEMENT 2: Living Paintings — Briony's Art Breathing")
    log("=" * 60)

    if not torch.cuda.is_available():
        log("FATAL: No GPU")
        sys.exit(1)
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log(f"GPU: {gpu} ({vram:.1f} GB)")

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Download paintings from Node 1 ----
    log("\nDownloading Briony's paintings from Node 1...")
    available_paintings = {}
    for name, cfg in PAINTINGS.items():
        local_path = INPUT_DIR / cfg["filename"]
        if local_path.exists():
            log(f"  {name}: already exists ({local_path})")
            available_paintings[name] = cfg
        else:
            try:
                download_from_node1(cfg["node1_path"], local_path)
                available_paintings[name] = cfg
            except Exception as e:
                log(f"  WARNING: Could not download {name}: {e}")

    if not available_paintings:
        log("FATAL: No paintings available!")
        sys.exit(1)

    log(f"Paintings available: {list(available_paintings.keys())}")

    # ---- Load pipeline ----
    log("\nLoading SD 1.5 img2img pipeline...")
    from diffusers import StableDiffusionImg2ImgPipeline, UniPCMultistepScheduler

    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        BASE_MODEL, torch_dtype=DTYPE, safety_checker=None
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

    # ---- Process each painting ----
    global_start = time.time()

    for painting_name, cfg in available_paintings.items():
        log(f"\n{'='*60}")
        log(f"PAINTING: {painting_name}")
        log(f"{'='*60}")

        # Load original painting
        original_path = INPUT_DIR / cfg["filename"]
        original = Image.open(original_path).convert("RGB").resize((512, 512))
        original_np = np.array(original, dtype=np.float32)

        prompt = cfg["prompt"]
        log(f"Prompt: {prompt[:80]}...")

        # Create output dirs
        p_frames_dir = OUTPUT_DIR / f"{painting_name}_frames"
        p_smooth_dir = OUTPUT_DIR / f"{painting_name}_smoothed"
        p_frames_dir.mkdir(parents=True, exist_ok=True)
        p_smooth_dir.mkdir(parents=True, exist_ok=True)

        # Check resume
        existing_frames = sorted(p_frames_dir.glob("frame_*.png"))
        start_frame = len(existing_frames)
        if start_frame > 0:
            log(f"  Resuming from frame {start_frame} (found {start_frame} existing)")
            # Load last frame as current
            current = Image.open(existing_frames[-1]).convert("RGB")
        else:
            current = original.copy()

        rendered_frames = []
        # Load existing frames for smoothing later
        for ef in existing_frames:
            rendered_frames.append(np.array(Image.open(ef).convert("RGB")))

        timings = []
        painting_start = time.time()

        # Vary strength slightly over time for organic feel
        # Subtle sinusoidal variation: 0.08-0.12
        import math

        for i in range(start_frame, N_FRAMES):
            start = time.perf_counter()

            # Slight strength variation for organic breathing feel
            phase = math.sin(2 * math.pi * i / 60) * 0.02  # oscillate over ~2s at 30fps
            strength = IMG2IMG_STRENGTH + phase  # 0.08 to 0.12

            gen = torch.Generator(DEVICE).manual_seed(SEED + i)  # Vary seed slightly per frame

            result = pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                image=current,
                strength=max(0.05, min(0.15, strength)),
                num_inference_steps=NUM_STEPS,
                guidance_scale=GUIDANCE_SCALE,
                generator=gen,
            ).images[0]

            # Anchor: blend 90% result + 10% original to prevent drift
            result_np = np.array(result, dtype=np.float32)
            anchored_np = (1 - ANCHOR_BLEND) * result_np + ANCHOR_BLEND * original_np
            anchored_np = np.clip(anchored_np, 0, 255).astype(np.uint8)
            anchored = Image.fromarray(anchored_np)

            # Save frame
            out_path = p_frames_dir / f"frame_{i:05d}.png"
            anchored.save(out_path)
            rendered_frames.append(anchored_np)

            # Next frame uses this as input
            current = anchored

            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            if i % 30 == 0 or i == N_FRAMES - 1:
                avg = sum(timings) / len(timings)
                remaining = avg * (N_FRAMES - i - 1)
                log(f"  Frame {i+1}/{N_FRAMES} — {elapsed:.2f}s (avg {avg:.2f}s, ETA {remaining/60:.1f}min, strength={strength:.3f})")

        p_time = time.time() - painting_start
        if timings:
            log(f"  Rendering done: {len(timings)} frames in {p_time/60:.1f}min")

        # Temporal smoothing
        log(f"  Temporal smoothing (window={SMOOTH_WINDOW})...")
        frames_np = np.array(rendered_frames)
        smoothed = temporal_smooth(frames_np, SMOOTH_WINDOW, SMOOTH_SIGMA)
        for i, frame in enumerate(smoothed):
            Image.fromarray(frame).save(p_smooth_dir / f"frame_{i:05d}.png")
        log("  Smoothing done.")

        # Video assembly
        video_path = OUTPUT_DIR / f"living_{painting_name}_30fps.mp4"
        frames_to_video(p_smooth_dir, video_path, FPS)

        # Also 16fps
        video_16 = OUTPUT_DIR / f"living_{painting_name}_16fps.mp4"
        frames_to_video(p_smooth_dir, video_16, 16)

    total_time = time.time() - global_start
    log("\n" + "=" * 60)
    log("REFINEMENT 2 COMPLETE")
    log(f"Total time: {total_time/60:.1f} min")
    log(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")
    log("=" * 60)


if __name__ == "__main__":
    main()
