"""
v2 ingest helper - applies hard reject filters + computes manifest rows for
files arriving in <ingest-root>/inbox/.

Does NOT auto-approve - flags each file with a recommendation that a human
must confirm before it moves to approved/.

Usage:
  python3 scripts/v2_ingest_helper.py
    -> walks austin-v2-ingest/inbox/, prints a per-file triage report,
       appends manifest rows to austin-v2-ingest/provenance/manifest.csv,
       writes triage decisions to austin-v2-ingest/inbox/_triage.json

  python3 scripts/v2_ingest_helper.py --apply
    -> after human review of _triage.json, actually moves files into
       approved/ or rejected/<reason>/ per the triage decisions

  python3 scripts/v2_ingest_helper.py --root <dir>
    -> override ingest root (default: austin-v2-ingest/). Useful for rehearsals
       and parallel ingest sessions without polluting the real directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "austin-v2-ingest"

RASTER_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif"}
VECTOR_EXTS = {".svg", ".pdf", ".eps", ".ai"}
SUPPORTED_EXTS = RASTER_EXTS | VECTOR_EXTS

# Hard-reject heuristics (not perfect - human must confirm)
MIN_SHORT_SIDE = 512        # < 512px shortest side -> too small for 512x512 training
MIN_FRAME_COVERAGE = 0.40   # heuristic: image must be > 40% non-edge variance
                            # (very rough proxy for "design fills frame")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def estimate_frame_coverage(im: Image.Image) -> float:
    """Rough proxy: ratio of non-edge-region variance to total variance.
    High = subject in middle (clean design plate). Low = subject is small in
    frame (installation context with lots of background).
    Uses grayscale variance on a center-crop vs full image.
    """
    gray = im.convert("L")
    w, h = gray.size
    cw, ch = int(w * 0.6), int(h * 0.6)
    cx, cy = (w - cw) // 2, (h - ch) // 2
    center = gray.crop((cx, cy, cx + cw, cy + ch))
    import statistics
    full_var = statistics.pvariance(gray.getdata())
    if full_var < 1e-6:
        return 0.0
    center_var = statistics.pvariance(center.getdata())
    # Center should be at least as varied as full if subject is centered
    return min(1.0, center_var / max(full_var, 1e-6))


def triage_file(p: Path) -> dict:
    info = {
        "filename": p.name,
        "size_bytes": p.stat().st_size,
        "sha256": sha256(p),
        "ext": p.suffix.lower(),
        "checks": [],
        "recommendation": "review",  # default - human must decide
        "reasons": [],
    }
    if info["ext"] in VECTOR_EXTS:
        info["kind"] = "vector"
        info["checks"].append("vector-like source file - inspect manually; preferred if it is Austin source artwork")
        return info

    info["kind"] = "raster"
    try:
        with Image.open(p) as im:
            info["dimensions"] = f"{im.width}x{im.height}"
            info["mode"] = im.mode
            short = min(im.width, im.height)
            info["shortest_side"] = short
            if short < MIN_SHORT_SIDE:
                info["recommendation"] = "reject"
                info["reasons"].append(f"shortest side {short}px < {MIN_SHORT_SIDE}px")
            coverage = estimate_frame_coverage(im)
            info["frame_coverage_estimate"] = round(coverage, 2)
            if coverage < MIN_FRAME_COVERAGE:
                info["recommendation"] = "reject"
                info["reasons"].append(f"frame coverage estimate {coverage:.2f} < {MIN_FRAME_COVERAGE}")
    except Exception as e:
        info["recommendation"] = "reject"
        info["reasons"].append(f"open error: {type(e).__name__}: {e}")

    # Filename pattern hints (don't auto-reject; flag for human attention)
    name_lower = p.name.lower()
    pattern_hints = {
        "screenshot": "may be design capture or UI screenshot - verify visually",
        "_design": "filename suggests design plate - likely keep candidate",
        "_description": "filename suggests text-heavy description page - likely reject",
        "logo": "verify isn't a third-party brand logo (Arc'teryx, etc.)",
        "_concept": "may be concept board with text/photos - verify visually",
    }
    for k, v in pattern_hints.items():
        if k in name_lower:
            info["checks"].append(f"{k}: {v}")
    return info


def paths_for(root: Path) -> dict:
    return {
        "root": root,
        "inbox": root / "inbox",
        "approved": root / "approved",
        "rejected": root / "rejected",
        "manifest": root / "provenance" / "manifest.csv",
        "triage": root / "inbox" / "_triage.json",
    }


def cmd_triage(root: Path):
    paths = paths_for(root)
    inbox = paths["inbox"]
    if not inbox.exists():
        raise SystemExit(f"inbox/ not found: {inbox}")
    files = [p for p in inbox.iterdir()
             if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS and not p.name.startswith("_")]
    if not files:
        print(f"No supported files in {inbox}/. Drop curated files there and re-run.")
        return
    print(f"Triaging {len(files)} files in {inbox}/...\n")
    decisions = []
    for p in sorted(files):
        info = triage_file(p)
        decisions.append(info)
        flag = {"reject": "x", "review": "?", "approve": "+"}[info["recommendation"]]
        print(f"  {flag} {info['filename']}")
        print(f"      kind={info.get('kind','?')}  dims={info.get('dimensions','?')}  cov={info.get('frame_coverage_estimate','?')}")
        for chk in info["checks"]:
            print(f"      hint: {chk}")
        for reason in info["reasons"]:
            print(f"      reason: {reason}")
    paths["triage"].write_text(json.dumps(decisions, indent=2))
    print(f"\nWrote {paths['triage']}")
    print(f"\nNext: review {paths['triage'].name}, edit `recommendation` per file to 'approve' / 'reject',")
    if root == DEFAULT_ROOT:
        print(f"      then run: python3 scripts/v2_ingest_helper.py --apply")
    else:
        print(f"      then run: python3 scripts/v2_ingest_helper.py --apply --root {root}")


def cmd_apply(root: Path):
    paths = paths_for(root)
    triage = paths["triage"]
    inbox = paths["inbox"]
    approved = paths["approved"]
    rejected = paths["rejected"]
    manifest = paths["manifest"]

    if not triage.exists():
        raise SystemExit(f"No triage file at {triage}. Run without --apply first.")
    decisions = json.loads(triage.read_text())

    manifest.parent.mkdir(parents=True, exist_ok=True)
    write_header = not manifest.exists() or manifest.stat().st_size == 0
    today = datetime.now().strftime("%Y-%m-%d")
    with manifest.open("a", newline="") as fh:
        w = csv.writer(fh)
        if write_header:
            w.writerow(["filename", "source", "sha256", "date_received", "austin_consent", "notes"])
        moved = {"approve": 0, "reject": 0, "skip": 0}
        for d in decisions:
            src = inbox / d["filename"]
            if not src.exists():
                continue
            rec = d.get("recommendation", "review")
            if rec == "approve":
                dst = approved / d["filename"]
                approved.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                w.writerow([d["filename"], "Austin curated drive", d.get("sha256", ""),
                            today, "pending", "; ".join(d.get("checks", []))])
                moved["approve"] += 1
            elif rec == "reject":
                reason_slug = "_".join(d.get("reasons", ["manual"])[0].split()[:3]).replace("/", "_")[:30]
                dst_dir = rejected / reason_slug
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst_dir / d["filename"]))
                moved["reject"] += 1
            else:
                moved["skip"] += 1
        print(f"\nApplied: {moved}")
        print(f"Manifest now at {manifest}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="After human review of _triage.json, actually move files")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help=f"Ingest root (default: {DEFAULT_ROOT}). Override for rehearsals.")
    args = ap.parse_args()
    if args.apply:
        cmd_apply(args.root.resolve())
    else:
        cmd_triage(args.root.resolve())
