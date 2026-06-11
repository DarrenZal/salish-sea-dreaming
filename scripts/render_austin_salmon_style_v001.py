#!/usr/bin/env python3.11
"""Austin-source-constrained salmon style study v001 - 10 stills.

Replaces the "animate v002 salmon" plan. The v002 morphology studies still read
as generic grey fish; this lane makes the procedural salmon Austin-informed
FIRST, using the source composition logic of `Animal_Salmon_Spawn_Eggs` -
rotational balance, big red/grey/brown colour masses, bold white negative-space
rivers, big focal eyes, and a roe field - before any animation.

Design logic is learned from the source; procedural studies do NOT copy exact
source paths. The two exact-source reference stills ARE source-derived and are
labelled as such.

Outputs 10 PNG stills (no MP4) to:
  track2-deterministic/morph_outputs_INTERNAL/
    austin_informed_salmon_style_study_v001_2026-05-19/

INTERNAL ONLY. Not Austin-approved. No SD/LoRA.
"""
from __future__ import annotations

import math
import subprocess

import cv2
import numpy as np

from primitive_water_grammar_v1 import (
    CRESCENT_BASE,
    ROOT,
    TRIGON_BASE,
    draw_poly_alpha,
    transform_points,
)

OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/austin_informed_salmon_style_study_v001_2026-05-19"
SVG_SRC = ROOT / "track2-deterministic/source-vectors/Animal_Salmon_Spawn_Eggs.svg"
JPG_SRC = ROOT / "austin-v2-ingest/training/Animal_Salmon_Spawn_Eggs.jpg"
RASTER = ROOT / "track2-deterministic/morph_outputs_INTERNAL/.austin_salmon_source_raster.png"
S = 1080

# Source palette, read from the SVG fills (RGB).
BG = (243, 238, 238)        # cls-13 warm tint over white
RED = (235, 79, 61)         # cls-15 red salmon
RED_DARK = (120, 73, 63)    # cls-9 dark brown
ROE_ORANGE = (255, 94, 59)  # cls-8 roe
ROE_DARK = (135, 84, 81)    # cls-14 red-brown roe
GREY_WARM = (181, 161, 154) # cls-10 warm grey body
GREY_MID = (134, 124, 124)  # cls-11 mid grey
GREY_DARK = (97, 97, 97)    # cls-12 dark grey
WHITE = (255, 255, 255)     # cls-7 negative-space channels
INK = (35, 31, 32)          # cls-5 outline

RED_PAL = (RED, RED_DARK)
GREY_PAL = (GREY_WARM, GREY_DARK)

UNIT_CIRCLE = np.array(
    [(math.cos(2 * math.pi * i / 80), math.sin(2 * math.pi * i / 80)) for i in range(80)],
    dtype=np.float32,
)

# Bold, deep Austin-salmon width profile (head t=0 -> peduncle t=1). Dorsal and
# ventral are kept close so the body stays smooth, not lumpy.
WIDTH_DORSAL = [
    (0.00, 0.06), (0.08, 0.46), (0.18, 0.82), (0.33, 0.97),
    (0.52, 0.80), (0.69, 0.50), (0.84, 0.29), (1.00, 0.13),
]
WIDTH_VENTRAL = [
    (0.00, 0.06), (0.08, 0.44), (0.18, 0.80), (0.34, 0.95),
    (0.52, 0.84), (0.68, 0.52), (0.84, 0.30), (1.00, 0.13),
]


def canvas() -> np.ndarray:
    f = np.empty((S, S, 3), np.uint8)
    f[:, :] = (BG[2], BG[1], BG[0])
    return f


def smoothstep(f: float) -> float:
    f = max(0.0, min(1.0, f))
    return f * f * (3.0 - 2.0 * f)


