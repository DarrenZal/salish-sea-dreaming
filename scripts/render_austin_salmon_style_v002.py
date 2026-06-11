#!/usr/bin/env python3.11
"""Austin-informed salmon style study v002 - 8 stills.

Refines v001. Key correction: the design is no longer limited to the literal
circle / crescent / trigon primitives. v002 builds richer Austin-like derived
forms, observed from `Animal_Salmon_Spawn_Eggs`:

  - S-crescents (double-curved strokes) for elegant negative-space channels
  - soft ovoids for eye sockets and interior masses
  - smooth tapered strokes for white negative-space rivers
  - smooth continuous body masses with curved (not geometric) mass seams
  - curved trigons / rays for fins and tail lobes
  - clustered organic roe fields

These forms are derived from observing the specific source artwork; they are
internal procedural sketches and are NOT presented as a named cultural grammar.

Outputs 8 PNG stills (no MP4) to:
  track2-deterministic/morph_outputs_INTERNAL/
    austin_informed_salmon_style_study_v002_2026-05-19/

INTERNAL ONLY. Not Austin-approved. No SD/LoRA. Not exact copies of the source.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from primitive_water_grammar_v1 import ROOT, draw_poly_alpha

OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/austin_informed_salmon_style_study_v002_2026-05-19"
S = 1120

# Source palette (RGB), read from the source SVG fills.
BG = (243, 238, 238)
RED = (235, 79, 61)
RED_DARK = (120, 73, 63)
ROE_ORANGE = (255, 94, 59)
ROE_WARM = (236, 96, 64)
ROE_DARK = (135, 84, 81)
GREY_WARM = (181, 161, 154)
GREY_DARK = (104, 100, 97)
WHITE = (255, 255, 255)
INK = (38, 33, 34)

RED_PAL = (RED, RED_DARK)
GREY_PAL = (GREY_WARM, GREY_DARK)

# Smooth, symmetric body width profile (head t=0 -> peduncle t=1).
WIDTH = [
    (0.00, 0.05), (0.08, 0.42), (0.18, 0.74), (0.33, 0.94),
    (0.52, 0.82), (0.69, 0.52), (0.84, 0.30), (1.00, 0.12),
]


def canvas() -> np.ndarray:
    f = np.empty((S, S, 3), np.uint8)
    f[:, :] = (BG[2], BG[1], BG[0])
    return f


def smoothstep(f: float) -> float:
    f = max(0.0, min(1.0, f))
    return f * f * (3.0 - 2.0 * f)


def width_at(t: float) -> float:
    t = max(0.0, min(1.0, t))
    for i in range(1, len(WIDTH)):
        t0, w0 = WIDTH[i - 1]
        t1, w1 = WIDTH[i]
        if t <= t1:
            f = smoothstep((t - t0) / (t1 - t0)) if t1 > t0 else 0.0
            return w0 + (w1 - w0) * f
    return WIDTH[-1][1]


def cubic(p0, p1, p2, p3, n=140):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def quad(p0, p1, p2, n=40):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def s_path(p0, p3, bow, n=40):
    """A double-curved S path between two points - the spine of an S-crescent."""
    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
    px, py = -dy, dx
    L = math.hypot(dx, dy) or 1.0
    p1 = (p0[0] + dx * 0.30 + px / L * bow, p0[1] + dy * 0.30 + py / L * bow)
    p2 = (p0[0] + dx * 0.70 - px / L * bow, p0[1] + dy * 0.70 - py / L * bow)
    return cubic(p0, p1, p2, p3, n)


def ring_arc(center, radius, a0_deg, sweep_deg, n=140):
    out = []
    for i in range(n):
        a = math.radians(a0_deg + sweep_deg * i / (n - 1))
        out.append((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)))
    return out


def polyline_tangent(pts, i):
    if i <= 0:
        a, b = pts[0], pts[1]
    elif i >= len(pts) - 1:
        a, b = pts[-2], pts[-1]
    else:
        a, b = pts[i - 1], pts[i + 1]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def spine_point(spine, t):
    f = max(0.0, min(1.0, t)) * (len(spine) - 1)
    i = int(f)
    if i >= len(spine) - 1:
        return spine[-1]
    fr = f - i
    return (spine[i][0] + (spine[i + 1][0] - spine[i][0]) * fr,
            spine[i][1] + (spine[i + 1][1] - spine[i][1]) * fr)


def spine_tangent(spine, t):
    return polyline_tangent(spine, int(max(0.0, min(1.0, t)) * (len(spine) - 1)))


def fill_poly(frame, pts, rgb, alpha, *, outline_alpha=0.0, ow=2):
    draw_poly_alpha(frame, np.asarray(pts, dtype=np.float32), rgb, alpha=alpha,
                    outline_rgb=INK, outline_alpha=outline_alpha, outline_thickness=ow)


def disc(frame, center, r, rgb, alpha, *, outline_alpha=0.0):
    pts = [(center[0] + r * math.cos(2 * math.pi * i / 64),
            center[1] + r * math.sin(2 * math.pi * i / 64)) for i in range(64)]
    fill_poly(frame, pts, rgb, alpha, outline_alpha=outline_alpha)


def ovoid(frame, center, rx, ry, angle, rgb, alpha, *, flatten=0.34, outline_alpha=0.0):
    """A soft ovoid: fuller convex top, flatter bottom, rounded corners."""
    c, s = math.cos(angle), math.sin(angle)
    pts = []
    for i in range(72):
        th = 2 * math.pi * i / 72
        x = rx * math.cos(th)
        sy = math.sin(th)
        y = -ry * sy if sy >= 0 else -ry * sy * (1.0 - flatten)
        pts.append((center[0] + x * c - y * s, center[1] + x * s + y * c))
    fill_poly(frame, pts, rgb, alpha, outline_alpha=outline_alpha)


def smooth_stroke(frame, path, width_fn, rgb, alpha, *, outline_alpha=0.0):
    """A tapered stroke along an arbitrary smooth path - the v002 workhorse.

    Used for elegant white channels, S-crescents, curved rays, and fins, by
    varying `width_fn(f)` (the half-width at path fraction f)."""
    n = len(path)
    if n < 3:
        return
    left, right = [], []
    for i, p in enumerate(path):
        f = i / (n - 1)
        w = width_fn(f)
        a = polyline_tangent(path, i)
        nx, ny = -math.sin(a), math.cos(a)
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    fill_poly(frame, left + right[::-1], rgb, alpha, outline_alpha=outline_alpha, ow=1)


def w_channel(peak):
    """Holds near full width through the middle, tapers to fine points."""
    return lambda f: peak * smoothstep(min(f, 1.0 - f) * 2.7)


def w_leaf(peak):
    """Fuller in the middle, fine points at both ends - a feather / S-crescent."""
    return lambda f: peak * (1.0 - (2.0 * f - 1.0) ** 2) ** 0.72


def w_ray(base):
    """Wide at the base (f=0), tapering to a fine point at the tip (f=1)."""
    return lambda f: base * (1.0 - f) ** 0.66 * smoothstep((1.0 - f) * 7.0 + 0.2)


def body_edges(spine, max_hw):
    n = len(spine)
    dors, vent = [], []
    for i, p in enumerate(spine):
        t = i / (n - 1)
        a = polyline_tangent(spine, i)
        nx, ny = -math.sin(a), math.cos(a)
        hw = width_at(t) * max_hw
        dors.append((p[0] + nx * hw, p[1] + ny * hw))
        vent.append((p[0] - nx * hw, p[1] - ny * hw))
    return dors, vent


def head_mass(frame, spine, dors, vent, max_hw, k_t, rgb):
    """A darker head colour mass with a CURVED rear seam, not a straight cut."""
    n = len(spine)
    k = int(k_t * (n - 1))
    seam_tan = spine_tangent(spine, k_t)
    bulge = max_hw * 0.5
    ctrl = (spine_point(spine, k_t)[0] + math.cos(seam_tan) * bulge,
            spine_point(spine, k_t)[1] + math.sin(seam_tan) * bulge)
    seam = quad(dors[k], ctrl, vent[k], 30)
    poly = dors[:k + 1] + seam + vent[:k + 1][::-1]
    fill_poly(frame, poly, rgb, 0.96)


def curved_ray(frame, base, tip, base_w, bow, rgb, alpha):
    """A curved tapered ray: wide curved base, fine point - fin / tail lobe."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    px, py = -dy, dx
    L = math.hypot(dx, dy) or 1.0
    ctrl = ((base[0] + tip[0]) / 2 + px / L * bow, (base[1] + tip[1]) / 2 + py / L * bow)
    smooth_stroke(frame, quad(base, ctrl, tip, 30), w_ray(base_w), rgb, alpha,
                  outline_alpha=0.32)


