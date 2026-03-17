# Draft Signal Message to Arshia — 2026-03-11

**Status:** READY TO SEND — Arshia joined Signal March 11

---

Hey Arshia, welcome to the group! Quick summary of where we're at with the training pipeline:

**Current state:**
- Base corpus: 539 curated underwater/nearshore marine photos at 512x512 (iNaturalist, CC-licensed, QC'd from 740 candidates across 37 Salish Sea species)
- Fine-tune corpus: 54 Briony Penn ecological watercolors at 512x512 (expanded from marine-only to include salmon-forest, camas, and landscape subjects)
- Smoke test complete: 25 kimg on Briony corpus, StyleGAN2 config, 1x H200 — pipeline validated end-to-end (dataset_tool → train.py → .pkl checkpoint)
- **Dataset downloads (anyone with link):**
  - [marine-photo-base.zip](https://drive.google.com/file/d/1l1x0TEY8W9WNG7jIX9TZ5iFdQkRoyHfo/view) — 539 photos, 64 MB
  - [briony-marine-colour.zip](https://drive.google.com/file/d/1cOoF09ZuNjpXQocg_hJ7NuMobVNd5ioV/view) — 54 watercolors, 27 MB
- **Shared Drive folder:** https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr

**TELUS bottleneck we discovered:**
The TELUS H200 notebook doesn't have C/C++ compilers (gcc/g++/nvcc), so StyleGAN2's custom CUDA extensions can't compile. It falls back to pure-Python ops — 10-20x slower. Our 25 kimg smoke test took 3h 09m instead of the expected ~18 min. We're raising this at Friday's TELUS meeting.

**Questions for you:**
1. Does Compute Canada have a full dev environment (gcc, nvcc, CUDA toolkit)? If so we could run training there while waiting for TELUS to fix the compiler issue
2. For 539 underwater/nearshore photos at 512x512, what kimg would you recommend for the base model? We were planning kimg=200 as a quick v1 checkpoint, with kimg=2000 as the full run once compilers are sorted
3. You mentioned 36 images is sufficient for fine-tuning (the clown faces example) — just confirming that holds for our expanded 54-image Briony corpus
4. Happy to share both datasets if you want to run parallel training on Compute Canada — I can send a zip (~64 MB for the base corpus)
5. Prav mentioned you suggested the MOVE37XR Mac Mini M4 could run Autolume — but Autolume requires CUDA (NVIDIA GPU), and Apple Silicon uses Metal/MPS. Is there a way to make it work on M4, or were you thinking of a different tool? This affects our hardware plan for the installation.

The goal is to get a base checkpoint → fine-tune on Briony → hand off to Prav for Autolume/TouchDesigner integration. We're about 4 weeks from the Salt Spring Art Show opening (April 12).
