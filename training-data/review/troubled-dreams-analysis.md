# Troubled Dreams: Rejected Image Analysis

> Analysis of 201 rejected iNaturalist images for potential use in a "troubled dreams"
> StyleGAN model — the Salish Sea's nightmare of human disturbance.

**Context:** The main training corpus (539 images) captures the living Salish Sea — underwater,
natural, undisturbed. These 201 rejects were excluded precisely because they show the
*other* reality: extraction, mortality, scientific objectification, and misidentification.
Prav's concept: train a separate model on these to generate "troubled dream" visuals
that the installation can shift into — the ecosystem's anxiety made visible.

## Category Breakdown

### 1. Human Handling (83 images) — 41.3%

Fish held in hands, on boats, fishing trophies, in containers/buckets/nets, person presenting catch.

| Species | Count | Notes |
|---------|-------|-------|
| Chinook Salmon | 8 | Trophy fishing culture — person holding large fish |
| Chum Salmon | 7 | Held, in containers/bags, person on boat |
| Copper Rockfish | 8 | Held on boats, in buckets — catch-and-release imagery |
| Coho Salmon | 5 | Held, in containers, person in stream |
| Eulachon | 8 | Held in hands/gloved hands, in baskets, with nets |
| Longfin Smelt | 5 | In hands, red gloves, in containers |
| Surf Smelt | 7 | In hands, in containers, held on beach |
| Quillback Rockfish | 5 | Handled, held on boats |
| Pink Salmon | 5 | Person holding, presenting fish |
| Pacific Herring | 4 | Held in hands, in blue bowl |
| Yelloweye Rockfish | 4 | Held on boats, person on boat (trophy) |
| Pacific Sand Lance | 2 | Held in hands |
| Big Skate | 3 | Held on boat, egg cases in hands, measured on boat |
| Bluntnose Sixgill Shark | 1 | Held/mouth open on dock |
| California Sea Cucumber | 1 | Held on boat by person |
| Cabezon | 2 | Fishing trophy, fish in bucket |
| Sockeye Salmon | 2 | Person holding, fishing gear/lure visible |
| Dungeness Crab | 1 | Person on beach |
| Lions Mane Jelly | 1 | In orange bucket |
| Sunflower Sea Star | 2 | Tiny specimens held in hand |
| Spiny Dogfish | 3 | Held by person, children on beach |

**Troubled dreams alignment: VERY HIGH.** This is the core of the concept — the extractive
relationship between humans and marine life. Hands gripping fish, trophy poses, the boat deck
as killing floor. A StyleGAN trained on these would learn the visual grammar of extraction:
flesh against skin, fingers wrapped around bodies, the unnatural angle of a fish held aloft.
The salmon species dominate, which is poetically apt — the most culturally contested species
appearing most often as trophies.

---

### 2. Dead/Mortality (30 images) — 14.9%

Dead specimens on docks, beaches, dissected, bloody, skulls/bones, dried specimens, dead piles.

| Species | Count | Notes |
|---------|-------|-------|
| Bluntnose Sixgill Shark | 7 | Dead on beach, dock, ground — bloody, specimens |
| Spiny Dogfish | 5 | Dead on beach, dead specimens |
| Lingcod | 5 | Dead on dock, dissected skull, jaw/skull bones |
| Big Skate | 1 | Dead/dissected specimen |
| Pacific Herring | 2 | Dead on red surface, dead on dock |
| Pink Salmon | 2 | Dead on dock, person holding dead fish |
| Sockeye Salmon | 1 | Dead on red surface |
| Northern Anchovy | 3 | Dead/dried specimens, dead skeleton on rocks |
| Eulachon | 2 | Dead on red plate, dead pile on ground |
| Surf Smelt | 1 | Dead pile on surface |
| Yelloweye Rockfish | 1 | Dead on diamond plate deck |

**Troubled dreams alignment: VERY HIGH.** Death imagery is the nightmare's core vocabulary.
The sixgill sharks dead on beaches — apex predators reduced to carcasses. Lingcod skulls and
jaw bones feel almost archaeological. The recurring "red surface" (cutting boards, plates) adds
a visceral color note. A model trained on these would generate images with the pallor and
stillness of death — bodies on hard surfaces, the wrong colors, the wrong stillness.

---

### 3. Lab/Scientific (27 images) — 13.4%

Rulers, measuring boards, graph paper, lab containers, white dishes, blue trays, measurement overlays.

