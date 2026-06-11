# Prompt-to-Primitive Scene Pipeline - 2026-05-19

Worker C design note for Salish Sea Dreaming Phase 2.

## Short Answer

Yes, for prompts like "whale jumping out of the ocean" and "tanker in Burrard Inlet" we can render a procedural 2D scene made from circles/ovals, crescents, trigons, dots, bands, and simple line/ribbon helpers. The result will read as a symbolic scene graph and motion study, not as photorealistic video and not as a claim about traditional meaning.

The viable direction is:

`visitor text prompt -> constrained scene graph -> primitive layout -> procedural animation -> alpha/MP4/NDI layer into Resolume`

Stable Diffusion and Austin LoRA should not be the core renderer. If used at all, they belong after the primitive geometry is locked, as optional atmosphere/finish/background, with a hard A/B kill switch and Austin/team review.

## Source Context

Read for this pass:

- `Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting.md`
- `Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md`
- `Transcripts/2026-05-18 The Salish Sea Dreaming Meeting Transcript.md`
- `Transcripts/2026-05-18 The Salish Sea Dreaming Meeting 2 Transcript.md`
- `docs/space-center/resolume-wide-wall-composition-plan-2026-05-18.md`
- `track2-deterministic/README.md`
- `track2-deterministic/decomposition-workflow.md`
- `track2-deterministic/primitives.csv`
- `track2-deterministic/scripts/generate_coast_salish_primitives.py`
- `track2-deterministic/scripts/morph_engine.py`
- `scripts/primitive_field_v2_flocking.py`
- `scripts/morph_primitive_field.py`

Relevant constraints from the May 18 production meeting:

- The current direction is the primitive grammar layer: Crescent / Circle / Trigon following water, salmon, kelp, current, and other motion.
- Style-transfer of Austin's work onto video was dropped as the primary path because bold-line geometry does not behave like Briony watercolor under img2img.
- Austin described circle -> crescent -> trigon as a water/ripple motion logic, with the eye drawn first to the circle and then guided by crescents/trigons.
- Industry/tankers rendered through the shape language can be acceptable when framed as the dreaming of the world as it is. Named chiefs/specific people and culturally high-load beings need stricter filtering/review.
- This week needs fast, reviewable procedural experiments, not a new hand-authored art request to Austin.

## Design Boundary

This pipeline is an internal technical sketch inspired by Austin's described primitive grammar. It should not be described as traditional knowledge, a teaching, or an authentic rendering of Coast Salish meaning. It is a constrained procedural layer that Austin can critique.

Operational guardrails:

- Use "primitive grammar layer", "grammar-inspired sketch", or "procedural primitive scene".
- Avoid "this means..." language for the primitives.
- Do not generate named people, chiefs, living public figures, or portraits.
- Keep Thunderbird, double-headed serpent, named beings, clan/crest material, and ceremonial references outside the prompt-to-scene path unless Austin explicitly approves a specific use.
- Treat tanker/industry/city prompts as world-content prompts, not cultural-symbol prompts.
- Keep all prompt-to-primitive outputs reviewable and easy to mute in Resolume.

## Pipeline Overview

### 1. Text Prompt Intake

Input:

```json
{
  "prompt": "whale jumping out of the ocean",
  "source": "visitor_app",
  "received_at": "2026-05-19T10:00:00-07:00"
}
```

The intake stage normalizes the prompt, lowercases it, strips unsafe characters, and passes it through:

- existing violence/sexual-content filters
- named-person / chief / portrait filter
- cultural-load filter for beings and story terms
- prompt length and repetition limit

For today, use a keyword/template mapper. Later, use an LLM only if it emits constrained JSON against a strict schema and cannot invent new primitive categories.

### 2. Prompt Classifier

The classifier maps visitor text into a small set of known scene intents:

```json
{
  "scene_intent": "whale_breach",
  "subjects": ["whale"],
  "actions": ["breach"],
  "place": "ocean",
  "water_state": "ocean",
  "mood": "surge",
  "cultural_load": "low_ecological_subject",
  "render_policy": "primitive_only"
}
```

Initial template groups:

- animals: whale, orca, salmon, herring, bird, seal
- water states: ocean, river, still pond, rain, mist/fog/cloud
- city/industry: tanker, ship traffic, shoreline, bridge, SkyTrain, buildings
- actions: jumping/breaching, swimming/schooling, drifting, raining, moving through, arriving/leaving

Unknown prompts should fall back to an abstract "water state" scene rather than free generation.

### 3. Scene Graph

The scene graph is the semantic plan. It does not include pixels yet.

```json
{
  "id": "visitor_scene_0001",
  "intent": "whale_breach",
  "canvas": {"w": 1920, "h": 1080, "fps": 24, "frames": 120},
  "entities": [
    {
      "id": "ocean_surface",
      "kind": "water_state",
      "role": "environment",
      "primitive_motif": "crescent_wave_band"
    },
    {
      "id": "breaching_whale",
      "kind": "animal_silhouette",
      "role": "subject",
      "primitive_motif": "oval_body_crescent_belly_trigon_tail"
    },
    {
      "id": "splash",
      "kind": "particle_event",
      "role": "motion_trace",
      "primitive_motif": "circles_crescents_trigons"
    }
  ],
  "animation": {
    "subject_path": "parabolic_breach",
    "water_motion": "slow_swell",
    "event_timing": {"breach_peak_frame": 48, "splash_peak_frame": 62}
  }
}
```

