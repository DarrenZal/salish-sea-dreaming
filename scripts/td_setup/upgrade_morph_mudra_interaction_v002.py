"""
Upgrade /project1/ssd_morph_mudra_scrubber to v002.

Adds:
- continuous pinch-scrub control: pinch thumb/index, move hand left/right
- manual override channels for testing
- a transparent two-node slider overlay over the morph output
- v002 .tox save for reuse

Run inside TouchDesigner after install_morph_mudra_scrubber.py.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
V002_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v002.tox"
PROGRESS_EXPR = (
    "op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress')[0] "
    "if op('/project1/ssd_morph_mudra_scrubber/morph_control') "
    "and op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress') "
    "else 0"
)


CHANNELS = [
    ("progress", 0.0),
    ("pinch", 0.0),
    ("target", 0.0),
    ("engaged", 0.0),
    ("manual", 0.0),
    ("speed", 0.18),
    ("guide_x", 0.5),
    ("guide_y", 0.5),
    ("pinch_distance", 1.0),
    ("mode", 1.0),          # 0 = trigger, 1 = pinch-scrub
    ("manual_active", 0.0),
    ("hold_release", 1.0),
    ("invert_x", 0.0),
]


def _td_class(name):
    return getattr(td, name)


def _set_par(op_obj, par_name, value):
    par_obj = getattr(op_obj.par, par_name, None)
    if par_obj is not None:
        par_obj.val = value
        return True
    return False


def _ensure(parent, op_type, name):
    existing = parent.op(name)
    if existing is not None:
        return existing
    return parent.create(_td_class(op_type), name)


def _set_const_channel(chop, index, name, value):
    _set_par(chop, f"const{index}name", name)
    par = getattr(chop.par, f"const{index}value", None)
    if par is not None:
        # Preserve live progress/manual values if they already exist.
        if name in ("progress", "manual"):
            try:
                old = chop[name][0]
                par.val = float(old)
                return
            except Exception:
                pass
        par.val = value


def upgrade():
    comp = op(COMP_PATH)
    if comp is None:
        raise RuntimeError(f"{COMP_PATH} not found")

    ctrl = comp.op("morph_control")
    if ctrl is None:
        ctrl = comp.create(_td_class("constantCHOP"), "morph_control")
    ctrl.nodeX = -650
    ctrl.nodeY = 230
    _set_par(ctrl, "const", len(CHANNELS))
    for i, (name, value) in enumerate(CHANNELS):
        _set_const_channel(ctrl, i, name, value)

    movie = comp.op("morph_movie")
    if movie is None:
        raise RuntimeError("morph_movie not found")
    _set_par(movie, "playmode", "specify")
    _set_par(movie, "play", False)
    _set_par(movie, "indexunit", "fraction")
    movie.par.index.expr = PROGRESS_EXPR
    movie.nodeX = -140
    movie.nodeY = 230

    clean = _ensure(comp, "nullTOP", "out_clean_movie")
    clean.nodeX = 120
    clean.nodeY = 320
    clean.setInputs([movie])

    driver = comp.op("mudra_to_progress")
    if driver is None:
        driver = comp.create(_td_class("executeDAT"), "mudra_to_progress")
    driver.nodeX = -650
    driver.nodeY = -30
    _set_par(driver, "framestart", True)
    _set_par(driver, "active", True)
    driver.text = r'''import json

HANDS_PATH = "/project1/MediaPipe/hands"
CONTROL_PATH = "/project1/ssd_morph_mudra_scrubber/morph_control"
PINCH_THRESHOLD = 0.060
ENGAGE_THRESHOLD = 0.32
DISENGAGE_THRESHOLD = 0.18
X_MIN = 0.18
X_MAX = 0.82

_latched = [False]

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def _smoothstep(v):
    v = _clamp(v)
    return v * v * (3.0 - 2.0 * v)

def _set_const(index, value):
    ctrl = op(CONTROL_PATH)
    if ctrl is not None:
        getattr(ctrl.par, f"const{index}value").val = value

def _read_hand():
    hands = op(HANDS_PATH)
    if hands is None or not hands.text:
        return None
    try:
        data = json.loads(hands.text)
        all_lm = data.get("gestureResults", {}).get("landmarks", [])
        if not all_lm or len(all_lm[0]) <= 8:
            return None
        lm = all_lm[0]
        thumb = lm[4]
        index = lm[8]
        dx = thumb["x"] - index["x"]
        dy = thumb["y"] - index["y"]
        dz = thumb.get("z", 0.0) - index.get("z", 0.0)
        dist = (dx * dx + dy * dy + dz * dz) ** 0.5
        raw = _clamp(1.0 - (dist / PINCH_THRESHOLD))
        pinch = raw * raw
        x = _clamp((thumb["x"] + index["x"]) * 0.5)
        y = _clamp((thumb["y"] + index["y"]) * 0.5)
        return pinch, x, y, dist
    except Exception:
        return None

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
    mode = int(round(float(ctrl["mode"][0])))
    manual_active = float(ctrl["manual_active"][0]) > 0.5
    hold_release = float(ctrl["hold_release"][0]) > 0.5
    invert_x = float(ctrl["invert_x"][0]) > 0.5

    hand = _read_hand()
    if hand is None:
        pinch, guide_x, guide_y, dist = 0.0, float(ctrl["guide_x"][0]), float(ctrl["guide_y"][0]), 1.0
    else:
        pinch, guide_x, guide_y, dist = hand

    if pinch >= ENGAGE_THRESHOLD:
        _latched[0] = True
    elif pinch <= DISENGAGE_THRESHOLD:
        _latched[0] = False
    engaged = 1.0 if _latched[0] else 0.0

    if manual_active:
        target = _clamp(manual)
    elif mode == 0:
        target = 1.0 if engaged else (progress if hold_release else 0.0)
    elif engaged:
        x = 1.0 - guide_x if invert_x else guide_x
        target = _smoothstep((x - X_MIN) / (X_MAX - X_MIN))
    else:
        target = progress if hold_release else 0.0

    next_progress = progress + (target - progress) * speed
    next_progress = _clamp(next_progress)

    _set_const(0, next_progress)
    _set_const(1, pinch)
    _set_const(2, target)
    _set_const(3, engaged)
    _set_const(6, guide_x)
    _set_const(7, guide_y)
    _set_const(8, dist)
'''

    overlay_cb = _ensure(comp, "textDAT", "slider_overlay_callbacks")
    overlay_cb.nodeX = -650
    overlay_cb.nodeY = -260
    overlay_cb.text = r'''import numpy as np

CONTROL_PATH = "/project1/ssd_morph_mudra_scrubber/morph_control"

def _channel(name, default=0.0):
    ctrl = op(CONTROL_PATH)
    if ctrl is None:
        return default
    ch = ctrl.chan(name)
    if ch is None:
        return default
    try:
        return float(ch[0])
    except Exception:
        return default

def _circle(arr, cx, cy, r, color):
    h, w, _ = arr.shape
    y, x = np.ogrid[:h, :w]
    mask = (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r
    arr[mask] = color

def _rect(arr, x0, y0, x1, y1, color):
    h, w, _ = arr.shape
    x0 = max(0, min(w, int(x0)))
    x1 = max(0, min(w, int(x1)))
    y0 = max(0, min(h, int(y0)))
    y1 = max(0, min(h, int(y1)))
    arr[y0:y1, x0:x1] = color

def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onCook(scriptOp):
    h = 1024
    w = 1024
    arr = np.zeros((h, w, 4), dtype=np.float32)

    progress = max(0.0, min(1.0, _channel("progress", 0.0)))
    target = max(0.0, min(1.0, _channel("target", progress)))
    engaged = _channel("engaged", 0.0)
    pinch = max(0.0, min(1.0, _channel("pinch", 0.0)))

    x0 = 156
    x1 = 868
    y = 892
    track_h = 8
    px = int(x0 + (x1 - x0) * progress)
    tx = int(x0 + (x1 - x0) * target)

    # soft base plate
    _rect(arr, 100, 838, 924, 950, (0.02, 0.02, 0.018, 0.26))

    # track and filled progress
    _rect(arr, x0, y - track_h // 2, x1, y + track_h // 2, (1.0, 1.0, 1.0, 0.28))
    _rect(arr, x0, y - track_h // 2, px, y + track_h // 2, (1.0, 0.64, 0.20, 0.86))

    # endpoint nodes
    _circle(arr, x0, y, 28, (1.0, 0.66, 0.16, 0.90))
    _circle(arr, x1, y, 28, (0.96, 0.28, 0.24, 0.90))
    _circle(arr, x0, y, 14, (0.08, 0.035, 0.02, 0.62))
    _circle(arr, x1, y, 14, (0.08, 0.02, 0.02, 0.62))

    # target ghost and active handle
    _circle(arr, tx, y, 15, (0.60, 0.90, 1.0, 0.26))
    ring_alpha = 0.95 if engaged > 0.5 else 0.55
    _circle(arr, px, y, 24, (1.0, 1.0, 1.0, ring_alpha))
    _circle(arr, px, y, 13, (0.05, 0.05, 0.045, 0.72))
    if pinch > 0.05:
        _circle(arr, px, y, int(28 + pinch * 20), (0.32, 0.90, 0.76, min(0.46, 0.14 + pinch * 0.34)))

    scriptOp.copyNumpyArray(arr)
'''

    overlay = _ensure(comp, "scriptTOP", "slider_overlay")
    overlay.nodeX = 120
    overlay.nodeY = 20
    _set_par(overlay, "callbacks", overlay_cb.path)
    duplicate_cb = comp.op("slider_overlay_callbacks1")
    if duplicate_cb is not None:
        duplicate_cb.destroy()
    _set_par(overlay, "outputresolution", "custom")
    _set_par(overlay, "resolutionw", 1024)
    _set_par(overlay, "resolutionh", 1024)

    over = _ensure(comp, "overTOP", "morph_with_slider_overlay")
    over.nodeX = 400
    over.nodeY = 230
    # Over TOP composites input 0 over input 1. Keep the diagnostic overlay on
    # top so the operator can see hand/pinch status while viewing out_morph.
    over.setInputs([overlay, movie])

    out = comp.op("out_morph")
    if out is None:
        out = comp.create(_td_class("nullTOP"), "out_morph")
    out.nodeX = 650
    out.nodeY = 230
    out.setInputs([over])

    notes = comp.op("README")
    if notes is not None:
        notes.text = (
            "SSD Morph Mudra Scrubber v002\n\n"
            "Output TOP: out_morph\n"
            "Clean movie TOP: out_clean_movie\n"
            "Control CHOP: morph_control\n\n"
            "Default mode is pinch-scrub: pinch thumb/index and move the hand "
            "left-right to guide progress between the two artworks. Release "
            "to hold the current morph point.\n\n"
            "Manual test: set manual_active=1, then set manual to 0..1.\n"
            "Set manual_active back to 0 for MediaPipe control.\n\n"
            "Internal experiment only. Austin per-output approval is required "
            "before public display.\n"
        )

    comp.store("ssd_template_role", "morph_mudra_scrubber_v002")
    comp.save(V002_TOX)
    return {
        "component": comp.path,
        "output_top": out.path,
        "clean_top": clean.path,
        "overlay_top": overlay.path,
        "control_channels": [name for name, _ in CHANNELS],
        "template_tox": V002_TOX,
    }


result = upgrade()
print(json.dumps(result, indent=2))
