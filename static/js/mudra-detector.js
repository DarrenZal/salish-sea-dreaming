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

// Mudra (one-hand pinch). The TD callback uses a fixed normalized threshold
// of 0.05 which works on the gallery 3090's high-res fixed-distance cam.
// On a laptop webcam, hand-to-camera distance varies, so we normalize the
// thumb-index distance by the hand's own length (wrist→middle-tip). 0.50
// means "fingers within half a finger-length" → matches what looks like an
// "OK" pinch in practice. Squaring the raw signal (TD does this) damps the
// response too much on lower-resolution webcams; we use the linear value.
export const MUDRA_RATIO_THRESHOLD = 0.50;
export const MUDRA_SMOOTHING = 0.40;            // α in EMA — quick to fire, quick to release

export const HAKINI_SUM_THRESHOLD = 1.0;        // 5-pair distance sum below this = hakini
export const HAKINI_SMOOTHING = 0.25;

// Landmark indices: wrist=0, thumb_tip=4, index_tip=8, middle_tip=12, ring_tip=16, pinky_tip=20
const FINGERTIPS = [4, 8, 12, 16, 20];

/**
 * Create a state object the detectors can mutate. Caller keeps one instance
 * for the lifetime of the page.
 */
export function createDetectorState() {
    return {
        mudraSmoothed: 0.0,
        hakiniSmoothed: 0.0,
    };
}

/**
 * Single-hand pinch (Chin Mudra). Pure function over a single hand's
 * landmarks. Tries each detected hand and returns the strongest pinch — so
 * pinching either hand fires the gesture, not just the first detected.
 * Returns 0..1, smoothed via EMA.
 *
 * Distance is normalized by the hand's own length (wrist→middle-tip) so a
 * pinch fires the same way at any distance from the camera.
 *
 *   handLen = ‖middle_tip - wrist‖
 *   ratio = ‖thumb_tip - index_tip‖ / handLen
 *   raw  = clamp01(1 - ratio / MUDRA_RATIO_THRESHOLD)
 */
export function readMudra(landmarks, state) {
    let bestRaw = 0.0;
    if (landmarks && landmarks.length >= 1) {
        for (const lm of landmarks) {
            if (!lm || lm.length < 21) continue;
            const wrist = lm[0], thumb = lm[4], index = lm[8], middleTip = lm[12];
            const handLen = dist3(wrist, middleTip);
            if (handLen < 1e-4) continue;  // can't normalize; skip this hand
            const pinchD = dist3(thumb, index);
            const ratio = pinchD / handLen;
            // Linear response curve. Squaring (TD-style) damps too much
            // on a laptop webcam; users have to do an exaggerated pinch
            // to register. Linear gives natural-pinch values around 60-80%.
            const raw = clamp01(1.0 - ratio / MUDRA_RATIO_THRESHOLD);
            if (raw > bestRaw) bestRaw = raw;
        }
    }
    if (state) {
        state.mudraSmoothed = MUDRA_SMOOTHING * bestRaw + (1 - MUDRA_SMOOTHING) * state.mudraSmoothed;
        return state.mudraSmoothed;
    }
    return bestRaw;
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
        mudra: readMudra(landmarks, state),
        hakini: readHakini(landmarks, state),
    };
}

// Internal ───────────────────────────────────────────────────────────────────

function clamp01(x) {
    if (x < 0) return 0;
    if (x > 1) return 1;
    return x;
}

function dist3(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dz = (a.z || 0) - (b.z || 0);
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
}
