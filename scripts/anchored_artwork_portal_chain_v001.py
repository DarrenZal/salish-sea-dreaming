#!/usr/bin/env python3
"""
Anchored artwork portal chain v001.

Internal mathematical/visual alignment study for Salish Sea Dreaming. This
script chains the v002 wave-to-artwork portal into a second Austin-authored
source artwork using one stable shared anchor: the sun-disc center and radius.

This is not atom reconfiguration. It does not train, diffuse, imitate,
synthesize, decompose, recolor, warp, or reuse Austin artwork components as
generic motifs. The anchor guides source alignment and masking only.

Status: INTERNAL ONLY. Pending Austin review. Not approved for public, show,
projector, sponsor, or social use. No cultural-meaning claim.
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
import wave_to_artwork_portal_v002 as wave_v002


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "anchored_artwork_portal_chain_v001_2026-05-21"
)
STILLS_DIR = OUT_DIR / "stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
SOURCE_DIR = OUT_DIR / "source_assets"

SOURCE_MAP = ROOT / "docs" / "space-center" / "austin-artwork-portal-source-map-2026-05-21.md"
CONSENT_MAP = ROOT / "docs" / "space-center" / "austin-consent-map.md"
V002_README = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "wave_to_artwork_portal_v002_2026-05-21"
    / "README.md"
)
PROVENANCE_CSV = ROOT / "austin-v2-ingest" / "provenance" / "manifest.csv"
TRIAGE_JSON = ROOT / "austin-v2-ingest" / "inbox" / "_triage.json"

W = base.W
H = base.H
FPS = base.FPS
DURATION_SECONDS = 24.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

BEFORE_TIME_SECONDS = 2.0
PORTAL_TIME_SECONDS = 6.2
ANCHOR_TIME_SECONDS = 10.0
TRANSITION_TIME_SECONDS = 15.0
AFTER_TIME_SECONDS = 20.0
PEAK_FRAME = int(AFTER_TIME_SECONDS * FPS)

ANCHOR_RADIUS_PX = 276.0
ANCHOR_CENTER_PX = (W * 0.5, H * 0.5)
ARTWORK_HIGH_RES_FACTOR = 4

DEEP_GROUND = (0, 5, 7)
MUTED_TEAL = (69, 119, 120)
PORTAL_GLOW = (255, 215, 130)
PORTAL_ORANGE = (218, 96, 39)
SOFT_GOLD = (246, 195, 91)
LABEL = (226, 234, 230)


@dataclass(frozen=True)
class ArtworkSpec:
    key: str
    filename: str
    expected_sha256: str
    source_path: Path
    approved_copy: Path
    drive_mirror: Path | None
    viewbox_size: float
    anchor_center_viewbox: tuple[float, float]
    anchor_radius_viewbox: float
    anchor_label: str
    cultural_load: str
    portal_use: str


@dataclass(frozen=True)
class ArtworkLayer:
    spec: ArtworkSpec
    bgr: np.ndarray
    alpha: np.ndarray
    soft_alpha: np.ndarray
    info: dict[str, object]


NATURE_SPEC = ArtworkSpec(
    key="nature_cosmic_sun",
    filename="Nature_Cosmic_Sun.svg",
    expected_sha256="197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1",
    source_path=ROOT / "track2-deterministic" / "source-vectors" / "Nature_Cosmic_Sun.svg",
    approved_copy=ROOT / "austin-v2-ingest" / "approved" / "Nature_Cosmic_Sun.svg",
    drive_mirror=ROOT / "austin-reference" / "google-drive-ai-training-2026-05-15" / "Nature_Cosmic_Sun.svg",
    viewbox_size=108.0,
    anchor_center_viewbox=(53.92, 53.86),
    anchor_radius_viewbox=34.08,
    anchor_label="main orb/sun-body circle",
    cultural_load="medium",
    portal_use="high; first internal radial portal anchor",
)

RAVEN_SPEC = ArtworkSpec(
    key="animal_bird_raven_sun",
    filename="Animal_Bird_Raven_Sun.svg",
    expected_sha256="5fa0ceaea6a49cc4c1408434541dc3a69e89d935fd96740606a4f1787c92c766",
    source_path=ROOT / "track2-deterministic" / "source-vectors" / "Animal_Bird_Raven_Sun.svg",
    approved_copy=ROOT / "austin-v2-ingest" / "approved" / "Animal_Bird_Raven_Sun.svg",
    drive_mirror=ROOT / "austin-reference" / "google-drive-ai-training-2026-05-15" / "Animal_Bird_Raven_Sun.svg",
    viewbox_size=108.0,
    anchor_center_viewbox=(54.00, 53.51),
    anchor_radius_viewbox=28.15,
    anchor_label="central Raven Sun disc",
    cultural_load="medium-high",
    portal_use="medium; private whole-composition portal/reference test only",
)

ARTWORK_SPECS = (NATURE_SPEC, RAVEN_SPEC)


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


def stable_anchor_mask(*, radius: float = ANCHOR_RADIUS_PX, soft_edge: float = 18.0) -> np.ndarray:
    return wave_v002.circle_mask(*ANCHOR_CENTER_PX, radius, soft_edge=soft_edge)


def ring_mask(radius: float, thickness: float = 4.0, blur: float = 3.0) -> np.ndarray:
    cx, cy = ANCHOR_CENTER_PX
    outer = wave_v002.circle_mask(cx, cy, radius + thickness * 0.5, soft_edge=0.0)
    inner = wave_v002.circle_mask(cx, cy, max(1.0, radius - thickness * 0.5), soft_edge=0.0)
    ring = cv2.subtract(outer, inner)
    return cv2.GaussianBlur(ring, (0, 0), blur)


ANCHOR_MASK = stable_anchor_mask()
ANCHOR_RING_MASK = ring_mask(ANCHOR_RADIUS_PX, thickness=5.0, blur=3.0)


def coherence_at_time(time_seconds: float) -> float:
    if time_seconds < 4.0:
        return smoothstep01(time_seconds / 4.0)
    return 1.0


def wave_levels(time_seconds: float) -> dict[str, float]:
    nature_in = smoothstep01((time_seconds - 4.2) / 2.8)
    raven_in = smoothstep01((time_seconds - 12.0) / 6.0)
    source_dom = max(nature_in, raven_in)
    return {
        "water": clamp01(0.95 - 0.40 * source_dom),
        "positive": clamp01(0.94 * (1.0 - 0.92 * source_dom)),
        "negative": clamp01(0.82 * (1.0 - 0.58 * source_dom)),
        "line": clamp01(0.78 * (1.0 - 0.34 * source_dom)),
    }


def render_wave_base(time_seconds: float) -> np.ndarray:
    coherence = coherence_at_time(time_seconds)
    sources = wave_v002.target_sources_at(time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=wave_v002.BLUR_SIGMA)
    return wave_v002.render_wave_layer(field, wave_levels(time_seconds))


def verify_source_provenance() -> dict[str, object]:
    issues: list[str] = []
    for required in (SOURCE_MAP, CONSENT_MAP, V002_README, PROVENANCE_CSV, TRIAGE_JSON):
        if not required.exists():
            issues.append(f"missing required context file: {required}")
    for spec in ARTWORK_SPECS:
        if not spec.source_path.exists():
            issues.append(f"missing source vector: {spec.source_path}")
        if not spec.approved_copy.exists():
            issues.append(f"missing approved-ingest copy: {spec.approved_copy}")
    if issues:
        return {"ok": False, "issues": issues}

    provenance_rows = list(csv.DictReader(PROVENANCE_CSV.open(newline="", encoding="utf-8")))
    triage_rows = json.loads(TRIAGE_JSON.read_text(encoding="utf-8"))
    pieces: dict[str, dict[str, object]] = {}
    for spec in ARTWORK_SPECS:
        source_sha = sha256(spec.source_path)
        approved_sha = sha256(spec.approved_copy)
        drive_sha = sha256(spec.drive_mirror) if spec.drive_mirror and spec.drive_mirror.exists() else None
        if source_sha != spec.expected_sha256:
            issues.append(f"{spec.filename} source SHA mismatch: {source_sha}")
        if approved_sha != source_sha:
            issues.append(f"{spec.filename} approved-ingest copy does not match source vector")
        if drive_sha is not None and drive_sha != source_sha:
            issues.append(f"{spec.filename} Drive mirror does not match source vector")
        provenance_row = next((row for row in provenance_rows if row.get("filename") == spec.filename), None)
        if provenance_row is None:
            issues.append(f"{spec.filename} not found in provenance manifest")
        elif provenance_row.get("sha256") != source_sha:
            issues.append(f"{spec.filename} provenance manifest SHA mismatch")
        triage_row = next((row for row in triage_rows if row.get("filename") == spec.filename), None)
        if triage_row is None:
            issues.append(f"{spec.filename} not found in triage metadata")
        elif triage_row.get("recommendation") != "approve":
            issues.append(f"{spec.filename} triage recommendation is not approve: {triage_row.get('recommendation')}")

        pieces[spec.key] = {
            "filename": spec.filename,
            "source_svg": str(spec.source_path),
            "approved_copy": str(spec.approved_copy),
            "drive_mirror": str(spec.drive_mirror) if spec.drive_mirror and spec.drive_mirror.exists() else None,
            "sha256": source_sha,
            "expected_sha256": spec.expected_sha256,
            "provenance_row": provenance_row,
            "triage_row": triage_row,
            "cultural_load": spec.cultural_load,
            "portal_use": spec.portal_use,
            "anchor": {
                "label": spec.anchor_label,
                "center_viewbox": list(spec.anchor_center_viewbox),
                "radius_viewbox": spec.anchor_radius_viewbox,
            },
        }

    return {
        "ok": not issues,
        "issues": issues,
        "pieces": pieces,
        "context_docs": {
            "source_map": str(SOURCE_MAP),
            "consent_map": str(CONSENT_MAP),
            "wave_to_artwork_portal_v002_readme": str(V002_README),
        },
        "public_approval_status": "pending; internal-only use only, no public/show/projector use until Austin review",
    }


def rasterize_svg(spec: ArtworkSpec, display_size_px: int) -> tuple[Path, Path]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    copied_svg = SOURCE_DIR / spec.filename
    if not copied_svg.exists() or sha256(copied_svg) != sha256(spec.source_path):
        shutil.copy2(spec.source_path, copied_svg)

    high_size = display_size_px * ARTWORK_HIGH_RES_FACTOR
    stem = Path(spec.filename).stem
    high_path = SOURCE_DIR / f"{stem}_author_source_highres_rgba.png"
    display_path = SOURCE_DIR / f"{stem}_author_source_display_rgba.png"
    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("ImageMagick `magick` is required to rasterize Austin source SVGs.")
    subprocess.run(
        [
            magick,
            "-background",
            "none",
            "-density",
            "768",
            str(spec.source_path),
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


def soft_artwork_alpha(alpha: np.ndarray, bbox: tuple[int, int, int, int], feather_px: float) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.minimum(xx - x0, x1 - xx)
    dy = np.minimum(yy - y0, y1 - yy)
    edge = np.minimum(dx, dy)
    feather = np.clip(edge / max(1e-6, feather_px), 0.0, 1.0)
    feather = feather * feather * (3.0 - 2.0 * feather)
    return np.clip(alpha.astype(np.float32) * feather, 0, 255).astype(np.uint8)


def load_artwork_layer(spec: ArtworkSpec) -> ArtworkLayer:
    scale = ANCHOR_RADIUS_PX / spec.anchor_radius_viewbox
    display_size = round(spec.viewbox_size * scale)
    high_path, display_path = rasterize_svg(spec, display_size)
    rgba = cv2.imread(str(display_path), cv2.IMREAD_UNCHANGED)
    if rgba is None:
        raise RuntimeError(f"could not read source raster: {display_path}")
    if rgba.shape[2] == 3:
        bgr = rgba
        alpha = np.full(rgba.shape[:2], 255, dtype=np.uint8)
    else:
        bgr = rgba[:, :, :3]
        alpha = rgba[:, :, 3]

    center_x, center_y = ANCHOR_CENTER_PX
    anchor_x = spec.anchor_center_viewbox[0] / spec.viewbox_size * display_size
    anchor_y = spec.anchor_center_viewbox[1] / spec.viewbox_size * display_size
    x0 = round(center_x - anchor_x)
    y0 = round(center_y - anchor_y)
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
        raise RuntimeError(f"{spec.filename} does not intersect the canvas")
    canvas[dy0:dy1, dx0:dx1] = bgr[sy0:sy1, sx0:sx1]
    canvas_alpha[dy0:dy1, dx0:dx1] = alpha[sy0:sy1, sx0:sx1]

    bbox = (int(dx0), int(dy0), int(dx1), int(dy1))
    soft_alpha = soft_artwork_alpha(canvas_alpha, bbox, feather_px=18.0 if spec.key == RAVEN_SPEC.key else 10.0)
    info = {
        "key": spec.key,
        "filename": spec.filename,
        "source_svg": str(spec.source_path),
        "high_res_raster": str(high_path),
        "display_raster": str(display_path),
        "high_res_factor": ARTWORK_HIGH_RES_FACTOR,
        "art_scale_px_per_svg_unit": scale,
        "art_raster_size_px": [int(bgr.shape[1]), int(bgr.shape[0])],
        "art_bbox_px": [bbox[0], bbox[1], bbox[2], bbox[3]],
        "anchor_center_viewbox": list(spec.anchor_center_viewbox),
        "anchor_radius_viewbox": spec.anchor_radius_viewbox,
        "anchor_center_px": [round(center_x, 3), round(center_y, 3)],
        "anchor_radius_px": ANCHOR_RADIUS_PX,
        "anchor_label": spec.anchor_label,
    }
    return ArtworkLayer(spec=spec, bgr=canvas, alpha=canvas_alpha, soft_alpha=soft_alpha, info=info)


def nature_aperture_mask(time_seconds: float, nature: ArtworkLayer) -> np.ndarray:
    if time_seconds < 4.0:
        return np.zeros((H, W), dtype=np.uint8)
    central = smoothstep01((time_seconds - 4.00) / 0.62)
    rays = smoothstep01((time_seconds - 4.62) / 1.00)
    full = smoothstep01((time_seconds - 5.80) / 1.25)
    if time_seconds >= 8.0:
        central = rays = full = 1.0
    levels = {
        "central_aperture": central,
        "ray_aperture": rays,
        "full_aperture": full,
    }
    masks = wave_v002.portal_aperture(levels, nature.alpha)
    return masks["aperture"]


def raven_reveal_mask(time_seconds: float, raven: ArtworkLayer) -> np.ndarray:
    if time_seconds < 12.0:
        return np.zeros((H, W), dtype=np.uint8)
    progress = smoothstep01((time_seconds - 12.0) / 6.0)
    anchor_open = smoothstep01((time_seconds - 12.0) / 0.82)
    radius = ANCHOR_RADIUS_PX + progress * 760.0
    expansion = wave_v002.circle_mask(*ANCHOR_CENTER_PX, radius, soft_edge=104.0)
    reveal = np.maximum((ANCHOR_MASK.astype(np.float32) * anchor_open).astype(np.uint8), expansion)
    if time_seconds >= 18.0:
        reveal = np.full((H, W), 255, dtype=np.uint8)
    return np.minimum(reveal, raven.soft_alpha)


def source_hold_levels(time_seconds: float) -> dict[str, float]:
    nature_in = smoothstep01((time_seconds - 4.18) / 2.15)
    if time_seconds >= 8.0:
        nature_in = 1.0
    nature_out = 1.0 - smoothstep01((time_seconds - 16.4) / 1.55)
    raven_in = smoothstep01((time_seconds - 12.0) / 6.0)
    if time_seconds >= 18.0:
        raven_in = 1.0
    return {
        "nature_opacity": clamp01(nature_in * nature_out),
        "raven_opacity": clamp01(raven_in),
        "anchor_alpha": clamp01(smoothstep01((time_seconds - 7.4) / 0.9) * (1.0 - smoothstep01((time_seconds - 18.2) / 0.9))),
    }


def draw_anchor_ring(frame: np.ndarray, alpha: float) -> None:
    if alpha <= 0.0:
        return
    wave_v002.blend_mask(frame, ANCHOR_RING_MASK, PORTAL_GLOW, 0.26 * alpha, glow=0.010 * alpha)
    wave_v002.blend_mask(frame, ANCHOR_RING_MASK, PORTAL_ORANGE, 0.08 * alpha)


def render_frame(
    time_seconds: float,
    nature: ArtworkLayer,
    raven: ArtworkLayer,
    *,
    labels: bool = False,
) -> tuple[np.ndarray, dict[str, object]]:
    frame = render_wave_base(time_seconds)
    levels = source_hold_levels(time_seconds)
    nature_mask = nature_aperture_mask(time_seconds, nature)
    if levels["nature_opacity"] > 0.0:
        wave_v002.alpha_over(frame, nature.bgr, nature_mask, levels["nature_opacity"])
    draw_anchor_ring(frame, levels["anchor_alpha"])
    raven_mask = raven_reveal_mask(time_seconds, raven)
    if levels["raven_opacity"] > 0.0:
        wave_v002.alpha_over(frame, raven.bgr, raven_mask, levels["raven_opacity"])
    # Keep a small rim over the transition so the stable anchor remains legible
    # without becoming a reusable drawn motif.
    draw_anchor_ring(frame, levels["anchor_alpha"] * (1.0 - 0.45 * levels["raven_opacity"]))

    if labels:
        base.draw_text(frame, f"anchored artwork portal chain v001  t={time_seconds:05.2f}", (42, 58), LABEL, scale=0.50)
        base.draw_text(frame, "stable source-alignment anchor: shared sun-disc center/radius", (42, 88), LABEL, scale=0.36)
    info = {
        "time_seconds": round(time_seconds, 4),
        "coherence": round(coherence_at_time(time_seconds), 4),
        "levels": {key: round(value, 4) for key, value in levels.items()},
        "masks": {
            "nature_aperture_nonzero": int(np.count_nonzero(nature_mask > 9)),
            "raven_reveal_nonzero": int(np.count_nonzero(raven_mask > 9)),
            "anchor_nonzero": int(np.count_nonzero(ANCHOR_MASK > 9)),
        },
    }
    return frame, info


def make_anchor_debug_sheet(nature: ArtworkLayer, raven: ArtworkLayer) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    t = ANCHOR_TIME_SECONDS
    coherence = coherence_at_time(t)
    sources = wave_v002.target_sources_at(t, coherence)
    field = base.evaluate_field(sources, t, blur_sigma=wave_v002.BLUR_SIGMA)
    wave = wave_v002.render_wave_layer(field, {"water": 0.72, "positive": 0.42, "negative": 0.52, "line": 0.88})
    wave_v002.draw_octagonal_axes(wave, alpha=0.58, labels=True)
    wave_v002.draw_source_positions(wave, sources, alpha=0.90, labels=True)
    cv2.circle(wave, (round(ANCHOR_CENTER_PX[0]), round(ANCHOR_CENTER_PX[1])), round(ANCHOR_RADIUS_PX), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)

    nature_panel = np.zeros((H, W, 3), dtype=np.uint8)
    nature_mask = nature_aperture_mask(8.0, nature)
    wave_v002.alpha_over(nature_panel, nature.bgr, nature_mask, 1.0)
    draw_anchor_ring(nature_panel, 1.0)
    nx0, ny0, nx1, ny1 = [int(v) for v in nature.info["art_bbox_px"]]
    cv2.rectangle(nature_panel, (nx0, ny0), (nx1, ny1), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)

    raven_panel = np.zeros((H, W, 3), dtype=np.uint8)
    wave_v002.alpha_over(raven_panel, raven.bgr, raven.soft_alpha, 1.0)
    draw_anchor_ring(raven_panel, 1.0)
    rx0, ry0, rx1, ry1 = [int(v) for v in raven.info["art_bbox_px"]]
    cv2.rectangle(raven_panel, (rx0, ry0), (rx1, ry1), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)

    mask_panel = np.zeros((H, W, 3), dtype=np.uint8)
    wave_v002.blend_mask(mask_panel, nature_mask, MUTED_TEAL, 0.42)
    wave_v002.blend_mask(mask_panel, ANCHOR_MASK, PORTAL_GLOW, 0.40)
    wave_v002.blend_mask(mask_panel, raven_reveal_mask(15.0, raven), PORTAL_ORANGE, 0.34)
    draw_anchor_ring(mask_panel, 1.0)
    cv2.rectangle(mask_panel, (nx0, ny0), (nx1, ny1), rgb_to_bgr(MUTED_TEAL), 1, lineType=cv2.LINE_AA)
    cv2.rectangle(mask_panel, (rx0, ry0), (rx1, ry1), rgb_to_bgr(PORTAL_ORANGE), 1, lineType=cv2.LINE_AA)

    panels = [
        cv2.resize(wave, (960, 540), interpolation=cv2.INTER_AREA),
        cv2.resize(nature_panel, (960, 540), interpolation=cv2.INTER_AREA),
        cv2.resize(raven_panel, (960, 540), interpolation=cv2.INTER_AREA),
        cv2.resize(mask_panel, (960, 540), interpolation=cv2.INTER_AREA),
    ]
    labels = [
        "wave proof point: 8-source geometry, axes, shared center",
        "Nature_Cosmic_Sun: whole source through v002 radial aperture",
        "Animal_Bird_Raven_Sun: whole source aligned by sun-disc anchor",
        "masks + bboxes: Nature aperture, stable anchor, Raven expansion",
    ]
    for panel, label in zip(panels, labels, strict=True):
        base.draw_text(panel, label, (26, 46), LABEL, scale=0.46)
    sheet = cv2.vconcat([cv2.hconcat(panels[:2]), cv2.hconcat(panels[2:])])
    path = DEBUG_DIR / "anchored_sun_portal_chain_v001_anchor_debug_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def save_stills(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in (
        ("before", BEFORE_TIME_SECONDS),
        ("portal", PORTAL_TIME_SECONDS),
        ("anchor", ANCHOR_TIME_SECONDS),
        ("transition", TRANSITION_TIME_SECONDS),
        ("after", AFTER_TIME_SECONDS),
    ):
        frame, _ = render_frame(t, nature, raven)
        path = STILLS_DIR / f"anchored_sun_portal_chain_v001_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[f"{key}_still"] = str(path.relative_to(OUT_DIR))
    peak_path = PEAK_DIR / "anchored_sun_portal_chain_v001_after_peak.png"
    peak_frame, _ = render_frame(AFTER_TIME_SECONDS, nature, raven)
    cv2.imwrite(str(peak_path), peak_frame)
    outputs["peak_still"] = str(peak_path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(stills: dict[str, str], debug_path: Path) -> Path:
    panels: list[np.ndarray] = []
    for key, label in (
        ("before_still", "before: wave gathers"),
        ("portal_still", "portal: Nature opens"),
        ("anchor_still", "anchor: shared sun disc"),
        ("transition_still", "transition: Raven from anchor"),
        ("after_still", "after: Raven holds"),
    ):
        img = cv2.imread(str(OUT_DIR / stills[key]), cv2.IMREAD_COLOR)
        if img is None:
            img = np.zeros((H, W, 3), dtype=np.uint8)
        panel = cv2.resize(img, (384, 216), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (14, 30), LABEL, scale=0.32)
        panels.append(panel)
    row1 = cv2.hconcat(panels)
    debug = cv2.imread(str(debug_path), cv2.IMREAD_COLOR)
    row2 = cv2.resize(debug if debug is not None else np.zeros((1080, 1920, 3), dtype=np.uint8), (1920, 720), interpolation=cv2.INTER_AREA)
    sheet = cv2.vconcat([row1, row2])
    path = OUT_DIR / "anchored_artwork_portal_chain_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, object]:
    output_path = OUT_DIR / "anchored_sun_portal_chain_v001.mp4"
    writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
    peak_info: dict[str, object] | None = None
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = frame_idx / FPS
            frame, info = render_frame(time_seconds, nature, raven)
            writer.write(frame)
            if frame_idx == PEAK_FRAME:
                peak_info = info
            if (frame_idx + 1) % FPS == 0:
                print(f"  anchored_sun_portal_chain_v001.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_frame(AFTER_TIME_SECONDS, nature, raven)
    return {
        "filename": "anchored_sun_portal_chain_v001.mp4",
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "peak_frame": PEAK_FRAME,
        "peak_time_seconds": AFTER_TIME_SECONDS,
        "peak_info": peak_info,
    }


def write_source_provenance_note(provenance: dict[str, object]) -> Path:
    lines = [
        "# Source Provenance Note",
        "",
        "Sources: `Nature_Cosmic_Sun.svg` and `Animal_Bird_Raven_Sun.svg`.",
        "",
        "This packet uses Austin's authored SVGs as whole source artworks. It does not train, diffuse, imitate, synthesize, decompose, recolor, warp, or reuse individual shapes as generic primitives. The shared anchor is alignment metadata: center, radius, source bbox, and portal masks.",
        "",
        "## Boundary",
        "",
        "Internal-only anchored portal study pending Austin review. No public, show, projector, sponsor, social, or press use.",
        "",
        "## Source Records",
        "",
    ]
    pieces = provenance.get("pieces", {})
    if isinstance(pieces, dict):
        for key, piece in pieces.items():
            row = piece.get("provenance_row") if isinstance(piece, dict) else None
            triage = piece.get("triage_row") if isinstance(piece, dict) else None
            consent = row.get("austin_consent", "unknown") if isinstance(row, dict) else "unknown"
            recommendation = triage.get("recommendation", "unknown") if isinstance(triage, dict) else "unknown"
            lines.extend(
                [
                    f"### {piece.get('filename', key)}",
                    "",
                    f"- Source vector: `{piece.get('source_svg')}`",
                    f"- Approved-ingest copy: `{piece.get('approved_copy')}`",
                    f"- Drive mirror: `{piece.get('drive_mirror')}`",
                    f"- SHA256: `{piece.get('sha256')}`",
                    f"- Provenance status: `{consent}`",
                    f"- Triage recommendation: `{recommendation}`",
                    f"- Cultural load: `{piece.get('cultural_load')}`",
                    f"- Portal posture: `{piece.get('portal_use')}`",
                    "",
                ]
            )
    path = OUT_DIR / "SOURCE_PROVENANCE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_manifest(
    provenance: dict[str, object],
    nature: ArtworkLayer,
    raven: ArtworkLayer,
    clip_summary: dict[str, object],
    stills: dict[str, str],
    debug_path: Path,
    contact_path: Path,
    provenance_note: Path,
) -> Path:
    manifest = {
        "project": "anchored_artwork_portal_chain_v001",
        "status": "INTERNAL ONLY; pending Austin review; no cultural-meaning claim",
        "renderer": "scripts/anchored_artwork_portal_chain_v001.py",
        "base_proof_point": "wave_to_artwork_portal_v002",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "concept": "stable shared anchor holds visual continuity while surrounding whole-source artwork changes",
        "rules": {
            "training": False,
            "diffusion": False,
            "style_imitation": False,
            "source_shape_fragment_reuse": False,
            "decomposition_for_rendering": False,
            "source_artwork_geometry_changes": "uniform scale/position/opacity/presentation masks only",
            "anchor_role": "alignment and masking metadata only; not a reusable primitive asset",
        },
        "context_docs": provenance["context_docs"],
        "source_provenance": provenance,
        "anchor": {
            "type": "shared sun-disc center/radius",
            "canvas_center_px": list(ANCHOR_CENTER_PX),
            "canvas_radius_px": ANCHOR_RADIUS_PX,
            "nature_anchor": NATURE_SPEC.anchor_label,
            "raven_anchor": RAVEN_SPEC.anchor_label,
        },
        "artwork_alignment": {
            "nature_cosmic_sun": nature.info,
            "animal_bird_raven_sun": raven.info,
        },
        "timing": {
            "wave_gather": [0.0, 4.0],
            "nature_reveal": [4.0, 8.0],
            "anchor_hold": [8.0, 12.0],
            "anchor_transition_to_raven": [12.0, 18.0],
            "raven_hold": [18.0, 24.0],
        },
        "clip": clip_summary,
        "deliverables": {
            "mp4": clip_summary["mp4"],
            "before_still": stills["before_still"],
            "portal_still": stills["portal_still"],
            "anchor_still": stills["anchor_still"],
            "transition_still": stills["transition_still"],
            "after_still": stills["after_still"],
            "peak_still": stills["peak_still"],
            "anchor_debug_sheet": str(debug_path.relative_to(OUT_DIR)),
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "source_provenance_note": str(provenance_note.relative_to(OUT_DIR)),
            "readme": "README.md",
        },
    }
    path = OUT_DIR / "anchored_artwork_portal_chain_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(nature: ArtworkLayer, raven: ArtworkLayer, clip_summary: dict[str, object]) -> Path:
    lines = [
        "# Anchored Artwork Portal Chain v001",
        "",
        "Status: INTERNAL ONLY. Pending Austin review. Not approved for public, show, projector, sponsor, social, or press use. No cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet tests an anchor-based transition chain between wave geometry and Austin-authored artworks. It uses the v002 wave-to-artwork portal proof point, then keeps one meaningful source-derived anchor stable while the surrounding whole-source artwork changes.",
        "",
        "Core framing: the stable anchor is not a generic primitive asset. It is alignment metadata: shared sun-disc center, radius, masks, axes, and source bboxes. The source artworks remain whole compositions.",
        "",
        "## Sources",
        "",
        "- `track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg`",
        "- `track2-deterministic/source-vectors/Animal_Bird_Raven_Sun.svg`",
        "",
        "Both sources are Austin curated Drive assets with provenance status `pending`. The source map marks Nature Cosmic Sun as high-suitability for private radial portal tests and Raven Sun as medium-suitability for private whole-composition portal tests. This output is internal only pending Austin review.",
        "",
        "## Sequence",
        "",
        "- 0-4s: water/cymatic field gathers into 8-fold radial geometry.",
        "- 4-8s: `Nature_Cosmic_Sun.svg` reveals through the v002 center/ray/circular portal.",
        "- 8-12s: Nature holds; the shared sun-disc anchor stabilizes.",
        "- 12-18s: `Animal_Bird_Raven_Sun.svg` emerges from the same center/radius anchor while the surrounding composition changes.",
        "- 18-24s: Raven Sun holds as the authored whole-source destination.",
        "",
        "## Anchor",
        "",
        f"- Canvas anchor center: `{list(ANCHOR_CENTER_PX)}`.",
        f"- Canvas anchor radius: `{ANCHOR_RADIUS_PX}` px.",
        f"- Nature anchor: `{NATURE_SPEC.anchor_label}`, SVG center `{list(NATURE_SPEC.anchor_center_viewbox)}`, radius `{NATURE_SPEC.anchor_radius_viewbox}`.",
        f"- Raven anchor: `{RAVEN_SPEC.anchor_label}`, SVG center `{list(RAVEN_SPEC.anchor_center_viewbox)}`, radius `{RAVEN_SPEC.anchor_radius_viewbox}`.",
        "- Both sources are scaled uniformly so those source anchors coincide exactly on canvas.",
        "",
        "## Deliverables",
        "",
        "- `anchored_sun_portal_chain_v001.mp4`: 1920x1080, 24 fps, 24 seconds.",
        "- Before/portal/anchor/transition/after stills in `stills/`.",
        "- Peak/after still in `peak_stills/`.",
        "- Anchor debug sheet: `debug_stills/anchored_sun_portal_chain_v001_anchor_debug_sheet.png`.",
        "- Contact sheet: `anchored_artwork_portal_chain_v001_contact_sheet.png`.",
        "- Manifest: `anchored_artwork_portal_chain_v001_manifest.json`.",
        "- Source provenance note: `SOURCE_PROVENANCE.md`.",
        "",
        "## Honest Verdict",
        "",
        "The intended pass condition is not that one artwork atomizes into another. The pass condition is that the viewer can feel a stable sun-disc anchor carry continuity from the 8-fold wave portal into Nature Cosmic Sun, then into Raven Sun. The transition is spatially masked from the shared center/radius outward to avoid a simple slideshow crossfade.",
        "",
        "This remains a technical and aesthetic test. It does not assert that the anchor has cultural meaning, that the transition is culturally correct, or that either artwork is approved for public use. Austin review is required before any external use.",
        "",
        "## Cultural Boundary",
        "",
        "Internal only. Pending Austin review. No public/show/projector use. No cultural-meaning claim.",
        "",
        "Renderer: `scripts/anchored_artwork_portal_chain_v001.py`",
        f"Clip summary: `{clip_summary['filename']}`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render anchored artwork portal chain v001.")
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
    print("Rasterizing Austin source SVGs", flush=True)
    nature = load_artwork_layer(NATURE_SPEC)
    raven = load_artwork_layer(RAVEN_SPEC)
    print("Writing stills and anchor debug sheet", flush=True)
    stills = save_stills(nature, raven)
    debug_path = make_anchor_debug_sheet(nature, raven)
    contact_path = make_contact_sheet(stills, debug_path)

    if args.preview:
        _frame, peak_info = render_frame(AFTER_TIME_SECONDS, nature, raven)
        clip_summary = {
            "filename": "anchored_sun_portal_chain_v001.mp4",
            "mp4": "anchored_sun_portal_chain_v001.mp4",
            "peak_frame": PEAK_FRAME,
            "peak_time_seconds": AFTER_TIME_SECONDS,
            "peak_info": peak_info,
        }
    else:
        print("Rendering anchored_sun_portal_chain_v001.mp4", flush=True)
        clip_summary = render_clip(nature, raven)

    manifest = write_manifest(provenance, nature, raven, clip_summary, stills, debug_path, contact_path, provenance_note)
    readme = write_readme(nature, raven, clip_summary)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
