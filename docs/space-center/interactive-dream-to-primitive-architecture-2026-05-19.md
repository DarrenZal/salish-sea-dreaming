# Interactive Dream-to-Primitive Architecture - 2026-05-19

Status: internal production architecture
Scope: visitor dream input for IMPACT without Stable Diffusion as core renderer and without Austin-style mimicry

## Short Answer

Use this live path:

`visitor prompt -> local safety filter -> local intent classifier -> approved scene template -> primitive renderer or pre-rendered Resolume clip`

Stable Diffusion, LoRA, TELUS, and internet services are optional async helpers only after the deterministic primitive layer is already running. They may produce a sketch, atmosphere plate, mask, or background candidate for operator review. They must not generate the core geometry, claim Austin style, or receive unfiltered culturally sensitive prompts.

The user-facing language should be "internal primitive grammar sketch" or "dream mapped into a primitive scene." Do not prompt "in Austin's style" unless Austin approves a specific workflow and language.

## System Shape

```text
Visitor web app
  -> local dream gateway
  -> safety + cultural-load filter
  -> intent/template classifier
  -> scene command
  -> Resolume clip trigger OR local primitive renderer
  -> screen-blend primitive layer over fallback media

Optional async:
  filtered scene command
  -> TELUS / SD / LoRA worker
  -> sketch/background/mask candidate
  -> operator/Austin-review tray
```

The deterministic layer is the show. The async layer is research and optional polish.

## What The Web App Should Send

The web app should send the raw prompt only to the local dream gateway, not directly to Resolume, TELUS, SD, or a renderer.

Recommended payload from web app to local gateway:

```json
{
  "submission_id": "uuid",
  "prompt_raw": "school of fish",
  "language": "en",
  "source": "visitor_app",
  "created_at": "2026-05-19T15:40:00-07:00",
  "display_consent": true
}
```

Recommended payload from gateway to show systems:

```json
{
  "submission_id": "uuid",
  "prompt_public_label": "school of fish",
  "intent": "fish_school",
  "template_id": "T02_fish_school_current",
  "cultural_load": "low_ecological",
  "render_policy": "deterministic_live_or_clip",
  "scene_params": {
    "density": "medium",
    "motion": "schooling_current",
    "palette": "pale_cyan_on_black",
    "duration_s": 12
  }
}
```

Do not send raw visitor text into the primitive renderer. The renderer should receive only a bounded `template_id` and numeric parameters. Store the raw prompt for audit only if consent and privacy posture are clear.

## Prompt Mapping Table

| Example prompt | Safe intent | Scene template | Primitive scene mapping | Safety/framing note |
|---|---|---|---|---|
| `whale` | `whale_breach_or_presence` | `T01_whale_surface_breath` | Large slow crescent/oval presence near waterline; circles as breath/impact anchors; trigons as spray/attenuation. | Use generic whale ecology, not crest/being language. Do not ask for Austin style. |
| `salmon` | `salmon_single_or_return` | `T02_fish_school_current` or `T03_salmon_return_current` | Small moving fish tokens made from oval/crescent/trigon clusters; current lines carry C/Cr/Cr/T phrases. | Avoid body-center circle if Austin rejects it; use current/impact anchors instead. |
| `school of fish` | `fish_school` | `T02_fish_school_current` | Boids-like group of tiny trigon/crescent fish marks, with shared current direction and sparse circles as water anchors. | No species-specific cultural claim. |
| `flock of birds` | `bird_flock_coast` | `T04_bird_flock_sky_water` | Distant trigon/crescent marks crossing upper band; water below remains ripple grammar. | Do not generate eagles/ravens/specific crest birds unless approved. |
| `clean drinking water` | `clean_water` | `T05_clean_water_ripple` | Clear droplet/pond sequence: circle impact, crescents radiate, trigons attenuate; low density, calm. | Strong safe public template; no people or cultural figure. |
| `kids playing on the beach` | `shoreline_play_energy` | `T06_shoreline_play` | Do not depict children. Use shoreline arcs, small circles as footprints/bubbles, kite-like trigons, gentle wave crescents. | Avoid person-specific or child depiction; show activity traces, not bodies. |
| `local food system` | `food_system_cycle` | `T07_food_system_cycle` | Four-band cycle: rain/river/shore/food nodes; circles as nodes, crescents as flows, trigons as direction/return. | Abstract systems diagram, not literal farms/people. Good for Indigenomics framing. |
| `rain` / `rain over pond` | `rain_pond` | `T08_rain_over_pond` | Falling trigons or small circles trigger circle impacts; crescents expand; trigons mark outer attenuation. | Best direct prompt-to-primitive water proof. |
| `mist` / `clouds` | `mist_water_state` | `T09_mist_field` | Low-alpha circles and stretched crescents drift slowly; no hard subject. | Default fallback for ambiguous poetic prompts. |
| `ship` / `tanker` | `industry_water_trace` | `T10_tanker_wake` | Long band/crescent hull, circle lights, wake C/Cr/Cr/T chain. | Pravin-first; Austin only if framing is needed. Avoid symbolic claims. |
| unknown safe prompt | `ambient_water` | `T09_mist_field` or `T05_clean_water_ripple` | Map to mist or clean ripple, using the prompt only as public label if approved. | Never free-generate unknown imagery live. |
| named person / chief / portrait | `blocked_person` | none | No render; switch to ambient fallback. | Block. Do not paraphrase into a person scene. |
| Thunderbird / serpent / supernatural being / crest | `blocked_or_review_high_cultural` | none live | No live visitor render; operator can log for later Austin conversation. | Block from live path unless Austin pre-approves a specific template. |

