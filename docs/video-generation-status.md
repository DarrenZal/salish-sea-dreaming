# Video Generation — Status & Learnings

**Date:** 2026-04-04 (updated after metamorphosis production sprint)
**Author:** Darren + Claude
**Total generated:** 600+ videos across 5 rounds of experiments
**Exhibition deadline:** April 10, 2026 (6 days)

## Infrastructure

| Notebook | URL | Token | GPU | VRAM | RAM |
|----------|-----|-------|-----|------|-----|
| model-deployment | model-deployment-0b50s.paas.ai.telus.com | 8f6ceea09691892cf2d19dc7466669ea | H200 (GPU-53b2) | 143 GB | 1.8 TB |
| ssd-style-transfer-2 | ssd-style-transfer-2-0b50s.paas.ai.telus.com | 15335440de57b5646cd4c25bdf1957d5 | H200 (GPU-9950) | 143 GB | 1.8 TB |
| ssd-style-transfer-3 | ssd-style-transfer-3-0b50s.paas.ai.telus.com | ada49fecb49f8b4a4d53a5fb44f91af0 | H200 (GPU-eb8e) | 143 GB | 1.8 TB |

**3 separate H200 nodes** — different GPU UUIDs, different hostnames. Can run different models simultaneously.
Note: model-deployment has Shawn's vLLM Qwen server (`qwen.ipynb`). Kill PID before loading large models, restart after.

---

## What Works (Ranked)

### Tier 1: Production Ready

**1. Style Transfer on Video (Moonfish footage → Briony LoRA)**
- Best technique: ControlNet for subjects with clear shapes (fish, sea stars), img2img for complex textures (kelp, reef, tidepools)
- Strength sweet spot: s=0.35-0.55 for img2img, controlnet_conditioning_scale=0.55-0.65
- RAFT optical flow smoothing for 60fps
- Matched originals at same resolution/fps for Resolume crossfading
- **Why it works:** Real footage provides temporal coherence. LoRA just adds style per-frame. No need to generate motion.
- **Output:** `output/` — 18 production videos

**2. Style Transfer on Stills (Denning photos → Briony LoRA)**
- Same ControlNet vs img2img per-subject selection
- 768px production quality
- ~2.5s per image on H200
- **Output:** `output/denning/`, `output/denning-for-prav/`

### Tier 2: Promising, Needs Iteration

**3. Wan I2V 14B — Animating Briony's Actual Paintings**
- Feed her real paintings as I2V input → model generates motion grounded in her art
- Estuary animation looked great (bears moving, salmon swimming, water flowing)
- Mandala animation (flora-fauna) was interesting
- **Why it works:** Starting from REAL art means frame 1 is already Briony. The model adds motion without needing to "learn" her style.
- **Why it's not Tier 1 yet:** Some clips have artifacts, some look too photorealistic (model fights the watercolor style). Needs prompt tuning.
- **Critical lesson:** Must use portrait dimensions (480x832) for portrait paintings! 832x480 warps them.
- **Output:** `output/overnight-results/node1-r3/r3_1a_wan_portrait/`, `r3_1b_tsawout_mandala/`, `r3_1c_other_mandalas/`

**4. Prompt Walk with Fixed Seed (SD 1.5 + Briony LoRA)**
- Encode two prompts, SLERP between embeddings, same seed every frame
- All 3 seeds (42, 123, 256) produced interesting results
- Smooth semantic shift: herring gradually become birds, kelp becomes fish, etc.
- **Why it works:** Fixed seed locks spatial composition. Only the semantic content drifts. No frame-to-frame jumps because the seed anchors the structure.
- **Limitation:** Still looks like a dissolve at the pixel level, but the semantic shift is more interesting than pure SLERP.
- **Output:** `output/overnight-results/node2/2c_prompt_walk_*_smoothed.mp4`

