#!/usr/bin/env python3
"""
Dissolution v2 — Landscape Dissolution Pipeline (Node 2)
=========================================================
Renders Boids v2 depth maps through ControlNet depth + Briony LoRA img2img.

Pipeline:
  1. Transfer 900 depth frames from Node 1 boids_v2/depth/
  2. Generate fixed background (SD 1.5 + Briony LoRA)
  3. Render 900 frames: img2img background + ControlNet depth + 6-phase prompts
  4. Temporal smoothing + video assembly (30fps + 16fps)

Output: /home/jovyan/dissolution_v2/output/

Run:
  nohup python3 /home/jovyan/dissolution_v2/dissolution_v2_render.py \
    >> /home/jovyan/dissolution_v2/progress.log 2>&1 &
"""

import os
import sys
import time
import datetime
import subprocess
import traceback
import numpy as np
import torch
from pathlib import Path
from PIL import Image
import requests
import base64

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path("/home/jovyan/dissolution_v2")
DEPTH_DIR = BASE_DIR / "depth"
OUTPUT_DIR = BASE_DIR / "output"
FRAMES_DIR = OUTPUT_DIR / "frames_main"
SMOOTH_DIR = OUTPUT_DIR / "smoothed_main"

LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET_MODEL = "lllyasviel/control_v11f1p_sd15_depth"

# Node 1 for depth map download
NODE1_URL = "https://model-deployment-0b50s.paas.ai.telus.com"
NODE1_TOKEN = "8f6ceea09691892cf2d19dc7466669ea"
NODE1_DEPTH_PATH = "boids_v2/depth"

# Background generation
BG_PROMPT = (
    "brionypenn watercolor of Pacific Northwest coast, "
    "ocean below meeting grey sky above, cedar trees along shoreline, "
    "the waterline dividing two worlds, soft atmospheric muted tones"
)
NEGATIVE_PROMPT = (
    "blurry, low quality, photographic, 3d render, digital art, neon, "
    "oversaturated, text, watermark"
)

# 6-phase prompt progression (each phase = 150 frames)
PHASE_PROMPTS = {
    0: (
        "brionypenn watercolor of silver herring gathering in cold dark water "
        "below the surface"
    ),
    150: (
        "brionypenn watercolor of fish rising from the deep toward dappled "
        "surface light"
    ),
    300: (
        "brionypenn watercolor of creatures crossing between ocean and sky, "
        "the waterline a threshold between worlds"
    ),
    450: (
        "brionypenn watercolor of dark seabirds sweeping across grey "
        "Pacific Northwest sky"
    ),
    600: (
        "brionypenn watercolor of birds spiraling together, tightening into "
        "a dark mass descending toward the sea"
    ),
    750: (
        "brionypenn watercolor of a great whale shape forming from the "
        "gathered flock, many becoming one, the whale swimming slowly "
        "through dark water"
    ),
}

PHASE_NAMES = {
    0: "Gathering",
    150: "Rising",
    300: "Crossing",
    450: "Murmuration",
    600: "Convergence",
    750: "Becoming Whale",
}

# Rendering params
CONTROLNET_SCALE = 0.75
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25
SEED = 42
IMG2IMG_STRENGTH = 0.55

# Temporal smoothing
SMOOTH_WINDOW = 9
SMOOTH_SIGMA = 2.5

# Video
FPS_FAST = 30   # 30 seconds
FPS_SLOW = 16   # ~56 seconds

DEVICE = "cuda"
DTYPE = torch.float16

TOTAL_FRAMES = 900


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [DISSOLUTION_V2] {msg}", flush=True)


