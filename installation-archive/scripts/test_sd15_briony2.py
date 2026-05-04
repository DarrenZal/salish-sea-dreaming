"""Test Briony v1 LoRA on SD 1.5 with 20-step DDIM (diffusers 0.24 compatible)."""
import torch
from diffusers import StableDiffusionPipeline, DDIMScheduler

print("Loading SD 1.5...")
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
)
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("cuda")

print("Loading Briony LoRA...")
pipe.load_lora_weights("C:/Users/user/Desktop/briony_watercolor_v1.safetensors")
print("LoRA loaded.")

prompts = [
    ("01_coast", "brionypenn pacific northwest coast dawn mist watercolor"),
    ("02_orca",  "brionypenn orca whale breaching ocean watercolor"),
    ("03_kelp",  "brionypenn kelp forest underwater sunlight watercolor"),
]

gen = torch.Generator(device="cuda").manual_seed(42)
for slug, prompt in prompts:
    print(f"Generating {slug}...")
    img = pipe(
        prompt=prompt,
        num_inference_steps=20,
        guidance_scale=7.5,
        generator=gen,
    ).images[0]
    path = f"C:/Users/user/Desktop/briony_test_{slug}.png"
    img.save(path)
    print(f"  Saved {path}")

print("Done.")
