#!/usr/bin/env python3
"""
salmon_in_place_v005 — v004 refined with cleaner masks + eye pulse.

Scope per operator 2026-05-17 ~5:05 PM: refine v004 only. Two changes
from v004:
  1. CLOSE_KERNEL_PX 15 → 35 + FINAL_DILATE_PX 5 → 10. Catches fin/
     crescent fragments that v004 missed (operator's original
     complaint).
  2. Add ONE subtle local articulation: eye-focal-oval pulse on top of
     the warped body. Operator-mentioned earlier ("maybe its eyes are
     moving around").

NO other changes. NO straighten / translate / rotate. NO additional
overlays beyond eye. If v005 doesn't clearly improve v004 → keep v004
canonical, stop.
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

# v005 mask refinement: larger close kernel + larger dilate to catch fragments
CLOSE_KERNEL_PX = 35  # was 15
FINAL_DILATE_PX = 10  # was 5

# Eye pulse params (one subtle local articulation)
EYE_PULSE_AMPLITUDE = 0.06  # 6% scale variation = ±3% from rest
EYE_PULSE_CYCLES = 4  # 4 pulses per loop = approx heartbeat


def load_atoms() -> list[dict]:
    csv_path = DECOMPOSED / PIECE / "atom_metadata.csv"
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


def segment_two_salmon(atoms: list[dict]):
    union = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    eye_atoms = []
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
            eye_atoms.append({
                "centroid_canvas": (cxc, cyc),
                "bbox": (a["bbox"][0] * scale, a["bbox"][1] * scale,
                         a["bbox"][2] * scale, a["bbox"][3] * scale),
                "mask": m,
                "atom": a,
            })
        elif a["label"] == "fin-tail":
            fin_pos.append((cxc, cyc))

    binary = (union > 128).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (CLOSE_KERNEL_PX, CLOSE_KERNEL_PX))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed, connectivity=8)
    comps = [(i, stats[i, cv2.CC_STAT_AREA], centroids[i][1]) for i in range(1, n_labels)]
    comps.sort(key=lambda x: -x[1])
    top_two = sorted(comps[:2], key=lambda x: x[2])
    upper_lbl, lower_lbl = top_two[0][0], top_two[1][0]
    upper_mask = ((labels == upper_lbl).astype(np.uint8)) * 255
    lower_mask = ((labels == lower_lbl).astype(np.uint8)) * 255
    fdk = np.ones((FINAL_DILATE_PX, FINAL_DILATE_PX), np.uint8)
    upper_mask = cv2.dilate(upper_mask, fdk, iterations=1)
    lower_mask = cv2.dilate(lower_mask, fdk, iterations=1)

    def find_spine(mask, eyes, fins):
        eyes_in = [e["centroid_canvas"] for e in eyes if mask[int(e["centroid_canvas"][1]), int(e["centroid_canvas"][0])] > 0]
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

    u_head, u_tail = find_spine(upper_mask, eye_atoms, fin_pos)
    l_head, l_tail = find_spine(lower_mask, eye_atoms, fin_pos)

    # Assign eyes to upper/lower by spatial distance to mask centroids
    # (mask-inside check fails because eyes are in negative-space areas of body)
    upper_ys, upper_xs = np.where(upper_mask > 0)
    lower_ys, lower_xs = np.where(lower_mask > 0)
    upper_cy = float(upper_ys.mean()) if len(upper_ys) else 0
    lower_cy = float(lower_ys.mean()) if len(lower_ys) else CANVAS
    upper_eyes = []
    lower_eyes = []
    for e in eye_atoms:
        ey = e["centroid_canvas"][1]
        if abs(ey - upper_cy) < abs(ey - lower_cy):
            upper_eyes.append(e)
        else:
            lower_eyes.append(e)

    return ({"mask": upper_mask, "head": u_head, "tail": u_tail, "eyes": upper_eyes},
            {"mask": lower_mask, "head": l_head, "tail": l_tail, "eyes": lower_eyes})


def compute_remap_field(head: tuple, tail: tuple, t_phase: float):
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


def main():
    atoms = load_atoms()
    base = load_base_jpg()
    base_rgb = np.asarray(base, dtype=np.uint8)
    print(f"Loaded {len(atoms)} atoms")

    print(f"Segmenting (CLOSE_KERNEL={CLOSE_KERNEL_PX}, DILATE={FINAL_DILATE_PX})...")
    upper, lower = segment_two_salmon(atoms)
    print(f"Upper: mask {(upper['mask']>0).sum()} px, eyes={len(upper['eyes'])}")
    print(f"Lower: mask {(lower['mask']>0).sum()} px, eyes={len(lower['eyes'])}")

    # Inpaint base
    combined_mask = np.maximum(upper["mask"], lower["mask"])
    # Also inpaint eye regions so when we composite eye pulses they don't double up
    for e in upper["eyes"] + lower["eyes"]:
        combined_mask = np.maximum(combined_mask, e["mask"])
    print("Inpainting...")
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(combined_mask, kernel, iterations=1)
    bgr = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2BGR)
    inpainted_bgr = cv2.inpaint(bgr, dilated, inpaintRadius=15, flags=cv2.INPAINT_TELEA)
    inpainted = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    inpainted_img = Image.fromarray(inpainted, "RGB")

    upper_rgba = np.dstack([base_rgb, upper["mask"]])
    lower_rgba = np.dstack([base_rgb, lower["mask"]])

    # Confine masks
    L_upper = math.hypot(upper["head"][0] - upper["tail"][0], upper["head"][1] - upper["tail"][1])
    L_lower = math.hypot(lower["head"][0] - lower["tail"][0], lower["head"][1] - lower["tail"][1])
    max_sway = int(WAVE_AMPLITUDE_FRAC * max(L_upper, L_lower) * 1.5)
    cf_kernel = np.ones((max_sway*2, max_sway*2), np.uint8)
    upper_confine = cv2.dilate(upper["mask"], cf_kernel, iterations=1)
    lower_confine = cv2.dilate(lower["mask"], cf_kernel, iterations=1)

    # Build eye sprites (cropped + alpha = atom mask)
    eye_sprites = []
    for e in upper["eyes"] + lower["eyes"]:
        bx, by, bw, bh = e["bbox"]
        # Add padding around bbox
        pad = 20
        x0 = max(0, int(bx) - pad)
        y0 = max(0, int(by) - pad)
        x1 = min(CANVAS, int(bx + bw) + pad)
        y1 = min(CANVAS, int(by + bh) + pad)
        cropped_rgba = np.dstack([base_rgb, e["mask"]])[y0:y1, x0:x1]
        eye_sprites.append({
            "sprite": cropped_rgba,
            "center": e["centroid_canvas"],
            "bbox_origin": (x0, y0),
            "original_size": (x1 - x0, y1 - y0),
        })
    print(f"Eye sprites: {len(eye_sprites)}")

    out_dir = INTERNAL / "salmon_in_place_v005"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = INTERNAL / "salmon_in_place_v005.mp4"
    inpainted_img.save(out_dir / "_inpainted_base.png")

    # Mask diagnostic
    diag = base.copy().convert("RGBA")
    ov = Image.new("RGBA", diag.size, (0, 0, 0, 0))
    for color, half in [((255, 0, 0, 80), upper), ((0, 0, 255, 80), lower)]:
        m = Image.fromarray((half["mask"] > 0).astype(np.uint8) * 255, "L")
        clr = Image.new("RGBA", diag.size, color)
        ov = Image.alpha_composite(ov, Image.composite(clr, Image.new("RGBA", diag.size, (0, 0, 0, 0)), m))
    od = ImageDraw.Draw(ov)
    for e in upper["eyes"] + lower["eyes"]:
        cx, cy = e["centroid_canvas"]
        od.ellipse([cx-12, cy-12, cx+12, cy+12], outline=(255, 255, 0, 255), width=3)
    Image.alpha_composite(diag, ov).convert("RGB").save(out_dir / "_segments_diagnostic.png")

    stills = {0: "00_t000.png", N_FRAMES // 4: "01_t025.png",
              N_FRAMES // 2: "02_t050.png", 3*N_FRAMES // 4: "03_t075.png"}
    omega_total = CYCLES_PER_LOOP * 2 * math.pi
    omega_eye = EYE_PULSE_CYCLES * 2 * math.pi

    print(f"Rendering {N_FRAMES} frames...")
    for i in range(N_FRAMES):
        t_norm = i / N_FRAMES
        t_u = t_norm * omega_total
        t_l = t_u + math.pi
        u_mx, u_my = compute_remap_field(upper["head"], upper["tail"], t_u)
        l_mx, l_my = compute_remap_field(lower["head"], lower["tail"], t_l)
        u_warped = cv2.remap(upper_rgba, u_mx, u_my,
                             interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
        l_warped = cv2.remap(lower_rgba, l_mx, l_my,
                             interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
        u_warped[..., 3] = np.minimum(u_warped[..., 3], upper_confine)
        l_warped[..., 3] = np.minimum(l_warped[..., 3], lower_confine)

        canvas = inpainted_img.copy().convert("RGBA")
        canvas.alpha_composite(Image.fromarray(u_warped, "RGBA"))
        canvas.alpha_composite(Image.fromarray(l_warped, "RGBA"))

        # Eye pulse overlay
        eye_scale = 1.0 + EYE_PULSE_AMPLITUDE / 2 * math.sin(t_norm * omega_eye)
        for es in eye_sprites:
            sprite = es["sprite"]
            sh, sw = sprite.shape[:2]
            if abs(eye_scale - 1.0) > 0.001:
                new_w = max(1, int(round(sw * eye_scale)))
                new_h = max(1, int(round(sh * eye_scale)))
                sprite_resized = cv2.resize(sprite, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            else:
                sprite_resized = sprite
                new_w, new_h = sw, sh
            sprite_pil = Image.fromarray(sprite_resized, "RGBA")
            # Paste centered at original bbox center
            cx, cy = es["center"]
            paste_x = int(cx - new_w // 2)
            paste_y = int(cy - new_h // 2)
            canvas.alpha_composite(sprite_pil, (paste_x, paste_y))

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
        print(f"  _inpainted_base.png, _segments_diagnostic.png")
    else:
        print(f"\nFFMPEG ERROR: {result.stderr[-300:]}")


if __name__ == "__main__":
    main()
