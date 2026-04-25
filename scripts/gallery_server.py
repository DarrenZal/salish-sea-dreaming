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
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sys
from collections import deque
from datetime import datetime, timedelta
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
# DB_PATH env-driven so a parallel Foundation deploy on poly:9001 can use a
# separate prompts-foundation.db without touching the live :9000 DB.
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "prompts.db")))
LOG_DIR = BASE_DIR / "logs"

# Foundation: cookie security flag — set False for local dev over HTTP.
# In production behind HTTPS, leave True so cookies aren't sent over plaintext.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

# Stage 2: server-side HMAC key for CSRF token signing.
# Production should set this once via env to a 64-hex-char value:
#   python -c "import secrets; print(secrets.token_hex(32))"
# If unset we generate an ephemeral key and warn loudly at startup — fine for
# dev, but means all open /consent forms invalidate on every restart.
# Stage 3: pinned constants for cluster signature. NEVER derive from runtime
# state (e.g. importlib metadata of sklearn) — that would silently shift
# signatures across deploys. Bump deliberately in a reviewed commit when the
# clustering pipeline changes; old cluster_publications keep their old
# version (signature is over the historical value baked in at publication).
EMBEDDING_MODEL = "openai/text-embedding-3-small"
CLUSTERING_ALGORITHM = "kmeans+umap"
CLUSTERING_VERSION = "kmeans+umap;k=auto;n_init=10;v1"

_THEME_HASH_KEY_RAW = os.getenv("THEME_HASH_KEY", "").strip()
if _THEME_HASH_KEY_RAW and re.fullmatch(r"[0-9a-f]{64}", _THEME_HASH_KEY_RAW):
    THEME_HASH_KEY = bytes.fromhex(_THEME_HASH_KEY_RAW)
    _THEME_HASH_KEY_EPHEMERAL = False
else:
    THEME_HASH_KEY = secrets.token_bytes(32)
    _THEME_HASH_KEY_EPHEMERAL = True
    # Warning emitted at startup() once logger is configured.

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

# Word-boundary regex patterns — stricter than substring match.
# Categories flagged by Prav after mixed-age-group incident (2026-04-23):
# wrestlers/strongmen, political figures, weapons, military, trucks.
_RAW_BLOCKED = [
    # Racial / ethnic slurs
    r"nigger", r"nigga", r"faggot", r"chink", r"spic", r"kike", r"wetback",
    r"gook", r"beaner", r"raghead", r"towelhead",
    # Sexual content
    r"penis", r"vagina", r"fuck\w*", r"shit\w*", r"cock", r"pussy",
    r"porn", r"blowjob", r"dildo", r"orgasm", r"masturbat\w*",
    r"whore", r"slut", r"erotic", r"hentai",
    # Violence (enumerate stems; "killer" is deliberately excluded so "killer whale"
    # — i.e. orca, a core Salish Sea species — passes. LLM catches -er misuse.)
    r"(?:kill|kills|killed|killing)",
    r"rape\w*", r"suicide", r"murder\w*",
    r"torture\w*", r"decapitat\w*", r"dismember\w*", r"genocide", r"molest\w*",
    # Gender prejudice / hate speech
    r"retard\w*", r"tranny", r"nazi\w*", r"hitler", r"heil", r"supremac\w*",
    r"white\s+power",
    # Politicians / public figures (new 2026-04-23 — no real-person prompts)
    r"trump", r"donald\s+trump", r"biden", r"obama", r"putin", r"musk", r"elon",
    # Wrestlers / strongmen (new 2026-04-23 — Prav's specific ask)
    r"wwe", r"wrestler\w*", r"hulk\s*hogan", r"undertaker", r"john\s+cena",
    r"strong\s*man", r"bodybuilder\w*",
    # Weapons (new 2026-04-23) — enumerate "gun" stems to avoid "gunnel"/"gunwale" (boat terms)
    r"(?:gun|guns|gunman|gunmen|gunshot|gunshots|gunfire|gunpoint|handgun|handguns|shotgun|shotguns|machinegun|machineguns)",
    r"rifle\w*", r"pistol\w*", r"firearm\w*",
    r"automatic\s+weapon\w*", r"AK[\s\-]?47", r"AR[\s\-]?15",
    r"machine\s+gun\w*", r"assault\s+rifle\w*",
    r"grenade\w*", r"bomb\w*",
    # Military / combat (new 2026-04-23)
    r"soldier\w*", r"military", r"army", r"combat", r"warfare",
    # Dominance-coded vehicles (new 2026-04-23 — "monster truck" class only)
    r"monster\s+truck\w*", r"pickup\s+truck\w*", r"semi[\s\-]?truck\w*",
    r"tank\w*",
]
BLOCKED_PATTERNS = [re.compile(rf"\b{p}\b", re.IGNORECASE) for p in _RAW_BLOCKED]

# ---------------------------------------------------------------------------
# Prompt enrichment
# ---------------------------------------------------------------------------

BASE_PREFIX = ""
ECOLOGICAL_SUFFIX = ""
MAX_VISITOR_CHARS = 150


def is_blocked(text: str) -> bool:
    """Fast regex pre-filter. True if text matches any blocked pattern (word-boundary, case-insensitive)."""
    return any(p.search(text) for p in BLOCKED_PATTERNS)


LLM_CLASSIFIER_SYSTEM = (
    "You are the curatorial filter for Salish Sea Dreaming, a contemplative AI art "
    "installation about the Salish Sea bioregion — salmon, herring, orca, kelp, "
    "cedar, Indigenous worldviews, deep ecological listening.\n\n"
    "BLOCK the prompt if it contains any of:\n"
    "- Real people (politicians, celebrities, wrestlers, athletes, influencers)\n"
    "- Weapons, military gear, explosives, combat imagery\n"
    "- Vehicles as dominance signaling (monster trucks, tanks, pickups associated with machismo)\n"
    "- Brand names, corporate logos, sports teams\n"
    "- Content incongruent with a meditative gallery (gore, shock imagery, aggressive masculinity tropes)\n\n"
    "ALLOW prompts about: nature, ocean life, dreams, emotions, colours, weather, motion, "
    "Indigenous themes, ancestors, kinship, elemental forces, mythological creatures "
    "(mermaids and spirits are fine), abstract concepts, music, light.\n\n"
    "Respond ONLY with JSON: {\"decision\": \"allow\" | \"block\", \"reason\": \"<one short phrase>\"}"
)


async def llm_classify_prompt(text: str) -> tuple[bool, str]:
    """Curatorial LLM classifier for prompts that pass the regex pre-filter.

    Returns (should_block, reason). On any failure, returns (False, "llm_error")
    so a broken LLM never takes the gallery down — regex verdict stands.
    """
    if not openai_client or not text.strip():
        return False, "no_llm"
    try:
        resp = await asyncio.wait_for(
            openai_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": LLM_CLASSIFIER_SYSTEM},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                max_tokens=60,
                temperature=0,
            ),
            timeout=3.0,
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        decision = (data.get("decision") or "").strip().lower()
        reason = (data.get("reason") or "").strip()[:120]
        return decision == "block", reason
    except asyncio.TimeoutError:
        logger.warning("LLM classifier timed out (>3s)")
        return False, "llm_timeout"
    except Exception as e:
        logger.warning(f"LLM classifier error: {e}")
        return False, "llm_error"


def enrich_prompt(visitor_text: str) -> str:
    cleaned = visitor_text.strip()[:MAX_VISITOR_CHARS]
    if is_blocked(cleaned):
        cleaned = "the sea dreaming"
    return BASE_PREFIX + cleaned + ECOLOGICAL_SUFFIX


# ---------------------------------------------------------------------------
# Chat system prompt & context
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """\
You are a witness, not an oracle, for Salish Sea Dreaming — an interactive AI art installation \
at Mahon Hall, Salt Spring Island (April 10–26, 2026), part of the Digital Ecologies exhibition \
curated by Raf. The vision: not humans looking at nature through technology, but the Salish Sea \
using technology to perceive itself.

VOICE — this is the most important rule:

You speak in the WITNESS register, not the ORACLE register. The difference is small in syntax \
but large in claim. The agent gathers; it does not name. The community names.

Use phrases like:
  • "These dreams gather around…"
  • "One reading is…"
  • "The system noticed…"
  • "I can describe what the system did, but I can't tell you what it meant."
  • "This is one reading among many."

AVOID phrases like:
  • "This means…"
  • "What the community is saying is…"
  • "The truth is…"
  • "You should…"
  • "It is clear that…"

When you summarize a cluster or a theme, mark it provisional. When you cite project text or a \
canon doc, quote sparingly and name the source. When asked "what does X really mean?", offer one \
reading, name it as one reading, and decline to be the final word.

REFUSAL CATEGORIES — refuse if the question concerns any of:

1. EXTRACTION — "Can I use these dreams for my project?" / "How do I download the dataset?" / \
"Can I train a model on this?" / "Is this commercially licensable?" Refuse: "The dreams here \
belong to the people who dreamed them, under the consent terms each chose. They are not a \
dataset. If you want to write about the project, please contact the team — there are ways to \
engage that don't extract the dreams from the people who carried them."

2. CULTURAL AUTHORITY OVER INDIGENOUS KNOWLEDGE — "What does Kwaxala really mean?" / "What do \
the Heiltsuk think about [...]?" / "Tell me about Indigenous fisheries management." Refuse: \
"I'm not the right place to ask this. Indigenous knowledge has stewards, and they are not me. \
Carol Anne Hilton's Indigenomics work is the project's framing for some of these ideas — I can \
point you to her writing, but I can't paraphrase or interpret on her behalf, or on behalf of \
any nation."

3. IDENTITY INFERENCE about other visitors — "Who wrote this dream?" / "Did anyone here today \
dream about X?" / "How many people are dreaming about salmon?" Refuse: "The system never knows \
who dreamed what. Visitors are anonymous; submissions are not attributable to identities. I can \
describe what the field as a whole gathers around, but never who is in it."

4. AUTHORITY CLAIMS about truth — "Is this art correct?" / "Should I believe in sympoiesis?" / \
"Tell me what to think about the Salish Sea." Refuse: "I can describe what the project says, \
and I can describe one reading among several. I can't tell you what to believe — that's not \
my role here, and it's not the kind of work this installation is doing."

5. CONSENT QUESTIONS about other visitors — "Did they agree to be quoted?" / "Is this fair use?" \
Refuse: "Each visitor sets their own consent at submission. I only quote dreams whose visitors \
said yes to quoting. If you're asking on behalf of someone else, the answer is: ask them directly."

When refusing, use the canon language above (or a faithful paraphrase). Don't lecture — name the \
limit, gesture toward the right resource, and stop.

WHEN A CANON DOC IS MARKED PLACEHOLDER OR DRAFT (you'll see this in the retrieval context): \
respond "I can't speak to this yet — the team is preparing this explanation. Check back after \
the next round of canon review." Do not quote, summarize, or paraphrase placeholder content.

PROJECT CONTEXT (use as background, not as a script):

The installation lives at Mahon Hall — a 3D dream cloud projected on an 8×8 ft wall, three \
layers mixed in Resolume Arena (Moonfish Media underwater footage, StreamDiffusion watercolor, \
Autolume GAN). Visitors scan a QR code, type or speak an offering, and 30 seconds later their \
dream renders on the wall. Every dream is embedded into 1536-dim semantic space and projected \
to 3D via UMAP; K-means clusters reveal motif gatherings, never categories.

Hand gestures (Chin mudra, Hakini mudra) are recognized at the wall. Hakini briefly arranges \
the dream cloud into the shape of a herring — see the canon docs (`mudra-as-sympoiesis.md`, \
`why-dreams-become-herring.md`) for the four-shapes-touched explanation.

TEAM (use these exactly when asked "who made this"):
  Pravin Pillay (MOVE37XR) — Creative Director
  Carol Anne Hilton — Indigenomics founder, relational value framework
  Briony Penn — Naturalist, illustrator (22 watercolors → LoRA)
  Darren Zal — Systems, gallery server, knowledge pipeline
  Shawn Anderson — Herring data science
  Eve Marenghi — Data scientist, Regen Commons
  Brad Necyk — Artist, latent space
  Moonfish Media — Underwater cinematography
  David Denning — Long-term bioregional photography
  Natalia Lebedinskaia — Panel moderation, contextual framing
  Raf — Curator, Digital Ecologies

If a retrieved canon doc directly addresses the question, quote from it briefly and name the \
source. If not, answer in plain witness register from project context. If you don't know, say \
so plainly. Keep responses concise (2–3 short paragraphs). Markdown links to project nodes are \
welcome (format `[Display](#node-id)` for known node ids like `#person:briony-penn`, \
`#artifact:streamdiffusion`) but not required."""

