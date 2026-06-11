#!/usr/bin/env python3
"""One-frame flat scaffold + ControlNet + Austin LoRA still test."""

from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_SOURCE = Path("austin-real-footage-h1-salmon-cn-lora-feasibility-2026-05-18-inputs/frames/frame_0013.jpg")
DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"
DEFAULT_CONTROLNET = "lllyasviel/sd-controlnet-canny"
DEFAULT_TRIGGER = "austin_v2"
DEFAULT_NEGATIVE = (
    "watermark, text, logo, signature, filename, timecode, stock footage text, fake Indigenous art, "
    "invented crest, clan crest, emblem, badge, ceremonial mask, supernatural being, human face, "
    "extra fish, new creature, photorealistic, dense biological scratch texture, noisy ornament, "
    "kaleidoscope, mandala, blurry, distorted, low quality"
)

CONSENT_TEXT = """INTERNAL ONLY - FLAT SCAFFOLD + AUSTIN LORA STILL TEST.

No public/show use. No prompt-only salmon generation. Source geometry comes from
one real H1 salmon footage frame, then an algorithmic flattened scaffold and
Canny control image. Austin v2 LoRA is tested only as a finish layer.

The high-risk setting is internal-only and should not be shown without explicit
operator framing and Austin review.
"""


@dataclass(frozen=True)
class Variant:
    id: str
    label: str
    strength: float
    lora_scale: float


VARIANTS = [
    Variant("conservative_d045_lora035", "conservative d=0.45 LoRA 0.35", 0.45, 0.35),
    Variant("style_test_d060_lora045", "style test d=0.60 LoRA 0.45", 0.60, 0.45),
    Variant("high_risk_d070_lora055", "HIGH-RISK internal d=0.70 LoRA 0.55", 0.70, 0.55),
]


