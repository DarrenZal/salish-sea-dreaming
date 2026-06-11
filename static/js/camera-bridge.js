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
    stage: 'idle',
    error: null,
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

export function debugState() {
    const video = _state.videoEl;
    const tracks = _state.stream ? _state.stream.getVideoTracks().map(track => ({
        label: track.label || '',
        enabled: track.enabled,
        muted: track.muted,
        readyState: track.readyState,
    })) : [];
    return {
        active: _state.active,
        stage: _state.stage,
        error: _state.error,
        hasStream: !!_state.stream,
        tracks,
        video: video ? {
            readyState: video.readyState,
            paused: video.paused,
            width: video.videoWidth || 0,
            height: video.videoHeight || 0,
        } : null,
        hasHandLandmarker: !!_state.handLandmarker,
    };
}

function setStage(stage, error = null) {
    _state.stage = stage;
    _state.error = error ? `${error.name || 'Error'}: ${error.message || error}` : null;
}

function cleanupStream() {
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
    _state.active = false;
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
    setStage('starting');
    if (!isAvailable()) {
        setStage('unavailable');
        throw new Error('Camera or WebAssembly not available in this browser');
    }
    if (!video) throw new Error('camera-bridge: video element required');
    if (typeof onLandmarks !== 'function') {
        throw new Error('camera-bridge: onLandmarks callback required');
    }

    try {
        // 1) Request the camera. Will throw NotAllowedError if user denies.
        setStage('requesting-camera');
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
        _state.active = true;
        setStage('stream-acquired');

        video.srcObject = stream;
        video.muted = true;
        video.playsInline = true;
        setStage('starting-video');
        await video.play().catch((e) => {
            console.warn('[camera-bridge] video.play warning:', e);
        });
        setStage('video-playing');

        // 2) Initialize MediaPipe Tasks Vision (lazy-imported via CDN).
        setStage('loading-mediapipe');
        const vision = await import(VISION_BUNDLE_URL);
        const { FilesetResolver, HandLandmarker } = vision;
        const fileset = await FilesetResolver.forVisionTasks(WASM_BASE_URL);
        setStage('loading-hand-model-gpu');
        let handLandmarker = null;
        const handOptions = {
            runningMode: 'VIDEO',
            numHands: numHands,
            minHandDetectionConfidence: 0.5,
            minHandPresenceConfidence: 0.5,
            minTrackingConfidence: 0.5,
        };
        try {
            handLandmarker = await HandLandmarker.createFromOptions(fileset, {
                ...handOptions,
                baseOptions: { modelAssetPath: HAND_MODEL_URL, delegate: 'GPU' },
            });
        } catch (gpuError) {
            console.warn('[camera-bridge] GPU hand model failed; retrying CPU:', gpuError);
            setStage('loading-hand-model-cpu');
            handLandmarker = await HandLandmarker.createFromOptions(fileset, {
                ...handOptions,
                baseOptions: { modelAssetPath: HAND_MODEL_URL },
            });
        }
        _state.handLandmarker = handLandmarker;

        // 3) Per-frame loop. detectForVideo expects a monotonically-increasing
        // timestamp. Use performance.now() and ensure strict monotonicity.
        _state.lastTimestamp = 0;
        setStage('ready');
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
    } catch (e) {
        cleanupStream();
        setStage('failed', e);
        throw e;
    }
}

export function stop() {
    cleanupStream();
    setStage('stopped');
}
