#!/usr/bin/env python3
"""
Landscape Dissolution — Narrative Boids (30-second, 900 frames, 6 phases)
=========================================================================
The "landscape dissolution" technique: Boids depth maps rendered through
ControlNet depth with landscape prompts. Fish shapes dissolve into/become
landscape elements. The fish form IS the landscape — "each creature contains
the whole ecosystem."

Source depth maps: Node 1 /home/jovyan/explore/exp1_narrative_boids/depth/
(900 frames, 6 narrative phases)

Pipeline:
  1. Download 900 depth frames from Node 1, resize to 512x512
  2. Generate fixed background (SD 1.5 + Briony LoRA)
  3. Render 900 frames: img2img background + ControlNet depth + phase prompts
  4. Render 3 ControlNet scale variants (first 150 frames each)
  5. Temporal smoothing + video assembly (30fps + 16fps)

Output: /home/jovyan/landscape_dissolution/output/

Run:
  nohup python3 /home/jovyan/landscape_dissolution/landscape_dissolution_narrative.py \
    >> /home/jovyan/landscape_dissolution/progress.log 2>&1 &
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
BASE_DIR = Path("/home/jovyan/landscape_dissolution")
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
NODE1_DEPTH_PATH = "explore/exp1_narrative_boids/depth"

# Background generation
BG_PROMPT = (
    "brionypenn watercolor painting of Pacific Northwest coastal landscape, "
    "ocean meeting sky at horizon, grey overcast, cedar trees along shoreline, "
    "soft muted tones, atmospheric perspective"
)
NEGATIVE_PROMPT = (
    "blurry, low quality, photographic, 3d render, digital art, neon, "
    "oversaturated, text, watermark"
)

# 6-phase prompt progression (each phase = 150 frames)
PHASE_PROMPTS = {
    # Frames 0-150: "The Gathering" — fish school forming
    0: (
        "brionypenn watercolor of silver herring school swimming in cold ocean, "
        "shimmering underwater light, natural history illustration"
    ),
    # Frames 150-300: "The Rising" — school rises toward surface
    150: (
        "brionypenn watercolor of fish rising through blue-green water toward "
        "the surface, light filtering from above"
    ),
    # Frames 300-450: "The Transformation" — fish cross waterline, become birds
    300: (
        "brionypenn watercolor of creatures crossing between ocean and sky, "
        "water surface reflecting clouds, Pacific Northwest coast"
    ),
    # Frames 450-600: "The Murmuration" — birds swirl in sky
    450: (
        "brionypenn watercolor of dark seabirds in murmuration against grey sky, "
        "Pacific Northwest coastline below, atmospheric"
    ),
    # Frames 600-750: "The Convergence" — murmuration tightens
    600: (
        "brionypenn watercolor of birds spiraling together against overcast sky, "
        "tightening into a dark mass"
    ),
    # Frames 750-900: "The Whale" — mass becomes single whale
    750: (
        "brionypenn watercolor of a great whale shape emerging in dark water, "
        "vast and solitary, Pacific Northwest ocean"
    ),
}

# Phase names for logging
PHASE_NAMES = {
    0: "The Gathering",
    150: "The Rising",
    300: "The Transformation",
    450: "The Murmuration",
    600: "The Convergence",
    750: "The Whale",
}

# Rendering params
CONTROLNET_SCALE = 0.75
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25  # Reduced from 30 to save time on 900 frames
SEED = 42
IMG2IMG_STRENGTH = 0.55

# Temporal smoothing
SMOOTH_WINDOW = 9
SMOOTH_SIGMA = 2.5

# Video
FPS_FAST = 30   # 30 seconds
FPS_SLOW = 16   # ~56 seconds, dreamier

# Variant ControlNet scales (render first 150 frames only)
VARIANT_SCALES = {
    "cn060": 0.60,  # Looser — more abstract
    "cn085": 0.85,  # Tighter — more structural
    "cn050": 0.50,  # Very loose — impressionistic
}
VARIANT_FRAMES = 150  # Only first 150 frames for variants

DEVICE = "cuda"
DTYPE = torch.float16

TOTAL_FRAMES = 900


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [LANDSCAPE] {msg}", flush=True)


# ============================================================
# STEP 1: Transfer depth maps from Node 1
# ============================================================
def download_depth_maps():
    """Download 900 depth frames from Node 1 via Jupyter API."""
    log("=" * 60)
    log("STEP 1: Transfer depth maps from Node 1")
    log("=" * 60)

    DEPTH_DIR.mkdir(parents=True, exist_ok=True)

    # Check how many we already have
    existing = sorted(DEPTH_DIR.glob("frame_*.png"))
    if len(existing) >= TOTAL_FRAMES:
        log(f"Already have {len(existing)} depth frames, skipping download")
        return True

    headers = {
        "Authorization": f"token {NODE1_TOKEN}",
    }

    # First, list the directory to get filenames
    log(f"Listing {NODE1_DEPTH_PATH} on Node 1...")
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

    # Download each frame
    downloaded = 0
    skipped = 0
    errors = 0

    for i, filename in enumerate(png_files):
        # Normalize output filename to frame_NNNN.png format
        out_path = DEPTH_DIR / f"frame_{i:04d}.png"

        if out_path.exists():
            skipped += 1
            if skipped % 100 == 0:
                log(f"  Skipped {skipped} existing frames...")
            continue

        try:
            r = requests.get(
                f"{NODE1_URL}/api/contents/{NODE1_DEPTH_PATH}/{filename}",
                headers=headers,
                params={"content": "1"},
                timeout=30,
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
                # Text content — shouldn't happen for PNG but handle it
                img_bytes = content.encode("latin-1")

            # Write raw bytes first
            raw_path = DEPTH_DIR / f"_raw_{filename}"
            with open(raw_path, "wb") as f:
                f.write(img_bytes)

            # Resize to 512x512
            img = Image.open(raw_path)
            img_resized = img.resize((512, 512), Image.LANCZOS)
            img_resized.save(out_path)

            # Clean up raw
            raw_path.unlink(missing_ok=True)

            downloaded += 1
            if downloaded % 50 == 0:
                log(f"  Downloaded {downloaded}/{len(png_files) - skipped} frames...")

        except Exception as e:
            log(f"  ERROR on {filename}: {e}")
            errors += 1

    log(f"Download complete: {downloaded} new, {skipped} existing, {errors} errors")

    # Verify count
    final_count = len(sorted(DEPTH_DIR.glob("frame_*.png")))
    log(f"Total depth frames: {final_count}")
    return final_count > 0


# ============================================================
# DEPTH PREPROCESSING
# ============================================================
def preprocess_depth(path):
    """Load 16-bit depth and normalize to 3-channel RGB for ControlNet."""
    img = Image.open(path)
    arr = np.array(img, dtype=np.float32)
    if arr.max() > 255:
        arr = (arr / arr.max() * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    # Handle both single-channel and multi-channel
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
    """Return prompt for the given frame based on 6-phase structure."""
    # Find which phase we're in
    phase_starts = sorted(PHASE_PROMPTS.keys())
    current_prompt = PHASE_PROMPTS[phase_starts[0]]
    for start in phase_starts:
        if frame_idx >= start:
            current_prompt = PHASE_PROMPTS[start]
    return current_prompt


def get_phase_name(frame_idx):
    """Return phase name for logging."""
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
        ffmpeg = "ffmpeg"  # Fall back to system ffmpeg

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
# RENDER FUNCTION (shared by main + variants)
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
            if i % 50 == 0:
                log(f"  [{label}] Frame {i+1}/{n_frames} — skipped (exists)")
            continue

        start = time.perf_counter()

        # Load and preprocess depth
        depth_image = preprocess_depth(depth_path)

        # Phase-appropriate prompt
        prompt = get_prompt_for_frame(i)

        # img2img the background with ControlNet depth overlay
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
    """Apply temporal smoothing and assemble videos."""
    smooth_dir = Path(smooth_dir)
    output_dir = Path(output_dir)
    smooth_dir.mkdir(parents=True, exist_ok=True)

    log(f"Temporal smoothing [{label}] (window={SMOOTH_WINDOW}, sigma={SMOOTH_SIGMA})...")
    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=SMOOTH_WINDOW, sigma=SMOOTH_SIGMA)

    for i, frame in enumerate(smoothed):
        Image.fromarray(frame).save(smooth_dir / f"frame_{i:05d}.png")
    log(f"  [{label}] Smoothing done: {len(smoothed)} frames")

    # Assemble at each FPS
    for fps in fps_list:
        video_path = output_dir / f"{name_prefix}_{fps}fps.mp4"
        log(f"  [{label}] Assembling {video_path.name}...")
        frames_to_video(smooth_dir, video_path, fps)


# ============================================================
# MAIN
# ============================================================
def main():
    log("=" * 70)
    log("LANDSCAPE DISSOLUTION — NARRATIVE BOIDS (6 phases, 900 frames)")
    log("'Each creature contains the whole ecosystem'")
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
        log("FATAL: Could not get depth maps")
        sys.exit(1)

    depth_files = sorted(DEPTH_DIR.glob("frame_*.png"))
    log(f"Depth maps available: {len(depth_files)}")

    # ---- STEP 2: Generate fixed background ----
    log("\n" + "=" * 60)
    log("STEP 2: Generate fixed background")
    log("=" * 60)

    bg_path = OUTPUT_DIR / "background.png"
    if bg_path.exists():
        log(f"Background already exists, loading: {bg_path}")
        bg_image = Image.open(bg_path).convert("RGB")
    else:
        log("Loading SD 1.5 txt2img pipeline for background...")
        from diffusers import (
            StableDiffusionPipeline,
            UniPCMultistepScheduler,
        )
        bg_pipe = StableDiffusionPipeline.from_pretrained(
            BASE_MODEL, torch_dtype=DTYPE, safety_checker=None
        ).to(DEVICE)
        bg_pipe.scheduler = UniPCMultistepScheduler.from_config(bg_pipe.scheduler.config)
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

    # ---- Render main (all 900 frames, cn_scale=0.75) ----
    rendered_main = render_frames(
        pipe, bg_image, depth_files, FRAMES_DIR,
        cn_scale=CONTROLNET_SCALE,
        n_frames=TOTAL_FRAMES,
        label="main",
    )

    # Smooth + assemble main
    smooth_and_assemble(
        rendered_main, SMOOTH_DIR, OUTPUT_DIR,
        name_prefix="narrative_boids_landscape",
        fps_list=[FPS_FAST, FPS_SLOW],
        label="main",
    )

    # ---- STEP 4: Render variants (first 150 frames) ----
    log("\n" + "=" * 60)
    log("STEP 4: ControlNet scale variants (first 150 frames)")
    log("=" * 60)

    for variant_name, cn_scale in VARIANT_SCALES.items():
        var_frames_dir = OUTPUT_DIR / f"frames_{variant_name}"
        var_smooth_dir = OUTPUT_DIR / f"smoothed_{variant_name}"

        rendered_var = render_frames(
            pipe, bg_image, depth_files, var_frames_dir,
            cn_scale=cn_scale,
            n_frames=VARIANT_FRAMES,
            label=variant_name,
        )

        smooth_and_assemble(
            rendered_var, var_smooth_dir, OUTPUT_DIR,
            name_prefix=f"variant_{variant_name}",
            fps_list=[FPS_FAST],
            label=variant_name,
        )

    # ---- FINAL SUMMARY ----
    total_time = time.time() - start_time
    log("\n" + "=" * 70)
    log("LANDSCAPE DISSOLUTION COMPLETE")
    log("=" * 70)
    log(f"Total time: {total_time/60:.1f} min ({total_time/3600:.1f} hours)")
    log(f"Output directory: {OUTPUT_DIR}")
    log("")

    # List all outputs
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        size_mb = f.stat().st_size / 1e6
        log(f"  {f.name} ({size_mb:.1f} MB)")
    for f in sorted(OUTPUT_DIR.glob("*.png")):
        if "frame_" not in f.name:
            log(f"  {f.name}")

    # Write completion marker
    marker = OUTPUT_DIR / "COMPLETE"
    with open(marker, "w") as fh:
        fh.write(f"Completed: {datetime.datetime.now().isoformat()}\n")
        fh.write(f"Total time: {total_time/60:.1f} minutes\n")
        fh.write(f"Main render: {TOTAL_FRAMES} frames, cn_scale={CONTROLNET_SCALE}\n")
        for vn, vs in VARIANT_SCALES.items():
            fh.write(f"Variant {vn}: {VARIANT_FRAMES} frames, cn_scale={vs}\n")
    log(f"Completion marker: {marker}")
    log("DONE.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
