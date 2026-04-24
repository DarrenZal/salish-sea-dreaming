# Mycelium Network — audio + hand-gesture-reactive fork of mycelium.py
#
# Audio inputs (OSC /salish/audio/volume + /salish/audio/energy, port 7000):
#   - pulse brightness  (volume remap -> 0.15 baseline, 5.65 at peak)
#   - pulse drift base speed
#   - bright-pulse hue intensity  (energy remap: teal -> cyan)
#
# Hand inputs (optional — from /project1/hand_pos Constant CHOP, fed by
# MediaPipe hand tracking; see setup_hand_bridge.py):
#   - hand X  -> pulse drift position offset (horizontal "conducting")
#              + warm/cool palette shift (right=warm pink, left=cool blue)
#   - hand Y  -> pulse drift position offset (vertical "conducting")
#              + glow intensity (raised hand = bigger bloom)
#
# Hand integration gracefully degrades: if /project1/hand_pos doesn't
# exist, expressions fall back to 0 and the scene is purely audio-reactive.
#
# Live-tuned 2026-04-23 via TD MCP with Darren; mycelium aesthetic
# matches Prav's "carrier wave memetics" brief — stillness rewarded,
# depth over flash, audio drives INTENSITY (not velocity), hand adds
# gestural-conducting layer on top.

project = op('/project1')

# ===========================================================================
# OSC audio chain: osc_in -> select (per feature) -> lag -> merge -> rename
# ===========================================================================

audio_osc = op('/project1/audio_osc')
if audio_osc is None:
    audio_osc = project.create(oscinCHOP, 'audio_osc')
    audio_osc.nodeX = -800; audio_osc.nodeY = 300
audio_osc.par.port = 7000
audio_osc.par.active = True

def _ensure_select(name, pattern, nodeY):
    n = op(f'/project1/{name}')
    if n is None:
        n = project.create(selectCHOP, name)
        n.nodeX = -650; n.nodeY = nodeY
    if not n.inputs or n.inputs[0] is not audio_osc:
        for i in range(len(n.inputConnectors)):
            try: n.inputConnectors[i].disconnect()
            except Exception: pass
        n.inputConnectors[0].connect(audio_osc)
    n.par.channames = pattern
    return n

a_vol_sel = _ensure_select('a_vol_sel', '*volume*', 400)
a_eng_sel = _ensure_select('a_eng_sel', '*energy*', 200)

a_vol_fast = op('/project1/a_vol_fast') or project.create(lagCHOP, 'a_vol_fast')
a_vol_fast.par.lag1 = 0.4; a_vol_fast.par.lag2 = 0.6
a_vol_fast.nodeX = -500; a_vol_fast.nodeY = 400
if not a_vol_fast.inputs or a_vol_fast.inputs[0] is not a_vol_sel:
    for i in range(len(a_vol_fast.inputConnectors)):
        try: a_vol_fast.inputConnectors[i].disconnect()
        except Exception: pass
    a_vol_fast.inputConnectors[0].connect(a_vol_sel)

a_eng_lag = op('/project1/a_eng_lag') or project.create(lagCHOP, 'a_eng_lag')
a_eng_lag.par.lag1 = 0.4; a_eng_lag.par.lag2 = 0.4
a_eng_lag.nodeX = -500; a_eng_lag.nodeY = 200
if not a_eng_lag.inputs or a_eng_lag.inputs[0] is not a_eng_sel:
    for i in range(len(a_eng_lag.inputConnectors)):
        try: a_eng_lag.inputConnectors[i].disconnect()
        except Exception: pass
    a_eng_lag.inputConnectors[0].connect(a_eng_sel)

a_merged = op('/project1/a_merged') or project.create(mergeCHOP, 'a_merged')
a_merged.nodeX = -350; a_merged.nodeY = 300
for i in range(len(a_merged.inputConnectors)):
    try: a_merged.inputConnectors[i].disconnect()
    except Exception: pass
a_merged.inputConnectors[0].connect(a_vol_fast)
a_merged.inputConnectors[1].connect(a_eng_lag)

