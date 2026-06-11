"""
v2 image prep — approved raster → 512×512 training plate + caption stub.

Bridges austin-v2-ingest/approved/ → austin-v2-ingest/training/.

Key behaviors:
  - Preserves aspect by scale-and-pad (NOT center-crop) so design isn't clipped.
    Pad color matches detected background (white for clean plates).
  - Flattens alpha against detected background.
  - EXIF transposed.
  - Writes paired .txt caption stub per the v2 caption rubric (filled with
    placeholders for human edit; trigger token preset).
  - Refuses to operate on a file that's actually a JSON wrapper (the bug
    materialize_json_images.py was added to recover from); points at that
    script if detected.

Usage:
  python3 scripts/prep_v2_image.py
    -> walks austin-v2-ingest/approved/, writes 512px JPGs + caption stubs
       to austin-v2-ingest/training/

  python3 scripts/prep_v2_image.py --dry-run
    -> preview what would happen without writing

  python3 scripts/prep_v2_image.py --src <dir> --dst <dir> --trigger <token>
    -> override defaults
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

DEFAULT_SRC = Path(__file__).resolve().parents[1] / "austin-v2-ingest" / "approved"
DEFAULT_DST = Path(__file__).resolve().parents[1] / "austin-v2-ingest" / "training"
DEFAULT_TRIGGER = "austin_v2"
TARGET = 512
JPEG_QUALITY = 95


# Caption stub template — element-level fields per v2 caption rubric.
# Each placeholder must be filled in by the human before training.
CAPTION_STUB = """{trigger}, <subject (e.g. orca + salmon, plant motif)>, <primitives present (e.g. ovoid eye, U-form body, crescent fin)>, <line behavior (e.g. heavy outline, tapered line)>, <palette (e.g. red and black on white)>, <negative space (e.g. breathing negative space, figure-on-ground)>, <medium (e.g. vector illustration, flat design plate)>"""


def is_json_wrapper(p: Path) -> bool:
    """Detect the failure mode where a file is actually a Jupyter Contents-API
    JSON payload masquerading as an image. Triggered the materialize bug."""
    try:
        with p.open("rb") as f:
            return f.read(1) == b"{"
    except OSError:
        return False


def detect_background_color(im: Image.Image) -> tuple[int, int, int]:
    """Sample the four corners of the image; if they agree, that's likely the
    background. Default to white if ambiguous (clean design plate convention)."""
    px = im.load()
    samples = [px[0, 0], px[im.width - 1, 0], px[0, im.height - 1], px[im.width - 1, im.height - 1]]
    samples = [s[:3] if isinstance(s, tuple) else (s, s, s) for s in samples]
    counts = Counter(samples)
    most_common, n = counts.most_common(1)[0]
    if n >= 3:  # 3 of 4 corners agree
        return most_common
    # Default to white (clean design plate norm)
    return (255, 255, 255)


def prep(src: Path, dst: Path, trigger: str, dry_run: bool = False) -> dict:
    info = {"src": str(src), "ok": False, "reason": None}
    if is_json_wrapper(src):
        info["reason"] = (
            f"file is a JSON wrapper, not an image. Run: "
            f"python3 scripts/materialize_json_images.py {src.parent} --out <real-dir>"
        )
        return info

    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            bg = detect_background_color(im if im.mode == "RGB" else im.convert("RGB"))

            # Flatten alpha against detected background
            if im.mode in ("RGBA", "LA", "P"):
                bg_layer = Image.new("RGB", im.size, bg)
                rgba = im.convert("RGBA")
                bg_layer.paste(rgba, mask=rgba.split()[-1])
                im = bg_layer
            else:
                im = im.convert("RGB")

            # Scale-and-pad to TARGET×TARGET (preserve aspect; no clipping)
            scale = min(TARGET / im.width, TARGET / im.height)
            new_w, new_h = max(1, int(round(im.width * scale))), max(1, int(round(im.height * scale)))
            im_scaled = im.resize((new_w, new_h), Image.LANCZOS)
            canvas = Image.new("RGB", (TARGET, TARGET), bg)
            canvas.paste(im_scaled, ((TARGET - new_w) // 2, (TARGET - new_h) // 2))

            info.update(
                src_dims=f"{im.width}x{im.height}",
                bg=bg,
                out_dims=f"{TARGET}x{TARGET}",
                pad_color=bg,
            )

            if dry_run:
                info["ok"] = True
                info["reason"] = "(dry-run; not written)"
                return info

            dst.mkdir(parents=True, exist_ok=True)
            out_jpg = dst / src.with_suffix(".jpg").name
            canvas.save(out_jpg, "JPEG", quality=JPEG_QUALITY, optimize=True)

            # Caption stub
            cap_path = out_jpg.with_suffix(".txt")
            if not cap_path.exists():
                cap_path.write_text(CAPTION_STUB.format(trigger=trigger) + "\n")
                info["caption_stub_written"] = True
            else:
                info["caption_stub_written"] = "(skipped — caption file already exists)"

            info["ok"] = True
            info["out"] = str(out_jpg)
    except Exception as e:
        info["reason"] = f"{type(e).__name__}: {e}"
    return info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC,
                    help=f"Approved raster source dir (default: {DEFAULT_SRC})")
    ap.add_argument("--dst", type=Path, default=DEFAULT_DST,
                    help=f"Training plate output dir (default: {DEFAULT_DST})")
    ap.add_argument("--trigger", default=DEFAULT_TRIGGER,
                    help=f"LoRA trigger token (default: {DEFAULT_TRIGGER!r})")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.src.exists():
        raise SystemExit(f"src does not exist: {args.src}")
    files = [p for p in sorted(args.src.iterdir())
             if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}]
    if not files:
        raise SystemExit(f"no raster files in {args.src}")

    print(f"prep_v2_image.py — src={args.src}  dst={args.dst}  trigger={args.trigger!r}  dry_run={args.dry_run}\n")
    ok = fail = 0
    for p in files:
        r = prep(p, args.dst, args.trigger, dry_run=args.dry_run)
        flag = "+" if r["ok"] else "x"
        print(f"  {flag} {p.name}")
        for k in ("src_dims", "out_dims", "bg", "out", "caption_stub_written", "reason"):
            if k in r and r[k] is not None:
                print(f"      {k}: {r[k]}")
        if r["ok"]:
            ok += 1
        else:
            fail += 1
    print(f"\nDone. ok={ok}  fail={fail}")
    if not args.dry_run and ok:
        print(f"\nNext: open each .txt sidecar in {args.dst}/ and replace the placeholders")
        print(f"      per austin-v2-ingest/caption-rubric.md")


if __name__ == "__main__":
    main()
