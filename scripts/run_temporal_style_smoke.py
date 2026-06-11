#!/usr/bin/env python3
"""Run the internal temporal style-transfer smoke matrix.

This is the buildable version of:

  docs/space-center/temporal-style-smoke-runbook-2026-05-13.md

Boundary:
  Internal recipe proof only. Do not send outputs to Austin, John, sponsors,
  or venue unless Darren explicitly packages them and Austin has approved the
  relevant public outputs.

Architecture:
  1. Read the prepared 5s real-footage clips.
  2. Stylize sparse keyframes with SD 1.5 img2img + Austin LoRA.
  3. Propagate styled keyframes through the original motion using OpenCV
     optical flow warp/blend.
  4. Compile one MP4 per variant plus a manifest.

This script deliberately does not use AnimateDiff.

Local validation:
  python3 scripts/run_temporal_style_smoke.py --version v2 --lora-dir none --dry-run

TELUS/pod usage after v2 still eval passes:
  python run_temporal_style_smoke.py \\
    --version v2 \\
    --lora-dir austin-v2-lora-out \\
    --inputs-dir temporal-style-smoke-inputs \\
    --out-dir temporal-style-smoke-v2
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_INPUTS_DIR = Path("output/temporal-style-smoke-2026-05-13/inputs")
DEFAULT_OUT_DIR = Path("output/temporal-style-smoke-2026-05-13/results")
DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_NEG = (
    "watermark, text, logo, signature, stock photo, copyright, title, label, "
    "invented crest, new crest, emblem, badge, photorealistic sculpture, "
    "building, street, jersey, product photo, decorative wallpaper, pattern collapse, "
    "blurry, distorted, low quality"
)


@dataclass(frozen=True)
class Variant:
    id: str
    clip_file: str
    mode: str
    strength: float
    controlnet_scale: float | None
    prompt_subject: str
    why: str


VARIANTS = [
    Variant(
        id="A_H2_canny_lora035",
        clip_file="H2_herring_in_kelp_5s.mp4",
        mode="controlnet_canny",
        strength=0.35,
        controlnet_scale=0.55,
        prompt_subject="underwater herring and kelp, preserve fish bodies, preserve kelp fronds, subtle flowing linework",
        why="subject-preserving fish/kelp test",
    ),
    Variant(
        id="B_H2_img2img_lora035",
        clip_file="H2_herring_in_kelp_5s.mp4",
        mode="img2img",
        strength=0.35,
        controlnet_scale=None,
        prompt_subject="underwater herring and kelp, preserve fish bodies, preserve kelp fronds, subtle flowing linework",
        why="lower-structure comparison against ControlNet",
    ),
    Variant(
        id="C_H5_img2img_lora035",
        clip_file="H5_reef_garden_5s.mp4",
        mode="img2img",
        strength=0.35,
        controlnet_scale=None,
        prompt_subject="underwater reef garden texture, preserve original reef shapes and camera motion, subtle flowing linework",
        why="complex reef texture test",
    ),
    Variant(
        id="D_H8_img2img_lora025",
        clip_file="H8_milky_water_5s.mp4",
        mode="img2img",
        strength=0.25,
        controlnet_scale=None,
        prompt_subject="soft underwater milky water atmosphere, preserve original water motion, pearl-like suspended particles",
        why="subtle pearl-water atmosphere test",
    ),
]


def trigger_for(version: str) -> str:
    v = version.lower().lstrip("v")
    return f"austin_v{v}"


def prompt_for(variant: Variant, trigger: str) -> str:
    return (
        f"{trigger}, {variant.prompt_subject}, internal style-transfer test, "
        "restrained palette, clean graphic edges, breathing negative space, "
        "do not change the subject"
    )


def parse_variant_ids(value: str) -> list[str]:
    if value.lower() == "all":
        return [v.id for v in VARIANTS]
    return [part.strip() for part in value.split(",") if part.strip()]


def selected_variants(ids: Iterable[str]) -> list[Variant]:
    by_id = {variant.id: variant for variant in VARIANTS}
    out = []
    for variant_id in ids:
        if variant_id not in by_id:
            raise SystemExit(f"Unknown variant {variant_id!r}. Choices: {', '.join(by_id)}")
        out.append(by_id[variant_id])
    return out


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def load_video_frames(video_path: Path, width: int, max_frames: int | None) -> tuple[list[Any], float]:
    import cv2
    from PIL import Image

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    src_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or width
    src_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or width
    height = int(round(width * (src_h / src_w)))
    height = max(64, (height // 8) * 8)

    frames = []
    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, (width, height), interpolation=cv2.INTER_AREA)
        frames.append(Image.fromarray(frame_rgb))
        if max_frames is not None and len(frames) >= max_frames:
            break
    cap.release()

    if not frames:
        raise RuntimeError(f"No frames read from {video_path}")
    return frames, float(fps)


def keyframe_indices(num_frames: int, interval: int) -> list[int]:
    indices = list(range(0, num_frames, interval))
    if indices[-1] != num_frames - 1:
        indices.append(num_frames - 1)
    return indices


def canny_image(frame: Any) -> Any:
    import cv2
    import numpy as np
    from PIL import Image

    arr = np.array(frame.convert("RGB"))
    edges = cv2.Canny(arr, threshold1=80, threshold2=180)
    edges = np.stack([edges, edges, edges], axis=-1)
    return Image.fromarray(edges)


class StylePipes:
    def __init__(
        self,
        *,
        base: str,
        controlnet_base: str,
        lora_dir: Path,
        lora_scale: float,
        dtype_name: str,
    ) -> None:
        self.base = base
        self.controlnet_base = controlnet_base
        self.lora_dir = lora_dir
        self.lora_scale = lora_scale
        self.dtype_name = dtype_name
        self.img2img = None
        self.controlnet = None

    def _dtype(self):
        import torch

        if self.dtype_name == "bf16":
            return torch.bfloat16
        if self.dtype_name == "fp32":
            return torch.float32
        return torch.float16

    def _finish_pipe(self, pipe: Any) -> Any:
        pipe = pipe.to("cuda")
        pipe.set_progress_bar_config(disable=True)
        pipe.load_lora_weights(str(self.lora_dir))
        pipe.fuse_lora(lora_scale=self.lora_scale)
        return pipe

    def get_img2img(self) -> Any:
        if self.img2img is None:
            from diffusers import StableDiffusionImg2ImgPipeline

            print(f"[load] img2img base={self.base}", flush=True)
            pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                self.base,
                torch_dtype=self._dtype(),
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.img2img = self._finish_pipe(pipe)
        return self.img2img

    def get_controlnet(self) -> Any:
        if self.controlnet is None:
            from diffusers import ControlNetModel, StableDiffusionControlNetImg2ImgPipeline

            print(f"[load] controlnet base={self.controlnet_base}", flush=True)
            controlnet = ControlNetModel.from_pretrained(
                self.controlnet_base,
                torch_dtype=self._dtype(),
            )
            pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
                self.base,
                controlnet=controlnet,
                torch_dtype=self._dtype(),
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.controlnet = self._finish_pipe(pipe)
        return self.controlnet


def stylize_keyframes(
    *,
    variant: Variant,
    frames: list[Any],
    indices: list[int],
    pipes: StylePipes,
    prompt: str,
    neg_prompt: str,
    seed: int,
    steps: int,
    cfg: float,
) -> dict[int, Any]:
    import torch

    styled = {}
    for idx in indices:
        frame = frames[idx]
        generator = torch.Generator(device="cuda").manual_seed(seed + idx)
        print(f"  keyframe {idx:04d}: {variant.mode}", flush=True)
        with torch.inference_mode():
            if variant.mode == "controlnet_canny":
                pipe = pipes.get_controlnet()
                image = pipe(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    image=frame,
                    control_image=canny_image(frame),
                    strength=variant.strength,
                    controlnet_conditioning_scale=variant.controlnet_scale or 0.55,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                ).images[0]
            else:
                pipe = pipes.get_img2img()
                image = pipe(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    image=frame,
                    strength=variant.strength,
                    num_inference_steps=steps,
                    guidance_scale=cfg,
                    generator=generator,
                ).images[0]
        styled[idx] = image.convert("RGB")
    return styled


def warp_with_flow(source_img: Any, source_original: Any, target_original: Any) -> Any:
    import cv2
    import numpy as np
    from PIL import Image

    source_gray = cv2.cvtColor(np.array(source_original.convert("RGB")), cv2.COLOR_RGB2GRAY)
    target_gray = cv2.cvtColor(np.array(target_original.convert("RGB")), cv2.COLOR_RGB2GRAY)
    flow = cv2.calcOpticalFlowFarneback(
        source_gray,
        target_gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=25,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )
    h, w = source_gray.shape
    grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
    map_x = (grid_x - flow[:, :, 0]).astype(np.float32)
    map_y = (grid_y - flow[:, :, 1]).astype(np.float32)
    warped = cv2.remap(
        np.array(source_img.convert("RGB")),
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    return Image.fromarray(warped)


def propagate_frames(
    frames: list[Any],
    styled_keyframes: dict[int, Any],
    indices: list[int],
) -> list[Any]:
    from PIL import Image

    outputs = []
    for i, frame in enumerate(frames):
        if i in styled_keyframes:
            outputs.append(styled_keyframes[i])
            continue

        prev_idx = max(idx for idx in indices if idx < i)
        next_candidates = [idx for idx in indices if idx > i]
        next_idx = min(next_candidates) if next_candidates else prev_idx

        prev_warp = warp_with_flow(styled_keyframes[prev_idx], frames[prev_idx], frame)
        if next_idx == prev_idx:
            outputs.append(prev_warp)
            continue

        next_warp = warp_with_flow(styled_keyframes[next_idx], frames[next_idx], frame)
        alpha = (i - prev_idx) / float(next_idx - prev_idx)
        outputs.append(Image.blend(prev_warp, next_warp, alpha))
    return outputs


def save_frames(frames: list[Any], out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(out_dir / f"frame_{i:05d}.png")


def compile_video(frames_dir: Path, out_mp4: Path, fps: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            f"{fps:.6f}",
            "-i",
            str(frames_dir / "frame_%05d.png"),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(out_mp4),
        ]
    )


def make_contact_sheet(images: list[Any], out_path: Path, cols: int = 6) -> None:
    from PIL import Image, ImageDraw

    if not images:
        return
    thumb_w = 192
    thumb_h = int(round(thumb_w * images[0].height / images[0].width))
    rows = math.ceil(len(images) / cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 20)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, image in enumerate(images):
        x = (i % cols) * thumb_w
        y = (i // cols) * (thumb_h + 20)
        sheet.paste(image.resize((thumb_w, thumb_h)), (x, y))
        draw.text((x + 4, y + thumb_h + 4), f"{i}", fill=(0, 0, 0))
    sheet.save(out_path)


def run_variant(
    *,
    variant: Variant,
    args: argparse.Namespace,
    pipes: StylePipes,
    trigger: str,
) -> dict[str, Any]:
    t0 = time.time()
    clip_path = args.inputs_dir / variant.clip_file
    require_file(clip_path)
    out_dir = args.out_dir / variant.id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {variant.id}: {variant.why} ===", flush=True)
    frames, fps = load_video_frames(clip_path, args.width, args.max_frames)
    indices = keyframe_indices(len(frames), args.keyframe_interval)
    prompt = prompt_for(variant, trigger)

    styled = stylize_keyframes(
        variant=variant,
        frames=frames,
        indices=indices,
        pipes=pipes,
        prompt=prompt,
        neg_prompt=args.neg_prompt,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
    )
    keyframe_images = [styled[idx] for idx in indices]
    keyframe_dir = out_dir / "styled_keyframes"
    save_frames(keyframe_images, keyframe_dir)
    make_contact_sheet(keyframe_images, out_dir / "_styled_keyframes_sheet.jpg")

    print("  optical-flow propagation", flush=True)
    output_frames = propagate_frames(frames, styled, indices)
    frames_dir = out_dir / "propagated_frames"
    save_frames(output_frames, frames_dir)
    out_mp4 = out_dir / f"{variant.id}.mp4"
    compile_video(frames_dir, out_mp4, fps)

    elapsed = time.time() - t0
    result = {
        "variant": asdict(variant),
        "clip": str(clip_path),
        "prompt": prompt,
        "negative_prompt": args.neg_prompt,
        "frames": len(frames),
        "fps": fps,
        "keyframe_interval": args.keyframe_interval,
        "keyframes": indices,
        "output_mp4": str(out_mp4),
        "elapsed_seconds": round(elapsed, 2),
    }
    (out_dir / "_variant_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_run_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--version", required=True, help="LoRA version, e.g. v15 or v2")
    parser.add_argument("--lora-dir", required=True, type=Path)
    parser.add_argument("--inputs-dir", type=Path, default=DEFAULT_INPUTS_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--variants", default="all", help="Comma-separated variant ids or 'all'")
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--controlnet-base", default=DEFAULT_CONTROLNET)
    parser.add_argument("--width", type=int, default=768, help="Output width, height preserves aspect and rounds to /8")
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--keyframe-interval", type=int, default=12)
    parser.add_argument("--lora-scale", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--neg-prompt", default=DEFAULT_NEG)
    parser.add_argument("--dry-run", action="store_true", help="Print/write manifest; do not import GPU deps")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    variants = selected_variants(parse_variant_ids(args.variants))
    trigger = trigger_for(args.version)

    manifest = {
        "boundary": "Internal recipe proof only; not public artwork and not for Austin/sponsors/venue without explicit operator decision and Austin approval.",
        "version": args.version,
        "trigger": trigger,
        "lora_dir": str(args.lora_dir),
        "inputs_dir": str(args.inputs_dir),
        "out_dir": str(args.out_dir),
        "base": args.base,
        "controlnet_base": args.controlnet_base,
        "lora_scale": args.lora_scale,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "width": args.width,
        "max_frames": args.max_frames,
        "keyframe_interval": args.keyframe_interval,
        "negative_prompt": args.neg_prompt,
        "variants": [
            {
                **asdict(variant),
                "prompt": prompt_for(variant, trigger),
                "input_path": str(args.inputs_dir / variant.clip_file),
            }
            for variant in variants
        ],
    }

    print("=" * 72)
    print(f"temporal style smoke: version={args.version} trigger={trigger}")
    print("=" * 72)
    print(f"inputs : {args.inputs_dir}")
    print(f"out    : {args.out_dir}")
    print(f"lora   : {args.lora_dir} @ {args.lora_scale}")
    print(f"matrix : {len(variants)} variant(s)")
    for variant in variants:
        print(
            f"  {variant.id:24s} {variant.mode:16s} "
            f"strength={variant.strength} clip={variant.clip_file}"
        )

    if args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_run_manifest(args.out_dir / "_dry_run_manifest.json", manifest)
        print("\n[DRY RUN] No videos read, no model loaded, no GPU touched.")
        return 0

    if str(args.lora_dir) == "none" or not args.lora_dir.exists():
        raise SystemExit(f"LoRA dir does not exist: {args.lora_dir}")
    if not args.inputs_dir.exists():
        raise SystemExit(f"Inputs dir does not exist: {args.inputs_dir}")

    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_run_manifest(args.out_dir / "_run_manifest_planned.json", manifest)

    pipes = StylePipes(
        base=args.base,
        controlnet_base=args.controlnet_base,
        lora_dir=args.lora_dir,
        lora_scale=args.lora_scale,
        dtype_name=args.dtype,
    )

    results = []
    t0 = time.time()
    for variant in variants:
        results.append(run_variant(variant=variant, args=args, pipes=pipes, trigger=trigger))

    manifest["results"] = results
    manifest["elapsed_seconds"] = round(time.time() - t0, 2)
    write_run_manifest(args.out_dir / "_run_manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
