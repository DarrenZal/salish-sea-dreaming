#!/usr/bin/env python3
"""
briony_video_style.py — Apply Briony LoRA + ControlNet depth style transfer
to Wan morph videos, frame by frame, then reassemble as mp4.

Same pipeline as the salmon/herring TELUS renders (telus_style_server.py)
but operating on video frames for temporal consistency.

Run on TELUS (split across 3 notebooks using --worker):
    python /home/jovyan/briony_video_style.py --worker 0   # notebook 1
    python /home/jovyan/briony_video_style.py --worker 1   # notebook 2
    python /home/jovyan/briony_video_style.py --worker 2   # notebook 3

Input:  /home/jovyan/wan_output/morphs/*_20s.mp4  (and *_30s.mp4 if present)
Output: /home/jovyan/wan_output/morphs_briony/

Temporal consistency: fixed seed per video + ControlNet depth guidance.
"""

import argparse
import gc
import io
import logging
import subprocess
import sys
import time
import traceback
from pathlib import Path

subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "diffusers>=0.20.0", "transformers", "accelerate", "safetensors",
    "imageio", "imageio-ffmpeg", "Pillow", "numpy",
])

import numpy as np
import torch
import imageio
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/jovyan/briony_video_style.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("briony_video_style")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LORA_PATH        = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
INPUT_DIR_MORPHS = Path("/home/jovyan/wan_output/morphs")
INPUT_DIR_30S    = Path("/home/jovyan/wan_output/morphs_30s")
OUTPUT_DIR       = Path("/home/jovyan/wan_output/morphs_briony")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE         = 512
STEPS            = 20          # fewer steps for speed; quality still good
GUIDANCE         = 7.0
CONTROLNET_SCALE = 0.55
FPS_OUT          = 8

PROMPT = (
    "brionypenn watercolor painting, Pacific Northwest coastal ecosystem, "
    "natural history illustration, pen-and-ink outlines, soft organic watercolor tones, "
    "dreaming in the Salish Sea"
)
NEG_PROMPT = (
    "photo, photograph, realistic, 3d render, blurry, low quality, "
    "text, watermark, harsh lighting, overexposed"
)


def collect_input_videos():
    """Collect the 20s and 30s morph videos, one per morph (best seed = 42)."""
    videos = []
    # 20s versions from main run — prefer seed 42 as representative
    for p in sorted(INPUT_DIR_MORPHS.glob("*_s42_20s.mp4")):
        if "_16fps" not in p.name:
            videos.append(p)
    # 30s versions
    for p in sorted(INPUT_DIR_30S.glob("*_s42.mp4")):
        if "_16fps" not in p.name:
            videos.append(p)
    return videos


def assign_worker_videos(all_videos, worker_id, num_workers):
    """Distribute videos across workers by index."""
    return [v for i, v in enumerate(all_videos) if i % num_workers == worker_id]


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_pipeline():
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler
    from transformers import DPTForDepthEstimation, DPTImageProcessor

    log.info("Loading DPT depth estimator...")
    t0 = time.time()
    depth_processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
    depth_model     = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")
    depth_model     = depth_model.to("cuda").eval()
    log.info(f"DPT loaded in {time.time()-t0:.1f}s")

    log.info("Loading ControlNet depth...")
    t0 = time.time()
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16,
    )
    log.info(f"ControlNet loaded in {time.time()-t0:.1f}s")

    log.info("Loading SD 1.5 pipeline...")
    t0 = time.time()
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.to("cuda")
    pipe.enable_attention_slicing()
    log.info(f"SD 1.5 loaded in {time.time()-t0:.1f}s")

    log.info(f"Loading Briony LoRA from {LORA_PATH}...")
    t0 = time.time()
    pipe.load_lora_weights(LORA_PATH)
    log.info(f"LoRA loaded in {time.time()-t0:.1f}s")

    log.info("Pipeline ready.")
    return pipe, depth_processor, depth_model


def depth_map(img_pil, depth_processor, depth_model):
    inputs = depth_processor(images=img_pil, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = depth_model(**inputs).predicted_depth
    depth = out.squeeze().cpu().numpy()
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    depth_img = Image.fromarray((depth * 255).astype(np.uint8)).convert("RGB")
    return depth_img.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)


