# Signal Message to Prav — March 27, 2026

## Part 1: Deirdre Request (for your review first)

I've gone through all the footage and picked out the strongest segments for the exhibition. Before we send anything to Deirdre, can you review these selections and make sure they match what you're envisioning? Adjust timecodes or swap clips as needed — you know the creative direction better than me.

Once you're happy with the list, here's what we'd ask Deirdre for:

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

Full shotlist with all timecodes and technique notes here: [docs/moonfish-shotlist.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/moonfish-shotlist.md)

## Part 2: First Render Packet

I've trimmed 3 hero subclips for your first Briony LoRA tests. They're on the shared Drive:

**Test these three:**

1. [**H1_salmon_school.mp4**](https://drive.google.com/file/d/1l2Iy5zCzWm4FtSOAHcir-G6WCw92LdnZ/view) (60s, 199 MB) — Dense salmon school, dramatic green light. The strongest motion candidate. Test at img2img strength 0.45.

2. [**H2_herring_in_kelp.mp4**](https://drive.google.com/file/d/1b0ME3ln0zyV2fGlZzOKvTKAVn_ry0Fvz/view) (65s, 211 MB) — Herring through golden kelp. Beautiful natural composition. The golden kelp vs silver fish is a good test of whether the LoRA preserves color relationships. Strength 0.45.

3. [**H5_reef_garden.mp4**](https://drive.google.com/file/d/1IxAbKg8z7Hpleeq5HUEZG3B0DEEQut1i/view) (19s, 63 MB) — Colorful intertidal reef — reds, oranges, pinks on dark background. Only 19 seconds so it's fast. This stress-tests whether the LoRA handles vivid non-green color. Try strength 0.55 on this one (it wants more transformation).

**What to do:**
- Extract 2 seconds (120 frames at 60fps) from the most interesting moment of each clip
- Run SD 1.5 + briony_watercolor_v1.safetensors, img2img, strength as noted, 20 steps
- Reassemble as video and send back
- We're looking for: does the watercolor work in motion? Too heavy? Too light? Does schooling motion survive?

LoRA setup details: [docs/lora-integration-guide.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/lora-integration-guide.md)
Style transfer options and ControlNet pipeline: [docs/style-transfer-guide.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/style-transfer-guide.md)

This is Round 1 — fast look-dev on the 3060. If any of these look promising, Round 2 is ControlNet + LoRA on the 3090 (once it passes readiness).

## Part 3: Where We Are

- 8 hero segments identified and trimmed from the footage
- 416 underwater frames extracted for GAN training corpus (Track B)
- 14 David Denning high-res photos curated (the macro marine shots — ideal for ControlNet reveals)
- Shotlist with technique decisions: [docs/moonfish-shotlist.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/moonfish-shotlist.md)
- Collaborator permissions documented: [training-data/licenses-collaborators.md](https://github.com/DarrenZal/salish-sea-dreaming/blob/main/training-data/licenses-collaborators.md)

Lock target is still Wednesday. The micro-render results from these 3 clips will tell us which techniques to commit to for production.
