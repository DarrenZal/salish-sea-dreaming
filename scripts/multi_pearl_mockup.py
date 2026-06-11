#!/usr/bin/env python3
"""
Multi-pearl A-lite mockup (3-node, 2-pearl simultaneous traversal).

Demonstrates the polyphonic "graph alive with multiple pearls in flight"
visual logic — extends the single-pearl prototype with multiple traversals
happening simultaneously on different edges.

Uses 3 Austin pieces as nodes:
  - Animal_Bird_Raven_Sun (top)
  - Nature_Cosmic_Sun (right)
  - Animal_Salmon_Spawn_Eggs (left)
arranged in a triangle. 2 pearls in flight at the same time on different
edges, each carrying its own morph clip's textures.

INTERNAL ONLY per Austin consent floor. Output to:
  track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import math
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17"

# Reuse the improved pearl rendering from single-pearl mockup
sys.path.insert(0, str(ROOT / "scripts"))
from pearl_bead_mockup import make_pearl, make_node_card, BG_COLOR, EDGE_COLOR, PEARL_HIGHLIGHT, NODE_FRAME

# Source morph frame dirs (3 different edges)
EDGE_MORPHS = {
    # edge_id: (frames_dir, n_frames)
    "raven_sun→cosmic_sun":       ROOT / "track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun",
    "cosmic_sun→salmon_spawn":    ROOT / "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn",
    "raven_sun→salmon_spawn":     ROOT / "track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_salmon_spawn",
}

# Source node thumbnails (rendered from SVGs via ImageMagick — re-use existing or render)
NODE_PNGS = {
    "raven_sun":     ROOT / "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/_node_raven_sun.png",
    "cosmic_sun":    ROOT / "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/_node_cosmic_sun.png",
    # salmon: render now
    "salmon_spawn":  OUT / "_node_salmon_spawn.png",
}

def render_salmon_node():
    """Render salmon_spawn_eggs SVG as PNG thumbnail if not exists."""
    if NODE_PNGS["salmon_spawn"].exists():
        return
    import subprocess
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "magick", "-background", "none", "-density", "200",
        str(ROOT / "track2-deterministic/source-vectors/Animal_Salmon_Spawn_Eggs.svg"),
        "-resize", "256x256",
        str(NODE_PNGS["salmon_spawn"])
    ], check=True)

def load_frame(edge_id: str, t: float, src_node: str = None, dst_node: str = None) -> Image.Image:
    """Load a frame from a given edge's morph clip at edge-position t.

    Fix per operator feedback 2026-05-17: at endpoints (t near 0 or 1),
    use the SVG-direct render of the source/destination node to ensure
    the pearl's appearance matches the static node-pearl exactly at
    docking time. Avoids the color-mismatch operator noticed.
    """
    # Endpoint snap to SVG renders
    if t <= 0.03 and src_node and src_node in NODE_PNGS:
        return _flatten_to_rgb(Image.open(NODE_PNGS[src_node]))
    if t >= 0.97 and dst_node and dst_node in NODE_PNGS:
        return _flatten_to_rgb(Image.open(NODE_PNGS[dst_node]))

    frames_dir = EDGE_MORPHS[edge_id]
    if not frames_dir.exists():
        return Image.new("RGB", (256, 256), (128, 128, 128))
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        return Image.new("RGB", (256, 256), (128, 128, 128))
    idx = max(0, min(len(frames) - 1, int(round(t * (len(frames) - 1)))))
    return Image.open(frames[idx]).convert("RGB")


def _flatten_to_rgb(img: Image.Image, bg=(255, 255, 255)) -> Image.Image:
    """Flatten an RGBA image onto a solid background (default white)."""
    if img.mode == "RGBA":
        bg_img = Image.new("RGB", img.size, bg)
        bg_img.paste(img, mask=img.split()[3])
        return bg_img
    return img.convert("RGB")

def make_multi_pearl_scene(out_path: Path, t_global: float, canvas_size=(1920, 1080), node_size=240, pearl_size=200):
    """Render a scene with 3 nodes in triangle + 2 pearls in flight on different edges.

    t_global drives both pearls; they can have different speeds.
    Pearl A: raven_sun → cosmic_sun, speed 1.0 (full traversal in 1.0)
    Pearl B: cosmic_sun → salmon_spawn, speed 0.7 (offset by 0.2)
    """
    W, H = canvas_size
    scene = Image.new("RGBA", (W, H), BG_COLOR + (255,))

    # Triangle node positions
    cx, cy = W // 2, H // 2
    radius = min(W, H) * 0.32
    # Top: raven_sun (angle 90° / pi/2 from horizontal, then offset)
    angles = {"raven_sun": -math.pi/2, "cosmic_sun": math.pi/6, "salmon_spawn": 5*math.pi/6}
    node_centers = {
        name: (int(cx + radius * math.cos(a)), int(cy + radius * math.sin(a)))
        for name, a in angles.items()
    }

    # Draw 3 edges (subtle lines, glowing)
    edge_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(edge_layer)
    edges_to_draw = [
        ("raven_sun", "cosmic_sun"),
        ("cosmic_sun", "salmon_spawn"),
        ("salmon_spawn", "raven_sun"),
    ]
    for a, b in edges_to_draw:
        edraw.line([node_centers[a], node_centers[b]], fill=(*EDGE_COLOR, 90), width=2)
    edge_layer = edge_layer.filter(ImageFilter.GaussianBlur(radius=3))
    scene = Image.alpha_composite(scene, edge_layer)
    # Second pass at full opacity for definition
    edge_layer2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    e2draw = ImageDraw.Draw(edge_layer2)
    for a, b in edges_to_draw:
        e2draw.line([node_centers[a], node_centers[b]], fill=(*EDGE_COLOR, 80), width=1)
    scene = Image.alpha_composite(scene, edge_layer2)

    # Render static nodes AS PEARLS (per operator feedback 2026-05-17 PM):
    # static_mode=True so SVG content isn't over-brightened (preserves Austin's
    # detail like cosmic_sun face features which got blown out in v2).
    for name, center in node_centers.items():
        svg_render = _flatten_to_rgb(Image.open(NODE_PNGS[name]))
        node_pearl = make_pearl(svg_render, node_size, static_mode=True)
        x = center[0] - node_size // 2
        y = center[1] - node_size // 2
        scene.paste(node_pearl, (x, y), node_pearl)

    # PEARL A: raven_sun → cosmic_sun, t = t_global
    tA = t_global % 1.0
    src = node_centers["raven_sun"]
    dst = node_centers["cosmic_sun"]
    pxA = int(src[0] + tA * (dst[0] - src[0]))
    pyA = int(src[1] + tA * (dst[1] - src[1]))
    pearlA_tex = load_frame("raven_sun→cosmic_sun", tA, src_node="raven_sun", dst_node="cosmic_sun")
    pearlA = make_pearl(pearlA_tex, pearl_size)

    # PEARL B: cosmic_sun → salmon_spawn, offset and slower
    tB = (t_global - 0.25) % 1.0
    src = node_centers["cosmic_sun"]
    dst = node_centers["salmon_spawn"]
    pxB = int(src[0] + tB * (dst[0] - src[0]))
    pyB = int(src[1] + tB * (dst[1] - src[1]))
    pearlB_tex = load_frame("cosmic_sun→salmon_spawn", tB, src_node="cosmic_sun", dst_node="salmon_spawn")
    pearlB = make_pearl(pearlB_tex, int(pearl_size * 0.85))  # slightly smaller for visual variety

    # Halo behind each pearl
    halo_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(halo_layer)
    for (px, py, sz) in [(pxA, pyA, pearl_size), (pxB, pyB, int(pearl_size * 0.85))]:
        halo_r = int(sz * 0.7)
        for i in range(10):
            a = 16 - i
            if a <= 0: break
            r = halo_r + i * 3
            hdraw.ellipse([px - r, py - r, px + r, py + r], fill=(*EDGE_COLOR, a))
    halo_layer = halo_layer.filter(ImageFilter.GaussianBlur(radius=12))
    scene = Image.alpha_composite(scene, halo_layer)

    # Paste pearls
    pA_size = pearl_size
    pB_size = int(pearl_size * 0.85)
    scene.paste(pearlA, (pxA - pA_size // 2, pyA - pA_size // 2), pearlA)
    scene.paste(pearlB, (pxB - pB_size // 2, pyB - pB_size // 2), pearlB)

    scene.convert("RGB").save(out_path, "PNG")

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    render_salmon_node()

    # 1. Hero still (mid-traversal moment)
    print("Rendering 02_multi_pearl_hero_t045.png ...")
    make_multi_pearl_scene(OUT / "02_multi_pearl_hero_t045.png", t_global=0.45)

    # 2. Animation strip (8 moments)
    print("Rendering 03_multi_pearl_strip.png ...")
    strip_panel_w = 600
    strip_panel_h = 400
    strip_w = strip_panel_w * 4
    strip_h = strip_panel_h * 2
    strip = Image.new("RGB", (strip_w, strip_h), BG_COLOR)
    for i in range(8):
        t = i / 7
        scene_path = OUT / f"_strip_t{int(t*100):03d}.png"
        make_multi_pearl_scene(scene_path, t_global=t, canvas_size=(strip_panel_w, strip_panel_h), node_size=90, pearl_size=75)
        panel = Image.open(scene_path)
        row = i // 4
        col = i % 4
        strip.paste(panel, (col * strip_panel_w, row * strip_panel_h))
    strip.save(OUT / "03_multi_pearl_strip.png", "PNG")
    # Cleanup
    for f in OUT.glob("_strip_*.png"):
        f.unlink()

    # 3. Animation frames for MP4
    print("Rendering 04_multi_pearl_animation frames ...")
    anim_dir = OUT / "_anim_frames"
    anim_dir.mkdir(exist_ok=True)
    anim_n = 120  # 5 sec at 24fps
    for i in range(anim_n):
        t = i / (anim_n - 1)
        make_multi_pearl_scene(anim_dir / f"frame_{i:04d}.png", t_global=t)
        if (i + 1) % 20 == 0:
            print(f"  frame {i + 1}/{anim_n}")

    print()
    print("Compose MP4 with:")
    print(f"  ffmpeg -y -framerate 24 -i '{anim_dir}/frame_%04d.png' -c:v libx264 -pix_fmt yuv420p -crf 18 '{OUT}/04_multi_pearl_animation.mp4'")

if __name__ == "__main__":
    main()
