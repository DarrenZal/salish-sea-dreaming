#!/usr/bin/env python3
"""Controlled abstract text-to-image affordance test.

Compares prompt-only Austin v2 LoRA against ControlNet/Canny synthetic
primitive scaffolds, with and without the LoRA. This is an internal affordance
test only: no animals, clan beings, supernatural beings, crests, or public/show
framing.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEGATIVE = (
    "animal, animals, creature, creatures, bird, raven, wolf, salmon, orca, whale, "
    "thunderbird, serpent, human, face, eyes, mask, crest, clan crest, emblem, badge, "
    "totem, ceremonial object, ceremony, supernatural being, character, figurative, "
    "fake Indigenous art, invented cultural symbol, invented icon, text, watermark, "
    "signature, logo, caption, blurry, noisy, low quality"
)


CONSENT_TEXT = """INTERNAL ONLY — ABSTRACT AFFORDANCE TEST.

No public/show use. No prompt-only Austin-style creatures. No animals, clan
beings, supernatural beings, or crests were requested.

This test compares prompt-only Austin v2 LoRA output against synthetic
Circle/Crescent/Trigon scaffolds with ControlNet. Outputs are not Austin Harry
artwork and are not approved public/show material. Use only for internal
discussion of what SD/LoRA is allowed to do: finish/background/atmosphere, not
authorship or geometry.
"""


@dataclass(frozen=True)
class PromptCase:
    id: str
    prompt: str
    scaffold: str


@dataclass(frozen=True)
class RenderSpec:
    id: str
    label: str
    mode: str
    lora_scale: float | None


PROMPTS = [
    PromptCase(
        id="p01_pearl_interior_three_primitives",
        prompt="pearl interior with three primitive forms, abstract luminous chamber, clean simple geometry, circle crescent trigon, negative space, soft ocean light",
        scaffold="radial_pearl",
    ),
    PromptCase(
        id="p02_dawn_water_abstract_geometry",
        prompt="dawn light over water as abstract geometry, horizon glow, circles crescents trigons, calm reflective atmosphere, clean shape study",
        scaffold="horizon_water",
    ),
    PromptCase(
        id="p03_tide_current_field",
        prompt="tide-current field of circles crescents trigons, abstract current map, rhythmic flow, clean primitive geometry, open negative space",
        scaffold="current_field",
    ),
    PromptCase(
        id="p04_breathing_negative_space",
        prompt="breathing negative space primitive composition, circles crescents trigons, spacious balanced abstract design, quiet luminous field",
        scaffold="negative_space",
    ),
]

SPECS = [
    RenderSpec("A_prompt_lora025", "A prompt-only LoRA 0.25", "prompt_only_lora", 0.25),
    RenderSpec("A_prompt_lora035", "A prompt-only LoRA 0.35", "prompt_only_lora", 0.35),
    RenderSpec("B_scaffold_lora025", "B scaffold + LoRA 0.25", "controlnet_lora", 0.25),
    RenderSpec("B_scaffold_lora035", "B scaffold + LoRA 0.35", "controlnet_lora", 0.35),
    RenderSpec("C_scaffold_no_lora", "C scaffold, no LoRA", "controlnet_no_lora", None),
]


def dtype_for(name: str):
    import torch

    if name == "bf16":
        return torch.bfloat16
    if name == "fp32":
        return torch.float32
    return torch.float16


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


def crescent_points(cx: float, cy: float, outer: float, inner: float, start: float, end: float, bite_dx: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(40):
        t = start + (end - start) * i / 39
        pts.append((cx + outer * math.cos(t), cy + outer * math.sin(t)))
    for i in range(39, -1, -1):
        t = start + (end - start) * i / 39
        pts.append((cx + bite_dx + inner * math.cos(t), cy + inner * math.sin(t)))
    return pts


def draw_crescent(draw: ImageDraw.ImageDraw, cx: float, cy: float, scale: float, angle: float, width: int = 8) -> None:
    # Use a filled polygon plus outline so Canny ControlNet sees a stable primitive.
    pts = crescent_points(0, 0, 52 * scale, 39 * scale, -1.35, 1.35, 26 * scale)
    ca, sa = math.cos(angle), math.sin(angle)
    rotated = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
    draw.polygon(rotated, outline=255, fill=255)
    # Cut a thinner interior groove to keep crescent recognition.
    inner_pts = crescent_points(0, 0, 38 * scale, 28 * scale, -1.17, 1.17, 18 * scale)
    inner = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in inner_pts]
    draw.polygon(inner, outline=0, fill=0)
    draw.line(rotated + [rotated[0]], fill=255, width=width, joint="curve")


def draw_trigon(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, angle: float, fill: int = 255) -> None:
    pts = []
    for k in range(3):
        a = angle - math.pi / 2 + k * 2 * math.pi / 3
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    draw.polygon(pts, outline=fill, fill=fill)


def draw_circle(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, width: int = 8, fill: bool = False) -> None:
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    if fill:
        draw.ellipse(box, outline=255, fill=255)
    else:
        draw.ellipse(box, outline=255, width=width)


def build_scaffold(case: PromptCase, size: int) -> Image.Image:
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    s = size / 512
    if case.scaffold == "radial_pearl":
        draw_circle(draw, 256 * s, 256 * s, 170 * s, width=max(5, int(8 * s)))
        draw_circle(draw, 256 * s, 256 * s, 46 * s, fill=True)
        draw_crescent(draw, 174 * s, 257 * s, 1.0 * s, 0.0)
        draw_crescent(draw, 338 * s, 257 * s, 1.0 * s, math.pi)
        draw_trigon(draw, 256 * s, 128 * s, 50 * s, 0.0)
        draw_trigon(draw, 256 * s, 384 * s, 50 * s, math.pi)
    elif case.scaffold == "horizon_water":
        draw.line([(60 * s, 252 * s), (452 * s, 252 * s)], fill=255, width=max(5, int(8 * s)))
        for x in (118, 214, 310, 406):
            draw.arc([x * s - 50 * s, 282 * s, x * s + 50 * s, 350 * s], 200, 340, fill=255, width=max(4, int(7 * s)))
        draw_circle(draw, 256 * s, 172 * s, 58 * s, width=max(5, int(8 * s)))
        draw_trigon(draw, 104 * s, 194 * s, 34 * s, -0.1)
        draw_crescent(draw, 386 * s, 190 * s, 0.75 * s, math.pi * 0.2)
    elif case.scaffold == "current_field":
        for idx in range(18):
            x = (72 + (idx % 6) * 76 + (idx // 6) * 15) * s
            y = (118 + (idx // 6) * 116 + math.sin(idx) * 18) * s
            if idx % 3 == 0:
                draw_circle(draw, x, y, 27 * s, width=max(4, int(6 * s)))
            elif idx % 3 == 1:
                draw_crescent(draw, x, y, 0.52 * s, 0.8 + idx * 0.35, width=max(3, int(5 * s)))
            else:
                draw_trigon(draw, x, y, 29 * s, idx * 0.2)
        for k in range(5):
            y = (90 + k * 78) * s
            draw.arc([36 * s, y, 476 * s, y + 110 * s], 192, 334, fill=255, width=max(2, int(3 * s)))
    elif case.scaffold == "negative_space":
        draw_circle(draw, 256 * s, 256 * s, 180 * s, width=max(7, int(10 * s)))
        draw_crescent(draw, 190 * s, 230 * s, 0.95 * s, 0.15)
        draw_crescent(draw, 322 * s, 230 * s, 0.95 * s, math.pi - 0.15)
        draw_crescent(draw, 256 * s, 342 * s, 0.75 * s, math.pi / 2)
        draw_trigon(draw, 256 * s, 148 * s, 48 * s, 0.0)
        # Open a central void.
        draw.ellipse([205 * s, 205 * s, 307 * s, 307 * s], fill=0)
    else:
        raise ValueError(case.scaffold)
    return image.convert("RGB")


class LoraMixin:
    pipe: Any
    loaded_lora_scale: float | None

    def set_lora(self, lora_dir: Path, scale: float | None) -> None:
        if getattr(self, "loaded_lora_scale", None) == scale:
            return
        if getattr(self, "loaded_lora_scale", None) is not None:
            self.pipe.unfuse_lora()
            self.pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        if scale is None:
            return
        self.pipe.load_lora_weights(str(lora_dir))
        self.pipe.fuse_lora(lora_scale=scale)
        self.loaded_lora_scale = scale


class PromptOnlyRunner(LoraMixin):
    def __init__(self, *, base: str, lora_dir: Path, dtype_name: str) -> None:
        self.base = base
        self.lora_dir = lora_dir
        self.dtype_name = dtype_name
        self.pipe = None
        self.loaded_lora_scale = None

    def load(self):
        if self.pipe is not None:
            return self.pipe
        from diffusers import StableDiffusionPipeline

        print(f"[load] prompt-only base={self.base}", flush=True)
        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.base,
            torch_dtype=dtype_for(self.dtype_name),
            safety_checker=None,
            requires_safety_checker=False,
        ).to("cuda")
        self.pipe.set_progress_bar_config(disable=True)
        return self.pipe

    def render(self, *, prompt: str, negative_prompt: str, scale: float, seed: int, steps: int, cfg: float, size: int) -> Image.Image:
        import torch

        pipe = self.load()
        self.set_lora(self.lora_dir, scale)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        with torch.inference_mode():
            return pipe(
                prompt=f"{DEFAULT_TRIGGER}, {prompt}",
                negative_prompt=negative_prompt,
                width=size,
                height=size,
                num_inference_steps=steps,
                guidance_scale=cfg,
                generator=generator,
            ).images[0].convert("RGB")


class ControlNetRunner(LoraMixin):
    def __init__(self, *, base: str, controlnet_base: str, lora_dir: Path, dtype_name: str) -> None:
        self.base = base
        self.controlnet_base = controlnet_base
        self.lora_dir = lora_dir
        self.dtype_name = dtype_name
        self.pipe = None
        self.loaded_lora_scale = None

    def load(self):
        if self.pipe is not None:
            return self.pipe
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

        print(f"[load] controlnet={self.controlnet_base}", flush=True)
        controlnet = ControlNetModel.from_pretrained(
            self.controlnet_base,
            torch_dtype=dtype_for(self.dtype_name),
        )
        print(f"[load] controlnet base={self.base}", flush=True)
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            self.base,
            controlnet=controlnet,
            torch_dtype=dtype_for(self.dtype_name),
            safety_checker=None,
            requires_safety_checker=False,
        ).to("cuda")
        self.pipe.set_progress_bar_config(disable=True)
        return self.pipe

    def render(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        scaffold: Image.Image,
        scale: float | None,
        seed: int,
        steps: int,
        cfg: float,
        controlnet_scale: float,
    ) -> Image.Image:
        import torch

        pipe = self.load()
        self.set_lora(self.lora_dir, scale)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        full_prompt = f"{DEFAULT_TRIGGER}, {prompt}" if scale is not None else prompt
        with torch.inference_mode():
            return pipe(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                image=scaffold,
                num_inference_steps=steps,
                guidance_scale=cfg,
                controlnet_conditioning_scale=controlnet_scale,
                generator=generator,
            ).images[0].convert("RGB")


def edge_overlap(scaffold: Image.Image, output: Image.Image) -> float:
    try:
        import cv2
        import numpy as np
    except Exception:
        return -1.0
    s = np.asarray(scaffold.convert("L").resize((128, 128), Image.Resampling.BILINEAR)) > 32
    arr = np.asarray(output.convert("RGB").resize((128, 128), Image.Resampling.BILINEAR))
    edges = cv2.Canny(arr, 80, 180) > 0
    union = np.logical_or(s, edges).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(s, edges).sum() / union)


def build_contact_sheet(out_dir: Path, results: list[dict[str, Any]], size: int) -> None:
    rows = PROMPTS
    cols = ["scaffold"] + [spec.id for spec in SPECS]
    thumb = 192
    row_head = 258
    label_h = 70
    sheet = Image.new("RGB", (row_head + len(cols) * thumb, label_h + len(rows) * (thumb + 34)), (244, 244, 244))
    draw = ImageDraw.Draw(sheet)
    font = load_font(11)
    font_b = load_font(13, bold=True)
    for col, label in enumerate(cols):
        draw.text((row_head + col * thumb + 6, 8), label[:24], fill=(20, 20, 20), font=font_b)
    by_key = {(r["prompt_id"], r["variant_id"]): r for r in results}
    for row, case in enumerate(rows):
        y = label_h + row * (thumb + 34)
        draw.text((10, y + 8), case.id, fill=(20, 20, 20), font=font_b)
        draw.text((10, y + 28), case.prompt[:38], fill=(60, 60, 60), font=font)
        scaffold_path = out_dir / "scaffolds" / f"{case.id}_scaffold.png"
        paths = [scaffold_path]
        for spec in SPECS:
            record = by_key.get((case.id, spec.id))
            paths.append(out_dir / record["file"] if record else None)
        for col, path in enumerate(paths):
            if path is None or not Path(path).exists():
                continue
            with Image.open(path) as image:
                image = image.convert("RGB")
                image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                x = row_head + col * thumb + (thumb - image.width) // 2
                sheet.paste(image, (x, y + (thumb - image.height) // 2))
    sheet.save(out_dir / "_contact_sheet.jpg", "JPEG", quality=90, optimize=True)


def write_report(out_dir: Path, results: list[dict[str, Any]], elapsed: float, args: argparse.Namespace) -> None:
    lines = [
        "# Austin Abstract T2I Affordance Test - 2026-05-18",
        "",
        "Internal-only controlled still test. No public/show use.",
        "",
        "## Test Shape",
        "",
        "- 4 low-cultural-load abstract prompts.",
        "- A: prompt-only Austin v2 LoRA at 0.25 and 0.35.",
        "- B: synthetic primitive scaffold + ControlNet/Canny + Austin v2 LoRA at 0.25 and 0.35.",
        "- C: same synthetic primitive scaffold + ControlNet/Canny with no Austin LoRA.",
        "- No animals, clan beings, supernatural beings, crests, or Austin-like creatures requested.",
        "",
        "## Settings",
        "",
        f"- Base: `{args.base}`",
        f"- ControlNet: `{args.controlnet_base}`",
        f"- LoRA dir: `{args.lora_dir}`",
        f"- Size: {args.size}",
        f"- Steps: {args.steps}",
        f"- CFG: {args.cfg}",
        f"- ControlNet scale: {args.controlnet_scale}",
        f"- Runtime: {elapsed:.2f}s",
        "",
        "## Outputs",
        "",
        "- `_contact_sheet.jpg`",
        "- `scaffolds/`",
        "- `results.json`",
        "",
        "## Quantitative Scaffold Edge Overlap",
        "",
    ]
    for record in results:
        if record["mode"] == "prompt_only_lora":
            continue
        lines.append(f"- `{record['file']}`: edge overlap {record['edge_overlap']:.4f}")
    lines.extend(["", "## Consent", "", CONSENT_TEXT.strip(), ""])
    (out_dir / "README.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--controlnet-base", default=DEFAULT_CONTROLNET)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--cfg", type=float, default=6.0)
    parser.add_argument("--controlnet-scale", type=float, default=0.92)
    parser.add_argument("--seed", type=int, default=1842)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE)
    parser.add_argument("--allow-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.out_dir.exists() and any(args.out_dir.iterdir()) and not args.allow_existing:
        raise SystemExit(f"Output directory exists and is not empty: {args.out_dir}")
    if args.out_dir.exists() and not args.allow_existing:
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)
    scaffold_dir = args.out_dir / "scaffolds"
    scaffold_dir.mkdir(exist_ok=True)

    planned = {
        "boundary": CONSENT_TEXT,
        "prompts": [case.__dict__ for case in PROMPTS],
        "specs": [spec.__dict__ for spec in SPECS],
        "settings": vars(args),
        "render_count": len(PROMPTS) * len(SPECS),
    }
    (args.out_dir / "_run_manifest_planned.json").write_text(json.dumps(planned, indent=2, default=str))
    for case in PROMPTS:
        scaffold = build_scaffold(case, args.size)
        scaffold.save(scaffold_dir / f"{case.id}_scaffold.png")
    if args.dry_run:
        print(json.dumps(planned, indent=2, default=str))
        return 0

    started = time.time()
    prompt_runner = PromptOnlyRunner(base=args.base, lora_dir=args.lora_dir, dtype_name=args.dtype)
    control_runner = ControlNetRunner(base=args.base, controlnet_base=args.controlnet_base, lora_dir=args.lora_dir, dtype_name=args.dtype)
    results: list[dict[str, Any]] = []
    try:
        for prompt_index, case in enumerate(PROMPTS):
            scaffold = Image.open(scaffold_dir / f"{case.id}_scaffold.png").convert("RGB")
            for spec_index, spec in enumerate(SPECS):
                seed = args.seed + prompt_index * 100 + spec_index
                print(f"[render] {case.id} {spec.id} seed={seed}", flush=True)
                if spec.mode == "prompt_only_lora":
                    image = prompt_runner.render(
                        prompt=case.prompt,
                        negative_prompt=args.negative_prompt,
                        scale=spec.lora_scale or 0.0,
                        seed=seed,
                        steps=args.steps,
                        cfg=args.cfg,
                        size=args.size,
                    )
                    overlap = -1.0
                else:
                    image = control_runner.render(
                        prompt=case.prompt,
                        negative_prompt=args.negative_prompt,
                        scaffold=scaffold,
                        scale=spec.lora_scale,
                        seed=seed,
                        steps=args.steps,
                        cfg=args.cfg,
                        controlnet_scale=args.controlnet_scale,
                    )
                    overlap = edge_overlap(scaffold, image)
                filename = f"{case.id}__{spec.id}.jpg"
                image.save(args.out_dir / filename, "JPEG", quality=94, optimize=True)
                results.append(
                    {
                        "prompt_id": case.id,
                        "prompt": case.prompt,
                        "variant_id": spec.id,
                        "label": spec.label,
                        "mode": spec.mode,
                        "lora_scale": spec.lora_scale,
                        "seed": seed,
                        "file": filename,
                        "edge_overlap": overlap,
                    }
                )
    finally:
        try:
            import gc
            import torch

            prompt_runner.pipe = None
            control_runner.pipe = None
            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            pass

    elapsed = time.time() - started
    (args.out_dir / "results.json").write_text(json.dumps(results, indent=2))
    build_contact_sheet(args.out_dir, results, args.size)
    run_manifest = dict(planned)
    run_manifest["elapsed_seconds"] = round(elapsed, 2)
    run_manifest["results_file"] = "results.json"
    (args.out_dir / "_run_manifest.json").write_text(json.dumps(run_manifest, indent=2, default=str))
    write_report(args.out_dir, results, elapsed, args)
    print(f"Done: {len(results)} renders in {args.out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
