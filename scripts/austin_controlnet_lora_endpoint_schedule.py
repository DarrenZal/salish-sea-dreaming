#!/usr/bin/env python3
"""Endpoint-constrained ControlNet + Austin LoRA finishing pass.

This is a bounded Raven->Cosmic production test: deterministic morph frames own
geometry, while SD/LoRA contributes only middle-frame finish. Endpoints are
kept exact by scheduling denoise and LoRA scale down to zero and by restoring a
destination negative-space mask during the approach to the Cosmic Sun endpoint.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CANNY_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEG = (
    "watermark, text, logo, signature, stock photo, copyright, label, caption, "
    "literal eyeball, central eye, fake crest, invented crest, emblem, badge, "
    "photorealistic, noisy texture, blurry, distorted, low quality, extra limbs, "
    "kaleidoscope, mandala, decorative wallpaper, new creature, invented animal, "
    "filled negative space, closed white gap, yellow bleed, melted linework"
)


CONSENT_TEXT = """INTERNAL ONLY — PENDING AUSTIN PER-OUTPUT APPROVAL.

Output set: endpoint-constrained Austin-derived ControlNet + Austin v2 LoRA
finishing test.

Source inputs are internal deterministic morph frames derived from Austin source
files. Generated outputs are NOT Austin Harry artwork and are NOT approved
public/show material.

Purpose: test a production principle where deterministic/vector frames own
geometry; SD/LoRA is only a finishing layer. Endpoint denoise and LoRA scale are
scheduled down to zero, ControlNet tightens near endpoints, and destination
negative-space cuts are protected from diffusion fill.

