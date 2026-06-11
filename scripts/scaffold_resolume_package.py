#!/usr/bin/env python3
"""Create a clean Space Centre Resolume show-package skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path


DIRS = [
    "01_calibration",
    "02_panel_clips/L_lens_science",
    "02_panel_clips/C_lineage_pearl",
    "02_panel_clips/R_water_bioregion",
    "03_wide_masters",
    "04_sources_provenance",
    "05_approval_records",
    "99_internal_do_not_project/dry_run_track2",
    "99_internal_do_not_project/failed_or_unapproved_tests",
]


FILES = {
    "00_README_OPERATOR.md": """# Space Centre Resolume Show Package

Status: scaffold only. Do not project until media, provenance, and approval records are populated.

## Load Order

1. Import calibration assets from `01_calibration/`.
2. Import show clips only from `02_panel_clips/`.
3. Do not import `99_internal_do_not_project/` into the show deck.

## Panel Folders

- `L_lens_science/` = left panel, lens / Western science / tide / footage
- `C_lineage_pearl/` = center panel, lineage / pearl / Austin-approved content only
- `R_water_bioregion/` = right panel, water / bioregion / footage

## Validation

Run before handoff:

```bash
python3 scripts/validate_resolume_package.py this-package-folder/
```

Passing validation is structural only. It does not replace Austin, venue, contributor, or operator approval.
""",
    "01_calibration/README.md": """# Calibration

Put projector calibration plates here. The John diagnostic pack is separate from the show package; copy only the calibration plate if it is useful for venue setup.
""",
    "02_panel_clips/README.md": """# Panel Clips

Only projection-safe show clips go in this folder.

Required subfolders:

- `L_lens_science/`
- `C_lineage_pearl/`
- `R_water_bioregion/`

Every media filename in this folder must appear in `04_sources_provenance/` and, if Austin-related, `05_approval_records/`.
""",
    "03_wide_masters/README.md": """# Wide Masters

Optional 5760x1080 masters live here before slicing into per-panel clips.

Resolume show playback should use the sliced files in `02_panel_clips/`.
""",
    "04_sources_provenance/footage_sources.md": """# Footage Sources

| filename | source contributor | source path | confirmation date | allowed use scope | credit line | compensation status | notes |
|---|---|---|---|---|---|---|---|
""",
    "04_sources_provenance/ai_workflow_sources.md": """# AI Workflow Sources

| filename | workflow | source assets | model / LoRA | internal or public | approval dependency | notes |
|---|---|---|---|---|---|---|
""",
    "04_sources_provenance/live_data_sources.md": """# Live Data Sources

| filename / layer | data source | endpoint / station | visual parameter | fallback | notes |
|---|---|---|---|---|---|
""",
    "04_sources_provenance/licenses.md": """# Licenses

| asset | contributor / service | license or permission state | attribution required | notes |
|---|---|---|---|---|
""",
    "05_approval_records/austin_output_approvals.md": """# Austin Output Approvals

Canonical approval source: `docs/space-center/austin-consent-map.md`.

| filename | consent-map row | source piece | workflow | approval state | allowed context | approval date | notes |
|---|---|---|---|---|---|---|---|
""",
    "05_approval_records/public_language_approvals.md": """# Public Language Approvals

Canonical approval source: `docs/space-center/austin-consent-map.md`.

| line ID | draft file | approval state | reviewer | approval date | notes |
|---|---|---|---|---|---|
""",
    "99_internal_do_not_project/README.md": """# Internal Only

This folder can hold learning artifacts, failed tests, dry-run renders, and review references.

Do not import this folder into Resolume. Do not send it as public artwork or venue preview.
""",
}


def write_file(path: Path, text: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def scaffold(root: Path, *, force: bool, dry_run: bool) -> tuple[list[Path], list[Path]]:
    created_dirs: list[Path] = []
    written_files: list[Path] = []

    for rel in DIRS:
        path = root / rel
        created_dirs.append(path)
        if not dry_run:
            path.mkdir(parents=True, exist_ok=True)

    for rel, text in FILES.items():
        path = root / rel
        written_files.append(path)
        if not dry_run:
            write_file(path, text, force=force)

    return created_dirs, written_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path, help="output package directory")
    parser.add_argument("--force", action="store_true", help="overwrite existing template files")
    parser.add_argument("--dry-run", action="store_true", help="print planned directories/files without writing")
    args = parser.parse_args()

    dirs, files = scaffold(args.package_root, force=args.force, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}package root: {args.package_root}")
    print(f"{prefix}directories: {len(dirs)}")
    for path in dirs:
        print(f"  {path}")
    print(f"{prefix}template files: {len(files)}")
    for path in files:
        print(f"  {path}")

    if not args.dry_run:
        print("\nNext: add media, fill provenance/approval rows, then run validate_resolume_package.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
