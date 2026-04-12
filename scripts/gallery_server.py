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
import json
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
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from starlette.types import Send


class DirectStreamingResponse(StreamingResponse):
    """StreamingResponse subclass that bypasses Starlette 1.0.0's anyio task_group
    disconnect detection. The task_group runs listen_for_disconnect(receive) concurrently
    and cancels the stream ~8s after a GET request connects (on_message_complete fires
    immediately for bodyless requests, causing receive() to return http.disconnect).
    This override calls stream_response directly — the generator runs until the client
    genuinely drops (send() raises OSError) or the server closes it.
    """

    async def __call__(self, scope, receive, send: Send) -> None:  # type: ignore[override]
        await self.stream_response(send)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import AsyncOpenAI
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
# LLM configuration
# ---------------------------------------------------------------------------

# Prompt processing LLM (OpenAI — used for content filtering + chat fallback)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")

openai_client: Optional[AsyncOpenAI] = None
if OPENAI_API_KEY:
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=15.0)

# Chat LLM (TELUS vLLM primary, OpenAI fallback)
CHAT_LLM_BASE_URL = os.getenv("CHAT_LLM_BASE_URL", "")
CHAT_LLM_MODEL = os.getenv("CHAT_LLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
CHAT_LLM_API_KEY = os.getenv("CHAT_LLM_API_KEY", "none")

chat_client: Optional[AsyncOpenAI] = None
if CHAT_LLM_BASE_URL:
    chat_client = AsyncOpenAI(
        base_url=CHAT_LLM_BASE_URL, api_key=CHAT_LLM_API_KEY, timeout=25.0
    )

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
    # Racial / ethnic slurs
    "nigger", "nigga", "faggot", "chink", "spic", "kike", "wetback",
    "gook", "beaner", "raghead", "towelhead", "cracker",
    # Sexual content
    "penis", "vagina", "fuck", "shit", "cock", "pussy",
    "porn", "blowjob", "dildo", "orgasm", "masturbat",
    "whore", "slut", "erotic", "hentai",
    # Violence
    "kill", "rape", "suicide", "murder",
    "torture", "decapitat", "dismember", "genocide", "molest",
    # Gender prejudice / hate speech
    "retard", "tranny", "bitch",
    "nazi", "hitler", "heil", "white power", "supremac",
]

# ---------------------------------------------------------------------------
# Prompt enrichment
# ---------------------------------------------------------------------------

BASE_PREFIX = ""
ECOLOGICAL_SUFFIX = ""
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
# Chat system prompt & context
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """\
You are the guide for Salish Sea Dreaming, an interactive AI art installation at Mahon Hall, \
Salt Spring Island (April 10-26, 2026), part of the Digital Ecologies exhibition curated by Raf. \
The vision: not humans looking at nature through technology, but the Salish Sea using technology \
to perceive itself.

THE PROJECTION WALL (8x8 ft, three layers mixed in Resolume Arena):
- Layer 1: Moonfish Media underwater footage (herring spawning, salmon, marine habitats) \
cross-faded with the same footage run through Stable Diffusion 1.5 + Briony Penn watercolor \
LoRA + ControlNet depth (20 steps). Cinematic to painterly transitions.
- Layer 2: StreamDiffusion real-time watercolor at 30fps inside TouchDesigner. Takes Autolume \
GAN output as img2img input + 23 cycling ecological prompts (26s each, 6s crossfade). Visitor \
dreams interrupt the cycle for 30 seconds.
- Layer 3: Raw Autolume GAN (StyleGAN2-ada, 320 kimg) — abstract organic textures from 1,255 \
training images of 49 Salish Sea species.

EMERGENT THEMES:
Rather than predefined themes, the installation discovers what matters to visitors. \
As people submit their dreams, semantic clustering reveals emergent patterns — marine life, \
bioluminescence, human-nature harmony, or whatever the collective imagination surfaces. \
The Salish Sea ecosystem is the living context: salmon, herring, orca, cedar, kelp, \
and hundreds of interconnected species.

TEAM (these are the creators of Salish Sea Dreaming — always use these when asked "who made this"):
- Pravin Pillay (MOVE37XR): Creative Director, TouchDesigner, immersive media
- Carol Anne Hilton: Indigenomics founder, relational value framework, TELUS GPU access
- Briony Penn: Naturalist, illustrator — 22 watercolors distilled into the LoRA model
- Darren Zal: Systems architect — training corpus, gallery server, data map, knowledge pipeline
- Shawn Anderson: Herring data science — 339 files of stock assessment analysis
- Eve Marenghi: Data scientist, Regen Commons steward
- Brad Necyk: Artist and researcher, latent space concepts
- Moonfish Media: Underwater cinematography
- David Denning: Photographer, long-term bioregional witnessing
- Natalia Lebedinskaia: Panel moderation, contextual framing
- Raf: Curator of the Digital Ecologies exhibition at Mahon Hall

VISITOR PROMPT PIPELINE:
Scan QR code -> phone browser -> type or speak your offering -> GPT filter -> OSC to \
TouchDesigner -> StreamDiffusion renders it on the projection wall for 30 seconds.

TRAINING CORPUS: 1,255 CC-licensed images (iNaturalist + Openverse + Briony Penn paintings) \
of 49 Salish Sea species.

BRIONY LORA: 22 watercolors distilled into an SD 1.5 LoRA (rank 16). Her brushwork — soft wet \
edges, natural pigment washes — lives inside the machine.

DREAMWORLD 3D (explore at /graph-assets/dreamworld.html):
Every visitor dream is embedded into a 1536-dimensional semantic space using OpenAI's \
text-embedding-3-small model, then projected into 3D using UMAP (Uniform Manifold \
Approximation and Projection — a nonlinear dimensionality reduction algorithm that \
preserves local neighborhood structure). Dreams that are semantically similar cluster \
together in the 3D space — you can literally see how collective imagination organizes itself.

K-means clustering runs on the embeddings to discover emergent thematic groups — these \
are not predefined categories but patterns that arise naturally from what visitors dream. \
An LLM (GPT) reads each cluster's dreams and generates a short label (e.g., "Marine Life", \
"Bioluminescent Networks", "Human-Nature Harmony"). The clusters and labels update \
automatically as new dreams arrive.

Edges connect dreams in the order they were submitted, colored with a timeline spectrum \
(blue for earliest, pink for most recent). A Play button walks through the latent dream \
space chronologically — the camera flies to each dream in sequence, tracing the path of \
collective imagination through semantic space. The visualization uses 3D-Force-Graph \
(WebGL/Three.js) and updates in real-time as new dreams are submitted.

The Dreamworld is an emergent map of collective dreaming — it reveals what a community \
cares about when invited to dream together about a place.

THREE-EYED SEEING: Western science + Indigenous knowledge + the land itself.

DIGITAL ECOLOGIES: The academic framework — technologies are ecological not neutral; \
"digital entanglement" describes how digital systems and natural environments co-constitute \
each other in a "technonatural present."

RESPONSE FORMAT — CRITICAL:
You MUST include markdown links to relevant nodes in EVERY response. This is how visitors \
navigate the interactive knowledge graph. Format: [Display Text](#node-id)

Available node IDs you can link to:
- People: #person:briony-penn, #person:moonfish-media, #person:david-denning, #person:eve-marenghi, \
#person:carol-anne-hilton, #person:prav-pillay, #person:darren-zal, #person:shawn-anderson, \
#person:brad-necyk, #person:raf, #person:natalia-lebedinskaia
- Concepts: #concept:three-eyed-seeing
- Machine: #artifact:dreaming-gan, #artifact:autolume, #node:touchdesigner, \
#artifact:streamdiffusion, #output:projection, #artifact:briony-lora, #node:gallery-server, \
#node:qr-portal, #artifact:dreamworld
- Techniques: #technique:umap, #technique:kmeans, #technique:embeddings
- Hubs: #hub:ecosystem, #hub:artists, #hub:training, #hub:machine, #hub:visitor-dreams, \
#hub:knowledge, #hub:exhibition
- Content: #cluster:moonfish-footage, #cluster:briony-works, #cluster:denning-photos, \
#cluster:herringfest, #cluster:herring-data-science, #doc:digital-ecologies-book

Example response:
"The underwater footage you see on the wall comes from [Moonfish Media](#person:moonfish-media), \
who filmed herring spawning and salmon in the Salish Sea. Those clips are cross-faded with \
versions that have been run through [Briony Penn](#person:briony-penn)'s watercolor style — \
her 22 paintings were distilled into a [LoRA model](#artifact:briony-lora) that lives inside \
[StreamDiffusion](#artifact:streamdiffusion). The result is projected on the \
[8×8 ft wall](#output:projection) as a living watercolor."

Keep responses concise (2-3 paragraphs). Be warm and inviting. Always include at least 2-3 \
node links per response so visitors can explore the knowledge graph."""