**5. ControlNet Depth Map Morphing**
- Generate depth maps for two keyframes, interpolate the depth maps, render each through ControlNet + LoRA
- Structural transformation is guided by geometry, not just pixel blending
- **Why it works:** Depth interpolation handles the 3D structural shift. The model fills in Briony-style details. Each frame is independently valid.
- **Limitation:** Depth estimation on watercolor paintings is imprecise — depth maps are noisy.
- **Output:** `output/overnight-results/node2/2b_controlnet_depth_morph_smoothed.mp4`, `node2-r3/r3_2c_depth_morph/`

**6. Boids + ControlNet Rendering**
- Programmatic flocking simulation → render each frame through ControlNet + LoRA
- Enhanced version with fish/bird silhouette agents
- **Why it works:** Full control over motion. AI only handles rendering, not motion planning. Each agent individually morphs.
- **Limitation:** The ControlNet rendering doesn't always respect the Boids structure — sometimes ignores the depth map. Agent shapes are still crude.
- **Next step:** Better silhouettes, stronger ControlNet conditioning, or use Canny edges instead of depth.
- **Output:** `output/overnight-results/node3/exp3a_boids/`, `node3-r3/r3_3a_boids_enhanced/`

### Tier 3: Interesting Concepts, Not Yet Working

**7. VAE Latent Interpolation (SD + Wan VAE)**
- Encode two keyframes, SLERP in latent space, decode
- Wan VAE slightly better than SD VAE (designed for video)
- **Why it's interesting:** Fast, no GPU inference needed for intermediate frames
- **Why it doesn't fully work:** SLERP through latent space passes through low-density regions → ghosting, blending artifacts. Need manifold-aware interpolation (geodesics on the data manifold, per research report).
- **Output:** `output/overnight-results/node2/exp2d_*_slerp.mp4`

**8. AnimateDiff Salmon→Roots (clip 2e_p2_s123)**
- One clip out of 80+ almost captured salmon dissolving into tree roots
- **Why the one clip worked:** Lucky seed + right prompt → the model found a latent path where fish body ≈ root structure
- **Why it's not reliable:** AnimateDiff generates each clip independently. Can't control which seed produces metamorphosis vs just a scene. Need to generate many seeds and cherry-pick.
- **Output:** `output/overnight-results/favorites/2e_p2_s123_clip.mp4`

**9. Food Web Cycle / Ecological Cascade**
- Sequence of scenes telling the salmon-forest story
- Individual scenes look good but transitions between them are cuts
- **Next step:** Use prompt walk or depth morph for transitions between scenes, not just concatenation
- **Output:** `output/overnight-results/node3/exp3i_foodweb/`

**10. Outpainting Spiral**
- Concept: zoom into Briony's painting, generate new content at edges
- Interesting idea but current execution is rough — generated content doesn't match her style well enough
- **Next step:** Stronger LoRA conditioning, use actual painting crops for context, slower zoom
- **Output:** `output/overnight-results/favorites/exp3j_outpaint_spiral.mp4`

---

## What Doesn't Work (And Why)

### Text-to-Video for Metamorphosis
**Models tried:** Wan 1.3B T2V, Wan 14B T2V, AnimateDiff
**Result:** Generates realistic footage of "a school of fish" then "birds flying" — NOT fish transforming into birds.
**Why:** T2V models learn to generate plausible video from text descriptions. "Fish transform into birds" is not a scene they've seen in training data. They interpret it as "a video containing fish and birds" and generate them sequentially or simultaneously, not as one form structurally becoming the other. True metamorphosis requires *structural* understanding of how forms relate, which current T2V models lack.
**Verdict:** Stop trying T2V for metamorphosis. Use it for single-scene animation instead.

### Iterative Frame Chaining (Feedback Loops)
**Result:** "Colored confetti" — noise accumulates exponentially over 300 frames.
**Why:** Each img2img pass adds a small amount of noise/artifacts. When you feed the output back as input, errors compound. After 50+ iterations, the image is unrecognizable. This is a fundamental property of iterated noisy processes.
**Verdict:** Never use previous frame as sole input for next frame. Always anchor to source material.

