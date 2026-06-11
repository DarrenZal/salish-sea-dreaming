#!/usr/bin/env python3
"""
Composite previews of the v002b water-flow layers over Moonfish footage.
Same blend recipe v002 used (additive at ~55% opacity, footage slightly
dimmed). Layered over P1099653 (open-water salmon school) for visual
parity across all four scenes — Pravin can swap footage in Resolume.

Output: composite MP4s alongside the layer files in:
    track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v002b_2026-05-22/

INTERNAL ONLY. Composite previews are review aids; production-time the
black-screen layer goes directly into Resolume over footage.
"""
import sys
import time
from pathlib import Path

_here = Path(__file__).parent
sys.path.insert(0, str(_here))
import water_flow_phrase_grammar_v002 as v002


SCENES = [
    "current_streamline_field_v002",
    "waterfall_vertical_phrase_v002",
    "transpiration_vertical_phrase_v002",
    "transpiration_vertical_phrase_v002_crescentup",
]

FOOTAGE = Path("/Users/darrenzal/projects/salish-sea-dreaming/media/"
               "collaborators/moonfish-video/underwater/P1099653.mp4")
START_S = 4.0           # offset into the source footage
OPACITY = 0.55          # additive layer opacity (v002 default)
FOOTAGE_DIM = -0.10     # slight dim so layer reads on top
LAYER_DIR = Path("/Users/darrenzal/projects/salish-sea-dreaming/"
                 "track2-deterministic/morph_outputs_INTERNAL/"
                 "water_flow_phrase_grammar_v002b_2026-05-22")


def main():
    assert FOOTAGE.is_file(), f"footage missing: {FOOTAGE}"
    print(f"== v002b composite previews ==")
    print(f"  footage:  {FOOTAGE.name}")
    print(f"  opacity:  {OPACITY}")
    print(f"  outdir:   {LAYER_DIR}")
    t0 = time.time()

    for scene in SCENES:
        layer_mp4 = LAYER_DIR / f"{scene}.mp4"
        if not layer_mp4.is_file():
            print(f"  SKIP {scene}: layer MP4 missing")
            continue
        out_mp4 = LAYER_DIR / f"{scene}__over_moonfish-water.mp4"
        v002.make_composite(
            layer_mp4=layer_mp4,
            footage=FOOTAGE,
            start=START_S,
            opacity=OPACITY,
            footage_dim=FOOTAGE_DIM,
            out_mp4=out_mp4,
            n_frames=v002.N_FRAMES,
        )

    print(f"\ntotal: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
