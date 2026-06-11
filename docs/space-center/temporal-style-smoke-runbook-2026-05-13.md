# Temporal Style Smoke Runbook — 2026-05-13

Purpose: prepare a narrow GPU experiment that tests the real-footage-first recovery path without waiting for new Austin files.

Boundary: internal recipe proof only. Do not send outputs to Austin, John, sponsors, or venue unless Darren explicitly packages them and Austin has approved the relevant public outputs.

## Local Prep

Prepare three 5-second 720p excerpts:

```bash
python3 scripts/prepare_temporal_style_smoke.py
```

Outputs:

```text
output/temporal-style-smoke-2026-05-13/
  inputs/H2_herring_in_kelp_5s.mp4
  inputs/H5_reef_garden_5s.mp4
  inputs/H8_milky_water_5s.mp4
  thumbs/*_mid.jpg
  manifest.json
```

Upload just the `inputs/` directory to TELUS if running GPU:

```bash
python3 scripts/jupyter_contents_sync.py upload output/temporal-style-smoke-2026-05-13/inputs temporal-style-smoke-inputs
```

Upload the runner too:

```bash
python3 scripts/jupyter_contents_sync.py upload scripts/run_temporal_style_smoke.py run_temporal_style_smoke.py
```

Local dry-run before any GPU work:

```bash
python3 scripts/run_temporal_style_smoke.py --version v2 --lora-dir none --out-dir /tmp/temporal-smoke-dry --dry-run
```

Run on TELUS only after v2 still eval passes:

```bash
python run_temporal_style_smoke.py \
  --version v2 \
  --lora-dir austin-v2-lora-out \
  --inputs-dir temporal-style-smoke-inputs \
  --out-dir temporal-style-smoke-v2
```

## Experiment Matrix

Run only after a usable Austin v2 LoRA exists, unless explicitly doing an internal clean-subset v1.5 algorithm smoke.

| Variant | Clip | Style pass | Why |
|---|---|---|---|
| A | H2 | ControlNet Canny + LoRA, strength 0.35, CN scale 0.55 | subject-preserving fish/kelp test |
| B | H2 | img2img + LoRA, strength 0.35 | lower-structure comparison |
| C | H5 | img2img + LoRA, strength 0.35 | complex reef texture test |
| D | H8 | img2img + LoRA, strength 0.25 | subtle pearl-water atmosphere |

Hold seed constant per clip. Do not use AnimateDiff in this smoke.

Implemented runner: `scripts/run_temporal_style_smoke.py`. It styles sparse keyframes and propagates those styled keyframes with OpenCV optical-flow warp/blend, then compiles one MP4 per variant. This is an internal smoke tool, not a production renderer.

## Pass Criteria

Pass:

- Original subject and motion remain legible.
- Style influence is visible but does not invent crests or named cultural figures.
- No watermark/text/signature artifacts.
- No decorative pattern collapse.
- Output can plausibly become left/right atmospheric material, not center teaching content.

Fail:

- Motion becomes abstract wallpaper.
- Subject disappears.
- Style reads generic or culturally noisy.
- Any output looks like invented Austin-style crest artwork.

## Next Action If It Passes

Use the same architecture after Austin's curated Drive lands:

1. Train v2 LoRA.
2. Run still eval.
3. Run this smoke with v2.
4. If still clean, scale one clip to 10-15 seconds for Prav internal review.

Track 2 deterministic primitives remain the production-safe center panel regardless of this smoke result.
