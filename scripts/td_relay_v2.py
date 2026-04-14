"""
td_relay_v2.py — runs on TD machine (Windows 3090).
Polls gallery server for new visitor prompts and photos, sends each via OSC to TouchDesigner.
NEW: Also controls Resolume layer opacity (auto-fade on prompt arrival).
     Dual mode: auto (relay controls Resolume) / live (Prav controls via MIDI).
     Mode toggle: GET http://localhost:7002/mode/auto|live|

Based on td_relay.py — original is preserved as rollback.
Run: python td_relay_v2.py
"""
import atexit
import logging
import os
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests
from pythonosc import udp_client
from resolume_fade import ResolumeFader

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

# TD snapshot: TD saves this file every ~3s; relay uploads it every SNAP_UPLOAD_EVERY polls
SNAP_LOCAL_PATH = Path(os.getenv("SNAP_LOCAL_PATH", r"C:\Users\user\Desktop\td_snap.jpg"))
SNAP_UPLOAD_EVERY = int(os.getenv("SNAP_UPLOAD_EVERY", "15"))  # polls (~30s)

# Snap watchdog: if td_snap.jpg hasn't changed in this many seconds, kick snap_runner via MCP
SNAP_STALE_SECS = int(os.getenv("SNAP_STALE_SECS", "120"))
TD_MCP_URL = os.getenv("TD_MCP_URL", "http://127.0.0.1:9981/api/td/server/exec")

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
# Resolume fade control (v2 addition)
# ---------------------------------------------------------------------------

RESOLUME_OSC_PORT = int(os.getenv("RESOLUME_OSC_PORT", "7001"))
RESOLUME_TD_LAYER = int(os.getenv("RESOLUME_TD_LAYER", "4"))
FADE_IN_SECS = float(os.getenv("FADE_IN_SECS", "2.0"))
FADE_OUT_SECS = float(os.getenv("FADE_OUT_SECS", "2.0"))
PROMPT_DWELL_SECS = float(os.getenv("PROMPT_DWELL_SECS", "30"))
MODE_PORT = int(os.getenv("MODE_PORT", "7002"))

fader = ResolumeFader(
    host="127.0.0.1",
    port=RESOLUME_OSC_PORT,
    layer=RESOLUME_TD_LAYER,
    fade_duration=FADE_IN_SECS,
)
_mode = "auto"  # "auto" or "live"
_prompt_arrived_at = 0.0  # wall-clock time of last visitor prompt

log.info(f"Resolume fade: layer={RESOLUME_TD_LAYER} port={RESOLUME_OSC_PORT} mode={_mode}")

# ---------------------------------------------------------------------------
# Mode toggle HTTP server (v2 addition)
# ---------------------------------------------------------------------------

class _ModeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _mode, _prompt_arrived_at
        if self.path == "/mode/auto":
            _mode = "auto"
            _prompt_arrived_at = 0.0
            msg = "auto"
            log.info("Mode switched to AUTO")
        elif self.path == "/mode/live":
            if _mode == "auto":
                fader.fade_out()  # graceful handoff
            _mode = "live"
            _prompt_arrived_at = 0.0
            msg = "live"
            log.info("Mode switched to LIVE")
        elif self.path == "/mode":
            msg = _mode
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode())

    def log_message(self, *args):
        pass  # suppress HTTP request logs

try:
    _mode_server = HTTPServer(("127.0.0.1", MODE_PORT), _ModeHandler)
    threading.Thread(target=_mode_server.serve_forever, daemon=True).start()
    log.info(f"Mode server: http://127.0.0.1:{MODE_PORT}/mode/auto|live")
except OSError as e:
    log.warning(f"Mode server failed to start on port {MODE_PORT}: {e} — mode toggle unavailable")

# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

session = requests.Session()
last_seq = 0
last_photo_seq = 0
consecutive_errors = 0
_telus_ok = False  # TELUS proxy not accessible (no jupyter-server-proxy); use local only
_snap_poll_count = 0
_snap_last_mtime = 0.0
_snap_watchdog_last_kick = 0.0  # wall-clock time of last watchdog kick


def _upload_snapshot() -> None:
    """Upload td_snap.jpg to gallery server if it's been updated since last upload."""
    global _snap_last_mtime, _snap_last_change_time
    if not SNAP_LOCAL_PATH.exists():
        return
    try:
        mtime = SNAP_LOCAL_PATH.stat().st_mtime
        if mtime <= _snap_last_mtime:
            return  # file hasn't changed
        data = SNAP_LOCAL_PATH.read_bytes()
        resp = session.post(
            f"{GALLERY_URL}/td/snapshot",
            data=data,
            headers={"Content-Type": "image/jpeg"},
            timeout=8,
        )
        if resp.status_code == 200:
            _snap_last_mtime = mtime
            log.info(f"Snapshot uploaded: {len(data)}B")
        else:
            log.debug(f"Snapshot upload returned {resp.status_code}")
    except Exception as e:
        log.debug(f"Snapshot upload error (non-fatal): {e}")


def _snap_watchdog() -> None:
    """If td_snap.jpg hasn't changed in SNAP_STALE_SECS, kick snap_runner via TD MCP."""
    global _snap_watchdog_last_kick
    if not SNAP_LOCAL_PATH.exists():
        return
    now = time.time()
    try:
        file_mtime = SNAP_LOCAL_PATH.stat().st_mtime
    except Exception:
        return
    stale_secs = now - file_mtime
    if stale_secs < SNAP_STALE_SECS:
        return
    # Don't kick more than once per 5 minutes
    if now - _snap_watchdog_last_kick < 300:
        return
    _snap_watchdog_last_kick = now  # cooldown regardless of outcome
    log.warning(f"Snap stale for {stale_secs:.0f}s — attempting snap_runner kick via MCP")
    try:
        r = session.post(
            TD_MCP_URL,
            json={"script": "td.run(\"op('/project1/snap_runner').run()\", delayFrames=30)"},
            timeout=5,
        )
        if r.status_code == 200:
            log.info("Snap watchdog: snap_runner kicked via MCP")
        else:
            log.info(f"Snap watchdog: MCP returned {r.status_code}")
    except Exception as e:
        log.info(f"Snap watchdog: MCP not reachable ({e})")


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
            # v2: fade in Resolume TD layer on visitor prompt (auto mode only)
            if _mode == "auto":
                fader.fade_in()
                _prompt_arrived_at = time.time()
                log.info(f"Resolume: fade IN (auto mode, dwell={PROMPT_DWELL_SECS}s)")
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

        # --- v2: Dwell timeout — fade out after prompt dwell period ---
        if _mode == "auto" and _prompt_arrived_at > 0:
            if (time.time() - _prompt_arrived_at) > PROMPT_DWELL_SECS:
                fader.fade_out()
                _prompt_arrived_at = 0.0
                log.info("Resolume: fade OUT (dwell expired)")

        # --- Upload TD snapshot every SNAP_UPLOAD_EVERY polls ---
        _snap_poll_count += 1
        if _snap_poll_count >= SNAP_UPLOAD_EVERY:
            _snap_poll_count = 0
            _upload_snapshot()
            _snap_watchdog()

        time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        log.info("Stopped by user (Ctrl+C).")
        break
    except Exception as e:
        consecutive_errors += 1
        backoff = min(5 * consecutive_errors, 15)
        log.warning(f"Poll error ({consecutive_errors}): {e}. Retrying in {backoff}s...")
        time.sleep(backoff)
