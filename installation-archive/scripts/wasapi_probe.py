"""Enumerate WASAPI loopback devices + capture 3 seconds from default to prove API works."""
import sys
try:
    import pyaudiowpatch as pyaudio
except ImportError as e:
    print(f"[FAIL] import pyaudiowpatch failed: {e}")
    sys.exit(1)

p = pyaudio.PyAudio()
print("PyAudio (pyaudiowpatch) initialized")

try:
    wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    print(f"WASAPI host API index: {wasapi['index']}")
    default_speakers = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
    print(f"Default output device: '{default_speakers['name']}' rate={int(default_speakers['defaultSampleRate'])} ch={default_speakers['maxOutputChannels']}")
except OSError as e:
    print(f"[FAIL] WASAPI host API unavailable: {e}")
    sys.exit(2)

# Find loopback mirror of default output
loopback = None
for d in p.get_loopback_device_info_generator():
    if default_speakers["name"] in d["name"]:
        loopback = d
        break

if loopback is None:
    print("[FAIL] No loopback device matching default output")
    print("--- all loopback devices ---")
    for d in p.get_loopback_device_info_generator():
        print(f"  [{d['index']}] {d['name']}  rate={int(d['defaultSampleRate'])} ch={d['maxInputChannels']}")
    sys.exit(3)

print(f"[OK] loopback device: '{loopback['name']}' rate={int(loopback['defaultSampleRate'])} ch={loopback['maxInputChannels']}")

# Capture 3 seconds, compute RMS
import numpy as np
rate = int(loopback["defaultSampleRate"])
chans = loopback["maxInputChannels"]
stream = p.open(
    format=pyaudio.paInt16,
    channels=chans,
    rate=rate,
    frames_per_buffer=4096,
    input=True,
    input_device_index=loopback["index"],
)
print(f"capturing 3s from loopback at {rate}Hz {chans}ch...")
frames = b""
for _ in range(int(rate * 3 / 4096)):
    frames += stream.read(4096, exception_on_overflow=False)
stream.stop_stream()
stream.close()

arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
rms = float(np.sqrt(np.mean(arr**2)))
peak = float(np.max(np.abs(arr)))
print(f"[OK] captured {len(arr)} samples, RMS={rms:.4f}, peak={peak:.4f}")
print(f"    (non-zero RMS/peak means Ableton/whatever is actually playing audio right now)")
p.terminate()
