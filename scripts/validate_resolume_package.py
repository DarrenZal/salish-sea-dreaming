#!/usr/bin/env python3
"""Validate a Space Centre Resolume show package before venue handoff.

This is a structural validator, not an artistic approval tool. It checks for
common operator mistakes: missing provenance, wrong panel resolution, mixed
frame rates, and internal/unapproved experiments inside projector-ready folders.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_DIRS = [
    "01_calibration",
    "02_panel_clips",
    "04_sources_provenance",
    "05_approval_records",
]

REQUIRED_FILES = [
    "00_README_OPERATOR.md",
]

PANEL_DIRS = [
    "L_lens_science",
    "C_lineage_pearl",
    "R_water_bioregion",
]

MEDIA_EXTS = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".png", ".jpg", ".jpeg"}
VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".avi", ".mkv"}

HARD_EXCLUSION_TOKENS = [
    "dry_run",
    "dry-run",
    "placeholder",
    "v1.5",
    "v15",
    "animatediff_failed",
    "failed_animatediff",
    "ip_adapter_installation",
    "installation_context",
    "unapproved",
]

WEAK_FILENAME_TOKENS = [
    "final",
    "test2",
    "good",
]

EXPECTED_WIDTH = 1920
EXPECTED_HEIGHT = 1080


@dataclass
class Finding:
    level: str
    path: str
    message: str


def add(findings: list[Finding], level: str, path: Path | str, message: str) -> None:
    findings.append(Finding(level=level, path=str(path), message=message))


def run_ffprobe(path: Path) -> dict | None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,codec_name",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError("ffprobe not found; install ffmpeg or run validation on the media machine")
    except subprocess.CalledProcessError:
        return None
    return json.loads(result.stdout)


def provenance_text(root: Path) -> str:
    provenance_dir = root / "04_sources_provenance"
    approval_dir = root / "05_approval_records"
    chunks: list[str] = []
    for directory in [provenance_dir, approval_dir]:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".csv", ".json"}:
                try:
                    chunks.append(path.read_text(errors="ignore"))
                except OSError:
                    continue
    return "\n".join(chunks)


def check_package(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    root = root.resolve()

    if not root.exists():
        add(findings, "ERROR", root, "package root does not exist")
        return findings
    if not root.is_dir():
        add(findings, "ERROR", root, "package root is not a directory")
        return findings

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            add(findings, "ERROR", path, "required package file is missing")

    for rel in REQUIRED_DIRS:
        path = root / rel
        if not path.is_dir():
            add(findings, "ERROR", path, "required package directory is missing")

    panel_root = root / "02_panel_clips"
    for rel in PANEL_DIRS:
        path = panel_root / rel
        if not path.is_dir():
            add(findings, "WARN", path, "expected panel directory is missing")

    provenance = provenance_text(root)
    media_files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTS)
    panel_media = [p for p in media_files if panel_root in p.parents]

    if not panel_media:
        add(findings, "WARN", panel_root, "no projection media found under 02_panel_clips")

    panel_rates: dict[str, list[Path]] = {}

    for path in panel_media:
        rel = path.relative_to(root)
        lower_name = path.name.lower()

        for token in HARD_EXCLUSION_TOKENS:
            if token in lower_name:
                add(findings, "ERROR", rel, f"hard-exclusion token in projector folder: {token}")

        for token in WEAK_FILENAME_TOKENS:
            if token in lower_name:
                add(findings, "WARN", rel, f"weak filename token; status should be explicit: {token}")

        if path.name not in provenance:
            add(findings, "ERROR", rel, "filename not found in provenance/approval records")

        if path.suffix.lower() in VIDEO_EXTS:
            probe = run_ffprobe(path)
            if probe is None:
                add(findings, "ERROR", rel, "ffprobe could not read media")
                continue

            streams = probe.get("streams", [])
            if not streams:
                add(findings, "ERROR", rel, "no video stream found")
                continue

            stream = streams[0]
            width = int(stream.get("width", 0) or 0)
            height = int(stream.get("height", 0) or 0)
            rate = stream.get("r_frame_rate", "")

            if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
                add(
                    findings,
                    "ERROR",
                    rel,
                    f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}, got {width}x{height}",
                )

            if rate:
                panel_rates.setdefault(rate, []).append(rel)

    if len(panel_rates) > 1:
        summary = ", ".join(f"{rate}: {len(paths)} file(s)" for rate, paths in sorted(panel_rates.items()))
        add(findings, "WARN", panel_root, f"mixed frame rates across panel clips: {summary}")

    internal_root = root / "99_internal_do_not_project"
    if internal_root.exists():
        for path in sorted(p for p in internal_root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTS):
            rel = path.relative_to(root)
            if "do_not_project" not in str(rel).lower():
                add(findings, "INFO", rel, "internal media present; keep out of Resolume show deck")

    return findings


def print_findings(findings: list[Finding]) -> int:
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for finding in findings:
        counts[finding.level] = counts.get(finding.level, 0) + 1
        print(f"{finding.level:5} {finding.path}: {finding.message}")

    print(
        "\nSummary: "
        f"{counts.get('ERROR', 0)} error(s), "
        f"{counts.get('WARN', 0)} warning(s), "
        f"{counts.get('INFO', 0)} info"
    )
    return 1 if counts.get("ERROR", 0) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path, help="show-package-space-centre-vYYYYMMDD directory")
    args = parser.parse_args()

    try:
        findings = check_package(args.package_root)
    except RuntimeError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    return print_findings(findings)


if __name__ == "__main__":
    raise SystemExit(main())
