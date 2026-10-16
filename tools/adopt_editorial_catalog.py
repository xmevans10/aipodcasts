#!/usr/bin/env python3
"""Stage a reviewed catalog replacement, then apply an exact fingerprinted plan.

Legacy IDs survive as notices. Original feed and assets are backed up before one
conditional feed update. New recordings must already resolve publicly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import editorial_policy
from daily_release import select, stage
from publish_feed import (add_share_urls, build_feed, episode_page, merge_feed,
                          r2_client, upload, validate_rendered_episodes, verify_staged_assets)
from withdraw_episode import encode, fingerprint, plan as withdraw_plan

NOTICE = ('Retired during Zwicky’s editorial update. This episode was produced before '
          'our current major-source selection, show-fit and plain-language writing reviews. '
          'Follow this show for newly reviewed episodes.')


def legacy(story):
    if story.get('withdrawalNotice') is not None:
        return False
    try:
        editorial_policy.require_story(story)
        return False
    except ValueError:
        return True


def projected(feed):
    result = feed
    for story in feed:
        if legacy(story):
            result = withdraw_plan(result, story['id'], NOTICE)['feed']
    return result


def make_plan(feed, incoming, day, source_run):
    if len(incoming) != 2 or any(s.get('published') != day for s in incoming):
        raise ValueError('Catalog adoption requires two current-day reviewed recordings')
    for story in incoming:
        editorial_policy.require_story(story)
    merged = merge_feed(projected(feed), incoming, day=day)
    if any(legacy(s) for s in merged):
        raise ValueError('Legacy playable episode survived migration')
    return {'feedSHA256': fingerprint(feed), 'original': feed, 'feed': merged,
            'incoming': incoming, 'day': day, 'sourceRun': int(source_run),
            'retiredIDs': [s['id'] for s in feed if legacy(s)]}


def apply(client, bucket, prefix, base, reviewed, expected_sha):
    if fingerprint(reviewed) != expected_sha:
        raise ValueError('Migration plan fingerprint differs from reviewed artifact')
    obj = client.get_object(Bucket=bucket, Key=f'{prefix}/feed.json')
    current = json.loads(obj['Body'].read())
    adopted = fingerprint(current) == fingerprint(reviewed['feed'])
    if not adopted and reviewed['day'] != dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat():
        raise ValueError('Migration plan publication date expired')
    if not adopted and fingerprint(current) != reviewed['feedSHA256']:
        raise ValueError('Live catalog changed; generate and review a fresh plan')
    if make_plan(reviewed['original'], reviewed['incoming'], reviewed['day'], reviewed['sourceRun']) != reviewed:
        raise ValueError('Migration plan was edited or is invalid')
    verify_staged_assets(reviewed['incoming'])
    backup = f"{prefix}/.release/editorial-adoption/{expected_sha}"
    if not adopted:
        # Back up every original object before changing any public record.
        client.put_object(Bucket=bucket, Key=backup + '/plan.json', Body=encode(reviewed),
                          ContentType='application/json', CacheControl='no-store')
        root = base.rstrip('/') + '/' + prefix
        for old in current:
            if old['id'] not in reviewed['retiredIDs']:
                continue
            name = old['id'].removeprefix('episode-')
            if (old.get('audioURL') != f'{root}/audio/{name}.m4a'
                    or old.get('detailURL') != f'{root}/episodes/{name}.json'
                    or old.get('shareURL') != f"{root}/listen/{old['id']}.html"):
                raise ValueError('Legacy asset origin does not match this catalog')
            for key in (f'{prefix}/audio/{name}.m4a', f'{prefix}/episodes/{name}.json',
                        f"{prefix}/listen/{old['id']}.html"):
                client.copy_object(Bucket=bucket, Key=backup + '/' + key,
                                   CopySource={'Bucket': bucket, 'Key': key})
        client.put_object(Bucket=bucket, Key=f'{prefix}/feed.json', Body=encode(reviewed['feed']),
                          ContentType='application/json', CacheControl='no-cache', IfMatch=obj['ETag'])
    for story in reviewed['feed']:
        if story['id'] not in reviewed['retiredIDs']:
            continue
        name = story['id'].removeprefix('episode-')
        client.put_object(Bucket=bucket, Key=f'{prefix}/episodes/{name}.json',
                          Body=encode({'story': story, 'withdrawalNotice': NOTICE}),
                          ContentType='application/json', CacheControl='no-cache')
        client.put_object(Bucket=bucket, Key=f"{prefix}/listen/{story['id']}.html",
                          Body=episode_page(story), ContentType='text/html; charset=utf-8',
                          CacheControl='no-cache')
        client.delete_object(Bucket=bucket, Key=f'{prefix}/audio/{name}.m4a')
    client.put_object(Bucket=bucket, Key=f'{prefix}/.release/baseline.json',
                      Body=encode({'minimum_run_id': reviewed['sourceRun'], 'editorialPolicy': editorial_policy.SELECTION}),
                      ContentType='application/json', CacheControl='no-cache')
    return {'active': sum(s.get('withdrawalNotice') is None for s in reviewed['feed']),
            'retired': len(reviewed['retiredIDs']), 'backup': backup}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['select', 'plan', 'apply'])
    parser.add_argument('--root', type=Path, default=Path('adoption'))
    parser.add_argument('--source-run', type=int)
    parser.add_argument('--plan-sha')
    args = parser.parse_args()
    client = r2_client()
    bucket, prefix, base = os.environ['R2_BUCKET'], os.environ.get('R2_PREFIX', 'v1'), os.environ['R2_PUBLIC_BASE']
    args.root.mkdir(parents=True, exist_ok=True)
    if args.mode == 'apply':
        if not args.plan_sha:
            parser.error('Apply requires the reviewed plan fingerprint')
        print(json.dumps(apply(client, bucket, prefix, base,
                              json.loads((args.root / 'plan.json').read_text()), args.plan_sha)))
        return
    if args.mode == 'select':
        obj = client.get_object(Bucket=bucket, Key=f'{prefix}/feed.json')
        feed = json.loads(obj['Body'].read())
        (args.root / 'original-feed.json').write_bytes(encode(feed))
        day = dt.datetime.now(ZoneInfo('America/New_York')).date().isoformat()
        (args.root / 'date.txt').write_text(day)
        picked = select(args.root / 'batches', projected(feed), day)
        if len(picked) != 2:
            raise ValueError('Need two approved unpublished episodes before migration')
        stage(picked, args.root / 'transcripts')
        return
    directory = args.root / 'episodes'
    episodes = [{**json.loads(p.read_text()), '_file': p.name}
                for p in directory.glob('*.json') if p.name != 'index.json']
    validate_rendered_episodes(episodes, directory)
    incoming = add_share_urls(build_feed(episodes, base, prefix), base, prefix)
    reviewed = make_plan(json.loads((args.root / 'original-feed.json').read_text()), incoming,
                         (args.root / 'date.txt').read_text(), args.source_run)
    upload(episodes, incoming, directory, prefix, client=client, assets_only=True)
    verify_staged_assets(incoming)
    (args.root / 'plan.json').write_bytes(encode(reviewed))
    summary = {'planSHA256': fingerprint(reviewed), 'retiredIDs': reviewed['retiredIDs'],
               'newEpisodes': [{'id': s['id'], 'title': s['title'], 'host': s['hostID'],
                                'policy': s['editorialPolicy']} for s in incoming]}
    (args.root / 'review.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
