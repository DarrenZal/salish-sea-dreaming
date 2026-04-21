#!/usr/bin/env python3
"""Patch static/ssd-data-map-zoom.json in place with v2 semantic predicates.

The v1 ontology plan used generic `conceptual` and `training` predicates
as catch-alls for hub-level edges. Semantic review (2026-04-21) produced
specific predicates that read more naturally and render with correct
direction:

  - knowledge -> ecosystem           conceptual   -> studies
  - ecosystem -> machine             conceptual   -> inspires
  - ecosystem -> exhibition          conceptual   -> subjectOf
  - ecosystem -> visitor-dreams      conceptual   -> inspires
  - install   -> {each hub 6x}       conceptual   -> involves
  - ecosystem -> training            training     -> sampledBy
  - artists   -> training            training     -> contributesTo
  - training  -> machine             signal       -> trains

Constraint: do NOT re-run build_datamap_v2.py (R1-01 — live zoom JSON
contains PDF-ingested nodes not reproducible from that builder). This
script edits the live JSON in place with surgical, idempotent changes.

Modes:
  default  write the retyped JSON back (idempotent).
  --verify read the JSON and assert every row in the retype table is
           present with its new linkType; exits non-zero on mismatch.
  --dry    print the diff summary but don't write.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ZOOM_PATH = REPO_ROOT / "static" / "ssd-data-map-zoom.json"

# Each row: (source_id, target_id, old_linkType_expected, new_linkType).
# Expected old value is checked only on write; --verify mode just checks new.
RETYPING: list[tuple[str, str, str, str]] = [
    # ── Hub-level conceptual → specific predicates ──────────────────────
    ("hub:knowledge",                "hub:ecosystem",         "conceptual", "studies"),
    ("hub:ecosystem",                "hub:machine",           "conceptual", "inspires"),
    ("hub:ecosystem",                "hub:exhibition",        "conceptual", "subjectOf"),
    ("hub:ecosystem",                "hub:visitor-dreams",    "conceptual", "inspires"),
    ("install:salish-sea-dreaming",  "hub:ecosystem",         "conceptual", "involves"),
    ("install:salish-sea-dreaming",  "hub:artists",           "conceptual", "involves"),
    ("install:salish-sea-dreaming",  "hub:training",          "conceptual", "involves"),
    ("install:salish-sea-dreaming",  "hub:machine",           "conceptual", "involves"),
    ("install:salish-sea-dreaming",  "hub:visitor-dreams",    "conceptual", "involves"),
    ("install:salish-sea-dreaming",  "hub:knowledge",         "conceptual", "involves"),
    # ── Person → thing conceptual → contributesTo ──────────────────────
    ("person:darren-zal",            "artifact:dreaming-gan", "conceptual", "contributesTo"),
    ("person:darren-zal",            "node:gallery-server",   "conceptual", "contributesTo"),
    ("person:darren-zal",            "hub:knowledge",         "conceptual", "contributesTo"),
    ("person:shawn-anderson",        "hub:knowledge",         "conceptual", "contributesTo"),
    ("person:zoe-zafiris-casey",     "hub:exhibition",        "conceptual", "contributesTo"),
    ("person:prav-pillay",           "hub:exhibition",        "conceptual", "contributesTo"),
    # ── Hub-level training (backwards) → correct predicates ─────────────
    ("hub:ecosystem",                "hub:training",          "training",   "sampledBy"),
    ("hub:artists",                  "hub:training",          "training",   "contributesTo"),
    ("hub:training",                 "hub:machine",           "signal",     "trains"),
    # ── Pipeline training edges → trains (correct direction already) ────
    ("cluster:salmon-forage",        "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:marine-mammals",       "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:seabirds",             "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:kelp-seagrass",        "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:intertidal",           "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:cephalopods",          "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:rockfish-reef",        "artifact:dreaming-gan", "training",   "trains"),
    ("cluster:bears",                "artifact:dreaming-gan", "training",   "trains"),
    ("artifact:dreaming-corpus",     "artifact:dreaming-gan", "training",   "trains"),
    # ── Corpus contribution edges → contributesTo ───────────────────────
    ("cluster:moonfish-footage",     "hub:training",          "training",   "contributesTo"),
    ("cluster:denning-photos",       "hub:training",          "training",   "contributesTo"),
    ("datasrc:inaturalist",          "artifact:dreaming-corpus","training", "contributesTo"),
    ("datasrc:openverse",            "artifact:dreaming-corpus","training", "contributesTo"),
    ("datasrc:briony-penn",          "artifact:dreaming-corpus","training", "contributesTo"),
]

# Edges explicitly kept on `conceptual` because no specific predicate fits
# better. These count against the `remaining conceptual == 0` rule below, so
# verify() whitelists exactly this set.
CONCEPTUAL_KEEP: set[tuple[str, str]] = {
    # The Digital Ecologies book is a theoretical frame for the installation
    # — not its subject, not an ingredient. Genuine "related to" case.
    ("doc:digital-ecologies-book", "install:salish-sea-dreaming"),
}


def _iter_matching(links: list[dict], src: str, tgt: str):
    for l in links:
        if l.get("source") == src and l.get("target") == tgt:
            yield l


def apply(dry: bool = False) -> int:
    data = json.loads(ZOOM_PATH.read_text(encoding="utf-8"))
    links = data.get("links", [])
    changed = 0
    by_new: dict[str, int] = {}
    unchanged = 0
    missing: list[tuple[str, str]] = []
    for src, tgt, old, new in RETYPING:
        matches = list(_iter_matching(links, src, tgt))
        if not matches:
            missing.append((src, tgt))
            continue
        for link in matches:
            cur = link.get("linkType")
            if cur == new:
                unchanged += 1
                continue
            if cur != old and cur != new:
                print(
                    f"  warn: {src} -> {tgt} has unexpected linkType {cur!r} "
                    f"(expected {old!r} or already-migrated {new!r}); retyping anyway",
                    file=sys.stderr,
                )
            link["linkType"] = new
            changed += 1
            by_new[new] = by_new.get(new, 0) + 1
    print(f"Retype summary: {changed} changed, {unchanged} already current, {len(missing)} missing")
    for new, n in sorted(by_new.items()):
        print(f"  → {new}: {n}")
    for src, tgt in missing:
        print(f"  MISSING: {src} -> {tgt}", file=sys.stderr)
    if missing:
        return 2
    if dry:
        print("(dry run — not writing)")
        return 0
    ZOOM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {ZOOM_PATH.relative_to(REPO_ROOT)}")
    return 0


def verify() -> int:
    data = json.loads(ZOOM_PATH.read_text(encoding="utf-8"))
    links = data.get("links", [])
    failures: list[str] = []
    for src, tgt, _old, new in RETYPING:
        matches = list(_iter_matching(links, src, tgt))
        if not matches:
            failures.append(f"{src} -> {tgt}: edge not found")
            continue
        for link in matches:
            if link.get("linkType") != new:
                failures.append(
                    f"{src} -> {tgt}: linkType is {link.get('linkType')!r}, expected {new!r}"
                )
    # Also: no in-use 'conceptual' or 'training' edges should remain other
    # than the whitelisted exceptions in CONCEPTUAL_KEEP.
    leftover_conceptual = [
        l for l in links
        if l.get("linkType") == "conceptual"
        and (l["source"], l["target"]) not in CONCEPTUAL_KEEP
    ]
    leftover_training = [
        l for l in links if l.get("linkType") == "training"
    ]
    if leftover_conceptual:
        failures.append(
            f"{len(leftover_conceptual)} unwhitelisted 'conceptual' edges remain "
            f"(expected only {len(CONCEPTUAL_KEEP)})"
        )
        for l in leftover_conceptual:
            failures.append(f"    unexpected: {l.get('source')} -> {l.get('target')}")
    if leftover_training:
        failures.append(f"{len(leftover_training)} 'training' edges remain (expected 0)")
        for l in leftover_training:
            failures.append(f"    unexpected: {l.get('source')} -> {l.get('target')}")
    if failures:
        print("VERIFY FAIL:")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"VERIFY OK: {len(RETYPING)} retyped edges present, 0 deprecated linkTypes remaining")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true", help="check only, don't write")
    p.add_argument("--dry", action="store_true", help="print diff, don't write")
    args = p.parse_args()
    if args.verify:
        return verify()
    return apply(dry=args.dry)


if __name__ == "__main__":
    raise SystemExit(main())
