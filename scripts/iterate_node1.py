#!/usr/bin/env python3
"""
Salish Sea Dreaming — Iteration Pipeline on TELUS Node 1 (H200)

Three iterations:
  1. Morphic Resonance — Fish <-> School oscillation (Wan T2V + ControlNet depth + LoRA)
  2. Orca Becoming Salmon — Breach transforms to school (Wan T2V + ControlNet depth + LoRA)
  3. Living Painting — Fixed drift version (img2img from ORIGINAL each frame)

Dependencies installed at start: diffusers, controlnet_aux, transformers, etc.
Downloads: Briony LoRA from Node 2, SD 1.5 from HF, ControlNet depth from HF.

Usage:
  nohup python3 iterate_node1.py > /home/jovyan/iterate/stdout.log 2>&1 &
"""
import os, sys, time, gc, signal, subprocess, logging, traceback, json, uuid
import urllib.request
import numpy as np

# ── Directories ──────────────────────────────────────────────────────────
BASE = "/home/jovyan/iterate"
OUTPUT = os.path.join(BASE, "output")
FRAMES = os.path.join(BASE, "frames")
MODELS = os.path.join(BASE, "models")
LOGFILE = os.path.join(BASE, "progress.log")

for d in [BASE, OUTPUT, FRAMES, MODELS]:
    os.makedirs(d, exist_ok=True)

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ITERATE] %(message)s",
    handlers=[
        logging.FileHandler(LOGFILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)
log.info("=" * 70)
log.info("ITERATION PIPELINE — Starting")
log.info("=" * 70)

# ── Install dependencies ─────────────────────────────────────────────────
log.info("Phase 0: Installing dependencies...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q",
    "diffusers>=0.32.0", "transformers>=4.40.0", "accelerate", "safetensors",
    "peft", "imageio", "imageio-ffmpeg", "Pillow", "scipy",
    "opencv-python-headless",
])
log.info("Dependencies installed")

import torch
from PIL import Image, ImageFilter
import imageio

# ── Utility functions ────────────────────────────────────────────────────

def save_video(frames_pil, path, fps=16):
    """Save list of PIL images as mp4 video."""
    writer = imageio.get_writer(path, fps=fps, codec="libx264",
                                output_params=["-pix_fmt", "yuv420p"])
    for frame in frames_pil:
        arr = np.array(frame)
        if arr.dtype in (np.float32, np.float64):
            arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        writer.append_data(arr)
    writer.close()
    log.info(f"  Saved video: {path} ({len(frames_pil)} frames @ {fps}fps)")


def save_frames_disk(frames_pil, outdir, prefix="frame"):
    """Save individual frames as PNGs."""
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, f in enumerate(frames_pil):
        p = os.path.join(outdir, f"{prefix}_{i:04d}.png")
        f.save(p)
        paths.append(p)
    return paths


def temporal_smooth(frames, window=9):
    """Apply temporal Gaussian smoothing across frame sequence."""
    from scipy.ndimage import gaussian_filter1d
    arr = np.stack([np.array(f).astype(np.float32) for f in frames])
    sigma = window / 4.0
    smoothed = gaussian_filter1d(arr, sigma=sigma, axis=0)
    return [Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)) for s in smoothed]


def kill_gpu_processes(exclude_pids=None):
    """Kill GPU processes to free memory. Optionally exclude certain PIDs."""
    if exclude_pids is None:
        exclude_pids = set()
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,name", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(",")
            pid = int(parts[0].strip())
            name = parts[1].strip() if len(parts) > 1 else ""
            if pid not in exclude_pids:
                log.info(f"  Killing GPU process: PID={pid} name={name}")
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
                except:
                    pass
    except Exception as e:
        log.info(f"  nvidia-smi check: {e}")


# ══════════════════════════════════════════════════════════════════════════
# PHASE 1: Download models
# ══════════════════════════════════════════════════════════════════════════

