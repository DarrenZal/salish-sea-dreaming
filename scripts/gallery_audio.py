"""
Gallery audio monitor -- WASAPI loopback version (Windows-only).

Listens to the 3090's default playback device via a WASAPI loopback input
stream and publishes RMS + spectral-energy features to TouchDesigner via OSC.
Also maintains a rolling 60s window + writes state snapshots so health_probe
can distinguish "monitor alive and audio flowing" from "monitor alive but
silent" from "monitor dead".

Replaces the prior sounddevice-based version that read from an input-side
mic. The 3090 has NO mic (confirmed by Prav 2026-04-19). The audio we care
about is the signal going OUT of the 3090 to the 3.5mm splitter -> speakers
+ Bluetooth transmitter. WASAPI loopback captures exactly that.

Baseline measurement 2026-04-20 evening with Ableton playing Matt's mp3:
  RMS ~= 0.02  (nominal ambient)
  peak ~= 0.10
Silence threshold set conservatively at 0.001 (anything below this = real
silence; typical playback is ~20x above).

OSC messages (same contract as the old mic version):
  /salish/audio/volume  float 0-1
  /salish/audio/energy  float 0-1

Config (.env):
  AUDIO_PEAK_REFERENCE=0.1   (calibration: RMS at which normalised volume=1.0)
  AUDIO_SILENCE_RMS=0.001    (below this, sustain 60s -> silence alert)
  TD_HOST=127.0.0.1
  TD_OSC_PORT=7000
  AUDIO_STATE_PATH=C:\Users\user\ssd_audio_state.json
  AUDIO_HEARTBEAT_PATH=C:\Users\user\heartbeats\gallery_audio.hb

Dependencies (install in the Python env that runs this script):
  pip install pyaudiowpatch numpy python-dotenv python-osc

Deploy path on 3090: C:\Users\user\gallery_audio.py, run via the venv at
C:\Users\user\wasapi_venv\ (created 2026-04-20 with pyaudiowpatch already
installed). Scheduled task SSD-Audio should point at:
  C:\Users\user\wasapi_venv\Scripts\python.exe C:\Users\user\gallery_audio.py
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    print("[FATAL] pyaudiowpatch not installed. pip install pyaudiowpatch", file=sys.stderr)
    sys.exit(1)

_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

AUDIO_PEAK_REFERENCE = float(os.getenv("AUDIO_PEAK_REFERENCE", "0.1"))
AUDIO_SILENCE_RMS    = float(os.getenv("AUDIO_SILENCE_RMS", "0.001"))
TD_HOST              = os.getenv("TD_HOST", "127.0.0.1")
TD_OSC_PORT          = int(os.getenv("TD_OSC_PORT", "7000"))
AUDIO_STATE_PATH     = os.getenv("AUDIO_STATE_PATH", r"C:\Users\user\ssd_audio_state.json")
AUDIO_HEARTBEAT_PATH = os.getenv("AUDIO_HEARTBEAT_PATH", r"C:\Users\user\heartbeats\gallery_audio.hb")

BLOCK_SIZE = 4096
EMA_ALPHA  = 0.3

_STATE_WINDOW_SECONDS = 60
_STATE_WINDOW_SAMPLES = _STATE_WINDOW_SECONDS * 10   # ~10 writes/sec
_vol_window: "collections.deque[float]" = collections.deque(maxlen=_STATE_WINDOW_SAMPLES)
_eng_window: "collections.deque[float]" = collections.deque(maxlen=_STATE_WINDOW_SAMPLES)

_lock = threading.Lock()
_smoothed_volume = 0.0
_smoothed_energy = 0.0


def _compute_spectral_energy_ratio(data: np.ndarray) -> float:
    mono = data[:, 0] if data.ndim > 1 else data
    spectrum = np.abs(np.fft.rfft(mono))
    total_energy = float(np.sum(spectrum))
    if total_energy < 1e-10:
        return 0.0
    midpoint = len(spectrum) // 2
    return float(np.sum(spectrum[midpoint:])) / total_energy


def _find_default_loopback(p: "pyaudio.PyAudio") -> dict:
    wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_output = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
    for d in p.get_loopback_device_info_generator():
        if default_output["name"] in d["name"]:
            return d
    raise RuntimeError(f"No loopback device matches default output '{default_output['name']}'")


def list_devices() -> None:
    p = pyaudio.PyAudio()
    try:
        default = _find_default_loopback(p)
        print(f"* Default loopback target: [{default['index']}] {default['name']}")
    except RuntimeError as e:
        print(f"WARN: {e}")
    print("\nAll loopback devices:")
    for d in p.get_loopback_device_info_generator():
        print(f"  [{d['index']}] {d['name']}  rate={int(d['defaultSampleRate'])}Hz ch={d['maxInputChannels']}")
    p.terminate()


def _audio_callback(in_data, frame_count, time_info, status):
    global _smoothed_volume, _smoothed_energy

    if status:
        print(f"[audio] status flag: {status}", flush=True)

    arr = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
    # WASAPI loopback is usually stereo; reduce to mono via mean per frame
    if arr.size >= frame_count * 2:
        arr = arr.reshape(-1, 2).mean(axis=1)

    rms = float(np.sqrt(np.mean(arr ** 2)))
    volume = min(1.0, rms / AUDIO_PEAK_REFERENCE)
    energy = _compute_spectral_energy_ratio(arr)

    with _lock:
        _smoothed_volume = EMA_ALPHA * volume + (1 - EMA_ALPHA) * _smoothed_volume
        _smoothed_energy = EMA_ALPHA * energy + (1 - EMA_ALPHA) * _smoothed_energy

    return (None, pyaudio.paContinue)


def _write_state_snapshot(vol: float, eng: float) -> None:
    try:
        snapshot = {
            "updated_at": time.time(),
            "volume": vol,
            "energy": eng,
            "vol_max_60s": max(_vol_window) if _vol_window else 0.0,
            "eng_max_60s": max(_eng_window) if _eng_window else 0.0,
            "samples_in_window": len(_vol_window),
            "window_seconds": _STATE_WINDOW_SECONDS,
            "source": "wasapi_loopback",
        }
        tmp = AUDIO_STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(snapshot, f)
        os.replace(tmp, AUDIO_STATE_PATH)
    except Exception:
        pass


def _write_heartbeat() -> None:
    try:
        Path(AUDIO_HEARTBEAT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIO_HEARTBEAT_PATH, "w") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S") + "Z\n")
    except Exception:
        pass


def run_calibrate() -> None:
    """Print live RMS + normalised volume for threshold tuning. No OSC sent."""
    p = pyaudio.PyAudio()
    try:
        dev = _find_default_loopback(p)
        print(f"Calibration from loopback: '{dev['name']}'")
        print(f"Current AUDIO_PEAK_REFERENCE={AUDIO_PEAK_REFERENCE}  SILENCE_RMS={AUDIO_SILENCE_RMS}")
        print(f"{'RMS':>10}  {'Volume':>8}  {'Energy':>8}  bar")
        print("-" * 60)
        stream = p.open(
            format=pyaudio.paInt16,
            channels=dev["maxInputChannels"],
            rate=int(dev["defaultSampleRate"]),
            frames_per_buffer=BLOCK_SIZE,
            input=True,
            input_device_index=dev["index"],
        )
        try:
            while True:
                chunk = stream.read(BLOCK_SIZE, exception_on_overflow=False)
                arr = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
                if arr.size >= BLOCK_SIZE * 2:
                    arr = arr.reshape(-1, 2).mean(axis=1)
                rms = float(np.sqrt(np.mean(arr ** 2)))
                vol = min(1.0, rms / AUDIO_PEAK_REFERENCE)
                eng = _compute_spectral_energy_ratio(arr)
                bar = "#" * int(vol * 30)
                print(f"{rms:10.5f}  {vol:8.3f}  {eng:8.3f}  {bar}", flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
    finally:
        p.terminate()


def run_monitor() -> None:
    """Main loop: capture loopback, send OSC, write state + heartbeat."""
    from pythonosc import udp_client

    osc = udp_client.SimpleUDPClient(TD_HOST, TD_OSC_PORT)
    p = pyaudio.PyAudio()
    try:
        dev = _find_default_loopback(p)
    except RuntimeError as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        p.terminate()
        sys.exit(2)

    print(f"Loopback source: '{dev['name']}' rate={int(dev['defaultSampleRate'])}Hz ch={dev['maxInputChannels']}")
    print(f"OSC target: {TD_HOST}:{TD_OSC_PORT}")
    print(f"State file: {AUDIO_STATE_PATH}")
    print(f"Heartbeat:  {AUDIO_HEARTBEAT_PATH}")

    stream = p.open(
        format=pyaudio.paInt16,
        channels=dev["maxInputChannels"],
        rate=int(dev["defaultSampleRate"]),
        frames_per_buffer=BLOCK_SIZE,
        input=True,
        input_device_index=dev["index"],
        stream_callback=_audio_callback,
    )
    stream.start_stream()

    state_tick = 0
    try:
        while stream.is_active():
            time.sleep(0.1)
            with _lock:
                vol = _smoothed_volume
                eng = _smoothed_energy
            osc.send_message("/salish/audio/volume", float(vol))
            osc.send_message("/salish/audio/energy", float(eng))
            _vol_window.append(float(vol))
            _eng_window.append(float(eng))
            state_tick += 1
            if state_tick >= 10:
                state_tick = 0
                _write_state_snapshot(float(vol), float(eng))
                _write_heartbeat()
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def main() -> None:
    parser = argparse.ArgumentParser(description="Gallery audio loopback monitor (WASAPI)")
    parser.add_argument("--calibrate", action="store_true", help="Live RMS/volume print (no OSC)")
    parser.add_argument("--list-devices", action="store_true", help="List loopback devices")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
    elif args.calibrate:
        run_calibrate()
    else:
        run_monitor()


if __name__ == "__main__":
    main()
