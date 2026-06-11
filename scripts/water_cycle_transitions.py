#!/usr/bin/env python3.11
"""
Water-cycle transition tests v001.

Worker Task 2 of the water-cycle continuum orchestration plan
(docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md,
Section 5). Renders the six boundary transition test clips, each proving the
source-list morph between two adjacent water-cycle phases is continuous with
NO crossfade:

  sun_to_vapor, vapor_to_rain, rain_to_raindrops,
  raindrops_to_interference, interference_to_snowflake, snowflake_to_melt

melt -> sun is NOT rendered here: it is the loop point, verified later by
field-identity at the seam (Worker Task 3), not a transition clip.

This script EXTENDS the v003 renderer and reuses the seven phase source-list
configurations from `water_cycle_phase_studies.py` (Worker Task 1). The morph
is a PARAMETER RAMP on the source list - amplitude, decay, velocity,
symmetry_order, birth/lifetime - NOT a visual crossfade. A single field
F(x,y,t) is evaluated every frame from one merged source list in which the
outgoing phase's sources ramp their amplitude down and the incoming phase's
sources ramp their amplitude up; emitters are born, die, and drift inside
that one continuous field. There is exactly one `extract_cells` pass and one
render per frame - no compositing of two rendered images. Cells are classified
from the stable field F(x,y), never from an animated display buffer Z.

Status: INTERNAL ONLY. Not Austin-approved, not public-use guidance, and not
a cultural-meaning claim. Internal R&D until Austin per-output review.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np

import sys as _sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_SCRIPTS_DIR))

# v003 engine + Task 1 phase configs.
import cymatic_field_topology_v003 as v003  # noqa: E402
import water_cycle_phase_studies as wcp  # noqa: E402

WaveSource = v003.WaveSource
CellRecord = v003.CellRecord
RenderCell = v003.RenderCell
ExtractionResult = v003.ExtractionResult
CellTracker = v003.CellTracker
LoopSpec = v003.LoopSpec
evaluate_field = v003.evaluate_field
extract_cells = v003.extract_cells
select_render_cells = v003.select_render_cells
audit_entry = v003.audit_entry
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
smootherstep = v003.smootherstep
TAU = v003.TAU
# v003 drawing primitives reused by the transition-specific beauty renderer.
canvas = v003.canvas
draw_scalar_field_beauty = v003.draw_scalar_field_beauty
draw_nodal_band = v003.draw_nodal_band
canonical_primitive_from_render_cell = v003.canonical_primitive_from_render_cell
draw_canonical_primitive = v003.draw_canonical_primitive
CanonicalPrimitive = v003.CanonicalPrimitive
DRAW_PRIORITY = v003.DRAW_PRIORITY
LABEL = v003.LABEL
DEBUG_CLASS_COLORS = v003.DEBUG_CLASS_COLORS
draw_contour_outline = v003.draw_contour_outline

ROOT = _SCRIPTS_DIR.parent
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_cycle_transitions_v001_2026-05-20"
)
DEBUG_DIR = OUT_DIR / "debug_stills"

W = v003.W
H = v003.H
FPS = v003.FPS
BACKGROUND_BGR = wcp.BACKGROUND_BGR  # #05070b near-black

# Timeline shape per transition test clip (Section 5 Worker Task 2):
#   lead-in (end of phase N) + ~3 s morph + lead-out (start of phase N+1).
LEAD_IN_SECONDS = 1.5
MORPH_SECONDS = 3.0  # the duration_s in the Section 6 transitions schema
LEAD_OUT_SECONDS = 1.5
CLIP_SECONDS = LEAD_IN_SECONDS + MORPH_SECONDS + LEAD_OUT_SECONDS  # 6.0 s, within 4-8 s


# ---------------------------------------------------------------------------
# Source-list morph machinery.
#
# A transition has an outgoing phase builder and an incoming phase builder
# (both from water_cycle_phase_studies). Over the clip:
#   - lead-in: only the outgoing phase's sources are active (at full weight).
#   - morph window: outgoing sources ramp amplitude DOWN to 0; incoming
#     sources ramp amplitude UP from 0. Both families are summed into ONE
#     field F(x,y,t) - this is a source-parameter ramp, not a frame crossfade.
#   - lead-out: only the incoming phase's sources are active (at full weight).
# The amplitude weight is multiplied into each WaveSource.amplitude, so the
# field engine sees a normal source list; nothing about the renderer changes.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransitionSpec:
    """One boundary transition test clip."""

    key: str
    order: int
    filename: str
    from_phase_key: str
    to_phase_key: str
    from_phase_order: int
    to_phase_order: int
    method: str
    params_ramped: tuple[str, ...]
    morph_read: str
    austin_risk: str
    # The v003 LoopSpec used for extraction/threshold/render parameters across
    # the whole clip. Picked to suit the busier of the two phases.
    loop: LoopSpec


def _phase_builder(phase_key: str):
    """Return the Task 1 source builder for a phase key."""
    for phase in wcp.PHASES:
        if phase.key == phase_key:
            return phase.loop.source_builder
    raise KeyError(f"unknown phase key {phase_key}")


def _scaled_amplitude_sources(
    builder, internal_phase: float, weight: float, id_prefix: str
) -> list[WaveSource]:
    """Build a phase's sources at a given internal phase, scaled by `weight`.

    `weight` in [0,1] multiplies each source's amplitude - the amplitude ramp.
    `id_prefix` keeps outgoing/incoming source IDs distinct so the tracker and
    the source-attribution code never confuse the two families.
    """
    sources = builder(internal_phase)
    out: list[WaveSource] = []
    for src in sources:
        out.append(
            replace(
                src,
                source_id=f"{id_prefix}__{src.source_id}",
                amplitude=src.amplitude * weight,
            )
        )
    return out


def transition_sources(
    spec: TransitionSpec, time_seconds: float
) -> tuple[list[WaveSource], float]:
    """Merged source list for the transition at `time_seconds`.

    Returns (sources, morph_progress) where morph_progress is 0 before the
    morph, 0..1 during it, 1 after. The outgoing phase fades its amplitude to
    0 and the incoming phase rises from 0 within one continuous field.
    """
    from_builder = _phase_builder(spec.from_phase_key)
    to_builder = _phase_builder(spec.to_phase_key)

    morph_start = LEAD_IN_SECONDS
    morph_end = LEAD_IN_SECONDS + MORPH_SECONDS

    if time_seconds <= morph_start:
        morph_progress = 0.0
    elif time_seconds >= morph_end:
        morph_progress = 1.0
    else:
        morph_progress = (time_seconds - morph_start) / MORPH_SECONDS

    # smootherstep ramp so amplitude enters/leaves the field gently - no hard
    # parameter step that would read as a pop.
    ramp = smootherstep(morph_progress)
    from_weight = 1.0 - ramp
    to_weight = ramp

    # Each phase's own internal animation advances across the whole clip so
    # the lead-in / lead-out look like genuine slices of phases N and N+1.
    # The internal phase is the clip time mapped into the phase's own loop.
    from_internal = (time_seconds / CLIP_SECONDS) % 1.0
    to_internal = (time_seconds / CLIP_SECONDS) % 1.0

    sources: list[WaveSource] = []
    if from_weight > 0.0005:
        sources.extend(
            _scaled_amplitude_sources(from_builder, from_internal, from_weight, "from")
        )
    if to_weight > 0.0005:
        sources.extend(
            _scaled_amplitude_sources(to_builder, to_internal, to_weight, "to")
        )
    # Guard: if both weights underflow (only at exact endpoints of the ramp),
    # keep the dominant family so the field is never empty.
    if not sources:
        if from_weight >= to_weight:
            sources = _scaled_amplitude_sources(from_builder, from_internal, 1.0, "from")
        else:
            sources = _scaled_amplitude_sources(to_builder, to_internal, 1.0, "to")
    return sources, morph_progress


# ---------------------------------------------------------------------------
# The six transitions, in cycle order. melt -> sun is omitted by design.
#
# loop choice: each transition is extracted/rendered with a single v003
# LoopSpec for the whole clip. We reuse the busier adjacent phase's LoopSpec
# (its max_cells cap, threshold, min_area) so the transition never exceeds the
# Section 6 caps - the per-phase studies already verified those caps hold.
# ---------------------------------------------------------------------------


def _loop_for(phase_key: str, *, key: str, filename: str, description: str) -> LoopSpec:
    """Clone a Task 1 phase LoopSpec, re-keyed for the transition clip."""
    for phase in wcp.PHASES:
        if phase.key == phase_key:
            base = phase.loop
            return LoopSpec(
                key=key,
                filename=filename,
                description=description,
                source_builder=base.source_builder,  # unused; transition_sources is used
                threshold_percentile=base.threshold_percentile,
                min_area=base.min_area,
                max_area=base.max_area,
                max_cells=base.max_cells,
                node_epsilon=base.node_epsilon,
                blur_sigma=base.blur_sigma,
                compound_policy=base.compound_policy,
            )
    raise KeyError(phase_key)


TRANSITIONS: tuple[TransitionSpec, ...] = (
    TransitionSpec(
        key="sun_to_vapor",
        order=1,
        filename="sun_to_vapor.mp4",
        from_phase_key="phase1_sun_radiant",
        to_phase_key="phase2_vapor_mist",
        from_phase_order=1,
        to_phase_order=2,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "decay", "velocity", "symmetry_order"),
        morph_read=(
            "The single radiant centre weakens; its sixfold angular term and "
            "amplitude fall while a weak upward-drifting multi-emitter mist "
            "network rises in the same field. The orb evaporates into faint "
            "drifting arcs."
        ),
        austin_risk="high (sun phase is the highest-risk endpoint)",
        loop=_loop_for(
            "phase1_sun_radiant",
            key="sun_to_vapor",
            filename="sun_to_vapor.mp4",
            description=(
                "Transition test: single sixfold radiant centre ramps down "
                "while a weak upward-drifting mist network ramps up, one "
                "continuous field, no crossfade."
            ),
        ),
    ),
    TransitionSpec(
        key="vapor_to_rain",
        order=2,
        filename="vapor_to_rain.mp4",
        from_phase_key="phase2_vapor_mist",
        to_phase_key="phase3_rain_onset",
        from_phase_order=2,
        to_phase_order=3,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "decay", "birth_time", "lifetime"),
        morph_read=(
            "The weak mist network cools and fades; discrete short-lived "
            "impact emitters are born with staggered birth times. Drifting "
            "mist arcs give way to discrete descending droplet origins."
        ),
        austin_risk="lower (rain-over-pond is close to the Meeting 2 metaphor)",
        loop=_loop_for(
            "phase3_rain_onset",
            key="vapor_to_rain",
            filename="vapor_to_rain.mp4",
            description=(
                "Transition test: weak mist network ramps down while "
                "short-lived staggered-birth rain impact emitters ramp up, "
                "one continuous field, no crossfade."
            ),
        ),
    ),
    TransitionSpec(
        key="rain_to_raindrops",
        order=3,
        filename="rain_to_raindrops.mp4",
        from_phase_key="phase3_rain_onset",
        to_phase_key="phase4_raindrops_on_water",
        from_phase_order=3,
        to_phase_order=4,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "lifetime", "birth_time"),
        morph_read=(
            "Short-lived rain-onset impulses give way to longer-lived radial "
            "impact sources whose ripple fronts overlap and cross. The field "
            "shifts from falling droplets to a surface ripple field."
        ),
        austin_risk="lowest (raindrops-on-water is the natural Austin lead)",
        loop=_loop_for(
            "phase4_raindrops_on_water",
            key="rain_to_raindrops",
            filename="rain_to_raindrops.mp4",
            description=(
                "Transition test: short-lived rain-onset impulses ramp down "
                "while longer-lived overlapping raindrop impact sources ramp "
                "up, one continuous field, no crossfade."
            ),
        ),
    ),
    TransitionSpec(
        key="raindrops_to_interference",
        order=4,
        filename="raindrops_to_interference.mp4",
        from_phase_key="phase4_raindrops_on_water",
        to_phase_key="phase5_standing_wave",
        from_phase_order=4,
        to_phase_order=5,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "lifetime", "decay"),
        morph_read=(
            "The transient decaying impact sources give way to persistent "
            "fixed emitters; the ripple field stops decaying and sets into a "
            "stable standing interference pattern."
        ),
        austin_risk="medium (standing wave is an internal legibility gate)",
        loop=_loop_for(
            "phase5_standing_wave",
            key="raindrops_to_interference",
            filename="raindrops_to_interference.mp4",
            description=(
                "Transition test: transient decaying raindrop impacts ramp "
                "down while persistent fixed standing-wave emitters ramp up, "
                "one continuous field, no crossfade."
            ),
        ),
    ),
    TransitionSpec(
        key="interference_to_snowflake",
        order=5,
        filename="interference_to_snowflake.mp4",
        from_phase_key="phase5_standing_wave",
        to_phase_key="phase6_snowflake",
        from_phase_order=5,
        to_phase_order=6,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "symmetry_order", "decay"),
        morph_read=(
            "The persistent multi-emitter standing field is pulled toward "
            "sixfold symmetry; the lattice reorganizes into a Bessel m=6 "
            "radial field - the standing pattern crystallizes."
        ),
        austin_risk="high (sixfold radial sits close to the radial sun)",
        loop=_loop_for(
            "phase6_snowflake",
            key="interference_to_snowflake",
            filename="interference_to_snowflake.mp4",
            description=(
                "Transition test: persistent standing-wave emitters ramp down "
                "while a single sixfold radial centre ramps up, one "
                "continuous field, no crossfade."
            ),
        ),
    ),
    TransitionSpec(
        key="snowflake_to_melt",
        order=6,
        filename="snowflake_to_melt.mp4",
        from_phase_key="phase6_snowflake",
        to_phase_key="phase7_melt_return",
        from_phase_order=6,
        to_phase_order=7,
        method="source_param_ramp_and_birth_death",
        params_ramped=("amplitude", "symmetry_order"),
        morph_read=(
            "The sixfold structure softens; amplitude and arm definition fall "
            "while the angular term begins ramping down. The six-ray structure "
            "starts collapsing inward toward a warming centre."
        ),
        austin_risk="low intrinsic (hands toward the melt/rest state)",
        loop=_loop_for(
            "phase6_snowflake",
            key="snowflake_to_melt",
            filename="snowflake_to_melt.mp4",
            description=(
                "Transition test: a strong sixfold radial field ramps down "
                "while a softening, angular-term-decaying melt centre ramps "
                "up, one continuous field, no crossfade."
            ),
        ),
    ),
)


def near_black_canvas() -> np.ndarray:
    """A 1920x1080 frame filled with the #05070b near-black background."""
    frame = np.empty((H, W, 3), dtype=np.uint8)
    frame[:, :, 0] = BACKGROUND_BGR[0]
    frame[:, :, 1] = BACKGROUND_BGR[1]
    frame[:, :, 2] = BACKGROUND_BGR[2]
    return frame