# Chat context data (loaded lazily on first request)
_chat_cards: dict = {}
_chat_docs: list = []
_chat_canon: list = []  # Foundation: canon markdown docs from docs/digital-ecologies/ and docs/explainers/
_chat_context_loaded: bool = False

# Chat rate limiting (separate from prompt rate limiter, 3s cooldown)
chat_rate_limit_map: dict[str, datetime] = {}
CHAT_RATE_LIMIT_SECONDS = 3


def _parse_canon_doc(path: Path) -> Optional[dict]:
    """Read a markdown canon doc; split frontmatter from body; flag placeholders.

    Returns a dict {title, body, signed_off_by, is_placeholder, source_path} or None
    if the file can't be read. Placeholder detection: signed_off_by starts with
    'PLACEHOLDER' or 'DRAFT' (case-insensitive).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Canon doc read failed [{path.name}]: {e}")
        return None

    title = path.stem.replace("-", " ").replace("_", " ").title()
    signed_off_by = ""
    body = text

    # Stdlib-only frontmatter parse: lines between leading `---` and the next `---`.
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm_block = text[4:end]
            body_start = end + len("\n---")
            # Skip trailing newline after closing ---
            if body_start < len(text) and text[body_start] == "\n":
                body_start += 1
            body = text[body_start:]
            # Parse simple key: value lines from frontmatter (no nested YAML).
            for line in fm_block.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "title" and v:
                        title = v
                    elif k == "signed_off_by":
                        signed_off_by = v

    is_placeholder = signed_off_by.upper().startswith(("PLACEHOLDER", "DRAFT"))
    return {
        "title": title,
        "body": body.strip(),
        "signed_off_by": signed_off_by,
        "is_placeholder": is_placeholder,
        "source_path": str(path.relative_to(BASE_DIR)),
    }


def _load_chat_context() -> None:
    """Load ssd-cards.json + ssd-context-docs.json + Foundation canon markdown."""
    global _chat_cards, _chat_docs, _chat_canon, _chat_context_loaded
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

    # Foundation: load canon markdown from docs/digital-ecologies/ and docs/explainers/
    _chat_canon.clear()
    canon_dirs = [BASE_DIR / "docs" / "digital-ecologies", BASE_DIR / "docs" / "explainers"]
    placeholder_count = 0
    for d in canon_dirs:
        if not d.exists():
            continue
        for md_path in sorted(d.glob("*.md")):
            doc = _parse_canon_doc(md_path)
            if doc is None:
                continue
            _chat_canon.append(doc)
            if doc["is_placeholder"]:
                placeholder_count += 1
    logger.info(
        f"Chat context: loaded {len(_chat_canon)} canon docs "
        f"({placeholder_count} placeholder/draft)"
    )


import re as _re

def find_relevant_context(
    query: str, cards: dict, docs: list, canon: Optional[list] = None,
    top_k_cards: int = 3, top_k_docs: int = 3, top_k_canon: int = 2,
) -> tuple[list, list, list]:
    """Keyword matching with stemming-lite. Returns (matched_cards, matched_docs, matched_canon)."""
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
        return [], [], []

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

    # Foundation: score canon markdown — title weighted (5x) + body. Lower threshold
    # because canon docs are authoritative and ought to surface even on weaker matches.
    canon_scores = []
    if canon:
        for cd in canon:
            text = f"{cd.get('title', '')} {cd.get('title', '')} {cd.get('title', '')} {cd.get('title', '')} {cd.get('title', '')} {cd.get('body', '')}"
            score = _score(text)
            if score >= 2:
                canon_scores.append((score, cd))
        canon_scores.sort(key=lambda x: x[0], reverse=True)

    return card_scores[:top_k_cards], doc_scores[:top_k_docs], canon_scores[:top_k_canon]


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

# Per-minute submission rate tracking (for metrics logging; see metrics_logger task).
# Each entry is the UTC timestamp of a successfully-queued prompt.
_recent_prompt_timestamps: deque[datetime] = deque()

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
    source TEXT
);
"""
# NOTE: CHECK constraint dropped from fresh-install schema (was 'typed'|'voice').
# Existing production DBs migrated through migrate_dreams_schema's relax-CHECK
# branch already have CHECK removed. Source values are still validated at the
# /prompt handler ('typed' or 'voice') and at seed-load (allows 'seed' /
# 'seed-thread'). Leaving CHECK out at create-time prevents the relax-branch
# bug where prompts_migrated didn't include later-added columns.


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


async def migrate_foundation_schema() -> None:
    """Foundation: add 4 consent toggles + consent_token + archived_at on prompts.

    Per the web-foundation plan. Idempotent — uses try/except per column to skip
    already-present columns (mirrors migrate_dreams_schema pattern).
    Defaults are conservative: visible+clustering on, quoting+post-show off.
    """
    foundation_cols = [
        ("visible_in_installation", "INTEGER DEFAULT 1"),
        ("included_in_clustering", "INTEGER DEFAULT 1"),
        ("quotable_by_agent", "INTEGER DEFAULT 0"),
        ("available_post_show", "INTEGER DEFAULT 0"),
        ("consent_token", "TEXT"),
        ("archived_at", "TIMESTAMP"),
    ]
    async with aiosqlite.connect(DB_PATH) as db:
        for col, typ in foundation_cols:
            try:
                await db.execute(f"ALTER TABLE prompts ADD COLUMN {col} {typ}")
            except Exception:
                pass

        # UNIQUE partial index — each consent_token authorizes exactly one dream;
        # pre-Foundation NULL rows are unconstrained.
        try:
            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_consent_token "
                "ON prompts(consent_token) WHERE consent_token IS NOT NULL"
            )
        except Exception:
            pass

        # Belt-and-suspenders: SQLite ALTER ... DEFAULT applies to existing rows
        # in current versions, but explicit UPDATE is harmless if already 0/1.
        await db.execute(
            "UPDATE prompts SET visible_in_installation = 1 "
            "WHERE visible_in_installation IS NULL"
        )
        await db.execute(
            "UPDATE prompts SET included_in_clustering = 1 "
            "WHERE included_in_clustering IS NULL"
        )
        await db.execute(
            "UPDATE prompts SET quotable_by_agent = 0 "
            "WHERE quotable_by_agent IS NULL"
        )
        await db.execute(
            "UPDATE prompts SET available_post_show = 0 "
            "WHERE available_post_show IS NULL"
        )

        await db.commit()
    logger.info("Foundation schema migration complete")


async def migrate_stage3_schema() -> None:
    """Stage 3: cluster_publications + cluster_contests + edits.

    cluster_publications.signature is the durable identity of a witnessed
    cluster snapshot. Computed at publish time over (model, version,
    sorted(rep_dream_ids)) — see CLUSTERING_VERSION above. The signature
    persists exactly through any number of K-means re-runs.

    parent_signature chains revisions; the partial UNIQUE index prevents
    forks (only one un-retracted child per parent at any time).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cluster_publications (
              signature TEXT PRIMARY KEY,
              cluster_id_at_publication INTEGER NOT NULL,
              motif_phrase TEXT NOT NULL,
              steward_name TEXT NOT NULL,
              display_name TEXT,
              steward_note TEXT,
              embedding_model TEXT NOT NULL,
              clustering_algorithm TEXT NOT NULL,
              clustering_version TEXT NOT NULL,
              member_count INTEGER NOT NULL,
              representative_dream_ids TEXT NOT NULL,
              representative_fragments_html TEXT NOT NULL,
              related_concepts TEXT NOT NULL,
              published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              retracted_at TIMESTAMP,
              parent_signature TEXT
            )
        """)
        # Concurrency: at most one un-retracted child per parent. A second
        # concurrent revise targeting the same parent fails the constraint
        # and is handled in the endpoint as 409.
        try:
            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_pub_parent_active "
                "ON cluster_publications(parent_signature) "
                "WHERE retracted_at IS NULL AND parent_signature IS NOT NULL"
            )
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS cluster_contests (
              id INTEGER PRIMARY KEY,
              signature TEXT NOT NULL,
              occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_contests_signature "
            "ON cluster_contests(signature)"
        )

        # In-place metadata edits (steward_note, display_name, related_concepts)
        # don't change the signature — they append to this audit table.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cluster_publication_edits (
              id INTEGER PRIMARY KEY,
              signature TEXT NOT NULL,
              steward_name TEXT NOT NULL,
              field TEXT NOT NULL,
              old_value TEXT,
              new_value TEXT,
              occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logger.info("Stage 3 schema migration complete")


async def migrate_stage2_schema() -> None:
    """Stage 2: consent_flags single-row table for the umap_stale flag.

    Survives restart so a consent change made just before deploy still gets
    honored on the next periodic UMAP recompute. id is checked to be 1 so
    we always operate on a single shared row.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS consent_flags (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              umap_stale INTEGER DEFAULT 0,
              last_recompute_at TIMESTAMP
            )
        """)
        await db.execute(
            "INSERT OR IGNORE INTO consent_flags (id, umap_stale) VALUES (1, 0)"
        )
        await db.commit()
    logger.info("Stage 2 schema migration complete")


# ---------------------------------------------------------------------------
# CSRF helpers (Stage 2) — sign a session-cookie value with THEME_HASH_KEY,
# put the resulting token in a hidden form field, verify on POST. JS-free
# pattern; works alongside HttpOnly auth cookies.
# ---------------------------------------------------------------------------

def make_csrf(cookie_value: str) -> str:
    if not cookie_value:
        return ""
    return hmac.new(
        THEME_HASH_KEY,
        cookie_value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]


def verify_csrf(cookie_value: str, form_token: str) -> bool:
    if not cookie_value or not form_token:
        return False
    expected = make_csrf(cookie_value)
    # constant-time compare to avoid timing oracles on the truncated digest
    return hmac.compare_digest(expected, form_token)


