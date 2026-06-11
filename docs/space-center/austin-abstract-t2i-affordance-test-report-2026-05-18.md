# Austin Abstract T2I Affordance Test - 2026-05-18

Internal-only affordance test. Not public/show material. Outputs are not Austin Harry artwork and are not approved for sharing outside the project team/Austin review context.

## Test Intent

Compare prompt-only Austin v2 LoRA against synthetic primitive-scaffold ControlNet on low cultural-load abstract prompts only. No animals, clan beings, supernatural beings, crests, or Austin-like creatures were requested.

The governing rule remains:

> Deterministic/vector geometry owns the work; SD/LoRA can only add finish, atmosphere, or background in explicitly allowed regions.

## Outputs

- Result folder: `track2-deterministic/morph_outputs_INTERNAL/austin-abstract-t2i-affordance-2026-05-18-results/`
- Contact sheet: `track2-deterministic/morph_outputs_INTERNAL/austin-abstract-t2i-affordance-2026-05-18-results/_contact_sheet.jpg`
- Script: `scripts/austin_abstract_t2i_affordance_test.py`
- Consent sidecar: `track2-deterministic/morph_outputs_INTERNAL/austin-abstract-t2i-affordance-2026-05-18-results/CONSENT.txt`

## Settings

- Base model: `stable-diffusion-v1-5/stable-diffusion-v1-5`
- ControlNet: `lllyasviel/sd-controlnet-canny`
- LoRA: Austin v2, scale `0.25` / `0.35`
- Image size: `512x512`
- Steps: `28`
- CFG: `6.0`
- ControlNet scale: `0.92`
- Runtime on H200: `77.01s`
- Render count: `20` stills

The SD 1.5 tokenizer emitted prompt-length warnings. The test still rendered correctly, but future runs should shorten the positive prompts and keep the negative prompt compact so conditioning is less likely to truncate.

## Overall Verdict

The prediction held.

Prompt-only Austin LoRA is visually interesting but not trustworthy as an authorship path. It does not reliably keep Circle/Crescent/Trigon readable, and it invents decorative composition logic that could be mistaken for fake cultural grammar.

Synthetic scaffold + ControlNet is the useful lane. It preserves primitive layout far better and makes clear what the model is allowed to affect: surface, light, palette, and atmosphere. LoRA at `0.25` is safer than `0.35`; at `0.35` it sometimes adds richer finish, but it also starts to distort or over-style the primitive geometry.

The no-LoRA scaffold branch is important. It proves that much of the useful structure comes from the scaffold and ControlNet, not from the Austin LoRA.

## Prompt-Only Assessment

Prompt-only does hallucinate generated design systems.

- `pearl interior`: produces attractive luminous/sculptural forms, but the three primitives are not consistently legible.
- `dawn water`: becomes generic landscape/atmosphere with weak primitive presence.
- `tide-current field`: produces circular/swirl compositions that are visually interesting but detach from the requested primitive field.
- `breathing negative space`: the `0.35` branch invents dense black/white ornament. This is exactly the risk case: it looks designed, but the design is model-authored and should not be treated as Austin-derived grammar.

Conclusion: prompt-only can be useful as a private imagination scratchpad, but it should not be shown as a candidate visual language and should not drive show material.

## Scaffold Assessment

The scaffolded ControlNet branch preserves the three primitives substantially better.

- `pearl interior`: strongest result. The circle container, central crescent-like form, and trigons remain legible. LoRA adds subtle material/pearl finish without fully taking over.
- `dawn water`: scaffold survives, especially in `B_scaffold_lora035` and `C_scaffold_no_lora`, but the stronger LoRA/pink glow begins to over-color the field.
- `tide-current field`: `C_scaffold_no_lora` and `B_scaffold_lora025` keep the primitive field readable. `B_scaffold_lora035` softens contrast and begins to bury small primitives.
- `breathing negative space`: the synthetic scaffold itself is flawed. It accidentally reads face-like because of the circular boundary, upper trigon, and lower crescent arrangement. This should not be reused without redesign.

Conclusion: ControlNet scaffold is worth continuing, but scaffold design is now the main authorship-sensitive step. The scaffold must be reviewed with the same care as the output.

## LoRA Effect

Useful effects:

- Adds warmth, soft material finish, and subtle surface texture.
- Pulls some outputs toward a more cohesive palette.
- Helps the pearl/interior prompt feel less like a bare technical diagram.

Failure modes:

- At `0.35`, it can flatten primitive contrast or replace geometry with ornamental texture.
- It sometimes adds radial/mandala logic even where the scaffold is more open.
- It does not understand "primitive grammar" reliably without the scaffold.

Recommendation: use Austin v2 LoRA only at low scale, starting at `0.25`, and only behind ControlNet or masks. Treat `0.35` as a review setting, not a default.

## Austin-Review Worthiness

Worth showing as an affordance, with careful framing:

- The contact sheet as a controlled comparison, not as proposed art.
- `p01_pearl_interior_three_primitives__B_scaffold_lora025.jpg` beside its scaffold and `C_scaffold_no_lora`.
- `p03_tide_current_field__B_scaffold_lora025.jpg` beside `C_scaffold_no_lora`, to ask whether the model finish helps or gets in the way.

Do not show as stand-alone outputs:

- Prompt-only variants.
- `p04_breathing_negative_space` variants, because the scaffold accidentally suggests a face-like arrangement.
- Any `0.35` output without the neighboring scaffold/control comparison.

Suggested Austin framing:

> We tested whether SD/LoRA can be constrained to finish abstract primitive scaffolds without inventing new figures or cultural forms. The prompt-only branch is not trustworthy. The scaffolded branch is more useful because the geometry is locked first and the model only adds surface, light, and atmosphere. Does that division of labor feel acceptable, or should the model stay away from these primitives entirely?

## Next Step

If we continue this lane, do one narrow follow-up: redesign the primitive scaffolds by hand as neutral geometric plates, then rerun only the scaffolded branches at LoRA `0.0`, `0.20`, and `0.25`. Do not run more prompt-only tests unless Austin explicitly wants to discuss the failure mode.
