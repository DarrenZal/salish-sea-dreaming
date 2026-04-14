#!/usr/bin/env python3
"""
Landscape Dissolution — Research Improvements (Node 2)
======================================================
Applies findings from the deep research report to improve the landscape
dissolution technique. Four experiments:

  1. Dynamic ControlNet Scale — cosine-interpolated scale per phase
  2. Prompt Superposition    — ambiguous prompts for the canopy phase
  3. Higher Resolution 768   — canopy phase at 768x768 for detail
  4. Seamless Loop Test      — 30-frame pixel-space crossfade

Uses existing Boids v2 depth maps at /home/jovyan/landscape_dissolution/depth/
(900 frames, 512x512) and the existing background.png from the baseline run.

Output: /home/jovyan/research_improvements/output/
  - dynamic_cn_scale_30fps.mp4 — main result with dynamic scaling
  - dynamic_cn_scale_16fps.mp4 — dreamy version
  - canopy_768px_30fps.mp4     — higher res canopy phase only
  - loop_test_30fps.mp4        — seamless loop test

Run:
  nohup python3 /home/jovyan/research_improvements/research_improvements_node2.py \
    >> /home/jovyan/research_improvements/progress.log 2>&1 &

Author: Darren Zal + Claude
Date: 2026-04-04
"""

import os
import sys
import gc
import time
import math
import subprocess
import traceback
import numpy as np
import datetime

from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path("/home/jovyan/research_improvements")
OUTPUT_DIR = BASE_DIR / "output"
LOG_FILE = BASE_DIR / "progress.log"

# Source depth maps (already on this node)
DEPTH_DIR = Path("/home/jovyan/landscape_dissolution/depth")

# Reuse background from baseline run
BG_PATH = Path("/home/jovyan/landscape_dissolution/output/background.png")

LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET_MODEL = "lllyasviel/control_v11f1p_sd15_depth"

# Background generation (if baseline bg not available)
BG_PROMPT = (
    "brionypenn watercolor of Pacific Northwest coast, "
    "ocean below meeting grey sky above, cedar trees along shoreline, "
    "the waterline dividing two worlds, soft atmospheric muted tones"
)
NEGATIVE_PROMPT = (
    "blurry, low quality, photographic, 3d render, digital art, neon, "
    "oversaturated, text, watermark"
)

# Rendering params
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25
SEED = 42
IMG2IMG_STRENGTH = 0.55

# Temporal smoothing
SMOOTH_WINDOW = 9
SMOOTH_SIGMA = 2.5

# Video
FPS_FAST = 30
FPS_SLOW = 16

DEVICE = "cuda"
TOTAL_FRAMES = 900

# ============================================================
# EXPERIMENT 1: Dynamic ControlNet Scale (per-phase, cosine interpolated)
# ============================================================
# Phase boundaries and target scales from the research report
PHASE_SCALES = [
    # (start_frame, end_frame, cn_scale, phase_name)
    (0,   150, 0.85, "Gathering/Fish"),
    (150, 300, 0.75, "Rising"),
    (300, 450, 0.60, "Crossing waterline"),
    (450, 600, 0.40, "Murmuration/Canopy"),   # KEY: very loose
    (600, 750, 0.65, "Convergence"),
    (750, 900, 0.90, "Whale"),
]

# ============================================================
# EXPERIMENT 2: Prompt Superposition (ambiguous canopy prompts)
# ============================================================
PHASE_PROMPTS_DYNAMIC = {
    0: (
        "brionypenn watercolor of silver herring schooling in cold dark water, "
        "underwater, shimmering scales, natural history illustration"
    ),
    150: (
        "brionypenn watercolor of fish rising through blue-green water toward "
        "the surface, light filtering from above, Pacific Northwest"
    ),
    300: (
        "brionypenn watercolor of creatures crossing between ocean and sky, "
        "water surface reflecting clouds, the threshold between worlds"
    ),
    # SUPERPOSITION: ambiguous prompt that reads as both birds AND trees
    450: (
        "brionypenn watercolor of organic fractal clusters, rhythmic branching, "
        "dappled light through shifting forms, Pacific Northwest, "
        "natural history illustration"
    ),
    600: (
        "brionypenn watercolor of dark forms spiraling together against grey sky, "
        "tightening into a dense mass, Pacific Northwest coast"
    ),
    750: (
        "brionypenn watercolor of a great whale shape in dark Pacific ocean, "
        "solitary and vast, natural history illustration"
    ),
}

