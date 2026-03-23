# Briony Style Transfer — Options & Fallback Guide

*Salish Sea Dreaming — March 2026*

---

The goal: apply Briony Penn's watercolor aesthetic to any input — GAN fish, David's photos, Moonfish footage, live camera. This doc covers every viable approach, ranked by readiness.

> **Status update (March 21):**
> - **SD-Turbo + LoRA:** Does NOT work (blurry at weight 1.0, invisible at low weight).
> - **SD 1.5 + LoRA at 30 steps:** Actually looks decent — watercolor feel, some linework, natural palette. The LoRA works, the problem was the inference pipeline (SD-Turbo + 4 steps), not the LoRA itself.
> - **SD 1.5 + LoRA at 4 steps (StreamDiffusion):** Too few steps for the LoRA to express. Need 8-20 steps minimum.
> - **AdaIN:** Tested March 21 on GAN fish frames + Briony paintings. Transfers color palette but produces texture-pattern artifacts, no linework. The LoRA at 30 steps is actually better.
> - **Key learning:** The LoRA IS the right approach — it just needs more inference steps. SD 1.5 + LoRA + LCM-LoRA (for speed) is the most promising path.

## TL;DR — Priority Stack (Updated March 21)

| Priority | Method | Setup Time | Real-time? | When to reach for it |
|----------|--------|-----------|------------|---------------------|
| **A** | LoRA + SD 1.5 (8-20 steps) | Done (retrain for better) | 1-6 fps | **Best results so far at 30 steps.** Need to find the right step count for real-time. |
| **B** | LoRA + LCM-LoRA combo | Minutes (download LCM) | 3-8 fps (est.) | Speed up SD 1.5 inference to 4-8 steps without losing quality. |
| **C** | LoRA retrain (54 images, rank 32) | 30-60 min | Same | More training data + higher rank → sharper Briony style. |
| **D** | Fast Neural Style (Johnson) | 2-4 hours train | 30+ fps | If LoRA fps is too low for live performance. Purpose-built for real-time. |
| **E** | AdaIN Arbitrary Style | Minutes (pretrained) | 20-40 fps | **Tested March 21 — color transfer OK but texture artifacts, no linework. Weaker than LoRA.** |
| **F** | CycleGAN | 12-24 hours | 30 fps (trained) | Research bet. Deeper structural transformation. |
| **G** | ControlNet + LoRA | Hours | No (pre-render) | Hero sequences from Moonfish footage. Batch overnight. |
| **H** | Classic NST (Gatys) | Minutes | No (30-60s/img) | Guaranteed to work. Pre-render only. |

> **Demoted:** SD-Turbo + LoRA — SD-Turbo's 1-step distillation is incompatible with style LoRAs.
> **Demoted:** AdaIN — tested, produces texture-pattern artifacts rather than Briony's painterly style. Better for color palette transfer than full style transfer.

---

## Option A: LoRA + StreamDiffusion (PRIMARY)

**Status:** The LoRA works well at 30 steps on SD 1.5. The challenge is getting enough inference steps in StreamDiffusion for real-time. SD-Turbo (1-4 steps) is too few — try SD 1.5 at 8-20 steps, or SD-Turbo with txt2img mode (not yet fully tested).

**What we know:**
- SD 1.5 + LoRA at 30 steps = beautiful results ([evaluation page](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html))
- SD 1.5 + LoRA at 4 steps (StreamDiffusion) = too few steps, style barely visible
- SD-Turbo + LoRA in img2img = doesn't work (blurry)
- SD-Turbo + LoRA in **txt2img** = **not yet fully tested** — Prav noted we hadn't tried this before concluding SD-Turbo doesn't work. Worth retesting.

**What to try next:**
1. SD-Turbo + LoRA in **txt2img mode** in StreamDiffusion (quick test)
2. SD 1.5 + LoRA at 8-20 steps in StreamDiffusion
3. LCM-LoRA + Briony LoRA combo on SD 1.5 (4-8 steps with LCM scheduler)

