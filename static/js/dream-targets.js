// dream-targets.js — port of the per-frame phase + per-fish target lerp from
// dream_positions_cb_morning.py's onCook(scriptOp).
//
// Two phase variables drive the visual:
//
//   phase ∈ [-1.6, +1.2]
//     mudra pulls toward UNITY_PHASE = -1.6 (cloud collapses to one point)
//     released drifts back toward MID_PHASE = +0.5 (settled cloud)
//     base_t = (sin(phase) + 1) / 2   ← weight between centroid and actual
//
//   herring_phase ∈ [0, 1]
//     hakini pulls toward 1 (cloud morphs into procedural herring shape)
//     released drifts back toward 0
//
// At herring_phase = 1 a fish sits at its assigned slot in the herring point
// cloud; at 0 it sits where base_t put it (centroid ↔ actual bezier).

import { assignHerringSlots } from './herring-builder.js';

// Match Python constants exactly. (1/60-second-tick budget: COLLAPSE_RATE
// of 12 means full mudra = phase moves ~0.2 toward UNITY_PHASE per frame.)
const UNITY_PHASE     = -1.6;
const MID_PHASE       =  0.5;
const COLLAPSE_RATE   = 12.0;
const RECOVER_RATE    =  2.5;
const HERRING_RATE    =  8.0;
const HERRING_RECOVER =  3.0;

// Match TD's per-frame smoothing on fish position lerp.
const SMOOTHING_PER_SEC = 6.0;

/**
 * Create / reset state. Caller keeps one instance for the page lifetime.
 *
 *   nodes:     full /dreams/3d node array (with x, y, z, color, cluster, ...)
 *   centroids: { cluster_id -> {x, y, z} } per-cluster mean
 *   herring:   per-region surface points (TD frame, before scaling)
 *   slot:      { dream_id -> integer index into herring[] }
 *   scale:     factor to map herring-local coords into cloud-coord space
 */
export function createTargetState(nodes) {
    const centroids = computeClusterCentroids(nodes);
    const { herring, slot } = assignHerringSlots(nodes);
    // Auto-scale: pick a herring length that roughly fills the cloud's
    // largest extent. Python uses HERRING_LEN = 3.0 in TD-world units; the
    // browser cloud is in the original UMAP/scaled coords. Compute the
    // cloud's max radius and scale the herring so its length matches.
    const cloudR = computeCloudRadius(nodes);
    const HERRING_LOCAL_HALF_LEN = 1.5;  // half of HERRING_LEN
    const scale = cloudR > 0 ? (cloudR / HERRING_LOCAL_HALF_LEN) : 1.0;
    return {
        phase: MID_PHASE,
        herringPhase: 0.0,
        centroids,
        herring,
        slot,
        scale,
        lastTickT: null,
    };
}

/**
 * Advance phases one tick using current gesture readings. Call every frame.
 *
 *   gestures: { mudra, hakini } from mudra-detector.js
 *   dtSec:    seconds since last tick (clamp 0..0.1 like TD)
 */
export function tickPhases(state, gestures, dtSec) {
    const dt = Math.max(0.0, Math.min(0.1, dtSec));
    const m = clamp01(gestures.mudra || 0);
    const h = clamp01(gestures.hakini || 0);

    // Phase: mudra collapses toward UNITY, released recovers toward MID.
    const pullDelta    = (UNITY_PHASE - state.phase) * m * COLLAPSE_RATE * dt;
    const recoverDelta = (MID_PHASE   - state.phase) * (1 - m) * RECOVER_RATE * dt;
    state.phase = clamp(state.phase + pullDelta + recoverDelta, UNITY_PHASE, 1.2);

    // Herring phase: hakini wakes it; released recovers to 0.
    if (h > 0.05) {
        state.herringPhase += (1 - state.herringPhase) * HERRING_RATE * dt * h;
    } else {
        state.herringPhase += (0 - state.herringPhase) * HERRING_RECOVER * dt;
    }
    state.herringPhase = clamp01(state.herringPhase);
}

/**
 * Compute a single fish's target position. Pure function — does not mutate.
 *
 * Algorithm (mirrors `onCook`):
 *   1. base_t   = (sin(phase) + 1) / 2     — phase position 0..1
 *   2. unity_t  = smoothstep(base_t)       — eased
 *   3. unity_lerp = bezier(centroid, actual, unity_t)   ← collapse → individual
 *   4. herring_target = scaled_herring_slot[i]
 *   5. final = lerp(unity_lerp, herring_target, herring_phase)
 */
