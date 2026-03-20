#!/usr/bin/env python3
"""
Convert Briony LoRA from kohya_ss format to diffusers format.

The old kohya format stores weights as flat keys like:
  lora_unet_down_blocks_0_attentions_0_transformer_blocks_0_attn1_to_q.lora_down.weight

The new diffusers format expects:
  unet.down_blocks.0.attentions.0.transformer_blocks.0.attn1.to_q.lora_layer.down.weight

StreamDiffusionTD warns:
  "You have saved the LoRA weights using the old format"
  — this means weights may not map correctly, causing weak/no style transfer.

Usage:
  python convert_lora_format.py briony_watercolor_sdturbo.safetensors
  python convert_lora_format.py briony_watercolor_sdturbo.safetensors --output briony_sdturbo_diffusers.safetensors
"""

import argparse
import sys
from pathlib import Path

try:
    from safetensors.torch import load_file, save_file
except ImportError:
    print("Error: safetensors required. Install with: pip install safetensors")
    sys.exit(1)


def convert_kohya_to_diffusers(state_dict):
    """Convert kohya_ss LoRA keys to diffusers format."""
    new_state_dict = {}
    converted = 0
    skipped = 0

    for key, value in state_dict.items():
        new_key = None

        # kohya format: lora_unet_... or lora_te_...
        if key.startswith("lora_unet_"):
            # Strip prefix and convert underscores to dots for module path
            suffix = key[len("lora_unet_"):]

            # Split off the lora weight type (lora_down.weight, lora_up.weight, alpha)
            if ".lora_down.weight" in suffix:
                module_path = suffix.replace(".lora_down.weight", "")
                weight_type = "lora_down.weight"
            elif ".lora_up.weight" in suffix:
                module_path = suffix.replace(".lora_up.weight", "")
                weight_type = "lora_up.weight"
            elif ".alpha" in suffix:
                module_path = suffix.replace(".alpha", "")
                weight_type = "alpha"
            else:
                print(f"  [skip] Unknown weight type: {key}")
                skipped += 1
                new_state_dict[key] = value
                continue

            # Convert underscore-separated module path to dot-separated
            # e.g., down_blocks_0_attentions_0_... → down_blocks.0.attentions.0...
            parts = module_path.split("_")
            dot_parts = []
            i = 0
            while i < len(parts):
                part = parts[i]
                # Check if next part is a number (layer index)
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    dot_parts.append(part)
                    dot_parts.append(parts[i + 1])
                    i += 2
                else:
                    dot_parts.append(part)
                    i += 1

            module_dotted = ".".join(dot_parts)

            # Handle common sub-patterns that use underscores within names
            # e.g., "to_q" "to_k" "to_v" "to_out" "proj_in" "proj_out"
            for pattern in ["to.q", "to.k", "to.v", "to.out", "proj.in", "proj.out",
                          "ff.net", "group.norm"]:
                underscore_ver = pattern.replace(".", "_")
                if f".{underscore_ver}." in f".{module_dotted}." or module_dotted.endswith(f".{underscore_ver}"):
                    # Only replace when it's a known multi-word identifier
                    pass  # These are actually correct with underscores in diffusers too

            new_key = f"unet.{module_dotted}.{weight_type}"

        elif key.startswith("lora_te_"):
            # Text encoder LoRA weights
            suffix = key[len("lora_te_"):]
            new_key = f"text_encoder.{suffix}"

        else:
            # Not a kohya key, pass through
            new_key = key

        if new_key:
            new_state_dict[new_key] = value
            if new_key != key:
                converted += 1
            else:
                skipped += 1

    return new_state_dict, converted, skipped


