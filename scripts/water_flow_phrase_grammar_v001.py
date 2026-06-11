#!/usr/bin/env python3
"""
water_flow_phrase_grammar_v001 -- SSD Phase 2, R&D Lane 2 (Water Dynamics / Flow-Following Grammar).

INTERNAL ONLY. Not Austin-approved. Not a public cultural-grammar claim.

Deterministic procedural renderer for Coast Salish primitive *phrases* that follow
water motion. A phrase is a travelling train of four glyphs in fixed grammar order:

    circle (origin)  ->  crescent  ->  crescent  ->  trigon (attenuation)

The circle marks where the phrase came from; the pointed trigon leads and marks
where the pulse is going / where it attenuates. Glyphs are path-led (radial /
spline / streamline), never randomly scattered, and the four glyphs of a phrase
travel rigidly together (common fate). Renders four 1920x1080 24fps 6s
black-screen additive loops.

NOT used here: topology / cymatics / seed-of-life circle-intersection geometry,
fish or animal figures, randomness. Every phrase position is an explicit
parametric function of a loop phase q in [0, 1).

Lane reference:    docs/space-center/pravin-internal-update-rd-lane-map-addendum-2026-05-20.md
Grammar reference: docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md
Pivot reference:   Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md

Usage:
    python3 scripts/water_flow_phrase_grammar_v001.py            # full render (144 frames)
    python3 scripts/water_flow_phrase_grammar_v001.py --frames 12  # fast pipeline smoke test
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

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------
W, H = 1920, 1080
FPS = 24
DUR_S = 6.0
N_FRAMES = int(round(FPS * DUR_S))          # 144

# additive primitive colours (warm origin -> cool body -> pale terminus)
COL_CIRCLE = np.array([1.00, 0.86, 0.60], np.float32)   # warm gold-white -- origin / focal anchor
COL_CRESC  = np.array([0.40, 0.83, 1.00], np.float32)   # bioluminescent cyan -- ripple body
COL_TRIGON = np.array([0.62, 1.00, 0.84], np.float32)   # pale teal-green -- attenuation terminus
COL_GUIDE  = np.array([0.16, 0.40, 0.62], np.float32)   # dim flow-channel hint

# role brightness: circle brightest (focal), trigon dimmest (attenuation, not a 2nd focal point)
I_CIRCLE = 1.05
I_CRESC  = 0.92
I_TRIGON = 0.66

# glyph geometry (px at 1080p)
R_CIRCLE = 27.0
R_CRESC  = 48.0
R_TRIGON = 28.0
GAP = 0.085                 # inter-glyph spacing along a path, in path-parameter units

EXPOSURE = 1.55             # filmic additive tone map
POST_GAMMA = 1.0 / 1.35

POND_CX, POND_CY = W * 0.5, H * 0.50

SCENES = [
    "pond_ripple_phrase_v001",
    "river_s_curve_phrase_v001",
    "waterfall_vertical_phrase_v001",
    "current_streamline_field_v001",
]


# --------------------------------------------------------------------------
# small math helpers
# --------------------------------------------------------------------------
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def window(q, w=0.10):
    """0 at q=0 and q=1, ~1 in the middle -- guarantees a seamless loop seam."""
    return smoothstep(0.0, w, q) * smoothstep(1.0, 1.0 - w, q)


def pond_env(q):
    """Short ripple lifetime: born, expand, fade, then dead for the rest of the
    loop. Zero at q=0 and q=1 so the loop seam stays clean."""
    return smoothstep(0.0, 0.10, q) * smoothstep(0.62, 0.46, q)


def _box(cx, cy, reach):
    x0 = max(0, int(math.floor(cx - reach)))
    x1 = min(W, int(math.ceil(cx + reach)))
    y0 = max(0, int(math.floor(cy - reach)))
    y1 = min(H, int(math.ceil(cy + reach)))
    return x0, y0, x1, y1


def _local(x0, y0, x1, y1, cx, cy):
    """Pixel-centre offsets from (cx, cy): lx is (1, Wb), ly is (Hb, 1)."""
    lx = (np.arange(x0, x1, dtype=np.float32) + 0.5) - cx
    ly = (np.arange(y0, y1, dtype=np.float32) + 0.5) - cy
    return lx[None, :], ly[:, None]


def _sdf_field(sdf, halo, edge=1.6, halo_w=0.5):
    """SDF -> additive intensity: solid soft-edged core plus an outer glow halo."""
    fill = smoothstep(edge, -edge, sdf)
    outer = np.exp(-(np.maximum(sdf, 0.0) / halo) ** 2)
    return np.maximum(fill, halo_w * outer)


def _add(canvas, x0, y0, x1, y1, field, color, intensity):
    canvas[y0:y1, x0:x1, :] += field[:, :, None] * (color[None, None, :] * np.float32(intensity))


# --------------------------------------------------------------------------
# primitive glyphs (all bounding-box clipped, all signed-distance based)
# --------------------------------------------------------------------------
def draw_circle(canvas, cx, cy, radius, color, intensity, halo=15.0):
    """Filled glowing disc -- the phrase origin / impact anchor."""
    if intensity <= 0.002 or radius <= 0.5:
        return
    reach = radius + halo * 2.8 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    r = np.sqrt(lx * lx + ly * ly)
    field = _sdf_field(r - radius, halo)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def draw_crescent(canvas, cx, cy, size, open_angle, color, intensity, halo=14.0,
                  cut=1.70, off_frac=1.05):
    """Crescent blade = (inside disc A, radius `size`) AND (outside disc B). Disc B is
    larger (radius `cut`*size) and offset `off_frac`*size toward `open_angle`, so the
    leftover lune is a clean ~135-degree blade tapering to two cusps -- not a fat
    near-ring. `open_angle` is the direction the concave side faces; for a phrase
    glyph it faces back toward the origin."""
    if intensity <= 0.002 or size <= 0.5:
        return
    reach = size + halo * 2.8 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    ca, sa = math.cos(open_angle), math.sin(open_angle)
    rx = ca * lx + sa * ly          # rotate so the concave side faces local +x
    ry = -sa * lx + ca * ly
    off = off_frac * size
    sdf_a = np.sqrt(rx * rx + ry * ry) - size
    bx = rx - off
    sdf_b = np.sqrt(bx * bx + ry * ry) - cut * size
    sdf = np.maximum(sdf_a, -sdf_b)  # inside A and outside larger B
    field = _sdf_field(sdf, halo)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


def _triangle_sdf(px, py, p0, p1, p2):
    """Exact signed distance to a triangle (Inigo Quilez), vectorised. Negative inside."""
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
    """A large disc placed just outside an edge; its near arc scoops a shallow
    concave curve into that edge so the trigon reads as an elegant Coast Salish
    three-point form rather than a crude straight triangle."""
    mx, my = (va[0] + vb[0]) * 0.5, (va[1] + vb[1]) * 0.5
    ex, ey = vb[0] - va[0], vb[1] - va[1]
    el = math.hypot(ex, ey)
    nx, ny = ey / el, -ex / el
    if nx * (mx - g[0]) + ny * (my - g[1]) < 0.0:   # force the normal to point away from centroid
        nx, ny = -nx, -ny
    d_off = 1.5 * el
    ccx, ccy = mx + nx * d_off, my + ny * d_off
    r = d_off + bite
    return r - np.sqrt((px - ccx) ** 2 + (py - ccy) ** 2)


def draw_trigon(canvas, cx, cy, size, point_angle, color, intensity, halo=13.0, concavity=0.10):
    """Concave-sided three-point trigon, tip pointing along `point_angle`."""
    if intensity <= 0.002 or size <= 0.5:
        return
    reach = size * 1.18 + halo * 2.8 + 4.0
    x0, y0, x1, y1 = _box(cx, cy, reach)
    if x1 <= x0 or y1 <= y0:
        return
    lx, ly = _local(x0, y0, x1, y1, cx, cy)
    ca, sa = math.cos(point_angle), math.sin(point_angle)
    rx = ca * lx + sa * ly          # rotate so the tip points along local +x
    ry = -sa * lx + ca * ly
    v0 = (size, 0.0)                       # tip (leading)
    v1 = (-0.72 * size, 0.66 * size)       # base corner
    v2 = (-0.72 * size, -0.66 * size)      # base corner
    g = ((v0[0] + v1[0] + v2[0]) / 3.0, 0.0)
    sdf = _triangle_sdf(rx, ry, v0, v1, v2)
    if concavity > 0.0:
        bite = concavity * size
        for va, vb in ((v0, v1), (v1, v2), (v2, v0)):
            sdf = np.maximum(sdf, _edge_bite(rx, ry, va, vb, g, bite))
    field = _sdf_field(sdf, halo)
    _add(canvas, x0, y0, x1, y1, field, color, intensity)


# --------------------------------------------------------------------------
# paths -- every scene is driven by an explicit parametric path, t in [0, 1]
# --------------------------------------------------------------------------
RIVER_MX, RIVER_A = 175.0, 205.0


def river_path(t):
    x = RIVER_MX + t * (W - 2.0 * RIVER_MX)
    y = H * 0.5 + RIVER_A * math.sin(2.0 * math.pi * t) + 0.17 * RIVER_A * math.sin(4.0 * math.pi * t + 0.6)
    return x, y


def river_tan(t):
    dx = W - 2.0 * RIVER_MX
    dy = (RIVER_A * 2.0 * math.pi * math.cos(2.0 * math.pi * t)
          + 0.17 * RIVER_A * 4.0 * math.pi * math.cos(4.0 * math.pi * t + 0.6))
    el = math.hypot(dx, dy)
    return dx / el, dy / el


WF_MY = 95.0
WF_LANES = [
    {"x": W * 0.300, "sway": 44.0, "ph": 0.0},
    {"x": W * 0.520, "sway": 30.0, "ph": 2.1},
    {"x": W * 0.715, "sway": 52.0, "ph": 4.0},
]


def wf_path(t, lane):
    y = WF_MY + t * (H - 2.0 * WF_MY)
    x = lane["x"] + lane["sway"] * math.sin(math.pi * 1.3 * t + lane["ph"])
    return x, y


def wf_tan(t, lane):
    dy = H - 2.0 * WF_MY
    dx = lane["sway"] * math.pi * 1.3 * math.cos(math.pi * 1.3 * t + lane["ph"])
    el = math.hypot(dx, dy)
    return dx / el, dy / el


CUR_MX = 135.0
STREAMLINES = [
    {"y": H * 0.235, "amp": 70.0,  "freq": 1.15, "ph": 0.30},
    {"y": H * 0.430, "amp": 122.0, "freq": 0.85, "ph": 2.40},
    {"y": H * 0.605, "amp": 58.0,  "freq": 1.45, "ph": 4.10},
    {"y": H * 0.790, "amp": 96.0,  "freq": 1.00, "ph": 1.10},
]


def stream_path(t, s):
    x = CUR_MX + t * (W - 2.0 * CUR_MX)
    y = s["y"] + s["amp"] * math.sin(2.0 * math.pi * s["freq"] * t + s["ph"])
    return x, y


def stream_tan(t, s):
    dx = W - 2.0 * CUR_MX
    dy = s["amp"] * 2.0 * math.pi * s["freq"] * math.cos(2.0 * math.pi * s["freq"] * t + s["ph"])
    el = math.hypot(dx, dy)
    return dx / el, dy / el


# --------------------------------------------------------------------------
# phrase rendering
# --------------------------------------------------------------------------
def render_phrase_on_path(canvas, path_fn, tan_fn, u_head, q, scale=1.0):
    """Draw one circle->crescent->crescent->trigon phrase as a rigid travelling train.
    u_head is the path parameter of the leading trigon; the circle origin trails
    3*GAP behind. Glyphs are only drawn while strictly on the path (u in [0, 1])."""
    win = float(window(q, 0.08))
    # rank 0 = trigon (head/leading), rank 3 = circle (tail/origin)
    layout = (
        (0, "trigon"),
        (1, "crescent"),
        (2, "crescent"),
        (3, "circle"),
    )
    for rank, kind in layout:
        u = u_head - rank * GAP
        if u < 0.0 or u > 1.0:        # nothing goes off-path
            continue
        x, y = path_fn(u)
        tx, ty = tan_fn(u)
        ang = math.atan2(ty, tx)
        fade = float(smoothstep(0.0, 0.07, u) * smoothstep(1.0, 0.93, u)) * win
        if fade <= 0.002:
            continue
        if kind == "circle":
            draw_circle(canvas, x, y, R_CIRCLE * scale, COL_CIRCLE, I_CIRCLE * fade)
        elif kind == "crescent":
            draw_crescent(canvas, x, y, R_CRESC * scale, ang + math.pi, COL_CRESC, I_CRESC * fade)
        else:
            draw_trigon(canvas, x, y, R_TRIGON * scale, ang, COL_TRIGON, I_TRIGON * fade)


POND_NK = 3


def frame_pond(canvas, f, n):
    """Pebble-in-still-water: a single central impact circle; three
    crescent->crescent->trigon ripple phrases are born at the impact, expand
    outward along golden-angle bearings, then fade -- so only one or two ripples
    are alive at once. Each phrase is a line of discrete glyphs (the grammar
    Austin's slide `06` teaches), with crescents cupping back toward the impact so
    they read as expanding ripple wavefronts."""
    # central impact circle: brightness and size driven by each phrase's birth pulse
    c_bright, c_size = 0.0, 20.0
    for k in range(POND_NK):
        q = (f / n + k / POND_NK) % 1.0
        e = float(pond_env(q))
        pulse = math.exp(-((q - 0.14) / 0.11) ** 2)
        c_bright += e * (0.30 + 0.85 * pulse)
        c_size = max(c_size, 20.0 + 16.0 * pulse * e)
    draw_circle(canvas, POND_CX, POND_CY, c_size, COL_CIRCLE, I_CIRCLE * min(c_bright, 1.2))

    for k in range(POND_NK):
        q = (f / n + k / POND_NK) % 1.0
        e = float(pond_env(q))
        if e <= 0.003:
            continue
        bearing = math.radians(k * 137.507 + 25.0)
        bx, by = math.cos(bearing), math.sin(bearing)
        # two crescents expand outward, cupping back toward the impact origin
        for r0, span, sz, role in ((60.0, 230.0, 58.0, 1.00), (128.0, 262.0, 54.0, 0.90)):
            r = r0 + q * span
            draw_crescent(canvas, POND_CX + bx * r, POND_CY + by * r, sz,
                          bearing + math.pi, COL_CRESC, I_CRESC * e * role)
        # trigon attenuation mark on the far ripple, pointing outward
        r_t = 212.0 + q * 250.0
        draw_trigon(canvas, POND_CX + bx * r_t, POND_CY + by * r_t, 30.0,
                    bearing, COL_TRIGON, I_TRIGON * e * 0.92)


def frame_river(canvas, f, n):
    """Phrases drift along one meandering S-curve current; nothing leaves the path."""
    span = 1.0 + 6.0 * GAP
    for off in (0.00, 0.37, 0.70):
        q = (f / n + off) % 1.0
        u_head = -3.0 * GAP + q * span
        render_phrase_on_path(canvas, river_path, river_tan, u_head, q)


def frame_waterfall(canvas, f, n):
    """Phrases descend three vertical lanes, accelerating under gravity; glyphs in
    a lane fall as one common-fate group."""
    span = 1.0 + 6.0 * GAP
    bases = (0.00, 0.18, 0.36)
    for lane, base in zip(WF_LANES, bases):
        pf = lambda t, ln=lane: wf_path(t, ln)
        tf = lambda t, ln=lane: wf_tan(t, ln)
        for off in (base, base + 0.5):
            q = (f / n + off) % 1.0
            u_head = -3.0 * GAP + (q ** 1.9) * span     # q**1.9 = gravitational acceleration
            render_phrase_on_path(canvas, pf, tf, u_head, q)


def frame_current(canvas, f, n):
    """Sparse common-fate streamlines, each carrying a phrase bundle -- a current
    field that breathes, no wallpaper density."""
    span = 1.0 + 6.0 * GAP
    assignments = ((0, 0.10), (1, 0.00), (1, 0.52), (2, 0.34), (3, 0.66))
    for idx, off in assignments:
        s = STREAMLINES[idx]
        pf = lambda t, ss=s: stream_path(t, ss)
        tf = lambda t, ss=s: stream_tan(t, ss)
        q = (f / n + off) % 1.0
        u_head = -3.0 * GAP + q * span
        render_phrase_on_path(canvas, pf, tf, u_head, q)


FRAME_FNS = {
    "pond_ripple_phrase_v001": frame_pond,
    "river_s_curve_phrase_v001": frame_river,
    "waterfall_vertical_phrase_v001": frame_waterfall,
    "current_streamline_field_v001": frame_current,
}


# --------------------------------------------------------------------------
# faint flow-channel guide layers (precomputed once per scene)
# --------------------------------------------------------------------------
def _stamp_ribbon(layer, path_fn, samples, width, peak):
    for i in range(samples):
        t = i / (samples - 1)
        x, y = path_fn(t)
        reach = width * 1.7 + 3.0
        x0, y0, x1, y1 = _box(x, y, reach)
        if x1 <= x0 or y1 <= y0:
            continue
        lx, ly = _local(x0, y0, x1, y1, x, y)
        v = np.exp(-(np.sqrt(lx * lx + ly * ly) / (width * 0.62)) ** 2) * peak
        sub = layer[y0:y1, x0:x1]
        np.maximum(sub, v, out=sub)


def build_guide(scene):
    layer = np.zeros((H, W), np.float32)
    if scene == "pond_ripple_phrase_v001":
        xs = (np.arange(W, dtype=np.float32) + 0.5) - POND_CX
        ys = (np.arange(H, dtype=np.float32) + 0.5) - POND_CY
        d = np.sqrt(xs[None, :] ** 2 + ys[:, None] ** 2)
        layer = (np.exp(-(d / 330.0) ** 2) * 0.085).astype(np.float32)
    elif scene == "river_s_curve_phrase_v001":
        _stamp_ribbon(layer, river_path, 320, 34.0, 0.090)
    elif scene == "waterfall_vertical_phrase_v001":
        for lane in WF_LANES:
            _stamp_ribbon(layer, lambda t, ln=lane: wf_path(t, ln), 300, 30.0, 0.075)
    elif scene == "current_streamline_field_v001":
        for s in STREAMLINES:
            _stamp_ribbon(layer, lambda t, ss=s: stream_path(t, ss), 320, 26.0, 0.070)
    return layer


# --------------------------------------------------------------------------
# tone map + encode
# --------------------------------------------------------------------------
def tonemap(canvas):
    x = 1.0 - np.exp(-np.maximum(canvas, 0.0) * EXPOSURE)
    x = np.power(np.clip(x, 0.0, 1.0), POST_GAMMA)
    return (x * 255.0 + 0.5).astype(np.uint8)


def render_scene(scene, outdir, n_frames):
    """Render one scene straight to an MP4; return the midpoint frame (uint8 RGB)."""
    frame_fn = FRAME_FNS[scene]
    guide = build_guide(scene)
    mid_idx = n_frames // 2
    out_mp4 = outdir / f"{scene}.mp4"

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "pipe:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    mid_frame = None
    t0 = time.time()
    for f in range(n_frames):
        canvas = np.zeros((H, W, 3), np.float32)
        shimmer = 0.80 + 0.20 * math.sin(2.0 * math.pi * f / n_frames)
        canvas += guide[:, :, None] * (COL_GUIDE[None, None, :] * np.float32(shimmer))
        frame_fn(canvas, f, n_frames)
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
        err = proc.stderr.read().decode("utf-8", "replace")
        raise RuntimeError(f"ffmpeg failed for {scene}:\n{err}")

    still = outdir / "midpoint_stills" / f"{scene}_mid.png"
    Image.fromarray(mid_frame).save(still)
    print(f"  {scene}: {n_frames} frames + still in {time.time() - t0:4.1f}s")
    return mid_frame


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------
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
        "width": int(st["width"]),
        "height": int(st["height"]),
        "codec": st["codec_name"],
        "fps": float(num) / float(den),
        "fps_raw": st["r_frame_rate"],
        "frames": int(st["nb_read_frames"]),
        "duration": float(fmt["duration"]),
        "size_kb": path.stat().st_size // 1024,
    }


def nonblank_check(frame):
    luma = (0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2])
    nonblack = int(np.count_nonzero(np.any(frame > 8, axis=2)))
    return {"max_luma": int(luma.max()), "nonblack_px": nonblack}


# --------------------------------------------------------------------------
# contact sheet
# --------------------------------------------------------------------------
SCENE_LABELS = {
    "pond_ripple_phrase_v001": "still pond -- impact circle, crescent ripples, trigon attenuation",
    "river_s_curve_phrase_v001": "river -- phrases follow one S-curve current path",
    "waterfall_vertical_phrase_v001": "waterfall -- phrases descend, gravity / common-fate",
    "current_streamline_field_v001": "current field -- sparse streamline phrase bundles",
}


def _load_font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def build_contact_sheet(stills, outpath):
    cw, ch = 960, 540
    sheet = Image.new("RGB", (cw * 2, ch * 2), (0, 0, 0))
    draw = ImageDraw.Draw(sheet)
    font_t = _load_font(26)
    font_s = _load_font(19)
    cells = [(0, 0), (cw, 0), (0, ch), (cw, ch)]
    for i, (scene, arr) in enumerate(stills):
        px, py = cells[i]
        sheet.paste(Image.fromarray(arr).resize((cw, ch), Image.LANCZOS), (px, py))
        title = f"{i + 1}  {scene}"
        sub = SCENE_LABELS[scene]
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (228, 240, 248))):
            draw.text((px + 20 + dx, py + 16 + dy), title, font=font_t, fill=fill)
        for dx, dy, fill in ((1, 1, (0, 0, 0)), (0, 0, (150, 186, 205))):
            draw.text((px + 20 + dx, py + 50 + dy), sub, font=font_s, fill=fill)
    sheet.save(outpath)
    return sheet.size


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------
def write_readme(outdir, clips, sheet_size, n_frames):
    lines = []
    a = lines.append
    a("# Water Flow Phrase Grammar v001 - 2026-05-20")
    a("")
    a("INTERNAL ONLY until Austin reviews. Layer-only black-background additive clips.")
    a("No SD / LoRA / style transfer, no topology / cymatics / seed-of-life construction")
    a("geometry, no fish or animal figures, no named/supernatural beings, no randomness.")
    a("Not Austin-approved and not a public cultural-grammar claim.")
    a("")
    a("## What This Packet Is")
    a("")
    a("Agent A revival of R&D Lane 2 (Water Dynamics / Flow-Following Grammar), kept")
    a("separate from the topology / cymatics lane. It returns to the phrase order and")
    a("flow common-fate called for in the lane-map addendum:")
    a("")
    a("    circle (origin)  ->  crescent  ->  crescent  ->  trigon (attenuation)")
    a("")
    a("A *phrase* is four primitive glyphs in fixed grammar order. The warm circle marks")
    a("the origin; the two cyan crescents are the rippling body; the dim pale-green trigon")
    a("marks where the pulse attenuates. Each phrase is path-led -- radial, spline, or")
    a("streamline -- never randomly scattered. In the river, waterfall, and current scenes")
    a("the four glyphs travel together as one common-fate train; in the pond the circle")
    a("holds at the impact point while the crescents and trigon ripple outward.")
    a("Every phrase therefore has a readable origin (circle) and a readable direction")
    a("(glyph order + trigon point + warm-to-cool hue progression).")
    a("")
    a("## Phrase Grammar Choices")
    a("")
    a("- **Circle = origin / focal anchor.** Brightest primitive, warm hue, so the eye")
    a("  lands there first (per Austin's grammar slide `06`).")
    a("- **Crescents = ripple body.** Concave side faces *back toward the origin*, convex")
    a("  bulge leads -- they read as bow-waves opening behind the travel direction.")
    a("- **Trigon = attenuation terminus.** Smaller and dimmer than the circle so it reads")
    a("  as the far/attenuated edge of the pulse, not a second focal point.")
    a("- **Loop seam:** every phrase is a continuous function of a loop phase q and is fully")
    a("  off-path (invisible) at q=0 and q=1, so frame %d == frame 0 exactly." % n_frames)
    a("")
    a("## Clips")
    a("")
    descriptions = {
        "pond_ripple_phrase_v001": (
            "Still-pond pebble metaphor: a central impact circle; three "
            "crescent->crescent->trigon ripple phrases are born at the impact, expand "
            "outward along golden-angle bearings, then fade, so only one or two ripples "
            "are alive at once. Ripples use the discrete crescent grammar, deliberately "
            "not closed concentric cymatic rings."),
        "river_s_curve_phrase_v001": (
            "Three phrases drift along a single meandering S-curve current path. Glyphs are "
            "only ever drawn while strictly on the path -- nothing goes off-path."),
        "waterfall_vertical_phrase_v001": (
            "Phrases descend three vertical lanes, accelerating under a gravity ease so the "
            "fall reads as common-fate motion. Circle origins sit at the waterfall lip."),
        "current_streamline_field_v001": (
            "Four sparse common-fate streamlines carry phrase bundles across the field. "
            "Density follows the streamlines, not a wallpaper tiling."),
    }
    methods = {
        "pond_ripple_phrase_v001": (
            "A central impact circle plus three radial phrases on a born/expand/fade "
            "envelope; each phrase places two crescent glyphs cupping back toward the "
            "impact and a trigon along an expanding radius."),
        "river_s_curve_phrase_v001": (
            "One analytic sine S-curve path; phrase head advances linearly in path "
            "parameter; glyph tangents follow the curve."),
        "waterfall_vertical_phrase_v001": (
            "Three near-vertical lane paths with slight sway; phrase head advances as "
            "phase**1.9 for gravitational acceleration."),
        "current_streamline_field_v001": (
            "Four sine streamlines at varied amplitude/frequency; one to two phrase bundles "
            "per streamline, staggered in loop phase."),
    }
    for i, c in enumerate(clips):
        pr, nb = c["ffprobe"], c["nonblank"]
        a(f"### {i + 1}. {c['scene']}.mp4")
        a("")
        a(f"- What it tests: {descriptions[c['scene']]}")
        a(f"- Technical method: {methods[c['scene']]}")
        a("- Layer role: Water layer. Resolume Screen/Additive blend over footage or black.")
        a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
          f"duration {pr['duration']:.3f}s, frames {pr['frames']}, codec {pr['codec']}, "
          f"{pr['size_kb']} KB")
        a(f"- Nonblank check: midpoint max luma {nb['max_luma']}, "
          f"nonblack pixels {nb['nonblack_px']}")
        a("")
    a("## Review Stills")
    a("")
    a("- Midpoint stills: `midpoint_stills/` (one 1920x1080 PNG per clip)")
    a(f"- Contact sheet: `contact_sheet_v001.png` ({sheet_size[0]}x{sheet_size[1]})")
    a("")
    a("## Resolume Notes")
    a("")
    a("- All clips are RGB H.264 MP4 on pure black; use Screen/Additive blend, no alpha.")
    a("- Loops are seamless (frame %d == frame 0); set the clip to loop." % n_frames)
    a("- Start water layers around 35-55% opacity over footage.")
    a("")
    a("## Constraints Honored")
    a("")
    a("- No topology / cymatics / seed-of-life circle-intersection construction geometry.")
    a("- No fish or animal figures; no named, chief, or supernatural beings.")
    a("- No random placement -- every phrase is an explicit deterministic parametric path.")
    a("- No SD / LoRA / style-transfer; pure procedural signed-distance rendering.")
    a("- Outputs written only to this folder and to `scripts/water_flow_phrase_grammar_v001.py`.")
    a("")
    a("## Open Questions For Austin")
    a("")
    a("1. Crescent orientation: here crescents cup *back toward the origin circle*. Austin")
    a("   review question 2 (should crescents cup back, face travel, or vary by water")
    a("   state) is still open -- this packet picks cup-back as a consistent default.")
    a("2. Is the crescent-grammar ripple (not concentric rings) the right read for a pond?")
    a("3. Should the faint flow-channel guide stay, or should the field be pure black?")
    a("")
    a("## Sources Read")
    a("")
    a("- Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md")
    a("- docs/space-center/topology-cell-region-taxonomy-2026-05-20.md")
    a("- docs/space-center/pravin-internal-update-rd-lane-map-addendum-2026-05-20.md")
    a("- docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md")
    a("- docs/space-center/austin-visual-morphology-atlas-2026-05-20.md")
    a("")
    a("## Regenerate")
    a("")
    a("    python3 scripts/water_flow_phrase_grammar_v001.py")
    a("")
    (outdir / "README.md").write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    repo = Path(__file__).resolve().parents[1]
    default_out = (repo / "track2-deterministic" / "morph_outputs_INTERNAL"
                   / "water_flow_phrase_grammar_v001_2026-05-20")
    ap = argparse.ArgumentParser(description="Water-flow primitive phrase grammar renderer.")
    ap.add_argument("--outdir", default=str(default_out))
    ap.add_argument("--frames", type=int, default=N_FRAMES,
                    help="frame count (use a small value for a fast pipeline smoke test)")
    ap.add_argument("--scenes", default="", help="comma-separated scene subset")
    args = ap.parse_args()

    n_frames = max(2, args.frames)
    outdir = Path(args.outdir)
    (outdir / "midpoint_stills").mkdir(parents=True, exist_ok=True)
    scenes = [s for s in (args.scenes.split(",") if args.scenes else SCENES) if s in SCENES]

    print(f"water_flow_phrase_grammar_v001 -> {outdir}")
    print(f"  {W}x{H}  {FPS}fps  {n_frames} frames  ({n_frames / FPS:.3f}s)\n")

    clips, stills = [], []
    for scene in scenes:
        mid = render_scene(scene, outdir, n_frames)
        stills.append((scene, mid))
        clips.append({
            "scene": scene,
            "ffprobe": ffprobe_check(outdir / f"{scene}.mp4"),
            "nonblank": nonblank_check(mid),
        })

    sheet_size = (0, 0)
    if len(stills) == len(SCENES):
        sheet_size = build_contact_sheet(stills, outdir / "contact_sheet_v001.png")
        print(f"  contact sheet: {sheet_size[0]}x{sheet_size[1]}")
    write_readme(outdir, clips, sheet_size, n_frames)
    print("  README.md written\n")

    # ---- verification summary ----
    print("VERIFICATION SUMMARY")
    ok = True
    for c in clips:
        pr, nb, name = c["ffprobe"], c["nonblank"], c["scene"]
        checks = {
            "1920x1080": pr["width"] == 1920 and pr["height"] == 1080,
            "24fps": abs(pr["fps"] - 24.0) < 0.01,
            f"{n_frames}frames": pr["frames"] == n_frames,
            "duration": abs(pr["duration"] - n_frames / FPS) < 0.05,
            "h264": pr["codec"] == "h264",
            "nonblank": nb["max_luma"] > 16 and nb["nonblack_px"] > 1000,
        }
        passed = all(checks.values())
        ok = ok and passed
        flags = " ".join(k for k, v in checks.items() if v)
        fail = " ".join("!" + k for k, v in checks.items() if not v)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {flags} {fail}".rstrip())

    print(f"\n{'ALL CHECKS PASSED' if ok else 'CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
