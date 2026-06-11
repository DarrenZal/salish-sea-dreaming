#!/usr/bin/env python3.11
"""Primitive Salmon Morphology v001 - 12 still studies.

Internal-only design study of a better primitive salmon vocabulary, made
BEFORE any further tracking animation. The v001 trajectory proof read as
segmented path markers rather than salmon; this lane asks what makes a salmon
read as a salmon when it is built from the circle/crescent/trigon/oval/line
grammar.

Design logic is learned from `track2-deterministic/source-vectors/
Animal_Salmon_Spawn_Eggs.svg` and its decomposition, NOT copied. The salmon
here is one continuous fusiform body mass (never a chain of equal beads), with
a broad head, a concentric focal eye, an explicit forked tail, swept fins, and
pale negative-space channels.

Outputs 12 PNG stills (no MP4) to:
  track2-deterministic/morph_outputs_INTERNAL/
    primitive_salmon_morphology_v001_2026-05-19/

INTERNAL ONLY. Not Austin-approved. Does not reproduce Austin's exact salmon.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from primitive_water_grammar_v1 import (
    CRESCENT_BASE,
    ROOT,
    draw_poly_alpha,
    transform_points,
)

OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_salmon_morphology_v001_2026-05-19"
S = 1080  # square study canvas

# Study palette (RGB). Restrained greys plus one bright accent; value
# separation is functional - it is what lets the form read on black.
BODY_MID = (158, 153, 143)
BODY_DARK = (104, 100, 95)
BODY_DEEP = (58, 56, 54)
BODY_LIGHT = (214, 210, 199)
PALE_CHANNEL = (226, 223, 213)
ACCENT = (238, 233, 220)
EYE_DARK = (20, 20, 24)
WATER = (196, 219, 226)
WATER_DIM = (110, 128, 134)
OUTLINE = (228, 235, 235)

UNIT_CIRCLE = np.array(
    [(math.cos(2 * math.pi * i / 96), math.sin(2 * math.pi * i / 96)) for i in range(96)],
    dtype=np.float32,
)

# Salmon side-profile width profile, head (t=0) to caudal peduncle (t=1), as a
# fraction of max body half-width. Distilled from the source: soft-pointed
# snout, maximum depth at the shoulder ~1/3 back, long taper to a narrow
# peduncle. Tuned for a fusiform ~4:1 length:depth salmon, not a chunky blob.
WIDTH_KNOTS = [
    (0.00, 0.06),
    (0.08, 0.34),
    (0.18, 0.66),
    (0.32, 0.92),
    (0.50, 0.80),
    (0.66, 0.52),
    (0.82, 0.30),
    (1.00, 0.13),
]


def canvas() -> np.ndarray:
    return np.zeros((S, S, 3), np.uint8)


def smoothstep(f: float) -> float:
    f = max(0.0, min(1.0, f))
    return f * f * (3.0 - 2.0 * f)


def width_at(t: float) -> float:
    t = max(0.0, min(1.0, t))
    for i in range(1, len(WIDTH_KNOTS)):
        t0, w0 = WIDTH_KNOTS[i - 1]
        t1, w1 = WIDTH_KNOTS[i]
        if t <= t1:
            f = smoothstep((t - t0) / (t1 - t0)) if t1 > t0 else 0.0
            return w0 + (w1 - w0) * f
    return WIDTH_KNOTS[-1][1]


def cubic(p0, p1, p2, p3, n=96) -> list[tuple[float, float]]:
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def straight_spine(center, length, angle, n=72) -> list[tuple[float, float]]:
    dx, dy = math.cos(angle), math.sin(angle)
    head = (center[0] + dx * length * 0.5, center[1] + dy * length * 0.5)
    return [(head[0] - dx * length * (i / (n - 1)), head[1] - dy * length * (i / (n - 1)))
            for i in range(n)]


def polyline_tangent(pts, i) -> float:
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


def spine_tangent(spine, t) -> float:
    return polyline_tangent(spine, int(max(0.0, min(1.0, t)) * (len(spine) - 1)))


def body_polygon(spine, max_hw, width_fn=width_at) -> np.ndarray:
    """Offset the spine by a tapering half-width to make ONE closed body mass.

    This is the core of the lane: the salmon is a single continuous silhouette,
    not a row of separate marks, so it cannot read as a segmented chain.
    """
    left, right = [], []
    n = len(spine)
    for i, p in enumerate(spine):
        hw = width_fn(i / (n - 1)) * max_hw
        a = polyline_tangent(spine, i)
        nx, ny = -math.sin(a), math.cos(a)
        left.append((p[0] + nx * hw, p[1] + ny * hw))
        right.append((p[0] - nx * hw, p[1] - ny * hw))
    return np.array(left + right[::-1], dtype=np.float32)


def fill_poly(frame, pts, rgb, alpha, *, outline_alpha=0.0, outline_rgb=OUTLINE, ow=1) -> None:
    draw_poly_alpha(frame, np.asarray(pts, dtype=np.float32), rgb, alpha=alpha,
                    outline_rgb=outline_rgb, outline_alpha=outline_alpha, outline_thickness=ow)


def oval(frame, center, rx, ry, angle, rgb, alpha, *, outline_alpha=0.0) -> None:
    c, s = math.cos(angle), math.sin(angle)
    p = UNIT_CIRCLE.copy()
    p[:, 0] *= rx
    p[:, 1] *= ry
    p = p @ np.array([[c, -s], [s, c]], dtype=np.float32).T
    p[:, 0] += center[0]
    p[:, 1] += center[1]
    fill_poly(frame, p, rgb, alpha, outline_alpha=outline_alpha)


def crescent(frame, center, size, angle, rgb, alpha, *, outline_alpha=0.0) -> None:
    fill_poly(frame, transform_points(CRESCENT_BASE, center, size, angle), rgb, alpha,
              outline_alpha=outline_alpha)


def forked_tail_polygon(peduncle, axis_angle, ped_half, span, length, notch) -> np.ndarray:
    """Explicit forked caudal fin: flares from the peduncle to two pointed
    lobes with a deep V-notch between them. Unambiguous, unlike a trigon."""
    ax = (math.cos(axis_angle), math.sin(axis_angle))
    pp = (-math.sin(axis_angle), math.cos(axis_angle))
    p_top = (peduncle[0] + pp[0] * ped_half, peduncle[1] + pp[1] * ped_half)
    p_bot = (peduncle[0] - pp[0] * ped_half, peduncle[1] - pp[1] * ped_half)
    up_tip = (peduncle[0] + ax[0] * length + pp[0] * span,
              peduncle[1] + ax[1] * length + pp[1] * span)
    lo_tip = (peduncle[0] + ax[0] * length - pp[0] * span,
              peduncle[1] + ax[1] * length - pp[1] * span)
    notch_p = (peduncle[0] + ax[0] * (length - notch), peduncle[1] + ax[1] * (length - notch))
    return np.array([p_top, up_tip, notch_p, lo_tip, p_bot], dtype=np.float32)


def swept_fin(frame, base, edge_angle, out_angle, base_half, length, rgb, alpha) -> None:
    """Clean swept triangle: base flush on the body edge, apex out and back."""
    et = (math.cos(edge_angle), math.sin(edge_angle))
    b1 = (base[0] - et[0] * base_half, base[1] - et[1] * base_half)
    b2 = (base[0] + et[0] * base_half, base[1] + et[1] * base_half)
    apex = (base[0] + math.cos(out_angle) * length, base[1] + math.sin(out_angle) * length)
    fill_poly(frame, [b1, apex, b2], rgb, alpha)


def draw_eye(frame, pos, r, angle) -> None:
    """Concentric focal eye: dark socket oval, pale ring, dark pupil."""
    oval(frame, pos, r, r * 0.88, angle, BODY_DEEP, 0.96)
    oval(frame, pos, r * 0.58, r * 0.52, angle, ACCENT, 0.96)
    oval(frame, pos, r * 0.24, r * 0.22, angle, EYE_DARK, 1.0)


def edge_point(spine, t, side, frac=1.0):
    """A point on the body edge at parameter t. side -1 dorsal, +1 ventral."""
    p = spine_point(spine, t)
    a = spine_tangent(spine, t)
    nx, ny = -math.sin(a), math.cos(a)
    hw = width_at(t) * frac
    return (p[0] + nx * hw * side, p[1] + ny * hw * side), a


def draw_salmon(
    frame,
    spine,
    max_hw,
    *,
    body_rgb=BODY_MID,
    body_alpha=0.96,
    tail=True,
    eye=True,
    gill=False,
    dorsal_fin=True,
    pectoral_fin=True,
    adipose_fin=True,
    negative_space=False,
    interior_marks=False,
    gill_triplet=False,
    body_center_circle=False,
    kype=False,
    outline_alpha=0.32,
) -> np.ndarray:
    """Draw a full primitive salmon and return its body polygon."""
    a_end = spine_tangent(spine, 1.0)
    if tail:
        ped_half = width_at(1.0) * max_hw
        tail_poly = forked_tail_polygon(spine[-1], a_end, ped_half,
                                        max_hw * 0.86, max_hw * 1.42, max_hw * 0.62)
        fill_poly(frame, tail_poly, BODY_DARK, body_alpha, outline_alpha=outline_alpha)

    poly = body_polygon(spine, max_hw)
    fill_poly(frame, poly, body_rgb, body_alpha, outline_alpha=outline_alpha, ow=2)

    if kype:
        snout = spine_point(spine, 0.0)
        a = spine_tangent(spine, 0.02)
        hook = (snout[0] + math.cos(a + math.pi) * max_hw * 0.22,
                snout[1] + math.sin(a + math.pi) * max_hw * 0.22)
        crescent(frame, hook, max_hw * 0.5, a + math.pi * 0.5, body_rgb, body_alpha)

    if negative_space:
        # Pale ribbons carving the body along the back and belly, echoing the
        # source's white interior channels.
        for side in (-1, 1):
            chan = []
            for i in range(25):
                t = 0.16 + 0.66 * i / 24
                ep, _ = edge_point(spine, t, side, frac=max_hw * (0.50 if side < 0 else 0.40))
                chan.append(ep)
            ribbon = []
            back = []
            for i, p in enumerate(chan):
                f = i / 24.0
                w = max_hw * 0.072 * smoothstep(min(f, 1.0 - f) * 2.2)
                a = polyline_tangent(chan, i)
                nx, ny = -math.sin(a), math.cos(a)
                ribbon.append((p[0] + nx * w, p[1] + ny * w))
                back.append((p[0] - nx * w, p[1] - ny * w))
            fill_poly(frame, np.array(ribbon + back[::-1], dtype=np.float32),
                      PALE_CHANNEL, 0.85)
        gp, ga = edge_point(spine, 0.27, 0, 0)
        crescent(frame, gp, max_hw * 0.66, ga + math.pi / 2, PALE_CHANNEL, 0.78)

    if interior_marks:
        for t in (0.40, 0.56, 0.70):
            p = spine_point(spine, t)
            a = spine_tangent(spine, t)
            crescent(frame, p, width_at(t) * max_hw * 1.35, a + math.pi / 2, BODY_DARK, 0.7)

    if body_center_circle:
        # Explicit test of Austin question 2: body-centre circle acceptable?
        p = spine_point(spine, 0.40)
        r = width_at(0.40) * max_hw * 0.36
        oval(frame, p, r, r, 0.0, BODY_LIGHT, 0.9)
        oval(frame, p, r * 0.42, r * 0.42, 0.0, BODY_DARK, 0.95)

    if gill_triplet:
        for k in range(3):
            t = 0.20 + k * 0.04
            p = spine_point(spine, t)
            a = spine_tangent(spine, t)
            nx, ny = -math.sin(a), math.cos(a)
            off = (k - 1) * width_at(t) * max_hw * 0.40
            crescent(frame, (p[0] + nx * off, p[1] + ny * off),
                     max_hw * 0.26, a + math.pi / 2, PALE_CHANNEL, 0.82)

    if gill and not negative_space:
        gp, ga = edge_point(spine, 0.30, 0, 0)
        crescent(frame, gp, max_hw * 0.6, ga - math.pi / 2, BODY_DARK, 0.55)

    if dorsal_fin:
        base, a = edge_point(spine, 0.40, -1, frac=max_hw * 0.92)
        swept_fin(frame, base, a, a - math.pi * 0.72, max_hw * 0.40, max_hw * 0.66,
                  BODY_DARK, 0.85)
    if adipose_fin:
        base, a = edge_point(spine, 0.80, -1, frac=max_hw * 0.92)
        swept_fin(frame, base, a, a - math.pi * 0.74, max_hw * 0.12, max_hw * 0.20,
                  BODY_DARK, 0.85)
    if pectoral_fin:
        base, a = edge_point(spine, 0.30, 1, frac=max_hw * 0.86)
        swept_fin(frame, base, a, a + math.pi * 0.70, max_hw * 0.26, max_hw * 0.52,
                  BODY_DARK, 0.82)

    if eye:
        ep, a = edge_point(spine, 0.135, -1, frac=max_hw * 0.34)
        draw_eye(frame, ep, max_hw * 0.20, a)

    return poly


def label(frame, text) -> None:
    cv2.putText(frame, text, (28, S - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (120, 120, 124), 1, cv2.LINE_AA)


SIDE_SPINE = cubic((222, 556), (440, 522), (650, 522), (838, 552))


# --- Group A: side-profile salmon glyphs ----------------------------------

def study_01_sideprofile_minimal():
    frame = canvas()
    draw_salmon(frame, SIDE_SPINE, 100, gill=False, dorsal_fin=False,
                pectoral_fin=False, adipose_fin=False)
    label(frame, "01 side-profile minimal: body mass + forked tail + eye only")
    return "01_sideprofile_minimal_v001.png", frame


def study_02_sideprofile_full():
    frame = canvas()
    draw_salmon(frame, SIDE_SPINE, 100, gill=True, dorsal_fin=True,
                pectoral_fin=True, adipose_fin=True)
    label(frame, "02 side-profile full: body + gill + dorsal / pectoral / adipose fins")
    return "02_sideprofile_full_v001.png", frame


def study_03_sideprofile_negative_space():
    frame = canvas()
    draw_salmon(frame, SIDE_SPINE, 100, gill=False, dorsal_fin=True,
                pectoral_fin=True, adipose_fin=True, negative_space=True)
    label(frame, "03 side-profile negative space: pale carved back / belly / gill channels")
    return "03_sideprofile_negative_space_v001.png", frame


def study_04_sideprofile_formline_detail():
    frame = canvas()
    draw_salmon(frame, SIDE_SPINE, 100, gill=True, dorsal_fin=True,
                pectoral_fin=True, adipose_fin=True, interior_marks=True,
                gill_triplet=True, body_center_circle=True)
    label(frame, "04 formline detail: interior crescents + gill triplet + body-centre circle test")
    return "04_sideprofile_formline_detail_v001.png", frame


# --- Group B: curved / spine salmon forms ---------------------------------

def study_05_curved_single_comma():
    frame = canvas()
    spine = cubic((402, 300), (690, 356), (744, 632), (560, 800))
    draw_salmon(frame, spine, 96, gill=True, dorsal_fin=True, pectoral_fin=True,
                adipose_fin=True)
    label(frame, "05 curved single comma: gentle C-curved swimming body")
    return "05_curved_single_comma_v001.png", frame


def study_06_curved_deep_hook():
    frame = canvas()
    spine = cubic((486, 318), (792, 408), (760, 760), (452, 790))
    draw_salmon(frame, spine, 90, gill=True, dorsal_fin=True, pectoral_fin=True,
                adipose_fin=True, kype=True)
    label(frame, "06 curved deep hook: strong spawning arc + hooked jaw (kype)")
    return "06_curved_deep_hook_v001.png", frame


def study_07_curved_rotational_pair():
    frame = canvas()
    cx, cy = S / 2, S / 2
    spine_a = cubic((366, 332), (596, 356), (648, 552), (548, 686))
    spine_b = [(2 * cx - x, 2 * cy - y) for (x, y) in spine_a]
    draw_salmon(frame, spine_a, 80, body_rgb=BODY_MID, gill=False, dorsal_fin=True,
                pectoral_fin=True, adipose_fin=True)
    draw_salmon(frame, spine_b, 80, body_rgb=BODY_DARK, gill=False, dorsal_fin=True,
                pectoral_fin=True, adipose_fin=True)
    oval(frame, (cx, cy), 52, 52, 0.0, BODY_DEEP, 0.92)
    oval(frame, (cx, cy), 30, 30, 0.0, PALE_CHANNEL, 0.95)
    oval(frame, (cx, cy), 12, 12, 0.0, EYE_DARK, 1.0)
    label(frame, "07 rotational pair: two curved salmon around a central focal")
    return "07_curved_rotational_pair_v001.png", frame


def study_08_curved_eye_focal():
    frame = canvas()
    spine = cubic((556, 452), (792, 540), (676, 792), (404, 676))
    # Faint focal rings drawn first, behind the fish, centred on the eye.
    ep, _ = edge_point(spine, 0.135, -1, frac=100 * 0.34)
    for r, al in ((318, 0.07), (224, 0.10), (150, 0.13)):
        oval(frame, ep, r, r, 0.0, WATER_DIM, al)
    draw_salmon(frame, spine, 100, gill=True, dorsal_fin=True, pectoral_fin=True,
                adipose_fin=True)
    label(frame, "08 eye-focal curve: body curl placing the concentric eye as the anchor")
    return "08_curved_eye_focal_v001.png", frame


# --- Group C: school-scale simplified marks -------------------------------

def school_fish(frame, center, length, angle, *, body_rgb=BODY_MID, alpha=0.95):
    """A tiny coherent fish: one continuous body mass + forked tail + eye dot.
    Kept as one silhouette so the school reads as fish, not as bead chains."""
    spine = straight_spine(center, length, angle, n=48)
    max_hw = length * 0.16
    a_end = spine_tangent(spine, 1.0)
    fill_poly(frame, forked_tail_polygon(spine[-1], a_end, width_at(1.0) * max_hw,
                                         max_hw * 0.9, max_hw * 1.4, max_hw * 0.6),
              BODY_DARK, alpha)
    fill_poly(frame, body_polygon(spine, max_hw), body_rgb, alpha, outline_alpha=0.3)
    base, a = edge_point(spine, 0.40, -1, frac=max_hw * 0.92)
    swept_fin(frame, base, a, a - math.pi * 0.72, max_hw * 0.34, max_hw * 0.5,
              BODY_DARK, 0.85)
    ep, _ = edge_point(spine, 0.15, -1, frac=max_hw * 0.34)
    oval(frame, ep, max_hw * 0.28, max_hw * 0.26, 0.0, EYE_DARK, 0.95)


def study_09_school_single():
    frame = canvas()
    school_fish(frame, (S / 2 - 30, S / 2), 430, math.radians(-7))
    label(frame, "09 school-scale single: minimum coherent fish (body + tail + dorsal + eye)")
    return "09_school_single_v001.png", frame


def study_10_school_cluster():
    frame = canvas()
    fish = [
        (300, 372, 250, -15), (532, 312, 300, -8), (770, 388, 226, -19),
        (404, 566, 286, 3), (642, 548, 322, -5), (486, 752, 244, 13),
        (770, 716, 262, 7), (244, 700, 196, 22),
    ]
    for x, y, length, deg in fish:
        school_fish(frame, (x, y), length, math.radians(deg),
                    body_rgb=BODY_MID if length > 250 else BODY_DARK, alpha=0.9)
    label(frame, "10 school-scale cluster: eight coherent fish reading as movement")
    return "10_school_cluster_v001.png", frame


# --- Group D: wake-only / salmon implied by water -------------------------

def flow_field_points():
    """Organic water-sample positions on gentle flow lines (not a grid)."""
    pts = []
    for ri in range(15):
        y0 = 96 + ri * (S - 192) / 14
        for ci in range(22):
            f = ci / 21
            x = 70 + f * (S - 140)
            y = y0 + 30 * math.sin(f * 3.0 + ri * 0.7) + 12 * math.sin(ci * 0.9)
            pts.append((x, y))
    return pts


def study_11_wake_negative_space():
    frame = canvas()
    spine = cubic((300, 470), (610, 410), (700, 690), (470, 800))
    contour = np.round(body_polygon(spine, 132)).astype(np.int32)
    for (x, y) in flow_field_points():
        if cv2.pointPolygonTest(contour, (float(x), float(y)), True) > -30:
            continue  # inside or close margin -> the salmon-shaped void
        ang = 0.14 + 0.20 * math.sin(x * 0.004 + y * 0.006)
        crescent(frame, (x, y), 32, ang, WATER, 0.36)
    ep, ea = edge_point(spine, 0.135, -1, frac=132 * 0.34)
    oval(frame, ep, 20, 17, ea, WATER_DIM, 0.46)
    label(frame, "11 wake / negative space: salmon as a fish-shaped void in the water")
    return "11_wake_negative_space_v001.png", frame


def study_12_wake_displacement():
    frame = canvas()
    spine = cubic((292, 612), (520, 524), (760, 532), (944, 604))
    fish = body_polygon(spine, 120)
    contour = np.round(fish).astype(np.int32)
    verts = fish
    for (x, y) in flow_field_points():
        d = cv2.pointPolygonTest(contour, (float(x), float(y)), True)
        if d > -6:
            continue  # inside the body -> the void
        dist = -d
        # Push direction is away from the nearest body-outline vertex.
        diffs = verts - np.array([x, y], dtype=np.float32)
        ni = int(np.argmin(np.einsum("ij,ij->i", diffs, diffs)))
        dx, dy = x - verts[ni][0], y - verts[ni][1]
        norm = math.hypot(dx, dy) or 1.0
        falloff = math.exp(-dist / 140.0)
        px = x + (dx / norm) * 104.0 * falloff
        py = y + (dy / norm) * 104.0 * falloff
        ang = math.atan2(dy, dx) + math.pi / 2
        crescent(frame, (px, py), 27 + 16 * falloff, ang, WATER, 0.30 + 0.34 * falloff)
    ep, ea = edge_point(spine, 0.135, -1, frac=120 * 0.34)
    oval(frame, ep, 18, 15, ea, WATER_DIM, 0.44)
    label(frame, "12 wake / displacement: salmon implied by water bending around it")
    return "12_wake_displacement_v001.png", frame


STUDIES = [
    study_01_sideprofile_minimal,
    study_02_sideprofile_full,
    study_03_sideprofile_negative_space,
    study_04_sideprofile_formline_detail,
    study_05_curved_single_comma,
    study_06_curved_deep_hook,
    study_07_curved_rotational_pair,
    study_08_curved_eye_focal,
    study_09_school_single,
    study_10_school_cluster,
    study_11_wake_negative_space,
    study_12_wake_displacement,
]

STUDY_NOTES = [
    ("01_sideprofile_minimal_v001.png",
     "Fewest primitives: one fusiform body mass, an explicit forked tail, a concentric eye.",
     "Does a salmon read from this minimum, or is the gill/fin set needed to disambiguate it from a generic fish?"),
    ("02_sideprofile_full_v001.png",
     "The same body with a gill arc, swept dorsal and pectoral fins, and the small salmon adipose fin.",
     "Does the swept fin set help the salmon read, or does it clutter the silhouette?"),
    ("03_sideprofile_negative_space_v001.png",
     "Body carved by pale negative-space channels along the back, belly, and gill, echoing the source's white interior channels.",
     "Should negative space be a primary construction tool for the salmon, or a secondary detail?"),
    ("04_sideprofile_formline_detail_v001.png",
     "Interior crescent muscle/flow marks, the three-crescent gill-raker detail, and an explicit body-centre circle.",
     "Is a body-centre circle acceptable on a primitive salmon, or should circles stay at the eye only? How much interior detail before it is busy?"),
    ("05_curved_single_comma_v001.png",
     "One gently C-curved body, the spine bent like a swimming salmon rather than a rigid side icon.",
     "Does the curved body still read clearly as a salmon, and is this curve closer to the intended feel?"),
    ("06_curved_deep_hook_v001.png",
     "A strong spawning arc with a hooked-jaw kype - a spawning-male cue, since the source is a spawn composition.",
     "Is the deep hook plus kype a useful spawning-salmon cue, or too specific without Austin guidance?"),
    ("07_curved_rotational_pair_v001.png",
     "Two curved salmon in rotational balance around a central concentric focal, learning the source's two-fold composition logic without copying its paths.",
     "Is the rotational two-salmon-plus-central-focal arrangement a safe internal study, or too close to the source composition?"),
    ("08_curved_eye_focal_v001.png",
     "A curled body composed so the concentric eye sits at the visual anchor, with faint outward focal rings.",
     "Should the eye act as the compositional anchor of a curved salmon, the way the source uses focal ovals?"),
    ("09_school_single_v001.png",
     "One school-scale fish: a single continuous body mass plus forked tail, dorsal fin, and eye dot - no bead chain.",
     "At small scale, is this the right primitive count, and does it still read as a salmon rather than a generic minnow?"),
    ("10_school_cluster_v001.png",
     "Eight coherent school-scale fish at varied size and heading, each one continuous mass.",
     "Does the cluster read as a salmon school in motion, and is the per-fish detail level right for school scale?"),
    ("11_wake_negative_space_v001.png",
     "No body is drawn: the salmon is a fish-shaped void in a field of water crescents, with one faint eye cue.",
     "Does the salmon read when it is the absence in the water rather than a drawn figure?"),
    ("12_wake_displacement_v001.png",
     "No body is drawn: water crescents bend away from an invisible body, implying the salmon by displacement and wake.",
     "Does displacement alone imply a salmon, and is this a better 'salmon implied by water' direction than the v001 trajectory markers?"),
]


def write_contact_sheet(filenames) -> None:
    thumbs = []
    for fn in filenames:
        img = cv2.imread(str(OUT_DIR / fn))
        if img is not None:
            thumbs.append(cv2.resize(img, (360, 360), interpolation=cv2.INTER_AREA))
    if not thumbs:
        return
    rows = []
    for i in range(0, len(thumbs), 4):
        row = thumbs[i:i + 4]
        while len(row) < 4:
            row.append(np.zeros_like(thumbs[0]))
        rows.append(cv2.hconcat(row))
    cv2.imwrite(str(OUT_DIR / "contact_sheet.png"), cv2.vconcat(rows))


def write_readme() -> None:
    lines = [
        "# Primitive Salmon Morphology v001 - 2026-05-19",
        "",
        "INTERNAL ONLY. Not Austin-approved. Not Austin-authored. These are "
        "procedural design studies; none reproduces Austin's exact salmon.",
        "",
        "## Why This Lane Exists",
        "",
        "The v001 salmon-trajectory proof was technically sound but read as "
        "segmented path markers, not as salmon. Before any further tracking "
        "animation, this lane studies what makes a salmon read as a salmon when "
        "built from the circle / crescent / trigon / oval / line grammar.",
        "",
        "## Design Logic Borrowed From The Source",
        "",
        "Studied from `Animal_Salmon_Spawn_Eggs.svg` and its decomposition, then "
        "rebuilt procedurally - not copied:",
        "",
        "- One continuous fusiform body mass (~4:1 length:depth), never a chain "
        "of equal marks. The body is a single offset-from-spine silhouette.",
        "- Width profile: soft-pointed snout, maximum depth at the shoulder ~1/3 "
        "back, long taper to a narrow caudal peduncle.",
        "- A broad head carrying a concentric focal eye (dark socket, pale ring, "
        "dark pupil), placed dorsally near the snout - never at body centre.",
        "- An explicit forked tail: two pointed lobes with a deep V-notch.",
        "- Swept fins: dorsal, pectoral, and the small salmon adipose fin.",
        "- Pale negative-space channels carving the body, as in the source's "
        "white interior channels.",
        "- A three-crescent gill-raker detail near the head.",
        "",
        "## What Each Study Tests",
        "",
    ]
    for fn, what, question in STUDY_NOTES:
        lines.extend([f"### {fn}", "", f"- Tests: {what}",
                      f"- Austin question: {question}", ""])
    lines.extend([
        "## How This Differs From The Rejected Lanes",
        "",
        "- Unlike the v004/v005 articulated fish glyph, the body is a true "
        "continuous silhouette generated from a spine and width profile, not "
        "primitives strung in a row.",
        "- Unlike the v001 trajectory markers, the salmon is a coherent mass (or "
        "a coherent void / displacement in the wake studies), so it cannot read "
        "as a segmented chain.",
        "",
        "## Austin Review Questions",
        "",
        "1. Which group reads most clearly as a salmon: side-profile, curved, "
        "school-scale, or wake-implied?",
        "2. Is a body-centre circle acceptable (study 04), or should circles stay "
        "limited to the eye, roe, and water anchors?",
        "3. Should negative-space channels (study 03) be a primary construction "
        "tool, or a secondary detail?",
        "4. Is the curved/comma body (studies 05-08) closer to the intended feel "
        "than the side profile?",
        "5. Is the rotational two-salmon study (07) a safe internal study, or too "
        "close to the source composition?",
        "6. Is the spawning kype (study 06) a useful cue, or too specific?",
        "7. For schools (09-10), is one continuous mass per fish the right "
        "approach at small scale?",
        "8. Do the wake-implied studies (11-12) read as salmon, and is that a "
        "better 'salmon implied by water' direction than v001 trajectory markers?",
        "9. Should the eye stay a concentric oval assembly, or simplify?",
        "10. Which single study should the next morphology version build on?",
        "",
        "## Files",
        "",
        "- 12 PNG studies listed above.",
        "- `contact_sheet.png`: all 12 studies in one 4x3 grid.",
        "",
        "## Scope",
        "",
        "Stills only, no MP4. No SD, no LoRA, no tracking animation. No edits to "
        "Agent B/C/D output folders. Internal review material; no public use and "
        "no claim of Austin authorship or cultural approval.",
        "",
    ])
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Salmon Morphology v001 to {OUT_DIR}", flush=True)
    filenames = []
    for study in STUDIES:
        fn, frame = study()
        cv2.imwrite(str(OUT_DIR / fn), frame)
        filenames.append(fn)
        print(f"  rendered {fn}", flush=True)
    write_contact_sheet(filenames)
    write_readme()
    print("Done. 12 stills, contact sheet, and README written.", flush=True)


if __name__ == "__main__":
    main()
