#!/usr/bin/env python3
"""
Lane 2E POC — atom-primitive-bridge.

Operator scope 2026-05-17 ~5:35 PM: 3-5 atom pairs only, mixed transition
types. Use Circle/Crescent/Trigon primitive cycle as shape bridge for
cross-type pairs. Preserve each atom's source/destination color and
position. Diagnostic first, then 3-4 sec clip.

Acceptance:
  1. Reads as individual forms moving/reforming, not image fading
  2. Primitives remain recognizable during transition
  3. Suggests scalable grammar
  4. No claim of meaningful correspondences (Austin's call)

POC pairs (Cosmic_Sun → Salmon_Spawn_Eggs):
  P1. eye-focal-oval → eye-focal-oval  (same-type circle→circle)
  P2. sun-ray (trigon) → egg-roe (circle)  (trigon→circle via prim morph)
  P3. crescent → egg-roe (circle)  (crescent→circle via reversed prim morph)

Source positions in left half of 1920×1080 canvas; destination positions
in right half. Atoms translate + morph across.

INTERNAL ONLY per Austin consent floor. Correspondences are author-picked
for technical demonstration, NOT cultural claims.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import csv
import math
import subprocess

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — python3.11")

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
MORPH_OUTPUTS = ROOT / "track2-deterministic/morph_outputs"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS_W = 1920
CANVAS_H = 1080
FPS = 24
N_FRAMES = 96  # 4 sec
BG_COLOR = (240, 234, 220)

# Source/dest piece centers on canvas
SRC_CENTER = (CANVAS_W // 4, CANVAS_H // 2)        # left quarter
DST_CENTER = (3 * CANVAS_W // 4, CANVAS_H // 2)    # right quarter
PIECE_RENDER_SIZE = 600  # both pieces rendered at 600px for display

# Atom display size on canvas
ATOM_RENDER_SIZE = 80  # bbox of rendered atom

# Primitive morph dirs (60 frames each)
PRIM_MORPHS = {
    ("circle", "crescent"): MORPH_OUTPUTS / "prim_circle_to_crescent",
    ("crescent", "trigon"): MORPH_OUTPUTS / "prim_crescent_to_trigon",
    ("trigon", "circle"): MORPH_OUTPUTS / "prim_trigon_to_circle",
}


def load_atoms(piece: str, viewbox: int) -> list[dict]:
    csv_path = DECOMPOSED / piece / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            try:
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "bbox": (float(row["bbox_x"]), float(row["bbox_y"]),
                             float(row["bbox_w"]), float(row["bbox_h"])),
                    "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                    "area": float(row["area"]),
                    "fill_color": row["fill_color"],
                    "isolated_png": DECOMPOSED / piece / row["isolated_png"],
                    "piece": piece,
                    "viewbox": viewbox,
                })
            except (ValueError, KeyError):
                continue
    return atoms


def pick_largest(atoms: list[dict], label: str, exclude_ids: set = None) -> dict:
    matching = [a for a in atoms if a["label"] == label]
    if exclude_ids:
        matching = [a for a in matching if a["atom_id"] not in exclude_ids]
    if not matching:
        return None
    return max(matching, key=lambda a: a["area"])


def pick_at_position(atoms: list[dict], label: str, position: str,
                     viewbox: int, exclude_ids: set = None) -> dict:
    """Pick atom of given label closest to spatial position (center / top / bottom / left / right)."""
    matching = [a for a in atoms if a["label"] == label]
    if exclude_ids:
        matching = [a for a in matching if a["atom_id"] not in exclude_ids]
    if not matching:
        return None
    cx, cy = viewbox / 2, viewbox / 2
    if position == "center":
        return min(matching, key=lambda a: math.hypot(a["centroid"][0] - cx, a["centroid"][1] - cy))
    elif position == "top":
        return min(matching, key=lambda a: a["centroid"][1])
    elif position == "bottom":
        return max(matching, key=lambda a: a["centroid"][1])
    elif position == "left":
        return min(matching, key=lambda a: a["centroid"][0])
    elif position == "right":
        return max(matching, key=lambda a: a["centroid"][0])
    return matching[0]


def primitive_for_label(label: str) -> str:
    """Map atom label to one of {circle, crescent, trigon}."""
    if label in ("circle-oval", "eye-focal-oval", "egg-roe"):
        return "circle"
    elif label in ("crescent",):
        return "crescent"
    elif label in ("trigon", "sun-ray"):
        return "trigon"
    else:
        return "circle"  # fallback


def load_primitive_morph_frames(src_prim: str, dst_prim: str) -> tuple[list[Image.Image], bool]:
    """Return (frames, reversed_flag) for primitive A → B transition.

    Uses available prim_*_to_* dirs; reverses if needed.
    Returns None,None if same primitive (no morph needed).
    """
    if src_prim == dst_prim:
        return None, False
    key = (src_prim, dst_prim)
    if key in PRIM_MORPHS:
        d = PRIM_MORPHS[key]
        if not d.exists():
            return None, False
        frames = [Image.open(f).convert("RGBA") for f in sorted(d.glob("frame_*.png"))]
        return frames, False
    # Try reverse
    rev_key = (dst_prim, src_prim)
    if rev_key in PRIM_MORPHS:
        d = PRIM_MORPHS[rev_key]
        if not d.exists():
            return None, False
        frames = list(reversed([Image.open(f).convert("RGBA") for f in sorted(d.glob("frame_*.png"))]))
        return frames, True
    return None, False


def atom_canvas_position(atom: dict, piece_center: tuple) -> tuple:
    """Map atom's viewbox-coord centroid to canvas position relative to piece_center."""
    cx_vb, cy_vb = atom["centroid"]
    vb = atom["viewbox"]
    # Normalize to [-0.5, +0.5] of piece, then scale to PIECE_RENDER_SIZE
    norm_x = (cx_vb / vb) - 0.5
    norm_y = (cy_vb / vb) - 0.5
    return (piece_center[0] + norm_x * PIECE_RENDER_SIZE,
            piece_center[1] + norm_y * PIECE_RENDER_SIZE)