def download_models():
    log.info("\n" + "=" * 70)
    log.info("PHASE 1: Downloading models")
    log.info("=" * 70)

    # 1a. Download Briony LoRA from Node 2
    lora_path = os.path.join(MODELS, "briony_watercolor_v1.safetensors")
    if not os.path.exists(lora_path):
        log.info("Downloading Briony LoRA from Node 2...")
        node2_url = "https://ssd-style-transfer-2-0b50s.paas.ai.telus.com/files/style-transfer/briony_watercolor_v1.safetensors"
        req = urllib.request.Request(node2_url)
        req.add_header("Authorization", "Token 15335440de57b5646cd4c25bdf1957d5")
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        with open(lora_path, "wb") as f:
            f.write(data)
        log.info(f"  Briony LoRA saved: {lora_path} ({len(data)/1e6:.1f} MB)")
    else:
        log.info(f"  Briony LoRA already exists: {lora_path}")

    # Also save a copy to the standard path
    std_lora = "/home/jovyan/briony_watercolor_v1.safetensors"
    if not os.path.exists(std_lora):
        import shutil
        shutil.copy2(lora_path, std_lora)
        log.info(f"  Copied to standard path: {std_lora}")

    # 1b. Download inshore painting from Node 2 for Iteration 3
    inshore_path = os.path.join(MODELS, "briony_inshore.jpg")
    if not os.path.exists(inshore_path):
        log.info("Downloading Briony inshore painting from Node 2...")
        node2_url = "https://ssd-style-transfer-2-0b50s.paas.ai.telus.com/files/style-transfer/../output/inputs/briony_inshore.jpg"
        try:
            req = urllib.request.Request(node2_url)
            req.add_header("Authorization", "Token 15335440de57b5646cd4c25bdf1957d5")
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
            with open(inshore_path, "wb") as f:
                f.write(data)
            log.info(f"  Inshore painting saved: {inshore_path}")
        except Exception as e:
            log.info(f"  Node 2 download failed, trying local: {e}")
            # Fall back to local copy
            local = "/home/jovyan/output/inputs/briony_inshore.jpg"
            if os.path.exists(local):
                import shutil
                shutil.copy2(local, inshore_path)
                log.info(f"  Copied from local: {local}")
            else:
                # Use the regular inshore
                local2 = "/home/jovyan/output/inputs/inshore.jpg"
                if os.path.exists(local2):
                    import shutil
                    shutil.copy2(local2, inshore_path)
                    log.info(f"  Copied from local fallback: {local2}")
    else:
        log.info(f"  Inshore painting already exists: {inshore_path}")

    # 1c. Pre-download SD 1.5 and ControlNet via diffusers (will cache in HF cache)
    log.info("Pre-caching SD 1.5 + ControlNet depth model from HuggingFace...")
    from diffusers import ControlNetModel
    from diffusers import StableDiffusionPipeline

    # Just trigger the download, don't load to GPU yet
    log.info("  Downloading ControlNet depth model...")
    cn = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16,
    )
    del cn
    gc.collect()
    log.info("  ControlNet depth model cached")

    log.info("  Downloading SD 1.5 base model...")
    # Download as base pipeline (not ControlNet variant) — ControlNet is added later
    base = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    del base
    gc.collect()
    log.info("  SD 1.5 cached")

    # Pre-download DPT depth model (used instead of ZoeDetector to avoid controlnet_aux mediapipe issue)
    log.info("  Pre-downloading DPT depth model...")
    try:
        from transformers import DPTForDepthEstimation, DPTImageProcessor
        DPTImageProcessor.from_pretrained("Intel/dpt-large")
        DPTForDepthEstimation.from_pretrained("Intel/dpt-large", torch_dtype=torch.float32)
        log.info("  DPT depth model cached")
    except Exception as e:
        log.warning(f"  DPT pre-download failed (will retry later): {e}")

    log.info("PHASE 1 complete — all models downloaded")


# ══════════════════════════════════════════════════════════════════════════
# PHASE 2: ComfyUI helpers (for Wan T2V generation)
# ══════════════════════════════════════════════════════════════════════════

COMFYUI_URL = "http://127.0.0.1:8188"


def ensure_comfyui():
    """Make sure ComfyUI is running."""
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/system_stats")
        urllib.request.urlopen(req, timeout=5)
        log.info("ComfyUI already running")
        return True
    except:
        log.info("Starting ComfyUI...")
        subprocess.Popen(
            [sys.executable, "main.py", "--listen", "0.0.0.0", "--port", "8188"],
            cwd="/home/jovyan/ComfyUI",
            stdout=open("/home/jovyan/iterate/comfyui.log", "w"),
            stderr=subprocess.STDOUT,
        )
        # Wait for it to be ready
        for i in range(120):
            time.sleep(5)
            try:
                req = urllib.request.Request(f"{COMFYUI_URL}/system_stats")
                urllib.request.urlopen(req, timeout=5)
                log.info(f"ComfyUI started after {(i+1)*5}s")
                return True
            except:
                if i % 6 == 0:
                    log.info(f"  Waiting for ComfyUI... ({(i+1)*5}s)")
        log.error("ComfyUI failed to start after 600s")
        return False


