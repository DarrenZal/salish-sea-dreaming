#!/usr/bin/env python3
"""
Build ssd-data-map-zoom.json — adds semantic zoom cluster hubs to the graph.

Run from repo root:
    python scripts/build_graph_clusters.py
"""
import json
from pathlib import Path
from collections import Counter

THEME_TO_HUB = {
    'briony-art':            'hub:briony-art',
    'data-package':          'hub:research-data',
    'ecological-data':       'hub:ecosystem',
    'marine-reference':      'hub:marine-ref',
    'training-data':         'hub:training',
    'raf-curator':           'hub:training',
    'generated-art':         'hub:generated',
    'generated-experiments': 'hub:generated',
    'handoff-renders':       'hub:generated',
    'video':                 'hub:video',
    'documentation':         'hub:docs',
    'code':                  'hub:code',
    'models':                'hub:code',
    'signal-loop':           'hub:other',
    'projection-learning':   'hub:other',
    'other':                 'hub:other',
}

HUB_LABELS = {
    'hub:briony-art':     "Briony Penn's Art",
    'hub:research-data':  'Research Data',
    'hub:ecosystem':      'Ecosystem Data',
    'hub:marine-ref':     'Marine Reference',
    'hub:training':       'Training Corpus',
    'hub:generated':      'Generated Works',
    'hub:video':          'Video',
    'hub:docs':           'Documentation',
    'hub:code':           'Codebase & Models',
    'hub:other':          'Other',
}

src = Path('static/ssd-data-map.json')
data = json.loads(src.read_text())
nodes = data['nodes']
links = data['links']

# Tag every node with its cluster hub
for n in nodes:
    n['clusterHub'] = THEME_TO_HUB.get(n.get('theme', ''), 'hub:other')

# Count nodes per hub (for badge display)
hub_counts = Counter(n['clusterHub'] for n in nodes)

# Create hub nodes
hub_nodes = []
for hub_id, label in HUB_LABELS.items():
    hub_nodes.append({
        'id': hub_id,
        'name': label,
        'type': 'hub',
        'theme': 'hub',
        'ext': '',
        'size': 0,
        'isDir': True,
        'depth': 0,
        'clusterHub': hub_id,
        'childCount': hub_counts.get(hub_id, 0),
    })

# Visitor voices hub — always-visible live injection target
hub_nodes.append({
    'id': 'hub:visitor-voices',
    'name': 'Visitor Voices',
    'type': 'hub',
    'theme': 'visitor',
    'ext': '',
    'size': 0,
    'isDir': True,
    'depth': 0,
    'clusterHub': 'hub:visitor-voices',
    'childCount': 0,
})

# Hub-to-center links (hubs radiate from src:github-repo anchor)
hub_links = [{'source': 'src:github-repo', 'target': h['id']} for h in hub_nodes]

out = {
    'nodes': hub_nodes + nodes,
    'links': hub_links + links,
    'theme_colors': data.get('theme_colors', {}),
    'ext_colors': data.get('ext_colors', {}),
    'meta': data.get('meta', {}),
}

dest = Path('static/ssd-data-map-zoom.json')
dest.write_text(json.dumps(out, separators=(',', ':')))
print(f"Written {dest}: {len(out['nodes'])} nodes, {len(out['links'])} links")
print(f"Hub counts: { {h['id']: h['childCount'] for h in hub_nodes} }")
