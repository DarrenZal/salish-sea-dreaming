#!/usr/bin/env python3
"""
Wave to artwork portal v001.

Internal mathematical/visual alignment study for Salish Sea Dreaming. The wave
engine supplies dark water/cymatic atmosphere, radial gathering, and portal
alignment. Austin's authored Nature_Cosmic_Sun.svg supplies the visual content.

This script does not train, diffuse, imitate, synthesize, decompose, or reuse
Austin's shapes as generic primitives. The SVG is rendered as a whole source
artwork, with only uniform scale/position/opacity and temporal portal masking.

Status: INTERNAL ONLY. Not Austin-approved for public use. Not public-use
guidance. Not a cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import cymatic_field_topology_v007 as base
import integrated_choreographer_v004_radial_arc_bounded_peak as radial


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "wave_to_artwork_portal_v001_2026-05-21"
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
FPS = base.FPS
DURATION_SECONDS = 12.0
N_FRAMES = int(FPS * DURATION_SECONDS)
PEAK_TIME_SECONDS = 7.0
PEAK_FRAME = int(PEAK_TIME_SECONDS * FPS)
BEFORE_TIME_SECONDS = 4.5
PORTAL_TIME_SECONDS = PEAK_TIME_SECONDS
AFTER_TIME_SECONDS = 9.2

EXPECTED_SHA256 = "197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1"

DEEP_GROUND = (0, 5, 7)
PORTAL_GLOW = (255, 209, 116)
SOFT_TEAL = (76, 139, 134)
LABEL = (226, 234, 230)

ARTWORK_VIEWBOX_SIZE = 108.0
ARTWORK_CENTER_VIEWBOX = (53.92, 53.86)
ARTWORK_SUN_ORB_RADIUS_VIEWBOX = 34.08
ARTWORK_OUTER_RING_RADIUS_VIEWBOX = 48.26


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


def verify_source_provenance() -> dict[str, object]:
    issues: list[str] = []
    if not SOURCE_SVG.exists():
        issues.append(f"missing source SVG: {SOURCE_SVG}")
    if not APPROVED_COPY.exists():
        issues.append(f"missing approved-ingest copy: {APPROVED_COPY}")
    if not PROVENANCE_CSV.exists():
        issues.append(f"missing provenance CSV: {PROVENANCE_CSV}")
    if not TRIAGE_JSON.exists():
        issues.append(f"missing triage metadata: {TRIAGE_JSON}")
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
        "public_approval_status": "pending; internal-only use permitted by this packet boundary, public use blocked until Austin review",
    }


def write_source_provenance_note(provenance: dict[str, object]) -> Path:
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
        f"- Provenance status: `{(provenance.get('provenance_row') or {}).get('austin_consent', 'unknown') if isinstance(provenance.get('provenance_row'), dict) else 'unknown'}`",
        f"- Triage recommendation: `{(provenance.get('triage_row') or {}).get('recommendation', 'unknown') if isinstance(provenance.get('triage_row'), dict) else 'unknown'}`",
        "",
        "## Boundary",
        "",
        "Internal-only portal study. Public/projector/social use remains blocked until Austin reviews and approves the specific output.",
    ]
    path = OUT_DIR / "SOURCE_PROVENANCE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def rasterize_source_svg(scale_px: int) -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    raster_path = SOURCE_DIR / "Nature_Cosmic_Sun_author_source_rgba.png"
    copied_svg = SOURCE_DIR / "Nature_Cosmic_Sun.svg"
    if not copied_svg.exists() or sha256(copied_svg) != sha256(SOURCE_SVG):
        shutil.copy2(SOURCE_SVG, copied_svg)

    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("ImageMagick `magick` is required to rasterize the source SVG for this portal render.")
    subprocess.run(
        [
            magick,
            "-background",
            "none",
            str(SOURCE_SVG),
            "-resize",
            f"{scale_px}x{scale_px}",
            f"PNG32:{raster_path}",
        ],
        check=True,
    )
    return raster_path


def load_artwork_layer() -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    art_scale = radial.TARGET.wavelength / ARTWORK_SUN_ORB_RADIUS_VIEWBOX
    art_size = round(ARTWORK_VIEWBOX_SIZE * art_scale)
    raster_path = rasterize_source_svg(art_size)
    rgba = cv2.imread(str(raster_path), cv2.IMREAD_UNCHANGED)
    if rgba is None:
        raise RuntimeError(f"could not read rasterized SVG: {raster_path}")
    if rgba.shape[2] == 3:
        alpha = np.full(rgba.shape[:2], 255, dtype=np.uint8)
        bgr = rgba
    else:
        bgr = rgba[:, :, :3]
        alpha = rgba[:, :, 3]

    center_x = W * 0.5
    center_y = H * 0.5
    art_center_x = ARTWORK_CENTER_VIEWBOX[0] / ARTWORK_VIEWBOX_SIZE * art_size
    art_center_y = ARTWORK_CENTER_VIEWBOX[1] / ARTWORK_VIEWBOX_SIZE * art_size
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
        raise RuntimeError("artwork layer does not intersect canvas")
    canvas[dy0:dy1, dx0:dx1] = bgr[sy0:sy1, sx0:sx1]
    canvas_alpha[dy0:dy1, dx0:dx1] = alpha[sy0:sy1, sx0:sx1]

    info = {
        "raster_path": str(raster_path),
        "art_scale_px_per_svg_unit": art_scale,
        "art_raster_size_px": [int(bgr.shape[1]), int(bgr.shape[0])],
        "art_bbox_px": [int(dx0), int(dy0), int(dx1), int(dy1)],
        "art_center_px": [round(center_x, 3), round(center_y, 3)],
        "alignment": {
            "svg_center": list(ARTWORK_CENTER_VIEWBOX),
            "canvas_center": [round(center_x, 3), round(center_y, 3)],
            "svg_sun_orb_radius": ARTWORK_SUN_ORB_RADIUS_VIEWBOX,
            "wave_spacing_radius_px": radial.TARGET.wavelength,
            "svg_outer_ring_radius_px": round(ARTWORK_OUTER_RING_RADIUS_VIEWBOX * art_scale, 3),
        },
    }
    return canvas, canvas_alpha, info


def time_levels(time_seconds: float, coherence: float) -> dict[str, float]:
    gather = smoothstep01((time_seconds - 3.0) / 2.0)
    portal_in = smoothstep01((time_seconds - 5.0) / 1.35)
    portal_out = 1.0 - smoothstep01((time_seconds - 8.0) / 2.0)
    portal = clamp01(portal_in * portal_out)
    portal_full = smoothstep01((time_seconds - 5.45) / 1.65) * portal_out
    artwork = smoothstep01((time_seconds - 5.18) / 1.18) * portal_out
    return {
        "gather": gather,
        "portal": portal,
        "portal_full": clamp01(portal_full),
        "artwork": clamp01(artwork),
        "coherence": coherence,
    }


def soft_mask(mask: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    return cv2.GaussianBlur(mask, (0, 0), sigma)


def portal_masks(time_seconds: float, artwork_alpha: np.ndarray, geometry: dict[str, object], levels: dict[str, float]) -> dict[str, np.ndarray]:
    seed = radial.v003.mask_union(geometry["center_mask"], *geometry["crescent_masks"])
    seed = cv2.dilate(seed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)), iterations=1)
    seed_soft = soft_mask(seed, 6.0)
    art_soft = soft_mask(artwork_alpha, 1.2)
    expand = levels["portal_full"]
    full_region = artwork_alpha > 4
    seed_region = seed > 4
    distance_from_seed = cv2.distanceTransform((~seed_region).astype(np.uint8), cv2.DIST_L2, 5)
    max_distance = float(distance_from_seed[full_region].max()) if np.any(full_region) else 1.0
    growth_radius = 32.0 + expand * max_distance
    soft_edge = 52.0
    growth = np.clip(1.0 - ((distance_from_seed - growth_radius) / soft_edge), 0.0, 1.0)
    growth[~full_region] = 0.0
    growth = cv2.GaussianBlur(growth.astype(np.float32), (0, 0), 1.6)
    aperture = np.maximum(seed_soft.astype(np.float32) * (1.0 - 0.25 * expand), art_soft.astype(np.float32) * growth)
    aperture = np.clip(aperture, 0, 255).astype(np.uint8)
    return {
        "seed": seed,
        "seed_soft": seed_soft,
        "growth": np.clip(growth * 255.0, 0, 255).astype(np.uint8),
        "artwork_alpha": artwork_alpha,
        "aperture": aperture,
    }


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


def blend_mask_rgb(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float) -> None:
    radial.blend_full_mask(frame, mask, rgb, alpha)


def render_frame(
    time_seconds: float,
    artwork_bgr: np.ndarray,
    artwork_alpha: np.ndarray,
    *,
    force_coherence: float | None = None,
    labels: bool = False,
) -> tuple[np.ndarray, dict[str, object]]:
    coherence = radial.coherence_at_time(time_seconds) if force_coherence is None else force_coherence
    sources = radial.v003.target_sources_at(radial.TARGET, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=radial.TARGET.blur_sigma)
    levels = time_levels(time_seconds, coherence)
    radial_levels = radial.layer_levels(time_seconds, coherence)

    wave_alpha = radial_levels["wave_regions"] * (1.0 - 0.78 * levels["artwork"])
    line_alpha = radial_levels["wave_lines"] * (1.0 - 0.55 * levels["artwork"])
    frame = radial.render_dark_wave_field(field, radial.TARGET, region_alpha=wave_alpha, line_alpha=line_alpha)
    geometry = radial.build_peak_geometry(radial.TARGET, sources)
    masks = portal_masks(time_seconds, artwork_alpha, geometry, levels)

    radial.draw_subtle_nodal_lines(frame, field, radial.TARGET, alpha=0.50 * line_alpha)
    radial.draw_reveal_scaffold(frame, geometry, radial_levels["construction"] * (1.0 - levels["artwork"]))
    radial.draw_outer_registration(frame, geometry, radial_levels["outer_registration"] * (1.0 - 0.30 * levels["artwork"]))

    # The v004 selected regions become the portal aperture. They fade before
    # the authored artwork becomes fully readable.
    radial.draw_selected_regions(
        frame,
        geometry,
        alpha=radial_levels["selected_regions"] * (1.0 - 0.72 * levels["artwork"]),
        primary_rgb=radial.CREAM,
    )
    blend_mask_rgb(frame, masks["seed"], PORTAL_GLOW, 0.08 * levels["portal"] * (1.0 - levels["artwork"]))
    blend_mask_rgb(frame, masks["aperture"], PORTAL_GLOW, 0.07 * levels["portal"] * (1.0 - 0.60 * levels["artwork"]))

    art_alpha = np.minimum(artwork_alpha, masks["aperture"])
    alpha_over(frame, artwork_bgr, art_alpha, levels["artwork"])

    if labels:
        base.draw_text(frame, f"wave-to-authored-artwork portal v001  c={coherence:.2f}", (42, 58), LABEL, scale=0.54)
        base.draw_text(frame, "source artwork is whole Nature_Cosmic_Sun.svg; wave geometry supplies aperture only", (42, 88), LABEL, scale=0.36)
    return frame, {
        "time_seconds": round(time_seconds, 4),
        "coherence": round(coherence, 4),
        "levels": {key: round(value, 4) for key, value in levels.items()},
        "radial_levels": {key: round(value, 4) for key, value in radial_levels.items()},
        "source_positions": [
            {"source_id": source.source_id, "x": round(source.x, 3), "y": round(source.y, 3)}
            for source in sources
        ],
        "portal": {
            "seed_mask_nonzero": int(np.count_nonzero(masks["seed"] > 9)),
            "aperture_nonzero": int(np.count_nonzero(masks["aperture"] > 9)),
            "artwork_alpha_nonzero": int(np.count_nonzero(artwork_alpha > 9)),
        },
    }


def make_alignment_debug_still(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray, artwork_info: dict[str, object]) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    time_seconds = PEAK_TIME_SECONDS
    coherence = 1.0
    sources = radial.v003.target_sources_at(radial.TARGET, time_seconds, coherence)
    field = base.evaluate_field(sources, time_seconds, blur_sigma=radial.TARGET.blur_sigma)
    geometry = radial.build_peak_geometry(radial.TARGET, sources)
    levels = time_levels(time_seconds, coherence)
    masks = portal_masks(time_seconds, artwork_alpha, geometry, levels)

    wave = radial.render_dark_wave_field(field, radial.TARGET, region_alpha=0.34, line_alpha=0.34)
    radial.draw_reveal_scaffold(wave, geometry, 0.45)
    radial.draw_selected_regions(wave, geometry, alpha=0.55, primary_rgb=radial.CREAM)

    mask_panel = np.zeros((H, W, 3), dtype=np.uint8)
    blend_mask_rgb(mask_panel, masks["artwork_alpha"], SOFT_TEAL, 0.42)
    blend_mask_rgb(mask_panel, masks["seed"], PORTAL_GLOW, 0.82)
    radial.draw_outer_registration(mask_panel, geometry, 0.50)

    final, _ = render_frame(time_seconds, artwork_bgr, artwork_alpha, force_coherence=1.0, labels=False)
    debug = final.copy()
    x0, y0, x1, y1 = [int(v) for v in artwork_info["art_bbox_px"]]
    cv2.rectangle(debug, (x0, y0), (x1, y1), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)
    cx, cy = [int(round(v)) for v in artwork_info["art_center_px"]]
    cv2.drawMarker(debug, (cx, cy), rgb_to_bgr(PORTAL_GLOW), markerType=cv2.MARKER_CROSS, markerSize=28, thickness=2, line_type=cv2.LINE_AA)

    panels = [
        cv2.resize(wave, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(mask_panel, (640, 360), interpolation=cv2.INTER_AREA),
        cv2.resize(debug, (640, 360), interpolation=cv2.INTER_AREA),
    ]
    labels = ["wave geometry + selected portal forms", "portal masks: seed + authored artwork alpha", "final alignment: bbox + shared center"]
    for panel, label in zip(panels, labels, strict=True):
        base.draw_text(panel, label, (18, 36), LABEL, scale=0.36)
    sheet = cv2.hconcat(panels)
    path = DEBUG_DIR / "wave_to_cosmic_sun_portal_v001_alignment_debug.png"
    cv2.imwrite(str(path), sheet)
    return path


def save_stills(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, t in (
        ("before", BEFORE_TIME_SECONDS),
        ("portal", PORTAL_TIME_SECONDS),
        ("after", AFTER_TIME_SECONDS),
    ):
        frame, _info = render_frame(t, artwork_bgr, artwork_alpha, force_coherence=radial.coherence_at_time(t), labels=False)
        path = STILLS_DIR / f"wave_to_cosmic_sun_portal_v001_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[f"{key}_still"] = str(path.relative_to(OUT_DIR))
    peak_path = PEAK_DIR / "wave_to_cosmic_sun_portal_v001_peak.png"
    peak_frame, _ = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0, labels=False)
    cv2.imwrite(str(peak_path), peak_frame)
    outputs["peak_still"] = str(peak_path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(stills: dict[str, str], debug_path: Path) -> Path:
    panels: list[np.ndarray] = []
    for key, label in (
        ("before_still", "before gather/portal"),
        ("portal_still", "portal peak"),
        ("after_still", "after release"),
    ):
        img = cv2.imread(str(OUT_DIR / stills[key]), cv2.IMREAD_COLOR)
        if img is None:
            img = np.zeros((H, W, 3), dtype=np.uint8)
        panel = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (18, 36), LABEL, scale=0.40)
        panels.append(panel)
    row1 = cv2.hconcat(panels)
    debug = cv2.imread(str(debug_path), cv2.IMREAD_COLOR)
    if debug is None:
        debug = np.zeros((360, 1920, 3), dtype=np.uint8)
    row2 = cv2.resize(debug, (1920, 360), interpolation=cv2.INTER_AREA)
    sheet = cv2.vconcat([row1, row2])
    path = OUT_DIR / "wave_to_artwork_portal_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip(artwork_bgr: np.ndarray, artwork_alpha: np.ndarray) -> dict[str, object]:
    output_path = OUT_DIR / "wave_to_cosmic_sun_portal_v001.mp4"
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
                print(f"  wave_to_cosmic_sun_portal_v001.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0)
    return {
        "filename": "wave_to_cosmic_sun_portal_v001.mp4",
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
    contact_path: Path,
    provenance_note: Path,
) -> Path:
    manifest = {
        "project": "wave_to_artwork_portal_v001",
        "status": "INTERNAL ONLY; not Austin-approved for public use; no cultural-meaning claim",
        "renderer": "scripts/wave_to_artwork_portal_v001.py",
        "output_dir": str(OUT_DIR),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frames_per_clip": N_FRAMES,
        "concept": "wave-to-authored-artwork portal study pending Austin review",
        "rules": {
            "training": False,
            "diffusion": False,
            "style_imitation": False,
            "source_shape_fragment_reuse": False,
            "source_artwork_geometry_changes": "uniform scale/position/opacity/temporal masking only",
        },
        "source_provenance": provenance,
        "artwork_alignment": artwork_info,
        "clip": clip_summary,
        "deliverables": {
            "mp4": clip_summary["mp4"],
            "peak_still": stills["peak_still"],
            "before_still": stills["before_still"],
            "portal_still": stills["portal_still"],
            "after_still": stills["after_still"],
            "alignment_debug_still": str(debug_path.relative_to(OUT_DIR)),
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "source_provenance_note": str(provenance_note.relative_to(OUT_DIR)),
            "readme": "README.md",
        },
    }
    path = OUT_DIR / "wave_to_artwork_portal_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_readme(clip_summary: dict[str, object], artwork_info: dict[str, object]) -> Path:
    lines = [
        "# Wave To Artwork Portal v001",
        "",
        "Status: INTERNAL ONLY. Not Austin-approved for public use. Not public-use guidance. No cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet tests a wave-to-authored-artwork portal study pending Austin review. The wave/choreographer engine provides dark water/cymatic atmosphere, radial gathering, and explicit geometric alignment. Austin's actual authored `Nature_Cosmic_Sun.svg` provides the visual content.",
        "",
        "The render does not train, diffuse, imitate, synthesize, decompose, or reuse Austin's individual shapes as generic primitives. The source SVG is rasterized as a whole artwork and revealed by uniform scale, position, opacity, and temporal portal masking only.",
        "",
        "## Provenance",
        "",
        "- Source SVG: `track2-deterministic/source-vectors/Nature_Cosmic_Sun.svg`.",
        "- SHA256: `197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1`.",
        "- Matches `austin-v2-ingest/approved/Nature_Cosmic_Sun.svg` and the fresh Google Drive mirror.",
        "- Existing provenance records mark Austin consent as `pending`; this packet is therefore internal-only and public-blocked until Austin reviews the specific output.",
        "- Full provenance note: `SOURCE_PROVENANCE.md`.",
        "",
        "## Timing",
        "",
        "- 0.0-3.0s: loose dark water/cymatic field.",
        "- 3.0-5.0s: radial geometry gathers; center and sixfold rhythm become visible.",
        "- 5.0-8.0s: portal moment; wave-derived masks open into the whole authored SVG.",
        "- 8.0-10.0s: artwork recedes back into wave geometry.",
        "- 10.0-12.0s: drifting field returns.",
        "",
        "## Alignment",
        "",
        f"- Artwork center aligned to canvas/wave center: `{artwork_info['art_center_px']}`.",
        f"- SVG sun orb radius `{ARTWORK_SUN_ORB_RADIUS_VIEWBOX}` maps to wave source spacing `{radial.TARGET.wavelength}` px.",
        f"- Artwork bbox at render scale: `{artwork_info['art_bbox_px']}`.",
        "",
        "## Deliverables",
        "",
        "- `wave_to_cosmic_sun_portal_v001.mp4`: 1920x1080, 24 fps, 12 seconds.",
        "- Peak still: `peak_stills/wave_to_cosmic_sun_portal_v001_peak.png`.",
        "- Before/portal/after stills in `stills/`.",
        "- Alignment debug still: `debug_stills/wave_to_cosmic_sun_portal_v001_alignment_debug.png`.",
        "- Contact sheet: `wave_to_artwork_portal_v001_contact_sheet.png`.",
        "- Manifest: `wave_to_artwork_portal_v001_manifest.json`.",
        "- Source provenance note: `SOURCE_PROVENANCE.md`.",
        "",
        "## Honest Verdict",
        "",
        "The intended read is not a generated Coast Salish-style image. The strongest moment is when the v004 radial aperture stops behaving like a separate constructed motif and becomes a reveal path for the whole Nature_Cosmic_Sun source artwork. At peak, the wave layer is intentionally dimmed so it does not compete with the authored artwork.",
        "",
        "Limitations: the transition is still a technical portal test. The artwork is being revealed with a mask over a water-field base, so it should be reviewed for whether it feels like a meaningful alignment or just an overlay. This packet makes no cultural claim and should be shown only as an internal review candidate.",
        "",
        "## Cultural Boundary",
        "",
        "Internal only. Not Austin-approved for public use. No cultural-meaning claim. Nothing here authorizes projector, social, sponsor, or press use without Austin's review of this specific output.",
        "",
        "Renderer: `scripts/wave_to_artwork_portal_v001.py`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wave-to-authored-artwork portal v001.")
    parser.add_argument("--preview", action="store_true", help="Write still/debug artifacts without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    provenance = verify_source_provenance()
    if not provenance["ok"]:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
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
    print("Writing stills and debug artifacts", flush=True)
    stills = save_stills(artwork_bgr, artwork_alpha)
    debug_path = make_alignment_debug_still(artwork_bgr, artwork_alpha, artwork_info)
    contact_path = make_contact_sheet(stills, debug_path)

    if args.preview:
        _frame, peak_info = render_frame(PEAK_TIME_SECONDS, artwork_bgr, artwork_alpha, force_coherence=1.0)
        clip_summary = {
            "filename": "wave_to_cosmic_sun_portal_v001.mp4",
            "mp4": "wave_to_cosmic_sun_portal_v001.mp4",
            "peak_frame": PEAK_FRAME,
            "peak_time_seconds": PEAK_TIME_SECONDS,
            "peak_info": peak_info,
        }
    else:
        print("Rendering wave_to_cosmic_sun_portal_v001.mp4", flush=True)
        clip_summary = render_clip(artwork_bgr, artwork_alpha)

    manifest = write_manifest(provenance, artwork_info, clip_summary, stills, debug_path, contact_path, provenance_note)
    readme = write_readme(clip_summary, artwork_info)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
