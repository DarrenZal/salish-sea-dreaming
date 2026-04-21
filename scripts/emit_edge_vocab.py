#!/usr/bin/env python3
"""Emit static/ssd-edge-vocab.json from the canonical ontology.

Reads `static/ontology/ssd-ontology.jsonld`, extracts the seven
`owl:ObjectProperty` entries, and writes a compact frontend-facing
lookup table keyed by `ssd:linkTypeKey`. Intentionally decoupled from
`scripts/build_datamap_v2.py` — the live zoom JSON contains nodes and
edges that are not reproducible from that builder (see plan R1-01),
so we never trigger a rebuild of zoom data as a side effect.

Idempotent: running twice produces byte-identical output.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = REPO_ROOT / "static" / "ontology" / "ssd-ontology.jsonld"
OUTPUT_PATH = REPO_ROOT / "static" / "ssd-edge-vocab.json"


def _is_object_property(entry: dict) -> bool:
    t = entry.get("@type")
    if isinstance(t, str):
        return t == "owl:ObjectProperty"
    if isinstance(t, list):
        return "owl:ObjectProperty" in t
    return False


def _require(entry: dict, key: str) -> str:
    val = entry.get(key)
    if not isinstance(val, str) or not val:
        raise ValueError(
            f"Ontology entry {entry.get('@id')!r} is missing required string field {key!r}"
        )
    return val


def build_vocab() -> dict:
    ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    vocab: dict[str, dict] = {}
    for entry in ontology.get("@graph", []):
        if not _is_object_property(entry):
            continue
        link_type_key = _require(entry, "ssd:linkTypeKey")
        forward_label = _require(entry, "ssd:forwardLabel")
        ui_color = _require(entry, "ssd:uiColor")
        # Symmetric predicates reuse forwardLabel as inverseLabel; the
        # ontology carries the same string explicitly so this is a
        # non-branching lookup here.
        inverse_label = _require(entry, "ssd:inverseLabel")
        comment = entry.get("rdfs:comment", "")
        vocab[link_type_key] = {
            "forward_label": forward_label,
            "inverse_label": inverse_label,
            "color": ui_color,
            "description": comment if isinstance(comment, str) else "",
            "iri": entry.get("@id", ""),
        }
    return vocab


def main() -> None:
    vocab = build_vocab()
    OUTPUT_PATH.write_text(
        json.dumps(vocab, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} with {len(vocab)} predicates")


if __name__ == "__main__":
    main()
