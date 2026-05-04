"""
Quick test: SD 1.5 + LCM LoRA + Briony v1 LoRA on Windows 3090.
Saves 3 images to C:/Users/user/Desktop/briony_test_*.png
"""
import torch
from diffusers import DiffusionPipeline, LCMScheduler

print("Loading SD 1.5...")
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    safety_checker=None,
)
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe = pipe.to("cuda")

# Load LCM LoRA first (enables fast inference)
print("Loading LCM LoRA...")
pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5", adapter_name="lcm")

# Load Briony style LoRA  
print("Loading Briony LoRA...")
pipe.load_lora_weights(
    "C:/Users/user/Desktop",
    weight_name="briony_watercolor_v1.safetensors",
    adapter_name="briony"
)

# Combine both LoRAs
pipe.set_adapters(["lcm", "briony"], adapter_weights=[1.0, 0.8])

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
        num_inference_steps=8,
        guidance_scale=1.0,
        generator=gen,
    ).images[0]
    path = f"C:/Users/user/Desktop/briony_test_{slug}.png"
    img.save(path)
    print(f"  Saved {path}")

print("Done.")
