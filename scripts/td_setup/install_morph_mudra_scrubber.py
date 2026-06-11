"""
Install a reusable SSD morph/mudra scrubber component in TouchDesigner.

Run inside TouchDesigner Textport or through the TD MCP bridge after opening a
fresh project/checkpoint. The script creates:

  /project1/ssd_morph_mudra_scrubber

The component reads a morph MP4 with Movie File In TOP in "Specify Index" mode.
It also creates a Constant CHOP whose progress channel can be driven manually,
or by a per-frame Execute DAT that parses /project1/MediaPipe/hands for a
thumb/index pinch.

This script is deliberately conservative: it sets known parameters directly and
does not introspect TD parameter objects. That avoids the TD 2025.32050 crash
path observed on 2026-05-17 while probing par.menuNames over MCP.
"""

import json
import os


PROJECT = "/project1"
COMP_NAME = "ssd_morph_mudra_scrubber"
PROGRESS_EXPR = (
    "op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress')[0] "
    "if op('/project1/ssd_morph_mudra_scrubber/morph_control') "
    "and op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress') "
    "else 0"
)

DEFAULT_MOVIE = (
    "/Users/darrenzal/projects/salish-sea-dreaming/"
    "track2-deterministic/morph_outputs_INTERNAL/"
    "cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v008_eye_carrier_overlay.mp4"
)

FALLBACK_MOVIE = (
    "/Users/darrenzal/projects/salish-sea-dreaming/"
    "track2-deterministic/morph_outputs_INTERNAL/"
    "cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v007_smooth_final_settle.mp4"
)

TEMPLATE_TOX = (
    "/Users/darrenzal/projects/salish-sea-dreaming/"
    "td/templates/ssd_morph_mudra_scrubber_template_v001.tox"
)


def _td_class(name):
    return getattr(td, name)


def _set_par(op_obj, par_name, value):
    par_obj = getattr(op_obj.par, par_name, None)
    if par_obj is not None:
        par_obj.val = value
        return True
    return False


def _set_const_channel(chop, index, name, value):
    _set_par(chop, f"const{index}name", name)
    _set_par(chop, f"const{index}value", value)


def _destroy_existing(path):
    existing = op(path)
    if existing is not None:
        existing.destroy()


def _choose_movie():
    if os.path.exists(DEFAULT_MOVIE):
        return DEFAULT_MOVIE
    return FALLBACK_MOVIE


def install():
    project_root = op(PROJECT)
    if project_root is None:
        raise RuntimeError(f"{PROJECT} not found")

    comp_path = f"{PROJECT}/{COMP_NAME}"
    _destroy_existing(comp_path)

    comp = project_root.create(_td_class("baseCOMP"), COMP_NAME)
    comp.nodeX = 1200
    comp.nodeY = 200

    ctrl = comp.create(_td_class("constantCHOP"), "morph_control")
    ctrl.nodeX = -450
    ctrl.nodeY = 200
    _set_par(ctrl, "const", 6)
    _set_const_channel(ctrl, 0, "progress", 0.0)
    _set_const_channel(ctrl, 1, "pinch", 0.0)
    _set_const_channel(ctrl, 2, "target", 0.0)
    _set_const_channel(ctrl, 3, "engaged", 0.0)
    _set_const_channel(ctrl, 4, "manual", 0.0)
    _set_const_channel(ctrl, 5, "speed", 0.12)

    movie = comp.create(_td_class("moviefileinTOP"), "morph_movie")
    movie.nodeX = -20
    movie.nodeY = 200
    _set_par(movie, "file", _choose_movie())
    _set_par(movie, "playmode", "specify")
    _set_par(movie, "play", False)
    _set_par(movie, "indexunit", "fraction")
    movie.par.index.expr = PROGRESS_EXPR
    _set_par(movie, "interp", True)

    out_top = comp.create(_td_class("nullTOP"), "out_morph")
    out_top.nodeX = 260
    out_top.nodeY = 200
    movie.outputConnectors[0].connect(out_top.inputConnectors[0])

    cook = comp.create(_td_class("executeDAT"), "mudra_to_progress")
    cook.nodeX = -450
    cook.nodeY = -40
    _set_par(cook, "framestart", True)
    _set_par(cook, "active", True)
    cook.text = r'''import json

HANDS_PATH = "/project1/MediaPipe/hands"
CONTROL_PATH = "/project1/ssd_morph_mudra_scrubber/morph_control"
PINCH_THRESHOLD = 0.055
SMOOTH_UP = 0.145
SMOOTH_DOWN = 0.08

def _set_const(index, value):
    ctrl = op(CONTROL_PATH)
    if ctrl is not None:
        getattr(ctrl.par, f"const{index}value").val = value

def _pinch_value():
    hands = op(HANDS_PATH)
    if hands is None or not hands.text:
        return 0.0
    try:
        data = json.loads(hands.text)
        all_lm = data.get("gestureResults", {}).get("landmarks", [])
        if not all_lm or len(all_lm[0]) <= 8:
            return 0.0
        lm = all_lm[0]
        thumb = lm[4]
        index = lm[8]
        dx = thumb["x"] - index["x"]
        dy = thumb["y"] - index["y"]
        dz = thumb.get("z", 0.0) - index.get("z", 0.0)
        dist = (dx * dx + dy * dy + dz * dz) ** 0.5
        raw = max(0.0, min(1.0, 1.0 - (dist / PINCH_THRESHOLD)))
        return raw * raw
    except Exception:
        return 0.0

def onStart(): pass
def onCreate(): pass
def onExit(): pass
def onFrameStart(frame):
    ctrl = op(CONTROL_PATH)
    if ctrl is None:
        return
    progress = float(ctrl["progress"][0])
    manual = float(ctrl["manual"][0])
    speed = max(0.001, float(ctrl["speed"][0]))
    pinch = _pinch_value()
    target = 1.0 if pinch > 0.35 else manual
    smooth = SMOOTH_UP if target > progress else SMOOTH_DOWN
    next_progress = progress + (target - progress) * max(speed, smooth)
    next_progress = max(0.0, min(1.0, next_progress))
    _set_const(0, next_progress)
    _set_const(1, pinch)
    _set_const(2, target)
    _set_const(3, 1.0 if pinch > 0.35 else 0.0)
'''

    notes = comp.create(_td_class("textDAT"), "README")
    notes.nodeX = -450
    notes.nodeY = -250
    notes.text = (
        "SSD Morph Mudra Scrubber v001\n"
        "\n"
        "Output TOP: out_morph\n"
        "Control CHOP: morph_control\n"
        "Movie: morph_movie\n"
        "\n"
        "Manual test: set morph_control manual to 0..1 or progress to 0..1.\n"
        "Mudra test: /project1/MediaPipe/hands must exist; thumb/index pinch "
        "pulls progress toward 1.\n"
        "\n"
        "Internal experiment only. Austin per-output approval is required before "
        "public display.\n"
    )

    comp.store("ssd_template_role", "morph_mudra_scrubber")
    comp.store("ssd_default_movie", _choose_movie())

    os.makedirs(os.path.dirname(TEMPLATE_TOX), exist_ok=True)
    comp.save(TEMPLATE_TOX)
    return {
        "component": comp.path,
        "output_top": out_top.path,
        "control_chop": ctrl.path,
        "movie": _choose_movie(),
        "template_tox": TEMPLATE_TOX,
    }


result = install()
print(json.dumps(result, indent=2))
