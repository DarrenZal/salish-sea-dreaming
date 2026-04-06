"""
td_relay.py — runs on TD machine (Windows 3090).
Pulls enriched prompts from gallery server via SSE, sends each as OSC to TouchDesigner.
Auto-reconnects on disconnect. Singleton via PID file — exits if another instance runs.
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("td_relay")

# Force line-buffering so output appears in log files immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GALLERY_URL = os.getenv("GALLERY_URL", "http://37.27.48.12:9000")
TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_PORT = int(os.getenv("TD_PORT", "7000"))

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
            # Check if that PID is actually still alive
            import subprocess
            try:
                r = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {old_pid}", "/NH"],
                    capture_output=True, text=True, timeout=5
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
log.info(f"Gallery SSE: {GALLERY_URL}/td/stream")

# ---------------------------------------------------------------------------
# Main reconnect loop
# ---------------------------------------------------------------------------

while True:
    try:
        log.info(f"Connecting to {GALLERY_URL}/td/stream ...")
        with requests.get(
            f"{GALLERY_URL}/td/stream",
            stream=True,
            timeout=(10, None),  # 10s connect timeout, no read timeout (SSE is infinite)
            headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
        ) as r:
            r.raise_for_status()
            log.info("Connected — waiting for visitor prompts")
            buf = ""
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if not chunk:
                    continue
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.rstrip("\r")
                    if line.startswith("data:"):
                        prompt = line[5:].strip()
                        if prompt and prompt != "ping":
                            osc.send_message("/salish/prompt/visitor", prompt)
                            log.info(f"\u2192 OSC: {prompt[:80]}")
    except KeyboardInterrupt:
        log.info("Stopped by user (Ctrl+C).")
        break
    except Exception as e:
        log.warning(f"Disconnected: {e}. Reconnecting in 5s...")
        time.sleep(5)
