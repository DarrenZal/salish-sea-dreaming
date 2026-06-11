#!/usr/bin/env python3
"""
water_flow_phrase_grammar_v003 -- SSD Phase 2, R&D Lane 2 (Water Dynamics /
Flow-Following Grammar).

INTERNAL ONLY. Not Austin-approved. Not a public cultural-grammar claim.

The v001/v002 water-flow clips placed primitive phrases on hand-authored
parametric paths (sine-wave streamlines, vertical waterfall lanes). Darren's
2026-05-20 overnight review liked `current_streamline_field_v002` and its
Moonfish composite, and asked for the next pass to use *real footage motion
fields* rather than hand-authored lines only.

v003 does exactly that. It runs a dense optical-flow analysis on real Moonfish
underwater footage, aggregates a mean apparent-motion field, and derives three
image-space motion quantities from it:

  - velocity  -> dominant current / motion paths   (streamlines)
  - curl      -> rotational / eddy areas           (eddy nodes)
  - strain    -> stretching / shear zones          (shear wavefronts)

Each quantity drives a different primitive-phrase placement, all in the same
circle -> crescent -> crescent -> trigon grammar:

  - circle   = source / eddy / pressure node / impact
  - crescent = shear front / wavefront / expansion band
  - trigon   = release / attenuation / directional tip

IMPORTANT -- this is NOT a fluid-physics claim. Optical flow measures *apparent
image-space motion* (camera drift + subject motion + current, combined). The
words divergence / curl / strain are used as image-plane motion descriptors, an
optical-flow proxy, not a measurement of literal water compression or vorticity.

Outputs (all 1920x1080, 24fps, 6.0s, 144-frame seamless loops):
  1. motion_field_current_layer_v003.mp4              black-screen additive
  2. curl_eddy_nodes_layer_v003.mp4                   black-screen additive
  3. strain_shear_wavefront_layer_v003.mp4            black-screen additive
  4. motion_field_current_composite_v003__over_moonfish-water.mp4   composite

The motion *structure* (streamlines, eddy nodes, wavefront sites) is extracted
once from the aggregated field and held fixed; only the phrases animate along
it. This is deterministic, loops seamlessly, and keeps strict common fate -- no
random scatter, no independent jitter.

Constraints honored: no fish / animal glyphs, no SD / LoRA / style transfer, no
topology / cymatics / seed-of-life construction geometry, no prompt scenes, no
randomness. Footage may contain fish (it is a salmon-school clip); the renderer
draws only abstract circle / crescent / trigon primitives placed by the motion
field -- never a fish glyph.

Glyph rendering (SDF glyphs, two-tier glow, tone map) is carried over unchanged
from water_flow_phrase_grammar_v002.py so the visual language Darren liked is
preserved; v003 changes only where the phrases are placed.

Dependencies: numpy, scipy, Pillow, ffmpeg/ffprobe. No OpenCV -- the dense
Lucas-Kanade optical flow is implemented here in numpy + scipy.ndimage.

Usage:
    python3 scripts/water_flow_phrase_grammar_v003.py            # full render
    python3 scripts/water_flow_phrase_grammar_v003.py --smoke    # fast pipeline test
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
from scipy.ndimage import (gaussian_filter, gaussian_filter1d, map_coordinates,
                           maximum_filter)

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------
W, H = 1920, 1080
FPS = 24
DUR_S = 6.0
N_FRAMES = int(round(FPS * DUR_S))           # 144

# optical-flow analysis resolution (cropped 16:9 footage scaled to this).
# 640x360 -> 3 clean pyramid levels (640/4=160, 360/4=90) and an exact x3
# upscale to the 1920x1080 render space.
AW, AH = 640, 360
UPSCALE = W / AW                             # 3.0

# footage crop drops the burned-in source-timecode strip (same crop as v002).
FOOTAGE_CROP = "crop=1770:996:75:0"

COL_CIRCLE = np.array([1.00, 0.86, 0.60], np.float32)   # warm gold-white -- origin / node
COL_CRESC  = np.array([0.40, 0.83, 1.00], np.float32)   # bioluminescent cyan -- wavefront body
COL_TRIGON = np.array([0.62, 1.00, 0.84], np.float32)   # pale teal-green -- release terminus
COL_GUIDE  = np.array([0.16, 0.40, 0.62], np.float32)   # dim flow-channel hint

I_CIRCLE = 1.05
I_CRESC  = 0.92
I_TRIGON = 0.66

R_CIRCLE = 32.0
R_CRESC  = 58.0
R_TRIGON = 33.0

GLOW_TIGHT = 14.0
GLOW_WIDE  = 34.0

TRAIL_N    = 3
TRAIL_GAP  = 0.013
TRAIL_FALL = 0.52

EXPOSURE = 1.58
POST_GAMMA = 1.0 / 1.35

SCENES = [
    "motion_field_current_layer_v003",
    "curl_eddy_nodes_layer_v003",
    "strain_shear_wavefront_layer_v003",
]


# ==========================================================================
# math helpers
# ==========================================================================
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def window(q, w=0.09):
    """0 at q=0 and q=1, ~1 in the middle -- keeps the loop seam clean."""
    return smoothstep(0.0, w, q) * smoothstep(1.0, 1.0 - w, q)


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
    """SDF -> additive intensity: a crisp soft-edged core, a clean tight halo,
    and just a whisper of wide bloom -- bold and projection-readable."""
    fill = smoothstep(1.7, -1.7, sdf)
    pos = np.maximum(sdf, 0.0)
    glow_tight = np.exp(-(pos / GLOW_TIGHT) ** 2)
    glow_wide = np.exp(-(pos / GLOW_WIDE) ** 2)
    return np.maximum(fill, np.maximum(0.52 * glow_tight, 0.10 * glow_wide))


def _add(canvas, x0, y0, x1, y1, field, color, intensity):
    canvas[y0:y1, x0:x1, :] += field[:, :, None] * (color[None, None, :] * np.float32(intensity))


# ==========================================================================
# primitive glyphs  (carried over verbatim from water_flow_phrase_grammar_v002)
# ==========================================================================
def draw_circle(canvas, cx, cy, radius, color, intensity):
    """Filled glowing disc -- the phrase origin / focal anchor / eddy node."""
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
    """Crescent = a tapered circular-arc blade. It cups toward `open_angle`
    (the concave side) and tapers to two sharp cusps. The arc spans ~110
    degrees so it reads as a clean bold blade, never ringing an enclosed dark
    core the way a deep two-disc lune does at large scale."""
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
    """Large disc just outside an edge; its near arc scoops a shallow concave
    curve so the trigon reads as an elegant three-point form."""
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
    """Soft round glow blob -- used to paint motion-trail wakes."""
    if intensity <= 0.002 or radius <= 0.5:
        return
    reach = radius * 2.7 + 3.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    field = np.exp(-(lx * lx + ly * ly) / (radius * radius))
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


# ==========================================================================
# optical flow  (dense Lucas-Kanade, pyramidal, pure numpy + scipy.ndimage)
# ==========================================================================
def extract_gray_frames(footage, start, dur, w, h):
    """Decode a cropped, scaled, 24fps grayscale frame stack from footage."""
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
        raise RuntimeError(f"footage window too short: only {n} frame(s) decoded")
    return np.frombuffer(proc.stdout[:n * w * h], np.uint8).reshape(n, h, w)


def _grad(im):
    """Central-difference spatial gradients."""
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
    """Backward-warp `im` by flow (u, v)."""
    h, w = im.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return map_coordinates(im, [yy + v, xx + u], order=1, mode="nearest")


def _lk_step(im1, im2, sigma):
    """One windowed Lucas-Kanade least-squares solve over the whole frame."""
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
    """Coarse-to-fine pyramidal Lucas-Kanade dense optical flow.

    Returns (u, v) at the input resolution. `im1`, `im2` are float [0, 1]."""
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


def aggregate_flow(frames, stride):
    """Mean apparent-motion field over consecutive frame pairs.

    Transient darts (fish flicking, ray shimmer) average out; the persistent
    current / drift / collective-motion component survives. Returns
    (mean_u, mean_v, n_pairs) at analysis resolution."""
    n = len(frames)
    su = np.zeros((AH, AW), np.float64)
    sv = np.zeros((AH, AW), np.float64)
    pairs = 0
    for i in range(0, n - 1, stride):
        a = frames[i].astype(np.float32) / 255.0
        b = frames[i + 1].astype(np.float32) / 255.0
        u, v = pyramid_flow(a, b)
        su += u
        sv += v
        pairs += 1
    mean_u = (su / pairs).astype(np.float32)
    mean_v = (sv / pairs).astype(np.float32)
    return mean_u, mean_v, pairs


def derive_fields(mean_u, mean_v):
    """Image-space motion descriptors from the mean apparent-motion field.

    These are optical-flow proxies, not fluid-physics measurements:
      curl   ~ rotational / eddy strength (signed: + = clockwise screen sense)
      strain ~ shear / stretching magnitude
    Also returns the principal-stretch orientation field `strain_dir`."""
    u = gaussian_filter(mean_u, 2.0)
    v = gaussian_filter(mean_v, 2.0)
    ux, uy = _grad(u)
    vx, vy = _grad(v)
    curl = gaussian_filter(vx - uy, 3.0)
    shear = uy + vx
    normal = ux - vy
    strain = gaussian_filter(np.sqrt(shear * shear + normal * normal), 3.0)
    # principal stretch axis of the symmetric strain-rate tensor
    strain_dir = 0.5 * np.arctan2(gaussian_filter(shear, 3.0),
                                  gaussian_filter(normal, 3.0))
    return {"u": u, "v": v, "curl": curl,
            "strain": strain, "strain_dir": strain_dir}


# ==========================================================================
# structure extraction  (deterministic; everything derived from a field)
# ==========================================================================
def _bilerp(field, x, y):
    """Bilinear sample of an (H, W) field at float (x, y)."""
    h, w = field.shape
    x = min(max(x, 0.0), w - 1.001)
    y = min(max(y, 0.0), h - 1.001)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    a = field[y0, x0]
    b = field[y0, x0 + 1]
    c = field[y0 + 1, x0]
    d = field[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def find_peaks(field, count, min_sep, frac_floor):
    """Local maxima of `field`, NMS-separated, ranked by value. `frac_floor`
    is a fraction of the field's own max -- adaptive, never random."""
    fmax = float(field.max())
    if fmax <= 1e-9:
        return [], 0
    floor = frac_floor * fmax
    mx = maximum_filter(field, size=9, mode="nearest")
    peaks = (field >= mx) & (field > floor)
    ys, xs = np.where(peaks)
    if len(xs) == 0:
        return [], 0
    vals = field[ys, xs]
    order = np.argsort(-vals)
    kept, rejected = [], 0
    for idx in order:
        x, y, val = float(xs[idx]), float(ys[idx]), float(vals[idx])
        if all(math.hypot(x - kx, y - ky) >= min_sep for kx, ky, _ in kept):
            kept.append((x, y, val))
        else:
            rejected += 1
        if len(kept) >= count:
            break
    return kept, rejected