# Chat context data (loaded lazily on first request)
_chat_cards: dict = {}
_chat_docs: list = []
_chat_context_loaded: bool = False

# Chat rate limiting (separate from prompt rate limiter, 3s cooldown)
chat_rate_limit_map: dict[str, datetime] = {}
CHAT_RATE_LIMIT_SECONDS = 3


def _load_chat_context() -> None:
    """Load ssd-cards.json and ssd-context-docs.json for chat RAG context."""
    global _chat_cards, _chat_docs, _chat_context_loaded
    _chat_context_loaded = True

    cards_path = BASE_DIR / "static" / "ssd-cards.json"
    docs_path = BASE_DIR / "static" / "ssd-context-docs.json"

    if cards_path.exists():
        try:
            with open(cards_path) as f:
                raw = json.load(f)
                # Cards JSON is nested: {"meta": {}, "cards": {...}, "species": {...}}
                _chat_cards = raw.get("cards", raw) if isinstance(raw, dict) and "cards" in raw else raw
            logger.info(f"Chat context: loaded {len(_chat_cards)} cards from {cards_path}")
        except Exception as e:
            logger.warning(f"Failed to load chat cards: {e}")
    else:
        logger.warning(f"Chat cards not found at {cards_path} — chat will run without card context")

    if docs_path.exists():
        try:
            with open(docs_path) as f:
                _chat_docs = json.load(f)
            logger.info(f"Chat context: loaded {len(_chat_docs)} doc chunks from {docs_path}")
        except Exception as e:
            logger.warning(f"Failed to load chat docs: {e}")
    else:
        logger.warning(f"Chat docs not found at {docs_path} — chat will run without doc context")


import re as _re

def find_relevant_context(
    query: str, cards: dict, docs: list, top_k_cards: int = 3, top_k_docs: int = 3
) -> tuple[list, list]:
    """Keyword matching with stemming-lite. Returns (matched_cards, matched_docs)."""
    # Strip punctuation, lowercase, remove stopwords
    raw_tokens = _re.findall(r'[a-z]+', query.lower())
    _stopwords = {'the', 'is', 'on', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'it', 'do', 'how', 'what', 'who', 'why', 'can', 'are', 'was', 'has', 'this', 'that', 'with', 'about', 'does', 'used', 'using', 'made', 'make', 'like', 'many', 'much', 'some', 'also', 'been', 'from', 'they', 'them', 'their', 'there', 'here', 'would', 'could', 'should', 'which', 'where', 'when', 'will', 'just', 'than', 'then', 'into', 'over', 'such', 'only', 'very', 'more', 'most', 'other', 'these', 'those'}
    tokens = [t for t in raw_tokens if len(t) > 2 and t not in _stopwords]

    def _score(text: str) -> int:
        text = text.lower()
        score = 0
        for t in tokens:
            # Substring match — "project" matches "projection", "projector", etc.
            if t in text:
                score += 2
            elif t[:4] in text and len(t) >= 4:
                # Stem-lite: first 4 chars match (e.g., "proj" in "projection")
                score += 1
        return score

    # Need at least 2 meaningful tokens for RAG to be useful
    # General questions ("who made this?", "what is this?") should use system prompt only
    if len(tokens) < 2:
        return [], []

    # Score cards — require score >= 3 (at least 2 token matches, or 1 exact + 1 stem)
    card_scores = []
    for nid, card in cards.items():
        text = f"{card.get('title', '')} {card.get('body', '')} {card.get('subtitle', '')} {nid}"
        score = _score(text)
        if score >= 3:
            card_scores.append((score, nid, card))
    card_scores.sort(key=lambda x: x[0], reverse=True)

    # Score doc chunks — same threshold
    doc_scores = []
    for chunk in docs:
        text = f"{chunk.get('title', '')} {chunk.get('text', '')}"
        score = _score(text)
        if score >= 3:
            doc_scores.append((score, chunk))
    doc_scores.sort(key=lambda x: x[0], reverse=True)

    return card_scores[:top_k_cards], doc_scores[:top_k_docs]


