#!/usr/bin/env python3
"""Export a credential-free run usage record, including failed reserved attempts.

Token totals cover responses recorded by the writer. Missing reviewer token counts
are unknown, not zero. Provider billing remains the source of actual dollar charges.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
from pathlib import Path


def report(db: sqlite3.Connection, run_id: str) -> dict:
    rows = [dict(zip(('day', 'role', 'attempts', 'inputTokens', 'outputTokens', 'tokenMeasuredAttempts'), row))
            for row in db.execute('SELECT day,provider,count(*),sum(input_tokens),sum(output_tokens),'
                                  'sum(input_tokens IS NOT NULL AND output_tokens IS NOT NULL) '
                                  'FROM calls GROUP BY day,provider ORDER BY day,provider')]
    return {'schemaVersion': 1, 'runID': run_id,
            'generatedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
            'writerModel': os.environ.get('OPENAI_MODEL', 'gpt-5.6-luna'),
            'attempts': sum(row['attempts'] for row in rows), 'usage': rows,
            'actualChargeUSD': None,
            'limitations': ['Reserved attempts include failures and may not all be billed.',
                            'Missing token usage is unknown; factual and audience reviewers may not report it.',
                            'The provider-call cap is local to this run, not an account-wide spend limit.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=Path('backend/data/lilt.sqlite3'))
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.db.is_file():
        raise ValueError('No generation database; refusing to report zero usage')
    with sqlite3.connect(f'file:{args.db.resolve()}?mode=ro', uri=True) as db:
        result = report(db, args.run_id)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