def trace_streamline(u, v, x0, y0, step, max_steps, mag_floor):
    """RK2-integrate the apparent-motion field through a seed, forward and
    backward, to recover one current path. Returns analysis-space points."""
    pts = [(x0, y0)]
    for direction in (1.0, -1.0):
        x, y = x0, y0
        for _ in range(max_steps):
            du, dv = _bilerp(u, x, y), _bilerp(v, x, y)
            m = math.hypot(du, dv)
            if m < mag_floor:
                break
            dx, dy = du / m, dv / m
            xm = x + direction * dx * step * 0.5
            ym = y + direction * dy * step * 0.5
            du2, dv2 = _bilerp(u, xm, ym), _bilerp(v, xm, ym)
            m2 = math.hypot(du2, dv2)
            if m2 < 1e-6:
                break
            dx, dy = du2 / m2, dv2 / m2
            x += direction * dx * step
            y += direction * dy * step
            if not (3.0 <= x < AW - 3.0 and 3.0 <= y < AH - 3.0):
                break
            if direction > 0:
                pts.append((x, y))
            else:
                pts.insert(0, (x, y))
    return pts


class Polyline:
    """Arc-length-parameterised polyline in render (1920x1080) space."""

    def __init__(self, pts):
        p = np.asarray(pts, np.float64)
        seg = np.hypot(np.diff(p[:, 0]), np.diff(p[:, 1]))
        self.s = np.concatenate([[0.0], np.cumsum(seg)])
        self.total = float(self.s[-1])
        self.p = p

    def point(self, u):
        d = np.clip(u, 0.0, 1.0) * self.total
        i = int(np.searchsorted(self.s, d) - 1)
        i = min(max(i, 0), len(self.s) - 2)
        span = max(self.s[i + 1] - self.s[i], 1e-6)
        f = (d - self.s[i]) / span
        return (self.p[i, 0] + f * (self.p[i + 1, 0] - self.p[i, 0]),
                self.p[i, 1] + f * (self.p[i + 1, 1] - self.p[i, 1]))

    def tangent(self, u):
        a = self.point(min(u + 0.012, 1.0))
        b = self.point(max(u - 0.012, 0.0))
        dx, dy = a[0] - b[0], a[1] - b[1]
        el = math.hypot(dx, dy) or 1.0
        return dx / el, dy / el


def extract_streamlines(fields, max_lines):
    """Seed in strong mean-flow regions, trace current paths, keep the
    longest well-separated few. Returns (Polylines, seed-debug, rejected)."""
    u, v = fields["u"], fields["v"]
    speed = gaussian_filter(np.sqrt(u * u + v * v), 2.5)
    # candidate seeds: a coarse grid scored by mean-flow speed
    cand = []
    for gy in np.linspace(AH * 0.16, AH * 0.84, 7):
        for gx in np.linspace(AW * 0.12, AW * 0.88, 11):
            cand.append((gx, gy, _bilerp(speed, gx, gy)))
    cand.sort(key=lambda c: -c[2])
    floor = 0.16 * max((c[2] for c in cand), default=0.0)
    streamlines, seeds, used, rejected = [], [], [], 0
    for gx, gy, sc in cand:
        if sc < floor:
            break
        if any(math.hypot(gx - ux, gy - uy) < AW * 0.17 for ux, uy in used):
            rejected += 1
            continue
        raw = trace_streamline(u, v, gx, gy, step=4.0, max_steps=130,
                               mag_floor=0.55 * floor)
        if len(raw) < 14:
            rejected += 1
            continue
        arr = np.asarray(raw, np.float64)
        arr[:, 0] = gaussian_filter1d(arr[:, 0], 3.0, mode="nearest")
        arr[:, 1] = gaussian_filter1d(arr[:, 1], 3.0, mode="nearest")
        length = float(np.hypot(np.diff(arr[:, 0]), np.diff(arr[:, 1])).sum())
        if length < AW * 0.34:
            rejected += 1
            continue
        used.append((gx, gy))
        seeds.append({"seed_xy": [round(gx, 1), round(gy, 1)],
                      "mean_speed": round(sc, 4),
                      "arc_len_analysis_px": round(length, 1),
                      "n_points": len(arr)})
        streamlines.append(Polyline(arr * UPSCALE))
        if len(streamlines) >= max_lines:
            break
    return streamlines, seeds, rejected


