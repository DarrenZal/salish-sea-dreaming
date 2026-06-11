#!/usr/bin/env python3
"""Run Austin-derived ControlNet/Canny + LoRA still matrix on an H200 pod.

Inputs are prepared by scripts/prepare_austin_controlnet_lora_inputs.py and
uploaded as a directory containing:
  - inputs/*.png
  - input_manifest.json

Matrix:
  - ControlNet/Canny only, denoise 0.20 / 0.30 / 0.40
  - ControlNet/Canny + Austin LoRA scale 0.25 / 0.35 / 0.45
  - Each LoRA scale at denoise 0.20 / 0.30 / 0.40

Evaluation question: do the circle/crescent/trigon shapes, clean boundaries,
and flat fills stay readable while LoRA acts only as an atmospheric pass?
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEG = (
    "watermark, text, logo, signature, stock photo, copyright, label, caption, "
    "literal eyeball, central eye, fake crest, invented crest, emblem, badge, "
    "photorealistic, noisy texture, blurry, distorted, low quality, extra limbs, "
    "kaleidoscope, mandala, decorative wallpaper"
)


CONSENT_TEXT = """INTERNAL ONLY — PENDING AUSTIN PER-OUTPUT APPROVAL.

Output set: Austin-derived ControlNet/Canny + Austin v2 LoRA technical matrix.

Source inputs are internal deterministic sketches and synthetic primitive/graph
prototypes prepared from Austin-source experiments. Generated outputs are NOT
Austin Harry artwork and are NOT approved public/show material.

Purpose: test whether ControlNet/Canny preserves circles, crescents, trigons,
line boundaries, and flat fills while low-scale LoRA contributes only palette,
register, and atmosphere.

