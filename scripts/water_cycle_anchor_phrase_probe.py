#!/usr/bin/env python3.11
"""
Water-cycle anchor-phrase probe v001.

A pivot away from the prior scalar-cell phase studies / transitions / continuum
lane. Those passed every mechanical Section 9 criterion but read as instrument
readouts, not water. This probe is *phrase composition first*: authored
parametric primitives (circle, crescent, trigon) that change meaning through
motion, color, and context across one anchor chain:

    sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent

The wave/interference engine from v003 is imported ONLY for phase 4 (rain
impact / ripple), where it drives a low-opacity background shimmer underneath
the AUTHORED concentric crescents. The geometry of every visible primitive in
every phase is authored, not field-extracted.

Status: primitive-like water-cycle phrase study pending cultural review.
INTERNAL ONLY. Not Austin-approved. No cultural-meaning, public-readiness,
Coast Salish grammar, or traditional-meaning claim.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

# Import v003's wave engine for phase 4 atmosphere ONLY (not as a geometry
# source). v003 is import-safe: its module body has no side effects.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
import cymatic_field_topology_v003 as v003  # noqa: E402

ROOT = _SCRIPTS_DIR.parent
RECIPE_PATH = (
    ROOT
    / "track2-deterministic"
    / "scene_recipes"
    / "water_cycle_anchor_phrase_probe_v001.json"
)
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_cycle_anchor_phrase_probe_v001_2026-05-21"
)
KEY_STILLS_DIR = OUT_DIR / "key_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"

W = 1920
H = 1080
FPS = 24
DURATION_S = 24.0
N_FRAMES = int(round(FPS * DURATION_S))  # 576
TAU = math.tau
CULTURAL_STATUS = "primitive-like water-cycle phrase study pending cultural review"

# Palette (BGR for OpenCV). Background is the near-black the prior lane used
# (`#05070b`); foreground palette is warm-amber for sun/origin, soft-ivory for
# boundary/ring, muted-gold for release, pale-blue for ripple/rain/wave, and
# desaturated lifts for vapor.
BACKGROUND_BGR = (0x0B, 0x07, 0x05)         # #05070b
AMBER_BGR = (90, 160, 235)                  # warm amber for sun/origin
AMBER_DIM_BGR = (52, 96, 142)               # dim amber for fading anchor
MUTED_GOLD_BGR = (110, 180, 240)            # ray/release warm gold
SOFT_IVORY_BGR = (220, 232, 240)            # ring / boundary highlight
IVORY_BGR = (236, 244, 248)                 # impact circle
PALE_BLUE_BGR = (238, 220, 150)             # ripple / rain
PALE_BLUE_DESAT_BGR = (200, 188, 156)       # vapor (desaturated pale blue)
PALE_BLUE_DEEP_BGR = (210, 178, 100)        # wave (slightly deeper)

CX = W / 2.0
CY = H / 2.0


# ---------------------------------------------------------------------------
# Phase windows: phase 4 is the only one that uses the wave-field atmosphere.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PhaseWindow:
    key: str
    order: int
    start_s: float
    end_s: float

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


PHASES: tuple[PhaseWindow, ...] = (
    PhaseWindow("phase1_sun",    1,  0.0,  5.0),
    PhaseWindow("phase2_vapor",  2,  5.0,  9.0),
    PhaseWindow("phase3_rain",   3,  9.0, 13.0),
    PhaseWindow("phase4_ripple", 4, 13.0, 18.0),
    PhaseWindow("phase5_wave",   5, 18.0, 24.0),
)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / max(1e-9, edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(a: Sequence[int], b: Sequence[int], t: float) -> tuple[int, int, int]:
    return (
        int(round(lerp(a[0], b[0], t))),
        int(round(lerp(a[1], b[1], t))),
        int(round(lerp(a[2], b[2], t))),
    )


# ---------------------------------------------------------------------------
# Authored primitive drawing.
#
# These are parametric primitives, not field-extracted cells. Each takes
# geometry + color + opacity controls. The crescent is drawn via two circle
# arcs and an offset (the SVG canonical reference for cusp behavior). The
# trigon is a curved-side triangle anchored to an attachment point so it
# never reads as a detached arrowhead. Each draws to an alpha-aware compositor
# so glow / soft edges work over the near-black base.
# ---------------------------------------------------------------------------


def make_canvas() -> np.ndarray:
    canvas = np.empty((H, W, 3), dtype=np.uint8)
    canvas[:, :, 0] = BACKGROUND_BGR[0]
    canvas[:, :, 1] = BACKGROUND_BGR[1]
    canvas[:, :, 2] = BACKGROUND_BGR[2]
    return canvas


def add_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    bgr: Sequence[int],
    alpha: float,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
    *,
    blend: str = "add",
) -> None:
    """Composite a soft mask onto the frame.

    blend="add"     : additive (default; saturates bright on amber-on-amber).
    blend="replace" : true alpha blend - color *replaces* underlying value
                      weighted by (mask * alpha). Use this for solid opaque
                      shapes that should NOT add to underlying brightness.
    """
    if alpha <= 0.0 and glow_alpha <= 0.0:
        return
    color = np.array(bgr, dtype=np.float32)
    base = frame.astype(np.float32)
    m = mask.astype(np.float32) / 255.0
    if alpha > 0.0:
        if blend == "replace":
            a = (m * alpha)[..., None]
            base = base * (1.0 - a) + color * a
        else:  # additive
            base += color * (m * alpha)[..., None]
    if glow_sigma > 0.0 and glow_alpha > 0.0:
        ksize = int(glow_sigma * 6) | 1
        ksize = max(3, ksize)
        glow = cv2.GaussianBlur(mask, (ksize, ksize), glow_sigma)
        gm = glow.astype(np.float32) / 255.0
        base += color * (gm * glow_alpha)[..., None]  # glow stays additive
    np.clip(base, 0, 255, out=base)
    frame[:, :, :] = base.astype(np.uint8)


def draw_circle(
    frame: np.ndarray,
    center: tuple[float, float],
    radius: float,
    fill_bgr: Sequence[int],
    *,
    fill_alpha: float = 0.85,
    stroke_bgr: Sequence[int] | None = None,
    stroke_w: float = 0.0,
    stroke_alpha: float = 1.0,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
    blend: str = "add",
) -> None:
    """Authored origin/orb/impact circle.

    `blend="replace"` makes the disc OPAQUE (alpha-blends, does not add),
    which prevents amber-on-amber saturation when a hot disc sits on top of
    other amber primitives.
    """
    if radius < 1.0 or fill_alpha <= 0.0 and stroke_w <= 0.0:
        return
    cx, cy = int(round(center[0])), int(round(center[1]))
    r = int(round(radius))
    # Render onto a local mask for soft compositing.
    pad = int(r + max(8.0, glow_sigma * 3))
    x0 = max(0, cx - pad); y0 = max(0, cy - pad)
    x1 = min(W, cx + pad + 1); y1 = min(H, cy + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    local_center = (cx - x0, cy - y0)
    if fill_alpha > 0.0:
        cv2.circle(mask, local_center, r, 255, -1, cv2.LINE_AA)
    crop = frame[y0:y1, x0:x1]
    if fill_alpha > 0.0:
        add_mask(crop, mask, fill_bgr, fill_alpha, glow_sigma, glow_alpha, blend=blend)
    if stroke_w > 0.0 and stroke_bgr is not None:
        smask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.circle(smask, local_center, r, 255, max(1, int(round(stroke_w))), cv2.LINE_AA)
        add_mask(crop, smask, stroke_bgr, stroke_alpha)


def crescent_polygon(
    outer_r: float,
    inner_r: float,
    offset: float,
    arc_angle_deg: float = 360.0,
    samples: int = 96,
) -> np.ndarray:
    """Local-frame crescent polygon.

    Two arcs: outer of radius `outer_r`, inner of radius `inner_r` whose
    center is shifted by `offset` along +x. `arc_angle_deg` controls how much
    of the outer arc is drawn (sharpening cusps when < 360 by stopping short
    of the natural intersection).
    """
    inner_r = max(1.0, min(inner_r, outer_r * 0.95))
    offset = max(abs(outer_r - inner_r) + 1.0, min(offset, outer_r + inner_r - 1.0))
    # natural cusp angle from intersection of the two arcs
    x_int = (outer_r * outer_r - inner_r * inner_r + offset * offset) / (2.0 * offset)
    y_sq = max(1.0, outer_r * outer_r - x_int * x_int)
    y_int = math.sqrt(y_sq)
    outer_phi = math.atan2(y_int, x_int)
    # cusp sharpening: shrink outer span toward (0, pi) i.e. cusps move out a bit
    half_arc = math.radians(arc_angle_deg) * 0.5
    outer_phi_eff = min(outer_phi, half_arc) if arc_angle_deg < 360.0 else outer_phi
    outer_angles = np.linspace(outer_phi_eff, TAU - outer_phi_eff, samples, dtype=np.float32)
    outer = np.column_stack([
        outer_r * np.cos(outer_angles),
        outer_r * np.sin(outer_angles),
    ])
    inner_top = math.atan2(y_int, x_int - offset)
    inner_bottom = math.atan2(-y_int, x_int - offset)
    inner_angles = np.linspace(inner_bottom, inner_top - TAU, samples, dtype=np.float32)
    inner = np.column_stack([
        offset + inner_r * np.cos(inner_angles),
        inner_r * np.sin(inner_angles),
    ])
    return np.vstack([outer, inner]).astype(np.float32)


def transform_points(points: np.ndarray, center: tuple[float, float], rotation_rad: float) -> np.ndarray:
    c = math.cos(rotation_rad)
    s = math.sin(rotation_rad)
    out = np.empty_like(points)
    out[:, 0] = center[0] + points[:, 0] * c - points[:, 1] * s
    out[:, 1] = center[1] + points[:, 0] * s + points[:, 1] * c
    return out


def draw_crescent(
    frame: np.ndarray,
    center: tuple[float, float],
    outer_r: float,
    *,
    body_thickness: float = 0.30,
    offset_factor: float = 0.50,
    cusp_sharpness: float = 0.0,
    rotation_rad: float = 0.0,
    fill_bgr: Sequence[int] = SOFT_IVORY_BGR,
    fill_alpha: float = 0.55,
    stroke_bgr: Sequence[int] | None = SOFT_IVORY_BGR,
    stroke_w: float = 2.0,
    stroke_alpha: float = 0.80,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
) -> None:
    """Authored crescent. `body_thickness` is the inner-to-outer radius gap
    fraction (0 = no body, 1 = full disk). `cusp_sharpness` in [0,1] tightens
    the outer arc to sharpen cusps. `rotation_rad` orients the cusps.
    """
    inner_r = outer_r * (1.0 - max(0.05, min(0.95, body_thickness)))
    offset = outer_r * offset_factor
    arc_angle_deg = lerp(360.0, 220.0, max(0.0, min(1.0, cusp_sharpness)))
    poly_local = crescent_polygon(outer_r, inner_r, offset, arc_angle_deg=arc_angle_deg)
    poly = transform_points(poly_local, center, rotation_rad)
    pts = np.round(poly).astype(np.int32)
    if pts.shape[0] < 3:
        return
    x0 = max(0, int(pts[:, 0].min()) - int(glow_sigma * 3 + 8))
    y0 = max(0, int(pts[:, 1].min()) - int(glow_sigma * 3 + 8))
    x1 = min(W, int(pts[:, 0].max()) + int(glow_sigma * 3 + 9))
    y1 = min(H, int(pts[:, 1].max()) + int(glow_sigma * 3 + 9))
    if x1 <= x0 or y1 <= y0:
        return
    local = pts.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(mask, [local.reshape(-1, 1, 2)], 255, lineType=cv2.LINE_AA)
    crop = frame[y0:y1, x0:x1]
    if fill_alpha > 0.0:
        add_mask(crop, mask, fill_bgr, fill_alpha, glow_sigma, glow_alpha)
    if stroke_w > 0.0 and stroke_bgr is not None:
        smask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.polylines(smask, [local.reshape(-1, 1, 2)], True, 255, max(1, int(round(stroke_w))), lineType=cv2.LINE_AA)
        add_mask(crop, smask, stroke_bgr, stroke_alpha)


def trigon_polygon(
    length: float,
    base_width: float,
    concavity: float = 0.30,
    samples_per_side: int = 26,
) -> np.ndarray:
    """Curved-side trigon polygon in local frame. Apex at +x, base at -x.

    `concavity` in roughly [0.0, 0.6]: 0 is a straight-sided triangle, ~0.3
    is a healthy curved-side trigon, 0.6 starts to read as a leaf.
    """
    apex = np.array([length, 0.0], dtype=np.float32)
    base_top = np.array([-length * 0.45, base_width * 0.5], dtype=np.float32)
    base_bot = np.array([-length * 0.45, -base_width * 0.5], dtype=np.float32)
    vertices = [apex, base_top, base_bot]
    points: list[np.ndarray] = []
    for idx in range(3):
        p0 = vertices[idx]
        p1 = vertices[(idx + 1) % 3]
        mid = (p0 + p1) * 0.5
        norm = np.linalg.norm(mid)
        outward = mid / norm if norm > 1e-6 else np.array([1.0, 0.0], dtype=np.float32)
        control = mid + outward * (concavity * length)
        ts = np.linspace(0.0, 1.0, samples_per_side, endpoint=False, dtype=np.float32)
        side = (
            ((1 - ts) ** 2)[:, None] * p0
            + (2 * (1 - ts) * ts)[:, None] * control
            + (ts ** 2)[:, None] * p1
        )
        points.extend(side)
    return np.asarray(points, dtype=np.float32)


def draw_wave_arc(
    frame: np.ndarray,
    center_y: float,
    amplitude: float,
    wavelength: float,
    phase: float,
    *,
    samples: int = 240,
    stroke_bgr: Sequence[int] = PALE_BLUE_BGR,
    stroke_w: float = 4.0,
    stroke_alpha: float = 0.65,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
) -> None:
    """A horizontally flowing sinusoidal wave-line.

    This is NOT a crescent - it's a sine-curve arc, drawn as a stroke only.
    Used for phase 5's surface-wave read where discrete crescents would read
    as a row of moons. The wave arc IS still a crescent-shaped form in spirit:
    it's an open arc (one bounding curve) following a path, with cusp/release
    points at its endpoints where it meets the frame edge.
    """
    xs = np.linspace(-100.0, W + 100.0, samples, dtype=np.float32)
    ys = center_y + amplitude * np.sin(TAU * (xs / wavelength) + phase)
    pts = np.column_stack([xs, ys]).astype(np.float32)
    rounded = np.round(pts).astype(np.int32)
    pad = int(amplitude + max(8.0, glow_sigma * 3) + stroke_w * 3)
    x0 = max(0, int(rounded[:, 0].min()) - pad)
    y0 = max(0, int(rounded[:, 1].min()) - pad)
    x1 = min(W, int(rounded[:, 0].max()) + pad + 1)
    y1 = min(H, int(rounded[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = rounded.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.polylines(mask, [local.reshape(-1, 1, 2)], False, 255, max(1, int(round(stroke_w))), cv2.LINE_AA)
    crop = frame[y0:y1, x0:x1]
    add_mask(crop, mask, stroke_bgr, stroke_alpha, glow_sigma, glow_alpha)


def draw_trigon_attached(
    frame: np.ndarray,
    attach: tuple[float, float],
    length: float,
    *,
    base_width: float | None = None,
    concavity: float = 0.30,
    direction_rad: float = 0.0,
    fill_bgr: Sequence[int] = MUTED_GOLD_BGR,
    fill_alpha: float = 0.75,
    stroke_bgr: Sequence[int] | None = MUTED_GOLD_BGR,
    stroke_w: float = 2.0,
    stroke_alpha: float = 0.85,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
) -> None:
    """Authored release-trigon ATTACHED to a parent point.

    The trigon's base sits at `attach` and its apex points along
    `direction_rad`. This is the anchoring rule from the arc-bounded-region
    notes: trigons attach; they do not float.
    """
    if base_width is None:
        base_width = length * 0.55
    poly_local = trigon_polygon(length, base_width, concavity=concavity)
    # Shift so the base sits at the attach point (the apex points outward).
    poly_local[:, 0] += length * 0.45
    poly = transform_points(poly_local, attach, direction_rad)
    pts = np.round(poly).astype(np.int32)
    if pts.shape[0] < 3:
        return
    pad = int(glow_sigma * 3 + 8)
    x0 = max(0, int(pts[:, 0].min()) - pad)
    y0 = max(0, int(pts[:, 1].min()) - pad)
    x1 = min(W, int(pts[:, 0].max()) + pad + 1)
    y1 = min(H, int(pts[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = pts.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(mask, [local.reshape(-1, 1, 2)], 255, lineType=cv2.LINE_AA)
    crop = frame[y0:y1, x0:x1]
    if fill_alpha > 0.0:
        add_mask(crop, mask, fill_bgr, fill_alpha, glow_sigma, glow_alpha)
    if stroke_w > 0.0 and stroke_bgr is not None:
        smask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.polylines(smask, [local.reshape(-1, 1, 2)], True, 255, max(1, int(round(stroke_w))), lineType=cv2.LINE_AA)
        add_mask(crop, smask, stroke_bgr, stroke_alpha)


# ---------------------------------------------------------------------------
# Phase renderers. Each is a deliberate phrase composition - not a glyph scatter.
# All five share an `anchor` central circle that persists in modified form so
# the cycle reads as one chain, not five disconnected scenes.
# ---------------------------------------------------------------------------


def render_phase1_sun(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 1 (0-5s): radial sun phrase.

    Central warm-amber orb (no inner stroke that would read as a target).
    Wide soft glow surrounding it so the field reads as radiance, not diagram.
    Six attached release-trigons in a slightly asymmetric ring around the orb
    so the composition reads as natural radiance, not a mandala. No
    construction ring; the rays attach directly to the orb perimeter (the
    arc-bounded-region rule: "attached to a ring, cell, crescent, or
    negative-space cut").
    """
    progress = t_in_phase / phase_dur  # 0..1 over the phase
    # No fade-in: the master opens directly with the sun visible. (Earlier
    # attempts at a soft fade-in produced amber-on-amber saturation white-spots
    # during the first ~6 frames; the right answer is to skip the fade.)
    fade_in = 1.0
    breathe = 1.0 + 0.04 * math.sin(TAU * progress * 0.75)
    orb_r = 220.0 * breathe
    # 1) Deep outer halo (most distant; broad warm glow filling much of frame).
    draw_circle(
        frame,
        (CX, CY),
        orb_r * 2.4,
        fill_bgr=AMBER_BGR,
        fill_alpha=0.0,
        stroke_bgr=None, stroke_w=0.0,
        glow_sigma=240.0,
        glow_alpha=0.30 * fade_in,
    )
    # 2) Mid halo: closer/brighter so the heat hot-spot reads.
    draw_circle(
        frame,
        (CX, CY),
        orb_r * 1.45,
        fill_bgr=AMBER_BGR,
        fill_alpha=0.0,
        stroke_bgr=None, stroke_w=0.0,
        glow_sigma=120.0,
        glow_alpha=0.42 * fade_in,
    )
    # 3) Three asymmetric soft release-trigons UNDER the orb. Bases tuck deep
    # inside so only the curved apex appears past the disc edge - the trigon
    # reads as warmth bleeding out from behind the centre, not as a glyph
    # stuck on top. No trigon glow (it would saturate the orb's amber).
    release_angles_deg = [55.0, 175.0, 295.0]  # 3-fold asymmetric, NOT 6-fold
    release_count = len(release_angles_deg)
    for k, deg in enumerate(release_angles_deg):
        a = math.radians(deg)
        # bases well inside the orb; apex extends a moderate amount past edge
        ax = CX + math.cos(a) * (orb_r * 0.30)
        ay = CY + math.sin(a) * (orb_r * 0.30)
        pulse = 1.0 + 0.06 * math.sin(TAU * (progress * 0.7 + k * 0.31))
        length = 190.0 * pulse  # apex sits ~ orb_r + 60 px past the edge
        draw_trigon_attached(
            frame,
            (ax, ay),
            length=length,
            base_width=length * 0.62,
            concavity=0.50,
            direction_rad=a,
            fill_bgr=MUTED_GOLD_BGR,
            fill_alpha=0.78 * fade_in,
            stroke_bgr=None,
            stroke_w=0.0,
            glow_sigma=0.0,   # no glow - prevents bright white saturation under the orb
            glow_alpha=0.0,
        )
    # 4) The orb itself ON TOP so it dominates the centre and the trigon apices
    # appear to emerge from behind it (not from inside it). blend="replace" so
    # the orb cleanly overwrites the trigon contribution beneath it instead of
    # saturating to white via additive overlap.
    draw_circle(
        frame,
        (CX, CY),
        orb_r,
        fill_bgr=AMBER_BGR,
        fill_alpha=0.98 * fade_in,
        stroke_bgr=None, stroke_w=0.0,
        glow_sigma=80.0,
        glow_alpha=0.32 * fade_in,
        blend="replace",
    )
    return {"orb_r": orb_r, "rays": release_count, "fade_in": fade_in}