def draw_tail(frame, peduncle, axis, max_hw, base_rgb):
    """A clean curved forked tail with white S-crescent negative space inside."""
    ax = (math.cos(axis), math.sin(axis))
    pp = (-math.sin(axis), math.cos(axis))

    def pt(along, across):
        return (peduncle[0] + ax[0] * along + pp[0] * across,
                peduncle[1] + ax[1] * along + pp[1] * across)

    ped_half = width_at(0.98) * max_hw
    span = max_hw * 0.86
    length = max_hw * 1.5
    mid_out = ped_half + (span - ped_half) * 0.5 + max_hw * 0.16
    poly = [pt(0, ped_half), pt(length * 0.5, mid_out), pt(length, span),
            pt(length * 0.55, 0.0), pt(length, -span),
            pt(length * 0.5, -mid_out), pt(0, -ped_half)]
    fill_poly(frame, poly, base_rgb, 0.97, outline_alpha=0.42, ow=2)
    for sgn in (1, -1):
        a = pt(length * 0.18, sgn * ped_half * 0.5)
        b = pt(length * 0.84, sgn * span * 0.62)
        smooth_stroke(frame, s_path(a, b, sgn * max_hw * 0.12, 26),
                      w_leaf(max_hw * 0.1), WHITE, 0.9)


