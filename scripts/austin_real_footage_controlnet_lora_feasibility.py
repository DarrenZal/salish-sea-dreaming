#!/usr/bin/env python3
"""Run one bounded ControlNet + Austin LoRA feasibility test on real footage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEGATIVE = (
    "watermark, text, logo, signature, caption, fake Indigenous art, invented cultural symbol, "
    "crest, clan crest, emblem, badge, mask, ceremonial object, supernatural being, new creature, "
    "new animal, extra fish, extra body, literal eye motif, face, mandala, kaleidoscope, ornate "
    "wallpaper, cartoon, anime, blurry, distorted, low quality"
)

CONSENT_TEXT = """INTERNAL ONLY — REAL FOOTAGE FEASIBILITY TEST.

No public/show use. No prompt-only generation. No Austin-like creatures, crests,
clan beings, or supernatural beings were requested.

Source structure is real salmon footage. ControlNet/Canny and low-denoise img2img
are used to preserve source motion and edges. Austin v2 LoRA, where enabled, is
tested only as a low-scale surface/light finishing layer, not as authorship of
new cultural geometry or new beings.
"""


@dataclass(frozen=True)
class Variant:
    id: str
    label: str
    lora_scale: float | None
    strength: float


VARIANTS = [
    Variant("controlnet_only_d30", "ControlNet only d=0.30", None, 0.30),
    Variant("lora025_d30", "ControlNet + LoRA 0.25 d=0.30", 0.25, 0.30),
    Variant("lora035_d30", "ControlNet + LoRA 0.35 d=0.30", 0.35, 0.30),
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, check=True)


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def load_font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def canny_image(frame: Image.Image, low: int, high: int) -> Image.Image:
    import cv2
    import numpy as np

    arr = np.array(frame.convert("RGB"))
    edges = cv2.Canny(arr, threshold1=low, threshold2=high)
    edges = np.stack([edges, edges, edges], axis=-1)
    return Image.fromarray(edges)


def load_manifest(inputs_dir: Path) -> dict[str, Any]:
    path = inputs_dir / "motion_manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def prompt_for(manifest: dict[str, Any], *, trigger: str | None) -> str:
    base = manifest.get("prompt_hint") or (
        "real underwater salmon-school footage, preserve original motion, preserve fish silhouettes, "
        "preserve water texture and source camera, subtle projection surface light, restrained finish"
    )
    if trigger:
        return f"{trigger}, {base}"
    return base


def ffmpeg_video(frames_dir: Path, out_path: Path, *, fps: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            f"{fps:.6f}",
            "-i",
            str(frames_dir / "frame_%04d.jpg"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            str(out_path),
        ]
    )


def load_small_rgb(path: Path, size: tuple[int, int] = (192, 108)):
    import numpy as np

    with Image.open(path) as image:
        image = image.convert("RGB").resize(size, Image.Resampling.BILINEAR)
        return np.asarray(image).astype("float32") / 255.0


def temporal_step_stats(paths: list[Path]) -> dict[str, Any]:
    import numpy as np

    arrays = [load_small_rgb(path) for path in paths]
    if len(arrays) < 2:
        return {"mean": 0.0, "max": 0.0, "std": 0.0}
    diffs = [float(np.mean(np.abs(arrays[idx + 1] - arrays[idx]))) for idx in range(len(arrays) - 1)]
    return {
        "mean": round(float(np.mean(diffs)), 6),
        "max": round(float(np.max(diffs)), 6),
        "std": round(float(np.std(diffs)), 6),
    }


def edge_iou_stats(source_paths: list[Path], output_paths: list[Path], *, low: int, high: int) -> dict[str, Any]:
    import cv2
    import numpy as np

    values: list[float] = []
    for source_path, output_path in zip(source_paths, output_paths):
        source = (load_small_rgb(source_path) * 255).astype("uint8")
        output = (load_small_rgb(output_path) * 255).astype("uint8")
        source_edges = cv2.Canny(source, low, high) > 0
        output_edges = cv2.Canny(output, low, high) > 0
        union = np.logical_or(source_edges, output_edges).sum()
        values.append(1.0 if union == 0 else float(np.logical_and(source_edges, output_edges).sum() / union))
    return {
        "mean": round(float(np.mean(values)), 6) if values else 0.0,
        "min": round(float(np.min(values)), 6) if values else 0.0,
        "max": round(float(np.max(values)), 6) if values else 0.0,
    }


class Renderer:
    def __init__(
        self,
        *,
        base: str,
        controlnet_base: str,
        lora_dir: Path,
        trigger: str,
        dtype_name: str,
        controlnet_scale: float,
        canny_low: int,
        canny_high: int,
        seed: int,
        steps: int,
        cfg: float,
        negative_prompt: str,
    ) -> None:
        self.base = base
        self.controlnet_base = controlnet_base
        self.lora_dir = lora_dir
        self.trigger = trigger
        self.dtype_name = dtype_name
        self.controlnet_scale = controlnet_scale
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.seed = seed
        self.steps = steps
        self.cfg = cfg
        self.negative_prompt = negative_prompt
        self.pipe = None
        self.loaded_lora_scale: float | None = None

    def dtype(self):
        import torch

        if self.dtype_name == "bf16":
            return torch.bfloat16
        if self.dtype_name == "fp32":
            return torch.float32
        return torch.float16

    def load_pipe(self):
        if self.pipe is not None:
            return self.pipe
        from diffusers import ControlNetModel, StableDiffusionControlNetImg2ImgPipeline

        print(f"[load] controlnet={self.controlnet_base}", flush=True)
        controlnet = ControlNetModel.from_pretrained(self.controlnet_base, torch_dtype=self.dtype())
        print(f"[load] base={self.base}", flush=True)
        pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
            self.base,
            controlnet=controlnet,
            torch_dtype=self.dtype(),
            safety_checker=None,
            requires_safety_checker=False,
        ).to("cuda")
        pipe.set_progress_bar_config(disable=True)
        self.pipe = pipe
        return pipe

    def set_lora(self, scale: float | None) -> None:
        pipe = self.load_pipe()
        if self.loaded_lora_scale is not None:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        if scale is None:
            return
        pipe.load_lora_weights(str(self.lora_dir))
        pipe.fuse_lora(lora_scale=scale)
        self.loaded_lora_scale = scale

    def render_frame(self, image: Image.Image, *, manifest: dict[str, Any], variant: Variant) -> Image.Image:
        import torch

        pipe = self.load_pipe()
        control = canny_image(image, self.canny_low, self.canny_high)
        prompt = prompt_for(manifest, trigger=self.trigger if variant.lora_scale is not None else None)
        generator = torch.Generator(device="cuda").manual_seed(self.seed)
        with torch.inference_mode():
            return pipe(
                prompt=prompt,
                negative_prompt=self.negative_prompt,
                image=image,
                control_image=control,
                strength=variant.strength,
                controlnet_conditioning_scale=self.controlnet_scale,
                num_inference_steps=self.steps,
                guidance_scale=self.cfg,
                generator=generator,
            ).images[0].convert("RGB")

    def close(self) -> None:
        if self.pipe is None:
            return
        if self.loaded_lora_scale is not None:
            self.pipe.unfuse_lora()
            self.pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        self.pipe = None
        try:
            import gc
            import torch

            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            pass


def build_contact_sheet(*, out_dir: Path, inputs_dir: Path, manifest: dict[str, Any], produced: list[dict[str, str]]) -> None:
    items = manifest["items"]
    step = max(1, len(items) // 8)
    samples = items[::step]
    if samples[-1] != items[-1]:
        samples.append(items[-1])
    cols = 1 + len(produced)
    thumb_w, thumb_h = 192, 108
    label_h = 36
    row_head = 150
    sheet = Image.new("RGB", (row_head + cols * thumb_w, label_h + len(samples) * thumb_h), (244, 244, 244))
    draw = ImageDraw.Draw(sheet)
    font = load_font(10)
    font_b = load_font(11, bold=True)
    labels = ["source"] + [item["label"] for item in produced]
    for col, label in enumerate(labels):
        x = row_head + col * thumb_w
        draw.text((x + 4, 6), label[:26], fill=(20, 20, 20), font=font_b)
    for row, item in enumerate(samples):
        y = label_h + row * thumb_h
        draw.text((6, y + 6), item["id"], fill=(20, 20, 20), font=font)
        paths = [inputs_dir / item["input_file"]]
        paths.extend(out_dir / product["frames_dir"] / f"{item['id']}.jpg" for product in produced)
        for col, path in enumerate(paths):
            if not path.exists():
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                x = row_head + col * thumb_w + (thumb_w - image.width) // 2
                sheet.paste(image, (x, y + (thumb_h - image.height) // 2))
    sheet.save(out_dir / "_contact_sheet.jpg", "JPEG", quality=92, optimize=True)


def build_comparison_video(*, out_dir: Path, inputs_dir: Path, manifest: dict[str, Any], produced: list[dict[str, str]]) -> None:
    compare_dir = out_dir / "comparison_frames"
    compare_dir.mkdir(exist_ok=True)
    cell_w, cell_h = 384, 216
    label_h = 30
    labels = ["source"] + [item["label"] for item in produced]
    font = load_font(14, bold=True)
    for idx, item in enumerate(manifest["items"], start=1):
        paths = [inputs_dir / item["input_file"]]
        paths.extend(out_dir / product["frames_dir"] / f"{item['id']}.jpg" for product in produced)
        canvas = Image.new("RGB", (len(paths) * cell_w, label_h + cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for col, path in enumerate(paths):
            draw.text((col * cell_w + 8, 7), labels[col][:38], fill=(15, 15, 15), font=font)
            if not path.exists():
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
                x = col * cell_w + (cell_w - image.width) // 2
                canvas.paste(image, (x, label_h + (cell_h - image.height) // 2))
        canvas.save(compare_dir / f"frame_{idx:04d}.jpg", "JPEG", quality=92)
    ffmpeg_video(compare_dir, out_dir / "comparison_source_controlnet_lora025_lora035.mp4", fps=float(manifest["fps"]))


def write_metrics(*, out_dir: Path, inputs_dir: Path, manifest: dict[str, Any], produced: list[dict[str, str]], low: int, high: int) -> dict[str, Any]:
    source_paths = [inputs_dir / item["input_file"] for item in manifest["items"]]
    source_temporal = temporal_step_stats(source_paths)
    source_mean = source_temporal["mean"] or 1.0
    metrics: dict[str, Any] = {
        "source": {"temporal_absdiff": source_temporal},
        "outputs": {},
    }
    for product in produced:
        paths = [out_dir / product["frames_dir"] / f"{item['id']}.jpg" for item in manifest["items"]]
        temporal = temporal_step_stats(paths)
        metrics["outputs"][product["id"]] = {
            "label": product["label"],
            "temporal_absdiff": temporal,
            "temporal_mean_ratio_to_source": round(float(temporal["mean"]) / float(source_mean), 4),
            "edge_iou_to_source": edge_iou_stats(source_paths, paths, low=low, high=high),
        }
    (out_dir / "_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def write_readme(*, out_dir: Path, inputs_dir: Path, manifest: dict[str, Any], run_manifest: dict[str, Any], metrics: dict[str, Any]) -> None:
    lines = [
        "# Real Salmon Footage ControlNet + Austin LoRA Feasibility",
        "",
        "Internal-only neural feasibility test. Not public/show material.",
        "",
        "No prompt-only generation was run. Source motion/edges come from real salmon footage and Canny/ControlNet.",
        "",
        "## Inputs",
        "",
        f"- Inputs dir: `{inputs_dir}`",
        f"- Source video: `{manifest.get('source_video')}`",
        f"- Source excerpt: {manifest.get('start_seconds')}s to {manifest.get('start_seconds') + manifest.get('duration_seconds')}s",
        f"- Frames: {manifest.get('frame_count')}",
        f"- FPS: {manifest.get('fps')}",
        f"- Frame size: {manifest.get('width')}x{manifest.get('height')}",
        "",
        "## Variants",
        "",
    ]
    for product in run_manifest["produced"]:
        values = metrics["outputs"].get(product["id"], {})
        edge = values.get("edge_iou_to_source", {})
        lines.append(
            f"- `{product['video']}`: {product['label']}; temporal ratio "
            f"{values.get('temporal_mean_ratio_to_source')}; edge IoU mean {edge.get('mean')}"
        )
    lines.extend(
        [
            "",
            "## Review Assets",
            "",
            "- `_contact_sheet.jpg`",
            "- `comparison_source_controlnet_lora025_lora035.mp4`",
            "- `_metrics.json`",
            "",
            "## Boundary",
            "",
            CONSENT_TEXT.strip(),
            "",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--controlnet", default=DEFAULT_CONTROLNET)
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--controlnet-scale", type=float, default=0.92)
    parser.add_argument("--canny-low", type=int, default=80)
    parser.add_argument("--canny-high", type=int, default=180)
    parser.add_argument("--seed", type=int, default=2667)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--cfg", type=float, default=5.5)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE)
    parser.add_argument("--output-prefix", default="h1_salmon_school_real_footage_cn_lora")
    parser.add_argument("--allow-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.inputs_dir)
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and not args.allow_existing:
        raise SystemExit(f"Output directory exists and is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    shutil.copy2(args.inputs_dir / "motion_manifest.json", args.out_dir / "_input_motion_manifest.json")
    planned = {
        "boundary": CONSENT_TEXT,
        "inputs_dir": str(args.inputs_dir),
        "out_dir": str(args.out_dir),
        "lora_dir": str(args.lora_dir),
        "base": args.base,
        "controlnet": args.controlnet,
        "variants": [variant.__dict__ for variant in VARIANTS],
        "controlnet_scale": args.controlnet_scale,
        "canny_low": args.canny_low,
        "canny_high": args.canny_high,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "frame_count": len(manifest["items"]),
        "fps": manifest["fps"],
        "negative_prompt": args.negative_prompt,
    }
    (args.out_dir / "_run_manifest_planned.json").write_text(json.dumps(planned, indent=2))
    if args.dry_run:
        print(json.dumps(planned, indent=2))
        return 0

    frames = [(item, Image.open(args.inputs_dir / item["input_file"]).convert("RGB")) for item in manifest["items"]]
    produced: list[dict[str, str]] = []
    started = time.time()
    renderer = Renderer(
        base=args.base,
        controlnet_base=args.controlnet,
        lora_dir=args.lora_dir,
        trigger=args.trigger,
        dtype_name=args.dtype,
        controlnet_scale=args.controlnet_scale,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
        negative_prompt=args.negative_prompt,
    )
    renderer.load_pipe()
    try:
        for variant in VARIANTS:
            print(f"[variant] {variant.label}", flush=True)
            renderer.set_lora(variant.lora_scale)
            frames_dir_name = f"frames_{variant.id}"
            frames_dir = args.out_dir / frames_dir_name
            frames_dir.mkdir(exist_ok=True)
            for item, image in frames:
                out_path = frames_dir / f"{item['id']}.jpg"
                print(f"[render] {variant.id} {item['id']}", flush=True)
                rendered = renderer.render_frame(image, manifest=manifest, variant=variant)
                rendered.save(out_path, "JPEG", quality=94, optimize=True)
            video_name = f"{safe_name(args.output_prefix)}__{variant.id}.mp4"
            ffmpeg_video(frames_dir, args.out_dir / video_name, fps=float(manifest["fps"]))
            produced.append(
                {
                    "id": variant.id,
                    "label": variant.label,
                    "frames_dir": frames_dir_name,
                    "video": video_name,
                }
            )
    finally:
        renderer.close()
        for _, image in frames:
            image.close()

    run_manifest = dict(planned)
    run_manifest.update({"produced": produced, "elapsed_seconds": round(time.time() - started, 2)})
    build_contact_sheet(out_dir=args.out_dir, inputs_dir=args.inputs_dir, manifest=manifest, produced=produced)
    build_comparison_video(out_dir=args.out_dir, inputs_dir=args.inputs_dir, manifest=manifest, produced=produced)
    metrics = write_metrics(
        out_dir=args.out_dir,
        inputs_dir=args.inputs_dir,
        manifest=manifest,
        produced=produced,
        low=args.canny_low,
        high=args.canny_high,
    )
    run_manifest["metrics_file"] = "_metrics.json"
    (args.out_dir / "_run_manifest.json").write_text(json.dumps(run_manifest, indent=2))
    write_readme(out_dir=args.out_dir, inputs_dir=args.inputs_dir, manifest=manifest, run_manifest=run_manifest, metrics=metrics)
    print(f"Done: {len(produced)} variants in {args.out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
