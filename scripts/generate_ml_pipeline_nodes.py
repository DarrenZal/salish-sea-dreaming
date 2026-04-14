#!/usr/bin/env python3
"""
Generate ML pipeline nodes for ssd-data-map-zoom.json.
Reads provenance.csv + dreaming-model-512/ to produce:
  - hub:ml-pipeline
  - datasrc:* (iNaturalist, Openverse, Briony Penn, Moonfish, Denning)
  - artifact:dreaming-corpus
  - species:* (one per species, sized by image count)
  - artifact:gan-model
  - artifact:briony-lora
  - artifact:autolume
  - artifact:streamdiffusion
"""

import json, csv, os, re, sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(REPO, 'training-data', 'dreaming-model-512')
PROVENANCE  = os.path.join(REPO, 'training-data', 'provenance.csv')
GRAPH_JSON  = os.path.join(REPO, 'static', 'ssd-data-map-zoom.json')

HUB_ID = 'hub:ml-pipeline'

# ── Load existing graph ──────────────────────────────────────────────────────
with open(GRAPH_JSON) as f:
    data = json.load(f)

# Remove any previous ml-pipeline nodes (idempotent re-run)
prev_ids = {n['id'] for n in data['nodes'] if n.get('clusterHub') == HUB_ID or n['id'] == HUB_ID}
data['nodes'] = [n for n in data['nodes'] if n['id'] not in prev_ids]
data['links'] = [l for l in data['links']
                 if l['source'] not in prev_ids and l['target'] not in prev_ids]
existing_ids = {n['id'] for n in data['nodes']}

# ── Count species from corpus filenames ──────────────────────────────────────
species_counts = Counter()
for fname in os.listdir(CORPUS_DIR):
    # Filename pattern: Species_Name_<hash-or-id>.ext
    m = re.match(r'^([A-Za-z][A-Za-z_]+?)_([a-f0-9\-]{6,}|[0-9]{5,})', fname)
    if m:
        raw = m.group(1).replace('_', ' ')
        species_counts[raw] += 1

# Also catch orca_swim / orca_with frame sequences
for fname in os.listdir(CORPUS_DIR):
    m = re.match(r'^(orca)_(swim|with)_(\d+)', fname)
    if m:
        species_counts['Orca'] += 1

# ── Read provenance for per-species source info ──────────────────────────────
provenance_files = set(os.listdir(CORPUS_DIR))
species_sources  = defaultdict(set)
total_src_counts = Counter()
license_counts   = Counter()

with open(PROVENANCE) as f:
    reader = csv.DictReader(f)
    for row in reader:
        fname = os.path.basename(row.get('filename', ''))
        if fname not in provenance_files:
            continue
        src = row.get('source', '') or 'unknown'
        lic = row.get('license', '') or 'unknown'
        total_src_counts[src] += 1
        license_counts[lic] += 1
        m = re.match(r'^([A-Za-z][A-Za-z_]+?)_', fname)
        if m:
            sp = m.group(1).replace('_', ' ')
            species_sources[sp].add(src)

new_nodes, new_links = [], []

# ── ML Pipeline hub ──────────────────────────────────────────────────────────
new_nodes.append({
    'id': HUB_ID,
    'name': 'ML Pipeline',
    'type': 'hub',
    'theme': 'hub',
    'ext': '',
    'size': 0,
    'isDir': True,
    'depth': 0,
    'clusterHub': HUB_ID,
    'childCount': 0,
    'description': '1,255 images from 49 Salish Sea species → StyleGAN2 + LoRA → Autolume latent navigation → StreamDiffusion img2img → the dreaming installation.',
})
new_links.append({'source': 'src:github-repo', 'target': HUB_ID})

# ── Data source nodes (depth 1) ──────────────────────────────────────────────
DATA_SOURCES = [
    {
        'id': 'datasrc:inaturalist',
        'name': 'iNaturalist',
        'icon': '🌿',
        'count': total_src_counts.get('iNaturalist', 564),
        'license': 'CC BY · CC0',
        'license_key': 'cc-by',
        'color': '#5aaa7a',
        'url': 'https://www.inaturalist.org',
        'description': 'Community nature photography platform. Citizen scientists across the Pacific Northwest contributed observations under open licenses. Each photo includes GPS coordinates, species ID, and observer notes.',
    },
    {
        'id': 'datasrc:openverse',
        'name': 'Openverse',
        'icon': '🌐',
        'count': total_src_counts.get('Openverse', 504),
        'license': 'CC BY · CC0 · CC BY-SA',
        'license_key': 'cc-by',
        'color': '#4a8ab0',
        'url': 'https://openverse.org',
        'description': 'WordPress Foundation open media search. Spans marine biology archives, nature photography collections, and institutional datasets — all commercially licensed.',
    },
    {
        'id': 'datasrc:briony-penn',
        'name': 'Briony Penn',
        'icon': '🎨',
        'count': 54,
        'license': 'artist permission',
        'license_key': 'artist',
        'color': '#c8a06a',
        'description': 'Naturalist, illustrator, and ecological storyteller. 54 original watercolor paintings depicting Salish Sea marine life — the visual language and style soul of the installation.',
    },
    {
        'id': 'datasrc:moonfish',
        'name': 'Moonfish Media',
        'icon': '🎬',
        'count': 0,
        'license': 'collaborator permission',
        'license_key': 'collaborator',
        'color': '#6a8ac8',
        'description': 'Professional underwater cinematography. Herring spawning, salmon migration, and deep marine habitat footage. Video frames extracted for corpus and hero exhibition segments.',
    },
    {
        'id': 'datasrc:denning',
        'name': 'David Denning',
        'icon': '📷',
        'count': 0,
        'license': 'collaborator permission',
        'license_key': 'collaborator',
        'color': '#8a9ab0',
        'description': 'Long-term bioregional witnessing through photography. Coastal, intertidal, and shoreline images from decades of observation on the Salish Sea.',
    },
]

