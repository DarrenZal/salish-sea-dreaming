# Screen Share with Prav — March 11, 5pm

## 1. Repo Walkthrough (5 min)
```
salish-sea-dreaming/
├── training-data/
│   ├── briony-marine-colour/  ← 54 watercolors at 512x512
│   └── marine-photo-base/     ← 539 marine photos at 512x512
├── models/briony-test-run/    ← 3 smoke test .pkl checkpoints
├── scripts/                   ← prep_training_data.py, crop_candidates.py
├── tools/                     ← iNat scraper, QC pipeline
├── VisualArt/Brionny/         ← Full art archive (git-lfs)
└── docs/autolume-integration.md ← The key technical doc
```

## 2. Training Corpora (5 min)
- Show Briony corpus (54 images) — scroll through `training-data/briony-marine-colour/`
- Show marine base corpus sample — open a few from `training-data/marine-photo-base/`
- Show crop review contact sheets in `training-data/review/contact-sheets/`
- Explain provenance tracking (`provenance.csv`, `keep.csv`, `rejects.csv`)

## 3. Smoke Test Results (5 min)
- Show `models/briony-test-run/` — 3 PKLs (0, 20, 25 kimg)
- Explain FID trajectory: 474.6 → 556.0 → 502.8 (expected with 36 images, no base model)
- The 000025.pkl is the best checkpoint — give to Prav for Autolume testing
- **Already uploaded to Drive** (links in prav-reply doc)

## 4. Autolume Integration Architecture (10 min)
Open `docs/autolume-integration.md` and walk through:
- Training pipeline: marine base → Briony fine-tune → photographic→painterly gradient
- Five Threads model concept (herring, salmon, orca, kelp, deep water)
- Autolume → NDI → TouchDesigner pipeline
- OSC/MIDI bidirectional control
- **Critical: Autolume is Windows/Linux only — no macOS**

## 5. TELUS Training (5 min)
- Show TELUS notebook access (if Prav has it, let him drive)
- Training commands (from plan doc):
  ```
  python train.py --outdir=./results --cfg=stylegan2 \
    --data=./data/marine-base512.zip --gpus=1 --batch=32 \
    --gamma=6.6 --kimg=200 --snap=10
  ```
- Compiler blocker (Q6) — 10-20x slowdown, pushing for fix Friday
- Ephemeral storage warning: download PKLs immediately

## 6. Hardware for Installation (5 min)
- Prav's RTX 3060: good for Autolume inference (test with smoke PKLs today)
- M4 Mac: **will NOT work** — needs NVIDIA for CUDA
- Installation needs: dedicated NVIDIA GPU machine
- Options: desktop with RTX 3060+, or Nicholas's LED volume infrastructure

## 7. Next Steps / Action Items
- [ ] Prav: download PKLs from Drive, test in Autolume
- [ ] Prav: confirm his OS/GPU setup for inference
- [ ] Darren: upload marine-photo-base.zip to TELUS tomorrow, start base training
- [ ] Darren: share fine-tune PKLs as they appear (snap=10 = every 10 kimg)
- [ ] Both: hardware plan for Salt Spring installation (4 weeks out)

## Drive Links (for Prav)
- [network-snapshot-000000.pkl](https://drive.google.com/file/d/1MJGq7VkvS6V3aZKIkKsOQIsTyObT0a5_/view)
- [network-snapshot-000020.pkl](https://drive.google.com/file/d/1tquQsIQCTiplsLDPZRBOXGsT_5qtEfQR/view)
- [network-snapshot-000025.pkl](https://drive.google.com/file/d/1WOMcUhi3RaML_TjqEilvHZOh8mBNyu7E/view) ← best
- [briony-marine-colour.zip](https://drive.google.com/file/d/1cOoF09ZuNjpXQocg_hJ7NuMobVNd5ioV/view) (27 MB)
- [marine-photo-base.zip](https://drive.google.com/file/d/1l1x0TEY8W9WNG7jIX9TZ5iFdQkRoyHfo/view) (64 MB)