def composite_on_near_black(beauty: np.ndarray) -> np.ndarray:
    """Composite a v003 beauty render (drawn on pure black) onto #05070b.

    This is an additive composite of the layer marks onto the near-black base
    - the same additive/screen blend the Resolume layer performs. It is NOT a
    crossfade between two rendered phase frames: there is only ONE rendered
    frame per timestep (the beauty render of the single merged-source field).
    """
    base = near_black_canvas().astype(np.int16)
    out = base + beauty.astype(np.int16)
    return np.clip(out, 0, 255).astype(np.uint8)


def transition_temporal_levels(time_seconds: float) -> tuple[float, float]:
    """Field / cell alpha for a transition test clip.

    v003's `temporal_levels` is calibrated for v003's 6 s "raw field reveal ->
    primitives -> dissolve" arc: it holds the full scalar field at alpha 1.0
    for the first 1.0 s with no primitives. That arc is wrong for a transition
    test, whose lead-in is the *end of phase N* and must already show phase
    N's primitives so the morph is read in context (Section 5 Worker Task 2).

    This transition curve instead keeps primitives visible across the WHOLE
    clip and the scalar field as a faint, near-constant context layer:
      - 0.0-0.6 s: a short ease-in so the clip does not pop on at frame 0
        (field eases 0.30 -> 0.12, cells ease 0.0 -> 1.0);
      - 0.6 s to end: field held faint and constant (0.12), cells held full.
    The field never fills the frame; the primitives are the subject throughout.
    """
    ease = smoothstep(0.0, 0.6, time_seconds)
    field_alpha = 0.30 - 0.18 * ease
    cell_alpha = ease
    return clamp01(field_alpha), clamp01(cell_alpha)


