import json
import math

_cache = {"nodes": [], "centroids": {}, "body_hash": None}
_phase = [0.6]
_last_t = [None]

def onSetupParameters(scriptOp): return
def onPulse(par): return

def _parse():
    wc = op("/project1/salish_dreamworld/dream_fetch")
    if wc is None: return False
    raw = wc.text
    if not raw: return False
    js = raw.find("{")
    if js < 0: return False
    body = raw[js:]
    h = hash(body[:200] + body[-100:])
    if h == _cache["body_hash"] and _cache["nodes"]:
        return True
    try: data = json.loads(body)
    except Exception: return False
    nodes = data.get("nodes", [])
    if not nodes: return False
    clusters = {}
    for n in nodes:
        cid = n.get("cluster", -1)
        if cid is None: cid = -1
        clusters.setdefault(cid, []).append(n)
    centroids = {}
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

def _read_bass():
    bn = op("/project1/salish_prisms/bands_norm")
    if bn is not None:
        ch = bn.chan("low")
        if ch is not None:
            return max(0.0, min(1.5, ch[0]))
    return 0.0

def _read_mudra():
    """Pinch detector via direct JSON parse from /project1/MediaPipe/hands.
    Returns 0..1 — 1 means thumb tip touching index tip on hand 1."""
    hands = op("/project1/MediaPipe/hands")
    if hands is None:
        return 0.0
    txt = hands.text
    if not txt:
        return 0.0
    try:
        data = json.loads(txt)
        lms_all = data.get("gestureResults", {}).get("landmarks", [])
        if not lms_all:
            return 0.0
        # Use first detected hand
        lm = lms_all[0]
        if len(lm) < 9:
            return 0.0
        thumb = lm[4]; index_ = lm[8]
        dx = thumb["x"] - index_["x"]
        dy = thumb["y"] - index_["y"]
        dz = thumb.get("z", 0) - index_.get("z", 0)
        d = (dx*dx + dy*dy + dz*dz) ** 0.5
        threshold = 0.05
        raw = max(0.0, min(1.0, 1.0 - (d / threshold)))
        return raw * raw  # quadratic — only firm pinches engage
    except Exception:
        return 0.0


def onCook(scriptOp):
    scriptOp.isTimeSlice = False
    if not _parse(): return
    nodes = _cache["nodes"]
    centroids = _cache["centroids"]
    if not nodes: return

    now = absTime.seconds
    dt = 1.0/60.0 if _last_t[0] is None else max(0.0, min(0.1, now - _last_t[0]))
    _last_t[0] = now

    bass = _read_bass()
    mudra = _read_mudra()

    # Optional bass-driven free speed (used when audio source present)
    if bass > 0.01:
        free_drift = (bass - 0.3) * 2.0
    else:
        free_drift = math.sin(now * 0.35) * 0.18  # subtle idle wobble

    # Two competing forces on phase:
    #   mudra HIGH -> snap toward UNITY_PHASE (collapse to single point)
    #   mudra LOW  -> spring toward MID_PHASE (expanded breathing)
    UNITY_PHASE = -1.6
    MID_PHASE = 0.5
    COLLAPSE_RATE = 12.0   # snap-to-unity speed
    RECOVER_RATE = 2.5     # spring-to-mid speed
    pull_delta = (UNITY_PHASE - _phase[0]) * mudra * COLLAPSE_RATE * dt
    recover_delta = (MID_PHASE - _phase[0]) * (1.0 - mudra) * RECOVER_RATE * dt
    wobble = free_drift * (1.0 - mudra) * dt * 0.4
    _phase[0] += pull_delta + recover_delta + wobble
    _phase[0] = max(-1.6, min(1.2, _phase[0]))

    # Stash for indicator
    op("/project1/salish_dreamworld").store("mudra_now", mudra)

    base_t = (math.sin(_phase[0]) + 1) * 0.5

    scriptOp.clear()
    txc = scriptOp.appendChan("tx"); tyc = scriptOp.appendChan("ty"); tzc = scriptOp.appendChan("tz")
    cr = scriptOp.appendChan("r"); cg = scriptOp.appendChan("g"); cb_ = scriptOp.appendChan("b")
    scriptOp.numSamples = len(nodes)

    SCALE = 100.0
    for i, n in enumerate(nodes):
        t = base_t * base_t * (3 - 2 * base_t)
        cid = n.get("cluster", -1)
        if cid is None: cid = -1
        cent = centroids.get(cid, (0, 0, 0))
        actual = (n.get("x", 0), n.get("y", 0), n.get("z", 0))
        u = 1.0 - t; w1 = 2.0 * u * t; w2 = t * t
        x = w1 * cent[0] + w2 * actual[0]
        y = w1 * cent[1] + w2 * actual[1]
        z = w1 * cent[2] + w2 * actual[2]
        txc[i] = x / SCALE; tyc[i] = y / SCALE; tzc[i] = z / SCALE
        h = n.get("color", "#ffffff").lstrip("#")
        try:
            cr[i] = int(h[0:2], 16) / 255.0
            cg[i] = int(h[2:4], 16) / 255.0
            cb_[i] = int(h[4:6], 16) / 255.0
        except Exception:
            cr[i] = 1; cg[i] = 1; cb_[i] = 1
