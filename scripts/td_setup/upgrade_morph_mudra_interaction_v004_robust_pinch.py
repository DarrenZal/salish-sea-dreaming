"""
Upgrade /project1/ssd_morph_mudra_scrubber to v004 robust pinch.

Keeps the v003 low-latency ProRes artwork source and the pinch-scrub interface,
but replaces the fixed thumb/index distance detector with a palm-size-normalized
pinch score. This makes detection less dependent on hand distance from camera.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
V004_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v004_robust_pinch.tox"
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
    ("speed", 0.34),
    ("guide_x", 0.5),
    ("guide_y", 0.5),
    ("pinch_distance", 1.0),
    ("mode", 1.0),
    ("manual_active", 0.0),
    ("hold_release", 1.0),
    ("invert_x", 0.0),
    ("pinch_ratio", 1.0),
    ("hand_present", 0.0),
    ("hand_count", 0.0),
    ("pinch_close", 0.24),
    ("pinch_far", 0.62),
    ("engage_threshold", 0.42),
    ("release_threshold", 0.18),
]


def _set_par(op_obj, par_name, value):
    par_obj = getattr(op_obj.par, par_name, None)
    if par_obj is not None:
        par_obj.val = value
        return True
    return False


def _set_const_channel(chop, index, name, value):
    _set_par(chop, f"const{index}name", name)
    par = getattr(chop.par, f"const{index}value", None)
    if par is None:
        return
    if name in ("progress", "manual", "mode", "hold_release", "invert_x"):
        try:
            par.val = float(chop[name][0])
            return
        except Exception:
            pass
    par.val = value


def upgrade():
    comp = op(COMP_PATH)
    if comp is None:
        raise RuntimeError(f"{COMP_PATH} not found")

    ctrl = comp.op("morph_control")
    driver = comp.op("mudra_to_progress")
    movie = comp.op("morph_movie")
    if ctrl is None or driver is None or movie is None:
        raise RuntimeError("Expected v003 morph_control, mudra_to_progress, and morph_movie")

    _set_par(ctrl, "const", len(CHANNELS))
    for i, (name, value) in enumerate(CHANNELS):
        _set_const_channel(ctrl, i, name, value)

    # Keep the actual artwork ProRes asset from v003.
    movie.par.index.expr = PROGRESS_EXPR
    _set_par(movie, "playmode", "specify")
    _set_par(movie, "indexunit", "fraction")
    _set_par(movie, "play", False)

    _set_par(driver, "framestart", True)
    _set_par(driver, "active", True)
    driver.text = r'''import json
import math

HANDS_PATH = "/project1/MediaPipe/hands"
CONTROL_PATH = "/project1/ssd_morph_mudra_scrubber/morph_control"
X_MIN = 0.16
X_MAX = 0.84

_latched = [False]

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def _smoothstep(v):
    v = _clamp(v)
    return v * v * (3.0 - 2.0 * v)

def _dist(a, b, use_z=False):
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    if use_z:
        dz = a.get("z", 0.0) - b.get("z", 0.0)
        return math.sqrt(dx * dx + dy * dy + dz * dz)
    return math.sqrt(dx * dx + dy * dy)

def _set_const(index, value):
    ctrl = op(CONTROL_PATH)
    if ctrl is not None:
        getattr(ctrl.par, f"const{index}value").val = value

def _control(name, default):
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

def _hand_score(lm, close_ratio, far_ratio):
    if len(lm) <= 20:
        return None
    thumb = lm[4]
    index = lm[8]

    # Palm scale from stable landmarks. This adapts to distance from camera.
    wrist = lm[0]
    index_mcp = lm[5]
    middle_mcp = lm[9]
    pinky_mcp = lm[17]
    palm_a = _dist(wrist, middle_mcp)
    palm_b = _dist(index_mcp, pinky_mcp)
    palm_c = _dist(wrist, index_mcp)
    palm_scale = max(0.0001, palm_a, palm_b, palm_c)

    tip_dist_2d = _dist(thumb, index)
    ratio = tip_dist_2d / palm_scale
    pinch = _clamp((far_ratio - ratio) / max(0.001, far_ratio - close_ratio))
    pinch = pinch * pinch * (3.0 - 2.0 * pinch)

    # Use midpoint between thumb and index as the guide point while pinching.
    guide_x = _clamp((thumb["x"] + index["x"]) * 0.5)
    guide_y = _clamp((thumb["y"] + index["y"]) * 0.5)
    return {
        "pinch": pinch,
        "ratio": ratio,
        "dist": tip_dist_2d,
        "x": guide_x,
        "y": guide_y,
    }

def _read_best_hand():
    hands = op(HANDS_PATH)
    if hands is None or not hands.text:
        return None, 0
    try:
        data = json.loads(hands.text)
        all_lm = data.get("gestureResults", {}).get("landmarks", [])
    except Exception:
        return None, 0
    if not all_lm:
        return None, 0

    close_ratio = _control("pinch_close", 0.24)
    far_ratio = _control("pinch_far", 0.62)
    best = None
    for lm in all_lm:
        score = _hand_score(lm, close_ratio, far_ratio)
        if score is None:
            continue
        if best is None or score["pinch"] > best["pinch"]:
            best = score
    return best, len(all_lm)

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
    engage_threshold = float(ctrl["engage_threshold"][0])
    release_threshold = float(ctrl["release_threshold"][0])

    hand, hand_count = _read_best_hand()
    if hand is None:
        pinch = 0.0
        guide_x = float(ctrl["guide_x"][0])
        guide_y = float(ctrl["guide_y"][0])
        dist = 1.0
        ratio = 1.0
        hand_present = 0.0
    else:
        pinch = hand["pinch"]
        guide_x = hand["x"]
        guide_y = hand["y"]
        dist = hand["dist"]
        ratio = hand["ratio"]
        hand_present = 1.0

    if pinch >= engage_threshold:
        _latched[0] = True
    elif pinch <= release_threshold:
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
    _set_const(13, ratio)
    _set_const(14, hand_present)
    _set_const(15, float(hand_count))
'''

    notes = comp.op("README")
    if notes is not None:
        notes.text = (
            "SSD Morph Mudra Scrubber v004 robust pinch\n\n"
            "Output TOP: out_morph\n"
            "Clean movie TOP: out_clean_movie\n"
            "Control CHOP: morph_control\n\n"
            "This version uses the actual artwork ProRes morph asset from v003 "
            "and a palm-size-normalized pinch detector. Pinch thumb/index and "
            "move left-right to guide the transition; release to hold.\n\n"
            "Calibration channels: pinch_ratio, hand_present, hand_count, "
            "pinch_close, pinch_far, engage_threshold, release_threshold.\n"
            "If pinch misses, raise pinch_far or lower engage_threshold. If it "
            "triggers too easily, lower pinch_far or raise engage_threshold.\n\n"
            "Manual test: set manual_active=1, then set manual to 0..1. "
            "Set manual_active back to 0 for MediaPipe control.\n\n"
            "Internal experiment only. Austin per-output approval is required "
            "before public display.\n"
        )

    comp.store("ssd_template_role", "morph_mudra_scrubber_v004_robust_pinch")
    comp.save(V004_TOX)
    return {
        "component": comp.path,
        "control_channels": [name for name, _ in CHANNELS],
        "template_tox": V004_TOX,
    }


result = upgrade()
print(json.dumps(result, indent=2))
