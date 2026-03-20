# Prav Handoff — Briony Style Transfer & Exhibition Build

*Darren — March 20, 2026*
*I'm away March 20–28. Here's everything about where we are with the Briony style transfer and what to try next.*

---

## What We Tried (March 19 session)

We spent the evening testing the Briony LoRA in StreamDiffusionTD on your RTX 3060 laptop. Here's what happened:

### SD-Turbo + LoRA: Doesn't work
- The LoRA at low weight (0.04, 0.42) had no visible effect
- At weight 1.0 it made everything blurry and incoherent
- **Root cause:** SD-Turbo is distilled for 1-step generation. Adding a style LoRA pushes it off its equilibrium — there aren't enough inference steps for the LoRA to express itself without destroying the image

### SD 1.5 + LoRA + 4 steps: Partially works
- Switched base model to SD 1.5 (`runwayml/stable-diffusion-v1-5`)
- Used `briony_watercolor_v1.safetensors` (38 MB — the SD 1.5 version)
- txt2img with prompts like `brionypenn watercolor fish` produced results
- **But** it wasn't obviously Briony's style — more "generic watercolor" than her bold linework and vivid colors
- 4 steps may still be too few for the LoRA to fully express

### What we didn't get to test
- SD 1.5 at higher steps (8, 15, 20) — more steps = more LoRA influence but slower
- LCM-LoRA + Briony LoRA combo
- img2img mode with SD 1.5
- The RTX 3090 desktop
- Any of the fallback approaches (Fast NST, AdaIN, IP-Adapter)

---

## Current State of Files

### On Shared Drive → [Models](https://drive.google.com/drive/folders/1B5hwQEds0Bcg6nHmtNJBcz17xr_E2dr9)

| File | Size | Use with | Status |
|------|------|----------|--------|
| **`briony_watercolor_v1.safetensors`** | 38 MB | **SD 1.5** | **Use this one.** Best results so far. |
| `briony_watercolor_sdturbo.safetensors` | 13 MB | SD-Turbo | Doesn't work well — skip |
| `briony_watercolor_sdturbo_kohya.safetensors` | 13 MB | SD-Turbo | Kohya format conversion — also skip |
| `marine-base-320kimg.pkl` | 364 MB | Autolume | Base GAN model (320 kimg, working) |

### On Shared Drive → [Models/Fish_model](https://drive.google.com/drive/folders/1A5KzChl5mPf42iAcKiHJCCpzSCnAEQDZ)

| File | Size | Status |
|------|------|--------|
| `fish-network-snapshot-000400.pkl` | 347 MB | Latest fish GAN (kimg 400). Load in Autolume. |
| `fish-network-snapshot-000200.pkl` | 347 MB | Earlier checkpoint |
| `fakes000400.png` | 61 MB | Fakes grid — fish shapes emerging clearly |

### On GitHub
- Style transfer guide (9 approaches): [`docs/style-transfer-guide.md`](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/style-transfer-guide.md)
- Honest LoRA evaluation: `briony-lora/eval/compare-v2.html` (open locally)
- LoRA training config: `briony-lora/train_config.toml`

---

## The Core Problem

Briony's art has **bold ink linework, vivid saturated colors (teals, reds, ochres), flat/illustrative perspective**. Open `briony-lora/eval/compare-v2.html` to see her actual paintings next to what the LoRA produces.

