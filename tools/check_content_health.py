#!/usr/bin/env python3
"""Check the public release independently of preparation or storage credentials."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from daily_release import app_feed_url
from publish_feed import is_https_url, verify_staged_assets, validate_readalong


def todays_episodes(feed: list, day: str) -> list:
    if not isinstance(feed, list) or not feed:
        raise ValueError("Public catalog is empty or malformed")
    ids = []
    for story in feed:
        if not isinstance(story, dict) or not isinstance(story.get("id"), str):
            raise ValueError("Public catalog contains an invalid episode")
        ids.append(story["id"])
        if not all(is_https_url(story.get(field, ""))
                   for field in ("audioURL", "detailURL", "shareURL")):
            raise ValueError(f"{story['id']}: invalid public asset URL")
    if len(set(ids)) != len(ids):
        raise ValueError("Public catalog contains duplicate episode IDs")
    today = [story for story in feed if story.get("published") == day]
    if len(today) != 2:
        raise ValueError(f"Expected two episodes for {day}; public catalog has {len(today)}")
    return today


def fetch(url: str):
    return urlopen(Request(url, headers={"User-Agent": "curl/8.0", "Cache-Control": "no-cache"}), timeout=20)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat())
    parser.add_argument("--all-episodes", action="store_true", help="probe the archive as well as today's release")
    args = parser.parse_args()
    with fetch(app_feed_url()) as response:
        feed = json.load(response)
    today = todays_episodes(feed, args.date)
    checked = feed if args.all_episodes else today
    verify_staged_assets(checked)
    for story in checked:
        with fetch(story["detailURL"]) as response:
            sidecar = json.load(response)
        if (sidecar.get("story", {}).get("id") != story["id"]
                or sidecar.get("story", {}).get("body") != story.get("body")
                or sidecar.get("story", {}).get("hostID") != story.get("hostID")
                or not sidecar.get("transcript")):
            raise ValueError(f"{story['id']}: public read-along differs from the feed")
        validate_readalong(sidecar, story["id"])
        request = Request(story["audioURL"], headers={"User-Agent": "curl/8.0", "Range": "bytes=0-31"})
        with urlopen(request, timeout=20) as response:
            header = response.read(32)
            if response.status != 206 or header[4:8] != b"ftyp":
                raise ValueError(f"{story['id']}: public audio is not a ranged M4A stream")
    report = {"date": args.date, "catalog_count": len(feed), "checked_episodes": len(checked), "released_ids": [s["id"] for s in today],
              "public_audio_read_along_and_sharing": "passed"}
    print(json.dumps(report, indent=2))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(f"### Public content health\n\nTwo episodes for {args.date}; "
                          f"audio, read along and sharing passed. Catalog: {len(feed)} episodes.\n")


if __name__ == "__main__":
    main()