Scene graph fields should be boring and inspectable:

- `kind`: controlled enum
- `role`: environment / subject / trace / accent
- `primitive_motif`: controlled enum
- `cultural_load`: low / review / blocked
- `data_hooks`: optional data source bindings, e.g. tide, ship traffic, rain
- `resolume_role`: background, foreground, accent, alpha overlay

### 4. Primitive Layout

The layout stage turns scene entities into shape instances. It uses a small primitive catalog:

- `circle` / `oval`: anchor points, eyes, bubbles, splash droplets, train wheels, portholes
- `crescent`: water ripple, belly/underside, wake, shoreline eddy, cloud arc
- `trigon`: fin, tail, spray accent, bow/stern, attenuated ripple, directional marker
- `dot`: small circle shorthand for foam/rain/roe-like particle, without implying roe unless explicitly intended
- `band` / `ribbon`: simple waterline, shoreline, track, bridge, horizon

The primitive layout output is concrete:

```json
{
  "groups": [
    {
      "id": "whale",
      "anchor": {"x": 820, "y": 500, "rotation": -18, "scale": 1.0},
      "primitives": [
        {"type": "oval", "x": 0, "y": 0, "w": 420, "h": 150},
        {"type": "crescent", "x": 20, "y": 45, "w": 300, "h": 70},
        {"type": "trigon", "x": -245, "y": -44, "w": 135, "h": 90},
        {"type": "trigon", "x": -245, "y": 44, "w": 135, "h": 90}
      ]
    }
  ]
}
```

For Austin-facing review, show the scene graph and primitive layout separately. That lets him say "the motion is okay, but this primitive order or framing is wrong" without conflating it with SD finish.

### 5. Animation

Animation is procedural and data-ready:

- `path`: keyframed x/y/rotation/scale
- `flow`: curl-noise or optical-flow vectors from real footage
- `ripple`: circle -> crescent -> trigon emergence along a line
- `schooling`: boids with primitive fish tokens
- `splash`: radial primitive particles with gravity/fade
- `mist`: slow drifting low-alpha circles/crescents
- `city_flow`: horizontal train/traffic motion and shoreline parallax

Today, use authored math. Later, bind to footage motion vectors:

- optical flow from salmon/kelp footage drives primitive trajectories
- ship AIS / Burrard Inlet traffic density drives tanker count or wake intensity
- precipitation drives rain impacts
- tide/wind drives waterline speed and amplitude
- SkyTrain schedule/audio can drive city-line pulses

### 6. Renderer

Renderer options:

- Today: Python/PIL pre-render to PNG sequence + MP4 with alpha/no-alpha variants.
- Today/near: TouchDesigner GLSL/SOP implementation for live NDI/Spout.
- Later: WebGL/Canvas preview in the visitor/control app.

Render outputs:

- 1920x1080 for quick review
- 3840x1080 for wide wall
- 3840x2160 centered variant if the projector path needs 16:9 UHD
- PNG sequence for TD/Resolume scrubber
- MP4 for Resolume deck

### 7. Resolume Layer

Recommended stack, aligned with the wide-wall plan:

1. Background footage / ocean / shoreline, public-safe and license checked
2. Primitive scene layer, low to medium opacity, alpha-capable
3. Austin-approved foreground assets, if any, on a separate kill-switch group
4. Optional SD/LoRA finish as an alternate clip, not a hidden effect
5. TD live source only when it is the active foreground, not buried

For visitor prompts, use a short dwell:

- fade primitive scene in over 1.5-3 seconds
- hold 8-20 seconds depending on composition
- fade back to ambient primitive field
- do not let rapid prompt spam create overlapping figures

## Example Mappings

### Whale Breach

Prompt: "whale jumping out of the ocean"

Scene graph:

- ocean surface
- breaching whale
- splash / foam / falling droplets
- optional moon/horizon if prompt asks for night/dawn

Primitive layout:

- whale body: large oval
- whale head: overlapping oval/circle
- underside: crescent
- tail flukes: two trigons
- pectoral fin: trigon
- spray: small circles, crescents, trigons
- ocean: repeating crescent bands with slight phase drift

Animation:

- whale follows a parabolic breach path
- body rotates nose-up at entry, flatter near peak, nose-down on re-entry
- splash particles emit near waterline and fall
- waves swell around breach point

Feasible today: yes. This is the proof included with this spec.

### Salmon School

Prompt: "salmon swimming together" or "salmon school in the river"

Scene graph:

- river current
- school of 20-80 fish tokens
- optional gravel/shoreline bands

Primitive layout:

- each salmon token is a compact oval/crescent/trigon cluster, not Austin's Salmon Spawn piece
- body oval, head circle/oval, tail trigon pair, belly crescent
- current lines are crescent sequences

