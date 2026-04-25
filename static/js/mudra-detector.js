// mudra-detector.js — port of dream_positions_cb_morning.py gesture detectors.
//
// MediaPipe Hands JS gives the same coordinate system as TouchDesigner's
// MediaPipe.tox: each landmark is { x, y, z } with x, y ∈ [0, 1] and z roughly
// in [-0.2, 0.2]. All thresholds from the Python (0.05, 0.07, 1.0, etc.) port
// directly without any unit conversion.
//
// The detector functions are PURE — they take a snapshot of MediaPipe output
// and return a number ∈ [0, 1]. State (smoothing) lives in the caller-managed
// State object.

// Match the Python constants exactly.
export const MUDRA_THRESHOLD = 0.05;            // pinch closeness ≤ 0.05 = full mudra
export const HAKINI_SUM_THRESHOLD = 1.0;        // 5-pair distance sum below this = hakini
export const HAKINI_SMOOTHING = 0.25;           // α in EMA: smoothed = α·raw + (1-α)·prev

// Thumb tip = 4, index tip = 8, middle tip = 12, ring tip = 16, pinky tip = 20
const FINGERTIPS = [4, 8, 12, 16, 20];

/**
 * Create a state object the detectors can mutate. Caller keeps one instance
 * for the lifetime of the page.
 */
export function createDetectorState() {
    return {
        hakiniSmoothed: 0.0,
    };
}

/**
 * Single-hand pinch (Chin Mudra). Pure function over the first hand's
 * landmarks. Returns 0..1.
 *
 * Matches `_read_mudra` from dream_positions_cb_morning.py:
 *   d = ‖thumb_tip - index_tip‖
 *   raw = clamp01(1 - d / 0.05)
 *   return raw * raw   ← squared for snappier curve
 */
export function readMudra(landmarks) {
    if (!landmarks || landmarks.length < 1) return 0.0;
    const lm = landmarks[0];
    if (!lm || lm.length < 9) return 0.0;
    const thumb = lm[4], index = lm[8];
    const dx = thumb.x - index.x;
    const dy = thumb.y - index.y;
    const dz = (thumb.z || 0) - (index.z || 0);
    const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
    const raw = clamp01(1.0 - d / MUDRA_THRESHOLD);
    return raw * raw;
}

/**
 * Two-hand Hakini: 5 fingertip-pair distances summed across the first two
 * hands; raw = clamp01(1 - sum / 1.0); returns raw² smoothed at α=0.25.
 *
 * Matches `_read_hakini`.
 */
export function readHakini(landmarks, state) {
    let raw = 0.0;
    if (landmarks && landmarks.length >= 2) {
        const h1 = landmarks[0], h2 = landmarks[1];
        if (h1 && h1.length >= 21 && h2 && h2.length >= 21) {
            let total = 0.0;
            for (const tip of FINGERTIPS) {
                const a = h1[tip], b = h2[tip];
                const dx = a.x - b.x;
                const dy = a.y - b.y;
                const dz = (a.z || 0) - (b.z || 0);
                total += Math.sqrt(dx * dx + dy * dy + dz * dz);
            }
            const rs = clamp01(1.0 - total / HAKINI_SUM_THRESHOLD);
            raw = rs * rs;
        }
    }
    state.hakiniSmoothed = HAKINI_SMOOTHING * raw + (1 - HAKINI_SMOOTHING) * state.hakiniSmoothed;
    return state.hakiniSmoothed;
}

/**
 * Convenience wrapper — read both gestures from a single landmarks snapshot.
 * Returns { mudra, hakini } each ∈ [0, 1].
 */
export function readGestures(landmarks, state) {
    return {
        mudra: readMudra(landmarks),
        hakini: readHakini(landmarks, state),
    };
}

// Internal ───────────────────────────────────────────────────────────────────

function clamp01(x) {
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}