**Files:**
- `briony_watercolor_v1.safetensors` (38 MB) — **SD 1.5 base** ([Download](https://drive.google.com/file/d/1fIFBYGorHjfg76w82AwHOhyiiqptSBGu/view))
- `briony_watercolor_sdturbo.safetensors` (13 MB) — SD-Turbo base (worth retesting in txt2img mode)
- Training config: `briony-lora/train_config.toml`
- Evaluation: `briony-lora/eval/compare-v2.html` ([live](https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html))

**Pipeline:**
```
Any input or prompt → StreamDiffusionTD (LoRA loaded) → TD compositor → Resolume → Projection
```

**Key settings:**
- Base model: `runwayml/stable-diffusion-v1-5` (or `sd-turbo` for txt2img retest)
- Mode: **both txt2img and img2img work** — txt2img for prompt-driven generation, img2img for styling input
- Trigger token: `brionypenn`
- Prompt: `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`
- Strength: `0.45` (sweet spot — dial 0.35-0.55 to taste)
- LoRA weight: `1.0` (full effect)

**Performance:** 6 fps on RTX 3060, potentially 10-15 fps on RTX 3090 with TensorRT.

**Detailed setup:** See `docs/prav-lora-integration-guide.md`

**Risks:**
- TensorRT build fails on the RTX 3090
- StreamDiffusionTD version mismatch with TD 2025
- Latency too high for live performance

---

## Option B: IP-Adapter (Zero-Shot Style Reference)

**What it is:** Uses a pre-trained image encoder to inject the "style" of a reference image into Stable Diffusion at inference time. No LoRA, no training — just point it at a Briony painting.

**Setup:**
```bash
pip install diffusers transformers accelerate
# Download IP-Adapter model (~1.5 GB, one-time)
```

**Usage (Python):**
```python
from diffusers import StableDiffusionPipeline
from diffusers.utils import load_image
import torch

# Load pipeline with IP-Adapter
pipe = StableDiffusionPipeline.from_pretrained(
    "stabilityai/sd-turbo", torch_dtype=torch.float16
).to("cuda")
pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")

# Briony painting as style reference
style_image = load_image("path/to/briony_watercolor.jpg")

# Any content image (GAN fish, photo, etc.)
content_image = load_image("path/to/fish.jpg")

# Generate styled output
result = pipe(
    prompt="watercolor painting of marine life",
    ip_adapter_image=style_image,
    image=content_image,
    strength=0.45,
    num_inference_steps=4,  # SD-Turbo is fast
).images[0]
result.save("styled_output.png")
```

**Quality:** Good "watercolor-ish" but less specifically Briony. Captures her palette and softness but not her exact brushwork. Good enough for a backup.

**Speed:** Similar to LoRA — depends on the diffusion pipeline.

**When to use:** The LoRA file causes errors, or you want to quickly test a different Briony painting as the reference without retraining.

**TD integration:** Run as a Python subprocess, or use ComfyUI as middleware with its IP-Adapter node.

---

## Option C: Fast Neural Style Transfer (Johnson et al. 2016)

**What it is:** A small feedforward neural network trained to apply ONE specific style. Once trained (~2-4 hours), it applies the style in a single forward pass — extremely fast.

**This is the best real-time fallback if StreamDiffusion breaks entirely.**

**Setup:**
```bash
# Clone PyTorch's official examples
git clone https://github.com/pytorch/examples.git
cd examples/fast_neural_style

pip install torch torchvision pillow
```

**Train a Briony style network:**
```bash
# Train on COCO dataset with Briony painting as style
# Takes 2-4 hours on RTX 3090
python neural_style/neural_style.py train \
    --dataset path/to/coco-train2017/ \
    --style-image path/to/briony_watercolor.jpg \
    --save-model-dir saved_models/ \
    --epochs 2 \
    --cuda 1 \
    --content-weight 1e5 \
    --style-weight 1e10
```

**Apply the style (real-time capable):**
```bash
python neural_style/neural_style.py eval \
    --content-image fish.jpg \
    --model saved_models/briony_style.model \
    --output-image styled_fish.jpg \
    --cuda 1
```

**For real-time video processing:**
```python
import torch
from torchvision import transforms
import cv2

# Load trained style model
style_model = torch.load("saved_models/briony_style.model")
style_model.eval().cuda()

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Lambda(lambda x: x.mul(255))
])

cap = cv2.VideoCapture(0)  # or NDI input
while True:
    ret, frame = cap.read()
    tensor = transform(frame).unsqueeze(0).cuda()
    with torch.no_grad():
        output = style_model(tensor)
    # output → display or send via NDI
```

**Quality:** Recognizable painterly effect but somewhat "flat" — captures color and texture patterns but lacks the structural intelligence of diffusion models. Think "Prisma filter" level.

**Speed:** 30-100+ fps on RTX 3090 at 512x512. The fastest option by far.

**When to use:** StreamDiffusion completely broken, need real-time style transfer with minimal dependencies.

---

## Option D: AdaIN — Arbitrary Style Transfer (Huang & Belongie 2017)

**What it is:** Adaptive Instance Normalization. Takes ANY content image + ANY style image, applies style in a single forward pass. No training per style — one pretrained model handles all styles.

**Setup:**
```bash
git clone https://github.com/naoto0804/pytorch-AdaIN.git
cd pytorch-AdaIN

# Download pretrained models
bash download_models.sh
# or manually: decoder.pth + vgg_normalised.pth
```

**Usage:**
```bash
python test.py \
    --content input/fish.jpg \
    --style input/briony_watercolor.jpg \
    --output output/styled.jpg \
    --alpha 0.8  # 0.0 = pure content, 1.0 = pure style
```

**For real-time with adjustable blend:**
```python
import torch
from PIL import Image
import net  # from pytorch-AdaIN

decoder = net.decoder
vgg = net.vgg
decoder.load_state_dict(torch.load("models/decoder.pth"))
vgg.load_state_dict(torch.load("models/vgg_normalised.pth"))
decoder.eval().cuda()
vgg.eval().cuda()

# Style can be swapped live — MIDI-controlled blending between
# different Briony paintings?
style_1 = load_and_encode("briony_herring.jpg")
style_2 = load_and_encode("briony_salmon.jpg")

# Interpolate between styles
blended_style = style_1 * (1 - midi_value) + style_2 * midi_value
output = decoder(adain(content_features, blended_style))
```

**Quality:** Better color transfer than fast NST, decent texture mapping. The `alpha` parameter controls style intensity — similar to LoRA weight.

**Speed:** 20-40 fps on RTX 3090 at 512x512.

**Unique advantage:** Can blend between multiple Briony paintings in real-time. Imagine a MIDI fader that smoothly transitions from her herring painting to her salmon painting — the style itself morphs.

**When to use:** Want live style blending between different reference images, or LoRA quality isn't right and you want a different aesthetic.

---

## Option E: ControlNet + LoRA (Pre-Rendered Hero Sequences)

**What it is:** ControlNet extracts structural information (edges, depth) from source footage, then the LoRA applies Briony's style while preserving that structure. Highest quality, but too slow for real-time.

**Pipeline:**
```
Moonfish herring footage
    → extract frames (ffmpeg)
    → ControlNet Canny edge detection
    → SD img2img with Briony LoRA + ControlNet guidance
    → reassemble as video
    → play in Resolume as a layer
```

**Setup (ComfyUI recommended):**
```bash
# Install ComfyUI + ControlNet
cd ComfyUI
pip install -r requirements.txt

# Download ControlNet canny model
# Place Briony LoRA in models/loras/
# Build workflow: Load Video → Canny → KSampler (LoRA) → Save Frames
```

**Batch processing script:**
```bash
# Extract frames
ffmpeg -i moonfish_herring.mp4 -vf fps=24 frames/frame_%04d.png

# Process each frame through ControlNet + LoRA
# (use ComfyUI API or diffusers pipeline)
# ~2-5 seconds per frame, 24 fps video = ~2-5 min per second of footage

# Reassemble
ffmpeg -framerate 24 -i styled/frame_%04d.png -c:v libx264 -pix_fmt yuv420p styled_herring.mp4
```

**Quality:** The highest quality option. Moonfish underwater footage that genuinely looks like Briony painted it, with accurate structural detail preserved.

**Speed:** 2-5 seconds per frame. Pre-render overnight.

**When to use:** Have specific hero footage (Moonfish, David) that needs to look exceptional. Pre-render key sequences, play as video layers in Resolume alongside real-time content.

---

## Option F: Classic Neural Style Transfer (Gatys et al. 2015)

**What it is:** The original — iteratively optimizes a single image to match the content of one image and the style of another, using VGG19 feature matching. The "older Python method."

**Setup:**
```bash
pip install torch torchvision pillow
```

**Usage — minimal script (~50 lines):**
```python
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from PIL import Image

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load images
def load_image(path, size=512):
    img = Image.open(path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize(size),
        transforms.CenterCrop(size),
        transforms.ToTensor(),
    ])
    return transform(img).unsqueeze(0).to(device)

content_img = load_image("fish.jpg")
style_img = load_image("briony_watercolor.jpg")

# VGG19 features
vgg = models.vgg19(pretrained=True).features.to(device).eval()

# Content and style layers
content_layers = [21]       # conv4_2
style_layers = [0, 5, 10, 19, 28]  # conv1_1 through conv5_1

def gram_matrix(x):
    b, c, h, w = x.size()
    features = x.view(b * c, h * w)
    G = torch.mm(features, features.t())
    return G.div(b * c * h * w)

def get_features(img, model, layers):
    features = {}
    x = img
    for i, layer in enumerate(model):
        x = layer(x)
        if i in layers:
            features[i] = x
    return features

content_features = get_features(content_img, vgg, content_layers)
style_features = get_features(style_img, vgg, style_layers)
style_grams = {l: gram_matrix(f) for l, f in style_features.items()}

# Optimize
output = content_img.clone().requires_grad_(True)
optimizer = optim.LBFGS([output])

for step in range(300):
    def closure():
        output.data.clamp_(0, 1)
        optimizer.zero_grad()
        out_features = get_features(output, vgg, content_layers + style_layers)

        content_loss = nn.functional.mse_loss(
            out_features[21], content_features[21]
        )

        style_loss = 0
        for l in style_layers:
            style_loss += nn.functional.mse_loss(
                gram_matrix(out_features[l]), style_grams[l]
            )

        loss = content_loss * 1 + style_loss * 1e6
        loss.backward()
        return loss

    optimizer.step(closure)

# Save
transforms.ToPILImage()(output.squeeze(0).clamp(0, 1).cpu()).save("styled.png")
```

**Quality:** Distinctive, recognizable, artistic. Each image is uniquely optimized. Results have a specific "neural style transfer" look that became iconic circa 2016.

**Speed:** 30-60 seconds per image on GPU. Not real-time.

**When to use:** Last resort, or when you want a very specific artistic quality for a single important image (e.g., the exhibition poster).

---

## Option G: CycleGAN (Unpaired Domain Translation)

**What it is:** Learns a bidirectional mapping between "photo domain" and "Briony watercolor domain" without needing paired examples. The network learns what makes a Briony watercolor different from a photo.

**Setup:**
```bash
git clone https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix.git
cd pytorch-CycleGAN-and-pix2pix
pip install -r requirements.txt
```

**Prepare dataset:**
```
datasets/briony2photo/
    trainA/  ← Briony watercolors (54 images)
    trainB/  ← Marine photos (378+ images from fish corpus)
    testA/
    testB/
```

**Train:**
```bash
python train.py --dataroot ./datasets/briony2photo \
    --name briony_style --model cycle_gan \
    --pool_size 50 --no_dropout \
    --n_epochs 100 --n_epochs_decay 100
# ~12-24 hours on RTX 3090
```

**Apply:**
```bash
python test.py --dataroot ./datasets/briony2photo \
    --name briony_style --model cycle_gan \
    --phase test --no_dropout
```

**Quality:** Can produce striking results — learns genuine structural transformations (not just color/texture overlay). But unpredictable — sometimes produces artifacts or mode collapse.

**Speed:** Real-time inference once trained (~30 fps).

**When to use:** Want something fundamentally different from LoRA's approach — a deeper structural transformation rather than a surface-level style filter.

---

## Option H: DreamBooth (Full SD Fine-Tune)

**What it is:** Fine-tunes the entire Stable Diffusion model (not just a LoRA adapter) on Briony's images. More expressive but higher risk of overfitting.

**Setup:**
```bash
pip install diffusers accelerate transformers bitsandbytes
```

**Train:**
```bash
accelerate launch train_dreambooth.py \
    --pretrained_model_name_or_path="stabilityai/sd-turbo" \
    --instance_data_dir="./briony-lora/" \
    --instance_prompt="a brionypenn watercolor painting" \
    --output_dir="./dreambooth-briony" \
    --resolution=512 \
    --train_batch_size=1 \
    --gradient_accumulation_steps=1 \
    --learning_rate=5e-6 \
    --max_train_steps=800 \
    --mixed_precision="fp16"
```

**Quality:** Potentially higher fidelity than LoRA — the model fully adapts to Briony's style. But with only 22-54 images, risk of overfitting (generating Briony's exact paintings instead of new ones in her style).

**Speed:** Same as LoRA once trained — inference through SD pipeline.

**When to use:** LoRA output feels "too generic" — DreamBooth can capture more subtle stylistic details.

---

## Option I: Cloud Services (OpenArt, Civitai)

**OpenArt:** Upload Briony's images, train a custom model through their web UI. Simple but less control.

**Civitai:** Community models + training. Could train and share a Briony LoRA publicly (check with Briony about image rights first).

**When to use:** All local environments are broken and you need a model fast.

---

## Decision Tree

```
Need real-time style transfer?
├── Yes → Is StreamDiffusion working?
│   ├── Yes → Option A (LoRA + StreamDiffusion) ✓
│   └── No → Is PyTorch working on the GPU?
│       ├── Yes → Option C (Fast Neural Style) — train 2-4 hrs, then 30+ fps
│       └── No → Fix GPU setup first
│
└── No (pre-rendered is fine) →
    ├── Want highest quality? → Option E (ControlNet + LoRA)
    ├── Want quick test? → Option F (Classic NST) — works in 50 lines
    └── Want structural transformation? → Option G (CycleGAN) — train overnight
```

## What's Currently Working

- [x] LoRA trained (SD 1.5 + SD-Turbo variants)
- [x] LoRA merged into TouchDiffusion on RTX 3090
- [x] img2img tested: 20 GAN frames × 5 strengths, sweet spot 0.45
- [x] Temporal coherence confirmed stable
- [x] Integration guide written for Prav: `docs/prav-lora-integration-guide.md`
- [ ] TensorRT build on RTX 3090 (needs GUI — Phase 7)
- [ ] Live projector test at exhibition scale

## References

- [StreamDiffusion](https://github.com/cumulo-autumn/StreamDiffusion) — real-time diffusion pipeline
- [StreamDiffusion v2](https://streamdiffusionv2.github.io/) — next generation
- [dotsimulate StreamDiffusionTD](https://dotsimulate.com/docs/streamdiffusiontd) — TouchDesigner integration
- [PyTorch Fast Neural Style](https://github.com/pytorch/examples/tree/main/fast_neural_style) — Johnson et al. implementation
- [pytorch-AdaIN](https://github.com/naoto0804/pytorch-AdaIN) — Arbitrary style transfer
- [CycleGAN](https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix) — Unpaired image translation
- [IP-Adapter](https://ip-adapter.github.io/) — Zero-shot style reference
- [Prav's reference](https://medium.com/@jamesonthecrow/20-minute-masterpiece-4b6043fdfff5) — "20 Minute Masterpiece"