def lerp_knots(knots, t: float) -> float:
    t = max(0.0, min(1.0, t))
    for i in range(1, len(knots)):
        t0, w0 = knots[i - 1]
        t1, w1 = knots[i]
        if t <= t1:
            f = smoothstep((t - t0) / (t1 - t0)) if t1 > t0 else 0.0
            return w0 + (w1 - w0) * f
    return knots[-1][1]


def width_dorsal(t):
    return lerp_knots(WIDTH_DORSAL, t)


def width_ventral(t):
    return lerp_knots(WIDTH_VENTRAL, t)


def cubic(p0, p1, p2, p3, n=120):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
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


def body_edges(spine, max_hw, dorsal_sign):
    n = len(spine)
    dors, vent = [], []
    for i, p in enumerate(spine):
        t = i / (n - 1)
        a = polyline_tangent(spine, i)
        nx = -math.sin(a) * dorsal_sign
        ny = math.cos(a) * dorsal_sign
        dors.append((p[0] + nx * width_dorsal(t) * max_hw, p[1] + ny * width_dorsal(t) * max_hw))
        vent.append((p[0] - nx * width_ventral(t) * max_hw, p[1] - ny * width_ventral(t) * max_hw))
    return dors, vent


def fill_poly(frame, pts, rgb, alpha, *, outline_alpha=0.0, ow=2):
    draw_poly_alpha(frame, np.asarray(pts, dtype=np.float32), rgb, alpha=alpha,
                    outline_rgb=INK, outline_alpha=outline_alpha, outline_thickness=ow)


def disc(frame, center, r, rgb, alpha, *, outline_alpha=0.0):
    p = UNIT_CIRCLE * r
    p[:, 0] += center[0]
    p[:, 1] += center[1]
    fill_poly(frame, p, rgb, alpha, outline_alpha=outline_alpha, ow=2)


def oval(frame, center, rx, ry, angle, rgb, alpha, *, outline_alpha=0.0):
    c, s = math.cos(angle), math.sin(angle)
    p = UNIT_CIRCLE.copy()
    p[:, 0] *= rx
    p[:, 1] *= ry
    p = p @ np.array([[c, -s], [s, c]], dtype=np.float32).T
    p[:, 0] += center[0]
    p[:, 1] += center[1]
    fill_poly(frame, p, rgb, alpha, outline_alpha=outline_alpha)


def crescent(frame, center, size, angle, rgb, alpha, *, outline_alpha=0.0):
    fill_poly(frame, transform_points(CRESCENT_BASE, center, size, angle), rgb, alpha,
              outline_alpha=outline_alpha)


def trigon(frame, center, size, angle, rgb, alpha, *, outline_alpha=0.0):
    fill_poly(frame, transform_points(TRIGON_BASE, center, size, angle), rgb, alpha,
              outline_alpha=outline_alpha)


def big_eye(frame, pos, r, angle):
    """A prominent concentric focal eye: socket ovoid, dark ring, white ring,
    pupil. Prominent but proportionate to the head."""
    oval(frame, pos, r * 1.24, r * 1.06, angle, INK, 0.9)
    disc(frame, pos, r, INK, 1.0)
    disc(frame, pos, r * 0.72, WHITE, 1.0)
    disc(frame, pos, r * 0.34, INK, 1.0)
    disc(frame, (pos[0] - math.sin(angle) * r * 0.26, pos[1] - math.cos(angle) * r * 0.26),
         r * 0.12, WHITE, 0.9)


def draw_mouth(frame, spine, max_hw, ds, teeth):
    """A clean open mouth at the snout: a dark notch, with optional white teeth
    seated inside it - the Austin red-fish jaw cue, anchored not floating."""
    snout = spine_point(spine, 0.0)
    a = spine_tangent(spine, 0.05)
    fwd = a + math.pi
    mc = (snout[0] + math.cos(fwd) * max_hw * 0.05, snout[1] + math.sin(fwd) * max_hw * 0.05)
    trigon(frame, mc, max_hw * 0.30, fwd, INK, 0.62)
    if teeth:
        nx, ny = -math.sin(a) * ds, math.cos(a) * ds
        for k in (-1, 0, 1):
            tp = (mc[0] + math.cos(fwd) * max_hw * 0.05 + nx * k * max_hw * 0.10,
                  mc[1] + math.sin(fwd) * max_hw * 0.05 + ny * k * max_hw * 0.10)
            trigon(frame, tp, max_hw * 0.115, fwd, WHITE, 0.96, outline_alpha=0.3)


