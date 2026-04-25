"""
dream_positions_cb_morning.py — UNIFIED morning paste-in for /project1/salish_dreamworld/dream_positions_cb

Drop the entire content of this file into the textDAT `dream_positions_cb`. Then re-bind
the script CHOP's callbacks parameter (toggle empty → cb.path) to force re-import.

Three new behaviors are added on top of the previous (already-shipping) callback,
EACH BEHIND A TOGGLE STORED ON /project1/salish_dreamworld:

    op("/project1/salish_dreamworld").store("hakini_bilateral", 1)  # B-light asymmetric fray
    op("/project1/salish_dreamworld").store("orient_fish", 1)        # per-fish rx/ry/rz from node.dir
    op("/project1/salish_dreamworld").store("swim_wiggle", 1)        # subtle per-fish swim wiggle

All toggles default to 0 (off) — paste this and the scene behaves IDENTICALLY to last
night's checkpoint. Flip toggles one at a time during morning testing.

Pre-requisites for `hakini_bilateral=1`:
    - MediaPipe must be configured for num_hands=4 and num_faces=2 (run preflight_mediapipe.py)
    - Pre-flight gate must have passed (FPS >= 45 with bumps)

Pre-requisites for `orient_fish=1`:
    - dream_cloud must have instance rotation params wired (run wire_orientation_params.py)
    - That sets dream_cloud.par.instancerx = 'rx', instancery = 'ry', instancerz = 'rz'

Kill switch: at any time, store any toggle = 0 to revert that behavior in <1 sec.
"""

import json
import math
import colorsys

# ──────────────────────────────────────────────────────────────────────────────
# Constants — tunable from the textport without re-paste
# ──────────────────────────────────────────────────────────────────────────────
HERRING_LEN = 3.0
HERRING_HEIGHT = 0.7
HERRING_WIDTH = 0.5

# B-light bilateral thresholds (all in MediaPipe normalized [0,1] space)
PAIR_TOUCH_THRESHOLD = 0.07     # per-pair fingertip distance to count as "touching"
SUM_SEAL_THRESHOLD = 0.5         # 5-pair sum below this = Hakini engaged
HYSTERESIS_IN_FRAMES = 6         # ~100ms at 60fps to enter "in-seal"
HYSTERESIS_OUT_FRAMES = 12       # ~200ms at 60fps to enter "released"
ASYMMETRIC_BREAK_FRAMES = 42     # one released ≥700ms before other = fray
MUTUAL_RELEASE_FRAMES = 90       # both released within 1.5s = clean disperse
OCCLUSION_TOLERANCE_FRAMES = 18  # tracking dropout ≤300ms = ignore
# Four-hand school constants
SCHOOL_HERRING_MIN_POINTS = 6        # minimum surface points for tiniest cluster
SCHOOL_HERRING_BASE_LEN = 0.4        # base size for a cluster of 1 dream
SCHOOL_HERRING_PER_DREAM = 0.05      # extra length per additional dream
SCHOOL_RATE = 8.0                    # spring rate when school activating
SCHOOL_RECOVER = 3.0                 # spring rate when school recovering
SCHOOL_TRIGGER_THRESHOLD = 0.05      # school strength threshold to activate
RECENT_SEAL_FRAMES = 30          # ~500ms grace to "restore" seal in 1-hand path  # tracking dropout ≤300ms = ignore
FRAY_HOLD_FRAMES = 180           # 3s before slow dissolve when broken alone

# Orientation — fallback if node.dir is absent
ORIENT_SWIM_AMP_DEG = 5.0        # swim wiggle amplitude in degrees
ORIENT_SWIM_RATE = 2.0           # swim wiggle cycles/sec base