def convert_to_peft_format(state_dict):
    """
    Alternative: convert to PEFT-compatible format that newer diffusers expects.
    Keys like: base_model.model.unet.down_blocks.0.attentions.0...lora_A.weight
    """
    new_state_dict = {}
    converted = 0

    for key, value in state_dict.items():
        new_key = key

        if key.startswith("lora_unet_"):
            suffix = key[len("lora_unet_"):]

            # Determine weight type
            if ".lora_down.weight" in suffix:
                module_path = suffix.replace(".lora_down.weight", "")
                weight_suffix = "lora_A.weight"
            elif ".lora_up.weight" in suffix:
                module_path = suffix.replace(".lora_up.weight", "")
                weight_suffix = "lora_B.weight"
            elif ".alpha" in suffix:
                module_path = suffix.replace(".alpha", "")
                weight_suffix = "alpha"
            else:
                new_state_dict[key] = value
                continue

            # Convert underscored module path to dotted
            # We need to be careful: "down_blocks_0" → "down_blocks.0"
            # but "to_q" stays as "to_q", "to_out_0" → "to_out.0"
            module_dotted = _underscore_to_dot(module_path)
            new_key = f"base_model.model.unet.{module_dotted}.{weight_suffix}"
            converted += 1

        elif key.startswith("lora_te_"):
            suffix = key[len("lora_te_"):]

            if ".lora_down.weight" in suffix:
                module_path = suffix.replace(".lora_down.weight", "")
                weight_suffix = "lora_A.weight"
            elif ".lora_up.weight" in suffix:
                module_path = suffix.replace(".lora_up.weight", "")
                weight_suffix = "lora_B.weight"
            elif ".alpha" in suffix:
                module_path = suffix.replace(".alpha", "")
                weight_suffix = "alpha"
            else:
                new_state_dict[key] = value
                continue

            module_dotted = _underscore_to_dot(module_path)
            new_key = f"base_model.model.text_encoder.{module_dotted}.{weight_suffix}"
            converted += 1

        new_state_dict[new_key] = value

    return new_state_dict, converted


def _underscore_to_dot(path):
    """
    Convert kohya underscore-separated path to dot-separated.
    Handles tricky cases like to_q, to_k, to_v, to_out, proj_in, proj_out, ff_net.
    """
    # Known compound names that should keep underscores
    compounds = {
        "to_q", "to_k", "to_v", "to_out", "proj_in", "proj_out",
        "ff_net", "group_norm", "conv_shortcut", "conv_in", "conv_out",
        "time_emb_proj", "linear_1", "linear_2",
    }

    parts = path.split("_")
    result = []
    i = 0

    while i < len(parts):
        # Check for compound names (2-word)
        if i + 1 < len(parts):
            two_word = f"{parts[i]}_{parts[i+1]}"
            if two_word in compounds:
                result.append(two_word)
                i += 2
                continue

        # Check if this part is a number (layer index → use dot separator)
        if parts[i].isdigit():
            result.append(parts[i])
            i += 1
            continue

        # Regular module name
        result.append(parts[i])
        i += 1

    return ".".join(result)


def main():
    parser = argparse.ArgumentParser(description="Convert kohya LoRA to diffusers format")
    parser.add_argument("input", help="Input .safetensors file (kohya format)")
    parser.add_argument("--output", "-o", help="Output file (default: adds _diffusers suffix)")
    parser.add_argument("--format", choices=["diffusers", "peft"], default="diffusers",
                       help="Target format: 'diffusers' (unet.* prefix) or 'peft' (base_model.model.* prefix)")
    parser.add_argument("--dry-run", action="store_true", help="Show key mappings without saving")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_name(
            input_path.stem + f"_{args.format}" + input_path.suffix
        )

    print(f"Loading: {input_path}")
    state_dict = load_file(str(input_path))
    print(f"  {len(state_dict)} weight tensors loaded")

    # Show a few original keys
    sample_keys = list(state_dict.keys())[:5]
    print(f"\n  Sample original keys:")
    for k in sample_keys:
        print(f"    {k}")

    # Check if already in diffusers format
    if any(k.startswith("unet.") or k.startswith("base_model.") for k in state_dict.keys()):
        print("\n  LoRA appears to already be in diffusers/PEFT format!")
        print("  If style still isn't showing, the issue is elsewhere.")
        sys.exit(0)

    # Convert
    if args.format == "peft":
        new_state_dict, converted = convert_to_peft_format(state_dict)
        skipped = len(state_dict) - converted
    else:
        new_state_dict, converted, skipped = convert_kohya_to_diffusers(state_dict)

    print(f"\n  Converted: {converted} keys")
    print(f"  Unchanged: {skipped} keys")

    # Show sample converted keys
    sample_new = list(new_state_dict.keys())[:5]
    print(f"\n  Sample converted keys:")
    for k in sample_new:
        print(f"    {k}")

    if args.dry_run:
        print("\n  [dry-run] No file written.")
        # Show full mapping
        print("\n  Full key mapping:")
        for old_key in sorted(state_dict.keys()):
            new_key = [k for k, v in new_state_dict.items()
                      if v is state_dict[old_key]]
            if new_key:
                if new_key[0] != old_key:
                    print(f"    {old_key}")
                    print(f"      → {new_key[0]}")
        return

    print(f"\n  Saving: {output_path}")
    save_file(new_state_dict, str(output_path))
    print(f"  Done! {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\n  Replace the old LoRA in StreamDiffusionTD with this file.")
    print(f"  Set LoRA weight to 1.0 and test again.")


if __name__ == "__main__":
    main()
