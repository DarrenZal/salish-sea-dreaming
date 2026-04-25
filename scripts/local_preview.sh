#!/usr/bin/env bash
#
# local_preview.sh — Boot scripts/gallery_server.py against a sandbox BASE_DIR.
#
# Purpose: preview chat-corpus changes (static/ssd-cards.json, static/ssd-context-docs.json)
# locally on port 9001 without touching the production gallery server on poly:9000.
#
# Approach (no source edits to gallery_server.py):
#   gallery_server.py computes BASE_DIR = Path(__file__).parent.parent. We build a sandbox
#   directory whose layout mirrors the repo: <sandbox>/scripts/ symlinked to the real
#   scripts/, plus <sandbox>/static/ holding editable JSON copies (ontology/ symlinked
#   from real repo so /ontology mount still works), plus <sandbox>/web/ symlinked
#   so /static mount still works, plus <sandbox>/.env symlinked from real repo if present.
#   uvicorn is invoked with PYTHONPATH=<sandbox>, so `scripts.gallery_server` loads
#   from <sandbox>/scripts/gallery_server.py (a symlink to the real file). Because
#   __file__ resolves through the symlink target via Path(__file__).parent.parent,
#   we use Path.parent (lexical), not resolve(), and gallery_server uses .parent.parent
#   without resolve() — confirmed at line 55. So __file__ stays under <sandbox>/scripts/
#   and BASE_DIR == <sandbox>. Verified: Python's __file__ for a symlinked module is
#   the symlink path itself, and Path(...).parent is purely lexical.

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT="/Users/darrenzal/projects/salish-sea-dreaming"
VENV_DIR="${REPO_ROOT}/venv"
PORT=9001
DEFAULT_SANDBOX="/tmp/ssd-sandbox-$(date +%Y%m%d-%H%M)"

SANDBOX_DIR="${1:-${DEFAULT_SANDBOX}}"

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

# Production JSONs must exist
SRC_CARDS="${REPO_ROOT}/static/ssd-cards.json"
SRC_DOCS="${REPO_ROOT}/static/ssd-context-docs.json"

if [[ ! -f "${SRC_CARDS}" ]]; then
    echo "ERROR: production cards JSON missing: ${SRC_CARDS}" >&2
    exit 1
fi
if [[ ! -f "${SRC_DOCS}" ]]; then
    echo "ERROR: production docs JSON missing: ${SRC_DOCS}" >&2
    exit 1
fi

# Port 9001 must be free
if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "ERROR: port ${PORT} already in use. Free it first:" >&2
    echo "  lsof -nP -iTCP:${PORT} -sTCP:LISTEN" >&2
    exit 1
fi

# Venv check (don't auto-install)
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "ERROR: Python venv not found at ${VENV_DIR}" >&2
    echo "Create it and install deps:" >&2
    echo "  python3 -m venv ${VENV_DIR} && ${VENV_DIR}/bin/pip install fastapi 'uvicorn[standard]' python-osc aiosqlite sse-starlette python-dotenv openai" >&2
    exit 1
fi

# Verify required deps inside venv
MISSING_DEPS=$("${VENV_DIR}/bin/python" - <<'PY'
import importlib
mods = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn[standard]"),
    ("pythonosc", "python-osc"),
    ("aiosqlite", "aiosqlite"),
    ("sse_starlette", "sse-starlette"),
    ("dotenv", "python-dotenv"),
    ("openai", "openai"),
]
missing = []
for mod, pkg in mods:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(pkg)
print(" ".join(missing))
PY
)

if [[ -n "${MISSING_DEPS}" ]]; then
    echo "ERROR: missing Python deps in venv: ${MISSING_DEPS}" >&2
    echo "Install with:" >&2
    echo "  ${VENV_DIR}/bin/pip install ${MISSING_DEPS}" >&2
    exit 1
fi

# Sandbox dir overwrite prompt
if [[ -e "${SANDBOX_DIR}" ]]; then
    echo "WARNING: sandbox dir already exists: ${SANDBOX_DIR}"
    printf "Overwrite? [y/N] "
    read -r REPLY
    case "${REPLY}" in
        y|Y|yes|YES)
            echo "Removing ${SANDBOX_DIR}"
            rm -rf "${SANDBOX_DIR}"
            ;;
        *)
            echo "Aborting (no changes made)."
            exit 1
            ;;
    esac
fi

# ---------------------------------------------------------------------------
# Build sandbox
# ---------------------------------------------------------------------------

mkdir -p "${SANDBOX_DIR}/static"

# Symlink scripts/ — gallery_server.py needs __file__.parent.parent == sandbox
ln -s "${REPO_ROOT}/scripts" "${SANDBOX_DIR}/scripts"

# Symlink web/ so the /static mount still serves the visitor-app frontend
if [[ -d "${REPO_ROOT}/web" ]]; then
    ln -s "${REPO_ROOT}/web" "${SANDBOX_DIR}/web"
fi

# Symlink .env if present (chat LLM keys, OpenAI key, etc.)
if [[ -f "${REPO_ROOT}/.env" ]]; then
    ln -s "${REPO_ROOT}/.env" "${SANDBOX_DIR}/.env"
fi

# Copy editable chat-corpus JSONs (the whole point of this harness)
cp "${SRC_CARDS}" "${SANDBOX_DIR}/static/ssd-cards.json"
cp "${SRC_DOCS}" "${SANDBOX_DIR}/static/ssd-context-docs.json"

# Symlink ontology/ subdir so /ontology mount + JSON-LD route still resolve
if [[ -d "${REPO_ROOT}/static/ontology" ]]; then
    ln -s "${REPO_ROOT}/static/ontology" "${SANDBOX_DIR}/static/ontology"
fi

# Empty logs/ to avoid clobbering the real one
mkdir -p "${SANDBOX_DIR}/logs"

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

cat <<BANNER

================================================================================
  Salish Sea Dreaming — local gallery_server preview (sandbox harness)
================================================================================
  Sandbox dir   : ${SANDBOX_DIR}
  Port          : ${PORT}    (production is 9000 — this harness avoids that)
  Cards JSON    : ${SANDBOX_DIR}/static/ssd-cards.json   (copy — editable)
  Docs JSON     : ${SANDBOX_DIR}/static/ssd-context-docs.json   (copy — editable)
  Scripts       : symlink -> ${REPO_ROOT}/scripts
  Web (UI)      : symlink -> ${REPO_ROOT}/web
  Ontology      : symlink -> ${REPO_ROOT}/static/ontology
  .env          : $([[ -L "${SANDBOX_DIR}/.env" ]] && echo "symlink -> ${REPO_ROOT}/.env" || echo "(none — chat LLM may be unavailable)")

  Test the chat endpoint:
    curl http://localhost:${PORT}/chat -X POST \\
      -H 'content-type: application/json' \\
      -d '{"message":"hello"}'

  Browse visitor app:
    open http://localhost:${PORT}/static/

  Edit the corpus JSONs in the sandbox dir and Ctrl-C + re-run this script
  (or restart uvicorn) to reload.

  Stop: Ctrl-C
================================================================================

BANNER

# ---------------------------------------------------------------------------
# Launch uvicorn
# ---------------------------------------------------------------------------

cd "${SANDBOX_DIR}"
export PYTHONPATH="${SANDBOX_DIR}"

exec "${VENV_DIR}/bin/python" -m uvicorn scripts.gallery_server:app \
    --host 127.0.0.1 \
    --port "${PORT}" \
    --workers 1 \
    --log-level info
