# Image Intake — David Denning

Thanks for contributing your marine photography to the Salish Sea Dreaming project. This document covers how to send files and how to organize them so they slot cleanly into our StyleGAN2 training pipeline.

## How to Send Files

Upload to a Google Drive folder and share the link with Darren. You can send images in batches — no need to wait until you have everything.

## Sorting by Visual Domain

Please sort images into subfolders by **visual domain**, not by species. We train separate models for each domain, so this grouping matters more than taxonomic categories.

| Folder name | What goes in it | Priority |
|-------------|-----------------|----------|
| `underwater-nearshore` | Fish, kelp, eelgrass, invertebrates, close underwater scenes | **v1 — top priority** |
| `surface-horizon` | Whales breaching, seabirds on water, ocean surface views | v2 |
| `boats-vessels` | Fishing boats, ferries, canoes, docks | v2 (separate model) |
| `aerial-coastal` | Coastline, estuaries, spawn events from above | v2 |

### Why underwater-nearshore is the priority

Your underwater and nearshore work may be the strongest base model source we have for this domain. If you can only do one batch, start here — it directly feeds the first model we are training.

### Other domains are still valuable

Surface, vessel, and aerial images will feed separate future models. Anything you have in those categories is welcome; they just come later in the pipeline.

## Provenance

For each batch you send, please include a quick note (a text file in the folder or an email) covering:

- **Photographer:** David Denning (or note if any images are from a collaborator)
- **Date range:** Approximate is fine (e.g., "Summer 2024" or "2020-2025")
- **Location:** General area (e.g., "Howe Sound", "Southern Gulf Islands")
- **Usage restrictions:** Anything we should know — otherwise we will assume the images are cleared for use in the project's generative models and derivative artworks

## Technical Notes

- **Highest resolution originals preferred** — RAW files or full-resolution JPEGs. The more detail the model can learn from, the better.
- **Minimum:** 500px on the shortest side. Anything smaller gets discarded during preprocessing.
- **File format:** RAW (any format), TIFF, PNG, or JPEG. We handle conversion on our end.
- **No need to edit or color-correct** — we want the images as close to original as possible.

## Questions?

Reach out to Darren (zaldarren@gmail.com) anytime.
