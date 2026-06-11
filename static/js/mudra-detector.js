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
export const SWEEP_DISTANCE_THRESHOLD = 0.13;   // normalized palm-x movement in one open-palm frame interval
export const SWEEP_VELOCITY_THRESHOLD = 0.00032;
export const SWEEP_PULSE_MS = 420;              // hold a discrete sweep long enough for the page threshold
export const SWEEP_COOLDOWN_MS = 900;

// "Fray" — port of TD's asymmetric-break behavior, simplified for one
// person across two hands. When the seal is broken by losing ONE hand
// (camera occlusion, dropping a hand, leaving frame) but the other hand
// stays visible, hold the herring shape elevated so it dissolves slowly
// instead of snapping back to dispersed. Two hands gone = normal full
// release (camera still rolling but seal genuinely ended).
export const FRAY_RECENT_SEAL_MS = 3000;          // window after seal to consider fray
export const FRAY_DECAY_PER_FRAME = 0.992;        // ~half-life ≈ 3s at 30fps
export const SEAL_TRIGGER = 0.40;                  // raw hakini above this = sealed

// Landmark indices: wrist=0, thumb_tip=4, index_tip=8, middle_tip=12, ring_tip=16, pinky_tip=20
const FINGERTIPS = [4, 8, 12, 16, 20];

/**
 * Create a state object the detectors can mutate. Caller keeps one instance
 * for the lifetime of the page.
 */