for ds in DATA_SOURCES:
    new_nodes.append({
        'id': ds['id'],
        'name': ds['name'],
        'type': 'ml-source',
        'theme': 'ml-pipeline',
        'ext': '',
        'size': max(ds['count'], 1) * 800,
        'isDir': False,
        'depth': 1,
        'clusterHub': HUB_ID,
        'label': f"{ds['count']} images · {ds['license']}" if ds['count'] else ds['license'],
        'license': ds['license'],
        'license_key': ds['license_key'],
        'mlColor': ds['color'],
        'url': ds.get('url', ''),
        'description': ds['description'],
    })
    new_links.append({'source': HUB_ID, 'target': ds['id']})

# ── Dreaming corpus node ──────────────────────────────────────────────────────
CORPUS_ID = 'artifact:dreaming-corpus'
new_nodes.append({
    'id': CORPUS_ID,
    'name': 'Dreaming Corpus',
    'type': 'artifact',
    'theme': 'ml-pipeline',
    'ext': '.zip',
    'size': 174 * 1024 * 1024,
    'isDir': False,
    'depth': 1,
    'clusterHub': HUB_ID,
    'label': f"{len(species_counts)} species · 1,255 images · 512×512",
    'description': (
        f"QC'd training dataset: {sum(species_counts.values())} images across {len(species_counts)} Salish Sea species at 512×512px. "
        "Assembled March 2026 from iNaturalist citizen science, Openverse open media, Briony Penn's watercolors, "
        "and collaborator footage. Commercial-use licenses only (CC BY, CC0, CC BY-SA, artist permission)."
    ),
    'artifactType': 'dataset',
})
new_links.append({'source': HUB_ID, 'target': CORPUS_ID})
# Flow from each data source → corpus
for ds in DATA_SOURCES:
    new_links.append({'source': ds['id'], 'target': CORPUS_ID, 'flow': True})

# ── Species nodes (depth 2, clustered under corpus) ──────────────────────────
# Canonical species names (merge orca duplicates etc.)
merged_counts = Counter()
for sp, count in species_counts.items():
    canonical = sp.strip()
    # Normalize variants
    if canonical.lower() in ('orca', 'orca swim', 'orca_swim'):
        canonical = 'Orca'
    elif canonical.lower() in ('kelp', 'bull kelp'):
        canonical = canonical  # keep separate
    elif canonical.lower() in ('eelgrass',):
        canonical = 'Eelgrass'
    elif canonical.lower() in ('octopus', 'giant pacific octopus'):
        canonical = canonical
    merged_counts[canonical] += count

for species_name, count in sorted(merged_counts.items(), key=lambda x: -x[1]):
    sp_id = 'species:' + re.sub(r'[^a-z0-9]+', '_', species_name.lower()).strip('_')
    srcs = list(species_sources.get(species_name, set()))
    new_nodes.append({
        'id': sp_id,
        'name': species_name,
        'type': 'species',
        'theme': 'ml-pipeline',
        'ext': '',
        'size': count * 4000,
        'isDir': False,
        'depth': 2,
        'clusterHub': HUB_ID,
        '_parentId': CORPUS_ID,
        'imageCount': count,
        'sources': srcs,
        'description': (
            f"{count} training images in the Salish Sea dreaming corpus. "
            + (f"Source: {', '.join(srcs)}." if srcs else "")
        ),
    })
    new_links.append({'source': CORPUS_ID, 'target': sp_id})

# ── GAN model node ────────────────────────────────────────────────────────────
GAN_ID = 'artifact:gan-model'
new_nodes.append({
    'id': GAN_ID,
    'name': 'Dreaming GAN',
    'type': 'artifact',
    'theme': 'ml-pipeline',
    'ext': '.pkl',
    'size': 364 * 1024 * 1024,
    'isDir': False,
    'depth': 1,
    'clusterHub': HUB_ID,
    'label': 'StyleGAN2 · 512×512 · training on H200',
    'status': 'training',
    'description': (
        'StyleGAN2 model trained on the full 49-species dreaming corpus. Currently at 2,000+ kimg on TELUS H200 GPU, '
        'targeting 3,000 kimg by setup day. Generates abstract organic textures that morph continuously through latent space. '
        'Two exhibition roles: (1) direct 8×8 ft wall projection via Autolume, (2) input to StreamDiffusion img2img.'
    ),
    'artifactType': 'model',
})
new_links.append({'source': HUB_ID, 'target': GAN_ID})
new_links.append({'source': CORPUS_ID, 'target': GAN_ID, 'flow': True})

