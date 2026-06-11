#!/usr/bin/env python3
"""
Label decomposed Austin atoms with an LLM (OpenAI GPT-4o-mini vision).

For each atom PNG, sends the image to the LLM with a Coast Salish formline
classification prompt. Appends labels to atom_metadata.csv.

Reads OPENAI_API_KEY from the operator's env (project .env files searched).

Usage:
  python3 scripts/label_atoms_with_claude.py            # label all unlabeled
  python3 scripts/label_atoms_with_claude.py --piece Nature_Cosmic_Sun
  python3 scripts/label_atoms_with_claude.py --limit 5  # smoke-test first
  python3 scripts/label_atoms_with_claude.py --dry-run  # show prompt only

INTERNAL ONLY. Atom classification is for our understanding of Austin's
grammar; not authorship; not public-facing without Austin per-output OK.

Note: script name still says "claude" (created when Anthropic key was
expected). Functionally identical; just uses OpenAI instead. Rename later.
"""
from __future__ import annotations
import argparse
import base64
import csv
import json
import os
import re
import sys
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
DECOMP = ROOT / "austin-v2-ingest/decomposed"
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"  # vision-capable, fast, cheap

CLASSIFICATION_LABELS = [
    "circle-oval",
    "crescent",
    "trigon",
    "formline-primary",   # thick contour defining main figure boundary
    "formline-secondary", # secondary U-form inside primary
    "formline-tertiary",  # tertiary inner-element
    "eye-focal-oval",
    "wing-feather",
    "fin-tail",
    "body-element",
    "sun-ray",
    "egg-roe",
    "negative-space",
    "background-field",
    "other",
]

PROMPT_TEMPLATE = """You are classifying a shape extracted from a Coast Salish artwork by Austin Harry. The shape is rendered isolated on a white background.

Classify the shape as ONE of the following formline grammar categories:
{labels}

Coast Salish formline notes (your reference):
- Circle/Oval = central energetic core; often eye, sun, joint, womb, egg
- Crescent = embracing/cupping element; often used in negative space; arc with concave and convex sides
- Trigon = triangular/directional element; often pointing or ascending
- Formline-primary = thick contour defining main figure boundary
- Formline-secondary/tertiary = U-forms and inner elements
- Wing/feather, fin/tail, body, sun-ray = figural elements
- Egg/roe = small round repeated elements (salmon roe, fish eggs)
- Negative-space = engineered gap / cutout in larger composition
- Background-field = solid color region, no formline structure

Reply ONLY with a JSON object:
{{"label": "<one-of-above>", "confidence": <0.0-1.0>, "reason": "<one-sentence>"}}

Do not include any other text. No markdown fences.
""".format(labels="\n".join(f"  - {l}" for l in CLASSIFICATION_LABELS))


def load_api_key() -> str:
    if not ENV_FILE.exists():
        print(f"ERROR: env file not found at {ENV_FILE}")
        sys.exit(1)
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    print(f"ERROR: ANTHROPIC_API_KEY not in {ENV_FILE}")
    sys.exit(1)


def classify_atom(image_path: Path, api_key: str, dry_run: bool = False) -> dict:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
                {"type": "text", "text": PROMPT_TEMPLATE},
            ],
        }],
    }
    if dry_run:
        print(f"  [DRY-RUN] would classify {image_path.name}, prompt size {len(PROMPT_TEMPLATE)} chars")
        return {"label": "(dry-run)", "confidence": 0.0, "reason": "dry-run mode"}

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"label": "API-ERROR", "confidence": 0.0, "reason": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        return {"label": "API-ERROR", "confidence": 0.0, "reason": f"{type(e).__name__}: {e}"}

    text = data.get("content", [{}])[0].get("text", "").strip()
    # Extract JSON from response
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(0))
            return {
                "label": parsed.get("label", "PARSE-ERROR"),
                "confidence": float(parsed.get("confidence", 0.0)),
                "reason": parsed.get("reason", ""),
            }
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return {"label": "PARSE-ERROR", "confidence": 0.0, "reason": f"{e}; raw: {text[:200]}"}
    return {"label": "PARSE-ERROR", "confidence": 0.0, "reason": f"no JSON in: {text[:200]}"}


def label_piece(piece_dir: Path, api_key: str, limit: int | None = None, dry_run: bool = False) -> int:
    meta_path = piece_dir / "atom_metadata.csv"
    if not meta_path.exists():
        print(f"  SKIP: no atom_metadata.csv in {piece_dir.name}")
        return 0
    # Read existing rows
    with open(meta_path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not rows:
        print(f"  SKIP: empty metadata in {piece_dir.name}")
        return 0
    labeled_count = 0
    for i, row in enumerate(rows):
        if row.get("ai_label"):
            continue  # already labeled
        if limit is not None and labeled_count >= limit:
            break
        iso_png = row.get("isolated_png")
        if not iso_png:
            continue
        image_path = piece_dir / iso_png
        if not image_path.exists():
            continue
        print(f"  [{i+1}/{len(rows)}] {row['atom_id']} ({row.get('element_type')}, fill={row.get('fill_color')}) ...", end="", flush=True)
        result = classify_atom(image_path, api_key, dry_run=dry_run)
        row["ai_label"] = result["label"]
        row["ai_confidence"] = f"{result['confidence']:.2f}"
        row["ai_reason"] = result["reason"]
        print(f" → {result['label']} ({result['confidence']:.2f})")
        labeled_count += 1
    # Write back
    if labeled_count > 0:
        with open(meta_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return labeled_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", help="Label only this piece (e.g., Nature_Cosmic_Sun)")
    ap.add_argument("--limit", type=int, help="Max atoms to label per piece (smoke test)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen; no API calls")
    args = ap.parse_args()

    api_key = "" if args.dry_run else load_api_key()
    pieces = sorted([d for d in DECOMP.iterdir() if d.is_dir()])
    if args.piece:
        pieces = [p for p in pieces if p.name == args.piece]
        if not pieces:
            print(f"ERROR: piece '{args.piece}' not found in {DECOMP}")
            sys.exit(1)

    total = 0
    for piece_dir in pieces:
        print(f"Labeling {piece_dir.name}:")
        n = label_piece(piece_dir, api_key, limit=args.limit, dry_run=args.dry_run)
        print(f"  → {n} new labels")
        total += n
    print(f"\nTotal newly-labeled: {total}")


if __name__ == "__main__":
    main()
