#!/usr/bin/env python3
"""Publish rendered episodes to a public Cloudflare R2 bucket and write the app feed.

Each episode has an opaque id (its file name, from bundle_shows.episode_key). The feed
lists stories with an absolute ``audioURL`` and a ``detailURL`` sidecar that carries the
word-timed transcript and the cover envelope, so read-along works for streamed episodes.
The audio is keyed by the same id, so only the matching id streams.

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


def story_payload(payload: dict, name: str, base: str) -> dict:
    """The feed story: audio and detail sidecar at absolute public URLs."""
    story = dict(payload["story"])
    story["audioURL"] = f"{base}/audio/{name}.m4a"
    story["detailURL"] = f"{base}/episodes/{name}.json"
    return story


def build_feed(episodes: list, public_base: str, prefix: str) -> list:
    """Story payloads with absolute URLs, newest published first."""
    base = public_base.rstrip("/") + "/" + prefix.strip("/")
    feed = [story_payload(payload, Path(payload["_file"]).stem, base) for payload in episodes]
    return sorted(feed, key=lambda s: s.get("published", ""), reverse=True)


def load_episodes(directory: Path) -> list:
    episodes = []
    for path in sorted(directory.glob("*.json")):
        if path.stem == "index":
            continue
        episodes.append({**json.loads(path.read_text()), "_file": str(path)})
    return episodes


def upload(episodes: list, feed: list, directory: Path, prefix: str) -> dict:
    import boto3  # imported lazily so local runs without R2 can still build the feed

    endpoint = os.environ["R2_ENDPOINT"]
    bucket = os.environ["R2_BUCKET"]
    client = boto3.client("s3", endpoint_url=endpoint, region_name="auto",
                          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])
    key = prefix.strip("/")
    base = os.environ["R2_PUBLIC_BASE"].rstrip("/") + "/" + key
    stories = {story["id"]: story for story in feed}
    audio = 0
    for payload in episodes:
        name = Path(payload["_file"]).stem
        client.upload_file(str(directory / f"{name}.m4a"), bucket, f"{key}/audio/{name}.m4a",
                           ExtraArgs={"ContentType": "audio/mp4", "CacheControl": "public, max-age=86400"})
        sidecar = {k: v for k, v in payload.items() if k != "_file"}
        sidecar["story"] = stories[payload["story"]["id"]]
        client.put_object(Bucket=bucket, Key=f"{key}/episodes/{name}.json",
                          Body=json.dumps(sidecar, ensure_ascii=False).encode(),
                          ContentType="application/json", CacheControl="public, max-age=86400")
        audio += 1
    body = json.dumps(feed, ensure_ascii=False).encode()
    client.put_object(Bucket=bucket, Key=f"{key}/feed.json", Body=body,
                      ContentType="application/json", CacheControl="no-cache")
    return {"feed": f"{base}/feed.json", "audio": audio, "sidecars": audio, "bytes": len(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", default=str(ROOT / "ios/Zwicky/Episodes"))
    parser.add_argument("--out", default="", help="also write feed.json here for inspection")
    parser.add_argument("--dry-run", action="store_true", help="build the feed, do not upload")
    args = parser.parse_args()

    directory = Path(args.episodes)
    prefix = os.environ.get("R2_PREFIX", "v1")
    public_base = os.environ.get("R2_PUBLIC_BASE", "https://example.invalid")
    episodes = load_episodes(directory)
    feed = build_feed(episodes, public_base, prefix)
    if args.out:
        Path(args.out).write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n")
    print(f"feed has {len(feed)} episodes; base {public_base.rstrip('/')}/{prefix}")
    if args.dry_run:
        for story in feed[:3]:
            print("  ", story["hostID"], "->", story["audioURL"], "| detail:", story["detailURL"])
        return
    print(json.dumps(upload(episodes, feed, directory, prefix), indent=2))


if __name__ == "__main__":
    main()