def extract_eddy_nodes(fields, max_nodes):
    """Eddy nodes = local maxima of |curl| (rotational apparent motion)."""
    curl = fields["curl"]
    peaks, rejected = find_peaks(np.abs(curl), max_nodes, AW * 0.15, 0.30)
    cmax = float(np.abs(curl).max()) or 1.0
    nodes = []
    for x, y, val in peaks:
        sign = 1.0 if _bilerp(curl, x, y) >= 0.0 else -1.0
        nodes.append({
            "xy": (x * UPSCALE, y * UPSCALE),
            "xy_analysis": [round(x, 1), round(y, 1)],
            "curl_abs": round(val, 5),
            "strength": round(min(1.0, val / cmax), 3),
            "rotation": "cw_screen" if sign > 0 else "ccw_screen",
            "sign": sign,
        })
    return nodes, rejected


def extract_wavefront_sites(fields, max_sites):
    """Wavefront sites = local maxima of strain (shear / stretch zones)."""
    strain = fields["strain"]
    sdir = fields["strain_dir"]
    peaks, rejected = find_peaks(strain, max_sites, AW * 0.26, 0.34)
    smax = float(strain.max()) or 1.0
    sites = []
    for x, y, val in peaks:
        theta = float(_bilerp(np.cos(2 * sdir), x, y))
        thetb = float(_bilerp(np.sin(2 * sdir), x, y))
        ang = 0.5 * math.atan2(thetb, theta)          # principal stretch axis
        # the stretch axis is 180-deg ambiguous; propagate the wavefront the
        # way that points into the frame so it does not expand off-screen
        toward = math.atan2(AH * 0.5 - y, AW * 0.5 - x)
        if math.cos(ang - toward) < 0.0:
            ang += math.pi
        sites.append({
            "xy": (x * UPSCALE, y * UPSCALE),
            "xy_analysis": [round(x, 1), round(y, 1)],
            "strain": round(val, 5),
            "strength": round(min(1.0, val / smax), 3),
            "stretch_angle_rad": round(ang, 4),
            "angle": ang,
        })
    return sites, rejected


# ==========================================================================
# faint guide layer
# ==========================================================================
def _stamp_ribbon(layer, path_fn, samples, width, peak):
    for i in range(samples):
        x, y = path_fn(i / (samples - 1))
        reach = width * 1.7 + 3.0
        x0, y0, x1, y1 = _box(x, y, reach)
        if x1 <= x0 or y1 <= y0:
            continue
        lx, ly = _local(x0, y0, x1, y1, x, y)
        val = np.exp(-(np.sqrt(lx * lx + ly * ly) / (width * 0.62)) ** 2) * peak
        sub = layer[y0:y1, x0:x1]
        np.maximum(sub, val, out=sub)


def _stamp_glow(layer, cx, cy, radius, peak):
    reach = radius * 2.4 + 3.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    val = np.exp(-(lx * lx + ly * ly) / (radius * radius)) * peak
    sub = layer[y0:y1, x0:x1]
    np.maximum(sub, val, out=sub)


def build_guide(scene, streamlines, nodes, sites):
    """Dim flow-channel hint -- shows the footage-derived structure faintly."""
    layer = np.zeros((H, W), np.float32)
    if scene == "motion_field_current_layer_v003":
        for sl in streamlines:
            _stamp_ribbon(layer, sl.point, 360, 26.0, 0.070)
    elif scene == "curl_eddy_nodes_layer_v003":
        for nd in nodes:
            cx, cy = nd["xy"]
            _stamp_glow(layer, cx, cy, 120.0 + 70.0 * nd["strength"], 0.060)
    elif scene == "strain_shear_wavefront_layer_v003":
        for st in sites:
            cx, cy = st["xy"]
            _stamp_glow(layer, cx, cy, 100.0 + 80.0 * st["strength"], 0.052)
    return layer


# ==========================================================================
# phrase rendering -- layer 1: phrases travel current streamlines
# ==========================================================================
def render_phrase_on_path(canvas, path_fn, tan_fn, u_head, q, gap, scale=1.0):
    """Draw one circle->crescent->crescent->trigon phrase as a rigid travelling
    train with a short curved motion-trail wake. The circle (origin) trails
    upstream; the trigon (release) leads downstream."""
    win = float(window(q, 0.09))
    layout = (
        (0, "trigon", COL_TRIGON, R_TRIGON, I_TRIGON),
        (1, "crescent", COL_CRESC, R_CRESC, I_CRESC),
        (2, "crescent", COL_CRESC, R_CRESC, I_CRESC),
        (3, "circle", COL_CIRCLE, R_CIRCLE, I_CIRCLE),
    )
    for rank, kind, col, size, inten in layout:
        u = u_head - rank * gap
        if u < 0.0 or u > 1.0:
            continue
        x, y = path_fn(u)
        tx, ty = tan_fn(u)
        ang = math.atan2(ty, tx)
        fade = float(smoothstep(0.0, 0.09, u) * smoothstep(1.0, 0.91, u)) * win
        if fade <= 0.003:
            continue
        wake_r = size * scale * 0.42
        for j in range(1, TRAIL_N + 1):
            ut = u - j * TRAIL_GAP
            if ut < 0.0:
                break
            bx, by = path_fn(ut)
            bfade = fade * 0.45 * (TRAIL_FALL ** j) * float(smoothstep(0.0, 0.06, ut))
            draw_blob(canvas, bx, by, wake_r * (1.0 - 0.13 * j), col, inten * bfade)
        if kind == "circle":
            draw_circle(canvas, x, y, size * scale, col, inten * fade)
        elif kind == "crescent":
            # concave cups back toward the origin; convex bulge leads
            draw_crescent(canvas, x, y, size * scale, ang + math.pi, col, inten * fade)
        else:
            draw_trigon(canvas, x, y, size * scale, ang, col, inten * fade)


def render_current_layer(canvas, f, n, streamlines, bundles, guide):
    """Sparse phrase bundles riding the footage-derived current streamlines."""
    shimmer = 0.80 + 0.20 * math.sin(2.0 * math.pi * f / n)
    canvas += guide[:, :, None] * (COL_GUIDE[None, None, :] * np.float32(shimmer))
    gap_base = 150.0
    span_pad = 6.0
    for sl_idx, n_bundles, off0 in bundles:
        sl = streamlines[sl_idx]
        gap = min(0.135, max(0.052, gap_base / max(sl.total, 1.0)))
        span = 1.0 + span_pad * gap
        for b in range(n_bundles):
            off = (off0 + b / n_bundles) % 1.0
            q = (f / n + off) % 1.0
            u_head = -3.0 * gap + q * span
            render_phrase_on_path(canvas, sl.point, sl.tangent, u_head, q, gap)


