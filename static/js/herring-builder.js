// herring-builder.js — port of dream_positions_cb_morning.py procedural herring
// shape functions. Pure functions, no DOM. Output bit-for-bit matches the TD
// callback so visual A/B works against the gallery wall.
//
// Coords from this module are in TD's "herring local" frame:
//   length axis  = X ∈ [-1.5, +1.5]    (HERRING_LEN/2)
//   height axis  = Y ∈ [-0.35, +0.35]  (HERRING_HEIGHT/2)
//   width axis   = Z ∈ [-0.25, +0.25]  (HERRING_WIDTH/2)
// Caller scales this to fit the cloud's actual extent.
//
// Color → region mapping (Python `_classify_color`):
//   region 0 = warm  (tail + dorsal stripe)
//   region 1 = body  (ellipsoidal core)
//   region 2 = belly (light, low saturation)
//   region 3 = dark  (eye + dorsal cap)
//   region 4 = green (fins)

export const HERRING_LEN    = 3.0;
export const HERRING_HEIGHT = 0.7;
export const HERRING_WIDTH  = 0.5;

// Public ─────────────────────────────────────────────────────────────────────

/**
 * Map a #rrggbb hex string to one of the 5 herring regions.
 * Faithful port of Python `_classify_color` using rgb_to_hls semantics.
 */