# ──────────────────────────────────────────────────────────────────────────────
# Module-level state
# ──────────────────────────────────────────────────────────────────────────────
_cache = {
    "nodes": [],
    "centroids": {},
    "body_hash": None,
    "herring": [],
    "herring_slot": {},
    "directions": {},  # node_id -> (dx, dy, dz) unit vector
    "cluster_herrings": {},  # cluster_id -> list of (x,y,z) surface points
    "cluster_slot_map": {},  # node_id -> (cluster_id, point_index)
}
_phase = [0.5]
_herring_phase = [0.0]
_school_phase = [0.0]   # 0..1, 4-hand school activation
_hakini_smoothed = [0.0]
_last_t = [None]

# B-light bilateral state — tracked frame-by-frame
# Each person: {"in_seal": bool, "in_seal_frames": int, "out_seal_frames": int,
#               "release_frame": int or None, "occlusion_frames": int}
_person_a = {"in_seal": False, "in_seal_frames": 0, "out_seal_frames": 0,
             "release_frame": None, "occlusion_frames": 0, "last_seal_frame": None}
_person_b = {"in_seal": False, "in_seal_frames": 0, "out_seal_frames": 0,
             "release_frame": None, "occlusion_frames": 0, "last_seal_frame": None}
_frame_counter = [0]
_fray_state = {"active": False, "side": None, "started_frame": None}


def onSetupParameters(scriptOp): return
def onPulse(par): return


# ──────────────────────────────────────────────────────────────────────────────
# Color classifier
# ──────────────────────────────────────────────────────────────────────────────
def _classify_color(hex_str):
    """Return region idx 0..4 from HSL of #rrggbb hex string."""
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


# ──────────────────────────────────────────────────────────────────────────────
# Procedural herring builders
# ──────────────────────────────────────────────────────────────────────────────
def _herring_region_points(region, n):
    L = HERRING_LEN; H = HERRING_HEIGHT; W = HERRING_WIDTH
    pts = []
    if region == 0:
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
        for i in range(n):
            phi = (i * 2.39996323) % (2 * math.pi)
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