# ============================================================
# STEP 1: Transfer depth maps from Node 1
# ============================================================
def download_depth_maps():
    """Download 900 depth frames from Node 1 via Jupyter API."""
    log("=" * 60)
    log("STEP 1: Transfer depth maps from Node 1 (boids_v2)")
    log("=" * 60)

    DEPTH_DIR.mkdir(parents=True, exist_ok=True)

    # Check how many we already have
    existing = sorted(DEPTH_DIR.glob("frame_*.png"))
    if len(existing) >= TOTAL_FRAMES:
        log(f"Already have {len(existing)} depth frames, skipping download")
        return True

    headers = {"Authorization": f"token {NODE1_TOKEN}"}

    # List the directory
    log(f"Listing {NODE1_DEPTH_PATH} on Node 1...")
    try:
        r = requests.get(
            f"{NODE1_URL}/api/contents/{NODE1_DEPTH_PATH}",
            headers=headers,
            timeout=30,
        )
        if r.status_code != 200:
            log(f"ERROR: Cannot list depth dir: {r.status_code} {r.text[:200]}")
            return False

        items = r.json().get("content", [])
        png_files = sorted([
            item["name"] for item in items
            if item["name"].startswith("frame_") and item["name"].endswith(".png")
        ])
        log(f"Found {len(png_files)} PNG files on Node 1")

        if len(png_files) == 0:
            log("FATAL: No depth frames found on Node 1!")
            return False

    except Exception as e:
        log(f"FATAL: Could not connect to Node 1: {e}")
        return False

    # Download each frame
    downloaded = 0
    skipped = 0
    errors = 0

    for i, filename in enumerate(png_files):
        out_path = DEPTH_DIR / filename  # Keep original naming

        if out_path.exists():
            skipped += 1
            continue

        try:
            r = requests.get(
                f"{NODE1_URL}/api/contents/{NODE1_DEPTH_PATH}/{filename}",
                headers=headers,
                params={"content": "1"},
                timeout=60,
            )
            if r.status_code != 200:
                log(f"  ERROR downloading {filename}: {r.status_code}")
                errors += 1
                continue

            data = r.json()
            content = data.get("content", "")
            fmt = data.get("format", "")

            if fmt == "base64":
                img_bytes = base64.b64decode(content)
            else:
                img_bytes = content.encode("latin-1")

            # Write raw, then resize
            raw_path = DEPTH_DIR / f"_raw_{filename}"
            with open(raw_path, "wb") as f:
                f.write(img_bytes)

            img = Image.open(raw_path).resize((512, 512), Image.LANCZOS)
            img.save(out_path)
            raw_path.unlink(missing_ok=True)

            downloaded += 1
            if downloaded % 50 == 0:
                log(f"  Downloaded {downloaded}/{len(png_files) - skipped}...")

        except Exception as e:
            log(f"  ERROR on {filename}: {e}")
            errors += 1

    log(f"Download complete: {downloaded} new, {skipped} existing, {errors} errors")
    final_count = len(sorted(DEPTH_DIR.glob("frame_*.png")))
    log(f"Total depth frames: {final_count}")
    return final_count > 0


# ============================================================
# DEPTH PREPROCESSING
# ============================================================
def preprocess_depth(path):
    """Load depth and normalize to 3-channel RGB for ControlNet."""
    img = Image.open(path)
    arr = np.array(img, dtype=np.float32)
    if arr.max() > 255:
        arr = (arr / arr.max() * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    if len(arr.shape) == 2:
        rgb = np.stack([arr, arr, arr], axis=-1)
    elif arr.shape[2] == 1:
        rgb = np.concatenate([arr, arr, arr], axis=-1)
    else:
        rgb = arr[:, :, :3]
    return Image.fromarray(rgb).resize((512, 512))


# ============================================================
# PROMPT LOGIC
# ============================================================
def get_prompt_for_frame(frame_idx):
    phase_starts = sorted(PHASE_PROMPTS.keys())
    prompt = PHASE_PROMPTS[phase_starts[0]]
    for start in phase_starts:
        if frame_idx >= start:
            prompt = PHASE_PROMPTS[start]
    return prompt


def get_phase_name(frame_idx):
    phase_starts = sorted(PHASE_NAMES.keys())
    name = PHASE_NAMES[phase_starts[0]]
    for start in phase_starts:
        if frame_idx >= start:
            name = PHASE_NAMES[start]
    return name


# ============================================================
# TEMPORAL SMOOTHING
# ============================================================
def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=9, sigma=2.5):
    """Temporal gaussian smoothing across frame sequence."""
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


