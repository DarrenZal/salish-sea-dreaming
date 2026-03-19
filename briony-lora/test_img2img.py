#!/usr/bin/env python3
"""
Step 6: Test LoRA as post-processing layer on Autolume GAN output (img2img).

This is the highest-value integration test — can the LoRA "paint"
Autolume's StyleGAN fish output in Briony's watercolor style?

Run on Windows RTX 3090:
  C:\\Users\\user\\kohya-env\\Scripts\\python.exe test_img2img.py \\
    --lora C:\\Users\\user\\briony-training\\output\\briony_watercolor_v1.safetensors \\
    --input-dir C:\\Users\\user\\briony-training\\autolume-frames \\
    --output C:\\Users\\user\\briony-training\\img2img-results

Input: Sample frames exported from Autolume fish model (SCP'd from TELUS checkpoints)
Output: Side-by-side comparisons at multiple strength levels
"""

import argparse
import time
import torch
from diffusers import StableDiffusionImg2ImgPipeline
from pathlib import Path
from PIL import Image


# Strength controls how much the LoRA style overrides the input
# Lower = more faithful to input structure, higher = more Briony style
STRENGTH_LEVELS = [0.25, 0.35, 0.45, 0.55, 0.65]

# Style-only prompt — tests pure aesthetic transfer without changing subject matter
DEFAULT_PROMPT = "brionypenn watercolor painting, soft edges, natural pigment, ecological illustration"


def test_img2img(lora_path: str, input_dir: str, output_dir: str,
                 base_model: str = "runwayml/stable-diffusion-v1-5",
                 custom_prompt: str = None):
    input_path = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Find input frames
    frames = sorted(list(input_path.glob("*.png")) + list(input_path.glob("*.jpg")))
    if not frames:
        print(f"ERROR: No image files found in {input_dir}")
        print("Expected: Sample frames from Autolume fish model")
        print("To get frames:")
        print("  1. Export from Autolume (preferred)")
        print("  2. Or use marine-photo-base QC'd photos as stand-in")
        return

    print(f"Found {len(frames)} input frames")
    print(f"Loading pipeline: {base_model}")

    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        base_model, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")

    print(f"Loading LoRA: {lora_path}")
    pipe.load_lora_weights(lora_path)

    prompt = custom_prompt or DEFAULT_PROMPT
    timings = []

    for frame_path in frames[:20]:  # Cap at 20 frames
        frame_name = frame_path.stem
        frame = Image.open(frame_path).convert("RGB").resize((512, 512))

        # Save original for comparison
        frame.save(output / f"{frame_name}_original.png")

        for strength in STRENGTH_LEVELS:
            generator = torch.Generator("cuda").manual_seed(42)

            start = time.perf_counter()
            result = pipe(
                prompt,
                image=frame,
                strength=strength,
                num_inference_steps=30,
                guidance_scale=7.5,
                generator=generator,
            ).images[0]
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            fname = f"{frame_name}_s{strength:.2f}.png"
            result.save(output / fname)
            print(f"  {fname} — {elapsed:.2f}s")

    # Print performance summary
    print(f"\n=== Performance Summary ===")
    print(f"Frames processed: {len(frames[:20])}")
    print(f"Strength levels: {STRENGTH_LEVELS}")
    print(f"Total images generated: {len(timings)}")
    if timings:
        avg = sum(timings) / len(timings)
        print(f"Average latency: {avg:.2f}s per frame")
        print(f"Min: {min(timings):.2f}s, Max: {max(timings):.2f}s")
        print(f"Theoretical max fps (no overhead): {1/avg:.1f}")

    print(f"\n=== Results in {output} ===")
    print("Review side-by-side:")
    print("  - *_original.png: Raw GAN/photo input")
    print("  - *_s0.25.png: Light style transfer (structure preserved)")
    print("  - *_s0.45.png: Medium style transfer (balanced)")
    print("  - *_s0.65.png: Heavy style transfer (more Briony, less input)")
    print()
    print("Key question: At which strength does Briony's watercolor aesthetic")
    print("emerge while still recognizing the fish species?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test LoRA img2img on Autolume frames")
    parser.add_argument("--lora", required=True, help="Path to LoRA .safetensors")
    parser.add_argument("--input-dir", required=True, help="Directory with input frames")
    parser.add_argument("--output", default="C:\\Users\\user\\briony-training\\img2img-results",
                        help="Output directory")
    parser.add_argument("--base-model", default="runwayml/stable-diffusion-v1-5")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt (default: style-only prompt for pure aesthetic transfer)")
    args = parser.parse_args()
    test_img2img(args.lora, args.input_dir, args.output, args.base_model, args.prompt)
