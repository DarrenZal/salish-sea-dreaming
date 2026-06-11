#!/usr/bin/env python3.11
"""Salmon Trajectory Grammar v001 - proof packet renderer.

Places past-trail / present-anchor / future-intention primitive marks in the
water AROUND moving salmon (and around flow paths), never on the fish bodies.
The fish body is never drawn; only the wake it leaves, an offset attention
anchor, and a faint intention ahead of it.

Reuses the v005 nearest-neighbour tracker unchanged (detect_salmon_candidates +
track_update). No YOLO / ByteTrack / CoTracker. No SD, no LoRA, no fish glyphs,
no body-centre circles, no eyes.

Outputs (layer-only, pure black, H.264):
  track2-deterministic/morph_outputs_INTERNAL/
    salmon_trajectory_grammar_v001_2026-05-19/

Design source: docs/space-center/salmon-trajectory-grammar-design-2026-05-19.md
INTERNAL ONLY until Austin reviews. Not Austin-approved.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from primitive_water_grammar_v1 import (
    H,
    H1_SALMON,
    H6_KELP,
    H264Writer,
    N_FRAMES,
    ROOT,
    SampledVideo,
    W,
    calc_flow,
    sample_flow,
    smooth_angle,
)
from primitive_water_grammar_v5 import (
    detect_salmon_candidates,
    draw_circle,
    draw_crescent,
    draw_trigon,
    ffprobe,
    track_update,
)

OUT_DIR = ROOT / "track2-deterministic/morph_outputs_INTERNAL/salmon_trajectory_grammar_v001_2026-05-19"
MIDPOINT_DIR = OUT_DIR / "midpoint_stills"
DATA_DIR = OUT_DIR / "trajectory_data"
FPS = 24

# Bundle tuning. Marks stay sparse and soft so the layer reads as water
# response to motion, not as figure decoration.
MAX_BUNDLES = 5
SALMON_BUNDLE_ALPHA = 0.52
CONTROL_BUNDLE_ALPHA = 0.42
# Trail spacing as a fraction of fish length. Set so consecutive wake
# crescents are spaced ~1.5x their own along-path footprint: close enough to
# read as a connected dissipating wake, far enough never to fuse into a body.
SALMON_TRAIL_SPACING = 0.50
CONTROL_TRAIL_SPACING = 0.60
TRAIL_COUNT = 4

# Per-mark opacity multipliers (relative to the bundle alpha).
TRAIL_NEW_MUL = 0.62
TRAIL_OLD_MUL = 0.22
ANCHOR_MUL = 0.56
FUTURE_CRESCENT_MUL = 0.33
FUTURE_TRIGON_MUL = 0.25


@dataclass(frozen=True)
class ClipMeta:
    filename: str
    source: str
    test: str
    method: str
    layer_role: str
    runtime_note: str = ""


def sample_trail_by_arclength(
    history: list[dict[str, float]], spacing: float, count: int
) -> list[tuple[tuple[float, float], float]]:
    """Walk backward along the observed path, emitting a sample every `spacing`
    pixels of travelled distance.

    Sampling by arc length (not by frame count) means a slow or stationary fish
    produces a short trail or none at all - which is correct, a still fish has
    no wake - while a fast fish produces an evenly spaced trail. It also keeps
    adjacent crescents far enough apart that they never merge into a body-like
    silhouette. Returns newest-first.
    """
    if len(history) < 2:
        return []
    pts = [(h["x"], h["y"]) for h in history]
    samples: list[tuple[tuple[float, float], float]] = []
    target = spacing
    travelled = 0.0
    i = len(pts) - 1
    while i > 0 and len(samples) < count:
        x1, y1 = pts[i]
        x0, y0 = pts[i - 1]
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg < 1e-6:
            i -= 1
            continue
        while travelled + seg >= target and len(samples) < count:
            frac = (target - travelled) / seg
            sx = x1 + (x0 - x1) * frac
            sy = y1 + (y0 - y1) * frac
            # Tangent points older -> newer, i.e. along the path toward the
            # fish's present position.
            tangent = math.atan2(y1 - y0, x1 - x0)
            samples.append(((sx, sy), tangent))
            target += spacing
        travelled += seg
        i -= 1
    return samples


def upward_perp(heading: float) -> float:
    """Perpendicular to `heading` whose screen-y component points up.

    Used to offset the present anchor off the fish body. Keeping the offset on
    the dorsal/up side means the circle never lands on the body centre or the
    eye position regardless of swim direction.
    """
    a = heading + math.pi / 2.0
    if math.sin(a) > 0.0:  # sin > 0 means pointing down in image coordinates
        a -= math.pi
    return a


def render_trajectory_bundle(
    frame: np.ndarray,
    *,
    present: tuple[float, float],
    heading: float,
    length: float,
    history: list[dict[str, float]],
    alpha: float,
    draw_anchor: bool,
    future_enabled: bool,
    trail_spacing_mul: float,
) -> None:
    """Render one mover's past trail, present anchor, and future intention.

    The fish body is intentionally never drawn here.
    """
    # --- Past trail: fading crescents along the observed wake ---
    samples = sample_trail_by_arclength(history, length * trail_spacing_mul, TRAIL_COUNT)
    denom = max(1, TRAIL_COUNT - 1)
    for idx, (pos, tangent) in enumerate(samples):
        age = idx / denom  # 0 newest .. 1 oldest
        mul = TRAIL_NEW_MUL + (TRAIL_OLD_MUL - TRAIL_NEW_MUL) * age
        size = length * (0.30 - 0.12 * age)
        a = alpha * mul
        if a < 0.025:
            continue
        draw_crescent(frame, pos, size, tangent, alpha=a)

    # --- Present anchor: small circle offset OFF the body ---
    if draw_anchor:
        perp = upward_perp(heading)
        offset = length * 0.46
        apos = (present[0] + math.cos(perp) * offset, present[1] + math.sin(perp) * offset)
        draw_circle(frame, apos, length * 0.072, alpha=alpha * ANCHOR_MUL)

    # --- Future intention: faint crescent + trigon ahead of the nose ---
    if future_enabled:
        head = (
            present[0] + math.cos(heading) * length * 0.5,
            present[1] + math.sin(heading) * length * 0.5,
        )
        f1 = (head[0] + math.cos(heading) * length * 0.42, head[1] + math.sin(heading) * length * 0.42)
        f2 = (head[0] + math.cos(heading) * length * 0.95, head[1] + math.sin(heading) * length * 0.95)
        draw_crescent(frame, f1, length * 0.24, heading, alpha=alpha * FUTURE_CRESCENT_MUL)
        draw_trigon(frame, f2, length * 0.30, heading, alpha=alpha * FUTURE_TRIGON_MUL)


def render_salmon_clips() -> tuple[list[ClipMeta], list[list]]:
    """Single detection pass over H1, two outputs: full bundle and no-anchor."""
    full_out = OUT_DIR / "01_salmon_trajectory_H1_full_v001_black_screen.mp4"
    noanchor_out = OUT_DIR / "02_salmon_trajectory_H1_no_anchor_v001_black_screen.mp4"
    reader = SampledVideo(H1_SALMON, start_seconds=8.0)
    w_full = H264Writer(full_out)
    w_noanchor = H264Writer(noanchor_out)
    prev_raw = reader.frame(0)
    tracks: list[dict[str, float]] = []
    next_id = 1
    histories: dict[int, list[dict[str, float]]] = {}
    active_counts: list[int] = []
    data_rows: list[list] = []

    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        detections = detect_salmon_candidates(raw, flow)
        tracks, next_id = track_update(tracks, detections, next_id, fi)

        # Extend the observed-path history only on fresh observations, so an
        # occluded (missing) track's frozen position does not pad the wake.
        for tr in tracks:
            if tr["missing"] == 0:
                histories.setdefault(int(tr["id"]), []).append(
                    {"frame": float(fi), "x": tr["x"], "y": tr["y"], "angle": tr["angle"]}
                )

        frame_full = np.zeros((H, W, 3), np.uint8)
        frame_noanchor = np.zeros((H, W, 3), np.uint8)
        renderable = sorted(tracks, key=lambda tr: -tr["age"])[:MAX_BUNDLES]
        active = 0
        for tr in renderable:
            fade_in = min(1.0, tr["age"] / 10.0)
            fade_out = max(0.0, 1.0 - tr["missing"] / 12.0)
            alpha = SALMON_BUNDLE_ALPHA * fade_in * fade_out
            if alpha < 0.03:
                continue
            active += 1
            hist = histories.get(int(tr["id"]), [])
            future_on = tr["age"] > 6  # wait for the heading to stabilise
            # Anchor only once the track is established, so a brief blip never
            # leaves a lone floating circle.
            anchor_on = tr["age"] > 4
            for frame, draw_anchor in ((frame_full, anchor_on), (frame_noanchor, False)):
                render_trajectory_bundle(
                    frame,
                    present=(tr["x"], tr["y"]),
                    heading=tr["angle"],
                    length=tr["length"],
                    history=hist,
                    alpha=alpha,
                    draw_anchor=draw_anchor,
                    future_enabled=future_on,
                    trail_spacing_mul=SALMON_TRAIL_SPACING,
                )
            data_rows.append(
                [
                    "salmon_H1",
                    fi,
                    int(tr["id"]),
                    round(tr["x"], 1),
                    round(tr["y"], 1),
                    round(tr["angle"], 4),
                    round(tr["length"], 1),
                    int(tr["age"]),
                    int(tr["missing"]),
                    len(hist),
                ]
            )
        active_counts.append(active)
        w_full.write(frame_full)
        w_noanchor.write(frame_noanchor)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            recent = active_counts[-48:]
            print(
                f"  salmon trajectory {fi + 1}/{N_FRAMES} "
                f"avg active bundles={sum(recent) / len(recent):.1f}",
                flush=True,
            )

    w_full.close()
    w_noanchor.close()
    reader.close()
    avg = sum(active_counts) / max(1, len(active_counts))
    total_tracks = len({r[2] for r in data_rows})
    note = (
        f"Average active trajectory bundles per frame: {avg:.1f}; "
        f"distinct tracks over the clip: {total_tracks}."
    )
    metas = [
        ClipMeta(
            filename=full_out.name,
            source=str(H1_SALMON.relative_to(ROOT)),
            test=(
                "Full trajectory grammar over H1 salmon: fading-crescent past trail, "
                "offset present anchor, faint future-intention crescent and trigon."
            ),
            method=(
                "v005 nearest-neighbour tracker (unchanged) supplies positions and "
                "headings; arc-length trail sampling, perpendicular off-body anchor "
                "offset, heading-projected future marks."
            ),
            layer_role=(
                "Salmon trajectory water layer. Screen/Additive over salmon footage "
                "or wide-wall fallback. Sits below the v005 water layers."
            ),
            runtime_note=note,
        ),
        ClipMeta(
            filename=noanchor_out.name,
            source=str(H1_SALMON.relative_to(ROOT)),
            test=(
                "Anchor-omitted variant: past trail plus future intention only, no "
                "circle anywhere. The safe variant if body-centre or near-body "
                "circles are rejected."
            ),
            method="Identical tracking to clip 01; the present-anchor circle is not drawn.",
            layer_role=(
                "Salmon trajectory water layer, conservative variant. Use if Austin "
                "rejects any circle near the fish."
            ),
            runtime_note=note,
        ),
    ]
    return metas, data_rows


def render_kelp_control() -> tuple[ClipMeta, list[list]]:
    """Fish-free control: flow-advected anchors driven by the SAME renderer.

    No detection, no fish. Proves the trajectory grammar reads as water/current
    motion when there is no fish present to be confused with.
    """
    out = OUT_DIR / "03_kelp_flowpath_control_H6_v001_black_screen.mp4"
    reader = SampledVideo(H6_KELP, start_seconds=8.0)
    writer = H264Writer(out)
    seeds = [
        (0.18, 0.30),
        (0.44, 0.26),
        (0.74, 0.34),
        (0.28, 0.62),
        (0.58, 0.70),
        (0.82, 0.58),
    ]
    anchors = [
        {
            "id": idx,
            "x": W * sx,
            "y": H * sy,
            "angle": -0.30 + idx * 0.13,  # spread of current directions
            "length": 176.0,
        }
        for idx, (sx, sy) in enumerate(seeds)
    ]
    histories: dict[int, list[dict[str, float]]] = {a["id"]: [] for a in anchors}
    prev_raw = reader.frame(0)
    data_rows: list[list] = []

    for fi in range(N_FRAMES):
        raw = reader.frame(fi)
        flow = calc_flow(prev_raw, raw) if fi > 0 else None
        frame = np.zeros((H, W, 3), np.uint8)
        for a in anchors:
            if flow is not None:
                dx, dy = sample_flow(flow, a["x"], a["y"])
                if math.hypot(dx, dy) > 0.20:
                    a["angle"] = smooth_angle(a["angle"], math.atan2(dy, dx), amount=0.18)
                # Steady glide along heading plus a flow component, so the
                # control shows real travelled current paths within 6 seconds.
                # Flow coefficient kept modest so paths stay distinct rather
                # than herding into one clump.
                a["x"] += math.cos(a["angle"]) * 1.65 + dx * 0.6
                a["y"] += math.sin(a["angle"]) * 1.65 + dy * 0.6
            wrapped = False
            if a["x"] < -130 or a["x"] > W + 130 or a["y"] < 70 or a["y"] > H - 70:
                a["x"] = min(max(a["x"], 90.0), W - 90.0)
                a["y"] = min(max(a["y"], 120.0), H - 120.0)
                wrapped = True
            if wrapped:
                histories[a["id"]].clear()  # do not streak the wake across a clamp
            histories[a["id"]].append(
                {"frame": float(fi), "x": a["x"], "y": a["y"], "angle": a["angle"]}
            )
            alpha = CONTROL_BUNDLE_ALPHA * min(1.0, fi / 14.0)
            if alpha >= 0.03:
                render_trajectory_bundle(
                    frame,
                    present=(a["x"], a["y"]),
                    heading=a["angle"],
                    length=a["length"],
                    history=histories[a["id"]],
                    alpha=alpha,
                    draw_anchor=True,
                    future_enabled=fi > 8,
                    trail_spacing_mul=CONTROL_TRAIL_SPACING,
                )
            data_rows.append(
                [
                    "kelp_H6",
                    fi,
                    a["id"],
                    round(a["x"], 1),
                    round(a["y"], 1),
                    round(a["angle"], 4),
                    round(a["length"], 1),
                    fi,
                    0,
                    len(histories[a["id"]]),
                ]
            )
        writer.write(frame)
        prev_raw = raw
        if (fi + 1) % 48 == 0:
            print(f"  kelp flowpath control {fi + 1}/{N_FRAMES}", flush=True)

    writer.close()
    reader.close()
    meta = ClipMeta(
        filename=out.name,
        source=str(H6_KELP.relative_to(ROOT)),
        test=(
            "Fish-free control: the same renderer driven by flow-advected anchors "
            "on H6 kelp footage. No detection, no fish."
        ),
        method=(
            f"{len(anchors)} seed anchors advected by Farneback optical flow; each "
            "carries a position history and is rendered with the identical trajectory bundle."
        ),
        layer_role=(
            "Control / current layer. Demonstrates the grammar reads as water "
            "motion with no salmon present; the anchor here is a current knot."
        ),
        runtime_note=f"{len(anchors)} flow-advected current paths; deterministic seeds, no RNG.",
    )
    return meta, data_rows


def write_data_csv(rows: list[list]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "tracks_per_frame.csv"
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "source",
                "frame",
                "track_id",
                "x",
                "y",
                "heading_rad",
                "length_px",
                "age",
                "missing",
                "history_len",
            ]
        )
        writer.writerows(rows)


def nonblank_stats(path: Path) -> str:
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return "midpoint read failed"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return f"midpoint max luma {int(gray.max())}, nonblack pixels {int((gray > 2).sum())}"


def save_stills_and_contact_sheet(metas: list[ClipMeta]) -> None:
    MIDPOINT_DIR.mkdir(parents=True, exist_ok=True)
    thumbs: list[np.ndarray] = []
    for meta in metas:
        cap = cv2.VideoCapture(str(OUT_DIR / meta.filename))
        cap.set(cv2.CAP_PROP_POS_FRAMES, N_FRAMES // 2)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            continue
        cv2.imwrite(
            str(MIDPOINT_DIR / f"{Path(meta.filename).stem}_midpoint.jpg"),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 92],
        )
        thumb = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
        cv2.putText(
            thumb,
            Path(meta.filename).stem[:54],
            (12, 344),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )
        thumbs.append(thumb)
    if thumbs:
        cv2.imwrite(
            str(OUT_DIR / "contact_sheet_midpoints.jpg"),
            cv2.vconcat(thumbs),
            [cv2.IMWRITE_JPEG_QUALITY, 92],
        )


def write_readme(metas: list[ClipMeta]) -> None:
    lines = [
        "# Salmon Trajectory Grammar v001 - 2026-05-19",
        "",
        "INTERNAL ONLY until Austin reviews. Not Austin-approved. Layer-only "
        "pure-black clips; no SD, LoRA, SAM, YOLO, ByteTrack, CoTracker, named "
        "chiefs/specific people, or fish glyphs.",
        "",
        "Design source: `docs/space-center/salmon-trajectory-grammar-design-2026-05-19.md`.",
        "",
        "## What This Lane Is",
        "",
        "Primitive marks are placed in the water AROUND moving salmon, never on "
        "the fish bodies. Each tracked fish produces three bundles:",
        "",
        "- Past trail: fading crescents along the observed wake, oldest faintest.",
        "- Present anchor: one small circle offset off the body (clip 01 only).",
        "- Future intention: a faint crescent and trigon projected ahead of the nose.",
        "",
        "The fish body is never drawn. Read forward along travel the bundle is "
        "circle (now) -> crescent -> trigon (ahead); read backward it is the "
        "widening crescent wake. This is Recipe 01 pond-ripple grammar projected "
        "onto a moving point.",
        "",
        "## How This Differs From The Rejected Fish-Glyph Lane",
        "",
        "The v004/v005 articulated-fish clips built a fish figure from primitives "
        "(trigon head, crescent gill, circle body, eye, trigon tail). This lane "
        "builds none of that. Primitives mark water states, not anatomy. No "
        "body-centre circles, no eyes, no fins, no glyph silhouette.",
        "",
        "## Tracking",
        "",
        "Reuses the v005 nearest-neighbour tracker unchanged "
        "(`detect_salmon_candidates` + `track_update` from `primitive_water_grammar_v5`). "
        "Each track gains an observed-path history ring; the trail is sampled by "
        "arc length so a slow fish yields a short wake and a still fish yields "
        "none. No YOLO/ByteTrack/CoTracker in v001 - those are the documented "
        "stronger-path upgrades.",
        "",
        "## Review Order",
        "",
        "1. `01_salmon_trajectory_H1_full_v001_black_screen.mp4`",
        "2. `02_salmon_trajectory_H1_no_anchor_v001_black_screen.mp4`",
        "3. `03_kelp_flowpath_control_H6_v001_black_screen.mp4`",
        "",
        "## Resolume Notes",
        "",
        "- All clips are RGB H.264 MP4 on pure black. Use Screen/Additive blend; "
        "no alpha channel required.",
        "- Start the trajectory layer around 30-40% opacity, below the v005 water "
        "layers so the marks read as the same water sheet.",
        "- Clips 01 and 02 share identical tracking; only the present anchor differs.",
        "",
        "## Austin Questions",
        "",
        "- Does marking the water around a moving fish read as water grammar, or "
        "still as figure decoration?",
        "- Should the present anchor be a small offset circle (clip 01) or omitted "
        "entirely (clip 02)?",
        "- Do wake crescents cupping back along the path read as ripples left behind?",
        "- Does the faint future crescent/trigon read as intention, or as noise?",
        "- Should the anchor be on the body, offset off the body, or absent?",
        "",
        "## Clips",
        "",
    ]
    for meta in metas:
        probe = ffprobe(OUT_DIR / meta.filename)
        stats = nonblank_stats(OUT_DIR / meta.filename)
        lines.extend(
            [
                f"### {meta.filename}",
                "",
                f"- What it tests: {meta.test}",
                f"- Source: `{meta.source}`",
                f"- Technical method: {meta.method}",
                f"- Layer role: {meta.layer_role}",
            ]
        )
        if meta.runtime_note:
            lines.append(f"- Runtime note: {meta.runtime_note}")
        lines.extend(
            [
                f"- ffprobe: {probe['width']}x{probe['height']}, fps {probe['fps']}, "
                f"duration {float(probe['duration']):.3f}s, frames {probe['frames']}",
                f"- Nonblank check: {stats}",
                "",
            ]
        )
    lines.extend(
        [
            "## Data",
            "",
            "- `trajectory_data/tracks_per_frame.csv`: per-frame track positions, "
            "headings, length, age, missing count, and history length for both the "
            "salmon and the kelp-control passes.",
            "",
            "## Review Stills",
            "",
            "- Midpoint stills: `midpoint_stills/`",
            "- Contact sheet: `contact_sheet_midpoints.jpg`",
            "",
        ]
    )
    (OUT_DIR / "README.md").write_text("\n".join(lines))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing Salmon Trajectory Grammar v001 to {OUT_DIR}", flush=True)
    salmon_metas, salmon_rows = render_salmon_clips()
    control_meta, control_rows = render_kelp_control()
    metas = [*salmon_metas, control_meta]
    write_data_csv(salmon_rows + control_rows)
    save_stills_and_contact_sheet(metas)
    write_readme(metas)
    print("Done. README includes ffprobe metadata and nonblank checks.", flush=True)


if __name__ == "__main__":
    main()
