#!/usr/bin/env python3
"""Generate ssd-cards.json from the Salish Sea Dreaming repo.

Reads:
  - 59 Briony artwork metadata.md files → rich artwork cards
  - 7 species TSV files → species enrichment entries
  - 8 key project docs → document cards with summaries
  - ssd-data-map.json → auto-generates minimal cards for remaining nodes

Writes:
  - static/ssd-cards.json
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────

SSD_REPO = Path(os.path.expanduser(
    "~/.claude/local/dock/repos/salish-sea-dreaming"
))
IAI_STATIC = Path(os.path.expanduser(
    "~/Workspace/IndigenomicsAI/static"
))
GRAPH_JSON = IAI_STATIC / "ssd-data-map.json"
OUTPUT = IAI_STATIC / "ssd-cards.json"

# ── Metadata.md parser ──────────────────────────────────────────


def parse_metadata_md(path: Path) -> dict:
    """Parse a Briony artwork metadata.md into a card dict."""
    text = path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")

    card = {
        "title": "",
        "body": "",
        "artist": "Briony Penn",
        "category": "",
        "thumbnail_url": "",
        "filename": "",
        "tags": [],
        "notes": "",
    }

    # Title from first heading, fall back to parent directory name
    for line in lines:
        if line.startswith("# "):
            card["title"] = line[2:].strip()
            break
    if not card["title"]:
        card["title"] = path.parent.name.replace("-", " ").replace("_", " ").title()

    # Field extraction
    field_map = {
        "Category": "category",
        "Artist": "artist",
        "Filename": "filename",
        "Source URL": "thumbnail_url",
    }

    description_lines = []
    notes_lines = []
    in_description = False
    in_notes = False

    for line in lines:
        stripped = line.strip()

        # Check for field markers
        matched_field = False
        for marker, key in field_map.items():
            if stripped.startswith(f"- **{marker}:**") or stripped.startswith(f"**{marker}:**"):
                value = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
                # Clean markdown formatting
                value = value.strip("* ")
                card[key] = value
                matched_field = True
                in_description = False
                in_notes = False
                break

        if matched_field:
            continue

        # Description block
        if stripped.startswith("- **Description:**") or stripped.startswith("**Description:**"):
            desc_start = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if desc_start:
                description_lines.append(desc_start.strip("* "))
            in_description = True
            in_notes = False
            continue

        # Notes block
        if stripped.startswith("- **Notes:**") or stripped.startswith("**Notes:**") or stripped.startswith("## Notes"):
            note_start = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if note_start:
                notes_lines.append(note_start.strip("* "))
            in_notes = True
            in_description = False
            continue

        # Continuation lines
        if in_description and stripped and not stripped.startswith("#"):
            description_lines.append(stripped.lstrip("- ").strip("* "))
        elif in_notes and stripped and not stripped.startswith("#"):
            notes_lines.append(stripped.lstrip("- ").strip("* "))

    body = " ".join(description_lines).strip()
    # Clean markdown bold markers from parsed text
    body = body.replace("**", "")
    card["body"] = body
    card["notes"] = " ".join(notes_lines).strip().replace("**", "")

    # Append Squarespace thumbnail format if URL exists
    if card["thumbnail_url"] and "squarespace-cdn" in card["thumbnail_url"]:
        url = card["thumbnail_url"]
        if "?" not in url:
            card["thumbnail_url"] = url + "?format=200w"

    # Derive category from path if not in metadata
    if not card["category"]:
        parent = path.parent.parent.name
        if parent != "Brionny":
            card["category"] = parent

    return card


# ── Species TSV parser ──────────────────────────────────────────


def parse_species_tsvs() -> dict:
    """Parse all species TSV files into a species dict."""
    species = {}
    tsv_dir = SSD_REPO / "tools"

    for tsv_file in sorted(tsv_dir.glob("species*.tsv")):
        group = tsv_file.stem.replace("species-", "").replace("species", "salish-sea")
        with open(tsv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                common = row.get("common_name", "").strip()
                scientific = row.get("scientific_name", "").strip()
                taxon_id = row.get("taxon_id", "").strip()
                if not common:
                    continue
                slug = common.lower().replace(" ", "-").replace("'", "")
                sid = f"species:{slug}"
                if sid not in species:
                    species[sid] = {
                        "title": common,
                        "scientific_name": scientific,
                        "taxon_id": taxon_id,
                        "groups": [],
                        "appears_in": [],
                    }
                if group not in species[sid]["groups"]:
                    species[sid]["groups"].append(group)

    # Also parse the main salish-sea-species.tsv
    main_tsv = tsv_dir / "salish-sea-species.tsv"
    if main_tsv.exists():
        with open(main_tsv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                common = row.get("common_name", "").strip()
                scientific = row.get("scientific_name", "").strip()
                taxon_id = row.get("taxon_id", "").strip()
                if not common:
                    continue
                slug = common.lower().replace(" ", "-").replace("'", "")
                sid = f"species:{slug}"
                if sid not in species:
                    species[sid] = {
                        "title": common,
                        "scientific_name": scientific,
                        "taxon_id": taxon_id,
                        "groups": ["salish-sea"],
                        "appears_in": [],
                    }

    return species


# ── Species cross-referencing ───────────────────────────────────


def cross_reference_species(cards: dict, species: dict) -> None:
    """Find species mentions in card bodies, link both ways."""
    # Build a lookup: lowercase common name → species id
    name_to_id = {}
    for sid, sp in species.items():
        name_to_id[sp["title"].lower()] = sid
        # Also add partial names for compound names
        parts = sp["title"].lower().split()
        if len(parts) > 1:
            # e.g., "Pacific Herring" also matches "herring" but only
            # as a weaker signal — we prefer full name matches
            name_to_id[parts[-1]] = sid

    # Sort by length descending for longest-match-first
    sorted_names = sorted(name_to_id.keys(), key=len, reverse=True)

    for card_id, card in cards.items():
        body = (card.get("body", "") + " " + card.get("notes", "")).lower()
        title = card.get("title", "").lower()
        text = body + " " + title
        found = set()
        for name in sorted_names:
            if name in text and len(name) > 3:  # skip very short matches
                sid = name_to_id[name]
                if sid not in found:
                    found.add(sid)
        if found:
            card["species"] = sorted(found)
            for sid in found:
                if card_id not in species[sid]["appears_in"]:
                    species[sid]["appears_in"].append(card_id)


# ── Document card generator ─────────────────────────────────────


def generate_doc_cards() -> dict:
    """Generate cards for key project documents."""
    docs = {}
    doc_files = [
        "docs/project-vision.md",
        "docs/salish-sea-dreaming-one-pager.md",
        "docs/sonification-map-of-silence.md",
        "docs/team-handoff-march-2026.md",
        "docs/style-transfer-guide.md",
        "docs/lora-integration-guide.md",
        "docs/dreaming-model-corpus.md",
        "docs/moonfish-shotlist.md",
        "docs/autolume-integration.md",
        "docs/autolume-quickstart.md",
        "docs/animation-research.md",
    ]

    for rel_path in doc_files:
        full_path = SSD_REPO / rel_path
        if not full_path.exists():
            continue

        text = full_path.read_text(encoding="utf-8")
        lines = text.strip().split("\n")

        # Extract title from first heading
        title = full_path.stem.replace("-", " ").title()
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract first paragraph as summary (skip frontmatter and headings)
        summary_lines = []
        in_frontmatter = False
        past_title = False
        for line in lines:
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.startswith("# "):
                past_title = True
                continue
            if past_title and line.strip():
                if line.startswith("#"):
                    if summary_lines:
                        break  # stop at next heading if we have content
                    continue  # skip ## subheadings before first content
                # Skip italic-only lines (like "*Concept sketch*")
                stripped_clean = line.strip()
                if stripped_clean.startswith("*") and stripped_clean.endswith("*"):
                    continue
                # Skip short bold preamble lines (like "**For:** Raf...")
                if stripped_clean.startswith("**") and len(stripped_clean) < 40 and len(summary_lines) == 0:
                    continue
                # Skip markdown link-only lines
                if stripped_clean.startswith("[") and "](" in stripped_clean:
                    continue
                summary_lines.append(line.strip())
                if len(summary_lines) >= 5:
                    break

        body = " ".join(summary_lines).strip()

        # Determine theme from content
        tags = ["documentation"]
        lower_path = rel_path.lower()
        if "lora" in lower_path or "style-transfer" in lower_path:
            tags.append("models")
        if "sonification" in lower_path or "moonfish" in lower_path:
            tags.append("ecological-data")
        if "autolume" in lower_path or "dreaming" in lower_path:
            tags.append("generated-art")
        if "handoff" in lower_path or "animation" in lower_path:
            tags.append("video")

        card_id = f"repo:{rel_path}"
        docs[card_id] = {
            "title": title,
            "body": body,
            "tags": tags,
            "doc_length": len(text),
        }

    return docs


# ── Auto card for remaining nodes ───────────────────────────────


THEME_DESCRIPTIONS = {
    "briony-art": "Briony Penn artwork",
    "marine-reference": "Marine reference image",
    "training-data": "AI training data",
    "ecological-data": "Ecological dataset",
    "video": "Video asset",
    "documentation": "Project documentation",
    "code": "Code / script",
    "models": "AI model or weight",
    "generated-art": "AI-generated artwork",
    "raf-curator": "Curator output for Raf",
    "data-package": "Data package",
    "handoff-renders": "Render from team handoff",
    "generated-experiments": "Experimental generation",
    "projection-learning": "Projection learning material",
    "signal-loop": "Signal loop asset",
    "other": "Project file",
}


def format_size(size: int) -> str:
    if size > 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size > 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} bytes"


def generate_auto_card(node: dict) -> dict:
    """Generate a minimal card for a node without curated content."""
    theme = node.get("theme", "other")
    desc = THEME_DESCRIPTIONS.get(theme, "Project file")

    if node.get("isDir"):
        body = f"Directory containing {desc.lower()} files."
    else:
        size_str = format_size(node.get("size", 0))
        body = f"{desc}. {size_str}."

    return {
        "title": node["name"],
        "body": body,
        "tags": [theme],
    }


# ── Drive file enrichment ───────────────────────────────────────


def enrich_drive_cards(cards: dict, graph_nodes: list) -> None:
    """Add richer descriptions for known Drive file patterns."""
    for node in graph_nodes:
        nid = node["id"]
        if not nid.startswith("drive:"):
            continue
        if nid in cards:
            continue

        name = node["name"]
        lower = name.lower()

        # Raf curator outputs
        if "raf-still-dreaming" in lower:
            parts = name.replace(".png", "").split("_")
            version = next((p for p in parts if p.startswith("v")), "")
            aspect = next((p for p in parts if "x" in p and len(p) <= 3), "")
            desc_part = parts[-1].replace("-", " ") if parts else name
            cards[nid] = {
                "title": f"Raf Output — {desc_part}",
                "body": f"Curator output for Raf. {version} {aspect}. Generated for the Digital Ecologies exhibition proposal.",
                "tags": ["raf-curator", "generated-art"],
            }
        # Video files
        elif lower.endswith((".mp4", ".mov")):
            cards[nid] = {
                "title": node["name"],
                "body": f"Video asset. {format_size(node.get('size', 0))}. Part of the Salish Sea Dreaming visual pipeline.",
                "tags": ["video"],
            }


# ── Favorites (Darren experiments) enrichment ───────────────────


FAVORITES_DESCRIPTIONS = {
    "1a_estuary_anim": "Estuary animation — Briony's Central Coast estuary scene animated frame by frame",
    "1a_inshore_anim": "Inshore animation — Central Coast inshore scene animated",
    "1a_estuary_metamorph": "Estuary metamorphosis — shape-shifting between ecological states",
    "1c_flora_fauna_p1": "Flora-fauna mandala animation — Briony's ecological mandala in motion",
    "2b_controlnet_depth_morph": "ControlNet depth morphing — 3D-aware style transfer",
    "2c_prompt_walk": "Prompt walk — smooth interpolation between text prompts through latent space",
    "2e_p2_s123_clip": "CLIP-guided generation experiment",
    "3a_boids_rendered": "Boids flocking — algorithmic schooling behavior rendered as particles",
    "boids_controlnet_smoothed": "Boids + ControlNet — flocking algorithm guiding image generation",
    "exp2d_sd_vae_slerp": "VAE SLERP experiment — spherical interpolation in latent space (SD)",
    "exp2d_wan_vae_slerp": "WAN VAE SLERP — Wan 2.1 model latent space interpolation",
    "exp3i_foodweb_cycle": "Food web cycle — trophic cascade visualized as generative sequence",
    "exp3j_outpaint_spiral": "Outpaint spiral — image expands outward in a spiral pattern",
}


def enrich_favorites_cards(cards: dict, graph_nodes: list) -> None:
    """Add descriptions for Darren's experiment videos."""
    for node in graph_nodes:
        nid = node["id"]
        if not nid.startswith("fav:"):
            continue

        name = node["name"].replace(".mp4", "")
        for prefix, desc in FAVORITES_DESCRIPTIONS.items():
            if name.startswith(prefix):
                cards[nid] = {
                    "title": desc.split(" — ")[0] if " — " in desc else name,
                    "body": desc,
                    "tags": ["generated-experiments", "video"],
                }
                break


