# salish_dreamworld.py — live 3D constellation of visitor dreams
#
# Pulls the gallery's live /dreams/3d endpoint (UMAP-projected dream
# embeddings with cluster colors + chronological links) and renders
# them as a slowly rotating 3D cloud of colored spheres in TD.
#
# Built 2026-04-23 via TD MCP with Darren. The web backend already does
# the hard work: text embedding -> UMAP projection to 3D -> cluster
# labeling -> colors -> stored in SQLite -> served via HTTP JSON. TD
# just fetches the JSON every 30s and renders it.
#
# Visual feel: Prav's "carrier wave memetics" — every dream submitted
# during the exhibition becomes a point floating in Saturday's VJ layer.
# Audio-reactive (reads from salish_prisms/bands_norm — assumes that
# scene is also built for mic/audio reactivity).
#
# Endpoint: http://37.27.48.12:9000/dreams/3d
#   - returns nodes[] with {x,y,z,color(hex),cluster,text,submitted_at}
#   - positions in UMAP scale (~±200), scaled down 1/100 here to fit ±3
#   - links[] are chronological (node[i] -> node[i+1])
#
# Non-destructive — only touches /project1/salish_dreamworld.

DREAM_URL = 'http://37.27.48.12:9000/dreams/3d'
POSITION_SCALE = 100.0   # divide raw x/y/z by this (UMAP scale is ~±200)
REFRESH_SECONDS = 30     # re-fetch every N seconds for live updates

project = op('/project1')

_existing = op('/project1/salish_dreamworld')
if _existing:
    _existing.destroy()
c = project.create(baseCOMP, 'salish_dreamworld')
c.nodeX = 800; c.nodeY = -1200

# ==========================================================================
# HTTP fetch -> JSON parse -> per-dream CHOP samples (tx,ty,tz,r,g,b)
# ==========================================================================
wc = c.create(webclientDAT, 'dream_fetch')
wc.par.url = DREAM_URL
wc.par.reqmethod = 'get'
wc.par.request.pulse()
wc.nodeX = -400; wc.nodeY = 0

sc = c.create(scriptCHOP, 'dream_positions')
sc.nodeX = -200; sc.nodeY = 0
sc.par.timeslice = False

sc_cb = c.create(textDAT, 'dream_positions_cb')
sc_cb.nodeX = -400; sc_cb.nodeY = 100
sc_cb.text = f'''import json

def onSetupParameters(scriptOp): return
def onPulse(par): return

def onCook(scriptOp):
	scriptOp.clear()
	wc = op("/project1/salish_dreamworld/dream_fetch")
	if wc is None: return
	raw = wc.text
	if not raw: return
	bs = raw.find("\\r\\n\\r\\n")
	body = raw[bs+4:] if bs > 0 else raw
	try: data = json.loads(body)
	except Exception: return
	nodes = data.get("nodes", [])
	if not nodes: return
	tx = scriptOp.appendChan("tx"); ty = scriptOp.appendChan("ty"); tz = scriptOp.appendChan("tz")
	cr = scriptOp.appendChan("r"); cg = scriptOp.appendChan("g"); cb_ = scriptOp.appendChan("b")
	scriptOp.numSamples = len(nodes)
	for i, n in enumerate(nodes):
		tx[i] = n.get("x", 0) / {POSITION_SCALE}
		ty[i] = n.get("y", 0) / {POSITION_SCALE}
		tz[i] = n.get("z", 0) / {POSITION_SCALE}
		h = n.get("color", "#ffffff").lstrip("#")
		try:
			cr[i] = int(h[0:2], 16) / 255.0
			cg[i] = int(h[2:4], 16) / 255.0
			cb_[i] = int(h[4:6], 16) / 255.0
		except Exception:
			cr[i] = 1; cg[i] = 1; cb_[i] = 1
'''
sc.par.callbacks = sc_cb.path
sc.cook(force=True)

# Auto-refresh every N seconds
ex = c.create(executeDAT, 'refresh_exec')
ex.par.framestart = True
ex.par.active = True
ex.nodeX = -400; ex.nodeY = 200
ex.text = f'''_last_fetch = [0.0]

def onStart(): pass
def onCreate(): pass
def onExit(): pass

def onFrameStart(frame):
	import time
	now = time.time()
	if now - _last_fetch[0] > {REFRESH_SECONDS}:
		_last_fetch[0] = now
		wc = op("/project1/salish_dreamworld/dream_fetch")
		if wc is not None:
			wc.par.request.pulse()
		dp = op("/project1/salish_dreamworld/dream_positions")
		if dp is not None:
			dp.cook(force=True)
'''
# Toggle active to force re-register of callbacks
ex.par.active = False; ex.par.active = True

# ==========================================================================
# Geometry: instanced sphere per dream, per-instance color from CHOP
# ==========================================================================
geo = c.create(geometryCOMP, 'dream_cloud')
geo.nodeX = 200; geo.nodeY = 0
# Slow rotation so the cloud breathes like Refik Anadol
geo.par.ry.expr = 'absTime.seconds * 8'   # 8 deg/sec
geo.par.rx = 15

for child in list(geo.children): child.destroy()
sphere = geo.create(sphereSOP, 'dream_sphere')
# Audio-reactive sphere size — pulses with bass from salish_prisms scene
sphere.par.radx.expr = "0.08 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.05"
sphere.par.rady.expr = "0.08 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.05"
sphere.par.radz.expr = "0.08 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.05"
sphere.nodeX = 0

out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(sphere)
out_sop.render = True; out_sop.display = True
out_sop.nodeX = 200

# Instancing (master toggle is `instancing`, not `instanceactive`)
geo.par.instancing = True
geo.par.instanceop = sc.path
geo.par.instancecountmode = 'oplength'  # auto-match CHOP sample count
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'

# Per-instance color (cluster-based, from JSON hex)
geo.par.instancecolormode = 'replace'
geo.par.instancer = 'r'
geo.par.instanceg = 'g'
geo.par.instanceb = 'b'

mat = c.create(constantMAT, 'dream_mat')
mat.par.colorr = 1.0; mat.par.colorg = 1.0; mat.par.colorb = 1.0
mat.par.applypointcolor = True
mat.nodeX = 200; mat.nodeY = 200
geo.par.material = mat.path

# ==========================================================================
# Camera + Render
# ==========================================================================
cam = c.create(cameraCOMP, 'cam1')
cam.par.tz = 14   # far enough to see all ±3 unit extent
cam.nodeX = 200; cam.nodeY = -200

render = c.create(renderTOP, 'render1')
render.par.geometry = geo.path
render.par.camera = cam.path
render.par.resolutionw = 1280
render.par.resolutionh = 720
render.par.bgcolorr = 0.01; render.par.bgcolorg = 0.015; render.par.bgcolorb = 0.025   # deep ocean near-black
render.nodeX = 500; render.nodeY = 0

out_top = c.create(outTOP, 'output')
out_top.inputConnectors[0].connect(render)
out_top.nodeX = 700; out_top.nodeY = 0
out_top.viewer = True
out_top.display = True

print("salish_dreamworld — live visitor-dream constellation")
print(f"  fetch: {wc.path}  url: {DREAM_URL}  refresh: every {REFRESH_SECONDS}s")
print(f"  positions: {sc.path}  samples: {sc.numSamples}")
print(f"  cloud: {geo.path}  rotating at 8 deg/sec")
print(f"  output: {out_top.path}")
