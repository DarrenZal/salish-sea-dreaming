# Cymatics Interaction / Input Design - 2026-05-20

Status: internal interaction/input design only. No rendering. Not Austin-approved, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim. This document designs how audience and show input *could* drive the cymatic/radiant water geometry system; it does not authorize any public-facing cymatic output.

Workstream: interaction/input design for the topology/cymatics/radiant water geometry lane. The salmon/figure lane is parked; static Austin-like salmon replication is not a priority.

Read with:

- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/mvp-fallback-resolume-package-2026-05-19.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/radial_sacred_geometry_primitive_morphology_v001_2026-05-20/README.md`

## Design Spine

Two structural commitments hold this whole design together. Everything else is detail.

### Spine 1: The Cymatic Scene Parameter Vector (CSPV)

Every input source - a typed dream prompt, a sung note, a finger tap, a MIDI knob, or nothing at all - resolves into one bounded numeric object. The renderer (deterministic Python today, TouchDesigner later) reads *only* this object. It never receives raw prompt text, raw audio, or free-form anything.

```json
{
  "schema_version": "cymatic_scene.v1",
  "mode": "rain|snow|sun|mist|ocean|river|network",
  "field_family": "multi_emitter|bessel|chladni|csg_seed|damped_wave",
  "emitter_count": 5,
  "symmetry_order": 6,
  "wave_strength": 0.5,
  "expansion_speed": 0.5,
  "phase_speed": 0.4,
  "brightness": 0.6,
  "density_cap": 16,
  "line_fill_balance": 0.5,
  "palette": "pale_cyan_on_black",
  "energy": "calm|neutral|intense",
  "impulses": [{"x": 0.5, "y": 0.5, "amp": 0.8, "ttl_s": 4.0}],
  "seed": 313,
  "cultural_status": "internal_austin_review_needed"
}
```

Bounds (hard, enforced before the renderer sees the vector): `emitter_count` 3-7, `symmetry_order` 0-8, all `*_strength`/`*_speed`/`brightness`/`line_fill_balance` floats clamped 0.0-1.0, `density_cap` 8-24, `impulses` capped at 12 active entries. These bounds come straight from the v002 caps in `cymatic-standing-wave-algorithm-brief-2026-05-20.md` section 5 (3-7 emitters, 8-24 filled cells, no all-frame lattice).

This mirrors the renderer-contract principle already established in `interactive-dream-to-primitive-architecture-2026-05-19.md`: the renderer receives bounded enums and numbers, never raw text. The CSPV is that contract specialized for the cymatic field system.

### Spine 2: The Layered Input Model

Inputs are not peers. They are four priority layers, and the show is valid with only Layer 0 running.

| Layer | Source | Role | Degrades to | Internet? |
|---|---|---|---|---|
| 0 | Deterministic clock + seed | Floor. Base phase oscillator + slow mode auto-cycle. Always produces a valid CSPV. | nothing - this is the floor | No |
| 1 | Ambient audio (show music / room) | Continuous modulator on top of Layer 0 baseline. | Layer 0 baseline | No |
| 2 | Episodic visitor input (dream prompt, touch) | Discrete perturbations: shift mode, inject impulses. | Layers 0-1 (system keeps running) | Prompt classify: no (local). Richer interpretation: optional |
| 3 | Operator override (MIDI / Resolume) | Knobs, caps, kill-switch. Highest priority. | always available | No |

Conflict resolution when layers write the same CSPV field: **operator (3) > visitor prompt mode (2) > audio modulation (1) > clock baseline (0)**. Audio is modulation *layered onto* the baseline, not a replacement. The operator can clamp or freeze any field at any time.

The critical property: pull the internet, pull the audio, pull every visitor, and Layer 0 still emits a valid CSPV every frame. The wall never goes black for lack of input.

---

## 1. Input Sources

Six sources, mapped to the layer model above.

### 1.1 Web dream prompt (Layer 2)

- **What:** Visitor scans a QR code, opens the prompt form (`web/visitor.html` already exists in the repo), types a short phrase.
- **Signal it provides:** one short text string -> resolves to `mode`, `palette`, `density_cap`, `energy`.
- **Path:** raw text goes only to a local dream gateway, never to the renderer. A *local keyword classifier* (live, offline) maps the phrase to a `mode`. Optional *async* LLM/sentiment enrichment refines `palette`/`energy` later. This split is already specified in `interactive-dream-to-primitive-architecture-2026-05-19.md` - this document inherits it.
- **Hardware reality:** served from the show machine or LAN; works offline as long as the local web app is reachable.
- **Fallback if absent:** Layer 0 auto-cycle continues. Unknown/unclassifiable prompts fall back to `mist` or `ocean`.

### 1.2 Voice / microphone (Layer 1, optionally Layer 2)

- **What:** A visitor speaks or sings into a microphone near the installation.
- **Signal it provides:** two distinct uses. (a) **Audio-reactive driver** - amplitude envelope, pitch estimate, onset transients drive `wave_strength`, `symmetry_order`, and `impulses`. (b) **Optional STT -> prompt** - speech transcribed to text, then treated exactly like a web dream prompt (async).
- **Path:** use (a) is live and offline (Audio Device In CHOP -> Analyze/FFT). Use (b) is async and parked for IMPACT.
- **Hardware reality:** **the 3090 has no microphone** (logged in project memory: `project_3090_hardware_audio.md`). Any voice input needs a dedicated USB mic added to the show machine (3090 or the new 5090). Treat voice as a *stretch* input that requires a hardware add, not a given.
- **Fallback if absent:** drops to Layer 1 ambient audio, or Layer 0 if no audio device at all.

### 1.3 Music / audio (Layer 1)

- **What:** The always-on show audio - Matt's composition / Ableton output, or room ambience.
- **Signal it provides:** continuous amplitude/RMS, three frequency bands (low/mid/high), spectral centroid, onset transients.
- **Path:** live, offline. Audio Device In CHOP -> Analyze CHOP / FFT CHOP / Filter CHOP -> CSPV modulation. This is the primary continuous modulator and the reason the field always feels alive even with zero visitor input.
- **Hardware reality:** show audio routing already exists for the gallery build (`scripts/gallery_audio.py`, `scripts/ambient_audio.ps1`). A WASAPI loopback tap can read the show's own audio bus without a mic.
- **Fallback if absent:** Layer 0 baseline. A `fake_audio_osc.py`-style synthetic envelope already exists in the repo and can stand in for rehearsal.

### 1.4 Touch / mouse (Layer 2)

- **What:** A visitor taps a touchscreen or surface (or the operator clicks) to drop a ripple impact.
- **Signal it provides:** normalized `(x, y)` coordinate plus an amplitude -> one `impulse` entry appended to the CSPV.
- **Path:** live, offline. Each tap injects a damped-wave impulse (algorithm rank 5 in the cymatics brief) or a short-lived point emitter at `(x, y)`. Impulses carry a `ttl_s` and are rate-limited.
- **Hardware reality:** needs a touch surface or kiosk; mouse works for operator/rehearsal. The live damped-wave injection path needs the TouchDesigner realtime generator to be stable.
- **Fallback if absent:** no impulses; field runs on Layers 0-1 only.

### 1.5 MIDI / Resolume knobs (Layer 3)

- **What:** Pravin/Darren at a MIDI controller or Resolume's own UI.
- **Signal it provides:** direct operator writes to any CSPV field - `symmetry_order`, `emitter_count`, `phase_speed`, `density_cap`, `line_fill_balance`, `brightness`, `palette`, and the blackout/kill-switch.
- **Path:** live, offline. MIDI -> TD CHOP or -> Resolume layer/clip control.
- **Hardware reality:** Resolume + MIDI controllers are already core to Pravin's stack and the gallery build. Lowest-risk input to wire.
- **Fallback if absent:** system runs autonomously on Layers 0-2; no override available, which is acceptable for an unattended mode.

### 1.6 Deterministic fallback clock / random seed (Layer 0)

- **What:** No input at all - a wall clock and a fixed PRNG seed.
- **Signal it provides:** the base phase oscillator `p = 0.5 + 0.5*cos(omega*t)` (from the cymatics brief section 4) and a slow mode auto-cycle timer.
- **Path:** live, offline, dependency-free. Pure NumPy field math, or pre-rendered loops triggered on a timer.
- **Hardware reality:** none. Runs anywhere.
- **Fallback if absent:** this *is* the fallback. It has no fallback because it has no dependency.

---

## 2. Mapping Model

How each signal writes into the CSPV. All mappings are deterministic functions; none require a model or the internet unless explicitly marked async.

### 2.1 Prompt category -> mode

The local keyword classifier maps a dream phrase to one of seven modes. Each mode is a `field_family` plus default parameters.

| Mode | Field family | Default symmetry | Motion signature | Source recipe |
|---|---|---:|---|---|
| `rain` | `multi_emitter` (staggered onset) | 0 | Drops trigger expanding rings; interference lunes/trigons | Rain Cymatics Pond (topology grammar section 8) |
| `snow` | `bessel` (m=6) | 6 | Sixfold radial crystallization, phase-locked | Snowflake Harmonic |
| `sun` | `bessel` (m=0 + m=6 blend) | 6 | Central orb, radial crescent/trigon release | Sun / Ripple Radial Field |
| `mist` | `multi_emitter` (weak field) | 0 | Low-opacity node/edge extraction, slow drift | Flow-Network Mist |
| `ocean` | `multi_emitter` / membrane | 0 | Large slow standing-wave swells | Membrane-Wave (smooth-fluid doc) |
| `river` | spline advection + curl | 0 | Streamline flow, S-curve phrases | Spline-Advection River Bend |
| `network` | `multi_emitter` -> nodal graph | 0 | Nodal contours form a node/edge graph | Flow-Network Mist / Currents |

"Still pond" (named in the project CLAUDE.md water-state list) is not a separate field family - it is a low-energy preset of `ocean`/membrane: `wave_strength` low, `phase_speed` low, one or zero impulses. The auto-cycle (section 2.6) uses it as a calm beat.

### 2.2 Amplitude -> wave strength / brightness / expansion speed

Continuous, Layer 1. Normalized audio RMS `a` in 0.0-1.0:

- `wave_strength = clamp(0.15 + 0.7 * a)` - antinode fill energy, membrane pressure.
- `brightness = clamp(0.3 + 0.6 * a)` - fill opacity and bloom.
- `expansion_speed = clamp(0.25 + 0.6 * a)` - how fast rings/wavefronts expand.

Smoothing: the bridge sends raw values; TD smooths locally (the convention set in `live-feed-osc-contract.md` - "TouchDesigner should smooth locally"). A Lag/Filter CHOP with ~0.3-0.6 s rise prevents strobing.

### 2.3 Frequency bands -> radial harmonic count / symmetry order

Layer 1. Three-band split plus pitch:

- **Low band** energy -> ring-mode radius and damping (large, slow swells). Maps to Bessel `n` and emitter falloff `lambda`.
- **Mid band** energy -> `emitter_count` (3-7) and emitter phase offsets / Chladni mode blend.
- **High band** energy -> `density_cap` toward 24 and trigon release density, outline shimmer.
- **Dominant pitch / spectral peak** -> `symmetry_order` (the Bessel angular mode `m`, i.e. how many radial lobes). Low pitch -> low `m` (2-3 lobes); high pitch -> high `m` (6-8 lobes).
- **Spectral centroid** -> nudge `mode`/`palette` family between water/rain (cool, low centroid), snow/radial (mid), and sun/ripple (warm, high centroid). This is a *suggestion* weight, never an override of an operator- or prompt-set mode.

These follow `cymatic-standing-wave-algorithm-brief-2026-05-20.md` section 9 audio mappings exactly.

### 2.4 Touch / click -> impact point / ripple emitter

Layer 2. A tap at normalized `(x, y)` with strength `s`:

```text
append impulse { x, y, amp: clamp(0.4 + 0.5*s), ttl_s: 3.0-5.0 }
```

The impulse seeds a damped-wave impulse or a short-lived point emitter. Existing field wavefronts interfere with it, producing fresh crescent/trigon cells at the new overlaps. Rate limit: max ~3 impulses/second, max 12 active; excess taps are dropped (not queued) to keep the field legible.

### 2.5 Dream sentiment / keywords -> palette / density / calm-vs-intense

Layer 2, partly async. From the classified prompt:

- **Keywords** -> `palette` (e.g. "moonlight", "night" -> deep blue; "sun", "warm" -> warm radial) and `density_cap` ("storm", "many" -> higher; "single", "quiet" -> lower).
- **Sentiment** -> `energy` enum: `calm` / `neutral` / `intense`, which scales `phase_speed`, `wave_strength` ceiling, and `expansion_speed`. A local lexicon handles the common cases offline; an async sentiment model only *refines* it and never blocks the live response.

### 2.6 Knobs -> operator parameters

Layer 3, direct writes. Each operator control binds to one CSPV field:

| Control | CSPV field | Range |
|---|---|---|
| Opacity fader | (Resolume layer opacity, not CSPV) | 0-100% |
| Symmetry knob | `symmetry_order` | 0-8 |
| Phase speed knob | `phase_speed` | 0.0-1.0 |
| Line/fill knob | `line_fill_balance` | 0.0 (all outline) - 1.0 (all fill) |
| Emitter count knob | `emitter_count` | 3-7 |
| Density knob | `density_cap` | 8-24 |
| Mode selector | `mode` | 7 enums |
| Blackout / panic | kill-switch -> fallback scene | momentary |

`line_fill_balance` is the operator handle on the phase-inversion model from `cymatic-standing-wave-algorithm-brief-2026-05-20.md` section 4 - it biases the outline-vs-fill display state without touching the underlying field topology.

---

## 3. Live vs Async Split

### 3.1 Live deterministic cymatic mode (must work with no internet)

Everything needed to run a complete, beautiful show is local and offline:

- Layer 0 clock + seed.
- Layer 1 audio analysis (Audio Device In CHOP, WASAPI loopback - no mic required).
- Layer 2 **local keyword** prompt classifier and touch impulses.
- Layer 3 MIDI/Resolume.
- The cymatic field math itself (NumPy/OpenCV today, GLSL in TD later) - pure computation, zero network.
- Pre-rendered cymatic loops in Resolume as the codec-light path.

If the internet, TELUS, and any cloud service are all down, the show loses *nothing* from Layers 0, 1, and 3, and keeps the keyword-classified part of Layer 2.

### 3.2 AI prompt interpretation - optional and async

Only the *richer* interpretation of a prompt is async, and it is never on the live path:

- LLM intent repair / disambiguation of an unusual phrase.
- Sentiment refinement beyond the local lexicon.
- Any SD/LoRA/TELUS sketch or background plate.

These run after the deterministic layer has already responded. They write at most a refined `palette`/`energy` into a *future* CSPV, or produce an operator-reviewed candidate. They cannot block, stall, or change a scene already on the wall. This is the same async boundary drawn in `interactive-dream-to-primitive-architecture-2026-05-19.md`.

### 3.3 Fallback templates for common dream inputs

A small static table pre-resolves the most common phrases so the classifier never has to "think" live:

| Visitor phrase pattern | Mode | Notes |
|---|---|---|
| "rain", "rain on the ocean", "storm" | `rain` (over `ocean` base) | strongest direct proof |
| "snow", "snowflake", "frost", "ice" | `snow` | sixfold Bessel |
| "sun", "sunrise", "light", "warm" | `sun` | radial; no Austin sun replication |
| "mist", "fog", "clouds" | `mist` | default for poetic/ambiguous |
| "ocean", "sea", "waves", "tide" | `ocean` | large slow swells |
| "river", "stream", "current", "creek" | `river` | streamline flow |
| "web", "connection", "everything connected" | `network` | nodal graph |
| unknown but safe | `mist` or `ocean` | never free-generate |
| named person / chief / supernatural being | (blocked) | no render; hold on auto-cycle - see section 6 |

---

## 4. Resolume / TouchDesigner Integration

### 4.1 Today: black-screen additive MP4 layers

The lowest-risk, IMPACT-ready path. The cymatic v001 packet already contains four 6 s black-screen MP4 loops at 1920x1080 (`13_raindrop_interference_expansion`, `14_seed_flower_cell_emergence`, `15_cymatic_standing_wave_activation`, `16_chladni_nodal_primitive_activation`); the radial packet adds four more. These are pre-rendered, deterministic, and need no live generator.

In Resolume they slot as **Layer 5** of the fallback stack defined in `mvp-fallback-resolume-package-2026-05-19.md` - "(reserved) Primitive grammar layer", blend Screen/Add, opacity 8-22%, sitting above the clean Moonfish/Evan water footage. Input in this mode = the operator (or a timer / OSC trigger) choosing *which loop plays*. The CSPV collapses to a clip selector. No field math runs live.

### 4.2 Later: TouchDesigner realtime generator

When the TD realtime path is proven stable, the CSPV drives a live generator instead of selecting clips. The network is the one already specified in `cymatic-standing-wave-algorithm-brief-2026-05-20.md` section 9:

```text
Audio Device In CHOP / OSC In CHOP / MIDI In CHOP / touch input
  -> Analyze / FFT / Filter CHOP
  -> CSPV resolver (DAT)
  -> GLSL TOP field generator (multi-emitter / Chladni / Bessel)
  -> Threshold / Level TOP masks (positive, negative, nodal)
  -> optional Python DAT precomputed cell-recipe ingest
  -> SDF primitive raster TOP -> heightfield merge -> slope/normal GLSL
  -> caustic / refraction / bloom TOP
  -> Movie File Out / NDI / Spout -> Resolume layer
