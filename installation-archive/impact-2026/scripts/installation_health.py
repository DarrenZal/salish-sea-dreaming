"""
installation_health.py — runs on the 3090 (Windows).
Checks local process health and reports to the gallery server on poly.

Checks:
  - TouchDesigner.exe is running
  - Arena.exe (Resolume) is running
  - td_relay.py is running (python process with td_relay in command line)
  - td_snap.jpg freshness (age in seconds)

Reports heartbeat to gallery server every 60s via POST /health/heartbeat.

Usage:
    python installation_health.py

Register as NSSM service:
    nssm install ssd-health "C:\\path\\to\\python.exe" "C:\\path\\to\\installation_health.py"
    nssm set ssd-health Start SERVICE_AUTO_START
"""
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE = Path(__file__).with_name("installation_health.log")

handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=handlers,
)
log = logging.getLogger("installation_health")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GALLERY_URL = os.getenv("GALLERY_URL", "http://37.27.48.12:9000")
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # seconds
SNAP_PATH = Path(os.getenv("SNAP_LOCAL_PATH", r"C:\Users\user\Desktop\td_snap.jpg"))

# ---------------------------------------------------------------------------
# Process checks (Windows)
# ---------------------------------------------------------------------------


def _check_process(name: str) -> bool:
    """Check if a process with the given name is running (Windows tasklist)."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}", "/NH"],
            capture_output=True, text=True, timeout=10,
        )
        return name.lower() in result.stdout.lower()
    except Exception as e:
        log.warning(f"Failed to check process {name}: {e}")
        return False


def _check_relay() -> bool:
    """Check if td_relay.py is running via its PID file."""
    pid_file = Path(r"C:\Users\user\td_relay.pid")
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=5,
        )
        return "python" in result.stdout.lower()
    except Exception:
        return False


def _snap_age() -> float | None:
    """Return age of td_snap.jpg in seconds, or None if missing."""
    if not SNAP_PATH.exists():
        return None
    try:
        return time.time() - SNAP_PATH.stat().st_mtime
    except Exception:
        return None


def collect_health() -> dict:
    """Gather all health signals into a report dict."""
    snap_age = _snap_age()
    return {
        "processes": {
            "touchdesigner": _check_process("TouchDesigner.exe"),
            "resolume": _check_process("Arena.exe"),
            "autolume": _check_process("Autolume.exe"),
            "relay": _check_relay(),
        },
        "snap_age_s": round(snap_age, 1) if snap_age is not None else None,
        "snap_fresh": snap_age is not None and snap_age < 300,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ---------------------------------------------------------------------------
# Report to gallery server
# ---------------------------------------------------------------------------

def report_heartbeat(health: dict) -> bool:
    """POST health report to gallery server. Returns True on success."""
    import urllib.request
    try:
        data = json.dumps(health).encode("utf-8")
        req = urllib.request.Request(
            f"{GALLERY_URL}/health/heartbeat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        log.warning(f"Failed to report heartbeat: {e}")
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info(f"Installation health monitor started (interval={CHECK_INTERVAL}s)")
    log.info(f"Reporting to: {GALLERY_URL}/health/heartbeat")

    while True:
        try:
            health = collect_health()

            # Log locally
            procs = health["processes"]
            proc_str = " ".join(
                f"{k}={'OK' if v else 'DOWN'}" for k, v in procs.items()
            )
            snap_str = f"snap={health['snap_age_s']:.0f}s" if health["snap_age_s"] is not None else "snap=MISSING"
            log.info(f"Health: {proc_str} {snap_str}")

            # Alert on issues
            for name, running in procs.items():
                if not running:
                    log.warning(f"ALERT: {name} is NOT running!")
            if health["snap_age_s"] is not None and health["snap_age_s"] > 300:
                log.warning(f"ALERT: TD snapshot stale ({health['snap_age_s']:.0f}s)")

            # Report to gallery server
            ok = report_heartbeat(health)
            if ok:
                log.debug("Heartbeat reported successfully")
            else:
                log.warning("Heartbeat report failed — gallery server unreachable?")

        except KeyboardInterrupt:
            log.info("Stopped by user")
            break
        except Exception as e:
            log.error(f"Health check error: {e}")

        time.sleep(CHECK_INTERVAL)
