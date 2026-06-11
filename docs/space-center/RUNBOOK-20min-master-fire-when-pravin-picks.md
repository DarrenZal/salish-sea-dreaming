# Runbook: 20-min Autolume 4K Master — Fire on Pravin's Variant Pick

**Status:** Awaiting Pravin's variant pick (Signal `1779486026959` sent 2026-05-22).
**Target deliverable:** One 20-min 4K (3840×2160) MP4, continuous non-repeating, for Pravin's Saturday theatre recording. **Use case:** single layer in Resolume during 20-min performance.

## Variant → JSON

| Pravin's pick | psi  | seed | anim  |
|---------------|------|------|-------|
| baseline      | 0.8  | 0    | False |
| tight_psi050  | 0.5  | 0    | False |
| wild_psi120   | 1.2  | 0    | False |
| noise_drift   | 0.8  | 0    | True  |
| seed42        | 0.8  | 42   | False |

**For non-repeating over 20 min:** consider adding `noise_anim=True` on top of his pick. This adds frame-by-frame mutation that breaks visible repeat if the latent looper has a short cycle. Trade-off: subtle texture mutation may shift the aesthetic. If Pravin's pick is already `noise_drift`, this is already on. **Decision: ask Pravin on the variant Signal reply.**

## Step 1 — Build variants JSON (Mac, instant)

```bash
PICK="wild_psi120"  # ← replace with his pick
PSI=1.2; SEED=0; ANIM=false  # ← match his pick
ANIM_FOR_20MIN=true  # ← true if he wants guaranteed non-repeating

cat > /tmp/variants_20min.json <<EOF
[{"name": "${PICK}_20min", "trunc_psi": ${PSI}, "noise_seed": ${SEED}, "noise_anim": ${ANIM_FOR_20MIN}}]
EOF
scp /tmp/variants_20min.json windows-desktop-remote:C:/Users/user/variants_20min.json
```

## Step 2 — Fire 20-min render on 3090 (real-time, ~20 min wall-clock)

```bash
# Outputs to C:\Users\user\autolume_20min\<timestamp>\<variant>_20min.mp4 (512² @ 30fps)
ssh windows-desktop-remote "schtasks /run /tn 'SSD-Autolume-Sweep'"
# OR for fully custom invocation:
ssh windows-desktop-remote "python C:\\Users\\user\\autolume\\autolume_sweep.py \
  --pkl C:\\Users\\user\\Documents\\models\\network-snapshot-000120.pkl \
  --preset C:\\Users\\user\\Documents\\presets\\0 \
  --output-dir C:\\Users\\user\\autolume_20min\\20260522 \
  --record-seconds 1200 \
  --variants-file C:\\Users\\user\\variants_20min.json"
```

**Note:** SSD-Autolume-Sweep task currently points to its existing args. To re-aim at the 20-min variants file, may need to recreate the task with new `/tr` args. Alternative: ssh into 3090 and run the python directly under a screen/start /b wrapper.

## Step 3 — Pull 512² master + upload to TELUS (~2 min)

```bash
mkdir -p /tmp/autolume_20min_$(date +%Y%m%d)
scp -O windows-desktop-remote:C:/Users/user/autolume_20min/20260522/wild_psi120_20min.mp4 \
       /tmp/autolume_20min_$(date +%Y%m%d)/
```

## Step 4 — H200 4K upscale (~5+ hrs)

```bash
cd /Users/darrenzal/projects/salish-sea-dreaming
python3 scripts/telus_upscale.py \
  --input /tmp/autolume_20min_$(date +%Y%m%d)/wild_psi120_20min.mp4 \
  --output /tmp/autolume_20min_$(date +%Y%m%d)/wild_psi120_20min_4k_crop.mp4 \
  --model x4plus \
  --framing crop \
  --canvas 3840x2160
```

**Time estimate:** 0.54 s/frame × 36,000 frames = **5.4 hours**. Run in background; check overnight.

**Optional speedup:** Try `--model x2plus` for ~2x faster (~2.7h) with light quality drop, then rely on ffmpeg lanczos to reach 4K. Pravin probably won't notice the diff at projection scale, but the 4× direct is the safer pick for hero deliverable.

## Step 5 — Sanity check + deliver

```bash
ffprobe -of json -show_format /tmp/autolume_20min_<date>/wild_psi120_20min_4k_crop.mp4
# Verify: duration ≈ 1200s, codec h264, resolution 3840×2160
```

Upload to Drive folder `1xP0dzNpibCJetoiRXmMG6zXcLg0weYZO` (Shawn's shared SSD), into a new subfolder `06_Autolume_4K_20min_Master/`. Signal Pravin the link.

## Total wall-clock from variant pick → delivery
- Step 1: 1 min
- Step 2: 20 min (real-time render)
- Step 3: 2 min (scp)
- Step 4: 5.4 hr (H200 upscale)
- Step 5: 2 min
- **Total: ~5.8 hours**

## Risk register
- **Cold-start renderer**: first variant in sweep typically loses ~60 frames during settle. Mitigation: the existing script settles 180 frames (6s) before recording — should be enough.
- **Visible loop period**: if Pravin's pick + noise_anim=False shows obvious repeat in 20 min, redo with anim=True (still ~5.8 hr lost). Mitigation: ask Pravin on the variant reply.
- **H200 pod expiry**: pods are ephemeral. Keep a session alive during the 5+ hr upscale. The telus_upscale.py driver handles reconnection but verify pod is up before firing.
- **Disk space on 3090**: 20 min @ 512² H.264 ≈ 600-800MB. Plenty of headroom.