def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt", data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["prompt_id"]


def wait_for_completion(prompt_id, timeout=1200):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            resp = urllib.request.urlopen(req)
            history = json.loads(resp.read())
            if prompt_id in history:
                entry = history[prompt_id]
                status = entry.get("status", {})
                if status.get("completed") or status.get("status_str") == "success":
                    return entry
                elif status.get("status_str") == "error":
                    msgs = status.get("messages", [])
                    for msg in msgs:
                        if isinstance(msg, list) and len(msg) > 1 and msg[0] == "execution_error":
                            err = msg[1]
                            raise RuntimeError(
                                f"Node {err.get('node_type')} (id {err.get('node_id')}): "
                                f"{err.get('exception_message')}"
                            )
                    raise RuntimeError("Unknown ComfyUI error")
        except urllib.error.URLError:
            pass
        elapsed = int(time.time() - start)
        if elapsed % 60 == 0 and elapsed > 0:
            log.info(f"  ComfyUI: {elapsed}s elapsed...")
        time.sleep(10)
    raise TimeoutError(f"Prompt did not complete in {timeout}s")


def collect_comfyui_frames(history_entry, prefix_filter=None):
    """Collect output frames from a ComfyUI history entry."""
    frames = []
    outputs = history_entry.get("outputs", {})
    for node_id, node_out in outputs.items():
        images = node_out.get("images", [])
        for img_info in images:
            fname = img_info["filename"]
            subfolder = img_info.get("subfolder", "")
            if prefix_filter and not fname.startswith(prefix_filter):
                continue
            img_path = os.path.join("/home/jovyan/ComfyUI/output", subfolder, fname)
            if os.path.exists(img_path):
                frames.append((fname, Image.open(img_path).copy()))
    # Sort by filename
    frames.sort(key=lambda x: x[0])
    return [f[1] for f in frames]


def wan_t2v(prompt, seed, frames=81, width=832, height=480, prefix="ssd"):
    """Generate video with Wan T2V 14B via ComfyUI."""
    workflow = {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": "Wan2_1-T2V-14B_fp8_e4m3fn.safetensors",
                "base_precision": "bf16",
                "quantization": "disabled",
                "load_device": "main_device",
            },
        },
        "2": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {
                "model_name": "umt5-xxl-enc-fp8_e4m3fn.safetensors",
                "precision": "bf16",
            },
        },
        "3": {
            "class_type": "WanVideoVAELoader",
            "inputs": {
                "model_name": "Wan2_1_VAE_bf16.safetensors",
                "precision": "bf16",
            },
        },
        "4": {
            "class_type": "WanVideoTextEncode",
            "inputs": {
                "positive_prompt": prompt,
                "negative_prompt": "blurry, low quality, text, watermark, static, still image, deformed",
                "t5": ["2", 0],
            },
        },
        "5": {
            "class_type": "WanVideoEmptyEmbeds",
            "inputs": {
                "width": width,
                "height": height,
                "num_frames": frames,
            },
        },
        "6": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": ["1", 0],
                "image_embeds": ["5", 0],
                "text_embeds": ["4", 0],
                "steps": 30,
                "cfg": 5.5,
                "shift": 5.0,
                "seed": seed,
                "force_offload": True,
                "scheduler": "unipc",
                "riflex_freq_index": 0,
            },
        },
        "7": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["3", 0],
                "samples": ["6", 0],
                "enable_vae_tiling": False,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 128,
            },
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": prefix,
            },
        },
    }
    log.info(f"  Queuing Wan T2V: seed={seed}, frames={frames}, prefix={prefix}")
    t0 = time.time()
    pid = queue_prompt(workflow)
    log.info(f"  Prompt ID: {pid}")
    entry = wait_for_completion(pid, timeout=1200)
    elapsed = time.time() - t0
    log.info(f"  T2V complete in {elapsed:.0f}s")
    return entry


