# Reply to Prav — 2026-03-11

**Status:** SENT via Signal (March 11, ~3pm)

---

Hey Prav, great that you're focused on SSD the next couple days. Here's what I have ready:

**Assets ready for you:**
- 54 Briony ecological watercolors (curated, 512x512) — expanded from marine-only to include salmon-forest, camas, landscapes
- 539 underwater/nearshore marine photos (base corpus) — zipped and ready for TELUS upload (64 MB)
- Smoke test checkpoints from the Briony-only run (3 .pkl files, ~347 MB each):
  - [network-snapshot-000000.pkl](https://drive.google.com/file/d/1MJGq7VkvS6V3aZKIkKsOQIsTyObT0a5_/view) (initial)
  - [network-snapshot-000020.pkl](https://drive.google.com/file/d/1tquQsIQCTiplsLDPZRBOXGsT_5qtEfQR/view) (20 kimg)
  - [network-snapshot-000025.pkl](https://drive.google.com/file/d/1WOMcUhi3RaML_TjqEilvHZOh8mBNyu7E/view) (25 kimg — best)
- Training corpus zips:
  - [briony-marine-colour.zip](https://drive.google.com/file/d/1cOoF09ZuNjpXQocg_hJ7NuMobVNd5ioV/view) (54 watercolors, 27 MB)
  - [marine-photo-base.zip](https://drive.google.com/file/d/1l1x0TEY8W9WNG7jIX9TZ5iFdQkRoyHfo/view) (539 photos, 64 MB)
- Species contact sheets (37 PNGs showing what's in the base corpus)
- Existing docs: `docs/autolume-integration.md` covers the full TELUS bootstrap, training commands, and OSC/NDI architecture
- **Shared Drive:** https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr

**Quick question before screen share:**
- Are you on Windows or Linux with an NVIDIA GPU? That determines whether you can run Autolume locally today or if we're focused on checkpoint handoff + orientation
- Do you have TELUS notebook access yourself, or should I drive?

**Training plan:**
Base model on 539 marine photos → fine-tune on Briony's 54 watercolors → gradient of checkpoints from photographic to painterly (multiple snapshots at `--snap=10`).

One thing to know: the TELUS environment is ~10-20x slower than expected due to missing compilers (no CUDA extension compilation). We're pushing for a fix Friday. kimg=200 v1 checkpoint is the realistic target — gets you something to work with while we sort the full run.

Screen share at 5pm today — I'll walk you through the pipeline.
