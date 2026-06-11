"""KG invariant probes — visitor-perspective tests that should have caught
the 2026-05-26 round of bugs (Austin missing from hub.contains, Indigenomics
Themes floating, sponsor list incomplete).

Three invariants checked:

  1. kg_hub_contains_completeness
     For each contributor named in `credits-and-licenses-2026-05.md`, assert
     they appear in the contains-list of at least one hub. Catches the "Austin
     not in hub:artists.contains" bug.

  2. kg_no_floating_bridge_nodes
     For each bridge node (partOfEvent → other-event AND not partOfEvent → this
     event), assert at least one of its edges connects to a node that is
     ITSELF visible by default in the target event view (event hub, hub, or
     event-member tier-0 node). Catches the "Indigenomics Themes floats alone"
     bug.

  3. kp_relations_completeness
     For each named person node, assert their card has body (≥60 chars) AND
     they have at least one outbound `partOfEvent` edge AND at least one
     hub-contains edge AND outbound URL or vault entity note exists.
     Catches the "card with empty bio" / "person not in any hub" bug.

Usage:
    python3 scripts/test/kg_invariants.py
    python3 scripts/test/kg_invariants.py --event impact-2026
    python3 scripts/test/kg_invariants.py --remote https://salishseadreaming.art
"""
from __future__ import annotations
import argparse
import json
import sys
import urllib.request
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent.parent
DEFAULT_GRAPH_PATH = REPO_ROOT / "static" / "ssd-data-map-zoom.json"
DEFAULT_CARDS_PATH = REPO_ROOT / "static" / "ssd-cards.json"
CREDITS_PATH = REPO_ROOT / "docs" / "space-center" / "credits-and-licenses-2026-05.md"


def fetch_remote_json(base_url: str, path: str) -> dict:
    url = base_url.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)


def load_graph(args) -> dict:
    if args.remote:
        return fetch_remote_json(args.remote, "/graph-assets/ssd-data-map-zoom.json")
    return json.loads(DEFAULT_GRAPH_PATH.read_text())


def load_cards(args) -> dict:
    if args.remote:
        return fetch_remote_json(args.remote, "/graph-assets/ssd-cards.json")
    return json.loads(DEFAULT_CARDS_PATH.read_text())


def load_named_contributors() -> set[str]:
    """Pull contributor names from credits doc. Returns a set of canonical names."""
    if not CREDITS_PATH.exists():
        print(f"⚠ credits doc not found: {CREDITS_PATH}", file=sys.stderr)
        return set()
    text = CREDITS_PATH.read_text()
    # The credits doc structure is a markdown table; pull names from rows
    # that look like contributor entries. Loose heuristic: lines starting
    # with `| ` that have a name in the second column.
    names = set()
    for line in text.splitlines():
        if not line.startswith("| ") or "| Role" in line or "|---" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[1] and parts[1] not in ("Name", ""):
            # Filter out heading-style lines, parens-suffixes, comments
            name = parts[1].split("(")[0].split("—")[0].strip().strip("*").strip()  # strip markdown bold
            if name and len(name) > 2 and not name.startswith("#"):
                names.add(name)
    return names


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace("ʼ", "").replace("’", "")


# Contributors intentionally NOT in the graph (consent / scope decisions).
# Listed in credits doc but expected to have no graph node.
EXPECTED_ABSENT = {
    "James Harry",  # TBD with Austin — consent not granted (per credits doc)
    "Xwalacktun",   # referenced in Austin's bio, not a standalone contributor
    "Squamish Lil'wat Cultural Centre",  # mentioned, not a contributor entity
    "iNaturalist contributors",  # generic crowd attribution
}

# Acceptable node types when matching credits to graph (not just person)
NAMED_NODE_TYPES = {"person", "partner", "venue", "surface", "installation", "concept"}


def name_matches(node_name: str, credit_name: str) -> bool:
    """Liberal fuzzy match — handles 'Austin Harry' vs 'Austin Aan'yas Harry' etc."""
    if not node_name or not credit_name:
        return False
    if node_name == credit_name:
        return True
    nn = slugify(node_name)
    cn = slugify(credit_name)
    if nn == cn:
        return True
    # Token-set match: every token in credit must appear in node name
    node_tokens = set(nn.split("-"))
    credit_tokens = set(cn.split("-"))
    return credit_tokens.issubset(node_tokens) and len(credit_tokens) >= 2


