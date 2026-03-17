# Meeting Prep: Darren + Prav — March 14, 2026

## Context

Prav asked: *"Does the spring show need a more substantial rethink or redesign, given its original vision, scope, and trajectory — or do you think we can come close to that realization?"*

**Answer: No conceptual rethink, but yes a production simplification for April.** The exhibition outline and curator description are well-scoped and achievable. The training pivot changes *how* you get the visuals, not *what* the installation is. The key shift: treat GAN training as **one visual voice** inside a robust multi-layer installation, not the single point of failure.

---

## What's Confirmed Working

| What | Status | Evidence |
|------|--------|----------|
| PKL loads in Autolume | **CONFIRMED** | Prav's video of 000200 model test |
| NDI → TouchDesigner | **CONFIRMED** | Prav's Autolume-NDI-TD test video |
| 200 kimg + 320 kimg checkpoints | On shared Drive | Trained on 539 Salish Sea marine photos |
| Autolume UI | Prav learning | 2-week program started, facial model first |
| Curator description | **APPROVED** | Raf has text for contracts/media |
| Exhibition docs | **SOLID** | Exhibition Outline, Tech Rider, Collaboration Outline — all coherent |
| Briony corpus | 54 images at 512x512 | Watercolors ready (but need pruning for LoRA — see below) |
| Marine photo corpus | 539 images at 512x512 | QC'd, provenance tracked |
| Dream transform pipeline | **EXISTS** | `dream_briony.py`, `dream_video.py`, `create_loops.py` |

## What's Blocked or Uncertain

| What | Issue | Impact |
|------|-------|--------|
| Dataset too diverse | 37 species, inconsistent geometry | Base model won't converge to photorealism |
| LoRA pipeline | Not researched; Briony corpus not style-consistent enough as-is | Style transfer approach unproven for April |
| Sound layer | No named owner, no minimum spec | Core exhibition promise unfulfilled |
| Exhibition hardware | Prav's RTX 3060 laptop vs dedicated desktop | 16-day continuous operation risk |
| Autonomous mode | No burn-in testing, no restart procedure, no fallback | Operational gap |
| Moonfish footage | Referenced but not integrated | Potential visual layer unused |

---

## The Current Checkpoints: Useful Material, Not the Finish Line

The 320 kimg checkpoint at FID ~300 produces something dreamlike — marine forms that emerge and dissolve, recognizably *of* the sea. This serves the curator's description ("endlessly evolving visual landscapes") and the exhibition outline ("visuals flow, dissolve, and recombine").

**But don't overplay this.** Yesterday's team call committed to: redesign the dataset, pursue LoRA/IP Adapters for Briony style transfer, aim for a stronger base model. The current checkpoints are **valid material for the multi-layer composition and a solid fallback** — not proof that retraining is unnecessary.

**Question for Prav:** Having played with the 200 kimg and 320 kimg checkpoints — what does the output *feel* like projected? Is it artistically interesting as one visual layer among several, or does it feel broken when it's the primary visual? This is a creative judgment call.

---

## Timeline Reality

```
March 14 (today)     Darren + Prav alignment call
March 14-19          6 working days — Darren's last sprint before travel
March 20-28          Darren away — Prav working independently
March 28-April 9     12 days — final integration + testing
April 10             EXHIBITION OPENS (setup/calibration day before)
April 10-26          Exhibition live (16 days continuous)
```

**27 days total. The most dangerous gap: no one is testing operational stability yet.**

---

## Proposed Approach: Multi-Layer Installation with Parallel Tracks

The core production decision: **commit to multi-layer composition from day one.** Autolume is one visual voice, not the only one. Resolume mixes multiple sources. This makes the installation more robust AND more artistically rich, and plays to Prav's strengths as a live mixer.

### Track A: Autolume + Existing Checkpoints (Foundation Layer)
**Owner: Prav | Timeline: Now → April 10**

- Autolume running 200 kimg and/or 320 kimg checkpoint
- Latent space navigation as one visual stream
- NDI → TD → Resolume → projector pipeline (proven on same machine)
- OSC/MIDI mapping for live performance mode
- **Pre-render hours of autonomous content** (latent walks, slow transitions) as fallback playback

