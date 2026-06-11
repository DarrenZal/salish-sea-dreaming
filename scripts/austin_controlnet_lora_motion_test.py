#!/usr/bin/env python3
"""Run a short ControlNet + Austin LoRA motion test on the H200 pod."""

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
DEFAULT_CANNY_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_LINEART_CONTROLNET = "lllyasviel/control_v11p_sd15_lineart"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEG = (
    "watermark, text, logo, signature, stock photo, copyright, label, caption, "
    "literal eyeball, central eye, fake crest, invented crest, emblem, badge, "
    "photorealistic, noisy texture, blurry, distorted, low quality, extra limbs, "
    "kaleidoscope, mandala, decorative wallpaper, new creature, invented animal"
)


CONSENT_TEXT = """INTERNAL ONLY — PENDING AUSTIN PER-OUTPUT APPROVAL.

Output set: Austin-derived ControlNet + Austin v2 LoRA motion test.

Source inputs are internal deterministic morph frames derived from Austin source
files. Generated outputs are NOT Austin Harry artwork and are NOT approved
public/show material.

Purpose: evaluate temporal flicker, edge stability, primitive legibility, and
whether low-scale LoRA acts as atmospheric finish rather than generated new
Austin art.

Do not share with Austin, Pravin externally, sponsors, venue, social media, or
public audiences without an explicit operator decision and Austin's per-output
approval.
"""


@dataclass(frozen=True)
class Variant:
    id: str
    label: str
    lora_scale: float
    strength: float


@dataclass(frozen=True)
class ControlMode:
    id: str
    label: str
    controlnet_base: str


VARIANTS = [
    Variant(id="default_lora035_d30", label="default LoRA 0.35 d=0.30", lora_scale=0.35, strength=0.30),
    Variant(id="safer_lora025_d30", label="safer LoRA 0.25 d=0.30", lora_scale=0.25, strength=0.30),
]


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def canny_image(frame: Image.Image, low: int, high: int) -> Image.Image:
    import cv2
    import numpy as np

    arr = np.array(frame.convert("RGB"))
    edges = cv2.Canny(arr, threshold1=low, threshold2=high)
    edges = np.stack([edges, edges, edges], axis=-1)
    return Image.fromarray(edges)


def load_lineart_detector():
    from controlnet_aux import LineartDetector

    return LineartDetector.from_pretrained("lllyasviel/Annotators")


def prompt_for(item: dict[str, Any], *, trigger: str) -> str:
    hint = item.get("prompt_hint") or "Raven Sun to Cosmic Sun deterministic morph"
    return (
        f"{trigger}, {hint}, preserve original composition, preserve motion continuity, "
        "preserve circle oval crescent trigon forms, preserve clean line boundaries, "
        "flat color fields, restrained palette, subtle atmospheric style pass"
    )


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


class ModeRunner:
    def __init__(
        self,
        *,
        mode: ControlMode,
        base: str,
        lora_dir: Path,
        trigger: str,
        dtype_name: str,
        controlnet_scale: float,
        canny_low: int,
        canny_high: int,
        seed: int,
        steps: int,
        cfg: float,
        neg_prompt: str,
    ) -> None:
        self.mode = mode
        self.base = base
        self.lora_dir = lora_dir
        self.trigger = trigger
        self.dtype_name = dtype_name
        self.controlnet_scale = controlnet_scale
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.seed = seed
        self.steps = steps
        self.cfg = cfg
        self.neg_prompt = neg_prompt
        self.pipe = None
        self.lineart_detector = None
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

        print(f"[load] mode={self.mode.id} controlnet={self.mode.controlnet_base}", flush=True)
        controlnet = ControlNetModel.from_pretrained(
            self.mode.controlnet_base,
            torch_dtype=self.dtype(),
        )
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

    def set_lora(self, scale: float) -> None:
        pipe = self.load_pipe()
        if self.loaded_lora_scale == scale:
            return
        if self.loaded_lora_scale is not None:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        pipe.load_lora_weights(str(self.lora_dir))
        pipe.fuse_lora(lora_scale=scale)
        self.loaded_lora_scale = scale

    def control_image(self, image: Image.Image) -> Image.Image:
        if self.mode.id == "canny":
            return canny_image(image, self.canny_low, self.canny_high).resize(image.size, Image.Resampling.LANCZOS)
        if self.mode.id == "lineart":
            if self.lineart_detector is None:
                self.lineart_detector = load_lineart_detector()
            control = self.lineart_detector(image.convert("RGB")).convert("RGB")
            return control.resize(image.size, Image.Resampling.LANCZOS)
        raise ValueError(f"Unknown control mode: {self.mode.id}")

    def render_frame(self, item: dict[str, Any], image: Image.Image, variant: Variant) -> Image.Image:
        import torch

        pipe = self.load_pipe()
        control = self.control_image(image)
        prompt = prompt_for(item, trigger=self.trigger)
        # Re-seed each frame with the same seed to reduce frame-to-frame noise drift.
        generator = torch.Generator(device="cuda").manual_seed(self.seed)
        with torch.inference_mode():
            return pipe(
                prompt=prompt,
                negative_prompt=self.neg_prompt,
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
        self.pipe = None
        self.lineart_detector = None
        try:
            import gc
            import torch

            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            pass


def load_manifest(inputs_dir: Path) -> dict[str, Any]:
    path = inputs_dir / "motion_manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def ffmpeg_video(frames_dir: Path, out_path: Path, *, fps: float) -> None:
    subprocess.run(
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
        ],
        check=True,
    )


