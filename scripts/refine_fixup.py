#!/usr/bin/env python3
"""
Fixup script: Re-encode missing videos and complete the inshore painting.
Runs after the main pipeline if it hit the unlink bug.
"""
import os
import sys
import time
import datetime
import subprocess
import math
import numpy as np
import torch
from pathlib import Path
from PIL import Image


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [FIXUP] {msg}", flush=True)


def gaussian_kernel(size, sigma=None):
    if sigma is None:
        sigma = size / 4.0
    x = np.arange(size) - size // 2
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum()


def temporal_smooth(frames_np, window=9, sigma=2.5):
    if len(frames_np) < window:
        return frames_np
    kernel = gaussian_kernel(window, sigma)
    half_w = window // 2
    smoothed = np.copy(frames_np).astype(np.float32)
    for i in range(len(frames_np)):
        start = max(0, i - half_w)
        end = min(len(frames_np), i + half_w + 1)
        k_start = half_w - (i - start)
        k_end = k_start + (end - start)
        k = kernel[k_start:k_end]
        k = k / k.sum()
        weighted = np.zeros_like(frames_np[0], dtype=np.float32)
        for j, ki in zip(range(start, end), k):
            weighted += frames_np[j].astype(np.float32) * ki
        smoothed[i] = np.clip(weighted, 0, 255)
    return smoothed.astype(np.uint8)


def frames_to_video(frames_dir, output_path, fps=30):
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frames = sorted(Path(frames_dir).glob("frame_*.png"))
    if not frames:
        log(f"  No frames in {frames_dir}")
        return False
    filelist = Path(frames_dir) / "_filelist.txt"
    with open(filelist, 'w') as f:
        for frame in frames:
            f.write(f"file '{frame}'\n")
    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-r", str(fps),
        "-i", str(filelist),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if filelist.exists():
        filelist.unlink()
    if result.returncode == 0:
        size_mb = Path(output_path).stat().st_size / 1e6
        log(f"  Video: {output_path.name} ({size_mb:.1f} MB)")
        return True
    else:
        log(f"  ERROR encoding: {result.stderr[-300:]}")
        return False


