# Overnight GPU Plan — 8 Hours on 3x H200

**Date:** 2026-04-02 night
**Goal:** Find a technique that produces true metamorphosis animation in Briony Penn's watercolor style.

## Strategy

Run 3 different approaches in parallel on the 3 nodes. Each approach tackles the same test case:
**"A school of herring transforms into a murmuration of birds"** — using Briony's Inshore painting as the starting keyframe and her Offshore painting (with seabirds) as the ending keyframe.

---

## Node 1: model-deployment (Shawn's 256GB node)
**Approach: Wan I2V 14B — Image-to-Video from Briony's Paintings**

Load Wan I2V 14B (image-to-video). Feed it Briony's actual paintings as starting frames with transformation prompts. This grounds the generation in her real art style from frame 1.

Steps:
1. Kill vLLM if still running, free VRAM
2. Load `Wan-AI/Wan2.1-I2V-14B-480P-Diffusers`
3. Upload Briony's Inshore painting as input image
4. Generate with prompts describing the herring rising and transforming
5. Try multiple seeds (10+) and prompt variations
6. Also try: Estuary painting → salmon running upstream, Offshore painting → whales diving deep
7. Render at 81 frames (10s at 8fps) per clip
8. If I2V doesn't do metamorphosis well, try: generate first frame (herring in Briony style) with SD 1.5 + LoRA, use as I2V input

Estimated: ~5 min per clip × 20 clips = ~2 hours of generation. Rest of time for prompt iteration.

---

## Node 2: ssd-style-transfer-2
**Approach: VTG / CHIMERA — Purpose-Built Image Morphing**

Install and test the actual morphing frameworks designed for this problem.

Steps:
1. Clone VTG repo (arxiv.org/html/2508.01698v1) or CHIMERA (arxiv.org/html/2512.07155v1)
2. These take two keyframe images and generate a morph between them
3. Keyframe A: crop of herring from Briony's Inshore painting (or generate one with SD 1.5 + LoRA)
4. Keyframe B: crop of birds from Briony's Offshore painting (or generate one)
5. Generate morphing transitions at various settings
6. If VTG/CHIMERA don't have diffusers implementations, try SAGE (arxiv.org/html/2510.24667v2)
7. Fallback: Use Wan T2V 14B with much more specific "morphing" prompts — describe the intermediate states frame by frame

Estimated: 1-2 hours for setup, 3-4 hours for generation experiments.

---

## Node 3: ssd-style-transfer-3
**Approach: Hybrid — Boids + Style Transfer Pipeline**

The most controllable approach: generate motion programmatically, render in Briony's style.

Steps:
1. Write a Boids flocking simulation in Python (simple — 3 rules: separation, alignment, cohesion)
2. Simulate 200 agents starting as a fish school (tight, underwater, moving right), gradually transitioning to bird murmuration (wider, aerial, swirling)
3. Render the Boids as simple shapes (dots/arrows) on a depth map or motion mask
4. Use ControlNet + Briony LoRA to render each frame in watercolor style, conditioned on the Boids positions
5. RAFT smooth the result
6. Also try: render Boids as actual fish silhouettes → bird silhouettes, use as ControlNet depth input
7. This gives us FULL CONTROL over the motion — each "agent" can individually morph from fish to bird shape

Estimated: 2 hours for Boids sim + rendering pipeline, 4 hours for iterating on the look.

---

## Success Criteria

A clip is "exhibition-worthy" if:
- Forms visibly transform (not dissolve) — you can see individual herring becoming individual birds
- Temporal coherence — no frame-to-frame jumps
- Looks like it could be a Briony Penn watercolor in motion
- 10+ seconds long at 30fps
- Evokes the ecological cascade story

## Execution Notes

- All 3 nodes have 1.8TB RAM and 143GB VRAM — no memory constraints
- Wan 14B is already cached on model-deployment and ssd-style-transfer-2
- Briony LoRA is on ssd-style-transfer-2 and ssd-style-transfer-3
- Briony paintings need to be uploaded to model-deployment
- Each approach should save results to `/home/jovyan/output/` with descriptive names
- Run generation in nohup/background so websocket drops don't kill it

