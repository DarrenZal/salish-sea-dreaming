# Temporal Style Transfer Fallback — Real Footage First

Date: 2026-05-13  
Status: experiment plan, not public-output authorization.

## Why This Exists

Today's AnimateDiff tests failed because the motion adapter and v1 Austin LoRA competed inside the UNet. The result was temporally stable pattern collapse: no orca, no Thunderbird, no kelp, just abstract wallpaper.

The April Briony sprint already points to the better architecture: real footage supplies motion; the model supplies style. `docs/video-generation-status.md` ranks "Style Transfer on Video" as Tier 1 and says it worked because "Real footage provides temporal coherence. LoRA just adds style per-frame. No need to generate motion."

For Phase 2, this means:

- Do not spend more time on v1 LoRA + AnimateDiff.
- Do not use context-photo IP-Adapter refs for motion.
- Use Phase 1 Moonfish/Denning footage as the motion substrate.
- Use v2 Austin LoRA or approved design references only as a post-process style layer.
- Keep Track 2 deterministic primitives as the cultural/shape-bearing layer.

## Hypothesis

If v2 Austin LoRA preserves subject coherence on still frames, then a keyframe-style-transfer plus optical-flow propagation pipeline should produce more usable motion than AnimateDiff, because the footage carries temporal structure and the LoRA only affects appearance.

## Test Inputs

Use short excerpts first, not full hero clips:

| Clip | Why |
|---|---|
| `media/hero-subclips/H2_herring_in_kelp.mp4` | fish/kelp structure, best ControlNet candidate |
| `media/hero-subclips/H5_reef_garden.mp4` | complex reef texture, good img2img candidate |
| `media/hero-subclips/H8_milky_water.mp4` | soft water/spawn atmosphere, useful pearl-background material |

If GPU time is tight, start with `H2_herring_in_kelp.mp4` only.

## Matrix

Render 5-second excerpts at 512 or 768 first.

| Variant | Keyframes | Style pass | Propagation |
|---|---:|---|---|
| A | every 12 frames | v2 LoRA img2img, strength 0.35 | optical-flow warp/blend |
| B | every 12 frames | v2 LoRA img2img, strength 0.45 | optical-flow warp/blend |
| C | every 12 frames | ControlNet Canny + v2 LoRA, scale 0.55, strength 0.35 | optical-flow warp/blend |
| D | every 24 frames | best of A/B/C | optical-flow warp/blend |
| E | every frame | best still settings, no propagation | comparison only |

The key comparison is not "most stylized." It is "least generic while still preserving subject and motion."

## Evaluation

Pass only if all are true:

1. Subject remains legible without a text prompt explanation.
2. Motion follows original footage rather than melting into pattern fields.
3. No watermark, stock-text, signature, or pseudo-logo artifacts.
4. Style influence is visible but does not invent new crests or culturally specific motifs.
5. Output is clearly labelled internal-only until Austin approves.

Reject immediately if it repeats today's failure mode: stable decorative pattern with no subject.

## Likely Production Use

This fallback is best for the left/right atmospheric registers:

- Left Lens / Western science: footage-derived underwater ecology in a subtle Austin-approved register.
- Right Water / Bioregion: tide/Fraser-driven water texture, kelp, particulate flow.

It should not carry the central "teaching" content. The center Lineage panel should remain Track 2 deterministic primitives and Austin-approved morphs.

## Relationship To Existing Code

Relevant prior work:

- `scripts/run_temporal_style_smoke.py` — current Phase 2 runner for sparse keyframe style transfer plus OpenCV optical-flow propagation. Dry-run locally before TELUS upload.
- `output/overnight-results/node1/ebsynth_temporal_style.py` — keyframe stylization + optical-flow propagation prototype.
- `docs/style-transfer-guide.md` — April TELUS style-transfer options and EbSynth notes.
- `docs/video-generation-status.md` — April findings: real footage + LoRA + ControlNet/img2img was the best production path.

Do not run the old script unchanged for Austin. It is Briony-specific and contains old pod paths. Treat it as a reference architecture only.

## When To Run

Run after either:

1. Austin's curated Drive lands and v2 LoRA passes the fixed still eval, or
2. A narrow internal-only algorithm smoke test is useful using the clean-subset v1.5 LoRA, clearly labelled as recipe proof.

Do not send results to John, Austin, sponsors, or venue unless Darren explicitly decides to package them and Austin has approved the relevant outputs.
