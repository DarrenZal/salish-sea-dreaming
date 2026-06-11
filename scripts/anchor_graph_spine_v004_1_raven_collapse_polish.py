#!/usr/bin/env python3
"""
Anchor graph spine v004.1 Raven collapse polish.

Internal composition pass for Salish Sea Dreaming. This renderer composes the
validated anchor-graph pieces into one loop-closed UHD passage:

wave atmosphere -> Nature Cosmic Sun portal -> full Nature Cosmic Sun hold ->
shared sun-disc anchor -> Raven Sun spatial reveal -> stable Raven spatial hold
-> Raven anchor collapse -> ordered cymatic connective tissue -> Nature Cosmic
Sun return -> mathematically matched cymatic loop point.

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
    / "anchor_graph_spine_v004_1_raven_collapse_polish_2026-05-21"
)
STILLS_DIR = OUT_DIR / "stills"
PEAK_DIR = OUT_DIR / "peak_stills"
DEBUG_DIR = OUT_DIR / "debug_stills"
LOOP_DIR = OUT_DIR / "loop_diagnostics"
SOURCE_DIR = OUT_DIR / "source_assets"
V003_OUTPUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "anchor_graph_spine_v003_cymatic_loop_2026-05-21"
)
V004_OUTPUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "anchor_graph_spine_v004_round_nature_mask_2026-05-21"
)

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
V003_README = V003_OUTPUT_DIR / "README.md"
V003_MANIFEST = V003_OUTPUT_DIR / "anchor_graph_spine_v003_cymatic_loop_manifest.json"
V003_CONTACT_SHEET = V003_OUTPUT_DIR / "anchor_graph_spine_v003_cymatic_loop_contact_sheet.png"
V003_MP4 = V003_OUTPUT_DIR / "anchor_graph_spine_v003_cymatic_loop.mp4"
V004_README = V004_OUTPUT_DIR / "README.md"
V004_MANIFEST = V004_OUTPUT_DIR / "anchor_graph_spine_v004_round_nature_mask_manifest.json"
V004_MP4 = V004_OUTPUT_DIR / "anchor_graph_spine_v004_round_nature_mask.mp4"
WAVE_SCRIPT = ROOT / "scripts" / "wave_to_artwork_portal_v002.py"
CHAIN_SCRIPT = ROOT / "scripts" / "anchored_artwork_portal_chain_v001.py"

W = 3840
H = 2160
BASE_W = base.W
BASE_H = base.H
RES_SCALE = W / BASE_W
FPS = base.FPS
DURATION_SECONDS = 80.0
LOOP_SECONDS = DURATION_SECONDS
N_FRAMES = int(FPS * DURATION_SECONDS)
TAU = math.tau

ANCHOR_CENTER_PX = (W * 0.5, H * 0.5)
ANCHOR_RADIUS_PX = 276.0 * RES_SCALE
ARTWORK_HIGH_RES_FACTOR = 2
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
FAST_FW = max(480, W // 4)
FAST_FH = max(270, H // 4)
FAST_SX = W / FAST_FW
FAST_SY = H / FAST_FH
FAST_GRID_X = ((np.arange(FAST_FW, dtype=np.float32) + 0.5) * FAST_SX)[None, :]
FAST_GRID_Y = ((np.arange(FAST_FH, dtype=np.float32) + 0.5) * FAST_SY)[:, None]
FAST_EDGE_DISTANCE = np.minimum(
    np.minimum(FAST_GRID_X, W - FAST_GRID_X),
    np.minimum(FAST_GRID_Y, H - FAST_GRID_Y),
)
FAST_EDGE_WINDOW = np.clip(
    (FAST_EDGE_DISTANCE - 32.0 * RES_SCALE) / (148.0 * RES_SCALE),
    0.0,
    1.0,
).astype(np.float32)
FAST_EDGE_WINDOW = FAST_EDGE_WINDOW * FAST_EDGE_WINDOW * (3.0 - 2.0 * FAST_EDGE_WINDOW)

FIELD_BOUNDARY_RADIUS = wave_v002.FIELD_BOUNDARY_RADIUS * RES_SCALE
FIELD_BOUNDARY_SOFT_EDGE = 34.0 * RES_SCALE


def field_boundary_mask(radius: float = FIELD_BOUNDARY_RADIUS, soft_edge: float = FIELD_BOUNDARY_SOFT_EDGE) -> np.ndarray:
    alpha = np.clip((radius + soft_edge - DIST_FROM_ANCHOR) / max(1e-6, soft_edge), 0.0, 1.0)
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


FIELD_BOUNDARY_FULL = field_boundary_mask()
FAST_FIELD_BOUNDARY = cv2.resize(FIELD_BOUNDARY_FULL, (FAST_FW, FAST_FH), interpolation=cv2.INTER_AREA)
FIELD_BOUNDARY_EDGE_FULL = cv2.morphologyEx(
    FIELD_BOUNDARY_FULL,
    cv2.MORPH_GRADIENT,
    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
)

SOURCE_RING_RADIUS = wave_v002.SOURCE_RING_RADIUS * RES_SCALE
SOURCE_WAVELENGTH = wave_v002.SOURCE_WAVELENGTH * RES_SCALE
SOURCE_FREQUENCY = 9.0 / LOOP_SECONDS
SOURCE_DECAY = wave_v002.SOURCE_DECAY * RES_SCALE
DRIFT_AMPLITUDE = wave_v002.DRIFT_AMPLITUDE * RES_SCALE
FIELD_THRESHOLD = wave_v002.FIELD_THRESHOLD
NODE_EPSILON = wave_v002.NODE_EPSILON
BLUR_SIGMA = wave_v002.BLUR_SIGMA * RES_SCALE
FIELD_GAMMA = wave_v002.FIELD_GAMMA

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
RAVEN_NODE_W = 1920
RAVEN_NODE_H = 1080


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


@dataclass(frozen=True)
class OctagonalTargetSource:
    source_id: str
    angle_rad: float
    x: float
    y: float
    amplitude: float
    drift_scale: float
    orbit_phase: float
    orbit_cycles: int
    perturb_cycles: int
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
    frequency_cycles_per_loop: int
    decay: float
    drift_amplitude_px: float
    sources: tuple[OctagonalTargetSource, ...]


class H264Writer:
    def __init__(self, path: Path, *, fps: int, size: tuple[int, int]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = size
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "17",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            str(path),
        ]
        self.path = path
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

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
            raise RuntimeError(f"ffmpeg failed for {self.path} with code {code}\n{stderr[-4000:]}")


def make_octagonal_target() -> OctagonalTarget:
    cx, cy = ANCHOR_CENTER_PX
    sources: list[OctagonalTargetSource] = []
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
                orbit_cycles=1 + (idx % 2),
                perturb_cycles=2 + (idx % 3),
                phase_perturb=(0.137 * idx + 0.21) % 1.0,
            )
        )
    return OctagonalTarget(
        key="octagonal_cosmic_sun_portal_loop_closed_uhd",
        symmetry_type="C8/octagonal",
        source_count=8,
        center_px=(cx, cy),
        source_ring_radius_px=SOURCE_RING_RADIUS,
        wavelength_px=SOURCE_WAVELENGTH,
        frequency=SOURCE_FREQUENCY,
        frequency_cycles_per_loop=9,
        decay=SOURCE_DECAY,
        drift_amplitude_px=DRIFT_AMPLITUDE,
        sources=tuple(sources),
    )


TARGET = make_octagonal_target()


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
NATURE_OUTER_RAY_RADIUS_VIEWBOX = 48.26
NATURE_SCALE_PX_PER_VIEWBOX_UNIT = ANCHOR_RADIUS_PX / NATURE_SPEC.anchor_radius_viewbox
NATURE_OUTER_RAY_EXTENT_PX = NATURE_OUTER_RAY_RADIUS_VIEWBOX * NATURE_SCALE_PX_PER_VIEWBOX_UNIT
NATURE_RADIAL_FULL_RADIUS_MULTIPLIER = 1.00
NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER = 1.19
NATURE_RADIAL_FULL_RADIUS_PX = NATURE_OUTER_RAY_EXTENT_PX * NATURE_RADIAL_FULL_RADIUS_MULTIPLIER
NATURE_RADIAL_OUTER_RADIUS_PX = NATURE_OUTER_RAY_EXTENT_PX * NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER
NATURE_RADIAL_FALLOFF_PX = NATURE_RADIAL_OUTER_RADIUS_PX - NATURE_RADIAL_FULL_RADIUS_PX
NATURE_RADIAL_MASK_BLUR_PX = 1.15 * RES_SCALE
NATURE_RADIAL_MASK_CANDIDATES = (
    ("smaller falloff", 1.00, 1.13),
    ("selected", NATURE_RADIAL_FULL_RADIUS_MULTIPLIER, NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER),
    ("larger falloff", 1.00, 1.24),
)
RAVEN_PRESENTATION_OUTER_RX_PX = 630.0 * RES_SCALE
RAVEN_PRESENTATION_OUTER_RY_PX = 590.0 * RES_SCALE
RAVEN_PRESENTATION_FULL_NORM = 0.78
RAVEN_PRESENTATION_BLUR_PX = 1.4 * RES_SCALE
REQUIRED_CONTEXT = (
    ARCHITECTURE_DOC,
    REVIEW_PACKET_DOC,
    REGISTRY_PATH,
    REGISTRY_NOTES_DOC,
    V004_README,
    V004_MANIFEST,
    V004_MP4,
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
    ("initial_cymatic", 0.0),
    ("wave_gather", 6.0),
    ("nature_portal", 12.2),
    ("full_nature_hold", 19.0),
    ("shared_anchor", 28.0),
    ("raven_reveal", 38.0),
    ("raven_hold", 48.0),
    ("raven_collapse", 59.0),
    ("ordered_cymatic_field", 63.0),
    ("cymatic_regather", 66.0),
    ("nature_return", 70.5),
    ("cymatic_loop_point", 80.0),
)

CONTACT_TIMES = (0.0, 6.0, 10.5, 12.5, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 42.0, 48.0, 56.0, 60.0, 64.0, 68.5, 71.5, 74.0, 78.0, 80.0)


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
    return RAVEN_NODE_W * 0.5 + px_ndc * (RAVEN_NODE_H * 0.5), RAVEN_NODE_H * 0.5 - py_ndc * (RAVEN_NODE_H * 0.5)


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
        return 0.40 + 0.42 * t
    if time_seconds < 54.0:
        t = smoothstep01((time_seconds - 44.0) / 10.0)
        return 0.82 + 0.020 * t
    if time_seconds < 62.0:
        t = smoothstep01((time_seconds - 54.0) / 8.0)
        return 0.84 + 0.012 * t
    return 0.852


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
    if time_seconds < 45.5:
        t = smoothstep01((time_seconds - 44.0) / 1.5)
        return ANCHOR_RADIUS_PX * (1.0 - t) + (ANCHOR_RADIUS_PX * 0.955) * t
    if time_seconds < 62.0:
        return ANCHOR_RADIUS_PX * 0.955
    return ANCHOR_RADIUS_PX * 0.955


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


def ray_aperture_mask() -> np.ndarray:
    cx, cy = ANCHOR_CENTER_PX
    mask = np.zeros((H, W), dtype=np.uint8)
    inner_radius = NATURE_OUTER_RAY_EXTENT_PX * 0.30
    shoulder_radius = NATURE_OUTER_RAY_EXTENT_PX * 0.55
    outer_radius = NATURE_OUTER_RAY_EXTENT_PX * 0.98
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
    return cv2.GaussianBlur(mask, (0, 0), 3.2 * RES_SCALE)


FULL_APERTURE_MASK = centered_circle_mask(NATURE_OUTER_RAY_EXTENT_PX, soft_edge=32.0 * RES_SCALE)
CENTRAL_APERTURE_MASK = centered_circle_mask(NATURE_OUTER_RAY_EXTENT_PX * 0.39, soft_edge=18.0 * RES_SCALE)
RAY_APERTURE_MASK = ray_aperture_mask()
ANCHOR_MASK = centered_circle_mask(ANCHOR_RADIUS_PX, soft_edge=18.0 * RES_SCALE)
NATURE_FULL_HOLD_MASK = None
RAVEN_PRESENTATION_MASK = None
NATURE_BLACK_DISC_MASK = None


def mask_edge(mask: np.ndarray, *, kernel_px: int = 9, blur: float = 4.2) -> np.ndarray:
    source = np.where(mask > 12, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(
        source,
        cv2.MORPH_GRADIENT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_px, kernel_px)),
    )
    return cv2.GaussianBlur(edge, (0, 0), blur)


def mask_bbox(mask: np.ndarray, *, threshold: int = 1, pad: int = 0) -> tuple[int, int, int, int] | None:
    pts = cv2.findNonZero(np.where(mask > threshold, 255, 0).astype(np.uint8))
    if pts is None:
        return None
    x, y, w, h = cv2.boundingRect(pts)
    return (
        max(0, x - pad),
        max(0, y - pad),
        min(mask.shape[1], x + w + pad),
        min(mask.shape[0], y + h + pad),
    )


def alpha_over_roi(
    frame: np.ndarray,
    layer: np.ndarray,
    alpha_mask: np.ndarray,
    alpha: float,
    *,
    bbox: tuple[int, int, int, int] | None = None,
) -> None:
    if alpha <= 0.0:
        return
    bbox = bbox if bbox is not None else mask_bbox(alpha_mask, threshold=1)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    mask_roi = alpha_mask[y0:y1, x0:x1]
    a = (mask_roi.astype(np.float32) / 255.0) * alpha
    if float(a.max()) <= 0.0:
        return
    out = frame[y0:y1, x0:x1].astype(np.float32)
    lay = layer[y0:y1, x0:x1].astype(np.float32)
    out = out * (1.0 - a[..., None]) + lay * a[..., None]
    frame[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)


def blend_mask_roi(frame: np.ndarray, mask: np.ndarray, rgb: tuple[int, int, int], alpha: float, *, glow: float = 0.0) -> None:
    if alpha <= 0.0:
        return
    pad = round(18 * RES_SCALE) if glow > 0.0 else 0
    bbox = mask_bbox(mask, threshold=1, pad=pad)
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    mask_roi = mask[y0:y1, x0:x1]
    mask_f = (mask_roi.astype(np.float32) / 255.0) * alpha
    if float(mask_f.max()) <= 0.0:
        return
    out = frame[y0:y1, x0:x1].astype(np.float32)
    color = np.array(rgb_to_bgr(rgb), dtype=np.float32)
    if glow > 0.0:
        blur = cv2.GaussianBlur(mask_roi, (0, 0), 6.0 * RES_SCALE)
        out += color * ((blur.astype(np.float32) / 255.0) * glow)[..., None]
    out = out * (1.0 - mask_f[..., None]) + color * mask_f[..., None]
    frame[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)


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
    venv_python = ROOT / "track2-deterministic" / "probes" / "3d-extrusion-2026-05-21" / ".venv" / "bin" / "python"
    if not venv_python.exists():
        raise RuntimeError(f"CairoSVG venv python not found: {venv_python}")
    subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "import cairosvg, sys; "
                "cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2], "
                "output_width=int(sys.argv[3]), output_height=int(sys.argv[3]))"
            ),
            str(spec.source_path),
            str(high_path),
            str(high_size),
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
    soft_alpha = soft_artwork_alpha(canvas_alpha, bbox, feather_px=(10.0 if spec.key == NATURE_SPEC.key else 22.0) * RES_SCALE)
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
    if time_seconds < 72.0:
        return 1.0
    if time_seconds < 78.0:
        return 1.0 - smoothstep01((time_seconds - 72.0) / 6.0)
    return 0.0


def nature_opacity(time_seconds: float) -> float:
    first_in = smoothstep01((time_seconds - 8.0) / 3.2)
    first_out = 1.0 - smoothstep01((time_seconds - 24.0) / 8.0)
    first = first_in * first_out
    if time_seconds < 8.0:
        return 0.0
    if time_seconds < 32.0:
        return clamp01(0.98 * first)
    if time_seconds < 68.0:
        return 0.0
    ret_in = smoothstep01((time_seconds - 68.0) / 3.2)
    ret_out = 1.0 - smoothstep01((time_seconds - 72.0) / 5.5)
    return clamp01(0.98 * ret_in * ret_out)


def raven_opacity(time_seconds: float) -> float:
    in_level = smoothstep01((time_seconds - 32.0) / 8.0)
    if time_seconds >= 44.0:
        in_level = 1.0
    out_level = 1.0 - smoothstep01((time_seconds - 57.0) / 5.0)
    return clamp01(in_level * out_level)


def wave_levels(time_seconds: float) -> dict[str, float]:
    n = nature_opacity(time_seconds)
    r = raven_opacity(time_seconds)
    art_dominance = clamp01(max(n * 0.82, r * 0.78))
    gather = smoothstep01((time_seconds - 0.5) / 7.5) * (1.0 - smoothstep01((time_seconds - 8.0) / 1.2))
    collapse_order = smoothstep01((time_seconds - 52.0) / 6.0) * (1.0 - smoothstep01((time_seconds - 64.0) / 4.0))
    regather = smoothstep01((time_seconds - 62.0) / 6.0) * (1.0 - smoothstep01((time_seconds - 72.0) / 5.5))
    structure = max(gather, collapse_order, regather)
    return {
        "water": clamp01(0.94 - 0.34 * art_dominance + 0.12 * collapse_order),
        "positive": clamp01(0.88 * (1.0 - 0.82 * art_dominance) + 0.18 * collapse_order + 0.10 * regather),
        "negative": clamp01(0.78 * (1.0 - 0.50 * art_dominance) + 0.14 * collapse_order + 0.08 * regather),
        "line": clamp01(0.56 + 0.22 * structure - 0.12 * art_dominance),
    }


def source_position(source: OctagonalTargetSource, time_seconds: float, coherence: float) -> tuple[float, float]:
    phase01 = (time_seconds % LOOP_SECONDS) / LOOP_SECONDS
    radius = TARGET.drift_amplitude_px * source.drift_scale * (1.0 - coherence * coherence)
    angle = TAU * (source.orbit_phase + source.orbit_cycles * phase01)
    wobble = 0.24 * math.sin(TAU * (source.perturb_cycles * phase01 + source.phase_perturb))
    return (
        source.x + radius * math.cos(angle + wobble),
        source.y + radius * math.sin(angle + wobble),
    )


def target_sources_at(time_seconds: float, coherence: float | None = None) -> list[base.WaveSource]:
    c = spine_coherence(time_seconds) if coherence is None else coherence
    phase01 = (time_seconds % LOOP_SECONDS) / LOOP_SECONDS
    locked_phase = TAU * SOURCE_FREQUENCY * 12.8 - TAU * TARGET.source_ring_radius_px / TARGET.wavelength_px
    wave_sources: list[base.WaveSource] = []
    for source in TARGET.sources:
        x, y = source_position(source, time_seconds, c)
        perturb = (1.0 - c) * 0.70 * math.sin(TAU * (source.perturb_cycles * phase01 + source.phase_perturb))
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


def render_wave_base(time_seconds: float) -> tuple[np.ndarray, list[base.WaveSource]]:
    coherence = spine_coherence(time_seconds)
    sources = target_sources_at(time_seconds, coherence)
    field = fast_evaluate_field(sources, time_seconds, blur_sigma=BLUR_SIGMA)
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
    field_small = cv2.GaussianBlur(np.sign(field_norm) * (np.abs(field_norm) ** FIELD_GAMMA), (0, 0), 0.34)
    inside = FAST_FIELD_BOUNDARY > 4
    soft = FAST_FIELD_BOUNDARY

    pos = np.where((field_small > FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    neg = np.where((field_small < -FIELD_THRESHOLD) & inside, soft, 0).astype(np.uint8)
    node = np.where((np.abs(field_small) <= NODE_EPSILON) & inside, soft, 0).astype(np.uint8)
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
    blend_mask_roi(frame, FIELD_BOUNDARY_EDGE_FULL, wave_v002.MUTED_TEAL, 0.14 * levels["line"])
    return frame


def nature_portal_levels(time_seconds: float) -> dict[str, float]:
    if 68.0 <= time_seconds <= 72.0:
        local_time = 8.0 + (time_seconds - 68.0) * 1.38
    else:
        local_time = time_seconds
    if local_time < 8.0:
        return {"central_aperture": 0.0, "ray_aperture": 0.0, "full_aperture": 0.0}
    central = smoothstep01((local_time - 8.0) / 0.9)
    rays = smoothstep01((local_time - 8.8) / 1.35)
    full = smoothstep01((local_time - 10.2) / 1.65)
    if 12.0 <= local_time <= 14.4:
        central = rays = full = 1.0
    if local_time > 14.4:
        central = rays = full = 1.0
    return {
        "central_aperture": clamp01(central),
        "ray_aperture": clamp01(rays),
        "full_aperture": clamp01(full),
    }


def portal_aperture(levels: dict[str, float], artwork_alpha: np.ndarray) -> dict[str, np.ndarray]:
    central = (CENTRAL_APERTURE_MASK.astype(np.float32) * levels["central_aperture"]).astype(np.uint8)
    rays = (RAY_APERTURE_MASK.astype(np.float32) * levels["ray_aperture"]).astype(np.uint8)
    full = (FULL_APERTURE_MASK.astype(np.float32) * levels["full_aperture"]).astype(np.uint8)
    aperture = np.maximum(np.maximum(central, rays), full)
    aperture = np.minimum(aperture, artwork_alpha)
    edge_src = np.where(aperture > 14, 255, 0).astype(np.uint8)
    edge = cv2.morphologyEx(
        edge_src,
        cv2.MORPH_GRADIENT,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)),
    )
    edge = cv2.GaussianBlur(edge, (0, 0), 5.4 * RES_SCALE)
    return {
        "central": central,
        "rays": rays,
        "full": full,
        "aperture": aperture,
        "edge": edge,
    }


def radial_falloff_mask(full_radius_px: float, outer_radius_px: float, *, blur_px: float = 0.0) -> np.ndarray:
    falloff = max(1e-6, outer_radius_px - full_radius_px)
    alpha = np.clip((outer_radius_px - DIST_FROM_ANCHOR) / falloff, 0.0, 1.0)
    alpha[DIST_FROM_ANCHOR <= full_radius_px] = 1.0
    alpha = alpha * alpha * (3.0 - 2.0 * alpha)
    mask = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    if blur_px > 0.0:
        mask = cv2.GaussianBlur(mask, (0, 0), blur_px)
    return mask


def nature_radial_hold_mask_for(
    nature: ArtworkLayer,
    full_radius_multiplier: float,
    outer_radius_multiplier: float,
) -> np.ndarray:
    full_radius = NATURE_OUTER_RAY_EXTENT_PX * full_radius_multiplier
    outer_radius = NATURE_OUTER_RAY_EXTENT_PX * outer_radius_multiplier
    radial = radial_falloff_mask(full_radius, outer_radius, blur_px=NATURE_RADIAL_MASK_BLUR_PX)
    return np.minimum(nature.alpha, radial)


def nature_full_hold_mask(nature: ArtworkLayer) -> np.ndarray:
    global NATURE_FULL_HOLD_MASK
    if NATURE_FULL_HOLD_MASK is None:
        NATURE_FULL_HOLD_MASK = nature_radial_hold_mask_for(
            nature,
            NATURE_RADIAL_FULL_RADIUS_MULTIPLIER,
            NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER,
        )
    return NATURE_FULL_HOLD_MASK


def raven_presentation_mask() -> np.ndarray:
    global RAVEN_PRESENTATION_MASK
    if RAVEN_PRESENTATION_MASK is None:
        dx = (XX - ANCHOR_CENTER_PX[0]) / RAVEN_PRESENTATION_OUTER_RX_PX
        dy = (YY - ANCHOR_CENTER_PX[1]) / RAVEN_PRESENTATION_OUTER_RY_PX
        norm = np.sqrt(dx * dx + dy * dy, dtype=np.float32)
        falloff = max(1e-6, 1.0 - RAVEN_PRESENTATION_FULL_NORM)
        alpha = np.clip((1.0 - norm) / falloff, 0.0, 1.0)
        alpha[norm <= RAVEN_PRESENTATION_FULL_NORM] = 1.0
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        mask = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
        if RAVEN_PRESENTATION_BLUR_PX > 0.0:
            mask = cv2.GaussianBlur(mask, (0, 0), RAVEN_PRESENTATION_BLUR_PX)
        RAVEN_PRESENTATION_MASK = mask
    return RAVEN_PRESENTATION_MASK


def nature_presentation_mask(nature: ArtworkLayer, mask: np.ndarray) -> np.ndarray:
    global NATURE_BLACK_DISC_MASK
    alpha = mask.copy()
    if NATURE_BLACK_DISC_MASK is None:
        luminance = (
            0.114 * nature.bgr[:, :, 0].astype(np.float32)
            + 0.587 * nature.bgr[:, :, 1].astype(np.float32)
            + 0.299 * nature.bgr[:, :, 2].astype(np.float32)
        )
        NATURE_BLACK_DISC_MASK = (DIST_FROM_ANCHOR <= ANCHOR_RADIUS_PX * 0.985) & (luminance < 34.0) & (nature.alpha > 8)
    if np.any(NATURE_BLACK_DISC_MASK):
        alpha[NATURE_BLACK_DISC_MASK] = np.clip(alpha[NATURE_BLACK_DISC_MASK].astype(np.float32) * 0.86, 0, 255).astype(np.uint8)
    return alpha


def nature_mask_at(time_seconds: float, nature: ArtworkLayer) -> tuple[np.ndarray, np.ndarray]:
    if time_seconds < 8.0 or (32.0 <= time_seconds < 68.0):
        zero = np.zeros((H, W), dtype=np.uint8)
        return zero, zero
    full_hold = nature_full_hold_mask(nature)
    portal = portal_aperture(nature_portal_levels(time_seconds), nature.alpha)
    aperture = portal["aperture"]
    edge = portal["edge"]
    if 8.0 <= time_seconds < 14.0:
        return aperture, edge
    if 14.0 <= time_seconds < 24.0:
        settle = smoothstep01((time_seconds - 14.0) / 2.4)
        mask = (
            aperture.astype(np.float32) * (1.0 - settle)
            + full_hold.astype(np.float32) * settle
        )
        return np.clip(mask, 0, 255).astype(np.uint8), (edge if settle < 0.8 else np.zeros((H, W), dtype=np.uint8))
    if 24.0 <= time_seconds < 32.0:
        collapse = smoothstep01((time_seconds - 24.0) / 8.0)
        radius = 820.0 * (1.0 - collapse) + (ANCHOR_RADIUS_PX + 18.0) * collapse
        collapse_mask = centered_circle_mask(radius, soft_edge=118.0)
        return np.minimum(full_hold, collapse_mask), np.zeros((H, W), dtype=np.uint8)
    if 68.0 <= time_seconds < 70.2:
        return aperture, edge
    if 70.2 <= time_seconds <= 72.0:
        settle = smoothstep01((time_seconds - 70.2) / 1.4)
        mask = (
            aperture.astype(np.float32) * (1.0 - settle)
            + full_hold.astype(np.float32) * settle
        )
        return np.clip(mask, 0, 255).astype(np.uint8), (edge if settle < 0.8 else np.zeros((H, W), dtype=np.uint8))
    if 72.0 < time_seconds < 78.0:
        release = smoothstep01((time_seconds - 72.0) / 5.5)
        radius = (NATURE_RADIAL_OUTER_RADIUS_PX + 34.0 * RES_SCALE) * (1.0 - release) + (ANCHOR_RADIUS_PX * 1.05) * release
        release_mask = centered_circle_mask(radius, soft_edge=170.0 * RES_SCALE)
        return np.minimum(full_hold, release_mask), np.zeros((H, W), dtype=np.uint8)
    return np.zeros((H, W), dtype=np.uint8), np.zeros((H, W), dtype=np.uint8)


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


def load_raven_spatial_frame_sampled(frame_pos: float) -> tuple[np.ndarray, dict[str, object]]:
    frame_pos = max(0.0, min(float(RAVEN_SPATIAL_TOTAL_FRAMES - 1), frame_pos))
    lo = int(math.floor(frame_pos))
    hi = min(RAVEN_SPATIAL_TOTAL_FRAMES - 1, lo + 1)
    frac = frame_pos - lo
    if hi == lo or frac <= 1e-6:
        return load_raven_spatial_frame_raw(lo).copy(), {
            "frame_pos": round(frame_pos, 4),
            "frame_lo": lo,
            "frame_hi": hi,
            "frame_blend": 0.0,
        }
    a = load_raven_spatial_frame_raw(lo).astype(np.float32)
    b = load_raven_spatial_frame_raw(hi).astype(np.float32)
    blended = np.clip(a * (1.0 - frac) + b * frac, 0, 255).astype(np.uint8)
    return blended, {
        "frame_pos": round(frame_pos, 4),
        "frame_lo": lo,
        "frame_hi": hi,
        "frame_blend": round(frac, 4),
    }


def raven_spatial_transform_norm(time_seconds: float) -> float:
    if time_seconds < 44.0:
        return clamp01(raven_spatial_node_norm(time_seconds))
    return 0.82


def raven_spatial_reveal_mask(time_seconds: float) -> np.ndarray:
    if time_seconds < 32.0:
        return np.zeros((H, W), dtype=np.uint8)
    if time_seconds < 44.0:
        progress = smoothstep01((time_seconds - 33.5) / 10.5)
        anchor_open = smoothstep01((time_seconds - 32.0) / 1.35)
        expansion_radius = ANCHOR_RADIUS_PX + progress * 930.0 * RES_SCALE
        expansion = centered_circle_mask(expansion_radius, soft_edge=150.0 * RES_SCALE)
        anchor = (ANCHOR_MASK.astype(np.float32) * anchor_open).astype(np.uint8)
        return np.maximum(anchor, expansion)
    if time_seconds < 54.0:
        return np.full((H, W), 255, dtype=np.uint8)
    if time_seconds < 62.0:
        collapse = smoothstep01((time_seconds - 54.0) / 7.5)
        radius = 1320.0 * RES_SCALE * (1.0 - collapse) + (ANCHOR_RADIUS_PX + 22.0 * RES_SCALE) * collapse
        return centered_circle_mask(radius, soft_edge=170.0 * RES_SCALE)
    return np.zeros((H, W), dtype=np.uint8)


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
    frame_pos = t_norm * (RAVEN_SPATIAL_TOTAL_FRAMES - 1)
    raw, sample_info = load_raven_spatial_frame_sampled(frame_pos)

    raw_diff = np.abs(raw.astype(np.int16) - RAVEN_SPATIAL_BG_BGR.astype(np.int16)).sum(axis=2).astype(np.float32)
    raw_source_alpha = np.clip((raw_diff - 2.0) / 24.0, 0.0, 1.0)
    raw_source_alpha = cv2.GaussianBlur(raw_source_alpha, (0, 0), 0.85)
    raw_source_alpha = np.clip(raw_source_alpha * 255.0, 0, 255).astype(np.uint8)
    if time_seconds < 44.0:
        raw_source_alpha = feather_source_boundary(raw_source_alpha, 96.0)
    elif time_seconds < 54.0:
        raw_source_alpha = feather_source_boundary(raw_source_alpha, 116.0)
    else:
        raw_source_alpha = feather_source_boundary(raw_source_alpha, 108.0)

    transform_norm = raven_spatial_transform_norm(time_seconds)
    projected_center, projected_radius = raven_spatial_anchor_projection(transform_norm)
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
    source_alpha = cv2.warpAffine(
        raw_source_alpha,
        matrix,
        (W, H),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    source_alpha = np.minimum(source_alpha, raven_presentation_mask())

    reveal = raven_spatial_reveal_mask(time_seconds)
    mask = np.minimum(source_alpha, reveal)
    if 32.0 <= time_seconds < 44.0:
        mask = cv2.GaussianBlur(mask, (0, 0), 1.65 * RES_SCALE)
    elif 44.0 <= time_seconds < 54.0:
        mask = cv2.GaussianBlur(mask, (0, 0), 0.72 * RES_SCALE)
    else:
        mask = cv2.GaussianBlur(mask, (0, 0), 1.35 * RES_SCALE)
    mask = np.clip(mask, 0, 255).astype(np.uint8)

    info = {
        "spatial_variant": "clean_frame",
        "spatial_node_norm": round(t_norm, 4),
        "spatial_transform_norm": round(transform_norm, 4),
        "sampling": sample_info,
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
    raven_collapse = smoothstep01((time_seconds - 54.0) / 2.0) * (1.0 - smoothstep01((time_seconds - 62.0) / 1.2))
    nature_return = smoothstep01((time_seconds - 68.0) / 1.2) * (1.0 - smoothstep01((time_seconds - 71.6) / 0.8))
    return clamp01(max(nature_bridge, 0.54 * portal_hold, 0.90 * raven_collapse, 0.58 * nature_return))


def portal_alignment_alpha(time_seconds: float) -> float:
    gather = smoothstep01((time_seconds - 4.5) / 3.0) * (1.0 - smoothstep01((time_seconds - 15.6) / 1.2))
    collapse = smoothstep01((time_seconds - 52.0) / 4.5) * (1.0 - smoothstep01((time_seconds - 64.0) / 2.0))
    regather = smoothstep01((time_seconds - 62.0) / 4.4) * (1.0 - smoothstep01((time_seconds - 71.5) / 0.8))
    return clamp01(max(gather, 0.92 * collapse, regather))


def raven_collapse_structure_alpha(time_seconds: float) -> float:
    return clamp01(smoothstep01((time_seconds - 51.5) / 5.0) * (1.0 - smoothstep01((time_seconds - 64.5) / 3.2)))


def draw_octagonal_axes(frame: np.ndarray, *, alpha: float) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    cx, cy = ANCHOR_CENTER_PX
    for source in TARGET.sources:
        a = source.angle_rad
        p0 = (round(cx + 36.0 * RES_SCALE * math.cos(a)), round(cy + 36.0 * RES_SCALE * math.sin(a)))
        p1 = (
            round(cx + (NATURE_OUTER_RAY_EXTENT_PX + 46.0 * RES_SCALE) * math.cos(a)),
            round(cy + (NATURE_OUTER_RAY_EXTENT_PX + 46.0 * RES_SCALE) * math.sin(a)),
        )
        cv2.line(overlay, p0, p1, rgb_to_bgr(PORTAL_GLOW), max(1, round(1.2 * RES_SCALE)), lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_source_positions(frame: np.ndarray, sources: list[base.WaveSource], *, alpha: float) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    for source in sources:
        p = (round(source.x), round(source.y))
        cv2.circle(overlay, p, round(8 * RES_SCALE), rgb_to_bgr(SOFT_GOLD), max(1, round(1.1 * RES_SCALE)), lineType=cv2.LINE_AA)
        cv2.circle(overlay, p, round(2.2 * RES_SCALE), rgb_to_bgr(SOFT_GOLD), -1, lineType=cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1.0, 0, dst=frame)


def draw_ordered_cymatic_connective_tissue(frame: np.ndarray, sources: list[base.WaveSource], time_seconds: float, alpha: float) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    cx, cy = ANCHOR_CENTER_PX
    pulse = 0.5 + 0.5 * math.sin(TAU * ((SOURCE_FREQUENCY * time_seconds) % 1.0))
    for idx, source in enumerate(TARGET.sources):
        a = source.angle_rad
        spoke_outer = SOURCE_RING_RADIUS + (34.0 + 14.0 * pulse) * RES_SCALE
        p0 = (round(cx + ANCHOR_RADIUS_PX * 0.70 * math.cos(a)), round(cy + ANCHOR_RADIUS_PX * 0.70 * math.sin(a)))
        p1 = (round(cx + spoke_outer * math.cos(a)), round(cy + spoke_outer * math.sin(a)))
        color = PORTAL_GLOW if idx % 2 == 0 else MUTED_TEAL
        cv2.line(overlay, p0, p1, rgb_to_bgr(color), max(1, round(1.4 * RES_SCALE)), lineType=cv2.LINE_AA)
    for radius in (ANCHOR_RADIUS_PX, SOURCE_RING_RADIUS, NATURE_OUTER_RAY_EXTENT_PX):
        cv2.circle(
            overlay,
            (round(cx), round(cy)),
            round(radius + 10.0 * RES_SCALE * math.sin(TAU * ((SOURCE_FREQUENCY * time_seconds) % 1.0))),
            rgb_to_bgr(SOFT_GOLD if radius == ANCHOR_RADIUS_PX else MUTED_TEAL),
            max(1, round(1.2 * RES_SCALE)),
            lineType=cv2.LINE_AA,
        )
    cv2.addWeighted(overlay, 0.16 * alpha, frame, 1.0, 0, dst=frame)
    draw_source_positions(frame, sources, alpha=0.18 * alpha)


def draw_anchor_ripples(frame: np.ndarray, time_seconds: float, alpha: float) -> None:
    if alpha <= 0.0:
        return
    overlay = np.zeros_like(frame)
    phase = (time_seconds * 0.42) % 1.0
    for idx in range(3):
        offset = (20.0 * idx + 10.0 * math.sin(TAU * (phase + idx * 0.18))) * RES_SCALE
        radius = ANCHOR_RADIUS_PX + offset
        color = PORTAL_GLOW if idx == 0 else PORTAL_ORANGE
        cv2.circle(
            overlay,
            (round(ANCHOR_CENTER_PX[0]), round(ANCHOR_CENTER_PX[1])),
            max(1, round(radius)),
            rgb_to_bgr(color),
            max(1, round((1 + (idx == 0)) * RES_SCALE)),
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
        draw_octagonal_axes(frame, alpha=0.18 * align_alpha)
        draw_source_positions(frame, sources, alpha=0.22 * align_alpha)
    collapse_structure_alpha = raven_collapse_structure_alpha(time_seconds)
    if collapse_structure_alpha > 0.0:
        draw_ordered_cymatic_connective_tissue(frame, sources, time_seconds, collapse_structure_alpha)

    nature_mask, nature_edge = nature_mask_at(time_seconds, nature)
    n_opacity = nature_opacity(time_seconds)
    if n_opacity > 0.0:
        nature_mask = nature_presentation_mask(nature, nature_mask)
        alpha_over_roi(frame, nature.bgr, nature_mask, n_opacity, bbox=tuple(nature.info["bbox_px"]))
        if float(nature_edge.max()) > 0.0:
            blend_mask_roi(frame, nature_edge, PORTAL_GLOW, 0.18 * align_alpha, glow=0.006 * align_alpha)

    ripple_alpha = anchor_ripple_alpha(time_seconds)
    draw_anchor_ripples(frame, time_seconds, ripple_alpha)

    raven_spatial_info: dict[str, object] | None = None
    if 32.0 <= time_seconds < 62.0:
        raven_bgr, raven_mask, raven_spatial_info = raven_spatial_frame_at(time_seconds)
    else:
        raven_bgr = raven.bgr
        raven_mask = np.zeros((H, W), dtype=np.uint8)
    r_opacity = raven_opacity(time_seconds)
    if r_opacity > 0.0:
        alpha_over_roi(frame, raven_bgr, raven_mask, r_opacity)
        edge_alpha = smoothstep01((time_seconds - 32.0) / 2.0) * (1.0 - smoothstep01((time_seconds - 43.0) / 1.2))
        if edge_alpha > 0.001:
            reveal_edge = mask_edge(raven_mask, kernel_px=21, blur=5.0 * RES_SCALE)
            blend_mask_roi(frame, reveal_edge, PORTAL_GLOW, 0.13 * edge_alpha, glow=0.003 * edge_alpha)

    draw_anchor_ripples(frame, time_seconds, 0.44 * ripple_alpha * (1.0 - 0.42 * r_opacity))

    info = {
        "time_seconds": round(time_seconds, 4),
        "coherence": round(spine_coherence(time_seconds), 4),
        "nature_opacity": round(n_opacity, 4),
        "raven_opacity": round(r_opacity, 4),
        "raven_collapse_structure_alpha": round(collapse_structure_alpha, 4),
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
        base.draw_text(frame, f"anchor_graph_spine_v004_1_raven_collapse_polish t={time_seconds:05.2f}", (42, 56), LABEL, scale=0.50)
    return frame, info


def save_key_stills(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, str]:
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for key, time_seconds in KEY_STILL_TIMES:
        frame, _info = render_frame(time_seconds, nature, raven)
        path = STILLS_DIR / f"anchor_graph_spine_v004_1_raven_collapse_polish_{key}.png"
        cv2.imwrite(str(path), frame)
        outputs[f"{key}_still"] = str(path.relative_to(OUT_DIR))
    peak_frame, _info = render_frame(12.8, nature, raven)
    peak_path = PEAK_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish_nature_portal_peak.png"
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
    path = OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish_contact_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def read_video_frame_at(video_path: Path, time_seconds: float) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open comparison video: {video_path}")
    frame_index = max(0, round(time_seconds * FPS))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"could not read frame {frame_index} from {video_path}")
    return frame


def labeled_panel(frame: np.ndarray, label: str, size: tuple[int, int] = (960, 540)) -> np.ndarray:
    panel = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    shade = np.zeros_like(panel)
    cv2.rectangle(shade, (0, 0), (size[0], 58), rgb_to_bgr(DEEP_GROUND), -1)
    cv2.addWeighted(shade, 0.48, panel, 1.0, 0, dst=panel)
    base.draw_text(panel, label, (22, 39), LABEL, scale=0.42)
    return panel


def make_v004_v004_1_comparison_sheet(nature: ArtworkLayer, raven: ArtworkLayer) -> Path:
    panels: list[np.ndarray] = []
    comparisons = (
        ("Raven hold", 48.0, 48.0, "stable hold, reduced global motion"),
        ("Raven collapse", 58.5, 58.5, "ordered cymatic connective tissue"),
        ("Nature return", 70.5, 70.5, "same radial Nature presentation"),
        ("Loop point", 71.5, 80.0, "v004.1 returns to matched cymatic field"),
    )
    for label_prefix, v004_time, v004_1_time, note in comparisons:
        v004 = read_video_frame_at(V004_MP4, v004_time)
        v004_1, _info = render_frame(v004_1_time, nature, raven)
        panels.append(labeled_panel(v004, f"v004 {label_prefix} t={v004_time:04.1f}s"))
        panels.append(labeled_panel(v004_1, f"v004.1 {label_prefix} t={v004_1_time:04.1f}s: {note}"))
    sheet = cv2.vconcat([cv2.hconcat(panels[i : i + 2]) for i in range(0, len(panels), 2)])
    path = OUT_DIR / "anchor_graph_spine_v004_v004_1_comparison_sheet.png"
    cv2.imwrite(str(path), sheet)
    return path


def make_timeline_panel(width: int, height: int) -> np.ndarray:
    panel = np.full((height, width, 3), rgb_to_bgr(DEEP_GROUND), dtype=np.uint8)
    segments = (
        ("wave gather", 0.0, 8.0, MUTED_TEAL),
        ("Nature portal", 8.0, 14.0, SOFT_GOLD),
        ("full Nature hold", 14.0, 24.0, (232, 184, 92)),
        ("shared sun-disc anchor", 24.0, 32.0, PORTAL_GLOW),
        ("Raven reveal", 32.0, 44.0, PORTAL_ORANGE),
        ("stable Raven hold", 44.0, 54.0, (180, 168, 130)),
        ("Raven collapse", 54.0, 62.0, PORTAL_ORANGE),
        ("ordered field", 62.0, 68.0, MUTED_TEAL),
        ("Nature return", 68.0, 72.0, SOFT_GOLD),
        ("cymatic loop settle", 72.0, 80.0, MUTED_TEAL),
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
    base.draw_text(panel, "debug timeline: v004.1 masks, ordered Raven collapse field, and loop-closure settle", (42, 44), LABEL, scale=0.42)
    return panel


def make_debug_sheet(nature: ArtworkLayer, raven: ArtworkLayer) -> Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    panel_specs = (
        ("collapse field enters under Raven", 53.0),
        ("Raven mask closing; octagonal field rising", 56.0),
        ("Raven dissolving through shared anchor", 59.0),
        ("first balanced cymatic field after Raven", 62.5),
    )
    panels: list[np.ndarray] = []
    for label, time_seconds in panel_specs:
        frame, info = render_frame(time_seconds, nature, raven, collect_info=True)
        raven_mask = np.zeros((H, W), dtype=np.uint8)
        if 32.0 <= time_seconds < 62.0:
            _raven_bgr, raven_mask, _raven_info = raven_spatial_frame_at(time_seconds)
        if np.count_nonzero(raven_mask) > 0:
            blend_mask_roi(frame, mask_edge(raven_mask, kernel_px=21, blur=6.0 * RES_SCALE), PORTAL_ORANGE, 0.50)
        cv2.circle(
            frame,
            (round(ANCHOR_CENTER_PX[0]), round(ANCHOR_CENTER_PX[1])),
            round(ANCHOR_RADIUS_PX),
            rgb_to_bgr(PORTAL_GLOW),
            max(1, round(2 * RES_SCALE)),
            lineType=cv2.LINE_AA,
        )
        panel = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, label, (14, 30), LABEL, scale=0.28)
        base.draw_text(panel, f"t={time_seconds:04.1f}s", (14, 55), LABEL, scale=0.26)
        base.draw_text(panel, f"collapse field={info['raven_collapse_structure_alpha']:.2f}", (14, 80), LABEL, scale=0.24)
        panels.append(panel)
    actual_row = cv2.hconcat(panels)

    mask_panels: list[np.ndarray] = []
    for time_seconds in (54.0, 57.5, 60.5, 62.0):
        if time_seconds < 62.0:
            _raven_bgr, raven_mask, raven_info = raven_spatial_frame_at(time_seconds)
        else:
            raven_mask = np.zeros((H, W), dtype=np.uint8)
            raven_info = {"mask_nonzero_px": 0}
        collapse_mask = raven_spatial_reveal_mask(time_seconds)
        colored_raven = cv2.applyColorMap(cv2.resize(raven_mask, (480, 270), interpolation=cv2.INTER_AREA), cv2.COLORMAP_TURBO)
        colored_collapse = cv2.applyColorMap(cv2.resize(collapse_mask, (480, 270), interpolation=cv2.INTER_AREA), cv2.COLORMAP_VIRIDIS)
        panel = cv2.addWeighted(colored_raven, 0.62, colored_collapse, 0.38, 0)
        base.draw_text(panel, f"Raven/collapse masks t={time_seconds:04.1f}s", (16, 30), LABEL, scale=0.28)
        base.draw_text(panel, f"mask px>{raven_info['mask_nonzero_px']}", (16, 55), LABEL, scale=0.24)
        mask_panels.append(panel)
    mask_row = cv2.hconcat(mask_panels)

    loop_panels: list[np.ndarray] = []
    for label, time_seconds in (("loop start", 0.0), ("settling from Nature", 74.0), ("low coherence field", 78.0), ("loop endpoint", 80.0)):
        frame, _info = render_frame(time_seconds, nature, raven)
        panel = cv2.resize(frame, (480, 270), interpolation=cv2.INTER_AREA)
        base.draw_text(panel, f"{label} t={time_seconds:04.1f}s", (16, 30), LABEL, scale=0.28)
        loop_panels.append(panel)
    loop_row = cv2.hconcat(loop_panels)

    timeline = make_timeline_panel(1920, 220)
    sheet = cv2.vconcat([actual_row, mask_row, loop_row, timeline])
    path = DEBUG_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish_debug_masks_timeline.png"
    cv2.imwrite(str(path), sheet)
    return path


def timeline_time_for_frame(frame_idx: int) -> float:
    if N_FRAMES <= 1:
        return 0.0
    return (frame_idx / (N_FRAMES - 1)) * DURATION_SECONDS


def render_clip(nature: ArtworkLayer, raven: ArtworkLayer) -> dict[str, object]:
    output_path = OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish.mp4"
    writer = H264Writer(output_path, fps=FPS, size=(W, H))
    peak_info: dict[str, object] | None = None
    try:
        for frame_idx in range(N_FRAMES):
            time_seconds = timeline_time_for_frame(frame_idx)
            collect = frame_idx == round(12.8 * FPS)
            frame, info = render_frame(time_seconds, nature, raven, collect_info=collect)
            writer.write(frame)
            if frame_idx == round(12.8 * FPS):
                peak_info = info
            if (frame_idx + 1) % FPS == 0:
                print(f"  anchor_graph_spine_v004_1_raven_collapse_polish.mp4 {frame_idx + 1}/{N_FRAMES}", flush=True)
    finally:
        writer.close()
    if peak_info is None:
        _frame, peak_info = render_frame(12.8, nature, raven, collect_info=True)
    return {
        "filename": "anchor_graph_spine_v004_1_raven_collapse_polish.mp4",
        "mp4": str(output_path.relative_to(OUT_DIR)),
        "duration_seconds": DURATION_SECONDS,
        "fps": FPS,
        "frame_count": N_FRAMES,
        "loop_frame_time_mapping": "frame_idx/(frame_count-1)*duration; final encoded frame is sampled at exactly 80.0s for frame-0/final-frame equality",
        "peak_time_seconds": 12.8,
        "peak_info": peak_info,
    }


def read_video_frame_index(video_path: Path, frame_index: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"could not open video: {video_path}")
    frame_index = max(0, frame_index)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"could not read frame index {frame_index} from {video_path}")
    return frame


def mean_abs_diff(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))


def verify_source_loop_closure() -> dict[str, object]:
    sources_start = target_sources_at(0.0, spine_coherence(0.0))
    sources_end = target_sources_at(DURATION_SECONDS, spine_coherence(DURATION_SECONDS))
    max_position_delta = 0.0
    max_phase_delta = 0.0
    for start, end in zip(sources_start, sources_end, strict=True):
        max_position_delta = max(max_position_delta, math.hypot(start.x - end.x, start.y - end.y))
        phase_delta = abs(((start.phase - end.phase + math.pi) % TAU) - math.pi)
        max_phase_delta = max(max_phase_delta, phase_delta)
    frequency_cycles = SOURCE_FREQUENCY * DURATION_SECONDS
    return {
        "source_positions_match": max_position_delta < 1e-5,
        "source_phases_match_mod_tau": max_phase_delta < 1e-5,
        "max_source_position_delta_px": round(max_position_delta, 8),
        "max_source_phase_delta_rad": round(max_phase_delta, 8),
        "frequency_hz": SOURCE_FREQUENCY,
        "frequency_cycles_over_clip": frequency_cycles,
        "frequency_cycles_integer": abs(frequency_cycles - round(frequency_cycles)) < 1e-9,
    }


def make_loop_diagnostic_sheet(
    nature: ArtworkLayer,
    raven: ArtworkLayer,
    clip_summary: dict[str, object],
) -> tuple[Path, dict[str, object]]:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = OUT_DIR / clip_summary["mp4"]
    first = read_video_frame_index(video_path, 0)
    second = read_video_frame_index(video_path, 1)
    pre_final = read_video_frame_index(video_path, N_FRAMES - 2)
    final = read_video_frame_index(video_path, N_FRAMES - 1)

    cv2.imwrite(str(LOOP_DIR / "frame_0000_extracted.png"), first)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 1:04d}_final_extracted.png"), final)
    cv2.imwrite(str(LOOP_DIR / f"frame_{N_FRAMES - 2:04d}_pre_final_extracted.png"), pre_final)

    seam_mad = mean_abs_diff(first, final)
    start_adjacent_mad = mean_abs_diff(first, second)
    end_adjacent_mad = mean_abs_diff(pre_final, final)
    normal_adjacent_reference = (start_adjacent_mad + end_adjacent_mad) * 0.5

    raw_first, _ = render_frame(0.0, nature, raven)
    raw_final, _ = render_frame(DURATION_SECONDS, nature, raven)
    raw_seam_mad = mean_abs_diff(raw_first, raw_final)
    source_loop = verify_source_loop_closure()

    panels = [
        labeled_panel(first, "extracted frame 0 / loop start"),
        labeled_panel(final, f"extracted final frame {N_FRAMES - 1} / sampled at 80.0s"),
        labeled_panel(second, f"adjacent reference frame 1 MAD from start={start_adjacent_mad:.4f}"),
        labeled_panel(pre_final, f"adjacent reference frame {N_FRAMES - 2} MAD to final={end_adjacent_mad:.4f}"),
    ]
    sheet = cv2.vconcat([cv2.hconcat(panels[:2]), cv2.hconcat(panels[2:])])
    base.draw_text(
        sheet,
        f"decoded seam MAD={seam_mad:.4f}; adjacent reference mean={normal_adjacent_reference:.4f}; raw seam MAD={raw_seam_mad:.6f}",
        (32, sheet.shape[0] - 32),
        LABEL,
        scale=0.42,
    )
    path = LOOP_DIR / "anchor_graph_spine_v004_1_loop_diagnostic_sheet.png"
    cv2.imwrite(str(path), sheet)
    verification = {
        "frame_0_extracted": str((LOOP_DIR / "frame_0000_extracted.png").relative_to(OUT_DIR)),
        "final_frame_extracted": str((LOOP_DIR / f"frame_{N_FRAMES - 1:04d}_final_extracted.png").relative_to(OUT_DIR)),
        "pre_final_frame_extracted": str((LOOP_DIR / f"frame_{N_FRAMES - 2:04d}_pre_final_extracted.png").relative_to(OUT_DIR)),
        "decoded_frame0_final_mean_abs_diff": round(seam_mad, 6),
        "decoded_frame0_frame1_mean_abs_diff": round(start_adjacent_mad, 6),
        "decoded_pre_final_final_mean_abs_diff": round(end_adjacent_mad, 6),
        "decoded_adjacent_reference_mean_abs_diff": round(normal_adjacent_reference, 6),
        "decoded_loop_seam_less_than_adjacent_reference": seam_mad < normal_adjacent_reference,
        "raw_render_frame0_final_mean_abs_diff": round(raw_seam_mad, 8),
        "raw_render_loop_seam_exact": raw_seam_mad < 1e-7,
        "source_phase_closure": source_loop,
    }
    return path, verification


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
    loop_diagnostic_path: Path | None,
    loop_verification: dict[str, object],
    provenance_note: Path,
) -> Path:
    anchors = input_status["anchors"]
    manifest = {
        "project": "anchor_graph_spine_v004_1_raven_collapse_polish",
        "status": "internal_only_pending_austin_review",
        "boundary": "Internal only. Pending Austin review. No public/show/projector/sponsor/social/press use. No cultural-meaning claims. No motif extraction. No atom decomposition. No source recoloring. No new SVG assets.",
        "renderer": "scripts/anchor_graph_spine_v004_1_raven_collapse_polish.py",
        "renderer_sha256": sha256(ROOT / "scripts" / "anchor_graph_spine_v004_1_raven_collapse_polish.py"),
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolution": [W, H],
        "fps": FPS,
        "duration_seconds": DURATION_SECONDS,
        "frame_count": N_FRAMES,
        "target_format": "3840x2160 UHD, 16:9, 24fps",
        "baseline": {
            "v004_renderer": "scripts/anchor_graph_spine_v004_round_nature_mask.py",
            "v004_output_dir": str(V004_OUTPUT_DIR.relative_to(ROOT)),
            "v004_mp4": str(V004_MP4.relative_to(ROOT)),
        },
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
            "integration_method": "The clean-frame Raven spatial frames are composited through source-alpha and source-aligned reveal/collapse masks. The reveal is anchor-locked to the shared sun-disc radius; the hold uses a tighter monotonic frame range and a frozen projection transform to reduce residual slide/zoom.",
            "anchor_stabilization": {
                "target_center_px": list(ANCHOR_CENTER_PX),
                "reveal_target_radius_px": ANCHOR_RADIUS_PX,
                "hold_target_radius_px": round(ANCHOR_RADIUS_PX * 0.955, 3),
                "hold_transform_policy": "freeze projection transform at spatial-node norm 0.82; hold/collapse frame sample is monotonic and narrowed from norm 0.82 to 0.852, with only a 4.5% target-radius settle after reveal",
                "basis": "Projection of the Raven back-tier sun-disc center/radius from the spatial-node camera model; anchors remain metadata only.",
            },
            "debug_text_in_main_mp4": False,
        },
        "opacity_and_blend_settings": {
            "nature_global_opacity_max": 0.98,
            "nature_dark_disc_presentation_alpha_multiplier": 0.86,
            "nature_dark_disc_note": "v004 preserves v003 CairoSVG rasterization so the full authored yellow center remains source-faithful; the multiplier remains active for genuinely dark source pixels, but the v002 black center was an ImageMagick fill-none artifact rather than a source-faithful disc.",
            "nature_full_hold_mask": "whole-source alpha multiplied by a circular/radial presentation mask centered on the Nature sun-disc anchor; no square raster-bounds feather is used for the full hold or final return",
            "nature_radial_presentation_mask": {
                "source_anchor_id": "nature_cosmic_sun.central_sun_disc",
                "center_px": list(ANCHOR_CENTER_PX),
                "outer_ray_radius_viewbox": NATURE_OUTER_RAY_RADIUS_VIEWBOX,
                "outer_ray_extent_px": round(NATURE_OUTER_RAY_EXTENT_PX, 3),
                "full_strength_radius_px": round(NATURE_RADIAL_FULL_RADIUS_PX, 3),
                "full_strength_radius_multiplier_of_outer_ray": NATURE_RADIAL_FULL_RADIUS_MULTIPLIER,
                "outer_fade_radius_px": round(NATURE_RADIAL_OUTER_RADIUS_PX, 3),
                "outer_fade_radius_multiplier_of_outer_ray": NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER,
                "falloff_px": round(NATURE_RADIAL_FALLOFF_PX, 3),
                "edge_blur_px": NATURE_RADIAL_MASK_BLUR_PX,
                "used_for_initial_hold_seconds": [14.0, 32.0],
                "used_for_return_seconds": [70.2, 72.0],
                "presentation_only": True,
                "source_pixels_recolored": False,
            },
            "nature_rasterizer": "CairoSVG via the existing Raven spatial-node venv; chosen because ImageMagick filled SVG fill:none regions black in v002",
            "raven_spatial_source_alpha": "computed from difference against the clean-frame node background, with boundary feathering; RGB unchanged",
            "raven_presentation_mask": {
                "type": "wide elliptical falloff",
                "center_px": list(ANCHOR_CENTER_PX),
                "outer_rx_px": round(RAVEN_PRESENTATION_OUTER_RX_PX, 3),
                "outer_ry_px": round(RAVEN_PRESENTATION_OUTER_RY_PX, 3),
                "full_strength_norm": RAVEN_PRESENTATION_FULL_NORM,
                "edge_blur_px": RAVEN_PRESENTATION_BLUR_PX,
                "purpose": "presentation-only suppression of the clean-frame node's rectangular sky/background bounds; source RGB is unchanged and the whole Raven source remains the artwork input",
            },
            "cymatic_content": "abstract generated water/cymatic atmosphere only",
        },
        "collapse_field_parameters": {
            "ordered_cymatic_enter_seconds": [51.5, 56.5],
            "ordered_cymatic_exit_seconds": [64.5, 67.7],
            "source_count": TARGET.source_count,
            "source_ring_radius_px": round(TARGET.source_ring_radius_px, 3),
            "source_wavelength_px": round(TARGET.wavelength_px, 3),
            "frequency_hz": SOURCE_FREQUENCY,
            "frequency_cycles_over_clip": SOURCE_FREQUENCY * DURATION_SECONDS,
            "field_periodic_over_clip": True,
            "notes": "Raven exit brings in the same C8 source geometry underneath the spatial node before the Raven mask closes, so the first fully non-Raven field is centered and structurally related to the later Nature regather.",
        },
        "loop_closure_verification": loop_verification,
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
                "time_seconds": [8.0, 14.0],
                "edge_type": "wave_to_artwork",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "strongest_alignment_hold_seconds": [12.0, 14.0],
            },
            {
                "segment": "full Nature Cosmic Sun authored artwork hold",
                "time_seconds": [14.0, 24.0],
                "edge_type": "artwork_hold",
                "anchors_used": ["nature_cosmic_sun.central_sun_disc"],
                "notes": "Transitions out of the portal aperture into the whole source artwork, including the authored yellow sun disc, outward rays, and cream background. v004 replaces the v003 square raster-bounds feather with the shared radial presentation mask so the cream corners recede into the cymatic field.",
            },
            {
                "segment": "Nature collapses to shared sun-disc anchor",
                "time_seconds": [24.0, 32.0],
                "edge_type": "artwork_to_anchor_collapse",
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
                "segment": "Raven collapses through sun-disc anchor to cymatic/water field",
                "time_seconds": [54.0, 62.0],
                "edge_type": "artwork_to_wave_atmosphere",
                "anchors_used": ["animal_bird_raven_sun.central_sun_disc"],
                "transition_method": "Raven clean-frame source-alpha mask closes toward the shared sun-disc radius while the ordered C8 cymatic field rises under it.",
            },
            {
                "segment": "ordered cymatic field regathers into Nature alignment",
                "time_seconds": [62.0, 68.0],
                "edge_type": "wave_target_gather",
                "anchors_used": ["nature_cosmic_sun.eight_ray_radial_aperture_structure"],
            },
            {
                "segment": "Nature Cosmic Sun return",
                "time_seconds": [68.0, 72.0],
                "edge_type": "wave_to_artwork_return",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "return_choice": "portal return resolves into full Nature by the end; chosen because the loop is validating whole-artwork reveal rather than only an aperture endpoint.",
            },
            {
                "segment": "Nature dissolves to cymatic loop point",
                "time_seconds": [72.0, 80.0],
                "edge_type": "artwork_to_loop_closed_wave_atmosphere",
                "anchors_used": ["nature_cosmic_sun.central_sun_disc"],
                "loop_method": "Nature opacity falls to zero while source positions, source phases, and field frequency return exactly to the t=0 cymatic state. The final encoded frame is sampled at 80.0s.",
            },
        ],
        "tested_edges": [
            {
                "edge_id": "wave_to_nature_cosmic_sun_spine_v004_1",
                "edge_type": "wave_to_artwork",
                "status": "internal_composition_pass",
                "source_node": "wave_octagonal_c8",
                "target_node": "nature_cosmic_sun",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish.mp4").relative_to(ROOT)),
                "caveats": [
                    "No cultural-meaning claim.",
                    "Alignment is positional/radial, not a claim that the wave field reproduces Austin forms.",
                ],
            },
            {
                "edge_id": "nature_cosmic_sun_to_raven_sun_spine_v004_1",
                "edge_type": "artwork_to_artwork",
                "status": "internal_composition_pass_pending_austin_review",
                "source_node": "nature_cosmic_sun",
                "target_node": "animal_bird_raven_sun",
                "anchors_used": [
                    "nature_cosmic_sun.central_sun_disc",
                    "animal_bird_raven_sun.central_sun_disc",
                ],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish.mp4").relative_to(ROOT)),
                "caveats": [
                    "Transition uses whole-source alignment, source-alpha masks, and the clean-frame spatial node.",
                    "Austin review is required before any public or show use.",
                ],
            },
            {
                "edge_id": "raven_sun_to_cymatic_to_nature_return_spine_v004_1",
                "edge_type": "artwork_to_wave_atmosphere",
                "status": "internal_composition_pass",
                "source_node": "animal_bird_raven_sun",
                "target_node": "nature_cosmic_sun",
                "anchors_used": [
                    "animal_bird_raven_sun.central_sun_disc",
                    "nature_cosmic_sun.central_sun_disc",
                    "nature_cosmic_sun.eight_ray_radial_aperture_structure",
                ],
                "artifact_path": str((OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish.mp4").relative_to(ROOT)),
                "caveats": [
                    "Return cue is a presentation ripple and C8 gather, not a reusable extracted sun motif.",
                    "The generated connective field is abstract cymatic/water atmosphere, not a generated Coast Salish design.",
                ],
            },
        ],
        "clip": clip_summary,
        "deliverables": {
            "mp4": clip_summary["mp4"],
            "contact_sheet": str(contact_path.relative_to(OUT_DIR)),
            "v004_v004_1_comparison_sheet": str(comparison_path.relative_to(OUT_DIR)),
            "debug_masks_timeline_sheet": str(debug_path.relative_to(OUT_DIR)),
            "loop_diagnostic_sheet": str(loop_diagnostic_path.relative_to(OUT_DIR)) if loop_diagnostic_path is not None else None,
            "source_provenance_note": str(provenance_note.relative_to(OUT_DIR)),
            "readme": "README.md",
            **stills,
        },
    }
    path = OUT_DIR / "anchor_graph_spine_v004_1_raven_collapse_polish_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def write_readme(nature: ArtworkLayer, raven: ArtworkLayer, clip_summary: dict[str, object], loop_verification: dict[str, object]) -> Path:
    lines = [
        "# Anchor Graph Spine v004.1 Raven Collapse Polish",
        "",
        "Status: INTERNAL ONLY. Pending Austin review. Not approved for public, show, projector, sponsor, social, press, or external use. No cultural-meaning claim.",
        "",
        "## Purpose",
        "",
        "This packet parks the current spine as a finished internal UHD video checkpoint for Resolume review/use pending Austin approval. It preserves v004's successful radial Nature presentation, reduces Raven hold motion, turns the Raven exit into an ordered cymatic collapse, and adds an 80 second loop closure back to the exact starting cymatic state.",
        "",
        "Austin's source SVGs remain whole authored artworks. The shared sun-disc and eight-ray records are alignment metadata only. They are not renderable primitives, extracted motifs, atom records, or new SVG assets. The generated content is only abstract cymatic/water atmosphere.",
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
        "- 0-8s: cymatic/water atmosphere gathers into the 8-source octagonal structure.",
        "- 8-14s: Nature Cosmic Sun opens through the center/ray aperture.",
        "- 14-24s: full `Nature_Cosmic_Sun.svg` authored artwork resolves and holds through the v004 radial whole-source presentation mask.",
        "- 24-32s: Nature collapses from the same radial mask toward the shared sun-disc anchor.",
        "- 32-44s: Raven Sun emerges through the shared sun-disc anchor using the clean-frame spatial treatment.",
        "- 44-54s: Raven spatial hold keeps the global anchor transform frozen and narrows the monotonic clean-frame sample range.",
        "- 54-62s: Raven collapses through the sun-disc anchor while the ordered/octagonal cymatic field rises underneath.",
        "- 62-68s: ordered cymatic field regathers into the 8-source Nature alignment.",
        "- 68-72s: Nature portal return resolves into full Nature through the same radial mask used in the initial hold.",
        "- 72-80s: Nature dissolves back to the fully cymatic loop point.",
        "",
        "## Nature Radial Mask",
        "",
        f"- Outer ray extent from registry/source geometry: `{NATURE_OUTER_RAY_EXTENT_PX:.1f}px`.",
        f"- Full-strength radius: `{NATURE_RADIAL_FULL_RADIUS_PX:.1f}px` (`{NATURE_RADIAL_FULL_RADIUS_MULTIPLIER:.2f}x` outer ray extent).",
        f"- Outer fade radius: `{NATURE_RADIAL_OUTER_RADIUS_PX:.1f}px` (`{NATURE_RADIAL_OUTER_RADIUS_MULTIPLIER:.2f}x` outer ray extent).",
        f"- Falloff width: `{NATURE_RADIAL_FALLOFF_PX:.1f}px`, plus `{NATURE_RADIAL_MASK_BLUR_PX:.2f}px` Gaussian smoothing.",
        "- The mask is presentation-only: source RGB is unchanged, the whole source raster remains the artwork layer, and the corners fade so cymatic motion remains visible outside and under the falloff.",
        "",
        "## Loop Closure",
        "",
        f"- Duration: `{DURATION_SECONDS:.1f}s`, `{N_FRAMES}` frames at `{FPS}` fps.",
        f"- Snapped field frequency: `{SOURCE_FREQUENCY:.6f} Hz`, `{SOURCE_FREQUENCY * DURATION_SECONDS:.0f}` complete cycles over the clip.",
        f"- Decoded frame 0/final MAD: `{loop_verification.get('decoded_frame0_final_mean_abs_diff', 'n/a')}`.",
        f"- Adjacent-frame reference MAD: `{loop_verification.get('decoded_adjacent_reference_mean_abs_diff', 'n/a')}`.",
        f"- Seam less than adjacent reference: `{loop_verification.get('decoded_loop_seam_less_than_adjacent_reference', 'n/a')}`.",
        f"- Raw render frame 0/final MAD: `{loop_verification.get('raw_render_frame0_final_mean_abs_diff', 'n/a')}`.",
        "",
        "## Deliverables",
        "",
        "- `anchor_graph_spine_v004_1_raven_collapse_polish.mp4`: 3840x2160, 24 fps, 80 seconds.",
        "- `anchor_graph_spine_v004_1_raven_collapse_polish_contact_sheet.png`: labeled timestamp sequence sheet.",
        "- `anchor_graph_spine_v004_v004_1_comparison_sheet.png`: v004/v004.1 comparison focused on Raven hold/collapse, Nature return, and loop point.",
        "- `loop_diagnostics/anchor_graph_spine_v004_1_loop_diagnostic_sheet.png`: frame 0/final and adjacent-frame seam diagnostic.",
        "- `debug_stills/anchor_graph_spine_v004_1_raven_collapse_polish_debug_masks_timeline.png`: Raven collapse masks and timing sheet.",
        "- `anchor_graph_spine_v004_1_raven_collapse_polish_manifest.json`: sources, hashes, anchors, timings, collapse-field parameters, Raven stabilization, loop verification, and boundary flags.",
        "- `SOURCE_PROVENANCE.md`: local source provenance and boundary note.",
        "",
        "## Honest Verdict",
        "",
        "v004.1 keeps the v004 Nature improvement: the Nature hold still reads as a round/radial authored artwork presentation rather than a square card, and the full artwork remains visible.",
        "",
        "The Raven hold is calmer than v004. The global anchor transform is frozen during hold/collapse and the clean-frame sampling range is narrower, so the Raven reads less like a card sliding or zooming. There is still internal motion from the pre-rendered 1080p clean-frame node; this render is native UHD overall, but the Raven spatial node itself remains a 1920x1080 source input.",
        "",
        "The Raven exit is structurally better: the octagonal cymatic field appears beneath Raven before the mask closes, and the first non-Raven field is centered and related to the Nature regather. The final 8 seconds deliberately park the spine back at the same cymatic state as frame 0. The decoded seam metric is below a normal adjacent-frame step, so this should be treated as the solo spine endpoint and parked for the Austin conversation.",
        "",
        "This remains a technical/aesthetic internal study. It does not claim the shared anchor has cultural meaning, and it is not cleared for public, projector, sponsor, press, social, or show use. Austin review is required before any external use.",
        "",
        "Renderer: `scripts/anchor_graph_spine_v004_1_raven_collapse_polish.py`",
        f"Clip summary: `{clip_summary['filename']}`",
    ]
    path = OUT_DIR / "README.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render anchor graph spine v004.1 Raven collapse polish.")
    parser.add_argument("--preview", action="store_true", help="Write still/debug artifacts without rendering MP4.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    PEAK_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
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
    comparison_path = make_v004_v004_1_comparison_sheet(nature, raven)
    debug_path = make_debug_sheet(nature, raven)
    loop_diagnostic_path: Path | None = None

    if args.preview:
        _frame, peak_info = render_frame(12.8, nature, raven, collect_info=True)
        raw_first, _ = render_frame(0.0, nature, raven)
        raw_final, _ = render_frame(DURATION_SECONDS, nature, raven)
        raw_seam_mad = mean_abs_diff(raw_first, raw_final)
        loop_verification = {
            "preview_only": True,
            "decoded_frame0_final_mean_abs_diff": None,
            "decoded_adjacent_reference_mean_abs_diff": None,
            "decoded_loop_seam_less_than_adjacent_reference": None,
            "raw_render_frame0_final_mean_abs_diff": round(raw_seam_mad, 8),
            "raw_render_loop_seam_exact": raw_seam_mad < 1e-7,
            "source_phase_closure": verify_source_loop_closure(),
        }
        clip_summary = {
            "filename": "anchor_graph_spine_v004_1_raven_collapse_polish.mp4",
            "mp4": "anchor_graph_spine_v004_1_raven_collapse_polish.mp4",
            "duration_seconds": DURATION_SECONDS,
            "fps": FPS,
            "frame_count": N_FRAMES,
            "loop_frame_time_mapping": "frame_idx/(frame_count-1)*duration; final encoded frame is sampled at exactly 80.0s for frame-0/final-frame equality",
            "peak_time_seconds": 12.8,
            "peak_info": peak_info,
        }
    else:
        print("Rendering anchor_graph_spine_v004_1_raven_collapse_polish.mp4", flush=True)
        clip_summary = render_clip(nature, raven)
        print("Writing loop diagnostic sheet and seam metrics", flush=True)
        loop_diagnostic_path, loop_verification = make_loop_diagnostic_sheet(nature, raven, clip_summary)

    manifest = write_manifest(
        input_status,
        nature,
        raven,
        clip_summary,
        stills,
        contact_path,
        comparison_path,
        debug_path,
        loop_diagnostic_path,
        loop_verification,
        provenance_note,
    )
    readme = write_readme(nature, raven, clip_summary, loop_verification)
    print(f"Wrote {OUT_DIR / clip_summary['mp4']}", flush=True)
    print(f"Wrote {contact_path}", flush=True)
    print(f"Wrote {comparison_path}", flush=True)
    print(f"Wrote {debug_path}", flush=True)
    if loop_diagnostic_path is not None:
        print(f"Wrote {loop_diagnostic_path}", flush=True)
    print(f"Wrote {manifest}", flush=True)
    print(f"Wrote {readme}", flush=True)


if __name__ == "__main__":
    main()
