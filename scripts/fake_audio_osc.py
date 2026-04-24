"""
fake_audio_osc.py — send simulated /salish/audio/* OSC for local TD testing.

Mimics the shape of gallery_audio.py's output (which is Windows-only) so
scenes on the Mac can be developed against the same OSC contract.

Default mode: slow sinusoidal 'breathing' — volume rises and falls over
~12s, energy drifts on a longer cycle. Good for watching a scene idle
through its full dynamic range.

Other modes:
  --mode silent    pins volume=0, energy=0 (stillness baseline)
  --mode peak      pins volume=1, energy=1 (check max scaling)
  --mode random    noisy walk (more like real music)

Usage:
  python3 scripts/fake_audio_osc.py
  python3 scripts/fake_audio_osc.py --host 127.0.0.1 --port 7000
  python3 scripts/fake_audio_osc.py --mode silent
  python3 scripts/fake_audio_osc.py --mode peak
  python3 scripts/fake_audio_osc.py --rate 20        # messages per second

Install: pip install python-osc
"""
from __future__ import annotations

import argparse
import math
import random
import sys
import time

try:
    from pythonosc import udp_client
except ImportError:
    print("Missing: pip install python-osc", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7000)
    ap.add_argument("--mode", choices=["breathe", "silent", "peak", "random"],
                    default="breathe")
    ap.add_argument("--rate", type=float, default=10.0,
                    help="messages per second (default 10, matches gallery_audio)")
    ap.add_argument("--vol-period", type=float, default=12.0,
                    help="breathe mode: volume cycle seconds")
    ap.add_argument("--eng-period", type=float, default=37.0,
                    help="breathe mode: energy cycle seconds")
    args = ap.parse_args()

    osc = udp_client.SimpleUDPClient(args.host, args.port)
    dt = 1.0 / args.rate
    t0 = time.time()

    print(f"fake_audio_osc -> {args.host}:{args.port}  mode={args.mode}  rate={args.rate}Hz")
    print("Ctrl-C to stop.")

    # Random-walk state
    rw_vol, rw_eng = 0.3, 0.5

    try:
        while True:
            t = time.time() - t0
            if args.mode == "breathe":
                # Smooth sinusoidal rise/fall, 0..1
                vol = 0.5 + 0.5 * math.sin(2 * math.pi * t / args.vol_period)
                eng = 0.5 + 0.5 * math.sin(2 * math.pi * t / args.eng_period)
            elif args.mode == "silent":
                vol, eng = 0.0, 0.0
            elif args.mode == "peak":
                vol, eng = 1.0, 1.0
            elif args.mode == "random":
                rw_vol = max(0.0, min(1.0, rw_vol + random.uniform(-0.08, 0.08)))
                rw_eng = max(0.0, min(1.0, rw_eng + random.uniform(-0.04, 0.04)))
                vol, eng = rw_vol, rw_eng
            else:
                vol, eng = 0.0, 0.0

            osc.send_message("/salish/audio/volume", float(vol))
            osc.send_message("/salish/audio/energy", float(eng))
            time.sleep(dt)
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