PHASE_NAMES = {
    0: "Gathering",
    150: "Rising",
    300: "Crossing",
    450: "Murmuration/Canopy",
    600: "Convergence",
    750: "Whale",
}


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [RESEARCH] {msg}", flush=True)


# ============================================================
# COSINE INTERPOLATION for dynamic ControlNet scale
# ============================================================
def cosine_interp(a, b, t):
    """Cosine interpolation between a and b. t in [0, 1]."""
    return a + (b - a) * (1 - math.cos(t * math.pi)) / 2


def get_cn_scale(frame_idx):
    """Return cosine-interpolated ControlNet scale for a given frame.

    Within each phase, the scale cosine-interpolates from the current
    phase's target to the next phase's target.
    """
    for i, (start, end, scale, _) in enumerate(PHASE_SCALES):
        if start <= frame_idx < end:
            # Determine the next phase's scale for interpolation
            if i + 1 < len(PHASE_SCALES):
                next_scale = PHASE_SCALES[i + 1][2]
            else:
                next_scale = scale  # Last phase: hold steady

            # t = progress within this phase [0, 1]
            t = (frame_idx - start) / (end - start)
            return cosine_interp(scale, next_scale, t)

    # Fallback (should not reach)
    return PHASE_SCALES[-1][2]


def get_prompt(frame_idx):
    """Return prompt for frame based on 6-phase structure."""
    phase_starts = sorted(PHASE_PROMPTS_DYNAMIC.keys())
    prompt = PHASE_PROMPTS_DYNAMIC[phase_starts[0]]
    for start in phase_starts:
        if frame_idx >= start:
            prompt = PHASE_PROMPTS_DYNAMIC[start]
    return prompt


def get_phase_name(frame_idx):
    """Return phase name for logging."""
    phase_starts = sorted(PHASE_NAMES.keys())
    name = PHASE_NAMES[phase_starts[0]]
    for start in phase_starts:
        if frame_idx >= start:
            name = PHASE_NAMES[start]
    return name


# ============================================================
# DEPTH PREPROCESSING
# ============================================================
def preprocess_depth(path, target_size=512):
    """Load depth and normalize to 3-channel RGB for ControlNet."""
    from PIL import Image
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
    return Image.fromarray(rgb).resize((target_size, target_size), Image.LANCZOS)


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


def pil_to_video(pil_frames, output_path, fps=30):
    """Save list of PIL images directly as MP4."""
    import imageio
    writer = imageio.get_writer(
        str(output_path), fps=fps, codec="libx264",
        output_params=["-pix_fmt", "yuv420p", "-crf", "18"],
    )
    for frame in pil_frames:
        arr = np.array(frame)
        if arr.dtype in (np.float32, np.float64):
            arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        writer.append_data(arr)
    writer.close()
    size_mb = Path(output_path).stat().st_size / 1e6
    log(f"Video: {output_path.name} ({size_mb:.1f} MB, {fps}fps, {len(pil_frames)} frames)")


# ============================================================
# INSTALL DEPENDENCIES
# ============================================================
def install_deps():
    log("Installing dependencies...")
    packages = [
        "diffusers>=0.32.0",
        "transformers",
        "accelerate",
        "safetensors",
        "peft",
        "imageio",
        "imageio-ffmpeg",
        "Pillow",
        "numpy",
        "scipy",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "--upgrade"] + packages
    )
    log("Dependencies installed.")


