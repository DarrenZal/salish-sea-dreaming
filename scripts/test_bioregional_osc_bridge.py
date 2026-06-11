#!/usr/bin/env python3
"""End-to-end local smoke test for bioregional_osc_bridge.py.

Starts a local OSC receiver on an ephemeral UDP port, runs the bridge once
against the live IWLS/Fraser endpoints, and validates received address/type
shape against docs/next-iteration/_research/live-feed-osc-contract.md.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


EXPECTED = {
    "/sea/tide/level_m": "float",
    "/sea/tide/rate_mph": "float",
    "/sea/tide/predicted_next_hilo_m": "float",
    "/sea/tide/predicted_next_hilo_seconds": "float",
    "/river/fraser/discharge_cms": "float",
    "/river/fraser/level_m": "float",
    "/system/cache_used": "int",
    "/system/heartbeat": "heartbeat",
}


def validate_value(address: str, args: tuple[Any, ...]) -> str | None:
    expected = EXPECTED[address]
    if expected == "float":
        if len(args) != 1 or not isinstance(args[0], float):
            return f"{address} expected one float, got {args!r}"
        return None
    if expected == "int":
        if len(args) != 1 or not isinstance(args[0], int):
            return f"{address} expected one int, got {args!r}"
        return None
    if expected == "heartbeat":
        if len(args) != 2:
            return f"{address} expected two args, got {args!r}"
        if args[0] != 1 or not isinstance(args[1], float):
            return f"{address} expected [1, float_timestamp], got {args!r}"
        return None
    return f"Unknown expectation {expected!r} for {address}"


def run_receiver() -> tuple[ThreadingOSCUDPServer, dict[str, tuple[Any, ...]]]:
    received: dict[str, tuple[Any, ...]] = {}
    dispatcher = Dispatcher()

    def handler(address: str, *args: Any) -> None:
        received[address] = args

    dispatcher.set_default_handler(handler)
    server = ThreadingOSCUDPServer(("127.0.0.1", 0), dispatcher)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, received


def main() -> int:
    server, received = run_receiver()
    host, port = server.server_address

    with tempfile.TemporaryDirectory(prefix="ssd-bioregional-") as tmp:
        cache = Path(tmp) / "cache.json"
        cmd = [
            sys.executable,
            "scripts/bioregional_osc_bridge.py",
            "--once",
            "--osc-host",
            str(host),
            "--osc-port",
            str(port),
            "--cache",
            str(cache),
            "--no-cache-fallback",
        ]
        print(f"Running bridge -> OSC {host}:{port}")
        result = subprocess.run(cmd, text=True, capture_output=True)

    deadline = time.time() + 2.0
    while time.time() < deadline and len(received) < len(EXPECTED):
        time.sleep(0.05)
    server.shutdown()

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        return result.returncode

    missing = sorted(set(EXPECTED) - set(received))
    unexpected = sorted(set(received) - set(EXPECTED))
    errors = [err for address, args in sorted(received.items()) if address in EXPECTED
              for err in [validate_value(address, args)] if err]

    print("Received OSC:")
    for address in sorted(received):
        print(f"  {address} {received[address]!r}")

    if missing:
        errors.append(f"Missing expected address(es): {', '.join(missing)}")
    if unexpected:
        errors.append(f"Unexpected address(es): {', '.join(unexpected)}")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("PASS: OSC packet keys/types match live-feed contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
