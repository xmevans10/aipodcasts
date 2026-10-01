#!/usr/bin/env python3
"""Plan an explicit episode withdrawal; apply only a reviewed plan to the unchanged feed.

The original episode ID remains as a notice for saved records and old links. A corrected
recording needs a new ID and its own strict reviews. Audio and prior feed are backed up
before changes; conditional feed writes reject concurrent publication. This tool never
silently edits the science in a recording.
"""
import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

from publish_feed import episode_page, r2_client


def encode(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()


def fingerprint(feed: list) -> str:
    return hashlib.sha256(encode(feed)).hexdigest()


def plan(feed: list, episode_id: str, notice: str, replacement_id: str | None = None) -> dict:
    if not isinstance(feed, list) or any(not isinstance(s, dict) or not s.get('id') for s in feed):
        raise ValueError('Invalid feed')
    if len({s['id'] for s in feed}) != len(feed):
        raise ValueError('Duplicate episode IDs')
    if len(notice.strip()) < 20:
        raise ValueError('Give listeners a substantive withdrawal explanation')
    matches = [s for s in feed if s['id'] == episode_id]
    if len(matches) != 1 or not re.fullmatch(r'episode-[a-z0-9._-]+', episode_id):
        raise ValueError('Withdrawal must identify one existing episode')
    original = matches[0]
    if replacement_id:
        replacement = next((s for s in feed if s['id'] == replacement_id), None)
        if not replacement or replacement_id == episode_id or replacement.get('withdrawalNotice') is not None:
            raise ValueError('Replacement must be a distinct, already published playable episode')
        if replacement.get('hostID') != original.get('hostID') or not replacement.get('audioURL'):
            raise ValueError('Replacement must belong to the same show and have audio')
    revised = copy.deepcopy(feed)
    for story in revised:
        if story['id'] == episode_id:
            story.update(withdrawalNotice=notice.strip(), body=notice.strip(), audioURL=None,
                         turns=None, minutes=0)
            if replacement_id:
                story['replacementID'] = replacement_id
    return {'feedSHA256': fingerprint(feed), 'episodeID': episode_id,
            'notice': notice.strip(), 'replacementID': replacement_id,
            'original': original, 'feed': revised}


def apply(client, bucket: str, prefix: str, base: str, reviewed: dict) -> dict:
    prefix = prefix.strip('/')
    obj = client.get_object(Bucket=bucket, Key=f'{prefix}/feed.json')
    current = json.loads(obj['Body'].read())
    if fingerprint(current) != reviewed['feedSHA256']:
        raise ValueError('Feed changed since the plan; prepare and review a new plan')
    # Recompute rather than trusting an edited plan's replacement feed.
    checked = plan(current, reviewed['episodeID'], reviewed['notice'], reviewed.get('replacementID'))
    if checked != reviewed:
        raise ValueError('Withdrawal plan was edited or is malformed')
    name = reviewed['episodeID'].removeprefix('episode-')
    old = reviewed['original']
    root = base.rstrip('/') + '/' + prefix
    if (old.get('audioURL') not in (None, f'{root}/audio/{name}.m4a')
            or old.get('detailURL') != f'{root}/episodes/{name}.json'
            or old.get('shareURL') != f'{root}/listen/episode-{name}.html'):
        raise ValueError('Episode assets do not match this storage origin and prefix')
    backup = f"{prefix}/.release/withdrawals/{reviewed['feedSHA256']}/{name}"
    client.put_object(Bucket=bucket, Key=backup + '-plan.json', Body=encode(reviewed),
                      ContentType='application/json', CacheControl='no-store')
    if old.get('withdrawalNotice') is None:
        for key in (f'{prefix}/audio/{name}.m4a', f'{prefix}/episodes/{name}.json',
                    f'{prefix}/listen/episode-{name}.html'):
            client.copy_object(Bucket=bucket, Key=backup + '/' + key.rsplit('/', 1)[1],
                               CopySource={'Bucket': bucket, 'Key': key})
    # Publish the blocking notice with compare-and-swap before mutating public assets.
    client.put_object(Bucket=bucket, Key=f'{prefix}/feed.json', Body=encode(reviewed['feed']),
                      ContentType='application/json', CacheControl='no-cache', IfMatch=obj['ETag'])
    tombstone = next(s for s in reviewed['feed'] if s['id'] == reviewed['episodeID'])
    client.put_object(Bucket=bucket, Key=f'{prefix}/episodes/{name}.json',
                      Body=encode({'story': tombstone, 'withdrawalNotice': reviewed['notice']}),
                      ContentType='application/json', CacheControl='no-cache')
    client.put_object(Bucket=bucket, Key=f'{prefix}/listen/episode-{name}.html',
                      Body=episode_page(tombstone), ContentType='text/html; charset=utf-8', CacheControl='no-cache')
    # Cached older clients fail playback rather than stream superseded science.
    client.delete_object(Bucket=bucket, Key=f'{prefix}/audio/{name}.m4a')
    return {'withdrawnID': reviewed['episodeID'], 'backupPrefix': backup,
            'replacementID': reviewed.get('replacementID'), 'publicAudioRemoved': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed', type=Path, help='saved feed for an offline plan')
    parser.add_argument('--episode')
    parser.add_argument('--notice')
    parser.add_argument('--replacement-id')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--apply-plan', type=Path, help='explicitly apply this reviewed JSON plan')
    args = parser.parse_args()
    if args.apply_plan:
        if any((args.feed, args.episode, args.notice, args.out, args.replacement_id)):
            parser.error('--apply-plan cannot be combined with plan creation inputs')
        print(json.dumps(apply(r2_client(), os.environ['R2_BUCKET'], os.environ.get('R2_PREFIX', 'v1'),
                               os.environ['R2_PUBLIC_BASE'], json.loads(args.apply_plan.read_text())), indent=2))
        return
    if not args.episode or not args.notice or not args.out:
        parser.error('Plan creation requires --episode, --notice and --out')
    if args.feed:
        feed = json.loads(args.feed.read_text())
    else:
        obj = r2_client().get_object(Bucket=os.environ['R2_BUCKET'],
                                    Key=os.environ.get('R2_PREFIX', 'v1').strip('/') + '/feed.json')
        feed = json.loads(obj['Body'].read())
    result = plan(feed, args.episode, args.notice, args.replacement_id)
    args.out.write_bytes(encode(result) + b'\n')
    print(f"Prepared withdrawal plan for {args.episode}; no public changes made.")


if __name__ == '__main__':
    main()
