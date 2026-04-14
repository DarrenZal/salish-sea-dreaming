#!/usr/bin/env python3
"""
Orca Briony LoRA + ControlNet + RAFT Pipeline
=============================================
Transfer 243 orca frames from Node 1 → Node 2, render through Briony LoRA + ControlNet depth,
apply temporal smoothing, create normal + RAFT slow-motion videos.

Output in /home/jovyan/orca_long/output/:
  - orca_briony_16fps.mp4  (15s, normal speed)
  - orca_briony_8fps.mp4   (30s, dreamy)
  - orca_briony_raft_16fps.mp4 (45s, RAFT slow motion)
  - orca_briony_raft_8fps.mp4  (91s, RAFT ultra slow)
"""

import os
import sys
import time
import glob
import logging
import subprocess
import traceback
import numpy as np
from pathlib import Path
from PIL import Image

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/jovyan/orca_long/pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────
NODE1_URL = "https://model-deployment-0b50s.paas.ai.telus.com"
NODE1_TOKEN = "8f6ceea09691892cf2d19dc7466669ea"

LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
INPUT_DIR = Path("/home/jovyan/orca_long/input")
RENDER_DIR = Path("/home/jovyan/orca_long/rendered")
RAFT_DIR = Path("/home/jovyan/orca_long/raft")
OUTPUT_DIR = Path("/home/jovyan/orca_long/output")

PROMPT = "brionypenn watercolor painting of orca whale in the Salish Sea, Pacific Northwest ocean, natural history illustration, pen-and-ink outlines, soft organic tones"
NEG_PROMPT = "photo, photograph, realistic, 3d render, blurry, low quality, text, watermark"

CONTROLNET_SCALE = 0.6
GUIDANCE = 7.5
STEPS = 25
SEED = 42
IMG_SIZE = 512

SMOOTH_WINDOW = 9  # Temporal gaussian smoothing window
RAFT_INTERP = 2    # Frames to interpolate between each pair


