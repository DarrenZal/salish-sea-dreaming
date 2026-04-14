#!/usr/bin/env python3
"""
Phase 0: Generate redesigned data map JSON files.

Produces:
  - static/ssd-data-map-zoom.json  (7 hubs, 4-tier, signal chain, ecological categories)
  - static/ssd-cards.json          (card metadata with credits/attribution)

Run from repo root:
  python scripts/build_datamap_v2.py
"""

import csv
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO / "training-data" / "dreaming-model-512"
BRIONY_LORA_DIR = REPO / "briony-lora"
PROVENANCE_CSV = REPO / "training-data" / "provenance.csv"
OUT_GRAPH = REPO / "static" / "ssd-data-map-zoom.json"
OUT_CARDS = REPO / "static" / "ssd-cards.json"

# ── Ecological category mapping ──────────────────────────────────────────────

CATEGORY_MAP = {
    "cluster:salmon-forage": {
        "name": "Salmon & Forage Fish",
        "species": [
            "chinook_salmon", "coho_salmon", "sockeye_salmon", "pink_salmon",
            "chum_salmon", "pacific_herring", "herring_spawn",
            "northern_anchovy", "pacific_sand_lance", "eulachon",
        ],
    },
    "cluster:marine-mammals": {
        "name": "Marine Mammals",
        "species": [
            "orca", "humpback_whale", "minke_whale", "dalls_porpoise",
            "harbor_seal", "whale_underwater",
        ],
    },
    "cluster:seabirds": {
        "name": "Seabirds",
        "species": [
            "common_murre", "pigeon_guillemot", "marbled_murrelet",
            "tufted_puffin", "rhinoceros_auklet", "great_blue_heron",
            "bald_eagle", "eagle", "western_grebe", "common_loon",
        ],
    },
    "cluster:kelp-seagrass": {
        "name": "Kelp & Seagrass",
        "species": ["kelp", "bull_kelp", "eelgrass"],
    },
    "cluster:intertidal": {
        "name": "Intertidal",
        "species": [
            "ochre_sea_star", "sunflower_sea_star", "green_sea_urchin",
            "purple_sea_urchin", "aggregating_anemone", "giant_green_anemone",
            "giant_plumose_anemone", "opalescent_nudibranch",
            "lions_mane_jellyfish", "dungeness_crab", "red_rock_crab",
            "gumboot_chiton",
        ],
    },
    "cluster:cephalopods": {
        "name": "Cephalopods",
        "species": ["giant_pacific_octopus", "octopus"],
    },
    "cluster:rockfish-reef": {
        "name": "Rockfish & Reef",
        "species": ["copper_rockfish", "quillback_rockfish", "lingcod", "cabezon"],
    },
    "cluster:bears": {
        "name": "Bears",
        "species": ["black_bear"],
    },
}

# Reverse: species → category
SPECIES_TO_CATEGORY = {}
for cat_id, cat in CATEGORY_MAP.items():
    for sp in cat["species"]:
        SPECIES_TO_CATEGORY[sp] = cat_id

# ── Five Threads ─────────────────────────────────────────────────────────────

FIVE_THREADS = [
    {
        "id": "concept:salmon",
        "name": "Salmon",
        "subtitle": "Migration, cycles, return",
        "body": "The salmon thread traces the great cycle \u2014 ocean to river to forest and back. Salmon carry marine nutrients deep into the watershed, feeding eagles, bears, and ancient cedars. Their return is the pulse of the coast.",
        "connections": ["cluster:salmon-forage", "cluster:moonfish-footage"],
        "species": ["chinook_salmon", "coho_salmon", "sockeye_salmon", "pink_salmon", "chum_salmon"],
    },
    {
        "id": "concept:herring",
        "name": "Herring",
        "subtitle": "Foundation species \u2014 fishery tension, DFO",
        "body": "Pacific herring are the foundation of the Salish Sea food web. Their spawning events \u2014 turning the water milky white \u2014 feed hundreds of species. DFO management set baselines from 1953, a year that was already catastrophic. Indigenous nations like the Heiltsuk challenged this, taking over their own stock assessment.",
        "connections": ["cluster:salmon-forage", "cluster:herringfest"],
        "species": ["pacific_herring", "herring_spawn"],
    },
    {
        "id": "concept:orca",
        "name": "Orca",
        "subtitle": "Family, grief, resilience \u2014 J/K/L pods",
        "body": "The Southern Resident orca pods (J, K, and L) are a family in crisis. Down to ~75 individuals, they face starvation from depleted Chinook salmon, toxic bioaccumulation, and vessel noise. Tahlequah (J35) carried her dead calf for 17 days in 2018 \u2014 a mourning procession witnessed around the world.",
        "connections": ["cluster:marine-mammals", "cluster:moonfish-footage"],
        "species": ["orca", "whale_underwater"],
    },
    {
        "id": "concept:cedar",
        "name": "Cedar",
        "subtitle": "Long time, patience \u2014 forest health",
        "body": "Cedar represents deep time. A single western red cedar can live over a thousand years. Cedar is the tree of life for Coast Salish peoples \u2014 canoes, longhouses, regalia, medicine. The cedar thread asks: what does it mean to plan on a thousand-year timescale?",
        "connections": ["hub:knowledge"],
        "species": [],
        "tier": 1,
    },
    {
        "id": "concept:camas",
        "name": "Camas",
        "subtitle": "Restoration, community care \u2014 meadow restoration",
        "body": "Camas meadows were tended by Coast Salish peoples for millennia \u2014 burned, harvested, replanted. Colonization disrupted these relationships. Today, camas restoration projects are healing the land and rebuilding reciprocal care. The camas thread is about what grows back when we tend it.",
        "connections": ["hub:knowledge"],
        "species": [],
        "tier": 1,
    },
]

# ── Hub definitions ──────────────────────────────────────────────────────────

HUB_DEFS = [
    ("hub:ecosystem",      "The Salish Sea",       "#3a9a6a"),
    ("hub:artists",        "Artists & Witnesses",   "#d4956a"),
    ("hub:training",       "Training Corpus",       "#7a6aaa"),
    ("hub:machine",        "The Dreaming Machine",  "#7ab0aa"),
    ("hub:visitor-dreams", "Visitor Dreams",        "#7fffb2"),
    ("hub:knowledge",      "Knowledge & Research",  "#6a8aaa"),
    ("hub:exhibition",     "The Exhibition",        "#ba8a4a"),
]

# ── Helpers ──────────────────────────────────────────────────────────────────


def count_corpus_species():
    """Count images per species from dreaming-model-512 filenames."""
    counts = Counter()
    if not CORPUS_DIR.exists():
        return counts
    for f in CORPUS_DIR.iterdir():
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            # filename = Species_Name_hash.ext
            name = f.stem
            parts = name.rsplit("_", 1)
            sp = parts[0].lower() if len(parts) == 2 else name.lower()
            counts[sp] += 1
    return counts


def list_briony_lora_images():
    """List the 22 Briony watercolors used for LoRA training."""
    imgs = []
    if not BRIONY_LORA_DIR.exists():
        return imgs
    for f in sorted(BRIONY_LORA_DIR.iterdir()):
        if f.suffix.lower() == ".png" and "contact_sheet" not in f.name and "archive_not_in" not in f.name:
            imgs.append(f.name)
    return imgs