### Track B: Dataset Redesign + Retrain (Better GAN Layer)
**Owner: Darren | Timeline: March 14-19**

**Recommended: Option B2 — Underwater scene coherence** (not strict fish-only purity). The existing training docs already define the winning image grammar as coherent underwater/nearshore scenes with consistent lighting and color palette. This is closer to what Arshia meant by "consistent high-level features" than filtering by species alone.

- Filter existing 539 to remove surface/nearshore visual outliers
- Target ~300-400 images with blue-green underwater consistency
- Retrain on TELUS H200 to 800-1000 kimg
- New checkpoint drops into Prav's Autolume as a swap

**TELUS go/no-go by March 15.** The smoke test (March 9) ran at 10-20x slowdown because the TELUS notebook had no C/C++ compiler — custom CUDA extensions fell back to pure Python (`training-data/README.md:87`). The base v1 run (200 kimg) and resume run (120 kimg) completed despite this, but an 800-1000 kimg run at those speeds could take 4-5+ days and silently eat the entire sprint. **Before committing to this track:**

1. Check if TELUS has resolved the compiler issue since the March 9 smoke test
2. If yes → kick off by March 16, expect 2-4 day training
3. If no → either fix the environment first (install gcc/g++) or **drop this track** and lean fully on multi-layer composition with existing checkpoints

*Note: Prav's HuggingFace find (`Prabhjotschugh/Salish-Sea-Fishes`, 59 images, 4 species) is too small/low-res for StyleGAN but the species selection (chinook, humpback, orca, herring) aligns with Five Threads. Acknowledge the find, don't use it directly.*

### Track C: LoRA / IP Adapters (Briony Style — Exploration Only)
**Owner: Darren (research) + Prav (ComfyUI) | Timeline: March 14-19**

**Keep out of April critical path.** The current Briony corpus (54 images) was broadened beyond marine-only and isn't style-consistent enough for LoRA as-is — yesterday's notes explicitly flagged this. Two things need to happen before LoRA is viable:

1. **Prune the Briony set** to the most stylistically consistent watercolors
2. **Research LoRA training workflow** (tools, parameters, base model selection)

For April, the more achievable version:
- **IP Adapters in ComfyUI** — no training, feed one Briony watercolor as style reference, generate images in minutes. Prav can explore via Derek Schultz / Artificial Images YouTube course.
- **Output:** Pre-rendered still images or short sequences as TD compositing layers (the element-based approach Arshia recommended)

### Track D: Non-GAN Visual Assets (Show-Safe Backup Stack)
**Owner: Prav + Darren | Timeline: Now → April 10**

**This is not abstract "other layers" — these are real, existing tools in the repo:**

| Asset | Script/Source | What It Produces |
|-------|-------------|-----------------|
| Briony dream transforms | `scripts/dream_briony.py` | 13 watercolors × 5 directions — Briony's art made to "breathe, glow, partially dissolve" via img2img |
| Animated watercolors | `scripts/dream_video.py` | Veo 3.1 animations — "fish swim, birds fly, water ripples" while preserving Briony's style |
| Seamless video loops | `scripts/create_loops.py` | Ken Burns, crossfade, Five Threads montage — FFmpeg, any aspect ratio |
| Bioluminescence particles | `web/src/main.js` | 50,000 particle system with GLSL shaders — could translate to TD |
| Moonfish footage | Not yet integrated | Real underwater herring/salmon cinematography |
| Briony originals | `VisualArt/Brionny/` (git-lfs archive) | Full-resolution source paintings for projection — **not** the 512x512 training crops |
| TD generative | `scripts/mycelium.py`, `scripts/psychedelic_video.py` | Mycelium networks, video effect chains — TD native |

**These can be mixed with Autolume output in Resolume.** The installation becomes a genuine multi-source composition. If the GAN looks great, it leads. If not, the other layers carry the weight. Either way, the visual experience is richer.

