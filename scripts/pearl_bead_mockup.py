#!/usr/bin/env python3
"""
Pearl-bead-on-edges mockup generator (2026-05-17).

Produces static composite mockups demonstrating the pearl-bead-on-edges
visual concept for the SSD Phase 2 graph architecture: a pearl (bead)
travels along a graph edge between two Austin-piece nodes, with its
surface texture showing the morph at that edge-position.

Uses existing Exp 2 morph clip (Raven_Sun → Cosmic_Sun, 96 frames) as
texture data and source SVG thumbnails as node visuals.

Outputs to: track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/

INTERNAL ONLY per Austin consent floor (see feedback_austin_consent_trust_floor.md).
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import math

ROOT = Path(__file__).resolve().parent.parent
MORPH_FRAMES = ROOT / "track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun"
OUT = ROOT / "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17"
NODE_RAVEN = OUT / "_node_raven_sun.png"
NODE_COSMIC = OUT / "_node_cosmic_sun.png"

# Aesthetic constants (SSD palette per CLAUDE.md: deep ocean blues, bioluminescent cyans, warm salmon)
BG_COLOR = (8, 16, 32)  # deep ocean
EDGE_COLOR = (180, 200, 240)  # soft silver-blue
PEARL_HIGHLIGHT = (240, 230, 220)  # warm pearl highlight
PEARL_RIM = (160, 140, 200)  # iridescent rim hint
NODE_FRAME = (60, 80, 110)  # subtle node bezel

def load_morph_frame(t: float) -> Image.Image:
    """Load morph frame at normalized edge-position t in [0, 1]."""
    n_frames = 96
    idx = max(0, min(n_frames - 1, int(round(t * (n_frames - 1)))))
    path = MORPH_FRAMES / f"frame_{idx:04d}.png"
    return Image.open(path).convert("RGB")

def make_pearl(texture: Image.Image, size: int, static_mode: bool = False) -> Image.Image:
    """Render a pearl-bead displaying the morph texture clearly.

    Reframed 2026-05-17 after peer + operator review: previous version
    over-shaded the texture into a dark marble. New approach: the
    MORPH TEXTURE IS THE DOMINANT VISUAL; the "pearl" framing is just
    a circular form-factor with subtle curvature hints. Not faking 3D
    in PIL.

    - Texture: brightened + saturated to read clearly at small sizes
      (skipped in static_mode for SVG node renders where small details
      would get blown out by brightening)
    - Circular mask with soft feathered edge
    - Subtle rim glow (suggests luminescent edge, not heavy shading)
    - Very faint inner edge darkening (hint of curvature only)
    - NO aggressive radial darkening, NO bright top-left "highlight blob"

    static_mode (added 2026-05-17 PM per operator feedback): use for
    static node-pearls displaying SVG renders. Skips brightness/saturation
    pump because SVG content already has full contrast and would be
    blown out. Operator caught "cosmic_sun node-pearl looks like simplified
    sun without face features" — caused by brightening losing small
    formline detail.
    """
    texture = texture.resize((size, size), Image.LANCZOS).convert("RGB")

    if not static_mode:
        # Brighten + saturate the texture so it reads clearly (for video-frame textures)
        texture = ImageEnhance.Brightness(texture).enhance(1.25)
        texture = ImageEnhance.Color(texture).enhance(1.35)
        texture = ImageEnhance.Contrast(texture).enhance(1.10)

    # Soft circular mask with feathered edge
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse([0, 0, size - 1, size - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=size * 0.006))

    # Very subtle inner-edge darkening — hint of curvature only, NOT aggressive
    inner_shade = Image.new("L", (size, size), 255)
    isd = ImageDraw.Draw(inner_shade)
    cx, cy = size / 2, size / 2
    max_r = size / 2
    # Only the outermost 8% gets any shading
    n_rings = 12
    for i in range(n_rings):
        r = max_r * (1.0 - 0.08 * (i / n_rings))
        brightness = int(255 * (1 - 0.18 * (i / n_rings)))  # very mild gradient at edge
        isd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=brightness)
    inner_shade = inner_shade.filter(ImageFilter.GaussianBlur(radius=size * 0.02))

    # Apply mild edge darkening to texture
    r, g, b = texture.split()
    r = ImageChops.multiply(r, inner_shade)
    g = ImageChops.multiply(g, inner_shade)
    b = ImageChops.multiply(b, inner_shade)
    shaded = Image.merge("RGB", (r, g, b))

    # Subtle iridescent rim — soft luminous edge (NOT a dark vignette)
    rim = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rim)
    # Soft outer-edge glow (suggests pearl luminescence at the rim)
    for i in range(5):
        r_out = max_r * (0.99 - i * 0.005)
        rdraw.ellipse(
            [cx - r_out, cy - r_out, cx + r_out, cy + r_out],
            outline=(*PEARL_HIGHLIGHT, 50 - i * 8),
            width=2,
        )
    rim = rim.filter(ImageFilter.GaussianBlur(radius=size * 0.008))

    # Tiny specular dot (much smaller and softer than before — barely there hint of light)
    spec = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(spec)
    sr = size * 0.04  # tiny
    sx, sy = size * 0.36, size * 0.32
    sdraw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 255, 255, 60))
    spec = spec.filter(ImageFilter.GaussianBlur(radius=size * 0.02))

    # Compose: bright shaded texture + rim glow + tiny specular
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(shaded, (0, 0))
    out.putalpha(mask)
    out = Image.alpha_composite(out, rim)
    out = Image.alpha_composite(out, spec)
    return out

def make_node_card(node_img: Image.Image, size: int, label: str | None = None) -> Image.Image:
    """Render a node card with the piece image inside a subtle bezel."""
    card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(card)
    # Subtle bezel
    cdraw.ellipse([0, 0, size - 1, size - 1], outline=NODE_FRAME, width=3)
    # Inset the piece image
    pad = int(size * 0.08)
    inner_size = size - 2 * pad
    piece = node_img.convert("RGBA").resize((inner_size, inner_size), Image.LANCZOS)
    # Circular mask the piece
    mask = Image.new("L", (inner_size, inner_size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, inner_size - 1, inner_size - 1], fill=255)
    card.paste(piece, (pad, pad), mask)
    return card

def make_scene(
    out_path: Path,
    canvas_size: tuple[int, int],
    node_left: Image.Image,
    node_right: Image.Image,
    pearl_t: float,
    pearl_size: int,
    node_size: int,
    show_label: bool = True,
) -> None:
    """Render a single mockup scene: two nodes, edge between them, pearl at position t."""
    W, H = canvas_size
    scene = Image.new("RGB", (W, H), BG_COLOR)

    # Position nodes at left and right margins
    margin_x = int(W * 0.08)
    node_y = (H - node_size) // 2
    left_x = margin_x
    right_x = W - margin_x - node_size
    left_center = (left_x + node_size // 2, node_y + node_size // 2)
    right_center = (right_x + node_size // 2, node_y + node_size // 2)

    # Draw the edge as a subtle line with soft glow
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    edraw = ImageDraw.Draw(edge)
    edraw.line([left_center, right_center], fill=(*EDGE_COLOR, 110), width=2)
    edge = edge.filter(ImageFilter.GaussianBlur(radius=3))
    edge2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    e2draw = ImageDraw.Draw(edge2)
    e2draw.line([left_center, right_center], fill=(*EDGE_COLOR, 80), width=1)

    scene_rgba = scene.convert("RGBA")
    scene_rgba = Image.alpha_composite(scene_rgba, edge)
    scene_rgba = Image.alpha_composite(scene_rgba, edge2)

    # Paste nodes
    left_card = make_node_card(node_left, node_size)
    right_card = make_node_card(node_right, node_size)
    scene_rgba.paste(left_card, (left_x, node_y), left_card)
    scene_rgba.paste(right_card, (right_x, node_y), right_card)

    # Compute pearl position along the edge
    px = int(left_center[0] + pearl_t * (right_center[0] - left_center[0]))
    py = int(left_center[1] + pearl_t * (right_center[1] - left_center[1]))

    # Make the pearl with morph-frame texture at this t
    morph_frame = load_morph_frame(pearl_t)
    pearl = make_pearl(morph_frame, pearl_size)

    # Add pearl glow/halo behind
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(halo)
    halo_r = int(pearl_size * 0.75)
    for i in range(12):
        a = 18 - i
        if a <= 0: break
        r = halo_r + i * 3
        hdraw.ellipse([px - r, py - r, px + r, py + r], fill=(*EDGE_COLOR, a))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=15))
    scene_rgba = Image.alpha_composite(scene_rgba, halo)

    # Paste pearl
    scene_rgba.paste(pearl, (px - pearl_size // 2, py - pearl_size // 2), pearl)

    # Optional label at bottom
    if show_label:
        draw = ImageDraw.Draw(scene_rgba)
        label_text = f"pearl position on edge: t = {pearl_t:.2f}"
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(H * 0.022))
        except Exception:
            font = None
        bbox = draw.textbbox((0, 0), label_text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(
            ((W - tw) // 2, H - int(H * 0.06)),
            label_text,
            font=font,
            fill=(200, 210, 230, 200),
        )

    scene_rgba.convert("RGB").save(out_path, "PNG")

def main():
    OUT.mkdir(parents=True, exist_ok=True)

    node_raven = Image.open(NODE_RAVEN)
    node_cosmic = Image.open(NODE_COSMIC)

    # 1. Three-stage progression (t=0.0, 0.5, 1.0) — single composite
    print("Rendering 01_progression_3stage.png ...")
    W, H = 2400, 800
    progression = Image.new("RGB", (W, H), BG_COLOR)
    panel_w = W // 3
    panel_size_inner = (panel_w, H)
    for i, t in enumerate([0.0, 0.5, 1.0]):
        scene_path = OUT / f"_stage_t{int(t * 100):03d}.png"
        make_scene(
            scene_path,
            (panel_w, H),
            node_raven,
            node_cosmic,
            pearl_t=t,
            pearl_size=180,
            node_size=200,
            show_label=True,
        )
        panel = Image.open(scene_path)
        progression.paste(panel, (i * panel_w, 0))
    progression.save(OUT / "01_progression_3stage.png", "PNG")
    print(f"  → {OUT / '01_progression_3stage.png'}")

    # 2. Single-scene mockup at t=0.5 (largest, most polished)
    print("Rendering 02_single_scene_t05.png ...")
    make_scene(
        OUT / "02_single_scene_t05.png",
        (1920, 1080),
        node_raven,
        node_cosmic,
        pearl_t=0.5,
        pearl_size=240,
        node_size=280,
        show_label=False,
    )
    print(f"  → {OUT / '02_single_scene_t05.png'}")

    # 3. Animation strip (8 frames showing pearl traveling)
    print("Rendering 03_animation_strip.png ...")
    frames_n = 8
    strip_panel_w = 600
    strip_panel_h = 400
    strip_w = strip_panel_w * 4
    strip_h = strip_panel_h * 2
    strip = Image.new("RGB", (strip_w, strip_h), BG_COLOR)
    for i in range(frames_n):
        t = i / (frames_n - 1)
        scene_path = OUT / f"_strip_t{int(t * 100):03d}.png"
        make_scene(
            scene_path,
            (strip_panel_w, strip_panel_h),
            node_raven,
            node_cosmic,
            pearl_t=t,
            pearl_size=110,
            node_size=140,
            show_label=True,
        )
        panel = Image.open(scene_path)
        row = i // 4
        col = i % 4
        strip.paste(panel, (col * strip_panel_w, row * strip_panel_h))
    strip.save(OUT / "03_animation_strip.png", "PNG")
    print(f"  → {OUT / '03_animation_strip.png'}")

    # 4. Render an actual MP4 animation (smooth pearl traversal, 4 sec @ 24fps = 96 frames)
    print("Rendering 04_animation_frames/ (for MP4 composition) ...")
    anim_dir = OUT / "_anim_frames"
    anim_dir.mkdir(exist_ok=True)
    anim_n = 96
    for i in range(anim_n):
        t = i / (anim_n - 1)
        make_scene(
            anim_dir / f"frame_{i:04d}.png",
            (1920, 1080),
            node_raven,
            node_cosmic,
            pearl_t=t,
            pearl_size=240,
            node_size=280,
            show_label=False,
        )
        if (i + 1) % 16 == 0:
            print(f"  frame {i + 1}/{anim_n}")
    print(f"  → {anim_dir}/ (use ffmpeg to compile)")

    # Cleanup intermediate single-panel files
    for f in OUT.glob("_stage_*.png"):
        f.unlink()
    for f in OUT.glob("_strip_*.png"):
        f.unlink()

    print()
    print("Compose MP4 with:")
    print(f"  ffmpeg -y -framerate 24 -i '{anim_dir}/frame_%04d.png' \\")
    print(f"    -c:v libx264 -pix_fmt yuv420p -crf 18 \\")
    print(f"    '{OUT}/04_pearl_bead_traversal.mp4'")

if __name__ == "__main__":
    main()
