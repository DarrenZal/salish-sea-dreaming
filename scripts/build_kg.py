#!/usr/bin/env python3
"""build_kg.py — IMPACT 2026 event-scoped KG additions.

Phase 3 of the IMPACT KG event-scoped views plan
(~/.claude/plans/impact-kg-event-scoped-views.md).

This script reads the live ssd-data-map-zoom.json (already extended in P1 with
the two event hubs + 7 partOfEvent edges + 1 bridgesEvents edge) and layers
IMPACT 2026 contributor data on top:

  1. Adds 3 new Person nodes (Austin Harry, Matt Robertson, James Harry)
  2. Adds 1 new installation node (install:ssd-impact-2026-hubble)
  3. Adds partOfEvent edges:
       - new people  → event:impact-2026
       - cross-event people (Pravin, Darren, Carol Anne, Eve, Shawn) → BOTH
       - Digital-Ecologies-only people (Briony, Moonfish, Denning, Brad, Raf,
         Natalia, Zoe, Blair) → event:digital-ecologies-2026
       - install:ssd-impact-2026-hubble → event:impact-2026
  4. Adds involves edges from the IMPACT installation to participating people.

Strictly additive + idempotent. No existing node content is modified.
Does NOT add concept nodes (Crescent / Circle / Trigon / Pearl / Thunderbird /
Formline / DreamStates / 25 themes) — those are out of scope per decision #5
of the plan.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Authored data (the things we add)
# ---------------------------------------------------------------------------

# Three new Person nodes. Bio text is derived from vault entity notes at
# ~/Documents/Notes/People/{Austin Harry,Matt Robertson,
#   James Nexw'Kalus-Xwalacktun Harry}.md (the canonical source).
NEW_PEOPLE = [
    {
        "id": "person:austin-harry",
        "name": "Austin Aan'yas Harry",
        "type": "person",
        "tier": 1,
        "clusterHub": "hub:artists",
        "bio": (
            "Coast Salish artist; Sḵwx̱wú7mesh (Squamish) Wolf and Nam̓gis "
            "Thunderbird lineage. Son of master carver Xwalacktun. Co-leading "
            "artist for the IMPACT 2026 Hubble Space installation. Works in "
            "vector-based digital design and traditional Coast Salish forms; "
            "founder of INDIGITAL."
        ),
        "koi_uri": "orn:personal-koi.entity:person-austin-harry-60bbb02d5ddb",
    },
    {
        "id": "person:matt-robertson",
        "name": "Matt Robertson",
        "type": "person",
        "tier": 1,
        "clusterHub": "hub:artists",
        "bio": (
            "Composer. Produced the data-driven autonomous sound layer for "
            "the prior Salish Sea Dreaming exhibition (driven by herring + "
            "fishery + tide + lunar data). Composing the IMPACT 2026 sonic "
            "score against a wider data set (tide, salmon spawn, wind, "
            "LiDAR canopy, Burrard Inlet ship traffic, SkyTrain, shoreline "
            "ambient)."
        ),
        "koi_uri": "orn:personal-koi.entity:person-matt-robertson-906e3dd42175",
    },
    {
        "id": "person:james-harry",
        "name": "James Nexw'Kalus-Xwalacktun Harry",
        "type": "person",
        "tier": 1,
        "clusterHub": "hub:artists",
        "bio": (
            "Coast Salish sculptor based in Sḵwx̱wú7mesh (Squamish) territory. "
            "Brother of Austin Harry. Works extensively with the Coast Salish "
            "primitive shape language (Crescent / Circle / Trigon) in "
            "three-dimensional sculptural form — public installations "
            "including \"Welcome Gate\" and \"MIYIWTS\". Reference for the "
            "IMPACT trigon-wrapped-around-cylinder language. Homepage: "
            "jamesharry.ca"
        ),
        "koi_uri": (
            "orn:personal-koi.entity:"
            "person-james-nexwkalus-xwalacktun-harry-ec892a332500"
        ),
    },
]

# IMPACT installation node — mirrors the shape of install:salish-sea-dreaming.
NEW_INSTALL = {
    "id": "install:ssd-impact-2026-hubble",
    "name": "Salish Sea Dreaming — IMPACT Hubble",
    "type": "installation",
    "tier": 0,
    "clusterHub": "hub:exhibition",
    "subtitle": (
        "Indigenomics IMPACT 2026 — Hubble Space, HR MacMillan Space Centre, "
        "May 27–28, 2026"
    ),
}

# IMPACT 2026 event memberships (people only — the 7 existing hubs were already
# wired to digital-ecologies-2026 in P1). New IMPACT-only people are added via
# NEW_PEOPLE; here we name them by id for the edge layer.
IMPACT_ONLY_PEOPLE = [
    "person:austin-harry",
    "person:matt-robertson",
    "person:james-harry",
]

# Cross-event: present at both Digital Ecologies AND IMPACT.
# Sources:
# - Carol Anne, Pravin, Darren: confirmed across both meeting notes
#   (Digital Ecologies team + 2026-05-18 IMPACT planning attendees).
# - Eve, Shawn: confirmed in 2026-05-18 meeting note — gathering data sets for
#   Matt's IMPACT composition, were also on the Digital Ecologies team.
CROSS_EVENT_PEOPLE = [
    "person:carol-anne-hilton",
    "person:prav-pillay",
    "person:darren-zal",
    "person:eve-marenghi",
    "person:shawn-anderson",
]

# Digital-Ecologies-only people. The 7 hubs are already linked to
# digital-ecologies-2026 from P1, so these explicit partOfEvent edges are
# additive query-determinism (per the orchestrator's note in the prompt:
# "you may explicitly add the partOfEvent edge too for query-determinism,
# but optional"). We add them — same-cost and keeps the membership edge layer
# uniform across all people.
DE_ONLY_PEOPLE = [
    "person:briony-penn",
    "person:moonfish-media",
    "person:david-denning",
    "person:brad-necyk",
    "person:raf",
    "person:natalia-lebedinskaia",
    "person:zoe-zafiris-casey",
    "person:blair",
]

# IMPACT installation participants — the people whose work is involved in the
# IMPACT Hubble installation. Mirrors the involves pattern from
# install:salish-sea-dreaming → hub:* edges.
IMPACT_INSTALL_PARTICIPANTS = [
    "person:austin-harry",
    "person:matt-robertson",
    "person:james-harry",   # reference / inspiration source per meeting note
    "person:carol-anne-hilton",
    "person:prav-pillay",
    "person:darren-zal",
    "person:eve-marenghi",
    "person:shawn-anderson",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def has_node(nodes: list[dict], node_id: str) -> bool:
    return any(n.get("id") == node_id for n in nodes)


def has_edge(links: list[dict], src: str, tgt: str, link_type: str) -> bool:
    for l in links:
        if (
            l.get("source") == src
            and l.get("target") == tgt
            and l.get("linkType") == link_type
        ):
            return True
    return False


def add_node(nodes: list[dict], node: dict, log: list[str]) -> bool:
    """Add node if not already present. Returns True if added."""
    if has_node(nodes, node["id"]):
        log.append(f"  skip node (exists): {node['id']}")
        return False
    nodes.append(node)
    log.append(f"  add  node: {node['id']} ({node.get('name','?')})")
    return True


def add_edge(
    links: list[dict], src: str, tgt: str, link_type: str, log: list[str]
) -> bool:
    """Add edge if not already present. Returns True if added."""
    if has_edge(links, src, tgt, link_type):
        log.append(f"  skip edge (exists): {src} --{link_type}--> {tgt}")
        return False
    links.append({"source": src, "target": tgt, "linkType": link_type})
    log.append(f"  add  edge: {src} --{link_type}--> {tgt}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build(data: dict, log: list[str]) -> tuple[int, int, dict]:
    """Apply IMPACT 2026 additions. Returns (nodes_added, edges_added, breakdown)."""
    nodes = data.setdefault("nodes", [])
    links = data.setdefault("links", [])

    breakdown = {
        "person_nodes": 0,
        "install_nodes": 0,
        "partOfEvent_edges": 0,
        "involves_edges": 0,
    }

    log.append("== Nodes ==")
    # 1. Three new Person nodes
    for person in NEW_PEOPLE:
        node = {k: v for k, v in person.items() if k != "koi_uri"}
        # Stash KOI canonical URI under a nested key, matching no existing
        # convention (no other node has koi:* fields) — keep it tucked away
        # so D3 viz code falls through. We use 'koi_canonical_uri' as a
        # flat field for now since none of the existing nodes use a nested
        # 'koi' dict either; this is purely additive metadata.
        node["koi_canonical_uri"] = person["koi_uri"]
        if add_node(nodes, node, log):
            breakdown["person_nodes"] += 1

    # 2. Installation node
    if add_node(nodes, dict(NEW_INSTALL), log):
        breakdown["install_nodes"] += 1

    log.append("== Edges ==")
    # 3a. partOfEvent: IMPACT-only people → event:impact-2026
    for pid in IMPACT_ONLY_PEOPLE:
        if add_edge(links, pid, "event:impact-2026", "partOfEvent", log):
            breakdown["partOfEvent_edges"] += 1

    # 3b. partOfEvent: cross-event people → both events
    for pid in CROSS_EVENT_PEOPLE:
        for eid in ("event:impact-2026", "event:digital-ecologies-2026"):
            if add_edge(links, pid, eid, "partOfEvent", log):
                breakdown["partOfEvent_edges"] += 1

    # 3c. partOfEvent: DE-only people → event:digital-ecologies-2026
    for pid in DE_ONLY_PEOPLE:
        if add_edge(
            links, pid, "event:digital-ecologies-2026", "partOfEvent", log
        ):
            breakdown["partOfEvent_edges"] += 1

    # 3d. partOfEvent: install:ssd-impact-2026-hubble → event:impact-2026
    if add_edge(
        links,
        "install:ssd-impact-2026-hubble",
        "event:impact-2026",
        "partOfEvent",
        log,
    ):
        breakdown["partOfEvent_edges"] += 1

    # 4. involves: install:ssd-impact-2026-hubble → participating people
    for pid in IMPACT_INSTALL_PARTICIPANTS:
        if add_edge(
            links, "install:ssd-impact-2026-hubble", pid, "involves", log
        ):
            breakdown["involves_edges"] += 1

    # Update meta
    meta = data.setdefault("meta", {})
    meta["total_nodes"] = len(nodes)
    meta["total_links"] = len(links)
    meta["p3_impact_contributors_applied"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )

    nodes_added = (
        breakdown["person_nodes"] + breakdown["install_nodes"]
    )
    edges_added = (
        breakdown["partOfEvent_edges"] + breakdown["involves_edges"]
    )
    return nodes_added, edges_added, breakdown


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--input",
        default="/home/poly/ssd-v5/static/ssd-data-map-zoom.json",
        help="Path to input ssd-data-map-zoom.json",
    )
    ap.add_argument(
        "--output",
        default="/tmp/ssd-data-map-zoom-impact.json",
        help="Path to write the extended graph (DO NOT overwrite live).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended changes without writing output.",
    )
    args = ap.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print(f"ERROR: input file not found: {inp}", file=sys.stderr)
        return 1

    with inp.open() as f:
        data = json.load(f)

    pre_nodes = len(data.get("nodes", []))
    pre_links = len(data.get("links", []))

    log: list[str] = []
    nodes_added, edges_added, breakdown = build(data, log)

    if args.dry_run:
        print("\n".join(log))
        print()
    else:
        out = Path(args.output)
        with out.open("w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # Summary (< 20 lines)
    print("---- IMPACT 2026 KG build summary ----")
    print(f"input  : {inp}")
    if not args.dry_run:
        print(f"output : {args.output}")
    else:
        print("output : (dry-run, nothing written)")
    print(f"nodes  : {pre_nodes} -> {pre_nodes + nodes_added}  (+{nodes_added})")
    print(f"links  : {pre_links} -> {pre_links + edges_added}  (+{edges_added})")
    print("breakdown:")
    for k, v in breakdown.items():
        print(f"  {k:24s} {v:+d}")
    print(
        "scope: 3 person + 1 installation + partOfEvent + involves edges. "
        "No concept nodes. Idempotent."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