def draw_eye(frame, pos, r, angle):
    """A bold concentric eye seated in a soft ovoid socket, with an S-brow."""
    ovoid(frame, pos, r * 1.7, r * 1.42, angle, WHITE, 0.95, flatten=0.3)
    disc(frame, pos, r, INK, 1.0)
    disc(frame, pos, r * 0.66, WHITE, 1.0)
    disc(frame, pos, r * 0.32, INK, 1.0)
    disc(frame, (pos[0] - math.sin(angle) * r * 0.24, pos[1] - math.cos(angle) * r * 0.24),
         r * 0.12, WHITE, 0.95)
    brow_c = (pos[0] + math.sin(angle) * r * 1.7, pos[1] - math.cos(angle) * r * 1.7)
    bd = (math.cos(angle), math.sin(angle))
    smooth_stroke(frame, s_path((brow_c[0] - bd[0] * r * 1.5, brow_c[1] - bd[1] * r * 1.5),
                                (brow_c[0] + bd[0] * r * 1.5, brow_c[1] + bd[1] * r * 1.5),
                                r * 0.5, 26), w_leaf(r * 0.2), INK, 0.7)


def draw_jaw(frame, spine, max_hw, dorsal_sign):
    """An open jaw at the snout: a dark gape with white curved-trigon teeth."""
    snout = spine_point(spine, 0.0)
    a = spine_tangent(spine, 0.06)
    fwd = a + math.pi
    nx, ny = -math.sin(a) * dorsal_sign, math.cos(a) * dorsal_sign
    gape_c = (snout[0] + math.cos(fwd) * max_hw * 0.16 + nx * max_hw * 0.34,
              snout[1] + math.sin(fwd) * max_hw * 0.16 + ny * max_hw * 0.34)
    back = (gape_c[0] - math.cos(fwd) * max_hw * 0.66, gape_c[1] - math.sin(fwd) * max_hw * 0.66)
    smooth_stroke(frame, quad(gape_c, ((gape_c[0] + back[0]) / 2 + nx * max_hw * 0.1,
                                       (gape_c[1] + back[1]) / 2 + ny * max_hw * 0.1), back, 24),
                  w_leaf(max_hw * 0.2), INK, 0.78)
    for k in (-1, 0, 1, 2):
        f = k * 0.2
        tc = (gape_c[0] - math.cos(fwd) * max_hw * 0.14 * (k + 1.5) + nx * max_hw * 0.02,
              gape_c[1] - math.sin(fwd) * max_hw * 0.14 * (k + 1.5) + ny * max_hw * 0.02)
        tip = (tc[0] - nx * max_hw * 0.17, tc[1] - ny * max_hw * 0.17)
        curved_ray(frame, (tc[0] + nx * max_hw * 0.05, tc[1] + ny * max_hw * 0.05),
                   tip, max_hw * 0.085, max_hw * 0.02, WHITE, 0.95)


