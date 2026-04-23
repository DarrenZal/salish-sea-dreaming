# Mycelium Network — audio-reactive fork of mycelium.py
#
# Reads /salish/audio/volume (RMS 0-1) and /salish/audio/energy (spectral
# energy ratio 0-1) from an OSC In CHOP and drives:
#   - pulse motion speed   (volume -> tx/ty drift rate)
#   - pulse brightness     (volume -> pulse_boost.brightness)
#   - glow size            (volume -> blur radius)
#   - hue of bright pulse  (energy -> colorr/g/b, cool<->warm shift)
#
# Aesthetic brief (Prav 2026-04-23): carrier wave memetics, stillness
# rewarded, depth over flash. Baseline is quiet + barely breathing;
# audio drives amplitude above that.
#
# Safe to run standalone: if no OSC In CHOP exists at /project1/audio_osc,
# one is created listening on port 7000 (same port gallery_audio.py sends to).
# A downstream Rename CHOP (audio_vals) normalises the channel names to the
# stable 'volume' and 'energy' scalars that the scene expressions reference.

project = op('/project1')

# --- OSC In + Rename CHOP chain -------------------------------------------
# The OSC In CHOP auto-generates channel names from whatever /address the
# sender uses. To decouple the scene from TD's naming conventions, we feed
# it into a Rename CHOP that emits 'volume' and 'energy' as stable names.
audio_osc = op('/project1/audio_osc')
if audio_osc is None:
    audio_osc = project.create(oscinCHOP, 'audio_osc')
    audio_osc.par.port = 7000
    audio_osc.par.active = True
    audio_osc.nodeX = -600
    audio_osc.nodeY = 300

audio_vals = op('/project1/audio_vals')
if audio_vals is None:
    audio_vals = project.create(renameCHOP, 'audio_vals')
    audio_vals.inputConnectors[0].connect(audio_osc)
    audio_vals.nodeX = -400
    audio_vals.nodeY = 300
# Map any channel whose name contains 'volume' -> 'volume',
# anything containing 'energy' -> 'energy'. Tolerates whatever OSC In
# did with the address (full path, dotted, colon-delimited, etc).
audio_vals.par.renamefrom = '*volume* *energy*'
audio_vals.par.renameto   = 'volume energy'

# Expression fragments used below. chan() returns None if not found yet
# (e.g. before gallery_audio.py has sent its first message), so guard.
VOL = "(op('/project1/audio_vals').chan('volume')[0] if op('/project1/audio_vals').chan('volume') else 0)"
ENG = "(op('/project1/audio_vals').chan('energy')[0] if op('/project1/audio_vals').chan('energy') else 0)"

# --- Rebuild scene (non-destructive — only touches 'salish_audio') -------
# Note: we deliberately do NOT touch a pre-existing 'salish' container
# (the original mycelium.py scene), so both can coexist while testing.
_existing = op('/project1/salish_audio')
if _existing:
    _existing.destroy()

container = project.create(baseCOMP, 'salish_audio')

# === STATIC NETWORK ===
network_noise = container.create(noiseTOP, 'network_noise')
network_noise.par.mono = True
network_noise.par.period = 1.2
network_noise.par.harmon = 4
network_noise.par.rough = 0.6
network_noise.par.seed = 5
network_noise.par.resolutionw = 1280
network_noise.par.resolutionh = 720
network_noise.par.tx = 0
network_noise.par.ty = 0
network_noise.nodeX = 0
network_noise.nodeY = 0

veins = container.create(edgeTOP, 'veins')
veins.inputConnectors[0].connect(network_noise)
veins.nodeX = 200
veins.nodeY = 0

veins_boost = container.create(levelTOP, 'veins_boost')
veins_boost.inputConnectors[0].connect(veins)
veins_boost.par.brightness1 = 5
veins_boost.par.gamma1 = 0.5
veins_boost.nodeX = 400
veins_boost.nodeY = 0

# === ANIMATED PULSE — audio-reactive motion speed ===
pulse_noise = container.create(noiseTOP, 'pulse_noise')
pulse_noise.par.mono = True
pulse_noise.par.period = 0.8
pulse_noise.par.harmon = 2
pulse_noise.par.rough = 0.3
pulse_noise.par.seed = 5
pulse_noise.par.resolutionw = 1280
pulse_noise.par.resolutionh = 720
# Base drift 0.03 (slower than original's 0.1 — stillness baseline)
# + up to 0.35 added by volume. Quiet music = carrier-wave creep.
pulse_noise.par.tx.expr = f'absTime.seconds * (0.03 + ({VOL}) * 0.35)'
pulse_noise.par.ty.expr = f'absTime.seconds * (0.02 + ({VOL}) * 0.28)'
pulse_noise.nodeX = 0
pulse_noise.nodeY = -200

