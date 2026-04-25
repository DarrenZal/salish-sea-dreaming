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

// Spring rates for the unity-collapse (mudra) and herring-morph (hakini).
// In TD the equivalent code mixed centroid+actual every frame; on the web
// where /dreams/3d already supplies full individual positions, that pulled
// the cloud into its clusters at idle. Here phase 0 = exact original
// position; phase 1 = fully transformed.
const COLLAPSE_RATE   = 12.0;
const RECOVER_RATE    =  2.5;
const HERRING_RATE    =  8.0;
const HERRING_RECOVER =  3.0;

// Per-frame smoothing on fish position lerp.
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
    const { herring, slot } = assignHerringSlots(nodes);
    // Snapshot the original /dreams/3d position on each node — applyTargets
    // mutates n.x/y/z each frame so we can't read it back as the
    // "individual" anchor. Also compute the cloud centroid (mean of
    // actuals) which is the lerp target for mudra collapse — much more
    // visually meaningful than the world origin (0,0,0) since UMAP isn't
    // centered on origin.
    let sumX = 0, sumY = 0, sumZ = 0, count = 0;
    for (const n of nodes) {
        if (n.isSeed) continue;
        n._origX = n.x || 0;
        n._origY = n.y || 0;
        n._origZ = n.z || 0;
        sumX += n._origX; sumY += n._origY; sumZ += n._origZ;
        count++;
    }
    const cloudCenter = count > 0
        ? { x: sumX / count, y: sumY / count, z: sumZ / count }
        : { x: 0, y: 0, z: 0 };

    // Auto-scale herring to fit the cloud's typical extent.
    const cloudR = computeCloudRadius(nodes);
    const HERRING_LOCAL_HALF_LEN = 1.5;  // half of HERRING_LEN
    const scale = cloudR > 0 ? (cloudR / HERRING_LOCAL_HALF_LEN) : 1.0;

    return {
        unityPhase: 0.0,        // 0 = released (idle), 1 = fully collapsed
        herringPhase: 0.0,      // 0 = released, 1 = fully arranged as herring
        cloudCenter,
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

    // unityPhase springs toward mudra value. Collapse fast, release slower
    // (TD's COLLAPSE_RATE / RECOVER_RATE asymmetry).
    if (m > state.unityPhase) {
        state.unityPhase += (m - state.unityPhase) * COLLAPSE_RATE * dt;
    } else {
        state.unityPhase += (m - state.unityPhase) * RECOVER_RATE * dt;
    }
    state.unityPhase = clamp01(state.unityPhase);

    // herringPhase: hakini wakes it; released recovers to 0.
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
 * At idle (unityPhase = 0, herringPhase = 0): returns the snapshotted
 * original position. Identical to the v4 cloud.
 *
 * As mudra rises (unityPhase → 1): linearly lerps toward cloudCenter
 * (the mean of all dream positions — the cloud's "all my relations" point).
 *
 * As hakini rises (herringPhase → 1): linearly lerps the result toward this
 * dream's assigned slot in the procedural herring, scaled to cloud extent.
 */
export function computeFishTarget(state, node) {
    const id = String(node.id);
    const ox = (typeof node._origX === 'number') ? node._origX : (node.x || 0);
    const oy = (typeof node._origY === 'number') ? node._origY : (node.y || 0);
    const oz = (typeof node._origZ === 'number') ? node._origZ : (node.z || 0);
    const cc = state.cloudCenter || { x: 0, y: 0, z: 0 };

    // Mudra collapse: lerp(actual, cloudCenter, unityPhase)
    const u = state.unityPhase;
    let px = ox * (1 - u) + cc.x * u;
    let py = oy * (1 - u) + cc.y * u;
    let pz = oz * (1 - u) + cc.z * u;

    // Hakini herring morph: lerp(current, herring_slot, herringPhase)
    const hp = state.herringPhase;
    if (hp > 0.001) {
        const slotIdx = state.slot[id];
        if (slotIdx !== undefined) {
            const h = state.herring[slotIdx];
            if (h) {
                // Herring-local coords scaled + offset to the cloud center
                // so the herring forms where the dreams are, not at world origin.
                const sx = h.x * state.scale + cc.x;
                const sy = h.y * state.scale + cc.y;
                const sz = h.z * state.scale + cc.z;
                px = px * (1 - hp) + sx * hp;
                py = py * (1 - hp) + sy * hp;
                pz = pz * (1 - hp) + sz * hp;
            }
        }
    }

    return { x: px, y: py, z: pz };
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
