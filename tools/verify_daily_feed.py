#!/usr/bin/env python3
"""Confirm the app's default public feed exposes today's two releases."""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

from daily_release import app_feed_url, doi_from_url


def verify(feed: list, expected: list, day: str) -> None:
    if not isinstance(feed, list):
        raise ValueError("Public feed is not a JSON list")
    if sum(story.get("published") == day for story in feed) != 2:
        raise ValueError(f"Public feed does not show exactly two episodes for {day}")
    for artifact in expected:
        key = (artifact["host"], artifact["doi"].casefold())
        matching = [s for s in feed if s.get("hostID") == key[0]
                    and s.get("published") == day
                    and any(doi_from_url(source.get("url", "")) == key[1]
                            for source in s.get("sources", []))]
        if len(matching) != 1:
            raise ValueError(f"App feed does not contain today's {artifact['show']} episode")
        story = matching[0]
        if not all(story.get(name, "").startswith("https://")
                   for name in ("audioURL", "detailURL")):
            raise ValueError(f"{artifact['show']}: public audio or detail URL is missing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcripts", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    expected = [json.loads(p.read_text()) for p in args.transcripts.glob("*.json")]
    if not expected:
        raise ValueError("No daily transcripts to verify")
    url = app_feed_url()
    last_error = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={"Cache-Control": "no-cache",
                                                           "User-Agent": "curl/8.0"})
            with urllib.request.urlopen(request, timeout=20) as response:
                feed = json.load(response)
            verify(feed, expected, args.date)
            for artifact in expected:
                story = next(s for s in feed if s.get("hostID") == artifact["host"]
                             and s.get("published") == args.date
                             and any(doi_from_url(source.get("url", "")) == artifact["doi"].casefold()
                                     for source in s.get("sources", [])))
                for name in ("audioURL", "detailURL"):
                    with urllib.request.urlopen(urllib.request.Request(
                            story[name], method="HEAD", headers={"User-Agent": "curl/8.0"}),
                                                timeout=20) as response:
                        if response.status != 200:
                            raise ValueError(f"{name} returned HTTP {response.status}")
            print(f"App feed verified: two episodes published on {args.date}")
            return
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < 3:
                time.sleep(5)
    raise RuntimeError(f"Public app feed verification failed: {last_error}")


if __name__ == "__main__":
    main()
