# Briony LoRA — Integration Guide

**Date:** 2026-03-20 (updated)
**For:** Team

> **Status update (March 20):** SD-Turbo + LoRA doesn't work (blurry). Use **SD 1.5** with `briony_watercolor_v1.safetensors` instead. See [team handoff](team-handoff-march-2026.md) for full context and next steps.

We trained a LoRA on 22 Briony Penn watercolors that teaches Stable Diffusion her style. It works in two modes: **txt2img** (generate Briony-style scenes from prompts) and **img2img** (paint any input in Briony's style). Both are worth testing at the jam.

---

## Step 1: Download from Shared Drive

From the [shared project folder](https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr) → **Models**:

| File | Size | What it is |
|------|------|------------|
| `briony_watercolor_sdturbo.safetensors` | 13 MB | **Use this one.** Briony LoRA trained on SD-Turbo — matches StreamDiffusionTD base model. |

From **Models → Fish_model** (optional, for img2img with GAN):

| File | Size | What it is |
|------|------|------------|
| `fish-network-snapshot-000400.pkl` | 347 MB | Latest fish GAN checkpoint (kimg 400) for Autolume. |
| `fish-network-snapshot-000200.pkl` | 347 MB | Earlier fish checkpoint (kimg 200). |

**Note on the old LoRA:** `briony_watercolor_v1.safetensors` (38 MB) was trained on SD 1.5 and **won't work** with SD-Turbo — you'll get an "Architecture mismatch" error. Use the `sdturbo` version.

**Note on the RTX 3090 desktop:** The LoRA is already merged into the SD-Turbo base model on this machine (128 layers fused during setup). You may not need to load the .safetensors separately — test if the trigger token `brionypenn` already works in the prompt.

---

## Step 2: Load the LoRA in StreamDiffusionTD

1. Drop `briony_watercolor_sdturbo.safetensors` into your StreamDiffusionTD LoRA models folder (same place you'd put any LoRA).

2. In your StreamDiffusion component inside TouchDesigner:
   - **Base model:** `sd-turbo` — the LoRA is trained on this base.
   - **LoRA:** Select `briony_watercolor_sdturbo.safetensors`, weight `1.0`.
   - **Prompt:** `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`

### About the trigger token

`brionypenn` is a made-up token. SD-Turbo doesn't know what it means by default. During training, every image was captioned with `brionypenn watercolor painting...`, so the LoRA learned: "when you see `brionypenn`, apply this watercolor style." It won't try to generate a person. **Without `brionypenn` in the prompt, the LoRA has minimal effect.**

---

## Step 3: Test Three Modes

### Mode A: txt2img (no GAN, no input — simplest)

Generate Briony-style scenes from prompts alone. No Autolume, no input source needed.

1. Set StreamDiffusion to **txt2img mode**
2. Prompt: `brionypenn watercolor painting of herring swimming through kelp forest, soft edges, natural pigment`
3. Try different subjects:
   - `brionypenn watercolor painting of salmon spawning in a river`
   - `brionypenn watercolor painting of an orca breaching, misty morning`
   - `brionypenn watercolor painting of a great blue heron, coastal marsh`
4. Adjust **guidance scale** to control prompt adherence (try 3.0–7.5)

**Pros:** Simplest setup — one component, no GAN. Full control over what appears via prompting.
**Cons:** SD-Turbo with 1-4 inference steps may produce simpler compositions than img2img. Less organic unpredictability.

```
Prompt ──> StreamDiffusion (LoRA, txt2img) ──> TD ──> Resolume ──> Projection
```

### Mode B: img2img + GAN (Autolume fish → Briony filter)

The GAN provides organic, unpredictable fish forms. The LoRA paints them in Briony's style.

1. Load `fish-network-snapshot-000400.pkl` in Autolume
2. Set Autolume to output via NDI
3. Set StreamDiffusion to **img2img mode**
4. Route Autolume's NDI output into StreamDiffusion's img2img input
5. Prompt: `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`
6. **Strength/delta:** Start at `0.45`

**Pros:** Most organic results — GAN provides living, shifting compositions that no prompt could describe. The LoRA then paints them in Briony's hand.
**Cons:** Two systems running (Autolume + StreamDiffusion). More VRAM, more complexity.

```
Autolume (GAN fish) ──NDI──> StreamDiffusion (LoRA, img2img) ──> TD ──> Resolume
```

### Mode C: img2img + video/photos (no GAN)

Feed David's photos, Moonfish footage, or live camera through the LoRA filter.

1. Set StreamDiffusion to **img2img mode**
2. Route your input source into StreamDiffusion:
   - **Video file** (Moonfish herring footage, David's photos as slideshow)
   - **Camera / Kinect** (visitors become watercolor paintings — interactive)
   - **Any NDI or video source**
3. Prompt: `brionypenn watercolor painting, soft edges, natural pigment, ecological illustration`
4. **Strength/delta:** Start at `0.45` — adjust to taste

**Pros:** Uses real footage as the compositional foundation. Moonfish herring footage styled by Briony could be stunning. Camera input makes it interactive.
**Cons:** Output quality depends on input quality. Very different from footage may lose recognizability at higher strengths.

```
Video / Camera ──> StreamDiffusion (LoRA, img2img) ──> TD ──> Resolume
```

---

## Tuning Guide

### LoRA weight (how much Briony)
Controls how strongly the LoRA influences generation:
- `0.4` — Subtle watercolor wash, base model still dominant
- `0.7` — Clear Briony influence
- **`1.0` — Full effect** (start here, dial down if too strong)

### Strength / delta (img2img only — how much transformation)
Controls how much the output differs from the input image:
- `0.25` — Very light — input clearly recognizable, slight watercolor tint
- `0.35` — Light style transfer, good structural preservation
- **`0.45` — Recommended** — clear watercolor aesthetic, input still recognizable
- `0.55` — Heavy watercolor, input starts to abstract
- `0.65` — Very heavy — mostly Briony's style, input barely visible

### Guidance scale (txt2img — how closely to follow the prompt)
- `1.0–2.0` — Loose, dreamy, more abstract
- `3.0–5.0` — Balanced
- `7.0+` — Strict prompt following, more literal

### Negative prompt (optional)
`photograph, photorealistic, sharp lines, digital art, 3d render`

---

## Performance

- **RTX 3060 (Prav's laptop):** ~6 fps with SD-Turbo. LoRA shouldn't slow it down much.
- **RTX 3090 (desktop):** Should be faster, especially with TensorRT compiled.
- **Temporal coherence** is stable — no shimmer or flicker between frames. Safe for exhibition.

---

## Testing Checklist for the Jam

### Quick wins (test first)
- [ ] Load LoRA on Prav's 3060 laptop — does it load without errors?
- [ ] txt2img: prompt for herring, salmon, orca — is the style recognizably Briony?
- [ ] img2img: feed any video/image — does strength 0.45 look right?

### If time allows
- [ ] img2img with Autolume: load fish 400 kimg PKL, route NDI → StreamDiffusion
- [ ] Test on projector — does the style hold up at scale in a dark room?
- [ ] Try blending styled + unstyled in TD for a subtler effect
- [ ] Test if TensorRT works with the LoRA loaded, or if we need to bake it in
- [ ] Compare txt2img vs img2img quality — which looks better for the exhibition?
- [ ] Try different Briony prompts: kelp, tide pools, eagles, not just fish

### Key questions to answer
1. **txt2img vs img2img** — which gives us stronger output for the proof of experience?
2. **Strength on projector** — does 0.45 hold up, or need adjustment for the room?
3. **Where in the TD patch** should the filter sit — before or after any compositing?
4. **Do we need the GAN at all** for April, or is txt2img + LoRA enough?

---

## Fallback Options

If StreamDiffusion + LoRA doesn't work, we have documented alternatives:
→ See [`docs/style-transfer-guide.md`](style-transfer-guide.md) for 9 fallback approaches ranked by readiness.

Quickest fallbacks:
- **IP-Adapter** (minutes, zero training) — use a Briony painting as style reference
- **Fast Neural Style Transfer** (2-4 hours to train, 30+ fps) — best real-time fallback
- **AdaIN** (minutes, pretrained) — can blend between multiple Briony paintings live
