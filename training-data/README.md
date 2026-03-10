# AutoLoom/StyleGAN2-ada Training Datasets

Training datasets for The Salish Sea Dreaming installation's generative visual system.

## Strategy

**Primary path:** Train a base model on 500+ curated marine photographs, then fine-tune on Briony Penn marine watercolors. Fine-tuning renders marine life through Briony's palette and sensibility — "Briony-informed ecological dreaming," not exact imitation.

**Resolution:** 512x512 for both corpora. Only proceed to 1024 if David Denning corpus and additional GPU time are both confirmed.

**Status (2026-03-10):** Both corpora built and ready for training. TELUS H200 smoke test completed on Briony corpus — pipeline validated end-to-end.

## Corpora

### `marine-photo-base/`
539 curated underwater/nearshore marine photographs at 512x512.

**v1 scope: underwater/nearshore only.** Fish (single and schools), kelp, eelgrass, octopus, invertebrates, close underwater scenes. These share lighting, color palette, and spatial grammar — "one strong image grammar," not semantic completeness.

**NOT in v1:** Boats, seabirds on open water, horizon-heavy ocean scenes, aerial coastlines, harbor infrastructure. These are visually different domains → separate models later.

**Source:** iNaturalist research-grade observations — 740 images scraped across 37 Salish Sea species at 1024px, then QC-reviewed via species contact sheets. 539 approved (72.8% pass rate), 201 rejected. All CC-BY or CC-BY-NC licensed.

**QC criteria — reject:** wrong species, dead specimens on docks, fish in hands/buckets, lab/dish photos, text overlays, watermarks, rulers/ID tags, severely degraded (extremely blurry, overexposed), above-water landscape where species barely visible.

**QC tools:** `tools/qc_approve.py` (batch approve/reject from reject list), reject list at `review/rejects.csv`, contact sheets at `review/contact-sheets/marine-base/`.

### `briony-marine-colour/`
36 marine watercolor images at 512x512, curated from Briony Penn's archive. This is what the available source material supports — Arshia (MetaCreation Lab) confirmed 36 is sufficient for fine-tuning.

**Includes:** Marine paintings (panoramas, ecosystem cross-sections, octopus, basking shark, kelp forest), Central Coast illustrations (estuary, inshore, offshore scenes), compositional crops (horizontal thirds, panorama zones, center crops).

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
- Minimum 500 distinct images for base training — we have 539
- Fine-tuning on 36 Briony images (demonstrated with 50 clown faces, 36 should work)
- Save multiple fine-tune checkpoints (`--snap=10`) → gradient from photographic to painterly
- TELUS H200 GPUs for training; local RTX for inference

### TELUS Smoke Test (2026-03-09)

Validated full pipeline on 36 Briony images: `dataset_tool.py` → `train.py` → `.pkl` checkpoint.

```
Config: stylegan2, 512x512, 1× H200, batch=16, gamma=6.6, 25 kimg
FID50k: 388.05 (0 kimg) → 340.77 (25 kimg)
Time: ~18 min total
```

As expected, FID is high with only 36 images — the model needs the base+fine-tune approach. But the pipeline works: checkpoints load, fakes grids show recognizable marine forms. PKL checkpoints saved locally in `models/briony-test-run/` (not committed — ~347 MB each, available on request).

## Verification Checklist

- [x] Parser fix validated: spot-check 10 species common/scientific alignment
- [x] Visual QC: all 37 species contact sheets reviewed, 201 rejects documented with reasons
- [x] No single Briony source contributes >6 crops
- [x] `briony-marine-colour/`: 36 clean images, all marine/ecological
- [x] `marine-photo-base/`: 539 images, QC-reviewed from 740 candidates
- [x] `provenance.csv` complete for every training image (776 rows total)
- [x] Pilot 512px training validates quality (TELUS smoke test)
- [ ] Base model training on 539 marine photos
- [ ] Fine-tune on Briony corpus from base checkpoint
- [ ] `dream_briony.py` pipeline still functional as fallback
