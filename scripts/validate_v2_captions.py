#!/usr/bin/env python3
"""Validate Austin v2 LoRA training image/caption pairs before training.

This catches the failure modes that broke v1:
  - placeholder caption stubs left unedited
  - project-name captions instead of element-level visual grammar
  - missing image/caption pairs
  - non-512 training plates
  - generic cultural terms or subjective prose

Usage:
  python3 scripts/validate_v2_captions.py --root austin-v2-ingest --trigger austin_v2 --min-images 60
  python3 scripts/validate_v2_captions.py --training-dir austin-v2-ingest/training --trigger austin_v2
  python3 scripts/validate_v2_captions.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


DEFAULT_ROOT = Path("austin-v2-ingest")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_TRIGGER = "austin_v2"

BANNED_PROJECT_TERMS = {
    "westridge",
    "whitecaps",
    "kwikwi",
    "mst",
    "marvel",
    "arc'teryx",
    "arcteryx",
    "vancouver coastal health",
    "vch",
    "banff",
    "nelson elementary",
    "salish spirit",
}

BANNED_GENERIC_TERMS = {
    "indigenous art",
    "native american",
    "tribal",
    "tribe",
    "ethnic",
}

SUBJECTIVE_TERMS = {
    "beautiful",
    "striking",
    "stunning",
    "gorgeous",
    "amazing",
    "nice",
    "cool",
    "intricate",
}

SUBJECT_TERMS = {
    "orca",
    "killer whale",
    "wolf",
    "thunderbird",
    "salmon",
    "eagle",
    "bear",
    "frog",
    "raven",
    "sinulhka",
    "two-headed serpent",
    "human",
    "human figure",
    "abstract",
    "border pattern",
    "composite",
    "plant",
    "plant motif",
}

PRIMITIVE_TERMS = {
    "ovoid",
    "inner ovoid",
    "u-form",
    "split-u",
    "crescent",
    "tertiary line",
    "salmon-trout",
    "wedge",
    "triangle",
    "cross-hatching",
    "dashed fill",
    "solid fill",
}

LINE_TERMS = {
    "heavy outline",
    "thin outline",
    "tapered line",
    "closed contour",
    "open ends",
    "parallel ribbing",
    "concentric lines",
    "flowing curves",
    "geometric",
    "angular",
}

PALETTE_TERMS = {
    "red",
    "black",
    "white",
    "blue",
    "teal",
    "gold",
    "monochrome",
    "cyan",
    "earth tones",
    "ochre",
    "indigo",
}

SPACE_TERMS = {
    "negative space",
    "figure-on-ground",
    "interlocking forms",
    "border framing",
    "centered composition",
    "radial composition",
}

MEDIUM_TERMS = {
    "vector illustration",
    "flat design plate",
    "digital painting",
    "pencil sketch",
    "study",
    "installation panel",
    "photo of finished piece",
}


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def lower_words(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_any(text: str, terms: Iterable[str]) -> list[str]:
    lowered = lower_words(text)
    return sorted(term for term in terms if term in lowered)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_'-]+", text))


def paired_image_for(txt: Path, image_paths: set[Path]) -> Path | None:
    for ext in IMAGE_EXTS:
        candidate = txt.with_suffix(ext)
        if candidate in image_paths:
            return candidate
    return None


def load_manifest_names(root: Path) -> set[str]:
    manifest = root / "provenance" / "manifest.csv"
    if not manifest.exists():
        return set()
    names = set()
    try:
        with manifest.open(newline="") as fh:
            for row in csv.DictReader(fh):
                filename = (row.get("filename") or "").strip()
                if filename:
                    names.add(Path(filename).stem)
    except Exception:
        return set()
    return names


def validate_caption_text(txt_path: Path, text: str, trigger: str) -> list[Finding]:
    findings: list[Finding] = []
    label = str(txt_path)
    raw = text.strip()
    lowered = lower_words(raw)

    if not raw:
        findings.append(Finding("ERROR", label, "caption is empty"))
        return findings

    if "\n" in raw:
        findings.append(Finding("ERROR", label, "caption must be exactly one line"))

    if "<" in raw or ">" in raw:
        findings.append(Finding("ERROR", label, "caption still contains placeholder brackets"))

    if not lowered.startswith(trigger.lower() + ","):
        findings.append(Finding("ERROR", label, f"caption must start with trigger token '{trigger},'"))

    comma_parts = [part.strip() for part in raw.split(",") if part.strip()]
    if len(comma_parts) < 7:
        findings.append(Finding("ERROR", label, f"caption has {len(comma_parts)} comma chunks; expected at least 7"))

    project_terms = contains_any(raw, BANNED_PROJECT_TERMS)
    if project_terms:
        findings.append(Finding("ERROR", label, "project-name terms present: " + ", ".join(project_terms)))

    generic_terms = contains_any(raw, BANNED_GENERIC_TERMS)
    if generic_terms:
        findings.append(Finding("ERROR", label, "generic cultural terms present: " + ", ".join(generic_terms)))

    subjective_terms = contains_any(raw, SUBJECTIVE_TERMS)
    if subjective_terms:
        findings.append(Finding("WARN", label, "subjective quality words present: " + ", ".join(subjective_terms)))

    if word_count(raw) > 80:
        findings.append(Finding("WARN", label, "caption is long; keep fields tight and comma-structured"))

    checks = [
        ("subject vocabulary", SUBJECT_TERMS),
        ("primitive vocabulary", PRIMITIVE_TERMS),
        ("line-behavior vocabulary", LINE_TERMS),
        ("palette vocabulary", PALETTE_TERMS),
        ("negative-space vocabulary", SPACE_TERMS),
        ("medium/source vocabulary", MEDIUM_TERMS),
    ]
    for label_name, terms in checks:
        if not contains_any(raw, terms):
            findings.append(Finding("WARN", label, f"no obvious {label_name} term found"))

    return findings


def validate_training_dir(
    training_dir: Path,
    *,
    root: Path | None,
    trigger: str,
    min_images: int,
) -> list[Finding]:
    findings: list[Finding] = []
    if not training_dir.exists():
        return [Finding("ERROR", str(training_dir), "training dir does not exist")]

    image_paths = {p for p in training_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS}
    txt_paths = {p for p in training_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt"}

    if len(image_paths) < min_images:
        findings.append(
            Finding("ERROR", str(training_dir), f"only {len(image_paths)} image(s); min required is {min_images}")
        )

    for image in sorted(image_paths):
        txt = image.with_suffix(".txt")
        if txt not in txt_paths:
            findings.append(Finding("ERROR", str(image), "missing paired .txt caption"))
        try:
            with Image.open(image) as im:
                if im.size != (512, 512):
                    findings.append(Finding("ERROR", str(image), f"image is {im.width}x{im.height}; expected 512x512"))
                if im.mode not in {"RGB", "L"}:
                    findings.append(Finding("WARN", str(image), f"image mode is {im.mode}; expected RGB/L training plate"))
        except Exception as exc:
            findings.append(Finding("ERROR", str(image), f"could not open image: {type(exc).__name__}: {exc}"))

    for txt in sorted(txt_paths):
        image = paired_image_for(txt, image_paths)
        if image is None:
            findings.append(Finding("ERROR", str(txt), "missing paired image file"))
        try:
            text = txt.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("ERROR", str(txt), "caption is not UTF-8 text"))
            continue
        findings.extend(validate_caption_text(txt, text, trigger))

    if root is not None:
        manifest_names = load_manifest_names(root)
        if manifest_names:
            for image in sorted(image_paths):
                if image.stem not in manifest_names:
                    findings.append(Finding("WARN", str(image), "image stem not found in provenance manifest"))
        else:
            findings.append(Finding("WARN", str(root / "provenance" / "manifest.csv"), "no readable provenance manifest"))

    return findings


def print_report(findings: list[Finding], *, as_json: bool = False) -> None:
    counts = {
        "ERROR": sum(1 for f in findings if f.severity == "ERROR"),
        "WARN": sum(1 for f in findings if f.severity == "WARN"),
    }
    if as_json:
        print(json.dumps({"counts": counts, "findings": [f.__dict__ for f in findings]}, indent=2))
        return

    print(f"Caption validation: errors={counts['ERROR']} warnings={counts['WARN']}")
    if not findings:
        print("PASS: captions are ready for training gate.")
        return
    for finding in findings:
        print(f"{finding.severity:5s} {finding.path}: {finding.message}")


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="ssd-caption-validator-") as tmp:
        root = Path(tmp)
        training = root / "training"
        training.mkdir()
        img = Image.new("RGB", (512, 512), "white")
        img.save(training / "orca_plate_001.jpg")
        (training / "orca_plate_001.txt").write_text(
            "austin_v2, orca, ovoid eye, U-form body, crescent fin, "
            "heavy outline, tapered line, red and black on white, "
            "breathing negative space, figure-on-ground, vector illustration\n",
            encoding="utf-8",
        )
        good = validate_training_dir(training, root=None, trigger="austin_v2", min_images=1)
        if any(f.severity == "ERROR" for f in good):
            print_report(good)
            print("self-test failed: valid fixture produced errors", file=sys.stderr)
            return 1

        (training / "bad_stub_001.jpg").write_bytes((training / "orca_plate_001.jpg").read_bytes())
        (training / "bad_stub_001.txt").write_text(
            "austin_v2, <subject>, <primitives>, Westridge Elementary, beautiful Indigenous art\n",
            encoding="utf-8",
        )
        bad = validate_training_dir(training, root=None, trigger="austin_v2", min_images=1)
        if not any(f.severity == "ERROR" for f in bad):
            print_report(bad)
            print("self-test failed: bad fixture did not produce errors", file=sys.stderr)
            return 1
    print("validate_v2_captions self-test: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Ingest root; training defaults to <root>/training")
    parser.add_argument("--training-dir", type=Path, default=None, help="Override training dir")
    parser.add_argument("--trigger", default=DEFAULT_TRIGGER)
    parser.add_argument("--min-images", type=int, default=0, help="Fail if fewer image/caption pairs are present")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--warn-only", action="store_true", help="Return 0 even if errors are present")
    parser.add_argument("--self-test", action="store_true", help="Run built-in pass/fail fixtures")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    root = args.root.resolve() if args.root else None
    training_dir = (args.training_dir or (root / "training" if root else None))
    if training_dir is None:
        parser.error("missing --training-dir or --root")
    training_dir = training_dir.resolve()

    findings = validate_training_dir(
        training_dir,
        root=root,
        trigger=args.trigger,
        min_images=args.min_images,
    )
    print_report(findings, as_json=args.json)
    has_errors = any(f.severity == "ERROR" for f in findings)
    return 0 if args.warn_only or not has_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
