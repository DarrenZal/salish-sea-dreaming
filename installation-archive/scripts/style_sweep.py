# -*- coding: utf-8 -*-
import time, torch
from pathlib import Path
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline

OUTDIR = Path(r'C:\Users\user\style_compare')
img_in = Image.open(r'C:\Users\user\style_test_input.jpg').convert('RGB').resize((512, 512))
style_ref = Image.open(r'C:\Users\user\Desktop\briony_test_01_coast.png').convert('RGB').resize((512, 512))

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    'runwayml/stable-diffusion-v1-5', torch_dtype=torch.float16, safety_checker=None).to('cuda')
pipe.load_ip_adapter('h94/IP-Adapter', subfolder='models', weight_name='ip-adapter_sd15.bin')

PROMPT = 'watercolor painting, naturalist illustration, Pacific Northwest marine'

# Sweep: ip_adapter_scale x strength
variants = [
    ('D2_ipa020_s040', 0.20, 0.40),
    ('D3_ipa030_s035', 0.30, 0.35),
    ('D4_ipa040_s030', 0.40, 0.30),
    ('D5_ipa025_s030', 0.25, 0.30),
]

for name, ipa_scale, strength in variants:
    pipe.set_ip_adapter_scale(ipa_scale)
    t0 = time.time()
    out = pipe(prompt=PROMPT, image=img_in, ip_adapter_image=style_ref,
               strength=strength, num_inference_steps=25, guidance_scale=7.5).images[0]
    out.save(OUTDIR / (name + '.jpg'), quality=90)
    print('Done %s  scale=%.2f strength=%.2f  %.1fs' % (name, ipa_scale, strength, time.time()-t0))

print('Sweep done')
