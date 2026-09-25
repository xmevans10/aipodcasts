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
gh run list --workflow full-run.yml --status completed --limit 100 \
  --json databaseId,conclusion > "$out_root/completed-runs.json"
jq --argjson baseline "$baseline" -r \
  '[.[] | select(.conclusion == "success" and .databaseId >= $baseline)] | .[].databaseId' \
  "$out_root/completed-runs.json" | sort -n > "$out_root/run-ids.txt"
if [ ! -s "$out_root/run-ids.txt" ]; then
  echo "No successful full-run batches after baseline $baseline" >&2
  exit 1
fi
while IFS= read -r run_id; do
  if ! gh run download "$run_id" --name full-run-transcripts \
      --dir "$out_root/batches/$run_id"; then
    rm -rf "$out_root/batches/$run_id"
    echo "Skipping unavailable artifact from run $run_id"
  fi
done < "$out_root/run-ids.txt"

export LILT_REVIEWER=jev
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
