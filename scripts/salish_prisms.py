# salish_prisms.py — Salish Sea species cloud, mic-reactive
#
# 100+ camera-facing extruded rectangle "cards" in a 3D noise-displaced
# field. Each card shows a different Salish Sea species portrait from
# images/marine/. Size pulses with bass from the mic — play music through
# speakers and the species school breathes with the beat.
#
# Built 2026-04-23 via TD MCP with Darren. See inline comments for the
# non-obvious gotchas: TD's Geometry COMP needs `instancing=True` as the
# master toggle (NOT `instanceactive`, which is a StrMenu channel picker),
# and per-instance textures need `instancetexs` as a space-separated list
# of TOP paths + `instancetexindex` pointing at a CHOP channel.
#
# Requires: images in /Users/darrenzal/projects/salish-sea-dreaming/images/marine/
# Requires: macOS mic permission granted to TouchDesigner. On first run,
# explicitly set audio_in.par.device to 'BuiltInMicrophoneDevice' (not 'default')
# to trigger the permission prompt.

import os

SPECIES_FOLDER = '/Users/darrenzal/projects/salish-sea-dreaming/images/marine'
N_INSTANCES = 100   # 10x10 grid of species cards

project = op('/project1')

# Rebuild container clean
_existing = op('/project1/salish_prisms')
if _existing:
    _existing.destroy()
c = project.create(baseCOMP, 'salish_prisms')
c.nodeX = 400; c.nodeY = -800

# ==========================================================================
# Audio: mic input -> per-band filter -> RMS -> merge -> lag -> norm
# ==========================================================================
adi = c.create(audiodeviceinCHOP, 'audio_in')
adi.par.active = True
# Explicit device name triggers macOS mic permission prompt on first run.
adi.par.device = 'BuiltInMicrophoneDevice'
adi.nodeX = -600; adi.nodeY = 0

def make_band(name, filter_kind, cutoff_hz, y):
    flt = c.create(audiofilterCHOP, f'{name}_filter')
    flt.inputConnectors[0].connect(adi)
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

bands = c.create(mergeCHOP, 'bands')
bands.inputConnectors[0].connect(low_r)
bands.inputConnectors[1].connect(mid_r)
bands.inputConnectors[2].connect(high_r)
bands.nodeX = 400; bands.nodeY = 0

bands_lag = c.create(lagCHOP, 'bands_lag')
bands_lag.inputConnectors[0].connect(bands)
bands_lag.par.lag1 = 0.1; bands_lag.par.lag2 = 0.15
bands_lag.nodeX = 600; bands_lag.nodeY = 0

bands_norm = c.create(mathCHOP, 'bands_norm')
bands_norm.inputConnectors[0].connect(bands_lag)
bands_norm.par.gain = 40.0   # mic signal needs more gain than file input
bands_norm.nodeX = 800; bands_norm.nodeY = 0

# ==========================================================================
# Positions: grid + noise SOP -> sopToCHOP (tx, ty, tz per instance)
# Texture index: scriptCHOP producing random 0..N_SPECIES-1 per instance
# Merged into one CHOP that drives geo's instanceop
# ==========================================================================
grid = c.create(gridSOP, 'scatter_source')
grid.par.rows = 10; grid.par.cols = 10
grid.par.sizex = 8; grid.par.sizey = 8
grid.nodeX = 400; grid.nodeY = -400

noise_sop = c.create(noiseSOP, 'scatter_noise')
noise_sop.inputConnectors[0].connect(grid)
noise_sop.par.amp = 1.5
noise_sop.par.period = 2.0
noise_sop.nodeX = 600; noise_sop.nodeY = -400

positions = c.create(soptoCHOP, 'positions_chop')
positions.par.sop = noise_sop.path
positions.nodeX = 800; positions.nodeY = -400

