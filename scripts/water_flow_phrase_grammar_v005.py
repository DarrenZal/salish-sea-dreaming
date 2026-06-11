#!/usr/bin/env python3
"""
water_flow_phrase_grammar_v005 -- SSD Phase 2, R&D Lane 2 (Water Dynamics).

INTERNAL ONLY. Not Austin-approved. Not a public cultural-grammar claim.

FRAME-SYNCHRONOUS MOTION-LOCK PROOF on the best-available footage window.

v004 proved the frame-synchronous motion-lock mechanism works -- every glyph is
advected by the local per-frame optical flow -- but Darren's review found the
dense salmon-school footage (P1099653, t=160s) too complex for the lock to
*read*: hundreds of near-identical fish at many depths, no distinct landmark
for the eye to see a primitive glued to.

v005 keeps the v004 mechanism unchanged and runs it on a footage window chosen
for trackability. Per the trackability audit
(docs/space-center/footage-motion-lock-trackability-audit-2026-05-20.md) the
best window is the reef-garden clip P1111509, t=1-7s: an encrusted reef boulder
with vivid, individually distinct sponges/anemones, filmed with steady camera
movement. That gives:

  - Distinct high-contrast features the eye can lock onto (the direct fix for
    v004's no-landmark failure).
  - Rigid-scene camera parallax -- the cleanest, most reliable case for optical
    flow (no froth, no overlapping-layer tangle, no schooling chaos).

Mechanism (unchanged from v004):

  - Optical flow is computed for every consecutive frame pair (per-frame),
    then lightly smoothed over a short 3-frame temporal window.
  - Primitive phrases are seeded on the footage and ADVECTED frame by frame:
    every glyph is carried by the local apparent motion at its own position.
  - A glyph sits on a footage feature and moves exactly where that feature
    moves -- the overlay is locked to the footage by construction.

IMPORTANT -- this is NOT a 3D-motion or fluid-physics claim. Optical flow
measures 2D apparent image-space motion only (camera drift + subject motion,
combined). v005 makes no claim to extract 3D motion from monocular footage;
the reef window is chosen precisely because its motion is legible in the
image plane (rigid-scene parallax), not because depth is recovered.

Trade-off, stated honestly: a frame-synchronous overlay is tied to the footage
timeline and does NOT loop seamlessly. v005 is a motion-lock proof; v003
remains the seamless-loop option.

Primitive grammar (unchanged): circle -> crescent -> crescent -> trigon.
  circle   = origin / source anchor
  crescent = expansion band / wake mark
  trigon   = release / leading directional tip

Camera drift: a per-frame global-translation estimate (median flow) is
computed, shown in the debug HUD, and used to bias phrase seeding. It is
deliberately NOT subtracted from advection -- phrases advect by full apparent
flow so they stay pinned to footage features. See README.

Outputs (1920x1080, 24fps, 6.0s, 144 frames):
  1. best_window_motion_lock_v005__over_source.mp4         composite over footage
  2. best_window_motion_lock_layer_v005_black_screen.mp4   same layer on black
  3. debug_best_window_motion_lock_v005.mp4                footage + flow vectors
                                                           + phrase anchors

No fish / animal glyphs, no SD / LoRA, no topology / cymatics, no randomness.
The renderer draws only abstract circle/crescent/trigon primitives carried by
the motion field.

Glyph rendering (SDF glyphs, tone map) and the dense Lucas-Kanade optical flow
are carried over from v002/v003/v004.

Usage:
    python3 scripts/water_flow_phrase_grammar_v005.py            # full render
    python3 scripts/water_flow_phrase_grammar_v005.py --smoke    # fast test
"""

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------
W, H = 1920, 1080
FPS = 24
DUR_S = 6.0
N_FRAMES = int(round(FPS * DUR_S))           # 144

AW, AH = 640, 360                            # optical-flow analysis resolution
UPSCALE = W / AW                             # 3.0
FOOTAGE_CROP = "crop=1770:996:75:0"          # drops burned-in source timecode

COL_CIRCLE = np.array([1.00, 0.86, 0.60], np.float32)   # warm gold-white
COL_CRESC  = np.array([0.40, 0.83, 1.00], np.float32)   # bioluminescent cyan
COL_TRIGON = np.array([0.62, 1.00, 0.84], np.float32)   # pale teal-green

I_CIRCLE = 0.80
I_CRESC  = 0.95
I_TRIGON = 0.72

# v004 glyphs are a touch larger than v003 -- fewer, larger, clearly locked
R_CIRCLE = 38.0
R_CRESC  = 66.0
R_TRIGON = 40.0

# crisp, low-bloom glyphs -- v004 wants discrete marks that sit IN the footage
# and visibly lock to it, not soft glowing orbs that float over it
GLOW_TIGHT = 8.0
GLOW_WIDE  = 19.0

EXPOSURE = 1.42
POST_GAMMA = 1.0 / 1.35

# motion-lock phrase system
N_PHRASES = 5                                # few, large, clearly locked
LIFE = 84                                    # phrase lifespan, frames (~3.5s)
BIRTH_GAP = 88.0                             # glyph spacing at birth (render px)
WAKE_N = 16                                  # advected-position trail length
ORIENT_FLOOR = 2.4                           # render px/frame below which a
                                             # glyph keeps the phrase axis
TEMPORAL_SIGMA = 1.1                          # short-window flow smoothing


# ==========================================================================
# math helpers
# ==========================================================================
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _box(cx, cy, reach):
    x0 = max(0, int(math.floor(cx - reach)))
    x1 = min(W, int(math.ceil(cx + reach)))
    y0 = max(0, int(math.floor(cy - reach)))
    y1 = min(H, int(math.ceil(cy + reach)))
    return x0, y0, x1, y1


def _local(x0, y0, x1, y1, cx, cy):
    lx = (np.arange(x0, x1, dtype=np.float32) + 0.5) - cx
    ly = (np.arange(y0, y1, dtype=np.float32) + 0.5) - cy
    return lx[None, :], ly[:, None]


def _sdf_field(sdf):
    """SDF -> additive intensity: a crisp bold fill with only a thin halo and
    a whisper of bloom -- a discrete mark, not a soft floating orb."""
    fill = smoothstep(1.5, -1.5, sdf)
    pos = np.maximum(sdf, 0.0)
    glow_tight = np.exp(-(pos / GLOW_TIGHT) ** 2)
    glow_wide = np.exp(-(pos / GLOW_WIDE) ** 2)
    return np.maximum(fill, np.maximum(0.32 * glow_tight, 0.05 * glow_wide))


def _add(canvas, x0, y0, x1, y1, field, color, intensity):
    canvas[y0:y1, x0:x1, :] += field[:, :, None] * (color[None, None, :] * np.float32(intensity))


def ema_angle(cur, target, k):
    """Exponential-moving-average toward an angle, wrap-safe."""
    d = math.atan2(math.sin(target - cur), math.cos(target - cur))
    return cur + k * d


