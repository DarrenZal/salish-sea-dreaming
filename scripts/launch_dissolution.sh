#!/bin/bash
# ===========================================================================
# Salish Sea Dreaming — Dissolution Variants Launcher
# ===========================================================================
# Uploads dissolution_variants.py to Node 3, downloads depth maps from Node 1,
# then launches with nohup.
#
# Usage: bash scripts/launch_dissolution.sh
#
# Node 1 (source): model-deployment-0b50s.paas.ai.telus.com
# Node 3 (target): ssd-style-transfer-3-0b50s.paas.ai.telus.com
# ===========================================================================

set -euo pipefail

NODE1_URL="https://model-deployment-0b50s.paas.ai.telus.com"
NODE1_TOKEN="8f6ceea09691892cf2d19dc7466669ea"

NODE3_URL="https://ssd-style-transfer-3-0b50s.paas.ai.telus.com"
NODE3_TOKEN="ada49fecb49f8b4a4d53a5fb44f91af0"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================================="
echo "Salish Sea Dreaming — Dissolution Variants Launcher"
echo "=================================================="
echo ""

# --------------------------------------------------------------------------
# Step 1: Upload the dissolution_variants.py script to Node 3
# --------------------------------------------------------------------------
echo "[1/4] Uploading dissolution_variants.py to Node 3..."