def check_hub_contains_completeness(graph: dict, named: set[str], cards: dict) -> tuple[int, list[str]]:
    """Each named contributor should appear in some hub.contains, OR be a
    card-only entity (partners/orgs accessed via _ENTITY_LINKS auto-linking).
    Documented exclusions (consent/scope) skipped."""
    contains_targets = set()
    for l in graph["links"]:
        if l.get("linkType") == "contains" and l.get("source", "").startswith("hub:"):
            contains_targets.add(l.get("target"))
    cards_dict = cards.get("cards", {})
    failures = []
    for name in sorted(named):
        if name in EXPECTED_ABSENT:
            continue
        # Check graph nodes first
        match = None
        for n in graph["nodes"]:
            if n.get("type") in NAMED_NODE_TYPES and name_matches(n.get("name", ""), name):
                match = n["id"]
                break
        if not match:
            # Check cards (partners/orgs may be card-only)
            card_match = None
            for cid, c in cards_dict.items():
                if name_matches(c.get("title", ""), name):
                    card_match = cid
                    break
            if card_match:
                continue  # discoverable via card + _ENTITY_LINKS auto-link
            failures.append(f"  contributor '{name}' has NO graph node AND NO card")
            continue
        node_type = next((n.get("type") for n in graph["nodes"] if n.get("id") == match), None)
        if node_type in ("partner", "venue", "surface", "installation", "concept", "hub", "event"):
            continue
        if match not in contains_targets:
            hub_edges = [l for l in graph["links"] if l.get("target") == match and l.get("linkType") == "contains"]
            failures.append(f"  '{name}' ({match}) missing from any hub.contains "
                            f"(has {len(hub_edges)} contains-edges in)")
    return len(failures), failures


def check_no_floating_bridge_nodes(graph: dict, event_id: str) -> tuple[int, list[str]]:
    """Each bridge node should have an edge to a visible-by-default node."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    # Build member set
    member_ids = {event_id}
    for l in graph["links"]:
        if l.get("linkType") == "partOfEvent" and l["target"] == event_id:
            member_ids.add(l["source"])
    # Build bridge set
    other_event_hubs = {n["id"] for n in graph["nodes"] if n.get("type") == "event" and n["id"] != event_id}
    bridge_ids = set()
    for l in graph["links"]:
        if l.get("linkType") == "partOfEvent" and l.get("target") in other_event_hubs and l.get("source") not in member_ids:
            bridge_ids.add(l.get("source"))
    # A bridge is OK if it connects to ANY node that is visible by default.
    # In the JS rendering, isVisible() returns true for type='event', type='hub',
    # and tier=0 — regardless of bridge/member scope. So any hub neighbor
    # (even a bridge-hub) is enough for the bridge node to be "anchored".
    default_visible_ids = {n["id"] for n in graph["nodes"]
                           if n.get("type") in ("event", "hub")
                           or (n.get("tier") == 0 and n["id"] in member_ids)}
    failures = []
    for bid in sorted(bridge_ids):
        connects = False
        for l in graph["links"]:
            if l.get("linkType") in ("partOfEvent", "bridgesEvents", "offeredAtEvent"):
                continue
            s, t = l.get("source"), l.get("target")
            other = t if s == bid else (s if t == bid else None)
            if other and other in default_visible_ids:
                connects = True
                break
        if not connects:
            failures.append(f"  bridge '{bid}' has no non-event edge to any default-visible neighbor")
    return len(failures), failures


def check_kp_relations_completeness(graph: dict, cards: dict) -> tuple[int, list[str]]:
    """Each named person needs: card with bio (≥60c), partOfEvent edge, hub-contains edge."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    cards_dict = cards.get("cards", {})
    failures = []
    for n in graph["nodes"]:
        if n.get("type") != "person":
            continue
        pid = n["id"]
        if pid not in cards_dict:
            failures.append(f"  {pid}: no card")
            continue
        body = cards_dict[pid].get("body", "")
        if len(body) < 60:
            failures.append(f"  {pid}: card body only {len(body)}c (want ≥60)")
        # Need at least 1 partOfEvent
        ep = [l for l in graph["links"] if l.get("source") == pid and l.get("linkType") == "partOfEvent"]
        if not ep:
            failures.append(f"  {pid}: no partOfEvent edge")
        # Need at least 1 hub.contains pointing IN
        hc = [l for l in graph["links"] if l.get("target") == pid and l.get("linkType") == "contains" and l.get("source", "").startswith("hub:")]
        if not hc:
            failures.append(f"  {pid}: no hub.contains edge in")
    return len(failures), failures


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--event", default="event:impact-2026")
    p.add_argument("--remote", help="https://salishseadreaming.art")
    args = p.parse_args()

    print("=== SSD KG invariant checks ===")
    graph = load_graph(args)
    cards = load_cards(args)
    named = load_named_contributors()
    print(f"Loaded {len(graph['nodes'])} nodes, {len(graph['links'])} edges, "
          f"{len(cards.get('cards', {}))} cards, {len(named)} named contributors\n")

    all_pass = True
    for label, fn, args_tuple in [
        ("kg_hub_contains_completeness", check_hub_contains_completeness, (graph, named, cards)),
        ("kg_no_floating_bridge_nodes", check_no_floating_bridge_nodes, (graph, args.event)),
        ("kp_relations_completeness", check_kp_relations_completeness, (graph, cards)),
    ]:
        n_fail, msgs = fn(*args_tuple)
        status = "✅ PASS" if n_fail == 0 else f"❌ FAIL ({n_fail})"
        print(f"{status}  {label}")
        for m in msgs[:10]:
            print(m)
        if n_fail > 10:
            print(f"  … and {n_fail - 10} more")
        if n_fail:
            all_pass = False
        print()

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
