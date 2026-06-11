"""
Parameterized LoRA evaluation matrix runner.

Runs the locked eval matrix from austin-reference/clean-subset-lora-v1_5/EVAL_SPEC.md
against an arbitrary trained Austin LoRA (v1.5, v2, future versions). Parameterized
so the same script serves every version — no copy-paste-rename per train.

Designed to be uploaded to a TELUS H200 pod and run there. The --dry-run mode runs
locally without GPU/diffusers and prints what would be rendered (used to validate
the matrix before pod upload).

USAGE (on pod):
  python eval_lora.py \\
    --version v2 \\
    --lora-dir austin-v2-lora-out \\
    --out-dir austin-v2-eval

  -> 7 prompts × 4 scales = 28 renders + contact sheet at austin-v2-eval/_contact_sheet.jpg

USAGE (local dry-run):
  python3 scripts/eval_lora.py --version v2 --lora-dir none --out-dir /tmp/x --dry-run
  -> prints the full matrix that would render; no model load; exits 0

Other options:
  --scales "0.4,0.6,0.8,1.0"     override scale list (comma-separated)
  --seed 42                       per-prompt seed (constant across scales for direct comparison)
  --steps 30                      inference steps
  --cfg 7.5                       guidance scale
  --neg-prompt "..."              override negative prompt (default: watermark-killer)
  --no-contact-sheet              skip the contact sheet build
  --base BASE                     override base model id (default: SD 1.5)

Output naming:
  <out-dir>/{domain}_{tag}_s{int(scale*10):02d}.jpg
  <out-dir>/_contact_sheet.jpg
  <out-dir>/_run_manifest.json    records the exact prompts/scales/seed used

Cross-version notes:
  - v15 used trigger 'austin_v15'; v2 uses 'austin_v2'. Set via --version.
  - EVAL_SPEC.md hard rule: same prompts across versions for direct comparison.
    If you must change prompts, fork the spec and document why; do not edit prompts
    in this script. Per `feedback_austin_consent_trust_floor.md` discipline: stable
    eval lets us tell whether v(N) is genuinely better than v(N-1).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

# 7 prompts from EVAL_SPEC.md. {trigger} is filled in per --version.
PROMPTS = [
    ("seen", "plant_motif",
     "{trigger}, plant motif design plate, monochrome black on white, formline primitives, vector illustration, breathing negative space"),
    ("seen", "raven_motif",
     "{trigger}, raven crest design plate, formline ovoid eye, U-form wing, dark palette on white background, vector illustration"),
    ("seen", "composite_seen",
     "{trigger}, plant and bird composite design plate, formline primitives, monochrome with accent color, vector illustration"),
    ("unseen", "orca",
     "{trigger}, orca crest design plate, formline ovoid eye, U-form body, red and blue palette on white, vector illustration"),
    ("unseen", "salmon",
     "{trigger}, salmon design plate, side profile, formline ovoid eye, U-form fins, deep red on white, vector illustration"),
    ("unseen", "thunderbird",
     "{trigger}, thunderbird design plate, spread wings, formline primitives, gold and black on white, vector illustration"),
    ("unseen", "pearl_interior",
     "{trigger}, abstract pearl interior with three formline shapes — crescent, ovoid, U-form — swirling, contemporary digital art, breathing negative space"),
]

DEFAULT_SCALES = [0.4, 0.6, 0.8, 1.0]
DEFAULT_NEG = ("watermark, text, logo, signature, stock photo, dreamstime, "
               "shutterstock, getty, alamy, copyright, low quality, blurry, distorted")
DEFAULT_BASE = "stable-diffusion-v1-5/stable-diffusion-v1-5"


def trigger_for(version: str) -> str:
    """version='v15' -> 'austin_v15'; 'v2' -> 'austin_v2'; etc."""
    v = version.lower().lstrip("v")
    return f"austin_v{v}"


def expand_prompts(version: str) -> list[tuple[str, str, str]]:
    trig = trigger_for(version)
    return [(domain, tag, tmpl.format(trigger=trig)) for domain, tag, tmpl in PROMPTS]


def parse_scales(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def file_name_for(domain: str, tag: str, scale: float) -> str:
    return f"{domain}_{tag}_s{int(scale * 10):02d}.jpg"


def write_manifest(out_dir: Path, *, version: str, lora_dir: str, base: str,
                   scales: list[float], seed: int, steps: int, cfg: float,
                   neg: str, prompts_expanded: list[tuple[str, str, str]]):
    manifest = {
        "version": version,
        "trigger": trigger_for(version),
        "lora_dir": lora_dir,
        "base": base,
        "scales": scales,
        "seed": seed,
        "steps": steps,
        "cfg": cfg,
        "neg_prompt": neg,
        "prompts": [{"domain": d, "tag": t, "prompt": p} for d, t, p in prompts_expanded],
        "render_count": len(prompts_expanded) * len(scales),
        "naming": "{domain}_{tag}_s{int(scale*10):02d}.jpg",
    }
    (out_dir / "_run_manifest.json").write_text(json.dumps(manifest, indent=2))


def build_contact_sheet(out_dir: Path, prompts_expanded: list, scales: list[float]):
    """Builds rows=prompts × cols=scales contact sheet. Requires PIL."""
    from PIL import Image, ImageDraw, ImageFont
    CELL, LABEL, COL_HEAD, ROW_HEAD, PAD = 280, 32, 36, 220, 6
    n_rows, n_cols = len(prompts_expanded), len(scales)
    W = ROW_HEAD + n_cols * (CELL + PAD) + PAD
    H = COL_HEAD + n_rows * (CELL + LABEL + PAD) + PAD
    sheet = Image.new("RGB", (W, H), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)

    def font(s):
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/System/Library/Fonts/Supplemental/Arial.ttf"):
            try: return ImageFont.truetype(p, s)
            except OSError: continue
        return ImageFont.load_default()

    fH, fL = font(16), font(11)

    for ci, scale in enumerate(scales):
        x = ROW_HEAD + ci * (CELL + PAD)
        draw.text((x + 8, 8), f"scale {scale}", font=fH, fill=(20, 20, 20))

    for ri, (domain, tag, prompt) in enumerate(prompts_expanded):
        y = COL_HEAD + ri * (CELL + LABEL + PAD)
        color = (20, 100, 20) if domain == "seen" else (160, 60, 20)
        draw.text((PAD, y + 8), f"{domain.upper()}: {tag}", font=fH, fill=color)
        # word-wrap prompt
        words = prompt.split()
        line, lines, w_max = "", [], ROW_HEAD - 12
        for w in words:
            test = (line + " " + w).strip()
            if draw.textlength(test, font=fL) < w_max:
                line = test
            else:
                lines.append(line); line = w
        if line: lines.append(line)
        for li, l in enumerate(lines[:9]):
            draw.text((PAD, y + 30 + li * 14), l, font=fL, fill=(80, 80, 80))
        for ci, scale in enumerate(scales):
            f = out_dir / file_name_for(domain, tag, scale)
            if not f.exists(): continue
            with Image.open(f) as im:
                im = im.convert("RGB").resize((CELL, CELL), Image.LANCZOS)
            x = ROW_HEAD + ci * (CELL + PAD)
            sheet.paste(im, (x, y))
            draw.rectangle([x, y + CELL, x + CELL, y + CELL + LABEL], fill=(225, 225, 225))
            draw.text((x + 6, y + CELL + 8), f.name, font=fL, fill=(20, 20, 20))

    sheet.save(out_dir / "_contact_sheet.jpg", "JPEG", quality=88)
    return sheet.size


def render_matrix(*, lora_dir: Path, out_dir: Path, base: str, scales: list[float],
                  seed: int, steps: int, cfg: float, neg: str,
                  prompts_expanded: list[tuple[str, str, str]]):
    """The actual GPU work. Imports torch + diffusers lazily so --dry-run avoids them."""
    import torch
    from diffusers import StableDiffusionPipeline

    t0 = time.time()
    print(f"[load] {base} ...", flush=True)
    pipe = StableDiffusionPipeline.from_pretrained(
        base, torch_dtype=torch.bfloat16,
        safety_checker=None, requires_safety_checker=False,
    ).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    print(f"  loaded in {time.time() - t0:.1f}s", flush=True)

    for scale in scales:
        print(f"\n[scale {scale}]", flush=True)
        pipe.load_lora_weights(str(lora_dir))
        pipe.fuse_lora(lora_scale=scale)
        for domain, tag, prompt in prompts_expanded:
            g = torch.Generator(device="cuda").manual_seed(seed)
            with torch.inference_mode():
                img = pipe(
                    prompt=prompt, negative_prompt=neg,
                    num_inference_steps=steps, guidance_scale=cfg,
                    height=512, width=512, generator=g,
                ).images[0]
            out = out_dir / file_name_for(domain, tag, scale)
            img.save(out, "JPEG", quality=92)
            print(f"  {out.name}")
        pipe.unfuse_lora()
        pipe.unload_lora_weights()

    print(f"\nMatrix complete in {time.time() - t0:.1f}s.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True,
                    help="LoRA version tag, e.g. 'v15', 'v2'. Sets trigger token (austin_v<version>)")
    ap.add_argument("--lora-dir", required=True, type=Path,
                    help="Path to trained LoRA dir (use 'none' or any path with --dry-run)")
    ap.add_argument("--out-dir", required=True, type=Path,
                    help="Where to write renders + contact sheet + manifest")
    ap.add_argument("--scales", default=",".join(str(s) for s in DEFAULT_SCALES),
                    help=f"Comma-separated scales (default: {DEFAULT_SCALES})")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--cfg", type=float, default=7.5)
    ap.add_argument("--neg-prompt", default=DEFAULT_NEG,
                    help="Negative prompt. Default kills watermark/stock-site artifacts.")
    ap.add_argument("--base", default=DEFAULT_BASE,
                    help=f"Base model id (default: {DEFAULT_BASE})")
    ap.add_argument("--no-contact-sheet", action="store_true",
                    help="Skip contact sheet build")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the full matrix and exit; no GPU/diffusers required")
    args = ap.parse_args()

    scales = parse_scales(args.scales)
    prompts_expanded = expand_prompts(args.version)

    print("=" * 70)
    print(f"eval_lora.py — version={args.version}  trigger={trigger_for(args.version)}")
    print("=" * 70)
    print(f"lora_dir : {args.lora_dir}")
    print(f"out_dir  : {args.out_dir}")
    print(f"base     : {args.base}")
    print(f"scales   : {scales}")
    print(f"seed     : {args.seed}   steps: {args.steps}   cfg: {args.cfg}")
    print(f"neg      : {args.neg_prompt[:80]}{'...' if len(args.neg_prompt) > 80 else ''}")
    print(f"prompts  : {len(prompts_expanded)}  ({sum(1 for d,_,_ in prompts_expanded if d=='seen')} seen + "
          f"{sum(1 for d,_,_ in prompts_expanded if d=='unseen')} unseen)")
    print(f"renders  : {len(prompts_expanded) * len(scales)}")

    if args.dry_run:
        print("\n[DRY RUN] would render:")
        for scale in scales:
            for domain, tag, prompt in prompts_expanded:
                print(f"  {file_name_for(domain, tag, scale):40s}  {prompt[:120]}")
        print("\n[DRY RUN] no model loaded; exiting.")
        return

    if args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    write_manifest(
        args.out_dir,
        version=args.version, lora_dir=str(args.lora_dir), base=args.base,
        scales=scales, seed=args.seed, steps=args.steps, cfg=args.cfg,
        neg=args.neg_prompt, prompts_expanded=prompts_expanded,
    )

    render_matrix(
        lora_dir=args.lora_dir, out_dir=args.out_dir, base=args.base,
        scales=scales, seed=args.seed, steps=args.steps, cfg=args.cfg,
        neg=args.neg_prompt, prompts_expanded=prompts_expanded,
    )

    if not args.no_contact_sheet:
        print("\n[contact sheet]", flush=True)
        try:
            size = build_contact_sheet(args.out_dir, prompts_expanded, scales)
            print(f"  built: {size}")
        except Exception as e:
            print(f"  contact sheet failed: {type(e).__name__}: {e}", file=sys.stderr)

    n_files = len(list(args.out_dir.glob("*.jpg")))
    print(f"\nDone — {n_files} files in {args.out_dir}/")


if __name__ == "__main__":
    main()
