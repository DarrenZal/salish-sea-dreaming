# Briony LoRA Filter — Setup Guide

**Date:** 2026-03-18
**From:** Darren

We trained a LoRA that paints Briony Penn's watercolor style onto any image. The idea: Autolume generates fish, the LoRA makes them look like Briony painted them.

Check the sample images on Drive to see what it does — compare `sample-telus200_007_original.png` (raw GAN fish) with `sample-telus200_007_s0.45.png` (same fish, Briony-styled).

## Step 1: Download two files from Google Drive

From the [shared folder](https://drive.google.com/drive/folders/17QVEYgmEZDYupWI4vGF2QicXSVKWfk_6):

| File | Size | What it is |
|------|------|------------|
| `fish-network-snapshot-000200.pkl` | 347 MB | Fish model for Autolume |
| `briony_watercolor_v1.safetensors` | 38 MB | Briony watercolor LoRA for StreamDiffusion |

## Step 2: Load the fish model in Autolume

Load `fish-network-snapshot-000200.pkl` the same way you loaded the base model before. NDI output to TouchDesigner as usual.

This is early training (200 of 1000 kimg) — fish are recognizable but not fully converged. Better checkpoints coming March 22-23.

## Step 3: Set up the LoRA in StreamDiffusion

The LoRA sits on top of **Stable Diffusion 1.5** and runs in **img2img mode** — it takes a frame in and returns a styled frame.

**Settings:**
- **Base model:** `runwayml/stable-diffusion-v1-5`
- **LoRA file:** `briony_watercolor_v1.safetensors` (weight: 1.0)
- **Prompt:** `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`
- **Strength:** `0.45` (this is the sweet spot — clear watercolor style, fish still recognizable)
- **Mode:** img2img

If StreamDiffusion is a Python process on your machine:

```python
from streamdiffusion import StreamDiffusion

stream = StreamDiffusion(
    model_id_or_path="runwayml/stable-diffusion-v1-5",
    lora_dict={"briony_watercolor_v1.safetensors": 1.0},
    t_index_list=[30, 35, 40, 45],
    torch_dtype=torch.float16,
    mode="img2img",
)
stream.prepare(
    prompt="brionypenn watercolor painting, soft edges, natural pigment, ecological illustration",
    guidance_scale=1.2,
    delta=0.5,
)

# In your frame loop:
styled_frame = stream(input_frame)
```

If it's a TOX component in TouchDesigner, load the LoRA file and set the same prompt/strength in the TOX parameters.

## Step 4: Route it in TouchDesigner

```
Autolume ──NDI──> TD (NDI In TOP) ──> StreamDiffusion (LoRA) ──> TD (composite) ──> Resolume
```

1. Capture Autolume NDI with NDI In TOP
2. Send to StreamDiffusion via Spout Out TOP (or however your StreamDiffusion integration works)
3. Receive styled frame back
4. Composite / mix as needed
5. Output to Resolume

## Tuning the strength

Strength controls how much watercolor style vs how much of the original fish is preserved:

- `0.35` — Light wash, fish very clear
- **`0.45` — Recommended** — Briony aesthetic obvious, fish still recognizable
- `0.55` — Heavy watercolor, fish start to abstract

You can change this live if StreamDiffusion supports it — experiment with what looks best at exhibition scale.

## Performance

We measured 0.97s/frame in batch mode on an RTX 3090. StreamDiffusion should be significantly faster (5-15 fps) since it's optimized for streaming. Temporal coherence is stable — no shimmer or flicker between frames.

## Questions for Wednesday

- What strength looks best on the projector?
- Where in your TD patch should the filter sit — before or after boids?
- Should we try blending styled + unstyled (e.g., 50/50 mix) for a subtler effect?
