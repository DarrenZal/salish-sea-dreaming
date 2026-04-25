// camera-bridge.js — getUserMedia + MediaPipe HandLandmarker, opt-in flow.
//
// Architecture: 100% client-side. No video, no images, no biometric data
// leaves the browser. Aligns with the Foundation invariant "the room is
// allowed to forget" — the gesture detection IS the room, and it forgets
// every frame.
//
// Public API:
//   await CameraBridge.requestStart({ video, onLandmarks })
//   CameraBridge.stop()
//   CameraBridge.isAvailable()    // browser feature check, no permission ask
//   CameraBridge.isActive()       // currently streaming?
//
// Loads MediaPipe Tasks Vision via CDN (no npm build step). Hand landmarker
// model file is also CDN-hosted (Google's official mirror).

const VISION_BUNDLE_URL =
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs';
const HAND_MODEL_URL =
    'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task';
const WASM_BASE_URL =
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm';

let _state = {
    active: false,
    handLandmarker: null,
    videoEl: null,
    stream: null,
    rafId: null,
    onLandmarks: null,
    lastTimestamp: 0,
};

export function isAvailable() {
    if (!navigator || !navigator.mediaDevices) return false;
    if (typeof navigator.mediaDevices.getUserMedia !== 'function') return false;
    if (typeof window.WebAssembly === 'undefined') return false;
    return true;
}

export function isActive() {
    return _state.active;
}

/**
 * Begin streaming + detection. Throws if user denies camera or initialization
 * fails. Caller is responsible for the consent UX BEFORE calling this.
 *
 * Options:
 *   video:        an existing <video> element to feed (hidden is fine)
 *   onLandmarks:  function(landmarksList) called every frame.
 *                 landmarksList is an array of arrays of {x, y, z} (one
 *                 inner array per detected hand). May be empty.
 *   numHands:     int, default 2 (mobile-aware caller may pass 4)
 */
export async function requestStart({ video, onLandmarks, numHands = 2 }) {
    if (_state.active) return;
    if (!isAvailable()) {
        throw new Error('Camera or WebAssembly not available in this browser');
    }
    if (!video) throw new Error('camera-bridge: video element required');
    if (typeof onLandmarks !== 'function') {
        throw new Error('camera-bridge: onLandmarks callback required');
    }

    // 1) Request the camera. Will throw NotAllowedError if user denies.
    const stream = await navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 },
            frameRate: { ideal: 30, max: 30 },
        },
        audio: false,
    });
    _state.stream = stream;
    _state.videoEl = video;
    _state.onLandmarks = onLandmarks;

    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    await video.play().catch(() => {/* will autoplay once metadata loads */});

    // 2) Initialize MediaPipe Tasks Vision (lazy-imported via CDN).
    const vision = await import(VISION_BUNDLE_URL);
    const { FilesetResolver, HandLandmarker } = vision;
    const fileset = await FilesetResolver.forVisionTasks(WASM_BASE_URL);
    const handLandmarker = await HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: HAND_MODEL_URL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numHands: numHands,
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
    });
    _state.handLandmarker = handLandmarker;

    // 3) Per-frame loop. detectForVideo expects a monotonically-increasing
    // timestamp. Use performance.now() and ensure strict monotonicity.
    _state.active = true;
    _state.lastTimestamp = 0;
    const tick = () => {
        if (!_state.active) return;
        const v = _state.videoEl;
        if (v && v.readyState >= 2 && v.videoWidth > 0) {
            let ts = performance.now();
            if (ts <= _state.lastTimestamp) ts = _state.lastTimestamp + 1;
            _state.lastTimestamp = ts;
            try {
                const result = _state.handLandmarker.detectForVideo(v, ts);
                const landmarksList = (result && result.landmarks) || [];
                _state.onLandmarks(landmarksList);
            } catch (e) {
                // Don't tear down the loop on transient detect errors.
                console.warn('[camera-bridge] detect error:', e);
                _state.onLandmarks([]);
            }
        }
        _state.rafId = requestAnimationFrame(tick);
    };
    _state.rafId = requestAnimationFrame(tick);
}

export function stop() {
    if (!_state.active) return;
    _state.active = false;
    if (_state.rafId !== null) {
        cancelAnimationFrame(_state.rafId);
        _state.rafId = null;
    }
    if (_state.handLandmarker) {
        try { _state.handLandmarker.close(); } catch (_) {}
        _state.handLandmarker = null;
    }
    if (_state.stream) {
        for (const track of _state.stream.getTracks()) {
            try { track.stop(); } catch (_) {}
        }
        _state.stream = null;
    }
    if (_state.videoEl) {
        try { _state.videoEl.srcObject = null; } catch (_) {}
        _state.videoEl = null;
    }
    _state.onLandmarks = null;
}