# ══════════════════════════════════════════════════════════════════════════
# PHASE 3: SD 1.5 + ControlNet + LoRA pipeline
# ══════════════════════════════════════════════════════════════════════════

def load_controlnet_lora_pipeline():
    """Load SD 1.5 + ControlNet depth + Briony LoRA pipeline."""
    log.info("Loading SD 1.5 + ControlNet depth + Briony LoRA...")
    from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
    from diffusers import UniPCMultistepScheduler

    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16,
    )
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    # Load Briony LoRA
    lora_path = os.path.join(MODELS, "briony_watercolor_v1.safetensors")
    pipe.load_lora_weights(lora_path)
    log.info("  LoRA loaded: briony_watercolor_v1")

    pipe.to("cuda")
    log.info("  Pipeline ready on GPU")
    return pipe


def load_img2img_lora_pipeline():
    """Load SD 1.5 img2img + Briony LoRA pipeline (for living painting)."""
    log.info("Loading SD 1.5 img2img + Briony LoRA...")
    from diffusers import StableDiffusionImg2ImgPipeline
    from diffusers import UniPCMultistepScheduler

    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16,
        safety_checker=None,
    )
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    lora_path = os.path.join(MODELS, "briony_watercolor_v1.safetensors")
    pipe.load_lora_weights(lora_path)
    log.info("  LoRA loaded: briony_watercolor_v1")

    pipe.to("cuda")
    log.info("  Pipeline ready on GPU")
    return pipe


def extract_depth_maps(frames_pil):
    """Extract depth maps from frames using transformers DPT depth estimation."""
    log.info(f"  Extracting depth maps from {len(frames_pil)} frames...")

    # Use transformers depth-estimation pipeline (avoids controlnet_aux mediapipe issue)
    from transformers import DPTForDepthEstimation, DPTImageProcessor
    processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
    model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large", torch_dtype=torch.float32)
    model.to("cuda")
    model.eval()

    depth_maps = []
    for i, frame in enumerate(frames_pil):
        w, h = frame.size
        inputs = processor(images=frame, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = model(**inputs)
            predicted_depth = outputs.predicted_depth

        # Interpolate to original size
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=(h, w),
            mode="bicubic",
            align_corners=False,
        ).squeeze()

        # Normalize to 0-255 and convert to RGB depth map
        depth_np = prediction.cpu().numpy()
        depth_np = (depth_np - depth_np.min()) / (depth_np.max() - depth_np.min() + 1e-8)
        depth_np = (depth_np * 255).astype(np.uint8)
        depth_img = Image.fromarray(depth_np).convert("RGB")
        depth_maps.append(depth_img)

        if (i + 1) % 20 == 0:
            log.info(f"    Depth: {i+1}/{len(frames_pil)}")

    del model, processor
    gc.collect()
    torch.cuda.empty_cache()
    log.info(f"  Depth extraction complete: {len(depth_maps)} maps")
    return depth_maps


def render_controlnet_lora(pipe, depth_maps, prompt, neg_prompt, seed=42,
                           controlnet_scale=0.65, num_steps=25, guidance=7.5):
    """Render frames through ControlNet + LoRA pipeline."""
    log.info(f"  Rendering {len(depth_maps)} frames through ControlNet+LoRA (seed={seed})...")
    rendered = []
    gen = torch.Generator("cuda").manual_seed(seed)
    for i, depth in enumerate(depth_maps):
        result = pipe(
            prompt=prompt,
            negative_prompt=neg_prompt,
            image=depth,
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            controlnet_conditioning_scale=controlnet_scale,
            generator=gen,
        )
        rendered.append(result.images[0])
        if (i + 1) % 10 == 0:
            log.info(f"    Rendered: {i+1}/{len(depth_maps)}")
    log.info(f"  Rendering complete: {len(rendered)} frames")
    return rendered


# ══════════════════════════════════════════════════════════════════════════
# ITERATION 1: Morphic Resonance — Fish <-> School Oscillation
# ══════════════════════════════════════════════════════════════════════════