# ============================================================
# EXPERIMENT 1 + 2: Dynamic ControlNet Scale + Prompt Superposition
# (Combined — the dynamic scale IS the experiment, with superposition prompts)
# ============================================================
def experiment_dynamic_cn_scale(pipe, bg_image, depth_files):
    """Render all 900 frames with per-frame cosine-interpolated CN scale
    and superposition prompts for the canopy phase."""
    import torch
    from PIL import Image

    log("\n" + "=" * 70)
    log("EXPERIMENT 1+2: Dynamic ControlNet Scale + Prompt Superposition")
    log("=" * 70)

    frames_dir = OUTPUT_DIR / "frames_dynamic"
    smooth_dir = OUTPUT_DIR / "smoothed_dynamic"
    frames_dir.mkdir(parents=True, exist_ok=True)
    smooth_dir.mkdir(parents=True, exist_ok=True)

    n_frames = min(TOTAL_FRAMES, len(depth_files))
    log(f"Rendering {n_frames} frames with dynamic CN scale...")
    log("Phase scale map:")
    for start, end, scale, name in PHASE_SCALES:
        log(f"  Frames {start:>3}-{end:>3}: cn_scale={scale:.2f} ({name})")

    timings = []
    rendered_frames = []

    for i in range(n_frames):
        out_path = frames_dir / f"frame_{i:05d}.png"

        # Resume support
        if out_path.exists():
            img = Image.open(out_path)
            rendered_frames.append(np.array(img))
            if i % 100 == 0:
                log(f"  Frame {i+1}/{n_frames} — skipped (exists)")
            continue

        start_t = time.perf_counter()

        # Per-frame dynamic values
        cn_scale = get_cn_scale(i)
        prompt = get_prompt(i)
        depth_image = preprocess_depth(depth_files[i])

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

        elapsed = time.perf_counter() - start_t
        timings.append(elapsed)

        if i % 25 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            phase = get_phase_name(i)
            log(f"  Frame {i+1}/{n_frames} — {elapsed:.2f}s "
                f"(avg {avg:.2f}s, ETA {remaining/60:.1f}min) "
                f"[{phase}, cn={cn_scale:.3f}]")

        # Periodic VRAM cleanup
        if (i + 1) % 100 == 0:
            gc.collect()
            torch.cuda.empty_cache()

    total_time = sum(timings)
    if timings:
        log(f"Render done: {len(timings)} new frames in "
            f"{total_time/60:.1f}min (avg {total_time/len(timings):.2f}s/frame)")

    # Temporal smoothing
    log(f"Temporal smoothing (window={SMOOTH_WINDOW}, sigma={SMOOTH_SIGMA})...")
    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=SMOOTH_WINDOW, sigma=SMOOTH_SIGMA)

    for i, frame in enumerate(smoothed):
        from PIL import Image as PILImage
        PILImage.fromarray(frame).save(smooth_dir / f"frame_{i:05d}.png")
    log(f"Smoothing done: {len(smoothed)} frames")

    # Assemble videos
    for fps, suffix in [(FPS_FAST, "30fps"), (FPS_SLOW, "16fps")]:
        video_path = OUTPUT_DIR / f"dynamic_cn_scale_{suffix}.mp4"
        log(f"Assembling {video_path.name}...")
        frames_to_video(smooth_dir, video_path, fps)

    # Save CN scale curve for reference
    scale_log_path = OUTPUT_DIR / "cn_scale_curve.csv"
    with open(scale_log_path, "w") as f:
        f.write("frame,cn_scale,phase\n")
        for i in range(n_frames):
            f.write(f"{i},{get_cn_scale(i):.4f},{get_phase_name(i)}\n")
    log(f"CN scale curve saved: {scale_log_path}")

    return rendered_frames