export function computeFishTarget(state, node) {
    const id = String(node.id);
    const cid = (node.cluster === null || node.cluster === undefined) ? -1 : node.cluster;
    const cent = state.centroids[cid] || { x: 0, y: 0, z: 0 };
    const actual = { x: node.x || 0, y: node.y || 0, z: node.z || 0 };

    const baseT = (Math.sin(state.phase) + 1) * 0.5;
    // Smoothstep + Bezier weighting: w1 = 2u·t, w2 = t·t — same as TD callback.
    const t = baseT * baseT * (3 - 2 * baseT);
    const u = 1 - t;
    const w1 = 2 * u * t;
    const w2 = t * t;
    const unityX = w1 * cent.x + w2 * actual.x;
    const unityY = w1 * cent.y + w2 * actual.y;
    const unityZ = w1 * cent.z + w2 * actual.z;

    if (state.herringPhase <= 0.001) {
        return { x: unityX, y: unityY, z: unityZ };
    }

    // Apply herring shape weighted by herring_phase.
    const slot = state.slot[id];
    if (slot === undefined) {
        return { x: unityX, y: unityY, z: unityZ };
    }
    const hp = state.herring[slot];
    if (!hp) {
        return { x: unityX, y: unityY, z: unityZ };
    }
    const sx = hp.x * state.scale;
    const sy = hp.y * state.scale;
    const sz = hp.z * state.scale;

    const hPhase = state.herringPhase;
    return {
        x: unityX * (1 - hPhase) + sx * hPhase,
        y: unityY * (1 - hPhase) + sy * hPhase,
        z: unityZ * (1 - hPhase) + sz * hPhase,
    };
}

/**
 * Per-frame: lerp every node toward its target by SMOOTHING_PER_SEC.
 *
 * 3d-force-graph is initialized with cooldownTicks=0 in dreamworld.html, so
 * its physics simulation doesn't tick and node.x/y/z writes don't propagate
 * to the rendered THREE.Group positions. The IIFE in dreamworld.html keeps
 * a `fishMap` (id → THREE.Group) and exposes it on window._dw.fishMap; we
 * write group.position there directly.
 *
 * We also update node.x/y/z so any other code that reads them (deep-link
 * camera focus, link endpoint rendering, etc.) stays consistent.
 */
export function applyTargetsToNodes(state, nodes, dtSec, fishMap) {
    const dt = Math.max(0.0, Math.min(0.1, dtSec));
    const k = 1.0 - Math.exp(-SMOOTHING_PER_SEC * dt);
    for (const n of nodes) {
        if (n.isSeed) continue; // leave seed prompts alone
        const target = computeFishTarget(state, n);
        const cx = (typeof n.x === 'number') ? n.x : 0;
        const cy = (typeof n.y === 'number') ? n.y : 0;
        const cz = (typeof n.z === 'number') ? n.z : 0;
        const nx = cx + (target.x - cx) * k;
        const ny = cy + (target.y - cy) * k;
        const nz = cz + (target.z - cz) * k;
        n.x = nx; n.y = ny; n.z = nz;
        n.fx = nx; n.fy = ny; n.fz = nz;
        // Direct THREE.Group access via fishMap (set by createFish).
        const grp = fishMap && fishMap[n.id];
        if (grp && grp.position && typeof grp.position.set === 'function') {
            grp.position.set(nx, ny, nz);
        } else if (n.__threeObj && n.__threeObj.position) {
            // Fallback: 3d-force-graph stores back-ref on __threeObj.
            n.__threeObj.position.set(nx, ny, nz);
        }
    }
}

// Internal ───────────────────────────────────────────────────────────────────

function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }
function clamp(x, lo, hi) { return x < lo ? lo : (x > hi ? hi : x); }

function computeClusterCentroids(nodes) {
    const sums = {};
    const counts = {};
    for (const n of nodes) {
        if (n.isSeed) continue;
        const cid = (n.cluster === null || n.cluster === undefined) ? -1 : n.cluster;
        if (!sums[cid]) { sums[cid] = { x: 0, y: 0, z: 0 }; counts[cid] = 0; }
        sums[cid].x += (n.x || 0);
        sums[cid].y += (n.y || 0);
        sums[cid].z += (n.z || 0);
        counts[cid] += 1;
    }
    const centroids = {};
    for (const cid of Object.keys(sums)) {
        const c = counts[cid] || 1;
        centroids[cid] = {
            x: sums[cid].x / c,
            y: sums[cid].y / c,
            z: sums[cid].z / c,
        };
    }
    return centroids;
}

function computeCloudRadius(nodes) {
    let maxR = 0;
    for (const n of nodes) {
        if (n.isSeed) continue;
        const r = Math.sqrt((n.x || 0) ** 2 + (n.y || 0) ** 2 + (n.z || 0) ** 2);
        if (r > maxR) maxR = r;
    }
    return maxR;
}
