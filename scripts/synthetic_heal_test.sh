#!/usr/bin/env bash
# synthetic_heal_test.sh -- kill each watched component in sequence on the
# 3090, time its auto-recovery, and report PASS/FAIL. Designed for the
# Thursday "full crash-test" validation before the Friday board visit.
#
# Run from the Mac (has both windows-desktop-remote and windows-desktop-wg
# SSH aliases). Uses windows-desktop-wg by default since it's the independent
# path -- if a test somehow kills the primary SSH tunnel, the WG path keeps
# us observing.
#
# Writes a report to /tmp/synthetic_heal_report_<timestamp>.md and echoes
# pass/fail for each phase live.
#
# Usage:
#   scripts/synthetic_heal_test.sh            # run all phases
#   scripts/synthetic_heal_test.sh arena      # run just one phase
#   scripts/synthetic_heal_test.sh --dry-run  # print what would be tested
#
# CAUTION: this WILL cause brief visual disruptions on the wall (Arena
# restart takes ~60-90s; TD restart longer). Run only when gallery is
# closed or empty.

set -u
SSH_HOST="${SSH_HOST:-windows-desktop-wg}"
REPORT="/tmp/synthetic_heal_report_$(date +%Y%m%d-%H%M%S).md"
DRY=false
PHASE_FILTER="${1:-}"

if [[ "$PHASE_FILTER" == "--dry-run" ]]; then
    DRY=true
    PHASE_FILTER=""
fi

pssh() { ssh -o ConnectTimeout=10 "$SSH_HOST" "$@"; }
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$REPORT"; }

result_pass=0
result_fail=0

run_phase() {
    local name="$1"
    local kill_cmd="$2"
    local check_cmd="$3"
    local max_wait="$4"    # seconds
    local notes="$5"

    if [[ -n "$PHASE_FILTER" && "$PHASE_FILTER" != "$name" ]]; then
        return 0
    fi

    log ""
    log "=== PHASE: $name ==="
    log "notes: $notes"
    log "kill_cmd: $kill_cmd"
    log "check_cmd: $check_cmd"
    log "max_wait: ${max_wait}s"

    if $DRY; then
        log "(dry-run: skipping actual kill)"
        return 0
    fi

    # Baseline state
    local baseline
    baseline=$(pssh "powershell -Command \"$check_cmd\"" 2>&1 | head -5)
    log "baseline: $baseline"

    # Kill
    local t_kill
    t_kill=$(date +%s)
    log "KILL at $(date '+%H:%M:%S')"
    pssh "powershell -Command \"$kill_cmd\"" 2>&1 | head -3 | while read -r line; do log "  $line"; done

    # Poll for recovery
    local t_now elapsed recovered
    recovered=false
    while (( ($(date +%s) - t_kill) < max_wait )); do
        sleep 10
        t_now=$(date +%s)
        elapsed=$((t_now - t_kill))
        local state
        state=$(pssh "powershell -Command \"$check_cmd\"" 2>&1 | head -3)
        log "  T+${elapsed}s: $state"
        # Component-specific recovery detection: caller embeds the check in check_cmd
        # returning "true"/"false" in its output.
        if echo "$state" | grep -qE "RECOVERED|True|running|Running"; then
            recovered=true
            break
        fi
    done

    if $recovered; then
        log "PASS: $name recovered at T+${elapsed}s"
        result_pass=$((result_pass + 1))
    else
        log "FAIL: $name did not recover within ${max_wait}s"
        result_fail=$((result_fail + 1))
    fi
}

log "# Synthetic Heal Test Report"
log "# Run: $(date)"
log "# SSH target: $SSH_HOST"
log ""

# PHASE 1: Arena (Resolume)
run_phase "arena" \
    'Stop-Process -Name Arena -Force' \
    'if (Get-Process Arena -ErrorAction SilentlyContinue) { "RECOVERED PID=$((Get-Process Arena).Id)" } else { "still dead" }' \
    180 \
    "Kill Arena. Watchdog v2 should detect within 60s and restart via SSD-Resolume task. Expected recovery ~60-120s."

# PHASE 2: TouchDesigner
run_phase "touchdesigner" \
    'Stop-Process -Name TouchDesigner -Force' \
    'if (Get-Process TouchDesigner -ErrorAction SilentlyContinue) { "RECOVERED PID=$((Get-Process TouchDesigner).Id)" } else { "still dead" }' \
    240 \
    "Kill TD. Watchdog v2 (deployed Apr 20 evening) should detect and restart via SSD-TouchDesigner. Expected recovery ~60-180s."

# PHASE 3: Autolume
run_phase "autolume" \
    'Stop-Process -Name Autolume -Force' \
    'if (Get-Process Autolume -ErrorAction SilentlyContinue) { "RECOVERED PID=$((Get-Process Autolume | Select -First 1).Id)" } else { "still dead" }' \
    360 \
    "Kill Autolume. Watchdog v2 should detect and restart via SSD-Autolume. Expected recovery 120-300s (GPU + pkl load is slow)."

# PHASE 4: SSH tunnel
run_phase "ssh_tunnel" \
    'Get-CimInstance Win32_Process | Where-Object { ($_.CommandLine -like "*ssd_ssh_tunnel*" -and $_.Name -eq "powershell.exe") -or ($_.Name -eq "ssh.exe" -and $_.CommandLine -like "*2222:localhost:22*") } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }' \
    'if (Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "ssh.exe" -and $_.CommandLine -like "*2222:localhost:22*" }) { "RECOVERED tunnel" } else { "still dead" }' \
    180 \
    "Kill both tunnel parent ps + ssh child. tunnel_watchdog (60s check interval, restart after 2 fails) should recover in ~120-150s."

log ""
log "=== SUMMARY ==="
log "PASS: $result_pass"
log "FAIL: $result_fail"
log ""
log "Report saved to: $REPORT"

exit $result_fail
