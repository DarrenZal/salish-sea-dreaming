"""
Materialize image files that were downloaded as JSON/base64 payloads.

Some TELUS / notebook download paths save a JSON object with fields like
`content`, `mimetype`, and `format` while preserving a `.jpg` filename. This
script detects those wrappers and writes real image bytes to an output folder.

Usage:
  python3 scripts/materialize_json_images.py path/to/eval-renders --out /tmp/eval-images
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def is_json_payload(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            start = fh.read(1)
        return start == b"{"
    except OSError:
        return False


def output_suffix(payload: dict, fallback: str) -> str:
    mimetype = str(payload.get("mimetype", "")).lower()
    if mimetype == "image/png":
        return ".png"
    if mimetype in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    if mimetype == "image/webp":
        return ".webp"
    return fallback


def materialize(path: Path, out_dir: Path, overwrite: bool = False) -> Path | None:
    if not is_json_payload(path):
        return None
    payload = json.loads(path.read_text())
    content = payload.get("content")
    if not isinstance(content, str):
        return None
    suffix = output_suffix(payload, path.suffix)
    out_name = Path(payload.get("name") or path.name).with_suffix(suffix).name
    out_path = out_dir / out_name
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"{out_path} exists; use --overwrite")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(content))
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path,
                    help="Files or directories to scan")
    ap.add_argument("--out", type=Path, required=True,
                    help="Directory for materialized image files")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    candidates: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            candidates.extend(x for x in p.iterdir() if x.is_file())
        else:
            candidates.append(p)

    written = []
    skipped = 0
    for p in sorted(candidates):
        out = materialize(p, args.out, args.overwrite)
        if out:
            written.append(out)
        else:
            skipped += 1

    print(f"materialized={len(written)} skipped={skipped} out={args.out}")
    for p in written:
        print(p)


if __name__ == "__main__":
    main()