### AnimateDiff for Scene Transitions
**Result:** Each 16-frame clip is independent. No temporal coherence between clips.
**Why:** AnimateDiff's motion module operates within a single generation window (16-32 frames). There's no mechanism to carry motion state from one generation to the next. Each clip starts from a fresh noise sample.
**Verdict:** Use AnimateDiff for single scenes only. For transitions between scenes, use prompt walks, depth morphing, or RAFT interpolation.

### RAVE
**Result:** Could not install — Python 3.8 + old diffusers dependency hell.
**Verdict:** Skip unless we find a modernized fork.

### CogVideoX-5B
**Result:** Persistent corrupted tokenizer (spiece.model) on TELUS CDN.
**Verdict:** May work on a different hosting provider. Not worth fighting on TELUS.

### Wan 14B on 32GB RAM Pods
**Result:** OOM during T5-XXL text encoder shard loading.
**Why:** `enable_model_cpu_offload()` loads the full model into RAM first (~28GB weights + Python overhead > 32GB).
**Fix:** Use pods with 64GB+ RAM, or the 1.8TB model-deployment node.

### Wrong Aspect Ratio for Wan I2V
**Result:** Portrait paintings rendered at 832x480 (landscape) → warped/stretched.
**Why:** Hardcoded dimensions in experiment script.
**Fix:** Always match input aspect ratio. Briony's paintings are ~800x1024 portrait → use 480x832.

---

## Key Principles Learned

### 1. Real Art In, AI Motion Out
The best results come from feeding Briony's ACTUAL paintings to I2V or using her LoRA on REAL footage. The AI should add *motion* to existing art, not generate art from scratch. Her style is too specific for text prompts alone.

### 2. Separate Motion from Style
The "Watercolor V2V" pipeline concept from the research report is correct: generate motion first (even if it looks photorealistic), then apply style as a post-process. Trying to do both at once compromises both.

### 3. Fixed Seed = Spatial Coherence
When generating frame sequences, using the same seed across all frames locks the spatial composition. Only change the prompt embedding (semantic shift) or ControlNet input (structural shift). This prevents the random frame-to-frame jumps that make videos look like slideshows.

### 4. Structural Guidance Beats Latent Interpolation
ControlNet depth morphing > VAE SLERP > pixel blending. The more structural guidance you give the model, the more coherent the transitions. Pure latent interpolation passes through "ghost" regions. Depth maps keep the 3D structure valid at every intermediate point.

### 5. Cherry-Pick, Don't Optimize
With AnimateDiff and similar tools, generating 20 seeds and picking the best one is more productive than trying to perfect a single generation. The variance between seeds is huge — some produce beautiful accidents, most produce nothing interesting. Generate many, curate ruthlessly.

### 6. Temporal Smoothing is Essential
Every frame sequence benefits from: (a) RAFT optical flow interpolation between keyframes, (b) temporal gaussian smoothing (window=7-9, sigma=2.0). Apply both as post-processing to any generated video.

### 7. The Waterline is the Hardest Part
Briony's cross-section paintings have a distinctive waterline. This is the hardest element to maintain during transitions because it's a strong horizontal structure that doesn't interpolate well between compositions where it's at different heights or curvatures.

---

## What to Try Next

### High Priority (most likely to produce exhibition content)

1. **Wan I2V 14B on all Briony paintings at correct portrait dimensions** — iterate on prompts. "The painting comes alive" works better than "fish transform into birds." Let the model animate what's already there rather than trying to change it.

2. **Prompt walk gallery** — generate 30-second prompt walks for each ecological transition (herring→birds, kelp→herring, salmon→forest, bear→ferns) at multiple seeds. Cherry-pick the best. These are smooth, coherent, and clearly in Briony's style.

3. **Salmon→roots iteration** — the one clip (2e_p2_s123) that almost nailed it. Generate 100+ seeds with that exact prompt. One in 20 might be exhibition-worthy. The nitrogen cycle story is worth finding.

