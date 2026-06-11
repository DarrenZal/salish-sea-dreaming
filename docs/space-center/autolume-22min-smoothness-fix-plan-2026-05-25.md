# Plan — Fix the 22-min Autolume "too fast / jumps" feedback

**Source of Pravin's feedback** (Signal, 2026-05-24):

- 17:20: *"the automoin 22m did not work. ... it did what one of the earlier tests did - move very fast and jump... not a smooth evolving undulation as with the live version."*
- 17:29: *"it was wayyyy too fast and it skipped frames."*
- 17:38: *"35GB crashed Alley and then Resolume."* (his H.264 → AVI conversion attempt blew up)
- 17:43: *"please personally check the next version before send to me."* (explicit operator-QC requirement)

What we delivered: 22-min Autolume baseline, 3840×2160 / 30fps / H.264 / 7.9 GB, upscaled from native 1024² Autolume output via H200.

## Root cause hypothesis

The recorded output captures the GAN at a **higher per-frame latent step rate than live**. Live Autolume runs at ~8.7 fps on this 3090 (GPU shared w/ TD+SD+Arena, per `project_autolume_fps_expected.md`). Pravin's eyes integrate the slow live cadence into smooth flow. The offline recorder, however, drives the GAN to produce a unique frame for every 30-fps output frame — making the GAN step ~3.5× faster than its live performance pace. That's the "wayyyy too fast" reading.

**This is not `noise_anim=True`** — earlier session memory pinned the issue there, but `01_baseline` variant in `autolume_sweep.py` already has `noise_anim=False`. The "jump" sensation is **step-rate-too-high**, not noise-mutation.

Secondary issues:
- **H.264 format wrong for Pravin's Resolume pipeline.** He needs HAP MOV (Resolume-native, GPU-decoded, no Alley transcode needed). His attempt to convert H.264 → AVI was the 35 GB crash.
- **No operator-side QC happened on our delivery.** That's the `feedback_personal_review_before_send_to_pravin` contract — must view first 30s on this side before send.

## The fix — three parts

### Part 1 — Slow the latent walk to match live cadence

Need to identify and dial down the per-frame latent step in `autolume_sweep.py` so that 22 min × 30 fps of recorded frames covers the same latent distance as 22 min × 8.7 fps of live cadence — i.e. **step ~3.5× smaller per frame**.

Dial candidates (need to confirm in `modules/autolume_live.py` + preset 0 widgets):
- **`latent_walk` widget speed** — most likely lives in `viz.latent_walk_widget.params.speed` or similar
- **`trunc_noise_widget`** params — these are already what we override (`trunc_psi`, `noise_seed`, `noise_anim`); the speed dial is probably separate
- **Preset 0's saved walk speed** — if the saved preset has a "speed=1.0" dial, we override to "speed=0.28" (1/3.5)

Action: SSH into 3090, read `modules/autolume_live.py` (or wherever the walk widget lives) to confirm the exact attribute name, then add it to `_apply_variant` in `autolume_sweep.py`.

### Part 2 — Encode directly to HAP MOV, skip Resolume's transcode pain

After the autolume recorder finishes (it writes mp4v in MP4), we transcode in one step on the 3090:

```bash
ffmpeg -i out_raw.mp4 -c:v hap -format hap out_hap.mov
```

Output: HAP MOV, native to Resolume, no Alley step, no AVI bloat. Tradeoff: HAP files are larger than H.264 (5–10× depending on content) — at 22min @ 5120×1600 HAP, expect 40–80 GB. Pravin can play directly off external SSD or off Proton Drive download.

Alternative if size is unworkable: **HAP_q** (HAP "high quality") at ~half the bitrate, still GPU-decoded.

### Part 3 — Operator-side QC before send

Per `feedback_personal_review_before_send_to_pravin_md`: I will play the first 30 seconds locally (scp a sample to laptop, watch in VLC) before any send. If it looks fast/jumpy/wrong, we iterate before involving Pravin. **No Signal-send to Pravin until that QC pass.**

