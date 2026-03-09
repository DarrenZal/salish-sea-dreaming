# AutoLoom/StyleGAN2-ada Training Datasets

Training datasets for The Salish Sea Dreaming installation's generative visual system.

## Strategy

**Primary path:** Train a base model on 500+ curated marine photographs, then fine-tune on 40-70 Briony Penn marine watercolors. Fine-tuning renders marine life through Briony's palette and sensibility — "Briony-informed ecological dreaming," not exact imitation.

**Resolution:** Pilot at 512x512. Only proceed to 1024 if David Denning corpus and TELUS GPU access are both confirmed.

## Corpora

### `marine-photo-base/`
500+ manually curated coastal/marine photographs at 512x512 (or 1024x1024).

**Sources:** David Denning photography (primary), iNaturalist research-grade observations, NOAA photo library, Ocean Networks Canada, Wikimedia Commons (CC-licensed).

**Curation criteria — reject:** text overlays, watermarks, UI chrome, borders, off-bioregion species (tropical fish), poor lighting, motion blur, low resolution, heavily processed photos.

**Prioritize:** Herring schools, salmon species, orca pods, kelp forests, eelgrass meadows, tide pools, spawn events, bioluminescence, invertebrates, seabirds on water.

### `briony-marine-colour/`
40-70 clean marine watercolor images at 512x512, curated from Briony Penn's archive.

**Includes:** Marine paintings (panoramas, ecosystem cross-sections, octopus, basking shark), Central Coast illustrations, text-free detail crops from watercolour mandalas, marine/coastal field journal subjects.

**Excludes:** Pen-and-ink (separate corpus), illustrated maps (text-heavy), signage/murals, text-heavy mandalas, images dominated by labels.

### `briony-linework/`
Reserved for future pen-and-ink corpus. Not mixed into the colour model.

## Provenance Tracking

**`provenance.csv`** is the single source of truth for approval and export. Every image — original or derivative — must have a row.

| Column | Required | Description |
|--------|----------|-------------|
| `filename` | yes | Output path relative to `training-data/` |
| `source_file` | yes | Path to original source asset (relative to repo root) |
| `source` | yes | Origin (e.g., "David Denning", "iNaturalist", "Briony Penn archive") |
| `url` | if applicable | Source URL |
| `license` | yes | CC-BY, CC0, public domain, "artist permission", etc. |
| `photographer_artist` | yes | Creator name |
| `parent_source_file` | crops only | Original this was cropped from |
| `crop_box` | crops only | Pixel coordinates `x,y,w,h` |
| `crop_recipe` | crops only | Recipe used (e.g., "horizontal-thirds-top") |
| `approved_for_training` | yes | yes/no/pending |

**Hard gate:** Only rows with `approved_for_training=yes` are exported into training sets.

## Crop Workflow

1. `scripts/crop_candidates.py` generates candidate crops + contact sheets
2. Human marks keep/reject in `review/keep.csv`
3. `--promote` copies approved crops into `provenance.csv` with full metadata

## Augmentation

**Do NOT apply manual augmentation.** StyleGAN2-ada's Adaptive Discriminator Augmentation handles this internally during training. Adding manual flips/rotations creates near-duplicates that waste the training budget.

## Training Notes for Arshia

- StyleGAN2 configuration required for AutoLoom compatibility
- Train with StyleGAN3 codebase, StyleGAN2 config
- Minimum 500 distinct images for base training
- Fine-tuning on ~50 images works well (demonstrated with 50 clown faces)
- Save multiple fine-tune checkpoints → range from photographic to painterly
- TELUS H200 GPUs for training; local RTX for inference

## Verification Checklist

- [ ] Parser fix validated: spot-check 10 species common↔scientific alignment
- [ ] Visual QC: 50 random items per corpus — reject text, borders, watermarks
- [ ] No single Briony source contributes >6 crops
- [ ] `briony-marine-colour/`: 40-70 clean images, all marine/ecological
- [ ] `marine-photo-base/`: 500+ images, manually curated
- [ ] `provenance.csv` complete for every training image
- [ ] Pilot 512px training validates quality
- [ ] `dream_briony.py` pipeline still functional as fallback
