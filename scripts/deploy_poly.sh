#!/usr/bin/env bash
# deploy_poly.sh — Deploy gallery_server.py to poly and configure services.
# Run from repo root: bash scripts/deploy_poly.sh
set -euo pipefail

POLY="poly@37.27.48.12"
REMOTE_DIR="/home/poly/salish-sea-dreaming"

echo "==> Creating remote directories..."
ssh "$POLY" "mkdir -p $REMOTE_DIR/scripts $REMOTE_DIR/web $REMOTE_DIR/logs"

echo "==> Copying files to poly..."
scp scripts/gallery_server.py "$POLY:$REMOTE_DIR/scripts/"
scp web/visitor.html           "$POLY:$REMOTE_DIR/web/"
[ -f .env.example ] && scp .env.example "$POLY:$REMOTE_DIR/.env.example"

echo "==> Installing Python dependencies..."
ssh "$POLY" "
  cd $REMOTE_DIR
  python3 -m venv venv 2>/dev/null || true
  venv/bin/pip install -q --upgrade pip
  venv/bin/pip install -q fastapi 'uvicorn[standard]' python-osc aiosqlite sse-starlette python-dotenv
"

echo "==> Writing .env (no TD_HOST — poly uses SSE, not direct OSC)..."
ssh "$POLY" "cat > $REMOTE_DIR/.env" <<'EOF'
TD_HOST=
TD_OSC_PORT=7000
GALLERY_SERVER_PORT=9000
PROMPT_DWELL_SECONDS=30
MAX_QUEUE_SIZE=20
ADMIN_PASSWORD=salishsea
BASE_PROMPT=brionypenn watercolor painting, soft wet edges, natural pigment washes, ecological illustration, Salish Sea ecosystem
RATE_LIMIT_SECONDS=5
RATE_LIMIT_BYPASS_KEY=
TUNNEL_URL=https://ssd-gallery.cfargotunnel.com
EOF

echo "==> Installing systemd service for gallery server..."
ssh -t "$POLY" "sudo tee /etc/systemd/system/ssd-gallery.service" <<'UNIT'
[Unit]
Description=SSD Gallery Server
After=network.target

[Service]
User=poly
WorkingDirectory=/home/poly/salish-sea-dreaming
ExecStart=/home/poly/salish-sea-dreaming/venv/bin/uvicorn scripts.gallery_server:app --host 0.0.0.0 --port 9000 --workers 1
Restart=always
RestartSec=3
EnvironmentFile=/home/poly/salish-sea-dreaming/.env

[Install]
WantedBy=multi-user.target
UNIT

echo "==> Enabling and starting ssd-gallery service..."
ssh -t "$POLY" "sudo systemctl daemon-reload && sudo systemctl enable --now ssd-gallery"

echo "==> Waiting 3s for server to start..."
sleep 3

echo "==> Health check..."
curl -sf "http://37.27.48.12:9000/health" && echo "" && echo "Health check PASSED"

echo ""
echo "Done. Next: set up cloudflared tunnel on poly."
echo "  Run: ssh poly@37.27.48.12 'cloudflared tunnel login'"
echo "  (interactive — opens browser URL for Cloudflare auth)"
