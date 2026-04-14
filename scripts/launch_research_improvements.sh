#!/bin/bash
# ===========================================================================
# Salish Sea Dreaming — Research Improvements Launcher (Node 2)
# ===========================================================================
# Uploads research_improvements_node2.py to Node 2 and launches with nohup.
#
# Usage: bash scripts/launch_research_improvements.sh
#
# Node 2: ssd-style-transfer-2-0b50s.paas.ai.telus.com
# ===========================================================================

set -euo pipefail

NODE2_URL="https://ssd-style-transfer-2-0b50s.paas.ai.telus.com"
NODE2_TOKEN="15335440de57b5646cd4c25bdf1957d5"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_FILE="${SCRIPT_DIR}/research_improvements_node2.py"

echo "=================================================="
echo "Salish Sea Dreaming — Research Improvements Launcher"
echo "Target: Node 2 (${NODE2_URL})"
echo "=================================================="
echo ""

# --------------------------------------------------------------------------
# Step 1: Create research_improvements directory on Node 2
# --------------------------------------------------------------------------
echo "[1/4] Creating research_improvements directory..."

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE2_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE2_URL}/api/contents/research_improvements" \
    -d '{"type": "directory"}')

echo "  Directory: HTTP ${STATUS}"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE2_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE2_URL}/api/contents/research_improvements/output" \
    -d '{"type": "directory"}')

echo "  Output dir: HTTP ${STATUS}"

# --------------------------------------------------------------------------
# Step 2: Upload the main script
# --------------------------------------------------------------------------
echo "[2/4] Uploading research_improvements_node2.py..."

SCRIPT_CONTENT=$(python3 -c "
import json, sys
with open('${SCRIPT_FILE}', 'r') as f:
    content = f.read()
payload = {
    'type': 'file',
    'format': 'text',
    'name': 'research_improvements_node2.py',
    'path': 'research_improvements/research_improvements_node2.py',
    'content': content
}
json.dump(payload, sys.stdout)
")

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE2_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE2_URL}/api/contents/research_improvements/research_improvements_node2.py" \
    -d "${SCRIPT_CONTENT}")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "201" ]; then
    echo "  OK (HTTP ${STATUS})"
else
    echo "  FAILED (HTTP ${STATUS})"
    exit 1
fi

# --------------------------------------------------------------------------
# Step 3: Create launcher notebook
# --------------------------------------------------------------------------
echo "[3/4] Creating execution notebook..."

EXEC_NB=$(python3 -c "
import json, sys
nb = {
    'cells': [{
        'cell_type': 'code',
        'source': '''import subprocess, sys, time, os

# Launch with nohup
cmd = (
    'cd /home/jovyan/research_improvements && '
    'nohup python3 research_improvements_node2.py '
    '>> progress.log 2>&1 &'
)
os.system(cmd)

# Verify it started
time.sleep(3)
result = subprocess.run(['pgrep', '-f', 'research_improvements_node2.py'],
                       capture_output=True, text=True)
if result.stdout.strip():
    pids = result.stdout.strip().split(chr(10))
    print(f'Launched! PIDs: {\", \".join(pids)}')
    print(f'Monitor: tail -f /home/jovyan/research_improvements/progress.log')
else:
    print('WARNING: Process may not have started.')
    # Try direct execution for debugging
    print('Attempting direct execution...')
    os.system('cd /home/jovyan/research_improvements && python3 research_improvements_node2.py >> progress.log 2>&1 &')
    time.sleep(2)
    result = subprocess.run(['pgrep', '-f', 'research_improvements_node2.py'],
                           capture_output=True, text=True)
    print(f'PIDs after retry: {result.stdout.strip()}')
''',
        'metadata': {},
        'outputs': [],
        'execution_count': None
    },
    {
        'cell_type': 'code',
        'source': '# Monitor progress\\n!tail -50 /home/jovyan/research_improvements/progress.log',
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
    'name': 'run_research_improvements.ipynb',
    'path': 'run_research_improvements.ipynb',
    'content': nb
}
json.dump(payload, sys.stdout)
")

STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token ${NODE2_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE2_URL}/api/contents/run_research_improvements.ipynb" \
    -d "${EXEC_NB}")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "201" ]; then
    echo "  OK (HTTP ${STATUS})"
else
    echo "  FAILED (HTTP ${STATUS})"
fi

# --------------------------------------------------------------------------
# Step 4: Launch via kernel
# --------------------------------------------------------------------------
echo "[4/4] Launching via kernel execution..."

# Create a kernel
KERNEL_RESP=$(curl -s \
    -X POST \
    -H "Authorization: token ${NODE2_TOKEN}" \
    -H "Content-Type: application/json" \
    "${NODE2_URL}/api/kernels" \
    -d '{"name": "python3"}')

KERNEL_ID=$(echo "${KERNEL_RESP}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','NONE'))" 2>/dev/null || echo "NONE")

if [ "${KERNEL_ID}" = "NONE" ]; then
    echo "  Could not create kernel. Manual launch required."
else
    echo "  Kernel ID: ${KERNEL_ID}"
    sleep 3

    # Execute the launch command via kernel
    LAUNCH_CODE="import os, time, subprocess; os.makedirs('/home/jovyan/research_improvements', exist_ok=True); os.system('cd /home/jovyan/research_improvements && nohup python3 research_improvements_node2.py >> progress.log 2>&1 &'); time.sleep(3); r=subprocess.run(['pgrep','-f','research_improvements_node2.py'],capture_output=True,text=True); print('PIDs:',r.stdout.strip())"

    EXEC_RESULT=$(curl -s \
        -X POST \
        -H "Authorization: token ${NODE2_TOKEN}" \
        -H "Content-Type: application/json" \
        "${NODE2_URL}/api/kernels/${KERNEL_ID}/execute" \
        -d "{\"code\": \"${LAUNCH_CODE}\"}" 2>/dev/null || echo "{}")

    echo "  Kernel execute response: ${EXEC_RESULT:0:200}"
fi

echo ""
echo "=================================================="
echo "FILES ON NODE 2:"
echo "  - research_improvements/research_improvements_node2.py"
echo "  - run_research_improvements.ipynb"
echo ""
echo "TO START (if kernel launch didn't work):"
echo "  Open: ${NODE2_URL}/notebooks/run_research_improvements.ipynb?token=${NODE2_TOKEN}"
echo "  Click 'Run' on the first cell"
echo ""
echo "TO MONITOR:"
echo "  Progress: tail -f /home/jovyan/research_improvements/progress.log"
echo ""
echo "EXPECTED OUTPUT:"
echo "  /home/jovyan/research_improvements/output/dynamic_cn_scale_30fps.mp4"
echo "  /home/jovyan/research_improvements/output/dynamic_cn_scale_16fps.mp4"
echo "  /home/jovyan/research_improvements/output/canopy_768px_30fps.mp4"
echo "  /home/jovyan/research_improvements/output/loop_test_30fps.mp4"
echo "  /home/jovyan/research_improvements/output/loop_test_3x_30fps.mp4"
echo "  /home/jovyan/research_improvements/output/cn_scale_curve.csv"
echo "=================================================="
