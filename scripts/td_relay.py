"""
td_relay.py — runs on TD machine (Windows 3090).
Polls gallery server for new visitor prompts, sends each as OSC to TouchDesigner.

Uses HTTP polling (/td/next?after=N) instead of SSE streaming — SSE via
requests.iter_content() dies silently on Windows after 1-2 events due to
socket buffering differences.

Singleton via PID file — exits if another instance is already running.
Run: python td_relay.py
"""
import atexit
import logging
import os
import sys
import time
from pathlib import Path

import requests
from pythonosc import udp_client

# ---------------------------------------------------------------------------
# Logging — timestamps in every line
# ---------------------------------------------------------------------------

LOG_FILE = Path(__file__).with_name("td_relay.log")

handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=handlers,
)
log = logging.getLogger("td_relay")

# Line-buffering only works when stdout is a real stream (not None / windowless)
try:
    if sys.stdout is not None:
        sys.stdout.reconfigure(line_buffering=True)
    if sys.stderr is not None:
        sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GALLERY_URL = os.getenv("GALLERY_URL", "http://37.27.48.12:9000")
TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_PORT = int(os.getenv("TD_PORT", "7000"))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2.0"))  # seconds between polls

# PID file lives next to this script to prevent duplicate instances
PID_FILE = Path(__file__).with_suffix(".pid")

# ---------------------------------------------------------------------------
# Singleton lock — exit if another td_relay.py already running
# ---------------------------------------------------------------------------

def _acquire_singleton():
    my_pid = os.getpid()
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            old_pid = None
        if old_pid and old_pid != my_pid:
            import subprocess
            try:
                r = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {old_pid}", "/NH"],
                    capture_output=True, text=True, timeout=5,
                )
                if "python" in r.stdout.lower():
                    log.error(
                        f"Another td_relay.py is already running (PID {old_pid}). "
                        "Kill it first or let NSSM manage this service. Exiting."
                    )
                    sys.exit(1)
            except Exception:
                pass  # tasklist failed — proceed anyway
    PID_FILE.write_text(str(my_pid))
    atexit.register(lambda: PID_FILE.unlink(missing_ok=True))
    log.info(f"Started (PID {my_pid})")

_acquire_singleton()

# ---------------------------------------------------------------------------
# OSC client
# ---------------------------------------------------------------------------

osc = udp_client.SimpleUDPClient(TD_HOST, TD_PORT)
log.info(f"OSC target: {TD_HOST}:{TD_PORT}")
log.info(f"Gallery poll: {GALLERY_URL}/td/next  interval={POLL_INTERVAL}s")

# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

session = requests.Session()
last_seq = 0
consecutive_errors = 0

while True:
    try:
        resp = session.get(
            f"{GALLERY_URL}/td/next",
            params={"after": last_seq},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        consecutive_errors = 0  # reset on success

        server_seq = data.get("seq", 0)
        prompt = data.get("prompt")

        if prompt is not None and server_seq > last_seq:
            last_seq = server_seq
            osc.send_message("/salish/prompt/visitor", prompt)
            log.info(f"-> OSC seq={last_seq}: {prompt[:80]}")
        else:
            log.debug(f"poll seq={server_seq} (no change)")

        time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Stopped by user (Ctrl+C).")
        break
    except Exception as e:
        consecutive_errors += 1
        backoff = min(5 * consecutive_errors, 60)
        log.warning(f"Poll error ({consecutive_errors}): {e}. Retrying in {backoff}s...")
        time.sleep(backoff)
