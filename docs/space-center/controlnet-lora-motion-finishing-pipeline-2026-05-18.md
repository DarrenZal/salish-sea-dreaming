# ControlNet + Austin LoRA Motion Finishing Pipeline - 2026-05-18

## Status

Internal H200 motion test passed on the Raven Sun -> Cosmic Sun morph excerpt.
This confirms ControlNet + low-scale Austin v2 LoRA is viable as a finishing
layer for deterministic morph frames.

## Artifacts

Output folder:
`track2-deterministic/morph_outputs_INTERNAL/austin-controlnet-lora-motion-raven-cosmic-2026-05-17/results_r2/`

Key review files:

- `comparison_source_canny_lineart.mp4`
- `raven_cosmic_motion__canny__default_lora035_d30.mp4`
- `raven_cosmic_motion__canny__safer_lora025_d30.mp4`
- `raven_cosmic_motion__lineart__default_lora035_d30.mp4`
- `raven_cosmic_motion__lineart__safer_lora025_d30.mp4`
- `_motion_review_sheet.jpg`

Scripts:

- `scripts/prepare_austin_controlnet_lora_motion_excerpt.py`
- `scripts/austin_controlnet_lora_motion_test.py`

## Verified Shape

- Motion variants: 768x768, 48 frames, 4 seconds, 12 fps
- Comparison strip: 1920x412, 48 frames, 4 seconds, 12 fps
- Boundary: internal only, pending Austin per-output approval

## Verdict

Use this as a finishing pipeline candidate:

- Deterministic morph frames carry structure and timing.
- ControlNet preserves edges, primitives, and composition.
- Austin v2 LoRA contributes warmth, texture, palette, and visual register.
- It should not be framed as independent Austin-style generation.

Default candidate:

```text
ControlNet mode: Canny
LoRA scale: 0.35
Denoise: 0.30
ControlNet scale: 0.78
```

Safer fallback:

```text
ControlNet mode: Canny
LoRA scale: 0.25
Denoise: 0.30
ControlNet scale: 0.78
```

Canny and true lineart were nearly indistinguishable on this clean vector
source. Use Canny for now because it is simpler and stable.

## Next Steps

1. Run a longer Raven Sun -> Cosmic Sun pass with the default Canny setting.
2. If stable, try the same finishing pass on Cosmic Sun -> Salmon v007.
3. Keep the safer LoRA 0.25 setting available for review-facing variants.
4. Do not use this pipeline to generate new Austin-like figures from prompts
   without a separate Austin-guided review.