## Top 8 IMPACT Scene Templates

1. `T08_rain_over_pond` - strongest direct proof of circle impact, crescent ripple, trigon attenuation.
2. `T05_clean_water_ripple` - safe, clear, and thematically aligned with public dreams.
3. `T02_fish_school_current` - covers "salmon", "fish", and "school of fish" without requiring species-specific figure claims.
4. `T09_mist_field` - default for ambiguous, poetic, or blocked-but-safe redirections.
5. `T04_bird_flock_sky_water` - expands beyond water while staying abstract and low cultural load.
6. `T06_shoreline_play` - maps community/family prompts into traces and shoreline energy, not people.
7. `T07_food_system_cycle` - best Indigenomics/system prompt; turns "local food system" into flows and nodes.
8. `T10_tanker_wake` - useful world-content stress test for Pravin; keep Austin-facing only if framing is needed.

`T01_whale_surface_breath` is valuable but should not be in the top 8 lead set unless the icon-like whale v001 problem is solved. For IMPACT, prefer whale as a slow water-presence or breath/ripple template rather than a literal breaching icon.

## Live Local vs Async TELUS

| Function | Live locally | Async TELUS / internet | Notes |
|---|---:|---:|---|
| Prompt form UI | Yes | No | Serve from local machine or LAN if possible. |
| Safety keyword filter | Yes | Optional audit only | Must run locally before anything else. |
| Intent/template classifier | Yes | Optional richer classifier | Local keyword/rule classifier is the production path. |
| Scene JSON validation | Yes | No | Local schema validation gates all rendering. |
| Pre-rendered clip trigger | Yes | No | Fastest and safest live mode. |
| Lightweight primitive renderer | Yes | No | Use only if stable on show machine; otherwise pre-render. |
| Resolume OSC/MIDI/keyboard trigger | Yes | No | Must work without internet. |
| Prompt clustering / analytics | Optional | Yes | Not needed for show continuity. |
| SD/LoRA sketch/background/mask | No for core | Optional | Async, operator-reviewed, kill-switchable. |
| LLM prompt repair / richer interpretation | No for core | Optional | Never blocks live response. |

## Latency And Fallback Plan

| Mode | Target latency | Dependency | Behavior |
|---|---:|---|---|
| A. Pre-rendered Resolume clip | 0.2-1.0s | Local gateway + Resolume | Classifier chooses `template_id`, gateway triggers matching clip. Best IMPACT default. |
| B. Local live primitive render | 0.5-3.0s startup, real-time after | Local CPU/GPU | Renderer instantiates template with deterministic seed and streams/exports frames. Use only after rehearsal. |
| C. Local render-to-file | 10-90s | Local CPU | Useful for offscreen queue, not immediate wall response. |
| D. TELUS/SD async sketch | 30s-minutes | Internet/TELUS/GPU | Optional background/sketch candidate after deterministic layer has already responded. |
| E. Full offline fallback | immediate | Operator only | Manual hotkeys trigger ambient templates: ripple, mist, fish school, kelp/current. |

If internet or TELUS is unavailable:

- Keep accepting prompts locally if the LAN/web app is available.
- Classify with the local keyword/template map.
- Trigger pre-rendered Resolume clips or local deterministic templates.
- If the local web app fails, the operator uses a hotkey/MIDI page of the top templates.
- If classification fails, play `T09_mist_field` or `T05_clean_water_ripple`.
- If the renderer fails, stay on Agent A fallback media plus Agent B approved layer-only clips.

## Safety Rules

### Content and cultural safety

- Block named people, chiefs, living public figures, portraits, and prompts that ask to depict a specific person.
- Block or route to review: Thunderbird, double-headed serpent, Goat-man, Transformer, crest, clan, ceremony, sacred, ancestor, chief, named beings, and supernatural figures.
- Do not generate eagle/raven/orca/salmon as crest figures. Use generic ecological scene templates unless Austin approves a specific visual treatment.
- Do not display visitor text that includes private information, slurs, threats, self-harm, sexual content, or personal accusations.
- For children/family prompts, render traces of play or community energy, not bodies or faces.
- Unknown safe prompts fall back to abstract water states; unknown unsafe prompts do not render.

### Authorship and language safety

- Never prompt "in Austin's style", "Coast Salish style", or "Indigenous style" in the live system.
- Use "internal primitive grammar sketch", "procedural primitive scene", or "visitor dream mapped to a primitive scene."
- Do not claim the primitive mapping is traditional meaning, teaching, or Austin-authored work.
- Nothing Austin-derived becomes audience-facing without Austin's per-output approval.
- Keep the prompt-system architecture separate from Austin-derived foreground assets and with its own kill switch.