| Species | Count | Notes |
|---------|-------|-------|
| Longfin Smelt | 10 | Graph paper (x4), rulers (x3), lab equipment, blue surface |
| Surf Smelt | 2 | Ruler/measurement, white dish |
| Spiny Dogfish | 1 | Measurement/ruler |
| Lingcod | 1 | Ruler/measurement |
| Eulachon | 2 | Grid/crate with ruler, white measuring background |
| Cabezon | 1 | Specimen with measurement device |
| Coho Salmon | 2 | Specimens on white surface, fish in container/lab |
| Giant Pacific Octopus | 2 | Lab specimen on spoon/dish, shells/lab specimen |
| Sockeye Salmon | 1 | On display/white surface |
| Surf Smelt | 1 | Lab container |
| Northern Anchovy | 1 | Held/lab (blue tray) |
| Pink Salmon | 1 | Being measured |
| Longfin Smelt | 1 | Held with text label |
| Pacific Herring | 1 | Severely degraded/black image |

**Troubled dreams alignment: MODERATE-HIGH.** Scientific objectification — life reduced to data
points. The graph paper and rulers impose a grid of measurement onto organic forms. Longfin Smelt
dominate this category (10 of 27), suggesting they are the most "studied" species in the dataset —
small fish perpetually measured, counted, assessed. There is something haunting about this:
the bureaucracy of extinction. However, visually these images may be too clinical and flat
to generate compelling dream imagery. Best mixed with other categories rather than used alone.

---

### 4. Wrong Species (37 images) — 18.4%

Eagles, bears, sea lions, seagulls, otters, jellyfish, seals, whales, birds — predators and
bystanders captured instead of target species.

| Misidentified As | Count | Actual Target Species |
|------------------|-------|-----------------------|
| Eagles | 5 | Chinook Salmon, Pink Salmon, Pacific Herring, Giant Pacific Octopus |
| Seagulls/birds (general) | 12 | Ochre Sea Star (x4), Northern Anchovy (x4), Surf Smelt (x2), Chum Salmon, Dungeness Crab |
| Bears | 3 | Pink Salmon, Sockeye Salmon (x2) |
| Sea lions | 3 | Big Skate, California Sea Cucumber, Giant Pacific Octopus |
| Seals | 2 | Dungeness Crab, Giant Pacific Octopus (seal eating octopus) |
| Otters | 2 | Purple Sea Urchin, California Sea Cucumber (otter eating cucumber) |
| Jellyfish | 2 | Dungeness Crab, Giant Pacific Octopus |
| Whales | 1 | Northern Anchovy |
| Sea stars | 1 | Pacific Herring (sea star on glove) |
| Other | 6 | Various — sticks/branches, landscape with species barely visible |

**Troubled dreams alignment: LOW-MODERATE.** These are mostly healthy predator-prey images
(eagles catching salmon, bears fishing, otters eating urchins). They show the food web functioning
rather than disturbed. However, there is a conceptual angle: the Salish Sea's dream of itself
includes all its inhabitants — predators circling, the constant presence of death-from-above.
Eagles and bears could represent natural threat (vs. human threat in categories 1-2).
Not core material but could add texture. The "wrong species" framing itself is interesting —
who decides which species belongs?

---

### 5. Above-Water Landscape (11 images) — 5.5%

Aerial views, landscapes, no species visible, boat views.

| Species Context | Count | Notes |
|-----------------|-------|-------|
| Chum Salmon | 2 | Above-water landscape, no fish visible |
| Coho Salmon | 1 | Above-water landscape |
| Pacific Herring | 2 | Above-water landscape, aerial landscape |
| Eelgrass | 2 | Aerial/boat view, aerial landscape |
| Dungeness Crab | 1 | Above-water landscape (Golden Gate Bridge) |
| Sockeye Salmon | 1 | Above-water landscape |
| Northern Anchovy | 1 | Rocks/landscape, species barely visible |
| Sockeye Salmon | 1 | Above-water landscape |

**Troubled dreams alignment: LOW.** Surfaces without depth — the view from above that cannot
see what is below. Conceptually interesting (the sea seen but not understood) but visually
these are just landscape photos. Unless intentionally blended, they would dilute the model's
ability to generate marine-life-related imagery. Skip for troubled dreams, but could serve
as "transition" frames in the installation.

---

### 6. Watermarks/Text (3 images) — 1.5%

| Species | File | Notes |
|---------|------|-------|
| Dungeness Crab | 361950527 | San Diego Tracking Team watermark |
| Spiny Dogfish | 28048942 | Text/measurement overlay |
| Yelloweye Rockfish | 110978444 | Text watermark |

