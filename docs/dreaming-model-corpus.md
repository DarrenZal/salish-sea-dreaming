# The Dreaming Model — Corpus Design & Ecological Interface Atlas

*Salish Sea Dreaming — March 2026*

---

## Vision

A single StyleGAN model where navigating the latent space IS navigating the ecosystem. Herring morph into salmon, anemones bloom into starfish, octopus dissolve into kelp. "Each creature contains the whole."

StyleGAN organizes latent space by **visual similarity**, not taxonomy. If the training data includes visually similar images across species, the model creates smooth paths between them — the food web made navigable. The transitions between species become the installation's vocabulary.

## The Ecological Interface Insight

Don't curate the corpus by species taxonomy or even by visual grammar alone. Curate by **ecological interfaces** — the transitions between habitats where species meet, where the food web becomes visible.

### Countershading as a Latent Bridge

Fish and birds both evolved **dark backs and light bellies** (countershading) for the same reason — camouflage from predators above and below. If the corpus includes:
- Fish seen from above (dark back against dark water)
- Birds seen from above (dark back against dark water)

...StyleGAN places them near each other in latent space. The model **discovers convergent evolution** through visual statistics. A latent walk between these two regions reveals the shared adaptation.

Similarly:
- Fish seen from below (light belly against light surface)
- Birds seen from below (light belly against light sky)
- Whales seen from below (light belly)

These form another cluster. The countershading bridge connects fish, birds, and whales through a shared visual pattern that exists because of a shared ecological pressure.

### The Food Web as Latent Space Topology

```
Bear on land → bear in water → bear with salmon → salmon in water
  → bird diving for fish → bird on water surface
    → bird from above (dark back = camo against water)
      → fish from above (dark back = camo against water)
        = COUNTERSHADING BRIDGE
          → fish from below (light belly = camo against sky)
            → bird from below (light belly = camo against sky)
              → whale from below (light belly)
                → whale breaching → back to water...
```

Each step is visually similar enough for StyleGAN to interpolate smoothly. But ecologically, navigating this path traces the food web and the shared adaptations across species.

## Corpus Strategy: v1 (April) and v2 (Post-April)

### v1 — Water-Dominant (April 2026)

Keep the model in one strong visual grammar: **underwater and intertidal**. One domain that converges well in StyleGAN.

| Source | Species | Images | Status |
|--------|---------|--------|--------|
| Fish corpus | Herring, salmon (5 sp), anchovy, sand lance, eulachon, lingcod, cabezon, rockfish | 378 | CC-safe, QC'd |
| Intertidal invertebrates | Octopus, starfish (2 sp), sea urchin (2 sp), anemone (2 sp), nudibranch, jellyfish, crab (2 sp), chiton, plumose anemone | ~677 | Scraping, needs QC |
| Eelgrass | Eelgrass (Zostera marina) | ~50 | To scrape |
| Underwater whale/orca | Orca, humpback — **underwater shots only** | ~50-100 | QC from existing 731 whale images |
| Underwater seal | Harbor seal — **underwater only** | ~30-50 | To scrape |
| Bull kelp | Already in intertidal scrape | Included | — |

**v1 target:** 600-900 images, water-dominant, all CC-safe.
**Excluded from v1:** Birds, bears, sky-dominant, land-dominant, surface-split. These fracture the visual grammar.

### v2 — Full Ecological Interface (Post-April, target MOVE37XR Oct 2026)

Expand into surface, aerial, and terrestrial interfaces. Each addition should be tested for latent space coherence before committing.

**Additional species for v2:**
- Bald Eagle (diving, soaring, perched near water)
- Great Blue Heron (wading, striking at fish)
- Black Bear (in stream with salmon)
- Salmon (jumping — water→air interface)
- Harbor Seal (hauled out — water→land interface)
- Otter (swimming + on rocks)

**Countershading pairs (v2 priority):**
- Fish from above + bird from above (dark dorsal against dark water)
- Fish from below + bird from below (light ventral against light sky/surface)
- Whale from below (light belly — the massive version of the same adaptation)

## Transition Atlas Tags

A tagging system for QC, prompt design, Resolume sequencing, and v2 corpus curation:

| Tag | Description | Example images |
|-----|-------------|----------------|
| `underwater` | Organism fully submerged | Fish, octopus, anemone, kelp, underwater whale |
| `intertidal` | Tidepool, exposed at low tide | Starfish, urchin, chiton, anemone |
| `surface-split` | Above/below waterline visible | Whale breaching, salmon jumping, bird landing |
| `wading` | Organism in shallow water, legs visible | Heron, bear in stream, shorebird |
| `aerial-above-water` | Flying/swimming seen from above | Eagle soaring (dark back), fish school from above |
| `aerial-below-sky` | Flying/swimming seen from below | Bird from below (light belly), fish from below |
| `terrestrial-near-water` | On land, water nearby | Bear on riverbank, eagle perched above stream |
| `predation` | Predation moment | Bear with salmon, eagle striking, bird diving |
| `countershading` | Top-down or bottom-up view showing dark dorsal / light ventral | Any species showing the camo adaptation |
| `eelgrass-meadow` | Underwater meadow habitat | Eelgrass beds with fish, invertebrates |

