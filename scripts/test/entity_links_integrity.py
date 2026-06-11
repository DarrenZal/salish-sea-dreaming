"""Verify every _ENTITY_LINKS target either is a graph node OR has a card.
Orphan entity links mean chat may render '[Name](#node-id)' linking nowhere.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def fetch(base, path):
    with urllib.request.urlopen(base.rstrip("/") + path, timeout=10) as r:
        return json.load(r)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "https://salishseadreaming.art"

    # Pull _ENTITY_LINKS from the live gallery_server.py via ssh
    # OR check repo copy if available locally
    server_py = REPO / "scripts" / "gallery_server.py"
    if not server_py.exists():
        print(f"⚠ gallery_server.py not at {server_py}; pulling from poly")
        import subprocess
        out = subprocess.run(
            ["ssh", "poly@37.27.48.12", "cat", "/home/poly/ssd-v5/scripts/gallery_server.py"],
            capture_output=True, text=True, timeout=15,
        )
        text = out.stdout
    else:
        text = server_py.read_text()

    # Find the _ENTITY_LINKS dict
    m = re.search(r"_ENTITY_LINKS\s*=\s*\{(.*?)^\}", text, re.DOTALL | re.MULTILINE)
    if not m:
        print("❌ _ENTITY_LINKS dict not found")
        sys.exit(1)
    block = m.group(1)
    # Extract target IDs from "Name": "target:id" entries
    entries = re.findall(r'"[^"]+"\s*:\s*"([^"]+)"', block)
    targets = set(entries)

    graph = fetch(base, "/graph-assets/ssd-data-map-zoom.json")
    cards = fetch(base, "/graph-assets/ssd-cards.json")
    node_ids = {n["id"] for n in graph["nodes"]}
    card_ids = set(cards.get("cards", {}).keys())

    orphans = []
    for t in sorted(targets):
        if t not in node_ids and t not in card_ids:
            orphans.append(t)

    if orphans:
        print(f"❌ FAIL ({len(orphans)}) entity_links_integrity")
        for o in orphans[:20]:
            print(f"  orphan: '{o}' (no node, no card)")
        sys.exit(1)
    print(f"✅ PASS  entity_links_integrity ({len(targets)} entries, all resolve)")


if __name__ == "__main__":
    main()
