#!/usr/bin/env python3.11
"""
Water-cycle anchor-phrase probe v002 (loop closure).

Iterates v001's two named visual weaknesses and tests loop closure:

  phase 1 (sun, 0-5s):       drop cartoony 3-trigon flame-tongues;
                             use eclipse-partial crescent + 1 attached trigon at cusp;
                             replace-mode compositing prevents amber-on-amber saturation.

  phase 2 (vapor, 5-10s):    lift vapor with a warmer pale-lavender-blue palette;
                             more density; first crescent already lifting at phase open.

  phase 3 (rain, 10-15s):    drop concave-up trail crescents (shower-head failure mode);
                             cluster drops in 2-3 groups; use elongated vertical fall streaks;
                             cloud band has only an inverted-arc hint (concave-down), no crescents.

  phase 4 (ripple, 15-21s):  v001's strongest moment - kept; wider 6s window; pale-cyan.

  phase 5 (wave, 21-27s):    kept v001's attached-release-at-crest detail; deep teal.

  phase 6 (wave->vapor, 27-32s):  NEW. Spray droplets and small rising crescents born at
                                   wave-peak x-coordinates. Wave bands fade out underneath.

  phase 7 (vapor->sun, 32-36s):   NEW. Vapor crescents converge inward and warm; orb re-emerges
                                   from convergence; halo grows radially. Cycle returns to t=0.

Same primitive vocabulary as v001 (circle, crescent, trigon) carrying role mutation
through motion + color + composition context. Imports v003.evaluate_field ONLY for
phase 4 atmosphere (same scope as v001). No public/show/projector/sponsor/social use.

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
    / "water_cycle_anchor_phrase_probe_v002_loop_closure.json"
)
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_cycle_anchor_phrase_probe_v002_loop_closure_2026-05-21"
)
KEY_STILLS_DIR = OUT_DIR / "key_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"

W = 1920
H = 1080
FPS = 24
DURATION_S = 36.0
N_FRAMES = int(round(FPS * DURATION_S))  # 864
TAU = math.tau
CULTURAL_STATUS = "primitive-like water-cycle phrase study pending cultural review"

# Palette (BGR for OpenCV). Each phase has a subtle chromatic signature so
# chromatic variation does some of the role-mutation work motion alone was
# carrying in v001.
BACKGROUND_BGR = (0x0B, 0x07, 0x05)         # #05070b
AMBER_BGR = (90, 160, 235)                  # warm amber for sun/origin
AMBER_DIM_BGR = (52, 96, 142)               # dim amber for fading anchor + warm closure
AMBER_WARM_HALO_BGR = (60, 130, 200)        # softer warm-amber for halo
MUTED_GOLD_BGR = (110, 180, 240)            # ray/release warm gold
SOFT_IVORY_BGR = (220, 232, 240)            # ring / boundary highlight
IVORY_BGR = (236, 244, 248)                 # impact circle
LAVENDER_BLUE_BGR = (215, 200, 180)         # phase-2 vapor (warm-rising)
LAVENDER_BLUE_LIGHT_BGR = (228, 215, 200)   # phase-2 vapor highlight
STEEL_BLUE_BGR = (208, 168, 110)            # phase-3 rain (deeper)
STEEL_BLUE_LIGHT_BGR = (228, 192, 140)      # phase-3 rain highlight
PALE_CYAN_BGR = (240, 220, 150)             # phase-4 ripple
DEEP_TEAL_BGR = (180, 140, 70)              # phase-5 wave (deeper)
DEEP_TEAL_HIGHLIGHT_BGR = (220, 180, 100)   # phase-5 wave stroke

CX = W / 2.0
CY = H / 2.0


# ---------------------------------------------------------------------------
# Phase windows. Phase 4 is the only one that uses the wave-field atmosphere.
# Phases 6 and 7 are loop closure.
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
    PhaseWindow("phase1_sun",            1,  0.0,  5.0),
    PhaseWindow("phase2_vapor",          2,  5.0, 10.0),
    PhaseWindow("phase3_rain",           3, 10.0, 15.0),
    PhaseWindow("phase4_ripple",         4, 15.0, 21.0),
    PhaseWindow("phase5_wave",           5, 21.0, 27.0),
    PhaseWindow("phase6_wave_to_vapor",  6, 27.0, 32.0),
    PhaseWindow("phase7_vapor_to_sun",   7, 32.0, 36.0),
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
# Authored primitive drawing (kept compatible with v001's API surface but the
# behavior is unchanged - this is a standalone v002 script, not an import of
# v001).
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
    """Composite a soft mask onto the frame. blend in {"add","replace"}."""
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
    if radius < 1.0 or (fill_alpha <= 0.0 and stroke_w <= 0.0):
        return
    cx, cy = int(round(center[0])), int(round(center[1]))
    r = int(round(radius))
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
    inner_r = max(1.0, min(inner_r, outer_r * 0.95))
    offset = max(abs(outer_r - inner_r) + 1.0, min(offset, outer_r + inner_r - 1.0))
    x_int = (outer_r * outer_r - inner_r * inner_r + offset * offset) / (2.0 * offset)
    y_sq = max(1.0, outer_r * outer_r - x_int * x_int)
    y_int = math.sqrt(y_sq)
    outer_phi = math.atan2(y_int, x_int)
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
    blend: str = "add",
) -> tuple[float, float] | None:
    """Authored crescent. Returns the world-frame outer-cusp position (upper)
    when the crescent is partial-arc; useful for attaching a trigon to the
    crescent's natural cusp.
    """
    inner_r = outer_r * (1.0 - max(0.05, min(0.95, body_thickness)))
    offset = outer_r * offset_factor
    arc_angle_deg = lerp(360.0, 220.0, max(0.0, min(1.0, cusp_sharpness)))
    poly_local = crescent_polygon(outer_r, inner_r, offset, arc_angle_deg=arc_angle_deg)
    poly = transform_points(poly_local, center, rotation_rad)
    pts = np.round(poly).astype(np.int32)
    if pts.shape[0] < 3:
        return None
    x0 = max(0, int(pts[:, 0].min()) - int(glow_sigma * 3 + 8))
    y0 = max(0, int(pts[:, 1].min()) - int(glow_sigma * 3 + 8))
    x1 = min(W, int(pts[:, 0].max()) + int(glow_sigma * 3 + 9))
    y1 = min(H, int(pts[:, 1].max()) + int(glow_sigma * 3 + 9))
    if x1 <= x0 or y1 <= y0:
        return None
    local = pts.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    cv2.fillPoly(mask, [local.reshape(-1, 1, 2)], 255, lineType=cv2.LINE_AA)
    crop = frame[y0:y1, x0:x1]
    if fill_alpha > 0.0:
        add_mask(crop, mask, fill_bgr, fill_alpha, glow_sigma, glow_alpha, blend=blend)
    if stroke_w > 0.0 and stroke_bgr is not None:
        smask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.polylines(smask, [local.reshape(-1, 1, 2)], True, 255, max(1, int(round(stroke_w))), lineType=cv2.LINE_AA)
        add_mask(crop, smask, stroke_bgr, stroke_alpha)
    # Compute upper-cusp world position for caller-side attachment.
    cusp_local = np.array([math.cos(math.radians(arc_angle_deg) * 0.5) * outer_r,
                            math.sin(math.radians(arc_angle_deg) * 0.5) * outer_r], dtype=np.float32)
    cusp_w = transform_points(cusp_local.reshape(1, 2), center, rotation_rad)[0]
    return float(cusp_w[0]), float(cusp_w[1])


def trigon_polygon(
    length: float,
    base_width: float,
    concavity: float = 0.30,
    samples_per_side: int = 26,
) -> np.ndarray:
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
    if base_width is None:
        base_width = length * 0.55
    poly_local = trigon_polygon(length, base_width, concavity=concavity)
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


def draw_wave_arc(
    frame: np.ndarray,
    center_y: float,
    amplitude: float,
    wavelength: float,
    phase: float,
    *,
    samples: int = 240,
    stroke_bgr: Sequence[int] = DEEP_TEAL_HIGHLIGHT_BGR,
    stroke_w: float = 4.0,
    stroke_alpha: float = 0.65,
    glow_sigma: float = 0.0,
    glow_alpha: float = 0.0,
) -> None:
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


def draw_fall_streak(
    frame: np.ndarray,
    head_xy: tuple[float, float],
    streak_len: float,
    *,
    head_radius: float = 12.0,
    stroke_w: float = 4.0,
    head_alpha: float = 0.95,
    tail_alpha: float = 0.55,
    head_bgr: Sequence[int] = STEEL_BLUE_LIGHT_BGR,
    streak_bgr: Sequence[int] = STEEL_BLUE_BGR,
    glow_sigma: float = 6.0,
    glow_alpha: float = 0.18,
) -> None:
    """Phase-3 rain primitive: a drop head + an ELONGATED VERTICAL STREAK above
    it. This replaces v001's concave-up trail crescent that read as a
    'shower-head silhouette'. The streak is a tapered vertical line, brightest
    at the head and fading upward; the head circle sits at the bottom of the
    streak so the falling motion reads in stills.
    """
    head_x, head_y = head_xy
    # Build a tapered streak as a polyline with progressive alpha.
    samples = 14
    ys = np.linspace(head_y - streak_len, head_y, samples, dtype=np.float32)
    xs = np.full_like(ys, head_x, dtype=np.float32)
    pts = np.round(np.column_stack([xs, ys])).astype(np.int32)
    pad = int(max(8.0, glow_sigma * 3) + stroke_w * 3)
    x0 = max(0, int(pts[:, 0].min()) - pad)
    y0 = max(0, int(pts[:, 1].min()) - pad)
    x1 = min(W, int(pts[:, 0].max()) + pad + 1)
    y1 = min(H, int(pts[:, 1].max()) + pad + 1)
    if x1 <= x0 or y1 <= y0:
        return
    local = pts.copy()
    local[:, 0] -= x0
    local[:, 1] -= y0
    crop = frame[y0:y1, x0:x1]
    # Draw segments with progressive alpha (tail dim -> head bright).
    for i in range(samples - 1):
        seg_mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.line(
            seg_mask,
            tuple(local[i].tolist()),
            tuple(local[i + 1].tolist()),
            255,
            max(1, int(round(stroke_w))),
            cv2.LINE_AA,
        )
        seg_t = (i + 0.5) / (samples - 1)  # 0..1 from top to bottom
        seg_alpha = lerp(tail_alpha, head_alpha, seg_t)
        add_mask(crop, seg_mask, streak_bgr, seg_alpha)
    # Head circle on top of the streak.
    draw_circle(
        frame,
        (head_x, head_y),
        head_radius,
        fill_bgr=head_bgr,
        fill_alpha=head_alpha,
        stroke_bgr=IVORY_BGR,
        stroke_w=1.0,
        stroke_alpha=head_alpha,
        glow_sigma=glow_sigma,
        glow_alpha=glow_alpha,
    )


# ---------------------------------------------------------------------------
# Phase renderers.
# ---------------------------------------------------------------------------


def render_phase1_sun(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 1 (0-5s): radial sun phrase.

    v001's 3 perimeter release-trigons read as cartoony flame-tongues. v002
    replaces those with:

      - one ECLIPSE-PARTIAL crescent that cups the orb from one side
        (gives the orb its "warmth bleeds outward" quality without spiky
        flame-tongues), and
      - one small attached release-trigon at the upper crescent cusp.

    The orb itself uses replace-mode compositing so the underlying soft amber
    halo + crescent fill do not stack to a white saturation spot.
    """
    progress = t_in_phase / phase_dur  # 0..1 over the phase
    fade_in = 1.0
    breathe = 1.0 + 0.04 * math.sin(TAU * progress * 0.75)
    orb_r = 220.0 * breathe

    # 1) Deep outer halo (broad warm radiance filling much of frame).
    draw_circle(
        frame,
        (CX, CY),
        orb_r * 2.4,
        fill_bgr=AMBER_BGR,
        fill_alpha=0.0,
        stroke_bgr=None, stroke_w=0.0,
        glow_sigma=240.0,
        glow_alpha=0.28 * fade_in,
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
        glow_alpha=0.34 * fade_in,
    )

    # 3) Eclipse-partial crescent: cups the orb's warmth outward at one edge.
    # CRITICAL color choice: must be WARM (gold-tinted ivory), not desaturated
    # ivory, otherwise it reads as a gray moon pendant stuck to the side of
    # the sun. The crescent body wraps the orb's OUTER edge so the orb's
    # warmth visually continues into the crescent rather than the crescent
    # contrasting with it.
    crescent_center_r = orb_r * 1.18  # crescent center sits just outside orb
    crescent_angle_deg = 38.0 + 10.0 * math.sin(TAU * progress * 0.35)
    a = math.radians(crescent_angle_deg)
    crescent_cx = CX + math.cos(a) * crescent_center_r
    crescent_cy = CY + math.sin(a) * crescent_center_r
    # The crescent's natural cusp-axis is +x (cusps face +x direction). We
    # want the cusps to wrap TANGENTIALLY around the orb so they trail off
    # to either side of the orb-radial direction. Rotation = radial + 90 deg
    # so the cusp-axis is perpendicular to the radial direction, body
    # curves AROUND the orb rather than pointing back at it.
    crescent_rot = a + math.pi / 2.0
    # Warm crescent: tint between MUTED_GOLD (warm) and SOFT_IVORY (light)
    # so the crescent feels like the orb's edge-warmth, not a separate moon.
    warm_crescent_fill = lerp_color(MUTED_GOLD_BGR, SOFT_IVORY_BGR, 0.30)
    warm_crescent_stroke = lerp_color(MUTED_GOLD_BGR, SOFT_IVORY_BGR, 0.55)
    cusp_world = draw_crescent(
        frame,
        (crescent_cx, crescent_cy),
        outer_r=orb_r * 0.48,
        body_thickness=0.32,
        offset_factor=0.46,
        cusp_sharpness=0.20,
        rotation_rad=crescent_rot,
        fill_bgr=warm_crescent_fill,
        fill_alpha=0.42 * fade_in,
        stroke_bgr=warm_crescent_stroke,
        stroke_w=1.5,
        stroke_alpha=0.55 * fade_in,
        glow_sigma=22.0,
        glow_alpha=0.14 * fade_in,
    )

    # 4) The orb itself ON TOP of halo + crescent so it dominates centre.
    # replace-mode prevents amber-on-amber saturation white-spot underneath.
    draw_circle(
        frame,
        (CX, CY),
        orb_r,
        fill_bgr=AMBER_BGR,
        fill_alpha=0.98 * fade_in,
        stroke_bgr=None, stroke_w=0.0,
        glow_sigma=70.0,
        glow_alpha=0.26 * fade_in,
        blend="replace",
    )

    # 5) ONE small attached release-trigon at the crescent's upper cusp.
    # Direction points outward (away from orb center). This is the v001
    # "release" role, now anchored to the crescent, not to the orb perimeter
    # at a hard angle. Trigon is small and concave-sided so it does NOT read
    # as a flame-tongue.
    trigon_count = 0
    if cusp_world is not None:
        tx, ty = cusp_world
        # outward direction = from orb center to cusp position
        outward = math.atan2(ty - CY, tx - CX)
        # nudge slightly outward so the trigon base sits just past the cusp
        nx = tx + math.cos(outward) * 6.0
        ny = ty + math.sin(outward) * 6.0
        pulse = 1.0 + 0.05 * math.sin(TAU * progress * 0.9)
        draw_trigon_attached(
            frame,
            (nx, ny),
            length=72.0 * pulse,
            base_width=42.0,
            concavity=0.42,
            direction_rad=outward,
            fill_bgr=MUTED_GOLD_BGR,
            fill_alpha=0.78 * fade_in,
            stroke_bgr=None,
            stroke_w=0.0,
            glow_sigma=0.0,
            glow_alpha=0.0,
        )
        trigon_count = 1
    return {
        "orb_r": orb_r,
        "crescent_angle_deg": crescent_angle_deg,
        "release_trigons": trigon_count,
        "fade_in": fade_in,
    }


