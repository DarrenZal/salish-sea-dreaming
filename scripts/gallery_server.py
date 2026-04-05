"""
gallery_server.py — FastAPI backend for Salish Sea Dreaming gallery installation.

Receives visitor "offerings" (text prompts) and forwards them via OSC to
TouchDesigner running StreamDiffusion.

Usage:
    python scripts/gallery_server.py
    # or via uvicorn:
    uvicorn gallery_server:app --host 127.0.0.1 --port 8000 --workers 1
"""

import asyncio
import dataclasses
import logging
import os
import secrets
import sys
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiosqlite
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pythonosc import udp_client
from sse_starlette.sse import EventSourceResponse

# ---------------------------------------------------------------------------
# Paths & env
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent  # repo root
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_OSC_PORT = int(os.getenv("TD_OSC_PORT", "7000"))
GALLERY_SERVER_PORT = int(os.getenv("GALLERY_SERVER_PORT", "8000"))
PROMPT_DWELL_SECONDS = int(os.getenv("PROMPT_DWELL_SECONDS", "30"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "20"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "salishsea")
BASE_PROMPT = os.getenv(
    "BASE_PROMPT",
    "brionypenn watercolor painting, soft wet edges, natural pigment washes, "
    "ecological illustration, Salish Sea ecosystem",
)
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "5"))
RATE_LIMIT_BYPASS_KEY = os.getenv("RATE_LIMIT_BYPASS_KEY", "")
DB_PATH = BASE_DIR / "prompts.db"
LOG_DIR = BASE_DIR / "logs"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gallery_server")

# ---------------------------------------------------------------------------
# Blocked words
# ---------------------------------------------------------------------------

BLOCKED_WORDS = [
    "nigger", "faggot", "chink", "spic", "kike", "wetback",
    "penis", "vagina", "fuck", "shit", "cock", "pussy",
    "kill", "rape", "suicide", "murder",
]

# ---------------------------------------------------------------------------
# Prompt enrichment
# ---------------------------------------------------------------------------

BASE_PREFIX = (
    "brionypenn watercolor painting, soft wet edges, natural pigment washes, "
    "ecological illustration, "
)
ECOLOGICAL_SUFFIX = ", Salish Sea, Pacific Northwest, marine ecosystem"
MAX_VISITOR_CHARS = 150


def is_blocked(text: str) -> bool:
    """Return True if text contains any blocked word (case-insensitive)."""
    lower = text.lower()
    return any(w in lower for w in BLOCKED_WORDS)


def enrich_prompt(visitor_text: str) -> str:
    cleaned = visitor_text.strip()[:MAX_VISITOR_CHARS]
    if is_blocked(cleaned):
        cleaned = "the sea dreaming"
    return BASE_PREFIX + cleaned + ECOLOGICAL_SUFFIX


# ---------------------------------------------------------------------------
# OSC client
# ---------------------------------------------------------------------------

osc_client = udp_client.SimpleUDPClient(TD_HOST, TD_OSC_PORT)


def send_osc(address: str, value) -> None:
    try:
        osc_client.send_message(address, value)
        logger.info(f"OSC → {address} : {value!r}")
    except Exception as e:
        logger.warning(f"OSC send failed ({address}): {e}")


# ---------------------------------------------------------------------------
# Queue state
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class PromptItem:
    id: int
    raw_text: str
    enriched_text: str
    display_text: str  # raw_text if not blocked, else "the sea dreaming"
    source: str
    submitted_at: datetime


queue: deque[PromptItem] = deque()
current: Optional[PromptItem] = None
paused: bool = False
dwell_elapsed: float = 0.0

# Rate limiting: {ip: last_submission_timestamp}
rate_limit_map: dict[str, datetime] = {}

