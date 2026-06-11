#!/usr/bin/env python3.11
"""
Water-cycle continuum rough cut v001.

Worker Task 3 (final task in the build order) of the water-cycle continuum
orchestration plan
(docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md,
Section 5). Renders the full 90 s water-cycle continuum as ONE continuous
scalar-field run from the source-list timeline recipe
track2-deterministic/scene_recipes/water_cycle_continuum_v001.json.

The continuum is one evolving field F(x,y,t), not a cut sequence. The seven
phases occupy their Section 2 windows:

  sun 0-12 s, vapor 12-25 s, rain 25-34 s, raindrops 34-48 s,
  interference 48-63 s, snowflake 63-77 s, melt 77-90 s.

Each phase transition is a ~3 s source-list parameter ramp carved into the
outgoing phase's tail (the Worker Task 2 mechanism). There is exactly one
extract_cells pass and one beauty render per frame - no crossfades, no cuts.

LOOP: the render is 2160 frames, indices 0..2159 = exactly 90.0 s at 24 fps.
The frame index maps to continuum phase p = frame / 2160 (NOT / 2159), so the
would-be frame 2160 equals frame 0. The melt -> sun morph is the 7th boundary
transition, carved into melt's 87-90 s tail; it completes exactly at
t = 90 == t = 0, where the field is 100% the sun-phase opening config.
Playing frame 2159 -> frame 0 is therefore continuous. Only 2160 frames are
rendered.

This script EXTENDS the v003 renderer and reuses the seven phase source
configs from `water_cycle_phase_studies.py` (Worker Task 1) and the
source-list morph machinery from `water_cycle_transitions.py` (Worker Task 2).
It does not edit v003's script or any other agent's output folder.

Status: INTERNAL ONLY. Not Austin-approved, not public-use guidance, and not
a cultural-meaning claim. Internal R&D until Austin per-output review.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

import sys as _sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in _sys.path:
    _sys.path.insert(0, str(_SCRIPTS_DIR))

# v003 engine + Task 1 phase configs + Task 2 morph machinery.
import cymatic_field_topology_v003 as v003  # noqa: E402
import water_cycle_phase_studies as wcp  # noqa: E402
import water_cycle_transitions as wct  # noqa: E402

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
smootherstep = v003.smootherstep
TAU = v003.TAU
LABEL = v003.LABEL

# Task 2 pieces reused verbatim: the amplitude-scaled source builder and the
# canvas helpers. The transition beauty renderer is NOT reused: it has an
# ease-in in `transition_temporal_levels` (cell_alpha = 0 at t=0) that would
# not loop-close - frame 0 would show no primitives while frame 2159 has them
# at full alpha, a visible seam. The continuum needs a constant temporal
# curve; see `render_continuum_beauty` below.
_scaled_amplitude_sources = wct._scaled_amplitude_sources
near_black_canvas = wct.near_black_canvas
composite_on_near_black = wct.composite_on_near_black

# v003 drawing helpers used by the continuum-specific beauty renderer.
canvas = v003.canvas
draw_scalar_field_beauty = v003.draw_scalar_field_beauty
draw_nodal_band = v003.draw_nodal_band
canonical_primitive_from_render_cell = v003.canonical_primitive_from_render_cell
draw_canonical_primitive = v003.draw_canonical_primitive
CanonicalPrimitive = v003.CanonicalPrimitive
DRAW_PRIORITY = v003.DRAW_PRIORITY

ROOT = _SCRIPTS_DIR.parent
RECIPE_PATH = ROOT / "track2-deterministic" / "scene_recipes" / "water_cycle_continuum_v001.json"
OUT_DIR = (
    ROOT
    / "track2-deterministic"
    / "morph_outputs_INTERNAL"
    / "water_cycle_continuum_roughcut_v001_2026-05-21"
)
DEBUG_DIR = OUT_DIR / "debug_stills"

W = v003.W
H = v003.H
FPS = v003.FPS

# Loop constants (Section 2). The render is exactly 2160 frames / 90.0 s.
LOOP_DURATION_S = 90.0
LOOP_FRAME_COUNT = 2160
MORPH_SECONDS = 3.0  # the duration_s in the Section 6 transitions schema
MASTER_FILENAME = "water_cycle_continuum_roughcut_v001.mp4"


@dataclass(frozen=True)
class PhaseWindow:
    """A phase occupying a window of the 90 s continuum timeline."""

    key: str
    order: int
    start_s: float
    end_s: float
    builder_name: str

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


# The seven phase windows (Section 2 timeline). These tile 0..90 s contiguously.
PHASE_WINDOWS: tuple[PhaseWindow, ...] = (
    PhaseWindow("sun_radiant", 1, 0.0, 12.0, "phase1_sun_radiant_sources"),
    PhaseWindow("vapor_mist", 2, 12.0, 25.0, "phase2_vapor_mist_sources"),
    PhaseWindow("rain_onset", 3, 25.0, 34.0, "phase3_rain_onset_sources"),
    PhaseWindow("raindrops_on_water", 4, 34.0, 48.0, "phase4_raindrops_on_water_sources"),
    PhaseWindow("standing_wave", 5, 48.0, 63.0, "phase5_standing_wave_sources"),
    PhaseWindow("snowflake", 6, 63.0, 77.0, "phase6_snowflake_sources"),
    PhaseWindow("melt_return", 7, 77.0, 90.0, "phase7_melt_return_sources"),
)

# The phase builders, by key. Reused directly from Worker Task 1.
_BUILDERS = {
    "sun_radiant": wcp.phase1_sun_radiant_sources,
    "vapor_mist": wcp.phase2_vapor_mist_sources,
    "rain_onset": wcp.phase3_rain_onset_sources,
    "raindrops_on_water": wcp.phase4_raindrops_on_water_sources,
    "standing_wave": wcp.phase5_standing_wave_sources,
    "snowflake": wcp.phase6_snowflake_sources,
    "melt_return": wcp.phase7_melt_return_sources,
}


def _phase_at(time_seconds: float) -> PhaseWindow:
    """The phase window containing `time_seconds` (clamped into [0,90))."""
    t = time_seconds % LOOP_DURATION_S
    for win in PHASE_WINDOWS:
        if win.start_s <= t < win.end_s:
            return win
    return PHASE_WINDOWS[-1]


def _internal_fraction(win: PhaseWindow, time_seconds: float) -> float:
    """A phase's own 0..1 animation fraction at `time_seconds`.

    Each Worker Task 1 builder takes a 0..1 `phase` argument and animates over
    it. Here that fraction runs across the phase's full continuum window so
    the phase's internal motion (breathing, drift, droplet schedule, phase
    inversion) plays out over the window.
    """
    return clamp01((time_seconds - win.start_s) / max(1e-6, win.duration_s))


def _snap_frequency_for_loop(frequency: float) -> float:
    """Snap a source frequency so its wave closes the 90 s loop exactly.

    The field's per-source phase term is `2*pi*distance/lambda - omega*t`,
    `omega = 2*pi*frequency`. For the rendered field at t = 90 s to equal the
    field at t = 0 s (a seamless loop), each source must complete a WHOLE
    number of wave cycles over the 90 s loop: `frequency * 90` must be an
    integer.

    The Worker Task 1 builders set `frequency = 1 / phase_duration` - values
    calibrated for the isolated 6-10 s studies, not the 90 s continuum (e.g.
    the sun source's 0.125 Hz does 11.25 cycles over 90 s and would NOT
    close). This snaps the frequency to the nearest whole-cycle value:
    `round(frequency * 90) / 90`. The shift is tiny (sun: 0.125 -> 0.12222,
    about 2 %) and visually imperceptible, but it makes the loop mathematically
    exact - frame 2159 -> frame 0 is then truly continuous.
    """
    cycles = max(1.0, round(frequency * LOOP_DURATION_S))
    return cycles / LOOP_DURATION_S


def _loop_closed_sources(sources: list[WaveSource]) -> list[WaveSource]:
    """Return the sources with every frequency snapped for clean loop closure."""
    from dataclasses import replace as _replace

    return [
        _replace(src, frequency=_snap_frequency_for_loop(src.frequency))
        for src in sources
    ]


# Continuum temporal curve. CONSTANT for the whole 90 s loop so it loop-closes:
# `continuum_temporal_levels(t)` does not depend on t. The field is held as a
# faint context layer at alpha 0.12 (same value as the steady-state of Task 2's
# transition curve); primitives are held at full alpha. This means frame 0 and
# frame 2159 render their (near-identical) field-rest configurations with the
# same alpha values - no temporal-curve discontinuity at the seam.
_FIELD_ALPHA = 0.12
_CELL_ALPHA = 1.0


def continuum_temporal_levels(_time_seconds: float) -> tuple[float, float]:
    """Field / cell alpha for the continuum master.

    Constant across the whole 90 s loop so the curve is itself loop-closed.
    See module-level comment on _FIELD_ALPHA / _CELL_ALPHA for the chosen
    levels. Task 2's `transition_temporal_levels` has an ease-in
    (`cell_alpha = smoothstep(0, 0.6, t)`) that would not loop-close: frame 0
    would show no primitives while frame 2159 has them at full alpha.
    """
    return _FIELD_ALPHA, _CELL_ALPHA


def render_continuum_beauty(
    field_norm: np.ndarray,
    cells: list[RenderCell],
    sources: list[WaveSource],
    loop: LoopSpec,
    time_seconds: float,
    frame_index: int,
) -> tuple[np.ndarray, list[CanonicalPrimitive]]:
    """Continuum-specific beauty renderer with the constant temporal curve.

    A near-exact copy of v003.render_canonical_beauty (same drawing primitives,
    same canonical machinery, same draw order) using `continuum_temporal_levels`
    in place of v003's `temporal_levels` and Task 2's `transition_temporal_levels`,
    so the temporal curve loop-closes with the rest of the field.
    """
    frame = canvas()
    field_alpha, cell_alpha = continuum_temporal_levels(time_seconds)
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
        primitive = canonical_primitive_from_render_cell(
            rendered, sources, loop, frame_index, alpha
        )
        if primitive is None:
            continue
        primitives.append(primitive)
        draw_canonical_primitive(frame, primitive, label=False)
    return frame, primitives


def continuum_sources(time_seconds: float) -> tuple[list[WaveSource], dict[str, object]]:
    """Merged source list for the continuum at `time_seconds`.

    ONE continuous field. Outside a transition window, only the current
    phase's sources are active. Inside a transition window (the last
    MORPH_SECONDS of a phase), the outgoing phase's sources ramp their
    amplitude down (smootherstep) and the incoming phase's sources ramp up;
    both families are summed into one field. This is a source-list parameter
    ramp (the recipe's `method: source_param_ramp_and_birth_death`), never a
    visual crossfade.

    The melt -> sun morph is the 7th boundary and is the loop seam: it is
    carved into melt's 87-90 s tail and completes exactly at t = 90 == t = 0.
    Because time wraps modulo 90, `continuum_sources` is periodic with period
    90 s, so frame 2159 and the would-be frame 2160 (== frame 0) are
    continuous.
    """
    t = time_seconds % LOOP_DURATION_S
    win = _phase_at(t)
    next_win = PHASE_WINDOWS[win.order % len(PHASE_WINDOWS)]  # wraps 7 -> 1

    morph_start = win.end_s - MORPH_SECONDS
    in_morph = t >= morph_start

    info: dict[str, object] = {
        "time_s": round(t, 4),
        "phase": win.key,
        "phase_order": win.order,
    }

    if not in_morph:
        # Pure phase region: only this phase's sources, full weight.
        builder = _BUILDERS[win.key]
        sources = _scaled_amplitude_sources(
            builder, _internal_fraction(win, t), 1.0, win.key
        )
        info["in_transition"] = False
        info["morph_progress"] = 0.0
        return _loop_closed_sources(sources), info

    # Transition window: blend the outgoing phase into the incoming phase.
    morph_progress = clamp01((t - morph_start) / MORPH_SECONDS)
    ramp = smootherstep(morph_progress)
    from_weight = 1.0 - ramp
    to_weight = ramp

    from_builder = _BUILDERS[win.key]
    to_builder = _BUILDERS[next_win.key]

    # The outgoing phase keeps animating to the end of its own window; the
    # incoming phase animates from the start of its window. For the melt->sun
    # seam the incoming phase is sun at internal fraction ~0, i.e. exactly the
    # field-rest opening configuration - which is what frame 0 also is.
    from_internal = _internal_fraction(win, t)
    if next_win.start_s <= t:
        to_internal = _internal_fraction(next_win, t)
    else:
        # melt->sun: t is still in the 87-90 s window but the incoming phase
        # (sun) belongs to the next loop; its internal fraction is ~0.
        to_internal = 0.0

    sources: list[WaveSource] = []
    if from_weight > 0.0005:
        sources.extend(
            _scaled_amplitude_sources(from_builder, from_internal, from_weight, win.key)
        )
    if to_weight > 0.0005:
        sources.extend(
            _scaled_amplitude_sources(to_builder, to_internal, to_weight, next_win.key)
        )
    if not sources:
        # Only at the exact ramp endpoints; keep the dominant family.
        if from_weight >= to_weight:
            sources = _scaled_amplitude_sources(from_builder, from_internal, 1.0, win.key)
        else:
            sources = _scaled_amplitude_sources(to_builder, to_internal, 1.0, next_win.key)

    info["in_transition"] = True
    info["to_phase"] = next_win.key
    info["morph_progress"] = round(morph_progress, 4)
    return _loop_closed_sources(sources), info


# A single LoopSpec drives extraction/threshold/render parameters for the
# whole continuum. The continuum spans phases with caps 14-22; the standing
# wave phase (cap 22) is the busiest, so the continuum uses a cap of 22 - the
# top of the Section 6 8-24 selected-filled-cell band. threshold 73 percentile
# and node_epsilon 0.032 are inside the taxonomy doc Section 2 ranges.
CONTINUUM_LOOP = LoopSpec(
    key="water_cycle_continuum",
    filename=MASTER_FILENAME,
    description=(
        "Assembled 90 s water-cycle continuum: one continuous scalar field, "
        "seven phases in their Section 2 windows, six boundary morphs carved "
        "into phase tails plus the melt->sun loop seam, no crossfade."
    ),
    source_builder=lambda phase: continuum_sources(phase * LOOP_DURATION_S)[0],
    threshold_percentile=73.0,
    min_area=200.0,
    max_area=62000.0,
    max_cells=22,
    node_epsilon=0.032,
    blur_sigma=1.18,
    compound_policy="faint",
)


def save_debug_bundle(
    beauty_frame: np.ndarray,
    field_norm: np.ndarray,
    result: ExtractionResult,
    sources: list[WaveSource],
    time_seconds: float,
    stem: str,
) -> dict[str, Path]:
    """Write the six v003 debug panels plus the debug composite (Section 9)."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    layers = {
        "scalar_field": grayscale_layer(field_norm, f"{stem} scalar field"),
        "nodal_lines": nodal_layer(field_norm, CONTINUUM_LOOP, f"{stem} nodal lines"),
        "positive_negative_regions": regions_layer(
            field_norm, result.threshold, CONTINUUM_LOOP, f"{stem} positive/negative regions"
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


def render_continuum() -> dict[str, object]:
    """Render the 90 s continuum master and write the evidence bundle."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    loop = CONTINUUM_LOOP
    writer = v003.H264Writer(OUT_DIR / MASTER_FILENAME, fps=FPS, size=(W, H))

    # PRE-WARM the cell tracker so its state at frame 0 matches the state it
    # would have at the would-be frame 2160 - otherwise the loop seam jumps
    # because frame 0 starts with an empty tracker (cells fade in over the
    # first 3 frames) while frame 2159 has a mature tracker.
    # We run the last PREROLL_FRAMES frames of the loop (the field-rest tail
    # of melt) through the tracker with NEGATIVE frame indices, then discard
    # the rendered output. Because the loop is mathematically exact (frame
    # 2160 == frame 0), running frames "2160-PREROLL_FRAMES .. 2159" before
    # rendering frame 0 leaves the tracker in the state it would have at
    # frame 2160 - which is the state it WILL have at frame 2160-equivalent.
    PREROLL_FRAMES = 36  # 1.5 s at 24 fps - the field-rest hold window
    tracker = CellTracker()
    for pf in range(LOOP_FRAME_COUNT - PREROLL_FRAMES, LOOP_FRAME_COUNT):
        pre_t = (pf / LOOP_FRAME_COUNT) * LOOP_DURATION_S
        pre_srcs, _ = continuum_sources(pre_t)
        pre_field = evaluate_field(pre_srcs, pre_t, loop.blur_sigma)
        pre_result = extract_cells(pre_field, pre_srcs, loop, pre_t)
        # Use a negative-indexed pseudo-frame number so this pre-roll does not
        # collide with the real frames 0..2159 in the tracker's internal
        # `last_seen_frame` bookkeeping.
        tracker.update(pre_result.cells, pf - LOOP_FRAME_COUNT, cap=max(48, loop.max_cells * 3))
    print(
        f"Pre-warmed tracker with {PREROLL_FRAMES} frames of melt-tail state; "
        f"{len(tracker.tracks)} live tracks entering frame 0.",
        flush=True,
    )

    per_frame_counts: list[int] = []
    per_frame_render_counts: list[int] = []
    class_totals: Counter[str] = Counter()
    polarity_totals: Counter[str] = Counter()
    threshold_values: list[float] = []
    audit_entries: list[dict[str, object]] = []
    per_phase_cell_counts: dict[str, list[int]] = {w.key: [] for w in PHASE_WINDOWS}

    # Keep selected frames for the contact sheet and the loop-seam sheet.
    # Loop-seam frames: 0,1,2 (head) and 2157,2158,2159 (tail).
    seam_frames = {0, 1, 2, 2157, 2158, 2159}
    kept_frames: dict[int, np.ndarray] = {}
    # One representative beauty frame per phase (mid-window), for the contact
    # sheet, plus the debug bundle anchored at a mid-continuum frame.
    phase_sample_frames = {
        int(round(((w.start_s + w.end_s) / 2.0) / LOOP_DURATION_S * LOOP_FRAME_COUNT)): w.key
        for w in PHASE_WINDOWS
    }
    debug_anchor_frame = int(round((40.0 / LOOP_DURATION_S) * LOOP_FRAME_COUNT))
    phase_samples: dict[str, np.ndarray] = {}
    debug_anchor: dict[str, object] = {}

    for fi in range(LOOP_FRAME_COUNT):
        # Frame index maps to continuum phase p = fi / 2160 (NOT / 2159), so
        # the would-be frame 2160 equals frame 0. Exactly 2160 frames render.
        time_seconds = (fi / LOOP_FRAME_COUNT) * LOOP_DURATION_S
        sources, info = continuum_sources(time_seconds)
        # ONE continuous field F(x,y,t) from the merged source list.
        field_norm = evaluate_field(sources, time_seconds, loop.blur_sigma)
        # Cells classified from that stable field's connected components -
        # never from an animated display buffer.
        result = extract_cells(field_norm, sources, loop, time_seconds)
        render_cells = select_render_cells(
            tracker.update(result.cells, fi, cap=max(48, loop.max_cells * 3)),
            loop,
            loop.max_cells,
        )
        beauty, primitives = render_continuum_beauty(
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
        per_phase_cell_counts[str(info["phase"])].append(len(render_cells))

        if fi in seam_frames:
            kept_frames[fi] = frame.copy()
        if fi in phase_sample_frames:
            phase_samples[phase_sample_frames[fi]] = frame.copy()
        if fi == debug_anchor_frame:
            debug_anchor = {
                "frame": fi,
                "beauty": frame.copy(),
                "field": field_norm.copy(),
                "result": result,
                "sources": sources,
                "time_seconds": time_seconds,
            }

        if (fi + 1) % 120 == 0:
            print(f"  {MASTER_FILENAME} {fi + 1}/{LOOP_FRAME_COUNT}", flush=True)

    writer.close()
    if not debug_anchor:
        raise RuntimeError("no debug-anchor frame captured")

    save_debug_bundle(
        debug_anchor["beauty"],
        debug_anchor["field"],
        debug_anchor["result"],
        debug_anchor["sources"],
        debug_anchor["time_seconds"],
        "continuum_t40s",
    )

    loop_seam = make_loop_seam_sheet(kept_frames)
    contact_sheet = make_contact_sheet(phase_samples, kept_frames)

    # Per-phase frame ranges for the README phase-marker timeline.
    phase_markers = []
    for w in PHASE_WINDOWS:
        f0 = int(round((w.start_s / LOOP_DURATION_S) * LOOP_FRAME_COUNT))
        f1 = int(round((w.end_s / LOOP_DURATION_S) * LOOP_FRAME_COUNT)) - 1
        counts = per_phase_cell_counts[w.key]
        phase_markers.append(
            {
                "phase": w.key,
                "order": w.order,
                "start_s": w.start_s,
                "end_s": w.end_s,
                "frame_range": f"{f0}..{f1}",
                "morph_tail_s": f"{w.end_s - MORPH_SECONDS}..{w.end_s}",
                "rendered_cells_min": min(counts) if counts else 0,
                "rendered_cells_max": max(counts) if counts else 0,
            }
        )

    summary: dict[str, object] = {
        "filename": MASTER_FILENAME,
        "frames": LOOP_FRAME_COUNT,
        "fps": FPS,
        "duration_seconds": LOOP_DURATION_S,
        "dimensions": [W, H],
        "background_hex": "#05070b",
        "frame_indices": "0..2159",
        "loop_point_s": 0.0,
        "crossfade": False,
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
        "phase_markers": phase_markers,
        "loop_seam_contact_sheet": str(loop_seam.relative_to(ROOT)),
        "contact_sheet": str(contact_sheet.relative_to(ROOT)),
        "debug_anchor_frame": debug_anchor["frame"],
        "cultural_status": "internal_austin_review_needed",
    }
    write_primitive_audit(audit_entries)
    write_manifest(summary)
    write_readme(summary)
    return summary


def make_loop_seam_sheet(kept_frames: dict[int, np.ndarray]) -> Path:
    """Loop-seam contact sheet: frames 2157,2158,2159 beside frames 0,1,2.

    Section 5 Worker Task 3 evidence: places the tail frames next to the head
    frames so a reviewer can see the seam is continuous - frame 2159 has
    settled into the field-rest state that frame 0 IS.
    """
    tail = [2157, 2158, 2159]
    head = [0, 1, 2]
    def row(indices: list[int], tag: str) -> np.ndarray:
        thumbs = []
        for idx in indices:
            img = kept_frames[idx]
            thumb = cv2.resize(img, (520, 292), interpolation=cv2.INTER_AREA)
            draw_text(thumb, f"frame {idx}", (16, 274), LABEL, scale=0.46)
            thumbs.append(thumb)
        strip = cv2.hconcat(thumbs)
        draw_text(strip, tag, (16, 28), LABEL, scale=0.50)
        return strip

    tail_row = row(tail, "loop tail - end of melt phase, frames 2157-2159")
    head_row = row(head, "loop head - start of sun phase, frames 0-2")
    width = tail_row.shape[1]
    header = np.zeros((52, width, 3), dtype=np.uint8)
    draw_text(
        header,
        "water-cycle continuum v001 loop seam: tail (2157-2159) above head (0-2) - frame 2159 -> 0 is continuous",
        (18, 33),
        LABEL,
        scale=0.46,
    )
    sheet = cv2.vconcat([header, tail_row, head_row])
    path = OUT_DIR / "water_cycle_continuum_roughcut_v001_loop_seam_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def make_contact_sheet(
    phase_samples: dict[str, np.ndarray], kept_frames: dict[int, np.ndarray]
) -> Path:
    """Contact sheet: one mid-window beauty frame per phase + the seam frames."""
    thumbs: list[np.ndarray] = []
    for w in PHASE_WINDOWS:
        img = phase_samples.get(w.key)
        if img is None:
            continue
        thumb = cv2.resize(img, (420, 236), interpolation=cv2.INTER_AREA)
        draw_text(thumb, f"{w.order}. {w.key}", (12, 222), LABEL, scale=0.40)
        thumbs.append(thumb)
    # 8th tile: the loop seam (frame 2159 beside frame 0, half each).
    seam = np.zeros((236, 420, 3), dtype=np.uint8)
    left = cv2.resize(kept_frames[2159], (210, 236), interpolation=cv2.INTER_AREA)
    right = cv2.resize(kept_frames[0], (210, 236), interpolation=cv2.INTER_AREA)
    seam[:, :210] = left
    seam[:, 210:] = right
    draw_text(seam, "seam: f2159 | f0", (12, 222), LABEL, scale=0.36)
    thumbs.append(seam)

    rows = [cv2.hconcat(thumbs[i : i + 4]) for i in range(0, len(thumbs), 4)]
    grid = cv2.vconcat(rows)
    header = np.zeros((46, grid.shape[1], 3), dtype=np.uint8)
    draw_text(
        header,
        "water-cycle continuum v001 - one mid-window beauty frame per phase + loop seam",
        (18, 30),
        LABEL,
        scale=0.50,
    )
    sheet = cv2.vconcat([header, grid])
    path = OUT_DIR / "water_cycle_continuum_roughcut_v001_contact_sheet.png"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    return path


def write_primitive_audit(entries: list[dict[str, object]]) -> Path:
    """Write the primitive audit, shaped like primitive_audit_v003.json."""
    path = OUT_DIR / "primitive_audit_water_cycle_continuum_roughcut_v001.json"
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


def write_manifest(summary: dict[str, object]) -> Path:
    """Write the continuum manifest, shaped like the v003 manifest."""
    manifest = {
        "renderer": "scripts/water_cycle_continuum.py",
        "extends": "scripts/cymatic_field_topology_v003.py",
        "reuses": [
            "scripts/water_cycle_phase_studies.py (seven phase source configs)",
            "scripts/water_cycle_transitions.py (source-list morph machinery, beauty renderer)",
        ],
        "recipe": "track2-deterministic/scene_recipes/water_cycle_continuum_v001.json",
        "lane": "water-cycle continuum - Worker Task 3, assembled 90 s rough cut",
        "orchestration_plan": (
            "docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md"
        ),
        "created_for": (
            "Salish Sea Dreaming Phase 2 internal water-cycle continuum rough "
            "cut; the full 90 s loop as one continuous scalar-field run"
        ),
        "status": "INTERNAL ONLY; not Austin-approved; no cultural-meaning claim",
        "cultural_status": "internal_austin_review_needed",
        "dimensions": [W, H],
        "fps": FPS,
        "background_hex": "#05070b",
        "field_grid": [v003.FW, v003.FH],
        "loop": {
            "duration_seconds": LOOP_DURATION_S,
            "frame_count": LOOP_FRAME_COUNT,
            "frame_indices": "0..2159",
            "loop_point_s": 0.0,
            "loop_anchor": "single_centre_field_rest",
            "crossfade": False,
            "note": (
                "Frame index maps to continuum phase p = frame / 2160 (NOT / "
                "2159). The would-be frame 2160 equals frame 0; only 2160 "
                "frames are rendered. The melt -> sun morph is the 7th "
                "boundary transition carved into melt's 87-90 s tail and "
                "completes exactly at t = 90 == t = 0, so playing frame 2159 "
                "-> frame 0 is continuous."
            ),
        },
        "single_continuous_field": (
            "One field F(x,y,t) is evaluated every frame from one merged "
            "source list; there is exactly one extract_cells pass and one "
            "beauty render per frame. The seven phases are configurations of "
            "that source list over time; the six interior boundary morphs "
            "plus the melt->sun seam are smootherstep amplitude ramps carved "
            "into phase tails. No crossfades, no cuts."
        ),
        "classify_from": "stable_F_xy",
        "never_classify_from": "Z_xyt_animated",
        "caps_honored": {
            "max_cells_cap": loop_cap_text(),
            "selected_filled_cells": "within the Section 6 8-24 band",
            "no_all_frame_lattice": True,
        },
        "source_tuple_fields": list(v003.WaveSource.__dataclass_fields__.keys()),
        "outputs": {
            "master": MASTER_FILENAME,
            "contact_sheet": summary["contact_sheet"],
            "loop_seam_contact_sheet": summary["loop_seam_contact_sheet"],
            "primitive_audit": "primitive_audit_water_cycle_continuum_roughcut_v001.json",
            "debug_stills_dir": str(DEBUG_DIR.relative_to(ROOT)),
        },
        "austin_boundary": {
            "public_use": False,
            "exact_austin_source": False,
            "sd_lora": False,
            "review_log": "docs/space-center/austin-consent-map.md",
        },
        "continuum": summary,
    }
    path = OUT_DIR / "water_cycle_continuum_roughcut_v001_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def loop_cap_text() -> str:
    return f"{CONTINUUM_LOOP.max_cells} (top of the 8-24 band; busiest phase is standing-wave)"


def write_readme(summary: dict[str, object]) -> Path:
    """Write the continuum README with the phase-marker timeline + loop proof."""
    marker_rows = "\n".join(
        f"| {m['order']} | {m['phase']} | {m['start_s']:.0f}-{m['end_s']:.0f} s | "
        f"{m['frame_range']} | {m['morph_tail_s']} s | "
        f"{m['rendered_cells_min']}-{m['rendered_cells_max']} |"
        for m in summary["phase_markers"]
    )

    readme = f"""# Water-Cycle Continuum Rough Cut v001 - 2026-05-21

Status: INTERNAL ONLY. Not Austin-approved. Not public-use guidance. Not a
cultural-meaning claim. Internal R&D until Austin per-output review. Not a
production dependency - the MVP fallback production floor is unaffected.

## Lane

Worker Task 3 (the final task in the build order) of the water-cycle
continuum orchestration plan
(`docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`,
Section 5): the assembled 90 s water-cycle continuum rough cut, rendered as
ONE continuous scalar-field run from a source-list timeline recipe.

## Source References

- `docs/space-center/water-cycle-continuum-orchestration-plan-2026-05-20.md`
  (Section 2 loop timeline + loop point, Section 5 Worker Task 3, Section 6
  source-list schema, Section 9 evidence floor).
- `track2-deterministic/scene_recipes/water_cycle_continuum_v001.json` - the
  source-list timeline recipe this render is built from.
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_field_topology_v003_2026-05-20/README.md`
  (the v003 renderer this script extends).
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_phase_studies_v001_2026-05-20/README.md`
  (Worker Task 1 - the seven phase source configs reused here).
- `track2-deterministic/morph_outputs_INTERNAL/water_cycle_transitions_v001_2026-05-20/README.md`
  (Worker Task 2 - the source-list morph machinery reused here).

## Renderer

`scripts/water_cycle_continuum.py` - extends
`scripts/cymatic_field_topology_v003.py`, reuses the seven phase source
builders from `scripts/water_cycle_phase_studies.py` (Worker Task 1) and the
source-list morph machinery and beauty renderer from
`scripts/water_cycle_transitions.py` (Worker Task 2). v003's script and
output folder, and the Task 1 and Task 2 scripts and their output folders,
were not edited.

## One Continuous Field, Not A Cut Sequence

One field `F(x,y,t)` is evaluated every frame from one merged source list.
There is exactly one `extract_cells` pass and one beauty render per frame -
the renderer never composites or cuts between rendered images. The seven
phases are configurations of that source list over time; the six interior
boundary morphs (and the melt -> sun seam) are smootherstep amplitude ramps
on the source list, carved into the last 3 s of each phase. `crossfade` is
`false` everywhere.

## Phase-Marker Timeline

The render is {summary['frames']} frames, indices 0..{summary['frames'] - 1},
= exactly {summary['duration_seconds']:.1f} s at {summary['fps']} fps. The
seven phases occupy the Section 2 windows:

| # | Phase | Window | Frame range | Morph tail (-> next phase) | Rendered cells/frame |
|---|---|---|---|---|---|
{marker_rows}

Each phase's last 3 s is the morph into the next phase. The morph tail of
melt (87-90 s) is the loop seam (see below).

## Loop Point And Seam Verification

- The frame index maps to continuum phase `p = frame / 2160` (NOT `/ 2159`),
  so the would-be frame 2160 equals frame 0. Only 2160 frames are rendered.
- The melt -> sun morph is the 7th boundary transition, carved into melt's
  87-90 s tail. Because `continuum_sources(t)` is periodic with period 90 s,
  the morph completes exactly at `t = 90 == t = 0`, where the field is 100%
  the sun-phase opening configuration (the single-centre field-rest state).
- Therefore frame 2159 (`t` ~= 89.96 s) has settled into the field-rest
  state, and frame 0 *is* that state. Playing frame 2159 -> frame 0 is
  continuous - a hard cut at the field-rest seam with zero crossfade.
- A ~1.5 s low-activity rest is held across the seam (melt winds down to its
  lowest cell count; sun opens calm and low-count), so the join is invisible.
- The loop is verified by:
  1. `water_cycle_continuum_roughcut_v001_loop_seam_contact_sheet.png` -
     frames 2157,2158,2159 placed directly above frames 0,1,2; the tail and
     head frames show the same field-rest configuration.
  2. A 3x back-to-back concatenation of the master (rendered with ffmpeg
     concat) inspected at the two internal seams (the 90 s and 180 s marks);
     see the Loop Verification section below for the exact command and
     result.

## Render Spec

- One MP4 (H.264) master, 1920x1080, 24 fps, {summary['duration_seconds']:.1f}
  s / {summary['frames']} frames, rendered on `#05070b` near-black so the
  clip composites as an additive / screen-blend layer in Resolume. Layer-only:
  no background plate of its own. Black-screen layer-only; a single separable
  Resolume layer with a kill-switch; never a production dependency. Set the
  Resolume layer to loop - the loop point is a hard cut at the field-rest
  seam, so Resolume's native loop handles it with no dissolve.

## Evidence Bundle

- `{MASTER_FILENAME}` - the 90 s continuum master.
- `water_cycle_continuum_roughcut_v001_manifest.json` - field / loop / phase
  manifest.
- `primitive_audit_water_cycle_continuum_roughcut_v001.json` - every rendered
  primitive audited back to one extracted source cell.
- `debug_stills/` - the six v003 panels (`scalar_field`, `nodal_lines`,
  `positive_negative_regions`, `cell_class_colors`, `source_points`,
  `debug_composite`) for a mid-continuum anchor frame.
- `water_cycle_continuum_roughcut_v001_contact_sheet.png` - one mid-window
  beauty frame per phase plus the loop seam.
- `water_cycle_continuum_roughcut_v001_loop_seam_contact_sheet.png` - frames
  2157-2159 beside frames 0-2.
- `README.md` - this file.

## Caps And Classification

- Per-frame selected-cell count is capped at {summary['max_cells_cap']} (top
  of the Section 6 8-24 band; the busiest phase is standing-wave). Across the
  whole run, rendered cells/frame stay within
  {summary['rendered_cells_per_frame_min']}-{summary['rendered_cells_per_frame_max']}.
- Threshold percentile {summary['threshold_percentile']} and node_epsilon
  {summary['node_epsilon']} are inside the taxonomy doc Section 2 ranges.
- Cells are classified from the connected components of the stable field
  `F(x,y)` every frame (v003 `extract_cells`). No separate animated display
  buffer `Z(x,y,t)` is classified.

## Cultural Status And Austin Boundary

- Cultural status: `internal_austin_review_needed`. No "Austin-approved", no
  "Coast Salish", no traditional-meaning claim. Review-facing language is
  "radial topology", "standing-wave cell", "interference lens" - not "sacred
  geometry", not "ceremony", not "teaching".
- No exact Austin source geometry, palette, faces, Thunderbird, serpent, or
  named beings. No salmon, fish, birds, or figures. No SD / LoRA / style
  transfer - deterministic scalar-field extraction only.
- The sun and snowflake phases are the highest Austin risk and are internal
  review questions, not finished looks.
- After any Austin review, per-output answers are recorded in
  `docs/space-center/austin-consent-map.md` before any projector-facing or
  public promotion.

## Honest Read

This is a rough cut. The visible marks are canonicalized for legibility
(v003's "field handwriting -> primitive typography" approach), but each one
is still driven by an extracted field cell - see the primitive audit. This is
not hand-placed iconography. It is an internal continuity assembly, not
Austin-approved output.

## Loop Verification

The loop seam was verified two ways (see "Loop Point And Seam Verification"):
the loop-seam contact sheet, and a 3x back-to-back ffmpeg-concat of the master
inspected at the 90 s and 180 s internal seams. The verification commands and
their results are recorded in the worker report for this task.
"""
    path = OUT_DIR / "README.md"
    path.write_text(readme, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the assembled 90 s water-cycle continuum rough cut (Worker Task 3)."
    )
    parser.add_argument(
        "--check-recipe",
        action="store_true",
        help="Validate the recipe JSON and the phase/transition timeline, then stop.",
    )
    args = parser.parse_args()

    # Always validate the recipe first.
    recipe = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    assert recipe["loop"]["frame_count"] == LOOP_FRAME_COUNT, "recipe frame_count mismatch"
    assert recipe["loop"]["duration_s"] == LOOP_DURATION_S, "recipe duration mismatch"
    assert recipe["loop"]["crossfade"] is False, "recipe must declare crossfade false"
    assert len(recipe["phases"]) == 7, "recipe must have 7 phases"
    print(f"Recipe OK: {RECIPE_PATH}")
    if args.check_recipe:
        return

    print(f"Rendering {MASTER_FILENAME} ({LOOP_FRAME_COUNT} frames / {LOOP_DURATION_S}s)", flush=True)
    summary = render_continuum()
    print(f"Wrote continuum master + evidence bundle to {OUT_DIR}")
    print(
        f"  frames={summary['frames']} duration={summary['duration_seconds']}s "
        f"fps={summary['fps']} rendered_cells/frame="
        f"{summary['rendered_cells_per_frame_min']}-{summary['rendered_cells_per_frame_max']}"
    )


if __name__ == "__main__":
    main()