def iteration_1_morphic_resonance():
    log.info("\n" + "=" * 70)
    log.info("ITERATION 1: Morphic Resonance — Fish <-> School Oscillation")
    log.info("=" * 70)

    outdir_frames = os.path.join(FRAMES, "morphic_resonance")
    os.makedirs(outdir_frames, exist_ok=True)

    # Stage 1: Generate source motion with Wan T2V (3 seeds)
    log.info("\n--- Stage 1: Wan T2V source motion ---")
    if not ensure_comfyui():
        log.error("ComfyUI not available, skipping Iteration 1")
        return

    t2v_prompt = (
        "A single large silver herring fish swimming, the fish's body shimmers "
        "and fragments into dozens of smaller fish that form a school, the school "
        "swirls and contracts back into the shape of a single large fish, this "
        "cycle repeats, one becomes many becomes one, cinematic underwater"
    )

    seeds = [42, 123, 256]
    best_seed = None
    best_frames = None

    for seed in seeds:
        tag = f"morphic_s{seed}"
        log.info(f"\n  Generating Wan T2V: {tag}")
        try:
            entry = wan_t2v(t2v_prompt, seed=seed, frames=81, prefix=tag)
            frames = collect_comfyui_frames(entry, prefix_filter=tag)
            log.info(f"  Got {len(frames)} frames for seed {seed}")

            # Save raw source video
            if frames:
                save_video(frames, os.path.join(outdir_frames, f"source_{tag}.mp4"), fps=16)
                save_frames_disk(frames, os.path.join(outdir_frames, f"source_{tag}"))

                # Use first seed that works as best
                if best_frames is None:
                    best_seed = seed
                    best_frames = frames
                    log.info(f"  ** Best candidate so far: seed {seed}")

            del frames
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            log.error(f"  FAILED seed {seed}: {e}")
            traceback.print_exc()

    if best_frames is None:
        log.error("ITERATION 1 FAILED — no source frames generated")
        return

    # Stage 2: Extract depth maps from best seed
    log.info(f"\n--- Stage 2: Depth extraction (seed {best_seed}) ---")

    # Stop ComfyUI to free GPU memory for SD 1.5
    log.info("Stopping ComfyUI to free GPU...")
    try:
        subprocess.run(["pkill", "-f", "ComfyUI/main.py"], capture_output=True)
        time.sleep(5)
    except:
        pass
    gc.collect()
    torch.cuda.empty_cache()

    depth_maps = extract_depth_maps(best_frames)
    save_frames_disk(depth_maps, os.path.join(outdir_frames, "depth"))

    # Stage 3: Render through ControlNet + LoRA
    log.info(f"\n--- Stage 3: ControlNet + LoRA rendering ---")
    pipe = load_controlnet_lora_pipeline()

    lora_prompt = (
        "brionypenn watercolor painting of herring fish, natural history illustration, "
        "the relationship between individual and school, one and many, "
        "soft organic blue-green tones"
    )
    neg_prompt = "blurry, low quality, text, watermark, photorealistic, 3d render"

    rendered = render_controlnet_lora(
        pipe, depth_maps, lora_prompt, neg_prompt,
        seed=42, controlnet_scale=0.65, num_steps=25,
    )

    # Stage 4: Temporal smooth + assemble
    log.info(f"\n--- Stage 4: Temporal smooth + assembly ---")
    smoothed = temporal_smooth(rendered, window=9)
    save_frames_disk(smoothed, os.path.join(outdir_frames, "final"))
    save_video(smoothed, os.path.join(OUTPUT, "morphic_resonance_16fps.mp4"), fps=16)
    log.info("ITERATION 1 COMPLETE: morphic_resonance_16fps.mp4")

    # Cleanup
    del pipe, depth_maps, rendered, smoothed, best_frames
    gc.collect()
    torch.cuda.empty_cache()


# ══════════════════════════════════════════════════════════════════════════
# ITERATION 2: Orca Becoming Salmon
# ══════════════════════════════════════════════════════════════════════════