# SSE subscriber queues
sse_subscribers: List[asyncio.Queue] = []

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_text TEXT NOT NULL,
    enriched_text TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    source TEXT CHECK(source IN ('typed', 'voice'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(DB_SCHEMA)
        await db.commit()
    logger.info(f"SQLite initialised at {DB_PATH}")


async def insert_prompt(raw_text: str, enriched_text: str, source: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO prompts (raw_text, enriched_text, source) VALUES (?, ?, ?)",
            (raw_text, enriched_text, source),
        )
        await db.commit()
        return cursor.lastrowid


async def update_sent_at(prompt_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE prompts SET sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (prompt_id,),
        )
        await db.commit()


async def fetch_recent_prompts(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, raw_text, enriched_text, submitted_at, source "
            "FROM prompts ORDER BY submitted_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# SSE broadcast
# ---------------------------------------------------------------------------

def make_sse_event(item: PromptItem) -> dict:
    return {
        "id": item.id,
        "display_text": item.display_text,
        "source": item.source,
        "submitted_at": item.submitted_at.isoformat(),
    }


async def broadcast_sse(item: PromptItem) -> None:
    event = make_sse_event(item)
    dead: List[asyncio.Queue] = []
    for q in sse_subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        try:
            sse_subscribers.remove(q)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Queue worker
# ---------------------------------------------------------------------------

async def advance() -> None:
    global current, dwell_elapsed
    current = queue.popleft()
    send_osc("/salish/prompt/visitor", current.enriched_text)
    send_osc("/salish/prompt/weight", 1.0)
    send_osc("/salish/queue/count", len(queue))
    dwell_elapsed = 0
    logger.info(f"Queue advance → prompt id={current.id} source={current.source}")
    await update_sent_at(current.id)


def restore_base() -> None:
    global current
    current = None
    send_osc("/salish/prompt/visitor", BASE_PROMPT)
    send_osc("/salish/queue/count", 0)
    logger.info("Queue empty — restored base prompt")


async def queue_worker() -> None:
    global current, dwell_elapsed
    while True:
        await asyncio.sleep(1.0)
        if paused:
            continue
        dwell_elapsed += 1
        if current is None:
            if queue:
                await advance()
        elif dwell_elapsed >= PROMPT_DWELL_SECONDS:
            if queue:
                await advance()
            else:
                restore_base()


# ---------------------------------------------------------------------------
# Rate limit helper
# ---------------------------------------------------------------------------

def get_client_ip(request: Request) -> str:
    # Cloudflare real IP
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    # X-Forwarded-For (take first)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if client is over the rate limit."""
    # Bypass check
    if RATE_LIMIT_BYPASS_KEY:
        bypass = request.headers.get("X-Rate-Bypass", "")
        if secrets.compare_digest(bypass, RATE_LIMIT_BYPASS_KEY):
            return

    ip = get_client_ip(request)
    now = datetime.utcnow()
    last = rate_limit_map.get(ip)
    if last is not None:
        elapsed = (now - last).total_seconds()
        if elapsed < RATE_LIMIT_SECONDS:
            logger.info(f"Rate limit hit from {ip} ({elapsed:.1f}s since last)")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests — please wait {RATE_LIMIT_SECONDS}s between offerings.",
            )
    rate_limit_map[ip] = now


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Salish Sea Dreaming Gallery Server")
security = HTTPBasic()

# ---------------------------------------------------------------------------
# Admin auth dependency
# ---------------------------------------------------------------------------

def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    username_ok = secrets.compare_digest(credentials.username, "admin")
    password_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=401,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class PromptRequest(BaseModel):
    text: str
    source: str = "typed"


# ---------------------------------------------------------------------------
# API routes (MUST be registered before StaticFiles mount)
# ---------------------------------------------------------------------------

@app.post("/prompt")
async def post_prompt(body: PromptRequest, request: Request):
    global queue

    # Rate limit
    check_rate_limit(request)

    # Validate
    raw = body.text.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Prompt text must not be empty.")

    if body.source not in ("typed", "voice"):
        raise HTTPException(status_code=400, detail="source must be 'typed' or 'voice'.")

    # Determine display text (before enrichment checks for blocking)
    blocked = is_blocked(raw[:MAX_VISITOR_CHARS])
    if blocked:
        logger.info("Blocked word category matched — silently replacing prompt")
        display_text = "the sea dreaming"
    else:
        display_text = raw[:MAX_VISITOR_CHARS]

    enriched = enrich_prompt(raw)

    # Enforce max queue size — drop oldest
    if len(queue) >= MAX_QUEUE_SIZE:
        dropped = queue.popleft()
        logger.info(f"Queue full — dropped oldest prompt id={dropped.id}")

    # Insert into DB
    prompt_id = await insert_prompt(raw, enriched, body.source)

    item = PromptItem(
        id=prompt_id,
        raw_text=raw,
        enriched_text=enriched,
        display_text=display_text,
        source=body.source,
        submitted_at=datetime.utcnow(),
    )
    queue.append(item)
    logger.info(f"Queued prompt id={prompt_id} source={body.source} queue_size={len(queue)}")

    # Broadcast SSE to all listeners
    await broadcast_sse(item)

    return {"status": "queued", "position": len(queue)}


@app.get("/prompts")
async def get_prompts(limit: int = 20):
    limit = min(limit, 50)
    rows = await fetch_recent_prompts(limit)
    result = []
    for r in rows:
        blocked = is_blocked(r["raw_text"][:MAX_VISITOR_CHARS])
        display_text = "the sea dreaming" if blocked else r["raw_text"]
        result.append({
            "id": r["id"],
            "display_text": display_text,
            "source": r["source"],
            "submitted_at": r["submitted_at"],
        })
    return result


@app.get("/prompts/stream")
async def stream_prompts(request: Request):
    subscriber_q: asyncio.Queue = asyncio.Queue(maxsize=50)
    sse_subscribers.append(subscriber_q)

    async def event_generator():
        # Bootstrap: send last 5 prompts immediately
        try:
            recent = await fetch_recent_prompts(5)
            recent.reverse()  # oldest first
            for r in recent:
                blocked = is_blocked(r["raw_text"][:MAX_VISITOR_CHARS])
                display_text = "the sea dreaming" if blocked else r["raw_text"]
                bootstrap_item = PromptItem(
                    id=r["id"],
                    raw_text=r["raw_text"],
                    enriched_text=r.get("enriched_text", ""),
                    display_text=display_text,
                    source=r["source"] or "typed",
                    submitted_at=datetime.fromisoformat(r["submitted_at"])
                    if isinstance(r["submitted_at"], str)
                    else r["submitted_at"],
                )
                yield {"data": __import__("json").dumps(make_sse_event(bootstrap_item))}
        except Exception as e:
            logger.warning(f"SSE bootstrap error: {e}")

        # Stream new events
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(subscriber_q.get(), timeout=15.0)
                    yield {"data": __import__("json").dumps(event)}
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield {"comment": "keepalive"}
        finally:
            try:
                sse_subscribers.remove(subscriber_q)
            except ValueError:
                pass

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    current_text = current.enriched_text if current else BASE_PROMPT
    return {
        "status": "ok",
        "queue_size": len(queue),
        "current_prompt": current_text,
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(_: None = Depends(require_admin)):
    current_display = current.display_text if current else "(none — base prompt active)"
    current_enriched = current.enriched_text if current else BASE_PROMPT
    queue_rows = ""
    for i, item in enumerate(queue):
        queue_rows += (
            f"<tr><td>{i + 1}</td><td>{item.source}</td>"
            f"<td>{item.display_text}</td></tr>\n"
        )
    paused_status = "PAUSED" if paused else "RUNNING"
    pause_btn_label = "Resume" if paused else "Pause"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Salish Sea Dreaming — Admin</title>
<style>
  body {{ font-family: monospace; background: #0a0f1a; color: #a0c4d8; padding: 2rem; }}
  h1 {{ color: #4fc3f7; }}
  h2 {{ color: #80cbc4; margin-top: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #1e3a4a; padding: 0.5rem 1rem; text-align: left; }}
  th {{ background: #0d2035; color: #4fc3f7; }}
  .status {{ font-size: 1.2rem; margin: 0.5rem 0; }}
  .btn {{
    display: inline-block; margin: 0.5rem 0.5rem 0 0;
    padding: 0.5rem 1.2rem; border: none; border-radius: 4px;
    cursor: pointer; font-size: 1rem; font-family: monospace;
  }}
  .btn-pause {{ background: #f57f17; color: #fff; }}
  .btn-clear {{ background: #b71c1c; color: #fff; }}
  form {{ display: inline; }}
</style>
</head>
<body>
<h1>Salish Sea Dreaming — Gallery Admin</h1>

<h2>Status</h2>
<p class="status">State: <strong>{paused_status}</strong></p>
<p class="status">Queue size: <strong>{len(queue)}</strong></p>

<h2>Current Prompt</h2>
<p><em>{current_display}</em></p>
<p style="color:#546e7a;font-size:0.85rem;">{current_enriched}</p>

<h2>Controls</h2>
<form action="/admin/pause" method="post">
  <button class="btn btn-pause" type="submit">{pause_btn_label}</button>
</form>
<form action="/admin/clear" method="post">
  <button class="btn btn-clear" type="submit">Clear Queue</button>
</form>

<h2>Queue ({len(queue)} items)</h2>
<table>
<tr><th>#</th><th>Source</th><th>Visitor text</th></tr>
{queue_rows if queue_rows else '<tr><td colspan="3">Queue is empty</td></tr>'}
</table>
</body>
</html>"""
    return html


@app.post("/admin/pause")
async def admin_pause(_: None = Depends(require_admin)):
    global paused
    paused = not paused
    logger.info(f"Admin toggled paused → {paused}")
    return {"paused": paused}


@app.post("/admin/clear")
async def admin_clear(_: None = Depends(require_admin)):
    global queue
    queue.clear()
    restore_base()
    logger.info("Admin cleared queue")
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Root redirect and visitor alias
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/static/visitor.html")


@app.get("/visitor.html", include_in_schema=False)
async def visitor_redirect():
    return RedirectResponse("/static/visitor.html")


# ---------------------------------------------------------------------------
# Static files (LAST — after all API routes)
# ---------------------------------------------------------------------------

_web_dir = BASE_DIR / "web"
if _web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_web_dir)), name="static")
else:
    logger.warning(f"Static web dir not found at {_web_dir} — /static will not be served")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    LOG_DIR.mkdir(exist_ok=True)
    await init_db()

    # Admin password check
    if not os.getenv("ADMIN_PASSWORD") or ADMIN_PASSWORD == "salishsea":
        logger.warning(
            "WARNING: ADMIN_PASSWORD is unset or using default — "
            "change before exhibition opens"
        )

    # Start background queue worker
    asyncio.create_task(queue_worker())
    logger.info(
        f"Gallery server started — OSC → {TD_HOST}:{TD_OSC_PORT}, "
        f"dwell={PROMPT_DWELL_SECONDS}s, max_queue={MAX_QUEUE_SIZE}"
    )

    # Announce we're up
    send_osc("/salish/prompt/visitor", BASE_PROMPT)
    send_osc("/salish/queue/count", 0)


@app.on_event("shutdown")
async def shutdown():
    send_osc("/salish/prompt/visitor", BASE_PROMPT)
    logger.info("Gallery server shutting down — base prompt restored")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gallery_server:app",
        host="127.0.0.1",
        port=GALLERY_SERVER_PORT,
        reload=False,
        workers=1,
    )