def render_phase2_vapor(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 2 (5-10s): evaporation. Vapor crescents lift upward and thin;
    central origin shrinks and dims as anchor at base. v002: warmer
    pale-lavender-blue palette + first crescent already lifting at phase
    start; 6 crescents emitted (vs v001's 5)."""
    p = t_in_phase / phase_dur
    fade = 1.0 - smoothstep(0.0, 1.0, p) * 0.82
    orb_r = 110.0 * lerp(1.0, 0.58, p)
    orb_cy = CY + 80.0 * smoothstep(0.0, 1.0, p)
    draw_circle(
        frame,
        (CX, orb_cy),
        orb_r,
        fill_bgr=AMBER_DIM_BGR,
        fill_alpha=0.64 * fade,
        stroke_bgr=SOFT_IVORY_BGR,
        stroke_w=1.5,
        stroke_alpha=0.28 * fade,
        glow_sigma=44.0,
        glow_alpha=0.12 * fade,
    )
    # Vapor crescents distributed across the lift PATH (vertical) at any
    # given mid-phase moment. Strategy: each crescent loops INDEPENDENTLY
    # on its own lift cycle (period < phase_dur) so at any moment, some
    # are low (just born), some are mid, some are high. This produces a
    # real stream, not a row of moons stacked at one altitude.
    #
    # Each spec: (cycle_offset_in_period, home_x_offset, cycle_period_in_p_units, size_scale)
    # cycle_offset > 0 means "this crescent is ahead in its lift cycle".
    vapor_specs = [
        # (cycle_offset, home_x_offset, cycle_period, size_scale)
        (0.55, -260.0, 1.20, 1.05),   # k=0: starts mid-cycle, already lifted
        (0.20,  220.0, 1.15, 1.00),
        (0.80, -140.0, 1.30, 0.92),   # almost at top of its cycle
        (0.05,  -40.0, 1.25, 1.10),   # just starting
        (0.65,  180.0, 1.35, 0.85),
        (0.35, -310.0, 1.20, 0.98),
        (0.90,  300.0, 1.25, 0.78),   # near end
        (0.15,   60.0, 1.30, 1.00),   # early
    ]
    vapor_count = len(vapor_specs)
    lift_max = 720.0  # max vertical lift (almost to top of frame)
    for k, (cycle_offset, home_x, period, size_scale) in enumerate(vapor_specs):
        # Cycle progress: each crescent moves at its own rate through a
        # 0..1 lift loop. local_t wraps so the crescent restarts if its
        # cycle completes before phase end.
        cycle_t = (cycle_offset + p / period) % 1.0
        # Lateral drift sinusoidally around home_x.
        lateral = home_x + math.sin(TAU * (cycle_t * 1.2 + k * 0.31)) * 56.0
        rise = lift_max * smoothstep(0.0, 1.0, cycle_t)
        cx = CX + lateral
        cy = orb_cy - rise
        thickness = lerp(0.32, 0.06, cycle_t)
        cusp = lerp(0.28, 0.70, cycle_t)
        outer_r = lerp(78.0, 22.0, cycle_t) * size_scale
        # Alpha curve: ramps in over 0..0.15 of its cycle, holds, fades over
        # 0.75..1.0 of its cycle. So crescents emerge softly at the base
        # and dissolve softly at the top.
        if cycle_t < 0.15:
            alpha_env = cycle_t / 0.15
        elif cycle_t > 0.75:
            alpha_env = max(0.0, 1.0 - (cycle_t - 0.75) / 0.25)
        else:
            alpha_env = 1.0
        alpha = lerp(0.52, 0.04, cycle_t) * alpha_env
        if alpha <= 0.02:
            continue
        rotation = math.radians(-90.0 + 22.0 * math.sin(TAU * cycle_t + k * 0.7))
        draw_crescent(
            frame,
            (cx, cy),
            outer_r=outer_r,
            body_thickness=thickness,
            offset_factor=0.46,
            cusp_sharpness=cusp,
            rotation_rad=rotation,
            fill_bgr=LAVENDER_BLUE_BGR,
            fill_alpha=alpha,
            stroke_bgr=LAVENDER_BLUE_LIGHT_BGR,
            stroke_w=1.5,
            stroke_alpha=alpha * 1.2,
            glow_sigma=14.0,
            glow_alpha=alpha * 0.24,
        )
    return {"orb_alpha": 0.64 * fade, "vapor_count": vapor_count, "progress": p}


def _rain_drop_clusters() -> list[list[tuple[float, float, float]]]:
    """Return three CLUSTERS of raindrops. Each cluster is a list of
    (birth_t_in_phase, x, target_y). v001 spread drops out evenly across the
    frame and they read as isolated splashes - v002 groups them into 3
    spatial clusters so the event reads as 'rain falling from clouds'.
    """
    cluster_left = [
        (0.05, CX - 420, H * 0.62),
        (0.18, CX - 380, H * 0.66),
        (0.32, CX - 460, H * 0.58),
        (0.45, CX - 360, H * 0.70),
    ]
    cluster_center = [
        (0.12, CX - 30,  H * 0.66),
        (0.26, CX + 40,  H * 0.62),
        (0.40, CX - 50,  H * 0.70),
        (0.55, CX + 70,  H * 0.66),
        (0.70, CX,       H * 0.74),
    ]
    cluster_right = [
        (0.20, CX + 360, H * 0.64),
        (0.34, CX + 420, H * 0.60),
        (0.48, CX + 380, H * 0.68),
        (0.62, CX + 440, H * 0.70),
    ]
    return [cluster_left, cluster_center, cluster_right]


def render_phase3_rain(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 3 (10-15s): rain descent.

    v001 read as 'shower-head silhouettes near the top'. v002:
      - Drops the concave-up trail crescent ABOVE each drop (the shape
        responsible for the shower-head read).
      - Replaces it with an elongated vertical FALL STREAK below the head
        (motion implied in stills).
      - Clusters drops in 3 spatial groups (left, center, right) so the
        event reads as a group event, not isolated splashes.
      - Cloud band has NO crescents - just a soft glow + a single hint of
        an INVERTED arc (concave-DOWN) so it does not echo splash-tops.
      - Deeper steel-blue palette so rain has its own chromatic identity.
    """
    p = t_in_phase / phase_dur

    # 1) Residual vapor lap: re-render the phase-2 endpoint state of each
    # vapor crescent, faded across the first 0.3 of phase 3. Uses the same
    # vapor_specs + cycle logic as phase 2 so the lap is visually continuous.
    residual_fade = 1.0 - smoothstep(0.0, 0.3, p)
    if residual_fade > 0.02:
        # phase-2 endpoint anchor y position
        orb_cy_end = CY + 80.0
        vapor_specs = [
            (0.55, -260.0, 1.20, 1.05),
            (0.20,  220.0, 1.15, 1.00),
            (0.80, -140.0, 1.30, 0.92),
            (0.05,  -40.0, 1.25, 1.10),
            (0.65,  180.0, 1.35, 0.85),
            (0.35, -310.0, 1.20, 0.98),
            (0.90,  300.0, 1.25, 0.78),
            (0.15,   60.0, 1.30, 1.00),
        ]
        lift_max = 720.0
        # phase-2 endpoint progress p_phase2 = 1.0 (full duration in phase 2)
        for k, (cycle_offset, home_x, period, size_scale) in enumerate(vapor_specs):
            cycle_t = (cycle_offset + 1.0 / period) % 1.0
            lateral = home_x + math.sin(TAU * (cycle_t * 1.2 + k * 0.31)) * 56.0
            rise = lift_max * smoothstep(0.0, 1.0, cycle_t)
            cx = CX + lateral
            cy = orb_cy_end - rise
            thickness = lerp(0.32, 0.06, cycle_t)
            cusp = lerp(0.28, 0.70, cycle_t)
            outer_r = lerp(78.0, 22.0, cycle_t) * size_scale
            if cycle_t < 0.15:
                alpha_env = cycle_t / 0.15
            elif cycle_t > 0.75:
                alpha_env = max(0.0, 1.0 - (cycle_t - 0.75) / 0.25)
            else:
                alpha_env = 1.0
            alpha = lerp(0.52, 0.04, cycle_t) * alpha_env * residual_fade
            if alpha <= 0.02:
                continue
            rotation = math.radians(-90.0 + 22.0 * math.sin(TAU * cycle_t + k * 0.7))
            draw_crescent(
                frame,
                (cx, cy),
                outer_r=outer_r,
                body_thickness=thickness,
                offset_factor=0.46,
                cusp_sharpness=cusp,
                rotation_rad=rotation,
                fill_bgr=LAVENDER_BLUE_BGR,
                fill_alpha=alpha,
                stroke_bgr=LAVENDER_BLUE_LIGHT_BGR,
                stroke_w=1.5,
                stroke_alpha=alpha * 1.2,
                glow_sigma=14.0,
                glow_alpha=alpha * 0.24,
            )

    # 2) Cloud band: soft horizontal glow ONLY. No crescents. A single faint
    # inverted-arc hint (concave-DOWN, opening downward toward the falling
    # rain) under the glow so the cloud feels structured but does not echo
    # splash-tops. Glow band sits in the top sixth of the frame.
    band_alpha = max(0.0, 0.48 * (1.0 - smoothstep(0.0, 0.7, p)))
    if band_alpha > 0.02:
        # Three overlapping soft horizontal glow circles forming a wide sheet
        for bx_idx, bx in enumerate([CX - 360, CX, CX + 360]):
            draw_circle(
                frame,
                (bx, H * 0.14),
                240.0,
                fill_bgr=STEEL_BLUE_LIGHT_BGR,
                fill_alpha=0.0,
                stroke_bgr=None, stroke_w=0.0,
                glow_sigma=160.0,
                glow_alpha=0.22 * band_alpha,
            )
        # Single inverted-arc hint (concave-DOWN). Drawn as a thin sine arc
        # whose curvature opens downward - this is just a stroke, NOT a
        # crescent silhouette.
        # We do this by drawing a wide low-amplitude sine arc that dips down
        # in the center (so the arc's bottom is at the LOW point, opening up).
        # Wait - we want concave-DOWN (curvature pointing down, opening upward
        # is concave-up). Concave-down = arc with its peak in the middle.
        # We want it concave-DOWN to NOT echo splash-tops (which are concave-up,
        # opening down toward the falling drops below). So our cloud hint
        # arc should be UPSIDE-DOWN relative to a shower-head: peak at center,
        # ends drooping. That reads as 'underside of cloud', not 'tops of
        # splashes'.
        xs = np.linspace(-100.0, W + 100.0, 240, dtype=np.float32)
        # arc: y = base_y - amplitude * (1 - cos(pi * x_norm))/2  for x in [W*0.2, W*0.8]
        # i.e. a single broad bump centred at CX, opening downward at the ends.
        base_y = H * 0.18
        amplitude = 28.0
        # parametrize: only draw inside a window [W*0.2, W*0.8]; outside the
        # window the curve drops off to base_y.
        in_window = (xs > W * 0.20) & (xs < W * 0.80)
        x_norm = np.where(in_window, (xs - W * 0.5) / (W * 0.30), 0.0)  # -1..1
        bump = np.where(in_window, np.cos(x_norm * (math.pi / 2)) ** 2, 0.0)
        ys = base_y - amplitude * bump
        pts = np.column_stack([xs, ys]).astype(np.float32)
        rounded = np.round(pts).astype(np.int32)
        pad = int(max(amplitude, 12.0) + 8.0)
        x0 = max(0, int(rounded[:, 0].min()) - pad)
        y0 = max(0, int(rounded[:, 1].min()) - pad)
        x1 = min(W, int(rounded[:, 0].max()) + pad + 1)
        y1 = min(H, int(rounded[:, 1].max()) + pad + 1)
        if x1 > x0 and y1 > y0:
            local = rounded.copy()
            local[:, 0] -= x0
            local[:, 1] -= y0
            mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
            cv2.polylines(mask, [local.reshape(-1, 1, 2)], False, 255, 3, cv2.LINE_AA)
            crop = frame[y0:y1, x0:x1]
            add_mask(crop, mask, STEEL_BLUE_LIGHT_BGR, 0.40 * band_alpha,
                     glow_sigma=8.0, glow_alpha=0.10 * band_alpha)

    # 3) Anchor orb still visible at the bottom, very dim.
    draw_circle(
        frame,
        (CX, CY + 80.0),
        66.0,
        fill_bgr=AMBER_DIM_BGR,
        fill_alpha=0.16 * (1.0 - p * 0.7),
        glow_sigma=30.0,
        glow_alpha=0.04,
    )

    # 4) Raindrops in clusters with fall streaks.
    clusters = _rain_drop_clusters()
    drawn = 0
    for cluster in clusters:
        for birth, x, target_y in cluster:
            local_t = max(0.0, min(1.0, (p - birth) / max(0.05, 1.0 - birth)))
            if local_t <= 0.0:
                continue
            # Fall from top of frame (cloud band y) to target_y.
            cloud_y = H * 0.18
            y = lerp(cloud_y, target_y, local_t)
            drop_alpha = lerp(0.45, 0.95, smoothstep(0.0, 0.4, local_t)) * (
                1.0 - smoothstep(0.85, 1.0, local_t) * 0.3
            )
            # Streak length grows with local_t so motion implication strengthens.
            streak_len = lerp(30.0, 110.0, local_t)
            draw_fall_streak(
                frame,
                (x, y),
                streak_len=streak_len,
                head_radius=11.0,
                stroke_w=3.0,
                head_alpha=drop_alpha,
                tail_alpha=drop_alpha * 0.45,
                head_bgr=STEEL_BLUE_LIGHT_BGR,
                streak_bgr=STEEL_BLUE_BGR,
                glow_sigma=6.0,
                glow_alpha=0.16 * drop_alpha,
            )
            drawn += 1
    return {"drops_drawn": drawn, "progress": p}


def _ripple_field_atmosphere(time_seconds: float, alpha: float) -> np.ndarray:
    """Phase 4 atmosphere: imported wave field driving a low-opacity shimmer.
    Same scope as v001 - this is the only place v003.evaluate_field is used.
    """
    sources = [
        v003.WaveSource(
            source_id="ripple_atmosphere_a",
            x=CX - 220, y=CY + 30, amplitude=1.0, wavelength=210.0, frequency=0.18,
            phase=0.0, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=12.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
        v003.WaveSource(
            source_id="ripple_atmosphere_b",
            x=CX + 260, y=CY - 40, amplitude=0.9, wavelength=228.0, frequency=0.16,
            phase=0.7, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=12.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
        v003.WaveSource(
            source_id="ripple_atmosphere_c",
            x=CX + 30, y=CY + 180, amplitude=0.85, wavelength=190.0, frequency=0.22,
            phase=1.4, decay=820.0, velocity=(0.0, 0.0), birth_time=0.0,
            lifetime=12.0, symmetry_order=0, mode="continuous_radial",
            angular_alpha=0.0,
        ),
    ]
    field = v003.evaluate_field(sources, time_seconds, blur_sigma=1.5)
    field_full = cv2.resize(field, (W, H), interpolation=cv2.INTER_CUBIC)
    shimmer = np.clip(np.abs(field_full) * alpha, 0.0, 1.0).astype(np.float32)
    return shimmer


def render_phase4_ripple(
    frame: np.ndarray, t_in_phase: float, phase_dur: float, t_abs: float
) -> dict:
    """Phase 4 (15-21s): rain impact / ripple. v001's strongest moment.
    v002 widens the window to 6s for breathing room; uses pale-cyan palette."""
    p = t_in_phase / phase_dur
    impact_in = smoothstep(0.0, 0.12, p)
    impact_r = 60.0 + 6.0 * math.sin(TAU * p * 2.5)
    shimmer_alpha = 0.55 * impact_in * (1.0 - smoothstep(0.85, 1.0, p) * 0.5)
    shimmer = _ripple_field_atmosphere(t_abs, shimmer_alpha)
    base = frame.astype(np.float32)
    color = np.array(PALE_CYAN_BGR, dtype=np.float32) * 0.55
    base += shimmer[..., None] * color[None, None, :]
    np.clip(base, 0, 255, out=base)
    frame[:, :, :] = base.astype(np.uint8)
    draw_circle(
        frame,
        (CX, CY),
        impact_r,
        fill_bgr=IVORY_BGR,
        fill_alpha=0.90 * impact_in,
        stroke_bgr=PALE_CYAN_BGR,
        stroke_w=2.0,
        stroke_alpha=0.70 * impact_in,
        glow_sigma=42.0,
        glow_alpha=0.22 * impact_in,
    )
    ring_count = 5  # one more than v001 to fill the wider 6s window
    for k in range(ring_count):
        birth = k * 0.15
        local_t = max(0.0, min(1.0, (p - birth) / max(0.05, 1.0 - birth)))
        if local_t <= 0.0:
            continue
        ring_r = lerp(80.0, 500.0 + k * 30.0, local_t)
        thickness = lerp(0.16, 0.06, local_t)
        cusp = 0.35 + 0.15 * (1.0 - local_t)
        alpha = lerp(0.55, 0.05, local_t)
        for rot_deg in (90.0, 270.0):
            draw_crescent(
                frame,
                (CX, CY),
                outer_r=ring_r,
                body_thickness=thickness,
                offset_factor=0.08,
                cusp_sharpness=cusp,
                rotation_rad=math.radians(rot_deg),
                fill_bgr=PALE_CYAN_BGR,
                fill_alpha=alpha * 0.50,
                stroke_bgr=PALE_CYAN_BGR,
                stroke_w=2.0,
                stroke_alpha=alpha,
                glow_sigma=12.0,
                glow_alpha=alpha * 0.15,
            )
    return {"impact_in": impact_in, "rings": ring_count, "shimmer_alpha": shimmer_alpha}


# Wave-band definitions for phase 5 + phase 6 (shared so phase 6 can place
# spray crescents at the same wave-peak x-coordinates phase 5 was using).
WAVE_BANDS_v2 = [
    # (center_y, amplitude, wavelength, phase_speed_factor, alpha_base)
    (CY - 180.0, 38.0, 520.0, 0.55, 0.65),
    (CY -  40.0, 56.0, 640.0, 0.45, 0.70),
    (CY + 110.0, 44.0, 540.0, 0.65, 0.65),
    (CY + 260.0, 32.0, 460.0, 0.50, 0.55),
]


def _wave_band_phases_at(p_phase5_or_phase6: float, band_idx_offset: float = 0.0) -> list[tuple[float, float, float, float, float]]:
    """Return per-band (center_y, amplitude, wavelength, sine_phase, alpha_base)
    at a given progress through phase 5. The same function is reused by
    phase 6 (with a continuing time advance) so the spray crescents in phase
    6 are born at the same wave-peak x positions phase 5 was producing.
    """
    out = []
    for band_idx, (band_y, amp, wl, speed, alpha_base) in enumerate(WAVE_BANDS_v2):
        sine_phase = TAU * (p_phase5_or_phase6 + band_idx_offset) * speed + band_idx * 0.7
        out.append((band_y, amp, wl, sine_phase, alpha_base))
    return out


def render_phase5_wave(frame: np.ndarray, t_in_phase: float, phase_dur: float) -> dict:
    """Phase 5 (21-27s): surface wave. Kept v001's attached-release-at-crest
    detail; deeper teal palette."""
    p = t_in_phase / phase_dur
    fade_amp = 1.0 - smoothstep(0.85, 1.0, p) * 0.65
    band_phases = _wave_band_phases_at(p)
    for band_y, amp, wl, sine_phase, alpha_base in band_phases:
        draw_wave_arc(
            frame,
            center_y=band_y,
            amplitude=amp * fade_amp,
            wavelength=wl,
            phase=sine_phase,
            stroke_bgr=DEEP_TEAL_HIGHLIGHT_BGR,
            stroke_w=4.5,
            stroke_alpha=alpha_base * fade_amp,
            glow_sigma=14.0,
            glow_alpha=0.10 * fade_amp,
        )
    # The wave-crescent body on the top band (band_idx=1, the deepest), at a
    # positive sine crest near centre.
    top_y, top_amp, top_wl, top_phase, _ = band_phases[1]
    crest_offset = top_wl * (0.25 - (top_phase / TAU)) % top_wl
    crest_x = crest_offset
    while crest_x < W * 0.25:
        crest_x += top_wl
    while crest_x > W * 0.75:
        crest_x -= top_wl
    crest_y = top_y - top_amp * fade_amp
    cusp_world = draw_crescent(
        frame,
        (crest_x, crest_y + 30.0),
        outer_r=180.0 * fade_amp,
        body_thickness=0.16,
        offset_factor=0.55,
        cusp_sharpness=0.62,
        rotation_rad=math.radians(-90.0),
        fill_bgr=DEEP_TEAL_BGR,
        fill_alpha=0.42 * fade_amp,
        stroke_bgr=DEEP_TEAL_HIGHLIGHT_BGR,
        stroke_w=2.5,
        stroke_alpha=0.72 * fade_amp,
        glow_sigma=14.0,
        glow_alpha=0.10 * fade_amp,
    )
    # Small attached release-trigon at the crest, pointing upward.
    draw_trigon_attached(
        frame,
        (crest_x, crest_y),
        length=50.0,
        base_width=38.0,
        concavity=0.38,
        direction_rad=math.radians(-90.0),
        fill_bgr=SOFT_IVORY_BGR,
        fill_alpha=0.78 * fade_amp,
        stroke_bgr=None,
        stroke_w=0.0,
        glow_sigma=8.0,
        glow_alpha=0.12 * fade_amp,
    )
    return {
        "wave_bands": len(WAVE_BANDS_v2),
        "crest_x": crest_x,
        "fade_amp": fade_amp,
    }


def render_phase6_wave_to_vapor(
    frame: np.ndarray, t_in_phase: float, phase_dur: float
) -> dict:
    """Phase 6 (27-32s) NEW: wave releases upward into vapor.

    Loop-closure step A. The physical anchor for this transition:
      - Wave bands continue (taking their phase from where phase 5 left off)
        but fade out over the phase: amplitude shrinks, stroke alpha falls.
      - Spray droplets are BORN at sine-peak x-coordinates of the top wave
        band so the spray reads as 'the wave releases upward', not 'random
        vapor reappears'.
      - Each spray site has a small rising crescent (parented to the spray
        site at birth) that lifts and thins as p advances. Same primitive
        vocabulary as phase 2 vapor crescents - palette is the same
        pale-lavender-blue, so the chromatic continuity tells the eye
        "this is vapor".
    """
    p = t_in_phase / phase_dur
    # Wave bands fade out more gradually so the first half of phase 6 still
    # reads as "water surface releasing" not "spray over emptiness".
    wave_fade = 1.0 - smoothstep(0.05, 0.90, p)
    # Continue wave phase from where phase 5 left off.
    band_phases = _wave_band_phases_at(p, band_idx_offset=1.0)
    if wave_fade > 0.02:
        for band_y, amp, wl, sine_phase, alpha_base in band_phases:
            # Don't taper stroke_w below 2.5 - thin lines disappear at the
            # rescaled preview size and lose the "water surface" read.
            stroke_w_dyn = max(2.5, 4.5 * wave_fade)
            draw_wave_arc(
                frame,
                center_y=band_y,
                amplitude=amp * lerp(0.85, 1.0, wave_fade),
                wavelength=wl,
                phase=sine_phase,
                stroke_bgr=DEEP_TEAL_HIGHLIGHT_BGR,
                stroke_w=stroke_w_dyn,
                stroke_alpha=alpha_base * wave_fade,
                glow_sigma=14.0 * wave_fade,
                glow_alpha=0.10 * wave_fade,
            )
    # Find sine-peak x-positions on the top wave band (band_idx=1, same band
    # phase 5 used as the lead band). Phase-5 endpoint sine-phase = top_phase
    # at p_phase5=1.0; we continue advancing through phase 6.
    top_y, top_amp, top_wl, top_phase, _ = band_phases[1]
    # All sine peaks: 2*pi*x/wl + phase = pi/2 + 2*pi*n -> x = wl*(0.25 - phase/(2pi) + n)
    peaks_x: list[float] = []
    n = -2
    while True:
        x_candidate = top_wl * (0.25 - (top_phase / TAU) + n)
        if x_candidate > W + top_wl:
            break
        if x_candidate >= -50.0 and x_candidate <= W + 50.0:
            peaks_x.append(x_candidate)
        n += 1
        if n > 8:
            break
    # Use up to 5 peaks (the most central ones)
    peaks_x_sorted = sorted(peaks_x, key=lambda x: abs(x - CX))[:5]
    # Spray sites: each peak gets multiple small lifting droplets + a thin
    # rising arc that gradually becomes a small crescent only as it rises
    # higher. The KEY visual change vs the prior iteration: droplets are
    # small and clustered, the crescent only emerges in the upper half of
    # the lift (so the lower half reads as "spray" and the upper half reads
    # as "becoming vapor"). This prevents the "row of moons on water"
    # failure mode.
    spray_count = len(peaks_x_sorted)
    crest_y = top_y - top_amp * wave_fade
    for k, peak_x in enumerate(peaks_x_sorted):
        site_start = k * 0.06
        local_t = max(0.0, min(1.0, (p - site_start) / max(0.05, 1.0 - site_start)))
        if local_t <= 0.0:
            continue
        # Lift trajectory: spray rises from crest_y toward top of frame.
        rise = lerp(0.0, H * 0.62, local_t)
        cx = peak_x
        cy_spray_head = crest_y - rise
        # 3-4 small droplet pearls along the spray column, spaced vertically
        # so motion implication is strong. Brightest at the head, dimming
        # downward toward the crest.
        droplet_count = 4
        for d in range(droplet_count):
            df = d / max(1, droplet_count - 1)  # 0..1 from head down to crest
            cy_d = lerp(cy_spray_head, crest_y, df)
            drop_r = lerp(6.0, 2.5, df)
            drop_alpha = lerp(0.85, 0.18, df) * lerp(1.0, 0.25, local_t)
            if drop_alpha > 0.03:
                draw_circle(
                    frame,
                    (cx + math.sin(TAU * local_t + k + d) * 4.0, cy_d),
                    drop_r,
                    fill_bgr=SOFT_IVORY_BGR,
                    fill_alpha=drop_alpha,
                    stroke_bgr=None, stroke_w=0.0,
                    glow_sigma=lerp(5.0, 2.5, df),
                    glow_alpha=0.18 * drop_alpha,
                )
        # Small rising crescent ONLY when the spray has risen far enough to
        # be in the upper half of the lift (becoming vapor). Below that
        # threshold, the spray is just droplets - no crescent yet.
        if local_t > 0.35:
            crescent_emerge = smoothstep(0.35, 0.75, local_t)
            crescent_alpha = lerp(0.0, 0.42, crescent_emerge) * lerp(1.0, 0.45, local_t)
            if crescent_alpha > 0.03:
                # Crescent is SMALL and THIN so it reads as a wisp of vapor,
                # not as a body crescent or moon stamp.
                outer_r = lerp(28.0, 22.0, local_t)
                thickness = lerp(0.18, 0.08, local_t)
                cusp = lerp(0.45, 0.70, local_t)
                cy_cresc = cy_spray_head - lerp(10.0, 35.0, local_t)
                draw_crescent(
                    frame,
                    (cx, cy_cresc),
                    outer_r=outer_r,
                    body_thickness=thickness,
                    offset_factor=0.45,
                    cusp_sharpness=cusp,
                    rotation_rad=math.radians(-90.0 + 14.0 * math.sin(TAU * local_t + k)),
                    fill_bgr=LAVENDER_BLUE_BGR,
                    fill_alpha=crescent_alpha,
                    stroke_bgr=LAVENDER_BLUE_LIGHT_BGR,
                    stroke_w=1.2,
                    stroke_alpha=crescent_alpha * 1.2,
                    glow_sigma=8.0,
                    glow_alpha=crescent_alpha * 0.18,
                )
    return {
        "wave_fade": wave_fade,
        "spray_sites": spray_count,
        "progress": p,
    }


def render_phase7_vapor_to_sun(
    frame: np.ndarray, t_in_phase: float, phase_dur: float
) -> dict:
    """Phase 7 (32-36s) NEW: vapor condenses back into the warm sun origin.

    Loop-closure step B. The physical anchor for this transition:
      - Vapor crescents (carried over from phase 6 spray) CONVERGE inward
        toward (CX, CY). Each crescent has a converge_vector pointing to
        center; over the phase the converge progress increases.
      - The vapor warms: palette mix from LAVENDER_BLUE to AMBER_WARM_HALO
        increases with phase progress.
      - A warm halo grows radially outward from center, brightest in the
        last 1s.
      - The orb is reborn from the convergence (its radius grows from 0 to
        the phase-1 orb_r over the phase, with the brightest growth in the
        last ~30% of the phase).
    """
    p = t_in_phase / phase_dur
    # Vapor crescents converging inward toward CX, CY. We re-derive their
    # birth x-positions from the phase-5/6 wave-peak schedule so this feels
    # like a continuation of phase 6, not a new scene.
    band_phases = _wave_band_phases_at(1.0, band_idx_offset=1.0)  # phase-5 endpoint state
    top_y, top_amp, top_wl, top_phase, _ = band_phases[1]
    peaks_x: list[float] = []
    n = -2
    while True:
        x_candidate = top_wl * (0.25 - (top_phase / TAU) + n)
        if x_candidate > W + top_wl:
            break
        if x_candidate >= -50.0 and x_candidate <= W + 50.0:
            peaks_x.append(x_candidate)
        n += 1
        if n > 8:
            break
    peaks_x_sorted = sorted(peaks_x, key=lambda x: abs(x - CX))[:5]
    # Vapor convergence: each crescent starts at the TOP of the frame (where
    # it was at end of phase 6) and converges to (CX, CY) within the FIRST
    # ~40% of phase 7. After that it fades.
    #
    # Color mix from lavender-blue to amber happens IN PARALLEL with the
    # convergence so by the time a crescent reaches the orb, its color is
    # the orb's amber.
    #
    # KEY VISUAL ANCHOR: each crescent's rotation is computed from its
    # CURRENT position - this means as it converges inward, its cusp
    # direction rotates too, so the eye sees "this thing is being PULLED
    # inward" not "this thing is sliding".
    crest_y_phase6_end = top_y - top_amp * 0.0  # at end of phase 6, wave_fade=0
    vapor_fade_global = 1.0 - smoothstep(0.30, 0.55, p)
    for k, peak_x in enumerate(peaks_x_sorted):
        # Start position: top of frame at the peak's x-coordinate.
        start_x = peak_x
        start_y = H * 0.15
        # converge progress: full convergence by p=0.45 so the mid-phase
        # moment shows the vapor mostly-arrived (not still floating at top).
        cp = smoothstep(0.0, 0.45, p)
        cx = lerp(start_x, CX, cp)
        cy = lerp(start_y, CY, cp)
        # Color mix: cool -> warm. Mostly warm by p=0.40.
        warm_mix = smoothstep(0.0, 0.40, p)
        body_color = lerp_color(LAVENDER_BLUE_BGR, AMBER_BGR, warm_mix)
        stroke_color = lerp_color(LAVENDER_BLUE_LIGHT_BGR, MUTED_GOLD_BGR, warm_mix)
        # Crescents are LARGER at start (so the journey is visible) and
        # shrink + fade as they converge. Per-crescent alpha curve: visible
        # for cp in [0.0, 0.55], then rapid fade so by cp=0.85 the crescent
        # is invisible (preventing "moon shapes embedded in the orb").
        thickness = lerp(0.32, 0.06, cp)
        outer_r = lerp(72.0, 14.0, cp)
        # Fade curve: full at cp=0, rapid fade after cp=0.55.
        if cp < 0.55:
            alpha_env = 1.0
        else:
            alpha_env = max(0.0, 1.0 - (cp - 0.55) / 0.30)
        crescent_alpha = lerp(0.62, 0.04, cp) * vapor_fade_global * alpha_env
        # Cup direction: cusps point outward from center along the current
        # radial direction. As the crescent moves inward, its rotation
        # changes - the eye reads this as "pulled inward".
        dx = cx - CX
        dy = cy - CY
        if abs(dx) > 1e-3 or abs(dy) > 1e-3:
            radial_angle = math.atan2(dy, dx)
        else:
            radial_angle = 0.0
        if crescent_alpha > 0.02:
            draw_crescent(
                frame,
                (cx, cy),
                outer_r=outer_r,
                body_thickness=thickness,
                offset_factor=0.48,
                cusp_sharpness=0.45,
                rotation_rad=radial_angle,
                fill_bgr=body_color,
                fill_alpha=crescent_alpha,
                stroke_bgr=stroke_color,
                stroke_w=1.4,
                stroke_alpha=crescent_alpha * 1.2,
                glow_sigma=14.0,
                glow_alpha=crescent_alpha * 0.30,
            )
    # Warm halo grows radially outward from center over the phase. Three
    # nested halos at different radii so the warmth feels deep. The halo
    # grows EARLY (starts at p=0.0 and is mostly there by p=0.55) so the
    # mid-phase moment already has visible warmth pulling the vapor in.
    halo_in = smoothstep(0.0, 0.55, p)
    if halo_in > 0.0:
        # Outermost broad halo (mid-phase already strong).
        draw_circle(
            frame,
            (CX, CY),
            560.0,
            fill_bgr=AMBER_WARM_HALO_BGR,
            fill_alpha=0.0,
            stroke_bgr=None, stroke_w=0.0,
            glow_sigma=260.0,
            glow_alpha=0.26 * halo_in,
        )
        # Mid halo.
        draw_circle(
            frame,
            (CX, CY),
            340.0,
            fill_bgr=AMBER_BGR,
            fill_alpha=0.0,
            stroke_bgr=None, stroke_w=0.0,
            glow_sigma=130.0,
            glow_alpha=0.34 * halo_in,
        )
    # The orb re-emerges. Grow it earlier so the mid-phase moment already
    # has a small visible warm seed at center, then expand to phase-1 size
    # by the end. This prevents the "orb just appears in the last second"
    # failure mode.
    orb_grow = smoothstep(0.10, 0.95, p)
    orb_r = lerp(35.0, 220.0, orb_grow)
    orb_alpha = lerp(0.30, 0.98, smoothstep(0.20, 0.95, p))
    if orb_alpha > 0.02:
        draw_circle(
            frame,
            (CX, CY),
            orb_r,
            fill_bgr=AMBER_BGR,
            fill_alpha=orb_alpha,
            stroke_bgr=None, stroke_w=0.0,
            glow_sigma=70.0 * orb_grow,
            glow_alpha=0.26 * orb_grow,
            blend="replace",
        )
    return {
        "vapor_fade": vapor_fade_global,
        "halo_in": halo_in,
        "orb_r": orb_r,
        "orb_alpha": orb_alpha,
        "progress": p,
    }


# ---------------------------------------------------------------------------
# Per-frame dispatch.
# ---------------------------------------------------------------------------


def render_frame(frame_index: int) -> tuple[np.ndarray, dict]:
    frame = make_canvas()
    t = frame_index / FPS  # seconds in [0, 36)
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
    elif cur.key == "phase6_wave_to_vapor":
        info = render_phase6_wave_to_vapor(frame, t_in, dur)
    elif cur.key == "phase7_vapor_to_sun":
        info = render_phase7_vapor_to_sun(frame, t_in, dur)
    else:
        info = {}
    return frame, {"t_s": round(t, 4), "phase": cur.key, "phase_order": cur.order, **info}


def key_still_frames() -> list[tuple[int, str]]:
    """One key frame per phase, at the middle of each phase window."""
    keys = []
    for p in PHASES:
        mid_t = (p.start_s + p.end_s) / 2.0
        frame_index = int(round(mid_t * FPS))
        keys.append((frame_index, p.key))
    return keys


def extra_still_frames() -> list[tuple[int, str]]:
    """Additional stills for the contact sheet (>= 10 frames total).

    Captures loop-closure beats: phase 6 mid, phase 6 late, phase 7 mid,
    phase 7 late, final frame, plus one phase-1 opening still so the loop
    closure can be compared against the start.
    """
    extras: list[tuple[int, str]] = []
    extras.append((0, "phase1_open"))
    extras.append((int(round(28.0 * FPS)), "phase6_early"))
    extras.append((int(round(31.0 * FPS)), "phase6_late"))
    extras.append((int(round(33.0 * FPS)), "phase7_early"))
    extras.append((int(round(35.5 * FPS)), "phase7_late"))
    extras.append((N_FRAMES - 1, "phase7_final"))
    return extras


class H264Writer:
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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    KEY_STILLS_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    master_path = OUT_DIR / "water_cycle_anchor_phrase_probe_v002_loop_closure.mp4"
    writer = H264Writer(master_path, W, H, FPS)
    key_targets: dict[int, str] = {}
    for fi, phase_key in key_still_frames():
        key_targets[fi] = phase_key
    for fi, name in extra_still_frames():
        key_targets[fi] = name
    key_stills: dict[str, Path] = {}
    per_phase_samples: list[dict] = []
    for fi in range(N_FRAMES):
        frame, info = render_frame(fi)
        writer.write(frame)
        if fi in key_targets:
            phase_key = key_targets[fi]
            still_path = KEY_STILLS_DIR / f"{phase_key}.png"
            cv2.imwrite(str(still_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            key_stills[phase_key] = still_path
            per_phase_samples.append({
                "frame": fi,
                "phase": phase_key,
                "t_s": info["t_s"],
                "info": {k: v for k, v in info.items() if k not in ("t_s", "phase", "phase_order")},
            })
        if (fi + 1) % 48 == 0:
            print(f"  {master_path.name} {fi + 1}/{N_FRAMES}", flush=True)
    writer.close()
    return {"master_path": master_path, "key_stills": key_stills, "per_phase_samples": per_phase_samples}


# ---------------------------------------------------------------------------
# Contact + debug sheets.
# ---------------------------------------------------------------------------


def make_contact_sheet(key_stills: dict[str, Path]) -> Path:
    """Contact sheet with 11 frames (>= 10 required):
    one mid-phase still per phase (7) + phase1_open + phase6_late + phase7_early + phase7_final.
    """
    layout_order = [
        "phase1_open",       # 0s opening
        "phase1_sun",        # 2.5s mid
        "phase2_vapor",      # 7.5s mid
        "phase3_rain",       # 12.5s mid
        "phase4_ripple",     # 18s mid
        "phase5_wave",       # 24s mid
        "phase6_early",      # 28s
        "phase6_wave_to_vapor",  # 29.5s mid
        "phase6_late",       # 31s
        "phase7_early",      # 33s
        "phase7_vapor_to_sun",   # 34s mid
        "phase7_final",      # last frame (35.96s)
    ]
    cols: list[np.ndarray] = []
    for name in layout_order:
        still_path = key_stills.get(name)
        if still_path is None or not still_path.exists():
            continue
        img = cv2.imread(str(still_path), cv2.IMREAD_COLOR)
        thumb = cv2.resize(img, (480, 270), interpolation=cv2.INTER_AREA)
        label = name.replace("phase", "").replace("_", " ").strip()
        cv2.putText(thumb, label, (12, 252), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                    (236, 244, 248), 1, cv2.LINE_AA)
        # Time label
        if name in ("phase1_open",):
            t_label = "t=0.0s"
        elif name == "phase6_early":
            t_label = "t=28.0s"
        elif name == "phase6_late":
            t_label = "t=31.0s"
        elif name == "phase7_early":
            t_label = "t=33.0s"
        elif name == "phase7_final":
            t_label = "t=35.96s"
        else:
            phase = next((p for p in PHASES if p.key == name), None)
            if phase is not None:
                t_label = f"t={(phase.start_s + phase.end_s) / 2:.1f}s"
            else:
                t_label = ""
        if t_label:
            cv2.putText(thumb, t_label, (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                        (236, 244, 248), 1, cv2.LINE_AA)
        cols.append(thumb)
    if not cols:
        raise RuntimeError("no key stills to build contact sheet from")
    # Layout: 4 columns x 3 rows = 12 cells (pad blank if fewer).
    cols_per_row = 4
    rows: list[np.ndarray] = []
    for r in range(0, len(cols), cols_per_row):
        row_cols = cols[r:r + cols_per_row]
        while len(row_cols) < cols_per_row:
            blank = np.zeros_like(row_cols[0])
            row_cols.append(blank)
        rows.append(cv2.hconcat(row_cols))
    sheet = cv2.vconcat(rows)
    title_h = 64
    title = np.zeros((title_h, sheet.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        title,
        "water-cycle anchor-phrase probe v002 loop closure - mid + boundary stills (>= 10 frames)",
        (16, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (236, 244, 248),
        2,
        cv2.LINE_AA,
    )
    sheet = cv2.vconcat([title, sheet])
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v002_loop_closure_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_debug_sheet(key_stills: dict[str, Path]) -> Path:
    """Debug sheet showing anchor continuity across phases.

    Overlay anchor markers for each phase mid-still + the new loop-closure
    transition frames. The anchor chain is the literal vocabulary chain
    sun_circle -> rising_vapor -> rain_circle -> ripple_circle ->
    wave_crescent -> spray_vapor -> sun_circle (loop closure).
    """
    layout_order = [
        ("phase1_sun", "1. sun"),
        ("phase2_vapor", "2. vapor"),
        ("phase3_rain", "3. rain"),
        ("phase4_ripple", "4. ripple"),
        ("phase5_wave", "5. wave"),
        ("phase6_wave_to_vapor", "6. wave -> vapor"),
        ("phase7_vapor_to_sun", "7. vapor -> sun"),
        ("phase7_final", "7. final (returns to opening)"),
    ]
    cols: list[np.ndarray] = []
    for key, label in layout_order:
        still_path = key_stills.get(key)
        if still_path is None or not still_path.exists():
            continue
        img = cv2.imread(str(still_path), cv2.IMREAD_COLOR).copy()
        anchors = _debug_anchors_for(key)
        for ax, ay, anchor_label in anchors:
            cx_i, cy_i = int(round(ax)), int(round(ay))
            cv2.circle(img, (cx_i, cy_i), 8, (0, 220, 255), 2, cv2.LINE_AA)
            cv2.putText(img, anchor_label, (cx_i + 14, cy_i - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(img, label, (24, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                    (236, 244, 248), 2, cv2.LINE_AA)
        thumb = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)
        cols.append(thumb)
    cols_per_row = 4
    rows: list[np.ndarray] = []
    for r in range(0, len(cols), cols_per_row):
        row_cols = cols[r:r + cols_per_row]
        while len(row_cols) < cols_per_row:
            blank = np.zeros_like(row_cols[0])
            row_cols.append(blank)
        rows.append(cv2.hconcat(row_cols))
    sheet = cv2.vconcat(rows)
    title_h = 96
    title = np.zeros((title_h, sheet.shape[1], 3), dtype=np.uint8)
    cv2.putText(
        title,
        "debug sheet: authored primitive anchors per phase (v002 loop closure)",
        (24, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.66,
        (236, 244, 248),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        title,
        "anchor chain: sun -> vapor -> rain -> ripple -> wave -> spray_vapor -> sun (loop closure)",
        (24, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.54,
        (200, 220, 255),
        1,
        cv2.LINE_AA,
    )
    sheet = cv2.vconcat([title, sheet])
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v002_loop_closure_debug_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def _debug_anchors_for(key: str) -> list[tuple[float, float, str]]:
    if key == "phase1_sun":
        return [
            (CX, CY, "origin circle"),
            (CX + 220 * 1.05 * math.cos(math.radians(38.0)),
             CY + 220 * 1.05 * math.sin(math.radians(38.0)),
             "eclipse crescent"),
            (CX + 280, CY + 220, "trigon (attached)"),
        ]
    if key == "phase2_vapor":
        return [
            (CX, CY + 80, "anchor (fading)"),
            (CX, CY - 200, "vapor lift"),
        ]
    if key == "phase3_rain":
        anchors = [(CX, H * 0.14, "cloud band (no crescents)")]
        for cluster in _rain_drop_clusters():
            x = sum(c[1] for c in cluster) / len(cluster)
            y = sum(c[2] for c in cluster) / len(cluster)
            anchors.append((x, y, "rain cluster"))
        return anchors
    if key == "phase4_ripple":
        return [
            (CX, CY, "impact circle"),
            (CX, CY - 280, "ripple ring (upper)"),
            (CX, CY + 280, "ripple ring (lower)"),
        ]
    if key == "phase5_wave":
        return [
            (CX - 240, CY - 180, "wave band"),
            (CX + 200, CY + 110, "wave band"),
            (CX, CY - 96, "wave crescent (attached trigon)"),
        ]
    if key == "phase6_wave_to_vapor":
        # show 3 spray sites + the receding wave bands
        anchors = [
            (CX - 320, CY - 280, "spray site"),
            (CX, CY - 300, "spray site"),
            (CX + 320, CY - 280, "spray site"),
            (CX, CY + 110, "wave band (fading)"),
        ]
        return anchors
    if key == "phase7_vapor_to_sun":
        return [
            (CX, CY, "sun re-emerging"),
            (CX - 240, CY - 200, "vapor converging"),
            (CX + 240, CY - 200, "vapor converging"),
            (CX, CY - 360, "vapor converging"),
        ]
    if key == "phase7_final":
        return [
            (CX, CY, "sun (matches phase 1 opening)"),
        ]
    return []


def write_manifest(result: dict, contact_sheet: Path, debug_sheet: Path) -> Path:
    manifest = {
        "renderer": "scripts/water_cycle_anchor_phrase_probe_v002.py",
        "recipe": "track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v002_loop_closure.json",
        "imports_wave_engine_only_for_atmosphere": "scripts/cymatic_field_topology_v003.py (used in phase4_ripple ONLY to drive low-opacity background shimmer; not used to extract or classify cells)",
        "lane": "water-cycle anchor-phrase probe v002 loop closure (iterates v001's named weaknesses + adds closure phases 6-7)",
        "cultural_status": CULTURAL_STATUS,
        "austin_boundary": {
            "public_use": False,
            "austin_approved": False,
            "cultural_meaning_claim": False,
            "review_log": "docs/space-center/austin-consent-map.md",
        },
        "canvas": {
            "width": W, "height": H, "fps": FPS,
            "duration_s": DURATION_S, "frame_count": N_FRAMES, "background_hex": "#05070b",
        },
        "anchor_chain": "sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent -> spray_vapor -> sun_circle (loop closure)",
        "phases": [
            {
                "order": p.order, "key": p.key,
                "start_s": p.start_s, "end_s": p.end_s, "duration_s": p.duration_s,
                "frame_range": f"{int(round(p.start_s * FPS))}..{int(round(p.end_s * FPS)) - 1}",
            }
            for p in PHASES
        ],
        "key_stills": {k: str(v.relative_to(ROOT)) for k, v in result["key_stills"].items()},
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "debug_sheet": str(debug_sheet.relative_to(ROOT)),
        "per_phase_samples": result["per_phase_samples"],
        "primitives_are_authored_not_field_extracted": True,
        "wave_engine_use": "phase4 atmosphere only; geometry of every visible primitive is authored",
        "v001_fixes_attempted": {
            "phase1_sun": "drop 3-trigon flame-tongues; replace with eclipse-partial crescent + 1 attached trigon at cusp; replace-mode compositing",
            "phase3_rain": "drop concave-up trail crescents (shower-head silhouette failure mode); cluster drops in 3 groups; elongated vertical fall streaks; concave-DOWN cloud-band hint instead",
            "color_story": "each phase has a subtle palette signature; chromatic variation does some role-mutation work motion was carrying in v001",
        },
        "new_phases_for_loop_closure": {
            "phase6_wave_to_vapor": "spray crescents born at wave-peak x-positions; wave bands recede; spray rises and thins",
            "phase7_vapor_to_sun": "vapor converges + warms (palette mix lavender -> amber); orb re-emerges from convergence; final frame matches phase 1 opening",
        },
        "fail_modes_avoided": [
            "instrument-readout look (prior continuum lane failure)",
            "scattered glyphs without parent form",
            "needs-a-written-explanation-to-identify-the-cycle",
            "detached arrowhead trigons (all trigons attach to a parent point)",
            "moon-stamp crescents (all crescents cup an origin or follow a path)",
            "cartoony flame-tongue sun (v001 phase-1 failure mode - attempted fix)",
            "shower-head silhouette rain (v001 phase-3 failure mode - attempted fix)",
            "tacked-on loop closure (acceptance test - see README verdict)",
        ],
    }
    path = OUT_DIR / "water_cycle_anchor_phrase_probe_v002_loop_closure_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(result: dict, verdict: str) -> Path:
    rows = "\n".join(
        f"| {p.order} | `{p.key}` | {p.start_s:.1f}-{p.end_s:.1f} s | {int(round(p.start_s * FPS))}..{int(round(p.end_s * FPS)) - 1} |"
        for p in PHASES
    )
    readme = f"""# Water-Cycle Anchor-Phrase Probe v002 Loop Closure - 2026-05-21

Status: **{CULTURAL_STATUS}**

Internal R&D only. Not Austin-approved. Not public-ready. Not a cultural-meaning claim. Not a Coast Salish grammar claim. Not a traditional-meaning claim.

## Lane

Direct iteration of `water_cycle_anchor_phrase_probe_v001` (24 s, 5 phases),
which the prior worker self-assessed as MID / PASSABLE. v002 extends to 36 s,
adds two loop-closure phases (6 wave -> vapor, 7 vapor -> sun), and fixes the
two named v001 weaknesses:

- **phase 1 sun (v001 fix)**: replace the 3 perimeter release-trigons (which
  read as cartoony flame-tongues) with one **eclipse-partial crescent** that
  cups the orb from one side + one small attached release-trigon at the cusp.
  The orb uses **replace-mode compositing** so the underlying halo + crescent
  fill do NOT stack to a saturation white-spot.
- **phase 3 rain (v001 fix)**: drop the concave-up trail crescent above each
  raindrop (the shape responsible for the **shower-head silhouette read**).
  Replace with an **elongated vertical fall streak** below the drop head.
  **Cluster** drops into 3 spatial groups (left, center, right). Cloud band
  has no crescents - just a soft glow + a single **concave-DOWN** inverted-arc
  hint (so it does not echo splash-tops).

Same primitive vocabulary (circle, crescent, trigon) carries role mutation
through motion + color + composition context across seven phases now:

```text
sun_circle -> rising_vapor -> rain_circle -> ripple_circle -> wave_crescent
           -> spray_vapor   -> sun_circle (loop closure)
```

The v003 wave/interference engine is imported ONLY for phase 4 (ripple)
shimmer atmosphere - same scope as v001. The geometry of every visible
primitive in every phase is authored.

## Source References

- `docs/space-center/austin-reference-motifs-for-water-cycle-cymatics-2026-05-20.md`
- `docs/space-center/primitive-svg-reference-validation-2026-05-21.md`
- `docs/space-center/arc-bounded-region-rendering-notes-2026-05-21.md`
- `track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v002_loop_closure.json`
- v001 lane: `track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v001_2026-05-21/README.md`

## Renderer

`scripts/water_cycle_anchor_phrase_probe_v002.py`. Imports `evaluate_field`
from `scripts/cymatic_field_topology_v003.py` (read-only) for phase 4 shimmer
only. Does NOT import from `water_cycle_phase_studies.py`,
`water_cycle_transitions.py`, `water_cycle_continuum.py`, or the v001 script
(those are off-limits per the brief and were not edited).

## Phase Timeline

| # | Key | Window | Frame range |
|---|---|---|---|
{rows}

Master: 36.0 s / {N_FRAMES} frames / 24 fps / 1920x1080 / H.264.

## Color Story

v001 was mono-cool except for the warm sun. v002 gives each phase a subtle
palette signature so chromatic variation does some of the role-mutation
work motion alone was carrying in v001:

- phase 1 (sun): warm amber + soft ivory
- phase 2 (vapor): pale lavender-blue (warm-rising rather than cold-mist)
- phase 3 (rain): deeper steel-blue (rain has its own chromatic identity)
- phase 4 (ripple): ivory + pale cyan
- phase 5 (wave): deep teal
- phase 6 (spray): pale lavender-blue (visual continuity with phase 2 - tells
  the eye "this is vapor again")
- phase 7 (closure): pale lavender-blue -> warm amber color mix as vapor
  converges and warms

## Loop Closure Anchors

The acceptance test for v002 is whether the loop closure (phases 6 and 7)
feels plausible, not tacked on. The physical-visual anchors:

- **Phase 6 (wave -> vapor)**: each rising spray crescent is **parented** to
  a phase-5/6 sine-peak x-coordinate of the lead wave band. So spray is
  born at the wave peaks - the lift reads as "the wave releases upward".
  Spray color matches phase-2 vapor (pale lavender-blue) so the eye reads
  it as "this is vapor again".
- **Phase 7 (vapor -> sun)**: each converging vapor crescent has a
  converge-vector pointing at (CX, CY). Over the phase: progress increases
  (closer to center), warmth increases (palette mix lavender-blue -> amber),
  thickness decreases. A warm halo grows radially from center; the orb
  re-emerges from the convergence and matches phase-1's orb_r by t=36s.

If either of these reads as "and then it just is vapor/sun again" instead
of as a physical transformation, the closure is failing.

## Wave-Engine Atmosphere (Phase 4 Only)

`render_phase4_ripple` constructs three slow continuous `v003.WaveSource`
emitters and calls `v003.evaluate_field`. The resulting normalized field is
mapped to a low-opacity pale-cyan shimmer multiplier and added to the frame
*before* the authored concentric crescents are drawn on top. The wave field
is NOT classified, contoured, or used as geometry. If the wave-engine import
were removed, the phase would still render the authored impact circle + the
authored concentric crescents - only the background shimmer would go.

## Deliverables

- `water_cycle_anchor_phrase_probe_v002_loop_closure.mp4` - 36 s master.
- `key_stills/` - one mid-phase still per phase (7) + 6 transition stills
  (phase1_open, phase6_early, phase6_late, phase7_early, phase7_late,
  phase7_final). Total 13 stills.
- `water_cycle_anchor_phrase_probe_v002_loop_closure_contact_sheet.png` - 12
  stills in a 4x3 grid with phase labels.
- `water_cycle_anchor_phrase_probe_v002_loop_closure_debug_sheet.png` - 8
  stills with anchor markers + the anchor-chain banner.
- `water_cycle_anchor_phrase_probe_v002_loop_closure_manifest.json` - render
  manifest with v001-fix attempts + new-phase records.
- This README.

## Honest Verdict

{verdict}

## Cultural Boundary

Every artifact in this packet carries
`{CULTURAL_STATUS}`. No "Austin-approved",
no "Coast Salish", no traditional-meaning claim, no ceremonial reference. The
arc-bounded-region attachment rule still applies: every primitive feels
anchored (trigons attach to parent forms; crescents cup an origin or follow
a path; spray crescents in phase 6 are parented to wave peaks; converging
vapor crescents in phase 7 are parented to the central origin).

## Off-Limits Honored

The following were not edited:

- `scripts/cymatic_field_topology_v003.py`
- `scripts/water_cycle_phase_studies.py`
- `scripts/water_cycle_transitions.py`
- `scripts/water_cycle_continuum.py`
- `scripts/water_cycle_anchor_phrase_probe.py` (v001 - kept reproducible)
- `track2-deterministic/scene_recipes/water_cycle_continuum_v001.json`
- `track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v001.json`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_2026-05-20/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_transitions_v001_2026-05-20/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_continuum_roughcut_v001_2026-05-21/`
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v001_2026-05-21/`
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def smoke_one_frame(frame_t_s: float, out_path: Path) -> Path:
    fi = int(round(frame_t_s * FPS))
    fi = max(0, min(N_FRAMES - 1, fi))
    frame, _ = render_frame(fi)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the water-cycle anchor-phrase probe v002 loop closure."
    )
    parser.add_argument(
        "--smoke",
        help="Smoke-test a single frame at the given seconds-in-master (e.g. --smoke 2.5).",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--verdict",
        default=(
            "Placeholder verdict - replaced post-render with operator-style "
            "PASSABLE/MID/FAIL self-assessment across (a) v001 fixes, "
            "(b) new closure phases 6+7, (c) loop-as-a-whole."
        ),
        help="Honest verdict string injected into the README.",
    )
    args = parser.parse_args()

    if args.smoke is not None:
        out = Path("/tmp") / f"phrase_probe_v002_smoke_{args.smoke:.1f}s.png"
        smoke_one_frame(args.smoke, out)
        print(f"smoke still: {out}")
        return

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