# ==========================================================================
# phrase rendering -- layer 2: phrases orbit curl / eddy nodes
# ==========================================================================
def render_curl_layer(canvas, f, n, nodes, guide):
    """Each eddy node carries a pulsing circle pivot and a compact
    crescent/crescent/trigon spiral arm. The arm's radius grows and its angle
    lags along the phrase, so it reads as a turning eddy; rotation sense
    follows the sign of curl, crescents cup the pivot, the trigon releases
    outward-tangentially."""
    shimmer = 0.80 + 0.20 * math.sin(2.0 * math.pi * f / n)
    canvas += guide[:, :, None] * (COL_GUIDE[None, None, :] * np.float32(shimmer))
    t = f / n
    for idx, nd in enumerate(nodes):
        cx, cy = nd["xy"]
        s = nd["sign"]
        strg = nd["strength"]
        # circle pivot -- the eddy / pressure node; gentle pulse
        pulse = 1.0 + 0.11 * math.sin(2.0 * math.pi * t + idx)
        draw_circle(canvas, cx, cy, R_CIRCLE * (0.74 + 0.46 * strg) * pulse,
                    COL_CIRCLE, I_CIRCLE)
        # one full revolution per loop (seamless)
        phi = (math.atan2(cy - H * 0.5, cx - W * 0.5) + idx * 0.9
               + s * 2.0 * math.pi * t)
        gscale = 0.52 + 0.36 * strg
        # spiral arm: radius grows + angle lags along circle->cr->cr->trigon
        arm = (
            ("crescent", R_CIRCLE * 1.95, 0.00, I_CRESC,        R_CRESC),
            ("crescent", R_CIRCLE * 2.78, 0.62, I_CRESC * 0.84, R_CRESC * 0.92),
            ("trigon",   R_CIRCLE * 3.66, 1.32, I_TRIGON,       R_TRIGON),
        )
        for kind, r_base, dang, inten, size in arm:
            r_orb = r_base + 26.0 * strg
            a = phi - s * dang
            gx = cx + r_orb * math.cos(a)
            gy = cy + r_orb * math.sin(a)
            col = COL_TRIGON if kind == "trigon" else COL_CRESC
            # short curved wake receding along the spiral arc
            for j in range(1, TRAIL_N + 1):
                wa = a - s * j * 0.10
                wr = r_orb - j * 3.0
                draw_blob(canvas, cx + wr * math.cos(wa), cy + wr * math.sin(wa),
                          size * gscale * 0.40 * (1.0 - 0.13 * j),
                          col, inten * 0.40 * (TRAIL_FALL ** j))
            if kind == "trigon":
                # release: outward, leaning into the rotation sense
                out = math.atan2(gy - cy, gx - cx) + s * 0.7
                draw_trigon(canvas, gx, gy, size * gscale, out, col, inten)
            else:
                # crescent cups inward toward the eddy pivot
                cup = math.atan2(cy - gy, cx - gx)
                draw_crescent(canvas, gx, gy, size * gscale, cup, col, inten)


# ==========================================================================
# phrase rendering -- layer 3: strain/shear wavefront phrases
# ==========================================================================
def render_strain_layer(canvas, f, n, sites, guide):
    """Each strain site emits a phrase propagating along its principal stretch
    axis: a circle origin (impact / core), two broad crescent wavefronts
    expanding outward well-separated, and a small trigon release at the
    leading edge. Wide arcs + generous spacing + an early-fading circle keep
    it reading as an expanding wavefront family, not a compact body."""
    shimmer = 0.80 + 0.20 * math.sin(2.0 * math.pi * f / n)
    canvas += guide[:, :, None] * (COL_GUIDE[None, None, :] * np.float32(shimmer))
    t = f / n
    n_sites = max(len(sites), 1)
    for idx, st in enumerate(sites):
        cx, cy = st["xy"]
        ang = st["angle"]
        strg = st["strength"]
        dx, dy = math.cos(ang), math.sin(ang)
        # one wavefront per site, phases staggered across sites so a few are
        # always mid-life -- sparse and individually followable
        q = (t + idx / n_sites) % 1.0
        win = float(window(q, 0.10))
        if win <= 0.003:
            continue
        front = (96.0 + 300.0 * q) * (0.78 + 0.50 * strg)          # expansion
        # circle origin -- bright impact core, fades out by mid-life so the
        # phrase becomes a pure expanding front rather than a body anchor
        o_fade = win * float(smoothstep(0.44, 0.0, q))
        draw_circle(canvas, cx, cy, R_CIRCLE * (0.58 + 0.34 * strg),
                    COL_CIRCLE, I_CIRCLE * o_fade)
        # two broad crescent wavefronts (expanding ripple rings), broadside to
        # the stretch axis, cupping back toward the origin core
        for cr in range(2):
            off = front * (0.60 + 0.46 * cr)
            gx, gy = cx + dx * off, cy + dy * off
            cfade = win * ((1.0 - q) ** 1.15) * (1.0 - 0.16 * cr)
            csize = (R_CRESC * (1.26 + 0.20 * strg) * (1.0 + 0.12 * cr)
                     * (1.0 - 0.14 * q))
            draw_crescent(canvas, gx, gy, csize, ang + math.pi,
                          COL_CRESC, I_CRESC * cfade)
        # trigon release -- tucked just past the leading crescent so it reads
        # as the connected release tip, attenuating downstream
        tx, ty = cx + dx * front * 1.20, cy + dy * front * 1.20
        tfade = win * ((1.0 - q) ** 1.7)
        draw_trigon(canvas, tx, ty,
                    R_TRIGON * (0.86 + 0.2 * strg) * (1.0 - 0.24 * q),
                    ang, COL_TRIGON, I_TRIGON * tfade)


# ==========================================================================
# tone map + encode
# ==========================================================================
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


SCENE_RENDERERS = {
    "motion_field_current_layer_v003": "current",
    "curl_eddy_nodes_layer_v003": "curl",
    "strain_shear_wavefront_layer_v003": "strain",
}


def render_scene(scene, outdir, n_frames, ctx):
    """Render one black-screen layer to MP4; return the midpoint RGB frame."""
    kind = SCENE_RENDERERS[scene]
    guide = build_guide(scene, ctx["streamlines"], ctx["nodes"], ctx["sites"])
    mid_idx = n_frames // 2
    out_mp4 = outdir / f"{scene}.mp4"
    proc = _encoder(out_mp4)
    mid_frame = None
    t0 = time.time()
    for f in range(n_frames):
        canvas = np.zeros((H, W, 3), np.float32)
        if kind == "current":
            render_current_layer(canvas, f, n_frames, ctx["streamlines"],
                                  ctx["bundles"], guide)
        elif kind == "curl":
            render_curl_layer(canvas, f, n_frames, ctx["nodes"], guide)
        else:
            render_strain_layer(canvas, f, n_frames, ctx["sites"], guide)
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
        raise RuntimeError(f"ffmpeg failed for {scene}:\n"
                           f"{proc.stderr.read().decode('utf-8', 'replace')}")
    Image.fromarray(mid_frame).save(outdir / "midpoint_stills" / f"{scene}_mid.png")
    print(f"  {scene}: {n_frames} frames + still in {time.time() - t0:4.1f}s")
    return mid_frame