def main():
    log("=" * 60)
    log("FIXUP: Completing missing outputs")
    log("=" * 60)

    BASE = Path("/home/jovyan/refine")
    OUTPUT = BASE / "output"

    # ============================================================
    # FIXUP 1: R1 missing 16fps
    # ============================================================
    r1_smooth = OUTPUT / "01_murmuration_bg_anchor" / "smoothed"
    r1_16 = OUTPUT / "01_murmuration_bg_anchor" / "school_to_murmuration_bg_anchor_16fps.mp4"
    if r1_smooth.exists() and not r1_16.exists():
        log("\n--- R1: Encoding 16fps video ---")
        frames_to_video(r1_smooth, r1_16, 16)
    else:
        log(f"\nR1 16fps: {'exists' if r1_16.exists() else 'no smoothed frames'}")

    # ============================================================
    # FIXUP 2: R2 inshore painting + 16fps versions
    # ============================================================
    log("\n--- R2: Processing inshore painting ---")
    inshore_frames = OUTPUT / "02_living_paintings" / "inshore_frames"
    inshore_smooth = OUTPUT / "02_living_paintings" / "inshore_smoothed"

    if not inshore_frames.exists() or len(list(inshore_frames.glob("frame_*.png"))) < 300:
        # Need to render inshore
        inshore_path = BASE / "input" / "briony_paintings" / "briony_inshore.jpg"
        if not inshore_path.exists():
            log("  ERROR: briony_inshore.jpg not found")
        else:
            log("  Loading pipeline for inshore...")
            from diffusers import StableDiffusionImg2ImgPipeline, UniPCMultistepScheduler

            LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
            DEVICE = "cuda"
            DTYPE = torch.float16

            pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                "stable-diffusion-v1-5/stable-diffusion-v1-5",
                torch_dtype=DTYPE, safety_checker=None
            ).to(DEVICE)
            pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
            pipe.load_lora_weights(LORA_PATH)
            pipe.enable_attention_slicing()

            PROMPT = "brionypenn watercolor of Pacific Northwest inshore waters, kelp gently swaying, herring school drifting, light filtering through water, subtle current movement, natural history illustration"
            NEG = "blurry, low quality, deformed, ugly, cartoon, anime, 3d render, text, watermark, dramatic change, harsh, neon"
            N_FRAMES = 300
            ANCHOR_BLEND = 0.10
            SEED = 42
            IMG2IMG_STRENGTH = 0.10

            original = Image.open(inshore_path).convert("RGB").resize((512, 512))
            original_np = np.array(original, dtype=np.float32)

            inshore_frames.mkdir(parents=True, exist_ok=True)
            inshore_smooth.mkdir(parents=True, exist_ok=True)

            existing = sorted(inshore_frames.glob("frame_*.png"))
            start_frame = len(existing)
            if start_frame > 0:
                current = Image.open(existing[-1]).convert("RGB")
                log(f"  Resuming from frame {start_frame}")
            else:
                current = original.copy()

            rendered_frames = []
            for ef in existing:
                rendered_frames.append(np.array(Image.open(ef).convert("RGB")))

            timings = []
            for i in range(start_frame, N_FRAMES):
                start = time.perf_counter()
                phase = math.sin(2 * math.pi * i / 60) * 0.02
                strength = IMG2IMG_STRENGTH + phase
                gen = torch.Generator(DEVICE).manual_seed(SEED + i)

                result = pipe(
                    prompt=PROMPT,
                    negative_prompt=NEG,
                    image=current,
                    strength=max(0.05, min(0.15, strength)),
                    num_inference_steps=25,
                    guidance_scale=7.5,
                    generator=gen,
                ).images[0]

                result_np = np.array(result, dtype=np.float32)
                anchored_np = 0.90 * result_np + 0.10 * original_np
                anchored_np = np.clip(anchored_np, 0, 255).astype(np.uint8)
                anchored = Image.fromarray(anchored_np)

                anchored.save(inshore_frames / f"frame_{i:05d}.png")
                rendered_frames.append(anchored_np)
                current = anchored

                elapsed = time.perf_counter() - start
                timings.append(elapsed)
                if i % 30 == 0 or i == N_FRAMES - 1:
                    avg = sum(timings) / len(timings)
                    remaining = avg * (N_FRAMES - i - 1)
                    log(f"  Frame {i+1}/{N_FRAMES} — {elapsed:.2f}s (avg {avg:.2f}s, ETA {remaining/60:.1f}min)")

            # Temporal smooth
            log("  Temporal smoothing...")
            frames_np = np.array(rendered_frames)
            smoothed = temporal_smooth(frames_np, window=9, sigma=2.0)
            for i, frame in enumerate(smoothed):
                Image.fromarray(frame).save(inshore_smooth / f"frame_{i:05d}.png")

            del pipe
            torch.cuda.empty_cache()
    else:
        log(f"  Inshore frames already exist ({len(list(inshore_frames.glob('frame_*.png')))})")
        # Still might need smoothing
        if not inshore_smooth.exists() or len(list(inshore_smooth.glob("frame_*.png"))) < 300:
            log("  Smoothing existing frames...")
            frames_np = np.array([np.array(Image.open(f).convert("RGB")) for f in sorted(inshore_frames.glob("frame_*.png"))])
            smoothed = temporal_smooth(frames_np, window=9, sigma=2.0)
            inshore_smooth.mkdir(parents=True, exist_ok=True)
            for i, frame in enumerate(smoothed):
                Image.fromarray(frame).save(inshore_smooth / f"frame_{i:05d}.png")

    # Encode inshore videos
    if inshore_smooth.exists() and len(list(inshore_smooth.glob("frame_*.png"))) >= 300:
        v30 = OUTPUT / "02_living_paintings" / "living_inshore_30fps.mp4"
        v16 = OUTPUT / "02_living_paintings" / "living_inshore_16fps.mp4"
        if not v30.exists():
            log("  Encoding inshore 30fps...")
            frames_to_video(inshore_smooth, v30, 30)
        if not v16.exists():
            log("  Encoding inshore 16fps...")
            frames_to_video(inshore_smooth, v16, 16)

    # Encode estuary 16fps if missing
    estuary_smooth = OUTPUT / "02_living_paintings" / "estuary_smoothed"
    e16 = OUTPUT / "02_living_paintings" / "living_estuary_16fps.mp4"
    if estuary_smooth.exists() and not e16.exists():
        log("  Encoding estuary 16fps...")
        frames_to_video(estuary_smooth, e16, 16)

    # ============================================================
    # FIXUP 3: R3 missing videos
    # ============================================================
    log("\n--- R3: Checking eco HQ outputs ---")
    r3_dir = OUTPUT / "03_eco_hq"
    clips = ["eco_09_orca_surfacing", "eco_07_herring_school_tightening", "eco_02_murmuration_to_single_whale"]
    for clip in clips:
        smooth_dir = r3_dir / f"{clip}_hq_smoothed"
        v30 = r3_dir / f"{clip}_hq_30fps.mp4"
        v16 = r3_dir / f"{clip}_hq_16fps.mp4"
        frames_dir = r3_dir / f"{clip}_hq_frames"

        if frames_dir.exists() and len(list(frames_dir.glob("frame_*.png"))) >= 81:
            # Frames exist, check if smoothing needed
            if not smooth_dir.exists() or len(list(smooth_dir.glob("frame_*.png"))) < 81:
                log(f"  {clip}: Smoothing {len(list(frames_dir.glob('frame_*.png')))} frames...")
                smooth_dir.mkdir(parents=True, exist_ok=True)
                frames_np = np.array([np.array(Image.open(f).convert("RGB")) for f in sorted(frames_dir.glob("frame_*.png"))])
                smoothed = temporal_smooth(frames_np, window=9, sigma=2.5)
                for i, frame in enumerate(smoothed):
                    Image.fromarray(frame).save(smooth_dir / f"frame_{i+1:05d}.png")

            if smooth_dir.exists() and len(list(smooth_dir.glob("frame_*.png"))) >= 81:
                if not v30.exists():
                    log(f"  {clip}: Encoding 30fps...")
                    frames_to_video(smooth_dir, v30, 30)
                if not v16.exists():
                    log(f"  {clip}: Encoding 16fps...")
                    frames_to_video(smooth_dir, v16, 16)
            else:
                log(f"  {clip}: Not enough smoothed frames")
        else:
            n = len(list(frames_dir.glob("frame_*.png"))) if frames_dir.exists() else 0
            log(f"  {clip}: Only {n} frames rendered (need 81) — re-run R3")

    # ============================================================
    # Summary
    # ============================================================
    log("\n" + "=" * 60)
    log("FIXUP COMPLETE — All outputs:")
    log("=" * 60)
    for f in sorted(OUTPUT.rglob("*.mp4")):
        rel = f.relative_to(OUTPUT)
        log(f"  {rel} ({f.stat().st_size/1e6:.1f} MB)")

    # Completion marker
    marker = OUTPUT / "REFINE_COMPLETE"
    with open(marker, "w") as fh:
        fh.write(f"Completed: {datetime.datetime.now().isoformat()}\n")
        for f in sorted(OUTPUT.rglob("*.mp4")):
            fh.write(f"  {f.relative_to(OUTPUT)} ({f.stat().st_size/1e6:.1f} MB)\n")
    log("Done.")


if __name__ == "__main__":
    main()