# ============================================================
# EXPERIMENT 3: Higher Resolution (768x768) — Canopy Phase Only
# ============================================================
def experiment_768_canopy(pipe_512, bg_image_512, depth_files):
    """Re-render the canopy phase (frames 450-600) at 768x768.

    This requires building a separate pipeline at 768 resolution.
    We resize depth maps and background to 768x768.
    """
    import torch
    from PIL import Image
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    log("\n" + "=" * 70)
    log("EXPERIMENT 3: Canopy Phase at 768x768")
    log("=" * 70)

    frames_dir = OUTPUT_DIR / "frames_768_canopy"
    smooth_dir = OUTPUT_DIR / "smoothed_768_canopy"
    frames_dir.mkdir(parents=True, exist_ok=True)
    smooth_dir.mkdir(parents=True, exist_ok=True)

    # Frame range for canopy phase
    CANOPY_START = 450
    CANOPY_END = 600
    n_frames = CANOPY_END - CANOPY_START

    # Resize background to 768x768
    bg_768 = bg_image_512.resize((768, 768), Image.LANCZOS)
    log(f"Background resized to 768x768")

    # Use the superposition prompt for canopy
    canopy_prompt = PHASE_PROMPTS_DYNAMIC[450]
    # CN scale from the dynamic curve at mid-canopy
    canopy_cn_scale = 0.40  # The research target for this phase

    log(f"Rendering frames {CANOPY_START}-{CANOPY_END} at 768x768 (cn_scale={canopy_cn_scale})")
    log(f"Prompt: {canopy_prompt[:80]}...")

    # We need to clear the 512 pipeline and load a fresh one for 768
    # Actually, SD 1.5 + ControlNet can handle 768 directly — just pass 768x768 images
    # The pipeline doesn't have a fixed resolution. We just need to ensure
    # all inputs (image, control_image) are 768x768.

    # Use the existing pipeline — it handles variable resolution
    pipe = pipe_512

    timings = []
    rendered_frames = []

    for i in range(n_frames):
        frame_idx = CANOPY_START + i
        out_path = frames_dir / f"frame_{i:05d}.png"

        # Resume support
        if out_path.exists():
            img = Image.open(out_path)
            rendered_frames.append(np.array(img))
            if i % 50 == 0:
                log(f"  Frame {i+1}/{n_frames} (global {frame_idx}) — skipped (exists)")
            continue

        start_t = time.perf_counter()

        # Depth at 768x768
        depth_image = preprocess_depth(depth_files[frame_idx], target_size=768)

        # Use cosine-interpolated CN scale for this frame
        cn_scale = get_cn_scale(frame_idx)

        gen = torch.Generator(DEVICE).manual_seed(SEED)
        result = pipe(
            prompt=canopy_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=bg_768,
            control_image=depth_image,
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            strength=IMG2IMG_STRENGTH,
            controlnet_conditioning_scale=cn_scale,
            generator=gen,
        ).images[0]

        result.save(out_path)
        rendered_frames.append(np.array(result))

        elapsed = time.perf_counter() - start_t
        timings.append(elapsed)

        if i % 10 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            log(f"  Frame {i+1}/{n_frames} (global {frame_idx}) — {elapsed:.2f}s "
                f"(avg {avg:.2f}s, ETA {remaining/60:.1f}min) "
                f"[cn={cn_scale:.3f}]")

    total_time = sum(timings)
    if timings:
        log(f"768px render done: {len(timings)} new frames in "
            f"{total_time/60:.1f}min (avg {total_time/len(timings):.2f}s/frame)")

    # Temporal smoothing
    log(f"Temporal smoothing (window={SMOOTH_WINDOW})...")
    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=SMOOTH_WINDOW, sigma=SMOOTH_SIGMA)

    for i, frame in enumerate(smoothed):
        from PIL import Image as PILImage
        PILImage.fromarray(frame).save(smooth_dir / f"frame_{i:05d}.png")

    # Assemble video
    video_path = OUTPUT_DIR / "canopy_768px_30fps.mp4"
    log(f"Assembling {video_path.name}...")
    frames_to_video(smooth_dir, video_path, FPS_FAST)

    return rendered_frames


