#!/usr/bin/env python3
"""
Salish Sea Dreaming — Alternative Programmatic Simulations (Node 3)
====================================================================

"We are the Salish Sea, dreaming itself awake."

Five experiments using pure-Python simulations as depth maps for ControlNet
rendering through Briony's watercolor LoRA. No Blender needed — all simulations
are numpy-based.

Experiments:
  1. Reaction-Diffusion (Gray-Scott) -> ControlNet
     Organic Turing patterns: coral growth, branching, spots/stripes.
     300 frames, loose ControlNet (0.6).

  2. Diffusion-Limited Aggregation (DLA) -> ControlNet
     Branching root/mycelium/coral growth from random walkers.
     200 frames.

  3. Fluid Simulation (Navier-Stokes) -> ControlNet
     2D fluid solver with dye advection — ocean currents, tidal patterns.
     300 frames.

  4. Multi-Layer Resolume Test
     Three separate clips designed for Resolume layering:
     a) Base: slow reaction-diffusion as "underwater coral"
     b) Mid: simple Boids as "waterline transition"
     c) Top: evolving fBM noise as "clouds and mist"
     120 frames each.

  5. Slow-Motion Dissolution (3x)
     Download Boids v2 depth maps from Node 2, triple duration via
     frame repetition + optical flow interpolation.
     2700 frames -> 90 seconds at 30fps.

Target: TELUS Node 3 H200 GPU
Output: /home/jovyan/alt_simulations/output/

Run:
  nohup python3 /home/jovyan/alt_simulations/alt_simulations.py \
    >> /home/jovyan/alt_simulations/progress.log 2>&1 &

Author: Darren Zal + Claude
Date: 2026-04-04
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

ROOT = Path("/home/jovyan/alt_simulations")
OUTPUT_DIR = ROOT / "output"
DEPTH_DIR = ROOT / "depth"
FRAMES_DIR = ROOT / "frames"
LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "stable-diffusion-v1-5/stable-diffusion-v1-5"
CONTROLNET_MODEL = "lllyasviel/control_v11f1p_sd15_depth"
PROGRESS_LOG = ROOT / "progress.log"

# Node 2 for depth map download (Experiment 5)
NODE2_URL = "https://ssd-style-transfer-2-0b50s.paas.ai.telus.com"
NODE2_TOKEN = "15335440de57b5646cd4c25bdf1957d5"
NODE2_DEPTH_PATH = "landscape_dissolution/depth"

SEED = 42
GUIDANCE_SCALE = 7.5
NUM_STEPS = 25
NEGATIVE_PROMPT = (
    "photograph, photorealistic, sharp lines, digital art, 3d render, "
    "harsh shadows, blurry, deformed, ugly, text, watermark, signature, "
    "low quality, jpeg artifacts"
)

DEVICE = "cuda"

# ============================================================================
# SETUP
# ============================================================================

for d in [ROOT, OUTPUT_DIR, DEPTH_DIR, FRAMES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ALT_SIM] %(message)s",
    handlers=[
        logging.FileHandler(str(PROGRESS_LOG)),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ============================================================================
# INSTALL DEPENDENCIES
# ============================================================================

def install_deps():
    log.info("Installing dependencies...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-q",
        "diffusers>=0.32.0", "transformers>=4.40.0", "accelerate", "safetensors",
        "peft", "imageio", "imageio-ffmpeg", "Pillow", "scipy",
        "opencv-python-headless", "torch", "torchvision",
    ])
    log.info("Dependencies installed.")


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def depth_to_rgb(arr_2d):
    """Convert a 2D numpy array to 3-channel RGB image for ControlNet."""
    arr = arr_2d.astype(np.float32)
    if arr.max() > arr.min():
        arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255.0
    arr = arr.astype(np.uint8)
    return np.stack([arr, arr, arr], axis=-1)


def save_depth_frame(arr_2d, path):
    """Save a 2D simulation array as a depth map PNG."""
    from PIL import Image
    rgb = depth_to_rgb(arr_2d)
    Image.fromarray(rgb).save(str(path))


def frames_to_video(frames_dir, output_path, fps=30):
    """Assemble PNG frames into MP4 using ffmpeg."""
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ffmpeg = "ffmpeg"

    frames = sorted(Path(frames_dir).glob("frame_*.png"))
    if not frames:
        log.warning(f"No frames in {frames_dir}")
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
        log.info(f"Video: {output_path.name} ({size_mb:.1f} MB, {fps}fps, {len(frames)} frames)")
    else:
        log.error(f"ERROR encoding {output_path.name}: {result.stderr[-500:]}")


def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=7, sigma=2.0):
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


def load_pipeline():
    """Load SD 1.5 + ControlNet depth + Briony LoRA pipeline."""
    import torch
    from diffusers import (
        StableDiffusionControlNetImg2ImgPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    log.info("Loading ControlNet depth model...")
    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL, torch_dtype=torch.float16
    )

    log.info("Loading SD 1.5 + ControlNet img2img pipeline...")
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet,
        torch_dtype=torch.float16, safety_checker=None,
    ).to(DEVICE)
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LORA_PATH)
    pipe.enable_attention_slicing()
    try:
        pipe.enable_xformers_memory_efficient_attention()
        log.info("xformers enabled")
    except Exception:
        log.info("xformers not available, using standard attention")

    log.info("Pipeline loaded.")
    return pipe


def generate_background(prompt, seed=42):
    """Generate a fixed background image using txt2img."""
    import torch
    from diffusers import StableDiffusionPipeline, UniPCMultistepScheduler
    from PIL import Image

    log.info(f"Generating background: {prompt[:60]}...")
    bg_pipe = StableDiffusionPipeline.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, safety_checker=None,
    ).to(DEVICE)
    bg_pipe.scheduler = UniPCMultistepScheduler.from_config(bg_pipe.scheduler.config)
    bg_pipe.load_lora_weights(LORA_PATH)
    bg_pipe.enable_attention_slicing()

    gen = torch.Generator(DEVICE).manual_seed(seed)
    bg_image = bg_pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=40,
        guidance_scale=7.5,
        generator=gen,
        width=512, height=512,
    ).images[0]

    del bg_pipe
    torch.cuda.empty_cache()
    gc.collect()

    log.info("Background generated.")
    return bg_image


def render_depth_frames(pipe, bg_image, depth_files, output_frames_dir,
                        prompt, cn_scale=0.6, strength=0.55, label="render"):
    """Render depth map frames through ControlNet + LoRA img2img."""
    import torch
    from PIL import Image

    output_frames_dir = Path(output_frames_dir)
    output_frames_dir.mkdir(parents=True, exist_ok=True)

    n_frames = len(depth_files)
    log.info(f"Rendering {n_frames} frames [{label}] (cn_scale={cn_scale}, strength={strength})...")
    timings = []
    rendered = []

    for i, depth_path in enumerate(depth_files):
        out_path = output_frames_dir / f"frame_{i:05d}.png"

        # Resume support
        if out_path.exists():
            img = Image.open(out_path)
            rendered.append(np.array(img))
            if i % 50 == 0:
                log.info(f"  [{label}] Frame {i+1}/{n_frames} -- skipped (exists)")
            continue

        start = time.perf_counter()

        # Load and prepare depth image
        depth_img = Image.open(str(depth_path)).convert("RGB").resize((512, 512))

        gen = torch.Generator(DEVICE).manual_seed(SEED)
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=bg_image,
            control_image=depth_img,
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            strength=strength,
            controlnet_conditioning_scale=cn_scale,
            generator=gen,
        ).images[0]

        result.save(out_path)
        rendered.append(np.array(result))

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        if i % 25 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            log.info(f"  [{label}] Frame {i+1}/{n_frames} -- {elapsed:.2f}s "
                     f"(avg {avg:.2f}s, ETA {remaining/60:.1f}min)")

    if timings:
        total = sum(timings)
        log.info(f"  [{label}] Render done: {len(timings)} new frames in "
                 f"{total/60:.1f}min (avg {total/len(timings):.2f}s/frame)")

    return rendered


def render_with_prompt_schedule(pipe, bg_image, depth_files, output_frames_dir,
                                prompt_schedule, cn_scale=0.6, strength=0.55,
                                label="render"):
    """Render with a per-frame prompt schedule (dict of frame_idx -> prompt)."""
    import torch
    from PIL import Image

    output_frames_dir = Path(output_frames_dir)
    output_frames_dir.mkdir(parents=True, exist_ok=True)

    n_frames = len(depth_files)
    phase_starts = sorted(prompt_schedule.keys())

    def get_prompt(idx):
        prompt = prompt_schedule[phase_starts[0]]
        for start in phase_starts:
            if idx >= start:
                prompt = prompt_schedule[start]
        return prompt

    log.info(f"Rendering {n_frames} frames [{label}] with {len(phase_starts)} prompt phases...")
    timings = []
    rendered = []

    for i, depth_path in enumerate(depth_files):
        out_path = output_frames_dir / f"frame_{i:05d}.png"

        if out_path.exists():
            img = Image.open(out_path)
            rendered.append(np.array(img))
            if i % 50 == 0:
                log.info(f"  [{label}] Frame {i+1}/{n_frames} -- skipped (exists)")
            continue

        start = time.perf_counter()
        depth_img = Image.open(str(depth_path)).convert("RGB").resize((512, 512))
        prompt = get_prompt(i)

        gen = torch.Generator(DEVICE).manual_seed(SEED)
        result = pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=bg_image,
            control_image=depth_img,
            num_inference_steps=NUM_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            strength=strength,
            controlnet_conditioning_scale=cn_scale,
            generator=gen,
        ).images[0]

        result.save(out_path)
        rendered.append(np.array(result))

        elapsed = time.perf_counter() - start
        timings.append(elapsed)

        if i % 25 == 0 or i == n_frames - 1:
            avg = sum(timings) / len(timings)
            remaining = avg * (n_frames - i - 1)
            log.info(f"  [{label}] Frame {i+1}/{n_frames} -- {elapsed:.2f}s "
                     f"(avg {avg:.2f}s, ETA {remaining/60:.1f}min)")

    if timings:
        total = sum(timings)
        log.info(f"  [{label}] Render done: {len(timings)} new frames in "
                 f"{total/60:.1f}min (avg {total/len(timings):.2f}s/frame)")

    return rendered


def smooth_and_assemble(rendered_frames, smooth_dir, video_path, fps=30,
                        window=7, sigma=2.0, label="output"):
    """Temporal smooth + assemble to video."""
    from PIL import Image

    smooth_dir = Path(smooth_dir)
    smooth_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Temporal smoothing [{label}] ({len(rendered_frames)} frames, "
             f"window={window}, sigma={sigma})...")

    frames_np = np.array(rendered_frames)
    smoothed = temporal_smooth(frames_np, window=window, sigma=sigma)

    for i, frame in enumerate(smoothed):
        Image.fromarray(frame).save(smooth_dir / f"frame_{i:05d}.png")

    log.info(f"  [{label}] Smoothing done: {len(smoothed)} frames")
    frames_to_video(smooth_dir, video_path, fps)


# ============================================================================
# EXPERIMENT 1: Reaction-Diffusion (Gray-Scott)
# ============================================================================

def simulate_reaction_diffusion(n_frames=300, size=512, steps_per_frame=100):
    """
    Gray-Scott reaction-diffusion model.
    Creates organic Turing patterns: coral growth, branching, spots/stripes.

    Parameters tuned for coral/organic growth (f=0.055, k=0.062).
    """
    log.info("=" * 60)
    log.info("EXPERIMENT 1: Reaction-Diffusion (Gray-Scott)")
    log.info(f"  {n_frames} frames, {steps_per_frame} steps/frame, {size}x{size}")
    log.info("=" * 60)

    depth_dir = DEPTH_DIR / "reaction_diffusion"
    depth_dir.mkdir(parents=True, exist_ok=True)

    # Check if already simulated
    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= n_frames:
        log.info(f"  Already have {len(existing)} depth frames, skipping simulation")
        return sorted(depth_dir.glob("frame_*.png"))[:n_frames]

    from scipy.signal import convolve2d

    # Gray-Scott parameters for coral/organic growth
    f = 0.055   # feed rate
    k = 0.062   # kill rate
    Du = 0.16   # diffusion rate U
    Dv = 0.08   # diffusion rate V
    dt = 1.0

    # Initialize
    U = np.ones((size, size), dtype=np.float64)
    V = np.zeros((size, size), dtype=np.float64)

    # Seed with several spots at different locations for organic growth
    np.random.seed(SEED)
    n_seeds = 12
    for _ in range(n_seeds):
        cx = np.random.randint(size // 4, 3 * size // 4)
        cy = np.random.randint(size // 4, 3 * size // 4)
        r = np.random.randint(8, 20)
        y, x = np.ogrid[-cx:size-cx, -cy:size-cy]
        mask = x*x + y*y <= r*r
        U[mask] = 0.5 + np.random.random() * 0.1
        V[mask] = 0.25 + np.random.random() * 0.1

    # Laplacian kernel
    laplacian = np.array([[0.05, 0.2, 0.05],
                          [0.2, -1.0, 0.2],
                          [0.05, 0.2, 0.05]])

    log.info("  Running Gray-Scott simulation...")
    start_time = time.time()

    saved = 0
    for step in range(n_frames * steps_per_frame):
        # Compute Laplacians
        Lu = convolve2d(U, laplacian, mode='same', boundary='wrap')
        Lv = convolve2d(V, laplacian, mode='same', boundary='wrap')

        # Gray-Scott update
        uvv = U * V * V
        U += dt * (Du * Lu - uvv + f * (1 - U))
        V += dt * (Dv * Lv + uvv - (f + k) * V)

        # Clamp
        U = np.clip(U, 0, 1)
        V = np.clip(V, 0, 1)

        # Save frame
        if step % steps_per_frame == 0:
            frame_path = depth_dir / f"frame_{saved:05d}.png"
            if not frame_path.exists():
                save_depth_frame(V, frame_path)
            saved += 1
            if saved % 50 == 0:
                elapsed = time.time() - start_time
                log.info(f"  Frame {saved}/{n_frames} ({elapsed:.1f}s elapsed)")

    elapsed = time.time() - start_time
    log.info(f"  Simulation done: {saved} frames in {elapsed:.1f}s")

    return sorted(depth_dir.glob("frame_*.png"))[:n_frames]


def run_experiment_1(pipe):
    """Reaction-Diffusion -> ControlNet rendering."""
    from PIL import Image

    # Generate depth maps
    depth_files = simulate_reaction_diffusion(n_frames=300)

    # Generate background
    bg_prompt = (
        "brionypenn watercolor of underwater tidepool, dark water, "
        "soft light filtering through, Pacific Northwest intertidal"
    )
    bg_path = OUTPUT_DIR / "bg_reaction_diffusion.png"
    if bg_path.exists():
        bg_image = Image.open(bg_path).convert("RGB")
        log.info("Background loaded from cache.")
    else:
        bg_image = generate_background(bg_prompt, seed=SEED)
        bg_image.save(bg_path)

    # Render
    prompt = (
        "brionypenn watercolor of coral reef growing, organic branching patterns, "
        "natural history illustration, Pacific Northwest intertidal"
    )
    frames_dir = FRAMES_DIR / "reaction_diffusion"
    rendered = render_depth_frames(
        pipe, bg_image, depth_files, frames_dir,
        prompt=prompt, cn_scale=0.6, strength=0.55,
        label="reaction_diffusion",
    )

    # Smooth + assemble
    smooth_dir = FRAMES_DIR / "reaction_diffusion_smooth"
    video_path = OUTPUT_DIR / "reaction_diffusion_30fps.mp4"
    smooth_and_assemble(rendered, smooth_dir, video_path, fps=30,
                        label="reaction_diffusion")

    return True


# ============================================================================
# EXPERIMENT 2: Diffusion-Limited Aggregation (DLA)
# ============================================================================

def simulate_dla(n_frames=200, size=512, particles_per_frame=500):
    """
    Diffusion-Limited Aggregation.
    Random walkers stick when they touch existing structure.
    Creates branching root/mycelium/coral growth patterns.
    """
    log.info("=" * 60)
    log.info("EXPERIMENT 2: Diffusion-Limited Aggregation (DLA)")
    log.info(f"  {n_frames} frames, {particles_per_frame} particles/frame, {size}x{size}")
    log.info("=" * 60)

    depth_dir = DEPTH_DIR / "dla"
    depth_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= n_frames:
        log.info(f"  Already have {len(existing)} depth frames, skipping simulation")
        return sorted(depth_dir.glob("frame_*.png"))[:n_frames]

    np.random.seed(SEED)

    # Grid: 0 = empty, >0 = occupied (value = time of attachment for depth)
    grid = np.zeros((size, size), dtype=np.float32)

    # Seed: small cluster at center
    center = size // 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx*dx + dy*dy <= 9:
                grid[center + dx, center + dy] = 1.0

    # 4-connected neighbors
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]

    log.info("  Running DLA simulation...")
    start_time = time.time()

    max_radius = 10  # Track growth frontier

    for frame_idx in range(n_frames):
        particles_added = 0

        for _ in range(particles_per_frame):
            # Spawn walker on circle around current structure
            spawn_r = min(max_radius + 30, size // 2 - 5)
            angle = np.random.random() * 2 * np.pi
            x = int(center + spawn_r * np.cos(angle))
            y = int(center + spawn_r * np.sin(angle))
            x = np.clip(x, 1, size - 2)
            y = np.clip(y, 1, size - 2)

            kill_r = spawn_r + 50
            max_steps = 5000

            for step in range(max_steps):
                # Random walk
                dx, dy = directions[np.random.randint(len(directions))]
                x = np.clip(x + dx, 1, size - 2)
                y = np.clip(y + dy, 1, size - 2)

                # Check if too far away — kill
                dist = math.sqrt((x - center)**2 + (y - center)**2)
                if dist > kill_r:
                    break

                # Check if adjacent to existing structure
                stuck = False
                for ddx, ddy in directions:
                    nx, ny = x + ddx, y + ddy
                    if 0 <= nx < size and 0 <= ny < size and grid[nx, ny] > 0:
                        stuck = True
                        break

                if stuck:
                    # Depth = distance from center (normalized later)
                    grid[x, y] = dist
                    particles_added += 1
                    max_radius = max(max_radius, dist)
                    break

        # Save frame
        frame_path = depth_dir / f"frame_{frame_idx:05d}.png"
        if not frame_path.exists():
            # Use distance-from-center as depth (farther = brighter)
            depth = grid.copy()
            if depth.max() > 0:
                depth = depth / depth.max() * 255.0
            save_depth_frame(depth, frame_path)

        if frame_idx % 25 == 0:
            elapsed = time.time() - start_time
            total_particles = np.sum(grid > 0)
            log.info(f"  Frame {frame_idx+1}/{n_frames} "
                     f"({total_particles:.0f} particles, radius={max_radius:.0f}, "
                     f"{elapsed:.1f}s)")

    elapsed = time.time() - start_time
    log.info(f"  Simulation done: {n_frames} frames in {elapsed:.1f}s")

    return sorted(depth_dir.glob("frame_*.png"))[:n_frames]


def run_experiment_2(pipe):
    """DLA -> ControlNet rendering."""
    from PIL import Image

    depth_files = simulate_dla(n_frames=200)

    bg_prompt = (
        "brionypenn watercolor of dark forest floor, rich soil, "
        "Pacific Northwest old growth, soft diffused light"
    )
    bg_path = OUTPUT_DIR / "bg_dla.png"
    if bg_path.exists():
        bg_image = Image.open(bg_path).convert("RGB")
        log.info("Background loaded from cache.")
    else:
        bg_image = generate_background(bg_prompt, seed=SEED + 1)
        bg_image.save(bg_path)

    prompt = (
        "brionypenn watercolor of tree roots spreading through dark soil, "
        "mycelium network, branching life, natural history illustration"
    )
    frames_dir = FRAMES_DIR / "dla"
    rendered = render_depth_frames(
        pipe, bg_image, depth_files, frames_dir,
        prompt=prompt, cn_scale=0.65, strength=0.55,
        label="dla",
    )

    smooth_dir = FRAMES_DIR / "dla_smooth"
    video_path = OUTPUT_DIR / "dla_growth_30fps.mp4"
    smooth_and_assemble(rendered, smooth_dir, video_path, fps=30, label="dla")

    return True


# ============================================================================
# EXPERIMENT 3: Fluid Simulation (Navier-Stokes, Jos Stam style)
# ============================================================================

def simulate_fluid(n_frames=300, size=512, steps_per_frame=5):
    """
    2D incompressible fluid simulation (Jos Stam, "Stable Fluids" 1999).
    Velocity field + dye advection.
    Creates flowing, organic patterns — ocean currents, tidal patterns.
    """
    log.info("=" * 60)
    log.info("EXPERIMENT 3: Fluid Simulation (Navier-Stokes)")
    log.info(f"  {n_frames} frames, {steps_per_frame} steps/frame, {size}x{size}")
    log.info("=" * 60)

    depth_dir = DEPTH_DIR / "fluid"
    depth_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= n_frames:
        log.info(f"  Already have {len(existing)} depth frames, skipping simulation")
        return sorted(depth_dir.glob("frame_*.png"))[:n_frames]

    N = size
    dt = 0.1
    visc = 0.0001
    diff = 0.00001

    def set_bnd(b, x, N):
        """Boundary conditions (zero-flux walls)."""
        x[0, :] = -x[1, :] if b == 1 else x[1, :]
        x[N-1, :] = -x[N-2, :] if b == 1 else x[N-2, :]
        x[:, 0] = -x[:, 1] if b == 2 else x[:, 1]
        x[:, N-1] = -x[:, N-2] if b == 2 else x[:, N-2]
        x[0, 0] = 0.5 * (x[1, 0] + x[0, 1])
        x[0, N-1] = 0.5 * (x[1, N-1] + x[0, N-2])
        x[N-1, 0] = 0.5 * (x[N-2, 0] + x[N-1, 1])
        x[N-1, N-1] = 0.5 * (x[N-2, N-1] + x[N-1, N-2])

    def diffuse(b, x, x0, diff_rate, dt_val, N, iters=4):
        a = dt_val * diff_rate * N * N
        for _ in range(iters):
            x[1:-1, 1:-1] = (x0[1:-1, 1:-1] + a * (
                x[:-2, 1:-1] + x[2:, 1:-1] +
                x[1:-1, :-2] + x[1:-1, 2:]
            )) / (1 + 4 * a)
            set_bnd(b, x, N)

    def advect(b, d, d0, u, v, dt_val, N):
        dt0 = dt_val * N
        for i in range(1, N-1):
            for j in range(1, N-1):
                x = i - dt0 * u[i, j]
                y = j - dt0 * v[i, j]
                x = max(0.5, min(N - 1.5, x))
                y = max(0.5, min(N - 1.5, y))
                i0 = int(x); i1 = i0 + 1
                j0 = int(y); j1 = j0 + 1
                s1 = x - i0; s0 = 1 - s1
                t1 = y - j0; t0 = 1 - t1
                d[i, j] = (s0 * (t0 * d0[i0, j0] + t1 * d0[i0, j1]) +
                           s1 * (t0 * d0[i1, j0] + t1 * d0[i1, j1]))
        set_bnd(b, d, N)

    def project(u, v, p, div, N, iters=4):
        h = 1.0 / N
        div[1:-1, 1:-1] = -0.5 * h * (
            u[2:, 1:-1] - u[:-2, 1:-1] +
            v[1:-1, 2:] - v[1:-1, :-2]
        )
        p[:] = 0
        set_bnd(0, div, N)
        set_bnd(0, p, N)
        for _ in range(iters):
            p[1:-1, 1:-1] = (div[1:-1, 1:-1] +
                p[:-2, 1:-1] + p[2:, 1:-1] +
                p[1:-1, :-2] + p[1:-1, 2:]) / 4
            set_bnd(0, p, N)
        u[1:-1, 1:-1] -= 0.5 * (p[2:, 1:-1] - p[:-2, 1:-1]) / h
        v[1:-1, 1:-1] -= 0.5 * (p[1:-1, 2:] - p[1:-1, :-2]) / h
        set_bnd(1, u, N)
        set_bnd(2, v, N)

    # Use a smaller sim grid for speed, then upscale depth maps
    SIM_N = 128  # Simulate at 128x128, upscale to 512x512

    u = np.zeros((SIM_N, SIM_N), dtype=np.float64)
    v = np.zeros((SIM_N, SIM_N), dtype=np.float64)
    u_prev = np.zeros_like(u)
    v_prev = np.zeros_like(v)
    dens = np.zeros((SIM_N, SIM_N), dtype=np.float64)
    dens_prev = np.zeros_like(dens)
    p = np.zeros_like(u)
    div = np.zeros_like(u)

    np.random.seed(SEED)

    log.info("  Running fluid simulation...")
    start_time = time.time()

    saved = 0
    total_steps = n_frames * steps_per_frame

    for step in range(total_steps):
        # Add forces: rotating vortices that slowly move
        t = step * dt
        cx1 = SIM_N // 2 + int(15 * np.sin(t * 0.05))
        cy1 = SIM_N // 2 + int(15 * np.cos(t * 0.05))

        # Central vortex
        for di in range(-5, 6):
            for dj in range(-5, 6):
                ii = np.clip(cx1 + di, 1, SIM_N - 2)
                jj = np.clip(cy1 + dj, 1, SIM_N - 2)
                r = max(1, math.sqrt(di*di + dj*dj))
                strength = 20.0 / r
                u_prev[ii, jj] += strength * (-dj / r) * dt
                v_prev[ii, jj] += strength * (di / r) * dt
                dens_prev[ii, jj] += 5.0 * np.exp(-r / 3) * dt

        # Secondary vortex (opposite rotation)
        cx2 = SIM_N // 2 + int(20 * np.sin(t * 0.03 + 2.0))
        cy2 = SIM_N // 2 + int(20 * np.cos(t * 0.03 + 2.0))
        for di in range(-4, 5):
            for dj in range(-4, 5):
                ii = np.clip(cx2 + di, 1, SIM_N - 2)
                jj = np.clip(cy2 + dj, 1, SIM_N - 2)
                r = max(1, math.sqrt(di*di + dj*dj))
                strength = 12.0 / r
                u_prev[ii, jj] += strength * (dj / r) * dt
                v_prev[ii, jj] += strength * (-di / r) * dt

        # Velocity step
        diffuse(1, u, u_prev, visc, dt, SIM_N)
        diffuse(2, v, v_prev, visc, dt, SIM_N)
        project(u, v, p, div, SIM_N)
        u_prev[:] = u
        v_prev[:] = v
        advect(1, u, u_prev, u_prev, v_prev, dt, SIM_N)
        advect(2, v, v_prev, u_prev, v_prev, dt, SIM_N)
        project(u, v, p, div, SIM_N)

        # Density step
        diffuse(0, dens, dens_prev, diff, dt, SIM_N)
        dens_prev[:] = dens
        advect(0, dens, dens_prev, u, v, dt, SIM_N)

        # Slight decay
        dens *= 0.998

        # Save frame
        if step % steps_per_frame == 0:
            frame_path = depth_dir / f"frame_{saved:05d}.png"
            if not frame_path.exists():
                # Combine velocity magnitude and density for depth
                vel_mag = np.sqrt(u * u + v * v)
                combined = 0.5 * dens + 0.5 * vel_mag
                # Upscale to 512x512
                from PIL import Image as PILImage
                combined_norm = combined.astype(np.float32)
                if combined_norm.max() > combined_norm.min():
                    combined_norm = ((combined_norm - combined_norm.min()) /
                                     (combined_norm.max() - combined_norm.min()) * 255)
                combined_uint8 = combined_norm.astype(np.uint8)
                rgb = np.stack([combined_uint8]*3, axis=-1)
                img = PILImage.fromarray(rgb).resize((512, 512), PILImage.LANCZOS)
                img.save(str(frame_path))
            saved += 1
            if saved % 50 == 0:
                elapsed = time.time() - start_time
                log.info(f"  Frame {saved}/{n_frames} ({elapsed:.1f}s)")

        # Reset prev (forces applied each step)
        u_prev[:] = 0
        v_prev[:] = 0
        dens_prev[:] = 0

    elapsed = time.time() - start_time
    log.info(f"  Simulation done: {saved} frames in {elapsed:.1f}s")

    return sorted(depth_dir.glob("frame_*.png"))[:n_frames]


def run_experiment_3(pipe):
    """Fluid simulation -> ControlNet rendering."""
    from PIL import Image

    depth_files = simulate_fluid(n_frames=300)

    bg_prompt = (
        "brionypenn watercolor of ocean surface, Pacific Northwest coast, "
        "grey water, tidal currents, atmospheric mist"
    )
    bg_path = OUTPUT_DIR / "bg_fluid.png"
    if bg_path.exists():
        bg_image = Image.open(bg_path).convert("RGB")
        log.info("Background loaded from cache.")
    else:
        bg_image = generate_background(bg_prompt, seed=SEED + 2)
        bg_image.save(bg_path)

    prompt = (
        "brionypenn watercolor of ocean currents, flowing water, "
        "tidal patterns, Pacific Northwest coast, natural history illustration"
    )
    frames_dir = FRAMES_DIR / "fluid"
    rendered = render_depth_frames(
        pipe, bg_image, depth_files, frames_dir,
        prompt=prompt, cn_scale=0.6, strength=0.55,
        label="fluid",
    )

    smooth_dir = FRAMES_DIR / "fluid_smooth"
    video_path = OUTPUT_DIR / "fluid_sim_30fps.mp4"
    smooth_and_assemble(rendered, smooth_dir, video_path, fps=30, label="fluid")

    return True


# ============================================================================
# EXPERIMENT 4: Multi-Layer Resolume Test
# ============================================================================

def simulate_boids_simple(n_frames=120, size=512, n_boids=200):
    """
    Simple 2D Boids for the mid-layer.
    Returns depth maps based on boid density.
    """
    log.info("  Simulating simple Boids (mid layer)...")

    depth_dir = DEPTH_DIR / "boids_simple"
    depth_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= n_frames:
        log.info(f"  Already have {len(existing)} boids frames")
        return sorted(depth_dir.glob("frame_*.png"))[:n_frames]

    np.random.seed(SEED + 10)

    # Initialize boids
    pos = np.random.rand(n_boids, 2) * size
    vel = (np.random.rand(n_boids, 2) - 0.5) * 4

    max_speed = 4.0
    sep_dist = 20.0
    align_dist = 50.0
    cohesion_dist = 80.0
    sep_weight = 1.5
    align_weight = 1.0
    cohesion_weight = 1.0

    for frame_idx in range(n_frames):
        # Boids rules
        for i in range(n_boids):
            separation = np.zeros(2)
            alignment = np.zeros(2)
            cohesion = np.zeros(2)
            n_sep = 0
            n_align = 0
            n_coh = 0

            for j in range(n_boids):
                if i == j:
                    continue
                diff = pos[i] - pos[j]
                # Wrap distance
                diff = (diff + size/2) % size - size/2
                dist = np.linalg.norm(diff)

                if dist < sep_dist and dist > 0:
                    separation += diff / dist
                    n_sep += 1
                if dist < align_dist:
                    alignment += vel[j]
                    n_align += 1
                if dist < cohesion_dist:
                    cohesion += pos[j]
                    n_coh += 1

            if n_sep > 0:
                separation /= n_sep
            if n_align > 0:
                alignment /= n_align
                alignment -= vel[i]
            if n_coh > 0:
                cohesion = cohesion / n_coh - pos[i]
                cohesion = (cohesion + size/2) % size - size/2

            vel[i] += (sep_weight * separation +
                       align_weight * alignment +
                       cohesion_weight * cohesion) * 0.05

            # Limit speed
            speed = np.linalg.norm(vel[i])
            if speed > max_speed:
                vel[i] = vel[i] / speed * max_speed

        # Update positions (wrap)
        pos += vel
        pos = pos % size

        # Create depth map from boid density
        frame_path = depth_dir / f"frame_{frame_idx:05d}.png"
        if not frame_path.exists():
            density = np.zeros((size, size), dtype=np.float32)
            sigma = 15.0
            # Add Gaussian blobs for each boid
            yy, xx = np.mgrid[0:size, 0:size]
            for k in range(n_boids):
                bx, by = pos[k]
                # Wrapped distance
                dx = np.minimum(np.abs(xx - bx), size - np.abs(xx - bx))
                dy = np.minimum(np.abs(yy - by), size - np.abs(yy - by))
                dist_sq = dx**2 + dy**2
                density += np.exp(-dist_sq / (2 * sigma**2))

            save_depth_frame(density, frame_path)

        if frame_idx % 30 == 0:
            log.info(f"    Boids frame {frame_idx+1}/{n_frames}")

    return sorted(depth_dir.glob("frame_*.png"))[:n_frames]


def simulate_fbm_noise(n_frames=120, size=512):
    """
    Fractal Brownian Motion (fBM) noise evolving slowly.
    Creates cloud/mist patterns for the top atmospheric layer.
    """
    log.info("  Simulating fBM noise (top layer)...")

    depth_dir = DEPTH_DIR / "fbm"
    depth_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= n_frames:
        log.info(f"  Already have {len(existing)} fBM frames")
        return sorted(depth_dir.glob("frame_*.png"))[:n_frames]

    np.random.seed(SEED + 20)

    def fbm_2d(size, octaves=6, persistence=0.5, lacunarity=2.0, offset_x=0, offset_y=0):
        """Generate 2D fractional Brownian Motion noise."""
        result = np.zeros((size, size), dtype=np.float64)
        amplitude = 1.0
        frequency = 1.0

        for _ in range(octaves):
            # Generate noise at this frequency using interpolated random values
            grid_size = max(2, int(size / (frequency * 4)))
            noise = np.random.randn(grid_size, grid_size)

            # Interpolate to full size
            from scipy.ndimage import zoom
            scale = size / grid_size
            layer = zoom(noise, scale, order=3)[:size, :size]

            # Apply offset for animation
            shift_x = int(offset_x * frequency) % size
            shift_y = int(offset_y * frequency) % size
            layer = np.roll(np.roll(layer, shift_x, axis=0), shift_y, axis=1)

            result += amplitude * layer
            amplitude *= persistence
            frequency *= lacunarity

        return result

    for frame_idx in range(n_frames):
        frame_path = depth_dir / f"frame_{frame_idx:05d}.png"
        if not frame_path.exists():
            # Slowly evolving offset
            t = frame_idx * 0.5  # Very slow evolution
            noise = fbm_2d(size, octaves=6, persistence=0.55,
                          offset_x=t, offset_y=t * 0.7)
            # Normalize
            noise = (noise - noise.min()) / (noise.max() - noise.min())
            save_depth_frame(noise * 255, frame_path)

        if frame_idx % 30 == 0:
            log.info(f"    fBM frame {frame_idx+1}/{n_frames}")

    return sorted(depth_dir.glob("frame_*.png"))[:n_frames]


def run_experiment_4(pipe):
    """Multi-layer Resolume test: 3 clips designed for layering."""
    from PIL import Image

    log.info("=" * 60)
    log.info("EXPERIMENT 4: Multi-Layer Resolume Test")
    log.info("  Base: slow reaction-diffusion (underwater coral)")
    log.info("  Mid: Boids (waterline transition)")
    log.info("  Top: fBM noise (clouds and mist)")
    log.info("  Recommended blend modes: Base=Normal 100%, Mid=Alpha 100%, Top=Screen 40%")
    log.info("=" * 60)

    # ---- Layer 1: Base (slow reaction-diffusion) ----
    log.info("\n--- Layer 1: Base (slow underwater coral) ---")
    rd_depth = simulate_reaction_diffusion(n_frames=120, steps_per_frame=500)
    # Use only first 120
    rd_depth = rd_depth[:120]

    bg_prompt_base = (
        "brionypenn watercolor of deep underwater coral garden, "
        "dark blue Pacific Northwest waters, bioluminescent glow"
    )
    bg_path_base = OUTPUT_DIR / "bg_layer_base.png"
    if bg_path_base.exists():
        bg_base = Image.open(bg_path_base).convert("RGB")
    else:
        bg_base = generate_background(bg_prompt_base, seed=SEED + 3)
        bg_base.save(bg_path_base)

    prompt_base = (
        "brionypenn watercolor of underwater coral growth, "
        "deep ocean, bioluminescent patterns, Pacific Northwest seabed"
    )
    frames_base = FRAMES_DIR / "layer_base"
    rendered_base = render_depth_frames(
        pipe, bg_base, rd_depth, frames_base,
        prompt=prompt_base, cn_scale=0.55, strength=0.5,
        label="layer_base",
    )
    smooth_dir_base = FRAMES_DIR / "layer_base_smooth"
    video_base = OUTPUT_DIR / "layer_base_underwater.mp4"
    smooth_and_assemble(rendered_base, smooth_dir_base, video_base, fps=30,
                        label="layer_base")

    # ---- Layer 2: Mid (Boids) ----
    log.info("\n--- Layer 2: Mid (waterline transition) ---")
    boids_depth = simulate_boids_simple(n_frames=120)

    bg_prompt_mid = (
        "brionypenn watercolor of the waterline, where ocean meets sky, "
        "Pacific Northwest coast, grey light"
    )
    bg_path_mid = OUTPUT_DIR / "bg_layer_mid.png"
    if bg_path_mid.exists():
        bg_mid = Image.open(bg_path_mid).convert("RGB")
    else:
        bg_mid = generate_background(bg_prompt_mid, seed=SEED + 4)
        bg_mid.save(bg_path_mid)

    prompt_mid = (
        "brionypenn watercolor of fish schooling at the waterline, "
        "transition between ocean and sky, Pacific Northwest coast"
    )
    frames_mid = FRAMES_DIR / "layer_mid"
    rendered_mid = render_depth_frames(
        pipe, bg_mid, boids_depth, frames_mid,
        prompt=prompt_mid, cn_scale=0.6, strength=0.55,
        label="layer_mid",
    )
    smooth_dir_mid = FRAMES_DIR / "layer_mid_smooth"
    video_mid = OUTPUT_DIR / "layer_mid_transition.mp4"
    smooth_and_assemble(rendered_mid, smooth_dir_mid, video_mid, fps=30,
                        label="layer_mid")

    # ---- Layer 3: Top (fBM atmospheric) ----
    log.info("\n--- Layer 3: Top (atmospheric clouds/mist) ---")
    fbm_depth = simulate_fbm_noise(n_frames=120)

    bg_prompt_top = (
        "brionypenn watercolor of sky over the Salish Sea, "
        "mist and clouds, soft grey light, atmospheric"
    )
    bg_path_top = OUTPUT_DIR / "bg_layer_top.png"
    if bg_path_top.exists():
        bg_top = Image.open(bg_path_top).convert("RGB")
    else:
        bg_top = generate_background(bg_prompt_top, seed=SEED + 5)
        bg_top.save(bg_path_top)

    prompt_top = (
        "brionypenn watercolor of clouds and mist over the Salish Sea, "
        "atmospheric sky, Pacific Northwest coast, soft ethereal light"
    )
    frames_top = FRAMES_DIR / "layer_top"
    rendered_top = render_depth_frames(
        pipe, bg_top, fbm_depth, frames_top,
        prompt=prompt_top, cn_scale=0.5, strength=0.5,
        label="layer_top",
    )
    smooth_dir_top = FRAMES_DIR / "layer_top_smooth"
    video_top = OUTPUT_DIR / "layer_top_atmospheric.mp4"
    smooth_and_assemble(rendered_top, smooth_dir_top, video_top, fps=30,
                        label="layer_top")

    # Write Resolume notes
    notes_path = OUTPUT_DIR / "resolume_layer_notes.txt"
    with open(notes_path, "w") as f:
        f.write("RESOLUME LAYER SETUP — Salish Sea Dreaming\n")
        f.write("=" * 50 + "\n\n")
        f.write("Layer 1 (Base): layer_base_underwater.mp4\n")
        f.write("  Blend: Normal, Opacity: 100%\n")
        f.write("  Content: Slow underwater coral growth (reaction-diffusion)\n")
        f.write("  Speed: Slowest — save every 500 sim steps\n\n")
        f.write("Layer 2 (Mid): layer_mid_transition.mp4\n")
        f.write("  Blend: Alpha (or Add), Opacity: 100%\n")
        f.write("  Content: Boids schooling at the waterline\n")
        f.write("  Speed: Medium — natural boid rhythm\n\n")
        f.write("Layer 3 (Top): layer_top_atmospheric.mp4\n")
        f.write("  Blend: Screen, Opacity: 40%\n")
        f.write("  Content: Evolving clouds/mist (fBM noise)\n")
        f.write("  Speed: Slowest — barely perceptible drift\n\n")
        f.write("All clips: 512x512, 120 frames, 30fps (4 seconds per loop).\n")
        f.write("Loop all clips. Speed offsets will create evolving composition.\n")
        f.write("Consider: different loop speeds per layer for emergent variation.\n")

    log.info(f"Resolume notes saved: {notes_path}")
    return True


# ============================================================================
# EXPERIMENT 5: Slow-Motion Dissolution (3x duration)
# ============================================================================

def download_node2_depth_maps():
    """Download Boids v2 depth maps from Node 2."""
    import requests
    import base64

    depth_dir = DEPTH_DIR / "node2_boids"
    depth_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(depth_dir.glob("frame_*.png"))
    if len(existing) >= 900:
        log.info(f"  Already have {len(existing)} depth maps from Node 2")
        return sorted(depth_dir.glob("frame_*.png"))

    headers = {"Authorization": f"token {NODE2_TOKEN}"}

    log.info("  Listing depth maps on Node 2...")
    try:
        r = requests.get(
            f"{NODE2_URL}/api/contents/{NODE2_DEPTH_PATH}",
            headers=headers, timeout=30,
        )
        if r.status_code != 200:
            log.error(f"Cannot list Node 2 depth dir: {r.status_code}")
            return []

        items = r.json().get("content", [])
        png_files = sorted([
            item["name"] for item in items
            if item["name"].startswith("frame_") and item["name"].endswith(".png")
        ])
        log.info(f"  Found {len(png_files)} depth maps on Node 2")
    except Exception as e:
        log.error(f"Cannot connect to Node 2: {e}")
        return []

    downloaded = 0
    for filename in png_files:
        out_path = depth_dir / filename
        if out_path.exists():
            continue

        try:
            r = requests.get(
                f"{NODE2_URL}/api/contents/{NODE2_DEPTH_PATH}/{filename}",
                headers=headers, params={"content": "1"}, timeout=60,
            )
            if r.status_code != 200:
                continue

            data = r.json()
            content = data.get("content", "")
            fmt = data.get("format", "")

            if fmt == "base64":
                img_bytes = base64.b64decode(content)
            else:
                img_bytes = content.encode("latin-1")

            with open(out_path, "wb") as f:
                f.write(img_bytes)

            downloaded += 1
            if downloaded % 100 == 0:
                log.info(f"    Downloaded {downloaded}...")
        except Exception as e:
            log.warning(f"    Error on {filename}: {e}")

    final = sorted(depth_dir.glob("frame_*.png"))
    log.info(f"  Download complete: {downloaded} new, {len(final)} total")
    return final


def run_experiment_5(pipe):
    """
    Slow-motion dissolution: triple the duration.
    Each depth map used 3 times with optical flow interpolation between repeats.
    """
    import cv2
    from PIL import Image

    log.info("=" * 60)
    log.info("EXPERIMENT 5: Slow-Motion Dissolution (3x duration)")
    log.info("  Download 900 depth maps from Node 2")
    log.info("  Triple -> 2700 frames via frame repeat + flow interpolation")
    log.info("  Target: 90 seconds at 30fps (meditative pace)")
    log.info("=" * 60)

    # Download depth maps from Node 2
    depth_files = download_node2_depth_maps()
    if len(depth_files) < 100:
        log.error("Not enough depth maps from Node 2, skipping experiment 5")
        return False

    # Create tripled depth sequence with interpolation
    log.info(f"  Creating 3x slow-motion depth sequence from {len(depth_files)} frames...")
    slow_depth_dir = DEPTH_DIR / "slow_motion"
    slow_depth_dir.mkdir(parents=True, exist_ok=True)

    n_original = len(depth_files)
    n_output = n_original * 3  # 2700 frames target

    existing = sorted(slow_depth_dir.glob("frame_*.png"))
    if len(existing) >= n_output:
        log.info(f"  Already have {len(existing)} slow-motion depth frames")
    else:
        log.info("  Generating interpolated slow-motion depth maps...")

        for i in range(n_original):
            # Load current and next frame
            curr = cv2.imread(str(depth_files[i]), cv2.IMREAD_GRAYSCALE)
            if curr is None:
                continue

            if i < n_original - 1:
                next_frame = cv2.imread(str(depth_files[i + 1]), cv2.IMREAD_GRAYSCALE)
                if next_frame is None:
                    next_frame = curr
            else:
                next_frame = curr

            # Ensure 512x512
            if curr.shape != (512, 512):
                curr = cv2.resize(curr, (512, 512))
            if next_frame.shape != (512, 512):
                next_frame = cv2.resize(next_frame, (512, 512))

            # Frame 1: original
            out_idx = i * 3
            path1 = slow_depth_dir / f"frame_{out_idx:05d}.png"
            if not path1.exists():
                cv2.imwrite(str(path1), np.stack([curr]*3, axis=-1))

            # Frame 2: 1/3 interpolation toward next
            path2 = slow_depth_dir / f"frame_{out_idx+1:05d}.png"
            if not path2.exists():
                interp1 = (curr.astype(np.float32) * 0.667 +
                          next_frame.astype(np.float32) * 0.333).astype(np.uint8)
                cv2.imwrite(str(path2), np.stack([interp1]*3, axis=-1))

            # Frame 3: 2/3 interpolation toward next
            path3 = slow_depth_dir / f"frame_{out_idx+2:05d}.png"
            if not path3.exists():
                interp2 = (curr.astype(np.float32) * 0.333 +
                          next_frame.astype(np.float32) * 0.667).astype(np.uint8)
                cv2.imwrite(str(path3), np.stack([interp2]*3, axis=-1))

            if i % 100 == 0:
                log.info(f"    Interpolation: {i+1}/{n_original}")

    slow_depth_files = sorted(slow_depth_dir.glob("frame_*.png"))
    log.info(f"  Slow-motion depth frames: {len(slow_depth_files)}")

    # Generate background
    bg_prompt = (
        "brionypenn watercolor of Pacific Northwest coast, "
        "ocean below meeting grey sky above, cedar trees along shoreline, "
        "the waterline dividing two worlds, soft atmospheric muted tones"
    )
    bg_path = OUTPUT_DIR / "bg_slow_motion.png"
    if bg_path.exists():
        bg_image = Image.open(bg_path).convert("RGB")
    else:
        bg_image = generate_background(bg_prompt, seed=SEED + 6)
        bg_image.save(bg_path)

    # 6-phase prompts scaled to 2700 frames (each phase = 450 frames)
    prompt_schedule = {
        0: (
            "brionypenn watercolor of silver herring gathering in cold dark water "
            "below the surface"
        ),
        450: (
            "brionypenn watercolor of fish rising from the deep toward dappled "
            "surface light"
        ),
        900: (
            "brionypenn watercolor of creatures crossing between ocean and sky, "
            "the waterline a threshold between worlds"
        ),
        1350: (
            "brionypenn watercolor of dark seabirds sweeping across grey "
            "Pacific Northwest sky"
        ),
        1800: (
            "brionypenn watercolor of birds spiraling together, tightening into "
            "a dark mass descending toward the sea"
        ),
        2250: (
            "brionypenn watercolor of a great whale shape forming from the "
            "gathered flock, many becoming one, the whale swimming slowly "
            "through dark water"
        ),
    }

    # Render all 2700 frames
    frames_dir = FRAMES_DIR / "slow_motion"
    rendered = render_with_prompt_schedule(
        pipe, bg_image, slow_depth_files, frames_dir,
        prompt_schedule=prompt_schedule,
        cn_scale=0.75, strength=0.55,
        label="slow_motion",
    )

    # Smooth + assemble (90 seconds at 30fps)
    smooth_dir = FRAMES_DIR / "slow_motion_smooth"
    video_path = OUTPUT_DIR / "slow_motion_dissolution_90s.mp4"
    smooth_and_assemble(rendered, smooth_dir, video_path, fps=30,
                        window=9, sigma=2.5, label="slow_motion")

    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    log.info("=" * 70)
    log.info("SALISH SEA DREAMING — Alternative Simulations Pipeline")
    log.info("'We are the Salish Sea, dreaming itself awake.'")
    log.info("=" * 70)

    start_time = time.time()

    # Install deps
    install_deps()

    import torch
    if not torch.cuda.is_available():
        log.error("FATAL: No GPU available")
        sys.exit(1)

    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    log.info(f"GPU: {gpu} ({vram:.1f} GB)")

    # Phase 1: Run all simulations first (cheap, no GPU needed for sims)
    log.info("\n" + "=" * 60)
    log.info("PHASE 1: Generate all simulation depth maps")
    log.info("=" * 60)

    try:
        rd_depth = simulate_reaction_diffusion(n_frames=300)
        log.info(f"  Reaction-diffusion: {len(rd_depth)} frames")
    except Exception as e:
        log.error(f"  Reaction-diffusion failed: {e}")
        traceback.print_exc()

    try:
        dla_depth = simulate_dla(n_frames=200)
        log.info(f"  DLA: {len(dla_depth)} frames")
    except Exception as e:
        log.error(f"  DLA failed: {e}")
        traceback.print_exc()

    try:
        fluid_depth = simulate_fluid(n_frames=300)
        log.info(f"  Fluid: {len(fluid_depth)} frames")
    except Exception as e:
        log.error(f"  Fluid failed: {e}")
        traceback.print_exc()

    # Phase 2: Load pipeline once, run all rendering experiments
    log.info("\n" + "=" * 60)
    log.info("PHASE 2: Load pipeline and render all experiments")
    log.info("=" * 60)

    pipe = load_pipeline()

    experiments = [
        ("Experiment 1: Reaction-Diffusion", run_experiment_1),
        ("Experiment 2: DLA Growth", run_experiment_2),
        ("Experiment 3: Fluid Simulation", run_experiment_3),
        ("Experiment 4: Multi-Layer Resolume", run_experiment_4),
        ("Experiment 5: Slow-Motion Dissolution", run_experiment_5),
    ]

    results = {}
    for name, func in experiments:
        log.info(f"\n{'=' * 60}")
        log.info(f"Starting: {name}")
        log.info(f"{'=' * 60}")
        try:
            ok = func(pipe)
            results[name] = "OK" if ok else "PARTIAL"
            log.info(f"  {name}: {'OK' if ok else 'PARTIAL'}")
        except Exception as e:
            results[name] = f"FAILED: {e}"
            log.error(f"  {name}: FAILED: {e}")
            traceback.print_exc()
        gc.collect()
        torch.cuda.empty_cache()

    # Summary
    total_time = time.time() - start_time
    log.info("\n" + "=" * 70)
    log.info("ALL DONE — Alternative Simulations Pipeline")
    log.info(f"Total time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
    log.info("")

    for name, status in results.items():
        log.info(f"  {name}: {status}")

    log.info("")
    log.info(f"Output directory: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        size_mb = f.stat().st_size / 1e6
        log.info(f"  {f.name} ({size_mb:.1f} MB)")

    log.info("=" * 70)


if __name__ == "__main__":
    main()
