#!/usr/bin/env python3.11
"""Primitive Salmon Morphology v002 - 8 refined still studies.

Builds on the strongest v001 studies (03 negative-space, 05 curved comma,
08 eye-focal, 10 school cluster). The goal of v002 is to reduce the generic-fish
feel and improve Austin-informed shape quality, while staying CLEAN and bold -
formline character comes from few confident shapes, not from piled-on detail.

Refinements over v001:
  - Three-tone formline body: a darker head sub-mass, the mid body, and bold
    pale channels that CROSS the body as divisions (head from body, mid from
    tail-region) - not thin streaks running parallel to the contour.
  - The body can be carved into clean tonal masses (study 02).
  - Correctly-angled fins: clean swept blades that point cleanly out and back.
  - A socket eye: dark socket lens, pale ring, dark pupil, subtle brow.
  - Mild dorsal/ventral asymmetry so the silhouette has salmon character.
  - Confident curved spines.

The body stays ONE continuous fusiform mass. No body-centre circles. Stills
only, no animation.

Design logic learned from `Animal_Salmon_Spawn_Eggs.svg` and its decomposition,
NOT copied.

Outputs 8 PNG stills to:
  track2-deterministic/morph_outputs_INTERNAL/
    primitive_salmon_morphology_v002_2026-05-19/

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

OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/primitive_salmon_morphology_v002_2026-05-19"
S = 1080

BODY_MID = (164, 158, 147)
BODY_DARK = (110, 105, 99)
BODY_DEEP = (52, 50, 49)
PALE_CHANNEL = (226, 223, 213)
ACCENT = (242, 238, 226)
EYE_DARK = (16, 16, 20)
OUTLINE = (226, 233, 233)

UNIT_CIRCLE = np.array(
    [(math.cos(2 * math.pi * i / 96), math.sin(2 * math.pi * i / 96)) for i in range(96)],
    dtype=np.float32,
)

# Dorsal and ventral width profiles - mild asymmetry only (a slightly deeper
# shoulder up top, a slightly fuller belly mid-body).
WIDTH_DORSAL = [
    (0.00, 0.05), (0.08, 0.35), (0.18, 0.69), (0.33, 0.93),
    (0.52, 0.77), (0.69, 0.48), (0.84, 0.27), (1.00, 0.12),
]
WIDTH_VENTRAL = [
    (0.00, 0.05), (0.09, 0.33), (0.19, 0.64), (0.37, 0.85),
    (0.50, 0.83), (0.67, 0.55), (0.83, 0.30), (1.00, 0.12),
]


def canvas() -> np.ndarray:
    return np.zeros((S, S, 3), np.uint8)


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


def width_dorsal(t: float) -> float:
    return lerp_knots(WIDTH_DORSAL, t)


def width_ventral(t: float) -> float:
    return lerp_knots(WIDTH_VENTRAL, t)


def cubic(p0, p1, p2, p3, n=120) -> list[tuple[float, float]]:
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def arc_spine(center, length, angle, bow, n=64) -> list[tuple[float, float]]:
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    head = (center[0] + dx * length * 0.5, center[1] + dy * length * 0.5)
    tail = (center[0] - dx * length * 0.5, center[1] - dy * length * 0.5)
    b = bow * length
    p1 = (head[0] + (tail[0] - head[0]) * 0.34 + px * b, head[1] + (tail[1] - head[1]) * 0.34 + py * b)
    p2 = (head[0] + (tail[0] - head[0]) * 0.66 + px * b, head[1] + (tail[1] - head[1]) * 0.66 + py * b)
    return cubic(head, p1, p2, tail, n)


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


def fill_poly(frame, pts, rgb, alpha, *, outline_alpha=0.0, ow=1) -> None:
    draw_poly_alpha(frame, np.asarray(pts, dtype=np.float32), rgb, alpha=alpha,
                    outline_rgb=OUTLINE, outline_alpha=outline_alpha, outline_thickness=ow)


def oval(frame, center, rx, ry, angle, rgb, alpha) -> None:
    c, s = math.cos(angle), math.sin(angle)
    p = UNIT_CIRCLE.copy()
    p[:, 0] *= rx
    p[:, 1] *= ry
    p = p @ np.array([[c, -s], [s, c]], dtype=np.float32).T
    p[:, 0] += center[0]
    p[:, 1] += center[1]
    fill_poly(frame, p, rgb, alpha)


def crescent(frame, center, size, angle, rgb, alpha) -> None:
    fill_poly(frame, transform_points(CRESCENT_BASE, center, size, angle), rgb, alpha)


def tapered_band(frame, path, peak_hw, rgb, alpha) -> None:
    """A lens-tapered ribbon along a path - tapers to points at both ends."""
    n = len(path)
    if n < 3:
        return
    left, right = [], []
    for i, p in enumerate(path):
        f = i / (n - 1)
        w = peak_hw * smoothstep(min(f, 1.0 - f) * 2.3)
        a = polyline_tangent(path, i)
        nx, ny = -math.sin(a), math.cos(a)
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    fill_poly(frame, left + right[::-1], rgb, alpha)


def crossing_channel(frame, spine, max_hw, ds, t_dorsal, t_ventral, peak, rgb, alpha) -> None:
    """A bold pale channel CROSSING the body from the dorsal edge to the
    ventral edge - reads as a division (head/body, body/tail), not a streak."""
    pts = []
    n = 13
    for i in range(n):
        s = i / (n - 1)
        t = t_dorsal + (t_ventral - t_dorsal) * s
        cross = 1.0 - 2.0 * s
        p = spine_point(spine, t)
        a = spine_tangent(spine, t)
        nx = -math.sin(a) * ds
        ny = math.cos(a) * ds
        hw = (width_dorsal(t) if cross >= 0 else width_ventral(t)) * max_hw * cross
        pts.append((p[0] + nx * hw, p[1] + ny * hw))
    tapered_band(frame, pts, peak, rgb, alpha)


def forked_tail_polygon(peduncle, axis_angle, ped_half, span, length, notch) -> np.ndarray:
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


def fin_out_angle(tangent, dorsal_sign, side, sweep) -> float:
    """Direction a fin points: along the body normal, swept toward the tail."""
    ndx = -math.sin(tangent) * dorsal_sign
    ndy = math.cos(tangent) * dorsal_sign
    if side == "ventral":
        ndx, ndy = -ndx, -ndy
    base_ang = math.atan2(ndy, ndx)
    diff = math.atan2(math.sin(tangent - base_ang), math.cos(tangent - base_ang))
    return base_ang + diff * sweep


def draw_fin(frame, base, edge_tan, out_ang, base_half, length, rgb, alpha, *, concavity=0.14) -> None:
    """A clean swept fin blade: base flush on the body edge, apex out and back,
    a slight concave trailing edge for a touch of formline character."""
    et = (math.cos(edge_tan), math.sin(edge_tan))
    front = (base[0] - et[0] * base_half, base[1] - et[1] * base_half)
    rear = (base[0] + et[0] * base_half, base[1] + et[1] * base_half)
    apex = (base[0] + math.cos(out_ang) * length, base[1] + math.sin(out_ang) * length)
    pts = [front, apex]
    for k in range(1, 4):
        f = k / 4.0
        lx = apex[0] + (rear[0] - apex[0]) * f
        ly = apex[1] + (rear[1] - apex[1]) * f
        bump = math.sin(f * math.pi) * concavity
        lx += (base[0] - lx) * bump
        ly += (base[1] - ly) * bump
        pts.append((lx, ly))
    pts.append(rear)
    fill_poly(frame, pts, rgb, alpha)


def draw_socket_eye(frame, pos, r, angle) -> None:
    oval(frame, pos, r * 1.28, r * 1.02, angle, BODY_DEEP, 0.97)
    oval(frame, pos, r * 0.76, r * 0.68, angle, ACCENT, 0.97)
    oval(frame, pos, r * 0.33, r * 0.31, angle, EYE_DARK, 1.0)
    brow = (pos[0] - math.sin(angle) * r * 1.18, pos[1] - math.cos(angle) * r * 1.18)
    crescent(frame, brow, r * 1.35, angle, BODY_DEEP, 0.4)


def draw_salmon_v2(
    frame,
    spine,
    max_hw,
    *,
    dorsal_sign=-1.0,
    body_rgb=BODY_MID,
    head_submass=True,
    tail_submass=False,
    operculum=True,
    mid_channel=False,
    fins=True,
    jaw=True,
    kype=False,
    eye=True,
    outline_alpha=0.3,
):
    """Draw a refined three-tone primitive salmon. Returns the body polygon."""
    dors, vent = body_edges(spine, max_hw, dorsal_sign)
    ds = dorsal_sign
    a_end = spine_tangent(spine, 1.0)
    n = len(spine)

    # --- tail: forked, with one pale negative-space cut per lobe ---
    ped_half = width_dorsal(1.0) * max_hw
    span = max_hw * 0.84
    tlen = max_hw * 1.44
    fill_poly(frame, forked_tail_polygon(spine[-1], a_end, ped_half, span, tlen, max_hw * 0.64),
              BODY_DARK, 0.96, outline_alpha=outline_alpha)
    ax = (math.cos(a_end), math.sin(a_end))
    pp = (-math.sin(a_end), math.cos(a_end))
    for sgn in (1, -1):
        root = (spine[-1][0] + ax[0] * tlen * 0.18 + pp[0] * sgn * ped_half * 0.35,
                spine[-1][1] + ax[1] * tlen * 0.18 + pp[1] * sgn * ped_half * 0.35)
        tip = (spine[-1][0] + ax[0] * tlen * 0.82 + pp[0] * sgn * span * 0.74,
               spine[-1][1] + ax[1] * tlen * 0.82 + pp[1] * sgn * span * 0.74)
        mid = ((root[0] + tip[0]) / 2, (root[1] + tip[1]) / 2)
        tapered_band(frame, [root, mid, tip], max_hw * 0.085, PALE_CHANNEL, 0.62)

    # --- body: one continuous fusiform mass ---
    fill_poly(frame, dors + vent[::-1], body_rgb, 0.97, outline_alpha=outline_alpha, ow=2)

    # --- darker tonal sub-masses, sliced from the same edges so they sit flush ---
    if tail_submass:
        k0 = int(0.63 * (n - 1))
        fill_poly(frame, dors[k0:] + vent[k0:][::-1], BODY_DARK, 0.78)
    if head_submass:
        k = int(0.31 * (n - 1))
        fill_poly(frame, dors[:k + 1] + vent[:k + 1][::-1], BODY_DARK, 0.92)

    # --- bold crossing channels: clean divisions, not parallel streaks ---
    if operculum:
        crossing_channel(frame, spine, max_hw, ds, 0.325, 0.255, max_hw * 0.135,
                         PALE_CHANNEL, 0.86)
    if mid_channel:
        crossing_channel(frame, spine, max_hw, ds, 0.665, 0.605, max_hw * 0.10,
                         PALE_CHANNEL, 0.8)

    # --- fins: clean swept blades, correctly angled out and back ---
    if fins:
        for t, side, bh, ln, conc in (
            (0.44, "dorsal", 0.42, 0.74, 0.16),
            (0.36, "ventral", 0.24, 0.54, 0.40),
            (0.80, "dorsal", 0.12, 0.22, 0.10),
        ):
            p = spine_point(spine, t)
            a = spine_tangent(spine, t)
            nx = -math.sin(a) * ds
            ny = math.cos(a) * ds
            if side == "dorsal":
                base = (p[0] + nx * width_dorsal(t) * max_hw * 0.9,
                        p[1] + ny * width_dorsal(t) * max_hw * 0.9)
            else:
                base = (p[0] - nx * width_ventral(t) * max_hw * 0.88,
                        p[1] - ny * width_ventral(t) * max_hw * 0.88)
            out = fin_out_angle(a, ds, side, 0.42)
            draw_fin(frame, base, a, out, max_hw * bh, max_hw * ln, BODY_DARK, 0.9,
                     concavity=conc)

    # --- jaw line / spawning kype ---
    a0 = spine_tangent(spine, 0.03)
    if kype:
        snout = spine_point(spine, 0.0)
        hook = (snout[0] + math.cos(a0 + math.pi) * max_hw * 0.24,
                snout[1] + math.sin(a0 + math.pi) * max_hw * 0.24)
        crescent(frame, hook, max_hw * 0.46, a0 + math.pi * 0.5, body_rgb, 0.96)
    if jaw:
        jp = spine_point(spine, 0.06)
        nx = -math.sin(a0) * ds
        ny = math.cos(a0) * ds
        jl = (jp[0] - nx * width_ventral(0.06) * max_hw * 0.45,
              jp[1] - ny * width_ventral(0.06) * max_hw * 0.45)
        crescent(frame, jl, max_hw * 0.36, a0, BODY_DEEP, 0.5)

    # --- socket eye, dorsal-forward on the head ---
    if eye:
        p = spine_point(spine, 0.135)
        a = spine_tangent(spine, 0.135)
        nx = -math.sin(a) * ds
        ny = math.cos(a) * ds
        ep = (p[0] + nx * width_dorsal(0.135) * max_hw * 0.30,
              p[1] + ny * width_dorsal(0.135) * max_hw * 0.30)
        draw_socket_eye(frame, ep, max_hw * 0.21, a)

    return np.array(dors + vent[::-1], dtype=np.float32)


def school_salmon(frame, center, length, angle, bow, *, body_rgb=BODY_MID, alpha=0.94) -> None:
    """A refined school-scale salmon: one clean continuous gently curved mass,
    forked tail, one correctly-angled dorsal fin, a socket eye."""
    spine = arc_spine(center, length, angle, bow, n=56)
    max_hw = length * 0.15
    dors, vent = body_edges(spine, max_hw, -1.0)
    a_end = spine_tangent(spine, 1.0)
    ped_half = width_dorsal(1.0) * max_hw
    fill_poly(frame, forked_tail_polygon(spine[-1], a_end, ped_half, max_hw * 0.8,
                                         max_hw * 1.34, max_hw * 0.58), BODY_DARK, alpha)
    fill_poly(frame, dors + vent[::-1], body_rgb, alpha, outline_alpha=0.25)
    t = 0.44
    p = spine_point(spine, t)
    a = spine_tangent(spine, t)
    nx, ny = -math.sin(a) * -1.0, math.cos(a) * -1.0
    base = (p[0] + nx * width_dorsal(t) * max_hw * 0.9, p[1] + ny * width_dorsal(t) * max_hw * 0.9)
    draw_fin(frame, base, a, fin_out_angle(a, -1.0, "dorsal", 0.42),
             max_hw * 0.32, max_hw * 0.46, BODY_DARK, 0.86, concavity=0.14)
    p = spine_point(spine, 0.15)
    a = spine_tangent(spine, 0.15)
    nx, ny = -math.sin(a) * -1.0, math.cos(a) * -1.0
    ep = (p[0] + nx * width_dorsal(0.15) * max_hw * 0.30, p[1] + ny * width_dorsal(0.15) * max_hw * 0.30)
    oval(frame, ep, max_hw * 0.30, max_hw * 0.27, a, BODY_DEEP, 0.95)
    oval(frame, ep, max_hw * 0.13, max_hw * 0.12, a, ACCENT, 0.95)


def label(frame, text) -> None:
    cv2.putText(frame, text, (28, S - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                (120, 120, 124), 1, cv2.LINE_AA)


SIDE_SPINE = cubic((222, 556), (446, 524), (652, 524), (852, 552))


def study_01_negative_space_structural():
    frame = canvas()
    draw_salmon_v2(frame, SIDE_SPINE, 102, head_submass=True, operculum=True)
    label(frame, "01 negative-space structural: dark head sub-mass + bold operculum division")
    return "01_negative_space_structural_v002.png", frame


def study_02_negative_space_carved_masses():
    frame = canvas()
    draw_salmon_v2(frame, SIDE_SPINE, 102, head_submass=True, tail_submass=True,
                   operculum=True, mid_channel=True)
    label(frame, "02 negative-space carved masses: head / mid / tail masses, two pale divisions")
    return "02_negative_space_carved_masses_v002.png", frame


def study_03_curved_comma():
    frame = canvas()
    spine = cubic((404, 318), (706, 372), (738, 636), (556, 808))
    draw_salmon_v2(frame, spine, 98, dorsal_sign=1.0, head_submass=True, operculum=True)
    label(frame, "03 curved comma: confident C-curve swimming body")
    return "03_curved_comma_v002.png", frame


def study_04_curved_arc():
    frame = canvas()
    spine = cubic((236, 600), (474, 452), (726, 450), (940, 584))
    draw_salmon_v2(frame, spine, 96, dorsal_sign=-1.0, head_submass=True, operculum=True,
                   kype=True)
    label(frame, "04 curved arc: broad swimming arc + spawning kype")
    return "04_curved_arc_v002.png", frame


def study_05_eye_focal_curl():
    frame = canvas()
    spine = cubic((556, 398), (806, 522), (706, 820), (408, 740))
    p = spine_point(spine, 0.135)
    a = spine_tangent(spine, 0.135)
    nx, ny = -math.sin(a) * -1.0, math.cos(a) * -1.0
    ep = (p[0] + nx * width_dorsal(0.135) * 100 * 0.30, p[1] + ny * width_dorsal(0.135) * 100 * 0.30)
    for r, al in ((324, 0.07), (232, 0.10), (150, 0.12)):
        oval(frame, ep, r, r, 0.0, BODY_DARK, al)
    draw_salmon_v2(frame, spine, 100, dorsal_sign=-1.0, head_submass=True, operculum=True)
    label(frame, "05 eye-focal curl: open curl, faint focal rings centred on the eye")
    return "05_eye_focal_curl_v002.png", frame


def study_06_eye_focal_tight_curl():
    frame = canvas()
    spine = cubic((602, 380), (842, 612), (628, 850), (388, 632))
    p = spine_point(spine, 0.135)
    a = spine_tangent(spine, 0.135)
    nx, ny = -math.sin(a) * -1.0, math.cos(a) * -1.0
    ep = (p[0] + nx * width_dorsal(0.135) * 92 * 0.30, p[1] + ny * width_dorsal(0.135) * 92 * 0.30)
    for r, al in ((250, 0.09), (152, 0.13)):
        oval(frame, ep, r, r, 0.0, BODY_DARK, al)
    draw_salmon_v2(frame, spine, 92, dorsal_sign=-1.0, head_submass=True, operculum=True,
                   mid_channel=True)
    label(frame, "06 eye-focal tight curl: near-ring body, the eye as the still anchor")
    return "06_eye_focal_tight_curl_v002.png", frame


def study_07_school_flow():
    frame = canvas()
    fish = [
        (296, 304, 286, -11, 0.05), (628, 300, 322, -7, 0.04),
        (892, 372, 244, -13, 0.06), (372, 540, 300, -5, 0.05),
        (704, 548, 320, -9, 0.04), (300, 768, 262, -3, 0.06),
        (612, 776, 286, -10, 0.05), (888, 700, 222, -12, 0.06),
    ]
    for x, y, length, deg, bow in fish:
        school_salmon(frame, (x, y), length, math.radians(deg), bow,
                      body_rgb=BODY_MID if length > 270 else BODY_DARK)
    label(frame, "07 school flow: eight salmon on a shared current, common-fate heading")
    return "07_school_flow_v002.png", frame


def study_08_school_depth():
    frame = canvas()
    fish = [
        (404, 632, 432, 7, 0.05), (760, 736, 372, 17, 0.06),
        (286, 812, 312, 24, 0.06), (640, 432, 262, -5, 0.05),
        (876, 540, 220, 5, 0.06), (468, 350, 188, -13, 0.07),
        (742, 286, 152, -20, 0.07), (252, 482, 150, -2, 0.06),
    ]
    for x, y, length, deg, bow in fish:
        near = length > 250
        school_salmon(frame, (x, y), length, math.radians(deg), bow,
                      body_rgb=BODY_MID if near else BODY_DARK,
                      alpha=0.95 if near else 0.68)
    label(frame, "08 school depth: near salmon large and clear, far salmon small and dim")
    return "08_school_depth_v002.png", frame


STUDIES = [
    study_01_negative_space_structural,
    study_02_negative_space_carved_masses,
    study_03_curved_comma,
    study_04_curved_arc,
    study_05_eye_focal_curl,
    study_06_eye_focal_tight_curl,
    study_07_school_flow,
    study_08_school_depth,
]

STUDY_NOTES = [
    ("01_negative_space_structural_v002.png",
     "Refines v001-03. A three-tone body - dark head sub-mass, mid body, and one bold pale operculum channel crossing the body to divide head from body.",
     "Does the dark head sub-mass plus a single bold operculum division read as Coast-Salish-informed, or is more carving needed?"),
    ("02_negative_space_carved_masses_v002.png",
     "Carves the body into three clean tonal masses - dark head, mid flank, darker tail-region - separated by two bold pale crossing channels.",
     "Is carving the body into discrete tonal masses the right negative-space direction, or should the body stay more continuous?"),
    ("03_curved_comma_v002.png",
     "Refines v001-05. A confident C-curve comma body, three-tone, with the operculum division following the curved head.",
     "Is the curved comma the strongest salmon read, and is this curve graceful and confident enough?"),
    ("04_curved_arc_v002.png",
     "A broad swimming arc with a spawning kype - a different, shallower curve than the comma.",
     "Does a broad arc read as a swimming salmon, and is the kype a useful spawning cue?"),
    ("05_eye_focal_curl_v002.png",
     "Refines v001-08. An open curl with faint focal rings centred on the socket eye, so the eye anchors the composition.",
     "Does the eye work as the compositional anchor, and are the focal rings helpful or distracting?"),
    ("06_eye_focal_tight_curl_v002.png",
     "A tight near-ring curl bringing head and eye to the composition centre, echoing the source's rotational rest pose for a single fish.",
     "Is a near-ring salmon still legible as a salmon, and does the eye-as-anchor hold at this curl?"),
    ("07_school_flow_v002.png",
     "Refines v001-10. Eight clean school-scale salmon - each a continuous curved mass with a forked tail, one dorsal fin, and a socket eye - on a shared common-fate heading.",
     "Does the school read as salmon in current, and is the per-fish detail right for school scale?"),
    ("08_school_depth_v002.png",
     "A school with a depth read: large clear near salmon, small dim far salmon, gently turning.",
     "Does varied size plus dimming create depth, and does the school still read as one body of fish?"),
]


def write_contact_sheet(filenames) -> None:
    thumbs = []
    for fn in filenames:
        img = cv2.imread(str(OUT_DIR / fn))
        if img is not None:
            thumbs.append(cv2.resize(img, (380, 380), interpolation=cv2.INTER_AREA))
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
        "# Primitive Salmon Morphology v002 - 2026-05-19",
        "",
        "INTERNAL ONLY. Not Austin-approved. Not Austin-authored. Procedural "
        "design studies; none reproduces Austin's exact salmon.",
        "",
        "## Purpose",
        "",
        "Builds on the strongest v001 studies (03 negative-space, 05 curved "
        "comma, 08 eye-focal, 10 school cluster) to reduce the generic-fish feel "
        "and improve Austin-informed shape quality. Stills only, no animation.",
        "",
        "## Refinements Over v001",
        "",
        "- Three-tone formline body: a darker head sub-mass, the mid body, and "
        "bold pale channels - replacing v001's flat grey lens.",
        "- Negative space as bold divisions: pale channels CROSS the body "
        "(separating head from body, mid from tail-region) instead of running "
        "parallel to the contour as thin streaks.",
        "- The body can be carved into clean tonal masses (study 02).",
        "- Correctly-angled fins: clean swept blades pointing cleanly out and "
        "back, with a slight concave trailing edge for formline character.",
        "- A socket eye: dark socket lens, pale ring, dark pupil, subtle brow.",
        "- Mild dorsal/ventral asymmetry so the silhouette reads as salmon.",
        "- More confident curved spines.",
        "",
        "## Held From v001",
        "",
        "- The body is ONE continuous fusiform mass, never a chain of marks.",
        "- No body-centre circles: none of the eight v002 studies tests one.",
        "",
        "## What Each Study Tests",
        "",
    ]
    for fn, what, question in STUDY_NOTES:
        lines.extend([f"### {fn}", "", f"- Tests: {what}",
                      f"- Austin question: {question}", ""])
    lines.extend([
        "## Austin Review Questions",
        "",
        "1. Does the three-tone formline body reduce the generic-fish feel?",
        "2. Is a bold crossing operculum channel the right head/body division?",
        "3. How much negative space is right - study 01's single division or "
        "study 02's carved masses?",
        "4. Are the clean swept fin blades right, or should fins differ?",
        "5. Is the socket eye with a subtle brow the right eye treatment?",
        "6. Which curve reads best: comma (03), broad arc (04), or the "
        "eye-focal curls (05-06)?",
        "7. Does the eye hold as a compositional anchor in the curled studies?",
        "8. For schools (07-08), is the refined per-fish detail right at scale?",
        "9. Is the mild dorsal/ventral asymmetry helpful, or should the body "
        "stay symmetric?",
        "10. Which single study should a v003 build on?",
        "",
        "## Files",
        "",
        "- 8 PNG studies listed above.",
        "- `contact_sheet.png`: all 8 studies in one 4x2 grid.",
        "",
        "## Scope",
        "",
        "Stills only, no MP4, no animation. No SD, no LoRA, no tracking. No "
        "edits to Agent B/C/D output folders. Internal review material; no "
        "public use and no claim of Austin authorship or cultural approval.",
        "",
    ])
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Primitive Salmon Morphology v002 to {OUT_DIR}", flush=True)
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
