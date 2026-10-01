#!/usr/bin/env python3
"""Select exactly the remaining daily slots from reviewed Actions batches.

The batches directory contains downloaded `full-run-transcripts` artifacts, one
subdirectory per successful Actions run. Selection uses the R2 feed as the publication
ledger, so reruns cannot publish the same paper again under a new date.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "full-run"))
from check_batch import check_batch  # noqa: E402
from run_all_shows import slug  # noqa: E402
from publish_feed import load_existing_feed, r2_client  # noqa: E402
from dialogue import turns_body  # noqa: E402


def doi_from_url(url: str) -> str:
    match = re.search(r"10\.\d{4,9}/[^\s?#]+", url or "", re.I)
    return match.group(0).rstrip("/.").casefold() if match else ""


def app_feed_url() -> str:
    swift = (ROOT / "ios" / "Zwicky" / "Models.swift").read_text()
    match = re.search(r'static let defaultFeedURL\s*=\s*"(https://[^"]+)"', swift)
    if not match:
        raise ValueError("App default feed URL could not be found")
    return match.group(1)


def published_versions(feed: list) -> dict[tuple[str, str], str]:
    versions = {}
    for story in sorted(feed, key=lambda s: s.get("published", ""), reverse=True):
        host = story.get("hostID", "")
        for source in story.get("sources", []):
            doi = doi_from_url(source.get("url", ""))
            if host and doi:
                versions.setdefault((host, doi), story.get("body", "").strip())
    return versions


def available(batches: Path, feed: list) -> list[tuple[Path, dict]]:
    if not isinstance(feed, list):
        raise ValueError("Published feed is malformed")
    published = published_versions(feed)
    withdrawn = {(story.get('hostID'), doi_from_url(source.get('url', '')))
                 for story in feed if story.get('withdrawalNotice') is not None
                 for source in story.get('sources', [])}
    order = []
    candidates = {}
    for directory in sorted(batches.iterdir(),
                            key=lambda p: int(p.name) if p.name.isdigit() else -1,
                            reverse=True):
        if not directory.is_dir():
            continue
        try:
            # A batch may be incomplete, but every script we consider must have
            # its own current factual and audience approvals.
            check_batch(directory, require_all=False)
        except (FileNotFoundError, KeyError, ValueError, TypeError) as error:
            print(f"Skipping invalid batch {directory.name}: {error}", file=sys.stderr)
            continue
        manifest = json.loads((directory / "manifest.json").read_text())
        for entry in manifest["shows"]:
            if entry.get("status") != "approved":
                continue
            key = (entry["host"], doi_from_url(entry.get("doi", "")))
            if not key[1]:
                path = directory / "transcripts" / (slug(entry["show"]) + ".json")
                key = (entry["host"], doi_from_url(json.loads(path.read_text()).get("doi", "")))
            if not key[1]:
                raise ValueError(f"{entry['show']}: approved artifact has no DOI")
            path = directory / "transcripts" / (slug(entry["show"]) + ".json")
            draft = json.loads(path.read_text())["draft"]
            body = turns_body(draft) if "turns" in draft else draft["body"].strip()
            if key not in candidates:
                order.append(key)
                # Batches are traversed newest first, so the first approved
                # revision for a paper is the latest one.
                candidates[key] = (path, entry, body)
    return [(candidates[key][0], candidates[key][1]) for key in order
            if key not in withdrawn and key not in published]


def select(batches: Path, feed: list, day: str, *, limit: int = 2) -> list[tuple[Path, dict]]:
    if not isinstance(feed, list):
        raise ValueError("Published feed is malformed")
    published_today = sum(story.get("published") == day and story.get("withdrawalNotice") is None for story in feed)
    if published_today > limit:
        raise ValueError(f"Feed already has {published_today} episodes on {day}")
    slots = limit - published_today
    if slots == 0:
        return []
    coverage = {}
    for story in feed:
        host = story.get('hostID', '')
        coverage[host] = coverage.get(host, 0) + 1
    # Give empty/underfilled shows their first real episode before topping up the
    # earliest show in manifest order again. Stable ties keep newest-batch priority.
    candidates = sorted(available(batches, feed),
                        key=lambda item: coverage.get(item[1]['host'], 0))
    picked = candidates[:slots]
    if len(picked) == slots:
        return picked
    raise ValueError(f"Only {len(picked)} unpublished approved episodes available; need {slots} for {day}")


def stage(picked: list[tuple[Path, dict]], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError("Daily transcript directory must start empty")
    for path, entry in picked:
        stem = slug(entry["show"])
        shutil.copyfile(path, directory / (stem + ".json"))
        shutil.copyfile(path.with_suffix(".md"), directory / (stem + ".md"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--inventory", action="store_true", help="report usable unpublished inventory without rendering")
    parser.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--feed-file", type=Path, help="offline test input instead of R2")
    args = parser.parse_args()
    if args.feed_file:
        feed = json.loads(args.feed_file.read_text())
    else:
        target = os.environ["R2_PUBLIC_BASE"].rstrip("/") + "/" + os.environ.get("R2_PREFIX", "v1").strip("/") + "/feed.json"
        if target != app_feed_url():
            raise ValueError("R2 publication target differs from the app's default feed URL")
        feed = load_existing_feed(r2_client(), os.environ["R2_BUCKET"], os.environ.get("R2_PREFIX", "v1"))
    if args.inventory:
        eligible = available(args.batches, feed)
        shows = {}
        for _, entry in eligible:
            shows[entry["show"]] = shows.get(entry["show"], 0) + 1
        count = len(eligible)
        print(json.dumps({"eligible_episodes": count, "days_at_two_per_day": count / 2,
                          "below_week_buffer": count < 14, "shows": shows}, indent=2))
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
                summary.write(f"### Content inventory\n\n{count} unpublished, strictly reviewed episodes "
                              f"({count / 2:g} days at two/day). "
                              + ("Below the 14-episode buffer target.\n" if count < 14 else "Buffer target met.\n"))
        return
    if not args.out:
        parser.error("--out is required unless --inventory is used")
    picked = select(args.batches, feed, args.date)
    stage(picked, args.out)
    print(f"{len(picked)} episodes queued for {args.date}: " + ", ".join(e["show"] for _, e in picked))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"count={len(picked)}\n")


if __name__ == "__main__":
    main()
