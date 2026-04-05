"""Tests for SSD card generation — parser logic, cross-refs, and data integrity."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from generate_ssd_cards import (
    parse_metadata_md,
    parse_species_tsvs,
    cross_reference_species,
    format_size,
    generate_auto_card,
)


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def artwork_with_url(tmp_path):
    """Metadata.md with Squarespace source URL."""
    md = tmp_path / "metadata.md"
    md.write_text("""# Kelp Forest Ecosystem

- **Category:** Paintings
- **Artist:** Briony Penn
- **Filename:** IMG_1477.jpg
- **Source URL:** https://images.squarespace-cdn.com/content/v1/abc/image.jpg
- **Description:** A split-view watercolor showing the relationship between seabirds and the underwater kelp forest.
  - **Above Water:** Marbled Murrelets swimming on the surface.
  - **Below Water:** A rich kelp forest scene with rockfish.
- **Notes:** Highlights the connection between the marine canopy and avian predators.
""")
    return md


@pytest.fixture
def artwork_without_url(tmp_path):
    """Metadata.md from phone photo (no Source URL)."""
    md = tmp_path / "metadata.md"
    md.write_text("""# Giant Pacific Octopus

- **Category:** Paintings
- **Artist:** Briony Penn
- **Filename:** IMG_1480.jpg
- **Description:** A watercolor of a Giant Pacific Octopus in a rocky den.

## Notes

