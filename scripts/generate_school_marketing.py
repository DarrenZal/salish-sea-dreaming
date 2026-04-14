"""Generate school marketing images from matched raw + LoRA video frames.

For each (raw, lora, timestamp) tuple:
  - extract cropped raw frame (timecode removed, center-square)
  - extract matching LoRA frame (already square, upscaled)
  - save photo, watercolor, and three fade blends

Output: output/school-marketing/final/
"""
import subprocess
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "output" / "school-marketing" / "final"
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 1200

MOMENTS = [
    ("H1_salmon_medium",    "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    20),
    ("H1_salmon_cathedral", "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    40),
    ("H1_salmon_dense",     "media/hero-subclips/H1_salmon_school.mp4",    "output/H1_salmon_school_production_raft_smooth.mp4",    50),
    ("H2_herring_kelp",     "media/hero-subclips/H2_herring_in_kelp.mp4",  "output/H2_herring_in_kelp_production_raft_smooth.mp4",  20),
    ("H3_kelp_cathedral",   "media/hero-subclips/H3_kelp_cathedral.mp4",   "output/H3_kelp_cathedral_production_raft_smooth.mp4",   30),
]


def extract(src: str, t: int, out_path: Path, vf: str) -> None:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(REPO / src),
         "-frames:v", "1", "-vf", vf, str(out_path)],
        check=True,
    )


for name, raw_src, lora_src, t in MOMENTS:
    print(f"[{name}] t={t}s")
    raw_path = OUT / f"{name}_photo.jpg"
    lora_path = OUT / f"{name}_watercolor.jpg"

    # Raw: crop 1020x1020 centered horizontally, offset 30px from top to drop timecode
    extract(raw_src, t, raw_path,
            f"crop=1020:1020:(iw-1020)/2:30,scale={SIZE}:{SIZE}:flags=lanczos")

    # LoRA: upscale 512x512 to target
    extract(lora_src, t, lora_path, f"scale={SIZE}:{SIZE}:flags=lanczos")

    raw_img = Image.open(raw_path).convert("RGB")
    lora_img = Image.open(lora_path).convert("RGB")

    Image.blend(raw_img, lora_img, 0.35).save(OUT / f"{name}_dream-subtle.jpg", quality=95)
    Image.blend(raw_img, lora_img, 0.50).save(OUT / f"{name}_dream-balanced.jpg", quality=95)
    Image.blend(raw_img, lora_img, 0.65).save(OUT / f"{name}_dream-watercolor.jpg", quality=95)

print(f"\nDone. Output: {OUT}")
