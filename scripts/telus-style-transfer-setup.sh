#!/bin/bash
# Upload style transfer notebook + assets to TELUS JupyterLab
# Run this once the pod is online at salishsea-0b50s.paas.ai.telus.com
#
# Usage: bash scripts/telus-style-transfer-setup.sh

set -e

TELUS_URL="https://salishsea-0b50s.paas.ai.telus.com"
TOKEN=$(grep Jupyter_REST_API .env | cut -d= -f2)
REMOTE_DIR="style-transfer"

echo "=== TELUS Style Transfer Setup ==="
echo "URL: $TELUS_URL"
echo "Remote dir: /home/jovyan/$REMOTE_DIR/"
echo ""

# Check if pod is online
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOKEN" "$TELUS_URL/api/contents")
if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: TELUS pod not responding (HTTP $HTTP_CODE)"
    echo "Start the pod from the TELUS console first, then re-run this script."
    exit 1
fi
echo "Pod is online."

# Create working directory
echo ""
echo "=== Creating remote directory ==="
curl -s -X PUT -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "directory"}' \
  "$TELUS_URL/api/contents/$REMOTE_DIR" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Created: {d.get(\"path\",\"?\")}')" 2>/dev/null || echo "  (directory may already exist)"

# Upload function for small files (< ~5MB, base64 via API)
upload_file() {
    local LOCAL_PATH="$1"
    local REMOTE_NAME="$2"
    local FNAME=$(basename "$LOCAL_PATH")
    [ -n "$REMOTE_NAME" ] && FNAME="$REMOTE_NAME"

    local SIZE=$(stat -f%z "$LOCAL_PATH" 2>/dev/null || stat -c%s "$LOCAL_PATH" 2>/dev/null)
    local SIZE_MB=$(echo "scale=1; $SIZE / 1048576" | bc)

    echo "  Uploading $FNAME ($SIZE_MB MB)..."

    # Base64 encode and upload via contents API
    local B64=$(base64 < "$LOCAL_PATH")
    local PAYLOAD=$(python3 -c "
import json, sys
with open('$LOCAL_PATH', 'rb') as f:
    import base64
    content = base64.b64encode(f.read()).decode()
print(json.dumps({
    'type': 'file',
    'format': 'base64',
    'name': '$FNAME',
    'content': content
}))
")

    HTTP_CODE=$(echo "$PAYLOAD" | curl -s -o /dev/null -w "%{http_code}" \
      -X PUT -H "Authorization: token $TOKEN" \
      -H "Content-Type: application/json" \
      -d @- \
      "$TELUS_URL/api/contents/$REMOTE_DIR/$FNAME")

    if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
        echo "    OK ($HTTP_CODE)"
    else
        echo "    FAILED ($HTTP_CODE)"
    fi
}

# Upload function for large files via terminal + curl
upload_large_file() {
    local LOCAL_PATH="$1"
    local REMOTE_NAME="$2"
    local FNAME=$(basename "$LOCAL_PATH")
    [ -n "$REMOTE_NAME" ] && FNAME="$REMOTE_NAME"

    local SIZE=$(stat -f%z "$LOCAL_PATH" 2>/dev/null || stat -c%s "$LOCAL_PATH" 2>/dev/null)
    local SIZE_MB=$(echo "scale=1; $SIZE / 1048576" | bc)

    echo "  $FNAME ($SIZE_MB MB) — too large for API upload"
    echo "    Upload manually via JupyterLab file browser to $REMOTE_DIR/"
    echo "    Or drag-and-drop in the browser"
}

echo ""
echo "=== Uploading notebook ==="
upload_file "notebooks/style-transfer-video.ipynb"

echo ""
echo "=== Uploading LoRA weights ==="
upload_file "briony-lora/briony_watercolor_v1.safetensors"

echo ""
echo "=== Uploading Briony style reference (for NST) ==="
upload_file "training-data/briony-marine-colour/whole-kelp-forest-ecosystem.png"

echo ""
echo "=== Hero subclips ==="
# H5 is small enough (63MB) — but still too large for base64 API
# All clips need manual upload via JupyterLab file browser
echo "  These need manual upload via JupyterLab file browser:"
for f in media/hero-subclips/H*.mp4; do
    SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
    SIZE_MB=$(echo "scale=1; $SIZE / 1048576" | bc)
    echo "    $(basename $f) ($SIZE_MB MB)"
done
echo ""
echo "  Steps:"
echo "  1. Open $TELUS_URL in browser"
echo "  2. Navigate to $REMOTE_DIR/ folder"
echo "  3. Drag and drop the .mp4 files from media/hero-subclips/"
echo "  4. Start with H5_reef_garden.mp4 (smallest, 63 MB)"

echo ""
echo "=== Done ==="
echo ""
echo "Next steps:"
echo "  1. Upload hero clips via browser (see above)"
echo "  2. Open style-transfer-video.ipynb in JupyterLab"
echo "  3. Run cell 0 (setup) to install dependencies"
echo "  4. Run cells sequentially — start with Technique A (LoRA img2img)"
echo ""
echo "Notebook URL: $TELUS_URL/lab/tree/$REMOTE_DIR/style-transfer-video.ipynb"