## Resource plan

Need GPU for the render. Current state (verified 2026-05-25 ~11:25 PT):
- 97% GPU util, 12.7 GB VRAM used
- `PID 39544 — streamdiffusionTD\td_main.py` is the long-running CPU-145h process. **DO NOT KILL** — this is StreamDiffusion+TD live infrastructure for the show. Operator confirms TD is live.
- Autolume.exe x2 (PIDs 35564, 38624) — running but operator says "nobody using right now"
- Resolume Alley + OBS — non-critical, can close

To run the 22-min Autolume render cleanly, we either:
- **Coexist with TD+SD on 3090** — if VRAM headroom allows. Autolume's preset 0 PKL is 1024² and uses ~3–4 GB VRAM. 24 GB total – 12.7 used = 11 GB free → should fit, but contention will slow the render.
- **Pause TD+SD for the render** — operator decision; impacts other show prep.
- **Render on a different machine** — TELUS H200 access exists; could move the autolume pipeline there. But Autolume is finicky and only known-working on Pravin's exact 3090 setup. Risk: rebuild env on H200 takes hours.

Recommendation: try coexistence first. If OOM or unacceptably slow, surface to operator and decide whether to pause TD.

## Estimated render time

At ~8.7 fps GAN speed coexisting with TD, 22 min × 30 fps recorded ÷ 8.7 fps GAN = **~75 min real wall-time** for the render itself. Plus ~5–10 min HAP transcode. Total ~80–90 min from start to file-ready.

If we pause TD: GAN may hit 15–20 fps → **~33–44 min render**. Tradeoff: TD pause time.

## Acceptance criteria

A re-render passes if:
1. **Smooth motion** — visually matches the live Autolume cadence Pravin sees on his Mac. Verified by side-by-side comparison of the first 30s of recorded output vs live screen capture.
2. **No frame skipping** — recorder produces all 22 min × 30 fps = 39,600 frames with no drops (verify with ffprobe `nb_frames`).
3. **HAP MOV** loads directly in Resolume without Alley transcode (verify on 3090 if Resolume Arena is installed there; otherwise Pravin's Mac test).
4. **File size ≤ 80 GB** for the HAP MOV (or HAP_q if 80 is exceeded).
5. **Operator-side QC pass** — I watch first 30s in VLC before any send.

## Open questions to confirm before firing

1. **Exact resolution target.** Native Autolume is 1024². The May 24 delivery was 3840×2160. Tobias's spec is **2:1 4K (~3840×1920 or 4096×2048) for the venue**. The projector array native is **5120×1600** (per OBS NDI probe today). Which do we render to? If we upscale on H200, native autolume 1024² → 5120×1600 ratio is ~5× — close to the limit but doable. If we just render at 1024² and upscale to 3840×2160, that's what the May 24 delivery did.
2. **Walk-speed dial location.** Need to inspect Autolume source on 3090. Will do this WITHOUT firing compute — read-only file inspect.
3. **Co-exist with TD or pause it.** Operator decision.

## Step sequence (after operator approval)

1. **Read autolume_live.py + preset 0** on 3090 — find the walk-speed dial. (No GPU compute; SSH file reads only.)
2. **Add `walk_speed` override to `autolume_sweep.py`** — local edit, push via scp.
3. **Smoke test with a 30-second render** — verify the speed feels right. ~5 min wall-time.
4. **Operator QC the 30s test** — me on the laptop, watch in VLC.
5. **If smooth: fire 22-min render.** ~75 min coexisting w/ TD, or ~40 min pausing TD.
6. **HAP transcode.** ~5–10 min.
7. **H200 upscale to 5120×1600 (or 3840×1920)** if we kept native res through autolume. ~30 min.
8. **Operator final QC of first 30s of full file.**
9. **Send to Pravin via Proton Drive** with codec specs in the message.

Total wall-time best-case: ~3 hours. Worst-case w/ retries: 6+ hours.
