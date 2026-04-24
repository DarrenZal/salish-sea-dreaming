# salish_dreamworld.py — live 3D constellation of visitor dreams
# with music-driven unity -> cluster -> individual hierarchy breathing
#
# Pulls the gallery's live /dreams/3d endpoint (UMAP-projected dream
# embeddings with cluster colors + chronological links) and renders
# them as a 3D point cloud that BREATHES through three states:
#
#   unity point  (0,0,0)        — "all my relations" singularity
#       ^
#       | quiet music pulls dreams back toward unity
#       v
#   cluster centroids            — each cluster becomes a single node
#       ^
#       | bass surges push dreams outward
#       v
#   individual dreams            — full UMAP-projected positions
#
# Music DIRECTLY drives direction along this trajectory:
#   - Bass low  -> slow drift backward (toward unity)
#   - Bass high -> surge forward (toward individuation)
# And sphere size pulses with bass.
#
# Architecture:
#   webclientDAT  -> raw JSON response (re-fetched every 30s)
#   scriptCHOP    -> parses JSON, computes cluster centroids, accumulates
#                    music-driven phase, emits (tx, ty, tz, r, g, b) per
#                    dream via quadratic bezier (origin->centroid->actual)
#   geometryCOMP  -> sphere instanced per dream, per-instance color
#   cam + render  -> static camera, slow Y rotation on the cloud
#
# Built 2026-04-23 via TD MCP with Darren. Symbolic of Prav's "carrier wave
# memetics" brief: visitor dreams submitted during the exhibition become
# the very material of Saturday's VJ set, with the music's dynamics
# literally pushing/pulling them through a hierarchy of unity/cluster/individual.
#
# Assumes salish_prisms scene is also built (reads bass from its bands_norm).

DREAM_URL = 'http://37.27.48.12:9000/dreams/3d'
POSITION_SCALE = 100.0
REFRESH_SECONDS = 30

project = op('/project1')

_existing = op('/project1/salish_dreamworld')
if _existing:
    _existing.destroy()
c = project.create(baseCOMP, 'salish_dreamworld')
c.nodeX = 800; c.nodeY = -1200

# ==========================================================================
# HTTP fetch -> Script CHOP -> per-dream samples with music-driven phase
# ==========================================================================
wc = c.create(webclientDAT, 'dream_fetch')
wc.par.url = DREAM_URL
wc.par.reqmethod = 'get'
wc.par.request.pulse()
wc.nodeX = -400; wc.nodeY = 0

sc = c.create(scriptCHOP, 'dream_positions')
sc.nodeX = -200; sc.nodeY = 0
sc.par.timeslice = False   # cooks via input-wire trigger below

sc_cb = c.create(textDAT, 'dream_positions_cb')
sc_cb.nodeX = -400; sc_cb.nodeY = 100
sc_cb.text = f'''import json
import math

_cache = {{"nodes": [], "centroids": {{}}, "body_hash": None}}
_phase = [0.0]
_last_t = [None]

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _parse():
	wc = op("/project1/salish_dreamworld/dream_fetch")
	if wc is None: return False
	raw = wc.text
	if not raw: return False
	# Find JSON body via first "{{" (handles both header'd and streaming responses)
	js = raw.find("{{")
	if js < 0: return False
	body = raw[js:]
	h = hash(body[:200] + body[-100:])
	if h == _cache["body_hash"] and _cache["nodes"]:
		return True
	try: data = json.loads(body)
	except Exception: return False
	nodes = data.get("nodes", [])
	if not nodes: return False
	clusters = {{}}
	for n in nodes:
		cid = n.get("cluster", -1)
		if cid is None: cid = -1
		clusters.setdefault(cid, []).append(n)
	centroids = {{}}
	for cid, ns in clusters.items():
		centroids[cid] = (
			sum(n.get("x", 0) for n in ns) / len(ns),
			sum(n.get("y", 0) for n in ns) / len(ns),
			sum(n.get("z", 0) for n in ns) / len(ns),
		)
	_cache["nodes"] = nodes
	_cache["centroids"] = centroids
	_cache["body_hash"] = h
	return True

def onCook(scriptOp):
	if not _parse(): return  # preserve last-known values on bad fetches
	nodes = _cache["nodes"]
	centroids = _cache["centroids"]
	if not nodes: return

	# Wall-clock delta time
	now = absTime.seconds
	dt = 1.0/60.0 if _last_t[0] is None else max(0.0, min(0.1, now - _last_t[0]))
	_last_t[0] = now

	# Read bass from salish_prisms scene
	bass = 0.0
	bn = op("/project1/salish_prisms/bands_norm")
	if bn is not None:
		ch = bn.chan("low")
		if ch is not None:
			bass = max(0.0, min(1.5, ch[0]))

	# Music directly drives direction:
	#   bass ~0.1 -> speed negative (drifts back toward unity)
	#   bass ~0.3 -> still
	#   bass ~1.0 -> strong forward surge
	speed = (bass - 0.3) * 2.0
	_phase[0] += dt * speed
	_phase[0] = max(-1.2, min(1.2, _phase[0]))   # clamp so it breathes in range

	base_t = (math.sin(_phase[0]) + 1) * 0.5

	scriptOp.clear()
	tx = scriptOp.appendChan("tx"); ty = scriptOp.appendChan("ty"); tz = scriptOp.appendChan("tz")
	cr = scriptOp.appendChan("r"); cg = scriptOp.appendChan("g"); cb_ = scriptOp.appendChan("b")
	scriptOp.numSamples = len(nodes)

	for i, n in enumerate(nodes):
		# Smoothstep for soft ease at extremes
		t = base_t * base_t * (3 - 2 * base_t)
		cid = n.get("cluster", -1)
		if cid is None: cid = -1
		cent = centroids.get(cid, (0, 0, 0))
		actual = (n.get("x", 0), n.get("y", 0), n.get("z", 0))

		# Quadratic Bezier through (origin, centroid, actual):
		#   P(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
		# with P0 = origin (implicit zero term)
		u = 1.0 - t
		w1 = 2.0 * u * t
		w2 = t * t
		x = w1 * cent[0] + w2 * actual[0]
		y = w1 * cent[1] + w2 * actual[1]
		z = w1 * cent[2] + w2 * actual[2]

		tx[i] = x / {POSITION_SCALE}
		ty[i] = y / {POSITION_SCALE}
		tz[i] = z / {POSITION_SCALE}

		h = n.get("color", "#ffffff").lstrip("#")
		try:
			cr[i] = int(h[0:2], 16) / 255.0
			cg[i] = int(h[2:4], 16) / 255.0
			cb_[i] = int(h[4:6], 16) / 255.0
		except Exception:
			cr[i] = 1; cg[i] = 1; cb_[i] = 1
'''
sc.par.callbacks = sc_cb.path

