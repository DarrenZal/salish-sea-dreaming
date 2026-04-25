import json
import math
import colorsys

HERRING_LEN = 3.0
HERRING_HEIGHT = 0.7
HERRING_WIDTH = 0.5

_cache = {"nodes": [], "centroids": {}, "body_hash": None,
          "herring": [], "herring_slot": {}}
_phase = [0.5]
_herring_phase = [0.0]
_hakini_smoothed = [0.0]
_last_t = [None]

def onSetupParameters(scriptOp): return
def onPulse(par): return


def _classify_color(hex_str):
    """Return region idx 0..4 from HSL of #rrggbb hex string.
    0=tail/dorsal-stripe, 1=body, 2=belly, 3=eye/dorsal, 4=fin"""
    try:
        h = hex_str.lstrip("#")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
    except Exception:
        return 1
    H, L, S = colorsys.rgb_to_hls(r, g, b)
    H_deg = H * 360.0
    if L < 0.18: return 3
    if L > 0.72 and S < 0.30: return 2
    if (H_deg < 50.0) or (H_deg >= 330.0): return 0
    if 50.0 <= H_deg < 180.0: return 4
    return 1


def _herring_region_points(region, n):
    """Sample n points on a region of the procedural herring.
    Frame: head at +X, tail at -X, dorsal +Y, belly -Y, lateral ±Z."""
    L = HERRING_LEN; H = HERRING_HEIGHT; W = HERRING_WIDTH
    pts = []
    if region == 0:
        # Tail fork (60%) + dorsal-stripe warm band (40%)
        n_tail = max(1, int(n * 0.6))
        n_stripe = max(0, n - n_tail)
        for i in range(n_tail):
            t = i / max(1, n_tail - 1)
            side = 1 if i % 2 == 0 else -1
            x = -1.5 - 0.5 * t
            y = side * (0.05 + 0.4 * t)
            z = (((i * 7) % 11) / 10.0 - 0.5) * 0.05
            pts.append((x, y, z))
        for i in range(n_stripe):
            t = i / max(1, n_stripe - 1)
            x = -1.0 + 1.5 * t
            y = 0.20 + 0.06 * math.sin(t * math.pi)
            z = (((i * 3) % 7) / 6.0 - 0.5) * 0.06
            pts.append((x, y, z))
    elif region == 1:
        # Main body — Fibonacci-stratified ellipsoid surface
        for i in range(n):
            phi = (i * 2.39996323) % (2 * math.pi)  # golden angle
            theta = math.acos(1 - 2 * ((i + 0.5) / n))
            x_norm = math.cos(theta)
            y_base = (H / 2 * 0.85) * math.sin(theta) * math.cos(phi)
            z_base = (W / 2) * math.sin(theta) * math.sin(phi)
            x = x_norm * (L / 2 - 0.3) * 0.85 + 0.25
            pts.append((x, y_base, z_base))
    elif region == 2:
        for i in range(n):
            t = i / max(1, n - 1)
            x = -0.8 + 2.0 * t
            y = -0.20 - 0.10 * math.sin(t * math.pi)
            z = (((i * 5) % 13) / 12.0 - 0.5) * 0.18
            pts.append((x, y, z))
    elif region == 3:
        for i in range(n):
            if i % 3 == 0:
                ang = (i // 3) * 0.4
                x = 1.0 + 0.04 * math.cos(ang)
                y = 0.10 + 0.04 * math.sin(ang)
                z = 0.20 if (i % 6) < 3 else -0.20
            else:
                seg = max(1, n // 3 + 1)
                t = ((i // 3) % seg) / max(1, seg - 1)
                x = -0.5 + 1.5 * t
                y = 0.30
                z = (((i * 11) % 5) / 4.0 - 0.5) * 0.04
            pts.append((x, y, z))
    elif region == 4:
        for i in range(n):
            if i % 2 == 0:
                t = i / max(1, n - 1)
                x = -0.4 + 0.6 * t
                y = 0.30 + 0.15 * math.sin(t * math.pi)
                z = (((i * 7) % 5) / 4.0 - 0.5) * 0.04
            else:
                t = i / max(1, n - 1)
                x = 0.30 + 0.20 * t
                y = -0.15 + 0.04 * math.sin(t * math.pi)
                side = 1 if (i // 2) % 2 == 0 else -1
                z = side * (0.20 + 0.06 * t)
            pts.append((x, y, z))
    return pts


def _build_herring(region_counts):
    points = []
    for r in (0, 1, 2, 3, 4):
        n = region_counts.get(r, 0)
        if n <= 0: continue
        points.extend(_herring_region_points(r, n))
    return points


def _rebuild_herring_assignment(nodes):
    classified = []
    for n in nodes:
        region = _classify_color(n.get("color", "#ffffff"))
        classified.append((region, str(n.get("id", ""))))
    region_counts = {}
    for r, _ in classified:
        region_counts[r] = region_counts.get(r, 0) + 1
    herring_pts = _build_herring(region_counts)
    by_region = {}
    for r, dream_id in classified:
        by_region.setdefault(r, []).append(dream_id)
    for r in by_region:
        by_region[r].sort()
    offsets = {}
    cursor = 0
    for r in (0, 1, 2, 3, 4):
        if region_counts.get(r, 0) > 0:
            offsets[r] = cursor
            cursor += region_counts[r]
    slot = {}
    for r, ids in by_region.items():
        base = offsets.get(r, 0)
        for i, dream_id in enumerate(ids):
            slot[dream_id] = base + i
    _cache["herring"] = herring_pts
    _cache["herring_slot"] = slot


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
    _rebuild_herring_assignment(nodes)
    return True


def _read_bass():
    bn = op("/project1/salish_prisms/bands_norm")
    if bn is not None:
        ch = bn.chan("low")
        if ch is not None:
            return max(0.0, min(1.5, ch[0]))
    return 0.0


def _read_mudra():
    hands = op("/project1/MediaPipe/hands")
    if hands is None: return 0.0
    txt = hands.text
    if not txt: return 0.0
    try:
        data = json.loads(txt)
        lms_all = data.get("gestureResults", {}).get("landmarks", [])
        if not lms_all: return 0.0
        lm = lms_all[0]
        if len(lm) < 9: return 0.0
        thumb = lm[4]; index_ = lm[8]
        dx = thumb["x"] - index_["x"]
        dy = thumb["y"] - index_["y"]
        dz = thumb.get("z", 0) - index_.get("z", 0)
        d = (dx*dx + dy*dy + dz*dz) ** 0.5
        threshold = 0.05
        raw = max(0.0, min(1.0, 1.0 - (d / threshold)))
        return raw * raw
    except Exception:
        return 0.0


def _read_hakini():
    """Two-hand mudra: 5 fingertip pairs touching across hands. Smoothed α=0.25."""
    hands = op("/project1/MediaPipe/hands")
    raw = 0.0
    if hands is not None:
        txt = hands.text
        if txt:
            try:
                data = json.loads(txt)
                lms_all = data.get("gestureResults", {}).get("landmarks", [])
                if len(lms_all) >= 2:
                    h1 = lms_all[0]; h2 = lms_all[1]
                    if len(h1) >= 21 and len(h2) >= 21:
                        tot = 0.0
                        for tip in (4, 8, 12, 16, 20):
                            a = h1[tip]; b = h2[tip]
                            dx = a["x"] - b["x"]
                            dy = a["y"] - b["y"]
                            dz = a.get("z", 0) - b.get("z", 0)
                            tot += (dx*dx + dy*dy + dz*dz) ** 0.5
                        rs = max(0.0, min(1.0, 1.0 - tot / 1.0))
                        raw = rs * rs
            except Exception:
                pass
    _hakini_smoothed[0] = 0.25 * raw + 0.75 * _hakini_smoothed[0]
    return _hakini_smoothed[0]


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
    hakini = _read_hakini()

    if bass > 0.01:
        free_drift = (bass - 0.3) * 2.0
    else:
        free_drift = math.sin(now * 0.35) * 0.18

    UNITY_PHASE = -1.6
    MID_PHASE = 0.5
    COLLAPSE_RATE = 12.0
    RECOVER_RATE = 2.5
    pull_delta = (UNITY_PHASE - _phase[0]) * mudra * COLLAPSE_RATE * dt
    recover_delta = (MID_PHASE - _phase[0]) * (1.0 - mudra) * RECOVER_RATE * dt
    wobble = free_drift * (1.0 - mudra) * dt * 0.4
    _phase[0] += pull_delta + recover_delta + wobble
    _phase[0] = max(-1.6, min(1.2, _phase[0]))

    HERRING_RATE = 8.0
    HERRING_RECOVER = 3.0
    if hakini > 0.05:
        _herring_phase[0] += (1.0 - _herring_phase[0]) * HERRING_RATE * dt * hakini
    else:
        _herring_phase[0] += (0.0 - _herring_phase[0]) * HERRING_RECOVER * dt
    _herring_phase[0] = max(0.0, min(1.0, _herring_phase[0]))

    op("/project1/salish_dreamworld").store("mudra_now", mudra)
    op("/project1/salish_dreamworld").store("hakini_now", hakini)
    op("/project1/salish_dreamworld").store("herring_phase", _herring_phase[0])

    base_t = (math.sin(_phase[0]) + 1) * 0.5

    scriptOp.clear()
    txc = scriptOp.appendChan("tx"); tyc = scriptOp.appendChan("ty"); tzc = scriptOp.appendChan("tz")
    cr = scriptOp.appendChan("r"); cg = scriptOp.appendChan("g"); cb_ = scriptOp.appendChan("b")
    scriptOp.numSamples = len(nodes)

    SCALE = 100.0
    herring = _cache["herring"]
    slot_map = _cache["herring_slot"]
    h_phase = _herring_phase[0]

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
        x = x / SCALE; y = y / SCALE; z = z / SCALE

        if h_phase > 0.001 and herring:
            slot = slot_map.get(str(n.get("id", "")), -1)
            if 0 <= slot < len(herring):
                tx_h, ty_h, tz_h = herring[slot]
                x = x * (1 - h_phase) + tx_h * h_phase
                y = y * (1 - h_phase) + ty_h * h_phase
                z = z * (1 - h_phase) + tz_h * h_phase

        txc[i] = x; tyc[i] = y; tzc[i] = z
        hex_c = n.get("color", "#ffffff").lstrip("#")
        try:
            cr[i] = int(hex_c[0:2], 16) / 255.0
            cg[i] = int(hex_c[2:4], 16) / 255.0
            cb_[i] = int(hex_c[4:6], 16) / 255.0
        except Exception:
            cr[i] = 1; cg[i] = 1; cb_[i] = 1