# ============================================================
# EXPERIMENT 4: Seamless Loop Test
# ============================================================
def experiment_loop_test(rendered_dynamic):
    """Create a seamless loop from the dynamic CN scale render.

    Crossfade the first and last 30 frames in pixel space. Both ends
    show the fish school (frames 0-30 and 870-900), which should be
    visually similar enough for a smooth crossfade.
    """
    from PIL import Image

    log("\n" + "=" * 70)
    log("EXPERIMENT 4: Seamless Loop Test (30-frame crossfade)")
    log("=" * 70)

    if len(rendered_dynamic) < 60:
        log("ERROR: Not enough frames for loop test (need at least 60)")
        return

    n_total = len(rendered_dynamic)
    CROSSFADE = 30  # frames of crossfade

    # Strategy: trim the last CROSSFADE frames and crossfade them with the first CROSSFADE
    # Result length = n_total - CROSSFADE

    loop_frames = []
    for i in range(n_total - CROSSFADE):
        if i < CROSSFADE:
            # Crossfade zone: blend frame i (start) with frame (n_total - CROSSFADE + i) (end)
            alpha = i / CROSSFADE  # 0.0 at start -> 1.0 at crossfade boundary

            # Use cosine easing for smoother crossfade
            alpha = (1 - math.cos(alpha * math.pi)) / 2

            frame_start = rendered_dynamic[i].astype(np.float32)
            frame_end = rendered_dynamic[n_total - CROSSFADE + i].astype(np.float32)
            blended = frame_start * alpha + frame_end * (1 - alpha)
            loop_frames.append(np.clip(blended, 0, 255).astype(np.uint8))
        else:
            loop_frames.append(rendered_dynamic[i])

    log(f"Loop: {len(loop_frames)} frames (original {n_total}, crossfade {CROSSFADE})")

    # Save loop frames and assemble
    loop_frames_dir = OUTPUT_DIR / "frames_loop"
    loop_frames_dir.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(loop_frames):
        Image.fromarray(frame).save(loop_frames_dir / f"frame_{i:05d}.png")

    video_path = OUTPUT_DIR / "loop_test_30fps.mp4"
    log(f"Assembling {video_path.name}...")
    frames_to_video(loop_frames_dir, video_path, FPS_FAST)

    # Also create a 3x loop to verify seamlessness
    triple_dir = OUTPUT_DIR / "frames_loop_3x"
    triple_dir.mkdir(parents=True, exist_ok=True)
    frame_count = 0
    for cycle in range(3):
        for i, frame in enumerate(loop_frames):
            Image.fromarray(frame).save(triple_dir / f"frame_{frame_count:05d}.png")
            frame_count += 1

    triple_path = OUTPUT_DIR / "loop_test_3x_30fps.mp4"
    log(f"Assembling {triple_path.name} (3 cycles for verification)...")
    frames_to_video(triple_dir, triple_path, FPS_FAST)


