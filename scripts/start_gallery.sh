#!/bin/bash
# Salish Sea Dreaming — Gallery startup script (Mac/Linux dev/test)
# For production Windows: use start_gallery.bat + NSSM services
# This script is for development testing only.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

mkdir -p logs

# Load .env if present
if [ -f ".env" ]; then
    set -a; source .env; set +a
fi

TUNNEL_URL="${TUNNEL_URL:-https://ssd-gallery.cfargotunnel.com}"
GALLERY_SERVER_PORT="${GALLERY_SERVER_PORT:-8000}"

echo "=== Salish Sea Dreaming Gallery ==="
echo "Starting backend server..."
python -m uvicorn scripts.gallery_server:app \
    --host 0.0.0.0 \
    --port "$GALLERY_SERVER_PORT" \
    --workers 1 \
    >> logs/server.log 2>&1 &
SERVER_PID=$!

echo "Starting audio monitor..."
python scripts/gallery_audio.py >> logs/audio.log 2>&1 &
AUDIO_PID=$!

echo "Server PID: $SERVER_PID"
echo "Audio PID: $AUDIO_PID"
echo ""

# Check if cloudflared is running
if pgrep -x cloudflared > /dev/null 2>&1; then
    echo "Cloudflare tunnel: RUNNING"
else
    echo "Cloudflare tunnel: NOT running (start manually: cloudflared tunnel run ssd-gallery)"
fi

echo ""
echo "Visitor URL:  $TUNNEL_URL"
echo "Admin URL:    $TUNNEL_URL/admin"
echo "Local health: http://localhost:$GALLERY_SERVER_PORT/health"
echo ""
echo "Logs: tail -f logs/server.log | tail -f logs/audio.log"
echo "Stop: kill $SERVER_PID $AUDIO_PID"
