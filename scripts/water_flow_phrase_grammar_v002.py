#!/usr/bin/env python3
"""
water_flow_phrase_grammar_v002 -- SSD Phase 2, R&D Lane 2 (Water Dynamics / Flow-Following Grammar).

INTERNAL ONLY. Not Austin-approved. Not a public cultural-grammar claim.

A focused refinement of the two strongest v001 clips -- current_streamline_field
and waterfall_vertical_phrase. The pond and river scenes are intentionally dropped.

Refinements over v001:
  - Scale: larger, bolder primitives for projection readability.
  - Glow: a two-tier bloom (tight core halo + wide soft bloom) for a richer,
    more bioluminescent look.
  - Motion: each glyph carries a short curved wake of soft blobs receding along
    its path, so travelling phrases read as smooth, connected flow.
  - Spacing: per-scene glyph spacing tuned to pixel size; gentler entry/exit fades.

Primary outputs are black-screen layer-only loops (1920x1080, 24fps, 6s, additive).
The script also renders optional low-opacity composite previews of each layer over
Moonfish water / kelp footage, so reviewers can see how the layer reads over real
footage in Resolume. The black-screen clips remain the primary deliverable.

Same constraints as v001: no fish or animals, no topology / cymatics / seed-of-life
construction geometry, no prompt scenes, no SD/LoRA, no randomness.

Lane reference:    docs/space-center/pravin-internal-update-rd-lane-map-addendum-2026-05-20.md
Grammar reference: docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md

Usage:
    python3 scripts/water_flow_phrase_grammar_v002.py             # full render + composites
    python3 scripts/water_flow_phrase_grammar_v002.py --frames 12 # fast pipeline smoke test
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

COL_CIRCLE = np.array([1.00, 0.86, 0.60], np.float32)   # warm gold-white -- origin / focal anchor
COL_CRESC  = np.array([0.40, 0.83, 1.00], np.float32)   # bioluminescent cyan -- rippling body
COL_TRIGON = np.array([0.62, 1.00, 0.84], np.float32)   # pale teal-green -- attenuation terminus
COL_GUIDE  = np.array([0.16, 0.40, 0.62], np.float32)   # dim flow-channel hint

I_CIRCLE = 1.05
I_CRESC  = 0.92
I_TRIGON = 0.66

# v002 scale-up for projection readability
R_CIRCLE = 32.0
R_CRESC  = 58.0
R_TRIGON = 33.0

# two-tier glow
GLOW_TIGHT = 14.0
GLOW_WIDE  = 34.0

# motion-trail wake
TRAIL_N    = 3
TRAIL_GAP  = 0.013
TRAIL_FALL = 0.52

EXPOSURE = 1.58
POST_GAMMA = 1.0 / 1.35

SCENES = ["current_streamline_field_v002", "waterfall_vertical_phrase_v002"]


# --------------------------------------------------------------------------
# math helpers
# --------------------------------------------------------------------------
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
    """SDF -> additive intensity: a crisp soft-edged core, a clean tight halo, and
    just a whisper of wide bloom -- bold and projection-readable, not hazy."""
    fill = smoothstep(1.7, -1.7, sdf)
    pos = np.maximum(sdf, 0.0)
    glow_tight = np.exp(-(pos / GLOW_TIGHT) ** 2)
    glow_wide = np.exp(-(pos / GLOW_WIDE) ** 2)
    return np.maximum(fill, np.maximum(0.52 * glow_tight, 0.10 * glow_wide))


def _add(canvas, x0, y0, x1, y1, field, color, intensity):
    canvas[y0:y1, x0:x1, :] += field[:, :, None] * (color[None, None, :] * np.float32(intensity))


# --------------------------------------------------------------------------
# primitive glyphs
# --------------------------------------------------------------------------
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
    """Crescent = a tapered circular-arc blade. It cups toward `open_angle` (the
    concave side) and tapers to two sharp cusps. The arc spans ~110 degrees -- well
    under 180 -- so it reads as a clean bold blade and never rings an enclosed dark
    core the way a deep two-disc lune does at large scale."""
    if intensity <= 0.002 or size <= 0.5:
        return
    r_spine = size * 1.20
    half_span = 0.95
    half_thick = size * 0.34
    ccx = cx + r_spine * math.cos(open_angle)      # centre of curvature, concave side
    ccy = cy + r_spine * math.sin(open_angle)
    mid = open_angle + math.pi                     # arc-middle direction from the centre
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
    ht = half_thick * (taper ** 0.6)               # thickness tapers to 0 at the cusps
    band = np.abs(rad - r_spine) - ht
    over = np.maximum(dth - half_span, 0.0) * r_spine
    sdf = np.where(dth < half_span, band, np.sqrt(over * over + (rad - r_spine) ** 2))
    field = _sdf_field(sdf)
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
    """Large disc just outside an edge; its near arc scoops a shallow concave curve
    so the trigon reads as an elegant three-point form, not a crude triangle."""
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


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
CUR_MX = 140.0
STREAMLINES = [
    {"y": H * 0.260, "amp": 64.0,  "freq": 1.10, "ph": 0.40},
    {"y": H * 0.445, "amp": 108.0, "freq": 0.85, "ph": 2.50},
    {"y": H * 0.600, "amp": 54.0,  "freq": 1.40, "ph": 4.20},
    {"y": H * 0.775, "amp": 88.0,  "freq": 1.00, "ph": 1.20},
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


WF_MY = 100.0
WF_LANES = [
    {"x": W * 0.310, "sway": 42.0, "ph": 0.0},
    {"x": W * 0.520, "sway": 30.0, "ph": 2.1},
    {"x": W * 0.700, "sway": 48.0, "ph": 4.0},
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


# --------------------------------------------------------------------------
# phrase rendering
# --------------------------------------------------------------------------
def render_phrase_on_path(canvas, path_fn, tan_fn, u_head, q, gap, scale=1.0):
    """Draw one circle->crescent->crescent->trigon phrase as a rigid travelling
    train, plus a short curved motion-trail wake behind each glyph. Glyphs are only
    drawn while strictly on the path (u in [0, 1])."""
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
        # motion-trail wake: soft blobs receding along the path behind the glyph
        wake_r = size * scale * 0.42
        for j in range(1, TRAIL_N + 1):
            ut = u - j * TRAIL_GAP
            if ut < 0.0:
                break
            bx, by = path_fn(ut)
            bfade = fade * 0.45 * (TRAIL_FALL ** j) * float(smoothstep(0.0, 0.06, ut))
            draw_blob(canvas, bx, by, wake_r * (1.0 - 0.13 * j), col, inten * bfade)
        # the glyph itself
        if kind == "circle":
            draw_circle(canvas, x, y, size * scale, col, inten * fade)
        elif kind == "crescent":
            # concave cups back toward the origin; convex bulge leads (bow-wave)
            draw_crescent(canvas, x, y, size * scale, ang + math.pi, col, inten * fade)
        else:
            draw_trigon(canvas, x, y, size * scale, ang, col, inten * fade)


def frame_current(canvas, f, n):
    """Sparse common-fate streamlines, each carrying a phrase bundle -- a current
    field that breathes, no wallpaper density."""
    gap = 0.086
    span = 1.0 + 6.0 * gap
    assignments = ((0, 0.12), (1, 0.00), (1, 0.50), (2, 0.33), (3, 0.70))
    for idx, off in assignments:
        s = STREAMLINES[idx]
        pf = lambda t, ss=s: stream_path(t, ss)
        tf = lambda t, ss=s: stream_tan(t, ss)
        q = (f / n + off) % 1.0
        u_head = -3.0 * gap + q * span
        render_phrase_on_path(canvas, pf, tf, u_head, q, gap)


def frame_waterfall(canvas, f, n):
    """Phrases descend three vertical lanes, accelerating under gravity; glyphs in
    a lane fall as one common-fate group with trailing water-streak wakes."""
    gap = 0.150
    span = 1.0 + 6.0 * gap
    bases = (0.00, 0.17, 0.34)
    for lane, base in zip(WF_LANES, bases):
        pf = lambda t, ln=lane: wf_path(t, ln)
        tf = lambda t, ln=lane: wf_tan(t, ln)
        for off in (base, base + 0.5):
            q = (f / n + off) % 1.0
            u_head = -3.0 * gap + (q ** 1.8) * span     # q**1.8 = gravitational acceleration
            render_phrase_on_path(canvas, pf, tf, u_head, q, gap)


FRAME_FNS = {
    "current_streamline_field_v002": frame_current,
    "waterfall_vertical_phrase_v002": frame_waterfall,
}


# --------------------------------------------------------------------------
# faint flow-channel guide layers
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
    if scene == "current_streamline_field_v002":
        for s in STREAMLINES:
            _stamp_ribbon(layer, lambda t, ss=s: stream_path(t, ss), 340, 27.0, 0.072)
    elif scene == "waterfall_vertical_phrase_v002":
        for lane in WF_LANES:
            _stamp_ribbon(layer, lambda t, ln=lane: wf_path(t, ln), 320, 31.0, 0.078)
    return layer


# --------------------------------------------------------------------------
# tone map + encode
# --------------------------------------------------------------------------
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


def render_scene(scene, outdir, n_frames):
    """Render one black-screen layer scene to MP4; return the midpoint frame."""
    frame_fn = FRAME_FNS[scene]
    guide = build_guide(scene)
    mid_idx = n_frames // 2
    out_mp4 = outdir / f"{scene}.mp4"
    proc = _encoder(out_mp4)

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
        raise RuntimeError(f"ffmpeg failed for {scene}:\n{proc.stderr.read().decode('utf-8','replace')}")

    Image.fromarray(mid_frame).save(outdir / "midpoint_stills" / f"{scene}_mid.png")
    print(f"  {scene}: {n_frames} frames + still in {time.time() - t0:4.1f}s")
    return mid_frame


# --------------------------------------------------------------------------
# composite previews (layer additively blended over footage)
# --------------------------------------------------------------------------
def make_composite(layer_mp4, footage, start, opacity, footage_dim, out_mp4, n_frames):
    """Blend a black-screen layer additively over real footage. Footage is cropped
    to drop the burned-in source timecode strip, scaled to 1080p, set to 24fps,
    slightly dimmed, then the layer is added at `opacity`. Returns the midpoint
    still as a numpy array, or None on failure."""
    dur = n_frames / FPS
    crop = "crop=1770:996:75:0,scale=1920:1080"
    fc = (
        f"[0:v]{crop},fps=24,trim=duration={dur},setpts=PTS-STARTPTS,"
        f"eq=brightness={footage_dim}:saturation=1.05,format=gbrp[bg];"
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
    still = out_mp4.with_suffix("")
    still_png = still.parent / "midpoint_stills" / f"{still.name}_mid.png"
    grab = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(dur / 2.0),
         "-i", str(out_mp4), "-frames:v", "1", "-update", "1", str(still_png)],
        capture_output=True, text=True)
    if grab.returncode != 0:
        return None
    print(f"  {out_mp4.name}: composite over {Path(footage).name}")
    return np.asarray(Image.open(still_png).convert("RGB"))


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
        "width": int(st["width"]), "height": int(st["height"]),
        "codec": st["codec_name"], "fps": float(num) / float(den),
        "fps_raw": st["r_frame_rate"], "frames": int(st["nb_read_frames"]),
        "duration": float(fmt["duration"]), "size_kb": path.stat().st_size // 1024,
    }


def nonblank_check(frame):
    luma = 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]
    return {"max_luma": int(luma.max()),
            "nonblack_px": int(np.count_nonzero(np.any(frame > 8, axis=2)))}


# --------------------------------------------------------------------------
# contact sheet
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------
def write_readme(outdir, layers, composites, sheet_size, n_frames, footage_note, opacity):
    pct = int(round(opacity * 100))
    L = []
    a = L.append
    a("# Water Flow Phrase Grammar v002 - 2026-05-20")
    a("")
    a("INTERNAL ONLY until Austin reviews. Layer-only black-background additive clips,")
    a("plus low-opacity composite previews over real footage. No SD / LoRA / style")
    a("transfer, no topology / cymatics / seed-of-life construction geometry, no fish or")
    a("animal figures, no prompt scenes, no randomness. Not Austin-approved and not a")
    a("public cultural-grammar claim.")
    a("")
    a("## What This Packet Is")
    a("")
    a("A focused refinement of the two strongest v001 water-flow clips:")
    a("`current_streamline_field` and `waterfall_vertical_phrase`. The v001 pond and")
    a("river scenes are intentionally dropped. The phrase grammar is unchanged:")
    a("")
    a("    circle (origin)  ->  crescent  ->  crescent  ->  trigon (attenuation)")
    a("")
    a("The black-screen layer-only loops are the primary deliverable. The composite")
    a("previews show how each layer reads additively over Moonfish footage in Resolume;")
    a("they are review aids, not the deliverable.")
    a("")
    a("## Refinements Over v001")
    a("")
    a("- **Scale:** primitives enlarged for projection readability.")
    a("- **Crescent shape:** reworked from a two-disc lune to a tapered circular-arc")
    a("  blade -- a clean ~110-degree bold blade that, unlike a deep lune, never rings")
    a("  an enclosed dark core at the larger v002 scale.")
    a("- **Glow:** a crisp core with a clean tight halo and just a whisper of wide")
    a("  bloom -- bold and projection-readable rather than hazy.")
    a("- **Motion:** every glyph carries a short curved wake of soft blobs receding")
    a("  along its path, so travelling phrases read as smooth, connected flow.")
    a("- **Spacing:** glyph spacing retuned per scene to pixel size; gentler fades.")
    a("- **Scope:** two scenes only, so each gets a full quality pass.")
    a("")
    a("## Primary Clips (black-screen, layer-only)")
    a("")
    for c in layers:
        pr, nb = c["ffprobe"], c["nonblank"]
        a(f"### {c['scene']}.mp4")
        a("")
        a(f"- What it is: {c['desc']}")
        a("- Layer role: Water layer. Resolume Screen/Additive blend over footage or black.")
        a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
          f"duration {pr['duration']:.3f}s, frames {pr['frames']}, codec {pr['codec']}, "
          f"{pr['size_kb']} KB")
        a(f"- Nonblank check: midpoint max luma {nb['max_luma']}, "
          f"nonblack pixels {nb['nonblack_px']}")
        a("")
    a("## Composite Previews (layer over footage)")
    a("")
    a("Low-opacity additive composites, for review only. Footage is cropped to drop the")
    a("burned-in source timecode, scaled to 1080p, set to 24fps, slightly dimmed, then")
    a(f"the layer is added at ~{pct}% opacity. Each is a 144-frame (~6s) preview; only")
    a("the layer loops seamlessly.")
    a("")
    if footage_note:
        a(f"> Footage note: {footage_note}")
        a("")
    if composites:
        for c in composites:
            pr = c["ffprobe"]
            a(f"### {c['name']}.mp4")
            a("")
            a(f"- {c['desc']}")
            a(f"- ffprobe: {pr['width']}x{pr['height']}, fps {pr['fps_raw']}, "
              f"duration {pr['duration']:.3f}s, frames {pr['frames']}, codec {pr['codec']}, "
              f"{pr['size_kb']} KB")
            a("")
    else:
        a("(No composites in this run -- footage not found; black-screen clips render"
          " regardless.)")
        a("")
    a("## Review Stills")
    a("")
    a("- Midpoint stills: `midpoint_stills/` (1920x1080 PNG per clip)")
    a(f"- Contact sheet: `contact_sheet_v002.png` ({sheet_size[0]}x{sheet_size[1]}) --"
      " top row layers, bottom row composites")
    a("")
    a("## Resolume Notes")
    a("")
    a("- Primary clips are RGB H.264 MP4 on pure black; use Screen/Additive blend, no alpha.")
    a(f"- Layer loops are seamless (frame {n_frames} == frame 0); set the clip to loop.")
    a("- Composite previews are pre-blended at low opacity purely to preview the look;")
    a("  in production, layer the black-screen clip over footage in Resolume directly.")
    a("")
    a("## Constraints Honored")
    a("")
    a("- No topology / cymatics / seed-of-life construction geometry.")
    a("- No fish or animal figures; no named, chief, or supernatural beings.")
    a("- No prompt scenes; no SD / LoRA / style-transfer.")
    a("- No random placement -- every phrase is an explicit deterministic parametric path.")
    a("- Outputs written only to this folder and `scripts/water_flow_phrase_grammar_v002.py`.")
    a("")
    a("## Open Questions For Austin")
    a("")
    a("1. Crescent orientation still cups *back toward the origin* (v001 Austin Q2 open).")
    a("2. Does the motion-trail wake help the flow read, or is it visual clutter?")
    a(f"3. Composite opacity: previews use ~{pct}% additive -- is that the right")
    a("   starting point over footage, or lighter?")
    a("")
    a("## Sources Read")
    a("")
    a("- Meetings/The Salish Sea Dreaming/2026-05-18 The Salish Sea Dreaming Meeting 2.md")
    a("- docs/space-center/pravin-internal-update-rd-lane-map-addendum-2026-05-20.md")
    a("- docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md")
    a("- docs/space-center/austin-visual-morphology-atlas-2026-05-20.md")
    a("- track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v001_2026-05-20/")
    a("")
    a("## Regenerate")
    a("")
    a("    python3 scripts/water_flow_phrase_grammar_v002.py")
    a("")
    (outdir / "README.md").write_text("\n".join(L), encoding="utf-8")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
LAYER_DESC = {
    "current_streamline_field_v002":
        "Four sparse common-fate streamlines carry phrase bundles across the field, "
        "each glyph trailing a short curved wake. Density follows the streamlines.",
    "waterfall_vertical_phrase_v002":
        "Phrases descend three vertical lanes, accelerating under a gravity ease; "
        "trailing wakes read as falling-water streaks. Circle origins sit at the lip.",
}


def main():
    repo = Path(__file__).resolve().parents[1]
    default_out = (repo / "track2-deterministic" / "morph_outputs_INTERNAL"
                   / "water_flow_phrase_grammar_v002_2026-05-20")
    moon = repo / "media" / "collaborators" / "moonfish-video" / "underwater"
    ap = argparse.ArgumentParser(description="Water-flow phrase grammar v002 renderer.")
    ap.add_argument("--outdir", default=str(default_out))
    ap.add_argument("--frames", type=int, default=N_FRAMES)
    ap.add_argument("--kelp", default=str(moon / "P1111785.mp4"),
                    help="kelp-forest footage for the waterfall composite")
    ap.add_argument("--water", default=str(moon / "P1099653.mp4"),
                    help="open-water footage for the current composite")
    ap.add_argument("--kelp-start", type=float, default=4.0)
    ap.add_argument("--water-start", type=float, default=28.0)
    ap.add_argument("--opacity", type=float, default=0.55)
    ap.add_argument("--no-composites", action="store_true")
    args = ap.parse_args()

    n_frames = max(2, args.frames)
    outdir = Path(args.outdir)
    (outdir / "midpoint_stills").mkdir(parents=True, exist_ok=True)

    print(f"water_flow_phrase_grammar_v002 -> {outdir}")
    print(f"  {W}x{H}  {FPS}fps  {n_frames} frames  ({n_frames / FPS:.3f}s)\n")

    # ---- primary black-screen layer clips ----
    layers, layer_still = [], {}
    for scene in SCENES:
        mid = render_scene(scene, outdir, n_frames)
        layer_still[scene] = mid
        layers.append({"scene": scene, "desc": LAYER_DESC[scene],
                        "ffprobe": ffprobe_check(outdir / f"{scene}.mp4"),
                        "nonblank": nonblank_check(mid)})

    # ---- composite previews ----
    composites, comp_still, footage_note = [], {}, ""
    kelp, water = Path(args.kelp), Path(args.water)
    jobs = [
        ("current_streamline_field_v002", "moonfish-water", water, args.water_start,
         -0.10, "current_streamline_field over Moonfish open-water footage (P1099653)."),
        ("waterfall_vertical_phrase_v002", "kelp-forest", kelp, args.kelp_start,
         -0.15, "waterfall_vertical_phrase over Moonfish kelp-forest footage (P1111785)."),
    ]
    if not args.no_composites:
        footage_note = (
            "the hero subclip named H6_kelp_forest_floor(_4k).mp4 is mislabeled -- it is "
            "a dense salmon-school clip (burned-in source P1099653.MOV), not kelp. This "
            "packet substitutes P1111785.mp4, a genuine kelp-forest clip from the same "
            "Moonfish underwater set, for the kelp composite.")
        for scene, tag, footage, start, dim, desc in jobs:
            if not footage.exists():
                print(f"  composite skipped: footage not found -- {footage}")
                continue
            name = f"{scene}__over_{tag}"
            still = make_composite(outdir / f"{scene}.mp4", footage, start,
                                   args.opacity, dim, outdir / f"{name}.mp4", n_frames)
            if still is not None:
                comp_still[scene] = still
                composites.append({"name": name, "desc": desc,
                                    "ffprobe": ffprobe_check(outdir / f"{name}.mp4")})

    # ---- contact sheet (top row layers, bottom row composites) ----
    pct = int(round(args.opacity * 100))
    panels = [
        ("current_streamline_field_v002", "layer-only (black screen)",
         layer_still.get("current_streamline_field_v002")),
        ("waterfall_vertical_phrase_v002", "layer-only (black screen)",
         layer_still.get("waterfall_vertical_phrase_v002")),
        ("current over Moonfish water", f"composite preview ~{pct}% additive",
         comp_still.get("current_streamline_field_v002")),
        ("waterfall over kelp forest", f"composite preview ~{pct}% additive",
         comp_still.get("waterfall_vertical_phrase_v002")),
    ]
    sheet_size = build_contact_sheet(panels, outdir / "contact_sheet_v002.png")
    print(f"  contact sheet: {sheet_size[0]}x{sheet_size[1]}")
    write_readme(outdir, layers, composites, sheet_size, n_frames, footage_note, args.opacity)
    print("  README.md written\n")

    # ---- verification ----
    print("VERIFICATION SUMMARY")
    ok = True
    allclips = [(c["scene"], c["ffprobe"], c["nonblank"]) for c in layers]
    allclips += [(c["name"], c["ffprobe"], None) for c in composites]
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
    print(f"\n{'ALL CHECKS PASSED' if ok else 'CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