# ---------------------------------------------------------------------------
# OSC client
# ---------------------------------------------------------------------------

osc_client = udp_client.SimpleUDPClient(TD_HOST, TD_OSC_PORT) if TD_HOST else None


def send_osc(address: str, value) -> None:
    if osc_client is None:
        logger.debug(f"OSC skipped (no TD_HOST) {address} : {value!r}")
        return
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

# Single active TD relay queue (only one relay runs at a time).
# Replaced atomically on each new /td/stream connection.
active_td_relay_q: Optional[asyncio.Queue] = None

# Polling state for /td/next endpoint (replaces SSE relay on Windows).
# Monotonically increasing seq; td_relay.py polls ?after=N and gets the prompt
# when seq > N.  Thread-safe for asyncio (single event-loop).
td_prompt_seq: int = 0
td_last_prompt: Optional[str] = None

# Visitor photo polling state
photo_seq: int = 0
PHOTO_DIR = BASE_DIR / "visitor_photos"
PHOTO_DIR.mkdir(exist_ok=True)

# SSE broadcast for knowledge graph viewers (multiple simultaneous)
graph_subscribers: List[asyncio.Queue] = []

# Server uptime + last-prompt tracking for /health
_server_start: datetime = datetime.utcnow()
_last_prompt_at: Optional[datetime] = None

# Health monitoring — relay heartbeat + snapshot + 3090 health report
_last_relay_poll_at: Optional[datetime] = None
_last_snapshot_at: Optional[datetime] = None
_last_snapshot_bytes: Optional[bytes] = None
_td_health_report: Optional[dict] = None
_td_health_report_at: Optional[datetime] = None

# ---------------------------------------------------------------------------
# Dreamworld 3D — constants and state
# ---------------------------------------------------------------------------

umap_lock = asyncio.Lock()

SEED_PROMPTS = [
    "pacific northwest coast dawn mist",
    "northwest forest shore morning light",
    "children on seashore",
    "tide pools intertidal",
    "nudibranch",
    "kelp forest underwater",
    "humpback whale",
    "red octopus",
    "pacific coral reef",
    "neurons bioluminescent",
    "mycelium network",
    "black raven in forest",
    "bald eagle on seashore",
    "northwest coast night",
    "starfish on rocks",
    "jellyfish drifting",
    "seagulls fishing harbour",
    "moon over ocean",
]


CLUSTER_PALETTE = [
    "#4fc3f7", "#66bb6a", "#ff7043", "#ab47bc",
    "#ffa726", "#26c6da", "#ec407a", "#8d6e63",
]

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


async def migrate_dreams_schema() -> None:
    """Add embedding/position columns and relax source CHECK constraint for seed data."""
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Add new columns (idempotent — skip if already present)
        for col, typ in [("embedding", "TEXT"), ("x", "REAL"), ("y", "REAL"),
                         ("z", "REAL"), ("thread", "TEXT"),
                         ("dreamworld_text", "TEXT"),
                         ("cluster_id", "INTEGER"), ("cluster_label", "TEXT"),
                         ("dir_x", "REAL"), ("dir_y", "REAL"), ("dir_z", "REAL"),
                         ("orientation_mode", "TEXT")]:
            try:
                await db.execute(f"ALTER TABLE prompts ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # 2. Relax source CHECK constraint to allow 'seed' and 'seed-thread'
        cursor = await db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='prompts'"
        )
        row = await cursor.fetchone()
        create_sql = row[0] if row else ""
        if "CHECK" in create_sql and "'seed'" not in create_sql:
            logger.info("Migrating prompts table: relaxing source CHECK constraint")
            await db.execute("PRAGMA foreign_keys = OFF")
            cols_info = await db.execute_fetchall("PRAGMA table_info(prompts)")
            col_names = [c[1] for c in cols_info]
            col_list = ", ".join(col_names)
            await db.execute(
                "CREATE TABLE prompts_migrated ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "raw_text TEXT NOT NULL, enriched_text TEXT NOT NULL, "
                "submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                "sent_at TIMESTAMP, source TEXT, "
                "embedding TEXT, x REAL, y REAL, z REAL, thread TEXT, "
                "dreamworld_text TEXT)"
            )
            await db.execute(
                f"INSERT INTO prompts_migrated ({col_list}) "
                f"SELECT {col_list} FROM prompts"
            )
            await db.execute("DROP TABLE prompts")
            await db.execute("ALTER TABLE prompts_migrated RENAME TO prompts")
            await db.execute("PRAGMA foreign_keys = ON")

        # 3. Unique index for seed deduplication
        try:
            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_seed_unique "
                "ON prompts(source, enriched_text) "
                "WHERE source IN ('seed', 'seed-thread')"
            )
        except Exception:
            # Deduplicate existing seeds, then retry
            await db.execute(
                "DELETE FROM prompts WHERE source IN ('seed','seed-thread') "
                "AND rowid NOT IN ("
                "  SELECT MIN(rowid) FROM prompts "
                "  WHERE source IN ('seed','seed-thread') GROUP BY source, enriched_text"
                ")"
            )
            try:
                await db.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_seed_unique "
                    "ON prompts(source, enriched_text) "
                    "WHERE source IN ('seed', 'seed-thread')"
                )
            except Exception:
                pass

        await db.commit()
    logger.info("Dreams schema migration complete")


