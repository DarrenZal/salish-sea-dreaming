"""
Add pose-wrist fallback control to SSD morph/mudra scrubber components.

Root cause this addresses: on 2026-05-18, /project1/MediaPipe was producing
live pose landmarks and camera video, but /project1/MediaPipe/hands was returning
empty gestureResults.landmarks. The original scrubber only listened to the hand
landmark stream, so progress stayed frozen at 0.

This driver keeps the preferred thumb/index pinch path when hand landmarks are
available. If the hand model returns no landmarks, it falls back to MediaPipe
pose wrist landmarks and scrubs by the visible wrist's x position.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"

COMPONENTS = [
    {
        "path": "/project1/ssd_morph_mudra_scrubber",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox",
    },
    {
        "path": "/project1/ssd_morph_mudra_scrubber_raven_cosmic",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_raven_cosmic_v001.tox",
    },
    {
        "path": "/project1/ssd_morph_mudra_scrubber_primitive_cycle",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_primitive_cycle_v001.tox",
    },
    {
        "path": "/project1/ssd_morph_mudra_scrubber_primitive_field",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_primitive_field_v001.tox",
    },
]

WORKSPACE_TOE = f"{ROOT}/td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe"


DRIVER_TEMPLATE = r'''import json
import math

HANDS_PATH = "/project1/MediaPipe/hands"
POSE_PATH = "/project1/MediaPipe/pose"
CONTROL_PATH = "__CONTROL_PATH__"
X_MIN = 0.16
X_MAX = 0.84

_latched = [False]

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def _smoothstep(v):
    v = _clamp(v)
    return v * v * (3.0 - 2.0 * v)

def _dist(a, b):
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
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

    wrist = lm[0]
    index_mcp = lm[5]
    middle_mcp = lm[9]
    pinky_mcp = lm[17]
    palm_scale = max(0.0001, _dist(wrist, middle_mcp), _dist(index_mcp, pinky_mcp), _dist(wrist, index_mcp))
    tip_dist = _dist(thumb, index)
    ratio = tip_dist / palm_scale
    pinch = _clamp((far_ratio - ratio) / max(0.001, far_ratio - close_ratio))
    pinch = pinch * pinch * (3.0 - 2.0 * pinch)

    return {
        "source": "hand",
        "pinch": pinch,
        "ratio": ratio,
        "dist": tip_dist,
        "x": _clamp((thumb["x"] + index["x"]) * 0.5),
        "y": _clamp((thumb["y"] + index["y"]) * 0.5),
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

    close_ratio = _control("pinch_close", 0.20)
    far_ratio = _control("pinch_far", 0.74)
    best = None
    for lm in all_lm:
        score = _hand_score(lm, close_ratio, far_ratio)
        if score is None:
            continue
        if best is None or score["pinch"] > best["pinch"]:
            best = score
    return best, len(all_lm)

def _visibility(lm):
    try:
        return float(lm.get("visibility", 1.0))
    except Exception:
        return 0.0

def _read_pose_wrist():
    pose = op(POSE_PATH)
    if pose is None or not pose.text:
        return None
    try:
        data = json.loads(pose.text)
        all_lm = data.get("poseResults", {}).get("landmarks", [])
        if not all_lm or len(all_lm[0]) <= 16:
            return None
        lm = all_lm[0]
    except Exception:
        return None

    # MediaPipe Pose: 15 = left wrist, 16 = right wrist.
    candidates = []
    for idx in (15, 16):
        wrist = lm[idx]
        vis = _visibility(wrist)
        if vis < 0.25:
            continue
        x = _clamp(float(wrist.get("x", 0.5)))
        y = _clamp(float(wrist.get("y", 0.5)))
        # Favor the more visible and more raised wrist, but do not require a
        # special pose; this is the fallback when the hand model fails.
        score = vis + max(0.0, 0.9 - y) * 0.35
        candidates.append((score, vis, x, y))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    _, vis, x, y = candidates[0]
    return {
        "source": "pose_wrist",
        "pinch": 0.0,
        "ratio": 0.0,
        "dist": 0.0,
        "x": x,
        "y": y,
        "visibility": vis,
    }

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
    pose_wrist = None if hand is not None else _read_pose_wrist()

    if hand is not None:
        source = hand
        pinch = hand["pinch"]
        if pinch >= engage_threshold:
            _latched[0] = True
        elif pinch <= release_threshold:
            _latched[0] = False
        engaged = 1.0 if _latched[0] else 0.0
        hand_present = 1.0
    elif pose_wrist is not None:
        source = pose_wrist
        pinch = 0.0
        engaged = 1.0
        hand_present = 1.0
        hand_count = 1
    else:
        source = None
        pinch = 0.0
        engaged = 0.0
        hand_present = 0.0
        hand_count = 0

    if source is None:
        guide_x = float(ctrl["guide_x"][0])
        guide_y = float(ctrl["guide_y"][0])
        dist = 1.0
        ratio = 1.0
    else:
        guide_x = source["x"]
        guide_y = source["y"]
        dist = source["dist"]
        ratio = source["ratio"]

    if manual_active:
        target = _clamp(manual)
    elif mode == 0:
        target = 1.0 if engaged else (progress if hold_release else 0.0)
    elif engaged and source is not None:
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


def _driver_text(comp_path):
    return DRIVER_TEMPLATE.replace("__CONTROL_PATH__", comp_path + "/morph_control")


def install():
    results = []
    for spec in COMPONENTS:
        comp = op(spec["path"])
        if comp is None:
            results.append({"component": spec["path"], "exists": False})
            continue
        driver = comp.op("mudra_to_progress")
        ctrl = comp.op("morph_control")
        if driver is None or ctrl is None:
            results.append({"component": spec["path"], "exists": True, "updated": False})
            continue

        driver.text = _driver_text(spec["path"])
        if hasattr(driver.par, "framestart"):
            driver.par.framestart.val = True
        if hasattr(driver.par, "active"):
            driver.par.active.val = True
        ctrl.par.const0value.val = 0.0
        ctrl.par.const4value.val = 0.0
        ctrl.par.const10value.val = 0.0
        comp.store("ssd_control_driver", "pinch_with_pose_wrist_fallback_v001")
        comp.save(spec["tox"])
        results.append({"component": spec["path"], "updated": True, "tox": spec["tox"]})

    project.save(WORKSPACE_TOE)
    print(json.dumps(results, indent=2))
    return results


install_result = install()
