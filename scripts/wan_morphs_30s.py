#!/usr/bin/env python3
"""
wan_morphs_30s.py — 30-second Wan I2V metamorphosis sequences.

Run on TELUS notebook 2:
    python /home/jovyan/wan_morphs_30s.py

Generates 30s (241 frames @ 8fps) versions of the two most cinematic morphs:
  - fish_school_to_murmuration (herring rises from ocean, becomes birds)
  - murmuration_to_whale (flock condenses into a single whale)

Output: /home/jovyan/wan_output/morphs_30s/
"""

import gc
import logging
import os
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "diffusers>=0.32.0", "transformers", "accelerate", "safetensors",
    "imageio", "imageio-ffmpeg", "Pillow",
])

import torch
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/jovyan/wan_morphs_30s.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("wan_morphs_30s")

OUTPUT_DIR = Path("/home/jovyan/wan_output/morphs_30s")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 480, 480
NUM_FRAMES = 241    # 241 frames @ 8fps = ~30s
FPS = 8
INFERENCE_STEPS = 30
GUIDANCE_SCALE  = 5.0
SEEDS = [42, 123, 256]

NEG_PROMPT = "blurry, distorted, low quality, deformed, static, frozen, pixelated"

PAINTINGS  = "/home/jovyan/output/inputs"
MURM_PATH  = "/home/jovyan/start_images/murmuration.jpg"
MURM_URL   = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/"
    "Murmuration_of_starlings_in_October_2014.jpg/"
    "1280px-Murmuration_of_starlings_in_October_2014.jpg"
)

MORPHS = [
    (
        f"{PAINTINGS}/inshore.jpg",
        "fish_school_to_murmuration_30s",
        "A vast silver school of herring flowing through blue ocean water slowly rises toward the surface, "
        "the fish leaping into the air, their silver bodies catching light as they transform into starlings, "
        "the school seamlessly becoming a murmuration that sweeps and billows across the grey sky above the Salish Sea, "
        "continuous organic metamorphosis, dreamlike, cinematic, slow motion",
    ),
    (
        MURM_PATH,
        "murmuration_to_whale_30s",
        "Thousands of birds in a murmuration above the ocean coalesce and condense, "
        "spiraling downward into the water, the flock compressing into a single massive form — "
        "a humpback whale that breaches through the surface in slow motion, "
        "dreamlike metamorphosis, Pacific Northwest ocean, cinematic, slow motion",
    ),
]


def _ensure_murmuration():
    p = Path(MURM_PATH)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    log.info("Downloading murmuration image...")
    try:
        req = urllib.request.Request(MURM_URL, headers={"User-Agent": "WanMorphs/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            p.write_bytes(resp.read())
        log.info(f"Saved: {p} ({p.stat().st_size/1e6:.1f} MB)")
    except Exception as e:
        log.warning(f"Download failed ({e}) — using placeholder")
        Image.new("RGB", (W, H), (30, 35, 50)).save(str(p))


def load_start_image(path):
    if not os.path.exists(path):
        log.warning(f"Start image not found: {path} — using placeholder")
        return Image.new("RGB", (W, H), (30, 50, 80))
    img = Image.open(path).convert("RGB")
    target_ratio = W / H
    img_ratio = img.width / img.height
    if img_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    return img.resize((W, H), Image.LANCZOS)


def save_video(frames, path, fps):
    import imageio
    import numpy as np
    writer = imageio.get_writer(str(path), fps=fps, codec="libx264",
                                quality=8, pixelformat="yuv420p")
    for frame in frames:
        writer.append_data(frame if isinstance(frame, np.ndarray) else np.array(frame))
    writer.close()
    size_mb = Path(path).stat().st_size / 1e6
    log.info(f"  Saved: {path.name} ({size_mb:.1f} MB, {len(frames)} frames @ {fps}fps)")


def main():
    log.info("=" * 70)
    log.info("WAN MORPHS 30s — Salish Sea cinematic sequences")
    log.info(f"Output: {OUTPUT_DIR}")
    log.info(f"Frames: {NUM_FRAMES} @ {FPS}fps = {NUM_FRAMES/FPS:.0f}s")
    log.info("=" * 70)

    _ensure_murmuration()

    log.info("Loading Wan I2V 14B pipeline...")
    t0 = time.time()
    from diffusers import WanImageToVideoPipeline
    pipe = WanImageToVideoPipeline.from_pretrained(
        "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers",
        torch_dtype=torch.float16,
    )
    pipe.to("cuda")
    pipe.enable_model_cpu_offload()
    log.info(f"Pipeline loaded in {time.time()-t0:.0f}s")

    total_ok = 0
    total_fail = 0

    for img_path, out_name, prompt in MORPHS:
        log.info(f"\n{'='*60}")
        log.info(f"MORPH: {out_name}")
        log.info(f"{'='*60}")
        img = load_start_image(img_path)

        for seed in SEEDS:
            tag      = f"{out_name}_s{seed}"
            out_path = OUTPUT_DIR / f"{tag}.mp4"

            if out_path.exists():
                log.info(f"  SKIP (exists): {tag}")
                total_ok += 1
                continue

            log.info(f"\n  Generating: {tag}")
            t0 = time.time()
            try:
                gen = torch.Generator("cuda").manual_seed(seed)
                output = pipe(
                    image=img,
                    prompt=prompt,
                    negative_prompt=NEG_PROMPT,
                    height=H, width=W,
                    num_frames=NUM_FRAMES,
                    num_inference_steps=INFERENCE_STEPS,
                    guidance_scale=GUIDANCE_SCALE,
                    generator=gen,
                )
                frames = output.frames[0]
                elapsed = time.time() - t0
                log.info(f"  Generated {len(frames)} frames in {elapsed:.0f}s ({elapsed/len(frames):.1f}s/frame)")

                save_video(frames, out_path, fps=FPS)
                save_video(frames, OUTPUT_DIR / f"{tag}_16fps.mp4", fps=16)

                total_ok += 1
                del output, frames
                gc.collect()
                torch.cuda.empty_cache()

            except Exception as e:
                log.error(f"  FAILED {tag}: {e}")
                traceback.print_exc()
                total_fail += 1
                gc.collect()
                torch.cuda.empty_cache()

    log.info("\n" + "=" * 70)
    log.info(f"DONE — {total_ok} ok, {total_fail} failed")
    log.info(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log.info(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