def iteration_2_orca_salmon():
    log.info("\n" + "=" * 70)
    log.info("ITERATION 2: Orca Becoming Salmon — Breach to School")
    log.info("=" * 70)

    outdir_frames = os.path.join(FRAMES, "orca_salmon")
    os.makedirs(outdir_frames, exist_ok=True)

    # Stage 1: Generate source motion with Wan T2V
    log.info("\n--- Stage 1: Wan T2V source motion ---")
    if not ensure_comfyui():
        log.error("ComfyUI not available, skipping Iteration 2")
        return

    t2v_prompt = (
        "An orca whale breaches powerfully from dark ocean water, at the peak "
        "of the breach the whale's body shatters into hundreds of silver salmon "
        "that scatter in all directions like an explosion of fish, the salmon "
        "rain down into the water and begin swimming together as a school, "
        "cinematic slow motion"
    )

    seeds = [42, 123, 256]
    best_seed = None
    best_frames = None

    for seed in seeds:
        tag = f"orca_s{seed}"
        log.info(f"\n  Generating Wan T2V: {tag}")
        try:
            entry = wan_t2v(t2v_prompt, seed=seed, frames=81, prefix=tag)
            frames = collect_comfyui_frames(entry, prefix_filter=tag)
            log.info(f"  Got {len(frames)} frames for seed {seed}")

            if frames:
                save_video(frames, os.path.join(outdir_frames, f"source_{tag}.mp4"), fps=16)
                save_frames_disk(frames, os.path.join(outdir_frames, f"source_{tag}"))

                if best_frames is None:
                    best_seed = seed
                    best_frames = frames
                    log.info(f"  ** Best candidate so far: seed {seed}")

            del frames
            gc.collect()
            torch.cuda.empty_cache()

        except Exception as e:
            log.error(f"  FAILED seed {seed}: {e}")
            traceback.print_exc()

    if best_frames is None:
        log.error("ITERATION 2 FAILED — no source frames generated")
        return

    # Stage 2: Depth extraction
    log.info(f"\n--- Stage 2: Depth extraction (seed {best_seed}) ---")
    log.info("Stopping ComfyUI to free GPU...")
    try:
        subprocess.run(["pkill", "-f", "ComfyUI/main.py"], capture_output=True)
        time.sleep(5)
    except:
        pass
    gc.collect()
    torch.cuda.empty_cache()

    depth_maps = extract_depth_maps(best_frames)
    save_frames_disk(depth_maps, os.path.join(outdir_frames, "depth"))

    # Stage 3: ControlNet + LoRA render
    log.info(f"\n--- Stage 3: ControlNet + LoRA rendering ---")
    pipe = load_controlnet_lora_pipeline()

    lora_prompt = (
        "brionypenn watercolor of orca and salmon, Pacific Northwest marine ecosystem, "
        "the predator releasing its prey, natural history illustration"
    )
    neg_prompt = "blurry, low quality, text, watermark, photorealistic, 3d render"

    rendered = render_controlnet_lora(
        pipe, depth_maps, lora_prompt, neg_prompt,
        seed=42, controlnet_scale=0.7, num_steps=25,
    )

    # Stage 4: Smooth + assemble
    log.info(f"\n--- Stage 4: Temporal smooth + assembly ---")
    smoothed = temporal_smooth(rendered, window=9)
    save_frames_disk(smoothed, os.path.join(outdir_frames, "final"))
    save_video(smoothed, os.path.join(OUTPUT, "orca_to_salmon_16fps.mp4"), fps=16)
    log.info("ITERATION 2 COMPLETE: orca_to_salmon_16fps.mp4")

    del pipe, depth_maps, rendered, smoothed, best_frames
    gc.collect()
    torch.cuda.empty_cache()


# ══════════════════════════════════════════════════════════════════════════
# ITERATION 3: Living Painting — Fixed Drift
# ══════════════════════════════════════════════════════════════════════════

