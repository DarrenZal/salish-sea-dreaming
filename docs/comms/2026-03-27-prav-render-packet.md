# Signal Message to Prav — March 27, 2026

## Part 1: Deirdre Request

Can you pass this to Deirdre? We've reviewed all the footage and it's incredible. Here's what we'd love in higher quality:

**Priority clips (mezzanine/ProRes 422 or high-bitrate H.264, with a few seconds of handles):**

1. **P1099653** — two segments:
   - 1:35–2:35 (dense salmon/herring school — this is THE shot)
   - 3:35–4:25 (kelp forest floor looking up)
   - Slowed version of the first segment especially
2. **P1077716** — 0:00–1:05 (herring swimming through golden kelp bed). Slowed version.
3. **P1111785** — full clip, only 1:30 (golden bull kelp canopy — gorgeous slow). Slowed version.
4. **P1111509** — full clip, only 0:19 (colorful reef — does she have more of this location?)
5. **P1111707** — 0:35–1:15 (dense herring school through kelp)

For the salmon school segment (P1099653 1:35–2:35): RAW if she's willing — it's likely the single strongest frame in the whole collection.

Also still hoping for the bird murmuration/flocking footage she mentioned!

## Part 2: First Render Packet

I've trimmed 3 hero subclips for your first Briony LoRA tests. These are in the repo at `media/hero-subclips/` — I can also upload to Drive if easier.

**Test these three:**

1. **H1_salmon_school.mp4** (60s, 199 MB) — Dense salmon school, dramatic green light. The strongest motion candidate. Test at img2img strength 0.45.

2. **H2_herring_in_kelp.mp4** (65s, 211 MB) — Herring through golden kelp. Beautiful natural composition. The golden kelp vs silver fish is a good test of whether the LoRA preserves color relationships. Strength 0.45.

3. **H5_reef_garden.mp4** (19s, 63 MB) — Colorful intertidal reef — reds, oranges, pinks on dark background. Only 19 seconds so it's fast. This stress-tests whether the LoRA handles vivid non-green color. Try strength 0.55 on this one (it wants more transformation).

**What to do:**
- Extract 2 seconds (120 frames at 60fps) from the most interesting moment of each clip
- Run SD 1.5 + briony_watercolor_v1.safetensors, img2img, strength as noted, 20 steps
- Reassemble as video and send back
- We're looking for: does the watercolor work in motion? Too heavy? Too light? Does schooling motion survive?

This is Round 1 — fast look-dev on the 3060. If any of these look promising, Round 2 is ControlNet + LoRA on the 3090 (once it passes readiness).

## Part 3: Where We Are

- 8 hero segments identified and trimmed from the footage
- 416 underwater frames extracted for GAN training corpus (Track B)
- 14 David Denning high-res photos curated (the macro marine shots — ideal for ControlNet reveals)
- Shotlist with technique decisions: `docs/moonfish-shotlist.md`

Lock target is still Wednesday. The micro-render results from these 3 clips will tell us which techniques to commit to for production.