def load_font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_flat_scaffold(source: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Build a simplified graphic scaffold and Canny control image."""
    import cv2
    import numpy as np

    rgb = np.array(source.convert("RGB"))
    h, w = rgb.shape[:2]

    # The H1 subclip has burn-in text at the bottom. Suppress it in the working
    # scaffold so the control image does not learn filename/timecode strokes.
    work = rgb.copy()
    burn_h = max(24, int(h * 0.07))
    patch = work[max(0, h - burn_h * 2) : h - burn_h, :, :]
    fill = np.median(patch.reshape(-1, 3), axis=0).astype("uint8")
    work[h - burn_h :, :, :] = fill

    # Smooth the water first, then quantize into a few stable teal bands.
    smooth = cv2.bilateralFilter(work, d=11, sigmaColor=65, sigmaSpace=65)
    lab = cv2.cvtColor(smooth, cv2.COLOR_RGB2LAB)
    pixels = lab.reshape((-1, 3)).astype("float32")
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.8)
    _, labels, centers = cv2.kmeans(pixels, 5, None, criteria, 2, cv2.KMEANS_PP_CENTERS)
    quant_lab = centers[labels.flatten()].reshape(lab.shape).astype("uint8")
    quant = cv2.cvtColor(quant_lab, cv2.COLOR_LAB2RGB)

    gray = cv2.cvtColor(work, cv2.COLOR_RGB2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Fish are mostly dark silhouettes against the backlit water. Combine a
    # global dark threshold with adaptive thresholding to catch smaller bodies.
    dark = gray_blur < 112
    adaptive = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        35,
        5,
    ) > 0
    mask = np.logical_or(dark, adaptive).astype("uint8") * 255
    mask[h - burn_h :, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1)

    # Remove tiny noise and broad border-vignette regions while keeping fish.
    num, comp, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    clean = np.zeros_like(mask)
    for idx in range(1, num):
        x, y, cw, ch, area = stats[idx]
        touches_many_edges = (x == 0 or y == 0 or x + cw >= w or y + ch >= h) and area > 12000
        if 35 <= area <= 26000 and not touches_many_edges:
            clean[comp == idx] = 255
    clean = cv2.dilate(clean, np.ones((3, 3), np.uint8), iterations=1)

    scaffold = quant.copy()
    # Pull background toward a small set of calm teal/green tones.
    scaffold = cv2.addWeighted(scaffold, 0.72, np.full_like(scaffold, [40, 118, 104]), 0.28, 0)
    fish_fill = np.array([12, 31, 29], dtype="uint8")
    scaffold[clean > 0] = fish_fill
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(scaffold, contours, -1, (232, 226, 204), 2, cv2.LINE_AA)

    # Add one restrained warm accent to test whether the later LoRA has a
    # graphic palette bridge without changing geometry.
    accent = cv2.erode(clean, np.ones((9, 9), np.uint8), iterations=1)
    accent = cv2.GaussianBlur(accent, (0, 0), 1.6)
    accent_mask = accent > 95
    warm = np.array([174, 53, 32], dtype="uint8")
    scaffold[accent_mask] = (0.78 * scaffold[accent_mask] + 0.22 * warm).astype("uint8")

    edges = cv2.Canny(scaffold, 70, 170)
    edge_rgb = np.stack([edges, edges, edges], axis=-1)
    return Image.fromarray(scaffold).convert("RGB"), Image.fromarray(edge_rgb).convert("RGB")


def prompt_for(trigger: str) -> str:
    return (
        f"{trigger}, flat graphic salmon school scaffold, preserve exact fish silhouettes and source layout, "
        "clean vector linework, reduced palette, high contrast negative space, restrained red black yellow accents, "
        "digital design plate finish, surface and light only"
    )


class Renderer:
    def __init__(
        self,
        *,
        base: str,
        controlnet_base: str,
        lora_dir: Path,
        dtype_name: str,
        controlnet_scale: float,
        seed: int,
        steps: int,
        cfg: float,
        negative_prompt: str,
    ) -> None:
        self.base = base
        self.controlnet_base = controlnet_base
        self.lora_dir = lora_dir
        self.dtype_name = dtype_name
        self.controlnet_scale = controlnet_scale
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

    def set_lora(self, scale: float) -> None:
        pipe = self.load_pipe()
        if self.loaded_lora_scale is not None:
            pipe.unfuse_lora()
            pipe.unload_lora_weights()
            self.loaded_lora_scale = None
        pipe.load_lora_weights(str(self.lora_dir))
        pipe.fuse_lora(lora_scale=scale)
        self.loaded_lora_scale = scale

    def render(self, *, scaffold: Image.Image, control: Image.Image, prompt: str, variant: Variant) -> Image.Image:
        import torch

        pipe = self.load_pipe()
        self.set_lora(variant.lora_scale)
        generator = torch.Generator(device="cuda").manual_seed(self.seed)
        with torch.inference_mode():
            return pipe(
                prompt=prompt,
                negative_prompt=self.negative_prompt,
                image=scaffold,
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
        try:
            import gc
            import torch

            gc.collect()
            torch.cuda.empty_cache()
        except Exception:
            pass


def build_contact_sheet(
    *,
    out_dir: Path,
    source: Image.Image,
    scaffold: Image.Image,
    control: Image.Image,
    outputs: list[tuple[Variant, Image.Image]],
) -> None:
    cols: list[tuple[str, Image.Image]] = [
        ("source photo", source),
        ("segmented scaffold", scaffold),
        ("lineart control", control),
    ]
    cols.extend((variant.label, image) for variant, image in outputs)
    cell_w, cell_h = 300, 169
    label_h = 46
    sheet = Image.new("RGB", (len(cols) * cell_w, label_h + cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = load_font(13, bold=True)
    small = load_font(10)
    for index, (label, image) in enumerate(cols):
        x = index * cell_w
        draw.text((x + 8, 6), label[:32], fill=(15, 15, 15), font=font)
        if "HIGH-RISK" in label:
            draw.text((x + 8, 24), "internal-only", fill=(160, 30, 20), font=small)
        thumb = image.copy()
        thumb.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width) // 2, label_h + (cell_h - thumb.height) // 2))
    sheet.save(out_dir / "contact_sheet_source_scaffold_control_outputs.jpg", "JPEG", quality=92, optimize=True)


def write_readme(out_dir: Path, manifest: dict) -> None:
    lines = [
        "# Flat Salmon Scaffold + Austin LoRA Still Test",
        "",
        "Internal-only still-frame test. Not proposed artwork. Not public/show material.",
        "",
        "Pipeline: source H1 salmon frame -> algorithmic segmentation/flattening -> Canny control -> ControlNet + Austin v2 LoRA.",
        "",
        "No prompt-only salmon generation was run.",
        "",
        "## Variants",
        "",
    ]
    for variant in manifest["variants"]:
        lines.append(f"- {variant['label']}: denoise/strength `{variant['strength']}`, LoRA `{variant['lora_scale']}`")
    lines.extend(["", "## Boundary", "", CONSENT_TEXT.strip(), ""])
    (out_dir / "README.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--lora-dir", type=Path, default=Path("austin-v2-lora-out"))
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--controlnet", default=DEFAULT_CONTROLNET)
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--controlnet-scale", type=float, default=0.92)
    parser.add_argument("--seed", type=int, default=20260518)
    parser.add_argument("--steps", type=int, default=34)
    parser.add_argument("--cfg", type=float, default=6.7)
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

    manifest = {
        "boundary": CONSENT_TEXT,
        "source": str(args.source),
        "out_dir": str(args.out_dir),
        "base": args.base,
        "controlnet": args.controlnet,
        "lora_dir": str(args.lora_dir),
        "trigger": args.trigger,
        "prompt": prompt_for(args.trigger),
        "negative_prompt": args.negative_prompt,
        "controlnet_scale": args.controlnet_scale,
        "seed": args.seed,
        "steps": args.steps,
        "cfg": args.cfg,
        "dtype": args.dtype,
        "variants": [variant.__dict__ for variant in VARIANTS],
    }
    (args.out_dir / "_run_manifest_planned.json").write_text(json.dumps(manifest, indent=2))
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return 0

    source = Image.open(args.source).convert("RGB")
    scaffold, control = build_flat_scaffold(source)
    source.save(args.out_dir / "01_source_photo.jpg", "JPEG", quality=94, optimize=True)
    scaffold.save(args.out_dir / "02_segmented_flat_scaffold.jpg", "JPEG", quality=94, optimize=True)
    control.save(args.out_dir / "03_canny_lineart_control.jpg", "JPEG", quality=94, optimize=True)
    (args.out_dir / "CONSENT.txt").write_text(CONSENT_TEXT)

    started = time.time()
    renderer = Renderer(
        base=args.base,
        controlnet_base=args.controlnet,
        lora_dir=args.lora_dir,
        dtype_name=args.dtype,
        controlnet_scale=args.controlnet_scale,
        seed=args.seed,
        steps=args.steps,
        cfg=args.cfg,
        negative_prompt=args.negative_prompt,
    )
    outputs: list[tuple[Variant, Image.Image]] = []
    try:
        renderer.load_pipe()
        for variant in VARIANTS:
            print(f"[render] {variant.label}", flush=True)
            image = renderer.render(scaffold=scaffold, control=control, prompt=prompt_for(args.trigger), variant=variant)
            image.save(args.out_dir / f"04_{variant.id}.jpg", "JPEG", quality=94, optimize=True)
            outputs.append((variant, image))
    finally:
        renderer.close()

    build_contact_sheet(out_dir=args.out_dir, source=source, scaffold=scaffold, control=control, outputs=outputs)
    manifest["elapsed_seconds"] = round(time.time() - started, 2)
    manifest["outputs"] = [f"04_{variant.id}.jpg" for variant in VARIANTS]
    manifest["contact_sheet"] = "contact_sheet_source_scaffold_control_outputs.jpg"
    (args.out_dir / "_run_manifest.json").write_text(json.dumps(manifest, indent=2))
    write_readme(args.out_dir, manifest)
    print(f"Done: {args.out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