```

Division of labor (from the brief): Python remains the robust topology classifier and recipe writer; TD handles live phase inversion, audio reactivity, and shading; Resolume stays the production fallback layer stack.

### 4.3 OSC / MIDI control surface

A dedicated OSC namespace carries the CSPV into TD. Modeled on the conventions in `live-feed-osc-contract.md` (raw values; TD smooths locally; heartbeat so the renderer never drops to black). The repo already has OSC bridge precedent - `scripts/bioregional_osc_bridge.py`, `scripts/ssd_osc_in_callbacks.py`, `scripts/td_bioregional_osc_callbacks.py` - so the cymatic bridge is a sibling, not new infrastructure.

| OSC address | Type | Meaning |
|---|---|---|
| `/cymatic/mode` | int | mode enum (0-6) |
| `/cymatic/field_family` | int | field-family enum |
| `/cymatic/wave_strength` | float | 0.0-1.0 |
| `/cymatic/expansion_speed` | float | 0.0-1.0 |
| `/cymatic/phase_speed` | float | 0.0-1.0 |
| `/cymatic/symmetry_order` | int | 0-8 |
| `/cymatic/emitter_count` | int | 3-7 |
| `/cymatic/brightness` | float | 0.0-1.0 |
| `/cymatic/density_cap` | int | 8-24 |
| `/cymatic/line_fill` | float | 0.0-1.0 |
| `/cymatic/palette` | int | palette enum |
| `/cymatic/impulse` | float x3 | x, y, amplitude - one ripple impact |
| `/cymatic/blackout` | int | 1 = kill cymatic layer immediately |
| `/cymatic/heartbeat` | int, float | status flag + Unix timestamp every tick |

Raw prompt text is never an OSC value. The gateway resolves a prompt to CSPV fields *before* anything reaches OSC/TD. MIDI binds to the same fields via TD CHOP mapping or Resolume's native MIDI map.

### 4.4 Kill-switch and fallback scene

- **Kill-switch:** `/cymatic/blackout 1`, a MIDI panic button, or a Resolume layer-group solo-mute drops the entire cymatic layer instantly. This is a hard requirement - the cymatic content is internal/review-needed (section 6), so the operator must be able to remove it from the wall in one action.
- **Fallback scene:** on blackout, or on any renderer failure, the deck falls back to the **MVP fallback package** (`mvp-fallback-resolume-package-2026-05-19.md`) - clean, review-neutral H6/Moonfish/Evan water footage. The cymatic layer lives on its own Resolume layer group, separate from the fallback floor and from any Austin-derived group, exactly so it can be removed without disturbing anything else.
- **Heartbeat:** TD/Resolume watches `/cymatic/heartbeat`; if it stops, the cymatic layer is auto-faded and the fallback floor carries the wall. Same cache/heartbeat resilience pattern as the live-feed bridge.

---

## 5. Five Concrete Interactive Scenarios

Each traces input -> resolution -> CSPV -> renderer -> wall.

### 5.1 A visitor submits "rain on the ocean"

1. Visitor types "rain on the ocean" into `web/visitor.html`; raw text -> local dream gateway only.
2. Local keyword classifier matches "rain" + "ocean": `mode = ocean` as the base field, with `rain` staggered-onset emitters layered on. No internet used.
3. Gateway emits a CSPV: `mode: ocean`, `field_family: multi_emitter`, `emitter_count: 6`, `wave_strength: 0.5`, `palette: pale_cyan_on_black`, `energy: calm`, `seed` from submission id.
4. Optional async sentiment pass later refines `energy`/`palette`; it does not touch the scene already running.
5. Renderer path A (today): operator/OSC triggers the pre-rendered `13_raindrop_interference_expansion` loop over the ocean footage base. Path B (TD later): the GLSL field generator runs ocean membrane swells with rain impulses.
6. Wall shows expanding rain rings interfering across slow ocean swells; public label (if shown) reads "rain over the ocean". Latency target 0.2-1.0 s on the pre-rendered path.

### 5.2 A visitor says or sings into the microphone

1. Visitor sings a sustained note into the USB mic on the show machine (hardware add - see section 1.2).
2. Audio Device In CHOP -> Analyze/FFT: amplitude envelope, pitch, onsets. **No speech-to-text** - this is the pure audio-reactive use.
3. Mapping (section 2.2-2.3): amplitude -> `wave_strength`/`brightness`; sung pitch -> `symmetry_order` (a higher note pushes from 3 to 6-8 radial lobes); each breath onset -> a centre `impulse`.
4. CSPV updates continuously at Layer 1; the visitor hears the field swell and sharpen with their voice. TD Lag CHOP smooths so it breathes, not strobes.
5. When the visitor stops, audio drops, Layer 1 modulation relaxes, and the field settles back toward the Layer 0 baseline.
6. If no mic is fitted, this scenario is unavailable and the field runs on ambient show audio (Layer 1) instead - graceful, no error.

### 5.3 Audience taps to create ripple impacts

1. Visitors tap a touchscreen / tap surface; each tap -> normalized `(x, y)` + strength.
2. Each tap appends one `impulse` to the CSPV (section 2.4): `{x, y, amp, ttl_s: 4}`. Rate-limited to ~3/s, max 12 active.
3. Renderer injects a damped-wave impulse (algorithm rank 5) at each `(x, y)`. New wavefronts interfere with the existing field; crescent/lune and trigon cells appear at the fresh overlaps.
4. Impulses expire after `ttl_s`; the field returns to its Layers 0-1 state. No tap is permanent.
5. Live damped-wave injection needs the TD realtime generator stable. Degraded IMPACT version: a tap triggers a short pre-rendered "impact ripple" clip instead of true live injection.

### 5.4 Pravin / Darren controls symmetry with MIDI

1. Operator turns the symmetry knob on a MIDI controller.
2. MIDI CC -> TD CHOP (or Resolume MIDI map) -> `/cymatic/symmetry_order`, Layer 3, highest priority.
3. The field's Bessel angular mode `m` shifts live - a 3-lobe trigon-pressure field opens into a 6-lobe snowflake field into an 8-lobe radiant field.
4. Operator overrides win over audio: if the audio mapping (section 2.3) also wants to set symmetry, the operator value clamps it. Companion knobs cover `density_cap`, `phase_speed`, `line_fill_balance`.
5. Use: Pravin/Darren VJ the cymatic field live, or pre-set a calm symmetry for an unattended block. The same controller's panic button is the section 4.4 kill-switch.

### 5.5 No-internet fallback auto-cycles through water states

1. No internet, no visitors, no operator, possibly no audio. Only Layer 0 is alive.
2. The clock auto-cycle timer steps through a curated calm water sequence every ~90-120 s: `ocean` -> `river` -> still-pond preset -> `mist` -> back to `ocean`.
3. Each step emits a fixed-seed CSPV, so the cycle is fully deterministic and reproducible - the same wall every run.
4. Renderer path A: a Resolume timeline/auto-pilot cross-fades the four pre-rendered loops. Path B: the TD generator runs each mode on its fixed seed.
5. Layer 1 audio, if present, still modulates on top; if absent, the cycle runs on the bare phase oscillator.
6. This is the unattended-installation mode and the universal safety net: it needs nothing and never stops.

---

## 6. Safety / Cultural Boundaries

This document and the system it designs are bound by the same boundaries as every sibling doc in this lane.

- **Internal only.** This is interaction/input design, not a public specification. Nothing here authorizes a public showing.
- **No Austin-approval claims.** Nothing in this design is Austin-approved. The cymatic v001 and radial v001 packets it drives are explicitly `INTERNAL ONLY. Austin-review-needed`. The interaction plumbing being ready does not make the content public-safe.
- **Visitor prompts must not generate named chiefs or specific people.** The classifier blocks named people, chiefs, living public figures, and portraits - no render, hold on the auto-cycle. Inherited verbatim from `interactive-dream-to-primitive-architecture-2026-05-19.md`.
- **Block supernatural / crest beings from the live path.** Thunderbird, double-headed serpent, Transformer, crest, clan, ceremony, ancestor, named beings - blocked from live visitor rendering; an operator may log them for a later Austin conversation only.
- **Avoid exact Austin source replication.** No input mode, prompt, or knob may reproduce Austin's salmon, raven, sun, or other source-piece geometry, palette, or atom adjacency. The cymatic field is abstract topology, not figure-making.
- **Keep cymatic output abstract unless reviewed.** Circles, crescents, trigons, nodal lines - boundary-relation topology only. No fish/bird/wing/fin/eye/face semantics.
- **Audio/voice reactivity is not cultural translation.** Driving the field with sound must never be framed as translating sound into approved cultural grammar (per `primitive-topology-grammar-cymatics-2026-05-20.md` section 4A). It is internal math/design.
- **The interaction layer has its own kill switch** (section 4.4), separate from any Austin-derived asset group, so it can be removed from the wall instantly and independently.
- **No "Austin's style" / "Coast Salish style" prompting** anywhere in the live system. User-facing language is "internal primitive grammar sketch" or "dream mapped to a primitive scene".

---

## 7. MVP Recommendation for IMPACT

IMPACT 2026 is May 27-28 at the HR MacMillan Space Centre. The honest framing: the *interaction plumbing* is low cultural risk and buildable now; the *cymatic visual content* it drives is Austin-review-gated. Keep those two facts separate.

### 7.1 Build and rehearse now (low risk - it is plumbing)

- **Layer 0 deterministic auto-cycle** through the four water states, driving the pre-rendered cymatic/radial loops in Resolume. Zero internet, zero generation, fully reproducible. This is the floor and the single most reliable deliverable.
- **Resolume operator control + kill-switch** - layer-group solo-mute, opacity, blackout. Native Resolume + MIDI; trivially doable today.
- **CSPV + OSC bridge** - implement the `cymatic_scene.v1` resolver and the `/cymatic/...` OSC namespace as a sibling of `scripts/bioregional_osc_bridge.py`. Pure plumbing, no cultural surface.
- **Web dream prompt -> pre-rendered clip trigger** - the local gateway + keyword classifier from `interactive-dream-to-primitive-architecture-2026-05-19.md`, resolving a prompt to a `mode` that triggers the matching pre-rendered loop. Medium effort, no live generator needed.
- **Ambient audio-reactive modulation** - *only if* the TD realtime generator is rehearsed stable before the show. Otherwise the pre-rendered loops carry IMPACT and audio-reactive is a stretch.

### 7.2 The content gate (state this plainly to Pravin)

Every cymatic and radial v001 output is `INTERNAL ONLY. Austin-review-needed`. So at IMPACT the interaction system drives one of three things, in order of preference:

1. Austin-reviewed-and-approved cymatic loops, *if* that review lands before May 27 - the interaction system then drives approved content.
2. The review-neutral MVP fallback package (clean Moonfish/Evan/H6 water footage) - the interaction system selects among *those* clips instead.
3. Stays dark - cymatic layer kill-switched off; fallback floor carries the wall.

The plumbing is ready in all three cases. The gate is content review, not engineering.

### 7.3 Park until after Austin / Pravin review

- Any public-facing showing of cymatic/radial output (all v001 is internal-review-needed).
- Live TD realtime generator as the *core* renderer - unless it is rehearsed stable; pre-rendered loops are the IMPACT default.
- Live touch / damped-wave impulse injection - unless TD is stable; the degraded "tap triggers a pre-rendered ripple clip" version is the IMPACT-safe substitute.
- Voice STT -> prompt (and the USB-mic hardware add it depends on).
- Async LLM prompt interpretation and SD/LoRA sketch generation.
- Sentiment-driven palette beyond the local lexicon.
- Spectral-centroid mode auto-switching (keep mode under operator/prompt control for the show).
- Any multi-visitor collaborative scene or public archive of raw dream prompts.

### 7.4 One-line recommendation

Build the deterministic auto-cycle, the Resolume operator control + kill-switch, the CSPV/OSC bridge, and the prompt -> clip-trigger gateway now; treat audio-reactive and live touch as TD-stability-gated stretch goals; and do not put any cymatic output on a public wall at IMPACT without an Austin per-output review record.

---

## Path Verification

All paths referenced in this document were verified to exist on 2026-05-20:

Source docs read for this design:
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/smooth-fluid-primitive-grammar-prototype-2026-05-20.md`
- `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/mvp-fallback-resolume-package-2026-05-19.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_radiant_water_geometry_v001_2026-05-20/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/radial_sacred_geometry_primitive_morphology_v001_2026-05-20/README.md`

Cross-referenced and verified:
- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `docs/space-center/primitive-pattern-language-next-system-2026-05-19.md`
- `docs/space-center/austin-informed-water-phrase-recipes-2026-05-19.md`
- `docs/space-center/prompt-to-primitive-scene-pipeline-2026-05-19.md`
- `docs/space-center/resolume-wide-wall-composition-plan-2026-05-18.md`
- `docs/space-center/hubble-wide-wall-resolume-assembly-2026-05-19.md`
- `docs/next-iteration/_research/live-feed-osc-contract.md`
- `track2-deterministic/primitive_grammar/grammar_v001.json`
- `scripts/cymatic_radiant_water_geometry_v001.py`
- `scripts/cymatic_standing_wave_phase_inversion_v002.py`
- `scripts/radial_sacred_geometry_primitive_morphology_v001.py`
- `scripts/bioregional_osc_bridge.py`
- `scripts/ssd_osc_in_callbacks.py`
- `scripts/td_bioregional_osc_callbacks.py`
- `scripts/fake_audio_osc.py`
- `scripts/gallery_audio.py`
- `scripts/ambient_audio.ps1`
- `web/visitor.html`

No rendering was performed for this document.