# ==========================================================================
# composite preview (layer additively blended over footage)
# ==========================================================================
def make_composite(layer_mp4, footage, start, opacity, footage_dim, out_mp4, n_frames):
    """Blend a black-screen layer additively over the same footage window it
    was derived from. Footage is cropped to drop the burned-in timecode,
    scaled to 1080p, set to 24fps, slightly dimmed, then the layer is added."""
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
        return None
    still_png = out_mp4.parent / "midpoint_stills" / f"{out_mp4.stem}_mid.png"
    grab = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(dur / 2.0),
         "-i", str(out_mp4), "-frames:v", "1", "-update", "1", str(still_png)],
        capture_output=True, text=True)
    if grab.returncode != 0:
        return None
    print(f"  {out_mp4.name}: composite over {Path(footage).name}")
    return np.asarray(Image.open(still_png).convert("RGB"))


# ==========================================================================
# verification
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


# ==========================================================================
# debug visualisations  (evidence: prove the field drives the placement)
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


def _heat_seq(field, lo, hi):
    """Sequential heat colormap -> uint8 RGB (deep teal -> cyan -> white)."""
    t = np.clip((field - lo) / (hi - lo + 1e-9), 0.0, 1.0)
    r = np.clip(t * 1.5 - 0.45, 0.0, 1.0)
    g = np.clip(t * 1.25, 0.0, 1.0)
    b = np.clip(0.22 + t * 0.78, 0.0, 1.0)
    return (np.stack([r, g, b], -1) * 255.0).astype(np.uint8)


def _heat_div(field, scale):
    """Diverging colormap -> uint8 RGB (blue = CW, warm = CCW screen sense)."""
    t = np.clip(field / (scale + 1e-9), -1.0, 1.0)
    pos = np.clip(t, 0.0, 1.0)
    neg = np.clip(-t, 0.0, 1.0)
    r = 0.07 + pos * 0.93
    g = 0.09 + (pos + neg) * 0.26
    b = 0.13 + neg * 0.87
    return (np.stack([r, g, b], -1) * 255.0).astype(np.uint8)


def _label(draw, xy, text, font, fill=(232, 244, 250)):
    draw.text((xy[0] + 1, xy[1] + 1), text, font=font, fill=(0, 0, 0))
    draw.text(xy, text, font=font, fill=fill)


def render_debug_images(outdir, fields, ctx, n_pairs):
    """Four debug overlays proving every primitive sits on a field quantity."""
    dbg = outdir / "debug"
    dbg.mkdir(parents=True, exist_ok=True)
    font = _load_font(17)
    font_s = _load_font(13)
    out_w, out_h = 1280, 720
    panels = []

    def finish(img, title):
        img = img.resize((out_w, out_h), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        _label(d, (16, 12), title, font)
        img.save(dbg / f"debug_{title.split()[0].lower()}.png")
        panels.append((title, img))
        return img

    # 1. mean apparent-motion field -- quiver over speed heatmap
    speed = np.sqrt(fields["u"] ** 2 + fields["v"] ** 2)
    img = Image.fromarray(_heat_seq(speed, 0.0, max(speed.max(), 1e-6)))
    d = ImageDraw.Draw(img)
    for gy in range(0, AH, 26):
        for gx in range(0, AW, 26):
            uu, vv = fields["u"][gy, gx], fields["v"][gy, gx]
            d.line([(gx, gy), (gx + uu * 7.0, gy + vv * 7.0)], fill=(252, 224, 140), width=1)
            d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(250, 250, 250))
    finish(img, f"Velocity mean apparent-motion field ({n_pairs} flow pairs)")

    # 2. streamlines + seeds over speed heatmap
    img = Image.fromarray(_heat_seq(speed, 0.0, max(speed.max(), 1e-6)))
    d = ImageDraw.Draw(img)
    for sl in ctx["streamlines"]:
        pa = sl.p / UPSCALE
        d.line([(float(x), float(y)) for x, y in pa], fill=(255, 232, 150), width=2)
    for sd in ctx["seeds"]:
        sx, sy = sd["seed_xy"]
        d.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], outline=(255, 255, 255), width=2)
    finish(img, f"Streamlines {len(ctx['streamlines'])} current paths from seeds")

    # 3. curl field + eddy nodes
    curl = fields["curl"]
    cscale = max(np.abs(curl).max(), 1e-6)
    img = Image.fromarray(_heat_div(curl, cscale))
    d = ImageDraw.Draw(img)
    for nd in ctx["nodes"]:
        x, y = nd["xy_analysis"]
        rr = 7 + 13 * nd["strength"]
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255), width=2)
        arc = "CW" if nd["sign"] > 0 else "CCW"
        _label(d, (x + rr + 2, y - 8), arc, font_s)
    finish(img, f"Curl {len(ctx['nodes'])} eddy nodes (warm=CW blue=CCW)")

    # 4. strain field + wavefront sites with principal stretch ticks
    strain = fields["strain"]
    img = Image.fromarray(_heat_seq(strain, 0.0, max(strain.max(), 1e-6)))
    d = ImageDraw.Draw(img)
    for st in ctx["sites"]:
        x, y = st["xy_analysis"]
        rr = 6 + 12 * st["strength"]
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255), width=2)
        ca, sa = math.cos(st["angle"]), math.sin(st["angle"])
        d.line([(x - ca * 26, y - sa * 26), (x + ca * 26, y + sa * 26)],
               fill=(255, 232, 150), width=2)
    finish(img, f"Strain {len(ctx['sites'])} shear/wavefront sites")

    # debug contact sheet (2x2)
    cw, ch = 640, 360
    sheet = Image.new("RGB", (cw * 2, ch * 2), (0, 0, 0))
    for (title, im), (px, py) in zip(panels, [(0, 0), (cw, 0), (0, ch), (cw, ch)]):
        sheet.paste(im.resize((cw, ch), Image.LANCZOS), (px, py))
    sheet.save(dbg / "debug_contact_sheet.png")
    return [t for t, _ in panels]


# ==========================================================================
# contact sheet (deliverables)
# ==========================================================================
def build_contact_sheet(panels, outpath):
    """panels: list of (label, sublabel, ndarray-or-None), laid out 2x2."""
    cw, ch = 960, 540
    sheet = Image.new("RGB", (cw * 2, ch * 2), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    font_t, font_s = _load_font(25), _load_font(18)
    cells = [(0, 0), (cw, 0), (0, ch), (cw, ch)]
    for (label, sub, arr), (px, py) in zip(panels, cells):
        if arr is not None:
            sheet.paste(Image.fromarray(arr).resize((cw, ch), Image.LANCZOS), (px, py))
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (228, 240, 248))):
            draw.text((px + 20 + dx, py + 16 + dy), label, font=font_t, fill=fill)
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (150, 186, 205))):
            draw.text((px + 20 + dx, py + 48 + dy), sub, font=font_s, fill=fill)
    sheet.save(outpath)
    return sheet.size


