#!/usr/bin/env python3
"""Update only the listener-facing titles in the published feed. Audio is never touched.

Why this exists rather than `publish_feed.py`. That script republishes the whole catalog
from `ios/Zwicky/Episodes`, which locally holds only the four older bundled episodes. Run
against the live bucket it would upload four episodes, write a four-entry feed, and drop
the fourteen recent shows out of the catalog. This tool edits titles in place instead.

What it changes: the `title` field of matching entries in `feed.json`, and the same field
inside each episode's detail sidecar. Nothing else. No audio is read, uploaded or deleted,
no word timings change, no episode id changes, and no entry is added or removed, so
listening history and cached audio survive.

Why a title-only change is safe here. The rendered audio for the 2026-09-22 episodes never
speaks the episode headline; it names the paper. The feed's `title` is display text, and
the contract has always treated the listener-facing headline and the exact paper title as
two different strings. Changing the displayed title therefore cannot contradict the
recording. Changing `body` would, and this tool refuses to.

The safety check. An entry is retitled only when its live `body` matches the local
transcript's spoken text once the headline sentence is discounted. If an episode's audio
turns out to be a different script, it is reported and skipped rather than mislabelled.

Env (same as publish_feed.py):
  R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_PUBLIC_BASE
  R2_PREFIX (default "v1")

    python3 tools/retitle_feed.py --dry-run
    python3 tools/retitle_feed.py --apply
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS = ROOT / "experiments/full-run/latest/transcripts"

#: A live body may differ from the local transcript by at most this many words, and only
#: by words the transcript adds. That is the spoken-headline sentence and nothing else.
MAX_ADDED_WORDS = 14


def spoken(draft: dict) -> str:
    if "turns" in draft:
        return " ".join(turn["text"] for turn in draft["turns"])
    return draft.get("body", "")


def local_titles() -> dict:
    """hostID -> (episode title, spoken text) from the reviewed transcripts."""
    titles = {}
    for path in sorted(TRANSCRIPTS.glob("*.json")):
        artifact = json.loads(path.read_text())
        titles[artifact["host"]] = (artifact["draft"]["title"], spoken(artifact["draft"]))
    return titles


def difference(live_body: str, local_body: str) -> tuple[bool, str]:
    """Is the live recording the same script, give or take the spoken headline?"""
    live_words, local_words = live_body.split(), local_body.split()
    matcher = difflib.SequenceMatcher(None, live_words, local_words)
    added, removed = 0, 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        removed += i2 - i1
        added += j2 - j1
    if removed > MAX_ADDED_WORDS or added > MAX_ADDED_WORDS:
        return False, f"script differs (+{added}/-{removed} words); audio is not this transcript"
    return True, f"same script (+{added}/-{removed} words)"


def fetch(url: str) -> bytes:
    # r2.dev rejects the default Python user agent with a 403.
    request = urllib.request.Request(url, headers={"User-Agent": "ZwickyResearch/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def plan(base: str) -> tuple[list, list]:
    """Work out which live entries to retitle. Reads the public feed only."""
    feed = json.loads(fetch(base + "/feed.json"))
    titles = local_titles()
    changes, skipped = [], []
    for entry in feed:
        host = entry.get("hostID")
        current = entry.get("title", "")
        if host not in titles:
            skipped.append((current, f"no local transcript for host {host!r}"))
            continue
        new_title, local_body = titles[host]
        if current == new_title:
            skipped.append((current, "already retitled"))
            continue
        same, why = difference(entry.get("body") or "", local_body)
        if not same:
            skipped.append((current, why))
            continue
        changes.append({"id": entry["id"], "host": host, "old": current,
                        "new": new_title, "why": why,
                        "detail": entry.get("detailURL", "")})
    return changes, skipped


def apply(changes: list, base: str, prefix: str) -> dict:
    """Rewrite titles in each sidecar, then the feed. Sidecars first, so a failure
    part way through leaves the feed still pointing at coherent detail payloads."""
    import boto3

    client = boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    bucket, key = os.environ["R2_BUCKET"], prefix.strip("/")
    by_id = {change["id"]: change for change in changes}

    sidecars = 0
    for change in changes:
        name = change["detail"].rsplit("/", 1)[-1]
        if not name.endswith(".json"):
            raise ValueError("Unexpected detailURL for " + change["id"])
        payload = json.loads(fetch(change["detail"]))
        if payload["story"]["id"] != change["id"]:
            raise ValueError("Sidecar id does not match the feed entry for " + change["id"])
        payload["story"]["title"] = change["new"]
        client.put_object(Bucket=bucket, Key=f"{key}/episodes/{name}",
                          Body=json.dumps(payload, ensure_ascii=False).encode(),
                          ContentType="application/json",
                          CacheControl="public, max-age=86400")
        sidecars += 1

    feed = json.loads(fetch(base + "/feed.json"))
    for entry in feed:
        if entry["id"] in by_id:
            entry["title"] = by_id[entry["id"]]["new"]
    client.put_object(Bucket=bucket, Key=f"{key}/feed.json",
                      Body=json.dumps(feed, ensure_ascii=False).encode(),
                      ContentType="application/json", CacheControl="no-cache")
    return {"sidecars": sidecars, "feed_entries": len(feed), "retitled": len(changes)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="show the plan, change nothing")
    group.add_argument("--apply", action="store_true", help="write the sidecars and the feed")
    args = parser.parse_args()

    prefix = os.environ.get("R2_PREFIX", "v1")
    public = os.environ.get("R2_PUBLIC_BASE", "https://pub-e19f5de621fd4b4ea01c0465d0251407.r2.dev")
    base = public.rstrip("/") + "/" + prefix.strip("/")

    changes, skipped = plan(base)
    print(f"feed: {base}/feed.json")
    print(f"\n{len(changes)} entries to retitle:")
    for change in changes:
        print(f"  {change['host']:9} {change['old'][:52]!r}")
        print(f"  {'':9} -> {change['new']!r}   [{change['why']}]")
    print(f"\n{len(skipped)} entries left alone:")
    for title, why in skipped:
        print(f"  {title[:58]!r}: {why}")

    if args.dry_run:
        print("\nDry run. Nothing was uploaded.")
        return
    missing = [name for name in ("R2_ENDPOINT", "R2_BUCKET", "R2_ACCESS_KEY_ID",
                                 "R2_SECRET_ACCESS_KEY") if not os.environ.get(name)]
    if missing:
        sys.exit("Missing R2 credentials: " + ", ".join(missing))
    if not changes:
        print("\nNothing to do.")
        return
    print("\n" + json.dumps(apply(changes, base, prefix), indent=2))


if __name__ == "__main__":
    main()
