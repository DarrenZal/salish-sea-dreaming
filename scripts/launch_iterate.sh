#!/bin/bash
# Launch iterate_node1.py with nohup on TELUS Node 1
# Creates output dirs, logs to /home/jovyan/iterate/progress.log

set -e
cd /home/jovyan/iterate

# Create output directories
mkdir -p /home/jovyan/iterate/output
mkdir -p /home/jovyan/iterate/frames
mkdir -p /home/jovyan/iterate/models

echo "$(date) — Starting iteration pipeline..." | tee -a progress.log

# Kill any existing iterate process
pkill -f "iterate_node1.py" 2>/dev/null || true
sleep 2

# Launch with nohup
nohup python3 /home/jovyan/iterate/iterate_node1.py > /home/jovyan/iterate/stdout.log 2>&1 &
PID=$!
echo "$(date) — Launched iterate_node1.py as PID $PID" | tee -a progress.log
echo $PID > /home/jovyan/iterate/pid.txt

echo ""
echo "Monitor with:"
echo "  tail -f /home/jovyan/iterate/progress.log"
echo "  tail -f /home/jovyan/iterate/stdout.log"
echo ""
echo "Check output:"
echo "  ls -la /home/jovyan/iterate/output/"
