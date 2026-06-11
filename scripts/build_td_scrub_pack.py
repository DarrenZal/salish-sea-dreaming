#!/usr/bin/env python3
"""
Build/refresh TD frame-sequence scrubber asset packs.

Per overnight #1: produce or refresh scrubber packs for next-best clips
that can be wired into the v006-style Movie File In TOP scrubber pattern
(progress=0 → frame_0001, progress=1 → frame_LAST). Converts source
frames to JPG (TD-friendly), numbers from 1, writes README per pack.

Targets:
  1. cosmic_sun_to_salmon_spawn v007 landmark-routing — NEW pack
  2. cosmic_sun_to_salmon_spawn v006 — add missing README
  3. raven_sun_to_cosmic_sun v001 — verify (already has README)
  4. primitive_cycle v001 — verify (already has README)
  5. primitive_field v001 — verify (already has README)
"""
from pathlib import Path
from PIL import Image
import subprocess

ROOT = Path(__file__).resolve().parent.parent
INTERNAL = ROOT / "track2-deterministic/morph_outputs_INTERNAL"
MORPH_OUTPUTS = ROOT / "track2-deterministic/morph_outputs"
TD_ASSETS = ROOT / "td/templates/assets"


def build_pack(name: str, source_frame_dir: Path, source_clip_label: str,
               fps: int, description: str, jpg_quality: int = 92):
    """Convert source_frame_dir PNGs → numbered JPGs in TD assets/<name>/."""
    dst = TD_ASSETS / name
    dst.mkdir(parents=True, exist_ok=True)

    src_frames = sorted([p for p in source_frame_dir.glob("frame_*.png")])
    if not src_frames:
        # Maybe already JPGs
        src_frames = sorted([p for p in source_frame_dir.glob("frame_*.jpg")])
    if not src_frames:
        print(f"  SKIP {name}: no frames in {source_frame_dir}")
        return None

    print(f"Building {name} ({len(src_frames)} frames from {source_frame_dir.name})...")
    # Number from 1 for TD Movie File In TOP convention
    for i, src in enumerate(src_frames, start=1):
        dst_path = dst / f"frame_{i:04d}.jpg"
        if dst_path.exists():
            continue  # already converted
        img = Image.open(src).convert("RGB")
        img.save(dst_path, "JPEG", quality=jpg_quality)

    n_total = len(src_frames)
    duration_sec = n_total / fps
    readme_text = f"""# TD scrubber asset pack — {name}

## Source

- Source clip: {source_clip_label}
- Frame count: {n_total}
- FPS: {fps}
- Duration: {duration_sec:.2f} sec

## Description

{description}

## TD wiring (v006-style frame sequence scrubber)

This pack is structured for the Movie File In TOP frame-sequence approach
that fixed the index-seeking bug in v006:

1. Drop a **Movie File In TOP** into your project
2. Set `File` to the first frame: `td/templates/assets/{name}/frame_0001.jpg`
3. Set `Play Mode` to **Locked to Timeline** OR **Specify Index**
4. Wire a control CHOP (slider, hand-tracker, etc.) into the `Index` parameter
5. Map control value `0..1` to frame index `0..{n_total - 1}`:
   `index = int(control_value * {n_total - 1})`

OR use the reusable scrubber TOX pattern from
`td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox`
(re-point its frame-sequence path to this pack's folder).

## Verification

- `progress = 0` → first frame: `frame_0001.jpg`
- `progress = 1` → last frame: `frame_{n_total:04d}.jpg`
- Output pixels MUST differ between first/last frames (the v005 bug was
  static output regardless of index).

## Status

INTERNAL. Austin per-output OK required before any audience-facing use.
"""
    (dst / "README.md").write_text(readme_text)
    print(f"  → {dst} ({n_total} JPG frames + README)")
    return dst


def main():
    TD_ASSETS.mkdir(parents=True, exist_ok=True)

    # 1. Cosmic→Salmon v007 — NEW pack
    v007_src = INTERNAL / "cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007"
    if v007_src.exists():
        build_pack(
            name="cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001",
            source_frame_dir=v007_src,
            source_clip_label="cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4",
            fps=24,
            description=(
                "Cosmic Sun → Salmon Spawn morph using v007 landmark-atom-routing "
                "(Codex worker built). Uses Lane 2E routing rule: atoms routed by "
                "semantic role + spatial position rather than whole-piece path "
                "resampling. Smoother endpoint settle than v006. Better choice than "
                "v006 for cross-piece morph scrubber."
            ),
        )
    else:
        print(f"v007 source dir missing: {v007_src}")

    # 2. Cosmic→Salmon v006 — Add README to existing pack
    v006_pack = TD_ASSETS / "cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006"
    if v006_pack.exists() and not (v006_pack / "README.md").exists():
        n_frames = len(list(v006_pack.glob("frame_*.jpg")))
        readme_text = f"""# TD scrubber asset pack — cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006

## Source

- Source clip: cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4
- Frame count: {n_frames}
- FPS: 24
- Duration: {n_frames / 24:.2f} sec

## Description

Cosmic Sun → Salmon Spawn morph, v006 endpoint-correct variant. Removes
the destination Salmon full-canvas background rect that previously
appeared as an expanding square artifact. Endpoint-assisted: final frame
corrected against verified Salmon JPG. Older sibling of v007
landmark-routing pack — both available for scrubber use.

## TD wiring (v006-style frame sequence scrubber)

1. Drop a **Movie File In TOP** into your project
2. Set `File` to first frame: `td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/frame_0001.jpg`
3. Set `Play Mode` to **Specify Index**
4. Map control value `0..1` to frame index `0..{n_frames - 1}`

OR use TOX: `td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox`
which is already wired to this pack.

## Verification

- `progress = 0` → `frame_0001.jpg`
- `progress = 1` → `frame_{n_frames:04d}.jpg`

## Status

INTERNAL. Superseded for new builds by v007 landmark-routing pack but
retained as control for comparison.
"""
        (v006_pack / "README.md").write_text(readme_text)
        print(f"  → Added README to {v006_pack}")

    # 3. raven_sun_to_cosmic — verify existing
    rc_pack = TD_ASSETS / "raven_sun_to_cosmic_sun_scrub_frames_v001"
    if rc_pack.exists():
        readme = rc_pack / "README.md"
        if readme.exists():
            print(f"  ✓ raven_sun_to_cosmic_sun_scrub_frames_v001 README exists")
        else:
            print(f"  WARN raven pack missing README — would build but skipping (not source-mapped here)")

    # 4. primitive_cycle — verify
    pc_pack = TD_ASSETS / "primitive_cycle_scrub_frames_v001"
    if pc_pack.exists() and (pc_pack / "README.md").exists():
        print(f"  ✓ primitive_cycle_scrub_frames_v001 README exists")

    # 5. primitive_field — verify
    pf_pack = TD_ASSETS / "primitive_field_scrub_frames_v001"
    if pf_pack.exists() and (pf_pack / "README.md").exists():
        print(f"  ✓ primitive_field_scrub_frames_v001 README exists")

    # Inventory
    print("\n==== Final TD assets inventory ====")
    for d in sorted(TD_ASSETS.iterdir()):
        if d.is_dir():
            n = len(list(d.glob("frame_*.jpg")))
            r = "README ✓" if (d / "README.md").exists() else "no README"
            print(f"  {d.name}: {n} JPG frames, {r}")


if __name__ == "__main__":
    main()