**Troubled dreams alignment: NONE.** Technical rejects only. Exclude entirely.

---

### 7. Other (10 images) — 5.0%

| Image | Reason | Notes |
|-------|--------|-------|
| Pacific Sand Lance 187803364 | Drawing/sketch, not a photo | Art artifact |
| Pacific Herring 113694575 | Severely degraded/black image | Corrupt file |
| Big Skate 121166690 | Wrong species + watermark (dual reason) | Already counted in wrong species |
| Longfin Smelt 336586034 | In net (sampling) | Borderline lab/handling |
| Coho Salmon 46 | Dead in net | Borderline dead/handling |
| Pacific Sand Lance 344497772 | Dead on net | Borderline dead/handling |
| Lingcod 94 (jaw on driftwood) | Skull/jaw on driftwood | Natural decay vs. human |

*Note: Several "other" items are borderline cases between categories. The true "other" count
is small — about 5 genuinely uncategorizable images.*

**Troubled dreams alignment: MIXED.** The drawing/sketch is interesting as a meta-artifact.
The degraded/black image could actually be powerful — pure darkness, the absence of the visible.

---

## Summary Statistics

| Category | Count | % of Total | Troubled Dreams Fit |
|----------|-------|------------|---------------------|
| Human Handling | 83 | 41.3% | VERY HIGH |
| Wrong Species | 37 | 18.4% | LOW-MODERATE |
| Dead/Mortality | 30 | 14.9% | VERY HIGH |
| Lab/Scientific | 27 | 13.4% | MODERATE-HIGH |
| Above-Water Landscape | 11 | 5.5% | LOW |
| Other | 10 | 5.0% | MIXED |
| Watermarks/Text | 3 | 1.5% | NONE |
| **Total** | **201** | **100%** | |

## Recommendations for "Troubled Dreams" Model

### Tier 1: Core corpus (113 images)
**Human Handling + Dead/Mortality** — these are the nightmare. Hands on bodies, bodies on
docks, the extractive gaze. Together they form a coherent visual language of disturbance.

### Tier 2: Add for texture (27 images)
**Lab/Scientific** — the clinical objectification layer. Graph paper grids, rulers, white
surfaces. Adds a bureaucratic-horror dimension. Mix in at ~20% of corpus.

### Tier 3: Optional (37 images)
**Wrong Species** — predators and bystanders. Could add ecological complexity (the food web's
violence) but may confuse the model's visual coherence. Use selectively — eagles and bears
yes, random bird photos no.

### Exclude (14 images)
**Landscapes, watermarks, corrupt files** — no useful signal for the concept.

### Total usable for troubled dreams: ~140-177 images

This is borderline for StyleGAN training (typically want 500+ for good results), but:
- Combined with data augmentation (flips, crops, color jitter), 140 images could work
- The visual coherence within categories is high (hands + fish is a tight distribution)
- Could supplement with targeted scraping: fishing trophy photos, beach mortality surveys,
  fish market imagery, bycatch documentation
- A smaller model (lower resolution, fewer layers) would need fewer images

### Species Most Represented in "Troubled Dreams"

| Species | Total Rejects | Primary Categories |
|---------|---------------|-------------------|
| Longfin Smelt | 18 | Lab (10), Handling (5), Dead (1) |
| Chinook Salmon | 10 | Handling (8), Wrong species (1), Dead (1) |
| Eulachon | 11 | Handling (8), Lab (2), Dead (2) |
| Spiny Dogfish | 11 | Dead (5), Handling (3), Lab (1), Wrong spp (1) |
| Bluntnose Sixgill Shark | 9 | Dead (7), Handling (1), Dead+people (1) |
| Surf Smelt | 11 | Handling (7), Lab (2), Wrong spp (2), Dead (1) |
| Copper Rockfish | 8 | Handling (8) |
| Chum Salmon | 10 | Handling (7), Landscape (2), Wrong spp (1) |
| Lingcod | 9 | Dead (5), Handling (1), Lab (1), Dead/bones (2) |
| Pink Salmon | 9 | Handling (5), Dead (2), Wrong spp (2) |

**The poetic reading:** Longfin Smelt — the most measured, most objectified. Sixgill Sharks —
the most killed. Copper Rockfish — the most handled. Salmon species — the most displayed as
trophies. Each species has its own mode of suffering in the human gaze.

---

*Analysis generated 2026-03-11 for Prav's "troubled dreams" concept.*
*Source: `/training-data/review/rejects.csv` (201 images rejected from marine-photo-base corpus)*