export function createDetectorState() {
    return {
        mudraSmoothed: 0.0,
        middleMudraSmoothed: 0.0,
        hakiniSmoothed: 0.0,
        anjaliHoldMs: 0,
        anjaliActive: false,
        sweepSmoothed: 0.0,
        lastPalmX: null,
        lastPalmT: null,
        lastSweepTime: -SWEEP_COOLDOWN_MS,
        sweepPulseUntil: 0,
        sweepOpenPalm: false,
        sweepMotion: 0.0,
        // Bilateral-fray tracking
        lastSealTime: 0,        // ms timestamp of last frame raw hakini > SEAL_TRIGGER
        frayActive: false,      // current fray state (one hand missing after seal)
        remainingHandX: null,   // screen-x ∈ [0,1] of the still-visible hand during fray
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
    return readPinch(landmarks, state, 8, "mudraSmoothed");
}

export function readMiddleMudra(landmarks, state) {
    return readPinch(landmarks, state, 12, "middleMudraSmoothed");
}

function readPinch(landmarks, state, tipIndex, stateKey) {
    let bestRaw = 0.0;
    if (landmarks && landmarks.length >= 1) {
        for (const lm of landmarks) {
            if (!lm || lm.length < 21) continue;
            const wrist = lm[0], thumb = lm[4], finger = lm[tipIndex], middleTip = lm[12];
            const handLen = dist3(wrist, middleTip);
            if (handLen < 1e-4) continue;  // can't normalize; skip this hand
            const pinchD = dist3(thumb, finger);
            const ratio = pinchD / handLen;
            // Linear response curve. Squaring (TD-style) damps too much
            // on a laptop webcam; users have to do an exaggerated pinch
            // to register. Linear gives natural-pinch values around 60-80%.
            const raw = clamp01(1.0 - ratio / MUDRA_RATIO_THRESHOLD);
            if (raw > bestRaw) bestRaw = raw;
        }
    }
    if (state) {
        state[stateKey] = MUDRA_SMOOTHING * bestRaw + (1 - MUDRA_SMOOTHING) * (state[stateKey] || 0);
        return state[stateKey];
    }
    return bestRaw;
}

/**
 * Two-hand Hakini: 5 fingertip-pair distances summed across two hands;
 * raw = clamp01(1 - sum / 1.0)²; returns smoothed value at α=0.25.
 *
 * Asymmetric-break ("fray") behavior:
 *   - 0 hands visible        → normal EMA toward raw=0 (fast release)
 *   - 1 hand visible AND
 *     recently sealed        → SLOW decay (~3s half-life) so herring
 *                              shape lingers — the "fray" window
 *   - 2+ hands               → normal Hakini math
 *
 * Mirrors the spirit of TD's _read_hakini_bilateral without the 2-person
 * face/midline split. Sets state.frayActive so the caller can surface it.
 */
export function readHakini(landmarks, state) {
    const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const validHands = (landmarks || []).filter(h => h && h.length >= 21);
    const handsCount = validHands.length;

    let raw = 0.0;
    if (handsCount >= 2) {
        const h1 = validHands[0], h2 = validHands[1];
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

    // Track "we were just sealed" timestamp.
    if (raw > SEAL_TRIGGER) {
        state.lastSealTime = now;
    }
    const sinceSeal = now - (state.lastSealTime || 0);

    // Fray = exactly one hand visible AND we were sealed within the recent
    // window. With 2+ hands but no seal, this is just open hands → fall
    // through to normal EMA. With 0 hands, normal release (no fray).
    const inFray = (handsCount === 1 && state.lastSealTime > 0 && sinceSeal < FRAY_RECENT_SEAL_MS);
    state.frayActive = inFray;

    if (inFray) {
        // Track the screen-x of the remaining hand so the renderer can
        // anchor "its" half of the herring and let the other side fray.
        // Use the wrist landmark (0) as a stable reference.
        const rem = validHands[0];
        if (rem && rem[0] && typeof rem[0].x === 'number') {
            state.remainingHandX = rem[0].x;
        }
        // Slow decay — preserves the herring shape while one hand frames it.
        state.hakiniSmoothed *= FRAY_DECAY_PER_FRAME;
    } else {
        state.remainingHandX = null;
        state.hakiniSmoothed = HAKINI_SMOOTHING * raw + (1 - HAKINI_SMOOTHING) * state.hakiniSmoothed;
    }
    return state.hakiniSmoothed;
}

export function readAnjali(landmarks, state) {
    const validHands = (landmarks || []).filter(h => h && h.length >= 21);
    const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    let raw = 0.0;
    if (validHands.length >= 2) {
        const h1 = validHands[0], h2 = validHands[1];
        const wristD = dist3(h1[0], h2[0]);
        const palmD = (
            dist3(h1[5], h2[5]) + dist3(h1[9], h2[9]) +
            dist3(h1[13], h2[13]) + dist3(h1[17], h2[17])
        ) / 4;
        const fingerTipD = (
            dist3(h1[8], h2[8]) + dist3(h1[12], h2[12]) +
            dist3(h1[16], h2[16]) + dist3(h1[20], h2[20])
        ) / 4;
        const midline = Math.abs(((h1[0].x + h2[0].x) * 0.5) - 0.5);
        const vertical1 = Math.max(0, h1[0].y - h1[12].y);
        const vertical2 = Math.max(0, h2[0].y - h2[12].y);
        const closeness = clamp01(1.0 - ((wristD + palmD + fingerTipD) / 3) / 0.18);
        const midlineScore = clamp01(1.0 - midline / 0.22);
        const verticalScore = clamp01(((vertical1 + vertical2) * 0.5) / 0.16);
        raw = closeness * midlineScore * verticalScore;
    }

    const dt = state.lastAnjaliT ? Math.max(0, now - state.lastAnjaliT) : 0;
    state.lastAnjaliT = now;
    if (raw > 0.55) state.anjaliHoldMs += dt;
    else state.anjaliHoldMs = Math.max(0, state.anjaliHoldMs - dt * 1.8);
    state.anjaliActive = state.anjaliHoldMs >= 1700;
    return state.anjaliActive ? 1.0 : clamp01(state.anjaliHoldMs / 1700) * 0.8;
}

export function readOpenPalmSweep(landmarks, state) {
    const now = (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const validHands = (landmarks || []).filter(h => h && h.length >= 21);
    let raw = 0.0;
    state.sweepOpenPalm = false;
    state.sweepMotion = 0.0;
    if (validHands.length >= 1) {
        for (const lm of validHands) {
            const wrist = lm[0];
            const tips = [8, 12, 16, 20].map(i => lm[i]);
            const extended = tips.filter(t => dist3(wrist, t) > 0.14).length;
            const raised = tips.filter(t => t.y < wrist.y + 0.04).length;
            const open = extended >= 3 && raised >= 3;
            const palmX = (lm[0].x + lm[5].x + lm[9].x + lm[13].x + lm[17].x) / 5;
            if (open) state.sweepOpenPalm = true;
            if (open && state.lastPalmX !== null && state.lastPalmT !== null) {
                const dt = Math.max(1, now - state.lastPalmT);
                const dx = Math.abs(palmX - state.lastPalmX);
                const vx = dx / dt;
                state.sweepMotion = Math.max(state.sweepMotion || 0, clamp01(dx / SWEEP_DISTANCE_THRESHOLD));
                if (dx > SWEEP_DISTANCE_THRESHOLD && vx > SWEEP_VELOCITY_THRESHOLD && now - state.lastSweepTime > SWEEP_COOLDOWN_MS) {
                    state.sweepPulseUntil = now + SWEEP_PULSE_MS;
                    state.lastSweepTime = now;
                }
            }
            if (open) {
                state.lastPalmX = palmX;
                state.lastPalmT = now;
            }
        }
    }
    raw = now < (state.sweepPulseUntil || 0) ? 1.0 : raw;
    state.sweepSmoothed = 0.55 * raw + 0.45 * (state.sweepSmoothed || 0);
    return state.sweepSmoothed;
}

/**
 * Convenience wrapper — read both gestures from a single landmarks snapshot.
 * Returns { mudra, middleMudra, hakini, anjali, sweep, frayActive, remainingHandX }.
 *   remainingHandX: screen-x ∈ [0, 1] of the still-visible hand during fray.
 *                   null when not in fray.
 */
export function readGestures(landmarks, state) {
    const mudra = readMudra(landmarks, state);
    const middleMudra = readMiddleMudra(landmarks, state);
    const hakini = readHakini(landmarks, state);
    const anjali = readAnjali(landmarks, state);
    const sweep = readOpenPalmSweep(landmarks, state);
    return {
        mudra,
        middleMudra,
        hakini,
        anjali,
        sweep,
        sweepOpenPalm: !!state.sweepOpenPalm,
        sweepMotion: state.sweepMotion || 0,
        frayActive: !!state.frayActive,
        remainingHandX: state.frayActive ? state.remainingHandX : null,
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
