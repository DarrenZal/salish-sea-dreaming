#!/usr/bin/env python3
"""
Merge Briony LoRA weights into SD 1.5 base model.

Produces a single merged checkpoint that can be compiled to TensorRT
in StreamDiffusion without needing separate LoRA loading.

The merged model has the Briony watercolor style permanently baked in —
just use the trigger token "brionypenn" in the prompt.

Run on Windows RTX 3090:
  C:\Users\user\kohya-env\Scripts\python.exe merge_lora.py \
    --lora C:\Users\user\briony-training\output\briony_watercolor_v1.safetensors \
    --output C:\Users\user\briony-training\output\sd15-briony-merged
"""

import argparse
import torch
from diffusers import StableDiffusionPipeline


def merge_lora(lora_path: str, output_dir: str,
               base_model: str = "runwayml/stable-diffusion-v1-5",
               lora_weight: float = 1.0):
    print(f"Loading base model: {base_model}")
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model, torch_dtype=torch.float16, safety_checker=None
    )

    print(f"Loading LoRA: {lora_path} (weight: {lora_weight})")
    pipe.load_lora_weights(lora_path)

    print("Fusing LoRA weights into base model...")
    pipe.fuse_lora(lora_scale=lora_weight)
    pipe.unload_lora_weights()

    print(f"Saving merged model to: {output_dir}")
    pipe.save_pretrained(output_dir)

    print(f"\nDone! Merged model saved to {output_dir}")
    print("This model has Briony's watercolor style baked in.")
    print("Use prompt trigger token 'brionypenn' to activate the style.")
    print("\nNext: load this model in StreamDiffusion and compile to TensorRT.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA into SD 1.5")
    parser.add_argument("--lora", required=True, help="Path to LoRA .safetensors")
    parser.add_argument("--output", required=True, help="Output directory for merged model")
    parser.add_argument("--base-model", default="runwayml/stable-diffusion-v1-5")
    parser.add_argument("--weight", type=float, default=1.0, help="LoRA weight (default: 1.0)")
    args = parser.parse_args()
    merge_lora(args.lora, args.output, args.base_model, args.weight)