4. **SVD on Briony's mandalas** — her Tsawout 13-Moon wheel is perfect for "the painting breathes." SVD preserves the source image well and adds subtle motion. Try multiple motion_bucket_id values.

5. **ControlNet depth morph between Briony's actual paintings** — use her Estuary→Inshore→Offshore paintings directly, not generated keyframes.

### Medium Priority (research directions)

6. **VTG/SAGE/CHIMERA frameworks** — purpose-built for image morphing. We identified them in the research report but haven't successfully installed any. Need to find working implementations or repos.

7. **Boids with better rendering** — the concept works. Need: (a) actual fish/bird model silhouettes, (b) stronger ControlNet conditioning, (c) more frames, (d) Canny edge detection instead of depth.

8. **Deforum-style prompt scheduling** — long continuous generation with prompts that change on a schedule. Hasn't been tried yet with the Briony LoRA.

9. **Train a Wan-compatible LoRA** — would let Wan 14B generate video directly in Briony's style. Eliminates the V2V post-processing step. Requires researching Wan LoRA training pipeline.

### Lower Priority (speculative)

10. **Outpainting spiral from mandala center** — zoom into Tsawout wheel, each sector reveals deeper ecological layers
11. **Recursive "fish of fish" compositing** — holonic zoom effect, purely computational (no GPU needed)
12. **Real-time StreamDiffusion + LoRA** — already working in TouchDesigner (Leo/Prav session March 28)

---

## Assets & Outputs

### Briony Source Material
- `VisualArt/Brionny/Illustrations/Central-Coast-*` — 3 cross-section paintings
- `VisualArt/Brionny/Paintings/Ecological-Mandalas/` — 2 ecological mandalas
- `VisualArt/Brionny/Watercolour-Mandalas/` — 4 watercolour mandalas (Tsawout, Garry Oak, etc.)
- `briony-lora/briony_watercolor_v1.safetensors` — SD 1.5 LoRA, trigger `brionypenn`

### All Favorites
- `output/all-favorites/` — 17 curated videos (55MB)
- Also shared via Dropbox: `output/denning-for-prav/all-favorites/`

### Full Output Archive
- `output/overnight-results/node1/` — Round 1 Wan I2V (46 videos)
- `output/overnight-results/node2/` — Round 1 SD experiments (127 files)
- `output/overnight-results/node3/` — Round 1 creative experiments (308 files)
- `output/overnight-results/node1-r3/` — Round 3 portrait fix + mandalas (52 videos)
- `output/overnight-results/node2-r3/` — Round 3 salmon-roots + walks + morph (54 videos)
- `output/overnight-results/node3-r3/` — Round 3 SVD + dreaming + boids (45 videos)

### Research
- Deep research report: `~/Downloads/Artistic Video Metamorphosis Techniques.md`
- Key frameworks identified: VTG, SAGE, CHIMERA, MotionPro, FlowEdit, PainterLongVideo

---

## Metamorphosis Sprint Learnings (April 3-4)

### The Breakthrough: "Landscape Dissolution"

Accidentally discovered that rendering Boids depth maps through ControlNet + LoRA with **landscape prompts** creates a beautiful effect where creature shapes dissolve into/become landscape elements. Fish shapes become trees, coastlines, clouds. The creature forms literally ARE the landscape.

**Why it works:** ControlNet forces the model to follow the Boids structure. The landscape prompt makes it interpret those structures as natural features. The Boids motion creates organic movement. The LoRA adds Briony's watercolor style. Each component does one thing well.

**Best result so far:** `output/boids_v2/boids_v2_dissolution_16fps.mp4` — 56 seconds, fish in water + trees on land + birds in sky, the murmuration morphing with the treetops. User said: "it kind of looks like a fish that gets transitioned into the trees and the birds."

**Recipe:**
- Fixed background generated once with LoRA (Pacific Northwest coastal landscape)
- img2img on background at strength 0.55
- ControlNet depth at scale 0.75
- Prompt progression matching Boids phases
- Same seed (42) throughout
- Temporal smoothing window=9, sigma=2.5