**Attribution guardrail:** The exhibition outline requires "clear attribution of all artistic sources" and the team has previously flagged the need to distinguish Briony's work from AI derivatives. Three distinct categories in show language and visual treatment:
1. **Briony's original works** — projected from `VisualArt/Brionny/`, credited as her art
2. **Briony-derived AI transforms** — dream transforms, animations, LoRA-generated — credited as "AI interpretation of Briony Penn's watercolors"
3. **GAN outputs** — Autolume latent space — credited as "generative imagery trained on Salish Sea marine photography"

These distinctions matter for wall text, artist credits, and curatorial clarity.

### Track E: Sound (Needs Owner TODAY)
**Owner: ? | Timeline: Must start by March 20**

Sound is the **least-defined core layer** and it's already in the exhibition promise (Tech Rider: "Ableton Live + Max for Live data sonification tools", Exhibition Outline: "Continuous sonic environment, data-influenced sound textures").

**Minimum viable for April:**
- Generative ambient sound that runs on long cycles (hours of non-repeating content)
- Supports contemplation, not stimulation
- **If sound owner + capacity is confirmed today:** add exactly one data mapping (tidal cycle → tempo, or moon phase → harmonic palette). The project framing leans on biosonification, so one clean signal is worth including — but only if someone is building it.
- **If sound ownership is unresolved:** degrade gracefully to ambient-first. A beautiful generative ambient set with no data mapping is still a valid April sound layer. Don't let the data question block getting sound started.

**Phase 2 scope:** Multiple data streams, real-time feeds, complex sonification.

**The question:** Is Prav handling sound himself, or is there a collaborator? Budget? This needs a name and a minimum spec coming out of today's meeting.

---

## Operational Stability: The Missing Risk

The exhibition runs **16 days continuous**. The Tech Rider promises "autonomous system during exhibition hours" with "approximately 1 day setup and calibration." This means:

### Must-Have Deliverables (Before April 10)

1. **Burn-in test**: Run the full stack (Autolume → NDI → TD → Resolume → projector) for 8+ hours continuously. Note crashes, memory leaks, thermal throttling.

2. **Daily restart procedure**: Written checklist that gallery staff or Prav can follow. Power on → launch order → verify output → done in < 5 minutes.

3. **Fallback playback mode**: If Autolume crashes or the GPU overheats, Resolume plays pre-rendered video loops automatically. The audience never sees a desktop or error screen.

4. **Thermal management**: If using Prav's RTX 3060 laptop for 16 days, plan for external cooling and daily restarts. A dedicated desktop with proper airflow is strongly preferred.

5. **Rehearsal at Mahon Hall**: At least one day before opening to calibrate projection mapping, sound levels, and light.

### Hardware Decision

| Option | Pros | Cons |
|--------|------|------|
| Prav's RTX 3060 laptop | Works now, proven pipeline | Thermal risk, 16-day reliability concern |
| Used desktop (RTX 3060/3070) | Proper cooling, reliable for continuous | Needs procurement + budget + setup |
| **Recommendation** | If grant budget exists → dedicated desktop. If not → laptop with daily restart + external cooling + fallback playback mode. |

---

## 6 Decisions to Make With Prav Today

These are practical, not aspirational. Get concrete answers.

### 1. Is the current checkpoint artistically usable as one layer?
Not "is it perfect" — is it interesting enough to project alongside other visual sources? This determines whether Track B (retrain) is urgent or nice-to-have.

### 2. Are we committing to multi-layer composition?
Autolume as one source, Briony dream transforms as another, Moonfish footage as another, TD generative as another. Resolume mixes. **Recommendation: yes.** This is more robust and plays to Prav's skills.

### 3. Laptop or desktop for the exhibition?
Budget available? If yes, get a used RTX 3060/3070 desktop this week. If no, plan the laptop thermal/restart protocol.

### 4. Who owns sound?
A name and a minimum spec. Even "Prav builds a 4-hour generative ambient set in Ableton" is enough for April.

