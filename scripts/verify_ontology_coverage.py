#!/usr/bin/env python3
"""Static verifier for the Salish Sea Dreaming ontology.

Asserts that `static/ontology/ssd-ontology.jsonld` covers every node
`type` and non-empty `linkType` found in `static/ssd-data-map-zoom.json`,
plus the runtime-only `visitor` class and `in-cluster` predicate that the
frontend creates for visitor-dream links.

No browser required. Prints a coverage table to stdout and exits 1 on any
gap. Backs AC3 and AC4 of the edge-semantics-ontology plan.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = REPO_ROOT / "static" / "ontology" / "ssd-ontology.jsonld"
ZOOM_PATH = REPO_ROOT / "static" / "ssd-data-map-zoom.json"

# Runtime-only types/predicates added by the frontend bootstrap
# (not present in static data but required in the ontology).
RUNTIME_CLASSES = {"visitor"}
RUNTIME_PREDICATES = {"in-cluster"}

# Map from node.type kebab-case to expected owl:Class IRI.
# Matches the 14 static types + visitor runtime type.
TYPE_TO_CLASS = {
    "hub": "ssd:Hub",
    "installation": "ssd:Installation",
    "concept": "ssd:Concept",
    "person": "ssd:Person",
    "artifact": "ssd:Artifact",
    "software": "ssd:Software",
    "output": "ssd:Output",
    "interface": "ssd:Interface",
    "td-internal": "ssd:TdInternal",
    "species": "ssd:Species",
    "cluster-summary": "ssd:ClusterSummary",
    "photo": "ssd:Photo",
    "report": "ssd:Report",
    "ml-source": "ssd:MlSource",
    "visitor": "ssd:Visitor",
}

UI_COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{6}|hsl\([^)]+\))$")


def _load_ontology() -> dict:
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def _load_zoom() -> dict:
    return json.loads(ZOOM_PATH.read_text(encoding="utf-8"))


def _is_class(entry: dict) -> bool:
    t = entry.get("@type")
    return t == "owl:Class" if isinstance(t, str) else False


def _is_object_property(entry: dict) -> bool:
    t = entry.get("@type")
    if isinstance(t, str):
        return t == "owl:ObjectProperty"
    if isinstance(t, list):
        return "owl:ObjectProperty" in t
    return False


def _is_symmetric(entry: dict) -> bool:
    t = entry.get("@type")
    if isinstance(t, list):
        return "owl:SymmetricProperty" in t
    return False


def check_nodes(ontology: dict, zoom: dict) -> list[str]:
    errors: list[str] = []

    class_ids = {e["@id"] for e in ontology["@graph"] if _is_class(e)}

    zoom_types = Counter(n.get("type", "") for n in zoom["nodes"])
    expected_types = set(zoom_types) | RUNTIME_CLASSES
    expected_types.discard("")

    print(f"\n[nodes] distinct types in zoom JSON: {len(zoom_types)}")
    print(f"[nodes] runtime-added types:         {sorted(RUNTIME_CLASSES)}")
    print(f"[nodes] ontology classes:            {len(class_ids)}")
    print()
    print(f"  {'type':<20} {'count':>7}  {'class IRI':<28} present?")
    print(f"  {'-'*20} {'-'*7}  {'-'*28} {'-'*8}")

    for t in sorted(expected_types):
        expected_iri = TYPE_TO_CLASS.get(t)
        if expected_iri is None:
            errors.append(f"no TYPE_TO_CLASS mapping for type={t!r}")
            marker = "UNMAPPED"
        elif expected_iri not in class_ids:
            errors.append(
                f"ontology is missing class for type={t!r} (expected @id={expected_iri})"
            )
            marker = "MISSING"
        else:
            marker = "ok"
        count = zoom_types.get(t, 0) if t not in RUNTIME_CLASSES else "(runtime)"
        print(f"  {t:<20} {str(count):>7}  {str(expected_iri):<28} {marker}")

    return errors


def check_links(ontology: dict, zoom: dict) -> list[str]:
    errors: list[str] = []

    object_properties = [e for e in ontology["@graph"] if _is_object_property(e)]
    by_link_type_key: dict[str, dict] = {}
    by_id: dict[str, dict] = {e["@id"]: e for e in object_properties}

    for e in object_properties:
        key = e.get("ssd:linkTypeKey")
        if not isinstance(key, str) or not key:
            errors.append(
                f"ObjectProperty {e.get('@id')!r} missing ssd:linkTypeKey"
            )
            continue
        if key in by_link_type_key:
            errors.append(
                f"duplicate ssd:linkTypeKey={key!r} on "
                f"{by_link_type_key[key]['@id']} and {e['@id']}"
            )
        by_link_type_key[key] = e

    zoom_link_types = Counter(l.get("linkType", "") for l in zoom["links"])
    static_required = {k for k in zoom_link_types if k}  # non-empty only
    all_required = static_required | RUNTIME_PREDICATES

    untyped_count = zoom_link_types.get("", 0)

    print(f"\n[links] distinct non-empty linkType values: {len(static_required)}")
    print(f"[links] runtime-added predicates:           {sorted(RUNTIME_PREDICATES)}")
    print(f"[links] ontology ObjectProperties:          {len(object_properties)}")
    print(f"[links] untyped links in zoom JSON:         {untyped_count}  (warning only)")
    print()
    print(f"  {'linkType':<18} {'count':>6}  {'forward':<24} {'inverse':<24} color")
    print(f"  {'-'*18} {'-'*6}  {'-'*24} {'-'*24} {'-'*18}")

    for key in sorted(all_required):
        entry = by_link_type_key.get(key)
        count = zoom_link_types.get(key, 0) if key not in RUNTIME_PREDICATES else "(runtime)"
        if entry is None:
            errors.append(f"ontology is missing ObjectProperty with ssd:linkTypeKey={key!r}")
            print(f"  {key:<18} {str(count):>6}  MISSING")
            continue

        forward_label = entry.get("ssd:forwardLabel")
        inverse_label = entry.get("ssd:inverseLabel")
        ui_color = entry.get("ssd:uiColor")
        inverse_of = entry.get("owl:inverseOf")

        if not isinstance(forward_label, str) or not forward_label:
            errors.append(f"{entry['@id']} missing non-empty ssd:forwardLabel")
        if not (isinstance(inverse_label, str) and inverse_label) and not _is_symmetric(entry):
            errors.append(
                f"{entry['@id']} missing ssd:inverseLabel and not declared owl:SymmetricProperty"
            )
        if not isinstance(ui_color, str) or not UI_COLOR_RE.match(ui_color):
            errors.append(
                f"{entry['@id']} ssd:uiColor={ui_color!r} does not match #rrggbb or hsl(...)"
            )
        if inverse_of is not None:
            # owl:inverseOf may be a string IRI or {"@id": "..."}
            iri = inverse_of["@id"] if isinstance(inverse_of, dict) else inverse_of
            if not isinstance(iri, str) or not iri.startswith("ssd:"):
                errors.append(
                    f"{entry['@id']} owl:inverseOf has unexpected shape: {inverse_of!r}"
                )
            # Dangling-reference check: we allow inverseOf to point to an IRI that
            # is not itself a standalone @graph entry (the plan permits inverses to
            # live as inline labels on the forward property). No hard assertion.

        print(
            f"  {key:<18} {str(count):>6}  {str(forward_label):<24} "
            f"{str(inverse_label or '(symmetric)'):<24} {ui_color}"
        )

    if untyped_count > 0:
        print(
            f"\n  warning: {untyped_count} links have no linkType — rendered "
            f"under the 'related to' fallback section (see AC4b)."
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "mode",
        nargs="?",
        default="nodes",
        choices=("nodes", "links", "all"),
        help="which coverage check to run (default: nodes)",
    )
    args = parser.parse_args()

    if not ONTOLOGY_PATH.exists():
        print(f"ERROR: ontology file not found: {ONTOLOGY_PATH}", file=sys.stderr)
        return 1
    if not ZOOM_PATH.exists():
        print(f"ERROR: zoom JSON not found: {ZOOM_PATH}", file=sys.stderr)
        return 1

    ontology = _load_ontology()
    zoom = _load_zoom()

    errors: list[str] = []
    if args.mode in ("nodes", "all"):
        errors.extend(check_nodes(ontology, zoom))
    if args.mode in ("links", "all"):
        errors.extend(check_links(ontology, zoom))

    print()
    if errors:
        print(f"FAIL: {len(errors)} error(s):")
        for msg in errors:
            print(f"  - {msg}")
        return 1
    print("PASS: ontology coverage OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