# ── Main ────────────────────────────────────────────────────────


def main():
    # Load graph data for node ID mapping
    with open(GRAPH_JSON) as f:
        graph = json.load(f)

    all_nodes = graph["nodes"]
    print(f"Graph nodes: {len(all_nodes)}")

    cards = {}

    # 1. Artwork cards from metadata.md
    artwork_count = 0
    for md_path in sorted(SSD_REPO.glob("VisualArt/Brionny/**/metadata.md")):
        rel = str(md_path.relative_to(SSD_REPO))
        card_id = f"repo:{rel}"

        card = parse_metadata_md(md_path)
        cards[card_id] = card
        artwork_count += 1

        # Also create a card for the parent directory (the artwork folder)
        dir_id = f"repo:{str(md_path.parent.relative_to(SSD_REPO))}"
        if dir_id not in cards:
            cards[dir_id] = {
                "title": card["title"],
                "body": card["body"],
                "artist": card.get("artist", "Briony Penn"),
                "category": card.get("category", ""),
                "thumbnail_url": card.get("thumbnail_url", ""),
                "tags": ["briony-art"],
                "notes": card.get("notes", ""),
            }

        # And for sibling image files in the same dir
        for img in md_path.parent.glob("*"):
            if img.suffix.lower() in (".png", ".jpg", ".jpeg"):
                img_id = f"repo:{str(img.relative_to(SSD_REPO))}"
                if img_id not in cards:
                    cards[img_id] = {
                        "title": f"{card['title']} — {img.name}",
                        "body": card["body"],
                        "thumbnail_url": card.get("thumbnail_url", ""),
                        "tags": ["briony-art"],
                    }

    print(f"Artwork cards: {artwork_count} (× dirs + images = {len(cards)})")

    # 2. Species
    species = parse_species_tsvs()
    print(f"Species entries: {len(species)}")

    # 3. Document cards
    doc_cards = generate_doc_cards()
    cards.update(doc_cards)
    print(f"Document cards: {len(doc_cards)}")

    # 4. Cross-reference species in artwork and doc bodies
    cross_reference_species(cards, species)
    species_with_refs = sum(1 for s in species.values() if s["appears_in"])
    print(f"Species with cross-refs: {species_with_refs}")

    # 5. Enrich Drive and Favorites cards
    enrich_drive_cards(cards, all_nodes)
    enrich_favorites_cards(cards, all_nodes)
    drive_enriched = sum(1 for k in cards if k.startswith("drive:"))
    fav_enriched = sum(1 for k in cards if k.startswith("fav:"))
    print(f"Drive cards enriched: {drive_enriched}")
    print(f"Favorites cards enriched: {fav_enriched}")

    # 6. Auto-generate cards for remaining nodes
    auto_count = 0
    for node in all_nodes:
        nid = node["id"]
        if nid not in cards:
            cards[nid] = generate_auto_card(node)
            auto_count += 1
    print(f"Auto-generated cards: {auto_count}")

    # 7. Merge local base64 thumbnails (from LFS-pulled images)
    thumbs_path = Path("/tmp/ssd-thumbnails.json")
    local_thumb_count = 0
    if thumbs_path.exists():
        with open(thumbs_path) as f:
            local_thumbs = json.load(f)
        for node_id, data_uri in local_thumbs.items():
            if node_id in cards:
                # Only set if no Squarespace URL already exists
                if not cards[node_id].get("thumbnail_url"):
                    cards[node_id]["thumbnail_url"] = data_uri
                    local_thumb_count += 1
    print(f"Local thumbnails added: {local_thumb_count}")

    # Build output
    output = {
        "meta": {
            "generated": "2026-04-04",
            "total_cards": len(cards),
            "artwork_cards": artwork_count,
            "species_entries": len(species),
            "doc_cards": len(doc_cards),
            "auto_cards": auto_count,
            "local_thumbnails": local_thumb_count,
        },
        "cards": cards,
        "species": species,
    }

    OUTPUT.write_text(json.dumps(output, indent=1, ensure_ascii=False) + "\n")
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\nWritten: {OUTPUT}")
    print(f"Size: {size_kb} KB")
    print(f"Total cards: {len(cards)}")


if __name__ == "__main__":
    main()