# ==========================================================================
# sidecar + README
# ==========================================================================
def write_sidecar(outdir, ctx, meta):
    """Structured per-structure role data -- the evidence floor."""
    data = {
        "packet": "water_flow_phrase_grammar_v003_2026-05-20",
        "lane": "Water Dynamics / Flow-Following Grammar",
        "cultural_status": "internal -- Austin-review-needed, not public-ready",
        "source_footage": meta["footage_rel"],
        "analysis_window_s": [meta["start"], meta["start"] + meta["dur"]],
        "analysis_resolution": [AW, AH],
        "render_resolution": [W, H],
        "optical_flow": {
            "method": "dense pyramidal Lucas-Kanade (numpy + scipy.ndimage)",
            "pyramid_levels": 3,
            "flow_pairs_aggregated": meta["n_pairs"],
            "note": "apparent image-space motion (camera + subject + current), "
                    "an optical-flow proxy -- not a fluid-physics measurement",
        },
        "phrase_grammar": "circle (origin) -> crescent -> crescent -> trigon (release)",
        "primitive_roles": {
            "circle": "source / eddy / pressure node / impact",
            "crescent": "shear front / wavefront / expansion band",
            "trigon": "release / attenuation / directional tip",
        },
        "streamlines": {
            "role": "phrases travel dominant current / motion paths",
            "count": len(ctx["streamlines"]),
            "seeds_rejected_nms": ctx["rej_streamlines"],
            "seeds": ctx["seeds"],
        },
        "eddy_nodes": {
            "role": "curl / vorticity maxima -> circle pivot + orbiting phrase",
            "count": len(ctx["nodes"]),
            "peaks_rejected_nms": ctx["rej_nodes"],
            "nodes": [{k: v for k, v in nd.items() if k not in ("xy", "sign")}
                      for nd in ctx["nodes"]],
        },
        "wavefront_sites": {
            "role": "strain / shear maxima -> crescent wavefronts + trigon release",
            "count": len(ctx["sites"]),
            "peaks_rejected_nms": ctx["rej_sites"],
            "sites": [{k: v for k, v in st.items() if k not in ("xy", "angle")}
                      for st in ctx["sites"]],
        },
    }
    (outdir / "structures_v003.json").write_text(json.dumps(data, indent=2),
                                                 encoding="utf-8")
    return data


