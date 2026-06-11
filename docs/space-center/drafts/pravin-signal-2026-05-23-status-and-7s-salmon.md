When you're back from garden — quick check + status:

Q: Where's the original 4K 7 S salmon you're working with? Our local Moonfish hero clips (H1-H8) are all 1080p in the archive. Want to make sure I don't double-upscale or miss something you already have.

Pipeline now live across 2 H200 pods in parallel:
- H1 Salmon ESRGAN 4K → ~19:00 PDT (pod 1, in flight)
- H2 Herring ESRGAN 4K → ~20:25 PDT (pod 2, just started in parallel)
- Autolume baseline 22-min 4K (ffmpeg lanczos, not AI — tonight-feasible) → landing in ~2 min
- H3-H8 ESRGAN 4K → overnight, ready by morning
- Briony archive (91 MB, 9 categories, 206 files) → packaged, ready to drop on Proton when you have a moment

ESRGAN x2plus runs at 0.47 fps on H200, so each ~60s 1080p clip is ~130 min single-pod. Full AI upscale of the 22-min Autolume would be ~21 hours — that's why baseline goes lanczos tonight; the ESRGAN-quality version we can fire overnight tomorrow if you want it.

Enjoy Ari's talk. I'll have most of the asset set ready by the time you're back at Pravin's.