pulse_sharp = container.create(levelTOP, 'pulse_sharp')
pulse_sharp.inputConnectors[0].connect(pulse_noise)
pulse_sharp.par.gamma1 = 2.5
pulse_sharp.par.blacklevel = 0.3
pulse_sharp.nodeX = 200
pulse_sharp.nodeY = -200

pulsing = container.create(compositeTOP, 'pulsing')
pulsing.par.operand = 'multiply'
pulsing.inputConnectors[0].connect(veins_boost)
pulsing.inputConnectors[1].connect(pulse_sharp)
pulsing.nodeX = 400
pulsing.nodeY = -100

# Pulse brightness — audio-reactive
# Baseline 0.8 (barely visible) + up to 5.0 when volume is high
pulse_boost = container.create(levelTOP, 'pulse_boost')
pulse_boost.inputConnectors[0].connect(pulsing)
pulse_boost.par.brightness1.expr = f'0.8 + ({VOL}) * 5.0'
pulse_boost.par.gamma1 = 0.7
pulse_boost.nodeX = 600
pulse_boost.nodeY = -100

# === COLORS ===
# Dim base veins — cool teal, always visible
dim_color = container.create(constantTOP, 'dim_color')
dim_color.par.colorr = 0.01
dim_color.par.colorg = 0.06
dim_color.par.colorb = 0.04
dim_color.par.resolutionw = 1280
dim_color.par.resolutionh = 720
dim_color.nodeX = 400
dim_color.nodeY = 100

dim_veins = container.create(compositeTOP, 'dim_veins')
dim_veins.par.operand = 'multiply'
dim_veins.inputConnectors[0].connect(veins_boost)
dim_veins.inputConnectors[1].connect(dim_color)
dim_veins.nodeX = 600
dim_veins.nodeY = 50

# Bright pulse color — hue shifts with spectral energy:
#   low energy  (bass/warm)  -> teal-green   (0.1, 1.0, 0.5)  (matches original)
#   high energy (treble/air) -> luminous cyan (0.3, 0.9, 1.0)
# Linear blend via energy channel.
bright_color = container.create(constantTOP, 'bright_color')
bright_color.par.colorr.expr = f'0.10 + ({ENG}) * 0.20'  # 0.10 -> 0.30
bright_color.par.colorg.expr = f'1.00 - ({ENG}) * 0.10'  # 1.00 -> 0.90
bright_color.par.colorb.expr = f'0.50 + ({ENG}) * 0.50'  # 0.50 -> 1.00
bright_color.par.resolutionw = 1280
bright_color.par.resolutionh = 720
bright_color.nodeX = 600
bright_color.nodeY = -250

bright_pulse = container.create(compositeTOP, 'bright_pulse')
bright_pulse.par.operand = 'multiply'
bright_pulse.inputConnectors[0].connect(pulse_boost)
bright_pulse.inputConnectors[1].connect(bright_color)
bright_pulse.nodeX = 800
bright_pulse.nodeY = -100

# === FINAL COMBINE ===
combined = container.create(compositeTOP, 'combined')
combined.par.operand = 'add'
combined.inputConnectors[0].connect(dim_veins)
combined.inputConnectors[1].connect(bright_pulse)
combined.nodeX = 1000
combined.nodeY = 0

# Glow — audio-reactive bloom.
# Baseline 5 (subtle) + up to 40 when loud -> full bloom on peaks.
glow = container.create(blurTOP, 'glow')
glow.inputConnectors[0].connect(bright_pulse)
glow.par.size.expr = f'5 + ({VOL}) * 40'
glow.nodeX = 800
glow.nodeY = -250

with_glow = container.create(compositeTOP, 'with_glow')
with_glow.par.operand = 'add'
with_glow.inputConnectors[0].connect(combined)
with_glow.inputConnectors[1].connect(glow)
with_glow.nodeX = 1200
with_glow.nodeY = 0

out = container.create(outTOP, 'output')
out.inputConnectors[0].connect(with_glow)
out.nodeX = 1400
out.nodeY = 0
out.viewer = True
out.display = True

print("mycelium_audio — carrier-wave breathing, audio-reactive brightness/motion/glow/hue")
print(f"  OSC In   : {audio_osc.path}  port={audio_osc.par.port.eval()}")
print(f"  Rename   : {audio_vals.path}  (emits: volume, energy)")
print(f"  Scene    : {container.path}")
print("  NOTE: if 'volume'/'energy' channels are missing, check gallery_audio.py is")
print("        running on the sending machine and pointing at this TD's OSC port.")
