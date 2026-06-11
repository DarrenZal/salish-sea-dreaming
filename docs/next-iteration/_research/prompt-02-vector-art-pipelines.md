# Deep Research Prompt #2 — Vector-Art Training & Style-Transfer Pipelines

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research.

**Decision unblocked:** Training recipe for Austin's first asset batch (October), AND the **fast style-transfer pipeline for May social-media teasers** (NEW urgency, see Update 2026-05-13 below).

**Deadline:** 2026-05-15 (T+4 days).

---

## Update 2026-05-13 — elevated urgency

Per Prav's email this morning ("we really need to get the Style Transfer into the TD stream diffusion. Ie that cannot look like generic. ... this is the make or break for this version"), style transfer in Austin's register is now production-critical for May, not just an October training exercise. Austin signed the protocols framework May 11 and is compiling a curated Drive folder; until that lands, `austin-reference/` (127 scraped images) is the working source for INTERNAL experiments.

**Specific additions to weight in research:**
- **Fast no-train style transfer** that lands by EOD Day 5 (Fri May 15) for social-media teasers — img2img with prompt + Austin-portfolio IP-Adapter reference; ControlNet over Austin's existing vectors with low denoise (0.25–0.35); SDXL-Turbo vs Flux Schnell tradeoffs for 5–10s/frame interactive vs 30s/frame quality
- **Live TD StreamDiffusion register integration** — how to push Austin's color palette / line texture into the live SDTD top layer without OOM on 3090 (24GB total VRAM, ~6–8GB headroom per plan Section 4); IP-Adapter vs textual inversion vs negative prompting
- **LoRA training on contemporary Indigenous artist portfolios** — any precedents (consented, ethical) for vector-line-art LoRA training in 2025–2026; recommended dataset size + augmentation when training set is 100–200 images; cultural-protocol considerations beyond technical recipe

Add these specifics on top of the original questions below; don't replace them.

---

## Prompt (paste verbatim)

```
I need a 2025–2026 state-of-art survey on AI style-transfer and fine-tuning
for vector-based line art, specifically for an installation that may train
on Coast Salish artist Austin Harry's portfolio (with consent) over the next
6 months.

Constraints:
- Current production stack: TouchDesigner + StreamDiffusion + sd-turbo +
  TensorRT on a single RTX 3090 (24 GB VRAM). SD-Turbo + SD 1.5 LoRA is
  architecturally incompatible per GitHub issue #182.
- We have a working Briony Penn (watercolor) LoRA at SD 1.5 rank 16 / 1000
  steps that succeeds at 30 steps on H200 but breaks live on sd-turbo.
- Goal: a recipe that produces formline-grammar-correct outputs, not
  just "Coast Salish-ish."

Research and report on:

1. SD-Turbo / SDXL-Turbo / SD3 / Flux compatibility with LoRA fine-tuning
   in 2026. Which combinations actually work in production? What are the
   live-inference fps numbers on 3090-class GPUs?

2. IP-Adapter as a no-train alternative for transferring line aesthetic.
   How well does it preserve fine line weights and shape grammar vs.
   smearing them? Compare IP-Adapter v1 / v2 / IP-Adapter-Plus / Style-Aligned.

3. LoRA recipe for vector line art: rank, learning rate, regularization,
   dataset size estimates, captioning strategy (formal primitive names vs
   anglicized common names), training-data prep (vector → raster + tag).

4. Evaluation methodology — how do you *measure* whether a generated frame
   respects a strict shape vocabulary? Per-primitive shape-similarity
   metrics? CLIP-based aesthetic scoring + a human-eval rubric?

5. ControlNet variants for line conditioning: Lineart, Canny, SoftEdge,
   Scribble, MLSD. Which preserves Coast Salish formline best at low
   denoise strengths?

6. Real-world examples of artists training LoRAs on their own line work
   (manga artists, calligraphers, tattoo artists) and what techniques
   worked.

Deliverable: 8–12 page report with a comparison matrix of techniques,
recipe-style instructions for the recommended pipeline, and a one-page
decision summary at the top.
```