def load_small_rgb(path: Path, size: int = 192):
    import numpy as np

    with Image.open(path) as image:
        image = image.convert("RGB")
        image = image.resize((size, size), Image.Resampling.BILINEAR)
        return np.asarray(image).astype("float32") / 255.0


def frame_paths_for_sequence(
    *,
    frames_dir: Path,
    manifest: dict[str, Any],
    source: bool = False,
) -> list[Path]:
    paths: list[Path] = []
    for item in manifest["items"]:
        if source:
            paths.append(frames_dir / item["input_file"])
        else:
            paths.append(frames_dir / f"{item['id']}.jpg")
    return paths


def temporal_step_stats(paths: list[Path]) -> dict[str, Any]:
    import numpy as np

    arrays = [load_small_rgb(path) for path in paths]
    if len(arrays) < 2:
        return {"mean": 0.0, "max": 0.0, "std": 0.0, "per_step": []}
    diffs = [
        float(np.mean(np.abs(arrays[index + 1] - arrays[index])))
        for index in range(len(arrays) - 1)
    ]
    return {
        "mean": round(float(np.mean(diffs)), 6),
        "max": round(float(np.max(diffs)), 6),
        "std": round(float(np.std(diffs)), 6),
        "per_step": [round(value, 6) for value in diffs],
    }


def edge_iou_stats(source_paths: list[Path], output_paths: list[Path], *, low: int, high: int) -> dict[str, Any]:
    try:
        import cv2
        import numpy as np
    except Exception as exc:
        return {"available": False, "reason": repr(exc)}

    values: list[float] = []
    for source_path, output_path in zip(source_paths, output_paths):
        source = (load_small_rgb(source_path) * 255).astype("uint8")
        output = (load_small_rgb(output_path) * 255).astype("uint8")
        source_edges = cv2.Canny(source, low, high) > 0
        output_edges = cv2.Canny(output, low, high) > 0
        union = np.logical_or(source_edges, output_edges).sum()
        if union == 0:
            values.append(1.0)
            continue
        inter = np.logical_and(source_edges, output_edges).sum()
        values.append(float(inter / union))
    if not values:
        return {"available": True, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "available": True,
        "mean": round(float(np.mean(values)), 6),
        "min": round(float(np.min(values)), 6),
        "max": round(float(np.max(values)), 6),
    }