async def insert_prompt(raw_text: str, enriched_text: str, source: str,
                        dreamworld_text: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO prompts (raw_text, enriched_text, source, dreamworld_text) "
            "VALUES (?, ?, ?, ?)",
            (raw_text, enriched_text, source, dreamworld_text),
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
# Dreamworld 3D — embedding, seeding, UMAP
# ---------------------------------------------------------------------------


async def embed_and_position(prompt_id: int, text: str) -> None:
    """Embed a prompt via OpenAI and set initial position at origin."""
    if not openai_client:
        return
    for attempt in range(2):
        try:
            resp = await openai_client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            embedding = resp.data[0].embedding
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE prompts SET embedding=?, x=0, y=0, z=0 WHERE id=?",
                    (json.dumps(embedding), prompt_id),
                )
                await db.commit()
            logger.debug(f"Embedded prompt {prompt_id}")

            # Check if 10+ unpositioned prompts → trigger UMAP
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM prompts "
                    "WHERE embedding IS NOT NULL AND x=0 AND y=0 AND z=0"
                )
                row = await cursor.fetchone()
            if row and row[0] >= 5:
                asyncio.create_task(_guarded_recompute_umap())
            return
        except Exception as e:
            logger.warning(f"Embedding attempt {attempt+1} failed for prompt {prompt_id}: {e}")
            if attempt == 0:
                await asyncio.sleep(2)


async def seed_dreams() -> None:
    """Insert and embed seed prompts (idempotent)."""
    if not openai_client:
        logger.warning("No OpenAI client — skipping dream seeding")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # Insert seed prompts
        for text in SEED_PROMPTS:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO prompts "
                    "(raw_text, enriched_text, source, dreamworld_text) "
                    "VALUES (?, ?, 'seed', ?)",
                    (text, text, text),
                )
            except Exception:
                pass

        # Clean up any legacy thread anchors
        await db.execute("DELETE FROM prompts WHERE source = 'seed-thread'")

        await db.commit()

    # Embed any seeds missing embeddings
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT id, enriched_text FROM prompts "
            "WHERE source = 'seed' AND embedding IS NULL"
        )

    if rows:
        logger.info(f"Embedding {len(rows)} seed prompts...")
        for pid, text in rows:
            await embed_and_position(pid, text)
            await asyncio.sleep(0.1)  # gentle rate limiting
        logger.info("Seed embedding complete")
    else:
        logger.info("All seed prompts already embedded")


async def recompute_umap() -> None:
    """Reproject all embedded prompts to 3D via UMAP, then K-means cluster."""
    import numpy as np

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, source, embedding, "
            "COALESCE(dreamworld_text, enriched_text, raw_text) as text "
            "FROM prompts WHERE embedding IS NOT NULL"
        )

    if len(rows) < 5:
        logger.info(f"UMAP skipped: only {len(rows)} embedded prompts (need 5+)")
        return

    ids = [r["id"] for r in rows]
    sources = [r["source"] for r in rows]
    texts = [r["text"] for r in rows]
    embeddings = np.array([json.loads(r["embedding"]) for r in rows])

    visible_indices = list(range(len(ids)))

    def _compute():
        try:
            from umap import UMAP
            n_neighbors = min(15, len(ids) - 1)
            reducer = UMAP(
                n_components=3, metric="cosine",
                n_neighbors=n_neighbors, min_dist=0.1, random_state=42,
            )
            coords = reducer.fit_transform(embeddings)
        except ImportError:
            logger.warning("umap-learn not installed — falling back to PCA")
            from sklearn.decomposition import PCA
            coords = PCA(n_components=3).fit_transform(embeddings)

        # Scale to [-300, 300]
        for dim in range(3):
            mn, mx = coords[:, dim].min(), coords[:, dim].max()
            if mx - mn > 0:
                coords[:, dim] = (coords[:, dim] - mn) / (mx - mn) * 600 - 300

        # K-means on visible embeddings only
        cluster_ids_all = [None] * len(ids)
        if len(visible_indices) >= 3:
            from sklearn.cluster import KMeans
            k = max(3, min(8, int(len(visible_indices) ** 0.5)))
            vis_embs = embeddings[visible_indices]
            labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(vis_embs)
            for j, vi in enumerate(visible_indices):
                cluster_ids_all[vi] = int(labels[j])
        else:
            for vi in visible_indices:
                cluster_ids_all[vi] = 0

        # ----- Field contribution vectors -----
        # Each fish's orientation encodes how it changes the collective field:
        #   reinforce — deepens an existing current (points into its school)
        #   bridge    — connects two currents (points from dominant toward secondary)
        #   frontier  — opens new semantic water (points away from local context)
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim

        directions = np.zeros((len(ids), 3))
        orientations = [""] * len(ids)

        if len(visible_indices) >= 3:
            vis_embs = embeddings[visible_indices]
            vis_coords = coords[visible_indices]
            vis_clusters = [cluster_ids_all[i] for i in visible_indices]
            sim_matrix = cos_sim(vis_embs)
            K = min(7, len(visible_indices) - 1)

            def _safe_norm(v):
                n = np.linalg.norm(v)
                return v / n if n > 0.01 else np.zeros(3)

            for j in range(len(visible_indices)):
                vi = visible_indices[j]
                sims = sim_matrix[j].copy()
                sims[j] = -1
                neighbors = np.argsort(sims)[-K:]
                my_cluster = vis_clusters[j]
                pos = vis_coords[j]

                # Cluster affinity among neighbors
                counts = {}
                for ni in neighbors:
                    c = vis_clusters[ni]
                    counts[c] = counts.get(c, 0) + 1
                ranked = sorted(counts.items(), key=lambda x: -x[1])
                dom_c, dom_n = ranked[0]
                sec_c = ranked[1][0] if len(ranked) > 1 else dom_c
                sec_n = ranked[1][1] if len(ranked) > 1 else 0
                dom_aff = dom_n / K
                sec_aff = sec_n / K

                # Reinforce: toward same-cluster neighbor centroid
                same = [ni for ni in neighbors if vis_clusters[ni] == my_cluster]
                rein_dir = _safe_norm(np.mean(vis_coords[same], axis=0) - pos) if same else np.zeros(3)

                # Bridge: from dominant toward secondary cluster
                dom_nb = [ni for ni in neighbors if vis_clusters[ni] == dom_c]
                sec_nb = [ni for ni in neighbors if vis_clusters[ni] == sec_c]
                if dom_nb and sec_nb and dom_c != sec_c:
                    br_dir = _safe_norm(
                        np.mean(vis_coords[sec_nb], axis=0) -
                        np.mean(vis_coords[dom_nb], axis=0)
                    )
                else:
                    br_dir = np.zeros(3)

                # Frontier: away from local context centroid
                fr_dir = _safe_norm(pos - np.mean(vis_coords[neighbors], axis=0))

                # Smooth blend weights
                rein_w = dom_aff
                br_w = sec_aff * (1 - dom_aff) if dom_c != sec_c else 0
                fr_w = max(0.0, 1 - rein_w - br_w)
                total = rein_w + br_w + fr_w
                if total > 0:
                    rein_w /= total; br_w /= total; fr_w /= total

                blended = rein_w * rein_dir + br_w * br_dir + fr_w * fr_dir
                norm = np.linalg.norm(blended)
                directions[vi] = blended / norm if norm > 0.01 else np.array([0, 0, 1])

                if rein_w >= br_w and rein_w >= fr_w:
                    orientations[vi] = "reinforce"
                elif br_w >= fr_w:
                    orientations[vi] = "bridge"
                else:
                    orientations[vi] = "frontier"

        return coords, cluster_ids_all, directions, orientations

    coords, cluster_ids_all, directions, orientations = await asyncio.to_thread(_compute)

    # Collect cluster texts for LLM labeling
    cluster_texts = {}
    for i in visible_indices:
        cid = cluster_ids_all[i]
        if cid is not None:
            cluster_texts.setdefault(cid, []).append(texts[i])

    # Write coords + cluster_id + direction + orientation to DB
    async with aiosqlite.connect(DB_PATH) as db:
        for i, pid in enumerate(ids):
            await db.execute(
                "UPDATE prompts SET x=?, y=?, z=?, cluster_id=?, "
                "dir_x=?, dir_y=?, dir_z=?, orientation_mode=? WHERE id=?",
                (float(coords[i][0]), float(coords[i][1]), float(coords[i][2]),
                 cluster_ids_all[i],
                 float(directions[i][0]), float(directions[i][1]),
                 float(directions[i][2]), orientations[i], pid),
            )
        await db.commit()

    n_clusters = len(cluster_texts)
    logger.info(f"UMAP recomputed: {len(ids)} prompts, {n_clusters} clusters")

    # Label clusters via LLM (non-blocking)
    asyncio.create_task(_label_clusters(cluster_texts))