def forked_tail(frame, peduncle, axis, ped_half, span, length, base_rgb):
    """A bold fanned crescent/trigon tail carrying white negative-space marks."""
    ax = (math.cos(axis), math.sin(axis))
    pp = (-math.sin(axis), math.cos(axis))
    p_top = (peduncle[0] + pp[0] * ped_half, peduncle[1] + pp[1] * ped_half)
    p_bot = (peduncle[0] - pp[0] * ped_half, peduncle[1] - pp[1] * ped_half)
    up = (peduncle[0] + ax[0] * length + pp[0] * span, peduncle[1] + ax[1] * length + pp[1] * span)
    lo = (peduncle[0] + ax[0] * length - pp[0] * span, peduncle[1] + ax[1] * length - pp[1] * span)
    notch = (peduncle[0] + ax[0] * (length - length * 0.42),
             peduncle[1] + ax[1] * (length - length * 0.42))
    fill_poly(frame, [p_top, up, notch, lo, p_bot], base_rgb, 0.97, outline_alpha=0.4)
    for sgn in (1, -1):
        tipx = peduncle[0] + ax[0] * length * 0.82 + pp[0] * sgn * span * 0.7
        tipy = peduncle[1] + ax[1] * length * 0.82 + pp[1] * sgn * span * 0.7
        rootx = peduncle[0] + ax[0] * length * 0.2 + pp[0] * sgn * ped_half * 0.4
        rooty = peduncle[1] + ax[1] * length * 0.2 + pp[1] * sgn * ped_half * 0.4
        mid = ((tipx + rootx) / 2, (tipy + rooty) / 2)
        crescent(frame, mid, length * 0.5, math.atan2(tipy - rooty, tipx - rootx) + math.pi / 2,
                 WHITE, 0.9)


def white_river(frame, spine, t0, t1, offset_frac, max_hw, dorsal_sign, peak, *, alpha=0.92):
    """A bold white negative-space river sweeping along the body."""
    pts = []
    for i in range(26):
        t = t0 + (t1 - t0) * i / 25
        p = spine_point(spine, t)
        a = spine_tangent(spine, t)
        nx = -math.sin(a) * dorsal_sign
        ny = math.cos(a) * dorsal_sign
        w = width_dorsal(t) if offset_frac >= 0 else width_ventral(t)
        pts.append((p[0] + nx * w * max_hw * offset_frac, p[1] + ny * w * max_hw * offset_frac))
    left, right = [], []
    for i, p in enumerate(pts):
        f = i / 25
        w = peak * smoothstep(min(f, 1.0 - f) * 2.1)
        a = polyline_tangent(pts, i)
        nx, ny = -math.sin(a), math.cos(a)
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    fill_poly(frame, left + right[::-1], WHITE, alpha, ow=0)


