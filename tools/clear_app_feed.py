#!/usr/bin/env python3
"""Clear app-visible episode objects and preserve a net-new publication ledger."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

from daily_release import app_feed_url, doi_from_url
from publish_feed import load_existing_feed, r2_client


def state_key(prefix: str, name: str) -> str:
    return f"{prefix.strip('/')}/.release/{name}.json"


def read_json_object(client, bucket: str, key: str, default):
    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except Exception as error:
        code = getattr(error, "response", {}).get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404"):
            return default
        raise
    value = json.loads(response["Body"].read())
    return value


def published_dois(feed: list) -> set[str]:
    dois = set()
    for story in feed:
        for source in story.get("sources", []):
            doi = doi_from_url(source.get("url", ""))
            if doi:
                dois.add(doi.casefold())
    return dois


def load_exclusions(client, bucket: str, prefix: str) -> list[str]:
    value = read_json_object(client, bucket, state_key(prefix, "excluded-dois"), [])
    if not isinstance(value, list) or any(not isinstance(doi, str) for doi in value):
        raise ValueError("Stored exclusion ledger is malformed")
    return sorted({doi.casefold() for doi in value})


def write_json(client, bucket: str, key: str, value) -> None:
    client.put_object(Bucket=bucket, Key=key,
                      Body=json.dumps(value, ensure_ascii=False).encode(),
                      ContentType="application/json", CacheControl="no-cache")


def wipe_app(client, bucket: str, prefix: str, public_base: str, run_id: int,
             exclusions_path: Path) -> tuple[int, int]:
    key_prefix = prefix.strip("/")
    feed_url = public_base.rstrip("/") + "/" + key_prefix + "/feed.json"
    if feed_url != app_feed_url():
        raise ValueError("R2 publication target differs from the app's default feed URL")

    feed = load_existing_feed(client, bucket, key_prefix)
    if any(not isinstance(story, dict) or not story.get("id") for story in feed):
        raise ValueError("Existing feed is malformed; refusing to clear it")
    exclusions = set(load_exclusions(client, bucket, key_prefix)) | published_dois(feed)

    # Remove app visibility first. Even if later object cleanup fails, no old
    # episode remains listed in the app.
    write_json(client, bucket, f"{key_prefix}/feed.json", [])
    write_json(client, bucket, state_key(key_prefix, "excluded-dois"), sorted(exclusions))
    write_json(client, bucket, state_key(key_prefix, "baseline"), {
        "minimum_run_id": int(run_id),
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    })

    deleted = 0
    for subdir in ("audio/", "episodes/"):
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{key_prefix}/{subdir}"):
            keys = [{"Key": item["Key"]} for item in page.get("Contents", [])]
            for offset in range(0, len(keys), 1000):
                batch = keys[offset:offset + 1000]
                if batch:
                    result = client.delete_objects(Bucket=bucket,
                                                   Delete={"Objects": batch, "Quiet": True}) or {}
                    if result.get("Errors"):
                        raise RuntimeError(f"R2 object deletion failed: {result['Errors'][:3]}")
                    deleted += len(batch)

    exclusions_path.parent.mkdir(parents=True, exist_ok=True)
    exclusions_path.write_text(json.dumps(sorted(exclusions)) + "\n")
    return len(feed), deleted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-exclusions", type=Path)
    parser.add_argument("--baseline-out", type=Path)
    parser.add_argument("--wipe", action="store_true")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--exclude-dois-file", type=Path)
    args = parser.parse_args()

    client = r2_client()
    bucket = os.environ["R2_BUCKET"]
    prefix = os.environ.get("R2_PREFIX", "v1")
    if args.load_exclusions:
        args.load_exclusions.parent.mkdir(parents=True, exist_ok=True)
        args.load_exclusions.write_text(json.dumps(load_exclusions(client, bucket, prefix)) + "\n")
    if args.baseline_out:
        value = read_json_object(client, bucket, state_key(prefix, "baseline"), None)
        if not isinstance(value, dict) or not isinstance(value.get("minimum_run_id"), int):
            raise ValueError("No valid release baseline exists; refusing to use historical batches")
        args.baseline_out.parent.mkdir(parents=True, exist_ok=True)
        args.baseline_out.write_text(json.dumps(value) + "\n")
    if args.wipe:
        if args.run_id is None or args.exclude_dois_file is None:
            parser.error("--wipe requires --run-id and --exclude-dois-file")
        old_count, deleted = wipe_app(client, bucket, prefix,
                                      os.environ["R2_PUBLIC_BASE"], args.run_id,
                                      args.exclude_dois_file)
        print(f"Cleared {old_count} feed episodes and {deleted} audio/sidecar objects; "
              f"preserved {len(json.loads(args.exclude_dois_file.read_text()))} DOI exclusions")


if __name__ == "__main__":
    main()