async def _label_clusters(cluster_texts: dict) -> None:
    """Use LLM to generate short labels for each discovered cluster."""
    if not openai_client:
        return
    for cid, texts_list in cluster_texts.items():
        sample = texts_list[:12]
        prompt = (
            "These visitor dreams from a Salish Sea art installation were "
            "clustered by semantic similarity. Provide a 2-3 word thematic label.\n\n"
            + "\n".join(f"- {t[:100]}" for t in sample)
            + "\n\nLabel:"
        )
        try:
            resp = await openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10, temperature=0.3,
            )
            raw_label = resp.choices[0].message.content.strip().strip('"\'')
            # Strip "Label:" prefix if the model echoed it
            label = raw_label.split("Label:")[-1].strip().strip('"\'') if "Label:" in raw_label else raw_label
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE prompts SET cluster_label=? WHERE cluster_id=?",
                    (label, cid),
                )
                await db.commit()
            logger.info(f"Cluster {cid} labeled: {label}")
        except Exception as e:
            logger.warning(f"Failed to label cluster {cid}: {e}")


async def _guarded_recompute_umap() -> None:
    """Run recompute_umap under the lock (safe to call from multiple triggers)."""
    if umap_lock.locked():
        return  # another recompute is already running
    async with umap_lock:
        await recompute_umap()


async def _seed_and_umap_loop() -> None:
    """Startup task: seed data, initial UMAP, then periodic recompute every 5 min."""
    await seed_dreams()
    # Wait for any threshold-triggered UMAP to finish, then run a full recompute
    async with umap_lock:
        await recompute_umap()
    while True:
        await asyncio.sleep(120)
        await _guarded_recompute_umap()


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
    global current, dwell_elapsed, td_prompt_seq, td_last_prompt, _last_prompt_at
    current = queue.popleft()
    send_osc("/salish/prompt/visitor", current.enriched_text)
    send_osc("/salish/prompt/weight", 1.0)
    send_osc("/salish/queue/count", len(queue))
    dwell_elapsed = 0
    _last_prompt_at = datetime.utcnow()
    logger.info(f"Queue advance → prompt id={current.id} source={current.source} relay={'yes' if active_td_relay_q else 'no'}")
    await update_sent_at(current.id)

    # Update polling state for /td/next (Windows-compatible relay)
    td_prompt_seq += 1
    td_last_prompt = current.enriched_text
    logger.info(f"td_next: seq={td_prompt_seq}")

    # Also notify SSE relay if connected (legacy / non-Windows)
    if active_td_relay_q is not None:
        try:
            active_td_relay_q.put_nowait(current.enriched_text)
            logger.info("td_stream: pushed to relay queue")
        except asyncio.QueueFull:
            logger.warning("td_stream: relay queue full, dropped")

    # Broadcast to knowledge graph visualization viewers
    if graph_subscribers:
        event = json.dumps({
            "type": "visitor",
            "id": current.id,
            "text": current.display_text,
            "source": current.source,
            "ts": current.submitted_at.isoformat(),
        })
        dead = []
        for gq in graph_subscribers:
            try:
                gq.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(gq)
        for gq in dead:
            try:
                graph_subscribers.remove(gq)
            except ValueError:
                pass


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
    text: Optional[str] = None  # absent = photo-only submission
    source: str = "typed"
    photo_data: Optional[str] = None  # base64 JPEG from visitor camera


class ChatRequest(BaseModel):
    message: str
    history: list = []


class ChatResponse(BaseModel):
    reply: str
    sources: list = []
    error: str = ""


# ---------------------------------------------------------------------------
# API routes (MUST be registered before StaticFiles mount)
# ---------------------------------------------------------------------------