def write_readme(outdir, layers, composite, sheet_size, debug_titles, n_frames,
                 ctx, meta):
    L = []
    a = L.append
    a("# Water Flow Phrase Grammar v003 - 2026-05-20")
    a("")
    a("INTERNAL ONLY until Austin reviews. Black-background additive layer clips")
    a("plus one low-opacity composite preview over real footage. No SD / LoRA /")
    a("style transfer, no topology / cymatics / seed-of-life construction geometry,")
    a("no fish or animal glyphs, no prompt scenes, no randomness. Not Austin-approved")
    a("and not a public cultural-grammar claim.")
    a("")
    a("## Lane")
    a("")
    a("Water Dynamics / Flow-Following Grammar (Lane 2). This pass answers the")
    a("2026-05-20 overnight review note: the next water-flow pass should use *real")
    a("footage motion fields*, not hand-authored lines only.")
    a("")
    a("## What This Packet Is")
    a("")
    a("v001/v002 placed primitive phrases on hand-authored parametric paths. v003")
    a("runs a dense optical-flow analysis on real Moonfish underwater footage,")
    a("aggregates a mean apparent-motion field, and derives three image-space")
    a("motion quantities that each drive a different primitive-phrase placement:")
    a("")
    a("    velocity  ->  dominant current / motion paths   ->  streamline phrases")
    a("    curl      ->  rotational / eddy areas           ->  orbiting eddy phrases")
    a("    strain    ->  stretching / shear zones          ->  wavefront phrases")
    a("")
    a("The phrase grammar is unchanged:")
    a("")
    a("    circle (origin)  ->  crescent  ->  crescent  ->  trigon (release)")
    a("")
    a("    circle   = source / eddy / pressure node / impact")
    a("    crescent = shear front / wavefront / expansion band")
    a("    trigon   = release / attenuation / directional tip")
    a("")
    a("The motion *structure* (streamlines, eddy nodes, wavefront sites) is")
    a("extracted once from the aggregated field and held fixed; only the phrases")
    a("animate along it. This is deterministic, loops seamlessly, and keeps strict")
    a("common fate -- no random scatter, no independent jitter.")
    a("")
    a("## Source Footage")
    a("")
    a(f"- File: `{meta['footage_rel']}`")
    a(f"- Analysis + composite window: t = {meta['start']:.1f}s to "
      f"{meta['start'] + meta['dur']:.1f}s ({meta['dur']:.1f}s).")
    a("- Content: a dense salmon-school open-water clip from the Moonfish")
    a("  underwater set (same set v002 used). Cropped with "
      f"`{FOOTAGE_CROP}` to drop the burned-in source-timecode strip.")
    a("- Window choice: v002's composite used t=28s, but that window is a")
    a("  near-static sun-up shot (measured frame-motion ~1.2, almost no optical")
    a("  flow to analyse). v003 needs real motion, so a motion probe across the")
    a("  428s clip selected t=160s, where motion energy and spatial structure")
    a("  both peak. The footage there is a dense salmon school, so the optical")
    a("  flow is dominated by the school's collective motion plus camera drift.")
    a("- Not used / not mislabeled here: the separate hero subclip")
    a("  `H6_kelp_forest_floor.mp4` is the known-mislabeled file (named kelp,")
    a("  actually salmon); v003 reads the correctly-named source file directly.")
    a("")
    a("## Method")
    a("")
    a("1. Decode the cropped footage window to a 24fps grayscale stack at "
      f"{AW}x{AH}.")
    a("2. Dense pyramidal Lucas-Kanade optical flow (3-level, numpy + "
      "scipy.ndimage; no OpenCV) on every consecutive frame pair.")
    a(f"3. Aggregate the mean apparent-motion field over {meta['n_pairs']} flow")
    a("   pairs. Transient darts average out; the persistent current / drift /")
    a("   collective-motion component survives.")
    a("4. Derive divergence, curl, and strain as image-space motion descriptors")
    a("   (translation-invariant differential operators -- a uniform camera pan")
    a("   contributes zero curl/strain, so these isolate the non-uniform")
    a("   structure: eddies and shear).")
    a("5. Extract deterministic structure: streamline seeds in strong mean-flow")
    a("   regions (RK2 integration), eddy nodes at |curl| maxima, wavefront")
    a("   sites at strain maxima -- all NMS-separated, ranked by field value.")
    a("6. Render circle/crescent/trigon phrases that travel / orbit / propagate")
    a("   along that fixed structure, on pure black, additive.")
    a("")
    a("This is NOT a fluid-physics claim. Optical flow measures apparent")
    a("image-space motion (camera drift + subject motion + current, combined).")
    a("The words divergence / curl / strain are image-plane motion descriptors")
    a("-- an optical-flow proxy, not a measurement of literal water compression.")
    a("")
    a("## Outputs")
    a("")
    a("### Black-screen additive layers (primary deliverable)")
    a("")
    for c in layers:
        pr, nb = c["ffprobe"], c["nonblank"]
        a(f"**{c['scene']}.mp4**")
        a("")
        a(f"- {c['desc']}")
        a("- Layer role: Resolume Screen/Additive blend over footage or black.")
        a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
          f"duration {pr['duration']:.3f}s, frames {pr['frames']}, "
          f"codec {pr['codec']}, {pr['size_kb']} KB")
        a(f"- Nonblank check: midpoint max luma {nb['max_luma']}, "
          f"nonblack pixels {nb['nonblack_px']}")
        a("")
    a("### Composite preview (review aid, not the deliverable)")
    a("")
    if composite:
        pr = composite["ffprobe"]
        a(f"**{composite['name']}.mp4**")
        a("")
        a(f"- {composite['desc']}")
        a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
          f"duration {pr['duration']:.3f}s, frames {pr['frames']}, "
          f"codec {pr['codec']}, {pr['size_kb']} KB")
        a("- The layer was derived from this exact footage window, so the")
        a("  streamline phrases ride the school's actual collective motion.")
        a(f"- Layer added at ~{int(round(meta['opacity'] * 100))}% additive over")
        a("  dimmed footage. Only the layer loops seamlessly; the footage plays")
        a("  forward once. In production, layer the black-screen clip in Resolume.")
        a("")
    else:
        a("(No composite in this run -- footage not found; black-screen layers")
        a(" render regardless.)")
        a("")
    a("## Extracted Structure")
    a("")
    a(f"- Streamlines (current paths): {len(ctx['streamlines'])} "
      f"({ctx['rej_streamlines']} candidate seeds rejected by NMS / length).")
    a(f"- Eddy nodes (|curl| maxima): {len(ctx['nodes'])} "
      f"({ctx['rej_nodes']} peaks rejected by NMS).")
    a(f"- Wavefront sites (strain maxima): {len(ctx['sites'])} "
      f"({ctx['rej_sites']} peaks rejected by NMS).")
    a("- Full per-structure role data: `structures_v003.json`.")
    a("")
    a("## Review Order")
    a("")
    a("1. `debug/debug_contact_sheet.png` first -- it proves every primitive")
    a("   sits on a field quantity (flow vectors, streamlines, curl nodes,")
    a("   strain sites), not on decorative scatter.")
    a("2. `motion_field_current_layer_v003.mp4` on black -- the cleanest read")
    a("   of footage-derived current following.")
    a("3. `curl_eddy_nodes_layer_v003.mp4` on black -- rotational / eddy phrases.")
    a("4. `strain_shear_wavefront_layer_v003.mp4` on black -- shear wavefronts.")
    a("5. `motion_field_current_composite_v003__over_moonfish-water.mp4` -- the")
    a("   review-friendly clip: layer 1 over the footage it was derived from.")
    a("6. `contact_sheet_v003.png` for a single-image overview.")
    a("")
    a("## Caveats")
    a("")
    a("- Optical flow is apparent image-space motion -- camera drift, subject")
    a("  motion, and current are combined and cannot be separated here.")
    a("- divergence / curl / strain are optical-flow proxies, not fluid physics.")
    a("- The analysis window is a dense salmon school; the mean field is")
    a("  school-dominated. The footage contains fish, but the renderer draws")
    a("  only abstract circle/crescent/trigon primitives -- never a fish glyph.")
    a("- In the composite, circle nodes may land near fish in the footage.")
    a("  They are motion-field nodes, not eyes or body-centers (see Austin Q4).")
    a("- Lucas-Kanade is noisy per pair on a dense, self-occluding school;")
    a("  aggregation + smoothing trade spatial detail for stable structure,")
    a("  which suits sparse phrase placement.")
    a("- Structure is deterministic for a given footage window; re-running")
    a("  reproduces it exactly. No randomness anywhere in the pipeline.")
    a("- INTERNAL R&D only. Not Austin-approved, not public-ready, no cultural")
    a("  claim. circle/crescent/trigon are morphology classes here, not symbols.")
    a("")
    a("## Open Questions For Austin")
    a("")
    a("1. Crescent orientation still cups *back toward the origin* "
      "(v002 Austin Q open).")
    a("2. Does footage-derived placement (real optical flow) read better than")
    a("   v002's hand-authored streamlines, or is the hand-authored version")
    a("   cleaner / calmer?")
    a("3. Do the three motion quantities -- current paths, eddy rotation, shear")
    a("   wavefronts -- read as a meaningful water grammar, or is curl/strain")
    a("   too abstract to lead with?")
    a("4. In the composite, circle nodes sometimes sit over a fish school. Is a")
    a("   motion-field circle over (not on) animal motion acceptable, or should")
    a("   nodes be suppressed where the footage shows bodies?")
    a("")
    a("## Constraints Honored")
    a("")
    a("- Placement derived only from field quantities / paths -- no random scatter.")
    a("- No fish or animal glyphs; no named, chief, or supernatural beings.")
    a("- No topology / cymatics / seed-of-life construction geometry.")
    a("- No prompt scenes; no SD / LoRA / style transfer.")
    a("- Sparse, projector-readable; every phrase is followable start to end.")
    a("- Outputs written only to this folder and "
      "`scripts/water_flow_phrase_grammar_v003.py`.")
    a("")
    a("## Evidence")
    a("")
    a("- Debug overlays: `debug/` -- " + ", ".join(debug_titles).lower() + ".")
    a("- Debug contact sheet: `debug/debug_contact_sheet.png`.")
    a("- Deliverable contact sheet: "
      f"`contact_sheet_v003.png` ({sheet_size[0]}x{sheet_size[1]}).")
    a("- Midpoint stills: `midpoint_stills/` (1920x1080 PNG per clip).")
    a("- Per-structure sidecar: `structures_v003.json`.")
    a("- Verification: `py_compile` on the script; `ffprobe` on every MP4;")
    a("  nonblank checks on every midpoint still (see per-clip data above).")
    a("")
    a("## Sources Read")
    a("")
    a("- docs/space-center/overnight-visual-review-notes-2026-05-20.md")
    a("- docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md")
    a("- docs/space-center/primitive-pattern-language-canon-2026-05-20.md")
    a("- track2-deterministic/morph_outputs_INTERNAL/"
      "water_flow_phrase_grammar_v002_2026-05-20/README.md")
    a("- Meetings/The Salish Sea Dreaming/"
      "2026-05-18 The Salish Sea Dreaming Meeting 2.md")
    a("")
    a("## Regenerate")
    a("")
    a("    python3 scripts/water_flow_phrase_grammar_v003.py")
    a("")
    (outdir / "README.md").write_text("\n".join(L), encoding="utf-8")


# ==========================================================================
# main
# ==========================================================================
LAYER_DESC = {
    "motion_field_current_layer_v003":
        "Sparse phrase bundles ride the streamlines traced through the mean "
        "apparent-motion field -- phrases follow the footage's dominant "
        "current / motion paths.",
    "curl_eddy_nodes_layer_v003":
        "Each |curl| maximum becomes an eddy node: a pulsing circle pivot with "
        "one crescent/crescent/trigon phrase orbiting it; rotation sense "
        "follows the sign of curl, crescents cup inward, trigon releases "
        "tangentially.",
    "strain_shear_wavefront_layer_v003":
        "Each strain maximum emits a phrase propagating along its principal "
        "stretch axis: a circle origin, two crescent wavefronts expanding "
        "outward, and a trigon release at the leading edge, attenuating with "
        "age.",
}


def assign_bundles(streamlines):
    """One phrase bundle per streamline, plus a second on the longest one, so
    the current field reads as populated but stays sparse and followable."""
    if not streamlines:
        return []
    longest = max(range(len(streamlines)), key=lambda i: streamlines[i].total)
    bundles = []
    for i in range(len(streamlines)):
        n_b = 2 if i == longest else 1
        bundles.append((i, n_b, (i * 0.37) % 1.0))
    return bundles