The LoRA captures "watercolor softness" but misses:
- Bold dark outlines (her most distinctive feature)
- Vivid color saturation (output is muted by comparison)
- Illustrative composition (cross-sections, ecosystem diagrams)
- Flat perspective (LoRA still produces SD's default photographic depth)

**Why:** 22 training images is small, rank 16 may be too low, and 4 inference steps don't give the LoRA enough room to transform the output.

---

## What to Try Next (Priority Order)

### 1. More inference steps with SD 1.5 (try first)

The single biggest lever. We only tested at 4 steps — the LoRA needs more room.

In StreamDiffusionTD:
- Base model: `runwayml/stable-diffusion-v1-5`
- LoRA: `briony_watercolor_v1.safetensors`, weight **1.0**
- Steps: try **8, then 15, then 20**
- Prompt: `brionypenn watercolor painting of herring swimming, bold ink outlines, vivid teal and coral, ecological illustration`
- Mode: txt2img first (simplest), then img2img

More steps = slower FPS but stronger style. Find the sweet spot where Briony's style is visible and FPS is acceptable.

**Expected FPS on RTX 3060:**
- 4 steps: ~3 fps (what we had)
- 8 steps: ~1.5 fps
- 15 steps: ~0.8 fps
- 20 steps: ~0.5 fps

Even 1 fps might be usable for autonomous installation mode (not live performance).

### 2. LCM-LoRA + Briony LoRA combo

LCM-LoRA is a special LoRA that makes SD 1.5 produce good images in 4-8 steps (instead of 20-30). Stack it with the Briony LoRA:

- Base model: `runwayml/stable-diffusion-v1-5`
- LoRA 1: `latent-consistency/lcm-lora-sdv1-5` (download from HuggingFace, ~67 MB)
- LoRA 2: `briony_watercolor_v1.safetensors`, weight 1.0
- **Scheduler: LCM** (important — change from the default)
- Steps: 4-8
- Guidance scale: 1.0-2.0 (LCM works best with low guidance)

**Check if StreamDiffusionTD supports loading two LoRAs simultaneously.** Look for a LoRA list or "add LoRA" button. If it only supports one, this won't work directly — you'd need to merge them offline.

### 3. Better prompts

The captions we used in training were generic. More specific prompts that describe Briony's actual technique might help:

Instead of:
> `brionypenn watercolor fish`

Try:
> `brionypenn watercolor painting of pacific herring, bold ink outlines, vivid teal water, coral and ochre details, flat ecological illustration, natural pigment on paper, hand-painted, scientific illustration style`

The more you describe Briony's specific characteristics in the prompt, the more the LoRA has to work with.

**Negative prompt:**
> `photograph, photorealistic, 3d render, smooth gradient, digital art, blurry, soft focus`

### 4. Retrain the LoRA (if above doesn't work)

We only used 22 images. There are 54 Briony watercolors prepped in `training-data/briony-marine-colour/`. A retrain with:
- **All 54 images** (not 22)
- **Rank 32 or 64** (not 16) — more capacity for Briony's detail
- **2000-3000 steps** (not 1000)
- **Better captions** that describe her bold linework, vivid colors, flat perspective

Training takes ~30-60 min on the RTX 3090 desktop. Config: `briony-lora/train_config.toml`. Training script: `briony-lora/train.sh`.

To retrain on the RTX 3090:
```bash
# SSH into the desktop
# Activate the training environment
# Edit train_config.toml: change network_dim to 32, max_train_steps to 2000
# Point image_dir to the full 54-image set
# Run training
```

Ask Darren (Signal) if you need help with this — I can walk you through it remotely.

### 5. RTX 3090 desktop

The desktop has more VRAM (24 GB vs 8 GB) and compute. Same workflow but:
- Can handle more inference steps without dropping FPS as much
- Can build TensorRT engine (fuse LoRA into model → compile → faster inference)
- **Phase 7 still needed:** Load TouchDiffusion.tox, run `webui.bat` first time, build TensorRT engine (~10 min)

**TensorRT workflow:**
1. Get the style looking right first (correct LoRA, correct steps, correct weight)
2. Then merge LoRA into SD 1.5 base model
3. Compile TensorRT engine from the merged model
4. Run on the compiled engine — significant speedup

Don't compile TensorRT until the style is locked in — any change means recompiling.

### 6. Alternative approaches (if LoRA doesn't get there)

Full details in [`docs/style-transfer-guide.md`](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/style-transfer-guide.md). Quick summary:

**Fast Neural Style Transfer (best real-time fallback)**
- Train a small feedforward network on one Briony painting
- 2-4 hours to train on RTX 3090, then 30+ fps inference
- Captures bold linework and color better than LoRA (explicitly matches texture statistics)
- Runs in pure PyTorch — no StreamDiffusion needed
- Looks more like a "Prisma filter" but more faithful to Briony's colors

**AdaIN (zero setup)**
- Download pretrained model, no training
- Feed any Briony painting as style reference at runtime
- 20-40 fps on RTX 3090
- Can blend between multiple Briony paintings with a fader
- Less specific than a trained model but might actually look more like Briony than the current LoRA does

**IP-Adapter (zero training, works with SD)**
- Use Briony's paintings as image prompts in SD
- No LoRA needed — the style comes from the reference image at inference time
- Check if StreamDiffusionTD or ComfyUI supports IP-Adapter

**Classic Neural Style Transfer (guaranteed to work)**
- 50 lines of Python, pure PyTorch
- 30-60 seconds per image (not real-time)
- But produces the most faithful style transfer of all methods
- Good for pre-rendering hero sequences to play as video in Resolume

**Animate Briony's actual paintings in TD**
- Instead of generating new images in her style, animate HER paintings
- Pan, zoom, parallax, particle effects, dissolve between paintings
- Most faithful to her actual work (because it IS her work)
- No AI style transfer needed — just TD compositing

### 7. Prav's other items from the task list

These don't depend on the LoRA working:

- **Nano Banana** — you mentioned this as an approach to explore. I don't know what it is — if you have a link or reference, try it
- **OpenArt custom style training** — upload Briony's images to openart.ai, get a trained model back. No-code option.
- **The Medium article** you referenced: https://medium.com/@jamesonthecrow/20-minute-masterpiece-4b6043fdfff5

---

## The Trigger Token

`brionypenn` is a made-up word. During training, every Briony image was captioned starting with `brionypenn watercolor painting...`. The LoRA learned: "when you see `brionypenn`, produce this style."

- **With** `brionypenn` in prompt → LoRA style activates
- **Without** `brionypenn` → LoRA has minimal effect (style leaks slightly but not much)
- It will NOT try to generate a person named Briony

Always include `brionypenn` at the start of your prompt.

---

## Fish GAN Training (TELUS)

Running autonomously, no action needed from you.

- **Current:** kimg ~500 / 1,000 (50%)
- **ETA:** ~March 22
- **Status:** Healthy, no errors, fish shapes emerging clearly
- **Checkpoints:** Every 200 kimg. The kimg 400 checkpoint + fakes grid are on the shared Drive.
- **Arshia's guidance:** If no meaningful results by kimg 500, restart with different gamma. At kimg 400 it looks good — no restart needed.

Darren will download the final checkpoint when it completes and put it on Drive.

---

## Quick Reference

| What | Where |
|------|-------|
| Shared Drive | https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr |
| GitHub repo | https://github.com/DarrenZal/salish-sea-dreaming |
| Style transfer guide | `docs/style-transfer-guide.md` |
| LoRA eval (open locally) | `briony-lora/eval/compare-v2.html` |
| LoRA training config | `briony-lora/train_config.toml` |
| TELUS Jupyter API | `https://salishsea-0b50s.paas.ai.telus.com` (token in `.env`) |
| Briony's 54 watercolors | `training-data/briony-marine-colour/` |
| 22 training images + captions | `briony-lora/*.png` + `briony-lora/*.txt` |

**Darren is reachable on Signal.** Happy to screen-share for anything that needs debugging.

---

## Decision to Make This Week

The core question: **is LoRA + StreamDiffusion the right path for Briony's style, or should we pivot?**

If after testing steps 1-3 above the output still doesn't look like Briony's paintings, pivot to one of:
- Fast Neural Style Transfer (2-4 hrs to train, real-time)
- AdaIN (zero setup, real-time)
- Animate Briony's actual paintings directly in TD

Any of these can be ready before April 10. Better to pivot early than keep pushing a pipeline that doesn't capture her aesthetic.
