# Briony LoRA Integration Guide for Prav

**Date:** 2026-03-18
**From:** Darren
**Status:** LoRA trained, tested, and validated. Ready for pipeline integration.

## TL;DR

We trained a LoRA that applies Briony Penn's watercolor style to any image. It works as a post-processing "Briony filter" on StyleGAN fish output. You can use it in **two ways**:

1. **Autolume only** — Load `fish-network-snapshot-000200.pkl` and run GAN fish generation as-is (no LoRA, no watercolor style)
2. **Autolume + LoRA filter** — Capture Autolume frames, run them through the LoRA via StreamDiffusion or img2img, get Briony-styled fish

Option 1 is ready now. Option 2 needs StreamDiffusion integration (see below).

## What's on Google Drive

All in the [shared folder](https://drive.google.com/drive/folders/17QVEYgmEZDYupWI4vGF2QicXSVKWfk_6):

| File | Size | What it is |
|------|------|------------|
| `fish-network-snapshot-000200.pkl` | 347 MB | Fish species StyleGAN2 checkpoint (200 kimg, 378 QC'd images, 13 species). Load in Autolume. |
| `briony_watercolor_v1.safetensors` | 38 MB | Briony Penn watercolor LoRA (SD 1.5 base, rank 16, 1000 steps). |
| `sample-telus200_007_original.png` | — | Example: raw GAN fish frame |
| `sample-telus200_007_s0.45.png` | — | Example: same frame with Briony LoRA applied at strength 0.45 |
| `sample-styled_s0.45_sequence.gif` | — | GIF showing LoRA applied across multiple frames (temporal coherence test) |

## What's on GitHub

```bash
git pull origin main
```

Key files in `briony-lora/`:
- `test_img2img.py` — Batch img2img script (works standalone with diffusers)
- `extract_frames.py` — Slice fakes grids into individual 512x512 PNGs
- `evaluate_lora.py` — Generate evaluation images across subjects
- `eval/compare.html` — Side-by-side eval viewer (LoRA vs base model)
- `eval/img2img_compare.html` — img2img results viewer (references images in eval/img2img/ which are local-only, ~120 images)
- `train_config.toml` — Training config (for reference/reproducibility)

## Option 1: Autolume Only (No LoRA)

You already have Autolume running. Just load the new fish checkpoint:

1. Download `fish-network-snapshot-000200.pkl` from Drive
2. In Autolume, load the PKL (same process as when you tested the base model)
3. The fish model generates fish at 512x512 — you should see recognizable fish species
4. NDI output to TouchDesigner as before

**Note:** This is still early training (200 of 1000 kimg). Better checkpoints coming March 22-23. Fish shapes should be recognizable but not fully converged.

## Option 2: Autolume + Briony LoRA Filter

This is the pipeline we're aiming for:

```
Autolume (fish PKL) ──NDI──> TouchDesigner ──Spout/NDI──> StreamDiffusion (LoRA) ──> back to TD ──> Resolume
```

### How the LoRA works

- **Base model:** Stable Diffusion 1.5
- **Trigger token:** `brionypenn` — include this in the prompt to activate the style
- **img2img strength:** Controls how much watercolor style vs original composition
  - `0.25` — Very subtle, barely noticeable
  - `0.35` — Light watercolor wash, composition fully preserved
  - **`0.45` — Sweet spot** — clear Briony aesthetic, fish still recognizable
  - `0.55` — Heavy watercolor, composition starts to drift
  - `0.65` — Very painterly, subject may reshape

### Quick test (standalone, no Autolume needed)

If you have Python + PyTorch + CUDA on your machine:

```bash
pip install diffusers transformers accelerate peft pillow

python -c "
import torch
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    'runwayml/stable-diffusion-v1-5', torch_dtype=torch.float16, safety_checker=None
).to('cuda')
pipe.load_lora_weights('briony_watercolor_v1.safetensors')

# Use any image as input — a photo, a GAN frame, anything
img = Image.open('your_input.png').convert('RGB').resize((512, 512))
result = pipe(
    'brionypenn watercolor painting, soft edges, natural pigment, ecological illustration',
    image=img, strength=0.45, num_inference_steps=30, guidance_scale=7.5
).images[0]
result.save('briony_styled.png')
"
```

### StreamDiffusion integration (real-time path)

If you already have StreamDiffusion set up, the LoRA can be loaded into it:

```python
from streamdiffusion import StreamDiffusion

stream = StreamDiffusion(
    model_id_or_path="runwayml/stable-diffusion-v1-5",
    lora_dict={"briony_watercolor_v1.safetensors": 1.0},
    t_index_list=[30, 35, 40, 45],  # adjust for speed vs quality
    torch_dtype=torch.float16,
    mode="img2img",
)
stream.prepare(
    prompt="brionypenn watercolor painting, soft edges, natural pigment",
    guidance_scale=1.2,  # lower for StreamDiffusion
    delta=0.5,  # denoise strength
)

# In your frame loop:
styled_frame = stream(input_frame)
```

**Expected performance with StreamDiffusion:** Should be faster than our 0.97s/frame batch results — StreamDiffusion is optimized for streaming with ~5-15 fps depending on config. This would make real-time viable.

### TouchDesigner routing

For the TD integration, the frame capture → style → return loop would be:

1. **Capture Autolume NDI frame** in TD using NDI In TOP
2. **Send to StreamDiffusion** via Spout Out TOP or shared GPU texture
3. **Receive styled frame** back via Spout In TOP
4. **Composite** in TD (blend styled + original, crossfade, etc.)
5. **Output** to Resolume via NDI Out TOP or Spout

The StreamDiffusion TOX component (if you have it) can handle steps 2-3 as a single node.

## What we tested and learned

### Performance (RTX 3090, batch mode)
- **Average latency:** 0.97 seconds per frame
- **Min:** 0.60s (strength 0.25), **Max:** 1.34s (strength 0.65)
- **~1 fps** in batch mode — not real-time, but StreamDiffusion should be faster

### Style quality
- LoRA successfully learned Briony's watercolor aesthetic (soft edges, natural pigment blending, ecological palette)
- Style generalizes — works on marine, land, and atmospheric subjects, not just the training images
- At strength 0.45, fish compositions from the GAN are preserved while getting a clear watercolor treatment

### Temporal coherence
- Tested on 15 consecutive GAN frames
- Style application is consistent across frames — no shimmer or flicker
- Safe for video/exhibition use

## Questions for Wednesday jam

1. **Real-time vs pre-rendered?** At ~1 fps batch, we could pre-render styled sequences overnight. With StreamDiffusion, might get 5-15 fps real-time. Which approach for the exhibition?
2. **Strength preference?** Look at the sample images — is 0.45 the right balance, or should we go lighter/heavier?
3. **Pipeline routing?** Where exactly does the LoRA filter sit in your TD patch? Before or after boids? Before or after Resolume?
4. **Multiple styles?** We could train additional LoRAs (e.g., different Briony painting subsets, or other artists) and blend/switch between them.