def main():
    repo = Path(__file__).resolve().parents[1]
    default_out = (repo / "track2-deterministic" / "morph_outputs_INTERNAL"
                   / "water_flow_phrase_grammar_v003_2026-05-20")
    moon = repo / "media" / "collaborators" / "moonfish-video" / "underwater"

    ap = argparse.ArgumentParser(description="Water-flow phrase grammar v003 -- "
                                             "optical-flow-driven primitive overlays.")
    ap.add_argument("--outdir", default=str(default_out))
    ap.add_argument("--footage", default=str(moon / "P1099653.mp4"),
                    help="Moonfish open-water footage for analysis + composite")
    ap.add_argument("--start", type=float, default=160.0,
                    help="footage window start (s); 160 = peak motion structure")
    ap.add_argument("--dur", type=float, default=DUR_S)
    ap.add_argument("--frames", type=int, default=N_FRAMES,
                    help="render frame count")
    ap.add_argument("--flow-stride", type=int, default=1,
                    help="use every Nth consecutive frame pair for flow")
    ap.add_argument("--opacity", type=float, default=0.80,
                    help="composite additive opacity")
    ap.add_argument("--no-composite", action="store_true")
    ap.add_argument("--smoke", action="store_true",
                    help="fast pipeline test: few frames, strided flow")
    args = ap.parse_args()

    if args.smoke:
        args.frames = 24
        args.flow_stride = 6

    assert AW % 4 == 0 and AH % 4 == 0, "analysis res must allow 3 clean pyramid levels"
    n_frames = max(2, args.frames)
    outdir = Path(args.outdir)
    (outdir / "midpoint_stills").mkdir(parents=True, exist_ok=True)
    footage = Path(args.footage)

    print(f"water_flow_phrase_grammar_v003 -> {outdir}")
    print(f"  {W}x{H}  {FPS}fps  {n_frames} frames  ({n_frames / FPS:.3f}s)")
    print(f"  footage: {footage.name}  window [{args.start:.1f}s, "
          f"{args.start + args.dur:.1f}s]\n")

    # ---- optical flow analysis ----
    if not footage.exists():
        print(f"ERROR: footage not found -- {footage}")
        return 1
    t0 = time.time()
    print("OPTICAL FLOW ANALYSIS")
    frames = extract_gray_frames(footage, args.start, args.dur, AW, AH)
    print(f"  decoded {len(frames)} grayscale frames at {AW}x{AH}")
    mean_u, mean_v, n_pairs = aggregate_flow(frames, args.flow_stride)
    print(f"  aggregated {n_pairs} Lucas-Kanade flow pairs in "
          f"{time.time() - t0:4.1f}s")
    fields = derive_fields(mean_u, mean_v)
    print(f"  mean |flow| max {np.sqrt(mean_u**2 + mean_v**2).max():.3f}  "
          f"|curl| max {np.abs(fields['curl']).max():.4f}  "
          f"strain max {fields['strain'].max():.4f}")

    # ---- deterministic structure extraction ----
    streamlines, seeds, rej_sl = extract_streamlines(fields, max_lines=5)
    nodes, rej_nd = extract_eddy_nodes(fields, max_nodes=5)
    sites, rej_st = extract_wavefront_sites(fields, max_sites=4)
    print(f"  structure: {len(streamlines)} streamlines, {len(nodes)} eddy "
          f"nodes, {len(sites)} wavefront sites\n")

    ctx = {
        "streamlines": streamlines, "seeds": seeds, "rej_streamlines": rej_sl,
        "nodes": nodes, "rej_nodes": rej_nd,
        "sites": sites, "rej_sites": rej_st,
        "bundles": assign_bundles(streamlines),
    }
    meta = {
        "footage_rel": str(footage.relative_to(repo)) if footage.is_relative_to(repo)
                       else str(footage),
        "start": args.start, "dur": args.dur, "n_pairs": n_pairs,
        "opacity": args.opacity,
    }

    # ---- debug evidence ----
    debug_titles = render_debug_images(outdir, fields, ctx, n_pairs)
    print("  debug overlays + contact sheet written")
    write_sidecar(outdir, ctx, meta)
    print("  structures_v003.json written\n")

    # ---- primary black-screen layers ----
    print("RENDER")
    layers, layer_still = [], {}
    for scene in SCENES:
        mid = render_scene(scene, outdir, n_frames, ctx)
        layer_still[scene] = mid
        layers.append({"scene": scene, "desc": LAYER_DESC[scene],
                        "ffprobe": ffprobe_check(outdir / f"{scene}.mp4"),
                        "nonblank": nonblank_check(mid)})

    # ---- composite preview ----
    composite, comp_still = None, None
    if not args.no_composite:
        name = "motion_field_current_composite_v003__over_moonfish-water"
        still = make_composite(outdir / "motion_field_current_layer_v003.mp4",
                               footage, args.start, args.opacity, -0.20,
                               outdir / f"{name}.mp4", n_frames)
        if still is not None:
            comp_still = still
            composite = {
                "name": name,
                "desc": "motion_field_current_layer over the Moonfish open-water "
                        "footage window it was derived from (P1099653, "
                        f"t={args.start:.0f}s).",
                "ffprobe": ffprobe_check(outdir / f"{name}.mp4"),
            }

    # ---- contact sheet ----
    pct = int(round(args.opacity * 100))
    panels = [
        ("motion_field_current_layer_v003", "layer-only (black screen)",
         layer_still.get("motion_field_current_layer_v003")),
        ("curl_eddy_nodes_layer_v003", "layer-only (black screen)",
         layer_still.get("curl_eddy_nodes_layer_v003")),
        ("strain_shear_wavefront_layer_v003", "layer-only (black screen)",
         layer_still.get("strain_shear_wavefront_layer_v003")),
        ("current composite over Moonfish water", f"preview ~{pct}% additive",
         comp_still),
    ]
    sheet_size = build_contact_sheet(panels, outdir / "contact_sheet_v003.png")
    print(f"  contact sheet: {sheet_size[0]}x{sheet_size[1]}")
    write_readme(outdir, layers, composite, sheet_size, debug_titles,
                 n_frames, ctx, meta)
    print("  README.md written\n")

    # ---- verification ----
    print("VERIFICATION SUMMARY")
    ok = True
    allclips = [(c["scene"], c["ffprobe"], c["nonblank"]) for c in layers]
    if composite:
        allclips.append((composite["name"], composite["ffprobe"], None))
    for name, pr, nb in allclips:
        checks = {
            "1920x1080": pr["width"] == 1920 and pr["height"] == 1080,
            "24fps": abs(pr["fps"] - 24.0) < 0.01,
            f"{n_frames}frames": pr["frames"] == n_frames,
            "duration": abs(pr["duration"] - n_frames / FPS) < 0.06,
            "h264": pr["codec"] == "h264",
        }
        if nb is not None:
            checks["nonblank"] = nb["max_luma"] > 16 and nb["nonblack_px"] > 1000
        passed = all(checks.values())
        ok = ok and passed
        flags = " ".join(k for k, v in checks.items() if v)
        fail = " ".join("!" + k for k, v in checks.items() if not v)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {flags} {fail}".rstrip())
    n_struct = len(streamlines) + len(nodes) + len(sites)
    print(f"  [{'PASS' if n_struct > 0 else 'FAIL'}] structure extracted: "
          f"{n_struct} total primitives' placements field-derived")
    ok = ok and n_struct > 0
    print(f"\n{'ALL CHECKS PASSED' if ok else 'CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
