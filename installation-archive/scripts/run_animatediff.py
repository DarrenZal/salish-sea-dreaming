#!/usr/bin/env python3
"""
AnimateDiff + ControlNet + Briony LoRA video style transfer.
Salish Sea Dreaming — temporally coherent watercolor pipeline.

Processes input video in 16-frame windows with 4-frame overlap.
Temporal attention across all 16 frames = no per-frame flicker.

Usage:
  python run_animatediff.py --input frames/ --output output/ [options]
"""

import argparse
import time
import numpy as np
import cv2
import torch
from pathlib import Path
from PIL import Image
from diffusers import (
    AnimateDiffVideoToVideoControlNetPipeline,
    ControlNetModel,
    MotionAdapter,
    AutoencoderKL,
    DDIMScheduler,
)
from diffusers.utils import export_to_video

MOTION_ADAPTER = "guoyww/animatediff-motion-adapter-v1-5-3"
CONTROLNET = "lllyasviel/sd-controlnet-canny"
VAE_MODEL = "stabilityai/sd-vae-ft-mse"
BASE_MODEL = "runwayml/stable-diffusion-v1-5"

DEFAULT_LORA = str(
    Path(__file__).parent.parent.parent / "drive/Models/briony_watercolor_v1.safetensors"
)
DEFAULT_PROMPT = (
    "brionypenn watercolor painting, soft wet edges, natural pigment washes, "
    "ecological illustration, underwater marine life, translucent water, Salish Sea"
)
NEG_PROMPT = (
    "photograph, photorealistic, sharp lines, digital art, 3d render, "
    "harsh shadows, overexposed, blurry, artifacts"
)

WINDOW_SIZE = 16
WINDOW_STRIDE = 12  # 4-frame overlap


def canny_edges(img_pil, low=50, high=150):
    gray = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, low, high)
    return Image.fromarray(cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB))


def load_frames(input_dir, size=512):
    paths = sorted(Path(input_dir).glob("*.png")) + sorted(Path(input_dir).glob("*.jpg"))
    frames = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        if img.size != (size, size):
            img = img.resize((size, size), Image.LANCZOS)
        frames.append(img)
    return frames


def blend_windows(windows, stride, total):
    overlap = WINDOW_SIZE - stride
    result = [None] * total

    for w_idx, window in enumerate(windows):
        start = w_idx * stride
        for f_idx, frame in enumerate(window):
            abs_idx = start + f_idx
            if abs_idx >= total:
                break
            if result[abs_idx] is None:
                result[abs_idx] = np.array(frame, dtype=np.float32)
            elif f_idx < overlap:
                alpha = f_idx / overlap
                result[abs_idx] = (
                    (1 - alpha) * result[abs_idx] + alpha * np.array(frame, dtype=np.float32)
                )

    return [Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            for arr in result if arr is not None]


def build_pipeline(lora_path):
    print("Loading motion adapter (v1-5-3)...")
    adapter = MotionAdapter.from_pretrained(MOTION_ADAPTER, torch_dtype=torch.float16)

    print("Loading ControlNet (Canny)...")
    controlnet = ControlNetModel.from_pretrained(CONTROLNET, torch_dtype=torch.float16)

    print("Loading improved VAE...")
    vae = AutoencoderKL.from_pretrained(VAE_MODEL, torch_dtype=torch.float16)

    print(f"Loading base model ({BASE_MODEL})...")
    pipe = AnimateDiffVideoToVideoControlNetPipeline.from_pretrained(
        BASE_MODEL,
        motion_adapter=adapter,
        controlnet=controlnet,
        vae=vae,
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
    ).to("cuda")

    pipe.scheduler = DDIMScheduler.from_pretrained(
        BASE_MODEL,
        subfolder="scheduler",
        clip_sample=False,
        timestep_spacing="linspace",
        beta_schedule="linear",
        steps_offset=1,
    )

    print(f"Loading Briony LoRA...")
    pipe.load_lora_weights(lora_path, adapter_name="briony")
    pipe.set_adapters(["briony"], [1.0])
    # Fuse LoRA into model weights — saves ~1.5GB VRAM
    pipe.fuse_lora()
    pipe.unload_lora_weights()

    pipe.enable_vae_slicing()
    torch.backends.cuda.enable_flash_sdp(True)
    torch.backends.cuda.enable_mem_efficient_sdp(True)

    # Skip FreeInit on 12GB — saves ~2GB peak VRAM
    # Uncomment if you have 16GB+:
    # pipe.enable_free_init(num_iters=2, use_fast_sampling=True)

    return pipe