def _build_cluster_herring(num_points):
    """Build a small herring shape with `num_points` surface points,
    sized proportional to count. Returns list of (x,y,z) tuples in local frame.
    Same shape proportions as global herring; just smaller."""
    n = max(SCHOOL_HERRING_MIN_POINTS, int(num_points))
    L = SCHOOL_HERRING_BASE_LEN + SCHOOL_HERRING_PER_DREAM * num_points
    H = L * 0.23  # height proportional to length (matches herring's body ratio)
    W = L * 0.17  # width proportional
    # Allocate points across regions in 5 buckets:
    # tail+stripe (15%), body (51%), belly (21%), eye (7%), fins (5%)
    n_tail = max(1, int(n * 0.15))
    n_body = max(1, int(n * 0.51))
    n_belly = max(0, int(n * 0.21))
    n_eye = max(0, int(n * 0.07))
    n_fins = max(0, n - n_tail - n_body - n_belly - n_eye)
    pts = []
    # Tail (V-fork, scaled)
    for i in range(n_tail):
        t = i / max(1, n_tail - 1)
        side = 1 if i % 2 == 0 else -1
        x = -L*0.5 - L*0.17 * t
        y = side * (H*0.07 + H*0.57 * t)
        z = (((i*7) % 11)/10 - 0.5) * W*0.1
        pts.append((x, y, z))
    # Body (Fibonacci ellipsoid)
    import math as _m
    for i in range(n_body):
        phi = (i * 2.39996323) % (2 * _m.pi)
        theta = _m.acos(1 - 2 * ((i + 0.5) / n_body))
        x = _m.cos(theta) * (L*0.4 - 0.05) + L*0.08
        y_b = (H*0.5*0.85) * _m.sin(theta) * _m.cos(phi)
        z_b = (W*0.5) * _m.sin(theta) * _m.sin(phi)
        pts.append((x, y_b, z_b))
    # Belly
    for i in range(n_belly):
        t = i / max(1, n_belly - 1)
        x = -L*0.27 + L*0.67 * t
        y = -H*0.29 - H*0.14 * _m.sin(t * _m.pi)
        z = (((i*5) % 13)/12 - 0.5) * W*0.36
        pts.append((x, y, z))
    # Eye + dorsal stripe
    for i in range(n_eye):
        if i % 3 == 0:
            ang = (i // 3) * 0.4
            x = L*0.33 + L*0.013 * _m.cos(ang)
            y = H*0.14 + H*0.057 * _m.sin(ang)
            z = W*0.4 if (i % 6) < 3 else -W*0.4
        else:
            seg = max(1, n_eye // 3 + 1)
            t = ((i // 3) % seg) / max(1, seg - 1)
            x = -L*0.17 + L*0.5 * t
            y = H*0.43
            z = (((i*11) % 5)/4 - 0.5) * W*0.08
        pts.append((x, y, z))
    # Fins
    for i in range(n_fins):
        if i % 2 == 0:
            t = i / max(1, n_fins - 1)
            x = -L*0.13 + L*0.2 * t
            y = H*0.43 + H*0.21 * _m.sin(t * _m.pi)
            z = (((i*7) % 5)/4 - 0.5) * W*0.08
        else:
            t = i / max(1, n_fins - 1)
            x = L*0.1 + L*0.067 * t
            y = -H*0.21 + H*0.057 * _m.sin(t * _m.pi)
            side = 1 if (i // 2) % 2 == 0 else -1
            z = side * (W*0.4 + W*0.12 * t)
        pts.append((x, y, z))
    return pts[:n]


def _rebuild_cluster_herrings(nodes):
    """Build per-cluster herring point clouds + per-dream slot mapping."""
    # Group dreams by cluster
    by_cluster = {}
    for n in nodes:
        cid = n.get("cluster", -1)
        if cid is None: cid = -1
        by_cluster.setdefault(cid, []).append(n)
    cluster_herrings = {}
    cluster_slot_map = {}
    for cid, dreams in by_cluster.items():
        # Sort dreams by id for determinism
        dreams_sorted = sorted(dreams, key=lambda d: str(d.get("id", "")))
        herring_pts = _build_cluster_herring(len(dreams_sorted))
        cluster_herrings[cid] = herring_pts
        # Map each dream to its point in this cluster's herring
        for i, d in enumerate(dreams_sorted):
            point_idx = i % len(herring_pts)
            cluster_slot_map[str(d.get("id", ""))] = (cid, point_idx)
    _cache["cluster_herrings"] = cluster_herrings
    _cache["cluster_slot_map"] = cluster_slot_map


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
    # Cache directions for orientation toggle
    dirs = {}
    for n in nodes:
        d = n.get("dir")
        nid = str(n.get("id", ""))
        if d and len(d) >= 3:
            dx, dy, dz = float(d[0]), float(d[1]), float(d[2])
            mag = math.sqrt(dx*dx + dy*dy + dz*dz)
            if mag > 0.001:
                dirs[nid] = (dx/mag, dy/mag, dz/mag)
            else:
                dirs[nid] = (1.0, 0.0, 0.0)
        else:
            # Deterministic fallback: hash node id to a unit vector
            h = hash(nid)
            ax = ((h & 0xFF) / 255.0 - 0.5) * 2
            ay = (((h >> 8) & 0xFF) / 255.0 - 0.5) * 2
            az = (((h >> 16) & 0xFF) / 255.0 - 0.5) * 2
            mag = math.sqrt(ax*ax + ay*ay + az*az) or 1.0
            dirs[nid] = (ax/mag, ay/mag, az/mag)
    _cache["directions"] = dirs
    # Build per-cluster herrings for school mode
    _rebuild_cluster_herrings(nodes)


# ──────────────────────────────────────────────────────────────────────────────
# Fetch + parse
# ──────────────────────────────────────────────────────────────────────────────
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
    try:
        data = json.loads(body)
    except Exception:
        return False
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


# ──────────────────────────────────────────────────────────────────────────────
# Sensors — Side-A inputs
# ──────────────────────────────────────────────────────────────────────────────
def _read_bass():
    bn = op("/project1/salish_prisms/bands_norm")
    if bn is not None:
        ch = bn.chan("low")
        if ch is not None:
            return max(0.0, min(1.5, ch[0]))
    return 0.0


def _read_mudra():
    """Single-hand pinch (Chin Mudra)."""
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
    """Two-hand Hakini, basic version (sum across hand[0] and hand[1] only).
    Used when hakini_bilateral toggle is OFF.  Smoothed α=0.25."""
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


# ──────────────────────────────────────────────────────────────────────────────
# B-light: hand→person clustering + bilateral state machine
# ──────────────────────────────────────────────────────────────────────────────
def _cluster_hands_to_persons(landmarks_list, faces_list):
    """Return (person_a_hand_indices, person_b_hand_indices) given list of hand-landmark
    arrays and list of face-landmark arrays. None if too few hands or unsafe attribution."""
    if len(landmarks_list) < 2:
        return None  # Need at least 2 hands

    if len(faces_list) > 2:
        return "DISABLE"  # Too many people — disable fray detection

    # Compute hand centroids in screen-space
    def hand_center(lm):
        if not lm or len(lm) < 9: return (0.5, 0.5)
        # Use wrist (0) as a stable reference
        return (lm[0]["x"], lm[0]["y"])

    hand_centers = [hand_center(lm) for lm in landmarks_list]

    if len(faces_list) == 2:
        # Cluster by Euclidean distance to face centers
        def face_center(face_lm):
            if not face_lm: return (0.5, 0.5)
            xs = [p["x"] for p in face_lm if "x" in p]
            ys = [p["y"] for p in face_lm if "y" in p]
            return (sum(xs)/len(xs) if xs else 0.5, sum(ys)/len(ys) if ys else 0.5)
        f0 = face_center(faces_list[0])
        f1 = face_center(faces_list[1])
        # Assign each hand to nearest face
        a_hands = []; b_hands = []
        for i, hc in enumerate(hand_centers):
            d0 = (hc[0]-f0[0])**2 + (hc[1]-f0[1])**2
            d1 = (hc[0]-f1[0])**2 + (hc[1]-f1[1])**2
            if d0 < d1: a_hands.append(i)
            else: b_hands.append(i)
        if not a_hands or not b_hands:
            return None  # Both hands clustered to same person — ambiguous
        return (a_hands, b_hands)

    # 0–1 face: split frame at x=0.5
    a_hands = []; b_hands = []
    for i, hc in enumerate(hand_centers):
        # Ambiguity zone: 0.45 < x < 0.55 — don't fire
        if 0.45 < hc[0] < 0.55:
            return None
        if hc[0] < 0.5: a_hands.append(i)
        else: b_hands.append(i)
    if not a_hands or not b_hands:
        return None
    return (a_hands, b_hands)


def _person_seal_strength(landmarks_list, person_hands):
    """Return (seal_strength, valid) for one person.
    seal_strength = 0..1 — how 'in seal' the person's hand(s) are with the OTHER person's hand(s).
    Valid = True if measurement is meaningful."""
    # Simplification: take the ONE hand from this person closest to the other person's hand
    # and compute Hakini sum across that pair.
    # This lets two-handed people still trigger via dominant-hand contact.
    return None  # Computed in main onCook below where we have full context


def _update_person_state(person, in_seal_now, frame):
    """Hysteresis state machine for one person."""
    if in_seal_now:
        person["in_seal_frames"] += 1
        person["out_seal_frames"] = 0
        person["last_seal_frame"] = frame  # always update — useful for "recently in seal" check
        if not person["in_seal"] and person["in_seal_frames"] >= HYSTERESIS_IN_FRAMES:
            person["in_seal"] = True
            person["release_frame"] = None
    else:
        person["out_seal_frames"] += 1
        person["in_seal_frames"] = 0
        if person["in_seal"] and person["out_seal_frames"] >= HYSTERESIS_OUT_FRAMES:
            person["in_seal"] = False
            # Note: release_frame for 2-hand path is set by 1-hand path override
            # to avoid double-stamping; here we just transition state.


def _read_hakini_bilateral():
    """Bilateral Hakini detection: tracks two persons separately,
    returns (combined_strength, fray_active, fray_side).
    fray_side: 'a' or 'b' — which side broke the seal first.

    Per-person seal logic:
      - 2+ hands present and touching across midline → both share in_seal.
      - 1 hand only: missing-side person stamped released; remaining-side
        person kept in_seal so fray window can fire.
      - 0 hands: both released after occlusion tolerance.
    """
    hands = op("/project1/MediaPipe/hands")
    if hands is None: return (0.0, False, None)
    txt = hands.text
    if not txt: return (0.0, False, None)
    try:
        data = json.loads(txt)
        lms_all = data.get("gestureResults", {}).get("landmarks", [])
        faces_op = op("/project1/MediaPipe/face_landmarks")
        faces_list = []
        if faces_op:
            faces_txt = faces_op.text or ""
            try:
                faces_data = json.loads(faces_txt)
                fl = faces_data.get("faceLandmarks") or faces_data.get("landmarks") or []
                if isinstance(fl, list): faces_list = fl
            except Exception: pass
    except Exception:
        return (0.0, False, None)

    _frame_counter[0] += 1

    def _fray_check():
        if _person_a["release_frame"] is not None and _person_b["in_seal"]:
            gap = _frame_counter[0] - _person_a["release_frame"]
            if gap > ASYMMETRIC_BREAK_FRAMES:
                return (True, "a")
        if _person_b["release_frame"] is not None and _person_a["in_seal"]:
            gap = _frame_counter[0] - _person_b["release_frame"]
            if gap > ASYMMETRIC_BREAK_FRAMES:
                return (True, "b")
        return (False, None)

    if len(lms_all) == 0:
        _person_a["occlusion_frames"] += 1
        _person_b["occlusion_frames"] += 1
        if _person_a["occlusion_frames"] > OCCLUSION_TOLERANCE_FRAMES:
            _update_person_state(_person_a, False, _frame_counter[0])
        if _person_b["occlusion_frames"] > OCCLUSION_TOLERANCE_FRAMES:
            _update_person_state(_person_b, False, _frame_counter[0])
        _hakini_smoothed[0] *= 0.75
        fa, fs = _fray_check()
        return (_hakini_smoothed[0], fa, fs)

    if len(lms_all) == 1:
        h = lms_all[0]
        if not h or len(h) < 9:
            _hakini_smoothed[0] *= 0.75
            return (_hakini_smoothed[0], False, None)
        x = h[0]["x"]
        if 0.45 < x < 0.55:
            # Ambiguous which person — don't stamp release
            _hakini_smoothed[0] *= 0.75
            return (_hakini_smoothed[0], False, None)
        if x < 0.5:
            # Person A's hand remains; person B is missing.
            _person_a["occlusion_frames"] = 0
            _person_b["occlusion_frames"] += 1
            # Restore A's seal if they were recently sealed (overrides 2-hand release)
            if _person_a["last_seal_frame"] is not None:
                if (_frame_counter[0] - _person_a["last_seal_frame"]) <= RECENT_SEAL_FRAMES:
                    _person_a["in_seal"] = True
                    _person_a["release_frame"] = None
            # Stamp B's release (overwrites any stale 2-hand release stamp)
            if _person_b["last_seal_frame"] is not None and _person_b["release_frame"] is None:
                _person_b["in_seal"] = False
                _person_b["release_frame"] = _frame_counter[0]
            elif _person_b["release_frame"] is not None:
                # Already stamped — keep older to preserve fray timing
                _person_b["in_seal"] = False
        else:
            # Person B's hand remains; person A is missing.
            _person_b["occlusion_frames"] = 0
            _person_a["occlusion_frames"] += 1
            if _person_b["last_seal_frame"] is not None:
                if (_frame_counter[0] - _person_b["last_seal_frame"]) <= RECENT_SEAL_FRAMES:
                    _person_b["in_seal"] = True
                    _person_b["release_frame"] = None
            if _person_a["last_seal_frame"] is not None and _person_a["release_frame"] is None:
                _person_a["in_seal"] = False
                _person_a["release_frame"] = _frame_counter[0]
            elif _person_a["release_frame"] is not None:
                _person_a["in_seal"] = False
        _hakini_smoothed[0] *= 0.75
        fa, fs = _fray_check()
        return (_hakini_smoothed[0], fa, fs)

    # 2+ hands path
    _person_a["occlusion_frames"] = 0
    _person_b["occlusion_frames"] = 0

    cluster = _cluster_hands_to_persons(lms_all, faces_list)
    if cluster is None or cluster == "DISABLE":
        _hakini_smoothed[0] = 0.25 * 0.0 + 0.75 * _hakini_smoothed[0]
        return (_hakini_smoothed[0], False, None)

    a_hands, b_hands = cluster
    best_seal = 0.0
    best_sum = float("inf")
    for ai in a_hands:
        for bi in b_hands:
            ha = lms_all[ai]; hb = lms_all[bi]
            if len(ha) < 21 or len(hb) < 21: continue
            tot = 0.0
            for tip in (4, 8, 12, 16, 20):
                a = ha[tip]; b = hb[tip]
                dx = a["x"] - b["x"]
                dy = a["y"] - b["y"]
                dz = a.get("z", 0) - b.get("z", 0)
                tot += (dx*dx + dy*dy + dz*dz) ** 0.5
            if tot < best_sum:
                best_sum = tot
                rs = max(0.0, min(1.0, 1.0 - tot / 1.0))
                best_seal = rs * rs

    in_seal = (best_sum < SUM_SEAL_THRESHOLD)
    _update_person_state(_person_a, in_seal, _frame_counter[0])
    _update_person_state(_person_b, in_seal, _frame_counter[0])

    # Fray detection
    fray_active = False
    fray_side = None
    if _person_a["release_frame"] is not None and _person_b["in_seal"]:
        gap = _frame_counter[0] - _person_a["release_frame"]
        if gap > ASYMMETRIC_BREAK_FRAMES:
            fray_active = True
            fray_side = 'a'
    elif _person_b["release_frame"] is not None and _person_a["in_seal"]:
        gap = _frame_counter[0] - _person_b["release_frame"]
        if gap > ASYMMETRIC_BREAK_FRAMES:
            fray_active = True
            fray_side = 'b'

    _hakini_smoothed[0] = 0.25 * best_seal + 0.75 * _hakini_smoothed[0]
    return (_hakini_smoothed[0], fray_active, fray_side)


# ──────────────────────────────────────────────────────────────────────────────
# Main onCook
# ──────────────────────────────────────────────────────────────────────────────
def _read_quad_hand_school():
    """4-hand school trigger: requires 4+ hands present AND at least one
    pair among them in Hakini-seal proximity. Returns 0..1 strength.
    Cannot be faked solo — needs two visitors."""
    hands = op("/project1/MediaPipe/hands")
    if hands is None: return 0.0
    txt = hands.text
    if not txt: return 0.0
    try:
        data = json.loads(txt)
        lms = data.get("gestureResults", {}).get("landmarks", [])
    except Exception:
        return 0.0
    if len(lms) < 4: return 0.0
    # Find best Hakini-seal pair across (4 choose 2) = 6 combinations
    best_seal = 0.0
    n = len(lms)
    for i in range(n):
        for j in range(i + 1, n):
            ha = lms[i]; hb = lms[j]
            if len(ha) < 21 or len(hb) < 21: continue
            tot = 0.0
            for tip in (4, 8, 12, 16, 20):
                a = ha[tip]; b = hb[tip]
                dx = a["x"] - b["x"]; dy = a["y"] - b["y"]
                dz = a.get("z", 0) - b.get("z", 0)
                tot += (dx*dx + dy*dy + dz*dz) ** 0.5
            rs = max(0.0, min(1.0, 1.0 - tot / 1.0))
            seal = rs * rs
            if seal > best_seal:
                best_seal = seal
    return best_seal


def onCook(scriptOp):
    scriptOp.isTimeSlice = False
    if not _parse(): return
    nodes = _cache["nodes"]
    centroids = _cache["centroids"]
    if not nodes: return

    now = absTime.seconds
    dt = 1.0/60.0 if _last_t[0] is None else max(0.0, min(0.1, now - _last_t[0]))
    _last_t[0] = now

    # Read toggles (default off)
    sd = op("/project1/salish_dreamworld")
    bilateral = bool(sd.fetch("hakini_bilateral", 0))
    orient = bool(sd.fetch("orient_fish", 0))
    swim = bool(sd.fetch("swim_wiggle", 0))
    school_active = bool(sd.fetch("school_active", 0))

    bass = _read_bass()
    mudra = _read_mudra()

    if bilateral:
        hakini, fray_active, fray_side = _read_hakini_bilateral()
        # Hold herring_phase high while either person is still in_seal OR fray is active —
        # otherwise hakini collapses to 0 and herring disperses before fray can modulate it.
        cb_mod = op("/project1/salish_dreamworld/dream_positions_cb").module
        a_seal = cb_mod._person_a.get("in_seal", False) if hasattr(cb_mod, "_person_a") else False
        b_seal = cb_mod._person_b.get("in_seal", False) if hasattr(cb_mod, "_person_b") else False
        if a_seal or b_seal or fray_active:
            hakini = max(hakini, 0.8)
    else:
        hakini = _read_hakini()
        fray_active = False
        fray_side = None

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

    # School phase (4-hand school trigger)
    if school_active:
        school_strength = _read_quad_hand_school()
    else:
        school_strength = 0.0
    if school_strength > SCHOOL_TRIGGER_THRESHOLD:
        _school_phase[0] += (1.0 - _school_phase[0]) * SCHOOL_RATE * dt * school_strength
    else:
        _school_phase[0] += (0.0 - _school_phase[0]) * SCHOOL_RECOVER * dt
    _school_phase[0] = max(0.0, min(1.0, _school_phase[0]))
    sd.store("school_phase", _school_phase[0])
    sd.store("school_strength", school_strength)

    sd.store("mudra_now", mudra)
    sd.store("hakini_now", hakini)
    sd.store("herring_phase", _herring_phase[0])
    sd.store("fray_active", 1 if fray_active else 0)
    sd.store("fray_side", fray_side or "")

    base_t = (math.sin(_phase[0]) + 1) * 0.5

    scriptOp.clear()
    txc = scriptOp.appendChan("tx"); tyc = scriptOp.appendChan("ty"); tzc = scriptOp.appendChan("tz")
    cr = scriptOp.appendChan("r"); cg = scriptOp.appendChan("g"); cb_ = scriptOp.appendChan("b")
    if orient:
        rxc = scriptOp.appendChan("rx"); ryc = scriptOp.appendChan("ry"); rzc = scriptOp.appendChan("rz")
    scriptOp.numSamples = len(nodes)

    SCALE = 100.0
    herring = _cache["herring"]
    slot_map = _cache["herring_slot"]
    h_phase = _herring_phase[0]
    dirs_cache = _cache["directions"]

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

        dream_id = str(n.get("id", ""))
        # SCHOOL takes priority when active: each cluster's dreams target their cluster's herring
        s_phase = _school_phase[0]
        if s_phase > 0.001 and _cache.get("cluster_herrings"):
            slot_info = _cache["cluster_slot_map"].get(dream_id)
            if slot_info is not None:
                cid, pt_idx = slot_info
                cluster_pts = _cache["cluster_herrings"].get(cid, [])
                cluster_centroid = centroids.get(cid, (0, 0, 0))
                if 0 <= pt_idx < len(cluster_pts):
                    cx, cy, cz = cluster_pts[pt_idx]
                    # Position cluster herring at its centroid (cluster's UMAP center)
                    target_x = cluster_centroid[0] / SCALE + cx
                    target_y = cluster_centroid[1] / SCALE + cy
                    target_z = cluster_centroid[2] / SCALE + cz
                    x = x * (1 - s_phase) + target_x * s_phase
                    y = y * (1 - s_phase) + target_y * s_phase
                    z = z * (1 - s_phase) + target_z * s_phase
        elif h_phase > 0.001 and herring:
            slot = slot_map.get(dream_id, -1)
            fish_h_phase = h_phase
            if bilateral and fray_active and fray_side:
                if 0 <= slot < len(herring):
                    hx = herring[slot][0]
                    fish_side = 'a' if hx < 0 else 'b'
                    if fish_side == fray_side:
                        fish_h_phase = h_phase * max(0.0, 1.0 - (_frame_counter[0] - (_person_a["release_frame"] or _person_b["release_frame"] or _frame_counter[0])) / float(FRAY_HOLD_FRAMES))
            if 0 <= slot < len(herring):
                tx_h, ty_h, tz_h = herring[slot]
                x = x * (1 - fish_h_phase) + tx_h * fish_h_phase
                y = y * (1 - fish_h_phase) + ty_h * fish_h_phase
                z = z * (1 - fish_h_phase) + tz_h * fish_h_phase

        txc[i] = x; tyc[i] = y; tzc[i] = z
        hex_c = n.get("color", "#ffffff").lstrip("#")
        try:
            cr[i] = int(hex_c[0:2], 16) / 255.0
            cg[i] = int(hex_c[2:4], 16) / 255.0
            cb_[i] = int(hex_c[4:6], 16) / 255.0
        except Exception:
            cr[i] = 1; cg[i] = 1; cb_[i] = 1

        if orient:
            d = dirs_cache.get(dream_id, (1.0, 0.0, 0.0))
            # When school_phase is high, blend orientation toward +X (schooling alignment)
            if _school_phase[0] > 0.001:
                school_dir = (1.0, 0.0, 0.0)
                blend = _school_phase[0]
                d = (d[0] * (1 - blend) + school_dir[0] * blend,
                     d[1] * (1 - blend) + school_dir[1] * blend,
                     d[2] * (1 - blend) + school_dir[2] * blend)
            # Convert direction vector to Euler angles (degrees)
            ry_rad = math.atan2(d[0], d[2] if d[2] != 0 else 0.001)
            rx_rad = -math.asin(max(-1.0, min(1.0, d[1])))
            ry_deg = math.degrees(ry_rad)
            rx_deg = math.degrees(rx_rad)
            rz_deg = 0.0
            if swim:
                # Per-fish phase from id hash for varied wiggle
                phase_offset = (hash(dream_id) % 1000) / 1000.0 * 2 * math.pi
                rx_deg += math.sin(now * ORIENT_SWIM_RATE + phase_offset) * ORIENT_SWIM_AMP_DEG
                rz_deg += math.cos(now * ORIENT_SWIM_RATE * 0.7 + phase_offset) * ORIENT_SWIM_AMP_DEG * 0.3
            rxc[i] = rx_deg; ryc[i] = ry_deg; rzc[i] = rz_deg