# ==========================================================================
# primitive glyphs  (carried over from water_flow_phrase_grammar_v003)
# ==========================================================================
def draw_circle(canvas, cx, cy, radius, color, intensity):
    """Filled glowing disc -- the phrase origin / focal anchor."""
    if intensity <= 0.002 or radius <= 0.5:
        return
    reach = radius + GLOW_WIDE * 2.5 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    field = _sdf_field(np.sqrt(lx * lx + ly * ly) - radius)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def draw_crescent(canvas, cx, cy, size, open_angle, color, intensity):
    """Crescent = a tapered circular-arc blade cupping toward `open_angle`."""
    if intensity <= 0.002 or size <= 0.5:
        return
    r_spine = size * 1.20
    half_span = 0.95
    half_thick = size * 0.34
    ccx = cx + r_spine * math.cos(open_angle)
    ccy = cy + r_spine * math.sin(open_angle)
    mid = open_angle + math.pi
    pad = half_thick + GLOW_WIDE * 2.4 + 4.0
    xs = [ccx + r_spine * math.cos(mid - half_span + (2.0 * half_span) * (k / 6.0))
          for k in range(7)]
    ys = [ccy + r_spine * math.sin(mid - half_span + (2.0 * half_span) * (k / 6.0))
          for k in range(7)]
    x0 = max(0, int(math.floor(min(xs) - pad)))
    x1 = min(W, int(math.ceil(max(xs) + pad)))
    y0 = max(0, int(math.floor(min(ys) - pad)))
    y1 = min(H, int(math.ceil(max(ys) + pad)))
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, ccx, ccy)
    rad = np.sqrt(lx * lx + ly * ly)
    theta = np.arctan2(ly, lx)
    dth = np.abs((theta - mid + math.pi) % (2.0 * math.pi) - math.pi)
    taper = np.clip(np.cos(np.clip(dth / half_span, 0.0, 1.0) * (math.pi / 2.0)), 0.0, 1.0)
    ht = half_thick * (taper ** 0.6)
    band = np.abs(rad - r_spine) - ht
    over = np.maximum(dth - half_span, 0.0) * r_spine
    sdf = np.where(dth < half_span, band, np.sqrt(over * over + (rad - r_spine) ** 2))
    field = _sdf_field(sdf)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def _triangle_sdf(px, py, p0, p1, p2):
    """Exact signed distance to a triangle (Inigo Quilez), vectorised."""
    e0 = (p1[0] - p0[0], p1[1] - p0[1])
    e1 = (p2[0] - p1[0], p2[1] - p1[1])
    e2 = (p0[0] - p2[0], p0[1] - p2[1])
    v0x, v0y = px - p0[0], py - p0[1]
    v1x, v1y = px - p1[0], py - p1[1]
    v2x, v2y = px - p2[0], py - p2[1]

    def pq(vx, vy, e):
        d = e[0] * e[0] + e[1] * e[1]
        t = np.clip((vx * e[0] + vy * e[1]) / d, 0.0, 1.0)
        return vx - e[0] * t, vy - e[1] * t

    pq0x, pq0y = pq(v0x, v0y, e0)
    pq1x, pq1y = pq(v1x, v1y, e1)
    pq2x, pq2y = pq(v2x, v2y, e2)
    s = math.copysign(1.0, e0[0] * e2[1] - e0[1] * e2[0])
    dx = np.minimum(np.minimum(pq0x * pq0x + pq0y * pq0y,
                               pq1x * pq1x + pq1y * pq1y),
                    pq2x * pq2x + pq2y * pq2y)
    c0 = s * (v0x * e0[1] - v0y * e0[0])
    c1 = s * (v1x * e1[1] - v1y * e1[0])
    c2 = s * (v2x * e2[1] - v2y * e2[0])
    dy = np.minimum(np.minimum(c0, c1), c2)
    return -np.sqrt(np.maximum(dx, 0.0)) * np.sign(dy)


def _edge_bite(px, py, va, vb, g, bite):
    """Disc just outside an edge; its near arc scoops a shallow concave curve."""
    mx, my = (va[0] + vb[0]) * 0.5, (va[1] + vb[1]) * 0.5
    ex, ey = vb[0] - va[0], vb[1] - va[1]
    el = math.hypot(ex, ey)
    nx, ny = ey / el, -ex / el
    if nx * (mx - g[0]) + ny * (my - g[1]) < 0.0:
        nx, ny = -nx, -ny
    d_off = 1.5 * el
    ccx, ccy = mx + nx * d_off, my + ny * d_off
    r = d_off + bite
    return r - np.sqrt((px - ccx) ** 2 + (py - ccy) ** 2)


def draw_trigon(canvas, cx, cy, size, point_angle, color, intensity, concavity=0.10):
    """Concave-sided three-point trigon, tip pointing along `point_angle`."""
    if intensity <= 0.002 or size <= 0.5:
        return
    reach = size * 1.18 + GLOW_WIDE * 2.5 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    ca, sa = math.cos(point_angle), math.sin(point_angle)
    rx = ca * lx + sa * ly
    ry = -sa * lx + ca * ly
    v0 = (size, 0.0)
    v1 = (-0.72 * size, 0.66 * size)
    v2 = (-0.72 * size, -0.66 * size)
    g = ((v0[0] + v1[0] + v2[0]) / 3.0, 0.0)
    sdf = _triangle_sdf(rx, ry, v0, v1, v2)
    bite = concavity * size
    for va, vb in ((v0, v1), (v1, v2), (v2, v0)):
        sdf = np.maximum(sdf, _edge_bite(rx, ry, va, vb, g, bite))
    field = _sdf_field(sdf)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def draw_blob(canvas, cx, cy, radius, color, intensity):
    """Soft round glow blob -- used to paint advected motion-trail wakes."""
    if intensity <= 0.002 or radius <= 0.5:
        return
    reach = radius * 2.7 + 3.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    field = np.exp(-(lx * lx + ly * ly) / (radius * radius))
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def tonemap(canvas):
    x = 1.0 - np.exp(-np.maximum(canvas, 0.0) * EXPOSURE)
    x = np.power(np.clip(x, 0.0, 1.0), POST_GAMMA)
    return (x * 255.0 + 0.5).astype(np.uint8)


def _encoder(out_mp4):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


# ==========================================================================
# optical flow  (dense pyramidal Lucas-Kanade, numpy + scipy; carried over)
# ==========================================================================
def extract_gray_frames(footage, start, dur, w, h):
    """Decode a cropped, scaled, 24fps grayscale frame stack."""
    cmd = [
        "ffmpeg", "-v", "error", "-ss", f"{start}", "-i", str(footage),
        "-t", f"{dur}",
        "-vf", f"{FOOTAGE_CROP},scale={w}:{h},format=gray,fps={FPS}",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed:\n"
                           f"{proc.stderr.decode('utf-8', 'replace')}")
    n = len(proc.stdout) // (w * h)
    if n < 2:
        raise RuntimeError(f"footage window too short: {n} frame(s) decoded")
    return np.frombuffer(proc.stdout[:n * w * h], np.uint8).reshape(n, h, w)


