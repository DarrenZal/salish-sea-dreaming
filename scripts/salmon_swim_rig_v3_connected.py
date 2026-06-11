#!/usr/bin/env python3
"""
salmon_swim_rig_v003 — connected-component masks.

v002 worked but had fin/crescent fragments because atom-label-based
masks miss some salmon-body atoms (mis-classified as "other", or
centroid lands in wrong half). v003 fix: union ALL non-roe non-bg atoms
into one mask, apply morphological close to fill small gaps, run
connected-component labeling, take the 2 largest blobs = the 2 salmon
bodies. No arbitrary y-split.

Auto-assigns upper/lower by component centroid y-coordinate.
Same cv2.remap traveling-wave warp as v001/v002.

Acceptance: no orphan fin pieces, no stationary fragments inside
moving salmon, body warp is one continuous deformation per fish.
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
N_FRAMES = 144

PIECE = "Animal_Salmon_Spawn_Eggs"
JPG_NAME = "Animal_Salmon_Spawn_Eggs.jpg"
STATIC_LABELS = {"egg-roe", "background-field", "negative-space"}

WAVE_AMPLITUDE_FRAC = 0.04
WAVELENGTH_FRAC = 1.4
CYCLES_PER_LOOP = 2

# Morphological close kernel (fill internal gaps in body mask)
CLOSE_KERNEL_PX = 15
# Dilation around final per-salmon mask (catches antialiased edge pixels)
FINAL_DILATE_PX = 5


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
    """Return (upper_dict, lower_dict) each with mask + head + tail (canvas px).

    Pipeline:
      1. Union of all non-roe non-bg atom masks
      2. Morphological close to fill internal gaps
      3. Connected-component labeling, take 2 largest blobs
      4. Assign upper/lower by centroid y
      5. Within each component, find head (eye-focal nearest) and tail
         (fin-tail nearest), with PCA fallback
    """
    # Step 1: union of body atoms
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    eye_focal_pos = []
    fin_tail_pos = []
    scale = CANVAS / VIEWBOX
    for a in atoms:
        if a["label"] in STATIC_LABELS:
            continue
        m = build_atom_alpha(a)
        union = np.maximum(union, m)
        cx_canvas = a["centroid"][0] * scale
        cy_canvas = a["centroid"][1] * scale
        if a["label"] == "eye-focal-oval":
            eye_focal_pos.append((cx_canvas, cy_canvas))
        elif a["label"] == "fin-tail":
            fin_tail_pos.append((cx_canvas, cy_canvas))

    print(f"  Union mask area: {(union > 128).sum()} px")
    print(f"  Eye-focal atoms: {len(eye_focal_pos)}, fin-tail: {len(fin_tail_pos)}")

    # Step 2: morphological close to fill gaps
    binary = (union > 128).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (CLOSE_KERNEL_PX, CLOSE_KERNEL_PX))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    print(f"  After CLOSE: {(closed > 0).sum()} px")

    # Step 3: connected components
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    print(f"  Connected components: {n_labels - 1} (excluding bg)")
    # Sort components by area (largest first), skip bg (label 0)
    component_info = []
    for lbl in range(1, n_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        cy_centroid = centroids[lbl][1]
        component_info.append((lbl, area, cy_centroid))
    component_info.sort(key=lambda x: -x[1])
    if len(component_info) < 2:
        raise SystemExit("Failed to segment two salmon — fewer than 2 components")
    top_two = component_info[:2]
    print(f"  Top 2 areas: {top_two[0][1]} (cy={top_two[0][2]:.0f}), "
          f"{top_two[1][1]} (cy={top_two[1][2]:.0f})")

    # Assign upper/lower
    top_two.sort(key=lambda x: x[2])  # sort by cy ascending
    upper_lbl = top_two[0][0]  # smaller cy
    lower_lbl = top_two[1][0]

    upper_mask = ((labels == upper_lbl).astype(np.uint8)) * 255
    lower_mask = ((labels == lower_lbl).astype(np.uint8)) * 255

    # Final small dilation to soften edges
    final_kernel = np.ones((FINAL_DILATE_PX, FINAL_DILATE_PX), np.uint8)
    upper_mask = cv2.dilate(upper_mask, final_kernel, iterations=1)
    lower_mask = cv2.dilate(lower_mask, final_kernel, iterations=1)

    # Step 5: head/tail per component
    def find_spine_for_mask(mask: np.ndarray, eye_atoms: list, fin_atoms: list) -> tuple:
        # Filter atoms whose canvas position is INSIDE this component
        eyes_in = [p for p in eye_atoms if mask[int(p[1]), int(p[0])] > 0]
        fins_in = [p for p in fin_atoms if mask[int(p[1]), int(p[0])] > 0]
        if eyes_in and fins_in:
            return eyes_in[0], fins_in[0]
        # PCA fallback
        ys, xs = np.where(mask > 0)
        pts = np.column_stack([xs, ys]).astype(np.float32)
        mean = pts.mean(axis=0)
        cov = np.cov((pts - mean).T)
        _, eigvecs = np.linalg.eigh(cov)
        major = eigvecs[:, -1]
        proj = (pts - mean) @ major
        return tuple(mean + major * proj.min()), tuple(mean + major * proj.max())

    u_head, u_tail = find_spine_for_mask(upper_mask, eye_focal_pos, fin_tail_pos)
    l_head, l_tail = find_spine_for_mask(lower_mask, eye_focal_pos, fin_tail_pos)

    return ({"mask": upper_mask, "head": u_head, "tail": u_tail},
            {"mask": lower_mask, "head": l_head, "tail": l_tail})


def compute_remap_field(canvas_size: int, head: tuple, tail: tuple, t_phase: float) -> tuple[np.ndarray, np.ndarray]:
    H, W = canvas_size, canvas_size
    xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    hx, hy = head
    tx, ty = tail
    sx_v = tx - hx
    sy_v = ty - hy
    L = math.hypot(sx_v, sy_v) or 1.0
    sx, sy = sx_v / L, sy_v / L
    px, py = -sy, sx
    A = WAVE_AMPLITUDE_FRAC * L
    wavelength = WAVELENGTH_FRAC * L
    dx = xs - hx
    dy = ys - hy
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


def main():
    atoms = load_atoms()
    print(f"Loaded {len(atoms)} atoms")
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)

    print("Segmenting two salmon via connected components...")
    upper, lower = segment_two_salmon(atoms)
    print(f"Upper: mask {upper['mask'].sum() // 255} px, "
          f"head={upper['head']}, tail={upper['tail']}")
    print(f"Lower: mask {lower['mask'].sum() // 255} px, "
          f"head={lower['head']}, tail={lower['tail']}")

    # Inpaint base
    combined = np.maximum(upper["mask"], lower["mask"])
    print("Inpainting base...")
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(combined, kernel, iterations=1)
    bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=15, flags=cv2.INPAINT_TELEA)
    inpainted = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted_img = Image.fromarray(inpainted, "RGB")

    upper_rgba = np.dstack([base_rgb, upper["mask"]])
    lower_rgba = np.dstack([base_rgb, lower["mask"]])

    out_dir = INTERNAL / "salmon_swim_rig_v004_confined"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_swim_rig_v004_confined.mp4"
    inpainted_img.save(out_dir / "_inpainted_base.png")

    # Build "confine masks" — dilate body mask by 1.5x max sway amount so
    # warp output can sway WITHIN this region but not ghost far away
    max_sway_px = int(WAVE_AMPLITUDE_FRAC * 1000 * 1.5)  # ~60px buffer
    confine_kernel = np.ones((max_sway_px*2, max_sway_px*2), np.uint8)
    upper_confine = cv2.dilate(upper["mask"], confine_kernel, iterations=1)
    lower_confine = cv2.dilate(lower["mask"], confine_kernel, iterations=1)
    print(f"  Confine masks: upper {(upper_confine > 0).sum()} px, lower {(lower_confine > 0).sum()} px (max_sway={max_sway_px}px)")

    # Diagnostic still
    diag = base.copy().convert("RGBA")
    ov = Image.new("RGBA", diag.size, (0, 0, 0, 0))
    for color, half in [((255, 0, 0, 80), upper), ((0, 0, 255, 80), lower)]:
        m = Image.fromarray((half["mask"] > 0).astype(np.uint8) * 255, "L")
        clr = Image.new("RGBA", diag.size, color)
        ov = Image.alpha_composite(ov, Image.composite(clr, Image.new("RGBA", diag.size, (0, 0, 0, 0)), m))
    od = ImageDraw.Draw(ov)
    for half, line_color in [(upper, (0, 255, 255, 255)), (lower, (255, 200, 0, 255))]:
        od.line([half["head"], half["tail"]], fill=line_color, width=5)
        r = 18
        od.ellipse([half["head"][0]-r, half["head"][1]-r, half["head"][0]+r, half["head"][1]+r], outline=(0, 255, 0, 255), width=4)
        od.ellipse([half["tail"][0]-r, half["tail"][1]-r, half["tail"][0]+r, half["tail"][1]+r], outline=(255, 255, 0, 255), width=4)
    Image.alpha_composite(diag, ov).convert("RGB").save(out_dir / "_segments_diagnostic.png")

    stills = {0: "00_at_rest.png", N_FRAMES // 4: "01_peak.png",
              N_FRAMES // 2: "02_mid.png", N_FRAMES - 1: "03_return.png"}

    omega_total = CYCLES_PER_LOOP * 2 * math.pi
    print(f"Rendering {N_FRAMES} frames...")
    for i in range(N_FRAMES):
        t_u = (i / N_FRAMES) * omega_total
        t_l = t_u + math.pi
        u_mx, u_my = compute_remap_field(CANVAS, upper["head"], upper["tail"], t_u)
        l_mx, l_my = compute_remap_field(CANVAS, lower["head"], lower["tail"], t_l)
        u_warped = cv2.remap(upper_rgba, u_mx, u_my,
                             interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
        l_warped = cv2.remap(lower_rgba, l_mx, l_my,
                             interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
        # Confine warp output to near-body region — kills ghost artifacts
        # in canvas corners where the warp field pushed body pixels
        u_warped[..., 3] = np.minimum(u_warped[..., 3], upper_confine)
        l_warped[..., 3] = np.minimum(l_warped[..., 3], lower_confine)
        canvas = inpainted_img.copy().convert("RGBA")
        canvas.alpha_composite(Image.fromarray(u_warped, "RGBA"))
        canvas.alpha_composite(Image.fromarray(l_warped, "RGBA"))
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
        print(f"  diagnostics: _inpainted_base.png, _segments_diagnostic.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
