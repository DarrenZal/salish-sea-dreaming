# Feb 13 Visual Sprint - The Salish Sea Dreaming

> Briony paints the Salish Sea awake. We show it dreaming.

**Deadline:** February 13, 2026
**Deliverables:**
1. **Static visuals** - A curated set for Raf to consider for exhibition poster and public engagement (IG/FB)
2. **Short video material** - Loops and atmospheric motion studies for M37/Raf to post to Instagram

**Key constraint (from Raf):** "It would be great if the output looks distinct enough from Briony's artwork so that it's not confusing."

**Guiding principle (from Prav):** "We want to hold with integrity the care and attention and dare I say it 'love' of the artists providing the content so that this is transmitted through the aesthetic contemplative experience to the audience."

**Feb 11 priority task update:** See `docs/20260211-priority-task-salish-sea-dreaming-humans.md` for the current still-image focus for Raf.

---

## Source Material

### Briony Penn's Watercolors (in Signal exports)

Location: `/Users/darrenzal/signal-chats-salish-sea/M37SalishSeaDreaming/media/`

| File | Subject | Five Threads |
|------|---------|-------------|
| `IMG_1473.jpg` | Panoramic mural - tidal zone with octopus, kelp, boats, "SLOW" sign | T'lep, Herring |
| `IMG_1474.jpg` | Giant Pacific octopus close-up (T'lep) - vivid red, tentacles, alive | T'lep |
| `IMG_1475.jpg` | Kelp forest with divers, herring eggs on eelgrass, crabs | Herring, Kelp |
| `IMG_1476.jpg` | Herring spawn panorama - whales, seabirds, fishing boats, sea lions | Herring, Orca |
| `IMG_1477.jpg` | Eelgrass meadow - oystercatchers, sea stars, crabs, fish, islands | Herring |
| `IMG_1478.jpg` | Kelp forest underwater - bold blues/teals, rockfish, sea stars, waves | Kelp |
| `IMG_1479.jpg` | Salmon stream cross-section - bears, old growth, spawning salmon | Salmon, Cedar |
| `IMG_1483.jpg` | Ink drawing - tree with roots mirroring canopy (wide angle, context) | Cedar |
| `IMG_1484.jpg` | Same ink tree drawing - close crop, fine detail of root/branch network | Cedar |
| `IMG_1485.jpg` | Seasonal nature wheel - leaves, feathers, fungi, insects, seeds in mandala | Camas |
| `IMG_1486.jpg` | Seasonal flower wheel - botanical with species names (camas, shooting star) | Camas |
| `IMG_1488.jpg` | Close-up flower wheel - duskywing butterfly, serviceberry, larkspur detail | Camas |
| `signal-2026-02-08-070332.jpeg` | Herring/lingcod underwater with oystercatcher on shore (Briony's Feb 8) | Herring |

### Other Visual Assets
- **Moonfish Media** (David Denning & Deidre): Underwater herring footage - https://www.moonfishmedia.ca/
- **David Denning**: Marine photography, 17 years on Salt Spring
- **Shared Google Drive**: https://drive.google.com/drive/folders/1eWuiMKqALHh8SWBjMRRCMu5wrGoK8oEO
- **Mind Map**: https://coggle.it/diagram/aW01lIKXUtVgH4cW/t/wen%2Cn%C3%A1%2Cnec

### Existing Code
- **Web prototype** (Three.js particles): https://darrenzal.github.io/salish-sea-dreaming/
- **Mycelium network** (TD script): `scripts/mycelium.py` - bioluminescent pulsing veins
- **Psychedelic video** (TD script): `scripts/psychedelic_video.py` - real-time video transformation

---

## Creative Direction

### The Approach: img2img - Make Her Drawings Dream

**Discovered Feb 9:** The strongest approach is NOT generating abstract AI art inspired by Briony's subjects. Instead, we take Briony's actual watercolors and transform them into "dreaming" states using OpenAI's `gpt-image-1` model (image editing mode).

The drawings are the **foundational visual layer**. We don't replace them. We make them breathe, glow, partially dissolve - as if seen through moving water.

| Briony's Paintings | Our Dreaming Transformations |
|-------------------|------------------------------|
| Daytime consciousness | Dreaming state |
| Specific, illustrative, detailed | Same composition, now breathing with light |
| Earthy watercolor palette | Original palette + subtle bioluminescent glow |
| Hand-drawn line quality | Lines preserved but edges softening |
| Above and below water | Boundary between worlds becoming permeable |

### Briony's Basking Shark Metaphor

From conversation Feb 9 - Briony identified as the **oystercatcher** (can see above and below, but limited by its perspective). Her basking shark insight: **nested realities**.

> The plankton inside the basking shark experience it as their whole reality. The oystercatcher on the surface cannot see what's below. Each creature inhabits a different layer of the same world.

This inspired the "nested-reality" dream direction: drawings that reveal hidden layers, transparency between worlds, forms containing ecosystems.

### Dream Directions (5 styles)

| Direction | Style | Intensity |
|-----------|-------|-----------|
| **bioluminescent** | Soft glow, breathing edges, inner luminosity | Low (proven) |
| **submerged** | Seen through moving water, ripple distortion, blue-green shift | Low-medium |
| **nested-reality** | Hidden layers within layers, worlds within worlds (basking shark metaphor) | Medium |
| **night-ocean** | Dark palette, bioluminescent outlines, phosphorescent trails | Medium |
| **dissolving** | Forms breaking into particles of light, releasing shapes back to the sea | High |

### Color Palette (extracted from Briony's work)

- **Deep ocean:** `#0A1F33` `#1A3A4A` `#2B5566` - dark blues and teals
- **Bioluminescence:** `#33CCAA` `#66FFCC` `#99EEDD` - cyan/green glow
- **Kelp gold:** `#B8A030` `#D4C050` `#8B7A20` - golden browns
- **Salmon/octopus:** `#CC4433` `#E87060` `#FF9988` - warm reds and pinks
- **Spawn white:** `#E8E4D8` `#F0ECE0` - milky, pearlescent
- **Forest:** `#2A4A2A` `#3B6B3B` `#557755` - deep greens

---

## Production Pipeline

### Primary: img2img Dream Transformations (ACTIVE)

**Tool:** OpenAI `gpt-image-1` (image editing API)
**Script:** `scripts/dream_briony.py`
**Cost:** ~$0.12 per image

Takes Briony's watercolors as input and transforms them with guided prompts that preserve the watercolor DNA while adding dreamlike qualities. Five dream directions available (see above).

```bash
# Single image
python3.11 scripts/dream_briony.py --images octopus --direction bioluminescent

# By Five Threads
python3.11 scripts/dream_briony.py --thread salmon --direction night-ocean

# All images, all directions (~$8 total)
python3.11 scripts/dream_briony.py --all --all-directions

# Preview without generating
python3.11 scripts/dream_briony.py --dry-run --all
```

**Output:** `assets/output/experiments/{direction}/{timestamp}_{image-key}.png` (1536x1024)

### Proof Sheets (review tool)

**Script:** `scripts/proof_sheet.py`

```bash
python3.11 scripts/proof_sheet.py --best-of         # Most recent per image, all directions
python3.11 scripts/proof_sheet.py --direction bioluminescent  # One direction
python3.11 scripts/proof_sheet.py --compare octopus  # One image across all directions
python3.11 scripts/proof_sheet.py --all              # Everything
```

**Output:** `assets/output/proof-sheets/`

### Video Loops (Instagram material)

**Script:** `scripts/create_loops.py`
**Requires:** FFmpeg, Pillow

```bash
# Ken Burns (slow zoom/pan) from single image
python3.11 scripts/create_loops.py --mode kenburns --input path/to/image.png --format square

# Crossfade between dream versions of same source
python3.11 scripts/create_loops.py --mode crossfade --image-key octopus --format all

# Five Threads montage
python3.11 scripts/create_loops.py --mode montage --format story
```

**Formats:** square (1:1), portrait (4:5), story (9:16), landscape (16:9)
**Output:** `assets/output/video-loops/`

### Secondary Paths (for later / exhibition)

- **Web prototype** (Three.js particles): https://darrenzal.github.io/salish-sea-dreaming/ - for interactive exhibition
- **TouchDesigner scripts** (`scripts/mycelium.py`, `scripts/psychedelic_video.py`) - for live performance
- **StreamDiffusion TOX** - for real-time Kinect-driven transformations (exhibition north star)
- **Text-to-image** (`scripts/generate_visuals.py`) - produces more abstract results, useful for backgrounds

---

## Task Tracker

### Setup (completed Feb 9)

| # | Task | Status | Notes |
|---|------|--------|-------|
| X1 | Set up assets directory | [x] | `assets/reference/briony-watercolors/` (13 images), `assets/output/` |
| X2 | Build dream transformation pipeline | [x] | `scripts/dream_briony.py` - gpt-image-1 img2img |
| X3 | Build proof sheet generator | [x] | `scripts/proof_sheet.py` - Pillow contact sheets |
| X4 | Build video loop creator | [x] | `scripts/create_loops.py` - FFmpeg loops |
| X5 | Generate first 3 dream transformations | [x] | kelp, octopus, herring - bioluminescent direction |
| X6 | Generate first 3 text-to-image experiments | [x] | `scripts/generate_visuals.py` - DALL-E 3 |

### Deliverable 1: Static Visuals (poster / social media)

| # | Task | Status | Notes |
|---|------|--------|-------|
| S1 | Bioluminescent batch - all Five Threads coverage | [ ] | 6 new images (salmon, cedar, camas, eelgrass, tidal, herring-latest) |
| S2 | Nested-reality batch - 4 key compositions | [ ] | octopus, herring-panorama, ink-tree-wide, eelgrass |
| S3 | Night-ocean batch - 4 key compositions | [ ] | Same 4 as nested-reality |
| S4 | Dissolving batch - 2-3 images | [ ] | kelp-underwater, salmon-stream |
| S5 | Generate proof sheets for review | [ ] | One per direction + best-of comparison |
| S6 | Curate best 6-10 stills for Prav/Natalia | [ ] | Select strongest per thread |
| S7 | Prepare final high-res files for Raf | [ ] | Format TBD |

### Deliverable 2: Short Video / Motion Material (Instagram)

| # | Task | Status | Notes |
|---|------|--------|-------|
| V1 | Ken Burns loops from strongest stills | [ ] | 8-12s, all 3 IG formats |
| V2 | Crossfade loops - dream versions of same source | [ ] | octopus, herring, kelp |
| V3 | Five Threads montage | [ ] | 30-60s crossfade across threads |
| V4 | Format all videos (1:1, 4:5, 9:16) | [ ] | Instagram-ready MP4s |

### Open

| # | Task | Status | Notes |
|---|------|--------|-------|
| O1 | Get higher-res scans of Briony's watercolors | [ ] | Signal photos are phone quality |
| O2 | Share early experiments with Prav for feedback | [ ] | Before full batch generation |
| O3 | Check if Shawn has tools/access | [ ] | |
| O4 | What aspect ratio / resolution for poster? | [ ] | Ask Raf |

---

## Timeline

### Day 1 (Feb 9): Pipeline Built + First Results ✓
- [x] Set up assets directory, copied 13 reference watercolors
- [x] Built `dream_briony.py` with 13-image catalog, 5 dream directions, CLI
- [x] Generated 3 bioluminescent dream transformations (kelp, octopus, herring)
- [x] Generated 3 text-to-image experiments (DALL-E 3)
- [x] Built `proof_sheet.py` for visual review
- [x] Built `create_loops.py` for Instagram video loops
- [x] Tested Ken Burns video loop generation

### Day 2 (Feb 10): Batch Generation
- [ ] Run bioluminescent direction on 6 priority images (Five Threads coverage)
- [ ] Run nested-reality + night-ocean on 4 strongest compositions
- [ ] Run dissolving on 2-3 high-intensity candidates
- [ ] Generate proof sheets for each direction
- [ ] Share proof sheets with Prav for feedback

### Day 3 (Feb 11-12): Video + Refinement
- [ ] Generate Ken Burns loops from strongest stills (all 3 IG formats)
- [ ] Generate crossfade loops for octopus, herring, kelp
- [ ] Generate Five Threads montage
- [ ] Re-generate any images that need prompt refinement
- [ ] Curate best 6-10 stills

### Day 4 (Feb 12-13): Package & Deliver
- [ ] Final selection for Raf (stills + video)
- [ ] Format everything for intended use
- [ ] Document results and process for team

---

## Available Tools (Confirmed)

### Primary Pipeline (working)
- **OpenAI API** - `gpt-image-1` for img2img, DALL-E 3 for text-to-image
- **Python 3.11** - Pillow 10.4.0, OpenAI SDK
- **FFmpeg 7.1.1** - Video loop creation, format conversion
- **Scripts:** `dream_briony.py`, `proof_sheet.py`, `create_loops.py`, `generate_visuals.py`

### Local
- **TouchDesigner** - Installed with MCP integration
- **Three.js / WebGL** - Existing web prototype
- **Hardware:** Apple M2, 24GB RAM (memory-constrained, avoid local ML/diffusion)

### Cloud
- **OpenAI API** - gpt-image-1 (~$0.12/image), DALL-E 3
- **ChatGPT Plus** - Interactive image generation
- **Google Gemini** - Imagen 3 access

## Results (Feb 9)

### Generated Images
**Location:** `assets/output/experiments/`

| File | Source | Direction | Notes |
|------|--------|-----------|-------|
| `20260209-192207_dream-kelp-breathing.png` | kelp-underwater | bioluminescent | 1536x1024, maintains watercolor quality |
| `20260209-192316_dream-octopus-dreaming.png` | octopus | bioluminescent | T'lep with inner glow |
| `20260209-192413_dream-herring-emergence.png` | herring-panorama | bioluminescent | Panorama with luminous spawn |
| `20260209-182428_herring-spawn-dream.png` | (text-to-image) | DALL-E 3 | Abstract, no source watercolor |
| `20260209-182455_tlep-octopus-intelligence.png` | (text-to-image) | DALL-E 3 | Abstract neural octopus |
| `20260209-182534_kelp-forest-cathedral.png` | (text-to-image) | DALL-E 3 | Abstract kelp cathedral |

### Video Loops
**Location:** `assets/output/video-loops/`

| File | Mode | Format | Duration |
|------|------|--------|----------|
| `20260209-194310_kenburns_dream-kelp-breathing_square.mp4` | Ken Burns | 1:1 | 8s |

### Proof Sheets
**Location:** `assets/output/proof-sheets/`

---

## Open Questions

- [x] What image generation tools does Darren have access to right now? → OpenAI API (gpt-image-1, DALL-E 3)
- [x] Is TouchDesigner installed locally? → Yes, with MCP integration
- [x] Best approach for Feb 13 visuals? → img2img transformation of Briony's watercolors (not text-to-image)
- [ ] Is Shawn available and what tools does he bring?
- [ ] Can we get feedback from Prav/Natalia before Feb 13, or is it blind delivery?
- [ ] What aspect ratio / resolution does Raf need for the poster?
- [ ] Does M37 have an Instagram account already? What's the visual brand?

---

## Inspiration & References

### Artists working in similar territory
- **Refik Anadol** - Large-scale data sculptures, ocean datasets: https://refikanadol.com/
- **teamLab** - Immersive digital nature: https://www.teamlab.art/
- **Random International** - Rain Room, presence-responsive: https://www.random-international.com/
- **Marshmallow Laser Feast** - VR nature experiences: https://www.marshmallowlaserfeast.com/
- **Semiconductor** - Art from scientific data: https://semiconductorfilms.com/

### Generative art in nature/ocean space
- **Coral morphologic** - Fluorescence underwater: https://www.coralmorphologic.com/
- **Andy Lomas** - Morphogenetic creations: https://andylomas.com/
- **Nervous System** - Nature-inspired generative design: https://n-e-r-v-o-u-s.com/

### Technical references
- StreamDiffusion paper: https://arxiv.org/abs/2312.12491
- DotSimulate TD integration: https://github.com/dotsimulate/StreamDiffusionTD
- Real-time style transfer: https://arxiv.org/abs/1603.08155

---

*This is a living document. Update as experiments progress and directions clarify.*