def run(input_dir, output_dir, strength, controlnet_scale, canny_low, canny_high,
        steps, guidance_scale, lora_path, prompt, neg_prompt, seed, fps):

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    frames = load_frames(input_dir)
    n = len(frames)
    if n == 0:
        print("ERROR: No frames")
        return
    print(f"Loaded {n} frames")

    print("Extracting Canny edges...")
    edge_frames = [canny_edges(f, canny_low, canny_high) for f in frames]

    # Build windows
    window_starts = list(range(0, n - WINDOW_SIZE + 1, WINDOW_STRIDE))
    if window_starts and window_starts[-1] + WINDOW_SIZE < n:
        window_starts.append(n - WINDOW_SIZE)
    if not window_starts:
        window_starts = [0]

    print(f"\n{len(window_starts)} windows × {WINDOW_SIZE} frames")
    print(f"  strength={strength} cn={controlnet_scale} steps={steps} seed={seed}\n")

    pipe = build_pipeline(lora_path)
    generator = torch.Generator("cuda").manual_seed(seed)

    rendered_windows = []
    timings = []

    for w_idx, start in enumerate(window_starts):
        end = min(start + WINDOW_SIZE, n)
        video_window = list(frames[start:end])
        edge_window = list(edge_frames[start:end])

        while len(video_window) < WINDOW_SIZE:
            video_window.append(video_window[-1])
            edge_window.append(edge_window[-1])

        t0 = time.perf_counter()
        output = pipe(
            video=video_window,
            prompt=prompt,
            negative_prompt=neg_prompt,
            conditioning_frames=edge_window,
            strength=strength,
            controlnet_conditioning_scale=controlnet_scale,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
            decode_chunk_size=8,
        )
        elapsed = time.perf_counter() - t0
        timings.append(elapsed)

        window_frames = output.frames[0]
        actual_len = end - start
        rendered_windows.append(window_frames[:actual_len])

        vram = torch.cuda.max_memory_allocated() / 1e9
        print(f"  Window [{w_idx+1}/{len(window_starts)}] start={start} — {elapsed:.1f}s | VRAM: {vram:.1f}GB")
        torch.cuda.reset_peak_memory_stats()

    # Composite
    print("\nCompositing windows...")
    final_frames = blend_windows(rendered_windows, WINDOW_STRIDE, n)

    # Save frames
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    for i, frame in enumerate(final_frames):
        frame.save(frames_dir / f"frame_{i:04d}.png")

    # Export video
    output_video = output_path / "styled.mp4"
    export_to_video(final_frames, str(output_video), fps=fps)

    avg = sum(timings) / len(timings)
    print(f"\n=== Done ===")
    print(f"  Windows: {len(timings)} | Avg: {avg:.1f}s/window")
    print(f"  Frames: {len(final_frames)} | Total: {sum(timings):.0f}s")
    print(f"  Output: {output_video}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AnimateDiff + ControlNet + Briony LoRA")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strength", type=float, default=0.60)
    parser.add_argument("--controlnet-scale", type=float, default=0.70)
    parser.add_argument("--canny-low", type=int, default=50)
    parser.add_argument("--canny-high", type=int, default=150)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--lora", default=DEFAULT_LORA)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--neg-prompt", default=NEG_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fps", type=int, default=24, help="Output video FPS")
    args = parser.parse_args()

    run(args.input, args.output, args.strength, args.controlnet_scale,
        args.canny_low, args.canny_high, args.steps, args.guidance_scale,
        args.lora, args.prompt, args.neg_prompt, args.seed, args.fps)
