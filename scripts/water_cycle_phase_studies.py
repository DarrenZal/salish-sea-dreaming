#!/usr/bin/env python3.11
"""
Water-cycle phase studies v001.

Worker Task 1 of the water-cycle continuum orchestration plan
(docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md,
Section 5). Renders the seven isolated water-cycle phase studies as
black-screen layer-only clips:

  phase1_sun_radiant, phase2_vapor_mist, phase3_rain_onset,
  phase4_raindrops_on_water, phase5_standing_wave, phase6_snowflake,
  phase7_melt_return

This script EXTENDS the v003 renderer. It imports the v003 scalar-field
engine, cell classifier, canonical-primitive machinery, cell tracker, and
debug-layer functions; it does not edit v003's script or its output folder.
Each phase is a configuration of the source list (Section 6 per-phase
parameter table). Cells are classified from the stable field F(x,y), never
from the animated display - v003's `extract_cells` classifies the connected
components of the standing field every frame; the phase studies keep each
phase's source layout fixed within its render window so F's topology is
stable for that window (taxonomy doc Section 1).

Status: INTERNAL ONLY. Not Austin-approved, not public-use guidance, and not
a cultural-meaning claim. Internal R&D until Austin per-output review.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# Import the v003 field engine, classifier, and canonical-primitive machinery.
# v003 is import-safe: all execution is gated behind `if __name__ == "__main__"`.
import sys as _sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_SCRIPTS_DIR))

import cymatic_field_topology_v003 as v003  # noqa: E402

# Engine pieces reused verbatim from v003.
WaveSource = v003.WaveSource
CellRecord = v003.CellRecord
RenderCell = v003.RenderCell
CanonicalPrimitive = v003.CanonicalPrimitive
ExtractionResult = v003.ExtractionResult
CellTracker = v003.CellTracker
LoopSpec = v003.LoopSpec
evaluate_field = v003.evaluate_field
extract_cells = v003.extract_cells
select_render_cells = v003.select_render_cells
render_canonical_beauty = v003.render_canonical_beauty
audit_entry = v003.audit_entry
impact_envelope = v003.impact_envelope
draw_text = v003.draw_text
grayscale_layer = v003.grayscale_layer
nodal_layer = v003.nodal_layer
regions_layer = v003.regions_layer
classes_layer = v003.classes_layer
source_layer = v003.source_layer
source_to_json = v003.source_to_json
cell_to_json = v003.cell_to_json
clamp01 = v003.clamp01
smoothstep = v003.smoothstep
TAU = v003.TAU
LABEL = v003.LABEL

ROOT = _SCRIPTS_DIR.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_cycle_phase_studies_v001_2026-05-20"
)
DEBUG_DIR = OUT_DIR / "debug_stills"

W = v003.W
H = v003.H
FPS = v003.FPS

# Section 7 of the plan / Section 6 schema: render on near-black #05070b so the
# layer composites additive/screen blend in Resolume over the production-floor
# footage. v003 rendered on pure black (0,0,0); the phase studies use #05070b.
BACKGROUND_BGR = (0x0B, 0x07, 0x05)  # #05070b in B,G,R


@dataclass(frozen=True)
class PhaseSpec:
    """A water-cycle phase study. Wraps a v003 LoopSpec plus phase metadata."""

    key: str
    order: int
    filename: str
    duration_seconds: float
    visual_read: str
    symmetry_order: str
    mode: str
    dominant_taxonomy: tuple[str, ...]
    source_regime: str
    austin_risk: str
    loop: LoopSpec


# ---------------------------------------------------------------------------
# Per-phase source builders.
#
# Each builder takes the phase fraction (0..1 over the clip) and returns a
# WaveSource list. The plan's Section 6 per-phase table fixes symmetry_order,
# mode, dominant_taxonomy, and source regime; the builders below encode that.
#
# mode strings drive three v003 behaviours:
#   - "sixfold_radial"   -> angular modulation 1 + alpha*cos(6*theta)
#   - "impact"           -> attack/decay envelope (used for rain droplets)
#   - "radial_continuous"/"sixfold_radial" -> counted in origin-circle
#                            classification (nearest_active_source_distance)
# Within each phase the source LAYOUT is held fixed (positions, count) so the
# stable field F(x,y) topology does not change during the clip; only the
# global wave phase advances. This satisfies the taxonomy doc Section 1
# "classify from stable F, never animated Z" requirement.
# ---------------------------------------------------------------------------

CX = W / 2.0
CY = H / 2.0


def phase1_sun_radiant_sources(phase: float) -> list[WaveSource]:
    """One central emitter, sixfold radial blend, steady breathing envelope.

    Section 3 Phase 1 / Section 6: symmetry_order 0 (->6 blend), mode radial,
    1 centre steady. A slow breathing amplitude reads as a calm radiant orb.
    A low sixfold angular term gives a few attached curved trigon releases at
    selected lobes without detached rays.
    """
    breathe = 1.0 + 0.06 * math.sin(TAU * phase)
    return [
        WaveSource(
            source_id="sun_centre",
            x=CX,
            y=CY,
            amplitude=1.0 * breathe,
            wavelength=v003.SUN_WAVELENGTH,
            frequency=1.0 / DURATION_FOR(1),
            phase=0.0,
            # decay is the falloff LENGTH in px (exp(-distance/decay)); it must
            # be large so the radial field reaches across the frame. v003's own
            # sun source uses 920.0; a small decay collapses F to ~0 everywhere.
            decay=920.0,
            velocity=(0.0, 0.0),
            birth_time=0.0,
            lifetime=DURATION_FOR(1),
            symmetry_order=6,
            mode="sixfold_radial",
            # Low angular alpha: a hint of sixfold lobing for attached
            # curved-trigon releases, well below v003's sun-canary 0.70 so
            # this stays a calm radiant field, not a hard six-ray star.
            angular_alpha=0.34,
        )
    ]


def phase2_vapor_mist_sources(phase: float) -> list[WaveSource]:
    """Weak multi-emitter network, low amplitude, high decay, slow upward drift.

    Section 3 Phase 2 / Section 6: symmetry_order 0, mode network, 3-7 weak
    emitters drifting upward. Five emitters (within the 3-7 cap). Decay is
    high (small decay length) so contrast stays the lowest in the loop.
    Upward drift is encoded as a slow y-rise of the whole layout; the layout
    shape (relative spacing) is held fixed so F topology stays stable.
    """
    rise = 60.0 * phase  # whole network drifts up slowly
    layout = [
        (-340.0, 70.0),
        (-150.0, -40.0),
        (60.0, 90.0),
        (250.0, -30.0),
        (400.0, 110.0),
    ]
    freq = 1.0 / DURATION_FOR(2)
    sources: list[WaveSource] = []
    for idx, (dx, dy) in enumerate(layout):
        sources.append(
            WaveSource(
                f"mist_emitter_{idx:02d}",
                CX + dx,
                CY + dy - rise,
                0.52 + 0.05 * math.sin(idx * 1.3),  # low amplitude
                246.0 + (idx % 3) * 20.0,
                freq,
                idx * 0.55,
                300.0 + 40.0 * (idx % 3),  # high decay -> short reach -> low contrast
                (0.0, 0.0),
                0.0,
                DURATION_FOR(2),
                0,
                "network",
            )
        )
    return sources


# Rain-onset droplet schedule: (birth_s, x, y, wavelength, lifetime_s).
# 3-7 concurrent at any time; staggered births; short lifetimes; downward
# read comes from each drop being a short-lived descending impulse source.
RAIN_ONSET_DROPS: tuple[tuple[float, float, float, float, float], ...] = (
    (0.20, 540.0, 300.0, 150.0, 2.10),
    (0.95, 980.0, 250.0, 158.0, 2.00),
    (1.70, 1360.0, 330.0, 146.0, 1.95),
    (2.55, 720.0, 600.0, 162.0, 2.20),
    (3.40, 1180.0, 560.0, 154.0, 2.05),
    (4.20, 470.0, 470.0, 150.0, 2.00),
    (5.00, 1500.0, 640.0, 156.0, 1.90),
)


def phase3_rain_onset_sources(phase: float) -> list[WaveSource]:
    """Short-lived impulse emitters with staggered birth, downward read.

    Section 3 Phase 3 / Section 6: symmetry_order 0, mode impulse, 3-7
    short-lived emitters. Each drop is a discrete impact source; the impact
    envelope (v003.impact_envelope) gives the appear/fall/attenuate read.
    """
    time_seconds = phase * DURATION_FOR(3)
    sources: list[WaveSource] = []
    for idx, (birth, x, y, wavelength, lifetime) in enumerate(RAIN_ONSET_DROPS):
        sources.append(
            WaveSource(
                f"rain_drop_{idx:02d}",
                x,
                y,
                0.92 if idx % 2 else 1.0,  # small per-emitter amplitude
                wavelength,
                1.15,
                idx * 0.17,
                560.0 + 30.0 * (idx % 3),
                (0.0, 0.0),
                birth,
                lifetime,
                0,
                "impact",
            )
        )
    _ = time_seconds  # field engine recomputes envelope itself
    return sources


# Raindrops-on-water impact schedule: denser, longer-lived impacts so ripple
# fronts overlap and interference cells form (Section 3 Phase 4).
RAINDROP_IMPACTS: tuple[tuple[float, float, float, float, float], ...] = (
    (0.10, 470.0, 360.0, 170.0, 3.40),
    (0.70, 920.0, 300.0, 176.0, 3.30),
    (1.35, 1380.0, 380.0, 164.0, 3.20),
    (2.05, 700.0, 680.0, 182.0, 3.50),
    (2.80, 1180.0, 720.0, 170.0, 3.30),
    (3.55, 1520.0, 560.0, 174.0, 3.35),
    (4.30, 420.0, 600.0, 178.0, 3.45),
)


def phase4_raindrops_on_water_sources(phase: float) -> list[WaveSource]:
    """Multiple radial impact sources, each spawning expanding decaying rings.

    Section 3 Phase 4 / Section 6: symmetry_order 0, mode radial/impulse,
    3-7 impact sources, decaying. Longer lifetimes than rain-onset so ripple
    fronts cross and interference-lens crescents form.
    """
    _ = phase
    sources: list[WaveSource] = []
    for idx, (birth, x, y, wavelength, lifetime) in enumerate(RAINDROP_IMPACTS):
        sources.append(
            WaveSource(
                f"impact_{idx:02d}",
                x,
                y,
                1.04 if idx % 3 else 0.94,
                wavelength,
                1.05,
                -TAU * birth * 0.06 + idx * 0.13,
                640.0 + 36.0 * (idx % 4),
                (0.0, 0.0),
                birth,
                lifetime,
                0,
                "impact",
            )
        )
    return sources


def phase5_standing_wave_sources(phase: float) -> list[WaveSource]:
    """Persistent emitters in a FIXED layout: a stable standing field.

    Section 3 Phase 5 / Section 6: symmetry_order 0, mode multi_emitter, 3-7
    persistent emitters, fixed. The layout never moves, so F(x,y) topology is
    stable for the whole window - cells are classified from that stable F. The
    global wave phase advances over the clip (phase inversion), which v003
    handles by re-thresholding the same stable field; cell membership does not
    jump because the source layout is constant.
    """
    _ = phase
    # Five persistent emitters (within the 3-7 cap) in a fixed asymmetric
    # layout - asymmetric so the result is a legible interference lattice, not
    # a symmetric mandala.
    layout = [
        (-360.0, -150.0),
        (330.0, -190.0),
        (-300.0, 210.0),
        (370.0, 230.0),
        (20.0, -20.0),
    ]
    freq = 1.0 / DURATION_FOR(5)
    sources: list[WaveSource] = []
    for idx, (dx, dy) in enumerate(layout):
        sources.append(
            WaveSource(
                f"standing_emitter_{idx:02d}",
                CX + dx,
                CY + dy,
                1.0,
                204.0 + (idx % 2) * 14.0,
                freq,
                idx * math.pi * 0.07,
                1080.0,  # large decay length -> persistent, fills the field
                (0.0, 0.0),
                0.0,
                DURATION_FOR(5),
                0,
                "fixed_radial",
            )
        )
    return sources


def phase6_snowflake_sources(phase: float) -> list[WaveSource]:
    """One radial centre plus sixfold harmonic - the m=6 Bessel-style field.

    Section 3 Phase 6 / Section 6: symmetry_order 6, mode radial_bessel,
    1 centre + modes. Per the plan, prefer the radial-centre + sixfold mode
    term over six literal point emitters (v001's seven-source seed field read
    as a diagnostic). A strong angular alpha gives a clear sixfold structure;
    a slow breathing keeps the six arms from reading as a static mandala.
    """
    breathe = 1.0 + 0.05 * math.sin(TAU * phase)
    return [
        WaveSource(
            source_id="snow_centre",
            x=CX,
            y=CY,
            amplitude=1.0 * breathe,
            wavelength=218.0,
            frequency=1.0 / DURATION_FOR(6),
            phase=0.0,
            # decay = falloff LENGTH in px; large so the field reaches across
            # the frame (v003's sun source uses 920.0).
            decay=920.0,
            velocity=(0.0, 0.0),
            birth_time=0.0,
            lifetime=DURATION_FOR(6),
            symmetry_order=6,
            mode="sixfold_radial",
            angular_alpha=0.62,  # strong sixfold lobing -> six-arm crystallization
        )
    ]


def phase7_melt_return_sources(phase: float) -> list[WaveSource]:
    """Sixfold structure dissolving to a single low-amplitude warming centre.

    Section 3 Phase 7 / Section 6: symmetry_order 6 -> 0, mode radial,
    emitters merge to 1 centre. The sixfold angular term ramps to 0 over the
    clip and amplitude re-warms; the phase ends in the single-centre
    field-rest configuration that Phase 1 opens from (the loop anchor).
    """
    # angular term decays 0.55 -> ~0 ; amplitude re-warms toward the rest level.
    # (Amplitude is informational only - evaluate_field normalizes F to [-1,1]
    # each frame - but it keeps the source list honest about the melt read.)
    angular = 0.55 * (1.0 - smoothstep(0.0, 0.92, phase))
    amplitude = 0.62 + 0.30 * smoothstep(0.20, 1.0, phase)
    return [
        WaveSource(
            source_id="melt_centre",
            x=CX,
            y=CY,
            amplitude=amplitude,
            wavelength=220.0,
            frequency=1.0 / DURATION_FOR(7),
            phase=0.0,
            # decay = falloff LENGTH in px; large so the field reaches across
            # the frame (v003's sun source uses 920.0).
            decay=920.0,
            velocity=(0.0, 0.0),
            birth_time=0.0,
            lifetime=DURATION_FOR(7),
            symmetry_order=6,
            mode="sixfold_radial",
            angular_alpha=angular,
        )
    ]


# Per-phase durations (seconds, all within the 6-10 s study window).
_PHASE_DURATIONS: dict[int, float] = {
    1: 8.0,
    2: 9.0,
    3: 7.0,
    4: 9.0,
    5: 10.0,
    6: 9.0,
    7: 8.0,
}


def DURATION_FOR(order: int) -> float:
    return _PHASE_DURATIONS[order]


def _loop(
    key: str,
    filename: str,
    description: str,
    builder: Callable[[float], list[WaveSource]],
    *,
    threshold_percentile: float,
    min_area: float,
    max_cells: int,
) -> LoopSpec:
    """Build a v003 LoopSpec for a phase study.

    Threshold range 68-80 percentile and node_epsilon 0.015-0.050 are the
    taxonomy doc Section 2 parameter ranges; compound_policy faint matches
    Section 6's faint-ghost compound policy.
    """
    return LoopSpec(
        key=key,
        filename=filename,
        description=description,
        source_builder=builder,
        threshold_percentile=threshold_percentile,
        min_area=min_area,
        max_area=62000.0,
        max_cells=max_cells,
        node_epsilon=0.032,
        blur_sigma=1.18,
        compound_policy="faint",
    )


# The seven phase studies, in cycle order. max_cells caps stay within the
# 8-24 selected-filled-cell band (Section 6 caps). threshold_percentile values
# are inside the taxonomy doc's 68-80 range.
PHASES: tuple[PhaseSpec, ...] = (
    PhaseSpec(
        key="phase1_sun_radiant",
        order=1,
        filename="phase1_sun_radiant.mp4",
        duration_seconds=DURATION_FOR(1),
        visual_read=(
            "One luminous central origin; a few partial ring-phase crescent "
            "arcs; a small number of attached curved trigon releases. Calm, "
            "low cell count, open negative space dominant."
        ),
        symmetry_order="0 (->6 blend)",
        mode="radial",
        dominant_taxonomy=("radial_source_ring", "multi_source_trigon_scallop"),
        source_regime="1 centre, steady breathing envelope",
        austin_risk="high",
        loop=_loop(
            "phase1_sun_radiant",
            "phase1_sun_radiant.mp4",
            "Single centre source with a low sixfold angular blend; first-ring "
            "field cells become attached radiant curved trigons and ring-phase "
            "crescents around a central orb.",
            phase1_sun_radiant_sources,
            threshold_percentile=73.0,
            min_area=170.0,
            max_cells=16,
        ),
    ),
    PhaseSpec(
        key="phase2_vapor_mist",
        order=2,
        filename="phase2_vapor_mist.mp4",
        duration_seconds=DURATION_FOR(2),
        visual_read=(
            "Faint, low-contrast drifting partial arcs rising and spreading. "
            "Most circle origins absent. Sparse, soft, lowest contrast in the "
            "loop."
        ),
        symmetry_order="0",
        mode="network",
        dominant_taxonomy=("nodal_boundary", "interference_lens_crescent"),
        source_regime="3-7 weak emitters, upward drift",
        austin_risk="medium (no Meeting 2 cloud/mist grammar)",
        loop=_loop(
            "phase2_vapor_mist",
            "phase2_vapor_mist.mp4",
            "Weak five-emitter network at low amplitude and high decay drifting "
            "slowly upward; faint drifting crescent arcs, circle origins mostly "
            "absent.",
            phase2_vapor_mist_sources,
            threshold_percentile=70.0,
            min_area=220.0,
            max_cells=14,
        ),
    ),
    PhaseSpec(
        key="phase3_rain_onset",
        order=3,
        filename="phase3_rain_onset.mp4",
        duration_seconds=DURATION_FOR(3),
        visual_read=(
            "Discrete droplet origins appear and fall; the soft field becomes "
            "punctuated by small descending impulse sources. A quick gather."
        ),
        symmetry_order="0",
        mode="impulse",
        dominant_taxonomy=("radial_source_ring", "multi_source_trigon_scallop"),
        source_regime="3-7 short-lived impact emitters, staggered birth",
        austin_risk="lower (close to Meeting 2 pond metaphor)",
        loop=_loop(
            "phase3_rain_onset",
            "phase3_rain_onset.mp4",
            "Short-lived impact emitters with staggered birth times; each drop "
            "is a discrete origin with a first partial ripple arc, sparse "
            "impact phrases rather than particle wallpaper.",
            phase3_rain_onset_sources,
            threshold_percentile=74.0,
            min_area=200.0,
            max_cells=16,
        ),
    ),
    PhaseSpec(
        key="phase4_raindrops_on_water",
        order=4,
        filename="phase4_raindrops_on_water.mp4",
        duration_seconds=DURATION_FOR(4),
        visual_read=(
            "Radial ripples from multiple impacts; interference where ripple "
            "fronts cross; a legible circle -> crescent -> crescent -> trigon "
            "phrase per drop."
        ),
        symmetry_order="0",
        mode="radial/impulse",
        dominant_taxonomy=(
            "interference_lens_crescent",
            "multi_source_trigon_scallop",
        ),
        source_regime="3-7 impact sources, decaying overlapping ripples",
        austin_risk="lowest (natural Austin lead)",
        loop=_loop(
            "phase4_raindrops_on_water",
            "phase4_raindrops_on_water.mp4",
            "Seven decaying radial impact sources with overlapping ripple "
            "fields; impact origins, partial-ring crescents, and interference "
            "lens cells where two ripple fronts cup.",
            phase4_raindrops_on_water_sources,
            threshold_percentile=73.0,
            min_area=220.0,
            max_cells=20,
        ),
    ),
    PhaseSpec(
        key="phase5_standing_wave",
        order=5,
        filename="phase5_standing_wave.mp4",
        duration_seconds=DURATION_FOR(5),
        visual_read=(
            "A stable nodal lattice of cells; positive antinode cells fill, "
            "negative cells outline; a slow phase inversion swaps which "
            "polarity fills. The most overtly cymatic phase."
        ),
        symmetry_order="0",
        mode="multi_emitter",
        dominant_taxonomy=(
            "positive_phase_cell",
            "negative_phase_cell",
            "nodal_boundary",
        ),
        source_regime="3-7 persistent emitters, fixed layout, stable F",
        austin_risk="medium - internal legibility gate, not for Austin yet",
        loop=_loop(
            "phase5_standing_wave",
            "phase5_standing_wave.mp4",
            "Five persistent emitters in a fixed asymmetric layout forming a "
            "stable standing field; selected interference cells classified "
            "from the stable F(x,y), no all-frame lattice.",
            phase5_standing_wave_sources,
            threshold_percentile=74.0,
            min_area=240.0,
            max_cells=22,
        ),
    ),
    PhaseSpec(
        key="phase6_snowflake",
        order=6,
        filename="phase6_snowflake.mp4",
        duration_seconds=DURATION_FOR(6),
        visual_read=(
            "A sixfold radial structure; selected lens/crescent cells along "
            "six arms; attached curved trigon ray tips; a centre node. The "
            "sixfold read is clear but must not be a mandala."
        ),
        symmetry_order="6",
        mode="radial_bessel",
        dominant_taxonomy=("six_ray_snowflake_sun_candidate",),
        source_regime="1 radial centre + sixfold mode term",
        austin_risk="high - adjacency to radial sun, mandala risk",
        loop=_loop(
            "phase6_snowflake",
            "phase6_snowflake.mp4",
            "Single radial centre with a strong sixfold angular mode term "
            "(m=6); a clear six-arm crystallization with attached curved "
            "trigon ray tips and paired crescent cells along the arms.",
            phase6_snowflake_sources,
            threshold_percentile=72.0,
            min_area=180.0,
            max_cells=18,
        ),
    ),
    PhaseSpec(
        key="phase7_melt_return",
        order=7,
        filename="phase7_melt_return.mp4",
        duration_seconds=DURATION_FOR(7),
        visual_read=(
            "The sixfold structure dissolves; arms retract; cells fade; the "
            "field simplifies to a single warming centre. Lowest cell count "
            "of the loop; quiet."
        ),
        symmetry_order="6 ->0",
        mode="radial",
        dominant_taxonomy=("radial_source_ring",),
        source_regime="emitters merge to a single low-amplitude centre",
        austin_risk="low intrinsic; hands into the high-risk sun phase",
        loop=_loop(
            "phase7_melt_return",
            "phase7_melt_return.mp4",
            "Single centre whose sixfold angular term ramps to zero while "
            "amplitude re-warms; the six-arm structure dissolves into a calm "
            "single-centre field-rest state.",
            phase7_melt_return_sources,
            threshold_percentile=72.0,
            min_area=180.0,
            max_cells=14,
        ),
    ),
)


def near_black_canvas() -> np.ndarray:
    """A 1920x1080 frame filled with the #05070b near-black background.

    Section 7 of the plan: the layer composites additive/screen over the
    production-floor footage; it never carries its own background plate. v003
    rendered on pure black; the phase studies use #05070b so the near-black is
    explicit in the master.
    """
    frame = np.empty((H, W, 3), dtype=np.uint8)
    frame[:, :, 0] = BACKGROUND_BGR[0]
    frame[:, :, 1] = BACKGROUND_BGR[1]
    frame[:, :, 2] = BACKGROUND_BGR[2]
    return frame


def composite_on_near_black(beauty: np.ndarray) -> np.ndarray:
    """Composite a v003 beauty render (rendered on pure black) onto #05070b.

    v003's render_canonical_beauty draws on a pure-black canvas additively, so
    the field/primitive marks ARE the pixel values above black. Adding them to
    a #05070b base is the additive composite the Resolume layer will do; doing
    it here makes the near-black background explicit in the master while
    leaving the marks unchanged.
    """
    base = near_black_canvas().astype(np.int16)
    out = base + beauty.astype(np.int16)
    return np.clip(out, 0, 255).astype(np.uint8)


def save_debug_bundle(
    phase: PhaseSpec,
    beauty_frame: np.ndarray,
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    time_seconds: float,
) -> dict[str, Path]:
    """Write the six v003 debug panels plus the debug composite for a study.

    Panels: scalar_field, nodal_lines, positive_negative_regions,
    cell_class_colors, source_points, debug_composite (Section 9 evidence
    floor; same six panels as the v003 packet's debug_stills/).
    """
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stem = phase.key
    paths: dict[str, Path] = {}

    layers = {
        "scalar_field": grayscale_layer(field_norm, f"{stem} scalar field"),
        "nodal_lines": nodal_layer(field_norm, phase.loop, f"{stem} nodal lines"),
        "positive_negative_regions": regions_layer(
            field_norm, result.threshold, phase.loop, f"{stem} positive/negative regions"
        ),
        "cell_class_colors": classes_layer(result.cells, f"{stem} classified cells"),
        "source_points": source_layer(
            field_norm, sources, time_seconds, f"{stem} source points"
        ),
    }
    for layer_name, layer in layers.items():
        path = DEBUG_DIR / f"{stem}_{layer_name}.png"
        cv2.imwrite(str(path), layer, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        paths[layer_name] = path

    # debug_composite: beauty thumbnail beside the five debug panels.
    thumbs = [cv2.resize(beauty_frame, (480, 270), interpolation=cv2.INTER_AREA)]
    labels = ["beauty"]
    for layer_name in [
        "scalar_field",
        "nodal_lines",
        "positive_negative_regions",
        "cell_class_colors",
        "source_points",
    ]:
        thumbs.append(cv2.resize(layers[layer_name], (480, 270), interpolation=cv2.INTER_AREA))
        labels.append(layer_name)
    for thumb, label in zip(thumbs, labels, strict=True):
        draw_text(thumb, label, (16, 248), LABEL, scale=0.42)
    composite = cv2.hconcat(thumbs)
    composite_path = DEBUG_DIR / f"{stem}_debug_composite.png"
    cv2.imwrite(str(composite_path), composite, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    paths["debug_composite"] = composite_path
    return paths


def render_phase(phase: PhaseSpec) -> tuple[dict[str, object], list[dict[str, object]], np.ndarray]:
    """Render one phase study to MP4 and return its summary + audit entries."""
    duration = phase.duration_seconds
    n_frames = int(round(FPS * duration))
    spec = phase.loop
    writer = v003.H264Writer(OUT_DIR / phase.filename, fps=FPS, size=(W, H))
    tracker = CellTracker()

    # Legibility still sampled inside the readable window (v003 samples at
    # 2.25 s of its 6 s clip; here, scale that to ~37.5% of the clip).
    legibility_frame = int(round(0.375 * n_frames))

    per_frame_counts: list[int] = []
    per_frame_render_counts: list[int] = []
    class_totals: Counter[str] = Counter()
    polarity_totals: Counter[str] = Counter()
    threshold_values: list[float] = []
    audit_entries: list[dict[str, object]] = []

    midpoint_beauty: np.ndarray | None = None
    midpoint_field: np.ndarray | None = None
    midpoint_result: ExtractionResult | None = None
    midpoint_sources: list[WaveSource] | None = None

    for fi in range(n_frames):
        phase_fraction = fi / n_frames
        time_seconds = phase_fraction * duration
        sources = spec.source_builder(phase_fraction)
        # Stable field F(x,y,t): topology fixed within the phase window because
        # the source LAYOUT is constant; only the wave phase advances.
        field_norm = evaluate_field(sources, time_seconds, spec.blur_sigma)
        # Cells classified from that field's connected components - NOT from
        # any separate animated display buffer.
        result = extract_cells(field_norm, sources, spec, time_seconds)
        render_cells = select_render_cells(
            tracker.update(result.cells, fi, cap=max(48, spec.max_cells * 3)),
            spec,
            spec.max_cells,
        )
        beauty, primitives = render_canonical_beauty(
            field_norm, render_cells, sources, spec, time_seconds, fi
        )
        frame = composite_on_near_black(beauty)
        audit_entries.extend(audit_entry(primitive) for primitive in primitives)
        writer.write(frame)

        per_frame_counts.append(len(result.cells))
        per_frame_render_counts.append(len(render_cells))
        class_totals.update(result.counts_by_class)
        polarity_totals.update(result.counts_by_polarity)
        threshold_values.append(result.threshold)

        if fi == legibility_frame:
            midpoint_beauty = frame.copy()
            midpoint_field = field_norm.copy()
            midpoint_result = result
            midpoint_sources = sources

        if (fi + 1) % 24 == 0:
            print(f"  {phase.filename} {fi + 1}/{n_frames}", flush=True)

    writer.close()
    if (
        midpoint_beauty is None
        or midpoint_field is None
        or midpoint_result is None
        or midpoint_sources is None
    ):
        raise RuntimeError(f"no legibility frame captured for {phase.filename}")

    save_debug_bundle(
        phase,
        midpoint_beauty,
        midpoint_field,
        midpoint_result,
        midpoint_sources,
        legibility_frame / FPS,
    )

    summary: dict[str, object] = {
        "filename": phase.filename,
        "phase_key": phase.key,
        "phase_order": phase.order,
        "description": spec.description,
        "visual_read": phase.visual_read,
        "duration_seconds": duration,
        "frames": n_frames,
        "fps": FPS,
        "dimensions": [W, H],
        "background_hex": "#05070b",
        "symmetry_order": phase.symmetry_order,
        "mode": phase.mode,
        "dominant_taxonomy": list(phase.dominant_taxonomy),
        "source_regime": phase.source_regime,
        "austin_risk": phase.austin_risk,
        "legibility_still_frame": legibility_frame,
        "legibility_still_time_seconds": round(legibility_frame / FPS, 3),
        "threshold_percentile": spec.threshold_percentile,
        "node_epsilon": spec.node_epsilon,
        "blur_sigma": spec.blur_sigma,
        "min_area": spec.min_area,
        "max_cells_cap": spec.max_cells,
        "midpoint_threshold": round(midpoint_result.threshold, 5),
        "cells_per_frame_min": min(per_frame_counts),
        "cells_per_frame_max": max(per_frame_counts),
        "cells_per_frame_mean": round(float(np.mean(per_frame_counts)), 2),
        "rendered_cells_per_frame_min": min(per_frame_render_counts),
        "rendered_cells_per_frame_max": max(per_frame_render_counts),
        "rendered_cells_per_frame_mean": round(float(np.mean(per_frame_render_counts)), 2),
        "class_totals": dict(class_totals),
        "polarity_totals": dict(polarity_totals),
        "threshold_min": round(min(threshold_values), 5),
        "threshold_max": round(max(threshold_values), 5),
        "selected_cells_at_legibility_frame": len(midpoint_result.cells),
        "audit_entries": len(audit_entries),
        "classify_from": "stable_F_xy",
        "never_classify_from": "Z_xyt_animated",
        "midpoint_sources": [source_to_json(s) for s in midpoint_sources],
        "midpoint_cells": [cell_to_json(c) for c in midpoint_result.cells[:80]],
        "cultural_status": "internal_austin_review_needed",
    }
    return summary, audit_entries, midpoint_beauty


def make_contact_sheet(midpoints: list[tuple[PhaseSpec, np.ndarray]]) -> Path:
    """Contact sheet: final frame thumbnails for all seven studies + a debug row.

    Section 9 evidence floor requires a contact sheet showing final frames
    beside debug frames. Row 1: the seven final (beauty) legibility frames.
    Row 2: the matching seven debug_composite panels.
    """
    final_thumbs: list[np.ndarray] = []
    for phase, frame in midpoints:
        thumb = cv2.resize(frame, (420, 236), interpolation=cv2.INTER_AREA)
        draw_text(thumb, phase.key, (12, 222), LABEL, scale=0.40)
        final_thumbs.append(thumb)
    # Pad to a multiple of 4 for a clean grid (7 -> 8).
    while len(final_thumbs) % 4 != 0:
        final_thumbs.append(np.zeros((236, 420, 3), dtype=np.uint8))

    debug_thumbs: list[np.ndarray] = []
    for phase, _ in midpoints:
        debug_path = DEBUG_DIR / f"{phase.key}_debug_composite.png"
        img = cv2.imread(str(debug_path), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"missing debug composite for contact sheet: {debug_path}")
        thumb = cv2.resize(img, (420, 236), interpolation=cv2.INTER_AREA)
        draw_text(thumb, f"{phase.key} debug", (12, 222), LABEL, scale=0.36)
        debug_thumbs.append(thumb)
    while len(debug_thumbs) % 4 != 0:
        debug_thumbs.append(np.zeros((236, 420, 3), dtype=np.uint8))

    def grid(thumbs: list[np.ndarray]) -> np.ndarray:
        rows = [cv2.hconcat(thumbs[i : i + 4]) for i in range(0, len(thumbs), 4)]
        return cv2.vconcat(rows)

    final_grid = grid(final_thumbs)
    debug_grid = grid(debug_thumbs)
    header_h = 46
    width = final_grid.shape[1]
    header1 = np.zeros((header_h, width, 3), dtype=np.uint8)
    draw_text(
        header1,
        "water-cycle phase studies v001 - final (beauty) legibility frames",
        (18, 30),
        LABEL,
        scale=0.52,
    )
    header2 = np.zeros((header_h, width, 3), dtype=np.uint8)
    draw_text(
        header2,
        "debug frames per study: beauty + scalar_field/nodal/regions/classes/sources",
        (18, 30),
        LABEL,
        scale=0.48,
    )
    sheet = cv2.vconcat([header1, final_grid, header2, debug_grid])
    path = OUT_DIR / "water_cycle_phase_studies_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def write_manifest(summaries: list[dict[str, object]], contact_sheet: Path) -> Path:
    """Write the field/source manifest, shaped like the v003 manifest."""
    manifest = {
        "renderer": "scripts/water_cycle_phase_studies.py",
        "extends": "scripts/cymatic_field_topology_v003.py",
        "lane": "water-cycle continuum - Worker Task 1, isolated phase studies",
        "orchestration_plan": (
            "docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md"
        ),
        "created_for": (
            "Salish Sea Dreaming Phase 2 internal water-cycle phase studies; "
            "seven isolated water-state studies sharing one scalar-field engine"
        ),
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "cultural_status": "internal_austin_review_needed",
        "dimensions": [W, H],
        "fps": FPS,
        "background_hex": "#05070b",
        "field_grid": [v003.FW, v003.FH],
        "field_formula": (
            "point-source clips use F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i "
            "- omega_i*t + phase_i)*decay(distance)*envelope(t); radial-centre "
            "clips add a sixfold angular term (1 + alpha*cos(6*theta))"
        ),
        "classify_from": "stable_F_xy",
        "never_classify_from": "Z_xyt_animated",
        "classification_note": (
            "Cells are classified from the connected components of the stable "
            "field F(x,y) every frame (v003 extract_cells). Each phase holds "
            "its source LAYOUT fixed within its render window, so F's topology "
            "is stable for that window; only the global wave phase advances. "
            "No separate animated display buffer Z is classified."
        ),
        "caps_honored": {
            "emitters_or_centre_plus_modes": (
                "1 centre (sun/snowflake/melt) or 5 emitters (vapor/standing) "
                "or 7 impact sources (rain phases) - within 3-7 / 1-centre+modes"
            ),
            "selected_filled_cells": "max_cells caps 14-22, within the 8-24 band",
            "nodal_boundary_groups": "1-4 (single nodal-band layer per study)",
            "six_ray_candidates": "0-2 (sixfold field in phase 1/6/7)",
            "no_all_frame_lattice": True,
            "open_negative_space": "preserved (per-study cell-count caps)",
        },
        "source_tuple_fields": [
            "x",
            "y",
            "amplitude",
            "wavelength",
            "frequency",
            "phase",
            "decay",
            "velocity",
            "birth_time",
            "lifetime",
            "symmetry_order",
            "mode",
            "angular_alpha",
        ],
        "outputs": {
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "primitive_audit": "primitive_audit_water_cycle_phase_studies_v001.json",
            "debug_stills_dir": str(DEBUG_DIR.relative_to(ROOT)),
        },
        "austin_boundary": {
            "public_use": False,
            "exact_austin_source": False,
            "sd_lora": False,
            "review_log": "docs/space-center/austin-consent-map.md",
        },
        "phase_studies": summaries,
    }
    path = OUT_DIR / "water_cycle_phase_studies_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_primitive_audit(entries: list[dict[str, object]]) -> Path:
    """Write the primitive audit, shaped like primitive_audit_v003.json."""
    path = OUT_DIR / "primitive_audit_water_cycle_phase_studies_v001.json"
    payload = {
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "audit_rule": (
            "Every rendered primitive must trace to one extracted source cell "
            "(field-extracted, not hand-placed)."
        ),
        "entry_count": len(entries),
        "entries": entries,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_readme(summaries: list[dict[str, object]]) -> Path:
    """Write the study README with cultural status and the F(x,y) confirmation."""
    by_key = {s["phase_key"]: s for s in summaries}
    rows = []
    for phase in PHASES:
        s = by_key.get(phase.key)
        if s is None:
            continue
        rows.append(
            f"- `{phase.filename}` (phase {phase.order}): {phase.visual_read} "
            f"Duration {s['duration_seconds']}s / {s['frames']} frames. "
            f"Field family: multi-emitter scalar standing-wave; seed "
            f"`{phase.key}` source builder. Threshold percentile "
            f"{s['threshold_percentile']} (taxonomy 68-80 range); "
            f"node_epsilon {s['node_epsilon']}. Class totals across frames: "
            f"{s['class_totals']}. Selected cells at legibility frame: "
            f"{s['selected_cells_at_legibility_frame']} (cap "
            f"{s['max_cells_cap']}, within the 8-24 band). Austin risk: "
            f"{phase.austin_risk}."
        )
    rows_text = "\n".join(rows)

    readme = f"""# Water-Cycle Phase Studies v001 - 2026-05-20

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim. Internal R&D until Austin per-output review. Not a
production dependency - the MVP fallback production floor is unaffected.

## Lane

Worker Task 1 of the water-cycle continuum orchestration plan
(`docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`,
Section 5): the seven isolated water-cycle phase studies. Transitions and the
assembled continuum are later worker tasks and are NOT in this packet.

## Source References

- `docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`
  (Sections 2, 3, 6, 9 - loop structure, phase table, source-list schema,
  acceptance criteria).
- `docs/space-center/water-cycle-cymatic-primitive-scene-language-2026-05-20.md`
  (state morphology, render recipes).
- `docs/space-center/interference-field-cell-taxonomy-2026-05-20.md` (field
  convention, taxonomy classes, classification order, caps).
- `docs/space-center/primitive-grammar-visual-acceptance-criteria-2026-05-20.md`
  (Topology/Cymatics lane criteria).
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/README.md`
  (the v003 renderer this script extends).

## Renderer

`scripts/water_cycle_phase_studies.py` - extends
`scripts/cymatic_field_topology_v003.py`. The v003 scalar-field engine,
cell classifier (`classify_cell`, `extract_cells`), canonical-primitive
machinery (`render_canonical_beauty`, `canonical_primitive_from_render_cell`),
cell tracker (`CellTracker`), and debug-layer functions are imported and
reused unchanged. v003's script and output folder were not edited.

## Field Family And Seed

- Field family: multi-emitter scalar standing-wave field
  `F(x,y,t)=sum_i A_i*cos(2*pi*distance/lambda_i - omega_i*t + phase_i)*`
  `decay(distance)*envelope(t)`. Radial-centre phases (sun, snowflake, melt)
  add a sixfold angular term `(1 + alpha*cos(6*theta))`.
- Seed: each phase has a deterministic source builder in
  `scripts/water_cycle_phase_studies.py` named `<phase_key>_sources`. No
  random seed - the field is fully determined by the source list and time.

## Classification From F(x,y), Not Z(x,y,t)

Cells are classified from the connected components of the stable field
`F(x,y)` every frame (v003 `extract_cells`). Each phase holds its source
LAYOUT fixed within its render window, so the field topology is stable for
that window; only the global wave phase advances over the clip. There is no
separate time-multiplied animated display buffer `Z(x,y,t)` and none is
classified. This satisfies the taxonomy doc Section 1 process gate.

## Thresholds And Caps

- Threshold percentile per study is inside the taxonomy doc Section 2 range
  (68-80). `node_epsilon` 0.032 is inside the 0.015-0.050 range.
- Cell-count caps (`max_cells` 14-22 per study) stay inside the Section 6
  8-24 selected-filled-cell band. Compound cells: faint-ghost policy.
- Emitter regime: 1 radial centre (sun / snowflake / melt) or 5 emitters
  (vapor / standing-wave) or 7 short-lived impact sources (rain phases) -
  within the 3-7 emitters / 1-centre-plus-modes cap.
- No all-frame lattice; open negative space preserved by the per-study caps.

## Studies

{rows_text}

## Render Spec

- Seven MP4 (H.264) clips, 1920x1080, 24 fps, 6-10 s each, rendered on
  `#05070b` near-black so the clip composites as an additive / screen-blend
  layer in Resolume over production-floor footage. Layer-only: the clips
  carry no background plate of their own.
- Black-screen layer-only; a single separable Resolume layer with a
  kill-switch; never a production dependency.

## Evidence Bundle

- 7 MP4 phase-study clips (see Studies above).
- `water_cycle_phase_studies_v001_manifest.json` - field / source manifest.
- `primitive_audit_water_cycle_phase_studies_v001.json` - every rendered
  primitive audited back to one extracted source cell.
- `debug_stills/` - six panels per study: `scalar_field`, `nodal_lines`,
  `positive_negative_regions`, `cell_class_colors`, `source_points`,
  `debug_composite`.
- `water_cycle_phase_studies_v001_contact_sheet.png` - final (beauty)
  legibility frames beside the per-study debug composites.
- `README.md` - this file.

## Cultural Status And Austin Boundary

- Cultural status: `internal_austin_review_needed`. No "Austin-approved", no
  "Coast Salish", no traditional-meaning claim. Review-facing language is
  "radial topology", "standing-wave cell", "interference lens" - not "sacred
  geometry", not "ceremony", not "teaching".
- No exact Austin source geometry, palette, faces, Thunderbird, serpent, or
  named beings. No salmon, fish, birds, or figures. No SD / LoRA / style
  transfer - deterministic scalar-field extraction only.
- The sun (phase 1) and snowflake (phase 6) studies are the highest Austin
  risk and are review questions, not finished looks. The standing-wave study
  (phase 5) is an internal legibility gate and is not for Austin until that
  gate passes.
- After any Austin review, per-output answers are recorded in
  `docs/space-center/austin-consent-map.md` before any projector-facing or
  public promotion.

## Honest Read

The visible marks are canonicalized for legibility (v003's "field handwriting
-> primitive typography" approach), but each one is still driven by an
extracted field cell - see the primitive audit. This is not hand-placed
iconography. The radial sun and sixfold snowflake studies are internal radial-
topology probes, not Austin-approved sun/snow grammar.
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the seven water-cycle isolated phase studies (Worker Task 1)."
    )
    parser.add_argument(
        "--phase",
        choices=["all", *[p.key for p in PHASES]],
        default="all",
        help="Render one phase study for iteration, or all seven for the packet.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    selected = list(PHASES if args.phase == "all" else [p for p in PHASES if p.key == args.phase])
    summaries: list[dict[str, object]] = []
    midpoints: list[tuple[PhaseSpec, np.ndarray]] = []
    audit_entries: list[dict[str, object]] = []
    for phase in selected:
        print(f"Rendering {phase.filename}", flush=True)
        summary, entries, midpoint = render_phase(phase)
        summaries.append(summary)
        midpoints.append((phase, midpoint))
        audit_entries.extend(entries)

    primitive_audit = write_primitive_audit(audit_entries)
    print(f"Wrote {primitive_audit}")

    if args.phase == "all":
        contact_sheet = make_contact_sheet(midpoints)
        manifest = write_manifest(summaries, contact_sheet)
        readme = write_readme(summaries)
        print(f"Wrote {contact_sheet}")
        print(f"Wrote {manifest}")
        print(f"Wrote {readme}")
        print(f"Wrote water-cycle phase studies v001 packet to {OUT_DIR}")
    else:
        print(f"Wrote single-phase iteration output to {OUT_DIR}")


if __name__ == "__main__":
    main()
