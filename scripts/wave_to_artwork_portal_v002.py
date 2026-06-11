#!/usr/bin/env python3
"""
Wave to artwork portal v002.

Internal mathematical/visual alignment study for Salish Sea Dreaming. v002
fixes the v001 mismatch by replacing the sixfold portal geometry with an
octagonal eight-source gather aligned to Nature_Cosmic_Sun.svg's eight radial
ray/trigon rhythm. Austin's authored SVG is used as a whole source artwork.

This script does not train, diffuse, imitate, synthesize, decompose, or reuse
Austin's shapes as generic primitives. The SVG is revealed as a whole source
through a circular/radial presentation aperture, with only uniform scale,
position, opacity, and masking for the transition.

Status: INTERNAL ONLY. Not Austin-approved for public use. Not public-use
guidance. Not a cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import cymatic_field_topology_v007 as base


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "wave_to_artwork_portal_v002_2026-05-21"
)
STILLS_DIR = OUT_DIR / "stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
SOURCE_DIR = OUT_DIR / "source_assets"

SOURCE_SVG = ROOT / "track2-deterministic" / "source-vectors" / "Nature_Cosmic_Sun.svg"
APPROVED_COPY = ROOT / "austin-v2-ingest" / "approved" / "Nature_Cosmic_Sun.svg"
DRIVE_MIRROR = ROOT / "austin-reference" / "google-drive-ai-training-2026-05-15" / "Nature_Cosmic_Sun.svg"
PROVENANCE_CSV = ROOT / "austin-v2-ingest" / "provenance" / "manifest.csv"
TRIAGE_JSON = ROOT / "austin-v2-ingest" / "inbox" / "_triage.json"

W = base.W
H = base.H
FW = base.FW
FH = base.FH
FPS = base.FPS
DURATION_SECONDS = 12.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

BEFORE_TIME_SECONDS = 2.4
GATHER_TIME_SECONDS = 4.4
PORTAL_TIME_SECONDS = 5.85
PEAK_TIME_SECONDS = 7.0
AFTER_TIME_SECONDS = 10.7
PEAK_FRAME = int(PEAK_TIME_SECONDS * FPS)

EXPECTED_SHA256 = "197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1"

DEEP_GROUND = (0, 5, 7)
DARK_WATER = (2, 24, 29)
TEAL = (52, 151, 154)
MUTED_TEAL = (69, 119, 120)
WARM_CREAM = (235, 223, 184)
SOFT_GOLD = (246, 195, 91)
PORTAL_ORANGE = (218, 96, 39)
PORTAL_GLOW = (255, 215, 130)
INK = (0, 7, 9)
LABEL = (226, 234, 230)

ARTWORK_VIEWBOX_SIZE = 108.0
ARTWORK_CENTER_VIEWBOX = (53.92, 53.86)
ARTWORK_OUTER_RING_RADIUS_VIEWBOX = 48.26
ARTWORK_OUTER_RADIUS_PX = 392.0
ARTWORK_HIGH_RES_FACTOR = 4

SOURCE_RING_RADIUS = 292.0
SOURCE_WAVELENGTH = 246.0
SOURCE_FREQUENCY = 0.112
SOURCE_DECAY = 980.0
DRIFT_AMPLITUDE = 155.0
FIELD_THRESHOLD = 0.056
NODE_EPSILON = 0.044
BLUR_SIGMA = 0.58
FIELD_GAMMA = 0.86
FIELD_BOUNDARY_RADIUS = 520.0


@dataclass(frozen=True)
class OctagonalTargetSource:
    source_id: str
    angle_rad: float
    x: float
    y: float
    amplitude: float
    drift_scale: float
    orbit_phase: float
    orbit_speed: float
    phase_perturb: float


@dataclass(frozen=True)
class OctagonalTarget:
    key: str
    symmetry_type: str
    source_count: int
    center_px: tuple[float, float]
    source_ring_radius_px: float
    wavelength_px: float
    frequency: float
    decay: float
    drift_amplitude_px: float
    sources: tuple[OctagonalTargetSource, ...]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_octagonal_target() -> OctagonalTarget:
    cx, cy = W * 0.5, H * 0.5
    sources: list[OctagonalTargetSource] = []
    # Axis 0 points up, then proceeds clockwise in 45 degree steps. This
    # matches the visible eight-ray rhythm of Nature_Cosmic_Sun.svg.
    for idx in range(8):
        angle = -math.pi * 0.5 + TAU * idx / 8.0
        sources.append(
            OctagonalTargetSource(
                source_id=f"octagonal_ray_source_{idx:02d}",
                angle_rad=angle,
                x=cx + SOURCE_RING_RADIUS * math.cos(angle),
                y=cy + SOURCE_RING_RADIUS * math.sin(angle),
                amplitude=1.02,
                drift_scale=0.82 + 0.18 * ((idx % 2) * 0.55 + 0.45),
                orbit_phase=(0.115 * idx + 0.07) % 1.0,
                orbit_speed=0.16 + 0.018 * idx,
                phase_perturb=(0.137 * idx + 0.21) % 1.0,
            )
        )
    return OctagonalTarget(
        key="octagonal_cosmic_sun_portal",
        symmetry_type="C8/octagonal",
        source_count=8,
        center_px=(cx, cy),
        source_ring_radius_px=SOURCE_RING_RADIUS,
        wavelength_px=SOURCE_WAVELENGTH,
        frequency=SOURCE_FREQUENCY,
        decay=SOURCE_DECAY,
        drift_amplitude_px=DRIFT_AMPLITUDE,
        sources=tuple(sources),
    )


TARGET = make_octagonal_target()


def coherence_at_time(time_seconds: float) -> float:
    """0-3 drift, 3-5 gather, 5-8 lock, 8-10 release, 10-12 drift."""
    t = time_seconds % DURATION_SECONDS
    if t < 3.0:
        return 0.0
    if t < 5.0:
        return smoothstep01((t - 3.0) / 2.0)
    if t < 8.0:
        return 1.0
    if t < 10.0:
        return 1.0 - smoothstep01((t - 8.0) / 2.0)
    return 0.0


def source_position(source: OctagonalTargetSource, time_seconds: float, coherence: float) -> tuple[float, float]:
    radius = TARGET.drift_amplitude_px * source.drift_scale * (1.0 - coherence * coherence)
    angle = TAU * (source.orbit_phase + source.orbit_speed * time_seconds / DURATION_SECONDS)
    wobble = 0.24 * math.sin(TAU * (0.057 * time_seconds + source.phase_perturb))
    return (
        source.x + radius * math.cos(angle + wobble),
        source.y + radius * math.sin(angle + wobble),
    )


def target_sources_at(time_seconds: float, coherence: float | None = None) -> list[base.WaveSource]:
    c = coherence_at_time(time_seconds) if coherence is None else coherence
    locked_phase = TAU * TARGET.frequency * PEAK_TIME_SECONDS - TAU * TARGET.source_ring_radius_px / TARGET.wavelength_px
    wave_sources: list[base.WaveSource] = []
    for source in TARGET.sources:
        x, y = source_position(source, time_seconds, c)
        perturb = (1.0 - c) * 0.70 * math.sin(TAU * (0.043 * time_seconds + source.phase_perturb))
        wave_sources.append(
            base.WaveSource(
                source_id=source.source_id,
                x=x,
                y=y,
                amplitude=source.amplitude,
                wavelength=TARGET.wavelength_px,
                frequency=TARGET.frequency,
                phase=locked_phase + perturb,
                decay=TARGET.decay,
                velocity=(0.0, 0.0),
                birth_time=0.0,
                lifetime=999.0,
                symmetry_order=8,
                mode="continuous",
            )
        )
    return wave_sources


def verify_source_provenance() -> dict[str, object]:
    issues: list[str] = []
    for required in (SOURCE_SVG, APPROVED_COPY, PROVENANCE_CSV, TRIAGE_JSON):
        if not required.exists():
            issues.append(f"missing required provenance file: {required}")
    if issues:
        return {"ok": False, "issues": issues}

    source_sha = sha256(SOURCE_SVG)
    approved_sha = sha256(APPROVED_COPY)
    drive_sha = sha256(DRIVE_MIRROR) if DRIVE_MIRROR.exists() else None
    if source_sha != EXPECTED_SHA256:
        issues.append(f"source SVG SHA mismatch: {source_sha}")
    if approved_sha != source_sha:
        issues.append("approved-ingest copy does not match source-vector SVG")
    if drive_sha is not None and drive_sha != source_sha:
        issues.append("fresh Drive mirror does not match source-vector SVG")

    provenance_rows = list(csv.DictReader(PROVENANCE_CSV.open(newline="", encoding="utf-8")))
    provenance_row = next((row for row in provenance_rows if row.get("filename") == "Nature_Cosmic_Sun.svg"), None)
    if provenance_row is None:
        issues.append("Nature_Cosmic_Sun.svg not found in provenance manifest")
    elif provenance_row.get("sha256") != source_sha:
        issues.append("provenance manifest SHA does not match source SVG")

    triage = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    triage_row = next((row for row in triage if row.get("filename") == "Nature_Cosmic_Sun.svg"), None)
    if triage_row is None:
        issues.append("Nature_Cosmic_Sun.svg not found in triage metadata")
    elif triage_row.get("recommendation") != "approve":
        issues.append(f"triage recommendation is not approve: {triage_row.get('recommendation')}")

    return {
        "ok": not issues,
        "issues": issues,
        "source_svg": str(SOURCE_SVG),
        "approved_copy": str(APPROVED_COPY),
        "drive_mirror": str(DRIVE_MIRROR) if DRIVE_MIRROR.exists() else None,
        "sha256": source_sha,
        "expected_sha256": EXPECTED_SHA256,
        "provenance_row": provenance_row,
        "triage_row": triage_row,
        "public_approval_status": "pending; internal-only use only, public use blocked until Austin review",
    }


def write_source_provenance_note(provenance: dict[str, object]) -> Path:
    row = provenance.get("provenance_row")
    triage = provenance.get("triage_row")
    consent = row.get("austin_consent", "unknown") if isinstance(row, dict) else "unknown"
    recommendation = triage.get("recommendation", "unknown") if isinstance(triage, dict) else "unknown"
    lines = [
        "# Source Provenance Note",
        "",
        "Source artwork: `Nature_Cosmic_Sun.svg`.",
        "",
        "This packet uses Austin's authored SVG as a whole source artwork. It does not train, diffuse, imitate, synthesize, decompose, or reuse individual shapes as generic primitives.",
        "",
        "## Local Source Paths",
        "",
        f"- Source vector: `{SOURCE_SVG}`",
        f"- Approved-ingest copy: `{APPROVED_COPY}`",
        f"- Fresh Drive mirror: `{DRIVE_MIRROR if DRIVE_MIRROR.exists() else 'not present'}`",
        "",
        "## Hash",
        "",
        f"- SHA256: `{provenance.get('sha256', 'unknown')}`",
        "",
        "## Ingest Records",
        "",
        f"- Provenance CSV: `{PROVENANCE_CSV}`",
        f"- Triage JSON: `{TRIAGE_JSON}`",
        f"- Provenance status: `{consent}`",
        f"- Triage recommendation: `{recommendation}`",
        "",
        "## Boundary",
        "",
        "Internal-only wave-to-authored-artwork portal study pending Austin review. Public/projector/social use remains blocked until Austin reviews and approves the specific output.",
    ]
    path = OUT_DIR / "SOURCE_PROVENANCE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def rasterize_source_svg(display_size_px: int) -> tuple[Path, Path]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied_svg = SOURCE_DIR / "Nature_Cosmic_Sun.svg"
    if not copied_svg.exists() or sha256(copied_svg) != sha256(SOURCE_SVG):
        shutil.copy2(SOURCE_SVG, copied_svg)

    high_size = display_size_px * ARTWORK_HIGH_RES_FACTOR
    high_path = SOURCE_DIR / "Nature_Cosmic_Sun_author_source_highres_rgba.png"
    display_path = SOURCE_DIR / "Nature_Cosmic_Sun_author_source_display_rgba.png"
    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("ImageMagick `magick` is required to rasterize the source SVG.")
    subprocess.run(
        [
            magick,
            "-background",
            "none",
            "-density",
            "768",
            str(SOURCE_SVG),
            "-resize",
            f"{high_size}x{high_size}",
            f"PNG32:{high_path}",
        ],
        check=True,
    )
    rgba_high = cv2.imread(str(high_path), cv2.IMREAD_UNCHANGED)
    if rgba_high is None:
        raise RuntimeError(f"could not read high-resolution source raster: {high_path}")
    rgba_display = cv2.resize(rgba_high, (display_size_px, display_size_px), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(display_path), rgba_display)
    return high_path, display_path


def load_artwork_layer() -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    art_scale = ARTWORK_OUTER_RADIUS_PX / ARTWORK_OUTER_RING_RADIUS_VIEWBOX
    display_size = round(ARTWORK_VIEWBOX_SIZE * art_scale)
    high_path, display_path = rasterize_source_svg(display_size)
    rgba = cv2.imread(str(display_path), cv2.IMREAD_UNCHANGED)
    if rgba is None:
        raise RuntimeError(f"could not read display source raster: {display_path}")
    if rgba.shape[2] == 3:
        bgr = rgba
        alpha = np.full(rgba.shape[:2], 255, dtype=np.uint8)
    else:
        bgr = rgba[:, :, :3]
        alpha = rgba[:, :, 3]

    center_x, center_y = TARGET.center_px
    art_center_x = ARTWORK_CENTER_VIEWBOX[0] / ARTWORK_VIEWBOX_SIZE * display_size
    art_center_y = ARTWORK_CENTER_VIEWBOX[1] / ARTWORK_VIEWBOX_SIZE * display_size
    x0 = round(center_x - art_center_x)
    y0 = round(center_y - art_center_y)
    x1 = x0 + bgr.shape[1]
    y1 = y0 + bgr.shape[0]

    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    canvas_alpha = np.zeros((H, W), dtype=np.uint8)
    sx0 = max(0, -x0)
    sy0 = max(0, -y0)
    dx0 = max(0, x0)
    dy0 = max(0, y0)
    dx1 = min(W, x1)
    dy1 = min(H, y1)
    sx1 = sx0 + (dx1 - dx0)
    sy1 = sy0 + (dy1 - dy0)
    if dx1 <= dx0 or dy1 <= dy0:
        raise RuntimeError("artwork layer does not intersect the canvas")
    canvas[dy0:dy1, dx0:dx1] = bgr[sy0:sy1, sx0:sx1]
    canvas_alpha[dy0:dy1, dx0:dx1] = alpha[sy0:sy1, sx0:sx1]

    info = {
        "source_svg": str(SOURCE_SVG),
        "high_res_raster": str(high_path),
        "display_raster": str(display_path),
        "high_res_factor": ARTWORK_HIGH_RES_FACTOR,
        "art_scale_px_per_svg_unit": art_scale,
        "art_raster_size_px": [int(bgr.shape[1]), int(bgr.shape[0])],
        "art_bbox_px": [int(dx0), int(dy0), int(dx1), int(dy1)],
        "art_center_px": [round(center_x, 3), round(center_y, 3)],
        "artwork_outer_radius_px": ARTWORK_OUTER_RADIUS_PX,
        "alignment": {
            "svg_center": list(ARTWORK_CENTER_VIEWBOX),
            "canvas_center": [round(center_x, 3), round(center_y, 3)],
            "svg_outer_ring_radius": ARTWORK_OUTER_RING_RADIUS_VIEWBOX,
            "svg_outer_ring_radius_px": round(ARTWORK_OUTER_RING_RADIUS_VIEWBOX * art_scale, 3),
            "wave_source_ring_radius_px": TARGET.source_ring_radius_px,
            "octagonal_axis_count": 8,
        },
    }
    return canvas, canvas_alpha, info


def field_boundary_mask(radius: float = FIELD_BOUNDARY_RADIUS, soft_edge: float = 34.0) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = TARGET.center_px
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((radius + soft_edge - d) / max(1e-6, soft_edge), 0.0, 1.0)
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


FIELD_BOUNDARY_FULL = field_boundary_mask()
FIELD_BOUNDARY_SMALL = cv2.resize(FIELD_BOUNDARY_FULL, (FW, FH), interpolation=cv2.INTER_AREA)


def shape_field(field_norm: np.ndarray) -> np.ndarray:
    return (np.sign(field_norm) * (np.abs(field_norm) ** FIELD_GAMMA)).astype(np.float32)


def blend_mask(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float, *, glow: float = 0.0) -> None:
    if alpha <= 0.0:
        return
    mask_f = (mask.astype(np.float32) / 255.0) * alpha
    if float(mask_f.max()) <= 0.0:
        return
    out = frame.astype(np.float32)
    color = np.array(rgb_to_bgr(rgb), dtype=np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask, (0, 0), 6.0)
        out += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[:] = np.clip(out, 0, 255).astype(np.uint8)


def alpha_over(frame: np.ndarray, layer: np.ndarray, alpha_mask: np.ndarray, alpha: float) -> None:
    if alpha <= 0.0:
        return
    a = (alpha_mask.astype(np.float32) / 255.0) * alpha
    if float(a.max()) <= 0.0:
        return
    out = frame.astype(np.float32)
    lay = layer.astype(np.float32)
    out = out * (1.0 - a[..., None]) + lay * a[..., None]
    frame[:] = np.clip(out, 0, 255).astype(np.uint8)


def render_wave_layer(field_norm: np.ndarray, levels: dict[str, float]) -> np.ndarray:
    frame_small = np.zeros((FH, FW, 3), dtype=np.uint8)
    field_small = cv2.GaussianBlur(shape_field(field_norm), (0, 0), 0.36)
    inside = FIELD_BOUNDARY_SMALL > 4
    soft = FIELD_BOUNDARY_SMALL

    pos = np.where((field_small > FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    neg = np.where((field_small < -FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    node = np.where((np.abs(field_small) <= NODE_EPSILON) & inside, soft, 0).astype(np.uint8)
    node = cv2.morphologyEx(node, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    region = cv2.bitwise_or(pos, neg)
    edge = cv2.morphologyEx(region, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_edge = cv2.morphologyEx(node, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    blend_mask(frame_small, soft, DARK_WATER, 0.58 * levels["water"])
    blend_mask(frame_small, neg, TEAL, 0.68 * levels["negative"])
    blend_mask(frame_small, pos, WARM_CREAM, 0.58 * levels["positive"])
    blend_mask(frame_small, edge, INK, 0.28 * levels["line"])
    blend_mask(frame_small, node, INK, 0.64 * levels["line"])
    blend_mask(frame_small, node_edge, MUTED_TEAL, 0.18 * levels["line"])

    frame = cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)
    boundary_edge = cv2.morphologyEx(FIELD_BOUNDARY_FULL, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    blend_mask(frame, boundary_edge, MUTED_TEAL, 0.14 * levels["line"])
    return frame


def circle_mask(cx: float, cy: float, radius: float, *, soft_edge: float = 0.0) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    if soft_edge <= 0.0:
        return np.where(d <= radius, 255, 0).astype(np.uint8)
    alpha = np.clip((radius + soft_edge - d) / soft_edge, 0.0, 1.0)
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


def ray_aperture_mask() -> np.ndarray:
    cx, cy = TARGET.center_px
    mask = np.zeros((H, W), dtype=np.uint8)
    inner_radius = ARTWORK_OUTER_RADIUS_PX * 0.30
    shoulder_radius = ARTWORK_OUTER_RADIUS_PX * 0.55
    outer_radius = ARTWORK_OUTER_RADIUS_PX * 0.98
    inner_half = math.radians(5.5)
    shoulder_half = math.radians(10.0)
    outer_half = math.radians(5.0)
    for source in TARGET.sources:
        a = source.angle_rad
        pts = [
            (
                round(cx + inner_radius * math.cos(a)),
                round(cy + inner_radius * math.sin(a)),
            ),
            (
                round(cx + shoulder_radius * math.cos(a + shoulder_half)),
                round(cy + shoulder_radius * math.sin(a + shoulder_half)),
            ),
            (
                round(cx + outer_radius * math.cos(a + outer_half)),
                round(cy + outer_radius * math.sin(a + outer_half)),
            ),
            (
                round(cx + outer_radius * math.cos(a - outer_half)),
                round(cy + outer_radius * math.sin(a - outer_half)),
            ),
            (
                round(cx + shoulder_radius * math.cos(a - shoulder_half)),
                round(cy + shoulder_radius * math.sin(a - shoulder_half)),
            ),
            (
                round(cx + inner_radius * math.cos(a - inner_half)),
                round(cy + inner_radius * math.sin(a - inner_half)),
            ),
        ]
        cv2.fillPoly(mask, [np.array(pts, dtype=np.int32)], 255, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(mask, (0, 0), 3.2)


FULL_APERTURE_MASK = circle_mask(*TARGET.center_px, ARTWORK_OUTER_RADIUS_PX, soft_edge=32.0)
CENTRAL_APERTURE_MASK = circle_mask(*TARGET.center_px, ARTWORK_OUTER_RADIUS_PX * 0.39, soft_edge=18.0)
RAY_APERTURE_MASK = ray_aperture_mask()


def time_levels(time_seconds: float, coherence: float) -> dict[str, float]:
    portal_out = 1.0 - smoothstep01((time_seconds - 8.0) / 2.0)
    central = smoothstep01((time_seconds - 5.00) / 0.48) * portal_out
    rays = smoothstep01((time_seconds - 5.32) / 0.80) * portal_out
    full = smoothstep01((time_seconds - 6.04) / 0.92) * portal_out
    artwork = smoothstep01((time_seconds - 5.18) / 1.08) * portal_out
    gather = smoothstep01((time_seconds - 3.0) / 2.0)
    release = smoothstep01((time_seconds - 8.0) / 2.0)
    portal = max(central, rays, full) * portal_out
    return {
        "coherence": coherence,
        "gather": gather,
        "release": release,
        "central_aperture": clamp01(central),
        "ray_aperture": clamp01(rays),
        "full_aperture": clamp01(full),
        "portal": clamp01(portal),
        "artwork": clamp01(artwork),
        "water": clamp01(0.96 - 0.30 * artwork),
        "positive": clamp01(0.94 * (1.0 - 0.91 * artwork)),
        "negative": clamp01(0.82 * (1.0 - 0.58 * artwork)),
        "line": clamp01(0.72 * (1.0 - 0.34 * artwork) + 0.10 * coherence),
    }


def portal_aperture(levels: dict[str, float], artwork_alpha: np.ndarray) -> dict[str, np.ndarray]:
    central = (CENTRAL_APERTURE_MASK.astype(np.float32) * levels["central_aperture"]).astype(np.uint8)
    rays = (RAY_APERTURE_MASK.astype(np.float32) * levels["ray_aperture"]).astype(np.uint8)
    full = (FULL_APERTURE_MASK.astype(np.float32) * levels["full_aperture"]).astype(np.uint8)
    aperture = np.maximum(np.maximum(central, rays), full)
    aperture = np.minimum(aperture, artwork_alpha)
    edge_src = np.where(aperture > 14, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(edge_src, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    edge = cv2.GaussianBlur(edge, (0, 0), 5.4)
    return {
        "central": central,
        "rays": rays,
        "full": full,
        "aperture": aperture,
        "edge": edge,
    }


def draw_octagonal_axes(frame: np.ndarray, *, alpha: float, labels: bool = False) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    cx, cy = TARGET.center_px
    for idx, source in enumerate(TARGET.sources):
        a = source.angle_rad
        p0 = (round(cx + 36.0 * math.cos(a)), round(cy + 36.0 * math.sin(a)))
        p1 = (
            round(cx + (ARTWORK_OUTER_RADIUS_PX + 46.0) * math.cos(a)),
            round(cy + (ARTWORK_OUTER_RADIUS_PX + 46.0) * math.sin(a)),
        )
        cv2.line(overlay, p0, p1, rgb_to_bgr(PORTAL_GLOW), 1, lineType=cv2.LINE_AA)
        if labels:
            base.draw_text(overlay, f"axis {idx}", (p1[0] + 6, p1[1]), LABEL, scale=0.28)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_source_positions(frame: np.ndarray, sources: list[base.WaveSource], *, alpha: float, labels: bool) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    for source in sources:
        p = (round(source.x), round(source.y))
        cv2.circle(overlay, p, 8, rgb_to_bgr(SOFT_GOLD), 1, lineType=cv2.LINE_AA)
        cv2.circle(overlay, p, 2, rgb_to_bgr(SOFT_GOLD), -1, lineType=cv2.LINE_AA)
        if labels:
            base.draw_text(overlay, source.source_id.replace("octagonal_ray_source_", "src "), (p[0] + 10, p[1] - 8), LABEL, scale=0.28)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def render_frame(
    time_seconds: float,
    artwork_bgr: np.ndarray,
    artwork_alpha: np.ndarray,
    *,
    force_coherence: float | None = None,
    labels: bool = False,
) -> tuple[np.ndarray, dict[str, object]]:
    coherence = coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = target_sources_at(time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=BLUR_SIGMA)
    levels = time_levels(time_seconds, coherence)
    masks = portal_aperture(levels, artwork_alpha)

    frame = render_wave_layer(field, levels)

    # During the gather, the scaffold is only a faint alignment signal. During
    # the portal it becomes a glow at the aperture boundary instead of an
    # overlaid construction diagram.
    draw_octagonal_axes(frame, alpha=0.08 * smoothstep01((time_seconds - 3.0) / 2.0) * (1.0 - levels["artwork"]))
    blend_mask(frame, masks["edge"], PORTAL_GLOW, 0.20 * levels["portal"], glow=0.025 * levels["portal"])
    blend_mask(frame, masks["edge"], PORTAL_ORANGE, 0.10 * levels["ray_aperture"])

    art_alpha = masks["aperture"]
    alpha_over(frame, artwork_bgr, art_alpha, levels["artwork"])

    # Keep the portal rim alive over the artwork without letting the wave layer
    # compete with the source at peak.
    blend_mask(frame, masks["edge"], PORTAL_GLOW, 0.12 * levels["artwork"], glow=0.012 * levels["artwork"])

    if labels:
        base.draw_text(frame, f"wave-to-authored-artwork portal v002  c={coherence:.2f}", (42, 58), LABEL, scale=0.54)
        base.draw_text(frame, "8-source octagonal gather; whole Nature_Cosmic_Sun.svg through radial aperture", (42, 88), LABEL, scale=0.36)

    return frame, {
        "time_seconds": round(time_seconds, 4),
        "coherence": round(coherence, 4),
        "levels": {key: round(value, 4) for key, value in levels.items()},
        "source_positions": [
            {"source_id": source.source_id, "x": round(source.x, 3), "y": round(source.y, 3)}
            for source in sources
        ],
        "portal": {
            "aperture_nonzero": int(np.count_nonzero(masks["aperture"] > 9)),
            "full_aperture_nonzero": int(np.count_nonzero(masks["full"] > 9)),
            "ray_aperture_nonzero": int(np.count_nonzero(masks["rays"] > 9)),
            "central_aperture_nonzero": int(np.count_nonzero(masks["central"] > 9)),
            "artwork_alpha_nonzero": int(np.count_nonzero(artwork_alpha > 9)),
        },
    }


def make_alignment_debug_still(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray, artwork_info: dict[str, object]) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    sources = target_sources_at(PEAK_TIME_SECONDS, 1.0)
    field = base.evaluate_field(sources, PEAK_TIME_SECONDS, blur_sigma=BLUR_SIGMA)
    levels = time_levels(PEAK_TIME_SECONDS, 1.0)
    masks = portal_aperture(levels, artwork_alpha)

    wave = render_wave_layer(field, levels | {"positive": 0.44, "negative": 0.55, "line": 0.90, "water": 0.75})
    draw_octagonal_axes(wave, alpha=0.62, labels=True)
    draw_source_positions(wave, sources, alpha=0.90, labels=True)
    cv2.drawMarker(wave, (round(TARGET.center_px[0]), round(TARGET.center_px[1])), rgb_to_bgr(PORTAL_GLOW), cv2.MARKER_CROSS, 32, 2, line_type=cv2.LINE_AA)

    mask_panel = np.zeros((H, W, 3), dtype=np.uint8)
    blend_mask(mask_panel, masks["full"], TEAL, 0.36)
    blend_mask(mask_panel, masks["rays"], PORTAL_ORANGE, 0.78)
    blend_mask(mask_panel, masks["central"], PORTAL_GLOW, 0.72)
    blend_mask(mask_panel, masks["edge"], PORTAL_GLOW, 0.56)
    draw_octagonal_axes(mask_panel, alpha=0.46)

    final, _ = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0)
    x0, y0, x1, y1 = [int(v) for v in artwork_info["art_bbox_px"]]
    cv2.rectangle(final, (x0, y0), (x1, y1), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)
    cv2.circle(final, (round(TARGET.center_px[0]), round(TARGET.center_px[1])), round(ARTWORK_OUTER_RADIUS_PX), rgb_to_bgr(TEAL), 1, lineType=cv2.LINE_AA)
    cv2.drawMarker(final, (round(TARGET.center_px[0]), round(TARGET.center_px[1])), rgb_to_bgr(PORTAL_GLOW), cv2.MARKER_CROSS, 32, 2, line_type=cv2.LINE_AA)

    panels = [
        cv2.resize(wave, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(mask_panel, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(final, (640, 360), interpolation=cv2.INTER_AREA),
    ]
    labels = [
        "8 source positions + wave center + radial axes",
        "aperture masks: center first, 8 rays next, full circle",
        "final alignment: artwork bbox, shared center, aperture edge",
    ]
    for panel, label in zip(panels, labels, strict=True):
        base.draw_text(panel, label, (18, 36), LABEL, scale=0.36)
    sheet = cv2.hconcat(panels)
    path = DEBUG_DIR / "wave_to_cosmic_sun_portal_v002_alignment_debug.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_aperture_comparison_debug(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    levels = time_levels(PEAK_TIME_SECONDS, 1.0)
    masks = portal_aperture(levels, artwork_alpha)

    whole = np.zeros((H, W, 3), dtype=np.uint8)
    alpha_over(whole, artwork_bgr, masks["aperture"], 1.0)
    blend_mask(whole, masks["edge"], PORTAL_GLOW, 0.20)

    inner_crop = np.zeros((H, W, 3), dtype=np.uint8)
    inner_mask = np.minimum(circle_mask(*TARGET.center_px, ARTWORK_OUTER_RADIUS_PX * 0.70, soft_edge=24.0), artwork_alpha)
    inner_edge = cv2.GaussianBlur(
        cv2.morphologyEx(np.where(inner_mask > 12, 255, 0).astype(np.uint8), cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))),
        (0, 0),
        4.0,
    )
    alpha_over(inner_crop, artwork_bgr, inner_mask, 1.0)
    blend_mask(inner_crop, inner_edge, PORTAL_GLOW, 0.20)

    left = cv2.resize(whole, (960, 540), interpolation=cv2.INTER_AREA)
    right = cv2.resize(inner_crop, (960, 540), interpolation=cv2.INTER_AREA)
    base.draw_text(left, "USED: whole authored source through radial aperture", (28, 48), LABEL, scale=0.48)
    base.draw_text(right, "DEBUG ONLY: inner-motif crop NOT USED", (28, 48), LABEL, scale=0.48)
    base.draw_text(right, "not used unless Austin explicitly approves a crop", (28, 82), LABEL, scale=0.34)
    sheet = cv2.hconcat([left, right])
    path = DEBUG_DIR / "wave_to_cosmic_sun_portal_v002_aperture_comparison_debug_NOT_USED.png"
    cv2.imwrite(str(path), sheet)
    return path


def save_stills(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in (
        ("before", BEFORE_TIME_SECONDS),
        ("gather", GATHER_TIME_SECONDS),
        ("portal", PORTAL_TIME_SECONDS),
        ("peak", PEAK_TIME_SECONDS),
        ("after", AFTER_TIME_SECONDS),
    ):
        frame, _info = render_frame(t, artwork_bgr, artwork_alpha, force_coherence=coherence_at_time(t))
        if key == "peak":
            peak_path = PEAK_DIR / "wave_to_cosmic_sun_portal_v002_peak.png"
            cv2.imwrite(str(peak_path), frame)
            outputs["peak_still"] = str(peak_path.relative_to(OUT_DIR))
        path = STILLS_DIR / f"wave_to_cosmic_sun_portal_v002_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[f"{key}_still"] = str(path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(stills: dict[str, str], debug_path: Path, aperture_debug_path: Path) -> Path:
    panels: list[np.ndarray] = []
    for key, label in (
        ("before_still", "before: loose field"),
        ("gather_still", "gather: 8-source lock"),
        ("portal_still", "portal: center+rays"),
        ("peak_still", "peak: whole source dominates"),
        ("after_still", "after: drift returns"),
    ):
        img = cv2.imread(str(OUT_DIR / stills[key]), cv2.IMREAD_COLOR)
        if img is None:
            img = np.zeros((H, W, 3), dtype=np.uint8)
        panel = cv2.resize(img, (384, 216), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (14, 30), LABEL, scale=0.32)
        panels.append(panel)
    row1 = cv2.hconcat(panels)
    debug = cv2.imread(str(debug_path), cv2.IMREAD_COLOR)
    debug_row = cv2.resize(debug if debug is not None else np.zeros((360, 1920, 3), dtype=np.uint8), (1920, 360), interpolation=cv2.INTER_AREA)
    aperture = cv2.imread(str(aperture_debug_path), cv2.IMREAD_COLOR)
    aperture_row = cv2.resize(aperture if aperture is not None else np.zeros((540, 1920, 3), dtype=np.uint8), (1920, 360), interpolation=cv2.INTER_AREA)
    sheet = cv2.vconcat([row1, debug_row, aperture_row])
    path = OUT_DIR / "wave_to_artwork_portal_v002_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray) -> dict[str, object]:
    output_path = OUT_DIR / "wave_to_cosmic_sun_portal_v002.mp4"
    writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
    peak_info: dict[str, object] | None = None
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = frame_idx / FPS
            frame, info = render_frame(time_seconds, artwork_bgr, artwork_alpha)
            writer.write(frame)
            if frame_idx == PEAK_FRAME:
                peak_info = info
            if (frame_idx + 1) % FPS == 0:
                print(f"  wave_to_cosmic_sun_portal_v002.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0)
    return {
        "filename": "wave_to_cosmic_sun_portal_v002.mp4",
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "peak_frame": PEAK_FRAME,
        "peak_time_seconds": PEAK_TIME_SECONDS,
        "peak_info": peak_info,
    }


def write_manifest(
    provenance: dict[str, object],
    artwork_info: dict[str, object],
    clip_summary: dict[str, object],
    stills: dict[str, str],
    debug_path: Path,
    aperture_debug_path: Path,
    contact_path: Path,
    provenance_note: Path,
) -> Path:
    manifest = {
        "project": "wave_to_artwork_portal_v002",
        "status": "INTERNAL ONLY; not Austin-approved for public use; no cultural-meaning claim",
        "renderer": "scripts/wave_to_artwork_portal_v002.py",
        "base_script": "scripts/wave_to_artwork_portal_v001.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "concept": "wave-to-authored-artwork portal study pending Austin review",
        "critical_correction": "v002 uses an exact 8-source octagonal gather instead of v001 sixfold geometry.",
        "rules": {
            "training": False,
            "diffusion": False,
            "style_imitation": False,
            "source_shape_fragment_reuse": False,
            "source_artwork_geometry_changes": "uniform scale/position/opacity/presentation aperture masking only",
            "beauty_layer": "wave field plus whole authored source through circular/radial aperture",
        },
        "source_provenance": provenance,
        "octagonal_target": {
            **asdict(TARGET),
            "sources": [asdict(source) for source in TARGET.sources],
            "uses_center_source": False,
            "central_region_source": "constructive focal antinode from 8 phase-locked ring sources",
        },
        "artwork_alignment": artwork_info,
        "aperture_sequence": {
            "central_orb_aperture": "opens first from 5.0s",
            "eight_ray_apertures": "open next from 5.32s and align to octagonal axes",
            "full_radial_aperture": "soft circular whole-source mask opens from 6.04s",
            "rectangular_bounds": "original source bbox exists only in debug; beauty render fades rectangular corners with circular mask",
        },
        "timing": {
            "loose_field": [0.0, 3.0],
            "octagonal_gather": [3.0, 5.0],
            "portal": [5.0, 8.0],
            "release": [8.0, 10.0],
            "drift": [10.0, 12.0],
        },
        "clip": clip_summary,
        "deliverables": {
            "mp4": clip_summary["mp4"],
            "before_still": stills["before_still"],
            "gather_still": stills["gather_still"],
            "portal_still": stills["portal_still"],
            "peak_still": stills["peak_still"],
            "after_still": stills["after_still"],
            "alignment_debug_still": str(debug_path.relative_to(OUT_DIR)),
            "aperture_comparison_debug_NOT_USED": str(aperture_debug_path.relative_to(OUT_DIR)),
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "source_provenance_note": str(provenance_note.relative_to(OUT_DIR)),
            "readme": "README.md",
        },
    }
    path = OUT_DIR / "wave_to_artwork_portal_v002_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(clip_summary: dict[str, object], artwork_info: dict[str, object]) -> Path:
    lines = [
        "# Wave To Artwork Portal v002",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved for public use. Not public-use guidance. No cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet tests a wave-to-authored-artwork portal study pending Austin review. It keeps the v001 portal idea but corrects the structural mismatch: `Nature_Cosmic_Sun.svg` has an eightfold radial rhythm, so v002 uses an exact 8-source octagonal wave gather instead of the sixfold radial geometry inherited by v001.",
        "",
        "The render does not train, diffuse, imitate, synthesize, decompose, or reuse Austin's individual shapes as generic primitives. The source SVG is rasterized as a whole authored artwork at high resolution, downsampled for crispness, and revealed through uniform scale, position, opacity, and circular/radial presentation masking only.",
        "",
        "## Timing",
        "",
        "- 0.0-3.0s: loose dark water/cymatic field.",
        "- 3.0-5.0s: 8-source octagonal radial geometry gathers.",
        "- 5.0-8.0s: portal moment into `Nature_Cosmic_Sun.svg`.",
        "- 8.0-10.0s: artwork recedes into wave geometry.",
        "- 10.0-12.0s: drifting field returns.",
        "",
        "## v002 Fixes",
        "",
        "- Eight phase-locked ring sources align to the artwork's eight radial ray/trigon axes.",
        "- The central orb aperture opens first, eight ray apertures open next, then the whole authored source appears through a soft circular aperture.",
        "- The original rectangular SVG bounds are not used as a beauty-frame card. They are shown only in the alignment debug still.",
        "- Wave positive regions fade quickly during the portal; dark/negative structure and portal rim persist more subtly so the artwork dominates at peak.",
        "- The source is rasterized at 4x display size and downsampled before compositing to avoid v001's blurred source read.",
        "",
        "## Alignment",
        "",
        f"- Artwork center aligned to wave center: `{artwork_info['art_center_px']}`.",
        f"- Artwork original bbox at render scale: `{artwork_info['art_bbox_px']}`.",
        f"- Artwork outer radial radius: `{ARTWORK_OUTER_RADIUS_PX}` px.",
        f"- Wave source ring radius: `{TARGET.source_ring_radius_px}` px.",
        "- Octagonal source count: `8`.",
        "- No center source is added; the central field read is a constructive focal antinode from the eight phase-locked ring sources.",
        "",
        "## Deliverables",
        "",
        "- `wave_to_cosmic_sun_portal_v002.mp4`: 1920x1080, 24 fps, 12 seconds.",
        "- Before/gather/portal/peak/after stills in `stills/`.",
        "- Peak still: `peak_stills/wave_to_cosmic_sun_portal_v002_peak.png`.",
        "- Alignment debug still: `debug_stills/wave_to_cosmic_sun_portal_v002_alignment_debug.png`.",
        "- Debug-only aperture comparison: `debug_stills/wave_to_cosmic_sun_portal_v002_aperture_comparison_debug_NOT_USED.png`.",
        "- Contact sheet: `wave_to_artwork_portal_v002_contact_sheet.png`.",
        "- Manifest: `wave_to_artwork_portal_v002_manifest.json`.",
        "- Source provenance note: `SOURCE_PROVENANCE.md`.",
        "",
        "## Honest Verdict",
        "",
        "v002 is structurally better aligned than v001 because the wave gather and aperture sequence now share the source artwork's eightfold rhythm. The circular/radial aperture also removes the rectangular-card read: at peak, the source's square bounds are not visible in the beauty frame.",
        "",
        "The remaining review question is aesthetic and cultural, not technical: whether the wave-to-authored-artwork portal feels like meaningful alignment or like a presentation effect. This packet makes no cultural claim and should be treated as an internal exploration pending cultural review.",
        "",
        "## Cultural Boundary",
        "",
        "Internal only. Not Austin-approved for public use. No cultural-meaning claim. Nothing here authorizes projector, social, sponsor, press, or external use without Austin's review of this specific output.",
        "",
        "Renderer: `scripts/wave_to_artwork_portal_v002.py`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wave-to-authored-artwork portal v002.")
    parser.add_argument("--preview", action="store_true", help="Write still/debug artifacts without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    provenance = verify_source_provenance()
    if not provenance["ok"]:
        issue_path = OUT_DIR / "SOURCE_PROVENANCE_ISSUE.md"
        issue_path.write_text(
            "# Source Provenance Issue\n\n"
            "Rendering stopped because source approval/provenance was unclear.\n\n"
            + "\n".join(f"- {issue}" for issue in provenance["issues"])
            + "\n",
            encoding="utf-8",
        )
        raise SystemExit(f"source provenance failed; wrote {issue_path}")

    provenance_note = write_source_provenance_note(provenance)
    artwork_bgr, artwork_alpha, artwork_info = load_artwork_layer()
    print("Writing v002 stills and debug artifacts", flush=True)
    stills = save_stills(artwork_bgr, artwork_alpha)
    debug_path = make_alignment_debug_still(artwork_bgr, artwork_alpha, artwork_info)
    aperture_debug_path = make_aperture_comparison_debug(artwork_bgr, artwork_alpha)
    contact_path = make_contact_sheet(stills, debug_path, aperture_debug_path)

    if args.preview:
        _frame, peak_info = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0)
        clip_summary = {
            "filename": "wave_to_cosmic_sun_portal_v002.mp4",
            "mp4": "wave_to_cosmic_sun_portal_v002.mp4",
            "peak_frame": PEAK_FRAME,
            "peak_time_seconds": PEAK_TIME_SECONDS,
            "peak_info": peak_info,
        }
    else:
        print("Rendering wave_to_cosmic_sun_portal_v002.mp4", flush=True)
        clip_summary = render_clip(artwork_bgr, artwork_alpha)

    manifest = write_manifest(provenance, artwork_info, clip_summary, stills, debug_path, aperture_debug_path, contact_path, provenance_note)
    readme = write_readme(clip_summary, artwork_info)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