def style_frame(img_pil, pipe, depth_processor, depth_model, generator):
    img_resized = img_pil.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
    d_map = depth_map(img_resized, depth_processor, depth_model)
    result = pipe(
        prompt=PROMPT,
        negative_prompt=NEG_PROMPT,
        image=d_map,
        num_inference_steps=STEPS,
        guidance_scale=GUIDANCE,
        controlnet_conditioning_scale=CONTROLNET_SCALE,
        generator=generator,
        width=IMG_SIZE,
        height=IMG_SIZE,
    ).images[0]
    return result


def process_video(video_path, pipe, depth_processor, depth_model, seed=42):
    out_name   = video_path.stem + "_briony.mp4"
    out_path   = OUTPUT_DIR / out_name
    if out_path.exists():
        log.info(f"  SKIP (exists): {out_name}")
        return True

    log.info(f"\nProcessing: {video_path.name}")
    t_video = time.time()

    try:
        reader = imageio.get_reader(str(video_path))
        meta   = reader.get_meta_data()
        in_fps = meta.get("fps", FPS_OUT)
        raw_frames = [Image.fromarray(f).convert("RGB") for f in reader]
        reader.close()
        log.info(f"  Loaded {len(raw_frames)} frames @ {in_fps}fps")

        # Fixed generator seed for temporal consistency
        generator = torch.Generator(device="cuda").manual_seed(seed)

        styled_frames = []
        for i, frame in enumerate(raw_frames):
            t0 = time.time()
            styled = style_frame(frame, pipe, depth_processor, depth_model, generator)
            elapsed = time.time() - t0
            styled_frames.append(np.array(styled))
            if (i + 1) % 10 == 0 or i == 0:
                eta = elapsed * (len(raw_frames) - i - 1)
                log.info(f"  Frame {i+1}/{len(raw_frames)} ({elapsed:.1f}s/frame, ETA {eta/60:.1f}min)")

        # Write output video
        writer = imageio.get_writer(
            str(out_path), fps=FPS_OUT, codec="libx264",
            quality=8, pixelformat="yuv420p"
        )
        for f in styled_frames:
            writer.append_data(f)
        writer.close()

        size_mb = out_path.stat().st_size / 1e6
        total_t = time.time() - t_video
        log.info(f"  Done: {out_name} ({size_mb:.1f} MB, {total_t/60:.1f}min total)")

        del styled_frames, raw_frames
        gc.collect()
        torch.cuda.empty_cache()
        return True

    except Exception as e:
        log.error(f"  FAILED {video_path.name}: {e}")
        traceback.print_exc()
        gc.collect()
        torch.cuda.empty_cache()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker",      type=int, default=0, help="Worker index (0, 1, or 2)")
    parser.add_argument("--num-workers", type=int, default=3, help="Total number of workers")
    parser.add_argument("--seed",        type=int, default=42, help="Fixed seed for temporal consistency")
    args = parser.parse_args()

    all_videos = collect_input_videos()
    my_videos  = assign_worker_videos(all_videos, args.worker, args.num_workers)

    log.info("=" * 70)
    log.info(f"BRIONY VIDEO STYLE TRANSFER — worker {args.worker}/{args.num_workers}")
    log.info(f"Total input videos: {len(all_videos)}")
    log.info(f"This worker: {len(my_videos)} videos")
    log.info(f"Output: {OUTPUT_DIR}")
    log.info("=" * 70)

    if not my_videos:
        log.info("No videos assigned to this worker — exiting")
        return

    for v in my_videos:
        log.info(f"  Queued: {v.name}")

    pipe, depth_processor, depth_model = load_pipeline()

    ok = fail = 0
    for v in my_videos:
        result = process_video(v, pipe, depth_processor, depth_model, seed=args.seed)
        if result:
            ok += 1
        else:
            fail += 1

    log.info("\n" + "=" * 70)
    log.info(f"DONE — worker {args.worker}: {ok} ok, {fail} failed")
    log.info(f"Output: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.glob("*.mp4")):
        log.info(f"  {f.name} ({f.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