def draw_salmon(frame, spine, max_hw, pal, *, dorsal_sign=-1.0, jaw=False,
                extra_channels=False):
    """A v002 procedural salmon: smooth body mass, curved head-mass seam,
    elegant S-crescent white channels, curved-ray fins/tail, ovoid-socket eye.
    """
    base, dark = pal
    ds = dorsal_sign
    dors, vent = body_edges(spine, max_hw)
    a_end = spine_tangent(spine, 1.0)

    # tail (behind the body)
    draw_tail(frame, spine[-1], a_end, max_hw, dark)

    # smooth continuous body mass
    fill_poly(frame, dors + vent[::-1], base, 0.98, outline_alpha=0.5, ow=3)

    # darker head colour mass with a curved seam
    head_mass(frame, spine, dors, vent, max_hw, 0.33, dark)

    # elegant S-crescent white negative-space channels
    def edge_pt(t, frac):
        p = spine_point(spine, t)
        a = spine_tangent(spine, t)
        nx, ny = -math.sin(a) * ds, math.cos(a) * ds
        return (p[0] + nx * width_at(t) * max_hw * frac,
                p[1] + ny * width_at(t) * max_hw * frac)

    # operculum channel: crosses the head/body seam
    smooth_stroke(frame, s_path(edge_pt(0.30, 0.95), edge_pt(0.27, -0.95),
                                max_hw * 0.18, 24), w_channel(max_hw * 0.15), WHITE, 0.92)
    # flank S-crescent along the upper body
    smooth_stroke(frame, s_path(edge_pt(0.38, 0.30), edge_pt(0.82, 0.62),
                                max_hw * 0.5, 30), w_leaf(max_hw * 0.17), WHITE, 0.9)
    if extra_channels:
        smooth_stroke(frame, s_path(edge_pt(0.42, -0.34), edge_pt(0.78, -0.56),
                                    -max_hw * 0.42, 30), w_leaf(max_hw * 0.12), WHITE, 0.86)
        smooth_stroke(frame, s_path(edge_pt(0.20, 0.2), edge_pt(0.42, 0.66),
                                    max_hw * 0.34, 26), w_leaf(max_hw * 0.1), WHITE, 0.82)

    # interior ovoid detail form on the shoulder
    sp = spine_point(spine, 0.42)
    ovoid(frame, sp, max_hw * 0.34, max_hw * 0.5, spine_tangent(spine, 0.42) + math.pi / 2,
          dark, 0.5, flatten=0.3)

    if jaw:
        draw_jaw(frame, spine, max_hw, ds)

    # ovoid-socket eye, dorsal-forward on the head
    et = 0.165
    p = spine_point(spine, et)
    a = spine_tangent(spine, et)
    nx, ny = -math.sin(a) * ds, math.cos(a) * ds
    ep = (p[0] + nx * width_at(et) * max_hw * 0.24, p[1] + ny * width_at(et) * max_hw * 0.24)
    draw_eye(frame, ep, max_hw * 0.2, a)


def central_focal(frame, center, r):
    ovoid(frame, center, r * 1.12, r, 0.0, ROE_ORANGE, 0.97, flatten=0.2, outline_alpha=0.3)
    disc(frame, center, r * 0.56, WHITE, 0.97)
    disc(frame, center, r * 0.28, RED_DARK, 1.0)


def roe_field(frame, clumps):
    """Organic clustered roe: power-law size variation, varied clumps, a few
    large edge circles. Never a grid."""
    for cx, cy, spread, count, big, seed in clumps:
        for i in range(count):
            def rnd(salt):
                h = math.sin((seed + i * 1.7) * salt) * 43758.5453
                return h - math.floor(h)
            ang = rnd(12.9898) * 2 * math.pi
            dist = (rnd(78.233) ** 0.62) * spread
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist
            r = 5.0 + (rnd(37.719) ** 2.7) * big
            shade = rnd(53.1)
            col = ROE_ORANGE if shade > 0.34 else (ROE_WARM if shade > 0.14 else ROE_DARK)
            disc(frame, (x, y), r, col, 0.96, outline_alpha=0.2)