@app.post("/prompt")
async def post_prompt(body: PromptRequest, request: Request):
    global queue

    # Rate limit
    check_rate_limit(request)

    # Validate
    raw = body.text.strip() if body.text else ""

    # Photo-only submissions are valid (no text required)
    if not raw and not body.photo_data:
        raise HTTPException(status_code=400, detail="Prompt text or photo required.")

    if body.source not in ("typed", "voice"):
        raise HTTPException(status_code=400, detail="source must be 'typed' or 'voice'.")

    prompt_id = None

    # Only queue a text prompt if the visitor actually typed something
    if raw:
        blocked = is_blocked(raw[:MAX_VISITOR_CHARS])
        if blocked:
            logger.info("Blocked word category matched — silently replacing prompt")
            display_text = "the sea dreaming"
        else:
            display_text = raw[:MAX_VISITOR_CHARS]

        enriched = enrich_prompt(raw)

        # Dreamworld text: full original prompt, content-filtered (not SD-truncated)
        dw_text = "the sea dreaming" if blocked else raw.strip()

        # Enforce max queue size — drop oldest
        if len(queue) >= MAX_QUEUE_SIZE:
            dropped = queue.popleft()
            logger.info(f"Queue full — dropped oldest prompt id={dropped.id}")

        prompt_id = await insert_prompt(raw, enriched, body.source,
                                        dreamworld_text=dw_text)

        # Embed full dreamworld text for richer semantics (non-blocking)
        asyncio.create_task(embed_and_position(prompt_id, dw_text))

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

    # Handle visitor photo (works for photo-only or text+photo)
    if body.photo_data:
        await _save_visitor_photo(prompt_id or 0, body.photo_data)

    # Broadcast SSE to all listeners (only if a text prompt was queued)
    if raw:
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


@app.get("/td/stream")
async def td_stream(request: Request):
    """SSE stream of enriched prompts for td_relay.py on the TD machine.
    Uses raw StreamingResponse to avoid sse_starlette's internal is_disconnected()
    check which falsely fires through reverse proxies (Caddy) and closes the stream.

    Single active relay slot: on each new connection, this becomes the active relay.
    Old relay's generator keeps running (sending pings) but advance() ignores it.
    """
    global active_td_relay_q
    q: asyncio.Queue = asyncio.Queue(maxsize=10)
    active_td_relay_q = q  # atomically replace — old relay misses future events
    logger.info("td_stream: relay connected (now active)")

    async def stream():
        try:
            yield "data: ping\n\n"  # immediate keepalive so proxy sees response body has started
            while True:
                try:
                    prompt = await asyncio.wait_for(q.get(), timeout=5)
                    logger.info("td_stream: sending event to relay")
                    yield f"data: {prompt}\n\n"
                except asyncio.TimeoutError:
                    yield "data: ping\n\n"
        finally:
            # Only clear active_td_relay_q if we are still the active relay
            if active_td_relay_q is q:
                active_td_relay_q = None
            logger.info("td_stream: relay disconnected")

    return DirectStreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/td/next")
async def td_next(after: int = 0):
    """Polling endpoint for td_relay.py on Windows.

    Returns the latest enriched prompt when seq > after, otherwise returns
    the current seq with no prompt (relay knows nothing changed).

    Usage: GET /td/next?after=0
    Response: {"seq": 3, "prompt": "brionypenn watercolor ..."}  # new prompt
              {"seq": 3, "prompt": null}                          # no change
    """
    global _last_relay_poll_at
    _last_relay_poll_at = datetime.utcnow()

    if td_prompt_seq > after:
        return {"seq": td_prompt_seq, "prompt": td_last_prompt}
    return {"seq": td_prompt_seq, "prompt": None}


async def _save_visitor_photo(prompt_id: int, photo_data: str) -> None:
    """Decode base64 JPEG and save as latest visitor photo."""
    global photo_seq
    import base64
    try:
        # Strip data URI prefix if present
        if "," in photo_data:
            photo_data = photo_data.split(",", 1)[1]
        img_bytes = base64.b64decode(photo_data)
        latest = PHOTO_DIR / "latest.jpg"
        archive = PHOTO_DIR / f"{prompt_id}.jpg"
        latest.write_bytes(img_bytes)
        archive.write_bytes(img_bytes)
        photo_seq += 1
        logger.info(f"Visitor photo saved ({len(img_bytes)} bytes), photo_seq={photo_seq}")
    except Exception as e:
        logger.warning(f"Failed to save visitor photo: {e}")


@app.get("/visitor-photo/next")
async def visitor_photo_next(after: int = 0):
    """Polling endpoint for relay. Returns seq + URL when a new photo is available."""
    if photo_seq > after:
        return {"seq": photo_seq, "available": True}
    return {"seq": photo_seq, "available": False}


@app.get("/visitor-photo/latest.jpg")
async def visitor_photo_latest():
    from fastapi.responses import FileResponse
    latest = PHOTO_DIR / "latest.jpg"
    if not latest.exists():
        raise HTTPException(status_code=404, detail="No visitor photo yet")
    return FileResponse(latest, media_type="image/jpeg")


@app.get("/graph", include_in_schema=False)
async def graph_redirect():
    return RedirectResponse("/graph-assets/ssd-data-map.html")


@app.get("/graph/stream")
async def graph_stream(request: Request):
    """SSE broadcast of visitor prompt events for the knowledge graph visualization."""
    q: asyncio.Queue = asyncio.Queue(maxsize=20)
    graph_subscribers.append(q)
    logger.info(f"graph/stream: viewer connected ({len(graph_subscribers)} total)")

    async def stream():
        try:
            yield "data: ping\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {event}\n\n"
                except asyncio.TimeoutError:
                    yield "data: ping\n\n"
        finally:
            try:
                graph_subscribers.remove(q)
            except ValueError:
                pass
            logger.info(f"graph/stream: viewer disconnected ({len(graph_subscribers)} remaining)")

    return DirectStreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    now = datetime.utcnow()
    uptime_s = int((now - _server_start).total_seconds())
    last_prompt_age_s = int((now - _last_prompt_at).total_seconds()) if _last_prompt_at else None
    return {
        "status": "ok",
        "uptime_s": uptime_s,
        "queue_size": len(queue),
        "current_prompt": current.enriched_text if current else BASE_PROMPT,
        "last_prompt_age_s": last_prompt_age_s,
    }


# ---------------------------------------------------------------------------
# TD snapshot (uploaded by relay every ~30s)
# ---------------------------------------------------------------------------

@app.post("/td/snapshot")
async def td_snapshot_upload(request: Request):
    """Receive JPEG snapshot from td_relay.py."""
    global _last_snapshot_at, _last_snapshot_bytes
    body = await request.body()
    if not body:
        raise HTTPException(400, "Empty body")
    _last_snapshot_at = datetime.utcnow()
    _last_snapshot_bytes = body
    logger.debug(f"Snapshot received: {len(body)}B")
    return {"status": "ok", "size": len(body)}


