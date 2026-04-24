# salish_prisms.py — audio-reactive instanced cube cloud
#
# Aesthetic: 4096 cubes spread as a noise-displaced 3D field. Size and
# color of all cubes modulate with low/mid/high audio bands in real time.
# Kinetic counterpart to the contemplative mycelium_audio scene — gives
# Prav a second distinct aesthetic to mix between for Saturday VJ.
#
# Inspired by Prav's reference tutorial (audio prisms), adapted to TD 2025
# by Darren + Claude via MCP vibe-code 2026-04-23. The tutorial's audio-
# analysis CHOP was renamed/removed in modern TD, so we build the band
# separation manually with audiofilterCHOP + analyzeCHOP per band.
#
# Requirements:
#   - A .wav / .aiff / .flac audio file. Set AUDIO_FILE constant below.
#   - System audio output routed correctly (the scene plays the file
#     through audiodeviceoutCHOP, so you hear what the scene is reacting to).
#
# To use with live mic input instead of a file, replace audiofileinCHOP
# with audiodeviceinCHOP and remove the audio_out wiring.
#
# Non-destructive: only touches /project1/salish_prisms. Coexists with
# mycelium_audio + MediaPipe + salish_hand scenes.

AUDIO_FILE = "/Users/darrenzal/Downloads/Download 2026-04-24T01-00-51-867Z/A3. In 3.wav"

project = op('/project1')

# Rebuild container clean
_existing = op('/project1/salish_prisms')
if _existing:
    _existing.destroy()
c = project.create(baseCOMP, 'salish_prisms')
c.nodeX = 400; c.nodeY = -800

# ==========================================================================
# Audio: file -> speakers -> per-band filter -> RMS analysis -> merge -> norm
# ==========================================================================

af = c.create(audiofileinCHOP, 'audio_file')
af.par.file = AUDIO_FILE
af.par.play = True
af.par.repeat = True
af.nodeX = -600; af.nodeY = 0

ado = c.create(audiodeviceoutCHOP, 'audio_out')
ado.inputConnectors[0].connect(af)
ado.nodeX = -400; ado.nodeY = -100

# Per-band filter chain: low (<250 Hz), mid (bandpass 1kHz), high (>2 kHz)
def make_band(name, filter_kind, cutoff_hz, y):
    flt = c.create(audiofilterCHOP, f'{name}_filter')
    flt.inputConnectors[0].connect(af)
    flt.par.filter = filter_kind
    flt.par.cutofffrequency = cutoff_hz
    flt.nodeX = -400; flt.nodeY = y

    ana = c.create(analyzeCHOP, f'{name}_level')
    ana.inputConnectors[0].connect(flt)
    ana.par.function = 'rmspower'
    ana.nodeX = -200; ana.nodeY = y

    mono = c.create(selectCHOP, f'{name}_mono')
    mono.inputConnectors[0].connect(ana)
    mono.par.channames = 'chan1'
    mono.nodeX = 0; mono.nodeY = y

    renm = c.create(renameCHOP, f'{name}_r')
    renm.inputConnectors[0].connect(mono)
    renm.par.renamefrom = '*'
    renm.par.renameto = name
    renm.nodeX = 200; renm.nodeY = y
    return renm

low_r = make_band('low', 'lowpass', 250, 200)
mid_r = make_band('mid', 'bandpass', 1000, 0)
high_r = make_band('high', 'highpass', 2000, -200)

# Merge into one 3-channel CHOP: low, mid, high
bands = c.create(mergeCHOP, 'bands')
bands.inputConnectors[0].connect(low_r)
bands.inputConnectors[1].connect(mid_r)
bands.inputConnectors[2].connect(high_r)
bands.nodeX = 400; bands.nodeY = 0

# Lag smooth
bands_lag = c.create(lagCHOP, 'bands_lag')
bands_lag.inputConnectors[0].connect(bands)
bands_lag.par.lag1 = 0.1; bands_lag.par.lag2 = 0.15
bands_lag.nodeX = 600; bands_lag.nodeY = 0

