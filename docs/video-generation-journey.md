# Salish Sea Dreaming — Video Generation Journey

> *"Each creature contains the whole ecosystem."*

A technical and creative log of our experiments generating AI watercolor animation for the Salt Spring Spring Art Show (April 10-26, 2026).

**Team:** Darren Zal, Pravin Pillay (Creative Director), Shawn Anderson, Briony Penn (artist)
**Infrastructure:** 3x NVIDIA H200 GPUs (150GB VRAM each) on TELUS Sovereign AI Factory
**Style:** Briony Penn LoRA (SD 1.5, trained on 22 watercolor paintings, trigger: `brionypenn`)
**Duration:** 4 days of experiments, 600+ generated videos

---

## The Breakthrough: "Landscape Dissolution"

After 600+ experiments across 4 days, we discovered that **programmatic Boids flocking simulation + ControlNet depth rendering + Briony's watercolor LoRA** produces something magical: creature shapes that dissolve into and become the Pacific Northwest landscape.

Fish shapes become trees. Bird murmurations become cloud patterns. The waterline divides two worlds. The creature IS the landscape.

This is the project's thesis made visible: **every organism contains the blueprint of its entire ecosystem.**

### The Pipeline

```
Blender Boids simulation (200 agents, 30-40 seconds)
    ↓
Depth map sequence (512x512 PNGs)
    ↓
Fixed background (SD 1.5 + LoRA, generated once)
    ↓
Per-frame render: img2img on background + ControlNet depth + LoRA
    ↓
Dynamic ControlNet scale per narrative phase
    ↓
Temporal gaussian smoothing
    ↓
Video assembly (30fps or 16fps)
```

---

## Exhibition Candidate Videos

| # | Video | Duration | Description |
|---|-------|----------|-------------|
| 01 | Landscape Dissolution | 56s | Hero piece — fish school rises, crosses waterline, becomes murmuration, murmuration merges with tree canopy, converges into whale. All in Briony's watercolor style. |
| 02 | Fish Becoming Landscape | 6s | The accidental discovery — fish shapes dissolving into trees, coastline, birds. |
| 03 | Orca Breaching | 5s | Orca surfacing with birds, watercolor style. |
| 04 | Herring Morphic Resonance | 5s | A fish and a school oscillating — one becomes many becomes one. |
| 05 | Murmuration to Whale | 10s | Birds converging into whale shape. |
| 06 | Boids Watercolor | 10s | Original Boids + ControlNet experiment. |
| 07 | Estuary Painting Alive | 10s | Briony's actual estuary painting animated with Wan I2V. |
| 08 | Shore to Sea Transect | 29s | Three Briony paintings morphing with zoom-out. |
| 09 | Salmon to Forest | 28s | Nitrogen cycle — salmon dissolving into root structure and forest. |

---

## The Journey: What We Tried

### Phase 1: Style Transfer on Real Footage (Day 1) ✅

**What:** Applied Briony LoRA to Moonfish underwater footage and David Denning photos.
**Result:** 18 production-quality styled videos + 14 styled stills.
**Learning:** Style transfer on REAL footage works perfectly. The challenge is generating new creative motion.

### Phase 2: AI Video Generation for Metamorphosis (Days 1-2) ❌

**What:** Tried AnimateDiff, Wan 2.1 T2V (1.3B and 14B), CogVideoX, VACE.
**Result:** 400+ clips. AI generates beautiful footage but CANNOT do structural metamorphosis. "Herring transform into birds" produces fish, then birds — never fish BECOMING birds.
**Learning:** Text-to-video models don't understand structural transformation.

### Phase 3: Two-Stage Pipeline (Days 2-3) ⚠️

**What:** Generate realistic motion with Wan T2V → extract depth → re-render in Briony's style.
**Result:** Style works but Wan depth maps are noisy/blobby = visual chaos.
**Learning:** Clean depth maps are everything. AI-generated depth is too noisy.

### Phase 4: Programmatic Simulation + AI Style (Days 3-4) ✅ BREAKTHROUGH

**What:** Blender Boids → depth maps → ControlNet + LoRA.
**Result:** The "landscape dissolution" discovery. Clean, readable, meaningful.
**Learning:** Separate simulation from style. Each component does one thing well.

### Phase 5: Research-Informed Refinement (Day 4+) 🔬 IN PROGRESS

- Dynamic ControlNet scale (0.40 during canopy = tree↔bird ambiguity)
- Alternative simulations: reaction-diffusion, DLA growth, fluid dynamics
- Longer durations (90-180 seconds) for contemplative pacing
- Multi-layer Resolume composition
- Seamless looping, higher resolution

---

## Key Principles

1. **Real art in, AI motion out.** Start from Briony's paintings or controlled simulations.
2. **Separate motion from style.** Programmatic simulation + AI LoRA. Don't combine.
3. **Clean depth maps are everything.** Simple depth = better results.
4. **The creature IS the landscape.** The most powerful metaphor emerged accidentally.
5. **Fixed seed = spatial coherence.** Same seed across all frames.
6. **Cherry-pick, don't optimize.** Generate many, curate ruthlessly.

---

## Technical Stack

| Component | Tool |
|-----------|------|
| Simulation | Blender 4.3 (Boids, mesh morphing, depth export) |
| Style | SD 1.5 + Briony LoRA + ControlNet depth |
| Video Gen | Wan 2.1 T2V/I2V 14B (ComfyUI) |
| Smoothing | Temporal gaussian + RAFT optical flow |
| Playback | Resolume Arena (multi-layer projection) |
| Real-time | StreamDiffusion + TouchDesigner (30fps) |
| GPUs | 3x NVIDIA H200 (TELUS Sovereign AI Factory) |

## Research Reports

- [Video Style Transfer Techniques](docs/research-video-style-transfer.md)
- [Practical Metamorphosis](docs/research-metamorphosis-practical.md)
- [Latent Ecological Simulations](docs/research-latent-ecological-simulations.md)
- [Video Generation Status & Learnings](docs/video-generation-status.md)