audio_vals = op('/project1/audio_vals') or project.create(renameCHOP, 'audio_vals')
audio_vals.par.renamefrom = '*volume* *energy*'
audio_vals.par.renameto = 'volume energy'
audio_vals.nodeX = -200; audio_vals.nodeY = 300
if not audio_vals.inputs or audio_vals.inputs[0] is not a_merged:
    for i in range(len(audio_vals.inputConnectors)):
        try: audio_vals.inputConnectors[i].disconnect()
        except Exception: pass
    audio_vals.inputConnectors[0].connect(a_merged)

# ===========================================================================
# Expression fragments
# ===========================================================================
VOL_FROM_LO, VOL_FROM_HI = 0.70, 0.95
ENG_FROM_LO, ENG_FROM_HI = 0.02, 0.15

VOL = (
    f"max(0.0, min(1.0, "
    f"(op('/project1/a_vol_fast')['salish/audio/volume'][0] - {VOL_FROM_LO}) / {VOL_FROM_HI - VOL_FROM_LO}"
    f"))"
)
ENG = (
    f"max(0.0, min(1.0, "
    f"(op('/project1/a_eng_lag')['salish/audio/energy'][0] - {ENG_FROM_LO}) / {ENG_FROM_HI - ENG_FROM_LO}"
    f"))"
)
# Hand fragments — gracefully degrade if hand_pos doesn't exist.
# We reference it directly; if the CHOP is absent at evaluate time, TD
# produces 0 for the channel read, which is equivalent to "hand at origin".
HX = "(op('/project1/hand_pos')['x'][0] if op('/project1/hand_pos') else 0)"
HY = "(op('/project1/hand_pos')['y'][0] if op('/project1/hand_pos') else 0)"

# ===========================================================================
# Scene (non-destructive — only touches 'salish_audio')
# ===========================================================================
_existing = op('/project1/salish_audio')
if _existing:
    _existing.destroy()

container = project.create(baseCOMP, 'salish_audio')
container.nodeX = 400; container.nodeY = 0

# --- Static vein network ---------------------------------------------------
network_noise = container.create(noiseTOP, 'network_noise')
network_noise.par.mono = True
network_noise.par.period = 1.2
network_noise.par.harmon = 4
network_noise.par.rough = 0.6
network_noise.par.seed = 5
network_noise.par.resolutionw = 1280
network_noise.par.resolutionh = 720
network_noise.nodeX = 0; network_noise.nodeY = 0

veins = container.create(edgeTOP, 'veins')
veins.inputConnectors[0].connect(network_noise)
veins.nodeX = 200; veins.nodeY = 0

veins_boost = container.create(levelTOP, 'veins_boost')
veins_boost.inputConnectors[0].connect(veins)
veins_boost.par.brightness1 = 5
veins_boost.par.gamma1 = 0.5
veins_boost.nodeX = 400; veins_boost.nodeY = 0

# --- Pulse: slow constant drift + hand position offset ---------------------
# Rate is static (no teleport on variable rate). Hand adds a POSITION offset
# scaled by 0.2 — moving hand shifts where the pulse is sampled in noise.
pulse_noise = container.create(noiseTOP, 'pulse_noise')
pulse_noise.par.mono = True
pulse_noise.par.period = 0.8
pulse_noise.par.harmon = 1
pulse_noise.par.rough = 0.15
pulse_noise.par.seed = 5
pulse_noise.par.resolutionw = 1280
pulse_noise.par.resolutionh = 720
pulse_noise.par.tx.expr = f'absTime.seconds * 0.02 + ({HX}) * 0.2'
pulse_noise.par.ty.expr = f'absTime.seconds * 0.014 + ({HY}) * 0.2'
pulse_noise.nodeX = 0; pulse_noise.nodeY = -200

pulse_sharp = container.create(levelTOP, 'pulse_sharp')
pulse_sharp.inputConnectors[0].connect(pulse_noise)
pulse_sharp.par.gamma1 = 2.5
pulse_sharp.par.blacklevel = 0.3
pulse_sharp.nodeX = 200; pulse_sharp.nodeY = -200

pulsing = container.create(compositeTOP, 'pulsing')
pulsing.par.operand = 'multiply'
pulsing.inputConnectors[0].connect(veins_boost)
pulsing.inputConnectors[1].connect(pulse_sharp)
pulsing.nodeX = 400; pulsing.nodeY = -100

