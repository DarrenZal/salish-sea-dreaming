"""
Upgrade /project1/ssd_morph_mudra_scrubber to v003 low-latency scrubbing.

This keeps the v002 pinch-scrub interface but swaps the visual source from
H.264 MP4 to an intra-frame ProRes proxy MOV. Random-access scrubbing in TD is
much smoother with all-intra media.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
PRORES_MOV = f"{ROOT}/td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_prores_proxy_v003.mov"
V003_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v003_low_latency.tox"
PROGRESS_EXPR = (
    "op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress')[0] "
    "if op('/project1/ssd_morph_mudra_scrubber/morph_control') "
    "and op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress') "
    "else 0"
)


def _set_par(op_obj, par_name, value):
    par_obj = getattr(op_obj.par, par_name, None)
    if par_obj is not None:
        par_obj.val = value
        return True
    return False


def upgrade():
    if not os.path.exists(PRORES_MOV):
        raise RuntimeError(f"Missing low-latency ProRes asset: {PRORES_MOV}")

    comp = op(COMP_PATH)
    if comp is None:
        raise RuntimeError(f"{COMP_PATH} not found")

    movie = comp.op("morph_movie")
    ctrl = comp.op("morph_control")
    if movie is None or ctrl is None:
        raise RuntimeError("Expected morph_movie and morph_control from v002")

    _set_par(movie, "file", PRORES_MOV)
    _set_par(movie, "reloadpulse", True)
    _set_par(movie, "playmode", "specify")
    _set_par(movie, "play", False)
    _set_par(movie, "indexunit", "fraction")
    movie.par.index.expr = PROGRESS_EXPR
    _set_par(movie, "interp", True)
    _set_par(movie, "prereadframes", 12)
    _set_par(movie, "alwaysloadinitial", True)
    _set_par(movie, "highperfread", True)
    _set_par(movie, "highperfreadfactor", 2)

    # Faster progress convergence; v002's 0.18 was intentionally gentle but
    # felt laggy when driven by a live hand.
    if hasattr(ctrl.par, "const5value"):
        ctrl.par.const5value.val = 0.32
    if hasattr(ctrl.par, "const0value"):
        ctrl.par.const0value.val = 0.0
    if hasattr(ctrl.par, "const2value"):
        ctrl.par.const2value.val = 0.0
    if hasattr(ctrl.par, "const4value"):
        ctrl.par.const4value.val = 0.0
    if hasattr(ctrl.par, "const10value"):
        ctrl.par.const10value.val = 0.0

    notes = comp.op("README")
    if notes is not None:
        notes.text = (
            "SSD Morph Mudra Scrubber v003 low latency\n\n"
            "Output TOP: out_morph\n"
            "Clean movie TOP: out_clean_movie\n"
            "Control CHOP: morph_control\n\n"
            "Default mode is pinch-scrub: pinch thumb/index and move the hand "
            "left-right to guide progress between the two artworks. Release "
            "to hold the current morph point.\n\n"
            "v003 uses an intra-frame ProRes proxy MOV for smoother random "
            "scrubbing than the H.264 review MP4.\n\n"
            "Manual test: set manual_active=1, then set manual to 0..1. "
            "Set manual_active back to 0 for MediaPipe control.\n\n"
            "Internal experiment only. Austin per-output approval is required "
            "before public display.\n"
        )

    comp.store("ssd_template_role", "morph_mudra_scrubber_v003_low_latency")
    comp.store("ssd_low_latency_movie", PRORES_MOV)
    comp.save(V003_TOX)
    return {
        "component": comp.path,
        "movie": PRORES_MOV,
        "speed": ctrl.par.const5value.eval() if hasattr(ctrl.par, "const5value") else None,
        "template_tox": V003_TOX,
    }


result = upgrade()
print(json.dumps(result, indent=2))