export function classifyColor(hexStr) {
    let r, g, b;
    try {
        const h = (hexStr || '').replace(/^#/, '');
        r = parseInt(h.slice(0, 2), 16) / 255.0;
        g = parseInt(h.slice(2, 4), 16) / 255.0;
        b = parseInt(h.slice(4, 6), 16) / 255.0;
        if (!isFinite(r) || !isFinite(g) || !isFinite(b)) return 1;
    } catch (_) {
        return 1;
    }
    const { h: H, l: L, s: S } = rgbToHls(r, g, b);
    const Hdeg = H * 360.0;
    if (L < 0.18) return 3;
    if (L > 0.72 && S < 0.30) return 2;
    if (Hdeg < 50.0 || Hdeg >= 330.0) return 0;
    if (Hdeg >= 50.0 && Hdeg < 180.0) return 4;
    return 1;
}

/**
 * Generate `n` surface points for region `region` of the herring.
 * Returns an array of {x, y, z} in herring-local coordinates.
 */
export function herringRegionPoints(region, n) {
    const L = HERRING_LEN, H = HERRING_HEIGHT, W = HERRING_WIDTH;
    const pts = [];

    if (region === 0) {
        // Tail (60%) + dorsal stripe (40%)
        const nTail = Math.max(1, Math.floor(n * 0.6));
        const nStripe = Math.max(0, n - nTail);
        for (let i = 0; i < nTail; i++) {
            const t = i / Math.max(1, nTail - 1);
            const side = (i % 2 === 0) ? 1 : -1;
            const x = -1.5 - 0.5 * t;
            const y = side * (0.05 + 0.4 * t);
            const z = (((i * 7) % 11) / 10.0 - 0.5) * 0.05;
            pts.push({ x, y, z });
        }
        for (let i = 0; i < nStripe; i++) {
            const t = i / Math.max(1, nStripe - 1);
            const x = -1.0 + 1.5 * t;
            const y = 0.20 + 0.06 * Math.sin(t * Math.PI);
            const z = (((i * 3) % 7) / 6.0 - 0.5) * 0.06;
            pts.push({ x, y, z });
        }
    } else if (region === 1) {
        // Body — Fibonacci-spiral ellipsoid
        for (let i = 0; i < n; i++) {
            const phi = (i * 2.39996323) % (2 * Math.PI);
            const theta = Math.acos(1 - 2 * ((i + 0.5) / n));
            const xNorm = Math.cos(theta);
            const yBase = (H / 2 * 0.85) * Math.sin(theta) * Math.cos(phi);
            const zBase = (W / 2) * Math.sin(theta) * Math.sin(phi);
            const x = xNorm * (L / 2 - 0.3) * 0.85 + 0.25;
            pts.push({ x, y: yBase, z: zBase });
        }
    } else if (region === 2) {
        // Belly
        for (let i = 0; i < n; i++) {
            const t = i / Math.max(1, n - 1);
            const x = -0.8 + 2.0 * t;
            const y = -0.20 - 0.10 * Math.sin(t * Math.PI);
            const z = (((i * 5) % 13) / 12.0 - 0.5) * 0.18;
            pts.push({ x, y, z });
        }
    } else if (region === 3) {
        // Dark — eye cluster + thin dorsal cap
        for (let i = 0; i < n; i++) {
            if (i % 3 === 0) {
                const ang = (Math.floor(i / 3)) * 0.4;
                const x = 1.0 + 0.04 * Math.cos(ang);
                const y = 0.10 + 0.04 * Math.sin(ang);
                const z = (i % 6) < 3 ? 0.20 : -0.20;
                pts.push({ x, y, z });
            } else {
                const seg = Math.max(1, Math.floor(n / 3) + 1);
                const t = (Math.floor(i / 3) % seg) / Math.max(1, seg - 1);
                const x = -0.5 + 1.5 * t;
                const y = 0.30;
                const z = (((i * 11) % 5) / 4.0 - 0.5) * 0.04;
                pts.push({ x, y, z });
            }
        }
    } else if (region === 4) {
        // Greens — fins
        for (let i = 0; i < n; i++) {
            if (i % 2 === 0) {
                const t = i / Math.max(1, n - 1);
                const x = -0.4 + 0.6 * t;
                const y = 0.30 + 0.15 * Math.sin(t * Math.PI);
                const z = (((i * 7) % 5) / 4.0 - 0.5) * 0.04;
                pts.push({ x, y, z });
            } else {
                const t = i / Math.max(1, n - 1);
                const x = 0.30 + 0.20 * t;
                const y = -0.15 + 0.04 * Math.sin(t * Math.PI);
                const side = (Math.floor(i / 2) % 2 === 0) ? 1 : -1;
                const z = side * (0.20 + 0.06 * t);
                pts.push({ x, y, z });
            }
        }
    }
    return pts;
}

/**
 * Build the full herring point cloud given counts per region.
 * Concatenated in region order 0..4.
 */
export function buildHerring(regionCounts) {
    const points = [];
    for (const r of [0, 1, 2, 3, 4]) {
        const n = regionCounts[r] || 0;
        if (n <= 0) continue;
        for (const p of herringRegionPoints(r, n)) points.push(p);
    }
    return points;
}

/**
 * Given an array of {id, color} dream nodes, return:
 *   - herring: full point array in herring-local coords
 *   - slot: { dreamId -> integer slot in herring[] }
 *   - regionCounts: { region -> count }
 *
 * Faithful port of Python `_rebuild_herring_assignment`. Within each region,
 * dream IDs are sorted lexicographically — same deterministic mapping as TD.
 */
export function assignHerringSlots(nodes) {
    const classified = nodes.map(n => ({
        region: classifyColor(n.color || '#ffffff'),
        id: String(n.id),
    }));
    const regionCounts = {};
    for (const { region } of classified) {
        regionCounts[region] = (regionCounts[region] || 0) + 1;
    }
    const herring = buildHerring(regionCounts);

    const byRegion = {};
    for (const c of classified) {
        if (!byRegion[c.region]) byRegion[c.region] = [];
        byRegion[c.region].push(c.id);
    }
    for (const r of Object.keys(byRegion)) byRegion[r].sort();

    const offsets = {};
    let cursor = 0;
    for (const r of [0, 1, 2, 3, 4]) {
        if ((regionCounts[r] || 0) > 0) {
            offsets[r] = cursor;
            cursor += regionCounts[r];
        }
    }
    const slot = {};
    for (const r of Object.keys(byRegion)) {
        const base = offsets[r] || 0;
        const ids = byRegion[r];
        for (let i = 0; i < ids.length; i++) {
            slot[ids[i]] = base + i;
        }
    }
    return { herring, slot, regionCounts };
}

// Internal ───────────────────────────────────────────────────────────────────

/**
 * RGB → HLS, mirroring CPython's colorsys.rgb_to_hls.
 * r, g, b ∈ [0, 1]. Returns { h, l, s } also ∈ [0, 1].
 */
function rgbToHls(r, g, b) {
    const maxc = Math.max(r, g, b);
    const minc = Math.min(r, g, b);
    const l = (minc + maxc) / 2.0;
    if (minc === maxc) return { h: 0, l, s: 0 };
    let s;
    if (l <= 0.5) s = (maxc - minc) / (maxc + minc);
    else s = (maxc - minc) / (2.0 - maxc - minc);
    const rc = (maxc - r) / (maxc - minc);
    const gc = (maxc - g) / (maxc - minc);
    const bc = (maxc - b) / (maxc - minc);
    let h;
    if (r === maxc) h = bc - gc;
    else if (g === maxc) h = 2.0 + rc - bc;
    else h = 4.0 + gc - rc;
    h = (h / 6.0) % 1.0;
    if (h < 0) h += 1.0;
    return { h, l, s };
}
