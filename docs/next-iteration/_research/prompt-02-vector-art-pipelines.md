# Deep Research Prompt #2 — Vector-Art Training & Style-Transfer Pipelines

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research.

**Decision unblocked:** Training recipe for Austin's first asset batch (October), and the no-train fallback we run for May.

**Deadline:** 2026-05-15 (T+4 days).

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