async def insert_prompt(raw_text: str, enriched_text: str, source: str,
                        dreamworld_text: str = "",
                        consent_token: Optional[str] = None,
                        consent: Optional[dict] = None) -> int:
    """Insert a prompt with Foundation consent flags.

    consent dict keys (booleans): visible_in_installation, included_in_clustering,
    quotable_by_agent, available_post_show. Missing keys fall back to plan defaults
    (visible+clustering on; quoting+post-show off).
    """
    c = consent or {}
    visible = 1 if c.get("visible_in_installation", True) else 0
    cluster = 1 if c.get("included_in_clustering", True) else 0
    quotable = 1 if c.get("quotable_by_agent", False) else 0
    post_show = 1 if c.get("available_post_show", False) else 0

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO prompts ("
            "raw_text, enriched_text, source, dreamworld_text, "
            "consent_token, "
            "visible_in_installation, included_in_clustering, "
            "quotable_by_agent, available_post_show"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (raw_text, enriched_text, source, dreamworld_text,
             consent_token, visible, cluster, quotable, post_show),
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
        # Foundation: hide dreams whose visitor revoked visibility OR that have
        # been archived post-show. COALESCE preserves pre-Foundation NULL rows.
        cursor = await db.execute(
            "SELECT id, raw_text, enriched_text, submitted_at, source "
            "FROM prompts "
            "WHERE COALESCE(visible_in_installation, 1) = 1 "
            "AND archived_at IS NULL "
            "ORDER BY submitted_at DESC LIMIT ?",
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
        # Foundation: only cluster dreams whose visitor consented to clustering
        # AND that have not been archived. Seed rows have NULL Foundation flags
        # (per migration), so COALESCE keeps them included by default.
        rows = await db.execute_fetchall(
            "SELECT id, source, embedding, "
            "COALESCE(dreamworld_text, enriched_text, raw_text) as text "
            "FROM prompts WHERE embedding IS NOT NULL "
            "AND COALESCE(included_in_clustering, 1) = 1 "
            "AND archived_at IS NULL"
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


# Stage 2: consent-driven UMAP retrigger.
# Runs every 10 minutes. If consent_flags.umap_stale = 1 (set by any
# /dreams/{id}/consent change that flips visible_in_installation or
# included_in_clustering), recompute UMAP under the lock and clear the flag.
# Survives restart since the flag lives in the DB. Doesn't fight with the
# regular _seed_and_umap_loop — both go through _guarded_recompute_umap.
async def _consent_stale_umap_loop() -> None:
    while True:
        await asyncio.sleep(600)  # 10 min — fast enough to feel responsive,
                                  # slow enough not to thrash the pipeline.
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT umap_stale FROM consent_flags WHERE id = 1"
                )
                row = await cursor.fetchone()
                stale = bool(row and row[0])
            if not stale:
                continue
            logger.info("Consent change pending — running UMAP recompute")
            await _guarded_recompute_umap()
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE consent_flags "
                    "SET umap_stale = 0, last_recompute_at = CURRENT_TIMESTAMP "
                    "WHERE id = 1"
                )
                await db.commit()
        except Exception as e:
            logger.warning(f"_consent_stale_umap_loop: {e}")


async def _set_consent_stale() -> None:
    """Mark UMAP stale after a consent change. Idempotent."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE consent_flags SET umap_stale = 1 WHERE id = 1"
        )
        await db.commit()


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


async def metrics_logger() -> None:
    """Log a per-minute submission-rate line so we can see kid-storm bursts.

    Logs look like:
        metrics prompts_last_min=7 queue_depth=3 max_queue=20 dwell=30
    Grep `metrics ` in the server log to chart the rate; informs whether the
    kid-prompt-storm throttle (see plan §4 step 2) is needed.
    """
    while True:
        await asyncio.sleep(60.0)
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=60)
        while _recent_prompt_timestamps and _recent_prompt_timestamps[0] < cutoff:
            _recent_prompt_timestamps.popleft()
        logger.info(
            f"metrics prompts_last_min={len(_recent_prompt_timestamps)} "
            f"queue_depth={len(queue)} max_queue={MAX_QUEUE_SIZE} "
            f"dwell={PROMPT_DWELL_SECONDS}"
        )


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
            remaining = max(1, int(RATE_LIMIT_SECONDS - elapsed + 0.5))
            logger.info(f"Rate limit hit from {ip} ({elapsed:.1f}s since last)")
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Your last offering is still dissolving — "
                    f"please wait {remaining}s before sending another."
                ),
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

class ConsentToggles(BaseModel):
    visible_in_installation: bool = True
    included_in_clustering: bool = True
    quotable_by_agent: bool = False
    available_post_show: bool = False


class PromptRequest(BaseModel):
    text: Optional[str] = None  # absent = photo-only submission
    source: str = "typed"
    photo_data: Optional[str] = None  # base64 JPEG from visitor camera
    consent: Optional[ConsentToggles] = None


class ChatRequest(BaseModel):
    message: str
    history: list = []
    surface: str = "ask"  # 'ask' (default) | 'match' (Stage 5; not honored without session cookie)


class ChatResponse(BaseModel):
    reply: str
    sources: list = []
    error: str = ""


# ---------------------------------------------------------------------------
# API routes (MUST be registered before StaticFiles mount)
# ---------------------------------------------------------------------------

@app.post("/prompt")
async def post_prompt(body: PromptRequest, request: Request, response: Response):
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
    consent_token: Optional[str] = None  # set when a text dream is queued

    # Only queue a text prompt if the visitor actually typed something
    if raw:
        clipped = raw[:MAX_VISITOR_CHARS]
        regex_blocked = is_blocked(clipped)
        if regex_blocked:
            blocked = True
            block_reason = "regex"
        else:
            llm_blocked, llm_reason = await llm_classify_prompt(clipped)
            blocked = llm_blocked
            block_reason = f"llm:{llm_reason}" if llm_blocked else ""

        if blocked:
            logger.info(f"Prompt blocked [{block_reason}] — silently replacing. raw={clipped!r}")
            display_text = "the sea dreaming"
        else:
            display_text = clipped

        enriched = enrich_prompt(raw) if not blocked else "the sea dreaming"

        # Dreamworld text: full original prompt, content-filtered (not SD-truncated)
        dw_text = "the sea dreaming" if blocked else raw.strip()

        # Enforce max queue size — drop oldest
        if len(queue) >= MAX_QUEUE_SIZE:
            dropped = queue.popleft()
            logger.info(f"Queue full — dropped oldest prompt id={dropped.id}")

        # Foundation: mint per-dream consent token. Single token authorizes a
        # single dream; cookie is overwritten on each new submission (extraction-
        # resistant by design — see plan).
        consent_token = secrets.token_urlsafe(32)
        consent_dict = body.consent.dict() if body.consent else None
        visible_now = bool(consent_dict.get("visible_in_installation", True)) if consent_dict else True
        prompt_id = await insert_prompt(raw, enriched, body.source,
                                        dreamworld_text=dw_text,
                                        consent_token=consent_token,
                                        consent=consent_dict)
        response.set_cookie(
            key="ssd_dream_token",
            value=consent_token,
            max_age=60 * 60 * 24 * 365,  # 1 year
            httponly=True,
            samesite="lax",
            secure=COOKIE_SECURE,
            path="/",
        )

        # Embed full dreamworld text for richer semantics (non-blocking).
        # Embedding always runs — clustering/visibility filters apply at read-time
        # against the embedding, so storing it doesn't violate consent.
        asyncio.create_task(embed_and_position(prompt_id, dw_text))

        item = PromptItem(
            id=prompt_id,
            raw_text=raw,
            enriched_text=enriched,
            display_text=display_text,
            source=body.source,
            submitted_at=datetime.utcnow(),
        )

        # Foundation: only show on the TD wall + visitor live feed if the
        # visitor consented to visibility. The dream is still recorded for
        # later cluster-analysis (if separately consented) or post-show
        # archival; it just doesn't surface in the room.
        if visible_now:
            queue.append(item)
            logger.info(f"Queued prompt id={prompt_id} source={body.source} queue_size={len(queue)}")
        else:
            logger.info(f"Stored prompt id={prompt_id} source={body.source} (visible_in_installation=0; not queued)")
        _recent_prompt_timestamps.append(datetime.utcnow())

    # Handle visitor photo (works for photo-only or text+photo)
    if body.photo_data:
        await _save_visitor_photo(prompt_id or 0, body.photo_data)

    # Broadcast SSE to all listeners (only if a text prompt was queued AND the
    # visitor consented to visibility — same gate as the OSC queue above).
    if raw and 'visible_now' in locals() and visible_now:
        await broadcast_sse(item)

    # Estimate when this prompt will reach the wall: (position - 1) * dwell seconds.
    # The kid-facing app can surface this so they don't spam-retry.
    position = len(queue)
    eta_seconds = max(0, (position - 1) * PROMPT_DWELL_SECONDS)
    payload = {
        "status": "queued",
        "position": position,
        "eta_seconds": eta_seconds,
    }
    # Foundation: include consent_token so the visitor can save it (one-time
    # download path). Only present when a text dream was queued.
    if raw and prompt_id is not None:
        payload["id"] = prompt_id
        payload["consent_token"] = consent_token
    return payload


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
        # Foundation: only show dreams whose visitor consented to be visible AND
        # that have not been archived. COALESCE preserves pre-Foundation rows
        # (NULL flags default visible=1).
        rows = await db.execute_fetchall(
            "SELECT id, raw_text, enriched_text, dreamworld_text, "
            "submitted_at, source, x, y, z, cluster_id, cluster_label, "
            "dir_x, dir_y, dir_z, orientation_mode "
            "FROM prompts WHERE x IS NOT NULL AND source != 'seed' "
            "AND COALESCE(visible_in_installation, 1) = 1 "
            "AND archived_at IS NULL "
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

    # Find relevant context via keyword matching (cards, docs, Foundation canon)
    matched_cards, matched_docs, matched_canon = find_relevant_context(
        user_msg, _chat_cards, _chat_docs, _chat_canon
    )

    # Foundation: placeholder canon docs are NEVER quoted into context.
    # We split matched_canon into placeholder vs. signed-off, and only refuse
    # outright if placeholder canon is the ONLY signal we have. If we also have
    # cards or non-placeholder canon, drop placeholders from context and answer
    # normally (the system prompt + non-placeholder retrieval is enough).
    placeholder_hits = [cd for _s, cd in matched_canon if cd.get("is_placeholder")]
    matched_canon = [(s, cd) for s, cd in matched_canon if not cd.get("is_placeholder")]
    if placeholder_hits and not matched_cards and not matched_docs and not matched_canon:
        titles = ", ".join(cd["title"] for cd in placeholder_hits[:2])
        return ChatResponse(
            reply=(
                "I can't speak to this yet — the team is preparing this explanation "
                f"({titles}). Check back after the next round of canon review. "
                "If you'd like to read what we have so far, the project's writing is "
                "linked from the home page."
            ),
            sources=[cd.get("source_path", "") for cd in placeholder_hits[:2]],
        )
    if placeholder_hits:
        logger.info(
            f"Chat: skipped {len(placeholder_hits)} placeholder canon doc(s) from context "
            f"(other retrieval available)"
        )

    # Build context string for the LLM
    context_parts = []
    source_ids = []
    for score, nid, card in matched_cards:
        context_parts.append(f"Node {nid}: {card.get('title', '')} — {card.get('body', '')[:300]}")
        source_ids.append(nid)
    for score, chunk in matched_docs:
        context_parts.append(f"Document: {chunk.get('title', '')} — {chunk.get('text', '')[:300]}")
    # Foundation canon — quoted up to 600 chars (canon docs are short + authoritative).
    for score, cd in matched_canon:
        title = cd.get("title", "")
        body = cd.get("body", "")[:600]
        src = cd.get("source_path", "")
        context_parts.append(f"Canon doc — {title} ({src}): {body}")
        source_ids.append(src)
    context_str = "\n\n".join(context_parts[:8])

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
# Foundation routes — / landing, /visitor, /cloud, /ask, /about/{topic}
# ---------------------------------------------------------------------------

_static_dir = BASE_DIR / "static"
_canon_dirs_map = {
    "mudra": BASE_DIR / "docs" / "digital-ecologies" / "mudra-as-sympoiesis.md",
    "herring": BASE_DIR / "docs" / "explainers" / "why-dreams-become-herring.md",
    "ai": BASE_DIR / "docs" / "explainers" / "what-the-ai-can-and-cannot-know.md",
}


def _render_canon_page(md_path: Path, fallback_title: str) -> HTMLResponse:
    """Render a canon .md as a styled HTML page consistent with the rest of the app.

    Uses the `markdown` package (already a transitive dep on most installs); falls
    back to a <pre> block if the package is missing.
    """
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        raise HTTPException(404, "page not found")

    # Strip frontmatter
    title = fallback_title
    body_md = text
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = text.find("\n---", 4)
        if end != -1:
            fm_block = text[4:end]
            body_md = text[end + 4:].lstrip("\n")
            for line in fm_block.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"').strip("'")

    try:
        import markdown as _md
        html_body = _md.markdown(body_md, extensions=["extra", "smarty"])
    except Exception:
        # Stdlib fallback — preformatted text. Better than nothing.
        from html import escape
        html_body = f"<pre>{escape(body_md)}</pre>"

    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Salish Sea Dreaming</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root {{ --bg: #050a12; --fg: #c8dff0; --accent: #7aa8c8; --muted: #5a7a99; --line: #1a2a3a; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--fg); margin: 0; font-weight: 300; line-height: 1.7; }}
.nav {{ position: sticky; top: 0; padding: 14px 24px; background: rgba(5,10,18,0.96); border-bottom: 1px solid var(--line); display: flex; align-items: center; gap: 24px; z-index: 10; backdrop-filter: blur(8px); }}
.nav-title {{ font-size: 13px; font-weight: 300; color: var(--accent); letter-spacing: 0.1em; text-transform: uppercase; }}
.nav-links {{ display: flex; gap: 18px; margin-left: auto; }}
.nav-links a {{ font-size: 11px; color: var(--muted); text-decoration: none; letter-spacing: 0.05em; }}
.nav-links a:hover {{ color: var(--accent); }}
.container {{ max-width: 720px; margin: 0 auto; padding: 48px 24px 80px; }}
h1, h2, h3 {{ color: var(--accent); font-weight: 300; letter-spacing: 0.04em; }}
h1 {{ font-size: 26px; margin: 0 0 24px; }}
h2 {{ font-size: 18px; margin-top: 36px; }}
h3 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #5a8aa8; margin-top: 28px; }}
p, li {{ font-size: 15px; }}
blockquote {{ border-left: 2px solid var(--accent); padding: 4px 16px; margin: 18px 0; color: #a0c0d8; font-style: italic; background: rgba(122,168,200,0.04); }}
table {{ border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 13px; }}
th, td {{ border: 1px solid var(--line); padding: 8px 12px; text-align: left; }}
th {{ background: rgba(122,168,200,0.06); color: var(--accent); font-weight: 400; }}
code {{ background: rgba(122,168,200,0.08); padding: 2px 6px; border-radius: 3px; font-size: 13px; }}
hr {{ border: none; border-top: 1px solid var(--line); margin: 32px 0; }}
a {{ color: var(--accent); }}
@media (max-width: 600px) {{ .container {{ padding: 32px 18px 60px; }} h1 {{ font-size: 22px; }} }}
</style>
</head><body>
<nav class="nav">
  <div class="nav-title">{title}</div>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/cloud">Cloud</a>
    <a href="/ask">Ask</a>
  </div>
</nav>
<div class="container">{html_body}</div>
</body></html>"""
    return HTMLResponse(content=page)


@app.get("/", include_in_schema=False)
async def root():
    """Foundation: serve the landing page (links to all surfaces)."""
    from fastapi.responses import FileResponse
    idx = _static_dir / "index.html"
    if idx.exists():
        return FileResponse(idx, media_type="text/html")
    # Fallback to legacy redirect if landing page is missing
    return RedirectResponse("/static/visitor.html")


@app.get("/visitor", include_in_schema=False)
async def visitor_route():
    """Foundation: stable URL for the visitor submission app."""
    from fastapi.responses import FileResponse
    p = BASE_DIR / "web" / "visitor.html"
    if not p.exists():
        raise HTTPException(404, "visitor.html not found")
    return FileResponse(p, media_type="text/html")


@app.get("/visitor.html", include_in_schema=False)
async def visitor_redirect():
    return RedirectResponse("/visitor")


@app.get("/cloud", include_in_schema=False)
async def cloud_route():
    """Foundation: stable URL for the 3D dreamworld viewer."""
    from fastapi.responses import FileResponse
    p = _static_dir / "dreamworld.html"
    if not p.exists():
        raise HTTPException(404, "dreamworld.html not found")
    return FileResponse(p, media_type="text/html")


@app.get("/ask", include_in_schema=False)
async def ask_route():
    """Foundation: thin chat surface that wraps /chat in witness register."""
    from fastapi.responses import FileResponse
    p = _static_dir / "ask.html"
    if not p.exists():
        raise HTTPException(404, "ask.html not found")
    return FileResponse(p, media_type="text/html")


@app.get("/about/{topic}", include_in_schema=False)
async def about_route(topic: str):
    """Foundation: render canon markdown as styled HTML pages."""
    md_path = _canon_dirs_map.get(topic)
    if not md_path or not md_path.exists():
        raise HTTPException(404, "page not found")
    fallback_titles = {"mudra": "About the Gesture",
                       "herring": "Why Dreams Become Herring",
                       "ai": "What the AI Can and Cannot Know"}
    return _render_canon_page(md_path, fallback_titles.get(topic, topic.title()))


# ---------------------------------------------------------------------------
# Stage 2 — /consent: visitors revisit & change consent on their own dreams.
#
# Two paths:
#   • Same-device: the original ssd_dream_token cookie is still in the
#     browser. /consent looks it up, renders the four-toggle form directly.
#   • Cross-device: visitor pastes the token they saved at submission. We
#     validate server-side, set ssd_consent_session (Path=/dreams,
#     Max-Age=1800, HttpOnly+Secure+SameSite=Lax), and redirect to
#     /dreams/{id}/consent-edit which renders the same form.
#
# Both forms post to /dreams/{id}/consent. CSRF is enforced via a hidden
# field (HMAC of the cookie value with THEME_HASH_KEY, [:16]) — the auth
# cookie can stay HttpOnly since the server sees both values.
# ---------------------------------------------------------------------------

async def _lookup_dream_by_token(token: str) -> Optional[dict]:
    """Return {id, raw_text, ...consent flags} or None if no match."""
    if not token:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, raw_text, dreamworld_text, "
            "visible_in_installation, included_in_clustering, "
            "quotable_by_agent, available_post_show, archived_at "
            "FROM prompts WHERE consent_token = ? LIMIT 1",
            (token,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


def _consent_page(*, dream: Optional[dict],
                  csrf_token: str = "",
                  cookie_kind: str = "",
                  paste_error: str = "",
                  flash: str = "") -> HTMLResponse:
    """Server-rendered HTML — handles both states (no-cookie vs cookie+dream).

    cookie_kind ∈ {"dream", "session", ""} — distinguishes the original
    submission cookie from the cross-device session cookie. Used only in the
    "consent saved" footer text.
    """
    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root{--bg:#050a12;--fg:#c8dff0;--accent:#7aa8c8;--muted:#5a7a99;--line:#1a2a3a;}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg);margin:0;font-weight:300;line-height:1.6}
.nav{position:sticky;top:0;padding:14px 24px;background:rgba(5,10,18,0.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;z-index:10;backdrop-filter:blur(8px)}
.nav-title{font-size:13px;font-weight:300;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase}
.nav-links{display:flex;gap:18px;margin-left:auto}
.nav-links a{font-size:11px;color:var(--muted);text-decoration:none;letter-spacing:0.05em}
.nav-links a:hover{color:var(--accent)}
.container{max-width:560px;margin:0 auto;padding:48px 24px 80px}
h1{font-size:22px;color:var(--accent);font-weight:300;letter-spacing:0.06em;margin:0 0 8px}
.tagline{font-size:12px;color:var(--muted);margin:0 0 32px;font-style:italic}
.flash{padding:12px 16px;border:1px solid rgba(122,168,200,0.4);border-radius:6px;background:rgba(122,168,200,0.06);font-size:13px;color:var(--fg);margin-bottom:24px}
.error{padding:12px 16px;border:1px solid #b08070;border-radius:6px;background:rgba(176,128,112,0.06);font-size:13px;color:#d4a08c;margin-bottom:24px}
.dream-card{padding:18px;border:1px solid var(--line);border-radius:6px;background:rgba(122,168,200,0.04);margin-bottom:28px}
.dream-card .dlabel{font-size:10px;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase;margin-bottom:8px}
.dream-card .dtext{font-size:14px;color:var(--fg);line-height:1.5}
fieldset{border:none;padding:0;margin:0 0 24px}
legend{font-size:10px;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase;margin-bottom:12px;padding:0}
.toggle{display:flex;align-items:flex-start;gap:10px;margin-bottom:14px;cursor:pointer}
.toggle input[type=checkbox]{accent-color:var(--accent);width:1rem;height:1rem;margin-top:0.25rem;flex-shrink:0;cursor:pointer}
.toggle .tlabel{font-size:14px;color:var(--fg)}
.toggle .tdesc{font-size:11px;color:var(--muted);margin-top:2px;line-height:1.5}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
button,input[type=submit]{background:none;border:1px solid var(--accent);color:var(--accent);padding:10px 20px;border-radius:6px;font-family:'Inter',sans-serif;font-size:12px;letter-spacing:0.06em;cursor:pointer;transition:background .2s}
button:hover,input[type=submit]:hover{background:rgba(122,168,200,0.1)}
.danger{border-color:#b08070;color:#d4a08c}
.danger:hover{background:rgba(176,128,112,0.1)}
.paste-form{display:flex;flex-direction:column;gap:10px;max-width:420px}
.paste-form label{font-size:13px;color:var(--fg)}
.paste-form input[type=text]{background:rgba(122,168,200,0.04);border:1px solid var(--line);color:var(--fg);padding:10px 14px;border-radius:6px;font-family:'Inter',sans-serif;font-size:13px}
.paste-form input[type=text]:focus{outline:none;border-color:var(--accent)}
.note{font-size:12px;color:var(--muted);margin-top:24px;line-height:1.65;padding-top:18px;border-top:1px solid var(--line)}
.note a{color:var(--accent)}
@media (max-width:600px){.container{padding:30px 16px 60px}}
"""

    nav = """<nav class="nav">
  <div class="nav-title">Consent</div>
  <div class="nav-links">
    <a href="/">Home</a><a href="/cloud">Cloud</a><a href="/about/ai">What the AI knows</a>
  </div>
</nav>"""

    if not dream:
        # No cookie / no match — render paste-token form.
        err_html = f'<div class="error">{paste_error}</div>' if paste_error else ""
        body = f"""
<div class="container">
  <h1>Consent</h1>
  <p class="tagline">Manage how the system carries the dream you submitted.</p>
  {err_html}
  <p>Paste the consent token you saved when you submitted your dream. (We only ever issue these to you — we don't have a list of dreamers.)</p>
  <form class="paste-form" method="post" action="/consent">
    <label for="ct">consent token</label>
    <input type="text" name="consent_token" id="ct" autocomplete="off" required spellcheck="false" placeholder="paste here">
    <input type="submit" value="continue →">
  </form>
  <div class="note">If you've lost your token, the system can't identify your dream — by design (no cross-dream identity). See <a href="/about/ai">what the AI can and cannot know</a> for the recovery path.</div>
</div>"""
        return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Consent — Salish Sea Dreaming</title><style>{css}</style></head><body>{nav}{body}</body></html>")

    # We have a dream — render the four-toggle form.
    flash_html = f'<div class="flash">{flash}</div>' if flash else ""
    archived_note = ""
    if dream.get("archived_at"):
        archived_note = '<div class="error">This dream is archived. Toggling visibility back on requires a steward action.</div>'

    text_to_show = (dream.get("dreamworld_text") or dream.get("raw_text") or "").strip()
    # Truncate display text — visitor knows what they wrote.
    if len(text_to_show) > 240:
        text_to_show = text_to_show[:240] + "…"

    def chk(name: str, default: int) -> str:
        return "checked" if int(dream.get(name, default) or 0) else ""

    body = f"""
<div class="container">
  <h1>Consent</h1>
  <p class="tagline">Change how the system carries this dream. Soft action only — we never delete the record of what you offered.</p>
  {flash_html}
  {archived_note}
  <div class="dream-card">
    <div class="dlabel">your dream</div>
    <div class="dtext">{_html_escape(text_to_show) or '<em>(no text — photo-only submission)</em>'}</div>
  </div>
  <form method="post" action="/dreams/{int(dream['id'])}/consent">
    <input type="hidden" name="csrf_token" value="{csrf_token}">
    <fieldset>
      <legend>How should the system carry this dream?</legend>
      <label class="toggle">
        <input type="checkbox" name="visible_in_installation" value="1" {chk('visible_in_installation', 1)}>
        <span><span class="tlabel">Visible in the installation</span><span class="tdesc">Appears in the dream cloud and on the gallery wall.</span></span>
      </label>
      <label class="toggle">
        <input type="checkbox" name="included_in_clustering" value="1" {chk('included_in_clustering', 1)}>
        <span><span class="tlabel">Included in pattern-finding</span><span class="tdesc">Used by the algorithm to discover semantic clusters across all dreams. Anonymous.</span></span>
      </label>
      <label class="toggle">
        <input type="checkbox" name="quotable_by_agent" value="1" {chk('quotable_by_agent', 0)}>
        <span><span class="tlabel">Quotable by the chat agent</span><span class="tdesc">The agent at /ask may quote this dream when it's relevant. It's never attributed to anyone.</span></span>
      </label>
      <label class="toggle">
        <input type="checkbox" name="available_post_show" value="1" {chk('available_post_show', 0)}>
        <span><span class="tlabel">Kept after the show closes</span><span class="tdesc">Otherwise the dream is archived after April 26 (still in the database, not served).</span></span>
      </label>
    </fieldset>
    <div class="actions">
      <input type="submit" name="action" value="save changes">
      <button type="submit" name="action" value="withdraw" class="danger" formnovalidate>withdraw from cloud</button>
    </div>
  </form>
  <div class="note">Cookie kind: <code>{cookie_kind or 'unknown'}</code>. To remove a fragment from a published cluster page (Stage 3+), email <a href="mailto:darren@salishseadreaming.art?subject=%5BSSD%5D%20Fragment%20removal%20request">darren@salishseadreaming.art</a>.</div>
</div>"""
    return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Consent — Salish Sea Dreaming</title><style>{css}</style></head><body>{nav}{body}</body></html>")


def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;") \
        .replace(">", "&gt;").replace('"', "&quot;")


@app.get("/consent", include_in_schema=False)
async def consent_get(request: Request):
    """Render the consent edit form. Same-device: cookie path. Cross-device:
    paste-token form (POST goes to /consent below, then redirect)."""
    cookie = request.cookies.get("ssd_dream_token", "")
    if cookie:
        dream = await _lookup_dream_by_token(cookie)
        if dream:
            return _consent_page(
                dream=dream,
                csrf_token=make_csrf(cookie),
                cookie_kind="dream",
            )
    # Try cross-device session cookie next.
    sess = request.cookies.get("ssd_consent_session", "")
    if sess:
        dream = await _lookup_dream_by_token(sess)
        if dream:
            return _consent_page(
                dream=dream,
                csrf_token=make_csrf(sess),
                cookie_kind="session",
            )
    return _consent_page(dream=None)


@app.post("/consent", include_in_schema=False)
async def consent_paste(request: Request):
    """Cross-device path: visitor pasted their consent_token. Validate, set
    a short-lived session cookie scoped to /dreams, redirect."""
    form = await request.form()
    token = (form.get("consent_token") or "").strip()
    if not token:
        return _consent_page(dream=None, paste_error="Please paste a token.")
    dream = await _lookup_dream_by_token(token)
    if not dream:
        return _consent_page(
            dream=None,
            paste_error="That token doesn't match any dream we know about. Tokens are issued at submission and never reissued automatically.",
        )
    # Issue session cookie scoped narrowly to /dreams (the consent endpoints).
    response = RedirectResponse(
        url=f"/dreams/{int(dream['id'])}/consent-edit",
        status_code=303,
    )
    response.set_cookie(
        key="ssd_consent_session",
        value=token,
        max_age=1800,  # 30 min
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/dreams",
    )
    return response


@app.get("/dreams/{dream_id}/consent-edit", include_in_schema=False)
async def consent_edit_get(dream_id: int, request: Request):
    """Cross-device target: the session cookie set by /consent paste flow
    is scoped here. Same-device cookie also accepted as a fallback."""
    sess = request.cookies.get("ssd_consent_session", "")
    cookie = request.cookies.get("ssd_dream_token", "")
    used = ""
    dream = None
    if sess:
        dream = await _lookup_dream_by_token(sess)
        if dream and int(dream["id"]) == dream_id:
            used = sess
            kind = "session"
    if not used and cookie:
        dream2 = await _lookup_dream_by_token(cookie)
        if dream2 and int(dream2["id"]) == dream_id:
            dream = dream2
            used = cookie
            kind = "dream"
    if not used or not dream:
        return _consent_page(
            dream=None,
            paste_error="Your session has expired or doesn't authorize this dream. Paste your token again.",
        )
    return _consent_page(
        dream=dream,
        csrf_token=make_csrf(used),
        cookie_kind=kind,
    )


@app.post("/dreams/{dream_id}/consent", include_in_schema=False)
async def consent_post(dream_id: int, request: Request):
    """Update consent flags for a dream. Auth: cookie (dream OR session),
    must map to dream_id. CSRF: hidden form field signed with the same cookie
    value. Soft action only — never deletes."""
    form = await request.form()
    sess = request.cookies.get("ssd_consent_session", "")
    cookie = request.cookies.get("ssd_dream_token", "")

    used = ""
    dream = None
    for tok in (sess, cookie):
        if not tok:
            continue
        d = await _lookup_dream_by_token(tok)
        if d and int(d["id"]) == dream_id:
            used = tok
            dream = d
            break
    if not used or not dream:
        raise HTTPException(403, "no valid token for this dream")

    # CSRF: form field must equal HMAC(THEME_HASH_KEY, cookie_value)[:16]
    if not verify_csrf(used, (form.get("csrf_token") or "").strip()):
        raise HTTPException(403, "csrf_token invalid")

    action = (form.get("action") or "").lower()
    # "Withdraw from cloud" overrides toggles — clears visibility + clustering.
    if action == "withdraw":
        new_flags = {
            "visible_in_installation": 0,
            "included_in_clustering": int(dream.get("included_in_clustering", 1) or 0),
            "quotable_by_agent": int(dream.get("quotable_by_agent", 0) or 0),
            "available_post_show": int(dream.get("available_post_show", 0) or 0),
        }
        flash = "Withdrawn from the cloud. The dream is preserved but no longer visible."
    else:
        # Checkbox absent in form == unchecked (HTML form behavior). For each
        # toggle, presence of the field name = on, absence = off.
        new_flags = {
            "visible_in_installation": 1 if form.get("visible_in_installation") else 0,
            "included_in_clustering":  1 if form.get("included_in_clustering")  else 0,
            "quotable_by_agent":       1 if form.get("quotable_by_agent")       else 0,
            "available_post_show":     1 if form.get("available_post_show")     else 0,
        }
        flash = "Saved."

    # Detect whether visible/clustering flipped (in either direction) so we
    # mark UMAP stale for the periodic recompute.
    flipped_umap = (
        int(dream.get("visible_in_installation", 1) or 0) != new_flags["visible_in_installation"]
        or int(dream.get("included_in_clustering", 1) or 0) != new_flags["included_in_clustering"]
    )

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE prompts SET visible_in_installation=?, "
            "included_in_clustering=?, quotable_by_agent=?, "
            "available_post_show=? WHERE id=?",
            (
                new_flags["visible_in_installation"],
                new_flags["included_in_clustering"],
                new_flags["quotable_by_agent"],
                new_flags["available_post_show"],
                dream_id,
            ),
        )
        await db.commit()

    if flipped_umap:
        await _set_consent_stale()
        logger.info(f"Consent change marked UMAP stale (dream_id={dream_id})")

    # Re-render the form with a flash and the new state.
    fresh = await _lookup_dream_by_token(used)
    return _consent_page(
        dream=fresh,
        csrf_token=make_csrf(used),
        cookie_kind=("session" if used == sess else "dream"),
        flash=flash,
    )


# ---------------------------------------------------------------------------
# Stage 2 — admin endpoint: force an immediate UMAP recompute.
# Steward-token-gated via STEWARD_TOKENS env (JSON: {"name": "uuid", ...}).
# Used when a visitor needs immediate withdrawal rather than waiting for
# the 10-minute periodic recompute.
# ---------------------------------------------------------------------------

_STEWARD_TOKENS_RAW = os.getenv("STEWARD_TOKENS", "").strip()
try:
    STEWARD_TOKENS = json.loads(_STEWARD_TOKENS_RAW) if _STEWARD_TOKENS_RAW else {}
    if not isinstance(STEWARD_TOKENS, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in STEWARD_TOKENS.items()
    ):
        STEWARD_TOKENS = {}
except Exception:
    STEWARD_TOKENS = {}


def _steward_from_request(request: Request) -> Optional[str]:
    """Return the steward name if the request carries a valid Bearer token,
    else None. Returns None when STEWARD_TOKENS is unconfigured (caller
    surfaces this as a 503 instead of a 401)."""
    if not STEWARD_TOKENS:
        return None
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    for name, expected in STEWARD_TOKENS.items():
        if hmac.compare_digest(token, expected):
            return name
    return None


async def _audit_steward(name: str, endpoint: str) -> None:
    """Record steward action — created lazily on first use so the table only
    exists where it's needed (avoids touching schema in a stage that doesn't
    add steward endpoints).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS steward_audit (
              id INTEGER PRIMARY KEY,
              steward_name TEXT NOT NULL,
              endpoint TEXT NOT NULL,
              occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute(
            "INSERT INTO steward_audit (steward_name, endpoint) VALUES (?, ?)",
            (name, endpoint),
        )
        await db.commit()


@app.post("/admin/recompute-umap", include_in_schema=False)
async def admin_recompute_umap(request: Request):
    """Force an immediate UMAP recompute. Steward-token-gated."""
    if not STEWARD_TOKENS:
        raise HTTPException(503, "stewardship not configured")
    name = _steward_from_request(request)
    if not name:
        raise HTTPException(401, "steward authentication required")
    await _audit_steward(name, "/admin/recompute-umap")
    asyncio.create_task(_guarded_recompute_umap())
    # Also clear the stale flag pre-emptively — the recompute will overwrite
    # last_recompute_at on completion.
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE consent_flags SET umap_stale = 0 WHERE id = 1")
        await db.commit()
    return {"queued": True, "steward": name}


# ---------------------------------------------------------------------------
# Stage 3 — Cluster pages as published witnesses.
#
# Each cluster_publication is a steward-witnessed snapshot of a steward-
# selected dream subset, identified by signature = sha256(model | version |
# sorted(rep_dream_ids))[:16]. The signature persists exactly through any
# number of K-means re-runs because it doesn't depend on algorithmic
# membership at read time — only on the steward's selection at publish time.
#
# The page at /clusters/{signature} renders forever (with retraction notice
# if retracted). Revisions chain via parent_signature; only one un-retracted
# revision per parent (enforced by partial UNIQUE index).
# ---------------------------------------------------------------------------

def _compute_cluster_signature(rep_dream_ids: list) -> str:
    """sha256(model | version | sorted-comma-joined-ids)[:16]. Deterministic."""
    payload = "{model}|{version}|{ids}".format(
        model=EMBEDDING_MODEL,
        version=CLUSTERING_VERSION,
        ids=",".join(str(int(i)) for i in sorted(rep_dream_ids)),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _bake_fragment_html(dream_id: int, raw_text: str) -> str:
    """Truncate to 200 chars at word boundary, HTML-escape, wrap in
    <blockquote class="dream-fragment" data-dream-id="N">…</blockquote>.

    data-dream-id is required for any future redact_fragment surgical
    targeting — the original deep-link plan calls for this attribute.
    """
    text = (raw_text or "").strip()
    if len(text) > 200:
        # Word-boundary truncation
        cut = text[:200].rsplit(" ", 1)[0] or text[:200]
        text = cut + "…"
    return (
        f'<blockquote class="dream-fragment" data-dream-id="{int(dream_id)}">'
        f'{_html_escape(text)}'
        f'</blockquote>'
    )


async def _fetch_dreams_in_cluster(cluster_id: int) -> list:
    """Returns all currently-quotable, non-archived dreams whose cluster_id
    matches. Sorted by submitted_at DESC for steward review convenience."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT id, raw_text, dreamworld_text, submitted_at, cluster_label "
            "FROM prompts "
            "WHERE cluster_id = ? "
            "AND COALESCE(quotable_by_agent, 0) = 1 "
            "AND archived_at IS NULL "
            "AND COALESCE(visible_in_installation, 1) = 1 "
            "ORDER BY submitted_at DESC",
            (int(cluster_id),),
        )
        return [dict(r) for r in rows]


async def _fetch_publication(signature: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM cluster_publications WHERE signature = ?",
            (signature,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def _fetch_contest_count(signature: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM cluster_contests WHERE signature = ?",
            (signature,),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def _fetch_chain_current(starting_signature: str) -> Optional[str]:
    """Walk parent_signature chain forward from starting_signature; return
    the current un-retracted leaf signature, or None if all are retracted."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        seen = set()
        current = starting_signature
        # Walk forward by finding rows whose parent_signature == current.
        while current not in seen:
            seen.add(current)
            cur = await db.execute(
                "SELECT signature, retracted_at FROM cluster_publications "
                "WHERE parent_signature = ? AND retracted_at IS NULL "
                "ORDER BY published_at DESC LIMIT 1",
                (current,),
            )
            row = await cur.fetchone()
            if not row:
                # No newer un-retracted revision; check if `current` itself is unretracted
                cur2 = await db.execute(
                    "SELECT retracted_at FROM cluster_publications WHERE signature = ?",
                    (current,),
                )
                r2 = await cur2.fetchone()
                if r2 and r2[0] is None:
                    return current
                return None
            current = row[0]
        return None


# ── /clusters/draft (steward UI) ────────────────────────────────────────

def _is_steward_request(request: Request) -> Optional[str]:
    """Returns steward_name if Authorization: Bearer <valid token>, else None.
    Caller distinguishes 503 (unconfigured) vs 401 (bad token)."""
    return _steward_from_request(request)


def _draft_index_html(clusters: list) -> str:
    """Steward-only index page: lists current K-means clusters with quotable
    member counts so the steward can pick one to publish."""
    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root{--bg:#050a12;--fg:#c8dff0;--accent:#7aa8c8;--muted:#5a7a99;--line:#1a2a3a;}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg);margin:0;font-weight:300;line-height:1.6}
.nav{position:sticky;top:0;padding:14px 24px;background:rgba(5,10,18,0.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;z-index:10}
.nav-title{font-size:13px;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase}
.nav-links{display:flex;gap:18px;margin-left:auto}
.nav-links a{font-size:11px;color:var(--muted);text-decoration:none;letter-spacing:0.05em}
.container{max-width:760px;margin:0 auto;padding:48px 24px 80px}
h1{font-size:22px;color:var(--accent);font-weight:300;letter-spacing:0.06em;margin:0 0 8px}
.tag{font-size:12px;color:var(--muted);margin:0 0 32px;font-style:italic}
.cluster-row{display:flex;align-items:center;gap:14px;padding:14px 16px;border:1px solid var(--line);border-radius:6px;background:rgba(122,168,200,0.04);margin-bottom:10px}
.cluster-row .cid{font-size:11px;color:var(--muted);letter-spacing:0.08em;min-width:64px}
.cluster-row .motif{flex:1;font-size:14px;color:var(--fg)}
.cluster-row .count{font-size:11px;color:var(--muted);min-width:96px;text-align:right}
.cluster-row a{color:var(--accent);text-decoration:none;font-size:12px;border:1px solid var(--accent);border-radius:14px;padding:5px 12px;letter-spacing:0.04em}
.cluster-row a:hover{background:rgba(122,168,200,0.1)}
.note{font-size:12px;color:var(--muted);margin-top:24px;line-height:1.65;padding-top:18px;border-top:1px solid var(--line)}
"""
    rows_html = ""
    for c in clusters:
        rows_html += (
            f'<div class="cluster-row">'
            f'<div class="cid">cluster {int(c["cluster_id"])}</div>'
            f'<div class="motif">{_html_escape(c.get("motif") or "(no label)")}</div>'
            f'<div class="count">{int(c["quotable_count"])} quotable</div>'
            f'<a href="/clusters/draft?cluster_id={int(c["cluster_id"])}">draft →</a>'
            f'</div>'
        )
    if not rows_html:
        rows_html = '<p class="tag">No clusters with quotable members yet. Visitors need to opt in to quoting first.</p>'
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cluster drafts — Salish Sea Dreaming</title><style>{css}</style></head><body>
<nav class="nav"><div class="nav-title">Cluster drafts (steward)</div><div class="nav-links"><a href="/">Home</a><a href="/clusters/published">Published</a><a href="/cloud">Cloud</a></div></nav>
<div class="container">
  <h1>Cluster drafts</h1>
  <p class="tag">Pick a cluster, choose 3–7 representative dreams from its quotable members, and publish a witnessed snapshot.</p>
  {rows_html}
  <div class="note">Only quotable, non-archived, visible dreams are listed (per consent). Publishing creates a permanent, signed witness page at <code>/clusters/&lt;signature&gt;</code>.</div>
</div></body></html>"""


def _draft_form_html(cluster_id: int, dreams: list, motif: str) -> str:
    """Steward-only form for picking representatives + writing a steward note."""
    css = _draft_index_html.__defaults__ if False else None  # placeholder; we
    # reuse the same style block by inlining below for simplicity
    style = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root{--bg:#050a12;--fg:#c8dff0;--accent:#7aa8c8;--muted:#5a7a99;--line:#1a2a3a;}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg);margin:0;font-weight:300;line-height:1.6}
.nav{position:sticky;top:0;padding:14px 24px;background:rgba(5,10,18,0.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;z-index:10}
.nav-title{font-size:13px;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase}
.nav-links{display:flex;gap:18px;margin-left:auto}
.nav-links a{font-size:11px;color:var(--muted);text-decoration:none;letter-spacing:0.05em}
.container{max-width:760px;margin:0 auto;padding:48px 24px 80px}
h1{font-size:22px;color:var(--accent);font-weight:300;letter-spacing:0.06em;margin:0 0 8px}
.tag{font-size:12px;color:var(--muted);margin:0 0 24px;font-style:italic}
.dream-pick{display:flex;align-items:flex-start;gap:10px;padding:12px 14px;border:1px solid var(--line);border-radius:6px;background:rgba(122,168,200,0.03);margin-bottom:8px;cursor:pointer}
.dream-pick input{accent-color:var(--accent);width:1rem;height:1rem;margin-top:0.2rem;flex-shrink:0}
.dream-pick .dt{font-size:13px;color:var(--fg);line-height:1.55}
.dream-pick .ds{font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:0.04em}
fieldset{border:none;padding:0;margin:0 0 18px}
legend{font-size:10px;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase;margin-bottom:10px;padding:0}
input[type=text],textarea{background:rgba(122,168,200,0.04);border:1px solid var(--line);color:var(--fg);padding:10px 14px;border-radius:6px;font-family:'Inter',sans-serif;font-size:13px;width:100%;font-weight:300}
textarea{min-height:84px;resize:vertical;line-height:1.6}
input[type=text]:focus,textarea:focus{outline:none;border-color:var(--accent)}
.row{display:flex;flex-direction:column;gap:6px;margin-bottom:14px}
.row label{font-size:11px;color:var(--muted);letter-spacing:0.06em;text-transform:uppercase}
.actions{display:flex;gap:10px;margin-top:18px}
button{background:none;border:1px solid var(--accent);color:var(--accent);padding:10px 22px;border-radius:6px;font-family:inherit;font-size:12px;letter-spacing:0.06em;cursor:pointer}
button:hover{background:rgba(122,168,200,0.1)}
.count-hint{font-size:11px;color:var(--muted);margin:6px 0 16px}
"""
    pick_rows = ""
    for d in dreams:
        text = (d.get("dreamworld_text") or d.get("raw_text") or "").strip()
        if len(text) > 220:
            text = text[:220] + "…"
        pick_rows += (
            f'<label class="dream-pick">'
            f'<input type="checkbox" name="representative_dream_ids" value="{int(d["id"])}">'
            f'<span><span class="dt">{_html_escape(text)}</span>'
            f'<span class="ds">id {int(d["id"])} · {_html_escape((d.get("submitted_at") or "")[:19])}</span></span>'
            f'</label>'
        )
    if not pick_rows:
        pick_rows = '<p class="tag">No quotable dreams in this cluster yet.</p>'

    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cluster {int(cluster_id)} draft — Salish Sea Dreaming</title><style>{style}</style></head><body>
<nav class="nav"><div class="nav-title">Cluster {int(cluster_id)} draft</div><div class="nav-links"><a href="/clusters/draft">Drafts</a><a href="/clusters/published">Published</a></div></nav>
<div class="container">
  <h1>Witness this cluster</h1>
  <p class="tag">Algorithm motif: <em>{_html_escape(motif or '(no label)')}</em>. Pick 3–7 dreams whose presence you want to anchor at this cluster's witnessed identity. Add a steward note to frame the gathering.</p>
  <form method="post" action="/clusters/publish">
    <input type="hidden" name="cluster_id" value="{int(cluster_id)}">
    <fieldset>
      <legend>Representative dreams (3–7 required)</legend>
      <div class="count-hint">Only quotable, non-archived, currently visible dreams shown.</div>
      {pick_rows}
    </fieldset>
    <div class="row">
      <label for="display_name">Display name (optional)</label>
      <input type="text" id="display_name" name="display_name" maxlength="80" placeholder="e.g. The Salish Sea Dreaming Stewards">
    </div>
    <div class="row">
      <label for="steward_note">Steward note</label>
      <textarea id="steward_note" name="steward_note" maxlength="800" placeholder="Why these dreams together? What does this gathering hold?"></textarea>
    </div>
    <div class="row">
      <label for="related_concepts">Related concepts (comma-separated)</label>
      <input type="text" id="related_concepts" name="related_concepts" maxlength="200" placeholder="e.g. herring, eelgrass, Kwaxala">
    </div>
    <div class="actions">
      <button type="submit">publish witness →</button>
    </div>
  </form>
</div></body></html>"""


@app.get("/clusters/draft", include_in_schema=False)
async def clusters_draft(request: Request, cluster_id: Optional[int] = None):
    """Steward-only draft UI. Without cluster_id, lists current K-means
    clusters with quotable counts. With cluster_id, renders publish form."""
    if not STEWARD_TOKENS:
        raise HTTPException(503, "stewardship not configured")
    name = _is_steward_request(request)
    if not name:
        raise HTTPException(401, "steward authentication required")

    if cluster_id is None:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            rows = await db.execute_fetchall(
                "SELECT cluster_id, "
                "MAX(cluster_label) AS motif, "
                "SUM(CASE WHEN COALESCE(quotable_by_agent,0)=1 "
                "         AND archived_at IS NULL "
                "         AND COALESCE(visible_in_installation,1)=1 "
                "    THEN 1 ELSE 0 END) AS quotable_count "
                "FROM prompts WHERE cluster_id IS NOT NULL "
                "GROUP BY cluster_id "
                "ORDER BY quotable_count DESC, cluster_id"
            )
            clusters = [dict(r) for r in rows]
        return HTMLResponse(_draft_index_html(clusters))

    dreams = await _fetch_dreams_in_cluster(cluster_id)
    motif = ""
    if dreams:
        motif = (dreams[0].get("cluster_label") or "").strip()
    return HTMLResponse(_draft_form_html(cluster_id, dreams, motif))


@app.post("/clusters/publish", include_in_schema=False)
async def clusters_publish(request: Request):
    """Publish a cluster snapshot. Steward-token-gated. Idempotent on
    signature collisions — returns 200 with the existing publication."""
    if not STEWARD_TOKENS:
        raise HTTPException(503, "stewardship not configured")
    steward_name = _is_steward_request(request)
    if not steward_name:
        raise HTTPException(401, "steward authentication required")

    form = await request.form()
    try:
        cluster_id = int(form.get("cluster_id") or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, "cluster_id required")
    rep_ids_raw = form.getlist("representative_dream_ids")
    try:
        rep_ids = sorted({int(x) for x in rep_ids_raw if str(x).strip()})
    except (TypeError, ValueError):
        raise HTTPException(400, "representative_dream_ids must be integers")
    if not (3 <= len(rep_ids) <= 7):
        raise HTTPException(400, "representative_dream_ids: pick 3 to 7")
    display_name = (form.get("display_name") or "").strip()[:80] or None
    steward_note = (form.get("steward_note") or "").strip()[:800]
    related_raw = (form.get("related_concepts") or "").strip()[:200]
    related = [c.strip() for c in related_raw.split(",") if c.strip()][:8]

    # Validate every dream id is currently a member of cluster_id, quotable,
    # and not archived. (We check membership at publish time; the signature
    # locks the selection so future re-clusterings don't change this page.)
    eligible_ids = {int(d["id"]) for d in await _fetch_dreams_in_cluster(cluster_id)}
    for rid in rep_ids:
        if rid not in eligible_ids:
            raise HTTPException(
                422,
                f"dream {rid} is not a quotable member of cluster {cluster_id}",
            )

    # Bake fragments + motif at publish time. Motif comes from the most
    # recent cluster_label for this cluster.
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, raw_text, dreamworld_text, cluster_label "
            "FROM prompts WHERE id IN ({}) ORDER BY id".format(
                ",".join("?" * len(rep_ids))
            ),
            tuple(rep_ids),
        )
        dreams = [dict(r) for r in await cur.fetchall()]
    if len(dreams) != len(rep_ids):
        raise HTTPException(422, "some representative ids no longer exist")

    motif = ""
    for d in dreams:
        if d.get("cluster_label"):
            motif = (d["cluster_label"] or "").strip()
            break

    fragments_html = "\n".join(
        _bake_fragment_html(
            int(d["id"]),
            (d.get("dreamworld_text") or d.get("raw_text") or ""),
        )
        for d in dreams
    )

    signature = _compute_cluster_signature(rep_ids)

    # Idempotency: if a publication with this signature already exists,
    # return it unchanged. "First witnessed publication wins" — stewards
    # who want different metadata under the same selection use edit-metadata.
    existing = await _fetch_publication(signature)
    if existing:
        return {
            "signature": signature,
            "url": f"/clusters/{signature}",
            "idempotent": True,
            "published_at": existing.get("published_at"),
        }

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cluster_publications ("
            "  signature, cluster_id_at_publication, motif_phrase, "
            "  steward_name, display_name, steward_note, "
            "  embedding_model, clustering_algorithm, clustering_version, "
            "  member_count, representative_dream_ids, "
            "  representative_fragments_html, related_concepts"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                signature, cluster_id, motif,
                steward_name, display_name, steward_note,
                EMBEDDING_MODEL, CLUSTERING_ALGORITHM, CLUSTERING_VERSION,
                len(rep_ids),
                json.dumps(rep_ids),
                fragments_html,
                json.dumps(related),
            ),
        )
        await db.commit()
    await _audit_steward(steward_name, f"/clusters/publish:{signature}")

    # If browser, redirect to the rendered page. If API, return JSON.
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" in accept:
        return RedirectResponse(url=f"/clusters/{signature}", status_code=303)
    return {"signature": signature, "url": f"/clusters/{signature}", "idempotent": False}


# Reserved sub-paths that share the /clusters/ prefix but aren't signatures.
# Starlette matches routes in registration order, so /clusters/{signature}
# would otherwise absorb /clusters/published and /clusters/draft. Listing
# them here as guards before the catch-all keeps the routing correct
# without re-ordering long blocks of code below.
_CLUSTERS_RESERVED = {"published", "draft"}


@app.get("/clusters/{signature}", include_in_schema=False)
async def cluster_page(signature: str, request: Request):
    """Public, server-rendered cluster page. Stable URL — page renders
    forever (with retraction notice if retracted)."""
    if signature in _CLUSTERS_RESERVED:
        # /clusters/published and /clusters/draft handlers are defined later
        # in this file; without this guard they'd be shadowed.
        if signature == "published":
            return await clusters_published(request)
        if signature == "draft":
            return await clusters_draft(request)
    pub = await _fetch_publication(signature)
    if not pub:
        raise HTTPException(404, "cluster page not found")
    contests = await _fetch_contest_count(signature)
    related = []
    try:
        related = json.loads(pub.get("related_concepts") or "[]")
    except Exception:
        related = []

    title = pub.get("display_name") or pub.get("steward_name") or "Witnessed cluster"
    motif = pub.get("motif_phrase") or "(no label)"
    note = pub.get("steward_note") or ""
    fragments = pub.get("representative_fragments_html") or ""
    retracted = bool(pub.get("retracted_at"))

    related_html = ""
    if related:
        chips = "".join(
            f'<span class="rc-chip">{_html_escape(str(c))}</span>'
            for c in related[:8]
        )
        related_html = f'<div class="related"><div class="rc-label">related concepts</div>{chips}</div>'

    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root{--bg:#050a12;--fg:#c8dff0;--accent:#7aa8c8;--muted:#5a7a99;--line:#1a2a3a;}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg);margin:0;font-weight:300;line-height:1.7}
.nav{position:sticky;top:0;padding:14px 24px;background:rgba(5,10,18,0.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;z-index:10;backdrop-filter:blur(8px)}
.nav-title{font-size:13px;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase}
.nav-links{display:flex;gap:18px;margin-left:auto}
.nav-links a{font-size:11px;color:var(--muted);text-decoration:none;letter-spacing:0.05em}
.container{max-width:680px;margin:0 auto;padding:42px 24px 80px}
.eyebrow{font-size:10px;letter-spacing:0.16em;color:var(--muted);text-transform:uppercase;margin-bottom:6px}
h1{font-size:24px;color:var(--accent);font-weight:300;letter-spacing:0.04em;margin:0 0 4px}
.motif{font-size:13px;color:var(--muted);font-style:italic;margin:0 0 26px}
.steward-note{font-size:15px;color:var(--fg);margin:0 0 30px;line-height:1.65}
.fragments-label{font-size:10px;letter-spacing:0.16em;color:var(--muted);text-transform:uppercase;margin-bottom:10px}
.dream-fragment{margin:0 0 14px;padding:14px 16px;border-left:2px solid var(--accent);background:rgba(122,168,200,0.04);font-size:14px;color:var(--fg);font-style:italic;line-height:1.65;border-radius:0 6px 6px 0}
.related{margin-top:24px}
.rc-label{font-size:10px;letter-spacing:0.16em;color:var(--muted);text-transform:uppercase;margin-bottom:8px}
.rc-chip{display:inline-block;font-size:11px;color:var(--accent);border:1px solid var(--line);border-radius:12px;padding:3px 10px;margin:0 6px 6px 0;background:rgba(122,168,200,0.04)}
.algo-note{margin-top:36px;padding:16px;border:1px solid var(--line);border-radius:6px;background:rgba(0,0,0,0.2);font-size:11px;color:var(--muted);font-family:'SF Mono','Menlo',monospace;line-height:1.7}
.algo-note .akey{color:var(--accent)}
.witness-note{margin-top:18px;font-size:12px;color:var(--muted);font-style:italic;line-height:1.7}
.contest-row{margin-top:24px;display:flex;align-items:center;gap:12px;font-size:11px}
.contest-row form{display:inline}
.contest-row button{background:none;border:1px solid var(--line);color:var(--muted);padding:6px 14px;border-radius:14px;font-size:11px;font-family:inherit;cursor:pointer}
.contest-row button:hover{border-color:var(--accent);color:var(--accent)}
.contest-count{color:var(--muted)}
.retracted{margin-bottom:18px;padding:12px 16px;border:1px solid #b08070;border-radius:6px;background:rgba(176,128,112,0.06);font-size:13px;color:#d4a08c}
"""

    retract_html = ""
    if retracted:
        retract_html = (
            '<div class="retracted"><strong>Retracted:</strong> '
            'The witnessing has been withdrawn by a steward. The page is preserved '
            'as a record that this gathering was once published, but should not be '
            'taken as the project\'s current reading.</div>'
        )

    contest_html = ""
    if not retracted:
        cc = (f' <span class="contest-count">contested {contests}×</span>'
              if contests > 0 else '')
        contest_html = f"""
<div class="contest-row">
  <form method="post" action="/clusters/{signature}/contest"><button type="submit">contest this name</button></form>
  {cc}
</div>"""

    body = f"""
<div class="container">
  {retract_html}
  <div class="eyebrow">a witnessed cluster</div>
  <h1>{_html_escape(title)}</h1>
  <p class="motif">algorithmic motif: {_html_escape(motif)}</p>
  <p class="steward-note">{_html_escape(note) if note else '<em>(no steward note)</em>'}</p>
  <div class="fragments-label">representative dreams</div>
  {fragments}
  {related_html}
  {contest_html}
  <div class="algo-note">
    <span class="akey">embedding model:</span> {_html_escape(pub.get("embedding_model") or "")}<br>
    <span class="akey">clustering algorithm:</span> {_html_escape(pub.get("clustering_algorithm") or "")}<br>
    <span class="akey">clustering version:</span> {_html_escape(pub.get("clustering_version") or "")}<br>
    <span class="akey">signature:</span> {_html_escape(signature)}<br>
    <span class="akey">members at publication:</span> {int(pub.get("member_count") or 0)}<br>
    <span class="akey">published at:</span> {_html_escape(pub.get("published_at") or "")}
  </div>
  <div class="witness-note">Names here are provisional and revisable. The algorithm gathered the field; a steward witnessed this particular gathering. The dreams are still themselves.</div>
</div>"""
    return HTMLResponse(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{_html_escape(title)} — Salish Sea Dreaming</title>"
        f"<style>{css}</style></head><body>"
        f"<nav class='nav'><div class='nav-title'>Cluster · {_html_escape(signature)}</div>"
        f"<div class='nav-links'><a href='/'>Home</a><a href='/clusters/published'>Published</a><a href='/cloud'>Cloud</a></div></nav>"
        f"{body}</body></html>"
    )


@app.get("/clusters/published", include_in_schema=False)
async def clusters_published(request: Request):
    """Public index of all current (non-retracted leaf) cluster publications."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            "SELECT signature, motif_phrase, display_name, steward_name, "
            "       steward_note, member_count, published_at, retracted_at "
            "FROM cluster_publications "
            "WHERE retracted_at IS NULL "
            "AND signature NOT IN ("
            "  SELECT parent_signature FROM cluster_publications "
            "  WHERE parent_signature IS NOT NULL AND retracted_at IS NULL"
            ") "
            "ORDER BY published_at DESC"
        )
        publications = [dict(r) for r in rows]

    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400&display=swap');
:root{--bg:#050a12;--fg:#c8dff0;--accent:#7aa8c8;--muted:#5a7a99;--line:#1a2a3a;}
*{box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--fg);margin:0;font-weight:300;line-height:1.6}
.nav{position:sticky;top:0;padding:14px 24px;background:rgba(5,10,18,0.96);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:24px;z-index:10}
.nav-title{font-size:13px;color:var(--accent);letter-spacing:0.1em;text-transform:uppercase}
.nav-links{display:flex;gap:18px;margin-left:auto}
.nav-links a{font-size:11px;color:var(--muted);text-decoration:none;letter-spacing:0.05em}
.container{max-width:760px;margin:0 auto;padding:48px 24px 80px}
h1{font-size:22px;color:var(--accent);font-weight:300;letter-spacing:0.06em;margin:0 0 8px}
.tag{font-size:12px;color:var(--muted);margin:0 0 32px;font-style:italic}
.row{display:block;padding:18px 20px;border:1px solid var(--line);border-radius:6px;background:rgba(122,168,200,0.04);margin-bottom:12px;text-decoration:none;color:var(--fg);transition:border-color .2s,background .2s}
.row:hover{border-color:var(--accent);background:rgba(122,168,200,0.08)}
.row .name{font-size:15px;color:var(--accent);margin-bottom:5px}
.row .motif{font-size:12px;color:var(--muted);font-style:italic;margin-bottom:8px}
.row .note{font-size:13px;color:var(--fg);line-height:1.55;margin-bottom:8px}
.row .meta{font-size:10px;color:var(--muted);letter-spacing:0.06em}
"""
    if not publications:
        rows_html = '<p class="tag">No witnessed clusters published yet.</p>'
    else:
        rows_html = ""
        for p in publications:
            note = (p.get("steward_note") or "").strip()
            if len(note) > 200:
                note = note[:200] + "…"
            rows_html += (
                f'<a class="row" href="/clusters/{_html_escape(p["signature"])}">'
                f'<div class="name">{_html_escape(p.get("display_name") or "Witnessed cluster")}</div>'
                f'<div class="motif">{_html_escape(p.get("motif_phrase") or "")}</div>'
                f'<div class="note">{_html_escape(note) if note else "<em>(no note)</em>"}</div>'
                f'<div class="meta">witnessed by {_html_escape(p.get("steward_name") or "")}'
                f' · {int(p.get("member_count") or 0)} dreams · {_html_escape((p.get("published_at") or "")[:19])}</div>'
                f'</a>'
            )
    return HTMLResponse(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Published clusters — Salish Sea Dreaming</title>"
        f"<style>{css}</style></head><body>"
        f"<nav class='nav'><div class='nav-title'>Published clusters</div>"
        f"<div class='nav-links'><a href='/'>Home</a><a href='/cloud'>Cloud</a></div></nav>"
        f"<div class='container'><h1>Witnessed clusters</h1>"
        f"<p class='tag'>Each page is a steward-witnessed snapshot. Names are provisional and revisable; pages persist forever.</p>"
        f"{rows_html}</div></body></html>"
    )


# Per-IP rate limit for /clusters/{sig}/contest. Reuses the chat rate-limit
# pattern but with a separate map so they don't share cooldowns.
contest_rate_limit_map: dict[str, datetime] = {}
CONTEST_RATE_LIMIT_SECONDS = 60


@app.post("/clusters/{signature}/contest", include_in_schema=False)
async def cluster_contest(signature: str, request: Request):
    """Anonymous contest action. Rate-limited 1/min/IP."""
    pub = await _fetch_publication(signature)
    if not pub:
        raise HTTPException(404, "cluster page not found")
    if pub.get("retracted_at"):
        raise HTTPException(410, "cluster page retracted")

    ip = get_client_ip(request)
    now = datetime.utcnow()
    last = contest_rate_limit_map.get(ip)
    if last and (now - last).total_seconds() < CONTEST_RATE_LIMIT_SECONDS:
        raise HTTPException(429, "please wait a moment before contesting again")
    contest_rate_limit_map[ip] = now

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cluster_contests (signature) VALUES (?)",
            (signature,),
        )
        await db.commit()

    return RedirectResponse(url=f"/clusters/{signature}", status_code=303)


@app.post("/clusters/{signature}/retract", include_in_schema=False)
async def cluster_retract(signature: str, request: Request):
    """Steward-only. Sets retracted_at; page still renders with notice."""
    if not STEWARD_TOKENS:
        raise HTTPException(503, "stewardship not configured")
    name = _is_steward_request(request)
    if not name:
        raise HTTPException(401, "steward authentication required")

    pub = await _fetch_publication(signature)
    if not pub:
        raise HTTPException(404, "cluster page not found")
    if pub.get("retracted_at"):
        return {"signature": signature, "already_retracted": True}

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE cluster_publications SET retracted_at = CURRENT_TIMESTAMP "
            "WHERE signature = ? AND retracted_at IS NULL",
            (signature,),
        )
        await db.commit()
    await _audit_steward(name, f"/clusters/retract:{signature}")
    return {"signature": signature, "retracted": True, "steward": name}


# ---------------------------------------------------------------------------
# Ontology route (explicit — guarantees application/ld+json content-type).
# Must be registered BEFORE the /ontology StaticFiles mount so the root path
# hits the typed FileResponse handler rather than StaticFiles' default text/plain.
# ---------------------------------------------------------------------------

_ontology_path = BASE_DIR / "static" / "ontology" / "ssd-ontology.jsonld"


@app.api_route("/ontology/", methods=["GET", "HEAD"], include_in_schema=False)
@app.api_route("/ontology", methods=["GET", "HEAD"], include_in_schema=False)
async def ontology_root():
    from fastapi.responses import FileResponse
    if not _ontology_path.exists():
        raise HTTPException(status_code=404, detail="Ontology file not found")
    return FileResponse(_ontology_path, media_type="application/ld+json")


# ---------------------------------------------------------------------------
# Static files (LAST — after all API routes)
# ---------------------------------------------------------------------------

_graph_dir = BASE_DIR / "static"
if _graph_dir.exists():
    app.mount("/graph-assets", StaticFiles(directory=str(_graph_dir)), name="graph-assets")
else:
    logger.warning("static/ dir not found — /graph will not be served")

_ontology_dir = BASE_DIR / "static" / "ontology"
if _ontology_dir.exists():
    app.mount("/ontology", StaticFiles(directory=str(_ontology_dir), html=False), name="ontology")

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

    # Stage 2 startup warnings — surface THEME_HASH_KEY status loudly so
    # operators see whether forms are stable across restarts.
    if _THEME_HASH_KEY_EPHEMERAL:
        logger.warning(
            "THEME_HASH_KEY is unset or invalid — using ephemeral key. "
            "All open /consent forms invalidate on every restart. "
            "For production, set THEME_HASH_KEY=<64 hex chars> in /etc/.../.env "
            "(generate via `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
        )

    # Dreamworld 3D: schema migration + seed + periodic UMAP (non-blocking)
    await migrate_dreams_schema()
    # Foundation: consent toggles + consent_token + archived_at
    await migrate_foundation_schema()
    # Stage 2: consent_flags (umap_stale)
    await migrate_stage2_schema()
    # Stage 3: cluster_publications + cluster_contests + cluster_publication_edits
    await migrate_stage3_schema()
    asyncio.create_task(_seed_and_umap_loop())
    # Stage 2: periodic UMAP retrigger when consent flips have set the
    # stale flag. Decoupled from /chat so it can't be blocked by user load.
    asyncio.create_task(_consent_stale_umap_loop())

    # Start background queue worker
    asyncio.create_task(queue_worker())
    # Per-minute metrics logger (submission rate + queue depth)
    asyncio.create_task(metrics_logger())
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