def setup_dirs():
    """Create all output directories."""
    for d in [INPUT_DIR, RENDER_DIR, RAFT_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    log.info("Directories created.")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: Transfer frames from Node 1
# ═══════════════════════════════════════════════════════════════════════════
def transfer_frames():
    """Download all 243 orca frames from Node 1, resize to 512x512."""
    import requests
    from io import BytesIO
    import base64

    existing = sorted(INPUT_DIR.glob("*.png"))
    if len(existing) >= 243:
        log.info(f"All 243 frames already present in {INPUT_DIR}, skipping transfer.")
        return

    log.info("Starting frame transfer from Node 1...")
    session = requests.Session()
    session.headers.update({"Authorization": f"Token {NODE1_TOKEN}"})

    clips = [
        ("orca_clip_00", 81),
        ("orca_clip_01", 81),
        ("orca_clip_02", 81),
    ]

    transferred = 0
    for clip_name, count in clips:
        for i in range(1, count + 1):
            fname = f"{clip_name}_{i:05d}_.png"
            out_path = INPUT_DIR / fname

            if out_path.exists():
                transferred += 1
                continue

            url = f"{NODE1_URL}/api/contents/ComfyUI/output/{fname}"
            try:
                resp = session.get(url, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                img_bytes = base64.b64decode(data["content"])
                img = Image.open(BytesIO(img_bytes)).convert("RGB")
                img = img.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
                img.save(out_path)
                transferred += 1

                if transferred % 20 == 0:
                    log.info(f"  Transferred {transferred}/243 frames...")
            except Exception as e:
                log.error(f"  Failed to transfer {fname}: {e}")

    log.info(f"Transfer complete: {transferred}/243 frames in {INPUT_DIR}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: Render through Briony LoRA + ControlNet depth
# ═══════════════════════════════════════════════════════════════════════════
def render_frames():
    """Render all input frames through SD 1.5 + ControlNet depth + Briony LoRA."""
    import torch
    from diffusers import (
        StableDiffusionControlNetPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )
    from transformers import DPTForDepthEstimation, DPTImageProcessor

    existing = sorted(RENDER_DIR.glob("*.png"))
    input_frames = sorted(INPUT_DIR.glob("*.png"))

    if len(existing) >= len(input_frames):
        log.info(f"All {len(input_frames)} frames already rendered, skipping.")
        return

    log.info(f"Loading models for rendering {len(input_frames)} frames...")

    # ── Depth estimator (DPT-Large, no libGL dependency) ──
    log.info("Loading DPT depth estimator (Intel/dpt-large)...")
    depth_processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
    depth_model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")
    depth_model = depth_model.to("cuda").eval()

    # ── ControlNet depth ──
    log.info("Loading ControlNet depth model...")
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16,
    )

    # ── SD 1.5 + ControlNet pipeline ──
    log.info("Loading Stable Diffusion 1.5 pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")
    # Use attention slicing instead of xformers (version mismatch on this node)
    pipe.enable_attention_slicing()

    # ── Load Briony LoRA ──
    log.info(f"Loading Briony LoRA from {LORA_PATH}...")
    pipe.load_lora_weights(LORA_PATH)

    log.info("Models loaded. Starting render...")
    generator = torch.Generator(device="cuda").manual_seed(SEED)

    for idx, frame_path in enumerate(input_frames):
        out_path = RENDER_DIR / frame_path.name
        if out_path.exists():
            continue

        img = Image.open(frame_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))

        # Depth map
        inputs = depth_processor(images=img, return_tensors="pt").to("cuda")
        with torch.no_grad():
            depth_out = depth_model(**inputs).predicted_depth

        depth = depth_out.squeeze().cpu().numpy()
        depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
        depth_img = Image.fromarray((depth * 255).astype(np.uint8)).convert("RGB")
        depth_img = depth_img.resize((IMG_SIZE, IMG_SIZE))

        # Render
        result = pipe(
            prompt=PROMPT,
            negative_prompt=NEG_PROMPT,
            image=depth_img,
            num_inference_steps=STEPS,
            guidance_scale=GUIDANCE,
            controlnet_conditioning_scale=CONTROLNET_SCALE,
            generator=generator,
            width=IMG_SIZE,
            height=IMG_SIZE,
        ).images[0]

        result.save(out_path)

        if (idx + 1) % 10 == 0:
            log.info(f"  Rendered {idx + 1}/{len(input_frames)} frames")

    log.info(f"Rendering complete. {len(list(RENDER_DIR.glob('*.png')))} frames in {RENDER_DIR}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Temporal smoothing
# ═══════════════════════════════════════════════════════════════════════════
def gaussian_kernel(size):
    """1D Gaussian kernel for temporal smoothing."""
    sigma = size / 4.0
    x = np.arange(size) - size // 2
    kernel = np.exp(-x**2 / (2 * sigma**2))
    return kernel / kernel.sum()


def temporal_smooth(frames_dir, window=SMOOTH_WINDOW):
    """Apply temporal gaussian smoothing to a directory of frames in-place."""
    frame_paths = sorted(frames_dir.glob("*.png"))
    if len(frame_paths) == 0:
        return

    log.info(f"Temporal smoothing ({len(frame_paths)} frames, window={window})...")

    # Load all frames into array
    arrays = []
    for fp in frame_paths:
        img = np.array(Image.open(fp)).astype(np.float32)
        arrays.append(img)
    stack = np.stack(arrays, axis=0)  # (T, H, W, C)

    kernel = gaussian_kernel(window)
    half = window // 2
    smoothed = np.zeros_like(stack)

    for t in range(len(stack)):
        weights_sum = 0.0
        acc = np.zeros_like(stack[0])
        for k in range(window):
            src = t + k - half
            src = max(0, min(len(stack) - 1, src))
            acc += kernel[k] * stack[src]
            weights_sum += kernel[k]
        smoothed[t] = acc / weights_sum

    # Save back
    for i, fp in enumerate(frame_paths):
        img = Image.fromarray(smoothed[i].clip(0, 255).astype(np.uint8))
        img.save(fp)

    log.info("Temporal smoothing complete.")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: RAFT optical flow interpolation
# ═══════════════════════════════════════════════════════════════════════════
def raft_interpolate():
    """Use RAFT to interpolate frames for slow motion."""
    import torch
    import torchvision.transforms.functional as TF
    from torchvision.models.optical_flow import raft_small, Raft_Small_Weights

    existing = sorted(RAFT_DIR.glob("*.png"))
    rendered = sorted(RENDER_DIR.glob("*.png"))

    expected = len(rendered) + (len(rendered) - 1) * RAFT_INTERP
    if len(existing) >= expected:
        log.info(f"RAFT interpolation already done ({len(existing)} frames), skipping.")
        return

    log.info(f"RAFT interpolation: {len(rendered)} → ~{expected} frames...")

    # Load RAFT model
    weights = Raft_Small_Weights.DEFAULT
    model = raft_small(weights=weights).to("cuda").eval()
    transforms = weights.transforms()

    def load_tensor(path):
        img = Image.open(path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        return TF.to_tensor(img).unsqueeze(0).to("cuda")

    def warp_flow(img_tensor, flow):
        """Warp an image tensor using optical flow."""
        B, C, H, W = img_tensor.shape
        grid_y, grid_x = torch.meshgrid(
            torch.arange(H, device=flow.device, dtype=torch.float32),
            torch.arange(W, device=flow.device, dtype=torch.float32),
            indexing="ij",
        )
        grid_x = grid_x.unsqueeze(0) + flow[:, 0]
        grid_y = grid_y.unsqueeze(0) + flow[:, 1]
        # Normalize to [-1, 1]
        grid_x = 2 * grid_x / (W - 1) - 1
        grid_y = 2 * grid_y / (H - 1) - 1
        grid = torch.stack([grid_x, grid_y], dim=-1)
        return torch.nn.functional.grid_sample(
            img_tensor, grid, mode="bilinear", padding_mode="border", align_corners=True
        )

    frame_counter = 0
    for i in range(len(rendered)):
        # Save original frame
        src = Image.open(rendered[i]).convert("RGB")
        out_name = f"raft_{frame_counter:06d}.png"
        src.save(RAFT_DIR / out_name)
        frame_counter += 1

        if i < len(rendered) - 1:
            img1 = load_tensor(rendered[i])
            img2 = load_tensor(rendered[i + 1])

            # Prepare for RAFT (needs specific transforms)
            img1_t, img2_t = transforms(img1, img2)

            with torch.no_grad():
                flows = model(img1_t, img2_t)
                flow_fwd = flows[-1]  # Use final refinement

            # Interpolate N frames between
            for n in range(1, RAFT_INTERP + 1):
                alpha = n / (RAFT_INTERP + 1)
                # Forward warp from img1, backward warp from img2
                partial_flow = flow_fwd * alpha
                warped = warp_flow(img1, partial_flow)
                # Blend with linear interpolation for stability
                blended = (1 - alpha) * img1 + alpha * img2
                # Weighted: mostly warped, some linear for stability
                result = 0.7 * warped + 0.3 * blended
                result = result.clamp(0, 1).squeeze(0)
                result_img = TF.to_pil_image(result.cpu())
                out_name = f"raft_{frame_counter:06d}.png"
                result_img.save(RAFT_DIR / out_name)
                frame_counter += 1

        if (i + 1) % 30 == 0:
            log.info(f"  RAFT progress: {i + 1}/{len(rendered)} source frames processed ({frame_counter} total)")

    log.info(f"RAFT interpolation complete: {frame_counter} frames in {RAFT_DIR}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: Assemble videos
# ═══════════════════════════════════════════════════════════════════════════
def assemble_video(frames_dir, pattern, output_path, fps):
    """Assemble PNG frames into MP4 using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-pattern_type", "glob",
        "-i", str(frames_dir / pattern),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        str(output_path),
    ]
    log.info(f"Assembling {output_path.name} at {fps}fps...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"ffmpeg error: {result.stderr}")
    else:
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log.info(f"  Created {output_path.name} ({size_mb:.1f} MB)")


def assemble_all_videos():
    """Create all output videos."""
    # Normal speed videos from rendered frames
    assemble_video(RENDER_DIR, "*.png", OUTPUT_DIR / "orca_briony_16fps.mp4", fps=16)
    assemble_video(RENDER_DIR, "*.png", OUTPUT_DIR / "orca_briony_8fps.mp4", fps=8)

    # RAFT slow motion videos
    assemble_video(RAFT_DIR, "raft_*.png", OUTPUT_DIR / "orca_briony_raft_16fps.mp4", fps=16)
    assemble_video(RAFT_DIR, "raft_*.png", OUTPUT_DIR / "orca_briony_raft_8fps.mp4", fps=8)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    t_start = time.time()
    log.info("=" * 60)
    log.info("ORCA BRIONY PIPELINE — START")
    log.info("=" * 60)

    try:
        setup_dirs()

        # Phase 1: Transfer
        t = time.time()
        transfer_frames()
        log.info(f"Phase 1 (transfer): {time.time() - t:.0f}s")

        # Phase 2: Render
        t = time.time()
        render_frames()
        log.info(f"Phase 2 (render): {time.time() - t:.0f}s")

        # Phase 3: Temporal smoothing on rendered frames
        t = time.time()
        temporal_smooth(RENDER_DIR)
        log.info(f"Phase 3 (smooth): {time.time() - t:.0f}s")

        # Phase 4: RAFT interpolation
        t = time.time()
        raft_interpolate()
        log.info(f"Phase 4 (RAFT): {time.time() - t:.0f}s")

        # Phase 4b: Temporal smoothing on RAFT frames too
        t = time.time()
        temporal_smooth(RAFT_DIR)
        log.info(f"Phase 4b (RAFT smooth): {time.time() - t:.0f}s")

        # Phase 5: Assemble videos
        t = time.time()
        assemble_all_videos()
        log.info(f"Phase 5 (videos): {time.time() - t:.0f}s")

        # Summary
        log.info("=" * 60)
        log.info("PIPELINE COMPLETE")
        total = time.time() - t_start
        log.info(f"Total time: {total / 60:.1f} minutes")

        for mp4 in sorted(OUTPUT_DIR.glob("*.mp4")):
            size_mb = mp4.stat().st_size / (1024 * 1024)
            log.info(f"  {mp4.name}: {size_mb:.1f} MB")

    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        log.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