def draw_austin_salmon(frame, spine, max_hw, pal, *, dorsal_sign=-1.0,
                       split_mass=True, second_mass=False, jaw=False,
                       river_led=False):
    """A procedural salmon built from Austin's source logic: a bold curled
    colour mass, white negative-space rivers, a big focal eye, a crescent tail.
    """
    base, dark = pal
    ds = dorsal_sign
    n = len(spine)
    dors, vent = body_edges(spine, max_hw, ds)
    a_end = spine_tangent(spine, 1.0)

    # tail behind the body
    forked_tail(frame, spine[-1], a_end, width_dorsal(1.0) * max_hw,
                max_hw * 0.95, max_hw * 1.5, dark)

    # body: one bold continuous colour mass
    fill_poly(frame, dors + vent[::-1], base, 0.98, outline_alpha=0.5, ow=3)

    # split colour masses (head, and optionally a tail-region mass)
    if split_mass:
        k = int(0.34 * (n - 1))
        fill_poly(frame, dors[:k + 1] + vent[:k + 1][::-1], dark, 0.95, outline_alpha=0.0)
    if second_mass:
        k0 = int(0.60 * (n - 1))
        fill_poly(frame, dors[k0:] + vent[k0:][::-1], dark, 0.9)

    # bold white negative-space rivers
    rivers = [
        (0.30, 0.86, 0.40, max_hw * 0.20),
        (0.36, 0.78, -0.42, max_hw * 0.15),
    ]
    if river_led:
        rivers += [
            (0.18, 0.62, 0.0, max_hw * 0.16),
            (0.46, 0.92, 0.66, max_hw * 0.12),
        ]
    for t0, t1, off, peak in rivers:
        white_river(frame, spine, t0, t1, off, max_hw, ds, peak)
    # operculum: a bold white crescent crossing the head/body seam
    op = spine_point(spine, 0.30)
    crescent(frame, op, max_hw * 1.5, spine_tangent(spine, 0.30), WHITE, 0.9)

    # mouth at the snout (clean), with white teeth on the jaw studies
    draw_mouth(frame, spine, max_hw, ds, teeth=jaw)

    # prominent focal eye, dorsal-forward on the head
    ep_t = 0.16
    p = spine_point(spine, ep_t)
    a = spine_tangent(spine, ep_t)
    nx, ny = -math.sin(a) * ds, math.cos(a) * ds
    ep = (p[0] + nx * width_dorsal(ep_t) * max_hw * 0.26,
          p[1] + ny * width_dorsal(ep_t) * max_hw * 0.26)
    big_eye(frame, ep, max_hw * 0.185, a)


def draw_roe(frame, clumps):
    """Deterministic roe field: orange circles, wildly varied scale, clustered
    in cloud-like clumps - never a grid."""
    for ci, (cx, cy, spread, count, big, seed) in enumerate(clumps):
        for i in range(count):
            def rnd(salt):
                h = math.sin((seed + i) * salt) * 43758.5453
                return h - math.floor(h)
            ang = rnd(12.9898) * 2 * math.pi
            dist = (rnd(78.233) ** 0.7) * spread
            x = cx + math.cos(ang) * dist
            y = cy + math.sin(ang) * dist
            rr = rnd(37.719)
            r = 5.0 + (rr ** 2.4) * big
            col = ROE_ORANGE if rnd(9.51) > 0.22 else ROE_DARK
            disc(frame, (x, y), r, col, 0.96, outline_alpha=0.22)


def central_focal(frame, center, r):
    """The small concentric focal at the rotation centre - source's roe-eye."""
    disc(frame, center, r, ROE_ORANGE, 0.97, outline_alpha=0.3)
    disc(frame, center, r * 0.58, WHITE, 0.97)
    disc(frame, center, r * 0.3, RED_DARK, 1.0)


def label(frame, text, *, ref=False):
    y = S - 30
    if ref:
        cv2.rectangle(frame, (0, S - 92), (S, S), (228, 228, 236), -1)
        cv2.putText(frame, "EXACT-SOURCE REFERENCE - internal, not Austin-approved",
                    (28, S - 56), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (40, 40, 120), 2, cv2.LINE_AA)
        cv2.putText(frame, text, (28, y), cv2.FONT_HERSHEY_SIMPLEX, 0.54,
                    (70, 70, 70), 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, text, (28, y), cv2.FONT_HERSHEY_SIMPLEX, 0.56,
                    (96, 96, 100), 1, cv2.LINE_AA)