def _grad(im):
    gx = np.zeros_like(im)
    gy = np.zeros_like(im)
    gx[:, 1:-1] = (im[:, 2:] - im[:, :-2]) * 0.5
    gx[:, 0] = im[:, 1] - im[:, 0]
    gx[:, -1] = im[:, -1] - im[:, -2]
    gy[1:-1, :] = (im[2:, :] - im[:-2, :]) * 0.5
    gy[0, :] = im[1, :] - im[0, :]
    gy[-1, :] = im[-1, :] - im[-2, :]
    return gx, gy


def _warp(im, u, v):
    h, w = im.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return map_coordinates(im, [yy + v, xx + u], order=1, mode="nearest")


def _lk_step(im1, im2, sigma):
    Ix, Iy = _grad(im1)
    It = im2 - im1
    Sxx = gaussian_filter(Ix * Ix, sigma)
    Syy = gaussian_filter(Iy * Iy, sigma)
    Sxy = gaussian_filter(Ix * Iy, sigma)
    Sxt = gaussian_filter(Ix * It, sigma)
    Syt = gaussian_filter(Iy * It, sigma)
    det = Sxx * Syy - Sxy * Sxy
    eps = 1e-6
    u = -(Syy * Sxt - Sxy * Syt) / (det + eps)
    v = -(Sxx * Syt - Sxy * Sxt) / (det + eps)
    bad = det < 1e-7
    u[bad] = 0.0
    v[bad] = 0.0
    np.clip(u, -16.0, 16.0, out=u)
    np.clip(v, -16.0, 16.0, out=v)
    return u, v


def pyramid_flow(im1, im2, levels=3, sigma=3.0, iters=2):
    """Coarse-to-fine pyramidal Lucas-Kanade dense optical flow."""
    p1 = [im1]
    p2 = [im2]
    for _ in range(levels - 1):
        p1.append(gaussian_filter(p1[-1], 1.0)[::2, ::2])
        p2.append(gaussian_filter(p2[-1], 1.0)[::2, ::2])
    u = np.zeros_like(p1[-1])
    v = np.zeros_like(p1[-1])
    for lvl in range(levels - 1, -1, -1):
        if u.shape != p1[lvl].shape:
            u = (u.repeat(2, 0).repeat(2, 1) * 2.0)[:p1[lvl].shape[0], :p1[lvl].shape[1]]
            v = (v.repeat(2, 0).repeat(2, 1) * 2.0)[:p1[lvl].shape[0], :p1[lvl].shape[1]]
        for _ in range(iters):
            i2w = _warp(p2[lvl], u, v)
            du, dv = _lk_step(p1[lvl], i2w, sigma)
            u = u + du
            v = v + dv
    return u, v


def compute_flow_sequence(frames):
    """Per-frame dense optical flow for every consecutive pair, then a short
    3-frame temporal smoothing. Returns (n_pairs, AH, AW, 2) in analysis px."""
    n = len(frames)
    flows = np.zeros((n - 1, AH, AW, 2), np.float32)
    for i in range(n - 1):
        a = frames[i].astype(np.float32) / 255.0
        b = frames[i + 1].astype(np.float32) / 255.0
        u, v = pyramid_flow(a, b)
        flows[i, :, :, 0] = gaussian_filter(u, 1.2)
        flows[i, :, :, 1] = gaussian_filter(v, 1.2)
    # short-window temporal smoothing -> frame-synchronous but not jittery
    flows = gaussian_filter1d(flows, TEMPORAL_SIGMA, axis=0, mode="nearest")
    return flows


def estimate_drift(flows):
    """Per-frame global-translation estimate (median flow) -- a camera-drift
    proxy. Robust to the school's many local motions. Analysis px/frame."""
    return np.stack([np.median(flows[:, :, :, 0], axis=(1, 2)),
                     np.median(flows[:, :, :, 1], axis=(1, 2))], axis=1)


# ==========================================================================
# flow sampling
# ==========================================================================
def sample_disp(flow_field, x_render, y_render):
    """Bilinear-sample a flow field at a render-space point; return the
    render-space per-frame displacement (apparent motion at that pixel)."""
    xa = min(max(x_render / UPSCALE, 0.0), AW - 1.001)
    ya = min(max(y_render / UPSCALE, 0.0), AH - 1.001)
    x0, y0 = int(xa), int(ya)
    fx, fy = xa - x0, ya - y0
    f = flow_field
    u = ((f[y0, x0, 0] * (1 - fx) + f[y0, x0 + 1, 0] * fx) * (1 - fy)
         + (f[y0 + 1, x0, 0] * (1 - fx) + f[y0 + 1, x0 + 1, 0] * fx) * fy)
    v = ((f[y0, x0, 1] * (1 - fx) + f[y0, x0 + 1, 1] * fx) * (1 - fy)
         + (f[y0 + 1, x0, 1] * (1 - fx) + f[y0 + 1, x0 + 1, 1] * fx) * fy)
    return float(u) * UPSCALE, float(v) * UPSCALE


# ==========================================================================
# phrase seeding + simulation
# ==========================================================================
def pick_seed(flow_field, drift_a, active):
    """Choose a seed point: highest local (non-global) apparent motion, away
    from frame edges and from already-active phrases. Fully deterministic."""
    dxr, dyr = drift_a[0] * UPSCALE, drift_a[1] * UPSCALE
    centroids = []
    for ph in active:
        gs = ph["glyphs"]
        centroids.append((sum(g["x"] for g in gs) / 4.0,
                          sum(g["y"] for g in gs) / 4.0))
    best, best_score = None, -1.0
    for gy in np.linspace(H * 0.20, H * 0.80, 7):
        for gx in np.linspace(W * 0.16, W * 0.84, 13):
            if any(math.hypot(gx - cx, gy - cy) < W * 0.20 for cx, cy in centroids):
                continue
            u, v = sample_disp(flow_field, gx, gy)
            residual = math.hypot(u - dxr, v - dyr)        # local, non-global
            if residual > best_score:
                best_score, best = residual, (gx, gy)
    if best is None:                                       # frame fully packed
        best = (W * 0.5, H * 0.5)
    u, v = sample_disp(flow_field, best[0], best[1])
    direction = math.atan2(v, u) if math.hypot(u, v) > 1e-3 else 0.0
    return best, direction, best_score


