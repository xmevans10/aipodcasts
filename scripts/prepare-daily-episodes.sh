#!/usr/bin/env bash
set -euo pipefail

# Shared by the overnight workflow and the morning publisher's fallback path.
release_date=${1:?Pass the Eastern publication date}
out_root=${2:-.}
mkdir -p "$out_root/batches"
printf '%s\n' "$release_date" > "$out_root/release-date.txt"

python3 -m pip install boto3
python3 tools/clear_app_feed.py --baseline-out "$out_root/release-baseline.json"
baseline=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["minimum_run_id"])' \
  "$out_root/release-baseline.json")
# Match the detailed audience reviewer used by full-run; scientific verification
# remains Jev and is checked independently in every transcript.
export LILT_REVIEWER=openai
python3 tools/download_reviewed_batches.py --out "$out_root/batches" --baseline "$baseline"
python3 tools/daily_release.py --batches "$out_root/batches" --inventory
python3 tools/daily_release.py --batches "$out_root/batches" \
  --out "$out_root/daily-transcripts" --date "$release_date"
find "$out_root/daily-transcripts" -maxdepth 1 -name '*.json' | wc -l | tr -d ' ' \
  > "$out_root/release-count.txt"
count=$(cat "$out_root/release-count.txt")
if [ "$count" -gt 0 ]; then
  sudo apt-get update
  sudo apt-get install -y espeak-ng ffmpeg
  python3 -m pip install numpy 'google-cloud-texttospeech>=2.31.0'
  python3 tools/tts/bundle_shows.py \
    --transcripts "$out_root/daily-transcripts" --out "$out_root/daily-episodes" \
    --date "$release_date" --tts-provider google-cloud
  python3 tools/tts/estimate_cost.py --episodes "$out_root/daily-episodes" \
    --out "$out_root/cost-estimate.json"
fi