# LFO used ONLY as a per-frame cook trigger (its value is ignored — it
# was formerly the animation source but its `rate` param was not in Hz
# as documented; we now drive phase from bass directly).
lfo = c.create(lfoCHOP, 'anim_tick')
lfo.par.wavetype = 'sin'
lfo.par.rate = 60.0
lfo.nodeX = -400; lfo.nodeY = -100
sc.inputConnectors[0].connect(lfo)

sc.cook(force=True)

# ==========================================================================
# Auto-refresh the fetch every N seconds for live updates
# ==========================================================================
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
'''
ex.par.active = False; ex.par.active = True

# ==========================================================================
# Geometry: sphere per dream, music-reactive size, per-instance color
# ==========================================================================
geo = c.create(geometryCOMP, 'dream_cloud')
geo.nodeX = 200; geo.nodeY = 0
# Slow Y rotation so the cloud has visual motion even when music is quiet
geo.par.ry.expr = 'absTime.seconds * 8'
geo.par.rx = 15

for child in list(geo.children): child.destroy()
sphere = geo.create(sphereSOP, 'dream_sphere')
# Sphere size pulses with bass from salish_prisms scene
sphere.par.radx.expr = "0.07 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.08"
sphere.par.rady.expr = "0.07 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.08"
sphere.par.radz.expr = "0.07 + op('/project1/salish_prisms/bands_norm')['low'][0] * 0.08"
sphere.nodeX = 0

out_sop = geo.create(outSOP, 'out1')
out_sop.inputConnectors[0].connect(sphere)
out_sop.render = True; out_sop.display = True
out_sop.nodeX = 200

# Master instancing toggle (not `instanceactive`)
geo.par.instancing = True
geo.par.instanceop = sc.path
geo.par.instancecountmode = 'oplength'
geo.par.instancetx = 'tx'
geo.par.instancety = 'ty'
geo.par.instancetz = 'tz'

# Per-instance color
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
cam.par.tz = 14
cam.nodeX = 200; cam.nodeY = -200

render = c.create(renderTOP, 'render1')
render.par.geometry = geo.path
render.par.camera = cam.path
render.par.resolutionw = 1280
render.par.resolutionh = 720
render.par.bgcolorr = 0.01; render.par.bgcolorg = 0.015; render.par.bgcolorb = 0.025
render.nodeX = 500; render.nodeY = 0

out_top = c.create(outTOP, 'output')
out_top.inputConnectors[0].connect(render)
out_top.nodeX = 700; out_top.nodeY = 0
out_top.viewer = True
out_top.display = True

print("salish_dreamworld — live dream constellation with music-driven unity/cluster/individual breathing")
print(f"  fetch: {{wc.path}}  url: {DREAM_URL}")
print(f"  phase driven by bass band from salish_prisms/bands_norm")
print(f"  output: {{out_top.path}}")
