#!/usr/bin/env python3
"""Create an operator view from strict-reviewed inventory and the actual public feed."""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from hosts import HOSTS
from beats import normalize_host
from daily_release import available, app_feed_url
from urllib.request import Request, urlopen


def status(batches: Path, feed: list) -> dict:
    if (not isinstance(feed, list) or any(not isinstance(s, dict) or not s.get('id') for s in feed)
            or len({s['id'] for s in feed}) != len(feed)):
        raise ValueError('Malformed or duplicate public feed')
    eligible = available(batches, feed)
    canonical = {normalize_host(host.id): host.show for host in HOSTS.values()}
    rows = []
    for host, show in canonical.items():
        public = [s for s in feed if normalize_host(s.get('hostID', '')) == host and s.get('withdrawalNotice') is None]
        pending = [entry for _, entry in eligible if normalize_host(entry['host']) == host]
        rows.append({'host': host, 'show': show, 'publicEpisodes': len(public),
                     'lastPublished': max((s.get('published', '') for s in public), default=None),
                     'approvedUnpublished': len(pending),
                     'evidenceTiers': sorted({str(e.get('evidence_tier', 'unknown')) for e in pending})})
    runs = {}
    for path in batches.rglob('usage.json'):
        usage = json.loads(path.read_text()); run_id = usage['runID']
        if run_id in runs and runs[run_id] != usage:
            raise ValueError(f'Conflicting usage records for run {run_id}')
        runs[run_id] = usage
    count = len(eligible)
    return {'generatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
            'withdrawnEpisodes': sum(s.get('withdrawalNotice') is not None for s in feed),
            'publicEpisodes': sum(s.get('withdrawalNotice') is None for s in feed), 'playableShows': sum(r['publicEpisodes'] > 0 for r in rows),
            'catalogShows': len(rows), 'approvedUnpublished': count, 'daysAtTwoPerDay': count / 2,
            'belowWeekBuffer': count < 14, 'shows': rows, 'recordedUsageRuns': list(runs.values()),
            'billingBalanceAndActualSpend': 'unknown; reconcile provider billing',
            'nextActions': ['Fill every promoted show or advertise a smaller catalog.',
                            'Replenish below fourteen approved unpublished episodes.',
                            'Listen to launch audio and verify on physical devices.']}


def markdown(result: dict) -> str:
    lines = ['# Content operations status', '',
             f"{result['publicEpisodes']} public episodes; {result['playableShows']}/{result['catalogShows']} shows playable.",
             f"{result['approvedUnpublished']} approved unpublished episodes ({result['daysAtTwoPerDay']:g} days at two/day).",
             '', '| Show | Public | Ready inventory | Latest publication |', '|---|---:|---:|---|']
    lines.extend(f"| {r['show']} | {r['publicEpisodes']} | {r['approvedUnpublished']} | {r['lastPublished'] or 'None'} |"
                 for r in result['shows'])
    lines += ['', 'Actual spend and balances: unverified. Recorded call counts are not dollar charges.',
              'This report validates scripts, not subjective listening quality or public asset availability.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batches', type=Path, required=True)
    parser.add_argument('--feed', type=Path, help='saved feed; otherwise fetch the app public feed')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.feed:
        feed = json.loads(args.feed.read_text())
    else:
        with urlopen(Request(app_feed_url(), headers={'User-Agent': 'curl/8.0'}), timeout=20) as response:
            feed = json.load(response)
    result = status(args.batches, feed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.out / 'status.md').write_text(markdown(result))
    print(markdown(result))


if __name__ == '__main__':
    main()