---

## Experiment Queues (Priority Order)

Each node runs experiments sequentially. If the primary approach fails or produces poor results, move to the next experiment in the queue.

### Node 1 Queue (model-deployment)

**1A. Wan I2V 14B — Animate Briony's Paintings** (Primary — described above)

**1B. Wan T2V 14B — Explicit Intermediate State Prompts**
Instead of one prompt describing the full transformation, generate separate clips for each intermediate state and stitch:
- Clip 1: "Watercolor illustration of herring swimming tightly packed underwater, some fish at the surface beginning to leap"
- Clip 2: "Watercolor illustration of fish-bird hybrid creatures, half-fish half-bird, emerging from ocean surface, fins becoming wings"
- Clip 3: "Watercolor illustration of dark birds taking flight from ocean surface, last traces of silver scales on their bodies"
- Clip 4: "Watercolor illustration of a murmuration of birds swirling against grey sky"
Then RAFT-interpolate between the last frame of each and first frame of the next.

**1C. Wan I2V — Photo-to-Watercolor Metamorphosis**
Use a real Moonfish underwater photo as I2V input, prompt: "the photograph gradually transforms into a watercolor painting, photographic detail dissolving into brushstrokes and watercolor washes, pen-and-ink lines emerging." This is a different kind of metamorphosis — reality becoming art — which is literally what the installation is about.

**1D. Wan T2V 14B — Ecological Cascade Narrative (Long Form)**
Generate 6 connected clips using PainterLongVideo-style approach: use the last 8 frames of each clip as "motion frames" seed for the next clip's generation, creating temporal continuity:
1. Open ocean waves → camera descends underwater
2. Kelp forest swaying → herring appear swimming through
3. Herring school tightens → salmon appear chasing them
4. Salmon swimming upstream → bear catches salmon
5. Bear on riverbank → dissolves into forest
6. Forest floor → mushrooms and ferns, cycle complete

**1E. Deforum-Style Zoom with Wan**
Generate a static Briony-style scene with T2V, then use it as I2V input with a slow zoom prompt. Repeat: zoom into the center, generate new content that continues the scene. Creates infinite zoom effect where new ecological details emerge as you go deeper.

---

### Node 2 Queue (ssd-style-transfer-2)

**2A. VTG / CHIMERA / SAGE — Image Morphing** (Primary — described above)

**2B. Dual-Image Latent Interpolation with Wan VAE**
Instead of SLERP (which gave us dissolves), try:
- Encode keyframe A and B with Wan's VAE (better than SD 1.5 VAE for video)
- Use the Wan T2V denoiser to "denoise" the interpolated latents — this forces each intermediate frame through the model's learned distribution, producing valid images rather than blended ghosts
- This is the "manifold-aware interpolation" from the research report

**2C. ControlNet Depth Morphing**
- Generate depth maps for keyframe A (herring painting) and keyframe B (birds painting)
- Smoothly interpolate the depth maps (this is just geometry, no style)
- Render each interpolated depth map through SD 1.5 + Briony LoRA + ControlNet
- The depth interpolation handles the structural transformation, the model handles making it look like Briony's art

**2D. SD 1.5 + LoRA "Prompt Walk" with Fixed Structure**
Generate a grid of images that smoothly transition between two prompts:
- "brionypenn watercolor of silver herring swimming underwater in a school" (weight: 1.0→0.0)
- "brionypenn watercolor of dark birds flying in a murmuration against grey sky" (weight: 0.0→1.0)
Use the same seed throughout so the composition is stable. Generate 120 frames. This is different from AnimateDiff — it's single-image generation with prompt interpolation, keeping spatial coherence through the seed.

