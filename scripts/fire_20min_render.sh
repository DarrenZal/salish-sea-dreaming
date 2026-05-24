#!/usr/bin/env bash
# fire_20min_render.sh — kick off the 20-min Autolume render on the 3090
# once ssh is back. Variant: both baseline + wild_psi120 (Pravin 2026-05-23).
#
# Prerequisites: 3090 reachable via windows-desktop-remote; /tmp/ssd-20min-stage/
# variants_both.json exists locally; SSD-Autolume-Sweep task exists on 3090.
#
# Idempotent: rerun safely. Creates a fresh timestamped output dir each run.

set -euo pipefail

STAMP=$(date +%Y%m%d_%H%M)
OUT_DIR_REMOTE="C:\\Users\\user\\autolume_20min\\${STAMP}"
VARIANTS_LOCAL="/tmp/ssd-20min-stage/variants_both.json"
VARIANTS_REMOTE="C:/Users/user/variants_20min.json"
PKL="C:\\Users\\user\\Documents\\models\\network-snapshot-000120.pkl"
PRESET="C:\\Users\\user\\Documents\\presets\\0"
AUTOLUME="C:\\Users\\user\\autolume"
SWEEP_PY="C:\\Users\\user\\autolume_sweep.py"

echo "=== 1. Verify 3090 reachable ==="
ssh -o ConnectTimeout=8 windows-desktop-remote "echo OK_PRE_FIRE_$(date +%H:%M)" || {
  echo "FATAL: 3090 not reachable, aborting"
  exit 2
}

echo ""
echo "=== 2. scp variants_both.json to 3090 ==="
scp -O "$VARIANTS_LOCAL" "windows-desktop-remote:${VARIANTS_REMOTE}"

echo ""
echo "=== 3. Verify PKL + preset + sweep script + autolume dir exist on 3090 ==="
ssh windows-desktop-remote "if exist \"${PKL}\" (echo PKL_OK) else (echo PKL_MISSING)"
ssh windows-desktop-remote "if exist \"${PRESET}\" (echo PRESET_OK) else (echo PRESET_MISSING)"
ssh windows-desktop-remote "if exist \"${SWEEP_PY}\" (echo SWEEP_OK) else (echo SWEEP_MISSING)"
ssh windows-desktop-remote "if exist \"${AUTOLUME}\" (echo AUTOLUME_OK) else (echo AUTOLUME_MISSING)"

echo ""
echo "=== 4. Fire render via detached cmd (survives ssh disconnect) ==="
# Build a one-shot batch file on the 3090 that invokes the python sweep,
# then launch it detached via 'start /b cmd /c'.
#
# Using a batch file avoids fragile cmd escaping over ssh and gives us a
# stable log file path we can tail.
FIRE_BAT="C:\\Users\\user\\fire_20min_${STAMP}.bat"
LOG_REMOTE="C:\\Users\\user\\autolume_20min_${STAMP}.log"

ssh windows-desktop-remote "(echo @echo off & echo cd /d ${AUTOLUME} & echo python ${SWEEP_PY} --pkl ${PKL} --preset ${PRESET} --output-dir ${OUT_DIR_REMOTE} --record-seconds 1200 --settle-seconds 5 --variants-file C:\\Users\\user\\variants_20min.json --autolume-dir ${AUTOLUME} ^> ${LOG_REMOTE} 2^>^&1) > ${FIRE_BAT}"

ssh windows-desktop-remote "type ${FIRE_BAT}"

echo ""
echo "Launching detached..."
ssh windows-desktop-remote "schtasks /create /tn SSD-Fire-20min-${STAMP} /tr ${FIRE_BAT} /sc onstart /ru user /rl HIGHEST /f"
ssh windows-desktop-remote "schtasks /run /tn SSD-Fire-20min-${STAMP}"

echo ""
echo "=== 5. Poll status ==="
echo "Render running. Output: ${OUT_DIR_REMOTE}"
echo "Log: ${LOG_REMOTE}"
echo ""
echo "Tail log with:"
echo "  ssh windows-desktop-remote \"type ${LOG_REMOTE}\""
echo ""
echo "When complete (~40 min), pull MP4s:"
echo "  scp -O windows-desktop-remote:${OUT_DIR_REMOTE}/*.mp4 /tmp/autolume_20min_${STAMP}/"
echo ""
echo "Cleanup the throwaway task afterward:"
echo "  ssh windows-desktop-remote \"schtasks /delete /tn SSD-Fire-20min-${STAMP} /f\""