def load_source_raster():
    """Rasterise the source SVG over the source's warm background."""
    if not RASTER.exists():
        subprocess.run(
            ["magick", "-density", "240", "-background", "#F3EEEE",
             str(SVG_SRC), "-flatten", str(RASTER)],
            check=True,
        )
    img = cv2.imread(str(RASTER))
    if img is None:
        img = cv2.imread(str(JPG_SRC))
    return img


# --- 2 exact-source reference stills --------------------------------------

def study_01_source_full(src):
    frame = canvas()
    m = 70
    fit = cv2.resize(src, (S - 2 * m, S - 2 * m), interpolation=cv2.INTER_AREA)
    frame[m:S - m, m:S - m] = fit
    cv2.rectangle(frame, (m, m), (S - m, S - m), (60, 60, 60), 1)
    label(frame, "01 source full composition - Animal_Salmon_Spawn_Eggs.svg", ref=True)
    return "01_exact_source_full_reference_v001.png", frame


def study_02_source_detail(src):
    frame = canvas()
    h, w = src.shape[:2]
    crop = src[int(h * 0.04):int(h * 0.52), int(w * 0.03):int(w * 0.62)]
    m = 70
    fit = cv2.resize(crop, (S - 2 * m, S - 2 * m), interpolation=cv2.INTER_AREA)
    frame[m:S - m, m:S - m] = fit
    cv2.rectangle(frame, (m, m), (S - m, S - m), (60, 60, 60), 1)
    label(frame, "02 source detail crop - head / focal eye / white channels / jaw", ref=True)
    return "02_exact_source_detail_reference_v001.png", frame


# --- 4 procedural single-salmon studies -----------------------------------

def study_03_red_jaw():
    frame = canvas()
    spine = cubic((448, 308), (742, 392), (726, 706), (486, 840))
    draw_austin_salmon(frame, spine, 132, RED_PAL, dorsal_sign=1.0, jaw=True)
    label(frame, "03 procedural red salmon: curled red/brown body, white rivers, open jaw")
    return "03_procedural_red_jaw_salmon_v001.png", frame


def study_04_grey():
    frame = canvas()
    spine = cubic((448, 308), (742, 392), (726, 706), (486, 840))
    draw_austin_salmon(frame, spine, 132, GREY_PAL, dorsal_sign=1.0)
    label(frame, "04 procedural grey salmon: curled warm-grey body, white rivers, big eye")
    return "04_procedural_grey_salmon_v001.png", frame


def study_05_split_masses():
    frame = canvas()
    spine = cubic((300, 560), (520, 300), (760, 300), (980, 556))
    draw_austin_salmon(frame, spine, 126, RED_PAL, dorsal_sign=-1.0,
                       split_mass=True, second_mass=True)
    label(frame, "05 procedural split masses: red body, brown head and tail masses")
    return "05_procedural_split_masses_salmon_v001.png", frame


def study_06_river_led():
    frame = canvas()
    spine = cubic((448, 308), (742, 392), (726, 706), (486, 840))
    draw_austin_salmon(frame, spine, 132, GREY_PAL, dorsal_sign=1.0, river_led=True)
    label(frame, "06 procedural white-river-led: negative-space channels dominate the body")
    return "06_procedural_white_river_led_salmon_v001.png", frame


# --- 2 two-salmon rotational / yin-yang studies ---------------------------

def study_07_rotational_pair():
    frame = canvas()
    cx, cy = S / 2, S / 2
    spine_a = cubic((360, 322), (628, 352), (672, 560), (548, 706))
    spine_b = [(2 * cx - x, 2 * cy - y) for (x, y) in spine_a]
    draw_austin_salmon(frame, spine_a, 104, RED_PAL, dorsal_sign=1.0, jaw=True)
    draw_austin_salmon(frame, spine_b, 104, GREY_PAL, dorsal_sign=1.0)
    central_focal(frame, (cx, cy), 46)
    label(frame, "07 two-salmon rotational: red + grey in yin-yang balance, central focal")
    return "07_two_salmon_rotational_v001.png", frame