Do not share with Austin, Pravin externally, sponsors, venue, social media, or
public audiences without an explicit operator decision and Austin's per-output
approval.
"""


@dataclass(frozen=True)
class FrameSchedule:
    index: int
    frame_id: str
    endpoint_distance: int
    endpoint_t: float
    strength: float
    lora_scale: float
    lora_scale_effective: float
    controlnet_scale: float
    destination_mask_weight: float
    skip_diffusion: bool


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def smoothstep(value: float) -> float:
    x = max(0.0, min(1.0, value))
    return x * x * (3.0 - 2.0 * x)


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


def prompt_for(item: dict[str, Any], *, trigger: str) -> str:
    hint = item.get("prompt_hint") or "Raven Sun to Cosmic Sun deterministic morph"
    return (
        f"{trigger}, {hint}, preserve original composition, preserve motion continuity, "
        "preserve circle oval crescent trigon forms, preserve clean line boundaries, "
        "preserve white negative-space cuts, flat color fields, restrained palette, "
        "subtle atmospheric style pass"
    )


def load_manifest(inputs_dir: Path) -> dict[str, Any]:
    path = inputs_dir / "motion_manifest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def dtype_for(name: str):
    import torch

    if name == "bf16":
        return torch.bfloat16
    if name == "fp32":
        return torch.float32
    return torch.float16


class ScheduledRunner:
    def __init__(
        self,
        *,
        base: str,
        controlnet_base: str,
        lora_dir: Path,
        trigger: str,
        dtype_name: str,
        canny_low: int,
        canny_high: int,
        seed: int,
        steps: int,
        cfg: float,
        neg_prompt: str,
        quantize_lora_step: float,
    ) -> None:
        self.base = base
        self.controlnet_base = controlnet_base
        self.lora_dir = lora_dir
        self.trigger = trigger
        self.dtype_name = dtype_name
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.seed = seed
        self.steps = steps
        self.cfg = cfg
        self.neg_prompt = neg_prompt
        self.quantize_lora_step = quantize_lora_step
        self.pipe = None
        self.dynamic_adapter = False
        self.loaded_fused_lora_scale: float | None = None

    def load_pipe(self):
        if self.pipe is not None:
            return self.pipe
        from diffusers import ControlNetModel, StableDiffusionControlNetImg2ImgPipeline

        print(f"[load] controlnet={self.controlnet_base}", flush=True)
        controlnet = ControlNetModel.from_pretrained(
            self.controlnet_base,
            torch_dtype=dtype_for(self.dtype_name),
        )
        print(f"[load] base={self.base}", flush=True)
        pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
            self.base,
            controlnet=controlnet,
            torch_dtype=dtype_for(self.dtype_name),
            safety_checker=None,
            requires_safety_checker=False,
        ).to("cuda")
        pipe.set_progress_bar_config(disable=True)
        try:
            pipe.load_lora_weights(str(self.lora_dir), adapter_name="austin")
            pipe.set_adapters(["austin"], adapter_weights=[0.0])
            self.dynamic_adapter = True
            print("[load] LoRA loaded as dynamic adapter", flush=True)
        except Exception as exc:
            print(f"[load] dynamic LoRA adapter unavailable, will fuse by scale: {exc!r}", flush=True)
            try:
                pipe.unload_lora_weights()
            except Exception:
                pass
            self.dynamic_adapter = False
        self.pipe = pipe
        return pipe

    def effective_lora_scale(self, requested: float) -> float:
        if requested <= 0.0:
            return 0.0
        if self.dynamic_adapter or self.quantize_lora_step <= 0:
            return requested
        return round(requested / self.quantize_lora_step) * self.quantize_lora_step

    def set_lora_scale(self, requested: float) -> float:
        pipe = self.load_pipe()
        scale = self.effective_lora_scale(requested)
        if self.dynamic_adapter:
            pipe.set_adapters(["austin"], adapter_weights=[scale])
            return scale
        if self.loaded_fused_lora_scale == scale:
            return scale
        if self.loaded_fused_lora_scale is not None:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
            self.loaded_fused_lora_scale = None
        if scale > 0:
            pipe.load_lora_weights(str(self.lora_dir))
            pipe.fuse_lora(lora_scale=scale)
            self.loaded_fused_lora_scale = scale
        return scale

    def render_frame(
        self,
        *,
        item: dict[str, Any],
        image: Image.Image,
        schedule: FrameSchedule,
    ) -> Image.Image:
        import torch

        if schedule.skip_diffusion:
            return image.copy()

        pipe = self.load_pipe()
        self.set_lora_scale(schedule.lora_scale)
        control = canny_image(image, self.canny_low, self.canny_high).resize(image.size, Image.Resampling.LANCZOS)
        generator = torch.Generator(device="cuda").manual_seed(self.seed)
        with torch.inference_mode():
            rendered = pipe(
                prompt=prompt_for(item, trigger=self.trigger),
                negative_prompt=self.neg_prompt,
                image=image,
                control_image=control,
                strength=schedule.strength,
                controlnet_conditioning_scale=schedule.controlnet_scale,
                num_inference_steps=self.steps,
                guidance_scale=self.cfg,
                generator=generator,
            ).images[0].convert("RGB")
        return rendered

    def close(self) -> None:
        if self.pipe is None:
            return
        try:
            if self.loaded_fused_lora_scale is not None:
                self.pipe.unfuse_lora()
            self.pipe.unload_lora_weights()
        except Exception:
            pass
        self.pipe = None
        try:
            import gc
            import torch

            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            pass


def build_schedule(
    *,
    manifest: dict[str, Any],
    ramp_frames: int,
    mid_strength: float,
    mid_lora_scale: float,
    mid_controlnet_scale: float,
    endpoint_controlnet_scale: float,
    skip_strength_below: float,
    dest_mask_ramp_frames: int,
    runner: ScheduledRunner,
) -> list[FrameSchedule]:
    items = manifest["items"]
    n = len(items)
    out: list[FrameSchedule] = []
    dest_start = max(0, n - 1 - dest_mask_ramp_frames)
    for index, item in enumerate(items):
        endpoint_distance = min(index, n - 1 - index)
        endpoint_t = smoothstep(endpoint_distance / max(1, ramp_frames))
        strength = mid_strength * endpoint_t
        lora_scale = mid_lora_scale * endpoint_t
        controlnet_scale = endpoint_controlnet_scale + (mid_controlnet_scale - endpoint_controlnet_scale) * endpoint_t
        dest_weight = smoothstep((index - dest_start) / max(1, dest_mask_ramp_frames))
        effective = runner.effective_lora_scale(lora_scale)
        out.append(
            FrameSchedule(
                index=index,
                frame_id=item["id"],
                endpoint_distance=endpoint_distance,
                endpoint_t=round(endpoint_t, 6),
                strength=round(strength, 6),
                lora_scale=round(lora_scale, 6),
                lora_scale_effective=round(effective, 6),
                controlnet_scale=round(controlnet_scale, 6),
                destination_mask_weight=round(dest_weight, 6),
                skip_diffusion=strength < skip_strength_below,
            )
        )
    return out


def apply_destination_mask(rendered: Image.Image, source: Image.Image, mask: Image.Image, weight: float) -> Image.Image:
    if weight <= 0.0:
        return rendered
    alpha = mask.point(lambda p: int(max(0.0, min(1.0, weight)) * p))
    return Image.composite(source, rendered, alpha)


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


def temporal_step_stats(paths: list[Path]) -> dict[str, Any]:
    import numpy as np

    arrays = [load_small_rgb(path) for path in paths]
    if len(arrays) < 2:
        return {"mean": 0.0, "max": 0.0, "std": 0.0, "per_step": []}
    diffs = [float(np.mean(np.abs(arrays[i + 1] - arrays[i]))) for i in range(len(arrays) - 1)]
    return {
        "mean": round(float(np.mean(diffs)), 6),
        "max": round(float(np.max(diffs)), 6),
        "std": round(float(np.std(diffs)), 6),
        "per_step": [round(v, 6) for v in diffs],
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
        values.append(1.0 if union == 0 else float(np.logical_and(source_edges, output_edges).sum() / union))
    return {
        "available": True,
        "mean": round(float(np.mean(values)), 6),
        "min": round(float(np.min(values)), 6),
        "max": round(float(np.max(values)), 6),
    }


def masked_drift_stats(
    *,
    source_paths: list[Path],
    output_paths: list[Path],
    mask: Image.Image,
    schedule: list[FrameSchedule],
) -> dict[str, Any]:
    import numpy as np

    mask_arr = np.asarray(mask.resize((192, 192), Image.Resampling.BILINEAR)).astype("float32") / 255.0
    active = mask_arr > 0.05
    values = []
    for source_path, output_path, item in zip(source_paths, output_paths, schedule):
        if item.destination_mask_weight <= 0:
            continue
        source = load_small_rgb(source_path)
        output = load_small_rgb(output_path)
        diff = np.abs(source - output).mean(axis=2)
        values.append(
            {
                "frame": item.frame_id,
                "mask_weight": item.destination_mask_weight,
                "mean_absdiff_under_mask": round(float(diff[active].mean()), 6),
            }
        )
    if not values:
        return {"frames": 0, "mean": 0.0, "max": 0.0, "per_frame": []}
    means = [v["mean_absdiff_under_mask"] for v in values]
    return {
        "frames": len(values),
        "mean": round(float(np.mean(means)), 6),
        "max": round(float(np.max(means)), 6),
        "per_frame": values,
    }


def build_metrics(
    *,
    out_dir: Path,
    inputs_dir: Path,
    manifest: dict[str, Any],
    frames_dir: Path,
    schedule: list[FrameSchedule],
    mask: Image.Image,
    canny_low: int,
    canny_high: int,
) -> dict[str, Any]:
    source_paths = [inputs_dir / item["input_file"] for item in manifest["items"]]
    output_paths = [frames_dir / f"{item['id']}.jpg" for item in manifest["items"]]
    source_steps = temporal_step_stats(source_paths)
    output_steps = temporal_step_stats(output_paths)
    source_mean = float(source_steps["mean"]) or 1.0
    metrics = {
        "source": {
            "frames": len(source_paths),
            "temporal_absdiff": source_steps,
        },
        "scheduled_output": {
            "frames": len(output_paths),
            "temporal_absdiff": output_steps,
            "temporal_mean_ratio_to_source": round(float(output_steps["mean"]) / source_mean, 4),
            "edge_iou_to_source": edge_iou_stats(source_paths, output_paths, low=canny_low, high=canny_high),
            "destination_masked_drift_to_source": masked_drift_stats(
                source_paths=source_paths,
                output_paths=output_paths,
                mask=mask,
                schedule=schedule,
            ),
        },
    }
    (out_dir / "_endpoint_schedule_metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def build_review_sheet(
    *,
    out_dir: Path,
    inputs_dir: Path,
    manifest: dict[str, Any],
    frames_dir: Path,
    mask: Image.Image,
    schedule: list[FrameSchedule],
) -> None:
    indices = sorted({0, 12, 24, 48, 72, 78, 84, 90, len(manifest["items"]) - 1})
    indices = [idx for idx in indices if 0 <= idx < len(manifest["items"])]
    thumb = 160
    label_h = 54
    row_head = 168
    cols = ["source", "scheduled", "abs diff", "dest mask"]
    sheet = Image.new("RGB", (row_head + len(cols) * thumb, label_h + len(indices) * thumb), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = load_font(10)
    font_b = load_font(11, bold=True)
    for col, label in enumerate(cols):
        draw.text((row_head + col * thumb + 6, 6), label, fill=(20, 20, 20), font=font_b)
    mask_thumb = Image.new("RGB", (thumb, thumb), "black")
    mask_rgb = Image.merge("RGB", [mask, mask, mask])
    mask_rgb.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
    mask_thumb.paste(mask_rgb, ((thumb - mask_rgb.width) // 2, (thumb - mask_rgb.height) // 2))
    for row, idx in enumerate(indices):
        item = manifest["items"][idx]
        sched = schedule[idx]
        y = label_h + row * thumb
        draw.text((6, y + 6), item["id"], fill=(20, 20, 20), font=font_b)
        draw.text((6, y + 24), f"d={sched.strength:.3f} L={sched.lora_scale:.3f}", fill=(50, 50, 50), font=font)
        draw.text((6, y + 40), f"CN={sched.controlnet_scale:.2f} M={sched.destination_mask_weight:.2f}", fill=(50, 50, 50), font=font)
        source_path = inputs_dir / item["input_file"]
        out_path = frames_dir / f"{item['id']}.jpg"
        with Image.open(source_path) as source, Image.open(out_path) as output:
            source = source.convert("RGB")
            output = output.convert("RGB")
            diff = ImageChops.difference(source, output).resize((thumb, thumb), Image.Resampling.BILINEAR)
            diff = Image.eval(diff, lambda p: min(255, p * 4))
            for col, image in enumerate([source, output, diff]):
                image = image.copy()
                image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                sheet.paste(image, (row_head + col * thumb + (thumb - image.width) // 2, y + (thumb - image.height) // 2))
        sheet.paste(mask_thumb, (row_head + 3 * thumb, y))
    sheet.save(out_dir / "_endpoint_schedule_review_sheet.jpg", "JPEG", quality=92, optimize=True)


def write_readme(
    *,
    out_dir: Path,
    manifest: dict[str, Any],
    run_manifest: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    drift = metrics["scheduled_output"]["destination_masked_drift_to_source"]
    edge = metrics["scheduled_output"]["edge_iou_to_source"]
    lines = [
        "# Raven->Cosmic Endpoint-Constrained Finishing Test",
        "",
        "Internal technical output. Not public/show material without Austin per-output approval.",
        "",
        "## Source",
        "",
        f"- Source video: `{manifest.get('source_video', 'unknown')}`",
        f"- Frames: {run_manifest['frame_count']}",
        f"- FPS: {run_manifest['fps']}",
        "",
        "## Settings",
        "",
        f"- Base: `{run_manifest['base']}`",
        f"- ControlNet: `{run_manifest['canny_controlnet']}`",
        f"- LoRA dir: `{run_manifest['lora_dir']}`",
        f"- Middle settings: Canny + LoRA {run_manifest['mid_lora_scale']} + denoise {run_manifest['mid_strength']} + ControlNet {run_manifest['mid_controlnet_scale']}",
        f"- Endpoint settings: denoise 0 / LoRA 0 / ControlNet {run_manifest['endpoint_controlnet_scale']}",
        f"- Ramp frames: {run_manifest['ramp_frames']}",
        f"- Destination mask ramp frames: {run_manifest['dest_mask_ramp_frames']}",
        "",
        "## Output",
        "",
        f"- `{run_manifest['video']}`",
        f"- Frames dir: `{run_manifest['frames_dir']}`",
        "- `_endpoint_schedule_review_sheet.jpg`",
        "- `_endpoint_schedule_metrics.json`",
        "- `_frame_schedule.json`",
        "",
        "## Metrics",
        "",
        f"- Temporal mean ratio to source: {metrics['scheduled_output']['temporal_mean_ratio_to_source']}",
        f"- Edge IoU to source: mean {edge.get('mean')}, min {edge.get('min')}",
        f"- Destination masked drift to source: mean {drift.get('mean')}, max {drift.get('max')}",
        f"- Runtime: {run_manifest['elapsed_seconds']}s",
        "",
        "## Boundary",
        "",
        CONSENT_TEXT.strip(),
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inputs-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--endpoint-mask", type=Path, required=True)
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--canny-controlnet", default=DEFAULT_CANNY_CONTROLNET)
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--mid-strength", type=float, default=0.30)
    parser.add_argument("--mid-lora-scale", type=float, default=0.35)
    parser.add_argument("--mid-controlnet-scale", type=float, default=0.78)
    parser.add_argument("--endpoint-controlnet-scale", type=float, default=1.0)
    parser.add_argument("--ramp-frames", type=int, default=18)
    parser.add_argument("--dest-mask-ramp-frames", type=int, default=18)
    parser.add_argument("--skip-strength-below", type=float, default=0.045)
    parser.add_argument("--quantize-lora-step", type=float, default=0.05)
    parser.add_argument("--canny-low", type=int, default=80)
    parser.add_argument("--canny-high", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--cfg", type=float, default=6.5)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEG)
    parser.add_argument("--output-prefix", default="raven_cosmic_endpoint_scheduled_2026-05-18")
    parser.add_argument("--allow-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.inputs_dir)
    fps = float(manifest.get("fps") or 24.0)
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and not args.allow_existing:
        raise SystemExit(f"Output directory exists and is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    shutil.copy2(args.inputs_dir / "motion_manifest.json", args.out_dir / "_input_motion_manifest.json")
    shutil.copy2(args.endpoint_mask, args.out_dir / "_endpoint_negative_space_mask.png")

    runner = ScheduledRunner(
        base=args.base,
        controlnet_base=args.canny_controlnet,
        lora_dir=args.lora_dir,
        trigger=args.trigger,
        dtype_name=args.dtype,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
        neg_prompt=args.negative_prompt,
        quantize_lora_step=args.quantize_lora_step,
    )
    schedule = build_schedule(
        manifest=manifest,
        ramp_frames=args.ramp_frames,
        mid_strength=args.mid_strength,
        mid_lora_scale=args.mid_lora_scale,
        mid_controlnet_scale=args.mid_controlnet_scale,
        endpoint_controlnet_scale=args.endpoint_controlnet_scale,
        skip_strength_below=args.skip_strength_below,
        dest_mask_ramp_frames=args.dest_mask_ramp_frames,
        runner=runner,
    )
    (args.out_dir / "_frame_schedule.json").write_text(json.dumps([item.__dict__ for item in schedule], indent=2))
    planned = {
        "boundary": CONSENT_TEXT,
        "inputs_dir": str(args.inputs_dir),
        "out_dir": str(args.out_dir),
        "endpoint_mask": str(args.endpoint_mask),
        "lora_dir": str(args.lora_dir),
        "base": args.base,
        "canny_controlnet": args.canny_controlnet,
        "mid_strength": args.mid_strength,
        "mid_lora_scale": args.mid_lora_scale,
        "mid_controlnet_scale": args.mid_controlnet_scale,
        "endpoint_controlnet_scale": args.endpoint_controlnet_scale,
        "ramp_frames": args.ramp_frames,
        "dest_mask_ramp_frames": args.dest_mask_ramp_frames,
        "skip_strength_below": args.skip_strength_below,
        "quantize_lora_step": args.quantize_lora_step,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "frame_count": len(manifest["items"]),
        "fps": fps,
    }
    (args.out_dir / "_run_manifest_planned.json").write_text(json.dumps(planned, indent=2))
    if args.dry_run:
        print(json.dumps(planned, indent=2))
        return 0

    started = time.time()
    mask = Image.open(args.endpoint_mask).convert("L")
    frames_dir_name = "frames_canny_endpoint_scheduled"
    frames_dir = args.out_dir / frames_dir_name
    frames_dir.mkdir(exist_ok=True)
    try:
        runner.load_pipe()
        for item, frame_schedule in zip(manifest["items"], schedule):
            source = Image.open(args.inputs_dir / item["input_file"]).convert("RGB")
            print(
                "[render] "
                f"{item['id']} strength={frame_schedule.strength:.3f} "
                f"lora={frame_schedule.lora_scale:.3f} "
                f"control={frame_schedule.controlnet_scale:.3f} "
                f"mask={frame_schedule.destination_mask_weight:.3f} "
                f"skip={frame_schedule.skip_diffusion}",
                flush=True,
            )
            rendered = runner.render_frame(item=item, image=source, schedule=frame_schedule)
            rendered = apply_destination_mask(
                rendered=rendered,
                source=source,
                mask=mask,
                weight=frame_schedule.destination_mask_weight,
            )
            rendered.save(frames_dir / f"{item['id']}.jpg", "JPEG", quality=94, optimize=True)
            source.close()
    finally:
        runner.close()

    video_name = f"{safe_name(args.output_prefix)}__canny__endpoint_scheduled_lora035_d30_cn078to100.mp4"
    ffmpeg_video(frames_dir, args.out_dir / video_name, fps=fps)
    metrics = build_metrics(
        out_dir=args.out_dir,
        inputs_dir=args.inputs_dir,
        manifest=manifest,
        frames_dir=frames_dir,
        schedule=schedule,
        mask=mask,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
    )
    run_manifest = dict(planned)
    run_manifest.update(
        {
            "elapsed_seconds": round(time.time() - started, 2),
            "frames_dir": frames_dir_name,
            "video": video_name,
            "temporal_metrics_file": "_endpoint_schedule_metrics.json",
            "frame_schedule_file": "_frame_schedule.json",
        }
    )
    (args.out_dir / "_run_manifest.json").write_text(json.dumps(run_manifest, indent=2))
    build_review_sheet(
        out_dir=args.out_dir,
        inputs_dir=args.inputs_dir,
        manifest=manifest,
        frames_dir=frames_dir,
        mask=mask,
        schedule=schedule,
    )
    write_readme(out_dir=args.out_dir, manifest=manifest, run_manifest=run_manifest, metrics=metrics)
    print(f"Done: {args.out_dir / video_name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
