#!/usr/bin/env python3
"""
AnimateDiff + FreeNoise + ControlNet + Briony LoRA.
Processes ALL frames as one sequence — no window boundaries.

FreeNoise extends AnimateDiff beyond 16 frames by rescheduling
noise across a sliding context window. 48 frames = one coherent pass.

Usage:
  python run_animatediff_freenoise.py --input frames/ --output output/ [options]
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

DEFAULT_PROMPT = (
    "brionypenn watercolor painting, soft wet edges, natural pigment washes, "
    "ecological illustration, underwater marine life, translucent water, Salish Sea"
)
NEG_PROMPT = (
    "photograph, photorealistic, sharp lines, digital art, 3d render, "
    "harsh shadows, overexposed, blurry, artifacts"
)


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


def run(input_dir, output_dir, strength, controlnet_scale, steps,
        guidance_scale, lora_path, prompt, neg_prompt, seed, fps,
        context_length, context_stride):

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    frames = load_frames(input_dir)
    n = len(frames)
    if n == 0:
        print("ERROR: No frames")
        return
    print(f"Loaded {n} frames")

    print("Extracting Canny edges...")
    edge_frames = [canny_edges(f) for f in frames]

    # Build pipeline
    print("Loading motion adapter...")
    adapter = MotionAdapter.from_pretrained(MOTION_ADAPTER, torch_dtype=torch.float16)

    print("Loading ControlNet...")
    controlnet = ControlNetModel.from_pretrained(CONTROLNET, torch_dtype=torch.float16)

    print("Loading VAE...")
    vae = AutoencoderKL.from_pretrained(VAE_MODEL, torch_dtype=torch.float16)

    print(f"Loading base model...")
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
        BASE_MODEL, subfolder="scheduler",
        clip_sample=False, timestep_spacing="linspace",
        beta_schedule="linear", steps_offset=1,
    )

    print("Loading Briony LoRA...")
    pipe.load_lora_weights(lora_path, adapter_name="briony")
    pipe.set_adapters(["briony"], [1.0])
    pipe.fuse_lora()
    pipe.unload_lora_weights()

    pipe.enable_vae_slicing()

    # FreeNoise — the key: extends temporal attention across all frames
    print(f"Enabling FreeNoise (context_length={context_length}, stride={context_stride})...")
    pipe.enable_free_noise(
        context_length=context_length,
        context_stride=context_stride,
    )

    # Also enable FreeInit for noise refinement
    print("Enabling FreeInit (2 iterations, fast sampling)...")
    pipe.enable_free_init(
        num_iters=2,
        use_fast_sampling=True,
        method="butterworth",
        order=4,
        spatial_stop_frequency=0.25,
        temporal_stop_frequency=0.25,
    )

    print(f"\nGenerating {n} frames as ONE sequence")
    print(f"  strength={strength} cn={controlnet_scale} steps={steps}")
    print(f"  FreeNoise context={context_length} stride={context_stride}")
    print(f"  FreeInit iters=2")

    generator = torch.Generator("cuda").manual_seed(seed)

    t0 = time.perf_counter()
    output = pipe(
        video=frames,
        prompt=prompt,
        negative_prompt=neg_prompt,
        conditioning_frames=edge_frames,
        strength=strength,
        controlnet_conditioning_scale=controlnet_scale,
        num_inference_steps=steps,
        guidance_scale=guidance_scale,
        generator=generator,
        decode_chunk_size=4,
    )
    elapsed = time.perf_counter() - t0

    result_frames = output.frames[0]
    print(f"\nGeneration done: {elapsed:.0f}s ({elapsed/n:.1f}s/frame)")

    # Save frames
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    for i, frame in enumerate(result_frames):
        if isinstance(frame, Image.Image):
            frame.save(frames_dir / f"frame_{i:04d}.png")
        else:
            Image.fromarray(frame).save(frames_dir / f"frame_{i:04d}.png")

    # Export video
    video_path = output_path / "styled.mp4"
    export_to_video(result_frames, str(video_path), fps=fps)

    vram = torch.cuda.max_memory_allocated() / 1e9
    print(f"\n=== Done ===")
    print(f"  Frames: {len(result_frames)}")
    print(f"  Time: {elapsed:.0f}s ({elapsed/n:.1f}s/frame)")
    print(f"  Peak VRAM: {vram:.1f}GB")
    print(f"  Video: {video_path}")
    print(f"  Frames: {frames_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strength", type=float, default=0.60)
    parser.add_argument("--controlnet-scale", type=float, default=0.70)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--lora", required=True)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--neg-prompt", default=NEG_PROMPT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--context-length", type=int, default=16,
                        help="FreeNoise context window (16 = AnimateDiff native)")
    parser.add_argument("--context-stride", type=int, default=4,
                        help="FreeNoise stride between context windows")
    args = parser.parse_args()

    run(args.input, args.output, args.strength, args.controlnet_scale,
        args.steps, args.guidance_scale, args.lora, args.prompt,
        args.neg_prompt, args.seed, args.fps,
        args.context_length, args.context_stride)
