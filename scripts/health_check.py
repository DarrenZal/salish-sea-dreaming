#!/usr/bin/env python3
"""
health_check.py — periodic health checker with alerting.
Runs on poly via cron. Hits /health/full on the gallery server and sends
alerts when the installation is unhealthy.

Cron setup (every 15 minutes):
    */15 * * * * /usr/bin/python3 /path/to/health_check.py

Alert channels (configure via env vars or .env):
    ALERT_SLACK_WEBHOOK   — Slack incoming webhook URL
    ALERT_TELEGRAM_TOKEN  — Telegram bot token
    ALERT_TELEGRAM_CHAT   — Telegram chat ID
    ALERT_EMAIL_TO        — Email address(es), comma-separated
    ALERT_EMAIL_FROM      — Sender email
    ALERT_SMTP_HOST       — SMTP server (default: localhost)

At least one alert channel must be configured.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GALLERY_URL = os.getenv("GALLERY_URL", "http://127.0.0.1:9000")
STATE_FILE = Path(__file__).with_name(".health_state.json")

# Alert channels
SLACK_WEBHOOK = os.getenv("ALERT_SLACK_WEBHOOK", "")
TELEGRAM_TOKEN = os.getenv("ALERT_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.getenv("ALERT_TELEGRAM_CHAT", "")
EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")
EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "")
SMTP_HOST = os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("ALERT_SMTP_PORT", "587"))
SMTP_USER = os.getenv("ALERT_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("ALERT_SMTP_PASSWORD", "")

# Load .env file if present (simple parser, no dependencies)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and not os.getenv(key):
                os.environ[key] = val
    # Re-read after .env load
    SLACK_WEBHOOK = os.getenv("ALERT_SLACK_WEBHOOK", SLACK_WEBHOOK)
    TELEGRAM_TOKEN = os.getenv("ALERT_TELEGRAM_TOKEN", TELEGRAM_TOKEN)
    TELEGRAM_CHAT = os.getenv("ALERT_TELEGRAM_CHAT", TELEGRAM_CHAT)
    EMAIL_TO = os.getenv("ALERT_EMAIL_TO", EMAIL_TO)


# ---------------------------------------------------------------------------
# State management (avoid alerting on every check — only on transitions)
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_status": "unknown", "last_alert_at": None, "consecutive_failures": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_health() -> dict:
    """Hit /health/full and return the response."""
    url = f"{GALLERY_URL}/health/full"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {
            "status": "critical",
            "issues": [f"Gallery server unreachable: {e}"],
            "server": None,
            "relay": None,
            "snapshot": None,
            "td_health": None,
        }
    except Exception as e:
        return {
            "status": "critical",
            "issues": [f"Health check error: {e}"],
            "server": None,
            "relay": None,
            "snapshot": None,
            "td_health": None,
        }


# ---------------------------------------------------------------------------
# Alert formatting
# ---------------------------------------------------------------------------

def format_alert(health: dict, recovered: bool = False) -> str:
    """Format a human-readable alert message."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    if recovered:
        return f"[SSD] Installation RECOVERED at {now}\nAll systems OK."

    issues = health.get("issues", ["Unknown issue"])
    status = health.get("status", "unknown").upper()
    lines = [
        f"[SSD] Installation {status} at {now}",
        "",
        "Issues:",
    ]
    for issue in issues:
        lines.append(f"  - {issue}")

    # Add context
    relay = health.get("relay")
    if relay:
        age = relay.get("last_poll_age_s")
        age_str = f"{age}s ago" if age is not None else "never"
        lines.append(f"\nRelay: {'polling' if relay.get('polling') else 'NOT polling'} "
                      f"(last poll {age_str})")

    snapshot = health.get("snapshot")
    if snapshot:
        age = snapshot.get("last_age_s")
        age_str = f"{age}s ago" if age is not None else "never received"
        lines.append(f"Snapshot: {'fresh' if snapshot.get('fresh') else 'STALE'} "
                      f"(last {age_str})")

    td = health.get("td_health", {})
    report = td.get("report") if td else None
    if report:
        procs = report.get("processes", {})
        for name, running in procs.items():
            lines.append(f"{name}: {'OK' if running else 'DOWN'}")

    lines.append("\nCheck: ssh windows-desktop-remote")
    lines.append(f"Full status: {GALLERY_URL}/health/full")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Alert delivery
# ---------------------------------------------------------------------------

def send_slack(message: str) -> bool:
    if not SLACK_WEBHOOK:
        return False
    try:
        data = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            SLACK_WEBHOOK,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Slack alert failed: {e}", file=sys.stderr)
        return False


def send_telegram(message: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT,
            "text": message,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram alert failed: {e}", file=sys.stderr)
        return False


def send_email(message: str) -> bool:
    if not EMAIL_TO or not EMAIL_FROM:
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(message)
        msg["Subject"] = "[SSD] Installation Health Alert"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            if SMTP_PORT == 587:
                s.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(EMAIL_FROM, EMAIL_TO.split(","), msg.as_string())
        return True
    except Exception as e:
        print(f"Email alert failed: {e}", file=sys.stderr)
        return False


def send_alert(message: str) -> bool:
    """Try all configured alert channels. Return True if any succeeded."""
    sent = False
    if SLACK_WEBHOOK:
        sent = send_slack(message) or sent
    if TELEGRAM_TOKEN and TELEGRAM_CHAT:
        sent = send_telegram(message) or sent
    if EMAIL_TO:
        sent = send_email(message) or sent
    if not sent:
        print(f"WARNING: No alert channel configured or all failed", file=sys.stderr)
        print(message, file=sys.stderr)
    return sent


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    state = _load_state()
    health = check_health()
    status = health.get("status", "unknown")

    now_iso = datetime.now().isoformat()
    prev_status = state.get("last_status", "unknown")

    if status != "ok":
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1

        # Alert on first failure or every 4th consecutive failure (once per hour at 15min intervals)
        should_alert = (
            state["consecutive_failures"] == 1 or
            state["consecutive_failures"] % 4 == 0
        )
        if should_alert:
            message = format_alert(health)
            send_alert(message)
            state["last_alert_at"] = now_iso
            print(f"ALERT sent: {status} ({len(health.get('issues', []))} issues)")

        else:
            print(f"Still unhealthy ({state['consecutive_failures']} consecutive), "
                  f"next alert at {state['consecutive_failures'] + (4 - state['consecutive_failures'] % 4)}")

    else:
        # Recovered — send recovery alert if we were previously failing
        if prev_status != "ok" and state.get("consecutive_failures", 0) > 0:
            message = format_alert(health, recovered=True)
            send_alert(message)
            print("RECOVERY alert sent")

        state["consecutive_failures"] = 0
        print(f"OK — all systems healthy")

    state["last_status"] = status
    state["last_check_at"] = now_iso
    _save_state(state)


if __name__ == "__main__":
    main()