def load_provenance():
    """Parse provenance.csv → per-species credit data + per-file credit lookup."""
    species_credits = defaultdict(lambda: {
        "licenses": Counter(),
        "photographers": Counter(),
        "sources": Counter(),
        "total": 0,
    })
    # Per-file lookup: filename stem → {license, photographer, source}
    file_credits = {}

    if not PROVENANCE_CSV.exists():
        return species_credits, file_credits

    with open(PROVENANCE_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fn = row.get("filename", "")
            lic = row.get("license", "").strip()
            photographer = row.get("photographer_artist", "").strip()
            source = row.get("source", "").strip()

            # Skip NC-licensed
            if "nc" in lic.lower():
                continue

            # Per-file credit (keyed by filename stem, lowercase)
            base = fn.split("/")[-1]
            stem = Path(base).stem.lower()
            if stem and (lic or photographer):
                file_credits[stem] = {
                    "license": lic,
                    "photographer": photographer,
                    "source": source,
                }

            # Per-species aggregation
            parts = base.rsplit("_", 1)
            sp = parts[0].lower() if len(parts) == 2 else None
            if not sp:
                continue

            d = species_credits[sp]
            d["total"] += 1
            if lic:
                d["licenses"][lic] += 1
            if photographer:
                d["photographers"][photographer] += 1
            if source:
                d["sources"][source] += 1

    return species_credits, file_credits


def pretty_name(sp_id):
    """species_key → 'Species Key'"""
    return sp_id.replace("_", " ").title()


# ── Build graph ──────────────────────────────────────────────────────────────


def build_graph():
    nodes = []
    links = []
    corpus_counts = count_corpus_species()
    briony_lora_imgs = list_briony_lora_images()
    provenance, file_credits = load_provenance()

    # Build species → list of filenames for photo nodes
    corpus_files_by_species = defaultdict(list)
    if CORPUS_DIR.exists():
        for f in sorted(CORPUS_DIR.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                parts = f.stem.rsplit("_", 1)
                sp = parts[0].lower() if len(parts) == 2 else f.stem.lower()
                corpus_files_by_species[sp].append(f.name)

    # ── Hubs (tier 0) ────────────────────────────────────────────────────────
    for hub_id, hub_name, hub_color in HUB_DEFS:
        nodes.append({
            "id": hub_id,
            "name": hub_name,
            "type": "hub",
            "tier": 0,
            "clusterHub": hub_id,
            "color": hub_color,
        })

    # Hub-to-hub narrative flow edges (visible even when children are hidden)
    hub_flow = [
        ("hub:ecosystem",      "hub:training",       "training",        "Ecosystem species become training data"),
        ("hub:artists",        "hub:training",       "training",        "Artist contributions feed the corpus"),
        ("hub:training",       "hub:machine",        "signal",          "Corpus trains the dreaming machine"),
        # Bidirectional visitor ↔ machine
        ("hub:visitor-dreams", "hub:machine",        "visitor-signal",  "Visitors submit dreams to the machine"),
        ("hub:machine",        "hub:visitor-dreams",  "signal",          "Machine renders visitor dreams"),
        # Knowledge + Exhibition
        ("hub:knowledge",      "hub:ecosystem",      "conceptual",      "Research grounds the ecosystem story"),
        ("hub:exhibition",     "hub:machine",        "signal",          "Exhibition hosts the dreaming machine"),
        # Salish Sea as visual center
        ("hub:ecosystem",      "hub:machine",        "conceptual",      "The Salish Sea dreams through the machine"),
        ("hub:ecosystem",      "hub:exhibition",     "conceptual",      "The Salish Sea is exhibited"),
        ("hub:ecosystem",      "hub:visitor-dreams",  "conceptual",      "Visitors dream of the Salish Sea"),
    ]
    for src, tgt, lt, _desc in hub_flow:
        links.append({"source": src, "target": tgt, "linkType": lt})

    # ── Five Threads concept nodes (tier 0, ecosystem hub) ───────────────────
    for thread in FIVE_THREADS:
        nodes.append({
            "id": thread["id"],
            "name": thread["name"],
            "type": "concept",
            "tier": thread.get("tier", 0),
            "clusterHub": "hub:ecosystem",
            "subtitle": thread["subtitle"],
        })
        links.append({
            "source": "hub:ecosystem",
            "target": thread["id"],
            "linkType": "contains",
        })
        # Conceptual edges to categories/hubs
        for conn in thread["connections"]:
            links.append({
                "source": thread["id"],
                "target": conn,
                "linkType": "conceptual",
            })
        # Direct conceptual edges to individual species
        for sp in thread.get("species", []):
            sp_id = f"species:{sp}"
            links.append({
                "source": thread["id"],
                "target": sp_id,
                "linkType": "conceptual",
            })

    # ── Knowledge concepts (tier 0) ──────────────────────────────────────────
    nodes.append({
        "id": "concept:three-eyed-seeing",
        "name": "Three-Eyed Seeing",
        "type": "concept",
        "tier": 0,
        "clusterHub": "hub:knowledge",
        "subtitle": "Western science + Indigenous knowledge + the land itself",
    })
    links.append({"source": "hub:knowledge", "target": "concept:three-eyed-seeing", "linkType": "contains"})

    # ── Exhibition (tier 0) ──────────────────────────────────────────────────
    nodes.append({
        "id": "install:digital-ecologies",
        "name": "Digital Ecologies",
        "type": "installation",
        "tier": 0,
        "clusterHub": "hub:exhibition",
        "subtitle": "Salt Spring Art Show \u2014 Mahon Hall, Apr 10\u201326, 2026",
    })
    links.append({"source": "hub:exhibition", "target": "install:digital-ecologies", "linkType": "contains"})

    # Faint radial edges from exhibition to all other hubs
    for hub_id, _, _ in HUB_DEFS:
        if hub_id != "hub:exhibition":
            links.append({
                "source": "install:digital-ecologies",
                "target": hub_id,
                "linkType": "conceptual",
            })

    # ── Person nodes (tier 1) ────────────────────────────────────────────────
    people = [
        ("person:briony-penn",      "Briony Penn",       "hub:artists",     "Naturalist, illustrator \u2014 watercolors and ecological storytelling. Her art is the visual language of the Salish Sea."),
        ("person:moonfish-media",   "Moonfish Media",    "hub:artists",     "Underwater cinematography team capturing herring, salmon, and marine habitats. 13 videos, 416 frames used with collaborator permission."),
        ("person:david-denning",    "David Denning",     "hub:artists",     "Photographer \u2014 long-term bioregional witnessing. 14 high-resolution photos used with collaborator permission."),
        ("person:eve-marenghi",     "Eve Marenghi",      "hub:artists",     "Data scientist, Regen Commons steward. HerringFest documentation."),
        ("person:carol-anne-hilton", "Carol Anne Hilton", "hub:exhibition",  "Indigenomics founder, vision holder. Framework for relational value and Indigenous economic design."),
        ("person:prav-pillay",      "Pravin Pillay",     "hub:exhibition",  "Creative Director (MOVE37XR). TouchDesigner, AI visualization, immersive media. Studio: 108 Fraser Rd, Salt Spring."),
        ("person:darren-zal",       "Darren Zal",        "hub:knowledge",   "Systems architect. Built training corpus, gallery server, data map, and knowledge pipeline."),
        ("person:shawn-anderson",   "Shawn Anderson",    "hub:knowledge",   "Herring data science package \u2014 339 files of herring stock assessment analysis."),
        ("person:raf",              "Raf",               "hub:exhibition",  "Curator, Digital Ecologies exhibition at Mahon Hall."),
        ("person:brad-necyk",       "Brad Necyk",        "hub:artists",     "Artist and researcher, latent space concepts."),
        ("person:natalia-lebedinskaia", "Natalia Lebedinskaia", "hub:exhibition", "Panel moderation and contextual framing."),
    ]
    for pid, pname, phub, pbio in people:
        nodes.append({
            "id": pid,
            "name": pname,
            "type": "person",
            "tier": 1,
            "clusterHub": phub,
            "bio": pbio,
        })
        links.append({"source": phub, "target": pid, "linkType": "contains"})

    # Extra people edges
    links.append({"source": "person:shawn-anderson", "target": "cluster:herring-data-science", "linkType": "contains"})
    links.append({"source": "person:darren-zal", "target": "artifact:dreaming-gan", "linkType": "conceptual"})
    links.append({"source": "person:darren-zal", "target": "node:gallery-server", "linkType": "conceptual"})

    # ── Signal chain (tier 1, machine hub — revealed on hub click) ─────────
    signal_chain = [
        ("artifact:dreaming-gan", "Dreaming GAN",      "artifact"),
        ("artifact:autolume",     "Autolume",           "artifact"),
        ("node:touchdesigner",    "TouchDesigner",      "software"),
        ("artifact:streamdiffusion", "StreamDiffusion", "artifact"),
        ("output:projection",    "Projection",          "output"),
    ]
    for sid, sname, stype in signal_chain:
        nodes.append({
            "id": sid,
            "name": sname,
            "type": stype,
            "tier": 1,
            "clusterHub": "hub:machine",
        })
        links.append({"source": "hub:machine", "target": sid, "linkType": "contains"})

    # Signal edges (GAN → Autolume → TD → SD → Projection)
    signal_pairs = [
        ("artifact:dreaming-gan", "artifact:autolume"),
        ("artifact:autolume", "node:touchdesigner"),
        ("node:touchdesigner", "artifact:streamdiffusion"),
        ("artifact:streamdiffusion", "output:projection"),
    ]
    for src, tgt in signal_pairs:
        links.append({"source": src, "target": tgt, "linkType": "signal"})

    # Gallery server + QR portal (tier 1)
    nodes.append({
        "id": "node:gallery-server",
        "name": "Gallery Server",
        "type": "software",
        "tier": 1,
        "clusterHub": "hub:machine",
        "subtitle": "Visitor web app \u2192 OSC \u2192 TouchDesigner",
    })
    links.append({"source": "hub:machine", "target": "node:gallery-server", "linkType": "contains"})

    nodes.append({
        "id": "node:qr-portal",
        "name": "QR Portal",
        "type": "interface",
        "tier": 1,
        "clusterHub": "hub:machine",
        "subtitle": "Visitor entry point \u2014 scan to dream",
    })
    links.append({"source": "hub:machine", "target": "node:qr-portal", "linkType": "contains"})

    # Visitor signal path: QR → gallery_server → TD
    links.append({"source": "node:qr-portal", "target": "node:gallery-server", "linkType": "visitor-signal"})
    links.append({"source": "node:gallery-server", "target": "node:touchdesigner", "linkType": "visitor-signal"})
    # Also from visitor dreams hub → gallery server
    links.append({"source": "hub:visitor-dreams", "target": "node:gallery-server", "linkType": "visitor-signal"})

    # ── LoRA path (tier 0/1, machine hub) ────────────────────────────────────
    nodes.append({
        "id": "artifact:briony-lora",
        "name": "Briony LoRA",
        "type": "artifact",
        "tier": 1,
        "clusterHub": "hub:machine",
        "subtitle": "Style transfer model \u2014 22 watercolors distilled",
    })
    links.append({"source": "hub:machine", "target": "artifact:briony-lora", "linkType": "contains"})

    nodes.append({
        "id": "cluster:briony-training-set",
        "name": "Briony Training Set",
        "type": "cluster-summary",
        "tier": 1,
        "clusterHub": "hub:machine",
        "childCount": len(briony_lora_imgs),
        "subtitle": f"{len(briony_lora_imgs)} watercolors used for LoRA training",
    })
    links.append({"source": "hub:machine", "target": "cluster:briony-training-set", "linkType": "contains"})

    # LoRA training edges (salmon-pink)
    links.append({"source": "cluster:briony-training-set", "target": "artifact:briony-lora", "linkType": "training-lora"})
    links.append({"source": "artifact:briony-lora", "target": "artifact:streamdiffusion", "linkType": "training-lora"})

    # ── TD internal nodes (tier 1, inside TD) ────────────────────────────────
    td_internals = [
        ("td:ndi-in",      "NDI In TOP",            "Receives Autolume video feed"),
        ("td:kinect",      "Kinect CHOP",           "Presence and depth sensing"),
        ("td:osc-in",      "OSC In DAT",            "Receives visitor prompts from gallery server"),
        ("td:prompt-seq",  "Prompt Sequencer",      "Cycles 23 ecological prompts (26s each, 6s crossfade). Visitor dreams interrupt for 30s with smooth fade."),
        ("td:sd-tox",      "StreamDiffusion TOX",   "Real-time img2img inference at 30fps"),
        ("td:boids-sop",   "Boids SOP",             "Intent field \u2014 flocking fish simulation"),
        ("td:output",      "Output TOP",            "Final composite to projector"),
    ]
    for tid, tname, tsub in td_internals:
        nodes.append({
            "id": tid,
            "name": tname,
            "type": "td-internal",
            "tier": 1,
            "clusterHub": "hub:machine",
            "_parentId": "node:touchdesigner",
            "subtitle": tsub,
        })
        links.append({"source": "node:touchdesigner", "target": tid, "linkType": "contains"})

    # Internal signal flow through TD
    td_signal = [
        ("td:ndi-in", "td:sd-tox"),
        ("td:osc-in", "td:prompt-seq"),
        ("td:prompt-seq", "td:sd-tox"),
        ("td:sd-tox", "td:output"),
    ]
    for src, tgt in td_signal:
        links.append({"source": src, "target": tgt, "linkType": "signal"})

    # ── Ecological category clusters (tier 1, training hub) ──────────────────
    total_corpus_images = 0
    for cat_id, cat in CATEGORY_MAP.items():
        cat_image_count = sum(corpus_counts.get(sp, 0) for sp in cat["species"])
        total_corpus_images += cat_image_count
        species_in_cat = [sp for sp in cat["species"] if corpus_counts.get(sp, 0) > 0]

        nodes.append({
            "id": cat_id,
            "name": cat["name"],
            "type": "cluster-summary",
            "tier": 1,
            "clusterHub": "hub:training",
            "childCount": len(species_in_cat),
            "imageCount": cat_image_count,
        })
        links.append({"source": "hub:training", "target": cat_id, "linkType": "contains"})

        # Training flow: category → GAN
        links.append({"source": cat_id, "target": "artifact:dreaming-gan", "linkType": "training"})

        # Species nodes (tier 2 under category) + photo nodes (tier 3)
        for sp in cat["species"]:
            count = corpus_counts.get(sp, 0)
            if count == 0:
                continue
            sp_id = f"species:{sp}"
            nodes.append({
                "id": sp_id,
                "name": pretty_name(sp),
                "type": "species",
                "tier": 2,
                "clusterHub": "hub:training",
                "_parentId": cat_id,
                "imageCount": count,
            })
            links.append({"source": cat_id, "target": sp_id, "linkType": "contains"})

            # Photo nodes (tier 3 under species)
            photo_files = sorted(corpus_files_by_species.get(sp, []))
            for pf in photo_files:
                stem = Path(pf).stem
                photo_id = f"photo:{stem}"
                nodes.append({
                    "id": photo_id,
                    "name": pretty_name(sp),
                    "type": "photo",
                    "tier": 3,
                    "clusterHub": "hub:training",
                    "_parentId": sp_id,
                    "thumbUrl": f"/graph-assets/thumbs/{stem}.jpg",
                    "fullUrl": f"/graph-assets/corpus/{pf}",
                })
                links.append({"source": sp_id, "target": photo_id, "linkType": "contains"})

    # ── Training corpus summary node (tier 0, for total count) ───────────────
    nodes.append({
        "id": "artifact:dreaming-corpus",
        "name": "Dreaming Corpus",
        "type": "artifact",
        "tier": 1,
        "clusterHub": "hub:training",
        "imageCount": total_corpus_images,
        "subtitle": f"{total_corpus_images:,} images \u2014 50 species",
    })
    links.append({"source": "hub:training", "target": "artifact:dreaming-corpus", "linkType": "contains"})
    # Corpus → GAN training edge
    links.append({"source": "artifact:dreaming-corpus", "target": "artifact:dreaming-gan", "linkType": "training"})

    # ── Artists hub content ──────────────────────────────────────────────────

    # Briony works archive cluster (tier 1)
    nodes.append({
        "id": "cluster:briony-works",
        "name": "Briony Penn Archive",
        "type": "cluster-summary",
        "tier": 1,
        "clusterHub": "hub:artists",
        "childCount": 519,
        "subtitle": "519 paintings, illustrations, and field journals",
        "body": "519 paintings, illustrations, and field journals from Briony Penn\u2019s decades of natural history work. Source material for the Briony LoRA style transfer model.",
    })
    links.append({"source": "hub:artists", "target": "cluster:briony-works", "linkType": "contains"})
    links.append({"source": "person:briony-penn", "target": "cluster:briony-works", "linkType": "contains"})

    # Moonfish footage cluster (tier 1)
    nodes.append({
        "id": "cluster:moonfish-footage",
        "name": "Moonfish Footage",
        "type": "cluster-summary",
        "tier": 1,
        "clusterHub": "hub:artists",
        "childCount": 13,
        "subtitle": "13 underwater videos, 416 extracted frames",
        "license": "collaborator permission",
        "body": "13 underwater videos of herring spawning, salmon migration, marine habitats. 416 frames extracted. Layer 1 of the projection uses this footage cross-faded with ControlNet+LoRA style-transferred versions.",
    })
    links.append({"source": "hub:artists", "target": "cluster:moonfish-footage", "linkType": "contains"})
    links.append({"source": "person:moonfish-media", "target": "cluster:moonfish-footage", "linkType": "contains"})
    # Training flow from Moonfish → corpus
    links.append({"source": "cluster:moonfish-footage", "target": "hub:training", "linkType": "training"})

    # Denning photos cluster (tier 1)
    nodes.append({
        "id": "cluster:denning-photos",
        "name": "Denning Photos",
        "type": "cluster-summary",
        "tier": 1,
        "clusterHub": "hub:artists",
        "childCount": 14,
        "subtitle": "14 high-resolution bioregional photographs",
        "license": "collaborator permission",
        "body": "14 high-resolution photographs of Salish Sea coastline, intertidal zones, forests. Long-term bioregional witnessing.",
    })
    links.append({"source": "hub:artists", "target": "cluster:denning-photos", "linkType": "contains"})
    links.append({"source": "person:david-denning", "target": "cluster:denning-photos", "linkType": "contains"})
    links.append({"source": "cluster:denning-photos", "target": "hub:training", "linkType": "training"})

    # HerringFest cluster (tier 1)
    nodes.append({
        "id": "cluster:herringfest",
        "name": "HerringFest",
        "type": "cluster-summary",
        "tier": 1,
        "clusterHub": "hub:artists",
        "childCount": 65,
        "subtitle": "HerringFest documentation \u2014 Eve Marenghi",
        "body": "65 documentary images from HerringFest on Salt Spring Island \u2014 community celebration of Pacific herring. Documented by Eve Marenghi.",
    })
    links.append({"source": "hub:artists", "target": "cluster:herringfest", "linkType": "contains"})
    links.append({"source": "person:eve-marenghi", "target": "cluster:herringfest", "linkType": "contains"})

    # ── Knowledge hub content ────────────────────────────────────────────────
    knowledge_nodes = [
        ("doc:herring-report-i",      "The Salish Sea Herring",     "report",  "DFO management, shifting baselines, Indigenous rights, trophic cascade"),
        ("doc:herring-report-ii",     "The Living Salish Sea",      "report",  "Ecosystem health, Hornby stronghold, food web, conservation models"),
        ("cluster:herring-data-science", "Herring Data Science",    "cluster-summary", "Shawn Anderson\u2019s data package \u2014 339 files of herring analysis"),
    ]
    for kid, kname, ktype, ksub in knowledge_nodes:
        node_dict = {
            "id": kid,
            "name": kname,
            "type": ktype,
            "tier": 1,
            "clusterHub": "hub:knowledge",
            "subtitle": ksub,
        }
        if kid == "cluster:herring-data-science":
            node_dict["body"] = "339 files of Pacific herring stock assessment, DFO catch data, population models, and statistical analysis. Shawn Anderson\u2019s quantitative foundation for the herring thread."
        nodes.append(node_dict)
        links.append({"source": "hub:knowledge", "target": kid, "linkType": "contains"})

    # Digital Ecologies book node
    nodes.append({
        "id": "doc:digital-ecologies-book",
        "name": "Digital Ecologies: Mediating More-Than-Human Worlds",
        "type": "report",
        "tier": 1,
        "clusterHub": "hub:knowledge",
        "subtitle": "CC BY 4.0 \u2014 Turnbull, Searle, Anderson-Elliott, Giraud (eds.), Manchester University Press, 2024",
    })
    links.append({"source": "hub:knowledge", "target": "doc:digital-ecologies-book", "linkType": "contains"})
    links.append({"source": "doc:digital-ecologies-book", "target": "install:digital-ecologies", "linkType": "conceptual"})

    # ── Briony in Training Corpus (54 images distributed across categories) ──
    # Her images are "artist permission" in provenance, already in the corpus
    # The 54 briony-marine-colour images are spread across categories naturally
    # This is represented by the fact that species clusters contain her work

    # ── Briony triple presence links ─────────────────────────────────────────
    # Artists hub: person:briony-penn → cluster:briony-works (above)
    # Training hub: her 54 images are inside species clusters (implicit)
    # Machine hub: cluster:briony-training-set → artifact:briony-lora (above)

    # ── Data source badges for training corpus ───────────────────────────────
    datasource_nodes = [
        ("datasrc:inaturalist",  "iNaturalist",     "CC BY / CC0"),
        ("datasrc:openverse",    "Openverse",        "CC BY / CC0 / CC BY-SA"),
        ("datasrc:briony-penn",  "Briony Penn",      "Artist permission \u2014 54 watercolors"),
    ]
    for dsid, dsname, dslic in datasource_nodes:
        nodes.append({
            "id": dsid,
            "name": dsname,
            "type": "ml-source",
            "tier": 1,
            "clusterHub": "hub:training",
            "subtitle": dslic,
        })
        links.append({"source": "hub:training", "target": dsid, "linkType": "contains"})
        links.append({"source": dsid, "target": "artifact:dreaming-corpus", "linkType": "training"})

    # ── Precompute tier-0 positions (normalized 0–1) ────────────────────────
    import math
    hub_ids = [h[0] for h in HUB_DEFS]
    hub_positions = {}
    for i, hid in enumerate(hub_ids):
        angle = (2 * math.pi / len(hub_ids)) * i - math.pi / 2
        hub_positions[hid] = (0.5 + math.cos(angle) * 0.32, 0.5 + math.sin(angle) * 0.32)

    # Assign positions to all tier-0 nodes
    # First, group children by hub
    hub_children = defaultdict(list)
    for n in nodes:
        if n.get("tier") != 0:
            continue
        nid = n["id"]
        if nid in hub_positions:
            n["px"], n["py"] = hub_positions[nid]
        else:
            hub_children[n.get("clusterHub", "hub:ecosystem")].append(n)

    # Position children in concentric rings around each hub
    for hub_id, children in hub_children.items():
        hx, hy = hub_positions.get(hub_id, (0.5, 0.5))
        count = len(children)
        if count == 0:
            continue
        # Ring layout: inner radius avoids hub, rings hold ~10 nodes each
        ring_capacity = 16
        min_radius = 0.05  # minimum distance from hub center
        ring_gap = 0.035   # distance between rings
        idx = 0
        for n in children:
            ring = idx // ring_capacity
            pos_in_ring = idx % ring_capacity
            ring_count = min(ring_capacity, count - ring * ring_capacity)
            radius = min_radius + ring * ring_gap
            angle = (2 * math.pi / ring_count) * pos_in_ring + ring * 0.5  # offset each ring
            n["px"] = max(0.03, min(0.97, hx + math.cos(angle) * radius))
            n["py"] = max(0.03, min(0.97, hy + math.sin(angle) * radius))
            idx += 1

    return nodes, links, total_corpus_images


# ── Build cards ──────────────────────────────────────────────────────────────


def build_cards(nodes, provenance_credits, file_credits=None):
    cards = {}
    species_cards = {}

    for node in nodes:
        nid = node["id"]
        card = {"title": node["name"]}

        if node["type"] == "hub":
            hub_descs = {
                "hub:ecosystem": "The Salish Sea ecosystem \u2014 a living web of salmon, herring, orca, kelp, and hundreds of interconnected species. The Five Threads weave through it.",
                "hub:artists": "The artists and witnesses whose eyes, cameras, and brushes became the project\u2019s sensory organs. Their work is the raw perception.",
                "hub:training": "1,255 images across 50 species \u2014 the visual corpus that trained the Dreaming GAN. Every image is CC-licensed or used with permission.",
                "hub:machine": "The dreaming machine. Three projection layers: L1 = Moonfish footage cross-faded with ControlNet+LoRA style-transferred versions. L2 = StreamDiffusion real-time watercolor at 30fps. L3 = Raw Autolume GAN dreams. All composited in Resolume Arena onto the 8\u00d78 ft wall.",
                "hub:visitor-dreams": "Your words become dreams. Speak or type at the QR portal \u2014 your vision travels through GPT filtering, OSC, and TouchDesigner to the projection wall. The machine renders your dream back to you. Bidirectional: your words travel to the machine; its dreams travel back to the wall.",
                "hub:knowledge": "Reports, data, and Indigenous knowledge that ground the project. The Kwaxala model. Three-Eyed Seeing. The herring story.",
                "hub:exhibition": "Digital Ecologies: Bridging Nature and Technology \u2014 Salt Spring Art Show at Mahon Hall, April 10\u201326, 2026.",
            }
            card["body"] = hub_descs.get(nid, "")

        elif node["type"] == "concept":
            # Find matching thread
            for thread in FIVE_THREADS:
                if thread["id"] == nid:
                    card["subtitle"] = thread["subtitle"]
                    card["body"] = thread["body"]
                    break
            else:
                if nid == "concept:three-eyed-seeing":
                    card["subtitle"] = "Western science + Indigenous knowledge + the land itself"
                    card["body"] = "Three-Eyed Seeing integrates Western scientific observation, Indigenous Traditional Knowledge, and direct perception from the land itself. Not a hierarchy but a braiding \u2014 each eye sees what the others cannot."

        elif node["type"] == "person":
            card["body"] = node.get("bio", "")
            card["tags"] = ["person"]

        elif node["type"] == "installation":
            card["subtitle"] = node.get("subtitle", "")
            card["body"] = "An interactive AI art installation exploring the Salish Sea ecosystem. The vision: not humans looking at nature through technology, but the Salish Sea using technology to perceive itself. Curated by Raf for the Digital Ecologies show."
            card["tags"] = ["exhibition"]

        elif node["type"] == "cluster-summary":
            card["subtitle"] = node.get("subtitle", "")
            if node.get("license") == "collaborator permission":
                card["tags"] = ["collaborator permission"]
                if not node.get("body"):
                    card["body"] = f"Used with collaborator permission from {node['name'].split()[0]}."
            elif node.get("imageCount"):
                card["imageCount"] = node["imageCount"]
                card["childCount"] = node.get("childCount", 0)
                # Aggregate credits for this category
                cat_def = CATEGORY_MAP.get(nid)
                if cat_def:
                    license_totals = Counter()
                    photographer_totals = Counter()
                    for sp in cat_def["species"]:
                        sp_lower = sp.lower()
                        creds = provenance_credits.get(sp_lower, provenance_credits.get(sp, {}))
                        if creds:
                            for lic, cnt in creds.get("licenses", {}).items():
                                license_totals[lic] += cnt
                            for ph, cnt in creds.get("photographers", {}).items():
                                photographer_totals[ph] += cnt
                    if license_totals:
                        card["licenses"] = dict(license_totals.most_common())
                    if photographer_totals:
                        card["photographers"] = dict(photographer_totals.most_common(10))

            card["body"] = card.get("body", node.get("body", f"{node.get('childCount', '')} items in this collection."))

        elif node["type"] == "species":
            sp_key = nid.replace("species:", "")
            card["imageCount"] = node.get("imageCount", 0)

            # Credits from provenance
            creds = provenance_credits.get(sp_key, {})
            if creds:
                if creds.get("licenses"):
                    card["licenses"] = dict(creds["licenses"].most_common())
                if creds.get("photographers"):
                    card["photographers"] = dict(creds["photographers"].most_common(5))
                if creds.get("sources"):
                    card["sources"] = dict(creds["sources"].most_common())
            card["body"] = f"{node.get('imageCount', 0)} images in the training corpus."

            # Also store in species section
            species_cards[nid] = {
                "title": node["name"],
                "imageCount": node.get("imageCount", 0),
                "groups": [SPECIES_TO_CATEGORY.get(sp_key, "").replace("cluster:", "")],
            }

        elif node["type"] in ("artifact", "software", "output", "interface"):
            subtitles = {
                "artifact:dreaming-gan": "StyleGAN2-ada (320 kimg), ~1,255 images of 49 species. Abstract organic textures. Dual role: direct projection via Autolume + input to StreamDiffusion.",
                "artifact:autolume": "SFU MetaCreation Lab. Real-time latent space navigation. Audio-reactive, OSC. Layer 3 of projection: raw GAN dreams. Also feeds StreamDiffusion as img2img input.",
                "node:touchdesigner": "Integration hub. Autolume video via NDI, visitor prompts via OSC. Prompt Sequencer cycles 23 ecological prompts (26s each, 6s crossfade). StreamDiffusion runs inside as TOX.",
                "artifact:streamdiffusion": "30fps img2img with SD-Turbo inside TD. Takes Autolume GAN output + 23 cycling prompts. Layer 2: real-time watercolor via Briony LoRA. Visitor dreams interrupt the cycle for 30s.",
                "output:projection": "The key node. 8\u00d78 ft wall. Three layers in Resolume Arena: L1=Moonfish footage cross-faded with same footage through SD 1.5 + Briony LoRA + ControlNet depth (20 steps). L2=StreamDiffusion real-time watercolor. L3=Raw Autolume GAN.",
                "artifact:briony-lora": "LoRA rank 16, 22 watercolors, SD 1.5. Used in L1 (briony_video_style.py + RAFT smoothing) and L2 (StreamDiffusion real-time). Prompt: \"brionypenn watercolor painting, Pacific Northwest coastal ecosystem\".",
                "node:gallery-server": "FastAPI server. Processes visitor text through GPT-4.1-mini for content filtering. OSC to TouchDesigner. SQLite for submissions. SSE for live updates.",
                "node:qr-portal": "Scan QR \u2192 phone browser \u2192 type/speak \u2192 30s on projection wall.",
            }
            card["body"] = subtitles.get(nid, node.get("subtitle", ""))

        elif node["type"] == "td-internal":
            card["body"] = node.get("subtitle", "")
            card["tags"] = ["touchdesigner"]

        elif node["type"] == "ml-source":
            card["body"] = f"Data source: {node.get('subtitle', '')}. Images scraped, QC\u2019d, and curated for the dreaming corpus."

        elif node["type"] == "report":
            card["body"] = node.get("subtitle", "")
            card["tags"] = ["research"]

        elif node["type"] == "photo":
            # Look up per-file provenance by filename stem
            stem = nid.replace("photo:", "").lower()
            fc = (file_credits or {}).get(stem, {})
            species_name = node.get("name", "")
            photographer = fc.get("photographer", "")
            lic = fc.get("license", "")
            source = fc.get("source", "")

            # Build narrative body
            parts = [f"This photograph of {species_name} was part of the training corpus "
                     f"for the Dreaming GAN \u2014 the AI model that powers the Salish Sea "
                     f"Dreaming installation at Mahon Hall."]
            if photographer:
                parts.append(f"Photographed by {photographer}.")
            if source:
                parts.append(f"Source: {source}.")
            if lic:
                parts.append(f"License: {lic.upper()}.")
            parts.append("Along with 1,254 other images across 50 species, "
                         "this photo taught the machine to dream in the visual language "
                         "of the Salish Sea.")
            card["body"] = " ".join(parts)
            if photographer:
                card["artist"] = photographer
            if lic:
                card["tags"] = [lic]

        cards[nid] = card

    return cards, species_cards


# ── Phase 6: Process Digital Ecologies PDFs ─────────────────────────────────

# Keyword → graph node ID mapping for auto-tagging
TAG_KEYWORDS = {
    "hub:ecosystem": ["species", "ecosystem", "ecology", "biodiversity", "habitat", "wildlife",
                      "salmon", "herring", "orca", "kelp", "marine", "ocean", "salish"],
    "hub:machine": ["technology", "machine", "algorithm", "computation", "digital", "software",
                    "neural", "model", "AI", "artificial intelligence", "generative"],
    "hub:knowledge": ["knowledge", "research", "indigenous", "traditional", "epistemology",
                      "ontology", "data", "science", "methodology"],
    "hub:artists": ["art", "artist", "creative", "visual", "painting", "photography",
                    "cinema", "film", "aesthetics", "representation"],
    "hub:exhibition": ["exhibition", "gallery", "installation", "museum", "curation",
                       "display", "audience", "visitor", "public"],
    "concept:three-eyed-seeing": ["three-eyed", "braiding", "indigenous knowledge",
                                   "western science", "ways of knowing"],
    "artifact:streamdiffusion": ["diffusion", "style transfer", "real-time", "img2img",
                                  "visualization"],
    "hub:visitor-dreams": ["participation", "interactive", "engagement", "audience",
                           "co-creation"],
}


def process_digital_ecologies():
    """Extract and chunk Digital Ecologies CC BY PDFs for chat context.

    Reads from docs/digital-ecologies/ in the repo.
    Returns list of chunk dicts. Writes to static/ssd-context-docs.json.
    Skips gracefully if PyPDF2 is not installed or PDFs are missing.
    """
    try:
        import PyPDF2
    except ImportError:
        print("WARNING: PyPDF2 not installed. Skipping Digital Ecologies PDF processing.")
        print("  Install with: pip install PyPDF2")
        return []

    pdf_dir = REPO / "docs" / "digital-ecologies"
    if not pdf_dir.exists():
        print(f"WARNING: {pdf_dir} not found. Skipping PDF processing.")
        return []

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"WARNING: No PDFs found in {pdf_dir}. Skipping PDF processing.")
        return []

    chunks = []
    chunk_id = 0

    for pdf_path in pdf_files:
        print(f"  Processing: {pdf_path.name}")
        try:
            reader = PyPDF2.PdfReader(str(pdf_path))
        except Exception as e:
            print(f"  WARNING: Could not read {pdf_path.name}: {e}")
            continue

        # Extract text page by page
        pages_text = []
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text and text.strip():
                    pages_text.append((page_num, text.strip()))
            except Exception as e:
                print(f"  WARNING: Could not extract page {page_num}: {e}")
                continue

        if not pages_text:
            print(f"  WARNING: No text extracted from {pdf_path.name}")
            continue

        # Chunk by paragraphs, keeping ~500-800 tokens per chunk
        # Approximate: 1 token ~ 4 characters
        current_chunk_lines = []
        current_chunk_chars = 0
        chunk_start_page = pages_text[0][0] if pages_text else 1
        current_heading = pdf_path.stem  # default heading

        for page_num, page_text in pages_text:
            paragraphs = page_text.split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Detect headings (short lines, often uppercase or title case)
                is_heading = (len(para) < 100 and not para.endswith(".")
                              and para == para.title() or para.isupper()) and len(para) > 3

                if is_heading:
                    current_heading = para[:80]

                para_chars = len(para)

                # If adding this paragraph would exceed ~800 tokens (~3200 chars)
                # and we already have content, flush the current chunk
                if current_chunk_chars + para_chars > 3200 and current_chunk_chars > 0:
                    chunk_text = "\n\n".join(current_chunk_lines)
                    chunk_end_page = page_num
                    tags = _auto_tag_chunk(chunk_text)
                    chunks.append({
                        "id": f"de-chunk-{chunk_id}",
                        "title": current_heading,
                        "text": chunk_text,
                        "source": "Digital Ecologies Book",
                        "license": "CC BY 4.0",
                        "authors": "Turnbull, Searle, Anderson-Elliott, Giraud",
                        "page_range": f"{chunk_start_page}-{chunk_end_page}",
                        "tags": tags,
                    })
                    chunk_id += 1
                    current_chunk_lines = []
                    current_chunk_chars = 0
                    chunk_start_page = page_num

                current_chunk_lines.append(para)
                current_chunk_chars += para_chars

        # Flush remaining content
        if current_chunk_lines:
            chunk_text = "\n\n".join(current_chunk_lines)
            tags = _auto_tag_chunk(chunk_text)
            chunks.append({
                "id": f"de-chunk-{chunk_id}",
                "title": current_heading,
                "text": chunk_text,
                "source": "Digital Ecologies Book",
                "license": "CC BY 4.0",
                "authors": "Turnbull, Searle, Anderson-Elliott, Giraud",
                "page_range": f"{chunk_start_page}-{pages_text[-1][0]}",
                "tags": tags,
            })
            chunk_id += 1

    # Write output
    out_path = REPO / "static" / "ssd-context-docs.json"
    with open(out_path, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"  Wrote {out_path} ({len(chunks)} chunks, {os.path.getsize(out_path):,} bytes)")

    return chunks


def _auto_tag_chunk(text):
    """Auto-tag a chunk with graph node IDs based on keyword overlap."""
    text_lower = text.lower()
    tags = []
    for node_id, keywords in TAG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score >= 2:  # require at least 2 keyword matches
            tags.append(node_id)
    return tags


# ── Phase 7: Data Exports ───────────────────────────────────────────────────

# Hub display order for markdown export
HUB_SECTIONS = [
    ("hub:exhibition",     "The Exhibition"),
    ("hub:ecosystem",      "The Salish Sea"),
    ("hub:artists",        "Artists & Witnesses"),
    ("hub:training",       "Training Corpus"),
    ("hub:machine",        "The Dreaming Machine"),
    ("hub:visitor-dreams", "Visitor Dreams"),
    ("hub:knowledge",      "Knowledge & Research"),
]


def sanitize_for_export(node):
    """Strip internal IPs, file paths, and admin details from a node dict."""
    import re
    cleaned = dict(node)

    # Remove fullUrl if it contains an IP address
    full_url = cleaned.get("fullUrl", "")
    if full_url and re.search(r"\d+\.\d+\.\d+\.\d+", full_url):
        del cleaned["fullUrl"]

    # Remove any field containing filesystem paths
    for key in list(cleaned.keys()):
        val = cleaned[key]
        if isinstance(val, str):
            if "/home/" in val or "/Users/" in val or "C:\\" in val:
                cleaned[key] = re.sub(r"(/home/|/Users/|C:\\)[^\s,;\"']+", "[path removed]", val)
            # Remove internal IPs
            if re.search(r"\b(?:10\.\d+|127\.0\.0\.1|37\.27\.48\.12|192\.168)\.\d+\.\d+(?::\d+)?\b", val):
                cleaned[key] = re.sub(
                    r"\b(?:10\.\d+|127\.0\.0\.1|37\.27\.48\.12|192\.168)\.\d+\.\d+(?::\d+)?\b",
                    "[server]", val
                )

    return cleaned


def export_markdown(nodes, links, cards):
    """Generate static/ssd-data-export.md with all nodes organized by hub."""
    lines = []
    lines.append("# Salish Sea Dreaming -- Data Map\n")
    lines.append("**Interactive knowledge graph for the Salish Sea Dreaming AI art installation**\n")
    lines.append("- **Exhibition:** Digital Ecologies: Bridging Nature and Technology")
    lines.append("- **Venue:** Mahon Hall, Salt Spring Island, BC")
    lines.append("- **Dates:** April 10--26, 2026")
    lines.append("- **Creator:** Salish Sea Dreaming Collective")
    lines.append("- **License:** Mixed -- see per-asset licenses")
    lines.append("- **Date Published:** 2026-04-10")
    lines.append("")

    # Build lookup structures
    node_by_id = {n["id"]: n for n in nodes}
    outgoing = defaultdict(list)  # source → [(target, linkType)]
    incoming = defaultdict(list)  # target → [(source, linkType)]
    for link in links:
        outgoing[link["source"]].append((link["target"], link["linkType"]))
        incoming[link["target"]].append((link["source"], link["linkType"]))

    for hub_id, section_title in HUB_SECTIONS:
        lines.append(f"\n## {section_title}\n")

        # Hub description from cards
        hub_card = cards.get(hub_id, {})
        if hub_card.get("body"):
            lines.append(f"{hub_card['body']}\n")

        # Collect nodes belonging to this hub
        hub_nodes = [n for n in nodes if n.get("clusterHub") == hub_id and n["id"] != hub_id]
        # Sort: tier 0 first, then tier 1, then by name
        hub_nodes.sort(key=lambda n: (n.get("tier", 99), n.get("name", "")))

        for node in hub_nodes:
            nid = node["id"]
            clean = sanitize_for_export(node)
            card = cards.get(nid, {})
            name = clean.get("name", nid)
            ntype = clean.get("type", "")
            tier = clean.get("tier", "")

            lines.append(f"### {name}")
            lines.append(f"Type: {ntype} | Tier: {tier}")

            # Description from card
            body = card.get("body", "")
            if body:
                # Sanitize body text too
                import re
                body = re.sub(r"\b(?:10\.\d+|127\.0\.0\.1|37\.27\.48\.12|192\.168)\.\d+\.\d+(?::\d+)?\b", "[server]", body)
                body = re.sub(r"(/home/|/Users/|C:\\)[^\s,;\"']+", "[path removed]", body)
                lines.append(f"\n{body}")

            # Connections
            out_links = outgoing.get(nid, [])
            in_links = incoming.get(nid, [])
            if out_links or in_links:
                conn_parts = []
                for target, lt in out_links:
                    tname = node_by_id.get(target, {}).get("name", target)
                    conn_parts.append(f"-> {tname} ({lt})")
                for source, lt in in_links:
                    sname = node_by_id.get(source, {}).get("name", source)
                    conn_parts.append(f"<- {sname} ({lt})")
                lines.append(f"\nConnections: {', '.join(conn_parts[:10])}")
                if len(out_links) + len(in_links) > 10:
                    lines.append(f"  ...and {len(out_links) + len(in_links) - 10} more")

            lines.append("")

    out_path = REPO / "static" / "ssd-data-export.md"
    content = "\n".join(lines)
    with open(out_path, "w") as f:
        f.write(content)
    print(f"Wrote {out_path} ({os.path.getsize(out_path):,} bytes)")


def export_jsonld(nodes, links, cards):
    """Generate static/ssd-data-export.jsonld with schema.org types."""
    import re

    # Schema.org type mapping
    type_map = {
        "hub":              "schema:Thing",
        "concept":          "schema:Thing",
        "person":           "schema:Person",
        "report":           "schema:ScholarlyArticle",
        "species":          "schema:Thing",
        "artifact":         "schema:SoftwareApplication",
        "software":         "schema:SoftwareApplication",
        "output":           "schema:Thing",
        "interface":        "schema:Thing",
        "installation":     "schema:ExhibitionEvent",
        "cluster-summary":  "schema:Collection",
        "td-internal":      "schema:SoftwareApplication",
        "ml-source":        "schema:Dataset",
        "photo":            "schema:ImageObject",
    }

    # Edge type mapping
    edge_type_map = {
        "contains":        "schema:hasPart",
        "training":        "ssd:trainedBy",
        "signal":          "ssd:feedsInto",
        "visitor-signal":  "ssd:visitorSignal",
        "conceptual":      "ssd:relatedTo",
        "training-lora":   "ssd:loraTraining",
    }

    def node_iri(nid):
        """Convert node ID to valid IRI: replace colons with hyphens."""
        return f"ssd:{nid.replace(':', '-')}"

    # Build @graph
    graph_nodes = []
    node_by_id = {n["id"]: n for n in nodes}

    for node in nodes:
        clean = sanitize_for_export(node)
        nid = node["id"]
        card = cards.get(nid, {})

        entry = {
            "@id": node_iri(nid),
            "@type": type_map.get(clean.get("type", ""), "schema:Thing"),
            "schema:name": clean.get("name", nid),
            "ssd:nodeType": clean.get("type", ""),
            "ssd:tier": clean.get("tier", 0),
        }

        # Add description from card
        body = card.get("body", "")
        if body:
            body = re.sub(r"\b(?:10\.\d+|127\.0\.0\.1|37\.27\.48\.12|192\.168)\.\d+\.\d+(?::\d+)?\b", "[server]", body)
            body = re.sub(r"(/home/|/Users/|C:\\)[^\s,;\"']+", "[path removed]", body)
            entry["schema:description"] = body

        # Add subtitle
        subtitle = clean.get("subtitle", card.get("subtitle", ""))
        if subtitle:
            entry["schema:alternateName"] = subtitle

        # Per-asset license
        card_licenses = card.get("licenses", {})
        card_tags = card.get("tags", [])
        node_license = clean.get("license", "")
        if node_license:
            entry["schema:license"] = node_license
        elif card_licenses:
            # Use the most common license
            top_lic = max(card_licenses, key=card_licenses.get)
            entry["schema:license"] = top_lic
        elif any(t in card_tags for t in ["cc0", "CC0", "cc by", "CC BY", "cc by-sa", "CC BY-SA"]):
            entry["schema:license"] = [t for t in card_tags if "cc" in t.lower()][0]

        # Person-specific fields
        if clean.get("type") == "person":
            bio = clean.get("bio", "")
            if bio:
                bio = re.sub(r"\b(?:10\.\d+|127\.0\.0\.1|37\.27\.48\.12|192\.168)\.\d+\.\d+(?::\d+)?\b", "[server]", bio)
                bio = re.sub(r"(/home/|/Users/|C:\\)[^\s,;\"']+", "[path removed]", bio)
                entry["schema:description"] = bio

        # Photo-specific fields
        if clean.get("type") == "photo":
            thumb = clean.get("thumbUrl", "")
            if thumb and not re.search(r"\d+\.\d+\.\d+\.\d+", thumb):
                entry["schema:thumbnailUrl"] = thumb
            photographer = card.get("artist", "")
            if photographer:
                entry["schema:creator"] = photographer

        # Hub membership
        cluster_hub = clean.get("clusterHub", "")
        if cluster_hub and cluster_hub != nid:
            entry["schema:isPartOf"] = node_iri(cluster_hub)

        graph_nodes.append(entry)

    # Build edges
    graph_edges = []
    for link in links:
        src = link["source"]
        tgt = link["target"]
        lt = link.get("linkType", "")

        edge = {
            "@type": "ssd:Edge",
            "ssd:source": node_iri(src),
            "ssd:target": node_iri(tgt),
            "ssd:edgeType": edge_type_map.get(lt, f"ssd:{lt}"),
        }
        graph_edges.append(edge)

    jsonld = {
        "@context": {
            "schema": "https://schema.org/",
            "ssd": "https://salishseadreaming.art/ontology/",
        },
        "schema:name": "Salish Sea Dreaming -- Data Map",
        "schema:description": "Interactive knowledge graph for the Salish Sea Dreaming AI art installation",
        "schema:creator": "Salish Sea Dreaming Collective",
        "schema:datePublished": "2026-04-10",
        "schema:license": "mixed -- see per-asset licenses",
        "ssd:exhibition": "Digital Ecologies: Bridging Nature and Technology",
        "ssd:venue": "Mahon Hall, Salt Spring Island, BC",
        "ssd:url": "/graph",
        "@graph": graph_nodes + graph_edges,
    }

    out_path = REPO / "static" / "ssd-data-export.jsonld"
    with open(out_path, "w") as f:
        json.dump(jsonld, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path} ({os.path.getsize(out_path):,} bytes)")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    provenance_credits, file_credits = load_provenance()
    nodes, links, total_images = build_graph()

    # Count tier-0 nodes
    tier0 = [n for n in nodes if n.get("tier") == 0]
    print(f"Tier 0 (always visible): {len(tier0)} nodes")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total links: {len(links)}")
    print(f"Corpus images: {total_images}")

    # Validate
    hub_count = sum(1 for n in nodes if n["type"] == "hub")
    assert hub_count == 7, f"Expected 7 hubs, got {hub_count}"

    cat_count = sum(1 for n in nodes if n["id"].startswith("cluster:") and n["id"] in CATEGORY_MAP)
    assert cat_count == 8, f"Expected 8 categories, got {cat_count}"

    species_count = sum(1 for n in nodes if n["type"] == "species")
    print(f"Species nodes: {species_count}")

    # Check all nodes have tier
    for n in nodes:
        assert "tier" in n, f"Node {n['id']} missing tier"

    # Check all links have linkType
    for l in links:
        assert "linkType" in l, f"Link {l['source']}→{l['target']} missing linkType"

    # Check signal chain exists
    signal_links = [l for l in links if l["linkType"] == "signal"]
    print(f"Signal links: {len(signal_links)}")

    # Check LoRA path
    lora_links = [l for l in links if l["linkType"] == "training-lora"]
    print(f"LoRA links: {len(lora_links)}")

    # Check Briony triple presence
    briony_nodes = [n for n in nodes if "briony" in n["id"].lower()]
    briony_hubs = set(n.get("clusterHub") for n in briony_nodes)
    print(f"Briony nodes: {len(briony_nodes)} across hubs: {briony_hubs}")

    # ── Write graph JSON ─────────────────────────────────────────────────────
    graph = {
        "nodes": nodes,
        "links": links,
        "theme_colors": {
            "ecosystem":      "#3a9a6a",
            "artists":        "#d4956a",
            "training":       "#7a6aaa",
            "machine":        "#7ab0aa",
            "visitor-dreams":  "#7fffb2",
            "knowledge":      "#6a8aaa",
            "exhibition":     "#ba8a4a",
            "signal":         "#7fffb2",
            "training-flow":  "#c8a04a",
            "lora-flow":      "#d4856a",
            "concept":        "#a0c8e0",
            "person":         "#d4956a",
        },
        "meta": {
            "generated": "2026-04-09",
            "version": "2.0",
            "total_nodes": len(nodes),
            "tier0_nodes": len(tier0),
            "total_links": len(links),
            "hub_count": hub_count,
            "species_count": species_count,
            "corpus_images": total_images,
        },
    }

    with open(OUT_GRAPH, "w") as f:
        json.dump(graph, f, indent=2)
    print(f"\nWrote {OUT_GRAPH} ({os.path.getsize(OUT_GRAPH):,} bytes)")

    # ── Write cards JSON ─────────────────────────────────────────────────────
    cards_dict, species_dict = build_cards(nodes, provenance_credits, file_credits)
    cards_out = {
        "meta": {
            "generated": "2026-04-09",
            "total_cards": len(cards_dict),
            "species_entries": len(species_dict),
        },
        "cards": cards_dict,
        "species": species_dict,
    }

    with open(OUT_CARDS, "w") as f:
        json.dump(cards_out, f, indent=2)
    print(f"Wrote {OUT_CARDS} ({os.path.getsize(OUT_CARDS):,} bytes)")

    # ── Phase 6: Process Digital Ecologies PDFs ─────────────────────────────
    print("\n── Processing Digital Ecologies PDFs ──")
    process_digital_ecologies()

    # ── Phase 7: Data Exports ───────────────────────────────────────────────
    print("\n── Generating data exports ──")
    export_markdown(nodes, links, cards_dict)
    export_jsonld(nodes, links, cards_dict)


if __name__ == "__main__":
    main()
