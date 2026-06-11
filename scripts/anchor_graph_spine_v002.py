#!/usr/bin/env python3
"""
Anchor graph spine v002.

Internal composition pass for Salish Sea Dreaming. This renderer composes the
validated anchor-graph pieces into one continuous passage:

wave atmosphere -> Nature Cosmic Sun portal -> shared sun-disc anchor ->
Raven Sun spatial reveal -> Raven clean-frame spatial hold -> return to
wave/water atmosphere.

Austin source SVGs are rasterized as whole authored artworks. Anchor records
are read as alignment metadata only: center, radius, masks, axes, and timing.
The renderer does not train, diffuse, imitate, synthesize, decompose, recolor,
or extract motifs from the source artworks.

Status: INTERNAL ONLY. Pending Austin review. Not approved for public, show,
projector, sponsor, social, press, or external use. No cultural-meaning claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
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
    / "anchor_graph_spine_v002_2026-05-21"
)
STILLS_DIR = OUT_DIR / "stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
SOURCE_DIR = OUT_DIR / "source_assets"

REGISTRY_PATH = ROOT / "track2-deterministic" / "anchor_graph" / "austin_anchor_registry_v001.json"
ARCHITECTURE_DOC = ROOT / "docs" / "space-center" / "installation-anchor-graph-architecture-2026-05-21.md"
REVIEW_PACKET_DOC = ROOT / "docs" / "space-center" / "austin-architectural-review-packet-draft-2026-05-21.md"
REGISTRY_NOTES_DOC = ROOT / "docs" / "space-center" / "austin-anchor-registry-notes-2026-05-21.md"
V002_README = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "wave_to_artwork_portal_v002_2026-05-21"
    / "README.md"
)
CHAIN_README = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "anchored_artwork_portal_chain_v001_2026-05-21"
    / "README.md"
)
RAVEN_3D_README = ROOT / "track2-deterministic" / "probes" / "3d-extrusion-2026-05-21" / "README.md"
RAVEN_SPATIAL_NODE_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "raven_sun_spatial_node_v002_2026-05-21"
)
RAVEN_SPATIAL_README = RAVEN_SPATIAL_NODE_DIR / "README.md"
RAVEN_SPATIAL_MANIFEST = RAVEN_SPATIAL_NODE_DIR / "manifest.json"
RAVEN_SPATIAL_FRAMES_DIR = RAVEN_SPATIAL_NODE_DIR / "frames" / "clean_frame"
RAVEN_SPATIAL_MP4 = RAVEN_SPATIAL_NODE_DIR / "out" / "raven_sun_spatial_node_v002_clean_frame.mp4"
WAVE_SCRIPT = ROOT / "scripts" / "wave_to_artwork_portal_v002.py"
CHAIN_SCRIPT = ROOT / "scripts" / "anchored_artwork_portal_chain_v001.py"

W = base.W
H = base.H
FPS = base.FPS
DURATION_SECONDS = 60.0
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

ANCHOR_CENTER_PX = (W * 0.5, H * 0.5)
ANCHOR_RADIUS_PX = 276.0
ARTWORK_HIGH_RES_FACTOR = 4
VIEWBOX_SIZE = 108.0

NATURE_SHA256 = "197c922ed7c2fe924630503ce0c01c4e6b721befb19c5e7f625a6a197bd2b7f1"
RAVEN_SHA256 = "5fa0ceaea6a49cc4c1408434541dc3a69e89d935fd96740606a4f1787c92c766"

DEEP_GROUND = (0, 5, 7)
MUTED_TEAL = (69, 119, 120)
PORTAL_GLOW = (255, 215, 130)
PORTAL_ORANGE = (218, 96, 39)
SOFT_GOLD = (246, 195, 91)
LABEL = (226, 234, 230)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
DIST_FROM_ANCHOR = np.sqrt((XX - ANCHOR_CENTER_PX[0]) ** 2 + (YY - ANCHOR_CENTER_PX[1]) ** 2)
FAST_FW = max(240, base.FW // 2)
FAST_FH = max(135, base.FH // 2)
FAST_SX = W / FAST_FW
FAST_SY = H / FAST_FH
FAST_GRID_X = ((np.arange(FAST_FW, dtype=np.float32) + 0.5) * FAST_SX)[None, :]
FAST_GRID_Y = ((np.arange(FAST_FH, dtype=np.float32) + 0.5) * FAST_SY)[:, None]
FAST_EDGE_WINDOW = cv2.resize(base.EDGE_WINDOW, (FAST_FW, FAST_FH), interpolation=cv2.INTER_AREA).astype(np.float32)
FAST_FIELD_BOUNDARY = cv2.resize(wave_v002.FIELD_BOUNDARY_FULL, (FAST_FW, FAST_FH), interpolation=cv2.INTER_AREA)
FIELD_BOUNDARY_EDGE_FULL = cv2.morphologyEx(
    wave_v002.FIELD_BOUNDARY_FULL,
    cv2.MORPH_GRADIENT,
    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
)

RAVEN_SPATIAL_BG_BGR = np.array([12, 6, 8], dtype=np.uint8)
RAVEN_SPATIAL_TOTAL_FRAMES = 288
RAVEN_SPATIAL_LAYER_SIZE = 2.4
RAVEN_SPATIAL_BACK_Z = -0.35
RAVEN_SPATIAL_CAM_Z_START = 3.2
RAVEN_SPATIAL_CAM_Z_END = 2.2
RAVEN_SPATIAL_YAW_DEG = 5.0
RAVEN_SPATIAL_PITCH_DEG = 2.0
RAVEN_SPATIAL_LATERAL = 0.10
RAVEN_SPATIAL_VERTICAL = 0.05
RAVEN_SPATIAL_FOCAL = 1.6
RAVEN_SPATIAL_RASTER_SIZE = 2160.0


@dataclass(frozen=True)
class ArtworkSpec:
    key: str
    title: str
    filename: str
    source_path: Path
    expected_sha256: str
    anchor_id: str
    anchor_type: str
    anchor_center_viewbox: tuple[float, float]
    anchor_radius_viewbox: float
    edge_suitability: dict[str, str]


@dataclass(frozen=True)
class ArtworkLayer:
    spec: ArtworkSpec
    bgr: np.ndarray
    alpha: np.ndarray
    soft_alpha: np.ndarray
    info: dict[str, object]


NATURE_SPEC = ArtworkSpec(
    key="nature_cosmic_sun",
    title="Nature Cosmic Sun",
    filename="Nature_Cosmic_Sun.svg",
    source_path=ROOT / "track2-deterministic" / "source-vectors" / "Nature_Cosmic_Sun.svg",
    expected_sha256=NATURE_SHA256,
    anchor_id="nature_cosmic_sun.central_sun_disc",
    anchor_type="central_sun_disc",
    anchor_center_viewbox=(53.92, 53.86),
    anchor_radius_viewbox=34.08,
    edge_suitability={
        "wave_to_artwork": "strong validated internal target",
        "artwork_to_artwork": "strong shared sun-disc anchor",
        "artwork_to_spatial": "weak current parallax target",
    },
)

RAVEN_SPEC = ArtworkSpec(
    key="animal_bird_raven_sun",
    title="Animal Bird Raven Sun",
    filename="Animal_Bird_Raven_Sun.svg",
    source_path=ROOT / "track2-deterministic" / "source-vectors" / "Animal_Bird_Raven_Sun.svg",
    expected_sha256=RAVEN_SHA256,
    anchor_id="animal_bird_raven_sun.central_sun_disc",
    anchor_type="central_sun_disc",
    anchor_center_viewbox=(54.0, 53.51),
    anchor_radius_viewbox=28.15,
    edge_suitability={
        "artwork_to_artwork": "strong shared sun-disc anchor",
        "artwork_to_spatial": "strong figure-on-field 2.5D candidate",
        "wave_to_artwork": "medium future candidate pending test",
    },
)

ARTWORK_SPECS = (NATURE_SPEC, RAVEN_SPEC)
REQUIRED_CONTEXT = (
    ARCHITECTURE_DOC,
    REVIEW_PACKET_DOC,
    REGISTRY_PATH,
    REGISTRY_NOTES_DOC,
    V002_README,
    CHAIN_README,
    RAVEN_3D_README,
    RAVEN_SPATIAL_README,
    RAVEN_SPATIAL_MANIFEST,
    RAVEN_SPATIAL_MP4,
    WAVE_SCRIPT,
    CHAIN_SCRIPT,
    NATURE_SPEC.source_path,
    RAVEN_SPEC.source_path,
)

KEY_STILL_TIMES = (
    ("wave_gather", 6.0),
    ("nature_portal", 12.5),
    ("nature_hold", 19.0),
    ("shared_anchor", 28.0),
    ("raven_transition", 38.0),
    ("raven_hold", 48.0),
    ("return", 57.0),
)

CONTACT_TIMES = (0.0, 6.0, 10.5, 12.8, 18.0, 26.0, 31.5, 36.0, 41.5, 48.0, 55.0, 59.5)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def smoothstep01(value: float) -> float:
    t = clamp01(value)
    return t * t * (3.0 - 2.0 * t)


def rgb_to_bgr(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return (rgb[2], rgb[1], rgb[0])


def spatial_camera_at(t_norm: float) -> dict[str, object]:
    ease = 0.5 - 0.5 * math.cos(math.pi * clamp01(t_norm))
    cam_z = RAVEN_SPATIAL_CAM_Z_START + (RAVEN_SPATIAL_CAM_Z_END - RAVEN_SPATIAL_CAM_Z_START) * ease
    yaw = math.radians(RAVEN_SPATIAL_YAW_DEG) * math.sin(TAU * t_norm)
    pitch = math.radians(RAVEN_SPATIAL_PITCH_DEG) * math.sin(TAU * t_norm + math.pi / 2.0)
    lateral = RAVEN_SPATIAL_LATERAL * math.sin(TAU * t_norm + math.pi / 4.0)
    vertical = RAVEN_SPATIAL_VERTICAL * math.sin(TAU * t_norm)
    return {
        "pos": (lateral, vertical, cam_z),
        "focal": RAVEN_SPATIAL_FOCAL,
        "yaw": yaw,
        "pitch": pitch,
    }


def spatial_project(point_world: tuple[float, float, float], camera: dict[str, object]) -> tuple[float, float]:
    x, y, z = point_world
    cx, cy, cz = camera["pos"]
    x_c, y_c, z_c = x - cx, y - cy, z - cz

    cos_y, sin_y = math.cos(camera["yaw"]), math.sin(camera["yaw"])
    x_r = cos_y * x_c + sin_y * z_c
    z_r = -sin_y * x_c + cos_y * z_c

    cos_p, sin_p = math.cos(camera["pitch"]), math.sin(camera["pitch"])
    y_r2 = cos_p * y_c - sin_p * z_r
    z_r2 = sin_p * y_c + cos_p * z_r
    if z_r2 >= -1e-4:
        z_r2 = -1e-4

    px_ndc = (RAVEN_SPATIAL_FOCAL * x_r) / -z_r2
    py_ndc = (RAVEN_SPATIAL_FOCAL * y_r2) / -z_r2
    return W * 0.5 + px_ndc * (H * 0.5), H * 0.5 - py_ndc * (H * 0.5)


def spatial_source_to_world(
    source_x_viewbox: float,
    source_y_viewbox: float,
    *,
    layer_z: float = RAVEN_SPATIAL_BACK_Z,
) -> tuple[float, float, float]:
    x_norm = source_x_viewbox / VIEWBOX_SIZE
    y_norm = source_y_viewbox / VIEWBOX_SIZE
    x_world = (x_norm - 0.5) * RAVEN_SPATIAL_LAYER_SIZE
    y_world = (0.5 - y_norm) * RAVEN_SPATIAL_LAYER_SIZE
    return (x_world, y_world, layer_z)


def raven_spatial_node_norm(time_seconds: float) -> float:
    if time_seconds < 32.0:
        return 0.42
    if time_seconds < 44.0:
        t = smoothstep01((time_seconds - 32.0) / 12.0)
        return 0.42 + 0.44 * t
    if time_seconds < 54.0:
        t = smoothstep01((time_seconds - 44.0) / 10.0)
        return 0.86 + 0.08 * t + 0.018 * math.sin(TAU * t)
    t = smoothstep01((time_seconds - 54.0) / 6.0)
    return 0.94 + 0.05 * t


def raven_spatial_anchor_projection(t_norm: float) -> tuple[tuple[float, float], float]:
    camera = spatial_camera_at(t_norm)
    center_world = spatial_source_to_world(*RAVEN_SPEC.anchor_center_viewbox)
    rim_world = spatial_source_to_world(
        RAVEN_SPEC.anchor_center_viewbox[0] + RAVEN_SPEC.anchor_radius_viewbox,
        RAVEN_SPEC.anchor_center_viewbox[1],
    )
    center_px = spatial_project(center_world, camera)
    rim_px = spatial_project(rim_world, camera)
    radius_px = math.hypot(rim_px[0] - center_px[0], rim_px[1] - center_px[1])
    return center_px, radius_px


def raven_spatial_target_radius(time_seconds: float) -> float:
    if time_seconds < 44.0:
        return ANCHOR_RADIUS_PX
    if time_seconds < 48.0:
        t = smoothstep01((time_seconds - 44.0) / 4.0)
        return ANCHOR_RADIUS_PX * (1.0 - t) + 246.0 * t
    if time_seconds < 54.0:
        return 246.0
    t = smoothstep01((time_seconds - 54.0) / 6.0)
    return 246.0 * (1.0 - t) + ANCHOR_RADIUS_PX * t


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def centered_circle_mask(radius: float, *, soft_edge: float = 0.0) -> np.ndarray:
    if soft_edge <= 0.0:
        return np.where(DIST_FROM_ANCHOR <= radius, 255, 0).astype(np.uint8)
    alpha = np.clip((radius + soft_edge - DIST_FROM_ANCHOR) / max(1e-6, soft_edge), 0.0, 1.0)
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


def centered_ring_mask(radius: float, *, thickness: float = 4.0, blur: float = 2.4) -> np.ndarray:
    half = thickness * 0.5
    ring = np.where(
        (DIST_FROM_ANCHOR >= radius - half) & (DIST_FROM_ANCHOR <= radius + half),
        255,
        0,
    ).astype(np.uint8)
    if blur > 0:
        ring = cv2.GaussianBlur(ring, (0, 0), blur)
    return ring


ANCHOR_MASK = centered_circle_mask(ANCHOR_RADIUS_PX, soft_edge=18.0)
NATURE_RADIAL_HOLD_MASK = None


def mask_edge(mask: np.ndarray, *, kernel_px: int = 9, blur: float = 4.2) -> np.ndarray:
    source = np.where(mask > 12, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(
        source,
        cv2.MORPH_GRADIENT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_px, kernel_px)),
    )
    return cv2.GaussianBlur(edge, (0, 0), blur)


def soft_artwork_alpha(alpha: np.ndarray, bbox: tuple[int, int, int, int], feather_px: float) -> np.ndarray:
    x0, y0, x1, y1 = bbox
    dx = np.minimum(XX - x0, x1 - XX)
    dy = np.minimum(YY - y0, y1 - YY)
    edge = np.minimum(dx, dy)
    feather = np.clip(edge / max(1e-6, feather_px), 0.0, 1.0)
    feather = feather * feather * (3.0 - 2.0 * feather)
    return np.clip(alpha.astype(np.float32) * feather, 0, 255).astype(np.uint8)


def load_registry_anchors() -> dict[str, dict[str, object]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    anchors = {
        anchor.get("anchor_id"): anchor
        for anchor in registry.get("anchors", [])
        if isinstance(anchor, dict)
    }
    required = (
        "nature_cosmic_sun.central_sun_disc",
        "nature_cosmic_sun.eight_ray_radial_aperture_structure",
        "animal_bird_raven_sun.central_sun_disc",
    )
    missing = [anchor_id for anchor_id in required if anchor_id not in anchors]
    if missing:
        raise RuntimeError(f"required registry anchors missing: {missing}")
    for anchor_id in required:
        anchor = anchors[anchor_id]
        if anchor.get("asset_type") != "alignment_metadata_only":
            raise RuntimeError(f"{anchor_id} is not marked alignment_metadata_only")
        if anchor.get("is_renderable_primitive") is not False:
            raise RuntimeError(f"{anchor_id} is not marked is_renderable_primitive=false")
        if anchor.get("may_extract_as_motif") is not False:
            raise RuntimeError(f"{anchor_id} is not marked may_extract_as_motif=false")
    return {anchor_id: anchors[anchor_id] for anchor_id in required}


def verify_inputs() -> dict[str, object]:
    issues: list[str] = []
    for path in REQUIRED_CONTEXT:
        if not path.exists():
            issues.append(f"missing required input: {path}")
    source_hashes: dict[str, str] = {}
    for spec in ARTWORK_SPECS:
        if spec.source_path.exists():
            digest = sha256(spec.source_path)
            source_hashes[spec.key] = digest
            if digest != spec.expected_sha256:
                issues.append(f"{spec.filename} SHA mismatch: {digest}")
    if issues:
        return {"ok": False, "issues": issues, "source_hashes": source_hashes}
    anchors = load_registry_anchors()
    return {
        "ok": True,
        "issues": [],
        "source_hashes": source_hashes,
        "registry_sha256": sha256(REGISTRY_PATH),
        "anchors": anchors,
        "context_docs": [str(path.relative_to(ROOT)) for path in REQUIRED_CONTEXT if path.suffix in {".md", ".json"}],
    }


def rasterize_svg(spec: ArtworkSpec, display_size_px: int) -> tuple[Path, Path]:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    high_size = display_size_px * ARTWORK_HIGH_RES_FACTOR
    stem = Path(spec.filename).stem
    high_path = SOURCE_DIR / f"{stem}_author_source_highres_rgba.png"
    display_path = SOURCE_DIR / f"{stem}_author_source_display_rgba.png"
    magick = shutil.which("magick")
    if magick is None:
        raise RuntimeError("ImageMagick `magick` is required to rasterize source SVGs.")
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


def load_artwork_layer(spec: ArtworkSpec) -> ArtworkLayer:
    scale = ANCHOR_RADIUS_PX / spec.anchor_radius_viewbox
    display_size = round(VIEWBOX_SIZE * scale)
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

    anchor_x = spec.anchor_center_viewbox[0] / VIEWBOX_SIZE * display_size
    anchor_y = spec.anchor_center_viewbox[1] / VIEWBOX_SIZE * display_size
    x0 = round(ANCHOR_CENTER_PX[0] - anchor_x)
    y0 = round(ANCHOR_CENTER_PX[1] - anchor_y)
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
    soft_alpha = soft_artwork_alpha(canvas_alpha, bbox, feather_px=10.0 if spec.key == NATURE_SPEC.key else 22.0)
    info = {
        "artwork_id": spec.key,
        "title": spec.title,
        "filename": spec.filename,
        "source_svg": str(spec.source_path.relative_to(ROOT)),
        "source_sha256": sha256(spec.source_path),
        "high_res_raster": str(high_path.relative_to(OUT_DIR)),
        "display_raster": str(display_path.relative_to(OUT_DIR)),
        "high_res_factor": ARTWORK_HIGH_RES_FACTOR,
        "viewbox_size": VIEWBOX_SIZE,
        "source_anchor_id": spec.anchor_id,
        "source_anchor_type": spec.anchor_type,
        "source_anchor_center_viewbox": list(spec.anchor_center_viewbox),
        "source_anchor_radius_viewbox": spec.anchor_radius_viewbox,
        "canvas_anchor_center_px": list(ANCHOR_CENTER_PX),
        "canvas_anchor_radius_px": ANCHOR_RADIUS_PX,
        "scale_px_per_svg_unit": scale,
        "raster_size_px": [int(bgr.shape[1]), int(bgr.shape[0])],
        "bbox_px": [bbox[0], bbox[1], bbox[2], bbox[3]],
        "edge_suitability": spec.edge_suitability,
    }
    return ArtworkLayer(spec=spec, bgr=canvas, alpha=canvas_alpha, soft_alpha=soft_alpha, info=info)


def spine_coherence(time_seconds: float) -> float:
    if time_seconds < 1.0:
        return 0.0
    if time_seconds < 8.0:
        return smoothstep01((time_seconds - 1.0) / 6.5)
    if time_seconds < 54.0:
        return 1.0
    return 1.0 - 0.62 * smoothstep01((time_seconds - 54.0) / 6.0)


def nature_opacity(time_seconds: float) -> float:
    in_level = smoothstep01((time_seconds - 8.0) / 3.6)
    if time_seconds >= 12.0:
        in_level = max(in_level, 1.0)
    out_level = 1.0 - smoothstep01((time_seconds - 34.0) / 8.0)
    return clamp01(in_level * out_level)


def raven_opacity(time_seconds: float) -> float:
    in_level = smoothstep01((time_seconds - 32.0) / 8.0)
    if time_seconds >= 44.0:
        in_level = 1.0
    out_level = 1.0 - smoothstep01((time_seconds - 54.0) / 6.0)
    return clamp01(in_level * out_level)


def wave_levels(time_seconds: float) -> dict[str, float]:
    n = nature_opacity(time_seconds)
    r = raven_opacity(time_seconds)
    art_dominance = clamp01(max(n * 0.82, r * 0.78))
    return_level = smoothstep01((time_seconds - 54.0) / 5.2)
    gather = smoothstep01((time_seconds - 0.5) / 7.5)
    return {
        "water": clamp01(0.94 - 0.34 * art_dominance + 0.18 * return_level),
        "positive": clamp01(0.88 * (1.0 - 0.82 * art_dominance) + 0.20 * return_level),
        "negative": clamp01(0.78 * (1.0 - 0.50 * art_dominance) + 0.12 * return_level),
        "line": clamp01(0.56 + 0.18 * gather - 0.12 * art_dominance + 0.20 * return_level),
    }


def render_wave_base(time_seconds: float) -> tuple[np.ndarray, list[base.WaveSource]]:
    coherence = spine_coherence(time_seconds)
    sources = wave_v002.target_sources_at(time_seconds, coherence)
    field = fast_evaluate_field(sources, time_seconds, blur_sigma=wave_v002.BLUR_SIGMA)
    frame = render_wave_layer_fast(field, wave_levels(time_seconds))
    return frame, sources


def fast_evaluate_field(sources: list[base.WaveSource], time_seconds: float, blur_sigma: float) -> np.ndarray:
    field = np.zeros((FAST_FH, FAST_FW), dtype=np.float32)
    for source in sources:
        env = base.source_envelope(source, time_seconds)
        if env <= 0.0001:
            continue
        dx = FAST_GRID_X - source.x
        dy = FAST_GRID_Y - source.y
        distance = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
        omega = TAU * source.frequency
        phase = TAU * distance / source.wavelength - omega * time_seconds + source.phase
        decay = np.exp(-distance / max(1.0, source.decay), dtype=np.float32)
        wave = np.cos(phase, dtype=np.float32) * decay
        field += (source.amplitude * env) * wave

    field *= FAST_EDGE_WINDOW
    if blur_sigma > 0:
        field = cv2.GaussianBlur(field, (0, 0), max(0.20, blur_sigma * 0.52))
    max_abs = float(np.percentile(np.abs(field), 99.35))
    if max_abs >= 1e-5:
        field = np.clip(field / max_abs, -1.0, 1.0).astype(np.float32)
    field = cv2.GaussianBlur(field, (0, 0), max(0.22, blur_sigma * 0.40))
    return np.clip(field, -1.0, 1.0).astype(np.float32)


def render_wave_layer_fast(field_norm: np.ndarray, levels: dict[str, float]) -> np.ndarray:
    frame_small = np.zeros((FAST_FH, FAST_FW, 3), dtype=np.uint8)
    field_small = cv2.GaussianBlur(wave_v002.shape_field(field_norm), (0, 0), 0.34)
    inside = FAST_FIELD_BOUNDARY > 4
    soft = FAST_FIELD_BOUNDARY

    pos = np.where((field_small > wave_v002.FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    neg = np.where((field_small < -wave_v002.FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    node = np.where((np.abs(field_small) <= wave_v002.NODE_EPSILON) & inside, soft, 0).astype(np.uint8)
    node = cv2.morphologyEx(node, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    region = cv2.bitwise_or(pos, neg)
    edge = cv2.morphologyEx(region, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    node_edge = cv2.morphologyEx(node, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))

    wave_v002.blend_mask(frame_small, soft, wave_v002.DARK_WATER, 0.58 * levels["water"])
    wave_v002.blend_mask(frame_small, neg, wave_v002.TEAL, 0.68 * levels["negative"])
    wave_v002.blend_mask(frame_small, pos, wave_v002.WARM_CREAM, 0.58 * levels["positive"])
    wave_v002.blend_mask(frame_small, edge, wave_v002.INK, 0.28 * levels["line"])
    wave_v002.blend_mask(frame_small, node, wave_v002.INK, 0.64 * levels["line"])
    wave_v002.blend_mask(frame_small, node_edge, wave_v002.MUTED_TEAL, 0.18 * levels["line"])

    frame = cv2.resize(frame_small, (W, H), interpolation=cv2.INTER_CUBIC)
    wave_v002.blend_mask(frame, FIELD_BOUNDARY_EDGE_FULL, wave_v002.MUTED_TEAL, 0.14 * levels["line"])
    return frame


def nature_portal_levels(time_seconds: float) -> dict[str, float]:
    if time_seconds < 8.0:
        return {"central_aperture": 0.0, "ray_aperture": 0.0, "full_aperture": 0.0}
    central = smoothstep01((time_seconds - 8.0) / 0.9)
    rays = smoothstep01((time_seconds - 8.8) / 1.35)
    full = smoothstep01((time_seconds - 10.2) / 1.65)
    if 12.0 <= time_seconds <= 14.4:
        central = rays = full = 1.0
    if time_seconds > 14.4:
        central = rays = full = 1.0
    return {
        "central_aperture": clamp01(central),
        "ray_aperture": clamp01(rays),
        "full_aperture": clamp01(full),
    }


def nature_mask_at(time_seconds: float, nature: ArtworkLayer) -> tuple[np.ndarray, np.ndarray]:
    if time_seconds < 8.0:
        zero = np.zeros((H, W), dtype=np.uint8)
        return zero, zero
    global NATURE_RADIAL_HOLD_MASK
    if NATURE_RADIAL_HOLD_MASK is None:
        NATURE_RADIAL_HOLD_MASK = np.minimum(wave_v002.FULL_APERTURE_MASK, nature.alpha)
    portal = wave_v002.portal_aperture(nature_portal_levels(time_seconds), nature.alpha)
    aperture = portal["aperture"]
    edge = portal["edge"]
    if time_seconds < 14.4:
        return aperture, edge
    if time_seconds < 16.0:
        settle = smoothstep01((time_seconds - 14.4) / 1.6)
        mask = (
            aperture.astype(np.float32) * (1.0 - settle)
            + NATURE_RADIAL_HOLD_MASK.astype(np.float32) * settle
        )
        return np.clip(mask, 0, 255).astype(np.uint8), edge
    return NATURE_RADIAL_HOLD_MASK, np.zeros((H, W), dtype=np.uint8)


def raven_mask_at(time_seconds: float, raven: ArtworkLayer) -> np.ndarray:
    if time_seconds < 32.0:
        return np.zeros((H, W), dtype=np.uint8)
    if time_seconds < 44.0:
        progress = smoothstep01((time_seconds - 32.0) / 9.0)
        anchor_open = smoothstep01((time_seconds - 32.0) / 1.4)
        expansion_radius = ANCHOR_RADIUS_PX + progress * 900.0
        expansion = centered_circle_mask(expansion_radius, soft_edge=118.0)
        anchor = (ANCHOR_MASK.astype(np.float32) * anchor_open).astype(np.uint8)
        return np.minimum(np.maximum(anchor, expansion), raven.soft_alpha)
    if time_seconds < 54.0:
        return raven.soft_alpha
    return_progress = smoothstep01((time_seconds - 54.0) / 6.0)
    radius = 1320.0 * (1.0 - return_progress) + (ANCHOR_RADIUS_PX + 28.0) * return_progress
    return np.minimum(centered_circle_mask(radius, soft_edge=160.0), raven.soft_alpha)


@lru_cache(maxsize=72)
def load_raven_spatial_frame_raw(frame_idx: int) -> np.ndarray:
    frame_idx = max(0, min(RAVEN_SPATIAL_TOTAL_FRAMES - 1, frame_idx))
    path = RAVEN_SPATIAL_FRAMES_DIR / f"frame_{frame_idx:04d}.png"
    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"could not read Raven clean-frame spatial frame: {path}")
    return frame


def raven_spatial_reveal_mask(time_seconds: float) -> np.ndarray:
    if time_seconds < 32.0:
        return np.zeros((H, W), dtype=np.uint8)
    if time_seconds < 44.0:
        progress = smoothstep01((time_seconds - 33.5) / 10.5)
        anchor_open = smoothstep01((time_seconds - 32.0) / 1.35)
        expansion_radius = ANCHOR_RADIUS_PX + progress * 930.0
        expansion = centered_circle_mask(expansion_radius, soft_edge=150.0)
        anchor = (ANCHOR_MASK.astype(np.float32) * anchor_open).astype(np.uint8)
        return np.maximum(anchor, expansion)
    if time_seconds < 54.0:
        return np.full((H, W), 255, dtype=np.uint8)
    return_progress = smoothstep01((time_seconds - 54.0) / 6.0)
    radius = 1320.0 * (1.0 - return_progress) + (ANCHOR_RADIUS_PX + 34.0) * return_progress
    return centered_circle_mask(radius, soft_edge=170.0)


def feather_source_boundary(source_alpha: np.ndarray, feather_px: float) -> np.ndarray:
    binary = np.where(source_alpha > 8, 255, 0).astype(np.uint8)
    if np.count_nonzero(binary) == 0:
        return source_alpha
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5).astype(np.float32)
    feather = np.clip(dist / max(1e-6, feather_px), 0.0, 1.0)
    feather = feather * feather * (3.0 - 2.0 * feather)
    return np.clip(source_alpha.astype(np.float32) * feather, 0, 255).astype(np.uint8)


def raven_spatial_frame_at(time_seconds: float) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    t_norm = clamp01(raven_spatial_node_norm(time_seconds))
    frame_idx = round(t_norm * (RAVEN_SPATIAL_TOTAL_FRAMES - 1))
    raw = load_raven_spatial_frame_raw(frame_idx)

    projected_center, projected_radius = raven_spatial_anchor_projection(t_norm)
    target_radius = raven_spatial_target_radius(time_seconds)
    align_scale = target_radius / max(1e-6, projected_radius)
    tx = ANCHOR_CENTER_PX[0] - align_scale * projected_center[0]
    ty = ANCHOR_CENTER_PX[1] - align_scale * projected_center[1]
    matrix = np.array([[align_scale, 0.0, tx], [0.0, align_scale, ty]], dtype=np.float32)
    aligned = cv2.warpAffine(
        raw,
        matrix,
        (W, H),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=tuple(int(v) for v in RAVEN_SPATIAL_BG_BGR),
    )

    diff = np.abs(aligned.astype(np.int16) - RAVEN_SPATIAL_BG_BGR.astype(np.int16)).sum(axis=2).astype(np.float32)
    source_alpha = np.clip((diff - 2.0) / 24.0, 0.0, 1.0)
    source_alpha = cv2.GaussianBlur(source_alpha, (0, 0), 0.85)
    source_alpha = np.clip(source_alpha * 255.0, 0, 255).astype(np.uint8)
    if time_seconds < 44.0:
        source_alpha = feather_source_boundary(source_alpha, 96.0)
    elif time_seconds < 54.0:
        source_alpha = feather_source_boundary(source_alpha, 116.0)
    else:
        source_alpha = feather_source_boundary(source_alpha, 108.0)

    reveal = raven_spatial_reveal_mask(time_seconds)
    mask = np.minimum(source_alpha, reveal)
    if 32.0 <= time_seconds < 44.0:
        mask = cv2.GaussianBlur(mask, (0, 0), 1.65)
    elif 44.0 <= time_seconds < 54.0:
        mask = cv2.GaussianBlur(mask, (0, 0), 0.72)
    else:
        mask = cv2.GaussianBlur(mask, (0, 0), 1.35)
    mask = np.clip(mask, 0, 255).astype(np.uint8)

    info = {
        "spatial_variant": "clean_frame",
        "spatial_frame_idx": int(frame_idx),
        "spatial_node_norm": round(t_norm, 4),
        "projected_anchor_center_px_before_alignment": [round(projected_center[0], 3), round(projected_center[1], 3)],
        "projected_anchor_radius_px_before_alignment": round(projected_radius, 3),
        "anchor_alignment_scale": round(align_scale, 4),
        "canvas_anchor_center_px_after_alignment": list(ANCHOR_CENTER_PX),
        "canvas_anchor_radius_px_after_alignment": round(target_radius, 3),
        "source_alpha_nonzero_px": int(np.count_nonzero(source_alpha > 8)),
        "mask_nonzero_px": int(np.count_nonzero(mask > 8)),
    }
    return aligned, mask, info


def anchor_ripple_alpha(time_seconds: float) -> float:
    nature_bridge = smoothstep01((time_seconds - 23.0) / 3.0) * (1.0 - smoothstep01((time_seconds - 42.0) / 4.0))
    portal_hold = smoothstep01((time_seconds - 11.0) / 1.0) * (1.0 - smoothstep01((time_seconds - 15.5) / 1.0))
    return_cue = smoothstep01((time_seconds - 54.0) / 1.8) * (1.0 - smoothstep01((time_seconds - 58.7) / 1.2))
    return clamp01(max(nature_bridge, 0.54 * portal_hold, 0.90 * return_cue))


def portal_alignment_alpha(time_seconds: float) -> float:
    gather = smoothstep01((time_seconds - 4.5) / 3.0) * (1.0 - smoothstep01((time_seconds - 15.6) / 1.2))
    return clamp01(gather)


def draw_anchor_ripples(frame: np.ndarray, time_seconds: float, alpha: float) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    phase = (time_seconds * 0.42) % 1.0
    for idx in range(3):
        offset = 20.0 * idx + 10.0 * math.sin(TAU * (phase + idx * 0.18))
        radius = ANCHOR_RADIUS_PX + offset
        color = PORTAL_GLOW if idx == 0 else PORTAL_ORANGE
        cv2.circle(
            overlay,
            (round(ANCHOR_CENTER_PX[0]), round(ANCHOR_CENTER_PX[1])),
            max(1, round(radius)),
            rgb_to_bgr(color),
            1 + (idx == 0),
            lineType=cv2.LINE_AA,
        )
    cv2.addWeighted(overlay, 0.42 * alpha, frame, 1.0, 0, dst=frame)


def render_frame(
    time_seconds: float,
    nature: ArtworkLayer,
    raven: ArtworkLayer,
    *,
    debug: bool = False,
    collect_info: bool = False,
) -> tuple[np.ndarray, dict[str, object]]:
    frame, sources = render_wave_base(time_seconds)
    align_alpha = portal_alignment_alpha(time_seconds)
    if align_alpha > 0.0:
        wave_v002.draw_octagonal_axes(frame, alpha=0.18 * align_alpha, labels=False)
        wave_v002.draw_source_positions(frame, sources, alpha=0.22 * align_alpha, labels=False)

    nature_mask, nature_edge = nature_mask_at(time_seconds, nature)
    n_opacity = nature_opacity(time_seconds)
    if n_opacity > 0.0:
        wave_v002.alpha_over(frame, nature.bgr, nature_mask, n_opacity)
        if float(nature_edge.max()) > 0.0:
            wave_v002.blend_mask(frame, nature_edge, PORTAL_GLOW, 0.18 * align_alpha, glow=0.006 * align_alpha)

    ripple_alpha = anchor_ripple_alpha(time_seconds)
    draw_anchor_ripples(frame, time_seconds, ripple_alpha)

    raven_spatial_info: dict[str, object] | None = None
    if time_seconds >= 32.0:
        raven_bgr, raven_mask, raven_spatial_info = raven_spatial_frame_at(time_seconds)
    else:
        raven_bgr = raven.bgr
        raven_mask = np.zeros((H, W), dtype=np.uint8)
    r_opacity = raven_opacity(time_seconds)
    if r_opacity > 0.0:
        wave_v002.alpha_over(frame, raven_bgr, raven_mask, r_opacity)
        edge_alpha = smoothstep01((time_seconds - 32.0) / 2.0) * (1.0 - smoothstep01((time_seconds - 43.0) / 1.2))
        if edge_alpha > 0.001:
            reveal_edge = mask_edge(raven_mask, kernel_px=11, blur=5.0)
            wave_v002.blend_mask(frame, reveal_edge, PORTAL_GLOW, 0.13 * edge_alpha, glow=0.003 * edge_alpha)

    draw_anchor_ripples(frame, time_seconds, 0.44 * ripple_alpha * (1.0 - 0.42 * r_opacity))

    info = {
        "time_seconds": round(time_seconds, 4),
        "coherence": round(spine_coherence(time_seconds), 4),
        "nature_opacity": round(n_opacity, 4),
        "raven_opacity": round(r_opacity, 4),
        "anchor_ripple_alpha": round(ripple_alpha, 4),
        "portal_alignment_alpha": round(align_alpha, 4),
    }
    if collect_info:
        info["masks"] = {
            "nature_nonzero_px": int(np.count_nonzero(nature_mask > 8)),
            "raven_nonzero_px": int(np.count_nonzero(raven_mask > 8)),
            "anchor_nonzero_px": int(np.count_nonzero(ANCHOR_MASK > 8)),
        }
        if raven_spatial_info is not None:
            info["raven_spatial"] = raven_spatial_info
    if debug:
        base.draw_text(frame, f"anchor_graph_spine_v002 t={time_seconds:05.2f}", (42, 56), LABEL, scale=0.50)
    return frame, info


def save_key_stills(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, time_seconds in KEY_STILL_TIMES:
        frame, _info = render_frame(time_seconds, nature, raven)
        path = STILLS_DIR / f"anchor_graph_spine_v002_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[f"{key}_still"] = str(path.relative_to(OUT_DIR))
    peak_frame, _info = render_frame(12.8, nature, raven)
    peak_path = PEAK_DIR / "anchor_graph_spine_v002_nature_portal_peak.png"
    cv2.imwrite(str(peak_path), peak_frame)
    outputs["nature_portal_peak"] = str(peak_path.relative_to(OUT_DIR))
    return outputs


def make_contact_sheet(nature: ArtworkLayer, raven: ArtworkLayer) -> Path:
    panels: list[np.ndarray] = []
    for time_seconds in CONTACT_TIMES:
        frame, _info = render_frame(time_seconds, nature, raven)
        panel = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, f"t={time_seconds:04.1f}s", (16, 30), LABEL, scale=0.34)
        panels.append(panel)
    rows = [cv2.hconcat(panels[i : i + 4]) for i in range(0, len(panels), 4)]
    sheet = cv2.vconcat(rows)
    path = OUT_DIR / "anchor_graph_spine_v002_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_v001_v002_comparison_sheet(contact_path: Path) -> Path:
    v001_path = (
        ROOT
        / "track2-deterministic"
        / "morph_outputs_INTERNAL"
        / "anchor_graph_spine_v001_2026-05-21"
        / "anchor_graph_spine_v001_contact_sheet.png"
    )
    v001 = cv2.imread(str(v001_path), cv2.IMREAD_COLOR)
    v002 = cv2.imread(str(contact_path), cv2.IMREAD_COLOR)
    if v001 is None:
        raise RuntimeError(f"could not read v001 contact sheet: {v001_path}")
    if v002 is None:
        raise RuntimeError(f"could not read v002 contact sheet: {contact_path}")
    if v001.shape[:2] != v002.shape[:2]:
        v001 = cv2.resize(v001, (v002.shape[1], v002.shape[0]), interpolation=cv2.INTER_AREA)
    label_h = 56
    bar1 = np.full((label_h, v002.shape[1], 3), rgb_to_bgr(DEEP_GROUND), dtype=np.uint8)
    bar2 = bar1.copy()
    base.draw_text(bar1, "v001: flat Raven hold", (28, 38), LABEL, scale=0.48)
    base.draw_text(bar2, "v002: clean-frame Raven spatial node, anchor-stabilized", (28, 38), LABEL, scale=0.48)
    sheet = cv2.vconcat([bar1, v001, bar2, v002])
    path = OUT_DIR / "anchor_graph_spine_v001_v002_comparison_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_timeline_panel(width: int, height: int) -> np.ndarray:
    panel = np.full((height, width, 3), rgb_to_bgr(DEEP_GROUND), dtype=np.uint8)
    segments = (
        ("wave gather", 0.0, 8.0, MUTED_TEAL),
        ("Nature portal", 8.0, 16.0, SOFT_GOLD),
        ("Nature hold", 16.0, 24.0, (232, 184, 92)),
        ("shared sun-disc anchor", 24.0, 32.0, PORTAL_GLOW),
        ("Raven reveal", 32.0, 44.0, PORTAL_ORANGE),
        ("Raven spatial hold", 44.0, 54.0, (180, 168, 130)),
        ("return to wave", 54.0, 60.0, MUTED_TEAL),
    )
    x_pad = 42
    y = height // 2
    track_w = width - 2 * x_pad
    cv2.line(panel, (x_pad, y), (width - x_pad, y), rgb_to_bgr(LABEL), 1, lineType=cv2.LINE_AA)
    for label, start, end, color in segments:
        x0 = x_pad + round(track_w * start / DURATION_SECONDS)
        x1 = x_pad + round(track_w * end / DURATION_SECONDS)
        cv2.rectangle(panel, (x0, y - 20), (x1, y + 20), rgb_to_bgr(color), -1, lineType=cv2.LINE_AA)
        base.draw_text(panel, label, (x0 + 6, y - 34), LABEL, scale=0.30)
        base.draw_text(panel, f"{start:.0f}-{end:.0f}s", (x0 + 6, y + 44), LABEL, scale=0.28)
    base.draw_text(panel, "debug timeline: masks and anchors are metadata-driven presentation guides", (42, 44), LABEL, scale=0.42)
    return panel


def make_debug_sheet(nature: ArtworkLayer, raven: ArtworkLayer) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    panel_specs = (
        ("wave gather: C8 source positions", 6.0),
        ("Nature portal: center/ray/full aperture", 12.5),
        ("Nature hold: residual wave support", 19.0),
        ("shared anchor: sun-disc radius aligned", 28.0),
        ("Raven reveal: expansion from shared disc", 38.0),
        ("return: source recedes to ripple cue", 57.0),
    )
    panels: list[np.ndarray] = []
    for label, time_seconds in panel_specs:
        frame, _info = render_frame(time_seconds, nature, raven)
        nature_mask, _edge = nature_mask_at(time_seconds, nature)
        _raven_bgr, raven_mask, _raven_info = raven_spatial_frame_at(time_seconds) if time_seconds >= 32.0 else (
            raven.bgr,
            np.zeros((H, W), dtype=np.uint8),
            {},
        )
        if np.count_nonzero(nature_mask) > 0:
            wave_v002.blend_mask(frame, mask_edge(nature_mask), MUTED_TEAL, 0.40)
        if np.count_nonzero(raven_mask) > 0:
            wave_v002.blend_mask(frame, mask_edge(raven_mask), PORTAL_ORANGE, 0.36)
        cv2.circle(
            frame,
            (round(ANCHOR_CENTER_PX[0]), round(ANCHOR_CENTER_PX[1])),
            round(ANCHOR_RADIUS_PX),
            rgb_to_bgr(PORTAL_GLOW),
            2,
            lineType=cv2.LINE_AA,
        )
        panel = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (18, 34), LABEL, scale=0.34)
        base.draw_text(panel, f"t={time_seconds:04.1f}s", (18, 62), LABEL, scale=0.30)
        panels.append(panel)
    top = cv2.hconcat(panels[:3])
    bottom = cv2.hconcat(panels[3:])

    mask_panel = np.full((360, 1920, 3), rgb_to_bgr(DEEP_GROUND), dtype=np.uint8)
    n_mask, _edge = nature_mask_at(12.5, nature)
    _raven_bgr, r_mask, _raven_info = raven_spatial_frame_at(38.0)
    n_mask_small = cv2.resize(n_mask, (1920, 360), interpolation=cv2.INTER_AREA)
    anchor_small = cv2.resize(ANCHOR_MASK, (1920, 360), interpolation=cv2.INTER_AREA)
    r_mask_small = cv2.resize(r_mask, (1920, 360), interpolation=cv2.INTER_AREA)
    wave_v002.blend_mask(mask_panel, n_mask_small, MUTED_TEAL, 0.34)
    wave_v002.blend_mask(mask_panel, anchor_small, PORTAL_GLOW, 0.24)
    wave_v002.blend_mask(mask_panel, r_mask_small, PORTAL_ORANGE, 0.30)
    cv2.circle(mask_panel, (round(ANCHOR_CENTER_PX[0]), 180), round(ANCHOR_RADIUS_PX / 3.0), rgb_to_bgr(PORTAL_GLOW), 2, lineType=cv2.LINE_AA)
    base.draw_text(mask_panel, "debug masks: Nature aperture + metadata-only shared anchor + Raven reveal mask", (42, 52), LABEL, scale=0.46)
    base.draw_text(mask_panel, "No standalone anchor is a renderable primitive or extracted motif.", (42, 88), LABEL, scale=0.38)

    timeline = make_timeline_panel(1920, 220)
    sheet = cv2.vconcat([top, bottom, mask_panel, timeline])
    path = DEBUG_DIR / "anchor_graph_spine_v002_anchor_mask_timeline_debug.png"
    cv2.imwrite(str(path), sheet)
    return path


def render_clip(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, object]:
    output_path = OUT_DIR / "anchor_graph_spine_v002.mp4"
    writer = base.H264Writer(output_path, fps=FPS, size=(W, H))
    peak_info: dict[str, object] | None = None
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = frame_idx / FPS
            collect = frame_idx == round(12.8 * FPS)
            frame, info = render_frame(time_seconds, nature, raven, collect_info=collect)
            writer.write(frame)
            if frame_idx == round(12.8 * FPS):
                peak_info = info
            if (frame_idx + 1) % FPS == 0:
                print(f"  anchor_graph_spine_v002.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_frame(12.8, nature, raven, collect_info=True)
    return {
        "filename": "anchor_graph_spine_v002.mp4",
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "frame_count": N_FRAMES,
        "peak_time_seconds": 12.8,
        "peak_info": peak_info,
    }


def write_source_provenance_note(input_status: dict[str, object]) -> Path:
    lines = [
        "# Source Provenance Note",
        "",
        "Status: INTERNAL ONLY. Pending Austin review. No public/show/projector/sponsor/social/press use.",
        "",
        "This packet uses Austin-authored SVGs as whole source artworks. The renderer rasterizes the SVGs to PNG for compositing and does not create new SVG assets.",
        "",
        "## Sources",
        "",
    ]
    for spec in ARTWORK_SPECS:
        lines.extend(
            [
                f"### {spec.title}",
                "",
                f"- Source path: `{spec.source_path.relative_to(ROOT)}`",
                f"- SHA256: `{sha256(spec.source_path)}`",
                f"- Whole-source-only: `true`",
                f"- Consent status: `pending_austin_review`",
                "",
            ]
        )
    lines.extend(
        [
            "## Registry",
            "",
            f"- Registry path: `{REGISTRY_PATH.relative_to(ROOT)}`",
            f"- Registry SHA256: `{input_status.get('registry_sha256')}`",
            "- Anchor records used here are alignment metadata only, not renderable primitives.",
        ]
    )
    path = OUT_DIR / "SOURCE_PROVENANCE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_manifest(
    input_status: dict[str, object],
    nature: ArtworkLayer,
    raven: ArtworkLayer,
    clip_summary: dict[str, object],
    stills: dict[str, str],
    contact_path: Path,
    comparison_path: Path,
    debug_path: Path,
    provenance_note: Path,
) -> Path:
    anchors = input_status["anchors"]
    manifest = {
        "project": "anchor_graph_spine_v002",
        "status": "internal_only_pending_austin_review",
        "boundary": "Internal only. Pending Austin review. No public/show/projector/sponsor/social/press use. No cultural-meaning claims. No motif extraction. No atom decomposition. No source recoloring. No new SVG assets.",
        "renderer": "scripts/anchor_graph_spine_v002.py",
        "renderer_sha256": sha256(ROOT / "scripts" / "anchor_graph_spine_v002.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "rules": {
            "whole_austin_artworks_remain_whole_source": True,
            "anchor_records_are_alignment_metadata_only": True,
            "training": False,
            "diffusion": False,
            "style_imitation": False,
            "source_recoloring": False,
            "motif_extraction": False,
            "atom_decomposition": False,
            "new_svg_assets_created": False,
        },
        "spatial_node_integration": {
            "node_id": "raven_sun_spatial_node_v002_2026-05-21",
            "variant": "clean_frame",
            "node_readme": str(RAVEN_SPATIAL_README.relative_to(ROOT)),
            "node_manifest": str(RAVEN_SPATIAL_MANIFEST.relative_to(ROOT)),
            "node_mp4": str(RAVEN_SPATIAL_MP4.relative_to(ROOT)),
            "node_frames_dir": str(RAVEN_SPATIAL_FRAMES_DIR.relative_to(ROOT)),
            "integration_method": "The clean-frame Raven spatial frames are composited through source-alpha and source-aligned reveal masks, then affine-stabilized so the Raven central sun-disc metadata anchor lands at canvas center [960, 540]. The reveal preserves the 276 px shared radius; the hold eases to a slightly smaller center-locked radius so the clean-frame node reads as a spatial passage rather than an oversized card.",
            "anchor_stabilization": {
                "target_center_px": list(ANCHOR_CENTER_PX),
                "reveal_target_radius_px": ANCHOR_RADIUS_PX,
                "hold_target_radius_px": 246.0,
                "basis": "Projection of the Raven back-tier sun-disc center/radius from the spatial-node camera model; anchors remain metadata only.",
            },
            "debug_text_in_main_mp4": False,
        },
        "context_docs": input_status["context_docs"],
        "source_artworks": {
            "nature_cosmic_sun": nature.info,
            "animal_bird_raven_sun": raven.info,
        },
        "anchors": [
            anchors["nature_cosmic_sun.central_sun_disc"],
            anchors["nature_cosmic_sun.eight_ray_radial_aperture_structure"],
            anchors["animal_bird_raven_sun.central_sun_disc"],
        ],
        "timings": [
            {
                "segment": "wave atmosphere gather",
                "time_seconds": [0.0, 8.0],
                "edge_type": "wave_atmosphere",
                "notes": "C8 wave sources gather into an octagonal structure aligned to the Nature portal target.",
            },
            {
                "segment": "Nature Cosmic Sun portal",
                "time_seconds": [8.0, 16.0],
                "edge_type": "wave_to_artwork",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "strongest_alignment_hold_seconds": [12.0, 14.4],
            },
            {
                "segment": "Nature hold with residual wave presence",
                "time_seconds": [16.0, 24.0],
                "edge_type": "artwork_hold",
                "anchors_used": ["nature_cosmic_sun.central_sun_disc"],
            },
            {
                "segment": "shared sun-disc anchor stabilizes",
                "time_seconds": [24.0, 32.0],
                "edge_type": "artwork_to_artwork_anchor_bridge",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "animal_bird_raven_sun.central_sun_disc",
                ],
            },
            {
                "segment": "Raven Sun spatial reveal from shared anchor",
                "time_seconds": [32.0, 44.0],
                "edge_type": "artwork_to_artwork",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "animal_bird_raven_sun.central_sun_disc",
                ],
                "transition_method": "clean-frame Raven spatial frames through source-alpha, source-aligned expansion masks, edge feathering, residual wave atmosphere, and shared sun-disc anchor stabilization",
            },
            {
                "segment": "Raven Sun clean-frame spatial hold",
                "time_seconds": [44.0, 54.0],
                "edge_type": "spatial_artwork_hold",
                "anchors_used": ["animal_bird_raven_sun.central_sun_disc"],
                "spatial_note": "Uses the raven_sun_spatial_node_v002 clean_frame treatment with subtle parallax. The whole authored Raven artwork remains the source; the renderer does not add a new artwork node or split the figure beyond the authored grouping already documented in the spatial node.",
            },
            {
                "segment": "return to wave/water atmosphere",
                "time_seconds": [54.0, 60.0],
                "edge_type": "artwork_to_wave_atmosphere",
                "anchors_used": ["animal_bird_raven_sun.central_sun_disc"],
            },
        ],
        "tested_edges": [
            {
                "edge_id": "wave_to_nature_cosmic_sun_spine_v002",
                "edge_type": "wave_to_artwork",
                "status": "internal_composition_pass",
                "source_node": "wave_octagonal_c8",
                "target_node": "nature_cosmic_sun",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v002.mp4").relative_to(ROOT)),
                "caveats": [
                    "No cultural-meaning claim.",
                    "Alignment is positional/radial, not a claim that the wave field reproduces Austin forms.",
                ],
            },
            {
                "edge_id": "nature_cosmic_sun_to_raven_sun_spine_v002",
                "edge_type": "artwork_to_artwork",
                "status": "internal_composition_pass_pending_austin_review",
                "source_node": "nature_cosmic_sun",
                "target_node": "animal_bird_raven_sun",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "animal_bird_raven_sun.central_sun_disc",
                ],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v002.mp4").relative_to(ROOT)),
                "caveats": [
                    "Transition uses whole-source alignment, source-alpha masks, and the clean-frame spatial node.",
                    "Austin review is required before any public or show use.",
                ],
            },
            {
                "edge_id": "raven_sun_to_wave_return_spine_v002",
                "edge_type": "artwork_to_wave_atmosphere",
                "status": "internal_composition_pass",
                "source_node": "animal_bird_raven_sun",
                "target_node": "wave_water_atmosphere",
                "anchors_used": ["animal_bird_raven_sun.central_sun_disc"],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v002.mp4").relative_to(ROOT)),
                "caveats": ["Return cue is a presentation ripple, not a reusable extracted sun motif."],
            },
        ],
        "clip": clip_summary,
        "deliverables": {
            "mp4": clip_summary["mp4"],
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "v001_v002_comparison_sheet": str(comparison_path.relative_to(OUT_DIR)),
            "debug_sheet": str(debug_path.relative_to(OUT_DIR)),
            "source_provenance_note": str(provenance_note.relative_to(OUT_DIR)),
            "readme": "README.md",
            **stills,
        },
    }
    path = OUT_DIR / "anchor_graph_spine_v002_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(nature: ArtworkLayer, raven: ArtworkLayer, clip_summary: dict[str, object]) -> Path:
    lines = [
        "# Anchor Graph Spine v002",
        "",
        "Status: INTERNAL ONLY. Pending Austin review. Not approved for public, show, projector, sponsor, social, press, or external use. No cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet refines `anchor_graph_spine_v001` by integrating the `raven_sun_spatial_node_v002` clean-frame Raven treatment into the lead spine. It keeps the same passage structure: wave atmosphere -> Nature Cosmic Sun portal -> shared sun-disc anchor -> Raven spatial reveal -> Raven clean-frame spatial hold -> return to wave/water atmosphere.",
        "",
        "Austin's source SVGs remain whole authored artworks. The shared sun-disc and eight-ray records are alignment metadata only. They are not renderable primitives, extracted motifs, atom records, or new SVG assets. The Raven spatial node is used as an authored-grouping treatment already documented in its own internal packet, not as a new artwork node.",
        "",
        "## Sources",
        "",
        f"- `{nature.info['source_svg']}` SHA256 `{nature.info['source_sha256']}`",
        f"- `{raven.info['source_svg']}` SHA256 `{raven.info['source_sha256']}`",
        f"- Anchor registry: `{REGISTRY_PATH.relative_to(ROOT)}`",
        f"- Raven spatial node: `{RAVEN_SPATIAL_README.relative_to(ROOT)}`",
        f"- Raven clean-frame MP4: `{RAVEN_SPATIAL_MP4.relative_to(ROOT)}`",
        "",
        "## Sequence",
        "",
        "- 0-8s: wave/cymatic atmosphere gathers into an 8-source octagonal structure.",
        "- 8-16s: Nature Cosmic Sun opens through the v002 portal. The strongest portal-alignment state holds from 12.0s to 14.4s.",
        "- 16-24s: Nature holds with subtle residual wave presence.",
        "- 24-32s: the shared sun-disc anchor stabilizes as a continuity bridge.",
        "- 32-44s: Raven Sun emerges from the same center/radius through source-aligned masks, using the clean-frame spatial treatment under residual wave atmosphere.",
        "- 44-54s: Raven Sun holds as the clean-frame spatial node with subtle parallax. The projected Raven sun-disc is stabilized back to the shared canvas center/radius.",
        "- 54-60s: the source recedes back toward wave/water atmosphere, with a ripple cue around the same center.",
        "",
        "## Deliverables",
        "",
        "- `anchor_graph_spine_v002.mp4`: 1920x1080, 24 fps, 60 seconds.",
        "- `anchor_graph_spine_v002_contact_sheet.png`: 12-frame sequence sheet.",
        "- `stills/`: wave gather, Nature portal, Nature hold, shared anchor, Raven transition, Raven hold, and return stills.",
        "- `anchor_graph_spine_v001_v002_comparison_sheet.png`: v001/v002 contact-sheet comparison.",
        "- `debug_stills/anchor_graph_spine_v002_anchor_mask_timeline_debug.png`: anchor, mask, and timeline diagnostics.",
        "- `anchor_graph_spine_v002_manifest.json`: sources, hashes, anchors, timings, edge types, spatial-node integration, and deliverables.",
        "- `SOURCE_PROVENANCE.md`: local source provenance and boundary note.",
        "",
        "## Honest Verdict",
        "",
        "This is a real improvement over v001 where it needed to improve. The Raven section no longer reads as a flat card simply appearing after the Nature portal; the clean-frame parallax gives the Raven field spatial behaviour, and the reveal is carried by source-alpha masks rather than a hard rectangle.",
        "",
        "The compromise is that anchor stabilization slightly reins in the raw camera drift from the standalone Raven node, and the hold relaxes from the exact 276 px reveal radius to a center-locked 246 px radius to keep the whole clean-frame treatment readable. That is intentional for this spine: the shared sun-disc remains the continuity contract, while the Raven layers still retain enough parallax to feel spatial. The back sky rectangle can still be perceived as a picture plane during the hold, but it is no longer a pasted flat card transition.",
        "",
        "This remains a technical/aesthetic internal study. It does not claim the shared anchor has cultural meaning, and it is not cleared for public, projector, sponsor, press, social, or show use. Austin review is required before any external use.",
        "",
        "Renderer: `scripts/anchor_graph_spine_v002.py`",
        f"Clip summary: `{clip_summary['filename']}`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render anchor graph spine v002.")
    parser.add_argument("--preview", action="store_true", help="Write still/debug artifacts without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    input_status = verify_inputs()
    if not input_status["ok"]:
        issue_path = OUT_DIR / "SOURCE_PROVENANCE_ISSUE.md"
        issue_path.write_text(
            "# Source Provenance Issue\n\n"
            "Rendering stopped because a required source, context file, or hash check failed.\n\n"
            + "\n".join(f"- {issue}" for issue in input_status["issues"])
            + "\n",
            encoding="utf-8",
        )
        raise SystemExit(f"input verification failed; wrote {issue_path}")

    print("Rasterizing Austin source SVGs as whole-source PNG layers", flush=True)
    nature = load_artwork_layer(NATURE_SPEC)
    raven = load_artwork_layer(RAVEN_SPEC)
    provenance_note = write_source_provenance_note(input_status)

    print("Writing key stills, contact sheet, and debug sheet", flush=True)
    stills = save_key_stills(nature, raven)
    contact_path = make_contact_sheet(nature, raven)
    comparison_path = make_v001_v002_comparison_sheet(contact_path)
    debug_path = make_debug_sheet(nature, raven)

    if args.preview:
        _frame, peak_info = render_frame(12.8, nature, raven, collect_info=True)
        clip_summary = {
            "filename": "anchor_graph_spine_v002.mp4",
            "mp4": "anchor_graph_spine_v002.mp4",
            "duration_seconds": DURATION_SECONDS,
            "fps": FPS,
            "frame_count": N_FRAMES,
            "peak_time_seconds": 12.8,
            "peak_info": peak_info,
        }
    else:
        print("Rendering anchor_graph_spine_v002.mp4", flush=True)
        clip_summary = render_clip(nature, raven)

    manifest = write_manifest(
        input_status,
        nature,
        raven,
        clip_summary,
        stills,
        contact_path,
        comparison_path,
        debug_path,
        provenance_note,
    )
    readme = write_readme(nature, raven, clip_summary)
    print(f"Wrote {OUT_DIR / clip_summary['mp4']}", flush=True)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {comparison_path}", flush=True)
    print(f"Wrote {debug_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