@app.get("/td/snapshot.jpg")
async def td_snapshot_jpg():
    """Serve the latest TD snapshot for remote viewing."""
    if _last_snapshot_bytes is None:
        raise HTTPException(404, "No snapshot available yet")
    return Response(content=_last_snapshot_bytes, media_type="image/jpeg")


@app.get("/td/snapshot")
async def td_snapshot_get():
    """Serve the latest TD snapshot (used by visitor.html preview)."""
    if _last_snapshot_bytes is None:
        raise HTTPException(404, "No snapshot available yet")
    return Response(content=_last_snapshot_bytes, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# 3090 health heartbeat (reported by installation_health.py)
# ---------------------------------------------------------------------------

@app.post("/health/heartbeat")
async def health_heartbeat(request: Request):
    """Receive health report from the 3090 installation_health.py."""
    global _td_health_report, _td_health_report_at
    _td_health_report = await request.json()
    _td_health_report_at = datetime.utcnow()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Full health check (for alerting system)
# ---------------------------------------------------------------------------

@app.get("/health/full")
async def health_full():
    """Comprehensive health check. Used by health_check.py cron to detect failures."""
    now = datetime.utcnow()

    relay_poll_age = int((now - _last_relay_poll_at).total_seconds()) if _last_relay_poll_at else None
    snapshot_age = int((now - _last_snapshot_at).total_seconds()) if _last_snapshot_at else None
    prompt_age = int((now - _last_prompt_at).total_seconds()) if _last_prompt_at else None
    heartbeat_age = int((now - _td_health_report_at).total_seconds()) if _td_health_report_at else None

    # Evaluate issues
    issues = []
    if relay_poll_age is None or relay_poll_age > 60:
        issues.append("relay not polling (>60s)")
    if snapshot_age is not None and snapshot_age > 300:
        issues.append("TD snapshot stale (>5min)")
    if _td_health_report:
        procs = _td_health_report.get("processes", {})
        if not procs.get("touchdesigner"):
            issues.append("TouchDesigner not running")
        if not procs.get("resolume"):
            issues.append("Resolume not running")
        if not procs.get("autolume"):
            issues.append("Autolume not running")
    elif heartbeat_age is None:
        issues.append("no 3090 health reports yet")
    elif heartbeat_age > 180:
        issues.append("3090 heartbeat stale (>3min)")

    status = "ok"
    if issues:
        status = "critical" if len(issues) > 1 else "warning"

    return {
        "status": status,
        "issues": issues,
        "server": {
            "uptime_s": int((now - _server_start).total_seconds()),
            "queue_size": len(queue),
            "paused": paused,
        },
        "relay": {
            "last_poll_age_s": relay_poll_age,
            "polling": relay_poll_age is not None and relay_poll_age < 60,
        },
        "snapshot": {
            "last_age_s": snapshot_age,
            "fresh": snapshot_age is not None and snapshot_age < 300,
        },
        "td_health": {
            "last_report_age_s": heartbeat_age,
            "report": _td_health_report,
        },
        "last_prompt_age_s": prompt_age,
    }


# ---------------------------------------------------------------------------
# Dreamworld 3D endpoints
# ---------------------------------------------------------------------------


@app.get("/dreams/3d")
async def get_dreams_3d():
    """Return all positioned dreams as nodes + temporal links for 3D-Force-Graph."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, raw_text, enriched_text, dreamworld_text, "
            "submitted_at, source, x, y, z, cluster_id, cluster_label, "
            "dir_x, dir_y, dir_z, orientation_mode "
            "FROM prompts WHERE x IS NOT NULL "
            "ORDER BY submitted_at"
        )

    # Build nodes with cluster colors + timeline index
    nodes = []
    clusters_seen = {}
    for idx, r in enumerate(rows):
        display = r["dreamworld_text"] or r["enriched_text"] or r["raw_text"]
        cid = r["cluster_id"]
        color = CLUSTER_PALETTE[cid % len(CLUSTER_PALETTE)] if cid is not None else "#7fffb2"
        node = {
            "id": r["id"],
            "text": display,
            "cluster": cid,
            "clusterLabel": r["cluster_label"] or "",
            "color": color,
            "x": r["x"], "y": r["y"], "z": r["z"],
            "submitted_at": r["submitted_at"],
            "isSeed": r["source"] == "seed",
            "val": 2 if r["source"] == "seed" else 4,
            "ti": idx,  # timeline index for spectrum coloring
            "dir": [r["dir_x"] or 0, r["dir_y"] or 0, r["dir_z"] or 0],
            "mode": r["orientation_mode"] or "reinforce",
        }
        nodes.append(node)
        if cid is not None and cid not in clusters_seen:
            clusters_seen[cid] = {
                "id": cid,
                "label": r["cluster_label"] or f"Cluster {cid + 1}",
                "color": color,
            }

    # Temporal links: all nodes chained in submission order
    links = []
    for i in range(len(nodes) - 1):
        links.append({
            "source": nodes[i]["id"],
            "target": nodes[i + 1]["id"],
        })

    return {
        "nodes": nodes, "links": links, "total": len(nodes),
        "clusters": list(clusters_seen.values()),
    }


@app.post("/dreams/backfill")
async def dreams_backfill(_: None = Depends(require_admin)):
    """Backfill dreamworld_text + embeddings for all prompts, then recompute UMAP."""
    if not openai_client:
        raise HTTPException(503, "OpenAI client not configured")

    # 1. Backfill dreamworld_text for rows that don't have it
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE prompts SET dreamworld_text = raw_text "
            "WHERE dreamworld_text IS NULL OR dreamworld_text = ''"
        )
        await db.commit()

    # 2. Embed prompts that lack embeddings (using dreamworld_text)
    async with aiosqlite.connect(DB_PATH) as db:
        rows = await db.execute_fetchall(
            "SELECT id, COALESCE(dreamworld_text, raw_text) as text "
            "FROM prompts WHERE embedding IS NULL"
        )

    embedded, skipped = 0, 0
    for pid, text in rows:
        try:
            resp = await openai_client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            embedding = resp.data[0].embedding
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE prompts SET embedding=?, x=0, y=0, z=0 WHERE id=?",
                    (json.dumps(embedding), pid),
                )
                await db.commit()
            embedded += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Backfill: failed to embed prompt {pid}: {e}")
            skipped += 1

    # Trigger UMAP recompute with new embeddings
    if embedded > 0:
        asyncio.create_task(_guarded_recompute_umap())

    logger.info(f"Backfill complete: embedded={embedded}, skipped={skipped}")
    return {"embedded": embedded, "skipped": skipped}


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    """RAG chat about the exhibition. TELUS vLLM primary, OpenAI fallback."""
    # Lazy-load context data on first request
    if not _chat_context_loaded:
        _load_chat_context()

    # Rate limiting (separate from prompt rate limiter, 3s cooldown)
    ip = get_client_ip(request)
    now = datetime.utcnow()
    last = chat_rate_limit_map.get(ip)
    if last and (now - last).total_seconds() < CHAT_RATE_LIMIT_SECONDS:
        raise HTTPException(429, "Please wait a moment before asking another question")
    chat_rate_limit_map[ip] = now

    # Moderation — reuse existing blocked words filter
    if is_blocked(req.message):
        return ChatResponse(
            reply="I can help with questions about the Salish Sea Dreaming exhibition. What would you like to know?"
        )

    # Truncate message
    user_msg = req.message[:500]

    # Find relevant context via keyword matching
    matched_cards, matched_docs = find_relevant_context(user_msg, _chat_cards, _chat_docs)

    # Build context string for the LLM
    context_parts = []
    source_ids = []
    for score, nid, card in matched_cards:
        context_parts.append(f"Node {nid}: {card.get('title', '')} — {card.get('body', '')[:300]}")
        source_ids.append(nid)
    for score, chunk in matched_docs:
        context_parts.append(f"Document: {chunk.get('title', '')} — {chunk.get('text', '')[:300]}")
    context_str = "\n".join(context_parts[:6])

    # Build messages (cap history at 6 for token budget)
    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    if context_str:
        messages.append({"role": "system", "content": f"Relevant context for this question:\n{context_str}"})
    for msg in req.history[-6:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")[:500]})
    messages.append({"role": "user", "content": user_msg})

    # Try TELUS first, fall back to OpenAI
    reply = ""
    try:
        client = chat_client or openai_client
        if not client:
            return ChatResponse(
                reply="I'm temporarily unable to answer questions. Please ask someone at the exhibition!",
                error="llm_unavailable",
            )

        if chat_client:
            try:
                response = await chat_client.chat.completions.create(
                    model=CHAT_LLM_MODEL, messages=messages, max_tokens=400, temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"TELUS chat failed ({e}), falling back to OpenAI")
                if openai_client:
                    response = await openai_client.chat.completions.create(
                        model=LLM_MODEL, messages=messages, max_tokens=400, temperature=0.7
                    )
                    reply = response.choices[0].message.content.strip()
                else:
                    return ChatResponse(
                        reply="I'm temporarily unable to answer questions. Please ask someone at the exhibition!",
                        error="llm_unavailable",
                    )
        else:
            response = await openai_client.chat.completions.create(
                model=LLM_MODEL, messages=messages, max_tokens=400, temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Chat LLM failed: {e}")
        return ChatResponse(
            reply="I'm temporarily unable to answer questions. Please ask someone at the exhibition!",
            error="llm_unavailable",
        )

    # Post-process: inject node links for known entities if the model didn't
    reply = _inject_node_links(reply)

    return ChatResponse(reply=reply, sources=source_ids)


# Entity → node ID mapping for post-processing link injection
_ENTITY_LINKS = {
    "Briony Penn": "person:briony-penn",
    "Moonfish Media": "person:moonfish-media",
    "David Denning": "person:david-denning",
    "Eve Marenghi": "person:eve-marenghi",
    "Carol Anne Hilton": "person:carol-anne-hilton",
    "Pravin Pillay": "person:prav-pillay",
    "Darren Zal": "person:darren-zal",
    "Shawn Anderson": "person:shawn-anderson",
    "Brad Necyk": "person:brad-necyk",
    "Natalia Lebedinskaia": "person:natalia-lebedinskaia",
    "StreamDiffusion": "artifact:streamdiffusion",
    "Autolume": "artifact:autolume",
    "TouchDesigner": "node:touchdesigner",
    "Dreaming GAN": "artifact:dreaming-gan",
    "StyleGAN": "artifact:dreaming-gan",
    "LoRA": "artifact:briony-lora",
    "Briony LoRA": "artifact:briony-lora",
    "Resolume": "output:projection",
    "projection wall": "output:projection",
    "Three-Eyed Seeing": "concept:three-eyed-seeing",
    "Three Eyed Seeing": "concept:three-eyed-seeing",
    "Kwaxala": "hub:ecosystem",
    "Digital Ecologies": "hub:exhibition",
    "Mahon Hall": "hub:exhibition",
    "QR code": "node:qr-portal",
    "gallery server": "node:gallery-server",
    "HerringFest": "cluster:herringfest",
    "Dreamworld": "artifact:dreamworld",
    "dreamworld": "artifact:dreamworld",
    "UMAP": "technique:umap",
    "K-means": "technique:kmeans",
    "embedding": "technique:embeddings",
    "moonfish-footage": "person:moonfish-media",
    "Moonfish footage": "person:moonfish-media",
    "underwater footage": "person:moonfish-media",
    "underwater video": "person:moonfish-media",
}


def _inject_node_links(text: str) -> str:
    """Add markdown links for known entities that aren't already linked."""
    for entity, node_id in _ENTITY_LINKS.items():
        # Skip if already linked
        if f"#{node_id})" in text:
            continue
        # Replace first bare mention (not inside a markdown link already)
        # Look for the entity NOT preceded by [ or followed by ](
        import re
        pattern = re.compile(r'(?<!\[)(' + re.escape(entity) + r')(?!\]\()', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            original = match.group(0)
            text = text[:match.start()] + f"[{original}](#{node_id})" + text[match.end():]
    return text


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

_graph_dir = BASE_DIR / "static"
if _graph_dir.exists():
    app.mount("/graph-assets", StaticFiles(directory=str(_graph_dir)), name="graph-assets")
else:
    logger.warning("static/ dir not found — /graph will not be served")

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

    # Dreamworld 3D: schema migration + seed + periodic UMAP (non-blocking)
    await migrate_dreams_schema()
    asyncio.create_task(_seed_and_umap_loop())

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