# Load all species images + create MFI TOPs, one per image
species_files = sorted([f for f in os.listdir(SPECIES_FOLDER) if f.endswith(('.jpg','.jpeg','.png'))])
top_paths = []
for i, f in enumerate(species_files):
    mfi = c.create(moviefileinTOP, f'species_{i:03d}')
    mfi.par.file = os.path.join(SPECIES_FOLDER, f)
    mfi.nodeX = 1700 + (i % 8) * 120
    mfi.nodeY = -100 - (i // 8) * 100
    top_paths.append(mfi.path)

N_SPECIES = len(species_files)

# tex_idx: per-instance random texture index
tex_idx = c.create(scriptCHOP, 'tex_idx')
tex_idx.nodeX = 800; tex_idx.nodeY = -600
tex_cb = c.create(textDAT, 'tex_idx_cb')
tex_cb.nodeX = 600; tex_cb.nodeY = -600
tex_cb.text = f'''import random
def onSetupParameters(scriptOp): return
def onPulse(par): return
def onCook(scriptOp):
	scriptOp.clear()
	ch = scriptOp.appendChan("texindex")
	scriptOp.numSamples = {N_INSTANCES}
	random.seed(7)
	for i in range({N_INSTANCES}):
		ch[i] = float(random.randint(0, {N_SPECIES - 1}))
'''
tex_idx.par.callbacks = tex_cb.path
tex_idx.cook(force=True)

# Merge positions + texindex into one CHOP
inst_data = c.create(mergeCHOP, 'inst_data')
inst_data.inputConnectors[0].connect(positions)
inst_data.inputConnectors[1].connect(tex_idx)
inst_data.nodeX = 1000; inst_data.nodeY = -400

# ==========================================================================
# Geometry COMP: extruded rectangles (fish-card cards)
# ==========================================================================
geo = c.create(geometryCOMP, 'geo_cubes')
geo.nodeX = 1100; geo.nodeY = -400

for child in list(geo.children): child.destroy()

rect = geo.create(rectangleSOP, 'fish_card')
rect.par.sizex = 0.5; rect.par.sizey = 0.35
# Audio-reactive size: bass pulses the card bigger
rect.par.sizex.expr = "0.4 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.3"
rect.par.sizey.expr = "0.28 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.2"
rect.nodeX = 0

# Small Z extrusion for subtle 3D
ext = geo.create(extrudeSOP, 'fish_extrude')
ext.inputConnectors[0].connect(rect)
ext.par.depthscale = 0.15
ext.par.initextrude.pulse()   # Pulse to initialize extrusion
ext.nodeX = 200

out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(ext)
out_sop.render = True; out_sop.display = True
out_sop.nodeX = 400

# --- Instancing ---
# MASTER TOGGLE (the one switch that actually enables it).
# `instanceactive` is NOT this — it's a StrMenu for per-instance visibility.
geo.par.instancing = True

geo.par.instanceop = inst_data.path
geo.par.instancecountmode = 'manual'
geo.par.numinstances = N_INSTANCES
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'

# Face the camera so textures read cleanly
cam = c.create(cameraCOMP, 'cam1')
cam.par.tz = 6
cam.nodeX = 1100; cam.nodeY = -800
geo.par.instancerottoop = cam.path
geo.par.instancerottoforward = 'posz'

# Per-instance texture: instancetexs is a TOPMulti (space-separated paths)
# instancetexindex = channel name whose value picks which TOP per instance
geo.par.instancetexs = ' '.join(top_paths)
geo.par.instancetexindex = 'texindex'

# Constant material — white base so texture shows clean
mat = c.create(constantMAT, 'cube_mat')
mat.par.colorr = 1.0; mat.par.colorg = 1.0; mat.par.colorb = 1.0
mat.par.colormap = top_paths[0]   # fallback texture if instancetexs fails
mat.nodeX = 1100; mat.nodeY = -200
geo.par.material = mat.path

# ==========================================================================
# Render + Output
# ==========================================================================
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

print(f"salish_prisms — {N_INSTANCES} species cards, {N_SPECIES} unique species loaded")
print(f"  audio: {adi.path} (mic)  bands_norm gain: {bands_norm.par.gain.eval()}")
print(f"  geo: {geo.path}  instancing: {geo.par.instancing.eval()}")
print(f"  output: {out_top.path}")