**2E. FlowEdit — Inversion-Free Video Style Transfer**
If we can install FlowEdit:
- Take one of the Wan 14B realistic fish→birds clips (from our T2V attempts)
- Apply FlowEdit to re-render it in Briony's watercolor style
- The motion is already there (even if it's "fish then birds" not "fish becoming birds") — FlowEdit might make it look artistic enough to be interesting

**2F. Train a Wan LoRA on Briony's 22 Paintings**
If time allows (likely won't finish overnight but can start):
- Use kohya_ss or diffusers training to fine-tune a Wan-compatible LoRA on the 22 Briony watercolors
- This would let Wan 14B generate video directly in her style, eliminating the V2V post-process step
- Even partial training (100 steps) might capture enough style signal

---

### Node 3 Queue (ssd-style-transfer-3)

**3A. Boids + ControlNet Hybrid** (Primary — described above)

**3B. Boids + Briony Painting Compositing**
Instead of ControlNet rendering (which might lose Briony's style), try:
- Run Boids simulation outputting position + rotation + scale for each agent
- Cut out individual herring from Briony's Inshore painting (there are actual herring in it)
- Cut out individual birds from Briony's Offshore painting
- For each frame, composite the agents using the Boids positions, gradually crossfading each agent from fish cutout to bird cutout
- This uses Briony's ACTUAL art, not AI-generated approximation
- Add watercolor paper texture overlay and edge softening for painterly feel

**3C. AnimateDiff — Longer Clips with Prompt Travel**
We tried 16-frame clips before. Try:
- Install AnimateDiff with FreeInit (better temporal consistency)
- Generate 32-frame clips (double length)
- Use prompt travel: smoothly shift the prompt embedding from herring → birds over the 32 frames
- Generate 10+ clips with different seeds, cherry-pick the best

**3D. Stable Video Diffusion (SVD) — Animate Briony's Stills**
- Load SVD (image-to-video model, ~4GB)
- Feed it a Briony watercolor of herring as the input image
- SVD generates 25 frames of plausible motion from the still
- This won't do metamorphosis but might make her paintings "breathe" beautifully — kelp swaying, fish swimming, water rippling
- Run on all 22 Briony paintings → library of animated watercolors for the exhibition

**3E. DynamiCrafter — Creative Image Animation**
Alternative to SVD that's reported to handle more creative motion:
- Feed Briony's herring painting + text prompt "the herring begin to swim and the painting comes alive"
- May produce more dramatic animation than SVD

**3F. Depth-Guided Morphing with MiDaS**
- Run MiDaS depth estimation on both Briony paintings (herring scene and bird scene)
- Create a smooth depth map morph between them
- At each frame, use the interpolated depth as ControlNet input
- Use a blended prompt that shifts from herring to birds
- The depth map handles 3D structure, the prompt handles semantic content

**3G. Outpainting Spiral**
- Start from the center of Briony's Inshore painting (herring)
- Use SD inpainting to extend the edges outward
- Each step zooms out slightly and the new content shifts toward the next scene
- After 30+ steps, the herring scene has gradually been replaced by the bird/sky scene
- Unique "infinite reveal" effect

---

## Experiment Priority Summary

| Priority | Node 1 | Node 2 | Node 3 |
|----------|--------|--------|--------|
| 1st | Wan I2V from paintings | VTG/CHIMERA morphing | Boids + ControlNet |
| 2nd | Explicit intermediate prompts | Wan VAE manifold interpolation | Boids + painting compositing |
| 3rd | Photo→watercolor metamorphosis | ControlNet depth morphing | SVD animate Briony's stills |
| 4th | Ecological cascade (long form) | SD 1.5 prompt walk | AnimateDiff + prompt travel |
| 5th | Deforum-style zoom | FlowEdit V2V | DynamiCrafter |
| 6th | — | Train Wan LoRA | Depth morph / outpainting |

---

## Prompt to Resume This Work

Give the next Claude session this prompt:
```
Read /Users/darrenzal/projects/salish-sea-dreaming/docs/video-generation-status.md and /Users/darrenzal/projects/salish-sea-dreaming/docs/overnight-gpu-plan.md — these document our video generation experiments and the overnight plan. Execute the experiment queues across 3 TELUS H200 notebooks (each has its own GPU with 143GB VRAM and 1.8TB RAM). The goal is true metamorphosis animation (herring→birds, salmon→forest) in Briony Penn's watercolor style. See also the deep research report at ~/Downloads/Artistic Video Metamorphosis Techniques.md. Start all 3 nodes in parallel, running experiments in priority order. Save all outputs to /home/jovyan/output/ on each node with descriptive names.
```