Do not share with Austin, Pravin externally, sponsors, venue, social media, or
public audiences without an explicit operator decision and Austin's per-output
approval.
"""


@dataclass(frozen=True)
class Variant:
    id: str
    label: str
    lora_scale: float | None
    strength: float


def build_variants(strengths: list[float], lora_scales: list[float]) -> list[Variant]:
    variants: list[Variant] = []
    for strength in strengths:
        variants.append(
            Variant(
                id=f"controlnet_only_d{int(strength * 100):02d}",
                label=f"CN only d={strength:.2f}",
                lora_scale=None,
                strength=strength,
            )
        )
    for scale in lora_scales:
        for strength in strengths:
            variants.append(
                Variant(
                    id=f"lora{int(scale * 100):03d}_d{int(strength * 100):02d}",
                    label=f"LoRA {scale:.2f} d={strength:.2f}",
                    lora_scale=scale,
                    strength=strength,
                )
            )
    return variants


def parse_float_list(value: str) -> list[float]:
    return [float(part.strip()) for part in value.split(",") if part.strip()]


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def canny_image(frame: Image.Image, low: int, high: int) -> Image.Image:
    import cv2
    import numpy as np

    arr = np.array(frame.convert("RGB"))
    edges = cv2.Canny(arr, threshold1=low, threshold2=high)
    edges = np.stack([edges, edges, edges], axis=-1)
    return Image.fromarray(edges)


def prompt_for(item: dict[str, Any], *, trigger: str, with_lora: bool) -> str:
    hint = item.get("prompt_hint") or "clean vector shape study"
    common = (
        f"{hint}, preserve original composition, preserve clean line boundaries, "
        "preserve circle oval crescent trigon forms, flat color fields, breathing negative space"
    )
    if with_lora:
        return f"{trigger}, {common}, restrained palette, subtle atmospheric style pass"
    return f"{common}, simple clean vector rendering"


class Runner:
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
        neg_prompt: str,
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
        self.neg_prompt = neg_prompt
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
        controlnet = ControlNetModel.from_pretrained(
            self.controlnet_base,
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

    def set_lora(self, scale: float | None) -> None:
        pipe = self.load_pipe()
        if self.loaded_lora_scale == scale:
            return
        if self.loaded_lora_scale is not None:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        if scale is None:
            return
        pipe.load_lora_weights(str(self.lora_dir))
        pipe.fuse_lora(lora_scale=scale)
        self.loaded_lora_scale = scale

    def render(self, item: dict[str, Any], image: Image.Image, variant: Variant, item_index: int) -> Image.Image:
        import torch

        pipe = self.load_pipe()
        control = canny_image(image, self.canny_low, self.canny_high)
        generator = torch.Generator(device="cuda").manual_seed(self.seed + item_index)
        prompt = prompt_for(item, trigger=self.trigger, with_lora=variant.lora_scale is not None)
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


def load_manifest(inputs_dir: Path) -> dict[str, Any]:
    manifest_path = inputs_dir / "input_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    return json.loads(manifest_path.read_text())


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


def build_contact_sheet(
    *,
    out_dir: Path,
    manifest: dict[str, Any],
    variants: list[Variant],
    canny_low: int,
    canny_high: int,
) -> None:
    items = manifest["items"]
    thumb = 136
    label_h = 42
    row_head = 220
    col_count = 2 + len(variants)
    row_count = len(items)
    w = row_head + col_count * thumb
    h = label_h + row_count * (thumb + 28)
    sheet = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = load_font(10)
    font_b = load_font(12, bold=True)

    headers = ["source", "canny"] + [variant.label for variant in variants]
    for col, header in enumerate(headers):
        x = row_head + col * thumb
        draw.text((x + 4, 6), header[:20], font=font_b, fill=(30, 30, 30))

    for row, item in enumerate(items):
        y = label_h + row * (thumb + 28)
        draw.text((8, y + 8), item["id"], font=font_b, fill=(20, 20, 20))
        draw.text((8, y + 24), item.get("prompt_hint", "")[:34], font=font, fill=(70, 70, 70))
        source_path = out_dir / "sources" / f"{item['id']}.png"
        if source_path.exists():
            with Image.open(source_path) as image:
                image = image.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
            sheet.paste(image, (row_head, y))
            canny = canny_image(image, canny_low, canny_high)
            sheet.paste(canny.resize((thumb, thumb), Image.Resampling.LANCZOS), (row_head + thumb, y))
        for col, variant in enumerate(variants, start=2):
            result_path = out_dir / f"{item['id']}__{variant.id}.jpg"
            if not result_path.exists():
                continue
            with Image.open(result_path) as image:
                image = image.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
            sheet.paste(image, (row_head + col * thumb, y))
    sheet.save(out_dir / "_contact_sheet_by_input.jpg", "JPEG", quality=88)


def write_run_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inputs-dir", type=Path, default=Path("austin-cn-lora-inputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("austin-cn-lora-results-2026-05-17"))
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--controlnet-base", default=DEFAULT_CONTROLNET)
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--strengths", default="0.20,0.30,0.40")
    parser.add_argument("--lora-scales", default="0.25,0.35,0.45")
    parser.add_argument("--controlnet-scale", type=float, default=0.78)
    parser.add_argument("--canny-low", type=int, default=80)
    parser.add_argument("--canny-high", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--cfg", type=float, default=6.5)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--neg-prompt", default=DEFAULT_NEG)
    parser.add_argument("--limit", type=int, default=None, help="Optional first-N input limit for smoke tests")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.inputs_dir)
    items = manifest["items"][: args.limit] if args.limit else manifest["items"]
    strengths = parse_float_list(args.strengths)
    lora_scales = parse_float_list(args.lora_scales)
    variants = build_variants(strengths, lora_scales)
    planned = {
        "boundary": CONSENT_TEXT,
        "inputs_dir": str(args.inputs_dir),
        "out_dir": str(args.out_dir),
        "lora_dir": str(args.lora_dir),
        "base": args.base,
        "controlnet_base": args.controlnet_base,
        "trigger": args.trigger,
        "strengths": strengths,
        "lora_scales": lora_scales,
        "controlnet_scale": args.controlnet_scale,
        "canny": {"low": args.canny_low, "high": args.canny_high},
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "render_count": len(items) * len(variants),
        "items": items,
        "variants": [variant.__dict__ for variant in variants],
    }

    print("=" * 72)
    print("Austin ControlNet/Canny + LoRA matrix")
    print("=" * 72)
    print(f"inputs: {args.inputs_dir} ({len(items)} stills)")
    print(f"matrix: {len(variants)} variants -> {len(items) * len(variants)} renders")
    print(f"out   : {args.out_dir}")
    print(f"lora  : {args.lora_dir}")

    if args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_run_manifest(args.out_dir / "_dry_run_manifest.json", planned)
        print("[DRY RUN] no model loaded.")
        return 0

    if not args.lora_dir.exists():
        raise SystemExit(f"LoRA dir does not exist: {args.lora_dir}")
    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    write_run_manifest(args.out_dir / "_run_manifest_planned.json", planned)

    sources_dir = args.out_dir / "sources"
    sources_dir.mkdir()
    runner = Runner(
        base=args.base,
        controlnet_base=args.controlnet_base,
        lora_dir=args.lora_dir,
        trigger=args.trigger,
        dtype_name=args.dtype,
        controlnet_scale=args.controlnet_scale,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
        neg_prompt=args.neg_prompt,
    )

    results: list[dict[str, Any]] = []
    t0 = time.time()
    loaded_items: list[tuple[int, dict[str, Any], Image.Image]] = []
    for item_index, item in enumerate(items):
        input_path = args.inputs_dir / item["input_file"]
        image = Image.open(input_path).convert("RGB")
        image.save(sources_dir / f"{item['id']}.png")
        loaded_items.append((item_index, item, image))

    for variant in variants:
        print(f"\n[variant] {variant.label}", flush=True)
        runner.set_lora(variant.lora_scale)
        for item_index, item, image in loaded_items:
            out_name = f"{safe_name(item['id'])}__{variant.id}.jpg"
            out_path = args.out_dir / out_name
            print(f"[render] {out_name}", flush=True)
            rendered = runner.render(item, image, variant, item_index)
            rendered.save(out_path, "JPEG", quality=92)
            results.append(
                {
                    "input_id": item["id"],
                    "variant": variant.__dict__,
                    "output_file": out_name,
                    "prompt": prompt_for(item, trigger=args.trigger, with_lora=variant.lora_scale is not None),
                }
            )

    planned["results"] = results
    planned["elapsed_seconds"] = round(time.time() - t0, 2)
    write_run_manifest(args.out_dir / "_run_manifest.json", planned)
    build_contact_sheet(
        out_dir=args.out_dir,
        manifest={"items": items},
        variants=variants,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
    )
    print(f"Done: {len(results)} renders in {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
