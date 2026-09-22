#!/usr/bin/env python3
"""Publish rendered episodes to a public Cloudflare R2 bucket and write the app feed.

Reads the bundled Episodes payloads, rewrites each story's audioURL to the bucket's
public URL, writes feed.json, and uploads the audio plus the feed with R2's S3-compatible
API. The app's Settings feed field then points at ``<public-base>/<prefix>/feed.json``.

Env:
  R2_ENDPOINT          https://<account>.r2.cloudflarestorage.com
  R2_BUCKET            bucket name
  R2_ACCESS_KEY_ID     R2 API token access key
  R2_SECRET_ACCESS_KEY R2 API token secret
  R2_PUBLIC_BASE       public origin for the bucket (r2.dev or a custom domain)
  R2_PREFIX            optional key prefix (default "v1")

    python3 tools/publish_feed.py --episodes ios/Zwicky/Episodes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_feed(episodes: list, public_base: str, prefix: str) -> list:
    """Story payloads with absolute audio URLs, newest published first."""
    base = public_base.rstrip("/") + "/" + prefix.strip("/")
    feed = []
    for payload in episodes:
        story = dict(payload["story"])
        name = Path(payload["_file"]).stem
        story["audioURL"] = f"{base}/audio/{name}.m4a"
        feed.append(story)
    return sorted(feed, key=lambda s: s.get("published", ""), reverse=True)


def load_episodes(directory: Path) -> list:
    episodes = []
    for path in sorted(directory.glob("*.json")):
        if path.stem == "index":
            continue
        episodes.append({**json.loads(path.read_text()), "_file": str(path)})
    return episodes


def upload(feed: list, directory: Path, prefix: str) -> dict:
    import boto3  # imported lazily so local runs without R2 can still build the feed

    endpoint = os.environ["R2_ENDPOINT"]
    bucket = os.environ["R2_BUCKET"]
    client = boto3.client("s3", endpoint_url=endpoint, region_name="auto",
                          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    key = prefix.strip("/")
    for episode in load_episodes(directory):
        name = Path(episode["_file"]).stem
        client.upload_file(str(directory / f"{name}.m4a"), bucket, f"{key}/audio/{name}.m4a",
                           ExtraArgs={"ContentType": "audio/mp4", "CacheControl": "public, max-age=86400"})
    body = json.dumps(feed, ensure_ascii=False).encode()
    client.put_object(Bucket=bucket, Key=f"{key}/feed.json", Body=body,
                      ContentType="application/json", CacheControl="no-cache")
    return {"feed_key": f"{key}/feed.json", "audio": len(feed), "bytes": len(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", default=str(ROOT / "ios/Zwicky/Episodes"))
    parser.add_argument("--out", default="", help="also write feed.json here for inspection")
    parser.add_argument("--dry-run", action="store_true", help="build the feed, do not upload")
    args = parser.parse_args()

    directory = Path(args.episodes)
    prefix = os.environ.get("R2_PREFIX", "v1")
    public_base = os.environ.get("R2_PUBLIC_BASE", "https://example.invalid")
    feed = build_feed(load_episodes(directory), public_base, prefix)
    if args.out:
        Path(args.out).write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n")
    print(f"feed has {len(feed)} episodes; base {public_base.rstrip('/')}/{prefix}")
    if args.dry_run:
        for story in feed[:3]:
            print("  ", story["hostID"], "->", story["audioURL"])
        return
    print(json.dumps(upload(feed, directory, prefix), indent=2))


if __name__ == "__main__":
    main()