**These tags serve multiple purposes:**
1. **GAN corpus QC** — which images to include in v1 vs v2
2. **Briony prompt vocabulary** — what to render for the narrative wall (txt2img and img2img)
3. **Resolume sequencing** — which visual layers appear when
4. **Data witness cues** — when ecological data surfaces as evidence

## QC Criteria

### For v1 (water-dominant)
- **Include:** Underwater, intertidal, eelgrass meadow images
- **Include:** Organism fills most of the frame (organism-dominant composition)
- **Include:** Natural ambient lighting (no flash blowout, no studio lighting)
- **Include:** Clear organism silhouette against background
- **Reject:** Surface/sky visible, horizon line, aerial shots
- **Reject:** Human handling, dead/beached organisms, captive animals
- **Reject:** Subject small or ambiguous in frame
- **Reject:** Extreme close-ups with no ecological context

### For v2 (full interface, post-April)
- Apply v1 criteria PLUS:
- **Include:** Ecological interface images (predation, wading, diving, breaching)
- **Include:** Countershading pairs (top-down and bottom-up views)
- **Balance:** No single interface type should dominate. Cap at ~100 images per tag.
- **Bridge discipline:** Only include surface/aerial/terrestrial images that visually bridge to the water-dominant core.

## Composition as Transition Dimension

### Multi-Subject Images Create Richer Latent Space

A single image of "salmon chasing herring through eelgrass" gives StyleGAN three latent directions to organize around simultaneously:
- Salmon body form
- Herring school pattern
- Eelgrass habitat texture

That image sits at the **intersection** of those three dimensions in latent space. Navigate one direction and the salmon becomes more prominent. Navigate another and the eelgrass takes over. Navigate a third and the herring scatter. The more multi-subject compositions in the corpus, the richer the latent topology — more paths to navigate, more ecological relationships encoded.

StyleGAN doesn't see "salmon" and "herring" as labeled concepts. It sees visual features at different spatial positions. A training image with multiple organisms teaches the model that those features **co-occur** — they belong in the same region of latent space. This is how ecological relationships become navigable without any labels or text.

### Three Image Types for a Balanced Corpus

| Image type | What it teaches the model | Example | Corpus share |
|-----------|--------------------------|---------|-------------|
| **Single organism, dominant** | Clear species morphology, silhouette, texture | Octopus filling the frame | ~60-70% |
| **Multi-subject, ecological** | Co-occurrence, predation, relationship, transition paths | Salmon among herring in eelgrass bed | ~20-30% |
| **Habitat-rich** | Environmental context, visual grammar bridges, depth | Kelp forest with multiple species at different depths | ~10-15% |

**Prefer images with ecological context over isolated organisms:**
- Salmon chasing herring > lone salmon on gravel
- Anemone with hermit crab or small fish > anemone alone
- Kelp forest with fish swimming through > kelp frond closeup
- Octopus in its den surrounded by shells and urchins > octopus on blank substrate
- Seal swimming among fish > seal portrait

**But keep organism-dominant images as the majority** — the model needs clear morphological signal to learn species forms. Multi-subject images provide the transition paths between those forms. Both are needed.

### QC Implication

During QC, **tag composition type** alongside the ecological interface tags:
- `single-dominant` — one organism fills frame
- `multi-subject` — two or more species visible in ecological relationship
- `habitat-scene` — habitat structure (kelp, eelgrass, reef) with organisms present

Don't reject a strong multi-subject ecological scene just because no single organism dominates. These are the images that make the latent space navigable — the connective tissue between species clusters.

---

## How Steering Works

### In the GAN (Autolume) — no text, no labels
StyleGAN discovers structure from visual statistics. You steer by:
- **Latent vector navigation** — sliders/OSC move through the 512-dimensional space
- **Seed interpolation** — smooth morphing between two outputs
- **Truncation PSI** — controls "normal" (0.5) vs "wild" (1.5) output
- **Network Bending** — MIDI faders for semantic directions (Autolume feature)

Post-training, Arshia identifies clusters (fish region, anemone region, octopus region) and maps navigation paths. The training data determines WHERE things are in latent space. Curation = latent space topology.

### In SD 1.5 + Briony LoRA — text prompts steer
For the Briony narrative wall:
- **txt2img:** Prompts directly describe the scene — the transition atlas tags become prompt vocabulary
- **img2img:** Input images (photos, GAN frames, Moonfish footage) guide composition; LoRA applies Briony's aesthetic

The narrative transition chain (bear → salmon → bird → countershading) becomes a **sequence of authored prompts**, each rendered at 30 steps, composited in Resolume with dissolves and rhythm.

## Files

| File | Purpose |
|------|---------|
| `tools/species-fish.tsv` | 13 fish species with taxon IDs |
| `tools/species-intertidal.tsv` | 14 intertidal invertebrate species with taxon IDs |
| `tools/species-whales.tsv` | 6 cetacean species (QC for underwater-only for v1) |
| `training-data/provenance.csv` | License + source tracking for all scraped images |
| `tools/scrape_inaturalist_guide.py` | Scraper with `--license-filter`, `--corpus`, `--species-list` |
| `tools/qc_approve.py` | Batch approve/reject with `--corpus`, `--rejects-file` |
| `scripts/prep_training_data.py` | Resize + center-crop to 512x512 training format |
