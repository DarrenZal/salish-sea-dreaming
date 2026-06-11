#!/usr/bin/env python3
"""Generate IMPACT Dome cosmic-journey concept stills and GIFs.

These are presentation concept assets, not a live Dome renderer. They use the
existing SSD knowledge graph as visual substrate and render abstract
constellation scenes for Carol Anne's Friday AI presentation.

Boundary:
  - no Austin source imagery
  - no Coast Salish design motifs
  - no claim of live survey functionality
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "static" / "ssd-data-map.json"
OUT_ROOT = ROOT / "output" / "dome-cosmic-journey-2026-05-15"
STILLS_DIR = OUT_ROOT / "stills"
GIFS_DIR = OUT_ROOT / "gifs"

STILL_SIZE = (1920, 1080)
GIF_SIZE = (960, 540)
GIF_FRAMES = 36
GIF_DURATION_MS = 80


@dataclass(frozen=True)
class Scene:
    number: int
    title: str
    subtitle: str
    keywords: tuple[str, ...]
    palette: tuple[tuple[int, int, int], ...]
    layout: str


SCENES = [
    Scene(
        1,
        "Enter the Living Graph",
        "A constellation of relationships opens around the audience",
        ("exhibition", "knowledge", "graph", "salish", "sea", "dreaming"),
        ((98, 210, 255), (77, 255, 210), (255, 219, 111)),
        "spiral",
    ),
    Scene(
        2,
        "From Pearl to Constellation",
        "The Hubble experience expands into the Dome-scale graph",
        ("pearl", "dome", "projection", "visitor", "dream", "hubble"),
        ((211, 236, 255), (122, 180, 255), (255, 214, 150)),
        "bridge",
    ),
    Scene(
        3,
        "People, Places, Agreements",
        "Participants, venues, and commitments appear as linked stars",
        ("person", "venue", "agreement", "artist", "carol", "prav", "darren"),
        ((255, 154, 128), (255, 222, 126), (127, 229, 255)),
        "clusters",
    ),
    Scene(
        4,
        "Survey Becomes Signal",
        "Intake points become analyzable light in the graph",
        ("survey", "question", "response", "intake", "economic", "indigenomics"),
        ((110, 255, 184), (255, 230, 102), (255, 130, 170)),
        "fountain",
    ),
    Scene(
        5,
        "Questions Find Relations",
        "Questions connect to evidence, themes, and nearby commitments",
        ("question", "knowledge", "research", "evidence", "concept", "document"),
        ((124, 188, 255), (185, 154, 255), (92, 255, 218)),
        "web",
    ),
    Scene(
        6,
        "Voices in Orbit",
        "Interview and testimony material moves as orbital paths",
        ("voice", "interview", "story", "witness", "dream", "visitor"),
        ((255, 170, 96), (124, 214, 255), (255, 238, 180)),
        "orbit",
    ),
    Scene(
        7,
        "Sovereign AI Layer",
        "Model, compute, and graph infrastructure become a visible field",
        ("ai", "model", "telus", "gpu", "server", "machine", "compute"),
        ((124, 255, 244), (122, 145, 255), (255, 255, 255)),
        "grid",
    ),
    Scene(
        8,
        "Economic Patterns Emerge",
        "Clusters form without flattening the relations that produced them",
        ("economic", "indigenomics", "value", "pattern", "cluster", "relation"),
        ((255, 206, 89), (73, 220, 180), (255, 110, 129)),
        "clusters",
    ),
    Scene(
        9,
        "Visitors Join the Field",
        "Hubble app offerings can become graph events when consented",
        ("visitor", "dream", "offering", "qr", "portal", "app"),
        ((97, 221, 255), (126, 255, 180), (255, 150, 220)),
        "fountain",
    ),
    Scene(
        10,
        "IMPACT Constellation",
        "One event arc, two rooms, one living substrate",
        ("impact", "space", "centre", "dome", "hubble", "indigenomics"),
        ((255, 245, 190), (91, 210, 255), (255, 116, 116)),
        "bridge",
    ),
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def load_graph() -> tuple[list[dict], list[dict], Counter]:
    data = json.loads(GRAPH_PATH.read_text())
    nodes = data.get("nodes", [])
    links = data.get("links", [])
    degree: Counter = Counter()
    for link in links:
        src = link.get("source")
        dst = link.get("target")
        if isinstance(src, dict):
            src = src.get("id")
        if isinstance(dst, dict):
            dst = dst.get("id")
        if src:
            degree[str(src)] += 1
        if dst:
            degree[str(dst)] += 1
    return nodes, links, degree


def node_text(node: dict) -> str:
    parts = [
        str(node.get("id", "")),
        str(node.get("name", "")),
        str(node.get("type", "")),
        str(node.get("theme", "")),
        str(node.get("ext", "")),
    ]
    return " ".join(parts).lower()


def choose_nodes(scene: Scene, nodes: list[dict], degree: Counter, count: int = 42) -> list[dict]:
    keyword_hits = []
    for node in nodes:
        text = node_text(node)
        score = sum(1 for kw in scene.keywords if kw.lower() in text)
        if score:
            node_id = str(node.get("id", ""))
            keyword_hits.append((score * 100 + degree[node_id], node))

    keyword_hits.sort(key=lambda item: item[0], reverse=True)
    chosen = [node for _, node in keyword_hits[:count]]

    if len(chosen) < count:
        chosen_ids = {node.get("id") for node in chosen}
        fallback = sorted(
            (node for node in nodes if node.get("id") not in chosen_ids),
            key=lambda node: degree[str(node.get("id", ""))],
            reverse=True,
        )
        chosen.extend(fallback[: count - len(chosen)])

    return chosen[:count]


def node_label(node: dict) -> str:
    name = str(node.get("name") or node.get("id") or "node")
    if len(name) > 30:
        return name[:27] + "..."
    return name


def build_positions(scene: Scene, n: int, size: tuple[int, int], phase: float) -> list[tuple[float, float, float]]:
    w, h = size
    cx, cy = w * 0.52, h * 0.53
    rng = random.Random(scene.number * 991)
    points = []

    for i in range(n):
        t = i / max(1, n - 1)
        jitter = rng.uniform(-0.08, 0.08)
        pulse = 1.0 + 0.05 * math.sin(phase + i * 0.37)

        if scene.layout == "spiral":
            angle = t * math.tau * 2.6 + phase * 0.35
            radius = (70 + t * min(w, h) * 0.40) * pulse
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius * 0.70
        elif scene.layout == "bridge":
            side = -1 if i % 2 == 0 else 1
            band = (i // 2) / max(1, n // 2)
            x = w * (0.22 + 0.56 * band)
            y = cy + side * (h * 0.20 * math.sin(band * math.pi + phase * 0.3))
            x += math.sin(phase + i) * 18
            y += math.cos(phase * 0.7 + i) * 14
        elif scene.layout == "clusters":
            cluster = i % 3
            centers = [(w * 0.33, h * 0.42), (w * 0.61, h * 0.35), (w * 0.52, h * 0.68)]
            base_x, base_y = centers[cluster]
            angle = (i / 3) * 0.91 + phase * (0.08 + cluster * 0.04)
            radius = (55 + ((i // 3) % 8) * 18) * pulse
            x = base_x + math.cos(angle) * radius
            y = base_y + math.sin(angle) * radius
        elif scene.layout == "fountain":
            angle = -math.pi * 0.85 + t * math.pi * 1.7 + jitter
            radius = min(w, h) * (0.16 + 0.33 * math.sin(t * math.pi))
            x = cx + math.cos(angle) * radius + math.sin(phase + i) * 20
            y = h * 0.72 - math.sin(t * math.pi) * h * 0.42 + math.cos(phase + i) * 12
        elif scene.layout == "orbit":
            ring = 0.18 + (i % 4) * 0.075
            angle = i * 0.63 + phase * (0.25 + (i % 4) * 0.03)
            x = cx + math.cos(angle) * w * ring
            y = cy + math.sin(angle) * h * ring * 0.92
        elif scene.layout == "grid":
            cols = 7
            row = i // cols
            col = i % cols
            x = w * 0.22 + col * w * 0.09 + math.sin(phase + i) * 12
            y = h * 0.30 + row * h * 0.085 + math.cos(phase * 0.8 + i) * 10
        else:
            angle = i * math.tau / max(1, n) + phase * 0.2
            radius = min(w, h) * 0.32
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

        points.append((x, y, 1.0 + (i % 5) * 0.18))

    return points


def make_background(size: tuple[int, int], scene: Scene, phase: float) -> Image.Image:
    w, h = size
    low_w = max(80, w // 8)
    low_h = max(45, h // 8)
    img = Image.new("RGB", (low_w, low_h), (4, 8, 18))
    pix = img.load()
    base = scene.palette[0]
    for y in range(low_h):
        yy = y / max(1, low_h - 1)
        for x in range(low_w):
            xx = x / max(1, low_w - 1)
            glow = max(0.0, 1.0 - math.hypot(xx - 0.55, yy - 0.50) * 1.55)
            r = int(4 + base[0] * glow * 0.10 + 12 * yy)
            g = int(8 + base[1] * glow * 0.08 + 8 * (1 - yy))
            b = int(18 + base[2] * glow * 0.11 + 12 * xx)
            pix[x, y] = (min(255, r), min(255, g), min(255, b))
    img = img.resize(size, Image.Resampling.BICUBIC)

    draw = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(scene.number * 1337)
    for _ in range(260 if w > 1000 else 120):
        x = rng.randrange(w)
        y = rng.randrange(h)
        twinkle = 0.45 + 0.55 * math.sin(phase + x * 0.017 + y * 0.011)
        alpha = int(rng.randrange(40, 145) * twinkle)
        radius = rng.choice([1, 1, 1, 2])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(210, 235, 255, alpha))
    return img


def draw_scene(scene: Scene, nodes: list[dict], size: tuple[int, int], phase: float = 0.0) -> Image.Image:
    w, h = size
    img = make_background(size, scene, phase)
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow, "RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    positions = build_positions(scene, len(nodes), size, phase)
    palette = scene.palette

    # Draw relationship lines first.
    for i in range(len(nodes)):
        x1, y1, _ = positions[i]
        for step in (3, 7):
            j = (i + step) % len(nodes)
            if j <= i:
                continue
            x2, y2, _ = positions[j]
            color = palette[(i + step) % len(palette)]
            alpha = 24 + int(24 * (0.5 + 0.5 * math.sin(phase + i * 0.13)))
            draw.line((x1, y1, x2, y2), fill=(*color, alpha), width=1)
            draw_glow.line((x1, y1, x2, y2), fill=(*color, 22), width=4)

    # Scene-specific gesture lines.
    if scene.layout == "bridge":
        left = (w * 0.18, h * 0.55)
        right = (w * 0.82, h * 0.45)
        for k in range(5):
            off = (k - 2) * h * 0.035
            draw.arc((left[0], h * 0.22 + off, right[0], h * 0.83 + off), 188, 348, fill=(*palette[k % 3], 72), width=2)
    elif scene.layout == "orbit":
        for k in range(4):
            pad_x = w * (0.16 + k * 0.055)
            pad_y = h * (0.20 + k * 0.045)
            draw.ellipse((pad_x, pad_y, w - pad_x, h - pad_y), outline=(*palette[k % 3], 34), width=2)
    elif scene.layout == "grid":
        for k in range(8):
            x = w * (0.18 + k * 0.09)
            draw.line((x, h * 0.24, x, h * 0.80), fill=(*palette[k % 3], 24), width=1)

    # Draw nodes.
    for i, node in enumerate(nodes):
        x, y, scale = positions[i]
        color = palette[i % len(palette)]
        radius = (4.0 + scale * 3.2) * (1.0 + 0.2 * math.sin(phase * 2 + i))
        draw_glow.ellipse((x - radius * 4, y - radius * 4, x + radius * 4, y + radius * 4), fill=(*color, 24))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, 205))
        draw.ellipse((x - radius * 0.35, y - radius * 0.35, x + radius * 0.35, y + radius * 0.35), fill=(255, 255, 255, 210))

    glow = glow.filter(ImageFilter.GaussianBlur(7 if w > 1000 else 4))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    draw = ImageDraw.Draw(img, "RGBA")

    title_font = load_font(72 if w > 1000 else 36, bold=True)
    subtitle_font = load_font(30 if w > 1000 else 16)
    small_font = load_font(22 if w > 1000 else 11)

    margin_x = int(w * 0.07)
    title_y = int(h * 0.075)
    draw.text((margin_x + 2, title_y + 2), scene.title, fill=(0, 0, 0, 150), font=title_font)
    draw.text((margin_x, title_y), scene.title, fill=(244, 249, 255, 245), font=title_font)
    draw.text((margin_x, title_y + int(h * 0.085)), scene.subtitle, fill=(190, 225, 238, 210), font=subtitle_font)

    footer = "IMPACT Dome concept - pre-recorded primary - live functionality not implied"
    draw.text((margin_x, int(h * 0.91)), footer, fill=(160, 190, 205, 150), font=small_font)
    draw.text((int(w * 0.86), int(h * 0.91)), f"{scene.number:02d}/10", fill=(220, 235, 245, 180), font=small_font)

    return img.convert("RGB")


def write_manifest(scenes: list[Scene]) -> None:
    lines = [
        "# Dome Cosmic Journey Concept Assets - 2026-05-15",
        "",
        "Generated by `scripts/generate_dome_cosmic_journey_assets.py` from `static/ssd-data-map.json`.",
        "",
        "Boundary: abstract constellation visuals only. No Austin source imagery, no Coast Salish design motifs, and no claim of live survey functionality.",
        "",
        "| # | Title | Still | GIF | Notes |",
        "|---:|---|---|---|---|",
    ]
    for scene in scenes:
        stem = f"{scene.number:02d}_{slug(scene.title)}"
        lines.append(
            f"| {scene.number:02d} | {scene.title} | `stills/{stem}.png` | `gifs/{stem}.gif` | {scene.subtitle} |"
        )
    lines.extend(
        [
            "",
            "Recommended use: concept slides or short pre-recorded presentation insert.",
            "Do not present these as the final Dome renderer or live survey analytic visualization.",
        ]
    )
    (OUT_ROOT / "00_manifest.md").write_text("\n".join(lines) + "\n")


def slug(value: str) -> str:
    out = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_")


def main() -> int:
    nodes, _links, degree = load_graph()
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    GIFS_DIR.mkdir(parents=True, exist_ok=True)

    for scene in SCENES:
        selected = choose_nodes(scene, nodes, degree)
        stem = f"{scene.number:02d}_{slug(scene.title)}"

        still = draw_scene(scene, selected, STILL_SIZE, phase=0.8)
        still_path = STILLS_DIR / f"{stem}.png"
        still.save(still_path)

        frames = []
        for frame_idx in range(GIF_FRAMES):
            phase = frame_idx / GIF_FRAMES * math.tau
            frame = draw_scene(scene, selected, GIF_SIZE, phase=phase)
            frames.append(frame)
        gif_path = GIFS_DIR / f"{stem}.gif"
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=GIF_DURATION_MS,
            loop=0,
            optimize=True,
        )

        print(f"wrote {still_path.relative_to(ROOT)}")
        print(f"wrote {gif_path.relative_to(ROOT)}")

    write_manifest(SCENES)
    print(f"wrote {(OUT_ROOT / '00_manifest.md').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