def build_temporal_metrics(
    *,
    out_dir: Path,
    inputs_dir: Path,
    manifest: dict[str, Any],
    produced: list[dict[str, str]],
    canny_low: int,
    canny_high: int,
) -> dict[str, Any]:
    source_paths = frame_paths_for_sequence(frames_dir=inputs_dir, manifest=manifest, source=True)
    source_steps = temporal_step_stats(source_paths)
    source_mean = float(source_steps["mean"]) or 1.0
    metrics: dict[str, Any] = {
        "source": {
            "frames": len(source_paths),
            "temporal_absdiff": source_steps,
        },
        "outputs": {},
    }
    for product in produced:
        output_paths = frame_paths_for_sequence(frames_dir=out_dir / product["frames_dir"], manifest=manifest)
        steps = temporal_step_stats(output_paths)
        metrics["outputs"][product["video"]] = {
            "label": product["label"],
            "frames": len(output_paths),
            "temporal_absdiff": steps,
            "temporal_mean_ratio_to_source": round(float(steps["mean"]) / source_mean, 4),
            "edge_iou_to_source": edge_iou_stats(source_paths, output_paths, low=canny_low, high=canny_high),
        }
    (out_dir / "_temporal_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def write_readme(
    *,
    out_dir: Path,
    manifest: dict[str, Any],
    run_manifest: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    lines = [
        "# Austin ControlNet + LoRA Motion Finishing Pass",
        "",
        "Internal technical output. Not public/show material without Austin per-output approval.",
        "",
        "## Source",
        "",
        f"- Source video: `{manifest.get('source_video', 'unknown')}`",
        f"- Frames: {run_manifest.get('frame_count')}",
        f"- FPS: {run_manifest.get('fps')}",
        "",
        "## Settings",
        "",
        f"- Base: `{run_manifest.get('base')}`",
        f"- LoRA dir: `{run_manifest.get('lora_dir')}`",
        f"- ControlNet scale: {run_manifest.get('controlnet_scale')}",
        f"- Steps: {run_manifest.get('steps')}",
        f"- CFG: {run_manifest.get('cfg')}",
        f"- Seed: {run_manifest.get('seed')}",
        "",
        "## Outputs",
        "",
    ]
    source_mean = metrics.get("source", {}).get("temporal_absdiff", {}).get("mean")
    lines.append(f"- Source temporal absdiff mean: {source_mean}")
    for product in run_manifest.get("produced", []):
        output_metrics = metrics.get("outputs", {}).get(product["video"], {})
        ratio = output_metrics.get("temporal_mean_ratio_to_source")
        edge_iou = output_metrics.get("edge_iou_to_source", {})
        lines.append(
            f"- `{product['video']}`: {product['label']}; temporal ratio {ratio}; "
            f"edge IoU mean {edge_iou.get('mean')}"
        )
    if run_manifest.get("skipped"):
        lines.extend(["", "## Skipped", ""])
        for skipped in run_manifest["skipped"]:
            lines.append(f"- {skipped}")
    lines.extend(["", "## Boundary", "", CONSENT_TEXT.strip(), ""])
    (out_dir / "README.md").write_text("\n".join(lines))


def build_review_sheet(
    *,
    out_dir: Path,
    inputs_dir: Path,
    manifest: dict[str, Any],
    produced: list[dict[str, str]],
) -> None:
    sample_items = manifest["items"][:: max(1, len(manifest["items"]) // 6)]
    if sample_items[-1] != manifest["items"][-1]:
        sample_items.append(manifest["items"][-1])

    columns = ["source"] + [f"{item['mode']} {item['variant']}" for item in produced]
    thumb = 128
    label_h = 48
    row_head = 130
    sheet = Image.new("RGB", (row_head + len(columns) * thumb, label_h + len(sample_items) * thumb), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = load_font(10)
    font_b = load_font(11, bold=True)
    for col, label in enumerate(columns):
        x = row_head + col * thumb
        draw.text((x + 4, 4), label[:22], fill=(20, 20, 20), font=font_b)
    for row, item in enumerate(sample_items):
        y = label_h + row * thumb
        draw.text((4, y + 4), item["id"], fill=(20, 20, 20), font=font_b)
        paths = [inputs_dir / item["input_file"]]
        for product in produced:
            paths.append(out_dir / product["frames_dir"] / f"{item['id']}.jpg")
        for col, path in enumerate(paths):
            if not path.exists():
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                x = row_head + col * thumb
                sheet.paste(image, (x + (thumb - image.width) // 2, y + (thumb - image.height) // 2))
    sheet.save(out_dir / "_motion_review_sheet.jpg", "JPEG", quality=92, optimize=True)


def build_comparison_video(
    *,
    out_dir: Path,
    inputs_dir: Path,
    manifest: dict[str, Any],
    produced: list[dict[str, str]],
    fps: float,
) -> None:
    compare_dir = out_dir / "comparison_frames"
    compare_dir.mkdir(exist_ok=True)
    cell = 384
    label_h = 28
    labels = ["source"] + [item["label"] for item in produced]
    font = load_font(14, bold=True)
    for frame_num, item in enumerate(manifest["items"], start=1):
        paths = [inputs_dir / item["input_file"]]
        for product in produced:
            paths.append(out_dir / product["frames_dir"] / f"{item['id']}.jpg")
        cols = len(paths)
        canvas = Image.new("RGB", (cols * cell, cell + label_h), "white")
        draw = ImageDraw.Draw(canvas)
        for col, path in enumerate(paths):
            if not path.exists():
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((cell, cell), Image.Resampling.LANCZOS)
                x = col * cell + (cell - image.width) // 2
                canvas.paste(image, (x, label_h + (cell - image.height) // 2))
            draw.text((col * cell + 8, 6), labels[col][:30], fill=(20, 20, 20), font=font)
        canvas.save(compare_dir / f"frame_{frame_num:04d}.jpg", "JPEG", quality=92)
    ffmpeg_video(compare_dir, out_dir / "comparison_source_canny_lineart.mp4", fps=fps)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--canny-controlnet", default=DEFAULT_CANNY_CONTROLNET)
    parser.add_argument("--lineart-controlnet", default=DEFAULT_LINEART_CONTROLNET)
    parser.add_argument("--control-modes", default="canny,lineart")
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--controlnet-scale", type=float, default=0.78)
    parser.add_argument("--canny-low", type=int, default=80)
    parser.add_argument("--canny-high", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--cfg", type=float, default=6.5)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEG)
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--allow-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.inputs_dir)
    fps = float(manifest.get("fps") or 12.0)
    requested_modes = {part.strip() for part in args.control_modes.split(",") if part.strip()}
    modes: list[ControlMode] = []
    if "canny" in requested_modes:
        modes.append(ControlMode("canny", "Canny", args.canny_controlnet))
    if "lineart" in requested_modes:
        modes.append(ControlMode("lineart", "Lineart", args.lineart_controlnet))

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
        "modes": [mode.__dict__ for mode in modes],
        "variants": [variant.__dict__ for variant in VARIANTS],
        "controlnet_scale": args.controlnet_scale,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "frame_count": len(manifest["items"]),
        "fps": fps,
        "output_prefix": args.output_prefix,
    }
    (args.out_dir / "_run_manifest_planned.json").write_text(json.dumps(planned, indent=2))
    if args.dry_run:
        print(json.dumps(planned, indent=2))
        return 0

    started = time.time()
    produced: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    frames = [(item, Image.open(args.inputs_dir / item["input_file"]).convert("RGB")) for item in manifest["items"]]
    for mode in modes:
        print(f"\n[mode] {mode.label}", flush=True)
        runner = ModeRunner(
            mode=mode,
            base=args.base,
            lora_dir=args.lora_dir,
            trigger=args.trigger,
            dtype_name=args.dtype,
            controlnet_scale=args.controlnet_scale,
            canny_low=args.canny_low,
            canny_high=args.canny_high,
            seed=args.seed,
            steps=args.steps,
            cfg=args.cfg,
            neg_prompt=args.negative_prompt,
        )
        try:
            runner.load_pipe()
            if mode.id == "lineart":
                runner.lineart_detector = load_lineart_detector()
        except Exception as exc:
            skipped.append({"mode": mode.id, "reason": repr(exc)})
            print(f"[skip] mode={mode.id} reason={exc!r}", flush=True)
            runner.close()
            continue
        for variant in VARIANTS:
            print(f"[variant] {mode.id} {variant.label}", flush=True)
            runner.set_lora(variant.lora_scale)
            frames_dir_name = f"frames_{mode.id}_{variant.id}"
            frames_dir = args.out_dir / frames_dir_name
            frames_dir.mkdir(exist_ok=True)
            for item, image in frames:
                out_path = frames_dir / f"{item['id']}.jpg"
                print(f"[render] {mode.id} {variant.id} {item['id']}", flush=True)
                rendered = runner.render_frame(item, image, variant)
                rendered.save(out_path, "JPEG", quality=94, optimize=True)
            prefix = args.output_prefix or safe_name(Path(str(manifest.get("source_video", "motion"))).stem)
            video_name = f"{prefix}__{mode.id}__{variant.id}.mp4"
            ffmpeg_video(frames_dir, args.out_dir / video_name, fps=fps)
            produced.append(
                {
                    "mode": mode.id,
                    "variant": variant.id,
                    "label": f"{mode.label} {variant.label}",
                    "frames_dir": frames_dir_name,
                    "video": video_name,
                }
            )
        runner.close()

    for _, image in frames:
        image.close()

    run_manifest = dict(planned)
    run_manifest.update(
        {
            "produced": produced,
            "skipped": skipped,
            "elapsed_seconds": round(time.time() - started, 2),
        }
    )
    build_review_sheet(out_dir=args.out_dir, inputs_dir=args.inputs_dir, manifest=manifest, produced=produced)
    build_comparison_video(out_dir=args.out_dir, inputs_dir=args.inputs_dir, manifest=manifest, produced=produced, fps=fps)
    metrics = build_temporal_metrics(
        out_dir=args.out_dir,
        inputs_dir=args.inputs_dir,
        manifest=manifest,
        produced=produced,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
    )
    run_manifest["temporal_metrics_file"] = "_temporal_metrics.json"
    (args.out_dir / "_run_manifest.json").write_text(json.dumps(run_manifest, indent=2))
    write_readme(out_dir=args.out_dir, manifest=manifest, run_manifest=run_manifest, metrics=metrics)
    print(f"Done: {len(produced)} videos in {args.out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