# ── Briony LoRA node ──────────────────────────────────────────────────────────
LORA_ID = 'artifact:briony-lora'
new_nodes.append({
    'id': LORA_ID,
    'name': 'Briony LoRA',
    'type': 'artifact',
    'theme': 'ml-pipeline',
    'ext': '.safetensors',
    'size': 38 * 1024 * 1024,
    'isDir': False,
    'depth': 1,
    'clusterHub': HUB_ID,
    'label': '22 watercolors · rank 16 · SD 1.5',
    'description': (
        "Low-rank adaptation trained on 22 of Briony Penn's watercolor paintings. "
        'Injects her naturalist illustration style — luminous washes, organic line, ecological detail — '
        'into Stable Diffusion 1.5. Used with ControlNet for the TELUS-rendered video sequences (30 steps). '
        'Also being explored for real-time StreamDiffusion.'
    ),
    'artifactType': 'model',
})
new_links.append({'source': HUB_ID, 'target': LORA_ID})
new_links.append({'source': 'datasrc:briony-penn', 'target': LORA_ID, 'flow': True})
new_links.append({'source': 'hub:briony-art', 'target': LORA_ID})

# ── Autolume node ─────────────────────────────────────────────────────────────
AUTOLUME_ID = 'artifact:autolume'
new_nodes.append({
    'id': AUTOLUME_ID,
    'name': 'Autolume',
    'type': 'artifact',
    'theme': 'ml-pipeline',
    'ext': '',
    'size': 50 * 1024 * 1024,
    'isDir': False,
    'depth': 1,
    'clusterHub': HUB_ID,
    'label': 'StyleGAN2 latent nav · real-time · NDI out',
    'description': (
        'SFU MetaCreation Lab generative visual system. Navigates StyleGAN2 latent space in real time — '
        'smooth interpolation through the GAN\'s learned distribution of marine life. '
        'Audio-reactive, MIDI/OSC controlled. Outputs live video via NDI to TouchDesigner '
        'for the StreamDiffusion img2img pass.'
    ),
    'artifactType': 'software',
})
new_links.append({'source': HUB_ID, 'target': AUTOLUME_ID})
new_links.append({'source': GAN_ID, 'target': AUTOLUME_ID, 'flow': True})

# ── StreamDiffusion node ──────────────────────────────────────────────────────
SD_ID = 'artifact:streamdiffusion'
new_nodes.append({
    'id': SD_ID,
    'name': 'StreamDiffusion',
    'type': 'artifact',
    'theme': 'ml-pipeline',
    'ext': '',
    'size': 80 * 1024 * 1024,
    'isDir': False,
    'depth': 1,
    'clusterHub': HUB_ID,
    'label': 'SD-Turbo · 30fps · visitor prompts',
    'status': 'live',
    'description': (
        'Real-time img2img diffusion inside TouchDesigner at 30fps. Takes the Autolume NDI video feed '
        'as input and transforms it using visitor prompts — "salmon", "herring spawn", "bioluminescent kelp". '
        'The living visual language of the installation. Visitor voices literally reshape what the Salish Sea dreams.'
    ),
    'artifactType': 'software',
})
new_links.append({'source': HUB_ID, 'target': SD_ID})
new_links.append({'source': AUTOLUME_ID, 'target': SD_ID, 'flow': True})
new_links.append({'source': LORA_ID, 'target': SD_ID, 'flow': True})
# Connect to hub:visitor-voices if it exists
new_links.append({'source': 'hub:visitor-voices', 'target': SD_ID})

# ── Merge + write ─────────────────────────────────────────────────────────────
data['theme_colors']['ml-pipeline'] = '#7ab0aa'
data['nodes'].extend(new_nodes)
data['links'].extend(new_links)

# Update hub childCount
hub_node = next(n for n in data['nodes'] if n['id'] == HUB_ID)
hub_node['childCount'] = len([n for n in data['nodes'] if n.get('clusterHub') == HUB_ID and n['id'] != HUB_ID])

with open(GRAPH_JSON, 'w') as f:
    json.dump(data, f, separators=(',', ':'))

added_n = len(new_nodes)
added_l = len(new_links)
total_n = len(data['nodes'])
total_l = len(data['links'])
print(f'✓  Added {added_n} nodes ({len(merged_counts)} species + pipeline nodes)')
print(f'✓  Added {added_l} links ({sum(1 for l in new_links if l.get("flow"))} flow links)')
print(f'✓  Total: {total_n} nodes, {total_l} links')
print(f'\nSpecies cluster ({len(merged_counts)} species):')
for sp, count in sorted(merged_counts.items(), key=lambda x: -x[1])[:10]:
    print(f'   {count:3d}  {sp}')
print(f'   ... and {max(0,len(merged_counts)-10)} more')