# ============================================================
# VIDEO ASSEMBLY
# ============================================================
def frames_to_video(frames_dir, output_path, fps=30):
    """Assemble frames into MP4 using ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = "ffmpeg"

    frames = sorted(Path(frames_dir).glob("frame_*.png"))
    if not frames:
        log(f"WARNING: No frames in {frames_dir}")
        return

    filelist = Path(frames_dir) / "_filelist.txt"
    with open(filelist, "w") as f:
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
        log(f"Video: {output_path.name} ({size_mb:.1f} MB, {fps}fps, {len(frames)} frames)")
    else:
        log(f"ERROR encoding {output_path.name}: {result.stderr[-500:]}")


# ============================================================
# RENDER
# ============================================================
def render_frames(pipe, bg_image, depth_files, frames_dir, cn_scale,
                  n_frames=None, label="main"):
    """Render frames with the landscape dissolution technique."""
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    if n_frames is None:
        n_frames = len(depth_files)
    else:
        n_frames = min(n_frames, len(depth_files))

    log(f"Rendering {n_frames} frames [{label}] (cn_scale={cn_scale})...")
    timings = []
    rendered_frames = []

    for i in range(n_frames):
        depth_path = depth_files[i]
        out_path = frames_dir / f"frame_{i:05d}.png"

        # Resume support
        if out_path.exists():
            img = Image.open(out_path)
            rendered_frames.append(np.array(img))
            if i % 100 == 0:
                log(f"  [{label}] Frame {i+1}/{n_frames} — skipped (exists)")
            continue

        start = time.perf_counter()

        depth_image = preprocess_depth(depth_path)
        prompt = get_prompt_for_frame(i)

        gen = torch.Generator(DEVICE).manual_seed(SEED)
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=bg_image,
            control_image=depth_image,
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            strength=IMG2IMG_STRENGTH,
            controlnet_conditioning_scale=cn_scale,
            generator=gen,
        ).images[0]

        result.save(out_path)
        rendered_frames.append(np.array(result))

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        if i % 25 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            phase = get_phase_name(i)
            log(f"  [{label}] Frame {i+1}/{n_frames} — {elapsed:.2f}s "
                f"(avg {avg:.2f}s, ETA {remaining/60:.1f}min) "
                f"[{phase}]")

    total_time = sum(timings)
    if timings:
        log(f"  [{label}] Render done: {len(timings)} new frames in "
            f"{total_time/60:.1f}min (avg {total_time/len(timings):.2f}s/frame)")

    return rendered_frames


# ============================================================
# SMOOTH + ASSEMBLE
# ============================================================
def smooth_and_assemble(rendered_frames, smooth_dir, output_dir,
                        name_prefix, fps_list, label="main"):
    smooth_dir = Path(smooth_dir)
    output_dir = Path(output_dir)
    smooth_dir.mkdir(parents=True, exist_ok=True)

    log(f"Temporal smoothing [{label}] (window={SMOOTH_WINDOW}, sigma={SMOOTH_SIGMA})...")
    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=SMOOTH_WINDOW, sigma=SMOOTH_SIGMA)

    for i, frame in enumerate(smoothed):
        Image.fromarray(frame).save(smooth_dir / f"frame_{i:05d}.png")
    log(f"  [{label}] Smoothing done: {len(smoothed)} frames")

    for fps in fps_list:
        video_path = output_dir / f"{name_prefix}_{fps}fps.mp4"
        log(f"  [{label}] Assembling {video_path.name}...")
        frames_to_video(smooth_dir, video_path, fps)


# ============================================================
# MAIN
# ============================================================
def main():
    log("=" * 70)
    log("DISSOLUTION V2 — Boids v2 through Landscape Dissolution")
    log("'Many becoming one — fish, birds, whale, all continuous'")
    log("=" * 70)
    start_time = time.time()

    # GPU check
    if not torch.cuda.is_available():
        log("FATAL: No GPU")
        sys.exit(1)
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log(f"GPU: {gpu} ({vram:.1f} GB)")

    # Create directories
    for d in [BASE_DIR, DEPTH_DIR, OUTPUT_DIR, FRAMES_DIR, SMOOTH_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # ---- STEP 1: Transfer depth maps ----
    ok = download_depth_maps()
    if not ok:
        log("FATAL: Could not get depth maps from Node 1")
        sys.exit(1)

    depth_files = sorted(DEPTH_DIR.glob("frame_*.png"))
    log(f"Depth maps available: {len(depth_files)}")

    if len(depth_files) < TOTAL_FRAMES:
        log(f"WARNING: Only {len(depth_files)} depth frames (expected {TOTAL_FRAMES})")
        ACTUAL_FRAMES = len(depth_files)
    else:
        ACTUAL_FRAMES = TOTAL_FRAMES

    # ---- STEP 2: Generate fixed background ----
    log("\n" + "=" * 60)
    log("STEP 2: Generate fixed background")
    log("=" * 60)

    bg_path = OUTPUT_DIR / "background_v2.png"
    if bg_path.exists():
        log(f"Background already exists: {bg_path}")
        bg_image = Image.open(bg_path).convert("RGB")
    else:
        log("Loading SD 1.5 txt2img pipeline for background...")
        from diffusers import StableDiffusionPipeline, UniPCMultistepScheduler

        bg_pipe = StableDiffusionPipeline.from_pretrained(
            BASE_MODEL, torch_dtype=DTYPE, safety_checker=None
        ).to(DEVICE)
        bg_pipe.scheduler = UniPCMultistepScheduler.from_config(
            bg_pipe.scheduler.config
        )
        bg_pipe.load_lora_weights(LORA_PATH)
        bg_pipe.enable_attention_slicing()

        log("Generating background...")
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
        bg_image.save(bg_path)
        log(f"Background saved: {bg_path}")

        del bg_pipe
        torch.cuda.empty_cache()

    # ---- STEP 3: Load ControlNet img2img pipeline ----
    log("\n" + "=" * 60)
    log("STEP 3: Render with landscape dissolution technique")
    log("=" * 60)

    log("Loading ControlNet depth model...")
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL, torch_dtype=DTYPE
    )
    log("Loading SD 1.5 + ControlNet img2img pipeline...")
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet, torch_dtype=DTYPE, safety_checker=None
    ).to(DEVICE)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LORA_PATH)
    pipe.enable_attention_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
        log("xformers enabled")
    except Exception:
        log("xformers not available, using standard attention")
    log("Pipeline loaded.")

    # ---- Render main ----
    rendered_main = render_frames(
        pipe, bg_image, depth_files, FRAMES_DIR,
        cn_scale=CONTROLNET_SCALE,
        n_frames=ACTUAL_FRAMES,
        label="main",
    )

    # Smooth + assemble
    smooth_and_assemble(
        rendered_main, SMOOTH_DIR, OUTPUT_DIR,
        name_prefix="boids_v2_dissolution",
        fps_list=[FPS_FAST, FPS_SLOW],
        label="main",
    )

    # ---- Summary ----
    total_time = time.time() - start_time
    log("\n" + "=" * 70)
    log("ALL DONE — Dissolution v2")
    log(f"Total time: {total_time/60:.1f}min")
    log(f"Output dir: {OUTPUT_DIR}")

    # List outputs
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        size_mb = f.stat().st_size / 1e6
        log(f"  {f.name} ({size_mb:.1f} MB)")

    log("=" * 70)


if __name__ == "__main__":
    main()