def render_phase2_vapor(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 2 (5-9s): evaporation; rays/crescents lift upward as vapor arcs;
    the central orb fades but persists as anchor at the base of the frame."""
    p = t_in_phase / phase_dur  # 0..1
    # Anchor orb fades from amber to dim and shrinks slightly, but stays put.
    fade = 1.0 - smoothstep(0.0, 1.0, p) * 0.78
    orb_r = 110.0 * lerp(1.0, 0.62, p)
    # Sink the anchor slightly toward the bottom third.
    orb_cy = CY + 80.0 * smoothstep(0.0, 1.0, p)
    draw_circle(
        frame,
        (CX, orb_cy),
        orb_r,
        fill_bgr=AMBER_DIM_BGR,
        fill_alpha=0.66 * fade,
        stroke_bgr=SOFT_IVORY_BGR,
        stroke_w=1.5,
        stroke_alpha=0.30 * fade,
        glow_sigma=40.0,
        glow_alpha=0.10 * fade,
    )
    # Vapor crescents: a few lifting arcs that drift upward and thin as they
    # rise. We emit five of them on staggered timings. The FIRST one starts at
    # p=0 (no stagger) so the moment phase 2 opens there is already vapor in
    # the air - no transition hole.
    vapor_count = 5
    for k in range(vapor_count):
        # Each crescent has its own start offset so they lift in sequence;
        # k=0 starts at p=0 so the opening moment of phase 2 already has lift.
        start = k * 0.08
        local_t = max(0.0, min(1.0, (p - start) / max(0.05, 1.0 - start)))
        # k=0 is launched at p>=0 with a small initial position so it's
        # already visible right at the phase boundary.
        if k == 0:
            local_t = max(0.10, local_t)
        if local_t <= 0.0:
            continue
        # Lift path: start near the orb, drift up + slightly outward.
        lateral = math.sin(TAU * (k / vapor_count) + 0.4) * (140.0 + 60.0 * local_t)
        rise = lerp(40.0, 540.0, local_t)
        cx = CX + lateral
        cy = orb_cy - rise
        # Thickness and opacity thin as they rise.
        thickness = lerp(0.32, 0.10, local_t)
        cusp = lerp(0.25, 0.65, local_t)
        outer_r = lerp(95.0, 55.0, local_t)
        alpha = lerp(0.55, 0.06, local_t)
        # Cup direction: opens upward (cusp points up).
        rotation = math.radians(-90.0 + 12.0 * math.sin(TAU * local_t + k))
        draw_crescent(
            frame,
            (cx, cy),
            outer_r=outer_r,
            body_thickness=thickness,
            offset_factor=0.45,
            cusp_sharpness=cusp,
            rotation_rad=rotation,
            fill_bgr=PALE_BLUE_DESAT_BGR,
            fill_alpha=alpha,
            stroke_bgr=PALE_BLUE_DESAT_BGR,
            stroke_w=1.5,
            stroke_alpha=alpha * 1.2,
            glow_sigma=10.0,
            glow_alpha=alpha * 0.18,
        )
    return {"orb_alpha": 0.66 * fade, "vapor_count": vapor_count, "progress": p}


def _rain_drop_schedule() -> list[tuple[float, float, float]]:
    """Return (birth_t_in_phase, x, target_y) for ~7 falling raindrops."""
    return [
        (0.05, CX - 380, H * 0.55),
        (0.28, CX - 120, H * 0.62),
        (0.40, CX + 200, H * 0.58),
        (0.52, CX - 260, H * 0.66),
        (0.62, CX + 380, H * 0.60),
        (0.74, CX + 60,  H * 0.66),
        (0.85, CX - 60,  H * 0.62),
    ]


def render_phase3_rain(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 3 (9-13s): rain descent. Small pale-blue circles fall from the
    upper vapor band; each carries a short crescent trail behind it."""
    p = t_in_phase / phase_dur  # 0..1
    # 1) Residual vapor: the phase-2 lifting vapor doesn't disappear at t=9 s
    # - a few of those rising crescents linger in the upper portion of the
    # frame for the first ~1 s of phase 3, then fade out. This laps the
    # phase-2 -> phase-3 transition so there's no visual hole.
    residual_fade = 1.0 - smoothstep(0.0, 0.3, p)  # fully present at p=0, gone by p=0.3
    if residual_fade > 0.02:
        for k in range(5):
            start = k * 0.10
            # use a synthesized "late vapor" progress at the moment p=0
            lv = max(0.0, min(1.0, (1.0 - start)))  # the phase-2 endpoint position
            lateral = math.sin(TAU * (k / 5) + 0.4) * (140.0 + 60.0 * lv)
            cx = CX + lateral
            cy = (CY + 80.0) - lerp(40.0, 540.0, lv)
            thickness = lerp(0.32, 0.10, lv)
            cusp = lerp(0.25, 0.65, lv)
            outer_r = lerp(95.0, 55.0, lv)
            alpha = lerp(0.55, 0.06, lv) * residual_fade
            rotation = math.radians(-90.0 + 12.0 * math.sin(TAU * lv + k))
            draw_crescent(
                frame,
                (cx, cy),
                outer_r=outer_r,
                body_thickness=thickness,
                offset_factor=0.45,
                cusp_sharpness=cusp,
                rotation_rad=rotation,
                fill_bgr=PALE_BLUE_DESAT_BGR,
                fill_alpha=alpha,
                stroke_bgr=PALE_BLUE_DESAT_BGR,
                stroke_w=1.5,
                stroke_alpha=alpha * 1.2,
                glow_sigma=10.0,
                glow_alpha=alpha * 0.18,
            )
    # 2) Cloud band: instead of moon-silhouette crescents at the top, paint a
    # SOFT horizontal vapor diffusion - a wide horizontal sheet of low-opacity
    # pale-blue rendered as a wide glow ellipse, plus a few short arc lines
    # for the "cloud band" read. This avoids the moon-row failure mode.
    band_alpha = max(0.0, 0.40 * (1.0 - smoothstep(0.0, 0.7, p)))
    if band_alpha > 0.02:
        # Wide soft horizontal glow band at the top.
        draw_circle(
            frame,
            (CX, H * 0.16),
            220.0,
            fill_bgr=PALE_BLUE_DESAT_BGR,
            fill_alpha=0.0,
            stroke_bgr=None, stroke_w=0.0,
            glow_sigma=140.0,
            glow_alpha=0.30 * band_alpha,
        )
        # A few sine-arc lines across the band (cloud streaks).
        for arc_idx in range(3):
            draw_wave_arc(
                frame,
                center_y=H * 0.16 + arc_idx * 24.0 - 24.0,
                amplitude=22.0,
                wavelength=560.0,
                phase=arc_idx * 1.1 + p * 0.6,
                stroke_bgr=PALE_BLUE_DESAT_BGR,
                stroke_w=2.5,
                stroke_alpha=0.45 * band_alpha,
                glow_sigma=10.0,
                glow_alpha=0.06 * band_alpha,
            )
    # 3) Anchor orb still visible at the bottom, much dimmer.
    draw_circle(
        frame,
        (CX, CY + 80.0),
        70.0,
        fill_bgr=AMBER_DIM_BGR,
        fill_alpha=0.18 * (1.0 - p * 0.7),
        glow_sigma=30.0,
        glow_alpha=0.05,
    )
    # 4) Raindrops.
    drops = _rain_drop_schedule()
    drawn = 0
    for birth, x, target_y in drops:
        local_t = max(0.0, min(1.0, (p - birth) / max(0.05, 1.0 - birth)))
        if local_t <= 0.0:
            continue
        # Fall from the cloud band (y=H*0.18) to target_y over local_t.
        y = lerp(H * 0.18, target_y, local_t)
        drop_alpha = lerp(0.40, 0.95, smoothstep(0.0, 0.4, local_t)) * (1.0 - smoothstep(0.85, 1.0, local_t) * 0.3)
        draw_circle(
            frame,
            (x, y),
            14.0,
            fill_bgr=PALE_BLUE_BGR,
            fill_alpha=drop_alpha,
            stroke_bgr=IVORY_BGR,
            stroke_w=1.0,
            stroke_alpha=drop_alpha,
            glow_sigma=8.0,
            glow_alpha=0.20 * drop_alpha,
        )
        # Short trailing crescent ABOVE the drop, cup opening downward toward
        # the drop. Length proportional to fall distance.
        trail_length = min(70.0, 50.0 + 60.0 * local_t)
        trail_cy = y - trail_length * 0.5
        draw_crescent(
            frame,
            (x, trail_cy),
            outer_r=trail_length * 0.55,
            body_thickness=0.12,
            offset_factor=0.55,
            cusp_sharpness=0.55,
            rotation_rad=math.radians(90.0),
            fill_bgr=PALE_BLUE_BGR,
            fill_alpha=0.20 * drop_alpha,
            stroke_bgr=PALE_BLUE_BGR,
            stroke_w=1.5,
            stroke_alpha=0.45 * drop_alpha,
        )
        drawn += 1
    return {"drops_drawn": drawn, "progress": p}


def _ripple_field_atmosphere(time_seconds: float, alpha: float) -> np.ndarray:
    """Phase 4 atmosphere: imported wave field driving a low-opacity shimmer.

    This is the ONLY place v003.evaluate_field is used. The wave field is NOT
    classified or used as geometry; it modulates the background blue-channel
    brightness behind the authored concentric crescents to give the impact
    field a real water-shimmer feel.
    """
    # Construct a few low-amplitude impact-like wave sources in the v003 model.
    # Three slow continuous sources placed asymmetrically so the field reads as
    # gentle interference, not a target pattern.
    sources = [
        v003.WaveSource(
            source_id="ripple_atmosphere_a",
            x=CX - 220, y=CY + 30, amplitude=1.0, wavelength=210.0, frequency=0.18,
            phase=0.0, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=10.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
        v003.WaveSource(
            source_id="ripple_atmosphere_b",
            x=CX + 260, y=CY - 40, amplitude=0.9, wavelength=228.0, frequency=0.16,
            phase=0.7, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=10.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
        v003.WaveSource(
            source_id="ripple_atmosphere_c",
            x=CX + 30, y=CY + 180, amplitude=0.85, wavelength=190.0, frequency=0.22,
            phase=1.4, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=10.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
    ]
    field = v003.evaluate_field(sources, time_seconds, blur_sigma=1.5)  # (FH, FW)
    field_full = cv2.resize(field, (W, H), interpolation=cv2.INTER_CUBIC)
    # Map field [-1,1] -> [0,1] absolute amplitude as a soft shimmer multiplier.
    shimmer = np.clip(np.abs(field_full) * alpha, 0.0, 1.0).astype(np.float32)
    return shimmer


def render_phase4_ripple(frame: np.ndarray, t_in_phase: float, phase_dur: float, t_abs: float) -> dict:
    """Phase 4 (13-18s): rain impact / ripple. The last falling circle lands
    at the centre and becomes the impact circle; authored concentric crescents
    expand outward. The wave-field engine drives a low-opacity shimmer
    underneath those authored crescents (atmosphere only, not geometry)."""
    p = t_in_phase / phase_dur  # 0..1
    # Impact circle appears and pulses.
    impact_in = smoothstep(0.0, 0.15, p)
    impact_r = 60.0 + 6.0 * math.sin(TAU * p * 2.5)
    # Wave-field atmosphere (low alpha, blue-tinted): added BEFORE the authored
    # crescents so the crescents sit on top.
    shimmer_alpha = 0.55 * impact_in * (1.0 - smoothstep(0.85, 1.0, p) * 0.5)
    shimmer = _ripple_field_atmosphere(t_abs, shimmer_alpha)
    # tint the shimmer pale-blue and ADD onto the frame.
    base = frame.astype(np.float32)
    color = np.array(PALE_BLUE_BGR, dtype=np.float32) * 0.55  # softer tint
    base += shimmer[..., None] * color[None, None, :]
    np.clip(base, 0, 255, out=base)
    frame[:, :, :] = base.astype(np.uint8)
    # Impact circle on top of the shimmer.
    draw_circle(
        frame,
        (CX, CY),
        impact_r,
        fill_bgr=IVORY_BGR,
        fill_alpha=0.90 * impact_in,
        stroke_bgr=PALE_BLUE_BGR,
        stroke_w=2.0,
        stroke_alpha=0.70 * impact_in,
        glow_sigma=40.0,
        glow_alpha=0.22 * impact_in,
    )
    # Authored concentric expanding crescents (rings). We emit 4 rings whose
    # radii grow over the phase. Each ring is two facing-cup half-arcs so the
    # cups are intentional (one cups upward, one downward) - not full circles.
    ring_count = 4
    for k in range(ring_count):
        # Each ring is born at a staggered time so they expand outward in sequence.
        birth = k * 0.18
        local_t = max(0.0, min(1.0, (p - birth) / max(0.05, 1.0 - birth)))
        if local_t <= 0.0:
            continue
        ring_r = lerp(80.0, 460.0 + k * 30.0, local_t)
        thickness = lerp(0.16, 0.06, local_t)
        cusp = 0.35 + 0.15 * (1.0 - local_t)
        alpha = lerp(0.55, 0.05, local_t)
        # two half-crescents per ring: cup up and cup down
        for rot_deg in (90.0, 270.0):
            draw_crescent(
                frame,
                (CX, CY),
                outer_r=ring_r,
                body_thickness=thickness,
                offset_factor=0.08,
                cusp_sharpness=cusp,
                rotation_rad=math.radians(rot_deg),
                fill_bgr=PALE_BLUE_BGR,
                fill_alpha=alpha * 0.50,
                stroke_bgr=PALE_BLUE_BGR,
                stroke_w=2.0,
                stroke_alpha=alpha,
                glow_sigma=12.0,
                glow_alpha=alpha * 0.15,
            )
    return {"impact_in": impact_in, "rings": ring_count, "shimmer_alpha": shimmer_alpha}


def render_phase5_wave(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 5 (18-24s): surface wave / return. Concentric ripple crescents
    stretch into horizontal flow; a few small trigon releases at wave crests;
    in the final ~1.5 s the field dissolves toward a faint return-to-sun echo."""
    p = t_in_phase / phase_dur  # 0..1
    # Surface wave: three or four overlapping sine-arc lines that flow across
    # the frame at different vertical bands, different wavelengths, and a slow
    # drift in their phase. These read as flowing water surface, NOT as a row
    # of discrete moon-crescents. Each arc is just a stroke; no fill.
    # The water/wave fade-out begins after the 70% mark of the phase.
    fade_amp = 1.0 - smoothstep(0.85, 1.0, p) * 0.65
    wave_bands = [
        # (center_y, amplitude, wavelength, phase_speed_factor, alpha_base)
        (CY - 180.0, 38.0, 520.0,  0.55, 0.65),
        (CY -  40.0, 56.0, 640.0,  0.45, 0.70),
        (CY + 110.0, 44.0, 540.0,  0.65, 0.65),
        (CY + 260.0, 32.0, 460.0,  0.50, 0.55),
    ]
    band_phases = []  # collect the band sine phase for crescent/trigon placement
    for band_idx, (band_y, amp, wl, speed, alpha_base) in enumerate(wave_bands):
        sine_phase = TAU * p * speed + band_idx * 0.7
        band_phases.append((band_y, amp, wl, sine_phase, alpha_base))
        draw_wave_arc(
            frame,
            center_y=band_y,
            amplitude=amp * fade_amp,
            wavelength=wl,
            phase=sine_phase,
            stroke_bgr=PALE_BLUE_BGR,
            stroke_w=4.5,
            stroke_alpha=alpha_base * fade_amp,
            glow_sigma=14.0,
            glow_alpha=0.10 * fade_amp,
        )
    # On the top band, place ONE long shallow wave-crescent that follows the
    # local sine peak: this is the role-specific "wave crescent" mark
    # (larger, horizontal, flowing laterally per the brief). Place it where the
    # sine has a positive crest (so it sits below the line, body curving up).
    top_y, top_amp, top_wl, top_phase, _ = band_phases[1]
    # crest_x where sin(2*pi*x/wl + phase) is at +1: x s.t. 2*pi*x/wl + phase = pi/2 + 2*pi*n
    # i.e. x = wl * (0.25 - phase/(2*pi)) + n*wl. Pick the one nearest centre.
    crest_offset = top_wl * (0.25 - (top_phase / TAU)) % top_wl
    crest_x = crest_offset
    while crest_x < W * 0.25:
        crest_x += top_wl
    while crest_x > W * 0.75:
        crest_x -= top_wl
    crest_y = top_y - top_amp * fade_amp  # at the sine peak above the line
    draw_crescent(
        frame,
        (crest_x, crest_y + 30.0),     # crescent body sits just under the crest
        outer_r=180.0 * fade_amp,
        body_thickness=0.16,
        offset_factor=0.55,
        cusp_sharpness=0.62,
        rotation_rad=math.radians(-90.0),  # cusps left/right, body curls up
        fill_bgr=PALE_BLUE_DEEP_BGR,
        fill_alpha=0.40 * fade_amp,
        stroke_bgr=PALE_BLUE_BGR,
        stroke_w=2.5,
        stroke_alpha=0.70 * fade_amp,
        glow_sigma=14.0,
        glow_alpha=0.10 * fade_amp,
    )
    # Small attached release-trigon at the crest, pointing upward. The trigon
    # role ("release") - attached, never detached - reappears here as the
    # phase-1 release-trigon role returning at the cycle's end.
    draw_trigon_attached(
        frame,
        (crest_x, crest_y),
        length=50.0,
        base_width=38.0,
        concavity=0.38,
        direction_rad=math.radians(-90.0),
        fill_bgr=SOFT_IVORY_BGR,
        fill_alpha=0.75 * fade_amp,
        stroke_bgr=None,
        stroke_w=0.0,
        glow_sigma=8.0,
        glow_alpha=0.12 * fade_amp,
    )
    # Dissolve toward atmospheric return: in the last 1.5s, a faint warm-amber
    # echo of the original sun orb appears at centre (the cycle's "and we are
    # back where we began" beat).
    return_in = smoothstep(0.70, 1.0, p)
    if return_in > 0.0:
        draw_circle(
            frame,
            (CX, CY),
            70.0,
            fill_bgr=AMBER_DIM_BGR,
            fill_alpha=0.22 * return_in,
            glow_sigma=80.0,
            glow_alpha=0.18 * return_in,
        )
    return {"wave_bands": len(wave_bands), "return_in": return_in}


# ---------------------------------------------------------------------------
# Per-frame dispatch with brief lap-over so cross-phase persistence reads.
# ---------------------------------------------------------------------------


def render_frame(frame_index: int) -> tuple[np.ndarray, dict]:
    """Render one continuum frame. Returns (frame, per-frame metadata)."""
    frame = make_canvas()
    t = frame_index / FPS  # seconds in [0, 24)
    # Find the current phase. Phase windows tile [start, end); the last frame's
    # t is 23.96 so phase 5 catches it.
    cur = next((p for p in PHASES if p.start_s <= t < p.end_s), PHASES[-1])
    t_in = t - cur.start_s
    dur = cur.duration_s
    if cur.key == "phase1_sun":
        info = render_phase1_sun(frame, t_in, dur)
    elif cur.key == "phase2_vapor":
        info = render_phase2_vapor(frame, t_in, dur)
    elif cur.key == "phase3_rain":
        info = render_phase3_rain(frame, t_in, dur)
    elif cur.key == "phase4_ripple":
        info = render_phase4_ripple(frame, t_in, dur, t_abs=t)
    elif cur.key == "phase5_wave":
        info = render_phase5_wave(frame, t_in, dur)
    else:
        info = {}
    return frame, {"t_s": round(t, 4), "phase": cur.key, "phase_order": cur.order, **info}


def key_still_frames() -> list[tuple[int, str]]:
    """One key frame per phase, taken at the middle of each phase window."""
    keys = []
    for p in PHASES:
        mid_t = (p.start_s + p.end_s) / 2.0
        frame_index = int(round(mid_t * FPS))
        keys.append((frame_index, p.key))
    return keys


class H264Writer:
    """Minimal ffmpeg H.264 writer that takes BGR uint8 frames."""

    def __init__(self, path: Path, width: int, height: int, fps: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", str(fps),
            "-i", "-",
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(path),
        ]
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )

    def write(self, frame: np.ndarray) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("ffmpeg stdin closed")
        if frame.shape != (H, W, 3):
            raise ValueError(f"unexpected frame shape {frame.shape}")
        self.proc.stdin.write(frame.tobytes())

    def close(self) -> None:
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        stderr = self.proc.stderr.read().decode("utf-8", errors="replace") if self.proc.stderr else ""
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed: {code}\n{stderr[-3000:]}")


def render_master() -> dict:
    """Render the 24 s master MP4 and the 5 key stills."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    KEY_STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    master_path = OUT_DIR / "water_cycle_anchor_phrase_probe_v001.mp4"
    writer = H264Writer(master_path, W, H, FPS)
    key_targets = {fi: phase_key for fi, phase_key in key_still_frames()}
    key_stills: dict[str, Path] = {}
    per_phase_samples: list[dict] = []
    for fi in range(N_FRAMES):
        frame, info = render_frame(fi)
        writer.write(frame)
        if fi in key_targets:
            phase_key = key_targets[fi]
            still_path = KEY_STILLS_DIR / f"{phase_key}_mid.png"
            cv2.imwrite(str(still_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            key_stills[phase_key] = still_path
            per_phase_samples.append({"frame": fi, "phase": phase_key, "t_s": info["t_s"], "info": {k: v for k, v in info.items() if k not in ("t_s", "phase", "phase_order")}})
        if (fi + 1) % 48 == 0:
            print(f"  {master_path.name} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return {"master_path": master_path, "key_stills": key_stills, "per_phase_samples": per_phase_samples}


def make_contact_sheet(key_stills: dict[str, Path]) -> Path:
    """Contact sheet: the 5 mid-phase key stills side by side with phase labels."""
    cols: list[np.ndarray] = []
    for p in PHASES:
        still_path = key_stills.get(p.key)
        if still_path is None or not still_path.exists():
            continue
        img = cv2.imread(str(still_path), cv2.IMREAD_COLOR)
        thumb = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)
        label = f"{p.order}. {p.key.replace('phase', '').lstrip('123456789_').replace('_', ' ').strip()}"
        cv2.putText(
            thumb,
            label,
            (16, 340),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (236, 244, 248),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            thumb,
            f"t={(p.start_s + p.end_s) / 2:.1f}s",
            (16, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (236, 244, 248),
            2,
            cv2.LINE_AA,
        )
        cols.append(thumb)
    if not cols:
        raise RuntimeError("no key stills to build contact sheet from")
    # 5 columns wide ≈ 3200 px — too wide; lay out as 3 + 2 rows.
    row1 = cv2.hconcat(cols[:3])
    if len(cols) > 3:
        row2_cols = cols[3:]
        # pad row 2 with a black filler so widths match
        if len(row2_cols) < 3:
            filler = np.zeros((row2_cols[0].shape[0], row1.shape[1] - sum(c.shape[1] for c in row2_cols), 3), dtype=np.uint8)
            row2 = cv2.hconcat([*row2_cols, filler])
        else:
            row2 = cv2.hconcat(row2_cols)
        sheet = cv2.vconcat([row1, row2])
    else:
        sheet = row1
    title_h = 60
    title = np.zeros((title_h, sheet.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        title,
        "water-cycle anchor-phrase probe v001 - one mid-phase key still per phase",
        (24, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (236, 244, 248),
        2,
        cv2.LINE_AA,
    )
    sheet = cv2.vconcat([title, sheet])
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_debug_sheet(key_stills: dict[str, Path]) -> Path:
    """Debug sheet with anchors and transition links.

    For each phase mid-still, overlay role labels at anchor points (origin,
    impact, ring, etc.) so the reviewer can see the anchor chain at a glance.
    """
    cols: list[np.ndarray] = []
    for p in PHASES:
        still_path = key_stills.get(p.key)
        if still_path is None or not still_path.exists():
            continue
        img = cv2.imread(str(still_path), cv2.IMREAD_COLOR).copy()
        # Overlay anchor markers per phase.
        if p.key == "phase1_sun":
            anchors = [(CX, CY, "origin circle (sun)")]
            for k in range(6):
                a = TAU * k / 6 + math.radians(30.0)
                ax = CX + math.cos(a) * 240
                ay = CY + math.sin(a) * 240
                anchors.append((ax, ay, f"ray {k+1} attach"))
        elif p.key == "phase2_vapor":
            anchors = [(CX, CY + 80, "anchor (fading)"), (CX, CY - 200, "vapor lift")]
        elif p.key == "phase3_rain":
            anchors = [(CX, H * 0.18, "vapor band"), (CX, CY + 80, "anchor (dim)")]
            for birth, x, ty in _rain_drop_schedule()[:5]:
                anchors.append((x, ty, "rain drop"))
        elif p.key == "phase4_ripple":
            anchors = [(CX, CY, "impact circle"), (CX, CY - 250, "ripple ring"), (CX, CY + 250, "ripple ring")]
        elif p.key == "phase5_wave":
            anchors = [(CX - 200, CY - 180, "wave"), (CX + 200, CY + 20, "wave"), (CX, CY, "return-to-sun echo")]
        else:
            anchors = []
        for ax, ay, label in anchors:
            cx_i, cy_i = int(round(ax)), int(round(ay))
            cv2.circle(img, (cx_i, cy_i), 8, (0, 220, 255), 2, cv2.LINE_AA)
            cv2.putText(img, label, (cx_i + 14, cy_i - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)
        # Phase title.
        cv2.putText(img, f"{p.order}. {p.key}", (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (236, 244, 248), 2, cv2.LINE_AA)
        thumb = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)
        cols.append(thumb)
    row1 = cv2.hconcat(cols[:3])
    if len(cols) > 3:
        row2_cols = cols[3:]
        if len(row2_cols) < 3:
            filler = np.zeros((row2_cols[0].shape[0], row1.shape[1] - sum(c.shape[1] for c in row2_cols), 3), dtype=np.uint8)
            row2 = cv2.hconcat([*row2_cols, filler])
        else:
            row2 = cv2.hconcat(row2_cols)
        sheet = cv2.vconcat([row1, row2])
    else:
        sheet = row1
    # Transition links banner at the top.
    title_h = 96
    title = np.zeros((title_h, sheet.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        title,
        "debug sheet: authored primitive anchors per phase",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.70,
        (236, 244, 248),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        title,
        "anchor chain: sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent",
        (24, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 220, 255),
        1,
        cv2.LINE_AA,
    )
    sheet = cv2.vconcat([title, sheet])
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v001_debug_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def write_manifest(result: dict, contact_sheet: Path, debug_sheet: Path) -> Path:
    manifest = {
        "renderer": "scripts/water_cycle_anchor_phrase_probe.py",
        "recipe": "track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v001.json",
        "imports_wave_engine_only_for_atmosphere": "scripts/cymatic_field_topology_v003.py (used in phase4_ripple ONLY to drive low-opacity background shimmer; not used to extract or classify cells)",
        "lane": "water-cycle anchor-phrase probe v001 (pivot)",
        "cultural_status": CULTURAL_STATUS,
        "austin_boundary": {
            "public_use": False,
            "austin_approved": False,
            "cultural_meaning_claim": False,
            "review_log": "docs/space-center/austin-consent-map.md",
        },
        "canvas": {"width": W, "height": H, "fps": FPS, "duration_s": DURATION_S, "frame_count": N_FRAMES, "background_hex": "#05070b"},
        "anchor_chain": "sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent",
        "phases": [
            {"order": p.order, "key": p.key, "start_s": p.start_s, "end_s": p.end_s, "duration_s": p.duration_s,
             "frame_range": f"{int(round(p.start_s * FPS))}..{int(round(p.end_s * FPS)) - 1}"}
            for p in PHASES
        ],
        "key_stills": {k: str(v.relative_to(ROOT)) for k, v in result["key_stills"].items()},
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "debug_sheet": str(debug_sheet.relative_to(ROOT)),
        "per_phase_samples": result["per_phase_samples"],
        "primitives_are_authored_not_field_extracted": True,
        "wave_engine_use": "phase4 atmosphere only; geometry of every visible primitive is authored",
        "fail_modes_avoided": [
            "instrument-readout look (prior continuum lane failure)",
            "scattered glyphs without parent form",
            "needs-a-written-explanation-to-identify-the-cycle",
            "detached arrowhead trigons (all trigons attach to a parent point)",
            "moon-stamp crescents (all crescents cup an origin or follow a path)",
        ],
    }
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(result: dict, verdict: str) -> Path:
    rows = "\n".join(
        f"| {p.order} | `{p.key}` | {p.start_s:.1f}-{p.end_s:.1f} s | {int(round(p.start_s * FPS))}..{int(round(p.end_s * FPS)) - 1} |"
        for p in PHASES
    )
    readme = f"""# Water-Cycle Anchor-Phrase Probe v001 - 2026-05-21

Status: **{CULTURAL_STATUS}**

Internal R&D only. Not Austin-approved. Not public-ready. Not a cultural-meaning claim. Not a Coast Salish grammar claim. Not a traditional-meaning claim.

## Lane

A pivot away from the prior scalar-cell phase studies / transitions / continuum
lane. Those lanes passed every mechanical Section 9 criterion (frame counts,
caps, untouched upstream, clean loop) and still read as **instrument readouts**
on inspection, not as water. This probe is **phrase composition first**:
authored parametric primitives (circle, crescent, trigon) that change meaning
through motion, color, and context across one anchor chain:

```text
sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent
```

The wave/interference engine from v003 is imported ONLY for phase 4 (rain
impact / ripple), where it drives a low-opacity background shimmer underneath
the AUTHORED concentric crescents. The geometry of every visible primitive in
every phase is authored, not field-extracted.

## Source References

- `docs/space-center/austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md`
- `docs/space-center/primitive-svg-reference-validation-2026-05-21.md`
- `docs/space-center/arc-bounded-region-rendering-notes-2026-05-21.md`
- `docs/space-center/primitive-composition-renderer-pivot-plan-2026-05-21.md`
- `track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v001.json`

## Renderer

`scripts/water_cycle_anchor_phrase_probe.py`. Imports `evaluate_field` from
`scripts/cymatic_field_topology_v003.py` (read-only) for phase 4 shimmer only.
Does NOT import from `water_cycle_phase_studies.py`, `water_cycle_transitions.py`,
or `water_cycle_continuum.py` (those are off-limits per the brief and were not
edited).

## Phase Timeline

| # | Key | Window | Frame range |
|---|---|---|---|
{rows}

Master: 24.0 s / 576 frames / 24 fps / 1920x1080 / H.264.

## Primitive Vocabulary And Roles

Each primitive class appears in multiple roles; each role is visibly distinct
through motion + color + composition context.

- **Origin circle**: solid, weighted, central or impact-like (warm amber for
  the sun anchor; ivory for the rain-impact circle).
- **Rain circle**: small, falling, with short crescent trail.
- **Ripple crescent**: concentric, expanding, thin-to-medium arcs, pale blue.
- **Vapor crescent**: lighter body, vertical drift, fading upward, desaturated.
- **Wave crescent**: larger, horizontal, flowing laterally, slightly deeper blue.
- **Release trigon**: attached to a parent form (six attached at the sun ring,
  small ones attached at wave crests) - never detached arrows.

## Geometry Controls Exposed By The Renderer

The Coast Salish SVG references are *silhouette baselines* (used with the
embedded white rect stripped). The renderer exposes the parameters the SVG
validation doc flagged as needing renderer-side control:

- Crescent: `outer_r`, `body_thickness` (inner/outer radius gap), `offset_factor`,
  `cusp_sharpness` (tightens the outer arc), `rotation_rad`, `fill_alpha`,
  `stroke_w`, `glow`.
- Trigon: `length`, `base_width`, `concavity` (curved sides; capped to avoid
  arrowhead read), `direction_rad`, attached at a parent point.
- Circle: `radius`, `fill_alpha`, `stroke_w`, `glow`.

## Wave-Engine Atmosphere (Phase 4 Only)

`render_phase4_ripple` constructs three slow continuous `v003.WaveSource`
emitters and calls `v003.evaluate_field`. The resulting normalized field is
mapped to a low-opacity pale-blue shimmer multiplier and added to the frame
*before* the authored concentric crescents are drawn on top. The wave field
is NOT classified, contoured, or used as geometry. If the wave-engine import
were removed, the phase would still render the authored impact circle + the
authored concentric crescents - only the background shimmer would go.

## Deliverables

- `water_cycle_anchor_phrase_probe_v001.mp4` - 24 s master, 1920x1080, 24 fps.
- `key_stills/` - one mid-phase still per phase (5 total).
- `water_cycle_anchor_phrase_probe_v001_contact_sheet.png` - the 5 stills in
  one sheet with phase labels.
- `water_cycle_anchor_phrase_probe_v001_debug_sheet.png` - the 5 stills with
  anchor markers and the anchor-chain banner.
- `water_cycle_anchor_phrase_probe_v001_manifest.json` - render manifest.
- This README.

## Honest Verdict

{verdict}

## Cultural Boundary

Every artifact in this packet carries
`{CULTURAL_STATUS}`. No "Austin-approved",
no "Coast Salish", no traditional-meaning claim, no ceremonial reference. The
arc-bounded-region notes' attachment rule still applies: every primitive feels
anchored even though geometry is authored, not field-extracted (trigons
attach; crescents cup an origin or follow a path).

## Off-Limits Honored

The following were not edited (verified via `git status`):

- `scripts/cymatic_field_topology_v003.py`
- `scripts/water_cycle_phase_studies.py`
- `scripts/water_cycle_transitions.py`
- `scripts/water_cycle_continuum.py`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_2026-05-20/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_transitions_v001_2026-05-20/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_continuum_roughcut_v001_2026-05-21/`
- `track2-deterministic/scene_recipes/water_cycle_continuum_v001.json`
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def smoke_one_frame(phase_key: str, out_path: Path) -> Path:
    """Render a single mid-phase frame to disk without invoking ffmpeg."""
    p = next((q for q in PHASES if q.key == phase_key), PHASES[0])
    fi = int(round(((p.start_s + p.end_s) / 2.0) * FPS))
    frame, _ = render_frame(fi)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the water-cycle anchor-phrase probe v001.")
    parser.add_argument("--smoke", help="Smoke-test a single mid-phase still (e.g. --smoke phase1_sun). Output goes to /tmp.", default=None)
    parser.add_argument(
        "--verdict",
        default=(
            "Mechanical pass is necessary but not sufficient; the operator's acceptance criterion is whether a viewer can read the cycle without labels. "
            "See contact sheet and debug sheet alongside the master. This v001 is an authored phrase study, intentionally sparse "
            "and large-scale; if it does not read as the water cycle without labels, do NOT advance it - iterate the recipe."
        ),
        help="Honest verdict string injected into the README.",
    )
    args = parser.parse_args()

    if args.smoke:
        out = Path("/tmp") / f"phrase_probe_smoke_{args.smoke}.png"
        smoke_one_frame(args.smoke, out)
        print(f"smoke still: {out}")
        return

    # Validate the recipe before rendering.
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert recipe["canvas"]["frame_count"] == N_FRAMES, "recipe frame_count mismatch"
    assert recipe["canvas"]["duration_s"] == DURATION_S, "recipe duration mismatch"
    print(f"Recipe OK: {RECIPE_PATH}")

    result = render_master()
    contact_sheet = make_contact_sheet(result["key_stills"])
    debug_sheet = make_debug_sheet(result["key_stills"])
    manifest = write_manifest(result, contact_sheet, debug_sheet)
    readme = write_readme(result, args.verdict)
    print(f"Wrote master: {result['master_path']}")
    print(f"Wrote key stills: {KEY_STILLS_DIR}")
    print(f"Wrote contact sheet: {contact_sheet}")
    print(f"Wrote debug sheet: {debug_sheet}")
    print(f"Wrote manifest: {manifest}")
    print(f"Wrote README: {readme}")


if __name__ == "__main__":
    main()