Animation:

- boids or flow-field following
- current pulls school downstream
- sizes vary for depth

Feasible today: yes for abstract school tokens. Later, use footage optical flow from salmon/kelp to make the motion less generic.

### Tanker In Burrard Inlet

Prompt: "tanker in Burrard Inlet"

Scene graph:

- Burrard Inlet water surface
- tanker silhouette
- shoreline/mountain/port hints
- wake
- optional ship traffic data hook

Primitive layout:

- hull: long band or rounded rectangle helper
- bow/stern: trigons
- portholes/lights: circles
- wake: crescents trailing behind
- waterline: crescent wave bands

Animation:

- slow horizontal transit
- wake crescents pulse outward
- ship density or AIS data could modulate count/speed later

Feasible today: yes. Keep the framing as "the scene is made from primitive shapes" rather than "the tanker has cultural meaning."

### SkyTrain / Shoreline

Prompt: "SkyTrain along the shoreline"

Scene graph:

- shoreline band
- SkyTrain guideway
- train cars
- city/water boundary

Primitive layout:

- train cars: bands/rectangles with circle windows or wheels
- guideway: line/ribbon
- shoreline: crescent and trigon current accents
- buildings/bridge: trigons/bands as sparse geometry

Animation:

- train moves laterally
- shoreline water primitives move independently
- optional city sound / SkyTrain data drives rhythm

Feasible today: yes as a graphic scene. Later, bind to real audio/schedule/traffic data.

### Rain Over Pond

Prompt: "rain over a pond"

Scene graph:

- still pond
- rain impacts
- ripple rings

Primitive layout:

- impact point: circle
- first ripple: crescent pair or ring arcs
- attenuated ripple: trigons at outer edge
- raindrops: small circles

Animation:

- repeated impacts at random or precipitation-driven points
- circle -> crescent -> trigon sequence expands and fades

Feasible today: yes. This is the closest direct match to Austin's water/ripple explanation and should be an early review candidate.

### Cloud / Mist

Prompt: "clouds over the inlet" or "mist over the water"

Scene graph:

- fog field
- water surface
- optional shoreline silhouettes

Primitive layout:

- low-alpha circles and ovals
- stretched crescents
- small trigons as directional edges only if needed

Animation:

- slow drift
- opacity breathing
- no hard subject silhouette unless prompt asks

Feasible today: yes. Good fallback for ambiguous prompts.

## What We Can Do Today

- Implement a constrained prompt-to-scene mapper for the example set.
- Render JSON scene recipes to 1080p PNG sequences and MP4.
- Create 6-10 hand-authored templates:
  - whale breach
  - salmon school
  - tanker transit
  - SkyTrain/shoreline
  - rain pond
  - mist/cloud
  - abstract ocean current
  - river flow
- Put outputs into `track2-deterministic/morph_outputs_INTERNAL/` with README/provenance.
- Feed the MP4 into Resolume as a foreground/ambient primitive layer.
- Use the renderer as a quick visual test before porting to TD.
- Keep all outputs internal until reviewed.

## Later Work

- Replace keyword parsing with a constrained LLM JSON parser.
- Add a prompt safety model that blocks named people and cultural high-load requests before scene generation.
- Add a richer primitive motif library reviewed against Austin's primitive presentation.
- Use optical flow from salmon/kelp/shoreline footage to drive primitive paths.
- Add TouchDesigner live rendering with Spout/NDI and OSC prompt intake.
- Bind city/ecological data to motion parameters:
  - tide
  - herring/salmon spawn
  - precipitation/wind
  - coastal birds
  - ship traffic in Burrard Inlet
  - SkyTrain / bridge / traffic rhythms
- Add 3D carved primitive forms later, using Austin/James reference only with explicit permission.
- Build an Austin review UI: scene graph on left, primitive layout preview in center, render clip on right, approve/revise notes per template.

## SD / LoRA Role

Use SD/LoRA only if it is subordinate to the primitive renderer.

Allowed technical roles:

- optional atmosphere/background pass, masked away from primitive geometry
- optional ControlNet/Canny finish driven by the primitive render, with low denoise
- still-frame visual exploration for internal discussion
- offline A/B candidate, never a hidden live dependency

Not allowed as the core path:

- prompt-only Austin-style image generation
- SD inventing animal/crest/supernatural geometry
- SD modifying primitive layout after Austin/team approval
- visitor prompt directly producing an Austin-like creature through LoRA

Acceptance rule: if SD/LoRA changes the silhouette, primitive ordering, or subject identity, reject the pass. The deterministic primitive render remains the source of truth.

## Proof Artifact

Tiny proof for "whale jumping out of ocean":

- Recipe: `track2-deterministic/scene_recipes/whale_breach_primitive_v001.json`
- Renderer: `track2-deterministic/scripts/render_primitive_scene_recipe.py`
- Output target: `track2-deterministic/morph_outputs_INTERNAL/prompt_to_primitive_scene_whale_breach_v001/`

This proof uses only procedural primitives and local PIL rendering. It does not use Austin source assets, Stable Diffusion, LoRA, or external media.

