#!/usr/bin/env python3
"""
Salish Sea Dreaming — Overnight Experiment Suite (3E-3P)
========================================================

"We are the Salish Sea, dreaming itself awake."

Twelve experiments exploring visual techniques for the Salt Spring Spring Art Show
(April 10-26, 2026). Each experiment generates video/image sequences in Briony
Penn's watercolor style using the Briony LoRA on SD 1.5.

CORE VISION — THE HOLONIC MORPHING SYSTEM:
  "Each holon contains the whole." Scales of a fish become individual fish in a
  school. The school condenses into a salmon. Schools of salmon become a whale.
  The whale dissolves into a murmuration of birds. Birds dive and become a
  herring ball. Individual herring whose scales are fish. The cycle IS the food web.
  "The crossfades ARE the consumption."

Experiments:
  3E — THE DREAMING MIND (900 frames): Continuous latent drift. Start from a
       Briony underwater scene, add tiny noise each frame, denoise minimally.
       The bioregion's unconscious background layer. 90 seconds of pure drift.

  3F — TIDAL BREATHING (4 scenes x 360 frames): Img2img strength oscillates
       sinusoidally. Inhale = painterly abstraction. Exhale = recognizable form.
       Like the tide pulling form in and out of legibility.

  3G — ECOLOGICAL CASCADE (320 frames): The salmon-forest cycle as one continuous
       dream. Kelp -> herring -> salmon -> bear -> forest -> rain -> ocean.
       The ecological story told without cuts.

  3H — RECURSIVE "FISH OF FISH" (compositing + animation): Generate a single
       herring in Briony style, composite 200 copies arranged within a fish
       silhouette. Animate zoom: school level -> individual fish -> scales are fish.
       Then schools-as-salmon, salmon-as-whale. Holonic fractal zoom.

  3I — FULL FOOD WEB CYCLE (AnimateDiff + LoRA): 8 scenes tracing the cascade:
       herring scales -> school -> salmon -> bear -> forest -> roots -> stream ->
       herring eggs. Each scene as AnimateDiff clip, RAFT-style temporal blending.

  3J — OUTPAINTING SPIRAL (80 steps): Start from herring eggs at center, extend
       outward. Each step reveals a wider ecological context. Infinite zoom-out.

  3K — WATER CYCLE (280 frames): Rain -> stream -> river -> ocean -> evaporation
       -> clouds -> rain. The medium (watercolor) IS the subject (water).

  3L — DEPTH MORPH (3 pairs x 60 frames): MiDaS depth on two scenes, interpolate
       depth maps, render through ControlNet. Kelp forest -> cedar forest.
       Herring school -> starling murmuration. Reef -> meadow.

  3M — MANDALA BLOOM (240 frames): Ecological mandala slowly rotates and
       breathes. Glowing wheel of life turning in a dark room.

  3N — CROSS-SECTION MORPH (120 frames): Briony's 3 Central Coast paintings
       (Estuary -> Inshore -> Offshore) via depth interpolation. Shore to
       open ocean as one continuous painting.

  3O — SPECIES PORTRAITS (10 species x 100 frames): Gallery of beings.
       Each species gently animated via img2img drift. Herring, salmon, orca,
       octopus, sea star, kelp, murrelet, bear, eagle, seal.

  3P — BIOLUMINESCENCE PULSE (200 frames): Deep water scene with pulsing
       bioluminescent organisms. Darkness punctuated by living light.
       Stillness rewarded — the longer you watch, the more you see.

Target: H200 GPU, 143GB VRAM. Each experiment self-contained with error handling.
Progress logged to /home/jovyan/output/progress2.log.

Author: Darren Zal + Claude
Date: 2026-04-01
"""

import os
import sys
import time
import math
import traceback
import subprocess
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_ROOT = Path("/home/jovyan/output")
LORA_PATH = "/home/jovyan/style-transfer/briony_watercolor_v1.safetensors"
BASE_MODEL = "runwayml/stable-diffusion-v1-5"
PROGRESS_LOG = OUTPUT_ROOT / "progress2.log"

# Common generation settings
SEED = 42
GUIDANCE_SCALE = 7.5
NUM_STEPS = 30
NEGATIVE_PROMPT = (
    "photograph, photorealistic, sharp lines, digital art, 3d render, "
    "harsh shadows, blurry, deformed, ugly, text, watermark, signature"
)
BRIONY_PREFIX = "brionypenn watercolor painting, soft wet edges, natural pigment washes, ecological illustration"

# ============================================================================
# LOGGING
# ============================================================================

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(PROGRESS_LOG),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ssd-overnight")


def log_experiment_start(name, description):
    log.info("=" * 70)
    log.info(f"EXPERIMENT {name}")
    log.info(f"  {description}")
    log.info("=" * 70)


def log_experiment_end(name, elapsed, output_dir):
    log.info(f"EXPERIMENT {name} COMPLETE -- {elapsed:.1f}s ({elapsed/60:.1f}min)")
    if output_dir:
        files = list(Path(output_dir).glob("*"))
        log.info(f"  Output: {output_dir} ({len(files)} files)")
    log.info("")


# ============================================================================
# UTILITIES
# ============================================================================

