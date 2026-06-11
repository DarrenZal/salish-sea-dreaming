#!/usr/bin/env python3
"""
salmon_circle_chase_v001 — A.2 circle chase.

Both salmon follow same circular orbit (clockwise on screen), 180°
phase-offset so they're always opposite. Each fish rotates so head
points in tangent direction (chasing). Swim wave applied perpendicular
to current body orientation. Roe + bg stay static.

Reuses v004 pipeline (connected-component masks, swim wave, confine
mask) but adds per-frame rotation + translation around circle path.

Guardrails per peer/operator 2026-05-17:
  - Preserve fish as coherent body (no detached fins/tails)
  - No independent group drift; whole fish moves as one
  - No eye pulse added yet
  - Target image: "Austin's two salmon have started swimming inside the piece"
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import numpy as np
import csv
import math
import subprocess

try:
    import cv2
except ImportError:
    raise SystemExit("Needs cv2 — run with python3.11")

ROOT = Path(__file__).resolve().parent.parent
DECOMPOSED = ROOT / "austin-v2-ingest/decomposed"
TRAINING = ROOT / "austin-v2-ingest/training"
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"

CANVAS = 1536
VIEWBOX = 1500
FPS = 24
N_FRAMES = 192  # 8 sec — longer loop for circle motion to read

PIECE = "Animal_Salmon_Spawn_Eggs"
JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"
STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}

# Swim wave (carried over from v004)
WAVE_AMPLITUDE_FRAC = 0.04
WAVELENGTH_FRAC = 1.4
SWIM_CYCLES_PER_LOOP = 4  # faster body wave than circle orbit

# Circle orbit
CIRCLE_RADIUS_FRAC = 0.12  # 12% of canvas — modest, fish stays "inside the piece"
CIRCLE_ORBITS_PER_LOOP = 1  # 1 full revolution per video


def load_atoms() -> list[dict]:
    csv_path = DECOMPOSED / PIECE / "atom_metadata.csv"
    atoms = []
    with csv_path.open() as f:
        for row in csv.DictReader(f):
            try:
                atoms.append({
                    "atom_id": row["atom_id"],
                    "label": row["ai_label"],
                    "centroid": (float(row["centroid_x"]), float(row["centroid_y"])),
                    "isolated_png": DECOMPOSED / PIECE / row["isolated_png"],
                })
            except (ValueError, KeyError):
                continue
    return atoms


def load_base_jpg() -> Image.Image:
    img = Image.open(TRAINING / JPG_NAME).convert("RGB")
    img = ImageOps.contain(img, (CANVAS, CANVAS), Image.LANCZOS)
    if img.size != (CANVAS, CANVAS):
        canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
        x = (CANVAS - img.width) // 2
        y = (CANVAS - img.height) // 2
        canvas.paste(img, (x, y))
        img = canvas
    return img


def build_atom_alpha(atom: dict) -> np.ndarray:
    iso = Image.open(atom["isolated_png"]).convert("L").resize((CANVAS, CANVAS), Image.LANCZOS)
    return 255 - np.asarray(iso, dtype=np.uint8)


def segment_two_salmon(atoms: list[dict]) -> tuple[dict, dict]:
    """Same as v003/v004: union → close → connected components → 2 largest."""
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    eye_pos = []
    fin_pos = []
    scale = CANVAS / VIEWBOX
    for a in atoms:
        if a["label"] in STATIC_LABELS:
            continue
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        cxc = a["centroid"][0] * scale
        cyc = a["centroid"][1] * scale
        if a["label"] == "eye-focal-oval":
            eye_pos.append((cxc, cyc))
        elif a["label"] == "fin-tail":
            fin_pos.append((cxc, cyc))

    binary = (union > 128).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    comps = [(i, stats[i, cv2.CC_STAT_AREA], centroids[i][1]) for i in range(1, n_labels)]
    comps.sort(key=lambda x: -x[1])
    top_two = comps[:2]
    top_two.sort(key=lambda x: x[2])  # by cy ascending
    upper_lbl, lower_lbl = top_two[0][0], top_two[1][0]
    upper_mask = ((labels == upper_lbl).astype(np.uint8)) * 255
    lower_mask = ((labels == lower_lbl).astype(np.uint8)) * 255
    fdk = np.ones((5, 5), np.uint8)
    upper_mask = cv2.dilate(upper_mask, fdk, iterations=1)
    lower_mask = cv2.dilate(lower_mask, fdk, iterations=1)

    def find_spine(mask, eyes, fins):
        eyes_in = [p for p in eyes if mask[int(p[1]), int(p[0])] > 0]
        fins_in = [p for p in fins if mask[int(p[1]), int(p[0])] > 0]
        if eyes_in and fins_in:
            return eyes_in[0], fins_in[0]
        ys, xs = np.where(mask > 0)
        pts = np.column_stack([xs, ys]).astype(np.float32)
        mean = pts.mean(axis=0)
        cov = np.cov((pts - mean).T)
        _, eigvecs = np.linalg.eigh(cov)
        major = eigvecs[:, -1]
        proj = (pts - mean) @ major
        return tuple(mean + major * proj.min()), tuple(mean + major * proj.max())

    u_head, u_tail = find_spine(upper_mask, eye_pos, fin_pos)
    l_head, l_tail = find_spine(lower_mask, eye_pos, fin_pos)
    return ({"mask": upper_mask, "head": u_head, "tail": u_tail},
            {"mask": lower_mask, "head": l_head, "tail": l_tail})


def compute_remap_field(head: tuple, tail: tuple, t_phase: float) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = np.meshgrid(np.arange(CANVAS, dtype=np.float32), np.arange(CANVAS, dtype=np.float32))
    hx, hy = head
    tx, ty = tail
    sx_v, sy_v = tx - hx, ty - hy
    L = math.hypot(sx_v, sy_v) or 1.0
    sx, sy = sx_v / L, sy_v / L
    px, py = -sy, sx
    A = WAVE_AMPLITUDE_FRAC * L
    wavelength = WAVELENGTH_FRAC * L
    dx, dy = xs - hx, ys - hy
    s = dx * sx + dy * sy
    s_norm = np.clip(s / L, 0.0, 1.0)
    phase = (2 * math.pi * s / wavelength) - t_phase
    gain = s_norm * s_norm * (3.0 - 2.0 * s_norm)
    lateral = A * gain * np.sin(phase)
    disp_x = lateral * px
    disp_y = lateral * py
    map_x = (xs - disp_x).astype(np.float32)
    map_y = (ys - disp_y).astype(np.float32)
    return map_x, map_y


def warp_then_transform(fish_rgba: np.ndarray, head: tuple, tail: tuple,
                        swim_phase: float, confine_mask: np.ndarray,
                        target_pos: tuple, target_angle_rad: float) -> np.ndarray:
    """Apply swim warp at rest, then rotate around fish centroid + translate to target.

    Returns full-canvas RGBA. Composite onto base.
    """
    # 1. Swim warp at rest position
    map_x, map_y = compute_remap_field(head, tail, swim_phase)
    warped = cv2.remap(fish_rgba, map_x, map_y,
                       interpolation=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_TRANSPARENT)
    # Confine to body region
    warped[..., 3] = np.minimum(warped[..., 3], confine_mask)

    # 2. Rotate around fish centroid + translate to target
    rest_cx = (head[0] + tail[0]) / 2
    rest_cy = (head[1] + tail[1]) / 2
    # Fish natural head direction (tail → head vector)
    nat_dx = head[0] - tail[0]
    nat_dy = head[1] - tail[1]
    nat_angle = math.atan2(nat_dy, nat_dx)

    rotation_rad = target_angle_rad - nat_angle
    rotation_deg = math.degrees(rotation_rad)

    # cv2.getRotationMatrix2D: rotate by angle around center, then we add translation
    # Note: positive angle = counterclockwise in cv2
    M = cv2.getRotationMatrix2D((rest_cx, rest_cy), -rotation_deg, 1.0)
    # Add translation: after rotation, move from rest_centroid to target_pos
    tx = target_pos[0] - rest_cx
    ty = target_pos[1] - rest_cy
    M[0, 2] += tx
    M[1, 2] += ty

    # Apply affine
    transformed = cv2.warpAffine(warped, M, (CANVAS, CANVAS),
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_TRANSPARENT)
    return transformed


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    print("Segmenting two salmon...")
    upper, lower = segment_two_salmon(atoms)
    print(f"Upper: head={upper['head']}, tail={upper['tail']}")
    print(f"Lower: head={lower['head']}, tail={lower['tail']}")

    combined_mask = np.maximum(upper["mask"], lower["mask"])
    print("Inpainting base...")
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(combined_mask, kernel, iterations=1)
    bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=15, flags=cv2.INPAINT_TELEA)
    inpainted = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted_img = Image.fromarray(inpainted, "RGB")

    upper_rgba = np.dstack([base_rgb, upper["mask"]])
    lower_rgba = np.dstack([base_rgb, lower["mask"]])

    # Confine masks per v004
    L_upper = math.hypot(upper["head"][0] - upper["tail"][0], upper["head"][1] - upper["tail"][1])
    L_lower = math.hypot(lower["head"][0] - lower["tail"][0], lower["head"][1] - lower["tail"][1])
    max_sway = int(WAVE_AMPLITUDE_FRAC * max(L_upper, L_lower) * 1.5)
    cf_kernel = np.ones((max_sway*2, max_sway*2), np.uint8)
    upper_confine = cv2.dilate(upper["mask"], cf_kernel, iterations=1)
    lower_confine = cv2.dilate(lower["mask"], cf_kernel, iterations=1)

    out_dir = INTERNAL / "salmon_circle_chase_v001"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_circle_chase_v001.mp4"
    inpainted_img.save(out_dir / "_inpainted_base.png")

    # Circle parameters
    R = CIRCLE_RADIUS_FRAC * CANVAS
    # Use mean of the two fish centroids as orbit center
    cx_circle = (upper["head"][0] + upper["tail"][0] + lower["head"][0] + lower["tail"][0]) / 4
    cy_circle = (upper["head"][1] + upper["tail"][1] + lower["head"][1] + lower["tail"][1]) / 4
    print(f"Circle: center=({cx_circle:.0f}, {cy_circle:.0f}), R={R:.0f}px")

    # Diagnostic with circle drawn
    diag = base.copy().convert("RGBA")
    od = ImageDraw.Draw(diag)
    od.ellipse([cx_circle-R, cy_circle-R, cx_circle+R, cy_circle+R], outline=(255, 0, 255, 200), width=4)
    od.ellipse([cx_circle-8, cy_circle-8, cx_circle+8, cy_circle+8], fill=(255, 0, 255, 200))
    # Mark upper rest position (red) and lower rest position (blue)
    u_rest = ((upper["head"][0] + upper["tail"][0])/2, (upper["head"][1] + upper["tail"][1])/2)
    l_rest = ((lower["head"][0] + lower["tail"][0])/2, (lower["head"][1] + lower["tail"][1])/2)
    r = 16
    od.ellipse([u_rest[0]-r, u_rest[1]-r, u_rest[0]+r, u_rest[1]+r], outline=(255, 0, 0, 255), width=4)
    od.ellipse([l_rest[0]-r, l_rest[1]-r, l_rest[0]+r, l_rest[1]+r], outline=(0, 0, 255, 255), width=4)
    diag.convert("RGB").save(out_dir / "_circle_diagnostic.png")

    stills = {0: "00_t000.png", N_FRAMES // 4: "01_t025.png",
              N_FRAMES // 2: "02_t050.png", 3*N_FRAMES // 4: "03_t075.png"}

    omega_swim = SWIM_CYCLES_PER_LOOP * 2 * math.pi
    omega_orbit = CIRCLE_ORBITS_PER_LOOP * 2 * math.pi
    initial_offset_upper = 0.0  # start at right (east)
    initial_offset_lower = math.pi  # start at left (west) — 180° offset

    print(f"Rendering {N_FRAMES} frames (clockwise orbit, 180° offset)...")
    for i in range(N_FRAMES):
        t_norm = i / N_FRAMES
        theta_upper = initial_offset_upper + t_norm * omega_orbit  # clockwise
        theta_lower = initial_offset_lower + t_norm * omega_orbit
        swim_phase = t_norm * omega_swim

        # Target positions on circle
        u_pos = (cx_circle + R * math.cos(theta_upper), cy_circle + R * math.sin(theta_upper))
        l_pos = (cx_circle + R * math.cos(theta_lower), cy_circle + R * math.sin(theta_lower))

        # Target angles: tangent to circle at current θ for clockwise motion.
        # For clockwise on screen (y-down), tangent at θ = atan2(cos θ, -sin θ).
        u_tangent = math.atan2(math.cos(theta_upper), -math.sin(theta_upper))
        l_tangent = math.atan2(math.cos(theta_lower), -math.sin(theta_lower))

        u_transformed = warp_then_transform(upper_rgba, upper["head"], upper["tail"],
                                            swim_phase, upper_confine,
                                            u_pos, u_tangent)
        l_transformed = warp_then_transform(lower_rgba, lower["head"], lower["tail"],
                                            swim_phase, lower_confine,
                                            l_pos, l_tangent)
        canvas = inpainted_img.copy().convert("RGBA")
        canvas.alpha_composite(Image.fromarray(u_transformed, "RGBA"))
        canvas.alpha_composite(Image.fromarray(l_transformed, "RGBA"))
        canvas.convert("RGB").save(out_dir / f"frame_{i:04d}.png")
        if i in stills:
            canvas.convert("RGB").save(out_dir / stills[i])
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
        print(f"  _inpainted_base.png + _circle_diagnostic.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
