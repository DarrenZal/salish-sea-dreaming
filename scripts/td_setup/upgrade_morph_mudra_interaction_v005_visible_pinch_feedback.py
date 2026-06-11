"""
Upgrade /project1/ssd_morph_mudra_scrubber to v005 visible pinch feedback.

Keeps v004 robust pinch and actual artwork source. Adds visible diagnostics to
the overlay so the operator can tell whether MediaPipe sees a hand and whether
the pinch is crossing threshold.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
V005_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v005_visible_pinch_feedback.tox"


def upgrade():
    comp = op(COMP_PATH)
    if comp is None:
        raise RuntimeError(f"{COMP_PATH} not found")

    ctrl = comp.op("morph_control")
    overlay_cb = comp.op("slider_overlay_callbacks")
    overlay = comp.op("slider_overlay")
    movie = comp.op("morph_movie")
    if ctrl is None or overlay_cb is None or overlay is None or movie is None:
        raise RuntimeError("Expected v004 morph_control, slider_overlay, and morph_movie")

    # More forgiving defaults for live hand testing. These remain adjustable in
    # morph_control without editing code.
    ctrl.par.const0value.val = 0.0   # progress
    ctrl.par.const1value.val = 0.0   # pinch
    ctrl.par.const2value.val = 0.0   # target
    ctrl.par.const3value.val = 0.0   # engaged
    ctrl.par.const4value.val = 0.0   # manual
    ctrl.par.const5value.val = 0.34  # speed
    ctrl.par.const10value.val = 0.0  # manual_active
    ctrl.par.const16value.val = 0.20 # pinch_close
    ctrl.par.const17value.val = 0.74 # pinch_far
    ctrl.par.const18value.val = 0.30 # engage_threshold
    ctrl.par.const19value.val = 0.10 # release_threshold

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

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def _mix(a, b, t):
    t = _clamp(t)
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(len(a)))

def _circle(arr, cx, cy, r, color):
    h, w, _ = arr.shape
    y, x = np.ogrid[:h, :w]
    mask = (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r
    arr[mask] = color

def _ring(arr, cx, cy, r_outer, r_inner, color):
    h, w, _ = arr.shape
    y, x = np.ogrid[:h, :w]
    d = (x - cx) * (x - cx) + (y - cy) * (y - cy)
    mask = (d <= r_outer * r_outer) & (d >= r_inner * r_inner)
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

    progress = _clamp(_channel("progress", 0.0))
    target = _clamp(_channel("target", progress))
    engaged = _channel("engaged", 0.0)
    pinch = _clamp(_channel("pinch", 0.0))
    hand_present = _channel("hand_present", 0.0)
    hand_count = _channel("hand_count", 0.0)
    guide_x = _clamp(_channel("guide_x", 0.5))
    guide_y = _clamp(_channel("guide_y", 0.5))
    engage_threshold = _clamp(_channel("engage_threshold", 0.30))

    x0 = 156
    x1 = 868
    y = 892
    track_h = 8
    px = int(x0 + (x1 - x0) * progress)
    tx = int(x0 + (x1 - x0) * target)

    # Bottom scrubber.
    _rect(arr, 100, 838, 924, 950, (0.02, 0.02, 0.018, 0.24))
    _rect(arr, x0, y - track_h // 2, x1, y + track_h // 2, (1.0, 1.0, 1.0, 0.28))
    _rect(arr, x0, y - track_h // 2, px, y + track_h // 2, (1.0, 0.64, 0.20, 0.86))
    _circle(arr, x0, y, 28, (1.0, 0.66, 0.16, 0.90))
    _circle(arr, x1, y, 28, (0.96, 0.28, 0.24, 0.90))
    _circle(arr, x0, y, 14, (0.08, 0.035, 0.02, 0.62))
    _circle(arr, x1, y, 14, (0.08, 0.02, 0.02, 0.62))
    _circle(arr, tx, y, 15, (0.60, 0.90, 1.0, 0.26))
    _circle(arr, px, y, 24, (1.0, 1.0, 1.0, 0.95 if engaged > 0.5 else 0.55))
    _circle(arr, px, y, 13, (0.05, 0.05, 0.045, 0.72))

    # Top-left detection status: gray/red = no hand, blue = hand, green = pinch.
    _rect(arr, 42, 42, 338, 132, (0.02, 0.02, 0.018, 0.30))
    hand_color = (0.36, 0.48, 0.60, 0.70)
    if hand_present > 0.5:
        hand_color = _mix((0.12, 0.66, 1.0, 0.86), (0.18, 1.0, 0.58, 0.95), pinch)
    _circle(arr, 88, 87, 26, hand_color)
    if hand_count >= 1:
        _ring(arr, 88, 87, 38, 33, (0.12, 0.66, 1.0, 0.50))
    if engaged > 0.5:
        _ring(arr, 88, 87, 47, 42, (0.18, 1.0, 0.58, 0.82))

    # Pinch strength meter beside the status light.
    meter_x0 = 134
    meter_x1 = 306
    meter_y0 = 76
    meter_y1 = 98
    _rect(arr, meter_x0, meter_y0, meter_x1, meter_y1, (1.0, 1.0, 1.0, 0.18))
    _rect(arr, meter_x0, meter_y0, meter_x0 + int((meter_x1 - meter_x0) * pinch), meter_y1, (0.18, 1.0, 0.58, 0.86))
    threshold_x = meter_x0 + int((meter_x1 - meter_x0) * engage_threshold)
    _rect(arr, threshold_x - 2, meter_y0 - 8, threshold_x + 2, meter_y1 + 8, (1.0, 1.0, 1.0, 0.65))

    # Live hand guide dot. If no hand is detected, only the status panel remains.
    if hand_present > 0.5:
        gx = int(guide_x * w)
        gy = int(guide_y * h)
        dot = _mix((0.12, 0.66, 1.0, 0.72), (0.18, 1.0, 0.58, 0.92), pinch)
        _ring(arr, gx, gy, int(34 + pinch * 20), int(28 + pinch * 15), dot)
        _circle(arr, gx, gy, int(8 + pinch * 7), dot)

    scriptOp.copyNumpyArray(arr)
'''

    overlay.par.callbacks.val = overlay_cb.path
    overlay.cook(force=True)

    comp.store("ssd_template_role", "morph_mudra_scrubber_v005_visible_pinch_feedback")
    comp.save(V005_TOX)
    return {
        "component": comp.path,
        "template_tox": V005_TOX,
        "pinch_far": ctrl.par.const17value.eval(),
        "engage_threshold": ctrl.par.const18value.eval(),
    }


result = upgrade()
print(json.dumps(result, indent=2))