def get_ffmpeg():
    """Get ffmpeg path -- try system first, then imageio_ffmpeg."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            return "ffmpeg"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        log.warning("No ffmpeg found -- video assembly will be skipped")
        return None


FFMPEG = get_ffmpeg()


def frames_to_video(frames_dir, output_path, fps=10, pattern="frame_%05d.png"):
    """Assemble PNG frames into an MP4 video."""
    if not FFMPEG:
        log.warning(f"Skipping video assembly (no ffmpeg): {output_path}")
        return False
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(fps),
        "-i", str(Path(frames_dir) / pattern),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size_mb = Path(output_path).stat().st_size / 1e6
        log.info(f"  Video: {output_path} ({size_mb:.1f} MB)")
        return True
    else:
        log.error(f"  ffmpeg error: {result.stderr[-300:]}")
        return False


def frames_to_gif(frames_dir, output_path, fps=10, pattern="frame_*.png"):
    """Assemble PNG frames into a GIF for quick preview."""
    try:
        from PIL import Image
        frames = sorted(Path(frames_dir).glob(pattern))
        if not frames:
            return False
        images = [Image.open(f).resize((384, 384)) for f in frames[:120]]
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=int(1000 / fps),
            loop=0,
        )
        size_mb = Path(output_path).stat().st_size / 1e6
        log.info(f"  GIF preview: {output_path} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        log.warning(f"  GIF creation failed: {e}")
        return False


def save_contact_sheet(images, output_path, cols=8, cell_size=256):
    """Save a grid of PIL images as a contact sheet."""
    from PIL import Image
    n = len(images)
    if n == 0:
        return
    rows = math.ceil(n / cols)
    sheet = Image.new("RGB", (cols * cell_size, rows * cell_size), "white")
    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        thumb = img.resize((cell_size, cell_size))
        sheet.paste(thumb, (c * cell_size, r * cell_size))
    sheet.save(output_path)
    log.info(f"  Contact sheet: {output_path}")


def load_pipe_img2img():
    """Load SD 1.5 img2img pipeline with Briony LoRA."""
    import torch
    from diffusers import StableDiffusionImg2ImgPipeline

    log.info("Loading SD 1.5 img2img + Briony LoRA...")
    pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    pipe.load_lora_weights(LORA_PATH)
    log.info("  Pipeline ready.")
    return pipe


def load_pipe_txt2img():
    """Load SD 1.5 txt2img pipeline with Briony LoRA."""
    import torch
    from diffusers import StableDiffusionPipeline

    log.info("Loading SD 1.5 txt2img + Briony LoRA...")
    pipe = StableDiffusionPipeline.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    pipe.load_lora_weights(LORA_PATH)
    log.info("  Pipeline ready.")
    return pipe


def load_pipe_inpaint():
    """Load SD 1.5 inpainting pipeline with Briony LoRA."""
    import torch
    from diffusers import StableDiffusionInpaintPipeline

    log.info("Loading SD 1.5 inpainting + Briony LoRA...")
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        "runwayml/stable-diffusion-inpainting", torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    try:
        pipe.load_lora_weights(LORA_PATH)
        log.info("  Inpainting pipeline + LoRA ready.")
    except Exception as e:
        log.warning(f"  LoRA load failed on inpainting model (will use without): {e}")
    return pipe


def load_pipe_controlnet_depth():
    """Load ControlNet depth pipeline with Briony LoRA."""
    import torch
    from diffusers import (
        StableDiffusionControlNetPipeline,
        ControlNetModel,
        UniPCMultistepScheduler,
    )

    log.info("Loading ControlNet (depth) + SD 1.5 + Briony LoRA...")
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/control_v11f1p_sd15_depth", torch_dtype=torch.float16
    ).to("cuda")
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        BASE_MODEL, controlnet=controlnet, torch_dtype=torch.float16, safety_checker=None
    ).to("cuda")
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LORA_PATH)
    log.info("  ControlNet pipeline ready.")
    return pipe, controlnet


def unload_pipeline(*pipes):
    """Free GPU memory by deleting pipelines."""
    import torch
    for p in pipes:
        if p is not None:
            del p
    torch.cuda.empty_cache()
    import gc
    gc.collect()
    log.info("  GPU memory cleared.")


def generate_seed_image(pipe, prompt_suffix, seed=SEED):
    """Generate a seed image from noise via high-strength img2img."""
    import torch
    from PIL import Image

    full_prompt = f"{BRIONY_PREFIX}, {prompt_suffix}"
    generator = torch.Generator(device="cuda").manual_seed(seed)
    noise_img = Image.fromarray(np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8))
    result = pipe(
        full_prompt, image=noise_img, strength=0.99,
        num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
        negative_prompt=NEGATIVE_PROMPT, generator=generator,
    ).images[0]
    return result


def load_depth_estimator():
    """Load depth estimation model -- tries DPT first, falls back to MiDaS."""
    import torch

    try:
        from transformers import DPTForDepthEstimation, DPTImageProcessor
        log.info("  Loading DPT depth estimator...")
        processor = DPTImageProcessor.from_pretrained("Intel/dpt-large")
        model = DPTForDepthEstimation.from_pretrained(
            "Intel/dpt-large", torch_dtype=torch.float16
        ).to("cuda")
        return model, processor
    except Exception:
        log.info("  Falling back to MiDaS via torch hub...")
        model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small").to("cuda").eval()
        return model, None


def estimate_depth(pil_image, depth_model, depth_processor=None):
    """Run depth estimation, return depth as numpy float32 array (H,W)."""
    import torch

    if depth_processor is not None:
        inputs = depth_processor(images=pil_image, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = depth_model(**inputs)
            depth = outputs.predicted_depth
        depth = torch.nn.functional.interpolate(
            depth.unsqueeze(1), size=(512, 512), mode="bicubic", align_corners=False
        ).squeeze()
    else:
        import torchvision.transforms as T
        transform = T.Compose([T.Resize(384), T.CenterCrop(384), T.ToTensor()])
        img_tensor = transform(pil_image).unsqueeze(0).to("cuda")
        with torch.no_grad():
            depth = depth_model(img_tensor).squeeze()
        depth = torch.nn.functional.interpolate(
            depth.unsqueeze(0).unsqueeze(0), size=(512, 512), mode="bicubic"
        ).squeeze()

    depth = depth.float()
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8) * 255
    return depth.cpu().numpy().astype(np.float32)


def depth_to_pil(depth_np):
    """Convert numpy depth array to PIL RGB image for ControlNet."""
    from PIL import Image
    return Image.fromarray(depth_np.astype(np.uint8)).convert("RGB")


# ============================================================================
# EXPERIMENT 3E: THE DREAMING MIND (900 frames)
# ============================================================================

def experiment_3e():
    """
    THE DREAMING MIND -- 900 frames of continuous latent drift.

    Start from a Briony-style underwater scene. Each frame: feed the previous
    frame back through img2img at very low strength (0.12-0.20). The image
    slowly evolves, forms dissolve and reform. Like watching watercolors bleed.

    No destination. No narrative. Just the bioregion's unconscious visual stream.
    This is the ambient background layer for the installation -- projected behind
    everything else, always drifting, always dreaming.

    900 frames at 10fps = 90 seconds of pure drift. With looping, infinite.

    The prompt drifts too: underwater -> herring -> salmon -> forest -> rain ->
    ocean -> back to underwater. The cycle completes without anyone noticing.
    """
    import torch
    from PIL import Image

    name = "3E"
    desc = "THE DREAMING MIND -- 900 frames of bioregional unconscious"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3e_dreaming"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    # Generate seed image
    log.info("  Generating seed image (deep underwater)...")
    current = generate_seed_image(
        pipe,
        "deep underwater Salish Sea, dark blue water, particles of light, "
        "kelp silhouettes in distance, bioluminescence, vast quiet depth",
        seed=SEED,
    )
    current.save(frames_dir / "frame_00000.png")
    current.save(out_dir / "seed_image.png")

    # Dream prompts -- cycle very slowly through the ecosystem
    # Each prompt holds for ~120 frames (12 seconds), blending at edges
    dream_cycle = [
        (0,   "deep underwater, dark blue, particles of light, kelp silhouettes, bioluminescence, vast quiet"),
        (120, "underwater kelp forest, dappled light, herring swimming through fronds, green and gold"),
        (240, "school of silver herring, shifting formation, light refracting through bodies, blue water"),
        (360, "salmon in green river water, gravel bottom, dappled sunlight, swimming upstream"),
        (480, "forest reflected in still water, cedars, ferns, moss, morning mist, mushrooms"),
        (600, "rain on water surface, ripples expanding, grey sky, drops falling, circles within circles"),
        (720, "ocean surface from below, silver ceiling of waves, light rays descending, bubbles rising"),
        (840, "deep underwater again, dark blue, bioluminescent plankton, the dreaming continues"),
    ]

    num_frames = 900

    def get_prompt(frame_idx):
        """Get the dream prompt for this frame -- smooth transitions."""
        prev = dream_cycle[0]
        for start, prompt in dream_cycle:
            if start <= frame_idx:
                prev = (start, prompt)
        return f"{BRIONY_PREFIX}, {prev[1]}, Salish Sea"

    log.info(f"  Generating {num_frames} dream frames (this is the long one)...")
    all_frames = [current]

    for i in range(1, num_frames):
        # Very low strength: minimal change per frame, maximum coherence
        # Breathing oscillation so the dream pulses gently
        breath = 0.02 * math.sin(2 * math.pi * i / 80)
        strength = 0.15 + breath  # Range: 0.13 - 0.17

        prompt = get_prompt(i)

        # Seed drifts very slowly -- changes every 60 frames
        frame_seed = SEED + (i // 60)
        generator = torch.Generator(device="cuda").manual_seed(frame_seed)

        # Use fewer steps for the dreaming -- 15 steps at low strength
        # is enough and keeps it fast (900 frames is a lot)
        current = pipe(
            prompt, image=current, strength=strength,
            num_inference_steps=15, guidance_scale=6.0,
            negative_prompt=NEGATIVE_PROMPT, generator=generator,
        ).images[0]

        current.save(frames_dir / f"frame_{i:05d}.png")
        all_frames.append(current)

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            remaining = (num_frames - i - 1) / rate
            log.info(
                f"    Frame {i+1}/{num_frames} -- "
                f"{rate:.1f} frames/sec, ~{remaining/60:.0f}min remaining"
            )

    # Contact sheet (every 37th frame = ~24 samples)
    step = max(1, num_frames // 24)
    save_contact_sheet(
        [all_frames[j] for j in range(0, num_frames, step)][:24],
        out_dir / "exp3e_contact_sheet.png",
    )

    frames_to_video(frames_dir, out_dir / "exp3e_dreaming_90s.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3e_dreaming_preview.gif", fps=10)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3F: TIDAL BREATHING
# ============================================================================

def experiment_3f():
    """
    TIDAL BREATHING -- The painting breathes.

    Generate a Briony-style scene. Apply img2img with strength oscillating
    sinusoidally (0.12 -> 0.50 -> 0.12) over 120-frame cycles.

    Inhale (high strength) = watercolor bleed, painterly abstraction.
    Exhale (low strength) = return to recognizable forms.

    Four scenes breathe independently: kelp cathedral, herring spawn,
    orca deep, intertidal. Each gets 3 breath cycles (360 frames = 36 sec).
    The anchor image stays the same -- it's the DEGREE of transformation
    that oscillates. The painting holds its shape but breathes.
    """
    import torch
    from PIL import Image

    name = "3F"
    desc = "TIDAL BREATHING -- paintings breathe between form and abstraction"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3f_tidal"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    scenes = [
        {
            "name": "kelp_cathedral",
            "prompt": f"{BRIONY_PREFIX}, underwater kelp forest cathedral, giant bull kelp, shafts of light, sea otter floating, Salish Sea",
            "seed": 42,
        },
        {
            "name": "herring_spawn",
            "prompt": f"{BRIONY_PREFIX}, herring spawning on eelgrass, milky water, turquoise and silver, thousands of eggs, Salish Sea spring",
            "seed": 137,
        },
        {
            "name": "orca_deep",
            "prompt": f"{BRIONY_PREFIX}, orca whale swimming in deep water, dorsal fin, black and white, dark blue ocean, J pod, Salish Sea",
            "seed": 256,
        },
        {
            "name": "intertidal",
            "prompt": f"{BRIONY_PREFIX}, intertidal zone, sea anemones, purple sea stars, barnacles, tide pools, rocky shore, Salish Sea",
            "seed": 512,
        },
    ]

    num_frames = 360
    breath_period = 120
    min_strength = 0.12
    max_strength = 0.50

    for scene in scenes:
        scene_dir = frames_dir / scene["name"]
        scene_dir.mkdir(parents=True, exist_ok=True)

        log.info(f"  Scene: {scene['name']}")

        # Generate anchor
        anchor = generate_seed_image(pipe, scene["prompt"].replace(BRIONY_PREFIX + ", ", ""), scene["seed"])
        anchor.save(out_dir / f"{scene['name']}_anchor.png")

        scene_frames = []
        for i in range(num_frames):
            phase = 2 * math.pi * i / breath_period
            strength = min_strength + (max_strength - min_strength) * (0.5 + 0.5 * math.sin(phase))

            generator = torch.Generator(device="cuda").manual_seed(SEED)
            result = pipe(
                scene["prompt"], image=anchor, strength=strength,
                num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
                negative_prompt=NEGATIVE_PROMPT, generator=generator,
            ).images[0]

            result.save(scene_dir / f"frame_{i:05d}.png")
            scene_frames.append(result)

            if (i + 1) % 60 == 0:
                log.info(f"    {scene['name']} frame {i+1}/{num_frames} -- strength={strength:.3f}")

        frames_to_video(scene_dir, out_dir / f"exp3f_{scene['name']}.mp4", fps=10)

        # One breath cycle contact sheet
        cycle_samples = [scene_frames[j] for j in range(0, 120, 5)]
        save_contact_sheet(cycle_samples, out_dir / f"exp3f_{scene['name']}_breath.png", cols=8)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3G: ECOLOGICAL CASCADE
# ============================================================================

def experiment_3g():
    """
    ECOLOGICAL CASCADE -- The salmon-forest cycle as one continuous dream.

    Prompt-scheduled generation cycling through:
      kelp -> herring -> salmon -> river -> bear -> forest -> rain -> ocean

    Same seed throughout for spatial coherence. Each phase 40 frames (4 sec).
    Transitions overlap by 10 frames where strength ramps up.
    Total: ~320 frames (32 seconds at 10fps).

    This tells THE story. Everything is connected.
    "The crossfades ARE the consumption."
    """
    import torch
    from PIL import Image

    name = "3G"
    desc = "ECOLOGICAL CASCADE -- salmon-forest cycle, the crossfades ARE the consumption"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3g_cascade"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    cascade = [
        ("01_kelp", "underwater kelp forest, giant bull kelp swaying, shafts of golden light filtering down, sea urchins, Salish Sea", 40),
        ("02_herring", "massive school of Pacific herring, silver fish in formation, underwater blue-green light, shifting shapes", 40),
        ("03_salmon", "Chinook salmon swimming upstream, powerful fish in green water, river stones, determination", 40),
        ("04_rapids", "salmon leaping up river rapids, white water, rocks, forest on banks, eagles watching from trees", 40),
        ("05_bear", "black bear catching salmon in shallow river, fish leaping, misty forest morning, water splashing", 40),
        ("06_forest_floor", "salmon carcass on forest floor, mushrooms growing, ferns, moss, nurse log, decomposition", 40),
        ("07_canopy", "ancient forest canopy, rain falling, cedars and Douglas fir, moss hanging, clouds through treetops", 40),
        ("08_estuary", "river meeting ocean, estuary, eagles and herons, eelgrass meadow, salmon fry heading to sea", 40),
    ]

    # Seed image
    log.info("  Generating seed image (kelp forest)...")
    current = generate_seed_image(pipe, cascade[0][1], SEED)

    frame_count = 0
    all_frames = []
    transition_zone = 10

    for phase_idx, (phase_name, phase_desc, phase_frames) in enumerate(cascade):
        log.info(f"  Phase {phase_idx+1}/{len(cascade)}: {phase_name}")
        phase_prompt = f"{BRIONY_PREFIX}, {phase_desc}, Salish Sea ecosystem"

        for i in range(phase_frames):
            if i < transition_zone and phase_idx > 0:
                t = i / transition_zone
                strength = 0.30 + 0.20 * t
            else:
                strength = 0.35

            generator = torch.Generator(device="cuda").manual_seed(SEED)
            current = pipe(
                phase_prompt, image=current, strength=strength,
                num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
                negative_prompt=NEGATIVE_PROMPT, generator=generator,
            ).images[0]

            current.save(frames_dir / f"frame_{frame_count:05d}.png")
            all_frames.append(current)
            frame_count += 1

        log.info(f"    {phase_name} complete -- {frame_count} total frames")

    # Contact sheet
    step = max(1, len(all_frames) // 24)
    save_contact_sheet(
        [all_frames[j] for j in range(0, len(all_frames), step)][:24],
        out_dir / "exp3g_cascade_sheet.png", cols=8,
    )

    frames_to_video(frames_dir, out_dir / "exp3g_cascade.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3g_cascade_preview.gif", fps=10)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3H: RECURSIVE "FISH OF FISH" COMPOSITING
# ============================================================================

def experiment_3h():
    """
    RECURSIVE "FISH OF FISH" -- The holonic morphing system.

    "Each holon contains the whole."

    1. Generate a single herring in Briony style (high detail, transparent bg).
    2. Create a fish-shaped silhouette mask.
    3. Composite 200+ copies of the herring arranged within the fish silhouette.
       -> A school that IS a fish.
    4. Then take that "fish-of-fish" and arrange 30 copies in a whale silhouette.
       -> A whale made of schools made of fish.
    5. Animate a zoom: whale level -> school level -> individual fish -> scales.
       Each zoom level reveals the next holonic layer.

    Also generates the inverse: a single large fish whose SCALES are tiny fish.

    This is pure compositing -- no diffusion needed for the animation, just
    for generating the source fish images. Very fast.
    """
    import torch
    from PIL import Image, ImageDraw

    name = "3H"
    desc = "RECURSIVE FISH OF FISH -- holonic zoom, each holon contains the whole"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3h_holonic"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    # -- Step 1: Generate individual species images --
    log.info("  Generating individual species images...")

    species_prompts = {
        "herring": "single Pacific herring fish, side view, silver and blue-green, detailed scales, black background, isolated fish",
        "salmon": "single Chinook salmon, side view, silver with pink spots, powerful body, black background, isolated fish",
        "orca": "single orca whale, side view, black and white, dorsal fin, powerful body, black background, isolated whale",
    }

    species_images = {}
    for sp_name, sp_prompt in species_prompts.items():
        full = f"{BRIONY_PREFIX}, {sp_prompt}"
        img = generate_seed_image(pipe, sp_prompt, seed=SEED + hash(sp_name) % 1000)
        img.save(out_dir / f"individual_{sp_name}.png")
        species_images[sp_name] = img
        log.info(f"    Generated: {sp_name}")

    unload_pipeline(pipe)

    # -- Step 2: Create silhouette masks --
    log.info("  Creating silhouette masks...")

    def create_fish_silhouette(size=512, body_ratio=0.7):
        """Create a fish-shaped mask using ellipse + tail."""
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        # Body (ellipse)
        body_w = int(size * body_ratio)
        body_h = int(size * 0.35)
        cx, cy = size // 2, size // 2
        draw.ellipse(
            [cx - body_w // 2, cy - body_h // 2, cx + body_w // 2, cy + body_h // 2],
            fill=255,
        )
        # Tail (triangle)
        tail_x = cx + body_w // 2 - 20
        tail_h = int(body_h * 0.8)
        draw.polygon(
            [(tail_x, cy), (tail_x + body_w // 4, cy - tail_h), (tail_x + body_w // 4, cy + tail_h)],
            fill=255,
        )
        # Head taper
        head_x = cx - body_w // 2
        draw.polygon(
            [(head_x, cy), (head_x - 20, cy - 10), (head_x - 20, cy + 10)],
            fill=255,
        )
        return mask

    def create_whale_silhouette(size=512):
        """Create a whale-shaped mask."""
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        # Larger, rounder body
        body_w = int(size * 0.75)
        body_h = int(size * 0.30)
        cx, cy = size // 2, size // 2
        draw.ellipse(
            [cx - body_w // 2, cy - body_h // 2, cx + body_w // 2, cy + body_h // 2],
            fill=255,
        )
        # Tail flukes
        tail_x = cx + body_w // 2 - 10
        fluke_h = int(body_h * 1.2)
        draw.polygon(
            [(tail_x, cy), (tail_x + 60, cy - fluke_h), (tail_x + 40, cy)],
            fill=255,
        )
        draw.polygon(
            [(tail_x, cy), (tail_x + 60, cy + fluke_h), (tail_x + 40, cy)],
            fill=255,
        )
        # Dorsal fin
        draw.polygon(
            [(cx - 20, cy - body_h // 2), (cx + 20, cy - body_h // 2),
             (cx + 10, cy - body_h // 2 - 40)],
            fill=255,
        )
        return mask

    fish_mask = create_fish_silhouette()
    whale_mask = create_whale_silhouette()
    fish_mask.save(out_dir / "fish_silhouette.png")
    whale_mask.save(out_dir / "whale_silhouette.png")

    # -- Step 3: Composite "fish of fish" --
    log.info("  Compositing fish-of-fish...")

    def composite_instances(source_img, silhouette_mask, num_instances=200,
                           instance_size_range=(15, 35), canvas_size=512):
        """Place many small copies of source_img within the silhouette."""
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 255))
        mask_np = np.array(silhouette_mask)

        # Get valid positions (where mask is white)
        ys, xs = np.where(mask_np > 128)
        if len(xs) == 0:
            return canvas

        rng = np.random.RandomState(SEED)
        placed = 0
        attempts = 0
        max_attempts = num_instances * 10

        while placed < num_instances and attempts < max_attempts:
            idx = rng.randint(0, len(xs))
            x, y = int(xs[idx]), int(ys[idx])
            size = rng.randint(instance_size_range[0], instance_size_range[1])

            # Random slight rotation for organic feel
            angle = rng.uniform(-15, 15)
            small_fish = source_img.resize((size, int(size * 0.6))).rotate(
                angle, expand=True, fillcolor=(0, 0, 0)
            )

            # Random opacity for depth
            alpha = rng.uniform(0.4, 1.0)

            # Paste
            paste_x = x - small_fish.width // 2
            paste_y = y - small_fish.height // 2

            if 0 <= paste_x < canvas_size - small_fish.width and \
               0 <= paste_y < canvas_size - small_fish.height:
                # Blend with alpha
                small_rgba = small_fish.convert("RGBA")
                r, g, b, a = small_rgba.split()
                a = a.point(lambda p: int(p * alpha))
                small_rgba = Image.merge("RGBA", (r, g, b, a))
                canvas.paste(small_rgba, (paste_x, paste_y), small_rgba)
                placed += 1
            attempts += 1

        log.info(f"    Placed {placed}/{num_instances} instances")
        return canvas.convert("RGB")

    # Fish made of herring
    herring_fish = composite_instances(species_images["herring"], fish_mask, num_instances=200)
    herring_fish.save(out_dir / "fish_of_herring.png")
    log.info("    Saved: fish made of herring")

    # Salmon made of herring (herring feed salmon -- the crossfade IS the consumption)
    salmon_of_herring = composite_instances(species_images["herring"], fish_mask,
                                            num_instances=150, instance_size_range=(20, 40))
    salmon_of_herring.save(out_dir / "salmon_of_herring.png")

    # Whale made of fish-of-fish
    # First make a smaller fish-of-fish image, then tile it into a whale
    small_fish_of_fish = herring_fish.resize((80, 80))
    whale_of_fish = composite_instances(small_fish_of_fish, whale_mask,
                                        num_instances=80, instance_size_range=(30, 60))
    whale_of_fish.save(out_dir / "whale_of_fish_of_herring.png")
    log.info("    Saved: whale made of fish-of-fish")

    # -- Step 4: Animated zoom through holonic levels --
    log.info("  Generating holonic zoom animation...")

    zoom_frames = 120  # 12 seconds at 10fps
    # Three levels: whale (frames 0-40), school (40-80), individual (80-120)
    levels = [
        (whale_of_fish, "Whale made of schools"),
        (herring_fish, "School made of herring"),
        (species_images["herring"], "Individual herring"),
    ]

    for i in range(zoom_frames):
        level_idx = min(i * len(levels) // zoom_frames, len(levels) - 1)
        base_img = levels[level_idx][0]

        # Progressive zoom within each level
        frames_per_level = zoom_frames // len(levels)
        local_frame = i % frames_per_level
        zoom_progress = local_frame / frames_per_level

        # Zoom: crop from center, progressively tighter
        crop_size = int(512 * (1 - 0.4 * zoom_progress))
        offset = (512 - crop_size) // 2
        cropped = base_img.crop((offset, offset, offset + crop_size, offset + crop_size))
        frame = cropped.resize((512, 512), Image.LANCZOS)

        frame.save(frames_dir / f"frame_{i:05d}.png")

    frames_to_video(frames_dir, out_dir / "exp3h_holonic_zoom.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3h_holonic_preview.gif", fps=10)

    # Master contact sheet: all holonic levels
    save_contact_sheet(
        [whale_of_fish, herring_fish, salmon_of_herring, species_images["herring"],
         species_images["salmon"], species_images["orca"]],
        out_dir / "exp3h_holonic_levels.png", cols=3, cell_size=384,
    )

    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3I: FULL FOOD WEB CYCLE (AnimateDiff)
# ============================================================================

def experiment_3i():
    """
    FULL FOOD WEB CYCLE -- 8 animated scenes tracing the cascade.

    herring scales -> school -> salmon -> bear -> forest -> roots -> stream -> herring eggs

    Each scene: generate via AnimateDiff (16 frames) if available, otherwise
    img2img drift (30 frames). Then temporally blend between clips.

    "The crossfades ARE the consumption." -- the dissolution of herring
    IS the appearance of salmon. The bear vanishes as the forest grows.
    """
    import torch

    name = "3I"
    desc = "FULL FOOD WEB CYCLE -- 8 scenes, crossfades are consumption"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3i_foodweb"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Try AnimateDiff
    use_animatediff = False
    try:
        from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler
        log.info("  Loading AnimateDiff + Briony LoRA...")
        adapter = MotionAdapter.from_pretrained("guoyww/animatediff-motion-adapter-v1-5-2")
        pipe = AnimateDiffPipeline.from_pretrained(
            BASE_MODEL, motion_adapter=adapter,
            torch_dtype=torch.float16, safety_checker=None,
        ).to("cuda")
        pipe.scheduler = DDIMScheduler.from_config(
            pipe.scheduler.config, beta_schedule="linear", clip_sample=False,
        )
        pipe.load_lora_weights(LORA_PATH)
        use_animatediff = True
        log.info("  AnimateDiff ready.")
    except Exception as e:
        log.warning(f"  AnimateDiff unavailable: {e}")
        log.info("  Using img2img drift instead.")
        pipe = load_pipe_img2img()

    food_web = [
        ("herring_scales", "extreme close-up of herring scales, iridescent silver and blue-green, each scale a tiny mirror, underwater macro", 77),
        ("herring_school", "school of Pacific herring, thousands of silver fish moving as one body, shifting formation, underwater light", 88),
        ("salmon_feeding", "Chinook salmon pursuing herring, open mouth, powerful chase, silver fish scattering, underwater action", 99),
        ("bear_catching", "black bear catching salmon in river, fish in jaws, water splashing, morning mist, primal moment", 110),
        ("forest_nourish", "salmon carcass beneath cedar tree, mushrooms and ferns growing from nutrients, decomposition feeding life", 121),
        ("root_network", "tree root systems underground, mycelium network connecting roots, cross-section view, nutrients flowing", 132),
        ("stream_flowing", "mountain stream flowing over mossy rocks to sea, salmon fry in clear water, beginning the journey", 143),
        ("herring_eggs", "herring eggs on eelgrass, tiny translucent spheres, new life beginning, turquoise water, spring spawning", 154),
    ]

    all_scene_frames = []
    global_frame = 0

    for scene_name, scene_prompt, scene_seed in food_web:
        log.info(f"  Scene: {scene_name}")
        scene_dir = out_dir / scene_name
        scene_dir.mkdir(parents=True, exist_ok=True)

        full_prompt = f"{BRIONY_PREFIX}, {scene_prompt}, Salish Sea ecosystem"
        generator = torch.Generator(device="cuda").manual_seed(scene_seed)

        if use_animatediff:
            try:
                result = pipe(
                    full_prompt,
                    negative_prompt=NEGATIVE_PROMPT,
                    num_frames=16,
                    guidance_scale=GUIDANCE_SCALE,
                    num_inference_steps=NUM_STEPS,
                    generator=generator,
                    height=512, width=512,
                )
                scene_frames = result.frames[0]
                # Repeat to get ~30 frames
                extended = []
                for repeat in range(2):
                    extended.extend(scene_frames)
                scene_frames = extended[:30]
            except Exception as e:
                log.warning(f"    AnimateDiff failed for {scene_name}: {e}, using static")
                # Generate single image and replicate
                from PIL import Image
                img = generate_seed_image(pipe, scene_prompt, scene_seed)
                scene_frames = [img] * 30
        else:
            # img2img drift
            from PIL import Image
            current = generate_seed_image(pipe, scene_prompt, scene_seed)
            scene_frames = [current]
            for fi in range(1, 30):
                strength = 0.15 + 0.04 * math.sin(2 * math.pi * fi / 15)
                gen = torch.Generator(device="cuda").manual_seed(SEED)
                current = pipe(
                    full_prompt, image=current, strength=strength,
                    num_inference_steps=20, guidance_scale=GUIDANCE_SCALE,
                    negative_prompt=NEGATIVE_PROMPT, generator=gen,
                ).images[0]
                scene_frames.append(current)

        # Save scene frames
        for fi, frame in enumerate(scene_frames):
            frame.save(scene_dir / f"frame_{fi:05d}.png")

        all_scene_frames.append(scene_frames)
        log.info(f"    {scene_name}: {len(scene_frames)} frames")

    # -- Assemble with crossfade transitions --
    log.info("  Assembling with crossfade transitions...")
    from PIL import Image

    crossfade_length = 8  # frames of overlap
    final_frames = []

    for scene_idx, scene_frames in enumerate(all_scene_frames):
        if scene_idx > 0 and len(final_frames) >= crossfade_length:
            # Crossfade: blend the end of previous scene with start of this scene
            for cf in range(crossfade_length):
                alpha = cf / crossfade_length
                prev_frame = final_frames[-(crossfade_length - cf)]
                curr_frame = scene_frames[cf]
                # Blend
                prev_np = np.array(prev_frame).astype(np.float32)
                curr_np = np.array(curr_frame).astype(np.float32)
                blended = ((1 - alpha) * prev_np + alpha * curr_np).astype(np.uint8)
                final_frames[-(crossfade_length - cf)] = Image.fromarray(blended)
            # Add remaining frames (after crossfade zone)
            final_frames.extend(scene_frames[crossfade_length:])
        else:
            final_frames.extend(scene_frames)

    # Save final assembled frames
    for fi, frame in enumerate(final_frames):
        frame.save(frames_dir / f"frame_{fi:05d}.png")

    frames_to_video(frames_dir, out_dir / "exp3i_foodweb_cycle.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3i_foodweb_preview.gif", fps=10)

    # Contact sheet: one frame per scene
    sheet_imgs = [sf[len(sf)//2] for sf in all_scene_frames]
    save_contact_sheet(sheet_imgs, out_dir / "exp3i_foodweb_scenes.png", cols=4)

    if use_animatediff:
        try:
            del adapter
        except:
            pass
    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3J: OUTPAINTING SPIRAL
# ============================================================================

def experiment_3j():
    """
    OUTPAINTING SPIRAL -- Infinite reveal.

    Start from herring eggs at the center. Each step zooms out slightly,
    masks the new edges, inpaints with content that shifts ecological context.

    Layer 0: herring eggs on eelgrass
    Layer 10: herring school
    Layer 20: kelp forest
    Layer 30: waterline (above and below)
    Layer 40: rocky shore
    Layer 50: coastal forest
    Layer 60: ancient rainforest
    Layer 70: mountain ridgeline and clouds

    80 steps, playing at 6fps = ~13 seconds of continuous zoom-out.
    """
    import torch
    from PIL import Image, ImageDraw

    name = "3J"
    desc = "OUTPAINTING SPIRAL -- infinite zoom-out from herring eggs to mountains"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3j_outpaint"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_inpaint()

    canvas_size = 512
    num_steps = 80
    zoom_factor = 0.92

    layers = [
        (0,  "herring eggs on eelgrass, underwater, turquoise light, tiny translucent eggs, new life"),
        (10, "herring school, silver fish swimming, underwater blue-green light, shifting formation"),
        (20, "kelp forest underwater, bull kelp fronds, dappled light from above, sea life"),
        (30, "waterline, split view, kelp reaching surface, sky and water meeting, liminal zone"),
        (40, "rocky shore, intertidal zone, sea stars and anemones, barnacles, tide pools"),
        (50, "coastal forest edge, cedars and shore pines, eagle perched on snag, driftwood"),
        (60, "ancient temperate rainforest, moss-covered cedars, ferns, misty, mushrooms"),
        (70, "mountain ridgeline, clouds gathering, rain beginning, Pacific coast vista"),
    ]

    def get_layer_prompt(step):
        current = layers[0]
        for start, prompt in layers:
            if start <= step:
                current = (start, prompt)
        return f"{BRIONY_PREFIX}, {current[1]}, Salish Sea ecosystem"

    # Generate center image
    log.info("  Generating center image (herring eggs)...")
    generator = torch.Generator(device="cuda").manual_seed(SEED)
    blank = Image.new("RGB", (canvas_size, canvas_size), (128, 128, 128))
    full_mask = Image.new("L", (canvas_size, canvas_size), 255)

    current = pipe(
        get_layer_prompt(0), image=blank, mask_image=full_mask,
        num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
        negative_prompt=NEGATIVE_PROMPT, generator=generator,
        height=canvas_size, width=canvas_size,
    ).images[0]
    current.save(frames_dir / "frame_00000.png")

    all_frames = [current]

    for step in range(1, num_steps + 1):
        shrunk_size = int(canvas_size * zoom_factor)
        offset = (canvas_size - shrunk_size) // 2
        shrunk = current.resize((shrunk_size, shrunk_size), Image.LANCZOS)

        new_canvas = Image.new("RGB", (canvas_size, canvas_size), (128, 128, 128))
        new_canvas.paste(shrunk, (offset, offset))

        mask = Image.new("L", (canvas_size, canvas_size), 255)
        draw = ImageDraw.Draw(mask)
        blend_margin = 8
        draw.rectangle(
            [offset + blend_margin, offset + blend_margin,
             offset + shrunk_size - blend_margin, offset + shrunk_size - blend_margin],
            fill=0,
        )

        prompt = get_layer_prompt(step)
        generator = torch.Generator(device="cuda").manual_seed(SEED + step)

        current = pipe(
            prompt, image=new_canvas, mask_image=mask,
            num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
            negative_prompt=NEGATIVE_PROMPT, generator=generator,
            height=canvas_size, width=canvas_size,
        ).images[0]

        current.save(frames_dir / f"frame_{step:05d}.png")
        all_frames.append(current)

        if step % 10 == 0:
            log.info(f"    Outpaint step {step}/{num_steps}")

    step_s = max(1, len(all_frames) // 16)
    save_contact_sheet(
        [all_frames[j] for j in range(0, len(all_frames), step_s)][:16],
        out_dir / "exp3j_outpaint_sheet.png", cols=8,
    )

    frames_to_video(frames_dir, out_dir / "exp3j_outpaint_spiral.mp4", fps=6)
    frames_to_gif(frames_dir, out_dir / "exp3j_outpaint_preview.gif", fps=6)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3K: WATER CYCLE
# ============================================================================

def experiment_3k():
    """
    WATER CYCLE -- The medium IS the subject.

    Rain -> stream -> river -> estuary -> ocean -> surface -> clouds -> rain.
    The water itself is the protagonist. Watercolor painting about water.
    Form follows medium follows meaning.

    40 frames per phase, 280 total (28 sec at 10fps).
    """
    import torch
    from PIL import Image

    name = "3K"
    desc = "WATER CYCLE -- watercolor painting water, the medium is the message"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3k_watercycle"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    phases = [
        ("rain", "rain falling on water surface, ripples expanding, each drop a circle, grey-blue sky", 40),
        ("stream", "mountain stream tumbling over mossy rocks, white water, clear pools, fallen leaves", 40),
        ("river", "wide river flowing, salmon visible in green water, gravel bars, reflections of sky and trees", 40),
        ("estuary", "river meeting ocean, mixing fresh and salt water, eelgrass swaying, herring fry, tide coming in", 40),
        ("ocean", "deep ocean water, blue-black depths, plankton drifting, vast emptiness with scattered life", 40),
        ("surface", "ocean surface from below, sunlight filtering through waves, silver undulating ceiling, bubbles rising", 40),
        ("clouds", "clouds forming over Pacific ocean, water vapor rising, billowing clouds, light breaking through, mountains below", 40),
    ]

    current = generate_seed_image(pipe, phases[0][1], SEED)
    frame_count = 0
    all_frames = []

    for phase_idx, (phase_name, phase_desc, phase_frames) in enumerate(phases):
        log.info(f"  Phase: {phase_name}")
        phase_prompt = f"{BRIONY_PREFIX}, {phase_desc}, water cycle, Salish Sea"

        for i in range(phase_frames):
            if i < 8 and phase_idx > 0:
                strength = 0.25 + 0.15 * (i / 8)
            else:
                strength = 0.30
            strength += 0.03 * math.sin(2 * math.pi * frame_count / 20)

            generator = torch.Generator(device="cuda").manual_seed(SEED)
            current = pipe(
                phase_prompt, image=current, strength=strength,
                num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
                negative_prompt=NEGATIVE_PROMPT, generator=generator,
            ).images[0]

            current.save(frames_dir / f"frame_{frame_count:05d}.png")
            all_frames.append(current)
            frame_count += 1

        log.info(f"    {phase_name} complete -- {frame_count} total frames")

    step = max(1, len(all_frames) // 21)
    save_contact_sheet(
        [all_frames[j] for j in range(0, len(all_frames), step)][:21],
        out_dir / "exp3k_watercycle_sheet.png", cols=7,
    )

    frames_to_video(frames_dir, out_dir / "exp3k_watercycle.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3k_watercycle_preview.gif", fps=10)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3L: DEPTH MORPH
# ============================================================================

def experiment_3l():
    """
    DEPTH MORPH -- Morphing entire scene structure between analogous ecosystems.

    Three pairs that reveal structural parallels:
      1. Kelp forest -> Cedar forest (vertical structures, filtering light)
      2. Herring school -> Starling murmuration (collective motion, emergence)
      3. Reef garden -> Garry oak meadow (horizontal diversity, color)

    MiDaS depth on both scenes, interpolate depth maps, render through ControlNet.
    The structural similarity between ecosystems becomes visible.
    60 frames per pair, smooth S-curve interpolation.
    """
    import torch
    from PIL import Image

    name = "3L"
    desc = "DEPTH MORPH -- kelp:cedar, herring:starlings, reef:meadow"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3l_depthmorph"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe_cn, controlnet = load_pipe_controlnet_depth()
    depth_model, depth_processor = load_depth_estimator()

    morph_pairs = [
        {
            "name": "kelp_to_cedar",
            "src_prompt": f"{BRIONY_PREFIX}, underwater kelp forest, tall swaying fronds reaching upward, dappled light filtering down, fish swimming between kelp, Salish Sea",
            "dst_prompt": f"{BRIONY_PREFIX}, ancient cedar forest, tall trees reaching upward, dappled light through canopy, birds flying between trunks, Pacific Northwest",
            "src_seed": 42,
            "dst_seed": 137,
        },
        {
            "name": "herring_to_starlings",
            "src_prompt": f"{BRIONY_PREFIX}, school of herring swimming in formation, silver bodies flowing as one, underwater blue, Salish Sea",
            "dst_prompt": f"{BRIONY_PREFIX}, murmuration of starlings, thousands of birds flowing as one in evening sky, purple and orange sunset, Pacific coast",
            "src_seed": 256,
            "dst_seed": 512,
        },
        {
            "name": "reef_to_meadow",
            "src_prompt": f"{BRIONY_PREFIX}, underwater reef garden, anemones and sea stars, colorful marine life, rocky bottom, Salish Sea",
            "dst_prompt": f"{BRIONY_PREFIX}, Garry oak meadow, wildflowers blooming, camas and shooting stars, butterflies, golden grass, Salt Spring Island",
            "src_seed": 333,
            "dst_seed": 444,
        },
    ]

    num_frames_per_morph = 60

    for pair in morph_pairs:
        log.info(f"  Morph pair: {pair['name']}")
        pair_dir = frames_dir / pair["name"]
        pair_dir.mkdir(parents=True, exist_ok=True)

        # Generate anchors
        import torch as _torch
        flat_depth = Image.new("RGB", (512, 512), (128, 128, 128))

        gen = _torch.Generator(device="cuda").manual_seed(pair["src_seed"])
        src_img = pipe_cn(
            pair["src_prompt"], image=flat_depth,
            num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
            controlnet_conditioning_scale=0.3,
            negative_prompt=NEGATIVE_PROMPT, generator=gen,
        ).images[0]
        src_img.save(out_dir / f"{pair['name']}_src.png")

        gen = _torch.Generator(device="cuda").manual_seed(pair["dst_seed"])
        dst_img = pipe_cn(
            pair["dst_prompt"], image=flat_depth,
            num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
            controlnet_conditioning_scale=0.3,
            negative_prompt=NEGATIVE_PROMPT, generator=gen,
        ).images[0]
        dst_img.save(out_dir / f"{pair['name']}_dst.png")

        src_depth = estimate_depth(src_img, depth_model, depth_processor)
        dst_depth = estimate_depth(dst_img, depth_model, depth_processor)

        pair_frames = []
        for i in range(num_frames_per_morph):
            t_linear = i / (num_frames_per_morph - 1)
            t = 0.5 - 0.5 * math.cos(math.pi * t_linear)  # S-curve

            interp_depth = (1 - t) * src_depth + t * dst_depth
            depth_img = depth_to_pil(interp_depth)

            if t < 0.3:
                prompt = pair["src_prompt"]
            elif t > 0.7:
                prompt = pair["dst_prompt"]
            else:
                prompt = f"{BRIONY_PREFIX}, transformation, one ecosystem becoming another, Salish Sea, Pacific Northwest"

            gen = _torch.Generator(device="cuda").manual_seed(SEED)
            result = pipe_cn(
                prompt, image=depth_img,
                num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
                controlnet_conditioning_scale=0.75,
                negative_prompt=NEGATIVE_PROMPT, generator=gen,
            ).images[0]

            result.save(pair_dir / f"frame_{i:05d}.png")
            pair_frames.append(result)

            if (i + 1) % 20 == 0:
                log.info(f"    {pair['name']} frame {i+1}/{num_frames_per_morph}, t={t:.3f}")

        frames_to_video(pair_dir, out_dir / f"exp3l_{pair['name']}.mp4", fps=10)
        frames_to_gif(pair_dir, out_dir / f"exp3l_{pair['name']}.gif", fps=10)

        save_contact_sheet(
            [pair_frames[j] for j in range(0, len(pair_frames), max(1, len(pair_frames)//12))][:12],
            out_dir / f"exp3l_{pair['name']}_sheet.png", cols=6,
        )

    del depth_model
    if depth_processor:
        del depth_processor
    unload_pipeline(pipe_cn, controlnet)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3M: MANDALA BLOOM
# ============================================================================

def experiment_3m():
    """
    MANDALA BLOOM -- Briony's ecological mandala comes alive.

    Generate a circular ecological mandala and make it slowly rotate and breathe.
    New forms emerge from the edges. Species cycle through the seasons.

    Visually stunning for projection: a glowing wheel of life turning in darkness.
    240 frames = 24 seconds at 10fps. One slow revolution.
    """
    import torch
    from PIL import Image

    name = "3M"
    desc = "MANDALA BLOOM -- ecological wheel of life rotating and breathing"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3m_mandala"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    num_frames = 240
    rotation_per_frame = 1.5  # Full 360 in 240 frames

    mandala_prompt = (
        f"{BRIONY_PREFIX}, circular ecological mandala, seasonal wheel of life, "
        "Salish Sea species arranged in circle, salmon, herring, orca, eagle, cedar, "
        "kelp, sea star, camas flowers, radial symmetry, illuminated manuscript style, "
        "gold and blue and green, black background"
    )

    log.info("  Generating seed mandala...")
    current = generate_seed_image(
        pipe,
        "circular ecological mandala, seasonal wheel of life, Salish Sea species in circle, "
        "salmon herring orca eagle cedar kelp, radial symmetry, illuminated manuscript, "
        "gold blue green, black background",
        seed=SEED,
    )
    current.save(out_dir / "seed_mandala.png")
    current.save(frames_dir / "frame_00000.png")

    all_frames = [current]

    for i in range(1, num_frames):
        rotated = current.rotate(-rotation_per_frame, resample=Image.BICUBIC, expand=False, fillcolor=(0, 0, 0))
        breath = 0.20 + 0.08 * math.sin(2 * math.pi * i / 60)
        generator = torch.Generator(device="cuda").manual_seed(SEED)

        current = pipe(
            mandala_prompt, image=rotated, strength=breath,
            num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
            negative_prompt=NEGATIVE_PROMPT, generator=generator,
        ).images[0]

        current.save(frames_dir / f"frame_{i:05d}.png")
        all_frames.append(current)

        if (i + 1) % 30 == 0:
            log.info(f"    Mandala frame {i+1}/{num_frames} -- rotation={rotation_per_frame*i:.0f}deg")

    step = max(1, num_frames // 16)
    save_contact_sheet(
        [all_frames[j] for j in range(0, num_frames, step)][:16],
        out_dir / "exp3m_mandala_sheet.png", cols=8,
    )

    frames_to_video(frames_dir, out_dir / "exp3m_mandala_bloom.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3m_mandala_preview.gif", fps=10)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3N: CROSS-SECTION MORPH
# ============================================================================

def experiment_3n():
    """
    CROSS-SECTION MORPH -- Briony's 3 Central Coast paintings.

    Estuary (river/forest/shore) -> Inshore (kelp/reef) -> Offshore (open ocean).
    All share the waterline cross-section structure.

    Generate intermediates via ControlNet depth interpolation + blended prompts.
    60 frames per transition, 120 total.
    """
    import torch
    from PIL import Image

    name = "3N"
    desc = "CROSS-SECTION MORPH -- Estuary to Inshore to Offshore"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3n_crosssection"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe_cn, controlnet = load_pipe_controlnet_depth()
    depth_model, depth_processor = load_depth_estimator()

    sections = [
        {
            "name": "estuary",
            "prompt": f"{BRIONY_PREFIX}, cross-section view, estuary, waterline dividing above and below, river meeting sea, bear on shore, salmon below, forest above, eelgrass meadow",
            "seed": 42,
        },
        {
            "name": "inshore",
            "prompt": f"{BRIONY_PREFIX}, cross-section view, inshore reef, waterline dividing above and below, kelp forest underwater, sea otters on surface, herring below, rocky reef",
            "seed": 137,
        },
        {
            "name": "offshore",
            "prompt": f"{BRIONY_PREFIX}, cross-section view, open ocean, waterline dividing above and below, orca deep below, seabirds above, whale spout, dark deep water",
            "seed": 256,
        },
    ]

    # Generate anchors
    log.info("  Generating 3 cross-section anchors...")
    anchors = []
    anchor_depths = []
    flat_depth = Image.new("RGB", (512, 512), (128, 128, 128))

    for sec in sections:
        gen = torch.Generator(device="cuda").manual_seed(sec["seed"])
        img = pipe_cn(
            sec["prompt"], image=flat_depth,
            num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
            controlnet_conditioning_scale=0.3,
            negative_prompt=NEGATIVE_PROMPT, generator=gen,
        ).images[0]
        img.save(out_dir / f"anchor_{sec['name']}.png")
        anchors.append(img)

        depth = estimate_depth(img, depth_model, depth_processor)
        anchor_depths.append(depth)
        log.info(f"    Anchor: {sec['name']}")

    # Morph between pairs
    transitions = [(0, 1, "estuary_to_inshore"), (1, 2, "inshore_to_offshore")]
    frames_per_transition = 60
    frame_count = 0
    all_frames = []

    for src_idx, dst_idx, trans_name in transitions:
        log.info(f"  Morphing: {trans_name}")
        src_d = anchor_depths[src_idx]
        dst_d = anchor_depths[dst_idx]

        for i in range(frames_per_transition):
            t = i / (frames_per_transition - 1)

            interp_d = (1 - t) * src_d + t * dst_d
            depth_img = depth_to_pil(interp_d)

            if t < 0.33:
                prompt = sections[src_idx]["prompt"]
            elif t < 0.67:
                prompt = f"{BRIONY_PREFIX}, cross-section view, waterline, transition between ecosystems, Salish Sea"
            else:
                prompt = sections[dst_idx]["prompt"]

            gen = torch.Generator(device="cuda").manual_seed(SEED)
            result = pipe_cn(
                prompt, image=depth_img,
                num_inference_steps=NUM_STEPS, guidance_scale=GUIDANCE_SCALE,
                controlnet_conditioning_scale=0.8,
                negative_prompt=NEGATIVE_PROMPT, generator=gen,
            ).images[0]

            result.save(frames_dir / f"frame_{frame_count:05d}.png")
            all_frames.append(result)
            frame_count += 1

            if (i + 1) % 20 == 0:
                log.info(f"    {trans_name} frame {i+1}/{frames_per_transition}")

    step = max(1, len(all_frames) // 24)
    save_contact_sheet(
        [all_frames[j] for j in range(0, len(all_frames), step)][:24],
        out_dir / "exp3n_morph_sheet.png",
    )

    frames_to_video(frames_dir, out_dir / "exp3n_crosssection_morph.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3n_crosssection_preview.gif", fps=10)

    del depth_model
    if depth_processor:
        del depth_processor
    unload_pipeline(pipe_cn, controlnet)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3O: SPECIES PORTRAITS
# ============================================================================

def experiment_3o():
    """
    SPECIES PORTRAITS -- A gallery of beings.

    10 key Salish Sea species, each gently animated via img2img drift.
    100 frames per species (10 seconds at 10fps).

    These cycle on the projection wall as a gallery of beings --
    each creature acknowledged, each form honored in Briony's watercolor style.
    """
    import torch
    from PIL import Image

    name = "3O"
    desc = "SPECIES PORTRAITS -- gallery of beings, 10 species"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3o_portraits"
    out_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    species = [
        ("pacific_herring", "Pacific herring school, hundreds of silver fish in formation, underwater blue-green light", 100),
        ("chinook_salmon", "Chinook salmon leaping upstream, powerful red fish, white water rapids, river rocks", 200),
        ("orca_jpod", "orca whale swimming, J pod, black and white, dorsal fin breaking surface, deep blue water", 300),
        ("giant_pacific_octopus", "giant Pacific octopus, eight arms flowing, coral and rock, intelligent eyes, deep water", 400),
        ("sunflower_sea_star", "sunflower sea star on reef, orange and purple, many arms, tide pool, colorful marine life", 500),
        ("bull_kelp", "bull kelp forest swaying in current, flowing fronds, underwater light, fish swimming between", 600),
        ("marbled_murrelet", "marbled murrelet diving underwater, small seabird, wings spread, chasing fish, bubbles", 700),
        ("black_bear", "black bear in shallow river with salmon in mouth, misty morning, forest background", 800),
        ("bald_eagle", "bald eagle on cedar branch, sharp eyes, white head, overlooking river, fish in talons", 900),
        ("harbour_seal", "harbour seal on rocky shore, spotted grey fur, curious dark eyes, waves lapping, kelp nearby", 1000),
    ]

    num_frames = 100  # 10 seconds per species

    for sp_name, sp_desc, sp_seed in species:
        log.info(f"  Portrait: {sp_name}")
        sp_dir = out_dir / sp_name
        sp_dir.mkdir(parents=True, exist_ok=True)

        full_prompt = f"{BRIONY_PREFIX}, {sp_desc}, Salish Sea"
        current = generate_seed_image(pipe, sp_desc, sp_seed)
        current.save(sp_dir / "frame_00000.png")

        for i in range(1, num_frames):
            strength = 0.15 + 0.05 * math.sin(2 * math.pi * i / 30)
            generator = torch.Generator(device="cuda").manual_seed(SEED)
            current = pipe(
                full_prompt, image=current, strength=strength,
                num_inference_steps=20, guidance_scale=GUIDANCE_SCALE,
                negative_prompt=NEGATIVE_PROMPT, generator=generator,
            ).images[0]
            current.save(sp_dir / f"frame_{i:05d}.png")

        frames_to_video(sp_dir, out_dir / f"exp3o_{sp_name}.mp4", fps=10)

        if (species.index((sp_name, sp_desc, sp_seed)) + 1) % 3 == 0:
            log.info(f"    {sp_name} complete")

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# EXPERIMENT 3P: BIOLUMINESCENCE PULSE
# ============================================================================

def experiment_3p():
    """
    BIOLUMINESCENCE PULSE -- Living light in darkness.

    Deep underwater scene. Bioluminescent organisms pulse in and out of
    visibility. The painting oscillates between near-black and revealing
    glowing forms -- comb jellies, dinoflagellates, deep-sea creatures.

    Stillness is rewarded. The longer you watch, the more you see.
    This IS the installation's core experience: perception as attention.

    200 frames (20 sec at 10fps). Multiple nested pulse frequencies:
    - Slow swell (80 frames = 8 sec): overall brightness
    - Medium pulse (30 frames = 3 sec): individual organisms
    - Fast flicker (8 frames): bioluminescent sparks
    """
    import torch
    from PIL import Image, ImageEnhance

    name = "3P"
    desc = "BIOLUMINESCENCE PULSE -- living light in darkness, stillness rewarded"
    log_experiment_start(name, desc)
    t0 = time.time()

    out_dir = OUTPUT_ROOT / "exp3p_biolum"
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipe_img2img()

    num_frames = 200

    # Two anchor images: dark water and bioluminescent scene
    dark_prompt = f"{BRIONY_PREFIX}, deep dark underwater, near-black ocean depths, barely visible shapes, vast darkness, abyss"
    glow_prompt = f"{BRIONY_PREFIX}, deep underwater bioluminescence, glowing comb jellies, dinoflagellate sparkle, blue-green light, living light in darkness, deep Salish Sea"

    log.info("  Generating dark anchor...")
    dark_anchor = generate_seed_image(pipe, dark_prompt.replace(BRIONY_PREFIX + ", ", ""), SEED)
    dark_anchor.save(out_dir / "dark_anchor.png")

    log.info("  Generating bioluminescent anchor...")
    glow_anchor = generate_seed_image(pipe, glow_prompt.replace(BRIONY_PREFIX + ", ", ""), SEED + 1)
    glow_anchor.save(out_dir / "glow_anchor.png")

    all_frames = []

    for i in range(num_frames):
        # Nested pulse frequencies
        slow_swell = 0.5 + 0.5 * math.sin(2 * math.pi * i / 80)       # 0-1 over 8 sec
        medium_pulse = 0.5 + 0.5 * math.sin(2 * math.pi * i / 30)     # 0-1 over 3 sec
        fast_flicker = 0.5 + 0.5 * math.sin(2 * math.pi * i / 8)      # 0-1 over 0.8 sec

        # Combined luminosity: mostly controlled by slow swell,
        # modulated by medium pulse, with fast flicker accents
        luminosity = 0.6 * slow_swell + 0.3 * medium_pulse + 0.1 * fast_flicker
        # Range: 0 to 1

        # Blend between dark and glow anchors based on luminosity
        dark_np = np.array(dark_anchor).astype(np.float32)
        glow_np = np.array(glow_anchor).astype(np.float32)
        blended_np = ((1 - luminosity) * dark_np + luminosity * glow_np).astype(np.uint8)
        blended = Image.fromarray(blended_np)

        # Apply img2img to add life and variation
        strength = 0.15 + 0.10 * luminosity  # More transformation when brighter
        prompt = glow_prompt if luminosity > 0.5 else dark_prompt
        generator = torch.Generator(device="cuda").manual_seed(SEED + (i // 20))

        result = pipe(
            prompt, image=blended, strength=strength,
            num_inference_steps=15, guidance_scale=6.0,
            negative_prompt=NEGATIVE_PROMPT, generator=generator,
        ).images[0]

        # Darken edges (vignette) for projection room feel
        result_np = np.array(result).astype(np.float32)
        h, w = result_np.shape[:2]
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / (math.sqrt(center_x**2 + center_y**2))
        vignette = np.clip(1.0 - 0.5 * dist**2, 0, 1)
        result_np = (result_np * vignette[:, :, np.newaxis]).astype(np.uint8)
        result = Image.fromarray(result_np)

        result.save(frames_dir / f"frame_{i:05d}.png")
        all_frames.append(result)

        if (i + 1) % 40 == 0:
            log.info(f"    Biolum frame {i+1}/{num_frames} -- luminosity={luminosity:.3f}")

    step = max(1, num_frames // 20)
    save_contact_sheet(
        [all_frames[j] for j in range(0, num_frames, step)][:20],
        out_dir / "exp3p_biolum_sheet.png", cols=10,
    )

    frames_to_video(frames_dir, out_dir / "exp3p_bioluminescence.mp4", fps=10)
    frames_to_gif(frames_dir, out_dir / "exp3p_biolum_preview.gif", fps=10)

    unload_pipeline(pipe)
    log_experiment_end(name, time.time() - t0, out_dir)


# ============================================================================
# MAIN -- Run all experiments with error isolation
# ============================================================================

def main():
    log.info("=" * 70)
    log.info("SALISH SEA DREAMING -- OVERNIGHT EXPERIMENT SUITE (3E-3P)")
    log.info(f"Started: {datetime.now().isoformat()}")
    log.info(f"Output: {OUTPUT_ROOT}")
    log.info(f"LoRA: {LORA_PATH}")
    log.info(f"Base model: {BASE_MODEL}")
    log.info("=" * 70)
    log.info("")
    log.info("CORE VISION: The holonic morphing system.")
    log.info("  Each holon contains the whole.")
    log.info("  The crossfades ARE the consumption.")
    log.info("  Scales -> fish -> school -> salmon -> whale -> birds -> herring -> scales.")
    log.info("")

    # Install dependencies
    log.info("Checking dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "diffusers", "transformers", "accelerate", "safetensors", "peft",
             "controlnet-aux", "opencv-python-headless", "pillow",
             "imageio-ffmpeg", "scipy"],
            capture_output=True, timeout=300,
        )
        log.info("  Dependencies OK.")
    except Exception as e:
        log.warning(f"  pip install issue (may be fine): {e}")

    # Verify GPU
    import torch
    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        log.info(f"GPU: {gpu} ({vram:.1f} GB VRAM)")
    else:
        log.error("NO CUDA GPU -- experiments will be extremely slow or fail")

    # Verify LoRA -- update module-level variable if needed
    if not Path(LORA_PATH).exists():
        log.error(f"LoRA not found at {LORA_PATH}!")
        for candidate in [
            "/home/jovyan/briony_watercolor_v1.safetensors",
            "/home/jovyan/style-transfer/models/briony_watercolor_v1.safetensors",
        ]:
            if Path(candidate).exists():
                log.info(f"  Found at {candidate}")
                globals()["LORA_PATH"] = candidate
                break

    # Experiment ordering: simpler/faster first, ControlNet+depth later,
    # AnimateDiff/inpainting last (most likely to have issues)
    experiments = [
        # --- TIER 1: img2img only, fast ---
        ("3E -- THE DREAMING MIND (900 frames)",     experiment_3e),
        ("3G -- ECOLOGICAL CASCADE (320 frames)",    experiment_3g),
        ("3K -- WATER CYCLE (280 frames)",           experiment_3k),
        ("3P -- BIOLUMINESCENCE PULSE (200 frames)", experiment_3p),
        ("3M -- MANDALA BLOOM (240 frames)",         experiment_3m),
        ("3H -- RECURSIVE FISH OF FISH (compositing)", experiment_3h),
        # --- TIER 2: img2img, more frames ---
        ("3F -- TIDAL BREATHING (4x360 frames)",     experiment_3f),
        ("3O -- SPECIES PORTRAITS (10x100 frames)",  experiment_3o),
        # --- TIER 3: ControlNet + depth estimation ---
        ("3N -- CROSS-SECTION MORPH (120 frames)",   experiment_3n),
        ("3L -- DEPTH MORPH (3x60 frames)",          experiment_3l),
        # --- TIER 4: AnimateDiff / Inpainting ---
        ("3I -- FULL FOOD WEB CYCLE (AnimateDiff)",  experiment_3i),
        ("3J -- OUTPAINTING SPIRAL (80 steps)",      experiment_3j),
    ]

    results = {}
    total_start = time.time()

    for exp_name, exp_func in experiments:
        try:
            log.info(f"\n{'#' * 70}")
            log.info(f"# STARTING: {exp_name}")
            log.info(f"{'#' * 70}\n")
            exp_start = time.time()
            exp_func()
            elapsed = time.time() - exp_start
            results[exp_name] = f"SUCCESS ({elapsed/60:.1f} min)"
            log.info(f">>> {exp_name}: SUCCESS ({elapsed/60:.1f} min)")
        except Exception as e:
            elapsed = time.time() - exp_start
            results[exp_name] = f"FAILED ({elapsed/60:.1f} min): {str(e)[:100]}"
            log.error(f">>> {exp_name}: FAILED after {elapsed/60:.1f} min")
            log.error(traceback.format_exc())
            import torch
            torch.cuda.empty_cache()
            import gc
            gc.collect()

    # Summary
    total_elapsed = time.time() - total_start
    log.info("\n" + "=" * 70)
    log.info("EXPERIMENT SUITE COMPLETE")
    log.info(f"Total time: {total_elapsed/60:.1f} min ({total_elapsed/3600:.1f} hours)")
    log.info(f"Finished: {datetime.now().isoformat()}")
    log.info("=" * 70)
    log.info("\nRESULTS:")

    successes = 0
    for exp_name, status in results.items():
        icon = "OK" if "SUCCESS" in status else "XX"
        if "SUCCESS" in status:
            successes += 1
        log.info(f"  [{icon}] {exp_name}: {status}")

    log.info(f"\n{successes}/{len(experiments)} experiments succeeded.")

    # Count output
    total_files = len(list(OUTPUT_ROOT.rglob("*.png"))) + len(list(OUTPUT_ROOT.rglob("*.mp4")))
    total_size = sum(f.stat().st_size for f in OUTPUT_ROOT.rglob("*") if f.is_file()) / 1e9
    log.info(f"Total output: {total_files} files, {total_size:.1f} GB")
    log.info(f"Output directory: {OUTPUT_ROOT}")
    log.info("")
    log.info("The Salish Sea dreams on.")


if __name__ == "__main__":
    main()
