#!/usr/bin/env python3
"""Exercise withdrawal, conditional feed writes and rollback on an isolated R2 prefix.

Copies one existing public recording. No generation, app feed mutation or production
asset deletion. Leaves the isolated staging catalog available for device checks.
"""
import argparse
import copy
import json
import os
from pathlib import Path

from publish_feed import episode_page, r2_client
from withdraw_episode import apply, encode, plan


def drill(client, bucket: str, base: str, run_id: str) -> dict:
    if not run_id.isdigit():
        raise ValueError('Staging run ID must be numeric')
    prefix = f'v1-release-drill/{run_id}'
    live = os.environ.get('R2_PREFIX', 'v1').strip('/')
    if prefix == live or live.startswith(prefix + '/'):
        raise ValueError('Staging prefix overlaps the live publication prefix')
    feed = json.loads(client.get_object(Bucket=bucket, Key=live + '/feed.json')['Body'].read())
    original = next(s for s in feed if s.get('audioURL') and s.get('withdrawalNotice') is None)
    name = original['id'].removeprefix('episode-')
    origin = base.rstrip('/') + '/' + live
    if original['audioURL'] != f'{origin}/audio/{name}.m4a':
        raise ValueError('Source audio does not belong to the expected production origin')
    staged = []
    original_sidecar = json.loads(client.get_object(Bucket=bucket, Key=f'{live}/episodes/{name}.json')['Body'].read())
    for episode_name in (name, 'drill-replacement'):
        story = copy.deepcopy(original)
        story.update(id='episode-' + episode_name,
                     audioURL=f'{base}/{prefix}/audio/{episode_name}.m4a',
                     detailURL=f'{base}/{prefix}/episodes/{episode_name}.json',
                     shareURL=f'{base}/{prefix}/listen/episode-{episode_name}.html')
        sidecar = {**original_sidecar, 'story': story}
        client.copy_object(Bucket=bucket, Key=f'{prefix}/audio/{episode_name}.m4a',
                           CopySource={'Bucket': bucket, 'Key': f'{live}/audio/{name}.m4a'})
        client.put_object(Bucket=bucket, Key=f'{prefix}/episodes/{episode_name}.json',
                          Body=encode(sidecar), ContentType='application/json')
        client.put_object(Bucket=bucket, Key=f'{prefix}/listen/episode-{episode_name}.html',
                          Body=episode_page(story), ContentType='text/html; charset=utf-8')
        staged.append(story)
    client.put_object(Bucket=bucket, Key=prefix + '/feed.json', Body=encode(staged),
                      ContentType='application/json', CacheControl='no-cache')
    # Prove the actual storage API rejects an incorrect precondition.
    try:
        client.put_object(Bucket=bucket, Key=prefix + '/feed.json', Body=b'[]',
                          IfMatch='"deliberately-wrong-etag"')
    except Exception as error:
        if str(getattr(error, 'response', {}).get('Error', {}).get('Code')) not in ('PreconditionFailed', '412'):
            raise
    else:
        raise ValueError('Storage accepted a stale feed precondition')
    reviewed = plan(staged, original['id'], 'Staging drill: withdrawn to test correction handling.',
                    'episode-drill-replacement')
    result = apply(client, bucket, prefix, base, reviewed)
    withdrawn = json.loads(client.get_object(Bucket=bucket, Key=prefix + '/feed.json')['Body'].read())
    tombstone = next(s for s in withdrawn if s['id'] == original['id'])
    if tombstone.get('audioURL') is not None or not tombstone.get('replacementID'):
        raise ValueError('Staged withdrawal did not expose its notice and replacement')
    try:
        client.head_object(Bucket=bucket, Key=f'{prefix}/audio/{name}.m4a')
    except Exception as error:
        if str(getattr(error, 'response', {}).get('Error', {}).get('Code')) not in ('404', 'NoSuchKey', 'NotFound'):
            raise
    else:
        raise ValueError('Withdrawn staged audio still exists')
    # Roll back assets first, then the staging feed using its new ETag.
    backup = result['backupPrefix']
    for directory, filename in [('audio', name + '.m4a'), ('episodes', name + '.json'),
                                ('listen', 'episode-' + name + '.html')]:
        client.copy_object(Bucket=bucket, Key=f'{prefix}/{directory}/{filename}',
                           CopySource={'Bucket': bucket, 'Key': f'{backup}/{filename}'})
    current = client.get_object(Bucket=bucket, Key=prefix + '/feed.json')
    client.put_object(Bucket=bucket, Key=prefix + '/feed.json', Body=encode(staged),
                      ContentType='application/json', CacheControl='no-cache', IfMatch=current['ETag'])
    restored = json.loads(client.get_object(Bucket=bucket, Key=prefix + '/feed.json')['Body'].read())
    if restored != staged:
        raise ValueError('Staging feed rollback differs from the original snapshot')
    client.head_object(Bucket=bucket, Key=f'{prefix}/audio/{name}.m4a')
    return {'stagingFeedURL': f'{base}/{prefix}/feed.json', 'productionFeedUntouched': True,
            'conditionalWriteRejected': True, 'withdrawalAndReplacementPassed': True,
            'withdrawnAudioRemovalPassed': True, 'snapshotRollbackPassed': True,
            'devicePlaybackAndQueueQA': 'pending; storage checks do not prove device behavior'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = drill(r2_client(), os.environ['R2_BUCKET'], os.environ['R2_PUBLIC_BASE'].rstrip('/'), args.run_id)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
