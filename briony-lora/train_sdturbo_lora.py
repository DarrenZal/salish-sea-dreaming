#!/usr/bin/env python3
"""
Train Briony LoRA on SD-Turbo base model.

SD-Turbo is what Prav runs in StreamDiffusionTD. Training the LoRA on the
same base model avoids the architecture mismatch error.

Run on Windows RTX 3090:
  python train_sdturbo_lora.py --train-dir <images_dir> --output-dir <output_dir>
"""

import argparse
import os
import torch
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from diffusers import StableDiffusionPipeline, DDPMScheduler
from transformers import CLIPTokenizer
from peft import LoraConfig, get_peft_model
import torch.nn.functional as F


class BrionyDataset(Dataset):
    def __init__(self, image_dir, tokenizer, resolution=512):
        self.image_dir = Path(image_dir)
        self.tokenizer = tokenizer
        self.resolution = resolution

        # Find all image+caption pairs
        self.items = []
        for img_path in sorted(self.image_dir.glob("*.png")):
            txt_path = img_path.with_suffix(".txt")
            if txt_path.exists():
                caption = txt_path.read_text().strip()
            else:
                caption = "brionypenn watercolor painting, soft edges, natural pigment, ecological illustration"
            self.items.append((img_path, caption))

        print(f"Found {len(self.items)} training images")

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        img_path, caption = self.items[idx]
        image = Image.open(img_path).convert("RGB").resize(
            (self.resolution, self.resolution), Image.LANCZOS
        )
        # Normalize to [-1, 1]
        image = torch.tensor(
            list(image.getdata()), dtype=torch.float32
        ).reshape(self.resolution, self.resolution, 3).permute(2, 0, 1) / 127.5 - 1.0

        tokens = self.tokenizer(
            caption, padding="max_length", truncation=True,
            max_length=self.tokenizer.model_max_length, return_tensors="pt"
        )
        return image, tokens.input_ids.squeeze(0)


def train(args):
    device = "cuda"

    print(f"Loading SD-Turbo pipeline: {args.base_model}")
    pipe = StableDiffusionPipeline.from_pretrained(
        args.base_model, torch_dtype=torch.float32, safety_checker=None
    )

    tokenizer = pipe.tokenizer
    text_encoder = pipe.text_encoder.to(device)
    vae = pipe.vae.to(device)
    unet = pipe.unet.to(device)

    # Freeze everything except LoRA layers
    text_encoder.requires_grad_(False)
    vae.requires_grad_(False)

    # Apply LoRA to UNet
    lora_config = LoraConfig(
        r=args.rank,
        lora_alpha=args.rank,
        target_modules=["to_q", "to_k", "to_v", "to_out.0"],
        lora_dropout=0.0,
    )
    unet = get_peft_model(unet, lora_config)
    unet.print_trainable_parameters()

    # Dataset
    dataset = BrionyDataset(args.train_dir, tokenizer, args.resolution)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    # Noise scheduler
    noise_scheduler = DDPMScheduler.from_config(pipe.scheduler.config)

    # Optimizer
    optimizer = torch.optim.AdamW(unet.parameters(), lr=args.learning_rate)

    # Training loop
    unet.train()
    global_step = 0
    num_epochs = args.max_steps // len(dataloader) + 1

    print(f"\nTraining LoRA (rank {args.rank}) on {args.base_model}")
    print(f"Steps: {args.max_steps}, Batch: {args.batch_size}, LR: {args.learning_rate}")
    print(f"Epochs needed: {num_epochs}\n")

    for epoch in range(num_epochs):
        for batch_idx, (images, input_ids) in enumerate(dataloader):
            if global_step >= args.max_steps:
                break

            images = images.to(device)
            input_ids = input_ids.to(device)

            # Encode images to latent space
            with torch.no_grad():
                latents = vae.encode(images).latent_dist.sample() * vae.config.scaling_factor

            # Encode text
            with torch.no_grad():
                encoder_output = text_encoder(input_ids)[0]

            # Add noise
            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, noise_scheduler.config.num_train_timesteps,
                                      (latents.shape[0],), device=device).long()
            noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

            # Predict noise (or v for v-prediction models)
            noise_pred = unet(noisy_latents, timesteps, encoder_output).sample

            # Loss — SD-Turbo uses v-prediction
            if noise_scheduler.config.prediction_type == "v_prediction":
                target = noise_scheduler.get_velocity(latents, noise, timesteps)
            else:
                target = noise

            loss = F.mse_loss(noise_pred, target)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            global_step += 1
            if global_step % 50 == 0:
                print(f"Step {global_step}/{args.max_steps} | Loss: {loss.item():.4f}")

            # Save checkpoint
            if global_step % args.save_every == 0:
                save_lora(unet, pipe, args.output_dir,
                          f"briony_watercolor_sdturbo-step{global_step:05d}")

        if global_step >= args.max_steps:
            break

    # Save final
    save_lora(unet, pipe, args.output_dir, "briony_watercolor_sdturbo")
    print(f"\nTraining complete! Final model saved to {args.output_dir}")


def save_lora(unet, pipe, output_dir, name):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    save_path = out / f"{name}.safetensors"

    # Merge back to diffusers format and save
    unet.save_pretrained(out / "unet_lora_temp")

    # Use pipe's save method for proper diffusers LoRA format
    from peft.utils import get_peft_model_state_dict
    from safetensors.torch import save_file

    state_dict = get_peft_model_state_dict(unet)

    # Convert peft keys to diffusers LoRA format
    diffusers_state = {}
    for key, value in state_dict.items():
        new_key = key.replace("base_model.model.", "")
        new_key = new_key.replace(".lora_A.weight", ".lora_A.weight")
        new_key = new_key.replace(".lora_B.weight", ".lora_B.weight")
        diffusers_state[new_key] = value

    save_file(diffusers_state, str(save_path))
    print(f"  Saved: {save_path} ({save_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Clean up temp dir
    import shutil
    temp = out / "unet_lora_temp"
    if temp.exists():
        shutil.rmtree(temp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Briony LoRA on SD-Turbo")
    parser.add_argument("--train-dir", required=True, help="Directory with training images + .txt captions")
    parser.add_argument("--output-dir", required=True, help="Output directory for LoRA checkpoints")
    parser.add_argument("--base-model", default="stabilityai/sd-turbo")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--save-every", type=int, default=200)
    parser.add_argument("--resolution", type=int, default=512)
    args = parser.parse_args()
    train(args)
