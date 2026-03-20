#!/usr/bin/env python3
"""
Convert Briony LoRA to the format StreamDiffusionTD expects.

Our LoRA has PEFT/diffusers-native keys:
  down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_A.weight

StreamDiffusionTD (older diffusers) expects kohya-style keys:
  lora_unet_down_blocks_0_attentions_0_transformer_blocks_0_attn1_to_q.lora_down.weight

Despite the warning saying "old format", it actually needs the kohya format.

Usage:
  python convert_for_streamdiffusion.py briony_watercolor_sdturbo.safetensors
  → outputs briony_watercolor_sdturbo_kohya.safetensors

Drop the output file into StreamDiffusionTD's LoRA folder and set weight to 1.0.
"""

import argparse
import sys
from pathlib import Path

try:
    from safetensors.torch import load_file, save_file
except ImportError:
    print("Error: safetensors required. Install with: pip install safetensors")
    sys.exit(1)


def convert_peft_to_kohya(state_dict):
    """Convert PEFT/diffusers-native LoRA keys to kohya format for StreamDiffusionTD."""
    new_state_dict = {}
    converted = 0
    skipped = 0

    for key, value in state_dict.items():
        new_key = key

        # Strip base_model.model prefix if present
        clean_key = key
        if clean_key.startswith("base_model.model."):
            clean_key = clean_key[len("base_model.model."):]
        if clean_key.startswith("unet."):
            clean_key = clean_key[len("unet."):]

        # Check if it's a UNet LoRA weight (starts with down_blocks, mid_block, up_blocks)
        is_unet = any(clean_key.startswith(p) for p in
                      ["down_blocks", "mid_block", "up_blocks"])

        # Check if text encoder
        is_te = clean_key.startswith("text_model") or key.startswith("text_encoder")
        if is_te:
            if key.startswith("text_encoder."):
                clean_key = key[len("text_encoder."):]

        if is_unet:
            # Convert lora_A/lora_B to lora_down/lora_up
            if ".lora_A.weight" in clean_key:
                module_path = clean_key.replace(".lora_A.weight", "")
                weight_suffix = ".lora_down.weight"
            elif ".lora_B.weight" in clean_key:
                module_path = clean_key.replace(".lora_B.weight", "")
                weight_suffix = ".lora_up.weight"
            elif ".alpha" in clean_key:
                module_path = clean_key.replace(".alpha", "")
                weight_suffix = ".alpha"
            else:
                new_state_dict[key] = value
                skipped += 1
                continue

            # Convert dots to underscores for the module path
            kohya_module = module_path.replace(".", "_")
            new_key = f"lora_unet_{kohya_module}{weight_suffix}"
            converted += 1

        elif is_te:
            if ".lora_A.weight" in clean_key:
                module_path = clean_key.replace(".lora_A.weight", "")
                weight_suffix = ".lora_down.weight"
            elif ".lora_B.weight" in clean_key:
                module_path = clean_key.replace(".lora_B.weight", "")
                weight_suffix = ".lora_up.weight"
            elif ".alpha" in clean_key:
                module_path = clean_key.replace(".alpha", "")
                weight_suffix = ".alpha"
            else:
                new_state_dict[key] = value
                skipped += 1
                continue

            kohya_module = module_path.replace(".", "_")
            new_key = f"lora_te_{kohya_module}{weight_suffix}"
            converted += 1
        else:
            skipped += 1

        new_state_dict[new_key] = value

    return new_state_dict, converted, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Convert LoRA to kohya format for StreamDiffusionTD")
    parser.add_argument("input", help="Input .safetensors file")
    parser.add_argument("--output", "-o", help="Output file (default: adds _kohya suffix)")
    parser.add_argument("--dry-run", action="store_true", help="Show key mappings without saving")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_name(
        input_path.stem + "_kohya" + input_path.suffix
    )

    print(f"Loading: {input_path}")
    state_dict = load_file(str(input_path))
    print(f"  {len(state_dict)} weight tensors")

    # Check current format
    sample_keys = list(state_dict.keys())[:3]
    print(f"\n  Current format (sample keys):")
    for k in sample_keys:
        print(f"    {k}")

    already_kohya = any(k.startswith("lora_unet_") for k in state_dict.keys())
    if already_kohya:
        print("\n  Already in kohya format! No conversion needed.")
        sys.exit(0)

    # Convert
    new_state_dict, converted, skipped = convert_peft_to_kohya(state_dict)

    print(f"\n  Converted: {converted} keys to kohya format")
    print(f"  Unchanged: {skipped} keys")

    sample_new = list(new_state_dict.keys())[:3]
    print(f"\n  Converted format (sample keys):")
    for k in sample_new:
        print(f"    {k}")

    if args.dry_run:
        print("\n  [dry-run] No file written.")
        return

    print(f"\n  Saving: {output_path}")
    save_file(new_state_dict, str(output_path))
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  Done! {size_mb:.1f} MB")
    print(f"\n  Next steps:")
    print(f"  1. Copy {output_path.name} to StreamDiffusionTD LoRA folder")
    print(f"  2. Select it in StreamDiffusionTD")
    print(f"  3. Set LoRA weight to 1.0")
    print(f"  4. The 'old format' warning should be gone")


if __name__ == "__main__":
    main()
