# Briony LoRA Filter — Setup Guide

**Date:** 2026-03-18
**From:** Darren

We trained a LoRA that paints Briony Penn's watercolor style onto any image. The idea: Autolume generates fish, the LoRA makes them look like Briony painted them.

Check the sample images on Drive to see what it does — compare `sample-telus200_007_original.png` (raw GAN fish) with `sample-telus200_007_s0.45.png` (same fish, Briony-styled).

## Step 1: Download from Google Drive

From the [shared folder](https://drive.google.com/drive/folders/17QVEYgmEZDYupWI4vGF2QicXSVKWfk_6):

| File | Size | What it is |
|------|------|------------|
| `briony_watercolor_sdturbo.safetensors` | 13 MB | **Use this one.** Briony LoRA trained on SD-Turbo — matches your StreamDiffusionTD base model. |
| `fish-network-snapshot-000200.pkl` | 347 MB | Fish model for Autolume (optional — see note below). |

**Note on the old LoRA:** `briony_watercolor_v1.safetensors` (38 MB) was trained on SD 1.5 and won't work with SD-Turbo — you'll get an "Architecture mismatch" error. Use the `sdturbo` version instead.

## Step 2: Load the LoRA in StreamDiffusionTD

Drop `briony_watercolor_sdturbo.safetensors` into your StreamDiffusionTD LoRA models folder (same place you put the old one).

In your StreamDiffusion component inside TouchDesigner:

1. **Base model:** Keep `sd-turbo` — the LoRA is trained on it.

2. **Set img2img mode** — the LoRA needs to receive frames as input and style them. If it's in txt2img mode it will generate from scratch instead of styling input.

3. **LoRA:** Select `briony_watercolor_sdturbo.safetensors`, weight `1.0` (or dial down to taste).

4. **Prompt:** `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`

5. **Strength/delta:** Start at `0.45`.

### About the prompt

`brionypenn` is a made-up trigger token — SD-Turbo has no idea what it means by default. During training, every image was captioned with `brionypenn watercolor painting...`, so the LoRA learned: "when you see `brionypenn`, apply this watercolor style." It won't try to generate a person. Without `brionypenn` in the prompt, the LoRA has no effect.

## Step 3: Feed it input

You can feed anything into the img2img input:

- **Autolume NDI** — GAN-generated fish get the Briony watercolor treatment
- **Camera / Kinect** — visitors become part of a Briony watercolor (interactive)
- **Any video / image source** — everything gets styled

```
Input source ──> StreamDiffusion (LoRA) ──> composite ──> Resolume
```

If using Autolume, load `fish-network-snapshot-000200.pkl` and route the NDI into StreamDiffusion's img2img input. But any input works — the LoRA styles whatever it receives.

## Tuning

**LoRA weight** — controls how much Briony style is applied:
- `0.4` — Subtle watercolor wash
- **`1.0` — Full effect** (start here)
- You already had it at 0.44 in your last run, try higher

**Strength/delta** — controls how much the output differs from the input:
- `0.35` — Light, input very recognizable
- **`0.45` — Recommended** — clear watercolor style, input still recognizable
- `0.55` — Heavy watercolor, input starts to abstract

## Performance

You were already getting **6 fps** on your RTX 3060 with SD-Turbo. The LoRA shouldn't slow it down much. With TensorRT compiled, could be faster.

Temporal coherence is stable — no shimmer or flicker between frames. Safe for exhibition.

## Questions for Wednesday

- What strength looks best on the projector?
- Where in your TD patch should the filter sit — before or after boids?
- Should we try blending styled + unstyled for a subtler effect?
- Does TensorRT work with the LoRA loaded, or do we need to bake it in first?