### 5. What exact handoff does Darren deliver before March 20?
Concrete commitments:
- [ ] **TELUS go/no-go by March 15** — check compiler issue, either fix env + kick off B2 training, or drop track
- [ ] Redesigned dataset (B2: underwater scene coherence) kicked off on TELUS (if go)
- [ ] LoRA research summary + Briony corpus pruning recommendations
- [ ] IP Adapter proof-of-concept images (if achievable in the time)
- [ ] **Fallback exhibition media package**: video loops generated locally via `create_loops.py` (crossfade + Ken Burns from Briony originals in `VisualArt/Brionny/` and existing dream stills). This is the irreducible fallback — must not depend on API availability. `dream_video.py` (Veo) animations are a stretch addition if API is up, but the core fallback package is locally generated loops.
- [ ] Updated repo docs reflecting multi-layer direction
- [ ] Sound strategy note (what data Eve has, which one signal for April, minimum spec)

### 6. Eve's data — which one signal for April?
Eve is analyzing herring spawn index, tidal cycles, Fraser discharge, moon phase, SST. The project framing promises data-influenced sound, so commit to **exactly one data mapping for April** — not zero, not many. The strongest candidates:
- **Tidal cycle** → visual tempo or sound rhythm (clean, cyclical, immediately legible as "of this place")
- **Moon phase** → harmonic palette or color temperature (long cycle, poetic)
- **Herring spawn index** → seasonal intensity parameter (most aligned with project narrative, but less real-time)

Ask Prav which one resonates artistically. Eve can prepare the data; the question is which signal and which output parameter.

---

## What the Exhibition Needs to Deliver (Gap Analysis)

| Exhibition Promise | How We Meet It | Status |
|-------------------|---------------|--------|
| "AI-assisted dreaming visuals trained on naturalist illustration, marine photography, underwater footage" | Autolume (marine checkpoint) + Briony dream transforms + Moonfish footage — multi-layer in Resolume | **Foundation exists, integration needed** |
| "Visuals flow, dissolve, and recombine" | Autolume latent navigation + Resolume crossfades + Ken Burns loops | **Ready** — GAN does this naturally; `create_loops.py` adds more |
| "Continuous sonic environment" | Ableton generative ambient | **Not started — needs owner** |
| "Presence gently influences the system" | Webcam/Kinect → TD → OSC | **Not started — optional for April** |
| "Autonomous Installation Mode" | Pre-rendered content in Resolume + fallback playback | **Needs burn-in testing + restart procedure** |
| "Live Performance Mode" | MIDI/OSC → Autolume + Resolume | **Pipeline proven, mapping needed** |
| "1 day setup and calibration" | Rehearsal at Mahon Hall | **Need to schedule** |

---

## The Big Picture

The April show is achievable. The exhibition docs are thoughtful, well-scoped, and grounded in restraint ("succeeds by doing less, not more"). The training pivot is a production detail.

What the installation actually needs:
1. **Prav mastering Autolume** as one performance instrument (underway)
2. **Multi-layer visual composition** so no single element carries everything (commit today)
3. **A sound layer with a named owner** (even simple generative ambient)
4. **Reliable hardware + operational stability** (burn-in, restart procedure, fallback playback)
5. **One rehearsal day at Mahon Hall** before opening

Everything else — better checkpoints, LoRA style transfer, data sonification, Kinect presence — is additive improvement on a foundation that already works.

---

## Conversation Flow

1. **Aesthetic check** — what does the checkpoint output feel like projected? Usable as one layer?
2. **Multi-layer commitment** — Autolume + dream transforms + footage + TD generative. All in Resolume.
3. **Hardware** — laptop or desktop? Budget?
4. **Sound owner** — who, minimum spec, when
5. **Darren's March 20 handoff** — concrete deliverable list
6. **Prav's solo trajectory** (March 20-28) — Autolume mastery, OSC/MIDI, multi-machine NDI, Resolume workflow, ComfyUI exploration, sound
7. **Eve's data** — one signal for April, rest for Phase 2
8. **Operational stability** — burn-in test plan, restart procedure, fallback mode
9. **Rehearsal scheduling** — when can you get into Mahon Hall?
