# setup_hand_bridge.py — Wire MediaPipe hand tracking into a stable
# Constant CHOP at /project1/hand_pos that scene expressions can read.
#
# Prerequisites (one-time, manual in TD):
#   1. Import MediaPipe.tox into /project1 as 'mediapipe_base'. The .tox
#      ships in tools/mediapipe/MediaPipe.tox (downloaded from
#      github.com/torinmb/mediapipe-touchdesigner).
#      File -> Import -> MediaPipe.tox; let it initialize (may take a
#      few seconds — 180 MB component with embedded models).
#   2. Grant webcam permission to TouchDesigner (Mac: System Settings ->
#      Privacy & Security -> Camera).
#   3. Optional: enable "Generate GUI" pulses on the MediaPipe component
#      to expose the config panels for live tuning.
#
# What this script does (idempotent, safe to re-run):
#   1. Creates/updates /project1/hand_pos — a Constant CHOP with x,y channels.
#   2. Creates/updates /project1/hand_poll — an Execute DAT with an
#      onFrameStart callback that parses /project1/mediapipe_base/hand_results
#      JSON every frame and writes fingertip x/y into hand_pos.
#
# Why JSON parse instead of MediaPipe's own hand SOP output?
#   At time of writing (TD 2025.32050, MediaPipe plugin 2026-Q1), the
#   plugin's hand SOP ('/project1/mediapipe_base/hand_tracking/hand1') was
#   observed to cache and not re-cook even when hand_results JSON updated.
#   The JSON path is reliably live. Worth revisiting if a newer plugin
#   release fixes the SOP-side refresh.
#
# Coordinates:
#   MediaPipe returns normalized [0,1] with origin top-left.
#   We remap to [-3, 3] roughly, with Y inverted so hand-up = +Y.
#   Tuning knobs: SCALE (range), tip_index (which landmark).
#
# Landmark indices (MediaPipe hand model):
#   0 = wrist,  4 = thumb tip,  8 = index fingertip (default),
#   12 = middle tip, 16 = ring tip, 20 = pinky tip.

project = op('/project1')

# Tuning
SCALE = 6.0          # remap [0,1] -> [-SCALE/2, +SCALE/2]
TIP_INDEX = 8        # index fingertip
MEDIAPIPE_PATH = '/project1/mediapipe_base/hand_results'

# --- hand_pos Constant CHOP ------------------------------------------------
hp = op('/project1/hand_pos')
if hp is None:
    hp = project.create(constantCHOP, 'hand_pos')
    hp.nodeX = -900; hp.nodeY = 400
hp.par.name0 = 'x'; hp.par.name1 = 'y'
# Don't reset values on re-run — preserve last known hand position

# --- Execute DAT per-frame parser -----------------------------------------
ex = op('/project1/hand_poll')
if ex is None:
    ex = project.create(executeDAT, 'hand_poll')
    ex.nodeX = -1100; ex.nodeY = 400
ex.par.framestart = True
ex.par.active = True

ex.text = f'''import json

def onStart(): pass
def onCreate(): pass
def onExit(): pass

def onFrameStart(frame):
	hr = op("{MEDIAPIPE_PATH}")
	if hr is None: return
	raw = hr.text
	if not raw: return
	try: data = json.loads(raw)
	except Exception: return
	lm = data.get("gestureResults", {{}}).get("landmarks", [])
	if not lm or not lm[0] or len(lm[0]) <= {TIP_INDEX}: return
	tip = lm[0][{TIP_INDEX}]
	hp = op("/project1/hand_pos")
	# MediaPipe: x,y in [0,1], origin top-left. Remap + invert Y.
	hp.par.value0 = (tip["x"] - 0.5) * {SCALE}
	hp.par.value1 = -(tip["y"] - 0.5) * {SCALE}
'''

# Toggle to force re-registration of callbacks after text change
ex.par.active = False
ex.par.active = True

print("hand_pos bridge installed.")
print(f"  /project1/hand_pos  (Constant CHOP: x, y)")
print(f"  /project1/hand_poll (Execute DAT: onFrameStart)")
print(f"  source : {MEDIAPIPE_PATH}")
print(f"  scale  : [0,1] -> [-{SCALE/2}, +{SCALE/2}]   tip_index={TIP_INDEX}")
print("")
print("Next: run mycelium_audio.py (scene reads hand_pos if present, else 0).")