# ============================================================
# MAIN
# ============================================================
def main():
    import torch
    from PIL import Image

    log("=" * 70)
    log("LANDSCAPE DISSOLUTION — RESEARCH IMPROVEMENTS")
    log("Applying deep research findings to Boids v2 depth maps")
    log("=" * 70)
    start_time = time.time()

    # Install deps
    install_deps()

    # GPU check
    if not torch.cuda.is_available():
        log("FATAL: No GPU")
        sys.exit(1)
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log(f"GPU: {gpu} ({vram:.1f} GB)")

    # Create directories
    for d in [BASE_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # ---- Verify depth maps ----
    depth_files = sorted(DEPTH_DIR.glob("frame_*.png"))
    log(f"Depth maps available: {len(depth_files)}")
    if len(depth_files) < TOTAL_FRAMES:
        log(f"WARNING: Only {len(depth_files)} depth frames (expected {TOTAL_FRAMES})")
    if len(depth_files) == 0:
        log("FATAL: No depth maps found!")
        sys.exit(1)

    # ---- Load or generate background ----
    if BG_PATH.exists():
        log(f"Reusing background from baseline: {BG_PATH}")
        bg_image = Image.open(BG_PATH).convert("RGB")
    else:
        log("Baseline background not found, generating new one...")
        from diffusers import StableDiffusionPipeline, UniPCMultistepScheduler

        bg_pipe = StableDiffusionPipeline.from_pretrained(
            BASE_MODEL, torch_dtype=torch.float16, safety_checker=None
        ).to(DEVICE)
        bg_pipe.scheduler = UniPCMultistepScheduler.from_config(bg_pipe.scheduler.config)
        bg_pipe.load_lora_weights(LORA_PATH)
        bg_pipe.enable_attention_slicing()

        gen = torch.Generator(DEVICE).manual_seed(SEED)
        bg_image = bg_pipe(
            prompt=BG_PROMPT,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=40,
            guidance_scale=7.5,
            generator=gen,
            width=512, height=512,
        ).images[0]

        bg_save_path = OUTPUT_DIR / "background.png"
        bg_image.save(bg_save_path)
        log(f"Background saved: {bg_save_path}")

        del bg_pipe
        torch.cuda.empty_cache()

    # ---- Load ControlNet img2img pipeline ----
    log("\nLoading ControlNet depth model...")
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL, torch_dtype=torch.float16
    )
    log("Loading SD 1.5 + ControlNet img2img pipeline...")
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet, torch_dtype=torch.float16,
        safety_checker=None
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

    # ============================================================
    # RUN EXPERIMENTS
    # ============================================================
    results = {}

    # ---- Experiment 1+2: Dynamic CN Scale + Prompt Superposition ----
    try:
        t_exp = time.time()
        rendered_dynamic = experiment_dynamic_cn_scale(pipe, bg_image, depth_files)
        elapsed = time.time() - t_exp
        results["Exp 1+2: Dynamic CN + Superposition"] = f"OK ({elapsed/60:.1f}min)"
        log(f"Experiment 1+2 complete: {elapsed/60:.1f}min")
    except Exception as e:
        log(f"Experiment 1+2 FAILED: {e}")
        traceback.print_exc()
        results["Exp 1+2: Dynamic CN + Superposition"] = f"FAILED: {e}"
        rendered_dynamic = None

    gc.collect()
    torch.cuda.empty_cache()

    # ---- Experiment 3: 768x768 Canopy ----
    try:
        t_exp = time.time()
        experiment_768_canopy(pipe, bg_image, depth_files)
        elapsed = time.time() - t_exp
        results["Exp 3: 768px Canopy"] = f"OK ({elapsed/60:.1f}min)"
        log(f"Experiment 3 complete: {elapsed/60:.1f}min")
    except Exception as e:
        log(f"Experiment 3 FAILED: {e}")
        traceback.print_exc()
        results["Exp 3: 768px Canopy"] = f"FAILED: {e}"

    gc.collect()
    torch.cuda.empty_cache()

    # ---- Experiment 4: Seamless Loop ----
    if rendered_dynamic is not None:
        try:
            t_exp = time.time()
            experiment_loop_test(rendered_dynamic)
            elapsed = time.time() - t_exp
            results["Exp 4: Seamless Loop"] = f"OK ({elapsed/60:.1f}min)"
            log(f"Experiment 4 complete: {elapsed/60:.1f}min")
        except Exception as e:
            log(f"Experiment 4 FAILED: {e}")
            traceback.print_exc()
            results["Exp 4: Seamless Loop"] = f"FAILED: {e}"
    else:
        results["Exp 4: Seamless Loop"] = "SKIPPED (no dynamic render)"
        log("Experiment 4 skipped — dynamic render failed")

    # ============================================================
    # SUMMARY
    # ============================================================
    total_time = time.time() - start_time
    log("\n" + "=" * 70)
    log("RESEARCH IMPROVEMENTS — FINAL SUMMARY")
    log(f"Total runtime: {total_time/60:.1f}min ({total_time/3600:.1f}h)")
    log("=" * 70)

    for name, status in results.items():
        log(f"  {name}: {status}")

    log("\nOutput files:")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        size_mb = f.stat().st_size / 1e6
        log(f"  {f.name} ({size_mb:.1f} MB)")
    for f in sorted(OUTPUT_DIR.glob("*.csv")):
        log(f"  {f.name}")

    # Write completion marker
    marker = OUTPUT_DIR / "COMPLETE"
    with open(marker, "w") as fh:
        fh.write(f"Completed: {datetime.datetime.now().isoformat()}\n")
        fh.write(f"Total time: {total_time/60:.1f} minutes\n")
        for name, status in results.items():
            fh.write(f"{name}: {status}\n")
    log(f"Completion marker: {marker}")

    log("")
    log("KEY FINDINGS TO COMPARE:")
    log("  - dynamic_cn_scale vs baseline (narrative_boids_landscape): does dynamic CN scale")
    log("    improve the murmuration/canopy dissolution? Check frames 450-600.")
    log("  - canopy_768px: more detail in Briony brushstrokes at 768?")
    log("  - loop_test / loop_test_3x: does the fish->fish crossfade loop seamlessly?")
    log("")
    log("DONE.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
