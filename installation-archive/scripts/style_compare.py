# -*- coding: utf-8 -*-
"""style_compare.py - Compare 4 style transfer methods on a visitor photo."""
import io, os, sys, time
from pathlib import Path
import torch
from PIL import Image

INPUT  = r'C:\Users\user\style_test_input.jpg'
OUTDIR = Path(r'C:\Users\user\style_compare')
OUTDIR.mkdir(exist_ok=True)

SD15        = 'runwayml/stable-diffusion-v1-5'
SDTURBO     = 'stabilityai/sd-turbo'
BRIONY_LORA = r'C:\Users\user\Desktop\briony_watercolor_sdturbo.safetensors'
BRIONY_LORA_SD15 = r'C:\Users\user\Desktop\briony_watercolor_v1.safetensors'
BRIONY_REF  = r'C:\Users\user\Desktop\briony_test_01_coast.png'
IP_ADAPTER  = 'h94/IP-Adapter'

img_in = Image.open(INPUT).convert('RGB').resize((512, 512))
img_in.save(OUTDIR / '00_input.jpg', quality=90)
print('Input saved')

dtype = torch.float16
device = 'cuda'

# -----------------------------------------------------------------------
# Method A: SD-Turbo + Briony LoRA  strength=0.35  cfg=1.5
# -----------------------------------------------------------------------
print('\n--- Method A: SD-Turbo + Briony LoRA (strength=0.35) ---')
from diffusers import AutoPipelineForImage2Image
pA = AutoPipelineForImage2Image.from_pretrained(SDTURBO, torch_dtype=dtype, variant='fp16').to(device)
try:
    pA.load_lora_weights(BRIONY_LORA)
    print('  LoRA loaded')
except Exception as e: print('  LoRA skipped:', e)
t0 = time.time()
outA = pA(prompt='brionypenn watercolor painting, loose brushwork, naturalist illustration',
          image=img_in, strength=0.35, num_inference_steps=4, guidance_scale=1.5).images[0]
print('  Done in %.1fs' % (time.time()-t0))
outA.save(OUTDIR / 'A_sdturbo_lora_s035.jpg', quality=90)
del pA; torch.cuda.empty_cache()

# -----------------------------------------------------------------------
# Method B: SD-Turbo + Briony LoRA  strength=0.6  cfg=1.5
# -----------------------------------------------------------------------
print('\n--- Method B: SD-Turbo + Briony LoRA (strength=0.6) ---')
pB = AutoPipelineForImage2Image.from_pretrained(SDTURBO, torch_dtype=dtype, variant='fp16').to(device)
try: pB.load_lora_weights(BRIONY_LORA)
except Exception as e: print('  LoRA skipped:', e)
t0 = time.time()
outB = pB(prompt='brionypenn watercolor painting, loose brushwork, naturalist illustration',
          image=img_in, strength=0.6, num_inference_steps=4, guidance_scale=1.5).images[0]
print('  Done in %.1fs' % (time.time()-t0))
outB.save(OUTDIR / 'B_sdturbo_lora_s060.jpg', quality=90)
del pB; torch.cuda.empty_cache()

# -----------------------------------------------------------------------
# Method C: SD 1.5 + LCM scheduler + Briony LoRA v1  strength=0.6
# -----------------------------------------------------------------------
print('\n--- Method C: SD1.5 + LCM + Briony LoRA v1 ---')
from diffusers import LCMScheduler
pC = AutoPipelineForImage2Image.from_pretrained(SD15, torch_dtype=dtype, safety_checker=None).to(device)
pC.scheduler = LCMScheduler.from_config(pC.scheduler.config)
try: pC.load_lora_weights(BRIONY_LORA_SD15)
except Exception as e: print('  LoRA skipped:', e)
t0 = time.time()
outC = pC(prompt='brionypenn watercolor painting, loose expressive brushwork, naturalist illustration, Pacific Northwest',
          image=img_in, strength=0.6, num_inference_steps=8, guidance_scale=1.5).images[0]
print('  Done in %.1fs' % (time.time()-t0))
outC.save(OUTDIR / 'C_sd15_lcm_lora_s060.jpg', quality=90)
del pC; torch.cuda.empty_cache()

# -----------------------------------------------------------------------
# Method D: SD 1.5 + IP-Adapter (Briony painting as style reference)
# -----------------------------------------------------------------------
print('\n--- Method D: SD1.5 + IP-Adapter + Briony reference ---')
from diffusers import StableDiffusionImg2ImgPipeline
pD = StableDiffusionImg2ImgPipeline.from_pretrained(SD15, torch_dtype=dtype, safety_checker=None).to(device)
pD.load_ip_adapter(IP_ADAPTER, subfolder='models', weight_name='ip-adapter_sd15.bin')
pD.set_ip_adapter_scale(0.7)
style_ref = Image.open(BRIONY_REF).convert('RGB').resize((512, 512))
t0 = time.time()
outD = pD(prompt='watercolor painting, naturalist illustration, Pacific Northwest marine',
          image=img_in, ip_adapter_image=style_ref,
          strength=0.5, num_inference_steps=25, guidance_scale=7.5).images[0]
print('  Done in %.1fs' % (time.time()-t0))
outD.save(OUTDIR / 'D_sd15_ipadapter_s050.jpg', quality=90)
del pD; torch.cuda.empty_cache()

print('\nAll done! Results in:', OUTDIR)
for f in sorted(OUTDIR.iterdir()):
    print(' ', f.name)