pulse_boost = container.create(levelTOP, 'pulse_boost')
pulse_boost.inputConnectors[0].connect(pulsing)
pulse_boost.par.brightness1.expr = f'0.15 + ({VOL}) * 5.5'
pulse_boost.par.gamma1 = 0.7
pulse_boost.nodeX = 600; pulse_boost.nodeY = -100

# --- Colors: audio + hand X warm/cool shift --------------------------------
dim_color = container.create(constantTOP, 'dim_color')
dim_color.par.colorr = 0.015
dim_color.par.colorg = 0.09
dim_color.par.colorb = 0.06
dim_color.par.alpha = 1.0
dim_color.par.resolutionw = 1280
dim_color.par.resolutionh = 720
dim_color.nodeX = 400; dim_color.nodeY = 100

dim_veins = container.create(compositeTOP, 'dim_veins')
dim_veins.par.operand = 'multiply'
dim_veins.inputConnectors[0].connect(veins_boost)
dim_veins.inputConnectors[1].connect(dim_color)
dim_veins.nodeX = 600; dim_veins.nodeY = 50

# Bright-pulse hue:
#   energy shift: teal-green -> luminous cyan
#   hand right (+X): warmer pink tint
#   hand left (-X):  cooler blue tint
bright_color = container.create(constantTOP, 'bright_color')
bright_color.par.colorr.expr = f'0.10 + ({ENG}) * 0.20 + max(0, {HX}) * 0.08'
bright_color.par.colorg.expr = f'1.00 - ({ENG}) * 0.10 - abs({HX}) * 0.05'
bright_color.par.colorb.expr = f'0.50 + ({ENG}) * 0.50 + max(0, -({HX})) * 0.15'
bright_color.par.alpha = 1.0
bright_color.par.resolutionw = 1280
bright_color.par.resolutionh = 720
bright_color.nodeX = 600; bright_color.nodeY = -250

bright_pulse = container.create(compositeTOP, 'bright_pulse')
bright_pulse.par.operand = 'multiply'
bright_pulse.inputConnectors[0].connect(pulse_boost)
bright_pulse.inputConnectors[1].connect(bright_color)
bright_pulse.nodeX = 800; bright_pulse.nodeY = -100

# --- Combine + bloom (with hand Y boost) + final composite ----------------
combined = container.create(compositeTOP, 'combined')
combined.par.operand = 'add'
combined.inputConnectors[0].connect(dim_veins)
combined.inputConnectors[1].connect(bright_pulse)
combined.nodeX = 1000; combined.nodeY = 0

# Glow size: audio peaks + hand Y (raised hand = big bloom)
glow = container.create(blurTOP, 'glow')
glow.inputConnectors[0].connect(bright_pulse)
glow.par.size.expr = f'5 + ({VOL}) * 40 + (({HY}) + 3) * 3'
glow.nodeX = 800; glow.nodeY = -250

with_glow = container.create(compositeTOP, 'with_glow')
with_glow.par.operand = 'add'
with_glow.inputConnectors[0].connect(combined)
with_glow.inputConnectors[1].connect(glow)
with_glow.nodeX = 1200; with_glow.nodeY = 0

backdrop = container.create(constantTOP, 'backdrop')
backdrop.par.colorr = 0.01
backdrop.par.colorg = 0.015
backdrop.par.colorb = 0.02
backdrop.par.alpha = 1.0
backdrop.par.resolutionw = 1280
backdrop.par.resolutionh = 720
backdrop.nodeX = 1000; backdrop.nodeY = 200

final_comp = container.create(compositeTOP, 'final_comp')
final_comp.par.operand = 'over'
final_comp.inputConnectors[0].connect(with_glow)
final_comp.inputConnectors[1].connect(backdrop)
final_comp.nodeX = 1300; final_comp.nodeY = 100

out = container.create(outTOP, 'output')
out.inputConnectors[0].connect(final_comp)
out.nodeX = 1500; out.nodeY = 100
out.viewer = True
out.display = True

print("mycelium_audio — live-tuned 2026-04-23")
print(f"  audio_vals : {audio_vals.path}  (volume, energy)")
print(f"  hand_pos   : optional — {op('/project1/hand_pos') and op('/project1/hand_pos').path or '(not present; set up via setup_hand_bridge.py)'}")
print(f"  scene      : {container.path}  ({len(container.children)} nodes)")
print(f"  output     : {out.path}")