def study_08_rotational_tight():
    frame = canvas()
    cx, cy = S / 2, S / 2
    spine_a = cubic((420, 300), (672, 392), (640, 588), (498, 690))
    spine_b = [(2 * cx - x, 2 * cy - y) for (x, y) in spine_a]
    draw_austin_salmon(frame, spine_a, 96, GREY_PAL, dorsal_sign=1.0)
    draw_austin_salmon(frame, spine_b, 96, RED_PAL, dorsal_sign=1.0, jaw=True)
    central_focal(frame, (cx, cy), 40)
    label(frame, "08 two-salmon rotational tight: closer interlock around the focal")
    return "08_two_salmon_rotational_tight_v001.png", frame


# --- 2 roe / salmon field studies -----------------------------------------

def study_09_single_roe_field():
    frame = canvas()
    spine = cubic((448, 308), (742, 392), (726, 706), (486, 840))
    roe = [
        (250, 250, 230, 26, 95, 4.0), (840, 300, 220, 22, 90, 11.0),
        (860, 800, 250, 28, 110, 19.0), (260, 820, 210, 22, 85, 27.0),
        (560, 560, 150, 16, 42, 33.0),
    ]
    draw_roe(frame, roe)
    draw_austin_salmon(frame, spine, 126, RED_PAL, dorsal_sign=1.0, jaw=True)
    label(frame, "09 roe field: a single salmon among clustered roe clouds")
    return "09_roe_field_single_salmon_v001.png", frame


def study_10_two_salmon_roe_surround():
    frame = canvas()
    cx, cy = S / 2, S / 2
    roe = [
        (170, 170, 240, 30, 130, 5.0), (910, 175, 230, 28, 120, 13.0),
        (915, 905, 250, 32, 135, 23.0), (175, 905, 240, 30, 125, 41.0),
        (540, 120, 200, 20, 70, 53.0), (120, 540, 190, 18, 66, 61.0),
        (960, 540, 200, 20, 70, 71.0), (540, 960, 200, 20, 72, 83.0),
    ]
    draw_roe(frame, roe)
    spine_a = cubic((360, 322), (628, 352), (672, 560), (548, 706))
    spine_b = [(2 * cx - x, 2 * cy - y) for (x, y) in spine_a]
    draw_austin_salmon(frame, spine_a, 104, RED_PAL, dorsal_sign=1.0, jaw=True)
    draw_austin_salmon(frame, spine_b, 104, GREY_PAL, dorsal_sign=1.0)
    central_focal(frame, (cx, cy), 46)
    label(frame, "10 roe surround: two-salmon rotation embedded in a full roe field")
    return "10_two_salmon_roe_surround_v001.png", frame


PROCEDURAL = [
    study_03_red_jaw, study_04_grey, study_05_split_masses, study_06_river_led,
    study_07_rotational_pair, study_08_rotational_tight,
    study_09_single_roe_field, study_10_two_salmon_roe_surround,
]

