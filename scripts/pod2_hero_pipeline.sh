#!/usr/bin/env bash
# pod2_hero_pipeline.sh — manual orchestrator for pod 2 ESRGAN queue.
#
# 1. Poll H2 retry job for _status.txt = DONE on pod 2
# 2. Download H2_herring_in_kelp_4k.mp4 from job dir
# 3. Fire H1 retry on pod 2
# 4. Poll, download
# 5. Continue H3, H4, H5, H7, H8 (skip H6 which already has 4K)
#
# Run in background with run_in_background:true

set -uo pipefail
POD_URL="https://salishseadreaming-0b50s.paas.ai.telus.com"
TOKEN="3e777ac2d1d6543672fe72f5d3e213f4"
OUT_DIR="/tmp/4k-heroes"
mkdir -p "$OUT_DIR"

# Helper: poll one job to DONE, then download the output mp4
poll_and_download() {
  local job_name="$1"
  local output_filename="$2"
  local local_output="$3"
  local max_attempts="${4:-150}"  # default 12.5 hours at 5-min intervals

  for i in $(seq 1 $max_attempts); do
    STATUS=$(curl -s -m 8 -H "Authorization: token $TOKEN" \
      "$POD_URL/api/contents/upscale-test/jobs/$job_name/_status.txt?content=1" 2>/dev/null | \
      python3 -c "import json,sys
try: print(json.load(sys.stdin).get('content','').strip())
except: print('')" 2>/dev/null)
    PROG=$(curl -s -m 8 -H "Authorization: token $TOKEN" \
      "$POD_URL/api/contents/upscale-test/jobs/$job_name/_progress.txt?content=1" 2>/dev/null | \
      python3 -c "import json,sys
try: print(json.load(sys.stdin).get('content','').strip())
except: print('')" 2>/dev/null)
    if [ "$STATUS" = "DONE" ]; then
      echo "[$(date +%H:%M:%S)] $job_name DONE after $i polls"
      break
    fi
    if [[ "$STATUS" == ERROR* ]]; then
      echo "[$(date +%H:%M:%S)] $job_name ERROR: $STATUS"
      return 1
    fi
    echo "  [$(date +%H:%M:%S)] $job_name attempt $i — status='$STATUS' progress='$PROG'"
    sleep 300
  done

  # Download the output mp4 via Python (base64 decode)
  echo "[$(date +%H:%M:%S)] downloading $output_filename..."
  python3 <<PY
import requests, base64, sys
TOKEN = "$TOKEN"
URL = "$POD_URL"
job = "$job_name"
filename = "$output_filename"
local = "$local_output"
H = {"Authorization": f"token {TOKEN}"}
r = requests.get(f"{URL}/api/contents/upscale-test/jobs/{job}/{filename}",
                 headers=H, params={"format":"base64"}, timeout=180)
if r.status_code != 200:
    print(f"  download fail HTTP {r.status_code}: {r.text[:300]}")
    sys.exit(1)
body = r.json()
if body.get("format") != "base64":
    print(f"  unexpected format {body.get('format')}")
    sys.exit(1)
data = base64.b64decode(body["content"])
with open(local, "wb") as f:
    f.write(data)
print(f"  ✓ saved {local} ({len(data)/1024/1024:.1f} MB)")
PY
}

# Helper: fire ESRGAN job on pod 2 (returns the job name)
fire_pod2_esrgan() {
  local source_path="$1"
  local job_label="$2"
  local output_filename="$3"
  cd /Users/darrenzal/projects/salish-sea-dreaming
  echo "[$(date +%H:%M:%S)] firing $job_label..."
  TELUS_POD_URL="$POD_URL" \
  Jupyter_REST_API="$TOKEN" \
  python3 scripts/telus_upscale.py \
    "$source_path" \
    --model x2plus \
    --canvas 3840x2160 \
    -o "$OUT_DIR/${output_filename}" \
    --job-name "$job_label" \
    > "/tmp/${job_label}_driver.log" 2>&1 &
  # Driver will time out but pod-side job continues; we poll instead
  local DRIVER_PID=$!
  echo "  driver PID=$DRIVER_PID (will time out; pod-side keeps running)"
  echo "$job_label"
}

# ---- STEP 1: poll H2 retry to DONE + download ----
poll_and_download "h2_herring_4k_retry_1821" "H2_herring_in_kelp_4k.mp4" "$OUT_DIR/H2_herring_in_kelp_4k.mp4"

# ---- STEP 2: fire H1 retry on pod 2 ----
H1_JOB="h1_salmon_retry_$(date +%H%M)"
fire_pod2_esrgan "/Users/darrenzal/projects/salish-sea-dreaming/media/hero-subclips/H1_salmon_school.mp4" "$H1_JOB" "H1_salmon_school_4k_esrgan.mp4"
sleep 120  # let upload + init phase complete
poll_and_download "$H1_JOB" "H1_salmon_school_4k_esrgan.mp4" "$OUT_DIR/H1_salmon_school_4k_esrgan.mp4"

# ---- STEP 3-7: fire H3, H4, H5, H7, H8 in queue ----
for HERO_INFO in "H3_kelp_cathedral:H3_kelp_cathedral_4k_esrgan.mp4" \
                 "H4_dense_school:H4_dense_school_4k_esrgan.mp4" \
                 "H5_reef_garden:H5_reef_garden_4k_esrgan.mp4" \
                 "H7_spawn_feast:H7_spawn_feast_4k_esrgan.mp4" \
                 "H8_milky_water:H8_milky_water_4k_esrgan.mp4"; do
  HERO_NAME="${HERO_INFO%%:*}"
  HERO_OUT="${HERO_INFO##*:}"
  HERO_JOB="${HERO_NAME,,}_$(date +%H%M)"
  fire_pod2_esrgan "/Users/darrenzal/projects/salish-sea-dreaming/media/hero-subclips/${HERO_NAME}.mp4" "$HERO_JOB" "$HERO_OUT"
  sleep 120
  poll_and_download "$HERO_JOB" "$HERO_OUT" "$OUT_DIR/${HERO_OUT}"
done

echo "[$(date +%H:%M:%S)] All ESRGAN jobs complete"
ls -lh "$OUT_DIR/"