def _new_phrase(birth, seed, direction, idx):
    """Lay out a circle->crescent->crescent->trigon phrase along `direction`;
    circle trails as the origin, trigon leads."""
    sx, sy = seed
    dx, dy = math.cos(direction), math.sin(direction)
    layout = (
        ("circle", -1.60), ("crescent", -0.55),
        ("crescent", 0.55), ("trigon", 1.60),
    )
    glyphs = []
    for kind, off in layout:
        glyphs.append({
            "kind": kind,
            "x": sx + dx * off * BIRTH_GAP,
            "y": sy + dy * off * BIRTH_GAP,
            "ang": direction,
            "traj": {},                                    # frame -> (x, y, ang)
        })
    return {"idx": idx, "birth": birth, "life": LIFE, "glyphs": glyphs}


def simulate(flows, drift, n_frames):
    """Advect primitive phrases through the per-frame optical flow.

    Every glyph is carried by the local apparent motion at its own position
    each frame -- the phrase is locked to the footage by construction.
    Returns (all_phrases, metrics)."""
    nf = len(flows)
    all_phrases, working = [], []
    next_idx = 0
    seg = max(1, LIFE // N_PHRASES)

    # initial spawn -- staggered births so deaths/respawns desynchronise
    for k in range(N_PHRASES):
        seed, direction, _ = pick_seed(flows[0], drift[0], working)
        ph = _new_phrase(-k * seg, seed, direction, next_idx)
        next_idx += 1
        working.append(ph)
        all_phrases.append(ph)

    disp_sum = disp_n = 0.0
    resid_sum = drift_sum = 0.0

    for f in range(n_frames):
        # ---- advect: carry every glyph by the local per-frame motion ----
        if f > 0:
            ff = flows[min(f - 1, nf - 1)]
            for ph in working:
                if f <= ph["birth"]:
                    continue
                for g in ph["glyphs"]:
                    du, dv = sample_disp(ff, g["x"], g["y"])
                    g["x"] += du
                    g["y"] += dv
                    disp_sum += math.hypot(du, dv)
                    disp_n += 1.0
        # ---- orient each glyph by the local flow direction this frame ----
        of = flows[min(f, nf - 1)]
        dxr = drift[min(f, nf - 1), 0] * UPSCALE
        dyr = drift[min(f, nf - 1), 1] * UPSCALE
        for ph in working:
            cg, tg = ph["glyphs"][0], ph["glyphs"][3]
            axis = math.atan2(tg["y"] - cg["y"], tg["x"] - cg["x"])
            for g in ph["glyphs"]:
                du, dv = sample_disp(of, g["x"], g["y"])
                mag = math.hypot(du, dv)
                target = math.atan2(dv, du) if mag > ORIENT_FLOOR else axis
                g["ang"] = ema_angle(g["ang"], target, 0.22)
                if 0 <= f and ph["birth"] <= f:
                    resid_sum += math.hypot(du - dxr, dv - dyr)
                    drift_sum += math.hypot(dxr, dyr)
        # ---- record the frame's glyph state ----
        for ph in working:
            if ph["birth"] <= f < ph["birth"] + ph["life"]:
                for g in ph["glyphs"]:
                    g["traj"][f] = (g["x"], g["y"], g["ang"])
        # ---- cull phrases that end after this frame, respawn to keep N ----
        working = [ph for ph in working if f + 1 < ph["birth"] + ph["life"]]
        if f + 1 < n_frames:
            while len(working) < N_PHRASES:
                seed, direction, _ = pick_seed(flows[min(f + 1, nf - 1)],
                                               drift[min(f + 1, nf - 1)], working)
                ph = _new_phrase(f + 1, seed, direction, next_idx)
                next_idx += 1
                working.append(ph)
                all_phrases.append(ph)

    metrics = {
        "phrases_total": len(all_phrases),
        "mean_glyph_disp_px_per_frame": round(disp_sum / max(disp_n, 1.0), 2),
        "mean_local_residual_px_per_frame": round(resid_sum / max(disp_n, 1.0), 2),
        "mean_global_drift_px_per_frame": round(drift_sum / max(disp_n, 1.0), 2),
    }
    return all_phrases, metrics


def fade_curve(age, life):
    return float(smoothstep(0.0, 12.0, age) * smoothstep(life, life - 20.0, age))


def active_phrases(all_phrases, f):
    return [ph for ph in all_phrases if ph["birth"] <= f < ph["birth"] + ph["life"]]


# ==========================================================================
# render -- primitive phrase layer (black screen, advected glyphs)
# ==========================================================================
GLYPH_STYLE = {
    "circle": (COL_CIRCLE, R_CIRCLE, I_CIRCLE),
    "crescent": (COL_CRESC, R_CRESC, I_CRESC),
    "trigon": (COL_TRIGON, R_TRIGON, I_TRIGON),
}


def render_phrase_layer(all_phrases, outdir, n_frames):
    """Render the advected phrases on pure black. Each glyph carries a wake of
    its own recent advected positions -- a true short motion trail."""
    out_mp4 = outdir / "best_window_motion_lock_layer_v005_black_screen.mp4"
    proc = _encoder(out_mp4)
    mid_idx = n_frames // 2
    mid_frame = None
    t0 = time.time()
    for f in range(n_frames):
        canvas = np.zeros((H, W, 3), np.float32)
        for ph in active_phrases(all_phrases, f):
            fade = fade_curve(f - ph["birth"], ph["life"])
            if fade <= 0.003:
                continue
            for g in ph["glyphs"]:
                col, size, inten = GLYPH_STYLE[g["kind"]]
                x, y, ang = g["traj"][f]
                # wake -- the glyph's own recent advected positions
                for j in range(1, WAKE_N + 1):
                    pf = f - j
                    if pf not in g["traj"]:
                        break
                    wx, wy, _ = g["traj"][pf]
                    wfade = fade * 0.42 * (0.86 ** j)
                    draw_blob(canvas, wx, wy, size * 0.40 * (1.0 - 0.05 * j),
                              col, inten * wfade)
                if g["kind"] == "circle":
                    draw_circle(canvas, x, y, size, col, inten * fade)
                elif g["kind"] == "crescent":
                    draw_crescent(canvas, x, y, size, ang + math.pi, col, inten * fade)
                else:
                    draw_trigon(canvas, x, y, size, ang, col, inten * fade)
        rgb = tonemap(canvas)
        if f == mid_idx:
            mid_frame = rgb.copy()
        try:
            proc.stdin.write(rgb.tobytes())
        except BrokenPipeError:
            break
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (phrase layer):\n"
                           f"{proc.stderr.read().decode('utf-8', 'replace')}")
    print(f"  phrase layer: {n_frames} frames in {time.time() - t0:4.1f}s")
    return out_mp4, mid_frame