### Technical safety

- The renderer receives structured commands only, never raw prompt text.
- All templates are enum values. No arbitrary shape names, colors, subjects, or free text are accepted by the renderer.
- Every scene command includes `cultural_load`, `render_policy`, `template_id`, and `seed`.
- Every live scene has a maximum dwell time and cannot stack indefinitely.
- The operator can mute the whole visitor-dream layer instantly.

## Stable Diffusion / LoRA Role

SD/LoRA does not belong in the live core path.

Allowed only as async, optional, reviewed output:

- background atmosphere plate behind an already-running deterministic primitive scene
- mask/sketch candidate derived from locked primitive geometry
- still-frame research artifact for Pravin/Austin discussion
- low-denoise ControlNet pass where geometry stays locked

Not allowed:

- visitor prompt directly generating image/video
- "Austin-style" prompting
- LoRA composing animals, crest-like figures, supernatural beings, or cultural geometry
- SD changing the silhouette, primitive order, subject identity, or approved layout
- hidden SD finish on a layer presented as deterministic or Austin-approved

The useful boundary sentence is: the model is not composing the cultural geometry; it can only add surface/light where the geometry is already locked.

## Scene Command Schema

Use a compact command object for the live system:

```json
{
  "schema_version": "dream_scene_command.v1",
  "submission_id": "uuid",
  "template_id": "T08_rain_over_pond",
  "intent": "rain_pond",
  "prompt_public_label": "rain over a pond",
  "seed": 313,
  "duration_s": 12,
  "cultural_load": "low",
  "review_required": false,
  "render_policy": "pre_rendered_clip",
  "scene_params": {
    "density": "medium",
    "energy": "calm",
    "palette": "pale_cyan_on_black",
    "blend": "screen"
  }
}
```

`prompt_raw` should stay in the gateway/log layer. `prompt_public_label` should be normalized or omitted if the raw text is sensitive.

## What To Show Pravin

Show Pravin the architecture as production resilience:

1. Pre-rendered clip trigger path as the IMPACT default.
2. Local deterministic classifier and template map.
3. The top 8 templates, especially rain, clean water, fish school, mist, shoreline play, and food-system cycle.
4. TELUS/SD as async background/sketch only, never as a live dependency.
5. Operator kill switch and fallback behavior.
6. Tanker/industry as Pravin-only stress test.

Pravin decision asks:

- Which 8 templates should be loaded as hotkeys in Resolume?
- Should visitor prompts display as text labels, or should only the scene response appear?
- Is TELUS async worth wiring before IMPACT, or should it remain parked?
- Does "local food system" need a more explicit Indigenomics scene, or is the abstract cycle enough?

## What To Show Austin

For Austin review, lead with Agent B v004 if it lands well:

1. Perspective ripple plane.
2. Articulated fish.
3. Kelp/current layer.
4. Prompt-system architecture only after the grammar clips.

If v004 is not ready, use the best reviewed Agent B layer-only sequence, then show the prompt system as architecture rather than rendered public content.

Ask Austin:

- Are low-cultural-load visitor prompts acceptable if they map only to bounded primitive templates?
- Which ecological subjects should be allowed live: whale, salmon, fish, birds, mist, clean water, shoreline play, food systems?
- Should any subjects be review-only even when rendered abstractly?
- Is the phrase "internal primitive grammar sketch" acceptable for this lane?
- Where does a template become too close to culturally specific figure-making?

Do not ask Austin to approve arbitrary visitor generation. Ask him to critique the bounded template set and the division of labor.

## Park Until After IMPACT

- Free-form LLM scene generation.
- TELUS/SD live dependency.
- Prompt-only SD/LoRA outputs.
- Austin-style or Coast-Salish-style prompting.
- Supernatural/crest/named-being visitor templates.
- Person/portrait templates.
- Automatic cultural-load classifier beyond simple local rules.
- TouchDesigner live renderer unless it is already stable.
- Multi-prompt collaborative scenes.
- Public archive of raw visitor dreams.
- Data-bound versions using AIS, tides, precipitation, food systems, or SkyTrain schedules.
- Automatic "reads as prompt" scoring.

## Source Map

- [Prompt-to-Primitive Scene Pipeline](prompt-to-primitive-scene-pipeline-2026-05-19.md)
- [Prompt-to-Primitive Scene Review Index](prompt-to-primitive-scene-review-index-2026-05-19.md)
- [Deep Research Implementation Brief](deep-research-implementation-brief-2026-05-19.md)
- [Primitive Water Grammar v003 README](../../track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v003_2026-05-19/README.md)
- [Prompt-to-Primitive Scene Library README](../../track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_library_2026-05-19/README.md)
- [Austin Abstract Affordance One-Page Summary](../../track2-deterministic/morph_outputs_INTERNAL/austin-abstract-t2i-affordance-2026-05-18-austin-review-excerpt/ONE_PAGE_SUMMARY.md)
- [John Install Checklist](john-install-checklist-2026-05-14.md)
