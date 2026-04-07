"""
td_relay.py — runs on TD machine (Windows 3090).
Polls gallery server for new visitor prompts and photos, sends each via OSC to TouchDesigner.

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
PHOTO_LOCAL_PATH = Path(os.getenv("PHOTO_LOCAL_PATH", r"C:\Users\user\visitor_latest.jpg"))

# Style servers — TELUS H200 tried first, local 3090 as fallback
# TELUS accessed via Jupyter server proxy on port 8765
TELUS_STYLE_URL = os.getenv(
    "TELUS_STYLE_URL",
    "https://model-deployment-0b50s.paas.ai.telus.com/proxy/8765"
)
TELUS_TOKEN = os.getenv("TELUS_TOKEN", "8f6ceea09691892cf2d19dc7466669ea")
LOCAL_STYLE_URL = os.getenv("LOCAL_STYLE_URL", "http://127.0.0.1:8765")

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
last_photo_seq = 0
consecutive_errors = 0
_telus_ok = False  # TELUS proxy not accessible (no jupyter-server-proxy); use local only


def _apply_style(raw_bytes: bytes) -> bytes:
    """Try TELUS H200 first, fall back to local 3090 style server."""
    global _telus_ok

    if _telus_ok:
        try:
            t0 = time.time()
            r = session.post(
                f"{TELUS_STYLE_URL}/style",
                data=raw_bytes,
                headers={
                    "Content-Type": "image/jpeg",
                    "Authorization": f"Token {TELUS_TOKEN}",
                },
                timeout=60,
                verify=False,
            )
            if r.status_code == 200:
                elapsed = time.time() - t0
                log.info(f"  TELUS style: {len(raw_bytes)}B -> {len(r.content)}B in {elapsed:.1f}s")
                return r.content
            else:
                log.warning(f"  TELUS style returned {r.status_code}, falling back to local")
                _telus_ok = False
        except Exception as e:
            log.warning(f"  TELUS style failed ({e}), falling back to local")
            _telus_ok = False

    # Local fallback (3090)
    try:
        t0 = time.time()
        r = session.post(
            f"{LOCAL_STYLE_URL}/style",
            data=raw_bytes,
            headers={"Content-Type": "image/jpeg"},
            timeout=45,
        )
        if r.status_code == 200:
            elapsed = time.time() - t0
            log.info(f"  Local style: {len(raw_bytes)}B -> {len(r.content)}B in {elapsed:.1f}s")
            return r.content
        else:
            log.warning(f"  Local style returned {r.status_code}, using raw photo")
    except Exception as e:
        log.warning(f"  Local style failed ({e}), using raw photo")

    return raw_bytes  # pass through unstyled if both fail

while True:
    try:
        # --- Poll for new prompt ---
        resp = session.get(
            f"{GALLERY_URL}/td/next",
            params={"after": last_seq},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        consecutive_errors = 0

        server_seq = data.get("seq", 0)
        prompt = data.get("prompt")

        # Detect server restart (seq went backwards) — reset our counter
        if server_seq < last_seq:
            log.warning(f"Server seq went backwards ({last_seq}->{server_seq}) — server restarted, resetting")
            last_seq = 0
            last_photo_seq = 0

        if prompt is not None and server_seq > last_seq:
            last_seq = server_seq
            osc.send_message("/salish/prompt/visitor", prompt)
            log.info(f"-> OSC seq={last_seq}: {prompt[:80]}")
        else:
            log.debug(f"poll seq={server_seq} (no change)")

        # --- Poll for new visitor photo ---
        try:
            photo_resp = session.get(
                f"{GALLERY_URL}/visitor-photo/next",
                params={"after": last_photo_seq},
                timeout=10,
            )
            photo_resp.raise_for_status()
            photo_data = photo_resp.json()
            server_photo_seq = photo_data.get("seq", 0)

            if server_photo_seq < last_photo_seq:
                log.warning(f"Photo seq reset ({last_photo_seq}->{server_photo_seq})")
                last_photo_seq = 0

            if photo_data.get("available") and server_photo_seq > last_photo_seq:
                last_photo_seq = server_photo_seq
                img_resp = session.get(f"{GALLERY_URL}/visitor-photo/latest.jpg", timeout=15)
                img_resp.raise_for_status()
                raw_bytes = img_resp.content
                log.info(f"Photo received: {len(raw_bytes)}B seq={last_photo_seq} — styling...")
                styled_bytes = _apply_style(raw_bytes)
                PHOTO_LOCAL_PATH.write_bytes(styled_bytes)
                osc.send_message("/salish/photo/visitor", str(PHOTO_LOCAL_PATH))
                log.info(f"-> OSC photo seq={last_photo_seq} -> {PHOTO_LOCAL_PATH}")
        except Exception as e:
            log.debug(f"Photo poll error (non-fatal): {e}")

        time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Stopped by user (Ctrl+C).")
        break
    except Exception as e:
        consecutive_errors += 1
        backoff = min(5 * consecutive_errors, 15)
        log.warning(f"Poll error ({consecutive_errors}): {e}. Retrying in {backoff}s...")
        time.sleep(backoff)