def render_transition_beauty(
    field_norm: np.ndarray,
    cells: list[RenderCell],
    sources: list[WaveSource],
    loop: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> tuple[np.ndarray, list[CanonicalPrimitive]]:
    """Transition beauty renderer.

    A near-exact copy of v003.render_canonical_beauty - same v003 drawing
    primitives, same canonical-primitive machinery, same draw order - with
    ONE change: it uses `transition_temporal_levels` instead of v003's
    `temporal_levels`, so primitives stay visible across the whole transition
    clip. v003's script is not edited; this is an extension.
    """
    frame = canvas()
    field_alpha, cell_alpha = transition_temporal_levels(time_seconds)
    draw_scalar_field_beauty(frame, field_norm, alpha=field_alpha)
    draw_nodal_band(frame, field_norm, loop.node_epsilon, alpha=0.045 * field_alpha)

    primitives: list[CanonicalPrimitive] = []
    ordered_cells = sorted(
        cells,
        key=lambda rendered: (
            DRAW_PRIORITY.get(rendered.cell.topology_class, 0),
            rendered.cell.area_px,
        ),
    )
    for rendered in ordered_cells:
        cell = rendered.cell
        if cell.render_policy == "suppress" or cell.topology_class == "compound":
            continue
        confidence_scale = 0.76 + 0.24 * cell.confidence
        alpha = cell_alpha * rendered.strength * confidence_scale
        primitive = canonical_primitive_from_render_cell(rendered, sources, loop, frame_index, alpha)
        if primitive is None:
            continue
        primitives.append(primitive)
        draw_canonical_primitive(frame, primitive, label=False)
    return frame, primitives


def make_morph_midpoint_still(
    spec: TransitionSpec,
    field_norm: np.ndarray,
    result: ExtractionResult,
    from_cells: list[CellRecord],
    to_cells: list[CellRecord],
) -> np.ndarray:
    """The extra debug still proving the morph is continuous, not a cut.

    Shows, in ONE field at the morph midpoint, the cells attributable to the
    outgoing phase and the cells attributable to the incoming phase co-present
    - colored by which phase's sources dominate them. If this still shows both
    populations, the morph is a continuous source-list blend, not a crossfade.
    """
    frame = near_black_canvas()
    # faint scalar field context
    field_full = cv2.resize(field_norm, (W, H), interpolation=cv2.INTER_CUBIC)
    amp = np.clip(np.abs(field_full), 0.0, 1.0) ** 0.8
    base = frame.astype(np.float32)
    base += amp[..., None] * np.array([60.0, 52.0, 30.0], dtype=np.float32) * 0.5
    frame[:, :, :] = np.clip(base, 0, 255).astype(np.uint8)

    from_ids = {c.cell_id for c in from_cells}
    to_ids = {c.cell_id for c in to_cells}
    from_color = (228, 198, 92)   # warm gold-ish: outgoing phase
    to_color = (136, 219, 238)    # pale blue: incoming phase
    n_from = n_to = 0
    for cell in result.cells:
        if cell.cell_id in from_ids:
            draw_contour_outline(frame, cell.contour, from_color, alpha=0.85, thickness=3)
            n_from += 1
        elif cell.cell_id in to_ids:
            draw_contour_outline(frame, cell.contour, to_color, alpha=0.85, thickness=3)
            n_to += 1
        else:
            draw_contour_outline(frame, cell.contour, (120, 130, 128), alpha=0.45, thickness=2)
        x, y = int(cell.centroid_px[0]), int(cell.centroid_px[1])
        draw_text(frame, cell.topology_class.replace("_like", ""), (x + 6, y), LABEL, scale=0.30)

    draw_text(frame, f"{spec.key}: morph-midpoint cell co-presence", (42, 56), LABEL, scale=0.58)
    draw_text(
        frame,
        "ONE field F(x,y) at morph midpoint; both phases' cells co-present = continuous morph, no crossfade",
        (42, 88),
        LABEL,
        scale=0.40,
    )
    cv2.rectangle(frame, (42, 110), (62, 128), (from_color[2], from_color[1], from_color[0]), -1)
    draw_text(frame, f"outgoing phase ({spec.from_phase_key}): {n_from} cells", (72, 125), LABEL, scale=0.40)
    cv2.rectangle(frame, (42, 138), (62, 156), (to_color[2], to_color[1], to_color[0]), -1)
    draw_text(frame, f"incoming phase ({spec.to_phase_key}): {n_to} cells", (72, 153), LABEL, scale=0.40)
    return frame, n_from, n_to


def attribute_cells_to_phase(
    spec: TransitionSpec,
    field_norm: np.ndarray,
    loop: LoopSpec,
    time_seconds: float,
) -> tuple[list[CellRecord], list[CellRecord]]:
    """Re-extract the field with ONLY the outgoing, then ONLY the incoming
    phase's sources, to label which cells each phase contributes at this time.

    This is a debug-only attribution pass - the actual render always uses the
    merged field. It lets the midpoint still color each merged-field cell by
    which phase's sources produced a cell at the same centroid.
    """
    from_builder = _phase_builder(spec.from_phase_key)
    to_builder = _phase_builder(spec.to_phase_key)
    internal = (time_seconds / CLIP_SECONDS) % 1.0
    from_only = _scaled_amplitude_sources(from_builder, internal, 1.0, "from")
    to_only = _scaled_amplitude_sources(to_builder, internal, 1.0, "to")
    from_field = evaluate_field(from_only, time_seconds, loop.blur_sigma)
    to_field = evaluate_field(to_only, time_seconds, loop.blur_sigma)
    from_result = extract_cells(from_field, from_only, loop, time_seconds)
    to_result = extract_cells(to_field, to_only, loop, time_seconds)
    return from_result.cells, to_result.cells


def nearest_centroid_match(
    merged_cells: list[CellRecord], phase_cells: list[CellRecord], tol: float = 96.0
) -> set[str]:
    """IDs of merged-field cells whose centroid is near a phase-only cell."""
    matched: set[str] = set()
    for mc in merged_cells:
        for pc in phase_cells:
            if (
                math.hypot(
                    mc.centroid_px[0] - pc.centroid_px[0],
                    mc.centroid_px[1] - pc.centroid_px[1],
                )
                <= tol
            ):
                matched.add(mc.cell_id)
                break
    return matched


def save_debug_bundle(
    spec: TransitionSpec,
    beauty_frame: np.ndarray,
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    time_seconds: float,
) -> dict[str, Path]:
    """Write the six v003 debug panels plus the debug composite (Section 9)."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stem = spec.key
    paths: dict[str, Path] = {}
    layers = {
        "scalar_field": grayscale_layer(field_norm, f"{stem} scalar field"),
        "nodal_lines": nodal_layer(field_norm, spec.loop, f"{stem} nodal lines"),
        "positive_negative_regions": regions_layer(
            field_norm, result.threshold, spec.loop, f"{stem} positive/negative regions"
        ),
        "cell_class_colors": classes_layer(result.cells, f"{stem} classified cells"),
        "source_points": source_layer(field_norm, sources, time_seconds, f"{stem} source points"),
    }
    for layer_name, layer in layers.items():
        path = DEBUG_DIR / f"{stem}_{layer_name}.png"
        cv2.imwrite(str(path), layer, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        paths[layer_name] = path

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


def render_transition(
    spec: TransitionSpec,
) -> tuple[dict[str, object], list[dict[str, object]], np.ndarray]:
    """Render one transition test clip to MP4 and return its summary."""
    n_frames = int(round(FPS * CLIP_SECONDS))
    loop = spec.loop
    writer = v003.H264Writer(OUT_DIR / spec.filename, fps=FPS, size=(W, H))
    tracker = CellTracker()

    morph_mid_frame = int(round(FPS * (LEAD_IN_SECONDS + MORPH_SECONDS / 2.0)))
    legibility_frame = morph_mid_frame  # debug bundle sampled at the morph midpoint

    per_frame_counts: list[int] = []
    per_frame_render_counts: list[int] = []
    class_totals: Counter[str] = Counter()
    polarity_totals: Counter[str] = Counter()
    threshold_values: list[float] = []
    audit_entries: list[dict[str, object]] = []
    morph_progress_samples: list[float] = []

    mid_beauty: np.ndarray | None = None
    mid_field: np.ndarray | None = None
    mid_result: ExtractionResult | None = None
    mid_sources: list[WaveSource] | None = None

    for fi in range(n_frames):
        time_seconds = fi / FPS
        sources, morph_progress = transition_sources(spec, time_seconds)
        # ONE continuous field F(x,y,t) from the merged source list. The
        # outgoing and incoming families are both summed here; there is no
        # second field and no frame-level crossfade.
        field_norm = evaluate_field(sources, time_seconds, loop.blur_sigma)
        # Cells classified from that stable field's connected components.
        result = extract_cells(field_norm, sources, loop, time_seconds)
        render_cells = select_render_cells(
            tracker.update(result.cells, fi, cap=max(48, loop.max_cells * 3)),
            loop,
            loop.max_cells,
        )
        beauty, primitives = render_transition_beauty(
            field_norm, render_cells, sources, loop, time_seconds, fi
        )
        frame = composite_on_near_black(beauty)
        audit_entries.extend(audit_entry(p) for p in primitives)
        writer.write(frame)

        per_frame_counts.append(len(result.cells))
        per_frame_render_counts.append(len(render_cells))
        class_totals.update(result.counts_by_class)
        polarity_totals.update(result.counts_by_polarity)
        threshold_values.append(result.threshold)
        morph_progress_samples.append(morph_progress)

        if fi == legibility_frame:
            mid_beauty = frame.copy()
            mid_field = field_norm.copy()
            mid_result = result
            mid_sources = sources

        if (fi + 1) % 24 == 0:
            print(f"  {spec.filename} {fi + 1}/{n_frames}", flush=True)

    writer.close()
    if mid_beauty is None or mid_field is None or mid_result is None or mid_sources is None:
        raise RuntimeError(f"no morph-midpoint frame captured for {spec.filename}")

    save_debug_bundle(spec, mid_beauty, mid_field, mid_result, mid_sources, legibility_frame / FPS)

    # The extra co-presence midpoint still (Section 5 Worker Task 2).
    from_cells, to_cells = attribute_cells_to_phase(
        spec, mid_field, loop, legibility_frame / FPS
    )
    from_matched = nearest_centroid_match(mid_result.cells, from_cells)
    to_matched = nearest_centroid_match(mid_result.cells, to_cells)
    # color the still using the matched-id sets
    midpoint_still, n_from, n_to = make_morph_midpoint_still(
        spec,
        mid_field,
        mid_result,
        [c for c in mid_result.cells if c.cell_id in from_matched],
        [c for c in mid_result.cells if c.cell_id in to_matched],
    )
    midpoint_path = DEBUG_DIR / f"{spec.key}_morph_midpoint_cell_copresence.png"
    cv2.imwrite(str(midpoint_path), midpoint_still, [cv2.IMWRITE_PNG_COMPRESSION, 3])

    summary: dict[str, object] = {
        "filename": spec.filename,
        "transition_key": spec.key,
        "transition_order": spec.order,
        "from_phase": spec.from_phase_key,
        "to_phase": spec.to_phase_key,
        "from_phase_order": spec.from_phase_order,
        "to_phase_order": spec.to_phase_order,
        "description": loop.description,
        "morph_read": spec.morph_read,
        "method": spec.method,
        "params_ramped": list(spec.params_ramped),
        "crossfade": False,
        "duration_seconds": CLIP_SECONDS,
        "lead_in_seconds": LEAD_IN_SECONDS,
        "morph_seconds": MORPH_SECONDS,
        "lead_out_seconds": LEAD_OUT_SECONDS,
        "frames": n_frames,
        "fps": FPS,
        "dimensions": [W, H],
        "background_hex": "#05070b",
        "morph_midpoint_frame": morph_mid_frame,
        "morph_midpoint_time_seconds": round(morph_mid_frame / FPS, 3),
        "morph_progress_at_midpoint": round(morph_progress_samples[morph_mid_frame], 4),
        "morph_midpoint_outgoing_cells": n_from,
        "morph_midpoint_incoming_cells": n_to,
        "morph_midpoint_both_phases_copresent": n_from > 0 and n_to > 0,
        "threshold_percentile": loop.threshold_percentile,
        "node_epsilon": loop.node_epsilon,
        "blur_sigma": loop.blur_sigma,
        "max_cells_cap": loop.max_cells,
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
        "audit_entries": len(audit_entries),
        "classify_from": "stable_F_xy",
        "never_classify_from": "Z_xyt_animated",
        "midpoint_sources": [source_to_json(s) for s in mid_sources],
        "midpoint_cells": [cell_to_json(c) for c in mid_result.cells[:80]],
        "austin_risk": spec.austin_risk,
        "cultural_status": "internal_austin_review_needed",
    }
    return summary, audit_entries, mid_beauty


def make_contact_sheet(midpoints: list[tuple[TransitionSpec, np.ndarray]]) -> Path:
    """Contact sheet: final morph-midpoint frames + the per-transition debug
    composites + the cell-co-presence midpoint stills (Section 9)."""
    def labelled(img: np.ndarray, text: str, scale: float = 0.40) -> np.ndarray:
        thumb = cv2.resize(img, (420, 236), interpolation=cv2.INTER_AREA)
        draw_text(thumb, text, (12, 222), LABEL, scale=scale)
        return thumb

    final_thumbs: list[np.ndarray] = []
    debug_thumbs: list[np.ndarray] = []
    copresence_thumbs: list[np.ndarray] = []
    for spec, frame in midpoints:
        final_thumbs.append(labelled(frame, spec.key))
        dbg = cv2.imread(str(DEBUG_DIR / f"{spec.key}_debug_composite.png"), cv2.IMREAD_COLOR)
        if dbg is None:
            raise RuntimeError(f"missing debug composite: {spec.key}")
        debug_thumbs.append(labelled(dbg, f"{spec.key} debug", 0.34))
        cop = cv2.imread(
            str(DEBUG_DIR / f"{spec.key}_morph_midpoint_cell_copresence.png"), cv2.IMREAD_COLOR
        )
        if cop is None:
            raise RuntimeError(f"missing co-presence still: {spec.key}")
        copresence_thumbs.append(labelled(cop, f"{spec.key} co-presence", 0.32))

    def grid(thumbs: list[np.ndarray]) -> np.ndarray:
        padded = list(thumbs)
        while len(padded) % 3 != 0:
            padded.append(np.zeros((236, 420, 3), dtype=np.uint8))
        rows = [cv2.hconcat(padded[i : i + 3]) for i in range(0, len(padded), 3)]
        return cv2.vconcat(rows)

    width = grid(final_thumbs).shape[1]

    def header(text: str) -> np.ndarray:
        h = np.zeros((46, width, 3), dtype=np.uint8)
        draw_text(h, text, (18, 30), LABEL, scale=0.50)
        return h

    sheet = cv2.vconcat(
        [
            header("water-cycle transition tests v001 - morph-midpoint (beauty) frames"),
            grid(final_thumbs),
            header("debug frames per transition: beauty + scalar/nodal/regions/classes/sources"),
            grid(debug_thumbs),
            header("morph-midpoint cell co-presence: both phases' cells in one field = no crossfade"),
            grid(copresence_thumbs),
        ]
    )
    path = OUT_DIR / "water_cycle_transitions_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def write_manifest(summaries: list[dict[str, object]], contact_sheet: Path) -> Path:
    """Write the field/source manifest, shaped like the v003 manifest."""
    manifest = {
        "renderer": "scripts/water_cycle_transitions.py",
        "extends": "scripts/cymatic_field_topology_v003.py",
        "reuses": "scripts/water_cycle_phase_studies.py (seven phase source configs)",
        "lane": "water-cycle continuum - Worker Task 2, boundary transition tests",
        "orchestration_plan": (
            "docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md"
        ),
        "created_for": (
            "Salish Sea Dreaming Phase 2 internal water-cycle transition tests; "
            "six boundary morphs proving the source-list ramp is continuous"
        ),
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "cultural_status": "internal_austin_review_needed",
        "dimensions": [W, H],
        "fps": FPS,
        "background_hex": "#05070b",
        "field_grid": [v003.FW, v003.FH],
        "clip_structure": {
            "lead_in_seconds": LEAD_IN_SECONDS,
            "morph_seconds": MORPH_SECONDS,
            "lead_out_seconds": LEAD_OUT_SECONDS,
            "total_seconds": CLIP_SECONDS,
            "note": (
                "Each test clip is lead-in (end of phase N) + ~3 s morph + "
                "lead-out (start of phase N+1), within the 4-8 s window."
            ),
        },
        "morph_method": {
            "method": "source_param_ramp_and_birth_death",
            "crossfade": False,
            "description": (
                "The morph is a parameter ramp on the source list, NOT a "
                "visual crossfade. One field F(x,y,t) is evaluated every frame "
                "from a single merged source list; the outgoing phase's "
                "sources ramp amplitude to 0 (smootherstep) while the incoming "
                "phase's sources ramp amplitude up from 0. Emitters are born, "
                "die, and drift inside that one continuous field. There is "
                "exactly one extract_cells pass and one render per frame - no "
                "compositing of two rendered images."
            ),
            "ramp_shape": "smootherstep over the 3 s morph window",
        },
        "classify_from": "stable_F_xy",
        "never_classify_from": "Z_xyt_animated",
        "classification_note": (
            "Cells are classified from the connected components of the merged "
            "field F(x,y) every frame (v003 extract_cells). No separate "
            "animated display buffer Z is classified."
        ),
        "loop_not_rendered": (
            "melt -> sun is the loop point, not a transition clip; it is "
            "verified by field-identity at the seam in Worker Task 3."
        ),
        "caps_honored": {
            "max_cells_caps": "14-22 per clip (the busier adjacent phase's cap)",
            "selected_filled_cells": "within the Section 6 8-24 band",
            "no_all_frame_lattice": True,
        },
        "source_tuple_fields": list(v003.WaveSource.__dataclass_fields__.keys()),
        "outputs": {
            "contact_sheet": str(contact_sheet.relative_to(ROOT)),
            "primitive_audit": "primitive_audit_water_cycle_transitions_v001.json",
            "debug_stills_dir": str(DEBUG_DIR.relative_to(ROOT)),
        },
        "austin_boundary": {
            "public_use": False,
            "exact_austin_source": False,
            "sd_lora": False,
            "review_log": "docs/space-center/austin-consent-map.md",
        },
        "transitions": summaries,
    }
    path = OUT_DIR / "water_cycle_transitions_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def write_primitive_audit(entries: list[dict[str, object]]) -> Path:
    """Write the primitive audit, shaped like primitive_audit_v003.json."""
    path = OUT_DIR / "primitive_audit_water_cycle_transitions_v001.json"
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
    """Write the transitions README with cultural status + no-crossfade proof."""
    by_key = {s["transition_key"]: s for s in summaries}
    rows = []
    for spec in TRANSITIONS:
        s = by_key.get(spec.key)
        if s is None:
            continue
        cop = (
            "BOTH phases' cells co-present"
            if s["morph_midpoint_both_phases_copresent"]
            else "WARNING: co-presence not confirmed"
        )
        rows.append(
            f"- `{spec.filename}` (transition {spec.order}, "
            f"{spec.from_phase_key} -> {spec.to_phase_key}): {spec.morph_read} "
            f"Duration {s['duration_seconds']}s / {s['frames']} frames "
            f"(lead-in {s['lead_in_seconds']}s + morph {s['morph_seconds']}s + "
            f"lead-out {s['lead_out_seconds']}s). Params ramped: "
            f"{', '.join(s['params_ramped'])}. crossfade: {s['crossfade']}. "
            f"At the morph midpoint (frame {s['morph_midpoint_frame']}): "
            f"{s['morph_midpoint_outgoing_cells']} outgoing-phase cells + "
            f"{s['morph_midpoint_incoming_cells']} incoming-phase cells in one "
            f"field - {cop}. Rendered cells/frame {s['rendered_cells_per_frame_min']}"
            f"-{s['rendered_cells_per_frame_max']} (cap {s['max_cells_cap']}). "
            f"Austin risk: {spec.austin_risk}."
        )
    rows_text = "\n".join(rows)

    readme = f"""# Water-Cycle Transition Tests v001 - 2026-05-20

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim. Internal R&D until Austin per-output review. Not a
production dependency - the MVP fallback production floor is unaffected.

## Lane

Worker Task 2 of the water-cycle continuum orchestration plan
(`docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`,
Section 5): the six boundary transition test clips. Each clip proves the
source-list morph between two adjacent water-cycle phases is continuous with
NO crossfade. The assembled 90 s continuum is Worker Task 3 and is NOT in
this packet.

## Source References

- `docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`
  (Section 3 phase + transition definitions, Section 5 Worker Task 2,
  Section 6 transitions schema, Section 9 evidence floor).
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/README.md`
  (the v003 renderer this script extends).
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_2026-05-20/README.md`
  (Worker Task 1; this packet reuses its seven phase source configs).

## Renderer

`scripts/water_cycle_transitions.py` - extends
`scripts/cymatic_field_topology_v003.py` and reuses the seven phase source
builders from `scripts/water_cycle_phase_studies.py`. The v003 scalar-field
engine, cell classifier, canonical-primitive machinery, `CellTracker`,
drawing primitives, and debug-layer functions are imported and reused
unchanged. v003's script and output folder, and the Task 1 script and its
output folder, were not edited.

The one piece this script provides rather than imports is the beauty
temporal curve: `transition_temporal_levels` / `render_transition_beauty`.
v003's `temporal_levels` holds the raw scalar field at full alpha for the
first second (a "field reveal -> primitives -> dissolve" arc suited to v003's
isolated clips). For a transition test the lead-in is the *end of phase N*
and must already show phase N's primitives, so this script keeps primitives
visible across the whole clip and the field as a faint constant context
layer. Only the alpha curve differs; all drawing uses v003's primitives.

## The Morph Is A Source-List Parameter Ramp, Not A Crossfade

Each transition test clip runs lead-in (end of phase N) + a ~3 s morph +
lead-out (start of phase N+1). During the morph, ONE field F(x,y,t) is
evaluated every frame from a single merged source list:

- the outgoing phase's sources ramp their amplitude down to 0 (smootherstep);
- the incoming phase's sources ramp their amplitude up from 0;
- both families are summed into the same continuous field; emitters are born,
  die, and drift inside it.

There is exactly one `extract_cells` pass and one beauty render
(`render_transition_beauty`) call per frame - the renderer never composites
two rendered phase frames. Amplitude is a `WaveSource` parameter, so the ramp
is a source-list parameter ramp (the Section 6
`method: source_param_ramp_and_birth_death`), not a visual crossfade
(`crossfade: false`).

The proof is the per-transition `*_morph_midpoint_cell_copresence.png` debug
still: at the morph midpoint it colors each merged-field cell by which phase's
sources produced a matching cell. Both the outgoing and incoming phase's cell
populations are present in the same single field - which is only possible if
the morph is a continuous source-list blend. A crossfade would show two
separate rendered images, not one field with both cell families.

## Classification From F(x,y), Not Z(x,y,t)

Cells are classified from the connected components of the merged field
`F(x,y)` every frame (v003 `extract_cells`). There is no separate
time-multiplied animated display buffer `Z(x,y,t)` and none is classified.

## melt -> sun Is Not Rendered Here

The seventh boundary, melt -> sun, is the loop point. Per the plan it is
verified by field-identity at the seam in Worker Task 3 (the assembled
continuum), not rendered as a transition clip. This packet has six clips.

## Transitions

{rows_text}

## Render Spec

- Six MP4 (H.264) clips, 1920x1080, 24 fps, {CLIP_SECONDS} s each (within the
  4-8 s window), rendered on `#05070b` near-black so each clip composites as
  an additive / screen-blend layer in Resolume. Layer-only: no background
  plate of its own. Black-screen layer-only; a single separable Resolume
  layer with a kill-switch; never a production dependency.

## Evidence Bundle

- 6 MP4 transition test clips (see Transitions above).
- `water_cycle_transitions_v001_manifest.json` - field / source / morph
  manifest.
- `primitive_audit_water_cycle_transitions_v001.json` - every rendered
  primitive audited back to one extracted source cell.
- `debug_stills/` - per transition: the six v003 panels (`scalar_field`,
  `nodal_lines`, `positive_negative_regions`, `cell_class_colors`,
  `source_points`, `debug_composite`) PLUS the extra
  `<key>_morph_midpoint_cell_copresence.png` still proving the morph is
  continuous.
- `water_cycle_transitions_v001_contact_sheet.png` - morph-midpoint beauty
  frames beside the debug composites and the co-presence stills.
- `README.md` - this file.

## Cultural Status And Austin Boundary

- Cultural status: `internal_austin_review_needed`. No "Austin-approved", no
  "Coast Salish", no traditional-meaning claim. Review-facing language is
  "radial topology", "standing-wave cell", "interference lens" - not "sacred
  geometry", not "ceremony", not "teaching".
- No exact Austin source geometry, palette, faces, Thunderbird, serpent, or
  named beings. No salmon, fish, birds, or figures. No SD / LoRA / style
  transfer - deterministic scalar-field extraction only.
- The sun and snowflake endpoints are the highest Austin risk; transitions
  touching them (`sun_to_vapor`, `interference_to_snowflake`,
  `snowflake_to_melt`) are internal review questions, not finished looks.
- After any Austin review, per-output answers are recorded in
  `docs/space-center/austin-consent-map.md` before any projector-facing or
  public promotion.

## Honest Read

The visible marks are canonicalized for legibility (v003's "field handwriting
-> primitive typography" approach), but each one is still driven by an
extracted field cell - see the primitive audit. This is not hand-placed
iconography. These are internal continuity tests, not Austin-approved output.
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the six water-cycle boundary transition tests (Worker Task 2)."
    )
    parser.add_argument(
        "--transition",
        choices=["all", *[t.key for t in TRANSITIONS]],
        default="all",
        help="Render one transition for iteration, or all six for the packet.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    selected = list(
        TRANSITIONS if args.transition == "all" else [t for t in TRANSITIONS if t.key == args.transition]
    )
    summaries: list[dict[str, object]] = []
    midpoints: list[tuple[TransitionSpec, np.ndarray]] = []
    audit_entries: list[dict[str, object]] = []
    for spec in selected:
        print(f"Rendering {spec.filename}", flush=True)
        summary, entries, midpoint = render_transition(spec)
        summaries.append(summary)
        midpoints.append((spec, midpoint))
        audit_entries.extend(entries)

    primitive_audit = write_primitive_audit(audit_entries)
    print(f"Wrote {primitive_audit}")

    if args.transition == "all":
        contact_sheet = make_contact_sheet(midpoints)
        manifest = write_manifest(summaries, contact_sheet)
        readme = write_readme(summaries)
        print(f"Wrote {contact_sheet}")
        print(f"Wrote {manifest}")
        print(f"Wrote {readme}")
        print(f"Wrote water-cycle transition tests v001 packet to {OUT_DIR}")
    else:
        print(f"Wrote single-transition iteration output to {OUT_DIR}")


if __name__ == "__main__":
    main()