SCRIPT_CONTENT=$(python3 -c "
import json, sys
with open('${SCRIPT_DIR}/dissolution_variants.py', 'r') as f:
    content = f.read()
payload = {
    'type': 'file',
    'format': 'text',
    'name': 'dissolution_variants.py',
    'path': 'dissolution_variants.py',
    'content': content
}
json.dump(payload, sys.stdout)
")

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/contents/dissolution_variants.py" \
    -d "${SCRIPT_CONTENT}")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "201" ]; then
    echo "  OK (HTTP ${STATUS})"
else
    echo "  FAILED (HTTP ${STATUS})"
    exit 1
fi

# --------------------------------------------------------------------------
# Step 2: Upload the download-and-launch notebook/script to Node 3
# --------------------------------------------------------------------------
echo "[2/4] Creating depth map download + launch script on Node 3..."

# This Python script runs on Node 3: downloads depth maps from Node 1 via
# the Jupyter API, then launches dissolution_variants.py with nohup.
DOWNLOAD_SCRIPT=$(cat <<'PYEOF'
#!/usr/bin/env python3
"""Download depth maps from Node 1 and launch dissolution experiments."""
import os
import sys
import json
import urllib.request
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

NODE1_URL = "https://model-deployment-0b50s.paas.ai.telus.com"
NODE1_TOKEN = "8f6ceea09691892cf2d19dc7466669ea"

ROOT = Path("/home/jovyan/dissolution_variants")
SALMON_DIR = ROOT / "depth" / "salmon_roots"
BOIDS_DIR = ROOT / "depth" / "school_murmuration"

SALMON_DIR.mkdir(parents=True, exist_ok=True)
BOIDS_DIR.mkdir(parents=True, exist_ok=True)


def download_file(src_path, dest_path):
    """Download a single file from Node 1 Jupyter API."""
    url = f"{NODE1_URL}/api/contents/{src_path}?content=1&type=file"
    req = urllib.request.Request(url, headers={"Authorization": f"token {NODE1_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        # Binary files come base64-encoded
        import base64
        content = base64.b64decode(data["content"])
        with open(dest_path, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  FAILED: {src_path}: {e}", file=sys.stderr)
        return False


def list_files(api_path):
    """List files in a Node 1 directory."""
    url = f"{NODE1_URL}/api/contents/{api_path}"
    req = urllib.request.Request(url, headers={"Authorization": f"token {NODE1_TOKEN}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return [item for item in data.get("content", []) if item["type"] == "file"]


def download_depth_set(api_path, local_dir, prefix_filter="frame_"):
    """Download all depth maps from a Node 1 directory."""
    print(f"\nListing {api_path}...")
    files = list_files(api_path)
    # Filter to frame_ files (higher resolution)
    target_files = [f for f in files if f["name"].startswith(prefix_filter)]
    if not target_files:
        # Fall back to all PNG files
        target_files = [f for f in files if f["name"].endswith(".png")]

    existing = set(os.listdir(local_dir)) if os.path.exists(local_dir) else set()
    to_download = [f for f in target_files if f["name"] not in existing]

    print(f"  Found {len(target_files)} files, {len(existing)} already downloaded, "
          f"{len(to_download)} to download")

    if not to_download:
        print("  All files already present.")
        return len(target_files)

    downloaded = 0
    failed = 0
    t0 = time.time()

    # Download with thread pool for speed
    def dl(item):
        dest = os.path.join(local_dir, item["name"])
        return download_file(item["path"], dest), item["name"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(dl, item) for item in to_download]
        for i, future in enumerate(as_completed(futures)):
            ok, name = future.result()
            if ok:
                downloaded += 1
            else:
                failed += 1
            if (downloaded + failed) % 50 == 0:
                elapsed = time.time() - t0
                print(f"  Progress: {downloaded + failed}/{len(to_download)} "
                      f"({elapsed:.0f}s)")

    elapsed = time.time() - t0
    print(f"  Done: {downloaded} downloaded, {failed} failed in {elapsed:.0f}s")
    return len(target_files) - failed


# ── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Downloading depth maps from Node 1...")
    print("=" * 60)

    # Download salmon→roots depth maps (450 frames)
    salmon_count = download_depth_set(
        "explore/exp2_salmon_roots/depth",
        str(SALMON_DIR),
        prefix_filter="frame_",
    )

    # Download school→murmuration depth maps (90 frames)
    boids_count = download_depth_set(
        "blender_morph/output/school_to_murmuration_depth",
        str(BOIDS_DIR),
        prefix_filter="frame_",
    )

    print(f"\nDepth maps ready: salmon={salmon_count}, boids={boids_count}")
    print("\nLaunching dissolution_variants.py with nohup...")

    # Launch the main experiment script
    cmd = (
        "cd /home/jovyan && "
        "nohup python3 dissolution_variants.py "
        "> dissolution_variants/nohup.log 2>&1 &"
    )
    os.system(cmd)

    # Verify it started
    time.sleep(2)
    pid_check = subprocess.run(
        ["pgrep", "-f", "dissolution_variants.py"],
        capture_output=True, text=True,
    )
    if pid_check.stdout.strip():
        pids = pid_check.stdout.strip().split("\n")
        print(f"\nLaunched! PIDs: {', '.join(pids)}")
        print(f"Monitor: tail -f /home/jovyan/dissolution_variants/progress.log")
        print(f"nohup log: tail -f /home/jovyan/dissolution_variants/nohup.log")
    else:
        print("\nWARNING: Process may not have started. Check nohup.log.")
PYEOF
)

# Upload the download+launch script
LAUNCH_PAYLOAD=$(python3 -c "
import json, sys
content = sys.stdin.read()
payload = {
    'type': 'file',
    'format': 'text',
    'name': 'launch_dissolution_download.py',
    'path': 'launch_dissolution_download.py',
    'content': content
}
json.dump(payload, sys.stdout)
" <<< "${DOWNLOAD_SCRIPT}")

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/contents/launch_dissolution_download.py" \
    -d "${LAUNCH_PAYLOAD}")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "201" ]; then
    echo "  OK (HTTP ${STATUS})"
else
    echo "  FAILED (HTTP ${STATUS})"
    exit 1
fi

# --------------------------------------------------------------------------
# Step 3: Execute the download + launch script on Node 3 via Jupyter kernel
# --------------------------------------------------------------------------
echo "[3/4] Starting kernel and executing download + launch on Node 3..."

# Create a kernel
KERNEL_RESP=$(curl -s \
    -X POST \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/kernels" \
    -d '{"name": "python3"}')

KERNEL_ID=$(echo "${KERNEL_RESP}" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "  Kernel ID: ${KERNEL_ID}"

# Give kernel time to start
sleep 3

# Execute the launch script via kernel
EXEC_CODE="exec(open('/home/jovyan/launch_dissolution_download.py').read())"
EXEC_PAYLOAD=$(python3 -c "
import json, sys, uuid
payload = {
    'header': {
        'msg_id': str(uuid.uuid4()),
        'msg_type': 'execute_request',
        'username': '',
        'session': str(uuid.uuid4()),
        'version': '5.3'
    },
    'parent_header': {},
    'metadata': {},
    'content': {
        'code': '''${EXEC_CODE}''',
        'silent': False,
        'store_history': False,
        'user_expressions': {},
        'allow_stdin': False,
        'stop_on_error': True
    },
    'buffers': [],
    'channel': 'shell'
}
json.dump(payload, sys.stdout)
")

# Use the REST API to execute code
curl -s -o /dev/null \
    -X POST \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/kernels/${KERNEL_ID}/execute" \
    -d "{\"code\": \"${EXEC_CODE}\"}" 2>/dev/null || true

# Alternative: use a notebook approach
echo "  Executing via notebook API..."

# Create an execution notebook
EXEC_NB=$(python3 -c "
import json
nb = {
    'cells': [{
        'cell_type': 'code',
        'source': 'exec(open(\"/home/jovyan/launch_dissolution_download.py\").read())',
        'metadata': {},
        'outputs': [],
        'execution_count': None
    }],
    'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.10.0'}
    },
    'nbformat': 4,
    'nbformat_minor': 5
}
payload = {
    'type': 'notebook',
    'format': 'json',
    'name': 'run_dissolution.ipynb',
    'path': 'run_dissolution.ipynb',
    'content': nb
}
json.dump(payload, sys.stdout)
")

curl -s -o /dev/null -w "" \
    -X PUT \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/contents/run_dissolution.ipynb" \
    -d "${EXEC_NB}"

echo "  Notebook created. Executing..."

# --------------------------------------------------------------------------
# Step 4: Use terminal API for reliable execution
# --------------------------------------------------------------------------
echo "[4/4] Creating terminal session for reliable nohup execution..."

# Create a terminal
TERM_RESP=$(curl -s \
    -X POST \
    -H "Authorization: token ${NODE3_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE3_URL}/api/terminals" \
    -d '{}')

TERM_NAME=$(echo "${TERM_RESP}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" 2>/dev/null || echo "")

if [ -n "${TERM_NAME}" ]; then
    echo "  Terminal: ${TERM_NAME}"
    echo "  Sending execution command..."

    # The terminal WebSocket approach is complex; instead, use the kernel execute endpoint
    # that most JupyterHub installations support
    echo ""
    echo "  NOTE: Terminal created but WebSocket execution requires manual step."
    echo "  Opening notebook in browser for execution instead."
else
    echo "  Terminal API not available. Using kernel execution."
fi

echo ""
echo "=================================================="
echo "FILES UPLOADED TO NODE 3:"
echo "  - dissolution_variants.py (main experiment script)"
echo "  - launch_dissolution_download.py (download + launch helper)"
echo "  - run_dissolution.ipynb (execution notebook)"
echo ""
echo "TO START THE EXPERIMENTS:"
echo "  1. Open: ${NODE3_URL}/notebooks/run_dissolution.ipynb?token=${NODE3_TOKEN}"
echo "  2. Click 'Run' on the cell"
echo "  3. Or SSH/terminal: python3 /home/jovyan/launch_dissolution_download.py"
echo ""
echo "TO MONITOR PROGRESS:"
echo "  - Progress log: tail -f /home/jovyan/dissolution_variants/progress.log"
echo "  - nohup log: tail -f /home/jovyan/dissolution_variants/nohup.log"
echo ""
echo "EXPECTED OUTPUT:"
echo "  /home/jovyan/dissolution_variants/output/salmon_to_forest_30fps.mp4"
echo "  /home/jovyan/dissolution_variants/output/salmon_to_forest_16fps.mp4"
echo "  /home/jovyan/dissolution_variants/output/kelp_to_forest_30fps.mp4"
echo "  /home/jovyan/dissolution_variants/output/kelp_to_forest_16fps.mp4"
echo "  /home/jovyan/dissolution_variants/output/dreaming_abstract_30fps.mp4"
echo "  /home/jovyan/dissolution_variants/output/dreaming_abstract_16fps.mp4"
echo "=================================================="
