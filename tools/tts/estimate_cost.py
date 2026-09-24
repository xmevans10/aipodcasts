#!/usr/bin/env python3
"""Estimate Gemini 2.5 Flash TTS list-price audio cost for a rendered batch.

Google bills 25 audio tokens per generated second at $10/M audio tokens.
The sidecar duration includes short non-Google stingers and gaps, so this is an
upper bound for one successful synthesis pass, not a Cloud Billing charge.
Retries and text input charges are not included; use billing export for actuals.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

AUDIO_TOKENS_PER_SECOND = 25
USD_PER_MILLION_AUDIO_TOKENS = 10


def estimate(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("*.json")):
        if path.stem == "index":
            continue
        payload = json.loads(path.read_text())
        seconds = float(payload["duration"])
        if seconds <= 0 or not (directory / f"{path.stem}.m4a").is_file():
            raise ValueError(f"Missing playable audio for {path.stem}")
        story = payload["story"]
        rows.append({
            "id": story["id"], "title": story["title"], "hostID": story["hostID"],
            "durationSeconds": seconds,
            "audioCostUpperBoundUSD": round(
                seconds * AUDIO_TOKENS_PER_SECOND * USD_PER_MILLION_AUDIO_TOKENS / 1_000_000, 6),
        })
    if not rows:
        raise ValueError("No rendered episodes to estimate")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = estimate(args.episodes)
    result = {"model": "gemini-2.5-flash-tts", "currency": "USD",
              "method": "audio duration upper bound at public list price; excludes input and retries",
              "episodes": rows}
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    for row in rows:
        print(f"{row['title']}: ${row['audioCostUpperBoundUSD']:.4f} audio upper bound")


if __name__ == "__main__":
    main()