# Normalize: bass is naturally much louder than mid/high. Gain to bring
# all three into a comparable [0, ~1] range so expressions can treat
# them symmetrically.
bands_norm = c.create(mathCHOP, 'bands_norm')
bands_norm.inputConnectors[0].connect(bands_lag)
bands_norm.par.gain = 20.0
bands_norm.nodeX = 800; bands_norm.nodeY = 0

# ==========================================================================
# Positions: 64x64 grid SOP + noise SOP displacement -> sopToCHOP -> instances
# ==========================================================================
grid = c.create(gridSOP, 'scatter_source')
grid.par.rows = 64
grid.par.cols = 64
grid.par.sizex = 8
grid.par.sizey = 8
grid.nodeX = 400; grid.nodeY = -400

# Noise SOP displaces grid points along Z (and others) for 3D cloud
noise_sop = c.create(noiseSOP, 'scatter_noise')
noise_sop.inputConnectors[0].connect(grid)
noise_sop.par.amp = 1.5
noise_sop.par.period = 2.0
noise_sop.nodeX = 600; noise_sop.nodeY = -400

# sopToCHOP: 4096 samples of (tx, ty, tz) -- one per grid point
positions = c.create(soptoCHOP, 'positions_chop')
positions.par.sop = noise_sop.path
positions.nodeX = 800; positions.nodeY = -400

# ==========================================================================
# Geometry COMP with instancing
# ==========================================================================
geo = c.create(geometryCOMP, 'geo_cubes')
geo.nodeX = 1100; geo.nodeY = -400

# Internal: a single tiny box that gets instanced 4096 times
for child in list(geo.children): child.destroy()
box = geo.create(boxSOP, 'box1')
# Box size is audio-reactive: low band drives pulse
box.par.sizex.expr = "0.012 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.02"
box.par.sizey.expr = "0.012 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.02"
box.par.sizez.expr = "0.012 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.02"
box.nodeX = 0

out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(box)
out_sop.render = True; out_sop.display = True
out_sop.nodeX = 200

# THE master instancing toggle — this is the ONE SWITCH that actually
# enables instanced rendering. `instanceactive` is NOT the enable toggle;
# it's a StrMenu that selects a per-instance-visibility CHOP channel.
# Setting `instanceactive = True` (string) silently does nothing.
geo.par.instancing = True

geo.par.instanceop = positions.path
geo.par.instancecountmode = 'manual'   # oplength was flaky for us; manual is reliable
geo.par.numinstances = 4096
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'

# Constant material with audio-reactive RGB
mat = c.create(constantMAT, 'cube_mat')
mat.par.colorr.expr = "0.3 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.4"
mat.par.colorg.expr = "0.5 + op('/project1/salish_prisms/bands_norm')['mid'][0] * 3.0"
mat.par.colorb.expr = "0.6 + op('/project1/salish_prisms/bands_norm')['high'][0] * 5.0"
mat.nodeX = 1100; mat.nodeY = -200
geo.par.material = mat.path

# ==========================================================================
# Camera + Render + Output
# ==========================================================================
cam = c.create(cameraCOMP, 'cam1')
cam.par.tz = 6
cam.nodeX = 1100; cam.nodeY = -600

render = c.create(renderTOP, 'render1')
render.par.geometry = geo.path
render.par.camera = cam.path
render.par.resolutionw = 1280
render.par.resolutionh = 720
render.nodeX = 1400; render.nodeY = -400

out_top = c.create(outTOP, 'output')
out_top.inputConnectors[0].connect(render)
out_top.nodeX = 1600; out_top.nodeY = -400
out_top.viewer = True
out_top.display = True

print("salish_prisms — audio-reactive 4096-cube cloud")
print(f"  audio     : {af.path}  (file: {af.par.file.eval()})")
print(f"  bands     : {bands_norm.path}  (low, mid, high — gain {bands_norm.par.gain.eval()}x)")
print(f"  geometry  : {geo.path}  (instancing ON, {geo.par.numinstances.eval()} instances)")
print(f"  material  : {mat.path}  (audio-reactive RGB)")
print(f"  output    : {out_top.path}")
