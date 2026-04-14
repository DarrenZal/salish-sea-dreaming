#!/usr/bin/env python3
"""
resolume_fade.py — Resolume Arena OSC layer fade controller.

Controls Resolume layer opacity via OSC to create smooth fade-in/fade-out
when visitor prompts arrive. Designed to be imported by td_relay.py or
run standalone for testing.

Resolume OSC address format:
  /composition/layers/{layer}/video/opacity  (float 0.0–1.0)

Usage (standalone test):
    python resolume_fade.py --fade-in --layer 1
    python resolume_fade.py --fade-out --layer 1
    python resolume_fade.py --test --layer 1   # fade in, wait 5s, fade out

Integration with td_relay.py:
    from resolume_fade import ResolumeFader
    fader = ResolumeFader(host="127.0.0.1", port=7001, layer=1)
    fader.fade_in()   # non-blocking, runs in background thread
    fader.fade_out()  # non-blocking

Deploy to 3090: scp scripts/resolume_fade.py windows-desktop-remote:C:/Users/user/resolume_fade.py
"""

import argparse
import logging
import os
import threading
import time

from pythonosc import udp_client

log = logging.getLogger("resolume_fade")


class ResolumeFader:
    """Controls a single Resolume layer's opacity via OSC."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7001,
        layer: int = 1,
        fade_duration: float = 2.0,
        fade_steps: int = 20,
    ):
        self.host = host
        self.port = port
        self.layer = layer
        self.fade_duration = fade_duration
        self.fade_steps = fade_steps
        self.osc = udp_client.SimpleUDPClient(host, port)
        self._current_opacity = 0.0
        self._fade_lock = threading.Lock()
        self._cancel_event = threading.Event()
        log.info(f"ResolumeFader: layer={layer} target={host}:{port} fade={fade_duration}s")

    @property
    def _osc_address(self) -> str:
        return f"/composition/layers/{self.layer}/video/opacity"

    def _send_opacity(self, value: float) -> None:
        """Send a single opacity value to Resolume."""
        clamped = max(0.0, min(1.0, value))
        self.osc.send_message(self._osc_address, clamped)
        self._current_opacity = clamped

    def _ramp(self, target: float) -> None:
        """Blocking ramp from current opacity to target."""
        with self._fade_lock:
            self._cancel_event.clear()
            start = self._current_opacity
            if abs(target - start) < 0.01:
                self._send_opacity(target)
                return
            interval = self.fade_duration / self.fade_steps
            for i in range(self.fade_steps + 1):
                if self._cancel_event.is_set():
                    return
                t = i / self.fade_steps
                value = start + (target - start) * t
                self._send_opacity(value)
                if i < self.fade_steps:
                    time.sleep(interval)

    def fade_in(self, blocking: bool = False) -> None:
        """Fade layer opacity to 1.0. Non-blocking by default."""
        self._cancel_event.set()  # cancel any in-progress fade
        if blocking:
            self._ramp(1.0)
        else:
            threading.Thread(target=self._ramp, args=(1.0,), daemon=True).start()
        log.info(f"Resolume layer {self.layer}: fade IN")

    def fade_out(self, blocking: bool = False) -> None:
        """Fade layer opacity to 0.0. Non-blocking by default."""
        self._cancel_event.set()  # cancel any in-progress fade
        if blocking:
            self._ramp(0.0)
        else:
            threading.Thread(target=self._ramp, args=(0.0,), daemon=True).start()
        log.info(f"Resolume layer {self.layer}: fade OUT")

    def set_opacity(self, value: float) -> None:
        """Immediately set opacity (no fade)."""
        self._send_opacity(value)


def main():
    parser = argparse.ArgumentParser(description="Resolume layer fade controller")
    parser.add_argument("--host", default="127.0.0.1", help="Resolume OSC host")
    parser.add_argument("--port", type=int, default=7001, help="Resolume OSC port")
    parser.add_argument("--layer", type=int, default=1, help="Resolume layer number")
    parser.add_argument("--duration", type=float, default=2.0, help="Fade duration in seconds")
    parser.add_argument("--fade-in", action="store_true", help="Fade layer in")
    parser.add_argument("--fade-out", action="store_true", help="Fade layer out")
    parser.add_argument("--test", action="store_true", help="Fade in, wait 5s, fade out")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    fader = ResolumeFader(
        host=args.host,
        port=args.port,
        layer=args.layer,
        fade_duration=args.duration,
    )

    if args.test:
        print(f"Testing: fade in layer {args.layer}, hold 5s, fade out...")
        fader.fade_in(blocking=True)
        print("  Holding at full opacity for 5s...")
        time.sleep(5)
        fader.fade_out(blocking=True)
        print("  Done.")
    elif args.fade_in:
        fader.fade_in(blocking=True)
        print("Fade in complete.")
    elif args.fade_out:
        fader.fade_out(blocking=True)
        print("Fade out complete.")
    else:
        parser.error("Specify --fade-in, --fade-out, or --test")


if __name__ == "__main__":
    main()