def label(frame, text):
    cv2.putText(frame, text, (30, S - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.56,
                (96, 96, 100), 1, cv2.LINE_AA)


# A gentle ring-arc curl: constant radius well above max_hw, so the body
# never self-intersects on the inside of the curve.
COMMA = ring_arc((560, 585), 300, -142, 166)


def study_01_smooth_red():
    frame = canvas()
    draw_salmon(frame, COMMA, 96, RED_PAL, dorsal_sign=-1.0)
    label(frame, "01 smooth red salmon: S-crescent channels, ovoid eye, curved forked tail")
    return "01_smooth_red_salmon_v002.png", frame


def study_02_smooth_grey():
    frame = canvas()
    draw_salmon(frame, COMMA, 96, GREY_PAL, dorsal_sign=-1.0)
    label(frame, "02 smooth grey salmon: same elegant channels and forms in the grey palette")
    return "02_smooth_grey_salmon_v002.png", frame


def study_03_jaw_eye():
    frame = canvas()
    spine = cubic((280, 486), (560, 372), (820, 398), (1000, 600))
    draw_salmon(frame, spine, 122, RED_PAL, dorsal_sign=-1.0, jaw=True)
    label(frame, "03 jaw + eye study: refined open jaw with teeth, ovoid-socket eye")
    return "03_jaw_eye_study_v002.png", frame


def study_04_curved_rays():
    frame = canvas()
    draw_salmon(frame, COMMA, 96, RED_PAL, dorsal_sign=-1.0, extra_channels=True)
    label(frame, "04 curved-ray study: curved trigon/ray fins and tail, layered S-channels")
    return "04_curved_ray_fins_v002.png", frame


def study_05_interlocking_pair():
    frame = canvas()
    cx, cy = S / 2, S / 2
    spine_a = ring_arc((cx, cy), 250, -112, 178)
    spine_b = ring_arc((cx, cy), 250, 68, 178)
    draw_salmon(frame, spine_a, 92, RED_PAL, dorsal_sign=-1.0, jaw=True)
    draw_salmon(frame, spine_b, 92, GREY_PAL, dorsal_sign=-1.0)
    central_focal(frame, (cx, cy), 50)
    label(frame, "05 interlocking pair: red + grey salmon woven around a central focal")
    return "05_interlocking_pair_v002.png", frame


def study_06_interlocking_tight():
    frame = canvas()
    cx, cy = S / 2, S / 2
    spine_a = ring_arc((cx, cy), 214, -120, 196)
    spine_b = ring_arc((cx, cy), 214, 60, 196)
    draw_salmon(frame, spine_a, 84, GREY_PAL, dorsal_sign=-1.0)
    draw_salmon(frame, spine_b, 84, RED_PAL, dorsal_sign=-1.0, jaw=True)
    central_focal(frame, (cx, cy), 44)
    label(frame, "06 interlocking pair tight: closer ring, heads tucked toward tails")
    return "06_interlocking_pair_tight_v002.png", frame


def study_07_roe_single():
    frame = canvas()
    roe = [
        (210, 230, 240, 30, 110, 4.0), (910, 250, 220, 26, 100, 12.0),
        (940, 880, 250, 32, 120, 21.0), (230, 900, 230, 28, 105, 33.0),
        (560, 150, 200, 18, 64, 47.0), (560, 980, 200, 18, 70, 59.0),
    ]
    roe_field(frame, roe)
    draw_salmon(frame, COMMA, 96, RED_PAL, dorsal_sign=-1.0, jaw=True)
    label(frame, "07 roe field: a single salmon among organic clustered roe clouds")
    return "07_roe_field_single_v002.png", frame


def study_08_roe_interlocking():
    frame = canvas()
    cx, cy = S / 2, S / 2
    roe = [
        (150, 150, 260, 36, 140, 5.0), (970, 160, 250, 34, 132, 13.0),
        (980, 970, 270, 38, 145, 23.0), (160, 975, 260, 36, 138, 41.0),
        (560, 96, 210, 18, 78, 53.0), (96, 560, 200, 18, 74, 61.0),
        (1024, 560, 210, 18, 78, 71.0), (560, 1024, 210, 18, 80, 83.0),
    ]
    roe_field(frame, roe)
    spine_a = ring_arc((cx, cy), 250, -112, 178)
    spine_b = ring_arc((cx, cy), 250, 68, 178)
    draw_salmon(frame, spine_a, 92, RED_PAL, dorsal_sign=-1.0, jaw=True)
    draw_salmon(frame, spine_b, 92, GREY_PAL, dorsal_sign=-1.0)
    central_focal(frame, (cx, cy), 50)
    label(frame, "08 roe surround: interlocking pair embedded in a full organic roe field")
    return "08_roe_field_interlocking_v002.png", frame


STUDIES = [
    study_01_smooth_red, study_02_smooth_grey, study_03_jaw_eye, study_04_curved_rays,
    study_05_interlocking_pair, study_06_interlocking_tight,
    study_07_roe_single, study_08_roe_interlocking,
]

STUDY_NOTES = [
    ("01_smooth_red_salmon_v002.png",
     "A smooth red/brown salmon with S-crescent white channels, a curved head-mass seam, an ovoid-socket eye, and a curved-ray tail.",
     "Better than v001: the white channels are S-curved tapered strokes, not geometric sweeps; the head/body seam is curved; the eye sits in a soft ovoid socket. Still off vs source: the source layers more interior formline detail and its channels feather more. Austin: approve the S-crescent channel vocabulary and the ovoid eye."),
    ("02_smooth_grey_salmon_v002.png",
     "The same elegant forms in the warm-grey palette.",
     "Better than v001: smoother contour, elegant channels. Still off: the source grey fish carries denser interior detail than ours. Austin: approve the grey palette and the channel placement."),
    ("03_jaw_eye_study_v002.png",
     "A focus study on a refined open jaw - a dark gape with white curved-trigon teeth - and the ovoid-socket eye, on a broad arc body.",
     "Better than v001: the jaw is an intentional anchored shape with clean curved teeth, not a floating row; the eye is bolder and seated. Still off: the source's jaw integrates into the head silhouette; ours is drawn on top. Austin: approve the jaw/teeth motif and confirm it is acceptable."),
    ("04_curved_ray_fins_v002.png",
     "A study leaning on curved trigon/ray fins and tail lobes with layered S-crescent channels.",
     "Better than v001: fins and tail lobes are curved tapered rays, not straight shards. Still off: the source's terminal forms carry interior negative space; ours are solid. Austin: approve curved rays as the fin/tail vocabulary."),
    ("05_interlocking_pair_v002.png",
     "Two salmon - red and grey - woven on a shared ring around a central focal, a true interlock rather than v001's separate rotation.",
     "Better than v001: the two fish now wrap a shared ring and interlock head-to-tail; the focal is the shared still point. Still off: the source's fish share negative-space channels at the weave; ours meet but do not share channels. Austin: approve the interlocking rotational composition."),
    ("06_interlocking_pair_tight_v002.png",
     "A tighter interlock: a smaller ring, each fish wrapping further so heads tuck toward the other's tail.",
     "Better than v001: a closer, more woven interlock. Still off: at this tightness the bodies crowd the focal; the source keeps the centre clearer. Austin: approve the tighter weave or prefer the looser study 05."),
    ("07_roe_field_single_v002.png",
     "A single salmon among organic clustered roe - power-law size variation, varied clump sizes, warm-shade variation.",
     "Better than v001: the roe clusters are more organic, with stronger size variation and a few large circles. Still off: the source roe wraps the whole composition as a continuous surround; ours is discrete clumps. Austin: approve roe as a general field element."),
    ("08_roe_field_interlocking_v002.png",
     "The interlocking pair embedded in a full organic roe surround - the closest v002 rebuild of the source's whole composition logic.",
     "Better than v001: interlocking fish + central focal + organic roe surround together. Still off: the roe ring is denser at the corners than the source's even cloud wrap; the fish do not share channels. Austin: approve this whole-composition echo and confirm it is clearly NOT presented as his work."),
]


def write_contact_sheet(filenames):
    thumbs = []
    for fn in filenames:
        img = cv2.imread(str(OUT_DIR / fn))
        if img is not None:
            thumbs.append(cv2.resize(img, (420, 420), interpolation=cv2.INTER_AREA))
    if not thumbs:
        return
    rows = []
    for i in range(0, len(thumbs), 4):
        row = thumbs[i:i + 4]
        while len(row) < 4:
            row.append(np.full_like(thumbs[0], 240))
        rows.append(cv2.hconcat(row))
    cv2.imwrite(str(OUT_DIR / "contact_sheet.png"), cv2.vconcat(rows))


def write_readme():
    lines = [
        "# Austin-Informed Salmon Style Study v002 - 2026-05-19",
        "",
        "INTERNAL ONLY. Not Austin-approved. Not Austin-authored. No SD/LoRA. "
        "Procedural studies; not exact copies of the source.",
        "",
        "## Purpose",
        "",
        "Refines v001. The key correction: the design is no longer limited to "
        "literal circle / crescent / trigon primitives. v002 builds richer "
        "Austin-like derived forms observed from `Animal_Salmon_Spawn_Eggs`.",
        "",
        "## Expanded Form Vocabulary",
        "",
        "- S-crescents: double-curved tapered strokes for elegant channels.",
        "- Soft ovoids: for the eye socket and interior shoulder masses.",
        "- Smooth tapered strokes: one stroke-along-a-path generator drives the "
        "white channels, S-crescents, fins, and tail lobes.",
        "- Smooth continuous body masses with CURVED mass seams (the head/body "
        "division is a curve, not a straight cut).",
        "- Curved trigons / rays: for fins and tail lobes.",
        "- Clustered organic roe fields with power-law size variation.",
        "",
        "These forms are derived from observing the specific source artwork. "
        "They are internal procedural sketches and are NOT presented as a named "
        "or canonical cultural grammar; that framing is for Austin to set.",
        "",
        "## What Improved Over v001",
        "",
        "- White channels are S-curved tapered strokes, not geometric sweeps.",
        "- The head/body colour-mass seam is curved, not a straight cut.",
        "- Fins and tail lobes are curved tapered rays, not straight shards.",
        "- The eye sits in a soft ovoid socket with an S-crescent brow.",
        "- The two-salmon studies now genuinely interlock on a shared ring.",
        "- The roe field is more organic.",
        "",
        "## Per-Study Comparison To The Source",
        "",
    ]
    for fn, what, compare in STUDY_NOTES:
        lines.extend([f"### {fn}", "", f"- Study: {what}",
                      f"- Vs source: {compare}", ""])
    lines.extend([
        "## Where v002 Still Falls Short",
        "",
        "- The source layers dense interior formline detail; our bodies are "
        "still comparatively plain.",
        "- The source's two fish share negative-space channels at the weave; "
        "our interlocking pairs meet but do not share channels.",
        "- The source roe wraps the composition as a continuous cloud; ours "
        "clusters in discrete clumps.",
        "- The jaw is drawn on top of the head rather than cut into the "
        "silhouette.",
        "",
        "## What Austin Would Need To Approve",
        "",
        "- The expanded form vocabulary (S-crescents, ovoids, curved rays) and "
        "whether any of it maps to a named cultural grammar.",
        "- Use of the source palette in our outputs.",
        "- The jaw/teeth, ovoid-socket eye, and interlocking-pair composition.",
        "- Roe as a general field element beyond the exact spawn source.",
        "- Confirmation that procedural studies are clearly NOT presented as "
        "Austin's work.",
        "",
        "## Recommendation",
        "",
        "Still do not animate. Take studies 01, 03, and 05 to Austin as the "
        "strongest v002 directions. If the form vocabulary and the interlocking "
        "composition are accepted, a v003 should add interior formline detail "
        "and shared weave-channels before any motion work.",
        "",
        "## Files",
        "",
        "- 8 PNG studies listed above.",
        "- `contact_sheet.png`: all 8 in one 4x2 grid.",
        "",
        "## Scope",
        "",
        "Stills only, no MP4, no animation. No SD, no LoRA. No edits to Agent "
        "B/C/D output folders or to the v001 study. Internal review material; "
        "no public use, no claim of Austin authorship or cultural approval.",
        "",
    ])
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Austin-Informed Salmon Style Study v002 to {OUT_DIR}", flush=True)
    filenames = []
    for study in STUDIES:
        fn, frame = study()
        cv2.imwrite(str(OUT_DIR / fn), frame)
        filenames.append(fn)
        print(f"  rendered {fn}", flush=True)
    write_contact_sheet(filenames)
    write_readme()
    print("Done. 8 stills, contact sheet, and README written.", flush=True)


if __name__ == "__main__":
    main()