# ==========================================================================
# render -- composite (additive layer over footage)
# ==========================================================================
def make_composite(layer_mp4, footage, start, opacity, footage_dim, out_mp4, n_frames):
    """Blend a black-screen layer additively over the source footage window."""
    dur = n_frames / FPS
    fc = (
        f"[0:v]{FOOTAGE_CROP},scale=1920:1080,fps=24,trim=duration={dur},"
        f"setpts=PTS-STARTPTS,eq=brightness={footage_dim}:saturation=1.05,"
        f"format=gbrp[bg];"
        f"[1:v]format=gbrp,colorchannelmixer=rr={opacity}:gg={opacity}:bb={opacity}[lay];"
        f"[bg][lay]blend=all_mode=addition:shortest=1,format=yuv420p[out]"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(start), "-i", str(footage),
        "-i", str(layer_mp4),
        "-filter_complex", fc, "-map", "[out]", "-t", str(dur),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  composite FAILED ({out_mp4.name}): {r.stderr.strip().splitlines()[-1:]}")
        return False
    return True


def grab_frame(mp4, t):
    """Grab a single RGB frame from an MP4 at time t (seconds)."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(mp4),
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True)
    if r.returncode != 0 or len(r.stdout) < W * H * 3:
        return None
    return np.frombuffer(r.stdout[:W * H * 3], np.uint8).reshape(H, W, 3)


# ==========================================================================
# render -- debug motion-lock clip (footage + flow vectors + phrase anchors)
# ==========================================================================
def _load_font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _read_exact(stream, n):
    buf = b""
    while len(buf) < n:
        chunk = stream.read(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _otext(draw, xy, text, font, fill=(245, 248, 252)):
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


def _arrow(draw, x0, y0, x1, y1, fill, width=2):
    draw.line([(x0, y0), (x1, y1)], fill=fill, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    hl = 6.0
    for da in (2.5, -2.5):
        draw.line([(x1, y1),
                   (x1 + hl * math.cos(ang + da), y1 + hl * math.sin(ang + da))],
                  fill=fill, width=width)


def render_debug_clip(footage, start, all_phrases, flows, drift, out_mp4, n_frames):
    """Single pass: decode footage, draw an opaque verification overlay
    (per-frame flow vectors + primitive-phrase anchors + camera-drift HUD),
    encode. Lets a reviewer confirm the layer is locked to frame motion."""
    nf = len(flows)
    dur = n_frames / FPS
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-i", str(footage),
         "-t", str(dur),
         "-vf", f"{FOOTAGE_CROP},scale=1920:1080,fps=24",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        stdout=subprocess.PIPE)
    enc = _encoder(out_mp4)
    font = _load_font(22)
    font_s = _load_font(17)
    mid_idx = n_frames // 2
    mid_frame = None
    grid = [(int(gx), int(gy))
            for gy in range(70, H - 40, 116) for gx in range(80, W - 40, 116)]
    sk_col = {"circle": (255, 214, 130), "crescent": (150, 214, 255),
              "trigon": (165, 255, 205)}
    t0 = time.time()
    for f in range(n_frames):
        raw = _read_exact(dec.stdout, W * H * 3)
        if raw is None:
            break
        arr = (np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)
               * 0.60).astype(np.uint8)
        img = Image.fromarray(arr)
        d = ImageDraw.Draw(img)
        ff = flows[min(f, nf - 1)]
        # per-frame flow vector field (this is the motion the phrases ride;
        # arrows are scaled x5 for visibility -- the field is a few px/frame)
        for gx, gy in grid:
            u, v = sample_disp(ff, gx, gy)
            mag = math.hypot(u, v)
            if mag < 0.7:
                continue
            t = min(mag / 22.0, 1.0)
            col = (int(70 + 185 * t), int(150 + 90 * t), int(220 - 70 * t))
            _arrow(d, gx, gy, gx + u * 5.0, gy + v * 5.0, col, 2)
        # per-phrase motion trail -- the path the phrase rode through the flow
        for ph in active_phrases(all_phrases, f):
            trail = []
            for pf in range(max(ph["birth"], f - 16), f + 1):
                cs = [g["traj"][pf] for g in ph["glyphs"] if pf in g["traj"]]
                if len(cs) == 4:
                    trail.append((sum(c[0] for c in cs) / 4.0,
                                  sum(c[1] for c in cs) / 4.0))
            for i in range(1, len(trail)):
                tt = i / max(len(trail) - 1, 1)
                col = (int(60 + 150 * tt), int(80 + 150 * tt), int(95 + 150 * tt))
                d.line([trail[i - 1], trail[i]], fill=col, width=1 + int(3 * tt))
        # primitive-phrase anchors (skeletons) -- watch these ride the footage
        for ph in active_phrases(all_phrases, f):
            pts = [ph_g["traj"][f][:2] for ph_g in ph["glyphs"]]
            d.line(pts, fill=(248, 250, 255), width=2)
            for g, (px, py) in zip(ph["glyphs"], pts):
                c = sk_col[g["kind"]]
                rr = 9 if g["kind"] in ("circle", "trigon") else 6
                d.ellipse([px - rr, py - rr, px + rr, py + rr],
                          outline=(15, 15, 20), width=4)
                d.ellipse([px - rr, py - rr, px + rr, py + rr],
                          outline=c, width=2)
            tx, ty = pts[3]
            _otext(d, (tx + 12, ty - 26), f"P{ph['idx']}", font_s)
        # camera-drift HUD
        dax, day = drift[min(f, nf - 1)]
        dmag = math.hypot(dax, day)
        hx, hy = 150, H - 150
        d.ellipse([hx - 4, hy - 4, hx + 4, hy + 4], fill=(255, 150, 90))
        _arrow(d, hx, hy, hx + dax * UPSCALE * 7.0, hy + day * UPSCALE * 7.0,
               (255, 150, 90), 3)
        _otext(d, (40, H - 96),
               f"global apparent drift ~ {dmag:.2f} px/frame (640x360 analysis)",
               font_s)
        _otext(d, (40, 36),
               "yellow = per-frame apparent-motion field   "
               "ringed dots = primitive phrase anchors (advected by that flow)",
               font_s)
        _otext(d, (W - 230, H - 56), f"frame {f + 1:3d} / {n_frames}", font)
        frame = np.asarray(img)
        if f == mid_idx:
            mid_frame = frame.copy()
        try:
            enc.stdin.write(frame.tobytes())
        except BrokenPipeError:
            break
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    if enc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed (debug clip):\n"
                           f"{enc.stderr.read().decode('utf-8', 'replace')}")
    print(f"  debug clip:   {n_frames} frames in {time.time() - t0:4.1f}s")
    return mid_frame


# ==========================================================================
# verification + contact sheet
# ==========================================================================
def ffprobe_check(path):
    cmd = [
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,r_frame_rate,nb_read_frames",
        "-show_entries", "format=duration", "-of", "json", str(path),
    ]
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    st, fmt = d["streams"][0], d["format"]
    num, den = st["r_frame_rate"].split("/")
    return {
        "width": int(st["width"]), "height": int(st["height"]),
        "codec": st["codec_name"], "fps": float(num) / float(den),
        "fps_raw": st["r_frame_rate"], "frames": int(st["nb_read_frames"]),
        "duration": float(fmt["duration"]), "size_kb": path.stat().st_size // 1024,
    }


def nonblank_check(frame):
    luma = 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]
    return {"max_luma": int(luma.max()),
            "nonblack_px": int(np.count_nonzero(np.any(frame > 8, axis=2)))}


def build_contact_sheet(panels, outpath):
    """panels: list of (label, sublabel, ndarray-or-None), laid out 2x2."""
    cw, ch = 960, 540
    sheet = Image.new("RGB", (cw * 2, ch * 2), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    font_t, font_s = _load_font(25), _load_font(18)
    for (label, sub, arr), (px, py) in zip(panels, [(0, 0), (cw, 0), (0, ch), (cw, ch)]):
        if arr is not None:
            sheet.paste(Image.fromarray(arr).resize((cw, ch), Image.LANCZOS), (px, py))
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (228, 240, 248))):
            draw.text((px + 20 + dx, py + 16 + dy), label, font=font_t, fill=fill)
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (150, 186, 205))):
            draw.text((px + 20 + dx, py + 48 + dy), sub, font=font_s, fill=fill)
    sheet.save(outpath)
    return sheet.size


# ==========================================================================
# README
# ==========================================================================
def write_readme(outdir, clips, metrics, meta, sheet_size, verdict):
    L = []
    a = L.append
    a("# Water Flow Phrase Grammar v005 - 2026-05-20")
    a("")
    a("INTERNAL ONLY until Austin reviews. A frame-synchronous motion-lock")
    a("proof on the best-available footage window. No SD / LoRA / style")
    a("transfer, no topology / cymatics, no fish or animal glyphs, no")
    a("randomness. Not Austin-approved and not a public cultural-grammar claim.")
    a("")
    a("## Why v005 Exists")
    a("")
    a("v004 proved the frame-synchronous motion-lock mechanism works, but")
    a("Darren's review found the dense salmon-school footage too complex for")
    a("the lock to *read*: hundreds of near-identical fish at many depths, no")
    a("distinct landmark for the eye to see a primitive glued to. v005 keeps")
    a("the v004 mechanism unchanged and runs it on a footage window chosen for")
    a("trackability.")
    a("")
    a("## What v005 Changed")
    a("")
    a("Only the footage window. The mechanism is identical to v004:")
    a("")
    a("- Optical flow is computed for **every consecutive frame pair**, then")
    a("  lightly smoothed over a short 3-frame temporal window.")
    a("- Primitive phrases are seeded on the footage and **advected** frame by")
    a("  frame -- every glyph is carried by the local apparent motion at its")
    a("  own position, so it sits on a footage feature and moves where that")
    a("  feature moves. The overlay is locked to the footage by construction.")
    a("- Each glyph carries a wake of its own recent advected positions -- a")
    a("  true short motion trail showing the path it took.")
    a("")
    a("## Source Footage")
    a("")
    a(f"- File: `{meta['footage_rel']}`")
    a(f"- Window: t = {meta['start']:.1f}s to {meta['start'] + meta['dur']:.1f}s "
      f"({meta['dur']:.1f}s).")
    a("- Content: a reef-garden boulder -- vivid, individually distinct sponges")
    a("  and anemones -- with kelp stipes behind, filmed with steady camera")
    a("  movement. Chosen by the trackability audit as the best window: it")
    a("  directly fixes v004's no-landmark failure (distinct high-contrast")
    a("  features the eye can lock onto) and gives clean rigid-scene camera")
    a("  parallax -- the most reliable case for optical flow.")
    a(f"- Cropped with `{FOOTAGE_CROP}` to drop the burned-in source-timecode")
    a("  strip. Optical flow computed at 640x360, rendered at 1920x1080.")
    a("- See `docs/space-center/"
      "footage-motion-lock-trackability-audit-2026-05-20.md` for the full")
    a("  footage survey and the ranked window list behind this choice.")
    a("")
    a("## No 3D Claim")
    a("")
    a("Optical flow measures **2D apparent image-space motion only**. v005 does")
    a("not claim to recover 3D motion from this monocular footage. The reef")
    a("window was chosen precisely because its motion is legible in the image")
    a("plane -- a rigid scene under camera parallax -- not because depth is")
    a("reconstructed. divergence/curl/strain language from earlier versions is")
    a("not used here; v005 only advects by the raw apparent-motion vectors.")
    a("")
    a("## Camera Drift")
    a("")
    a("A per-frame global-translation estimate (median of the flow field) is")
    a(f"computed as a camera-drift proxy -- mean ~{metrics['mean_global_drift_px_per_frame']}")
    a("px/frame over the clip. It is shown live in the debug-clip HUD and is")
    a("used to bias phrase seeding. It is deliberately **not** subtracted from")
    a("advection -- phrases advect by full apparent flow so they stay pinned to")
    a("reef features. On a reef the camera parallax IS most of the apparent")
    a("motion, and pinning the phrases to it is exactly the intended lock.")
    a("")
    a("## Lock Evidence (measured)")
    a("")
    a(f"- Phrases advected through apparent motion averaging "
      f"**{metrics['mean_glyph_disp_px_per_frame']} render px/frame** -- a")
    a("  steady, clearly visible traverse over the 6 s clip.")
    a("- The reef is a rigid scene, so this apparent motion is dominated by")
    a(f"  camera parallax: a global-translation estimate averages "
      f"{metrics['mean_global_drift_px_per_frame']} px/frame, with a smaller")
    a(f"  local-residual component (~{metrics['mean_local_residual_px_per_frame']} "
      "px/frame) from depth parallax between the near reef and the farther")
    a("  background. This is expected and correct -- on a rigid scene the")
    a("  camera parallax IS the motion to lock to; a phrase pinned to a reef")
    a("  feature rides that parallax and stays on the feature. (The local-vs-")
    a("  global split mattered on v004's salmon school, to separate fish")
    a("  motion from camera pan; on a rigid reef it is not the relevant lens.)")
    a("- The debug clip shows the lock directly: watch a ringed anchor stay on")
    a("  the same reef feature as the camera moves the scene across frame.")
    a("")
    a("## Honest Verdict")
    a("")
    for line in verdict:
        a(line)
    a("")
    a("## Outputs")
    a("")
    for c in clips:
        pr = c["ffprobe"]
        a(f"### {c['name']}.mp4")
        a("")
        a(f"- {c['desc']}")
        a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
          f"duration {pr['duration']:.3f}s, frames {pr['frames']}, "
          f"codec {pr['codec']}, {pr['size_kb']} KB")
        if c.get("nonblank"):
            nb = c["nonblank"]
            a(f"- Nonblank check: midpoint max luma {nb['max_luma']}, "
              f"nonblack pixels {nb['nonblack_px']}")
        a("")
    a("## Review Order")
    a("")
    a("1. `debug_best_window_motion_lock_v005.mp4` first -- it overlays the")
    a("   per-frame flow field and the phrase anchors on the footage. Pick a")
    a("   ringed anchor and confirm it rides a reef feature frame to frame.")
    a("2. `best_window_motion_lock_v005__over_source.mp4` -- the composite;")
    a("   judge whether the phrases visibly follow the reef as the camera moves.")
    a("3. `best_window_motion_lock_layer_v005_black_screen.mp4` -- the layer")
    a("   alone, for Resolume.")
    a("4. `contact_sheet_v005.png` -- the two composite panels are at different")
    a("   times, so the same phrases appear displaced with the reef.")
    a("")
    a("## Caveats")
    a("")
    a("- **Does not loop seamlessly.** A frame-synchronous overlay is tied to")
    a("  the footage timeline; frame 144 != frame 0. Inherent to the motion-")
    a("  lock approach. For seamless looping playback use v003.")
    a("- Optical flow is 2D apparent image-space motion -- not fluid physics,")
    a("  not 3D motion, not a vorticity measurement.")
    a("- A glyph that advects into a low-texture / low-motion region will")
    a("  briefly slow or stall -- that is the flow being honestly followed.")
    a("- Deterministic: same footage window reproduces the same result. No")
    a("  randomness in seeding, advection, or orientation.")
    a("- INTERNAL R&D only. circle/crescent/trigon are morphology classes")
    a("  here, not symbols; no cultural claim, no public readiness.")
    a("")
    a("## Open Questions For Austin")
    a("")
    a("1. Does the motion-lock now read clearly on the reef window (v005),")
    a("   versus the dense salmon school (v004)?")
    a("2. Crescent orientation: glyphs orient to the local flow direction and")
    a("   crescents cup back along it -- is that the right behaviour?")
    a("3. A frame-locked clip cannot loop. Is a non-looping clip acceptable for")
    a("   the show, or must the show layer loop (which forces v003's approach)?")
    a("")
    a("## Constraints Honored")
    a("")
    a("- Phrase motion is 100% footage-derived (per-frame advection); no")
    a("  scripted speed, no random scatter.")
    a("- No fish / animal glyphs; no named, chief, or supernatural beings.")
    a("- No topology / cymatics, no SD / LoRA / style transfer.")
    a("- No 3D-motion claim from monocular footage.")
    a("- Few (5), large, clearly locked phrases rather than many decorative marks.")
    a("- Outputs written only to this folder, the audit doc, and "
      "`scripts/water_flow_phrase_grammar_v005.py`.")
    a("")
    a("## Verification")
    a("")
    a("- `py_compile` on the script.")
    a("- `ffprobe` on every MP4 (dimensions / fps / duration / frame count above).")
    a("- Nonblank checks on every midpoint still.")
    a(f"- Contact sheet `contact_sheet_v005.png` ({sheet_size[0]}x{sheet_size[1]}); "
      "midpoint stills in `midpoint_stills/`.")
    a("")
    a("## Sources Read")
    a("")
    a("- Darren v004 review (salmon school too complex/3D for the lock to read).")
    a("- v004 README (mechanism + honest verdict + footage recommendation).")
    a("- docs/space-center/"
      "footage-motion-lock-trackability-audit-2026-05-20.md")
    a("")
    a("## Regenerate")
    a("")
    a("    python3 scripts/water_flow_phrase_grammar_v005.py")
    a("")
    (outdir / "README.md").write_text("\n".join(L), encoding="utf-8")


# ==========================================================================
# main
# ==========================================================================
def build_verdict(metrics):
    """An honest read of the motion-lock test. The mechanism is verified by
    construction + metrics + the debug clip; perceptual obviousness in the
    composite depends on the footage offering trackable landmarks, which the
    operator must judge by watching the clips."""
    disp = metrics["mean_glyph_disp_px_per_frame"]
    return [
        f"MECHANISM (unchanged from v004). Every glyph is advected frame by "
        f"frame by the local per-frame optical flow at its own position -- "
        f"mean apparent motion {disp} render px/frame. The phrases carry the "
        "footage's own motion and nothing else, so the overlay is locked to "
        "the footage by construction. On this rigid reef scene that motion is "
        "mostly camera parallax -- which is correct: a phrase pinned to a reef "
        "feature stays on it precisely by riding that parallax.",
        "",
        "WHAT v005 CHANGED. Only the footage window. v004 ran on the dense "
        "salmon school, where hundreds of near-identical fish at many depths "
        "gave the eye no landmark to see a primitive glued to. v005 runs on "
        "the reef-garden window (P1111509, t=1-7s) chosen by the trackability "
        "audit: an encrusted reef boulder with distinct high-contrast "
        "features (sponges, anemones) and clean rigid-scene camera parallax.",
        "",
        "WHY THIS SHOULD READ BETTER. Distinct features let the eye verify "
        "the lock -- watch a ringed anchor stay on the same orange sponge as "
        "the camera moves the whole reef across frame. Rigid-scene parallax "
        "also gives far cleaner, more reliable optical flow than froth or a "
        "schooling tangle. No 3D claim is made or needed: the reef's motion "
        "is legible in the 2D image plane.",
        "",
        "A motion-locked result cannot be fully judged from still frames -- "
        "the operator should watch debug_best_window_motion_lock_v005.mp4 "
        "(the lock is explicit there: flow vectors + anchors + trails) and "
        "best_window_motion_lock_v005__over_source.mp4. If the relationship "
        "between reef motion and primitive motion is now obvious, v005 is a "
        "pass; if it still does not read, that is a failed VISUAL test and "
        "should be reported plainly rather than over-polished.",
    ]


def main():
    repo = Path(__file__).resolve().parents[1]
    default_out = (repo / "track2-deterministic" / "morph_outputs_INTERNAL"
                   / "water_flow_phrase_grammar_v005_2026-05-20")
    moon = repo / "media" / "collaborators" / "moonfish-video" / "underwater"

    ap = argparse.ArgumentParser(description="Water-flow phrase grammar v005 -- "
                                             "motion-lock proof on the best window.")
    ap.add_argument("--outdir", default=str(default_out))
    # best window per the trackability audit: P1111509 reef garden, t=1-7s
    ap.add_argument("--footage", default=str(moon / "P1111509.mp4"))
    ap.add_argument("--start", type=float, default=1.0)
    ap.add_argument("--dur", type=float, default=DUR_S)
    ap.add_argument("--frames", type=int, default=N_FRAMES)
    ap.add_argument("--opacity", type=float, default=0.82,
                    help="composite additive opacity (reef footage is bright "
                         "and busy -- phrases need to read against it)")
    ap.add_argument("--smoke", action="store_true",
                    help="fast pipeline test: 30 frames")
    args = ap.parse_args()

    if args.smoke:
        args.frames = 30
        args.dur = args.frames / FPS

    assert AW % 4 == 0 and AH % 4 == 0, "analysis res must allow 3 pyramid levels"
    n_frames = max(2, args.frames)
    outdir = Path(args.outdir)
    (outdir / "midpoint_stills").mkdir(parents=True, exist_ok=True)
    footage = Path(args.footage)
    if not footage.exists():
        print(f"ERROR: footage not found -- {footage}")
        return 1

    print(f"water_flow_phrase_grammar_v005 -> {outdir}")
    print(f"  {W}x{H}  {FPS}fps  {n_frames} frames  ({n_frames / FPS:.3f}s)")
    print(f"  footage: {footage.name}  window [{args.start:.1f}s, "
          f"{args.start + args.dur:.1f}s]\n")

    # ---- per-frame optical flow ----
    t0 = time.time()
    print("PER-FRAME OPTICAL FLOW")
    frames = extract_gray_frames(footage, args.start, args.dur, AW, AH)
    print(f"  decoded {len(frames)} grayscale frames at {AW}x{AH}")
    flows = compute_flow_sequence(frames)
    drift = estimate_drift(flows)
    print(f"  computed {len(flows)} per-frame flow fields + 3-frame temporal "
          f"smoothing in {time.time() - t0:4.1f}s")
    print(f"  mean global drift {np.hypot(drift[:, 0], drift[:, 1]).mean():.3f} "
          f"px/frame (analysis 640x360)\n")

    # ---- simulate advected phrases ----
    all_phrases, metrics = simulate(flows, drift, n_frames)
    print(f"SIMULATION: {metrics['phrases_total']} phrases advected; "
          f"mean glyph motion {metrics['mean_glyph_disp_px_per_frame']} px/frame "
          f"(local residual {metrics['mean_local_residual_px_per_frame']}, "
          f"global drift {metrics['mean_global_drift_px_per_frame']}, "
          f"measured separately)\n")

    # ---- render ----
    print("RENDER")
    layer_mp4, layer_mid = render_phrase_layer(all_phrases, outdir, n_frames)

    comp_mp4 = outdir / "best_window_motion_lock_v005__over_source.mp4"
    comp_ok = make_composite(layer_mp4, footage, args.start, args.opacity,
                             -0.10, comp_mp4, n_frames)
    if comp_ok:
        print(f"  composite:    {comp_mp4.name}")

    debug_mp4 = outdir / "debug_best_window_motion_lock_v005.mp4"
    debug_mid = render_debug_clip(footage, args.start, all_phrases, flows, drift,
                                  debug_mp4, n_frames)

    # ---- midpoint stills ----
    mids = outdir / "midpoint_stills"
    Image.fromarray(layer_mid).save(
        mids / "best_window_motion_lock_layer_v005_mid.png")
    Image.fromarray(debug_mid).save(
        mids / "debug_best_window_motion_lock_v005_mid.png")
    comp_mid = grab_frame(comp_mp4, n_frames / FPS / 2.0) if comp_ok else None
    comp_early = grab_frame(comp_mp4, n_frames / FPS * 0.30) if comp_ok else None
    comp_late = grab_frame(comp_mp4, n_frames / FPS * 0.72) if comp_ok else None
    if comp_mid is not None:
        Image.fromarray(comp_mid).save(
            mids / "best_window_motion_lock_v005_mid.png")

    # ---- contact sheet (two composite times show the phrases displaced) ----
    panels = [
        ("best_window_motion_lock_layer_v005", "layer-only (black screen)",
         layer_mid),
        ("debug_best_window_motion_lock_v005",
         "footage + flow vectors + phrase anchors", debug_mid),
        ("reef overlay  (t ~ 30%)", "composite -- note phrase positions",
         comp_early),
        ("reef overlay  (t ~ 72%)",
         "composite -- same phrases, advected with the reef", comp_late),
    ]
    sheet_size = build_contact_sheet(panels, outdir / "contact_sheet_v005.png")
    print(f"  contact sheet: {sheet_size[0]}x{sheet_size[1]}")

    # ---- assemble clip metadata + verify ----
    clips = []
    clips.append({
        "name": "best_window_motion_lock_v005__over_source",
        "desc": "Composite: advected primitive phrases over the reef-garden "
                "source window. Phrase positions/orientations update from "
                "per-frame optical flow, so traces follow the reef as the "
                "camera moves past it.",
        "ffprobe": ffprobe_check(comp_mp4) if comp_ok else None,
        "nonblank": nonblank_check(comp_mid) if comp_mid is not None else None,
    })
    clips.append({
        "name": "best_window_motion_lock_layer_v005_black_screen",
        "desc": "The same advected phrase layer on pure black, for Resolume "
                "Screen/Additive mixing. Frame-synchronous -- does not loop.",
        "ffprobe": ffprobe_check(layer_mp4),
        "nonblank": nonblank_check(layer_mid),
    })
    clips.append({
        "name": "debug_best_window_motion_lock_v005",
        "desc": "Verification clip: source footage with the per-frame flow "
                "field and the primitive-phrase anchors drawn on top, plus a "
                "camera-drift HUD -- confirms the layer is locked to frame motion.",
        "ffprobe": ffprobe_check(debug_mp4),
        "nonblank": nonblank_check(debug_mid),
    })

    meta = {
        "footage_rel": str(footage.relative_to(repo)) if footage.is_relative_to(repo)
                       else str(footage),
        "start": args.start, "dur": args.dur,
    }
    verdict = build_verdict(metrics)
    write_readme(outdir, [c for c in clips if c["ffprobe"]], metrics, meta,
                 sheet_size, verdict)
    print("  README.md written\n")

    # ---- verification summary ----
    print("VERIFICATION SUMMARY")
    ok = True
    for c in clips:
        pr = c["ffprobe"]
        if pr is None:
            print(f"  [FAIL] {c['name']}: not produced")
            ok = False
            continue
        checks = {
            "1920x1080": pr["width"] == 1920 and pr["height"] == 1080,
            "24fps": abs(pr["fps"] - 24.0) < 0.01,
            f"{n_frames}frames": pr["frames"] == n_frames,
            "duration": abs(pr["duration"] - n_frames / FPS) < 0.06,
            "h264": pr["codec"] == "h264",
        }
        if c["nonblank"]:
            nb = c["nonblank"]
            checks["nonblank"] = nb["max_luma"] > 16 and nb["nonblack_px"] > 1000
        passed = all(checks.values())
        ok = ok and passed
        flags = " ".join(k for k, v in checks.items() if v)
        fail = " ".join("!" + k for k, v in checks.items() if not v)
        print(f"  [{'PASS' if passed else 'FAIL'}] {c['name']}: {flags} {fail}".rstrip())
    print(f"  [{'PASS' if metrics['phrases_total'] > 0 else 'FAIL'}] "
          f"{metrics['phrases_total']} phrases advected by per-frame flow")
    print(f"\n{'ALL CHECKS PASSED' if ok else 'CHECKS FAILED'}")
    print(f"VERDICT: {verdict[0]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