def render_atom_as_primitive(prim_type: str, color: tuple, size: int) -> Image.Image:
    """Render a clean primitive shape of given type, color, size.

    Returns RGBA image of (size, size) with the primitive shape.
    Used when same-type pair or when morph frames aren't available.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 8
    if prim_type == "circle":
        d.ellipse([pad, pad, size - pad, size - pad], fill=color + (255,))
    elif prim_type == "crescent":
        # Outer circle filled, inner offset circle in BG color (subtracts)
        d.ellipse([pad, pad, size - pad, size - pad], fill=color + (255,))
        d.ellipse([pad + size // 4, pad, size - pad + size // 4, size - pad], fill=(0, 0, 0, 0))
    elif prim_type == "trigon":
        # Triangle pointing right
        cx, cy = size // 2, size // 2
        d.polygon([(pad, pad), (size - pad, cy), (pad, size - pad)], fill=color + (255,))
    return img


def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (60, 60, 60)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def main():
    cosmic_atoms = load_atoms("Nature_Cosmic_Sun", 108)
    salmon_atoms = load_atoms("Animal_Salmon_Spawn_Eggs", 1500)
    print(f"Cosmic: {len(cosmic_atoms)} atoms, Salmon: {len(salmon_atoms)} atoms")

    # Pick atom pairs — SPATIALLY meaningful so correspondences read as intentional
    # P1: CENTER → CENTER (sun center → yin-yang pivot)
    # P2: TOP → TOP (top sun-ray → top of roe field)
    # P3: BOTTOM → BOTTOM (bottom crescent → bottom of roe field)
    pairs_spec = [
        ("eye-focal-oval", "eye-focal-oval", "center",  "P1_center_circle_to_circle"),
        ("sun-ray",         "egg-roe",        "top",     "P2_top_trigon_to_circle"),
        ("crescent",        "egg-roe",        "bottom",  "P3_bottom_crescent_to_circle"),
    ]
    pairs = []
    used_dst_ids = set()
    for src_label, dst_label, position, name in pairs_spec:
        src_atom = pick_at_position(cosmic_atoms, src_label, position, 108)
        dst_atom = pick_at_position(salmon_atoms, dst_label, position, 1500, exclude_ids=used_dst_ids)
        if src_atom is None or dst_atom is None:
            print(f"  SKIP {name}: src={src_atom is not None}, dst={dst_atom is not None}")
            continue
        used_dst_ids.add(dst_atom["atom_id"])
        pairs.append({
            "name": name,
            "src_atom": src_atom,
            "dst_atom": dst_atom,
            "src_prim": primitive_for_label(src_label),
            "dst_prim": primitive_for_label(dst_label),
            "src_color": hex_to_rgb(src_atom["fill_color"]),
            "dst_color": hex_to_rgb(dst_atom["fill_color"]),
            "src_pos": atom_canvas_position(src_atom, SRC_CENTER),
            "dst_pos": atom_canvas_position(dst_atom, DST_CENTER),
        })
        print(f"  {name}: {src_atom['atom_id']} ({src_atom['fill_color']}) → {dst_atom['atom_id']} ({dst_atom['fill_color']})")

    # Pre-load primitive morph frames per pair
    for p in pairs:
        frames, reversed_flag = load_primitive_morph_frames(p["src_prim"], p["dst_prim"])
        p["morph_frames"] = frames
        p["morph_reversed"] = reversed_flag
        if frames:
            print(f"  {p['name']}: morph frames {len(frames)} (reversed={reversed_flag})")
        else:
            print(f"  {p['name']}: same primitive type, no morph needed")

    out_dir = INTERNAL / "lane_2e_atom_primitive_bridge_poc_v002_spatial_pairs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "lane_2e_atom_primitive_bridge_poc_v002_spatial_pairs.mp4"

    # Pre-render the two source/destination pieces (faded) for background context
    def load_and_fit(piece, target_size):
        jpg = TRAINING / f"{piece}.jpg"
        img = Image.open(jpg).convert("RGB")
        img = ImageOps.contain(img, (target_size, target_size), Image.LANCZOS)
        # Pad to square
        sq = Image.new("RGB", (target_size, target_size), BG_COLOR)
        sq.paste(img, ((target_size - img.width) // 2, (target_size - img.height) // 2))
        return sq

    src_piece_img = load_and_fit("Nature_Cosmic_Sun", PIECE_RENDER_SIZE)
    dst_piece_img = load_and_fit("Animal_Salmon_Spawn_Eggs", PIECE_RENDER_SIZE)

    # Diagnostic still: source + dest pieces + correspondence lines
    diag = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    # Paste pieces at half opacity
    src_faded = Image.blend(Image.new("RGB", src_piece_img.size, BG_COLOR), src_piece_img, 0.4)
    dst_faded = Image.blend(Image.new("RGB", dst_piece_img.size, BG_COLOR), dst_piece_img, 0.4)
    diag.paste(src_faded, (SRC_CENTER[0] - PIECE_RENDER_SIZE // 2, SRC_CENTER[1] - PIECE_RENDER_SIZE // 2))
    diag.paste(dst_faded, (DST_CENTER[0] - PIECE_RENDER_SIZE // 2, DST_CENTER[1] - PIECE_RENDER_SIZE // 2))
    dd = ImageDraw.Draw(diag)
    # Labels
    dd.text((SRC_CENTER[0] - 80, 40), "Cosmic_Sun (source)", fill=(80, 80, 80))
    dd.text((DST_CENTER[0] - 90, 40), "Salmon_Spawn (dest)", fill=(80, 80, 80))
    # Correspondence arrows + atoms
    pair_colors = [(220, 60, 60), (60, 130, 220), (60, 180, 80)]
    for i, p in enumerate(pairs):
        c = pair_colors[i % len(pair_colors)]
        sp, dp = p["src_pos"], p["dst_pos"]
        # Source atom (circle outline at src position)
        r = 22
        dd.ellipse([sp[0]-r, sp[1]-r, sp[0]+r, sp[1]+r], outline=c, width=3)
        dd.ellipse([dp[0]-r, dp[1]-r, dp[0]+r, dp[1]+r], outline=c, width=3)
        # Arrow line
        dd.line([sp, dp], fill=c, width=2)
        # Label
        mid_x = (sp[0] + dp[0]) // 2
        mid_y = (sp[1] + dp[1]) // 2 - 20
        dd.text((mid_x - 100, mid_y), p["name"], fill=c)
    diag.save(out_dir / "_diagnostic_correspondences.png")

    # Animation phases:
    #   0-15:   hold source piece + source atoms visible at src positions
    #   15-80:  atoms translate + shape-morph from src → dst
    #   80-96:  hold dest piece + dest atoms visible at dst positions
    HOLD_SRC_END = 15
    HOLD_DST_START = 80

    print(f"Rendering {N_FRAMES} frames {CANVAS_W}×{CANVAS_H}...")
    for i in range(N_FRAMES):
        t_norm = i / (N_FRAMES - 1)

        # Background composite: src piece fades out, dst piece fades in
        if i < HOLD_SRC_END:
            src_alpha = 1.0
            dst_alpha = 0.0
        elif i < HOLD_DST_START:
            phase = (i - HOLD_SRC_END) / (HOLD_DST_START - HOLD_SRC_END)
            src_alpha = 1.0 - phase
            dst_alpha = phase
        else:
            src_alpha = 0.0
            dst_alpha = 1.0

        canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
        # Faded pieces
        if src_alpha > 0:
            src_blended = Image.blend(Image.new("RGB", src_piece_img.size, BG_COLOR), src_piece_img, src_alpha * 0.3)
            canvas.paste(src_blended, (SRC_CENTER[0] - PIECE_RENDER_SIZE // 2, SRC_CENTER[1] - PIECE_RENDER_SIZE // 2))
        if dst_alpha > 0:
            dst_blended = Image.blend(Image.new("RGB", dst_piece_img.size, BG_COLOR), dst_piece_img, dst_alpha * 0.3)
            canvas.paste(dst_blended, (DST_CENTER[0] - PIECE_RENDER_SIZE // 2, DST_CENTER[1] - PIECE_RENDER_SIZE // 2))

        canvas_rgba = canvas.convert("RGBA")

        # Per-atom animation
        for p in pairs:
            # Compute atom progress
            if i < HOLD_SRC_END:
                pair_t = 0.0  # at source
            elif i < HOLD_DST_START:
                pair_t = (i - HOLD_SRC_END) / (HOLD_DST_START - HOLD_SRC_END)
            else:
                pair_t = 1.0  # at dest
            # Eased
            pair_t_eased = pair_t * pair_t * (3 - 2 * pair_t)

            # Position: lerp src → dst
            px = p["src_pos"][0] + pair_t_eased * (p["dst_pos"][0] - p["src_pos"][0])
            py = p["src_pos"][1] + pair_t_eased * (p["dst_pos"][1] - p["src_pos"][1])

            # Color: lerp
            color = lerp_color(p["src_color"], p["dst_color"], pair_t_eased)

            # Shape: get current primitive frame
            if p["morph_frames"] is None:
                # Same-type — use simple primitive renderer
                shape_img = render_atom_as_primitive(p["src_prim"], color, ATOM_RENDER_SIZE)
            else:
                # Cross-type — sample primitive morph frame at pair_t
                n_morph = len(p["morph_frames"])
                morph_idx = int(round(pair_t_eased * (n_morph - 1)))
                morph_idx = max(0, min(n_morph - 1, morph_idx))
                morph_frame = p["morph_frames"][morph_idx]
                # Resize to ATOM_RENDER_SIZE
                morph_frame = morph_frame.resize((ATOM_RENDER_SIZE, ATOM_RENDER_SIZE), Image.LANCZOS)
                # Tint with current color: multiply RGB by color/255
                arr = np.asarray(morph_frame, dtype=np.float32)
                # morph frames are black-on-white; treat dark pixels as the shape
                # Build new RGBA: alpha from darkness, RGB from current color
                darkness = 1.0 - (arr[..., :3].mean(axis=-1) / 255.0)
                alpha = (darkness * 255).astype(np.uint8)
                rgb = np.zeros((ATOM_RENDER_SIZE, ATOM_RENDER_SIZE, 3), dtype=np.uint8)
                rgb[..., 0] = color[0]
                rgb[..., 1] = color[1]
                rgb[..., 2] = color[2]
                shape_img = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")

            # Paste centered at (px, py)
            sw, sh = shape_img.size
            paste_x = int(px - sw / 2)
            paste_y = int(py - sh / 2)
            canvas_rgba.alpha_composite(shape_img, (paste_x, paste_y))

        canvas_rgba.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
        if (i + 1) % 24 == 0:
            print(f"  frame {i + 1}/{N_FRAMES}")

    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(out_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"\n→ {out_mp4}")
        print(f"  _diagnostic_correspondences.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