def iteration_3_living_painting():
    log.info("\n" + "=" * 70)
    log.info("ITERATION 3: Living Painting — Fixed Drift Version")
    log.info("=" * 70)

    outdir_frames = os.path.join(FRAMES, "living_painting")
    os.makedirs(outdir_frames, exist_ok=True)

    # Load the source painting
    inshore_path = os.path.join(MODELS, "briony_inshore.jpg")
    if not os.path.exists(inshore_path):
        # Try alternate locations
        for alt in [
            "/home/jovyan/output/inputs/briony_inshore.jpg",
            "/home/jovyan/output/inputs/inshore.jpg",
        ]:
            if os.path.exists(alt):
                inshore_path = alt
                break
    if not os.path.exists(inshore_path):
        log.error("ITERATION 3 FAILED — no source painting found")
        return

    log.info(f"Source painting: {inshore_path}")
    original = Image.open(inshore_path).convert("RGB")

    # Resize to SD 1.5 friendly dimensions (512x768 portrait or 768x512 landscape)
    # Keep aspect ratio, fit within 768x512
    w, h = original.size
    if w > h:
        new_w, new_h = 768, 512
    else:
        new_w, new_h = 512, 768
    original = original.resize((new_w, new_h), Image.LANCZOS)
    original.save(os.path.join(outdir_frames, "original_resized.png"))
    log.info(f"  Resized to {new_w}x{new_h}")

    # Load img2img pipeline with LoRA
    pipe = load_img2img_lora_pipeline()

    lora_prompt = (
        "brionypenn watercolor painting of Salish Sea inshore habitat, "
        "kelp forest, fish, marine creatures, natural history illustration, "
        "soft organic tones, subtle movement"
    )
    neg_prompt = "blurry, low quality, text, watermark, photorealistic, 3d render, abstract, red blob, green blob"

    # Generate 300 frames — each from the ORIGINAL painting (no drift!)
    # Strength 0.08-0.15 gives subtle variation without losing composition
    log.info(f"\n--- Generating 300 frames from ORIGINAL painting ---")
    NUM_FRAMES = 300
    frames = []

    # Vary strength in a gentle sine wave for organic breathing
    for i in range(NUM_FRAMES):
        # Sine wave strength: 0.08 to 0.15
        phase = (i / NUM_FRAMES) * 2 * np.pi * 3  # 3 breathing cycles
        strength = 0.08 + 0.035 * (1 + np.sin(phase)) / 2  # 0.08 to 0.115

        gen = torch.Generator("cuda").manual_seed(i)  # Different seed each frame
        try:
            result = pipe(
                prompt=lora_prompt,
                negative_prompt=neg_prompt,
                image=original,  # ALWAYS from the original — no drift
                strength=strength,
                num_inference_steps=20,
                guidance_scale=7.0,
                generator=gen,
            )
            frames.append(result.images[0])

            if (i + 1) % 25 == 0:
                log.info(f"  Frame {i+1}/{NUM_FRAMES} (strength={strength:.3f})")
                # Save checkpoint every 25 frames
                result.images[0].save(
                    os.path.join(outdir_frames, f"raw_{i:04d}.png")
                )

        except Exception as e:
            log.error(f"  Frame {i} failed: {e}")
            # Use previous frame as fallback
            if frames:
                frames.append(frames[-1].copy())
            else:
                frames.append(original.copy())

    log.info(f"  Generated {len(frames)} raw frames")

    # Save raw frames
    save_frames_disk(frames, os.path.join(outdir_frames, "raw"))

    # Temporal Gaussian smooth
    log.info("  Applying temporal smooth (window=9)...")
    smoothed = temporal_smooth(frames, window=9)
    save_frames_disk(smoothed, os.path.join(outdir_frames, "smoothed"))

    # Assemble at both 16fps (dreamier) and 30fps
    save_video(smoothed, os.path.join(OUTPUT, "living_inshore_fixed_16fps.mp4"), fps=16)
    save_video(smoothed, os.path.join(OUTPUT, "living_inshore_fixed_30fps.mp4"), fps=30)
    log.info("ITERATION 3 COMPLETE: living_inshore_fixed_16fps.mp4, living_inshore_fixed_30fps.mp4")

    del pipe, frames, smoothed
    gc.collect()
    torch.cuda.empty_cache()


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    t_start = time.time()

    try:
        # Phase 1: Download everything
        download_models()

        # Phase 2: Iteration 1 — Morphic Resonance (Wan T2V → depth → ControlNet+LoRA)
        iteration_1_morphic_resonance()

        # Phase 3: Iteration 2 — Orca Becoming Salmon (same pipeline)
        iteration_2_orca_salmon()

        # Phase 4: Iteration 3 — Living Painting (img2img from original, no drift)
        iteration_3_living_painting()

    except Exception as e:
        log.error(f"FATAL ERROR: {e}")
        traceback.print_exc()

    elapsed = time.time() - t_start
    log.info("\n" + "=" * 70)
    log.info(f"ALL ITERATIONS COMPLETE — Total time: {elapsed/60:.1f} minutes")
    log.info("=" * 70)

    # List output files
    log.info("\nOutput files:")
    for f in sorted(os.listdir(OUTPUT)):
        fpath = os.path.join(OUTPUT, f)
        if os.path.isfile(fpath):
            size_mb = os.path.getsize(fpath) / 1e6
            log.info(f"  {f} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
