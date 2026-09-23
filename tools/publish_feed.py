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

    python3 tools/publish_feed.py --episodes rendered-episodes
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

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


def add_share_urls(feed: list, public_base: str, prefix: str) -> list:
    """Give every feed entry a stable, browser-friendly listening page."""
    base = public_base.rstrip("/") + "/" + prefix.strip("/")
    if urlparse(base).scheme != "https":
        raise ValueError("Public listening pages require an HTTPS origin")
    updated = []
    for story in feed:
        story_id = story["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", story_id):
            raise ValueError(f"Invalid episode id for a public URL: {story_id!r}")
        updated.append({**story, "shareURL": f"{base}/listen/{story_id}.html"})
    return updated


def episode_page(story: dict) -> bytes:
    """A standalone page with metadata, audio, transcript and sources."""
    escape = lambda value: html.escape(str(value or ""), quote=True)
    share_url = story["shareURL"]
    audio_url = story.get("audioURL", "")
    if urlparse(share_url).scheme != "https" or urlparse(audio_url).scheme != "https":
        raise ValueError("Listening pages require HTTPS share and audio URLs")
    title, dek = escape(story.get("title")), escape(story.get("dek"))
    body = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in story.get("body", "").split("\n\n") if paragraph)
    sources = "\n".join(
        f'<li><a href="{escape(source["url"])}">{escape(source.get("title"))}</a>'
        f' — {escape(source.get("attribution"))}</li>'
        for source in story.get("sources", [])
        if urlparse(source.get("url", "")).scheme == "https"
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Zwicky</title>
<meta name="description" content="{dek}">
<link rel="canonical" href="{escape(share_url)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{dek}">
<meta property="og:url" content="{escape(share_url)}">
<meta name="twitter:card" content="summary">
<style>body{{font:18px/1.6 system-ui,sans-serif;max-width:720px;margin:auto;padding:32px 20px;color:#161614;background:#faf9f6}}
h1{{font:700 clamp(2rem,7vw,3.5rem)/1.12 Georgia,serif}}audio{{width:100%}}a{{color:#304c75}}
small,.meta{{color:#68665f}}section{{margin-top:2rem}}li{{margin:.5rem 0}}</style></head>
<body><header><p class="meta">ZWICKY · {escape(story.get("topic"))}</p>
<h1>{title}</h1><p>{dek}</p></header>
<main><audio controls preload="none" src="{escape(audio_url)}">Your browser cannot play this audio.</audio>
<p class="meta">{escape(story.get("minutes"))} min · AI-narrated</p>
<section aria-label="Transcript"><h2>Transcript</h2>{body}</section>
<section aria-label="About this episode"><h2>About this episode</h2><p>{escape(story.get("caveat"))}</p></section>
<section aria-label="Sources"><h2>Sources</h2><ol>{sources}</ol></section></main>
<footer><small>Hosts are fictional AI presenters. Check the linked sources for the underlying research.</small></footer>
</body></html>"""
    return page.encode("utf-8")


def load_episodes(directory: Path) -> list:
    episodes = []
    for path in sorted(directory.glob("*.json")):
        if path.stem == "index":
            continue
        episodes.append({**json.loads(path.read_text()), "_file": str(path)})
    return episodes


def merge_feed(existing: list, incoming: list, *, day: str, max_per_day: int = 2) -> list:
    """Keep the archive, replace older editions, and enforce the daily allowance."""
    if not isinstance(existing, list) or any(not isinstance(s, dict) or not s.get("id") for s in existing):
        raise ValueError("Existing feed is malformed; refusing to replace it")
    if any(not isinstance(s, dict) or not s.get("id") for s in incoming):
        raise ValueError("New feed contains a story without an id")
    def paper_key(story):
        for source in story.get("sources", []):
            match = re.search(r"10\.\d{4,9}/[^\s?#]+", source.get("url", ""), re.I)
            if match and story.get("hostID"):
                return (story["hostID"], match.group(0).rstrip("/.").casefold())
        return None

    incoming_ids = {story["id"] for story in incoming}
    incoming_papers = {key for story in incoming if (key := paper_key(story))}
    existing = [story for story in existing
                if paper_key(story) not in incoming_papers or story["id"] in incoming_ids]
    by_id = {story["id"]: story for story in existing}
    if len(by_id) != len(existing):
        raise ValueError("Existing feed has duplicate story ids")
    for story in incoming:
        old = by_id.get(story["id"])
        if old and {k: v for k, v in old.items() if k != "shareURL"} != story:
            raise ValueError("Published story id already has different metadata")
        by_id[story["id"]] = story
    merged = sorted(by_id.values(), key=lambda s: (s.get("published", ""), s["id"]), reverse=True)
    if sum(s.get("published") == day for s in merged) > max_per_day:
        raise ValueError(f"More than {max_per_day} episodes would be published on {day}")
    return merged


def r2_client():
    import boto3  # imported lazily so local runs without R2 can still build the feed
    return boto3.client("s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
                          aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"])


def load_existing_feed(client, bucket: str, prefix: str) -> list:
    try:
        response = client.get_object(Bucket=bucket, Key=f"{prefix.strip('/')}/feed.json")
    except Exception as error:
        # Only a genuinely absent feed is an empty feed. Auth, network and parsing
        # failures must not reset the archive.
        code = getattr(error, "response", {}).get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404"):
            return []
        raise
    feed = json.loads(response["Body"].read())
    if not isinstance(feed, list):
        raise ValueError("Existing feed is not a JSON list")
    return feed


def upload(episodes: list, feed: list, directory: Path, prefix: str, client=None) -> dict:
    client = client or r2_client()
    bucket = os.environ["R2_BUCKET"]
    key = prefix.strip("/")
    base = os.environ["R2_PUBLIC_BASE"].rstrip("/") + "/" + key
    stories = {story["id"]: story for story in feed}
    pages = [(story["id"], episode_page(story)) for story in feed]
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
    for story_id, page in pages:
        client.put_object(Bucket=bucket, Key=f"{key}/listen/{story_id}.html",
                          Body=page, ContentType="text/html; charset=utf-8",
                          CacheControl="public, max-age=300")
    body = json.dumps(feed, ensure_ascii=False).encode()
    client.put_object(Bucket=bucket, Key=f"{key}/feed.json", Body=body,
                      ContentType="application/json", CacheControl="no-cache")
    return {"feed": f"{base}/feed.json", "audio": audio, "sidecars": audio,
            "listening_pages": len(feed), "bytes": len(body)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", default=str(ROOT / "rendered-episodes"))
    parser.add_argument("--out", default="", help="also write feed.json here for inspection")
    parser.add_argument("--dry-run", action="store_true", help="build the feed, do not upload")
    parser.add_argument("--merge-existing", action="store_true", help="append to the existing R2 feed")
    parser.add_argument("--share-pages-only", action="store_true",
                        help="publish listening pages for the existing feed without new episodes")
    parser.add_argument("--max-per-day", type=int, default=2)
    args = parser.parse_args()

    directory = Path(args.episodes)
    prefix = os.environ.get("R2_PREFIX", "v1")
    public_base = os.environ.get("R2_PUBLIC_BASE", "https://example.invalid")
    episodes = [] if args.share_pages_only else load_episodes(directory)
    if not episodes and not args.share_pages_only:
        raise ValueError("No rendered episodes to publish")
    client = None
    if args.share_pages_only:
        client = r2_client()
        feed = load_existing_feed(client, os.environ["R2_BUCKET"], prefix)
        if not feed:
            raise ValueError("No existing feed to add listening pages to")
    else:
        feed = build_feed(episodes, public_base, prefix)
    if args.merge_existing and not args.share_pages_only:
        client = r2_client()
        existing = load_existing_feed(client, os.environ["R2_BUCKET"], prefix)
        dates = {story["published"] for story in feed}
        if len(dates) != 1:
            raise ValueError("Daily release must contain episodes from one publication date")
        feed = merge_feed(existing, feed, day=dates.pop(), max_per_day=args.max_per_day)
    feed = add_share_urls(feed, public_base, prefix)
    if args.out:
        Path(args.out).write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n")
    print(f"feed has {len(feed)} episodes; base {public_base.rstrip('/')}/{prefix}")
    if args.dry_run:
        for story in feed[:3]:
            print("  ", story["hostID"], "->", story["audioURL"], "| detail:", story["detailURL"])
        return
    print(json.dumps(upload(episodes, feed, directory, prefix, client=client), indent=2))


if __name__ == "__main__":
    main()
