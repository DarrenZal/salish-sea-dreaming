#!/usr/bin/env bash
# Integration test for the event-scoped KG pipeline.
#
# Tests (passive — does not modify the 3090, only observes):
#   1. Submit a prompt via the primary URL with consent toggles ON
#   2. Verify the response includes prompt_id
#   3. Wait for v5's queue advance + relay polling + KG endpoint merge
#   4. Confirm the offering appears in /graph/event/impact-2026
#   5. Submit a prompt with consent OFF
#   6. Confirm offering_count does NOT increase (consent gate)
#   7. Optional: pull TD snapshot if relay forwarded it
#
# Requires: curl, python3, jq optional. SSH access to poly is NOT required —
# everything tests via the public URL.
#
# Usage:
#   bash scripts/integration_test_kg.sh           # quick test
#   bash scripts/integration_test_kg.sh --verbose
#
# Exit codes:
#   0 = all checks passed
#   1 = consent ON submission failed to appear
#   2 = consent OFF submission appeared (consent gate broken)
#   3 = submit endpoint returned non-2xx
#   4 = environment problem (curl/python3 missing)

set -u
PRIMARY="${PRIMARY_URL:-https://salishseadreaming.art}"
EVENT="${EVENT:-impact-2026}"
WAIT_SECONDS="${WAIT_SECONDS:-6}"
VERBOSE=0
if [[ "${1:-}" == "--verbose" ]]; then VERBOSE=1; fi

log()   { echo "[$(date -u +%H:%M:%S)] $*"; }
vlog()  { (( VERBOSE )) && echo "  $*"; return 0; }

# fetch_with_retry URL [max_attempts=3] — GET URL via curl, retry on empty body.
# Returns 0 with body on stdout if OK, 1 if all attempts failed.
fetch_with_retry() {
  local url="$1"
  local attempts="${2:-3}"
  local i body
  for (( i=1; i<=attempts; i++ )); do
    body=$(curl -s -m 8 "$url")
    if [[ -n "$body" && "$body" == "{"* ]]; then
      printf '%s' "$body"
      return 0
    fi
    sleep 2
  done
  return 1
}

command -v curl >/dev/null    || { log "curl missing"; exit 4; }
command -v python3 >/dev/null || { log "python3 missing"; exit 4; }

log "=== Integration test: event-scoped KG ($EVENT) ==="
log "Target: $PRIMARY"

# --- Step 1: submit with consent ON ---
log "1/6 Submitting prompt with consent ON..."
RESP_ON=$(curl -s -m 8 -X POST "$PRIMARY/prompt" \
  -H "Content-Type: application/json" \
  -d '{"source":"typed","text":"integration test KG — consent ON",
       "consent":{"visible_in_installation":true,"included_in_clustering":true,
                  "quotable_by_agent":false,"available_post_show":false}}')
vlog "raw: $RESP_ON"
PID_ON=$(echo "$RESP_ON" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('prompt_id',''))")
if [[ -z "$PID_ON" ]]; then
  log "FAIL: consent-ON submit returned no prompt_id"
  exit 3
fi
log "   prompt_id=$PID_ON"

# --- Step 2: count offerings before our consent-OFF submit ---
log "2/6 Reading baseline offering_count from /graph/event/$EVENT..."
sleep "$WAIT_SECONDS"
BASELINE_BODY=$(fetch_with_retry "$PRIMARY/graph/event/$EVENT") || { log "FAIL: could not fetch /graph/event/$EVENT (3 attempts)"; exit 1; }
BASELINE=$(echo "$BASELINE_BODY" | python3 -c "import json,sys; print(json.load(sys.stdin)['meta']['offering_count'])")
log "   offering_count after consent-ON wait: $BASELINE"

# --- Step 3: verify our consent-ON offering appears ---
log "3/6 Verifying offering:$PID_ON is in the graph..."
GRAPH_BODY=$(fetch_with_retry "$PRIMARY/graph/event/$EVENT") || { log "FAIL: could not fetch /graph/event/$EVENT (3 attempts)"; exit 1; }
HAS=$(echo "$GRAPH_BODY" | python3 -c "
import json,sys
d=json.load(sys.stdin)
target='offering:$PID_ON'
print('yes' if any(n['id']==target for n in d['nodes']) else 'no')")
if [[ "$HAS" != "yes" ]]; then
  log "FAIL: offering:$PID_ON did not appear in /graph/event/$EVENT after ${WAIT_SECONDS}s wait"
  exit 1
fi
log "   ✓ offering:$PID_ON present"

# --- Step 4: submit consent OFF (sleep before to clear rate limit) ---
log "4/6 Waiting 5s to clear rate limit, then submitting prompt with consent OFF..."
sleep 5
RESP_OFF=$(curl -s -m 8 -X POST "$PRIMARY/prompt" \
  -H "Content-Type: application/json" \
  -d '{"source":"typed","text":"integration test KG — consent OFF",
       "consent":{"visible_in_installation":false,"included_in_clustering":true,
                  "quotable_by_agent":false,"available_post_show":false}}')
vlog "raw: $RESP_OFF"
PID_OFF=$(echo "$RESP_OFF" 2>/dev/null | python3 -c "import json,sys
try:
    d = json.loads(sys.stdin.read())
    print(d.get('prompt_id',''))
except Exception:
    print('')" 2>/dev/null)
if [[ -z "$PID_OFF" ]]; then
  log "FAIL: consent-OFF submit returned no prompt_id (rate limit? server error?)"
  log "  response was: $RESP_OFF"
  exit 3
fi
log "   prompt_id=$PID_OFF"

# --- Step 5: verify consent-OFF does NOT appear ---
log "5/6 Verifying offering:$PID_OFF does NOT appear after ${WAIT_SECONDS}s wait..."
sleep "$WAIT_SECONDS"
GRAPH_BODY_OFF=$(fetch_with_retry "$PRIMARY/graph/event/$EVENT") || { log "FAIL: could not fetch /graph/event/$EVENT (3 attempts)"; exit 1; }
HAS_OFF=$(echo "$GRAPH_BODY_OFF" | python3 -c "
import json,sys
d=json.load(sys.stdin)
target='offering:$PID_OFF'
print('yes' if any(n['id']==target for n in d['nodes']) else 'no')")
if [[ "$HAS_OFF" == "yes" ]]; then
  log "FAIL: offering:$PID_OFF appeared in graph despite visible_in_installation=false (consent gate broken!)"
  exit 2
fi
log "   ✓ offering:$PID_OFF correctly hidden"

# --- Step 6: snapshot check (best-effort, may take longer) ---
log "6/6 Checking visitor snapshot for prompt_id=$PID_ON (best-effort, may not be ready yet)..."
SNAP_CODE=$(curl -s -m 8 -o /dev/null -w "%{http_code}" "$PRIMARY/td/snapshot/visitor/$PID_ON.jpg")
if [[ "$SNAP_CODE" == "200" ]]; then
  log "   ✓ snapshot available (HTTP $SNAP_CODE)"
else
  log "   ~ snapshot not ready (HTTP $SNAP_CODE) — non-blocking; relay may need 30s+ before pushing"
fi

log "=== All checks passed ==="
log "Cleanup note: test prompts $PID_ON (visible) and $PID_OFF (hidden) remain in prompts-v5.db"
log "To remove, contact the operator; do NOT delete autonomously."
exit 0