Image taken from phone photo of original painting.
""")
    return md


@pytest.fixture
def minimal_metadata(tmp_path):
    """Bare-minimum metadata.md."""
    md = tmp_path / "metadata.md"
    md.write_text("# Untitled Sketch\n")
    return md


# ── parse_metadata_md ───────────────────────────────────────────


class TestParseMetadata:
    def test_extracts_title(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert card["title"] == "Kelp Forest Ecosystem"

    def test_extracts_artist(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert card["artist"] == "Briony Penn"

    def test_extracts_category(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert card["category"] == "Paintings"

    def test_appends_format_to_squarespace_url(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert card["thumbnail_url"].endswith("?format=200w")
        assert "squarespace-cdn" in card["thumbnail_url"]

    def test_no_thumbnail_without_source_url(self, artwork_without_url):
        card = parse_metadata_md(artwork_without_url)
        assert card["thumbnail_url"] == ""

    def test_extracts_description_body(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert "split-view watercolor" in card["body"]
        assert "kelp forest" in card["body"]

    def test_body_has_no_markdown_bold_markers(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert "**" not in card["body"]

    def test_extracts_notes(self, artwork_with_url):
        card = parse_metadata_md(artwork_with_url)
        assert "marine canopy" in card["notes"]

    def test_handles_notes_under_heading(self, artwork_without_url):
        card = parse_metadata_md(artwork_without_url)
        assert "phone photo" in card["notes"]

    def test_minimal_metadata_has_title(self, minimal_metadata):
        card = parse_metadata_md(minimal_metadata)
        assert card["title"] == "Untitled Sketch"
        assert card["body"] == ""


# ── cross_reference_species ─────────────────────────────────────


class TestSpeciesCrossRef:
    def test_finds_species_in_body(self):
        cards = {
            "card1": {"body": "A painting of Pacific Herring in kelp.", "title": "Test"},
        }
        species = {
            "species:pacific-herring": {
                "title": "Pacific Herring",
                "scientific_name": "Clupea pallasii",
                "taxon_id": "117571",
                "groups": [],
                "appears_in": [],
            },
        }
        cross_reference_species(cards, species)
        assert "species:pacific-herring" in cards["card1"]["species"]
        assert "card1" in species["species:pacific-herring"]["appears_in"]

    def test_case_insensitive(self):
        cards = {"c1": {"body": "pacific herring swimming", "title": ""}}
        species = {
            "species:pacific-herring": {
                "title": "Pacific Herring",
                "scientific_name": "",
                "taxon_id": "",
                "groups": [],
                "appears_in": [],
            },
        }
        cross_reference_species(cards, species)
        assert "species:pacific-herring" in cards["c1"]["species"]

    def test_skips_short_matches(self):
        """Names 3 chars or shorter should not match (too ambiguous)."""
        cards = {"c1": {"body": "The sea was calm.", "title": ""}}
        species = {
            "species:sea": {
                "title": "Sea",
                "scientific_name": "",
                "taxon_id": "",
                "groups": [],
                "appears_in": [],
            },
        }
        cross_reference_species(cards, species)
        assert "species" not in cards["c1"]

    def test_no_duplicate_refs(self):
        cards = {"c1": {"body": "herring herring herring", "title": "herring"}}
        species = {
            "species:pacific-herring": {
                "title": "Pacific Herring",
                "scientific_name": "",
                "taxon_id": "",
                "groups": [],
                "appears_in": [],
            },
        }
        cross_reference_species(cards, species)
        assert species["species:pacific-herring"]["appears_in"].count("c1") == 1


# ── format_size ─────────────────────────────────────────────────


class TestFormatSize:
    def test_bytes(self):
        assert format_size(500) == "500 bytes"

    def test_kilobytes(self):
        assert format_size(10240) == "10 KB"

    def test_megabytes(self):
        assert format_size(3 * 1024 * 1024) == "3.0 MB"

    def test_zero(self):
        assert format_size(0) == "0 bytes"


# ── generate_auto_card ──────────────────────────────────────────


class TestAutoCard:
    def test_file_card(self):
        node = {"name": "test.py", "theme": "code", "size": 1024, "isDir": False}
        card = generate_auto_card(node)
        assert card["title"] == "test.py"
        assert "Code" in card["body"]
        assert "code" in card["tags"]

    def test_dir_card(self):
        node = {"name": "scripts", "theme": "code", "size": 0, "isDir": True}
        card = generate_auto_card(node)
        assert "Directory" in card["body"]


# ── Data integrity (runs against real output) ───────────────────


CARDS_JSON = Path(__file__).parent.parent / "static" / "ssd-cards.json"
GRAPH_JSON = Path(__file__).parent.parent / "static" / "ssd-data-map.json"


@pytest.mark.skipif(not CARDS_JSON.exists(), reason="ssd-cards.json not generated")
class TestDataIntegrity:
    @pytest.fixture(autouse=True)
    def load_data(self):
        with open(CARDS_JSON) as f:
            self.cards_data = json.load(f)
        with open(GRAPH_JSON) as f:
            self.graph_data = json.load(f)
        self.cards = self.cards_data["cards"]
        self.species = self.cards_data["species"]
        self.graph_ids = {n["id"] for n in self.graph_data["nodes"]}

    def test_every_graph_node_has_card(self):
        card_ids = set(self.cards.keys())
        missing = self.graph_ids - card_ids
        assert missing == set(), f"Graph nodes without cards: {missing}"

    def test_no_orphan_cards(self):
        card_ids = set(self.cards.keys())
        extra = card_ids - self.graph_ids
        assert extra == set(), f"Cards without graph nodes: {extra}"

    def test_artwork_count(self):
        assert self.cards_data["meta"]["artwork_cards"] == 59

    def test_all_species_have_titles(self):
        for sid, sp in self.species.items():
            assert sp["title"], f"Species {sid} has no title"

    def test_thumbnails_are_valid_urls(self):
        for cid, card in self.cards.items():
            url = card.get("thumbnail_url", "")
            if url:
                assert url.startswith("https://") or url.startswith("data:image/"), \
                    f"Invalid thumbnail URL for {cid}: {url[:60]}"

    def test_no_empty_titles(self):
        empty = [cid for cid, c in self.cards.items() if not c.get("title")]
        assert empty == [], f"Cards with empty titles: {empty[:5]}"
