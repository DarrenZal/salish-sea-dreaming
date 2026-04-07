"""
Gallery ambient mic monitor.
Reads audio from mic, computes RMS volume + spectral centroid, sends OSC to TD.

OSC messages sent (every 100ms):
  /salish/audio/volume  float 0-1  (RMS, smoothed, normalized by peak reference)
  /salish/audio/energy  float 0-1  (high-freq ratio, smoothed)

TouchDesigner mapping (via OSC In CHOP + Math CHOP):
  /salish/audio/volume → guidance_scale: remapped 0-1 → 7.0-12.0
  /salish/audio/energy → strength: remapped 0-1 → 0.3-0.7

Config (from .env):
  AUDIO_DEVICE_INDEX=0   (set after running sounddevice.query_devices())
  AUDIO_PEAK_REFERENCE=0.1  (RMS value that maps to 1.0; calibrate with clap test)
  TD_HOST=127.0.0.1
  TD_OSC_PORT=7000
"""

import argparse
import os
import threading
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

# Load .env from repo root
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

AUDIO_DEVICE_INDEX = int(os.getenv("AUDIO_DEVICE_INDEX", "0"))
AUDIO_PEAK_REFERENCE = float(os.getenv("AUDIO_PEAK_REFERENCE", "0.1"))
TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_OSC_PORT = int(os.getenv("TD_OSC_PORT", "7000"))

SAMPLE_RATE = 44100
BLOCK_SIZE = 4096  # ~93ms at 44100Hz
EMA_ALPHA = 0.3    # Exponential moving average smoothing factor

# Shared state protected by a lock
_lock = threading.Lock()
_smoothed_volume = 0.0
_smoothed_energy = 0.0


def _get_validated_device(preferred_index: int) -> int:
    """Return preferred device index if valid, else fall back to system default input."""
    import sounddevice as sd
    try:
        devices = sd.query_devices()
        if preferred_index < len(devices) and devices[preferred_index]["max_input_channels"] > 0:
            return preferred_index
    except Exception:
        pass
    default_in = sd.default.device[0]
    print(f"[audio] Device {preferred_index} not available — using system default ({default_in})")
    return default_in


def _compute_spectral_energy_ratio(data: np.ndarray) -> float:
    """
    Compute high-frequency energy ratio as a proxy for spectral centroid.
    Returns a float 0-1: fraction of energy above the median frequency bin.
    """
    mono = data[:, 0] if data.ndim > 1 else data
    spectrum = np.abs(np.fft.rfft(mono))
    total_energy = float(np.sum(spectrum))
    if total_energy < 1e-10:
        return 0.0
    midpoint = len(spectrum) // 2
    high_energy = float(np.sum(spectrum[midpoint:]))
    return high_energy / total_energy


def audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
    """sounddevice InputStream callback — runs in audio thread."""
    global _smoothed_volume, _smoothed_energy

    if status:
        print(f"[audio] Status: {status}", flush=True)

    # Compute RMS and normalize
    rms = float(np.sqrt(np.mean(indata ** 2)))
    volume = min(1.0, rms / AUDIO_PEAK_REFERENCE)

    # Spectral energy ratio
    energy = _compute_spectral_energy_ratio(indata)

    # Apply EMA smoothing
    with _lock:
        _smoothed_volume = EMA_ALPHA * volume + (1 - EMA_ALPHA) * _smoothed_volume
        _smoothed_energy = EMA_ALPHA * energy + (1 - EMA_ALPHA) * _smoothed_energy


def run_calibrate() -> None:
    """Print live RMS and normalized volume to stdout for calibration."""
    import sounddevice as sd

    print(f"Calibration mode — device index: {AUDIO_DEVICE_INDEX}")
    print(f"AUDIO_PEAK_REFERENCE = {AUDIO_PEAK_REFERENCE}")
    print("Clap loudly to calibrate. Press Ctrl+C to stop.\n")
    print(f"{'RMS':>12}  {'Normalized':>12}  {'Energy ratio':>14}")
    print("-" * 44)

    def _cal_callback(indata, frames, time_info, status):
        rms = float(np.sqrt(np.mean(indata ** 2)))
        volume = min(1.0, rms / AUDIO_PEAK_REFERENCE)
        energy = _compute_spectral_energy_ratio(indata)
        bar = "#" * int(volume * 30)
        print(f"{rms:12.6f}  {volume:12.4f}  {energy:14.4f}  {bar}", flush=True)

    try:
        with sd.InputStream(
            device=AUDIO_DEVICE_INDEX,
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=_cal_callback,
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCalibration stopped.")
    except sd.PortAudioError as exc:
        print(f"Could not open audio device {AUDIO_DEVICE_INDEX}. "
              f"Run with --list-devices to see available devices.\n{exc}")


def run_monitor() -> None:
    """Main monitoring loop: read mic, send OSC to TouchDesigner every 100ms."""
    import sounddevice as sd
    from pythonosc import udp_client

    osc_client = udp_client.SimpleUDPClient(TD_HOST, TD_OSC_PORT)
    device_index = _get_validated_device(AUDIO_DEVICE_INDEX)
    print(f"OSC target: {TD_HOST}:{TD_OSC_PORT}")
    print(f"Audio device index: {device_index}  |  Peak reference: {AUDIO_PEAK_REFERENCE}")
    print("Sending /salish/audio/volume and /salish/audio/energy every 100ms. Ctrl+C to stop.\n")

    try:
        with sd.InputStream(
            device=device_index,
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=audio_callback,
        ):
            while True:
                time.sleep(0.1)
                with _lock:
                    vol = _smoothed_volume
                    eng = _smoothed_energy
                osc_client.send_message("/salish/audio/volume", float(vol))
                osc_client.send_message("/salish/audio/energy", float(eng))
    except KeyboardInterrupt:
        print("\nAudio monitor stopped.")
    except Exception as exc:
        # Check if it's a PortAudioError (sounddevice may not be importable for isinstance)
        if "PortAudio" in type(exc).__name__ or "sounddevice" in str(exc).lower():
            print(f"Could not open audio device {AUDIO_DEVICE_INDEX}. "
                  f"Run with --list-devices to see available devices.\n{exc}")
        else:
            raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gallery ambient mic monitor — sends audio features via OSC to TouchDesigner"
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Print live audio levels for calibration (no OSC sent)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List audio devices and exit",
    )
    args = parser.parse_args()

    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        return

    if args.calibrate:
        run_calibrate()
    else:
        run_monitor()


if __name__ == "__main__":
    main()