STUDY_NOTES = [
    ("01_exact_source_full_reference_v001.png",
     "Exact-source reference: the full Animal_Salmon_Spawn_Eggs composition, rasterised from the source SVG over its warm ground.",
     "Matches source: everything (it IS the source). Off: nothing - reference only. Austin: source-usage clearance is needed before any exact-source geometry is used in an output."),
    ("02_exact_source_detail_reference_v001.png",
     "Exact-source reference: a detail crop on a head, focal eye, white negative-space channels, and the open jaw.",
     "Matches source: it IS the source. Off: nothing. Austin: this is the shape-logic reference our procedural studies are measured against."),
    ("03_procedural_red_jaw_salmon_v001.png",
     "Procedural: a curled salmon in the source red/brown palette with white rivers, a big focal eye, an open jaw with white teeth.",
     "Matches source: red/brown palette, curl, big eye, white channels, jaw teeth. Still off: the white rivers are simpler and less gestural than the source's feathered channels; the body silhouette is more even than Austin's bolder, more asymmetric forms. Austin would need to approve the palette use, the jaw/teeth motif, and the eye treatment."),
    ("04_procedural_grey_salmon_v001.png",
     "Procedural: the same curled body in the source warm-grey palette.",
     "Matches source: warm-grey palette, curl, big eye, white operculum channel. Still off: the grey fish in the source carries more internal dark formline detail; ours is plainer. Austin would need to approve the grey palette and channel placement."),
    ("05_procedural_split_masses_salmon_v001.png",
     "Procedural: a salmon whose body is split into a red body mass with brown head and tail-region masses.",
     "Matches source: bold split colour masses, the head as a distinct dark mass. Still off: the source splits masses along gestural negative-space curves, not at clean cross-sections; our split seams are too geometric. Austin would need to approve mass division as a design device."),
    ("06_procedural_white_river_led_salmon_v001.png",
     "Procedural: a salmon where bold white negative-space rivers are the dominant design element.",
     "Matches source: white negative space as a primary, body-carving element. Still off: the source's white channels are feathered, tapered, and read as flow/water; ours are smoother sweeps. Austin would need to approve negative space as a lead device and review its cultural load."),
    ("07_two_salmon_rotational_v001.png",
     "Procedural: two salmon - one red, one grey - in 180-degree rotational balance around a central concentric focal.",
     "Matches source: rotational (not bilateral) balance, a red + grey pair, a central roe-eye focal. Still off: the source's two fish interlock tightly with shared negative-space channels; our pair sits in rotation but does not interlock or share channels. Austin would need to approve the rotational-pair composition."),
    ("08_two_salmon_rotational_tight_v001.png",
     "Procedural: a tighter rotational interlock of the two salmon around the focal.",
     "Matches source: closer rotational interlock, the focal as the still point. Still off: still not a true interlock where one fish's curve cradles the other; the heads do not meet as in the source. Austin would need to approve the tighter composition."),
    ("09_roe_field_single_salmon_v001.png",
     "Procedural: a single curled salmon among clustered roe clouds in the source orange.",
     "Matches source: roe as clustered cloud-clumps of wildly varied scale, source orange. Still off: in the source the roe wraps and frames the whole composition as a surround; here it is nearby clumps only. Austin would need to approve roe as a general field element."),
    ("10_two_salmon_roe_surround_v001.png",
     "Procedural: the two-salmon rotation embedded in a full roe-field surround - the closest procedural rebuild of the source's whole composition logic.",
     "Matches source: rotational pair + central focal + roe surround, the full composition logic. Still off: the fish do not interlock and the roe ring is more even than the source's organic clumping; palette and composition are echoed, not reproduced. Austin would need to approve this whole-composition echo and confirm it is clearly NOT presented as his work."),
]


def write_contact_sheet(filenames):
    thumbs = []
    for fn in filenames:
        img = cv2.imread(str(OUT_DIR / fn))
        if img is not None:
            thumbs.append(cv2.resize(img, (360, 360), interpolation=cv2.INTER_AREA))
    if not thumbs:
        return
    rows = []
    for i in range(0, len(thumbs), 5):
        row = thumbs[i:i + 5]
        while len(row) < 5:
            row.append(np.full_like(thumbs[0], 255))
        rows.append(cv2.hconcat(row))
    cv2.imwrite(str(OUT_DIR / "contact_sheet.png"), cv2.vconcat(rows))