### What's Working (Updated Ranking)

**Tier 1: Exhibition Candidates**
1. **Boids Dissolution** — Programmatic Boids → depth maps → ControlNet + LoRA with landscape prompts. Best metamorphosis technique we've found. Clean, readable, meaningful.
2. **Moonfish Footage Style Transfer** — Real video → LoRA. Already production quality.
3. **Wan I2V on Briony's Paintings** — Her actual paintings animated. Portrait aspect (480x832). Estuary and inshore look great.

**Tier 2: Promising, Needs More Iteration**
4. **School→Murmuration bg-anchor** — The "fish becoming trees and birds" accidental discovery. Needs longer versions with better narrative arc.
5. **Eco narrative clips** (orca surfacing, herring tightening) — Some look good through LoRA but motion from Wan T2V is noisy/blobby.
6. **Prompt walks** — Smooth semantic transitions in Briony's style.

**Tier 3: Interesting Concepts, Not Exhibition-Ready**
7. Living paintings (breathing) — too subtle or drifts to abstract
8. Morphic resonance (fish↔school) — concept is right, execution is messy
9. EbSynth flow propagation — improves coherence but underlying clips need to be better
10. VACE reference-image style transfer — too weak, not really Briony's style

### Key Principle: Clean Depth Maps Are Everything

The single most important factor for quality: **how clean and structured are the depth maps feeding into ControlNet.**

| Depth Source | Quality | Result |
|-------------|---------|--------|
| Blender Boids (programmatic) | Clean, structured, controllable | Best results — clear forms, readable |
| ZoeDetector on real video | Good, natural depth | Good for style transfer on existing footage |
| ZoeDetector on Wan T2V output | Noisy, blobby, overlapping | Messy — overlapping layers, unclear forms |
| Complex 3D scenes (salmon+roots) | Too many depth layers | Incoherent — model renders each layer separately |

**Rule: Simple depth = better results.** One group of agents against a clean background beats complex multi-object scenes every time.

### What Doesn't Work (Confirmed)

- **Wan T2V for metamorphosis** — Generates scenes, not transformations. 50+ prompts tested, 0 convincing morphs.
- **VACE reference-image conditioning** — Too weak for style transfer. Doesn't reproduce Briony's actual linework/washes.
- **Iterative img2img (feedback loops)** — Drifts to abstract blobs within 100-300 frames, even at s=0.08.
- **Complex depth maps with many objects** — ControlNet renders them as disconnected visual layers.
- **Wan T2V depth → ControlNet** — Noisy source = noisy result. Overlapping shapes produce visual chaos.
- **ComfyUI VACE V2V pipeline** — Got it working but output was too abstract/bright, didn't look like Briony's style.

### Boids v3 (In Progress)

Complete cycle: fish school → rise → cross waterline → murmuration in tree canopy (trees and birds share space — bottom agents slow = tree-like, top agents swirl = bird-like) → murmuration dives back into water → fish school again. 1200 frames, 40 seconds. Rendering now on Node 1.

### Output Locations

| Directory | Contents |
|-----------|----------|
| `output/boids_v2/` | Hero dissolution clip (30s/56s) |
| `output/dissolution/` | Salmon→forest, kelp→forest, dreaming abstract, landscape variants |
| `output/refined/` | Living paintings, murmuration bg-anchor, eco HQ re-renders |
| `output/iterations/` | Morphic resonance, orca→salmon, living painting fixed |
| `output/eco-narrative-briony/` | 10 eco clips through LoRA |
| `output/ebsynth-flow/` | Temporal coherence experiments |
| `output/overnight-results/` | All overnight experiments (rounds 1-3) |
| `output/all-favorites/` | Earlier curated favorites |
| `output/vace-v2v-full/` | VACE V2V attempts |
| `output/wan14b/` | Wan 14B T2V clips |
| `output/denning-for-prav/` | Denning stills + Dropbox deliverables |
