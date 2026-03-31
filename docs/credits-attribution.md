# Salish Sea Dreaming — Credits & Attribution

**Date:** 2026-03-31
**Exhibition:** "Digital Ecologies: Bridging Nature and Technology" — Mahon Hall, Salt Spring Island, April 10-26, 2026

## License Policy

**COMMERCIAL USE** — exhibition with artist fee = commercial under CC terms.
Only CC0, CC BY, and CC BY-SA materials used in training and exhibition outputs.
CC BY-NC and CC BY-NC-ND are excluded from all corpora.

---

## Visual Art — Style Transfer

| Source | Materials | License | Credit |
|--------|-----------|---------|--------|
| **Briony Penn** | 54 watercolor paintings (cropped to 512x512 training images) | Artist permission | Briony Penn, naturalist and illustrator |
| | LoRA v1 trained on 22 selected works, rank 16, 1000 steps | | Style: "in the style of Briony Penn's ecological watercolors" |

**Note:** Briony must be materially present in exhibition credits. Full artist bio required.

## Underwater Cinematography

| Source | Materials | License | Credit |
|--------|-----------|---------|--------|
| **Moonfish Media** (Deirdre Leowinata) | 13 video files (6 underwater, 6 drone, 1 longform), 4.7 GB | Collaborator permission | Moonfish Media — underwater cinematography |
| | 8 hero segments selected, 3 subclips trimmed for style transfer | | |
| | 416 underwater frames extracted for GAN training corpus | | |

**Status:** Shared via Dropbox by Prav (March 26). Deirdre offered to send RAW files for selected segments.
**Action needed:** Confirm written permission for commercial exhibition use.

## Photography

| Source | Materials | License | Credit |
|--------|-----------|---------|--------|
| **David Denning** | 47 images from "Victoria Natural History" / "Secret Sea" PPT (2016), 14 high-res | Collaborator permission | David Denning — photographer |
| | Macro marine: moon snails, sea stars, tidepools, nudibranchs, sunflower star | | |

**Status:** Shared via Google Drive by Prav (March 26).
**Action needed:** Confirm written permission for commercial exhibition use.

## Training Corpus — Marine Photography (1,254 images, 50 species)

| Source | Count | License | Credit |
|--------|-------|---------|--------|
| **iNaturalist** (Guide 19640 + targeted scrapes) | ~900 images | CC0, CC BY, CC BY-SA only | Individual photographers credited in `training-data/provenance.csv` |
| **Openverse** | ~220 images | CC0, CC BY, CC BY-SA only | Individual photographers credited in provenance.csv |
| **Briony Penn archive** | 54 images | Artist permission | Briony Penn |
| **Moonfish Media frames** | ~80 images | Collaborator permission | Moonfish Media |

All images license-filtered at scrape time. Per-image provenance tracked in `training-data/provenance.csv`.

## GAN Models

| Model | Training Data | Status | License |
|-------|--------------|--------|---------|
| Fish model (kimg 1000) | 353 CC-safe fish images | Complete — fallback only | Clean (CC0/BY/BY-SA corpus) |
| Dreaming model | ~1,254 images, 50 species | Not yet trained | Clean (all sources above) |
| Base model (kimg 320) | Mixed sources incl. license-tainted | R&D only | NOT for exhibition |

## Software & Models

| Component | Source | License |
|-----------|--------|---------|
| Stable Diffusion 1.5 | RunwayML | CreativeML Open RAIL-M |
| StreamDiffusion | kumahiyo/StreamDiffusion | Apache 2.0 |
| StreamDiffusionTD TOX (v0.3.0) | Leo (via Prav session) | TBD — confirm with Leo |
| TouchDesigner 2025 | Derivative | Commercial license |
| Resolume Arena | Resolume | Commercial license |
| StyleGAN2-ada (Autolume) | SFU MetaCreation Lab | Research — confirm for exhibition |
| ComfyUI | comfyanonymous | GPL 3.0 |

## Sound / Music

| Source | Materials | License | Credit |
|--------|-----------|---------|--------|
| **Eve Marenghi** | Ecological data MIDI + Manifest CSV | Collaborator contribution | Eve Marenghi — data scientist |
| **Ableton Live + Max for Live** | Biosonification engine | Commercial license | |

## Data Sources (OSC Engine)

| Channel | Source | License |
|---------|--------|---------|
| Tides | Fisheries and Oceans Canada | Open Government Licence - Canada |
| Moon phase | Public domain astronomical data | Public domain |
| Fraser River discharge | Environment Canada Water Office | Open Government Licence - Canada |
| Herring spawn | DFO Pacific Herring Data | Open Government Licence - Canada |

## Pending Confirmations

- [ ] **Moonfish Media** — written permission for commercial exhibition use (check with Prav for email/Signal confirmation from Deirdre)
- [ ] **David Denning** — written permission for commercial exhibition use
- [ ] **StreamDiffusionTD TOX** — confirm licensing terms from Leo
- [ ] **Autolume** — confirm MetaCreation Lab licensing for exhibition use
- [ ] **iNaturalist individual credits** — generate CC BY attribution list from provenance.csv for exhibition label

## Exhibition Credit Format (Draft)

```
SALISH SEA DREAMING
An immersive digital ecology

Pravin Pillay — Creative Director, systems architecture
Carol Anne Hilton — Framework, relational value
Briony Penn — Ecological watercolors
Darren Zal — Technical infrastructure, knowledge systems
Shawn Anderson — Creative technology, GPU systems
Eve Marenghi — Ecological data

Underwater cinematography: Moonfish Media (Deirdre Leowinata)
Photography: David Denning
Marine observations: iNaturalist community (CC BY)
Ecological data: Fisheries and Oceans Canada, Environment Canada

Curated by Raf
Digital Ecologies: Bridging Nature and Technology
Mahon Hall, Salt Spring Island
```