def write_readme():
    lines = [
        "# Austin-Informed Salmon Style Study v001 - 2026-05-19",
        "",
        "INTERNAL ONLY. Not Austin-approved. No SD/LoRA.",
        "",
        "## Purpose",
        "",
        "Replaces the 'animate v002 salmon' plan. The v002 morphology studies "
        "still read as generic grey fish. Animating them would only produce "
        "better-moving generic fish. This lane makes the procedural salmon "
        "Austin-informed FIRST, using the composition logic of "
        "`Animal_Salmon_Spawn_Eggs`: rotational balance, big red/grey/brown "
        "colour masses, bold white negative-space rivers, big focal eyes, and a "
        "roe field. Stills only, no animation.",
        "",
        "## Exact-Source vs Procedural",
        "",
        "- Studies 01-02 are EXACT-SOURCE REFERENCE: rasterised directly from "
        "the source SVG and labelled as such. They are the measuring stick, not "
        "our design output.",
        "- Studies 03-10 are PROCEDURAL: built from the source's design logic "
        "without copying its exact paths. They are internal sketches, not "
        "Austin-authored and not Austin-approved.",
        "",
        "## Source Palette Used",
        "",
        "Read from the source SVG fills: red `#eb4f3d`, dark brown `#78493f`, "
        "roe orange `#ff5e3b`, warm grey `#b5a19a`, mid/dark grey `#867c7c` / "
        "`#616161`, white channels `#ffffff`, ink outline `#231f20`, warm "
        "background `#875451` at low opacity.",
        "",
        "## Per-Study Comparison To The Source",
        "",
    ]
    for fn, what, compare in STUDY_NOTES:
        lines.extend([f"### {fn}", "", f"- Study: {what}",
                      f"- Vs source: {compare}", ""])
    lines.extend([
        "## Where The Procedural Studies Still Fall Short",
        "",
        "- The source's white channels are feathered and gestural and read as "
        "water/flow; ours are smoother geometric sweeps.",
        "- The source's two fish truly interlock and share negative-space "
        "channels; our rotational pairs sit in balance but do not interlock.",
        "- The source divides colour masses along gestural curves; our mass "
        "seams are still too geometric.",
        "- The source's roe wraps the whole composition as an organic surround; "
        "ours clusters in discrete clumps.",
        "",
        "## What Austin Would Need To Approve",
        "",
        "- Use of the source palette (red/brown/grey/roe-orange) in our outputs.",
        "- The jaw/teeth, big-focal-eye, and white-negative-space motifs.",
        "- The rotational two-salmon composition and the central focal.",
        "- Roe as a general field element beyond the exact spawn source.",
        "- Confirmation that any procedural study is clearly NOT presented as "
        "Austin's work, and source-usage clearance for the exact-source stills.",
        "",
        "## Recommendation",
        "",
        "Do not animate yet. Take studies 03, 07, and 10 to Austin as the "
        "strongest Austin-informed direction, get the palette and composition "
        "questions answered, then build a v002 style study before any motion "
        "work.",
        "",
        "## Files",
        "",
        "- 10 PNG stills listed above (02 exact-source reference, 08 procedural).",
        "- `contact_sheet.png`: all 10 in one 5x2 grid.",
        "",
        "## Scope",
        "",
        "Stills only, no MP4, no animation. No SD, no LoRA. No edits to Agent "
        "B/C/D output folders. Internal review material; no public use, no "
        "claim of Austin authorship or cultural approval.",
        "",
    ])
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Austin-Informed Salmon Style Study v001 to {OUT_DIR}", flush=True)
    src = load_source_raster()
    filenames = []
    for fn, frame in (study_01_source_full(src), study_02_source_detail(src)):
        cv2.imwrite(str(OUT_DIR / fn), frame)
        filenames.append(fn)
        print(f"  rendered {fn}", flush=True)
    for study in PROCEDURAL:
        fn, frame = study()
        cv2.imwrite(str(OUT_DIR / fn), frame)
        filenames.append(fn)
        print(f"  rendered {fn}", flush=True)
    write_contact_sheet(filenames)
    write_readme()
    print("Done. 10 stills, contact sheet, and README written.", flush=True)


if __name__ == "__main__":
    main()
