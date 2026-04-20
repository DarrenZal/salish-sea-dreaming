"""
gallery_audio_loopback_draft.py -- DRAFT rewrite of gallery_audio.py using
WASAPI loopback on the default playback device, instead of reading from
a nonexistent input mic.

Status: DRAFT -- not deployed. Do not replace scripts/gallery_audio.py
until this has been tested on the 3090 with Ableton running.

Why rewrite:
  The 3090 has no microphone (confirmed by Prav on Signal 2026-04-19
  evening). The original gallery_audio.py reads from AUDIO_DEVICE_INDEX=0
  (input side) and bases its silence alerts on that data. Since there's
  nothing actually connected to that input, the alerts are meaningless.
  The right signal is the *output* going to the 3.5mm -> splitter ->
  speakers + BT broadcaster, captured via WASAPI loopback.

Approach:
  WASAPI loopback is a Windows feature that lets you open an "input"
  stream that mirrors the audio being sent to an output device. This
  requires the pyaudiowpatch package (Windows-only fork of pyaudio with
  explicit WASAPI loopback support). The stock sounddevice package can
  sometimes do this by passing an output device index to InputStream,
  but the behavior is driver-dependent and flaky.

  pip install pyaudiowpatch

Behavior preserved from original:
  - Same OSC output (/salish/audio/volume, /salish/audio/energy)
  - Same state snapshot at C:\\Users\\user\\ssd_audio_state.json
  - Same EMA smoothing
  - Same 60s rolling window

Behavior changed:
  - No longer reads a mic. Reads the default-playback-device loopback.
  - Silence threshold should be tuned lower (output-side signal is more
    directly tied to app audio, not room ambient).

Testing plan (once deployed):
  1. Start Ableton with the gallery audio loop playing.
  2. Run: python gallery_audio_loopback_draft.py --list-devices
     -> confirm loopback device enumerates (should show "[Loopback]" suffix)
  3. Run the script -- state file should show nonzero volume.
  4. Mute Ableton -> state file should show volume -> 0 within 1-2s.
  5. Alert threshold (in health_probe.ps1) should catch the drop.

KNOWN GAP: Bluetooth-transmitter pairing failures. The loopback captures
the PRE-split signal, so if the BT transmitter loses pairing but the
wired-speaker branch still works, this detector can't tell. To catch
that we'd need either a mic in the gallery or a BT transmitter with
pair-state reporting.
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
    import pyaudiowpatch as pyaudio  # Windows WASAPI-loopback-capable fork
except ImportError:
    print("[audio] ERROR: pyaudiowpatch not installed. Run: pip install pyaudiowpatch", file=sys.stderr)
    sys.exit(1)

_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)

AUDIO_PEAK_REFERENCE = float(os.getenv("AUDIO_PEAK_REFERENCE", "0.1"))
TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_OSC_PORT = int(os.getenv("TD_OSC_PORT", "7000"))
AUDIO_STATE_PATH = os.getenv("AUDIO_STATE_PATH", r"C:\Users\user\ssd_audio_state.json")

SAMPLE_RATE_TARGET = 48000
BLOCK_SIZE = 4096
EMA_ALPHA = 0.3

_STATE_WINDOW_SECONDS = 60
_STATE_WINDOW_SAMPLES = _STATE_WINDOW_SECONDS * 10
_vol_window: "collections.deque[float]" = collections.deque(maxlen=_STATE_WINDOW_SAMPLES)
_eng_window: "collections.deque[float]" = collections.deque(maxlen=_STATE_WINDOW_SAMPLES)

_lock = threading.Lock()
_smoothed_volume = 0.0
_smoothed_energy = 0.0


def find_default_loopback_device(p: "pyaudio.PyAudio") -> dict:
    """
    Locate the WASAPI loopback device matching the current default output.
    pyaudiowpatch exposes loopback variants via get_loopback_device_info_generator().
    """
    try:
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError as e:
        raise RuntimeError(f"WASAPI not available: {e}")
    default_output = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
    out_name = default_output["name"]

    for dev in p.get_loopback_device_info_generator():
        if out_name in dev["name"]:
            return dev
    raise RuntimeError(f"No loopback device matches default output '{out_name}'")


def list_devices() -> None:
    p = pyaudio.PyAudio()
    try:
        default = find_default_loopback_device(p)
    except RuntimeError as e:
        print(f"[audio] {e}")
        default = None
    print("\nAll loopback devices:")
    for dev in p.get_loopback_device_info_generator():
        marker = " *" if default and dev["index"] == default["index"] else ""
        print(f"  [{dev['index']}] {dev['name']}{marker}  ch={dev['maxInputChannels']} rate={int(dev['defaultSampleRate'])}")
    p.terminate()


# TODO: port the rest of the original gallery_audio.py here:
#   - _compute_spectral_energy_ratio
#   - OSC sender thread
#   - state snapshot writer (AUDIO_STATE_PATH)
#   - stream callback that updates _smoothed_volume, _smoothed_energy, windows
#   - main loop
#
# The only real change needed beyond boilerplate is opening the stream via
# pyaudiowpatch against the loopback device instead of sounddevice against
# an input device. Signature:
#
# stream = p.open(
#     format=pyaudio.paInt16,
#     channels=device["maxInputChannels"],
#     rate=int(device["defaultSampleRate"]),
#     frames_per_buffer=BLOCK_SIZE,
#     input=True,
#     input_device_index=device["index"],
#     stream_callback=_audio_callback,
# )
#
# Then the _audio_callback converts bytes -> np.int16 -> float -> runs the
# same RMS + FFT logic already in gallery_audio.py.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()
    if args.list_devices:
        list_devices()
        sys.exit(0)
    print("[audio] Full implementation pending. Use --list-devices to enumerate WASAPI loopback targets.")
