#!/usr/bin/env python3
"""
Evaluate Briony LoRA quality — tests style generalization across subjects.

Run on Windows RTX 3090:
  C:\\Users\\user\\kohya-env\\Scripts\\python.exe evaluate_lora.py \\
    --lora C:\\Users\\user\\briony-training\\output\\briony_watercolor_v1.safetensors \\
    --output C:\\Users\\user\\briony-training\\eval

Success criteria:
  - Outputs show Briony's soft watercolor edges and pigment blending
  - Style transfers across subjects (not just marine scenes)
  - Doesn't collapse to reproducing training images
"""

import argparse
import os
import torch
from diffusers import StableDiffusionPipeline
from pathlib import Path


# Test prompts spanning different subjects to verify style generalization
TEST_PROMPTS = [
    # Marine subjects (should be strong — training data is mostly marine)
    "brionypenn watercolor painting of an orca whale breaching, soft edges, natural pigment",
    "brionypenn watercolor painting of herring schooling underwater, kelp forest, soft edges",
    "brionypenn watercolor painting of a giant pacific octopus in a coral reef, vibrant colors",

    # Land subjects (tests generalization beyond training content)
    "brionypenn watercolor painting of a cedar forest in morning mist, ecological illustration",
    "brionypenn watercolor painting of a camas meadow with butterflies, soft edges, natural pigment",
    "brionypenn watercolor painting of a black bear catching salmon in a stream",

    # Atmospheric/abstract (tests technique capture)
    "brionypenn watercolor painting of a misty coastline at dawn, loose wash, atmospheric",
    "brionypenn watercolor painting of an underwater kelp forest, bioluminescent, ecological",

    # Without trigger token (control — should NOT show Briony style)
    "watercolor painting of an orca whale breaching",
    "watercolor painting of a cedar forest in morning mist",
]

# Also test at different guidance scales
GUIDANCE_SCALES = [7.5]  # Standard; add [5, 7.5, 10] for full sweep


def evaluate(lora_path: str, output_dir: str, base_model: str = "runwayml/stable-diffusion-v1-5"):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    print(f"Loading base model: {base_model}")
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")

    # Generate control images (no LoRA) for the control prompts
    print("\n=== Control images (no LoRA) ===")
    for i, prompt in enumerate(TEST_PROMPTS[-2:]):
        generator = torch.Generator("cuda").manual_seed(42)
        image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5,
                     generator=generator).images[0]
        fname = f"control_{i:02d}.png"
        image.save(output / fname)
        print(f"  {fname}: {prompt[:60]}...")

    # Load LoRA
    print(f"\nLoading LoRA: {lora_path}")
    pipe.load_lora_weights(lora_path)

    # Generate LoRA images
    print("\n=== LoRA images ===")
    for i, prompt in enumerate(TEST_PROMPTS):
        for gs in GUIDANCE_SCALES:
            generator = torch.Generator("cuda").manual_seed(42)
            image = pipe(prompt, num_inference_steps=30, guidance_scale=gs,
                         generator=generator).images[0]
            fname = f"lora_{i:02d}_gs{gs}.png"
            image.save(output / fname)
            print(f"  {fname}: {prompt[:60]}...")

    # Generate comparison: same seed, same prompt, with and without LoRA trigger
    print("\n=== Trigger comparison ===")
    pipe.unload_lora_weights()
    for i, prompt in enumerate(TEST_PROMPTS[:3]):
        generator = torch.Generator("cuda").manual_seed(42)
        # Without LoRA
        image_base = pipe(prompt.replace("brionypenn ", ""),
                          num_inference_steps=30, guidance_scale=7.5,
                          generator=generator).images[0]
        image_base.save(output / f"compare_base_{i:02d}.png")

    pipe.load_lora_weights(lora_path)
    for i, prompt in enumerate(TEST_PROMPTS[:3]):
        generator = torch.Generator("cuda").manual_seed(42)
        # With LoRA
        image_lora = pipe(prompt, num_inference_steps=30, guidance_scale=7.5,
                          generator=generator).images[0]
        image_lora.save(output / f"compare_lora_{i:02d}.png")

    print(f"\nEvaluation complete! {len(os.listdir(output))} images saved to {output}")
    print("\nNext steps:")
    print("  1. Review images for Briony watercolor style (soft edges, pigment blending)")
    print("  2. Compare lora_* vs control_* for style difference")
    print("  3. Check that style appears on land subjects (not just marine)")
    print("  4. Verify no training image reproduction (mode collapse check)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Briony LoRA")
    parser.add_argument("--lora", required=True, help="Path to LoRA .safetensors")
    parser.add_argument("--output", default="C:\\Users\\user\\briony-training\\eval",
                        help="Output directory for evaluation images")
    parser.add_argument("--base-model", default="runwayml/stable-diffusion-v1-5",
                        help="Base model")
    args = parser.parse_args()
    evaluate(args.lora, args.output, args.base_model)
